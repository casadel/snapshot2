# -*- coding: utf-8 -*-
import itertools
from bs4 import BeautifulSoup
import sys
import time
import requests
import os
import datetime
import threading

def get_nypost(soup):
    table = soup.find_all('div', {'class': 'site-content box'})[0]
    article = table.find('article').find('h3')
    title = article.text
    link = article.find('a')['href']
    return title, link

def get_nypost_news(soup):
    table = soup.find_all('div', {'id': 'primary'})[0]
    article = table.find('article').find('h3')
    title = article.text
    link = article.find('a')['href']
    return title, link

def get_citron(soup):
    article = soup.find('article')
    title = article.find('h2').text
    story_link = article.find('a')['href']
    link = 'http://citronresearch.com' + story_link
    return title, link

def get_muddy(soup):
    first_cell = soup.find('tbody').find('td')
    title = first_cell.text
    link = first_cell.find('a')['href']
    return title, link

def get_spruced(soup):
    story = soup.find('h2')
    title = story.text
    link = story.find('a')['href']
    return title, link

def get_prescience(soup):
    story = soup.find('article').find('h6')
    title = story.text
    link = story.find('a')['href']
    return title, link

def get_gotham(soup):
    article = soup.find('article')
    title = article.find('h2').text
    story_link = article.find('a')['href']
    link = 'http://citronresearch.com' + story_link
    return title, link

def get_fdanews(soup):
    table = soup.find_all('div', {'class': 'panel-body'})[0]
    article = table.find('li')
    title = article.text
    link = article.find('a')['href']
    link = 'http://www.fda.gov' + link
    return title, link

def loop(watcher):
    while True:
	page = requests.get(watcher['url'])
	soup = BeautifulSoup(page.text, 'html.parser')
	title, link = watcher['selector'](soup)
	if watcher['last_title'] is not None and title != watcher['last_title']:
	    cmd = 'start "" "C:\Program Files (x86)\Google\Chrome\Application\Chrome.exe" --new-window "%s"' %link
	    os.system(cmd)
	    print str(datetime.datetime.now())
	watcher['last_title'] = title
	time.sleep(1)


watchmen = [
    {
        'url': 'https://www.nypost.com/author/josh-kosman/',
        'selector': get_nypost,
        'last_title': None
    },
    {
        'url': 'https://www.nypost.com/author/claire-atkinson/',
        'selector': get_nypost,
        'last_title': None
    },
    {
        'url': 'http://nypost.com/news/',
        'selector': get_nypost_news,
        'last_title': None
    },
    {
        'url': 'http://www.citronresearch.com/reports/',
        'selector': get_citron,
        'last_title': None
    },
    {
        'url': 'http://www.muddywatersresearch.com/research/',
        'selector': get_muddy,
        'last_title': None
    },
    {
        'url': 'http://www.sprucepointcap.com/research/',
        'selector': get_spruced,
        'last_title': None
    },
    {
        'url': 'http://www.presciencepoint.com/research/',
        'selector': get_prescience,
        'last_title': None
    },
    {
        'url': 'https://gothamcityresearch.com/research/',
        'selector': get_gotham,
        'last_title': None
    },
    {
        'url': 'http://www.fda.gov/NewsEvents/Newsroom/PressAnnouncements/default.htm',
        'selector': get_fdanews,
        'last_title': None
    }
]

for watcher in watchmen:
    t = threading.Thread(target=loop, args=(watcher,))
    t.daemon = True
    t.start()

while True:
    time.sleep(1)
