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
import concurrent.futures as cf

url = 'https://packages.ubuntu.com/jammy-updates/xrdp'
url = 'https://packages.ubuntu.com/jammy/python3-pip'

DEBUG = False
arch = 'amd64'
useGlobalPackage = True
GlobalPackagePath = 'global'
recommends = False # ulrec
suggestions = False # ulsug
CacheSaveFile = 'downloaded.txt'

fuck_linux_virtual_bullshit_package_i_fucking_hate_this_busllshit_system = 'https://www.debian.org/doc/debian-policy/ch-binary.html#s-virtual_pkg'

def SaveDownloaded():
    with open(GetPathToFileInCache(CacheSaveFile), 'w', encoding='utf8') as f:
        for pckgname in saved:
            f.write(pckgname + '\t' + saved[pckgname] + '\n')

def GetParsedPage(url, verbose):
    status = 100
    while not (200 <= status <= 399):
        a = rq.get(url)
        status = a.status_code
        if verbose:
            print(status, url)
    body = bs(a.content, 'html.parser')
    return body

def GrabDeps(block):
    '''
    Grab all href in this block
    '''
    deps = []
    try:
        anchors = block.select('a')
        for anchor in anchors:
            deps.append(anchor['href'])
    except Exception as e:
        print('GrabDeps', e)
    return deps

def GetDeps(body: bs):
    '''
    Parsing all dependencies listed on the given page.
    parsing Pre-deps and deps as one, recommends and suggestions at request
    returns list of anchors' href to dependencies
    '''
    deps = []
    # Im cutting 1:, because at the page the is a legend above, which tells you, how to define dependency from recommends, sug.. etc, it has the same class name
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
    '''
    Join relative path of urls with base to get absolute path to url
    '''
    ans = [ps.urljoin(base, url) for url in urls]
    return ans

def GetDownloadLink(body, arch, url, verbose):
    try:
        wall = [i['href'] for i in body.select('#pdownload')[0].select('a') if 'all' in i]
        warch = [i['href'] for i in body.select('#pdownload')[0].select('a') if arch in i]
        w = wall + warch
    except IndexError:
        allAnchors = body.select('a')
        for i in allAnchors:
            if i['href'] == fuck_linux_virtual_bullshit_package_i_fucking_hate_this_busllshit_system:
                if verbose:
                    print('this useless piece of crap is fucking virtual package, because linux cannot fucking comprehend the idea about packing 2+ packages into one packet for saving the internet crap and at the same time the idea, that not all the machines HAVE the fucking internet. #FUCK_LINUX')
                return fuck_linux_virtual_bullshit_package_i_fucking_hate_this_busllshit_system
    urls = GetAbsolutePath(w, url)
    if len(urls) > 0:
        if len(urls) > 1 and verbose:
            print('Very Curious', urls)
        return urls[0]
    # raise Error('No Download links')
    print('error in GetDownloadLink', url, arch)
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
def DownloadFile(url, pckgname, dts, verbose):
    if url in done: return
    t = ps.urlparse(url)
    filename = os.path.basename(t.path)
    dest = os.path.join(dts, filename)
    if filename in globalPackage:
        if verbose:
            print(f'copied {filename} from cache')
        copy(GetPathToFileInCache(filename), dest)
        saved[pckgname] = filename
        SaveDownloaded()
        done.add(url)
        return (dest, None)
    ans = rqget.urlretrieve(url, dest)
    if useGlobalPackage:
        if verbose:
            print('cached')
        copy(ans[0], GetPathToFileInCache(filename))
        saved[pckgname] = filename
        SaveDownloaded()
    done.add(url)
    return ans

def DownloadMirror(mirrors, pckgurl, dts, verbose):
    '''
    return code: 1 = success, 0 = fail
    '''
    if pckgurl in downloaded and downloaded[pckgurl] == 'inProgress': return 1
    downloaded[pckgurl] = 'inProgress'
    for mirror in mirrors:
        try:
            r = DownloadFile(mirror, pckgurl, dts, verbose)
            downloaded[pckgurl] = mirror
            return 1
        except Exception as e:
            print('DownloadMirror', e, mirror, pckgurl)
    downloaded[pckgurl] = 'failed'
    return 0

def DownloadFromSecurity(body, pckgurl, dts, verbose):
    # security as in "Ubuntu security updates are officially distributed only via security.ubuntu.com."
    anchors = body.select('a')
    for a in anchors:
        href = a['href']
        if 'security.ubuntu.com' in href:
            r = DownloadFile(href, pckgurl, dts, verbose)
            downloaded[pckgurl] = href
            return 1
    downloaded[pckgurl] = 'failed'
    return 0

# dict of {[package_name: string]: status}, where status is one of these: 'planned' | 'parsing' | 'finished' | 'virtual crap' | 'failed'
downloaded = {}
# dict of all loaded files {[package_name: string] : path_to_file}, where path_to_file is relative path for global path
saved = {}
# dict of {[package_name]: dependencies}, where dependencies is the list[string] of dependencies in urls
deptree = {}

