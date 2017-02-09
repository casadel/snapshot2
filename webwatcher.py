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
    damelos = ['Josh Kosman', 'Claire Atkinson']
    if any(damelo in authors for damelo in damelos):
        return link, link
    else:
        return False, False

def get_rss(soup):
    article = soup.find('item')
    link = article.find('link').text
    return link, link

def get_ctfn(soup):
    last_pubs = soup.find_all('ul', {'class': 'last-published-contents'})[0]
    last_symbol = last_pubs.find('li').find('strong').text
    url = 'http://ctfn.news/'
    return last_symbol, url

def get_dcd(soup):
    case = soup.find('item')
    url = 'https://ecf.dcd.uscourts.gov/cgi-bin/rss_outside.pl'
    title = case.find('title').text
    case_number = '1:16-cv-01493' #US v ANTM
    if case_number in title:
        return title, url
    else:
        return False, False

def get_ded(soup):
    case = soup.find('item')
    url = 'https://ecf.ded.uscourts.gov/cgi-bin/rss_outside.pl'
    title = case.find('title').text
    case_numbers = ['1:16-cv-01267', '1:16-cv-01243'] #JUNO-KITE TEVA-various
    if any(case_number in title for case_number in case_numbers):
        return title, url
    else:
        return False, False

def get_cafc(soup):
    url = 'https://ecf.cafc.uscourts.gov/cmecf/servlet/TransportRoom?servlet=RSSGenerator'
    case = soup.find('item')
    title = case.find('title').text
    case_numbers = ['17-1480', '17-1575'] #AMGN-SNY TEVA-Sandoz 
    if any(case_number in title for case_number in case_numbers):
        return title, url
    else:
        return False, False

def get_interference(soup):
    url = 'https://acts.uspto.gov/ifiling/PublicView.jsp?identifier=106048&identifier2=null&tabSel=4&action=filecontent&replyTo=PublicView.jsp'
    doc_num = soup.find_all('tr', {'class': 'odd'})[0].find_all('td')[1].text
    return doc_num, url

def loop(watcher):
    while True:
        try:
	    headers = {
		'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'
	    }

            page = requests.get(watcher['url'], headers=headers)
            soup = BeautifulSoup(page.text, 'html.parser')
            link, url = watcher['selector'](soup)
        except Exception as e:
            print 'Scraping %s failed for some reason' %watcher['url'], str(datetime.datetime.now())
            link = False
        if len(watcher['last_link'].keys()) > 0 and link not in watcher['last_link'] and link:
            cmd = 'start "" "C:\Program Files (x86)\Google\Chrome\Application\Chrome.exe" --new-window "%s"' %url
            os.system(cmd)
            winsound.Beep(440, 500)
            print str(datetime.datetime.now())
        watcher['last_link'][link] = True
        time.sleep(watcher['delay'])


watchmen = [
    {
        'url': 'http://nypost.com/feed/',
        'selector': get_nypost,
        'delay': .5
    },
    {
        'url': 'http://www.citronresearch.com/feed',
        'selector': get_rss,
        'delay': .5
    },
    {
        'url': 'http://www.muddywatersresearch.com/feed/?post_type=reports',
        'selector': get_rss,
        'delay': .5
    },
    {
        'url': 'http://www.sprucepointcap.com/research/feed',
        'selector': get_rss,
        'delay': .5
    },
    {
        'url': 'http://www.presciencepoint.com/research/feed',
        'selector': get_rss,
        'delay': .5
    },
    {
        'url': 'http://www.fda.gov/AboutFDA/ContactFDA/StayInformed/RSSFeeds/PressReleases/rss.xml',
        'selector': get_rss,
        'delay': .5
    },
    #{
    #    'url': 'http://apps.shareholder.com/rss/rss.aspx?channels=7196&companyid=ABEA-4CW8X0&sh_auth=3100301180%2E0%2E0%2E42761%2Eb96f9d5de05fc54b98109cd0d905924d',
    #    'selector': get_rss,
    #    'delay': .5
    #},
    {
        'url': 'http://ctfn.news/',
        'selector': get_ctfn,
        'delay': .5
    },
    {
        'url': 'https://ecf.dcd.uscourts.gov/cgi-bin/rss_outside.pl',
        'selector': get_dcd,
        'delay': 3
    },
    {
        'url': 'https://ecf.ded.uscourts.gov/cgi-bin/rss_outside.pl',
        'selector': get_ded,
        'delay': 3
    },
    {
        'url': 'https://ecf.cafc.uscourts.gov/cmecf/servlet/TransportRoom?servlet=RSSGenerator',
        'selector': get_cafc,
        'delay': 4
    },
    {
        'url': 'https://acts.uspto.gov/ifiling/PublicView.jsp?identifier=106048&identifier2=null&tabSel=4&action=filecontent&replyTo=PublicView.jsp',
        'selector': get_interference,
        'delay': 1
    }
]

for watcher in watchmen:
    watcher['last_link'] = {}
    t = threading.Thread(target=loop, args=(watcher,))
    t.daemon = True
    t.start()

while True:
    time.sleep(1)

