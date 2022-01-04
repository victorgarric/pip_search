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

    table = Table(
        title=(
            f"[not italic]:snake:[/] [bold][magenta]{s.start_url} "
            "[not italic]:snake:[/]"
        )
    )
    table.add_column("Package", style="cyan", no_wrap=True)
    table.add_column("Version", style="bold yellow")
    table.add_column("Released", style="bold green")
    table.add_column("Description", style="bold blue")
    for snippet in snippets:
        link = urljoin(api_url, snippet.get("href"))
        package = re.sub(
            r"\s+", " ", snippet.select_one('span[class*="name"]').text.strip()
        )
        version = re.sub(
            r"\s+",
            " ",
            snippet.select_one('span[class*="version"]').text.strip(),
        )
        checked_version = check_version(package)
        if checked_version == version:
            version = f"[bold cyan]{version} ==[/]"
        elif checked_version is not False:
            version = f"{version} > [bold purple]{checked_version}[/]"
        released = re.sub(
            r"\s+",
            " ",
            snippet.select_one('span[class*="released"]').text.strip(),
        )
        description = re.sub(
            r"\s+",
            " ",
            snippet.select_one('p[class*="description"]').text.strip(),
        )
        emoji = ":open_file_folder:"
        table.add_row(
            f"[link={link}]{emoji}[/link] {package}",
            version,
            released,
            description,
        )

    console = Console()
    console.print(table)
    return
