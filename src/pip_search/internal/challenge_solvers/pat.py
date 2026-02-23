"""PAT challenge provider implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger

from .types import ChallengeContext, ChallengeResponse, ChallengeType

if TYPE_CHECKING:
    import httpx


class PATChallengeProvider:
    """Resolve PAT challenge payloads via Fastly PAT endpoint."""

    def __init__(self, client: httpx.Client, *, base_url: str) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")

    def solve(self, *, context: ChallengeContext) -> ChallengeResponse:
        """Return PAT challenge response payload."""
        url = f"{self._base_url}{context.path}/pat"
        response = self._client.post(
            url,
            params={"token": context.token},
            content=b"",
            headers={
                "Accept": "text/plain",
                "Content-Type": "application/json",
                "Referer": context.referer_url,
            },
        )

        auth = ""
        if response.status_code != 200:
            logger.debug("Fastly: PAT request failed: HTTP {}", response.status_code)
            return {"ty": ChallengeType.PAT, "auth": auth}

        try:
            data: Any = response.json()
        except ValueError:
            logger.debug("Fastly: PAT response not JSON")
            return {"ty": ChallengeType.PAT, "auth": auth}

        raw_auth = data.get("auth") if isinstance(data, dict) else None
        if isinstance(raw_auth, str):
            auth = raw_auth

        return {"ty": ChallengeType.PAT, "auth": auth}
