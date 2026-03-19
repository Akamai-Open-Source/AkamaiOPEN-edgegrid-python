# pylint: disable=missing-function-docstring,too-many-lines,protected-access
# pylint: disable=too-many-arguments,too-many-positional-arguments,too-few-public-methods
"""Unit tests for Account Protection API client.

Mirrors all Go test scenarios from pkg/accountprotection/ test files:
- account_protection_test.go (TestClient: 2 scenarios)
- errors_test.go (TestJsonErrorUnmarshalling: 3, TestErrorError: 2, TestErrorIs: 12)
- protected_operation_test.go (CRUD: 28 scenarios)
- general_settings_test.go (GET/PUT: 8 scenarios)
- user_risk_response_strategy_test.go (GET/PUT: 7 scenarios)
- user_allow_list_id_test.go (GET/PUT/DELETE: 11 scenarios)

Total: 73 test scenarios
"""

import json

import pytest

from akamai.edgegrid.accountprotection.accountprotection import (
    AccountProtectionClient,
)
from akamai.edgegrid.accountprotection import models
from akamai.edgegrid.accountprotection.errors import Error, ErrStructValidation
from akamai.edgegrid.accountprotection.test.conftest import MockResponse


# ---------------------------------------------------------------------------
# Module-level test data (mirrors Go package-level testError variable)
# ---------------------------------------------------------------------------
_test_error = Error(type="a", title="b", detail="c", status_code=400)
_wrapped_error = ValueError("wrapped error")
_wrapped_error.__cause__ = _test_error


# ===================================================================
# TestClient — from account_protection_test.go (2 scenarios)
# ===================================================================


class TestClient:
    """Tests for AccountProtectionClient construction.

    Mirrors Go TestClient from account_protection_test.go.
    """

    def test_no_options_default(self, mock_session):
        client = AccountProtectionClient(mock_session)
        assert client._session is mock_session

    def test_with_session(self, mock_session):
        client = AccountProtectionClient(mock_session)
        assert client._session is mock_session


# ===================================================================
# TestJsonErrorUnmarshalling — from errors_test.go lines 17-78
# (3 scenarios)
# ===================================================================


class TestJsonErrorUnmarshalling:
    """Tests for error parsing of non-JSON responses.

    Mirrors Go TestJsonErrorUnmarshalling from errors_test.go.
    Response bodies are VERBATIM from Go test fixtures.
    """

    @pytest.mark.parametrize(
        "test_name, response_body, response_status,"
        " expected_type, expected_title, expected_detail,"
        " expected_status_code",
        [
            (
                "API failure with HTML response",
                "<HTML><HEAD>...</HEAD><BODY>...</BODY></HTML>",
                503,
                "",
                "Failed to unmarshal error body. Bot Manager API failed."
                " Check details for more information.",
                "<HTML><HEAD>...</HEAD><BODY>...</BODY></HTML>",
                503,
            ),
            (
                "API failure with plain text response",
                "Your request did not succeed as this operation has"
                " reached  the limit for your account. Please try"
                " after 2024-01-16T15:20:55.945Z",
                503,
                "",
                "Failed to unmarshal error body. Bot Manager API failed."
                " Check details for more information.",
                "Your request did not succeed as this operation has"
                " reached  the limit for your account. Please try"
                " after 2024-01-16T15:20:55.945Z",
                503,
            ),
            (
                "API failure with XML response",
                '<Root><Item id="1" name="Example" /></Root>',
                503,
                "",
                "Failed to unmarshal error body. Bot Manager API failed."
                " Check details for more information.",
                '<Root><Item id="1" name="Example" /></Root>',
                503,
            ),
        ],
    )
    def test_json_error_unmarshalling(
        self,
        mock_client,
        test_name,
        response_body,
        response_status,
        expected_type,
        expected_title,
        expected_detail,
        expected_status_code,
    ):
        mock_response = MockResponse(
            status_code=response_status, body=response_body
        )
        error = mock_client._parse_error(mock_response)
        assert error.type == expected_type, f"{test_name}: type mismatch"
        assert error.title == expected_title, f"{test_name}: title mismatch"
        assert error.detail == expected_detail, (
            f"{test_name}: detail mismatch"
        )
        assert error.status_code == expected_status_code, (
            f"{test_name}: status_code mismatch"
        )


# ===================================================================
# TestErrorError — from errors_test.go lines 80-123 (2 scenarios)
# ===================================================================


class TestErrorError:
    """Tests for Error.__str__() formatting.

    Mirrors Go TestErrorError from errors_test.go.
    Note: Space before ']' in child errors matches Go's strings.Join
    + ' ]' format exactly.
    """

    @pytest.mark.parametrize(
        "test_name, error, expected_string",
        [
            (
                "without errors",
                Error(type="a", title="b", detail="c", status_code=400),
                "Title: b; Type: a; Detail: c",
            ),
            (
                "with errors",
                Error(
                    type="parent-type",
                    title="parent-title",
                    detail="parent-detail",
                    status_code=400,
                    errors=[
                        Error(
                            type="child1-type",
                            title="child1-title",
                            detail="child1-detail",
                            status_code=401,
                        ),
                        Error(
                            type="child2-type",
                            title="child2-title",
                            detail="child2-detail",
                            status_code=402,
                        ),
                    ],
                ),
                "Title: parent-title; Type: parent-type;"
                " Detail: parent-detail: [child1-detail,"
                " child2-detail ]",
            ),
        ],
    )
    def test_error_error(self, test_name, error, expected_string):
        assert str(error) == expected_string, (
            f"{test_name}: str(error) mismatch"
        )


