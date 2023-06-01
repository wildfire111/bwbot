from classes import *
import json
from utils import *
#create_full_database()
#transactions = get_transactions_for_trader_from_db('0xd1c1d7ade57144f0b7bfad2aaf3e99d26fa89b29')
#trades = transactions_to_trades(transactions)
#trader = Trader('0xd1c1d7ade57144f0b7bfad2aaf3e99d26fa89b29',trades)
#print(trader.get_average_profit_percentage())
#print(trader.get_maximum_drawdown())
#print(trader.get_profitable_trades_percentage())
#print(trader.get_total_profit())
#for trade in trades:
#    print(trade)
#print(get_transaction_price(227178,'WBTC'))
#HumanParse(transactions)
#for tx in transactions:
#    print(tx)
trader_list = get_traders()
print(trader_list[0].get_profitable_trades_percentage())