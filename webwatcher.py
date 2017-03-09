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

if os.name == 'nt':
    import winsound

def append_timestamp(url):
    return url + str(int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds() * 1000))

###############################################################

def get_nypost(soup, watcher):
    article = soup.find('item')
    link = article.find('link').text
    authors = article.find('dc:creator').text.split(', ')
    damelo = 'Josh Kosman'
    if damelo in authors:
        return link, link
    else:
        return False, False

def get_rss(soup, watcher):
    article = soup.find('item')
    link = article.find('link').text
    return link, link

def get_gotham(soup, watcher):
    article = soup.find('article')
    link = article.find('a')['href']
    return link, link

def get_ctfn(soup, watcher):
    last_pubs = soup.find_all('ul', {'class': 'last-published-contents'})[0]
    last_symbol = last_pubs.find('li').find('strong').text
    return last_symbol, watcher['url']

# DC District
def get_dcd(soup, watcher):
    case = soup.find('item')
    title = case.find('title').text
    #case_number = '1:16-cv-01493' #US v ANTM
    #if case_number in title:
    return title, watcher['url']
    #else:
    #    return False, False

# Delaware district
def get_ded(soup, watcher):
    case = soup.find('item')
    title = case.find('title').text
    case_numbers = ['1:16-cv-01267', '1:16-cv-01243'] #JUNO-KITE TEVA-various
    if any(case_number in title for case_number in case_numbers):
        return title, watcher['url']
    else:
        return False, False

# Federal Circuit Court of Appeals
def get_cafc(soup, watcher):
    case = soup.find('item')
    title = case.find('title').text
    case_numbers = ['17-1480', '17-1575'] #AMGN-SNY TEVA-Sandoz
    if any(case_number in title for case_number in case_numbers):
        return title, watcher['url']
    else:
        return False, False

# DC Circuit Court of Appeals
def get_cadc(soup, watcher):
    case = soup.find('item')
    title = case.find('title').text
    case_number = '17-5024' #US-ANTM appeal
    if case_number in title:
        return title, watcher['url']
    else:
        return False, False

def get_ptab_uspto(json, watcher):
    def make_url(doc, url):
        return append_timestamp(url).split('?')[0] + '/' + doc['objectId'] + '/anonymousDownload'

    url = 'https://ptab.uspto.gov/#/login'

    # this is more documents than we've seen before
    if len(watcher['last_link']) > 0 and len(json) not in watcher['last_link']:
        for doc in json:
            if any(doc['paperTypeName'] == dec_type for dec_type in watcher['dec_types']):
                url = make_url(doc, watcher['url'])
                break

    return len(json), url

###############################################################################

headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'
        }

def loop(watcher):
    while True:
        # append the current unix timestamp to the URL if necessary
        # (ptab.uspto.gov requires it)
        url = watcher['url']
        if watcher['timestamp']:
            url = append_timestamp(url)

        try:
            # download the page and parse it appropriately (as json vs html)
            page = requests.get(url, headers=headers)
            if watcher['type'] == 'json':
                parsed = json.loads(page.text)
            else:
                parsed = BeautifulSoup(page.text, 'html.parser')

            link, open_url = watcher['selector'](parsed, watcher)

        except Exception as e:
            print '%s: Scraping %s failed for some reason (%s)' %(str(datetime.datetime.now()), url, str(e))
            link = False

        if len(watcher['last_link']) > 0 and link not in watcher['last_link'] and link and open_url:
            cmd = ('start "" "C:\Program Files (x86)\Google\Chrome\Application\Chrome.exe" --new-window "%s"'
                   if os.name == 'nt' else "open '%s'") %open_url
            os.system(cmd)

            if os.name == 'nt':
                winsound.PlaySound(watcher['sound'], winsound.SND_FILENAME)
            else:
                os.system("say '%s'" % watcher['name'])

            print '%s: Successfully opened %s' %(str(datetime.datetime.now()), watcher['name'])

        watcher['last_link'].add(link)
        time.sleep(watcher['delay'])


