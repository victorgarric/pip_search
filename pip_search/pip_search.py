import re
from argparse import Namespace
from dataclasses import InitVar, dataclass
from datetime import datetime
from typing import Generator, Union
from urllib.parse import urljoin
import string
import hashlib

import requests
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
    link: InitVar[str] = None

    def __post_init__(self, link: str = None):
        self.link = link or config.link_defualt_format.format(package=self)
        self.released_date = datetime.strptime(
            self.released, "%Y-%m-%dT%H:%M:%S%z"
        )

    def released_date_str(self, date_format: str = config.date_format) -> str:
        """Return the released date as a string formatted
        according to date_formate ou Config.date_format (default)

        Returns:
            str: Formatted date string
        """
        return self.released_date.strftime(date_format)


def search(
    query: str, opts: Union[dict, Namespace] = {}
) -> Generator[Package, None, None]:
    """Search for packages matching the query

    Yields:
        Package: package object
    """
    snippets = []
    s = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    }
    params = {"q": query}
    r = s.get(config.api_url, params=params, headers=headers)

    # Get script.js url
    pattern = re.compile(r"/(.*)/script.js")
    path = pattern.findall(r.text)[0]
    script_url = f"https://pypi.org/{path}/script.js"

    r = s.get(script_url)

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
    r = s.post(back_url, json=data)

    for page in range(1, config.page_size + 1):
        params = {"q": query, "page": page}
        r = s.get(config.api_url, params=params)
        soup = BeautifulSoup(r.text, "html.parser")
        snippets += soup.select('a[class*="package-snippet"]')

    if "sort" in opts:
        if opts.sort == "name":
            snippets = sorted(
                snippets,
                key=lambda s: s.select_one('span[class*="package-snippet__name"]').text.strip(),
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

        # Get version info from https://pypi.org/project/PACKAGE_NAME 
        response = s.get(link)
        package_page = BeautifulSoup(response.text, "html.parser")
        version_element = package_page.select_one('h1.package-header__name')
        version = version_element.text.split()[-1] if version_element else "Unknown"

        # version = re.sub(
        #     r"\s+",
        #     " ",
        #     snippet.select_one('span[class*="package-snippet__version"]').text.strip(),
        # )
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
        yield Package(package, version, released, description, link)
