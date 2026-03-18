# pylint: disable=missing-function-docstring
"""CPS test fixtures and helpers.

Provides mock session, HTTP response helpers, and CPS client factory
for CPS unit tests.  Mirrors Go's ``mockAPIClient`` pattern from
``cps_test.go``.
"""

import json
import os

from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.cps.cps import CPSClient

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

test_dir = os.path.abspath(os.path.dirname(__file__))

# ---------------------------------------------------------------------------
# Common test data constants
# ---------------------------------------------------------------------------

# Standard 500 error response body used by many Go tests.
INTERNAL_SERVER_ERROR_BODY = {
    "type": "internal_error",
    "title": "Internal Server Error",
    "detail": "Error fetching data",
    "instance": "",
    "statusCode": 500,
}

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_session():
    """Create a mock Session for CPS client testing.

    Mirrors Go's ``mockAPIClient`` which creates a CPS client bound to a
    test TLS server with EdgeGrid signing configured.

    The mock session provides:

    * ``exec()`` method that returns ``(response, result)`` tuple
    * Configurable response status codes and bodies
    """
    session = MagicMock()
    session.exec = MagicMock()
    return session


@pytest.fixture
def cps_client(mock_session):  # pylint: disable=redefined-outer-name
    """Create a :class:`CPSClient` bound to the mock session.

    Mirrors Go's ``mockAPIClient(t, fn)``.
    """
    return CPSClient(mock_session)


# ---------------------------------------------------------------------------
# Helper functions (not fixtures — called directly by tests)
# ---------------------------------------------------------------------------


def make_mock_response(status_code, body=None, headers=None):
    """Create a mock HTTP response.

    Mirrors the Go test pattern where ``httptest.NewTLSServer`` handler
    returns a configurable status code and body.

    Args:
        status_code: HTTP status code to return.
        body: Response body (``dict``, ``list``, or ``str``).  If a
            ``dict`` or ``list`` is supplied it will be JSON-serialized.
        headers: Optional response headers dict.

    Returns:
        ``MagicMock`` configured as a ``requests.Response``.
    """
    response = MagicMock()
    response.status_code = status_code
    response.headers = headers or {}

    if isinstance(body, (dict, list)):
        response.json.return_value = body
        response.text = json.dumps(body)
    elif isinstance(body, str):
        response.text = body
        try:
            response.json.return_value = json.loads(body)
        except (json.JSONDecodeError, TypeError):
            response.json.side_effect = json.JSONDecodeError("", "", 0)
    else:
        response.text = ""
        response.json.return_value = None

    response.content = (
        response.text.encode("utf-8") if response.text else b""
    )
    return response


def make_error_response(  # pylint: disable=too-many-arguments
    status_code=500,
    *,
    error_type="internal_error",
    title="Internal Server Error",
    detail="Error processing request",
    instance="",
    errors_list=None,
    warnings_list=None,
):
    """Create a standard CPS API error response.

    Mirrors the common error response pattern used in Go test fixtures.

    Args:
        status_code: HTTP error status code.
        error_type: Error type string.
        title: Error title.
        detail: Error detail message.
        instance: Optional instance identifier.
        errors_list: Optional errors array.
        warnings_list: Optional warnings array.
    """
    body = {
        "type": error_type,
        "title": title,
        "detail": detail,
        "instance": instance,
        "statusCode": status_code,
    }
    if errors_list is not None:
        body["errors"] = errors_list
    if warnings_list is not None:
        body["warnings"] = warnings_list

    return make_mock_response(status_code, body)


def load_fixture(filename):
    """Load a JSON fixture file from the ``testdata`` directory.

    Args:
        filename: Filename relative to the ``testdata/`` directory.

    Returns:
        Parsed JSON data.
    """
    fixture_path = os.path.join(test_dir, "testdata", filename)
    with open(fixture_path, "r", encoding="utf-8") as fobj:
        return json.load(fobj)


def configure_mock_session(  # pylint: disable=redefined-outer-name,too-many-arguments
    mock_session,
    method,
    path,
    status_code,
    response_body,
    *,
    accept_header=None,
    content_type_header=None,
    request_body_validator=None,
):
    """Configure mock session to return a specific response.

    Mirrors Go's ``httptest`` handler that validates URL path, method,
    and headers before returning a configured response.

    The *method*, *path*, and header expectations are stored on the mock
    session so that tests can later assert the correct request was made.
    If a *request_body_validator* is provided it is also stored for
    downstream assertion.

    Args:
        mock_session: The mock session to configure.
        method: Expected HTTP method.
        path: Expected URL path.
        status_code: Status code for the response.
        response_body: Response body (``dict``/``list``/``str``).
        accept_header: Expected *Accept* header value.
        content_type_header: Expected *Content-Type* header value.
        request_body_validator: Optional callable to validate the
            request body.
    """
    response = make_mock_response(status_code, response_body)

    # Store expected request metadata so tests can assert on them.
    mock_session.expected_method = method
    mock_session.expected_path = path
    mock_session.expected_accept_header = accept_header
    mock_session.expected_content_type_header = content_type_header
    mock_session.expected_request_body_validator = request_body_validator

    if isinstance(response_body, (dict, list)):
        parsed_body = response_body
    elif isinstance(response_body, str):
        try:
            parsed_body = json.loads(response_body)
        except (json.JSONDecodeError, TypeError):
            parsed_body = None
    else:
        parsed_body = None

    mock_session.exec.return_value = (
        response,
        parsed_body if status_code < 400 else None,
    )
    return response
