# pylint: disable=too-many-lines
"""Unit tests for the HAPI service client.

Mirrors Go test files:
- pkg/hapi/hapi_test.go (TestClient)
- pkg/hapi/change_requests_test.go (TestGetChangeRequest)
- pkg/hapi/edgehostname_test.go (TestDeleteEdgeHostname, TestGetEdgeHostname,
  TestPatchEdgeHostname, TestGetCertificate)
- pkg/hapi/errors_test.go (TestNewError, TestJsonErrorUnmarshalling)

Total: 22 test cases across 7 test groups.
"""

import json
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.hapi import (
    HapiClient,
    GetChangeRequestRequest,
    ChangeRequest,
    DeleteEdgeHostnameRequest,
    DeleteEdgeHostnameResponse,
    UpdateEdgeHostnameRequest,
    UpdateEdgeHostnameRequestBody,
    UpdateEdgeHostnameResponse,
    EdgeHostname,
    ChinaCDN,
    UseCase,
    GetEdgeHostnameResponse,
    GetCertificateRequest,
    GetCertificateResponse,
    Error,
    ErrorItem,
    ErrGetChangeRequest,
    ErrDeleteEdgeHostname,
    ErrGetEdgeHostname,
    ErrUpdateEdgeHostname,
    ErrGetCertificate,
    ErrNotFound,
)
from akamai.edgegrid.hapi.errors import (
    ErrStructValidation,
    parse_hapi_error,
)
from akamai.edgegrid.hapi.test.conftest import make_mock_response

# Type reference used in pytest.raises for API sentinel error assertions.
# All HAPI sentinel constants are instances of this internal type.
_SentinelType = type(ErrGetChangeRequest)

# Common error title for JSON unmarshal failures (verbatim from Go).
_UNMARSHAL_TITLE = (
    "Failed to unmarshal error body. "
    "HAPI API failed. "
    "Check details for more information."
)

# Common 500 internal server error response body (verbatim from Go tests).
_INTERNAL_500_BODY = (
    '{"type": "internal_error", "title": "Internal Server Error",'
    ' "detail": "Error deleting activation", "status": 500}'
)


def _mock_success(mock_session, body_str):
    """Configure mock_session.exec for a successful response.

    Parses the JSON body string and returns it as the exec result.
    """
    body_dict = json.loads(body_str)
    mock_resp = MagicMock(status_code=200)
    mock_session.exec.return_value = (mock_resp, body_dict)


def _mock_api_error(mock_session, status, body_str):
    """Configure mock_session.exec to raise an HAPI Error.

    Parses the JSON body, constructs an Error, and sets it as side_effect.
    Returns the Error object for assertion use.
    """
    body_dict = json.loads(body_str)
    err = Error.from_dict(body_dict)
    err.status = status
    mock_session.exec.side_effect = err
    return err


def _assert_exec(mock_session, method, path, **kwargs):
    """Assert mock_session.exec was called with expected method and path.

    Additional keyword arguments are checked against the call's kwargs.
    """
    mock_session.exec.assert_called_once()
    call_args = mock_session.exec.call_args
    assert call_args[0][0] == method
    assert call_args[0][1] == path
    for key, value in kwargs.items():
        assert call_args[1][key] == value


# ======================================================================
# 1. TestClient (1 test case)
# ======================================================================


class TestClient:  # pylint: disable=too-few-public-methods
    """Test client construction. Mirrors Go TestClient."""

    def test_no_options_provided_return_default(self, mock_session):
        """Test: 'no options provided, return default'."""
        client = HapiClient(mock_session)
        # pylint: disable=protected-access
        assert client._session is mock_session


# ======================================================================
# 2. TestGetChangeRequest (3 test cases)
# ======================================================================


