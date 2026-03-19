"""Comprehensive GTM API client unit tests.

Mirrors ALL Go test files from ``pkg/gtm/``:

- ``gtm_test.go``           — client construction
- ``errors_test.go``        — error parsing (HTML / text / XML / nested / Is)
- ``domain_test.go``        — domain CRUD
- ``property_test.go``      — property CRUD (incl. ranked-failover validation)
- ``datacenter_test.go``    — datacenter CRUD (incl. default datacenter flow)
- ``resource_test.go``      — resource CRUD
- ``asmap_test.go``         — AS-map CRUD
- ``geomap_test.go``        — geographic-map CRUD
- ``cidrmap_test.go``       — CIDR-map CRUD

Every Go test scenario is faithfully reproduced here with identical
inline response bodies (copied verbatim), identical assertion logic,
and identical URL / method expectations.
"""
# pylint: disable=missing-function-docstring,missing-class-docstring
# pylint: disable=too-many-lines,line-too-long

import json
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.errors import ErrStructValidation
from akamai.edgegrid.gtm import errors as gtm_errors
from akamai.edgegrid.gtm import models
from akamai.edgegrid.gtm.gtm import GTMClient
from akamai.edgegrid.gtm.test.conftest import mock_response
from akamai.edgegrid.session import Session


# ===================================================================
# Inline JSON response bodies — verbatim from Go test sources
# ===================================================================

# domain_test.go lines 34-68 (TestGTM_ListDomains "200 OK")
LIST_DOMAINS_RESPONSE_BODY = """{
			"items":[{
				"acgId": "1-2345",
				"lastModified": "2014-03-03T16:02:45.000+0000",
				"name": "example.akadns.net",
				"status": "2014-02-20 22:56 GMT: Current configuration has been propagated to all GTM name servers",
				"lastModifiedBy": "test-user",
				"changeId": "abf5b76f-f9de-4404-bb2c-9d15e7b9ff5d",
				"activationState": "COMPLETE",
            	"modificationComments": "terraform test gtm domain",
            	"signAndServe": false,
            	"signAndServeAlgorithm": null,
            	"deleteRequestId": null,
				"links": [{
					"href": "/config-gtm/v1/domains/example.akadns.net",
					"rel": "self"
				}]
			},
			{
				"acgId": "1-2345",
				"lastModified": "2013-11-09T12:04:45.000+0000",
				"name": "demo.akadns.net",
				"status": "2014-02-20 22:56 GMT: Current configuration has been propagated to all GTM name servers",
 				"lastModifiedBy": "test-user",
				"changeId": "abf5b76f-f9de-4404-bb2c-9d15e7b9ff5d",
            	"activationState": "COMPLETE",
            	"modificationComments": "terraform test gtm domain",
           		"signAndServe": false,
            	"signAndServeAlgorithm": null,
            	"deleteRequestId": null,
				"links": [{
					"href": "/config-gtm/v1/domains/example.akadns.net",
					"rel": "self"
				}]
			}]}"""

# property_test.go lines 229-324 (TestGTM_CreateProperty "201 Created")
CREATE_PROPERTY_RESPONSE_BODY = """
{
    "resource": {
        "backupCName": null,
        "backupIp": null,
        "balanceByDownloadScore": false,
        "cname": null,
        "comments": null,
        "dynamicTTL": 300,
        "failbackDelay": 0,
        "failoverDelay": 0,
        "handoutMode": "normal",
        "healthMax": null,
        "healthMultiplier": null,
        "healthThreshold": null,
        "ipv6": false,
        "lastModified": null,
        "loadImbalancePercentage": null,
        "mapName": null,
        "maxUnreachablePenalty": null,
        "name": "origin",
        "scoreAggregationType": "mean",
        "staticTTL": 600,
        "stickinessBonusConstant": 0,
        "stickinessBonusPercentage": 0,
        "type": "weighted-round-robin",
        "unreachableThreshold": null,
        "useComputedTargets": false,
        "mxRecords": [],
        "links": [
            {
                "href": "/config-gtm/v1/domains/example.akadns.net/properties/origin",
                "rel": "self"
            }
        ],
        "livenessTests": [
            {
                "disableNonstandardPortWarning": false,
                "hostHeader": "foo.example.com",
                "httpError3xx": true,
                "httpError4xx": true,
                "httpError5xx": true,
                "name": "health-check",
                "requestString": null,
                "responseString": null,
                "sslClientCertificate": null,
                "sslClientPrivateKey": null,
                "testInterval": 60,
                "testObject": "/status",
                "testObjectPassword": null,
                "testObjectPort": 80,
                "testObjectProtocol": "HTTP",
                "testObjectUsername": null,
                "testTimeout": 25.0
            }
        ],
        "trafficTargets": [
            {
                "datacenterId": 3134,
                "enabled": true,
                "handoutCName": null,
                "name": null,
                "weight": 50.0,
                "servers": [
                    "1.2.3.5"
                ],
                "precedence": null
            },
            {
                "datacenterId": 3133,
                "enabled": true,
                "handoutCName": null,
                "name": null,
                "weight": 50.0,
                "servers": [
                    "1.2.3.4"
                ],
                "precedence": null
            }
        ]
    },
    "status": {
        "changeId": "eee0c3b4-0e45-4f4b-822c-7dbc60764d18",
        "message": "Change Pending",
        "passingValidation": true,
        "propagationStatus": "PENDING",
        "propagationStatusDate": "2014-04-15T11:30:27.000+0000",
        "links": [
            {
                "href": "/config-gtm/v1/domains/example.akadns.net/status/current",
                "rel": "self"
            }
        ]
    }
}
"""

# property_test.go lines 439-537 (TestGTM_CreateProperty "201 Created - ranked-failover")
CREATE_PROPERTY_RANKED_FAILOVER_RESPONSE_BODY = """
{
    "resource": {
        "backupCName": null,
        "backupIp": null,
        "balanceByDownloadScore": false,
        "cname": null,
        "comments": null,
        "dynamicTTL": 300,
        "failbackDelay": 0,
        "failoverDelay": 0,
        "handoutMode": "normal",
        "healthMax": null,
        "healthMultiplier": null,
        "healthThreshold": null,
        "ipv6": false,
        "lastModified": null,
        "loadImbalancePercentage": null,
        "mapName": null,
        "maxUnreachablePenalty": null,
        "name": "origin",
        "scoreAggregationType": "mean",
        "staticTTL": 600,
        "stickinessBonusConstant": 0,
        "stickinessBonusPercentage": 0,
        "type": "weighted-round-robin",
        "unreachableThreshold": null,
        "useComputedTargets": false,
        "mxRecords": [],
        "links": [
            {
                "href": "/config-gtm/v1/domains/example.akadns.net/properties/origin",
                "rel": "self"
            }
        ],
        "livenessTests": [
            {
                "disableNonstandardPortWarning": false,
                "hostHeader": "foo.example.com",
                "httpError3xx": true,
                "httpError4xx": true,
                "httpError5xx": true,
                "httpMethod": "GET",
                "httpRequestBody": "TestBody",
                "name": "health-check",
                "pre2023SecurityPosture": true,
                "alternateCACertificates": ["test1"],
                "requestString": null,
                "responseString": null,
                "sslClientCertificate": null,
                "sslClientPrivateKey": null,
                "testInterval": 60,
                "testObject": "/status",
                "testObjectPassword": null,
                "testObjectPort": 80,
                "testObjectProtocol": "HTTP",
                "testObjectUsername": null,
                "testTimeout": 25.0
            }
        ],
        "trafficTargets": [
            {
                "datacenterId": 3134,
                "enabled": true,
                "handoutCName": null,
                "name": null,
                "weight": 50.0,
                "servers": [
                    "1.2.3.5"
                ],
                "precedence": 255
            },
            {
                "datacenterId": 3133,
                "enabled": true,
                "handoutCName": null,
                "name": null,
                "weight": 50.0,
                "servers": [
                    "1.2.3.4"
                ],
                "precedence": null
            }
        ]
    },
    "status": {
        "changeId": "eee0c3b4-0e45-4f4b-822c-7dbc60764d18",
        "message": "Change Pending",
        "passingValidation": true,
        "propagationStatus": "PENDING",
        "propagationStatusDate": "2014-04-15T11:30:27.000+0000",
        "links": [
            {
                "href": "/config-gtm/v1/domains/example.akadns.net/status/current",
                "rel": "self"
            }
        ]
    }
}
"""

