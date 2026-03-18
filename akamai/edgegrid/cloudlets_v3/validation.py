"""Request validation functions for Cloudlets V3 API.

Mirrors EVERY ``Validate()`` method defined across Go source files:
``policy.go``, ``policy_version.go``, ``policy_activation.go``,
``policy_property.go``, and ``match_rule.go``.

Each Go ``Validate()`` method uses ``ozzo-validation`` with
``edgegriderr.ParseValidationErrors()``.  The Python equivalent uses
the shared ``parse_validation_errors()`` from
``akamai.edgegrid.validation``.
"""
# pylint: disable=too-many-lines

import re

from akamai.edgegrid.validation import parse_validation_errors
from akamai.edgegrid.cloudlets_v3 import models

# ---------------------------------------------------------------------------
# Constants — compiled regex patterns & valid enum values
# ---------------------------------------------------------------------------

_POLICY_NAME_PATTERN = re.compile(r"^[a-z_A-Z0-9]+$")

_VALID_CLOUDLET_TYPES = ("AP", "AS", "CD", "ER", "FR", "IG")

_VALID_MATCH_TYPES_AP = frozenset({
    "header", "hostname", "path", "extension", "query", "cookie",
    "deviceCharacteristics", "clientip", "continent", "countrycode",
    "regioncode", "protocol", "method", "proxy",
})

_VALID_MATCH_TYPES_AS = _VALID_MATCH_TYPES_AP | {"range", "regex"}

_VALID_MATCH_TYPES_ER = _VALID_MATCH_TYPES_AP | {"regex"}

_VALID_MATCH_TYPES_FR = _VALID_MATCH_TYPES_AP | {"regex"}

_VALID_MATCH_TYPES_RC = _VALID_MATCH_TYPES_AP

_VALID_MATCH_OPERATORS = ("contains", "exists", "equals")

_VALID_CHECK_IPS = (
    "CONNECTING_IP", "XFF_HEADERS", "CONNECTING_IP XFF_HEADERS",
)

_VALID_NETWORKS = ("STAGING", "PRODUCTION")

_VALID_STATUS_CODES = (301, 302, 303, 307, 308)

_VALID_USE_RELATIVE_URLS = ("none", "copy_scheme_hostname", "relative_url")

_VALID_ALLOW_DENY = ("allow", "deny", "denybranded")


# ---------------------------------------------------------------------------
# Private helpers — type check validators
# ---------------------------------------------------------------------------


def _pass_through_percent_validation(value):
    """Validate PassThroughPercent custom rule.

    Mirrors Go ``passThroughPercentValidation`` from match_rule.go
    lines 555-570.

    Args:
        value: The pass-through percent value (``float | None``).

    Returns:
        Error message string, or ``None`` if valid.
    """
    if value is None:
        return "cannot be blank"
    if not isinstance(value, (int, float)):
        return (
            f"type {type(value).__name__} is invalid. "
            "Must be *float64"
        )
    if value < -1:
        return "must be no less than -1"
    if value > 100:
        return "must be no greater than 100"
    return None


def _object_match_value_simple_or_object_validation(value):
    """Validate ObjectMatchValue is simple or object type.

    Mirrors Go ``objectMatchValueSimpleOrObjectValidation`` from
    match_rule.go lines 531-541.
    """
    if value is None:
        return None
    if isinstance(
        value,
        (models.ObjectMatchValueObject, models.ObjectMatchValueSimple),
    ):
        return None
    return (
        f"type {type(value).__name__} is invalid. "
        "Must be one of: 'simple' or 'object'"
    )


def _object_match_value_simple_or_range_or_object_validation(value):
    """Validate ObjectMatchValue is simple, range, or object type.

    Mirrors Go ``objectMatchValueSimpleOrRangeOrObjectValidation``
    from match_rule.go lines 543-553.
    """
    if value is None:
        return None
    if isinstance(
        value,
        (
            models.ObjectMatchValueObject,
            models.ObjectMatchValueSimple,
            models.ObjectMatchValueRange,
        ),
    ):
        return None
    return (
        f"type {type(value).__name__} is invalid. "
        "Must be one of: 'simple', 'range' or 'object'"
    )


# ---------------------------------------------------------------------------
# Private helpers — match type error message generators
# ---------------------------------------------------------------------------


def _match_type_error_ap(match_type):
    """MatchType error for AP/PR/RC criteria."""
    return (
        f"value '{match_type}' is invalid. Must be one of: "
        "'header', 'hostname', 'path', 'extension', 'query', "
        "'cookie', 'deviceCharacteristics', 'clientip', "
        "'continent', 'countrycode', 'regioncode', 'protocol', "
        "'method', 'proxy'"
    )


def _match_type_error_as(match_type):
    """MatchType error for AS criteria."""
    return (
        f"value '{match_type}' is invalid. Must be one of: "
        "'header', 'hostname', 'path', 'extension', 'query', "
        "'range', 'regex', 'cookie', 'deviceCharacteristics', "
        "'clientip', 'continent', 'countrycode', 'regioncode', "
        "'protocol', 'method', 'proxy'"
    )


