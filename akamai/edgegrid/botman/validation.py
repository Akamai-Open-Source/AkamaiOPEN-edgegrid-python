"""Request validation functions for the Bot Manager API client.

Each function validates the parameters for a specific Bot Manager API request,
mirroring the Go SDK's ozzo-validation Validate() methods. On validation failure,
ErrStructValidation is raised with a formatted error message.
"""

from akamai.edgegrid.botman.errors import ErrStructValidation
from akamai.edgegrid.validation import parse_validation_errors


def _validate_required(value) -> str | None:
    """Check if a value is required and non-empty.

    Mirrors Go's ozzo-validation Required rule:
    - None is considered empty
    - 0 for int/float is considered empty
    - Empty string is considered empty
    - Empty bytes/bytearray is considered empty
    - Empty list/tuple/dict is considered empty
    """
    if value is None:
        return "cannot be blank"
    if isinstance(value, (int, float)) and value == 0:
        return "cannot be blank"
    if isinstance(value, str) and value == "":
        return "cannot be blank"
    if isinstance(value, (bytes, bytearray)) and len(value) == 0:
        return "cannot be blank"
    if isinstance(value, (list, tuple, dict)) and len(value) == 0:
        return "cannot be blank"
    return None


def _run_validation(errors: dict[str, str | None]) -> None:
    """Run validation and raise ErrStructValidation on failure.

    Filters out None values from the errors dict, then formats remaining
    errors using parse_validation_errors and raises ErrStructValidation.
    Mirrors Go's validation.Errors{...}.Filter() followed by
    fmt.Errorf('%w: %%s', ErrStructValidation, err.Error()).
    """
    filtered = {k: v for k, v in errors.items() if v is not None}
    if filtered:
        error_msg = parse_validation_errors(filtered)
        raise ErrStructValidation(
            f"struct validation: {error_msg}"
        )


# ---------------------------------------------------------------------------
# AkamaiBotCategoryAction validations
# ---------------------------------------------------------------------------


def validate_get_akamai_bot_category_action_request(params):
    """Validate GetAkamaiBotCategoryActionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "CategoryID": _validate_required(params.category_id),
    })


def validate_get_akamai_bot_category_action_list_request(params):
    """Validate GetAkamaiBotCategoryActionListRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
    })


def validate_update_akamai_bot_category_action_request(params):
    """Validate UpdateAkamaiBotCategoryActionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "CategoryID": _validate_required(params.category_id),
        "JsonPayload": _validate_required(params.json_payload),
    })


# ---------------------------------------------------------------------------
# BotAnalyticsCookie validations
# ---------------------------------------------------------------------------


def validate_get_bot_analytics_cookie_request(params):
    """Validate GetBotAnalyticsCookieRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
    })


def validate_update_bot_analytics_cookie_request(params):
    """Validate UpdateBotAnalyticsCookieRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "JsonPayload": _validate_required(params.json_payload),
    })


# ---------------------------------------------------------------------------
# BotCategoryException validations
# ---------------------------------------------------------------------------


def validate_get_bot_category_exception_request(params):
    """Validate GetBotCategoryExceptionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
    })


def validate_update_bot_category_exception_request(params):
    """Validate UpdateBotCategoryExceptionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "JsonPayload": _validate_required(params.json_payload),
    })


# ---------------------------------------------------------------------------
# BotDetectionAction validations
# ---------------------------------------------------------------------------


def validate_get_bot_detection_action_request(params):
    """Validate GetBotDetectionActionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "DetectionID": _validate_required(params.detection_id),
    })


def validate_get_bot_detection_action_list_request(params):
    """Validate GetBotDetectionActionListRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
    })


def validate_update_bot_detection_action_request(params):
    """Validate UpdateBotDetectionActionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "DetectionID": _validate_required(params.detection_id),
        "JsonPayload": _validate_required(params.json_payload),
    })


# ---------------------------------------------------------------------------
# BotEndpointCoverageReport validations (CONDITIONAL)
# ---------------------------------------------------------------------------