watchmen = [
    {
        'url': 'http://nypost.com/feed/',
        'selector': get_nypost,
        'sound': 'C:\\Windows\Media\kosman.wav'
    },
    {
        'url': 'http://www.citronresearch.com/feed',
        'sound': 'C:\\Windows\Media\citron.wav'
    },
    {
        'url': 'http://sirf-online.org/feed/',
        'sound': 'C:\\Windows\Media\sirf.wav'
    },
    {
        'url': 'http://www.muddywatersresearch.com/feed/?post_type=reports',
        'sound': 'C:\\Windows\Media\MW.wav'
    },
    {
        'url': 'http://www.sprucepointcap.com/research/feed',
        'delay': 1,
        'sound': 'C:\\Windows\Media\spruce.wav'
    },
    {
        'url': 'http://www.presciencepoint.com/research/feed',
        'sound': 'C:\\Windows\Media\prescience.wav'
    },
    {
        'url': 'http://www.fda.gov/AboutFDA/ContactFDA/StayInformed/RSSFeeds/PressReleases/rss.xml',
        'delay': 2,
        'sound': 'C:\\Windows\Media\fda.wav'
    },
    #{
    #    'url': 'http://apps.shareholder.com/rss/rss.aspx?channels=7196&companyid=ABEA-4CW8X0&sh_auth=3100301180%2E0%2E0%2E42761%2Eb96f9d5de05fc54b98109cd0d905924d',
    #    'sound': 'C:\\Windows\Media\tsla.wav'
    #},
    {
        'url': 'http://ctfn.news/',
        'selector': get_ctfn,
        'sound': 'C:\\Windows\Media\ctfn.wav'
    },
    #{
    #    'url': 'https://ecf.dcd.uscourts.gov/cgi-bin/rss_outside.pl',
    #    'selector': get_dcd,
    #    'delay': 3,
    #    'sound': 'C:\\Windows\Media\court.wav'
    #},
    #{
    #    'url': 'https://ecf.ded.uscourts.gov/cgi-bin/rss_outside.pl',
    #    'selector': get_ded,
    #    'delay': 3,
    #    'sound': 'C:\\Windows\Media\court.wav'
    #},
    #{
    #    'url': 'https://ecf.cafc.uscourts.gov/cmecf/servlet/TransportRoom?servlet=RSSGenerator',
    #    'selector': get_cafc,
    #    'delay': 4,
    #    'sound': 'C:\\Windows\Media\court.wav'
    #},
    #{
    #    'url': 'https://ecf.cadc.uscourts.gov/cmecf/servlet/TransportRoom?servlet=RSSGenerator',
    #    'selector': get_cadc,
    #    'delay': 2,
    #    'sound': 'C:\\Windows\Media\court.wav'
    #},
    {
        # ABBV CHRS Humira, due 5/17
        'name': 'IPR2016-00172',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1463015/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:\\Windows\Media\abbv_chrs.wav',
        'type': 'json',
    },
    {
        # ACOR-CAD Ampyra, IPRS 1850 1853 1857 1858 all due by 3/11
        'name': 'IPR2015-01853',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1459705/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:\\Windows\Media\acor_bass.wav',
        'type': 'json',
    },
    {
        'name': 'IPR2015-01850',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1459994/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:\\Windows\Media\acor_bass.wav',
        'type': 'json',
    },
    {
        'name': 'IPR2015-01857',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1459733/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:\\Windows\Media\acor_bass.wav',
        'type': 'json',
    },
    {
        'name': 'IPR2015-01858',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1463318/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:\\Windows\Media\acor_bass.wav',
        'type': 'json',
    },
    {
        # BIIB - CAD Tecfidera, due 3/22
        'name': 'IPR2015-01993',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1464139/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:\\Windows\Media\biib_bass.wav',
        'type': 'json',
    },
    {
        # MYL - TEVA Copaxone, institution decision due by May
        'name': 'IPR2017-00195',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1473916/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:\\Windows\Media\teva.wav',
        'type': 'json',
        'dec_types': ['Decision Granting Institution', 'Decision Denying Institution']
    },
    {
        # AZN - MYL war on AstraZeneca Onglyza and Kombiglyze, decision due 5/2
        'name': 'IPR2015-01340',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1462326/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:\\Windows\Media\Azn_myl.wav',
        'type': 'json',
    }

]

for watcher in watchmen:
    # set some defaults
    watcher['last_link'] = set()
    watcher['name'] = watcher.get('name', watcher['url'])
    watcher['type'] = watcher.get('type', 'soup')
    if watcher['type'] == 'soup':
        watcher['delay'] = watcher.get('delay', 0.5)
        watcher['selector'] = watcher.get('selector', get_rss)
        watcher['timestamp'] = watcher.get('timestamp', False)
    else:
        # defaults specifically for json parsing, which for now is exclusively
        # done on https://ptab.uspto.gov
        watcher['delay'] = watcher.get('delay', 30)
        watcher['selector'] = watcher.get('selector', get_ptab_uspto)
        watcher['timestamp'] = watcher.get('timestamp', True)
        watcher['dec_types'] = watcher.get('dec_types', ['Final Decision'])

    t = threading.Thread(target=loop, args=(watcher,))
    t.daemon = True
    t.start()

while True:
    time.sleep(1)

