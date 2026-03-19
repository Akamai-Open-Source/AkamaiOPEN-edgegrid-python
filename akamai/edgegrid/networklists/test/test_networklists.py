"""Unit tests for the Network Lists API client.

Mirrors ALL Go test scenarios from:
- networklists_test.go (TestClient)
- activations_test.go (TestApsec_ListActivations, TestAppSec_GetActivations)
- network_list_test.go (ListNetworkList, FilterNetworkLists, GetNetworkList,
  CreateNetworkList, UpdateNetworkList, DeleteNetworkList)
- network_list_description_test.go (ListDescription, GetDescription,
  UpdateDescription)
- network_list_subscription_test.go (ListSubscription, GetSubscription,
  UpdateSubscription)
- errors_test.go (TestNewError, TestJsonErrorUnmarshalling)
"""

import json
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.networklists.networklists import NetworkListsClient
from akamai.edgegrid.networklists.models import (
    GetActivationsRequest,
    GetActivationsResponse,
    GetNetworkListRequest,
    GetNetworkListsRequest,
    GetNetworkListsResponse,
    GetNetworkListResponse,
    CreateNetworkListRequest,
    CreateNetworkListResponse,
    UpdateNetworkListRequest,
    UpdateNetworkListResponse,
    RemoveNetworkListRequest,
    RemoveNetworkListResponse,
    GetNetworkListDescriptionRequest,
    GetNetworkListDescriptionResponse,
    UpdateNetworkListDescriptionRequest,
    UpdateNetworkListDescriptionResponse,
    GetNetworkListSubscriptionRequest,
    GetNetworkListSubscriptionResponse,
    UpdateNetworkListSubscriptionRequest,
    UpdateNetworkListSubscriptionResponse,
    from_dict,
)
from akamai.edgegrid.networklists.errors import Error
from akamai.edgegrid.networklists.test.conftest import (
    load_fixture_bytes,
    compact_json,
    create_mock_response,
)


# -----------------------------------------------------------------------
# TestClient — Mirrors Go TestClient (networklists_test.go lines 63-89)
# -----------------------------------------------------------------------


class TestClient:
    """Test client construction. Mirrors Go TestClient."""

    def test_no_options_provided_return_default(self):
        """Verify client can be constructed with a session (no options)."""
        session = MagicMock()
        client = NetworkListsClient(session)
        assert client._session is session  # pylint: disable=protected-access

    def test_dummy_option(self):
        """Verify client construction with options (Go dummy option)."""
        session = MagicMock()
        client = NetworkListsClient(session)
        assert client._session is session  # pylint: disable=protected-access


# -----------------------------------------------------------------------
# Activation Tests — activations_test.go
# -----------------------------------------------------------------------


@pytest.mark.parametrize("name, test_case", [
    ("200 OK", {
        "with_error": None,
    }),
    ("500 internal server error", {
        "with_error": Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching Activations",
            status_code=500,
        ),
    }),
])
def test_apsec_list_activations(name, test_case, mock_session, mock_client):
    """Mirrors Go TestApsec_ListActivations (activations_test.go:16-84).

    Tests get_activations with context headers variant.
    """
    params = GetActivationsRequest(
        unique_id="38069_INTERNALWHITELIST", network="STAGING",
    )
    expected_path = (
        "/network-list/v2/network-lists/38069_INTERNALWHITELIST"
        "/environments/STAGING/status"
    )

    if test_case["with_error"] is not None:
        mock_session.get.side_effect = test_case["with_error"]
        with pytest.raises(Error) as exc_info:
            mock_client.get_activations(params)
        assert exc_info.value.is_equivalent(test_case["with_error"]), \
            f"Error mismatch for test case: {name}"
    else:
        resp_data = compact_json(
            load_fixture_bytes("TestActivations/Activations.json"),
        )
        parsed = json.loads(resp_data)
        expected = from_dict(GetActivationsResponse, parsed)
        mock_session.get.return_value = (
            MagicMock(status_code=200), parsed,
        )
        result = mock_client.get_activations(params)
        assert result == expected, \
            f"Response mismatch for test case: {name}"

    mock_session.get.assert_called_once()
    assert mock_session.get.call_args[0][0] == expected_path


