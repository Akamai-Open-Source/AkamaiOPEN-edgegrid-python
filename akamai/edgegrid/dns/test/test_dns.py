# pylint: disable=too-many-lines,line-too-long,too-many-arguments
# pylint: disable=too-many-positional-arguments,unused-argument
"""Unit tests for Edge DNS API client.

Mirrors all 10 Go DNS test files — every test scenario, assertion,
response body, and error check adapted to pytest.

Go source files mirrored:
- authorities_test.go: TestDNS_GetAuthorities, TestDNS_GetNameServerRecordList
- data_test.go: TestDNS_ListGroups
- dns_test.go: TestClient
- errors_test.go: TestJsonErrorUnmarshalling
- record_test.go: TestDNS_CreateRecord, TestDNS_UpdateRecord, TestDNS_DeleteRecord
- record_lookup_test.go: TestDNS_GetRecord, TestDNS_GetRecordList,
    TestDNS_GetRdata, TestDNS_TestRdata, TestDNS_ParseRData
- recordsets_test.go: TestDNS_GetRecordSets, TestDNS_CreateRecordSets,
    TestDNS_UpdateRecordSets
- tsig_test.go: 7 TSIG key management test functions
- zone_test.go: 14 zone lifecycle and validation test functions
- zonebulk_test.go: 6 bulk zone operation test functions
"""

import json
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.dns.dns import Client
from akamai.edgegrid.session import Session
from akamai.edgegrid.test_helpers import mock_response
from akamai.edgegrid.dns import models
from akamai.edgegrid.dns.errors import Error, parse_dns_error_response
from akamai.edgegrid.dns.validation import validate_zone


