from web3 import Web3
import requests
import os
import json

from dotenv import load_dotenv
load_dotenv()
apikey = os.getenv('ALCH_KEY')
url = 'https://arb-mainnet.g.alchemy.com/v2/'+apikey

blockhex = Web3.toHex(24421014)
increasepostopic = '0x2fe68525253654c21998f35787a8d0f361905ef647c854092430ab65f2f15022'
decreasepostopic = '0x93d75d64d1f84fc6f430a64fc578bdd4c1e090e90ea2d51773e626d19de56d30'
tokenlist = {
    'wbtc':'0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f',
    'usdc':'0xff970a61a04b1ca14834a43f5de4533ebddb5cc8',
    'weth':'0x82af49447d8a07e3bd95bd0d56f35241523fbab1',
}
print(tokenlist)
payload = {
    "id": 1,
    "jsonrpc": "2.0",
    "method": "eth_getLogs",
    "params": [
        {
            "fromBlock": Web3.toHex(24421028),
            "toBlock": Web3.toHex(24421028),
            #"fromAddress": "0x3D6bA331e3D9702C5e8A8d254e5d8a285F223aba",
            "Address":"0x489ee077994B6658eAfA855C308275EAd8097C4A",
            #"blockHash":"0x0a063d41a043c0395f3b29dbf5eaf74f08a2eb609bd88ea0530d97dc18f3c8b5"
            #"contractAddresses": ["0x3D6bA331e3D9702C5e8A8d254e5d8a285F223aba"],
            #"category": ["external"],
            #"order": "asc",
            #"withMetadata": False,
            #"excludeZeroValue": True,
            #"maxCount": "0x3e8",
            #"pageKey": "string"
        }

    ]
}
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}
response = requests.post(url, json=payload, headers=headers)
if response.ok == True:
    print("TX OK")
else:
    print("OH NO")

respdict = response.json()
datatypes = ['Key','AccAddress','Collateral','Index','CollatDelta','SizeDelta','IsLong','Price','Fee']

#print(dict['result'][0]['address'])
for tx in respdict['result']:
#    print(Web3.toInt(hexstr=tx['blockNumber']))
    for txtopic in tx['topics']:
        if tx['topics'][0] != increasepostopic and tx['topics'][0] != decreasepostopic:
            break
        print(tx['transactionHash'])
        if tx['topics'][0] == increasepostopic:
            print('Position increasing')
        else:
            print('Position decreasing')
        txdata = tx['data']
        txdata = txdata[2:]
        txdatalist = list()
        if len(txdata)%64 != 0:
            print('Error in data')
            break
        parseddata = dict()
        for i in range(int(len(txdata)/64)):
            txdatalist.append(txdata[0:64])
            if len(txdata) != 0:
                txdata = txdata[64:]
        for i in range(len(txdatalist)):
            parseddata[datatypes[i]] = txdatalist[i]
        #print(parseddata)
        #Web3.toInt(hexstr=parseddata['CollatDelta'])
        parseddata['Collateral'] = (Web3.toHex(hexstr=parseddata['Collateral'][24:]))
        parseddata['Index'] = (Web3.toHex(hexstr=parseddata['Index'][24:]))
        parseddata['AccAddress'] = (Web3.toHex(hexstr=parseddata['AccAddress'][24:]))
        #print(Web3.toInt(hexstr=parseddata['Price']))
        parseddata['Price'] = Web3.toInt(hexstr=parseddata['Price'])/(10**30)
        parseddata['CollatDelta'] = Web3.toInt(hexstr=parseddata['CollatDelta'])/(10**30)
        parseddata['SizeDelta'] = Web3.toInt(hexstr=parseddata['SizeDelta'])/(10**30)
        parseddata['Fee'] = Web3.toInt(hexstr=parseddata['Fee'])/(10**30)
        for a,b in tokenlist.items():
            if parseddata['Collateral'] == b:
                parseddata['Collateral'] = a
            if parseddata['Index'] == b:
                parseddata['Index'] = a
        if parseddata['Collateral'] not in tokenlist or parseddata['Index'] not in tokenlist:
            print("Couldn't find a token")
        if int(parseddata['IsLong']) == 1:
            parseddata['IsLong'] = True
        else:
            parseddata['IsLong'] = False
        for key,value in parseddata.items():
            print(f"{key} - {value}")




#pretty = json.dumps(response.json(), indent=4)
#print(pretty)
