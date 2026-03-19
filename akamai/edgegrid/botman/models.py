"""Request and response model classes for the Bot Manager API client.

Each Go struct from the AkamaiOPEN-edgegrid-golang/pkg/botman package maps to a
Python dataclass with fields matching Go struct field names (snake_case
equivalents of Go PascalCase), types mapped per Go-to-Python type mapping, and
default values matching Go zero values.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Shared / base types (validation_response.go, sequences)

@dataclass
class ValidationDetail:
    """Validation detail entry used in bot manager API responses."""
    title: str = ""
    type: str = ""
    detail: str = ""

@dataclass
class ValidationResponse:
    """Validation member embedded in certain bot manager API responses."""
    errors: list[ValidationDetail] = field(default_factory=list)
    notices: list[ValidationDetail] = field(default_factory=list)
    warnings: list[ValidationDetail] = field(default_factory=list)

@dataclass
class UUIDSequence:
    """Generic ordered sequence of UUIDs (reusable across endpoints)."""
    sequence: list[str] = field(default_factory=list)

@dataclass
class ContentProtectionRuleUUIDSequence:
    """Ordered sequence of content protection rule UUIDs."""
    content_protection_rule_sequence: list[str] = field(default_factory=list)

@dataclass
class RecategorizedAkamaiDefinedBotResponse:
    """Typed response for a recategorized Akamai-defined bot."""
    bot_id: str = ""
    category_id: str = ""

@dataclass
class CustomBotCategorySequenceResponse:
    """Response containing the custom bot category sequence."""
    sequence: list[str] = field(default_factory=list)

@dataclass
class CustomClientSequenceResponse:
    """Response containing the custom client sequence with validation info."""
    sequence: list[str] = field(default_factory=list)
    validation: ValidationResponse = field(default_factory=ValidationResponse)


# AkamaiBotCategory models (akamai_bot_category.go)

@dataclass
class GetAkamaiBotCategoryListRequest:
    """Request for retrieving the Akamai bot category list."""
    category_name: str = ""

@dataclass
class GetAkamaiBotCategoryListResponse:
    """Response containing Akamai bot categories."""
    categories: list[dict[str, Any]] = field(default_factory=list)


# AkamaiBotCategoryAction models (akamai_bot_category_action.go)

@dataclass
class GetAkamaiBotCategoryActionListRequest:
    """Request for retrieving Akamai bot category action list."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    category_id: str = ""

@dataclass
class GetAkamaiBotCategoryActionListResponse:
    """Response containing Akamai bot category actions."""
    akamai_bot_category_actions: list[dict[str, Any]] = field(
        default_factory=list
    )

@dataclass
class GetAkamaiBotCategoryActionRequest:
    """Request for retrieving a specific Akamai bot category action."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    category_id: str = ""

@dataclass
class UpdateAkamaiBotCategoryActionRequest:
    """Request for updating an Akamai bot category action."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    category_id: str = ""
    json_payload: Any = None


# AkamaiDefinedBot models (akamai_defined_bot.go)

@dataclass
class GetAkamaiDefinedBotListRequest:
    """Request for retrieving the Akamai-defined bot list."""
    bot_name: str = ""

@dataclass
class GetAkamaiDefinedBotListResponse:
    """Response containing Akamai-defined bots."""
    bots: list[dict[str, Any]] = field(default_factory=list)


# BotAnalyticsCookie models (bot_analytics_cookie.go)

@dataclass
class GetBotAnalyticsCookieRequest:
    """Request for retrieving bot analytics cookie settings."""
    config_id: int = 0
    version: int = 0

@dataclass
class UpdateBotAnalyticsCookieRequest:
    """Request for updating bot analytics cookie settings."""
    config_id: int = 0
    version: int = 0
    json_payload: Any = None


# BotCategoryException models (bot_category_exception.go)

@dataclass
class GetBotCategoryExceptionRequest:
    """Request for retrieving bot category exception settings."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""

@dataclass
class UpdateBotCategoryExceptionRequest:
    """Request for updating bot category exception settings."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    json_payload: Any = None


