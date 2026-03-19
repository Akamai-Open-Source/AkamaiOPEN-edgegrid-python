"""Validation functions for Client Lists API requests.

Mirrors the ``validate()`` methods on Go request structs from:
- ``pkg/clientlists/client_list.go`` (8 validators)
- ``pkg/clientlists/client_list_activation.go`` (5 validators)

Each function enforces exactly the same constraints as its Go counterpart,
raising ``ErrStructValidation`` on failure or returning ``None`` when
validation passes.  Validation errors prevent HTTP requests from being made.
"""

from akamai.edgegrid.validation import parse_validation_errors
from akamai.edgegrid.clientlists.errors import ErrStructValidation
from akamai.edgegrid.clientlists import models


def _raise_on_errors(errors: dict[str, str | None]) -> None:
    """Format validation errors and raise ErrStructValidation if any exist.

    Uses ``parse_validation_errors()`` from the base validation module to
    format the errors dict into a human-readable multi-line string, then
    wraps it in ``ErrStructValidation``.

    Args:
        errors: A dict mapping field names to error messages.
                ``None`` values are filtered out by parse_validation_errors.
    """
    result = parse_validation_errors(errors)
    if result is not None:
        raise ErrStructValidation(f"struct validation: {result}")


# ===================================================================
# Client List request validators (from client_list.go)
# ===================================================================


def validate_get_client_lists_request(
    type_list: list[str] | None,
) -> None:
    """Validate GetClientListsRequest parameters.

    Mirrors Go ``GetClientListsRequest.validate()`` (client_list.go
    lines 494-500).

    If type list is provided, each value must be a valid ClientListType.
    Error message mirrors Go's ``fmt.Sprintf("Invalid 'type' value(s)
    provided. Valid values are: %s", listTypes)``.

    Args:
        type_list: List of client list type filter values, or ``None``.

    Raises:
        ErrStructValidation: If any type value is not in VALID_LIST_TYPES.
    """
    errors: dict[str, str | None] = {}
    if type_list:
        for t in type_list:
            if t not in models.VALID_LIST_TYPES:
                errors["Type"] = (
                    "Invalid 'type' value(s) provided. "
                    f"Valid values are: {models.VALID_LIST_TYPES}"
                )
                break
    _raise_on_errors(errors)


def validate_get_client_list_request(list_id: str) -> None:
    """Validate GetClientListRequest parameters.

    Mirrors Go ``GetClientListRequest.validate()`` (client_list.go
    lines 462-466).
    Requires: ListID (non-empty string).

    Args:
        list_id: The client list identifier.

    Raises:
        ErrStructValidation: If list_id is empty.
    """
    errors: dict[str, str | None] = {}
    if not list_id:
        errors["ListID"] = "cannot be blank"
    _raise_on_errors(errors)


def validate_create_client_list_request(
    name: str, type_val: str,
) -> None:
    """Validate CreateClientListRequest parameters.

    Mirrors Go ``CreateClientListRequest.validate()`` (client_list.go
    lines 481-486).
    Requires: Name, Type.

    Args:
        name: The name for the new client list.
        type_val: The type of the new client list.

    Raises:
        ErrStructValidation: If name or type_val is empty.
    """
    errors: dict[str, str | None] = {}
    if not name:
        errors["Name"] = "cannot be blank"
    if not type_val:
        errors["Type"] = "cannot be blank"
    _raise_on_errors(errors)


def validate_update_client_list_request(list_id: str) -> None:
    """Validate UpdateClientListRequest parameters.

    Mirrors Go ``UpdateClientListRequest.validate()`` (client_list.go
    lines 468-473).
    Requires: ListID, Name.

    Note: The Go implementation validates ``v.ListID`` for both the
    ``"ListID"`` and ``"Name"`` validation keys — this is a known Go
    SDK bug that is mirrored here for exact parity.

    Args:
        list_id: The client list identifier (checked for both ListID
                 and Name fields per Go bug).

    Raises:
        ErrStructValidation: If list_id is empty.
    """
    errors: dict[str, str | None] = {}
    if not list_id:
        errors["ListID"] = "cannot be blank"
    # Go bug: Name validation also checks v.ListID instead of v.Name
    if not list_id:
        errors["Name"] = "cannot be blank"
    _raise_on_errors(errors)


def validate_update_client_list_items_request(list_id: str) -> None:
    """Validate UpdateClientListItemsRequest parameters.

    Mirrors Go ``UpdateClientListItemsRequest.validate()``
    (client_list.go lines 475-479).
    Requires: ListID.

    Args:
        list_id: The client list identifier.

    Raises:
        ErrStructValidation: If list_id is empty.
    """
    errors: dict[str, str | None] = {}
    if not list_id:
        errors["ListID"] = "cannot be blank"
    _raise_on_errors(errors)


