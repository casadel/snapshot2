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
import color_console as cons

sys.stdout = codecs.getwriter('utf8')(sys.stdout)

default_colors = cons.get_text_attr()
default_bg = default_colors & 0x0070

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
    title = article.find('title').text
    authors = article.find('dc:creator').text.split(', ')
    damelos = ['Kosman', 'Atkinson', 'Dugan']
    for author in authors:
        for damelo in damelos:
            if damelo in author:
                watcher['sound'] = 'C:\\Windows\Media\%s.wav' %damelo
                watcher['name'] = damelo + ' NY POST'
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
    title = soup.find('h6', attrs={'class': 'entry-title'}).text
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
    title = soup.find('article').text
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
    table = soup.find('table').find('tbody').find_all('tr')
    if 'Your selected month and year did not return any results.' not in table[0].text:
        link = 'https://www.accessdata.fda.gov' + table[-1].find('a')['href']
        return link, link
    else:
        return False

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
                         
def get_calisuper(page, watcher):
    #import random
    #return random.random(), page
    return len(page), watcher['url']
#################################################################
# HANDLERS triggered when a change occurs

highlights = ['Kosman NY POST', 'SPRUCE PT.', 'CITRON', 'MW', 'SIRF', 'PRESCIENCE PT.', 'FEUERSTEIN']   
def open_url(data, watcher):
    PlaySound(watcher['sound'], SND_FILENAME | SND_ASYNC)
    if isinstance(data, tuple):
        title, url = data
        name = watcher['name']
        if name in highlights:
            cons.set_text_attr(cons.FOREGROUND_GREY | cons.BACKGROUND_RED |
                     cons.FOREGROUND_INTENSITY | cons.BACKGROUND_INTENSITY)
        print(str(datetime.datetime.now()), watcher['name'], '\n', title)
    else:
        url = data
        print('%s: Successfully opened %s' %(str(datetime.datetime.now()), watcher['name']))
    cmd = ('start "" "C:\Program Files (x86)\Google\Chrome\Application\Chrome.exe" --new-window "%s"' %url)
    subprocess.Popen(cmd, shell=True)
    cons.set_text_attr(default_colors)
    time.sleep(5)

def new_data_ptab(page, watcher):
    def make_url(doc, url):
        return append_timestamp(url).split('?')[0] + '/' + doc['objectId'] + '/anonymousDownload'

    PlaySound(watcher['sound'], SND_FILENAME | SND_ASYNC)
    print (watcher['name'])
    print('Change detected %s at %s' %(watcher['name'], (str(datetime.datetime.now()))))
    
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
        cons.set_text_attr(cons.FOREGROUND_GREY | cons.BACKGROUND_RED |
                     cons.FOREGROUND_INTENSITY | cons.BACKGROUND_INTENSITY)
        print(str(datetime.datetime.now()), case_name, url)
        cons.set_text_attr(default_colors)
        
        # download View Document page
        page = requests.get(url, cookies=watcher['cookies'], headers=headers)
        print (page.content)
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
        time.sleep(20)
        
        print('\n\n', case_name, watcher['name'])
    else:
        PlaySound(watcher['sound'], SND_FILENAME | SND_ASYNC)
        print(case_name, watcher['name'], str(datetime.datetime.now()))

def open_nflx(doc, watcher):
    found = False
    if 'Letter' in doc.text:
        link = doc['href']
        link = 'https://ir.netflix.com/' + link
        open_url(link, watcher)

def open_de(case_name, watcher):
    PlaySound(watcher['sound'], SND_FILENAME | SND_ASYNC)
    print(case_name, watcher['url'], str(datetime.datetime.now()))
###############################################################################
#  SCRAPER method to monitor the list of sites

headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36'
        }