# ===================================================================
# TestErrorIs — from errors_test.go lines 125-236 (12 scenarios)
# ===================================================================


class TestErrorIs:
    """Tests for Error.is_equivalent() comparison.

    Mirrors Go TestErrorIs from errors_test.go.
    """

    @pytest.mark.parametrize(
        "test_name, err, target, expected",
        [
            (
                "unwrap fail",
                Error(),
                ValueError("NOPE"),
                False,
            ),
            (
                "unwrap ok",
                _test_error,
                _wrapped_error,
                True,
            ),
            ("empty", Error(), Error(), True),
            ("same pointer", _test_error, _test_error, True),
            (
                "all fields equal",
                _test_error,
                Error(type="a", title="b", detail="c", status_code=400),
                True,
            ),
            (
                "same child errors list",
                Error(errors=[Error(type="a")]),
                Error(errors=[Error(type="a")]),
                True,
            ),
            (
                "child errors list with different type",
                Error(errors=[Error(type="a")]),
                Error(errors=[Error(type="notA")]),
                True,
            ),
            (
                "child errors list with different detail",
                Error(errors=[Error(detail="a")]),
                Error(errors=[Error(detail="notA")]),
                False,
            ),
            (
                "different type",
                Error(type="a"),
                Error(type="notA"),
                False,
            ),
            (
                "different title",
                Error(title="b"),
                Error(title="notB"),
                False,
            ),
            (
                "different detail",
                Error(detail="c"),
                Error(detail="notC"),
                False,
            ),
            (
                "different status code",
                Error(status_code=400),
                Error(status_code=401),
                False,
            ),
        ],
    )
    def test_error_is(self, test_name, err, target, expected):
        assert err.is_equivalent(target) == expected, (
            f"{test_name}: is_equivalent mismatch"
        )


# ===================================================================
# TestListProtectedOperations — from protected_operation_test.go
# lines 16-148 (5 scenarios: 1 success + 1 error + 3 validation)
# ===================================================================

# Verbatim response body constants from Go test fixtures
_LIST_OPS_RESPONSE_BODY = json.dumps({
    "metadata": {
        "configId": 43253,
        "configVersion": 15,
        "securityPolicyId": "AAAA_81230",
    },
    "operations": [
        {
            "operationId": "b85e3eaa-d334-466d-857e-33308ce416be",
            "testKey": "testValue1",
        },
        {
            "operationId": "69acad64-7459-4c1d-9bad-672600150127",
            "testKey": "testValue2",
        },
        {
            "operationId": "cc9c3f89-e179-4892-89cf-d5e623ba9dc7",
            "testKey": "testValue3",
        },
        {
            "operationId": "10c54ea3-e3cb-4fc0-b0e0-fa3658aebd7b",
            "testKey": "testValue4",
        },
        {
            "operationId": "4d64d85a-a07f-485a-bbac-24c60658a1b8",
            "testKey": "testValue5",
        },
    ],
})

_ERROR_FETCHING_DATA = json.dumps({
    "type": "internal_error",
    "title": "Internal Server Error",
    "detail": "Error fetching data",
    "status": 500,
})

_ERROR_CREATING_DATA = json.dumps({
    "type": "internal_error",
    "title": "Internal Server Error",
    "detail": "Error creating data",
    "status": 500,
})

_ERROR_CREATING_ZONE = json.dumps({
    "type": "internal_error",
    "title": "Internal Server Error",
    "detail": "Error creating zone",
    "status": 500,
})

_ERROR_DELETING_MATCH_TARGET = json.dumps({
    "type": "internal_error",
    "title": "Internal Server Error",
    "detail": "Error deleting match target",
    "status": 500,
})

_ERROR_FETCHING_MATCH_TARGET = json.dumps({
    "type": "internal_error",
    "title": "Internal Server Error",
    "detail": "Error fetching match target",
    "status": 500,
})


class TestListProtectedOperations:
    """Tests for list_protected_operations.

    Mirrors Go Test_ListProtectedOperations from
    protected_operation_test.go lines 16-148.
    """

    def test_200_ok(self, mock_session, mock_client):
        body_data = json.loads(_LIST_OPS_RESPONSE_BODY)
        mock_session.exec.return_value = (
            MockResponse(status_code=200, body=_LIST_OPS_RESPONSE_BODY),
            body_data,
        )
        result = mock_client.list_protected_operations(
            models.ListProtectedOperationsRequest(
                config_id=43253,
                version=15,
                security_policy_id="AAAA_81230",
            )
        )
        assert isinstance(result, models.ListProtectedOperationsResponse)
        assert result.metadata.config_id == 43253
        assert result.metadata.config_version == 15
        assert result.metadata.security_policy_id == "AAAA_81230"
        assert len(result.operations) == 5
        assert result.operations[0]["operationId"] == (
            "b85e3eaa-d334-466d-857e-33308ce416be"
        )
        assert result.operations[4]["operationId"] == (
            "4d64d85a-a07f-485a-bbac-24c60658a1b8"
        )
        args, _ = mock_session.exec.call_args
        assert args[0] == "GET"
        assert args[1] == (
            "/appsec/v1/configs/43253/versions/15/security-policies"
            "/AAAA_81230/transactional-endpoints/account-protection"
        )

    def test_500_internal_server_error(self, mock_session, mock_client):
        mock_session.exec.return_value = (
            MockResponse(status_code=500, body=_ERROR_FETCHING_DATA),
            None,
        )
        with pytest.raises(Error) as exc_info:
            mock_client.list_protected_operations(
                models.ListProtectedOperationsRequest(
                    config_id=43253,
                    version=15,
                    security_policy_id="AAAA_81230",
                )
            )
        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error fetching data"
        assert err.status_code == 500
        args, _ = mock_session.exec.call_args
        assert args[0] == "GET"

    @pytest.mark.parametrize(
        "test_name, params, expected_field",
        [
            (
                "Missing ConfigID",
                models.ListProtectedOperationsRequest(
                    version=15,
                    security_policy_id="AAAA_81230",
                ),
                "ConfigID",
            ),
            (
                "Missing Version",
                models.ListProtectedOperationsRequest(
                    config_id=43253,
                    security_policy_id="AAAA_81230",
                ),
                "Version",
            ),
            (
                "Missing SecurityPolicyID",
                models.ListProtectedOperationsRequest(
                    config_id=43253,
                    version=15,
                ),
                "SecurityPolicyID",
            ),
        ],
    )
    def test_validation_error(
        self, mock_session, mock_client, test_name, params, expected_field
    ):
        with pytest.raises(ValueError) as exc_info:
            mock_client.list_protected_operations(params)
        assert ErrStructValidation in str(exc_info.value), (
            f"{test_name}: missing ErrStructValidation"
        )
        assert expected_field in str(exc_info.value), (
            f"{test_name}: missing {expected_field}"
        )
        mock_session.exec.assert_not_called()