@pytest.mark.parametrize("name, test_case", [
    ("200 OK", {
        "with_error": None,
    }),
    ("500 internal server error", {
        "with_error": Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching Activations",
            status_code=500,
        ),
    }),
])
def test_appsec_get_activations(name, test_case, mock_session, mock_client):
    """Mirrors Go TestAppSec_GetActivations (activations_test.go:87-144).

    Tests get_activations without context headers (background context).
    Error body does NOT include 'status' field — different from List variant.
    """
    params = GetActivationsRequest(
        unique_id="38069_INTERNALWHITELIST", network="STAGING",
    )
    expected_path = (
        "/network-list/v2/network-lists/38069_INTERNALWHITELIST"
        "/environments/STAGING/status"
    )

    if test_case["with_error"] is not None:
        mock_session.get.side_effect = test_case["with_error"]
        with pytest.raises(Error) as exc_info:
            mock_client.get_activations(params)
        assert exc_info.value.is_equivalent(test_case["with_error"]), \
            f"Error mismatch for test case: {name}"
    else:
        resp_data = compact_json(
            load_fixture_bytes("TestActivations/Activations.json"),
        )
        parsed = json.loads(resp_data)
        expected = from_dict(GetActivationsResponse, parsed)
        mock_session.get.return_value = (
            MagicMock(status_code=200), parsed,
        )
        result = mock_client.get_activations(params)
        assert result == expected, \
            f"Response mismatch for test case: {name}"

    mock_session.get.assert_called_once()
    assert mock_session.get.call_args[0][0] == expected_path


# -----------------------------------------------------------------------
# Network List Tests — network_list_test.go
# -----------------------------------------------------------------------


@pytest.mark.parametrize("name, test_case", [
    ("200 OK", {
        "with_error": None,
    }),
    ("500 internal server error", {
        "with_error": Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching networklist",
            status_code=500,
        ),
    }),
])
def test_network_list_list_network_list(
    name, test_case, mock_session, mock_client,
):
    """Mirrors Go TestNetworkList_ListNetworkList (network_list_test.go:16-88).

    HTTP GET /network-list/v2/network-lists — no filtering.
    """
    params = GetNetworkListsRequest()
    expected_path = "/network-list/v2/network-lists"

    if test_case["with_error"] is not None:
        mock_session.get.side_effect = test_case["with_error"]
        with pytest.raises(Error) as exc_info:
            mock_client.get_network_lists(params)
        assert exc_info.value.is_equivalent(test_case["with_error"]), \
            f"Error mismatch for test case: {name}"
    else:
        resp_data = compact_json(
            load_fixture_bytes("TestNetworkList/NetworkLists.json"),
        )
        parsed = json.loads(resp_data)
        expected = from_dict(GetNetworkListsResponse, parsed)
        mock_session.get.return_value = (
            MagicMock(status_code=200), parsed,
        )
        result = mock_client.get_network_lists(params)
        assert result == expected, \
            f"Response mismatch for test case: {name}"

    mock_session.get.assert_called_once()
    assert mock_session.get.call_args[0][0] == expected_path


