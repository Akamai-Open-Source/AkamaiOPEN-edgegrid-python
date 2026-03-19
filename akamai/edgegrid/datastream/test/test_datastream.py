# pylint: disable=missing-function-docstring,missing-class-docstring
# pylint: disable=line-too-long,too-many-lines,protected-access
# pylint: disable=too-few-public-methods,too-many-arguments,too-many-positional-arguments
"""Unit tests for the DataStream API client.

Mirrors all Go test files from pkg/datastream/*_test.go:
  - ds_test.go          -> TestClient
  - errors_test.go      -> TestErrors
  - connectors_test.go  -> TestConnectorValidation
  - stream_test.go      -> TestGetStream, TestCreateStream, TestUpdateStream,
                           TestDeleteStream, TestDestinations,
                           TestSetDestinationTypes, TestListStreams
  - stream_activation_test.go -> TestActivateStream, TestDeactivateStream,
                                  TestGetActivationHistory
  - properties_test.go  -> TestGetProperties, TestGetDatasetFields
"""

import json
from unittest.mock import MagicMock, Mock

import pytest

from akamai.edgegrid.datastream.datastream import Client
from akamai.edgegrid.datastream.models import (
    CreateStreamRequest,
    GetStreamRequest,
    UpdateStreamRequest,
    DeleteStreamRequest,
    ListStreamsRequest,
    ActivateStreamRequest,
    DeactivateStreamRequest,
    GetActivationHistoryRequest,
    GetPropertiesRequest,
    GetDatasetFieldsRequest,
    DetailedStreamVersion,
    StreamConfiguration,
    DeliveryConfiguration,
    Frequency,
    PropertyID,
    DatasetFieldID,
    S3Connector,
    AzureConnector,
    DatadogConnector,
    SplunkConnector,
    GCSConnector,
    CustomHTTPSConnector,
    SumoLogicConnector,
    OracleCloudStorageConnector,
    LogglyConnector,
    NewRelicConnector,
    ElasticsearchConnector,
    S3CompatibleConnector,
    TrafficPeakConnector,
    DynatraceConnector,
    STREAM_STATUS_ACTIVATED,
    STREAM_STATUS_DEACTIVATED,
    STREAM_STATUS_ACTIVATING,
    STREAM_STATUS_DEACTIVATING,
    STREAM_STATUS_INACTIVE,
    DELIMITER_TYPE_SPACE,
    FORMAT_TYPE_STRUCTURED,
    FORMAT_TYPE_JSON,
    INTERVAL_IN_SECONDS_30,
    DESTINATION_TYPE_S3,
    AUTHENTICATION_TYPE_NONE,
    AUTHENTICATION_TYPE_BASIC,
)
from akamai.edgegrid.datastream.errors import (
    Error,
    RequestErrors,
    ErrStructValidation,
    ErrCreateStream,
    ErrGetStream,
    ErrUpdateStream,
    ErrDeleteStream,
    ErrListStreams,
    ErrActivateStream,
    ErrDeactivateStream,
    ErrGetActivationHistory,
    ErrGetProperties,
    ErrGetDatasetFields,
)
from akamai.edgegrid.datastream.validation import (
    validate_custom_https_connector,
)
from akamai.edgegrid.datastream.test.conftest import make_mock_response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _assert_validation_error(mock_client, method_name, params, sentinel):
    """Assert that calling *method_name* raises a validation ValueError."""
    method = getattr(mock_client, method_name)
    with pytest.raises(ValueError) as exc_info:
        method(params)
    msg = str(exc_info.value)
    assert sentinel in msg, f"Expected sentinel \'{sentinel}\' in: {msg}"
    assert ErrStructValidation in msg, (
        f"Expected \'{ErrStructValidation}\' in: {msg}"
    )


def _assert_api_error(mock_client, method_name, params,
                       mock_session, status_code, body,
                       sentinel, expected_error):
    """Assert that an API error response is properly parsed and raised."""
    resp = make_mock_response(status_code, body)
    mock_session.exec.return_value = (resp, None)
    method = getattr(mock_client, method_name)
    with pytest.raises(ValueError) as exc_info:
        method(params)
    msg = str(exc_info.value)
    assert sentinel in msg, f"Expected sentinel \'{sentinel}\' in: {msg}"
    # Verify parsing produces correct Error by comparing string forms
    actual_error = mock_client._parse_error(
        make_mock_response(status_code, body)
    )
    assert actual_error.is_equivalent(expected_error), (
        f"Error mismatch:\n  want: {expected_error}\n  got:  {actual_error}"
    )


def _call_success(mock_session, mock_client, method_name, params,
                   status_code, body):
    """Call *method_name* with a mock success response, return result."""
    resp = make_mock_response(status_code, body)
    data = json.loads(body) if body and body.strip() else None
    mock_session.exec.return_value = (resp, data)
    method = getattr(mock_client, method_name)
    return method(params)


def _verify_exec_call(mock_session, expected_method, expected_path,
                       expected_params=None):
    """Verify session.exec was called with the expected arguments."""
    mock_session.exec.assert_called_once()
    args, kwargs = mock_session.exec.call_args
    assert args[0] == expected_method, (
        f"HTTP method: want {expected_method}, got {args[0]}"
    )
    assert args[1] == expected_path, (
        f"Path: want {expected_path}, got {args[1]}"
    )
    if expected_params is not None:
        assert kwargs.get("params") == expected_params, (
            f"Params: want {expected_params}, got {kwargs.get('params')}"
        )


# ===================================================================
# TestClient — mirrors ds_test.go TestClient (lines 38-66)
# ===================================================================


class TestClient:
    """Mirrors Go TestClient — verifies Client construction."""

    def test_no_options_provided_return_default(self):
        session = MagicMock()
        client = Client(session)
        assert client is not None
        assert client._session is session

    def test_option_provided_overwrite_session(self):
        session1 = MagicMock()
        session2 = MagicMock()
        client = Client(session1)
        assert client._session is session1
        client._session = session2
        assert client._session is session2


# ===================================================================
# TestErrors — mirrors errors_test.go (lines 15-131)
# ===================================================================


class TestErrors:
    """Mirrors Go TestNewError and TestJsonErrorUnmarshalling.

    Tests error parsing from HTTP responses via Client._parse_error.
    """

    def test_valid_response_status_code_500(self):
        body = '''{"type":"a","title":"b","detail":"c"}'''
        resp = make_mock_response(500, body)
        client = Client(MagicMock())
        result = client._parse_error(resp)
        expected = Error(type="a", title="b", detail="c", status_code=500)
        assert result.is_equivalent(expected), (
            f"want: {expected}\ngot:  {result}"
        )

    def test_invalid_response_body_assign_status_code(self):
        body = "test"
        resp = make_mock_response(500, body)
        client = Client(MagicMock())
        result = client._parse_error(resp)
        expected = Error(
            title=(
                "Failed to unmarshal error body. "
                "DataStream2 API failed. "
                "Check details for more information."
            ),
            detail="test",
            status_code=500,
        )
        assert result.is_equivalent(expected), (
            f"want: {expected}\ngot:  {result}"
        )

    def test_api_failure_with_html_response(self):
        body = "<HTML><HEAD>...</HEAD><BODY>...</BODY></HTML>"
        resp = make_mock_response(503, body)
        client = Client(MagicMock())
        result = client._parse_error(resp)
        expected = Error(
            title=(
                "Failed to unmarshal error body. "
                "DataStream2 API failed. "
                "Check details for more information."
            ),
            detail="<HTML><HEAD>...</HEAD><BODY>...</BODY></HTML>",
            status_code=503,
        )
        assert result.is_equivalent(expected)

    def test_api_failure_with_plain_text_response(self):
        body = (
            "Your request did not succeed as this operation has reached"
            "  the limit for your account. Please try after"
            " 2024-01-16T15:20:55.945Z"
        )
        resp = make_mock_response(503, body)
        client = Client(MagicMock())
        result = client._parse_error(resp)
        expected = Error(
            title=(
                "Failed to unmarshal error body. "
                "DataStream2 API failed. "
                "Check details for more information."
            ),
            detail=body,
            status_code=503,
        )
        assert result.is_equivalent(expected)

    def test_api_failure_with_xml_response(self):
        body = '<Root><Item id="1" name="Example" /></Root>'
        resp = make_mock_response(503, body)
        client = Client(MagicMock())
        result = client._parse_error(resp)
        expected = Error(
            title=(
                "Failed to unmarshal error body. "
                "DataStream2 API failed. "
                "Check details for more information."
            ),
            detail=body,
            status_code=503,
        )
        assert result.is_equivalent(expected)


# ===================================================================
# TestConnectorValidation — mirrors connectors_test.go (lines 10-123)
# ===================================================================


class TestConnectorValidation:
    """Mirrors Go TestCustomHTTPSValidation — 11 cases."""

    @staticmethod
    def _base_connector():
        c = CustomHTTPSConnector(
            display_name="Test Connector",
            authentication_type=AUTHENTICATION_TYPE_NONE,
            endpoint="https://example.com",
        )
        c.set_destination_type()
        return c

    @pytest.mark.parametrize("name,modify,expect_error", [
        (
            "AuthenticationType not in specified set",
            {"authentication_type": "NOTEXISTING"},
            True,
        ),
        (
            "UserName required for auth type BASIC",
            {"authentication_type": AUTHENTICATION_TYPE_BASIC,
             "password": "password"},
            True,
        ),
        (
            "Password required for auth type BASIC",
            {"authentication_type": AUTHENTICATION_TYPE_BASIC,
             "user_name": "username"},
            True,
        ),
        (
            "UserName and Password not required for type NONE",
            {"authentication_type": AUTHENTICATION_TYPE_NONE},
            False,
        ),
        (
            "UserName and Password required for type BASIC",
            {"authentication_type": AUTHENTICATION_TYPE_BASIC},
            True,
        ),
        (
            "CustomHeaderName specified without CustomHeaderValue",
            {"custom_header_name": "Custom_Name"},
            True,
        ),
        (
            "CustomHeaderValue specified without CustomHeaderName",
            {"custom_header_value": "Custom header value"},
            True,
        ),
        (
            "CustomHeaderValue and CustomHeaderName both specified",
            {"custom_header_name": "Custom_Name",
             "custom_header_value": "Custom header value"},
            False,
        ),
        (
            "CustomHeaderName contains forbidden characters",
            {"custom_header_name": "azAZ09_-!?>",
             "custom_header_value": "Custom header value"},
            True,
        ),
        (
            "CustomHeaderName contains only allowed characters",
            {"custom_header_name": "azAZ09_-",
             "custom_header_value": "Custom header value"},
            False,
        ),
        (
            "CustomHeaderValue and CustomHeaderName are optional",
            {},
            False,
        ),
    ])
    def test_custom_https_validation(self, name, modify, expect_error):
        connector = self._base_connector()
        for key, val in modify.items():
            setattr(connector, key, val)
        err = validate_custom_https_connector(connector)
        if expect_error:
            assert err is not None, (
                f"[{name}] expected validation error but got None"
            )
        else:
            assert err is None, (
                f"[{name}] expected no error but got: {err}"
            )


