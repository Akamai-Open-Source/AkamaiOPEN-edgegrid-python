"""Request/response model dataclasses for the Network Lists API.

Mirrors Go structs from:
- pkg/networklists/network_list.go
- pkg/networklists/activations.go
- pkg/networklists/network_list_description.go
- pkg/networklists/network_list_subscription.go
"""
from __future__ import annotations

import dataclasses
import types
from dataclasses import dataclass, field
from typing import get_type_hints

# Field names ``type`` and ``list`` mirror Go JSON tags and intentionally
# shadow the Python built-ins within their dataclass scope.
# pylint: disable=redefined-builtin


def _snake_to_camel(name: str) -> str:
    """Convert a snake_case name to camelCase."""
    components = name.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def _unwrap_optional(type_hint: type) -> type:
    """Unwrap ``T | None`` to ``T``.

    Returns *type_hint* unchanged when it is not a union with ``None``.
    PEP 604 unions (``X | Y``) are ``types.UnionType`` instances — they
    expose ``__args__`` directly, unlike ``typing.Union`` which uses
    ``__origin__``.
    """
    if isinstance(type_hint, types.UnionType):
        non_none = [a for a in type_hint.__args__ if a is not types.NoneType]
        if len(non_none) == 1:
            return non_none[0]
    return type_hint


def _get_list_element_type(type_hint: type) -> type | None:
    """Return the element type from ``list[T]``, or ``None``."""
    origin = getattr(type_hint, "__origin__", None)
    if origin is list:
        args = getattr(type_hint, "__args__", ())
        if args:
            return args[0]
    return None


# ---------------------------------------------------------------------------
# Link helper dataclasses
# ---------------------------------------------------------------------------

@dataclass
class LinkInfo:
    """Hypermedia link with href and method.

    Mirrors Go ``LinkInfo`` struct (network_list.go).
    """

    href: str = ""
    method: str = ""


@dataclass
class LinkHrefMethod:
    """Inline struct with href and method for anonymous link fields."""

    href: str = ""
    method: str = ""


@dataclass
class LinkHref:
    """Inline struct with href only for anonymous link fields."""

    href: str = ""


# ---------------------------------------------------------------------------
# Link collection dataclasses
# ---------------------------------------------------------------------------

@dataclass
class NetworkListsResponseLinks:
    """Top-level response links containing a create link.

    Mirrors Go ``NetworkListsResponseLinks`` (network_list.go).
    """

    create: LinkInfo | None = None


@dataclass
class NetworkListsLinks:
    """Links for individual network list items using ``*LinkInfo`` pointers.

    Mirrors Go ``NetworkListsLinks`` (network_list.go).
    """

    activate_in_production: LinkInfo | None = None
    activate_in_staging: LinkInfo | None = None
    append_items: LinkInfo | None = None
    retrieve: LinkInfo | None = None
    status_in_production: LinkInfo | None = None
    status_in_staging: LinkInfo | None = None
    update: LinkInfo | None = None


@dataclass
class NetworkListResponseLinks:
    """Inline links struct for network list detail responses.

    Used by ``GetNetworkListResponse``, ``CreateNetworkListResponse``,
    ``GetNetworkListDescriptionResponse``, and list elements in
    ``UpdateNetworkListResponse`` / ``GetNetworkListSubscriptionResponse``.
    """

    activate_in_production: LinkHrefMethod | None = None
    activate_in_staging: LinkHrefMethod | None = None
    append_items: LinkHrefMethod | None = None
    retrieve: LinkHref | None = None
    status_in_production: LinkHref | None = None
    status_in_staging: LinkHref | None = None
    update: LinkHrefMethod | None = None


@dataclass
class ActivationResponseLinks:
    """Inline links struct for activation responses.

    Used by ``GetActivationsResponse``, ``CreateActivationsResponse``,
    and ``RemoveActivationsResponse``.
    """

    append_items: LinkHrefMethod | None = None
    retrieve: LinkHref | None = None
    status_in_production: LinkHref | None = None
    status_in_staging: LinkHref | None = None
    sync_point_history: LinkHref | None = None
    update: LinkHrefMethod | None = None
    activation_details: LinkHref | None = None


@dataclass
class ActivationNetworkListLinks:
    """Inline links struct for the ``networkList`` field in
    ``GetActivationResponse``.
    """

    append_items: LinkHrefMethod | None = None
    retrieve: LinkHref | None = None
    status_in_production: LinkHref | None = None
    status_in_staging: LinkHref | None = None
    sync_point_history: LinkHref | None = None
    update: LinkHrefMethod | None = None


@dataclass
class ResponseCreateLinks:
    """Inline links struct containing only a create link.

    Used by ``UpdateNetworkListResponse`` and
    ``GetNetworkListSubscriptionResponse``.
    """

    create: LinkHrefMethod | None = None