@pytest.mark.parametrize("name, test_case", [
    ("200 OK", {
        "params": GetNetworkListsRequest(type="GEO"),
        "with_error": None,
    }),
    ("500 internal server error", {
        "params": GetNetworkListsRequest(),
        "with_error": Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching networklist",
            status_code=500,
        ),
    }),
])
def test_network_list_filter_network_lists(
    name, test_case, mock_session, mock_client,
):
    """Mirrors Go TestNetworkList_FilterNetworkLists (network_list_test.go:90-167).

    Success case: server returns full catalog (NetworkLists.json),
    client filters to GEO items only.
    Expected response uses NetworkLists_GEO.json, NOT NetworkLists.json.
    """
    expected_path = "/network-list/v2/network-lists"

    if test_case["with_error"] is not None:
        mock_session.get.side_effect = test_case["with_error"]
        with pytest.raises(Error) as exc_info:
            mock_client.get_network_lists(test_case["params"])
        assert exc_info.value.is_equivalent(test_case["with_error"]), \
            f"Error mismatch for test case: {name}"
    else:
        # Server returns full unfiltered list
        server_data = compact_json(
            load_fixture_bytes("TestNetworkList/NetworkLists.json"),
        )
        parsed = json.loads(server_data)
        # Expected result is the GEO-filtered subset
        expected_data = compact_json(
            load_fixture_bytes("TestNetworkList/NetworkLists_GEO.json"),
        )
        expected = from_dict(
            GetNetworkListsResponse, json.loads(expected_data),
        )
        mock_session.get.return_value = (
            MagicMock(status_code=200), parsed,
        )
        result = mock_client.get_network_lists(test_case["params"])
        assert result == expected, \
            f"Response mismatch for test case: {name}"

    mock_session.get.assert_called_once()
    assert mock_session.get.call_args[0][0] == expected_path


@pytest.mark.parametrize("name, test_case", [
    ("200 OK", {
        "with_error": None,
    }),
    ("500 internal server error", {
        "with_error": Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching networklist",
            status_code=500,
        ),
    }),
])
def test_network_list_get_network_list(
    name, test_case, mock_session, mock_client,
):
    """Mirrors Go TestNetworkList_GetNetworkList (network_list_test.go:169-231).

    HTTP GET /network-list/v2/network-lists/{uniqueId}
    """
    params = GetNetworkListRequest(unique_id="Test")
    expected_path = "/network-list/v2/network-lists/Test"

    if test_case["with_error"] is not None:
        mock_session.get.side_effect = test_case["with_error"]
        with pytest.raises(Error) as exc_info:
            mock_client.get_network_list(params)
        assert exc_info.value.is_equivalent(test_case["with_error"]), \
            f"Error mismatch for test case: {name}"
    else:
        resp_data = compact_json(
            load_fixture_bytes("TestNetworkList/NetworkList.json"),
        )
        parsed = json.loads(resp_data)
        expected = from_dict(GetNetworkListResponse, parsed)
        mock_session.get.return_value = (
            MagicMock(status_code=200), parsed,
        )
        result = mock_client.get_network_list(params)
        assert result == expected, \
            f"Response mismatch for test case: {name}"

    mock_session.get.assert_called_once()
    assert mock_session.get.call_args[0][0] == expected_path


@pytest.mark.parametrize("name, test_case", [
    ("201 Created", {
        "with_error": None,
    }),
    ("500 internal server error", {
        "with_error": Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error creating networklist",
            status_code=500,
        ),
    }),
])
def test_network_list_create_network_list(
    name, test_case, mock_session, mock_client,
):
    """Mirrors Go TestNetworkList_CreateNetworkList (network_list_test.go:233-311).

    HTTP POST /network-list/v2/network-lists
    """
    params = CreateNetworkListRequest(name="Test")
    expected_path = "/network-list/v2/network-lists"

    if test_case["with_error"] is not None:
        mock_session.post.side_effect = test_case["with_error"]
        with pytest.raises(Error) as exc_info:
            mock_client.create_network_list(params)
        assert exc_info.value.is_equivalent(test_case["with_error"]), \
            f"Error mismatch for test case: {name}"
    else:
        resp_data = compact_json(
            load_fixture_bytes("TestNetworkList/NetworkList.json"),
        )
        parsed = json.loads(resp_data)
        expected = from_dict(CreateNetworkListResponse, parsed)
        mock_session.post.return_value = (
            MagicMock(status_code=201), parsed,
        )
        result = mock_client.create_network_list(params)
        assert result == expected, \
            f"Response mismatch for test case: {name}"

    mock_session.post.assert_called_once()
    assert mock_session.post.call_args[0][0] == expected_path


