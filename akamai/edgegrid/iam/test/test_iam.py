# pylint: disable=missing-function-docstring,too-many-lines,too-few-public-methods
"""Unit tests for the IAM (Identity & Access Management) API client."""

import json

import pytest

from akamai.edgegrid.iam.iam import IAMClient
from akamai.edgegrid.iam import models
from akamai.edgegrid.iam.errors import (
    Error,
    ErrLockAPIClient,
    ErrUnlockAPIClient,
    ErrListAPIClients,
    ErrGetAPIClient,
    ErrCreateAPIClient,
    ErrUpdateAPIClient,
    ErrDeleteAPIClient,
    ErrCreateCredential,
    ErrListCredentials,
    ErrGetCredential,
    ErrUpdateCredential,
    ErrDeleteCredential,
    ErrDeactivateCredential,
    ErrDeactivateCredentials,
    ErrListBlockedProperties,
    ErrUpdateBlockedProperties,
    ErrListCIDRBlocks,
    ErrCreateCIDRBlock,
    ErrGetCIDRBlock,
    ErrUpdateCIDRBlock,
    ErrDeleteCIDRBlock,
    ErrValidateCIDRBlock,
    ErrCreateGroup,
    ErrGetGroup,
    ErrListAffectedUsers,
    ErrListGroups,
    ErrRemoveGroup,
    ErrUpdateGroupName,
    ErrListAllowedCPCodes,
    ErrListAuthorizedUsers,
    ErrListAllowedAPIs,
    ErrAccessibleGroups,
    ErrDisableIPAllowlist,
    ErrEnableIPAllowlist,
    ErrGetIPAllowlistStatus,
    ErrListProperties,
    ErrListUsersForProperty,
    ErrGetProperty,
    ErrMoveProperty,
    ErrBlockUsers,
    ErrCreateRole,
    ErrGetRole,
    ErrUpdateRole,
    ErrDeleteRole,
    ErrListRoles,
    ErrListGrantableRoles,
    ErrGetPasswordPolicy,
    ErrListProducts,
    ErrListStates,
    ErrListTimeoutPolicies,
    ErrListAccountSwitchKeys,
    ErrSupportedContactTypes,
    ErrSupportedCountries,
    ErrSupportedLanguages,
    ErrSupportedTimezones,
    ErrCreateUser,
    ErrGetUser,
    ErrListUsers,
    ErrRemoveUser,
    ErrUpdateUserAuthGrants,
    ErrUpdateUserInfo,
    ErrUpdateUserNotifications,
    ErrUpdateMFA,
    ErrResetMFA,
    ErrLockUser,
    ErrUnlockUser,
    ErrResetUserPassword,
    ErrSetUserPassword,
    parse_iam_error_response,
)
from akamai.edgegrid.iam.test.conftest import (
    mock_response,
    assert_exec_called_with,
)


# ===================================================================
# Standard error response bodies — VERBATIM from Go test fixtures
# ===================================================================
ISE_RESPONSE_BODY = json.dumps({
    "type": "internal_error",
    "title": "Internal Server Error",
    "detail": "Error making request",
    "status": 500,
})

ISE_PROCESSING_RESPONSE_BODY = json.dumps({
    "type": "internal_error",
    "title": "Internal Server Error",
    "detail": "Error processing request",
    "status": 500,
})


def _ise_error(sentinel):
    """Helper — create a 500 ISE Error side_effect for a given sentinel."""
    return Error(
        type="internal_error",
        title=f"{sentinel}: Internal Server Error",
        detail="Error making request",
        status_code=500,
    )


def _ise_processing_error(sentinel):
    """Helper — create a 500 ISE (processing) Error side_effect."""
    return Error(
        type="internal_error",
        title=f"{sentinel}: Internal Server Error",
        detail="Error processing request",
        status_code=500,
    )


# ===================================================================
# 1. Error Tests — from errors_test.go
# ===================================================================


class TestNewError:
    """Mirrors TestNewError from errors_test.go."""

    def test_valid_response_status_code_500(self):
        resp = mock_response(500, '''{"type":"a","title":"b","detail":"c"}''')
        err = parse_iam_error_response(resp)
        assert err.type == "a"
        assert err.title == "b"
        assert err.detail == "c"
        assert err.status_code == 500

    def test_invalid_response_body_assign_status_code(self):
        resp = mock_response(500, "test")
        err = parse_iam_error_response(resp)
        assert "Failed to unmarshal error body" in err.title
        assert err.detail == "test"
        assert err.status_code == 500


class TestJsonErrorUnmarshalling:
    """Mirrors TestJsonErrorUnmarshalling from errors_test.go."""

    def test_api_failure_with_html_response(self):
        body = (
            "<HTML><HEAD>\n<TITLE>Access Denied</TITLE>\n"
            "</HEAD><BODY>\n<H1>Access Denied</H1>\n</BODY></HTML>"
        )
        resp = mock_response(503, body)
        err = parse_iam_error_response(resp)
        assert err.status_code == 503
        assert err.detail == body

    def test_api_failure_with_plain_text_response(self):
        body = (
            "Your request did not succeed as this operation has reached "
            " the limit for your account. Please try after "
            "2024-01-16T15:20:55.945Z"
        )
        resp = mock_response(503, body)
        err = parse_iam_error_response(resp)
        assert err.status_code == 503
        assert err.detail == body

    def test_api_failure_with_xml_response(self):
        body = '<Root><Item id="1" name="Example" /></Root>'
        resp = mock_response(503, body)
        err = parse_iam_error_response(resp)
        assert err.status_code == 503
        assert err.detail == body


# ===================================================================
# 2. Client Constructor — from iam_test.go
# ===================================================================


class TestClientConstructor:
    """Mirrors TestClient from iam_test.go."""

    def test_client_constructor(self, mock_session):
        client = IAMClient(mock_session)
        assert client is not None


# ===================================================================
# 3. API Client Tests — from api_clients_test.go
# ===================================================================


class TestLockAPIClient:
    """Mirrors TestIAM_LockAPIClient from api_clients_test.go."""

    def test_200_ok_with_specified_client(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(200, ""), None)
        iam_client.lock_api_client(
            models.LockAPIClientRequest(client_id="test1234"),
        )
        assert_exec_called_with(
            mock_session, "PUT",
            "/identity-management/v3/api-clients/test1234/lock",
        )

    def test_200_ok_self(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(200, ""), None)
        iam_client.lock_api_client(models.LockAPIClientRequest())
        assert_exec_called_with(
            mock_session, "PUT",
            "/identity-management/v3/api-clients/self/lock",
        )

    def test_404_not_found(self, iam_client, mock_session):
        mock_session.exec.side_effect = Error(
            type="/identity-management/error-types/2",
            title=f"{ErrLockAPIClient}: invalid open identity",
            http_status=404, status_code=404,
        )
        with pytest.raises(Error) as exc_info:
            iam_client.lock_api_client(
                models.LockAPIClientRequest(client_id="test1234"),
            )
        assert exc_info.value.status_code == 404

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrLockAPIClient)
        with pytest.raises(Error) as exc_info:
            iam_client.lock_api_client(
                models.LockAPIClientRequest(client_id="test1234"),
            )
        assert exc_info.value.status_code == 500


class TestUnlockAPIClient:
    """Mirrors TestIAM_UnlockAPIClient from api_clients_test.go."""

    def test_200_ok(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(200, ""), None)
        iam_client.unlock_api_client(
            models.UnlockAPIClientRequest(client_id="test1234"),
        )
        assert_exec_called_with(
            mock_session, "PUT",
            "/identity-management/v3/api-clients/test1234/unlock",
        )

    def test_validation_errors(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="ClientID: cannot be blank"):
            iam_client.unlock_api_client(
                models.UnlockAPIClientRequest(),
            )
        mock_session.exec.assert_not_called()

    def test_404_not_found(self, iam_client, mock_session):
        mock_session.exec.side_effect = Error(
            type="/identity-management/error-types/2",
            title=f"{ErrUnlockAPIClient}: invalid open identity",
            http_status=404, status_code=404,
        )
        with pytest.raises(Error) as exc_info:
            iam_client.unlock_api_client(
                models.UnlockAPIClientRequest(client_id="test1234"),
            )
        assert exc_info.value.status_code == 404

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrUnlockAPIClient)
        with pytest.raises(Error) as exc_info:
            iam_client.unlock_api_client(
                models.UnlockAPIClientRequest(client_id="test1234"),
            )
        assert exc_info.value.status_code == 500


