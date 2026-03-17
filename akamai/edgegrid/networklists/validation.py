"""Request validation functions for the Network Lists API.

Mirrors the ``Validate()`` methods on Go request structs from:
- ``pkg/networklists/network_list.go``
- ``pkg/networklists/activations.go``
- ``pkg/networklists/network_list_description.go``

Each function checks exactly the same required fields as its Go
counterpart and returns a formatted error string on failure or
``None`` when validation passes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from akamai.edgegrid.networklists import models


def validate_get_network_list_request(
    params: models.GetNetworkListRequest,
) -> str | None:
    """Validate a GetNetworkListRequest.

    Mirrors Go ``GetNetworkListRequest.Validate()``.
    Requires: UniqueID (non-empty string).

    Args:
        params: The request parameters to validate.

    Returns:
        A formatted error string if validation fails, ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not params.unique_id:
        errors["UniqueID"] = "cannot be blank"
    return _format_errors(errors)


def validate_create_network_list_request(
    params: models.CreateNetworkListRequest,
) -> str | None:
    """Validate a CreateNetworkListRequest.

    Mirrors Go ``CreateNetworkListRequest.Validate()``.
    Requires: Name (non-empty string).

    Args:
        params: The request parameters to validate.

    Returns:
        A formatted error string if validation fails, ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not params.name:
        errors["Name"] = "cannot be blank"
    return _format_errors(errors)


def validate_update_network_list_request(
    params: models.UpdateNetworkListRequest,
) -> str | None:
    """Validate an UpdateNetworkListRequest.

    Mirrors Go ``UpdateNetworkListRequest.Validate()``.
    Requires: Name (non-empty string).

    Args:
        params: The request parameters to validate.

    Returns:
        A formatted error string if validation fails, ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not params.name:
        errors["Name"] = "cannot be blank"
    return _format_errors(errors)


def validate_remove_network_list_request(
    params: models.RemoveNetworkListRequest,
) -> str | None:
    """Validate a RemoveNetworkListRequest.

    Mirrors Go ``RemoveNetworkListRequest.Validate()``.
    Requires: UniqueID (non-empty string).

    Args:
        params: The request parameters to validate.

    Returns:
        A formatted error string if validation fails, ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not params.unique_id:
        errors["UniqueID"] = "cannot be blank"
    return _format_errors(errors)


def validate_get_activations_request(
    params: models.GetActivationsRequest,
) -> str | None:
    """Validate a GetActivationsRequest.

    Mirrors Go ``GetActivationsRequest.Validate()``.
    Requires: UniqueID (non-empty string).

    Args:
        params: The request parameters to validate.

    Returns:
        A formatted error string if validation fails, ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not params.unique_id:
        errors["UniqueID"] = "cannot be blank"
    return _format_errors(errors)


def validate_get_activation_request(
    params: models.GetActivationRequest,
) -> str | None:
    """Validate a GetActivationRequest.

    Mirrors Go ``GetActivationRequest.Validate()``.
    Requires: ActivationID (non-zero integer).

    In Go, ``validation.Required`` applied to an ``int`` field checks
    that the value is non-zero.  Therefore ``ActivationID == 0`` fails
    validation, matching the behaviour of ``not params.activation_id``
    in Python (``0`` is falsy).

    Args:
        params: The request parameters to validate.

    Returns:
        A formatted error string if validation fails, ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not params.activation_id:
        errors["ActivationID"] = "cannot be blank"
    return _format_errors(errors)


def validate_get_network_list_description_request(
    params: models.GetNetworkListDescriptionRequest,
) -> str | None:
    """Validate a GetNetworkListDescriptionRequest.

    Mirrors Go ``GetNetworkListDescriptionRequest.Validate()``.
    Requires: UniqueID (non-empty string).

    Args:
        params: The request parameters to validate.

    Returns:
        A formatted error string if validation fails, ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not params.unique_id:
        errors["UniqueID"] = "cannot be blank"
    return _format_errors(errors)


def validate_update_network_list_description_request(
    params: models.UpdateNetworkListDescriptionRequest,
) -> str | None:
    """Validate an UpdateNetworkListDescriptionRequest.

    Mirrors Go ``UpdateNetworkListDescriptionRequest.Validate()``.
    Requires: UniqueID (non-empty string).

    Args:
        params: The request parameters to validate.

    Returns:
        A formatted error string if validation fails, ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not params.unique_id:
        errors["UniqueID"] = "cannot be blank"
    return _format_errors(errors)


def _format_errors(errors: dict[str, str]) -> str | None:
    """Format validation errors into a single string.

    Mirrors Go ``validation.Errors{...}.Filter()`` behaviour:

    * Returns ``None`` when the dict is empty (equivalent to Go
      returning ``nil``).
    * Sorts keys alphabetically for deterministic output, matching
      Go's ``ozzo-validation`` library which iterates map keys in
      sorted order when producing the error string.
    * Joins individual field errors with ``"; "`` separators.

    Args:
        errors: Mapping of field names to their error messages.

    Returns:
        A formatted error string, or ``None`` when there are no errors.
    """
    if not errors:
        return None
    parts = [f"{key}: {msg}" for key, msg in sorted(errors.items())]
    return "; ".join(parts)