# ===================================================================
# TestGetStream — mirrors stream_test.go TestDs_GetStream (lines 17-429)
# ===================================================================


# --- Verbatim response bodies from Go tests ---

_GET_STREAM_BODY_1 = (
    '{"collectMidgress":false,"contractId":"P-1324","createdBy":"user1",'
    '"createdDate":"16-01-2020 11:07:12 GMT",'
    '"currentVersionId":2,'
    '"datasetFields":[{"datasetFieldDescription":"datasetFieldDescription_1",'
    '"datasetFieldGroup":"group_1","datasetFieldId":1,"datasetFieldJsonKey":"jsonKey_1",'
    '"datasetFieldName":"name_1"},{"datasetFieldDescription":"datasetFieldDescription_2",'
    '"datasetFieldGroup":"group_2","datasetFieldId":2,"datasetFieldJsonKey":"jsonKey_2",'
    '"datasetFieldName":"name_2"},{"datasetFieldDescription":"datasetFieldDescription_3",'
    '"datasetFieldGroup":"group_3","datasetFieldId":3,"datasetFieldJsonKey":"jsonKey_3",'
    '"datasetFieldName":"name_3"}],'
    '"deliveryConfiguration":{"delimiter":"SPACE","fieldDelimiter":"SPACE",'
    '"format":"STRUCTURED","frequency":{"intervalInSeconds":30},'
    '"uploadFilePrefix":"logs","uploadFileSuffix":"ak"},'
    '"destination":{"bucket":"bucket_1","compressLogs":false,"destinationType":"S3",'
    '"displayName":"displayName_1","path":"path_1","region":"region_1"},'
    '"groupId":1234,"latestVersion":2,"modifiedBy":"user2",'
    '"modifiedDate":"16-01-2020 11:07:12 GMT",'
    '"notificationEmails":["useremail1@akamai.com","useremail2@akamai.com"],'
    '"productId":"Adaptive_Media_Delivery",'
    '"properties":[{"hostname":"hostname_1","productId":"Adaptive_Media_Delivery",'
    '"productName":"Adaptive Media Delivery","propertyId":1,"propertyName":"property_1"},'
    '{"hostname":"hostname_2","productId":"Adaptive_Media_Delivery",'
    '"productName":"Adaptive Media Delivery","propertyId":2,"propertyName":"property_2"}],'
    '"streamId":1,"streamName":"TestStream","streamStatus":"ACTIVATED",'
    '"streamVersion":2}'
)

_GET_STREAM_BODY_2 = (
    '{"collectMidgress":true,"contractId":"P-1324","createdBy":"user1",'
    '"createdDate":"16-01-2020 11:07:12 GMT",'
    '"currentVersionId":2,'
    '"datasetFields":[{"datasetFieldDescription":"datasetFieldDescription_1",'
    '"datasetFieldGroup":"group_1","datasetFieldId":1,"datasetFieldJsonKey":"jsonKey_1",'
    '"datasetFieldName":"name_1"}],'
    '"deliveryConfiguration":{"delimiter":"SPACE","fieldDelimiter":"SPACE",'
    '"format":"STRUCTURED","frequency":{"intervalInSeconds":30},'
    '"uploadFilePrefix":"logs","uploadFileSuffix":"ak"},'
    '"destination":{"bucket":"bucket_1","compressLogs":false,"destinationType":"S3",'
    '"displayName":"displayName_1","path":"path_1","region":"region_1"},'
    '"groupId":1234,"integrationType":"DS_MANAGED","latestVersion":2,'
    '"modifiedBy":"user2","modifiedDate":"16-01-2020 11:07:12 GMT",'
    '"notificationEmails":["useremail1@akamai.com"],'
    '"productId":"Adaptive_Media_Delivery",'
    '"properties":[{"hostname":"hostname_1","productId":"Adaptive_Media_Delivery",'
    '"productName":"Adaptive Media Delivery","propertyId":1,"propertyName":"property_1"}],'
    '"samplingPercentage":33,"streamId":2,"streamName":"TestStream",'
    '"streamStatus":"ACTIVATED","streamVersion":2}'
)

_GET_STREAM_BODY_3 = (
    '{"collectMidgress":false,"contractId":"P-1324","createdBy":"user1",'
    '"createdDate":"16-01-2020 11:07:12 GMT",'
    '"currentVersionId":2,'
    '"datasetFields":[{"datasetFieldDescription":"datasetFieldDescription_1",'
    '"datasetFieldGroup":"group_1","datasetFieldId":1,"datasetFieldJsonKey":"jsonKey_1",'
    '"datasetFieldName":"name_1"}],'
    '"deliveryConfiguration":{"delimiter":"SPACE","fieldDelimiter":"SPACE",'
    '"format":"STRUCTURED","frequency":{"intervalInSeconds":30},'
    '"uploadFilePrefix":"logs","uploadFileSuffix":"ak"},'
    '"destination":{"bucket":"bucket_1","compressLogs":false,"destinationType":"S3",'
    '"displayName":"displayName_1","path":"path_1","region":"region_1"},'
    '"groupId":1234,"integrationType":"PM_DEPENDENT","latestVersion":2,'
    '"modifiedBy":"user2","modifiedDate":"16-01-2020 11:07:12 GMT",'
    '"notificationEmails":["useremail1@akamai.com"],'
    '"productId":"Adaptive_Media_Delivery",'
    '"properties":[{"hostname":"hostname_1","productId":"Adaptive_Media_Delivery",'
    '"productName":"Adaptive Media Delivery","propertyId":1,"propertyName":"property_1"}],'
    '"samplingPercentage":50,"streamId":3,"streamName":"TestStream",'
    '"streamStatus":"INACTIVE","streamVersion":2}'
)

_GET_STREAM_BODY_4 = (
    '{"collectMidgress":false,"contractId":"P-1324","createdBy":"user1",'
    '"createdDate":"16-01-2020 11:07:12 GMT",'
    '"currentVersionId":2,'
    '"datasetFields":[{"datasetFieldDescription":"datasetFieldDescription_1",'
    '"datasetFieldGroup":"group_1","datasetFieldId":1,"datasetFieldJsonKey":"jsonKey_1",'
    '"datasetFieldName":"name_1"}],'
    '"deliveryConfiguration":{"delimiter":"SPACE","fieldDelimiter":"SPACE",'
    '"format":"STRUCTURED","frequency":{"intervalInSeconds":30},'
    '"uploadFilePrefix":"logs","uploadFileSuffix":"ak"},'
    '"destination":{"bucket":"bucket_1","compressLogs":false,"destinationType":"S3",'
    '"displayName":"displayName_1","path":"path_1","region":"region_1"},'
    '"groupId":1234,"integrationType":"HYBRID","latestVersion":2,'
    '"modifiedBy":"user2","modifiedDate":"16-01-2020 11:07:12 GMT",'
    '"notificationEmails":["useremail1@akamai.com"],'
    '"productId":"Adaptive_Media_Delivery",'
    '"properties":[{"hostname":"hostname_1","productId":"Adaptive_Media_Delivery",'
    '"productName":"Adaptive Media Delivery","propertyId":1,"propertyName":"property_1"}],'
    '"samplingPercentage":88,"streamId":4,"streamName":"TestStream",'
    '"streamStatus":"INACTIVE","streamVersion":2}'
)

_GET_STREAM_ERROR_400 = (
    '{"type":"bad-request","title":"Bad Request",'
    '"detail":"bad request",'
    '"instance":"82b67b97-d98d-4bee-ac1e-ef6eaf7cac82",'
    '"statusCode":400,'
    '"errors":[{"type":"bad-request","title":"Bad Request",'
    '"detail":"Stream does not exist. Please provide valid stream."}]}'
)


class TestGetStream:
    """Mirrors Go TestDs_GetStream — 6 cases."""

    def test_200_ok_without_midgress(self, mock_session, mock_client):
        result = _call_success(
            mock_session, mock_client, "get_stream",
            GetStreamRequest(stream_id=1), 200, _GET_STREAM_BODY_1,
        )
        _verify_exec_call(
            mock_session, "GET",
            "/datastream-config-api/v3/log/cdn/streams/1",
        )
        assert isinstance(result, DetailedStreamVersion)
        assert result.stream_id == 1
        assert result.stream_name == "TestStream"
        assert result.stream_status == STREAM_STATUS_ACTIVATED
        assert result.collect_midgress is False
        assert result.contract_id == "P-1324"
        assert result.group_id == 1234
        assert result.latest_version == 2
        assert result.stream_version == 2
        assert result.created_by == "user1"
        assert result.modified_by == "user2"
        assert result.product_id == "Adaptive_Media_Delivery"
        # delivery config
        assert result.delivery_configuration.delimiter == DELIMITER_TYPE_SPACE
        assert result.delivery_configuration.format == FORMAT_TYPE_STRUCTURED
        assert result.delivery_configuration.frequency.interval_in_seconds == INTERVAL_IN_SECONDS_30
        assert result.delivery_configuration.upload_file_prefix == "logs"
        assert result.delivery_configuration.upload_file_suffix == "ak"
        # destination
        assert result.destination.destination_type == DESTINATION_TYPE_S3
        assert result.destination.display_name == "displayName_1"
        assert result.destination.bucket == "bucket_1"
        assert result.destination.path == "path_1"
        assert result.destination.region == "region_1"
        # dataset fields
        assert len(result.dataset_fields) == 3
        assert result.dataset_fields[0].dataset_field_id == 1
        # properties
        assert len(result.properties) == 2
        # notification emails
        assert len(result.notification_emails) == 2

    def test_200_ok_with_midgress_ds_managed_sp33(self, mock_session,
                                                    mock_client):
        result = _call_success(
            mock_session, mock_client, "get_stream",
            GetStreamRequest(stream_id=2), 200, _GET_STREAM_BODY_2,
        )
        assert result.collect_midgress is True
        assert result.integration_type == "DS_MANAGED"
        assert result.sampling_percentage == 33
        assert result.stream_id == 2

    def test_200_ok_pm_dependent_sp50(self, mock_session, mock_client):
        result = _call_success(
            mock_session, mock_client, "get_stream",
            GetStreamRequest(stream_id=3), 200, _GET_STREAM_BODY_3,
        )
        assert result.integration_type == "PM_DEPENDENT"
        assert result.sampling_percentage == 50
        assert result.stream_status == STREAM_STATUS_INACTIVE
        assert result.stream_id == 3

    def test_200_ok_hybrid_sp88(self, mock_session, mock_client):
        result = _call_success(
            mock_session, mock_client, "get_stream",
            GetStreamRequest(stream_id=4), 200, _GET_STREAM_BODY_4,
        )
        assert result.integration_type == "HYBRID"
        assert result.sampling_percentage == 88
        assert result.stream_id == 4

    def test_validation_error(self, mock_client):
        _assert_validation_error(
            mock_client, "get_stream",
            GetStreamRequest(stream_id=0), ErrGetStream,
        )

    def test_400_bad_request(self, mock_session, mock_client):
        _assert_api_error(
            mock_client, "get_stream",
            GetStreamRequest(stream_id=12),
            mock_session, 400, _GET_STREAM_ERROR_400,
            ErrGetStream,
            Error(
                type="bad-request", title="Bad Request",
                detail="bad request",
                instance="82b67b97-d98d-4bee-ac1e-ef6eaf7cac82",
                status_code=400,
                errors=[
                    RequestErrors(
                        type="bad-request", title="Bad Request",
                        detail="Stream does not exist. Please provide valid stream.",
                    ),
                ],
            ),
        )


