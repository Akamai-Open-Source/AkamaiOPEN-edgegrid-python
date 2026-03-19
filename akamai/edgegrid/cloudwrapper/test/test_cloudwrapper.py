# pylint: disable=missing-function-docstring,too-many-lines,line-too-long
# pylint: disable=too-many-statements
"""Unit tests for the Cloud Wrapper API client.

Mirrors all 7 Go test files for comprehensive coverage of
configurations, properties, capacity, locations, multi-CDN,
error handling, and client construction.

All responseBody values are VERBATIM from Go tests and NEVER modified.
"""

import json
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.cloudwrapper import CloudWrapperClient
from akamai.edgegrid.cloudwrapper import models as _models  # noqa: F401
from akamai.edgegrid.cloudwrapper import errors as _errors  # noqa: F401
from akamai.edgegrid.cloudwrapper.models import (
    GetConfigurationRequest,
    CreateConfigurationRequest,
    CreateConfigurationRequestBody,
    UpdateConfigurationRequest,
    UpdateConfigurationRequestBody,
    DeleteConfigurationRequest,
    ActivateConfigurationRequest,
    ListPropertiesRequest,
    ListOriginsRequest,
    ListCapacitiesRequest,
    ListAuthKeysRequest,
    MultiCDNSettings,
    BOCC,
    DataStreams,
    CDN,
    CDNAuthKey,
    Origin,
    ConfigLocationReq,
    Capacity,
)
from akamai.edgegrid.cloudwrapper.errors import (
    Error,
    parse_cloudwrapper_error,
)
from akamai.edgegrid.session import Session
from akamai.edgegrid.cloudwrapper.test.conftest import (
    make_mock_response,
    assert_request_made,
)


# ---------------------------------------------------------------------------
# Helper: exec side-effect that invokes the real error_parser lambda
# ---------------------------------------------------------------------------

def _server_error_side_effect(status_code, body):
    """Create a side_effect for mock_session.exec that invokes the
    error_parser keyword argument exactly as Session.exec would for a
    non-2xx response, then raises the resulting Error.
    """
    def _side_effect(*_args, **kwargs):
        error_parser = kwargs.get("error_parser")
        resp = MagicMock()
        resp.status_code = status_code
        resp.text = body
        resp.content = body.encode("utf-8") if body else b""
        try:
            resp.json.return_value = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            resp.json.side_effect = json.JSONDecodeError("", "", 0)
        if error_parser:
            raise error_parser(resp)
    return _side_effect


# ===================================================================
# Error Tests — from errors_test.go
# ===================================================================

class TestNewError:
    """Mirrors Go TestNewError (errors_test.go lines 15-109)."""

    def test_bad_request_400(self):
        body = (
            '{\n'
            '  "type": "bad-request",\n'
            '  "title": "Bad Request",\n'
            '  "instance": "30109837-7ea6-4b14-a41d-50cfb12a4b03",\n'
            '  "status": 400,\n'
            '  "detail": "Erroneous data input",\n'
            '  "errors": [\n'
            '    {\n'
            '      "type": "bad-request",\n'
            '      "title": "Bad Request",\n'
            '      "detail": "Configuration with name UpdateConfiguration'
            ' already exists in account 1234-3KNWKV.",\n'
            '      "illegalValue": "UpdateConfiguration",\n'
            '      "illegalParameter": "configurationName"\n'
            '    },\n'
            '    {\n'
            '      "type": "bad-request",\n'
            '      "title": "Bad Request",\n'
            '      "detail": "One or more ARL Property is already used'
            ' in another configuration.",\n'
            '      "illegalValue": [\n'
            '        {\n'
            '          "propertyId": "123010"\n'
            '        }\n'
            '      ],\n'
            '      "illegalParameter": "properties"\n'
            '    }\n'
            '  ]\n'
            '}'
        )
        resp = MagicMock()
        resp.status_code = 400
        resp.text = body
        resp.content = body.encode("utf-8")
        resp.json.return_value = json.loads(body)

        result = parse_cloudwrapper_error(resp)

        assert result.type == "bad-request"
        assert result.title == "Bad Request"
        assert result.instance == "30109837-7ea6-4b14-a41d-50cfb12a4b03"
        assert result.status == 400
        assert result.detail == "Erroneous data input"
        assert len(result.errors) == 2

        item0 = result.errors[0]
        assert item0.type == "bad-request"
        assert item0.title == "Bad Request"
        assert item0.detail == (
            "Configuration with name UpdateConfiguration"
            " already exists in account 1234-3KNWKV."
        )
        assert item0.illegal_value == "UpdateConfiguration"
        assert item0.illegal_parameter == "configurationName"

        item1 = result.errors[1]
        assert item1.type == "bad-request"
        assert item1.title == "Bad Request"
        assert item1.detail == (
            "One or more ARL Property is already used"
            " in another configuration."
        )
        assert item1.illegal_value == [{"propertyId": "123010"}]
        assert item1.illegal_parameter == "properties"

    def test_invalid_response_body_assign_status_code(self):
        resp = MagicMock()
        resp.status_code = 500
        resp.text = "test"
        resp.content = b"test"
        resp.json.side_effect = json.JSONDecodeError("", "", 0)

        result = parse_cloudwrapper_error(resp)

        assert result.title == (
            "Failed to unmarshal error body. Cloud Wrapper API failed."
            " Check details for more information."
        )
        assert result.detail == "test"
        assert result.status == 500


class TestIs:  # pylint: disable=too-few-public-methods
    """Mirrors Go TestIs (errors_test.go lines 112-145)."""

    @pytest.mark.parametrize(
        "test_name,err,target,want",
        [
            (
                "different error code",
                Error(status=404),
                Error(status=401),
                False,
            ),
            (
                "same error code",
                Error(status=404),
                Error(status=404),
                True,
            ),
            (
                "same error code and title",
                Error(status=404, title="some error"),
                Error(status=404, title="some error"),
                True,
            ),
            (
                "same error code and different error message",
                Error(status=404, title="some error"),
                Error(status=404, title="other error"),
                False,
            ),
        ],
    )
    def test_is(self, test_name, err, target, want):
        assert err.is_equivalent(target) == want, f"[{test_name}] expected {want}"


class TestJsonErrorUnmarshalling:
    """Mirrors Go TestJsonErrorUnmarshalling (errors_test.go 147-202)."""

    def test_html_response(self):
        body = "<HTML><HEAD>...</HEAD><BODY>...</BODY></HTML>"
        resp = MagicMock()
        resp.status_code = 0
        resp.text = body
        resp.content = body.encode("utf-8")
        resp.json.side_effect = json.JSONDecodeError("", "", 0)

        result = parse_cloudwrapper_error(resp)

        assert result.type == ""
        assert result.title == (
            "Failed to unmarshal error body. Cloud Wrapper API failed."
            " Check details for more information."
        )
        assert result.detail == "<HTML><HEAD>...</HEAD><BODY>...</BODY></HTML>"

    def test_plain_text_response(self):
        body = (
            "Your request did not succeed as this operation has"
            " reached  the limit for your account. Please try"
            " after 2024-01-16T15:20:55.945Z"
        )
        resp = MagicMock()
        resp.status_code = 0
        resp.text = body
        resp.content = body.encode("utf-8")
        resp.json.side_effect = json.JSONDecodeError("", "", 0)

        result = parse_cloudwrapper_error(resp)

        assert result.type == ""
        assert result.title == (
            "Failed to unmarshal error body. Cloud Wrapper API failed."
            " Check details for more information."
        )
        assert result.detail == body

    def test_xml_response(self):
        body = '<Root><Item id="1" name="Example" /></Root>'
        resp = MagicMock()
        resp.status_code = 0
        resp.text = body
        resp.content = body.encode("utf-8")
        resp.json.side_effect = json.JSONDecodeError("", "", 0)

        result = parse_cloudwrapper_error(resp)

        assert result.type == ""
        assert result.title == (
            "Failed to unmarshal error body. Cloud Wrapper API failed."
            " Check details for more information."
        )
        assert result.detail == '<Root><Item id="1" name="Example" /></Root>'


# ===================================================================
# Standard error body shared across many 500 tests
# ===================================================================

_SERVER_ERROR_BODY = (
    '{\n'
    '    "type": "/cloudwrapper/error-types/cloudwrapper-server-error",\n'
    '    "title": "An unexpected error has occurred.",\n'
    '    "detail": "Error processing request",\n'
    '    "instance": "/cloudwrapper/error-instances/abc",\n'
    '    "status": 500\n'
    '}'
)


def _assert_server_error(exc_info):
    """Common assertions for 500 server error tests."""
    err = exc_info.value
    assert err.status == 500
    assert err.type == "/cloudwrapper/error-types/cloudwrapper-server-error"
    assert "An unexpected error has occurred." in err.title
    assert err.detail == "Error processing request"
    assert err.instance == "/cloudwrapper/error-instances/abc"


# ===================================================================
# Configuration Tests — from configurations_test.go
# ===================================================================

