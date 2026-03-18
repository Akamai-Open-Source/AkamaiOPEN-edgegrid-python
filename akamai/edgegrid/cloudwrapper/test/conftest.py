# pylint: disable=missing-function-docstring,redefined-outer-name
"""Cloud Wrapper test fixtures and helpers."""

import json
import os
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.cloudwrapper.cloudwrapper import CloudWrapperClient
from akamai.edgegrid.session import Session

test_dir = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture
def mock_session():
    """Create a mock Session with intercepted HTTP requests.

    Mirrors Go's mockAPIClient() which sets up an httptest.NewTLSServer
    and injects it into the session.

    Returns:
        MagicMock configured with spec=Session so that only methods
        actually defined on Session can be called.
    """
    session = MagicMock(spec=Session)
    session._session = MagicMock()  # pylint: disable=protected-access
    return session


@pytest.fixture
def cloudwrapper_client(mock_session):
    """Create a CloudWrapperClient with a mocked session.

    Mirrors Go's ``client := mockAPIClient(t, mockServer)``.

    Args:
        mock_session: The mock Session fixture.

    Returns:
        A CloudWrapperClient wired to the mock session.
    """
    return CloudWrapperClient(mock_session)


def make_mock_response(status_code, body="", headers=None):
    """Create a mock HTTP response.

    Mirrors the response from httptest.NewTLSServer handlers in Go tests.
    Produces an object that behaves like ``requests.Response`` for the
    attributes used by the Cloud Wrapper client: ``status_code``,
    ``headers``, ``text``, ``content``, and ``json()``.

    Args:
        status_code: HTTP status code (e.g. 200, 201, 400, 500).
        body: Response body string (JSON or plain text).
        headers: Optional response headers dict.

    Returns:
        MagicMock configured as a requests.Response.
    """
    response = MagicMock()
    response.status_code = status_code
    response.headers = headers or {}
    response.text = body
    response.content = body.encode("utf-8") if body else b""

    if body:
        try:
            parsed = json.loads(body)
            response.json.return_value = parsed
        except (json.JSONDecodeError, ValueError):
            response.json.side_effect = json.JSONDecodeError("", "", 0)
    else:
        response.json.side_effect = json.JSONDecodeError("", "", 0)

    return response


def load_fixture(filename):
    """Load a JSON fixture file from the testdata directory.

    Args:
        filename: Name of the fixture file (relative to testdata/).

    Returns:
        Parsed JSON data (dict or list).
    """
    filepath = os.path.join(test_dir, "testdata", filename)
    with open(filepath, "r", encoding="utf-8") as fobj:
        return json.load(fobj)


def assert_request_made(mock_session, method, path, body=None):
    """Assert that a specific HTTP request was made via the mock session.

    Validates the method, path, and optionally the request body
    of the last call to the mock session's ``exec()`` method.
    CloudWrapperClient._exec() calls self._session.exec(method, uri, ...)
    so this helper inspects the call_args on mock_session.exec.

    Args:
        mock_session: The mock Session fixture.
        method: Expected HTTP method (GET, POST, PUT, DELETE).
        path: Expected URL path (may include query params).
        body: Expected request body (compared as JSON if dict/list,
            or string).  When ``None`` the body is not checked.
    """
    call_args = mock_session.exec.call_args
    assert call_args is not None, "No request was made"

    args = call_args.args
    kwargs = call_args.kwargs

    # Method is the first positional arg to Session.exec()
    actual_method = args[0] if args else kwargs.get("method")
    assert actual_method == method, (
        f"Expected method {method}, got {actual_method}"
    )

    # Path is the second positional arg to Session.exec()
    actual_path = (
        args[1] if len(args) > 1 else kwargs.get("path")
    )
    assert actual_path == path, (
        f"Expected path {path}, got {actual_path}"
    )

    # Check body if provided
    if body is not None:
        actual_body = kwargs.get("body")
        if isinstance(actual_body, str):
            actual_body = json.loads(actual_body)
        expected_body = (
            json.loads(body) if isinstance(body, str) else body
        )
        assert actual_body == expected_body, (
            f"Request body mismatch: expected {expected_body}, "
            f"got {actual_body}"
        )
