import itertools
from bs4 import BeautifulSoup
import sys
import time
import requests
import os
import datetime
import threading
import json
import re

headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'
}

url = 'https://ecf.ded.uscourts.gov/cgi-bin/WrtOpRpt.pl'
payload = {'login': 'heusenvon', 'key': 'Ca$adelt'}
data = {'filed_from': '3/1/2017',
        'filed_to': '3/27/17'}

cookies = {}

page = requests.post(url, data = payload, headers=headers)
result = re.search('PacerSession=(.+?);', page.content)
cookies['PacerSession'] = result.group(1)

result = re.search('WrtOpRpt\.pl(\?\d+-L_1_0-1)', page.content)
suffix = result.group(1)

page2 = requests.post(url + suffix, data=data, cookies=cookies, headers=headers)

soup = BeautifulSoup(page2.text, 'html.parser')
print(soup)
