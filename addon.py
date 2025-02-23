# -*- coding: utf-8 -*-
import re
import time
import base64
import urllib.request, urllib.error, urllib.parse
import requests
from bs4 import BeautifulSoup
from kodibgcommon.settings import settings
from kodibgcommon.logging import log_info, log_error
from kodibgcommon.utils import *
from kodibgcommon.notifications import notify_error
import ssl


def get_products(url):
  '''
  Get all items from the 'predavaniya' and 'seriali' pages
  Products have no titles, only icons
  '''
  products = []
  log_info("GET " + host + url)
  ssl._create_default_https_context = ssl._create_unverified_context
  req = urllib.request.Request(host + url)
  text = urllib.request.urlopen(req).read().decode('utf-8')
  soup = BeautifulSoup(text, 'html5lib')
  el = soup.find("div", class_='order-listing-wrapper')

  imgs = el.find_all('img')
  log_info("Number of img elements found: %s" % len(imgs))
  links = el.find_all('a')
  linktext = el.find_all('span', class_='title')
  log_info("Number of a elements found: %s" % len(links))

  for i in range(0, len(imgs)):
    id = re.compile('\/(\d+)+\/').findall(links[i]['href'])
    if len(id) == 0:
      log_error("No href found!")
      continue
    log_info("Extracted product id: %s" % id[0])
    # Change url to load episodes from the Search url
    if not imgs[i]["src"].startswith("http"):
      logoSrc = 'https:' + imgs[i]['src']
    else:
      logoSrc = imgs[i]['src']
    title = linktext[i].get_text()
    item = {"title": title, "url": 'search/?id=' + id[0], "logo": logoSrc}
    products.append(item)

  return products
  
def get_episodes(url):
  '''
  Get all episodes from the search page
  '''
  episodes = []  
  log_info("GET " + host + url)
  ssl._create_default_https_context = ssl._create_unverified_context
  req = urllib.request.Request(host + url)
  req.add_header('User-agent', user_agent)
  text = urllib.request.urlopen(req).read().decode('utf-8')
  soup = BeautifulSoup(text, 'html5lib')
  el = soup.find("div", class_="search-page-wrapper")
  
  imgs = el.find_all('img')
  log_info("imgs: %s" % len(imgs))
  links = el.find_all('a')
  log_info("a: %s" % len(links))
  locks = el.find_all('span', class_='icon-locker')
  linktext = el.find_all('span', class_='title')
  
  # locked content is not viewable, so we are ignoring it
  for i in range(0, len(imgs) - len(locks)):
    title = linktext[i].get_text()
    item = {"title": title, "url": links[i]['href'], "logo": "https://" + imgs[i]['src']}
    episodes.append(item)
    
  for i in range(len(imgs) - len(locks), len(imgs)):
    title = linktext[i].get_text()
    item = {"title": "[COLOR red]"+title+"[/COLOR]", "url": None, "logo": "https://" + imgs[i]['src']}
    episodes.append(item)

  #pagination:
  try:
    next = soup.find('li', class_='page next')
    if next:
      href = next.a['href']
      item = {"title": next_page_title, "url": href}
      episodes.append(item)
  except Exception as er:
    log_error("Adding pagination failed %s" % er)

  return episodes  


def show_episodes(episodes):

  for episode in episodes:
    if episode['title'] != next_page_title:
      url = make_url({"action":"play_stream", "url": episode["url"], "title": episode["title"]})
      add_listitem_unresolved(episode["title"], url, iconImage=episode.get("logo"), thumbnailImage=episode.get("logo"))
    else:
      url = make_url({"action":"show_episodes", "url": episode["url"]})
      add_listitem_folder(episode["title"], url)

def get_stream(url):

  log_info("GET " + host2 + url)
  ssl._create_default_https_context = ssl._create_unverified_context
  req = urllib.request.Request(host2 + url)
  text = urllib.request.urlopen(req).read().decode('utf-8')
  soup = BeautifulSoup(text, 'html5lib')
  item = {"stream": None, "logo": None}
  
  title = soup.title.get_text()
  m = re.compile('url[\s:]+\'(.*)\',').findall(text)
  if len(m) > 0:
    url2 = m[0]
    log_info("resolved stream1: %s" % url2)
  else:
    log_error("No url found!")
    return
  req2 = urllib.request.Request(host2 + url2)
  text2 = urllib.request.urlopen(req2).read().decode('utf-8')
  soup2 = BeautifulSoup(text2, 'html5lib')
  m = re.compile('src[:=\s\'\"]+(.*m3u8)').findall(text2)
  if len(m) > 0:
    item["stream"] = m[0].replace('\\', '')
    if not item["stream"].startswith("http"):
      item["stream"] = 'https:' + item["stream"]
    log_info("resolved stream2: %s" % item["stream"])
 
    m = re.compile('poster[:\s\'"]+(http.*jpg)').findall(text)
    if len(m) > 0:
      item["logo"] = m[0].replace('\\', '')
      if not item["logo"].startswith("http"):
        item["logo"] = 'https:'+ item["logo"]
  else:
    log_error("No streams found!")
  return item


