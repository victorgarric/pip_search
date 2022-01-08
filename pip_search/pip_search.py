import re
from datetime import datetime
from typing import Generator
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


class Config:
    """Configuration class"""

    api_url = "https://pypi.org/search/"
    page_size = 2
    sort_by = "name"
    date_format = "%b %-d, %Y"


class Package:
    """Package class"""

    def __init__(
        self,
        name: str,
        version: str,
        released: str,
        description: str,
        link: str = None,
    ):
        self.name = name
        self.version = version
        self.released = released
        self.description = description
        self.link = link or urljoin(Config.api_url, f"{name}/{version}/")

    def __str__(self) -> str:
        """Return a string representation of the package"""
        return f"{self.name} {self.version}"

    @property
    def released_date(self) -> datetime:
        """Return the released date as a datetime object"""
        return datetime.strptime(self.released, "%Y-%m-%dT%H:%M:%S%z")

    def released_date_str(self) -> str:
        """Return the released date as a string
        formatted according to Config.date_format"""
        return self.released_date.strftime(Config.date_format)


config = Config()


def search(query: str, opts: dict = {}) -> Generator[Package, None, None]:
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
        snippets += soup.select('a[class*="snippet"]')

    if "sort" in opts:
        if opts.sort == "name":
            snippets = sorted(
                snippets,
                key=lambda s: s.select_one('span[class*="name"]').text.strip(),
            )
        elif opts.sort == "version":
            from distutils.version import StrictVersion

            snippets = sorted(
                snippets,
                key=lambda s: StrictVersion(
                    s.select_one('span[class*="version"]').text.strip()
                ),
            )
        elif opts.sort == "released":
            snippets = sorted(
                snippets,
                key=lambda s: s.select_one('span[class*="released"]').find(
                    "time"
                )["datetime"],
            )

    for snippet in snippets:
        link = urljoin(config.api_url, snippet.get("href"))
        package = re.sub(
            r"\s+", " ", snippet.select_one('span[class*="name"]').text.strip()
        )
        version = re.sub(
            r"\s+",
            " ",
            snippet.select_one('span[class*="version"]').text.strip(),
        )
        released = re.sub(
            r"\s+",
            " ",
            snippet.select_one('span[class*="released"]').find("time")[
                "datetime"
            ],
        )
        description = re.sub(
            r"\s+",
            " ",
            snippet.select_one('p[class*="description"]').text.strip(),
        )
        yield Package(package, version, released, description, link)