class TestListAPIClients:
    """Mirrors TestIAM_ListAPIClients from api_clients_test.go."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "accessToken": "test_token1234",
            "activeCredentialCount": 1,
            "allowAccountSwitch": False,
            "authorizedUsers": ["jdoe"],
            "clientDescription": "Test",
            "clientId": "abcd1234",
            "clientName": "test",
            "clientType": "CLIENT",
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "isLocked": False,
            "notificationEmails": ["jdoe@example.com"],
            "serviceConsumerToken": "test_token12345",
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_api_clients(
            models.ListAPIClientsRequest(actions=False),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/api-clients",
            params={"actions": 'false'},
            expect_json=True,
        )
        assert len(result) == 1
        assert result[0].client_id == "abcd1234"

    def test_200_ok_with_actions(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "accessToken": "test_token1234",
            "activeCredentialCount": 1,
            "allowAccountSwitch": False,
            "authorizedUsers": ["jdoe"],
            "clientDescription": "Test",
            "clientId": "abcd1234",
            "clientName": "test",
            "clientType": "CLIENT",
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "isLocked": False,
            "notificationEmails": ["jdoe@example.com"],
            "serviceConsumerToken": "test_token12345",
            "actions": {
                "lock": True,
                "unlock": False,
                "edit": True,
                "delete": True,
                "transfer": True,
                "deactivateAll": True,
            },
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_api_clients(
            models.ListAPIClientsRequest(actions=True),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/api-clients",
            params={"actions": 'true'},
            expect_json=True,
        )
        assert len(result) == 1

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrListAPIClients)
        with pytest.raises(Error) as exc_info:
            iam_client.list_api_clients(
                models.ListAPIClientsRequest(actions=False),
            )
        assert exc_info.value.status_code == 500


class TestGetAPIClient:
    """Mirrors TestIAM_GetAPIClient from api_clients_test.go."""

    def test_200_ok_self(self, iam_client, mock_session):
        resp_body = json.dumps({
            "accessToken": "test_token1234",
            "activeCredentialCount": 1,
            "allowAccountSwitch": False,
            "authorizedUsers": ["jdoe"],
            "clientDescription": "Test",
            "clientId": "abcd1234",
            "clientName": "test",
            "clientType": "CLIENT",
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "isLocked": False,
            "notificationEmails": ["jdoe@example.com"],
            "serviceConsumerToken": "test_token12345",
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.get_api_client(
            models.GetAPIClientRequest(
                actions=False,
                group_access=False,
                api_access=False,
                credentials=False,
                ip_acl=False,
            ),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/api-clients/self",
            params={
                "actions": 'false',
                "groupAccess": 'false',
                "apiAccess": 'false',
                "credentials": 'false',
                "ipAcl": 'false',
            },
            expect_json=True,
        )
        assert result.client_id == "abcd1234"

    def test_200_ok_specified_client(self, iam_client, mock_session):
        resp_body = json.dumps({
            "accessToken": "test_token1234",
            "activeCredentialCount": 1,
            "allowAccountSwitch": False,
            "authorizedUsers": ["jdoe"],
            "clientDescription": "Test",
            "clientId": "abcd1234",
            "clientName": "test",
            "clientType": "CLIENT",
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "isLocked": False,
            "notificationEmails": ["jdoe@example.com"],
            "serviceConsumerToken": "test_token12345",
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.get_api_client(
            models.GetAPIClientRequest(
                client_id="test1234",
                actions=True,
                group_access=True,
                api_access=True,
                credentials=True,
                ip_acl=True,
            ),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/api-clients/test1234",
            params={
                "actions": 'true',
                "groupAccess": 'true',
                "apiAccess": 'true',
                "credentials": 'true',
                "ipAcl": 'true',
            },
            expect_json=True,
        )
        assert result.client_id == "abcd1234"

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrGetAPIClient)
        with pytest.raises(Error) as exc_info:
            iam_client.get_api_client(
                models.GetAPIClientRequest(
                    client_id="test1234",
                    actions=False,
                    group_access=False,
                    api_access=False,
                    credentials=False,
                    ip_acl=False,
                ),
            )
        assert exc_info.value.status_code == 500


class TestCreateAPIClient:
    """Mirrors TestIAM_CreateAPIClient from api_clients_test.go."""

    def test_201_created(self, iam_client, mock_session):
        resp_body = json.dumps({
            "accessToken": "test_token1234",
            "activeCredentialCount": 0,
            "allowAccountSwitch": False,
            "authorizedUsers": [],
            "clientDescription": "test_description",
            "clientId": "abcd1234",
            "clientName": "test_name",
            "clientType": "CLIENT",
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "isLocked": False,
            "notificationEmails": ["jdoe@example.com"],
            "serviceConsumerToken": "test_token12345",
        })
        mock_session.exec.return_value = (
            mock_response(201, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.create_api_client(
            models.CreateAPIClientRequest(
                allow_account_switch=False,
                authorized_users=["jdoe"],
                client_description="test_description",
                client_name="test_name",
                client_type="CLIENT",
                notification_emails=["jdoe@example.com"],
            ),
        )
        assert result.client_id == "abcd1234"

    def test_validation_errors_empty_request(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="cannot be blank"):
            iam_client.create_api_client(models.CreateAPIClientRequest())
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrCreateAPIClient)
        with pytest.raises(Error) as exc_info:
            iam_client.create_api_client(
                models.CreateAPIClientRequest(
                    allow_account_switch=False,
                    authorized_users=["jdoe"],
                    client_description="test",
                    client_name="test",
                    client_type="CLIENT",
                    notification_emails=["jdoe@example.com"],
                ),
            )
        assert exc_info.value.status_code == 500


class TestUpdateAPIClient:
    """Mirrors TestIAM_UpdateAPIClient from api_clients_test.go."""

    def test_200_ok_self(self, iam_client, mock_session):
        resp_body = json.dumps({
            "accessToken": "test_token1234",
            "activeCredentialCount": 1,
            "allowAccountSwitch": False,
            "authorizedUsers": ["jdoe"],
            "clientDescription": "Updated",
            "clientId": "abcd1234",
            "clientName": "test",
            "clientType": "CLIENT",
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "isLocked": False,
            "notificationEmails": ["jdoe@example.com"],
            "serviceConsumerToken": "test_token12345",
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.update_api_client(
            models.UpdateAPIClientRequest(
                body=models.UpdateAPIClientRequestBody(
                    allow_account_switch=False,
                    api_access=models.APIAccessRequest(
                        all_accessible_apis=True,
                    ),
                    authorized_users=["jdoe"],
                    client_description="Updated",
                    client_name="test",
                    client_type="CLIENT",
                    group_access=models.GroupAccessRequest(
                        clone_authorized_user_groups=True,
                    ),
                    notification_emails=["jdoe@example.com"],
                ),
            ),
        )
        assert_exec_called_with(
            mock_session, "PUT",
            "/identity-management/v3/api-clients/self",
        )
        assert result.client_description == "Updated"

    def test_200_ok_specified_client(self, iam_client, mock_session):
        resp_body = json.dumps({
            "accessToken": "test_token1234",
            "activeCredentialCount": 1,
            "allowAccountSwitch": False,
            "authorizedUsers": ["jdoe"],
            "clientDescription": "Updated",
            "clientId": "abcd1234",
            "clientName": "test",
            "clientType": "CLIENT",
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "isLocked": False,
            "notificationEmails": ["jdoe@example.com"],
            "serviceConsumerToken": "test_token12345",
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.update_api_client(
            models.UpdateAPIClientRequest(
                client_id="test1234",
                body=models.UpdateAPIClientRequestBody(
                    allow_account_switch=False,
                    api_access=models.APIAccessRequest(
                        all_accessible_apis=True,
                    ),
                    authorized_users=["jdoe"],
                    client_description="Updated",
                    client_name="test",
                    client_type="CLIENT",
                    group_access=models.GroupAccessRequest(
                        clone_authorized_user_groups=True,
                    ),
                    notification_emails=["jdoe@example.com"],
                ),
            ),
        )
        assert_exec_called_with(
            mock_session, "PUT",
            "/identity-management/v3/api-clients/test1234",
        )
        assert result.client_description == "Updated"

    def test_validation_errors(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="cannot be blank"):
            iam_client.update_api_client(models.UpdateAPIClientRequest())
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrUpdateAPIClient)
        with pytest.raises(Error) as exc_info:
            iam_client.update_api_client(
                models.UpdateAPIClientRequest(
                    client_id="test1234",
                    body=models.UpdateAPIClientRequestBody(
                        allow_account_switch=False,
                        api_access=models.APIAccessRequest(
                            all_accessible_apis=True,
                        ),
                        authorized_users=["jdoe"],
                        client_description="Updated",
                        client_name="test",
                        client_type="CLIENT",
                        group_access=models.GroupAccessRequest(
                            clone_authorized_user_groups=True,
                        ),
                        notification_emails=["jdoe@example.com"],
                    ),
                ),
            )
        assert exc_info.value.status_code == 500


class TestDeleteAPIClient:
    """Mirrors TestIAM_DeleteAPIClient from api_clients_test.go."""

    def test_204_no_content_self(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        iam_client.delete_api_client(models.DeleteAPIClientRequest())
        assert_exec_called_with(
            mock_session, "DELETE",
            "/identity-management/v3/api-clients/self",
        )

    def test_204_no_content_specified_client(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        iam_client.delete_api_client(
            models.DeleteAPIClientRequest(client_id="test1234"),
        )
        assert_exec_called_with(
            mock_session, "DELETE",
            "/identity-management/v3/api-clients/test1234",
        )

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrDeleteAPIClient)
        with pytest.raises(Error) as exc_info:
            iam_client.delete_api_client(
                models.DeleteAPIClientRequest(client_id="test1234"),
            )
        assert exc_info.value.status_code == 500


# ===================================================================
# 4. Credential Tests — from api_clients_credentials_test.go
# ===================================================================


class TestCreateCredential:
    """Mirrors TestIAM_CreateCredential from api_clients_credentials_test.go."""

    def test_201_with_specified_client(self, iam_client, mock_session):
        resp_body = json.dumps({
            "credentialId": 1,
            "clientToken": "test-token1",
            "clientSecret": "test-secret",
            "createdOn": "2024-05-14T11:10:25.000Z",
            "description": "",
            "expiresOn": "2026-05-14T11:10:25.000Z",
            "status": "ACTIVE",
            "maxAllowedExpiry": "2026-07-25T11:09:30.658Z",
        })
        mock_session.exec.return_value = (
            mock_response(201, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.create_credential(
            models.CreateCredentialRequest(client_id="test1234"),
        )
        assert_exec_called_with(
            mock_session, "POST",
            "/identity-management/v3/api-clients/test1234/credentials",
            expect_json=True,
        )
        assert result.credential_id == 1

    def test_201_self(self, iam_client, mock_session):
        resp_body = json.dumps({
            "credentialId": 1,
            "clientToken": "test-token1",
            "clientSecret": "test-secret",
            "createdOn": "2024-05-14T11:10:25.000Z",
            "description": "",
            "expiresOn": "2026-05-14T11:10:25.000Z",
            "status": "ACTIVE",
            "maxAllowedExpiry": "2026-07-25T11:09:30.658Z",
        })
        mock_session.exec.return_value = (
            mock_response(201, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.create_credential(
            models.CreateCredentialRequest(),
        )
        assert_exec_called_with(
            mock_session, "POST",
            "/identity-management/v3/api-clients/self/credentials",
            expect_json=True,
        )
        assert result.credential_id == 1

    def test_404_not_found(self, iam_client, mock_session):
        mock_session.exec.side_effect = Error(
            type="/identity-management/error-types/2",
            title=f"{ErrCreateCredential}: invalid open identity",
            http_status=404, status_code=404,
        )
        with pytest.raises(Error) as exc_info:
            iam_client.create_credential(
                models.CreateCredentialRequest(client_id="test1234"),
            )
        assert exc_info.value.status_code == 404

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrCreateCredential)
        with pytest.raises(Error) as exc_info:
            iam_client.create_credential(
                models.CreateCredentialRequest(client_id="test1234"),
            )
        assert exc_info.value.status_code == 500


class TestListCredentials:
    """Mirrors TestIAM_ListCredentials from api_clients_credentials_test.go."""

    def test_200_ok_with_specified_client(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "credentialId": 1,
            "clientToken": "test-token1",
            "status": "ACTIVE",
            "createdOn": "2024-05-14T11:10:25.000Z",
            "description": "",
            "expiresOn": "2026-05-14T11:10:25.000Z",
            "maxAllowedExpiry": "2026-07-25T11:09:30.658Z",
            "actions": {
                "deactivate": True,
                "delete": True,
                "activate": True,
                "editDescription": True,
                "editExpiration": True,
            },
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_credentials(
            models.ListCredentialsRequest(
                client_id="test1234", actions=True,
            ),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/api-clients/test1234/credentials",
            params={"actions": 'true'},
            expect_json=True,
        )
        assert len(result) == 1

    def test_200_ok_self(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "credentialId": 1,
            "clientToken": "test-token1",
            "status": "ACTIVE",
            "createdOn": "2024-05-14T11:10:25.000Z",
            "description": "",
            "expiresOn": "2026-05-14T11:10:25.000Z",
            "maxAllowedExpiry": "2026-07-25T11:09:30.658Z",
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_credentials(
            models.ListCredentialsRequest(actions=False),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/api-clients/self/credentials",
            params={"actions": 'false'},
            expect_json=True,
        )
        assert len(result) == 1

    def test_404_not_found(self, iam_client, mock_session):
        mock_session.exec.side_effect = Error(
            type="/identity-management/error-types/2",
            title=f"{ErrListCredentials}: invalid open identity",
            http_status=404, status_code=404,
        )
        with pytest.raises(Error) as exc_info:
            iam_client.list_credentials(
                models.ListCredentialsRequest(
                    client_id="test1234", actions=False,
                ),
            )
        assert exc_info.value.status_code == 404

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrListCredentials)
        with pytest.raises(Error) as exc_info:
            iam_client.list_credentials(
                models.ListCredentialsRequest(actions=False),
            )
        assert exc_info.value.status_code == 500


class TestGetCredential:
    """Mirrors TestIAM_GetCredential from api_clients_credentials_test.go."""

    def test_200_ok_with_specified_client(self, iam_client, mock_session):
        resp_body = json.dumps({
            "credentialId": 1,
            "clientToken": "test-token1",
            "status": "ACTIVE",
            "createdOn": "2024-05-14T11:10:25.000Z",
            "description": "",
            "expiresOn": "2026-05-14T11:10:25.000Z",
            "maxAllowedExpiry": "2026-07-25T11:09:30.658Z",
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.get_credential(
            models.GetCredentialRequest(
                client_id="test1234", credential_id=123, actions=False,
            ),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/api-clients/test1234/credentials/123",
            params={"actions": 'false'},
            expect_json=True,
        )
        assert result.credential_id == 1

    def test_200_ok_self_with_actions(self, iam_client, mock_session):
        resp_body = json.dumps({
            "credentialId": 1,
            "clientToken": "test-token1",
            "status": "ACTIVE",
            "createdOn": "2024-05-14T11:10:25.000Z",
            "description": "",
            "expiresOn": "2026-05-14T11:10:25.000Z",
            "maxAllowedExpiry": "2026-07-25T11:09:30.658Z",
            "actions": {
                "deactivate": True,
                "delete": True,
                "activate": True,
                "editDescription": True,
                "editExpiration": False,
            },
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.get_credential(
            models.GetCredentialRequest(credential_id=123, actions=True),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/api-clients/self/credentials/123",
            params={"actions": 'true'},
            expect_json=True,
        )
        assert result.credential_id == 1

    def test_validation_missing_credential_id(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="CredentialID: cannot be blank"):
            iam_client.get_credential(
                models.GetCredentialRequest(
                    client_id="test1234", actions=False,
                ),
            )
        mock_session.exec.assert_not_called()

    def test_404_not_found(self, iam_client, mock_session):
        mock_session.exec.side_effect = Error(
            type="/identity-management/error-types/25",
            title=f"{ErrGetCredential}: ERROR_NO_CREDENTIAL",
            http_status=404, status_code=404,
        )
        with pytest.raises(Error) as exc_info:
            iam_client.get_credential(
                models.GetCredentialRequest(
                    client_id="test1234", credential_id=123, actions=False,
                ),
            )
        assert exc_info.value.status_code == 404

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrGetCredential)
        with pytest.raises(Error) as exc_info:
            iam_client.get_credential(
                models.GetCredentialRequest(
                    client_id="test1234", credential_id=123, actions=False,
                ),
            )
        assert exc_info.value.status_code == 500


class TestUpdateCredential:
    """Mirrors TestIAM_UpdateCredential from api_clients_credentials_test.go."""

    def test_200_ok_with_specified_client(self, iam_client, mock_session):
        resp_body = json.dumps({
            "status": "ACTIVE",
            "expiresOn": "2026-05-14T11:10:25.000Z",
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.update_credential(
            models.UpdateCredentialRequest(
                client_id="test1234",
                credential_id=123,
                body=models.UpdateCredentialRequestBody(
                    status="ACTIVE",
                    expires_on="2026-05-14T11:10:25.000Z",
                ),
            ),
        )
        assert_exec_called_with(
            mock_session, "PUT",
            "/identity-management/v3/api-clients/test1234/credentials/123",
        )
        assert result.status == "ACTIVE"

    def test_200_ok_self_with_description(self, iam_client, mock_session):
        resp_body = json.dumps({
            "status": "INACTIVE",
            "expiresOn": "2026-05-14T11:10:25.000Z",
            "description": "test description",
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.update_credential(
            models.UpdateCredentialRequest(
                credential_id=123,
                body=models.UpdateCredentialRequestBody(
                    status="INACTIVE",
                    expires_on="2026-05-14T11:10:25.000Z",
                    description="test description",
                ),
            ),
        )
        assert_exec_called_with(
            mock_session, "PUT",
            "/identity-management/v3/api-clients/self/credentials/123",
        )
        assert result.description == "test description"

    def test_validation_missing_required_fields(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="CredentialID: cannot be blank"):
            iam_client.update_credential(
                models.UpdateCredentialRequest(),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrUpdateCredential)
        with pytest.raises(Error) as exc_info:
            iam_client.update_credential(
                models.UpdateCredentialRequest(
                    client_id="test1234",
                    credential_id=123,
                    body=models.UpdateCredentialRequestBody(
                        status="ACTIVE",
                        expires_on="2026-05-14T11:10:25.000Z",
                    ),
                ),
            )
        assert exc_info.value.status_code == 500


class TestDeleteCredential:
    """Mirrors TestIAM_DeleteCredential from api_clients_credentials_test.go."""

    def test_204_with_specified_client(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        iam_client.delete_credential(
            models.DeleteCredentialRequest(
                client_id="test1234", credential_id=123,
            ),
        )
        assert_exec_called_with(
            mock_session, "DELETE",
            "/identity-management/v3/api-clients/test1234/credentials/123",
        )

    def test_204_self(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        iam_client.delete_credential(
            models.DeleteCredentialRequest(credential_id=123),
        )
        assert_exec_called_with(
            mock_session, "DELETE",
            "/identity-management/v3/api-clients/self/credentials/123",
        )

    def test_validation_missing_credential_id(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="CredentialID: cannot be blank"):
            iam_client.delete_credential(
                models.DeleteCredentialRequest(),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrDeleteCredential)
        with pytest.raises(Error) as exc_info:
            iam_client.delete_credential(
                models.DeleteCredentialRequest(
                    client_id="test1234", credential_id=123,
                ),
            )
        assert exc_info.value.status_code == 500


class TestDeactivateCredential:
    """Mirrors TestIAM_DeactivateCredential."""

    def test_204_with_specified_client(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        iam_client.deactivate_credential(
            models.DeactivateCredentialRequest(
                client_id="test1234", credential_id=123,
            ),
        )
        assert_exec_called_with(
            mock_session, "POST",
            "/identity-management/v3/api-clients/test1234/credentials/123/deactivate",
        )

    def test_204_self(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        iam_client.deactivate_credential(
            models.DeactivateCredentialRequest(credential_id=123),
        )
        assert_exec_called_with(
            mock_session, "POST",
            "/identity-management/v3/api-clients/self/credentials/123/deactivate",
        )

    def test_validation_missing_credential_id(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="CredentialID: cannot be blank"):
            iam_client.deactivate_credential(
                models.DeactivateCredentialRequest(),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrDeactivateCredential)
        with pytest.raises(Error) as exc_info:
            iam_client.deactivate_credential(
                models.DeactivateCredentialRequest(
                    client_id="test1234", credential_id=123,
                ),
            )
        assert exc_info.value.status_code == 500


class TestDeactivateCredentials:
    """Mirrors TestIAM_DeactivateCredentials."""

    def test_204_with_specified_client(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        iam_client.deactivate_credentials(
            models.DeactivateCredentialsRequest(client_id="test1234"),
        )
        assert_exec_called_with(
            mock_session, "POST",
            "/identity-management/v3/api-clients/test1234/credentials/deactivate",
        )

    def test_204_self(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        iam_client.deactivate_credentials(
            models.DeactivateCredentialsRequest(),
        )
        assert_exec_called_with(
            mock_session, "POST",
            "/identity-management/v3/api-clients/self/credentials/deactivate",
        )

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrDeactivateCredentials)
        with pytest.raises(Error) as exc_info:
            iam_client.deactivate_credentials(
                models.DeactivateCredentialsRequest(client_id="test1234"),
            )
        assert exc_info.value.status_code == 500


# ===================================================================
# 5. Blocked Properties Tests — from blocked_properties_test.go
# ===================================================================


class TestListBlockedProperties:
    """Mirrors TestIAM_ListBlockedProperties."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps([10977166])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_blocked_properties(
            models.ListBlockedPropertiesRequest(
                identity_id="1-ABCDE", group_id=12345,
            ),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/ui-identities/1-ABCDE"
            "/groups/12345/blocked-properties",
            expect_json=True,
        )
        assert result == [10977166]

    def test_200_ok_no_blocked_property(self, iam_client, mock_session):
        resp_body = json.dumps([])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_blocked_properties(
            models.ListBlockedPropertiesRequest(
                identity_id="1-ABCDE", group_id=12345,
            ),
        )
        assert result == []

    def test_404_not_found(self, iam_client, mock_session):
        mock_session.exec.side_effect = Error(
            type="/identity-management/error-types/2",
            title=f"{ErrListBlockedProperties}: Not Found",
            http_status=404, status_code=404,
        )
        with pytest.raises(Error) as exc_info:
            iam_client.list_blocked_properties(
                models.ListBlockedPropertiesRequest(
                    identity_id="1-ABCDE", group_id=12345,
                ),
            )
        assert exc_info.value.status_code == 404

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrListBlockedProperties)
        with pytest.raises(Error) as exc_info:
            iam_client.list_blocked_properties(
                models.ListBlockedPropertiesRequest(
                    identity_id="1-ABCDE", group_id=12345,
                ),
            )
        assert exc_info.value.status_code == 500