# BotDetection models (bot_detection.go)

@dataclass
class GetBotDetectionListRequest:
    """Request for retrieving the bot detection list."""
    detection_name: str = ""

@dataclass
class GetBotDetectionListResponse:
    """Response containing bot detections."""
    detections: list[dict[str, Any]] = field(default_factory=list)


# BotDetectionAction models (bot_detection_action.go)

@dataclass
class GetBotDetectionActionListRequest:
    """Request for retrieving bot detection action list."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    detection_id: str = ""

@dataclass
class GetBotDetectionActionListResponse:
    """Response containing bot detection actions."""
    bot_detection_actions: list[dict[str, Any]] = field(default_factory=list)

@dataclass
class GetBotDetectionActionRequest:
    """Request for retrieving a specific bot detection action."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    detection_id: str = ""

@dataclass
class UpdateBotDetectionActionRequest:
    """Request for updating a bot detection action."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    detection_id: str = ""
    json_payload: Any = None


# BotEndpointCoverageReport models (bot_endpoint_coverage_report.go)

@dataclass
class GetBotEndpointCoverageReportRequest:
    """Request for retrieving the bot endpoint coverage report."""
    config_id: int = 0
    version: int = 0
    operation_id: str = ""

@dataclass
class GetBotEndpointCoverageReportResponse:
    """Response containing bot endpoint coverage report operations."""
    operations: list[dict[str, Any]] = field(default_factory=list)


# BotManagementSetting models (bot_management_setting.go)

@dataclass
class GetBotManagementSettingRequest:
    """Request for retrieving bot management settings."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""

@dataclass
class UpdateBotManagementSettingRequest:
    """Request for updating bot management settings."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    json_payload: Any = None


# ChallengeAction models (challenge_action.go)

@dataclass
class GetChallengeActionListRequest:
    """Request for retrieving challenge actions for a configuration."""
    config_id: int = 0
    version: int = 0
    action_id: str = ""

@dataclass
class GetChallengeActionListResponse:
    """Response containing challenge actions."""
    challenge_actions: list[dict[str, Any]] = field(default_factory=list)

@dataclass
class GetChallengeActionRequest:
    """Request for retrieving a specific challenge action."""
    config_id: int = 0
    version: int = 0
    action_id: str = ""

@dataclass
class CreateChallengeActionRequest:
    """Request for creating a new challenge action."""
    config_id: int = 0
    version: int = 0
    json_payload: Any = None

@dataclass
class UpdateChallengeActionRequest:
    """Request for updating an existing challenge action."""
    config_id: int = 0
    version: int = 0
    action_id: str = ""
    json_payload: Any = None

@dataclass
class RemoveChallengeActionRequest:
    """Request for removing a challenge action."""
    config_id: int = 0
    version: int = 0
    action_id: str = ""

@dataclass
class UpdateGoogleReCaptchaSecretKeyRequest:
    """Request for updating Google reCAPTCHA secret key for a challenge action."""
    config_id: int = 0
    version: int = 0
    action_id: str = ""
    secret_key: str = ""


# ChallengeInjectionRules models (challenge_injection_rules.go)

@dataclass
class GetChallengeInjectionRulesRequest:
    """Request for retrieving challenge injection rules."""
    config_id: int = 0
    version: int = 0

@dataclass
class UpdateChallengeInjectionRulesRequest:
    """Request for updating challenge injection rules."""
    config_id: int = 0
    version: int = 0
    json_payload: Any = None


# ClientSideSecurity models (client_side_security.go)

@dataclass
class GetClientSideSecurityRequest:
    """Request for retrieving client-side security settings."""
    config_id: int = 0
    version: int = 0

@dataclass
class UpdateClientSideSecurityRequest:
    """Request for updating client-side security settings."""
    config_id: int = 0
    version: int = 0
    json_payload: Any = None


# ConditionalAction models (conditional_action.go)

@dataclass
class GetConditionalActionListRequest:
    """Request for retrieving conditional actions for a configuration."""
    config_id: int = 0
    version: int = 0
    action_id: str = ""

@dataclass
class GetConditionalActionListResponse:
    """Response containing conditional actions."""
    conditional_actions: list[dict[str, Any]] = field(default_factory=list)

@dataclass
class GetConditionalActionRequest:
    """Request for retrieving a specific conditional action."""
    config_id: int = 0
    version: int = 0
    action_id: str = ""

@dataclass
class CreateConditionalActionRequest:
    """Request for creating a new conditional action."""
    config_id: int = 0
    version: int = 0
    json_payload: Any = None

@dataclass
class UpdateConditionalActionRequest:
    """Request for updating an existing conditional action."""
    config_id: int = 0
    version: int = 0
    action_id: str = ""
    json_payload: Any = None

@dataclass
class RemoveConditionalActionRequest:
    """Request for removing a conditional action."""
    config_id: int = 0
    version: int = 0
    action_id: str = ""


# ============================================================
# ContentProtectionJavaScriptInjectionRule models
# (content_protection_javascript_injection_rule.go)
# ============================================================

@dataclass
class GetContentProtectionJavaScriptInjectionRuleListRequest:
    """Request for retrieving content protection JS injection rules."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    content_protection_javascript_injection_rule_id: str = ""

