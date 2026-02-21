# -*- coding: utf-8 -*-
"""
Created on Sat Feb 21 10:23:20 2026

@author: Fox
"""

from bs4 import BeautifulSoup as bs
import requests as rq
import urllib.parse as ps
import os
import urllib.request as rqget
from shutil import copy
import argparse as ap

url = 'https://packages.ubuntu.com/jammy-updates/xrdp'
url = 'https://packages.ubuntu.com/jammy/python3-pip'
dir_to_save = os.path.basename(ps.urlparse(url).path)
arch = 'amd64'

useGlobalPackage = True
GlobalPackagePath = 'global'
recommends = False # ulrec
suggestions = False # ulsug
DEBUG = False
CacheSaveFile = 'downloaded.txt'

fuck_linux_virtual_bullshit_package_i_fucking_hate_this_busllshit_system = 'https://www.debian.org/doc/debian-policy/ch-binary.html#s-virtual_pkg'

def SaveDownloaded():
    with open(GetPathToFileInCache(CacheSaveFile), 'w', encoding='utf8') as f:
        for pckgname in saved:
            f.write(pckgname + '\t' + saved[pckgname] + '\n')

def GetParsedPage(url):
    status = 100
    while not (200 <= status <= 399):
        a = rq.get(url)
        status = a.status_code
        print(status)
    body = bs(a.content, 'html.parser')
    return body

def GrabDeps(block):
    deps = []
    try:
        anchors = block.select('a')
        for anchor in anchors:
            deps.append(anchor['href'])
    except Error as e:
        print('GrabDeps', e)
    return deps

def GetDeps(body):
    deps = []
    uldep = body.select('.uldep')[1:]
    for block in uldep:
        deps += GrabDeps(block)
    
    if recommends:
        ulrec = body.select('.ulrec')[1:]
        for block in ulrec:
            deps += GrabDeps(block)
            
    if suggestions:
        ulsug = body.select('.ulsug')[1:]
        for block in ulsug:
            deps += GrabDeps(block)
            
    return deps

def GetAbsolutePath(urls, base=url):
    ans = [ps.urljoin(base, url) for url in urls]
    return ans

def GetDownloadLink(body, url):
    try:
        wall = [i['href'] for i in body.select('#pdownload')[0].select('a') if 'all' in i]
        warch = [i['href'] for i in body.select('#pdownload')[0].select('a') if arch in i]
        w = wall + warch
    except IndexError:
        allAnchors = body.select('a')
        for i in allAnchors:
            if i['href'] == fuck_linux_virtual_bullshit_package_i_fucking_hate_this_busllshit_system:
                print('this useless piece of crap is fucking virtual package, because linux cannot fucking comprehend the idea about packing 2+ packages into one packet for saving the internet crap and at the same time the idea, that not all the machines HAVE the fucking internet. #FUCK_LINUX')
                return fuck_linux_virtual_bullshit_package_i_fucking_hate_this_busllshit_system
    urls = GetAbsolutePath(w, url)
    if len(urls) > 0:
        if len(urls) > 1:
            print('Very Curious', urls)
        return urls[0]
    # raise Error('No Download links')
    print('error in GetDownloadLink', url)
    return []

def GetPathToFileInCache(file):
    path = os.path.join(GlobalPackagePath, file)
    return path

def GetMirrors(body):
    cards = body.select('.cardleft, .cardright')
    mirrors = []
    for card in cards:
        anchors = card.select('a')
        for anchor in anchors:
            mirrors.append(anchor['href'])
    return mirrors

done = set()
def DownloadFile(url, pckgname, dts=dir_to_save):
    if url in done: return
    t = ps.urlparse(url)
    filename = os.path.basename(t.path)
    dest = os.path.join(dts, filename)
    if filename in globalPackage:
        print(f'copied {filename} from cache')
        copy(GetPathToFileInCache(filename), dest)
        saved[pckgname] = filename
        SaveDownloaded()
        done.add(url)
        return (dest, None)
    ans = rqget.urlretrieve(url, dest)
    if useGlobalPackage:
        print('cached')
        copy(ans[0], GetPathToFileInCache(filename))
        saved[pckgname] = filename
        SaveDownloaded()
    done.add(url)
    return ans