def update(name, location, crash=None):
  try:
      lu = settings.last_update
      day = time.strftime("%d")
      if lu == "" or lu != day:
        from ga import ga
        settings.last_update = day
        p = {}
        p['an'] = get_addon_name()
        p['av'] = get_addon_version()
        p['ec'] = 'Addon actions'
        p['ea'] = name
        p['ev'] = '1'
        p['ul'] = get_kodi_language()
        p['cd'] = location
        ga('UA-79422131-4').update(p, crash)
  except:
    pass
    
params = get_params()
action = params.get("action")
id = params.get("id")
url = params.get("url")
title = params.get("title")
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
view_mode = 500
host = base64.b64decode("aHR0cHM6Ly9idHZwbHVzLmJnLw==").decode('utf-8')
host2 = base64.b64decode("aHR0cHM6Ly9idHZwbHVzLmJn").decode('utf-8')
next_page_title = 'Следваща страница'

if action == None:
  items = [
    {'title': 'Предавания', "url": "predavaniya", "action": "show_products"},
    {'title': 'Сериали', "url": "seriali", "action": "show_products"},
    {'title': 'Новини', "url": "search/?type=101", "action": "show_episodes"},
    {'title': 'Спорт', "url": "search/?type=102", "action": "show_episodes"},
    {'title': 'Времето', "url": "search/?type=103", "action": "show_episodes"},
    {'title': 'bTV на живо', "url": "live", "action": "play_live"},
    {'title': 'Търсене', "url": "search", "action": "search"},
  ]
  
  for item in items:
    url = make_url({"url": item['url'], "action": item['action']})
    if item['url'] == 'live':
      add_listitem_unresolved(item['title'], url)
    else:
      add_listitem_folder(item['title'], url)
  
  update('browse', 'Categories')
  view_mode = 50
  
  
elif action == 'show_products':

  products = get_products(url)
  log_info("Found %s products" % len(products))
  
  for product in products:
    # Set empty title, as there are no titles only icons
    url = make_url({"action":"show_episodes", "url": product["url"]})
    add_listitem_folder(product["title"], url, iconImage=product["logo"], thumbnailImage=product["logo"])

  
elif action == 'show_episodes':
  show_episodes(get_episodes(url))

  
elif action == 'play_stream':
  stream = get_stream(url)["stream"]
  log_info('Extracted stream %s ' % stream)
  add_listitem_resolved_url(title, stream)

  
elif action == 'play_live':

  if settings.btv_username == '' or settings.btv_password == '':
    notify_error('Липсва потребителско име и парола за bTV')

  body = { "username": settings.btv_username, "password": settings.btv_password }
  headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
  s = requests.session()

  r = s.post(base64.b64decode('aHR0cHM6Ly9idHZwbHVzLmJnL2xiaW4vc29jaWFsL2xvZ2luLnBocA=='), headers=headers, data=body)
  log_info(r.text)
  
  if r.json()["resp"] != "success":
    log_info("Unable to login to btv.bg")
  else:
    url = base64.b64decode('aHR0cHM6Ly9idHZwbHVzLmJnL2xiaW4vdjMvYnR2cGx1cy9wbGF5ZXJfY29uZmlnLnBocD9tZWRpYV9pZD0yMTEwMzgzNjI1Jl89JXM=').decode('utf-8')
    log_info(url)
    url = url % str(time.time() * 100)
    log_info("URL: %s" % url)
    r = s.get(url, headers=headers)
    m = re.compile('(http.*\.m3u.*?)[\s\'"\\\\]+[\s\'"\\\\]+').findall(r.text)
    if len(m) > 0:
      stream = m[0].replace('\/', '/')
      if not stream.startswith('http'):
        stream = 'https:' + stream
      log_info('Извлечен видео поток %s' % stream)  
      add_listitem_resolved_url('bTV на живо', stream)
    else:
      log_info("No match for playlist url found")

      
elif action == 'search':

  keyboard = xbmc.Keyboard('', 'Търсене...')
  keyboard.doModal()
  searchText = ''
  if keyboard.isConfirmed():
    searchText = urllib.parse.quote_plus(keyboard.getText())
    if searchText != '':
      show_episodes(get_episodes('search/?q=%s' % searchText))
        
        
xbmcplugin.endOfDirectory(get_addon_handle())
xbmc.executebuiltin("Container.SetViewMode(%s)" % view_mode)
