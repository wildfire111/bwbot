import sqlite3
from tqdm import tqdm
from dotenv import load_dotenv
import os

load_dotenv()

owner = os.getenv('OWNER')

con = sqlite3.connect('transactions.db')
cur = con.cursor()

class Trader:
    def __init__(self,accaddress:str,islong:bool,index:str,collatdelta:float,price:float,sizedelta:float) -> None:
        self.accaddress = accaddress
        self.islong = islong
        self.index = index
        self.collatdelta = collatdelta
        self.price = price
        self.sizedelta = sizedelta
        

cur.execute(f'SELECT * FROM transactions WHERE AccAddress = "{owner}" ORDER BY block ASC')
transactions = cur.fetchall()
traders = list()
for tx in transactions:
    traders.append(Trader('asd',True,'sdfs',1.1,1.1,1.2))
    print(traders)