# ---------------------------------------------------------------------------
# Composite helper dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ActivationNetworkList:
    """Inline struct for ``GetActivationResponse.networkList``."""

    activation_comments: str = ""
    activation_status: str = ""
    links: ActivationNetworkListLinks | None = None
    sync_point: int = 0
    unique_id: str = ""


@dataclass
class ResponseNetworkListElement:  # pylint: disable=too-many-instance-attributes
    """Inline network list element in response arrays.

    Used by ``UpdateNetworkListResponse.networkLists`` and
    ``GetNetworkListSubscriptionResponse.networkLists``.
    """

    element_count: int = 0
    links: NetworkListResponseLinks | None = None
    name: str = ""
    network_list_type: str = ""
    read_only: bool = False
    shared: bool = False
    sync_point: int = 0
    type: str = ""
    unique_id: str = ""
    access_control_group: str = ""
    description: str = ""


# ---------------------------------------------------------------------------
# Network list CRUD request / response dataclasses
# ---------------------------------------------------------------------------

@dataclass
class GetNetworkListRequest:
    """Request parameters for ``GetNetworkList``."""

    unique_id: str = field(default="", metadata={"json": "-"})


@dataclass
class GetNetworkListsRequest:
    """Request parameters for ``GetNetworkLists``."""

    name: str = ""
    type: str = ""


@dataclass
class GetNetworkListsResponse:
    """Response from ``GetNetworkLists``."""

    links: NetworkListsResponseLinks | None = None
    network_lists: list[GetNetworkListsResponseListElement] = field(
        default_factory=list,
    )


@dataclass
class GetNetworkListsResponseListElement:  # pylint: disable=too-many-instance-attributes
    """Information about a single network list in a list response."""

    element_count: int = 0
    links: NetworkListsLinks | None = None
    name: str = ""
    network_list_type: str = ""
    read_only: bool = False
    shared: bool = False
    sync_point: int = 0
    type: str = ""
    unique_id: str = ""
    access_control_group: str = ""
    description: str = ""


@dataclass
class GetNetworkListResponse:  # pylint: disable=too-many-instance-attributes
    """Detailed response for a single network list."""

    name: str = ""
    unique_id: str = ""
    contract_id: str = ""
    group_id: int = 0
    sync_point: int = 0
    type: str = ""
    description: str = ""
    network_list_type: str = ""
    element_count: int = 0
    read_only: bool = False
    shared: bool = False
    list: list[str] = field(default_factory=list)
    links: NetworkListResponseLinks | None = None


@dataclass
class CreateNetworkListRequest:
    """Request body for ``CreateNetworkList``."""

    name: str = ""
    type: str = ""
    description: str = ""
    contract_id: str = ""
    group_id: int = 0
    list: list[str] = field(default_factory=list)


@dataclass
class CreateNetworkListResponse:  # pylint: disable=too-many-instance-attributes
    """Response from ``CreateNetworkList``."""

    name: str = ""
    description: str = ""
    unique_id: str = ""
    sync_point: int = 0
    type: str = ""
    network_list_type: str = ""
    element_count: int = 0
    read_only: bool = False
    shared: bool = False
    list: list[str] = field(default_factory=list)
    links: NetworkListResponseLinks | None = None


@dataclass
class UpdateNetworkListRequest:  # pylint: disable=too-many-instance-attributes
    """Request body for ``UpdateNetworkList``."""

    name: str = ""
    type: str = ""
    description: str = ""
    contract_id: str = ""
    group_id: int = 0
    sync_point: int = 0
    list: list[str] = field(default_factory=list)
    unique_id: str = field(default="", metadata={"json": "-"})


@dataclass
class UpdateNetworkListResponse:
    """Response from ``UpdateNetworkList``."""

    links: ResponseCreateLinks | None = None
    network_lists: list[ResponseNetworkListElement] = field(
        default_factory=list,
    )


@dataclass
class RemoveNetworkListRequest:
    """Request parameters for ``RemoveNetworkList``."""

    unique_id: str = field(default="", metadata={"json": "-"})


@dataclass
class RemoveNetworkListResponse:
    """Response from ``RemoveNetworkList``."""

    status: int = 0
    unique_id: str = ""
    sync_point: int = 0


# ---------------------------------------------------------------------------
# Activation request / response dataclasses
# ---------------------------------------------------------------------------

@dataclass
class GetActivationsRequest:
    """Request parameters for ``GetActivations``."""

    unique_id: str = field(default="", metadata={"json": "-"})
    action: str = field(default="", metadata={"json": "-"})
    network: str = ""
    activation_id: int = 0


@dataclass
class GetActivationRequest:
    """Request parameters for ``GetActivation``."""

    activation_id: int = 0