# ===================================================================
# TestCreateStream — mirrors stream_test.go TestDs_CreateStream
#                    (lines 431-898)
# ===================================================================

_CREATE_STREAM_BODY_PM_DEPENDENT = """{
    "contractId": "2-AB1234",
    "createdBy": "pmuser",
    "createdDate": "2023-01-20T10:00:00Z",
    "integrationType": "PM_DEPENDENT",
    "samplingPercentage": 75,
    "collectMidgress": true,
    "datasetFields": [
        {"datasetFieldId":2020, "datasetFieldName":"pm_field", "datasetFieldJsonKey":"pm_key"}
    ],
    "deliveryConfiguration": {
        "fieldDelimiter": "SPACE",
        "format": "STRUCTURED",
        "frequency": {"intervalInSeconds": 15},
        "uploadFilePrefix": "pm_logs",
        "uploadFileSuffix": "pmx"
    },
    "destination": {
        "bucket": "pmbucket.com",
        "compressLogs": false,
        "destinationType": "S3",
        "displayName": "pm display-name",
        "path": "pm-path/{%Y/%m/%d}",
        "region": "eu-central-1"
    },
    "groupId": 1234,
    "latestVersion": 2,
    "modifiedBy": "pmuser2",
    "modifiedDate": "2023-01-21T12:00:00Z",
    "notificationEmails": ["pmuser@akamai.com"],
    "productId": "PMDelivery",
    "properties": [{"propertyId": 4321, "propertyName": "pmprop"}],
    "streamId": 9500,
    "streamName": "PMStream",
    "streamStatus": "ACTIVATED",
    "streamVersion": 2
}"""

_CREATE_STREAM_BODY_ACTIVATE_NOW = """{
    "contractId": "2-AB1234",
    "createdBy": "sample_username",
    "createdDate": "2022-11-04T00:49:45Z",
    "collectMidgress": true,
    "datasetFields": [
        {
            "datasetFieldId":2020,
            "datasetFieldName":"field_name_1",
            "datasetFieldJsonKey":"field_json_key_1"
        }
    ],
    "deliveryConfiguration": {
        "fieldDelimiter": "SPACE",
        "format": "STRUCTURED",
        "frequency": {
            "intervalInSeconds": 30
        },
        "uploadFilePrefix": "logs",
        "uploadFileSuffix": "ak"
    },
    "destination": {
        "bucket": "datastream.com",
        "compressLogs": true,
        "destinationType": "S3",
        "displayName": "sample-display-name",
        "path": "sample-path/{%Y/%m/%d}",
        "region": "ap-south-1"
    },
    "groupId": 1234,
    "latestVersion": 1,
    "modifiedBy": "sample_username2",
    "modifiedDate": "2022-11-04T02:14:29Z",
    "notificationEmails": [
        "useremail1@akamai.com", "useremail2@akamai.com"
    ],
    "productId": "Adaptive_Media_Delivery",
    "properties": [
        {
            "propertyId": 1234,
            "propertyName": "abcd"
        },
        {
            "propertyId": 1234,
            "propertyName": "abcd"
        }
    ],
    "streamId": 7050,
    "streamName": "TestStream",
    "streamStatus": "ACTIVATED",
    "streamVersion": 1
}"""

_CREATE_STREAM_ERROR_403 = """{
\t"type": "forbidden",
\t"title": "Forbidden",
\t"detail": "forbidden",
\t"instance": "72a7654e-3f95-454f-a174-104bc946be52",
\t"statusCode": 403,
\t"errors": [
\t\t{
\t\t\t"type": "forbidden",
\t\t\t"title": "Forbidden",
\t\t\t"detail": "User is not having access for the group. Access denied, please contact support."
\t\t}
\t]
}"""

_CREATE_STREAM_ERROR_400 = """{
\t"type": "bad-request",
\t"title": "Bad Request",
\t"detail": "bad-request",
\t"instance": "d0d2497e-ed93-4685-b44c-93a8eb8f3dea",
\t"statusCode": 400,
\t"errors": [
\t\t{
\t\t\t"type": "bad-request",
\t\t\t"title": "Bad Request",
\t\t\t"detail": "The credentials provided don\u2019t give you write access to the bucket. Check your AWS credentials or bucket permissions in the S3 account and try again."
\t\t}
\t]
}"""


def _base_create_request():
    """Build the baseline CreateStreamRequest used by CreateStream tests."""
    return CreateStreamRequest(
        activate=True,
        stream_configuration=StreamConfiguration(
            delivery_configuration=DeliveryConfiguration(
                delimiter=DELIMITER_TYPE_SPACE,
                format=FORMAT_TYPE_STRUCTURED,
                frequency=Frequency(
                    interval_in_seconds=INTERVAL_IN_SECONDS_30,
                ),
                upload_file_prefix="logs",
                upload_file_suffix="ak",
            ),
            destination=S3Connector(
                path="sample-path/{%Y/%m/%d}",
                display_name="sample-display-name",
                bucket="datastream.com",
                region="ap-south-1",
                access_key="1234ABCD",
                secret_access_key="1234ABCD",
            ),
            contract_id="2-AB1234",
            dataset_fields=[DatasetFieldID(dataset_field_id=2020)],
            notification_emails=[
                "useremail1@akamai.com",
                "useremail2@akamai.com",
            ],
            group_id=1234,
            properties=[
                PropertyID(property_id=1234),
                PropertyID(property_id=1234),
            ],
            stream_name="TestStream",
            collect_midgress=True,
            sampling_percentage=0,
        ),
    )


class TestCreateStream:
    """Mirrors Go TestDs_CreateStream — 10 cases (2 success, 6 validation, 2 API error)."""

    def test_201_pm_dependent_sp75(self, mock_session, mock_client):
        req = _base_create_request()
        req.stream_configuration.sampling_percentage = 75
        result = _call_success(
            mock_session, mock_client, "create_stream",
            req, 201, _CREATE_STREAM_BODY_PM_DEPENDENT,
        )
        assert result.contract_id == "2-AB1234"
        assert result.created_by == "pmuser"
        assert result.integration_type == "PM_DEPENDENT"
        assert result.sampling_percentage == 75
        assert result.collect_midgress is True
        assert result.stream_id == 9500
        assert result.stream_name == "PMStream"
        assert result.stream_status == STREAM_STATUS_ACTIVATED
        assert result.stream_version == 2
        assert result.group_id == 1234
        assert result.latest_version == 2

    def test_201_activate_now_true(self, mock_session, mock_client):
        req = _base_create_request()
        result = _call_success(
            mock_session, mock_client, "create_stream",
            req, 201, _CREATE_STREAM_BODY_ACTIVATE_NOW,
        )
        assert result.stream_id == 7050
        assert result.stream_name == "TestStream"
        assert result.stream_status == STREAM_STATUS_ACTIVATED
        assert result.stream_version == 1
        assert result.collect_midgress is True
        assert result.contract_id == "2-AB1234"
        assert result.created_by == "sample_username"
        assert result.modified_by == "sample_username2"
        assert result.product_id == "Adaptive_Media_Delivery"
        assert len(result.dataset_fields) == 1
        assert result.dataset_fields[0].dataset_field_id == 2020
        assert len(result.properties) == 2
        assert result.properties[0].property_id == 1234
        assert len(result.notification_emails) == 2

    def test_validation_error_empty_destination(self, mock_session, mock_client):
        req = _base_create_request()
        req.stream_configuration.destination = S3Connector()
        req.stream_configuration.destination.set_destination_type()
        _assert_validation_error(
            mock_client, "create_stream", req, ErrCreateStream,
        )
        mock_session.exec.assert_not_called()

    def test_validation_error_delimiter_with_json(self, mock_session, mock_client):
        req = _base_create_request()
        req.stream_configuration.delivery_configuration = DeliveryConfiguration(
            delimiter=DELIMITER_TYPE_SPACE,
            format=FORMAT_TYPE_JSON,
            frequency=Frequency(interval_in_seconds=INTERVAL_IN_SECONDS_30),
            upload_file_prefix="logs",
            upload_file_suffix="ak",
        )
        _assert_validation_error(
            mock_client, "create_stream", req, ErrCreateStream,
        )
        mock_session.exec.assert_not_called()

    def test_validation_error_no_delimiter_structured(self, mock_session, mock_client):
        req = _base_create_request()
        req.stream_configuration.delivery_configuration = DeliveryConfiguration(
            format=FORMAT_TYPE_STRUCTURED,
            frequency=Frequency(interval_in_seconds=INTERVAL_IN_SECONDS_30),
            upload_file_prefix="logs",
            upload_file_suffix="ak",
        )
        _assert_validation_error(
            mock_client, "create_stream", req, ErrCreateStream,
        )
        mock_session.exec.assert_not_called()

    def test_validation_error_missing_dest_config(self, mock_session, mock_client):
        req = _base_create_request()
        req.stream_configuration.destination = S3Connector(
            path="log/edgelogs/{ %Y/%m/%d }",
            display_name="S3Destination",
            bucket="datastream.akamai.com",
            region="ap-south-1",
        )
        req.stream_configuration.destination.set_destination_type()
        _assert_validation_error(
            mock_client, "create_stream", req, ErrCreateStream,
        )
        mock_session.exec.assert_not_called()

    def test_validation_error_sampling_lt_1(self, mock_session, mock_client):
        req = _base_create_request()
        req.stream_configuration.sampling_percentage = -1
        _assert_validation_error(
            mock_client, "create_stream", req, ErrCreateStream,
        )
        mock_session.exec.assert_not_called()

    def test_validation_error_sampling_gt_100(self, mock_session, mock_client):
        req = _base_create_request()
        req.stream_configuration.sampling_percentage = 101
        _assert_validation_error(
            mock_client, "create_stream", req, ErrCreateStream,
        )
        mock_session.exec.assert_not_called()

    def test_403_forbidden(self, mock_session, mock_client):
        req = _base_create_request()
        _assert_api_error(
            mock_client, "create_stream", req,
            mock_session, 403, _CREATE_STREAM_ERROR_403,
            ErrCreateStream,
            Error(
                type="forbidden", title="Forbidden",
                detail="forbidden",
                instance="72a7654e-3f95-454f-a174-104bc946be52",
                status_code=403,
                errors=[RequestErrors(
                    type="forbidden", title="Forbidden",
                    detail="User is not having access for the group. Access denied, please contact support.",
                )],
            ),
        )

    def test_400_bad_request(self, mock_session, mock_client):
        req = _base_create_request()
        _assert_api_error(
            mock_client, "create_stream", req,
            mock_session, 400, _CREATE_STREAM_ERROR_400,
            ErrCreateStream,
            Error(
                type="bad-request", title="Bad Request",
                detail="bad-request",
                instance="d0d2497e-ed93-4685-b44c-93a8eb8f3dea",
                status_code=400,
                errors=[RequestErrors(
                    type="bad-request", title="Bad Request",
                    detail="The credentials provided don\u2019t give you write access to the bucket. Check your AWS credentials or bucket permissions in the S3 account and try again.",
                )],
            ),
        )


