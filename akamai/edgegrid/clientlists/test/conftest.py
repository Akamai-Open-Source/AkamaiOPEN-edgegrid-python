# pylint: disable=missing-function-docstring
"""Pytest fixtures for Client Lists API tests."""

import json
import os
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.clientlists.clientlists import Client


test_dir = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture
def mock_session():
    """Create a mock session for testing.

    Mirrors Go's mockAPIClient pattern where a test server + session
    are created for each test. In Python, we mock the session's
    request method to return predetermined responses.
    """
    session = MagicMock()
    return session


@pytest.fixture
def mock_client(mock_session):  # pylint: disable=redefined-outer-name
    """Create a Client Lists client backed by a mock session.

    Mirrors Go's:
        client := mockAPIClient(t, mockServer)
    """
    client = Client(mock_session)
    return client


def create_mock_response(
    status_code: int, body: str = "", headers: dict | None = None,
):
    """Create a mock HTTP response.

    Mirrors Go's httptest.NewTLSServer handler that writes status code
    and body to the response writer.

    Args:
        status_code: HTTP status code
        body: Response body string (JSON or non-JSON)
        headers: Optional response headers dict

    Returns:
        MagicMock configured as a requests.Response
    """
    response = MagicMock()
    response.status_code = status_code
    response.text = body
    response.headers = headers or {}

    # Support .json() method for JSON body parsing
    if body:
        try:
            parsed = json.loads(body)
            response.json.return_value = parsed
        except (json.JSONDecodeError, ValueError):
            response.json.side_effect = json.JSONDecodeError("", "", 0)
    else:
        response.json.side_effect = json.JSONDecodeError("", "", 0)

    # Support iteration and content access
    response.content = body.encode("utf-8") if body else b""

    return response


def load_test_fixture(filename: str) -> dict:
    """Load a JSON test fixture file from the testdata directory.

    Args:
        filename: Name of the JSON file in testdata/

    Returns:
        Parsed JSON data as a dict
    """
    filepath = os.path.join(test_dir, "testdata", filename)
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)