def validate_get_bot_endpoint_coverage_report_request(params):
    """Validate GetBotEndpointCoverageReportRequest parameters.

    Uses conditional validation: ConfigID is required only when Version
    is non-zero, and Version is required only when ConfigID is non-zero.
    Mirrors Go's validation.When() pattern.
    """
    errors = {}
    if params.version:
        errors["ConfigID"] = _validate_required(params.config_id)
    if params.config_id:
        errors["Version"] = _validate_required(params.version)
    _run_validation(errors)


# ---------------------------------------------------------------------------
# BotManagementSetting validations
# ---------------------------------------------------------------------------


def validate_get_bot_management_setting_request(params):
    """Validate GetBotManagementSettingRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
    })


def validate_update_bot_management_setting_request(params):
    """Validate UpdateBotManagementSettingRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "JsonPayload": _validate_required(params.json_payload),
    })


# ---------------------------------------------------------------------------
# ChallengeAction validations
# ---------------------------------------------------------------------------


def validate_get_challenge_action_request(params):
    """Validate GetChallengeActionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "ActionID": _validate_required(params.action_id),
    })


def validate_get_challenge_action_list_request(params):
    """Validate GetChallengeActionListRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
    })


def validate_create_challenge_action_request(params):
    """Validate CreateChallengeActionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "JsonPayload": _validate_required(params.json_payload),
    })


def validate_update_challenge_action_request(params):
    """Validate UpdateChallengeActionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "ActionID": _validate_required(params.action_id),
        "JsonPayload": _validate_required(params.json_payload),
    })


def validate_remove_challenge_action_request(params):
    """Validate RemoveChallengeActionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "ActionID": _validate_required(params.action_id),
    })


def validate_update_google_recaptcha_secret_key_request(params):
    """Validate UpdateGoogleReCaptchaSecretKeyRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "ActionID": _validate_required(params.action_id),
        "SecretKey": _validate_required(params.secret_key),
    })


# ---------------------------------------------------------------------------
# ChallengeInjectionRules validations
# ---------------------------------------------------------------------------


def validate_get_challenge_injection_rules_request(params):
    """Validate GetChallengeInjectionRulesRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
    })


def validate_update_challenge_injection_rules_request(params):
    """Validate UpdateChallengeInjectionRulesRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "JsonPayload": _validate_required(params.json_payload),
    })


# ---------------------------------------------------------------------------
# ClientSideSecurity validations
# ---------------------------------------------------------------------------


def validate_get_client_side_security_request(params):
    """Validate GetClientSideSecurityRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
    })


def validate_update_client_side_security_request(params):
    """Validate UpdateClientSideSecurityRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "JsonPayload": _validate_required(params.json_payload),
    })


# ---------------------------------------------------------------------------
# ConditionalAction validations
# ---------------------------------------------------------------------------


def validate_get_conditional_action_request(params):
    """Validate GetConditionalActionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "ActionID": _validate_required(params.action_id),
    })


def validate_get_conditional_action_list_request(params):
    """Validate GetConditionalActionListRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
    })


def validate_create_conditional_action_request(params):
    """Validate CreateConditionalActionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "JsonPayload": _validate_required(params.json_payload),
    })


def validate_update_conditional_action_request(params):
    """Validate UpdateConditionalActionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "ActionID": _validate_required(params.action_id),
        "JsonPayload": _validate_required(params.json_payload),
    })


def validate_remove_conditional_action_request(params):
    """Validate RemoveConditionalActionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "ActionID": _validate_required(params.action_id),
    })


# ---------------------------------------------------------------------------
# ContentProtectionJavaScriptInjectionRule validations
# ---------------------------------------------------------------------------


def validate_get_content_protection_javascript_injection_rule_request(params):
    """Validate GetContentProtectionJavaScriptInjectionRuleRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "ContentProtectionJavaScriptInjectionRuleID": _validate_required(
            params.content_protection_javascript_injection_rule_id
        ),
    })


def validate_get_content_protection_javascript_injection_rule_list_request(params):
    """Validate GetContentProtectionJavaScriptInjectionRuleListRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "Version": _validate_required(params.version),
    })


def validate_create_content_protection_javascript_injection_rule_request(params):
    """Validate CreateContentProtectionJavaScriptInjectionRuleRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "JsonPayload": _validate_required(params.json_payload),
    })


