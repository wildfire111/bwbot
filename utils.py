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
    #print(f"Current block: {current_block}")
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_address TEXT,
    collateral_type TEXT,
    underlying_token TEXT,
    price REAL,
    collateral_delta REAL,
    size_delta REAL,
    fee REAL,
    is_long INTEGER,
    block_number INTEGER,
    tx_hash TEXT
    );
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
                    collateral_delta = data[4]
                    size_delta = data[5]
                    islongint = int(data[6])
                    price = data[7]
                    fee = data[8]
                    if islongint > 0:
                        is_long = True
                    else:
                        is_long = False
                    """ print('accadd: '+str(Web3.toHex(hexstr=account_address[24:])))
                    print('collat: '+str(Web3.toHex(hexstr=collateral_type_hex[24:])))
                    print('underlying: '+str(Web3.toHex(hexstr=underlying_token_hex[24:])))
                    print('price: '+str(Web3.toInt(hexstr=price)/(10**30)))
                    print('collat_delta: '+str(Web3.toInt(hexstr=collateral_delta)/(10**30)))
                    print('size_delta: '+str(Web3.toInt(hexstr=size_delta)/(10**30)))
                    print('fee: '+str(Web3.toInt(hexstr=fee)/(10**30)))
                    print('is_long: '+str(is_long)) """
                    newtrade = Transaction(
                        Web3.toHex(hexstr=account_address[24:]),
                        Web3.toHex(hexstr=collateral_type_hex[24:]),
                        Web3.toHex(hexstr=underlying_token_hex[24:]),
                        Web3.toInt(hexstr=price)/(10**30),
                        Web3.toInt(hexstr=collateral_delta)/(10**30),
                        Web3.toInt(hexstr=size_delta)/(10**30),
                        Web3.toInt(hexstr=fee)/(10**30),
                        is_long,
                        result.get('blockNumber', ''),
                        result.get('transactionHash', '')
                    )
                    print(newtrade)
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

def get_transactions_for_trader(trader_address: str) -> list:
    # Open the database and retrieve transactions for the specified trader
    conn = sqlite3.connect("TransactionList.db")
    c = conn.cursor()
    c.execute("SELECT * FROM transactions WHERE account_address=?", (trader_address,))
    rows = c.fetchall()
    conn.close()

    # Create Transaction objects for each row and sort by block number
    transactions = []
    for row in rows:
        transaction = Transaction(*row)
        transactions.append(transaction)
    transactions.sort(key=lambda t: t.block_number)
    
    return transactions

from typing import List

def transactions_to_trades(transactions: list) -> list:
    trades = []
    open_positions = {}
    for transaction in transactions:
        # Get the key for the open position corresponding to the transaction
        key = (transaction.collateral_type, transaction.underlying_token, transaction.is_long)

        # Check if the transaction opens or closes a position
        if transaction.size_delta > 0:
            # If the transaction opens a position, create a new open position
            if key not in open_positions:
                open_positions[key] = {
                    'size': transaction.size_delta,
                    'collateral': transaction.collateral_delta,
                    'average_open_price': transaction.price
                }
            else:
                # If the position is already open, update the position size, collateral and average open price
                position = open_positions[key]
                new_size = position['size'] + transaction.size_delta
                new_collateral = position['collateral'] + transaction.collateral_delta
                new_average_open_price = (
                    (position['size'] * position['average_open_price'] +
                     transaction.size_delta * transaction.price) / new_size
                )
                position['size'] = new_size
                position['collateral'] = new_collateral
                position['average_open_price'] = new_average_open_price
        else:
            # If the transaction closes a position, calculate the profit and create a new Trade object
            if key in open_positions:
                position = open_positions[key]
                if abs(transaction.size_delta) >= position['size']:
                    # If the position is fully closed, calculate the profit and remove the position
                    end_price = transaction.price
                    start_price = position['average_open_price']
                    size = position['size']
                    collateral = position['collateral']
                    trade = Trade(start_price, end_price, size, collateral)
                    trades.append(trade)
                    del open_positions[key]
                else:
                    # If the position is only partially closed, update the position size and collateral
                    position['size'] -= abs(transaction.size_delta)
                    position['collateral'] -= abs(transaction.collateral_delta)

    # Close any remaining open positions
    for key in open_positions.keys():
        position = open_positions[key]
        end_price = transactions[-1].price
        start_price = position['average_open_price']
        size = position['size']
        collateral = position['collateral']
        trade = Trade(start_price, end_price, size, collateral)
        trades.append(trade)

    # Sort trades by the block number of the first transaction
    trades.sort(key=lambda t: t.start_block)

    return trades
