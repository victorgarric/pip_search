"""Fastly challenge orchestrator."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from loguru import logger

from .errors import FastlyChallengeError, FastlyChallengeParseError
from .metrics import ClientMetricsChallengeProvider
from .parser import extract_script_url, has_challenge, parse_challenge_script
from .pat import PATChallengeProvider
from .pow import PoWChallengeProvider
from .response_builder import ChallengeResponseBuilder
from .types import (
    ChallengeConfig,
    ChallengeContext,
    ChallengeResponse,
    ChallengeRoundHandler,
)

if TYPE_CHECKING:
    import httpx


class FastlyChallengeSolver:
    """Orchestrate full Fastly challenge workflow."""

    def __init__(
        self,
        client: httpx.Client,
        *,
        response_builder: ChallengeRoundHandler | None = None,
        base_url: str = "https://pypi.org",
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._response_builder = response_builder or ChallengeResponseBuilder(
            pat_provider=PATChallengeProvider(client, base_url=self._base_url),
            pow_provider=PoWChallengeProvider(),
            metrics_provider=ClientMetricsChallengeProvider(),
        )

    def ensure_access(self, trigger_url: str, *, referer: str | None = None) -> bool:
        """Ensure the client can access endpoint by solving Fastly challenge if needed."""
        referer_url = referer or trigger_url

        logger.debug("Fastly: probing access: {}", trigger_url)
        probe_response = self._client.get(trigger_url)
        probe_body = probe_response.text

        if probe_response.status_code != 200:
            raise FastlyChallengeError(f"Challenge probe failed: HTTP {probe_response.status_code}")

        if not has_challenge(probe_body):
            logger.debug("Fastly: no challenge detected")
            return True

        script_url = extract_script_url(probe_body, base_url=self._base_url)
        logger.debug("Fastly: challenge script url: {}", script_url)

        script_response = self._client.get(
            script_url,
            headers={
                "Accept": "*/*",
                "Referer": referer_url,
            },
        )
        if script_response.status_code != 200:
            raise FastlyChallengeError(
                f"Failed to fetch challenge script: HTTP {script_response.status_code}"
            )

        config = parse_challenge_script(script_response.text)
        return self._solve_challenge_chain(config, referer_url=referer_url)

    def _solve_challenge_chain(self, config: ChallengeConfig, *, referer_url: str) -> bool:
        """Solve challenge chain using round-based post-back flow."""
        logger.debug("Fastly: solving challenge chain")

        token = config.token
        challenges = config.challenges

        for round_idx in range(1, 6):
            context = ChallengeContext(token=token, path=config.path, referer_url=referer_url)
            responses = self._response_builder.build(challenges, context=context)

            logger.debug(
                "Fastly: post-back round={} responses={}",
                round_idx,
                [response.get("ty") for response in responses],
            )

            result = self._post_back(context=context, responses=responses)
            status = str(result.get("status", ""))
            logger.debug("Fastly: post-back status={}", status)

            if status == "success":
                return True

            next_challenges = result.get("ch")
            next_token = result.get("tok")
            if isinstance(next_challenges, list) and isinstance(next_token, str) and next_token:
                challenges = [item for item in next_challenges if isinstance(item, dict)]
                token = next_token
                continue

            break

        raise FastlyChallengeError("Challenge did not complete successfully")

    def _post_back(
        self,
        *,
        context: ChallengeContext,
        responses: list[ChallengeResponse],
    ) -> dict[str, Any]:
        """Post challenge responses and parse Fastly post-back payload."""
        url = f"{self._base_url}{context.path}/fst-post-back"
        payload = {"token": context.token, "data": responses}

        response = self._client.post(
            url,
            json=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Origin": self._base_url,
                "Referer": context.referer_url,
            },
        )
        if response.status_code != 200:
            raise FastlyChallengeError(f"Post-back failed: HTTP {response.status_code}")

        try:
            data = response.json()
        except ValueError as exc:
            raise FastlyChallengeParseError(f"Invalid JSON from post-back: {exc}") from exc

        if not isinstance(data, Mapping):
            raise FastlyChallengeParseError("Invalid JSON from post-back: expected object")

        return dict(data)