def validate_update_content_protection_javascript_injection_rule_request(params):
    """Validate UpdateContentProtectionJavaScriptInjectionRuleRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "ContentProtectionJavaScriptInjectionRuleID": _validate_required(
            params.content_protection_javascript_injection_rule_id
        ),
        "JsonPayload": _validate_required(params.json_payload),
    })


def validate_remove_content_protection_javascript_injection_rule_request(params):
    """Validate RemoveContentProtectionJavaScriptInjectionRuleRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "ContentProtectionJavaScriptInjectionRuleID": _validate_required(
            params.content_protection_javascript_injection_rule_id
        ),
    })


# ---------------------------------------------------------------------------
# ContentProtectionRule validations
# ---------------------------------------------------------------------------


def validate_get_content_protection_rule_request(params):
    """Validate GetContentProtectionRuleRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "ContentProtectionRuleID": _validate_required(
            params.content_protection_rule_id
        ),
    })


def validate_get_content_protection_rule_list_request(params):
    """Validate GetContentProtectionRuleListRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "Version": _validate_required(params.version),
    })


def validate_create_content_protection_rule_request(params):
    """Validate CreateContentProtectionRuleRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "JsonPayload": _validate_required(params.json_payload),
    })


def validate_update_content_protection_rule_request(params):
    """Validate UpdateContentProtectionRuleRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "ContentProtectionRuleID": _validate_required(
            params.content_protection_rule_id
        ),
        "JsonPayload": _validate_required(params.json_payload),
    })


def validate_remove_content_protection_rule_request(params):
    """Validate RemoveContentProtectionRuleRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "ContentProtectionRuleID": _validate_required(
            params.content_protection_rule_id
        ),
    })


# ---------------------------------------------------------------------------
# ContentProtectionRuleSequence validations
# ---------------------------------------------------------------------------


def validate_get_content_protection_rule_sequence_request(params):
    """Validate GetContentProtectionRuleSequenceRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
    })


def validate_update_content_protection_rule_sequence_request(params):
    """Validate UpdateContentProtectionRuleSequenceRequest parameters.

    Validates the nested ContentProtectionRuleSequence field within the
    ContentProtectionRuleSequence body object, mirroring Go's
    v.ContentProtectionRuleSequence.ContentProtectionRuleSequence validation.
    """
    outer = getattr(params, "content_protection_rule_sequence", None)
    nested_val = (
        getattr(outer, "content_protection_rule_sequence", None)
        if outer is not None else None
    )
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "ContentProtectionRuleSequence": _validate_required(
            nested_val
        ),
    })


# ---------------------------------------------------------------------------
# CustomBotCategory validations
# ---------------------------------------------------------------------------


def validate_get_custom_bot_category_request(params):
    """Validate GetCustomBotCategoryRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "CategoryID": _validate_required(params.category_id),
    })


def validate_get_custom_bot_category_list_request(params):
    """Validate GetCustomBotCategoryListRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
    })


def validate_create_custom_bot_category_request(params):
    """Validate CreateCustomBotCategoryRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "JsonPayload": _validate_required(params.json_payload),
    })


def validate_update_custom_bot_category_request(params):
    """Validate UpdateCustomBotCategoryRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "CategoryID": _validate_required(params.category_id),
        "JsonPayload": _validate_required(params.json_payload),
    })


def validate_remove_custom_bot_category_request(params):
    """Validate RemoveCustomBotCategoryRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "CategoryID": _validate_required(params.category_id),
    })


# ---------------------------------------------------------------------------
# CustomBotCategoryAction validations
# ---------------------------------------------------------------------------


def validate_get_custom_bot_category_action_request(params):
    """Validate GetCustomBotCategoryActionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "CategoryID": _validate_required(params.category_id),
    })


def validate_get_custom_bot_category_action_list_request(params):
    """Validate GetCustomBotCategoryActionListRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
    })


def validate_update_custom_bot_category_action_request(params):
    """Validate UpdateCustomBotCategoryActionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "CategoryID": _validate_required(params.category_id),
        "JsonPayload": _validate_required(params.json_payload),
    })


# ---------------------------------------------------------------------------
# CustomBotCategoryItemSequence validations
# ---------------------------------------------------------------------------