def DownloadPackageWithDependencies(url, arch, dts, threads = 4, verbose = False, level = 0, copy_from_cache=[], download=[], queue = []):
    '''
    url to root of package
    arch is like 'amd64', 'i386' etc...
    dts is dir_to_save - where to load, so that all the packages, needed for work of first package will be in the same directory
    threads - how much simultanious workers, or Executor

    the rest is private, do not give them
    '''
    # Check that i already started that package
    if url in downloaded and downloaded[url] != 'planned': return 'planned'
    if verbose:
        print(url, 'parsing')
    downloaded[url] = 'parsing'

    if level == 0 and type(threads) == int:
        Executor = cf.ThreadPoolExecutor(max_workers=threads)
    else:
        Executor = threads
    
    def GetDependenciesForThisUrl():
        # Load the page of extension, where is listed its dependencies and download block
        body = GetParsedPage(url, verbose)

        # Load all dependencies
        deps = GetDeps(body)
        deps_absolute = GetAbsolutePath(deps, url)
        for dep in deps_absolute:
            if dep in downloaded: continue
            downloaded[dep] = 'planned'
        deptree[url] = deps_absolute
        
        # I first collect all dependencies of dependencies of dependencies of ....
        for dep in deps_absolute:
            if dep in downloaded and downloaded[dep] != 'planned': continue
            DownloadPackageWithDependencies(dep, arch, dts, Executor, verbose, level + 1, copy_from_cache, download, queue)
    
        if url in saved:
            copy_from_cache.append(url)
            # print(f'copied {url} from cache')
            # copy(GetPathToFileInCache(saved[url]), os.path.join(dts, saved[url]))
            return url
        
        download_link = GetDownloadLink(body, arch, url, verbose)
        if download_link != fuck_linux_virtual_bullshit_package_i_fucking_hate_this_busllshit_system:
            download_body = GetParsedPage(download_link, verbose)

            download.append((url, download_body))
            # status = DownloadMirror(mirrors, url, dts)
            # if not status:
            #     status = DownloadFromSecurity(download_body, url, dts)
            # print(url, 'finished')
        else:
            downloaded[url] = 'virtual crap'
            if verbose:
                print(url, 'useless')
        return url

    queue.append(Executor.submit(GetDependenciesForThisUrl))

    if level == 0:
        completed = 0
        done = set()
        prefix = '' if verbose else '\r'
        end = '\n' if verbose else ''
        start = '' if verbose else '\n'
        while 1:
            total = len(queue)
            for future in cf.as_completed(queue):
                t = future.result()
                if type(t) == str and t not in done:
                    done.add(t)
                    if completed != len(done):
                        completed = len(done)
                        print(f'{prefix}completed: {completed} / {len(queue)}', end=end)
            if len(queue) == total:
                break
        if not verbose: print()

        if len(copy_from_cache) > 0:
            print(f'Will be copied {len(copy_from_cache)} from cache')
        if len(download) > 0:
            print(f'Will be downloaded {len(download)} from internet')

        def CopyFromCache(url):
            copy(GetPathToFileInCache(saved[url]), os.path.join(dts, saved[url]))
            if verbose:
                print(f'copied {url} from cache')

        def DownloadFromInternet(url, download_body):
            mirrors = GetMirrors(download_body)
            status = DownloadMirror(mirrors, url, dts, verbose)
            if not status:
                status = DownloadFromSecurity(download_body, url, dts, verbose)
            if verbose:
                print(url, 'finished')

        queue = []
        for url in copy_from_cache:
            future = Executor.submit(CopyFromCache, url)
            # CopyFromCache(url)
            queue.append(future)

        for url, download_body in download:
            future = Executor.submit(DownloadFromInternet, url, download_body)
            # CopyFromCache(url)
            queue.append(future)
        
        total = len(copy_from_cache) + len(download)
        completed = 0

        for future in cf.as_completed(queue):
            completed += 1
            print(f'{prefix}completed: {completed} / {total}', end=end)

        print(f'{start}all is done')

if __name__ == '__main__':
    ap = argparse.ArgumentParser(
            prog='Ubuntu Package Downloader',
            description='This program allow to download packages from packages.ubuntu.com with all dependencies in .deb extension',
            epilog='Why this program was made only in 2026?'
        )
    ap.add_argument('url', help='direct src to needed package on packages.ubuntu.com. Example: "https://packages.ubuntu.com/jammy-updates/xrdp"')
    ap.add_argument('-o', '--dir-to-save', help='directory to save package. If undefined, use package root name, like "xrdp"')
    ap.add_argument('--arch', help='what architecture to download. "amd64" by default', default='amd64')
    ap.add_argument('-c', '--cache', help='does this program use cache for download, like, do i need to download already loaded packages? Only checks packages in this program argument "GlobalPackagePath". Enabled by default', action='store_true', default=True)
    ap.add_argument('--global-package-path', help='where to store downloaded packages? By default, the dir is "global" in script working dir', default='global')
    ap.add_argument('--do-recommends', help='download recommended packages? By default - disabled', action='store_true', default=False)
    ap.add_argument('--do-suggestions', help='download suggested packages? By default - disabled', action='store_true', default=False)
    ap.add_argument('--cache-save-file', help='path to save file, where i write root packages, that already downloaded. Stored in GlobalPackagePath. Joined from there. Default: "downloaded.txt"', default='downloaded.txt')
    ap.add_argument('--threads', help='how much workers launch for download, default = 4', type=int, default=4)
    ap.add_argument('-v', '--verbose', help='verbose, False by default', action='store_true', default=False)

    args = ap.parse_args()

    url = args.url
    dir_to_save = args.dir_to_save
    arch = args.arch
    useGlobalPackage = args.cache
    GlobalPackagePath = args.global_package_path
    recommends = args.do_recommends
    suggestions = args.do_suggestions
    CacheSaveFile = args.cache_save_file
    threads = args.threads
    verbose = args.verbose

    if dir_to_save is None: dir_to_save = os.path.basename(ps.urlparse(url).path)

    print(url, dir_to_save, arch, useGlobalPackage, GlobalPackagePath, recommends, suggestions, CacheSaveFile)
    
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
    
    DownloadPackageWithDependencies(url, arch, dir_to_save, threads, verbose)

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
    