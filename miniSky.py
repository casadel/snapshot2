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
from winsound import PlaySound, Beep, SND_FILENAME, SND_ASYNC
import pyttsx
import random


sys.stdout = codecs.getwriter('utf8')(sys.stdout)

def append_timestamp(url):
    return url + str(int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds() * 1000))

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

###############################################################
# RETRIEVERS retrieve the relevant page and return the soup to be parsed

def page_retriever(url, watcher):
    page = requests.get(url, headers=headers)
    parsed = BeautifulSoup(page.text, 'html.parser')
    return parsed

def ptab_retriever(url, watcher):
    url = append_timestamp(url)
    page = requests.get(url, headers=headers)
    parsed = page.content
    return parsed

def pacer_retriever(url, watcher):
    cookies = {}
    payload = {'login': 'lchelouche', 'key': '#14285Chel'}
    data =  {'filed_from': today_str, 'filed_to': today_str, 'Key1': 'de_date_filed'}

    page = requests.post(url, data=payload, headers=headers)
    result = re.search('PacerSession=(.+?);', page.content)
    cookies['PacerSession'] = result.group(1)

    result = re.search('WrtOpRpt\.pl(\?\d+-L_1_0-1)', page.content)
    suffix = result.group(1)

    # perform the search and retrieve the page
    page2 = requests.post(url + suffix, data=data, cookies=cookies, headers=headers)
    parsed = BeautifulSoup(page2.text, 'html.parser')

    watcher['cookies'] = cookies
    return parsed

def itc_retriever(url, watcher):
    url_end = 'month%5D={}&field_release_date_value_1%5Bvalue%5D%5Byear%5D={}'.format(today.month, today.year)
    url = url+url_end
    page = requests.get(url, headers=headers)
    parsed = BeautifulSoup(page.text, 'html.parser')
    return parsed

def drug_retriever(url, watcher):
    data = {'reportSelectMonth': today.month, 'reportSelectYear': today.year}
    page = requests.post(url, data=data, headers=headers)
    soup = BeautifulSoup(page.text, 'html.parser')
    return soup

###############################################################
# SELECTORS find the info within the soup to be monitored
def get_nypost(soup, watcher):
    article = soup.find('item')
    link = article.find('link').text
    title = article.find('title').text
    authors = article.find('dc:creator').text.split(', ')
    damelos = ['Kosman', 'Atkinson', 'Dugan']
    for author in authors:
        for damelo in damelos:
            if damelo in author:
                watcher['name'] = damelo + ' ' + 'NY POST'
                return link, (title, link)
    else:
        return False

def get_axios(soup, watcher):
    article = soup.find('article')
    link = article['data-url']
    author_list = article.find_all('li', attrs={'class': 'author-avatar__item'})
    found = False
    for author in author_list:
        if 'Jonathan Swan' in author.text:
            found = True
            return link, link
            break
    if found == False:
        return False
    
def get_ctfn(soup, watcher):
    last_pubs = soup.find_all('ul', {'class': 'last-published-contents'})[0]
    last_symbol = last_pubs.find('li').find('strong').text
    return last_symbol, watcher['url']

def get_muddy(soup, watcher):
    link = soup.find('table', attrs={'id': 'research-table'}).find('a')['href']
    title = soup.find('table', attrs={'id': 'research-table'}).find('a').text
    return link, (title, link)
    
def get_rss(soup, watcher):
    article = soup.find('item')
    link = article.find('link').text
    title = article.find('title').text
    return link, (title, link)

def get_spruce(soup, watcher):
    link = soup.find('h2', attrs={'class': 'entry-title'}).find('a')['href']
    title = soup.find('h2', attrs={'class': 'entry-title'}).text
    return link, (title, link)

def get_prescience(soup, watcher):
    link = soup.find('h6', attrs={'class': 'entry-title'}).find('a')['href']
    title = soup.find('h6', attrs={'class': 'entry-title'}).find('a').text
    return link, (title, link)

def get_citron(soup, watcher):
    link = soup.find('h2', attrs={'class': 'post-title entry-title'}).find('a')['href']
    link = watcher['url'] + link
    title = soup.find('h2', attrs={'class': 'post-title entry-title'}).text
    return link, (title, link)

def get_mox(soup, watcher):
    link = soup.find('h1', attrs={'class': 'entry-title'}).find('a')['href']
    title = soup.find('h1', attrs={'class': 'entry-title'}).find('a').text
    return link, (title, link)

def get_glaucus(soup, watcher):
    link = soup.find_all('p')[2].find('a')['href']
    return link, link