# ===================================================================
# TestGetProtectedOperationByID — from protected_operation_test.go
# lines 150-279 (5 scenarios: 1 success + 1 error + 3 validation)
# ===================================================================


class TestGetProtectedOperationByID:
    """Tests for get_protected_operation_by_id.

    Mirrors Go Test_GetProtectedOperationByID from
    protected_operation_test.go lines 150-279.
    """

    def test_200_ok(self, mock_session, mock_client):
        # Verbatim Go responseBody: single operation object.
        # Python _build_list_response wraps it in
        # ListProtectedOperationsResponse (differs from Go's raw map).
        body_data = {
            "operationId": "cc9c3f89-e179-4892-89cf-d5e623ba9dc7",
            "testKey": "testValue3",
        }
        body_str = json.dumps(body_data)
        mock_session.exec.return_value = (
            MockResponse(status_code=200, body=body_str),
            body_data,
        )
        result = mock_client.get_protected_operation_by_id(
            models.GetProtectedOperationByIDRequest(
                config_id=43253,
                version=15,
                security_policy_id="AAAA_81230",
                operation_id="cc9c3f89-e179-4892-89cf-d5e623ba9dc7",
            )
        )
        # Python client wraps in ListProtectedOperationsResponse
        assert isinstance(result, models.ListProtectedOperationsResponse)
        args, _ = mock_session.exec.call_args
        assert args[0] == "GET"
        assert args[1] == (
            "/appsec/v1/configs/43253/versions/15/security-policies"
            "/AAAA_81230/transactional-endpoints/account-protection"
            "/cc9c3f89-e179-4892-89cf-d5e623ba9dc7"
        )

    def test_500_internal_server_error(self, mock_session, mock_client):
        mock_session.exec.return_value = (
            MockResponse(status_code=500, body=_ERROR_FETCHING_DATA),
            None,
        )
        with pytest.raises(Error) as exc_info:
            mock_client.get_protected_operation_by_id(
                models.GetProtectedOperationByIDRequest(
                    config_id=43253,
                    version=15,
                    security_policy_id="AAAA_81230",
                    operation_id=(
                        "cc9c3f89-e179-4892-89cf-d5e623ba9dc7"
                    ),
                )
            )
        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error fetching data"
        assert err.status_code == 500

    @pytest.mark.parametrize(
        "test_name, params, expected_field",
        [
            (
                "Missing ConfigID",
                models.GetProtectedOperationByIDRequest(
                    version=15,
                    security_policy_id="AAAA_81230",
                    operation_id=(
                        "cc9c3f89-e179-4892-89cf-d5e623ba9dc7"
                    ),
                ),
                "ConfigID",
            ),
            (
                "Missing Version",
                models.GetProtectedOperationByIDRequest(
                    config_id=43253,
                    security_policy_id="AAAA_81230",
                    operation_id=(
                        "cc9c3f89-e179-4892-89cf-d5e623ba9dc7"
                    ),
                ),
                "Version",
            ),
            (
                "Missing SecurityPolicyID",
                models.GetProtectedOperationByIDRequest(
                    config_id=43253,
                    version=15,
                    operation_id=(
                        "cc9c3f89-e179-4892-89cf-d5e623ba9dc7"
                    ),
                ),
                "SecurityPolicyID",
            ),
        ],
    )
    def test_validation_error(
        self, mock_session, mock_client, test_name, params, expected_field
    ):
        with pytest.raises(ValueError) as exc_info:
            mock_client.get_protected_operation_by_id(params)
        assert ErrStructValidation in str(exc_info.value), (
            f"{test_name}: missing ErrStructValidation"
        )
        assert expected_field in str(exc_info.value), (
            f"{test_name}: missing {expected_field}"
        )
        mock_session.exec.assert_not_called()


# ===================================================================
# TestCreateProtectedOperations — from protected_operation_test.go
# lines 281-407 (5 scenarios: 1 success + 1 error + 3 validation)
# ===================================================================

_CREATE_OPS_RESPONSE_BODY = json.dumps({
    "metadata": {
        "configId": 43253,
        "configVersion": 15,
        "securityPolicyId": "AAAA_81230",
    },
    "operations": [
        {
            "operationId": "cc9c3f89-e179-4892-89cf-d5e623ba9dc7",
            "testKey": "testValue3",
        },
    ],
})