def DownloadMirror(mirrors, pckgurl, dts=dir_to_save):
    '''
    return code: 1 = success, 0 = fail
    '''
    if pckgurl in downloaded and downloaded[pckgurl] == 'inProgress': return 1
    downloaded[pckgurl] = 'inProgress'
    for mirror in mirrors:
        try:
            r = DownloadFile(mirror, pckgurl, dts)
            downloaded[pckgurl] = mirror
            return 1
        except Exception as e:
            print('DownloadMirror', e, mirror, pckgurl)
    downloaded[pckgurl] = 'failed'
    return 0

def DownloadFromSecurity(body, pckgurl, dts=dir_to_save):
    # security as in "Ubuntu security updates are officially distributed only via security.ubuntu.com."
    anchors = body.select('a')
    for a in anchors:
        href = a['href']
        if 'security.ubuntu.com' in href:
            r = DownloadFile(href, pckgurl, dts)
            downloaded[pckgurl] = href
            return 1
    downloaded[pckgurl] = 'failed'
    return 0

downloaded = {}
saved = {}
deptree = {}

basepath = os.path.basename(ps.urlparse(url).path)
os.makedirs(basepath, exist_ok=True)
if useGlobalPackage:
    os.makedirs(GlobalPackagePath, exist_ok=True)
    globalPackage = set(os.listdir(GlobalPackagePath))
    try:
        with open(GetPathToFileInCache(CacheSaveFile), 'r', encoding='utf8') as f:
            for line in f:
                pckgname, file = line.strip('\n').split('\t')
                saved[pckgname] = file
    except: pass

def DownloadPackageWithDependencies(url, dts = dir_to_save):
    if url in downloaded and downloaded[url] != 'planned': return
    print(url, 'parsing')
    downloaded[url] = 'parsing'
    body = GetParsedPage(url)
    deps = GetDeps(body)
    deps_absolute = GetAbsolutePath(deps, url)
    for dep in deps_absolute:
        if dep in downloaded: continue
        downloaded[dep] = 'planned'
    deptree[url] = deps_absolute
    for dep in deps_absolute:
        DownloadPackageWithDependencies(dep, dts)
    
    if url in saved:
        print(f'copied {url} from cache')
        copy(GetPathToFileInCache(saved[url]), os.path.join(dts, saved[url]))
        return
    
    download_link = GetDownloadLink(body, url)
    if download_link != fuck_linux_virtual_bullshit_package_i_fucking_hate_this_busllshit_system:
        download_body = GetParsedPage(download_link)
        mirrors = GetMirrors(download_body)
        status = DownloadMirror(mirrors, url, dts)
        if not status:
            status = DownloadFromSecurity(download_body, url, dts)
        print(url, 'finished')
    else:
        downloaded[url] = 'virtual crap'
        print(url, 'useless')

DownloadPackageWithDependencies(url)

print('success')

if useGlobalPackage:
    SaveDownloaded()

failed = []
for i in downloaded:
    if downloaded[i] == 'failed':
        failed.append(i)

if len(failed) > 0:
    print('failed to load:')
    print('\n'.join(failed))

if DEBUG == True:
    def ClearFromTrash(filename):
        filename = filename.replace('1%3a', '')
        filename = filename.replace('2%3a', '')
        return filename
    linux = [ClearFromTrash(i) for i in os.listdir(r'D:\Quick Share\xrdpp')]
    me = os.listdir(r'D:\UbuntuPckgLoader\xrdp')
    ml = set(me) - set(linux)
    lm = set(linux) - set(me)
    
    deptree_diff = {}
    ml2 = []
    for i in downloaded:
        t = os.path.basename(ps.urlparse(downloaded[i]).path)
        if t in ml:
            ml2.append(i)
    for dep in deptree:
        deps = deptree[dep]
        for d in deps:
            for diff in ml2:
                if diff in d:
                    if dep not in deptree_diff:
                        deptree_diff[dep] = []
                    deptree_diff[dep].append(diff)
                    