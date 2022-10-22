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

#creates the tables if they don't exist
def checktables():
    con = sqlite3.connect('transactions.db')
    cur = con.cursor()
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
            TxHash String
        )''')
    con.commit()
    con.close()

def currentblock():
    #getting current block
    payload = {"jsonrpc": "2.0", "id": 0, "method": "eth_blockNumber"}
    headers = {"Accept": "application/json","Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    respdict = response.json()
    curblock = Web3.toInt(hexstr=respdict['result'])
    print(f"Current block: {curblock}")
    return curblock

#call this with whatever block you want to start with. 
def updatedb(beginblock):
    con = sqlite3.connect('transactions.db')
    cur = con.cursor()
    #Define topics for increasing and decreasing positions for finding tx's.
    topiclist = [
        '0x2fe68525253654c21998f35787a8d0f361905ef647c854092430ab65f2f15022',
        '0x93d75d64d1f84fc6f430a64fc578bdd4c1e090e90ea2d51773e626d19de56d30',
        '0x2e1f85a64a2f22cf2f0c42584e7c919ed4abe8d53675cff0f62bf1e95a1c676f']

    tokenlist = { #all the tokens that can be collateral
        'wbtc':'0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f',
        'usdc':'0xff970a61a04b1ca14834a43f5de4533ebddb5cc8',
        'weth':'0x82af49447d8a07e3bd95bd0d56f35241523fbab1',
        'uni':'0xfa7f8980b0f1e64a2062791cc3b0871572f1f7f0',
        'link':'0xf97f4df75117a78c1a5a0dbb814af92458539fb4',
        'usdt':'0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9',
        'dai':'0xda10009cbd5d07dd0cecc66161fc93d7c9000da1',
        'fxs':'0x9d2f299715d94d8a7e6f5eaa8e654e8c74a988a7',
        'frax':'0x17fc002b466eec40dae837fc4be5c67993ddbd6f',
        'mim':'0xfea7a6a0b346362bf88a9e4a88416b77a57d6c2a'
        }

    curblock = currentblock()

    multiplier = 1 #multiplied by size and collateral delta to make them negative if it's a decrease
    datatypes = ['Key','AccAddress','Collateral','Index','CollatDelta','SizeDelta','IsLong','Price','Fee']
    liqdatatypes = ['Key','AccAddress','Collateral','Index','IsLong','SizeDelta','CollatDelta','Fee','PnL','Price']
    pbar = tqdm(total=((curblock-beginblock)*3)) #progressbar init
    for txtopic in topiclist:
        startblock = beginblock
        if txtopic == '0x2fe68525253654c21998f35787a8d0f361905ef647c854092430ab65f2f15022':
            multiplier = 1
        else:
            multiplier = -1 #either a position decrease or liquidation
        
        while startblock < curblock:
            targetblock = startblock + 20000 #grabbing 20000 blocks of transactions
            if targetblock > curblock:
                targetblock = curblock #preventing overshooting past the current block so api requests don't fail
            payload = {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "eth_getLogs",
                "params": [
                    {
                    "fromBlock": Web3.toHex(startblock),
                    "toBlock": Web3.toHex(targetblock),
                    "address": "0x489ee077994B6658eAfA855C308275EAd8097C4A",
                    "topics": [
                        txtopic
                        ]
                    }
                ]
            }
            headers = {"Accept": "application/json","Content-Type": "application/json"}
            response = requests.post(url, json=payload, headers=headers)
            if response.ok == False:
                targetblock = targetblock - 18000 #if there are too many transactions in 20k blocks, api fails
                payload = {
                    "jsonrpc": "2.0",
                    "id": 0,
                    "method": "eth_getLogs",
                    "params": [
                        {
                        "fromBlock": Web3.toHex(startblock),
                        "toBlock": Web3.toHex(targetblock),
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
                    quit() 
            respdict = response.json()
            startblock = targetblock + 1 #making sure next request doesn't overlap
            for tx in respdict['result']:
                txdata = tx['data'] #everything we want is in data in one big block
                txdata = txdata[2:] #so we want to break it into useable chunks and assign to dictionary
                parseddata = dict()
                #If tx == liquidation
                if txtopic == '0x2e1f85a64a2f22cf2f0c42584e7c919ed4abe8d53675cff0f62bf1e95a1c676f':
                    curdatatypes = liqdatatypes
                else:
                    curdatatypes = datatypes
                for type in curdatatypes:
                    parseddata[type] = txdata[0:64]
                    txdata = txdata[64:]
                parseddata['AccAddress'] = (Web3.toHex(hexstr=parseddata['AccAddress'][24:]))
                parseddata['Collateral'] = (Web3.toHex(hexstr=parseddata['Collateral'][24:]))
                parseddata['Index'] = (Web3.toHex(hexstr=parseddata['Index'][24:]))
                parseddata['Price'] = Web3.toInt(hexstr=parseddata['Price'])/(10**30)
                parseddata['CollatDelta'] = Web3.toInt(hexstr=parseddata['CollatDelta'])/(10**30)*multiplier
                parseddata['SizeDelta'] = Web3.toInt(hexstr=parseddata['SizeDelta'])/(10**30)*multiplier
                parseddata['Fee'] = Web3.toInt(hexstr=parseddata['Fee'])/(10**30)
                else: #this is where we handle liquidations
                    
                for a,b in tokenlist.items():
                    if parseddata['Collateral'] == b: #assigning plaintext instead of hex address
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
                cur.execute('INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?,?)', (
                    parseddata['AccAddress'],
                    parseddata['Collateral'],
                    parseddata['Index'],
                    parseddata['Price'],
                    parseddata['CollatDelta'],
                    parseddata['SizeDelta'],
                    parseddata['Fee'],
                    parseddata['IsLong'],
                    Web3.toInt(hexstr=tx['blockNumber']),
                    tx['transactionHash']
                    ))
                    
            pbar.update(20000)
            con.commit() #saves to db every 20000 blocks
    pbar.close()
    con.close()

if __name__ == '__main__':
    checktables()
    updatedb('227091') #block that GMX contracts were created
