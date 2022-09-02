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
    info_set: bool = False
    link: InitVar[str] = None

    def __post_init__(self, link: str = None):
        self.link = link or config.link_defualt_format.format(package=self)
        self.released_date = datetime.strptime(
            self.released, "%Y-%m-%dT%H:%M:%S%z"
        )
        self.stars: str = ''
        self.forks: str = ''
        self.watchers: str = ''
        self.github_link: str = ''

    def released_date_str(self, date_format: str = config.date_format) -> str:
        """Return the released date as a string formatted
        according to date_formate ou Config.date_format (default)

        Returns:
            str: Formatted date string
        """
        return self.released_date.strftime(date_format)

    def set_gh_info(self, info):
        self.info_set = True
        self.stars = info['stars']
        self.forks = info['forks']
        self.watchers = info['watchers']
        self.github_link = info['github_link']


def search(
    query: str, opts: Union[dict, Namespace] = {}
) -> Generator[Package, None, None]:
    """Search for packages matching the query

    Yields:
        Package: package object
    """
    snippets = []
    s = requests.Session()
    for page in range(1, config.page_size + 1):
        params = {"q": query, "page": page}
        r = s.get(config.api_url, params=params)
        soup = BeautifulSoup(r.text, "html.parser")
        snippets += soup.select('a[class*="package-snippet"]')
    authparam = None
    if 'auth' in opts:
        GITHUBAPITOKEN = os.getenv('GITHUBAPITOKEN')
        GITHUB_USERNAME = os.getenv('GITHUB_USERNAME')
        authparam = HTTPBasicAuth(GITHUB_USERNAME, GITHUBAPITOKEN)

    if "sort" in opts:
        if opts.sort == "name":
            snippets = sorted(
                snippets,
                key=lambda s: s.select_one('span[class*="package-snippet__name"]').text.strip(),
            )
        elif opts.sort == "version":
            from pkg_resources import parse_version

            snippets = sorted(
                snippets,
                key=lambda s: parse_version(
                    s.select_one('span[class*="package-snippet__version"]').text.strip()
                ),
            )
        elif opts.sort == "released":
            snippets = sorted(
                snippets,
                key=lambda s: s.select_one('span[class*="package-snippet__created"]').find(
                    "time"
                )["datetime"],
            )

    for snippet in snippets:
        link = urljoin(config.api_url, snippet.get("href"))
        package = re.sub(
            r"\s+", " ", snippet.select_one('span[class*="package-snippet__name"]').text.strip()
        )
        version = re.sub(
            r"\s+",
            " ",
            snippet.select_one('span[class*="package-snippet__version"]').text.strip(),
        )
        released = re.sub(
            r"\s+",
            " ",

            snippet.select_one('span[class*="package-snippet__created"]').find("time")[
                "datetime"
            ],
        )
        description = re.sub(
            r"\s+",
            " ",
            snippet.select_one('p[class*="package-snippet__description"]').text.strip(),
        )
        info = get_github_info(link, authparam)
        pack = Package(package, version, released, description, link)
        if info['set']:
            pack.set_gh_info(info)
        yield pack #Package(package, version, released, description, link, links)

def get_repo_info(repo, auth=None):
    info = {'stars':'', 'forks':'', 'watchers':'', 'set':False}    
    if 'github' in repo:
        try:
            reponame = repo.split('github.com/')[1].rstrip('/')            
        except IndexError as e:
            logger.error(f'[r] err:{e} repo:{repo}')
            return info
        apiurl = f'https://api.github.com/repos/{reponame}'
        r = requests.get(apiurl, auth=auth)
        if 'Not Found' in r.text:
            logger.warning(f'[r] {r.status_code} r:{reponame} apiurl:{apiurl} not found' )
            return info
        if 'API rate limit exceeded' in r.text:
            logger.warning(f'[r] {r.status_code} {reponame} apiurl:{apiurl} API rate limit exceeded')
            return info
        try:
            info['stars'] = str(r.json()["stargazers_count"])
        except TypeError as e:
            logger.error(f'[gri] {e} r:{r.status_code} len:{len(r.content)} apiurl:{apiurl} rj:{r.json()}')
        info['forks'] = str(r.json()["forks_count"])
        info['watchers'] = str(r.json()["watchers_count"])
        info['github_link'] = repo
        info['set'] = True
        return info
    else:
        logger.warning(f'[gri] wrong url: {repo}')
        return info

def get_github_info(repolink, authparam):
    gh_link = get_links(repolink)
    logger.debug(f'[ggi] repolink:{repolink} gh:{gh_link}')
    github_link = gh_link['github']
    homepage = gh_link['homepage']
    info = get_repo_info(github_link,authparam)
    return info

def get_links(pkg_url):
    s = requests.session()
    r = s.get(pkg_url)
    soup = BeautifulSoup(r.text, "html.parser")
    homepage = ''
    githublink = ''
    docslink = ''
    try:
        homepage = soup.select_one('.vertical-tabs__tabs > div:nth-child(2) > ul:nth-child(2) > li:nth-child(1) > a:nth-child(1)',href=True).attrs['href']
        if 'github' in homepage:
            githublink = homepage
            githublink = githublink.replace('/tags','')
            return {'github':githublink, 'homepage':homepage}
    except AttributeError as e:
        logger.warning(f'[err] err:{e} pkg_url:{pkg_url}')
        #logger.warning(f'[!] No homepage for {pkg_url}')
    try:
        githublink = soup.select_one('.vertical-tabs__tabs > div:nth-child(2) > ul:nth-child(2) > li:nth-child(2) > a:nth-child(1)',href=True).attrs['href']
        githublink = githublink.replace('/tags','')
        return {'github':githublink, 'homepage':homepage}
    except AttributeError as e:
        logger.warning(f'[err] err:{e} pkg_url:{pkg_url}')
    return {'github':githublink, 'homepage':homepage}    