def _match_type_error_er(match_type):
    """MatchType error for ER criteria."""
    return (
        f"value '{match_type}' is invalid. Must be one of: "
        "'header', 'hostname', 'path', 'extension', 'query', "
        "'regex', 'cookie', 'deviceCharacteristics', 'clientip', "
        "'continent', 'countrycode', 'regioncode', 'protocol', "
        "'method', 'proxy' or '' (empty)"
    )


def _match_type_error_fr(match_type):
    """MatchType error for FR criteria."""
    return (
        f"value '{match_type}' is invalid. Must be one of: "
        "'header', 'hostname', 'path', 'extension', 'query', "
        "'regex', 'cookie', 'deviceCharacteristics', 'clientip', "
        "'continent', 'countrycode', 'regioncode', 'protocol', "
        "'method', 'proxy'"
    )


# ---------------------------------------------------------------------------
# Private helpers — common match criteria validation
# ---------------------------------------------------------------------------


def _validate_match_criteria_errors(  # pylint: disable=too-many-branches
    criteria,
    valid_match_types,
    match_type_required,
    match_type_error_fn,
    omv_validator,
):
    """Common match-criteria validation logic shared by all cloudlet types.

    Returns a dict of ``{field_name: error_message}`` or ``None``.
    """
    errors: dict = {}
    match_type = criteria.match_type
    match_value = criteria.match_value
    omv = criteria.object_match_value

    # MatchType -------------------------------------------------------
    if match_type_required:
        if not match_type:
            errors["MatchType"] = "cannot be blank"
        elif match_type not in valid_match_types:
            errors["MatchType"] = match_type_error_fn(match_type)
    else:
        if match_type and match_type not in valid_match_types:
            errors["MatchType"] = match_type_error_fn(match_type)

    # MatchValue — rules in order: Length, Required.When, Empty.When --
    mv_err = None
    if match_value and len(match_value) > 8192:
        mv_err = "the length must be between 1 and 8192"
    if mv_err is None and not match_value and omv is None:
        mv_err = "cannot be blank when ObjectMatchValue is blank"
    if mv_err is None and match_value and omv is not None:
        mv_err = "must be blank when ObjectMatchValue is set"
    if mv_err is not None:
        errors["MatchValue"] = mv_err

    # MatchOperator ---------------------------------------------------
    match_op = criteria.match_operator
    if match_op and match_op not in _VALID_MATCH_OPERATORS:
        errors["MatchOperator"] = (
            f"value '{match_op}' is invalid. Must be one of: "
            "'contains', 'exists', 'equals' or '' (empty)"
        )

    # CheckIPs --------------------------------------------------------
    check_ips = criteria.check_ips
    if check_ips and check_ips not in _VALID_CHECK_IPS:
        errors["CheckIPs"] = (
            f"value '{check_ips}' is invalid. Must be one of: "
            "'CONNECTING_IP', 'XFF_HEADERS', "
            "'CONNECTING_IP XFF_HEADERS' or '' (empty)"
        )

    # ObjectMatchValue — rules in order: Required.When, Empty.When, By
    omv_err = None
    if not match_value and omv is None:
        omv_err = "cannot be blank when MatchValue is blank"
    if omv_err is None and match_value and omv is not None:
        omv_err = "must be blank when MatchValue is set"
    if omv_err is None and omv is not None:
        omv_err = omv_validator(omv)
    if omv_err is not None:
        errors["ObjectMatchValue"] = omv_err

    return errors if errors else None


# ---------------------------------------------------------------------------
# Private helpers — body validation (returns raw error dict)
# ---------------------------------------------------------------------------


def _validate_update_policy_body_errors(body):
    """Return raw errors dict for UpdatePolicyRequestBody validation.

    Mirrors Go ``UpdatePolicyRequestBody.Validate()`` (uses .Filter()).
    """
    errors: dict = {}
    if body.group_id == 0:
        errors["GroupID"] = "cannot be blank"
    desc = body.description
    if desc is not None and desc and len(desc) > 255:
        errors["Description"] = "the length must be no more than 255"
    return errors if errors else None


def _validate_clone_policy_body_errors(body):
    """Return raw errors dict for ClonePolicyRequestBody validation.

    Mirrors Go ``ClonePolicyRequestBody.Validate()`` (uses .Filter()).
    """
    errors: dict = {}
    new_name = body.new_name
    if not new_name:
        errors["NewName"] = "cannot be blank"
    elif len(new_name) > 64:
        errors["NewName"] = "the length must be no more than 64"
    elif not _POLICY_NAME_PATTERN.match(new_name):
        errors["NewName"] = (
            f"value '{new_name}' is invalid. "
            "Must be of format: ^[a-z_A-Z0-9]+$"
        )
    return errors if errors else None


# =========================================================================
# Policy validations (from policy.go)
# =========================================================================


def validate_list_policies_request(request) -> str | None:
    """Validate ListPoliciesRequest.

    Mirrors Go ``ListPoliciesRequest.Validate()`` from policy.go
    lines 146-151.
    """
    errors: dict = {}
    if request.page != 0 and request.page < 0:
        errors["Page"] = "must be no less than 0"
    if request.size != 0 and request.size < 10:
        errors["Size"] = "must be no less than 10"
    return parse_validation_errors(errors)


