"""Pytest fixtures and helpers for Bot Manager API client tests.

Provides shared test infrastructure for all ``test_botman.py`` test scenarios.
Mirrors Go ``pkg/botman/botman_test.go`` ``mockAPIClient`` pattern by
providing mock session fixtures and helper functions for HTTP response
simulation, request assertion, and test fixture loading.
"""

import json
import os
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.botman.botman import BotManClient
from akamai.edgegrid.botman.errors import Error  # pylint: disable=unused-import  # re-exported for tests

test_dir = os.path.abspath(os.path.dirname(__file__))


def create_mock_response(status_code, body="", headers=None):
    """Create a mock HTTP response object.

    Mirrors Go's ``httptest.NewTLSServer`` handler behaviour where the
    test handler writes a status code, optional headers, and a response
    body.

    The returned ``MagicMock`` is configured to behave like a
    ``requests.Response`` instance with ``status_code``, ``text``,
    ``json()``, ``content``, ``headers``, and ``ok`` attributes.

    Args:
        status_code: HTTP status code (e.g. 200, 400, 500).
        body: Response body string (typically JSON).
        headers: Optional dict of response headers.

    Returns:
        MagicMock configured as a ``requests.Response``.
    """
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.text = body
    mock_response.content = body.encode("utf-8") if isinstance(body, str) else body
    mock_response.headers = headers if headers is not None else {
        "Content-Type": "application/json",
    }
    mock_response.ok = status_code < 400
    mock_response.url = ""

    # Configure json() method — parse the body if it is valid JSON,
    # otherwise raise JSONDecodeError like a real Response would.
    if body and body.strip():
        try:
            parsed = json.loads(body)
            mock_response.json.return_value = parsed
        except (json.JSONDecodeError, ValueError):
            mock_response.json.side_effect = json.JSONDecodeError(
                "No JSON body", "", 0,
            )
    else:
        mock_response.json.return_value = {}

    # Configure raise_for_status() to mirror requests behaviour.
    if status_code >= 400:
        mock_response.raise_for_status.side_effect = Exception(
            f"HTTP {status_code}",
        )
    else:
        mock_response.raise_for_status.return_value = None

    return mock_response


@pytest.fixture
def mock_session():
    """Create a mock Session object that replaces HTTP calls.

    Mirrors Go's ``mockAPIClient`` pattern which creates an
    ``httptest.NewTLSServer`` and routes all client calls through it.

    Returns a ``MagicMock`` configured as an
    ``akamai.edgegrid.session.Session`` with a callable ``exec`` method
    that captures request details (method, path, body, headers) and
    returns configurable ``(response, parsed_body)`` tuples.
    """
    session = MagicMock()
    session.exec = MagicMock()
    return session


@pytest.fixture
def botman_client(mock_session):  # pylint: disable=redefined-outer-name
    """Create a ``BotManClient`` wired to a mock session.

    Mirrors Go's ``client := mockAPIClient(t, mockServer)`` pattern.

    Args:
        mock_session: Injected mock session fixture.

    Returns:
        ``BotManClient`` initialised with the mock session.
    """
    return BotManClient(mock_session)


def setup_mock_response(mock_session, status_code, body="", headers=None):  # pylint: disable=redefined-outer-name
    """Configure mock session to return a specific response.

    Sets ``mock_session.exec`` to return
    ``(mock_response, parsed_body)`` matching the
    ``Session.exec()`` return-type convention.

    Args:
        mock_session: The mock Session fixture.
        status_code: HTTP status code for the response.
        body: Response body string (JSON string).
        headers: Optional dict of response headers.

    Returns:
        The ``MagicMock`` configured as the HTTP response, useful for
        additional per-test assertions.
    """
    mock_response = create_mock_response(status_code, body, headers)

    parsed_body = None
    if body and body.strip():
        try:
            parsed_body = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            parsed_body = body

    mock_session.exec.return_value = (mock_response, parsed_body)
    return mock_response


def assert_request_made(mock_session, expected_method, expected_path):  # pylint: disable=redefined-outer-name
    """Assert that a request was made with the expected method and path.

    Mirrors Go test assertions::

        assert.Equal(t, test.expectedPath, r.URL.String())
        assert.Equal(t, http.MethodGet, r.Method)

    Args:
        mock_session: The mock Session fixture.
        expected_method: Expected HTTP method (GET, POST, PUT, DELETE).
        expected_path: Expected URL path.

    Raises:
        AssertionError: When the method or path does not match.
    """
    mock_session.exec.assert_called_once()
    call_args = mock_session.exec.call_args

    # Positional arguments: exec(method, path, ...)
    positional = call_args[0] if call_args[0] else ()
    keyword = call_args[1] if call_args[1] else {}

    actual_method = positional[0] if len(positional) > 0 else keyword.get("method")
    actual_path = positional[1] if len(positional) > 1 else keyword.get("path")

    assert actual_method == expected_method, (
        f"Expected method {expected_method!r}, got {actual_method!r}"
    )
    assert actual_path == expected_path, (
        f"Expected path {expected_path!r}, got {actual_path!r}"
    )


def load_test_fixture(filename):
    """Load a JSON test fixture from the ``testdata`` directory.

    Args:
        filename: Name of the JSON fixture file (e.g. ``"response.json"``).

    Returns:
        Parsed JSON data (dict or list).

    Raises:
        FileNotFoundError: When the fixture file does not exist.
        json.JSONDecodeError: When the file is not valid JSON.
    """
    fixture_path = os.path.join(test_dir, "testdata", filename)
    with open(fixture_path, encoding="utf-8") as f:
        return json.load(f)
