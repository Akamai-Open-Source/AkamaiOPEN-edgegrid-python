"""Unit tests for the Client Lists API client.

Mirrors ALL Go test scenarios from:
- pkg/clientlists/clientlists_test.go  (TestClient — 2 scenarios)
- pkg/clientlists/errors_test.go       (TestJsonErrorsUnmarshalling — 3 scenarios)
- pkg/clientlists/client_list_test.go  (8 test functions — ~30 scenarios)
- pkg/clientlists/client_list_activation_test.go (4 test functions — ~14 scenarios)

Uses ``@pytest.mark.parametrize`` for table-driven tests and
``unittest.mock`` for HTTP mocking.  Response body values are copied
VERBATIM from Go test fixtures per AAP §0.7.1.
"""
# pylint: disable=protected-access,too-many-lines

import json

import pytest

from akamai.edgegrid.clientlists import (
    Client,
    Error,
    ErrStructValidation,
    parse_error_response,
    GetClientListsRequest,
    GetClientListsResponse,
    GetClientListRequest,
    GetClientListResponse,
    CreateClientListRequest,
    CreateClientListResponse,
    UpdateClientListRequest,
    UpdateClientListResponse,
    UpdateClientListItemsRequest,
    UpdateClientListItemsResponse,
    DeleteClientListRequest,
    GetClientListItemsRequest,
    GetClientListItemsResponse,
    GetActivationRequest,
    GetActivationResponse,
    GetActivationStatusRequest,
    GetActivationStatusResponse,
    CreateActivationRequest,
    CreateActivationResponse,
    CreateDeactivationRequest,
    CreateDeactivationResponse,
    IP,
    GEO,
    ACTIVATE,
    DEACTIVATE,
    PRODUCTION,
    PENDING_ACTIVATION,
    PENDING_DEACTIVATION,
    ListItemContent,
    ListItemPayload,
    ClientList,
)
from akamai.edgegrid.clientlists.test.conftest import create_mock_response


# ===================================================================
# TestClient — mirrors Go TestClient (clientlists_test.go)
# ===================================================================


class TestClient:  # pylint: disable=too-few-public-methods
    """Test Client constructor — mirrors Go TestClient (clientlists_test.go).

    Verifies the client can be instantiated with a mock session.
    Go has 2 scenarios: 'no options provided' and 'dummy option'.
    Python does not have the Go Option pattern, so both scenarios simply
    instantiate the client and confirm it is not None.
    """

    @pytest.mark.parametrize("name", [
        "no options provided",
        "dummy option",
    ])
    def test_client(self, name, mock_session):  # pylint: disable=unused-argument
        """Client can be instantiated."""
        client = Client(mock_session)
        assert client is not None


# ===================================================================
# TestJsonErrorsUnmarshalling — mirrors Go TestJsonErrorsUnmarshalling
# (errors_test.go)
# ===================================================================


class TestJsonErrorsUnmarshalling:  # pylint: disable=too-few-public-methods
    """Test error response parsing — mirrors Go TestJsonErrorsUnmarshalling.

    Verifies that parse_error_response handles non-JSON response bodies
    (HTML, plain text, XML) by setting the title to the unmarshal failure
    message and the detail to the raw body content.
    """

    @pytest.mark.parametrize("name, body, expected_detail", [
        (
            "API failure with HTML response",
            "<HTML><HEAD>...</HEAD><BODY>...</BODY></HTML>",
            "<HTML><HEAD>...</HEAD><BODY>...</BODY></HTML>",
        ),
        (
            "API failure with plain text response",
            "Your request did not succeed as this operation has reached "
            " the limit for your account. Please try after "
            "2024-01-16T15:20:55.945Z",
            "Your request did not succeed as this operation has reached "
            " the limit for your account. Please try after "
            "2024-01-16T15:20:55.945Z",
        ),
        (
            "API failure with XML response",
            '<Root><Item id="1" name="Example" /></Root>',
            '<Root><Item id="1" name="Example" /></Root>',
        ),
    ])
    def test_json_errors_unmarshalling(  # pylint: disable=unused-argument
        self, name, body, expected_detail,
    ):
        """Non-JSON bodies produce unmarshal error with raw detail."""
        mock_resp = create_mock_response(
            status_code=503,
            body=body,
        )
        result = parse_error_response(mock_resp)
        assert result.type == ""
        assert result.title == (
            "Failed to unmarshal error body. Client Lists API failed. "
            "Check details for more information."
        )
        assert result.detail == expected_detail
        assert result.status_code == 503


# ===================================================================
# TestGetClientLists — mirrors Go TestGetClientLists
# (client_list_test.go lines 18-329)
# ===================================================================

# Verbatim response body for GetClientLists 200 OK
_GET_CLIENT_LISTS_200_BODY = """{
    "content": [
        {
            "createDate": "2023-06-06T15:58:39.225+00:00",
            "createdBy": "ccare2",
            "deprecated": false,
            "filePrefix": "CL",
            "itemsCount": 1,
            "listId": "91596_AUDITLOGSTESTLIST",
            "listType": "CL",
            "name": "AUDIT LOGS - TEST LIST",
            "productionActivationStatus": "INACTIVE",
            "readOnly": false,
            "shared": false,
            "stagingActivationStatus": "INACTIVE",
            "tags": ["green"],
            "type": "IP",
            "updateDate": "2023-06-06T15:58:39.225+00:00",
            "updatedBy": "ccare2",
            "version": 1
        },
        {
            "createDate": "2022-11-10T14:42:04.857+00:00",
            "createdBy": "ccare2",
            "deprecated": false,
            "filePrefix": "CL",
            "itemsCount": 2,
            "listId": "85988_ANTHONYGEOLISTOPEN",
            "listType": "CL",
            "name": "AnthonyGeoListOPEN",
            "notes": "This is another Geo client list for Nov 11",
            "productionActivationStatus": "INACTIVE",
            "readOnly": false,
            "shared": false,
            "stagingActivationStatus": "INACTIVE",
            "tags": [],
            "type": "GEO",
            "updateDate": "2023-05-11T15:30:10.224+00:00",
            "updatedBy": "ccare2",
            "version": 66
        },
        {
            "createDate": "2022-10-17T13:39:25.319+00:00",
            "createdBy": "ccare2",
            "deprecated": false,
            "filePrefix": "CL",
            "itemsCount": 0,
            "listId": "85552_ANTHONYFILEHASHLIST",
            "listType": "CL",
            "name": "File Hash List",
            "notes": "This is another File hash client list for Oct 17",
            "productionActivationStatus": "PENDING_ACTIVATION",
            "readOnly": false,
            "shared": false,
            "stagingActivationStatus": "INACTIVE",
            "tags": ["blue"],
            "type": "TLS_FINGERPRINT",
            "updateDate": "2023-06-05T06:56:19.004+00:00",
            "updatedBy": "ccare2",
            "version": 343
        }
    ]
}"""

# Verbatim response body for GetClientLists 200 OK filtered by name + type
_GET_CLIENT_LISTS_FILTERED_BODY = """{
    "content": [
        {
            "createDate": "2023-06-06T15:58:39.225+00:00",
            "createdBy": "ccare2",
            "deprecated": false,
            "filePrefix": "CL",
            "itemsCount": 1,
            "listId": "91596_AUDITLOGSTESTLIST",
            "listType": "CL",
            "name": "AUDIT LOGS - TEST LIST",
            "productionActivationStatus": "INACTIVE",
            "readOnly": false,
            "shared": false,
            "stagingActivationStatus": "INACTIVE",
            "tags": ["green"],
            "type": "IP",
            "updateDate": "2023-06-06T15:58:39.225+00:00",
            "updatedBy": "ccare2",
            "version": 1
        }
    ]
}"""

