# pylint: disable=missing-function-docstring
"""Pytest fixtures for API Definitions service client tests.

Provides mock HTTP server helpers, fixture loading, and common test data
used by test_apidefinitions.py. Mirrors the Go mockAPIClient pattern from
apidefinitions_test.go.
"""

import json
import os

from unittest.mock import MagicMock, patch  # pylint: disable=unused-import

import pytest

from akamai.edgegrid.apidefinitions.apidefinitions import Client
from akamai.edgegrid.session import Session


test_dir = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture
def mock_session():
    """Create a mock Session for testing.

    Returns a Session-like mock object where the HTTP request method
    is mocked, allowing tests to control responses without making
    real HTTP calls. Mirrors Go's httptest.NewTLSServer + mockAPIClient.
    """
    session = MagicMock(spec=Session)
    return session


@pytest.fixture
def mock_client(mock_session):  # pylint: disable=redefined-outer-name
    """Create a Client instance backed by a mocked Session.

    Mirrors Go mockAPIClient which creates a Client with a mocked
    HTTP transport. Tests configure mock_session.exec to return
    specific responses before calling client methods.
    """
    client = Client(mock_session)
    return client


def mock_response(status_code=200, text_body="", headers=None):
    """Create a mock HTTP response object.

    Mimics requests.Response behavior for testing.
    Used to configure mock_session.exec return values.

    Args:
        status_code: HTTP status code.
        text_body: Raw response body text (use VERBATIM Go test values).
        headers: Response headers dict.

    Returns:
        MagicMock configured as a requests.Response.
    """
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = headers or {}
    resp.text = text_body

    # Configure json() to parse the text body
    try:
        parsed = json.loads(text_body) if text_body.strip() else None
        resp.json.return_value = parsed
    except (json.JSONDecodeError, ValueError):
        resp.json.side_effect = json.JSONDecodeError("", "", 0)

    resp.content = text_body.encode("utf-8") if text_body else b""
    return resp


def load_fixture(filename):
    """Load a JSON test fixture from the testdata/ directory.

    Args:
        filename: Name of the JSON file in testdata/.

    Returns:
        Parsed JSON data (dict or list).
    """
    fixture_path = os.path.join(test_dir, "testdata", filename)
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


def assert_json_equal(actual, expected):
    """Assert two JSON values are semantically equal.

    Handles comparison of JSON strings or dicts/lists.
    Mirrors Go's assert.JSONEq behavior.

    Args:
        actual: Actual JSON value (string or dict/list).
        expected: Expected JSON value (string or dict/list).
    """
    if isinstance(actual, str):
        actual = json.loads(actual)
    if isinstance(expected, str):
        expected = json.loads(expected)
    assert actual == expected