@dataclass
class GetContentProtectionJavaScriptInjectionRuleListResponse:
    """Response containing content protection JS injection rules."""
    content_protection_javascript_injection_rules: list[dict[str, Any]] = (
        field(default_factory=list)
    )

@dataclass
class GetContentProtectionJavaScriptInjectionRuleRequest:
    """Request for retrieving a specific content protection JS injection rule."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    content_protection_javascript_injection_rule_id: str = ""

@dataclass
class CreateContentProtectionJavaScriptInjectionRuleRequest:
    """Request for creating a content protection JS injection rule."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    json_payload: Any = None

@dataclass
class UpdateContentProtectionJavaScriptInjectionRuleRequest:
    """Request for updating a content protection JS injection rule."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    content_protection_javascript_injection_rule_id: str = ""
    json_payload: Any = None

@dataclass
class RemoveContentProtectionJavaScriptInjectionRuleRequest:
    """Request for removing a content protection JS injection rule."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    content_protection_javascript_injection_rule_id: str = ""


# ContentProtectionRule models (content_protection_rule.go)

@dataclass
class GetContentProtectionRuleListRequest:
    """Request for retrieving content protection rules for a policy."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    content_protection_rule_id: str = ""

@dataclass
class GetContentProtectionRuleListResponse:
    """Response containing content protection rules."""
    content_protection_rules: list[dict[str, Any]] = field(
        default_factory=list
    )

@dataclass
class GetContentProtectionRuleRequest:
    """Request for retrieving a specific content protection rule."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    content_protection_rule_id: str = ""

@dataclass
class CreateContentProtectionRuleRequest:
    """Request for creating a new content protection rule."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    json_payload: Any = None

@dataclass
class UpdateContentProtectionRuleRequest:
    """Request for updating a content protection rule."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    content_protection_rule_id: str = ""
    json_payload: Any = None

@dataclass
class RemoveContentProtectionRuleRequest:
    """Request for removing a content protection rule."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    content_protection_rule_id: str = ""


# ============================================================
# ContentProtectionRuleSequence models
# (content_protection_rule_sequence.go)
# ============================================================

@dataclass
class GetContentProtectionRuleSequenceRequest:
    """Request for retrieving content protection rule sequence."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""

@dataclass
class GetContentProtectionRuleSequenceResponse:
    """Response containing the content protection rule sequence."""
    content_protection_rule_sequence: list[str] = field(default_factory=list)