class TestGetConfiguration:
    """Mirrors Go TestGetConfiguration (configurations_test.go 16-342)."""

    def test_200_ok(self, mock_session, cloudwrapper_client):
        response_body = """
{
    "configId": 1,
    "configName": "TestConfigName",
    "contractId": "TestContractID",
    "propertyIds": [
        "321",
		"654"
    ],
    "comments": "TestComments",
    "status": "ACTIVE",
    "retainIdleObjects": false,
    "locations": [
        {
            "trafficTypeId": 1,
            "comments": "TestComments",
            "capacity": {
                "value": 1,
                "unit": "GB"
            },
			"mapName": "cw-s-use"
        },
		{
            "trafficTypeId": 2,
            "comments": "TestComments",
            "capacity": {
                "value": 2,
                "unit": "TB"
            },
			"mapName": "cw-s-use"
        }
    ],
    "multiCdnSettings": {
        "origins": [
            {
                "originId": "TestOriginID",
                "hostname": "TestHostname",
						"propertyId": 321
            },
			{
                "originId": "TestOriginID2",
                "hostname": "TestHostname",
                "propertyId": 654
            }
        ],
        "cdns": [
            {
                "cdnCode": "TestCDNCode",
                "enabled": true,
                "cdnAuthKeys": [
                    {
                        "authKeyName": "TestAuthKeyName"
                    }
                ],
                "ipAclCidrs": [],
                "httpsOnly": false
            },
			{
                "cdnCode": "TestCDNCode",
                "enabled": false,
                "cdnAuthKeys": [
                    {
                        "authKeyName": "TestAuthKeyName"
                    },
					{
                        "authKeyName": "TestAuthKeyName2"
                    }
                ],
                "ipAclCidrs": [
					"test1",
					"test2"
				],
                "httpsOnly": true
            }
        ],
        "dataStreams": {
            "enabled": true,
            "dataStreamIds": [
				11,
				22
			],
			"samplingRate": 999
        },
        "bocc": {
            "enabled": false,
			"conditionalSamplingFrequency": "ONE_TENTH",
			"forwardType": "ORIGIN_AND_MIDGRESS",
			"requestType": "EDGE_ONLY",
			"samplingFrequency": "ZERO"
        },
        "enableSoftAlerts": true
    },
    "capacityAlertsThreshold": 75,
    "notificationEmails": [
        "test@akamai.com"
    ],
    "lastUpdatedDate": "2023-05-10T09:55:37.000Z",
    "lastUpdatedBy": "user",
    "lastActivatedDate": "2023-05-10T10:14:49.379Z",
    "lastActivatedBy": "user"
}"""
        parsed = json.loads(response_body)
        mock_response = make_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, parsed)

        result = cloudwrapper_client.get_configuration(
            GetConfigurationRequest(config_id=1)
        )

        assert_request_made(mock_session, "GET",
                            "/cloud-wrapper/v1/configurations/1")

        assert result.config_id == 1
        assert result.config_name == "TestConfigName"
        assert result.contract_id == "TestContractID"
        assert result.property_ids == ["321", "654"]
        assert result.comments == "TestComments"
        assert result.status == "ACTIVE"
        assert result.retain_idle_objects is False
        assert result.capacity_alerts_threshold == 75
        assert result.notification_emails == ["test@akamai.com"]
        assert result.last_updated_by == "user"
        assert result.last_updated_date == "2023-05-10T09:55:37.000Z"
        assert result.last_activated_by == "user"
        assert result.last_activated_date == "2023-05-10T10:14:49.379Z"

        assert len(result.locations) == 2
        loc0 = result.locations[0]
        assert loc0.traffic_type_id == 1
        assert loc0.comments == "TestComments"
        assert loc0.capacity.value == 1
        assert loc0.capacity.unit == "GB"
        assert loc0.map_name == "cw-s-use"

        loc1 = result.locations[1]
        assert loc1.traffic_type_id == 2
        assert loc1.capacity.value == 2
        assert loc1.capacity.unit == "TB"

        mcdn = result.multi_cdn_settings
        assert mcdn is not None
        assert mcdn.enable_soft_alerts is True

        assert mcdn.bocc.enabled is False
        assert mcdn.bocc.conditional_sampling_frequency == "ONE_TENTH"
        assert mcdn.bocc.forward_type == "ORIGIN_AND_MIDGRESS"
        assert mcdn.bocc.request_type == "EDGE_ONLY"
        assert mcdn.bocc.sampling_frequency == "ZERO"

        assert mcdn.data_streams.enabled is True
        assert mcdn.data_streams.data_stream_ids == [11, 22]
        assert mcdn.data_streams.sampling_rate == 999

        assert len(mcdn.cdns) == 2
        cdn0 = mcdn.cdns[0]
        assert cdn0.cdn_code == "TestCDNCode"
        assert cdn0.enabled is True
        assert cdn0.https_only is False
        assert cdn0.ip_acl_cidrs == []
        assert len(cdn0.cdn_auth_keys) == 1
        assert cdn0.cdn_auth_keys[0].auth_key_name == "TestAuthKeyName"

        cdn1 = mcdn.cdns[1]
        assert cdn1.enabled is False
        assert cdn1.https_only is True
        assert cdn1.ip_acl_cidrs == ["test1", "test2"]
        assert len(cdn1.cdn_auth_keys) == 2
        assert cdn1.cdn_auth_keys[1].auth_key_name == "TestAuthKeyName2"

        assert len(mcdn.origins) == 2
        assert mcdn.origins[0].origin_id == "TestOriginID"
        assert mcdn.origins[0].hostname == "TestHostname"
        assert mcdn.origins[0].property_id == 321
        assert mcdn.origins[1].origin_id == "TestOriginID2"
        assert mcdn.origins[1].property_id == 654

    def test_200_ok_minimal(self, mock_session, cloudwrapper_client):
        response_body = """
{
   "configId":1,
   "configName":"TestConfigName",
   "contractId":"TestContractID",
   "propertyIds":[
      "123"
   ],
   "comments":"TestComments",
   "status":"ACTIVE",
   "retainIdleObjects":false,
   "locations":[
      {
         "trafficTypeId":1,
         "comments":"TestComments",
         "capacity":{
            "value":1,
            "unit":"GB"
         },
		 "mapName": "cw-s-use"
      }
   ],
   "multiCdnSettings":null,
   "capacityAlertsThreshold":null,
   "notificationEmails":[],
   "lastUpdatedDate":"2023-05-10T09:55:37.000Z",
   "lastUpdatedBy":"user",
   "lastActivatedDate":null,
   "lastActivatedBy":null
}"""
        parsed = json.loads(response_body)
        mock_response = make_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, parsed)

        result = cloudwrapper_client.get_configuration(
            GetConfigurationRequest(config_id=1)
        )

        assert_request_made(mock_session, "GET",
                            "/cloud-wrapper/v1/configurations/1")

        assert result.config_id == 1
        assert result.multi_cdn_settings is None
        assert result.capacity_alerts_threshold is None
        assert result.notification_emails == []
        assert result.last_activated_by is None
        assert result.last_activated_date is None
        assert result.last_updated_by == "user"
        assert result.last_updated_date == "2023-05-10T09:55:37.000Z"

    def test_validation_error(self, cloudwrapper_client):
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.get_configuration(GetConfigurationRequest())
        assert exc_info.value.title == (
            "get configuration: struct validation:"
            " ConfigID: cannot be blank"
        )

    def test_500_error(self, mock_session, cloudwrapper_client):
        mock_session.exec.side_effect = _server_error_side_effect(
            500, _SERVER_ERROR_BODY
        )
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.get_configuration(
                GetConfigurationRequest(config_id=3)
            )
        _assert_server_error(exc_info)


class TestListConfigurations:
    """Mirrors Go TestListConfigurations (configurations_test.go 344-586)."""

    def test_200_ok(self, mock_session, cloudwrapper_client):
        response_body = """
{
   "configurations":[
      {
         "configId":1,
         "configName":"testcloudwrapper",
         "contractId":"testContract",
         "propertyIds":[
            "11"
         ],
         "comments":"testComments",
         "status":"ACTIVE",
         "retainIdleObjects":false,
         "locations":[
            {
               "trafficTypeId":1,
               "comments":"usageNotes",
               "capacity":{
                  "value":1,
                  "unit":"GB"
               },
			   "mapName": "cw-s-use"
            }
         ],
         "multiCdnSettings":null,
         "capacityAlertsThreshold":75,
         "notificationEmails":[
            "user@akamai.com"
         ],
         "lastUpdatedDate":"2023-05-10T09:55:37.000Z",
         "lastUpdatedBy":"user",
         "lastActivatedDate":"2023-05-10T10:14:49.379Z",
         "lastActivatedBy":"user"
      },
      {
         "configId":2,
         "configName":"testcloudwrappermcdn",
         "contractId":"testContract2",
         "propertyIds":[
            "22"
         ],
         "comments":"mcdn",
         "status":"ACTIVE",
         "retainIdleObjects":false,
         "locations":[
            {
               "trafficTypeId":2,
               "comments":"mcdn",
               "capacity":{
                  "value":2,
                  "unit":"TB"
               },
			   "mapName": "cw-s-use"
            }
         ],
         "multiCdnSettings":{
            "origins":[
               {
                  "originId":"testOrigin",
                  "hostname":"hostname.example.com",
                  "propertyId":222
               }
            ],
            "cdns":[
               {
                  "cdnCode":"testCode2",
                  "enabled":true,
                  "cdnAuthKeys":[
                     {
                        "authKeyName":"authKeyTest2"
                     }
                  ],
                  "ipAclCidrs":[
                     "2.2.2.2/22"
                  ],
                  "httpsOnly":true
               }
            ],
            "dataStreams":{
               "enabled":false,
               "dataStreamIds":[
                  2
               ]
            },
            "bocc":{
               "enabled":false
            },
            "enableSoftAlerts":true
         },
         "capacityAlertsThreshold":75,
         "notificationEmails":[
            "user@akamai.com"
         ],
         "lastUpdatedDate":"2023-05-10T09:55:37.000Z",
         "lastUpdatedBy":"user",
         "lastActivatedDate":"2023-05-10T10:14:49.379Z",
         "lastActivatedBy":"user"
      }
   ]
}"""
        parsed = json.loads(response_body)
        mock_response = make_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, parsed)

        result = cloudwrapper_client.list_configurations()

        assert_request_made(mock_session, "GET",
                            "/cloud-wrapper/v1/configurations")

        assert len(result.configurations) == 2
        c0 = result.configurations[0]
        assert c0.config_id == 1
        assert c0.config_name == "testcloudwrapper"
        assert c0.capacity_alerts_threshold == 75
        assert c0.last_activated_by == "user"
        assert c0.last_activated_date == "2023-05-10T10:14:49.379Z"
        assert c0.multi_cdn_settings is None

        c1 = result.configurations[1]
        assert c1.config_id == 2
        assert c1.config_name == "testcloudwrappermcdn"
        assert c1.multi_cdn_settings is not None
        assert c1.multi_cdn_settings.enable_soft_alerts is True
        assert c1.multi_cdn_settings.bocc.enabled is False
        assert c1.multi_cdn_settings.data_streams.enabled is False
        assert c1.multi_cdn_settings.data_streams.data_stream_ids == [2]
        assert len(c1.multi_cdn_settings.cdns) == 1
        assert c1.multi_cdn_settings.cdns[0].https_only is True
        assert c1.multi_cdn_settings.cdns[0].ip_acl_cidrs == ["2.2.2.2/22"]

    def test_500_error(self, mock_session, cloudwrapper_client):
        mock_session.exec.side_effect = _server_error_side_effect(
            500, _SERVER_ERROR_BODY
        )
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.list_configurations()
        _assert_server_error(exc_info)