class TestGetChangeRequest:
    """Tests for get_change_request.

    Mirrors Go TestGetChangeRequest — 3 table-driven test cases.
    """

    def test_200_ok(self, hapi_client, mock_session):
        """Test: '200 OK' — successful change request retrieval."""
        body = (
            '{"action": "EDIT", "changeId": 123, '
            '"edgeHostnames": [{"chinaCdn": {"isChinaCdn": false}, '
            '"dnsZone": "edgekey.net", "edgeHostnameId": 112233, '
            '"ipVersionBehavior": "IPV6_IPV4_DUALSTACK", '
            '"map": "a;bcd.akamaiedge.net", "productId": "DSA", '
            '"recordName": "test123", '
            '"securityType": "ENHANCED-TLS", '
            '"serialNumber": 0, "slotNumber": 1234, '
            '"ttl": 21600, '
            '"useDefaultMap": true, "useDefaultTtl": true}], '
            '"status": "PENDING", '
            '"statusMessage": '
            '"File uploaded and awaiting validation", '
            '"statusUpdateDate": '
            '"2023-09-04T09:21:38.000+00:00", '
            '"submitDate": "2023-09-04T09:21:38.000+00:00", '
            '"submitter": "nobody", '
            '"submitterEmail": "nobody@nomail-akamai.com"}'
        )
        _mock_success(mock_session, body)
        result = hapi_client.get_change_request(
            GetChangeRequestRequest(change_id=123)
        )
        _assert_exec(
            mock_session, "GET", "/hapi/v1/change-requests/123"
        )
        assert isinstance(result, ChangeRequest)
        assert result.action == "EDIT"
        assert result.change_id == 123
        assert len(result.edge_hostnames) == 1
        ehost = result.edge_hostnames[0]
        assert isinstance(ehost, EdgeHostname)
        assert ehost.china_cdn == ChinaCDN(is_china_cdn=False)
        assert ehost.dns_zone == "edgekey.net"
        assert ehost.edge_hostname_id == 112233
        assert ehost.ip_version_behavior == "IPV6_IPV4_DUALSTACK"
        assert ehost.map == "a;bcd.akamaiedge.net"
        assert ehost.product_id == "DSA"
        assert ehost.record_name == "test123"
        assert ehost.security_type == "ENHANCED-TLS"
        assert ehost.serial_number == 0
        assert ehost.slot_number == 1234
        assert ehost.ttl == 21600
        assert ehost.use_default_map is True
        assert ehost.use_default_ttl is True
        assert result.status == "PENDING"
        assert result.status_message == (
            "File uploaded and awaiting validation"
        )
        assert result.status_update_date == (
            "2023-09-04T09:21:38.000+00:00"
        )
        assert result.submit_date == (
            "2023-09-04T09:21:38.000+00:00"
        )
        assert result.submitter == "nobody"
        assert result.submitter_email == (
            "nobody@nomail-akamai.com"
        )

    def test_403_access_denied(self, hapi_client, mock_session):
        """Test: '403 Access Denied to Edge Hostname'."""
        body = (
            '{"type": '
            '"/hapi/problems/access-denied-to-edge-hostname", '
            '"title": "Access Denied to Edge Hostname", '
            '"status": 403, '
            '"detail": '
            '"You do not have access to this edge hostname", '
            '"instance": "/hapi/error-instances/'
            '7a2c1b84-fe90-40f2-8391-aaaaaaaaaa", '
            '"requestInstance": '
            '"http://cloud.akamaiapis.net/hapi/open/v1/'
            'change-requests/234#aaaaaaa", '
            '"method": "GET", '
            '"requestTime": '
            '"2023-09-04T09:26:16.561878149Z", '
            '"errors": []}'
        )
        api_err = _mock_api_error(mock_session, 403, body)
        with pytest.raises(_SentinelType) as exc_info:
            hapi_client.get_change_request(
                GetChangeRequestRequest(change_id=234)
            )
        assert str(ErrGetChangeRequest) in str(exc_info.value)
        cause = exc_info.value.__cause__
        assert cause is api_err
        assert cause.type == (
            "/hapi/problems/access-denied-to-edge-hostname"
        )
        assert cause.title == "Access Denied to Edge Hostname"
        assert cause.status == 403
        assert cause.detail == (
            "You do not have access to this edge hostname"
        )
        assert cause.instance == (
            "/hapi/error-instances/"
            "7a2c1b84-fe90-40f2-8391-aaaaaaaaaa"
        )
        assert cause.request_instance == (
            "http://cloud.akamaiapis.net/hapi/open/v1/"
            "change-requests/234#aaaaaaa"
        )
        assert cause.method == "GET"
        assert cause.request_time == (
            "2023-09-04T09:26:16.561878149Z"
        )
        # Validate errors list type (ErrorItem)
        assert all(
            isinstance(e, ErrorItem) for e in cause.errors
        )

    def test_500_internal_server_error(
        self, hapi_client, mock_session
    ):
        """Test: '500 internal server error'."""
        api_err = _mock_api_error(
            mock_session, 500, _INTERNAL_500_BODY
        )
        with pytest.raises(_SentinelType) as exc_info:
            hapi_client.get_change_request(
                GetChangeRequestRequest(change_id=123)
            )
        assert str(ErrGetChangeRequest) in str(exc_info.value)
        cause = exc_info.value.__cause__
        assert cause is api_err
        assert cause.type == "internal_error"
        assert cause.title == "Internal Server Error"
        assert cause.detail == "Error deleting activation"
        assert cause.status == 500