class TestUpdateBlockedProperties:
    """Mirrors TestIAM_UpdateBlockedProperties."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps([10977166, 10977167])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.update_blocked_properties(
            models.UpdateBlockedPropertiesRequest(
                identity_id="1-ABCDE",
                group_id=12345,
                body=[10977166, 10977167],
            ),
        )
        assert_exec_called_with(
            mock_session, "PUT",
            "/identity-management/v3/user-admin/ui-identities/1-ABCDE"
            "/groups/12345/blocked-properties",
        )
        assert result == [10977166, 10977167]

    def test_404_not_found(self, iam_client, mock_session):
        mock_session.exec.side_effect = Error(
            type="/identity-management/error-types/2",
            title=f"{ErrUpdateBlockedProperties}: Not Found",
            http_status=404, status_code=404,
        )
        with pytest.raises(Error) as exc_info:
            iam_client.update_blocked_properties(
                models.UpdateBlockedPropertiesRequest(
                    identity_id="1-ABCDE",
                    group_id=12345,
                    body=[10977166],
                ),
            )
        assert exc_info.value.status_code == 404

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrUpdateBlockedProperties)
        with pytest.raises(Error) as exc_info:
            iam_client.update_blocked_properties(
                models.UpdateBlockedPropertiesRequest(
                    identity_id="1-ABCDE",
                    group_id=12345,
                    body=[10977166],
                ),
            )
        assert exc_info.value.status_code == 500


# ===================================================================
# 6. CIDR Tests — from cidr_test.go
# ===================================================================


class TestListCIDRBlocks:
    """Mirrors TestIAM_ListCIDRBlocks."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "cidrBlockId": 1234,
            "cidrBlock": "128.0.0.1/32",
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "enabled": True,
            "comments": "test",
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_cidr_blocks(
            models.ListCIDRBlocksRequest(actions=False),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/ip-acl/allowlist",
            params={"actions": 'false'},
            expect_json=True,
        )
        assert len(result) == 1
        assert result[0].cidr_block_id == 1234

    def test_200_ok_with_actions(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "cidrBlockId": 1234,
            "cidrBlock": "128.0.0.1/32",
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "enabled": True,
            "comments": "test",
            "actions": {"edit": True, "delete": True},
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_cidr_blocks(
            models.ListCIDRBlocksRequest(actions=True),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/ip-acl/allowlist",
            params={"actions": 'true'},
            expect_json=True,
        )
        assert len(result) == 1

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrListCIDRBlocks)
        with pytest.raises(Error) as exc_info:
            iam_client.list_cidr_blocks(
                models.ListCIDRBlocksRequest(actions=False),
            )
        assert exc_info.value.status_code == 500


