import sqlite3
from tqdm import tqdm
from dotenv import load_dotenv
import os

load_dotenv()

owner = os.getenv('OWNER')

con = sqlite3.connect('transactions.db')
cur = con.cursor()
        
def pullfromdb():
    global traders
    cur.execute(f'SELECT * FROM transactions WHERE AccAddress = "{owner}" ORDER BY block ASC')
    transactions = cur.fetchall()
    traders = dict()
    for tx in transactions:
        tradedict = dict()
        tradedict['index'] = tx[2]
        tradedict['price'] = tx[3]
        tradedict['collatdelta'] = tx[4]
        tradedict['sizedelta'] = tx[5]
        tradedict['fee'] = tx[6]
        tradedict['islong'] = tx[7]
        tradedict['block'] = tx[8]
        if tx[0] not in traders:
            traders[tx[0]] = list()
        traders[tx[0]].append(tradedict)

def assesstrader(tradelist):
    collateral = 0
    realisedlosses = 0
    position = {eth:0.0,btc:0.0,link:0.0}
    for trade in tradelist:
        if trade['index'] not in ['weth','wbtc','link']:
            break
        collateral = collateral + trade['collatdelta']
        realisedlosses += trade['fees']
        
    
#{'index': 'weth', 'price': 1359.52, 'collatdelta': 0,
# 'sizedelta': -13.9156, 'fee': 0.0139156, 'islong': 1, 'block': 25413877}
pullfromdb()

for name,trader in traders.items():
    for trade in trader:
        print(trade)
    
    