@pytest.mark.parametrize("name, test_case", [
    ("200 Success", {
        "with_error": None,
    }),
    ("500 internal server error", {
        "with_error": Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error updating networklist",
            status_code=500,
        ),
    }),
])
def test_network_list_update_network_list(
    name, test_case, mock_session, mock_client,
):
    """Mirrors Go TestNetworkList_UpdateNetworkList (network_list_test.go:313-389).

    HTTP PUT /network-list/v2/network-lists/{uniqueId}
    """
    params = UpdateNetworkListRequest(name="TEST", unique_id="Test")
    expected_path = "/network-list/v2/network-lists/Test"

    if test_case["with_error"] is not None:
        mock_session.put.side_effect = test_case["with_error"]
        with pytest.raises(Error) as exc_info:
            mock_client.update_network_list(params)
        assert exc_info.value.is_equivalent(test_case["with_error"]), \
            f"Error mismatch for test case: {name}"
    else:
        resp_data = compact_json(
            load_fixture_bytes("TestNetworkList/NetworkList.json"),
        )
        parsed = json.loads(resp_data)
        expected = from_dict(UpdateNetworkListResponse, parsed)
        mock_session.put.return_value = (
            MagicMock(status_code=201), parsed,
        )
        result = mock_client.update_network_list(params)
        assert result == expected, \
            f"Response mismatch for test case: {name}"

    mock_session.put.assert_called_once()
    assert mock_session.put.call_args[0][0] == expected_path


@pytest.mark.parametrize("name, test_case", [
    ("200 Success", {
        "with_error": None,
    }),
    ("500 internal server error", {
        "with_error": Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error deleting networklist",
            status_code=500,
        ),
    }),
])
def test_network_list_delete_network_list(
    name, test_case, mock_session, mock_client,
):
    """Mirrors Go TestNetworkList_DeleteNetworkList (network_list_test.go:391-467).

    HTTP DELETE /network-list/v2/network-lists/{uniqueId}
    Uses NetworkListEmpty.json fixture for success response.
    """
    params = RemoveNetworkListRequest(unique_id="Test")
    expected_path = "/network-list/v2/network-lists/Test"

    if test_case["with_error"] is not None:
        mock_session.delete.side_effect = test_case["with_error"]
        with pytest.raises(Error) as exc_info:
            mock_client.remove_network_list(params)
        assert exc_info.value.is_equivalent(test_case["with_error"]), \
            f"Error mismatch for test case: {name}"
    else:
        resp_data = compact_json(
            load_fixture_bytes("TestNetworkList/NetworkListEmpty.json"),
        )
        parsed = json.loads(resp_data)
        expected = from_dict(RemoveNetworkListResponse, parsed)
        mock_session.delete.return_value = (
            MagicMock(status_code=200), parsed,
        )
        result = mock_client.remove_network_list(params)
        assert result == expected, \
            f"Response mismatch for test case: {name}"

    mock_session.delete.assert_called_once()
    assert mock_session.delete.call_args[0][0] == expected_path


# -----------------------------------------------------------------------
# Network List Description Tests — network_list_description_test.go
# -----------------------------------------------------------------------


