"""Pytest fixtures for mTLS Key Store API client tests."""

import json
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.session import Session
from akamai.edgegrid.mtlskeystore.mtlskeystore import Client
from akamai.edgegrid.test_helpers import mock_response  # pylint: disable=unused-import  # noqa: F401


# ---------------------------------------------------------------------------
# Shared error response body constants — VERBATIM from Go test fixtures
# ---------------------------------------------------------------------------

SERVER_ERROR_RESPONSE = """{
\t"type": "internal-server-error",
\t"title": "Internal Server Error",
\t"detail": "Error making request",
\t"instance": "TestInstances",
\t"status": 500
}"""

NOT_FOUND_RESPONSE = """{
\t"type": "resource-not-found",
\t"title": "Resource Not Found",
\t"instance": "a2aa0865-219e-4345-9b4d-44e035f7c246",
\t"status": 404,
\t"detail": "The requested resource could not be found on the server.",
\t"problemId": "8346a5d6-a339-4a5b-9dcf-33d482989c78",
\t"field": "certificateId"
}"""


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_session():
    """Create a mock session for testing.

    Returns a ``MagicMock(spec=Session)`` that intercepts HTTP calls.
    Test functions configure ``mock_session.exec.return_value`` or
    ``mock_session.exec.side_effect`` to control the mocked API
    behaviour, mirroring Go's ``mockAPIClient`` + ``httptest.NewTLSServer``
    pattern.

    The mock honours the ``Session.exec()`` signature so that
    ``isinstance`` checks and attribute access work as expected.
    """
    session = MagicMock(spec=Session)
    return session


@pytest.fixture
def client(mock_session):  # pylint: disable=redefined-outer-name
    """Create a Client instance backed by the *mock_session* fixture.

    Mirrors Go ``Client(sess)`` where the test session is injected
    directly into the service client.
    """
    return Client(mock_session)


def create_mock_response(status_code, body="", headers=None):
    """Create a mock HTTP response object.

    Builds a ``MagicMock`` that mimics ``requests.Response`` with the
    given *status_code*, *body*, and optional *headers*.

    When *body* is valid JSON, ``response.json()`` returns the parsed
    data; otherwise it raises ``json.JSONDecodeError``.

    Args:
        status_code: HTTP status code (e.g. 200, 400, 404, 500).
        body: Response body string (JSON or plain text).
        headers: Optional dict of response headers.

    Returns:
        ``MagicMock`` configured with ``status_code``, ``text``,
        ``content``, ``headers``, ``ok``, and ``json()`` attributes.
    """
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = body
    resp.content = body.encode("utf-8") if isinstance(body, str) else body
    resp.headers = headers or {}
    resp.ok = status_code < 400
    resp.url = ""

    try:
        parsed = json.loads(body) if body.strip() else {}
        resp.json.return_value = parsed
    except (json.JSONDecodeError, AttributeError):
        resp.json.side_effect = json.JSONDecodeError(
            "No JSON body", "", 0
        )

    if status_code >= 400:
        resp.raise_for_status.side_effect = Exception(
            f"HTTP {status_code}"
        )
    else:
        resp.raise_for_status.return_value = None

    return resp
