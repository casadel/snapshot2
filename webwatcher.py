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
    damelos = ['Josh Kosman', 'Claire Atkinson', 'Associated Press']
    if any(damelo in authors for damelo in damelos):
        return link
    else:
        return False

def get_rss(soup):
    article = soup.find('item')
    link = article.find('link').text
    return link

def get_gotham(soup):
    article = soup.find('article')
    link = article.find('a')['href']
    return link

def get_street(soup):
    article = soup.find_all('div', {'class': 'news-list__item'})[0]
    link = artlcle.find('a')['href']
    author = article.find_all('div', {'class': 'news-list__author-name'})[0].text
    damelo = 'Adam Feuerstein'
    if author == damelo:
        return link
    else:
        return false

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
        'url': 'http://www.citronresearch.com/feed',
        'selector': get_rss,
        'last_link': {}
    },
    {
        'url': 'http://www.muddywatersresearch.com/feed/?post_type=reports',
        'selector': get_rss,
        'last_link': {}
    },
    {
        'url': 'http://www.sprucepointcap.com/research/feed',
        'selector': get_rss,
        'last_link': {}
    },
    {
        'url': 'http://www.presciencepoint.com/research/feed',
        'selector': get_rss,
        'last_link': {}
    },
    {
        'url': 'http://www.fda.gov/AboutFDA/ContactFDA/StayInformed/RSSFeeds/PressReleases/rss.xml',
        'selector': get_rss,
        'last_link': {}
    },
    #{
    #    'url': 'http://apps.shareholder.com/rss/rss.aspx?channels=7196&companyid=ABEA-4CW8X0&sh_auth=3100301180%2E0%2E0%2E42761%2Eb96f9d5de05fc54b98109cd0d905924d',
    #    'selector': get_rss,
    #    'last_link': {}
    #}
    # Requests.get(thestreet_url) returns response 404!!
    #{
    #    'url': 'https://www.thestreet.com',
    #    'selector': get_street,
    #    'last_link': {}
    #},
    {
        'url': 'https://gothamcityresearch.com/research/',
        'selector': get_gotham,
        'last_link': {}
    }
]

for watcher in watchmen:
    t = threading.Thread(target=loop, args=(watcher,))
    t.daemon = True
    t.start()

while True:
    time.sleep(1)
