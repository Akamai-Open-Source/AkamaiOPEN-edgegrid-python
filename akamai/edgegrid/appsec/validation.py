# pylint: disable=too-many-lines
"""Request validation functions for the Application Security API client.

Provides validation for all AppSec API request models, mirroring the
Go ozzo-validation and edgegriderr.ParseValidationErrors patterns.

Two validation patterns are used:
1. Simple (.Filter()) pattern: _validate_required() - joins all errors sorted by key
2. Parsed (ParseValidationErrors) pattern: _validate_parsed() - structured multi-line output
"""

from akamai.edgegrid.errors import ErrStructValidation
from akamai.edgegrid.validation import parse_validation_errors


def _required(value):
    """Check if a value meets the required validation constraint.

    Mirrors Go ozzo-validation Required rule where zero values fail.
    For int: 0 fails. For str: empty string fails. For None: fails.
    For list/dict: empty collection fails.

    Args:
        value: The value to validate.

    Returns:
        Error message string if invalid, None if valid.
    """
    if value is None:
        return "cannot be blank"
    if isinstance(value, (int, float)) and value == 0:
        return "cannot be blank"
    if isinstance(value, str) and value == "":
        return "cannot be blank"
    if isinstance(value, (list, dict)) and len(value) == 0:
        return "cannot be blank"
    return None


def _in_values(value, allowed, error_msg):
    """Check if a non-empty value is in the allowed set.

    Mirrors Go ozzo-validation In() rule which skips zero/empty values.
    Only validates non-empty values against the allowed set.

    Args:
        value: The value to validate.
        allowed: Tuple of allowed values.
        error_msg: Error message to return if value is not in allowed set.

    Returns:
        Error message string if invalid, None if valid or empty.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)) and value == 0:
        return None
    if isinstance(value, str) and value == "":
        return None
    if isinstance(value, (list, dict)) and len(value) == 0:
        return None
    if value not in allowed:
        return error_msg
    return None


def _required_in(value, allowed, error_msg):
    """Check required constraint first, then in-set constraint.

    Combines Go ozzo-validation Required and In rules in sequence.
    If empty, fails with required error. If non-empty but not in set,
    fails with in-set error.

    Args:
        value: The value to validate.
        allowed: Tuple of allowed values.
        error_msg: Error message for in-set validation failure.

    Returns:
        Error message string if invalid, None if valid.
    """
    req = _required(value)
    if req is not None:
        return req
    if value not in allowed:
        return error_msg
    return None


def _validate_required(errors):
    """Validate using simple .Filter() pattern and raise on failure.

    Mirrors Go validation.Errors{...}.Filter(). Collects all errors,
    sorts by key, and joins with semicolons ending with a period.

    Args:
        errors: Dict mapping field names to error messages (None if valid).

    Raises:
        ErrStructValidation: If any field has a validation error.
    """
    filtered = {k: v for k, v in errors.items() if v is not None}
    if filtered:
        parts = [f"{k}: {v}" for k, v in sorted(filtered.items())]
        msg = "; ".join(parts) + "."
        raise ErrStructValidation(f"struct validation: {msg}")


def _validate_parsed(errors):
    """Validate using ParseValidationErrors pattern and raise on failure.

    Mirrors Go edgegriderr.ParseValidationErrors(validation.Errors{...}).
    Uses structured multi-line output format with indentation.

    Args:
        errors: Dict mapping field names to error messages, nested dicts, or None.

    Raises:
        ErrStructValidation: If any field has a validation error.
    """
    result = parse_validation_errors(errors)
    if result is not None:
        raise ErrStructValidation(f"struct validation: {result}")


def validate_get_activations_request(params):
    """Validate GetActivationsRequest."""
    _validate_required({
        "activationid": _required(params.activation_id),
    })


def validate_get_activation_history_request(params):
    """Validate GetActivationHistoryRequest."""
    _validate_required({
        "configId": _required(params.config_id),
    })


def validate_get_configuration_request(params):
    """Validate GetConfigurationRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
    })


