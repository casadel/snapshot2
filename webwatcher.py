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
    payload = {'login': 'heusenvon', 'key': 'Ca$adelt'}
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
    
def get_street(soup, watcher):
    article = soup.find('div', attrs={'class': 'news-list-compact__block'})
    link = 'https://www.thestreet.com' + article.find('a')['href']
    return link, link

def get_itc_pr(soup, watcher):
    prs = soup.find_all('div', attrs={'class': 'views-field views-field-title'})
    if prs != []:
        links = [('https://www.usitc.gov' + pr.find('a')['href']) for pr in prs]
        return [(link, link) for link in links]
    else:
        return False
    
def get_drugs(soup, watcher):
    table = soup.find('table').find('tbody').find_all('tr')
    if 'Your selected month and year did not return any results.' not in table[0].text:
        link = 'https://www.accessdata.fda.gov' + table[-1].find('a')['href']
        return link, link
    else:
        return False
    
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

#################################################################
# HANDLERS triggered when a change occurs

def open_nflx(doc, watcher):
    found = False
    if 'Letter' in doc.text:
        link = doc['href']
        link = 'https://ir.netflix.com/' + link
        open_url(link, watcher)
    
def open_url(url, watcher):
    cmd = ('start "" "C:\Program Files (x86)\Google\Chrome\Application\Chrome.exe" --new-window "%s"' %url)
    subprocess.Popen(cmd, shell=True)
    PlaySound(watcher['sound'], SND_FILENAME | SND_ASYNC)
    print('%s: Successfully opened %s' %(str(datetime.datetime.now()), watcher['name']))

def new_data_ptab(page, watcher):
    def make_url(doc, url):
        return append_timestamp(url).split('?')[0] + '/' + doc['objectId'] + '/anonymousDownload'

    PlaySound(watcher['sound'], SND_FILENAME | SND_ASYNC)
    print('Change detected %s at %s' %(watcher['name'], (str(datetime.datetime.now()))))
    page = json.loads(page)
    opened = False
    for i in xrange(len(page) - 1, -1, -1):
        doc = page[i]
        if 'paperTypeName' not in doc:
            continue
        if any(doc['paperTypeName'] == dec_type for dec_type in watcher['dec_types']):
            url = make_url(doc, watcher['url'])
            #get/parse/return order
            filename = 'C:/Python27/Scripts/tmp/' + str(uuid.uuid4()) + '.pdf'
            pdf = requests.get(url, headers=headers)
            with open(filename, 'wb') as file:
                file.write(pdf.content)
            try:
                order = conclusion.find_order(filename)
                if ' not ' in order:
                    PlaySound('C:\Users\Rob\Music\Abbv.wav', SND_FILENAME | SND_ASYNC)
                else:
                    PlaySound('C:\Users\Rob\Music\Chrs.wav', SND_FILENAME | SND_ASYNC)
                print("\n\n" + watcher['name'] + "\n" + order + "\n")
                
            except:
                #open decision in browser if order not found
                cmd = ('start "" "C:\Program Files (x86)\Google\Chrome\Application\Chrome.exe" --new-window "%s"' %url)
                subprocess.Popen(cmd, shell=True)
                print('%s: Successfully opened %s' %(str(datetime.datetime.now()), watcher['name']))
            opened = True
            break
    if not opened:
        open_url('https://ptab.uspto.gov/#/login', watcher)

def open_pacer((url, case_name), watcher):

    case_nos = [case_no for case_no in watcher['case_nos'] if case_no in case_name]
    if len(case_nos):
        # open View Document page in Chrome
        case_no = case_nos[0].split(':')
        case_no = case_no[0] + case_no[1]
        sound_file = 'C:\\Windows\Media\Court case audio\%s.wav' %case_no
        cmd = ('start "" "C:\Program Files (x86)\Google\Chrome\Application\Chrome.exe" --new-window "%s"' %url)
        subprocess.Popen(cmd, shell=True)
        PlaySound(sound_file, SND_FILENAME | SND_ASYNC)
        print(str(datetime.datetime.now()), case_name, url)

        # download View Document page
        page = requests.get(url, cookies=watcher['cookies'], headers=headers)
        data = {'pdf_toggle_possible': 1, 'got_receipt': 1}
        result = re.search('onSubmit="goDLS\(\'.*?\',\'(.*?)\',\'(.*?)\'', page.content)
        data['caseid'] = result.group(1)
        data['de_seq_num'] = result.group(1)

        # downloads PDF
        pdf = requests.post(url, data=data, cookies=watcher['cookies'], headers=headers)
        filename = 'C:/Python27/Scripts/tmp/' + str(uuid.uuid4()) + '.pdf'
        with open(filename, 'wb') as file:
            file.write(pdf.content)
        conc = conclusion.find_conclusion(filename)
        print(conc)
        Beep(440, 500)
    else:
        PlaySound(watcher['sound'], SND_FILENAME | SND_ASYNC)
        print(str(datetime.datetime.now()), case_name, url)

