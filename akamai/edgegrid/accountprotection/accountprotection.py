"""Account Protection API client for Akamai.

Provides access to the Akamai Application Security Account Protection APIs
for managing protected operations, general settings, user risk response
strategies, and user allow lists.

See: https://techdocs.akamai.com/account-protector/reference/api

Mirrors Go pkg/accountprotection (account_protection.go, protected_operation.go,
general_settings.go, user_risk_response_strategy.go, user_allow_list_id.go,
errors.go).
"""

import json
import logging

from typing import Any

from akamai.edgegrid.session import Session
from akamai.edgegrid.utils import unescape_content
from akamai.edgegrid.accountprotection import errors
from akamai.edgegrid.accountprotection import models
from akamai.edgegrid.accountprotection import validation

logger = logging.getLogger(__name__)


class AccountProtectionClient:
    """Account Protection API client.

    Provides methods for managing account protection features including
    protected operations, general settings, user risk response strategies,
    and user allow lists.

    Mirrors Go AccountProtection interface and accountProtection struct
    from pkg/accountprotection/account_protection.go.

    Usage::

        >>> from akamai.edgegrid.session import Session
        >>> session = Session(edgerc_path="~/.edgerc", section="default")
        >>> client = AccountProtectionClient(session)
        >>> result = client.list_protected_operations(request)
    """

    def __init__(self, session: Session) -> None:
        """Initialize Account Protection client.

        Mirrors Go Client(sess session.Session, opts ...Option) factory
        from account_protection.go line 94.

        Args:
            session: An authenticated Session instance.
        """
        self._session = session

    # ================================================================
    # Protected Operations (from protected_operation.go)
    # ================================================================

    def list_protected_operations(
        self, params: models.ListProtectedOperationsRequest
    ) -> models.ListProtectedOperationsResponse:
        """Get list of protected operations for a configuration.

        See: https://techdocs.akamai.com/account-protector/reference/get-account-protection

        Args:
            params: Request parameters including config_id, version,
                security_policy_id.

        Returns:
            ListProtectedOperationsResponse with metadata and operations.

        Raises:
            ValueError: If request parameters are invalid.
            errors.Error: If the API returns an error response.
        """
        logger.debug("ListProtectedOperations")

        validation_error = (
            validation.validate_list_protected_operations_request(params)
        )
        if validation_error:
            raise ValueError(
                f"{errors.ErrStructValidation}: {validation_error}"
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/transactional-endpoints/account-protection"
        )

        response, result = self._session.exec(
            "GET", uri,
            expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise self._parse_error(response)

        return self._build_list_response(result)

    def get_protected_operation_by_id(
        self, params: models.GetProtectedOperationByIDRequest
    ) -> models.ListProtectedOperationsResponse:
        """Get protected operation by operation ID.

        See: https://techdocs.akamai.com/account-protector/reference/get-account-protection-op

        Args:
            params: Request parameters including config_id, version,
                security_policy_id, operation_id.

        Returns:
            ListProtectedOperationsResponse with metadata and operations.

        Raises:
            ValueError: If request parameters are invalid.
            errors.Error: If the API returns an error response.
        """
        logger.debug("GetProtectedOperationByID")

        validation_error = (
            validation.validate_get_protected_operation_by_id_request(params)
        )
        if validation_error:
            raise ValueError(
                f"{errors.ErrStructValidation}: {validation_error}"
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/transactional-endpoints/account-protection"
            f"/{params.operation_id}"
        )

        response, result = self._session.exec(
            "GET", uri,
            expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise self._parse_error(response)

        return self._build_list_response(result)

    def create_protected_operations(
        self, params: models.CreateProtectedOperationsRequest
    ) -> models.ListProtectedOperationsResponse:
        """Create a list of protected operations.

        See: https://techdocs.akamai.com/account-protector/reference/post-account-protection

        Args:
            params: Request parameters including config_id, version,
                security_policy_id, json_payload.

        Returns:
            ListProtectedOperationsResponse with metadata and operations.

        Raises:
            ValueError: If request parameters are invalid.
            errors.Error: If the API returns an error response.
        """
        logger.debug("CreateProtectedOperations")

        validation_error = (
            validation.validate_create_protected_operations_request(params)
        )
        if validation_error:
            raise ValueError(
                f"{errors.ErrStructValidation}: {validation_error}"
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/transactional-endpoints/account-protection"
        )

        response, result = self._session.exec(
            "POST", uri,
            body=params.json_payload,
            expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 201:
            raise self._parse_error(response)

        return self._build_list_response(result)

    def update_protected_operation(
        self, params: models.UpdateProtectedOperationRequest
    ) -> dict[str, Any]:
        """Update a protected operation.

        See: https://techdocs.akamai.com/account-protector/reference/put-account-protection-op

        Args:
            params: Request parameters including config_id, version,
                security_policy_id, operation_id, json_payload.

        Returns:
            Response data as a dictionary.

        Raises:
            ValueError: If request parameters are invalid.
            errors.Error: If the API returns an error response.
        """
        logger.debug("UpdateProtectedOperation")

        validation_error = (
            validation.validate_update_protected_operation_request(params)
        )
        if validation_error:
            raise ValueError(
                f"{errors.ErrStructValidation}: {validation_error}"
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/transactional-endpoints/account-protection"
            f"/{params.operation_id}"
        )

        response, result = self._session.exec(
            "PUT", uri,
            body=params.json_payload,
            expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise self._parse_error(response)

        return result

    def remove_protected_operation(
        self, params: models.RemoveProtectedOperationRequest
    ) -> None:
        """Delete a protected operation.

        See: https://techdocs.akamai.com/account-protector/reference/delete-account-protection-op

        Args:
            params: Request parameters including config_id, version,
                security_policy_id, operation_id.

        Raises:
            ValueError: If request parameters are invalid.
            errors.Error: If the API returns an error response.
        """
        logger.debug("RemoveProtectedOperation")

        validation_error = (
            validation.validate_remove_protected_operation_request(params)
        )
        if validation_error:
            raise ValueError(
                f"{errors.ErrStructValidation}: {validation_error}"
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/transactional-endpoints/account-protection"
            f"/{params.operation_id}"
        )

        response, _ = self._session.exec(
            "DELETE", uri,
            error_parser=self._parse_error,
        )

        if response.status_code != 204:
            raise self._parse_error(response)

    # ================================================================
    # General Settings (from general_settings.go)
    # ================================================================

    def get_general_settings(
        self, params: models.GetGeneralSettingsRequest
    ) -> dict[str, Any]:
        """Get general settings for account protection.

        See: https://techdocs.akamai.com/account-protector/reference/get-account-protection-settings

        Args:
            params: Request parameters including config_id, version,
                security_policy_id.

        Returns:
            Response data as a dictionary.

        Raises:
            ValueError: If request parameters are invalid.
            errors.Error: If the API returns an error response.
        """
        logger.debug("GetGeneralSettings")

        validation_error = (
            validation.validate_get_general_settings_request(params)
        )
        if validation_error:
            raise ValueError(
                f"{errors.ErrStructValidation}: {validation_error}"
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/account-protection-settings"
        )

        response, result = self._session.exec(
            "GET", uri,
            expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise self._parse_error(response)

        return result

    def upsert_general_settings(
        self, params: models.UpsertGeneralSettingsRequest
    ) -> dict[str, Any]:
        """Update or create general settings for account protection.

        See: https://techdocs.akamai.com/account-protector/reference/put-account-protection-settings

        Args:
            params: Request parameters including config_id, version,
                security_policy_id, json_payload.

        Returns:
            Response data as a dictionary.

        Raises:
            ValueError: If request parameters are invalid.
            errors.Error: If the API returns an error response.
        """
        logger.debug("UpsertGeneralSettings")

        validation_error = (
            validation.validate_upsert_general_settings_request(params)
        )
        if validation_error:
            raise ValueError(
                f"{errors.ErrStructValidation}: {validation_error}"
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/account-protection-settings"
        )

        response, result = self._session.exec(
            "PUT", uri,
            body=params.json_payload,
            expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise self._parse_error(response)

        return result

    # ================================================================
    # User Risk Response Strategy (from user_risk_response_strategy.go)
    # ================================================================

    def get_user_risk_response_strategy(
        self, params: models.GetUserRiskResponseStrategyRequest
    ) -> dict[str, Any]:
        """Get User Risk Response Strategy for a security configuration.

        See: https://techdocs.akamai.com/account-protector/reference/get-user-risk-response-strategy

        Args:
            params: Request parameters including config_id, version.

        Returns:
            Response data as a dictionary.

        Raises:
            ValueError: If request parameters are invalid.
            errors.Error: If the API returns an error response.
        """
        logger.debug("GetUserRiskResponseStrategy")

        validation_error = (
            validation.validate_get_user_risk_response_strategy_request(
                params
            )
        )
        if validation_error:
            raise ValueError(
                f"{errors.ErrStructValidation}: {validation_error}"
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/advanced-settings/account-protection"
            f"/user-risk-response-strategy"
        )

        response, result = self._session.exec(
            "GET", uri,
            expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise self._parse_error(response)

        return result

    def upsert_user_risk_response_strategy(
        self, params: models.UpsertUserRiskResponseStrategyRequest
    ) -> dict[str, Any]:
        """Update or create User Risk Response Strategy.

        See: https://techdocs.akamai.com/account-protector/reference/put-user-risk-response-strategy

        Args:
            params: Request parameters including config_id, version,
                json_payload.

        Returns:
            Response data as a dictionary.

        Raises:
            ValueError: If request parameters are invalid.
            errors.Error: If the API returns an error response.
        """
        logger.debug("UpsertUserRiskResponseStrategy")

        validation_error = (
            validation.validate_upsert_user_risk_response_strategy_request(
                params
            )
        )
        if validation_error:
            raise ValueError(
                f"{errors.ErrStructValidation}: {validation_error}"
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/advanced-settings/account-protection"
            f"/user-risk-response-strategy"
        )

        response, result = self._session.exec(
            "PUT", uri,
            body=params.json_payload,
            expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise self._parse_error(response)

        return result

    # ================================================================
    # User Allow List ID (from user_allow_list_id.go)
    # ================================================================

    def get_user_allow_list_id(
        self, params: models.GetUserAllowListIDRequest
    ) -> dict[str, Any]:
        """Get User Allow List ID for a security configuration.

        See: https://techdocs.akamai.com/account-protector/reference/get-user-allow-list

        Args:
            params: Request parameters including config_id, version.

        Returns:
            Response data as a dictionary.

        Raises:
            ValueError: If request parameters are invalid.
            errors.Error: If the API returns an error response.
        """
        logger.debug("GetUserAllowListID")

        validation_error = (
            validation.validate_get_user_allow_list_id_request(params)
        )
        if validation_error:
            raise ValueError(
                f"{errors.ErrStructValidation}: {validation_error}"
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/advanced-settings/account-protection"
            f"/user-allow-list-id"
        )

        response, result = self._session.exec(
            "GET", uri,
            expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise self._parse_error(response)

        return result

    def upsert_user_allow_list_id(
        self, params: models.UpsertUserAllowListIDRequest
    ) -> dict[str, Any]:
        """Update User Allow List ID for a security configuration.

        See: https://techdocs.akamai.com/account-protector/reference/put-get-user-allow-list

        Args:
            params: Request parameters including config_id, version,
                json_payload.

        Returns:
            Response data as a dictionary.

        Raises:
            ValueError: If request parameters are invalid.
            errors.Error: If the API returns an error response.
        """
        logger.debug("UpsertUserAllowListID")

        validation_error = (
            validation.validate_upsert_user_allow_list_id_request(params)
        )
        if validation_error:
            raise ValueError(
                f"{errors.ErrStructValidation}: {validation_error}"
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/advanced-settings/account-protection"
            f"/user-allow-list-id"
        )

        response, result = self._session.exec(
            "PUT", uri,
            body=params.json_payload,
            expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise self._parse_error(response)

        return result

    def delete_user_allow_list_id(
        self, params: models.DeleteUserAllowListIDRequest
    ) -> None:
        """Delete User Allow List ID for a security configuration.

        See: https://techdocs.akamai.com/account-protector/reference/delete-get-user-allow-list

        Args:
            params: Request parameters including config_id, version.

        Raises:
            ValueError: If request parameters are invalid.
            errors.Error: If the API returns an error response.
        """
        logger.debug("DeleteUserAllowListID")

        validation_error = (
            validation.validate_delete_user_allow_list_id_request(params)
        )
        if validation_error:
            raise ValueError(
                f"{errors.ErrStructValidation}: {validation_error}"
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/advanced-settings/account-protection"
            f"/user-allow-list-id"
        )

        response, _ = self._session.exec(
            "DELETE", uri,
            error_parser=self._parse_error,
        )

        if response.status_code != 204:
            raise self._parse_error(response)

    # ================================================================
    # Private Helpers
    # ================================================================

    @staticmethod
    def _build_list_response(
        result: dict[str, Any],
    ) -> models.ListProtectedOperationsResponse:
        """Build ListProtectedOperationsResponse from parsed JSON dict.

        Extracts metadata and operations from the raw API response
        dictionary and constructs a typed response model.

        Args:
            result: Parsed JSON response dictionary.

        Returns:
            ListProtectedOperationsResponse instance.
        """
        metadata_data = result.get("metadata", {})
        return models.ListProtectedOperationsResponse(
            metadata=models.Metadata(
                config_id=metadata_data.get("configId", 0),
                config_version=metadata_data.get("configVersion", 0),
                security_policy_id=metadata_data.get(
                    "securityPolicyId", ""
                ),
            ),
            operations=result.get("operations", []),
        )

    def _parse_error(self, response) -> errors.Error:
        """Parse API error from HTTP response.

        Mirrors Go accountProtection.Error() method from errors.go.
        Reads response body, attempts JSON parsing, falls back to HTML
        unescaping for non-JSON error responses.

        CRITICAL: The fallback title message preserves Go's exact string
        verbatim from errors.go line 50, including the "Bot Manager API"
        reference which is intentional in the Go source.

        Args:
            response: The HTTP response to parse.

        Returns:
            Error instance populated from the response.
        """
        # Step 1: Read response body (mirrors Go io.ReadAll(r.Body))
        try:
            body = response.text
        except Exception as err:  # pylint: disable=broad-exception-caught
            logger.error("reading error response body: %s", err)
            return errors.Error(
                status_code=response.status_code,
                title="Failed to read error body",
                detail=str(err),
            )

        # Step 2: Attempt JSON parsing (mirrors Go json.Unmarshal)
        try:
            data = json.loads(body)
            nested_errors = []
            if "errors" in data and isinstance(data["errors"], list):
                nested_errors = [
                    errors.Error(
                        type=e.get("type", ""),
                        title=e.get("title", ""),
                        detail=e.get("detail", ""),
                        status_code=e.get("status", 0),
                    )
                    for e in data["errors"]
                ]
            return errors.Error(
                type=data.get("type", ""),
                title=data.get("title", ""),
                detail=data.get("detail", ""),
                status_code=response.status_code,
                errors=nested_errors,
            )
        except (json.JSONDecodeError, AttributeError) as err:
            # Fallback for non-JSON responses — unescape HTML content.
            # Title message matches Go errors.go line 50 EXACTLY.
            logger.error("could not unmarshal API error: %s", err)
            return errors.Error(
                status_code=response.status_code,
                title=(
                    "Failed to unmarshal error body. Bot Manager API"
                    " failed. Check details for more information."
                ),
                detail=unescape_content(body),
            )