class TestCreateConfiguration:
    """Mirrors Go TestCreateConfiguration (configurations_test.go 588-2100)."""

    def test_200_ok_minimal(self, mock_session, cloudwrapper_client):
        response_body = """
{
   "configId":111,
   "configName":"TestConfigName",
   "contractId":"TestContractID",
   "propertyIds":[
      "123"
   ],
   "comments":"TestComments",
   "status":"IN_PROGRESS",
   "retainIdleObjects":false,
   "locations":[
      {
         "trafficTypeId":1,
         "comments":"TestComments",
         "capacity":{
            "value":1,
            "unit":"GB"
         },
		 "mapName": "cw-s-use"
      }
   ],
   "multiCdnSettings":null,
   "capacityAlertsThreshold":50,
   "notificationEmails":[
      
   ],
   "lastUpdatedDate":"2022-06-10T13:21:14.488Z",
   "lastUpdatedBy":"johndoe",
   "lastActivatedDate":null,
   "lastActivatedBy":null
}"""
        parsed = json.loads(response_body)
        mock_response = make_mock_response(201, response_body)
        mock_session.exec.return_value = (mock_response, parsed)

        params = CreateConfigurationRequest(
            body=CreateConfigurationRequestBody(
                comments="TestComments",
                contract_id="TestContractID",
                locations=[
                    ConfigLocationReq(
                        comments="TestComments",
                        traffic_type_id=1,
                        capacity=Capacity(unit="GB", value=1),
                    ),
                ],
                config_name="TestConfigName",
                property_ids=["123"],
            ),
        )
        result = cloudwrapper_client.create_configuration(params)

        assert_request_made(
            mock_session, "POST",
            "/cloud-wrapper/v1/configurations?activate=false",
            body={
                "locations": [
                    {
                        "capacity": {"value": 1, "unit": "GB"},
                        "comments": "TestComments",
                        "trafficTypeId": 1,
                    }
                ],
                "propertyIds": ["123"],
                "contractId": "TestContractID",
                "comments": "TestComments",
                "configName": "TestConfigName",
            },
        )

        assert result.config_id == 111
        assert result.status == "IN_PROGRESS"
        assert result.capacity_alerts_threshold == 50
        assert result.notification_emails == []
        assert result.last_activated_by is None
        assert result.last_activated_date is None
        assert result.last_updated_by == "johndoe"

    def test_200_ok_activate(self, mock_session, cloudwrapper_client):
        response_body = """
{
   "configId":111,
   "configName":"TestConfigName",
   "contractId":"TestContractID",
   "propertyIds":[
      "123"
   ],
   "comments":"TestComments",
   "status":"IN_PROGRESS",
   "retainIdleObjects":false,
   "locations":[
      {
         "trafficTypeId":1,
         "comments":"TestComments",
         "capacity":{
            "value":1,
            "unit":"GB"
         },
		 "mapName": "cw-s-use"
      }
   ],
   "multiCdnSettings":null,
   "capacityAlertsThreshold":50,
   "notificationEmails":[
      
   ],
   "lastUpdatedDate":"2022-06-10T13:21:14.488Z",
   "lastUpdatedBy":"johndoe",
   "lastActivatedDate":null,
   "lastActivatedBy":null
}"""
        parsed = json.loads(response_body)
        mock_response = make_mock_response(201, response_body)
        mock_session.exec.return_value = (mock_response, parsed)

        params = CreateConfigurationRequest(
            activate=True,
            body=CreateConfigurationRequestBody(
                comments="TestComments",
                contract_id="TestContractID",
                locations=[
                    ConfigLocationReq(
                        comments="TestComments",
                        traffic_type_id=1,
                        capacity=Capacity(unit="GB", value=1),
                    ),
                ],
                config_name="TestConfigName",
                property_ids=["123"],
            ),
        )
        result = cloudwrapper_client.create_configuration(params)

        assert_request_made(
            mock_session, "POST",
            "/cloud-wrapper/v1/configurations?activate=true",
        )
        assert result.config_id == 111

    def test_200_ok_minimal_multicdn(self, mock_session, cloudwrapper_client):
        response_body = """
{
   "configId":111,
   "configName":"TestConfigName",
   "contractId":"TestContractID",
   "propertyIds":[
      "123"
   ],
   "comments":"TestComments",
   "status":"IN_PROGRESS",
   "retainIdleObjects":false,
   "locations":[
      {
         "trafficTypeId":1,
         "comments":"TestComments",
         "capacity":{
            "value":1,
            "unit":"GB"
         },
		 "mapName": "cw-s-use"
      }
   ],
   "multiCdnSettings":{
      "origins":[
         {
            "originId":"TestOriginID",
            "hostname":"TestHostname",
            "propertyId":123
         }
      ],
      "cdns":[
         {
            "cdnCode":"TestCDNCode",
            "enabled":true,
            "cdnAuthKeys":[
               {
                  "authKeyName":"TestAuthKeyName",
                  "headerName":"TestHeaderName",
                  "secret":"testtesttesttesttesttest",
                  "expiryDate":"TestExpiryDate"
               }
            ],
            "ipAclCidrs":[],
            "httpsOnly":false
         }
      ],
      "dataStreams":{
         "enabled":false
      },
      "bocc":{
         "enabled":false
      },
      "enableSoftAlerts":false
   },
   "capacityAlertsThreshold":null,
   "notificationEmails":[],
   "lastUpdatedDate":"2022-06-10T13:21:14.488Z",
   "lastUpdatedBy":"johndoe",
   "lastActivatedDate":null,
   "lastActivatedBy":null
}"""
        parsed = json.loads(response_body)
        mock_response = make_mock_response(201, response_body)
        mock_session.exec.return_value = (mock_response, parsed)

        params = CreateConfigurationRequest(
            body=CreateConfigurationRequestBody(
                comments="TestComments",
                contract_id="TestContractID",
                locations=[
                    ConfigLocationReq(
                        comments="TestComments",
                        traffic_type_id=1,
                        capacity=Capacity(unit="GB", value=1),
                    ),
                ],
                multi_cdn_settings=MultiCDNSettings(
                    bocc=BOCC(enabled=False),
                    cdns=[
                        CDN(
                            cdn_auth_keys=[
                                CDNAuthKey(
                                    auth_key_name="TestAuthKeyName",
                                    expiry_date="TestExpiryDate",
                                    header_name="TestHeaderName",
                                    secret="testtesttesttesttesttest",
                                ),
                            ],
                            cdn_code="TestCDNCode",
                            enabled=True,
                        ),
                    ],
                    data_streams=DataStreams(enabled=False),
                    origins=[
                        Origin(
                            hostname="TestHostname",
                            origin_id="TestOriginID",
                            property_id=123,
                        ),
                    ],
                ),
                config_name="TestConfigName",
                property_ids=["123"],
            ),
        )
        result = cloudwrapper_client.create_configuration(params)

        assert_request_made(
            mock_session, "POST",
            "/cloud-wrapper/v1/configurations?activate=false",
        )

        assert result.config_id == 111
        assert result.capacity_alerts_threshold is None
        assert result.multi_cdn_settings is not None
        assert result.multi_cdn_settings.bocc.enabled is False
        assert result.multi_cdn_settings.cdns[0].cdn_code == "TestCDNCode"
        assert result.multi_cdn_settings.cdns[0].ip_acl_cidrs == []
        assert result.multi_cdn_settings.enable_soft_alerts is False

    def test_200_ok_full_multicdn(self, mock_session, cloudwrapper_client):
        response_body = """
{
   "configId":111,
   "capacityAlertsThreshold": 70,
   "configName":"TestConfigName",
   "contractId":"TestContractID",
   "propertyIds":[
      "123"
   ],
   "comments":"TestComments",
   "status":"IN_PROGRESS",
   "retainIdleObjects":true,
   "locations":[
      {
         "trafficTypeId":1,
         "comments":"TestComments",
         "capacity":{
            "value":1,
            "unit":"GB"
         },
		 "mapName": "cw-s-use"
      },
	  {
         "trafficTypeId":2,
         "comments":"TestComments2",
         "capacity":{
            "value":2,
            "unit":"TB"
         },
		 "mapName": "cw-s-use"
      }
   ],
   "multiCdnSettings":{
      "origins":[
         {
            "originId":"TestOriginID",
            "hostname":"TestHostname",
            "propertyId":123
         },
		 {
            "originId":"TestOriginID2",
            "hostname":"TestHostname2",
            "propertyId":1234
         }
      ],
      "cdns":[
         {
            "cdnCode":"TestCDNCode",
            "enabled":true,
            "cdnAuthKeys":[
               {
                  "authKeyName":"TestAuthKeyName",
                  "headerName":"TestHeaderName",
                  "secret":"testtesttesttesttesttest",
                  "expiryDate":"TestExpiryDate"
               }
            ],
            "ipAclCidrs":[],
            "httpsOnly":true
         },
		 {
            "cdnCode":"TestCDNCode",
            "enabled":true,
            "httpsOnly":true,
			"ipAclCidrs": [
				"1.1.1.1/1"
			]
         }
      ],
      "dataStreams":{
         "enabled":true,
		 "dataStreamIds": [
			1
		 ],
		 "samplingRate": 10
      },
      "bocc":{
         "enabled":true,
		 "conditionalSamplingFrequency": "ZERO",
		 "forwardType": "ORIGIN_AND_MIDGRESS",
		 "requestType": "EDGE_AND_MIDGRESS",
		 "samplingFrequency": "ZERO"
      },
      "enableSoftAlerts": true
   },
   "notificationEmails":[
      "test@test.com"
   ],
   "lastUpdatedDate":"2022-06-10T13:21:14.488Z",
   "lastUpdatedBy":"johndoe",
   "lastActivatedDate":null,
   "lastActivatedBy":null
}"""
        parsed = json.loads(response_body)
        mock_response = make_mock_response(201, response_body)
        mock_session.exec.return_value = (mock_response, parsed)

        params = CreateConfigurationRequest(
            body=CreateConfigurationRequestBody(
                capacity_alerts_threshold=70,
                comments="TestComments",
                contract_id="TestContractID",
                locations=[
                    ConfigLocationReq(
                        comments="TestComments",
                        traffic_type_id=1,
                        capacity=Capacity(unit="GB", value=1),
                    ),
                    ConfigLocationReq(
                        comments="TestComments2",
                        traffic_type_id=2,
                        capacity=Capacity(unit="TB", value=2),
                    ),
                ],
                multi_cdn_settings=MultiCDNSettings(
                    bocc=BOCC(
                        conditional_sampling_frequency="ZERO",
                        enabled=True,
                        forward_type="ORIGIN_AND_MIDGRESS",
                        request_type="EDGE_AND_MIDGRESS",
                        sampling_frequency="ZERO",
                    ),
                    cdns=[
                        CDN(
                            cdn_auth_keys=[
                                CDNAuthKey(
                                    auth_key_name="TestAuthKeyName",
                                    expiry_date="TestExpiryDate",
                                    header_name="TestHeaderName",
                                    secret="testtesttesttesttesttest",
                                ),
                            ],
                            cdn_code="TestCDNCode",
                            enabled=True,
                            https_only=True,
                        ),
                        CDN(
                            cdn_code="TestCDNCode",
                            enabled=True,
                            https_only=True,
                            ip_acl_cidrs=["1.1.1.1/1"],
                        ),
                    ],
                    data_streams=DataStreams(
                        data_stream_ids=[1],
                        enabled=True,
                        sampling_rate=10,
                    ),
                    origins=[
                        Origin(
                            hostname="TestHostname",
                            origin_id="TestOriginID",
                            property_id=123,
                        ),
                        Origin(
                            hostname="TestHostname2",
                            origin_id="TestOriginID2",
                            property_id=1234,
                        ),
                    ],
                    enable_soft_alerts=True,
                ),
                config_name="TestConfigName",
                notification_emails=["test@test.com"],
                property_ids=["123"],
                retain_idle_objects=True,
            ),
        )
        result = cloudwrapper_client.create_configuration(params)

        assert result.config_id == 111
        assert result.capacity_alerts_threshold == 70
        assert result.retain_idle_objects is True
        assert result.notification_emails == ["test@test.com"]
        assert result.multi_cdn_settings.enable_soft_alerts is True
        assert result.multi_cdn_settings.bocc.enabled is True
        assert result.multi_cdn_settings.bocc.conditional_sampling_frequency == "ZERO"
        assert result.multi_cdn_settings.data_streams.sampling_rate == 10
        assert result.multi_cdn_settings.data_streams.data_stream_ids == [1]
        assert len(result.multi_cdn_settings.cdns) == 2
        assert len(result.multi_cdn_settings.origins) == 2
        assert len(result.locations) == 2

    def test_200_ok_bocc_defaults(self, mock_session, cloudwrapper_client):
        response_body = """
{
   "configId":111,
   "capacityAlertsThreshold":null,
   "configName":"TestConfigName",
   "contractId":"TestContractID",
   "propertyIds":[
      "123"
   ],
   "comments":"TestComments",
   "status":"IN_PROGRESS",
   "retainIdleObjects":false,
   "locations":[
      {
         "trafficTypeId":1,
         "comments":"TestComments",
         "capacity":{
            "value":10,
            "unit":"GB"
         }
      }
   ],
   "multiCdnSettings":{
      "origins":[
         {
            "originId":"TestOriginID",
            "hostname":"TestHostname",
            "propertyId":123
         }
      ],
      "cdns":[
         {
            "cdnCode":"TestCDNCode",
            "enabled":true,
            "cdnAuthKeys":[
               {
                  "authKeyName":"TestAuthKeyName"
               }
            ],
            "ipAclCidrs":[]
         }
      ],
      "dataStreams":{
         "enabled":true
      },
      "bocc":{
         "enabled":false
      },
      "enableSoftAlerts":false
   },
   "notificationEmails":[
      
   ],
   "lastUpdatedDate":"2022-06-10T13:21:14.488Z",
   "lastUpdatedBy":"johndoe",
   "lastActivatedDate":null,
   "lastActivatedBy":null
}"""
        parsed = json.loads(response_body)
        mock_response = make_mock_response(201, response_body)
        mock_session.exec.return_value = (mock_response, parsed)

        params = CreateConfigurationRequest(
            body=CreateConfigurationRequestBody(
                comments="TestComments",
                contract_id="TestContractID",
                locations=[
                    ConfigLocationReq(
                        comments="TestComments",
                        traffic_type_id=1,
                        capacity=Capacity(unit="GB", value=10),
                    ),
                ],
                multi_cdn_settings=MultiCDNSettings(
                    bocc=BOCC(),
                    cdns=[
                        CDN(
                            cdn_auth_keys=[
                                CDNAuthKey(auth_key_name="TestAuthKeyName"),
                            ],
                            cdn_code="TestCDNCode",
                            enabled=True,
                        ),
                    ],
                    data_streams=DataStreams(enabled=True),
                    origins=[
                        Origin(
                            hostname="TestHostname",
                            origin_id="TestOriginID",
                            property_id=123,
                        ),
                    ],
                ),
                config_name="TestConfigName",
                property_ids=["123"],
            ),
        )
        result = cloudwrapper_client.create_configuration(params)

        assert result.config_id == 111
        assert result.multi_cdn_settings.bocc.enabled is False

    def test_200_ok_datastreams_defaults(self, mock_session,
                                         cloudwrapper_client):
        response_body = """
{
   "configId":111,
   "capacityAlertsThreshold":null,
   "configName":"TestConfigName",
   "contractId":"TestContractID",
   "propertyIds":[
      "123"
   ],
   "comments":"TestComments",
   "status":"IN_PROGRESS",
   "retainIdleObjects":false,
   "locations":[
      {
         "trafficTypeId":1,
         "comments":"TestComments",
         "capacity":{
            "value":10,
            "unit":"GB"
         },
		 "mapName": "cw-s-use"
      }
   ],
   "multiCdnSettings":{
      "origins":[
         {
            "originId":"TestOriginID",
            "hostname":"TestHostname",
            "propertyId":123
         }
      ],
      "cdns":[
         {
            "cdnCode":"TestCDNCode",
            "enabled":true,
            "cdnAuthKeys":[
               {
                  "authKeyName":"TestAuthKeyName"
               }
            ],
            "ipAclCidrs":[]
         }
      ],
      "dataStreams":{
         "enabled":false,
		 "dataStreamsIds": []
      },
      "bocc":{
         "enabled":false
      },
      "enableSoftAlerts":false
   },
   "notificationEmails":[],
   "lastUpdatedDate":"2022-06-10T13:21:14.488Z",
   "lastUpdatedBy":"johndoe",
   "lastActivatedDate":null,
   "lastActivatedBy":null
}"""
        parsed = json.loads(response_body)
        mock_response = make_mock_response(201, response_body)
        mock_session.exec.return_value = (mock_response, parsed)

        params = CreateConfigurationRequest(
            body=CreateConfigurationRequestBody(
                comments="TestComments",
                contract_id="TestContractID",
                locations=[
                    ConfigLocationReq(
                        comments="TestComments",
                        traffic_type_id=1,
                        capacity=Capacity(unit="GB", value=10),
                    ),
                ],
                multi_cdn_settings=MultiCDNSettings(
                    bocc=BOCC(),
                    cdns=[
                        CDN(
                            cdn_auth_keys=[
                                CDNAuthKey(auth_key_name="TestAuthKeyName"),
                            ],
                            cdn_code="TestCDNCode",
                            enabled=True,
                        ),
                    ],
                    data_streams=DataStreams(),
                    origins=[
                        Origin(
                            hostname="TestHostname",
                            origin_id="TestOriginID",
                            property_id=123,
                        ),
                    ],
                ),
                config_name="TestConfigName",
                property_ids=["123"],
            ),
        )
        result = cloudwrapper_client.create_configuration(params)
        assert result.config_id == 111
        assert result.multi_cdn_settings.data_streams.enabled is False

    def test_validation_missing_all(self, cloudwrapper_client):
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.create_configuration(
                CreateConfigurationRequest()
            )
        assert exc_info.value.title == (
            "create configuration: struct validation: Body: {\n"
            "\tComments: cannot be blank\n"
            "\tConfigName: cannot be blank\n"
            "\tContractID: cannot be blank\n"
            "\tLocations: cannot be blank\n"
            "\tPropertyIDs: cannot be blank\n"
            "}"
        )

    def test_validation_location_fields(self, cloudwrapper_client):
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.create_configuration(
                CreateConfigurationRequest(
                    body=CreateConfigurationRequestBody(
                        comments="TestComments",
                        contract_id="TestContractID",
                        locations=[
                            ConfigLocationReq(
                                comments="",
                                traffic_type_id=0,
                                capacity=Capacity(),
                            ),
                        ],
                        config_name="TestConfigName",
                        property_ids=["1"],
                    ),
                )
            )
        assert exc_info.value.title == (
            "create configuration: struct validation: Body: {\n"
            "\tLocations[0]: {\n"
            "\t\tCapacity: {\n"
            "\t\t\tUnit: cannot be blank\n"
            "\t\t\tValue: cannot be blank\n"
            "\t\t}\n"
            "\t\tComments: cannot be blank\n"
            "\t\tTrafficTypeID: cannot be blank\n"
            "\t}\n"
            "}"
        )

    def test_validation_multicdn_fields(self, cloudwrapper_client):
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.create_configuration(
                CreateConfigurationRequest(
                    body=CreateConfigurationRequestBody(
                        comments="TestComments",
                        contract_id="TestContractID",
                        locations=[
                            ConfigLocationReq(
                                comments="TestComments",
                                traffic_type_id=5,
                                capacity=Capacity(unit="GB", value=10),
                            ),
                        ],
                        multi_cdn_settings=MultiCDNSettings(),
                        config_name="TestConfigName",
                        property_ids=["1"],
                    ),
                )
            )
        assert exc_info.value.title == (
            "create configuration: struct validation: Body: {\n"
            "\tMultiCDNSettings: {\n"
            "\t\tBOCC: cannot be blank\n"
            "\t\tCDNs: cannot be blank\n"
            "\t\tDataStreams: cannot be blank\n"
            "\t\tOrigins: cannot be blank\n"
            "\t}\n"
            "}"
        )

    def test_validation_bocc_enabled(self, cloudwrapper_client):
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.create_configuration(
                CreateConfigurationRequest(
                    body=CreateConfigurationRequestBody(
                        comments="TestComments",
                        contract_id="TestContractID",
                        locations=[
                            ConfigLocationReq(
                                comments="TestComments",
                                traffic_type_id=5,
                                capacity=Capacity(unit="GB", value=10),
                            ),
                        ],
                        multi_cdn_settings=MultiCDNSettings(
                            bocc=BOCC(enabled=True),
                            cdns=[
                                CDN(
                                    cdn_auth_keys=[
                                        CDNAuthKey(
                                            auth_key_name="TestAuthKeyName"
                                        ),
                                    ],
                                    cdn_code="TestCDNCode",
                                    enabled=True,
                                ),
                            ],
                            data_streams=DataStreams(enabled=True),
                            origins=[
                                Origin(
                                    hostname="TestHostname",
                                    origin_id="TestOriginID",
                                    property_id=1,
                                ),
                            ],
                        ),
                        config_name="TestConfigName",
                        property_ids=["1"],
                    ),
                )
            )
        assert exc_info.value.title == (
            "create configuration: struct validation: Body: {\n"
            "\tMultiCDNSettings: {\n"
            "\t\tBOCC: {\n"
            "\t\t\tConditionalSamplingFrequency: cannot be blank\n"
            "\t\t\tForwardType: cannot be blank\n"
            "\t\t\tRequestType: cannot be blank\n"
            "\t\t\tSamplingFrequency: cannot be blank\n"
            "\t\t}\n"
            "\t}\n"
            "}"
        )

    def test_validation_origin_fields(self, cloudwrapper_client):
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.create_configuration(
                CreateConfigurationRequest(
                    body=CreateConfigurationRequestBody(
                        comments="TestComments",
                        contract_id="TestContractID",
                        locations=[
                            ConfigLocationReq(
                                comments="TestComments",
                                traffic_type_id=5,
                                capacity=Capacity(unit="GB", value=10),
                            ),
                        ],
                        multi_cdn_settings=MultiCDNSettings(
                            bocc=BOCC(enabled=False),
                            cdns=[
                                CDN(
                                    cdn_code="TestCDNCode",
                                    enabled=True,
                                    ip_acl_cidrs=["1.1.1.1/1"],
                                ),
                            ],
                            data_streams=DataStreams(enabled=True),
                            origins=[Origin()],
                        ),
                        config_name="TestConfigName",
                        property_ids=["1"],
                    ),
                )
            )
        assert exc_info.value.title == (
            "create configuration: struct validation: Body: {\n"
            "\tMultiCDNSettings: {\n"
            "\t\tOrigins[0]: {\n"
            "\t\t\tHostname: cannot be blank\n"
            "\t\t\tOriginID: cannot be blank\n"
            "\t\t\tPropertyID: cannot be blank\n"
            "\t\t}\n"
            "\t}\n"
            "}"
        )

    def test_validation_cdn_enabled(self, cloudwrapper_client):
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.create_configuration(
                CreateConfigurationRequest(
                    body=CreateConfigurationRequestBody(
                        comments="TestComments",
                        contract_id="TestContractID",
                        locations=[
                            ConfigLocationReq(
                                comments="TestComments",
                                traffic_type_id=5,
                                capacity=Capacity(unit="GB", value=10),
                            ),
                        ],
                        multi_cdn_settings=MultiCDNSettings(
                            bocc=BOCC(enabled=False),
                            cdns=[
                                CDN(
                                    cdn_code="TestCDNCode",
                                    enabled=False,
                                    ip_acl_cidrs=["1.1.1.1/1"],
                                ),
                                CDN(
                                    cdn_code="TestCDNCode",
                                    enabled=False,
                                    ip_acl_cidrs=["1.1.1.1/1"],
                                ),
                            ],
                            data_streams=DataStreams(enabled=False),
                            origins=[
                                Origin(
                                    hostname="TestHostname",
                                    origin_id="TestOriginID",
                                    property_id=1,
                                ),
                            ],
                        ),
                        config_name="TestConfigName",
                        property_ids=["1"],
                    ),
                )
            )
        assert exc_info.value.title == (
            "create configuration: struct validation: Body: {\n"
            "\tMultiCDNSettings: {\n"
            "\t\tCDNs: at least one of CDNs must be enabled\n"
            "\t}\n"
            "}"
        )

    def test_validation_cdn_auth(self, cloudwrapper_client):
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.create_configuration(
                CreateConfigurationRequest(
                    body=CreateConfigurationRequestBody(
                        comments="TestComments",
                        contract_id="TestContractID",
                        locations=[
                            ConfigLocationReq(
                                comments="TestComments",
                                traffic_type_id=5,
                                capacity=Capacity(unit="GB", value=10),
                            ),
                        ],
                        multi_cdn_settings=MultiCDNSettings(
                            bocc=BOCC(enabled=False),
                            cdns=[
                                CDN(
                                    cdn_code="TestCDNCode",
                                    enabled=False,
                                ),
                            ],
                            data_streams=DataStreams(enabled=False),
                            origins=[
                                Origin(
                                    hostname="TestHostname",
                                    origin_id="TestOriginID",
                                    property_id=1,
                                ),
                            ],
                        ),
                        config_name="TestConfigName",
                        property_ids=["1"],
                    ),
                )
            )
        assert exc_info.value.title == (
            "create configuration: struct validation: Body: {\n"
            "\tMultiCDNSettings: {\n"
            "\t\tCDNs: at least one authentication method is required"
            " for CDN. Either IP ACL or header authentication"
            " must be enabled\n"
            "\t}\n"
            "}"
        )

    def test_validation_struct_fields(self, cloudwrapper_client):
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.create_configuration(
                CreateConfigurationRequest(
                    body=CreateConfigurationRequestBody(
                        capacity_alerts_threshold=20,
                        comments="TestComments",
                        contract_id="TestContractID",
                        locations=[
                            ConfigLocationReq(
                                comments="TestComments",
                                traffic_type_id=5,
                                capacity=Capacity(unit="MB", value=10),
                            ),
                        ],
                        multi_cdn_settings=MultiCDNSettings(
                            bocc=BOCC(
                                conditional_sampling_frequency="a",
                                enabled=False,
                                forward_type="a",
                                request_type="a",
                                sampling_frequency="a",
                            ),
                            cdns=[
                                CDN(
                                    cdn_code="TestCDNCode",
                                    enabled=True,
                                    ip_acl_cidrs=["1.1.1.1/1"],
                                ),
                                CDN(
                                    cdn_auth_keys=[CDNAuthKey()],
                                    cdn_code="TestCDNCode",
                                    enabled=True,
                                ),
                            ],
                            data_streams=DataStreams(
                                data_stream_ids=[1],
                                enabled=True,
                                sampling_rate=-10,
                            ),
                            origins=[
                                Origin(
                                    hostname="TestHostname",
                                    origin_id="TestOriginID",
                                    property_id=1,
                                ),
                            ],
                        ),
                        config_name="TestConfigName",
                        property_ids=["1"],
                    ),
                )
            )
        assert exc_info.value.title == (
            "create configuration: struct validation: Body: {\n"
            "\tCapacityAlertsThreshold: must be no less than 50\n"
            "\tLocations[0]: {\n"
            "\t\tCapacity: {\n"
            "\t\t\tUnit: value 'MB' is invalid. Must be one of: 'GB', 'TB'\n"
            "\t\t}\n"
            "\t}\n"
            "\tMultiCDNSettings: {\n"
            "\t\tBOCC: {\n"
            "\t\t\tConditionalSamplingFrequency: value 'a' is invalid."
            " Must be one of: 'ZERO', 'ONE_TENTH'\n"
            "\t\t\tForwardType: value 'a' is invalid."
            " Must be one of: 'ORIGIN_ONLY', 'MIDGRESS_ONLY',"
            " 'ORIGIN_AND_MIDGRESS'\n"
            "\t\t\tRequestType: value 'a' is invalid."
            " Must be one of: 'EDGE_ONLY', 'EDGE_AND_MIDGRESS'\n"
            "\t\t\tSamplingFrequency: value 'a' is invalid."
            " Must be one of: 'ZERO', 'ONE_TENTH'\n"
            "\t\t}\n"
            "\t\tCDNs[1]: {\n"
            "\t\t\tCDNAuthKeys[0]: {\n"
            "\t\t\t\tAuthKeyName: cannot be blank\n"
            "\t\t\t}\n"
            "\t\t}\n"
            "\t\tDataStreams: {\n"
            "\t\t\tSamplingRate: must be no less than 1\n"
            "\t\t}\n"
            "\t}\n"
            "}"
        )

    def test_500_error(self, mock_session, cloudwrapper_client):
        mock_session.exec.side_effect = _server_error_side_effect(
            500, _SERVER_ERROR_BODY
        )
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.create_configuration(
                CreateConfigurationRequest(
                    body=CreateConfigurationRequestBody(
                        comments="TestComments",
                        contract_id="TestContractID",
                        locations=[
                            ConfigLocationReq(
                                comments="TestComments",
                                traffic_type_id=1,
                                capacity=Capacity(unit="GB", value=1),
                            ),
                        ],
                        config_name="TestConfigName",
                        property_ids=["123"],
                    ),
                )
            )
        _assert_server_error(exc_info)