def validate_delete_client_list_request(list_id: str) -> None:
    """Validate DeleteClientListRequest parameters.

    Mirrors Go ``DeleteClientListRequest.validate()`` (client_list.go
    lines 488-492).
    Requires: ListID.

    Args:
        list_id: The client list identifier.

    Raises:
        ErrStructValidation: If list_id is empty.
    """
    errors: dict[str, str | None] = {}
    if not list_id:
        errors["ListID"] = "cannot be blank"
    _raise_on_errors(errors)


def validate_translate_usernames_request(
    usernames: list[str],
) -> None:
    """Validate TranslateUsernamesRequest parameters.

    Mirrors Go ``TranslateUsernamesRequest.validate()`` (client_list.go
    lines 502-509).
    Requires: non-empty list with at least one element
    (``validation.Required`` + ``validation.Length(1, 0)``).

    Args:
        usernames: The list of usernames to translate.

    Raises:
        ErrStructValidation: If usernames is empty or None.
    """
    errors: dict[str, str | None] = {}
    if not usernames or len(usernames) < 1:
        errors["TranslateUsernamesRequest"] = "cannot be blank"
    _raise_on_errors(errors)


def validate_get_client_list_items_request(list_id: str) -> None:
    """Validate GetClientListItemsRequest parameters.

    Mirrors Go ``GetClientListItemsRequest.validate()`` (client_list.go
    lines 511-515).
    Requires: ListID.

    Args:
        list_id: The client list identifier.

    Raises:
        ErrStructValidation: If list_id is empty.
    """
    errors: dict[str, str | None] = {}
    if not list_id:
        errors["ListID"] = "cannot be blank"
    _raise_on_errors(errors)


# ===================================================================
# Activation request validators (from client_list_activation.go)
# ===================================================================


def validate_get_activation_request(activation_id: int) -> None:
    """Validate GetActivationRequest parameters.

    Mirrors Go ``GetActivationRequest.validate()``
    (client_list_activation.go lines 114-118).
    Requires: ActivationID (non-zero).  For integers,
    ``validation.Required`` means the value must not be zero.

    Args:
        activation_id: The activation identifier.

    Raises:
        ErrStructValidation: If activation_id is zero or falsy.
    """
    errors: dict[str, str | None] = {}
    if not activation_id:
        errors["ActivationID"] = "cannot be blank"
    _raise_on_errors(errors)


def validate_get_activation_status_request(
    list_id: str, network: str,
) -> None:
    """Validate GetActivationStatusRequest parameters.

    Mirrors Go ``GetActivationStatusRequest.validate()``
    (client_list_activation.go lines 120-125).
    Requires: ListID, Network.

    Args:
        list_id: The client list identifier.
        network: The activation network.

    Raises:
        ErrStructValidation: If list_id or network is empty.
    """
    errors: dict[str, str | None] = {}
    if not list_id:
        errors["ListID"] = "cannot be blank"
    if not network:
        errors["Network"] = "cannot be blank"
    _raise_on_errors(errors)


def validate_create_activation_request(
    list_id: str, network: str,
) -> None:
    """Validate CreateActivationRequest parameters.

    Mirrors Go ``CreateActivationRequest.validate()``
    (client_list_activation.go lines 127-132).
    Requires: ListID, Network.

    Args:
        list_id: The client list identifier.
        network: The activation network.

    Raises:
        ErrStructValidation: If list_id or network is empty.
    """
    errors: dict[str, str | None] = {}
    if not list_id:
        errors["ListID"] = "cannot be blank"
    if not network:
        errors["Network"] = "cannot be blank"
    _raise_on_errors(errors)


def validate_create_deactivation_request(
    list_id: str, network: str,
) -> None:
    """Validate CreateDeactivationRequest parameters.

    Mirrors Go ``CreateDeactivationRequest.validate()``
    (client_list_activation.go lines 134-139).
    Requires: ListID, Network.

    Args:
        list_id: The client list identifier.
        network: The activation network.

    Raises:
        ErrStructValidation: If list_id or network is empty.
    """
    errors: dict[str, str | None] = {}
    if not list_id:
        errors["ListID"] = "cannot be blank"
    if not network:
        errors["Network"] = "cannot be blank"
    _raise_on_errors(errors)


def validate_activation_network(network: str) -> None:
    """Validate ActivationNetwork value.

    Mirrors Go ``ActivationNetwork.Validate()``
    (client_list_activation.go lines 142-144).
    Uses ``validation.In(Staging, Production)`` — must be one of the
    two valid ``ActivationNetwork`` constants.

    Args:
        network: The activation network value to validate.

    Raises:
        ValueError: If network is not STAGING or PRODUCTION.
    """
    if network not in (models.STAGING, models.PRODUCTION):
        raise ValueError(f"must be a valid value: {network}")
