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
    finishedtrades = list()
    collateral = {'weth':0.0,'btc':0.0,'link':0.0}
    position = {
        'long':{
        'weth':{'price':0.0,'units':0.0},
        'btc':{'price':0.0,'units':0.0},
        'link':{'price':0.0,'units':0.0}
        },
        'short':{
        'weth':{'price':0.0,'units':0.0},
        'btc':{'price':0.0,'units':0.0},
        'link':{'price':0.0,'units':0.0}    
        }}
    for trade in tradelist:
        direction = 'long' if trade['islong'] == 1 else 'short'
        curpos = position[direction][trade['index']]
        cursize = curpos['price']*curpos['units']
        if trade['sizedelta'] > 0:
            units = trade['sizedelta']/trade['price']
            position[direction][trade['index']]['price'] = (cursize+trade['sizedelta'])/(curpos['units']+units)
            position[direction][trade['index']]['units'] += units
            collateral[trade['index']] += trade['collatdelta']
            print(f'''{direction.capitalize()} position increase to {position[direction][trade['index']]['units']} units
at ${position[direction][trade['index']]['price']} avg,
leverage = {position[direction][trade['index']]['units']*position[direction][trade['index']]['price']/collateral[trade['index']]}''')
            if trade['collatdelta'] > 0:
                print(f"Added ${trade['collatdelta']}, now {collateral[trade['index']]}")
        elif trade['sizedelta'] < 0:
            unitdecrease = trade['sizedelta']/curpos['price']
            profit = (trade['price']-curpos['price'])*unitdecrease
            percentprofit = profit/collateral[trade['index']]
            position[direction][trade['index']]['units'] += unitdecrease
            collateral[trade['index']] += trade['collatdelta']
            lev = position[direction][trade['index']]['units']*position[direction][trade['index']]['price']/collateral[trade['index']]
            if trade['collatdelta'] == 0:
                if lev < 1:
                    if lev > 0:
                        print(f"LEVERAGE FUCKED UP CHECK YOUR CODE, LEV: {lev}")
                    print(f"Leverage is {lev}, position closed and collateral withdrawn.")
                    collateral[trade['index']] = 0.0
            finalisedtrade = [trade['block'],percentprofit]
            finishedtrades.append(finalisedtrade)
            print(f"Sold {unitdecrease*-1} units at {trade['price']} for a profit of {percentprofit*100}%. Leverage at {lev}")
        else:
            collateral[trade['index']] += trade['collatdelta']
            print(f"Collateral change of {trade['collatdelta']}")
        print('/')
    return(finishedtrades)
            
            
        
        
    
#{'index': 'weth', 'price': 1359.52, 'collatdelta': 0,
# 'sizedelta': -13.9156, 'fee': 0.0139156, 'islong': 1, 'block': 25413877}
pullfromdb()
profitlist = dict()
for name,tradelist in traders.items():
    profitlist[name] = assesstrader(tradelist)
print(profitlist)
for trader,profits in profitlist.items():
    total = 0
    for i in profits:
        total += i[1]
    print(f"Total PnL = {total*100:.2f}%")
    
    



