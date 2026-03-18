"""Pytest fixtures and helpers for Cloud Access Manager tests."""

import json
import os

from unittest.mock import MagicMock

import pytest

# Absolute path to this test directory, used for locating fixture files.
test_dir = os.path.abspath(os.path.dirname(__file__))


def load_test_data(name):
    """Load raw test data content from the testdata directory.

    Mirrors Go ``loadTestData`` (access_key_test.go lines 577-584).
    Reads the file as UTF-8 text so callers can pass it directly to
    ``json.loads`` or use it as a raw response body string.

    :param name: Relative path within ``testdata/``,
        e.g. ``"AccessKey/GetAccessKey.resp.json"``.
    :returns: String content of the requested fixture file.
    """
    path = os.path.join(test_dir, "testdata", name)
    with open(path, encoding="utf-8") as fobj:
        return fobj.read()


def load_json_fixture(name):
    """Load and parse a JSON fixture from the testdata directory.

    Convenience wrapper around :func:`load_test_data` that additionally
    deserialises the content into a Python object.

    :param name: Relative path within ``testdata/``.
    :returns: Parsed JSON as ``dict`` or ``list``.
    """
    return json.loads(load_test_data(name))


def make_mock_response(status_code, body="", headers=None):
    """Create a mock HTTP response object.

    Replaces Go's ``httptest.NewTLSServer`` + ``http.HandlerFunc``
    pattern.  Returns a :class:`~unittest.mock.MagicMock` configured
    to behave like a ``requests.Response``.

    :param status_code: HTTP status code (e.g. ``200``, ``404``).
    :param body: Response body string.  When the string is valid JSON,
        ``response.json()`` will return the parsed payload.  For
        non-JSON bodies a :class:`ValueError` is raised on ``.json()``
        instead.
    :param headers: Optional mapping of response headers.
    :returns: ``MagicMock`` mimicking ``requests.Response``.
    """
    response = MagicMock()
    response.status_code = status_code
    response.text = body

    if body and body.strip():
        try:
            response.json.return_value = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            response.json.side_effect = ValueError("No JSON")
    else:
        response.json.return_value = {}

    response.headers = dict(headers) if headers else {}
    return response


@pytest.fixture
def mock_session():
    """Create a mock Session object for testing.

    Mirrors the Go ``mockAPIClient`` pattern
    (cloudaccess_test.go lines 17-32).  Returns a
    :class:`~unittest.mock.MagicMock` whose ``exec()`` method can be
    configured per-test to return ``(response, parsed_result)`` tuples.
    """
    session = MagicMock()
    return session


@pytest.fixture
def client(mock_session):  # pylint: disable=redefined-outer-name
    """Create a :class:`CloudAccessClient` backed by *mock_session*.

    Mirrors the Go ``Client(s)`` constructor call in test setup.
    Uses a lazy import to avoid circular-import issues during pytest
    collection.

    :returns: ``CloudAccessClient`` instance wired to *mock_session*.
    """
    # pylint: disable=import-outside-toplevel
    from akamai.edgegrid.cloudaccess.cloudaccess import CloudAccessClient
    return CloudAccessClient(mock_session)