class TestCreateProtectedOperations:
    """Tests for create_protected_operations.

    Mirrors Go Test_CreateProtectedOperations from
    protected_operation_test.go lines 281-407.
    """

    def test_201_created(self, mock_session, mock_client):
        body_data = json.loads(_CREATE_OPS_RESPONSE_BODY)
        mock_session.exec.return_value = (
            MockResponse(status_code=201, body=_CREATE_OPS_RESPONSE_BODY),
            body_data,
        )
        result = mock_client.create_protected_operations(
            models.CreateProtectedOperationsRequest(
                config_id=43253,
                version=15,
                security_policy_id="AAAA_81230",
                json_payload='{"operations": [{"testKey":"testValue3"}]}',
            )
        )
        assert isinstance(result, models.ListProtectedOperationsResponse)
        assert result.metadata.config_id == 43253
        assert result.metadata.config_version == 15
        assert result.metadata.security_policy_id == "AAAA_81230"
        assert len(result.operations) == 1
        assert result.operations[0]["operationId"] == (
            "cc9c3f89-e179-4892-89cf-d5e623ba9dc7"
        )
        args, _ = mock_session.exec.call_args
        assert args[0] == "POST"
        assert args[1] == (
            "/appsec/v1/configs/43253/versions/15/security-policies"
            "/AAAA_81230/transactional-endpoints/account-protection"
        )

    def test_500_internal_server_error(self, mock_session, mock_client):
        mock_session.exec.return_value = (
            MockResponse(status_code=500, body=_ERROR_CREATING_DATA),
            None,
        )
        with pytest.raises(Error) as exc_info:
            mock_client.create_protected_operations(
                models.CreateProtectedOperationsRequest(
                    config_id=43253,
                    version=15,
                    security_policy_id="AAAA_81230",
                    json_payload=(
                        '{"operations": [{"testKey":"testValue3"}]}'
                    ),
                )
            )
        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error creating data"
        assert err.status_code == 500

    @pytest.mark.parametrize(
        "test_name, params, expected_field",
        [
            (
                "Missing ConfigID",
                models.CreateProtectedOperationsRequest(
                    version=15,
                    security_policy_id="AAAA_81230",
                    json_payload=(
                        '{"operations": [{"testKey":"testValue3"}]}'
                    ),
                ),
                "ConfigID",
            ),
            (
                "Missing Version",
                models.CreateProtectedOperationsRequest(
                    config_id=43253,
                    security_policy_id="AAAA_81230",
                    json_payload=(
                        '{"operations": [{"testKey":"testValue3"}]}'
                    ),
                ),
                "Version",
            ),
            (
                "Missing JsonPayload",
                models.CreateProtectedOperationsRequest(
                    config_id=43253,
                    version=15,
                    security_policy_id="AAAA_81230",
                ),
                "JsonPayload",
            ),
        ],
    )
    def test_validation_error(
        self, mock_session, mock_client, test_name, params, expected_field
    ):
        with pytest.raises(ValueError) as exc_info:
            mock_client.create_protected_operations(params)
        assert ErrStructValidation in str(exc_info.value), (
            f"{test_name}: missing ErrStructValidation"
        )
        assert expected_field in str(exc_info.value), (
            f"{test_name}: missing {expected_field}"
        )
        mock_session.exec.assert_not_called()


# ===================================================================
# TestUpdateProtectedOperation — from protected_operation_test.go
# lines 409-545 (7 scenarios: 1 success + 1 error + 5 validation)
# ===================================================================

_UPDATE_OP_JSON_PAYLOAD = (
    '{"operationId":"cc9c3f89-e179-4892-89cf-d5e623ba9dc7",'
    ' "testKey":"testValue3"}'
)


