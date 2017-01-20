# -*- coding: utf-8 -*-
import itertools
from bs4 import BeautifulSoup
import sys
import time
import requests
import os
import datetime
import threading
import winsound

def get_nypost(soup):
    article = soup.find('item')
    link = article.find('link').text
    authors = article.find('dc:creator').text.split(', ')
    if 'Josh Kosman' in authors or 'Claire Atkinson' in authors:
        return link
    else:
        return False

def get_citron(soup):
    article = soup.find('article')
    story_link = article.find('a')['href']
    link = 'http://citronresearch.com' + story_link
    return link

def get_muddy(soup):
    first_cell = soup.find('tbody').find('td')
    link = first_cell.find('a')['href']
    return link

def get_spruced(soup):
    story = soup.find('h2')
    link = story.find('a')['href']
    return link

def get_prescience(soup):
    story = soup.find('article').find('h6')
    link = story.find('a')['href']
    return link

def get_gotham(soup):
    article = soup.find('article')
    story_link = article.find('a')['href']
    link = 'http://citronresearch.com' + story_link
    return link

def get_fdanews(soup):
    table = soup.find_all('div', {'class': 'panel-body'})[0]
    article = table.find('li')
    link = article.find('a')['href']
    link = 'http://www.fda.gov' + link
    return link

def loop(watcher):
    while True:
    	try:
	    page = requests.get(watcher['url'])
            soup = BeautifulSoup(page.text, 'html.parser')
            link = watcher['selector'](soup)
        except Exception as e:
            print 'Scraping %s failed for some reason' %watcher['url']
            link = False
        if len(watcher['last_link'].keys()) > 0 and link not in watcher['last_link'] and link:
            cmd = 'start "" "C:\Program Files (x86)\Google\Chrome\Application\Chrome.exe" --new-window "%s"' %link
            os.system(cmd)
            winsound.Beep(440, 500)
            print str(datetime.datetime.now())
	watcher['last_link'][link] = True
        time.sleep(.5)


watchmen = [
    {
        'url': 'http://nypost.com/feed/',
        'selector': get_nypost,
        'last_link': {}
    },
    {
        'url': 'http://www.citronresearch.com/reports/',
        'selector': get_citron,
        'last_link': {}
    },
    {
        'url': 'http://www.muddywatersresearch.com/research/',
        'selector': get_muddy,
        'last_link': {}
    },
    {
        'url': 'http://www.sprucepointcap.com/research/',
        'selector': get_spruced,
        'last_link': {}
    },
    {
        'url': 'http://www.presciencepoint.com/research/',
        'selector': get_prescience,
        'last_link': {}
    },
    {
        'url': 'https://gothamcityresearch.com/research/',
        'selector': get_gotham,
        'last_link': {}
    },
    {
        'url': 'http://www.fda.gov/NewsEvents/Newsroom/PressAnnouncements/default.htm',
        'selector': get_fdanews,
        'last_link': {}
    }
]

for watcher in watchmen:
    t = threading.Thread(target=loop, args=(watcher,))
    t.daemon = True
    t.start()

while True:
    time.sleep(1)