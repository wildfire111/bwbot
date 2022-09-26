from web3 import Web3
from tqdm import tqdm
import sqlite3
import os
import requests
import json
from dotenv import load_dotenv
load_dotenv()

apikey = os.getenv('ALCH_KEY')
url = 'https://arb-mainnet.g.alchemy.com/v2/'+apikey

def gettimestamp(blockid):
    payload = {"jsonrpc":"2.0","id":0,"method":"eth_getBlockByNumber","params":[Web3.toHex(blockid),False]}
    headers = {"Accept": "application/json","Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    if response.ok != True:
        print('No dice.')
        print(response.json())
        return
    respdict = response.json()
    timestamphex = respdict['result']['timestamp']
    return(Web3.toInt(hexstr=timestamphex))

target = input('Target wallet: ')
if target == '':
    target = os.getenv('OWNER')

con = sqlite3.connect('transactions.db')
cur = con.cursor()

cur.execute('SELECT * FROM transactions WHERE AccAddress = ?',(target,))
print(cur.fetchone())