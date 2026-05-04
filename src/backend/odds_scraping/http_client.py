"""HTTP client with retry logic, domain-aware rate limiting, and User-Agent rotation.

Replaces bare ``requests.get()`` calls with a resilient http layer that
handles transient failures transparently and respects per-domain crawl
delays to avoid overloading upstream APIs.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from importlib import import_module
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import httpx
from courlan.urlutils import get_hostinfo
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

try:
    import orjson as _json  # fast JSON; drop-in for stdlib json
except ImportError:  # pragma: no cover
    import json as _json  # type: ignore[no-redef]

if TYPE_CHECKING:
    from curl_cffi.requests import Response as CurlResponse
    from curl_cffi.requests.impersonate import BrowserTypeLiteral
else:
    BrowserTypeLiteral = str

try:
    from curl_cffi import requests as _curl_requests  # TLS impersonation
    from curl_cffi.requests.exceptions import RequestException as _CurlRequestException

    _curl_get: Callable[..., CurlResponse] | None = _curl_requests.get
    _CURL_TRANSIENT_EXCEPTIONS = (_CurlRequestException,)
    _CURL_AVAILABLE = True
except ImportError:  # pragma: no cover
    _curl_get = None
    _CURL_TRANSIENT_EXCEPTIONS: tuple[type[Exception], ...] = ()
    _CURL_AVAILABLE = False

logger = logging.getLogger(__name__)


class _FallbackUserAgent:
    @property
    def random(self) -> str:
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36'


def _build_user_agent_provider():
    try:
        user_agent_module = import_module('fake_useragent')
        user_agent_factory = user_agent_module.UserAgent
    except (ImportError, AttributeError):  # pragma: no cover
        return _FallbackUserAgent()
    return user_agent_factory()


_ua_generator = _build_user_agent_provider()

# Exceptions we consider transient and worth retrying
_TRANSIENT_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ReadError,
    httpx.RemoteProtocolError,
    httpx.TimeoutException,
    httpx.HTTPStatusError,
)


class HttpClient:
    """Thin wrapper around ``httpx`` with tenacity retry + per-domain rate limiting.

    Usage::

        http = HttpClient()
        response = http.get(url, params={'sport': 'basketball'})
        data = response.json()
        http.close()
    """

    def __init__(
        self,
        *,
        min_delay: float = 1.0,
        max_retries: int = 3,
        default_timeout: float = 10.0,
    ):
        self._min_delay = min_delay
        self._max_retries = max_retries
        self._default_timeout = default_timeout

        # Track last-request timestamp per *effective domain* (e.g. espn.com)
        self._domain_timestamps: dict[str, float] = {}

        # Create a single httpx.Client (connection pooling, keep-alive)
        self._client = httpx.Client(
            timeout=httpx.Timeout(self._default_timeout),
            headers=self._build_headers(),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(
        self,
        url: str,
        *,
        params: dict | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """GET *url* with automatic retry, rate limiting, and UA rotation.

        Raises the last ``httpx.HTTPError`` subclass after exhausting retries.
        """
        domain = self._resolve_domain(url)
        self._wait_for_domain(domain)

        # Rotate User-Agent + merge caller overrides
        merged_headers = {**self._build_headers(), **(headers or {})}

        # Build a retry decorator that retries on transient failures
        _retryer = retry(
            retry=retry_if_exception_type(_TRANSIENT_EXCEPTIONS),
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            reraise=True,
            before_sleep=self._log_retry_attempt,
        )

        @_retryer
        def _do_request() -> httpx.Response:
            response = self._client.get(url, params=params, headers=merged_headers)
            response.raise_for_status()
            return response

        self._domain_timestamps[domain] = time.monotonic()
        return _do_request()

    def get_json(
        self,
        url: str,
        *,
        params: dict | None = None,
        headers: dict[str, str] | None = None,
        impersonate: BrowserTypeLiteral | None = None,
    ) -> object:
        """GET *url* and return parsed JSON using orjson (fast) or stdlib json.

        If *impersonate* is set (e.g. ``'chrome110'``) **and** curl_cffi is
        installed, the request is sent via ``curl_cffi`` which presents a
        genuine browser TLS fingerprint, bypassing most bot-detection layers.
        Falls back to the normal httpx path when curl_cffi is unavailable.
        """
        if impersonate and _CURL_AVAILABLE and _curl_get is not None:
            domain = self._resolve_domain(url)
            self._wait_for_domain(domain)
            merged_headers = {**self._build_headers(), **(headers or {})}
            curl_get = _curl_get

            _retryer = retry(
                retry=retry_if_exception_type(_CURL_TRANSIENT_EXCEPTIONS),
                stop=stop_after_attempt(self._max_retries),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                reraise=True,
                before_sleep=self._log_retry_attempt,
            )

            @_retryer
            def _do_curl_request() -> CurlResponse:
                resp = curl_get(
                    url,
                    params=params,
                    headers=merged_headers,
                    impersonate=impersonate,
                    timeout=self._default_timeout,
                )
                resp.raise_for_status()
                return resp

            resp = _do_curl_request()
            self._domain_timestamps[domain] = time.monotonic()
            return _json.loads(resp.content)

        response = self.get(url, params=params, headers=headers)
        return _json.loads(response.content)

    def close(self) -> None:
        """Close the underlying ``httpx.Client`` and free resources."""
        self._client.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_headers() -> dict[str, str]:
        return {
            'User-Agent': _ua_generator.random,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        }

    def _resolve_domain(self, url: str) -> str:
        """Extract a rate-limiting key from *url* (e.g. 'espn.com')."""
        hostinfo = get_hostinfo(url)
        if hostinfo is not None and hostinfo[0] is not None:
            return hostinfo[0]
        return urlparse(url).netloc

    def _wait_for_domain(self, domain: str) -> None:
        """Sleep if *domain* was accessed too recently."""
        if domain not in self._domain_timestamps:
            return
        elapsed = time.monotonic() - self._domain_timestamps[domain]
        wait_time = self._min_delay - elapsed
        if wait_time > 0:
            logger.debug('Rate limiting %s: sleeping %.2fs', domain, wait_time)
            time.sleep(wait_time)

    @staticmethod
    def _log_retry_attempt(retry_state) -> None:
        """Callback invoked by tenacity before each retry sleep."""
        attempt = retry_state.attempt_number
        exc = retry_state.outcome.exception() if retry_state.outcome else None
        logger.warning(
            'HTTP retry %d/%d — %s: %s',
            attempt,
            retry_state.retry_object.stop.max_attempt_number,  # type: ignore[union-attr]
            type(exc).__name__ if exc else 'unknown',
            exc,
        )