@pytest.mark.parametrize("name, test_case", [
    ("200 OK", {
        "with_error": None,
    }),
    ("500 internal server error", {
        "with_error": Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching NetworkListDescription",
            status_code=500,
        ),
    }),
])
def test_apsec_list_network_list_description(
    name, test_case, mock_session, mock_client,
):
    """Mirrors Go TestApsec_ListNetworkListDescription (lines 16-88).

    HTTP GET /network-list/v2/network-lists/{uniqueId} — with context headers.
    """
    params = GetNetworkListDescriptionRequest(unique_id="Test")
    expected_path = "/network-list/v2/network-lists/Test"

    if test_case["with_error"] is not None:
        mock_session.get.side_effect = test_case["with_error"]
        with pytest.raises(Error) as exc_info:
            mock_client.get_network_list_description(params)
        assert exc_info.value.is_equivalent(test_case["with_error"]), \
            f"Error mismatch for test case: {name}"
    else:
        resp_data = compact_json(load_fixture_bytes(
            "TestNetworkListDescription/NetworkListDescription.json",
        ))
        parsed = json.loads(resp_data)
        expected = from_dict(GetNetworkListDescriptionResponse, parsed)
        mock_session.get.return_value = (
            MagicMock(status_code=200), parsed,
        )
        result = mock_client.get_network_list_description(params)
        assert result == expected, \
            f"Response mismatch for test case: {name}"

    mock_session.get.assert_called_once()
    assert mock_session.get.call_args[0][0] == expected_path


@pytest.mark.parametrize("name, test_case", [
    ("200 OK", {
        "with_error": None,
    }),
    ("500 internal server error", {
        "with_error": Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching NetworkListDescription",
            status_code=500,
        ),
    }),
])
def test_appsec_get_network_list_description(
    name, test_case, mock_session, mock_client,
):
    """Mirrors Go TestAppSec_GetNetworkListDescription (lines 91-152).

    HTTP GET /network-list/v2/network-lists/{uniqueId} — background context.
    Error body does NOT include 'status' field.
    """
    params = GetNetworkListDescriptionRequest(unique_id="Test")
    expected_path = "/network-list/v2/network-lists/Test"

    if test_case["with_error"] is not None:
        mock_session.get.side_effect = test_case["with_error"]
        with pytest.raises(Error) as exc_info:
            mock_client.get_network_list_description(params)
        assert exc_info.value.is_equivalent(test_case["with_error"]), \
            f"Error mismatch for test case: {name}"
    else:
        resp_data = compact_json(load_fixture_bytes(
            "TestNetworkListDescription/NetworkListDescription.json",
        ))
        parsed = json.loads(resp_data)
        expected = from_dict(GetNetworkListDescriptionResponse, parsed)
        mock_session.get.return_value = (
            MagicMock(status_code=200), parsed,
        )
        result = mock_client.get_network_list_description(params)
        assert result == expected, \
            f"Response mismatch for test case: {name}"

    mock_session.get.assert_called_once()
    assert mock_session.get.call_args[0][0] == expected_path


@pytest.mark.parametrize("name, test_case", [
    ("200 Success", {
        "with_error": None,
    }),
    ("500 internal server error", {
        "with_error": Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error creating NetworkListDescription",
            status_code=500,
        ),
    }),
])
def test_appsec_update_network_list_description(
    name, test_case, mock_session, mock_client,
):
    """Mirrors Go TestAppSec_UpdateNetworkListDescription (lines 155-230).

    HTTP PUT /network-list/v2/network-lists/{uniqueId}/details
    Response status 201.
    """
    params = UpdateNetworkListDescriptionRequest(unique_id="Test")
    expected_path = "/network-list/v2/network-lists/Test/details"

    if test_case["with_error"] is not None:
        mock_session.put.side_effect = test_case["with_error"]
        with pytest.raises(Error) as exc_info:
            mock_client.update_network_list_description(params)
        assert exc_info.value.is_equivalent(test_case["with_error"]), \
            f"Error mismatch for test case: {name}"
    else:
        resp_data = compact_json(load_fixture_bytes(
            "TestNetworkListDescription/NetworkListDescription.json",
        ))
        parsed = json.loads(resp_data)
        expected = from_dict(
            UpdateNetworkListDescriptionResponse, parsed,
        )
        mock_session.put.return_value = (
            MagicMock(status_code=201), parsed,
        )
        result = mock_client.update_network_list_description(params)
        assert result == expected, \
            f"Response mismatch for test case: {name}"

    mock_session.put.assert_called_once()
    assert mock_session.put.call_args[0][0] == expected_path


