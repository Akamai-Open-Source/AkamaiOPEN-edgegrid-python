# pylint: disable=missing-function-docstring,redefined-outer-name
"""Shared pytest fixtures for EdgeWorkers/EdgeKV test package.

Provides mock HTTP infrastructure, client factories, fixture loading
utilities, and reusable assertion helpers that mirror Go's
mockAPIClient + httptest patterns from edgeworkers_test.go.
"""

import json
import os
from unittest.mock import MagicMock, Mock, patch  # pylint: disable=unused-import

import pytest

from akamai.edgegrid.edgeworkers.edgeworkers import Client
from akamai.edgegrid.edgeworkers.errors import Error as EdgeWorkersError

# Absolute path to this test directory, used for locating fixture files.
test_dir = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture
def mock_session():
    """Create a mock Session for testing EdgeWorkers client.

    Mirrors Go's mockAPIClient pattern from edgeworkers_test.go.
    The mock session intercepts all HTTP calls, allowing tests to:
    - Configure response status codes and bodies via
      ``mock_session.exec.return_value``
    - Assert request paths, methods, headers, query params, bodies

    Returns:
        MagicMock: A mock session object that can be passed to Client().
    """
    session = MagicMock()
    return session


def make_mock_response(status_code, body=None, headers=None, text=None):
    """Create a mock HTTP response object.

    Mirrors Go's httptest.NewTLSServer response handler pattern where
    the test handler writes a status code and body to the response writer::

        w.WriteHeader(test.responseStatus)
        _, _ = w.Write([]byte(test.responseBody))

    Args:
        status_code: HTTP status code (e.g., 200, 201, 500).
        body: Response body as a dict/list (will be JSON serialized).
            Mutually exclusive with *text*.
        headers: Optional dict of response headers.
        text: Raw response text (alternative to *body* for non-JSON
            responses or when verbatim Go test ``responseBody`` strings
            must be passed unchanged).

    Returns:
        Mock: A mock response object with ``status_code``, ``json()``,
            ``text``, ``headers``, and ``content`` attributes.
    """
    response = Mock()
    response.status_code = status_code
    response.headers = dict(headers) if headers else {}

    if body is not None:
        # Dict/list body → automatic JSON serialization
        response.json.return_value = body
        response.text = (
            json.dumps(body) if isinstance(body, (dict, list)) else str(body)
        )
    elif text is not None:
        # Raw text body → attempt JSON parse for .json() method
        response.text = text
        try:
            response.json.return_value = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            response.json.side_effect = json.JSONDecodeError(
                "Expecting value", text, 0
            )
    else:
        # Empty body
        response.text = ""
        response.json.return_value = None

    response.content = (
        response.text.encode("utf-8") if response.text else b""
    )

    return response


@pytest.fixture
def edgeworkers_client(mock_session):
    """Create an EdgeWorkers client with a mock session.

    Mirrors Go's ``client := mockAPIClient(t, mockServer)`` pattern
    from edgeworkers_test.go where a Client is constructed with a mock
    HTTP server-backed session.

    Args:
        mock_session: The mock session fixture.

    Returns:
        Client: An EdgeWorkers client instance connected to the mock
            session.
    """
    return Client(mock_session)


def load_fixture(filename):
    """Load a JSON test fixture from the testdata directory.

    Mirrors Go's testdata file loading pattern where test cases
    reference JSON files for expected request/response payloads.

    Args:
        filename: Name of the JSON fixture file (relative to
            ``testdata/``), e.g. ``"ListActivations.json"``.

    Returns:
        dict or list: Parsed JSON data from the fixture file.
    """
    filepath = os.path.join(test_dir, "testdata", filename)
    with open(filepath, encoding="utf-8") as fobj:
        return json.load(fobj)


def load_fixture_text(filename):
    """Load a test fixture as raw text from the testdata directory.

    For non-JSON fixtures or when the verbatim text content is needed
    (e.g., Go ``responseBody`` strings that must be preserved exactly).

    Args:
        filename: Name of the fixture file (relative to ``testdata/``).

    Returns:
        str: Raw text content of the fixture file.
    """
    filepath = os.path.join(test_dir, "testdata", filename)
    with open(filepath, encoding="utf-8") as fobj:
        return fobj.read()