# ======================================================================
# 3. TestDeleteEdgeHostname (4 test cases)
# ======================================================================


class TestDeleteEdgeHostname:
    """Tests for delete_edge_hostname.

    Mirrors Go TestDeleteEdgeHostname — 4 table-driven test cases.
    """

    def test_202_accepted(self, hapi_client, mock_session):
        """Test: '202 Accepted' — successful deletion."""
        body = (
            '{"action": "DELETE", "changeId": 66025603, '
            '"edgeHostnames": [{"chinaCdn": '
            '{"isChinaCdn": false}, '
            '"dnsZone": "edgesuite.net", '
            '"edgeHostnameId": 4558392, '
            '"recordName": "mgw-test-001", '
            '"securityType": "STANDARD-TLS", '
            '"useDefaultMap": false, '
            '"useDefaultTtl": false}], '
            '"status": "PENDING", '
            '"statusMessage": '
            '"File uploaded and awaiting validation", '
            '"statusUpdateDate": '
            '"2021-09-23T15:07:10.000+00:00", '
            '"submitDate": '
            '"2021-09-23T15:07:10.000+00:00", '
            '"submitter": "ftzgvvigljhoq5ib", '
            '"submitterEmail": '
            '"ftzgvvigljhoq5ib@nomail-akamai.com"}'
        )
        _mock_success(mock_session, body)
        result = hapi_client.delete_edge_hostname(
            DeleteEdgeHostnameRequest(
                dns_zone="edgesuite.net",
                record_name="mgw-test-001",
                status_update_email=["some@example.com"],
                comments="some comment",
            )
        )
        _assert_exec(
            mock_session, "DELETE",
            "/hapi/v1/dns-zones/edgesuite.net"
            "/edge-hostnames/mgw-test-001",
            params={
                "comments": "some comment",
                "statusUpdateEmail": "some@example.com",
            },
        )
        assert isinstance(result, DeleteEdgeHostnameResponse)
        assert result.action == "DELETE"
        assert result.change_id == 66025603
        assert len(result.edge_hostnames) == 1
        ehost = result.edge_hostnames[0]
        assert ehost.china_cdn == ChinaCDN(
            is_china_cdn=False
        )
        assert ehost.dns_zone == "edgesuite.net"
        assert ehost.edge_hostname_id == 4558392
        assert ehost.record_name == "mgw-test-001"
        assert ehost.security_type == "STANDARD-TLS"
        assert ehost.use_default_map is False
        assert ehost.use_default_ttl is False
        assert result.status == "PENDING"
        assert result.status_message == (
            "File uploaded and awaiting validation"
        )
        assert result.status_update_date == (
            "2021-09-23T15:07:10.000+00:00"
        )
        assert result.submit_date == (
            "2021-09-23T15:07:10.000+00:00"
        )
        assert result.submitter == "ftzgvvigljhoq5ib"
        assert result.submitter_email == (
            "ftzgvvigljhoq5ib@nomail-akamai.com"
        )

    def test_404_not_found(self, hapi_client, mock_session):
        """Test: '404 could not find edge hostname'."""
        body = (
            '{"type": '
            '"/hapi/problems/'
            'record-name-dns-zone-not-found", '
            '"title": "Invalid Record Name/DNS Zone", '
            '"status": 404, '
            '"detail": "Could not find edge hostname '
            'with record name mgw-test-003 and DNS Zone '
            'edgesuite.net", '
            '"instance": "/hapi/error-instances/'
            '47f08d26-00b4-4c05-a8c0-bcbc542b9bce", '
            '"requestInstance": '
            '"http://cloud-qa-resource-impl.luna-dev.'
            'akamaiapis.net/hapi/open/v1/dns-zones/'
            'edgesuite.net/edge-hostnames/'
            'mgw-test-003#9ea9060c", '
            '"method": "DELETE", '
            '"requestTime": '
            '"2021-09-23T15:37:28.383173Z", '
            '"errors": [], '
            '"domainPrefix": "mgw-test-003", '
            '"domainSuffix": "edgesuite.net"}'
        )
        api_err = _mock_api_error(mock_session, 404, body)
        with pytest.raises(_SentinelType) as exc_info:
            hapi_client.delete_edge_hostname(
                DeleteEdgeHostnameRequest(
                    dns_zone="edgesuite.net",
                    record_name="mgw-test-003",
                    status_update_email=[
                        "some@example.com",
                    ],
                    comments="some comment",
                )
            )
        assert str(ErrDeleteEdgeHostname) in str(
            exc_info.value
        )
        cause = exc_info.value.__cause__
        assert cause is api_err
        assert cause.type == (
            "/hapi/problems/"
            "record-name-dns-zone-not-found"
        )
        assert cause.title == (
            "Invalid Record Name/DNS Zone"
        )
        assert cause.status == 404
        assert cause.detail == (
            "Could not find edge hostname with record "
            "name mgw-test-003 and DNS Zone edgesuite.net"
        )
        assert cause.domain_prefix == "mgw-test-003"
        assert cause.domain_suffix == "edgesuite.net"

    def test_500_internal_server_error(
        self, hapi_client, mock_session
    ):
        """Test: '500 internal server error'."""
        api_err = _mock_api_error(
            mock_session, 500, _INTERNAL_500_BODY
        )
        with pytest.raises(_SentinelType) as exc_info:
            hapi_client.delete_edge_hostname(
                DeleteEdgeHostnameRequest(
                    dns_zone="edgesuite.net",
                    record_name="mgw-test-002",
                    status_update_email=[
                        "some@example.com",
                    ],
                    comments="some comment",
                )
            )
        assert str(ErrDeleteEdgeHostname) in str(
            exc_info.value
        )
        assert exc_info.value.__cause__ is api_err

    def test_validation_error(self, hapi_client):
        """Test: 'validation error' — missing dns_zone."""
        with pytest.raises(Exception) as exc_info:
            hapi_client.delete_edge_hostname(
                DeleteEdgeHostnameRequest(
                    record_name="atv_1696855",
                    status_update_email=[
                        "some@example.com",
                    ],
                    comments="some comment",
                )
            )
        assert str(ErrStructValidation) in str(
            exc_info.value
        )


