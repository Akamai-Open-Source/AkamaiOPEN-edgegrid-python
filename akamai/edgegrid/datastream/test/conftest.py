# pylint: disable=missing-function-docstring
"""Shared pytest fixtures and helpers for DataStream API client tests."""

import json
import os
from unittest.mock import MagicMock, Mock

import pytest

from akamai.edgegrid.datastream.datastream import Client

test_dir = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture
def mock_session():
    """Create a mock session for testing.

    Returns a MagicMock that simulates a Session object.
    The mock's request method can be configured to return
    specific responses for each test case.
    """
    session = MagicMock()
    return session


@pytest.fixture
def mock_client(mock_session):  # pylint: disable=redefined-outer-name
    """Create a DataStream client with a mock session."""
    return Client(mock_session)


def make_mock_response(status_code, body="", headers=None):
    """Create a mock HTTP response.

    Mirrors Go's httptest.NewTLSServer handler that writes
    status code and response body.

    Args:
        status_code: HTTP status code (e.g., 200, 400, 500)
        body: Response body string (typically JSON)
        headers: Optional response headers dict

    Returns:
        MagicMock simulating a requests.Response
    """
    response = Mock()
    response.status_code = status_code
    response.text = body
    response.headers = headers or {}
    if body and body.strip():
        try:
            response.json.return_value = json.loads(body)
        except json.JSONDecodeError:
            response.json.side_effect = json.JSONDecodeError("", "", 0)
    else:
        response.json.return_value = {}
    return response


def load_testdata(filename):
    """Load a JSON test fixture from the testdata directory.

    Args:
        filename: Name of the JSON file in testdata/

    Returns:
        Parsed JSON data (dict or list)
    """
    filepath = os.path.join(test_dir, "testdata", filename)
    with open(filepath, encoding="utf-8") as data_file:
        return json.load(data_file)