class TestUpdateConfiguration:
    """Mirrors Go TestUpdateConfiguration (configurations_test.go 2102-2743)."""

    def test_200_ok_minimal(self, mock_session, cloudwrapper_client):
        response_body = """
{
   "configId":111,
   "configName":"TestConfigName",
   "contractId":"TestContractID",
   "propertyIds":[
      "123"
   ],
   "comments":"TestCommentsUpdated",
   "status":"IN_PROGRESS",
   "retainIdleObjects":false,
   "locations":[
      {
         "trafficTypeId":1,
         "comments":"TestCommentsUpdated",
         "capacity":{
            "value":1,
            "unit":"GB"
         },
		 "mapName": "cw-s-use"
      }
   ],
   "multiCdnSettings":null,
   "capacityAlertsThreshold":50,
   "notificationEmails":[
      
   ],
   "lastUpdatedDate":"2022-06-10T13:21:14.488Z",
   "lastUpdatedBy":"johndoe",
   "lastActivatedDate":null,
   "lastActivatedBy":null
}"""
        parsed = json.loads(response_body)
        mock_response = make_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, parsed)

        params = UpdateConfigurationRequest(
            config_id=111,
            body=UpdateConfigurationRequestBody(
                comments="TestCommentsUpdated",
                locations=[
                    ConfigLocationReq(
                        comments="TestCommentsUpdated",
                        traffic_type_id=1,
                        capacity=Capacity(unit="GB", value=1),
                    ),
                ],
                property_ids=["123"],
            ),
        )
        result = cloudwrapper_client.update_configuration(params)

        assert_request_made(
            mock_session, "PUT",
            "/cloud-wrapper/v1/configurations/111?activate=false",
        )

        assert result.config_id == 111
        assert result.comments == "TestCommentsUpdated"
        assert result.capacity_alerts_threshold == 50
        assert result.status == "IN_PROGRESS"

    def test_200_ok_multicdn(self, mock_session, cloudwrapper_client):
        response_body = """
{
   "configId":111,
   "configName":"TestConfigName",
   "contractId":"TestContractID",
   "propertyIds":[
      "123"
   ],
   "comments":"TestCommentsUpdated",
   "status":"IN_PROGRESS",
   "retainIdleObjects":false,
   "locations":[
      {
         "trafficTypeId":1,
         "comments":"TestCommentsUpdated",
         "capacity":{
            "value":1,
            "unit":"GB"
         },
		 "mapName": "cw-s-use"
      }
   ],
   "multiCdnSettings":{
      "origins":[
         {
            "originId":"TestOriginID",
            "hostname":"TestHostname",
            "propertyId":123
         }
      ],
      "cdns":[
         {
            "cdnCode":"TestCDNCode",
            "enabled":true,
            "cdnAuthKeys":[],
            "ipAclCidrs":[
               "1.1.1.1/1"
            ],
            "httpsOnly":false
         }
      ],
      "dataStreams":{
         "enabled":false
      },
      "bocc":{
         "enabled":false
      },
      "enableSoftAlerts":false
   },
   "capacityAlertsThreshold":null,
   "notificationEmails":[],
   "lastUpdatedDate":"2022-06-10T13:21:14.488Z",
   "lastUpdatedBy":"johndoe",
   "lastActivatedDate":null,
   "lastActivatedBy":null
}"""
        parsed = json.loads(response_body)
        mock_response = make_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, parsed)

        params = UpdateConfigurationRequest(
            config_id=111,
            body=UpdateConfigurationRequestBody(
                comments="TestCommentsUpdated",
                locations=[
                    ConfigLocationReq(
                        comments="TestCommentsUpdated",
                        traffic_type_id=1,
                        capacity=Capacity(unit="GB", value=1),
                    ),
                ],
                property_ids=["123"],
                multi_cdn_settings=MultiCDNSettings(
                    bocc=BOCC(enabled=False),
                    cdns=[
                        CDN(
                            cdn_code="TestCDNCode",
                            enabled=True,
                            ip_acl_cidrs=["1.1.1.1/1"],
                        ),
                    ],
                    data_streams=DataStreams(enabled=False),
                    origins=[
                        Origin(
                            hostname="TestHostname",
                            origin_id="TestOriginID",
                            property_id=123,
                        ),
                    ],
                ),
            ),
        )
        result = cloudwrapper_client.update_configuration(params)

        assert_request_made(
            mock_session, "PUT",
            "/cloud-wrapper/v1/configurations/111?activate=false",
        )

        assert result.multi_cdn_settings is not None
        assert result.multi_cdn_settings.cdns[0].ip_acl_cidrs == ["1.1.1.1/1"]
        assert result.multi_cdn_settings.cdns[0].cdn_auth_keys == []

    def test_200_ok_all_fields(self, mock_session, cloudwrapper_client):
        response_body = """
{
   "configId":111,
   "configName":"TestConfigName",
   "contractId":"TestContractID",
   "propertyIds":[
      "123"
   ],
   "comments":"TestCommentsUpdated",
   "status":"IN_PROGRESS",
   "retainIdleObjects":true,
   "locations":[
      {
         "trafficTypeId":1,
         "comments":"TestCommentsUpdated",
         "capacity":{
            "value":1,
            "unit":"GB"
         },
		 "mapName": "cw-s-use"
      }
   ],
   "multiCdnSettings":{
      "origins":[
         {
            "originId":"TestOriginID",
            "hostname":"TestHostname",
            "propertyId":123
         }
      ],
      "cdns":[
         {
            "cdnCode":"TestCDNCode",
            "enabled":true,
            "cdnAuthKeys":[
               {
                  "authKeyName":"TestAuthKeyName",
                  "expiryDate":"TestExpiryDate",
                  "headerName":"TestHeaderName",
                  "secret":"TestSecretTestSecret1234"
               }
            ],
            "ipAclCidrs":[
               "1.1.1.1/1"
            ],
            "httpsOnly":true
         }
      ],
      "dataStreams":{
         "enabled":true,
         "dataStreamIds":[
            1
         ],
         "samplingRate":10
      },
      "bocc":{
         "enabled":true,
         "conditionalSamplingFrequency":"ZERO",
         "forwardType":"ORIGIN_AND_MIDGRESS",
         "requestType":"EDGE_AND_MIDGRESS",
         "samplingFrequency":"ZERO"
      },
      "enableSoftAlerts":true
   },
   "capacityAlertsThreshold":80,
   "notificationEmails":[
      "test@test.com"
   ],
   "lastUpdatedDate":"2022-06-10T13:21:14.488Z",
   "lastUpdatedBy":"johndoe",
   "lastActivatedDate":null,
   "lastActivatedBy":null
}"""
        parsed = json.loads(response_body)
        mock_response = make_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, parsed)

        params = UpdateConfigurationRequest(
            config_id=111,
            body=UpdateConfigurationRequestBody(
                capacity_alerts_threshold=80,
                comments="TestCommentsUpdated",
                locations=[
                    ConfigLocationReq(
                        comments="TestCommentsUpdated",
                        traffic_type_id=1,
                        capacity=Capacity(unit="GB", value=1),
                    ),
                ],
                multi_cdn_settings=MultiCDNSettings(
                    bocc=BOCC(
                        conditional_sampling_frequency="ZERO",
                        enabled=True,
                        forward_type="ORIGIN_AND_MIDGRESS",
                        request_type="EDGE_AND_MIDGRESS",
                        sampling_frequency="ZERO",
                    ),
                    cdns=[
                        CDN(
                            cdn_auth_keys=[
                                CDNAuthKey(
                                    auth_key_name="TestAuthKeyName",
                                    expiry_date="TestExpiryDate",
                                    header_name="TestHeaderName",
                                    secret="TestSecretTestSecret1234",
                                ),
                            ],
                            cdn_code="TestCDNCode",
                            enabled=True,
                            ip_acl_cidrs=["1.1.1.1/1"],
                            https_only=True,
                        ),
                    ],
                    data_streams=DataStreams(
                        data_stream_ids=[1],
                        enabled=True,
                        sampling_rate=10,
                    ),
                    origins=[
                        Origin(
                            hostname="TestHostname",
                            origin_id="TestOriginID",
                            property_id=123,
                        ),
                    ],
                ),
                notification_emails=["test@test.com"],
                property_ids=["123"],
                retain_idle_objects=True,
            ),
        )
        result = cloudwrapper_client.update_configuration(params)

        assert result.capacity_alerts_threshold == 80
        assert result.retain_idle_objects is True
        assert result.multi_cdn_settings.enable_soft_alerts is True
        assert result.multi_cdn_settings.bocc.enabled is True

    def test_validation_error(self, cloudwrapper_client):
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.update_configuration(
                UpdateConfigurationRequest()
            )
        assert exc_info.value.title == (
            "update configuration: struct validation: Body: {\n"
            "\tComments: cannot be blank\n"
            "\tLocations: cannot be blank\n"
            "\tPropertyIDs: cannot be blank\n"
            "}\n"
            "ConfigID: cannot be blank"
        )

    def test_500_error(self, mock_session, cloudwrapper_client):
        mock_session.exec.side_effect = _server_error_side_effect(
            500, _SERVER_ERROR_BODY
        )
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.update_configuration(
                UpdateConfigurationRequest(
                    config_id=1,
                    body=UpdateConfigurationRequestBody(
                        comments="TestCommentsUpdated",
                        locations=[
                            ConfigLocationReq(
                                comments="TestCommentsUpdated",
                                traffic_type_id=1,
                                capacity=Capacity(unit="GB", value=1),
                            ),
                        ],
                        property_ids=["1"],
                    ),
                )
            )
        _assert_server_error(exc_info)