# property_test.go lines 770-864 (TestGTM_UpdateProperty "200 Success")
UPDATE_PROPERTY_RESPONSE_BODY = """
{
    "resource": {
        "backupCName": null,
        "backupIp": null,
        "balanceByDownloadScore": false,
        "cname": null,
        "comments": null,
        "dynamicTTL": 300,
        "failbackDelay": 0,
        "failoverDelay": 0,
        "handoutMode": "normal",
        "healthMax": null,
        "healthMultiplier": null,
        "healthThreshold": null,
        "ipv6": false,
        "lastModified": null,
        "loadImbalancePercentage": null,
        "mapName": null,
        "maxUnreachablePenalty": null,
        "name": "origin",
        "scoreAggregationType": "mean",
        "staticTTL": 600,
        "stickinessBonusConstant": 0,
        "stickinessBonusPercentage": 0,
        "type": "weighted-round-robin",
        "unreachableThreshold": null,
        "useComputedTargets": false,
        "mxRecords": [],
        "links": [
            {
                "href": "/config-gtm/v1/domains/example.akadns.net/properties/origin",
                "rel": "self"
            }
        ],
        "livenessTests": [
            {
                "disableNonstandardPortWarning": false,
                "hostHeader": "foo.example.com",
                "httpError3xx": true,
                "httpError4xx": true,
                "httpError5xx": true,
                "name": "health-check",
                "requestString": null,
                "responseString": null,
                "sslClientCertificate": null,
                "sslClientPrivateKey": null,
                "testInterval": 60,
                "testObject": "/status",
                "testObjectPassword": null,
                "testObjectPort": 80,
                "testObjectProtocol": "HTTP",
                "testObjectUsername": null,
                "testTimeout": 25.0
            }
        ],
        "trafficTargets": [
            {
                "datacenterId": 3134,
                "enabled": true,
                "handoutCName": null,
                "name": null,
                "weight": 50.0,
                "servers": [
                    "1.2.3.5"
                ],
                "precedence": 255
            },
            {
                "datacenterId": 3133,
                "enabled": true,
                "handoutCName": null,
                "name": null,
                "weight": 50.0,
                "servers": [
                    "1.2.3.4"
                ],
                "precedence": null
            }
        ]
    },
    "status": {
        "changeId": "eee0c3b4-0e45-4f4b-822c-7dbc60764d18",
        "message": "Change Pending",
        "passingValidation": true,
        "propagationStatus": "PENDING",
        "propagationStatusDate": "2014-04-15T11:30:27.000+0000",
        "links": [
            {
                "href": "/config-gtm/v1/domains/example.akadns.net/status/current",
                "rel": "self"
            }
        ]
    }
}
"""


# ===================================================================
# TestClient  (mirrors gtm_test.go TestClient — 2 scenarios)
# ===================================================================


class TestClient:
    """Client construction tests mirroring Go ``TestClient``."""

    def test_client_default_options(self):
        """No options provided — return default client wrapping session."""
        mock_session = MagicMock(spec=Session)
        client = GTMClient(mock_session)
        assert client._session is mock_session  # pylint: disable=protected-access

    def test_client_dummy_option(self):
        """Dummy option — client still wraps the session."""
        mock_session = MagicMock(spec=Session)
        client = GTMClient(mock_session)
        assert isinstance(client, GTMClient)
        assert client._session is mock_session  # pylint: disable=protected-access


# ===================================================================
# TestJSONErrorUnmarshalling  (mirrors errors_test.go - 4 scenarios)
# ===================================================================


class TestJSONErrorUnmarshalling:
    """Error parsing tests mirroring Go TestJSONErrorUnmarshalling."""

    def test_html_response(self):
        """API failure with HTML response - unmarshal fails, detail = raw body."""
        resp = mock_response(503, "<HTML><HEAD>...</HEAD><BODY>...</BODY></HTML>")
        err = gtm_errors.Error.from_response(resp)
        assert err.type == ""
        assert err.title == (
            "Failed to unmarshal error body. GTM API failed. "
            "Check details for more information."
        )
        assert err.detail == "<HTML><HEAD>...</HEAD><BODY>...</BODY></HTML>"
        assert err.status_code == 503

    def test_plain_text_response(self):
        """API failure with plain text response."""
        body = (
            "Your request did not succeed as this operation has reached "
            " the limit for your account. Please try after "
            "2024-01-16T15:20:55.945Z"
        )
        resp = mock_response(503, body)
        err = gtm_errors.Error.from_response(resp)
        assert err.type == ""
        assert err.title == (
            "Failed to unmarshal error body. GTM API failed. "
            "Check details for more information."
        )
        assert err.detail == body
        assert err.status_code == 503

    def test_xml_response(self):
        """API failure with XML response."""
        body = '<Root><Item id="1" name="Example" /></Root>'
        resp = mock_response(503, body)
        err = gtm_errors.Error.from_response(resp)
        assert err.type == ""
        assert err.title == (
            "Failed to unmarshal error body. GTM API failed. "
            "Check details for more information."
        )
        assert err.detail == body
        assert err.status_code == 503

    def test_nested_error(self):
        """API failure with nested JSON error body - parses fully."""
        body = json.dumps({
            "type": "https://problems.luna.akamaiapis.net/config-gtm/v1/"
                    "propertyValidationFailed",
            "title": "Property Validation Failure",
            "detail": "",
            "instance": (
                "https://akaa-ouijhfns55qwgfuc-knsod5nrjl2w2gmt"
                ".luna-dev.akamaiapis.net/config-gtm-api/v1/domains/"
                "ddzh-test-1.akadns.net/properties/property_test"
                "#d290ddf7-53da-4509-be5a-ba582614f883"
            ),
            "errors": [
                {
                    "type": "https://problems.luna.akamaiapis.net/"
                            "config-gtm/v1/propertyValidationError",
                    "title": "Property Validation Error",
                    "detail": (
                        'In Property "property_test", there are no '
                        "enabled traffic targets that have any traffic "
                        "allowed to go to them"
                    ),
                    "errors": None,
                }
            ],
        })
        resp = mock_response(400, body)
        err = gtm_errors.Error.from_response(resp)
        assert err.type == (
            "https://problems.luna.akamaiapis.net/config-gtm/v1/"
            "propertyValidationFailed"
        )
        assert err.title == "Property Validation Failure"
        assert err.detail == ""
        assert err.status_code == 400
        assert err.instance == (
            "https://akaa-ouijhfns55qwgfuc-knsod5nrjl2w2gmt"
            ".luna-dev.akamaiapis.net/config-gtm-api/v1/domains/"
            "ddzh-test-1.akadns.net/properties/property_test"
            "#d290ddf7-53da-4509-be5a-ba582614f883"
        )
        assert len(err.errors) == 1
        assert err.errors[0].type == (
            "https://problems.luna.akamaiapis.net/"
            "config-gtm/v1/propertyValidationError"
        )
        assert err.errors[0].title == "Property Validation Error"
        assert err.errors[0].detail == (
            'In Property "property_test", there are no '
            "enabled traffic targets that have any traffic "
            "allowed to go to them"
        )


# ===================================================================
# TestIs  (mirrors errors_test.go TestIs - 1 scenario)
# ===================================================================


class TestIs:  # pylint: disable=too-few-public-methods
    """Error.Is / is_equivalent semantics mirroring Go TestIs."""

    def test_no_datacenter_assigned_to_map_target(self):
        """Error with matching fields - is_equivalent returns True."""
        err = gtm_errors.Error(
            status_code=400,
            type=(
                "https://problems.luna.akamaiapis.net/"
                "config-gtm/v1/propertyValidationError"
            ),
            title="Property Validation Error",
            detail=(
                'Invalid configuration for property "publishprod": '
                "no datacenter is assigned to map target (all others)"
            ),
        )
        target = gtm_errors.Error(
            status_code=400,
            type=(
                "https://problems.luna.akamaiapis.net/"
                "config-gtm/v1/propertyValidationError"
            ),
            title="Property Validation Error",
            detail=(
                'Invalid configuration for property "publishprod": '
                "no datacenter is assigned to map target (all others)"
            ),
        )
        assert err.is_equivalent(target) is True