# Verbatim response body for GetClientLists 200 OK with search + query params
_GET_CLIENT_LISTS_SEARCH_BODY = """{
    "content": [
        {
            "createDate": "2023-06-06T15:58:39.225+00:00",
            "createdBy": "ccare2",
            "deprecated": false,
            "filePrefix": "CL",
            "itemsCount": 1,
            "listId": "91596_AUDITLOGSTESTLIST",
            "listType": "CL",
            "name": "AUDIT LOGS - TEST LIST",
            "productionActivationStatus": "INACTIVE",
            "readOnly": false,
            "shared": false,
            "stagingActivationStatus": "INACTIVE",
            "tags": ["green"],
            "type": "IP",
            "updateDate": "2023-06-06T15:58:39.225+00:00",
            "updatedBy": "ccare2",
            "version": 1,
            "items": []
        }
    ]
}"""


class TestGetClientLists:
    """Test GetClientLists — mirrors Go TestGetClientLists.

    4 scenarios: 200 OK, 200 filtered name+type, 200 search+params, 500.
    """

    def test_200_ok(self, mock_client):
        """GetClientLists returns full list on 200 OK."""
        body = _GET_CLIENT_LISTS_200_BODY
        mock_response = create_mock_response(status_code=200, body=body)
        mock_client._session.exec.return_value = (
            mock_response, json.loads(body),
        )

        result = mock_client.get_client_lists(GetClientListsRequest())

        expected = GetClientListsResponse(
            content=[
                ClientList(
                    name="AUDIT LOGS - TEST LIST",
                    type="IP",
                    tags=["green"],
                    list_id="91596_AUDITLOGSTESTLIST",
                    version=1,
                    items_count=1,
                    create_date="2023-06-06T15:58:39.225+00:00",
                    created_by="ccare2",
                    update_date="2023-06-06T15:58:39.225+00:00",
                    updated_by="ccare2",
                    production_activation_status="INACTIVE",
                    staging_activation_status="INACTIVE",
                    list_type="CL",
                    shared=False,
                    read_only=False,
                    deprecated=False,
                ),
                ClientList(
                    name="AnthonyGeoListOPEN",
                    type="GEO",
                    notes="This is another Geo client list for Nov 11",
                    tags=[],
                    list_id="85988_ANTHONYGEOLISTOPEN",
                    version=66,
                    items_count=2,
                    create_date="2022-11-10T14:42:04.857+00:00",
                    created_by="ccare2",
                    update_date="2023-05-11T15:30:10.224+00:00",
                    updated_by="ccare2",
                    production_activation_status="INACTIVE",
                    staging_activation_status="INACTIVE",
                    list_type="CL",
                    shared=False,
                    read_only=False,
                    deprecated=False,
                ),
                ClientList(
                    name="File Hash List",
                    type="TLS_FINGERPRINT",
                    notes=(
                        "This is another File hash client list for Oct 17"
                    ),
                    tags=["blue"],
                    list_id="85552_ANTHONYFILEHASHLIST",
                    version=343,
                    items_count=0,
                    create_date="2022-10-17T13:39:25.319+00:00",
                    created_by="ccare2",
                    update_date="2023-06-05T06:56:19.004+00:00",
                    updated_by="ccare2",
                    production_activation_status="PENDING_ACTIVATION",
                    staging_activation_status="INACTIVE",
                    list_type="CL",
                    shared=False,
                    read_only=False,
                    deprecated=False,
                ),
            ],
        )
        assert result == expected

        # Verify request
        mock_client._session.exec.assert_called_once()
        call_args, _call_kwargs = mock_client._session.exec.call_args
        assert call_args[0] == "GET"
        assert call_args[1] == "/client-list/v1/lists"

    def test_200_ok_filtered_by_name_and_type(self, mock_client):
        """GetClientLists returns filtered results by name and type."""
        body = _GET_CLIENT_LISTS_FILTERED_BODY
        mock_response = create_mock_response(status_code=200, body=body)
        mock_client._session.exec.return_value = (
            mock_response, json.loads(body),
        )

        result = mock_client.get_client_lists(
            GetClientListsRequest(
                name="list name",
                type=[IP, GEO],
            ),
        )

        assert len(result.content) == 1
        assert result.content[0].list_id == "91596_AUDITLOGSTESTLIST"

        # Verify URL has correct query params
        mock_client._session.exec.assert_called_once()
        call_args, _ = mock_client._session.exec.call_args
        uri = call_args[1]
        assert "name=list+name" in uri
        assert "type=IP" in uri
        assert "type=GEO" in uri

    def test_200_ok_filtered_by_search_and_params(self, mock_client):
        """GetClientLists returns filtered results by search and params."""
        body = _GET_CLIENT_LISTS_SEARCH_BODY
        mock_response = create_mock_response(status_code=200, body=body)
        mock_client._session.exec.return_value = (
            mock_response, json.loads(body),
        )

        result = mock_client.get_client_lists(
            GetClientListsRequest(
                search="search term",
                include_items=True,
                include_deprecated=True,
                include_network_list=True,
                page=0,
                page_size=2,
                sort=["updatedBy:desc", "value:desc"],
            ),
        )

        assert len(result.content) == 1
        assert result.content[0].items == []

        # Verify URL has all expected query params
        mock_client._session.exec.assert_called_once()
        call_args, _ = mock_client._session.exec.call_args
        uri = call_args[1]
        assert "search=search+term" in uri
        assert "includeItems=true" in uri
        assert "includeDeprecated=true" in uri
        assert "includeNetworkList=true" in uri
        assert "page=0" in uri
        assert "pageSize=2" in uri
        assert "sort=updatedBy%3Adesc" in uri
        assert "sort=value%3Adesc" in uri

    def test_500_internal_server_error(self, mock_client):
        """GetClientLists raises Error on 500."""
        error_body = json.dumps({
            "type": "internal_error",
            "title": "Internal Server Error",
            "detail": "Error fetching client lists",
            "status": 500,
        })
        mock_response = create_mock_response(
            status_code=500, body=error_body,
        )
        mock_client._session.exec.return_value = (mock_response, None)

        with pytest.raises(Error) as exc_info:
            mock_client.get_client_lists(GetClientListsRequest())

        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error fetching client lists"
        assert err.status_code == 500


# ===================================================================
# TestGetClientList — mirrors Go TestGetClientList
# (client_list_test.go lines 331-509)
# ===================================================================

# Verbatim response body for GetClientList 200 OK
_GET_CLIENT_LIST_200_BODY = """{
    "createDate": "2023-06-06T15:58:39.225+00:00",
    "createdBy": "ccare2",
    "deprecated": false,
    "filePrefix": "CL",
    "itemsCount": 1,
    "listId": "12_AB",
    "listType": "CL",
    "name": "AUDIT LOGS - TEST LIST",
    "productionActivationStatus": "INACTIVE",
    "readOnly": false,
    "shared": false,
    "stagingActivationStatus": "INACTIVE",
    "productionActiveVersion": 2,
    "stagingActiveVersion": 2,
    "tags": ["green"],
    "type": "IP",
    "updateDate": "2023-06-06T15:58:39.225+00:00",
    "updatedBy": "ccare2",
    "version": 1,
    "groupId": 12,
    "groupName": "123_ABC",
    "contractId" :"12_CO",
    "items": [
        {
            "createDate": "2022-07-12T20:14:29.189+00:00",
            "createdBy": "ccare2",
            "createdVersion": 9,
            "productionStatus": "INACTIVE",
            "stagingStatus": "PENDING_ACTIVATION",
            "tags": [],
            "type": "IP",
            "updateDate": "2022-07-12T20:14:29.189+00:00",
            "updatedBy": "ccare2",
            "value": "7d0:1:0::0/64"
        },
        {
            "createDate": "2022-07-12T20:14:29.189+00:00",
            "createdBy": "ccare2",
            "createdVersion": 9,
            "description": "Item with description, tags, expiration date",
            "expirationDate": "2030-12-31T12:40:00.000+00:00",
            "productionStatus": "INACTIVE",
            "stagingStatus": "PENDING_ACTIVATION",
            "tags": [
                "red",
                "green",
                "blue"
            ],
            "type": "IP",
            "updateDate": "2022-07-12T20:14:29.189+00:00",
            "updatedBy": "ccare2",
            "value": "7d0:1:1::0/64"
        }
    ]
}"""


