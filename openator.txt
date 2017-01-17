{\rtf1\ansi\ansicpg1252\cocoartf1265\cocoasubrtf210
{\fonttbl\f0\fmodern\fcharset0 Courier;}
{\colortbl;\red255\green255\blue255;\red245\green245\blue245;\red38\green38\blue38;}
\margl1440\margr1440\vieww28600\viewh16220\viewkind0
\deftab720
\pard\pardeftab720

\f0\fs28 \cf0 \cb2 import itertools\
import numpy as np\
import pandas as pd\
import sys\
import requests\
import time\
from bs4 import BeautifulSoup\
import os\
\
def get_nflx(link_dict, qtr):\
    while True:\
        page = requests.get(link_dict['NFLX'])\
        soup = BeautifulSoup(page.text, 'html.parser')\
        q_html = soup.find_all('div', \{'class': 'accBody'\})[0]\
        docs = q_html.find_all('a')\
        dwnload = []\
        found = False\
        for doc in docs:\
            if doc.text == \'91%s16 Letter to shareholders' %qtr:\
                link = doc['href']\
                found = True\
                break\
        if found:\
            break\
        time.sleep(1)\
    link = 'https://ir.netflix.com/' + link\
    cmd = \'93start %s" %link\
    os.system(cmd)\
\
def get_amzn(link_dict, qtr):\
    while True:\
        page = requests.get(link_dict['AMZN'])\
        soup = BeautifulSoup(page.text, 'html.parser')\
        q_html = soup.find_all('div', \{'class': 'a-section article-copy'\})[0]\
        docs = q_html.find_all('a')\
        dwnload = []\
        found = False\
        for doc in docs:\
            if doc.text == \'91%s 2016 Financial Results' %qtr:\
                link = doc['href']\
                found = True\
                break\
        if found:\
            break\
        time.sleep(1)\
    cmd = \'93start %s" %link\
    os.system(cmd)\
\
def get_twtr(link_dict, qtr):\
    while True: \
        page = requests.get(link_dict['TWTR'])\
        soup = BeautifulSoup(page.text, 'html.parser')\
        q_html = soup.find_all('div', \{'class': 'ndq-expand-content'\})[0]\
        docs = q_html.find_all('a')\
        dwnload = []\
        found = False\
        for doc in docs:\
            if doc.text == \'93%s\'92 2016 Shareholder Letter" %qtr:\
                link = doc['href']\
                found = True\
                break\
        if found:\
            break\
        time.sleep(1)\
    link = 'https://investor.twitterinc.com/' + link\
    cmd = \'93start %s" %link\
    os.system(cmd)\
\
tix = ['TWTR', 'TSLA', 'NFLX', 'AMZN']\
links = ['https://investor.twitterinc.com/index.cfm', 'http://ir.tesla.com/', 'https://ir.netflix.com/results.cfm' ,'http://phx.corporate-ir.net/phoenix.zhtml?c=97664&p=irol-reportsOther']\
ir_dict = dict(zip(tix, links))\
\
globals()[\'93get_\'94 + sys.argv[0]](ir_dict, sys.argv[1])\
\
\
\cf3 \
}