class TestDeleteConfiguration:
    """Mirrors Go TestDeleteConfiguration (configurations_test.go 2745-2812)."""

    def test_202_accepted(self, mock_session, cloudwrapper_client):
        mock_response = make_mock_response(202)
        mock_session.exec.return_value = (mock_response, None)

        cloudwrapper_client.delete_configuration(
            DeleteConfigurationRequest(config_id=1)
        )

        assert_request_made(
            mock_session, "DELETE",
            "/cloud-wrapper/v1/configurations/1",
        )

    def test_validation_error(self, cloudwrapper_client):
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.delete_configuration(
                DeleteConfigurationRequest()
            )
        assert exc_info.value.title == (
            "delete configuration: struct validation:"
            " ConfigID: cannot be blank"
        )

    def test_500_error(self, mock_session, cloudwrapper_client):
        mock_session.exec.side_effect = _server_error_side_effect(
            500, _SERVER_ERROR_BODY
        )
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.delete_configuration(
                DeleteConfigurationRequest(config_id=1)
            )
        _assert_server_error(exc_info)


class TestActivateConfiguration:
    """Mirrors Go TestActivateConfiguration (configurations_test.go 2813-2906)."""

    def test_204_single(self, mock_session, cloudwrapper_client):
        mock_response = make_mock_response(204)
        mock_session.exec.return_value = (mock_response, None)

        cloudwrapper_client.activate_configuration(
            ActivateConfigurationRequest(configuration_ids=[1])
        )

        assert_request_made(
            mock_session, "POST",
            "/cloud-wrapper/v1/configurations/activate",
            body={"configurationIds": [1]},
        )

    def test_204_multiple(self, mock_session, cloudwrapper_client):
        mock_response = make_mock_response(204)
        mock_session.exec.return_value = (mock_response, None)

        cloudwrapper_client.activate_configuration(
            ActivateConfigurationRequest(configuration_ids=[1, 2, 3])
        )

        assert_request_made(
            mock_session, "POST",
            "/cloud-wrapper/v1/configurations/activate",
            body={"configurationIds": [1, 2, 3]},
        )

    def test_validation_error(self, cloudwrapper_client):
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.activate_configuration(
                ActivateConfigurationRequest()
            )
        assert exc_info.value.title == (
            "activate configuration: struct validation:"
            " ConfigurationIDs: cannot be blank"
        )

    def test_500_error(self, mock_session, cloudwrapper_client):
        mock_session.exec.side_effect = _server_error_side_effect(
            500, _SERVER_ERROR_BODY
        )
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.activate_configuration(
                ActivateConfigurationRequest(configuration_ids=[1])
            )
        _assert_server_error(exc_info)