# ======================================================================
# 4. TestGetEdgeHostname (3 test cases)
# ======================================================================


class TestGetEdgeHostname:
    """Tests for get_edge_hostname.

    Mirrors Go TestGetEdgeHostname — 3 table-driven test cases.
    """

    def test_200_ok(self, hapi_client, mock_session):
        """Test: '200 OK' — successful retrieval."""
        body = (
            '{"chinaCdn": {"isChinaCdn": false}, '
            '"comments": "Created by Property-Manager'
            '/PAPI on Thu Mar 03 15:58:17 GMT 2022", '
            '"dnsZone": "edgekey.net", '
            '"edgeHostnameId": 4617960, '
            '"ipVersionBehavior": '
            '"IPV6_IPV4_DUALSTACK", '
            '"productId": "DSA", '
            '"map": "e;dscx.akamaiedge.net", '
            '"recordName": '
            '"aws_ci_pearltest-asorigin-na-as-eu-ionp.'
            'cumulus-essl.webexp-ipqa-ion.com-v2", '
            '"securityType": "ENHANCED-TLS", '
            '"slotNumber": 47463, "ttl": 21600, '
            '"useDefaultMap": true, '
            '"useDefaultTtl": true, '
            '"mapAlias": "al", '
            '"useCases": [{"type": "GLOBAL", '
            '"option": "LIVE", '
            '"useCase": "Segmented_Media_Mode"}]}'
        )
        _mock_success(mock_session, body)
        result = hapi_client.get_edge_hostname(1234)
        _assert_exec(
            mock_session, "GET",
            "/hapi/v1/edge-hostnames/1234",
        )
        assert isinstance(result, GetEdgeHostnameResponse)
        assert result.china_cdn == ChinaCDN(
            is_china_cdn=False
        )
        assert result.comments == (
            "Created by Property-Manager/PAPI on "
            "Thu Mar 03 15:58:17 GMT 2022"
        )
        assert result.dns_zone == "edgekey.net"
        assert result.edge_hostname_id == 4617960
        assert result.ip_version_behavior == (
            "IPV6_IPV4_DUALSTACK"
        )
        assert result.product_id == "DSA"
        assert result.map == "e;dscx.akamaiedge.net"
        assert result.record_name == (
            "aws_ci_pearltest-asorigin-na-as-eu-ionp."
            "cumulus-essl.webexp-ipqa-ion.com-v2"
        )
        assert result.security_type == "ENHANCED-TLS"
        assert result.slot_number == 47463
        assert result.ttl == 21600
        assert result.use_default_map is True
        assert result.use_default_ttl is True
        assert result.map_alias == "al"
        assert len(result.use_cases) == 1
        assert result.use_cases[0] == UseCase(
            type="GLOBAL",
            option="LIVE",
            use_case="Segmented_Media_Mode",
        )

    def test_404_not_found(
        self, hapi_client, mock_session
    ):
        """Test: '404 could not find edge hostname'."""
        body = (
            '{"type": '
            '"/hapi/problems/edge-hostname-not-found", '
            '"title": "Edge Hostname Not Found", '
            '"status": 404, '
            '"detail": "Edge hostname not found", '
            '"instance": "/hapi/error-instances/'
            'cdc47ffa-46f2-410d-8059-3f454c435e93", '
            '"requestInstance": '
            '"http://cloud-qa-resource-impl.luna-dev.'
            'akamaiapis.net/hapi/open/v1/'
            'edge-hostnames/9999#8a702528", '
            '"method": "GET", '
            '"requestTime": '
            '"2022-03-03T16:43:19.876613Z", '
            '"errors": []}'
        )
        api_err = _mock_api_error(
            mock_session, 404, body
        )
        with pytest.raises(_SentinelType) as exc_info:
            hapi_client.get_edge_hostname(9999)
        assert str(ErrGetEdgeHostname) in str(
            exc_info.value
        )
        cause = exc_info.value.__cause__
        assert cause is api_err
        assert cause.type == (
            "/hapi/problems/edge-hostname-not-found"
        )
        assert cause.title == (
            "Edge Hostname Not Found"
        )
        assert cause.status == 404
        assert cause.detail == (
            "Edge hostname not found"
        )

    def test_500_internal_server_error(
        self, hapi_client, mock_session
    ):
        """Test: '500 internal server error'."""
        api_err = _mock_api_error(
            mock_session, 500, _INTERNAL_500_BODY
        )
        with pytest.raises(_SentinelType) as exc_info:
            hapi_client.get_edge_hostname(9999)
        assert str(ErrGetEdgeHostname) in str(
            exc_info.value
        )
        assert exc_info.value.__cause__ is api_err


