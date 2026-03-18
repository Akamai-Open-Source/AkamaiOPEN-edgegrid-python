"""Shared pytest fixtures for Network Lists API tests."""

import json
import os
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.networklists.networklists import NetworkListsClient


# Directory containing this conftest.py
TEST_DIR = os.path.abspath(os.path.dirname(__file__))
# Directory containing JSON test fixtures
TESTDATA_DIR = os.path.join(TEST_DIR, "testdata")


def load_fixture_bytes(path: str) -> bytes:
    """Load the entire contents of a test fixture file as bytes.

    Mirrors Go's loadFixtureBytes helper from networklists_test.go
    (lines 44-51).

    Args:
        path: Relative path from testdata directory
              (e.g., "TestActivations/Activations.json").

    Returns:
        Raw file contents as bytes.
    """
    full_path = os.path.join(TESTDATA_DIR, path)
    with open(full_path, "rb") as fobj:
        return fobj.read()


def compact_json(encoded: bytes) -> str:
    """Convert JSON-encoded bytes to a compact string representation.

    Mirrors Go's compactJSON helper from networklists_test.go
    (lines 53-61).  Removes all optional whitespace from JSON for
    deterministic comparison.

    Args:
        encoded: JSON-encoded bytes.

    Returns:
        Compact JSON string with no extra whitespace.
    """
    data = json.loads(encoded)
    return json.dumps(data, separators=(",", ":"), sort_keys=False)


def create_mock_response(
    status_code: int,
    body: str,
    headers: dict | None = None,
):
    """Create a mock HTTP response object.

    Mirrors Go's httptest.NewTLSServer handler behavior where the test
    writes a status code and response body.

    Args:
        status_code: HTTP status code.
        body: Response body string.
        headers: Optional response headers dict.

    Returns:
        MagicMock configured as an HTTP response with ``status_code``,
        ``text``, ``json()``, and ``headers`` attributes.
    """
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.text = body
    mock_response.headers = headers or {}

    # For JSON-parseable bodies, set up the .json() return value
    try:
        parsed = json.loads(body)
        mock_response.json.return_value = parsed
    except (json.JSONDecodeError, ValueError):
        mock_response.json.side_effect = json.JSONDecodeError("", "", 0)

    return mock_response


@pytest.fixture
def mock_session():
    """Create a mock Session for client construction tests.

    Mirrors Go's ``session.New()`` used in ``TestClient`` and
    ``mockAPIClient``.  Returns a ``MagicMock`` that stands in for the
    ``Session`` class.
    """
    session = MagicMock()
    return session


@pytest.fixture
def mock_client(mock_session):  # pylint: disable=redefined-outer-name
    """Create a ``NetworkListsClient`` with a mocked session.

    Mirrors Go's ``mockAPIClient(t, mockServer)`` helper from
    ``networklists_test.go`` (lines 21-36).

    The Go helper creates a TLS-aware session pointed at the mock
    server.  In Python, we create a ``NetworkListsClient`` with a
    mocked session that can be configured per-test to return specific
    responses.

    Returns:
        ``NetworkListsClient`` instance with a mock session.
    """
    return NetworkListsClient(mock_session)
