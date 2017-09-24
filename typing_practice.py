import pandas as pd
import numpy
from numpy import random
from datetime import datetime
from datetime import timedelta
import time
import atexit

amexdf=pd.read_csv("AMEX.csv")
nysedf=pd.read_csv("NYSE.csv")
qqqdf=pd.read_csv("NASDAQ.csv")

frames = [amexdf, nysedf, qqqdf]

exc_list_mstr = pd.concat(frames)

tix = []
for row, index in exc_list_mstr.iterrows():
    symbol = str(index.Symbol)
    name = str(index.Name)
    market_cap = int(index.MarketCap)
    sector = str(index.Sector)
    carat = '^' in symbol
    letters = symbol.isalpha()
    #sector_list = []
    #industry_list = []
    if carat == False and letters == True and market_cap > 1000000 and sector == 'Technology':
        tix.append((symbol, name))

        
sleep = range(2, 10, 3)        

times = []

def report_stats(times):
    avg = sum( times) / len(times)
    print '\n', avg

while True:
    try:
        time.sleep(3)
        t1 = datetime.now()
        random.shuffle(tix)
        symbol, name = tix.pop()
        print symbol
        inpt = raw_input()
        diff = datetime.now() - t1
        diff_str = str(diff)
        print diff_str, name
        times.append(diff.total_seconds())
    except KeyboardInterrupt:
        report_stats(times)
        raise

    