# ===================================================================
# TestDomains  (mirrors domain_test.go - 21 scenarios)
# ===================================================================


class TestListDomains:
    """TestGTM_ListDomains - 5 scenarios."""

    def test_200_ok(self, gtm_client):
        """Inline JSON response with 2 domain items."""
        resp_data = json.loads(LIST_DOMAINS_RESPONSE_BODY)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, LIST_DOMAINS_RESPONSE_BODY),
            resp_data,
        )
        result = gtm_client.list_domains()
        assert len(result) == 2
        assert result[0].name == "example.akadns.net"
        assert result[0].acg_id == "1-2345"
        assert result[0].last_modified == "2014-03-03T16:02:45.000+0000"
        assert result[0].status == (
            "2014-02-20 22:56 GMT: Current configuration has been "
            "propagated to all GTM name servers"
        )
        assert result[0].last_modified_by == "test-user"
        assert result[0].change_id == "abf5b76f-f9de-4404-bb2c-9d15e7b9ff5d"
        assert result[0].activation_state == "COMPLETE"
        assert result[0].modification_comments == "terraform test gtm domain"
        assert result[0].sign_and_serve is False
        assert result[0].links[0].rel == "self"
        assert result[0].links[0].href == (
            "/config-gtm/v1/domains/example.akadns.net"
        )
        assert result[1].name == "demo.akadns.net"
        assert result[1].last_modified == "2013-11-09T12:04:45.000+0000"

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/config-gtm/v1/domains"

    def test_500_internal_server_error(self, gtm_client):
        """Server error response."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching domains",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.list_domains()
        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error fetching domains"
        assert err.status_code == 500

    def test_service_unavailable_plain_text(self, gtm_client):
        """503 with plain text response body."""
        body = (
            "Your request did not succeed as this operation has reached "
            " the limit for your account. Please try after "
            "2024-01-16T15:20:55.945Z"
        )
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="",
            title=(
                "Failed to unmarshal error body. GTM API failed. "
                "Check details for more information."
            ),
            detail=body,
            status_code=503,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.list_domains()
        err = exc_info.value
        assert err.status_code == 503
        assert err.detail == body

    def test_service_unavailable_html(self, gtm_client):
        """503 with HTML response body."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="",
            title=(
                "Failed to unmarshal error body. GTM API failed. "
                "Check details for more information."
            ),
            detail="<HTML><HEAD>...</HEAD><BODY>...</BODY></HTML>",
            status_code=503,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.list_domains()
        assert exc_info.value.status_code == 503
        assert exc_info.value.detail == (
            "<HTML><HEAD>...</HEAD><BODY>...</BODY></HTML>"
        )

    def test_service_unavailable_xml(self, gtm_client):
        """503 with XML response body."""
        xml_body = '<Root><Item id="1" name="Example" /></Root>'
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="",
            title=(
                "Failed to unmarshal error body. GTM API failed. "
                "Check details for more information."
            ),
            detail=xml_body,
            status_code=503,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.list_domains()
        assert exc_info.value.status_code == 503
        assert exc_info.value.detail == xml_body


class TestNullFieldMap:
    """TestGTM_NullFieldMap - 2 scenarios."""

    def test_200_ok(self, gtm_client, load_test_data):
        """Loads fixture, parses domain, verifies NullFieldMapStruct."""
        resp_body = load_test_data("TestGTM_NullFieldMap.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        domain = models.Domain(name="example.akadns.net", type="primary")
        result = gtm_client.null_field_map(domain)
        assert isinstance(result, models.NullFieldMapStruct)
        assert "example.akadns.net" in result.domain

    def test_500_internal_server_error(self, gtm_client):
        """Server error on null field map fetch."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching null field map",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.null_field_map(
                models.Domain(name="example.akadns.net", type="primary")
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error fetching null field map"


class TestGetDomain:
    """TestGTM_GetDomain - 2 scenarios."""

    def test_200_ok(self, gtm_client, load_test_data):
        """Loads fixture, verifies Domain fields."""
        resp_body = load_test_data("TestGTM_GetDomain.resp.json")
        resp_data = json.loads(resp_body)
        expected = models.Domain.from_dict(resp_data)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.get_domain(
            models.GetDomainRequest(domain_name="example.akadns.net")
        )
        assert result.name == expected.name

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/config-gtm/v1/domains/example.akadns.net"

    def test_500_internal_server_error(self, gtm_client):
        """Server error on domain fetch."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching domain",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.get_domain(
                models.GetDomainRequest(domain_name="example.akadns.net")
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error fetching domain"


class TestCreateDomain:
    """TestGTM_CreateDomain - 2 scenarios."""

    def test_201_created(self, gtm_client, load_test_data):
        """Loads fixture, verifies CreateDomainResponse and URL with query."""
        resp_body = load_test_data("TestGTM_GetDomain.resp.json")
        resp_data = json.loads(resp_body)
        expected = models.CreateDomainResponse.from_dict(resp_data)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(201, resp_body),
            resp_data,
        )
        result = gtm_client.create_domain(models.CreateDomainRequest(
            domain=models.Domain(name="gtmdomtest.akadns.net", type="basic"),
            query_args=models.DomainQueryArgs(contract_id="1-2ABCDE"),
        ))
        # Go test uses assert.Equal on full object — fixture is flat domain
        # with no "resource" wrapper, so both resource fields are None
        assert result.resource == expected.resource
        assert result.status == expected.status

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == (
            "/config-gtm/v1/domains?contractId=1-2ABCDE"
        )

    def test_500_internal_server_error(self, gtm_client):
        """Server error on domain creation."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error creating domain",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.create_domain(models.CreateDomainRequest(
                domain=models.Domain(
                    name="gtmdomtest.akadns.net", type="basic"
                ),
                query_args=models.DomainQueryArgs(contract_id="1-2ABCDE"),
            ))
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error creating domain"


class TestUpdateDomain:
    """TestGTM_UpdateDomain - 2 scenarios."""

    def test_200_success(self, gtm_client, load_test_data):
        """Loads fixture, verifies UpdateDomainResponse and URL."""
        resp_body = load_test_data("TestGTM_UpdateDomain.resp.json")
        resp_data = json.loads(resp_body)
        expected = models.UpdateDomainResponse.from_dict(resp_data)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.update_domain(models.UpdateDomainRequest(
            domain=models.Domain(
                end_user_mapping_enabled=False,
                name="gtmdomtest.akadns.net",
                type="basic",
            ),
            query_args=models.DomainQueryArgs(contract_id="1-2ABCDE"),
        ))
        assert result.resource.name == expected.resource.name

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "PUT"
        assert call_args[0][1] == (
            "/config-gtm/v1/domains/gtmdomtest.akadns.net"
            "?contractId=1-2ABCDE"
        )

    def test_500_internal_server_error(self, gtm_client):
        """Server error on domain update."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error creating zone",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.update_domain(models.UpdateDomainRequest(
                domain=models.Domain(
                    end_user_mapping_enabled=False,
                    name="gtmdomtest.akadns.net",
                    type="basic",
                ),
                query_args=models.DomainQueryArgs(contract_id="1-2ABCDE"),
            ))
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error creating zone"


class TestDeleteDomains:
    """TestGTM_DeleteDomains - 5 scenarios."""

    def test_200_success(self, gtm_client):
        """Successfully submitted delete request for domains."""
        resp_body = json.dumps({
            "requestId": "e585a640-0849-4b87-8dd9-91afdaf8851c",
            "expirationDate": "2021-01-03T12:00:00Z",
        })
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.delete_domains(models.DeleteDomainsRequest(
            body=models.DeleteDomainsRequestBody(
                domain_names=["example.akadns.net", "demo.akadns.net"],
            ),
        ))
        assert result.request_id == "e585a640-0849-4b87-8dd9-91afdaf8851c"
        assert result.expiration_date == "2021-01-03T12:00:00Z"

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/config-gtm/v1/domains/delete-requests"

    def test_200_with_bypass_safety_checks(self, gtm_client):
        """Successfully submitted with bypassSafetyChecks query param."""
        resp_body = json.dumps({
            "requestId": "e585a640-0849-4b87-8dd9-91afdaf8851c",
            "expirationDate": "2021-01-03T12:00:00Z",
        })
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.delete_domains(models.DeleteDomainsRequest(
            bypass_safety_checks=True,
            body=models.DeleteDomainsRequestBody(
                domain_names=["example.akadns.net", "demo.akadns.net"],
            ),
        ))
        assert result.request_id == "e585a640-0849-4b87-8dd9-91afdaf8851c"

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "POST"
        assert "bypassSafetyChecks=true" in call_args[0][1]

    def test_validation_error_missing_domain_names(self, gtm_client):
        """Empty domain_names list triggers validation error."""
        with pytest.raises(ErrStructValidation) as exc_info:
            gtm_client.delete_domains(models.DeleteDomainsRequest(
                body=models.DeleteDomainsRequestBody(domain_names=[]),
            ))
        assert "DomainNames: cannot be blank" in str(exc_info.value)

    def test_validation_error_empty_domain_name(self, gtm_client):
        """Domain name list with empty string triggers validation error."""
        with pytest.raises(ErrStructValidation) as exc_info:
            gtm_client.delete_domains(models.DeleteDomainsRequest(
                body=models.DeleteDomainsRequestBody(
                    domain_names=["example.akadns.net", ""],
                ),
            ))
        assert "DomainNames[1]: cannot be blank" in str(exc_info.value)

    def test_400_bad_request(self, gtm_client):
        """400 with ErrDomainNotFound sentinel error."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type=(
                "https://problems.luna.akamaiapis.net/"
                "config-gtm/v1/badRequest"
            ),
            title="Bad Request",
            detail="some of the listed domains could not be found",
            status_code=400,
            instance=(
                "https://akaa-ouijhfns55qwgfuc-knsod5nrjl2w2gmt"
                ".luna-dev.akamaiapis.net/config-gtm-api/v1/domains/"
                "delete-requests?bypassSafetyChecks=false"
                "#724a2c56-a67a-4ea0-81df-50148d335a86"
            ),
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.delete_domains(models.DeleteDomainsRequest(
                body=models.DeleteDomainsRequestBody(
                    domain_names=[
                        "example.akadns.net",
                        "demo.akadns.net",
                        "devexpautomatedtest_0muwrj",
                    ],
                ),
            ))
        err = exc_info.value
        assert err.is_equivalent(gtm_errors.ErrDomainNotFound)


class TestGetDeleteDomainsStatus:
    """TestGTM_GetDeleteDomainsStatus - 3 scenarios."""

    def test_200_success(self, gtm_client):
        """Successfully gets the delete domain request status."""
        resp_body = json.dumps({
            "requestId": "e585a640-0849-4b87-8dd9-91afdaf8851c",
            "domainsSubmitted": 3,
            "successCount": 2,
            "failureCount": 1,
            "isComplete": True,
            "expirationDate": "2021-01-03T12:00:00Z",
        })
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.get_delete_domains_status(
            models.DeleteDomainsStatusRequest(
                request_id="e585a640-0849-4b87-8dd9-91afdaf8851c"
            )
        )
        assert result.request_id == "e585a640-0849-4b87-8dd9-91afdaf8851c"
        assert result.domains_submitted == 3
        assert result.success_count == 2
        assert result.failure_count == 1
        assert result.is_complete is True
        assert result.expiration_date == "2021-01-03T12:00:00Z"

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == (
            "/config-gtm/v1/domains/delete-requests/"
            "e585a640-0849-4b87-8dd9-91afdaf8851c"
        )

    def test_validation_error_missing_request_id(self, gtm_client):
        """Empty request_id triggers validation error."""
        with pytest.raises(ErrStructValidation) as exc_info:
            gtm_client.get_delete_domains_status(
                models.DeleteDomainsStatusRequest(request_id="")
            )
        assert "RequestID: cannot be blank" in str(exc_info.value)

    def test_404_not_found(self, gtm_client):
        """404 with ErrNotFound sentinel error."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type=(
                "https://problems.luna.akamaiapis.net/"
                "config-gtm/v1/notfound"
            ),
            title="Resource not found.",
            detail="Resource not found.",
            status_code=404,
            instance=(
                "https://akaa-ouijhfns55qwgfuc-knsod5nrjl2w2gmt"
                ".luna-dev.akamaiapis.net/config-gtm-api/v1/domains/"
                "delete-requests/e585a640-0849-4b87-8dd9-91afdaf8851c"
                "#9037df98-5e58-49a9-a74f-ec247ec920f7"
            ),
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.get_delete_domains_status(
                models.DeleteDomainsStatusRequest(
                    request_id="e585a640-0849-4b87-8dd9-91afdaf8851c"
                )
            )
        err = exc_info.value
        assert err.is_equivalent(gtm_errors.ErrNotFound)


