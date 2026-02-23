"""Fingerprint provider implementations used by challenge solvers."""

from __future__ import annotations

from typing import Any


class SealedFingerprintProvider:
    """Load fingerprint data from packaged sealed fingerprint payload."""

    def load(self) -> dict[str, Any]:
        """Return default sealed fingerprint payload."""
        from . import default

        return dict(default())
