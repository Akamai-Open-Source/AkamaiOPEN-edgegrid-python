"""Shared pytest fixtures and helpers for Cloud Certificates API tests.

Provides test infrastructure mirroring Go's ``mockAPIClient`` pattern from
``pkg/cloudcertificates/cloudcertificates_test.go`` (lines 17-32).  Instead
of Go's ``httptest.NewTLSServer`` with TLS certificate pools, Python tests
mock the session's ``exec()`` method directly using ``unittest.mock``.

Exports
-------
test_dir : str
    Absolute path of this test package directory.
mock_session : pytest.fixture
    Function-scoped ``MagicMock`` simulating a :class:`Session`.
client : pytest.fixture
    Function-scoped :class:`Client` backed by *mock_session*.
MockResponse : class
    Lightweight HTTP response simulator with *status_code*, *headers*,
    ``json()``, and ``text``.
load_fixture : function
    Load and parse a JSON fixture from ``testdata/``.
setup_mock_response : function
    Configure *mock_session* to return a canned ``(MockResponse, body)``
    tuple from its ``exec()`` method.
"""

import json
import os
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.cloudcertificates.cloudcertificates import Client

# ---------------------------------------------------------------------------
# Module-level constant — mirrors existing pattern in
# akamai/edgegrid/test/conftest.py
# ---------------------------------------------------------------------------

test_dir = os.path.abspath(os.path.dirname(__file__))


# ---------------------------------------------------------------------------
# MockResponse — lightweight HTTP response object for testing
# ---------------------------------------------------------------------------


class MockResponse:
    """Simulate an HTTP response for unit tests.

    Mirrors the response written by Go's ``httptest.NewTLSServer`` handler
    (status code, headers, and a JSON or plain-text body).  Preferred over
    a ``MagicMock`` because it provides deterministic ``json()`` / ``text``
    behaviour without relying on mock auto-attribute semantics.

    Attributes:
        status_code: HTTP status code (e.g. 200, 400, 500).
        headers: Response header dict.
    """

    def __init__(self, status_code, body="", headers=None):
        """Initialise the mock response.

        Args:
            status_code: HTTP status code.
            body: Response body — a JSON string or a ``dict``.
            headers: Optional response header mapping.
        """
        self.status_code = status_code
        self.headers = headers or {}
        self._body = body

    def json(self):
        """Parse the body as JSON.

        Returns:
            Parsed body as ``dict`` or ``list``.

        Raises:
            json.JSONDecodeError: When *body* is a non-JSON string.
        """
        if isinstance(self._body, dict):
            return self._body
        return json.loads(self._body)

    @property
    def text(self):
        """Return the raw body as a string.

        If the body was provided as a ``dict`` it is serialised to a JSON
        string so that callers always receive ``str``.

        Returns:
            String representation of the response body.
        """
        if isinstance(self._body, dict):
            return json.dumps(self._body)
        return self._body


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def load_fixture(filename):
    """Load and parse a JSON fixture from the ``testdata/`` directory.

    Mirrors Go ``loadFixtureBytes`` / ``loadFixtureString`` helpers found
    across cloudcertificates test files.

    Args:
        filename: Relative path within ``testdata/``,
            e.g. ``"create_certificate_base_response.json"``.

    Returns:
        Parsed JSON data (``dict`` or ``list``).
    """
    filepath = os.path.join(test_dir, "testdata", filename)
    with open(filepath, encoding="utf-8") as fobj:
        return json.load(fobj)


def setup_mock_response(mock_session, status_code, body="", headers=None):  # pylint: disable=redefined-outer-name
    """Configure *mock_session* to return a canned HTTP response.

    Sets ``mock_session.exec.return_value`` to a ``(MockResponse,
    parsed_body)`` tuple so that the :class:`Client` methods under test
    receive consistent response data.

    Mirrors Go's ``httptest.NewTLSServer`` handler that writes a status
    code, headers, and a response body.

    Args:
        mock_session: The ``MagicMock`` standing in for :class:`Session`.
        status_code: HTTP status code to return.
        body: Response body — a JSON string, a ``dict``, or an empty
            string for no-body responses (e.g. 204).
        headers: Optional ``dict`` of response headers.

    Returns:
        The configured :class:`MockResponse` instance (useful for
        additional per-test assertions).
    """
    response = MockResponse(status_code, body, headers)

    # Derive the parsed body that Session.exec would normally produce
    # after deserialising the JSON response.
    if isinstance(body, str) and body:
        try:
            parsed_body = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            parsed_body = body
    elif isinstance(body, dict):
        parsed_body = body
    else:
        parsed_body = None

    mock_session.exec.return_value = (response, parsed_body)
    return response


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_session():
    """Create a mock session for testing Cloud Certificates client.

    Returns a ``MagicMock`` that simulates the :class:`Session` class
    with a mockable ``exec()`` method.  Each test receives a fresh
    instance (function scope) to prevent cross-test contamination.

    Mirrors Go's ``mockAPIClient`` which creates an ``httptest.NewTLSServer``-
    backed session and returns ``Client(s)``.

    Returns:
        ``MagicMock`` simulating :class:`Session`.
    """
    session = MagicMock()
    return session


@pytest.fixture
def client(mock_session):  # pylint: disable=redefined-outer-name
    """Create a Cloud Certificates :class:`Client` with a mock session.

    Mirrors Go's ``mockAPIClient(t, mockServer)`` which returns
    ``Client(s)`` where ``s`` is a session backed by a mock server.

    Args:
        mock_session: The mock session fixture.

    Returns:
        :class:`Client` instance backed by *mock_session*.
    """
    return Client(mock_session)
