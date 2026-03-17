"""Request validation functions for the Client Lists API.

Mirrors the ``validate()`` methods on Go request structs from:
- ``pkg/clientlists/client_list.go`` (8 validators)
- ``pkg/clientlists/client_list_activation.go`` (4 private validators + 1 public)

Each function checks exactly the same required fields as its Go
counterpart and returns a formatted error string on failure or
``None`` when validation passes.
"""

from akamai.edgegrid.validation import parse_validation_errors
from akamai.edgegrid.clientlists import models


# ---------------------------------------------------------------------------
# Valid list types for GetClientListsRequest.Type validation
# Mirrors Go getValidListTypesAsInterface() in client_list.go
# ---------------------------------------------------------------------------
_VALID_LIST_TYPES = (
    models.IP,
    models.GEO,
    models.ASN,
    models.TLS_FINGERPRINT,
    models.FILE_HASH,
    models.USER,
    models.DOMAIN,
)


# ===================================================================
# Client List request validators (from client_list.go)
# ===================================================================


def validate_get_client_lists_request(
    params: models.GetClientListsRequest,
) -> str | None:
    """Validate a GetClientListsRequest.

    Mirrors Go ``GetClientListsRequest.validate()`` (client_list.go).
    Validates that any specified Type values are valid ClientListType
    values.

    Args:
        params: The request parameters to validate.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {}
    if params.type:
        for t in params.type:
            if t not in _VALID_LIST_TYPES:
                errors["Type"] = (
                    f"Invalid 'type' value(s) provided. "
                    f"Valid values are: {list(_VALID_LIST_TYPES)}"
                )
                break
    return parse_validation_errors(errors)


def validate_get_client_list_request(
    params: models.GetClientListRequest,
) -> str | None:
    """Validate a GetClientListRequest.

    Mirrors Go ``GetClientListRequest.validate()`` (client_list.go).
    Requires: ListID (non-empty string).

    Args:
        params: The request parameters to validate.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {}
    if not params.list_id:
        errors["ListID"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_create_client_list_request(
    params: models.CreateClientListRequest,
) -> str | None:
    """Validate a CreateClientListRequest.

    Mirrors Go ``CreateClientListRequest.validate()`` (client_list.go).
    Requires: Name, Type.

    Args:
        params: The request parameters to validate.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {}
    if not params.name:
        errors["Name"] = "cannot be blank"
    if not params.type:
        errors["Type"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_update_client_list_request(
    params: models.UpdateClientListRequest,
) -> str | None:
    """Validate an UpdateClientListRequest.

    Mirrors Go ``UpdateClientListRequest.validate()`` (client_list.go).
    Requires: ListID, Name.

    Note: The Go implementation validates ListID for both the "ListID"
    and "Name" fields — this is a known Go SDK bug that is mirrored
    here for parity.

    Args:
        params: The request parameters to validate.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {}
    if not params.list_id:
        errors["ListID"] = "cannot be blank"
    # Go bug: Name validation also checks ListID instead of Name
    if not params.list_id:
        errors["Name"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_update_client_list_items_request(
    params: models.UpdateClientListItemsRequest,
) -> str | None:
    """Validate an UpdateClientListItemsRequest.

    Mirrors Go ``UpdateClientListItemsRequest.validate()`` (client_list.go).
    Requires: ListID.

    Args:
        params: The request parameters to validate.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {}
    if not params.list_id:
        errors["ListID"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_delete_client_list_request(
    params: models.DeleteClientListRequest,
) -> str | None:
    """Validate a DeleteClientListRequest.

    Mirrors Go ``DeleteClientListRequest.validate()`` (client_list.go).
    Requires: ListID.

    Args:
        params: The request parameters to validate.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {}
    if not params.list_id:
        errors["ListID"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_translate_usernames_request(
    params: models.TranslateUsernamesRequest,
) -> str | None:
    """Validate a TranslateUsernamesRequest.

    Mirrors Go ``TranslateUsernamesRequest.validate()`` (client_list.go).
    Requires: The list itself must be non-empty (validation.Required +
    validation.Length(1, 0)).

    TranslateUsernamesRequest is ``list[str]``.

    Args:
        params: The list of usernames to translate.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {}
    if not params or len(params) < 1:
        errors["TranslateUsernamesRequest"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_get_client_list_items_request(
    params: models.GetClientListItemsRequest,
) -> str | None:
    """Validate a GetClientListItemsRequest.

    Mirrors Go ``GetClientListItemsRequest.validate()`` (client_list.go).
    Requires: ListID.

    Args:
        params: The request parameters to validate.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {}
    if not params.list_id:
        errors["ListID"] = "cannot be blank"
    return parse_validation_errors(errors)


# ===================================================================
# Activation request validators (from client_list_activation.go)
# ===================================================================


def validate_get_activation_request(
    params: models.GetActivationRequest,
) -> str | None:
    """Validate a GetActivationRequest.

    Mirrors Go ``GetActivationRequest.validate()``
    (client_list_activation.go).
    Requires: ActivationID.

    Args:
        params: The request parameters to validate.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {}
    if not params.activation_id:
        errors["ActivationID"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_get_activation_status_request(
    params: models.GetActivationStatusRequest,
) -> str | None:
    """Validate a GetActivationStatusRequest.

    Mirrors Go ``GetActivationStatusRequest.validate()``
    (client_list_activation.go).
    Requires: ListID, Network.

    Args:
        params: The request parameters to validate.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {}
    if not params.list_id:
        errors["ListID"] = "cannot be blank"
    if not params.network:
        errors["Network"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_create_activation_request(
    params: models.CreateActivationRequest,
) -> str | None:
    """Validate a CreateActivationRequest.

    Mirrors Go ``CreateActivationRequest.validate()``
    (client_list_activation.go).
    Requires: ListID, Network.

    Args:
        params: The request parameters to validate.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {}
    if not params.list_id:
        errors["ListID"] = "cannot be blank"
    if not params.network:
        errors["Network"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_create_deactivation_request(
    params: models.CreateActivationRequest,
) -> str | None:
    """Validate a CreateDeactivationRequest.

    Mirrors Go ``CreateDeactivationRequest.validate()``
    (client_list_activation.go).
    Requires: ListID, Network.

    Args:
        params: The request parameters to validate.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {}
    if not params.list_id:
        errors["ListID"] = "cannot be blank"
    if not params.network:
        errors["Network"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_activation_network(network: str) -> str | None:
    """Validate ActivationNetwork value.

    Mirrors Go ``ActivationNetwork.Validate()``
    (client_list_activation.go).
    The value must be either STAGING or PRODUCTION.

    Returns ``None`` if valid, otherwise an error string.

    Args:
        network: The activation network value to validate.

    Returns:
        Error string, or ``None`` if valid.
    """
    if network not in (models.STAGING, models.PRODUCTION):
        return (
            f"value '{network}' is invalid. Must be one of: "
            f"'{models.STAGING}' or '{models.PRODUCTION}'"
        )
    return None