def validate_get_configurations_request(params):
    """Validate GetConfigurationsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
    })


def validate_update_configuration_request(params):
    """Validate UpdateConfigurationRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
    })


def validate_remove_configuration_request(params):
    """Validate RemoveConfigurationRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
    })


def validate_get_configuration_clone_request(params):
    """Validate GetConfigurationCloneRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_create_configuration_clone_request(params):
    """Validate CreateConfigurationCloneRequest."""
    _validate_required({
        "CreateFromConfigID": _required(params.create_from.config_id),
    })


def validate_get_configuration_version_request(params):
    """Validate GetConfigurationVersionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_configuration_version_clone_request(params):
    """Validate GetConfigurationVersionCloneRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_create_configuration_version_clone_request(params):
    """Validate CreateConfigurationVersionCloneRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.create_from_version),
    })


def validate_remove_configuration_version_clone_request(params):
    """Validate RemoveConfigurationVersionCloneRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_security_policies_request(params):
    """Validate GetSecurityPoliciesRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_security_policy_request(params):
    """Validate GetSecurityPolicyRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_create_security_policy_request(params):
    """Validate CreateSecurityPolicyRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyName": _required(params.policy_name),
        "PolicyPrefix": _required(params.policy_prefix),
    })


def validate_create_security_policy_with_default_protections_request(params):
    """Validate CreateSecurityPolicyWithDefaultProtectionsRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyName": _required(params.policy_name),
        "PolicyPrefix": _required(params.policy_prefix),
    })


def validate_update_security_policy_request(params):
    """Validate UpdateSecurityPolicyRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_remove_security_policy_request(params):
    """Validate RemoveSecurityPolicyRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_security_policy_clone_request(params):
    """Validate GetSecurityPolicyCloneRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_security_policy_clones_request(params):
    """Validate GetSecurityPolicyClonesRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_create_security_policy_clone_request(params):
    """Validate CreateSecurityPolicyCloneRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_policy_protections_request(params):
    """Validate GetPolicyProtectionsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_policy_protections_request(params):
    """Validate UpdatePolicyProtectionsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_custom_rule_request(params):
    """Validate GetCustomRuleRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ID": _required(params.id),
    })


def validate_get_custom_rules_request(params):
    """Validate GetCustomRulesRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
    })


def validate_create_custom_rule_request(params):
    """Validate CreateCustomRuleRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
    })


def validate_update_custom_rule_request(params):
    """Validate UpdateCustomRuleRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ID": _required(params.id),
    })


def validate_remove_custom_rule_request(params):
    """Validate RemoveCustomRuleRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ID": _required(params.id),
    })


def validate_get_custom_rules_usage_request(params):
    """Validate GetCustomRulesUsageRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "RuleIDs": _required(params.request_body),
    })


def validate_get_custom_rule_action_request(params):
    """Validate GetCustomRuleActionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_custom_rule_actions_request(params):
    """Validate GetCustomRuleActionsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_custom_rule_action_request(params):
    """Validate UpdateCustomRuleActionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "ID": _required(params.rule_id),
    })


def validate_get_custom_deny_request(params):
    """Validate GetCustomDenyRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "ID": _required(params.id),
    })


def validate_get_custom_deny_list_request(params):
    """Validate GetCustomDenyListRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_create_custom_deny_request(params):
    """Validate CreateCustomDenyRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_custom_deny_request(params):
    """Validate UpdateCustomDenyRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "ID": _required(params.id),
    })


def validate_remove_custom_deny_request(params):
    """Validate RemoveCustomDenyRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "ID": _required(params.id),
    })


def validate_get_rate_policy_request(params):
    """Validate GetRatePolicyRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "RatePolicyID": _required(params.rate_policy_id),
    })


def validate_get_rate_policies_request(params):
    """Validate GetRatePoliciesRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
    })


def validate_create_rate_policy_request(params):
    """Validate CreateRatePolicyRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
    })


