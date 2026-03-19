# pylint: disable=missing-function-docstring
# pylint: disable=redefined-outer-name
"""Shared pytest fixtures for Account Protection API tests.

Provides mock session, client, and response helpers that mirror
Go's mockAPIClient pattern from account_protection_test.go.
"""

import json
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.accountprotection.accountprotection import (
    AccountProtectionClient,
)


class MockResponse:
    """Mock HTTP response object.

    Simulates requests.Response for testing the client's HTTP handling.
    Mirrors Go's httptest.ResponseRecorder behavior.

    Attributes:
        status_code: HTTP status code of the response.
        headers: Dictionary of response headers.
    """

    def __init__(self, status_code=200, body="", headers=None):
        """Initialize a mock HTTP response.

        Args:
            status_code: HTTP status code. Defaults to 200.
            body: Response body string. Defaults to empty string.
            headers: Optional dictionary of response headers.
        """
        self.status_code = status_code
        self._body = body
        self.headers = headers or {}

    @property
    def text(self):
        """Return the response body as text.

        Returns:
            The raw response body string.
        """
        return self._body

    def json(self):
        """Parse the response body as JSON.

        Returns:
            Parsed JSON data as a Python object (dict, list, etc.).

        Raises:
            json.JSONDecodeError: If the body is not valid JSON.
        """
        return json.loads(self._body)


@pytest.fixture
def mock_session():
    """Create a mock Session for testing.

    Mirrors Go's mockAPIClient pattern where a session is created with
    a mock HTTP client. The session's exec() method can be configured
    per test to return specific responses.

    Returns:
        A MagicMock instance mimicking the Session interface.
    """
    session = MagicMock()
    return session


@pytest.fixture
def mock_client(mock_session):
    """Create an AccountProtectionClient with mock session.

    Mirrors Go's Client(s) factory that creates an accountProtection
    client with a given session, as used in mockAPIClient from
    account_protection_test.go.

    Args:
        mock_session: The mock session fixture.

    Returns:
        An AccountProtectionClient instance backed by the mock session.
    """
    return AccountProtectionClient(mock_session)
