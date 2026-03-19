# pylint: disable=missing-function-docstring,missing-class-docstring,too-many-lines,line-too-long,too-few-public-methods
"""Unit tests for the API Definitions service client.

Mirrors all test scenarios from Go pkg/apidefinitions/*_test.go files.
Each test function maps to a corresponding Go test function.
All responseBody and responseHeaders values are VERBATIM from Go tests.
"""

import json

import pytest
from akamai.edgegrid.apidefinitions.apidefinitions import Client
from akamai.edgegrid.apidefinitions.models import (
    GetEndpointRequest,
    ListEndpointsRequest,
    RegisterEndpointRequest,
    RegisterEndpointFromFileRequest,
    ShowEndpointRequest,
    HideEndpointRequest,
    DeleteEndpointRequest,
    SecurityScheme,
    SecuritySchemeDetail,
    APIParameterRestriction,
    LengthRestriction,
    ArrayRestriction,
    APIResourceMethod,
    APIParameter,
    AkamaiSecurityRestrictions,
    APIResource,
    APIVersionInfo,
    ListEndpointVersionsRequest,
    GetEndpointVersionRequest,
    CloneEndpointVersionRequest,
    DeleteEndpointVersionRequest,
    UpdateEndpointVersionRequest,
    UpdateEndpointVersionRequestBody,
    VerifyVersionRequest,
    VerifyVersionRequestBody,
    ActivateVersionRequest,
    ActivationRequestBody,
    DeactivateVersionRequest,
    RestrictionsBool,
    ACTIVATION_NETWORK_STAGING,
    ACTIVATION_NETWORK_PRODUCTION,
    IMPORT_FILE_SOURCE_URL,
    IMPORT_FILE_SOURCE_BASE64,
)
from akamai.edgegrid.apidefinitions.errors import (
    Error as APIDefinitionsError,
)
from akamai.edgegrid.apidefinitions.validation import (
    validate_list_endpoints_request,
    validate_security_scheme,
    validate_api_parameter_restriction,
    validate_api_resource_method,
    validate_akamai_security_restrictions,
    validate_register_endpoint_request,
    validate_api_resource_methods,
    validate_register_endpoint_from_file_request,
)
from akamai.edgegrid.errors import ErrStructValidation

# conftest fixtures (mock_session, mock_client) are auto-discovered.
# conftest helpers imported explicitly where needed.
from akamai.edgegrid.apidefinitions.test.conftest import (
    mock_response,
    load_fixture,
)


# ======================================================================
# TestClient -- mirrors Go TestClient (apidefinitions_test.go)
# ======================================================================


class TestClient:
    """Tests for Client constructor -- mirrors Go TestClient."""

    def test_client_no_options(self, mock_session):
        client = Client(mock_session)
        assert client is not None
        assert client._session is mock_session  # pylint: disable=protected-access


# ======================================================================
# TestNewError -- mirrors Go TestNewError (errors_test.go)
# ======================================================================


class TestNewError:
    """Tests for Error.from_response -- mirrors Go TestNewError."""

    def test_valid_response_500(self):
        resp = mock_response(500, '{"type":"a","title":"b","detail":"c"}')
        result = APIDefinitionsError.from_response(resp)
        expected = APIDefinitionsError(
            type="a",
            title="b",
            detail="c",
            status=500,
        )
        assert result.is_equivalent(expected)

    def test_invalid_response_body(self):
        resp = mock_response(500, "test")
        result = APIDefinitionsError.from_response(resp)
        assert result.status == 500
        assert result.title == "Failed to unmarshal error body"


# ======================================================================
# TestGetEndpoint -- mirrors Go TestGetEndpoint (endpoints_test.go)
# ======================================================================


