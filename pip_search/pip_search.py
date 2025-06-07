import sys
import re
import os
import time
import json
import random
import string
import hashlib
from loguru import logger
from argparse import Namespace
from dataclasses import InitVar, dataclass
from datetime import datetime
from typing import Generator, Union
from urllib.parse import urljoin
import httpx
import requests
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup

import socket
from urllib3.connection import HTTPConnection

HTTPConnection.default_socket_options = HTTPConnection.default_socket_options + [
    (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
    (socket.SOL_TCP, socket.TCP_KEEPIDLE, 45),
    (socket.SOL_TCP, socket.TCP_KEEPINTVL, 10),
    (socket.SOL_TCP, socket.TCP_KEEPCNT, 6),
]

DEBUG = True
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
    "Mozilla/5.0 (Linux; Android 11; SM-G960U) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Mobile Safari/537.36",
]


class Config:
    """Configuration class"""

    api_url: str = "https://pypi.org/search/"
    page_size: int = 2
    sort_by: str = "name"
    date_format: str = "%d-%-m-%Y"
    link_defualt_format: str = "https://pypi.org/project/{package.name}"


# config = Config()


@dataclass
class Package:
    """Package class"""

    name: str
    version: str
    released: str
    description: str
    link: InitVar[str] = None

    def __post_init__(self, link: str = None):
        self.config = Config()
        self.link = link or self.config.link_defualt_format.format(package=self)
        self.released_date = datetime.strptime(self.released, "%Y-%m-%dT%H:%M:%S%z")
        self.stars: int = 0
        self.forks: int = 0
        self.watchers: int = 0
        self.github_link: str = ""
        self.info_set: bool = False

    def released_date_str(self, date_format: str) -> str:
        """Return the released date as a string formatted
        according to date_formate ou Config.date_format (default)

        Returns:
                str: Formatted date string
        """
        return self.released_date.strftime(date_format)

    def set_gh_info(self, info):
        self.stars = info["stars"]
        self.forks = info["forks"]
        self.watchers = info["watchers"]
        self.github_link = info["github_link"]
        self.info_set = True


# todo add url to results
def search(args, config, opts: Union[dict, Namespace] = {}) -> Generator[Package, None, None]:
    query = args.query
    query = "".join(query)
    qurl = config.api_url + f"?q={query}"

    # time.sleep(5)

    snippets = []
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    }
    params = {"q": query}
    r = session.get(config.api_url, params=params, headers=headers)

    # Get script.js url
    pattern = re.compile(r"/(.*)/script.js")
    path = pattern.findall(r.text)[0]
    script_url = f"https://pypi.org/{path}/script.js"

    r = session.get(script_url)

    # Find the PoW data from script.js
    # TODO: make the pattern more robust
    pattern = re.compile(
        r'init\(\[\{"ty":"pow","data":\{"base":"(.+?)","hash":"(.+?)","hmac":"(.+?)","expires":"(.+?)"\}\}\], "(.+?)"'
    )
    base, hash, hmac, expires, token = pattern.findall(r.text)[0]

    # Compute the PoW answer
    answer = ""
    characters = string.ascii_letters + string.digits
    for c1 in characters:
        for c2 in characters:
            c = base + c1 + c2
            if hashlib.sha256(c.encode()).hexdigest() == hash:
                answer = c1 + c2
                break
        if answer:
            break

    # Send the PoW answer
    back_url = f"https://pypi.org/{path}/fst-post-back"
    data = {
        "token": token,
        "data": [
            {"ty": "pow", "base": base, "answer": answer, "hmac": hmac, "expires": expires}
        ],
    }
    r = session.post(back_url, json=data)

    # soup = BeautifulSoup(browser.page_source, "html.parser")
    for page in range(1, config.page_size + 1):
        params = {"q": query, "page": page}
        r = session.get(config.api_url, params=params)
        soup = BeautifulSoup(r.text, "html.parser")
        snippets += soup.select('a[class*="package-snippet"]')
        logger.debug(f'[s] p:{page} snippets={len(snippets)} query={query} ')

    # snippets = soup.select('a[class*="package-snippet"]')
    # logger.debug(f'qurl: {qurl} soup: {len(soup)} snippets: {len(snippets)}')
    authparam = None
    if opts.extra:
        GITHUBAPITOKEN = os.getenv("GITHUBAPITOKEN")
        GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
        authparam = HTTPBasicAuth(GITHUB_USERNAME, GITHUBAPITOKEN)
    for snippet in snippets:
        info = {}
        link = urljoin(config.api_url, snippet.get("href"))
        package = re.sub(r"\s+", " ", snippet.select_one('span[class*="package-snippet__name"]').text.strip())
        version = 'noversion'  # re.sub(r"\s+"," ",snippet.select_one('span[class*="package-snippet__version"]').text.strip())
        released = re.sub(r"\s+"," ",snippet.select_one('span[class*="package-snippet__created"]').find("time")["datetime"])
        description = re.sub(r"\s+"," ",snippet.select_one('p[class*="package-snippet__description"]').text.strip())
        pack = Package(package, version, released, description, link)
        if opts.extra:
            info = get_github_info(link, authparam)
            if info:
                pack.set_gh_info(info)
        if args.debug:
            logger.debug(f'[s] pack: {pack} link: {link} info: {info}')
        yield pack