class TestGetClientList:
    """Test GetClientList — mirrors Go TestGetClientList.

    3 scenarios: 200 OK, 500 error, validation error.
    """

    def test_200_ok(self, mock_client):
        """GetClientList returns list details on 200 OK."""
        body = _GET_CLIENT_LIST_200_BODY
        mock_response = create_mock_response(status_code=200, body=body)
        mock_client._session.exec.return_value = (
            mock_response, json.loads(body),
        )

        result = mock_client.get_client_list(
            GetClientListRequest(list_id="12_AB", include_items=True),
        )

        expected = GetClientListResponse(
            name="AUDIT LOGS - TEST LIST",
            type="IP",
            tags=["green"],
            list_id="12_AB",
            version=1,
            items_count=1,
            create_date="2023-06-06T15:58:39.225+00:00",
            created_by="ccare2",
            update_date="2023-06-06T15:58:39.225+00:00",
            updated_by="ccare2",
            production_activation_status="INACTIVE",
            staging_activation_status="INACTIVE",
            production_active_version=2,
            staging_active_version=2,
            list_type="CL",
            shared=False,
            read_only=False,
            deprecated=False,
            contract_id="12_CO",
            group_id=12,
            group_name="123_ABC",
            items=[
                ListItemContent(
                    create_date="2022-07-12T20:14:29.189+00:00",
                    created_by="ccare2",
                    created_version=9,
                    production_status="INACTIVE",
                    staging_status="PENDING_ACTIVATION",
                    tags=[],
                    type="IP",
                    update_date="2022-07-12T20:14:29.189+00:00",
                    updated_by="ccare2",
                    value="7d0:1:0::0/64",
                ),
                ListItemContent(
                    create_date="2022-07-12T20:14:29.189+00:00",
                    created_by="ccare2",
                    created_version=9,
                    production_status="INACTIVE",
                    staging_status="PENDING_ACTIVATION",
                    tags=["red", "green", "blue"],
                    description=(
                        "Item with description, tags, expiration date"
                    ),
                    expiration_date="2030-12-31T12:40:00.000+00:00",
                    type="IP",
                    update_date="2022-07-12T20:14:29.189+00:00",
                    updated_by="ccare2",
                    value="7d0:1:1::0/64",
                ),
            ],
        )
        assert result == expected

        # Verify request
        mock_client._session.exec.assert_called_once()
        call_args, _ = mock_client._session.exec.call_args
        assert call_args[0] == "GET"
        assert call_args[1] == "/client-list/v1/lists/12_AB?includeItems=true"

    def test_500_internal_server_error(self, mock_client):
        """GetClientList raises Error on 500."""
        error_body = json.dumps({
            "type": "internal_error",
            "title": "Internal Server Error",
            "detail": "Error fetching client lists",
            "status": 500,
        })
        mock_response = create_mock_response(
            status_code=500, body=error_body,
        )
        mock_client._session.exec.return_value = (mock_response, None)

        with pytest.raises(Error) as exc_info:
            mock_client.get_client_list(
                GetClientListRequest(list_id="12_AB", include_items=True),
            )

        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error fetching client lists"
        assert err.status_code == 500

    def test_validation_error(self, mock_client):
        """GetClientList raises ErrStructValidation for empty ListID."""
        with pytest.raises(ErrStructValidation):
            mock_client.get_client_list(GetClientListRequest())

        mock_client._session.exec.assert_not_called()


# ===================================================================
# TestUpdateClientList — mirrors Go TestUpdateClientList
# (client_list_test.go lines 511-640)
# ===================================================================

# Verbatim response body for UpdateClientList 200 OK
_UPDATE_CLIENT_LIST_200_BODY = """{
    "contractId": "M-2CF0QRI",
    "createDate": "2023-04-03T15:50:34.074+00:00",
    "createdBy": "ccare2",
    "deprecated": false,
    "filePrefix": "CL",
    "groupName": "Kona QA16-M-2CF0QRI",
    "groupId": 12,
    "itemsCount": 51,
    "listId": "12_12",
    "listType": "CL",
    "name": "Some New Name",
    "tags": [ "red"],
    "notes": "Updating list notes",
    "productionActivationStatus": "INACTIVE",
    "readOnly": false,
    "shared": false,
    "stagingActivationStatus": "INACTIVE",
    "productionActiveVersion":    2,
    "stagingActiveVersion":       2,
    "type": "IP",
    "updateDate": "2023-06-15T20:28:09.047+00:00",
    "updatedBy": "ccare2",
    "version": 75
}"""


class TestUpdateClientList:
    """Test UpdateClientList — mirrors Go TestUpdateClientList.

    3 scenarios: 200 OK, 500 error, validation error.
    """

    def test_200_ok(self, mock_client):
        """UpdateClientList returns updated list on 200 OK."""
        body = _UPDATE_CLIENT_LIST_200_BODY
        mock_response = create_mock_response(status_code=200, body=body)
        mock_client._session.exec.return_value = (
            mock_response, json.loads(body),
        )

        result = mock_client.update_client_list(
            UpdateClientListRequest(
                name="Some New Name",
                tags=["red"],
                notes="Updating list notes",
                list_id="12_12",
            ),
        )

        expected = UpdateClientListResponse(
            name="Some New Name",
            type="IP",
            notes="Updating list notes",
            tags=["red"],
            list_id="12_12",
            version=75,
            items_count=51,
            create_date="2023-04-03T15:50:34.074+00:00",
            created_by="ccare2",
            update_date="2023-06-15T20:28:09.047+00:00",
            updated_by="ccare2",
            production_activation_status="INACTIVE",
            staging_activation_status="INACTIVE",
            production_active_version=2,
            staging_active_version=2,
            list_type="CL",
            shared=False,
            read_only=False,
            deprecated=False,
            contract_id="M-2CF0QRI",
            group_name="Kona QA16-M-2CF0QRI",
            group_id=12,
        )
        assert result == expected

        # Verify request method and path
        mock_client._session.exec.assert_called_once()
        call_args, call_kwargs = mock_client._session.exec.call_args
        assert call_args[0] == "PUT"
        assert call_args[1] == "/client-list/v1/lists/12_12"

        # Verify request body
        req_body = call_kwargs.get(
            "body", call_args[2] if len(call_args) > 2 else None,
        )
        expected_body = {
            "name": "Some New Name",
            "notes": "Updating list notes",
            "tags": ["red"],
        }
        assert req_body == expected_body

    def test_500_internal_server_error(self, mock_client):
        """UpdateClientList raises Error on 500."""
        error_body = json.dumps({
            "type": "internal_error",
            "title": "Internal Server Error",
            "detail": "Error fetching client lists",
            "status": 500,
        })
        mock_response = create_mock_response(
            status_code=500, body=error_body,
        )
        mock_client._session.exec.return_value = (mock_response, None)

        with pytest.raises(Error) as exc_info:
            mock_client.update_client_list(
                UpdateClientListRequest(
                    name="Some New Name",
                    tags=["red"],
                    notes="Updating list notes",
                    list_id="12_12",
                ),
            )

        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error fetching client lists"
        assert err.status_code == 500

    def test_validation_error(self, mock_client):
        """UpdateClientList raises ErrStructValidation for empty ListID."""
        with pytest.raises(ErrStructValidation):
            mock_client.update_client_list(UpdateClientListRequest())

        mock_client._session.exec.assert_not_called()


