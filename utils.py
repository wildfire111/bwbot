from web3 import Web3
import requests
import os
import json
from tqdm import tqdm
import sqlite3
from classes import *
from tqdm import tqdm

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
    con = sqlite3.connect('TransactionList.db')
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
    con = sqlite3.connect('TransactionList.db')
    cur = con.cursor()
    cur.execute('''CREATE TABLE transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_address TEXT,
        collateral_type TEXT,
        underlying_token TEXT,
        price REAL,
        collateral_delta REAL,
        size_delta REAL,
        fee REAL,
        is_long BOOLEAN,
        block_number INTEGER,
        tx_hash TEXT
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
    INITIAL_CHUNK_SIZE = 250000
    CHUNK_INCREMENT_FACTOR = 0.005  # 0.5% increment
    CHUNK_DECREMENT_FACTOR = 0.10  # 10% decrement
    MIN_CHUNK_SIZE = 10000
    MAX_RETRIES = 20
    current_block = GetCurrentBlock()
    responses = []

    if start_block > current_block:
        raise ValueError("Start block is greater than the current block.")

    from_block = start_block
    total_blocks = current_block - start_block + 1
    pbar = tqdm(total=total_blocks, desc='Progress', unit='block')

    chunk_size = INITIAL_CHUNK_SIZE

    while from_block <= current_block:
        to_block = min(from_block + chunk_size - 1, current_block)
        retries = 0
        success = False

        while chunk_size >= MIN_CHUNK_SIZE and retries < MAX_RETRIES:
            response = GetBlocksByTopic(from_block, to_block, topic)
            json_response = response.json()
            if 'error' not in json_response:
                results = json_response.get('result', [])  # Extract the 'result' list
                for result in results:
                    address = result.get('address', '')
                    data = result.get('data', '')
                    # Modify the data field as required
                    data = data[2:]  # Drop the first two characters
                    data = [data[i:i+64] for i in range(0, len(data), 64)]  # Split every 64 characters
                    if topic == '0x2e1f85a64a2f22cf2f0c42584e7c919ed4abe8d53675cff0f62bf1e95a1c676f':
                        account_address = data[1]
                        collateral_type_hex = data[2]
                        underlying_token_hex = data[3]
                        collateral_delta = -1e300
                        size_delta = -1e300
                        islongint = int(data[4])
                        price = 0
                        fee = 0
                    else:
                        account_address = data[1]
                        collateral_type_hex = data[2]
                        underlying_token_hex = data[3]
                        collateral_delta = data[4]
                        collateral_delta = Web3.toInt(hexstr=collateral_delta)/(10**30)
                        size_delta = data[5]
                        size_delta = Web3.toInt(hexstr=size_delta)/(10**30)
                        islongint = int(data[6])
                        price = data[7]
                        price = Web3.toInt(hexstr=price)/(10**30)
                        fee = data[8]
                        fee = Web3.toInt(hexstr=fee)/(10**30)
                    if islongint > 0:
                        is_long = True
                    else:
                        is_long = False
                    #if position decrease
                    if topic == '0x93d75d64d1f84fc6f430a64fc578bdd4c1e090e90ea2d51773e626d19de56d30':
                        size_delta *= -1
                        collateral_delta *= -1
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
                        price,
                        collateral_delta,
                        size_delta,
                        fee,
                        is_long,
                        result.get('blockNumber', ''),
                        result.get('transactionHash', '')
                    )
                    #print(newtrade)
                    responses.append(newtrade)

                success = True
                chunk_size = chunk_size + int(chunk_size * CHUNK_INCREMENT_FACTOR)
                break
            else:
                chunk_size = max(int(chunk_size - chunk_size * CHUNK_DECREMENT_FACTOR), MIN_CHUNK_SIZE)
                to_block = min(from_block + chunk_size - 1, current_block)
                retries += 1

        if retries >= MAX_RETRIES and not success:
            raise RuntimeError("Exceeded maximum retry limit for fetching logs.")

        from_block = to_block + 1
        pbar.update(chunk_size)

    pbar.close()
    return responses


def get_transactions_for_trader_from_db(trader_address: str) -> list:
    # Open the database and retrieve transactions for the specified trader
    conn = sqlite3.connect("TransactionList.db")
    c = conn.cursor()
    c.execute("SELECT * FROM transactions WHERE account_address=?", (trader_address,))
    rows = c.fetchall()
    conn.close()

    # Create Transaction objects for each row and sort by block number
    transactions = []
    for row in rows:
        transaction = Transaction(row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],row[9],row[10])
        transactions.append(transaction)
    transactions.sort(key=lambda t: t.block_number)
    
    return transactions

def transactions_to_trades(transactions: list) -> list:
    trades = []  # List to store the resulting trades
    open_positions = {}  # Dictionary to track open positions
    
    # Sort the transactions based on the block number
    transactions.sort(key=lambda t: t.block_number)
    
    for transaction in transactions:
        key = (transaction.underlying_token, transaction.is_long)
        
        if transaction.size_delta > 0:  # Opening a new position
            if key not in open_positions:  # If position doesn't exist, create a new one
                open_positions[key] = {
                    'size_dollars': max(transaction.size_delta, 0),
                    'collateral_value': max(transaction.collateral_delta, 0),
                    'average_open_price': transaction.price
                }
            else:  # Position already exists, update the position
                position = open_positions[key]
                new_size_dollars = position['size_dollars'] + transaction.size_delta
                new_collateral_value = position['collateral_value'] + transaction.collateral_delta
                current_units = position['size']/position['average_open_price']
                added_units = transaction.size_delta/transaction.price
                new_average_open_price = (position['size']+transaction.size_delta)/(current_units+added_units)
                position['size_dollars'] = max(new_size_dollars, 0)
                position['collateral_value'] = max(new_collateral_value, 0)
                position['average_open_price'] = new_average_open_price
        else:  # Closing a position
            if key in open_positions:  # If position exists, close it
                position = open_positions[key]
                if abs(transaction.size_delta) >= position['size_dollars']:
                    # Generate a trade for the closed position
                    end_price = transaction.price
                    start_price = position['average_open_price']
                    size_dollars = position['size_dollars']
                    collateral_value = position['collateral_value']
                    trade = Trade(transaction.block_number, start_price, end_price, size_dollars, collateral_value)
                    trades.append(trade)
                    del open_positions[key]  # Remove the closed position from the dictionary
                else:  # Update the open position and generate a trade for the closed part
                    closed_size_dollars = abs(transaction.size_delta)
                    closed_collateral_value = abs(transaction.collateral_delta)
                    position['size_dollars'] -= closed_size_dollars
                    position['collateral_value'] -= closed_collateral_value
                    start_price = position['average_open_price']
                    end_price = transaction.price
                    size_dollars = closed_size_dollars
                    collateral_value = closed_collateral_value
                    trade = Trade(transaction.block_number, start_price, end_price, size_dollars, collateral_value)
                    trades.append(trade)
    
    # Generate trades for the remaining open positions
    for key in open_positions.keys():
        position = open_positions[key]
        end_price = None
        search_block = transactions[-1].block_number
        while end_price is None:
            if search_block < 0:
                raise ValueError("Invalid search block. No transaction found.")
            end_price = get_transaction_price(key[0],search_block)
            search_block -= 1
        start_price = position['average_open_price']
        size_dollars = position['size_dollars']
        collateral_value = position['collateral_value']
        trade = Trade(transactions[-1].block_number, start_price, end_price, size_dollars, collateral_value)
        trades.append(trade)
    
    # Sort the trades based on the finalized block number
    trades.sort(key=lambda t: t.finalized_block)
    
    return trades




def create_full_database():
    # Check if the database exists
    if not os.path.exists('TransactionList.db'):
        # If the database doesn't exist, create the tables
        CreateTables()

    # Define the topics to fetch logs for
    topics = ['0x2fe68525253654c21998f35787a8d0f361905ef647c854092430ab65f2f15022', '0x93d75d64d1f84fc6f430a64fc578bdd4c1e090e90ea2d51773e626d19de56d30', '0x2e1f85a64a2f22cf2f0c42584e7c919ed4abe8d53675cff0f62bf1e95a1c676f']

    # Iterate over the topics
    for topic in topics:
        # Fetch logs using GetBlocksByTopicInChunks
        logs = GetAllLogsByTopicInChunks(0, topic)

        # Insert the transactions into the database
        conn = sqlite3.connect('TransactionList.db')
        c = conn.cursor()

        with tqdm(total=len(logs), desc=f'Processing topic: {topic}') as pbar:
            for log in logs:
                # Insert the transaction into the database
                query = log.get_sql_query()
                c.execute(query)
                pbar.update(1)

        conn.commit()
        conn.close()
        
import sqlite3

def get_transaction_price(block_number, underlying_token):
    # Establish a connection to your SQLite database
    conn = sqlite3.connect('TransactionList.db')
    cursor = conn.cursor()

    # Write your SQLite query to retrieve the price based on block number and underlying token
    query = f"""
        SELECT price
        FROM transactions
        WHERE block_number = {block_number} AND underlying_token = \"{underlying_token}\"
    """

    # Execute the query and fetch the result
    cursor.execute(query)
    result = cursor.fetchone()

    # Close the database connection
    conn.close()

    # Check if a result is found and return the price
    if result is not None:
        return result[0]  # Assuming the price is stored in the first column of the result
    else:
        return None  # Return None if no matching transaction is found

def HumanParse(transactions):
    sorted_transactions = sorted(transactions, key=lambda t: t.block_number)
    for transaction in sorted_transactions:
        underlying_token = transaction.underlying_token
        collateral_delta = transaction.collateral_delta
        size_delta = transaction.size_delta
        is_long = transaction.is_long
        
        if size_delta < 0 and abs(size_delta) > 1e299:
            # Liquidation
            print(f"Liquidated {'long' if is_long else 'short'} on {underlying_token}.")
        elif size_delta > 0:
            position_type = "long" if is_long else "short"
            position_size = abs(size_delta)
            leverage = size_delta / collateral_delta if collateral_delta != 0 else 0

            print(f"Increased {position_type} on {underlying_token}. Position size increased by ${position_size:.2f}. Leverage: {leverage:.2f}x.")
        elif size_delta < 0:
            position_type = "long" if is_long else "short"
            position_size = abs(size_delta)
            leverage = size_delta / collateral_delta if collateral_delta != 0 else 0

            print(f"Decreased {position_type} on {underlying_token}. Position size decreased by ${position_size:.2f}. Leverage: {leverage:.2f}x.")
        else:
            collateral_change = collateral_delta
            change_message = "increased" if collateral_change > 0 else "decreased"
            print(f"Changed collateral on {underlying_token}. Collateral {change_message} by ${abs(collateral_change):.2f}.")