# ===================================================================
# Properties Tests — from properties_test.go
# ===================================================================

class TestListProperties:
    """Mirrors Go TestListProperties (properties_test.go 14-193)."""

    def test_200_ok_multiple(self, mock_session, cloudwrapper_client):
        response_body = """
{
   "properties":[
      {
         "propertyId":1,
         "propertyName":"TestPropertyName1",
         "contractId":"TestContractID1",
         "groupId":11,
         "type":"MEDIA"
      },
      {
         "propertyId":2,
         "propertyName":"TestPropertyName2",
         "contractId":"TestContractID2",
         "groupId":22,
         "type":"WEB"
      },
      {
         "propertyId":3,
         "propertyName":"TestPropertyName3",
         "contractId":"TestContractID3",
         "groupId":33,
         "type":"WEB"
      }
   ]
}"""
        parsed = json.loads(response_body)
        mock_response = make_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, parsed)

        result = cloudwrapper_client.list_properties(ListPropertiesRequest())

        assert_request_made(
            mock_session, "GET",
            "/cloud-wrapper/v1/properties?unused=false",
        )

        assert len(result.properties) == 3
        assert result.properties[0].property_id == 1
        assert result.properties[0].type == "MEDIA"
        assert result.properties[0].group_id == 11
        assert result.properties[1].type == "WEB"
        assert result.properties[2].property_name == "TestPropertyName3"

    def test_200_ok_single(self, mock_session, cloudwrapper_client):
        response_body = """
{
   "properties":[
      {
         "propertyId":1,
         "propertyName":"TestPropertyName1",
         "contractId":"TestContractID1",
         "groupId":11,
         "type":"MEDIA"
      }
   ]
}"""
        parsed = json.loads(response_body)
        mock_response = make_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, parsed)

        result = cloudwrapper_client.list_properties(ListPropertiesRequest())

        assert len(result.properties) == 1
        assert result.properties[0].property_id == 1

    def test_200_ok_query_params(self, mock_session, cloudwrapper_client):
        response_body = """
{
   "properties":[
      {
         "propertyId":1,
         "propertyName":"TestPropertyName1",
         "contractId":"TestContractID1",
         "groupId":11,
         "type":"MEDIA"
      },
      {
         "propertyId":2,
         "propertyName":"TestPropertyName2",
         "contractId":"TestContractID2",
         "groupId":22,
         "type":"MEDIA"
      }
   ]
}"""
        parsed = json.loads(response_body)
        mock_response = make_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, parsed)

        result = cloudwrapper_client.list_properties(
            ListPropertiesRequest(
                unused=True,
                contract_ids=["TestContractID1", "TestContractID2"],
            )
        )

        assert_request_made(
            mock_session, "GET",
            "/cloud-wrapper/v1/properties"
            "?contractIds=TestContractID1"
            "&contractIds=TestContractID2"
            "&unused=true",
        )
        assert len(result.properties) == 2

    def test_500_error(self, mock_session, cloudwrapper_client):
        mock_session.exec.side_effect = _server_error_side_effect(
            500, _SERVER_ERROR_BODY
        )
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.list_properties(ListPropertiesRequest())
        _assert_server_error(exc_info)