class TestUpdateProtectedOperation:
    """Tests for update_protected_operation.

    Mirrors Go Test_UpdateProtectedOperation from
    protected_operation_test.go lines 409-545.
    Note: Version=10 for this endpoint.
    """

    def test_200_success(self, mock_session, mock_client):
        body_data = {
            "operationId": "cc9c3f89-e179-4892-89cf-d5e623ba9dc7",
            "testKey": "testValue3",
        }
        body_str = json.dumps(body_data)
        mock_session.exec.return_value = (
            MockResponse(status_code=200, body=body_str),
            body_data,
        )
        result = mock_client.update_protected_operation(
            models.UpdateProtectedOperationRequest(
                config_id=43253,
                version=10,
                security_policy_id="AAAA_81230",
                operation_id="cc9c3f89-e179-4892-89cf-d5e623ba9dc7",
                json_payload=_UPDATE_OP_JSON_PAYLOAD,
            )
        )
        assert result == {
            "operationId": "cc9c3f89-e179-4892-89cf-d5e623ba9dc7",
            "testKey": "testValue3",
        }
        args, _ = mock_session.exec.call_args
        assert args[0] == "PUT"
        assert args[1] == (
            "/appsec/v1/configs/43253/versions/10/security-policies"
            "/AAAA_81230/transactional-endpoints/account-protection"
            "/cc9c3f89-e179-4892-89cf-d5e623ba9dc7"
        )

    def test_500_internal_server_error(self, mock_session, mock_client):
        mock_session.exec.return_value = (
            MockResponse(status_code=500, body=_ERROR_CREATING_ZONE),
            None,
        )
        with pytest.raises(Error) as exc_info:
            mock_client.update_protected_operation(
                models.UpdateProtectedOperationRequest(
                    config_id=43253,
                    version=10,
                    security_policy_id="AAAA_81230",
                    operation_id=(
                        "cc9c3f89-e179-4892-89cf-d5e623ba9dc7"
                    ),
                    json_payload=_UPDATE_OP_JSON_PAYLOAD,
                )
            )
        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error creating zone"
        assert err.status_code == 500

    @pytest.mark.parametrize(
        "test_name, params, expected_field",
        [
            (
                "Missing ConfigID",
                models.UpdateProtectedOperationRequest(
                    version=10,
                    security_policy_id="AAAA_81230",
                    operation_id=(
                        "cc9c3f89-e179-4892-89cf-d5e623ba9dc7"
                    ),
                    json_payload=_UPDATE_OP_JSON_PAYLOAD,
                ),
                "ConfigID",
            ),
            (
                "Missing Version",
                models.UpdateProtectedOperationRequest(
                    config_id=43253,
                    security_policy_id="AAAA_81230",
                    operation_id=(
                        "cc9c3f89-e179-4892-89cf-d5e623ba9dc7"
                    ),
                    json_payload=_UPDATE_OP_JSON_PAYLOAD,
                ),
                "Version",
            ),
            (
                "Missing SecurityPolicyID",
                models.UpdateProtectedOperationRequest(
                    config_id=43253,
                    version=10,
                    operation_id=(
                        "cc9c3f89-e179-4892-89cf-d5e623ba9dc7"
                    ),
                    json_payload=_UPDATE_OP_JSON_PAYLOAD,
                ),
                "SecurityPolicyID",
            ),
            (
                "Missing JsonPayload",
                models.UpdateProtectedOperationRequest(
                    config_id=43253,
                    version=10,
                    security_policy_id="AAAA_81230",
                    operation_id=(
                        "cc9c3f89-e179-4892-89cf-d5e623ba9dc7"
                    ),
                ),
                "JsonPayload",
            ),
            (
                "Missing OperationID",
                models.UpdateProtectedOperationRequest(
                    config_id=43253,
                    version=10,
                    security_policy_id="AAAA_81230",
                    json_payload=_UPDATE_OP_JSON_PAYLOAD,
                ),
                "OperationID",
            ),
        ],
    )
    def test_validation_error(
        self, mock_session, mock_client, test_name, params, expected_field
    ):
        with pytest.raises(ValueError) as exc_info:
            mock_client.update_protected_operation(params)
        assert ErrStructValidation in str(exc_info.value), (
            f"{test_name}: missing ErrStructValidation"
        )
        assert expected_field in str(exc_info.value), (
            f"{test_name}: missing {expected_field}"
        )
        mock_session.exec.assert_not_called()


# ===================================================================
# TestRemoveProtectedOperation — from protected_operation_test.go
# lines 547-661 (6 scenarios: 1 success + 1 error + 4 validation)
# ===================================================================


class TestRemoveProtectedOperation:
    """Tests for remove_protected_operation.

    Mirrors Go Test_RemoveProtectedOperation from
    protected_operation_test.go lines 547-661.
    Note: Version=10, DELETE returns 204 No Content.
    """

    def test_204_success(self, mock_session, mock_client):
        mock_session.exec.return_value = (
            MockResponse(status_code=204, body=""),
            None,
        )
        result = mock_client.remove_protected_operation(
            models.RemoveProtectedOperationRequest(
                config_id=43253,
                version=10,
                security_policy_id="AAAA_81230",
                operation_id="cc9c3f89-e179-4892-89cf-d5e623ba9dc7",
            )
        )
        assert result is None
        args, _ = mock_session.exec.call_args
        assert args[0] == "DELETE"
        assert args[1] == (
            "/appsec/v1/configs/43253/versions/10/security-policies"
            "/AAAA_81230/transactional-endpoints/account-protection"
            "/cc9c3f89-e179-4892-89cf-d5e623ba9dc7"
        )

    def test_500_internal_server_error(self, mock_session, mock_client):
        mock_session.exec.return_value = (
            MockResponse(
                status_code=500, body=_ERROR_DELETING_MATCH_TARGET
            ),
            None,
        )
        with pytest.raises(Error) as exc_info:
            mock_client.remove_protected_operation(
                models.RemoveProtectedOperationRequest(
                    config_id=43253,
                    version=10,
                    security_policy_id="AAAA_81230",
                    operation_id=(
                        "cc9c3f89-e179-4892-89cf-d5e623ba9dc7"
                    ),
                )
            )
        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error deleting match target"
        assert err.status_code == 500

    @pytest.mark.parametrize(
        "test_name, params, expected_field",
        [
            (
                "Missing ConfigID",
                models.RemoveProtectedOperationRequest(
                    version=10,
                    security_policy_id="AAAA_81230",
                    operation_id=(
                        "cc9c3f89-e179-4892-89cf-d5e623ba9dc7"
                    ),
                ),
                "ConfigID",
            ),
            (
                "Missing Version",
                models.RemoveProtectedOperationRequest(
                    config_id=43253,
                    security_policy_id="AAAA_81230",
                    operation_id=(
                        "cc9c3f89-e179-4892-89cf-d5e623ba9dc7"
                    ),
                ),
                "Version",
            ),
            (
                "Missing SecurityPolicyID",
                models.RemoveProtectedOperationRequest(
                    config_id=43253,
                    version=10,
                    operation_id=(
                        "cc9c3f89-e179-4892-89cf-d5e623ba9dc7"
                    ),
                ),
                "SecurityPolicyID",
            ),
            (
                "Missing OperationID",
                models.RemoveProtectedOperationRequest(
                    config_id=43253,
                    version=10,
                    security_policy_id="AAAA_81230",
                ),
                "OperationID",
            ),
        ],
    )
    def test_validation_error(
        self, mock_session, mock_client, test_name, params, expected_field
    ):
        with pytest.raises(ValueError) as exc_info:
            mock_client.remove_protected_operation(params)
        assert ErrStructValidation in str(exc_info.value), (
            f"{test_name}: missing ErrStructValidation"
        )
        assert expected_field in str(exc_info.value), (
            f"{test_name}: missing {expected_field}"
        )
        mock_session.exec.assert_not_called()