def validate_create_policy_request(request) -> str | None:
    """Validate CreatePolicyRequest.

    Mirrors Go ``CreatePolicyRequest.Validate()`` from policy.go
    lines 154-164.
    """
    errors: dict = {}

    # CloudletType: Required + In(AP,AS,CD,ER,FR,IG)
    cloudlet_type = request.cloudlet_type
    if not cloudlet_type:
        errors["CloudletType"] = "cannot be blank"
    elif cloudlet_type not in _VALID_CLOUDLET_TYPES:
        errors["CloudletType"] = (
            f"value '{cloudlet_type}' is invalid. Must be one of: "
            "'AP', 'AS', 'CD', 'ER', 'FR', 'IG'"
        )

    # Description: Length(0, 255) on optional *string
    desc = request.description
    if desc is not None and desc and len(desc) > 255:
        errors["Description"] = "the length must be no more than 255"

    # GroupID: Required
    if request.group_id == 0:
        errors["GroupID"] = "cannot be blank"

    # Name: Required + Length(0, 64) + Match(pattern)
    name = request.name
    if not name:
        errors["Name"] = "cannot be blank"
    elif len(name) > 64:
        errors["Name"] = "the length must be no more than 64"
    elif not _POLICY_NAME_PATTERN.match(name):
        errors["Name"] = (
            f"value '{name}' is invalid. "
            "Must be of format: ^[a-z_A-Z0-9]+$"
        )

    # PolicyType: In(SHARED) — no Required
    policy_type = request.policy_type
    if policy_type and policy_type != "SHARED":
        errors["PolicyType"] = (
            f"value '{policy_type}' is invalid. Must be 'SHARED'"
        )

    return parse_validation_errors(errors)


