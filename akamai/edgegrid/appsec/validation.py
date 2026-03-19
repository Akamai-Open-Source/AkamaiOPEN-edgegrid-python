# pylint: disable=too-many-lines
"""Request validation functions for the Application Security API client.

Provides validation for all AppSec API request models, mirroring the
Go ozzo-validation and edgegriderr.ParseValidationErrors patterns.

Each validator returns a formatted error string on failure, or None when valid.

Two internal formatting patterns are used:
1. Simple (.Filter()) pattern: _validate_required() - joins all errors sorted by key
2. Parsed (ParseValidationErrors) pattern: _validate_parsed() - structured multi-line output
"""

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

    Returns:
        Formatted error string on failure, None when valid.
    """
    filtered = {k: v for k, v in errors.items() if v is not None}
    if filtered:
        parts = [f"{k}: {v}" for k, v in sorted(filtered.items())]
        msg = "; ".join(parts) + "."
        return f"struct validation: {msg}"
    return None


def _validate_parsed(errors):
    """Validate using ParseValidationErrors pattern and raise on failure.

    Mirrors Go edgegriderr.ParseValidationErrors(validation.Errors{...}).
    Uses structured multi-line output format with indentation.

    Args:
        errors: Dict mapping field names to error messages, nested dicts, or None.

    Returns:
        Formatted error string on failure, None when valid.
    """
    result = parse_validation_errors(errors)
    if result is not None:
        return f"struct validation: {result}"
    return None


def validate_get_activations_request(params) -> str | None:
    """Validate GetActivationsRequest."""
    return _validate_required({
        "activationid": _required(params.activation_id),
    })


def validate_get_activation_history_request(params) -> str | None:
    """Validate GetActivationHistoryRequest."""
    return _validate_required({
        "configId": _required(params.config_id),
    })


def validate_get_configuration_request(params) -> str | None:
    """Validate GetConfigurationRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
    })


def validate_get_configurations_request(params) -> str | None:
    """Validate GetConfigurationsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
    })


def validate_update_configuration_request(params) -> str | None:
    """Validate UpdateConfigurationRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
    })


def validate_remove_configuration_request(params) -> str | None:
    """Validate RemoveConfigurationRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
    })


def validate_get_configuration_clone_request(params) -> str | None:
    """Validate GetConfigurationCloneRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_create_configuration_clone_request(params) -> str | None:
    """Validate CreateConfigurationCloneRequest."""
    create_from = params.create_from or {}
    if isinstance(create_from, dict):
        config_id = create_from.get("configId")
    else:
        config_id = getattr(create_from, "config_id", None)
    return _validate_required({
        "CreateFromConfigID": _required(config_id),
    })


def validate_get_configuration_version_request(params) -> str | None:
    """Validate GetConfigurationVersionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_configuration_version_clone_request(params) -> str | None:
    """Validate GetConfigurationVersionCloneRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_create_configuration_version_clone_request(params) -> str | None:
    """Validate CreateConfigurationVersionCloneRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.create_from_version),
    })


def validate_remove_configuration_version_clone_request(params) -> str | None:
    """Validate RemoveConfigurationVersionCloneRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_security_policies_request(params) -> str | None:
    """Validate GetSecurityPoliciesRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_security_policy_request(params) -> str | None:
    """Validate GetSecurityPolicyRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_create_security_policy_request(params) -> str | None:
    """Validate CreateSecurityPolicyRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyName": _required(params.policy_name),
        "PolicyPrefix": _required(params.policy_prefix),
    })


def validate_create_security_policy_with_default_protections_request(params) -> str | None:
    """Validate CreateSecurityPolicyWithDefaultProtectionsRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyName": _required(params.policy_name),
        "PolicyPrefix": _required(params.policy_prefix),
    })


def validate_update_security_policy_request(params) -> str | None:
    """Validate UpdateSecurityPolicyRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_remove_security_policy_request(params) -> str | None:
    """Validate RemoveSecurityPolicyRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_security_policy_clone_request(params) -> str | None:
    """Validate GetSecurityPolicyCloneRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_security_policy_clones_request(params) -> str | None:
    """Validate GetSecurityPolicyClonesRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_create_security_policy_clone_request(params) -> str | None:
    """Validate CreateSecurityPolicyCloneRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_policy_protections_request(params) -> str | None:
    """Validate GetPolicyProtectionsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_policy_protections_request(params) -> str | None:
    """Validate UpdatePolicyProtectionsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_custom_rule_request(params) -> str | None:
    """Validate GetCustomRuleRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ID": _required(params.id),
    })


