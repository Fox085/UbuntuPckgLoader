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
import argparse

url = 'https://packages.ubuntu.com/jammy-updates/xrdp'
url = 'https://packages.ubuntu.com/jammy/python3-pip'

DEBUG = False

ap = argparse.ArgumentParser(
        prog='Ubuntu Package Downloader',
        description='This program allow to download packages from packages.ubuntu.com with all dependencies in .deb extension',
        epilog='Why this program was made only in 2026?'
    )
ap.add_argument('url', help='direct src to needed package on packages.ubuntu.com. Example: "https://packages.ubuntu.com/jammy-updates/xrdp"')
ap.add_argument('-o', '--dir-to-save', help='directory to save package. If undefined, use package root name, like "xrdp"')
ap.add_argument('--arch', help='what architecture to download. "amd64" by default', default='amd64')
ap.add_argument('--all-arch', help='download all architectures. False by default', action='store_true', default=False)
# ap.add_argument('--only-one-arch', help='download only one selected arch - only "amd64" or "all", for example. False by default', action='store_true', default=False)
ap.add_argument('-c', '--cache', help='does this program use cache for download, like, do i need to download already loaded packages? Only checks packages in this program argument "GlobalPackagePath". Enabled by default', action='store_true', default=True)
ap.add_argument('--global-package-path', help='where to store downloaded packages? By default, the dir is "global" in script working dir', default='global')
ap.add_argument('--do-recommends', help='download recommended packages? By default - disabled', action='store_true', default=False)
ap.add_argument('--do-suggestions', help='download suggested packages? By default - disabled', action='store_true', default=False)
ap.add_argument('--cache-save-file', help='path to save file, where i write root packages, that already downloaded. Stored in GlobalPackagePath. Joined from there. Default: "downloaded.txt"', default='downloaded.txt')

args = ap.parse_args()

url = args.url
dir_to_save = args.dir_to_save
arch = args.arch
AllArch = args.all_arch
# OnlyOneArch = args.only_one_arch
OnlyOneArch = not AllArch
useGlobalPackage = args.cache
GlobalPackagePath = args.global_package_path
recommends = args.do_recommends
suggestions = args.do_suggestions
CacheSaveFile = args.cache_save_file

if dir_to_save is None: dir_to_save = os.path.basename(ps.urlparse(url).path)
#if arch is None: arch = 'amd64'
#if useGlobalPackage is None: useGlobalPackage = True
#if GlobalPackagePath is None: GlobalPackagePath = 'global'
#if recommends is None: recommends = False # ulrec
#if suggestions is None: suggestions = False # ulsug
#if CacheSaveFile is None: CacheSaveFile = 'downloaded.txt'

print(url, dir_to_save, arch, useGlobalPackage, GlobalPackagePath, recommends, suggestions, CacheSaveFile, AllArch, OnlyOneArch)

# exit()

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

def GetDownloadLink(body, baseurl):
    try:
        ws = [(i.text, i['href']) for i in body.select('#pdownload')[0].select('a')]
        if AllArch:
            w = ws
        else:
            wall = [i for i in ws if 'all' in i[0]]
            warch = [i for i in ws if arch in i[0]]
            w = wall + warch
    except IndexError:
        allAnchors = body.select('a')
        for i in allAnchors:
            if i['href'] == fuck_linux_virtual_bullshit_package_i_fucking_hate_this_busllshit_system:
                print('this useless piece of crap is fucking virtual package, because linux cannot fucking comprehend the idea about packing 2+ packages into one packet for saving the internet crap and at the same time the idea, that not all the machines HAVE the fucking internet. #FUCK_LINUX')
                return fuck_linux_virtual_bullshit_package_i_fucking_hate_this_busllshit_system
    if OnlyOneArch:
        w = w[:1]
    #urls = GetAbsolutePath(w, url)
    urls = [(url[0], ps.urljoin(baseurl, url[1])) for url in w]
    if len(urls) > 0:
        return urls
    # raise Error('No Download links')
    print('error in GetDownloadLink', baseurl)
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

def DownloadMirror(mirrors, pckgurl, arch, dts=dir_to_save):
    '''
    return code: 1 = success, 0 = fail
    '''
    addr = pckgurl + '_' + arch
    if addr in downloaded and downloaded[addr] == 'inProgress': return 1
    downloaded[addr] = 'inProgress'
    for mirror in mirrors:
        try:
            r = DownloadFile(mirror, addr, dts)
            downloaded[addr] = mirror
            return 1
        except Exception as e:
            print('DownloadMirror', e, mirror, pckgurl, arch)
    downloaded[addr] = 'failed'
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
    print('parsing', url)
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
    
    download_links = GetDownloadLink(body, url)
    if download_links != fuck_linux_virtual_bullshit_package_i_fucking_hate_this_busllshit_system:
        for arch, download_link in download_links:
            print('started', url + '_' + arch)
            download_body = GetParsedPage(download_link)
            mirrors = GetMirrors(download_body)
            status = DownloadMirror(mirrors, url, arch, dts)
            if not status:
                status = DownloadFromSecurity(download_body, url, dts)
            print('finished', url + '_' + arch)
        print('finished', url)
        downloaded[url] = 'done'
    else:
        downloaded[url] = 'virtual crap'
        print('useless', url)

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
                    