# ======================================================================
# 5. TestPatchEdgeHostname (3 test cases)
# ======================================================================


class TestPatchEdgeHostname:
    """Tests for update_edge_hostname.

    Mirrors Go TestPatchEdgeHostname — 3 table-driven test cases.
    """

    def test_202_accepted(self, hapi_client, mock_session):
        """Test: '202 Accepted' — successful patch."""
        body = (
            '{"action": "EDIT", "changeId": 66025603, '
            '"edgeHostnames": [{"chinaCdn": '
            '{"isChinaCdn": false}, '
            '"dnsZone": "edgesuite.net", '
            '"edgeHostnameId": 4558392, '
            '"ipVersionBehavior": "IPV4", '
            '"recordName": "mgw-test-001", '
            '"securityType": "STANDARD-TLS", '
            '"ttl": 10000, '
            '"useDefaultMap": false, '
            '"useDefaultTtl": false}], '
            '"status": "PENDING", '
            '"statusMessage": '
            '"File uploaded and awaiting validation", '
            '"statusUpdateDate": '
            '"2021-09-23T15:07:10.000+00:00", '
            '"submitDate": '
            '"2021-09-23T15:07:10.000+00:00", '
            '"submitter": "ftzgvvigljhoq5ib", '
            '"submitterEmail": '
            '"ftzgvvigljhoq5ib@nomail-akamai.com"}'
        )
        _mock_success(mock_session, body)
        result = hapi_client.update_edge_hostname(
            UpdateEdgeHostnameRequest(
                dns_zone="edgesuite.net",
                record_name="mgw-test-001",
                status_update_email=["some@example.com"],
                comments="some comment",
                body=[
                    UpdateEdgeHostnameRequestBody(
                        op="replace",
                        path="/ttl",
                        value="10000",
                    ),
                    UpdateEdgeHostnameRequestBody(
                        op="replace",
                        path="/ipVersionBehavior",
                        value="IPV4",
                    ),
                ],
            )
        )
        _assert_exec(
            mock_session, "PATCH",
            "/hapi/v1/dns-zones/edgesuite.net"
            "/edge-hostnames/mgw-test-001",
            params={
                "comments": "some comment",
                "statusUpdateEmail": "some@example.com",
            },
        )
        assert isinstance(result, UpdateEdgeHostnameResponse)
        assert result.action == "EDIT"
        assert result.change_id == 66025603
        assert len(result.edge_hostnames) == 1
        ehost = result.edge_hostnames[0]
        assert ehost.china_cdn == ChinaCDN(
            is_china_cdn=False
        )
        assert ehost.dns_zone == "edgesuite.net"
        assert ehost.edge_hostname_id == 4558392
        assert ehost.ip_version_behavior == "IPV4"
        assert ehost.record_name == "mgw-test-001"
        assert ehost.security_type == "STANDARD-TLS"
        assert ehost.ttl == 10000
        assert ehost.use_default_map is False
        assert ehost.use_default_ttl is False
        assert result.status == "PENDING"
        assert result.status_message == (
            "File uploaded and awaiting validation"
        )
        assert result.submitter == "ftzgvvigljhoq5ib"

    def test_400_incorrect_body(self, hapi_client):
        """Test: '400 Incorrect body'.

        In Go, validation catches the invalid body before the HTTP
        call and wraps the error with ErrUpdateEdgeHostname via %w,
        so errors.Is(err, ErrUpdateEdgeHostname) is true.  The mock
        server response body is never consumed.

        In Python, validation raises ErrStructValidation whose
        message contains both ErrUpdateEdgeHostname and the
        validation details.
        """
        with pytest.raises(Exception) as exc_info:
            hapi_client.update_edge_hostname(
                UpdateEdgeHostnameRequest(
                    dns_zone="edgesuite.net",
                    record_name="mgw-test-001",
                    status_update_email=[
                        "some@example.com",
                    ],
                    comments="some comment",
                    body=[
                        UpdateEdgeHostnameRequestBody(
                            path="/incorrect",
                            value="some Value",
                        ),
                    ],
                )
            )
        # Mirrors Go: errors.Is(err, ErrUpdateEdgeHostname)
        assert str(ErrUpdateEdgeHostname) in str(
            exc_info.value
        )
        assert str(ErrStructValidation) in str(
            exc_info.value
        )

    def test_500_internal_server_error(
        self, hapi_client, mock_session
    ):
        """Test: '500 internal server error'."""
        api_err = _mock_api_error(
            mock_session, 500, _INTERNAL_500_BODY
        )
        with pytest.raises(_SentinelType) as exc_info:
            hapi_client.update_edge_hostname(
                UpdateEdgeHostnameRequest(
                    dns_zone="edgesuite.net",
                    record_name="mgw-test-002",
                    status_update_email=[
                        "some@example.com",
                    ],
                    comments="some comment",
                    body=[
                        UpdateEdgeHostnameRequestBody(
                            op="replace",
                            path="/ttl",
                            value="10000",
                        ),
                    ],
                )
            )
        assert str(ErrUpdateEdgeHostname) in str(
            exc_info.value
        )
        assert exc_info.value.__cause__ is api_err


