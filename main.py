print('running...')
import sqlite3
from tqdm import tqdm
import extractor
import datetime
import requests
import os
import time
import json
from web3 import Web3
from dotenv import load_dotenv
load_dotenv()
apikey = os.getenv('ALCH_KEY')
arbiapi = os.getenv('ARBI')
alchurl = 'https://arb-mainnet.g.alchemy.com/v2/'+apikey




        
def pullfromdb(trader=False):
    con = sqlite3.connect('transactions.db')
    cur = con.cursor()
    if trader != False:
        cur.execute(f'SELECT * FROM transactions WHERE AccAddress = "{trader}" ORDER BY block ASC')
    else:
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

def assesstrader(tradelist): #input list of trades, returns dict of finalised trades {block:profit,}
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
        #print(i+1)
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
            #if trade['collatdelta'] > 0:
            #print(f"Added ${trade['collatdelta']}, now {collateral[direction][trade['index']]}")
        elif trade['sizedelta'] < 0:
            unitdecrease = trade['sizedelta']/curpos['price']
            profit = (trade['price']-curpos['price'])*(unitdecrease*-1)*multiplier
            percentprofit = profit/collateral[direction][trade['index']]
            position[direction][trade['index']]['units'] += unitdecrease
            collateral[direction][trade['index']] += trade['collatdelta']
            lev = position[direction][trade['index']]['units']*position[direction][trade['index']]['price']/collateral[direction][trade['index']]
            if trade['collatdelta'] == 0:
                if (position[direction][trade['index']]['units']*trade['price']) < 5:
                    #print(f"Leverage is {lev}, position closed and collateral withdrawn.")
                    collateral[direction][trade['index']] = 0.0
                    position[direction][trade['index']]['units'] = 0
                    position[direction][trade['index']]['price'] = 0
            finalisedtrade = [trade['block'],percentprofit]
            finishedtrades.append(finalisedtrade)
            print(f"{trade['index']} Sold {unitdecrease*-1} units at {trade['price']} for a profit of {percentprofit*100}%. Leverage at {lev}")
        else:
            collateral[direction][trade['index']] += trade['collatdelta']
            print(f"{trade['index']} Collateral change of {trade['collatdelta']}")
        print('\n')
    return(finishedtrades)

def gettableblock():
    con = sqlite3.connect('transactions.db')
    cur = con.cursor()
    try:            
        cur.execute('SELECT block FROM transactions ORDER BY block DESC LIMIT 1')
        tabblock = cur.fetchone()[0]+1
    except:
        tabblock = 227091
    con.close()
    return(tabblock)

def getblockbytime(timestamp):
    arbiurl = f'https://api.arbiscan.io/api?module=block&action=getblocknobytime&timestamp={timestamp}&closest=before&apikey={arbiapi}'
    response = requests.post(arbiurl)
    time.sleep(0.2) #api is limited to 5 requests a second
    if response.json()['status'] != 0:
        return response.json()['result']
    else:
        print('error in getting block by time')
        return(False)

def gettimebyblock(block):
    block = Web3.toHex(block)
    payload = {"jsonrpc": "2.0", "id": 0, "method": "eth_getBlockByNumber", "params": [block,False]}
    headers = {"Accept": "application/json","Content-Type": "application/json"}
    response = requests.post(alchurl, json=payload, headers=headers)
    respdict = response.json()
    return Web3.toInt(hexstr=respdict['result']['timestamp'])

def findbest():
    traderlist = pullfromdb()
    weeksback = int(input('How many weeks to go back and compare previous performance against: '))
    weeks = datetime.datetime.utcnow() - datetime.timedelta(days=(7*weeksback))
    splitblock = int(getblockbytime(round(weeks.timestamp())))
    for trader,trades in traderlist.items():
        countforward = 0
        countback = 0
        if trades[0]['block'] > splitblock:
            continue
        for trade in trades:
            if trade['block'] > int(splitblock):
                countforward += 1
            else:
                countback += 1
        if countforward < (2*weeksback) or countback < 30:
            continue #This makes sure the trader has made more than 3 trades a week in the comparing period.
        profits = assesstrader(trades)
        sum = 0
        for trade in profits:
            sum += trade[1]
        if sum < 0:
            continue
        profit = 0
        for trade in profits:
            profit += trade[1]    
        days = (datetime.datetime.utcnow()-datetime.datetime.fromtimestamp(gettimebyblock(trades[0]['block']))).days
        profit = profit/days
        if profit < 0.05:
            continue
        print(f"{trader} {round((1+(profit/10))**365,2)}%")

def checktrader(trader):
    trades = pullfromdb(trader)[f'{trader}']
    print(assesstrader(trades))

checktrader("0x487a2fd64096f90f19caa57b34b0714a2e8f6be7")  
        

        

#extractor.checktables()
#extractor.updatedb(gettableblock())

#tradersandtrades = pullfromdb()
#profitlist = dict()
#pbar = tqdm(total=len(tradersandtrades))
##for name,tradelist in tradersandtrades.items():
#    profitlist[name] = assesstrader(tradelist)
#    pbar.update(1)
#pbar.close()

#for trader,profits in profitlist.items():
#    total = 0
#    for i in profits:
#        total += i[1]
#    print(f"Total PnL = {total*100:.2f}%")

#seconds since contract genesis

    