def validate_get_custom_rules_request(params) -> str | None:
    """Validate GetCustomRulesRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
    })


def validate_create_custom_rule_request(params) -> str | None:
    """Validate CreateCustomRuleRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
    })


def validate_update_custom_rule_request(params) -> str | None:
    """Validate UpdateCustomRuleRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ID": _required(params.id),
    })


def validate_remove_custom_rule_request(params) -> str | None:
    """Validate RemoveCustomRuleRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ID": _required(params.id),
    })


def validate_get_custom_rules_usage_request(params) -> str | None:
    """Validate GetCustomRulesUsageRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "RuleIDs": _required(params.request_body),
    })


def validate_get_custom_rule_action_request(params) -> str | None:
    """Validate GetCustomRuleActionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_custom_rule_actions_request(params) -> str | None:
    """Validate GetCustomRuleActionsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_custom_rule_action_request(params) -> str | None:
    """Validate UpdateCustomRuleActionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "ID": _required(params.rule_id),
    })


def validate_get_custom_deny_request(params) -> str | None:
    """Validate GetCustomDenyRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "ID": _required(params.id),
    })


def validate_get_custom_deny_list_request(params) -> str | None:
    """Validate GetCustomDenyListRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_create_custom_deny_request(params) -> str | None:
    """Validate CreateCustomDenyRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_custom_deny_request(params) -> str | None:
    """Validate UpdateCustomDenyRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "ID": _required(params.id),
    })


def validate_remove_custom_deny_request(params) -> str | None:
    """Validate RemoveCustomDenyRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "ID": _required(params.id),
    })


def validate_get_rate_policy_request(params) -> str | None:
    """Validate GetRatePolicyRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "RatePolicyID": _required(params.rate_policy_id),
    })


def validate_get_rate_policies_request(params) -> str | None:
    """Validate GetRatePoliciesRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
    })


def validate_create_rate_policy_request(params) -> str | None:
    """Validate CreateRatePolicyRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
    })


def validate_update_rate_policy_request(params) -> str | None:
    """Validate UpdateRatePolicyRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "RatePolicyID": _required(params.rate_policy_id),
    })


def validate_remove_rate_policy_request(params) -> str | None:
    """Validate RemoveRatePolicyRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "RatePolicyID": _required(params.rate_policy_id),
    })


def validate_get_rate_policy_actions_request(params) -> str | None:
    """Validate GetRatePolicyActionsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_rate_policy_action_request(params) -> str | None:
    """Validate UpdateRatePolicyActionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "RatePolicyID": _required(params.rate_policy_id),
    })


def validate_get_eval_request(params) -> str | None:
    """Validate GetEvalRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_eval_request(params) -> str | None:
    """Validate UpdateEvalRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_remove_eval_request(params) -> str | None:
    """Validate RemoveEvalRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_eval_rule_request(params) -> str | None:
    """Validate GetEvalRuleRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "RuleID": _required(params.rule_id),
    })


def validate_get_eval_rules_request(params) -> str | None:
    """Validate GetEvalRulesRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_eval_rule_request(params) -> str | None:
    """Validate UpdateEvalRuleRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "RuleID": _required(params.rule_id),
    })


def validate_get_attack_group_request(params) -> str | None:
    """Validate GetAttackGroupRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_attack_groups_request(params) -> str | None:
    """Validate GetAttackGroupsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_attack_group_request(params) -> str | None:
    """Validate UpdateAttackGroupRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_penalty_box_request(params) -> str | None:
    """Validate GetPenaltyBoxRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_penalty_box_request(params) -> str | None:
    """Validate UpdatePenaltyBoxRequest."""
    return _validate_required({
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


def validate_get_penalty_box_conditions_request(params) -> str | None:
    """Validate GetPenaltyBoxConditionsRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_penalty_box_conditions_request(params) -> str | None:
    """Validate UpdatePenaltyBoxConditionsRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "ConditionsPayload": _required(params.conditions_payload),
    })