def validate_update_rate_policy_request(params):
    """Validate UpdateRatePolicyRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "RatePolicyID": _required(params.rate_policy_id),
    })


def validate_remove_rate_policy_request(params):
    """Validate RemoveRatePolicyRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "RatePolicyID": _required(params.rate_policy_id),
    })


def validate_get_rate_policy_actions_request(params):
    """Validate GetRatePolicyActionsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_rate_policy_action_request(params):
    """Validate UpdateRatePolicyActionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "RatePolicyID": _required(params.rate_policy_id),
    })


def validate_get_eval_request(params):
    """Validate GetEvalRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_eval_request(params):
    """Validate UpdateEvalRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_remove_eval_request(params):
    """Validate RemoveEvalRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_eval_rule_request(params):
    """Validate GetEvalRuleRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "RuleID": _required(params.rule_id),
    })


def validate_get_eval_rules_request(params):
    """Validate GetEvalRulesRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_eval_rule_request(params):
    """Validate UpdateEvalRuleRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "RuleID": _required(params.rule_id),
    })


def validate_get_attack_group_request(params):
    """Validate GetAttackGroupRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_attack_groups_request(params):
    """Validate GetAttackGroupsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_attack_group_request(params):
    """Validate UpdateAttackGroupRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_penalty_box_request(params):
    """Validate GetPenaltyBoxRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_penalty_box_request(params):
    """Validate UpdatePenaltyBoxRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "Action": _required_in(
            params.action,
            ("alert", "deny", "none"),
            f"value '{params.action}' is invalid. Must be one of: "
            f"'alert', 'deny' or 'none'",
        ),
    })


def validate_get_penalty_box_conditions_request(params):
    """Validate GetPenaltyBoxConditionsRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_penalty_box_conditions_request(params):
    """Validate UpdatePenaltyBoxConditionsRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "ConditionsPayload": _required(params.conditions_payload),
    })


def validate_get_reputation_profile_request(params):
    """Validate GetReputationProfileRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "RatePolicyID": _required(params.reputation_profile_id),
    })


def validate_get_reputation_profiles_request(params):
    """Validate GetReputationProfilesRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
    })


def validate_create_reputation_profile_request(params):
    """Validate CreateReputationProfileRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
    })


def validate_update_reputation_profile_request(params):
    """Validate UpdateReputationProfileRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "ReputationProfileId": _required(params.reputation_profile_id),
    })


def validate_remove_reputation_profile_request(params):
    """Validate RemoveReputationProfileRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "ReputationProfileId": _required(params.reputation_profile_id),
    })


def validate_get_reputation_profile_action_request(params):
    """Validate GetReputationProfileActionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "ReputationProfileID": _required(params.reputation_profile_id),
    })


def validate_get_reputation_profile_actions_request(params):
    """Validate GetReputationProfileActionsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_reputation_profile_action_request(params):
    """Validate UpdateReputationProfileActionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "ReputationProfileID": _required(params.reputation_profile_id),
    })


def validate_get_reputation_analysis_request(params):
    """Validate GetReputationAnalysisRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_reputation_analysis_request(params):
    """Validate UpdateReputationAnalysisRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_match_target_request(params):
    """Validate GetMatchTargetRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "TargetID": _required(params.target_id),
    })


def validate_get_match_targets_request(params):
    """Validate GetMatchTargetsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
    })


def validate_create_match_target_request(params):
    """Validate CreateMatchTargetRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
    })


def validate_update_match_target_request(params):
    """Validate UpdateMatchTargetRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "TargetID": _required(params.target_id),
    })


def validate_remove_match_target_request(params):
    """Validate RemoveMatchTargetRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "TargetID": _required(params.target_id),
    })


