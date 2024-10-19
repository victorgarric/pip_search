#!/usr/bin/env python3
import argparse
import sys
from urllib.parse import urlencode

from rich.console import Console
from rich.table import Table

try:
    from pip_search.pip_search import config, search
except ModuleNotFoundError:
    from pip_search import config, search
try:
    from . import __version__
except ImportError:
    __version__ = "0.0.0"
try:
    from .utils import check_version, check_local_libs
except ImportError:
    from utils import check_version, check_local_libs


def text_output(result, query, args):
    # res = [k for k in result]
    for package in result:
        if package.info_set:
            print(f'{package.name} l:{package.link} ver:{package.version} rel:{package.released_date_str(args.date_format)} gh:{package.github_link} s:{package.stars} f:{package.forks} w:{package.watchers}')
        else:
            print(f'{package.name} l:{package.link} ver:{package.version} rel:{package.released_date_str(args.date_format)}')
        print(f'\tdescription: {package.description}')

def table_output(result, query, args):
    table = Table(title=(f"[not italic]:snake:[/] [bold][magenta] {config.api_url}?{urlencode({'q': query})} [/] [not italic]:snake:[/]"))
    table.add_column("Package", style="cyan", no_wrap=True)
    table.add_column("Version", style="bold yellow")
    table.add_column("Released", style="bold green")
    table.add_column("Description", style="bold blue")
    if args.links:
        table.add_column("Link", style="bold blue")
    if args.extra:
        table.add_column("GH info", style="bold blue")
    # emoji = ":open_file_folder:"
    for package in result:
        checked_version = check_version(package.name)
        if checked_version == package.version:
            package.version = f"[bold cyan]{package.version} ==[/]"
        elif checked_version is not False:
            package.version = (f"{package.version} > [bold purple]{checked_version}[/]")
        # table.add_row(f"[link={package.link}]{emoji}[/link] {package.name}",package.version,package.released_date_str(args.date_format),package.description,f's:{package.stars} f:{package.forks} w:{package.watchers}')
        # tbl_row = f''
        if args.links and args.extra:
            table.add_row(f"{package.name}",package.version,package.released_date_str(args.date_format),package.description, package.link, f's:{package.stars} f:{package.forks} w:{package.watchers}')
        elif args.links:
            table.add_row(f"{package.name}",package.version,package.released_date_str(args.date_format),package.description, package.link)
        elif args.extra:
            table.add_row(f"{package.name}",package.version,package.released_date_str(args.date_format),package.description, f's:{package.stars} f:{package.forks} w:{package.watchers}')
        else:
            table.add_row(f"{package.name}",package.version,package.released_date_str(args.date_format),package.description)
    console = Console()
    console.print(table)

def main():
    ap = argparse.ArgumentParser(prog="pip_search", description="Search for packages on PyPI")
    ap.add_argument("-s","--sort",type=str, const="name",nargs="?",choices=['name', 'version', 'released', 'stars','watchers','forks'],help="sort results by package name, version or release date (default: %(const)s)")
    ap.add_argument("query", nargs="*", type=str, help="terms to search pypi.org package repository")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    ap.add_argument("--date_format", type=str, default="%d-%m-%Y", nargs="?", help="format for release date, (default: %(default)s)")
    ap.add_argument("-e", "--extra", action="store_true", default=False, help="get extra github info")
    ap.add_argument("-l", "--links", action="store_true", default=False, help="show links")
    ap.add_argument("--chklocallibs", action="store_true", default=False, help="check local libs ~/lib/pythonxxx/site-packages ")
    args = ap.parse_args()
    if args.chklocallibs:
        libpath = '/home/kth/.local/lib/python3.12/site-packages/'
        outdated_libs,error_list = check_local_libs(libpath)
        print(f'outdated libs: {len(outdated_libs)} errors: {len(error_list)} \n')
        print(f'\noutdated libs: {outdated_libs}\n')
        print(f'\nerrors: {error_list}\n')
        sys.exit(0)
    if not args.query:
        ap.print_help()
        sys.exit(1)
    query = " ".join(args.query)
    # result = search(query, opts=args)
    res = [k for k in search(query, opts=args)]
    if 'sort' in args:
        if args.sort == 'released':
            res = [k for k in sorted(res, key=lambda s: s.released)]
        if args.sort == 'name':
            res = [k for k in sorted(res, key=lambda s: s.name)]
        if args.sort == 'version':
            res = [k for k in sorted(res, key=lambda s: s.version)]
        if args.sort == 'stars':
            res = [k for k in sorted(res, key=lambda s: s.stars)]
        if args.sort == 'watchers':
            res = [k for k in sorted(res, key=lambda s: s.watchers)]
        if args.sort == 'forks':
            res = [k for k in sorted(res, key=lambda s: s.forks)]
    # text_output(res, query, args)
    table_output(res, query, args)

if __name__ == "__main__":
    sys.exit(main())
