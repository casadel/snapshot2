import itertools
import numpy as np
import pandas as pd
import sys
import requests
import time
from bs4 import BeautifulSoup
import os

def get_nflx(link_dict, qtr):
    while True:
        page = requests.get(link_dict['NFLX'])
        soup = BeautifulSoup(page.text, 'html.parser')
        q_html = soup.find_all('div', {'class': 'accBody'})[0]
        docs = q_html.find_all('a')
        dwnload = []
        found = False
        for doc in docs:
            if doc.text == ‘%s16 Letter to shareholders' %qtr:
                link = doc['href']
                found = True
                break
        if found:
            break
        time.sleep(1)
    link = 'https://ir.netflix.com/' + link
    cmd = “start %s" %link
    os.system(cmd)

def get_amzn(link_dict, qtr):
    while True:
        page = requests.get(link_dict['AMZN'])
        soup = BeautifulSoup(page.text, 'html.parser')
        q_html = soup.find_all('div', {'class': 'a-section article-copy'})[0]
        docs = q_html.find_all('a')
        dwnload = []
        found = False
        for doc in docs:
            if doc.text == ‘%s 2016 Financial Results' %qtr:
                link = doc['href']
                found = True
                break
        if found:
            break
        time.sleep(1)
    cmd = “start %s" %link
    os.system(cmd)

def get_twtr(link_dict, qtr):
    while True: 
        page = requests.get(link_dict['TWTR'])
        soup = BeautifulSoup(page.text, 'html.parser')
        q_html = soup.find_all('div', {'class': 'ndq-expand-content'})[0]
        docs = q_html.find_all('a')
        dwnload = []
        found = False
        for doc in docs:
            if doc.text == “%s’ 2016 Shareholder Letter" %qtr:
                link = doc['href']
                found = True
                break
        if found:
            break
        time.sleep(1)
    link = 'https://investor.twitterinc.com/' + link
    cmd = “start %s" %link
    os.system(cmd)

tix = ['TWTR', 'TSLA', 'NFLX', 'AMZN']
links = ['https://investor.twitterinc.com/index.cfm', 'http://ir.tesla.com/', 'https://ir.netflix.com/results.cfm' ,'http://phx.corporate-ir.net/phoenix.zhtml?c=97664&p=irol-reportsOther']
ir_dict = dict(zip(tix, links))

globals()[“get_” + sys.argv[0]](ir_dict, sys.argv[1])