class TestCreateCIDRBlock:
    """Mirrors TestIAM_CreateCIDRBlock."""

    def test_201_created(self, iam_client, mock_session):
        resp_body = json.dumps({
            "cidrBlockId": 1234,
            "cidrBlock": "128.0.0.1/32",
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "enabled": True,
            "comments": "test",
        })
        mock_session.exec.return_value = (
            mock_response(201, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.create_cidr_block(
            models.CreateCIDRBlockRequest(
                body=models.CreateCIDRBlockRequestBody(
                    cidr_block="128.0.0.1/32",
                    enabled=True,
                    comments="test",
                ),
            ),
        )
        assert_exec_called_with(
            mock_session, "POST",
            "/identity-management/v3/user-admin/ip-acl/allowlist",
        )
        assert result.cidr_block_id == 1234

    def test_validation_missing_required_fields(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="cannot be blank"):
            iam_client.create_cidr_block(
                models.CreateCIDRBlockRequest(),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrCreateCIDRBlock)
        with pytest.raises(Error) as exc_info:
            iam_client.create_cidr_block(
                models.CreateCIDRBlockRequest(
                    body=models.CreateCIDRBlockRequestBody(
                        cidr_block="128.0.0.1/32",
                        enabled=True,
                        comments="test",
                    ),
                ),
            )
        assert exc_info.value.status_code == 500


class TestGetCIDRBlock:
    """Mirrors TestIAM_GetCIDRBlock."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps({
            "cidrBlockId": 1234,
            "cidrBlock": "128.0.0.1/32",
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "enabled": True,
            "comments": "test",
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.get_cidr_block(
            models.GetCIDRBlockRequest(cidr_block_id=1234, actions=False),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/ip-acl/allowlist/1234",
            params={"actions": 'false'},
            expect_json=True,
        )
        assert result.cidr_block_id == 1234

    def test_200_ok_with_actions(self, iam_client, mock_session):
        resp_body = json.dumps({
            "cidrBlockId": 1234,
            "cidrBlock": "128.0.0.1/32",
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "enabled": True,
            "comments": "test",
            "actions": {"edit": True, "delete": True},
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.get_cidr_block(
            models.GetCIDRBlockRequest(cidr_block_id=1234, actions=True),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/ip-acl/allowlist/1234",
            params={"actions": 'true'},
            expect_json=True,
        )
        assert result.cidr_block_id == 1234

    def test_validation_missing_cidr_block_id(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="CIDRBlockID: cannot be blank"):
            iam_client.get_cidr_block(
                models.GetCIDRBlockRequest(actions=False),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrGetCIDRBlock)
        with pytest.raises(Error) as exc_info:
            iam_client.get_cidr_block(
                models.GetCIDRBlockRequest(cidr_block_id=1234, actions=False),
            )
        assert exc_info.value.status_code == 500


class TestUpdateCIDRBlock:
    """Mirrors TestIAM_UpdateCIDRBlock."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps({
            "cidrBlockId": 1234,
            "cidrBlock": "128.0.0.1/32",
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "enabled": True,
            "comments": "updated",
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.update_cidr_block(
            models.UpdateCIDRBlockRequest(
                cidr_block_id=1234,
                body=models.UpdateCIDRBlockRequestBody(
                    cidr_block="128.0.0.1/32",
                    enabled=True,
                    comments="updated",
                ),
            ),
        )
        assert_exec_called_with(
            mock_session, "PUT",
            "/identity-management/v3/user-admin/ip-acl/allowlist/1234",
        )
        assert result.comments == "updated"

    def test_validation_missing_cidr_block_id(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="CIDRBlockID: cannot be blank"):
            iam_client.update_cidr_block(
                models.UpdateCIDRBlockRequest(),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrUpdateCIDRBlock)
        with pytest.raises(Error) as exc_info:
            iam_client.update_cidr_block(
                models.UpdateCIDRBlockRequest(
                    cidr_block_id=1234,
                    body=models.UpdateCIDRBlockRequestBody(
                        cidr_block="128.0.0.1/32",
                        enabled=True,
                        comments="updated",
                    ),
                ),
            )
        assert exc_info.value.status_code == 500


class TestDeleteCIDRBlock:
    """Mirrors TestIAM_DeleteCIDRBlock."""

    def test_204_no_content(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        iam_client.delete_cidr_block(
            models.DeleteCIDRBlockRequest(cidr_block_id=1234),
        )
        assert_exec_called_with(
            mock_session, "DELETE",
            "/identity-management/v3/user-admin/ip-acl/allowlist/1234",
        )

    def test_validation_missing_cidr_block_id(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="CIDRBlockID: cannot be blank"):
            iam_client.delete_cidr_block(
                models.DeleteCIDRBlockRequest(),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrDeleteCIDRBlock)
        with pytest.raises(Error) as exc_info:
            iam_client.delete_cidr_block(
                models.DeleteCIDRBlockRequest(cidr_block_id=1234),
            )
        assert exc_info.value.status_code == 500


class TestValidateCIDRBlock:
    """Mirrors TestIAM_ValidateCIDRBlock."""

    def test_204_no_content(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        iam_client.validate_cidr_block(
            models.ValidateCIDRBlockRequest(cidr_block="128.0.0.1/32"),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/ip-acl/allowlist/validate",
            params={"cidrblock": "128.0.0.1/32"},
        )

    def test_validation_missing_cidr_block(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="CIDRBlock: cannot be blank"):
            iam_client.validate_cidr_block(
                models.ValidateCIDRBlockRequest(),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrValidateCIDRBlock)
        with pytest.raises(Error) as exc_info:
            iam_client.validate_cidr_block(
                models.ValidateCIDRBlockRequest(cidr_block="128.0.0.1/32"),
            )
        assert exc_info.value.status_code == 500


# ===================================================================
# 7. Group Tests — from groups_test.go
# ===================================================================


class TestCreateGroup:
    """Mirrors TestIAM_CreateGroup."""

    def test_201_ok(self, iam_client, mock_session):
        resp_body = json.dumps({
            "groupId": 12345,
            "groupName": "TestGroup",
            "parentGroupId": 67890,
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "modifiedBy": "jdoe",
            "modifiedDate": "2022-05-13T20:04:35.000Z",
        })
        mock_session.exec.return_value = (
            mock_response(201, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.create_group(
            models.GroupRequest(group_id=67890, group_name="TestGroup"),
        )
        assert_exec_called_with(
            mock_session, "POST",
            "/identity-management/v3/user-admin/groups/67890",
        )
        assert result.group_id == 12345

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrCreateGroup)
        with pytest.raises(Error) as exc_info:
            iam_client.create_group(
                models.GroupRequest(group_id=67890, group_name="TestGroup"),
            )
        assert exc_info.value.status_code == 500

    def test_missing_group_id(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="cannot be blank"):
            iam_client.create_group(
                models.GroupRequest(group_name="TestGroup"),
            )
        mock_session.exec.assert_not_called()

    def test_missing_group_name(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="cannot be blank"):
            iam_client.create_group(
                models.GroupRequest(group_id=67890),
            )
        mock_session.exec.assert_not_called()


class TestMoveGroup:
    """Mirrors TestIAM_MoveGroup."""

    def test_204_no_content(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        iam_client.move_group(
            models.MoveGroupRequest(
                source_group_id=12345,
                destination_group_id=67890,
            ),
        )
        assert_exec_called_with(
            mock_session, "POST",
            "/identity-management/v3/user-admin/groups/move",
        )

    def test_missing_source_group_id(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="cannot be blank"):
            iam_client.move_group(
                models.MoveGroupRequest(destination_group_id=67890),
            )
        mock_session.exec.assert_not_called()

    def test_missing_destination_group_id(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="cannot be blank"):
            iam_client.move_group(
                models.MoveGroupRequest(source_group_id=12345),
            )
        mock_session.exec.assert_not_called()


class TestGetGroup:
    """Mirrors TestIAM_GetGroup."""

    def test_200_ok_no_query_params(self, iam_client, mock_session):
        resp_body = json.dumps({
            "groupId": 12345,
            "groupName": "TestGroup",
            "parentGroupId": 67890,
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "modifiedBy": "jdoe",
            "modifiedDate": "2022-05-13T20:04:35.000Z",
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.get_group(
            models.GetGroupRequest(group_id=12345, actions=False),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/groups/12345",
            params={"actions": 'false'},
            expect_json=True,
        )
        assert result.group_id == 12345

    def test_200_ok_with_actions(self, iam_client, mock_session):
        resp_body = json.dumps({
            "groupId": 12345,
            "groupName": "TestGroup",
            "parentGroupId": 67890,
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "modifiedBy": "jdoe",
            "modifiedDate": "2022-05-13T20:04:35.000Z",
            "subGroups": [{
                "groupId": 11111,
                "groupName": "SubGroup",
                "parentGroupId": 12345,
            }],
            "actions": {
                "edit": True,
                "delete": True,
            },
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.get_group(
            models.GetGroupRequest(group_id=12345, actions=True),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/groups/12345",
            params={"actions": 'true'},
            expect_json=True,
        )
        assert result.group_id == 12345

    def test_validation_missing_group_id(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="GroupID: cannot be blank"):
            iam_client.get_group(
                models.GetGroupRequest(actions=False),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrGetGroup)
        with pytest.raises(Error) as exc_info:
            iam_client.get_group(
                models.GetGroupRequest(group_id=12345, actions=False),
            )
        assert exc_info.value.status_code == 500


class TestListAffectedUsers:
    """Mirrors TestIAM_ListAffectedUsers."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "uiIdentityId": "A-BC-1234567",
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@mycompany.com",
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_affected_users(
            models.ListAffectedUsersRequest(
                source_group_id=12345,
                destination_group_id=67890,
            ),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/groups/move"
            "/12345/67890/affected-users",
            expect_json=True,
        )
        assert len(result) == 1

    def test_200_ok_with_user_type(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "uiIdentityId": "A-BC-1234567",
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@mycompany.com",
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_affected_users(
            models.ListAffectedUsersRequest(
                source_group_id=12345,
                destination_group_id=67890,
                user_type="lostAccess",
            ),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/groups/move"
            "/12345/67890/affected-users",
            params={"userType": "lostAccess"},
            expect_json=True,
        )
        assert len(result) == 1

    def test_validation_missing_source_group_id(
        self, iam_client, mock_session,
    ):
        with pytest.raises(ValueError, match="cannot be blank"):
            iam_client.list_affected_users(
                models.ListAffectedUsersRequest(
                    destination_group_id=67890,
                ),
            )
        mock_session.exec.assert_not_called()

    def test_validation_missing_destination_group_id(
        self, iam_client, mock_session,
    ):
        with pytest.raises(ValueError, match="cannot be blank"):
            iam_client.list_affected_users(
                models.ListAffectedUsersRequest(
                    source_group_id=12345,
                ),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrListAffectedUsers)
        with pytest.raises(Error) as exc_info:
            iam_client.list_affected_users(
                models.ListAffectedUsersRequest(
                    source_group_id=12345,
                    destination_group_id=67890,
                ),
            )
        assert exc_info.value.status_code == 500


class TestListGroups:
    """Mirrors TestIAM_ListGroups."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "groupId": 12345,
            "groupName": "TestGroup",
            "parentGroupId": 67890,
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "modifiedBy": "jdoe",
            "modifiedDate": "2022-05-13T20:04:35.000Z",
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_groups(
            models.ListGroupsRequest(actions=False),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/groups",
            params={"actions": 'false'},
            expect_json=True,
        )
        assert len(result) == 1

    def test_200_ok_with_actions(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "groupId": 12345,
            "groupName": "TestGroup",
            "parentGroupId": 67890,
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "modifiedBy": "jdoe",
            "modifiedDate": "2022-05-13T20:04:35.000Z",
            "actions": {"edit": True, "delete": True},
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_groups(
            models.ListGroupsRequest(actions=True),
        )
        assert len(result) == 1

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrListGroups)
        with pytest.raises(Error) as exc_info:
            iam_client.list_groups(
                models.ListGroupsRequest(actions=False),
            )
        assert exc_info.value.status_code == 500


class TestRemoveGroup:
    """Mirrors TestIAM_RemoveGroup."""

    def test_204_no_content(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        iam_client.remove_group(
            models.RemoveGroupRequest(group_id=12345),
        )
        assert_exec_called_with(
            mock_session, "DELETE",
            "/identity-management/v3/user-admin/groups/12345",
        )

    def test_validation_missing_group_id(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="GroupID: cannot be blank"):
            iam_client.remove_group(models.RemoveGroupRequest())
        mock_session.exec.assert_not_called()

    def test_403_forbidden(self, iam_client, mock_session):
        mock_session.exec.side_effect = Error(
            title=f"{ErrRemoveGroup}: Forbidden",
            detail="Not Authorized to perform this action",
            http_status=403, status_code=403,
        )
        with pytest.raises(Error) as exc_info:
            iam_client.remove_group(
                models.RemoveGroupRequest(group_id=12345),
            )
        assert exc_info.value.status_code == 403

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrRemoveGroup)
        with pytest.raises(Error) as exc_info:
            iam_client.remove_group(
                models.RemoveGroupRequest(group_id=12345),
            )
        assert exc_info.value.status_code == 500


class TestUpdateGroupName:
    """Mirrors TestIAM_UpdateGroupName."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps({
            "groupId": 12345,
            "groupName": "UpdatedGroup",
            "parentGroupId": 67890,
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "modifiedBy": "jdoe",
            "modifiedDate": "2022-05-13T20:04:35.000Z",
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.update_group_name(
            models.GroupRequest(group_id=12345, group_name="UpdatedGroup"),
        )
        assert_exec_called_with(
            mock_session, "PUT",
            "/identity-management/v3/user-admin/groups/12345",
        )
        assert result.group_name == "UpdatedGroup"

    def test_missing_group_id(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="cannot be blank"):
            iam_client.update_group_name(
                models.GroupRequest(group_name="UpdatedGroup"),
            )
        mock_session.exec.assert_not_called()

    def test_missing_group_name(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="cannot be blank"):
            iam_client.update_group_name(
                models.GroupRequest(group_id=12345),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrUpdateGroupName)
        with pytest.raises(Error) as exc_info:
            iam_client.update_group_name(
                models.GroupRequest(
                    group_id=12345, group_name="UpdatedGroup",
                ),
            )
        assert exc_info.value.status_code == 500


# ===================================================================
# 8. Helper Tests — from helper_test.go
# ===================================================================


class TestListAllowedCPCodes:
    """Mirrors TestIAM_ListAllowedCPCodes."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "name": "Stream Analyzer (36915)",
            "value": 36915,
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_allowed_cp_codes(
            models.ListAllowedCPCodesRequest(
                user_name="jsmith",
                body=models.ListAllowedCPCodesRequestBody(
                    client_type="CLIENT",
                ),
            ),
        )
        assert_exec_called_with(
            mock_session, "POST",
            "/identity-management/v3/users/jsmith/allowed-cpcodes",
        )
        assert len(result) == 1

    def test_200_ok_with_groups(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "name": "Stream Analyzer (36915)",
            "value": 36915,
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_allowed_cp_codes(
            models.ListAllowedCPCodesRequest(
                user_name="jsmith",
                body=models.ListAllowedCPCodesRequestBody(
                    client_type="SERVICE_ACCOUNT",
                    groups=[models.ClientGroupRequestItem(group_id=1, role_id=2)],
                ),
            ),
        )
        assert len(result) == 1

    def test_validation_missing_user_name(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="UserName: cannot be blank"):
            iam_client.list_allowed_cp_codes(
                models.ListAllowedCPCodesRequest(
                    body=models.ListAllowedCPCodesRequestBody(
                        client_type="CLIENT",
                    ),
                ),
            )
        mock_session.exec.assert_not_called()

    def test_validation_missing_body(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="cannot be blank"):
            iam_client.list_allowed_cp_codes(
                models.ListAllowedCPCodesRequest(user_name="jdoe"),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrListAllowedCPCodes)
        with pytest.raises(Error) as exc_info:
            iam_client.list_allowed_cp_codes(
                models.ListAllowedCPCodesRequest(
                    user_name="jsmith",
                    body=models.ListAllowedCPCodesRequestBody(
                        client_type="CLIENT",
                    ),
                ),
            )
        assert exc_info.value.status_code == 500


class TestListAuthorizedUsers:
    """Mirrors TestIAM_ListAuthorizedUsers."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "uiIdentityId": "A-BC-1234567",
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@mycompany.com",
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_authorized_users()
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/users",
            expect_json=True,
        )
        assert len(result) == 1

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrListAuthorizedUsers)
        with pytest.raises(Error) as exc_info:
            iam_client.list_authorized_users()
        assert exc_info.value.status_code == 500


class TestListAllowedAPIs:
    """Mirrors TestIAM_ListAllowedAPIs."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "apiId": 12345,
            "apiName": "Test API",
            "description": "Test",
            "endPoint": "/test",
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_allowed_apis(
            models.ListAllowedAPIsRequest(
                user_name="jdoe",
                client_type="CLIENT",
                allow_account_switch=False,
            ),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/users/jdoe/allowed-apis",
            params={
                "clientType": "CLIENT",
                "allowAccountSwitch": 'false',
            },
            expect_json=True,
        )
        assert len(result) == 1

    def test_200_ok_with_allow_account_switch(
        self, iam_client, mock_session,
    ):
        resp_body = json.dumps([{
            "apiId": 12345,
            "apiName": "Test API",
            "description": "Test",
            "endPoint": "/test",
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_allowed_apis(
            models.ListAllowedAPIsRequest(
                user_name="jdoe",
                client_type="CLIENT",
                allow_account_switch=True,
            ),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/users/jdoe/allowed-apis",
            params={
                "clientType": "CLIENT",
                "allowAccountSwitch": 'true',
            },
            expect_json=True,
        )
        assert len(result) == 1

    def test_validation_missing_user_name(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="UserName: cannot be blank"):
            iam_client.list_allowed_apis(
                models.ListAllowedAPIsRequest(
                    client_type="CLIENT",
                    allow_account_switch=False,
                ),
            )
        mock_session.exec.assert_not_called()

    def test_validation_wrong_client_type(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="ClientType.*invalid"):
            iam_client.list_allowed_apis(
                models.ListAllowedAPIsRequest(
                    user_name="jdoe",
                    client_type="Test",
                    allow_account_switch=False,
                ),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrListAllowedAPIs)
        with pytest.raises(Error) as exc_info:
            iam_client.list_allowed_apis(
                models.ListAllowedAPIsRequest(
                    user_name="jdoe",
                    client_type="CLIENT",
                    allow_account_switch=False,
                ),
            )
        assert exc_info.value.status_code == 500


class TestAccessibleGroups:
    """Mirrors TestIAM_AccessibleGroups."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "groupId": 12345,
            "roleId": 1,
            "groupName": "TestGroup",
            "isBlocked": False,
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_accessible_groups(
            models.ListAccessibleGroupsRequest(user_name="jdoe"),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/users/jdoe/group-access",
            expect_json=True,
        )
        assert len(result) == 1

    def test_validation_missing_user_name(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="UserName: cannot be blank"):
            iam_client.list_accessible_groups(
                models.ListAccessibleGroupsRequest(),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrAccessibleGroups)
        with pytest.raises(Error) as exc_info:
            iam_client.list_accessible_groups(
                models.ListAccessibleGroupsRequest(user_name="jdoe"),
            )
        assert exc_info.value.status_code == 500


# ===================================================================
# 9. IP Allowlist Tests — from ip_allowlist_test.go
# ===================================================================


class TestDisableIPAllowlist:
    """Mirrors TestIAM_DisableIPAllowlist."""

    def test_204_no_content(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        iam_client.disable_ip_allowlist()
        assert_exec_called_with(
            mock_session, "POST",
            "/identity-management/v3/user-admin/ip-acl/allowlist/disable",
        )

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrDisableIPAllowlist)
        with pytest.raises(Error) as exc_info:
            iam_client.disable_ip_allowlist()
        assert exc_info.value.status_code == 500


class TestEnableIPAllowlist:
    """Mirrors TestIAM_EnableIPAllowlist."""

    def test_204_no_content(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        iam_client.enable_ip_allowlist()
        assert_exec_called_with(
            mock_session, "POST",
            "/identity-management/v3/user-admin/ip-acl/allowlist/enable",
        )

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrEnableIPAllowlist)
        with pytest.raises(Error) as exc_info:
            iam_client.enable_ip_allowlist()
        assert exc_info.value.status_code == 500


class TestGetIPAllowlistStatus:
    """Mirrors TestIAM_GetIPAllowlistStatus."""

    def test_200_ok_enabled_true(self, iam_client, mock_session):
        resp_body = json.dumps({"enabled": True})
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.get_ip_allowlist_status()
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/ip-acl/allowlist/status",
            expect_json=True,
        )
        assert result.enabled is True

    def test_200_ok_enabled_false(self, iam_client, mock_session):
        resp_body = json.dumps({"enabled": False})
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.get_ip_allowlist_status()
        assert result.enabled is False

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrGetIPAllowlistStatus)
        with pytest.raises(Error) as exc_info:
            iam_client.get_ip_allowlist_status()
        assert exc_info.value.status_code == 500


# ===================================================================
# 10. Properties Tests — from properties_test.go
# ===================================================================


class TestListProperties:
    """Mirrors TestIAM_ListProperties."""

    def test_200_ok_no_query_params(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "propertyId": 12345,
            "propertyName": "TestProperty",
            "propertyTypeDescription": "Web Performance",
            "groupId": 67890,
            "groupName": "TestGroup",
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_properties(
            models.ListPropertiesRequest(actions=False),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/properties",
            params={"actions": 'false'},
            expect_json=True,
        )
        assert len(result) == 1

    def test_200_ok_with_query_params(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "propertyId": 12345,
            "propertyName": "TestProperty",
            "propertyTypeDescription": "Web Performance",
            "groupId": 67890,
            "groupName": "TestGroup",
            "actions": {"move": True},
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_properties(
            models.ListPropertiesRequest(
                actions=True, group_id=12345,
            ),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/properties",
            params={"actions": 'true', "groupId": '12345'},
            expect_json=True,
        )
        assert len(result) == 1

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_processing_error(
            ErrListProperties,
        )
        with pytest.raises(Error) as exc_info:
            iam_client.list_properties(
                models.ListPropertiesRequest(actions=False),
            )
        assert exc_info.value.status_code == 500


class TestListUsersForProperty:
    """Mirrors TestIAM_ListUserForProperty."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "uiIdentityId": "A-BC-1234567",
            "firstName": "John",
            "lastName": "Doe",
            "isBlocked": False,
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_users_for_property(
            models.ListUsersForPropertyRequest(
                property_id=12345, user_type="all",
            ),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/properties/12345/users",
            params={"userType": "all"},
            expect_json=True,
        )
        assert len(result) == 1

    def test_validation_missing_property_id(self, iam_client, mock_session):
        with pytest.raises(
            ValueError, match="PropertyID: cannot be blank",
        ):
            iam_client.list_users_for_property(
                models.ListUsersForPropertyRequest(user_type="all"),
            )
        mock_session.exec.assert_not_called()

    def test_validation_missing_user_type(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="UserType:.*invalid"):
            iam_client.list_users_for_property(
                models.ListUsersForPropertyRequest(property_id=12345),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_processing_error(
            ErrListUsersForProperty,
        )
        with pytest.raises(Error) as exc_info:
            iam_client.list_users_for_property(
                models.ListUsersForPropertyRequest(
                    property_id=12345, user_type="all",
                ),
            )
        assert exc_info.value.status_code == 500


class TestGetProperty:
    """Mirrors TestIAM_GetProperty."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps({
            "arlConfigFile": "test.xml",
            "propertyId": 12345,
            "propertyName": "TestProperty",
            "propertyTypeDescription": "Web Performance",
            "groupId": 67890,
            "groupName": "TestGroup",
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.get_property(
            models.GetPropertyRequest(
                property_id=12345, group_id=67890,
            ),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/properties/12345",
            params={"groupId": '67890'},
            expect_json=True,
        )
        assert result.property_id == 12345

    def test_validation_missing_property_id(self, iam_client, mock_session):
        with pytest.raises(
            ValueError, match="PropertyID: cannot be blank",
        ):
            iam_client.get_property(
                models.GetPropertyRequest(group_id=67890),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_processing_error(
            ErrGetProperty,
        )
        with pytest.raises(Error) as exc_info:
            iam_client.get_property(
                models.GetPropertyRequest(
                    property_id=12345, group_id=67890,
                ),
            )
        assert exc_info.value.status_code == 500


class TestMoveProperty:
    """Mirrors TestIAM_MoveProperty."""

    def test_204_no_content(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        iam_client.move_property(
            models.MovePropertyRequest(
                property_id=12345,
                body=models.MovePropertyRequestBody(
                    destination_group_id=67890,
                    source_group_id=11111,
                ),
            ),
        )
        assert_exec_called_with(
            mock_session, "PUT",
            "/identity-management/v3/user-admin/properties/12345",
        )

    def test_validation_missing_property_id(self, iam_client, mock_session):
        with pytest.raises(
            ValueError, match="PropertyID: cannot be blank",
        ):
            iam_client.move_property(
                models.MovePropertyRequest(
                    body=models.MovePropertyRequestBody(
                        destination_group_id=67890,
                    ),
                ),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_processing_error(
            ErrMoveProperty,
        )
        with pytest.raises(Error) as exc_info:
            iam_client.move_property(
                models.MovePropertyRequest(
                    property_id=12345,
                    body=models.MovePropertyRequestBody(
                        destination_group_id=67890,
                        source_group_id=11111,
                    ),
                ),
            )
        assert exc_info.value.status_code == 500


class TestMapPropertyIDToName:
    """Mirrors TestIAM_MapPropertyIDToName."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps({
            "arlConfigFile": "test.xml",
            "propertyId": 12345,
            "propertyName": "TestProperty",
            "propertyTypeDescription": "Web Performance",
            "groupId": 67890,
            "groupName": "TestGroup",
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.map_property_id_to_name(
            models.MapPropertyIDToNameRequest(
                property_id=12345, group_id=67890,
            ),
        )
        assert result is not None
        assert result == "TestProperty"

    def test_validation_missing_property_id(self, iam_client, mock_session):
        with pytest.raises(
            ValueError, match="PropertyID: cannot be blank",
        ):
            iam_client.map_property_id_to_name(
                models.MapPropertyIDToNameRequest(group_id=67890),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_processing_error(
            ErrGetProperty,
        )
        with pytest.raises(ValueError, match="map property by id"):
            iam_client.map_property_id_to_name(
                models.MapPropertyIDToNameRequest(
                    property_id=12345, group_id=67890,
                ),
            )


class TestBlockUsers:
    """Mirrors TestIAM_BlockUsers."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps([
            {
                "firstName": "John",
                "isBlocked": True,
                "lastName": "Doe",
                "uiIdentityId": "A-BC-1234567",
                "uiUserName": "jdoe",
            },
        ])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.block_users(
            models.BlockUsersRequest(
                property_id=12345,
                body=[
                    models.BlockUserItem(
                        ui_identity_id="A-BC-1234567",
                    ),
                ],
            ),
        )
        assert_exec_called_with(
            mock_session, "PUT",
            "/identity-management/v3/user-admin/properties"
            "/12345/users/block",
        )
        assert len(result) == 1

    def test_validation_missing_property_id(self, iam_client, mock_session):
        with pytest.raises(
            ValueError, match="PropertyID: cannot be blank",
        ):
            iam_client.block_users(
                models.BlockUsersRequest(
                    body=[
                        models.BlockUserItem(
                            ui_identity_id="A-BC-1234567",
                        ),
                    ],
                ),
            )
        mock_session.exec.assert_not_called()

    def test_validation_missing_body(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="cannot be blank"):
            iam_client.block_users(
                models.BlockUsersRequest(property_id=12345),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_processing_error(
            ErrBlockUsers,
        )
        with pytest.raises(Error) as exc_info:
            iam_client.block_users(
                models.BlockUsersRequest(
                    property_id=12345,
                    body=[
                        models.BlockUserItem(
                            ui_identity_id="A-BC-1234567",
                        ),
                    ],
                ),
            )
        assert exc_info.value.status_code == 500


# ===================================================================
# 11. Roles Tests — from roles_test.go
# ===================================================================


class TestCreateRole:
    """Mirrors TestIAM_CreateRole."""

    def test_201_created(self, iam_client, mock_session):
        resp_body = json.dumps({
            "roleId": 12345,
            "roleName": "TestRole",
            "roleDescription": "Test role description",
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "modifiedBy": "jdoe",
            "modifiedDate": "2022-05-13T20:04:35.000Z",
            "type": "custom",
        })
        mock_session.exec.return_value = (
            mock_response(201, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.create_role(
            models.RoleRequest(
                name="TestRole",
                description="Test role description",
                granted_roles=[
                    models.GrantedRoleID(id=1),
                ],
            ),
        )
        assert_exec_called_with(
            mock_session, "POST",
            "/identity-management/v3/user-admin/roles",
        )
        assert result.role_id == 12345

    def test_missing_role_name(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="Name: cannot be blank"):
            iam_client.create_role(
                models.RoleRequest(
                    description="Test",
                    granted_roles=[
                        models.GrantedRoleID(id=1),
                    ],
                ),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrCreateRole)
        with pytest.raises(Error) as exc_info:
            iam_client.create_role(
                models.RoleRequest(
                    name="TestRole",
                    description="Test",
                    granted_roles=[
                        models.GrantedRoleID(id=1),
                    ],
                ),
            )
        assert exc_info.value.status_code == 500


class TestGetRole:
    """Mirrors TestIAM_GetRole."""

    def test_200_ok_minimal(self, iam_client, mock_session):
        resp_body = json.dumps({
            "roleId": 12345,
            "roleName": "TestRole",
            "roleDescription": "Test role",
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "modifiedBy": "jdoe",
            "modifiedDate": "2022-05-13T20:04:35.000Z",
            "type": "custom",
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.get_role(
            models.GetRoleRequest(
                id=12345,
                actions=False,
                granted_roles=False,
                users=False,
            ),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/roles/12345",
            params={
                "actions": 'false',
                "grantedRoles": 'false',
                "users": 'false',
            },
            expect_json=True,
        )
        assert result.role_id == 12345

    def test_200_ok_with_params(self, iam_client, mock_session):
        resp_body = json.dumps({
            "roleId": 12345,
            "roleName": "TestRole",
            "roleDescription": "Test role",
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "modifiedBy": "jdoe",
            "modifiedDate": "2022-05-13T20:04:35.000Z",
            "type": "custom",
            "grantedRoles": [{"grantedRoleId": 1, "grantedRoleName": "admin"}],
            "users": [{"uiIdentityId": "A-BC-1234567"}],
            "actions": {"edit": True, "delete": True},
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.get_role(
            models.GetRoleRequest(
                id=12345,
                actions=True,
                granted_roles=True,
                users=True,
            ),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/roles/12345",
            params={
                "actions": 'true',
                "grantedRoles": 'true',
                "users": 'true',
            },
            expect_json=True,
        )
        assert result.role_id == 12345

    def test_validation_missing_role_id(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="ID: cannot be blank"):
            iam_client.get_role(
                models.GetRoleRequest(
                    actions=False, granted_roles=False, users=False,
                ),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrGetRole)
        with pytest.raises(Error) as exc_info:
            iam_client.get_role(
                models.GetRoleRequest(
                    id=12345,
                    actions=False,
                    granted_roles=False,
                    users=False,
                ),
            )
        assert exc_info.value.status_code == 500


class TestUpdateRole:
    """Mirrors TestIAM_UpdateRole."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps({
            "roleId": 12345,
            "roleName": "UpdatedRole",
            "roleDescription": "Updated",
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "modifiedBy": "jdoe",
            "modifiedDate": "2022-05-13T21:04:35.000Z",
            "type": "custom",
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.update_role(
            models.UpdateRoleRequest(
                id=12345,
                name="UpdatedRole",
                description="Updated",
                granted_roles=[
                    models.GrantedRoleID(id=1),
                ],
            ),
        )
        assert_exec_called_with(
            mock_session, "PUT",
            "/identity-management/v3/user-admin/roles/12345",
        )
        assert result.role_name == "UpdatedRole"

    def test_validation_missing_role_id(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="ID: cannot be blank"):
            iam_client.update_role(
                models.UpdateRoleRequest(
                    name="UpdatedRole",
                    description="Updated",
                ),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrUpdateRole)
        with pytest.raises(Error) as exc_info:
            iam_client.update_role(
                models.UpdateRoleRequest(
                    id=12345,
                    name="UpdatedRole",
                    description="Updated",
                ),
            )
        assert exc_info.value.status_code == 500


class TestDeleteRole:
    """Mirrors TestIAM_DeleteRole."""

    def test_204_no_content(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        iam_client.delete_role(
            models.DeleteRoleRequest(id=12345),
        )
        assert_exec_called_with(
            mock_session, "DELETE",
            "/identity-management/v3/user-admin/roles/12345",
        )

    def test_validation_missing_role_id(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="ID: cannot be blank"):
            iam_client.delete_role(models.DeleteRoleRequest())
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrDeleteRole)
        with pytest.raises(Error) as exc_info:
            iam_client.delete_role(
                models.DeleteRoleRequest(id=12345),
            )
        assert exc_info.value.status_code == 500


class TestListRoles:
    """Mirrors TestIAM_ListRoles."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "roleId": 12345,
            "roleName": "TestRole",
            "roleDescription": "Test",
            "type": "custom",
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "modifiedBy": "jdoe",
            "modifiedDate": "2022-05-13T20:04:35.000Z",
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_roles(
            models.ListRolesRequest(actions=False),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/roles",
            expect_json=True,
        )
        assert len(result) == 1

    def test_200_ok_with_params(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "roleId": 12345,
            "roleName": "TestRole",
            "roleDescription": "Test",
            "type": "custom",
            "createdBy": "jdoe",
            "createdDate": "2022-05-13T20:04:35.000Z",
            "modifiedBy": "jdoe",
            "modifiedDate": "2022-05-13T20:04:35.000Z",
            "grantedRoles": [{"grantedRoleId": 1}],
            "actions": {"edit": True, "delete": True},
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_roles(
            models.ListRolesRequest(
                actions=True,
                group_id=12345,
                ignore_context=True,
                users=True,
            ),
        )
        assert len(result) == 1

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrListRoles)
        with pytest.raises(Error) as exc_info:
            iam_client.list_roles(
                models.ListRolesRequest(actions=False),
            )
        assert exc_info.value.status_code == 500


class TestListGrantableRoles:
    """Mirrors TestIAM_ListGrantableRoles."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "grantedRoleId": 1,
            "grantedRoleName": "admin",
            "grantedRoleDescription": "Administrator",
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_grantable_roles()
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/roles/grantable-roles",
            expect_json=True,
        )
        assert len(result) == 1

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrListGrantableRoles)
        with pytest.raises(Error) as exc_info:
            iam_client.list_grantable_roles()
        assert exc_info.value.status_code == 500


# ===================================================================
# 12. Support Tests — from support_test.go
# ===================================================================


class TestGetPasswordPolicy:
    """Mirrors TestIAM_GetPasswordPolicy."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps({
            "caseDif": 1,
            "maxRepeating": 2,
            "minDigits": 1,
            "minLength": 8,
            "minLetters": 1,
            "minNonAlpha": 1,
            "minReuse": 4,
            "pwclass": "B",
            "rotateFrequency": 365,
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.get_password_policy()
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/common/password-policy",
            expect_json=True,
        )
        assert result.min_length == 8

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrGetPasswordPolicy)
        with pytest.raises(Error) as exc_info:
            iam_client.get_password_policy()
        assert exc_info.value.status_code == 500


class TestSupportedCountries:
    """Mirrors TestIAM_SupportedCountries."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps(["Greece", "Greenland", "Grenada"])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.supported_countries()
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/common"
            "/countries",
            expect_json=True,
        )
        assert result == ["Greece", "Greenland", "Grenada"]

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrSupportedCountries)
        with pytest.raises(Error) as exc_info:
            iam_client.supported_countries()
        assert exc_info.value.status_code == 500


class TestSupportedTimezones:
    """Mirrors TestIAM_SupportedTimezones."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps([
            {
                "timezone": "Asia/Aden",
                "description": "(GMT+03:00) Aden",
                "offset": "+0300",
                "posix": "GST-4",
            },
            {
                "timezone": "Asia/Almaty",
                "description": "(GMT+06:00) Almaty",
                "offset": "+0600",
                "posix": "NOVST-7",
            },
        ])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.supported_timezones()
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/common"
            "/timezones",
            expect_json=True,
        )
        assert len(result) == 2

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrSupportedTimezones)
        with pytest.raises(Error) as exc_info:
            iam_client.supported_timezones()
        assert exc_info.value.status_code == 500


class TestSupportedContactTypes:
    """Mirrors TestIAM_SupportedContactTypes."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps(["Billing", "Security"])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.supported_contact_types()
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/common"
            "/contact-types",
            expect_json=True,
        )
        assert result == ["Billing", "Security"]

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrSupportedContactTypes)
        with pytest.raises(Error) as exc_info:
            iam_client.supported_contact_types()
        assert exc_info.value.status_code == 500


class TestSupportedLanguages:
    """Mirrors TestIAM_SupportedLanguages."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps(["Deutsch", "English"])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.supported_languages()
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/common"
            "/supported-languages",
            expect_json=True,
        )
        assert result == ["Deutsch", "English"]

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrSupportedLanguages)
        with pytest.raises(Error) as exc_info:
            iam_client.supported_languages()
        assert exc_info.value.status_code == 500


class TestListProducts:
    """Mirrors TestIAM_ListProducts."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps([
            "Adaptive Media Delivery",
            "API Gateway",
        ])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_products()
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/common/notification-products",
            expect_json=True,
        )
        assert len(result) == 2

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrListProducts)
        with pytest.raises(Error) as exc_info:
            iam_client.list_products()
        assert exc_info.value.status_code == 500


class TestListTimeoutPolicies:
    """Mirrors TestIAM_ListTimeoutPolicies."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps([
            {"value": 0, "name": "No Timeout"},
            {"value": 30, "name": "30 Minutes"},
            {"value": 60, "name": "1 Hour"},
        ])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_timeout_policies()
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/common"
            "/timeout-policies",
            expect_json=True,
        )
        assert len(result) == 3

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrListTimeoutPolicies)
        with pytest.raises(Error) as exc_info:
            iam_client.list_timeout_policies()
        assert exc_info.value.status_code == 500


class TestListStates:
    """Mirrors TestIAM_ListStates."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps([
            "Alabama", "Alaska", "Arizona",
        ])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_states(
            models.ListStatesRequest(country="USA"),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/common/countries/USA/states",
            expect_json=True,
        )
        assert len(result) == 3

    def test_validation_missing_country(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="Country: cannot be blank"):
            iam_client.list_states(models.ListStatesRequest())
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrListStates)
        with pytest.raises(Error) as exc_info:
            iam_client.list_states(
                models.ListStatesRequest(country="USA"),
            )
        assert exc_info.value.status_code == 500


class TestListAccountSwitchKeys:
    """Mirrors TestIAM_ListAccountSwitchKeys."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "accountSwitchKey": "F-AC-1234567",
            "accountName": "TestAccount",
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_account_switch_keys(
            models.ListAccountSwitchKeysRequest(),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/api-clients/self/account-switch-keys",
            expect_json=True,
        )
        assert len(result) == 1

    def test_200_ok_with_client_id(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "accountSwitchKey": "F-AC-1234567",
            "accountName": "TestAccount",
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_account_switch_keys(
            models.ListAccountSwitchKeysRequest(client_id="test1234"),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/api-clients"
            "/test1234/account-switch-keys",
            expect_json=True,
        )
        assert len(result) == 1

    def test_200_ok_with_search(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "accountSwitchKey": "F-AC-1234567",
            "accountName": "TestAccount",
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_account_switch_keys(
            models.ListAccountSwitchKeysRequest(search="Test"),
        )
        assert len(result) == 1

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(
            ErrListAccountSwitchKeys,
        )
        with pytest.raises(Error) as exc_info:
            iam_client.list_account_switch_keys(
                models.ListAccountSwitchKeysRequest(),
            )
        assert exc_info.value.status_code == 500


# ===================================================================
# 13. User Tests — from user_test.go
# ===================================================================


class TestCreateUser:
    """Mirrors TestIAM_CreateUser."""

    def test_201_ok(self, iam_client, mock_session):
        resp_body = json.dumps({
            "uiIdentityId": "A-BC-1234567",
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@mycompany.com",
            "phone": "(123) 321-1234",
            "state": "CA",
            "country": "USA",
            "additionalAuthenticationConfigured": False,
            "additionalAuthentication": "NONE",
        })
        mock_session.exec.return_value = (
            mock_response(201, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.create_user(
            models.CreateUserRequest(
                first_name="John",
                last_name="Doe",
                email="john.doe@mycompany.com",
                phone="(123) 321-1234",
                country="USA",
                state="CA",
                additional_authentication="NONE",
                auth_grants=[
                    models.AuthGrantRequest(group_id=1, role_id=1),
                ],
                send_email=False,
            ),
        )
        assert_exec_called_with(
            mock_session, "POST",
            "/identity-management/v3/user-admin/ui-identities",
            params={"sendEmail": 'false'},
        )
        assert result.identity_id == "A-BC-1234567"

    def test_201_ok_all_fields(self, iam_client, mock_session):
        resp_body = json.dumps({
            "uiIdentityId": "A-BC-1234567",
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@mycompany.com",
            "phone": "(123) 321-1234",
            "state": "CA",
            "country": "USA",
            "additionalAuthenticationConfigured": False,
            "additionalAuthentication": "NONE",
        })
        mock_session.exec.return_value = (
            mock_response(201, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.create_user(
            models.CreateUserRequest(
                first_name="John",
                last_name="Doe",
                user_name="UserName",
                email="john.doe@mycompany.com",
                phone="(123) 321-1234",
                time_zone="GMT+2",
                job_title="Title",
                secondary_email="second@email.com",
                mobile_phone="123123123",
                address="Address",
                city="City",
                state="CA",
                zip_code="11-111",
                country="USA",
                contact_type="Dev",
                preferred_language="EN",
                session_time_out=1,
                additional_authentication="MFA",
                auth_grants=[
                    models.AuthGrantRequest(group_id=1, role_id=1),
                ],
                send_email=True,
                notifications=models.UserNotifications(
                    enable_email=False,
                    options=models.UserNotificationOptions(
                        new_user=False,
                        password_expiry=False,
                        proactive=["Test1"],
                        upgrade=["Test2"],
                        api_client_credential_expiry=False,
                    ),
                ),
            ),
        )
        assert_exec_called_with(
            mock_session, "POST",
            "/identity-management/v3/user-admin/ui-identities",
            params={"sendEmail": 'true'},
        )
        assert result.identity_id == "A-BC-1234567"

    def test_validation_errors(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="cannot be blank"):
            iam_client.create_user(models.CreateUserRequest())
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrCreateUser)
        with pytest.raises(Error) as exc_info:
            iam_client.create_user(
                models.CreateUserRequest(
                    first_name="John",
                    last_name="Doe",
                    email="john.doe@mycompany.com",
                    phone="(123) 321-1234",
                    country="USA",
                    state="CA",
                    additional_authentication="TFA",
                    auth_grants=[
                        models.AuthGrantRequest(group_id=1, role_id=1),
                    ],
                    send_email=False,
                ),
            )
        assert exc_info.value.status_code == 500


class TestGetUser:
    """Mirrors TestIAM_GetUser."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps({
            "uiIdentityId": "A-BC-1234567",
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@mycompany.com",
            "phone": "(123) 321-1234",
            "state": "CA",
            "country": "USA",
            "accountId": "sampleID",
            "userStatus": "PENDING",
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.get_user(
            models.GetUserRequest(
                identity_id="A-BC-1234567",
                actions=False,
                auth_grants=False,
                notifications=False,
            ),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/ui-identities/A-BC-1234567",
            params={
                "actions": 'false',
                "authGrants": 'false',
                "notifications": 'false',
            },
            expect_json=True,
        )
        assert result.identity_id == "A-BC-1234567"

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrGetUser)
        with pytest.raises(Error) as exc_info:
            iam_client.get_user(
                models.GetUserRequest(
                    identity_id="A-BC-1234567",
                    actions=False,
                    auth_grants=False,
                    notifications=False,
                ),
            )
        assert exc_info.value.status_code == 500


class TestListUsers:
    """Mirrors TestIAM_ListUsers."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "uiIdentityId": "A-B-123456",
            "firstName": "John",
            "lastName": "Doe",
            "uiUserName": "johndoe",
            "email": "john.doe@mycompany.com",
            "accountId": "1-123A",
            "lastLoginDate": "2016-01-13T17:53:57.000Z",
            "tfaEnabled": True,
            "tfaConfigured": True,
            "isLocked": False,
            "additionalAuthentication": "TFA",
            "additionalAuthenticationConfigured": False,
            "actions": {
                "resetPassword": True,
                "delete": True,
                "edit": True,
                "apiClient": True,
                "thirdPartyAccess": True,
                "isCloneable": True,
                "editProfile": True,
                "canEditTFA": True,
                "canEditMFA": True,
                "canEditNone": True,
            },
            "authGrants": [{
                "groupId": 12345,
                "roleId": 12,
                "groupName": "mygroup",
                "roleName": "admin",
                "roleDescription":
                    "This is a new role that has been created to",
                "isBlocked": False,
            }],
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_users(
            models.ListUsersRequest(
                group_id=12345,
                actions=True,
                auth_grants=True,
            ),
        )
        assert_exec_called_with(
            mock_session, "GET",
            "/identity-management/v3/user-admin/ui-identities",
            expect_json=True,
        )
        assert len(result) == 1

    def test_200_ok_no_actions_nor_grants(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "uiIdentityId": "A-B-123456",
            "firstName": "John",
            "lastName": "Doe",
            "uiUserName": "johndoe",
            "email": "john.doe@mycompany.com",
            "accountId": "1-123A",
            "lastLoginDate": "2016-01-13T17:53:57.000Z",
            "tfaEnabled": True,
            "tfaConfigured": True,
            "isLocked": False,
            "additionalAuthentication": "MFA",
            "additionalAuthenticationConfigured": True,
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_users(
            models.ListUsersRequest(
                group_id=12345,
                actions=False,
                auth_grants=False,
            ),
        )
        assert len(result) == 1

    def test_200_ok_no_group_id(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "uiIdentityId": "A-B-123456",
            "firstName": "John",
            "lastName": "Doe",
            "uiUserName": "johndoe",
            "email": "john.doe@mycompany.com",
            "accountId": "1-123A",
            "lastLoginDate": "2016-01-13T17:53:57.000Z",
            "tfaEnabled": True,
            "tfaConfigured": True,
            "isLocked": False,
            "additionalAuthentication": "TFA",
            "additionalAuthenticationConfigured": True,
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.list_users(
            models.ListUsersRequest(
                actions=False,
                auth_grants=False,
            ),
        )
        assert len(result) == 1

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_processing_error(
            ErrListUsers,
        )
        with pytest.raises(Error) as exc_info:
            iam_client.list_users(
                models.ListUsersRequest(
                    actions=False,
                    auth_grants=False,
                ),
            )
        assert exc_info.value.status_code == 500


class TestUpdateUserInfo:
    """Mirrors TestIAM_UpdateUserInfo."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps({
            "firstName": "John",
            "lastName": "Doe",
            "email": "john.doe@mycompany.com",
            "phone": "(123) 321-1234",
            "state": "CA",
            "country": "USA",
            "preferredLanguage": "English",
            "contactType": "Billing",
            "sessionTimeOut": 30,
            "timeZone": "GMT",
            "additionalAuthentication": "NONE",
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.update_user_info(
            models.UpdateUserInfoRequest(
                identity_id="1-ABCDE",
                user=models.UserBasicInfo(
                    first_name="John",
                    last_name="Doe",
                    email="john.doe@mycompany.com",
                    phone="(123) 321-1234",
                    time_zone="GMT",
                    state="CA",
                    country="USA",
                    contact_type="Billing",
                    preferred_language="English",
                    session_time_out=30,
                    additional_authentication="NONE",
                ),
            ),
        )
        assert_exec_called_with(
            mock_session, "PUT",
            "/identity-management/v3/user-admin"
            "/ui-identities/1-ABCDE/basic-info",
        )
        assert result.first_name == "John"

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrUpdateUserInfo)
        with pytest.raises(Error) as exc_info:
            iam_client.update_user_info(
                models.UpdateUserInfoRequest(
                    identity_id="1-ABCDE",
                    user=models.UserBasicInfo(
                        first_name="John",
                        last_name="Doe",
                        email="john.doe@mycompany.com",
                        phone="(123) 321-1234",
                        country="USA",
                        preferred_language="English",
                        session_time_out=30,
                        time_zone="GMT",
                    ),
                ),
            )
        assert exc_info.value.status_code == 500


class TestUpdateUserNotifications:
    """Mirrors TestIAM_UpdateUserNotifications."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps({
            "enableEmailNotifications": True,
            "options": {
                "upgrade": [
                    "NetStorage",
                    "Other Upgrade Notifications (Planned)",
                ],
                "proactive": [
                    "EdgeScape",
                    "EdgeSuite (HTTP Content Delivery)",
                ],
                "passwordExpiry": True,
                "newUserNotification": True,
                "apiClientCredentialExpiryNotification": True,
            },
        })
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.update_user_notifications(
            models.UpdateUserNotificationsRequest(
                identity_id="1-ABCDE",
                notifications=models.UserNotifications(
                    enable_email=True,
                    options=models.UserNotificationOptions(
                        new_user=True,
                        password_expiry=True,
                        proactive=[
                            "EdgeScape",
                            "EdgeSuite (HTTP Content Delivery)",
                        ],
                        upgrade=[
                            "NetStorage",
                            "Other Upgrade Notifications (Planned)",
                        ],
                        api_client_credential_expiry=True,
                    ),
                ),
            ),
        )
        assert_exec_called_with(
            mock_session, "PUT",
            "/identity-management/v3/user-admin"
            "/ui-identities/1-ABCDE/notifications",
        )
        assert result.enable_email is True

    def test_validation_errors(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="cannot be blank"):
            iam_client.update_user_notifications(
                models.UpdateUserNotificationsRequest(),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(
            ErrUpdateUserNotifications,
        )
        with pytest.raises(Error) as exc_info:
            iam_client.update_user_notifications(
                models.UpdateUserNotificationsRequest(
                    identity_id="1-ABCDE",
                    notifications=models.UserNotifications(
                        enable_email=True,
                        options=models.UserNotificationOptions(),
                    ),
                ),
            )
        assert exc_info.value.status_code == 500


class TestUpdateUserAuthGrants:
    """Mirrors TestIAM_UpdateUserAuthGrants."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps([{
            "groupId": 12345,
            "roleId": 16,
            "subGroups": [{"groupId": 54321}],
        }])
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.update_user_auth_grants(
            models.UpdateUserAuthGrantsRequest(
                identity_id="1-ABCDE",
                auth_grants=[
                    models.AuthGrant(
                        group_id=12345,
                        role_id=16,
                        subgroups=[
                            models.AuthGrant(group_id=54321),
                        ],
                    ),
                ],
            ),
        )
        assert_exec_called_with(
            mock_session, "PUT",
            "/identity-management/v3/user-admin"
            "/ui-identities/1-ABCDE/auth-grants",
        )
        assert len(result) == 1

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(
            ErrUpdateUserAuthGrants,
        )
        with pytest.raises(Error) as exc_info:
            iam_client.update_user_auth_grants(
                models.UpdateUserAuthGrantsRequest(
                    identity_id="1-ABCDE",
                    auth_grants=[
                        models.AuthGrant(group_id=12345, role_id=16),
                    ],
                ),
            )
        assert exc_info.value.status_code == 500


