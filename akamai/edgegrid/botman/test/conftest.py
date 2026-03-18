"""Shared pytest fixtures and helpers for Bot Manager API tests."""

import json
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.session import Session
from akamai.edgegrid.botman.botman import BotManClient


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
    """Create a ``BotManClient`` with a mocked session.

    Mirrors Go's ``mockAPIClient(t, mockServer)`` helper.
    The Go helper creates a TLS-aware session pointed at the mock
    server.  In Python, we create a ``BotManClient`` with a mocked
    session that can be configured per-test to return specific
    responses.

    Returns:
        ``BotManClient`` instance with a mock session.
    """
    return BotManClient(mock_session)
