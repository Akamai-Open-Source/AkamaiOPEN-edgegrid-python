# pylint: disable=missing-function-docstring
"""GTM test fixtures and helpers.

Provides pytest fixtures and helper functions for the GTM test suite.
Mirrors the functionality from Go's ``gtm_test.go`` helper functions:

- ``mockAPIClient(t, mockServer)`` → :func:`gtm_client` fixture
- ``loadTestData(name)`` → :func:`load_test_data` fixture

Also follows patterns from the existing Python conftest at
``akamai/edgegrid/test/conftest.py``.
"""

import json
import os
from unittest.mock import MagicMock
from unittest.mock import patch  # pylint: disable=unused-import  # re-exported for tests

import pytest

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
"""Absolute path to the directory containing this conftest.py."""

TESTDATA_DIR = os.path.join(TEST_DIR, "testdata")
"""Absolute path to the ``testdata/`` directory holding JSON fixtures."""

# ---------------------------------------------------------------------------
# GTM schema version and header constants  (mirrors common.go)
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "1.6"
"""Default GTM schema version. Mirrors Go ``schemaVersion`` from common.go."""

GTM_CONTENT_TYPE = (
    f"application/vnd.config-gtm.v{SCHEMA_VERSION}+json;charset=UTF-8"
)
"""Content-Type header value for GTM requests carrying a body."""

GTM_ACCEPT = f"application/vnd.config-gtm.v{SCHEMA_VERSION}+json"
"""Accept header value for all GTM requests."""


# ---------------------------------------------------------------------------
# Helper function (not a fixture — importable by test modules)
# ---------------------------------------------------------------------------


def mock_response(status_code, body="", headers=None):
    """Create a mock ``requests.Response`` object.

    Mirrors the pattern from Go ``httptest.NewTLSServer`` handlers where
    tests write a status code and response body for the mock server to
    return.

    Args:
        status_code: HTTP status code (e.g. 200, 400, 500).
        body: Response body as a string or bytes.
        headers: Optional mapping of response header names to values.

    Returns:
        A :class:`~unittest.mock.MagicMock` configured with
        ``status_code``, ``text``, ``json()``, ``content``, ``headers``,
        and ``ok`` attributes.
    """
    response = MagicMock()
    response.status_code = status_code

    if isinstance(body, bytes):
        body_str = body.decode("utf-8")
    else:
        body_str = body

    response.text = body_str
    response.content = (
        body_str.encode("utf-8") if isinstance(body_str, str) else body
    )
    response.ok = status_code < 400
    response.url = ""

    # Set up json() behaviour: return parsed value on valid JSON,
    # raise JSONDecodeError on invalid or empty bodies.
    if body_str and body_str.strip():
        try:
            parsed = json.loads(body_str)
            response.json.return_value = parsed
        except (json.JSONDecodeError, ValueError):
            response.json.side_effect = json.JSONDecodeError(
                "No JSON body", "", 0
            )
    else:
        response.json.return_value = {}

    response.headers = headers or {}

    if status_code >= 400:
        response.raise_for_status.side_effect = Exception(
            f"HTTP {status_code}"
        )
    else:
        response.raise_for_status.return_value = None

    return response


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def load_test_data():
    """Load test fixture data from the ``testdata/`` directory.

    Mirrors Go ``loadTestData()`` from ``gtm_test.go`` (lines 42-49).

    Returns:
        A callable that accepts a filename (relative to ``testdata/``)
        and returns the raw UTF-8 string content of that file.
    """
    def _load(name: str) -> str:
        filepath = os.path.join(TESTDATA_DIR, name)
        with open(filepath, encoding="utf-8") as fobj:
            return fobj.read()
    return _load


@pytest.fixture
def load_test_data_json(load_test_data):  # pylint: disable=redefined-outer-name
    """Load and parse JSON test fixture data.

    Convenience wrapper around :func:`load_test_data` that additionally
    deserialises the file content into a Python object.

    Returns:
        A callable that accepts a filename (relative to ``testdata/``)
        and returns the parsed JSON as a ``dict`` or ``list``.
    """
    def _load(name: str) -> dict | list:
        return json.loads(load_test_data(name))
    return _load


@pytest.fixture
def gtm_client():
    """Create a :class:`~akamai.edgegrid.gtm.gtm.GTMClient` with a mocked session.

    Mirrors Go ``mockAPIClient(t, mockServer)`` from ``gtm_test.go``
    (lines 19-34).  The Go helper creates a TLS-aware session pointed at
    the mock server.  In Python we create a ``GTMClient`` with a
    ``MagicMock(spec=Session)`` that can be configured per-test to return
    specific responses.

    Returns:
        A ``GTMClient`` instance whose underlying session is a
        ``MagicMock(spec=Session)``.
    """
    # Lazy imports to avoid circular dependencies and module-level
    # import overhead — the GTM package imports session, and importing
    # session at module level here would create a dependency cycle
    # during test collection when the package __init__ has not yet
    # finished initialising.
    from akamai.edgegrid.gtm.gtm import GTMClient  # pylint: disable=import-outside-toplevel
    from akamai.edgegrid.session import Session  # pylint: disable=import-outside-toplevel

    mock_session = MagicMock(spec=Session)
    client = GTMClient(mock_session)
    return client
