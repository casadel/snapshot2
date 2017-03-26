# -*- coding: utf-8 -*-

from __future__ import print_function

import itertools
from bs4 import BeautifulSoup
import sys
import time
import requests
import os
import subprocess
import datetime
import threading
import json
import conclusion
import uuid
import codecs

if os.name == 'nt':
    import winsound

sys.stdout = codecs.getwriter('utf8')(sys.stdout)

def append_timestamp(url):
    return url + str(int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds() * 1000))

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

###############################################################
# RETRIEVERS retrieve the relevant page and return the soup to be parsed

def page_retriever(url):
    page = requests.get(url, headers=headers)
    parsed = BeautifulSoup(page.text, 'html.parser')
    return parsed

def ptab_retriever(url):
    url = append_timestamp(url)
    page = requests.get(url, headers=headers)
    parsed = page.content
    return parsed

def pacer_retriever(url):
    cookies = {}
    payload = {'login': 'heusenvon', 'key': 'Ca$adelt'}
    data =  {'filed_from': filed_from, 'filed_to': filed_to, 'Key1': 'de_date_filed'}
    
    page = requests.post(url, data=payload, headers=headers)
    result = re.search('PacerSession=(.+?);', page.content)
    cookies['PacerSession'] = result.group(1)

    result = re.search('WrtOpRpt\.pl(\?\d+-L_1_0-1)', page.content)
    suffix = result.group(1)

    # perform the search and retrieve the page
    page2 = requests.post(url + suffix, data=data, cookies=cookies, headers=headers)
    parsed = BeautifulSoup(page2.text, 'html.parser')
    return parsed

###############################################################
# SELECTORS find the info within the soup to be monitored

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

def get_ctfn(soup, watcher):
    last_pubs = soup.find_all('ul', {'class': 'last-published-contents'})[0]
    last_symbol = last_pubs.find('li').find('strong').text
    return last_symbol, watcher['url']

def get_ptab_uspto(page, watcher):
    return len(page), page

def pacer_selector(soup, watcher):
    case = soup.find('table').find_all('tr')[-1]
    link = case.find_all('td')[2].find('a')['href']
    case_name = case.find_all('td')[1].text
    case_nos = watcher['case_nos']
    if any(case_no in case_name for case_no in case_nos):
        sound_file = 'C:\\Windows\Media\%s.wav' %case_no
        watcher['sound'] = watcher.get('sound', sound_file)
        return link, link
    else:
        return False, False

#################################################################
# HANDLERS triggered when a change occurs

def open_url(url, watcher):
    cmd = ('start "" "C:\Program Files (x86)\Google\Chrome\Application\Chrome.exe" --new-window "%s"'
        if os.name == 'nt' else "open '%s'") %url
    subprocess.Popen(cmd, shell=True)
    print('%s: Successfully opened %s' %(str(datetime.datetime.now()), watcher['name']))

def new_data_ptab(page, watcher):
    def make_url(doc, url):
        return append_timestamp(url).split('?')[0] + '/' + doc['objectId'] + '/anonymousDownload'

    page = json.loads(page)

    opened = False
    for doc in page:
        if any(doc['paperTypeName'] == dec_type for dec_type in watcher['dec_types']):
            url = make_url(doc, watcher['url'])
            open_url(url, watcher)
            
            filename = 'tmp/' + str(uuid.uuid4()) + '.pdf'

            # download and save the pdf
            pdf = requests.get(url, headers=headers)
            with open(filename, 'wb') as file:
                file.write(pdf.content)
            conc = conclusion.find_conclusion(filename)
            print("\n\n\n" + watcher['name'] + "\n" + conc + "\n")
            opened = True
            break

    if not opened:
        open_url('https://ptab.uspto.gov/#/login', watcher)

###############################################################################
#  SCRAPER method to monitor the list of sites

headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'
        }

today = datetime.datetime.now()
DD = datetime.timedelta(days=3)
filed_from = today - DD
filed_from = filed_from.strftime("%m/%d/%Y")
filed_to = today.strftime("%m/%d/%Y")

def loop(watcher):
    while True:
        url = watcher['url']

        try:
            parsed = watcher['retriever'](url)
            prev, data = watcher['selector'](parsed, watcher)

        except Exception as e:
            eprint('%s: Scraping %s failed for some reason (%s)' %(str(datetime.datetime.now()), url, str(e)))
            prev = False

        if len(watcher['prev']) > 0 and prev not in watcher['prev'] and prev:
            if os.name == 'nt':
                winsound.PlaySound(watcher['sound'], winsound.SND_FILENAME)
            else:
                subprocess.Popen("say '%s'" % watcher['name'], shell=True)

            try:
                watcher['data_handler'](data, watcher)
            except Exception as e:
                eprint('%s: Handling %s failed for some reason (%s)' %(str(datetime.datetime.now()), url, str(e)))

        watcher['prev'].add(prev)
        time.sleep(watcher['delay'])