# -----------------------------------------------------------------------
# Network List Subscription Tests — network_list_subscription_test.go
# -----------------------------------------------------------------------


@pytest.mark.parametrize("name, test_case", [
    ("200 OK", {
        "with_error": None,
    }),
    ("500 internal server error", {
        "with_error": Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching subscriptions",
            status_code=500,
        ),
    }),
])
def test_apsec_list_network_list_subscription(
    name, test_case, mock_session, mock_client,
):
    """Mirrors Go TestApsec_ListNetworkListSubscription (lines 16-88).

    HTTP GET /network-list/v2/notifications/subscriptions
    """
    params = GetNetworkListSubscriptionRequest()
    expected_path = "/network-list/v2/notifications/subscriptions"

    if test_case["with_error"] is not None:
        mock_session.get.side_effect = test_case["with_error"]
        with pytest.raises(Error) as exc_info:
            mock_client.get_network_list_subscription(params)
        assert exc_info.value.is_equivalent(test_case["with_error"]), \
            f"Error mismatch for test case: {name}"
    else:
        resp_data = compact_json(load_fixture_bytes(
            "TestNetworkListSubscription/NetworkListSubscription.json",
        ))
        parsed = json.loads(resp_data)
        expected = from_dict(
            GetNetworkListSubscriptionResponse, parsed,
        )
        mock_session.get.return_value = (
            MagicMock(status_code=200), parsed,
        )
        result = mock_client.get_network_list_subscription(params)
        assert result == expected, \
            f"Response mismatch for test case: {name}"

    mock_session.get.assert_called_once()
    assert mock_session.get.call_args[0][0] == expected_path


@pytest.mark.parametrize("name, test_case", [
    ("200 OK", {
        "with_error": None,
    }),
    ("500 internal server error", {
        "with_error": Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching subscriptions",
            status_code=500,
        ),
    }),
])
def test_appsec_get_network_list_subscription(
    name, test_case, mock_session, mock_client,
):
    """Mirrors Go TestAppSec_GetNetworkListSubscription (lines 91-152).

    HTTP GET /network-list/v2/notifications/subscriptions
    Error body does NOT include 'status' field.
    """
    params = GetNetworkListSubscriptionRequest()
    expected_path = "/network-list/v2/notifications/subscriptions"

    if test_case["with_error"] is not None:
        mock_session.get.side_effect = test_case["with_error"]
        with pytest.raises(Error) as exc_info:
            mock_client.get_network_list_subscription(params)
        assert exc_info.value.is_equivalent(test_case["with_error"]), \
            f"Error mismatch for test case: {name}"
    else:
        resp_data = compact_json(load_fixture_bytes(
            "TestNetworkListSubscription/NetworkListSubscription.json",
        ))
        parsed = json.loads(resp_data)
        expected = from_dict(
            GetNetworkListSubscriptionResponse, parsed,
        )
        mock_session.get.return_value = (
            MagicMock(status_code=200), parsed,
        )
        result = mock_client.get_network_list_subscription(params)
        assert result == expected, \
            f"Response mismatch for test case: {name}"

    mock_session.get.assert_called_once()
    assert mock_session.get.call_args[0][0] == expected_path


