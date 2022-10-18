import requests

apikey = 'NHPRBPYDJKFBWHDNIA86HPIMJ1KPPG7AWZ'
url = f"https://api.arbiscan.io/api?module=block&action=getblocknobytime&timestamp=1601510400&closest=before&apikey={apikey}"

response = requests.post(url)
print(response.ok)