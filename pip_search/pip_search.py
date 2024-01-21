import re
import os
from loguru import logger
from argparse import Namespace
from dataclasses import InitVar, dataclass
from datetime import datetime
from typing import Generator, Union
from urllib.parse import urljoin

import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup

DEBUG = True

class Config:
    """Configuration class"""

    api_url: str = "https://pypi.org/search/"
    page_size: int = 2
    sort_by: str = "name"
    date_format: str = "%d-%-m-%Y"
    link_defualt_format: str = "https://pypi.org/project/{package.name}"


config = Config()


@dataclass
class Package:
    """Package class"""

    name: str
    version: str
    released: str
    description: str
    link: InitVar[str] = None

    def __post_init__(self, link: str = None):
        self.link = link or config.link_defualt_format.format(package=self)
        self.released_date = datetime.strptime(self.released, "%Y-%m-%dT%H:%M:%S%z")
        self.stars: int = 0
        self.forks: int = 0
        self.watchers: int = 0
        self.github_link: str = ''
        self.info_set: bool = False

    def released_date_str(self, date_format: str = config.date_format) -> str:
        """Return the released date as a string formatted
        according to date_formate ou Config.date_format (default)

        Returns:
            str: Formatted date string
        """
        return self.released_date.strftime(date_format)

    def set_gh_info(self, info):
        self.stars = info['stars']
        self.forks = info['forks']
        self.watchers = info['watchers']
        self.github_link = info['github_link']
        self.info_set = True

# todo add url to results
def search(query: str, opts: Union[dict, Namespace] = {}) -> Generator[Package, None, None]:
    """Search for packages matching the query

    Yields:
        Package: package object
    """
    snippets = []
    session = requests.Session()
    for page in range(1, config.page_size + 1):
        params = {"q": query, "page": page}
        r = session.get(config.api_url, params=params)
        soup = BeautifulSoup(r.text, "html.parser")
        snippets += soup.select('a[class*="package-snippet"]')
        logger.debug(f'[s] p:{page} snippets={len(snippets)} query={query} ')
    authparam = None
    if opts.extra:
        GITHUBAPITOKEN = os.getenv('GITHUBAPITOKEN')
        GITHUB_USERNAME = os.getenv('GITHUB_USERNAME')
        authparam = HTTPBasicAuth(GITHUB_USERNAME, GITHUBAPITOKEN)

    # if "sort" in opts:
    #     if opts.sort == "name":
    #         snippets = sorted(snippets,key=lambda s: s.select_one('span[class*="package-snippet__name"]').text.strip())
    #     elif opts.sort == "version":
    #         from pkg_resources import parse_version
    #         snippets = sorted(snippets,key=lambda s: parse_version(s.select_one('span[class*="package-snippet__version"]').text.strip()))
    #     elif opts.sort == "released":
    #         snippets = sorted(snippets,key=lambda s: s.select_one('span[class*="package-snippet__created"]').find("time")["datetime"])

    for snippet in snippets:
        link = urljoin(config.api_url, snippet.get("href"))
        package = re.sub(r"\s+", " ", snippet.select_one('span[class*="package-snippet__name"]').text.strip())
        version = re.sub(r"\s+"," ",snippet.select_one('span[class*="package-snippet__version"]').text.strip())
        released = re.sub(r"\s+"," ",snippet.select_one('span[class*="package-snippet__created"]').find("time")["datetime"])
        description = re.sub(r"\s+"," ",snippet.select_one('p[class*="package-snippet__description"]').text.strip())
        pack = Package(package, version, released, description, link)
        if opts.extra:
            info = get_github_info(link, authparam, session)
            if info:
                pack.set_gh_info(info)
                # logger.debug(f'[s] snippet {s} / {len(snippets)} link: {link}')
        yield pack #Package(package, version, released, description, link, links)

def get_repo_info(repo, auth, session):
    #info = {'stars':'', 'forks':'', 'watchers':'', 'set':False}
    info = {'stars':0, 'forks':0, 'watchers':0, 'set':False, 'github_link':''}
    try:
        reponame = repo.split('github.com/')[1].rstrip('/')
    except IndexError as e:
        logger.error(f'[r] err:{e} repo:{repo}')
        return info
    apiurl = f'https://api.github.com/repos/{reponame}'
    r = session.get(apiurl, auth=auth)
    # logger.info(f'[r] repo:{repo} apiurl: {apiurl} r={r.status_code}')
    if r.status_code == 401:
        if DEBUG:
            logger.error(f'[r] autherr:401 repo: {repo} apiurl: {apiurl} a:{auth}')
        return info
    if r.status_code == 404:
        if DEBUG:
            logger.warning(f'[r] {r.status_code} url: {repo} r: {reponame} apiurl: {apiurl} not found' )
        return info
    if r.status_code == 403:
        if DEBUG:
            logger.warning(f'[r] {r.status_code} r: {reponame} apiurl: {apiurl} API rate limit exceeded')
        return info
    if r.status_code == 200:
        try:
            info['stars'] = r.json().get("stargazers_count",0) # str(r.json()["stargazers_count"])
            info['forks'] = r.json().get("forks_count",0)
            info['watchers'] = r.json().get("watchers_count",0)
            info['github_link'] = repo
            info['set'] = True
            return info
        except (KeyError, TypeError, AttributeError) as err:
            logger.error(f'[gri] {err} r:{r.status_code} apiurl:{apiurl} rj:{r.json()}')
            logger.error(f'[gri] info:{info}')
            return info

def get_github_info(repolink, authparam, session):
    gh_link = None
    gh_link = get_links(repolink, session)
    if gh_link:
        info = get_repo_info(repo=gh_link['github'], auth=authparam, session=session)
        return info
    else:
        return None

def get_links(pkg_url, session):
    # s = requests.session()
    r = session.get(pkg_url)
    soup = BeautifulSoup(r.text, "html.parser")
    homepage = ''
    githublink = ''
    try:
        # .vertical-tabs__tabs > div:nth-child(2) > ul:nth-child(2) > li:nth-child(2) > a:nth-child(1)
        homepage = soup.select_one('.vertical-tabs__tabs > div:nth-child(2) > ul:nth-child(2) > li:nth-child(1) > a:nth-child(1)',href=True).attrs['href']
        if 'issues' in homepage:
            homepage = soup.select_one('.vertical-tabs__tabs > div:nth-child(2) > ul:nth-child(2) > li:nth-child(2) > a:nth-child(1)',href=True).attrs['href']
        if 'github' in homepage:
            githublink = homepage
            githublink = githublink.replace('/tags','')
            return {'github':githublink, 'homepage':homepage}
        else:
            return None
    except AttributeError as e:
        #pass
        logger.warning(f'[err] err:{e} homepage not found pkg_url:{pkg_url}')
        return None
    # try:
    #     githublink = soup.select_one('.vertical-tabs__tabs > div:nth-child(2) > ul:nth-child(2) > li:nth-child(2) > a:nth-child(1)',href=True).attrs['href']
    #     githublink = githublink.replace('/tags','')
    #     return {'github':githublink, 'homepage':homepage}
    # except AttributeError as e:
    #     # pass
    #     logger.warning(f'[err] err:{e} gh link not found pkg_url:{pkg_url} h:{homepage}')
    # return {'github':githublink, 'homepage':homepage}