def assert_error_is(error, expected_error):
    """Assert that an error matches an expected error.

    Mirrors Go's ``errors.Is(err, test.withError)`` pattern from
    edgeworkers test files.

    Handling by type:
    - **EdgeWorkersError**: uses ``is_equivalent()`` for comparison,
      which checks status codes and error codes for sentinel matching.
    - **str** sentinel: checks that the error's string representation
      contains the sentinel text.
    - **Other types**: checks ``isinstance`` match on the error type.

    Args:
        error: The actual error raised during the test.
        expected_error: The expected error to match against.  Can be
            an ``EdgeWorkersError`` instance, a sentinel string, or
            any other exception type.
    """
    if isinstance(expected_error, EdgeWorkersError):
        assert isinstance(error, EdgeWorkersError), (
            f"Error type mismatch: want EdgeWorkersError, "
            f"got {type(error).__name__}"
        )
        assert error.is_equivalent(expected_error), (
            f"Error mismatch: want {expected_error}, got {error}"
        )
    elif isinstance(expected_error, str):
        assert expected_error in str(error), (
            f"Error message mismatch: want '{expected_error}' "
            f"in '{error}'"
        )
    else:
        assert isinstance(error, type(expected_error)), (
            f"Error type mismatch: want {type(expected_error).__name__}, "
            f"got {type(error).__name__}"
        )


def assert_request(mock_session, expected_method, expected_path,
                   expected_body=None, expected_headers=None):
    """Assert that the mock session received the expected HTTP request.

    Mirrors Go's httptest handler assertions::

        assert.Equal(t, test.expectedPath, r.URL.String())
        assert.Equal(t, http.MethodGet, r.Method)

    Validates that ``mock_session.exec`` was called exactly once with
    the expected HTTP method, URL path, and optional body/headers.

    Args:
        mock_session: The mock session to check.
        expected_method: Expected HTTP method (``"GET"``, ``"POST"``,
            ``"PUT"``, ``"DELETE"``).
        expected_path: Expected URL path (including query string).
        expected_body: Expected request body.  When a ``dict``, JSON
            structural comparison is used.  When a ``str``, exact
            string comparison is used.  ``None`` skips body assertion.
        expected_headers: Expected request headers dict.  ``None``
            skips header assertion.
    """
    mock_session.exec.assert_called_once()
    call_args = mock_session.exec.call_args

    # Positional args: (method, path, ...)
    actual_method = (
        call_args[0][0]
        if call_args[0]
        else call_args[1].get("method")
    )
    actual_path = (
        call_args[0][1]
        if len(call_args[0]) > 1
        else call_args[1].get("path")
    )

    assert actual_method == expected_method, (
        f"Method mismatch: want {expected_method}, got {actual_method}"
    )
    assert actual_path == expected_path, (
        f"Path mismatch: want {expected_path}, got {actual_path}"
    )

    # Body assertion (keyword arg)
    if expected_body is not None:
        actual_body = call_args[1].get("body")
        if actual_body is None and len(call_args[0]) > 2:
            actual_body = call_args[0][2]
        if isinstance(expected_body, dict):
            # JSON structural comparison — normalize through
            # dumps/loads to ensure identical representations.
            assert json.loads(json.dumps(actual_body)) == expected_body, (
                f"Body mismatch: want {expected_body}, got {actual_body}"
            )
        else:
            assert actual_body == expected_body, (
                f"Body mismatch: want {expected_body}, got {actual_body}"
            )

    # Headers assertion (keyword arg)
    if expected_headers:
        actual_headers = call_args[1].get("headers", {})
        for key, value in expected_headers.items():
            assert actual_headers.get(key) == value, (
                f"Header {key} mismatch: want {value}, "
                f"got {actual_headers.get(key)}"
            )
