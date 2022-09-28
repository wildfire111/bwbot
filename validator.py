import sqlite3
from tqdm import tqdm

con = sqlite3.connect('transactions.db')
cur = con.cursor()

cur.execute('SELECT DISTINCT AccAddress FROM transactions')
users = cur.fetchall()
print(f'Users: {len(users)}')

pbar = tqdm(total=len(users))
#for user in users:
#    cur.execute(f'SELECT * FROM transactions WHERE AccAddress = "{user[0]}" ORDER BY block ASC LIMIT 1')
#    tx = cur.fetchone()
#    if tx[4] <= 0:
#        print(tx)
#    pbar.update(1)

cur.execute('SELECT AccAddress, MIN(block), CollatDelta FROM transactions GROUP BY AccAddress ORDER BY MIN(block) ASC')
txlist = cur.fetchall()
for tx in txlist:
    if tx[2] <= 0:
        print(tx)
    pbar.update(1)