# ======================================================================
# 6. TestGetCertificate (4 test cases)
# ======================================================================


class TestGetCertificate:
    """Tests for get_certificate.

    Mirrors Go TestGetCertificate — 4 table-driven test cases.
    """

    def test_200_ok(self, hapi_client, mock_session):
        """Test: '200 OK' — successful certificate retrieval."""
        body = (
            '{"certificateId": "1234", '
            '"commonName": "example.com", '
            '"serialNumber": '
            '"12:34:56:78:90:AB:CD:EF", '
            '"slotNumber": 8927, '
            '"expirationDate": '
            '"2019-10-31T23:59:59Z", '
            '"certificateType": "SAN", '
            '"validationType": "DOMAIN_VALIDATION", '
            '"status": "PENDING", '
            '"availableDomains": ['
            '"live.example.com", '
            '"secure.example.com", '
            '"www.example.com"]}'
        )
        _mock_success(mock_session, body)
        result = hapi_client.get_certificate(
            GetCertificateRequest(
                dns_zone="edgekey.net",
                record_name="mgw-test-002",
            )
        )
        _assert_exec(
            mock_session, "GET",
            "/hapi/v1/dns-zones/edgekey.net"
            "/edge-hostnames/mgw-test-002/certificate",
        )
        assert isinstance(result, GetCertificateResponse)
        assert result.certificate_id == "1234"
        assert result.common_name == "example.com"
        assert result.serial_number == (
            "12:34:56:78:90:AB:CD:EF"
        )
        assert result.slot_number == 8927
        # ExpirationDate is str (Go time.Time -> Python str)
        assert result.expiration_date == (
            "2019-10-31T23:59:59Z"
        )
        assert result.certificate_type == "SAN"
        assert result.validation_type == (
            "DOMAIN_VALIDATION"
        )
        assert result.status == "PENDING"
        assert result.available_domains == [
            "live.example.com",
            "secure.example.com",
            "www.example.com",
        ]

    def test_404_certificate_not_found(
        self, hapi_client, mock_session
    ):
        """Test: '404 certificate not found'.

        Special case: error wraps ErrGetCertificate + ErrNotFound.
        """
        body = (
            '{"type": "CERTIFICATE_NOT_FOUND", '
            '"title": "Certificate Not Found", '
            '"status": 404, '
            '"detail": "Details are not available for '
            'this certificate; the certificate is '
            'missing or access is denied", '
            '"instance": "/hapi/error-instances/'
            'a30f67cc-df20-4e02-bbc3-cf7c204a4aab", '
            '"requestInstance": '
            '"http://origin.pulsar.akamai.com/hapi/'
            'open/v1/dns-zones/edgekey.net/'
            'edge-hostnames/example.com/certificate'
            '?depth=ALL&accountSwitchKey='
            'F-AC-1937217#d7aa7348", '
            '"method": "GET", '
            '"requestTime": '
            '"2022-11-30T18:51:43.482982Z", '
            '"errors": [], '
            '"extensionFields": []}'
        )
        _mock_api_error(mock_session, 404, body)
        with pytest.raises(_SentinelType) as exc_info:
            hapi_client.get_certificate(
                GetCertificateRequest(
                    dns_zone="edgekey.net",
                    record_name="unknown",
                )
            )
        msg = str(exc_info.value)
        assert str(ErrGetCertificate) in msg
        assert str(ErrNotFound) in msg
        cause = exc_info.value.__cause__
        assert isinstance(cause, Error)
        assert cause.type == "CERTIFICATE_NOT_FOUND"
        assert cause.title == "Certificate Not Found"
        assert cause.status == 404

    def test_500_internal_server_error(
        self, hapi_client, mock_session
    ):
        """Test: '500 internal server error'."""
        api_err = _mock_api_error(
            mock_session, 500, _INTERNAL_500_BODY
        )
        with pytest.raises(_SentinelType) as exc_info:
            hapi_client.get_certificate(
                GetCertificateRequest(
                    dns_zone="edgekey.net",
                    record_name="mgw-test-002",
                )
            )
        assert str(ErrGetCertificate) in str(
            exc_info.value
        )
        assert exc_info.value.__cause__ is api_err

    def test_missing_required_values(self, hapi_client):
        """Test: 'missing required values' — validation error."""
        with pytest.raises(Exception) as exc_info:
            hapi_client.get_certificate(
                GetCertificateRequest()
            )
        assert str(ErrStructValidation) in str(
            exc_info.value
        )


