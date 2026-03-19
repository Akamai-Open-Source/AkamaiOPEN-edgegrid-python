"""Validation functions for Cloud Access Manager API requests.

Mirrors Go validation methods from ``pkg/cloudaccess`` request types using
``edgegriderr.ParseValidationErrors`` style error formatting.  Each exported
function corresponds to a Go request struct's ``Validate()`` method.
"""

from akamai.edgegrid.cloudaccess import models
from akamai.edgegrid.validation import parse_validation_errors


# ===================================================================
# Access Key request validators (from access_key.go)
# ===================================================================


def validate_get_access_key_status_request(
    request: models.GetAccessKeyStatusRequest,
) -> str | None:
    """Validate a GetAccessKeyStatusRequest.

    Mirrors Go ``GetAccessKeyStatusRequest.Validate()``
    (access_key.go lines 107-111).

    Rules:
        - RequestID: Required

    Args:
        request: The request to validate.

    Returns:
        Formatted validation error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {
        "RequestID": _validate_required_int(request.request_id),
    }
    return parse_validation_errors(errors)


def validate_create_access_key_request(
    request: models.CreateAccessKeyRequest,
) -> str | None:
    """Validate a CreateAccessKeyRequest.

    Mirrors Go ``CreateAccessKeyRequest.Validate()``
    (access_key.go lines 114-124) combined with
    ``SecureNetwork.Validate()`` (access_key.go lines 127-132)
    for network configuration constraints.

    Rules:
        - AccessKeyName: Required
        - AuthenticationMethod: Required, In(AuthAWS, AuthGOOG,
          AuthAOS, AuthAVMCloudinary)
        - ContractID: Required
        - CloudAccessKeyID: Required (from Credentials)
        - CloudSecretAccessKey: Required (from Credentials)
        - GroupID: Required
        - SecurityNetwork: Required, In(NetworkEnhanced, NetworkStandard)
        - AdditionalCDN: When present, In(ChinaCDN, RussiaCDN)

    Args:
        request: The request to validate.

    Returns:
        Formatted validation error string, or ``None`` if valid.
    """
    net_cfg: models.SecureNetwork = request.network_configuration
    errors: dict[str, str | None] = {
        "AccessKeyName": _validate_required_str(
            request.access_key_name,
        ),
        "AuthenticationMethod": _validate_required_in_str(
            request.authentication_method,
            (
                models.AuthAWS,
                models.AuthGOOG,
                models.AuthAOS,
                models.AuthAVMCloudinary,
            ),
        ),
        "ContractID": _validate_required_str(request.contract_id),
        "CloudAccessKeyID": _validate_required_str(
            request.credentials.cloud_access_key_id,
        ),
        "CloudSecretAccessKey": _validate_required_str(
            request.credentials.cloud_secret_access_key,
        ),
        "GroupID": _validate_required_int(request.group_id),
        "SecurityNetwork": _validate_required_in_str(
            net_cfg.security_network,
            (models.NetworkEnhanced, models.NetworkStandard),
        ),
    }
    # Validate AdditionalCDN when present — mirrors
    # Go SecureNetwork.Validate() AdditionalCDN constraint.
    cdn_error = _validate_optional_in(
        net_cfg.additional_cdn,
        (models.ChinaCDN, models.RussiaCDN),
    )
    if cdn_error is not None:
        errors["AdditionalCDN"] = cdn_error
    return parse_validation_errors(errors)


def validate_access_key_request(
    request: models.AccessKeyRequest,
) -> str | None:
    """Validate an AccessKeyRequest.

    Mirrors Go ``AccessKeyRequest.Validate()``
    (access_key.go lines 135-139).

    Rules:
        - AccessKeyUID: Required

    Args:
        request: The request to validate.

    Returns:
        Formatted validation error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {
        "AccessKeyUID": _validate_required_int(
            request.access_key_uid,
        ),
    }
    return parse_validation_errors(errors)