# ===================================================================
# TestUpdateStream — mirrors stream_test.go TestDs_UpdateStream
#                    (lines 900-1166)
# ===================================================================

_UPDATE_STREAM_BODY_OK = """{
    "contractId": "2-AB1234",
    "createdBy": "sample_username",
    "createdDate": "2022-11-04T00:49:45Z",
    "collectMidgress": true,
    "integrationType": "PM_DEPENDENT",
    "samplingPercentage": 55,
    "datasetFields": [
        {
            "datasetFieldId":2020,
            "datasetFieldName":"field_name_1",
            "datasetFieldJsonKey":"field_json_key_1"
        }
    ],
    "deliveryConfiguration": {
        "fieldDelimiter": "SPACE",
        "format": "STRUCTURED",
        "frequency": {
            "intervalInSeconds": 30
        },
        "uploadFilePrefix": "logs",
        "uploadFileSuffix": "ak"
    },
    "destination": {
        "bucket": "datastream.com",
        "compressLogs": true,
        "destinationType": "S3",
        "displayName": "sample-display-name",
        "path": "sample-path/{%Y/%m/%d}",
        "region": "ap-south-1"
    },
    "groupId": 1234,
    "latestVersion": 2,
    "modifiedBy": "modified_by_user",
    "modifiedDate": "2022-11-04T02:14:29Z",
    "notificationEmails": [
        "useremail1@akamai.com", "useremail2@akamai.com"
    ],
    "productId": "Adaptive_Media_Delivery",
    "properties": [
        {
            "propertyId": 1234,
            "propertyName": "sample1.com"
        },
        {
            "propertyId": 1234,
            "propertyName": "sample2.com"
        }
    ],
    "streamId": 7050,
    "streamName": "TestStream",
    "streamStatus": "ACTIVATED",
    "streamVersion": 2
}"""

_UPDATE_STREAM_ERROR_400 = """{
\t"type": "bad-request",
\t"title": "Bad Request",
\t"detail": "bad request",
\t"instance": "a42cc1e6-fea4-4e3a-91ce-9da9819e089a",
\t"statusCode": 400,
\t"errors": [
\t\t{
\t\t\t"type": "bad-request",
\t\t\t"title": "Bad Request",
\t\t\t"detail": "Stream does not exist. Please provide valid stream."
\t\t}
\t]
}"""


def _base_update_request():
    """Build baseline UpdateStreamRequest used by UpdateStream tests."""
    return UpdateStreamRequest(
        stream_id=7050,
        activate=True,
        stream_configuration=StreamConfiguration(
            delivery_configuration=DeliveryConfiguration(
                delimiter=DELIMITER_TYPE_SPACE,
                format=FORMAT_TYPE_STRUCTURED,
                frequency=Frequency(
                    interval_in_seconds=INTERVAL_IN_SECONDS_30,
                ),
                upload_file_prefix="logs",
                upload_file_suffix="ak",
            ),
            destination=S3Connector(
                display_name="sample-display-name",
                destination_type=DESTINATION_TYPE_S3,
                path="sample-path/{%Y/%m/%d}",
                bucket="datastream.com",
                region="ap-south-1",
                access_key="ABC",
                secret_access_key="XYZ",
            ),
            contract_id="P-1324",
            dataset_fields=[
                DatasetFieldID(dataset_field_id=1),
                DatasetFieldID(dataset_field_id=2),
                DatasetFieldID(dataset_field_id=3),
            ],
            notification_emails=[
                "test@aka.mai",
                "useremail2@akamai.com",
            ],
            properties=[
                PropertyID(property_id=123123),
                PropertyID(property_id=123123),
            ],
            stream_name="TestStream",
        ),
    )


class TestUpdateStream:
    """Mirrors Go TestDs_UpdateStream — 8 cases."""

    def test_200_ok_with_integration_type(self, mock_session, mock_client):
        req = _base_update_request()
        result = _call_success(
            mock_session, mock_client, "update_stream",
            req, 200, _UPDATE_STREAM_BODY_OK,
        )
        assert result.stream_id == 7050
        assert result.contract_id == "2-AB1234"
        assert result.integration_type == "PM_DEPENDENT"
        assert result.sampling_percentage == 55
        assert result.collect_midgress is True
        assert result.stream_status == STREAM_STATUS_ACTIVATED
        assert result.stream_version == 2
        assert result.modified_by == "modified_by_user"
        assert len(result.dataset_fields) == 1
        assert result.dataset_fields[0].dataset_field_id == 2020
        assert len(result.properties) == 2
        assert result.properties[0].property_name == "sample1.com"

    def test_validation_error_delimiter_with_json(self, mock_session, mock_client):
        req = _base_update_request()
        req.stream_configuration.delivery_configuration = DeliveryConfiguration(
            delimiter=DELIMITER_TYPE_SPACE,
            format=FORMAT_TYPE_JSON,
            frequency=Frequency(interval_in_seconds=INTERVAL_IN_SECONDS_30),
            upload_file_prefix="logs",
            upload_file_suffix="ak",
        )
        _assert_validation_error(
            mock_client, "update_stream", req, ErrUpdateStream,
        )
        mock_session.exec.assert_not_called()

    def test_validation_error_no_delimiter_structured(self, mock_session, mock_client):
        req = _base_update_request()
        req.stream_configuration.delivery_configuration = DeliveryConfiguration(
            format=FORMAT_TYPE_STRUCTURED,
            frequency=Frequency(interval_in_seconds=INTERVAL_IN_SECONDS_30),
            upload_file_prefix="logs",
            upload_file_suffix="ak",
        )
        _assert_validation_error(
            mock_client, "update_stream", req, ErrUpdateStream,
        )
        mock_session.exec.assert_not_called()

    def test_validation_error_group_id_modification(self, mock_session, mock_client):
        req = _base_update_request()
        req.stream_configuration.group_id = 1337
        _assert_validation_error(
            mock_client, "update_stream", req, ErrUpdateStream,
        )
        mock_session.exec.assert_not_called()

    def test_validation_error_missing_contract_id(self, mock_session, mock_client):
        req = _base_update_request()
        req.stream_configuration.contract_id = ""
        _assert_validation_error(
            mock_client, "update_stream", req, ErrUpdateStream,
        )
        mock_session.exec.assert_not_called()

    def test_validation_error_sampling_lt_1(self, mock_session, mock_client):
        req = _base_update_request()
        req.stream_configuration.sampling_percentage = -1
        _assert_validation_error(
            mock_client, "update_stream", req, ErrUpdateStream,
        )
        mock_session.exec.assert_not_called()

    def test_validation_error_sampling_gt_100(self, mock_session, mock_client):
        req = _base_update_request()
        req.stream_configuration.sampling_percentage = 101
        _assert_validation_error(
            mock_client, "update_stream", req, ErrUpdateStream,
        )
        mock_session.exec.assert_not_called()

    def test_400_bad_request(self, mock_session, mock_client):
        req = _base_update_request()
        _assert_api_error(
            mock_client, "update_stream", req,
            mock_session, 400, _UPDATE_STREAM_ERROR_400,
            ErrUpdateStream,
            Error(
                type="bad-request", title="Bad Request",
                detail="bad request",
                instance="a42cc1e6-fea4-4e3a-91ce-9da9819e089a",
                status_code=400,
                errors=[RequestErrors(
                    type="bad-request", title="Bad Request",
                    detail="Stream does not exist. Please provide valid stream.",
                )],
            ),
        )


# ===================================================================
# TestDeleteStream — mirrors stream_test.go TestDs_DeleteStream
#                    (lines 1168-1249)
# ===================================================================

_DELETE_STREAM_ERROR_400 = """{
\t"type": "bad-request",
\t"title": "Bad Request",
\t"detail": "bad request",
\t"instance": "82b67b97-d98d-4bee-ac1e-ef6eaf7cac82",
\t"statusCode": 400,
\t"errors": [
\t\t{
\t\t\t"type": "bad-request",
\t\t\t"title": "Bad Request",
\t\t\t"detail": "Stream does not exist. Please provide valid stream."
\t\t}
\t]
}"""


class TestDeleteStream:
    """Mirrors Go TestDs_DeleteStream — 3 cases."""

    def test_200_ok(self, mock_session, mock_client):
        resp = make_mock_response(204, "")
        mock_session.exec.return_value = (resp, None)
        mock_client.delete_stream(DeleteStreamRequest(stream_id=1))
        _verify_exec_call(
            mock_session, "DELETE",
            "/datastream-config-api/v3/log/cdn/streams/1",
        )

    def test_validation_error(self, mock_session, mock_client):
        _assert_validation_error(
            mock_client, "delete_stream",
            DeleteStreamRequest(stream_id=0), ErrDeleteStream,
        )
        mock_session.exec.assert_not_called()

    def test_400_bad_request(self, mock_session, mock_client):
        _assert_api_error(
            mock_client, "delete_stream",
            DeleteStreamRequest(stream_id=12),
            mock_session, 400, _DELETE_STREAM_ERROR_400,
            ErrDeleteStream,
            Error(
                type="bad-request", title="Bad Request",
                detail="bad request",
                instance="82b67b97-d98d-4bee-ac1e-ef6eaf7cac82",
                status_code=400,
                errors=[RequestErrors(
                    type="bad-request", title="Bad Request",
                    detail="Stream does not exist. Please provide valid stream.",
                )],
            ),
        )


# ===================================================================
# TestDestinations — mirrors stream_test.go TestDs_Destinations
#                    (lines 1251-1641) — 14 connector serialization tests
# ===================================================================