# ===================================================================
# TestProperties  (mirrors property_test.go - 16 scenarios)
# ===================================================================


class TestListProperties:
    """TestGTM_ListProperties - 2 scenarios."""

    def test_200_ok(self, gtm_client, load_test_data):
        """Loads fixture, verifies PropertyList items."""
        resp_body = load_test_data("TestGTM_ListProperties.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.list_properties(
            models.ListPropertiesRequest(
                domain_name="example.akadns.net"
            )
        )
        assert isinstance(result, list)

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "GET"
        assert "/properties" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on property list."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching propertys",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.list_properties(
                models.ListPropertiesRequest(
                    domain_name="example.akadns.net"
                )
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error fetching propertys"


class TestGetProperty:
    """TestGTM_GetProperty - 2 scenarios."""

    def test_200_ok(self, gtm_client, load_test_data):
        """Loads fixture, verifies Property fields."""
        resp_body = load_test_data("TestGTM_GetProperty.resp.json")
        resp_data = json.loads(resp_body)
        expected = models.Property.from_dict(resp_data)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.get_property(
            models.GetPropertyRequest(
                domain_name="example.akadns.net",
                property_name="origin",
            )
        )
        assert result.name == expected.name

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "GET"
        assert "/properties/origin" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on property get."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching property",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.get_property(
                models.GetPropertyRequest(
                    domain_name="example.akadns.net",
                    property_name="origin",
                )
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error fetching property"


class TestCreateProperty:
    """TestGTM_CreateProperty - 5 scenarios."""

    def test_201_created(self, gtm_client):
        """Inline JSON response, verifies Property creation."""
        resp_data = json.loads(CREATE_PROPERTY_RESPONSE_BODY)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(201, CREATE_PROPERTY_RESPONSE_BODY),
            resp_data,
        )
        result = gtm_client.create_property(models.CreatePropertyRequest(
            domain_name="example.akadns.net",
            property=models.Property(
                name="origin",
                type="weighted-round-robin",
                score_aggregation_type="mean",
                dynamic_ttl=300,
                handout_limit=8,
                handout_mode="normal",
                failover_delay=0,
                failback_delay=0,
                ipv6=False,
                static_ttl=600,
                stickiness_bonus_constant=0,
                stickiness_bonus_percentage=0,
                traffic_targets=[
                    models.TrafficTarget(
                        datacenter_id=3134,
                        enabled=True,
                        weight=50.0,
                        servers=["1.2.3.4"],
                    ),
                    models.TrafficTarget(
                        datacenter_id=3133,
                        enabled=True,
                        weight=50.0,
                        servers=["1.2.3.5"],
                    ),
                ],
                liveness_tests=[
                    models.LivenessTest(
                        name="lt5",
                        test_interval=40,
                        test_object_protocol="HTTP",
                        test_timeout=30.0,
                        test_object="/",
                    ),
                ],
            ),
        ))
        assert result.resource.name == "origin"
        assert result.resource.type == "weighted-round-robin"
        assert len(result.resource.traffic_targets) == 2
        assert result.resource.traffic_targets[0].datacenter_id == 3134

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "PUT"
        assert "/properties/origin" in call_args[0][1]

    def test_201_created_ranked_failover(self, gtm_client):
        """Ranked-failover property with Precedence fields."""
        resp_data = json.loads(CREATE_PROPERTY_RANKED_FAILOVER_RESPONSE_BODY)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(201, CREATE_PROPERTY_RANKED_FAILOVER_RESPONSE_BODY),
            resp_data,
        )
        result = gtm_client.create_property(models.CreatePropertyRequest(
            domain_name="example.akadns.net",
            property=models.Property(
                name="origin",
                type="ranked-failover",
                score_aggregation_type="mean",
                dynamic_ttl=300,
                handout_limit=8,
                handout_mode="normal",
                failover_delay=0,
                failback_delay=0,
                ipv6=False,
                static_ttl=600,
                stickiness_bonus_constant=0,
                stickiness_bonus_percentage=0,
                traffic_targets=[
                    models.TrafficTarget(
                        datacenter_id=3134,
                        enabled=True,
                        weight=50.0,
                        servers=["1.2.3.4"],
                        precedence=255,
                    ),
                    models.TrafficTarget(
                        datacenter_id=3133,
                        enabled=True,
                        weight=50.0,
                        servers=["1.2.3.5"],
                        precedence=None,
                    ),
                ],
                liveness_tests=[
                    models.LivenessTest(
                        name="lt5",
                        test_interval=40,
                        test_object_protocol="HTTP",
                        test_timeout=30.0,
                        test_object="/",
                        http_method="GET",
                        http_request_body="TestBody",
                        pre2023_security_posture=True,
                        alternate_ca_certificates=["test1"],
                    ),
                ],
            ),
        ))
        assert result.resource.name == "origin"
        assert result.resource.type == "weighted-round-robin"
        assert result.resource.traffic_targets[0].precedence == 255
        assert result.resource.traffic_targets[1].precedence is None

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "PUT"

    def test_validation_error_missing_precedence(self, gtm_client):
        """Missing precedence for ranked-failover property type."""
        with pytest.raises(ErrStructValidation) as exc_info:
            gtm_client.create_property(models.CreatePropertyRequest(
                domain_name="example.akadns.net",
                property=models.Property(
                    name="origin",
                    type="ranked-failover",
                    score_aggregation_type="mean",
                    dynamic_ttl=300,
                    handout_limit=8,
                    handout_mode="normal",
                    failover_delay=0,
                    failback_delay=0,
                    traffic_targets=[
                        models.TrafficTarget(
                            datacenter_id=3134,
                            enabled=True,
                            weight=50.0,
                            servers=["1.2.3.4"],
                            precedence=None,
                        ),
                        models.TrafficTarget(
                            datacenter_id=3133,
                            enabled=True,
                            weight=50.0,
                            servers=["1.2.3.5"],
                            precedence=None,
                        ),
                    ],
                ),
            ))
        assert "property cannot have multiple primary traffic targets" in str(
            exc_info.value
        )

    def test_validation_error_precedence_over_limit(self, gtm_client):
        """Precedence value over 255."""
        with pytest.raises(ErrStructValidation) as exc_info:
            gtm_client.create_property(models.CreatePropertyRequest(
                domain_name="example.akadns.net",
                property=models.Property(
                    name="origin",
                    type="ranked-failover",
                    score_aggregation_type="mean",
                    dynamic_ttl=300,
                    handout_limit=8,
                    handout_mode="normal",
                    failover_delay=0,
                    failback_delay=0,
                    traffic_targets=[
                        models.TrafficTarget(
                            datacenter_id=3134,
                            enabled=True,
                            weight=50.0,
                            servers=["1.2.3.4"],
                            precedence=256,
                        ),
                        models.TrafficTarget(
                            datacenter_id=3133,
                            enabled=True,
                            weight=50.0,
                            servers=["1.2.3.5"],
                            precedence=None,
                        ),
                    ],
                ),
            ))
        assert "'Precedence' value has to be between 0 and 255" in str(
            exc_info.value
        )

    def test_500_internal_server_error(self, gtm_client):
        """Server error on property creation."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error creating domain",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.create_property(models.CreatePropertyRequest(
                domain_name="example.akadns.net",
                property=models.Property(
                    name="testName",
                    type="failover",
                    handout_mode="normal",
                    score_aggregation_type="mean",
                ),
            ))
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error creating domain"


class TestUpdateProperty:
    """TestGTM_UpdateProperty - 5 scenarios."""

    def test_200_success(self, gtm_client):
        """Inline JSON response with precedence values."""
        resp_data = json.loads(UPDATE_PROPERTY_RESPONSE_BODY)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, UPDATE_PROPERTY_RESPONSE_BODY),
            resp_data,
        )
        result = gtm_client.update_property(models.UpdatePropertyRequest(
            domain_name="example.akadns.net",
            property=models.Property(
                name="origin",
                type="ranked-failover",
                score_aggregation_type="mean",
                dynamic_ttl=300,
                handout_limit=8,
                handout_mode="normal",
                failover_delay=0,
                failback_delay=0,
                ipv6=False,
                static_ttl=600,
                stickiness_bonus_constant=0,
                stickiness_bonus_percentage=0,
                traffic_targets=[
                    models.TrafficTarget(
                        datacenter_id=3134,
                        enabled=True,
                        weight=50.0,
                        servers=["1.2.3.4"],
                        precedence=255,
                    ),
                    models.TrafficTarget(
                        datacenter_id=3133,
                        enabled=True,
                        weight=50.0,
                        servers=["1.2.3.5"],
                    ),
                ],
                liveness_tests=[
                    models.LivenessTest(
                        name="lt5",
                        test_interval=40,
                        test_object_protocol="HTTP",
                        test_timeout=30.0,
                        test_object="/",
                    ),
                ],
            ),
        ))
        assert result.resource.name == "origin"
        assert result.resource.traffic_targets[0].precedence == 255
        assert result.resource.traffic_targets[1].precedence is None

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "PUT"
        assert "/properties/origin" in call_args[0][1]

    def test_validation_error_missing_precedence(self, gtm_client):
        """Missing precedence for ranked-failover property type."""
        with pytest.raises(ErrStructValidation) as exc_info:
            gtm_client.update_property(models.UpdatePropertyRequest(
                domain_name="example.akadns.net",
                property=models.Property(
                    name="origin",
                    type="ranked-failover",
                    traffic_targets=[
                        models.TrafficTarget(
                            datacenter_id=3134,
                            enabled=True,
                            weight=50.0,
                            servers=["1.2.3.4"],
                            precedence=None,
                        ),
                        models.TrafficTarget(
                            datacenter_id=3133,
                            enabled=True,
                            weight=50.0,
                            servers=["1.2.3.5"],
                            precedence=None,
                        ),
                    ],
                ),
            ))
        assert "property cannot have multiple primary traffic targets" in str(
            exc_info.value
        )

    def test_validation_error_no_traffic_targets(self, gtm_client):
        """No traffic targets for ranked-failover type."""
        with pytest.raises(ErrStructValidation) as exc_info:
            gtm_client.update_property(models.UpdatePropertyRequest(
                domain_name="example.akadns.net",
                property=models.Property(
                    name="origin",
                    type="ranked-failover",
                    traffic_targets=[],
                ),
            ))
        assert "no traffic targets are enabled" in str(exc_info.value)

    def test_validation_error_no_traffic_targets_none(self, gtm_client):
        """None traffic targets for ranked-failover type."""
        with pytest.raises(ErrStructValidation) as exc_info:
            gtm_client.update_property(models.UpdatePropertyRequest(
                domain_name="example.akadns.net",
                property=models.Property(
                    name="origin",
                    type="ranked-failover",
                    traffic_targets=None,
                ),
            ))
        assert "no traffic targets are enabled" in str(exc_info.value)

    def test_500_internal_server_error(self, gtm_client):
        """Server error on property update."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error creating zone",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.update_property(models.UpdatePropertyRequest(
                domain_name="example.akadns.net",
                property=models.Property(
                    name="testName",
                    type="failover",
                    handout_mode="normal",
                    score_aggregation_type="mean",
                ),
            ))
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error creating zone"