def get_skytides(soup, watcher):
    link = 'http://www.skytides.com/' + soup.find('td', attrs={'class': 'views-field views-field-title views-align-left'}).find('a')['href']
    return link, link

def get_gotham(soup, watcher):
    link = soup.find('h2', attrs={'class': 'entry-title'}).find('a')['href']
    return link, link

def get_bronte(soup, watcher):
    link = soup.find('h3', attrs={'class': 'post-title entry-title'}).find('a')['href']
    return link, link

def get_swept(soup, watcher):
    title = soup.find('h1').text
    link = watcher['url']
    return title, link

def get_beta(soup, watcher):
    title = soup.find('article').find('h2').find('a').text
    link = watcher['url']
    return title, (title, link)

def get_kerrisdale(soup, watcher):
    title = soup.find('h2', attrs={'class': 'post-heading'}).text
    link = watcher['url']
    return title, link

def get_aurelius(soup, watcher):
    article = soup.find('h2', attrs={'class': 'content-primary__title'})
    title = article.text
    link = article.find('a')['href']
    return link, (title, link)

def get_nflx(soup, watcher):
    q_html = soup.find('ul', {'class': 'textUL'})
    if q_html != None:
        doc_links = q_html.find_all('a')
        tmp = [(doc, doc) for doc in doc_links]
        #import random
        #tmp[0] = (random.random(), tmp[0][1])
        return tmp
    else:
        return False

def get_sq(soup, watcher):
    link = soup.find('a', {'class': 'arrow'})['href']
    return link, link

def get_drugs(soup, watcher):
    link = soup.find('table').find('tbody').find('tr').find('a')['href']
    return link, watcher['url']

def get_itc(soup, watcher):
    doc_id = soup.find('document').find('id').text
    link = watcher['url']
    return doc_id, link

def get_itc_pr(soup, watcher):
    prs = soup.find_all('div', attrs={'class': 'views-field views-field-title'})
    if prs != []:
        links = [('https://www.usitc.gov' + pr.find('a')['href']) for pr in prs]
        return [(link, link) for link in links]
    else:
        return False

def get_de(soup, watcher):
    name = soup.find('table').find('td').text
    return name, name

def get_ptab_uspto(page, watcher):
    #import random
    #return random.random(), page
    return len(page), page

def pacer_selector(soup, watcher):
    cases = soup.find('table').find_all('tr')
    last = cases[-1].find_all('td')[-1].text
    if last == 'Date Filed':
        return False
    else:
        links, case_names = zip(*((x.find_all('td')[2].find('a')['href'], x.find_all('td')[1].text) for x in cases[1:]))

        tmp = [(x[0], x) for x in zip(links, case_names)]
        # for testing
        #import random
        #for i in range(len(tmp)):
        #    if 'Acorda' in tmp[i][1][1]:
        #        tmp[i] = (tmp[i][0] + '?' + str(random.random()), tmp[i][1])
        #        break
        return tmp

def get_stat(soup, watcher):
    article = soup.find('div', attrs={'class': 'card-grid-item'})
    link = article.find('a')['href']
    title = article.find('h3', attrs={'class':'post-title'}).find('span').text
    author = article.find('p', attrs={'class': 'author'}).text
    if 'Adam Feuerstein' in author:
        return link, (title, link)
    else:
        return False

#################################################################
# HANDLERS triggered when a change occurs
    
def open_url(data, watcher):
    engine1 = watcher['engine']
    if isinstance(data, tuple):
        title, url = data
        print(str(datetime.datetime.now()), '\n', watcher['name'], ': ',  title)
        vox = title + ' ' + watcher['name'] 
        engine1.say(vox)
    else:
        url = data
        print('%s: Successfully opened %s' %(str(datetime.datetime.now()), watcher['name']))
        engine1.say(watcher['name'])
    cmd = ('start "" "C:\Program Files (x86)\Google\Chrome\Application\Chrome.exe" --new-window "%s"' %url)
    subprocess.Popen(cmd, shell=True)
    engine1.runAndWait()
    time.sleep(5)

