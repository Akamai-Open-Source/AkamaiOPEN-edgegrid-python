# pylint: disable=missing-function-docstring,redefined-outer-name
"""Shared pytest fixtures for HAPI service client tests."""

import json
from unittest.mock import MagicMock, patch  # pylint: disable=unused-import

import pytest

from akamai.edgegrid.hapi.hapi import HapiClient
from akamai.edgegrid.hapi.errors import parse_hapi_error  # pylint: disable=unused-import


@pytest.fixture
def mock_session():
    """Provide a mocked Session for HAPI client testing.

    Creates a MagicMock that simulates the Session class, allowing tests
    to configure return values for session.exec() calls.

    Mirrors Go's mockAPIClient helper from hapi_test.go.
    """
    session = MagicMock()
    return session


@pytest.fixture
def hapi_client(mock_session):
    """Provide an HapiClient initialized with a mock session.

    Returns:
        HapiClient configured with mock_session for testing.
    """
    return HapiClient(mock_session)


def make_mock_response(status_code, body_text=""):
    """Create a mock HTTP response object.

    Args:
        status_code: HTTP status code
        body_text: Raw response body text

    Returns:
        MagicMock mimicking a requests.Response
    """
    response = MagicMock()
    response.status_code = status_code
    response.text = body_text
    response.content = (
        body_text.encode("utf-8") if isinstance(body_text, str) else body_text
    )

    # Configure .json() to parse the body text
    try:
        parsed = json.loads(body_text)
        response.json.return_value = parsed
    except (json.JSONDecodeError, ValueError):
        response.json.side_effect = json.JSONDecodeError(
            "Expecting value", body_text, 0
        )

    return response
