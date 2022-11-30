#need to get weekly blocks
#then convert assessed trades into weekly blocks

import parser
import datetime
import time
from tqdm import tqdm

def getblockweekdelimiters():
    curblock = parser.gettableblock()
    initblock = 227091
    inittime = parser.gettimebyblock(initblock)
    itertime = parser.gettimebyblock(curblock) #returns as timestamp
    timestamplist = list()
    while itertime > inittime:
        timestamplist.append(itertime)
        itertime -= 604800 #1 week
    timestamplist.append(inittime)
    blocklist = list()
    pbar = tqdm(total=len(timestamplist))
    for timestamp in timestamplist:
        blocklist.append(parser.getblockbytime(timestamp))
        time.sleep(0.2)
        pbar.update(1)
    print(blocklist)
    
def main():
    getblockweekdelimiters()


if __name__ == '__main__':
    print('Running simlib.py')
    main()   

    