def validate_get_custom_bot_category_item_sequence_request(params):
    """Validate GetCustomBotCategoryItemSequenceRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "CategoryID": _validate_required(params.category_id),
    })


def validate_update_custom_bot_category_item_sequence_request(params):
    """Validate UpdateCustomBotCategoryItemSequenceRequest parameters.

    Validates the nested Sequence field within the Sequence body object,
    mirroring Go's v.Sequence.Sequence validation.
    """
    outer = getattr(params, "sequence", None)
    nested_val = (
        getattr(outer, "sequence", None)
        if outer is not None else None
    )
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "CategoryID": _validate_required(params.category_id),
        "Sequence": _validate_required(nested_val),
    })


# ---------------------------------------------------------------------------
# CustomBotCategorySequence validations
# ---------------------------------------------------------------------------


def validate_get_custom_bot_category_sequence_request(params):
    """Validate GetCustomBotCategorySequenceRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
    })


def validate_update_custom_bot_category_sequence_request(params):
    """Validate UpdateCustomBotCategorySequenceRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "Sequence": _validate_required(params.sequence),
    })


# ---------------------------------------------------------------------------
# CustomClient validations
# ---------------------------------------------------------------------------


def validate_get_custom_client_request(params):
    """Validate GetCustomClientRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "CustomClientID": _validate_required(params.custom_client_id),
    })


def validate_get_custom_client_list_request(params):
    """Validate GetCustomClientListRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
    })


def validate_create_custom_client_request(params):
    """Validate CreateCustomClientRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "JsonPayload": _validate_required(params.json_payload),
    })


def validate_update_custom_client_request(params):
    """Validate UpdateCustomClientRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "CustomClientID": _validate_required(params.custom_client_id),
        "JsonPayload": _validate_required(params.json_payload),
    })


def validate_remove_custom_client_request(params):
    """Validate RemoveCustomClientRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "CustomClientID": _validate_required(params.custom_client_id),
    })


# ---------------------------------------------------------------------------
# CustomClientSequence validations
# ---------------------------------------------------------------------------


def validate_get_custom_client_sequence_request(params):
    """Validate GetCustomClientSequenceRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
    })


def validate_update_custom_client_sequence_request(params):
    """Validate UpdateCustomClientSequenceRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "Sequence": _validate_required(params.sequence),
    })


# ---------------------------------------------------------------------------
# CustomCode validations
# ---------------------------------------------------------------------------


def validate_get_custom_code_request(params):
    """Validate GetCustomCodeRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
    })


def validate_update_custom_code_request(params):
    """Validate UpdateCustomCodeRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "JsonPayload": _validate_required(params.json_payload),
    })


# ---------------------------------------------------------------------------
# CustomDefinedBot validations
# ---------------------------------------------------------------------------


def validate_get_custom_defined_bot_request(params):
    """Validate GetCustomDefinedBotRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "BotID": _validate_required(params.bot_id),
    })


def validate_get_custom_defined_bot_list_request(params):
    """Validate GetCustomDefinedBotListRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
    })


def validate_create_custom_defined_bot_request(params):
    """Validate CreateCustomDefinedBotRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "JsonPayload": _validate_required(params.json_payload),
    })


def validate_update_custom_defined_bot_request(params):
    """Validate UpdateCustomDefinedBotRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "BotID": _validate_required(params.bot_id),
        "JsonPayload": _validate_required(params.json_payload),
    })


def validate_remove_custom_defined_bot_request(params):
    """Validate RemoveCustomDefinedBotRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "BotID": _validate_required(params.bot_id),
    })


# ---------------------------------------------------------------------------
# CustomDenyAction validations
# ---------------------------------------------------------------------------


def validate_get_custom_deny_action_request(params):
    """Validate GetCustomDenyActionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "ActionID": _validate_required(params.action_id),
    })


def validate_get_custom_deny_action_list_request(params):
    """Validate GetCustomDenyActionListRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
    })


def validate_create_custom_deny_action_request(params):
    """Validate CreateCustomDenyActionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "JsonPayload": _validate_required(params.json_payload),
    })


def validate_update_custom_deny_action_request(params):
    """Validate UpdateCustomDenyActionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "ActionID": _validate_required(params.action_id),
        "JsonPayload": _validate_required(params.json_payload),
    })


def validate_remove_custom_deny_action_request(params):
    """Validate RemoveCustomDenyActionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "ActionID": _validate_required(params.action_id),
    })