def new_data_ptab(page, watcher):
    def make_url(doc, url):
        return append_timestamp(url).split('?')[0] + '/' + doc['objectId'] + '/anonymousDownload'

    PlaySound(watcher['sound'], SND_FILENAME | SND_ASYNC)

    page = json.loads(page)
    opened = False
    for i in xrange(len(page) - 1, -1, -1):
        doc = page[i]
        if 'paperTypeName' not in doc:
            continue
        if any(doc['paperTypeName'] == dec_type for dec_type in watcher['dec_types']):
            #open decision in browser
            url = make_url(doc, watcher['url'])
            #get/parse/return order
            filename = 'C:/Python27/Scripts/tmp/' + str(uuid.uuid4()) + '.pdf'
            pdf = requests.get(url, headers=headers)
            with open(filename, 'wb') as file:
                file.write(pdf.content)
            try:
                order = conclusion.find_order(filename)
                neg_words = [' not ', ' fail', ' denied']
                if any(word in order for word in neg_words):
                    engine.say(watcher['POwin_sound'])
                else:
                    engine.say(watcher['POlose_sound'])
                print("\n\n" + watcher['name'] + " " + str(datetime.datetime.now())  + "\n" + order + "\n")
                engine.runAndWait()
            except:
                #open decision in browser if order not found
                cmd = ('start "" "C:\Program Files (x86)\Google\Chrome\Application\Chrome.exe" --new-window "%s"' %url)
                subprocess.Popen(cmd, shell=True)
                print('%s: Successfully opened %s' %(str(datetime.datetime.now()), watcher['name']))
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
today_str = today.strftime("%m/%d/%Y")
engine = pyttsx.init()
engine1 = pyttsx.init()
bugs = ['http://www.sprucepointcap.com/research/feed', 'http://moxreports.com/', 'https://glaucusresearch.com/', 'http://www.aureliusvalue.com/feed/']
def loop(watcher):
    while True:
        url = watcher['url']
        selected = None
        try:
            parsed = watcher['retriever'](url, watcher)
            selected = watcher['selector'](parsed, watcher)
            #if watcher['type'] == 'json':
                #print (watcher['name'], str(datetime.datetime.now()))
            if not watcher['status']:
                print ('All good!', str(datetime.datetime.now()))
            watcher['status'] = True
        except Exception as e:
            #if watcher['url'] not in bugs :
            eprint('%s: Scraping %s failed for some reason (%s)' %(str(datetime.datetime.now()), watcher['name'], str(e)))
            selected = False
            watcher['status'] = False
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


        if watcher['first_loop']:
            print ('%s initialized %s' %(watcher['name'],str(datetime.datetime.now())))
            watcher['first_loop'] = False
        time.sleep(watcher['delay'])

##########################################################
#PAGES

watchmen = [
    {
        'name': 'NY POST',
        'url': 'http://nypost.com/feed/',
        #'selector': get_nypost,
        'sound': 'C:\\Windows\Media\kosman.wav'
    },

    #{
    #    'name': 'CITRON',
    #    'url': 'http://www.citronresearch.com/feed',
    #   'selector': get_citron,
    #    'sound': 'C:\\Windows\Media\Citron.wav'
    #},

    {
        # LLY ‘209 patent alimta, due 10/4
        'name': 'IPR2016-01429',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1464714/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:/Users/abent/Music/Lly.wav',
        'POwin_sound' : 'Lilly wins',
        'POlose_sound' : 'Apotex wins',
        'type': 'json',
        'delay': 20
    },
]

for watcher in watchmen:
    # set some defaults
    watcher['prev'] = set()
    watcher['name'] = watcher.get('name', watcher['url'])
    watcher['type'] = watcher.get('type', 'soup')
    watcher['first_loop'] = True
    watcher['status'] = True

    if watcher['type'] == 'soup':
        watcher['delay'] = watcher.get('delay', 0.5)
        watcher['timestamp'] = watcher.get('timestamp', False)
        watcher['retriever'] = watcher.get('retriever', page_retriever)
        watcher['selector'] = watcher.get('selector', get_rss)
        watcher['data_handler'] = watcher.get('data_handler', open_url)
        watcher['engine'] = pyttsx.init()

    elif watcher['type'] == 'json':
        watcher['delay'] = watcher.get('delay', 60)
        watcher['timestamp'] = watcher.get('timestamp', True)
        watcher['dec_types'] = watcher.get('dec_types', ['Final Decision', 'Termination Decision Document'])
        watcher['retriever'] = watcher.get('retriever', ptab_retriever)
        watcher['selector'] = watcher.get('selector', get_ptab_uspto)
        watcher['data_handler'] = watcher.get('data_handler', new_data_ptab)

    elif watcher['type'] == 'pacer':
        watcher['delay'] = watcher.get('delay', 60)
        watcher['retriever'] = watcher.get('retriever', pacer_retriever)
        watcher['selector'] = watcher.get('selector', pacer_selector)
        watcher['data_handler'] = watcher.get('data_handler', open_pacer)

    t = threading.Thread(target=loop, args=(watcher,))
    t.daemon = True
    t.start()

while True:
    time.sleep(1)
    
