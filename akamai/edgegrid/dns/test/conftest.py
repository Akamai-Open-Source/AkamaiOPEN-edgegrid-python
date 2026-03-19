# pylint: disable=redefined-outer-name
"""Pytest fixtures for Edge DNS API client tests.

Provides ``mock_session`` and ``dns_client`` fixtures mirroring Go's
``mockAPIClient`` helper from ``dns_test.go``.  Also re-exports shared
test helpers (``mock_response``, ``load_json_fixture``, ``fixture_path``)
from :mod:`akamai.edgegrid.test_helpers` so that test modules in this
package can import them from a single location.
"""

from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.session import Session
from akamai.edgegrid.dns.dns import Client
from akamai.edgegrid.test_helpers import (
    mock_response,
    load_json_fixture,
    fixture_path,
)

# Re-export shared helpers alongside the fixtures so callers can reach
# everything through this conftest without a deep module path.  Listing
# them in __all__ also prevents pylint W0611 (unused-import).
__all__ = [
    "mock_session",
    "dns_client",
    "mock_response",
    "load_json_fixture",
    "fixture_path",
]


@pytest.fixture
def mock_session():
    """Create a mock :class:`Session` mirroring Go's httptest server pattern.

    Constructs a :class:`~unittest.mock.MagicMock` with ``spec=Session``
    so that only attributes and methods defined on the real
    :class:`~akamai.edgegrid.session.Session` class are accessible.
    This catches invalid attribute access early during test execution.

    The returned mock's ``exec`` method is itself a ``MagicMock`` whose
    ``return_value`` can be configured per-test to return specific HTTP
    responses and parsed data tuples::

        mock_session.exec.return_value = (
            mock_response(status_code=200, json_body={...}),
            {...},
        )

    Returns:
        MagicMock configured with ``spec=Session``.
    """
    session = MagicMock(spec=Session)
    return session


@pytest.fixture
def dns_client(mock_session):
    """Create a :class:`Client` bound to the *mock_session* fixture.

    Mirrors Go's ``mockAPIClient`` helper from ``dns_test.go`` (lines
    17-32) which creates an ``httptest.TLSServer``, configures a
    ``session.Session`` with the server's certificate, and returns
    ``dns.Client(session)``.

    In Python the TLS layer is unnecessary because we mock at the
    :class:`Session` level.  The fixture simply instantiates
    ``Client(mock_session)`` — identical to Go's ``return Client(s)``.

    Args:
        mock_session: Injected mock :class:`Session` fixture.

    Returns:
        :class:`Client` instance wired to the mock session for testing.
    """
    return Client(mock_session)