def validate_delete_policy_request(request) -> str | None:
    """Validate DeletePolicyRequest.

    Mirrors Go ``DeletePolicyRequest.Validate()`` from policy.go
    lines 167-171.
    """
    errors: dict = {}
    if request.policy_id == 0:
        errors["PolicyID"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_get_policy_request(request) -> str | None:
    """Validate GetPolicyRequest.

    Mirrors Go ``GetPolicyRequest.Validate()`` from policy.go
    lines 174-178.
    """
    errors: dict = {}
    if request.policy_id == 0:
        errors["PolicyID"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_update_policy_request(request) -> str | None:
    """Validate UpdatePolicyRequest.

    Mirrors Go ``UpdatePolicyRequest.Validate()`` from policy.go
    lines 181-186.
    """
    errors: dict = {}
    if request.policy_id == 0:
        errors["PolicyID"] = "cannot be blank"
    if request.body is None:
        errors["Body"] = "cannot be blank"
    else:
        body_errors = _validate_update_policy_body_errors(request.body)
        if body_errors:
            errors["Body"] = body_errors
    return parse_validation_errors(errors)


def validate_update_policy_request_body(body) -> str | None:
    """Validate UpdatePolicyRequestBody.

    Mirrors Go ``UpdatePolicyRequestBody.Validate()`` from policy.go
    lines 189-194.  Uses ``.Filter()`` directly.
    """
    errors = _validate_update_policy_body_errors(body) or {}
    return parse_validation_errors(errors)


def validate_clone_policy_request(request) -> str | None:
    """Validate ClonePolicyRequest.

    Mirrors Go ``ClonePolicyRequest.Validate()`` from policy.go
    lines 197-202.
    """
    errors: dict = {}
    if request.policy_id == 0:
        errors["PolicyID"] = "cannot be blank"
    if request.body is None:
        errors["Body"] = "cannot be blank"
    else:
        body_errors = _validate_clone_policy_body_errors(request.body)
        if body_errors:
            errors["Body"] = body_errors
    return parse_validation_errors(errors)


def validate_clone_policy_request_body(body) -> str | None:
    """Validate ClonePolicyRequestBody.

    Mirrors Go ``ClonePolicyRequestBody.Validate()`` from policy.go
    lines 205-210.  Uses ``.Filter()`` directly.
    """
    errors = _validate_clone_policy_body_errors(body) or {}
    return parse_validation_errors(errors)


# =========================================================================
# Policy version validations (from policy_version.go)
# =========================================================================


def validate_list_policy_versions_request(request) -> str | None:
    """Validate ListPolicyVersionsRequest.

    Mirrors Go ``ListPolicyVersionsRequest.Validate()`` from
    policy_version.go lines 107-114.
    """
    errors: dict = {}
    if request.page != 0 and request.page < 0:
        errors["Page"] = "must be no less than 0"
    if request.policy_id == 0:
        errors["PolicyID"] = "cannot be blank"
    if request.size != 0 and request.size < 10:
        errors["Size"] = "must be no less than 10"
    return parse_validation_errors(errors)


def validate_create_policy_version_request(request) -> str | None:
    """Validate CreatePolicyVersionRequest.

    Mirrors Go ``CreatePolicyVersionRequest.Validate()`` from
    policy_version.go lines 117-123 with cascading rule validation.
    """
    errors: dict = {}
    cpv = request.create_policy_version
    desc = cpv.description if cpv is not None else None
    match_rules = cpv.match_rules if cpv is not None else None

    if desc is not None and desc and len(desc) > 255:
        errors["Description"] = "the length must be no more than 255"

    # Validate match rules list AND individual rules
    if match_rules is not None and len(match_rules) > 0:
        match_err = validate_match_rules(match_rules)
        if match_err is not None:
            return match_err  # Return match rule errors directly

    if request.policy_id == 0:
        errors["PolicyID"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_update_policy_version_request(request) -> str | None:
    """Validate UpdatePolicyVersionRequest.

    Mirrors Go ``UpdatePolicyVersionRequest.Validate()`` from
    policy_version.go lines 126-133.
    """
    errors: dict = {}
    upv = request.update_policy_version
    desc = upv.description if upv is not None else None
    match_rules = upv.match_rules if upv is not None else None

    if desc is not None and desc and len(desc) > 255:
        errors["Description"] = "the length must be no more than 255"
    if (
        match_rules is not None
        and len(match_rules) > 0
        and len(match_rules) > 5000
    ):
        errors["MatchRules"] = "the length must be no more than 5000"
    if request.policy_id == 0:
        errors["PolicyID"] = "cannot be blank"
    if request.policy_version == 0:
        errors["PolicyVersion"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_delete_policy_version_request(request) -> str | None:
    """Validate DeletePolicyVersionRequest.

    Mirrors Go ``DeletePolicyVersionRequest.Validate()`` from
    policy_version.go lines 136-141.
    """
    errors: dict = {}
    if request.policy_id == 0:
        errors["PolicyID"] = "cannot be blank"
    if request.policy_version == 0:
        errors["PolicyVersion"] = "cannot be blank"
    return parse_validation_errors(errors)


# =========================================================================
# Policy activation validations (from policy_activation.go)
# =========================================================================


def validate_list_policy_activations_request(request) -> str | None:
    """Validate ListPolicyActivationsRequest.

    Mirrors Go ``ListPolicyActivationsRequest.Validate()`` from
    policy_activation.go lines 116-122.
    """
    errors: dict = {}
    if request.page != 0 and request.page < 0:
        errors["Page"] = "must be no less than 0"
    if request.policy_id == 0:
        errors["PolicyID"] = "cannot be blank"
    if request.size != 0 and request.size < 10:
        errors["Size"] = "must be no less than 10"
    return parse_validation_errors(errors)


def validate_get_policy_activation_request(request) -> str | None:
    """Validate GetPolicyActivationRequest.

    Mirrors Go ``GetPolicyActivationRequest.Validate()`` from
    policy_activation.go lines 125-130.
    """
    errors: dict = {}
    if request.activation_id == 0:
        errors["ActivationID"] = "cannot be blank"
    if request.policy_id == 0:
        errors["PolicyID"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_activate_policy_request(request) -> str | None:
    """Validate ActivatePolicyRequest.

    Mirrors Go ``ActivatePolicyRequest.Validate()`` from
    policy_activation.go lines 133-140.
    """
    errors: dict = {}
    network = request.network
    if not network:
        errors["Network"] = "cannot be blank"
    elif network not in _VALID_NETWORKS:
        errors["Network"] = (
            f"value '{network}' is invalid. "
            "Must be one of: 'STAGING' or 'PRODUCTION'"
        )
    if request.policy_id == 0:
        errors["PolicyID"] = "cannot be blank"
    if request.policy_version == 0:
        errors["PolicyVersion"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_deactivate_policy_request(request) -> str | None:
    """Validate DeactivatePolicyRequest.

    Mirrors Go ``DeactivatePolicyRequest.Validate()`` from
    policy_activation.go lines 143-150.
    """
    errors: dict = {}
    network = request.network
    if not network:
        errors["Network"] = "cannot be blank"
    elif network not in _VALID_NETWORKS:
        errors["Network"] = (
            f"value '{network}' is invalid. "
            "Must be one of: 'STAGING' or 'PRODUCTION'"
        )
    if request.policy_id == 0:
        errors["PolicyID"] = "cannot be blank"
    if request.policy_version == 0:
        errors["PolicyVersion"] = "cannot be blank"
    return parse_validation_errors(errors)


# =========================================================================
# Policy property validations (from policy_property.go)
# =========================================================================


def validate_list_active_policy_properties_request(
    request,
) -> str | None:
    """Validate ListActivePolicyPropertiesRequest.

    Mirrors Go ``ListActivePolicyPropertiesRequest.Validate()`` from
    policy_property.go lines 61-67.
    """
    errors: dict = {}
    if request.page != 0 and request.page < 0:
        errors["Page"] = "must be no less than 0"
    if request.policy_id == 0:
        errors["PolicyID"] = "cannot be blank"
    if request.size != 0 and request.size < 10:
        errors["Size"] = "must be no less than 10"
    return parse_validation_errors(errors)


# =========================================================================
# Match rules validation (from match_rule.go)
# =========================================================================


def validate_match_rules(match_rules) -> str | None:
    """Validate MatchRules list and each individual rule.

    Mirrors Go ``MatchRules.Validate()`` from match_rule.go
    lines 314-321 which calls rule.Validate() for each element.
    """
    if match_rules is None or len(match_rules) == 0:
        return None

    errors: dict = {}
    if len(match_rules) > 5000:
        errors["MatchRules"] = "the length must be no more than 5000"

    _type_to_validator = {
        "apMatchRule": validate_match_rule_ap,
        "asMatchRule": validate_match_rule_as,
        "cdMatchRule": validate_match_rule_pr,
        "erMatchRule": validate_match_rule_er,
        "frMatchRule": validate_match_rule_fr,
        "igMatchRule": validate_match_rule_rc,
    }

    for i, rule in enumerate(match_rules):
        rule_type = getattr(rule, "type", "")
        validator_fn = _type_to_validator.get(rule_type)
        if validator_fn is None:
            # Fallback: try to detect by class name
            cls_name = type(rule).__name__
            _cls_to_validator = {
                "MatchRuleAP": validate_match_rule_ap,
                "MatchRuleAS": validate_match_rule_as,
                "MatchRulePR": validate_match_rule_pr,
                "MatchRuleER": validate_match_rule_er,
                "MatchRuleFR": validate_match_rule_fr,
                "MatchRuleRC": validate_match_rule_rc,
            }
            validator_fn = _cls_to_validator.get(cls_name)
        if validator_fn is not None:
            rule_err = validator_fn(rule)
            if rule_err is not None:
                errors[f"MatchRules[{i}]"] = (
                    "{\n"
                    + "\n".join(
                        "\t" + line for line in rule_err.split("\n")
                    )
                    + "\n}"
                )
    if not errors:
        return None
    parts = []
    for key in sorted(errors.keys()):
        parts.append(f"{key}: {errors[key]}")
    return "\n".join(parts)


# =========================================================================
# Match rule validations (from match_rule.go)
# =========================================================================


def validate_match_rule_ap(rule) -> str | None:
    """Validate MatchRuleAP.

    Mirrors Go ``MatchRuleAP.Validate()`` from match_rule.go
    lines 324-335.
    """
    errors: dict = {}

    # Type: Required + In(apMatchRule)
    rule_type = rule.type
    if not rule_type:
        errors["Type"] = "cannot be blank"
    elif rule_type != "apMatchRule":
        errors["Type"] = (
            f"value '{rule_type}' is invalid. "
            "Must be: 'apMatchRule'"
        )

    # End: Min(0)
    if rule.end != 0 and rule.end < 0:
        errors["End"] = "must be no less than 0"

    # MatchURL: Length(0, 8192)
    if rule.match_url and len(rule.match_url) > 8192:
        errors["MatchURL"] = "the length must be no more than 8192"

    # Matches: validate each MatchCriteriaAP
    if rule.matches:
        matches_errors: dict = {}
        for i, match in enumerate(rule.matches):
            match_errs = _validate_match_criteria_errors(
                match,
                _VALID_MATCH_TYPES_AP,
                False,
                _match_type_error_ap,
                _object_match_value_simple_or_object_validation,
            )
            if match_errs:
                matches_errors[str(i)] = match_errs
        if matches_errors:
            errors["Matches"] = matches_errors

    # Name: Length(0, 8192)
    if rule.name and len(rule.name) > 8192:
        errors["Name"] = "the length must be no more than 8192"

    # PassThroughPercent: custom validation
    ptp_err = _pass_through_percent_validation(
        rule.pass_through_percent,
    )
    if ptp_err is not None:
        errors["PassThroughPercent"] = ptp_err

    # Start: Min(0)
    if rule.start != 0 and rule.start < 0:
        errors["Start"] = "must be no less than 0"

    return parse_validation_errors(errors)


def validate_match_rule_as(  # pylint: disable=too-many-branches
    rule,
) -> str | None:
    """Validate MatchRuleAS.

    Mirrors Go ``MatchRuleAS.Validate()`` from match_rule.go
    lines 338-351.
    """
    errors: dict = {}

    # Type: Required + In(asMatchRule)
    rule_type = rule.type
    if not rule_type:
        errors["Type"] = "cannot be blank"
    elif rule_type != "asMatchRule":
        errors["Type"] = (
            f"value '{rule_type}' is invalid. "
            "Must be: 'asMatchRule'"
        )

    # End: Min(0)
    if rule.end != 0 and rule.end < 0:
        errors["End"] = "must be no less than 0"

    # ForwardSettings: Required
    fs = rule.forward_settings
    if fs is None:
        errors["ForwardSettings"] = "cannot be blank"

    # ForwardSettings.OriginID: Length(0, 8192)
    origin_id = fs.origin_id if fs is not None else ""
    if origin_id and len(origin_id) > 8192:
        errors["ForwardSettings.OriginID"] = (
            "the length must be no more than 8192"
        )

    # ForwardSettings.PathAndQS: Length(1, 8192)
    path_and_qs = fs.path_and_qs if fs is not None else ""
    if path_and_qs and len(path_and_qs) > 8192:
        errors["ForwardSettings.PathAndQS"] = (
            "the length must be between 1 and 8192"
        )

    # MatchURL: Length(0, 8192)
    if rule.match_url and len(rule.match_url) > 8192:
        errors["MatchURL"] = "the length must be no more than 8192"

    # Matches: validate each MatchCriteriaAS
    if rule.matches:
        matches_errors: dict = {}
        for i, match in enumerate(rule.matches):
            match_errs = _validate_match_criteria_errors(
                match,
                _VALID_MATCH_TYPES_AS,
                False,
                _match_type_error_as,
                _object_match_value_simple_or_range_or_object_validation,
            )
            if match_errs:
                matches_errors[str(i)] = match_errs
        if matches_errors:
            errors["Matches"] = matches_errors

    # Name: Length(0, 8192)
    if rule.name and len(rule.name) > 8192:
        errors["Name"] = "the length must be no more than 8192"

    # Start: Min(0)
    if rule.start != 0 and rule.start < 0:
        errors["Start"] = "must be no less than 0"

    return parse_validation_errors(errors)


def validate_match_rule_pr(  # pylint: disable=too-many-branches
    rule,
) -> str | None:
    """Validate MatchRulePR.

    Mirrors Go ``MatchRulePR.Validate()`` from match_rule.go
    lines 354-368.
    """
    errors: dict = {}

    # Type: Required + In(cdMatchRule)
    rule_type = rule.type
    if not rule_type:
        errors["Type"] = "cannot be blank"
    elif rule_type != "cdMatchRule":
        errors["Type"] = (
            f"value '{rule_type}' is invalid. "
            "Must be: 'cdMatchRule'"
        )

    # End: Min(0)
    if rule.end != 0 and rule.end < 0:
        errors["End"] = "must be no less than 0"

    # ForwardSettings: Required
    fs = rule.forward_settings
    if fs is None:
        errors["ForwardSettings"] = "cannot be blank"

    # ForwardSettings.OriginID: Required + Length(0, 8192)
    origin_id = fs.origin_id if fs is not None else ""
    if not origin_id:
        errors["ForwardSettings.OriginID"] = "cannot be blank"
    elif len(origin_id) > 8192:
        errors["ForwardSettings.OriginID"] = (
            "the length must be no more than 8192"
        )

    # ForwardSettings.Percent: Required + Min(1) + Max(100)
    percent = fs.percent if fs is not None else 0
    if percent == 0:
        errors["ForwardSettings.Percent"] = "cannot be blank"
    elif percent < 1:
        errors["ForwardSettings.Percent"] = "must be no less than 1"
    elif percent > 100:
        errors["ForwardSettings.Percent"] = (
            "must be no greater than 100"
        )

    # MatchURL: Length(0, 8192)
    if rule.match_url and len(rule.match_url) > 8192:
        errors["MatchURL"] = "the length must be no more than 8192"

    # Matches: validate each MatchCriteriaPR
    if rule.matches:
        matches_errors: dict = {}
        for i, match in enumerate(rule.matches):
            match_errs = _validate_match_criteria_errors(
                match,
                _VALID_MATCH_TYPES_AP,
                False,
                _match_type_error_ap,
                _object_match_value_simple_or_object_validation,
            )
            if match_errs:
                matches_errors[str(i)] = match_errs
        if matches_errors:
            errors["Matches"] = matches_errors

    # Matches/MatchesAlways mutual exclusivity
    if rule.matches_always and rule.matches and len(rule.matches) > 0:
        errors["Matches/MatchesAlways"] = (
            'only one of [ "Matches", "MatchesAlways" ] '
            "can be specified"
        )

    # Name: Length(0, 8192)
    if rule.name and len(rule.name) > 8192:
        errors["Name"] = "the length must be no more than 8192"

    # Start: Min(0)
    if rule.start != 0 and rule.start < 0:
        errors["Start"] = "must be no less than 0"

    return parse_validation_errors(errors)


def validate_match_rule_er(  # pylint: disable=too-many-branches
    rule,
) -> str | None:
    """Validate MatchRuleER.

    Mirrors Go ``MatchRuleER.Validate()`` from match_rule.go
    lines 371-387.
    """
    errors: dict = {}

    # Type: Required + In(erMatchRule)
    rule_type = rule.type
    if not rule_type:
        errors["Type"] = "cannot be blank"
    elif rule_type != "erMatchRule":
        errors["Type"] = (
            f"value '{rule_type}' is invalid. "
            "Must be: 'erMatchRule'"
        )

    # End: Min(0)
    if rule.end != 0 and rule.end < 0:
        errors["End"] = "must be no less than 0"

    # MatchURL: Length(0, 8192)
    if rule.match_url and len(rule.match_url) > 8192:
        errors["MatchURL"] = "the length must be no more than 8192"

    # Matches: validate each MatchCriteriaER
    if rule.matches:
        matches_errors: dict = {}
        for i, match in enumerate(rule.matches):
            match_errs = _validate_match_criteria_errors(
                match,
                _VALID_MATCH_TYPES_ER,
                False,
                _match_type_error_er,
                _object_match_value_simple_or_object_validation,
            )
            if match_errs:
                matches_errors[str(i)] = match_errs
        if matches_errors:
            errors["Matches"] = matches_errors

    # Matches/MatchesAlways mutual exclusivity
    if rule.matches_always and rule.matches and len(rule.matches) > 0:
        errors["Matches/MatchesAlways"] = (
            'only one of [ "Matches", "MatchesAlways" ] '
            "can be specified"
        )

    # Name: Length(0, 8192)
    if rule.name and len(rule.name) > 8192:
        errors["Name"] = "the length must be no more than 8192"

    # RedirectURL: Required + Length(1, 8192)
    redirect_url = rule.redirect_url
    if not redirect_url:
        errors["RedirectURL"] = "cannot be blank"
    elif len(redirect_url) > 8192:
        errors["RedirectURL"] = (
            "the length must be between 1 and 8192"
        )

    # Start: Min(0)
    if rule.start != 0 and rule.start < 0:
        errors["Start"] = "must be no less than 0"

    # StatusCode: Required + In(301,302,303,307,308)
    status_code = rule.status_code
    if status_code == 0:
        errors["StatusCode"] = "cannot be blank"
    elif status_code not in _VALID_STATUS_CODES:
        errors["StatusCode"] = (
            f"value '{status_code}' is invalid. "
            "Must be one of: 301, 302, 303, 307 or 308"
        )

    # UseRelativeURL: In(none, copy_scheme_hostname, relative_url)
    use_rel = rule.use_relative_url
    if use_rel and use_rel not in _VALID_USE_RELATIVE_URLS:
        errors["UseRelativeURL"] = (
            f"value '{use_rel}' is invalid. Must be one of: "
            "'none', 'copy_scheme_hostname', 'relative_url' "
            "or '' (empty)"
        )

    return parse_validation_errors(errors)


def validate_match_rule_fr(  # pylint: disable=too-many-branches
    rule,
) -> str | None:
    """Validate MatchRuleFR.

    Mirrors Go ``MatchRuleFR.Validate()`` from match_rule.go
    lines 390-403.
    """
    errors: dict = {}

    # Type: Required + In(frMatchRule)
    rule_type = rule.type
    if not rule_type:
        errors["Type"] = "cannot be blank"
    elif rule_type != "frMatchRule":
        errors["Type"] = (
            f"value '{rule_type}' is invalid. "
            "Must be: 'frMatchRule'"
        )

    # End: Min(0)
    if rule.end != 0 and rule.end < 0:
        errors["End"] = "must be no less than 0"

    # ForwardSettings: Required
    fs = rule.forward_settings
    if fs is None:
        errors["ForwardSettings"] = "cannot be blank"

    # ForwardSettings.OriginID: Length(0, 8192)
    origin_id = fs.origin_id if fs is not None else ""
    if origin_id and len(origin_id) > 8192:
        errors["ForwardSettings.OriginID"] = (
            "the length must be no more than 8192"
        )

    # ForwardSettings.PathAndQS: Length(1, 8192)
    path_and_qs = fs.path_and_qs if fs is not None else ""
    if path_and_qs and len(path_and_qs) > 8192:
        errors["ForwardSettings.PathAndQS"] = (
            "the length must be between 1 and 8192"
        )

    # MatchURL: Length(0, 8192)
    if rule.match_url and len(rule.match_url) > 8192:
        errors["MatchURL"] = "the length must be no more than 8192"

    # Matches: validate each MatchCriteriaFR
    if rule.matches:
        matches_errors: dict = {}
        for i, match in enumerate(rule.matches):
            match_errs = _validate_match_criteria_errors(
                match,
                _VALID_MATCH_TYPES_FR,
                True,
                _match_type_error_fr,
                _object_match_value_simple_or_object_validation,
            )
            if match_errs:
                matches_errors[str(i)] = match_errs
        if matches_errors:
            errors["Matches"] = matches_errors

    # Name: Length(0, 8192)
    if rule.name and len(rule.name) > 8192:
        errors["Name"] = "the length must be no more than 8192"

    # Start: Min(0)
    if rule.start != 0 and rule.start < 0:
        errors["Start"] = "must be no less than 0"

    return parse_validation_errors(errors)


def validate_match_rule_rc(rule) -> str | None:
    """Validate MatchRuleRC.

    Mirrors Go ``MatchRuleRC.Validate()`` from match_rule.go
    lines 406-419.
    """
    errors: dict = {}

    # Type: Required + In(igMatchRule)
    rule_type = rule.type
    if not rule_type:
        errors["Type"] = "cannot be blank"
    elif rule_type != "igMatchRule":
        errors["Type"] = (
            f"value '{rule_type}' is invalid. "
            "Must be: 'igMatchRule'"
        )

    # AllowDeny: Required + In(allow, deny, denybranded)
    allow_deny = rule.allow_deny
    if not allow_deny:
        errors["AllowDeny"] = "cannot be blank"
    elif allow_deny not in _VALID_ALLOW_DENY:
        errors["AllowDeny"] = (
            f"value '{allow_deny}' is invalid. Must be one of: "
            "'allow', 'deny' or 'denybranded'"
        )

    # End: Min(0)
    if rule.end != 0 and rule.end < 0:
        errors["End"] = "must be no less than 0"

    # Matches: validate each MatchCriteriaRC
    if rule.matches:
        matches_errors: dict = {}
        for i, match in enumerate(rule.matches):
            match_errs = _validate_match_criteria_errors(
                match,
                _VALID_MATCH_TYPES_RC,
                True,
                _match_type_error_ap,
                _object_match_value_simple_or_object_validation,
            )
            if match_errs:
                matches_errors[str(i)] = match_errs
        if matches_errors:
            errors["Matches"] = matches_errors

    # Matches/MatchesAlways mutual exclusivity
    if rule.matches_always and rule.matches and len(rule.matches) > 0:
        errors["Matches/MatchesAlways"] = (
            'only one of [ "Matches", "MatchesAlways" ] '
            "can be specified"
        )

    # Name: Length(0, 8192)
    if rule.name and len(rule.name) > 8192:
        errors["Name"] = "the length must be no more than 8192"

    # Start: Min(0)
    if rule.start != 0 and rule.start < 0:
        errors["Start"] = "must be no less than 0"

    return parse_validation_errors(errors)


# =========================================================================
# Match criteria validations (from match_rule.go)
# =========================================================================


def validate_match_criteria_ap(criteria) -> str | None:
    """Validate MatchCriteriaAP.

    Mirrors Go ``MatchCriteriaAP.Validate()`` from match_rule.go
    lines 422-438.
    """
    errors = _validate_match_criteria_errors(
        criteria,
        _VALID_MATCH_TYPES_AP,
        False,
        _match_type_error_ap,
        _object_match_value_simple_or_object_validation,
    ) or {}
    return parse_validation_errors(errors)


def validate_match_criteria_as(criteria) -> str | None:
    """Validate MatchCriteriaAS.

    Mirrors Go ``MatchCriteriaAS.Validate()`` from match_rule.go
    lines 441-456.
    """
    errors = _validate_match_criteria_errors(
        criteria,
        _VALID_MATCH_TYPES_AS,
        False,
        _match_type_error_as,
        _object_match_value_simple_or_range_or_object_validation,
    ) or {}
    return parse_validation_errors(errors)


def validate_match_criteria_pr(criteria) -> str | None:
    """Validate MatchCriteriaPR.

    Mirrors Go ``MatchCriteriaPR.Validate()`` from match_rule.go
    lines 459-475.
    """
    errors = _validate_match_criteria_errors(
        criteria,
        _VALID_MATCH_TYPES_AP,
        False,
        _match_type_error_ap,
        _object_match_value_simple_or_object_validation,
    ) or {}
    return parse_validation_errors(errors)


def validate_match_criteria_er(criteria) -> str | None:
    """Validate MatchCriteriaER.

    Mirrors Go ``MatchCriteriaER.Validate()`` from match_rule.go
    lines 478-493.
    """
    errors = _validate_match_criteria_errors(
        criteria,
        _VALID_MATCH_TYPES_ER,
        False,
        _match_type_error_er,
        _object_match_value_simple_or_object_validation,
    ) or {}
    return parse_validation_errors(errors)


def validate_match_criteria_fr(criteria) -> str | None:
    """Validate MatchCriteriaFR.

    Mirrors Go ``MatchCriteriaFR.Validate()`` from match_rule.go
    lines 496-511.  MatchType is *Required* for FR.
    """
    errors = _validate_match_criteria_errors(
        criteria,
        _VALID_MATCH_TYPES_FR,
        True,
        _match_type_error_fr,
        _object_match_value_simple_or_object_validation,
    ) or {}
    return parse_validation_errors(errors)


def validate_match_criteria_rc(criteria) -> str | None:
    """Validate MatchCriteriaRC.

    Mirrors Go ``MatchCriteriaRC.Validate()`` from match_rule.go
    lines 514-529.  MatchType is *Required* for RC.
    """
    errors = _validate_match_criteria_errors(
        criteria,
        _VALID_MATCH_TYPES_RC,
        True,
        _match_type_error_ap,
        _object_match_value_simple_or_object_validation,
    ) or {}
    return parse_validation_errors(errors)


# =========================================================================
# ObjectMatchValue validations (from match_rule.go)
# =========================================================================


def validate_object_match_value_range(obj) -> str | None:
    """Validate ObjectMatchValueRange.

    Mirrors Go ``ObjectMatchValueRange.Validate()`` from match_rule.go
    lines 573-578.
    """
    errors: dict = {}
    obj_type = obj.type
    if obj_type and obj_type != "range":
        errors["Type"] = (
            f"value '{obj_type}' is invalid. Must be: 'range'"
        )
    return parse_validation_errors(errors)


def validate_object_match_value_simple(obj) -> str | None:
    """Validate ObjectMatchValueSimple.

    Mirrors Go ``ObjectMatchValueSimple.Validate()`` from match_rule.go
    lines 581-586.
    """
    errors: dict = {}
    obj_type = obj.type
    if obj_type and obj_type != "simple":
        errors["Type"] = (
            f"value '{obj_type}' is invalid. Must be: 'simple'"
        )
    return parse_validation_errors(errors)


def validate_object_match_value_object(obj) -> str | None:
    """Validate ObjectMatchValueObject.

    Mirrors Go ``ObjectMatchValueObject.Validate()`` from match_rule.go
    lines 589-595.
    """
    errors: dict = {}
    # Name: Required + Length(0, 8192)
    if not obj.name:
        errors["Name"] = "cannot be blank"
    elif len(obj.name) > 8192:
        errors["Name"] = "the length must be no more than 8192"
    # Type: Required + In(object)
    obj_type = obj.type
    if not obj_type:
        errors["Type"] = "cannot be blank"
    elif obj_type != "object":
        errors["Type"] = (
            f"value '{obj_type}' is invalid. Must be: 'object'"
        )
    return parse_validation_errors(errors)
