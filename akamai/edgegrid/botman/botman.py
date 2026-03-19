# pylint: disable=too-many-lines
"""Akamai Bot Manager API client implementation.

Provides the BotManClient class with all endpoint methods for managing
custom clients, bots, categories, challenge actions, detections,
management settings, and content protection.

Mirrors Go pkg/botman.BotMan interface.
"""

import logging
from typing import Any

from akamai.edgegrid.session import Session
from akamai.edgegrid.botman import errors
from akamai.edgegrid.botman import models
from akamai.edgegrid.botman import validation

logger = logging.getLogger(__name__)


def _check_validation(err_msg: str | None) -> None:
    """Raise :class:`errors.Error` if a validation function returned an error.

    Mirrors Go pattern::

        if err := params.Validate(); err != nil {
            return nil, fmt.Errorf("%w: %s", ErrStructValidation, err.Error())
        }

    Args:
        err_msg: The string returned by a ``validation.validate_*`` call,
                 or ``None`` when the request is valid.

    Raises:
        errors.Error: With ``type`` and ``title`` set to
            :data:`errors.ErrStructValidation` and ``detail`` set to
            the validation error message.
    """
    if err_msg is not None:
        raise errors.Error(
            type=errors.ErrStructValidation,
            title=errors.ErrStructValidation,
            detail=err_msg,
        )