def validate_get_match_target_sequence_request(params):
    """Validate GetMatchTargetSequenceRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "Type": _required(params.type),
    })


def validate_update_match_target_sequence_request(params):
    """Validate UpdateMatchTargetSequenceRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "Type": _required(params.config_version),
    })


def validate_get_rule_request(params):
    """Validate GetRuleRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "RuleID": _required(params.rule_id),
    })


def validate_get_rules_request(params):
    """Validate GetRulesRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_rule_request(params):
    """Validate UpdateRuleRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "RuleID": _required(params.rule_id),
    })


def validate_update_condition_exception_request(params):
    """Validate UpdateConditionExceptionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "RuleID": _required(params.rule_id),
    })


def validate_get_rule_upgrade_request(params):
    """Validate GetRuleUpgradeRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_rule_upgrade_request(params):
    """Validate UpdateRuleUpgradeRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_rapid_rules_request(params):
    """Validate GetRapidRulesRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_rapid_rules_status_request(params):
    """Validate UpdateRapidRulesStatusRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "Body": _required(params.body),
    })


def validate_update_rapid_rules_default_action_request(params):
    """Validate UpdateRapidRulesDefaultActionRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "Body": _required(params.body),
    })


def validate_update_rapid_rule_action_lock_request(params):
    """Validate UpdateRapidRuleActionLockRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "RuleID": _required(params.rule_id),
        "Body": _required(params.body),
    })


def validate_update_rapid_rule_action_request(params):
    """Validate UpdateRapidRuleActionRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "RuleID": _required(params.rule_id),
        "RuleVersion": _required(params.rule_version),
        "Body": _required(params.body),
    })


def validate_update_rapid_rule_exception_request(params):
    """Validate UpdateRapidRuleExceptionRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "RuleID": _required(params.rule_id),
        "Body": _required(params.body),
    })


def validate_get_waf_mode_request(params):
    """Validate GetWAFModeRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_waf_mode_request(params):
    """Validate UpdateWAFModeRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_ip_geo_request(params):
    """Validate GetIPGeoRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_ip_geo_request(params):
    """Validate UpdateIPGeoRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_ip_geo_protection_request(params):
    """Validate GetIPGeoProtectionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_ip_geo_protection_request(params):
    """Validate UpdateIPGeoProtectionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_rate_protection_request(params):
    """Validate GetRateProtectionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_rate_protection_request(params):
    """Validate UpdateRateProtectionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_reputation_protection_request(params):
    """Validate GetReputationProtectionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_reputation_protection_request(params):
    """Validate UpdateReputationProtectionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_waf_protection_request(params):
    """Validate GetWAFProtectionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_waf_protection_request(params):
    """Validate UpdateWAFProtectionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_slow_post_protection_settings_request(params):
    """Validate GetSlowPostProtectionSettingsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_slow_post_protection_request(params):
    """Validate GetSlowPostProtectionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_slow_post_protections_request(params):
    """Validate GetSlowPostProtectionsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_slow_post_protection_request(params):
    """Validate UpdateSlowPostProtectionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_slow_post_protection_setting_request(params):
    """Validate UpdateSlowPostProtectionSettingRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_ip_geo_protections_request(params):
    """Validate GetIPGeoProtectionsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_rate_protections_request(params):
    """Validate GetRateProtectionsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_reputation_protections_request(params):
    """Validate GetReputationProtectionsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_remove_reputation_protection_request(params):
    """Validate RemoveReputationProtectionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_malware_policy_request(params):
    """Validate GetMalwarePolicyRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "MalwarePolicyID": _required(params.malware_policy_id),
    })


def validate_get_malware_policies_request(params):
    """Validate GetMalwarePoliciesRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
    })


def validate_create_malware_policy_request(params):
    """Validate CreateMalwarePolicyRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "Policy": _required(params.policy),
    })


def validate_update_malware_policy_request(params):
    """Validate UpdateMalwarePolicyRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "MalwarePolicyID": _required(params.malware_policy_id),
        "Policy": _required(params.policy),
    })


def validate_remove_malware_policy_request(params):
    """Validate RemoveMalwarePolicyRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "MalwarePolicyID": _required(params.malware_policy_id),
    })


