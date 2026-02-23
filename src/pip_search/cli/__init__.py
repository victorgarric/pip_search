from __future__ import annotations

import sys
import argparse
import http.client
from typing import TYPE_CHECKING
from urllib.parse import urlencode

from loguru import logger

if TYPE_CHECKING:
    from collections.abc import Sequence
from rich.console import Console
from rich.table import Table

from .. import __version__
from ..pip_search import CONFIG, SearchOptions, SortBy, search
from ..utils import check_version

_LOGURU_LEVELS: tuple[str, ...] = (
    "TRACE",
    "DEBUG",
    "INFO",
    "SUCCESS",
    "WARNING",
    "ERROR",
    "CRITICAL",
)


def _setup_logger(*, log_level: str) -> None:
    logger.remove()
    normalized_level = log_level.upper()
    logger.add(sys.stderr, level=normalized_level)
    http.client.HTTPConnection.debuglevel = 1 if normalized_level == "TRACE" else 0


def cli(argv: Sequence[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="pip_search", description="Search for packages on PyPI")
    ap.add_argument("query", nargs="+", help="Search terms")
    ap.add_argument(
        "-s",
        "--sort",
        default=CONFIG.default_sort.value,
        choices=[s.value for s in SortBy],
        help="Sort results",
    )
    ap.add_argument(
        "--pages", type=int, default=CONFIG.pages, help="Number of result pages to fetch"
    )
    ap.add_argument("--date-format", default="%Y-%m-%d", help="strftime format for release date")
    ap.add_argument(
        "--log-level",
        type=str.upper,
        default="WARNING",
        choices=_LOGURU_LEVELS,
        help="Loguru logging level",
    )
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    args = ap.parse_args(list(argv) if argv is not None else None)
    _setup_logger(log_level=str(args.log_level))

    query = " ".join(args.query).strip()
    opts = SearchOptions(
        sort_by=SortBy(args.sort),
        pages=max(1, int(args.pages)),
    )

    url = f"{CONFIG.search_url}?{urlencode({'q': query})}"
    logger.info("PyPI search: url={}", url)

    table = Table(title=url)
    table.add_column("Package", style="cyan", no_wrap=True)
    table.add_column("Version", style="bold yellow", no_wrap=True)
    table.add_column("Released", style="bold green", no_wrap=True)
    table.add_column("Description", style="bold blue")

    for pkg in search(query, opts=opts):
        installed = check_version(pkg.name)
        if installed is None:
            version_text = pkg.version
        elif installed == pkg.version:
            version_text = f"[bold cyan]{pkg.version}[/] [dim](installed)[/]"
        else:
            version_text = f"{pkg.version} [dim](installed: {installed})[/]"

        table.add_row(
            f"[link={pkg.url}]{pkg.name}[/link]",
            version_text,
            pkg.released_date_str(args.date_format),
            pkg.description,
        )

    Console().print(table)


def pip_search() -> None:
    raise SystemExit(cli())
