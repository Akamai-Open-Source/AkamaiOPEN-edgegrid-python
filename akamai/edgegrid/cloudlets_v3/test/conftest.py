# pylint: disable=missing-function-docstring
"""Pytest fixtures and test helpers for Cloudlets V3 tests.

Provides mock session infrastructure equivalent to Go's mockAPIClient
helper from cloudlets_test.go, plus JSON fixture loading, error
construction helpers, and request assertion utilities used by
test_cloudlets_v3.py.
"""

import json
import os
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.session import Session
from akamai.edgegrid.cloudlets_v3.cloudlets_v3 import Client
from akamai.edgegrid.cloudlets_v3.errors import Error as CloudletsError


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_session():
    """Create a mock Session for testing.

    Returns a MagicMock constrained to the Session spec so that
    attribute access (e.g., ``mock_session.exec``) is validated
    against the real Session API.

    Mirrors Go's mockAPIClient which creates a session connected to
    httptest.NewTLSServer.  In Python we mock the Session's internal
    HTTP methods instead of standing up a real server.
    """
    session = MagicMock(spec=Session)
    return session


@pytest.fixture
def client(mock_session):  # pylint: disable=redefined-outer-name
    """Create a Cloudlets V3 client with a mocked session.

    Mirrors Go's ``client := mockAPIClient(t, mockServer)`` pattern
    from cloudlets_test.go line 31.
    """
    return Client(mock_session)


@pytest.fixture
def mock_response():
    """Factory fixture for creating mock HTTP response objects.

    Returns a callable that produces MagicMock objects configured to
    behave like ``requests.Response`` instances, with settable
    ``status_code``, ``text``, ``json()``, ``headers``, ``content``,
    and ``close()``.

    Mirrors the response patterns from Go's httptest.NewTLSServer
    handlers.
    """

    def _create_response(status_code=200, body="", headers=None):
        """Create a mock response with the given status code, body, and headers.

        Args:
            status_code: HTTP status code.
            body: Response body string (JSON or plain text).
            headers: Optional response headers dict.

        Returns:
            MagicMock configured to behave like requests.Response.
        """
        response = MagicMock()
        response.status_code = status_code
        response.headers = headers if headers is not None else {}
        response.text = body

        # Configure json() method — parse body if valid JSON, otherwise
        # raise JSONDecodeError on call (mirrors real Response.json()).
        try:
            parsed = json.loads(body) if body and body.strip() else None
            response.json.return_value = parsed
        except (json.JSONDecodeError, ValueError):
            response.json.side_effect = json.JSONDecodeError("", "", 0)

        response.content = (
            body.encode("utf-8") if isinstance(body, str) else body
        )
        response.close = MagicMock()
        return response

    return _create_response


@pytest.fixture(scope="module")
def test_dir():
    """Return the absolute path to this test directory.

    Used by ``load_fixture`` and other file-loading helpers to
    resolve testdata paths relative to this conftest.py location.
    """
    return os.path.abspath(os.path.dirname(__file__))


@pytest.fixture
def load_fixture(test_dir):  # pylint: disable=redefined-outer-name
    """Factory fixture to load JSON test fixture files from testdata/.

    Returns a callable that accepts a filename and returns the parsed
    JSON data from ``<test_dir>/testdata/<filename>``.
    """

    def _load(filename):
        filepath = os.path.join(test_dir, "testdata", filename)
        with open(filepath, "r", encoding="utf-8") as fobj:
            return json.load(fobj)

    return _load


# ---------------------------------------------------------------------------
# Helper functions (non-fixture, importable by test modules)
# ---------------------------------------------------------------------------


def create_error_response(status_code, body_dict):
    """Create a CloudletsError from a dict, simulating API error parsing.

    Builds a ``CloudletsError`` with fields populated from
    *body_dict* and *status_code*, matching the field mapping used by
    ``CloudletsV3Client._parse_error``.  This allows test code to
    construct expected ``Error`` objects for assertion comparison
    without going through HTTP response round-tripping.

    Args:
        status_code: HTTP status code for the error response.
        body_dict: Dictionary with error fields using their JSON
            key names (camelCase) — e.g. ``requestId``, ``clientIp``.

    Returns:
        A CloudletsError populated from the dict with the given
        HTTP status code.
    """
    error = CloudletsError()
    error.type = body_dict.get("type", "")
    error.title = body_dict.get("title", "")
    error.detail = body_dict.get("detail", "")
    error.instance = body_dict.get("instance", "")
    error.status = body_dict.get("status", 0)
    error.errors = body_dict.get("errors")
    error.request_id = body_dict.get("requestId", "")
    error.request_time = body_dict.get("requestTime", "")
    error.client_ip = body_dict.get("clientIp", "")
    error.server_ip = body_dict.get("serverIp", "")
    error.method = body_dict.get("method", "")
    # Override status with actual HTTP status code — mirrors Go behaviour
    # where ``resp.StatusCode`` always takes precedence.
    error.status = status_code
    return error


def assert_request_path(mock_session, expected_path, expected_method="GET"):  # pylint: disable=redefined-outer-name
    """Assert the last request to *mock_session* used the expected path and method.

    Inspects the most recent ``mock_session.exec(...)`` call and
    verifies both the HTTP method and the request path.

    Mirrors Go's assertions::

        assert.Equal(t, test.expectedPath, r.URL.String())
        assert.Equal(t, http.MethodGet, r.Method)

    Args:
        mock_session: The MagicMock(spec=Session) whose ``exec``
            method was called.
        expected_path: The expected URL path string.
        expected_method: The expected HTTP method (default ``"GET"``).
    """
    call_args = mock_session.exec.call_args
    assert call_args is not None, "No request was made to the session"

    args = call_args[0]
    kwargs = call_args[1] if call_args[1] else {}

    method = args[0] if args else kwargs.get("method")
    path = args[1] if len(args) > 1 else kwargs.get("path")

    assert method == expected_method, (
        f"Expected method {expected_method}, got {method}"
    )
    assert path == expected_path, (
        f"Expected path {expected_path}, got {path}"
    )


def assert_request_body_json(mock_session, expected_body):  # pylint: disable=redefined-outer-name
    """Assert the request body JSON matches *expected_body*, ignoring key ordering.

    Inspects the most recent ``mock_session.exec(...)`` call and
    performs a deep-equality comparison between the actual request
    body and the expected body.  Both sides are normalised to Python
    dicts/lists so that JSON key ordering differences are ignored.

    Mirrors Go's ``assert.JSONEq(t, test.expectedRequestBody, string(body))``.

    Args:
        mock_session: The MagicMock(spec=Session) whose ``exec``
            method was called.
        expected_body: Either a JSON string or a Python dict/list
            representing the expected request body.
    """
    call_args = mock_session.exec.call_args
    assert call_args is not None, "No request was made to the session"

    args = call_args[0]
    kwargs = call_args[1] if call_args[1] else {}

    body = kwargs.get("body")
    if body is None and len(args) > 2:
        body = args[2]

    if isinstance(body, str):
        actual = json.loads(body)
    elif isinstance(body, (dict, list)):
        actual = body
    else:
        actual = body

    if isinstance(expected_body, str):
        expected = json.loads(expected_body)
    else:
        expected = expected_body

    assert actual == expected, (
        f"Request body mismatch:\nExpected: {expected}\nActual: {actual}"
    )