class TestRemoveUser:
    """Mirrors TestIAM_RemoveUser."""

    def test_200_ok(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(200, ""), None)
        iam_client.remove_user(
            models.RemoveUserRequest(identity_id="1-ABCDE"),
        )
        assert_exec_called_with(
            mock_session, "DELETE",
            "/identity-management/v3/user-admin"
            "/ui-identities/1-ABCDE",
        )

    def test_204_no_content(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        iam_client.remove_user(
            models.RemoveUserRequest(identity_id="1-ABCDE"),
        )

    def test_validation_errors(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="cannot be blank"):
            iam_client.remove_user(models.RemoveUserRequest())
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrRemoveUser)
        with pytest.raises(Error) as exc_info:
            iam_client.remove_user(
                models.RemoveUserRequest(identity_id="1-ABCDE"),
            )
        assert exc_info.value.status_code == 500


class TestUpdateMFA:
    """Mirrors TestIAM_UpdateMFA."""

    def test_204_no_content(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        iam_client.update_mfa(
            models.UpdateMFARequest(
                identity_id="1-ABCDE",
                value="MFA",
            ),
        )
        assert_exec_called_with(
            mock_session, "PUT",
            "/identity-management/v3/user-admin"
            "/ui-identities/1-ABCDE/additionalAuthentication",
        )

    def test_validation_invalid_value(self, iam_client, mock_session):
        with pytest.raises(ValueError, match="Value"):
            iam_client.update_mfa(
                models.UpdateMFARequest(
                    identity_id="1-ABCDE",
                    value="INVALID",
                ),
            )
        mock_session.exec.assert_not_called()

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrUpdateMFA)
        with pytest.raises(Error) as exc_info:
            iam_client.update_mfa(
                models.UpdateMFARequest(
                    identity_id="1-ABCDE",
                    value="MFA",
                ),
            )
        assert exc_info.value.status_code == 500


