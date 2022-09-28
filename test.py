import sqlite3

con = sqlite3.connect('transactions.db')
cur = con.cursor()

cur.execute('SELECT COUNT (DISTINCT AccAddress) FROM transactions')
print(cur.fetchone())