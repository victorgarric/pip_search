# pip_search.py
from __future__ import annotations

import re
import asyncio
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from urllib.parse import quote, urljoin

import httpx

if TYPE_CHECKING:
    from collections.abc import Iterator
from bs4 import BeautifulSoup
from loguru import logger

from . import http
from .internal.challenge_solvers import FastlyChallengeSolver


class SortBy(StrEnum):
    NAME = "name"
    RELEASED = "released"


@dataclass(frozen=True, slots=True)
class SearchConfig:
    base_url: str = "https://pypi.org"
    search_url: str = "https://pypi.org/search/"
    pages: int = 2
    default_sort: SortBy = SortBy.NAME
    project_url_template: str = "https://pypi.org/project/{name}/"
    timeout_s: float = 30.0
    max_connections: int = 120
    max_keepalive_connections: int = 60
    keepalive_expiry_s: float = 30.0
    version_fetch_concurrency: int = 60


CONFIG = SearchConfig()


@dataclass(frozen=True, slots=True)
class SearchOptions:
    sort_by: SortBy = CONFIG.default_sort
    pages: int = CONFIG.pages


@dataclass(frozen=True, slots=True)
class Package:
    name: str
    version: str
    released_at: datetime
    description: str
    url: str

    def released_date_str(self, fmt: str = "%Y-%m-%d") -> str:
        return self.released_at.strftime(fmt)


class _Sel:
    SNIPPET = 'a[class*="package-snippet"]'
    NAME = 'span[class*="package-snippet__name"]'
    VERSION = 'span[class*="package-snippet__version"]'
    CREATED = 'span[class*="package-snippet__created"] time'
    DESCRIPTION = 'p[class*="package-snippet__description"]'


_DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _parse_iso_datetime(value: str) -> datetime:
    v = value.strip()
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    dt = datetime.fromisoformat(v)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def _make_client(cfg: SearchConfig) -> httpx.Client:
    """Create HTTPX client with default headers and HTTP/2."""
    return http.Client(
        http2=True,
        headers=_DEFAULT_HEADERS,
        timeout=httpx.Timeout(cfg.timeout_s),
        limits=httpx.Limits(
            max_connections=max(1, cfg.max_connections),
            max_keepalive_connections=max(1, cfg.max_keepalive_connections),
            keepalive_expiry=cfg.keepalive_expiry_s,
        ),
    )


def _coerce_opts(opts: SearchOptions | dict | None) -> SearchOptions:
    if opts is None:
        return SearchOptions()
    if isinstance(opts, SearchOptions):
        return opts
    sort_by = opts.get("sort_by") or opts.get("sort") or CONFIG.default_sort
    pages = opts.get("pages") or opts.get("page_size") or CONFIG.pages
    return SearchOptions(sort_by=SortBy(str(sort_by)), pages=int(pages))


async def _fetch_project_version(
    client: httpx.AsyncClient,
    *,
    base_url: str,
    package_name: str,
) -> tuple[str, str]:
    endpoint = f"{base_url.rstrip('/')}/pypi/{quote(package_name, safe='')}/json"

    try:
        resp = await client.get(endpoint)
    except httpx.HTTPError as exc:
        logger.debug("Failed to fetch version for {}: {}", package_name, exc)
        return package_name, "Unknown"

    if resp.status_code != 200:
        logger.debug("Failed to fetch version for {}: HTTP {}", package_name, resp.status_code)
        return package_name, "Unknown"

    try:
        data = resp.json()
    except ValueError:
        logger.debug("Version response is not JSON for {}", package_name)
        return package_name, "Unknown"

    if not isinstance(data, dict):
        return package_name, "Unknown"

    info = data.get("info")
    if not isinstance(info, dict):
        return package_name, "Unknown"

    version = info.get("version")
    if isinstance(version, str) and version:
        return package_name, version

    return package_name, "Unknown"


