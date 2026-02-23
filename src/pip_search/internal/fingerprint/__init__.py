# pip_search.config
"""Configuration package for pip_search."""

import json
from functools import cache
from importlib import resources
from typing import Any

from loguru import logger

from . import checksum
from .provider import SealedFingerprintProvider

_PACKAGE_PATH = "pip_search.internal.fingerprint"
_FINGERPRINT_FILE = "fingerprint.json"


def read(resource_name: str) -> str:
    return resources.files(_PACKAGE_PATH).joinpath(resource_name).read_text()


@cache
def default() -> dict[str, Any]:
    """Load default browser fingerprint from package data"""

    try:
        fingerprint_data: str = read(_FINGERPRINT_FILE)
        fingerprint_crc32: str = read(f"{_FINGERPRINT_FILE}.crc32")

        fingerprint: dict[str, Any] = json.loads(fingerprint_data)

        if not checksum.verify(fingerprint, checksum=fingerprint_crc32):
            logger.warning("Fingerprint data checksum mismatch.")

        return fingerprint

    except Exception as e:
        logger.warning("Failed to load fingerprint data: {}", e)
        # Fallback minimal fingerprint
        return {
            "userAgent": {"value": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
            "webDriver": {"value": False},
        }


__all__ = ["SealedFingerprintProvider", "default"]