##########################################################
#PAGES

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
        'url': 'http://www.fda.gov/AboutFDA/ContactFDA/StayInformed/RSSFeeds/PressReleases/rss.xml',
        'delay': 2,
        'sound': 'C:\\Windows\Media\fda.wav'
    },
    {
        'url': 'http://ctfn.news/',
        'selector': get_ctfn,
        'sound': 'C:\\Windows\Media\ctfn.wav'
    },
    #{
    #    'url': 'http://apps.shareholder.com/rss/rss.aspx?channels=7196&companyid=ABEA-4CW8X0&sh_auth=3100301180%2E0%2E0%2E42761%2Eb96f9d5de05fc54b98109cd0d905924d',
    #    'sound': 'C:\\Windows\Media\tsla.wav'
    #},
    #{
    #    'url': 'http://www.sprucepointcap.com/research/feed',
    #    'delay': 1,
    #    'sound': 'C:\\Windows\Media\spruce.wav'
    #},
    #{
    #    'url': 'http://www.presciencepoint.com/research/feed',
    #    'sound': 'C:\\Windows\Media\prescience.wav'
    #},
    
    # PTAB
    {
        # AZN - MYL war on AstraZeneca Onglyza and Kombiglyze, decision due 5/2
        'name': 'IPR2015-01340',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1462326/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:\\Windows\Media\Azn_myl.wav',
        'type': 'json'
    },
    {
        # ABBV CHRS Humira, due 5/17
        'name': 'IPR2016-00172',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1463015/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:\\Windows\Media\Abbv.wav',
        'type': 'json',
    },
    {
        # EW - BSX, institution decision due ~ April
        'name': 'IPR2017-00444',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1477074/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:\\Windows\Media\EW.wav',
        'type': 'json',
        'dec_types': ['Decision Granting Institution', 'Decision Denying Institution', 'Settlement Before Institution']
    },
    {
        'name': 'IPR2017-00072',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1472314/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:\\Windows\Media\EW.wav',
        'type': 'json',
        'dec_types': ['Decision Granting Institution', 'Decision Denying Institution', 'Settlement Before Institution']
    },
    {
        'name': 'IPR2017-00060',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1472154/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:\\Windows\Media\EW.wav',
        'type': 'json',
        'dec_types': ['Decision Granting Institution', 'Decision Denying Institution', 'Settlement Before Institution']
    },
    {
        # MYL - TEVA Copaxone, institution decision due by May
        'name': 'IPR2017-00195',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1473916/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:\\Windows\Media\Teva.wav',
        'type': 'json',
        'dec_types': ['Decision Granting Institution', 'Decision Denying Institution', 'Settlement Before Institution']
    },
    
    # PACER
    {
        'name': 'Delaware Dist. Court',
        'url': 'https://ecf.ded.uscourts.gov/cgi-bin/WrtOpRpt.pl',
        'type': 'pacer',
        'case_nos': ['1:14-cv-00882', '1:16-cv-01243', '1:16-cv-01267', '1:16-cv-00944', '1:16-cv-00666'] #ACOR, JUNO/KITE, TEVA, MNK/PX, ABBV/AMGN
    },
    {
        'name': 'Illinois Northern Dist. Court',
        'url': 'https://ecf.ilnd.uscourts.gov/cgi-bin/WrtOpRpt.pl',
        'type': 'pacer',
        'case_nos': ['1:16-cv-08637', '1:16-cv-07145'] #TSN/SAFM/PPC, SRCL
    },
    {
        'name': 'NJ Dist. Court',
        'url': 'https://ecf.njd.uscourts.gov/cgi-bin/WrtOpRpt.pl',
        'type': 'pacer',
        'case_nos': ['2:16-cv-01118', '2:15-cv-01360'] #AMGN, JAZZ
    }
]

for watcher in watchmen:
    # set some defaults
    watcher['prev'] = set()
    watcher['name'] = watcher.get('name', watcher['url'])
    watcher['type'] = watcher.get('type', 'soup')
    
    if watcher['type'] == 'soup':
        watcher['delay'] = watcher.get('delay', 0.5)
        watcher['timestamp'] = watcher.get('timestamp', False)
        watcher['retriever'] = watcher.get('retriever', page_retriever)
        watcher['selector'] = watcher.get('selector', get_rss)
        watcher['data_handler'] = watcher.get('data_handler', open_url)
    
    elif watcher['type'] == 'json':
        watcher['delay'] = watcher.get('delay', 30)
        watcher['timestamp'] = watcher.get('timestamp', True)
        watcher['dec_types'] = watcher.get('dec_types', ['Final Decision', 'Termination Decision Document'])
        watcher['retriever'] = watcher.get('retriever', ptab_retriever)
        watcher['selector'] = watcher.get('selector', get_ptab_uspto)
        watcher['data_handler'] = watcher.get('data_handler', new_data_ptab)
    
    elif watcher['type'] == 'pacer':
        watcher['delay'] = watcher.get('delay', 5)
        watcher['data_retriever'] = watcher.get('retriever', pacer_retriever)
        watcher['selector'] = watcher.get('selector', pacer_selector)
        watcher['data_handler'] = watcher.get('data_handler', open_url)
    
    t = threading.Thread(target=loop, args=(watcher,))
    t.daemon = True
    t.start()

while True:
    time.sleep(1)