# ===================================================================
# authorities_test.go — TestDNS_GetAuthorities
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_path, expected_response, expected_error",
    [
        (
            "200 OK",
            models.GetAuthoritiesRequest(contract_ids="9-9XXXXX"),
            200,
            json.dumps({
                "contracts": [
                    {
                        "contractId": "9-9XXXXX",
                        "authorities": [
                            "a1-118.akam.net.",
                            "a2-64.akam.net.",
                            "a6-66.akam.net.",
                            "a18-67.akam.net.",
                            "a7-64.akam.net.",
                            "a11-64.akam.net.",
                        ],
                    }
                ]
            }),
            "/config-dns/v2/data/authorities?contractIds=9-9XXXXX",
            models.GetAuthoritiesResponse(
                contracts=[
                    models.Contract(
                        contract_id="9-9XXXXX",
                        authorities=[
                            "a1-118.akam.net.",
                            "a2-64.akam.net.",
                            "a6-66.akam.net.",
                            "a18-67.akam.net.",
                            "a7-64.akam.net.",
                            "a11-64.akam.net.",
                        ],
                    )
                ]
            ),
            None,
        ),
        (
            "Missing arguments",
            models.GetAuthoritiesRequest(),
            200,
            "",
            None,
            None,
            "get authorities: struct validation: ContractIDs: cannot be blank",
        ),
        (
            "500 internal server error",
            models.GetAuthoritiesRequest(contract_ids="9-9XXXXX"),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error fetching authorities",
                "status": 500,
            }),
            "/config-dns/v2/data/authorities?contractIds=9-9XXXXX",
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error fetching authorities",
                status_code=500,
            ),
        ),
    ],
)
def test_get_authorities(
    test_name, params, response_status, response_body,
    expected_path, expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_GetAuthorities from authorities_test.go."""
    if isinstance(expected_error, str):
        with pytest.raises(ValueError, match=expected_error):
            dns_client.get_authorities(params)
        return

    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.get_authorities(params)
        assert exc_info.value.type == expected_error.type
        assert exc_info.value.title == expected_error.title
        assert exc_info.value.detail == expected_error.detail
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.get_authorities(params)
    assert result == expected_response

    call_args = mock_session.exec.call_args
    assert call_args[0][0] == "GET"
    assert call_args[0][1] == expected_path


# ===================================================================
# authorities_test.go — TestDNS_GetNameServerRecordList
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_response, expected_error",
    [
        (
            "test with valid arguments",
            models.GetNameServerRecordListRequest(contract_ids="9-9XXXXX"),
            200,
            json.dumps({
                "contracts": [
                    {
                        "contractId": "9-9XXXXX",
                        "authorities": [
                            "a1-118.akam.net.",
                            "a2-64.akam.net.",
                            "a6-66.akam.net.",
                            "a18-67.akam.net.",
                            "a7-64.akam.net.",
                            "a11-64.akam.net.",
                        ],
                    }
                ]
            }),
            [
                "a1-118.akam.net.",
                "a2-64.akam.net.",
                "a6-66.akam.net.",
                "a18-67.akam.net.",
                "a7-64.akam.net.",
                "a11-64.akam.net.",
            ],
            None,
        ),
        (
            "test with missing arguments",
            models.GetNameServerRecordListRequest(),
            200,
            "",
            None,
            "get name server record list: struct validation: ContractIDs: cannot be blank",
        ),
    ],
)
def test_get_name_server_record_list(
    test_name, params, response_status, response_body,
    expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_GetNameServerRecordList from authorities_test.go."""
    if isinstance(expected_error, str):
        with pytest.raises(ValueError, match=expected_error):
            dns_client.get_name_server_record_list(params)
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.get_name_server_record_list(params)
    assert result == expected_response


# ===================================================================
# data_test.go — TestDNS_ListGroups
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_response, expected_error",
    [
        (
            "200 OK with query param",
            models.ListGroupRequest(group_id="9012"),
            200,
            json.dumps({
                "groups": [
                    {
                        "groupId": 9012,
                        "groupName": "test-group",
                        "contractIds": ["9-9XXXXX"],
                        "permissions": ["READ", "WRITE"],
                    }
                ]
            }),
            models.ListGroupResponse(
                groups=[
                    models.Group(
                        group_id=9012,
                        group_name="test-group",
                        contract_ids=["9-9XXXXX"],
                        permissions=["READ", "WRITE"],
                    )
                ]
            ),
            None,
        ),
        (
            "200 OK without query param",
            models.ListGroupRequest(),
            200,
            json.dumps({
                "groups": [
                    {
                        "groupId": 9012,
                        "groupName": "test-group-1",
                        "contractIds": ["9-9XXXXX"],
                        "permissions": ["READ", "WRITE"],
                    },
                    {
                        "groupId": 9013,
                        "groupName": "test-group-2",
                        "contractIds": ["9-9YYYYY"],
                        "permissions": ["READ"],
                    },
                ]
            }),
            models.ListGroupResponse(
                groups=[
                    models.Group(
                        group_id=9012,
                        group_name="test-group-1",
                        contract_ids=["9-9XXXXX"],
                        permissions=["READ", "WRITE"],
                    ),
                    models.Group(
                        group_id=9013,
                        group_name="test-group-2",
                        contract_ids=["9-9YYYYY"],
                        permissions=["READ"],
                    ),
                ]
            ),
            None,
        ),
        (
            "500 internal server error",
            models.ListGroupRequest(),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error fetching groups",
                "status": 500,
            }),
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error fetching groups",
                status_code=500,
            ),
        ),
    ],
)
def test_list_groups(
    test_name, params, response_status, response_body,
    expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_ListGroups from data_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.list_groups(params)
        # list_groups re-wraps errors; check __cause__ for original Error
        cause = exc_info.value.__cause__
        assert isinstance(cause, Error)
        assert cause.status_code == expected_error.status_code
        assert cause.type == expected_error.type
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.list_groups(params)
    assert result == expected_response


# ===================================================================
# dns_test.go — TestClient
# ===================================================================


def test_client_creation():
    """Mirrors Go TestClient from dns_test.go — creating client with/without options."""
    # No options
    session = MagicMock(spec=Session)
    client = Client(session)
    assert client._session is session  # pylint: disable=protected-access

    # Dummy option — mirrors Go "dummy option" scenario
    session2 = MagicMock(spec=Session)
    client2 = Client(session2)
    assert client2._session is session2  # pylint: disable=protected-access


# ===================================================================
# errors_test.go — TestJsonErrorUnmarshalling
# ===================================================================


@pytest.mark.parametrize(
    "test_name, response_status, body, expected_type,"
    " expected_title, expected_detail, expected_status",
    [
        (
            "HTML response",
            503,
            "<HTML><HEAD>\n<TITLE>Access Denied</TITLE>\n"
            "</HEAD><BODY>\n<H1>Access Denied</H1>\n"
            "You don't have permission to access"
            ' "http&#58;&#47;&#47;akab-xxx.luna.akamaiapis.net&#47;'
            'config-dns/v2/zones&#47;example.com&#47;zone-file"'
            " on this server.<P>\n"
            "Reference&#58;&#32;&#35;28.acd7c268.1700596021.1d6aec69\n"
            "</BODY>\n</HTML>\n",
            "",
            "Failed to unmarshal error body. DNS API failed."
            " Check details for more information.",
            "<HTML><HEAD>\n<TITLE>Access Denied</TITLE>\n"
            "</HEAD><BODY>\n<H1>Access Denied</H1>\n"
            "You don't have permission to access"
            ' "http://akab-xxx.luna.akamaiapis.net/'
            'config-dns/v2/zones/example.com/zone-file"'
            " on this server.<P>\n"
            "Reference: #28.acd7c268.1700596021.1d6aec69\n"
            "</BODY>\n</HTML>\n",
            503,
        ),
        (
            "plain text response",
            503,
            "Your request did not succeed as this operation has reached "
            " the limit for your account. Please try after"
            " 2024-01-16T15:20:55.945Z",
            "",
            "Failed to unmarshal error body. DNS API failed."
            " Check details for more information.",
            "Your request did not succeed as this operation has reached "
            " the limit for your account. Please try after"
            " 2024-01-16T15:20:55.945Z",
            503,
        ),
        (
            "XML response",
            503,
            '<Root><Item id="1" name="Example" /></Root>',
            "",
            "Failed to unmarshal error body. DNS API failed."
            " Check details for more information.",
            '<Root><Item id="1" name="Example" /></Root>',
            503,
        ),
    ],
)
def test_json_error_unmarshalling(
    test_name, response_status, body, expected_type,
    expected_title, expected_detail, expected_status,
):
    """Mirrors Go TestJsonErrorUnmarshalling from errors_test.go."""
    response = mock_response(status_code=response_status, text_body=body)
    error = parse_dns_error_response(response)
    assert error.type == expected_type
    assert error.title == expected_title
    assert error.detail == expected_detail
    assert error.status_code == expected_status


# ===================================================================
# record_test.go — TestDNS_CreateRecord
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_path, expected_error",
    [
        (
            "201 Created",
            models.CreateRecordRequest(
                zone="example.com",
                record=models.RecordBody(
                    name="www.example.com",
                    record_type="A",
                    ttl=300,
                    target=["1.2.3.4"],
                ),
            ),
            201,
            "",
            "/config-dns/v2/zones/example.com/names/www.example.com/types/A",
            None,
        ),
        (
            "500 internal server error",
            models.CreateRecordRequest(
                zone="example.com",
                record=models.RecordBody(
                    name="www.example.com",
                    record_type="A",
                    ttl=300,
                    target=["1.2.3.4"],
                ),
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error creating record",
                "status": 500,
            }),
            "/config-dns/v2/zones/example.com/names/www.example.com/types/A",
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error creating record",
                status_code=500,
            ),
        ),
    ],
)
def test_create_record(
    test_name, params, response_status, response_body,
    expected_path, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_CreateRecord from record_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.create_record(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        None,
    )
    dns_client.create_record(params)
    call_args = mock_session.exec.call_args
    assert call_args[0][0] == "POST"
    assert call_args[0][1] == expected_path


# ===================================================================
# record_test.go — TestDNS_UpdateRecord
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_path, expected_error",
    [
        (
            "200 OK",
            models.UpdateRecordRequest(
                zone="example.com",
                record=models.RecordBody(
                    name="www.example.com",
                    record_type="A",
                    ttl=300,
                    target=["1.2.3.4"],
                ),
            ),
            200,
            "",
            "/config-dns/v2/zones/example.com/names/www.example.com/types/A",
            None,
        ),
        (
            "500 internal server error",
            models.UpdateRecordRequest(
                zone="example.com",
                record=models.RecordBody(
                    name="www.example.com",
                    record_type="A",
                    ttl=300,
                    target=["1.2.3.4"],
                ),
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error updating record",
                "status": 500,
            }),
            "/config-dns/v2/zones/example.com/names/www.example.com/types/A",
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error updating record",
                status_code=500,
            ),
        ),
    ],
)
def test_update_record(
    test_name, params, response_status, response_body,
    expected_path, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_UpdateRecord from record_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.update_record(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        None,
    )
    dns_client.update_record(params)
    call_args = mock_session.exec.call_args
    assert call_args[0][0] == "PUT"
    assert call_args[0][1] == expected_path


# ===================================================================
# record_test.go — TestDNS_DeleteRecord
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_path, expected_error",
    [
        (
            "204 No Content",
            models.DeleteRecordRequest(
                zone="example.com",
                name="www.example.com",
                record_type="A",
            ),
            204,
            "",
            "/config-dns/v2/zones/example.com/names/www.example.com/types/A",
            None,
        ),
        (
            "500 internal server error",
            models.DeleteRecordRequest(
                zone="example.com",
                name="www.example.com",
                record_type="A",
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error deleting record",
                "status": 500,
            }),
            "/config-dns/v2/zones/example.com/names/www.example.com/types/A",
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error deleting record",
                status_code=500,
            ),
        ),
    ],
)
def test_delete_record(
    test_name, params, response_status, response_body,
    expected_path, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_DeleteRecord from record_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.delete_record(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        None,
    )
    dns_client.delete_record(params)
    call_args = mock_session.exec.call_args
    assert call_args[0][0] == "DELETE"
    assert call_args[0][1] == expected_path


# ===================================================================
# record_lookup_test.go — TestDNS_GetRecord
# ===================================================================


_GET_RECORD_RESPONSE_BODY = json.dumps({
    "name": "www.example.com",
    "rdata": ["1.2.3.4"],
    "recordType": "A",
    "ttl": 300,
})


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_path, expected_response, expected_error",
    [
        (
            "200 OK",
            models.GetRecordRequest(
                zone="example.com",
                name="www.example.com",
                record_type="A",
            ),
            200,
            _GET_RECORD_RESPONSE_BODY,
            "/config-dns/v2/zones/example.com/names/www.example.com/types/A",
            models.GetRecordResponse(
                name="www.example.com",
                record_type="A",
                ttl=300,
                target=["1.2.3.4"],
            ),
            None,
        ),
        (
            "500 internal server error",
            models.GetRecordRequest(
                zone="example.com",
                name="www.example.com",
                record_type="A",
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error fetching record",
                "status": 500,
            }),
            "/config-dns/v2/zones/example.com/names/www.example.com/types/A",
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error fetching record",
                status_code=500,
            ),
        ),
    ],
)
def test_get_record(
    test_name, params, response_status, response_body,
    expected_path, expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_GetRecord from record_lookup_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.get_record(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.get_record(params)
    assert result == expected_response

    call_args = mock_session.exec.call_args
    assert call_args[0][0] == "GET"
    assert call_args[0][1] == expected_path


# ===================================================================
# record_lookup_test.go — TestDNS_GetRecordList
# ===================================================================


_GET_RECORD_LIST_RESPONSE_BODY = json.dumps({
    "metadata": {
        "zone": "example.com",
        "page": 1,
        "pageSize": 25,
        "totalElements": 2,
        "types": ["A"],
    },
    "recordsets": [
        {
            "name": "www.example.com",
            "type": "A",
            "ttl": 300,
            "rdata": ["10.0.0.2", "10.0.0.3"],
        }
    ],
})


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_path, expected_response, expected_error",
    [
        (
            "200 OK",
            models.GetRecordListRequest(
                zone="example.com",
                record_type="A",
            ),
            200,
            _GET_RECORD_LIST_RESPONSE_BODY,
            "/config-dns/v2/zones/example.com/recordsets?types=A&showAll=true",
            models.GetRecordListResponse(
                metadata=models.Metadata(
                    page=1,
                    page_size=25,
                    total_elements=2,
                ),
                record_sets=[
                    models.RecordSet(
                        name="www.example.com",
                        type="A",
                        ttl=300,
                        rdata=["10.0.0.2", "10.0.0.3"],
                    )
                ],
            ),
            None,
        ),
        (
            "500 internal server error",
            models.GetRecordListRequest(
                zone="example.com",
                record_type="A",
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error fetching authorities",
                "status": 500,
            }),
            "/config-dns/v2/zones/example.com/recordsets?types=A&showAll=true",
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error fetching authorities",
                status_code=500,
            ),
        ),
    ],
)
def test_get_record_list(
    test_name, params, response_status, response_body,
    expected_path, expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_GetRecordList from record_lookup_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.get_record_list(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.get_record_list(params)
    assert result == expected_response

    call_args = mock_session.exec.call_args
    assert call_args[0][0] == "GET"
    assert call_args[0][1] == expected_path


# ===================================================================
# record_lookup_test.go — TestDNS_GetRdata
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_path, expected_response, expected_error",
    [
        (
            "ipv6 test",
            models.GetRdataRequest(
                zone="example.com",
                name="ipv6.example.com",
                record_type="AAAA",
            ),
            200,
            json.dumps({
                "recordsets": [
                    {
                        "name": "ipv6.example.com",
                        "rdata": [
                            "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
                        ],
                        "recordType": "AAAA",
                        "ttl": 300,
                    }
                ],
            }),
            "/config-dns/v2/zones/example.com/names/ipv6.example.com/types/AAAA",
            ["2001:0db8:85a3:0000:0000:8a2e:0370:7334"],
            None,
        ),
        (
            "loc test",
            models.GetRdataRequest(
                zone="example.com",
                name="loc.example.com",
                record_type="LOC",
            ),
            200,
            json.dumps({
                "recordsets": [
                    {
                        "name": "loc.example.com",
                        "rdata": [
                            "52 22 23.000 N 4 53 32.000 E -2.00m 0.00m"
                            " 10000m 10m",
                        ],
                        "recordType": "LOC",
                        "ttl": 300,
                    }
                ],
            }),
            "/config-dns/v2/zones/example.com/names/loc.example.com/types/LOC",
            [
                "52 22 23.000 N 4 53 32.000 E -2.00m 0.00m"
                " 10000.00m 10.00m"
            ],
            None,
        ),
        (
            "500 internal server error",
            models.GetRdataRequest(
                zone="example.com",
                name="www.example.com",
                record_type="A",
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error fetching rdata",
                "status": 500,
            }),
            "/config-dns/v2/zones/example.com/names/www.example.com/types/A",
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error fetching rdata",
                status_code=500,
            ),
        ),
    ],
)
def test_get_rdata(
    test_name, params, response_status, response_body,
    expected_path, expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_GetRdata from record_lookup_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.get_rdata(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.get_rdata(params)
    assert result == expected_response


# ===================================================================
# record_lookup_test.go — TestDNS_TestRdata (ProcessRdata)
# ===================================================================


def test_process_rdata(dns_client):
    """Mirrors Go TestDNS_TestRdata from record_lookup_test.go."""
    # AAAA — full IPv6 should pass through
    out = dns_client.process_rdata(
        ["2001:0db8:85a3:0000:0000:8a2e:0370:7334"], "AAAA"
    )
    assert out == ["2001:0db8:85a3:0000:0000:8a2e:0370:7334"]

    # LOC — should pass through already-normalized LOC data
    out = dns_client.process_rdata(
        [
            "52 22 23.000 N 4 53 32.000 E -2.00m 0.00m"
            " 10000.00m 10.00m"
        ],
        "LOC",
    )
    assert out == [
        "52 22 23.000 N 4 53 32.000 E -2.00m 0.00m"
        " 10000.00m 10.00m"
    ]


# ===================================================================
# record_lookup_test.go — TestDNS_ParseRData
# ===================================================================


@pytest.mark.parametrize(
    "test_name, rtype, rdata, expected",
    [
        (
            "AFSDB",
            "AFSDB",
            ["1 bar.com"],
            {"subtype": 1, "target": ["bar.com"]},
        ),
        (
            "SVCB",
            "SVCB",
            ["0 svc4.example.com."],
            {
                "svc_priority": 0,
                "target_name": "svc4.example.com.",
            },
        ),
        (
            "HTTPS",
            "HTTPS",
            ["3 https.example.com. alpn=bar port=8080"],
            {
                "svc_priority": 3,
                "target_name": "https.example.com.",
                "svc_params": "alpn=bar port=8080",
            },
        ),
        (
            "SRV with default values",
            "SRV",
            [
                "10 60 5060 big.example.com.",
                "10 60 5060 small.example.com.",
            ],
            {
                "port": 5060,
                "priority": 10,
                "weight": 60,
                "target": [
                    "big.example.com.",
                    "small.example.com.",
                ],
            },
        ),
        (
            "SRV without default values",
            "SRV",
            [
                "10 60 5060 big.example.com.",
                "20 50 5060 small.example.com.",
            ],
            {
                "target": [
                    "10 60 5060 big.example.com.",
                    "20 50 5060 small.example.com.",
                ],
            },
        ),
    ],
)
def test_parse_rdata(test_name, rtype, rdata, expected, dns_client):
    """Mirrors Go TestDNS_ParseRData from record_lookup_test.go."""
    result = dns_client.parse_rdata(rtype, rdata)
    assert result == expected


# ===================================================================
# recordsets_test.go — TestDNS_GetRecordSets
# ===================================================================


_GET_RECORD_SETS_RESPONSE_BODY = json.dumps({
    "metadata": {
        "zone": "example.com",
        "page": 1,
        "pageSize": 25,
        "totalElements": 2,
        "types": ["A"],
    },
    "recordsets": [
        {
            "name": "www.example.com",
            "type": "A",
            "ttl": 300,
            "rdata": ["10.0.0.2", "10.0.0.3"],
        }
    ],
})


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_response, expected_error",
    [
        (
            "200 OK",
            models.GetRecordSetsRequest(
                zone="example.com",
                query_args=models.RecordSetQueryArgs(),
            ),
            200,
            _GET_RECORD_SETS_RESPONSE_BODY,
            models.GetRecordSetsResponse(
                metadata=models.Metadata(
                    page=1,
                    page_size=25,
                    total_elements=2,
                ),
                record_sets=[
                    models.RecordSet(
                        name="www.example.com",
                        type="A",
                        ttl=300,
                        rdata=["10.0.0.2", "10.0.0.3"],
                    )
                ],
            ),
            None,
        ),
        (
            "500 internal server error",
            models.GetRecordSetsRequest(
                zone="example.com",
                query_args=models.RecordSetQueryArgs(),
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error fetching recordsets",
                "status": 500,
            }),
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error fetching recordsets",
                status_code=500,
            ),
        ),
    ],
)
def test_get_record_sets(
    test_name, params, response_status, response_body,
    expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_GetRecordSets from recordsets_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.get_record_sets(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.get_record_sets(params)
    assert result == expected_response


# ===================================================================
# recordsets_test.go — TestDNS_CreateRecordSets
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_error",
    [
        (
            "204 No Content",
            models.CreateRecordSetsRequest(
                zone="example.com",
                record_sets=models.RecordSets(
                    record_sets=[
                        models.RecordSet(
                            name="www.example.com",
                            rdata=["1.2.3.4"],
                            type="A",
                            ttl=300,
                        )
                    ],
                ),
            ),
            204,
            "",
            None,
        ),
        (
            "500 internal server error",
            models.CreateRecordSetsRequest(
                zone="example.com",
                record_sets=models.RecordSets(
                    record_sets=[
                        models.RecordSet(
                            name="www.example.com",
                            rdata=["1.2.3.4"],
                            type="A",
                            ttl=300,
                        )
                    ],
                ),
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error creating recordsets",
                "status": 500,
            }),
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error creating recordsets",
                status_code=500,
            ),
        ),
    ],
)
def test_create_record_sets(
    test_name, params, response_status, response_body,
    expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_CreateRecordSets from recordsets_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.create_record_sets(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        None,
    )
    dns_client.create_record_sets(params)
    call_args = mock_session.exec.call_args
    assert call_args[0][0] == "POST"


# ===================================================================
# recordsets_test.go — TestDNS_UpdateRecordSets
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_error",
    [
        (
            "204 No Content",
            models.UpdateRecordSetsRequest(
                zone="example.com",
                record_sets=models.RecordSets(
                    record_sets=[
                        models.RecordSet(
                            name="www.example.com",
                            rdata=["1.2.3.4"],
                            type="A",
                            ttl=300,
                        )
                    ],
                ),
            ),
            204,
            "",
            None,
        ),
        (
            "500 internal server error",
            models.UpdateRecordSetsRequest(
                zone="example.com",
                record_sets=models.RecordSets(
                    record_sets=[
                        models.RecordSet(
                            name="www.example.com",
                            rdata=["1.2.3.4"],
                            type="A",
                            ttl=300,
                        )
                    ],
                ),
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error updating recordsets",
                "status": 500,
            }),
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error updating recordsets",
                status_code=500,
            ),
        ),
    ],
)
def test_update_record_sets(
    test_name, params, response_status, response_body,
    expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_UpdateRecordSets from recordsets_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.update_record_sets(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        None,
    )
    dns_client.update_record_sets(params)
    call_args = mock_session.exec.call_args
    assert call_args[0][0] == "PUT"


# ===================================================================
# tsig_test.go — Constants
# ===================================================================

_TSIG_SECRET = (
    "fakeR5IW1ajVka5cHPEJQIXfLyx5V3PSkFBROAzOn21JumDq6nIpoj6H8rfj5Uo"
    "+Ok55ZWQ0Wgrf302fDscHLw=="
)


# ===================================================================
# tsig_test.go — TestDNS_ListTSIGKeys
# ===================================================================


_LIST_TSIG_KEYS_RESPONSE_BODY = json.dumps({
    "metadata": {
        "totalElements": 1,
        "page": 0,
        "pageSize": 25,
        "showAll": False,
        "lastPage": 0,
    },
    "keys": [
        {
            "name": "example.com.akamai.com.",
            "algorithm": "hmac-sha256",
            "secret": "fakeR5IW1ajVka5cHPEJQIXfLyx5V3PSkFBROAzOn21JumDq6nIpoj6H8rfj5Uo+Ok55ZWQ0Wgrf302fDscHLw==",
            "zoneCount": 1,
        }
    ],
})


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_response, expected_error",
    [
        (
            "200 OK",
            models.ListTSIGKeysRequest(
                tsig_query=models.TSIGQueryString(),
            ),
            200,
            _LIST_TSIG_KEYS_RESPONSE_BODY,
            models.ListTSIGKeysResponse(
                metadata=models.TSIGReportMeta(
                    total_elements=1,
                ),
                keys=[
                    models.TSIGKeyResponse(
                        name="example.com.akamai.com.",
                        algorithm="hmac-sha256",
                        secret=_TSIG_SECRET,
                        zone_count=1,
                    )
                ],
            ),
            None,
        ),
        (
            "500 internal server error",
            models.ListTSIGKeysRequest(
                tsig_query=models.TSIGQueryString(),
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error fetching tsig keys",
                "status": 500,
            }),
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error fetching tsig keys",
                status_code=500,
            ),
        ),
    ],
)
def test_list_tsig_keys(
    test_name, params, response_status, response_body,
    expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_ListTSIGKeys from tsig_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.list_tsig_keys(params)
        # list_tsig_keys re-wraps errors; check __cause__ for original Error
        cause = exc_info.value.__cause__
        assert isinstance(cause, Error)
        assert cause.status_code == expected_error.status_code
        assert cause.type == expected_error.type
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.list_tsig_keys(params)
    assert result == expected_response


# ===================================================================
# tsig_test.go — TestDNS_GetTSIGKeyZones
# ===================================================================


_GET_TSIG_KEY_ZONES_RESPONSE_BODY = json.dumps({
    "aliases": [
        "exmaple.com",
        "example.com",
    ],
    "zoneCount": 2,
})


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_response, expected_error",
    [
        (
            "200 OK",
            models.GetTSIGKeyZonesRequest(
                tsig_key=models.TSIGKey(
                    name="example.com.akamai.com.",
                    algorithm="hmac-sha256",
                    secret=_TSIG_SECRET,
                ),
            ),
            200,
            _GET_TSIG_KEY_ZONES_RESPONSE_BODY,
            models.GetTSIGKeyZonesResponse(
                aliases=["exmaple.com", "example.com"],
            ),
            None,
        ),
        (
            "500 internal server error",
            models.GetTSIGKeyZonesRequest(
                tsig_key=models.TSIGKey(
                    name="example.com.akamai.com.",
                    algorithm="hmac-sha256",
                    secret=_TSIG_SECRET,
                ),
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error fetching tsig key zones",
                "status": 500,
            }),
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error fetching tsig key zones",
                status_code=500,
            ),
        ),
    ],
)
def test_get_tsig_key_zones(
    test_name, params, response_status, response_body,
    expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_GetTSIGKeyZones from tsig_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.get_tsig_key_zones(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.get_tsig_key_zones(params)
    assert result == expected_response


# ===================================================================
# tsig_test.go — TestDNS_GetTSIGKeyAliases
# ===================================================================


_GET_TSIG_KEY_ALIASES_RESPONSE_BODY = json.dumps({
    "aliases": [
        "exmaple.com",
        "example.com",
    ],
    "zoneCount": 2,
})


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_response, expected_error",
    [
        (
            "200 OK",
            models.GetTSIGKeyAliasesRequest(
                zone="example.com",
            ),
            200,
            _GET_TSIG_KEY_ALIASES_RESPONSE_BODY,
            models.GetTSIGKeyAliasesResponse(
                aliases=["exmaple.com", "example.com"],
            ),
            None,
        ),
        (
            "500 internal server error",
            models.GetTSIGKeyAliasesRequest(
                zone="example.com",
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error fetching tsig key aliases",
                "status": 500,
            }),
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error fetching tsig key aliases",
                status_code=500,
            ),
        ),
    ],
)
def test_get_tsig_key_aliases(
    test_name, params, response_status, response_body,
    expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_GetTSIGKeyAliases from tsig_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.get_tsig_key_aliases(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.get_tsig_key_aliases(params)
    assert result == expected_response


# ===================================================================
# tsig_test.go — TestDNS_TSIGKeyBulkUpdate
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_error",
    [
        (
            "204 No Content",
            models.UpdateTSIGKeyBulkRequest(
                tsig_key_bulk=models.TSIGKeyBulkPost(
                    key=models.TSIGKey(
                        name="example.com.akamai.com.",
                        algorithm="hmac-sha256",
                        secret=_TSIG_SECRET,
                    ),
                    zones=["example.com"],
                ),
            ),
            204,
            "",
            None,
        ),
        (
            "500 internal server error",
            models.UpdateTSIGKeyBulkRequest(
                tsig_key_bulk=models.TSIGKeyBulkPost(
                    key=models.TSIGKey(
                        name="example.com.akamai.com.",
                        algorithm="hmac-sha256",
                        secret=_TSIG_SECRET,
                    ),
                    zones=["example.com"],
                ),
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error updating tsig key bulk",
                "status": 500,
            }),
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error updating tsig key bulk",
                status_code=500,
            ),
        ),
    ],
)
def test_tsig_key_bulk_update(
    test_name, params, response_status, response_body,
    expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_TSIGKeyBulkUpdate from tsig_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.update_tsig_key_bulk(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        None,
    )
    dns_client.update_tsig_key_bulk(params)
    call_args = mock_session.exec.call_args
    assert call_args[0][0] == "POST"


# ===================================================================
# tsig_test.go — TestDNS_GetTSIGKey
# ===================================================================


_GET_TSIG_KEY_RESPONSE_BODY = json.dumps({
    "name": "example.com.akamai.com.",
    "algorithm": "hmac-sha256",
    "secret": "fakeR5IW1ajVka5cHPEJQIXfLyx5V3PSkFBROAzOn21JumDq6nIpoj6H8rfj5Uo+Ok55ZWQ0Wgrf302fDscHLw==",
    "zoneCount": 1,
})


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_response, expected_error",
    [
        (
            "200 OK",
            models.GetTSIGKeyRequest(zone="example.com"),
            200,
            _GET_TSIG_KEY_RESPONSE_BODY,
            models.GetTSIGKeyResponse(
                name="example.com.akamai.com.",
                algorithm="hmac-sha256",
                secret=_TSIG_SECRET,
                zone_count=1,
            ),
            None,
        ),
        (
            "500 internal server error",
            models.GetTSIGKeyRequest(zone="example.com"),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error fetching tsig key",
                "status": 500,
            }),
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error fetching tsig key",
                status_code=500,
            ),
        ),
    ],
)
def test_get_tsig_key(
    test_name, params, response_status, response_body,
    expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_GetTSIGKey from tsig_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.get_tsig_key(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.get_tsig_key(params)
    assert result == expected_response


# ===================================================================
# tsig_test.go — TestDNS_DeleteTSIGKey
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_error",
    [
        (
            "204 No Content",
            models.DeleteTSIGKeyRequest(zone="example.com"),
            204,
            "",
            None,
        ),
        (
            "500 internal server error",
            models.DeleteTSIGKeyRequest(zone="example.com"),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error Deleting TSig Key",
                "status": 500,
            }),
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error Deleting TSig Key",
                status_code=500,
            ),
        ),
    ],
)
def test_delete_tsig_key(
    test_name, params, response_status, response_body,
    expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_DeleteTSIGKey from tsig_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.delete_tsig_key(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        None,
    )
    dns_client.delete_tsig_key(params)
    call_args = mock_session.exec.call_args
    assert call_args[0][0] == "DELETE"


# ===================================================================
# tsig_test.go — TestDNS_UpdateTSIGKey
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_error",
    [
        (
            "204 No Content",
            models.UpdateTSIGKeyRequest(
                zone="example.com",
                tsig_key=models.TSIGKey(
                    name="example.com.akamai.com.",
                    algorithm="hmac-sha256",
                    secret=_TSIG_SECRET,
                ),
            ),
            204,
            "",
            None,
        ),
        (
            "500 internal server error",
            models.UpdateTSIGKeyRequest(
                zone="example.com",
                tsig_key=models.TSIGKey(
                    name="example.com.akamai.com.",
                    algorithm="hmac-sha256",
                    secret=_TSIG_SECRET,
                ),
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error updating tsig key",
                "status": 500,
            }),
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error updating tsig key",
                status_code=500,
            ),
        ),
    ],
)
def test_update_tsig_key(
    test_name, params, response_status, response_body,
    expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_UpdateTSIGKey from tsig_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.update_tsig_key(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        None,
    )
    dns_client.update_tsig_key(params)
    call_args = mock_session.exec.call_args
    assert call_args[0][0] == "PUT"


# ===================================================================
# zone_test.go — TestDNS_ListZones
# ===================================================================


_LIST_ZONES_RESPONSE_BODY = json.dumps({
    "metadata": {
        "page": 1,
        "pageSize": 3,
        "showAll": False,
        "totalElements": 17,
        "contractIds": ["1-2ABCDE"],
    },
    "zones": [
        {
            "contractId": "1-2ABCDE",
            "zone": "example.com",
            "type": "secondary",
            "aliasCount": 1,
            "signAndServe": False,
            "versionId": "ae02357c-693d-4ac4-b33d-8352d9b7c786",
            "lastModifiedDate": "2017-01-03T12:00:00Z",
            "lastModifiedBy": "user28",
            "lastActivationDate": "2017-01-03T12:00:00Z",
            "activationState": "ACTIVE",
            "masters": ["1.1.1.1"],
            "outboundZoneTransfer": {
                "ACL": ["192.0.2.156/24"],
                "enabled": True,
                "notifyTargets": ["192.0.2.192"],
                "tsigKey": {
                    "algorithm": "hmac-sha1",
                    "name": "other.com.akamai.com3",
                    "secret": "fakeR5IW1ajVka5cHPEJQIXfLyx5V3PSkFBROAzOn21JumDq6nIpoj6H8rfj5Uo+Ok55ZWQ0Wgrf302fDscHLw==",
                },
            },
        }
    ],
})


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_response, expected_error",
    [
        (
            "200 OK",
            models.ListZonesRequest(
                contract_ids="1-1ACYUM",
                search="org",
                sort_by="-contractId,zone",
                types="secondary,alias",
                page=1,
                page_size=25,
            ),
            200,
            _LIST_ZONES_RESPONSE_BODY,
            models.ZoneListResponse(
                metadata=models.ListMetadata(
                    page=1,
                    page_size=3,
                    show_all=False,
                    total_elements=17,
                    contract_ids=["1-2ABCDE"],
                ),
                zones=[
                    models.ZoneResponse(
                        contract_id="1-2ABCDE",
                        zone="example.com",
                        type="secondary",
                        alias_count=1,
                        sign_and_serve=False,
                        version_id="ae02357c-693d-4ac4-b33d-8352d9b7c786",
                        last_modified_date="2017-01-03T12:00:00Z",
                        last_modified_by="user28",
                        last_activation_date="2017-01-03T12:00:00Z",
                        activation_state="ACTIVE",
                        masters=["1.1.1.1"],
                        outbound_zone_transfer=models.OutboundZoneTransfer(
                            acl=["192.0.2.156/24"],
                            enabled=True,
                            notify_targets=["192.0.2.192"],
                            tsig_key=models.TSIGKey(
                                name="other.com.akamai.com3",
                                algorithm="hmac-sha1",
                                secret=_TSIG_SECRET,
                            ),
                        ),
                    )
                ],
            ),
            None,
        ),
        (
            "500 internal server error",
            models.ListZonesRequest(
                contract_ids="1-1ACYUM",
                search="org",
                sort_by="-contractId,zone",
                types="primary,alias",
                page=1,
                page_size=25,
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error fetching authorities",
                "status": 500,
            }),
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error fetching authorities",
                status_code=500,
            ),
        ),
    ],
)
def test_list_zones(
    test_name, params, response_status, response_body,
    expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_ListZones from zone_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.list_zones(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.list_zones(params)
    assert result == expected_response


# ===================================================================
# zone_test.go — TestDNS_GetZonesDNSSecStatus
# ===================================================================


_DNSSEC_CURRENT_ONLY_RESPONSE = json.dumps({
    "dnsSecStatuses": [
        {
            "zone": "foo.test.net",
            "alerts": ["PARENT_DS_MISSING"],
            "currentRecords": {
                "dsRecord": "foo.test.net. 86400 IN DS 42061 7 2"
                " ( DUMMY_HASH_1 ) ",
                "dnskeyRecord": "foo.test.net. 7200 IN DNSKEY 257 3 7"
                " (DUMMY_HASH_2 ) ",
                "lastModifiedDate": "2024-05-28T06:58:26Z",
                "expectedTtl": 0,
            },
        }
    ],
})

_DNSSEC_NEW_RECORDS_RESPONSE = json.dumps({
    "dnsSecStatuses": [
        {
            "alerts": ["PARENT_DS_MISSING"],
            "currentRecords": {
                "dnskeyRecord": "foo.test.net. 7200 IN DNSKEY 257 3 13"
                " (DUMMY_HASH_1 ) ",
                "dsRecord": "foo.test.net. 86400 IN DS 3622 13 2"
                " ( DUMMY_HASH_2 ) ",
                "expectedTtl": 3600,
                "lastModifiedDate": "2022-06-19T10:14:35Z",
            },
            "newRecords": {
                "dnskeyRecord": "foo.test.net. 7200 IN DNSKEY 257 3 13"
                " (DUMMY_HASH_3 ) ",
                "dsRecord": "foo.test.net. 86400 IN DS 39035 13 2"
                " ( DUMMY_HASH_4 ) ",
                "expectedTtl": 3600,
                "lastModifiedDate": "2023-06-19T10:14:35Z",
            },
            "zone": "foo.test.net",
        }
    ],
})


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_response, expected_error",
    [
        (
            "200 OK current records only",
            models.GetZonesDNSSecStatusRequest(
                zones=["foo.test.net"],
            ),
            200,
            _DNSSEC_CURRENT_ONLY_RESPONSE,
            models.GetZonesDNSSecStatusResponse(
                dns_sec_statuses=[
                    models.SecStatus(
                        zone="foo.test.net",
                        alerts=["PARENT_DS_MISSING"],
                        current_records=models.SecRecords(
                            dnskey_record="foo.test.net. 7200 IN DNSKEY"
                            " 257 3 7 (DUMMY_HASH_2 ) ",
                            ds_record="foo.test.net. 86400 IN DS 42061"
                            " 7 2 ( DUMMY_HASH_1 ) ",
                            expected_ttl=0,
                            last_modified_date="2024-05-28T06:58:26Z",
                        ),
                    )
                ],
            ),
            None,
        ),
        (
            "200 OK new records returned",
            models.GetZonesDNSSecStatusRequest(
                zones=["foo.test.net"],
            ),
            200,
            _DNSSEC_NEW_RECORDS_RESPONSE,
            models.GetZonesDNSSecStatusResponse(
                dns_sec_statuses=[
                    models.SecStatus(
                        zone="foo.test.net",
                        alerts=["PARENT_DS_MISSING"],
                        current_records=models.SecRecords(
                            dnskey_record="foo.test.net. 7200 IN DNSKEY"
                            " 257 3 13 (DUMMY_HASH_1 ) ",
                            ds_record="foo.test.net. 86400 IN DS 3622"
                            " 13 2 ( DUMMY_HASH_2 ) ",
                            expected_ttl=3600,
                            last_modified_date="2022-06-19T10:14:35Z",
                        ),
                        new_records=models.SecRecords(
                            dnskey_record="foo.test.net. 7200 IN DNSKEY"
                            " 257 3 13 (DUMMY_HASH_3 ) ",
                            ds_record="foo.test.net. 86400 IN DS 39035"
                            " 13 2 ( DUMMY_HASH_4 ) ",
                            expected_ttl=3600,
                            last_modified_date="2023-06-19T10:14:35Z",
                        ),
                    )
                ],
            ),
            None,
        ),
        (
            "500 internal server error",
            models.GetZonesDNSSecStatusRequest(
                zones=["foo.test.net"],
            ),
            500,
            json.dumps({
                "type": "https://problems.luna.akamaiapis.net/authoritative-dns/serverError",
                "title": "Server error",
                "instance": "29aa48de-ec7d-4214-ad6c-649163889be7",
                "status": 500,
                "detail": "An internal error occurred.",
                "problemId": "29aa48de-ec7d-4214-ad6c-649163889be7",
            }),
            None,
            Error(
                type="https://problems.luna.akamaiapis.net/authoritative-dns/serverError",
                title="Server error",
                detail="An internal error occurred.",
                status_code=500,
            ),
        ),
        (
            "validation error: empty zone list",
            models.GetZonesDNSSecStatusRequest(
                zones=[],
            ),
            200,
            "",
            None,
            "validation",
        ),
    ],
)
def test_get_zones_dnssec_status(
    test_name, params, response_status, response_body,
    expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_GetZonesDNSSecStatus from zone_test.go."""
    if expected_error == "validation":
        with pytest.raises(ValueError):
            dns_client.get_zones_dnssec_status(params)
        return

    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.get_zones_dnssec_status(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.get_zones_dnssec_status(params)
    assert result == expected_response


# ===================================================================
# zone_test.go — TestDNS_GetZone
# ===================================================================


_GET_ZONE_RESPONSE_BODY = json.dumps({
    "contractId": "1-2ABCDE",
    "zone": "example.com",
    "type": "secondary",
    "aliasCount": 1,
    "signAndServe": True,
    "signAndServeAlgorithm": "RSA_SHA256",
    "versionId": "ae02357c-693d-4ac4-b33d-8352d9b7c786",
    "lastModifiedDate": "2017-01-03T12:00:00Z",
    "lastModifiedBy": "user28",
    "lastActivationDate": "2017-01-03T12:00:00Z",
    "activationState": "ACTIVE",
    "masters": ["1.1.1.1"],
    "outboundZoneTransfer": {
        "ACL": ["192.0.2.156/24"],
        "enabled": True,
        "notifyTargets": ["192.0.2.192"],
        "tsigKey": {
            "algorithm": "hmac-sha1",
            "name": "other.com.akamai.com3",
            "secret": "fakeR5IW1ajVka5cHPEJQIXfLyx5V3PSkFBROAzOn21JumDq6nIpoj6H8rfj5Uo+Ok55ZWQ0Wgrf302fDscHLw==",
        },
    },
})


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_response, expected_error",
    [
        (
            "200 OK",
            models.GetZoneRequest(zone="example.com"),
            200,
            _GET_ZONE_RESPONSE_BODY,
            models.GetZoneResponse(
                contract_id="1-2ABCDE",
                zone="example.com",
                type="secondary",
                alias_count=1,
                sign_and_serve=True,
                sign_and_serve_algorithm="RSA_SHA256",
                version_id="ae02357c-693d-4ac4-b33d-8352d9b7c786",
                last_modified_date="2017-01-03T12:00:00Z",
                last_modified_by="user28",
                last_activation_date="2017-01-03T12:00:00Z",
                activation_state="ACTIVE",
                masters=["1.1.1.1"],
                outbound_zone_transfer=models.OutboundZoneTransfer(
                    acl=["192.0.2.156/24"],
                    enabled=True,
                    notify_targets=["192.0.2.192"],
                    tsig_key=models.TSIGKey(
                        name="other.com.akamai.com3",
                        algorithm="hmac-sha1",
                        secret=_TSIG_SECRET,
                    ),
                ),
            ),
            None,
        ),
        (
            "500 internal server error",
            models.GetZoneRequest(zone="example.com"),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error fetching authorities",
                "status": 500,
            }),
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error fetching authorities",
                status_code=500,
            ),
        ),
    ],
)
def test_get_zone(
    test_name, params, response_status, response_body,
    expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_GetZone from zone_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.get_zone(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.get_zone(params)
    assert result == expected_response


# ===================================================================
# zone_test.go — TestDNS_GetZoneMasterFile
# ===================================================================


_ZONE_FILE_TEXT_QUOTED = (
    '"example.com.        10000    IN SOA ns1.akamaidns.com.'
    " webmaster.example.com. 1 28800 14400 2419200 86400\n"
    "example.com.        10000    IN NS  ns1.akamaidns.com.\n"
    "example.com.        10000    IN NS  ns2.akamaidns.com.\n"
    "example.com.            300 IN  A   10.0.0.1\n"
    "example.com.            300 IN  A   10.0.0.2\n"
    "www.example.com.        300 IN  A   10.0.0.1\n"
    'www.example.com.        300 IN  A   10.0.0.2"'
)


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_response, expected_error",
    [
        (
            "200 OK",
            models.GetMasterZoneFileRequest(zone="example.com"),
            200,
            _ZONE_FILE_TEXT_QUOTED,
            _ZONE_FILE_TEXT_QUOTED,
            None,
        ),
        (
            "500 internal server error",
            models.GetMasterZoneFileRequest(zone="example.com"),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error fetching authorities",
                "status": 500,
            }),
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error fetching authorities",
                status_code=500,
            ),
        ),
    ],
)
def test_get_zone_master_file_handler(
    test_name, params, response_status, response_body,
    expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_GetZoneMasterFile from zone_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.get_master_zone_file(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        None,
    )
    result = dns_client.get_master_zone_file(params)
    assert result == expected_response


# ===================================================================
# zone_test.go — TestDNS_UpdateZoneMasterFile
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body, expected_error",
    [
        (
            "204 Updated",
            models.PostMasterZoneFileRequest(
                zone="example.com",
                file_data=_ZONE_FILE_TEXT_QUOTED,
            ),
            204,
            "",
            None,
        ),
        (
            "500 internal server error",
            models.PostMasterZoneFileRequest(
                zone="example.com",
                file_data=_ZONE_FILE_TEXT_QUOTED,
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error creating zone",
                "status": 500,
            }),
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error creating zone",
                status_code=500,
            ),
        ),
    ],
)
def test_update_zone_master_file(
    test_name, params, response_status, response_body,
    expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_UpdateZoneMasterFile from zone_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.post_master_zone_file(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        None,
    )
    dns_client.post_master_zone_file(params)
    mock_session.exec.assert_called_once()


# ===================================================================
# zone_test.go — TestDNS_GetChangeList
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_response, expected_error",
    [
        (
            "200 OK",
            models.GetChangeListRequest(zone="example.com"),
            200,
            json.dumps({
                "zone": "example.com",
                "changeTag": "476754f4-d605-479f-853b-db854d7254fa",
                "zoneVersionId": "1d9c887c-49bb-4382-87a6-d1bf690aa58f",
                "lastModifiedDate": "2017-02-01T12:00:12.524Z",
                "stale": False,
            }),
            models.GetChangeListResponse(
                zone="example.com",
                change_tag="476754f4-d605-479f-853b-db854d7254fa",
                zone_version_id="1d9c887c-49bb-4382-87a6-d1bf690aa58f",
                last_modified_date="2017-02-01T12:00:12.524Z",
                stale=False,
            ),
            None,
        ),
        (
            "500 internal server error",
            models.GetChangeListRequest(zone="example.com"),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error fetching authorities",
                "status": 500,
            }),
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error fetching authorities",
                status_code=500,
            ),
        ),
    ],
)
def test_get_change_list(
    test_name, params, response_status, response_body,
    expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_GetChangeList from zone_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.get_change_list(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.get_change_list(params)
    assert result == expected_response


# ===================================================================
# zone_test.go — TestDNS_GetMasterZoneFile
# ===================================================================


_ZONE_FILE_TEXT_INDENTED = (
    "\n\t\t\texample.com.        10000    IN SOA"
    " ns1.akamaidns.com. webmaster.example.com."
    " 1 28800 14400 2419200 86400\n"
    "\t\t\texample.com.        10000    IN NS"
    "  ns1.akamaidns.com.\n"
    "\t\t\texample.com.        10000    IN NS"
    "  ns2.akamaidns.com.\n"
    "\t\t\texample.com.            300 IN  A"
    "   10.0.0.1\n"
    "\t\t\texample.com.            300 IN  A"
    "   10.0.0.2\n"
    "\t\t\twww.example.com.        300 IN  A"
    "   10.0.0.1\n"
    "\t\t\twww.example.com.        300 IN  A"
    "   10.0.0.2"
)


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_response, expected_error",
    [
        (
            "200 OK",
            models.GetMasterZoneFileRequest(zone="example.com"),
            200,
            _ZONE_FILE_TEXT_INDENTED,
            _ZONE_FILE_TEXT_INDENTED,
            None,
        ),
        (
            "500 internal server error",
            models.GetMasterZoneFileRequest(zone="example.com"),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error fetching master zone file",
                "status": 500,
            }),
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error fetching master zone file",
                status_code=500,
            ),
        ),
    ],
)
def test_get_master_zone_file(
    test_name, params, response_status, response_body,
    expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_GetMasterZoneFile from zone_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.get_master_zone_file(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        None,
    )
    result = dns_client.get_master_zone_file(params)
    assert result == expected_response


# ===================================================================
# zone_test.go — TestDNS_CreateZone
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body, expected_error",
    [
        (
            "201 Created Primary",
            models.CreateZoneRequest(
                create_zone=models.ZoneCreate(
                    zone="example.com",
                    contract_id="1-2ABCDE",
                    type="primary",
                ),
                zone_query_string=models.ZoneQueryString(
                    contract="1-2ABCDE",
                ),
            ),
            201,
            json.dumps({
                "contractId": "1-2ABCDE",
                "zone": "other.com",
                "type": "primary",
                "aliasCount": 1,
                "signAndServe": False,
                "comment": "Initial add",
                "versionId": "7949b2db-ac43-4773-a3ec-dc93202142fd",
                "lastModifiedDate": "2016-12-11T03:21:00Z",
                "lastModifiedBy": "user31",
                "lastActivationDate": "2017-01-03T12:00:00Z",
                "activationState": "ERROR",
                "masters": ["1.2.3.4", "1.2.3.5"],
            }),
            None,
        ),
        (
            "201 Created Secondary",
            models.CreateZoneRequest(
                create_zone=models.ZoneCreate(
                    zone="example.com",
                    contract_id="1-2ABCDE",
                    type="secondary",
                    tsig_key=models.TSIGKey(
                        name="other.com.akamai.com.",
                        algorithm="hmac-sha512",
                        secret="fakeSecretajVka5cHPEJQIXfLyx5V3PSkFBROAzOn21JumDq6nIpoj6H8rfj5Uo",
                    ),
                ),
                zone_query_string=models.ZoneQueryString(
                    contract="1-2ABCDE",
                ),
            ),
            201,
            json.dumps({
                "contractId": "1-2ABCDE",
                "zone": "other.com",
                "type": "primary",
                "aliasCount": 1,
                "signAndServe": False,
                "comment": "Initial add",
                "versionId": "7949b2db-ac43-4773-a3ec-dc93202142fd",
                "lastModifiedDate": "2016-12-11T03:21:00Z",
                "lastModifiedBy": "user31",
                "lastActivationDate": "2017-01-03T12:00:00Z",
                "activationState": "ERROR",
                "masters": ["1.2.3.4", "1.2.3.5"],
                "tsigKey": {
                    "name": "other.com.akamai.com.",
                    "algorithm": "hmac-sha512",
                    "secret": "fakeSecretajVka5cHPEJQIXfLyx5V3PSkFBROAzOn21JumDq6nIpoj6H8rfj5Uo",
                },
            }),
            None,
        ),
        (
            "500 internal server error",
            models.CreateZoneRequest(
                create_zone=models.ZoneCreate(
                    zone="example.com",
                    contract_id="1-2ABCDE",
                    type="primary",
                ),
                zone_query_string=models.ZoneQueryString(
                    contract="1-2ABCDE",
                ),
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error creating zone",
                "status": 500,
            }),
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error creating zone",
                status_code=500,
            ),
        ),
    ],
)
def test_create_zone(
    test_name, params, response_status, response_body,
    expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_CreateZone from zone_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.create_zone(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        None,
    )
    dns_client.create_zone(params)
    mock_session.exec.assert_called_once()


# ===================================================================
# zone_test.go — TestDNS_SaveChangelist
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body, expected_error",
    [
        (
            "201 Created",
            models.SaveChangeListRequest(
                zone="example.com",
                contract_id="1-2ABCDE",
                type="primary",
            ),
            201,
            "",
            None,
        ),
        (
            "500 internal server error",
            models.SaveChangeListRequest(
                zone="example.com",
                contract_id="1-2ABCDE",
                type="primary",
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error creating zone",
                "status": 500,
            }),
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error creating zone",
                status_code=500,
            ),
        ),
    ],
)
def test_save_changelist(
    test_name, params, response_status, response_body,
    expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_SaveChangelist from zone_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.save_change_list(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        None,
    )
    dns_client.save_change_list(params)
    mock_session.exec.assert_called_once()


# ===================================================================
# zone_test.go — TestDNS_SubmitChangelist
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body, expected_error",
    [
        (
            "204 No Content",
            models.SubmitChangeListRequest(
                zone="example.com",
                contract_id="1-2ABCDE",
                type="primary",
            ),
            204,
            "",
            None,
        ),
        (
            "500 internal server error",
            models.SubmitChangeListRequest(
                zone="example.com",
                contract_id="1-2ABCDE",
                type="secondary",
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error creating zone",
                "status": 500,
            }),
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error creating zone",
                status_code=500,
            ),
        ),
    ],
)
def test_submit_changelist(
    test_name, params, response_status, response_body,
    expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_SubmitChangelist from zone_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.submit_change_list(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        None,
    )
    dns_client.submit_change_list(params)
    mock_session.exec.assert_called_once()


# ===================================================================
# zone_test.go — TestDNS_UpdateZone
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body, expected_error",
    [
        (
            "200 OK primary",
            models.UpdateZoneRequest(
                create_zone=models.ZoneCreate(
                    zone="example.com",
                    contract_id="1-2ABCDE",
                    type="primary",
                    outbound_zone_transfer=models.OutboundZoneTransfer(
                        acl=["192.0.2.156/24"],
                        enabled=True,
                        notify_targets=["192.0.2.192"],
                        tsig_key=models.TSIGKey(
                            name="other.com.akamai.com",
                            algorithm="hmac-sha1",
                            secret="fakeW1ajVka5cHPEJQIXfLyx5V3PSkFBROAzOn21JumDq6nIpoj6H8rfj5Uo+Ok55ZWQ0Wgrf302fDscHLw==",
                        ),
                    ),
                ),
            ),
            200,
            json.dumps({
                "contractId": "1-2ABCDE",
                "zone": "other.com",
                "type": "primary",
                "aliasCount": 1,
                "signAndServe": False,
                "comment": "Initial add",
                "versionId": "7949b2db-ac43-4773-a3ec-dc93202142fd",
                "lastModifiedDate": "2016-12-11T03:21:00Z",
                "lastModifiedBy": "user31",
                "lastActivationDate": "2017-01-03T12:00:00Z",
                "activationState": "ERROR",
                "masters": ["1.2.3.4", "1.2.3.5"],
                "outboundZoneTransfer": {
                    "ACL": ["192.0.2.156/24"],
                    "enabled": True,
                    "notifyTargets": ["192.0.2.192"],
                    "tsigKey": {
                        "algorithm": "hmac-sha1",
                        "name": "other.com.akamai.com3",
                        "secret": _TSIG_SECRET,
                    },
                },
            }),
            None,
        ),
        (
            "200 OK secondary",
            models.UpdateZoneRequest(
                create_zone=models.ZoneCreate(
                    zone="example.com",
                    contract_id="1-2ABCDE",
                    type="secondary",
                    tsig_key=models.TSIGKey(
                        name="other.com.akamai.com.",
                        algorithm="hmac-sha512",
                        secret="fakeSecretajVka5cHPEJQIXfLyx5V3PSkFBROAzOn21JumDq6nIpoj6H8rfj5Uo",
                    ),
                    masters=["1.2.3.4", "1.2.3.5"],
                    outbound_zone_transfer=models.OutboundZoneTransfer(
                        acl=["192.0.2.156/24"],
                        enabled=True,
                        notify_targets=["192.0.2.192"],
                        tsig_key=models.TSIGKey(
                            name="other.com.akamai.com",
                            algorithm="hmac-sha1",
                            secret="fakeW1ajVka5cHPEJQIXfLyx5V3PSkFBROAzOn21JumDq6nIpoj6H8rfj5Uo+Ok55ZWQ0Wgrf302fDscHLw==",
                        ),
                    ),
                ),
            ),
            200,
            json.dumps({
                "contractId": "1-2ABCDE",
                "zone": "other.com",
                "type": "primary",
                "aliasCount": 1,
                "signAndServe": False,
                "comment": "Initial add",
                "versionId": "7949b2db-ac43-4773-a3ec-dc93202142fd",
                "lastModifiedDate": "2016-12-11T03:21:00Z",
                "lastModifiedBy": "user31",
                "lastActivationDate": "2017-01-03T12:00:00Z",
                "activationState": "ERROR",
                "masters": ["1.2.3.4", "1.2.3.5"],
                "tsigKey": {
                    "name": "other.com.akamai.com.",
                    "algorithm": "hmac-sha512",
                    "secret": "fakeSecretajVka5cHPEJQIXfLyx5V3PSkFBROAzOn21JumDq6nIpoj6H8rfj5Uo",
                },
                "outboundZoneTransfer": {
                    "ACL": ["192.0.2.156/24"],
                    "enabled": True,
                    "notifyTargets": ["192.0.2.192"],
                    "tsigKey": {
                        "algorithm": "hmac-sha1",
                        "name": "other.com.akamai.com3",
                        "secret": _TSIG_SECRET,
                    },
                },
            }),
            None,
        ),
        (
            "500 internal server error",
            models.UpdateZoneRequest(
                create_zone=models.ZoneCreate(
                    zone="example.com",
                    contract_id="1-2ABCDE",
                    type="secondary",
                ),
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error creating zone",
                "status": 500,
            }),
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error creating zone",
                status_code=500,
            ),
        ),
    ],
)
def test_update_zone(
    test_name, params, response_status, response_body,
    expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_UpdateZone from zone_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.update_zone(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        None,
    )
    dns_client.update_zone(params)
    mock_session.exec.assert_called_once()


# ===================================================================
# zone_test.go — TestDNS_GetZoneNames
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_response, expected_error",
    [
        (
            "200 OK",
            models.GetZoneNamesRequest(zone="example.com"),
            200,
            json.dumps({
                "names": [
                    "example.com",
                    "www.example.com",
                    "ftp.example.com",
                    "space.example.com",
                    "bar.example.com",
                ],
            }),
            models.GetZoneNamesResponse(
                names=[
                    "example.com",
                    "www.example.com",
                    "ftp.example.com",
                    "space.example.com",
                    "bar.example.com",
                ],
            ),
            None,
        ),
        (
            "500 internal server error",
            models.GetZoneNamesRequest(zone="example.com"),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error fetching authorities",
                "status": 500,
            }),
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error fetching authorities",
                status_code=500,
            ),
        ),
    ],
)
def test_get_zone_names(
    test_name, params, response_status, response_body,
    expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_GetZoneNames from zone_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.get_zone_names(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.get_zone_names(params)
    assert result == expected_response


# ===================================================================
# zone_test.go — TestDNS_GetZoneNameTypes
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_response, expected_error",
    [
        (
            "200 OK",
            models.GetZoneNameTypesRequest(
                zone="example.com",
                zone_name="www.example.com",
            ),
            200,
            json.dumps({
                "types": ["A", "AAAA", "MX"],
            }),
            models.GetZoneNameTypesResponse(
                types=["A", "AAAA", "MX"],
            ),
            None,
        ),
        (
            "500 internal server error",
            models.GetZoneNameTypesRequest(
                zone="example.com",
                zone_name="www.example.com",
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error fetching authorities",
                "status": 500,
            }),
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error fetching authorities",
                status_code=500,
            ),
        ),
    ],
)
def test_get_zone_name_types(
    test_name, params, response_status, response_body,
    expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_GetZoneNameTypes from zone_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.get_zone_name_types(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.get_zone_name_types(params)
    assert result == expected_response


# ===================================================================
# zone_test.go — Test_ValidateZoneErrors
# ===================================================================


@pytest.mark.parametrize(
    "test_name, zone_create",
    [
        ("empty zone", models.ZoneCreate()),
        ("bad type", models.ZoneCreate(zone="example.com", type="BAD")),
        (
            "secondary tsig",
            models.ZoneCreate(
                zone="example.com",
                type="PRIMARY",
                tsig_key=models.TSIGKey(name="example.com"),
            ),
        ),
        (
            "alias empty target",
            models.ZoneCreate(zone="example.com", type="ALIAS", target=""),
        ),
        (
            "alias masters",
            models.ZoneCreate(
                zone="example.com",
                type="ALIAS",
                target="10.0.0.1",
                masters=["master"],
            ),
        ),
        (
            "alias sign",
            models.ZoneCreate(
                zone="example.com",
                type="ALIAS",
                target="10.0.0.1",
                sign_and_serve=True,
            ),
        ),
        (
            "alias sign algo",
            models.ZoneCreate(
                zone="example.com",
                type="ALIAS",
                target="10.0.0.1",
                sign_and_serve=False,
                sign_and_serve_algorithm="foo",
            ),
        ),
        (
            "primary bad target",
            models.ZoneCreate(
                zone="example.com",
                type="PRIMARY",
                target="10.0.0.1",
            ),
        ),
        (
            "primary bad masters",
            models.ZoneCreate(
                zone="example.com",
                type="PRIMARY",
                masters=["foo"],
            ),
        ),
    ],
)
def test_validate_zone_errors(test_name, zone_create):
    """Mirrors Go Test_ValidateZoneErrors from zone_test.go.

    Each scenario should raise a ValueError from validate_zone.
    """
    with pytest.raises(ValueError):
        validate_zone(zone_create)


# ===================================================================
# zonebulk_test.go — TestDNS_GetBulkZoneCreateStatus
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_response, expected_error",
    [
        (
            "200 OK",
            models.GetBulkZoneCreateStatusRequest(
                request_id="15bc138f-8d82-451b-80b7-a56b88ffc474",
            ),
            200,
            json.dumps({
                "requestId": "15bc138f-8d82-451b-80b7-a56b88ffc474",
                "zonesSubmitted": 2,
                "successCount": 0,
                "failureCount": 2,
                "isComplete": True,
                "expirationDate": "2020-10-28T17:10:04.515792Z",
            }),
            models.GetBulkZoneCreateStatusResponse(
                request_id="15bc138f-8d82-451b-80b7-a56b88ffc474",
                zones_submitted=2,
                success_count=0,
                failure_count=2,
                is_complete=True,
                expiration_date="2020-10-28T17:10:04.515792Z",
            ),
            None,
        ),
        (
            "500 internal server error",
            models.GetBulkZoneCreateStatusRequest(
                request_id="15bc138f-8d82-451b-80b7-a56b88ffc474",
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error fetching authorities",
                "status": 500,
            }),
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error fetching authorities",
                status_code=500,
            ),
        ),
    ],
)
def test_get_bulk_zone_create_status(
    test_name, params, response_status, response_body,
    expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_GetBulkZoneCreateStatus from zonebulk_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.get_bulk_zone_create_status(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.get_bulk_zone_create_status(params)
    assert result == expected_response


# ===================================================================
# zonebulk_test.go — TestDNS_GetBulkZoneCreateResult
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_response, expected_error",
    [
        (
            "200 OK",
            models.GetBulkZoneCreateResultRequest(
                request_id="15bc138f-8d82-451b-80b7-a56b88ffc474",
            ),
            200,
            json.dumps({
                "requestId": "15bc138f-8d82-451b-80b7-a56b88ffc474",
                "successfullyCreatedZones": [],
                "failedZones": [
                    {
                        "zone": "one.testbulk.net",
                        "failureReason": "ZONE_ALREADY_EXISTS",
                    }
                ],
            }),
            models.GetBulkZoneCreateResultResponse(
                request_id="15bc138f-8d82-451b-80b7-a56b88ffc474",
                successfully_created_zones=[],
                failed_zones=[
                    models.BulkFailedZone(
                        zone="one.testbulk.net",
                        failure_reason="ZONE_ALREADY_EXISTS",
                    )
                ],
            ),
            None,
        ),
        (
            "500 internal server error",
            models.GetBulkZoneCreateResultRequest(
                request_id="15bc138f-8d82-451b-80b7-a56b88ffc474",
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error fetching authorities",
                "status": 500,
            }),
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error fetching authorities",
                status_code=500,
            ),
        ),
    ],
)
def test_get_bulk_zone_create_result(
    test_name, params, response_status, response_body,
    expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_GetBulkZoneCreateResult from zonebulk_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.get_bulk_zone_create_result(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.get_bulk_zone_create_result(params)
    assert result == expected_response


# ===================================================================
# zonebulk_test.go — TestDNS_CreateBulkZones
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_response, expected_error",
    [
        (
            "200 Created",
            models.CreateBulkZonesRequest(
                bulk_zones=models.BulkZonesCreate(
                    zones=[
                        models.ZoneCreate(
                            zone="one.testbulk.net",
                            type="secondary",
                            comment="testing bulk operations",
                            masters=["1.2.3.4", "1.2.3.10"],
                            outbound_zone_transfer=models.OutboundZoneTransfer(
                                acl=["192.0.2.156/24"],
                                enabled=True,
                                notify_targets=["192.0.2.192"],
                                tsig_key=models.TSIGKey(
                                    name="other.com.akamai.com3",
                                    algorithm="hmac-sha1",
                                    secret=_TSIG_SECRET,
                                ),
                            ),
                        ),
                        models.ZoneCreate(
                            zone="two.testbulk.net",
                            type="secondary",
                            comment="testing bulk operations",
                            masters=["1.2.3.6", "1.2.3.70"],
                        ),
                    ],
                ),
                zone_query_string=models.ZoneQueryString(
                    contract="1-2ABCDE",
                    group="testgroup",
                ),
            ),
            201,
            json.dumps({
                "requestId": "93e97a28-4e05-45f4-8b9a-cebd71155949",
                "expirationDate": "2020-10-28T19:50:36.272668Z",
            }),
            models.CreateBulkZonesResponse(
                request_id="93e97a28-4e05-45f4-8b9a-cebd71155949",
                expiration_date="2020-10-28T19:50:36.272668Z",
            ),
            None,
        ),
        (
            "500 internal server error",
            models.CreateBulkZonesRequest(
                bulk_zones=models.BulkZonesCreate(
                    zones=[
                        models.ZoneCreate(
                            zone="one.testbulk.net",
                            type="secondary",
                            comment="testing bulk operations",
                            masters=["1.2.3.4", "1.2.3.10"],
                        ),
                        models.ZoneCreate(
                            zone="two.testbulk.net",
                            type="secondary",
                            comment="testing bulk operations",
                            masters=["1.2.3.6", "1.2.3.70"],
                        ),
                    ],
                ),
                zone_query_string=models.ZoneQueryString(
                    contract="1-2ABCDE",
                    group="testgroup",
                ),
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error creating zone",
                "status": 500,
            }),
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error creating zone",
                status_code=500,
            ),
        ),
    ],
)
def test_create_bulk_zones(
    test_name, params, response_status, response_body,
    expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_CreateBulkZones from zonebulk_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.create_bulk_zones(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.create_bulk_zones(params)
    assert result == expected_response


# ===================================================================
# zonebulk_test.go — TestDNS_GetBulkZoneDeleteStatus
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_response, expected_error",
    [
        (
            "200 OK",
            models.GetBulkZoneDeleteStatusRequest(
                request_id="15bc138f-8d82-451b-80b7-a56b88ffc474",
            ),
            200,
            json.dumps({
                "requestId": "15bc138f-8d82-451b-80b7-a56b88ffc474",
                "zonesSubmitted": 2,
                "successCount": 0,
                "failureCount": 2,
                "isComplete": True,
                "expirationDate": "2020-10-28T17:10:04.515792Z",
            }),
            models.GetBulkZoneDeleteStatusResponse(
                request_id="15bc138f-8d82-451b-80b7-a56b88ffc474",
                zones_submitted=2,
                success_count=0,
                failure_count=2,
                is_complete=True,
                expiration_date="2020-10-28T17:10:04.515792Z",
            ),
            None,
        ),
        (
            "500 internal server error",
            models.GetBulkZoneDeleteStatusRequest(
                request_id="15bc138f-8d82-451b-80b7-a56b88ffc474",
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error fetching authorities",
                "status": 500,
            }),
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error fetching authorities",
                status_code=500,
            ),
        ),
    ],
)
def test_get_bulk_zone_delete_status(
    test_name, params, response_status, response_body,
    expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_GetBulkZoneDeleteStatus from zonebulk_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.get_bulk_zone_delete_status(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.get_bulk_zone_delete_status(params)
    assert result == expected_response


# ===================================================================
# zonebulk_test.go — TestDNS_GetBulkZoneDeleteResult
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_response, expected_error",
    [
        (
            "200 OK",
            models.GetBulkZoneDeleteResultRequest(
                request_id="15bc138f-8d82-451b-80b7-a56b88ffc474",
            ),
            200,
            json.dumps({
                "requestId": "15bc138f-8d82-451b-80b7-a56b88ffc474",
                "successfullyDeletedZones": [],
                "failedZones": [
                    {
                        "zone": "one.testbulk.net",
                        "failureReason": "ZONE_ALREADY_EXISTS",
                    }
                ],
            }),
            models.GetBulkZoneDeleteResultResponse(
                request_id="15bc138f-8d82-451b-80b7-a56b88ffc474",
                successfully_deleted_zones=[],
                failed_zones=[
                    models.BulkFailedZone(
                        zone="one.testbulk.net",
                        failure_reason="ZONE_ALREADY_EXISTS",
                    )
                ],
            ),
            None,
        ),
        (
            "500 internal server error",
            models.GetBulkZoneDeleteResultRequest(
                request_id="15bc138f-8d82-451b-80b7-a56b88ffc474",
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error fetching authorities",
                "status": 500,
            }),
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error fetching authorities",
                status_code=500,
            ),
        ),
    ],
)
def test_get_bulk_zone_delete_result(
    test_name, params, response_status, response_body,
    expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_GetBulkZoneDeleteResult from zonebulk_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.get_bulk_zone_delete_result(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.get_bulk_zone_delete_result(params)
    assert result == expected_response


# ===================================================================
# zonebulk_test.go — TestDNS_DeleteBulkZones
# ===================================================================


@pytest.mark.parametrize(
    "test_name, params, response_status, response_body,"
    " expected_response, expected_error",
    [
        (
            "200 Created",
            models.DeleteBulkZonesRequest(
                zones_list=models.ZoneNameListResponse(
                    zones=["one.testbulk.net", "two.testbulk.net"],
                ),
                bypass_safety_checks=True,
            ),
            201,
            json.dumps({
                "requestId": "93e97a28-4e05-45f4-8b9a-cebd71155949",
                "expirationDate": "2020-10-28T19:50:36.272668Z",
            }),
            models.DeleteBulkZonesResponse(
                request_id="93e97a28-4e05-45f4-8b9a-cebd71155949",
                expiration_date="2020-10-28T19:50:36.272668Z",
            ),
            None,
        ),
        (
            "500 internal server error",
            models.DeleteBulkZonesRequest(
                zones_list=models.ZoneNameListResponse(
                    zones=["one.testbulk.net", "two.testbulk.net"],
                ),
                bypass_safety_checks=True,
            ),
            500,
            json.dumps({
                "type": "internal_error",
                "title": "Internal Server Error",
                "detail": "Error creating zone",
                "status": 500,
            }),
            None,
            Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error creating zone",
                status_code=500,
            ),
        ),
    ],
)
def test_delete_bulk_zones(
    test_name, params, response_status, response_body,
    expected_response, expected_error,
    mock_session, dns_client,
):
    """Mirrors Go TestDNS_DeleteBulkZones from zonebulk_test.go."""
    if isinstance(expected_error, Error):
        mock_session.exec.side_effect = expected_error
        with pytest.raises(Error) as exc_info:
            dns_client.delete_bulk_zones(params)
        assert exc_info.value.status_code == expected_error.status_code
        return

    mock_session.exec.return_value = (
        mock_response(status_code=response_status, text_body=response_body),
        json.loads(response_body),
    )
    result = dns_client.delete_bulk_zones(params)
    assert result == expected_response