def _dest_base_request(connector):
    """Build base CreateStreamRequest for Destination tests.

    Uses the same config as Go: ContractID "P-1324", GroupID 123231,
    3 dataset fields, 1 notification email, 2 properties.
    """
    return CreateStreamRequest(
        activate=True,
        stream_configuration=StreamConfiguration(
            delivery_configuration=DeliveryConfiguration(
                delimiter=DELIMITER_TYPE_SPACE,
                format=FORMAT_TYPE_STRUCTURED,
                frequency=Frequency(
                    interval_in_seconds=INTERVAL_IN_SECONDS_30,
                ),
                upload_file_prefix="logs",
                upload_file_suffix="ak",
            ),
            destination=connector,
            contract_id="P-1324",
            dataset_fields=[
                DatasetFieldID(dataset_field_id=1),
                DatasetFieldID(dataset_field_id=2),
                DatasetFieldID(dataset_field_id=3),
            ],
            notification_emails=["test@aka.mai"],
            group_id=123231,
            properties=[
                PropertyID(property_id=123123),
                PropertyID(property_id=123123),
            ],
            stream_name="TestStream",
        ),
    )


class TestDestinations:
    """Mirrors Go TestDs_Destinations — 14 connector types.

    Verifies that each connector serializes to the correct JSON destination
    dict when passed through CreateStream.  The test extracts the body kwarg
    from session.exec and checks the "destination" dict against expected keys.
    """

    @staticmethod
    def _run_destination_test(mock_session, mock_client, connector,
                               expected_fields):
        """Helper: run a CreateStream call and verify destination JSON."""
        req = _dest_base_request(connector)
        resp = make_mock_response(201, _CREATE_STREAM_BODY_ACTIVATE_NOW)
        mock_session.exec.return_value = (
            resp, json.loads(_CREATE_STREAM_BODY_ACTIVATE_NOW),
        )
        mock_client.create_stream(req)
        mock_session.exec.assert_called_once()
        _, kwargs = mock_session.exec.call_args
        body = kwargs["body"]
        actual_dest = body["destination"]
        # Verify all expected fields are present with correct values
        for key, val in expected_fields.items():
            assert key in actual_dest, (
                f"Missing key '{key}' in destination"
            )
            assert actual_dest[key] == val, (
                f"Mismatch on '{key}': want {val!r}, got {actual_dest[key]!r}"
            )

    def test_s3_connector(self, mock_session, mock_client):
        connector = S3Connector(
            path="testPath",
            display_name="testDisplayName",
            bucket="testBucket",
            region="testRegion",
            access_key="testAccessKey",
            secret_access_key="testSecretKey",
        )
        self._run_destination_test(mock_session, mock_client, connector, {
            "path": "testPath",
            "displayName": "testDisplayName",
            "bucket": "testBucket",
            "region": "testRegion",
            "accessKey": "testAccessKey",
            "secretAccessKey": "testSecretKey",
            "destinationType": "S3",
        })

    def test_azure_connector(self, mock_session, mock_client):
        connector = AzureConnector(
            account_name="testAccountName",
            access_key="testAccessKey",
            display_name="testDisplayName",
            container_name="testContainerName",
            path="testPath",
        )
        self._run_destination_test(mock_session, mock_client, connector, {
            "accountName": "testAccountName",
            "accessKey": "testAccessKey",
            "displayName": "testDisplayName",
            "containerName": "testContainerName",
            "path": "testPath",
            "destinationType": "AZURE",
        })

    def test_datadog_connector(self, mock_session, mock_client):
        connector = DatadogConnector(
            service="testService",
            auth_token="testAuthToken",
            display_name="testDisplayName",
            endpoint="testURL",
            source="testSource",
            tags="testTags",
            compress_logs=False,
        )
        self._run_destination_test(mock_session, mock_client, connector, {
            "service": "testService",
            "authToken": "testAuthToken",
            "displayName": "testDisplayName",
            "endpoint": "testURL",
            "source": "testSource",
            "tags": "testTags",
            "destinationType": "DATADOG",
            "compressLogs": False,
        })

    def test_splunk_connector(self, mock_session, mock_client):
        connector = SplunkConnector(
            display_name="testDisplayName",
            endpoint="testURL",
            event_collector_token="testEventCollector",
            compress_logs=True,
            custom_header_name="custom-header",
            custom_header_value="custom-header-value",
        )
        self._run_destination_test(mock_session, mock_client, connector, {
            "displayName": "testDisplayName",
            "endpoint": "testURL",
            "eventCollectorToken": "testEventCollector",
            "destinationType": "SPLUNK",
            "compressLogs": True,
            "customHeaderName": "custom-header",
            "customHeaderValue": "custom-header-value",
        })

    def test_gcs_connector(self, mock_session, mock_client):
        connector = GCSConnector(
            display_name="testDisplayName",
            bucket="testBucket",
            path="testPath",
            project_id="testProjectID",
            service_account_name="testServiceAccountName",
            private_key="testPrivateKey",
        )
        self._run_destination_test(mock_session, mock_client, connector, {
            "destinationType": "GCS",
            "displayName": "testDisplayName",
            "bucket": "testBucket",
            "path": "testPath",
            "projectId": "testProjectID",
            "serviceAccountName": "testServiceAccountName",
            "privateKey": "testPrivateKey",
        })

    def test_custom_https_connector(self, mock_session, mock_client):
        connector = CustomHTTPSConnector(
            authentication_type=AUTHENTICATION_TYPE_BASIC,
            display_name="testDisplayName",
            endpoint="testURL",
            user_name="testUserName",
            password="testPassword",
            compress_logs=True,
            custom_header_name="custom-header",
            custom_header_value="custom-header-value",
            content_type="application/json",
        )
        self._run_destination_test(mock_session, mock_client, connector, {
            "authenticationType": "BASIC",
            "displayName": "testDisplayName",
            "endpoint": "testURL",
            "userName": "testUserName",
            "password": "testPassword",
            "destinationType": "HTTPS",
            "compressLogs": True,
            "customHeaderName": "custom-header",
            "customHeaderValue": "custom-header-value",
            "contentType": "application/json",
        })

    def test_sumo_logic_connector(self, mock_session, mock_client):
        connector = SumoLogicConnector(
            display_name="testDisplayName",
            endpoint="testEndpoint",
            collector_code="testCollectorCode",
            compress_logs=True,
            custom_header_name="custom-header",
            custom_header_value="custom-header-value",
            content_type="application/json",
        )
        self._run_destination_test(mock_session, mock_client, connector, {
            "destinationType": "SUMO_LOGIC",
            "displayName": "testDisplayName",
            "endpoint": "testEndpoint",
            "collectorCode": "testCollectorCode",
            "compressLogs": True,
            "customHeaderName": "custom-header",
            "customHeaderValue": "custom-header-value",
            "contentType": "application/json",
        })

    def test_oracle_cloud_storage_connector(self, mock_session, mock_client):
        connector = OracleCloudStorageConnector(
            access_key="testAccessKey",
            display_name="testDisplayName",
            path="testPath",
            bucket="testBucket",
            region="testRegion",
            secret_access_key="testSecretAccessKey",
            namespace="testNamespace",
        )
        self._run_destination_test(mock_session, mock_client, connector, {
            "accessKey": "testAccessKey",
            "displayName": "testDisplayName",
            "path": "testPath",
            "bucket": "testBucket",
            "region": "testRegion",
            "secretAccessKey": "testSecretAccessKey",
            "destinationType": "Oracle_Cloud_Storage",
            "namespace": "testNamespace",
        })

    def test_loggly_connector(self, mock_session, mock_client):
        connector = LogglyConnector(
            display_name="testDisplayName",
            endpoint="testEndpoint",
            auth_token="testAuthToken",
            tags="testTags",
            content_type="testContentType",
            custom_header_name="testCustomHeaderName",
            custom_header_value="testCustomHeaderValue",
        )
        self._run_destination_test(mock_session, mock_client, connector, {
            "destinationType": "LOGGLY",
            "displayName": "testDisplayName",
            "endpoint": "testEndpoint",
            "authToken": "testAuthToken",
            "tags": "testTags",
            "contentType": "testContentType",
            "customHeaderName": "testCustomHeaderName",
            "customHeaderValue": "testCustomHeaderValue",
        })

    def test_new_relic_connector(self, mock_session, mock_client):
        connector = NewRelicConnector(
            display_name="testDisplayName",
            endpoint="testEndpoint",
            auth_token="testAuthToken",
            content_type="testContentType",
            custom_header_name="testCustomHeaderName",
            custom_header_value="testCustomHeaderValue",
        )
        self._run_destination_test(mock_session, mock_client, connector, {
            "destinationType": "NEWRELIC",
            "displayName": "testDisplayName",
            "endpoint": "testEndpoint",
            "authToken": "testAuthToken",
            "contentType": "testContentType",
            "customHeaderName": "testCustomHeaderName",
            "customHeaderValue": "testCustomHeaderValue",
        })

    def test_elasticsearch_connector(self, mock_session, mock_client):
        connector = ElasticsearchConnector(
            display_name="testDisplayName",
            endpoint="testEndpoint",
            index_name="testIndexName",
            user_name="testUserName",
            password="testPassword",
            content_type="testContentType",
            custom_header_name="testCustomHeaderName",
            custom_header_value="testCustomHeaderValue",
            tls_hostname="testTLSHostname",
            ca_cert="testCACert",
            client_cert="testClientCert",
            client_key="testClientKey",
        )
        self._run_destination_test(mock_session, mock_client, connector, {
            "destinationType": "ELASTICSEARCH",
            "displayName": "testDisplayName",
            "endpoint": "testEndpoint",
            "indexName": "testIndexName",
            "userName": "testUserName",
            "password": "testPassword",
            "contentType": "testContentType",
            "customHeaderName": "testCustomHeaderName",
            "customHeaderValue": "testCustomHeaderValue",
            "tlsHostname": "testTLSHostname",
            "caCert": "testCACert",
            "clientCert": "testClientCert",
            "clientKey": "testClientKey",
        })

    def test_s3_compatible_connector(self, mock_session, mock_client):
        connector = S3CompatibleConnector(
            path="testPath",
            display_name="testDisplayName",
            bucket="testBucket",
            region="testRegion",
            access_key="testAccessKey",
            secret_access_key="testSecretKey",
            endpoint="testEndpoint",
        )
        self._run_destination_test(mock_session, mock_client, connector, {
            "path": "testPath",
            "displayName": "testDisplayName",
            "bucket": "testBucket",
            "region": "testRegion",
            "accessKey": "testAccessKey",
            "secretAccessKey": "testSecretKey",
            "destinationType": "S3_COMPATIBLE",
            "endpoint": "testEndpoint",
        })

    def test_dynatrace_connector(self, mock_session, mock_client):
        connector = DynatraceConnector(
            display_name="testDisplayName",
            endpoint="testEndpoint",
            auth_token="testAuthToken",
            custom_header_name="testCustomHeaderName",
            custom_header_value="testCustomHeaderValue",
        )
        self._run_destination_test(mock_session, mock_client, connector, {
            "destinationType": "DYNATRACE",
            "displayName": "testDisplayName",
            "endpoint": "testEndpoint",
            "authToken": "testAuthToken",
            "customHeaderName": "testCustomHeaderName",
            "customHeaderValue": "testCustomHeaderValue",
        })

    def test_traffic_peak_connector(self, mock_session, mock_client):
        connector = TrafficPeakConnector(
            authentication_type=AUTHENTICATION_TYPE_BASIC,
            display_name="testDisplayName",
            endpoint="testURL",
            user_name="testUserName",
            password="testPassword",
            compress_logs=True,
            custom_header_name="custom-header",
            custom_header_value="custom-header-value",
            content_type="application/json",
        )
        self._run_destination_test(mock_session, mock_client, connector, {
            "authenticationType": "BASIC",
            "displayName": "testDisplayName",
            "endpoint": "testURL",
            "userName": "testUserName",
            "password": "testPassword",
            "destinationType": "TRAFFICPEAK",
            "compressLogs": True,
            "customHeaderName": "custom-header",
            "customHeaderValue": "custom-header-value",
            "contentType": "application/json",
        })