def validate_get_reputation_profile_request(params) -> str | None:
    """Validate GetReputationProfileRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "RatePolicyID": _required(params.reputation_profile_id),
    })


def validate_get_reputation_profiles_request(params) -> str | None:
    """Validate GetReputationProfilesRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
    })


def validate_create_reputation_profile_request(params) -> str | None:
    """Validate CreateReputationProfileRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
    })


def validate_update_reputation_profile_request(params) -> str | None:
    """Validate UpdateReputationProfileRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "ReputationProfileId": _required(params.reputation_profile_id),
    })


def validate_remove_reputation_profile_request(params) -> str | None:
    """Validate RemoveReputationProfileRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "ReputationProfileId": _required(params.reputation_profile_id),
    })


def validate_get_reputation_profile_action_request(params) -> str | None:
    """Validate GetReputationProfileActionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "ReputationProfileID": _required(params.reputation_profile_id),
    })


def validate_get_reputation_profile_actions_request(params) -> str | None:
    """Validate GetReputationProfileActionsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_reputation_profile_action_request(params) -> str | None:
    """Validate UpdateReputationProfileActionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "ReputationProfileID": _required(params.reputation_profile_id),
    })


def validate_get_reputation_analysis_request(params) -> str | None:
    """Validate GetReputationAnalysisRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_reputation_analysis_request(params) -> str | None:
    """Validate UpdateReputationAnalysisRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_match_target_request(params) -> str | None:
    """Validate GetMatchTargetRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "TargetID": _required(params.target_id),
    })


def validate_get_match_targets_request(params) -> str | None:
    """Validate GetMatchTargetsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
    })


def validate_create_match_target_request(params) -> str | None:
    """Validate CreateMatchTargetRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
    })


def validate_update_match_target_request(params) -> str | None:
    """Validate UpdateMatchTargetRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "TargetID": _required(params.target_id),
    })


def validate_remove_match_target_request(params) -> str | None:
    """Validate RemoveMatchTargetRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "TargetID": _required(params.target_id),
    })


def validate_get_match_target_sequence_request(params) -> str | None:
    """Validate GetMatchTargetSequenceRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "Type": _required(params.type),
    })


def validate_update_match_target_sequence_request(params) -> str | None:
    """Validate UpdateMatchTargetSequenceRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "Type": _required(params.config_version),
    })


def validate_get_rule_request(params) -> str | None:
    """Validate GetRuleRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "RuleID": _required(params.rule_id),
    })


def validate_get_rules_request(params) -> str | None:
    """Validate GetRulesRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_rule_request(params) -> str | None:
    """Validate UpdateRuleRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "RuleID": _required(params.rule_id),
    })


def validate_update_condition_exception_request(params) -> str | None:
    """Validate UpdateConditionExceptionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "RuleID": _required(params.rule_id),
    })


def validate_get_rule_upgrade_request(params) -> str | None:
    """Validate GetRuleUpgradeRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_rule_upgrade_request(params) -> str | None:
    """Validate UpdateRuleUpgradeRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_rapid_rules_request(params) -> str | None:
    """Validate GetRapidRulesRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_rapid_rules_status_request(params) -> str | None:
    """Validate UpdateRapidRulesStatusRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "Body": _required(params.body),
    })


def validate_update_rapid_rules_default_action_request(params) -> str | None:
    """Validate UpdateRapidRulesDefaultActionRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "Body": _required(params.body),
    })


def validate_update_rapid_rule_action_lock_request(params) -> str | None:
    """Validate UpdateRapidRuleActionLockRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "RuleID": _required(params.rule_id),
        "Body": _required(params.body),
    })


def validate_update_rapid_rule_action_request(params) -> str | None:
    """Validate UpdateRapidRuleActionRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "RuleID": _required(params.rule_id),
        "RuleVersion": _required(params.rule_version),
        "Body": _required(params.body),
    })


def validate_update_rapid_rule_exception_request(params) -> str | None:
    """Validate UpdateRapidRuleExceptionRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "RuleID": _required(params.rule_id),
        "Body": _required(params.body),
    })


def validate_get_waf_mode_request(params) -> str | None:
    """Validate GetWAFModeRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_waf_mode_request(params) -> str | None:
    """Validate UpdateWAFModeRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_ip_geo_request(params) -> str | None:
    """Validate GetIPGeoRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_ip_geo_request(params) -> str | None:
    """Validate UpdateIPGeoRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_ip_geo_protection_request(params) -> str | None:
    """Validate GetIPGeoProtectionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_ip_geo_protection_request(params) -> str | None:
    """Validate UpdateIPGeoProtectionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_rate_protection_request(params) -> str | None:
    """Validate GetRateProtectionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_rate_protection_request(params) -> str | None:
    """Validate UpdateRateProtectionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_reputation_protection_request(params) -> str | None:
    """Validate GetReputationProtectionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_reputation_protection_request(params) -> str | None:
    """Validate UpdateReputationProtectionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_waf_protection_request(params) -> str | None:
    """Validate GetWAFProtectionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_waf_protection_request(params) -> str | None:
    """Validate UpdateWAFProtectionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_slow_post_protection_settings_request(params) -> str | None:
    """Validate GetSlowPostProtectionSettingsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_slow_post_protection_request(params) -> str | None:
    """Validate GetSlowPostProtectionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_slow_post_protections_request(params) -> str | None:
    """Validate GetSlowPostProtectionsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_slow_post_protection_request(params) -> str | None:
    """Validate UpdateSlowPostProtectionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_slow_post_protection_setting_request(params) -> str | None:
    """Validate UpdateSlowPostProtectionSettingRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_ip_geo_protections_request(params) -> str | None:
    """Validate GetIPGeoProtectionsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_rate_protections_request(params) -> str | None:
    """Validate GetRateProtectionsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_reputation_protections_request(params) -> str | None:
    """Validate GetReputationProtectionsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_remove_reputation_protection_request(params) -> str | None:
    """Validate RemoveReputationProtectionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_malware_policy_request(params) -> str | None:
    """Validate GetMalwarePolicyRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "MalwarePolicyID": _required(params.malware_policy_id),
    })


def validate_get_malware_policies_request(params) -> str | None:
    """Validate GetMalwarePoliciesRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
    })


def validate_create_malware_policy_request(params) -> str | None:
    """Validate CreateMalwarePolicyRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "Policy": _required(params.policy),
    })


def validate_update_malware_policy_request(params) -> str | None:
    """Validate UpdateMalwarePolicyRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "MalwarePolicyID": _required(params.malware_policy_id),
        "Policy": _required(params.policy),
    })


def validate_remove_malware_policy_request(params) -> str | None:
    """Validate RemoveMalwarePolicyRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "MalwarePolicyID": _required(params.malware_policy_id),
    })


def validate_get_malware_policy_actions_request(params) -> str | None:
    """Validate GetMalwarePolicyActionsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_malware_policy_action_request(params) -> str | None:
    """Validate UpdateMalwarePolicyActionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "MalwarePolicyID": _required(params.malware_policy_id),
        "Action": _required(params.action),
        "UnscannedAction": _required(params.unscanned_action),
    })


def validate_update_malware_policy_actions_request(params) -> str | None:
    """Validate UpdateMalwarePolicyActionsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
        "MalwarePolicyActions": _required(params.malware_policy_actions),
    })


def validate_get_malware_content_types_request(params) -> str | None:
    """Validate GetMalwareContentTypesRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_malware_protection_request(params) -> str | None:
    """Validate GetMalwareProtectionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_malware_protections_request(params) -> str | None:
    """Validate GetMalwareProtectionsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_malware_protection_request(params) -> str | None:
    """Validate UpdateMalwareProtectionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_api_endpoints_request(params) -> str | None:
    """Validate GetApiEndpointsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_api_hostname_coverage_match_targets_request(params) -> str | None:
    """Validate GetApiHostnameCoverageMatchTargetsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_api_hostname_coverage_overlapping_request(params) -> str | None:
    """Validate GetApiHostnameCoverageOverlappingRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_api_request_constraints_request(params) -> str | None:
    """Validate GetApiRequestConstraintsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_api_request_constraints_request(params) -> str | None:
    """Validate UpdateApiRequestConstraintsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_remove_api_request_constraints_request(params) -> str | None:
    """Validate RemoveApiRequestConstraintsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_api_constraints_protection_request(params) -> str | None:
    """Validate GetAPIConstraintsProtectionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_api_constraints_protection_request(params) -> str | None:
    """Validate UpdateAPIConstraintsProtectionRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_wap_selected_hostnames_request(params) -> str | None:
    """Validate GetWAPSelectedHostnamesRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "SecurityPolicyID": _required(params.version),
    })


def validate_update_wap_selected_hostnames_request(params) -> str | None:
    """Validate UpdateWAPSelectedHostnamesRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "SecurityPolicyID": _required(params.version),
    })


