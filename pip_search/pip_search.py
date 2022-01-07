from rich.console import Console
from rich.table import Table
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .utils import check_version
import requests
import re


def search(query: str, opts: dict = {}):
    api_url = "https://pypi.org/search/"
    snippets = []
    s = requests.Session()
    for page in range(1, 3):
        params = {"q": query, "page": page}
        r = s.get(api_url, params=params)
        soup = BeautifulSoup(r.text, "html.parser")
        snippets += soup.select('a[class*="snippet"]')
        if not hasattr(s, "start_url"):
            s.start_url = r.url.rsplit("&page", maxsplit=1).pop(0)

    if "sort" in opts:
        if opts.sort == "name":
            snippets = sorted(
                snippets,
                key=lambda s: s.select_one('span[class*="name"]').text.strip()
            )
        elif opts.sort == "version":
            from distutils.version import StrictVersion
            snippets = sorted(
                snippets,
                key=lambda s: StrictVersion(s.select_one(
                    'span[class*="version"]').text.strip())
            )
        elif opts.sort == "released":
            snippets = sorted(
                snippets,
                key=lambda s: s.select_one(
                    'span[class*="released"]').find("time")["datetime"]
            )

    searchresults = []
    for snippet in snippets:
        res = {}
        res['link'] = urljoin(api_url, snippet.get("href"))
        res['package'] = re.sub(
            r"\s+", " ", snippet.select_one('span[class*="name"]').text.strip()
        )
        res['version'] = re.sub(
            r"\s+",
            " ",
            snippet.select_one('span[class*="version"]').text.strip(),
        )
        checked_version = check_version(res['package'])
        if checked_version == res['version']:
            res['version'] = f"[bold cyan]{res['version']} ==[/]"
        elif checked_version is not False:
            res['version'] = \
                f"{res['version']} > [bold purple]{checked_version}[/]"
        res['released'] = re.sub(
            r"\s+",
            " ",
            snippet.select_one('span[class*="released"]').text.strip(),
        )
        res['description'] = re.sub(
            r"\s+",
            " ",
            snippet.select_one('p[class*="description"]').text.strip(),
        )
        searchresults.append(res)

    return s.start_url, searchresults


def print_results(query: str, opts: dict = {}):
    title, searchresults = search(query, opts)

    if opts.brief:
        for res in searchresults:
            print(f"{res['package']} ({res['version']}): {res['description']}")
        return

    table = Table(
        title=(
            f"[not italic]:snake:[/] [bold][magenta]{title} "
            "[not italic]:snake:[/]"
        )
    )

    emoji = ":open_file_folder:"

    table.add_column("Package", style="cyan", no_wrap=True)
    table.add_column("Version", style="bold yellow")
    table.add_column("Released", style="bold green")
    table.add_column("Description", style="bold blue")

    for res in searchresults:
        table.add_row(
            f"[link={res['link']}]{emoji}[/link] {res['package']}",
            res['version'],
            res['released'],
            res['description']
        )

    console = Console()
    console.print(table)