def validate_update_access_key_request(
    request: models.UpdateAccessKeyRequest,
) -> str | None:
    """Validate an UpdateAccessKeyRequest.

    Mirrors Go ``UpdateAccessKeyRequest.Validate()``
    (access_key.go lines 142-146).

    Rules:
        - AccessKeyName: Required, Length(1, 50)

    Args:
        request: The request to validate.

    Returns:
        Formatted validation error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {
        "AccessKeyName": _validate_required_length_str(
            request.access_key_name, 1, 50,
        ),
    }
    return parse_validation_errors(errors)


# ===================================================================
# Access Key Version request validators (from access_key_version.go)
# ===================================================================


def validate_get_access_key_version_status_request(
    request: models.GetAccessKeyVersionStatusRequest,
) -> str | None:
    """Validate a GetAccessKeyVersionStatusRequest.

    Mirrors Go ``GetAccessKeyVersionStatusRequest.Validate()``
    (access_key_version.go lines 100-104).

    Rules:
        - RequestID: Required

    Args:
        request: The request to validate.

    Returns:
        Formatted validation error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {
        "RequestID": _validate_required_int(request.request_id),
    }
    return parse_validation_errors(errors)


def validate_create_access_key_version_request(
    request: models.CreateAccessKeyVersionRequest,
) -> str | None:
    """Validate a CreateAccessKeyVersionRequest.

    Mirrors Go ``CreateAccessKeyVersionRequest.Validate()``
    (access_key_version.go lines 107-112) with nested body
    validation from ``CreateAccessKeyVersionRequestBody.Validate()``
    (access_key_version.go lines 115-120).

    Rules:
        - AccessKeyUID: Required
        - Body: Required (non-zero struct) + nested field validation

    Args:
        request: The request to validate.

    Returns:
        Formatted validation error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {
        "AccessKeyUID": _validate_required_int(
            request.access_key_uid,
        ),
    }
    # Validate Body — mirrors Go validation.Required on a
    # Validatable struct.  The zero-value check fires first;
    # when the struct is non-zero, individual fields are
    # validated via the inner Validate() call.
    body: models.CreateAccessKeyVersionRequestBody = request.body
    body_is_zero = (
        not body.cloud_access_key_id
        and not body.cloud_secret_access_key
    )
    if body_is_zero:
        errors["Body"] = "cannot be blank"
    else:
        body_error = _validate_access_key_version_body(body)
        if body_error is not None:
            errors["Body"] = body_error
    return parse_validation_errors(errors)


def validate_get_access_key_version_request(
    request: models.GetAccessKeyVersionRequest,
) -> str | None:
    """Validate a GetAccessKeyVersionRequest.

    Mirrors Go ``GetAccessKeyVersionRequest.Validate()``
    (access_key_version.go lines 123-128).

    Rules:
        - AccessKeyUID: Required
        - Version: Required

    Args:
        request: The request to validate.

    Returns:
        Formatted validation error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {
        "AccessKeyUID": _validate_required_int(
            request.access_key_uid,
        ),
        "Version": _validate_required_int(request.version),
    }
    return parse_validation_errors(errors)


def validate_list_access_key_versions_request(
    request: models.ListAccessKeyVersionsRequest,
) -> str | None:
    """Validate a ListAccessKeyVersionsRequest.

    Mirrors Go ``ListAccessKeyVersionsRequest.Validate()``
    (access_key_version.go lines 131-135).

    Rules:
        - AccessKeyUID: Required

    Args:
        request: The request to validate.

    Returns:
        Formatted validation error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {
        "AccessKeyUID": _validate_required_int(
            request.access_key_uid,
        ),
    }
    return parse_validation_errors(errors)


def validate_delete_access_key_version_request(
    request: models.DeleteAccessKeyVersionRequest,
) -> str | None:
    """Validate a DeleteAccessKeyVersionRequest.

    Mirrors Go ``DeleteAccessKeyVersionRequest.Validate()``
    (access_key_version.go lines 138-143).

    Rules:
        - AccessKeyUID: Required
        - Version: Required

    Args:
        request: The request to validate.

    Returns:
        Formatted validation error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {
        "AccessKeyUID": _validate_required_int(
            request.access_key_uid,
        ),
        "Version": _validate_required_int(request.version),
    }
    return parse_validation_errors(errors)


# ===================================================================
# Property request validators (from properties.go)
# ===================================================================


