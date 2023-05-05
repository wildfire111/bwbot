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