def validate_get_wap_bypass_network_lists_request(params) -> str | None:
    """Validate GetWAPBypassNetworkListsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_wap_bypass_network_lists_request(params) -> str | None:
    """Validate UpdateWAPBypassNetworkListsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_remove_wap_bypass_network_lists_request(params) -> str | None:
    """Validate RemoveWAPBypassNetworkListsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_siem_settings_request(params) -> str | None:
    """Validate GetSiemSettingsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_siem_settings_request(params) -> str | None:
    """Validate UpdateSiemSettingsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_remove_siem_settings_request(params) -> str | None:
    """Validate RemoveSiemSettingsRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_selected_hostname_request(params) -> str | None:
    """Validate GetSelectedHostnameRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_selected_hostname_request(params) -> str | None:
    """Validate UpdateSelectedHostnameRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_host_move_validation_request(params) -> str | None:
    """Validate GetHostMoveValidationRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "Network": _required_in(
            params.network,
            ("PRODUCTION", "STAGING"),
            "must be a valid value",
        ),
    })


def validate_create_activations_with_host_move_request(params) -> str | None:
    """Validate CreateActivationsWithHostMoveRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "ConfigVersion": _required(params.config_version),
        "Action": _required(params.action),
        "Network": _required_in(
            params.network,
            ("PRODUCTION", "STAGING"),
            "must be a valid value",
        ),
    })


def validate_get_export_configuration_request(params) -> str | None:
    """Validate GetExportConfigurationRequest."""
    return _validate_parsed({
        "Source": _in_values(
            params.source,
            ("TF",),
            f"value '{params.source}' is invalid. Must be one of: 'TF' or empty",
        ),
    })


