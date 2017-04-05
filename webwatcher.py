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
import re
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
    data =  {'filed_from': today, 'filed_to': today, 'Key1': 'de_date_filed'}

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
        return False

def get_rss(soup, watcher):
    article = soup.find('item')
    link = article.find('link').text
    return link, link

def get_ctfn(soup, watcher):
    last_pubs = soup.find_all('ul', {'class': 'last-published-contents'})[0]
    last_symbol = last_pubs.find('li').find('strong').text
    return last_symbol, watcher['url']

def get_itc(soup, watcher):
    doc_id = soup.find('document').find('id').text
    link = watcher['url']
    return doc_id, link

def get_ptab_uspto(page, watcher):
    #import random
    #return random.random(), page
    return len(page), page

def pacer_selector(soup, watcher):
    cases = soup.find('table').find_all('tr')
    links, case_names = zip(*((x.find_all('td')[2].find('a')['href'], x.find_all('td')[1].text) for x in cases[1:]))
    return [(x[0], x) for x in zip(links, case_names)]

#################################################################
# HANDLERS triggered when a change occurs

def open_url(url, watcher):
    cmd = ('start "" "C:\Program Files (x86)\Google\Chrome\Application\Chrome.exe" --new-window "%s"' %url)
    subprocess.Popen(cmd, shell=True)
    winsound.PlaySound(watcher['sound'], winsound.SND_FILENAME)
    print('%s: Successfully opened %s' %(str(datetime.datetime.now()), watcher['name']))

def new_data_ptab(page, watcher):
    def make_url(doc, url):
        return append_timestamp(url).split('?')[0] + '/' + doc['objectId'] + '/anonymousDownload'

    winsound.PlaySound(watcher['sound'], winsound.SND_FILENAME)
    page = json.loads(page)
    opened = False
    for doc in page:
        if any(doc['paperTypeName'] == dec_type for dec_type in watcher['dec_types']):
            #open decision in browser
            url = make_url(doc, watcher['url'])
            cmd = ('start "" "C:\Program Files (x86)\Google\Chrome\Application\Chrome.exe" --new-window "%s"' %url)
            subprocess.Popen(cmd, shell=True)
            winsound.PlaySound(watcher['sound'], winsound.SND_FILENAME)
            #get/parse/return conclusion
            filename = 'C:/Python27/Scripts/tmp/' + str(uuid.uuid4()) + '.pdf'
            pdf = requests.get(url, headers=headers)
            with open(filename, 'wb') as file:
                file.write(pdf.content)
            conc = conclusion.find_conclusion(filename)
            winsound.Beep(440, 500)
            print("\n\n" + watcher['name'] + "\n" + conc + "\n")
            opened = True
            break
    if not opened:
        open_url('https://ptab.uspto.gov/#/login', watcher)

def open_pacer((url, case_name), watcher):
    case_nos = watcher['case_nos']
    if any(case_no in case_name for case_no in case_nos):
    #    sound_file = 'C:\\Windows\Media\%s.wav' %case_no
        cmd = ('start "" "C:\Program Files (x86)\Google\Chrome\Application\Chrome.exe" --new-window "%s"' %url)
        subprocess.Popen(cmd, shell=True)
        winsound.PlaySound(sound_file, winsound.SND_FILENAME)
        print(str(datetime.datetime.now()), case_name, url)
    else:
        cmd = ('start "" "C:\Program Files (x86)\Google\Chrome\Application\Chrome.exe" --new-window "%s"' %watcher['url'])
        subprocess.Popen(cmd, shell=True)
        winsound.PlaySound(watcher['sound'], winsound.SND_FILENAME)
        print(str(datetime.datetime.now()), case_name, url)

###############################################################################
#  SCRAPER method to monitor the list of sites

headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'
        }

today = datetime.datetime.now()
today = today.strftime("%m/%d/%Y")

