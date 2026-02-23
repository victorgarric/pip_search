from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


def check_version(distribution_name: str) -> str | None:
    try:
        return version(distribution_name)
    except PackageNotFoundError:
        return None
