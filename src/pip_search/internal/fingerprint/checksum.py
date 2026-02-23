import json
import zlib
from typing import Any


def crc32(d: bytes) -> str:
    return format(zlib.crc32(d) & 0xFFFFFFFF, "08X")


def canonicalize(d: dict[str, Any]) -> str:
    return json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def verify(d: dict[str, Any], *, checksum: str) -> bool:
    payload: bytes = canonicalize(d).encode()

    return crc32(payload).upper() == checksum.strip().upper()