# ---------------------------------------------------------------------------
# JavascriptInjection validations
# ---------------------------------------------------------------------------


def validate_get_javascript_injection_request(params):
    """Validate GetJavascriptInjectionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
    })


def validate_update_javascript_injection_request(params):
    """Validate UpdateJavascriptInjectionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "JsonPayload": _validate_required(params.json_payload),
    })


# ---------------------------------------------------------------------------
# RecategorizedAkamaiDefinedBot validations
# ---------------------------------------------------------------------------


def validate_get_recategorized_akamai_defined_bot_request(params):
    """Validate GetRecategorizedAkamaiDefinedBotRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "BotID": _validate_required(params.bot_id),
    })


def validate_get_recategorized_akamai_defined_bot_list_request(params):
    """Validate GetRecategorizedAkamaiDefinedBotListRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
    })


def validate_create_recategorized_akamai_defined_bot_request(params):
    """Validate CreateRecategorizedAkamaiDefinedBotRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "BotID": _validate_required(params.bot_id),
        "CategoryID": _validate_required(params.category_id),
    })


def validate_update_recategorized_akamai_defined_bot_request(params):
    """Validate UpdateRecategorizedAkamaiDefinedBotRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "BotID": _validate_required(params.bot_id),
        "CategoryID": _validate_required(params.category_id),
    })


def validate_remove_recategorized_akamai_defined_bot_request(params):
    """Validate RemoveRecategorizedAkamaiDefinedBotRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "BotID": _validate_required(params.bot_id),
    })


# ---------------------------------------------------------------------------
# ResponseAction validations
# ---------------------------------------------------------------------------


def validate_get_response_action_list_request(params):
    """Validate GetResponseActionListRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
    })


# ---------------------------------------------------------------------------
# ServeAlternateAction validations
# ---------------------------------------------------------------------------


def validate_get_serve_alternate_action_request(params):
    """Validate GetServeAlternateActionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "ActionID": _validate_required(params.action_id),
    })


def validate_get_serve_alternate_action_list_request(params):
    """Validate GetServeAlternateActionListRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
    })


def validate_create_serve_alternate_action_request(params):
    """Validate CreateServeAlternateActionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "JsonPayload": _validate_required(params.json_payload),
    })


def validate_update_serve_alternate_action_request(params):
    """Validate UpdateServeAlternateActionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "ActionID": _validate_required(params.action_id),
        "JsonPayload": _validate_required(params.json_payload),
    })


def validate_remove_serve_alternate_action_request(params):
    """Validate RemoveServeAlternateActionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "ActionID": _validate_required(params.action_id),
    })


# ---------------------------------------------------------------------------
# TransactionalEndpoint validations
# ---------------------------------------------------------------------------


def validate_get_transactional_endpoint_request(params):
    """Validate GetTransactionalEndpointRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "OperationID": _validate_required(params.operation_id),
    })


def validate_get_transactional_endpoint_list_request(params):
    """Validate GetTransactionalEndpointListRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "Version": _validate_required(params.version),
    })


def validate_create_transactional_endpoint_request(params):
    """Validate CreateTransactionalEndpointRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "JsonPayload": _validate_required(params.json_payload),
    })


def validate_update_transactional_endpoint_request(params):
    """Validate UpdateTransactionalEndpointRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "OperationID": _validate_required(params.operation_id),
        "JsonPayload": _validate_required(params.json_payload),
    })


def validate_remove_transactional_endpoint_request(params):
    """Validate RemoveTransactionalEndpointRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "SecurityPolicyID": _validate_required(
            params.security_policy_id
        ),
        "OperationID": _validate_required(params.operation_id),
    })


# ---------------------------------------------------------------------------
# TransactionalEndpointProtection validations
# ---------------------------------------------------------------------------


def validate_get_transactional_endpoint_protection_request(params):
    """Validate GetTransactionalEndpointProtectionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
    })


def validate_update_transactional_endpoint_protection_request(params):
    """Validate UpdateTransactionalEndpointProtectionRequest parameters."""
    _run_validation({
        "ConfigID": _validate_required(params.config_id),
        "Version": _validate_required(params.version),
        "JsonPayload": _validate_required(params.json_payload),
    })
