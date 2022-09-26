from web3 import Web3
import requests
import os
import json
from tqdm import tqdm
import sqlite3

from dotenv import load_dotenv
load_dotenv()
apikey = os.getenv('ALCH_KEY')
url = 'https://arb-mainnet.g.alchemy.com/v2/'+apikey
targetaddress = os.getenv('OWNER')

print('Running.')

con = sqlite3.connect('transactions.db')
cur = con.cursor()

#MAKE SURE YOU DELETE THIS BEFORE YOU GO LIVE LOL
try:
    cur.execute('DROP TABLE IF EXISTS tracker, transactions')
except:
    print("Tables don't exist, can't be dropped.")

try:
    cur.execute('SELECT recordedblock FROM tracker')
except:
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
        Timestamp Int
    )''')
#    cur.execute('CREATE TABLE usernames (AccAddress String, Name String)')

#cur.execute('SELECT AccAddress from usernames WHERE name NOT NULL')
#currentusers = list(cur.fetchall())

increasepostopic = '0x2fe68525253654c21998f35787a8d0f361905ef647c854092430ab65f2f15022'
decreasepostopic = '0x93d75d64d1f84fc6f430a64fc578bdd4c1e090e90ea2d51773e626d19de56d30'
startblock = 24421028
topiclist = ['0x2fe68525253654c21998f35787a8d0f361905ef647c854092430ab65f2f15022','0x93d75d64d1f84fc6f430a64fc578bdd4c1e090e90ea2d51773e626d19de56d30']


tokenlist = {
    'wbtc':'0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f',
    'usdc':'0xff970a61a04b1ca14834a43f5de4533ebddb5cc8',
    'weth':'0x82af49447d8a07e3bd95bd0d56f35241523fbab1',
    'wbtcalt':'0xfa7f8980b0f1e64a2062791cc3b0871572f1f7f0',
    'link':'0xf97f4df75117a78c1a5a0dbb814af92458539fb4',
    'usdt':'0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9',
    'dai':'0xda10009cbd5d07dd0cecc66161fc93d7c9000da1',
    'fxs':'0x9d2f299715d94d8a7e6f5eaa8e654e8c74a988a7',
    'frax':'0x17fc002b466eec40dae837fc4be5c67993ddbd6f'
    }

#getting current block
payload = {"jsonrpc": "2.0", "id": 0, "method": "eth_blockNumber"}
headers = {"Accept": "application/json","Content-Type": "application/json"}
response = requests.post(url, json=payload, headers=headers)
respdict = response.json()
curblock = Web3.toInt(hexstr=respdict['result'])
print(f"Current block: {curblock}")

multiplier = 1
datatypes = ['Key','AccAddress','Collateral','Index','CollatDelta','SizeDelta','IsLong','Price','Fee']

for txtopic in topiclist:
    if txtopic == '0x2fe68525253654c21998f35787a8d0f361905ef647c854092430ab65f2f15022':
        print('Extracting increases.')
        multiplier = 1
    else:
        print('Extracting decreases.')
        multiplier = -1
    pbar = tqdm(total=(curblock-startblock))
    while startblock < curblock:
        targetblock = startblock + 20000
        if targetblock > curblock:
            targetblock = curblock
        payload = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "eth_getLogs",
            "params": [
                {
                "fromBlock": "0x174a2a4",
                "toBlock": "0x177afe4",
                "address": "0x489ee077994B6658eAfA855C308275EAd8097C4A",
                "topics": [
                    txtopic
                    ]
                }
            ]
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.ok == False:
            targetblock = targetblock - 18000
            payload = {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "eth_getLogs",
                "params": [
                    {
                    "fromBlock": "0x174a2a4",
                    "toBlock": "0x177afe4",
                    "address": "0x489ee077994B6658eAfA855C308275EAd8097C4A",
                    "topics": [
                        txtopic
                        ]
                    }
                ]
            }
            response = requests.post(url, json=payload, headers=headers)
            if response.ok == False:
                print('Something went wrong with requesting transactions')
                break
        respdict = response.json()
        startblock = targetblock + 1
        executetext = 'INSERT INTO transactions VALUES '
        for tx in respdict['result']:
            txdata = tx['data']
            txdata = txdata[2:]
            parseddata = dict()
            for type in datatypes:
                parseddata[type] = txdata[0:64]
                txdata = txdata[64:]
            parseddata['AccAddress'] = (Web3.toHex(hexstr=parseddata['AccAddress'][24:]))
            parseddata['Collateral'] = (Web3.toHex(hexstr=parseddata['Collateral'][24:]))
            parseddata['Index'] = (Web3.toHex(hexstr=parseddata['Index'][24:]))
            parseddata['Price'] = Web3.toInt(hexstr=parseddata['Price'])/(10**30)
            parseddata['CollatDelta'] = Web3.toInt(hexstr=parseddata['CollatDelta'])/(10**30)*multiplier
            parseddata['SizeDelta'] = Web3.toInt(hexstr=parseddata['SizeDelta'])/(10**30)*multiplier
            parseddata['Fee'] = Web3.toInt(hexstr=parseddata['Fee'])/(10**30)
            for a,b in tokenlist.items():
                if parseddata['Collateral'] == b:
                    parseddata['Collateral'] = a
                if parseddata['Index'] == b:
                    parseddata['Index'] = a
            if parseddata['Collateral'] not in tokenlist or parseddata['Index'] not in tokenlist:
                print("Couldn't find a token")
                print(parseddata['Collateral'])
                print(parseddata['Index'])
                break
            if int(parseddata['IsLong']) == 1:
                parseddata['IsLong'] = True
            else:
                parseddata['IsLong'] = False
            cur.execute('INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?,NULL)', (
                parseddata['AccAddress'],
                parseddata['Collateral'],
                parseddata['Index'],
                parseddata['Price'],
                parseddata['CollatDelta'],
                parseddata['SizeDelta'],
                parseddata['Fee'],
                parseddata['IsLong'],
                Web3.toInt(hexstr=tx['blockNumber']),
                ))
        pbar.update(20000)
        con.commit()
