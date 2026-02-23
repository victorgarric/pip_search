"""Client metrics challenge provider implementation."""

from __future__ import annotations

import json

from pip_search.internal.fingerprint.provider import SealedFingerprintProvider

from .types import ChallengeResponse, ChallengeType, FingerprintProvider


class ClientMetricsChallengeProvider:
    """Build client metrics response payload from sealed fingerprint data."""

    def __init__(self, *, fingerprint_provider: FingerprintProvider | None = None) -> None:
        self._fingerprint_provider = fingerprint_provider or SealedFingerprintProvider()

    def solve(self) -> ChallengeResponse:
        """Return client metrics challenge response payload."""
        fingerprint = dict(self._fingerprint_provider.load())

        return {
            "ty": ChallengeType.CLIENT_METRICS,
            "webdriver": False,
            "bot_detection_result": {"bot_detected": False, "bot_kind": None},
            "browser_metrics": {
                "client_data": json.dumps(fingerprint, separators=(",", ":"), ensure_ascii=False),
                "error_trace": None,
            },
        }
