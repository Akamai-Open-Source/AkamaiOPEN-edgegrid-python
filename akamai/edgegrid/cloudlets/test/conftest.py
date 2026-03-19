# pylint: disable=missing-function-docstring
"""Shared pytest fixtures for Cloudlets API client tests."""

import json
import os
from unittest.mock import MagicMock, PropertyMock  # noqa: F401  # pylint: disable=unused-import

import pytest

test_dir = os.path.abspath(os.path.dirname(__file__))


class MockResponse:
    """Mock HTTP response mirroring ``requests.Response`` behavior.

    Provides the subset of the ``requests.Response`` interface that the
    Cloudlets client layer depends on: ``status_code``, ``text``,
    ``headers``, ``json()`` and the ``ok`` property.
    """

    def __init__(self, status_code, body, headers=None):
        """Initialize a MockResponse.

        Args:
            status_code: HTTP status code (e.g. 200, 404, 500).
            body: Raw response body as a string (JSON or plain text).
            headers: Optional dict of HTTP response headers.
        """
        self.status_code = status_code
        self.text = body
        self.headers = headers or {}
        self._json = None

    def json(self):
        """Parse the response body as JSON.

        Returns:
            Parsed JSON data (dict, list, or primitive).

        Raises:
            json.JSONDecodeError: If the body is not valid JSON.
        """
        if self._json is None:
            self._json = json.loads(self.text)
        return self._json

    @property
    def ok(self):
        """Return ``True`` when the status code indicates success (< 400)."""
        return self.status_code < 400


def mock_response(status_code, body, headers=None):
    """Create a :class:`MockResponse` instance.

    Convenience factory used in test parametrize data and inline test
    setup to build mock HTTP responses without direct class instantiation.

    Args:
        status_code: HTTP status code.
        body: Response body string (JSON or plain text).
        headers: Optional response headers dict.

    Returns:
        A :class:`MockResponse` instance.
    """
    return MockResponse(status_code, body, headers)


@pytest.fixture
def mock_session():
    """Create a mock Session for testing.

    Provides a ``MagicMock`` that mimics the ``Session`` interface used
    by the Cloudlets client:

    - ``session.base_url`` — base API URL
    - ``session.exec(method, path, ...)`` — returns ``(response, parsed)``

    Tests should configure the mock's return values before calling
    client methods::

        mock_session.exec.return_value = (mock_response(200, body), parsed)
    """
    session = MagicMock()
    session.base_url = "https://akaa-baseurl.luna.akamaiapis.net"
    return session


@pytest.fixture
def cloudlets_client(mock_session):  # pylint: disable=redefined-outer-name
    """Create a Cloudlets Client with a mock session.

    Lazily imports :class:`~akamai.edgegrid.cloudlets.cloudlets.Client`
    to avoid circular import issues and constructs a client backed by
    the ``mock_session`` fixture.

    Returns:
        A tuple of ``(client, mock_session)`` so tests can both invoke
        client methods and configure the session mock.
    """
    from akamai.edgegrid.cloudlets.cloudlets import Client  # pylint: disable=import-outside-toplevel
    client = Client(mock_session)
    return client, mock_session


def load_fixture(filename):
    """Load a JSON test fixture from the ``testdata/`` directory.

    Args:
        filename: Name of the JSON file inside ``testdata/``
            (e.g. ``"list_origins.json"``).

    Returns:
        Parsed JSON data (dict or list).

    Raises:
        FileNotFoundError: If the fixture file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    fixture_path = os.path.join(test_dir, "testdata", filename)
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)


def assert_error_is(error, expected):
    """Assert that *error* is equivalent to *expected*.

    Mirrors Go's ``errors.Is()`` semantics for Cloudlets error
    comparison.  Checks that:

    1. *error* is a :class:`~akamai.edgegrid.cloudlets.errors.Error`
       instance.
    2. The two errors are equivalent according to
       :meth:`~akamai.edgegrid.cloudlets.errors.Error.is_equivalent`.

    Args:
        error: The actual error / exception raised during the test.
        expected: The expected
            :class:`~akamai.edgegrid.cloudlets.errors.Error` instance
            to compare against.

    Raises:
        AssertionError: If the comparison fails.
    """
    from akamai.edgegrid.cloudlets.errors import Error as CloudletsError  # pylint: disable=import-outside-toplevel
    assert isinstance(error, CloudletsError), (
        f"Expected CloudletsError, got {type(error).__name__}: {error}"
    )
    assert error.is_equivalent(expected), f"want: {expected}; got: {error}"
