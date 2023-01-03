#need to get weekly blocks
#then convert assessed trades into weekly blocks

import parser
import datetime
import time
from tqdm import tqdm

def getblockweekdelimiters():
    curblock = parser.gettableblock()
    initblock = 227091
    itertime = parser.gettimebyblock(initblock)
    finishtime = parser.gettimebyblock(curblock) #returns as timestamp
    timestamplist = list()
    blocklist = list()
    while itertime < finishtime:
        timestamplist.append(itertime)
        itertime += 604800 #1 week
    timestamplist.append(finishtime)
    blocklist = list()
    pbar = tqdm(total=len(timestamplist))
    timestamplist.pop(0)
    blocklist.append(initblock)
    for timestamp in timestamplist:
        blocklist.append(parser.getblockbytime(timestamp))
        time.sleep(0.2)
        pbar.update(1)
    pbar.close()
    return(blocklist)
    
def identifybesttraders():
    weeks = getblockweekdelimiters()
    best50weeklyavg = topxweeklyavg(50,weeks)

def topxweeklyavg(numtraders,weeks):
    print(weeks)
    fulltradelist = parser.pullfromdb()
    recentblock = weeks[-8]
    for trader,trades in fulltradelist.items():
        print(trader)
        #for trade in trades:
        #    print(trade)
        assessed = parser.assesstrader(trades,True)

def main():
    identifybesttraders()



if __name__ == '__main__':
    print('Running simlib.py')
    main()   

    