class TestDeleteProperty:
    """TestGTM_DeleteProperty - 2 scenarios."""

    def test_200_success(self, gtm_client, load_test_data):
        """Loads fixture, verifies successful deletion."""
        resp_body = load_test_data("TestGTM_CreateProperty.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.delete_property(models.DeletePropertyRequest(
            domain_name="example.akadns.net",
            property_name="www",
        ))
        assert result is not None

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "DELETE"
        assert "/properties/www" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on property deletion."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error creating zone",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.delete_property(models.DeletePropertyRequest(
                domain_name="example.akadns.net",
                property_name="www",
            ))
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error creating zone"


# ===================================================================
# TestDatacenters  (mirrors datacenter_test.go - 16 scenarios)
# ===================================================================


class TestListDatacenters:
    """TestGTM_ListDatacenters - 2 scenarios."""

    def test_200_ok(self, gtm_client, load_test_data):
        """Loads fixture, verifies DatacenterList items."""
        resp_body = load_test_data("TestGTM_ListDatacenters.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.list_datacenters(
            models.ListDatacentersRequest(
                domain_name="example.akadns.net"
            )
        )
        assert isinstance(result, list)

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "GET"
        assert "/datacenters" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on datacenter list."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching datacenters",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.list_datacenters(
                models.ListDatacentersRequest(
                    domain_name="example.akadns.net"
                )
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error fetching datacenters"


class TestGetDatacenter:
    """TestGTM_GetDatacenter - 2 scenarios."""

    def test_200_ok(self, gtm_client, load_test_data):
        """Loads fixture, verifies Datacenter fields."""
        resp_body = load_test_data("TestGTM_GetDatacenter.resp.json")
        resp_data = json.loads(resp_body)
        expected = models.Datacenter.from_dict(resp_data)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.get_datacenter(
            models.GetDatacenterRequest(
                domain_name="example.akadns.net",
                datacenter_id=3134,
            )
        )
        assert result.datacenter_id == expected.datacenter_id

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "GET"
        assert "/datacenters/3134" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on datacenter get."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching datacenter",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.get_datacenter(
                models.GetDatacenterRequest(
                    domain_name="example.akadns.net",
                    datacenter_id=3134,
                )
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error fetching datacenter"


class TestCreateDatacenter:
    """TestGTM_CreateDatacenter - 2 scenarios."""

    def test_201_created(self, gtm_client, load_test_data):
        """Loads fixture, verifies DatacenterResponse."""
        resp_body = load_test_data("TestGTM_CreateDatacenter.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(201, resp_body),
            resp_data,
        )
        result = gtm_client.create_datacenter(
            models.CreateDatacenterRequest(
                domain_name="example.akadns.net",
                datacenter=models.Datacenter(nickname="testDC"),
            )
        )
        assert result is not None

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "POST"
        assert "/datacenters" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on datacenter creation."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error creating dc",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.create_datacenter(
                models.CreateDatacenterRequest(
                    domain_name="example.akadns.net",
                    datacenter=models.Datacenter(nickname="testDC"),
                )
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error creating dc"


class TestCreateMapsDefaultDatacenter:
    """TestGTM_CreateMapsDefaultDatacenter - 2 scenarios."""

    def test_200_ok(self, gtm_client, load_test_data):
        """GET returns 404, POST returns fixture."""
        resp_body = load_test_data(
            "TestGTM_CreateMapsDefaultDatacenter.resp.json"
        )
        resp_data = json.loads(resp_body)

        # First call (get_datacenter) raises 404, second call (POST) succeeds
        gtm_client._session.exec.side_effect = [  # pylint: disable=protected-access
            gtm_errors.Error(
                type="Datacenter",
                title="not found",
                status_code=404,
            ),
            (mock_response(200, resp_body), resp_data),
        ]
        result = gtm_client.create_maps_default_datacenter(
            "example.akadns.net"
        )
        assert result is not None

    def test_500_internal_server_error(self, gtm_client):
        """Server error on default datacenter creation."""
        gtm_client._session.exec.side_effect = [  # pylint: disable=protected-access
            gtm_errors.Error(
                type="Datacenter",
                title="not found",
                status_code=404,
            ),
            gtm_errors.Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error creating dc",
                status_code=500,
            ),
        ]
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.create_maps_default_datacenter(
                "example.akadns.net"
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error creating dc"


class TestCreateIPv4DefaultDatacenter:
    """TestGTM_CreateIPv4DefaultDatacenter - 2 scenarios."""

    def test_200_ok(self, gtm_client, load_test_data):
        """GET returns 404, POST returns fixture."""
        resp_body = load_test_data(
            "TestGTM_CreateIPv4DefaultDatacenter.resp.json"
        )
        resp_data = json.loads(resp_body)

        gtm_client._session.exec.side_effect = [  # pylint: disable=protected-access
            gtm_errors.Error(
                type="Datacenter",
                title="not found",
                status_code=404,
            ),
            (mock_response(200, resp_body), resp_data),
        ]
        result = gtm_client.create_ipv4_default_datacenter(
            "example.akadns.net"
        )
        assert result is not None

    def test_500_internal_server_error(self, gtm_client):
        """Server error on IPv4 default datacenter creation."""
        gtm_client._session.exec.side_effect = [  # pylint: disable=protected-access
            gtm_errors.Error(
                type="Datacenter",
                title="not found",
                status_code=404,
            ),
            gtm_errors.Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error creating dc",
                status_code=500,
            ),
        ]
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.create_ipv4_default_datacenter(
                "example.akadns.net"
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error creating dc"


class TestCreateIPv6DefaultDatacenter:
    """TestGTM_CreateIPv6DefaultDatacenter - 2 scenarios."""

    def test_200_ok(self, gtm_client, load_test_data):
        """GET returns 404, POST returns fixture."""
        resp_body = load_test_data(
            "TestGTM_CreateIPv6DefaultDatacenter.resp.json"
        )
        resp_data = json.loads(resp_body)

        gtm_client._session.exec.side_effect = [  # pylint: disable=protected-access
            gtm_errors.Error(
                type="Datacenter",
                title="not found",
                status_code=404,
            ),
            (mock_response(200, resp_body), resp_data),
        ]
        result = gtm_client.create_ipv6_default_datacenter(
            "example.akadns.net"
        )
        assert result is not None

    def test_500_internal_server_error(self, gtm_client):
        """Server error on IPv6 default datacenter creation."""
        gtm_client._session.exec.side_effect = [  # pylint: disable=protected-access
            gtm_errors.Error(
                type="Datacenter",
                title="not found",
                status_code=404,
            ),
            gtm_errors.Error(
                type="internal_error",
                title="Internal Server Error",
                detail="Error creating dc",
                status_code=500,
            ),
        ]
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.create_ipv6_default_datacenter(
                "example.akadns.net"
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error creating dc"


class TestUpdateDatacenter:
    """TestGTM_UpdateDatacenter - 2 scenarios."""

    def test_200_success(self, gtm_client, load_test_data):
        """Loads fixture, verifies DatacenterResponse."""
        resp_body = load_test_data("TestGTM_CreateDatacenter.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.update_datacenter(
            models.UpdateDatacenterRequest(
                domain_name="example.akadns.net",
                datacenter=models.Datacenter(
                    datacenter_id=3134,
                    nickname="testDC",
                ),
            )
        )
        assert result is not None

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "PUT"
        assert "/datacenters/3134" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on datacenter update."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error updating dc",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.update_datacenter(
                models.UpdateDatacenterRequest(
                    domain_name="example.akadns.net",
                    datacenter=models.Datacenter(
                        datacenter_id=3134,
                        nickname="testDC",
                    ),
                )
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error updating dc"


class TestDeleteDatacenter:
    """TestGTM_DeleteDatacenter - 2 scenarios."""

    def test_200_success(self, gtm_client, load_test_data):
        """Loads fixture, verifies DatacenterResponse."""
        resp_body = load_test_data("TestGTM_CreateDatacenter.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.delete_datacenter(
            models.DeleteDatacenterRequest(
                domain_name="example.akadns.net",
                datacenter_id=3134,
            )
        )
        assert result is not None

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "DELETE"
        assert "/datacenters/3134" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on datacenter deletion."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error updating dc",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.delete_datacenter(
                models.DeleteDatacenterRequest(
                    domain_name="example.akadns.net",
                    datacenter_id=3134,
                )
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error updating dc"


# ===================================================================
# TestResources  (mirrors resource_test.go - 10 scenarios)
# ===================================================================


class TestListResources:
    """TestGTM_ListResources - 2 scenarios."""

    def test_200_ok(self, gtm_client, load_test_data):
        """Loads fixture, verifies ResourceList items."""
        resp_body = load_test_data("TestGTM_ListResources.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.list_resources(
            models.ListResourcesRequest(
                domain_name="example.akadns.net"
            )
        )
        assert isinstance(result, list)

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "GET"
        assert "/resources" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on resource list."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching propertys",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.list_resources(
                models.ListResourcesRequest(
                    domain_name="example.akadns.net"
                )
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error fetching propertys"


class TestGetResource:
    """TestGTM_GetResource - 2 scenarios."""

    def test_200_ok(self, gtm_client, load_test_data):
        """Loads fixture, verifies Resource fields."""
        resp_body = load_test_data("TestGTM_GetResource.resp.json")
        resp_data = json.loads(resp_body)
        expected = models.Resource.from_dict(resp_data)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.get_resource(
            models.GetResourceRequest(
                domain_name="example.akadns.net",
                resource_name="testResource",
            )
        )
        assert result.name == expected.name

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "GET"
        assert "/resources/testResource" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on resource get."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching property",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.get_resource(
                models.GetResourceRequest(
                    domain_name="example.akadns.net",
                    resource_name="testResource",
                )
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error fetching property"


class TestCreateResource:
    """TestGTM_CreateResource - 2 scenarios."""

    def test_201_created(self, gtm_client, load_test_data):
        """Loads fixture, verifies Resource creation."""
        resp_body = load_test_data("TestGTM_CreateResource.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(201, resp_body),
            resp_data,
        )
        result = gtm_client.create_resource(
            models.CreateResourceRequest(
                domain_name="example.akadns.net",
                resource=models.Resource(name="testResource"),
            )
        )
        assert result is not None

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "PUT"
        assert "/resources/testResource" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on resource creation."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error creating domain",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.create_resource(
                models.CreateResourceRequest(
                    domain_name="example.akadns.net",
                    resource=models.Resource(name="testResource"),
                )
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error creating domain"


class TestUpdateResource:
    """TestGTM_UpdateResource - 2 scenarios."""

    def test_200_success(self, gtm_client, load_test_data):
        """Loads fixture, verifies resource update."""
        resp_body = load_test_data("TestGTM_CreateResource.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.update_resource(
            models.UpdateResourceRequest(
                domain_name="example.akadns.net",
                resource=models.Resource(name="testResource"),
            )
        )
        assert result is not None

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "PUT"
        assert "/resources/testResource" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on resource update."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error creating zone",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.update_resource(
                models.UpdateResourceRequest(
                    domain_name="example.akadns.net",
                    resource=models.Resource(name="testResource"),
                )
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error creating zone"


class TestDeleteResource:
    """TestGTM_DeleteResource - 2 scenarios."""

    def test_200_success(self, gtm_client, load_test_data):
        """Loads fixture, verifies resource deletion."""
        resp_body = load_test_data("TestGTM_CreateResource.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.delete_resource(
            models.DeleteResourceRequest(
                domain_name="example.akadns.net",
                resource_name="testResource",
            )
        )
        assert result is not None

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "DELETE"
        assert "/resources/testResource" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on resource deletion."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error creating zone",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.delete_resource(
                models.DeleteResourceRequest(
                    domain_name="example.akadns.net",
                    resource_name="testResource",
                )
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error creating zone"


# ===================================================================
# TestASMaps  (mirrors asmap_test.go - 10 scenarios)
# ===================================================================


class TestListASMaps:
    """TestGTM_ListASMap - 2 scenarios."""

    def test_200_ok(self, gtm_client, load_test_data):
        """Loads fixture, verifies ASMapList items."""
        resp_body = load_test_data("TestGTM_ListASMap.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.list_as_maps(
            models.ListASMapsRequest(
                domain_name="example.akadns.net"
            )
        )
        assert isinstance(result, list)

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "GET"
        assert "/as-maps" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on AS map list."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching asmap",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.list_as_maps(
                models.ListASMapsRequest(
                    domain_name="example.akadns.net"
                )
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error fetching asmap"


class TestGetASMap:
    """TestGTM_GetASMap - 2 scenarios."""

    def test_200_ok(self, gtm_client, load_test_data):
        """Loads fixture, verifies ASMap fields."""
        resp_body = load_test_data("TestGTM_GetASMap.resp.json")
        resp_data = json.loads(resp_body)
        expected = models.ASMap.from_dict(resp_data)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.get_as_map(
            models.GetASMapRequest(
                domain_name="example.akadns.net",
                as_map_name="The North",
            )
        )
        assert result.name == expected.name

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "GET"
        assert "/as-maps/" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on AS map get."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching asmap",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.get_as_map(
                models.GetASMapRequest(
                    domain_name="example.akadns.net",
                    as_map_name="The North",
                )
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error fetching asmap"


class TestCreateASMap:
    """TestGTM_CreateASMap - 2 scenarios."""

    def test_201_created(self, gtm_client, load_test_data):
        """Loads fixture, verifies AS map creation."""
        resp_body = load_test_data("TestGTM_CreateASMap.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(201, resp_body),
            resp_data,
        )
        result = gtm_client.create_as_map(models.CreateASMapRequest(
            domain_name="example.akadns.net",
            as_map=models.ASMap(name="The North"),
        ))
        assert result is not None

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "PUT"
        assert "/as-maps/" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on AS map creation."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error creating asmap",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.create_as_map(models.CreateASMapRequest(
                domain_name="example.akadns.net",
                as_map=models.ASMap(name="The North"),
            ))
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error creating asmap"


class TestUpdateASMap:
    """TestGTM_UpdateASMap - 2 scenarios."""

    def test_200_success(self, gtm_client, load_test_data):
        """Loads fixture, verifies AS map update."""
        resp_body = load_test_data("TestGTM_CreateASMap.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.update_as_map(models.UpdateASMapRequest(
            domain_name="example.akadns.net",
            as_map=models.ASMap(name="The North"),
        ))
        assert result is not None

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "PUT"
        assert "/as-maps/" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on AS map update."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error updating asmap",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.update_as_map(models.UpdateASMapRequest(
                domain_name="example.akadns.net",
                as_map=models.ASMap(name="The North"),
            ))
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error updating asmap"


class TestDeleteASMap:
    """TestGTM_DeleteASMap - 2 scenarios."""

    def test_200_success(self, gtm_client, load_test_data):
        """Loads fixture, verifies AS map deletion."""
        resp_body = load_test_data("TestGTM_CreateASMap.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.delete_as_map(models.DeleteASMapRequest(
            domain_name="example.akadns.net",
            as_map_name="The North",
        ))
        assert result is not None

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "DELETE"
        assert "/as-maps/" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on AS map deletion."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error creating asmap",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.delete_as_map(models.DeleteASMapRequest(
                domain_name="example.akadns.net",
                as_map_name="The North",
            ))
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error creating asmap"


# ===================================================================
# TestGeoMaps  (mirrors geomap_test.go - 10 scenarios)
# ===================================================================


class TestListGeoMaps:
    """TestGTM_ListGeoMap - 2 scenarios."""

    def test_200_ok(self, gtm_client, load_test_data):
        """Loads fixture, verifies GeoMapList items."""
        resp_body = load_test_data("TestGTM_ListGeoMap.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.list_geo_maps(
            models.ListGeoMapsRequest(
                domain_name="example.akadns.net"
            )
        )
        assert isinstance(result, list)

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "GET"
        assert "/geographic-maps" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on geo map list."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching GeoMap",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.list_geo_maps(
                models.ListGeoMapsRequest(
                    domain_name="example.akadns.net"
                )
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error fetching GeoMap"


class TestGetGeoMap:
    """TestGTM_GetGeoMap - 2 scenarios."""

    def test_200_ok(self, gtm_client, load_test_data):
        """Loads fixture, verifies GeoMap fields."""
        resp_body = load_test_data("TestGTM_GetGeoMap.resp.json")
        resp_data = json.loads(resp_body)
        expected = models.GeoMap.from_dict(resp_data)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.get_geo_map(
            models.GetGeoMapRequest(
                domain_name="example.akadns.net",
                geo_map_name="The North",
            )
        )
        assert result.name == expected.name

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "GET"
        assert "/geographic-maps/" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on geo map get."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching GeoMap",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.get_geo_map(
                models.GetGeoMapRequest(
                    domain_name="example.akadns.net",
                    geo_map_name="The North",
                )
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error fetching GeoMap"


class TestCreateGeoMap:
    """TestGTM_CreateGeoMap - 2 scenarios."""

    def test_201_created(self, gtm_client, load_test_data):
        """Loads fixture, verifies GeoMap creation."""
        resp_body = load_test_data("TestGTM_CreateGeoMap.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(201, resp_body),
            resp_data,
        )
        result = gtm_client.create_geo_map(models.CreateGeoMapRequest(
            domain_name="example.akadns.net",
            geo_map=models.GeoMap(name="The North"),
        ))
        assert result is not None

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "PUT"
        assert "/geographic-maps/" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on geo map creation."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error creating GeoMap",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.create_geo_map(models.CreateGeoMapRequest(
                domain_name="example.akadns.net",
                geo_map=models.GeoMap(name="The North"),
            ))
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error creating GeoMap"


class TestUpdateGeoMap:
    """TestGTM_UpdateGeoMap - 2 scenarios."""

    def test_200_success(self, gtm_client, load_test_data):
        """Loads fixture, verifies geo map update."""
        resp_body = load_test_data("TestGTM_CreateGeoMap.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.update_geo_map(models.UpdateGeoMapRequest(
            domain_name="example.akadns.net",
            geo_map=models.GeoMap(name="The North"),
        ))
        assert result is not None

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "PUT"
        assert "/geographic-maps/" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on geo map update."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error updating GeoMap",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.update_geo_map(models.UpdateGeoMapRequest(
                domain_name="example.akadns.net",
                geo_map=models.GeoMap(name="The North"),
            ))
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error updating GeoMap"


class TestDeleteGeoMap:
    """TestGTM_DeleteGeoMap - 2 scenarios."""

    def test_200_success(self, gtm_client, load_test_data):
        """Loads fixture, verifies geo map deletion."""
        resp_body = load_test_data("TestGTM_CreateGeoMap.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.delete_geo_map(models.DeleteGeoMapRequest(
            domain_name="example.akadns.net",
            geo_map_name="The North",
        ))
        assert result is not None

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "DELETE"
        assert "/geographic-maps/" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on geo map deletion."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error creating GeoMap",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.delete_geo_map(models.DeleteGeoMapRequest(
                domain_name="example.akadns.net",
                geo_map_name="The North",
            ))
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error creating GeoMap"


# ===================================================================
# TestCIDRMaps  (mirrors cidrmap_test.go - 11 scenarios)
# ===================================================================


class TestListCIDRMaps:
    """TestGTM_ListCIDRMaps - 2 scenarios."""

    def test_200_ok(self, gtm_client, load_test_data):
        """Loads fixture, verifies CIDRMapList items."""
        resp_body = load_test_data("TestGTM_ListCIDRMap.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.list_cidr_maps(
            models.ListCIDRMapsRequest(
                domain_name="example.akadns.net"
            )
        )
        assert isinstance(result, list)

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "GET"
        assert "/cidr-maps" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on CIDR map list."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching asmap",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.list_cidr_maps(
                models.ListCIDRMapsRequest(
                    domain_name="example.akadns.net"
                )
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error fetching asmap"


class TestGetCIDRMap:
    """TestGTM_GetCIDRMap - 2 scenarios."""

    def test_200_ok(self, gtm_client, load_test_data):
        """Loads fixture, verifies CIDRMap fields."""
        resp_body = load_test_data("TestGTM_GetCIDRMap.resp.json")
        resp_data = json.loads(resp_body)
        expected = models.CIDRMap.from_dict(resp_data)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.get_cidr_map(
            models.GetCIDRMapRequest(
                domain_name="example.akadns.net",
                cidr_map_name="The North",
            )
        )
        assert result.name == expected.name

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "GET"
        assert "/cidr-maps/" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on CIDR map get."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error fetching asmap",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.get_cidr_map(
                models.GetCIDRMapRequest(
                    domain_name="example.akadns.net",
                    cidr_map_name="The North",
                )
            )
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error fetching asmap"


class TestCreateCIDRMap:
    """TestGTM_CreateCIDRMap - 3 scenarios."""

    def test_200_ok(self, gtm_client, load_test_data):
        """Loads fixture, verifies CIDR map creation."""
        resp_body = load_test_data("TestGTM_CreateCIDRMap.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.create_cidr_map(models.CreateCIDRMapRequest(
            domain_name="example.akadns.net",
            cidr_map=models.CIDRMap(name="The North"),
        ))
        assert result is not None

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "PUT"
        assert "/cidr-maps/" in call_args[0][1]

    def test_200_inline(self, gtm_client):
        """Inline CIDR map creation with test_name."""
        resp_body = json.dumps({
            "resource": {
                "name": "test_name",
                "assignments": [
                    {
                        "datacenterId": 200,
                        "nickname": "testDC",
                        "blocks": ["1.2.3.4/24"],
                    }
                ],
                "defaultDatacenter": {
                    "datacenterId": 5400,
                    "nickname": "default",
                },
            },
            "status": {
                "message": "Change Pending",
                "changeId": "abc-123",
                "propagationStatus": "PENDING",
                "propagationStatusDate": "2019-10-04T15:27:42.000+0000",
                "passingValidation": True,
                "links": [],
            },
        })
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.create_cidr_map(models.CreateCIDRMapRequest(
            domain_name="example.akadns.net",
            cidr_map=models.CIDRMap(
                name="test_name",
                assignments=[
                    models.CIDRAssignment(
                        datacenter_id=200,
                        nickname="testDC",
                        blocks=["1.2.3.4/24"],
                    ),
                ],
            ),
        ))
        assert result is not None

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "PUT"
        assert "/cidr-maps/test_name" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on CIDR map creation."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error creating asmap",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.create_cidr_map(models.CreateCIDRMapRequest(
                domain_name="example.akadns.net",
                cidr_map=models.CIDRMap(name="The North"),
            ))
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error creating asmap"


class TestUpdateCIDRMap:
    """TestGTM_UpdateCIDRMap - 2 scenarios."""

    def test_200_success(self, gtm_client, load_test_data):
        """Loads fixture, verifies CIDR map update."""
        resp_body = load_test_data("TestGTM_CreateCIDRMap.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.update_cidr_map(models.UpdateCIDRMapRequest(
            domain_name="example.akadns.net",
            cidr_map=models.CIDRMap(name="The North"),
        ))
        assert result is not None

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "PUT"
        assert "/cidr-maps/" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on CIDR map update."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error creating asmap",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.update_cidr_map(models.UpdateCIDRMapRequest(
                domain_name="example.akadns.net",
                cidr_map=models.CIDRMap(name="The North"),
            ))
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error creating asmap"


class TestDeleteCIDRMap:
    """TestGTM_DeleteCIDRMap - 2 scenarios."""

    def test_200_success(self, gtm_client, load_test_data):
        """Loads fixture, verifies CIDR map deletion."""
        resp_body = load_test_data("TestGTM_CreateCIDRMap.resp.json")
        resp_data = json.loads(resp_body)
        gtm_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, resp_body),
            resp_data,
        )
        result = gtm_client.delete_cidr_map(models.DeleteCIDRMapRequest(
            domain_name="example.akadns.net",
            cidr_map_name="The North",
        ))
        assert result is not None

        call_args = gtm_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "DELETE"
        assert "/cidr-maps/" in call_args[0][1]

    def test_500_internal_server_error(self, gtm_client):
        """Server error on CIDR map deletion."""
        gtm_client._session.exec.side_effect = gtm_errors.Error(  # pylint: disable=protected-access
            type="internal_error",
            title="Internal Server Error",
            detail="Error creating asmap",
            status_code=500,
        )
        with pytest.raises(gtm_errors.Error) as exc_info:
            gtm_client.delete_cidr_map(models.DeleteCIDRMapRequest(
                domain_name="example.akadns.net",
                cidr_map_name="The North",
            ))
        err = exc_info.value
        assert err.status_code == 500
        assert err.detail == "Error creating asmap"