# ===================================================================
# TestGetGeneralSettings — from general_settings_test.go
# lines 16-81 (2 scenarios: 1 success + 1 error)
# ===================================================================

_SIMPLE_RESPONSE_BODY = json.dumps({"testKey": "testValue3"})


class TestGetGeneralSettings:
    """Tests for get_general_settings.

    Mirrors Go Test_GetGeneralSettings from
    general_settings_test.go lines 16-81.
    """

    def test_200_ok(self, mock_session, mock_client):
        body_data = {"testKey": "testValue3"}
        mock_session.exec.return_value = (
            MockResponse(status_code=200, body=_SIMPLE_RESPONSE_BODY),
            body_data,
        )
        result = mock_client.get_general_settings(
            models.GetGeneralSettingsRequest(
                config_id=43253,
                version=15,
                security_policy_id="AAAA_81230",
            )
        )
        assert result == {"testKey": "testValue3"}
        args, _ = mock_session.exec.call_args
        assert args[0] == "GET"
        assert args[1] == (
            "/appsec/v1/configs/43253/versions/15/security-policies"
            "/AAAA_81230/account-protection-settings"
        )

    def test_500_internal_server_error(self, mock_session, mock_client):
        mock_session.exec.return_value = (
            MockResponse(
                status_code=500, body=_ERROR_FETCHING_MATCH_TARGET
            ),
            None,
        )
        with pytest.raises(Error) as exc_info:
            mock_client.get_general_settings(
                models.GetGeneralSettingsRequest(
                    config_id=43253,
                    version=15,
                    security_policy_id="AAAA_81230",
                )
            )
        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error fetching match target"
        assert err.status_code == 500


# ===================================================================
# TestUpsertGeneralSettings — from general_settings_test.go
# lines 83-199 (6 scenarios: 1 success + 1 error + 4 validation)
# ===================================================================


class TestUpsertGeneralSettings:
    """Tests for upsert_general_settings.

    Mirrors Go Test_UpdateAccountProtectionGeneralSettings from
    general_settings_test.go lines 83-199.
    """

    def test_200_success(self, mock_session, mock_client):
        body_data = {"testKey": "testValue3"}
        mock_session.exec.return_value = (
            MockResponse(status_code=200, body=_SIMPLE_RESPONSE_BODY),
            body_data,
        )
        result = mock_client.upsert_general_settings(
            models.UpsertGeneralSettingsRequest(
                config_id=43253,
                version=15,
                security_policy_id="AAAA_81230",
                json_payload='{"testKey":"testValue3"}',
            )
        )
        assert result == {"testKey": "testValue3"}
        args, _ = mock_session.exec.call_args
        assert args[0] == "PUT"
        assert args[1] == (
            "/appsec/v1/configs/43253/versions/15/security-policies"
            "/AAAA_81230/account-protection-settings"
        )

    def test_500_internal_server_error(self, mock_session, mock_client):
        mock_session.exec.return_value = (
            MockResponse(status_code=500, body=_ERROR_CREATING_ZONE),
            None,
        )
        with pytest.raises(Error) as exc_info:
            mock_client.upsert_general_settings(
                models.UpsertGeneralSettingsRequest(
                    config_id=43253,
                    version=15,
                    security_policy_id="AAAA_81230",
                    json_payload='{"testKey":"testValue3"}',
                )
            )
        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error creating zone"
        assert err.status_code == 500

    @pytest.mark.parametrize(
        "test_name, params, expected_field",
        [
            (
                "Missing ConfigID",
                models.UpsertGeneralSettingsRequest(
                    version=15,
                    security_policy_id="AAAA_81230",
                ),
                "ConfigID",
            ),
            (
                "Missing Version",
                models.UpsertGeneralSettingsRequest(
                    config_id=43253,
                    security_policy_id="AAAA_81230",
                ),
                "Version",
            ),
            (
                "Missing SecurityPolicyID",
                models.UpsertGeneralSettingsRequest(
                    config_id=43253,
                    version=15,
                ),
                "SecurityPolicyID",
            ),
            (
                "Missing JsonPayload",
                models.UpsertGeneralSettingsRequest(
                    config_id=43253,
                    version=15,
                    security_policy_id="AAAA_81230",
                ),
                "JsonPayload",
            ),
        ],
    )
    def test_validation_error(
        self, mock_session, mock_client, test_name, params, expected_field
    ):
        with pytest.raises(ValueError) as exc_info:
            mock_client.upsert_general_settings(params)
        assert ErrStructValidation in str(exc_info.value), (
            f"{test_name}: missing ErrStructValidation"
        )
        assert expected_field in str(exc_info.value), (
            f"{test_name}: missing {expected_field}"
        )
        mock_session.exec.assert_not_called()


# ===================================================================
# TestGetUserRiskResponseStrategy —
# from user_risk_response_strategy_test.go
# lines 16-79 (2 scenarios: 1 success + 1 error)
# ===================================================================


