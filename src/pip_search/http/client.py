"""HTTP client utilities."""

from __future__ import annotations

from typing import Any, Final

import httpx
from loguru import logger

from .tracing import Redactor, body_preview

_SENSITIVE_HEADERS: Final[frozenset[str]] = frozenset({"authorization", "cookie"})


class Client(httpx.Client):
    """HTTPX client with request/response logging."""

    def __init__(self, **kwargs: Any) -> None:
        self._redactor = Redactor(_SENSITIVE_HEADERS)
        event_hooks = kwargs.pop("event_hooks", {})
        if not isinstance(event_hooks, dict):
            event_hooks = {}

        request_hooks = list(event_hooks.get("request", []))
        response_hooks = list(event_hooks.get("response", []))
        request_hooks.append(self._log_request)
        response_hooks.append(self._log_response)

        super().__init__(
            event_hooks={
                "request": request_hooks,
                "response": response_hooks,
            },
            **kwargs,
        )

    def build_request(
        self,
        method: str,
        url: httpx.URL | str,
        **kwargs: Any,
    ) -> httpx.Request:
        """Build request with normalized method and headers."""
        headers = kwargs.get("headers")
        if headers is not None:
            kwargs["headers"] = httpx.Headers(headers)

        return super().build_request(method.upper(), url, **kwargs)

    def _log_request(self, request: httpx.Request) -> None:
        logger.trace(
            "HTTP request: method={} url={} headers={} body={}",
            request.method,
            request.url,
            self._redactor.redact(dict(request.headers)),
            self._safe_preview(request),
        )

    def _log_response(self, response: httpx.Response) -> None:
        req = response.request
        body = self._safe_response_body(response)

        logger.trace("HTTP {} {} -> {}", req.method, req.url, response.status_code)
        logger.trace(
            "HTTP response: url={} status={} headers={} body_len={}",
            req.url,
            response.status_code,
            self._redactor.redact(dict(response.headers)),
            len(body),
        )

        if not response.is_redirect:
            logger.opt(lazy=True).trace(
                "HTTP response body preview: {}",
                lambda content=body: body_preview(content),
            )

    @staticmethod
    def _safe_preview(request: httpx.Request) -> str:
        try:
            return body_preview(request.content)
        except Exception:
            return "<streaming body>"

    @staticmethod
    def _safe_response_body(response: httpx.Response) -> bytes:
        try:
            return response.content
        except Exception:
            return b""