class TestListOrigins:
    """Mirrors Go TestListOrigins (properties_test.go 195-384)."""

    def test_200_ok_multiple(self, mock_session, cloudwrapper_client):
        response_body = """
{
   "default":[
      {
         "originType":"CUSTOMER",
         "hostname":"origin-www.example.com"
      },
      {
         "originType":"NET_STORAGE",
         "hostname":"origin-www.example2.com"
      }
   ],
   "children":[
      {
         "name":"Default CORS Policy",
         "behaviors":[
            {
               "originType":"NET_STORAGE",
               "hostname":"origin-www.example3.com"
            }
         ]
      },
      {
         "name":"Cloud Wrapper",
         "behaviors":[
            {
               "originType":"CUSTOMER",
               "hostname":"origin-www.example4.com"
            },
            {
               "originType":"CUSTOMER",
               "hostname":"origin-www.example5.com"
            }
         ]
      }
   ]
}"""
        parsed = json.loads(response_body)
        mock_response = make_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, parsed)

        result = cloudwrapper_client.list_origins(
            ListOriginsRequest(
                property_id=1,
                contract_id="TestContractID",
                group_id=11,
            )
        )

        assert_request_made(
            mock_session, "GET",
            "/cloud-wrapper/v1/properties/1/origins"
            "?contractId=TestContractID&groupId=11",
        )

        assert len(result.default) == 2
        assert result.default[0].origin_type == "CUSTOMER"
        assert result.default[0].hostname == "origin-www.example.com"
        assert result.default[1].origin_type == "NET_STORAGE"

        assert len(result.children) == 2
        assert result.children[0].name == "Default CORS Policy"
        assert len(result.children[0].behaviors) == 1
        assert result.children[0].behaviors[0].origin_type == "NET_STORAGE"
        assert result.children[1].name == "Cloud Wrapper"
        assert len(result.children[1].behaviors) == 2

    def test_200_ok_empty_behaviors(self, mock_session,
                                     cloudwrapper_client):
        response_body = """
{
   "default":[
      {
         "originType":"CUSTOMER",
         "hostname":"test.com"
      }
   ],
   "children":[
      {
         "name":"Default CORS Policy",
         "behaviors":[
            
         ]
      }
   ]
}"""
        parsed = json.loads(response_body)
        mock_response = make_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, parsed)

        result = cloudwrapper_client.list_origins(
            ListOriginsRequest(
                property_id=1,
                contract_id="TestContractID",
                group_id=11,
            )
        )

        assert result.children[0].name == "Default CORS Policy"
        assert result.children[0].behaviors == []
        assert result.default[0].hostname == "test.com"

    def test_validation_error(self, cloudwrapper_client):
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.list_origins(
                ListOriginsRequest(
                    property_id=0,
                    contract_id="",
                    group_id=0,
                )
            )
        assert exc_info.value.title == (
            "list origins: struct validation:"
            " ContractID: cannot be blank\n"
            "GroupID: cannot be blank\n"
            "PropertyID: cannot be blank"
        )

    def test_500_error(self, mock_session, cloudwrapper_client):
        mock_session.exec.side_effect = _server_error_side_effect(
            500, _SERVER_ERROR_BODY
        )
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.list_origins(
                ListOriginsRequest(
                    property_id=1,
                    contract_id="TestContractID",
                    group_id=11,
                )
            )
        _assert_server_error(exc_info)


# ===================================================================
# Capacity Tests — from capacity_test.go
# ===================================================================