# ======================================================================
# 7. TestNewError (2 test cases)
# ======================================================================


class TestNewError:
    """Tests for parse_hapi_error.

    Mirrors Go TestNewError — 2 table-driven test cases testing
    error parsing from mock HTTP responses.
    """

    def test_valid_response_status_500(self):
        """Test: 'valid response, status code 500'."""
        mock_resp = make_mock_response(
            500,
            '{"type":"a","title":"b","detail":"c"}',
        )
        err = parse_hapi_error(mock_resp)
        assert isinstance(err, Error)
        assert err.type == "a"
        assert err.title == "b"
        assert err.detail == "c"
        assert err.status == 500

    def test_invalid_response_body(self):
        """Test: 'invalid response body, assign status code'."""
        mock_resp = make_mock_response(500, "test")
        err = parse_hapi_error(mock_resp)
        assert isinstance(err, Error)
        assert err.title == _UNMARSHAL_TITLE
        assert err.detail == "test"
        assert err.status == 500


# ======================================================================
# 8. TestJsonErrorUnmarshalling (3 test cases)
# ======================================================================


class TestJsonErrorUnmarshalling:
    """Tests for JSON error unmarshalling with non-JSON bodies.

    Mirrors Go TestJsonErrorUnmarshalling — 3 table-driven test cases.
    """

    def test_html_response(self):
        """Test: 'API failure with HTML response'."""
        html_body = (
            "<HTML><HEAD>...</HEAD>"
            "<BODY>...</BODY></HTML>"
        )
        mock_resp = make_mock_response(0, html_body)
        err = parse_hapi_error(mock_resp)
        assert isinstance(err, Error)
        assert err.title == _UNMARSHAL_TITLE
        assert err.detail == html_body

    def test_plain_text_response(self):
        """Test: 'API failure with plain text response'."""
        text_body = (
            "Your request did not succeed as this "
            "operation has reached  the limit for "
            "your account. Please try after "
            "2024-01-16T15:20:55.945Z"
        )
        mock_resp = make_mock_response(0, text_body)
        err = parse_hapi_error(mock_resp)
        assert isinstance(err, Error)
        assert err.title == _UNMARSHAL_TITLE
        assert err.detail == text_body

    def test_xml_response(self):
        """Test: 'API failure with XML response'."""
        xml_body = (
            '<Root><Item id="1" name="Example" />'
            "</Root>"
        )
        mock_resp = make_mock_response(0, xml_body)
        err = parse_hapi_error(mock_resp)
        assert isinstance(err, Error)
        assert err.title == _UNMARSHAL_TITLE
        assert err.detail == xml_body
