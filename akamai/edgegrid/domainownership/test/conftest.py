# pylint: disable=missing-function-docstring
"""pytest fixtures and helpers for Domain Ownership test suite."""

import json
import os
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Module-level constant — directory containing this conftest.py.
# Mirrors the existing pattern from ``akamai/edgegrid/test/conftest.py``.
# ---------------------------------------------------------------------------
test_dir = os.path.abspath(os.path.dirname(__file__))


# ---------------------------------------------------------------------------
# Helper utilities (non-fixture, importable by test modules directly)
# ---------------------------------------------------------------------------


def make_mock_response(status_code, body="", headers=None):
    """Create a mock HTTP response.

    Mirrors Go httptest server responses.  Builds a ``MagicMock`` that
    behaves like a ``requests.Response`` with ``status_code``, ``text``,
    ``json()``, ``content``, and ``headers`` attributes.

    Args:
        status_code: HTTP status code (e.g. 200, 400, 500).
        body: Response body string (JSON or plain text).
        headers: Optional response headers dict.

    Returns:
        MagicMock configured as a ``requests.Response``.
    """
    response = MagicMock()
    response.status_code = status_code
    response.headers = headers or {}
    response.text = body

    # Configure json() to return parsed body or raise on non-JSON
    try:
        response.json.return_value = json.loads(body) if body.strip() else {}
    except (json.JSONDecodeError, ValueError):
        response.json.side_effect = json.JSONDecodeError("", "", 0)

    response.content = body.encode("utf-8") if body else b""
    return response


def load_fixture(filename):
    """Load a JSON test fixture from the testdata directory.

    Args:
        filename: Name of the JSON file in ``testdata/``.

    Returns:
        Parsed JSON data (``dict`` or ``list``).
    """
    filepath = os.path.join(test_dir, "testdata", filename)
    with open(filepath, encoding="utf-8") as fobj:
        return json.load(fobj)


# ---------------------------------------------------------------------------
# Fixtures — automatically discovered and injected by pytest
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_session():
    """Create a mock Session for testing.

    Mirrors Go's ``mockAPIClient`` pattern which creates a mock HTTP
    server and session.  In Python we mock the Session's ``request``
    method directly so that each test can configure the return value.
    """
    session = MagicMock()
    session.request = MagicMock()
    return session


@pytest.fixture
def client(mock_session):  # pylint: disable=redefined-outer-name
    """Create a Domain Ownership client with a mock session.

    Mirrors Go's ``mockAPIClient(t, mockServer)`` which constructs
    a ``Client(session)`` backed by the mock HTTP infrastructure.
    Uses a lazy import to avoid circular import issues.
    """
    from akamai.edgegrid.domainownership.domainownership import Client  # pylint: disable=import-outside-toplevel
    return Client(mock_session)


@pytest.fixture
def error_parser():
    """Provide error response parsing capability for tests.

    Returns a callable that, given a status code and response body
    string, creates a mock response and parses it through the same
    error handling logic used by the production client.
    """
    from akamai.edgegrid.domainownership.errors import parse_error_response  # pylint: disable=import-outside-toplevel

    def _parse(status_code, body):
        resp = make_mock_response(status_code, body)
        return parse_error_response(resp)

    return _parse