class TestListCapacities:
    """Mirrors Go TestListCapacity (capacity_test.go 14-212)."""

    def test_200_ok(self, mock_session, cloudwrapper_client):
        response_body = """
{
    "capacities": [
        {
            "locationId": 1,
            "locationName": "US East",
            "contractId": "A-BCDEFG",
            "type": "MEDIA",
            "approvedCapacity": {
                "value": 2000,
                "unit": "GB"
            },
            "assignedCapacity": {
                "value": 2,
                "unit": "GB"
            },
            "unassignedCapacity": {
                "value": 1998,
                "unit": "GB"
            }
        }
    ]
}"""
        parsed = json.loads(response_body)
        mock_response = make_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, parsed)

        result = cloudwrapper_client.list_capacities(
            ListCapacitiesRequest()
        )

        assert_request_made(
            mock_session, "GET", "/cloud-wrapper/v1/capacity"
        )

        assert len(result.capacities) == 1
        cap = result.capacities[0]
        assert cap.location_id == 1
        assert cap.location_name == "US East"
        assert cap.contract_id == "A-BCDEFG"
        assert cap.type == "MEDIA"
        assert cap.approved_capacity.value == 2000
        assert cap.approved_capacity.unit == "GB"
        assert cap.assigned_capacity.value == 2
        assert cap.unassigned_capacity.value == 1998

    def test_200_ok_with_contracts(self, mock_session, cloudwrapper_client):
        response_body = """
{
    "capacities": [
        {
            "locationId": 1,
            "locationName": "US East",
            "contractId": "A-BCDEFG",
            "type": "WEB_ENHANCED_TLS",
            "approvedCapacity": {
                "value": 10,
                "unit": "TB"
            },
            "assignedCapacity": {
                "value": 1,
                "unit": "TB"
            },
            "unassignedCapacity": {
                "value": 9,
                "unit": "TB"
            }
        }
    ]
}"""
        parsed = json.loads(response_body)
        mock_response = make_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, parsed)

        result = cloudwrapper_client.list_capacities(
            ListCapacitiesRequest(contract_ids=["A-BCDEF", "B-CDEFG"])
        )

        assert_request_made(
            mock_session, "GET",
            "/cloud-wrapper/v1/capacity"
            "?contractIds=A-BCDEF&contractIds=B-CDEFG",
        )

        cap = result.capacities[0]
        assert cap.type == "WEB_ENHANCED_TLS"
        assert cap.approved_capacity.unit == "TB"
        assert cap.approved_capacity.value == 10

    def test_401_not_authorized(self, mock_session, cloudwrapper_client):
        body = (
            '{\n'
            '    "type": "https://problems.luna-dev.akamaiapis.net'
            '/-/pep-authn/deny",\n'
            '    "title": "Not authorized",\n'
            '    "status": 401,\n'
            '    "detail": "The signature does not match",\n'
            '    "instance": "https://instance.luna-dev.akamaiapis.net'
            '/cloud-wrapper/v1/capacity",\n'
            '    "method": "GET",\n'
            '    "serverIp": "2.2.2.2",\n'
            '    "clientIp": "3.3.3.3",\n'
            '    "requestId": "a7a7a7a7a7a",\n'
            '    "requestTime": "2023-05-22T10:05:22Z"\n'
            '}'
        )
        mock_session.exec.side_effect = _server_error_side_effect(401, body)

        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.list_capacities(ListCapacitiesRequest())

        err = exc_info.value
        assert err.status == 401
        assert "Not authorized" in err.title

    def test_500_error(self, mock_session, cloudwrapper_client):
        body = (
            '{\n'
            '    "type": "https://problems.luna-dev.akamaiapis.net'
            '/-/resource-impl/forward-origin-error",\n'
            '    "title": "Server Error",\n'
            '    "status": 500,\n'
            '    "instance": "https://instance.luna-dev.akamaiapis.net'
            '/cloud-wrapper/v1/capacity",\n'
            '    "method": "GET",\n'
            '    "serverIp": "2.2.2.2",\n'
            '    "clientIp": "3.3.3.3",\n'
            '    "requestId": "a7a7a7a7a7a",\n'
            '    "requestTime": "2021-12-06T10:27:11Z"\n'
            '}'
        )
        mock_session.exec.side_effect = _server_error_side_effect(500, body)

        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.list_capacities(ListCapacitiesRequest())

        err = exc_info.value
        assert err.status == 500
        assert "Server Error" in err.title


# ===================================================================
# Locations Tests — from locations_test.go
# ===================================================================

class TestListLocations:
    """Mirrors Go TestCloudwrapper_ListLocations (locations_test.go 13-140)."""

    def test_200_ok(self, mock_session, cloudwrapper_client):
        response_body = """{
    "locations": [
        {
            "locationId": 1,
            "locationName": "US East",
            "trafficTypes": [
                {
                    "trafficTypeId": 1,
                    "trafficType": "TEST_TT1",
                    "mapName": "cw-essl-use"
                },
                {
                    "trafficTypeId": 2,
                    "trafficType": "TEST_TT2",
                    "mapName": "cw-s-use-live"
                }
            ],
            "multiCdnLocationId": "0123"
        },
        {
            "locationId": 2,
            "locationName": "US West",
            "trafficTypes": [
                {
                    "trafficTypeId": 3,
                    "trafficType": "TEST_TT1",
                    "mapName": "cw-essl-use"
                },
                {
                    "trafficTypeId": 4,
                    "trafficType": "TEST_TT2",
                    "mapName": "cw-s-use-live"
                }
            ],
            "multiCdnLocationId": "4567"
        }
	]}"""
        parsed = json.loads(response_body)
        mock_response = make_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, parsed)

        result = cloudwrapper_client.list_locations()

        assert_request_made(
            mock_session, "GET", "/cloud-wrapper/v1/locations"
        )

        assert len(result.locations) == 2

        loc0 = result.locations[0]
        assert loc0.location_id == 1
        assert loc0.location_name == "US East"
        assert loc0.multi_cdn_location_id == "0123"
        assert len(loc0.traffic_types) == 2
        assert loc0.traffic_types[0].traffic_type_id == 1
        assert loc0.traffic_types[0].traffic_type == "TEST_TT1"
        assert loc0.traffic_types[0].map_name == "cw-essl-use"
        assert loc0.traffic_types[1].traffic_type_id == 2

        loc1 = result.locations[1]
        assert loc1.location_id == 2
        assert loc1.location_name == "US West"
        assert loc1.multi_cdn_location_id == "4567"
        assert loc1.traffic_types[0].traffic_type_id == 3
        assert loc1.traffic_types[1].traffic_type_id == 4

    def test_500_error(self, mock_session, cloudwrapper_client):
        body = (
            '{\n'
            '    "type": "internal_error",\n'
            '    "title": "Internal Server Error",\n'
            '    "detail": "Error processing request",\n'
            '    "status": 500\n'
            '}'
        )
        mock_session.exec.side_effect = _server_error_side_effect(500, body)

        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.list_locations()

        err = exc_info.value
        assert err.status == 500
        assert "Internal Server Error" in err.title


# ===================================================================
# Multi-CDN Tests — from multi_cdn_test.go
# ===================================================================

class TestListAuthKeys:
    """Mirrors Go TestCloudwrapper_ListAuthKeys (multi_cdn_test.go 13-103)."""

    def test_200_ok(self, mock_session, cloudwrapper_client):
        response_body = """{
    "cdnAuthKeys": [
        {
            "authKeyName": "test7",
            "expiryDate": "2023-08-08",
            "headerName": "key"
        }
    ]
}"""
        parsed = json.loads(response_body)
        mock_response = make_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, parsed)

        result = cloudwrapper_client.list_auth_keys(
            ListAuthKeysRequest(
                contract_id="test_contract",
                cdn_code="dn123",
            )
        )

        assert_request_made(
            mock_session, "GET",
            "/cloud-wrapper/v1/multi-cdn/auth-keys"
            "?cdnCode=dn123&contractId=test_contract",
        )

        assert len(result.cdn_auth_keys) == 1
        key0 = result.cdn_auth_keys[0]
        assert key0.auth_key_name == "test7"
        assert key0.expiry_date == "2023-08-08"
        assert key0.header_name == "key"

    def test_missing_cdn_code(self, cloudwrapper_client):
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.list_auth_keys(
                ListAuthKeysRequest(contract_id="test_contract")
            )
        assert exc_info.value.title == (
            "list auth keys: struct validation:"
            " CDNCode: cannot be blank"
        )

    def test_missing_contract_id(self, cloudwrapper_client):
        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.list_auth_keys(
                ListAuthKeysRequest(cdn_code="dn123")
            )
        assert exc_info.value.title == (
            "list auth keys: struct validation:"
            " ContractID: cannot be blank"
        )

    def test_500_error(self, mock_session, cloudwrapper_client):
        body = (
            '{\n'
            '    "type": "internal_error",\n'
            '    "title": "Internal Server Error",\n'
            '    "detail": "Error processing request",\n'
            '    "status": 500\n'
            '}'
        )
        mock_session.exec.side_effect = _server_error_side_effect(500, body)

        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.list_auth_keys(
                ListAuthKeysRequest(
                    contract_id="test_contract",
                    cdn_code="dn123",
                )
            )
        err = exc_info.value
        assert err.status == 500
        assert "Internal Server Error" in err.title


class TestListCDNProviders:
    """Mirrors Go TestCloudwrapper_ListCDNProviders (multi_cdn_test.go 106-190)."""

    def test_200_ok(self, mock_session, cloudwrapper_client):
        response_body = """{
    "cdnProviders": [
        {
            "cdnCode": "dn002",
            "cdnName": "Level 3 (Centurylink)"
        },
        {
            "cdnCode": "dn003",
            "cdnName": "Limelight"
        },
        {
            "cdnCode": "dn004",
            "cdnName": "CloudFront"
        }
    ]
}"""
        parsed = json.loads(response_body)
        mock_response = make_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, parsed)

        result = cloudwrapper_client.list_cdn_providers()

        assert_request_made(
            mock_session, "GET",
            "/cloud-wrapper/v1/multi-cdn/providers",
        )

        assert len(result.cdn_providers) == 3
        assert result.cdn_providers[0].cdn_code == "dn002"
        assert result.cdn_providers[0].cdn_name == "Level 3 (Centurylink)"
        assert result.cdn_providers[1].cdn_code == "dn003"
        assert result.cdn_providers[1].cdn_name == "Limelight"
        assert result.cdn_providers[2].cdn_code == "dn004"
        assert result.cdn_providers[2].cdn_name == "CloudFront"

    def test_500_error(self, mock_session, cloudwrapper_client):
        body = (
            '{\n'
            '    "type": "internal_error",\n'
            '    "title": "Internal Server Error",\n'
            '    "detail": "Error processing request",\n'
            '    "status": 500\n'
            '}'
        )
        mock_session.exec.side_effect = _server_error_side_effect(500, body)

        with pytest.raises(Error) as exc_info:
            cloudwrapper_client.list_cdn_providers()
        err = exc_info.value
        assert err.status == 500
        assert "Internal Server Error" in err.title


# ===================================================================
# Client Construction Tests — from cloudwrapper_test.go
# ===================================================================

class TestClientConstruction:
    """Mirrors Go TestClient (cloudwrapper_test.go 34-62)."""

    def test_default(self):
        session = MagicMock(spec=Session)
        client = CloudWrapperClient(session)
        assert client._session is session  # pylint: disable=protected-access

    def test_with_options(self):
        session1 = MagicMock(spec=Session)
        session2 = MagicMock(spec=Session)
        client = CloudWrapperClient(session1)
        assert client._session is session1  # pylint: disable=protected-access
        client._session = session2  # pylint: disable=protected-access
        assert client._session is session2  # pylint: disable=protected-access
