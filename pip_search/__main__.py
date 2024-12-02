import argparse
import sys
from urllib.parse import urlencode

from rich.console import Console
from rich.table import Table

from pip_search.pip_search import config, search

from . import __version__
from .utils import check_version


def main():
    ap = argparse.ArgumentParser(
        prog="pip_search", description="Search for packages on PyPI"
    )
    ap.add_argument(
        "-s",
        "--sort",
        type=str,
        const="name",
        nargs="?",
        choices=["name", "released"],
        help="sort results by package name or \
                        release date (default: %(const)s)",
    )
    ap.add_argument(
        "query",
        nargs="*",
        type=str,
        help="terms to search pypi.org package repository",
    )
    ap.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    ap.add_argument(
        "--date_format",
        type=str,
        default="%d-%m-%Y",
        nargs="?",
        help="format for release date, (default: %(default)s)",
    )
    args = ap.parse_args()
    query = " ".join(args.query)
    result = search(query, opts=args)
    if not args.query:
        ap.print_help()
        sys.exit(1)

    table = Table(
        title=(
            "[not italic]:snake:[/] [bold][magenta]"
            f"{config.api_url}?{urlencode({'q': query})}"
            "[/] [not italic]:snake:[/]"
        )
    )
    table.add_column("Package", style="cyan", no_wrap=True)
    table.add_column("Version", style="bold yellow")
    table.add_column("Released", style="bold green")
    table.add_column("Description", style="bold blue")
    emoji = ":open_file_folder:"
    for package in result:
        checked_version = check_version(package.name)
        if checked_version == package.version:
            package.version = f"[bold cyan]{package.version} ==[/]"
        elif checked_version is not False:
            package.version = (
                f"{package.version} > [bold purple]{checked_version}[/]"
            )
        table.add_row(
            f"[link={package.link}]{emoji}[/link] {package.name}",
            package.version,
            package.released_date_str(args.date_format),
            package.description,
        )
    console = Console()
    console.print(table)


if __name__ == "__main__":
    sys.exit(main())
