from __future__ import annotations

import json

from pip_search.internal.fingerprint import checksum


def test_crc32_returns_uppercase_hex() -> None:
    result = checksum.crc32(b"test")

    assert len(result) == 8
    assert result == result.upper()
    assert all(char in "0123456789ABCDEF" for char in result)


def test_verify_accepts_upper_and_lower_checksum() -> None:
    payload = {"userAgent": {"value": "test"}}
    canonical = checksum.canonicalize(payload)
    valid = checksum.crc32(canonical.encode())

    assert checksum.verify(payload, checksum=valid)
    assert checksum.verify(payload, checksum=valid.lower())


def test_packaged_fingerprint_verifies() -> None:
    from pip_search.internal.fingerprint import read

    fingerprint_data = read("fingerprint.json")
    fingerprint_crc32 = read("fingerprint.json.crc32").strip()

    fingerprint = json.loads(fingerprint_data)

    assert checksum.verify(fingerprint, checksum=fingerprint_crc32)