def validate_get_malware_policy_actions_request(params):
    """Validate GetMalwarePolicyActionsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_malware_policy_action_request(params):
    """Validate UpdateMalwarePolicyActionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "MalwarePolicyID": _required(params.malware_policy_id),
        "Action": _required(params.action),
        "UnscannedAction": _required(params.unscanned_action),
    })


def validate_update_malware_policy_actions_request(params):
    """Validate UpdateMalwarePolicyActionsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "MalwarePolicyActions": _required(params.malware_policy_actions),
    })


def validate_get_malware_content_types_request(params):
    """Validate GetMalwareContentTypesRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_malware_protection_request(params):
    """Validate GetMalwareProtectionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_malware_protections_request(params):
    """Validate GetMalwareProtectionsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_malware_protection_request(params):
    """Validate UpdateMalwareProtectionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_api_endpoints_request(params):
    """Validate GetApiEndpointsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_api_hostname_coverage_match_targets_request(params):
    """Validate GetApiHostnameCoverageMatchTargetsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_api_hostname_coverage_overlapping_request(params):
    """Validate GetApiHostnameCoverageOverlappingRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_api_request_constraints_request(params):
    """Validate GetApiRequestConstraintsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_api_request_constraints_request(params):
    """Validate UpdateApiRequestConstraintsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_remove_api_request_constraints_request(params):
    """Validate RemoveApiRequestConstraintsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_api_constraints_protection_request(params):
    """Validate GetAPIConstraintsProtectionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_api_constraints_protection_request(params):
    """Validate UpdateAPIConstraintsProtectionRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_wap_selected_hostnames_request(params):
    """Validate GetWAPSelectedHostnamesRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "SecurityPolicyID": _required(params.version),
    })


def validate_update_wap_selected_hostnames_request(params):
    """Validate UpdateWAPSelectedHostnamesRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "SecurityPolicyID": _required(params.version),
    })


def validate_get_wap_bypass_network_lists_request(params):
    """Validate GetWAPBypassNetworkListsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_wap_bypass_network_lists_request(params):
    """Validate UpdateWAPBypassNetworkListsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_remove_wap_bypass_network_lists_request(params):
    """Validate RemoveWAPBypassNetworkListsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_siem_settings_request(params):
    """Validate GetSiemSettingsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_siem_settings_request(params):
    """Validate UpdateSiemSettingsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_remove_siem_settings_request(params):
    """Validate RemoveSiemSettingsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_selected_hostname_request(params):
    """Validate GetSelectedHostnameRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_selected_hostname_request(params):
    """Validate UpdateSelectedHostnameRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_host_move_validation_request(params):
    """Validate GetHostMoveValidationRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "Network": _required_in(
            params.network,
            ("PRODUCTION", "STAGING"),
            "must be a valid value",
        ),
    })


def validate_create_activations_with_host_move_request(params):
    """Validate CreateActivationsWithHostMoveRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "Action": _required(params.action),
        "Network": _required_in(
            params.network,
            ("PRODUCTION", "STAGING"),
            "must be a valid value",
        ),
    })


def validate_get_export_configuration_request(params):
    """Validate GetExportConfigurationRequest."""
    _validate_parsed({
        "Source": _in_values(
            params.source,
            ("TF",),
            f"value '{params.source}' is invalid. Must be one of: 'TF' or empty",
        ),
    })


def validate_get_version_notes_request(params):
    """Validate GetVersionNotesRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_version_notes_request(params):
    """Validate UpdateVersionNotesRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_threat_intel_request(params):
    """Validate GetThreatIntelRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_threat_intel_request(params):
    """Validate UpdateThreatIntelRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_tuning_recommendations_request(params):
    """Validate GetTuningRecommendationsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "RulesetType": _in_values(
            params.ruleset_type,
            ("active", "evaluation"),
            f"value '{params.ruleset_type}' is invalid. Must be one of: "
            f"'active', 'evaluation' or '' (empty)",
        ),
    })