class TestResetMFA:
    """Mirrors TestIAM_ResetMFA."""

    def test_204_no_content(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        iam_client.reset_mfa(
            models.ResetMFARequest(identity_id="1-ABCDE"),
        )
        assert_exec_called_with(
            mock_session, "PUT",
            "/identity-management/v3/user-admin/ui-identities"
            "/1-ABCDE/additionalAuthentication/reset",
        )

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrResetMFA)
        with pytest.raises(Error) as exc_info:
            iam_client.reset_mfa(
                models.ResetMFARequest(identity_id="1-ABCDE"),
            )
        assert exc_info.value.status_code == 500


# ===================================================================
# 14. User Lock Tests — from user_lock_test.go
# ===================================================================


class TestLockUser:
    """Mirrors TestIAM_LockUser."""

    def test_200_ok(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(200, ""), None)
        iam_client.lock_user(
            models.LockUserRequest(identity_id="A-BC-1234567"),
        )
        assert_exec_called_with(
            mock_session, "POST",
            "/identity-management/v3/user-admin/ui-identities"
            "/A-BC-1234567/lock",
        )

    def test_204_no_content(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        iam_client.lock_user(
            models.LockUserRequest(identity_id="A-BC-1234567"),
        )

    def test_404_not_found(self, iam_client, mock_session):
        mock_session.exec.side_effect = Error(
            type="/useradmin-api/error-types/1100",
            title=f"{ErrLockUser}: User not found",
            http_status=404, status_code=404,
        )
        with pytest.raises(Error) as exc_info:
            iam_client.lock_user(
                models.LockUserRequest(identity_id="A-BC-1234567"),
            )
        assert exc_info.value.status_code == 404

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrLockUser)
        with pytest.raises(Error) as exc_info:
            iam_client.lock_user(
                models.LockUserRequest(identity_id="A-BC-1234567"),
            )
        assert exc_info.value.status_code == 500