def validate_get_version_notes_request(params) -> str | None:
    """Validate GetVersionNotesRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_version_notes_request(params) -> str | None:
    """Validate UpdateVersionNotesRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_threat_intel_request(params) -> str | None:
    """Validate GetThreatIntelRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_update_threat_intel_request(params) -> str | None:
    """Validate UpdateThreatIntelRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_tuning_recommendations_request(params) -> str | None:
    """Validate GetTuningRecommendationsRequest."""
    return _validate_required({
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


def validate_get_attack_group_recommendations_request(params) -> str | None:
    """Validate GetAttackGroupRecommendationsRequest."""
    return _validate_required({
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


def validate_get_rule_recommendations_request(params) -> str | None:
    """Validate GetRuleRecommendationsRequest."""
    return _validate_required({
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


def validate_get_advanced_settings_logging_request(params) -> str | None:
    """Validate GetAdvancedSettingsLoggingRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_advanced_settings_logging_request(params) -> str | None:
    """Validate UpdateAdvancedSettingsLoggingRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_remove_advanced_settings_logging_request(params) -> str | None:
    """Validate RemoveAdvancedSettingsLoggingRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_advanced_settings_ase_penalty_box_request(params) -> str | None:
    """Validate GetAdvancedSettingsAsePenaltyBoxRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_advanced_settings_ase_penalty_box_request(params) -> str | None:
    """Validate UpdateAdvancedSettingsAsePenaltyBoxRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_advanced_settings_attack_payload_logging_request(params) -> str | None:
    """Validate GetAdvancedSettingsAttackPayloadLoggingRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_advanced_settings_attack_payload_logging_request(params) -> str | None:
    """Validate UpdateAdvancedSettingsAttackPayloadLoggingRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_remove_advanced_settings_attack_payload_logging_request(params) -> str | None:
    """Validate RemoveAdvancedSettingsAttackPayloadLoggingRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_advanced_settings_evasive_path_match_request(params) -> str | None:
    """Validate GetAdvancedSettingsEvasivePathMatchRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_advanced_settings_evasive_path_match_request(params) -> str | None:
    """Validate UpdateAdvancedSettingsEvasivePathMatchRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_remove_advanced_settings_evasive_path_match_request(params) -> str | None:
    """Validate RemoveAdvancedSettingsEvasivePathMatchRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_advanced_settings_ja4_fingerprint_request(params) -> str | None:
    """Validate GetAdvancedSettingsJA4FingerprintRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_advanced_settings_ja4_fingerprint_request(params) -> str | None:
    """Validate UpdateAdvancedSettingsJA4FingerprintRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_remove_advanced_settings_ja4_fingerprint_request(params) -> str | None:
    """Validate RemoveAdvancedSettingsJA4FingerprintRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_advanced_settings_pii_learning_request(params) -> str | None:
    """Validate GetAdvancedSettingsPIILearningRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_advanced_settings_pii_learning_request(params) -> str | None:
    """Validate UpdateAdvancedSettingsPIILearningRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_advanced_settings_pragma_request(params) -> str | None:
    """Validate GetAdvancedSettingsPragmaRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_advanced_settings_pragma_request(params) -> str | None:
    """Validate UpdateAdvancedSettingsPragmaRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_advanced_settings_prefetch_request(params) -> str | None:
    """Validate GetAdvancedSettingsPrefetchRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_advanced_settings_prefetch_request(params) -> str | None:
    """Validate UpdateAdvancedSettingsPrefetchRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_advanced_settings_request_body_request(params) -> str | None:
    """Validate GetAdvancedSettingsRequestBodyRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_advanced_settings_request_body_request(params) -> str | None:
    """Validate UpdateAdvancedSettingsRequestBodyRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_remove_advanced_settings_request_body_request(params) -> str | None:
    """Validate RemoveAdvancedSettingsRequestBodyRequest."""
    return _validate_parsed({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_remove_advanced_settings_ase_penalty_box_request(params) -> str | None:
    """Validate RemoveAdvancedSettingsAsePenaltyBoxRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_get_selected_hostnames_request(params) -> str | None:
    """Validate GetSelectedHostnamesRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


def validate_update_selected_hostnames_request(params) -> str | None:
    """Validate UpdateSelectedHostnamesRequest."""
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
    })


# ============================================================================
# Missing validators added to achieve full parity with Go appsec Validate()
# ============================================================================

_VALID_EXCEPTION_PROTECTIONS = (
    "botmanagement", "ipgeo", "rate", "urlProtection", "slowpost",
    "customrules", "waf", "apirequestconstraints", "clientrep",
    "malwareprotection", "aprProtection",
)

_VALID_EXCEPTION_ACTION_TYPES = (
    "alert", "deny", "all_custom", "abort", "allow", "delay",
    "ignore", "monitor", "slow", "tarpit", "*",
)


def validate_exception(exc) -> str | None:
    """Validate Exception fields (SIEM exception configuration).

    Mirrors Go ``Exception.Validate()`` from siem_settings.go.
    Validates Protection against known protection types and each
    ActionType against valid action type values.
    """
    errors: dict[str, str | None] = {}
    errors["Protection"] = _required_in(
        exc.protection,
        _VALID_EXCEPTION_PROTECTIONS,
        (
            f"value '{exc.protection}' is invalid. Must be one of: "
            "'botmanagement', 'ipgeo', 'rate', 'urlProtection', "
            "'slowpost', 'customrules', 'waf', "
            "'apirequestconstraints', 'clientrep', "
            "'malwareprotection', 'aprProtection'"
        ),
    )
    req_err = _required(exc.action_types)
    if req_err is not None:
        errors["ActionTypes"] = req_err
    else:
        for action_type in exc.action_types:
            if action_type not in _VALID_EXCEPTION_ACTION_TYPES:
                errors["ActionTypes"] = (
                    f"value '{action_type}' is invalid. Must be "
                    f"one of: {list(_VALID_EXCEPTION_ACTION_TYPES)}"
                )
                break
    return _validate_required(errors)


def validate_get_evals_request(params) -> str | None:
    """Validate GetEvalsRequest.

    Mirrors Go ``GetEvalsRequest.Validate()`` from eval.go.
    """
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_get_rapid_rules_default_action_request(params) -> str | None:
    """Validate GetRapidRulesDefaultActionRequest.

    Mirrors Go ``GetRapidRulesDefaultActionRequest.Validate()``
    which delegates to ``GetRapidRulesRequest.Validate()``.
    """
    return validate_get_rapid_rules_request(params)


def validate_get_rapid_rules_status_request(params) -> str | None:
    """Validate GetRapidRulesStatusRequest.

    Mirrors Go ``GetRapidRulesStatusRequest.Validate()``
    which delegates to ``GetRapidRulesRequest.Validate()``.
    """
    return validate_get_rapid_rules_request(params)


def validate_get_waf_protections_request(params) -> str | None:
    """Validate GetWAFProtectionsRequest.

    Mirrors Go ``GetWAFProtectionsRequest.Validate()`` from
    waf_protection.go.
    """
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_penalty_box_conditions_payload(payload) -> str | None:
    """Validate PenaltyBoxConditionsPayload.

    Mirrors Go ``PenaltyBoxConditionsPayload.Validate()`` from
    penalty_box_conditions.go. Uses Required for ConditionOperator
    and NotNil for Conditions.
    """
    errors: dict[str, str | None] = {}
    errors["ConditionOperator"] = _required(
        payload.condition_operator
    )
    if payload.conditions is None:
        errors["Conditions"] = "is required"
    return _validate_required(errors)


def validate_remove_reputation_analysis_request(params) -> str | None:
    """Validate RemoveReputationAnalysisRequest.

    Mirrors Go ``RemoveReputationAnalysisRequest.Validate()`` from
    reputation_analysis.go.
    """
    return _validate_required({
        "ConfigID": _required(params.config_id),
        "Version": _required(params.version),
        "PolicyID": _required(params.policy_id),
    })


def validate_rule_ids(rule_ids) -> str | None:
    """Validate RuleIDs.

    Mirrors Go ``RuleIDs.Validate()`` from custom_rule.go.
    IDs is required and must contain at least 1 element.
    """
    errors: dict[str, str | None] = {}
    if not rule_ids.ids:
        errors["IDs"] = "cannot be blank"
    elif len(rule_ids.ids) < 1:
        errors["IDs"] = "the length must be no less than 1"
    return _validate_required(errors)


def validate_update_rapid_rule_action_lock_request_body(body) -> str | None:
    """Validate UpdateRapidRuleActionLockRequestBody.

    Mirrors Go ``UpdateRapidRuleActionLockRequestBody.Validate()``
    from rapid_rule.go. Uses NotNil for Enabled (bool pointer).
    """
    errors: dict[str, str | None] = {}
    if body.enabled is None:
        errors["Enabled"] = "is required"
    return _validate_required(errors)


def validate_update_rapid_rule_action_request_body(body) -> str | None:
    """Validate UpdateRapidRuleActionRequestBody.

    Mirrors Go ``UpdateRapidRuleActionRequestBody.Validate()``
    from rapid_rule.go. Action is required.
    """
    return _validate_required({
        "Action": _required(body.action),
    })


def validate_update_rapid_rules_default_action_request_body(body) -> str | None:
    """Validate UpdateRapidRulesDefaultActionRequestBody.

    Mirrors Go ``UpdateRapidRulesDefaultActionRequestBody.Validate()``
    from rapid_rule.go. Action is required.
    """
    return _validate_required({
        "Action": _required(body.action),
    })


def validate_update_rapid_rules_status_request_body(body) -> str | None:
    """Validate UpdateRapidRulesStatusRequestBody.

    Mirrors Go ``UpdateRapidRulesStatusRequestBody.Validate()``
    from rapid_rule.go. Uses NotNil for Enabled (bool pointer).
    """
    errors: dict[str, str | None] = {}
    if body.enabled is None:
        errors["Enabled"] = "is required"
    return _validate_required(errors)
