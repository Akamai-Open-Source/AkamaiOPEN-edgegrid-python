# pylint: disable=missing-function-docstring,redefined-outer-name
"""PAPI test fixtures and helpers.

Provides shared pytest fixtures for the PAPI client test suite, including
mock session setup, mock HTTP request patching, fixture data loading,
and PAPI client factory helpers.

Mirrors Go pkg/papi/papi_test.go mockAPIClient helper.
"""

import json
import os
from unittest.mock import MagicMock, patch  # pylint: disable=unused-import

import pytest

from akamai.edgegrid.session import Session
from akamai.edgegrid.papi.papi import Client

test_dir = os.path.abspath(os.path.dirname(__file__))


def load_fixture(filename):
    """Load a JSON fixture from the testdata directory.

    Args:
        filename: Name of the JSON file in testdata/

    Returns:
        Parsed JSON data as a Python object (dict, list, etc.)
    """
    filepath = os.path.join(test_dir, 'testdata', filename)
    with open(filepath, encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def mock_session():
    """Create a mock Session instance for testing.

    Returns a MagicMock that simulates the Session class behavior.
    The PAPI Client wraps this session and delegates HTTP calls to it.

    Mirrors Go's pattern of creating a session with a mock server::

        s, err := session.New(session.WithClient(httpClient), ...)
        return Client(s)
    """
    session = MagicMock(spec=Session)
    return session


@pytest.fixture
def papi_client(mock_session):
    """Create a PAPI Client instance with a mocked session.

    Mirrors Go's mockAPIClient(t, mockServer) pattern which creates
    a PAPI client backed by a mock TLS server.

    The client's _exec method is the integration point -- tests should
    either mock the session's exec method or use mock_session_request
    to control HTTP responses.
    """
    return Client(mock_session, use_prefixes=True)


@pytest.fixture
def papi_client_no_prefixes(mock_session):
    """Create a PAPI Client with use_prefixes=False.

    Used for testing the WithUsePrefixes(false) option.
    """
    return Client(mock_session, use_prefixes=False)


@pytest.fixture
def mock_session_request(mock_session):
    """Provide a configurable mock for the session's HTTP request execution.

    Tests set ``mock_session_request.return_value`` to a mock response
    tuple to control what the PAPI client receives from HTTP calls.

    This mirrors Go's httptest.NewTLSServer handler pattern where the
    test controls the response status, body, and headers.

    Usage in tests::

        def test_something(self, papi_client, mock_session_request):
            mock_session_request.return_value = make_mock_response(
                200, '{\"key\": \"value\"}'
            )
            result = papi_client.some_method(request)
            assert result.key == \"value\"
    """
    return mock_session.exec


def make_mock_response(status_code, body_text, headers=None):
    """Create a mock HTTP response for testing.

    This is the central factory for all test HTTP responses. It creates
    a MagicMock that behaves like a requests.Response object.

    Mirrors Go's pattern of writing status + body to httptest response
    writer::

        w.WriteHeader(test.responseStatus)
        w.Write([]byte(test.responseBody))

    Args:
        status_code: HTTP status code (e.g., 200, 500)
        body_text: Raw response body string (copied VERBATIM from Go
            tests)
        headers: Optional response headers dict

    Returns:
        MagicMock configured as a requests.Response
    """
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = headers or {}
    resp.text = body_text
    resp.content = (
        body_text.encode('utf-8')
        if isinstance(body_text, str)
        else body_text
    )

    # Configure json() method -- parse body if valid JSON, otherwise
    # set side_effect to raise JSONDecodeError (mirrors Go behavior
    # where non-JSON bodies cause unmarshal failures).
    if body_text and body_text.strip():
        try:
            parsed = json.loads(body_text)
            resp.json.return_value = parsed
        except (json.JSONDecodeError, ValueError):
            resp.json.side_effect = json.JSONDecodeError(
                "Expecting value", "", 0
            )
    else:
        resp.json.side_effect = json.JSONDecodeError(
            "Expecting value", "", 0
        )

    resp.close = MagicMock()
    return resp


def assert_error_matches(
    error,
    expected_type="",
    expected_title="",
    expected_detail="",
    expected_status_code=0,
):
    """Assert that a PAPI Error matches expected values.

    Mirrors Go's errors.Is(err, want) pattern for Error comparison.
    Only asserts fields whose expected values are truthy, allowing
    partial matching on specific error attributes.

    Args:
        error: The papi Error instance to check
        expected_type: Expected error type URL
        expected_title: Expected error title
        expected_detail: Expected error detail message
        expected_status_code: Expected HTTP status code
    """
    if expected_type:
        assert error.type == expected_type
    if expected_title:
        assert error.title == expected_title
    if expected_detail:
        assert error.detail == expected_detail
    if expected_status_code:
        assert error.status_code == expected_status_code


def assert_request_made(
    mock_exec, method, path, params=None, body=None
):
    """Assert that the session exec was called with expected parameters.

    Mirrors Go's assertions inside httptest handler::

        assert.Equal(t, test.expectedPath, r.URL.String())
        assert.Equal(t, http.MethodGet, r.Method)

    Args:
        mock_exec: The mocked session.exec method
        method: Expected HTTP method ("GET", "POST", etc.)
        path: Expected URL path
        params: Expected query parameters dict
        body: Expected request body (for POST/PUT/PATCH)
    """
    mock_exec.assert_called_once()
    call_args = mock_exec.call_args

    # Validate positional args: method and path
    assert call_args[0][0] == method  # First positional arg
    assert call_args[0][1] == path    # Second positional arg

    # Validate keyword args: params
    if params is not None:
        actual_params = call_args[1].get('params', {})
        assert actual_params == params

    # Validate keyword args: body (JSON-compact comparison)
    if body is not None:
        actual_body = call_args[1].get('body')
        if isinstance(body, str):
            expected = json.loads(json.dumps(json.loads(body)))
            actual = json.loads(json.dumps(actual_body))
            assert expected == actual
        elif isinstance(body, dict):
            assert body == actual_body