# ===================================================================
# TestSetDestinationTypes — mirrors stream_test.go lines 1643-1709
# ===================================================================


class TestSetDestinationTypes:
    """Verifies that Client.create_stream calls set_destination_type()
    on the connector before serialisation.

    Mirrors Go TestDs_setDestinationTypes with mockConnector.
    """

    def test_set_destination_type_called(self, mock_session):
        # Create a mock connector that tracks calls
        mock_connector = Mock()
        mock_connector.set_destination_type = Mock()
        mock_connector.validate = Mock(return_value=None)
        mock_connector.destination_type = "MOCK_TYPE"
        mock_connector.display_name = "mock"
        mock_connector.bucket = "mock"
        mock_connector.path = "mock"
        mock_connector.region = "mock"
        mock_connector.access_key = "mock"
        mock_connector.secret_access_key = "mock"

        req = CreateStreamRequest(
            activate=True,
            stream_configuration=StreamConfiguration(
                delivery_configuration=DeliveryConfiguration(
                    delimiter=DELIMITER_TYPE_SPACE,
                    format=FORMAT_TYPE_STRUCTURED,
                    frequency=Frequency(
                        interval_in_seconds=INTERVAL_IN_SECONDS_30,
                    ),
                    upload_file_prefix="logs",
                    upload_file_suffix="ak",
                ),
                destination=mock_connector,
                contract_id="P-1324",
                dataset_fields=[DatasetFieldID(dataset_field_id=1)],
                notification_emails=["test@aka.mai"],
                group_id=123231,
                properties=[PropertyID(property_id=123123)],
                stream_name="TestStream",
            ),
        )
        resp = make_mock_response(201, _CREATE_STREAM_BODY_ACTIVATE_NOW)
        mock_session.exec.return_value = (
            resp, json.loads(_CREATE_STREAM_BODY_ACTIVATE_NOW),
        )
        client = Client(mock_session)
        try:
            client.create_stream(req)
        except (ValueError, AttributeError, TypeError):
            pass  # Serialisation may fail on mock — that is OK
        # The key assertion: set_destination_type was called
        mock_connector.set_destination_type.assert_called_once()


# ===================================================================
# TestListStreams — mirrors stream_test.go TestDs_ListStreams
#                   (lines 1711-2031)
# ===================================================================

_LIST_STREAMS_BODY_OK = """[
   {
      "contractId":"1-ABC",
      "createdBy":"abc",
      "createdDate":"2022-04-21T17:02:58Z",
      "groupId":123,
      "latestVersion":15,
      "modifiedBy":"abc",
      "modifiedDate":"2022-12-26T17:00:03Z",
      "productId":"API_Acceleration",
      "properties":[
         {
            "propertyId":123,
            "propertyName":"example.com"
         },
         {
            "propertyId":123,
            "propertyName":"abc.media"
         }
      ],
      "streamId":123,
      "streamName":"test-stream-1",
      "streamStatus":"ACTIVATED",
      "streamVersion":15
   },
   {
      "contractId":"1-123",
      "createdBy":"abc",
      "createdDate":"2023-01-03T12:44:15Z",
      "groupId":123,
      "latestVersion":1,
      "modifiedBy":"abc",
      "modifiedDate":"2023-01-03T12:44:15Z",
      "productId":"Download_Delivery",
      "properties":[
         {
            "propertyId":123,
            "propertyName":"abc"
         }
      ],
      "streamId":123,
      "streamName":"test-stream-2",
      "streamStatus":"INACTIVE",
      "streamVersion":1
   }
]"""

_LIST_STREAMS_BODY_GROUP = """[
  {
        "contractId": "1-123",
        "createdBy": "abc",
        "createdDate": "2022-07-25T08:36:32Z",
        "groupId": 123,
        "latestVersion": 2,
        "modifiedBy": "abc",
        "modifiedDate": "2022-12-26T20:00:02Z",
        "productId": "Object_Delivery",
        "properties": [
            {
                "propertyId": 123,
                "propertyName": "abc.net"
            }
        ],
        "streamId": 123,
        "streamName": "test-stream",
        "streamStatus": "ACTIVATED",
        "streamVersion": 2
    }
]"""

_LIST_STREAMS_BODY_INTEGRATION = """[
   {
      "contractId":"PM-123",
      "createdBy":"pmuser",
      "createdDate":"2024-01-15T10:30:00Z",
      "groupId":456,
      "latestVersion":3,
      "modifiedBy":"pmuser",
      "modifiedDate":"2024-01-16T14:20:00Z",
      "productId":"Premium_Delivery",
      "properties":[
         {
            "propertyId":789,
            "propertyName":"premium.example.com"
         }
      ],
      "streamId":555,
      "streamName":"premium-stream",
      "streamStatus":"ACTIVATED",
      "streamVersion":3,
      "integrationType":"PM_DEPENDENT",
      "samplingPercentage":75
   },
   {
      "contractId":"DS-456",
      "createdBy":"dsuser",
      "createdDate":"2024-02-01T08:00:00Z",
      "groupId":789,
      "latestVersion":1,
      "modifiedBy":"dsuser",
      "modifiedDate":"2024-02-01T08:00:00Z",
      "productId":"Data_Stream",
      "properties":[
         {
            "propertyId":999,
            "propertyName":"datastream.example.com"
         }
      ],
      "streamId":777,
      "streamName":"ds-managed-stream",
      "streamStatus":"INACTIVE",
      "streamVersion":1,
      "integrationType":"DS_MANAGED",
      "samplingPercentage":100
   }
]"""

_LIST_STREAMS_ERROR_400 = """{
\t"type": "bad-request",
\t"title": "Bad Request",
\t"detail": "bad request",
\t"instance": "82b67b97-d98d-4bee-ac1e-ef6eaf7cac82",
\t"statusCode": 400,
\t"errors": [
\t\t{
\t\t\t"type": "bad-request",
\t\t\t"title": "Bad Request",
\t\t\t"detail": "Stream does not exist. Please provide valid stream."
\t\t}
\t]
}"""


class TestListStreams:
    """Mirrors Go TestDs_ListStreams — 4 cases."""

    def test_200_ok(self, mock_session, mock_client):
        result = _call_success(
            mock_session, mock_client, "list_streams",
            ListStreamsRequest(), 200, _LIST_STREAMS_BODY_OK,
        )
        assert isinstance(result, list)
        assert len(result) == 2
        # First stream
        assert result[0].stream_name == "test-stream-1"
        assert result[0].stream_status == STREAM_STATUS_ACTIVATED
        assert result[0].product_id == "API_Acceleration"
        assert result[0].contract_id == "1-ABC"
        assert result[0].stream_id == 123
        assert result[0].latest_version == 15
        assert len(result[0].properties) == 2
        assert result[0].properties[0].property_name == "example.com"
        # Second stream
        assert result[1].stream_name == "test-stream-2"
        assert result[1].stream_status == STREAM_STATUS_INACTIVE
        assert result[1].product_id == "Download_Delivery"

    def test_200_ok_with_group_id(self, mock_session, mock_client):
        resp = make_mock_response(200, _LIST_STREAMS_BODY_GROUP)
        mock_session.exec.return_value = (
            resp, json.loads(_LIST_STREAMS_BODY_GROUP),
        )
        result = mock_client.list_streams(
            ListStreamsRequest(group_id=1234),
        )
        # Check that query param groupId was passed
        _, kwargs = mock_session.exec.call_args
        params = kwargs.get("params")
        assert params is not None
        assert params.get("groupId") == "1234"
        assert len(result) == 1
        assert result[0].product_id == "Object_Delivery"
        assert result[0].stream_name == "test-stream"
        assert result[0].stream_status == STREAM_STATUS_ACTIVATED

    def test_200_ok_with_integration_type(self, mock_session, mock_client):
        result = _call_success(
            mock_session, mock_client, "list_streams",
            ListStreamsRequest(), 200, _LIST_STREAMS_BODY_INTEGRATION,
        )
        assert len(result) == 2
        assert result[0].integration_type == "PM_DEPENDENT"
        assert result[0].sampling_percentage == 75
        assert result[0].stream_name == "premium-stream"
        assert result[1].integration_type == "DS_MANAGED"
        assert result[1].sampling_percentage == 100
        assert result[1].stream_name == "ds-managed-stream"

    def test_400_bad_request(self, mock_session, mock_client):
        _assert_api_error(
            mock_client, "list_streams",
            ListStreamsRequest(),
            mock_session, 400, _LIST_STREAMS_ERROR_400,
            ErrListStreams,
            Error(
                type="bad-request", title="Bad Request",
                detail="bad request",
                instance="82b67b97-d98d-4bee-ac1e-ef6eaf7cac82",
                status_code=400,
                errors=[RequestErrors(
                    type="bad-request", title="Bad Request",
                    detail="Stream does not exist. Please provide valid stream.",
                )],
            ),
        )


# ===================================================================
# TestActivateStream — mirrors stream_activation_test.go
#                      TestDs_ActivateStream (lines 14-203)
# ===================================================================