def validate_lookup_properties_request(
    request: models.LookupPropertiesRequest,
) -> str | None:
    """Validate a LookupPropertiesRequest.

    Mirrors Go ``LookupPropertiesRequest.Validate()``
    (properties.go lines 79-84).

    Rules:
        - Version: Required
        - AccessKeyUID: Required

    Args:
        request: The request to validate.

    Returns:
        Formatted validation error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {
        "Version": _validate_required_int(request.version),
        "AccessKeyUID": _validate_required_int(
            request.access_key_uid,
        ),
    }
    return parse_validation_errors(errors)


def validate_get_async_properties_lookup_id_request(
    request: models.GetAsyncPropertiesLookupIDRequest,
) -> str | None:
    """Validate a GetAsyncPropertiesLookupIDRequest.

    Mirrors Go ``GetAsyncPropertiesLookupIDRequest.Validate()``
    (properties.go lines 87-92).

    Rules:
        - Version: Required
        - AccessKeyUID: Required

    Args:
        request: The request to validate.

    Returns:
        Formatted validation error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {
        "Version": _validate_required_int(request.version),
        "AccessKeyUID": _validate_required_int(
            request.access_key_uid,
        ),
    }
    return parse_validation_errors(errors)


def validate_perform_async_properties_lookup_request(
    request: models.PerformAsyncPropertiesLookupRequest,
) -> str | None:
    """Validate a PerformAsyncPropertiesLookupRequest.

    Mirrors Go ``PerformAsyncPropertiesLookupRequest.Validate()``
    (properties.go lines 95-99).

    Rules:
        - LookupID: Required

    Args:
        request: The request to validate.

    Returns:
        Formatted validation error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {
        "LookupID": _validate_required_int(request.lookup_id),
    }
    return parse_validation_errors(errors)


# ===================================================================
# Private validation helpers — mirror ozzo-validation rule semantics
# ===================================================================


def _validate_required_str(value: str) -> str | None:
    """Check that a string value is non-empty.

    Mirrors Go ``validation.Required`` for string types.
    An empty string ``""`` is considered the zero value.
    """
    if not value:
        return "cannot be blank"
    return None


def _validate_required_int(value: int) -> str | None:
    """Check that an integer value is non-zero.

    Mirrors Go ``validation.Required`` for int64 types.
    The value ``0`` is considered the zero value.
    """
    if not value:
        return "cannot be blank"
    return None


def _validate_required_in_str(
    value: str,
    allowed: tuple[str, ...],
) -> str | None:
    """Check Required then In for a string value.

    Mirrors Go ``validation.Required`` followed by
    ``validation.In()``.  Rules are applied sequentially —
    if Required fails, In is not checked.

    Args:
        value: The string to validate.
        allowed: Tuple of valid values.

    Returns:
        Error message string, or ``None`` if valid.
    """
    if not value:
        return "cannot be blank"
    if value not in allowed:
        return "must be a valid value"
    return None


def _validate_required_length_str(
    value: str,
    min_len: int,
    max_len: int,
) -> str | None:
    """Check Required then Length for a string value.

    Mirrors Go ``validation.Required`` followed by
    ``validation.Length(min, max)``.  Rules are applied
    sequentially — if Required fails, Length is not checked.

    Args:
        value: The string to validate.
        min_len: Minimum allowed length (inclusive).
        max_len: Maximum allowed length (inclusive).

    Returns:
        Error message string, or ``None`` if valid.
    """
    if not value:
        return "cannot be blank"
    if not min_len <= len(value) <= max_len:
        return f"the length must be between {min_len} and {max_len}"
    return None


def _validate_optional_in(
    value: str | None,
    allowed: tuple[str, ...],
) -> str | None:
    """Check In constraint only when value is present.

    Mirrors Go ``validation.When(value != nil, validation.In())``.
    When value is ``None``, validation is skipped.

    Args:
        value: The optional string to validate.
        allowed: Tuple of valid values.

    Returns:
        Error message string, or ``None`` if valid or skipped.
    """
    if value is None:
        return None
    if value not in allowed:
        return "must be a valid value"
    return None


def _validate_access_key_version_body(
    body: models.CreateAccessKeyVersionRequestBody,
) -> str | None:
    """Validate CreateAccessKeyVersionRequestBody fields.

    Mirrors Go ``CreateAccessKeyVersionRequestBody.Validate()``
    (access_key_version.go lines 115-120).

    Called when the Body struct is non-zero (passes Required).

    Args:
        body: The request body to validate.

    Returns:
        Formatted validation error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {
        "CloudAccessKeyID": _validate_required_str(
            body.cloud_access_key_id,
        ),
        "CloudSecretAccessKey": _validate_required_str(
            body.cloud_secret_access_key,
        ),
    }
    return parse_validation_errors(errors)
