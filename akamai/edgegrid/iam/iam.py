"""IAM API client providing identity management endpoint methods.

Mirrors the Go ``pkg/iam`` interface and ``iam`` struct from
``AkamaiOPEN-edgegrid-golang/v12``, providing typed Python methods for all
identity-management/v3 API endpoints.
"""
# pylint: disable=too-many-lines,too-many-public-methods

import json
import logging
from datetime import datetime, timedelta

from akamai.edgegrid.session import Session
from akamai.edgegrid.iam import models
from akamai.edgegrid.iam import errors as iam_errors
from akamai.edgegrid.iam import validation as iam_validation

logger = logging.getLogger(__name__)


class IAMClient:
    """Akamai Identity & Access Management API client.

    Provides methods for managing API clients, credentials, users, groups,
    roles, properties, CIDR blocks, and support metadata through the
    identity-management/v3 API.

    Mirrors Go ``pkg/iam.IAM`` interface and ``iam`` struct.

    Usage::

        >>> from akamai.edgegrid.session import Session
        >>> from akamai.edgegrid.iam.iam import IAMClient
        >>> session = Session(edgerc_path="~/.edgerc", section="default")
        >>> iam = IAMClient(session)
        >>> clients = iam.list_api_clients(
        ...     models.ListAPIClientsRequest(actions=True)
        ... )
    """

    def __init__(self, session: Session) -> None:
        """Initialize IAM client with an authenticated session.

        Mirrors Go ``iam.Client(sess session.Session)`` constructor.

        Args:
            session: An authenticated :class:`Session` instance.
        """
        self._session = session

    # =================================================================
    # API Client methods (api_clients.go)
    # =================================================================

    def lock_api_client(
        self, params: models.LockAPIClientRequest,
    ) -> None:
        """Lock an API client.

        If *client_id* is empty the caller's own client is locked.

        See: https://techdocs.akamai.com/iam-api/reference/put-lock-api-client
        """
        logger.debug("LockAPIClient")
        client_id = params.client_id if params.client_id else "self"
        path = (
            f"/identity-management/v3/api-clients/{client_id}/lock"
        )
        self._session.exec(
            "PUT", path,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrLockAPIClient,
            ),
        )

    def unlock_api_client(
        self, params: models.UnlockAPIClientRequest,
    ) -> None:
        """Unlock an API client.

        See: https://techdocs.akamai.com/iam-api/reference/put-unlock-api-client
        """
        logger.debug("UnlockAPIClient")
        err = iam_validation.validate_unlock_api_client_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrUnlockAPIClient}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = (
            f"/identity-management/v3/api-clients/{params.client_id}/unlock"
        )
        self._session.exec(
            "PUT", path,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrUnlockAPIClient,
            ),
        )

    def list_api_clients(
        self, params: models.ListAPIClientsRequest,
    ) -> list[models.ListAPIClientsItem]:
        """List API clients the administrator can manage.

        See: https://techdocs.akamai.com/iam-api/reference/get-api-clients
        """
        logger.debug("ListAPIClients")
        path = "/identity-management/v3/api-clients"
        query_params: dict[str, str] = {
            "actions": str(params.actions).lower(),
        }
        _, result = self._session.exec(
            "GET", path, expect_json=True, params=query_params,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrListAPIClients,
            ),
        )
        return [models.ListAPIClientsItem.from_dict(item) for item in result]

    def get_api_client(
        self, params: models.GetAPIClientRequest,
    ) -> models.GetAPIClientResponse:
        """Get details for a single API client.

        If *client_id* is empty the caller's own client is returned.

        See: https://techdocs.akamai.com/iam-api/reference/get-api-client
        """
        logger.debug("GetAPIClient")
        client_id = params.client_id if params.client_id else "self"
        path = f"/identity-management/v3/api-clients/{client_id}"
        query_params: dict[str, str] = {
            "actions": str(params.actions).lower(),
            "groupAccess": str(params.group_access).lower(),
            "apiAccess": str(params.api_access).lower(),
            "credentials": str(params.credentials).lower(),
            "ipAcl": str(params.ip_acl).lower(),
        }
        _, result = self._session.exec(
            "GET", path, expect_json=True, params=query_params,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrGetAPIClient,
            ),
        )
        return models.GetAPIClientResponse.from_dict(result)

    def create_api_client(
        self, params: models.CreateAPIClientRequest,
    ) -> models.CreateAPIClientResponse:
        """Create a new API client.

        See: https://techdocs.akamai.com/iam-api/reference/post-api-clients
        """
        logger.debug("CreateAPIClient")
        err = iam_validation.validate_create_api_client_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrCreateAPIClient}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = "/identity-management/v3/api-clients"
        _, result = self._session.exec(
            "POST", path, body=params.to_dict(), expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrCreateAPIClient,
            ),
        )
        return models.CreateAPIClientResponse.from_dict(result)

    def update_api_client(
        self, params: models.UpdateAPIClientRequest,
    ) -> models.CreateAPIClientResponse:
        """Update an API client.

        If *client_id* is empty the caller's own client is updated.

        See: https://techdocs.akamai.com/iam-api/reference/put-api-client
        """
        logger.debug("UpdateAPIClient")
        err = iam_validation.validate_update_api_client_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrUpdateAPIClient}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        client_id = params.client_id if params.client_id else "self"
        path = f"/identity-management/v3/api-clients/{client_id}"
        body = params.body.to_dict() if params.body else {}
        _, result = self._session.exec(
            "PUT", path, body=body, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrUpdateAPIClient,
            ),
        )
        return models.CreateAPIClientResponse.from_dict(result)

    def delete_api_client(
        self, params: models.DeleteAPIClientRequest,
    ) -> None:
        """Permanently delete an API client.

        If *client_id* is empty the caller's own client is deleted.

        See: https://techdocs.akamai.com/iam-api/reference/delete-api-client
        """
        logger.debug("DeleteAPIClient")
        client_id = params.client_id if params.client_id else "self"
        path = f"/identity-management/v3/api-clients/{client_id}"
        self._session.exec(
            "DELETE", path,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrDeleteAPIClient,
            ),
        )

    # =================================================================
    # Credential methods (api_clients_credentials.go)
    # =================================================================

    def create_credential(
        self, params: models.CreateCredentialRequest,
    ) -> models.CreateCredentialResponse:
        """Create a new credential for an API client.

        If *client_id* is empty, operates on the caller's own client.

        See: https://techdocs.akamai.com/iam-api/reference/post-api-client-credentials
        """
        logger.debug("CreateCredential")
        client_id = params.client_id if params.client_id else "self"
        path = (
            f"/identity-management/v3/api-clients/{client_id}/credentials"
        )
        _, result = self._session.exec(
            "POST", path, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrCreateCredential,
            ),
        )
        return models.CreateCredentialResponse.from_dict(result)

    def list_credentials(
        self, params: models.ListCredentialsRequest,
    ) -> list[models.Credential]:
        """List credentials for an API client.

        If *client_id* is empty, operates on the caller's own client.

        See: https://techdocs.akamai.com/iam-api/reference/get-api-client-credentials
        """
        logger.debug("ListCredentials")
        client_id = params.client_id if params.client_id else "self"
        path = (
            f"/identity-management/v3/api-clients/{client_id}/credentials"
        )
        query_params: dict[str, str] = {
            "actions": str(params.actions).lower(),
        }
        _, result = self._session.exec(
            "GET", path, expect_json=True, params=query_params,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrListCredentials,
            ),
        )
        return [models.Credential.from_dict(item) for item in result]

    def get_credential(
        self, params: models.GetCredentialRequest,
    ) -> models.Credential:
        """Get a single credential for an API client.

        If *client_id* is empty, operates on the caller's own client.

        See: https://techdocs.akamai.com/iam-api/reference/get-api-client-credential
        """
        logger.debug("GetCredential")
        err = iam_validation.validate_get_credential_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrGetCredential}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        client_id = params.client_id if params.client_id else "self"
        path = (
            f"/identity-management/v3/api-clients/{client_id}"
            f"/credentials/{params.credential_id}"
        )
        query_params: dict[str, str] = {
            "actions": str(params.actions).lower(),
        }
        _, result = self._session.exec(
            "GET", path, expect_json=True, params=query_params,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrGetCredential,
            ),
        )
        return models.Credential.from_dict(result)

    def update_credential(
        self, params: models.UpdateCredentialRequest,
    ) -> models.UpdateCredentialResponse:
        """Update a credential for an API client.

        If *client_id* is empty, operates on the caller's own client.

        Implements the IDM-3347 nanosecond workaround: when ``ExpiresOn``
        has zero sub-second precision the API rejects the timestamp, so
        one microsecond is added automatically.

        See: https://techdocs.akamai.com/iam-api/reference/put-api-client-credential
        """
        logger.debug("UpdateCredential")
        err = iam_validation.validate_update_credential_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrUpdateCredential}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        client_id = params.client_id if params.client_id else "self"
        # IDM-3347 workaround — mirror Go: add time.Nanosecond when
        # ExpiresOn.Nanosecond() == 0 because the API rejects
        # timestamps without sub-second precision.
        if params.body and params.body.expires_on:
            raw = params.body.expires_on
            try:
                # Handle 'Z' suffix for fromisoformat in Python < 3.11
                dt_val = datetime.fromisoformat(
                    raw.replace("Z", "+00:00")
                )
                if dt_val.microsecond == 0:
                    dt_val = dt_val + timedelta(microseconds=1)
                    params.body.expires_on = (
                        dt_val.isoformat().replace("+00:00", "Z")
                    )
            except (ValueError, AttributeError):
                pass  # leave original value if parsing fails
        path = (
            f"/identity-management/v3/api-clients/{client_id}"
            f"/credentials/{params.credential_id}"
        )
        body = params.body.to_dict() if params.body else {}
        _, result = self._session.exec(
            "PUT", path, body=body, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrUpdateCredential,
            ),
        )
        return models.UpdateCredentialResponse.from_dict(result)

    def delete_credential(
        self, params: models.DeleteCredentialRequest,
    ) -> None:
        """Delete a credential for an API client.

        If *client_id* is empty, operates on the caller's own client.

        See: https://techdocs.akamai.com/iam-api/reference/delete-api-client-credential
        """
        logger.debug("DeleteCredential")
        err = iam_validation.validate_delete_credential_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrDeleteCredential}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        client_id = params.client_id if params.client_id else "self"
        path = (
            f"/identity-management/v3/api-clients/{client_id}"
            f"/credentials/{params.credential_id}"
        )
        self._session.exec(
            "DELETE", path,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrDeleteCredential,
            ),
        )

    def deactivate_credential(
        self, params: models.DeactivateCredentialRequest,
    ) -> None:
        """Deactivate a single credential for an API client.

        If *client_id* is empty, operates on the caller's own client.

        See: https://techdocs.akamai.com/iam-api/reference/post-api-client-credential-deactivate
        """
        logger.debug("DeactivateCredential")
        err = iam_validation.validate_deactivate_credential_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrDeactivateCredential}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        client_id = params.client_id if params.client_id else "self"
        path = (
            f"/identity-management/v3/api-clients/{client_id}"
            f"/credentials/{params.credential_id}/deactivate"
        )
        self._session.exec(
            "POST", path,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrDeactivateCredential,
            ),
        )

    def deactivate_credentials(
        self, params: models.DeactivateCredentialsRequest,
    ) -> None:
        """Deactivate all credentials for an API client.

        If *client_id* is empty, operates on the caller's own client.

        See: https://techdocs.akamai.com/iam-api/reference/post-api-client-credentials-deactivate
        """
        logger.debug("DeactivateCredentials")
        client_id = params.client_id if params.client_id else "self"
        path = (
            f"/identity-management/v3/api-clients/{client_id}"
            "/credentials/deactivate"
        )
        self._session.exec(
            "POST", path,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrDeactivateCredentials,
            ),
        )

    # =================================================================
    # Blocked Properties methods (blocked_properties.go)
    # =================================================================

    def list_blocked_properties(
        self, params: models.ListBlockedPropertiesRequest,
    ) -> list[int]:
        """List blocked property IDs for a user within a group.

        See: https://techdocs.akamai.com/iam-api/reference/get-blocked-properties
        """
        logger.debug("ListBlockedProperties")
        err = iam_validation.validate_list_blocked_properties_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrListBlockedProperties}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = (
            "/identity-management/v3/user-admin/ui-identities"
            f"/{params.identity_id}/groups/{params.group_id}"
            "/blocked-properties"
        )
        _, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrListBlockedProperties,
            ),
        )
        return list(result) if result else []

    def update_blocked_properties(
        self, params: models.UpdateBlockedPropertiesRequest,
    ) -> list[int]:
        """Update blocked property IDs for a user within a group.

        See: https://techdocs.akamai.com/iam-api/reference/put-blocked-properties
        """
        logger.debug("UpdateBlockedProperties")
        err = iam_validation.validate_update_blocked_properties_request(
            params,
        )
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrUpdateBlockedProperties}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = (
            "/identity-management/v3/user-admin/ui-identities"
            f"/{params.identity_id}/groups/{params.group_id}"
            "/blocked-properties"
        )
        _, result = self._session.exec(
            "PUT", path, body=params.body, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrUpdateBlockedProperties,
            ),
        )
        return list(result) if result else []

    # =================================================================
    # CIDR Block methods (cidr.go)
    # =================================================================

    def list_cidr_blocks(
        self, params: models.ListCIDRBlocksRequest,
    ) -> list[models.CIDRBlock]:
        """List CIDR blocks on the account allowlist.

        See: https://techdocs.akamai.com/iam-api/reference/get-allowlist
        """
        logger.debug("ListCIDRBlocks")
        path = "/identity-management/v3/user-admin/ip-acl/allowlist"
        query_params: dict[str, str] = {
            "actions": str(params.actions).lower(),
        }
        _, result = self._session.exec(
            "GET", path, expect_json=True, params=query_params,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrListCIDRBlocks,
            ),
        )
        return [models.CIDRBlock.from_dict(item) for item in result]

    def create_cidr_block(
        self, params: models.CreateCIDRBlockRequest,
    ) -> list[models.CIDRBlock]:
        """Add a CIDR block to the account allowlist.

        See: https://techdocs.akamai.com/iam-api/reference/post-allowlist
        """
        logger.debug("CreateCIDRBlock")
        err = iam_validation.validate_create_cidr_block_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrCreateCIDRBlock}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = "/identity-management/v3/user-admin/ip-acl/allowlist"
        body = params.body.to_dict() if params.body else {}
        _, result = self._session.exec(
            "POST", path, body=body, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrCreateCIDRBlock,
            ),
        )
        return [models.CIDRBlock.from_dict(item) for item in result]

    def get_cidr_block(
        self, params: models.GetCIDRBlockRequest,
    ) -> models.CIDRBlock:
        """Get a single CIDR block from the account allowlist.

        See: https://techdocs.akamai.com/iam-api/reference/get-allowlist-cidrblock
        """
        logger.debug("GetCIDRBlock")
        err = iam_validation.validate_get_cidr_block_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrGetCIDRBlock}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = (
            "/identity-management/v3/user-admin/ip-acl/allowlist"
            f"/{params.cidr_block_id}"
        )
        query_params: dict[str, str] = {
            "actions": str(params.actions).lower(),
        }
        _, result = self._session.exec(
            "GET", path, expect_json=True, params=query_params,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrGetCIDRBlock,
            ),
        )
        return models.CIDRBlock.from_dict(result)

    def update_cidr_block(
        self, params: models.UpdateCIDRBlockRequest,
    ) -> models.CIDRBlock:
        """Update a CIDR block on the account allowlist.

        See: https://techdocs.akamai.com/iam-api/reference/put-allowlist-cidrblock
        """
        logger.debug("UpdateCIDRBlock")
        err = iam_validation.validate_update_cidr_block_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrUpdateCIDRBlock}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = (
            "/identity-management/v3/user-admin/ip-acl/allowlist"
            f"/{params.cidr_block_id}"
        )
        body = params.body.to_dict() if params.body else {}
        _, result = self._session.exec(
            "PUT", path, body=body, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrUpdateCIDRBlock,
            ),
        )
        return models.CIDRBlock.from_dict(result)

    def delete_cidr_block(
        self, params: models.DeleteCIDRBlockRequest,
    ) -> None:
        """Delete a CIDR block from the account allowlist.

        See: https://techdocs.akamai.com/iam-api/reference/delete-allowlist-cidrblock
        """
        logger.debug("DeleteCIDRBlock")
        err = iam_validation.validate_delete_cidr_block_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrDeleteCIDRBlock}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = (
            "/identity-management/v3/user-admin/ip-acl/allowlist"
            f"/{params.cidr_block_id}"
        )
        self._session.exec(
            "DELETE", path,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrDeleteCIDRBlock,
            ),
        )

    def validate_cidr_block(
        self, params: models.ValidateCIDRBlockRequest,
    ) -> None:
        """Validate a CIDR block.

        See: https://techdocs.akamai.com/iam-api/reference/get-validate-allowlist
        """
        logger.debug("ValidateCIDRBlock")
        err = iam_validation.validate_validate_cidr_block_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrValidateCIDRBlock}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = (
            "/identity-management/v3/user-admin/ip-acl/allowlist/validate"
        )
        query_params: dict[str, str] = {
            "cidrblock": params.cidr_block,
        }
        self._session.exec(
            "GET", path, params=query_params,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrValidateCIDRBlock,
            ),
        )

    # =================================================================
    # Group methods (groups.go)
    # =================================================================

    def create_group(
        self, params: models.GroupRequest,
    ) -> models.Group:
        """Create a new group under a parent group.

        See: https://techdocs.akamai.com/iam-api/reference/post-groups
        """
        logger.debug("CreateGroup")
        err = iam_validation.validate_group_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrCreateGroup}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = (
            f"/identity-management/v3/user-admin/groups/{params.group_id}"
        )
        body = params.to_dict()
        _, result = self._session.exec(
            "POST", path, body=body, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrCreateGroup,
            ),
        )
        return models.Group.from_dict(result)

    def get_group(
        self, params: models.GetGroupRequest,
    ) -> models.Group:
        """Get details for a single group.

        See: https://techdocs.akamai.com/iam-api/reference/get-group
        """
        logger.debug("GetGroup")
        err = iam_validation.validate_get_group_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrGetGroup}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = (
            f"/identity-management/v3/user-admin/groups/{params.group_id}"
        )
        query_params: dict[str, str] = {
            "actions": str(params.actions).lower(),
        }
        _, result = self._session.exec(
            "GET", path, expect_json=True, params=query_params,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrGetGroup,
            ),
        )
        return models.Group.from_dict(result)

    def list_affected_users(
        self, params: models.ListAffectedUsersRequest,
    ) -> list[models.GroupUser]:
        """List users affected by moving a group.

        See: https://techdocs.akamai.com/iam-api/reference/get-move-affected-users
        """
        logger.debug("ListAffectedUsers")
        err = iam_validation.validate_list_affected_users_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrListAffectedUsers}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = (
            "/identity-management/v3/user-admin/groups/move"
            f"/{params.source_group_id}/{params.destination_group_id}"
            "/affected-users"
        )
        query_params: dict[str, str] = {}
        if params.user_type:
            query_params["userType"] = params.user_type
        _, result = self._session.exec(
            "GET", path, expect_json=True, params=query_params,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrListAffectedUsers,
            ),
        )
        return [models.GroupUser.from_dict(item) for item in result]

    def list_groups(
        self, params: models.ListGroupsRequest,
    ) -> list[models.Group]:
        """List all groups the administrator can manage.

        See: https://techdocs.akamai.com/iam-api/reference/get-groups
        """
        logger.debug("ListGroups")
        path = "/identity-management/v3/user-admin/groups"
        query_params: dict[str, str] = {
            "actions": str(params.actions).lower(),
        }
        _, result = self._session.exec(
            "GET", path, expect_json=True, params=query_params,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrListGroups,
            ),
        )
        return [models.Group.from_dict(item) for item in result]

    def remove_group(
        self, params: models.RemoveGroupRequest,
    ) -> None:
        """Remove a group.

        See: https://techdocs.akamai.com/iam-api/reference/delete-group
        """
        logger.debug("RemoveGroup")
        err = iam_validation.validate_remove_group_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrRemoveGroup}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = (
            f"/identity-management/v3/user-admin/groups/{params.group_id}"
        )
        self._session.exec(
            "DELETE", path,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrRemoveGroup,
            ),
        )

    def update_group_name(
        self, params: models.GroupRequest,
    ) -> models.Group:
        """Update a group name.

        See: https://techdocs.akamai.com/iam-api/reference/put-group
        """
        logger.debug("UpdateGroupName")
        err = iam_validation.validate_group_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrUpdateGroupName}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = (
            f"/identity-management/v3/user-admin/groups/{params.group_id}"
        )
        body = params.to_dict()
        _, result = self._session.exec(
            "PUT", path, body=body, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrUpdateGroupName,
            ),
        )
        return models.Group.from_dict(result)

    def move_group(
        self, params: models.MoveGroupRequest,
    ) -> None:
        """Move a group under a new parent group.

        See: https://techdocs.akamai.com/iam-api/reference/post-groups-move
        """
        logger.debug("MoveGroup")
        err = iam_validation.validate_move_group_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrMoveGroup}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = "/identity-management/v3/user-admin/groups/move"
        body = params.to_dict()
        self._session.exec(
            "POST", path, body=body,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrMoveGroup,
            ),
        )

    # =================================================================
    # Helper methods (helper.go)
    # =================================================================

    def list_allowed_cp_codes(
        self, params: models.ListAllowedCPCodesRequest,
    ) -> list[models.ListAllowedCPCodesResponseItem]:
        """List allowed CP codes for a user.

        See: https://techdocs.akamai.com/iam-api/reference/post-allowed-cpcodes
        """
        logger.debug("ListAllowedCPCodes")
        err = iam_validation.validate_list_allowed_cp_codes_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrListAllowedCPCodes}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = (
            "/identity-management/v3/users"
            f"/{params.user_name}/allowed-cpcodes"
        )
        body = params.body.to_dict() if params.body else {}
        _, result = self._session.exec(
            "POST", path, body=body, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrListAllowedCPCodes,
            ),
        )
        return [
            models.ListAllowedCPCodesResponseItem.from_dict(item)
            for item in result
        ]

    def list_authorized_users(self) -> list[models.AuthorizedUser]:
        """List authorized users for creating API clients.

        See: https://techdocs.akamai.com/iam-api/reference/get-authorized-users
        """
        logger.debug("ListAuthorizedUsers")
        path = "/identity-management/v3/users"
        _, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrListAuthorizedUsers,
            ),
        )
        return [models.AuthorizedUser.from_dict(item) for item in result]

    def list_allowed_apis(
        self, params: models.ListAllowedAPIsRequest,
    ) -> list[models.AllowedAPI]:
        """List allowed APIs for a user.

        See: https://techdocs.akamai.com/iam-api/reference/get-allowed-apis
        """
        logger.debug("ListAllowedAPIs")
        err = iam_validation.validate_list_allowed_apis_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrListAllowedAPIs}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = (
            "/identity-management/v3/users"
            f"/{params.user_name}/allowed-apis"
        )
        query_params: dict[str, str] = {}
        if params.client_type:
            query_params["clientType"] = params.client_type
        if params.allow_account_switch is not None:
            query_params["allowAccountSwitch"] = str(
                params.allow_account_switch
            ).lower()
        _, result = self._session.exec(
            "GET", path, expect_json=True, params=query_params,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrListAllowedAPIs,
            ),
        )
        return [models.AllowedAPI.from_dict(item) for item in result]

    def list_accessible_groups(
        self, params: models.ListAccessibleGroupsRequest,
    ) -> list[models.AccessibleGroup]:
        """List groups accessible to a user for API client creation.

        See: https://techdocs.akamai.com/iam-api/reference/get-accessible-groups
        """
        logger.debug("ListAccessibleGroups")
        err = iam_validation.validate_list_accessible_groups_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrAccessibleGroups}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = (
            "/identity-management/v3/users"
            f"/{params.user_name}/group-access"
        )
        _, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrAccessibleGroups,
            ),
        )
        return [models.AccessibleGroup.from_dict(item) for item in result]

    # =================================================================
    # IP Allowlist methods (ip_allowlist.go)
    # =================================================================

    def disable_ip_allowlist(self) -> None:
        """Disable the IP allowlist on the account.

        See: https://techdocs.akamai.com/iam-api/reference/post-allowlist-disable
        """
        logger.debug("DisableIPAllowlist")
        path = (
            "/identity-management/v3/user-admin/ip-acl/allowlist/disable"
        )
        self._session.exec(
            "POST", path,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrDisableIPAllowlist,
            ),
        )

    def enable_ip_allowlist(self) -> None:
        """Enable the IP allowlist on the account.

        See: https://techdocs.akamai.com/iam-api/reference/post-allowlist-enable
        """
        logger.debug("EnableIPAllowlist")
        path = (
            "/identity-management/v3/user-admin/ip-acl/allowlist/enable"
        )
        self._session.exec(
            "POST", path,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrEnableIPAllowlist,
            ),
        )

    def get_ip_allowlist_status(
        self,
    ) -> models.GetIPAllowlistStatusResponse:
        """Get the IP allowlist status for the account.

        See: https://techdocs.akamai.com/iam-api/reference/get-allowlist-status
        """
        logger.debug("GetIPAllowlistStatus")
        path = (
            "/identity-management/v3/user-admin/ip-acl/allowlist/status"
        )
        _, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrGetIPAllowlistStatus,
            ),
        )
        return models.GetIPAllowlistStatusResponse.from_dict(result)

    # =================================================================
    # Properties methods (properties.go)
    # =================================================================

    def list_properties(
        self, params: models.ListPropertiesRequest,
    ) -> list[models.Property]:
        """List properties a user has access to in a group.

        See: https://techdocs.akamai.com/iam-api/reference/get-properties
        """
        logger.debug("ListProperties")
        path = "/identity-management/v3/user-admin/properties"
        query_params: dict[str, str] = {
            "actions": str(params.actions).lower(),
        }
        if params.group_id != 0:
            query_params["groupId"] = str(params.group_id)
        _, result = self._session.exec(
            "GET", path, expect_json=True, params=query_params,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrListProperties,
            ),
        )
        return [models.Property.from_dict(item) for item in result]

    def list_users_for_property(
        self, params: models.ListUsersForPropertyRequest,
    ) -> list[models.UsersForProperty]:
        """List users who have access to a property.

        See: https://techdocs.akamai.com/iam-api/reference/get-property-users
        """
        logger.debug("ListUsersForProperty")
        err = iam_validation.validate_list_users_for_property_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrListUsersForProperty}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = (
            "/identity-management/v3/user-admin/properties"
            f"/{params.property_id}/users"
        )
        query_params: dict[str, str] = {}
        if params.user_type:
            query_params["userType"] = params.user_type
        _, result = self._session.exec(
            "GET", path, expect_json=True, params=query_params,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrListUsersForProperty,
            ),
        )
        return [models.UsersForProperty.from_dict(item) for item in result]

    def get_property(
        self, params: models.GetPropertyRequest,
    ) -> models.GetPropertyResponse:
        """Get details for a single property.

        See: https://techdocs.akamai.com/iam-api/reference/get-property
        """
        logger.debug("GetProperty")
        err = iam_validation.validate_get_property_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrGetProperty}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = (
            "/identity-management/v3/user-admin/properties"
            f"/{params.property_id}"
        )
        query_params: dict[str, str] = {
            "groupId": str(params.group_id),
        }
        _, result = self._session.exec(
            "GET", path, expect_json=True, params=query_params,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrGetProperty,
            ),
        )
        return models.GetPropertyResponse.from_dict(result)

    def move_property(
        self, params: models.MovePropertyRequest,
    ) -> None:
        """Move a property from one group to another.

        See: https://techdocs.akamai.com/iam-api/reference/put-property
        """
        logger.debug("MoveProperty")
        err = iam_validation.validate_move_property_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrMoveProperty}: "
                f"{iam_errors.ErrStructValidation}: {err}"
            )
        path = (
            "/identity-management/v3/user-admin/properties"
            f"/{params.property_id}"
        )
        body = params.body.to_dict() if params.body else {}
        self._session.exec(
            "PUT", path, body=body,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrMoveProperty,
            ),
        )

    def map_property_id_to_name(
        self, params: models.MapPropertyIDToNameRequest,
    ) -> str:
        """Map a property ID to its name.

        Delegates to GetProperty and returns the property name.

        See: https://techdocs.akamai.com/iam-api/reference/get-property
        """
        logger.debug("MapPropertyIDToName")
        err = iam_validation.validate_map_property_id_to_name_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrMapPropertyIDToName}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        get_req = models.GetPropertyRequest(
            property_id=params.property_id,
            group_id=params.group_id,
        )
        try:
            prop = self.get_property(get_req)
        except Exception as exc:
            raise ValueError(
                f"{iam_errors.ErrMapPropertyIDToName}: "
                f"request failed: {exc}"
            ) from exc
        return prop.property_name

    def block_users(
        self, params: models.BlockUsersRequest,
    ) -> list[models.UsersForProperty]:
        """Block or unblock users on a property.

        See: https://techdocs.akamai.com/iam-api/reference/put-property-users-block
        """
        logger.debug("BlockUsers")
        err = iam_validation.validate_block_users_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrBlockUsers}: "
                f"{iam_errors.ErrStructValidation}: {err}"
            )
        path = (
            "/identity-management/v3/user-admin/properties"
            f"/{params.property_id}/users/block"
        )
        body = [item.to_dict() for item in params.body]
        _, result = self._session.exec(
            "PUT", path, body=body, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrBlockUsers,
            ),
        )
        return [models.UsersForProperty.from_dict(item) for item in result]

    # =================================================================
    # Role methods (roles.go)
    # =================================================================

    def create_role(
        self, params: models.RoleRequest,
    ) -> models.Role:
        """Create a new custom role.

        See: https://techdocs.akamai.com/iam-api/reference/post-roles
        """
        logger.debug("CreateRole")
        err = iam_validation.validate_create_role_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrCreateRole}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = "/identity-management/v3/user-admin/roles"
        body = params.to_dict()
        _, result = self._session.exec(
            "POST", path, body=body, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrCreateRole,
            ),
        )
        return models.Role.from_dict(result)

    def get_role(
        self, params: models.GetRoleRequest,
    ) -> models.Role:
        """Get details for a single role.

        See: https://techdocs.akamai.com/iam-api/reference/get-role
        """
        logger.debug("GetRole")
        err = iam_validation.validate_get_role_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrGetRole}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = (
            f"/identity-management/v3/user-admin/roles/{params.id}"
        )
        query_params: dict[str, str] = {
            "actions": str(params.actions).lower(),
            "grantedRoles": str(params.granted_roles).lower(),
            "users": str(params.users).lower(),
        }
        _, result = self._session.exec(
            "GET", path, expect_json=True, params=query_params,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrGetRole,
            ),
        )
        return models.Role.from_dict(result)

    def update_role(
        self, params: models.UpdateRoleRequest,
    ) -> models.Role:
        """Update an existing role.

        See: https://techdocs.akamai.com/iam-api/reference/put-role
        """
        logger.debug("UpdateRole")
        err = iam_validation.validate_update_role_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrUpdateRole}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = (
            f"/identity-management/v3/user-admin/roles/{params.id}"
        )
        body: dict = {
            "roleName": params.name,
            "roleDescription": params.description,
        }
        if params.granted_roles is not None:
            body["grantedRoles"] = [
                r.to_dict() for r in params.granted_roles
            ]
        _, result = self._session.exec(
            "PUT", path, body=body, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrUpdateRole,
            ),
        )
        return models.Role.from_dict(result)

    def delete_role(
        self, params: models.DeleteRoleRequest,
    ) -> None:
        """Delete a custom role.

        See: https://techdocs.akamai.com/iam-api/reference/delete-role
        """
        logger.debug("DeleteRole")
        err = iam_validation.validate_delete_role_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrDeleteRole}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = (
            f"/identity-management/v3/user-admin/roles/{params.id}"
        )
        self._session.exec(
            "DELETE", path,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrDeleteRole,
            ),
        )

    def list_roles(
        self, params: models.ListRolesRequest,
    ) -> list[models.Role]:
        """List all roles available in the account.

        See: https://techdocs.akamai.com/iam-api/reference/get-roles
        """
        logger.debug("ListRoles")
        path = "/identity-management/v3/user-admin/roles"
        query_params: dict[str, str] = {
            "actions": str(params.actions).lower(),
            "ignoreContext": str(params.ignore_context).lower(),
            "users": str(params.users).lower(),
        }
        if params.group_id is not None:
            query_params["groupId"] = str(params.group_id)
        _, result = self._session.exec(
            "GET", path, expect_json=True, params=query_params,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrListRoles,
            ),
        )
        return [models.Role.from_dict(item) for item in result]

    def list_grantable_roles(self) -> list[models.RoleGrantedRole]:
        """List all grantable roles.

        See: https://techdocs.akamai.com/iam-api/reference/get-grantable-roles
        """
        logger.debug("ListGrantableRoles")
        path = (
            "/identity-management/v3/user-admin/roles/grantable-roles"
        )
        _, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrListGrantableRoles,
            ),
        )
        return [models.RoleGrantedRole.from_dict(item) for item in result]

    # =================================================================
    # Support methods (support.go)
    # =================================================================

    def get_password_policy(
        self,
    ) -> models.GetPasswordPolicyResponse:
        """Get the account password policy.

        See: https://techdocs.akamai.com/iam-api/reference/get-password-policy
        """
        logger.debug("GetPasswordPolicy")
        path = (
            "/identity-management/v3/user-admin/common/password-policy"
        )
        _, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrGetPasswordPolicy,
            ),
        )
        return models.GetPasswordPolicyResponse.from_dict(result)

    def list_products(self) -> list[str]:
        """List notification products.

        See: https://techdocs.akamai.com/iam-api/reference/get-notification-products
        """
        logger.debug("ListProducts")
        path = (
            "/identity-management/v3/user-admin/common"
            "/notification-products"
        )
        _, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrListProducts,
            ),
        )
        return list(result) if result else []

    def list_states(
        self, params: models.ListStatesRequest,
    ) -> list[str]:
        """List states for a given country.

        See: https://techdocs.akamai.com/iam-api/reference/get-states
        """
        logger.debug("ListStates")
        err = iam_validation.validate_list_states_request(params)
        if err is not None:
            raise ValueError(
                f"{iam_errors.ErrListStates}: "
                f"{iam_errors.ErrStructValidation}:\n{err}"
            )
        path = (
            "/identity-management/v3/user-admin/common/countries"
            f"/{params.country}/states"
        )
        _, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrListStates,
            ),
        )
        return list(result) if result else []

    def list_timeout_policies(self) -> list[models.TimeoutPolicy]:
        """List session timeout policies.

        See: https://techdocs.akamai.com/iam-api/reference/get-timeout-policies
        """
        logger.debug("ListTimeoutPolicies")
        path = (
            "/identity-management/v3/user-admin/common/timeout-policies"
        )
        _, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrListTimeoutPolicies,
            ),
        )
        return [models.TimeoutPolicy.from_dict(item) for item in result]

    def list_account_switch_keys(
        self, params: models.ListAccountSwitchKeysRequest,
    ) -> list[models.AccountSwitchKey]:
        """List account switch keys.

        See: https://techdocs.akamai.com/iam-api/reference/get-account-switch-keys
        """
        logger.debug("ListAccountSwitchKeys")
        client_id = params.client_id if params.client_id else "self"
        path = (
            "/identity-management/v3/api-clients"
            f"/{client_id}/account-switch-keys"
        )
        query_params: dict[str, str] = {}
        if params.search:
            query_params["search"] = params.search
        _, result = self._session.exec(
            "GET", path, expect_json=True, params=query_params,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrListAccountSwitchKeys,
            ),
        )
        return [models.AccountSwitchKey.from_dict(item) for item in result]

    def supported_contact_types(self) -> list[str]:
        """List supported contact types.

        See: https://techdocs.akamai.com/iam-api/reference/get-contact-types
        """
        logger.debug("SupportedContactTypes")
        path = (
            "/identity-management/v3/user-admin/common/contact-types"
        )
        _, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrSupportedContactTypes,
            ),
        )
        return list(result) if result else []

    def supported_countries(self) -> list[str]:
        """List supported countries.

        See: https://techdocs.akamai.com/iam-api/reference/get-countries
        """
        logger.debug("SupportedCountries")
        path = (
            "/identity-management/v3/user-admin/common/countries"
        )
        _, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrSupportedCountries,
            ),
        )
        return list(result) if result else []

    def supported_languages(self) -> list[str]:
        """List supported languages.

        See: https://techdocs.akamai.com/iam-api/reference/get-supported-languages
        """
        logger.debug("SupportedLanguages")
        path = (
            "/identity-management/v3/user-admin/common"
            "/supported-languages"
        )
        _, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrSupportedLanguages,
            ),
        )
        return list(result) if result else []

    def supported_timezones(self) -> list[models.Timezone]:
        """List supported timezones.

        See: https://techdocs.akamai.com/iam-api/reference/get-timezones
        """
        logger.debug("SupportedTimezones")
        path = (
            "/identity-management/v3/user-admin/common/timezones"
        )
        _, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrSupportedTimezones,
            ),
        )
        return [models.Timezone.from_dict(item) for item in result]

    # ------------------------------------------------------------------ #
    # Users (user.go)                                                     #
    # ------------------------------------------------------------------ #

    def create_user(
        self, params: models.CreateUserRequest,
    ) -> models.User:
        """Create a user in the account specified in your own API client
        credentials or in a managed account.

        See: https://techdocs.akamai.com/iam-api/reference/post-ui-identity
        """
        logger.debug("CreateUser")

        err = iam_validation.validate_create_user_request(params)
        if err is not None:
            raise err

        path = "/identity-management/v3/user-admin/ui-identities"
        query_params = {
            "sendEmail": str(params.send_email).lower(),
        }

        response, result = self._session.exec(
            "POST", path, body=params.to_dict(),
            expect_json=True, params=query_params,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrCreateUser,
            ),
        )

        if response.status_code != 201:
            raise iam_errors.create_error_from_response(
                response, iam_errors.ErrCreateUser,
            )

        return models.User.from_dict(result)

    def get_user(
        self, params: models.GetUserRequest,
    ) -> models.User:
        """Return a user's profile.

        See: https://techdocs.akamai.com/iam-api/reference/get-ui-identity
        """
        logger.debug("GetUser")

        err = iam_validation.validate_get_user_request(params)
        if err is not None:
            raise err

        path = (
            "/identity-management/v3/user-admin/ui-identities/"
            f"{params.identity_id}"
        )
        query_params = {
            "actions": str(params.actions).lower(),
            "authGrants": str(params.auth_grants).lower(),
            "notifications": str(params.notifications).lower(),
        }

        response, result = self._session.exec(
            "GET", path, expect_json=True, params=query_params,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrGetUser,
            ),
        )

        if response.status_code != 200:
            raise iam_errors.create_error_from_response(
                response, iam_errors.ErrGetUser,
            )

        return models.User.from_dict(result)

    def list_users(
        self, params: models.ListUsersRequest,
    ) -> list[models.UserListItem]:
        """Return a list of users who can access an account.

        See: https://techdocs.akamai.com/iam-api/reference/get-ui-identities
        """
        logger.debug("ListUsers")

        path = "/identity-management/v3/user-admin/ui-identities"
        query_params: dict[str, str] = {
            "actions": str(params.actions).lower(),
            "authGrants": str(params.auth_grants).lower(),
        }
        if params.group_id is not None:
            query_params["groupId"] = str(params.group_id)

        response, result = self._session.exec(
            "GET", path, expect_json=True, params=query_params,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrListUsers,
            ),
        )

        if response.status_code != 200:
            raise iam_errors.create_error_from_response(
                response, iam_errors.ErrListUsers,
            )

        return [models.UserListItem.from_dict(item) for item in result]

    def remove_user(
        self, params: models.RemoveUserRequest,
    ) -> None:
        """Remove a user identity from an account.

        See: https://techdocs.akamai.com/iam-api/reference/delete-ui-identity
        """
        logger.debug("RemoveUser")

        err = iam_validation.validate_remove_user_request(params)
        if err is not None:
            raise err

        path = (
            "/identity-management/v3/user-admin/ui-identities/"
            f"{params.identity_id}"
        )

        response, _ = self._session.exec(
            "DELETE", path,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrRemoveUser,
            ),
        )

        if response.status_code not in (200, 204):
            raise iam_errors.create_error_from_response(
                response, iam_errors.ErrRemoveUser,
            )

    def update_user_auth_grants(
        self, params: models.UpdateUserAuthGrantsRequest,
    ) -> list[models.AuthGrant]:
        """Update a user's auth grants on a per-group basis.

        See: https://techdocs.akamai.com/iam-api/reference/put-ui-identity-auth-grants
        """
        logger.debug("UpdateUserAuthGrants")

        err = iam_validation.validate_update_user_auth_grants_request(params)
        if err is not None:
            raise err

        path = (
            "/identity-management/v3/user-admin/ui-identities/"
            f"{params.identity_id}/auth-grants"
        )
        body = [g.to_dict() for g in params.auth_grants]

        response, result = self._session.exec(
            "PUT", path, body=body, expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrUpdateUserAuthGrants,
            ),
        )

        if response.status_code != 200:
            raise iam_errors.create_error_from_response(
                response, iam_errors.ErrUpdateUserAuthGrants,
            )

        return [models.AuthGrant.from_dict(item) for item in result]

    def update_user_info(
        self, params: models.UpdateUserInfoRequest,
    ) -> models.UserBasicInfo:
        """Update a user's basic information.

        See: https://techdocs.akamai.com/iam-api/reference/put-ui-identity-basic-info
        """
        logger.debug("UpdateUserInfo")

        err = iam_validation.validate_update_user_info_request(params)
        if err is not None:
            raise err

        path = (
            "/identity-management/v3/user-admin/ui-identities/"
            f"{params.identity_id}/basic-info"
        )

        response, result = self._session.exec(
            "PUT", path, body=params.user.to_dict(), expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrUpdateUserInfo,
            ),
        )

        if response.status_code != 200:
            raise iam_errors.create_error_from_response(
                response, iam_errors.ErrUpdateUserInfo,
            )

        return models.UserBasicInfo.from_dict(result)

    def update_user_notifications(
        self, params: models.UpdateUserNotificationsRequest,
    ) -> models.UserNotifications:
        """Update a user's notification settings.

        See: https://techdocs.akamai.com/iam-api/reference/put-ui-identity-notifications
        """
        logger.debug("UpdateUserNotifications")

        err = iam_validation.validate_update_user_notifications_request(params)
        if err is not None:
            raise err

        path = (
            "/identity-management/v3/user-admin/ui-identities/"
            f"{params.identity_id}/notifications"
        )

        response, result = self._session.exec(
            "PUT", path, body=params.notifications.to_dict(),
            expect_json=True,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrUpdateUserNotifications,
            ),
        )

        if response.status_code != 200:
            raise iam_errors.create_error_from_response(
                response, iam_errors.ErrUpdateUserNotifications,
            )

        return models.UserNotifications.from_dict(result)

    def update_mfa(
        self, params: models.UpdateMFARequest,
    ) -> None:
        """Update multi-factor authentication for a user.

        See: https://techdocs.akamai.com/iam-api/reference/put-ui-identity-additional-authentication
        """
        logger.debug("UpdateMFA")

        err = iam_validation.validate_update_mfa_request(params)
        if err is not None:
            raise err

        path = (
            "/identity-management/v3/user-admin/ui-identities/"
            f"{params.identity_id}/additionalAuthentication"
        )

        # Go JSON-encodes the MFAType string value (e.g. MFA → "MFA" with
        # quotes).  Python session sends str bodies as-is, so we need
        # json.dumps to add the JSON string quoting.
        response, _ = self._session.exec(
            "PUT", path, body=json.dumps(params.value),
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrUpdateMFA,
            ),
        )

        if response.status_code != 204:
            raise iam_errors.create_error_from_response(
                response, iam_errors.ErrUpdateMFA,
            )

    def reset_mfa(
        self, params: models.ResetMFARequest,
    ) -> None:
        """Reset multi-factor authentication for a user.

        See: https://techdocs.akamai.com/iam-api/reference/
        put-ui-identity-reset-additional-authentication
        """
        logger.debug("ResetMFA")

        # NOTE: Go source has NO Validate() call for ResetMFA — intentional.
        path = (
            "/identity-management/v3/user-admin/ui-identities/"
            f"{params.identity_id}/additionalAuthentication/reset"
        )

        response, _ = self._session.exec(
            "PUT", path,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrResetMFA,
            ),
        )

        if response.status_code != 204:
            raise iam_errors.create_error_from_response(
                response, iam_errors.ErrResetMFA,
            )

    # ------------------------------------------------------------------ #
    # User Lock (user_lock.go)                                            #
    # ------------------------------------------------------------------ #

    def lock_user(
        self, params: models.LockUserRequest,
    ) -> None:
        """Lock a user account.

        See: https://techdocs.akamai.com/iam-api/reference/post-ui-identity-lock
        """
        logger.debug("LockUser")

        err = iam_validation.validate_lock_user_request(params)
        if err is not None:
            raise err

        path = (
            "/identity-management/v3/user-admin/ui-identities/"
            f"{params.identity_id}/lock"
        )

        response, _ = self._session.exec(
            "POST", path,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrLockUser,
            ),
        )

        if response.status_code not in (200, 204):
            raise iam_errors.create_error_from_response(
                response, iam_errors.ErrLockUser,
            )

    def unlock_user(
        self, params: models.UnlockUserRequest,
    ) -> None:
        """Unlock a user account.

        See: https://techdocs.akamai.com/iam-api/reference/post-ui-identity-unlock
        """
        logger.debug("UnlockUser")

        err = iam_validation.validate_unlock_user_request(params)
        if err is not None:
            raise err

        path = (
            "/identity-management/v3/user-admin/ui-identities/"
            f"{params.identity_id}/unlock"
        )

        response, _ = self._session.exec(
            "POST", path,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrUnlockUser,
            ),
        )

        if response.status_code not in (200, 204):
            raise iam_errors.create_error_from_response(
                response, iam_errors.ErrUnlockUser,
            )

    # ------------------------------------------------------------------ #
    # User Password (user_password.go)                                    #
    # ------------------------------------------------------------------ #

    def reset_user_password(
        self, params: models.ResetUserPasswordRequest,
    ) -> models.ResetUserPasswordResponse | None:
        """Reset a user's password.

        When *send_email* is ``True`` the API sends the new password by
        e-mail and returns HTTP 204 (no body).  When ``False`` the API
        returns HTTP 200 with the new password in the response body.

        See: https://techdocs.akamai.com/iam-api/reference/post-ui-identity-reset-password
        """
        logger.debug("ResetUserPassword")

        err = iam_validation.validate_reset_user_password_request(params)
        if err is not None:
            raise err

        path = (
            "/identity-management/v3/user-admin/ui-identities/"
            f"{params.identity_id}/reset-password"
        )
        query_params = {
            "sendEmail": str(params.send_email).lower(),
        }

        response, result = self._session.exec(
            "POST", path, expect_json=True, params=query_params,
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrResetUserPassword,
            ),
        )

        # Complex status logic matching Go source:
        # SendEmail=true  → expect 204 (void, no body)
        # SendEmail=false → expect 200 (body with new password)
        if params.send_email:
            if response.status_code != 204:
                raise iam_errors.create_error_from_response(
                    response, iam_errors.ErrResetUserPassword,
                )
            return None

        if response.status_code != 200:
            raise iam_errors.create_error_from_response(
                response, iam_errors.ErrResetUserPassword,
            )
        return models.ResetUserPasswordResponse.from_dict(result)

    def set_user_password(
        self, params: models.SetUserPasswordRequest,
    ) -> None:
        """Set a user's password.

        See: https://techdocs.akamai.com/iam-api/reference/post-ui-identity-set-password
        """
        logger.debug("SetUserPassword")

        err = iam_validation.validate_set_user_password_request(params)
        if err is not None:
            raise err

        path = (
            "/identity-management/v3/user-admin/ui-identities/"
            f"{params.identity_id}/set-password"
        )

        response, _ = self._session.exec(
            "POST", path, body=params.to_dict(),
            error_parser=lambda resp: iam_errors.create_error_from_response(
                resp, iam_errors.ErrSetUserPassword,
            ),
        )

        if response.status_code != 204:
            raise iam_errors.create_error_from_response(
                response, iam_errors.ErrSetUserPassword,
            )