def validate_get_attack_group_recommendations_request(params):
    """Validate GetAttackGroupRecommendationsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "Group": _required(params.group),
        "RulesetType": _in_values(
            params.ruleset_type,
            ("active", "evaluation"),
            f"value '{params.ruleset_type}' is invalid. Must be one of: "
            f"'active', 'evaluation' or '' (empty)",
        ),
    })


def validate_get_rule_recommendations_request(params):
    """Validate GetRuleRecommendationsRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "RuleID": _required(params.rule_id),
        "RulesetType": _in_values(
            params.ruleset_type,
            ("active", "evaluation"),
            f"value '{params.ruleset_type}' is invalid. Must be one of: "
            f"'active', 'evaluation' or '' (empty)",
        ),
    })


def validate_get_advanced_settings_logging_request(params):
    """Validate GetAdvancedSettingsLoggingRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_advanced_settings_logging_request(params):
    """Validate UpdateAdvancedSettingsLoggingRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_remove_advanced_settings_logging_request(params):
    """Validate RemoveAdvancedSettingsLoggingRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_advanced_settings_ase_penalty_box_request(params):
    """Validate GetAdvancedSettingsAsePenaltyBoxRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_advanced_settings_ase_penalty_box_request(params):
    """Validate UpdateAdvancedSettingsAsePenaltyBoxRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_advanced_settings_attack_payload_logging_request(params):
    """Validate GetAdvancedSettingsAttackPayloadLoggingRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_advanced_settings_attack_payload_logging_request(params):
    """Validate UpdateAdvancedSettingsAttackPayloadLoggingRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_remove_advanced_settings_attack_payload_logging_request(params):
    """Validate RemoveAdvancedSettingsAttackPayloadLoggingRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_advanced_settings_evasive_path_match_request(params):
    """Validate GetAdvancedSettingsEvasivePathMatchRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_advanced_settings_evasive_path_match_request(params):
    """Validate UpdateAdvancedSettingsEvasivePathMatchRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_remove_advanced_settings_evasive_path_match_request(params):
    """Validate RemoveAdvancedSettingsEvasivePathMatchRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_advanced_settings_ja4_fingerprint_request(params):
    """Validate GetAdvancedSettingsJA4FingerprintRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_advanced_settings_ja4_fingerprint_request(params):
    """Validate UpdateAdvancedSettingsJA4FingerprintRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_remove_advanced_settings_ja4_fingerprint_request(params):
    """Validate RemoveAdvancedSettingsJA4FingerprintRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_advanced_settings_pii_learning_request(params):
    """Validate GetAdvancedSettingsPIILearningRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_advanced_settings_pii_learning_request(params):
    """Validate UpdateAdvancedSettingsPIILearningRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_advanced_settings_pragma_request(params):
    """Validate GetAdvancedSettingsPragmaRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_advanced_settings_pragma_request(params):
    """Validate UpdateAdvancedSettingsPragmaRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_advanced_settings_prefetch_request(params):
    """Validate GetAdvancedSettingsPrefetchRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_advanced_settings_prefetch_request(params):
    """Validate UpdateAdvancedSettingsPrefetchRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_advanced_settings_request_body_request(params):
    """Validate GetAdvancedSettingsRequestBodyRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_advanced_settings_request_body_request(params):
    """Validate UpdateAdvancedSettingsRequestBodyRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_remove_advanced_settings_request_body_request(params):
    """Validate RemoveAdvancedSettingsRequestBodyRequest."""
    _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_remove_advanced_settings_ase_penalty_box_request(params):
    """Validate RemoveAdvancedSettingsAsePenaltyBoxRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_selected_hostnames_request(params):
    """Validate GetSelectedHostnamesRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_selected_hostnames_request(params):
    """Validate UpdateSelectedHostnamesRequest."""
    _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })
