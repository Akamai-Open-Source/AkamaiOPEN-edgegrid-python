"""Request validation functions for the Account Protection API.

Mirrors Go ozzo-validation Validate() methods for each request struct
in the accountprotection package. Each function checks required fields
and returns a formatted error string or None if validation passes.

Go reference files:
- pkg/accountprotection/protected_operation.go (lines 112-159)
- pkg/accountprotection/general_settings.go (lines 44-60)
- pkg/accountprotection/user_risk_response_strategy.go (lines 37-51)
- pkg/accountprotection/user_allow_list_id.go (lines 46-68)
"""

from akamai.edgegrid.accountprotection import models


def _validate_required_fields(fields: dict[str, tuple]) -> str | None:
    """Validate that required fields are not empty or zero-valued.

    Mirrors Go's ozzo-validation pattern where validation.Required
    checks that a value is not the zero value for its type:
    - int fields must be non-zero
    - string fields must be non-empty
    - json (raw message) fields must not be None or empty

    Args:
        fields: Dict mapping Go PascalCase field name to a tuple of
                (value, field_type) where field_type is one of:
                'int' — must be non-zero,
                'str' — must be non-empty string,
                'json' — must not be None or empty.

    Returns:
        Formatted error string listing all invalid fields in
        alphabetical order separated by semicolons, matching
        ozzo-validation output format, or None if all fields pass.
    """
    errors: dict[str, str] = {}
    for field_name, (value, field_type) in fields.items():
        if field_type == "int" and (value is None or value == 0):
            errors[field_name] = "cannot be blank"
        elif field_type == "str" and (value is None or value == ""):
            errors[field_name] = "cannot be blank"
        elif field_type == "json" and (
            value is None
            or (isinstance(value, (str, bytes)) and len(value) == 0)
        ):
            errors[field_name] = "cannot be blank"

    if not errors:
        return None

    # Sort alphabetically to match Go's ozzo-validation Errors.Filter()
    # output, which iterates map keys in sorted order.
    parts = [f"{k}: {v}" for k, v in sorted(errors.items())]
    return "; ".join(parts)


# ===================================================================
# Protected Operation Validations
# (from protected_operation.go lines 112-159)
# ===================================================================


def validate_list_protected_operations_request(
    params: models.ListProtectedOperationsRequest,
) -> str | None:
    """Validate a ListProtectedOperationsRequest.

    Mirrors Go ListProtectedOperationsRequest.Validate() method.
    Checks: ConfigID (required int), SecurityPolicyID (required str),
    Version (required int).

    Args:
        params: The request to validate.

    Returns:
        Error message string if validation fails, None if valid.
    """
    return _validate_required_fields({
        "ConfigID": (params.config_id, "int"),
        "SecurityPolicyID": (params.security_policy_id, "str"),
        "Version": (params.version, "int"),
    })


def validate_get_protected_operation_by_id_request(
    params: models.GetProtectedOperationByIDRequest,
) -> str | None:
    """Validate a GetProtectedOperationByIDRequest.

    Mirrors Go GetProtectedOperationByIDRequest.Validate() method.
    Checks: ConfigID (required int), Version (required int),
    SecurityPolicyID (required str), OperationID (required str).

    Args:
        params: The request to validate.

    Returns:
        Error message string if validation fails, None if valid.
    """
    return _validate_required_fields({
        "ConfigID": (params.config_id, "int"),
        "Version": (params.version, "int"),
        "SecurityPolicyID": (params.security_policy_id, "str"),
        "OperationID": (params.operation_id, "str"),
    })


def validate_create_protected_operations_request(
    params: models.CreateProtectedOperationsRequest,
) -> str | None:
    """Validate a CreateProtectedOperationsRequest.

    Mirrors Go CreateProtectedOperationsRequest.Validate() method.
    Checks: ConfigID (required int), Version (required int),
    SecurityPolicyID (required str), JsonPayload (required json).

    Args:
        params: The request to validate.

    Returns:
        Error message string if validation fails, None if valid.
    """
    return _validate_required_fields({
        "ConfigID": (params.config_id, "int"),
        "Version": (params.version, "int"),
        "SecurityPolicyID": (params.security_policy_id, "str"),
        "JsonPayload": (params.json_payload, "json"),
    })


def validate_update_protected_operation_request(
    params: models.UpdateProtectedOperationRequest,
) -> str | None:
    """Validate an UpdateProtectedOperationRequest.

    Mirrors Go UpdateProtectedOperationRequest.Validate() method.
    Checks: ConfigID (required int), Version (required int),
    SecurityPolicyID (required str), OperationID (required str),
    JsonPayload (required json).

    Args:
        params: The request to validate.

    Returns:
        Error message string if validation fails, None if valid.
    """
    return _validate_required_fields({
        "ConfigID": (params.config_id, "int"),
        "Version": (params.version, "int"),
        "SecurityPolicyID": (params.security_policy_id, "str"),
        "OperationID": (params.operation_id, "str"),
        "JsonPayload": (params.json_payload, "json"),
    })