class TestGetUserRiskResponseStrategy:
    """Tests for get_user_risk_response_strategy.

    Mirrors Go Test_GetUserRiskResponseStrategy from
    user_risk_response_strategy_test.go lines 16-79.
    Note: No SecurityPolicyID — only ConfigID and Version.
    """

    def test_200_ok(self, mock_session, mock_client):
        body_data = {"testKey": "testValue3"}
        mock_session.exec.return_value = (
            MockResponse(status_code=200, body=_SIMPLE_RESPONSE_BODY),
            body_data,
        )
        result = mock_client.get_user_risk_response_strategy(
            models.GetUserRiskResponseStrategyRequest(
                config_id=43253,
                version=15,
            )
        )
        assert result == {"testKey": "testValue3"}
        args, _ = mock_session.exec.call_args
        assert args[0] == "GET"
        assert args[1] == (
            "/appsec/v1/configs/43253/versions/15/advanced-settings"
            "/account-protection/user-risk-response-strategy"
        )

    def test_500_internal_server_error(self, mock_session, mock_client):
        mock_session.exec.return_value = (
            MockResponse(
                status_code=500, body=_ERROR_FETCHING_MATCH_TARGET
            ),
            None,
        )
        with pytest.raises(Error) as exc_info:
            mock_client.get_user_risk_response_strategy(
                models.GetUserRiskResponseStrategyRequest(
                    config_id=43253,
                    version=15,
                )
            )
        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error fetching match target"
        assert err.status_code == 500


# ===================================================================
# TestUpsertUserRiskResponseStrategy —
# from user_risk_response_strategy_test.go
# lines 81-181 (5 scenarios: 1 success + 1 error + 3 validation)
# ===================================================================


class TestUpsertUserRiskResponseStrategy:
    """Tests for upsert_user_risk_response_strategy.

    Mirrors Go Test_UpdateUserRiskResponseStrategy from
    user_risk_response_strategy_test.go lines 81-181.
    """

    def test_200_success(self, mock_session, mock_client):
        body_data = {"testKey": "testValue3"}
        mock_session.exec.return_value = (
            MockResponse(status_code=200, body=_SIMPLE_RESPONSE_BODY),
            body_data,
        )
        result = mock_client.upsert_user_risk_response_strategy(
            models.UpsertUserRiskResponseStrategyRequest(
                config_id=43253,
                version=15,
                json_payload='{"testKey":"testValue3"}',
            )
        )
        assert result == {"testKey": "testValue3"}
        args, _ = mock_session.exec.call_args
        assert args[0] == "PUT"
        assert args[1] == (
            "/appsec/v1/configs/43253/versions/15/advanced-settings"
            "/account-protection/user-risk-response-strategy"
        )

    def test_500_internal_server_error(self, mock_session, mock_client):
        mock_session.exec.return_value = (
            MockResponse(status_code=500, body=_ERROR_CREATING_ZONE),
            None,
        )
        with pytest.raises(Error) as exc_info:
            mock_client.upsert_user_risk_response_strategy(
                models.UpsertUserRiskResponseStrategyRequest(
                    config_id=43253,
                    version=15,
                    json_payload='{"testKey":"testValue3"}',
                )
            )
        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error creating zone"
        assert err.status_code == 500

    @pytest.mark.parametrize(
        "test_name, params, expected_field",
        [
            (
                "Missing ConfigID",
                models.UpsertUserRiskResponseStrategyRequest(
                    version=15,
                ),
                "ConfigID",
            ),
            (
                "Missing Version",
                models.UpsertUserRiskResponseStrategyRequest(
                    config_id=43253,
                ),
                "Version",
            ),
            (
                "Missing JsonPayload",
                models.UpsertUserRiskResponseStrategyRequest(
                    config_id=43253,
                    version=15,
                ),
                "JsonPayload",
            ),
        ],
    )
    def test_validation_error(
        self, mock_session, mock_client, test_name, params, expected_field
    ):
        with pytest.raises(ValueError) as exc_info:
            mock_client.upsert_user_risk_response_strategy(params)
        assert ErrStructValidation in str(exc_info.value), (
            f"{test_name}: missing ErrStructValidation"
        )
        assert expected_field in str(exc_info.value), (
            f"{test_name}: missing {expected_field}"
        )
        mock_session.exec.assert_not_called()


# ===================================================================
# TestGetUserAllowListID — from user_allow_list_id_test.go
# lines 16-79 (2 scenarios: 1 success + 1 error)
# ===================================================================


class TestGetUserAllowListID:
    """Tests for get_user_allow_list_id.

    Mirrors Go Test_GetUserAllowListID from
    user_allow_list_id_test.go lines 16-79.
    Note: No SecurityPolicyID — only ConfigID and Version.
    """

    def test_200_ok(self, mock_session, mock_client):
        body_data = {"testKey": "testValue3"}
        mock_session.exec.return_value = (
            MockResponse(status_code=200, body=_SIMPLE_RESPONSE_BODY),
            body_data,
        )
        result = mock_client.get_user_allow_list_id(
            models.GetUserAllowListIDRequest(
                config_id=43253,
                version=15,
            )
        )
        assert result == {"testKey": "testValue3"}
        args, _ = mock_session.exec.call_args
        assert args[0] == "GET"
        assert args[1] == (
            "/appsec/v1/configs/43253/versions/15/advanced-settings"
            "/account-protection/user-allow-list-id"
        )

    def test_500_internal_server_error(self, mock_session, mock_client):
        mock_session.exec.return_value = (
            MockResponse(
                status_code=500, body=_ERROR_FETCHING_MATCH_TARGET
            ),
            None,
        )
        with pytest.raises(Error) as exc_info:
            mock_client.get_user_allow_list_id(
                models.GetUserAllowListIDRequest(
                    config_id=43253,
                    version=15,
                )
            )
        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error fetching match target"
        assert err.status_code == 500