# ===================================================================
# TestUpdateClientListItems — mirrors Go TestUpdateClientListItems
# (client_list_test.go lines 641-820)
# ===================================================================

# Verbatim response body for UpdateClientListItems 200 OK
_UPDATE_CLIENT_LIST_ITEMS_200_BODY = """{
    "appended": [
        {
            "createDate": "2023-06-15T20:46:30.780+00:00",
            "createdBy": "ccare2",
            "createdVersion": 76,
            "description": "Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley",
            "expirationDate": "2026-12-26T01:32:08.375+00:00",
            "productionStatus": "INACTIVE",
            "stagingStatus": "INACTIVE",
            "tags": [
                "new tag"
            ],
            "type": "IP",
            "updateDate": "2023-06-15T20:46:30.780+00:00",
            "updatedBy": "ccare2",
            "value": "1.1.1.75"
        }
    ],
    "deleted": [
        {
            "value": "1.1.1.39"
        }
    ],
    "updated": [
        {
            "createDate": "2023-04-28T19:34:00.906+00:00",
            "createdBy": "ccare2",
            "createdVersion": 54,
            "description": "remove exp date and tags",
            "productionStatus": "INACTIVE",
            "stagingStatus": "INACTIVE",
            "tags": [
                "t1"
            ],
            "type": "IP",
            "updateDate": "2023-06-15T20:46:30.765+00:00",
            "updatedBy": "ccare2",
            "value": "1.1.1.45"
        }
    ]
}"""


class TestUpdateClientListItems:
    """Test UpdateClientListItems — mirrors Go TestUpdateClientListItems.

    3 scenarios: 200 OK, 500 error, validation error.
    """

    def test_200_ok(self, mock_client):
        """UpdateClientListItems returns appended/updated/deleted items."""
        body = _UPDATE_CLIENT_LIST_ITEMS_200_BODY
        mock_response = create_mock_response(status_code=200, body=body)
        mock_client._session.exec.return_value = (
            mock_response, json.loads(body),
        )

        result = mock_client.update_client_list_items(
            UpdateClientListItemsRequest(
                list_id="12_12",
                append=[
                    ListItemPayload(
                        description=(
                            "Lorem Ipsum has been the industry's "
                            "standard dummy text ever since the "
                            "1500s..."
                        ),
                        expiration_date="2026-12-26T01:32:08.375+00:00",
                        value="1.1.1.72",
                    ),
                ],
                update=[
                    ListItemPayload(
                        description="remove exp date and tags",
                        expiration_date="",
                        tags=["t"],
                        value="1.1.1.45",
                    ),
                    ListItemPayload(
                        expiration_date="2028-11-26T17:32:08.375+00:00",
                        value="1.1.1.33",
                    ),
                ],
                delete=[
                    ListItemPayload(value="1.1.1.38"),
                ],
            ),
        )

        expected = UpdateClientListItemsResponse(
            appended=[
                ListItemContent(
                    description=(
                        "Lorem Ipsum has been the industry's standard "
                        "dummy text ever since the 1500s, when an "
                        "unknown printer took a galley"
                    ),
                    expiration_date="2026-12-26T01:32:08.375+00:00",
                    tags=["new tag"],
                    value="1.1.1.75",
                    create_date="2023-06-15T20:46:30.780+00:00",
                    created_by="ccare2",
                    created_version=76,
                    production_status="INACTIVE",
                    staging_status="INACTIVE",
                    type="IP",
                    update_date="2023-06-15T20:46:30.780+00:00",
                    updated_by="ccare2",
                ),
            ],
            deleted=[
                ListItemContent(value="1.1.1.39"),
            ],
            updated=[
                ListItemContent(
                    description="remove exp date and tags",
                    tags=["t1"],
                    value="1.1.1.45",
                    create_date="2023-04-28T19:34:00.906+00:00",
                    created_by="ccare2",
                    created_version=54,
                    production_status="INACTIVE",
                    staging_status="INACTIVE",
                    type="IP",
                    update_date="2023-06-15T20:46:30.765+00:00",
                    updated_by="ccare2",
                ),
            ],
        )
        assert result == expected

        # Verify request method and path
        mock_client._session.exec.assert_called_once()
        call_args, _ = mock_client._session.exec.call_args
        assert call_args[0] == "POST"
        assert call_args[1] == "/client-list/v1/lists/12_12/items"

    def test_500_internal_server_error(self, mock_client):
        """UpdateClientListItems raises Error on 500."""
        error_body = json.dumps({
            "type": "internal_error",
            "title": "Internal Server Error",
            "detail": "Error fetching client lists",
            "status": 500,
        })
        mock_response = create_mock_response(
            status_code=500, body=error_body,
        )
        mock_client._session.exec.return_value = (mock_response, None)

        with pytest.raises(Error) as exc_info:
            mock_client.update_client_list_items(
                UpdateClientListItemsRequest(
                    list_id="12_12",
                    append=[
                        ListItemPayload(
                            description=(
                                "Lorem Ipsum has been the industry's "
                                "standard dummy text ever since the "
                                "1500s..."
                            ),
                            expiration_date=(
                                "2026-12-26T01:32:08.375+00:00"
                            ),
                            value="1.1.1.72",
                        ),
                    ],
                    update=[
                        ListItemPayload(
                            description="remove exp date and tags",
                            expiration_date="",
                            tags=["t"],
                            value="1.1.1.45",
                        ),
                        ListItemPayload(
                            expiration_date=(
                                "2028-11-26T17:32:08.375+00:00"
                            ),
                            value="1.1.1.33",
                        ),
                    ],
                    delete=[ListItemPayload(value="1.1.1.38")],
                ),
            )

        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error fetching client lists"
        assert err.status_code == 500

    def test_validation_error(self, mock_client):
        """UpdateClientListItems raises ErrStructValidation for empty."""
        with pytest.raises(ErrStructValidation):
            mock_client.update_client_list_items(
                UpdateClientListItemsRequest(),
            )

        mock_client._session.exec.assert_not_called()


# ===================================================================
# TestCreateClientLists — mirrors Go TestCreateClientLists
# (client_list_test.go lines 822-950)
# ===================================================================

# Verbatim response body for CreateClientList 201 Created
_CREATE_CLIENT_LIST_201_BODY = """{
    "listId": "123_ABC",
    "name": "TEST LIST",
    "type": "IP",
    "notes": "Some notes",
    "tags": [
        "red",
        "green"
    ],
    "contractId": "M-2CF0QRI",
    "groupName": "Group A",
    "groupId": 12,
    "items": [
        {
            "value": "1.1.1.1",
            "description": "",
            "tags": [],
            "expirationDate": "2026-12-26T01:32:08.375+00:00"
        }
    ]
}"""