@dataclass
class UpdateContentProtectionRuleSequenceRequest:
    """Request for updating the content protection rule sequence."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    content_protection_rule_sequence: list[str] = field(default_factory=list)

@dataclass
class UpdateContentProtectionRuleSequenceResponse:
    """Response containing the updated content protection rule sequence."""
    content_protection_rule_sequence: list[str] = field(default_factory=list)


# CustomBotCategory models (custom_bot_category.go)

@dataclass
class GetCustomBotCategoryListRequest:
    """Request for retrieving custom bot categories for a configuration."""
    config_id: int = 0
    version: int = 0
    category_id: str = ""

@dataclass
class GetCustomBotCategoryListResponse:
    """Response containing custom bot categories."""
    categories: list[dict[str, Any]] = field(default_factory=list)

@dataclass
class GetCustomBotCategoryRequest:
    """Request for retrieving a specific custom bot category."""
    config_id: int = 0
    version: int = 0
    category_id: str = ""

@dataclass
class CreateCustomBotCategoryRequest:
    """Request for creating a new custom bot category."""
    config_id: int = 0
    version: int = 0
    json_payload: Any = None

@dataclass
class UpdateCustomBotCategoryRequest:
    """Request for updating an existing custom bot category."""
    config_id: int = 0
    version: int = 0
    category_id: str = ""
    json_payload: Any = None

@dataclass
class RemoveCustomBotCategoryRequest:
    """Request for removing a custom bot category."""
    config_id: int = 0
    version: int = 0
    category_id: str = ""


# CustomBotCategoryAction models (custom_bot_category_action.go)

@dataclass
class GetCustomBotCategoryActionListRequest:
    """Request for retrieving custom bot category actions for a policy."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    category_id: str = ""

@dataclass
class GetCustomBotCategoryActionListResponse:
    """Response containing custom bot category actions."""
    actions: list[dict[str, Any]] = field(default_factory=list)

@dataclass
class GetCustomBotCategoryActionRequest:
    """Request for retrieving a specific custom bot category action."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    category_id: str = ""

@dataclass
class UpdateCustomBotCategoryActionRequest:
    """Request for updating a custom bot category action."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    category_id: str = ""
    json_payload: Any = None


# ============================================================
# CustomBotCategoryItemSequence models
# (custom_bot_category_item_sequence.go)
# ============================================================

@dataclass
class GetCustomBotCategoryItemSequenceRequest:
    """Request for retrieving custom bot category item sequence."""
    config_id: int = 0
    version: int = 0
    category_id: str = ""

@dataclass
class GetCustomBotCategoryItemSequenceResponse:
    """Response containing the custom bot category item sequence."""
    sequence: list[str] = field(default_factory=list)

@dataclass
class UpdateCustomBotCategoryItemSequenceRequest:
    """Request for updating the custom bot category item sequence."""
    config_id: int = 0
    version: int = 0
    category_id: str = ""
    sequence: list[str] = field(default_factory=list)

@dataclass
class UpdateCustomBotCategoryItemSequenceResponse:
    """Response containing the updated custom bot category item sequence."""
    sequence: list[str] = field(default_factory=list)


# ============================================================
# CustomBotCategorySequence models
# (custom_bot_category_sequence.go)
# ============================================================

@dataclass
class GetCustomBotCategorySequenceRequest:
    """Request for retrieving the custom bot category sequence."""
    config_id: int = 0
    version: int = 0

@dataclass
class UpdateCustomBotCategorySequenceRequest:
    """Request for updating the custom bot category sequence."""
    config_id: int = 0
    version: int = 0
    sequence: list[str] = field(default_factory=list)


# CustomClient models (custom_client.go)

@dataclass
class GetCustomClientListRequest:
    """Request for retrieving custom clients for a configuration."""
    config_id: int = 0
    version: int = 0
    custom_client_id: str = ""

@dataclass
class GetCustomClientListResponse:
    """Response containing custom clients."""
    custom_clients: list[dict[str, Any]] = field(default_factory=list)

@dataclass
class GetCustomClientRequest:
    """Request for retrieving a specific custom client."""
    config_id: int = 0
    version: int = 0
    custom_client_id: str = ""

@dataclass
class CreateCustomClientRequest:
    """Request for creating a new custom client."""
    config_id: int = 0
    version: int = 0
    json_payload: Any = None

@dataclass
class UpdateCustomClientRequest:
    """Request for updating an existing custom client."""
    config_id: int = 0
    version: int = 0
    custom_client_id: str = ""
    json_payload: Any = None