_ACTIVATE_STREAM_BODY_OK = """
{
    "contractId": "P-1324", 
    "createdBy": "sample_username", 
    "createdDate": "2022-11-04T00:49:45Z", 
    "collectMidgress": true,
    "datasetFields": [
        {
            "datasetFieldId":1000,
            "datasetFieldName":"dataset_field_name_1",
            "datasetFieldJsonKey":"dataset_field_json_key_1"
        },
        {
            "datasetFieldId":1002,
            "datasetFieldName":"dataset_field_name_2",
            "datasetFieldJsonKey":"dataset_field_json_key_2"
        },
        {
            "datasetFieldId":1082,
            "datasetFieldName":"dataset_field_name_3",
            "datasetFieldJsonKey":"dataset_field_json_key_3"
        }
    ], 
    "deliveryConfiguration": {
        "fieldDelimiter": "SPACE", 
        "format": "STRUCTURED", 
        "frequency": {
            "intervalInSeconds": 30
        }, 
        "uploadFilePrefix": "ak", 
        "uploadFileSuffix": "ds"
    }, 
    "destination": {
        "bucket": "sample_bucket", 
        "compressLogs": true, 
        "destinationType": "S3", 
        "displayName": "sample_display_name", 
        "path": "/sample_path", 
        "region": "us-east-1"
    },
    "groupId": 1234, 
    "latestVersion": 2, 
    "modifiedBy": "sample_username2", 
    "modifiedDate": "2022-11-04T02:14:29Z", 
    "notificationEmails": [
        "sample_username@akamai.com"
    ], 
    "productId": "Adaptive_Media_Delivery", 
    "properties": [
        {
            "propertyId": 1234, 
            "propertyName": "sample.com"
        }
    ], 
    "streamId": 3, 
    "streamName": "ds2-sample-name", 
    "streamStatus": "ACTIVATING", 
    "streamVersion": 2
}
"""

_ACTIVATE_STREAM_ERROR_400 = """
{
\t"type": "bad-request",
\t"title": "Bad Request",
\t"detail": "",
\t"instance": "df22bc0f-ca8d-4bdb-afea-ffdeef819e22",
\t"statusCode": 400,
\t"errors": [
\t\t{
\t\t\t"type": "bad-request",
\t\t\t"title": "Bad Request",
\t\t\t"detail": "Stream does not exist. Please provide valid stream."
\t\t}
\t]
}
"""


class TestActivateStream:
    """Mirrors Go TestDs_ActivateStream — 3 cases."""

    def test_200_ok(self, mock_session, mock_client):
        result = _call_success(
            mock_session, mock_client, "activate_stream",
            ActivateStreamRequest(stream_id=3), 200,
            _ACTIVATE_STREAM_BODY_OK.strip(),
        )
        assert result.stream_status == STREAM_STATUS_ACTIVATING
        assert result.collect_midgress is True
        assert result.contract_id == "P-1324"
        assert result.created_by == "sample_username"
        assert result.created_date == "2022-11-04T00:49:45Z"
        assert len(result.dataset_fields) == 3
        assert result.dataset_fields[0].dataset_field_id == 1000
        assert result.dataset_fields[0].dataset_field_name == "dataset_field_name_1"
        assert result.dataset_fields[0].dataset_field_json_key == "dataset_field_json_key_1"
        assert result.dataset_fields[1].dataset_field_id == 1002
        assert result.dataset_fields[2].dataset_field_id == 1082
        assert result.delivery_configuration.delimiter == DELIMITER_TYPE_SPACE
        assert result.delivery_configuration.format == FORMAT_TYPE_STRUCTURED
        assert result.delivery_configuration.frequency.interval_in_seconds == INTERVAL_IN_SECONDS_30
        assert result.delivery_configuration.upload_file_prefix == "ak"
        assert result.delivery_configuration.upload_file_suffix == "ds"
        assert result.destination.bucket == "sample_bucket"
        assert result.destination.compress_logs is True
        assert result.destination.destination_type == DESTINATION_TYPE_S3
        assert result.destination.display_name == "sample_display_name"
        assert result.destination.path == "/sample_path"
        assert result.destination.region == "us-east-1"
        assert result.group_id == 1234
        assert result.latest_version == 2
        assert result.modified_by == "sample_username2"
        assert result.modified_date == "2022-11-04T02:14:29Z"
        assert result.notification_emails == ["sample_username@akamai.com"]
        assert result.product_id == "Adaptive_Media_Delivery"
        assert len(result.properties) == 1
        assert result.properties[0].property_id == 1234
        assert result.properties[0].property_name == "sample.com"
        assert result.stream_id == 3
        assert result.stream_name == "ds2-sample-name"
        assert result.stream_version == 2

    def test_validation_error(self, mock_session, mock_client):
        _assert_validation_error(
            mock_client, "activate_stream",
            ActivateStreamRequest(),
            ErrActivateStream,
        )
        mock_session.exec.assert_not_called()

    def test_400_bad_request(self, mock_session, mock_client):
        _assert_api_error(
            mock_client, "activate_stream",
            ActivateStreamRequest(stream_id=123),
            mock_session, 400, _ACTIVATE_STREAM_ERROR_400.strip(),
            ErrActivateStream,
            Error(
                type="bad-request", title="Bad Request",
                detail="",
                instance="df22bc0f-ca8d-4bdb-afea-ffdeef819e22",
                status_code=400,
                errors=[RequestErrors(
                    type="bad-request", title="Bad Request",
                    detail="Stream does not exist. Please provide valid stream.",
                )],
            ),
        )


# ===================================================================
# TestDeactivateStream — mirrors stream_activation_test.go
#                        TestDs_DeactivateStream (lines 205-394)
# ===================================================================

_DEACTIVATE_STREAM_BODY_OK = """
{
    "contractId": "P-1324", 
    "createdBy": "sample_username", 
    "createdDate": "2022-11-04T00:49:45Z", 
    "collectMidgress": true,
    "datasetFields": [
        {
            "datasetFieldId":1000,
            "datasetFieldName":"dataset_field_name_1",
            "datasetFieldJsonKey":"dataset_field_json_key_1"
        },
        {
            "datasetFieldId":1002,
            "datasetFieldName":"dataset_field_name_2",
            "datasetFieldJsonKey":"dataset_field_json_key_2"
        },
        {
            "datasetFieldId":1082,
            "datasetFieldName":"dataset_field_name_3",
            "datasetFieldJsonKey":"dataset_field_json_key_3"
        }
    ], 
    "deliveryConfiguration": {
        "fieldDelimiter": "SPACE", 
        "format": "STRUCTURED", 
        "frequency": {
            "intervalInSeconds": 30
        }, 
        "uploadFilePrefix": "ak", 
        "uploadFileSuffix": "ds"
    }, 
    "destination": {
        "bucket": "sample_bucket", 
        "compressLogs": true, 
        "destinationType": "S3", 
        "displayName": "sample_display_name", 
        "path": "/sample_path", 
        "region": "us-east-1"
    },
    "groupId": 1234, 
    "latestVersion": 2, 
    "modifiedBy": "sample_username2", 
    "modifiedDate": "2022-11-04T02:14:29Z", 
    "notificationEmails": [
        "sample_username@akamai.com"
    ], 
    "productId": "Adaptive_Media_Delivery", 
    "properties": [
        {
            "propertyId": 1234, 
            "propertyName": "sample.com"
        }
    ], 
    "streamId": 3, 
    "streamName": "ds2-sample-name", 
    "streamStatus": "DEACTIVATING", 
    "streamVersion": 2
}
"""

_DEACTIVATE_STREAM_ERROR_400 = """
{
\t"type": "bad-request",
\t"title": "Bad Request",
\t"detail": "",
\t"instance": "df22bc0f-ca8d-4bdb-afea-ffdeef819e22",
\t"statusCode": 400,
\t"errors": [
\t\t{
\t\t\t"type": "bad-request",
\t\t\t"title": "Bad Request",
\t\t\t"detail": "Stream does not exist. Please provide valid stream."
\t\t}
\t]
}
"""


class TestDeactivateStream:
    """Mirrors Go TestDs_DeactivateStream — 3 cases."""

    def test_200_ok(self, mock_session, mock_client):
        result = _call_success(
            mock_session, mock_client, "deactivate_stream",
            DeactivateStreamRequest(stream_id=3), 200,
            _DEACTIVATE_STREAM_BODY_OK.strip(),
        )
        assert result.stream_status == STREAM_STATUS_DEACTIVATING
        assert result.collect_midgress is True
        assert result.contract_id == "P-1324"
        assert result.created_by == "sample_username"
        assert result.created_date == "2022-11-04T00:49:45Z"
        assert len(result.dataset_fields) == 3
        assert result.dataset_fields[0].dataset_field_id == 1000
        assert result.dataset_fields[1].dataset_field_id == 1002
        assert result.dataset_fields[2].dataset_field_id == 1082
        assert result.delivery_configuration.delimiter == DELIMITER_TYPE_SPACE
        assert result.delivery_configuration.format == FORMAT_TYPE_STRUCTURED
        assert result.delivery_configuration.frequency.interval_in_seconds == INTERVAL_IN_SECONDS_30
        assert result.delivery_configuration.upload_file_prefix == "ak"
        assert result.delivery_configuration.upload_file_suffix == "ds"
        assert result.destination.bucket == "sample_bucket"
        assert result.destination.compress_logs is True
        assert result.destination.destination_type == DESTINATION_TYPE_S3
        assert result.destination.display_name == "sample_display_name"
        assert result.destination.path == "/sample_path"
        assert result.destination.region == "us-east-1"
        assert result.group_id == 1234
        assert result.latest_version == 2
        assert result.modified_by == "sample_username2"
        assert result.modified_date == "2022-11-04T02:14:29Z"
        assert result.notification_emails == ["sample_username@akamai.com"]
        assert result.product_id == "Adaptive_Media_Delivery"
        assert len(result.properties) == 1
        assert result.properties[0].property_id == 1234
        assert result.properties[0].property_name == "sample.com"
        assert result.stream_id == 3
        assert result.stream_name == "ds2-sample-name"
        assert result.stream_version == 2

    def test_validation_error(self, mock_session, mock_client):
        _assert_validation_error(
            mock_client, "deactivate_stream",
            DeactivateStreamRequest(),
            ErrDeactivateStream,
        )
        mock_session.exec.assert_not_called()

    def test_400_bad_request(self, mock_session, mock_client):
        _assert_api_error(
            mock_client, "deactivate_stream",
            DeactivateStreamRequest(stream_id=123),
            mock_session, 400, _DEACTIVATE_STREAM_ERROR_400.strip(),
            ErrDeactivateStream,
            Error(
                type="bad-request", title="Bad Request",
                detail="",
                instance="df22bc0f-ca8d-4bdb-afea-ffdeef819e22",
                status_code=400,
                errors=[RequestErrors(
                    type="bad-request", title="Bad Request",
                    detail="Stream does not exist. Please provide valid stream.",
                )],
            ),
        )


# ===================================================================
# TestGetActivationHistory — mirrors stream_activation_test.go
#                            TestDs_GetActivationHistory (lines 396-503)
# ===================================================================

_GET_ACTIVATION_HISTORY_BODY_OK = """
[
    {
        "streamId": 3,
        "streamVersion": 2,
        "modifiedBy": "user1",
        "modifiedDate": "16-01-2020 11:07:12 GMT",
        "status": "DEACTIVATED"
    },
    {
        "streamId": 3,
        "streamVersion": 2,
        "modifiedBy": "user2",
        "modifiedDate": "16-01-2020 09:31:02 GMT",
        "status": "ACTIVATED"
    }
]
"""