today = datetime.datetime.now()
today_str = today.strftime("%m/%d/%Y")
engine = pyttsx.init()
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
            if watcher['url'] not in bugs :
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
        'selector': get_nypost,
        'sound': 'C:\\Windows\Media\kosman.wav'
    },
    #{
    #    'url': 'http://www.axios.com',
    #    'selector': get_axios,
    #    'sound': 'C:\\Windows\Media\axios.wav'
    #},
    #{
    #    'url': 'http://ctfn.news/',
    #    'selector': get_ctfn,
    #    'sound': 'C:\\Windows\Media\CTFN.wav'
    #},
    {
        'name': 'FEUERSTEIN',
        'url': 'https://www.statnews.com/category/biotech/',
        'selector': get_stat,
        'sound': 'C:\\Windows\Media\Feuerstein_stat.wav'
    },
    {
        'name': 'CITRON',
        'url': 'http://www.citronresearch.com',
        'selector': get_citron,
        'sound': 'C:\\Windows\Media\Citron.wav'
    },
    {
        'name': 'SIRF',
        'url': 'http://sirf-online.org/',
        'selector': get_spruce,
        'sound': 'C:\\Windows\Media\SIRF.wav'
    },
    {
        'name': 'MW',
        'url': 'http://www.muddywatersresearch.com/research/',
        'sound': 'C:\\Windows\Media\MW.wav',
        'selector': get_muddy
    },
    {
        'name': 'SPRUCE PT.',
        'url': 'http://www.sprucepointcap.com/research/',
        'delay': 1,
        'selector': get_spruce,
        'sound': 'C:\\Windows\Media\Spruce.wav'
    },
    {
        'name': 'PRESCIENCE PT.',
        'url': 'http://www.presciencepoint.com/research/',
        'selector': get_prescience,
        'sound': 'C:\\Windows\Media\Prescience2.wav'
    },
    {
        'name': 'AURELIUS',
        'url': 'http://www.aureliusvalue.com/',
        'sound': 'C:\\Windows\Media\Aurelius_web.wav',
        'selector': get_aurelius
    },
    {
        'name': 'KREBS',
        'url': 'https://krebsonsecurity.com/feed/',
        'sound': 'C:\\Windows\Media\Krebs.wav'
    },
    {
        'name': 'MOX',
        'url': 'http://moxreports.com/',
        'selector': get_mox,
        'sound': 'C:\\Windows\Media\Mox.wav'
    },
    {
        'name': 'GLAUCUS',
        'url': 'https://glaucusresearch.com/',
        'selector': get_glaucus,
        'sound': 'C:\\Windows\Media\Glaucus.wav'
    },
    #{
    #    'name': 'SKY TIDES',
    #    'url': 'http://www.skytides.com/research',
    #    'selector': get_skytides,
    #    'sound': 'C:\\Windows\Media\Skytides.wav'
    #},
    {
        'name': 'GOTHAM',
        'url': 'https://gothamcityresearch.com/research/',
        'selector': get_gotham,
        'sound': 'C:\\Windows\Media\Gotham.wav'
    },
    {
        'name': 'BRONTE',
        'url': 'http://brontecapital.blogspot.com/2017/',
        'selector': get_bronte,
        'sound': 'C:\\Windows\Media\Bronte.wav'
    },
    {
        'name': 'BETAVILLE,
        'url': 'https://www.betaville.co.uk/',
        'selector': get_beta,
        'sound': 'C:\\Windows\Media\Betaville.wav'
    },
    #{
    #    'url': 'https://thestreetsweeper.org/',
    #    'selector': get_swept,
    #    'sound': 'C:\\Windows\Media\StreetSweeper.wav'
    #},
    #{
    #    'url': 'https://www.kerrisdalecap.com/blog/',
    #    'selector': get_kerrisdale,
    #    'sound': 'C:\\Windows\Media\Kcap.wav'
    #},
    #{
    #    'url': 'http://apps.shareholder.com/rss/rss.aspx?channels=7196&companyid=ABEA-4CW8X0&sh_auth=3100301180%2E0%2E0%2E42761%2Eb96f9d5de05fc54b98109cd0d905924d',
    #    'sound': 'C:\\Windows\Media\Tsla.wav'
    #},
    #{
    #    'url': 'https://ir.netflix.com/results.cfm?Quarter=&Year=2017',
    #    'selector': get_nflx,
    #    'sound': 'C:\\Windows\Media\NFLX.wav',
    #    'data_handler': open_nflx,
    #    'delay': .25
    #},
    #{
    #    'url': 'https://squareup.com/about/investors',
    #    'selector': get_sq,
    #    'sound': 'C:\\Windows\Media\SQ.wav',
    #    'delay': .25
    #},
    {
        'url': 'http://www.fda.gov/AboutFDA/ContactFDA/StayInformed/RSSFeeds/PressReleases/rss.xml',
        'delay': 2,
        'sound': 'C:\\Windows\Media\FDA.wav'
    },
    {
        'url': 'https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=reportsSearch.process',
        'sound': 'C:\\Windows\Media\Drugs.wav',
        'retriever': drug_retriever,
        'selector': get_drugs,  
    },
    {
        'url': 'https://www.usitc.gov/press_room/news_release/news_release_index.htm?field_release_date_value%5Bvalue%5D%5B',
        'sound': 'C:\\Windows\Media\ITC.wav',
        'retriever' : itc_retriever,
        'selector': get_itc_pr,
        'delay': 5
    },
    {
        'url': 'http://courts.delaware.gov/opinions/index.aspx?ag=supreme+court',
        'sound': 'C:\\Windows\Media\De.wav',
        'selector': get_de,
        'data_handler': open_de,
        'delay': 30
    },
    {
        'url': 'http://courts.delaware.gov/opinions/index.aspx?ag=court+of+chancery',
        'sound': 'C:\\Windows\Media\De.wav',
        'selector': get_de,
        'data_handler': open_de,
        'delay': 30
    },
    # PTAB

    # PACER
    #{
    #    'name': 'Cali. Central Dist. Court',
    #    'url': 'https://ecf.cacd.uscourts.gov/cgi-bin/WrtOpRpt.pl',
    #    'sound': "C:\\Windows\Media\Court.wav",
    #    'type': 'pacer',
    #    'case_nos': ['2:09-cv-05013', '2:16-cv-08697', '2:17-cv-02613', '8:14-cv-02004']
    #},
    #{
    #    'name': 'Cali. Northern Dist. Court',
    #    'url': 'https://ecf.casd.uscourts.gov/cgi-bin/WrtOpRpt.pl',
    #    'sound': "C:\\Windows\Media\Court.wav",
    #    'type': 'pacer',
    #    'case_nos': ['5:17-cv-00220', '5:16-cv-00923']
    #},
    {
        'name': 'Cali. Southern Dist. Court',
        'url': 'https://ecf.casd.uscourts.gov/cgi-bin/WrtOpRpt.pl',
        'sound': "C:\\Windows\Media\Court.wav",
        'type': 'pacer',
        'case_nos': ['3:15-cv-02287', '3:15-cv-02353', '3:15-cv-02324', '3:15-cv-02486', '3:17-cv-00108', '3:17-cv-01010']
    },
    #{
    #    'name': 'Connecticut Dist. Court',
    #    'url': 'https://ecf.ctd.uscourts.gov/cgi-bin/WrtOpRpt.pl',
    #    'sound': "C:\\Windows\Media\Court.wav",
    #    'type': 'pacer',
    #    'case_nos': ['3:16-cv-02056']
    #},
    #{
    #    'name': 'DC Dist. Court',
    #    'url': 'https://ecf.dcd.uscourts.gov/cgi-bin/WrtOpRpt.pl',
    #    'sound': 'C:\\Windows\Media\Court.wav',
    #    'type': 'pacer',
    #    'case_nos': ['1:17-cv-01006']
    #},
    {
        'name': 'Delaware Dist. Court',
        'url': 'https://ecf.ded.uscourts.gov/cgi-bin/WrtOpRpt.pl',
        'sound': 'C:\\Windows\Media\Court.wav',
        'type': 'pacer',
        'case_nos': ['1:16-cv-01243', '1:16-cv-01267', '1:16-cv-00944', '1:15-cv-00170', '1:16-cv-00666', '1:15-cv-00760', '1:17-cv-00711', '1:17-cv-00698', '1:15-cv-00839']
    },
    #{
    #    'name': 'Illinois Central Dist. Court',
    #    'url': 'https://ecf.ilcd.uscourts.gov/cgi-bin/WrtOpRpt.pl',
    #    'sound': 'C:\\Windows\Media\Court.wav',
    #    'type': 'pacer',
    #    'case_nos': []
    #},
    {
        'name': 'Illinois Northern Dist. Court',
        'url': 'https://ecf.ilnd.uscourts.gov/cgi-bin/WrtOpRpt.pl',
        'sound': 'C:\\Windows\Media\Court.wav',
        'type': 'pacer',
        'case_nos': ['1:16-cv-08637', '1:16-cv-07145', '1:17-cv-01164']
    },
    #{
    #    'name': 'Louisiana Eastern Dist. Court',
    #    'url': 'https://ecf.laed.uscourts.gov/cgi-bin/WrtOpRpt.pl',
    #    'sound': 'C:\\Windows\Media\Court.wav',
    #    'type': 'pacer',
    #    'case_nos': ['2:14-cv-02720', '2:14-md-02592']
    #},
    {
        'name': 'NJ Dist. Court',
        'url': 'https://ecf.njd.uscourts.gov/cgi-bin/WrtOpRpt.pl',
        'sound': 'C:\\Windows\Media\Court.wav',
        'type': 'pacer',
        'case_nos': ['2:13-cv-00391', '2:16-cv-04544', '2:16-cv-07704', '3:15-cv-05723', '3:16-cv-03642', '3:16-cv-01816', '2:15-cv-00697']
    },
    {
        'name': 'NY Southern Dist. Court',
        'url': 'https://ecf.nysd.uscourts.gov/cgi-bin/WrtOpRpt.pl',
        'sound': 'C:\\Windows\Media\Court.wav',
        'type': 'pacer',
        'case_nos': ['1:16-cv-08164']
    },
    #{
    #    'name': 'Pennsylvania Middle Dist. Court',
    #    'url': 'https://ecf.pamd.uscourts.gov/cgi-bin/WrtOpRpt.pl',
    #    'sound': 'C:\\Windows\Media\Court.wav',
    #    'type': 'pacer',
    #    'case_nos': ['3:17-cv-00101']
    #},
    #{
    #    'name': 'Texas Eastern Dist. Court',
    #    'url': 'https://ecf.txed.uscourts.gov/cgi-bin/WrtOpRpt.pl',
    #    'sound': 'C:\\Windows\Media\Court.wav',
    #    'type': 'pacer',
    #    'case_nos': ['2:15-cv-01455']
    #},
    #ITC
    #{
    #    'name': 'ITC 337-1010',
    #    'url': 'https://edis.usitc.gov/data/document?investigationNumber=337-1010',
    #    'sound': 'C:\\Windows\Media\Court case audio\XPER.wav',
    #    'selector': get_itc,
    #    'delay': 30
    #},
    #{
    #    'name': 'ITC 337-944',
    #    'url': 'https://edis.usitc.gov/data/document?investigationNumber=337-944',
    #    'sound': 'C:\\Windows\Media\Court case audio\ANET.wav',
    #    'selector': get_itc,
    #    'delay': 20
    #},
    {
        'name': 'ITC 337-945',
        'url': 'https://edis.usitc.gov/data/document?investigationNumber=337-945',
        'sound': 'C:\\Windows\Media\Court case audio\ANET.wav',
        'selector': get_itc,
        'delay': 30
    },
    #{
    #    'name': 'CGC-17-559555',
    #    'url': 'https://webapps.sftc.org/ci/CaseInfo.dll/datasnap/rest/TServerMethods1/GetROA/CGC17559555/06E8740C77B3BEF11189EA5B1292E4A7C9C731FB',
    #    'sound': 'C:\\Windows\Media\Court case audio\Wdc.wav',
    #    'retriever': calisuper_retriever
    #    'selector': get_calisuper,
    #    'delay': 30
    #},
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
    



