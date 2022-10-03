import sqlite3
from tqdm import tqdm
from dotenv import load_dotenv
import os

load_dotenv()

owner = os.getenv('OWNER')

con = sqlite3.connect('transactions.db')
cur = con.cursor()

cur.execute(f'SELECT * FROM transactions WHERE AccAddress = "{owner}"')
transactions = cur.fetchall()
for tx in transactions:
    print(tx)