class BotManClient:  # pylint: disable=too-many-public-methods
    """Akamai Bot Manager API client.

    Provides access to the Akamai Bot Manager API for managing custom clients,
    bots, categories, challenge actions, detections, management settings,
    and content protection.

    Mirrors Go pkg/botman.BotMan interface.
    """

    def __init__(self, session: Session) -> None:
        """Initialize the Bot Manager client.

        Mirrors Go botman.Client() factory function.

        Args:
            session: Authenticated Akamai API session.
        """
        self._session = session

    # ------------------------------------------------------------------ #
    # AkamaiBotCategory
    # ------------------------------------------------------------------ #

    def get_akamai_bot_category_list(
        self,
        params: models.GetAkamaiBotCategoryListRequest,
    ) -> models.GetAkamaiBotCategoryListResponse:
        """Retrieve a list of Akamai bot categories.

        https://techdocs.akamai.com/bot-manager/reference/get-akamai-bot-categories
        """
        logger.debug("GetAkamaiBotCategoryList")

        path = "/appsec/v1/akamai-bot-categories"
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        categories = result.get("categories", [])
        if params.category_name:
            categories = [
                c for c in categories
                if c.get("categoryName") == params.category_name
            ]

        return models.GetAkamaiBotCategoryListResponse(categories=categories)

    # ------------------------------------------------------------------ #
    # AkamaiBotCategoryAction
    # ------------------------------------------------------------------ #

    def get_akamai_bot_category_action(
        self,
        params: models.GetAkamaiBotCategoryActionRequest,
    ) -> dict[str, Any]:
        """Retrieve a specific Akamai bot category action.

        https://techdocs.akamai.com/bot-manager/reference/get-akamai-bot-category-action
        """
        logger.debug("GetAkamaiBotCategoryAction")
        _check_validation(validation.validate_get_akamai_bot_category_action_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/akamai-bot-category-actions/{params.category_id}"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def get_akamai_bot_category_action_list(
        self,
        params: models.GetAkamaiBotCategoryActionListRequest,
    ) -> models.GetAkamaiBotCategoryActionListResponse:
        """Retrieve Akamai bot category actions for a configuration.

        https://techdocs.akamai.com/bot-manager/reference/get-akamai-bot-category-actions
        """
        logger.debug("GetAkamaiBotCategoryActionList")
        _check_validation(validation.validate_get_akamai_bot_category_action_list_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/akamai-bot-category-actions"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        actions = result.get("actions", [])
        if params.category_id:
            actions = [
                a for a in actions
                if a.get("categoryId") == params.category_id
            ]

        return models.GetAkamaiBotCategoryActionListResponse(
            akamai_bot_category_actions=actions,
        )

    def update_akamai_bot_category_action(
        self,
        params: models.UpdateAkamaiBotCategoryActionRequest,
    ) -> dict[str, Any]:
        """Update an Akamai bot category action.

        https://techdocs.akamai.com/bot-manager/reference/put-akamai-bot-category-action
        """
        logger.debug("UpdateAkamaiBotCategoryAction")
        _check_validation(validation.validate_update_akamai_bot_category_action_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/akamai-bot-category-actions/{params.category_id}"
        )
        response, result = self._session.exec(
            "PUT", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    # ------------------------------------------------------------------ #
    # AkamaiDefinedBot
    # ------------------------------------------------------------------ #

    def get_akamai_defined_bot_list(
        self,
        params: models.GetAkamaiDefinedBotListRequest,
    ) -> models.GetAkamaiDefinedBotListResponse:
        """Retrieve a list of Akamai-defined bots.

        https://techdocs.akamai.com/bot-manager/reference/get-akamai-defined-bots
        """
        logger.debug("GetAkamaiDefinedBotList")

        path = "/appsec/v1/akamai-defined-bots"
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        bots = result.get("bots", [])
        if params.bot_name:
            bots = [b for b in bots if b.get("botName") == params.bot_name]

        return models.GetAkamaiDefinedBotListResponse(bots=bots)

    # ------------------------------------------------------------------ #
    # BotAnalyticsCookie
    # ------------------------------------------------------------------ #

    def get_bot_analytics_cookie(
        self,
        params: models.GetBotAnalyticsCookieRequest,
    ) -> dict[str, Any]:
        """Retrieve bot analytics cookie settings.

        https://techdocs.akamai.com/bot-manager/reference/get-bot-analytics-cookie
        """
        logger.debug("GetBotAnalyticsCookie")
        _check_validation(validation.validate_get_bot_analytics_cookie_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/advanced-settings/bot-analytics-cookie"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def update_bot_analytics_cookie(
        self,
        params: models.UpdateBotAnalyticsCookieRequest,
    ) -> dict[str, Any]:
        """Update bot analytics cookie settings.

        https://techdocs.akamai.com/bot-manager/reference/put-bot-analytics-cookie
        """
        logger.debug("UpdateBotAnalyticsCookie")
        _check_validation(validation.validate_update_bot_analytics_cookie_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/advanced-settings/bot-analytics-cookie"
        )
        response, result = self._session.exec(
            "PUT", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    # ------------------------------------------------------------------ #
    # BotAnalyticsCookieValues
    # ------------------------------------------------------------------ #

    def get_bot_analytics_cookie_values(self) -> dict[str, Any]:
        """Retrieve bot analytics cookie values.

        https://techdocs.akamai.com/bot-manager/reference/get-bot-analytics-cookie-values
        """
        logger.debug("GetBotAnalyticsCookieValues")

        path = "/appsec/v1/bot-analytics-cookie-values"
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    # ------------------------------------------------------------------ #
    # BotCategoryException
    # ------------------------------------------------------------------ #

    def get_bot_category_exception(
        self,
        params: models.GetBotCategoryExceptionRequest,
    ) -> dict[str, Any]:
        """Retrieve bot category exception settings.

        https://techdocs.akamai.com/bot-manager/reference/get-bot-category-exceptions
        """
        logger.debug("GetBotCategoryException")
        _check_validation(validation.validate_get_bot_category_exception_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/bot-category-exceptions"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def update_bot_category_exception(
        self,
        params: models.UpdateBotCategoryExceptionRequest,
    ) -> dict[str, Any]:
        """Update bot category exception settings.

        https://techdocs.akamai.com/bot-manager/reference/put-bot-category-exceptions
        """
        logger.debug("UpdateBotCategoryException")
        _check_validation(validation.validate_update_bot_category_exception_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/bot-category-exceptions"
        )
        response, result = self._session.exec(
            "PUT", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    # ------------------------------------------------------------------ #
    # BotDetection
    # ------------------------------------------------------------------ #

    def get_bot_detection_list(
        self,
        params: models.GetBotDetectionListRequest,
    ) -> models.GetBotDetectionListResponse:
        """Retrieve a list of bot detections.

        https://techdocs.akamai.com/bot-manager/reference/get-bot-detections
        """
        logger.debug("GetBotDetectionList")

        path = "/appsec/v1/bot-detections"
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        detections = result.get("detections", [])
        if params.detection_name:
            detections = [
                d for d in detections
                if d.get("detectionName") == params.detection_name
            ]

        return models.GetBotDetectionListResponse(detections=detections)

    # ------------------------------------------------------------------ #
    # BotDetectionAction
    # ------------------------------------------------------------------ #

    def get_bot_detection_action(
        self,
        params: models.GetBotDetectionActionRequest,
    ) -> dict[str, Any]:
        """Retrieve a specific bot detection action.

        https://techdocs.akamai.com/bot-manager/reference/get-bot-detection-action
        """
        logger.debug("GetBotDetectionAction")
        _check_validation(validation.validate_get_bot_detection_action_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/bot-detection-actions/{params.detection_id}"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def get_bot_detection_action_list(
        self,
        params: models.GetBotDetectionActionListRequest,
    ) -> models.GetBotDetectionActionListResponse:
        """Retrieve bot detection actions for a configuration.

        https://techdocs.akamai.com/bot-manager/reference/get-bot-detection-actions
        """
        logger.debug("GetBotDetectionActionList")
        _check_validation(validation.validate_get_bot_detection_action_list_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/bot-detection-actions"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        actions = result.get("actions", [])
        if params.detection_id:
            actions = [
                a for a in actions
                if a.get("detectionId") == params.detection_id
            ]

        return models.GetBotDetectionActionListResponse(
            bot_detection_actions=actions,
        )

    def update_bot_detection_action(
        self,
        params: models.UpdateBotDetectionActionRequest,
    ) -> dict[str, Any]:
        """Update a bot detection action.

        https://techdocs.akamai.com/bot-manager/reference/put-bot-detection-action
        """
        logger.debug("UpdateBotDetectionAction")
        _check_validation(validation.validate_update_bot_detection_action_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/bot-detection-actions/{params.detection_id}"
        )
        response, result = self._session.exec(
            "PUT", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    # ------------------------------------------------------------------ #
    # BotEndpointCoverageReport
    # ------------------------------------------------------------------ #

    def get_bot_endpoint_coverage_report(
        self,
        params: models.GetBotEndpointCoverageReportRequest,
    ) -> models.GetBotEndpointCoverageReportResponse:
        """Retrieve bot endpoint coverage report.

        https://techdocs.akamai.com/bot-manager/reference/get-bot-endpoint-coverage-report
        """
        logger.debug("GetBotEndpointCoverageReport")
        _check_validation(validation.validate_get_bot_endpoint_coverage_report_request(params))

        if params.config_id and params.version:
            path = (
                f"/appsec/v1/configs/{params.config_id}"
                f"/versions/{params.version}/bot-endpoint-coverage-report"
            )
        else:
            path = "/appsec/v1/bot-endpoint-coverage-report"

        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        operations = result.get("operations", [])
        if params.operation_id:
            operations = [
                o for o in operations
                if o.get("operationId") == params.operation_id
            ]

        return models.GetBotEndpointCoverageReportResponse(
            operations=operations,
        )

    # ------------------------------------------------------------------ #
    # BotManagementSetting
    # ------------------------------------------------------------------ #

    def get_bot_management_setting(
        self,
        params: models.GetBotManagementSettingRequest,
    ) -> dict[str, Any]:
        """Retrieve bot management settings.

        https://techdocs.akamai.com/bot-manager/reference/get-bot-management-settings
        """
        logger.debug("GetBotManagementSetting")
        _check_validation(validation.validate_get_bot_management_setting_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/bot-management-settings"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def update_bot_management_setting(
        self,
        params: models.UpdateBotManagementSettingRequest,
    ) -> dict[str, Any]:
        """Update bot management settings.

        https://techdocs.akamai.com/bot-manager/reference/put-bot-management-settings
        """
        logger.debug("UpdateBotManagementSetting")
        _check_validation(validation.validate_update_bot_management_setting_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/bot-management-settings"
        )
        response, result = self._session.exec(
            "PUT", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    # ------------------------------------------------------------------ #
    # ChallengeAction
    # ------------------------------------------------------------------ #

    def get_challenge_action(
        self,
        params: models.GetChallengeActionRequest,
    ) -> dict[str, Any]:
        """Retrieve a specific challenge action.

        https://techdocs.akamai.com/bot-manager/reference/get-challenge-action
        """
        logger.debug("GetChallengeAction")
        _check_validation(validation.validate_get_challenge_action_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/response-actions/challenge-actions/{params.action_id}"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def get_challenge_action_list(
        self,
        params: models.GetChallengeActionListRequest,
    ) -> models.GetChallengeActionListResponse:
        """Retrieve challenge actions for a configuration.

        https://techdocs.akamai.com/bot-manager/reference/get-challenge-actions
        """
        logger.debug("GetChallengeActionList")
        _check_validation(validation.validate_get_challenge_action_list_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/response-actions/challenge-actions"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        challenge_actions = result.get("challengeActions", [])
        if params.action_id:
            challenge_actions = [
                a for a in challenge_actions
                if a.get("actionId") == params.action_id
            ]

        return models.GetChallengeActionListResponse(
            challenge_actions=challenge_actions,
        )

    def create_challenge_action(
        self,
        params: models.CreateChallengeActionRequest,
    ) -> dict[str, Any]:
        """Create a new challenge action.

        https://techdocs.akamai.com/bot-manager/reference/post-challenge-action
        """
        logger.debug("CreateChallengeAction")
        _check_validation(validation.validate_create_challenge_action_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/response-actions/challenge-actions"
        )
        response, result = self._session.exec(
            "POST", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 201:
            raise errors.Error.from_response(response)

        return result

    def update_challenge_action(
        self,
        params: models.UpdateChallengeActionRequest,
    ) -> dict[str, Any]:
        """Update a challenge action.

        https://techdocs.akamai.com/bot-manager/reference/put-challenge-action
        """
        logger.debug("UpdateChallengeAction")
        _check_validation(validation.validate_update_challenge_action_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/response-actions/challenge-actions/{params.action_id}"
        )
        response, result = self._session.exec(
            "PUT", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def remove_challenge_action(
        self,
        params: models.RemoveChallengeActionRequest,
    ) -> None:
        """Remove a challenge action.

        https://techdocs.akamai.com/bot-manager/reference/delete-challenge-action
        """
        logger.debug("RemoveChallengeAction")
        _check_validation(validation.validate_remove_challenge_action_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/response-actions/challenge-actions/{params.action_id}"
        )
        response, _ = self._session.exec(
            "DELETE", path,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 204:
            raise errors.Error.from_response(response)

    def update_google_recaptcha_secret_key(
        self,
        params: models.UpdateGoogleReCaptchaSecretKeyRequest,
    ) -> None:
        """Update Google reCAPTCHA secret key for a challenge action.

        https://techdocs.akamai.com/bot-manager/reference/put-google-recaptcha-secret-key
        """
        logger.debug("UpdateGoogleReCaptchaSecretKey")
        _check_validation(validation.validate_update_google_recaptcha_secret_key_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/response-actions/challenge-actions/{params.action_id}"
            f"/google-recaptcha-secret-key"
        )
        body = {"googleReCaptchaSecretKey": params.secret_key}
        response, _ = self._session.exec(
            "PUT", path, body=body,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 204:
            raise errors.Error.from_response(response)

    # ------------------------------------------------------------------ #
    # ChallengeInjectionRules
    # ------------------------------------------------------------------ #

    def get_challenge_injection_rules(
        self,
        params: models.GetChallengeInjectionRulesRequest,
    ) -> dict[str, Any]:
        """Retrieve challenge injection rules.

        https://techdocs.akamai.com/bot-manager/reference/get-challenge-injection-rules
        """
        logger.debug("GetChallengeInjectionRules")
        _check_validation(validation.validate_get_challenge_injection_rules_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/advanced-settings/challenge-injection-rules"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def update_challenge_injection_rules(
        self,
        params: models.UpdateChallengeInjectionRulesRequest,
    ) -> dict[str, Any]:
        """Update challenge injection rules.

        https://techdocs.akamai.com/bot-manager/reference/put-challenge-injection-rules
        """
        logger.debug("UpdateChallengeInjectionRules")
        _check_validation(validation.validate_update_challenge_injection_rules_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/advanced-settings/challenge-injection-rules"
        )
        response, result = self._session.exec(
            "PUT", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    # ------------------------------------------------------------------ #
    # ClientSideSecurity
    # ------------------------------------------------------------------ #

    def get_client_side_security(
        self,
        params: models.GetClientSideSecurityRequest,
    ) -> dict[str, Any]:
        """Retrieve client-side security settings.

        https://techdocs.akamai.com/bot-manager/reference/get-client-side-security
        """
        logger.debug("GetClientSideSecurity")
        _check_validation(validation.validate_get_client_side_security_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/advanced-settings/client-side-security"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def update_client_side_security(
        self,
        params: models.UpdateClientSideSecurityRequest,
    ) -> dict[str, Any]:
        """Update client-side security settings.

        https://techdocs.akamai.com/bot-manager/reference/put-client-side-security
        """
        logger.debug("UpdateClientSideSecurity")
        _check_validation(validation.validate_update_client_side_security_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/advanced-settings/client-side-security"
        )
        response, result = self._session.exec(
            "PUT", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    # ------------------------------------------------------------------ #
    # ConditionalAction
    # ------------------------------------------------------------------ #

    def get_conditional_action(
        self,
        params: models.GetConditionalActionRequest,
    ) -> dict[str, Any]:
        """Retrieve a specific conditional action.

        https://techdocs.akamai.com/bot-manager/reference/get-conditional-action
        """
        logger.debug("GetConditionalAction")
        _check_validation(validation.validate_get_conditional_action_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/response-actions/conditional-actions/{params.action_id}"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def get_conditional_action_list(
        self,
        params: models.GetConditionalActionListRequest,
    ) -> models.GetConditionalActionListResponse:
        """Retrieve conditional actions for a configuration.

        https://techdocs.akamai.com/bot-manager/reference/get-conditional-actions
        """
        logger.debug("GetConditionalActionList")
        _check_validation(validation.validate_get_conditional_action_list_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/response-actions/conditional-actions"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        conditional_actions = result.get("conditionalActions", [])
        if params.action_id:
            conditional_actions = [
                a for a in conditional_actions
                if a.get("actionId") == params.action_id
            ]

        return models.GetConditionalActionListResponse(
            conditional_actions=conditional_actions,
        )

    def create_conditional_action(
        self,
        params: models.CreateConditionalActionRequest,
    ) -> dict[str, Any]:
        """Create a new conditional action.

        https://techdocs.akamai.com/bot-manager/reference/post-conditional-action
        """
        logger.debug("CreateConditionalAction")
        _check_validation(validation.validate_create_conditional_action_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/response-actions/conditional-actions"
        )
        response, result = self._session.exec(
            "POST", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 201:
            raise errors.Error.from_response(response)

        return result

    def update_conditional_action(
        self,
        params: models.UpdateConditionalActionRequest,
    ) -> dict[str, Any]:
        """Update a conditional action.

        https://techdocs.akamai.com/bot-manager/reference/put-conditional-action
        """
        logger.debug("UpdateConditionalAction")
        _check_validation(validation.validate_update_conditional_action_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/response-actions/conditional-actions/{params.action_id}"
        )
        response, result = self._session.exec(
            "PUT", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def remove_conditional_action(
        self,
        params: models.RemoveConditionalActionRequest,
    ) -> None:
        """Remove a conditional action.

        https://techdocs.akamai.com/bot-manager/reference/delete-conditional-action
        """
        logger.debug("RemoveConditionalAction")
        _check_validation(validation.validate_remove_conditional_action_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/response-actions/conditional-actions/{params.action_id}"
        )
        response, _ = self._session.exec(
            "DELETE", path,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 204:
            raise errors.Error.from_response(response)

    # ------------------------------------------------------------------ #
    # ContentProtectionJavaScriptInjectionRule
    # ------------------------------------------------------------------ #

    def get_content_protection_javascript_injection_rule(
        self,
        params: models.GetContentProtectionJavaScriptInjectionRuleRequest,
    ) -> dict[str, Any]:
        """Retrieve a specific content protection JavaScript injection rule.

        https://techdocs.akamai.com/content-protector/reference/get-content-protection-javascript-injection-rule
        """
        logger.debug("GetContentProtectionJavaScriptInjectionRule")
        _check_validation(
            validation.validate_get_content_protection_javascript_injection_rule_request(
                params,
            )
        )

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/content-protection-javascript-injection-rules"
            f"/{params.content_protection_javascript_injection_rule_id}"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def get_content_protection_javascript_injection_rule_list(
        self,
        params: models.GetContentProtectionJavaScriptInjectionRuleListRequest,
    ) -> models.GetContentProtectionJavaScriptInjectionRuleListResponse:
        """Retrieve content protection JavaScript injection rules for a policy.

        https://techdocs.akamai.com/content-protector/reference/get-content-protection-javascript-injection-rules
        """
        logger.debug("GetContentProtectionJavaScriptInjectionRuleList")
        _check_validation(
            validation.validate_get_content_protection_javascript_injection_rule_list_request(
                params,
            )
        )

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/content-protection-javascript-injection-rules"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        rules = result.get("contentProtectionJavaScriptInjectionRules", [])
        if params.content_protection_javascript_injection_rule_id:
            rules = [
                r for r in rules
                if r.get("contentProtectionJavaScriptInjectionRuleId")
                == params.content_protection_javascript_injection_rule_id
            ]

        return models.GetContentProtectionJavaScriptInjectionRuleListResponse(
            content_protection_javascript_injection_rules=rules,
        )

    def create_content_protection_javascript_injection_rule(
        self,
        params: models.CreateContentProtectionJavaScriptInjectionRuleRequest,
    ) -> dict[str, Any]:
        """Create a content protection JavaScript injection rule.

        https://techdocs.akamai.com/content-protector/reference/post-content-protection-javascript-injection-rule
        """
        logger.debug("CreateContentProtectionJavaScriptInjectionRule")
        _check_validation(
            validation.validate_create_content_protection_javascript_injection_rule_request(
                params,
            )
        )

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/content-protection-javascript-injection-rules"
        )
        response, result = self._session.exec(
            "POST", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 201:
            raise errors.Error.from_response(response)

        return result

    def update_content_protection_javascript_injection_rule(
        self,
        params: models.UpdateContentProtectionJavaScriptInjectionRuleRequest,
    ) -> dict[str, Any]:
        """Update a content protection JavaScript injection rule.

        https://techdocs.akamai.com/content-protector/reference/put-content-protection-javascript-injection-rule
        """
        logger.debug("UpdateContentProtectionJavaScriptInjectionRule")
        _check_validation(
            validation.validate_update_content_protection_javascript_injection_rule_request(
                params,
            )
        )

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/content-protection-javascript-injection-rules"
            f"/{params.content_protection_javascript_injection_rule_id}"
        )
        response, result = self._session.exec(
            "PUT", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def remove_content_protection_javascript_injection_rule(
        self,
        params: models.RemoveContentProtectionJavaScriptInjectionRuleRequest,
    ) -> None:
        """Remove a content protection JavaScript injection rule.

        https://techdocs.akamai.com/content-protector/reference/delete-content-protection-javascript-injection-rule
        """
        logger.debug("RemoveContentProtectionJavaScriptInjectionRule")
        _check_validation(
            validation.validate_remove_content_protection_javascript_injection_rule_request(
                params,
            )
        )

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/content-protection-javascript-injection-rules"
            f"/{params.content_protection_javascript_injection_rule_id}"
        )
        response, _ = self._session.exec(
            "DELETE", path,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 204:
            raise errors.Error.from_response(response)

    # ------------------------------------------------------------------ #
    # ContentProtectionRule
    # ------------------------------------------------------------------ #

    def get_content_protection_rule(
        self,
        params: models.GetContentProtectionRuleRequest,
    ) -> dict[str, Any]:
        """Retrieve a specific content protection rule.

        https://techdocs.akamai.com/content-protector/reference/get-content-protection-rule
        """
        logger.debug("GetContentProtectionRule")
        _check_validation(validation.validate_get_content_protection_rule_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/content-protection-rules/{params.content_protection_rule_id}"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def get_content_protection_rule_list(
        self,
        params: models.GetContentProtectionRuleListRequest,
    ) -> models.GetContentProtectionRuleListResponse:
        """Retrieve content protection rules for a policy.

        https://techdocs.akamai.com/content-protector/reference/get-content-protection-rules
        """
        logger.debug("GetContentProtectionRuleList")
        _check_validation(validation.validate_get_content_protection_rule_list_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/content-protection-rules"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        rules = result.get("contentProtectionRules", [])
        if params.content_protection_rule_id:
            rules = [
                r for r in rules
                if r.get("contentProtectionRuleId")
                == params.content_protection_rule_id
            ]

        return models.GetContentProtectionRuleListResponse(
            content_protection_rules=rules,
        )

    def create_content_protection_rule(
        self,
        params: models.CreateContentProtectionRuleRequest,
    ) -> dict[str, Any]:
        """Create a content protection rule.

        https://techdocs.akamai.com/content-protector/reference/post-content-protection-rule
        """
        logger.debug("CreateContentProtectionRule")
        _check_validation(validation.validate_create_content_protection_rule_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/content-protection-rules"
        )
        response, result = self._session.exec(
            "POST", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 201:
            raise errors.Error.from_response(response)

        return result

    def update_content_protection_rule(
        self,
        params: models.UpdateContentProtectionRuleRequest,
    ) -> dict[str, Any]:
        """Update a content protection rule.

        https://techdocs.akamai.com/content-protector/reference/put-content-protection-rule
        """
        logger.debug("UpdateContentProtectionRule")
        _check_validation(validation.validate_update_content_protection_rule_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/content-protection-rules/{params.content_protection_rule_id}"
        )
        response, result = self._session.exec(
            "PUT", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def remove_content_protection_rule(
        self,
        params: models.RemoveContentProtectionRuleRequest,
    ) -> None:
        """Remove a content protection rule.

        https://techdocs.akamai.com/content-protector/reference/delete-content-protection-rule
        """
        logger.debug("RemoveContentProtectionRule")
        _check_validation(validation.validate_remove_content_protection_rule_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/content-protection-rules/{params.content_protection_rule_id}"
        )
        response, _ = self._session.exec(
            "DELETE", path,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 204:
            raise errors.Error.from_response(response)

    # ------------------------------------------------------------------ #
    # ContentProtectionRuleSequence
    # ------------------------------------------------------------------ #

    def get_content_protection_rule_sequence(
        self,
        params: models.GetContentProtectionRuleSequenceRequest,
    ) -> models.GetContentProtectionRuleSequenceResponse:
        """Retrieve content protection rule sequence.

        https://techdocs.akamai.com/content-protector/reference/get-content-protection-rule-sequence
        """
        logger.debug("GetContentProtectionRuleSequence")
        _check_validation(validation.validate_get_content_protection_rule_sequence_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/content-protection-rule-sequence"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        # Parse into shared ContentProtectionRuleUUIDSequence (mirrors Go type alias)
        cp_seq = models.ContentProtectionRuleUUIDSequence(
            content_protection_rule_sequence=result.get(
                "contentProtectionRuleSequence", [],
            ),
        )
        return models.GetContentProtectionRuleSequenceResponse(
            content_protection_rule_sequence=cp_seq.content_protection_rule_sequence,
        )

    def update_content_protection_rule_sequence(
        self,
        params: models.UpdateContentProtectionRuleSequenceRequest,
    ) -> models.UpdateContentProtectionRuleSequenceResponse:
        """Update content protection rule sequence.

        https://techdocs.akamai.com/content-protector/reference/put-content-protection-rule-sequence
        """
        logger.debug("UpdateContentProtectionRuleSequence")
        _check_validation(validation.validate_update_content_protection_rule_sequence_request(
            params,
        ))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/content-protection-rule-sequence"
        )
        body = {
            "contentProtectionRuleSequence": (
                params.content_protection_rule_sequence
                .content_protection_rule_sequence
            ),
        }
        response, result = self._session.exec(
            "PUT", path, body=body, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        # Parse into shared ContentProtectionRuleUUIDSequence (mirrors Go type alias)
        cp_seq = models.ContentProtectionRuleUUIDSequence(
            content_protection_rule_sequence=result.get(
                "contentProtectionRuleSequence", [],
            ),
        )
        return models.UpdateContentProtectionRuleSequenceResponse(
            content_protection_rule_sequence=cp_seq.content_protection_rule_sequence,
        )

    # ------------------------------------------------------------------ #
    # CustomBotCategory
    # ------------------------------------------------------------------ #

    def get_custom_bot_category(
        self,
        params: models.GetCustomBotCategoryRequest,
    ) -> dict[str, Any]:
        """Retrieve a specific custom bot category.

        https://techdocs.akamai.com/bot-manager/reference/get-custom-bot-category
        """
        logger.debug("GetCustomBotCategory")
        _check_validation(validation.validate_get_custom_bot_category_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-bot-categories/{params.category_id}"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def get_custom_bot_category_list(
        self,
        params: models.GetCustomBotCategoryListRequest,
    ) -> models.GetCustomBotCategoryListResponse:
        """Retrieve custom bot categories for a configuration.

        https://techdocs.akamai.com/bot-manager/reference/get-custom-bot-categories
        """
        logger.debug("GetCustomBotCategoryList")
        _check_validation(validation.validate_get_custom_bot_category_list_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-bot-categories"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        categories = result.get("categories", [])
        if params.category_id:
            categories = [
                c for c in categories
                if c.get("categoryId") == params.category_id
            ]

        return models.GetCustomBotCategoryListResponse(
            categories=categories,
        )

    def create_custom_bot_category(
        self,
        params: models.CreateCustomBotCategoryRequest,
    ) -> dict[str, Any]:
        """Create a custom bot category.

        https://techdocs.akamai.com/bot-manager/reference/post-custom-bot-category
        """
        logger.debug("CreateCustomBotCategory")
        _check_validation(validation.validate_create_custom_bot_category_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-bot-categories"
        )
        response, result = self._session.exec(
            "POST", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 201:
            raise errors.Error.from_response(response)

        return result

    def update_custom_bot_category(
        self,
        params: models.UpdateCustomBotCategoryRequest,
    ) -> dict[str, Any]:
        """Update a custom bot category.

        https://techdocs.akamai.com/bot-manager/reference/put-custom-bot-category
        """
        logger.debug("UpdateCustomBotCategory")
        _check_validation(validation.validate_update_custom_bot_category_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-bot-categories/{params.category_id}"
        )
        response, result = self._session.exec(
            "PUT", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def remove_custom_bot_category(
        self,
        params: models.RemoveCustomBotCategoryRequest,
    ) -> None:
        """Remove a custom bot category.

        https://techdocs.akamai.com/bot-manager/reference/delete-custom-bot-category
        """
        logger.debug("RemoveCustomBotCategory")
        _check_validation(validation.validate_remove_custom_bot_category_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-bot-categories/{params.category_id}"
        )
        response, _ = self._session.exec(
            "DELETE", path,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 204:
            raise errors.Error.from_response(response)

    # ------------------------------------------------------------------ #
    # CustomBotCategoryAction
    # ------------------------------------------------------------------ #

    def get_custom_bot_category_action(
        self,
        params: models.GetCustomBotCategoryActionRequest,
    ) -> dict[str, Any]:
        """Retrieve a specific custom bot category action.

        https://techdocs.akamai.com/bot-manager/reference/get-custom-bot-category-action
        """
        logger.debug("GetCustomBotCategoryAction")
        _check_validation(validation.validate_get_custom_bot_category_action_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/custom-bot-category-actions/{params.category_id}"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def get_custom_bot_category_action_list(
        self,
        params: models.GetCustomBotCategoryActionListRequest,
    ) -> models.GetCustomBotCategoryActionListResponse:
        """Retrieve custom bot category actions for a policy.

        https://techdocs.akamai.com/bot-manager/reference/get-custom-bot-category-actions
        """
        logger.debug("GetCustomBotCategoryActionList")
        _check_validation(validation.validate_get_custom_bot_category_action_list_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/custom-bot-category-actions"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        actions = result.get("actions", [])
        if params.category_id:
            actions = [
                a for a in actions
                if a.get("categoryId") == params.category_id
            ]

        return models.GetCustomBotCategoryActionListResponse(actions=actions)

    def update_custom_bot_category_action(
        self,
        params: models.UpdateCustomBotCategoryActionRequest,
    ) -> dict[str, Any]:
        """Update a custom bot category action.

        https://techdocs.akamai.com/bot-manager/reference/put-custom-bot-category-action
        """
        logger.debug("UpdateCustomBotCategoryAction")
        _check_validation(validation.validate_update_custom_bot_category_action_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/custom-bot-category-actions/{params.category_id}"
        )
        response, result = self._session.exec(
            "PUT", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    # ------------------------------------------------------------------ #
    # CustomBotCategoryItemSequence
    # ------------------------------------------------------------------ #

    def get_custom_bot_category_item_sequence(
        self,
        params: models.GetCustomBotCategoryItemSequenceRequest,
    ) -> models.GetCustomBotCategoryItemSequenceResponse:
        """Retrieve custom bot category item sequence.

        https://techdocs.akamai.com/bot-manager/reference/get-custom-bot-category-item-sequence
        """
        logger.debug("GetCustomBotCategoryItemSequence")
        _check_validation(validation.validate_get_custom_bot_category_item_sequence_request(
            params,
        ))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-bot-categories/{params.category_id}"
            f"/custom-bot-category-item-sequence"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        # Parse into shared UUIDSequence type (mirrors Go type alias pattern)
        uuid_seq = models.UUIDSequence(sequence=result.get("sequence", []))
        return models.GetCustomBotCategoryItemSequenceResponse(
            sequence=uuid_seq.sequence,
        )

    def update_custom_bot_category_item_sequence(
        self,
        params: models.UpdateCustomBotCategoryItemSequenceRequest,
    ) -> models.UpdateCustomBotCategoryItemSequenceResponse:
        """Update custom bot category item sequence.

        https://techdocs.akamai.com/bot-manager/reference/put-custom-bot-category-item-sequence
        """
        logger.debug("UpdateCustomBotCategoryItemSequence")
        _check_validation(validation.validate_update_custom_bot_category_item_sequence_request(
            params,
        ))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-bot-categories/{params.category_id}"
            f"/custom-bot-category-item-sequence"
        )
        body = {"sequence": params.sequence}
        response, result = self._session.exec(
            "PUT", path, body=body, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        # Parse into shared UUIDSequence type (mirrors Go type alias pattern)
        uuid_seq = models.UUIDSequence(sequence=result.get("sequence", []))
        return models.UpdateCustomBotCategoryItemSequenceResponse(
            sequence=uuid_seq.sequence,
        )

    # ------------------------------------------------------------------ #
    # CustomBotCategorySequence
    # ------------------------------------------------------------------ #

    def get_custom_bot_category_sequence(
        self,
        params: models.GetCustomBotCategorySequenceRequest,
    ) -> models.CustomBotCategorySequenceResponse:
        """Retrieve custom bot category sequence.

        https://techdocs.akamai.com/bot-manager/reference/get-custom-bot-category-sequence
        """
        logger.debug("GetCustomBotCategorySequence")
        _check_validation(validation.validate_get_custom_bot_category_sequence_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-bot-category-sequence"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return models.CustomBotCategorySequenceResponse(
            sequence=result.get("sequence", []),
        )

    def update_custom_bot_category_sequence(
        self,
        params: models.UpdateCustomBotCategorySequenceRequest,
    ) -> models.CustomBotCategorySequenceResponse:
        """Update custom bot category sequence.

        https://techdocs.akamai.com/bot-manager/reference/put-custom-bot-category-sequence
        """
        logger.debug("UpdateCustomBotCategorySequence")
        _check_validation(validation.validate_update_custom_bot_category_sequence_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-bot-category-sequence"
        )
        body = {"sequence": params.sequence}
        response, result = self._session.exec(
            "PUT", path, body=body, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return models.CustomBotCategorySequenceResponse(
            sequence=result.get("sequence", []),
        )

    # ------------------------------------------------------------------ #
    # CustomClient
    # ------------------------------------------------------------------ #

    def get_custom_client(
        self,
        params: models.GetCustomClientRequest,
    ) -> dict[str, Any]:
        """Retrieve a specific custom client.

        https://techdocs.akamai.com/bot-manager/reference/get-custom-client
        """
        logger.debug("GetCustomClient")
        _check_validation(validation.validate_get_custom_client_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-clients/{params.custom_client_id}"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def get_custom_client_list(
        self,
        params: models.GetCustomClientListRequest,
    ) -> models.GetCustomClientListResponse:
        """Retrieve custom clients for a configuration.

        https://techdocs.akamai.com/bot-manager/reference/get-custom-clients
        """
        logger.debug("GetCustomClientList")
        _check_validation(validation.validate_get_custom_client_list_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-clients"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        custom_clients = result.get("customClients", [])
        if params.custom_client_id:
            custom_clients = [
                c for c in custom_clients
                if c.get("customClientId") == params.custom_client_id
            ]

        return models.GetCustomClientListResponse(
            custom_clients=custom_clients,
        )

    def create_custom_client(
        self,
        params: models.CreateCustomClientRequest,
    ) -> dict[str, Any]:
        """Create a custom client.

        https://techdocs.akamai.com/bot-manager/reference/post-custom-clients
        """
        logger.debug("CreateCustomClient")
        _check_validation(validation.validate_create_custom_client_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-clients"
        )
        response, result = self._session.exec(
            "POST", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 201:
            raise errors.Error.from_response(response)

        return result

    def update_custom_client(
        self,
        params: models.UpdateCustomClientRequest,
    ) -> dict[str, Any]:
        """Update a custom client.

        https://techdocs.akamai.com/bot-manager/reference/put-custom-client
        """
        logger.debug("UpdateCustomClient")
        _check_validation(validation.validate_update_custom_client_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-clients/{params.custom_client_id}"
        )
        response, result = self._session.exec(
            "PUT", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def remove_custom_client(
        self,
        params: models.RemoveCustomClientRequest,
    ) -> None:
        """Remove a custom client.

        https://techdocs.akamai.com/bot-manager/reference/delete-custom-client
        """
        logger.debug("RemoveCustomClient")
        _check_validation(validation.validate_remove_custom_client_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-clients/{params.custom_client_id}"
        )
        response, _ = self._session.exec(
            "DELETE", path,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 204:
            raise errors.Error.from_response(response)

    # ------------------------------------------------------------------ #
    # CustomClientSequence
    # ------------------------------------------------------------------ #

    def get_custom_client_sequence(
        self,
        params: models.GetCustomClientSequenceRequest,
    ) -> models.CustomClientSequenceResponse:
        """Retrieve custom client sequence.

        https://techdocs.akamai.com/bot-manager/reference/get-custom-client-sequence
        """
        logger.debug("GetCustomClientSequence")
        _check_validation(validation.validate_get_custom_client_sequence_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-client-sequence"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return models.CustomClientSequenceResponse(
            sequence=result.get("sequence", []),
            validation=result.get("validation"),
        )

    def update_custom_client_sequence(
        self,
        params: models.UpdateCustomClientSequenceRequest,
    ) -> models.CustomClientSequenceResponse:
        """Update custom client sequence.

        https://techdocs.akamai.com/bot-manager/reference/put-custom-client-sequence
        """
        logger.debug("UpdateCustomClientSequence")
        _check_validation(validation.validate_update_custom_client_sequence_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-client-sequence"
        )
        body = {"sequence": params.sequence}
        response, result = self._session.exec(
            "PUT", path, body=body, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return models.CustomClientSequenceResponse(
            sequence=result.get("sequence", []),
            validation=result.get("validation"),
        )

    # ------------------------------------------------------------------ #
    # CustomCode
    # ------------------------------------------------------------------ #

    def get_custom_code(
        self,
        params: models.GetCustomCodeRequest,
    ) -> dict[str, Any]:
        """Retrieve custom code settings.

        https://techdocs.akamai.com/bot-manager/reference/get-custom-code
        """
        logger.debug("GetCustomCode")
        _check_validation(validation.validate_get_custom_code_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/advanced-settings/transactional-endpoint-protection/custom-code"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def update_custom_code(
        self,
        params: models.UpdateCustomCodeRequest,
    ) -> dict[str, Any]:
        """Update custom code settings.

        Accepts HTTP status 200, 201, or 204 as success.

        https://techdocs.akamai.com/bot-manager/reference/put-custom-code
        """
        logger.debug("UpdateCustomCode")
        _check_validation(validation.validate_update_custom_code_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/advanced-settings/transactional-endpoint-protection/custom-code"
        )
        response, result = self._session.exec(
            "PUT", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code not in (200, 201, 204):
            raise errors.Error.from_response(response)

        return result

    # ------------------------------------------------------------------ #
    # CustomDefinedBot
    # ------------------------------------------------------------------ #

    def get_custom_defined_bot(
        self,
        params: models.GetCustomDefinedBotRequest,
    ) -> dict[str, Any]:
        """Retrieve a specific custom defined bot.

        https://techdocs.akamai.com/bot-manager/reference/get-custom-defined-bot
        """
        logger.debug("GetCustomDefinedBot")
        _check_validation(validation.validate_get_custom_defined_bot_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-defined-bots/{params.bot_id}"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def get_custom_defined_bot_list(
        self,
        params: models.GetCustomDefinedBotListRequest,
    ) -> models.GetCustomDefinedBotListResponse:
        """Retrieve custom defined bots for a configuration.

        https://techdocs.akamai.com/bot-manager/reference/get-custom-defined-bots
        """
        logger.debug("GetCustomDefinedBotList")
        _check_validation(validation.validate_get_custom_defined_bot_list_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-defined-bots"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        bots = result.get("bots", [])
        if params.bot_id:
            bots = [b for b in bots if b.get("botId") == params.bot_id]

        return models.GetCustomDefinedBotListResponse(bots=bots)

    def create_custom_defined_bot(
        self,
        params: models.CreateCustomDefinedBotRequest,
    ) -> dict[str, Any]:
        """Create a custom defined bot.

        https://techdocs.akamai.com/bot-manager/reference/post-custom-defined-bot
        """
        logger.debug("CreateCustomDefinedBot")
        _check_validation(validation.validate_create_custom_defined_bot_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-defined-bots"
        )
        response, result = self._session.exec(
            "POST", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 201:
            raise errors.Error.from_response(response)

        return result

    def update_custom_defined_bot(
        self,
        params: models.UpdateCustomDefinedBotRequest,
    ) -> dict[str, Any]:
        """Update a custom defined bot.

        https://techdocs.akamai.com/bot-manager/reference/put-custom-defined-bot
        """
        logger.debug("UpdateCustomDefinedBot")
        _check_validation(validation.validate_update_custom_defined_bot_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-defined-bots/{params.bot_id}"
        )
        response, result = self._session.exec(
            "PUT", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def remove_custom_defined_bot(
        self,
        params: models.RemoveCustomDefinedBotRequest,
    ) -> None:
        """Remove a custom defined bot.

        https://techdocs.akamai.com/bot-manager/reference/delete-custom-defined-bot
        """
        logger.debug("RemoveCustomDefinedBot")
        _check_validation(validation.validate_remove_custom_defined_bot_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-defined-bots/{params.bot_id}"
        )
        response, _ = self._session.exec(
            "DELETE", path,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 204:
            raise errors.Error.from_response(response)

    # ------------------------------------------------------------------ #
    # CustomDenyAction
    # ------------------------------------------------------------------ #

    def get_custom_deny_action(
        self,
        params: models.GetCustomDenyActionRequest,
    ) -> dict[str, Any]:
        """Retrieve a specific custom deny action.

        https://techdocs.akamai.com/bot-manager/reference/get-custom-deny-action
        """
        logger.debug("GetCustomDenyAction")
        _check_validation(validation.validate_get_custom_deny_action_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-deny-actions/{params.action_id}"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def get_custom_deny_action_list(
        self,
        params: models.GetCustomDenyActionListRequest,
    ) -> models.GetCustomDenyActionListResponse:
        """Retrieve custom deny actions for a configuration.

        https://techdocs.akamai.com/bot-manager/reference/get-custom-deny-actions
        """
        logger.debug("GetCustomDenyActionList")
        _check_validation(validation.validate_get_custom_deny_action_list_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-deny-actions"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        actions = result.get("customDenyActions", [])
        if params.action_id:
            actions = [
                a for a in actions
                if a.get("actionId") == params.action_id
            ]

        return models.GetCustomDenyActionListResponse(
            custom_deny_actions=actions,
        )

    def create_custom_deny_action(
        self,
        params: models.CreateCustomDenyActionRequest,
    ) -> dict[str, Any]:
        """Create a custom deny action.

        https://techdocs.akamai.com/bot-manager/reference/post-custom-deny-action
        """
        logger.debug("CreateCustomDenyAction")
        _check_validation(validation.validate_create_custom_deny_action_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-deny-actions"
        )
        response, result = self._session.exec(
            "POST", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 201:
            raise errors.Error.from_response(response)

        return result

    def update_custom_deny_action(
        self,
        params: models.UpdateCustomDenyActionRequest,
    ) -> dict[str, Any]:
        """Update a custom deny action.

        https://techdocs.akamai.com/bot-manager/reference/put-custom-deny-action
        """
        logger.debug("UpdateCustomDenyAction")
        _check_validation(validation.validate_update_custom_deny_action_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-deny-actions/{params.action_id}"
        )
        response, result = self._session.exec(
            "PUT", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def remove_custom_deny_action(
        self,
        params: models.RemoveCustomDenyActionRequest,
    ) -> None:
        """Remove a custom deny action.

        https://techdocs.akamai.com/bot-manager/reference/delete-custom-deny-action
        """
        logger.debug("RemoveCustomDenyAction")
        _check_validation(validation.validate_remove_custom_deny_action_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/custom-deny-actions/{params.action_id}"
        )
        response, _ = self._session.exec(
            "DELETE", path,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 204:
            raise errors.Error.from_response(response)

    # ------------------------------------------------------------------ #
    # JavascriptInjection
    # ------------------------------------------------------------------ #

    def get_javascript_injection(
        self,
        params: models.GetJavascriptInjectionRequest,
    ) -> dict[str, Any]:
        """Retrieve javascript injection settings for a policy.

        https://techdocs.akamai.com/bot-manager/reference/get-javascript-injection
        """
        logger.debug("GetJavascriptInjection")
        _check_validation(validation.validate_get_javascript_injection_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/javascript-injection"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def update_javascript_injection(
        self,
        params: models.UpdateJavascriptInjectionRequest,
    ) -> dict[str, Any]:
        """Update javascript injection settings for a policy.

        https://techdocs.akamai.com/bot-manager/reference/put-javascript-injection
        """
        logger.debug("UpdateJavascriptInjection")
        _check_validation(validation.validate_update_javascript_injection_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/javascript-injection"
        )
        response, result = self._session.exec(
            "PUT", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    # ------------------------------------------------------------------ #
    # RecategorizedAkamaiDefinedBot
    # ------------------------------------------------------------------ #

    def get_recategorized_akamai_defined_bot(
        self,
        params: models.GetRecategorizedAkamaiDefinedBotRequest,
    ) -> models.RecategorizedAkamaiDefinedBotResponse:
        """Retrieve a specific recategorized Akamai-defined bot.

        https://techdocs.akamai.com/bot-manager/reference/get-recategorized-akamai-defined-bot
        """
        logger.debug("GetRecategorizedAkamaiDefinedBot")
        _check_validation(validation.validate_get_recategorized_akamai_defined_bot_request(
            params,
        ))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/recategorized-akamai-defined-bots/{params.bot_id}"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return models.RecategorizedAkamaiDefinedBotResponse(
            bot_id=result.get("botId", ""),
            category_id=result.get("customBotCategoryId", ""),
        )

    def get_recategorized_akamai_defined_bot_list(
        self,
        params: models.GetRecategorizedAkamaiDefinedBotListRequest,
    ) -> models.GetRecategorizedAkamaiDefinedBotListResponse:
        """Retrieve recategorized Akamai-defined bots for a configuration.

        https://techdocs.akamai.com/bot-manager/reference/get-recategorized-akamai-defined-bots
        """
        logger.debug("GetRecategorizedAkamaiDefinedBotList")
        _check_validation(validation.validate_get_recategorized_akamai_defined_bot_list_request(
            params,
        ))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/recategorized-akamai-defined-bots"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        raw_bots = result.get("recategorizedBots", [])
        bots = [
            models.RecategorizedAkamaiDefinedBotResponse(
                bot_id=b.get("botId", ""),
                category_id=b.get("customBotCategoryId", ""),
            )
            for b in raw_bots
        ]
        if params.bot_id:
            bots = [b for b in bots if b.bot_id == params.bot_id]

        return models.GetRecategorizedAkamaiDefinedBotListResponse(bots=bots)

    def create_recategorized_akamai_defined_bot(
        self,
        params: models.CreateRecategorizedAkamaiDefinedBotRequest,
    ) -> models.RecategorizedAkamaiDefinedBotResponse:
        """Create a recategorized Akamai-defined bot.

        https://techdocs.akamai.com/bot-manager/reference/post-recategorized-akamai-defined-bot
        """
        logger.debug("CreateRecategorizedAkamaiDefinedBot")
        _check_validation(validation.validate_create_recategorized_akamai_defined_bot_request(
            params,
        ))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/recategorized-akamai-defined-bots"
        )
        body = {
            "botId": params.bot_id,
            "customBotCategoryId": params.category_id,
        }
        response, result = self._session.exec(
            "POST", path, body=body, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 201:
            raise errors.Error.from_response(response)

        return models.RecategorizedAkamaiDefinedBotResponse(
            bot_id=result.get("botId", ""),
            category_id=result.get("customBotCategoryId", ""),
        )

    def update_recategorized_akamai_defined_bot(
        self,
        params: models.UpdateRecategorizedAkamaiDefinedBotRequest,
    ) -> models.RecategorizedAkamaiDefinedBotResponse:
        """Update a recategorized Akamai-defined bot.

        https://techdocs.akamai.com/bot-manager/reference/put-recategorized-akamai-defined-bot
        """
        logger.debug("UpdateRecategorizedAkamaiDefinedBot")
        _check_validation(validation.validate_update_recategorized_akamai_defined_bot_request(
            params,
        ))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/recategorized-akamai-defined-bots/{params.bot_id}"
        )
        body = {
            "botId": params.bot_id,
            "customBotCategoryId": params.category_id,
        }
        response, result = self._session.exec(
            "PUT", path, body=body, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return models.RecategorizedAkamaiDefinedBotResponse(
            bot_id=result.get("botId", ""),
            category_id=result.get("customBotCategoryId", ""),
        )

    def remove_recategorized_akamai_defined_bot(
        self,
        params: models.RemoveRecategorizedAkamaiDefinedBotRequest,
    ) -> None:
        """Remove a recategorized Akamai-defined bot.

        https://techdocs.akamai.com/bot-manager/reference/delete-recategorized-akamai-defined-bot
        """
        logger.debug("RemoveRecategorizedAkamaiDefinedBot")
        _check_validation(validation.validate_remove_recategorized_akamai_defined_bot_request(
            params,
        ))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/recategorized-akamai-defined-bots/{params.bot_id}"
        )
        response, _ = self._session.exec(
            "DELETE", path,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 204:
            raise errors.Error.from_response(response)

    # ------------------------------------------------------------------ #
    # ResponseAction
    # ------------------------------------------------------------------ #

    def get_response_action_list(
        self,
        params: models.GetResponseActionListRequest,
    ) -> models.GetResponseActionListResponse:
        """Retrieve response actions for a configuration.

        https://techdocs.akamai.com/bot-manager/reference/get-response-actions
        """
        logger.debug("GetResponseActionList")
        _check_validation(validation.validate_get_response_action_list_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/response-actions"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        actions = result.get("responseActions", [])
        if params.action_id:
            actions = [
                a for a in actions
                if a.get("actionId") == params.action_id
            ]

        return models.GetResponseActionListResponse(
            response_actions=actions,
        )

    # ------------------------------------------------------------------ #
    # ServeAlternateAction
    # ------------------------------------------------------------------ #

    def get_serve_alternate_action(
        self,
        params: models.GetServeAlternateActionRequest,
    ) -> dict[str, Any]:
        """Retrieve a specific serve-alternate action.

        https://techdocs.akamai.com/bot-manager/reference/get-serve-alternate-action
        """
        logger.debug("GetServeAlternateAction")
        _check_validation(validation.validate_get_serve_alternate_action_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/response-actions/serve-alternate-actions/{params.action_id}"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def get_serve_alternate_action_list(
        self,
        params: models.GetServeAlternateActionListRequest,
    ) -> models.GetServeAlternateActionListResponse:
        """Retrieve serve-alternate actions for a configuration.

        https://techdocs.akamai.com/bot-manager/reference/get-serve-alternate-actions
        """
        logger.debug("GetServeAlternateActionList")
        _check_validation(validation.validate_get_serve_alternate_action_list_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/response-actions/serve-alternate-actions"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        actions = result.get("serveAlternateActions", [])
        if params.action_id:
            actions = [
                a for a in actions
                if a.get("actionId") == params.action_id
            ]

        return models.GetServeAlternateActionListResponse(
            serve_alternate_actions=actions,
        )

    def create_serve_alternate_action(
        self,
        params: models.CreateServeAlternateActionRequest,
    ) -> dict[str, Any]:
        """Create a serve-alternate action.

        https://techdocs.akamai.com/bot-manager/reference/post-serve-alternate-action
        """
        logger.debug("CreateServeAlternateAction")
        _check_validation(validation.validate_create_serve_alternate_action_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/response-actions/serve-alternate-actions"
        )
        response, result = self._session.exec(
            "POST", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 201:
            raise errors.Error.from_response(response)

        return result

    def update_serve_alternate_action(
        self,
        params: models.UpdateServeAlternateActionRequest,
    ) -> dict[str, Any]:
        """Update a serve-alternate action.

        https://techdocs.akamai.com/bot-manager/reference/put-serve-alternate-action
        """
        logger.debug("UpdateServeAlternateAction")
        _check_validation(validation.validate_update_serve_alternate_action_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/response-actions/serve-alternate-actions/{params.action_id}"
        )
        response, result = self._session.exec(
            "PUT", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def remove_serve_alternate_action(
        self,
        params: models.RemoveServeAlternateActionRequest,
    ) -> None:
        """Remove a serve-alternate action.

        https://techdocs.akamai.com/bot-manager/reference/delete-serve-alternate-action
        """
        logger.debug("RemoveServeAlternateAction")
        _check_validation(validation.validate_remove_serve_alternate_action_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/response-actions/serve-alternate-actions/{params.action_id}"
        )
        response, _ = self._session.exec(
            "DELETE", path,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 204:
            raise errors.Error.from_response(response)

    # ------------------------------------------------------------------ #
    # TransactionalEndpoint
    # ------------------------------------------------------------------ #

    def get_transactional_endpoint(
        self,
        params: models.GetTransactionalEndpointRequest,
    ) -> dict[str, Any]:
        """Retrieve a specific transactional endpoint.

        https://techdocs.akamai.com/bot-manager/reference/get-transactional-endpoint
        """
        logger.debug("GetTransactionalEndpoint")
        _check_validation(validation.validate_get_transactional_endpoint_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/transactional-endpoints/{params.operation_id}"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def get_transactional_endpoint_list(
        self,
        params: models.GetTransactionalEndpointListRequest,
    ) -> models.GetTransactionalEndpointListResponse:
        """Retrieve transactional endpoints for a policy.

        https://techdocs.akamai.com/bot-manager/reference/get-transactional-endpoints
        """
        logger.debug("GetTransactionalEndpointList")
        _check_validation(validation.validate_get_transactional_endpoint_list_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/transactional-endpoints"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        operations = result.get("operations", [])
        if params.operation_id:
            operations = [
                o for o in operations
                if o.get("operationId") == params.operation_id
            ]

        return models.GetTransactionalEndpointListResponse(
            operations=operations,
        )

    def create_transactional_endpoint(
        self,
        params: models.CreateTransactionalEndpointRequest,
    ) -> dict[str, Any]:
        """Create a transactional endpoint.

        https://techdocs.akamai.com/bot-manager/reference/post-transactional-endpoint
        """
        logger.debug("CreateTransactionalEndpoint")
        _check_validation(validation.validate_create_transactional_endpoint_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/transactional-endpoints"
        )
        response, result = self._session.exec(
            "POST", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 201:
            raise errors.Error.from_response(response)

        return result

    def update_transactional_endpoint(
        self,
        params: models.UpdateTransactionalEndpointRequest,
    ) -> dict[str, Any]:
        """Update a transactional endpoint.

        https://techdocs.akamai.com/bot-manager/reference/put-transactional-endpoint
        """
        logger.debug("UpdateTransactionalEndpoint")
        _check_validation(validation.validate_update_transactional_endpoint_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/transactional-endpoints/{params.operation_id}"
        )
        response, result = self._session.exec(
            "PUT", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def remove_transactional_endpoint(
        self,
        params: models.RemoveTransactionalEndpointRequest,
    ) -> None:
        """Remove a transactional endpoint.

        https://techdocs.akamai.com/bot-manager/reference/delete-transactional-endpoint
        """
        logger.debug("RemoveTransactionalEndpoint")
        _check_validation(validation.validate_remove_transactional_endpoint_request(params))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/transactional-endpoints/{params.operation_id}"
        )
        response, _ = self._session.exec(
            "DELETE", path,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 204:
            raise errors.Error.from_response(response)

    # ------------------------------------------------------------------ #
    # TransactionalEndpointProtection
    # ------------------------------------------------------------------ #

    def get_transactional_endpoint_protection(
        self,
        params: models.GetTransactionalEndpointProtectionRequest,
    ) -> dict[str, Any]:
        """Retrieve transactional endpoint protection settings.

        https://techdocs.akamai.com/bot-manager/reference/get-transactional-endpoint-protection
        """
        logger.debug("GetTransactionalEndpointProtection")
        _check_validation(validation.validate_get_transactional_endpoint_protection_request(
            params,
        ))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/advanced-settings/transactional-endpoint-protection"
        )
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result

    def update_transactional_endpoint_protection(
        self,
        params: models.UpdateTransactionalEndpointProtectionRequest,
    ) -> dict[str, Any]:
        """Update transactional endpoint protection settings.

        https://techdocs.akamai.com/bot-manager/reference/put-transactional-endpoint-protection
        """
        logger.debug("UpdateTransactionalEndpointProtection")
        _check_validation(validation.validate_update_transactional_endpoint_protection_request(
            params,
        ))

        path = (
            f"/appsec/v1/configs/{params.config_id}/versions/{params.version}"
            f"/advanced-settings/transactional-endpoint-protection"
        )
        response, result = self._session.exec(
            "PUT", path, body=params.json_payload, expect_json=True,
            error_parser=errors.Error.from_response,
        )
        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return result
