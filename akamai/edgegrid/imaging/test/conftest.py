# pylint: disable=missing-function-docstring
"""Pytest fixtures and helpers for Imaging API tests"""

import json
import os
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.imaging.imaging import Client


test_dir = os.path.abspath(os.path.dirname(__file__))


def create_mock_response(status_code, body="", headers=None):
    """Create a mock HTTP response object.

    Mirrors Go's httptest.NewTLSServer response pattern where the test
    server writes a status code, response body, and optional headers.

    Args:
        status_code: HTTP status code for the response.
        body: Response body string (JSON or plain text).
        headers: Optional dict of response headers.

    Returns:
        MagicMock configured as an HTTP response with ``status_code``,
        ``text``, ``headers``, and ``json()`` attributes.
    """
    response = MagicMock()
    response.status_code = status_code
    response.text = body
    response.headers = headers or {}

    # Configure json() method — parse body when valid JSON, raise on
    # non-JSON to mirror real requests.Response behaviour.
    if body and body.strip():
        try:
            parsed = json.loads(body)
            response.json.return_value = parsed
        except json.JSONDecodeError:
            response.json.side_effect = json.JSONDecodeError(
                "Expecting value", body, 0
            )
    else:
        response.json.return_value = {}

    return response


def create_mock_session():
    """Create a mock session for testing.

    Mirrors Go's ``mockAPIClient`` pattern from ``imaging_test.go``.
    Returns a ``MagicMock`` that behaves like a ``Session``, allowing
    per-test configuration of ``exec()`` return values.
    """
    session = MagicMock()
    return session


@pytest.fixture
def mock_session():
    """Provide a fresh mock session for each test."""
    return create_mock_session()


@pytest.fixture
def imaging_client(mock_session):  # pylint: disable=redefined-outer-name
    """Provide an Imaging API client backed by a mock session.

    Mirrors Go's ``client := mockAPIClient(t, mockServer)`` pattern.
    """
    return Client(mock_session)


def load_json_fixture(filename):
    """Load a JSON fixture file from the ``testdata`` directory.

    Args:
        filename: Name of the JSON file inside ``testdata/``.

    Returns:
        Parsed JSON data (dict or list).
    """
    filepath = os.path.join(test_dir, "testdata", filename)
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)