@dataclass
class GetActivationsResponse:  # pylint: disable=too-many-instance-attributes
    """Response from ``GetActivations``."""

    activation_id: int = 0
    activation_comments: str = ""
    activation_status: str = ""
    sync_point: int = 0
    unique_id: str = ""
    fast: bool = False
    dispatch_count: int = 0
    links: ActivationResponseLinks | None = None


@dataclass
class GetActivationResponse:
    """Response from ``GetActivation``."""

    activation_id: int = 0
    create_date: str = ""
    created_by: str = ""
    environment: str = ""
    fast: bool = False
    activation_status: str = field(
        default="", metadata={"json_name": "status"},
    )
    network_list: ActivationNetworkList | None = None


@dataclass
class CreateActivationsRequest:
    """Request body for ``CreateActivations``."""

    unique_id: str = field(default="", metadata={"json": "-"})
    action: str = field(default="", metadata={"json": "-"})
    network: str = ""
    comments: str = ""
    notification_recipients: list[str] = field(default_factory=list)


@dataclass
class CreateActivationsResponse:  # pylint: disable=too-many-instance-attributes
    """Response from ``CreateActivations``."""

    activation_id: int = 0
    activation_comments: str = ""
    activation_status: str = ""
    sync_point: int = 0
    unique_id: str = ""
    fast: bool = False
    dispatch_count: int = 0
    links: ActivationResponseLinks | None = None


@dataclass
class RemoveActivationsRequest:
    """Request body for ``RemoveActivations``."""

    unique_id: str = field(default="", metadata={"json": "-"})
    activation_id: int = field(default=0, metadata={"json": "-"})
    action: str = ""
    network: str = ""
    comments: str = ""
    notification_recipients: list[str] = field(default_factory=list)


@dataclass
class RemoveActivationsResponse:  # pylint: disable=too-many-instance-attributes
    """Response from ``RemoveActivations``."""

    activation_id: int = 0
    activation_comments: str = ""
    activation_status: str = ""
    sync_point: int = 0
    unique_id: str = ""
    fast: bool = False
    dispatch_count: int = 0
    links: ActivationResponseLinks | None = None


# ---------------------------------------------------------------------------
# Enum-style constant classes
# ---------------------------------------------------------------------------

class ActivationValue:  # pylint: disable=too-few-public-methods
    """Constants for the ``action`` parameter on activation requests."""

    ACTIVATE = "ACTIVATE"
    DEACTIVATE = "DEACTIVATE"


class NetworkValue:  # pylint: disable=too-few-public-methods
    """Constants for the ``network`` parameter on activation requests."""

    PRODUCTION = "PRODUCTION"
    STAGING = "STAGING"


class StatusValue:  # pylint: disable=too-few-public-methods
    """Constants for the ``activationStatus`` field on responses."""

    ACTIVATED = "ACTIVATED"
    INACTIVE = "INACTIVE"
    RECEIVED = "RECEIVED"
    ABORTED = "ABORTED"
    FAILED = "FAILED"
    DEACTIVATED = "DEACTIVATED"
    PENDING_DEACTIVATION = "PENDING_DEACTIVATION"
    NEW = "NEW"


# ---------------------------------------------------------------------------
# Network list description request / response dataclasses
# ---------------------------------------------------------------------------

@dataclass
class GetNetworkListDescriptionRequest:
    """Request parameters for ``GetNetworkListDescription``."""

    unique_id: str = ""
    name: str = ""
    description: str = ""


@dataclass
class GetNetworkListDescriptionResponse:  # pylint: disable=too-many-instance-attributes
    """Response from ``GetNetworkListDescription``."""

    name: str = ""
    unique_id: str = ""
    description: str = ""
    sync_point: int = 0
    type: str = ""
    network_list_type: str = ""
    element_count: int = 0
    read_only: bool = False
    shared: bool = False
    list: list[str] = field(default_factory=list)
    links: NetworkListResponseLinks | None = None


@dataclass
class UpdateNetworkListDescriptionRequest:
    """Request body for ``UpdateNetworkListDescription``."""

    unique_id: str = field(default="", metadata={"json": "-"})
    name: str = ""
    description: str = ""


@dataclass
class UpdateNetworkListDescriptionResponse:
    """Response from ``UpdateNetworkListDescription`` (empty body)."""

    empty: str = field(default="", metadata={"json": "-"})


# ---------------------------------------------------------------------------
# Network list subscription request / response dataclasses
# ---------------------------------------------------------------------------

@dataclass
class GetNetworkListSubscriptionRequest:
    """Request parameters for ``GetNetworkListSubscription``."""

    recipients: list[str] = field(
        default_factory=list, metadata={"json": "-"},
    )
    unique_ids: list[str] = field(
        default_factory=list, metadata={"json": "-"},
    )


@dataclass
class GetNetworkListSubscriptionResponse:
    """Response from ``GetNetworkListSubscription``."""

    links: ResponseCreateLinks | None = None
    network_lists: list[ResponseNetworkListElement] = field(
        default_factory=list,
    )