###############################################################################
#  SCRAPER method to monitor the list of sites

headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'
        }

today = datetime.datetime.now()
today_str = today.strftime("%m/%d/%Y")

def loop(watcher):
    while True:
        url = watcher['url']

        try:
            parsed = watcher['retriever'](url, watcher)
            selected = watcher['selector'](parsed, watcher)
            #if watcher['type'] == 'json':
            #   print ('ptab', str(datetime.datetime.now()))
            if not watcher['status']:
                print ('All good!')
            watcher['status'] = True
        except Exception as e:
            if watcher['url'] != 'http://www.sprucepointcap.com/research/feed':
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

        watcher['first_loop'] = False
        time.sleep(watcher['delay'])

##########################################################
#PAGES

watchmen = [
    #{
    #    'url': 'http://nypost.com/feed/',
    #    'selector': get_nypost,
    #    'sound': 'C:\\Windows\Media\kosman.wav'
    #},
    #{
    #    'url': 'http://www.citronresearch.com/feed',
    #    'sound': 'C:\\Windows\Media\Citron.wav'
    #},
    #{
    #    'url': 'http://sirf-online.org/feed/',
    #    'sound': 'C:\\Windows\Media\sirf.wav'
    #},
    #{
    #    'url': 'http://www.muddywatersresearch.com/feed/?post_type=reports',
    #    'sound': 'C:\\Windows\Media\MW.wav'
    #},
    #{
    #    'url': 'http://ctfn.news/',
    #    'selector': get_ctfn,
    #    'sound': 'C:\\Windows\Media\CTFN.wav'
    #},
    #{
    #    'url': 'https://www.thestreet.com/find/results?q=feuerstein',
    #    'selector': get_street,
    #    'sound': 'C:\\Windows\Media\Feuerstein.wav'
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
    # IRs
    #{
    #    'url': 'http://apps.shareholder.com/rss/rss.aspx?channels=7196&companyid=ABEA-4CW8X0&sh_auth=3100301180%2E0%2E0%2E42761%2Eb96f9d5de05fc54b98109cd0d905924d',
    #    'sound': 'C:\\Windows\Media\tsla.wav'
    #},
    #{
    #    'url': 'https://ir.netflix.com/results.cfm?Quarter=&Year=2017',
    #    'selector': get_nflx,
    #    'sound': 'C:\\Windows\Media\NFLX.wav',
    #    'data_handler': open_nflx,
    #    'delay': .25
    #},
    #{
    #    'url': 'http://www.fda.gov/AboutFDA/ContactFDA/StayInformed/RSSFeeds/PressReleases/rss.xml',
    #    'delay': 2,
    #    'sound': 'C:\\Windows\Media\FDA.wav'
    #},
    #{
    #    'url': 'https://www.usitc.gov/press_room/news_release/news_release_index.htm?field_release_date_value%5Bvalue%5D%5B',
    #    'sound': 'C:\\Windows\Media\ITC.wav',
    #    'retriever' : itc_retriever,
    #    'selector': get_itc_pr,
    #    'delay': 5
    #},
    #{
    #    'url': 'https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=reportsSearch.process',
    #    'sound': 'C:\\Windows\Media\FDA.wav'
    #    'retriever': drug_retriever,
    #    'selector': get_drugs,  
    #},
    # PTAB
    {
        # AZN - MYL war on AstraZeneca Onglyza and Kombiglyze, decision due 5/2
        'name': 'IPR2015-01340',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1462326/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:\Users\Rob\Music\Azn_myl.wav',
        'type': 'json',
        'delay': 5
    },
    {
        # NVS
        'name': 'IPR2016-00084',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1462562/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:\\Windows\Media\Nvs.wav',
        'type': 'json',
        'delay': 5
    },
    {
        # JNJ due 5/31
        'name': 'IPR2016-00286',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1462535/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:\\Windows\Media\Jnj.wav',
        'type': 'json',
        'delay': 15
    },
    {
        # LLY due 6/3
        'name': 'IPR2016-00237',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1461718/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:\\Windows\Media\Lly.wav',
        'type': 'json',
        'delay': 15
    },
    {
        # LLY due 6/3
        'name': 'IPR2016-00240',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1463994/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:\\Windows\Media\Lly.wav',
        'type': 'json',
        'delay': 15
    },
    {
        # ANET due 6/6
        'name': 'IPR2016-00306',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1464176/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:\\Windows\Media\Anet.wav',
        'type': 'json',
        'delay': 15
    },
    {
        # ANET due 6/6
        'name': 'IPR2016-00309',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1462570/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:\\Windows\Media\Anet.wav',
        'type': 'json',
        'delay': 15
    },
    {
        # FMS due 6/8
        'name': 'IPR2016-00254',
        'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1459784/documents?availability=PUBLIC&cacheFix=',
        'sound': 'C:\\Windows\Media\Fms.wav',
        'type': 'json',
        'delay': 15
    },
    #{
         # REGN AMGN dupixent preliminary
    #    'name': 'IPR2017-01129',
    #    'url': 'https://ptab.uspto.gov/ptabe2e/rest/petitions/1485794/documents?availability=PUBLIC&cacheFix=',
    #    'sound': 'C:\\Windows\Media\EW.wav',
    #    'type': 'json',
    #    'dec_types': ['Decision Granting Institution', 'Decision Denying Institution', 'Settlement Before Institution']
    #},
    
    # PACER
    #{
    #    'name': 'Delaware Dist. Court',
    #    'url': 'https://ecf.ded.uscourts.gov/cgi-bin/WrtOpRpt.pl',
    #    'sound': 'C:\\Windows\Media\Court.wav',
    #    'type': 'pacer',
    #    'case_nos': ['1:16-cv-01243', '1:16-cv-01267', '1:16-cv-00944', '1:15-cv-00170', '1:16-cv-00592', '1:16-cv-00666']
    #},
    #{
    #    'name': 'NJ Dist. Court',
    #    'url': 'https://ecf.njd.uscourts.gov/cgi-bin/WrtOpRpt.pl',
    #    'sound': 'C:\\Windows\Media\Court.wav',
    #    'type': 'pacer',
    #    'case_nos': ['2:13-cv-00391', '2:15-cv-01360', '2:16-cv-04544']
    #},
    #{
    #    'name': 'NY Southern Dist. Court',
    #    'url': 'https://ecf.nysd.uscourts.gov/cgi-bin/WrtOpRpt.pl',
    #    'sound': 'C:\\Windows\Media\Court.wav',
    #    'type': 'pacer',
    #    'case_nos': ['1:16-cv-08164']
    #},
    #{
    #    'name': 'DC Dist. Court',
    #    'url': 'https://ecf.dcd.uscourts.gov/cgi-bin/WrtOpRpt.pl',
    #    'sound': 'C:\\Windows\Media\Court.wav',
    #    'type': 'pacer',
    #    'case_nos': [1:16-cv-02521]
    #},
    #{
    #    'name': 'Cali. Northern Dist. Court',
    #    'url': 'https://ecf.casd.uscourts.gov/cgi-bin/WrtOpRpt.pl',
    #    'sound': "C:\\Windows\Media\Court.wav",
    #    'type': 'pacer',
    #    'case_nos': ['5:17-cv-00220', '5:16-cv-00923']
    #},
    #{
    #    'name': 'Cali. Southern Dist. Court',
    #    'url': 'https://ecf.casd.uscourts.gov/cgi-bin/WrtOpRpt.pl',
    #    'sound': "C:\\Windows\Media\Court.wav",
    #    'type': 'pacer',
    #    'case_nos': ['3:15-cv-02287', '3:15-cv-02353', '3:15-cv-02324', '3:15-cv-02486', '3:17-cv-00108']
    #},
    #{
    #    'name': 'Illinois Northern Dist. Court',
    #    'url': 'https://ecf.ilnd.uscourts.gov/cgi-bin/WrtOpRpt.pl',
    #    'sound': 'C:\\Windows\Media\Court.wav',
    #    'type': 'pacer',
    #    'case_nos': ['1:16-cv-08637', '1:16-cv-07145']
    #},
    #{
    #    'name': 'ITC 337-1010',
    #    'url': 'https://edis.usitc.gov/data/document?investigationNumber=337-1010',
    #    'sound': 'C:\\Windows\Media\Court case audio\XPER.wav',
    #    'selector': get_itc,
    #    'delay': 60
    #},
    #{
    #    'name': 'ITC 337-944',
    #    'url': 'https://edis.usitc.gov/data/document?investigationNumber=337-944',
    #    'sound': 'C:\\Windows\Media\Court case audio\ANET.wav',
    #    'selector': get_itc,
    #    'delay': 60
    #},
    #{
    #    'name': 'ITC 337-945',
    #    'url': 'https://edis.usitc.gov/data/document?investigationNumber=337-945',
    #    'sound': 'C:\\Windows\Media\Court case audio\ANET.wav',
    #    'selector': get_itc,
    #    'delay': 60
    #}
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




