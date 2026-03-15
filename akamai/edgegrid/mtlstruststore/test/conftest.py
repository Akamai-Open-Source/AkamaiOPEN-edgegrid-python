# pylint: disable=missing-function-docstring,redefined-outer-name
"""Shared pytest fixtures for the mTLS Trust Store API client tests."""

import json
import os
from unittest.mock import MagicMock, Mock

import pytest

test_dir = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture
def mock_session():
    """Create a mocked Session for testing.

    Mirrors Go mockAPIClient(t, mockServer) which creates a real client
    backed by httptest.NewTLSServer. In Python, we mock the Session's
    exec() method to return controlled responses.

    The mock_session.exec(method, path, **kwargs) returns a tuple of
    (mock_response, parsed_json_or_none).

    Usage in tests:
        def test_something(mock_session):
            mock_response = create_mock_response(200, '{"key": "value"}')
            mock_session.exec.return_value = (mock_response, {"key": "value"})
            client = Client(mock_session)
            result = client.some_method(...)
    """
    session = MagicMock()
    return session


def create_mock_response(status_code, body="", headers=None):
    """Create a mock HTTP response object.

    Mirrors the http.Response struct returned by httptest.NewTLSServer
    handlers. Configures status_code, text, headers, and json() behavior.

    Args:
        status_code: HTTP status code (e.g., 200, 201, 400, 404, 500).
        body: Response body string (JSON or plain text).
        headers: Optional dict of response headers
            (e.g., {"Retry-After": "..."}).

    Returns:
        Mock configured as an HTTP response with status_code, text,
        headers, and json() return value or side effect.
    """
    response = Mock()
    response.status_code = status_code
    response.text = body
    response.headers = headers or {}

    try:
        parsed = json.loads(body) if body else None
        response.json.return_value = parsed
    except (json.JSONDecodeError, TypeError):
        response.json.side_effect = json.JSONDecodeError(
            "Expecting value", "", 0
        )

    return response


def load_fixture(filename):
    """Load a JSON fixture file from the testdata directory.

    Args:
        filename: Name of the JSON file in testdata/.

    Returns:
        Parsed JSON data (dict or list).
    """
    filepath = os.path.join(test_dir, "testdata", filename)
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def assert_request(mock_session, expected_method, expected_path,
                   expected_body=None):
    """Assert that the mock session was called with expected parameters.

    Validates the method, path, and optionally the request body of
    the most recent call to mock_session.exec(). Body comparison is
    performed via JSON-normalized equality to ignore key ordering.

    Args:
        mock_session: The mocked Session whose exec() was called.
        expected_method: Expected HTTP method (GET, POST, PUT, DELETE).
        expected_path: Expected URL path.
        expected_body: Expected request body dict (compared via JSON
            equality). If None, body is not checked.
    """
    mock_session.exec.assert_called_once()
    call_args = mock_session.exec.call_args

    actual_method = call_args[0][0]
    actual_path = call_args[0][1]

    assert actual_method == expected_method, (
        f"Expected method {expected_method!r}, got {actual_method!r}"
    )
    assert actual_path == expected_path, (
        f"Expected path {expected_path!r}, got {actual_path!r}"
    )

    if expected_body is not None:
        actual_body = None
        if len(call_args[0]) > 2:
            actual_body = call_args[0][2]
        if actual_body is None and call_args[1]:
            actual_body = call_args[1].get("body")
        assert json.loads(json.dumps(actual_body)) == json.loads(
            json.dumps(expected_body)
        ), (
            f"Expected body {expected_body!r}, got {actual_body!r}"
        )