class TestCreateClientLists:
    """Test CreateClientList — mirrors Go TestCreateClientLists.

    3 scenarios: 201 Created, 500 error, validation error.
    """

    def test_201_created(self, mock_client):
        """CreateClientList returns created list on 201 Created."""
        body = _CREATE_CLIENT_LIST_201_BODY
        mock_response = create_mock_response(status_code=201, body=body)
        mock_client._session.exec.return_value = (
            mock_response, json.loads(body),
        )

        result = mock_client.create_client_list(
            CreateClientListRequest(
                name="TEST LIST",
                type="IP",
                notes="Some notes",
                tags=["red", "green"],
                contract_id="M-2CF0QRI",
                group_id=112524,
                items=[
                    ListItemPayload(
                        value="1.1.1.1",
                        description="some description",
                        tags=[],
                        expiration_date=(
                            "2026-12-26T01:32:08.375+00:00"
                        ),
                    ),
                ],
            ),
        )

        expected = CreateClientListResponse(
            list_id="123_ABC",
            name="TEST LIST",
            type="IP",
            notes="Some notes",
            tags=["red", "green"],
            contract_id="M-2CF0QRI",
            group_name="Group A",
            group_id=12,
            items=[
                ListItemContent(
                    value="1.1.1.1",
                    description="",
                    tags=[],
                    expiration_date=(
                        "2026-12-26T01:32:08.375+00:00"
                    ),
                ),
            ],
        )
        assert result == expected

        # Verify request
        mock_client._session.exec.assert_called_once()
        call_args, call_kwargs = mock_client._session.exec.call_args
        assert call_args[0] == "POST"
        assert call_args[1] == "/client-list/v1/lists"

        # Verify request body
        req_body = call_kwargs.get(
            "body", call_args[2] if len(call_args) > 2 else None,
        )
        expected_body = json.loads(
            '{"contractId":"M-2CF0QRI","groupId":112524,'
            '"name":"TEST LIST","type":"IP",'
            '"notes":"Some notes","tags":["red","green"],'
            '"items":[{"value":"1.1.1.1","tags":[],'
            '"description":"some description",'
            '"expirationDate":"2026-12-26T01:32:08.375+00:00"}]}',
        )
        assert req_body == expected_body

    def test_500_internal_server_error(self, mock_client):
        """CreateClientList raises Error on 500."""
        error_body = json.dumps({
            "type": "internal_error",
            "title": "Internal Server Error",
            "detail": "Error fetching client lists",
            "status": 500,
        })
        mock_response = create_mock_response(
            status_code=500, body=error_body,
        )
        mock_client._session.exec.return_value = (mock_response, None)

        with pytest.raises(Error) as exc_info:
            mock_client.create_client_list(
                CreateClientListRequest(
                    name="TEST LIST",
                    type="IP",
                    notes="Some notes",
                    tags=["red", "green"],
                    contract_id="M-2CF0QRI",
                    group_id=112524,
                    items=[
                        ListItemPayload(
                            value="1.1.1.1",
                            description="some description",
                            tags=[],
                            expiration_date=(
                                "2026-12-26T01:32:08.375+00:00"
                            ),
                        ),
                    ],
                ),
            )

        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error fetching client lists"
        assert err.status_code == 500

    def test_validation_error(self, mock_client):
        """CreateClientList raises ErrStructValidation for empty."""
        with pytest.raises(ErrStructValidation):
            mock_client.create_client_list(CreateClientListRequest())

        mock_client._session.exec.assert_not_called()


# ===================================================================
# TestDeleteClientLists — mirrors Go TestDeleteClientLists
# (client_list_test.go lines 952-1017)
# ===================================================================


class TestDeleteClientLists:
    """Test DeleteClientList — mirrors Go TestDeleteClientLists.

    3 scenarios: 204 NoContent, 500 error, validation error.
    """

    def test_204_no_content(self, mock_client):
        """DeleteClientList returns None on 204 NoContent."""
        mock_response = create_mock_response(status_code=204, body="")
        mock_client._session.exec.return_value = (mock_response, None)

        result = mock_client.delete_client_list(
            DeleteClientListRequest(list_id="12_AB"),
        )

        assert result is None

        # Verify request
        mock_client._session.exec.assert_called_once()
        call_args, _ = mock_client._session.exec.call_args
        assert call_args[0] == "DELETE"
        assert call_args[1] == "/client-list/v1/lists/12_AB"

    def test_500_internal_server_error(self, mock_client):
        """DeleteClientList raises Error on 500."""
        error_body = json.dumps({
            "type": "internal_error",
            "title": "Internal Server Error",
            "detail": "Error fetching client lists",
            "status": 500,
        })
        mock_response = create_mock_response(
            status_code=500, body=error_body,
        )
        mock_client._session.exec.return_value = (mock_response, None)

        with pytest.raises(Error) as exc_info:
            mock_client.delete_client_list(
                DeleteClientListRequest(list_id="12_AB"),
            )

        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error fetching client lists"
        assert err.status_code == 500

    def test_validation_error(self, mock_client):
        """DeleteClientList raises ErrStructValidation for empty."""
        with pytest.raises(ErrStructValidation):
            mock_client.delete_client_list(DeleteClientListRequest())

        mock_client._session.exec.assert_not_called()


# ===================================================================
# TestTranslateUsernames — mirrors Go TestTranslateUsernames
# (client_list_test.go lines 1019-1104)
# ===================================================================

# Verbatim response body for TranslateUsernames 200 OK
_TRANSLATE_USERNAMES_200_BODY = """{
    "user1": "3a453537-faa8-4525-b5db-022447bbbf2a",
    "user2": "07e29045-7739-4bd9-8cfb-9f118e000337",
    "user3": "e164394a-5ae1-4208-8487-1ac0f368ecf3"
}"""


class TestTranslateUsernames:
    """Test TranslateUsernames — mirrors Go TestTranslateUsernames.

    3 scenarios: 200 OK, 500 error, validation error.
    """

    def test_200_translate_usernames(self, mock_client):
        """TranslateUsernames returns username→UUID map on 200 OK."""
        body = _TRANSLATE_USERNAMES_200_BODY
        mock_response = create_mock_response(status_code=200, body=body)
        mock_client._session.exec.return_value = (
            mock_response, json.loads(body),
        )

        result = mock_client.translate_usernames(
            ["user1", "user2", "user3"],
        )

        expected = {
            "user1": "3a453537-faa8-4525-b5db-022447bbbf2a",
            "user2": "07e29045-7739-4bd9-8cfb-9f118e000337",
            "user3": "e164394a-5ae1-4208-8487-1ac0f368ecf3",
        }
        assert result == expected

        # Verify request
        mock_client._session.exec.assert_called_once()
        call_args, call_kwargs = mock_client._session.exec.call_args
        assert call_args[0] == "POST"
        assert call_args[1] == "/appsec/v1/search/user/external-uuid"

        # Verify request body
        req_body = call_kwargs.get(
            "body", call_args[2] if len(call_args) > 2 else None,
        )
        assert req_body == ["user1", "user2", "user3"]

    def test_500_internal_server_error(self, mock_client):
        """TranslateUsernames raises Error on 500."""
        error_body = json.dumps({
            "type": "internal_error",
            "title": "Internal Server Error",
            "detail": "Error fetching client lists",
            "status": 500,
        })
        mock_response = create_mock_response(
            status_code=500, body=error_body,
        )
        mock_client._session.exec.return_value = (mock_response, None)

        with pytest.raises(Error) as exc_info:
            mock_client.translate_usernames(
                ["user1", "user2", "user3"],
            )

        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error fetching client lists"
        assert err.status_code == 500

    def test_validation_error(self, mock_client):
        """TranslateUsernames raises ErrStructValidation for empty."""
        with pytest.raises(ErrStructValidation):
            mock_client.translate_usernames([])

        mock_client._session.exec.assert_not_called()


# ===================================================================
# TestGetClientListItems — mirrors Go TestGetClientListItems
# (client_list_test.go lines 1106-1312)
# ===================================================================

# Verbatim response body for GetClientListItems 200 OK (non-user type)
_GET_CLIENT_LIST_ITEMS_200_BODY = """{
    "content": [
        {
            "createDate": "2022-07-12T20:14:29.189+00:00",
            "createdBy": "ccare2",
            "createdVersion": 9,
            "productionStatus": "INACTIVE",
            "stagingStatus": "PENDING_ACTIVATION",
            "tags": [],
            "type": "IP",
            "updateDate": "2022-07-12T20:14:29.189+00:00",
            "updatedBy": "ccare2",
            "value": "7d0:1:0::0/64"
        },
        {
            "createDate": "2022-07-12T20:14:29.189+00:00",
            "createdBy": "ccare2",
            "createdVersion": 9,
            "description": "Item with description, tags, expiration date",
            "expirationDate": "2030-12-31T12:40:00.000+00:00",
            "productionStatus": "INACTIVE",
            "stagingStatus": "PENDING_ACTIVATION",
            "tags": [
                "red",
                "green",
                "blue"
            ],
            "type": "IP",
            "updateDate": "2022-07-12T20:14:29.189+00:00",
            "updatedBy": "ccare2",
            "value": "7d0:1:1::0/64"
        }
    ]
}"""