def get_repo_info(repo, auth):
    session = requests.session()
    # info = {'stars':'', 'forks':'', 'watchers':'', 'set':False}
    info = {"stars": 0, "forks": 0, "watchers": 0, "set": False, "github_link": ""}
    # session = requests.session()
    try:
        reponame = repo.split("github.com/")[1].rstrip("/")
    except IndexError as e:
        logger.error(f"[r] err:{e} repo:{repo}")
        return info
    apiurl = f"https://api.github.com/repos/{reponame}"
    r = session.get(apiurl, auth=auth)
    # logger.info(f'[r] repo:{repo} apiurl: {apiurl} r={r.status_code}')
    if r.status_code == 401:
        if DEBUG:
            logger.error(f"[r] autherr:401 repo: {repo} apiurl: {apiurl} a:{auth}")
        return info
    if r.status_code == 404:
        if DEBUG:
            logger.warning(
                f"[r] {r.status_code} url: {repo} r: {reponame} apiurl: {apiurl} not found"
            )
        return info
    if r.status_code == 403:
        if DEBUG:
            logger.warning(
                f"[r] {r.status_code} r: {reponame} apiurl: {apiurl} API rate limit exceeded"
            )
        return info
    if r.status_code == 200:
        try:
            info["stars"] = r.json().get(
                "stargazers_count", 0
            )  # str(r.json()["stargazers_count"])
            info["forks"] = r.json().get("forks_count", 0)
            info["watchers"] = r.json().get("watchers_count", 0)
            info["github_link"] = repo
            info["set"] = True
            return info
        except (KeyError, TypeError, AttributeError) as err:
            logger.error(f"[gri] {err} r:{r.status_code} apiurl:{apiurl} rj:{r.json()}")
            logger.error(f"[gri] info:{info}")
            return info


def get_github_info(repolink, authparam):
    gh_link = None
    gh_link = get_links(repolink)
    if gh_link:
        info = get_repo_info(repo=gh_link["github"], auth=authparam)
        return info
    else:
        return None


def get_links(pkg_url):
    s = requests.session()
    r = s.get(pkg_url)
    soup = BeautifulSoup(r.text, "html.parser")
    homepage = ""
    githublink = ""
    csspath = ".vertical-tabs__tabs > div:nth-child(3) > ul:nth-child(4) > li:nth-child(1) > a:nth-child(1)"
    try:
        homepage = soup.select_one(csspath, href=True).attrs["href"]
    except Exception as e:
        logger.error(f'[err] err:{e} homepage not found pkg_url:{pkg_url}')
        return None
    try:
        # .vertical-tabs__tabs > div:nth-child(2) > ul:nth-child(2) > li:nth-child(2) > a:nth-child(1)
        # '.vertical-tabs__tabs > div:nth-child(2) > ul:nth-child(2) > li:nth-child(1) > a:nth-child(1)'
        if "issues" in homepage:
            try:
                issues_homepage = soup.select_one(".vertical-tabs__tabs > div:nth-child(2) > ul:nth-child(2) > li:nth-child(2) > a:nth-child(1)", href=True,).attrs["href"]
            except Exception as e:
                logger.error(f'[err] {e} {type(e)} issues_homepage not found pkg_url:{pkg_url} homepage:{homepage}')
                return None
        if "github" in homepage:
            githublink = homepage
            githublink = githublink.replace("/tags", "")
            return {"github": githublink, "homepage": homepage}
        else:
            return None
    except AttributeError as e:
        # pass
        logger.warning(f"[err] err:{e} homepage not found pkg_url:{pkg_url}")
        return None
    # try:
    #     githublink = soup.select_one('.vertical-tabs__tabs > div:nth-child(2) > ul:nth-child(2) > li:nth-child(2) > a:nth-child(1)',href=True).attrs['href']
    #     githublink = githublink.replace('/tags','')
    #     return {'github':githublink, 'homepage':homepage}
    # except AttributeError as e:
    #     # pass
    #     logger.warning(f'[err] err:{e} gh link not found pkg_url:{pkg_url} h:{homepage}')
    # return {'github':githublink, 'homepage':homepage}
