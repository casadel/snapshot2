import pandas as pd
import numpy
from numpy import random
from datetime import datetime
from datetime import timedelta
import time
import atexit
import random as rd
import re
import subprocess
import pygame


amexdf=pd.read_csv("AMEX.csv")
nysedf=pd.read_csv("NYSE.csv")
qqqdf=pd.read_csv("NASDAQ.csv")

frames = [amexdf, nysedf, qqqdf]

exc_list_mstr = pd.concat(frames)

tix = []
big_tix = []
for row, index in exc_list_mstr.iterrows():
    symbol = str(index.Symbol)
    industry = str(index.Industry)
    name = str(index.Name)
    sector = str(index.Sector)
    try:
        market_cap = float(index.MarketCap)
    except:
        market_cap=0
    carat = '^' in symbol
    letters = symbol.isalpha()
    #sector_list = []
    #industry_list = []
    if carat == False and letters == True and sector == 'Technology':
        if market_cap > 800000000 and market_cap < 20000000000:
            tix.append((symbol, name))
        if market_cap > 20000000000:
            big_tix.append((symbol, name))

        
sleep = range(2, 10, 3)        

times = []

def report_stats(times):
    n = len(times)
    N = len(tix) + n
    avg = sum( times) / n
    med = numpy.median(times)
    print '\nn:', n, '\nMEAN:', avg, '\nMEDIAN:', med, '\nN:', N

heads = ['__  DJ: --- in advanced talks to sell itself', 'BREAKING: --- hires bank to weigh sale after approach by @', 'Long $__ on potential infinity squeeze' , '__  *DJ @ in talks to buy ---', '__  *@ to acquire --- for $60/sh', '__  *@ Considers offer for ---', '__  *--- close to decision on sale', '__  *DJ --- hires advisors after receiving takeover interest','--- could be looking to sell', '@ nears deal to buy ---', '__  *DJ: Elliot reports 6.5% stake in ---', '__  DJ: Jana Partners taking stake in ---', '__  *DJ Icahn to push for sale at ---', '__  *--- fielding takeover interest', 'BREAKING: @ has made offer to buy ---', '@ in talks to buy ---', '#  DJ: @ in talks to buy ---', '--- in talks to sell itself to a British Retailer', 'Softbank definitely in talks with --- about merger', '__  *DJ @ preparing bid for ---', 'CITRON EXPOSES ___ -- PRICE TARGET $0', '--- named new short by Muddy Waters', '---: All Signs Point to Fraud', '__  *@ no longer interested in bid for ---', '__  DJ: @ abandons attempts to buy ---', '*@ no longer interested in bid for ---', '*DJ --- discussions to sell itself have broken down', 'COULD ___ BE THE NEXT VALEANT?', 'CITRON RESEARCH EXPOSES ___ AND PROVES BEYOND ANY DOUBT WHY THIS STOCK WILL SOON BE CUT IN HALF', 'Exclusive: SoftBank calling off talks to acquire ---', '__  *Kerrisdale Capital is short ---', '__  *Muddy Waters is short ---', '___: CITRON EXPOSES THE LAWSUITS THAT WILL WIPE OUT THE EQUITY', 'Short $__: Fraud penalties to exceed $100 million', '__  *DJ --- Has Concluded Strategic Review', '___: ENRON IN THE MAKING?', '\n\n\n__ DJ @ Held Takeover Talks With Aircraft Maker --- \n__ *DJ Deal Would Value --- at Large Premium to its $3.7B Market Cap -- Source \n__ *DJ Talks Are on Hold as Parties Seek Approval From Govt. -- Sources \n__ *DJ @ Held Takeover Talks With --- - Sources', '\n\n\n# *DJ --- Had Market Capitalization of $9.8B Friday Afternoon \n# *DJ Glencore Agreed to Standstill That Expires in Coming Weeks -- Sources \n# *DJ Approach Follows Glencore Overture to --- Last Year \n# *DJ @ Has Made Takeover Approach to --- -- Sources', '\n\n\n__ *DJ --- Had $53B Market Value Thursday Afternoon \n__ *DJ @ Is in Talks to Buy --- -- Sources', '\n\n\n# DJ @, --- Consider Merger \n# *DJ Companies Have Combined Enterprise Value of About $12 Billion \n# *DJ @ is Still Interested in Buying --- -- Sources \n# *DJ Companies Have Held On-Again, Off-Again Talks -- Sources \n# *DJ @, --- Consider Combination -- Sources', '\n\n\n__ *DJ FTC Investigates --- Over Negotiations With Customers \n__ *DJ FTC Probe Doesnt Focus on ---s Wireless Segment -- Sources \n__ *DJ FTC Recently Issued Subpoenas in --- Antitrust Probe -- Sources \n__ *DJ FTC Investigates --- Over Negotiations With Customers -- Sources', '\n\n\n__ *DJ Lab-Supply Distributor Had Market Value of About $3.75 Billion \n__ *DJ New Mountain Capital Nears Deal to Buy --- -- Sources', '\n\n\n# *DJ ---, a Cancer Biotech, Has a Market Cap of About $5.5B \n# *DJ @ Is in Talks to Buy --- -- Sources', '\n\n\n__ *DJ --- Had Market Value of $970 Million Friday Afternoon \n__ *DJ Company is Working with Centerview and MTS -- Sources \n__ *DJ --- Exploring a Potential Sale -- Sources']
     
pygame.init()
while True:
    try:
        time.sleep(2)
        t1 = datetime.now()
        random.shuffle(tix)
        symbol, name = tix.pop()
        symbol_b, name_b = rd.choice(big_tix)
        headline = rd.choice(heads)
        headline = re.sub('___', name.upper(), headline)
        headline = re.sub('__', symbol, headline)
        headline = re.sub('---', name, headline)
        headline = re.sub('#', symbol_b, headline)
        headline = re.sub('@', name_b, headline)
        if '\n' in headline:
            chord = 'chord.wav'
            chord = pygame.mixer.Sound(chord)
            chord.play() 
        print headline
        inpt = raw_input()
        while inpt != symbol:
            inpt = raw_input()
        diff = datetime.now() - t1
        diff_str = str(diff)
        print diff_str, symbol
        times.append(diff.total_seconds())
    except:
        print '\n', symbol
        report_stats(times)
        raise