"""Shared test utilities for Akamai EdgeGrid service client test suites.

Provides reusable helpers for mocking HTTP responses, loading JSON test
fixtures, parsing datetime strings, simulating rate-limit behavior, and
asserting HTTP request properties.  Mirrors Go ``internal/test/test.go``
and ``internal/request/request.go`` patterns adapted for Python pytest.
"""

import json
import os
import random
import threading
import time
from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock

__all__ = [
    "new_time_from_string",
    "new_gmt_time_from_string",
    "mock_response",
    "load_json_fixture",
    "fixture_path",
    "RateLimitHandler",
    "assert_request",
]


# ---------------------------------------------------------------------------
# Time parsing helpers
# ---------------------------------------------------------------------------

def new_time_from_string(s: str) -> datetime:
    """Parse an RFC 3339 / ISO 8601 datetime string.

    Mirrors Go ``internal/test.NewTimeFromString`` which uses
    ``time.Parse(time.RFC3339Nano, s)``.  Note that Go strips trailing
    zeros in the fractional-seconds part, which might cause issues with
    IAM endpoints that do not accept the time format without the
    milliseconds part.

    Example::

        >>> new_time_from_string("2025-10-11T23:06:59.000Z")
        datetime.datetime(2025, 10, 11, 23, 6, 59, tzinfo=...)

    Args:
        s: An RFC 3339 datetime string such as
           ``"2025-10-11T23:06:59.000Z"``.

    Returns:
        A timezone-aware ``datetime`` object.
    """
    # Python 3.10's fromisoformat does not accept the 'Z' suffix;
    # replace with the equivalent '+00:00' before parsing.
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def new_gmt_time_from_string(s: str) -> datetime:
    """Parse an RFC 1123 datetime string.

    Mirrors Go ``internal/test.NewGMTTimeFromString`` which uses
    ``time.Parse(time.RFC1123, s)``.  This format is used by the
    ``Retry-After`` header for GMT times.

    Example::

        >>> new_gmt_time_from_string("Mon, 02 Jan 2006 15:04:05 GMT")
        datetime.datetime(2006, 1, 2, 15, 4, 5, tzinfo=...)

    Args:
        s: An RFC 1123 datetime string such as
           ``"Mon, 02 Jan 2006 15:04:05 GMT"``.

    Returns:
        A timezone-aware ``datetime`` object in UTC.
    """
    parsed = datetime.strptime(s, "%a, %d %b %Y %H:%M:%S %Z")
    # Guarantee the result is timezone-aware even when the platform
    # does not resolve the %Z token to a tzinfo object.
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


# ---------------------------------------------------------------------------
# HTTP mock helpers
# ---------------------------------------------------------------------------

def mock_response(
    status_code: int = 200,
    json_body: Any = None,
    text_body: str = "",
    headers: dict | None = None,
) -> MagicMock:
    """Create a mock object that behaves like ``requests.Response``.

    Used by all service-client tests to simulate Akamai API responses.
    Mirrors the pattern established by Go's ``httptest.NewTLSServer``
    fixtures.

    Args:
        status_code: HTTP status code for the response.
        json_body: JSON-serializable body.  When provided the mock's
            ``.json()`` returns this value and ``.text`` holds its
            JSON string representation.
        text_body: Plain-text body used when *json_body* is ``None``.
        headers: Optional response headers dictionary.

    Returns:
        A ``MagicMock`` configured with ``status_code``, ``headers``,
        ``ok``, ``text``, ``content``, ``json()``, ``url``, and
        ``raise_for_status()`` attributes.
    """
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = dict(headers) if headers else {}
    resp.ok = status_code < 400
    resp.url = ""

    if json_body is not None:
        resp.json.return_value = json_body
        resp.text = json.dumps(json_body)
    else:
        resp.text = text_body
        resp.json.side_effect = json.JSONDecodeError(
            "No JSON body", "", 0
        )

    resp.content = resp.text.encode("utf-8")

    if status_code >= 400:
        resp.raise_for_status.side_effect = Exception(
            f"HTTP {status_code}"
        )
    else:
        resp.raise_for_status.return_value = None

    return resp