def loop(watcher):
    while True:
        url = watcher['url']

        try:
            parsed = watcher['retriever'](url)
            selected = watcher['selector'](parsed, watcher)
            #if watcher['type'] == 'json':
            #    print ('scraped ptab', str(datetime.datetime.now()))
        except Exception as e:
            eprint('%s: Scraping %s failed for some reason (%s)' %(str(datetime.datetime.now()), watcher['name'], str(e)))
            selected = False

        # theoretically, this optimization fails if something in watcher['prev'] ends
        # up getting *removed* from the selected list
        if isinstance(selected, list) and len(selected) == len(watcher['prev']):
            selected = False

        if isinstance(selected, tuple):
            selected = [selected]

        if selected:
            for (prev, data) in selected:
                if prev not in watcher['prev']:
                    watcher['prev'].add(prev)

                    # don't open anything on the first loop
                    if not watcher['first_loop']:
                        try:
                            watcher['data_handler'](data, watcher)
                        except Exception as e:
                            eprint('%s: Handling %s failed for some reason (%s)' %(str(datetime.datetime.now()), url, str(e)))


        watcher['first_loop'] = False
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
        'sound': 'C:\\Windows\Media\Citron.wav'
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
        'sound': 'C:\\Windows\Media\FDA.wav'
    },
    {
        'url': 'http://ctfn.news/',
        'selector': get_ctfn,
        'sound': 'C:\\Windows\Media\CTFN.wav'
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
    {
        'url': 'http://www.presciencepoint.com/research/feed',
        'sound': 'C:\\Windows\Media\prescience.wav'
    },

    # PTAB
    #{
    #    # AZN - MYL war on AstraZeneca Onglyza and Kombiglyze, decision due 5/2
    #    'name': 'IPR2015-01340',
    #    'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1462326/documents?availability=PUBLIC&cacheFix=',
    #    'sound': 'C:\\Windows\Media\Azn_myl.wav',
    #    'type': 'json',
    #    'delay': 30
    #},
    #{
    #    # ABBV CHRS Humira, due 5/17
    #    'name': 'IPR2016-00172',
    #    'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1463015/documents?availability=PUBLIC&cacheFix=',
    #    'sound': 'C:\\Windows\Media\Abbv_chrs.wav',
    #    'type': 'json'
    #    #'delay': 30
    #},
    #{
         # REGN AMGN dupixent preliminary
    #    'name': 'IPR2017-01129',
    #    'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1485794/documents?availability=PUBLIC&cacheFix=',
    #    'sound': 'C:\\Windows\Media\EW.wav',
    #    'type': 'json',
    #    'dec_types': ['Decision Granting Institution', 'Decision Denying Institution', 'Settlement Before Institution']
    #},
    #{
    #    # EW - BSX, institution decision due ~ April
    #    'name': 'IPR2017-00444',
    #    'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1477074/documents?availability=PUBLIC&cacheFix=',
    #    'sound': 'C:\\Windows\Media\EW.wav',
    #    'type': 'json',
    #    'dec_types': ['Decision Granting Institution', 'Decision Denying Institution', 'Settlement Before Institution']
    #},
    #{
    #    'name': 'IPR2017-00072',
    #    'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1472314/documents?availability=PUBLIC&cacheFix=',
    #    'sound': 'C:\\Windows\Media\EW.wav',
    #    'type': 'json',
    #    'dec_types': ['Decision Granting Institution', 'Decision Denying Institution', 'Settlement Before Institution']
    #},
    #{
    #    'name': 'IPR2017-00060',
    #    'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1472154/documents?availability=PUBLIC&cacheFix=',
    #    'sound': 'C:\\Windows\Media\EW.wav',
    #    'type': 'json',
    #    'dec_types': ['Decision Granting Institution', 'Decision Denying Institution', 'Settlement Before Institution']
    #},
    #{
    #    # MYL - TEVA Copaxone, institution decision due by May
    #    'name': 'IPR2017-00195',
    #    'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1473916/documents?availability=PUBLIC&cacheFix=',
    #    'sound': 'C:\\Windows\Media\Teva.wav',
    #    'type': 'json',
    #    'dec_types': ['Decision Granting Institution', 'Decision Denying Institution', 'Settlement Before Institution']
    #},
    # PACER
    {
        'name': 'Delaware Dist. Court',
        'url': 'https://ecf.ded.uscourts.gov/cgi-bin/WrtOpRpt.pl',
        'sound': 'C:\\Windows\Media\Court.wav',
        'type': 'pacer',
        'case_nos': ['1:16-cv-01243', '1:16-cv-01267', '1:16-cv-00944', '1:15-cv-00170', '1:16-cv-00592', '1:16-cv-00666', '	1:14-cv-00955']
    },
    {
        'name': 'Cali. Southern Dist. Court',
        'url': 'https://ecf.casd.uscourts.gov/cgi-bin/WrtOpRpt.pl',
        'sound': "C:\\Windows\Media\Court case audio\BOFI.wav",
        'type': 'pacer',
        'case_nos': ['3:15-cv-02287', '3:15-cv-02353', '3:15-cv-02324', '3:15-cv-02486']
    },
    #{
    #    'name': 'Illinois Northern Dist. Court',
    #    'url': 'https://ecf.ilnd.uscourts.gov/cgi-bin/WrtOpRpt.pl',
    #    'sound': 'C:\\Windows\Media\Court.wav',
    #    'type': 'pacer',
    #    'case_nos': ['1:16-cv-08637', '1:16-cv-07145']
    #},
    {
        'name': 'NJ Dist. Court',
        'url': 'https://ecf.njd.uscourts.gov/cgi-bin/WrtOpRpt.pl',
        'sound': 'C:\\Windows\Media\Court.wav',
        'type': 'pacer',
        'case_nos': ['2:16-cv-01118', '2:15-cv-01360', '2:13-cv-00391']
    },
    {
        'name': 'ITC 337-944',
        'url': 'https://edis.usitc.gov/data/document?investigationNumber=337-944',
        'sound': 'C:\\Windows\Media\Court.wav',
        'selector': get_itc,
        'delay': 5
    }
]

for watcher in watchmen:
    # set some defaults
    watcher['prev'] = set()
    watcher['name'] = watcher.get('name', watcher['url'])
    watcher['type'] = watcher.get('type', 'soup')
    watcher['first_loop'] = True

    if watcher['type'] == 'soup':
        watcher['delay'] = watcher.get('delay', 0.5)
        watcher['timestamp'] = watcher.get('timestamp', False)
        watcher['retriever'] = watcher.get('retriever', page_retriever)
        watcher['selector'] = watcher.get('selector', get_rss)
        watcher['data_handler'] = watcher.get('data_handler', open_url)

    elif watcher['type'] == 'json':
        watcher['delay'] = watcher.get('delay', 60)
        watcher['timestamp'] = watcher.get('timestamp', True)
        watcher['dec_types'] = watcher.get('dec_types', ['Final Decision', 'Termination Decision Document'])
        watcher['retriever'] = watcher.get('retriever', ptab_retriever)
        watcher['selector'] = watcher.get('selector', get_ptab_uspto)
        watcher['data_handler'] = watcher.get('data_handler', new_data_ptab)

    elif watcher['type'] == 'pacer':
        watcher['delay'] = watcher.get('delay', 30)
        watcher['retriever'] = watcher.get('retriever', pacer_retriever)
        watcher['selector'] = watcher.get('selector', pacer_selector)
        watcher['data_handler'] = watcher.get('data_handler', open_pacer)

    t = threading.Thread(target=loop, args=(watcher,))
    t.daemon = True
    t.start()

while True:
    time.sleep(1)