_GET_ACTIVATION_HISTORY_ERROR_400 = """
{
\t"type": "bad-request",
\t"title": "Bad Request",
\t"detail": "",
\t"instance": "df22bc0f-ca8d-4bdb-afea-ffdeef819e22",
\t"statusCode": 400,
\t"errors": [
\t\t{
\t\t\t"type": "bad-request",
\t\t\t"title": "Bad Request",
\t\t\t"detail": "Stream does not exist. Please provide valid stream."
\t\t}
\t]
}
"""


class TestGetActivationHistory:
    """Mirrors Go TestDs_GetActivationHistory — 3 cases."""

    def test_200_ok(self, mock_session, mock_client):
        result = _call_success(
            mock_session, mock_client, "get_activation_history",
            GetActivationHistoryRequest(stream_id=3), 200,
            _GET_ACTIVATION_HISTORY_BODY_OK.strip(),
        )
        assert isinstance(result, list)
        assert len(result) == 2
        # First entry
        assert result[0].stream_id == 3
        assert result[0].stream_version == 2
        assert result[0].modified_by == "user1"
        assert result[0].modified_date == "16-01-2020 11:07:12 GMT"
        assert result[0].status == STREAM_STATUS_DEACTIVATED
        # Second entry
        assert result[1].stream_id == 3
        assert result[1].stream_version == 2
        assert result[1].modified_by == "user2"
        assert result[1].modified_date == "16-01-2020 09:31:02 GMT"
        assert result[1].status == STREAM_STATUS_ACTIVATED

    def test_validation_error(self, mock_session, mock_client):
        _assert_validation_error(
            mock_client, "get_activation_history",
            GetActivationHistoryRequest(),
            ErrGetActivationHistory,
        )
        mock_session.exec.assert_not_called()

    def test_400_bad_request(self, mock_session, mock_client):
        _assert_api_error(
            mock_client, "get_activation_history",
            GetActivationHistoryRequest(stream_id=123),
            mock_session, 400, _GET_ACTIVATION_HISTORY_ERROR_400.strip(),
            ErrGetActivationHistory,
            Error(
                type="bad-request", title="Bad Request",
                detail="",
                instance="df22bc0f-ca8d-4bdb-afea-ffdeef819e22",
                status_code=400,
                errors=[RequestErrors(
                    type="bad-request", title="Bad Request",
                    detail="Stream does not exist. Please provide valid stream.",
                )],
            ),
        )


# ===================================================================
# TestGetProperties — mirrors properties_test.go
#                     TestDs_GetProperties (lines 15-178)
# ===================================================================

_GET_PROPERTIES_BODY_OK = """
{
    "groupId": 12345,
    "properties": [
    {
        "contractId": "1-7KLGU",
        "propertyId": 382631,
        "propertyName": "customp.akamai.com",
        "productId": "Ion_Standard",
        "productName": "Ion Standard",
        "hostnames": [
            "customp.akamaize.net",
            "customp.akamaized-staging.net"
        ]
    },
    {
        "contractId": "1-7KLGU",
        "propertyId": 347459,
        "propertyName": "example.com",
        "productId": "Dynamic_Site_Accelerator",
        "productName": "Dynamic Site Accelerator",
        "hostnames": [
            "example.edgekey.net"
        ]
    }
]
}
"""

_GET_PROPERTIES_ERROR_400 = """
{
\t"type": "bad-request",
\t"title": "Bad Request",
\t"detail": "",
\t"instance": "baf2671f-7b3a-406d-9dd8-63ef20a01296",
\t"statusCode": 400,
\t"errors": [
\t\t{
\t\t\t"type": "bad-request",
\t\t\t"title": "Bad Request",
\t\t\t"detail": "Invalid Product Name"
\t\t}
\t]
}
"""

_GET_PROPERTIES_ERROR_403 = """
{
\t"type": "forbidden",
\t"title": "Forbidden",
\t"detail": "",
\t"instance": "28eb43a8-97ae-4c57-98aa-258081582b92",
\t"statusCode": 403,
\t"errors": [
\t\t{
\t\t\t"type": "forbidden",
\t\t\t"title": "Forbidden",
\t\t\t"detail": "User is not having access for the group. Access denied, please contact support."
\t\t}
\t]
}
"""


class TestGetProperties:
    """Mirrors Go TestDs_GetProperties — 4 cases."""

    def test_200_ok(self, mock_session, mock_client):
        result = _call_success(
            mock_session, mock_client, "get_properties",
            GetPropertiesRequest(group_id=12345), 200,
            _GET_PROPERTIES_BODY_OK.strip(),
        )
        assert result.group_id == 12345
        assert len(result.properties) == 2
        # First property
        prop0 = result.properties[0]
        assert prop0.contract_id == "1-7KLGU"
        assert prop0.property_id == 382631
        assert prop0.property_name == "customp.akamai.com"
        assert prop0.product_id == "Ion_Standard"
        assert prop0.product_name == "Ion Standard"
        assert prop0.hostnames == [
            "customp.akamaize.net",
            "customp.akamaized-staging.net",
        ]
        # Second property
        prop1 = result.properties[1]
        assert prop1.contract_id == "1-7KLGU"
        assert prop1.property_id == 347459
        assert prop1.property_name == "example.com"
        assert prop1.product_id == "Dynamic_Site_Accelerator"
        assert prop1.product_name == "Dynamic Site Accelerator"
        assert prop1.hostnames == ["example.edgekey.net"]

    def test_validation_error(self, mock_session, mock_client):
        _assert_validation_error(
            mock_client, "get_properties",
            GetPropertiesRequest(),
            ErrGetProperties,
        )
        mock_session.exec.assert_not_called()

    def test_400_bad_request(self, mock_session, mock_client):
        _assert_api_error(
            mock_client, "get_properties",
            GetPropertiesRequest(group_id=12345),
            mock_session, 400, _GET_PROPERTIES_ERROR_400.strip(),
            ErrGetProperties,
            Error(
                type="bad-request", title="Bad Request",
                detail="",
                instance="baf2671f-7b3a-406d-9dd8-63ef20a01296",
                status_code=400,
                errors=[RequestErrors(
                    type="bad-request", title="Bad Request",
                    detail="Invalid Product Name",
                )],
            ),
        )

    def test_403_forbidden(self, mock_session, mock_client):
        _assert_api_error(
            mock_client, "get_properties",
            GetPropertiesRequest(group_id=12345),
            mock_session, 403, _GET_PROPERTIES_ERROR_403.strip(),
            ErrGetProperties,
            Error(
                type="forbidden", title="Forbidden",
                detail="",
                instance="28eb43a8-97ae-4c57-98aa-258081582b92",
                status_code=403,
                errors=[RequestErrors(
                    type="forbidden", title="Forbidden",
                    detail="User is not having access for the group. Access denied, please contact support.",
                )],
            ),
        )


# ===================================================================
# TestGetDatasetFields — mirrors properties_test.go
#                        TestDs_GetDatasetFields (lines 180-304)
# ===================================================================

_GET_DATASET_FIELDS_BODY_OK = """
{
    "datasetFields": [
        {
            "datasetFieldDescription": "datasetFieldDescription_1",
            "datasetFieldGroup": "datasetFieldGroup_1",
            "datasetFieldId": 1000,
            "datasetFieldJsonKey": "datasetFieldJsonKey_1",
            "datasetFieldName": "datasetFieldName_1"
        },
        {
            "datasetFieldDescription": "datasetFieldDescription_2",
            "datasetFieldGroup": "datasetFieldGroup_2",
            "datasetFieldId": 1001,
            "datasetFieldJsonKey": "datasetFieldJsonKey_2",
            "datasetFieldName": "datasetFieldName_2"
        },
        {
            "datasetFieldDescription": "datasetFieldDescription_3",
            "datasetFieldGroup": "datasetFieldGroup_3",
            "datasetFieldId": 1002,
            "datasetFieldJsonKey": "datasetFieldJsonKey_3",
            "datasetFieldName": "datasetFieldName_3"
        }
    ]
}
"""

_GET_DATASET_FIELDS_ERROR_400 = """
{
    "errors": [
        {
            "detail": "Invalid product ID. Provide the correct product ID and try again.", 
            "problemId": "800a7291-c694-434a-99b7-8940d788239a", 
            "title": "Bad Request", 
            "type": "bad-request"
        }
    ], 
    "instance": "6e067164-4a61-429a-abaf-87452fd47036", 
    "problemId": "6e067164-4a61-429a-abaf-87452fd47036", 
    "status": 400, 
    "title": "Bad Request", 
    "type": "bad-request"
}
"""


class TestGetDatasetFields:
    """Mirrors Go TestDs_GetDatasetFields — 2 cases."""

    def test_200_ok(self, mock_session, mock_client):
        result = _call_success(
            mock_session, mock_client, "get_dataset_fields",
            GetDatasetFieldsRequest(product_id=None), 200,
            _GET_DATASET_FIELDS_BODY_OK.strip(),
        )
        assert len(result.dataset_fields) == 3
        # First field
        f0 = result.dataset_fields[0]
        assert f0.dataset_field_id == 1000
        assert f0.dataset_field_name == "datasetFieldName_1"
        assert f0.dataset_field_json_key == "datasetFieldJsonKey_1"
        assert f0.dataset_field_group == "datasetFieldGroup_1"
        assert f0.dataset_field_description == "datasetFieldDescription_1"
        # Second field
        f1 = result.dataset_fields[1]
        assert f1.dataset_field_id == 1001
        assert f1.dataset_field_name == "datasetFieldName_2"
        assert f1.dataset_field_json_key == "datasetFieldJsonKey_2"
        assert f1.dataset_field_group == "datasetFieldGroup_2"
        assert f1.dataset_field_description == "datasetFieldDescription_2"
        # Third field
        f2 = result.dataset_fields[2]
        assert f2.dataset_field_id == 1002
        assert f2.dataset_field_name == "datasetFieldName_3"
        assert f2.dataset_field_json_key == "datasetFieldJsonKey_3"
        assert f2.dataset_field_group == "datasetFieldGroup_3"
        assert f2.dataset_field_description == "datasetFieldDescription_3"

    def test_invalid_product_id(self, mock_session, mock_client):
        _assert_api_error(
            mock_client, "get_dataset_fields",
            GetDatasetFieldsRequest(product_id="INVALID_PROD_ID"),
            mock_session, 400, _GET_DATASET_FIELDS_ERROR_400.strip(),
            ErrGetDatasetFields,
            Error(
                type="bad-request", title="Bad Request",
                detail="",
                instance="6e067164-4a61-429a-abaf-87452fd47036",
                status_code=400,
                errors=[RequestErrors(
                    type="bad-request", title="Bad Request",
                    detail="Invalid product ID. Provide the correct product ID and try again.",
                )],
            ),
        )