@dataclass
class UpdateNetworkListSubscriptionRequest:
    """Request body for ``UpdateNetworkListSubscription``."""

    recipients: list[str] = field(default_factory=list)
    unique_ids: list[str] = field(default_factory=list)


@dataclass
class UpdateNetworkListSubscriptionResponse:
    """Response from ``UpdateNetworkListSubscription`` (empty body)."""

    empty: str = field(default="", metadata={"json": "-"})


@dataclass
class RemoveNetworkListSubscriptionRequest:
    """Request body for ``RemoveNetworkListSubscription``."""

    recipients: list[str] = field(default_factory=list)
    unique_ids: list[str] = field(default_factory=list)


@dataclass
class RemoveNetworkListSubscriptionResponse:
    """Response from ``RemoveNetworkListSubscription`` (empty body)."""

    empty: str = field(default="", metadata={"json": "-"})


@dataclass
class Recipients:
    """Wrapper for notification recipients.

    The Go JSON tag maps the ``recipients`` field to the key
    ``notificationRecipients``.
    """

    recipients: str = field(
        default="",
        metadata={"json_name": "notificationRecipients"},
    )


# ---------------------------------------------------------------------------
# JSON serialization helpers
# ---------------------------------------------------------------------------

def to_dict(obj: object) -> dict:
    """Convert a dataclass instance to a JSON-serializable dict.

    * Converts field names from ``snake_case`` to ``camelCase`` to match
      the Go JSON tags.
    * Skips fields whose metadata contains ``json: "-"`` (request-only
      path/query parameters that are not part of the HTTP body).
    * Uses a custom ``json_name`` metadata value when the standard
      ``_snake_to_camel`` conversion does not produce the correct key.
    * Omits ``None`` values.
    * Recursively serializes nested dataclass instances.
    """
    if not dataclasses.is_dataclass(obj) or isinstance(obj, type):
        raise TypeError(f"{obj!r} is not a dataclass instance")

    result: dict = {}
    for f in dataclasses.fields(obj):
        # Skip fields explicitly excluded from JSON (Go json:"-")
        if f.metadata.get("json") == "-":
            continue

        value = getattr(obj, f.name)

        # Determine the JSON key for this field
        json_key = f.metadata.get("json_name", _snake_to_camel(f.name))

        # Omit None values (mirrors Go omitempty for pointer types)
        if value is None:
            continue

        # Recursively serialize nested dataclasses
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            result[json_key] = to_dict(value)
        elif isinstance(value, list):
            result[json_key] = [
                to_dict(item)
                if dataclasses.is_dataclass(item)
                and not isinstance(item, type)
                else item
                for item in value
            ]
        else:
            result[json_key] = value

    return result


def from_dict(cls: type, data: dict) -> object:
    """Create a dataclass instance from a JSON-compatible dict.

    * Converts ``camelCase`` JSON keys to ``snake_case`` field names using
      a reverse lookup built from the class's field definitions.
    * Handles custom ``json_name`` metadata.
    * Recursively deserializes nested dataclass values.

    Args:
        cls: The target dataclass type.
        data: A dictionary with camelCase keys.

    Returns:
        An instance of *cls* populated from *data*.
    """
    if not dataclasses.is_dataclass(cls):
        raise TypeError(f"{cls!r} is not a dataclass")
    if not isinstance(data, dict):
        raise TypeError(f"expected dict, got {type(data).__name__}")

    hints = get_type_hints(cls)

    # Build a mapping from JSON key → (field_name, resolved_type)
    json_to_field: dict[str, tuple[str, type]] = {}
    for f in dataclasses.fields(cls):
        json_key = f.metadata.get("json_name", _snake_to_camel(f.name))
        # Also accept the raw field name when json:"-" metadata is set
        if f.metadata.get("json") == "-":
            json_key = f.name
        json_to_field[json_key] = (f.name, hints.get(f.name, f.type))

    kwargs: dict = {}
    for json_key, (field_name, field_type) in json_to_field.items():
        if json_key not in data:
            continue
        value = data[json_key]
        if value is None:
            kwargs[field_name] = None
            continue

        actual_type = _unwrap_optional(field_type)

        # Nested dataclass
        if dataclasses.is_dataclass(actual_type) and isinstance(value, dict):
            kwargs[field_name] = from_dict(actual_type, value)
            continue

        # List of dataclasses
        elem_type = _get_list_element_type(actual_type)
        if (
            elem_type is not None
            and dataclasses.is_dataclass(elem_type)
            and isinstance(value, list)
        ):
            kwargs[field_name] = [
                from_dict(elem_type, item) if isinstance(item, dict) else item
                for item in value
            ]
            continue

        kwargs[field_name] = value

    return cls(**kwargs)