class TestUnlockUser:
    """Mirrors TestIAM_UnlockUser."""

    def test_200_ok(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(200, ""), None)
        iam_client.unlock_user(
            models.UnlockUserRequest(identity_id="A-BC-1234567"),
        )
        assert_exec_called_with(
            mock_session, "POST",
            "/identity-management/v3/user-admin/ui-identities"
            "/A-BC-1234567/unlock",
        )

    def test_204_no_content(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        iam_client.unlock_user(
            models.UnlockUserRequest(identity_id="A-BC-1234567"),
        )

    def test_404_not_found(self, iam_client, mock_session):
        mock_session.exec.side_effect = Error(
            type="/useradmin-api/error-types/1100",
            title=f"{ErrUnlockUser}: User not found",
            http_status=404, status_code=404,
        )
        with pytest.raises(Error) as exc_info:
            iam_client.unlock_user(
                models.UnlockUserRequest(identity_id="A-BC-1234567"),
            )
        assert exc_info.value.status_code == 404

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrUnlockUser)
        with pytest.raises(Error) as exc_info:
            iam_client.unlock_user(
                models.UnlockUserRequest(identity_id="A-BC-1234567"),
            )
        assert exc_info.value.status_code == 500


# ===================================================================
# 15. User Password Tests — from user_password_test.go
# ===================================================================