@dataclass
class RemoveCustomClientRequest:
    """Request for removing a custom client."""
    config_id: int = 0
    version: int = 0
    custom_client_id: str = ""


# CustomClientSequence models (custom_client_sequence.go)

@dataclass
class GetCustomClientSequenceRequest:
    """Request for retrieving the custom client sequence."""
    config_id: int = 0
    version: int = 0

@dataclass
class UpdateCustomClientSequenceRequest:
    """Request for updating the custom client sequence."""
    config_id: int = 0
    version: int = 0
    sequence: list[str] = field(default_factory=list)


# CustomCode models (custom_code.go)

@dataclass
class GetCustomCodeRequest:
    """Request for retrieving custom code for a configuration."""
    config_id: int = 0
    version: int = 0

@dataclass
class UpdateCustomCodeRequest:
    """Request for updating custom code for a configuration."""
    config_id: int = 0
    version: int = 0
    json_payload: Any = None


# CustomDefinedBot models (custom_defined_bot.go)

@dataclass
class GetCustomDefinedBotListRequest:
    """Request for retrieving custom-defined bots for a configuration."""
    config_id: int = 0
    version: int = 0
    bot_id: str = ""

@dataclass
class GetCustomDefinedBotListResponse:
    """Response containing custom-defined bots."""
    bots: list[dict[str, Any]] = field(default_factory=list)

@dataclass
class GetCustomDefinedBotRequest:
    """Request for retrieving a specific custom-defined bot."""
    config_id: int = 0
    version: int = 0
    bot_id: str = ""

@dataclass
class CreateCustomDefinedBotRequest:
    """Request for creating a new custom-defined bot."""
    config_id: int = 0
    version: int = 0
    json_payload: Any = None

@dataclass
class UpdateCustomDefinedBotRequest:
    """Request for updating a custom-defined bot."""
    config_id: int = 0
    version: int = 0
    bot_id: str = ""
    json_payload: Any = None

@dataclass
class RemoveCustomDefinedBotRequest:
    """Request for removing a custom-defined bot."""
    config_id: int = 0
    version: int = 0
    bot_id: str = ""


# CustomDenyAction models (custom_deny_action.go)

@dataclass
class GetCustomDenyActionListRequest:
    """Request for retrieving custom deny actions for a configuration."""
    config_id: int = 0
    version: int = 0
    action_id: str = ""

@dataclass
class GetCustomDenyActionListResponse:
    """Response containing custom deny actions."""
    custom_deny_actions: list[dict[str, Any]] = field(default_factory=list)

@dataclass
class GetCustomDenyActionRequest:
    """Request for retrieving a specific custom deny action."""
    config_id: int = 0
    version: int = 0
    action_id: str = ""

@dataclass
class CreateCustomDenyActionRequest:
    """Request for creating a new custom deny action."""
    config_id: int = 0
    version: int = 0
    json_payload: Any = None

@dataclass
class UpdateCustomDenyActionRequest:
    """Request for updating a custom deny action."""
    config_id: int = 0
    version: int = 0
    action_id: str = ""
    json_payload: Any = None

@dataclass
class RemoveCustomDenyActionRequest:
    """Request for removing a custom deny action."""
    config_id: int = 0
    version: int = 0
    action_id: str = ""


# JavascriptInjection models (javascript_injection.go)

@dataclass
class GetJavascriptInjectionRequest:
    """Request for retrieving javascript injection settings."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""

@dataclass
class UpdateJavascriptInjectionRequest:
    """Request for updating javascript injection settings."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    json_payload: Any = None


# ============================================================
# RecategorizedAkamaiDefinedBot models
# (recategorized_akamai_defined_bot.go)
# ============================================================

@dataclass
class GetRecategorizedAkamaiDefinedBotListRequest:
    """Request for retrieving recategorized Akamai-defined bots."""
    config_id: int = 0
    version: int = 0
    bot_id: str = ""