# Verbatim response body for GetClientListItems 200 OK (user type)
_GET_CLIENT_LIST_ITEMS_USER_200_BODY = """{
    "content": [
        {
            "createDate": "2022-07-12T20:14:29.189+00:00",
            "createdBy": "ccare2",
            "createdVersion": 9,
            "productionStatus": "INACTIVE",
            "stagingStatus": "PENDING_ACTIVATION",
            "tags": [],
            "type": "USER_ID",
            "updateDate": "2022-07-12T20:14:29.189+00:00",
            "updatedBy": "ccare2",
            "value": "3a453537-faa8-4525-b5db-022447bbbf2a",
            "username": "user1"
        },
        {
            "createDate": "2022-07-12T20:14:29.189+00:00",
            "createdBy": "ccare2",
            "createdVersion": 9,
            "description": "Item with description, tags, expiration date",
            "expirationDate": "2030-12-31T12:40:00.000+00:00",
            "productionStatus": "INACTIVE",
            "stagingStatus": "PENDING_ACTIVATION",
            "tags": [
                "red",
                "green",
                "blue"
            ],
            "type": "USER_ID",
            "updateDate": "2022-07-12T20:14:29.189+00:00",
            "updatedBy": "ccare2",
            "value": "07e29045-7739-4bd9-8cfb-9f118e000337",
            "username": "user2"
        }
    ]
}"""


class TestGetClientListItems:
    """Test GetClientListItems — mirrors Go TestGetClientListItems.

    4 scenarios: 200 OK non-user, 200 OK user type, 500 error,
    validation error.
    """

    def test_200_ok_non_user_type(self, mock_client):
        """GetClientListItems returns IP items on 200 OK."""
        body = _GET_CLIENT_LIST_ITEMS_200_BODY
        mock_response = create_mock_response(status_code=200, body=body)
        mock_client._session.exec.return_value = (
            mock_response, json.loads(body),
        )

        result = mock_client.get_client_list_items(
            GetClientListItemsRequest(list_id="12_AB"),
        )

        expected = GetClientListItemsResponse(
            items=[
                ListItemContent(
                    create_date="2022-07-12T20:14:29.189+00:00",
                    created_by="ccare2",
                    created_version=9,
                    production_status="INACTIVE",
                    staging_status="PENDING_ACTIVATION",
                    tags=[],
                    type="IP",
                    update_date="2022-07-12T20:14:29.189+00:00",
                    updated_by="ccare2",
                    value="7d0:1:0::0/64",
                ),
                ListItemContent(
                    create_date="2022-07-12T20:14:29.189+00:00",
                    created_by="ccare2",
                    created_version=9,
                    production_status="INACTIVE",
                    staging_status="PENDING_ACTIVATION",
                    tags=["red", "green", "blue"],
                    description=(
                        "Item with description, tags, "
                        "expiration date"
                    ),
                    expiration_date=(
                        "2030-12-31T12:40:00.000+00:00"
                    ),
                    type="IP",
                    update_date="2022-07-12T20:14:29.189+00:00",
                    updated_by="ccare2",
                    value="7d0:1:1::0/64",
                ),
            ],
        )
        assert result == expected

        # Verify request
        mock_client._session.exec.assert_called_once()
        call_args, _ = mock_client._session.exec.call_args
        assert call_args[0] == "GET"
        assert "/client-list/v1/lists/12_AB/items" in call_args[1]
        assert "showUsernames=true" in call_args[1]

    def test_200_ok_user_type(self, mock_client):
        """GetClientListItems returns USER_ID items with username."""
        body = _GET_CLIENT_LIST_ITEMS_USER_200_BODY
        mock_response = create_mock_response(status_code=200, body=body)
        mock_client._session.exec.return_value = (
            mock_response, json.loads(body),
        )

        result = mock_client.get_client_list_items(
            GetClientListItemsRequest(list_id="12_AB"),
        )

        expected = GetClientListItemsResponse(
            items=[
                ListItemContent(
                    create_date="2022-07-12T20:14:29.189+00:00",
                    created_by="ccare2",
                    created_version=9,
                    production_status="INACTIVE",
                    staging_status="PENDING_ACTIVATION",
                    tags=[],
                    type="USER_ID",
                    update_date="2022-07-12T20:14:29.189+00:00",
                    updated_by="ccare2",
                    value=(
                        "3a453537-faa8-4525-b5db-022447bbbf2a"
                    ),
                    username="user1",
                ),
                ListItemContent(
                    create_date="2022-07-12T20:14:29.189+00:00",
                    created_by="ccare2",
                    created_version=9,
                    production_status="INACTIVE",
                    staging_status="PENDING_ACTIVATION",
                    tags=["red", "green", "blue"],
                    description=(
                        "Item with description, tags, "
                        "expiration date"
                    ),
                    expiration_date=(
                        "2030-12-31T12:40:00.000+00:00"
                    ),
                    type="USER_ID",
                    update_date="2022-07-12T20:14:29.189+00:00",
                    updated_by="ccare2",
                    value=(
                        "07e29045-7739-4bd9-8cfb-9f118e000337"
                    ),
                    username="user2",
                ),
            ],
        )
        assert result == expected

    def test_500_internal_server_error(self, mock_client):
        """GetClientListItems raises Error on 500."""
        error_body = json.dumps({
            "type": "internal_error",
            "title": "Internal Server Error",
            "detail": "Error fetching client lists",
            "status": 500,
        })
        mock_response = create_mock_response(
            status_code=500, body=error_body,
        )
        mock_client._session.exec.return_value = (mock_response, None)

        with pytest.raises(Error) as exc_info:
            mock_client.get_client_list_items(
                GetClientListItemsRequest(list_id="12_AB"),
            )

        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error fetching client lists"
        assert err.status_code == 500

    def test_validation_error(self, mock_client):
        """GetClientListItems raises ErrStructValidation for empty."""
        with pytest.raises(ErrStructValidation):
            mock_client.get_client_list_items(
                GetClientListItemsRequest(),
            )

        mock_client._session.exec.assert_not_called()


# ===================================================================
# TestCreateActivation — mirrors Go TestCreateActivation
# (client_list_activation_test.go lines 17-129)
# ===================================================================

# Verbatim response body for CreateActivation 200 OK
_CREATE_ACTIVATION_200_BODY = """{
    "action": "ACTIVATE",
    "activationStatus": "PENDING_ACTIVATION",
    "listId": "1234_NORTHAMERICAGEOALLOWLIST",
    "network": "PRODUCTION",
    "notificationRecipients": ["aa@dd.com"],
    "version": 1,
    "activationId": 12,
    "createDate": "2023-04-05T18:46:56.365Z",
    "createdBy": "jdoe",
    "network": "PRODUCTION",
    "comments": "Activation of GEO allowlist list",
    "siebelTicketId": "12_AB"
}"""


