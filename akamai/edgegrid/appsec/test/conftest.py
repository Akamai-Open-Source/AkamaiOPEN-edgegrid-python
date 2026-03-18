"""Per-service pytest fixtures and helpers for Application Security API tests.

Mirrors Go appsec_test.go helper functions:
- mockAPIClient() → mock_session() + mock_appsec_client() fixtures
- loadFixtureBytes() → load_fixture_bytes() + load_fixture() helpers
- compactJSON() → compact_json() helper
"""

import json
import os
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.appsec.appsec import Client


# Resolve testdata directory relative to this conftest.py file
TEST_DIR = os.path.abspath(os.path.dirname(__file__))
TESTDATA_DIR = os.path.join(TEST_DIR, "testdata")


def load_fixture_bytes(path: str) -> bytes:
    """Load a test fixture file and return raw bytes.

    Mirrors Go ``loadFixtureBytes()`` from ``appsec_test.go``.

    Args:
        path: Relative path from the testdata directory,
              e.g. ``"TestActivations/Activations.json"``.

    Returns:
        Raw bytes content of the fixture file.
    """
    full_path = os.path.join(TESTDATA_DIR, path)
    with open(full_path, "rb") as fobj:
        return fobj.read()


def load_fixture(path: str) -> dict | list:
    """Load a JSON test fixture file and return parsed data.

    Convenience wrapper around :func:`load_fixture_bytes` that additionally
    deserialises the content into a Python object.

    Args:
        path: Relative path from the testdata/ directory.

    Returns:
        Parsed JSON data (dict or list).
    """
    raw = load_fixture_bytes(path)
    return json.loads(raw)


def compact_json(data) -> str:
    """Convert JSON data to compact form with no extra whitespace.

    Mirrors Go ``compactJSON()`` from ``appsec_test.go``.
    Accepts either raw bytes/string (which are first parsed) or already-parsed
    Python objects (dict, list, etc.).

    Args:
        data: JSON bytes, string, dict, or list to compact.

    Returns:
        Compact JSON string with no extra whitespace.
    """
    if isinstance(data, (bytes, str)):
        parsed = json.loads(data)
    else:
        parsed = data
    return json.dumps(parsed, separators=(",", ":"))


def mock_response(status_code: int = 200, json_body=None,
                  text_body: str = "", headers: dict | None = None):
    """Create a mock HTTP response object.

    Used to simulate API responses when patching ``Session.exec()``.
    Callers pass either *json_body* (a JSON-serialisable object) for
    successful JSON responses, or *text_body* for plain-text / error
    responses.

    Args:
        status_code: HTTP status code.
        json_body: JSON-serializable response body (parsed).
        text_body: Raw text response body (used when *json_body* is ``None``).
        headers: Response headers dict.

    Returns:
        ``MagicMock`` configured to behave like ``requests.Response``.
    """
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = headers or {}
    if json_body is not None:
        resp.json.return_value = json_body
        resp.text = json.dumps(json_body)
    else:
        resp.text = text_body
        resp.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
    resp.content = resp.text.encode("utf-8")
    return resp


@pytest.fixture(scope="module")
def mock_session():
    """Create a mock Session for testing.

    Provides a ``MagicMock`` Session instance whose ``exec()`` method can be
    patched per-test to return specific responses.

    Mirrors the Go ``mockAPIClient`` pattern where each test sets up a mock
    HTTP server.
    """
    session = MagicMock()
    session.exec = MagicMock()
    return session


@pytest.fixture
def mock_appsec_client(mock_session):  # pylint: disable=redefined-outer-name
    """Create an AppSec Client with a mock session.

    Mirrors Go ``mockAPIClient()`` which creates a client connected to a mock
    HTTP server.  The *mock_session.exec()* can be patched in each test to
    simulate different API responses.

    Returns:
        ``Client`` instance with mocked session for testing.
    """
    client = Client.__new__(Client)
    client._session = mock_session  # pylint: disable=protected-access
    return client