# ===================================================================
# TestUpsertUserAllowListID — from user_allow_list_id_test.go
# lines 81-181 (5 scenarios: 1 success + 1 error + 3 validation)
# ===================================================================


class TestUpsertUserAllowListID:
    """Tests for upsert_user_allow_list_id.

    Mirrors Go Test_UpsertUserAllowListID from
    user_allow_list_id_test.go lines 81-181.
    """

    def test_200_success(self, mock_session, mock_client):
        body_data = {"testKey": "testValue3"}
        mock_session.exec.return_value = (
            MockResponse(status_code=200, body=_SIMPLE_RESPONSE_BODY),
            body_data,
        )
        result = mock_client.upsert_user_allow_list_id(
            models.UpsertUserAllowListIDRequest(
                config_id=43253,
                version=15,
                json_payload='{"testKey":"testValue3"}',
            )
        )
        assert result == {"testKey": "testValue3"}
        args, _ = mock_session.exec.call_args
        assert args[0] == "PUT"
        assert args[1] == (
            "/appsec/v1/configs/43253/versions/15/advanced-settings"
            "/account-protection/user-allow-list-id"
        )

    def test_500_internal_server_error(self, mock_session, mock_client):
        mock_session.exec.return_value = (
            MockResponse(status_code=500, body=_ERROR_CREATING_ZONE),
            None,
        )
        with pytest.raises(Error) as exc_info:
            mock_client.upsert_user_allow_list_id(
                models.UpsertUserAllowListIDRequest(
                    config_id=43253,
                    version=15,
                    json_payload='{"testKey":"testValue3"}',
                )
            )
        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error creating zone"
        assert err.status_code == 500

    @pytest.mark.parametrize(
        "test_name, params, expected_field",
        [
            (
                "Missing ConfigID",
                models.UpsertUserAllowListIDRequest(
                    version=15,
                ),
                "ConfigID",
            ),
            (
                "Missing Version",
                models.UpsertUserAllowListIDRequest(
                    config_id=43253,
                ),
                "Version",
            ),
            (
                "Missing JsonPayload",
                models.UpsertUserAllowListIDRequest(
                    config_id=43253,
                    version=15,
                ),
                "JsonPayload",
            ),
        ],
    )
    def test_validation_error(
        self, mock_session, mock_client, test_name, params, expected_field
    ):
        with pytest.raises(ValueError) as exc_info:
            mock_client.upsert_user_allow_list_id(params)
        assert ErrStructValidation in str(exc_info.value), (
            f"{test_name}: missing ErrStructValidation"
        )
        assert expected_field in str(exc_info.value), (
            f"{test_name}: missing {expected_field}"
        )
        mock_session.exec.assert_not_called()


# ===================================================================
# TestDeleteUserAllowListID — from user_allow_list_id_test.go
# lines 183-265 (4 scenarios: 1 success + 1 error + 2 validation)
# ===================================================================


class TestDeleteUserAllowListID:
    """Tests for delete_user_allow_list_id.

    Mirrors Go Test_DeleteUserAllowListID from
    user_allow_list_id_test.go lines 183-265.
    DELETE returns 204 No Content.
    """

    def test_204_success(self, mock_session, mock_client):
        mock_session.exec.return_value = (
            MockResponse(status_code=204, body=""),
            None,
        )
        result = mock_client.delete_user_allow_list_id(
            models.DeleteUserAllowListIDRequest(
                config_id=43253,
                version=15,
            )
        )
        assert result is None
        args, _ = mock_session.exec.call_args
        assert args[0] == "DELETE"
        assert args[1] == (
            "/appsec/v1/configs/43253/versions/15/advanced-settings"
            "/account-protection/user-allow-list-id"
        )

    def test_500_internal_server_error(self, mock_session, mock_client):
        mock_session.exec.return_value = (
            MockResponse(
                status_code=500, body=_ERROR_DELETING_MATCH_TARGET
            ),
            None,
        )
        with pytest.raises(Error) as exc_info:
            mock_client.delete_user_allow_list_id(
                models.DeleteUserAllowListIDRequest(
                    config_id=43253,
                    version=15,
                )
            )
        err = exc_info.value
        assert err.type == "internal_error"
        assert err.title == "Internal Server Error"
        assert err.detail == "Error deleting match target"
        assert err.status_code == 500

    @pytest.mark.parametrize(
        "test_name, params, expected_field",
        [
            (
                "Missing ConfigID",
                models.DeleteUserAllowListIDRequest(
                    version=15,
                ),
                "ConfigID",
            ),
            (
                "Missing Version",
                models.DeleteUserAllowListIDRequest(
                    config_id=43253,
                ),
                "Version",
            ),
        ],
    )
    def test_validation_error(
        self, mock_session, mock_client, test_name, params, expected_field
    ):
        with pytest.raises(ValueError) as exc_info:
            mock_client.delete_user_allow_list_id(params)
        assert ErrStructValidation in str(exc_info.value), (
            f"{test_name}: missing ErrStructValidation"
        )
        assert expected_field in str(exc_info.value), (
            f"{test_name}: missing {expected_field}"
        )
        mock_session.exec.assert_not_called()