async def _resolve_missing_versions_async(
    package_names: tuple[str, ...],
    *,
    config: SearchConfig,
) -> dict[str, str]:
    concurrency = max(1, min(config.version_fetch_concurrency, len(package_names)))
    sem = asyncio.Semaphore(concurrency)

    async with httpx.AsyncClient(
        http2=True,
        headers=_DEFAULT_HEADERS,
        timeout=httpx.Timeout(config.timeout_s),
        limits=httpx.Limits(
            max_connections=max(1, config.max_connections),
            max_keepalive_connections=max(1, config.max_keepalive_connections),
            keepalive_expiry=config.keepalive_expiry_s,
        ),
    ) as client:

        async def _task(name: str) -> tuple[str, str]:
            async with sem:
                return await _fetch_project_version(
                    client, base_url=config.base_url, package_name=name
                )

        resolved = await asyncio.gather(*(_task(name) for name in package_names))

    return dict(resolved)


def _resolve_missing_versions(
    package_names: list[str],
    *,
    config: SearchConfig,
) -> dict[str, str]:
    unique_names = tuple(dict.fromkeys(package_names))
    if not unique_names:
        return {}

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_resolve_missing_versions_async(unique_names, config=config))

    logger.debug("Event loop already running; falling back to sequential version fetch")
    results: dict[str, str] = {}
    with httpx.Client(
        http2=True,
        headers=_DEFAULT_HEADERS,
        timeout=httpx.Timeout(config.timeout_s),
    ) as client:
        for name in unique_names:
            resp = client.get(f"{config.base_url.rstrip('/')}/pypi/{quote(name, safe='')}/json")
            if resp.status_code != 200:
                results[name] = "Unknown"
                continue
            try:
                payload = resp.json()
            except ValueError:
                results[name] = "Unknown"
                continue

            info = payload.get("info") if isinstance(payload, dict) else None
            version = info.get("version") if isinstance(info, dict) else None
            results[name] = version if isinstance(version, str) and version else "Unknown"

    return results


def search(
    query: str,
    opts: SearchOptions | dict | None = None,
    *,
    client: httpx.Client | None = None,
    config: SearchConfig = CONFIG,
) -> Iterator[Package]:
    o = _coerce_opts(opts)
    c = client or _make_client(config)
    challenge_solver = FastlyChallengeSolver(c, base_url=config.base_url)
    challenge_solver.ensure_access(config.search_url, referer=config.search_url)

    logger.debug("Searching PyPI: query={!r} pages={}", query, o.pages)

    packages: list[Package] = []
    missing_version_entries: list[tuple[int, str]] = []
    for page in range(1, o.pages + 1):
        resp = c.get(config.search_url, params={"q": query, "page": page})
        soup = BeautifulSoup(resp.text, "html.parser")
        snippets = soup.select(_Sel.SNIPPET)
        logger.debug("Parsed page {}: snippets={}", page, len(snippets))

        for snip in snippets:
            name_el = snip.select_one(_Sel.NAME)
            if not name_el:
                continue
            name = re.sub(r"\s+", " ", name_el.get_text(strip=True))

            href = snip.get("href") or ""
            url = (
                urljoin(config.search_url, str(href))
                if href
                else config.project_url_template.format(name=name)
            )

            version_el = snip.select_one(_Sel.VERSION)
            version = (
                re.sub(r"\s+", " ", version_el.get_text(strip=True))
                if version_el and version_el.get_text(strip=True)
                else ""
            )

            created_el = snip.select_one(_Sel.CREATED)
            released_raw = created_el.get("datetime") if created_el else None
            if not released_raw:
                continue
            released_at = _parse_iso_datetime(str(released_raw))

            desc_el = snip.select_one(_Sel.DESCRIPTION)
            description = re.sub(r"\s+", " ", desc_el.get_text(strip=True)) if desc_el else ""

            package = Package(
                name=name,
                version=version,
                released_at=released_at,
                description=description,
                url=url,
            )
            packages.append(package)
            if not version:
                missing_version_entries.append((len(packages) - 1, name))

    if missing_version_entries:
        versions = _resolve_missing_versions(
            [name for _, name in missing_version_entries],
            config=config,
        )
        for index, package_name in missing_version_entries:
            packages[index] = replace(
                packages[index], version=versions.get(package_name, "Unknown")
            )

    match o.sort_by:
        case SortBy.NAME:
            packages.sort(key=lambda p: p.name.casefold())
        case SortBy.RELEASED:
            packages.sort(key=lambda p: p.released_at)

    yield from packages