class TestResetUserPassword:
    """Mirrors TestIAM_ResetUserPassword."""

    def test_200_ok(self, iam_client, mock_session):
        resp_body = json.dumps({"newPassword": "K8QVa7Q2"})
        mock_session.exec.return_value = (
            mock_response(200, resp_body),
            json.loads(resp_body),
        )
        result = iam_client.reset_user_password(
            models.ResetUserPasswordRequest(
                identity_id="A-BC-1234567",
                send_email=False,
            ),
        )
        assert_exec_called_with(
            mock_session, "POST",
            "/identity-management/v3/user-admin/ui-identities"
            "/A-BC-1234567/reset-password",
            params={"sendEmail": 'false'},
        )
        assert result is not None
        assert result.new_password == "K8QVa7Q2"

    def test_204_no_content_send_email(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        result = iam_client.reset_user_password(
            models.ResetUserPasswordRequest(
                identity_id="A-BC-1234567",
                send_email=True,
            ),
        )
        assert_exec_called_with(
            mock_session, "POST",
            "/identity-management/v3/user-admin/ui-identities"
            "/A-BC-1234567/reset-password",
            params={"sendEmail": 'true'},
        )
        assert result is None

    def test_404_not_found(self, iam_client, mock_session):
        mock_session.exec.side_effect = Error(
            type="/useradmin-api/error-types/1100",
            title=f"{ErrResetUserPassword}: User not found",
            http_status=404, status_code=404,
        )
        with pytest.raises(Error) as exc_info:
            iam_client.reset_user_password(
                models.ResetUserPasswordRequest(
                    identity_id="A-BC-1234567",
                    send_email=False,
                ),
            )
        assert exc_info.value.status_code == 404

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrResetUserPassword)
        with pytest.raises(Error) as exc_info:
            iam_client.reset_user_password(
                models.ResetUserPasswordRequest(
                    identity_id="A-BC-1234567",
                    send_email=False,
                ),
            )
        assert exc_info.value.status_code == 500


class TestSetUserPassword:
    """Mirrors TestIAM_SetUserPassword."""

    def test_204_no_content(self, iam_client, mock_session):
        mock_session.exec.return_value = (mock_response(204, ""), None)
        iam_client.set_user_password(
            models.SetUserPasswordRequest(
                identity_id="A-BC-1234567",
                new_password="newpwd",
            ),
        )
        assert_exec_called_with(
            mock_session, "POST",
            "/identity-management/v3/user-admin/ui-identities"
            "/A-BC-1234567/set-password",
        )

    def test_400_bad_request_same_password(self, iam_client, mock_session):
        mock_session.exec.side_effect = Error(
            title=f"{ErrSetUserPassword}: Bad Request",
            detail="New password must be different",
            http_status=400, status_code=400,
        )
        with pytest.raises(Error) as exc_info:
            iam_client.set_user_password(
                models.SetUserPasswordRequest(
                    identity_id="A-BC-1234567",
                    new_password="samepwd",
                ),
            )
        assert exc_info.value.status_code == 400

    def test_404_not_found(self, iam_client, mock_session):
        mock_session.exec.side_effect = Error(
            type="/useradmin-api/error-types/1100",
            title=f"{ErrSetUserPassword}: User not found",
            http_status=404, status_code=404,
        )
        with pytest.raises(Error) as exc_info:
            iam_client.set_user_password(
                models.SetUserPasswordRequest(
                    identity_id="A-BC-1234567",
                    new_password="newpwd",
                ),
            )
        assert exc_info.value.status_code == 404

    def test_500_internal_server_error(self, iam_client, mock_session):
        mock_session.exec.side_effect = _ise_error(ErrSetUserPassword)
        with pytest.raises(Error) as exc_info:
            iam_client.set_user_password(
                models.SetUserPasswordRequest(
                    identity_id="A-BC-1234567",
                    new_password="newpwd",
                ),
            )
        assert exc_info.value.status_code == 500