@pytest.mark.parametrize("name, test_case", [
    ("200 Success", {
        "with_error": None,
    }),
    ("500 internal server error", {
        "with_error": Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error creating subscription",
            status_code=500,
        ),
    }),
])
def test_appsec_update_network_list_subscription(
    name, test_case, mock_session, mock_client,
):
    """Mirrors Go TestAppSec_UpdateNetworkListSubscription (lines 155-230).

    HTTP POST /network-list/v2/notifications/subscribe
    Response status 201.
    """
    params = UpdateNetworkListSubscriptionRequest()
    expected_path = "/network-list/v2/notifications/subscribe"

    if test_case["with_error"] is not None:
        mock_session.post.side_effect = test_case["with_error"]
        with pytest.raises(Error) as exc_info:
            mock_client.update_network_list_subscription(params)
        assert exc_info.value.is_equivalent(test_case["with_error"]), \
            f"Error mismatch for test case: {name}"
    else:
        resp_data = compact_json(load_fixture_bytes(
            "TestNetworkListSubscription/NetworkListSubscription.json",
        ))
        parsed = json.loads(resp_data)
        expected = from_dict(
            UpdateNetworkListSubscriptionResponse, parsed,
        )
        mock_session.post.return_value = (
            MagicMock(status_code=201), parsed,
        )
        result = mock_client.update_network_list_subscription(params)
        assert result == expected, \
            f"Response mismatch for test case: {name}"

    mock_session.post.assert_called_once()
    assert mock_session.post.call_args[0][0] == expected_path


# -----------------------------------------------------------------------
# Error Parsing Tests — errors_test.go
# -----------------------------------------------------------------------


@pytest.mark.parametrize("name, test_case", [
    ("valid response, status code 500", {
        "response_body": '{"type":"a","title":"b","detail":"c"}',
        "status_code": 500,
        "expected": Error(
            type="a", title="b", detail="c", status_code=500,
        ),
    }),
    ("invalid response body, assign status code", {
        "response_body": "test",
        "status_code": 500,
        "expected": Error(
            title="Failed to unmarshal error body. Network Lists API "
                  "failed. Check details for more information.",
            detail="test",
            status_code=500,
        ),
    }),
])
def test_new_error(name, test_case, mock_client):
    """Mirrors Go TestNewError (errors_test.go lines 15-68).

    Tests _parse_error with both valid JSON and non-JSON response bodies.
    """
    response = create_mock_response(
        test_case["status_code"], test_case["response_body"],
    )
    # pylint: disable=protected-access
    result = mock_client._parse_error(response)
    assert result == test_case["expected"], \
        f"Error mismatch for test case: {name}"


@pytest.mark.parametrize("name, test_case", [
    ("API failure with HTML response", {
        "response_body": "<HTML><HEAD>...</HEAD><BODY>...</BODY></HTML>",
        "status_code": 503,
        "expected": Error(
            type="",
            title="Failed to unmarshal error body. Network Lists API "
                  "failed. Check details for more information.",
            detail="<HTML><HEAD>...</HEAD><BODY>...</BODY></HTML>",
            status_code=503,
        ),
    }),
    ("API failure with plain text response", {
        "response_body": (
            "Your request did not succeed as this operation has reached"
            "  the limit for your account. Please try after "
            "2024-01-16T15:20:55.945Z"
        ),
        "status_code": 503,
        "expected": Error(
            type="",
            title="Failed to unmarshal error body. Network Lists API "
                  "failed. Check details for more information.",
            detail=(
                "Your request did not succeed as this operation has reached"
                "  the limit for your account. Please try after "
                "2024-01-16T15:20:55.945Z"
            ),
            status_code=503,
        ),
    }),
    ("API failure with XML response", {
        "response_body": '<Root><Item id="1" name="Example" /></Root>',
        "status_code": 503,
        "expected": Error(
            type="",
            title="Failed to unmarshal error body. Network Lists API "
                  "failed. Check details for more information.",
            detail='<Root><Item id="1" name="Example" /></Root>',
            status_code=503,
        ),
    }),
])
def test_json_error_unmarshalling(name, test_case, mock_client):
    """Mirrors Go TestJsonErrorUnmarshalling (errors_test.go lines 70-131).

    Tests _parse_error with non-JSON bodies: HTML, plain text, and XML.
    All produce the unmarshal failure title with the raw body as detail.
    """
    response = create_mock_response(
        test_case["status_code"], test_case["response_body"],
    )
    # pylint: disable=protected-access
    result = mock_client._parse_error(response)
    assert result == test_case["expected"], \
        f"Error mismatch for test case: {name}"
