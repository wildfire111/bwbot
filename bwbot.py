from web3 import Web3
import requests
import os
import json

from dotenv import load_dotenv
load_dotenv()
apikey = os.getenv('ALCH_KEY')
url = 'https://arb-mainnet.g.alchemy.com/v2/'+apikey

blockhex = Web3.toHex(22473802)

payload = {
    "id": 1,
    "jsonrpc": "2.0",
    "method": "alchemy_getAssetTransfers",
    "params": [
        {
            "fromBlock": str(blockhex),
            "toBlock": "latest",
            #"fromAddress": "0x3D6bA331e3D9702C5e8A8d254e5d8a285F223aba",
            "toAddress": "0x3D6bA331e3D9702C5e8A8d254e5d8a285F223aba",
            #"contractAddresses": ["0x3D6bA331e3D9702C5e8A8d254e5d8a285F223aba"],
            "category": ["external"],
            "order": "asc",
            "withMetadata": False,
            "excludeZeroValue": True,
            "maxCount": "0x3e8",
#            "pageKey": "string"
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

#print(response.ok)

pretty = json.dumps(response.json(), indent=4)
print(pretty)