class TestCreateActivation:
    """Test CreateActivation — mirrors Go TestCreateActivation.

    3 scenarios: 200 OK, 500 error, validation error.
    """

    def test_200_ok(self, mock_client):
        """CreateActivation returns activation status on 200 OK."""
        body = _CREATE_ACTIVATION_200_BODY
        mock_response = create_mock_response(status_code=200, body=body)
        mock_client._session.exec.return_value = (
            mock_response, json.loads(body),
        )

        result = mock_client.create_activation(
            CreateActivationRequest(
                list_id="1234_NORTHAMERICAGEOALLOWLIST",
                action=ACTIVATE,
                network=PRODUCTION,
                comments="Activation of GEO allowlist list",
                siebel_ticket_id="12_B",
                notification_recipients=["a@a.com", "c@c.com"],
            ),
        )

        expected = CreateActivationResponse(
            action="ACTIVATE",
            activation_id=12,
            activation_status=PENDING_ACTIVATION,
            create_date="2023-04-05T18:46:56.365Z",
            created_by="jdoe",
            comments="Activation of GEO allowlist list",
            list_id="1234_NORTHAMERICAGEOALLOWLIST",
            network=PRODUCTION,
            notification_recipients=["aa@dd.com"],
            siebel_ticket_id="12_AB",
            version=1,
        )
        assert result == expected

        # Verify request
        mock_client._session.exec.assert_called_once()
        call_args, call_kwargs = mock_client._session.exec.call_args
        assert call_args[0] == "POST"
        assert call_args[1] == (
            "/client-list/v1/lists/"
            "1234_NORTHAMERICAGEOALLOWLIST/activations"
        )

        # Verify request body (only ActivationParams, not ListID)
        req_body = call_kwargs.get(
            "body", call_args[2] if len(call_args) > 2 else None,
        )
        expected_body = json.loads(
            '{"action":"ACTIVATE",'
            '"comments":"Activation of GEO allowlist list",'
            '"network":"PRODUCTION",'
            '"notificationRecipients":["a@a.com","c@c.com"],'
            '"siebelTicketId":"12_B"}',
        )
        assert req_body == expected_body

    def test_500_internal_server_error(self, mock_client):
        """CreateActivation raises Error on 500."""
        error_body = json.dumps({
            "type": "internal_error",
            "title": "Internal Server Error",
            "detail": "Error creating client lists activation",
            "status": 500,
        })
        mock_response = create_mock_response(
            status_code=500, body=error_body,
        )
        mock_client._session.exec.return_value = (mock_response, None)

        with pytest.raises(Error) as exc_info:
            mock_client.create_activation(
                CreateActivationRequest(
                    list_id="1234_NORTHAMERICAGEOALLOWLIST",
                    network=PRODUCTION,
                ),
            )

        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error creating client lists activation"
        assert err.status_code == 500

    def test_validation_error(self, mock_client):
        """CreateActivation raises ErrStructValidation for empty."""
        with pytest.raises(ErrStructValidation):
            mock_client.create_activation(CreateActivationRequest())

        mock_client._session.exec.assert_not_called()


# ===================================================================
# TestCreateDeactivation — mirrors Go TestCreateDeactivation
# (client_list_activation_test.go lines 131-275)
# ===================================================================

# Verbatim response body for CreateDeactivation 200 OK
_CREATE_DEACTIVATION_200_BODY = """{
    "action": "DEACTIVATE",
    "activationStatus": "PENDING_DEACTIVATION",
    "listId": "1234_NORTHAMERICAGEOALLOWLIST",
    "network": "PRODUCTION",
    "notificationRecipients": ["aa@dd.com"],
    "version": 1,
    "activationId": 12,
    "createDate": "2023-04-05T18:46:56.365Z",
    "createdBy": "jdoe",
    "network": "PRODUCTION",
    "comments": "Activation of GEO allowlist list",
    "siebelTicketId": "12_AB"
}"""


class TestCreateDeactivation:
    """Test CreateDeactivation — mirrors Go TestCreateDeactivation.

    5 scenarios: 200 OK, 403 forbidden, 404 not found,
    500 error, validation error.
    """

    def test_200_ok(self, mock_client):
        """CreateDeactivation returns deactivation status on 200 OK."""
        body = _CREATE_DEACTIVATION_200_BODY
        mock_response = create_mock_response(status_code=200, body=body)
        mock_client._session.exec.return_value = (
            mock_response, json.loads(body),
        )

        result = mock_client.create_deactivation(
            CreateDeactivationRequest(
                list_id="1234_NORTHAMERICAGEOALLOWLIST",
                action=DEACTIVATE,
                network=PRODUCTION,
                comments="Activation of GEO allowlist list",
                siebel_ticket_id="12_B",
                notification_recipients=["a@a.com", "c@c.com"],
            ),
        )

        expected = CreateDeactivationResponse(
            action="DEACTIVATE",
            activation_id=12,
            activation_status=PENDING_DEACTIVATION,
            create_date="2023-04-05T18:46:56.365Z",
            created_by="jdoe",
            comments="Activation of GEO allowlist list",
            list_id="1234_NORTHAMERICAGEOALLOWLIST",
            network=PRODUCTION,
            notification_recipients=["aa@dd.com"],
            siebel_ticket_id="12_AB",
            version=1,
        )
        assert result == expected

        # Verify request
        mock_client._session.exec.assert_called_once()
        call_args, call_kwargs = mock_client._session.exec.call_args
        assert call_args[0] == "POST"
        assert call_args[1] == (
            "/client-list/v1/lists/"
            "1234_NORTHAMERICAGEOALLOWLIST/activations"
        )

        # Verify request body
        req_body = call_kwargs.get(
            "body", call_args[2] if len(call_args) > 2 else None,
        )
        expected_body = json.loads(
            '{"action":"DEACTIVATE",'
            '"comments":"Activation of GEO allowlist list",'
            '"network":"PRODUCTION",'
            '"notificationRecipients":["a@a.com","c@c.com"],'
            '"siebelTicketId":"12_B"}',
        )
        assert req_body == expected_body

    def test_403_forbidden_operation_error(self, mock_client):
        """CreateDeactivation raises Error on 403 forbidden."""
        forbidden_type = (
            "https://problems.luna.akamaiapis.net/"
            "client-list/error-types/FORBIDDEN-OPERATION"
        )
        error_body = json.dumps({
            "type": forbidden_type,
            "title": "This operation is invalid",
            "detail": "Only not used client list are allowed "
                      "to be deactivated",
            "status": 403,
        })
        mock_response = create_mock_response(
            status_code=403, body=error_body,
        )
        mock_client._session.exec.return_value = (mock_response, None)

        with pytest.raises(Error) as exc_info:
            mock_client.create_deactivation(
                CreateDeactivationRequest(
                    list_id="1234_NORTHAMERICAGEOALLOWLIST",
                    action=DEACTIVATE,
                    network=PRODUCTION,
                    comments="Activation of GEO allowlist list",
                    siebel_ticket_id="12_B",
                    notification_recipients=["a@a.com", "c@c.com"],
                ),
            )

        err = exc_info.value
        assert err.type == (
            "https://problems.luna.akamaiapis.net/"
            "client-list/error-types/FORBIDDEN-OPERATION"
        )
        assert err.title == "This operation is invalid"
        assert err.detail == (
            "Only not used client list are allowed to be deactivated"
        )
        assert err.status_code == 403

    def test_404_not_found_error(self, mock_client):
        """CreateDeactivation raises Error on 404 not found."""
        error_body = json.dumps({
            "type": "https://problems.luna.akamaiapis.net/client-list/error-types/NOT-FOUND",
            "title": "Not Found",
            "detail": "Client list with uid 185417_IPTYPECLIENTLIST not found",
            "status": 404,
        })
        mock_response = create_mock_response(
            status_code=404, body=error_body,
        )
        mock_client._session.exec.return_value = (mock_response, None)

        with pytest.raises(Error) as exc_info:
            mock_client.create_deactivation(
                CreateDeactivationRequest(
                    list_id="1234_NORTHAMERICAGEOALLOWLIST",
                    action=DEACTIVATE,
                    network=PRODUCTION,
                    comments="Activation of GEO allowlist list",
                    siebel_ticket_id="12_B",
                    notification_recipients=["a@a.com", "c@c.com"],
                ),
            )

        err = exc_info.value
        assert err.type == (
            "https://problems.luna.akamaiapis.net/"
            "client-list/error-types/NOT-FOUND"
        )
        assert err.title == "Not Found"
        assert err.detail == (
            "Client list with uid 185417_IPTYPECLIENTLIST not found"
        )
        assert err.status_code == 404

    def test_500_internal_server_error(self, mock_client):
        """CreateDeactivation raises Error on 500."""
        error_type = (
            "https://problems.luna.akamaiapis.net/"
            "client-list/error-types/INTERNAL-SERVER-ERROR"
        )
        error_body = json.dumps({
            "type": error_type,
            "title": "Internal Server Error",
            "detail": "Error creating client lists deactivation",
            "status": 500,
        })
        mock_response = create_mock_response(
            status_code=500, body=error_body,
        )
        mock_client._session.exec.return_value = (mock_response, None)

        with pytest.raises(Error) as exc_info:
            mock_client.create_deactivation(
                CreateDeactivationRequest(
                    list_id="1234_NORTHAMERICAGEOALLOWLIST",
                    action=DEACTIVATE,
                    network=PRODUCTION,
                    comments="Activation of GEO allowlist list",
                    siebel_ticket_id="12_B",
                    notification_recipients=["a@a.com", "c@c.com"],
                ),
            )

        err = exc_info.value
        assert err.type == (
            "https://problems.luna.akamaiapis.net/"
            "client-list/error-types/INTERNAL-SERVER-ERROR"
        )
        assert err.title == "Internal Server Error"
        assert err.detail == (
            "Error creating client lists deactivation"
        )
        assert err.status_code == 500

    def test_validation_error(self, mock_client):
        """CreateDeactivation raises ErrStructValidation for empty."""
        with pytest.raises(ErrStructValidation):
            mock_client.create_deactivation(
                CreateDeactivationRequest(),
            )

        mock_client._session.exec.assert_not_called()


