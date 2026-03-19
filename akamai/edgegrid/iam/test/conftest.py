# pylint: disable=missing-function-docstring
"""Test fixtures and helpers for IAM service client tests."""

import json
import os
from unittest.mock import MagicMock

import pytest

# Path to this test directory — mirrors existing conftest.py pattern
# at akamai/edgegrid/test/conftest.py which uses the same idiom.
test_dir = os.path.abspath(os.path.dirname(__file__))


def load_fixture(filename: str):
    """Load a JSON fixture file from the testdata/ directory.

    Mirrors Go ``loadFixtureBytes`` helpers found in IAM test files.
    Reads and parses a JSON file from ``testdata/`` relative to this
    test directory.

    Args:
        filename: Name of the fixture file relative to ``testdata/``,
            e.g. ``'lock_api_client_200.json'``.

    Returns:
        Parsed JSON data (``dict`` or ``list``).
    """
    filepath = os.path.join(test_dir, 'testdata', filename)
    with open(filepath, 'r', encoding='utf-8') as fobj:
        return json.load(fobj)


def mock_response(status_code: int = 200, body: str = "",
                  headers: dict | None = None):
    """Create a mock HTTP response mimicking ``requests.Response``.

    This mirrors Go's ``httptest.NewTLSServer`` response writing pattern
    where the handler writes a status code and response body:

    - ``w.WriteHeader(tc.responseStatus)`` → ``status_code``
    - ``w.Write([]byte(tc.responseBody))`` → ``body`` text

    Args:
        status_code: HTTP status code (e.g. 200, 400, 500).
        body: Response body as string (JSON or plain text).
        headers: Optional response headers ``dict``.

    Returns:
        ``MagicMock`` configured to behave like ``requests.Response``
        with ``status_code``, ``text``, ``content``, ``headers``,
        ``json()``, and ``close()`` attributes.
    """
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = headers or {}
    resp.text = body
    resp.content = body.encode('utf-8') if body else b''

    # Support .json() method — parse body if valid JSON,
    # otherwise raise json.JSONDecodeError like real Response.json().
    if body and body.strip():
        try:
            parsed = json.loads(body)
            resp.json.return_value = parsed
        except json.JSONDecodeError:
            resp.json.side_effect = json.JSONDecodeError("", "", 0)
    else:
        resp.json.side_effect = json.JSONDecodeError("", "", 0)

    # Support .close() for response body cleanup
    resp.close.return_value = None

    return resp


@pytest.fixture
def mock_session():
    """Create a mock Session for IAMClient testing.

    Provides a ``MagicMock`` that mimics the ``Session`` class interface
    (``exec`` method), allowing tests to control HTTP responses.

    Mirrors Go's ``session.New()`` used inside ``mockAPIClient``.
    Function-scoped so each test gets a fresh mock.

    Usage in tests::

        def test_something(mock_session):
            mock_session.exec.return_value = (
                mock_response(200, '{"key":"val"}'),
                {"key": "val"},
            )
            client = IAMClient(mock_session)
            result = client.some_method(params)
    """
    session = MagicMock()
    return session


@pytest.fixture
def iam_client(mock_session):  # pylint: disable=redefined-outer-name
    """Create an IAMClient instance with a mock session.

    Mirrors Go's ``mockAPIClient(t, mockServer)`` pattern — provides a
    pre-configured client ready for testing with the ``mock_session``
    fixture.

    The import of ``IAMClient`` is deferred to avoid circular import
    issues between test infrastructure and production code.
    """
    # Lazy import to avoid circular dependency at module load time
    from akamai.edgegrid.iam.iam import IAMClient  # pylint: disable=import-outside-toplevel
    return IAMClient(mock_session)


def assert_exec_called_with(mock_session, method: str, path: str,  # pylint: disable=redefined-outer-name
                            **kwargs):
    """Assert that ``session.exec`` was called with expected arguments.

    Mirrors Go test assertions::

        assert.Equal(t, tc.expectedPath, r.URL.String())
        assert.Equal(t, http.MethodPost, r.Method)

    Verifies the mock session's ``exec`` method was called exactly once
    with the expected HTTP method and URL path as positional arguments,
    and optionally checks keyword arguments (``body``, ``params``,
    ``expect_json``, ``error_parser``, etc.).

    Args:
        mock_session: The mock ``Session`` instance.
        method: Expected HTTP method (``GET``, ``POST``, ``PUT``,
            ``DELETE``).
        path: Expected URL path.
        **kwargs: Additional expected keyword arguments passed to
            ``session.exec`` (e.g. ``body``, ``params``,
            ``expect_json``).
    """
    mock_session.exec.assert_called_once()
    call_args = mock_session.exec.call_args

    # Positional arguments: (method, path)
    assert call_args[0][0] == method, (
        f"Expected method {method}, got {call_args[0][0]}"
    )
    assert call_args[0][1] == path, (
        f"Expected path {path}, got {call_args[0][1]}"
    )

    # Keyword arguments verification
    for key, value in kwargs.items():
        assert key in call_args.kwargs, (
            f"Expected keyword argument '{key}' not found in exec call. "
            f"Actual kwargs: {list(call_args.kwargs.keys())}"
        )
        assert call_args.kwargs[key] == value, (
            f"Expected {key}={value!r}, got {call_args.kwargs[key]!r}"
        )