# ---------------------------------------------------------------------------
# Fixture loading helpers
# ---------------------------------------------------------------------------

def load_json_fixture(file_path: str) -> Any:
    """Load and return parsed data from a JSON test-fixture file.

    Args:
        file_path: Absolute or relative path to the JSON fixture.

    Returns:
        Parsed JSON data (``dict``, ``list``, or primitive).

    Raises:
        FileNotFoundError: If the fixture file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    with open(file_path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def fixture_path(test_file: str, *parts: str) -> str:
    """Construct an absolute path to a test-fixture file.

    Resolves the ``testdata/`` directory relative to the calling test
    module's location on disk.

    Example::

        # From inside akamai/edgegrid/iam/test/test_iam.py
        path = fixture_path(__file__, "ListAPIClients.json")
        data = load_json_fixture(path)

    Args:
        test_file: The ``__file__`` attribute of the calling test
            module.
        *parts: Path components relative to the ``testdata/``
            directory of the test module.

    Returns:
        Absolute path to the fixture file.
    """
    test_dir = os.path.dirname(os.path.abspath(test_file))
    return os.path.join(test_dir, "testdata", *parts)


# ---------------------------------------------------------------------------
# Rate-limit simulation
# ---------------------------------------------------------------------------

class RateLimitHandler:
    """Simulate rate-limited API responses for testing retry logic.

    Mirrors Go ``internal/test.RateLimitHTTPHandler``.  On the first
    call the handler returns HTTP 429 with a rate-limit header pointing
    to a time 1--4 milliseconds in the future.  It keeps returning 429
    until that point passes, then returns the configured success
    response indefinitely.

    Attributes:
        success_code: HTTP status code returned after the rate-limit
            window expires.
        success_body: Response body string returned on success.
    """

    def __init__(self, success_code: int, success_body: str):
        """Initialise the rate-limit handler.

        Args:
            success_code: HTTP status code for successful responses
                after the rate-limit window.
            success_body: Response body for successful responses.
        """
        self.success_code = success_code
        self.success_body = success_body
        self._lock = threading.Lock()
        self._available_at: float | None = None
        self._returned_codes: list[int] = []
        self._return_times: list[float] = []

    # -- public API --------------------------------------------------------

    def handle(
        self, header: str = "Akamai-RateLimit-Next"
    ) -> MagicMock:
        """Generate the next mock response based on rate-limit state.

        Mirrors Go ``RateLimitHTTPHandler.ServeHTTP``.  The first
        invocation sets a random future availability time and returns
        429.  Subsequent calls before that time also return 429.  Once
        the time has passed the handler returns the configured success
        response.

        Args:
            header: Name of the rate-limit header to include on 429
                responses.  Defaults to ``"Akamai-RateLimit-Next"``.

        Returns:
            A ``MagicMock`` behaving like ``requests.Response``.
        """
        available = self.available_at

        if available is None:
            # First request — set a random busy interval (1–4 ms),
            # mirroring Go's ``1 + rand.Intn(4)`` milliseconds.
            busy_ms = 1 + random.randint(0, 3)
            new_available = time.time() + busy_ms / 1000.0
            with self._lock:
                self._available_at = new_available
            return self._too_many_requests(header)

        if time.time() < available:
            return self._too_many_requests(header)

        return self._success_response()

    @property
    def available_at(self) -> float | None:
        """Epoch timestamp when rate limiting expires.

        Returns ``None`` if no request has been made yet (mirrors Go's
        zero-value ``time.Time`` check).
        """
        with self._lock:
            return self._available_at

    @property
    def returned_codes(self) -> list[int]:
        """Copy of all HTTP status codes returned so far."""
        with self._lock:
            return list(self._returned_codes)

    @property
    def return_times(self) -> list[float]:
        """Copy of all response timestamps (epoch seconds)."""
        with self._lock:
            return list(self._return_times)

    # -- private helpers ---------------------------------------------------

    def _record_code(self, status_code: int) -> None:
        """Record a returned status code and the current time."""
        with self._lock:
            self._returned_codes.append(status_code)
            self._return_times.append(time.time())

    def _format_next_time(self) -> str:
        """Format ``_available_at`` as an RFC 3339 string with 'Z'.

        Mirrors Go's ``time.Time.Format(time.RFC3339Nano)`` which
        strips trailing zeros from the fractional-seconds part.
        """
        with self._lock:
            stamp = self._available_at
        next_dt = datetime.fromtimestamp(stamp, tz=timezone.utc)
        base = next_dt.strftime("%Y-%m-%dT%H:%M:%S")
        if next_dt.microsecond:
            frac = f"{next_dt.microsecond:06d}".rstrip("0")
            base += "." + frac
        return base + "Z"

    def _too_many_requests(self, header: str) -> MagicMock:
        """Build a 429 Too Many Requests mock response."""
        next_str = self._format_next_time()
        body = (
            "Your request did not succeed as this operation "
            "has reached the limit for your account. "
            "Please try after " + next_str
        )
        self._record_code(429)
        return mock_response(
            status_code=429,
            text_body=body,
            headers={header: next_str},
        )

    def _success_response(self) -> MagicMock:
        """Build the configured success mock response."""
        self._record_code(self.success_code)
        return mock_response(
            status_code=self.success_code,
            text_body=self.success_body,
        )


# ---------------------------------------------------------------------------
# Request assertion helper
# ---------------------------------------------------------------------------

def assert_request(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    mock_call,
    method: str,
    path: str,
    headers: dict | None = None,
    params: dict | None = None,
    json_body: Any = None,
) -> None:
    """Assert properties of a mocked HTTP request call.

    Validates the method, URL path, headers, query parameters, and
    JSON body of a captured ``unittest.mock`` call from
    ``requests.Session.request``.

    Args:
        mock_call: A ``call`` object from ``unittest.mock``, typically
            obtained via ``mock.call_args`` or
            ``mock.call_args_list[i]``.
        method: Expected HTTP method (``"GET"``, ``"POST"``, etc.).
        path: Expected URL path substring.
        headers: If provided, each key/value pair must appear in the
            request's *headers* keyword argument.
        params: If provided, each key/value pair must appear in the
            request's *params* keyword argument.
        json_body: If not ``None``, must equal the request's *json*
            keyword argument.

    Raises:
        AssertionError: If any expected value does not match the
            actual request properties.
    """
    call_args, call_kwargs = mock_call

    # -- method ------------------------------------------------------------
    actual_method = (
        call_args[0] if call_args else call_kwargs.get("method")
    )
    assert actual_method == method, (
        f"Expected method {method!r}, got {actual_method!r}"
    )

    # -- path / URL --------------------------------------------------------
    actual_url = (
        call_args[1]
        if len(call_args) > 1
        else call_kwargs.get("url", "")
    )
    assert path in actual_url, (
        f"Expected path {path!r} in URL {actual_url!r}"
    )

    # -- headers -----------------------------------------------------------
    if headers is not None:
        actual_headers = call_kwargs.get("headers", {})
        for key, value in headers.items():
            assert key in actual_headers, (
                f"Expected header {key!r} not found in "
                f"{actual_headers!r}"
            )
            assert actual_headers[key] == value, (
                f"Header {key!r}: expected {value!r}, "
                f"got {actual_headers[key]!r}"
            )

    # -- query parameters --------------------------------------------------
    if params is not None:
        actual_params = call_kwargs.get("params", {})
        for key, value in params.items():
            assert key in actual_params, (
                f"Expected param {key!r} not found in "
                f"{actual_params!r}"
            )
            assert actual_params[key] == value, (
                f"Param {key!r}: expected {value!r}, "
                f"got {actual_params[key]!r}"
            )

    # -- JSON body ---------------------------------------------------------
    if json_body is not None:
        actual_json = call_kwargs.get("json")
        assert actual_json == json_body, (
            f"Expected JSON body {json_body!r}, "
            f"got {actual_json!r}"
        )
