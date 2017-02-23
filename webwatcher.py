# -*- coding: utf-8 -*-
import itertools
from bs4 import BeautifulSoup
import sys
import time
import requests
import os
import datetime
import threading
import json

# only import this if on Windows
if os.name == 'nt':
    import winsound

############################## Selectors ######################################

def get_nypost(soup, url):
    article = soup.find('item')
    link = article.find('link').text
    authors = article.find('dc:creator').text.split(', ')
    damelos = ['Josh Kosman', 'Claire Atkinson']
    if any(damelo in authors for damelo in damelos):
        return link, link
    else:
        return False, False

def get_rss(soup, url):
    article = soup.find('item')
    link = article.find('link').text
    return link, link

def get_street(soup, url):
    story = soup.find_all('li', {'class': 'news-ticker__item'})[0]
    link = story.find('a')['href']
    damelos = ['drug', 'therapeutics', 'pharma', 'pharmaceuticals', 'data', 'biotech', 'biopharma', 'cancer']
    if any(damelo in link for damelo in damelos):
        return link, link
    else:
        return False, False

def get_ctfn(soup, url):
    last_pubs = soup.find_all('ul', {'class': 'last-published-contents'})[0]
    last_symbol = last_pubs.find('li').find('strong').text
    return last_symbol, url

def get_dcd(soup, url):
    case = soup.find('item')
    title = case.find('title').text
    case_number = '1:16-cv-01493' #US v ANTM
    if case_number in title:
        return title, url
    else:
        return False, False

def get_ded(soup, url):
    case = soup.find('item')
    title = case.find('title').text
    case_numbers = ['1:16-cv-01267', '1:16-cv-01243'] #JUNO-KITE TEVA-various
    if any(case_number in title for case_number in case_numbers):
        return title, url
    else:
        return False, False

def get_cafc(soup, url):
    case = soup.find('item')
    title = case.find('title').text
    case_numbers = ['17-1480', '17-1575'] #AMGN-SNY TEVA-Sandoz
    if any(case_number in title for case_number in case_numbers):
        return title, url
    else:
        return False, False

def get_ptab_uspto(json, url):
    # the url to open, since hard to open to the document directly
    url = 'https://ptab.uspto.gov/#/login'

    # just return the number of currently uploaded documents
    return len(json), url

def get_interference(soup, url):
    doc_num = soup.find_all('tr', {'class': 'odd'})[0].find_all('td')[1].text
    return doc_num, url

#################################################################################

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'
}

def loop(watcher):
    while True:
        try:
	    # append the current unix timestamp to the URL if necessary
	    # (ptab.uspto.gov requires it)
	    url = watcher['url']
	    if watcher['timestamp']:
	    	url += str(int((datetime.datetime.utcnow() -
			        datetime.datetime(1970, 1, 1)).total_seconds() * 1000))

	    # download the page and parse it appropriately (as json vs html)
            page = requests.get(url, headers=headers)
            if watcher['type'] == 'json':
		parsed = json.loads(page.text)
            else:
		parsed = BeautifulSoup(page.text, 'html.parser')

            link, url = watcher['selector'](parsed, url)

        except Exception as e:
            print 'Scraping %s failed for some reason' %watcher['url'], str(datetime.datetime.now())
            link = False

        if len(watcher['last_link'].keys()) > 0 and link not in watcher['last_link'] and link:
	    if os.name == 'nt':
		cmd = 'start "" "C:\Program Files (x86)\Google\Chrome\Application\Chrome.exe" --new-window "%s"' %url
	    else:
		cmd = "open '%s'" %url
            os.system(cmd)

	    if os.name == 'nt':
		winsound.Beep(440, 500)

            print watcher['name'] + str(datetime.datetime.now())

        watcher['last_link'][link] = True
        time.sleep(watcher['delay'])

watchmen = [
    {
        # since you'll have multiple of these that just open ptab.uspto.gov when a change is
        # found, this name will get printed out at the console when it opens so that you
        # know what to search to find the change
    	'name': 'IPR2016-00172',
    	'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1463015/documents?availability=PUBLIC&cacheFix=',
    	'type': 'json',
    	'timestamp': True,
    	'selector': get_ptab_uspto,
    	'delay': 10
    },
    {
        'url': 'http://nypost.com/feed/',
        'selector': get_nypost,
    },
    {
        'url': 'http://www.citronresearch.com/feed',
    },
    {
        'url': 'http://www.muddywatersresearch.com/feed/?post_type=reports',
    },
    {
        'url': 'http://www.sprucepointcap.com/research/feed',
    },
    {
        'url': 'http://www.presciencepoint.com/research/feed',
    },
    {
        'url': 'http://www.fda.gov/AboutFDA/ContactFDA/StayInformed/RSSFeeds/PressReleases/rss.xml',
    },
    #{
    #    'url': 'http://apps.shareholder.com/rss/rss.aspx?channels=7196&companyid=ABEA-4CW8X0&sh_auth=3100301180%2E0%2E0%2E42761%2Eb96f9d5de05fc54b98109cd0d905924d',
    #},
    {
        'url': 'http://ctfn.news/',
        'selector': get_ctfn,
    },
    {
        'url': 'https://www.thestreet.com/latest-news',
        'selector': get_street,
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
    # set some defaults
    watcher['last_link'] = {}
    watcher['delay'] = watcher.get('delay', 0.5)
    watcher['type'] = watcher.get('type', 'soup')
    watcher['selector'] = watcher.get('selector', get_rss)
    watcher['timestamp'] = watcher.get('timestamp', False)
    watcher['name'] = watcher.get('name', watcher['url'])

    t = threading.Thread(target=loop, args=(watcher,))
    t.daemon = True
    t.start()

while True:
    time.sleep(1)