# ===================================================================
# TestGetActivation — mirrors Go TestGetActivation
# (client_list_activation_test.go lines 277-377)
# ===================================================================

# Verbatim response body for GetActivation 200 OK
_GET_ACTIVATION_200_BODY = """{
    "action": "ACTIVATE",
    "activationId": 12,
    "activationStatus": "PENDING_ACTIVATION",
    "comments": "latest activation",
    "createDate": "2023-04-05T18:46:56.365Z",
    "createdBy": "jdoe",
    "fast": true,
    "listId": "1234_NORTHAMERICAGEOALLOWLIST",
    "network": "PRODUCTION",
    "notificationRecipients": [
            "qw@ff.com"
    ],
    "siebelTicketId": "q",
    "version": 1
}"""


class TestGetActivation:
    """Test GetActivation — mirrors Go TestGetActivation.

    3 scenarios: 200 OK, 500 error, validation error.
    """

    def test_200_ok(self, mock_client):
        """GetActivation returns activation details on 200 OK."""
        body = _GET_ACTIVATION_200_BODY
        mock_response = create_mock_response(status_code=200, body=body)
        mock_client._session.exec.return_value = (
            mock_response, json.loads(body),
        )

        result = mock_client.get_activation(
            GetActivationRequest(activation_id=12),
        )

        expected = GetActivationResponse(
            activation_id=12,
            list_id="1234_NORTHAMERICAGEOALLOWLIST",
            version=1,
            create_date="2023-04-05T18:46:56.365Z",
            created_by="jdoe",
            fast=True,
            initial_activation=False,
            activation_status="PENDING_ACTIVATION",
            action=ACTIVATE,
            notification_recipients=["qw@ff.com"],
            comments="latest activation",
            network=PRODUCTION,
            siebel_ticket_id="q",
        )
        assert result == expected

        # Verify request
        mock_client._session.exec.assert_called_once()
        call_args, _ = mock_client._session.exec.call_args
        assert call_args[0] == "GET"
        assert call_args[1] == "/client-list/v1/activations/12"

    def test_500_internal_server_error(self, mock_client):
        """GetActivation raises Error on 500."""
        error_body = json.dumps({
            "type": "internal_error",
            "title": "Internal Server Error",
            "detail": "Error fetching client lists activation",
            "status": 500,
        })
        mock_response = create_mock_response(
            status_code=500, body=error_body,
        )
        mock_client._session.exec.return_value = (mock_response, None)

        with pytest.raises(Error) as exc_info:
            mock_client.get_activation(
                GetActivationRequest(activation_id=12),
            )

        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error fetching client lists activation"
        assert err.status_code == 500

    def test_validation_error(self, mock_client):
        """GetActivation raises ErrStructValidation for empty."""
        with pytest.raises(ErrStructValidation):
            mock_client.get_activation(GetActivationRequest())

        mock_client._session.exec.assert_not_called()


# ===================================================================
# TestGetActivationStatus — mirrors Go TestGetActivationStatus
# (client_list_activation_test.go lines 379-475)
# ===================================================================

# Verbatim response body for GetActivationStatus 200 OK
_GET_ACTIVATION_STATUS_200_BODY = """{
    "action": "ACTIVATE",
    "activationStatus": "PENDING_ACTIVATION",
    "listId": "1234_NORTHAMERICAGEOALLOWLIST",
    "network": "PRODUCTION",
    "notificationRecipients": [],
    "version": 1,
    "activationId": 12,
    "createDate": "2023-04-05T18:46:56.365Z",
    "createdBy": "jdoe",
    "network": "PRODUCTION",
    "comments": "Activation of GEO allowlist list",
    "siebelTicketId": "12_AB"
}"""


class TestGetActivationStatus:
    """Test GetActivationStatus — mirrors Go TestGetActivationStatus.

    3 scenarios: 200 OK, 500 error, validation error.
    """

    def test_200_ok(self, mock_client):
        """GetActivationStatus returns status on 200 OK."""
        body = _GET_ACTIVATION_STATUS_200_BODY
        mock_response = create_mock_response(status_code=200, body=body)
        mock_client._session.exec.return_value = (
            mock_response, json.loads(body),
        )

        result = mock_client.get_activation_status(
            GetActivationStatusRequest(
                list_id="1234_NORTHAMERICAGEOALLOWLIST",
                network=PRODUCTION,
            ),
        )

        expected = GetActivationStatusResponse(
            action="ACTIVATE",
            activation_id=12,
            activation_status=PENDING_ACTIVATION,
            create_date="2023-04-05T18:46:56.365Z",
            created_by="jdoe",
            comments="Activation of GEO allowlist list",
            list_id="1234_NORTHAMERICAGEOALLOWLIST",
            network=PRODUCTION,
            notification_recipients=[],
            siebel_ticket_id="12_AB",
            version=1,
        )
        assert result == expected

        # Verify request
        mock_client._session.exec.assert_called_once()
        call_args, _ = mock_client._session.exec.call_args
        assert call_args[0] == "GET"
        assert call_args[1] == (
            "/client-list/v1/lists/"
            "1234_NORTHAMERICAGEOALLOWLIST/"
            "environments/PRODUCTION/status"
        )

    def test_500_internal_server_error(self, mock_client):
        """GetActivationStatus raises Error on 500."""
        error_body = json.dumps({
            "type": "internal_error",
            "title": "Internal Server Error",
            "detail": "Error fetching client lists activation",
            "status": 500,
        })
        mock_response = create_mock_response(
            status_code=500, body=error_body,
        )
        mock_client._session.exec.return_value = (mock_response, None)

        with pytest.raises(Error) as exc_info:
            mock_client.get_activation_status(
                GetActivationStatusRequest(
                    list_id="1234_NORTHAMERICAGEOALLOWLIST",
                    network=PRODUCTION,
                ),
            )

        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error fetching client lists activation"
        assert err.status_code == 500

    def test_validation_error(self, mock_client):
        """GetActivationStatus raises ErrStructValidation for empty."""
        with pytest.raises(ErrStructValidation):
            mock_client.get_activation_status(
                GetActivationStatusRequest(),
            )

        mock_client._session.exec.assert_not_called()
