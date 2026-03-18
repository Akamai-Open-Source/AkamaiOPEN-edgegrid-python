"""Shared pytest fixtures and helpers for Global Traffic Management API tests."""

import json
import os
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.session import Session
from akamai.edgegrid.gtm.gtm import GTMClient

# Directory containing this conftest.py
TEST_DIR = os.path.abspath(os.path.dirname(__file__))
# Directory containing JSON test fixtures
TESTDATA_DIR = os.path.join(TEST_DIR, "testdata")


def load_fixture(path):
    """Load raw test data content from the testdata directory.

    Mirrors Go ``loadFixtureBytes`` helpers found in GTM test files.
    Reads the file as UTF-8 text so callers can pass it directly to
    ``json.loads`` or use it as a raw response body string.

    Args:
        path: Relative path within ``testdata/``,
            e.g. ``"TestGTM_CreateDomain.req.json"``.

    Returns:
        String content of the requested fixture file.
    """
    full_path = os.path.join(TESTDATA_DIR, path)
    with open(full_path, encoding="utf-8") as fobj:
        return fobj.read()


def load_json_fixture(path):
    """Load and parse a JSON fixture from the testdata directory.

    Convenience wrapper around :func:`load_fixture` that additionally
    deserialises the content into a Python object.

    Args:
        path: Relative path within ``testdata/``.

    Returns:
        Parsed JSON as ``dict`` or ``list``.
    """
    return json.loads(load_fixture(path))


def compact_json(encoded):
    """Convert JSON string to a compact representation.

    Mirrors Go's ``compactJSON`` helper.  Removes all optional
    whitespace from JSON for deterministic comparison.

    Args:
        encoded: JSON string or bytes.

    Returns:
        Compact JSON string with no extra whitespace.
    """
    data = json.loads(encoded)
    return json.dumps(data, separators=(",", ":"), sort_keys=False)


def create_mock_response(status_code, body="", headers=None):
    """Create a mock HTTP response object.

    Mirrors Go's ``httptest.NewTLSServer`` handler pattern where the test
    writes a status code and response body.

    Args:
        status_code: HTTP status code (e.g. 200, 400, 500).
        body: Response body string (typically JSON).
        headers: Optional response headers dict.

    Returns:
        MagicMock configured as an HTTP response with ``status_code``,
        ``text``, ``json()``, ``content``, ``headers``, and ``ok``
        attributes.
    """
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = body
    resp.content = body.encode("utf-8") if isinstance(body, str) else body
    resp.headers = headers or {}
    resp.ok = status_code < 400
    resp.url = ""

    if body and body.strip():
        try:
            parsed = json.loads(body)
            resp.json.return_value = parsed
        except (json.JSONDecodeError, ValueError):
            resp.json.side_effect = json.JSONDecodeError("No JSON body", "", 0)
    else:
        resp.json.return_value = {}

    if status_code >= 400:
        resp.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    else:
        resp.raise_for_status.return_value = None

    return resp


@pytest.fixture
def mock_session():
    """Create a mock Session for client construction tests.

    Mirrors Go's ``session.New()`` used in ``mockAPIClient``.
    Returns a ``MagicMock(spec=Session)`` that stands in for the
    ``Session`` class.
    """
    session = MagicMock(spec=Session)
    return session


@pytest.fixture
def mock_client(mock_session):  # pylint: disable=redefined-outer-name
    """Create a ``GTMClient`` with a mocked session.

    Mirrors Go's ``mockAPIClient(t, mockServer)`` helper.
    The Go helper creates a TLS-aware session pointed at the mock
    server.  In Python, we create a ``GTMClient`` with a mocked
    session that can be configured per-test to return specific
    responses.

    Returns:
        ``GTMClient`` instance with a mock session.
    """
    return GTMClient(mock_session)
