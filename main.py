import sqlite3
from tqdm import tqdm
import extractor


        
def pullfromdb():
    con = sqlite3.connect('transactions.db')
    cur = con.cursor()
    cur.execute(f'SELECT * FROM transactions ORDER BY block ASC')
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
    return(traders)
    con.close()

def assesstrader(tradelist):
    finishedtrades = list()
    collateral = {
        'long':{'weth':0.0,'wbtc':0.0,'link':0.0,'uni':0.0},
        'short':{'weth':0.0,'wbtc':0.0,'link':0.0,'uni':0.0}
        }
    position = {
        'long':{
        'weth':{'price':0.0,'units':0.0},
        'wbtc':{'price':0.0,'units':0.0},
        'link':{'price':0.0,'units':0.0},
        'uni':{'price':0.0,'units':0.0}
        },
        'short':{
        'weth':{'price':0.0,'units':0.0},
        'wbtc':{'price':0.0,'units':0.0},
        'link':{'price':0.0,'units':0.0},
        'uni':{'price':0.0,'units':0.0}   
        }}
    for i,trade in enumerate(tradelist):
        print(i+1)
        direction = 'long' if trade['islong'] == 1 else 'short'
        multiplier = 1 if trade['islong'] == 1 else -1
        curpos = position[direction][trade['index']]
        cursize = curpos['price']*curpos['units']
        if trade['sizedelta'] > 0:
            units = trade['sizedelta']/trade['price']
            position[direction][trade['index']]['price'] = (cursize+trade['sizedelta'])/(curpos['units']+units)
            position[direction][trade['index']]['units'] += units
            collateral[direction][trade['index']] += trade['collatdelta']
            lev = position[direction][trade['index']]['units']*position[direction][trade['index']]['price']/collateral[direction][trade['index']]
            print(f"{trade['index']} {direction.capitalize()} position increase to {position[direction][trade['index']]['units']:.2f} units at ${position[direction][trade['index']]['price']} avg, leverage = {lev:.2f}")
            if trade['collatdelta'] > 0:
                print(f"Added ${trade['collatdelta']}, now {collateral[direction][trade['index']]}")
        elif trade['sizedelta'] < 0:
            unitdecrease = trade['sizedelta']/curpos['price']
            profit = (trade['price']-curpos['price'])*unitdecrease*multiplier
            percentprofit = profit/collateral[direction][trade['index']]
            position[direction][trade['index']]['units'] += unitdecrease
            collateral[direction][trade['index']] += trade['collatdelta']
            lev = position[direction][trade['index']]['units']*position[direction][trade['index']]['price']/collateral[direction][trade['index']]
            if trade['collatdelta'] == 0:
                if lev < 1:
                    print(f"Leverage is {lev}, position closed and collateral withdrawn.")
                    collateral[direction][trade['index']] = 0.0
            finalisedtrade = [trade['block'],percentprofit]
            finishedtrades.append(finalisedtrade)
            print(f"{trade['index']} Sold {unitdecrease*-1} units at {trade['price']} for a profit of {percentprofit*100}%. Leverage at {lev}")
        else:
            collateral[direction][trade['index']] += trade['collatdelta']
            print(f"{trade['index']} Collateral change of {trade['collatdelta']}")
        print('\n')
    return(finishedtrades)

con = sqlite3.connect('transactions.db')
cur = con.cursor()
try:            
    cur.execute('SELECT block FROM transactions ORDER BY block DESC LIMIT 1')
    targetblock = cur.fetchone()[0]+1
except:
    targetblock = 227091
con.close()
extractor.checktables()
extractor.updatedb(targetblock)

tradersandtrades = pullfromdb()
profitlist = dict()
for name,tradelist in tradersandtrades.items():
    print(name)
    profitlist[name] = assesstrader(tradelist)

for trader,profits in profitlist.items():
    total = 0
    for i in profits:
        total += i[1]
    print(f"Total PnL = {total*100:.2f}%")
    
    