@dataclass
class GetRecategorizedAkamaiDefinedBotListResponse:
    """Response containing recategorized Akamai-defined bots."""
    bots: list[RecategorizedAkamaiDefinedBotResponse] = field(
        default_factory=list
    )

@dataclass
class GetRecategorizedAkamaiDefinedBotRequest:
    """Request for retrieving a specific recategorized Akamai-defined bot."""
    config_id: int = 0
    version: int = 0
    bot_id: str = ""

@dataclass
class CreateRecategorizedAkamaiDefinedBotRequest:
    """Request for creating a recategorized Akamai-defined bot."""
    config_id: int = 0
    version: int = 0
    bot_id: str = ""
    category_id: str = ""

@dataclass
class UpdateRecategorizedAkamaiDefinedBotRequest:
    """Request for updating a recategorized Akamai-defined bot."""
    config_id: int = 0
    version: int = 0
    bot_id: str = ""
    category_id: str = ""

@dataclass
class RemoveRecategorizedAkamaiDefinedBotRequest:
    """Request for removing a recategorized Akamai-defined bot."""
    config_id: int = 0
    version: int = 0
    bot_id: str = ""


# ResponseAction models (response_action.go)

@dataclass
class GetResponseActionListRequest:
    """Request for retrieving response actions for a configuration."""
    config_id: int = 0
    version: int = 0
    action_id: str = ""

@dataclass
class GetResponseActionListResponse:
    """Response containing response actions."""
    response_actions: list[dict[str, Any]] = field(default_factory=list)


# ServeAlternateAction models (serve_alternate_action.go)

@dataclass
class GetServeAlternateActionListRequest:
    """Request for retrieving serve-alternate actions."""
    config_id: int = 0
    version: int = 0
    action_id: str = ""

@dataclass
class GetServeAlternateActionListResponse:
    """Response containing serve-alternate actions."""
    serve_alternate_actions: list[dict[str, Any]] = field(
        default_factory=list
    )

@dataclass
class GetServeAlternateActionRequest:
    """Request for retrieving a specific serve-alternate action."""
    config_id: int = 0
    version: int = 0
    action_id: str = ""

@dataclass
class CreateServeAlternateActionRequest:
    """Request for creating a new serve-alternate action."""
    config_id: int = 0
    version: int = 0
    json_payload: Any = None

@dataclass
class UpdateServeAlternateActionRequest:
    """Request for updating a serve-alternate action."""
    config_id: int = 0
    version: int = 0
    action_id: str = ""
    json_payload: Any = None

@dataclass
class RemoveServeAlternateActionRequest:
    """Request for removing a serve-alternate action."""
    config_id: int = 0
    version: int = 0
    action_id: str = ""


# TransactionalEndpoint models (transactional_endpoint.go)

@dataclass
class GetTransactionalEndpointListRequest:
    """Request for retrieving transactional endpoints."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    operation_id: str = ""

@dataclass
class GetTransactionalEndpointListResponse:
    """Response containing transactional endpoints."""
    operations: list[dict[str, Any]] = field(default_factory=list)

@dataclass
class GetTransactionalEndpointRequest:
    """Request for retrieving a specific transactional endpoint."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    operation_id: str = ""

@dataclass
class CreateTransactionalEndpointRequest:
    """Request for creating a new transactional endpoint."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    json_payload: Any = None

@dataclass
class UpdateTransactionalEndpointRequest:
    """Request for updating a transactional endpoint."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    operation_id: str = ""
    json_payload: Any = None

@dataclass
class RemoveTransactionalEndpointRequest:
    """Request for removing a transactional endpoint."""
    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    operation_id: str = ""


# ============================================================
# TransactionalEndpointProtection models
# (transactional_endpoint_protection.go)
# ============================================================

@dataclass
class GetTransactionalEndpointProtectionRequest:
    """Request for retrieving transactional endpoint protection settings."""
    config_id: int = 0
    version: int = 0

@dataclass
class UpdateTransactionalEndpointProtectionRequest:
    """Request for updating transactional endpoint protection settings."""
    config_id: int = 0
    version: int = 0
    json_payload: Any = None