class TestGetEndpoint:
    """Tests for Client.get_endpoint -- mirrors Go TestGetEndpoint."""

    def test_200_ok(self, mock_client):
        response_body = '{"createdBy":"user","createDate":"2022-08-18T08:51:22+0000","updateDate":"2022-08-18T09:45:55+0000","updatedBy":"user2","apiEndPointId":3,"apiEndPointName":"Test","description":"Test desc","basePath":"/test","consumeType":"any","apiEndPointScheme":null,"apiEndPointVersion":999,"contractId":"TestContract","groupId":111,"versionNumber":10,"clonedFromVersion":222,"apiEndPointLocked":false,"stagingVersion":{"versionNumber":10,"status":"DEACTIVATED","timestamp":"2022-07-06T09:12:04+0000","lastError":null},"productionVersion":{"versionNumber":null,"status":null,"timestamp":null,"lastError":null},"protectedByApiKey":false,"apiGatewayEnabled":true,"apiEndPointHosts":["test.com"],"apiCategoryIds":[456],"source":null,"apiVersionInfo":{"location":"BASE_PATH","parameterName":null,"value":null},"positiveConstrainsEnabled":true,"versionHidden":false,"endpointHidden":false,"matchPathSegmentParam":false,"availableActions":["ACTIVATE_ON_PRODUCTION","CLONE_ENDPOINT","DELETE","HIDE_ENDPOINT","ACTIVATE_ON_STAGING","EDIT_ENDPOINT_DEFINITION"],"apiSource":"USER","apiSourceDetails":null,"cloningStatus":null,"securityScheme":null,"akamaiSecurityRestrictions":{"ALLOW_UNDEFINED_PARAMS":1},"discoveredPiiIds":[],"stagingStatus":null,"productionStatus":null,"locked":false,"graphQL":false,"caseSensitive":false,"isGraphQL":false,"apiResources":[],"lockVersion":10}'
        expected = json.loads(response_body)
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, response_body),
            expected,
        )
        result = mock_client.get_endpoint(
            GetEndpointRequest(api_endpoint_id=3)
        )
        assert result == expected
        call_args = mock_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/api-definitions/v2/endpoints/3"

    def test_403_forbidden(self, mock_client):
        api_error = APIDefinitionsError(
            type="/api-definitions/error-types/forbidden",
            title="Forbidden",
            instance="TestInstance123",
            status=403,
            detail="You have insufficient permissions to perform this action. Ensure that you have the correct permissions set in Identity and Access Management.",
            severity="ERROR",
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.get_endpoint(
                GetEndpointRequest(api_endpoint_id=1)
            )
        err = exc_info.value
        assert err.status == 403
        assert err.type == "/api-definitions/error-types/forbidden"

    def test_404_not_found(self, mock_client):
        api_error = APIDefinitionsError(
            type="test.com/api-definitions/error-types/NOT-FOUND",
            title="Not Found",
            detail="No Api Endpoint/Version found for endpoint ID 1 and version 10",
            instance="TestInstance123",
            status=404,
            severity="ERROR",
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.get_endpoint(
                GetEndpointRequest(api_endpoint_id=1)
            )
        err = exc_info.value
        assert err.status == 404

    def test_required_param_not_provided(self, mock_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            mock_client.get_endpoint(GetEndpointRequest())
        assert str(exc_info.value) == (
            "get endpoint: struct validation: "
            "APIEndpointID: cannot be blank"
        )


# ======================================================================
# Validation Tests -- mirrors Go endpoints_test.go validation tests
# ======================================================================


class TestListEndpointsRequestValidate:
    """Mirrors Go TestListEndpointsRequest_Validate."""

    @pytest.mark.parametrize("name,request_obj,error_expected", [
        ("min ok", ListEndpointsRequest(sort_by="name"), False),
        ("all ok", ListEndpointsRequest(
            sort_by="updateDate", sort_order="asc",
            version_preference="LAST_UPDATED", show="ALL"
        ), False),
        ("bad sortBy", ListEndpointsRequest(sort_by="random"), True),
        ("bad sortOrder", ListEndpointsRequest(sort_by="name", sort_order="random"), True),
        ("bad version preference", ListEndpointsRequest(sort_by="name", version_preference="random"), True),
        ("bad show", ListEndpointsRequest(sort_by="name", show="NONE"), True),
    ])
    def test_validate(self, name, request_obj, error_expected):
        err = validate_list_endpoints_request(request_obj)
        if error_expected:
            assert err is not None, f"Expected error for {name}"
        else:
            assert err is None, f"Unexpected error for {name}: {err}"


class TestSecuritySchemeValidate:
    """Mirrors Go TestSecurityScheme_Validate."""

    @pytest.mark.parametrize("name,scheme,error_expected", [
        ("no securitySchemeType", SecurityScheme(
            security_scheme_type="",
            security_scheme_detail=SecuritySchemeDetail(
                api_key_location="cookie", api_key_name="test")
        ), True),
        ("bad securitySchemeType", SecurityScheme(
            security_scheme_type="bad",
            security_scheme_detail=SecuritySchemeDetail(
                api_key_location="cookie", api_key_name="test")
        ), True),
        ("no apiKeyLocation", SecurityScheme(
            security_scheme_type="apikey",
            security_scheme_detail=SecuritySchemeDetail(
                api_key_location="", api_key_name="test")
        ), True),
        ("bad apiKeyLocation", SecurityScheme(
            security_scheme_type="apikey",
            security_scheme_detail=SecuritySchemeDetail(
                api_key_location="bad", api_key_name="test")
        ), True),
        ("no apiKeyName", SecurityScheme(
            security_scheme_type="apikey",
            security_scheme_detail=SecuritySchemeDetail(
                api_key_location="cookie", api_key_name="")
        ), True),
        ("ok", SecurityScheme(
            security_scheme_type="apikey",
            security_scheme_detail=SecuritySchemeDetail(
                api_key_location="cookie", api_key_name="test")
        ), False),
    ])
    def test_validate(self, name, scheme, error_expected):
        err = validate_security_scheme(scheme)
        if error_expected:
            assert err is not None, f"Expected error for {name}"
        else:
            assert err is None, f"Unexpected error for {name}: {err}"


class TestAPIParameterRestrictionValidate:
    """Mirrors Go TestAPIParameterRestriction_Validate."""

    @pytest.mark.parametrize("name,restriction,error_expected", [
        ("min OK", APIParameterRestriction(
            array_restriction=ArrayRestriction(max_items=10, min_items=0)
        ), False),
        ("bad LengthRestriction", APIParameterRestriction(
            length_restriction=LengthRestriction(length_max=-1, length_min=-1)
        ), True),
    ])
    def test_validate(self, name, restriction, error_expected):
        err = validate_api_parameter_restriction(restriction)
        if error_expected:
            assert err is not None, f"Expected error for {name}"
        else:
            assert err is None, f"Unexpected error for {name}: {err}"


class TestAPIResourceMethodValidate:
    """Mirrors Go TestAPIResourceMethod_Validate."""

    @pytest.mark.parametrize("name,method,error_expected", [
        ("no method", APIResourceMethod(
            api_resource_method="",
            api_parameters=[APIParameter(
                api_parameter_name="test",
                api_parameter_location="path",
                api_parameter_type="string",
            )],
        ), True),
        ("no param name", APIResourceMethod(
            api_resource_method="GET",
            api_parameters=[APIParameter(
                api_parameter_name="",
                api_parameter_location="path",
                api_parameter_type="string",
            )],
        ), True),
        ("no location", APIResourceMethod(
            api_resource_method="GET",
            api_parameters=[APIParameter(
                api_parameter_name="test",
                api_parameter_location="",
                api_parameter_type="string",
            )],
        ), True),
        ("bad location", APIResourceMethod(
            api_resource_method="GET",
            api_parameters=[APIParameter(
                api_parameter_name="test",
                api_parameter_location="random",
                api_parameter_type="string",
            )],
        ), True),
        ("no type", APIResourceMethod(
            api_resource_method="GET",
            api_parameters=[APIParameter(
                api_parameter_name="test",
                api_parameter_location="path",
                api_parameter_type="",
            )],
        ), True),
        ("bad type", APIResourceMethod(
            api_resource_method="GET",
            api_parameters=[APIParameter(
                api_parameter_name="test",
                api_parameter_location="path",
                api_parameter_type="random",
            )],
        ), True),
        ("min ok", APIResourceMethod(
            api_resource_method="GET",
            api_parameters=[APIParameter(
                api_parameter_name="test",
                api_parameter_location="path",
                api_parameter_type="number",
            )],
        ), False),
    ])
    def test_validate(self, name, method, error_expected):
        err = validate_api_resource_method(method)
        if error_expected:
            assert err is not None, f"Expected error for {name}"
        else:
            assert err is None, f"Unexpected error for {name}: {err}"


class TestAkamaiSecurityRestrictionsValidate:
    """Mirrors Go TestAkamaiSecurityRestrictions_Validate."""

    @pytest.mark.parametrize("name,restrictions,error_expected", [
        ("negative POSITIVE_SECURITY_VERSION", AkamaiSecurityRestrictions(
            positive_security_version=3,
        ), True),
        ("happy path", AkamaiSecurityRestrictions(
            positive_security_version=2,
        ), False),
    ])
    def test_validate(self, name, restrictions, error_expected):
        err = validate_akamai_security_restrictions(restrictions)
        if error_expected:
            assert err is not None, f"Expected error for {name}"
        else:
            assert err is None, f"Unexpected error for {name}: {err}"


class TestRegisterEndpointRequestValidate:
    """Mirrors Go TestRegisterEndpointRequest_Validate."""

    @pytest.mark.parametrize("name,request_obj,error_expected", [
        ("ok empty basePath", RegisterEndpointRequest(
            api_endpoint_name="test",
            api_endpoint_hosts=["test.com"],
            contract_id="1-ABC",
            group_id=123,
            base_path="",
            api_resources=[APIResource(
                api_resource_name="res",
                resource_path="/p",
                api_resource_methods=[APIResourceMethod(
                    api_resource_method="GET",
                    api_parameters=[APIParameter(
                        api_parameter_name="x",
                        api_parameter_location="path",
                        api_parameter_type="string",
                    )],
                )],
            )],
        ), False),
        ("basePath longer", RegisterEndpointRequest(
            api_endpoint_name="test",
            api_endpoint_hosts=["test.com"],
            contract_id="1-ABC",
            group_id=123,
            base_path="/test/path",
            api_resources=[APIResource(
                api_resource_name="res",
                resource_path="/p",
                api_resource_methods=[APIResourceMethod(
                    api_resource_method="GET",
                    api_parameters=[APIParameter(
                        api_parameter_name="x",
                        api_parameter_location="path",
                        api_parameter_type="string",
                    )],
                )],
            )],
        ), False),
        ("basePath slash", RegisterEndpointRequest(
            api_endpoint_name="test",
            api_endpoint_hosts=["test.com"],
            contract_id="1-ABC",
            group_id=123,
            base_path="/",
            api_resources=[APIResource(
                api_resource_name="res",
                resource_path="/p",
                api_resource_methods=[APIResourceMethod(
                    api_resource_method="GET",
                    api_parameters=[APIParameter(
                        api_parameter_name="x",
                        api_parameter_location="path",
                        api_parameter_type="string",
                    )],
                )],
            )],
        ), False),
        ("fail no name", RegisterEndpointRequest(
            api_endpoint_name="",
            api_endpoint_hosts=["test.com"],
            contract_id="1-ABC",
            group_id=123,
            api_resources=[APIResource(
                api_resource_name="res",
                resource_path="/p",
                api_resource_methods=[APIResourceMethod(
                    api_resource_method="GET",
                    api_parameters=[APIParameter(
                        api_parameter_name="x",
                        api_parameter_location="path",
                        api_parameter_type="string",
                    )],
                )],
            )],
        ), True),
        ("fail no hosts", RegisterEndpointRequest(
            api_endpoint_name="test",
            api_endpoint_hosts=[],
            contract_id="1-ABC",
            group_id=123,
            api_resources=[APIResource(
                api_resource_name="res",
                resource_path="/p",
                api_resource_methods=[APIResourceMethod(
                    api_resource_method="GET",
                    api_parameters=[APIParameter(
                        api_parameter_name="x",
                        api_parameter_location="path",
                        api_parameter_type="string",
                    )],
                )],
            )],
        ), True),
        ("fail no api resource name", RegisterEndpointRequest(
            api_endpoint_name="test",
            api_endpoint_hosts=["test.com"],
            contract_id="1-ABC",
            group_id=123,
            api_resources=[APIResource(
                api_resource_name="",
                resource_path="/p",
                api_resource_methods=[APIResourceMethod(
                    api_resource_method="GET",
                    api_parameters=[APIParameter(
                        api_parameter_name="x",
                        api_parameter_location="path",
                        api_parameter_type="string",
                    )],
                )],
            )],
        ), True),
        ("no api resources", RegisterEndpointRequest(
            api_endpoint_name="test",
            api_endpoint_hosts=["test.com"],
            contract_id="1-ABC",
            group_id=123,
            api_resources=[],
        ), False),
        ("nil apiVersionInfo", RegisterEndpointRequest(
            api_endpoint_name="test",
            api_endpoint_hosts=["test.com"],
            contract_id="1-ABC",
            group_id=123,
            api_version_info=None,
            api_resources=[],
        ), False),
        ("no apiVersionInfo.Location", RegisterEndpointRequest(
            api_endpoint_name="test",
            api_endpoint_hosts=["test.com"],
            contract_id="1-ABC",
            group_id=123,
            api_version_info=APIVersionInfo(location=""),
            api_resources=[],
        ), True),
        ("nil akamaiSecurityRestrictions", RegisterEndpointRequest(
            api_endpoint_name="test",
            api_endpoint_hosts=["test.com"],
            contract_id="1-ABC",
            group_id=123,
            akamai_security_restrictions=None,
            api_resources=[],
        ), False),
        ("bad akamaiSecurityRestrictions", RegisterEndpointRequest(
            api_endpoint_name="test",
            api_endpoint_hosts=["test.com"],
            contract_id="1-ABC",
            group_id=123,
            akamai_security_restrictions=AkamaiSecurityRestrictions(
                positive_security_version=3,
            ),
            api_resources=[],
        ), True),
        ("no contract", RegisterEndpointRequest(
            api_endpoint_name="test",
            api_endpoint_hosts=["test.com"],
            contract_id="",
            group_id=123,
            api_resources=[],
        ), True),
        ("no group", RegisterEndpointRequest(
            api_endpoint_name="test",
            api_endpoint_hosts=["test.com"],
            contract_id="1-ABC",
            group_id=0,
            api_resources=[],
        ), True),
    ])
    def test_validate(self, name, request_obj, error_expected):
        err = validate_register_endpoint_request(request_obj)
        if error_expected:
            assert err is not None, f"Expected error for {name}"
        else:
            assert err is None, f"Unexpected error for {name}: {err}"


class TestAPIResourceMethodsValidate:
    """Mirrors Go TestAPIResourceMethods_Validate.

    Go's ``APIResourceMethods.Validate()`` validates each method string in
    the slice.  The Python equivalent ``validate_api_resource_methods``
    accepts a single HTTP method string.
    """

    @pytest.mark.parametrize("name,method_str,error_expected", [
        ("ok", "HEAD", False),
        ("nok", "random", True),
    ])
    def test_validate(self, name, method_str, error_expected):
        err = validate_api_resource_methods(method_str)
        if error_expected:
            assert err is not None, f"Expected error for {name}"
        else:
            assert err is None, f"Unexpected error for {name}: {err}"


class TestRegisterEndpointFromFileRequestValidate:
    """Mirrors Go TestRegisterEndpointFromFileRequest_Validate."""

    @pytest.mark.parametrize("name,request_obj,error_expected,error_contains", [
        ("OK", RegisterEndpointFromFileRequest(
            import_file_source=IMPORT_FILE_SOURCE_BASE64,
            import_file_content="base64data",
            import_file_format="swagger",
            contract_id="1-ABC",
            group_id=123,
        ), False, None),
        ("NOK: import file source URL + import file content",
         RegisterEndpointFromFileRequest(
             import_file_source=IMPORT_FILE_SOURCE_URL,
             import_file_content="test",
             import_file_format="swagger",
             contract_id="1-ABC",
             group_id=123,
         ), True, "ImportFileContent: must not be set when ImportFileSource=='URL'"),
        ("NOK: import file source BODY_BASE64 + no import file content",
         RegisterEndpointFromFileRequest(
             import_file_source=IMPORT_FILE_SOURCE_BASE64,
             import_file_content="",
             import_file_format="swagger",
             contract_id="1-ABC",
             group_id=123,
         ), True, "ImportFileContent: must be set when ImportFileSource=='BODY_BASE64'"),
        ("NOK: no contract", RegisterEndpointFromFileRequest(
            import_file_source=IMPORT_FILE_SOURCE_BASE64,
            import_file_content="base64data",
            import_file_format="swagger",
            contract_id="",
            group_id=123,
        ), True, "ContractID: cannot be blank"),
        ("NOK: no group", RegisterEndpointFromFileRequest(
            import_file_source=IMPORT_FILE_SOURCE_BASE64,
            import_file_content="base64data",
            import_file_format="swagger",
            contract_id="1-ABC",
            group_id=0,
        ), True, "GroupID: cannot be blank"),
        ("NOK: no import file format", RegisterEndpointFromFileRequest(
            import_file_source=IMPORT_FILE_SOURCE_BASE64,
            import_file_content="base64data",
            import_file_format="",
            contract_id="1-ABC",
            group_id=123,
        ), True, "ImportFileFormat: cannot be blank"),
        ("NOK: no import file source", RegisterEndpointFromFileRequest(
            import_file_source="",
            import_file_content="base64data",
            import_file_format="swagger",
            contract_id="1-ABC",
            group_id=123,
        ), True, "ImportFileSource: cannot be blank"),
        ("NOK: bad import file source", RegisterEndpointFromFileRequest(
            import_file_source="bad",
            import_file_content="base64data",
            import_file_format="swagger",
            contract_id="1-ABC",
            group_id=123,
        ), True, "ImportFileSource: value 'bad' is not valid. Must be one of: 'URL', 'BODY_BASE64'"),
        ("NOK: bad import URL", RegisterEndpointFromFileRequest(
            import_file_source=IMPORT_FILE_SOURCE_URL,
            import_file_content="not-a-url",
            import_url="not-a-url",
            import_file_format="swagger",
            contract_id="1-ABC",
            group_id=123,
        ), True, None),
        ("OK: import URL", RegisterEndpointFromFileRequest(
            import_file_source=IMPORT_FILE_SOURCE_URL,
            import_url="https://example.com/spec.json",
            import_file_format="swagger",
            contract_id="1-ABC",
            group_id=123,
        ), False, None),
        ("NOK: import URL with file source BODY_BASE64",
         RegisterEndpointFromFileRequest(
             import_file_source=IMPORT_FILE_SOURCE_BASE64,
             import_url="https://example.com/spec.json",
             import_file_format="swagger",
             contract_id="1-ABC",
             group_id=123,
         ), True, None),
    ])
    def test_validate(self, name, request_obj, error_expected, error_contains):
        err = validate_register_endpoint_from_file_request(request_obj)
        if error_expected:
            assert err is not None, f"Expected error for {name}"
            if error_contains:
                assert error_contains in str(err), f"Expected '{error_contains}' in error for {name}: {err}"
        else:
            assert err is None, f"Unexpected error for {name}: {err}"


# ======================================================================
# TestListEndpoints -- mirrors Go TestListEndpoints (endpoints_test.go)
# ======================================================================


class TestListEndpoints:
    """Tests for Client.list_endpoints -- mirrors Go TestListEndpoints."""

    def test_200_ok(self, mock_client):
        response_body = '{"totalSize":466,"page":1,"pageSize":25,"apiEndpoints":[{"apiEndPointId":1297665,"apiEndPointName":"test","description":null,"basePath":"/test","apiEndPointScheme":null,"consumeType":"any","groupId":245324,"versionNumber":5,"clonedFromVersion":4,"createdBy":"testUser","createDate":"2022-01-27T15:00:34+0000","updatedBy":"testUser","updateDate":"2022-06-29T09:35:09+0000","apiEndPointLocked":false,"contractId":"TestContract","stagingVersion":{"versionNumber":2,"status":"DEACTIVATED","timestamp":"2022-06-08T10:50:16+0000","lastError":null},"productionVersion":{"versionNumber":null,"status":null,"timestamp":null,"lastError":null},"protectedByApiKey":false,"apiGatewayEnabled":true,"apiEndPointHosts":["testing.test.com"],"apiCategoryIds":[],"apiEndPointVersion":null,"source":null,"positiveConstrainsEnabled":true,"versionHidden":false,"endpointHidden":false,"matchPathSegmentParam":false,"availableActions":["ACTIVATE_ON_STAGING","CLONE_ENDPOINT","DELETE","ACTIVATE_ON_PRODUCTION","HIDE_ENDPOINT","EDIT_ENDPOINT_DEFINITION"],"apiSource":"USER","apiSourceDetails":null,"cloningStatus":null,"securityScheme":null,"akamaiSecurityRestrictions":{"POSITIVE_SECURITY_ENABLED":1,"ALLOW_UNDEFINED_RESOURCES":1,"POSITIVE_SECURITY_VERSION":2,"ALLOW_UNDEFINED_PARAMS":1,"ALLOW_ONLY_SPEC_UNDEFINED_METHODS":0},"apiResourceBaseInfo":[{"apiResourceName":"test","resourcePath":"/test","description":"test resource description"}],"lockVersion":14}]}'
        expected = json.loads(response_body)
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, response_body),
            expected,
        )
        result = mock_client.list_endpoints(
            ListEndpointsRequest(
                sort_by="name",
                sort_order="asc",
                version_preference="LAST_UPDATED",
                show="ALL",
                page=1,
                page_size=25,
                contains="pearl",
                category="__UNCATEGORIZED__",
                contract_id="3-XXXXXX",
                group_id=33333,
            )
        )
        assert result == expected
        call_args = mock_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "GET"

    def test_500_error(self, mock_client):
        api_error = APIDefinitionsError(
            type="a",
            title="b",
            detail="c",
            status=500,
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.list_endpoints(
                ListEndpointsRequest(sort_by="name")
            )
        err = exc_info.value
        assert err.status == 500

    def test_fail_validation(self, mock_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            mock_client.list_endpoints(
                ListEndpointsRequest(sort_by="creationDate")
            )
        assert "SortBy" in str(exc_info.value)


# ======================================================================
# TestRegisterEndpoint -- mirrors Go TestRegisterEndpoint (endpoints_test.go)
# ======================================================================


class TestRegisterEndpoint:
    """Tests for Client.register_endpoint -- mirrors Go TestRegisterEndpoint."""

    def test_ok_less_parameters(self, mock_client):
        response_body = '{"apiEndPointId":1231231,"apiEndPointName":"testing"}'
        expected = json.loads(response_body)
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(201, response_body),
            expected,
        )
        result = mock_client.register_endpoint(
            RegisterEndpointRequest(
                api_endpoint_name="testing",
                api_endpoint_hosts=["test.com"],
                contract_id="TestContract",
                group_id=1234,
                api_resources=[],
            )
        )
        assert result == expected

    def test_ok_all_parameters(self, mock_client):
        response_body = '{"createdBy":"testUser","createDate":"2022-08-18T08:51:22+0000","updateDate":"2022-08-18T09:45:55+0000","updatedBy":"testUser2","apiEndPointId":1297665,"apiEndPointName":"test","description":"testDesc","basePath":"/test","consumeType":"any","apiEndPointScheme":null,"apiEndPointVersion":null,"contractId":"TestContract","groupId":111,"versionNumber":1,"clonedFromVersion":null,"apiEndPointLocked":false,"stagingVersion":{"versionNumber":null,"status":null,"timestamp":null,"lastError":null},"productionVersion":{"versionNumber":null,"status":null,"timestamp":null,"lastError":null},"protectedByApiKey":false,"apiGatewayEnabled":true,"apiEndPointHosts":["test.com"],"apiCategoryIds":[456],"source":null,"apiVersionInfo":{"location":"QUERY","parameterName":null,"value":null},"positiveConstrainsEnabled":true,"versionHidden":false,"endpointHidden":false,"matchPathSegmentParam":false,"availableActions":["ACTIVATE_ON_PRODUCTION","CLONE_ENDPOINT","DELETE","HIDE_ENDPOINT","ACTIVATE_ON_STAGING","EDIT_ENDPOINT_DEFINITION"],"apiSource":"USER","apiSourceDetails":null,"cloningStatus":null,"securityScheme":{"securitySchemeType":"apikey","securitySchemeDetail":{"apiKeyLocation":"cookie","apiKeyName":"keytest"}},"akamaiSecurityRestrictions":{"POSITIVE_SECURITY_VERSION":2,"ALLOW_UNDEFINED_RESOURCES":1},"discoveredPiiIds":[],"stagingStatus":null,"productionStatus":null,"locked":false,"graphQL":false,"caseSensitive":false,"isGraphQL":false,"apiResources":[{"apiResourceName":"restResource","resourcePath":"/resource","description":"TestDesc","apiResourceMethods":[{"apiResourceMethod":"GET","apiParameters":[{"apiParameterName":"Test","apiParameterRequired":false,"apiParameterLocation":"header","apiParameterType":"string"}]}]}],"lockVersion":1}'
        expected = json.loads(response_body)
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(201, response_body),
            expected,
        )
        result = mock_client.register_endpoint(
            RegisterEndpointRequest(
                api_endpoint_name="test",
                description="testDesc",
                base_path="/test",
                api_endpoint_hosts=["test.com"],
                contract_id="TestContract",
                group_id=111,
                api_category_ids=[456],
                security_scheme=SecurityScheme(
                    security_scheme_type="apikey",
                    security_scheme_detail=SecuritySchemeDetail(
                        api_key_location="cookie",
                        api_key_name="keytest",
                    ),
                ),
                akamai_security_restrictions=AkamaiSecurityRestrictions(
                    positive_security_version=2,
                    allow_undefined_resources=RestrictionsBool(True),
                ),
                api_version_info=APIVersionInfo(location="QUERY"),
                api_resources=[APIResource(
                    api_resource_name="restResource",
                    resource_path="/resource",
                    description="TestDesc",
                    api_resource_methods=[APIResourceMethod(
                        api_resource_method="GET",
                        api_parameters=[APIParameter(
                            api_parameter_name="Test",
                            api_parameter_location="header",
                            api_parameter_type="string",
                        )],
                    )],
                )],
            )
        )
        assert result == expected
        call_args = mock_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/api-definitions/v2/endpoints"

    def test_fail_validation(self, mock_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            mock_client.register_endpoint(RegisterEndpointRequest())
        err_msg = str(exc_info.value)
        assert "APIEndpointHosts: cannot be blank" in err_msg
        assert "APIEndpointName: cannot be blank" in err_msg
        assert "ContractID: cannot be blank" in err_msg
        assert "GroupID: cannot be blank" in err_msg

    def test_403_forbidden(self, mock_client):
        api_error = APIDefinitionsError(
            type="/api-definitions/error-types/FORBIDDEN",
            title="Forbidden",
            status=403,
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.register_endpoint(
                RegisterEndpointRequest(
                    api_endpoint_name="test",
                    api_endpoint_hosts=["test.com"],
                    contract_id="1-ABC",
                    group_id=123,
                    api_resources=[],
                )
            )
        assert exc_info.value.status == 403


# ======================================================================
# TestListUserEntitlements -- mirrors Go TestListUserEntitlements
# ======================================================================


class TestListUserEntitlements:
    """Tests for Client.list_user_entitlements."""

    def test_200_ok(self, mock_client):
        response_body = '["API_READ","API_WRITE","API_VERSIONING","API_FEATURES"]'
        expected = json.loads(response_body)
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, response_body),
            expected,
        )
        result = mock_client.list_user_entitlements()
        assert result == expected
        call_args = mock_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/api-definitions/v2/endpoints/user-entitlements"

    def test_500_error(self, mock_client):
        api_error = APIDefinitionsError(
            type="a",
            title="Internal server error",
            detail="c",
            status=500,
            errors=[{}],
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.list_user_entitlements()
        assert exc_info.value.status == 500


# ======================================================================
# TestShowEndpoint -- mirrors Go TestShowEndpoint (endpoints_test.go)
# ======================================================================


class TestShowEndpoint:
    """Tests for Client.show_endpoint."""

    def test_200_ok(self, mock_client):
        response_body = '{"apiEndPointId":1328556,"apiEndPointName":"TEST_DXE-1385","securityScheme":{"securitySchemeType":"apikey","securitySchemeDetail":{"apiKeyLocation":"cookie","apiKeyName":"keyname"}},"akamaiSecurityRestrictions":{"POSITIVE_SECURITY_VERSION":2}}'
        expected = json.loads(response_body)
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, response_body),
            expected,
        )
        result = mock_client.show_endpoint(
            ShowEndpointRequest(api_endpoint_id=12345)
        )
        assert result == expected
        call_args = mock_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/api-definitions/v2/endpoints/12345/show"

    def test_500_internal_server_error(self, mock_client):
        api_error = APIDefinitionsError(
            type="test.com/resource-impl/forward-origin-error",
            title="Not Found",
            status=500,
            instance="TestInstance123",
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.show_endpoint(
                ShowEndpointRequest(api_endpoint_id=12345)
            )
        assert exc_info.value.status == 500

    def test_404_not_found(self, mock_client):
        api_error = APIDefinitionsError(
            type="test.com/api-definitions/error-types/NOT-FOUND",
            title="Not Found",
            detail="Invalid endpoint provided.",
            instance="aae04e5f-5f01-4f5d-9ad9-3b27c74c4c88",
            status=404,
            severity="ERROR",
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.show_endpoint(
                ShowEndpointRequest(api_endpoint_id=12345)
            )
        assert exc_info.value.status == 404


# ======================================================================
# TestHideEndpoint -- mirrors Go TestHideEndpoint (endpoints_test.go)
# ======================================================================


class TestHideEndpoint:
    """Tests for Client.hide_endpoint."""

    def test_200_ok(self, mock_client):
        response_body = '{"apiEndPointId":1328556,"versionHidden":true,"endpointHidden":true,"availableActions":["CLONE_ENDPOINT","SHOW_ENDPOINT"]}'
        expected = json.loads(response_body)
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, response_body),
            expected,
        )
        result = mock_client.hide_endpoint(
            HideEndpointRequest(api_endpoint_id=12345)
        )
        assert result == expected
        call_args = mock_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/api-definitions/v2/endpoints/12345/hide"

    def test_500_internal_server_error(self, mock_client):
        api_error = APIDefinitionsError(
            type="test.com/resource-impl/forward-origin-error",
            title="Not Found",
            status=500,
            instance="/api-definitions/v2/endpoints/12345/hide",
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.hide_endpoint(
                HideEndpointRequest(api_endpoint_id=12345)
            )
        assert exc_info.value.status == 500

    def test_404_not_found(self, mock_client):
        api_error = APIDefinitionsError(
            type="test.com/api-definitions/error-types/NOT-FOUND",
            title="Not Found",
            detail="Invalid endpoint provided.",
            instance="35838562-1234-1234-1234-123456789012",
            status=404,
            severity="ERROR",
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.hide_endpoint(
                HideEndpointRequest(api_endpoint_id=12345)
            )
        assert exc_info.value.status == 404


# ======================================================================
# TestDeleteEndpoint -- mirrors Go TestDeleteEndpoint (endpoints_test.go)
# ======================================================================


class TestDeleteEndpoint:
    """Tests for Client.delete_endpoint."""

    def test_204_deleted(self, mock_client):
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(204, ""),
            None,
        )
        mock_client.delete_endpoint(
            DeleteEndpointRequest(api_endpoint_id=123)
        )
        call_args = mock_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "DELETE"
        assert call_args[0][1] == "/api-definitions/v2/endpoints/123"

    def test_403_forbidden(self, mock_client):
        api_error = APIDefinitionsError(
            type="/api-definitions/error-types/forbidden",
            title="Forbidden",
            detail="You have insufficient permissions to perform this action. Ensure that you have the correct permissions set in Identity and Access Management.",
            instance="e368eeb7-1234-1234-1234-123456789012",
            status=403,
            severity="ERROR",
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.delete_endpoint(
                DeleteEndpointRequest(api_endpoint_id=123)
            )
        assert exc_info.value.status == 403

    def test_500_internal_server_error(self, mock_client):
        api_error = APIDefinitionsError(
            type="/api-definitions/error-types/smth",
            title="Not Found",
            status=500,
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.delete_endpoint(
                DeleteEndpointRequest(api_endpoint_id=123)
            )
        assert exc_info.value.status == 500


# ======================================================================
# TestRegisterEndpointFromFile -- mirrors Go TestRegisterEndpointFromFile
# ======================================================================


class TestRegisterEndpointFromFile:
    """Tests for Client.register_endpoint_from_file."""

    def test_does_not_validate(self, mock_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            mock_client.register_endpoint_from_file(
                RegisterEndpointFromFileRequest()
            )
        err_msg = str(exc_info.value)
        assert "ContractID: cannot be blank" in err_msg
        assert "GroupID: cannot be blank" in err_msg
        assert "ImportFileFormat: cannot be blank" in err_msg
        assert "ImportFileSource: cannot be blank" in err_msg

    def test_201_created(self, mock_client):
        response_body = '{"apiEndPointId":123456,"apiEndPointName":"Bookstore API","basePath":"/bookstore","apiResources":[{"apiResourceName":"books","resourcePath":"/books","apiResourceMethods":[{"apiResourceMethod":"GET","apiParameters":[{"apiParameterName":"bookId","apiParameterLocation":"path","apiParameterType":"integer","apiParameterRequired":true}]}]}]}'
        expected = json.loads(response_body)
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(201, response_body),
            expected,
        )
        result = mock_client.register_endpoint_from_file(
            RegisterEndpointFromFileRequest(
                import_file_source=IMPORT_FILE_SOURCE_BASE64,
                import_file_content="base64data",
                import_file_format="swagger",
                contract_id="1-ABC",
                group_id=123,
            )
        )
        assert result == expected
        call_args = mock_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/api-definitions/v2/endpoints/files"

    def test_503_error(self, mock_client):
        api_error = APIDefinitionsError(
            type="service-unavailable",
            title="Service Unavailable",
            status=503,
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.register_endpoint_from_file(
                RegisterEndpointFromFileRequest(
                    import_file_source=IMPORT_FILE_SOURCE_BASE64,
                    import_file_content="base64data",
                    import_file_format="swagger",
                    contract_id="1-ABC",
                    group_id=123,
                )
            )
        assert exc_info.value.status == 503


# ======================================================================
# TestListEndpointVersions -- mirrors Go TestListEndpointVersions
# ======================================================================


class TestListEndpointVersions:
    """Tests for Client.list_endpoint_versions."""

    def test_200_ok(self, mock_client):
        response_body = '{"totalSize":1,"page":2,"pageSize":3,"apiEndPointId":2,"apiEndPointName":"test_cache2","apiVersions":[{"createdBy":"tester","createDate":"2022-08-11T06:33:29+0000","updateDate":"2022-08-16T10:08:41+0000","updatedBy":"tester","apiEndPointVersionId":10101010,"basePath":"/test","versionNumber":1,"description":null,"basedOn":null,"stagingStatus":null,"productionStatus":null,"stagingDate":null,"productionDate":null,"isVersionLocked":false,"hidden":false,"availableActions":["ACTIVATE_ON_STAGING","COMPARE_ENDPOINT","DELETE","CLONE_VERSION","EDIT_AAG_SETTINGS","ACTIVATE_ON_PRODUCTION","COMPARE_RESOURCE_PURPOSES","HIDE_VERSION","RESOURCES","EDIT_ENDPOINT_DEFINITION","VIEW_AAG_SETTINGS","COMPARE_AAG_SETTINGS","VIEW_TAPIOCA"],"cloningStatus":null,"lockVersion":1}]}'
        expected = json.loads(response_body)
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, response_body),
            expected,
        )
        result = mock_client.list_endpoint_versions(
            ListEndpointVersionsRequest(api_endpoint_id=2)
        )
        assert result == expected
        call_args = mock_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "GET"

    def test_200_ok_fields_populated(self, mock_client):
        response_body = '{"totalSize":1,"page":2,"pageSize":3,"apiEndPointId":10,"apiEndPointName":"testingEndpoint","apiVersions":[{"createdBy":"user","createDate":"2020-02-27T15:22:46+0000","updateDate":"2020-02-27T15:22:46+0000","updatedBy":"user","apiEndPointVersionId":111222,"basePath":"/production/test","versionNumber":3,"description":"Test description","basedOn":2,"stagingStatus":"PENDING","productionStatus":"ACTIVE","stagingDate":"2022-02-27T15:22:46+0000","productionDate":"2022-02-27T15:22:46+0000","isVersionLocked":true,"hidden":true,"availableActions":["COMPARE_AAG_SETTINGS","EDIT_ENDPOINT_DEFINITION","VIEW_AAG_SETTINGS","ACTIVATE_ON_PRODUCTION","ACTIVATE_ON_STAGING","CLONE_VERSION","EDIT_AAG_SETTINGS","COMPARE_RESOURCE_PURPOSES","HIDE_VERSION","COMPARE_ENDPOINT","DELETE","RESOURCES","VIEW_TAPIOCA"],"cloningStatus":"FakeStatus","lockVersion":0},{"createdBy":"user2","createDate":"2020-01-22T20:06:07+0000","updateDate":"2020-01-22T20:06:19+0000","updatedBy":"user3","apiEndPointVersionId":999000,"basePath":"/production/test","versionNumber":2,"description":null,"basedOn":1,"stagingStatus":null,"productionStatus":"DEACTIVATED","stagingDate":null,"productionDate":"2020-01-22T21:26:45+0000","isVersionLocked":true,"hidden":false,"availableActions":["COMPARE_AAG_SETTINGS","VIEW_AAG_SETTINGS","ACTIVATE_ON_PRODUCTION","ACTIVATE_ON_STAGING","CLONE_VERSION","COMPARE_RESOURCE_PURPOSES","HIDE_VERSION","COMPARE_ENDPOINT","VIEW_TAPIOCA"],"cloningStatus":null,"lockVersion":2}]}'
        expected = json.loads(response_body)
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, response_body),
            expected,
        )
        result = mock_client.list_endpoint_versions(
            ListEndpointVersionsRequest(api_endpoint_id=10)
        )
        assert result == expected

    def test_200_ok_with_query_params(self, mock_client):
        response_body = '{"totalSize":3,"page":1,"pageSize":1,"apiEndPointId":2,"apiEndPointName":"test_cache2","apiVersions":[{"createdBy":"tester","createDate":"2022-08-11T06:33:29+0000","updateDate":"2022-08-16T10:08:41+0000","updatedBy":"tester","apiEndPointVersionId":10101010,"basePath":"/test","versionNumber":1,"description":null,"basedOn":null,"stagingStatus":null,"productionStatus":null,"stagingDate":null,"productionDate":null,"isVersionLocked":false,"hidden":false,"availableActions":["ACTIVATE_ON_STAGING","COMPARE_ENDPOINT","DELETE","CLONE_VERSION","EDIT_AAG_SETTINGS","ACTIVATE_ON_PRODUCTION","COMPARE_RESOURCE_PURPOSES","HIDE_VERSION","RESOURCES","EDIT_ENDPOINT_DEFINITION","VIEW_AAG_SETTINGS","COMPARE_AAG_SETTINGS","VIEW_TAPIOCA"],"cloningStatus":null,"lockVersion":1}]}'
        expected = json.loads(response_body)
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, response_body),
            expected,
        )
        result = mock_client.list_endpoint_versions(
            ListEndpointVersionsRequest(
                api_endpoint_id=2,
                page=1,
                page_size=1,
                sort_by="description",
                sort_order="asc",
                visibility="ALL",
            )
        )
        assert result == expected

    def test_403_forbidden(self, mock_client):
        api_error = APIDefinitionsError(
            type="/api-definitions/error-types/forbidden",
            title="Forbidden",
            instance="TestInstance123",
            status=403,
            detail="You have insufficient permissions to perform this action. Ensure that you have the correct permissions set in Identity and Access Management.",
            severity="ERROR",
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.list_endpoint_versions(
                ListEndpointVersionsRequest(api_endpoint_id=1)
            )
        assert exc_info.value.status == 403

    def test_404_not_found(self, mock_client):
        api_error = APIDefinitionsError(
            type="test.com/resource-impl/forward-origin-error",
            title="Not Found",
            instance="TestInstance123",
            status=404,
            method="GET",
            server_ip="1.1.1.1",
            client_ip="2.2.2.2",
            request_id="3222db8",
            request_time="2022-08-19T08:13:39Z",
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.list_endpoint_versions(
                ListEndpointVersionsRequest(api_endpoint_id=10101)
            )
        assert exc_info.value.status == 404

    def test_required_param_not_provided(self, mock_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            mock_client.list_endpoint_versions(
                ListEndpointVersionsRequest()
            )
        assert str(exc_info.value) == (
            "list endpoint versions: struct validation: "
            "APIEndpointID: cannot be blank"
        )

    def test_query_params_invalid(self, mock_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            mock_client.list_endpoint_versions(
                ListEndpointVersionsRequest(
                    api_endpoint_id=1,
                    page=1,
                    page_size=1,
                    sort_by="Wrong",
                    sort_order="Wrong",
                    visibility="Wrong",
                )
            )
        err_msg = str(exc_info.value)
        assert "Show: value 'Wrong' is invalid." in err_msg
        assert "SortBy: value 'Wrong' is invalid." in err_msg
        assert "SortOrder: value 'Wrong' is invalid." in err_msg


# ======================================================================
# TestUpdateEndpointVersion -- mirrors Go TestUpdateEndpointVersion
# ======================================================================


class TestUpdateEndpointVersion:
    """Tests for Client.update_endpoint_version."""

    def test_200_ok(self, mock_client):
        response_body = '{"createdBy":"user","createDate":"2022-08-18T08:51:22+0000","updateDate":"2022-08-18T09:45:55+0000","updatedBy":"user2","apiEndPointId":123,"apiEndPointName":"TestName","description":"Test description","basePath":"/test","consumeType":"any","apiEndPointScheme":null,"apiEndPointVersion":321,"contractId":"TestContract","groupId":123,"versionNumber":1,"clonedFromVersion":null,"apiEndPointLocked":false,"stagingVersion":{"versionNumber":null,"status":null,"timestamp":null,"lastError":null},"productionVersion":{"versionNumber":null,"status":null,"timestamp":null,"lastError":null},"protectedByApiKey":false,"apiGatewayEnabled":false,"apiEndPointHosts":["test.com"],"apiCategoryIds":null,"source":null,"positiveConstrainsEnabled":false,"versionHidden":false,"endpointHidden":false,"matchPathSegmentParam":true,"availableActions":null,"apiSource":null,"apiSourceDetails":null,"cloningStatus":null,"securityScheme":null,"akamaiSecurityRestrictions":{"ALLOW_UNDEFINED_PARAMS":1,"POSITIVE_SECURITY_VERSION":2,"POSITIVE_SECURITY_ENABLED":1,"ALLOW_UNDEFINED_RESOURCES":1,"ALLOW_ONLY_SPEC_UNDEFINED_METHODS":0},"discoveredPiiIds":[],"stagingStatus":null,"productionStatus":null,"locked":false,"graphQL":false,"caseSensitive":false,"isGraphQL":false,"apiResources":[{"createdBy":"testU","createDate":"2022-08-22T09:58:54+0000","updateDate":"2022-08-22T09:58:54+0000","updatedBy":"testU","apiResourceId":1,"apiResourceName":"testResource","resourcePath":"/res1","description":"TestDesc","link":"/Test1","apiResourceClonedFromId":1010,"apiResourceLogicId":2,"private":false,"apiResourceMethods":[{"apiResourceMethodId":34,"apiResourceMethod":"PUT","apiResourceMethodLogicId":234}],"lockVersion":3}],"lockVersion":2}'
        expected = json.loads(response_body)
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, response_body),
            expected,
        )
        result = mock_client.update_endpoint_version(
            UpdateEndpointVersionRequest(
                version_number=1,
                api_endpoint_id=123,
                body=UpdateEndpointVersionRequestBody(
                    security_scheme=SecurityScheme(
                        security_scheme_type="apikey",
                        security_scheme_detail=SecuritySchemeDetail(
                            api_key_location="cookie",
                            api_key_name="name",
                        ),
                    ),
                    akamai_security_restrictions=AkamaiSecurityRestrictions(
                        allow_undefined_params=RestrictionsBool(True),
                        positive_security_version=2,
                        positive_security_enabled=RestrictionsBool(True),
                        allow_undefined_resources=RestrictionsBool(True),
                        allow_only_spec_undefined_methods=RestrictionsBool(False),
                    ),
                    contract_id="TestContract",
                    group_id=123,
                    api_endpoint_id=123,
                    api_endpoint_version=321,
                    version_number=1,
                    api_endpoint_name="TestName",
                    description="Test description",
                    base_path="/test",
                    api_endpoint_scheme="http",
                    consume_type="any",
                    api_endpoint_hosts=["test.com"],
                    lock_version=1,
                    case_sensitive=False,
                    match_path_segment_param=True,
                    is_graphql=False,
                    api_gateway_enabled=False,
                    graphql=False,
                    api_version_info=APIVersionInfo(
                        location="HEADER",
                        parameter_name="ds",
                        value="qw",
                    ),
                    api_resources=[APIResource(
                        api_resource_cloned_from_id=1010,
                        api_resource_id=1,
                        api_resource_logic_id=2,
                        api_resource_methods=[APIResourceMethod(
                            api_resource_method_id=34,
                            api_resource_method_logic_id=234,
                            api_resource_method="PUT",
                        )],
                        api_resource_name="testResource",
                        description="TestDesc",
                        link="/Test1",
                        lock_version=2,
                        private=False,
                        resource_path="/res1",
                    )],
                ),
            )
        )
        assert result == expected
        call_args = mock_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "PUT"
        assert call_args[0][1] == "/api-definitions/v2/endpoints/123/versions/1"

    def test_404_not_found(self, mock_client):
        api_error = APIDefinitionsError(
            type="test.com/resource-impl/forward-origin-error",
            title="Not Found",
            instance="TestInstance123",
            status=404,
            method="GET",
            server_ip="1.1.1.1",
            client_ip="2.2.2.2",
            request_id="3222db8",
            request_time="2022-08-19T08:13:39Z",
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.update_endpoint_version(
                UpdateEndpointVersionRequest(
                    version_number=1,
                    api_endpoint_id=1,
                    body=UpdateEndpointVersionRequestBody(
                        security_scheme=SecurityScheme(
                            security_scheme_type="apikey",
                            security_scheme_detail=SecuritySchemeDetail(
                                api_key_location="cookie", api_key_name="name",
                            ),
                        ),
                        akamai_security_restrictions=AkamaiSecurityRestrictions(
                            allow_undefined_params=RestrictionsBool(True),
                            positive_security_version=2,
                            positive_security_enabled=RestrictionsBool(True),
                            allow_undefined_resources=RestrictionsBool(True),
                            allow_only_spec_undefined_methods=RestrictionsBool(False),
                        ),
                        contract_id="TestContract",
                        group_id=123,
                        api_endpoint_id=123,
                        api_endpoint_version=321,
                        version_number=1,
                        api_endpoint_name="TestName",
                        description="Test description",
                        base_path="/test",
                        api_endpoint_scheme="http",
                        api_endpoint_hosts=["test.com"],
                        api_category_ids=[12],
                        lock_version=1,
                        case_sensitive=True,
                        match_path_segment_param=True,
                        is_graphql=True,
                        graphql=False,
                        api_version_info=APIVersionInfo(
                            location="HEADER", parameter_name="ds", value="qw",
                        ),
                        api_resources=[APIResource(
                            api_resource_cloned_from_id=1010,
                            api_resource_id=1,
                            api_resource_logic_id=2,
                            api_resource_methods=[APIResourceMethod(
                                api_resource_method_id=34,
                                api_resource_method_logic_id=234,
                                api_resource_method="PUT",
                                api_parameters=[APIParameter(
                                    api_parameter_name="Test",
                                    api_parameter_location="header",
                                    api_parameter_type="string",
                                )],
                            )],
                            api_resource_name="testResource",
                            description="TestDesc",
                            link="/Test1",
                            lock_version=2,
                            private=False,
                            resource_path="/res1",
                        )],
                    ),
                )
            )
        assert exc_info.value.status == 404

    def test_409_conflict(self, mock_client):
        api_error = APIDefinitionsError(
            type="/api-definitions/error-types/CONCURRENT-MODIFICATION-ERROR",
            title="Concurrent Modification Error",
            instance="TestInstance123",
            detail="API Endpoint does not allow concurrent modification. Please get the latest API Definition and try again.",
            status=409,
            severity="ERROR",
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.update_endpoint_version(
                UpdateEndpointVersionRequest(
                    version_number=1,
                    api_endpoint_id=1,
                    body=UpdateEndpointVersionRequestBody(
                        security_scheme=SecurityScheme(
                            security_scheme_type="apikey",
                            security_scheme_detail=SecuritySchemeDetail(
                                api_key_location="cookie", api_key_name="name",
                            ),
                        ),
                        akamai_security_restrictions=AkamaiSecurityRestrictions(
                            positive_security_version=2,
                            allow_undefined_params=RestrictionsBool(True),
                            positive_security_enabled=RestrictionsBool(True),
                            allow_undefined_resources=RestrictionsBool(True),
                            allow_only_spec_undefined_methods=RestrictionsBool(False),
                        ),
                        contract_id="TestContract",
                        group_id=123,
                        api_endpoint_id=123,
                        api_endpoint_version=321,
                        version_number=1,
                        api_endpoint_name="TestName",
                        description="Test description",
                        base_path="/test",
                        api_endpoint_scheme="http",
                        api_endpoint_hosts=["test.com"],
                        api_category_ids=[12],
                        lock_version=1,
                        match_path_segment_param=True,
                        is_graphql=True,
                        api_gateway_enabled=False,
                        graphql=False,
                        api_version_info=APIVersionInfo(
                            location="HEADER", parameter_name="ds", value="qw",
                        ),
                        api_resources=[APIResource(
                            api_resource_cloned_from_id=1010,
                            api_resource_id=1,
                            api_resource_logic_id=2,
                            api_resource_methods=[APIResourceMethod(
                                api_resource_method_id=34,
                                api_resource_method_logic_id=234,
                                api_resource_method="PUT",
                                api_parameters=[APIParameter(
                                    api_parameter_name="Test",
                                    api_parameter_location="header",
                                    api_parameter_type="string",
                                )],
                            )],
                            api_resource_name="testResource",
                            description="TestDesc",
                            link="/Test1",
                            lock_version=2,
                            private=False,
                            resource_path="/res1",
                        )],
                    ),
                )
            )
        assert exc_info.value.status == 409
        assert exc_info.value.type == "/api-definitions/error-types/CONCURRENT-MODIFICATION-ERROR"

    def test_validation_errors(self, mock_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            mock_client.update_endpoint_version(
                UpdateEndpointVersionRequest()
            )
        err_msg = str(exc_info.value)
        assert "APIEndpointID: cannot be blank" in err_msg
        assert "VersionNumber: cannot be blank" in err_msg


# ======================================================================
# TestGetEndpointVersion -- mirrors Go TestGetEndpointVersion
# ======================================================================


class TestGetEndpointVersion:
    """Tests for Client.get_endpoint_version."""

    def test_200_ok(self, mock_client):
        response_body = '{"createdBy":"user","createDate":"2022-08-18T08:51:22+0000","updateDate":"2022-08-18T09:45:55+0000","updatedBy":"user2","apiEndPointId":3,"apiEndPointName":"Test","description":"Test desc","basePath":"/test","consumeType":"any","apiEndPointScheme":null,"apiEndPointVersion":999,"contractId":"TestContract","groupId":111,"versionNumber":10,"clonedFromVersion":222,"apiEndPointLocked":false,"stagingVersion":{"versionNumber":10,"status":"DEACTIVATED","timestamp":"2022-07-06T09:12:04+0000","lastError":null},"productionVersion":{"versionNumber":null,"status":null,"timestamp":null,"lastError":null},"protectedByApiKey":false,"apiGatewayEnabled":true,"apiEndPointHosts":["test.com"],"apiCategoryIds":[456],"source":null,"apiVersionInfo":{"location":"BASE_PATH","parameterName":null,"value":null},"positiveConstrainsEnabled":true,"versionHidden":false,"endpointHidden":false,"matchPathSegmentParam":false,"availableActions":["ACTIVATE_ON_PRODUCTION","CLONE_ENDPOINT","DELETE","HIDE_ENDPOINT","ACTIVATE_ON_STAGING","EDIT_ENDPOINT_DEFINITION"],"apiSource":"USER","apiSourceDetails":null,"cloningStatus":null,"securityScheme":null,"akamaiSecurityRestrictions":{"ALLOW_UNDEFINED_PARAMS":1,"POSITIVE_SECURITY_VERSION":2,"POSITIVE_SECURITY_ENABLED":1,"ALLOW_UNDEFINED_RESOURCES":1,"ALLOW_ONLY_SPEC_UNDEFINED_METHODS":0},"discoveredPiiIds":[],"stagingStatus":null,"productionStatus":null,"locked":false,"graphQL":false,"caseSensitive":false,"isGraphQL":false,"apiResources":[],"lockVersion":10}'
        expected = json.loads(response_body)
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, response_body),
            expected,
        )
        result = mock_client.get_endpoint_version(
            GetEndpointVersionRequest(version_number=10, api_endpoint_id=3)
        )
        assert result == expected
        call_args = mock_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/api-definitions/v2/endpoints/3/versions/10/resources-detail"

    def test_200_ok_all_fields(self, mock_client):
        response_body = '{"createdBy":"tester","createDate":"2022-08-11T06:33:29+0000","updateDate":"2022-08-16T10:08:41+0000","updatedBy":"tester","apiEndPointId":456,"apiEndPointName":"test","description":"test description","basePath":"/test","consumeType":"any","apiEndPointScheme":"http","apiEndPointVersion":1010,"contractId":"Test-Contract123","groupId":88888,"versionNumber":123,"clonedFromVersion":111,"apiEndPointLocked":true,"stagingVersion":{"versionNumber":10,"status":"ACTIVE","timestamp":"2022-08-16T10:08:41+0000","lastError":null},"productionVersion":{"versionNumber":10,"status":"ACTIVE","timestamp":"2022-08-16T10:08:41+0000","lastError":null},"protectedByApiKey":true,"apiGatewayEnabled":true,"apiEndPointHosts":["testing.com"],"apiCategoryIds":[],"source":{"type":"TestType","apiVersion":"TestVersion","specificationVersion":"Test"},"apiVersionInfo":{"location":"QUERY","parameterName":"QUERY","value":"test"},"positiveConstrainsEnabled":true,"versionHidden":true,"endpointHidden":true,"matchPathSegmentParam":true,"availableActions":["ACTIVATE_ON_PRODUCTION","CLONE_ENDPOINT","DELETE","HIDE_ENDPOINT","ACTIVATE_ON_STAGING","EDIT_ENDPOINT_DEFINITION"],"apiSource":"USER","apiSourceDetails":[{"name":"TestName","sourceValue":"TestSource","savedValue":"TestSaved"}],"cloningStatus":"PENDING","securityScheme":{"securitySchemeType":"apikey","securitySchemeDetail":{"apiKeyName":"test","apiKeyLocation":"cookie"}},"akamaiSecurityRestrictions":{"MAX_JSONXML_ELEMENT":5,"MAX_ELEMENT_NAME_LENGTH":100,"MAX_STRING_LENGTH":40,"MAX_INTEGER_VALUE":90,"MAX_DOC_DEPTH":20,"MAX_BODY_SIZE":400,"ALLOW_UNDEFINED_METHOD_GET":1},"discoveredPiiIds":[],"stagingStatus":"WAITING","productionStatus":"PENDING","locked":true,"graphQL":true,"caseSensitive":true,"isGraphQL":true,"apiResources":[{"createdBy":"test","createDate":"2022-08-11T06:33:29+0000","updateDate":"2022-08-11T06:33:29+0000","updatedBy":"test","apiResourceId":111,"apiResourceName":"test_api","resourcePath":"/test_api","description":"Test desc","link":"TestLink","apiResourceClonedFromId":10,"apiResourceLogicId":112,"private":false,"apiResourceMethods":[{"apiResourceMethodId":44,"apiResourceMethod":"GET","apiParameters":[{"apiParameterName":"TestName","apiParameterRequired":false,"apiParameterLocation":"TestLocation","pathParamLocationId":999,"apiParameterType":"TestType","array":true,"apiParameterNotes":"TestNotes","apiParameterRestriction":{"lengthRestriction":{"lengthMax":10,"lengthMin":1},"rangeRestriction":{"rangeMin":1,"rangeMax":15},"numberRangeRestriction":{"numberRangeMin":2,"numberRangeMax":30},"arrayRestriction":{"collectionFormat":"Test","maxItems":100,"minItems":20,"uniqueItems":false},"xmlConversionRule":{"attribute":false,"wrapped":true,"name":"Testing","namespace":"Test","prefix":"T"}},"apiParameterId":10,"apiParamLogicId":11,"apiResourceMethParamID":12}],"apiResourceMethodLogicId":55,"methodRestrictions":null}],"lockVersion":0},{"createdBy":"Test user","createDate":"2022-08-11T06:33:29+0000","updateDate":"2022-08-11T06:33:29+0000","updatedBy":"Test user","apiResourceId":321,"apiResourceName":"test_api3","resourcePath":"/test_api3","description":null,"link":null,"apiResourceClonedFromId":null,"apiResourceLogicId":4321,"private":false,"apiResourceMethods":[{"apiResourceMethodId":789,"apiResourceMethod":"GET","apiParameters":[],"apiResourceMethodLogicId":6789,"methodRestrictions":null}],"lockVersion":0}],"lockVersion":1}'
        expected = json.loads(response_body)
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, response_body),
            expected,
        )
        result = mock_client.get_endpoint_version(
            GetEndpointVersionRequest(version_number=123, api_endpoint_id=456)
        )
        assert result == expected

    def test_403_forbidden(self, mock_client):
        api_error = APIDefinitionsError(
            type="/api-definitions/error-types/forbidden",
            title="Forbidden",
            instance="TestInstance123",
            status=403,
            detail="You have insufficient permissions to perform this action. Ensure that you have the correct permissions set in Identity and Access Management.",
            severity="ERROR",
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.get_endpoint_version(
                GetEndpointVersionRequest(version_number=1, api_endpoint_id=1)
            )
        assert exc_info.value.status == 403

    def test_404_not_found(self, mock_client):
        api_error = APIDefinitionsError(
            type="test.com/api-definitions/error-types/NOT-FOUND",
            title="Not Found",
            detail="No Api Endpoint/Version found for endpoint ID 1 and version 10",
            instance="TestInstance123",
            status=404,
            severity="ERROR",
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.get_endpoint_version(
                GetEndpointVersionRequest(version_number=1010, api_endpoint_id=1)
            )
        assert exc_info.value.status == 404

    def test_required_param_not_provided(self, mock_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            mock_client.get_endpoint_version(
                GetEndpointVersionRequest(version_number=10)
            )
        assert str(exc_info.value) == (
            "get endpoint version: struct validation: "
            "APIEndpointID: cannot be blank"
        )


# ======================================================================
# TestCloneEndpointVersion -- mirrors Go TestCloneEndpointVersion
# ======================================================================


class TestCloneEndpointVersion:
    """Tests for Client.clone_endpoint_version."""

    def test_200_ok(self, mock_client):
        response_body = '{"createdBy":"user1","createDate":"2022-08-19T06:43:33+0000","updateDate":"2022-08-19T06:43:33+0000","updatedBy":"user1","apiEndPointId":123,"apiEndPointName":"IPQA_DXE_TEST_2","description":"Test","basePath":"/test","consumeType":"any","apiEndPointScheme":null,"apiEndPointVersion":111000,"contractId":"Contract123","groupId":222,"versionNumber":3,"clonedFromVersion":110000,"apiEndPointLocked":false,"stagingVersion":{"versionNumber":2,"status":"DEACTIVATED","timestamp":"2022-07-06T09:12:04+0000","lastError":null},"productionVersion":{"versionNumber":null,"status":null,"timestamp":null,"lastError":null},"protectedByApiKey":true,"apiGatewayEnabled":true,"apiEndPointHosts":["test.com","test2.com"],"apiCategoryIds":[12],"source":null,"positiveConstrainsEnabled":true,"versionHidden":false,"endpointHidden":false,"matchPathSegmentParam":false,"availableActions":["ACTIVATE_ON_STAGING","CLONE_ENDPOINT","DELETE","ACTIVATE_ON_PRODUCTION","HIDE_ENDPOINT","EDIT_ENDPOINT_DEFINITION"],"apiSource":"USER","apiSourceDetails":null,"cloningStatus":null,"securityScheme":null,"akamaiSecurityRestrictions":{"POSITIVE_SECURITY_VERSION":2,"ALLOW_UNDEFINED_PARAMS":1,"ALLOW_UNDEFINED_RESOURCES":1,"POSITIVE_SECURITY_ENABLED":1,"ALLOW_ONLY_SPEC_UNDEFINED_METHODS":0},"discoveredPiiIds":[],"stagingStatus":null,"productionStatus":null,"locked":false,"graphQL":false,"caseSensitive":false,"isGraphQL":false,"apiResources":[],"lockVersion":1}'
        expected = json.loads(response_body)
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, response_body),
            expected,
        )
        result = mock_client.clone_endpoint_version(
            CloneEndpointVersionRequest(version_number=2, api_endpoint_id=123)
        )
        assert result == expected
        call_args = mock_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/api-definitions/v2/endpoints/123/versions/2/cloneVersion"

    def test_200_ok_with_resources(self, mock_client):
        response_body = '{"createdBy":"test","createDate":"2022-08-19T07:35:43+0000","updateDate":"2022-08-19T07:35:43+0000","updatedBy":"test","apiEndPointId":1000,"apiEndPointName":"TestEndpoint","description":null,"basePath":"/test2","consumeType":"any","apiEndPointScheme":null,"apiEndPointVersion":100,"contractId":"Contract2","groupId":33,"versionNumber":10,"clonedFromVersion":200,"apiEndPointLocked":false,"stagingVersion":{"versionNumber":null,"status":null,"timestamp":null,"lastError":null},"productionVersion":{"versionNumber":2,"status":"ACTIVE","timestamp":"2019-10-02T14:49:09+0000","lastError":null},"protectedByApiKey":true,"apiGatewayEnabled":true,"apiEndPointHosts":["host.test.com"],"apiCategoryIds":[11],"source":null,"positiveConstrainsEnabled":false,"versionHidden":false,"endpointHidden":false,"matchPathSegmentParam":true,"availableActions":["ACTIVATE_ON_PRODUCTION","CLONE_ENDPOINT","ACTIVATE_ON_STAGING","DEACTIVATE_ON_PRODUCTION","EDIT_ENDPOINT_DEFINITION"],"apiSource":"USER","apiSourceDetails":null,"cloningStatus":null,"securityScheme":{"securitySchemeType":"apikey","securitySchemeDetail":{"apiKeyLocation":"header","apiKeyName":"key-header"}},"akamaiSecurityRestrictions":{"POSITIVE_SECURITY_VERSION":2},"discoveredPiiIds":[],"stagingStatus":null,"productionStatus":null,"locked":false,"graphQL":false,"caseSensitive":true,"isGraphQL":false,"apiResources":[{"createdBy":"user1","createDate":"2022-08-19T07:35:43+0000","updateDate":"2022-08-19T07:35:43+0000","updatedBy":"user1","apiResourceId":123,"apiResourceName":"testRes","resourcePath":"test/200","description":null,"link":null,"apiResourceClonedFromId":null,"apiResourceLogicId":456,"private":false,"apiResourceMethods":[{"apiResourceMethodId":1122,"apiResourceMethod":"GET","apiParameters":[],"apiResourceMethodLogicId":3344,"methodRestrictions":null},{"apiResourceMethodId":5566,"apiResourceMethod":"POST","apiParameters":[],"apiResourceMethodLogicId":7788,"methodRestrictions":null}],"lockVersion":0}],"lockVersion":1}'
        expected = json.loads(response_body)
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, response_body),
            expected,
        )
        result = mock_client.clone_endpoint_version(
            CloneEndpointVersionRequest(version_number=10, api_endpoint_id=1000)
        )
        assert result == expected

    def test_403_forbidden(self, mock_client):
        api_error = APIDefinitionsError(
            type="/api-definitions/error-types/forbidden",
            title="Forbidden",
            instance="TestInstance123",
            status=403,
            detail="You have insufficient permissions to perform this action. Ensure that you have the correct permissions set in Identity and Access Management.",
            severity="ERROR",
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.clone_endpoint_version(
                CloneEndpointVersionRequest(version_number=1, api_endpoint_id=1)
            )
        assert exc_info.value.status == 403

    def test_404_not_found(self, mock_client):
        api_error = APIDefinitionsError(
            type="test.com/api-definitions/error-types/NOT-FOUND",
            title="Not Found",
            detail="Cannot delete Api Endpoint Version. No Version found for API ID 10101",
            instance="TestInstance123",
            status=404,
            severity="ERROR",
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.clone_endpoint_version(
                CloneEndpointVersionRequest(version_number=1, api_endpoint_id=10101)
            )
        assert exc_info.value.status == 404

    def test_required_params_not_provided(self, mock_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            mock_client.clone_endpoint_version(
                CloneEndpointVersionRequest()
            )
        err_msg = str(exc_info.value)
        assert "APIEndpointID: cannot be blank" in err_msg
        assert "VersionNumber: cannot be blank" in err_msg


# ======================================================================
# TestDeleteEndpointVersion -- mirrors Go TestDeleteEndpointVersion
# ======================================================================


class TestDeleteEndpointVersion:
    """Tests for Client.delete_endpoint_version."""

    def test_204_no_content(self, mock_client):
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(204, ""),
            None,
        )
        mock_client.delete_endpoint_version(
            DeleteEndpointVersionRequest(version_number=10, api_endpoint_id=333000444)
        )
        call_args = mock_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "DELETE"
        assert call_args[0][1] == "/api-definitions/v2/endpoints/333000444/versions/10"

    def test_403_forbidden(self, mock_client):
        api_error = APIDefinitionsError(
            type="/api-definitions/error-types/forbidden",
            title="Forbidden",
            instance="TestInstance123",
            status=403,
            detail="You have insufficient permissions to perform this action. Ensure that you have the correct permissions set in Identity and Access Management.",
            severity="ERROR",
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.delete_endpoint_version(
                DeleteEndpointVersionRequest(version_number=1, api_endpoint_id=1)
            )
        assert exc_info.value.status == 403

    def test_404_not_found(self, mock_client):
        api_error = APIDefinitionsError(
            type="test.com/api-definitions/error-types/NOT-FOUND",
            title="Not Found",
            detail="Cannot delete Api Endpoint Version. No Version found for API ID 10101",
            instance="TestInstance123",
            status=404,
            severity="ERROR",
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.delete_endpoint_version(
                DeleteEndpointVersionRequest(version_number=1, api_endpoint_id=10101)
            )
        assert exc_info.value.status == 404

    def test_required_param_not_provided(self, mock_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            mock_client.delete_endpoint_version(
                DeleteEndpointVersionRequest()
            )
        err_msg = str(exc_info.value)
        assert "APIEndpointID: cannot be blank" in err_msg
        assert "VersionNumber: cannot be blank" in err_msg


# ======================================================================
# TestVerifyVersion -- mirrors Go TestVerifyVersion (activations_test.go)
# ======================================================================


class TestVerifyVersion:
    """Tests for Client.verify_version."""

    def test_200_ok(self, mock_client):
        response_body = '[{"severity":"ERROR","detail":"You shall not pass"},{"severity":"WARNING","detail":"You shall not pass"}]'
        expected = json.loads(response_body)
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, response_body),
            expected,
        )
        result = mock_client.verify_version(
            VerifyVersionRequest(
                version_number=1,
                api_endpoint_id=987,
                body=VerifyVersionRequestBody(
                    networks=[ACTIVATION_NETWORK_STAGING],
                ),
            )
        )
        assert result == expected
        call_args = mock_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/api-definitions/v2/endpoints/987/versions/1/activate/verify"

    def test_404_not_found(self, mock_client):
        api_error = APIDefinitionsError(
            type="test.com/api-definitions/error-types/NOT-FOUND",
            title="Not Found",
            detail="Invalid version provided.",
            instance="TestInstance123",
            status=404,
            severity="ERROR",
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.verify_version(
                VerifyVersionRequest(
                    version_number=4,
                    api_endpoint_id=987,
                    body=VerifyVersionRequestBody(
                        networks=[ACTIVATION_NETWORK_STAGING],
                    ),
                )
            )
        assert exc_info.value.status == 404

    def test_incorrect_network(self, mock_client):
        with pytest.raises(ErrStructValidation):
            mock_client.verify_version(
                VerifyVersionRequest(
                    version_number=1,
                    api_endpoint_id=987,
                    body=VerifyVersionRequestBody(
                        networks=["TYPO"],
                    ),
                )
            )

    def test_missing_network(self, mock_client):
        with pytest.raises(ErrStructValidation):
            mock_client.verify_version(
                VerifyVersionRequest(
                    version_number=1,
                    api_endpoint_id=987,
                    body=VerifyVersionRequestBody(),
                )
            )


# ======================================================================
# TestActivateVersion -- mirrors Go TestActivateVersion
# ======================================================================


class TestActivateVersion:
    """Tests for Client.activate_version."""

    def test_200_ok(self, mock_client):
        response_body = '{"networks":["STAGING"],"notes":"some notes","notificationRecipients":["devteam@domain.com"]}'
        expected = json.loads(response_body)
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, response_body),
            expected,
        )
        result = mock_client.activate_version(
            ActivateVersionRequest(
                version_number=1,
                api_endpoint_id=987,
                body=ActivationRequestBody(
                    networks=[ACTIVATION_NETWORK_STAGING],
                    notes="some notes",
                    notification_recipients=["devteam@domain.com"],
                ),
            )
        )
        assert result == expected
        call_args = mock_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/api-definitions/v2/endpoints/987/versions/1/activate"

    def test_200_only_mandatory(self, mock_client):
        response_body = '{"networks":["PRODUCTION"],"notes":null,"notificationRecipients":null}'
        expected = json.loads(response_body)
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, response_body),
            expected,
        )
        result = mock_client.activate_version(
            ActivateVersionRequest(
                version_number=1,
                api_endpoint_id=987,
                body=ActivationRequestBody(
                    networks=[ACTIVATION_NETWORK_PRODUCTION],
                ),
            )
        )
        assert result == expected

    def test_400_already_active(self, mock_client):
        api_error = APIDefinitionsError(
            type="/api-definitions/error-types/endpoint-version-already-active",
            title="Version already active",
            detail="Version 1 of endpoint 'dxetest' is already active on STAGING.",
            status=400,
            endpoint_id=987,
            endpoint_name="dxetest",
            version_number=1,
            network="STAGING",
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.activate_version(
                ActivateVersionRequest(
                    version_number=1,
                    api_endpoint_id=987,
                    body=ActivationRequestBody(
                        networks=[ACTIVATION_NETWORK_STAGING],
                        notes="some notes",
                        notification_recipients=["devteam@domain.com"],
                    ),
                )
            )
        err = exc_info.value
        assert err.status == 400
        assert err.endpoint_id == 987
        assert err.endpoint_name == "dxetest"
        assert err.version_number == 1
        assert err.network == "STAGING"

    def test_404_not_found(self, mock_client):
        api_error = APIDefinitionsError(
            type="test.com/api-definitions/error-types/NOT-FOUND",
            title="Not Found",
            detail="Invalid version provided.",
            instance="TestInstance123",
            status=404,
            severity="ERROR",
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.activate_version(
                ActivateVersionRequest(
                    version_number=4,
                    api_endpoint_id=987,
                    body=ActivationRequestBody(
                        networks=[ACTIVATION_NETWORK_STAGING],
                    ),
                )
            )
        assert exc_info.value.status == 404

    def test_incorrect_network(self, mock_client):
        with pytest.raises(ErrStructValidation):
            mock_client.activate_version(
                ActivateVersionRequest(
                    version_number=1,
                    api_endpoint_id=987,
                    body=ActivationRequestBody(
                        networks=["TYPO"],
                    ),
                )
            )

    def test_missing_network(self, mock_client):
        with pytest.raises(ErrStructValidation):
            mock_client.activate_version(
                ActivateVersionRequest(
                    version_number=1,
                    api_endpoint_id=987,
                    body=ActivationRequestBody(),
                )
            )

    def test_incorrect_recipient(self, mock_client):
        with pytest.raises(ErrStructValidation):
            mock_client.activate_version(
                ActivateVersionRequest(
                    version_number=1,
                    api_endpoint_id=987,
                    body=ActivationRequestBody(
                        networks=[ACTIVATION_NETWORK_STAGING],
                        notification_recipients=["devteam"],
                    ),
                )
            )


# ======================================================================
# TestDeactivateVersion -- mirrors Go TestDeactivateVersion
# ======================================================================


class TestDeactivateVersion:
    """Tests for Client.deactivate_version."""

    def test_200_ok(self, mock_client):
        response_body = '{"networks":["STAGING"],"notes":"some notes","notificationRecipients":["devteam@domain.com"]}'
        expected = json.loads(response_body)
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, response_body),
            expected,
        )
        result = mock_client.deactivate_version(
            DeactivateVersionRequest(
                version_number=1,
                api_endpoint_id=987,
                body=ActivationRequestBody(
                    networks=[ACTIVATION_NETWORK_STAGING],
                    notes="some notes",
                    notification_recipients=["devteam@domain.com"],
                ),
            )
        )
        assert result == expected
        call_args = mock_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/api-definitions/v2/endpoints/987/versions/1/deactivate"

    def test_200_only_mandatory(self, mock_client):
        response_body = '{"networks":["PRODUCTION"],"notes":null,"notificationRecipients":null}'
        expected = json.loads(response_body)
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, response_body),
            expected,
        )
        result = mock_client.deactivate_version(
            DeactivateVersionRequest(
                version_number=1,
                api_endpoint_id=987,
                body=ActivationRequestBody(
                    networks=[ACTIVATION_NETWORK_PRODUCTION],
                ),
            )
        )
        assert result == expected

    def test_400_not_active(self, mock_client):
        api_error = APIDefinitionsError(
            type="/api-definitions/error-types/endpoint-version-not-active",
            title="Version not active",
            detail="Version 1 of endpoint 'dxetest' is not active on STAGING.",
            status=400,
            endpoint_id=987,
            endpoint_name="dxetest",
            version_number=1,
            network="STAGING",
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.deactivate_version(
                DeactivateVersionRequest(
                    version_number=1,
                    api_endpoint_id=987,
                    body=ActivationRequestBody(
                        networks=[ACTIVATION_NETWORK_STAGING],
                        notes="some notes",
                        notification_recipients=["devteam@domain.com"],
                    ),
                )
            )
        err = exc_info.value
        assert err.status == 400
        assert err.endpoint_id == 987
        assert err.endpoint_name == "dxetest"
        assert err.version_number == 1
        assert err.network == "STAGING"

    def test_404_not_found(self, mock_client):
        api_error = APIDefinitionsError(
            type="test.com/api-definitions/error-types/NOT-FOUND",
            title="Not Found",
            detail="Invalid version provided.",
            instance="TestInstance123",
            status=404,
            severity="ERROR",
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.deactivate_version(
                DeactivateVersionRequest(
                    version_number=4,
                    api_endpoint_id=987,
                    body=ActivationRequestBody(
                        networks=[ACTIVATION_NETWORK_STAGING],
                    ),
                )
            )
        assert exc_info.value.status == 404

    def test_incorrect_network(self, mock_client):
        with pytest.raises(ErrStructValidation):
            mock_client.deactivate_version(
                DeactivateVersionRequest(
                    version_number=1,
                    api_endpoint_id=987,
                    body=ActivationRequestBody(
                        networks=["TYP0"],
                    ),
                )
            )

    def test_incorrect_recipient(self, mock_client):
        with pytest.raises(ErrStructValidation):
            mock_client.deactivate_version(
                DeactivateVersionRequest(
                    version_number=1,
                    api_endpoint_id=987,
                    body=ActivationRequestBody(
                        networks=[ACTIVATION_NETWORK_STAGING],
                        notification_recipients=["devteam"],
                    ),
                )
            )


# ======================================================================
# TestSearchResourceOperations -- mirrors Go TestSearchResourceOperations
# ======================================================================


class TestSearchResourceOperations:
    """Tests for Client.search_resource_operations."""

    def test_200_ok(self, mock_client):
        fixture = load_fixture("search_resource_operations.json")
        response_body = json.dumps(fixture)
        mock_client._session.exec.return_value = (  # pylint: disable=protected-access
            mock_response(200, response_body),
            fixture,
        )
        result = mock_client.search_resource_operations()
        assert result == fixture
        call_args = mock_client._session.exec.call_args  # pylint: disable=protected-access
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/api-definitions/v2/search-operations"

    def test_403_unauthorized(self, mock_client):
        fixture = load_fixture("search_resource_operations_403.json")
        api_error = APIDefinitionsError(
            type=fixture.get("type", ""),
            title=fixture.get("title", ""),
            detail=fixture.get("detail", ""),
            status=403,
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.search_resource_operations()
        assert exc_info.value.status == 403

    def test_500_internal_server_error(self, mock_client):
        fixture = load_fixture("search_resource_operations_500.json")
        api_error = APIDefinitionsError(
            type=fixture.get("type", ""),
            title=fixture.get("title", ""),
            detail=fixture.get("detail", ""),
            status=500,
        )
        mock_client._session.exec.side_effect = api_error  # pylint: disable=protected-access
        with pytest.raises(APIDefinitionsError) as exc_info:
            mock_client.search_resource_operations()
        assert exc_info.value.status == 500
