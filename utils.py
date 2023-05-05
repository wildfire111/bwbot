from web3 import Web3
import requests
import os
import json
from tqdm import tqdm
import sqlite3
from classes import Transaction

from dotenv import load_dotenv
load_dotenv()
apikey = os.getenv('ALCH_KEY')
url = 'https://arb-mainnet.g.alchemy.com/v2/'+apikey

def GetCurrentBlock():
    payload = {"jsonrpc": "2.0", "id": 0, "method": "eth_blockNumber"}
    headers = {"Accept": "application/json","Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    respdict = response.json()
    current_block = Web3.toInt(hexstr=respdict['result'])
    print(f"Current block: {current_block}")
    return current_block

def CheckTablesExist():
    con = sqlite3.connect('transactions.db')
    cur = con.cursor()
    tables_exist = True
    try:
        cur.execute('SELECT recordedblock FROM tracker')
    except:
        tables_exist = False
        CreateTables()
    con.commit()
    con.close()
    return tables_exist

def CreateTables():
    con = sqlite3.connect('transactions.db')
    cur = con.cursor()
    cur.execute('CREATE TABLE tracker (recordedblock Integer)')
    cur.execute('''CREATE TABLE transactions (
        AccAddress String,
        Collateral String,
        IndexToken String,
        Price Decimal(38,38),
        CollatDelta Decimal(38,38),
        SizeDelta Decimal(38,38),
        Fee Decimal(38,38),
        IsLong Bool,
        Block Int,
        TxHash String
    )''')
    con.commit()
    con.close()
    
def GetBlocksByTopic(from_block,to_block,topic):
    payload = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "eth_getLogs",
        "params": [
            {
            "fromBlock": Web3.toHex(from_block),
            "toBlock": Web3.toHex(to_block),
            "address": "0x489ee077994B6658eAfA855C308275EAd8097C4A",
            "topics": [topic]
            }
        ]
    }
    headers = {"Accept": "application/json","Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    return response

def GetAllLogsByTopicInChunks(start_block, topic):
    CHUNK_SIZE = 100000
    MIN_CHUNK_SIZE = 1
    MAX_RETRIES = 5
    current_block = GetCurrentBlock()
    responses = []

    if start_block > current_block:
        raise ValueError("Start block is greater than the current block.")

    from_block = start_block
    while from_block < current_block:
        to_block = min(from_block + CHUNK_SIZE - 1, current_block)
        chunk_size = CHUNK_SIZE
        retries = 0
        success = False

        while chunk_size >= MIN_CHUNK_SIZE and retries < MAX_RETRIES:
            response = GetBlocksByTopic(from_block, to_block, topic)

            if response.ok:
                json_response = response.json()
                results = json_response.get('result', [])  # Extract the 'result' list
                for result in results:
                    address = result.get('address', '')
                    data = result.get('data', '')
                    # Modify the data field as required
                    data = data[2:]  # Drop the first two characters
                    data = [data[i:i+64] for i in range(0, len(data), 64)]  # Split every 64 characters
                    account_address = data[1]
                    collateral_type_hex = data[2]
                    underlying_token_hex = data[3]
                    price = data[4]
                    collateral_delta = data[5]
                    size_delta = data[6]
                    fee = data[7]
                    direction = ""
                    newtrade = Transaction(
                        Web3.toHex(hexstr=account_address[24:]),
                        Web3.toHex(hexstr=collateral_type_hex[24:]),
                        Web3.toHex(hexstr=underlying_token_hex[24:]),
                        Web3.toInt(hexstr=price)/(10**30),
                        Web3.toInt(hexstr=collateral_delta)/(10**30),
                        Web3.toInt(hexstr=size_delta)/(10**30),
                        Web3.toInt(hexstr=fee)/(10**30),
                        direction,
                        result.get('blockNumber', ''),
                        result.get('transactionHash', '')
                    )
                    responses.append(newtrade)
                success = True
                break
            else:
                chunk_size //= 2
                to_block = min(from_block + chunk_size - 1, current_block)
                retries += 1

        if retries >= MAX_RETRIES and not success:
            raise RuntimeError("Exceeded maximum retry limit for fetching logs.")

        from_block = to_block + 1

    return responses