def validate_remove_protected_operation_request(
    params: models.RemoveProtectedOperationRequest,
) -> str | None:
    """Validate a RemoveProtectedOperationRequest.

    Mirrors Go RemoveProtectedOperationRequest.Validate() method.
    Checks: ConfigID (required int), Version (required int),
    SecurityPolicyID (required str), OperationID (required str).

    Args:
        params: The request to validate.

    Returns:
        Error message string if validation fails, None if valid.
    """
    return _validate_required_fields({
        "ConfigID": (params.config_id, "int"),
        "Version": (params.version, "int"),
        "SecurityPolicyID": (params.security_policy_id, "str"),
        "OperationID": (params.operation_id, "str"),
    })


# ===================================================================
# General Settings Validations
# (from general_settings.go lines 44-60)
# ===================================================================


def validate_get_general_settings_request(
    params: models.GetGeneralSettingsRequest,
) -> str | None:
    """Validate a GetGeneralSettingsRequest.

    Mirrors Go GetGeneralSettingsRequest.Validate() method.
    Checks: ConfigID (required int), Version (required int),
    SecurityPolicyID (required str).

    Args:
        params: The request to validate.

    Returns:
        Error message string if validation fails, None if valid.
    """
    return _validate_required_fields({
        "ConfigID": (params.config_id, "int"),
        "Version": (params.version, "int"),
        "SecurityPolicyID": (params.security_policy_id, "str"),
    })


def validate_upsert_general_settings_request(
    params: models.UpsertGeneralSettingsRequest,
) -> str | None:
    """Validate an UpsertGeneralSettingsRequest.

    Mirrors Go UpsertGeneralSettingsRequest.Validate() method.
    Checks: ConfigID (required int), Version (required int),
    SecurityPolicyID (required str), JsonPayload (required json).

    Args:
        params: The request to validate.

    Returns:
        Error message string if validation fails, None if valid.
    """
    return _validate_required_fields({
        "ConfigID": (params.config_id, "int"),
        "Version": (params.version, "int"),
        "SecurityPolicyID": (params.security_policy_id, "str"),
        "JsonPayload": (params.json_payload, "json"),
    })


# ===================================================================
# User Risk Response Strategy Validations
# (from user_risk_response_strategy.go lines 37-51)
# ===================================================================


def validate_get_user_risk_response_strategy_request(
    params: models.GetUserRiskResponseStrategyRequest,
) -> str | None:
    """Validate a GetUserRiskResponseStrategyRequest.

    Mirrors Go GetUserRiskResponseStrategyRequest.Validate() method.
    Checks: ConfigID (required int), Version (required int).

    Args:
        params: The request to validate.

    Returns:
        Error message string if validation fails, None if valid.
    """
    return _validate_required_fields({
        "ConfigID": (params.config_id, "int"),
        "Version": (params.version, "int"),
    })


def validate_upsert_user_risk_response_strategy_request(
    params: models.UpsertUserRiskResponseStrategyRequest,
) -> str | None:
    """Validate an UpsertUserRiskResponseStrategyRequest.

    Mirrors Go UpsertUserRiskResponseStrategyRequest.Validate() method.
    Checks: ConfigID (required int), Version (required int),
    JsonPayload (required json).

    Args:
        params: The request to validate.

    Returns:
        Error message string if validation fails, None if valid.
    """
    return _validate_required_fields({
        "ConfigID": (params.config_id, "int"),
        "Version": (params.version, "int"),
        "JsonPayload": (params.json_payload, "json"),
    })


# ===================================================================
# User Allow List ID Validations
# (from user_allow_list_id.go lines 46-68)
# ===================================================================


def validate_get_user_allow_list_id_request(
    params: models.GetUserAllowListIDRequest,
) -> str | None:
    """Validate a GetUserAllowListIDRequest.

    Mirrors Go GetUserAllowListIDRequest.Validate() method.
    Checks: ConfigID (required int), Version (required int).

    Args:
        params: The request to validate.

    Returns:
        Error message string if validation fails, None if valid.
    """
    return _validate_required_fields({
        "ConfigID": (params.config_id, "int"),
        "Version": (params.version, "int"),
    })


def validate_upsert_user_allow_list_id_request(
    params: models.UpsertUserAllowListIDRequest,
) -> str | None:
    """Validate an UpsertUserAllowListIDRequest.

    Mirrors Go UpsertUserAllowListIDRequest.Validate() method.
    Checks: ConfigID (required int), Version (required int),
    JsonPayload (required json).

    Args:
        params: The request to validate.

    Returns:
        Error message string if validation fails, None if valid.
    """
    return _validate_required_fields({
        "ConfigID": (params.config_id, "int"),
        "Version": (params.version, "int"),
        "JsonPayload": (params.json_payload, "json"),
    })


def validate_delete_user_allow_list_id_request(
    params: models.DeleteUserAllowListIDRequest,
) -> str | None:
    """Validate a DeleteUserAllowListIDRequest.

    Mirrors Go DeleteUserAllowListIDRequest.Validate() method.
    Checks: ConfigID (required int), Version (required int).

    Args:
        params: The request to validate.

    Returns:
        Error message string if validation fails, None if valid.
    """
    return _validate_required_fields({
        "ConfigID": (params.config_id, "int"),
        "Version": (params.version, "int"),
    })
