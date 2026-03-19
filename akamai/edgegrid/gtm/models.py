# pylint: disable=too-many-instance-attributes,too-many-lines,import-outside-toplevel,too-few-public-methods
"""Request and response models for the GTM (Global Traffic Management) API.

Defines all request/response model dataclasses for the Akamai Global Traffic
Management API, ported field-for-field from the Go v12 SDK structs defined
in the ``pkg/gtm`` package.  Every Go struct maps to a Python ``@dataclass``
with identical field names (using JSON tag names as canonical Python
attribute names), types mapped per the Go-to-Python type mapping table,
and required/optional semantics preserved.

Go reference files:
- pkg/gtm/common.go (ResponseStatus, DatacenterResponse, ResourceResponse,
  Link, LoadObject, DatacenterBase)
- pkg/gtm/domain.go (Domain, DomainItem, DomainsList, DomainQueryArgs,
  NullFieldMapStruct, NullPerObjectAttributeStruct, ObjectMap,
  and all domain request/response types)
- pkg/gtm/property.go (TrafficTarget, HTTPHeader, LivenessTest, StaticRRSet,
  Property, PropertyList, and all property request/response types)
- pkg/gtm/datacenter.go (Datacenter, DatacenterList, and all datacenter
  request/response types including default datacenter constants)
- pkg/gtm/resource.go (ResourceInstance, Resource, ResourceList, and all
  resource request/response types)
- pkg/gtm/asmap.go (ASAssignment, ASMap, ASMapList, and all AS map
  request/response types)
- pkg/gtm/geomap.go (GeoAssignment, GeoMap, GeoMapList, and all geo map
  request/response types)
- pkg/gtm/cidrmap.go (CIDRAssignment, CIDRMap, CIDRMapList, and all CIDR
  map request/response types)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Serialization / deserialization helpers
# ---------------------------------------------------------------------------

# Explicit JSON key overrides where snake_case -> camelCase is non-trivial.
_SPECIAL_JSON_KEYS: dict[str, str] = {
    "max_ttl": "maxTTL",
    "min_ttl": "minTTL",
    "static_ttl": "staticTTL",
    "dynamic_ttl": "dynamicTTL",
    "static_rr_sets": "staticRRSets",
    "alternate_ca_certificates": "alternateCACertificates",
    "weighted_hash_bits_for_ipv4": "weightedHashBitsForIPv4",
    "weighted_hash_bits_for_ipv6": "weightedHashBitsForIPv6",
    "domain_names": "domains",
}

_SPECIAL_PY_KEYS: dict[str, str] = {v: k for k, v in _SPECIAL_JSON_KEYS.items()}


def _snake_to_camel(name: str) -> str:
    """Convert *snake_case* Python name to *camelCase* JSON key."""
    if name in _SPECIAL_JSON_KEYS:
        return _SPECIAL_JSON_KEYS[name]
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _camel_to_snake(name: str) -> str:
    """Convert *camelCase* JSON key to *snake_case* Python name."""
    if name in _SPECIAL_PY_KEYS:
        return _SPECIAL_PY_KEYS[name]
    result: list[str] = []
    for char in name:
        if char.isupper() and result:
            result.append("_")
        result.append(char.lower())
    return "".join(result)


def _is_empty(value: object) -> bool:
    """Return ``True`` when *value* is the Go zero-value equivalent.

    Used to implement ``omitempty`` JSON serialisation semantics.
    """
    if value is None:
        return True
    if isinstance(value, bool):
        return not value
    if isinstance(value, (int, float)):
        return value == 0
    if isinstance(value, str):
        return value == ""
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def _serialize(value: object) -> object:
    """Recursively serialise a value for JSON output."""
    if value is None:
        return None
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    if hasattr(value, "to_dict"):
        return value.to_dict()  # type: ignore[union-attr]
    return value


def _to_dict_impl(obj: object, field_defs: list) -> dict:
    """Generic ``to_dict`` implementation driven by *field_defs*.

    Each element of *field_defs* is a 4-tuple::

        (python_name, json_key, omitempty, nested_info)

    *nested_info* is unused by ``to_dict`` (serialisation delegates to
    ``_serialize``).
    """
    result: dict[str, object] = {}
    for py_name, json_key, omit, _ in field_defs:
        val = getattr(obj, py_name)
        if omit and _is_empty(val):
            continue
        result[json_key] = _serialize(val)
    return result


def _from_dict_impl(cls: type, data: dict | None, field_defs: list) -> object:
    """Generic ``from_dict`` implementation driven by *field_defs*.

    *nested_info* conventions:

    * ``None`` – primitive or untyped value; assign directly.
    * *SomeClass* – single nested object; call ``SomeClass.from_dict()``.
    * ``(SomeClass,)`` – list of nested objects.
    * ``(SomeClass, "dict")`` – ``dict[str, SomeClass]``.
    """
    if not data:
        return cls()
    reverse: dict[str, tuple[str, object]] = {
        jk: (pn, ni) for pn, jk, _, ni in field_defs
    }
    kwargs: dict[str, object] = {}
    for json_key, raw in data.items():
        if json_key not in reverse:
            continue
        py_name, nested = reverse[json_key]
        kwargs[py_name] = _deserialize(raw, nested)
    return cls(**kwargs)


def _deserialize(raw: object, nested_info: object) -> object:
    """Deserialise a single raw JSON value using *nested_info*."""
    if raw is None or nested_info is None:
        return raw
    if isinstance(nested_info, tuple):
        ncls = nested_info[0]
        if len(nested_info) == 1 and isinstance(raw, list):
            return [
                ncls.from_dict(item) if isinstance(item, dict) else item
                for item in raw
            ]
        if len(nested_info) >= 2 and nested_info[1] == "dict" and isinstance(raw, dict):
            return {
                k: ncls.from_dict(v) if isinstance(v, dict) else v
                for k, v in raw.items()
            }
        return raw
    # single nested class
    return nested_info.from_dict(raw) if isinstance(raw, dict) else raw  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Constants from datacenter.go
# ---------------------------------------------------------------------------

MAP_DEFAULT_DC = 5400
"""Default Datacenter ID for Maps.  Mirrors Go ``MapDefaultDC``."""

IPV4_DEFAULT_DC = 5401
"""Default Datacenter ID for IPv4.  Mirrors Go ``Ipv4DefaultDC``."""

IPV6_DEFAULT_DC = 5402
"""Default Datacenter ID for IPv6.  Mirrors Go ``Ipv6DefaultDC``."""


# ---------------------------------------------------------------------------
# Type alias: ObjectMap  (mirrors Go ``ObjectMap = map[string]interface{}``)
# ---------------------------------------------------------------------------

ObjectMap = dict[str, Any]
"""Alias for ``dict[str, Any]``.  Mirrors Go ``ObjectMap``."""


# ===================================================================
# Common types  (common.go)
# ===================================================================

@dataclass
class Link:
    """Hyperlink reference.  Mirrors Go ``Link``."""

    rel: str = ""
    href: str = ""

    _FIELDS = [
        ("rel", "rel", True, None),
        ("href", "href", True, None),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> Link:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class LoadObject:
    """Load reporting interface info.  Mirrors Go ``LoadObject``."""

    load_object: str = ""
    load_object_port: int = 0
    load_servers: list[str] | None = None

    _FIELDS = [
        ("load_object", "loadObject", True, None),
        ("load_object_port", "loadObjectPort", True, None),
        ("load_servers", "loadServers", True, None),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> LoadObject:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class DatacenterBase:
    """Base datacenter reference.  Mirrors Go ``DatacenterBase``."""

    nickname: str = ""
    datacenter_id: int = 0

    _FIELDS = [
        ("nickname", "nickname", True, None),
        ("datacenter_id", "datacenterId", False, None),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> DatacenterBase:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class ResponseStatus:
    """Status returned on Create/Update/Delete operations.

    Mirrors Go ``ResponseStatus``.
    """

    change_id: str = ""
    links: list[Link] | None = None
    message: str = ""
    passing_validation: bool = False
    propagation_status: str = ""
    propagation_status_date: str = ""

    _FIELDS = [
        ("change_id", "changeId", True, None),
        ("links", "links", True, (Link,)),
        ("message", "message", True, None),
        ("passing_validation", "passingValidation", True, None),
        ("propagation_status", "propagationStatus", True, None),
        ("propagation_status_date", "propagationStatusDate", True, None),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> ResponseStatus:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


# ===================================================================
# Property sub-types  (property.go)
# ===================================================================

@dataclass
class TrafficTarget:
    """Traffic target for property.  Mirrors Go ``TrafficTarget``."""

    datacenter_id: int = 0
    enabled: bool = False
    weight: float = 0.0
    servers: list[str] | None = None
    name: str = ""
    handout_c_name: str = ""
    precedence: int | None = None

    _FIELDS = [
        ("datacenter_id", "datacenterId", False, None),
        ("enabled", "enabled", False, None),
        ("weight", "weight", True, None),
        ("servers", "servers", True, None),
        ("name", "name", True, None),
        ("handout_c_name", "handoutCName", True, None),
        ("precedence", "precedence", True, None),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> TrafficTarget:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class HTTPHeader:
    """HTTP header for liveness tests.  Mirrors Go ``HTTPHeader``."""

    name: str = ""
    value: str = ""

    _FIELDS = [
        ("name", "name", False, None),
        ("value", "value", False, None),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> HTTPHeader:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]



@dataclass
class LivenessTest:
    """Liveness test configuration.  Mirrors Go ``LivenessTest``."""

    name: str = ""
    error_penalty: float = 0.0
    peer_certificate_verification: bool = False
    test_interval: int = 0
    test_object: str = ""
    links: list[Link] | None = None
    request_string: str = ""
    response_string: str = ""
    http_error3xx: bool = False
    http_error4xx: bool = False
    http_error5xx: bool = False
    http_method: str | None = None
    http_request_body: str | None = None
    disabled: bool = False
    test_object_protocol: str = ""
    test_object_password: str = ""
    test_object_port: int = 0
    ssl_client_private_key: str = ""
    ssl_client_certificate: str = ""
    pre2023_security_posture: bool = False
    disable_nonstandard_port_warning: bool = False
    http_headers: list[HTTPHeader] | None = None
    test_object_username: str = ""
    test_timeout: float = 0.0
    timeout_penalty: float = 0.0
    answers_required: bool = False
    resource_type: str = ""
    recursion_requested: bool = False
    alternate_ca_certificates: list[str] | None = None

    _FIELDS = [
        ("name", "name", False, None),
        ("error_penalty", "errorPenalty", True, None),
        ("peer_certificate_verification", "peerCertificateVerification", False, None),
        ("test_interval", "testInterval", True, None),
        ("test_object", "testObject", True, None),
        ("links", "links", True, (Link,)),
        ("request_string", "requestString", True, None),
        ("response_string", "responseString", True, None),
        ("http_error3xx", "httpError3xx", False, None),
        ("http_error4xx", "httpError4xx", False, None),
        ("http_error5xx", "httpError5xx", False, None),
        ("http_method", "httpMethod", False, None),
        ("http_request_body", "httpRequestBody", False, None),
        ("disabled", "disabled", False, None),
        ("test_object_protocol", "testObjectProtocol", True, None),
        ("test_object_password", "testObjectPassword", True, None),
        ("test_object_port", "testObjectPort", True, None),
        ("ssl_client_private_key", "sslClientPrivateKey", True, None),
        ("ssl_client_certificate", "sslClientCertificate", True, None),
        ("pre2023_security_posture", "pre2023SecurityPosture", False, None),
        ("disable_nonstandard_port_warning", "disableNonstandardPortWarning", False, None),
        ("http_headers", "httpHeaders", True, (HTTPHeader,)),
        ("test_object_username", "testObjectUsername", True, None),
        ("test_timeout", "testTimeout", True, None),
        ("timeout_penalty", "timeoutPenalty", True, None),
        ("answers_required", "answersRequired", False, None),
        ("resource_type", "resourceType", True, None),
        ("recursion_requested", "recursionRequested", False, None),
        ("alternate_ca_certificates", "alternateCACertificates", False, None),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> LivenessTest:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class StaticRRSet:
    """Static record set.  Mirrors Go ``StaticRRSet``."""

    type: str = ""
    ttl: int = 0
    rdata: list[str] | None = None

    _FIELDS = [
        ("type", "type", False, None),
        ("ttl", "ttl", False, None),
        ("rdata", "rdata", False, None),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> StaticRRSet:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class Property:
    """GTM property.  Mirrors Go ``Property``."""

    name: str = ""
    type: str = ""
    ipv6: bool = False
    score_aggregation_type: str = ""
    stickiness_bonus_percentage: int = 0
    stickiness_bonus_constant: int = 0
    health_threshold: float = 0.0
    use_computed_targets: bool = False
    backup_ip: str = ""
    balance_by_download_score: bool = False
    static_ttl: int = 0
    static_rr_sets: list[StaticRRSet] | None = None
    last_modified: str = ""
    unreachable_threshold: float = 0.0
    min_live_fraction: float = 0.0
    health_multiplier: float = 0.0
    dynamic_ttl: int = 0
    max_unreachable_penalty: int = 0
    map_name: str = ""
    handout_limit: int = 0
    handout_mode: str = ""
    failover_delay: int = 0
    backup_c_name: str = ""
    failback_delay: int = 0
    load_imbalance_percentage: float = 0.0
    health_max: float = 0.0
    ghost_demand_reporting: bool = False
    comments: str = ""
    cname: str = ""
    weighted_hash_bits_for_ipv4: int = 0
    weighted_hash_bits_for_ipv6: int = 0
    traffic_targets: list[TrafficTarget] | None = None
    links: list[Link] | None = None
    liveness_tests: list[LivenessTest] | None = None

    _FIELDS = [
        ("name", "name", False, None),
        ("type", "type", False, None),
        ("ipv6", "ipv6", False, None),
        ("score_aggregation_type", "scoreAggregationType", False, None),
        ("stickiness_bonus_percentage", "stickinessBonusPercentage", True, None),
        ("stickiness_bonus_constant", "stickinessBonusConstant", True, None),
        ("health_threshold", "healthThreshold", True, None),
        ("use_computed_targets", "useComputedTargets", False, None),
        ("backup_ip", "backupIp", True, None),
        ("balance_by_download_score", "balanceByDownloadScore", False, None),
        ("static_ttl", "staticTTL", True, None),
        ("static_rr_sets", "staticRRSets", True, (StaticRRSet,)),
        ("last_modified", "lastModified", False, None),
        ("unreachable_threshold", "unreachableThreshold", True, None),
        ("min_live_fraction", "minLiveFraction", True, None),
        ("health_multiplier", "healthMultiplier", True, None),
        ("dynamic_ttl", "dynamicTTL", True, None),
        ("max_unreachable_penalty", "maxUnreachablePenalty", True, None),
        ("map_name", "mapName", True, None),
        ("handout_limit", "handoutLimit", False, None),
        ("handout_mode", "handoutMode", False, None),
        ("failover_delay", "failoverDelay", True, None),
        ("backup_c_name", "backupCName", True, None),
        ("failback_delay", "failbackDelay", True, None),
        ("load_imbalance_percentage", "loadImbalancePercentage", True, None),
        ("health_max", "healthMax", True, None),
        ("ghost_demand_reporting", "ghostDemandReporting", False, None),
        ("comments", "comments", True, None),
        ("cname", "cname", True, None),
        ("weighted_hash_bits_for_ipv4", "weightedHashBitsForIPv4", True, None),
        ("weighted_hash_bits_for_ipv6", "weightedHashBitsForIPv6", True, None),
        ("traffic_targets", "trafficTargets", True, (TrafficTarget,)),
        ("links", "links", True, (Link,)),
        ("liveness_tests", "livenessTests", True, (LivenessTest,)),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> Property:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]

    def validate(self) -> str | None:
        """Validate property-level constraints.  Delegates to ``validation``."""
        from akamai.edgegrid.gtm import validation  # lazy import
        return validation.validate_property(self)


@dataclass
class PropertyList:
    """List of GTM properties.  Mirrors Go ``PropertyList``."""

    property_items: list[Property] | None = None

    _FIELDS = [
        ("property_items", "items", False, (Property,)),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> PropertyList:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


# -- Property request / response types --------------------------------

@dataclass
class PropertyRequest:
    """Request body for Create/Update property.  Mirrors Go ``PropertyRequest``."""

    property: Property | None = None
    domain_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_create_property_request(self)


@dataclass
class GetPropertyRequest:
    """Parameters for GetProperty.  Mirrors Go ``GetPropertyRequest``."""

    domain_name: str = ""
    property_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_get_property_request(self)


@dataclass
class ListPropertiesRequest:
    """Parameters for ListProperties.  Mirrors Go ``ListPropertiesRequest``."""

    domain_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_list_properties_request(self)


@dataclass
class DeletePropertyRequest:
    """Parameters for DeleteProperty.  Mirrors Go ``DeletePropertyRequest``."""

    domain_name: str = ""
    property_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_delete_property_request(self)


@dataclass
class CreatePropertyResponse:
    """Response from CreateProperty.  Mirrors Go ``CreatePropertyResponse``."""

    resource: Property | None = None
    status: ResponseStatus | None = None

    _FIELDS = [
        ("resource", "resource", True, Property),
        ("status", "status", True, ResponseStatus),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> CreatePropertyResponse:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class UpdatePropertyResponse:
    """Response from UpdateProperty.  Mirrors Go ``UpdatePropertyResponse``."""

    resource: Property | None = None
    status: ResponseStatus | None = None

    _FIELDS = [
        ("resource", "resource", True, Property),
        ("status", "status", True, ResponseStatus),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> UpdatePropertyResponse:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class DeletePropertyResponse:
    """Response from DeleteProperty.  Mirrors Go ``DeletePropertyResponse``."""

    resource: Property | None = None
    status: ResponseStatus | None = None

    _FIELDS = [
        ("resource", "resource", True, Property),
        ("status", "status", True, ResponseStatus),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> DeletePropertyResponse:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


# Property type aliases
GetPropertyResponse = Property
ListPropertiesResponse = PropertyList
CreatePropertyRequest = PropertyRequest
class UpdatePropertyRequest(PropertyRequest):
    """Update property request — delegates to update-specific validation."""

    def validate(self):
        """Validate the update property request fields."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_update_property_request(self)


# ===================================================================
# Datacenter types  (datacenter.go)
# ===================================================================

@dataclass
class Datacenter:
    """GTM datacenter.  Mirrors Go ``Datacenter``."""

    city: str = ""
    clone_of: int = 0
    cloud_server_host_header_override: bool = False
    cloud_server_targeting: bool = False
    continent: str = ""
    country: str = ""
    datacenter_id: int = 0
    default_load_object: LoadObject | None = None
    latitude: float = 0.0
    links: list[Link] | None = None
    longitude: float = 0.0
    nickname: str = ""
    ping_interval: int = 0
    ping_packet_size: int = 0
    score_penalty: int = 0
    servermonitor_pool: str = ""
    state_or_province: str = ""
    virtual: bool = False

    _FIELDS = [
        ("city", "city", True, None),
        ("clone_of", "cloneOf", True, None),
        ("cloud_server_host_header_override", "cloudServerHostHeaderOverride", False, None),
        ("cloud_server_targeting", "cloudServerTargeting", False, None),
        ("continent", "continent", True, None),
        ("country", "country", True, None),
        ("datacenter_id", "datacenterId", True, None),
        ("default_load_object", "defaultLoadObject", True, LoadObject),
        ("latitude", "latitude", True, None),
        ("links", "links", True, (Link,)),
        ("longitude", "longitude", True, None),
        ("nickname", "nickname", True, None),
        ("ping_interval", "pingInterval", True, None),
        ("ping_packet_size", "pingPacketSize", True, None),
        ("score_penalty", "scorePenalty", True, None),
        ("servermonitor_pool", "servermonitorPool", True, None),
        ("state_or_province", "stateOrProvince", True, None),
        ("virtual", "virtual", False, None),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> Datacenter:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]

    def validate(self) -> str | None:
        """Validate datacenter-level constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_datacenter(self)


@dataclass
class DatacenterList:
    """List of datacenters.  Mirrors Go ``DatacenterList``."""

    datacenter_items: list[Datacenter] | None = None

    _FIELDS = [
        ("datacenter_items", "items", False, (Datacenter,)),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> DatacenterList:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


# -- Datacenter request / response types ------------------------------

@dataclass
class DatacenterRequest:
    """Request body for Create/Update datacenter.  Mirrors Go ``DatacenterRequest``."""

    datacenter: Datacenter | None = None
    domain_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_create_datacenter_request(self)


@dataclass
class ListDatacentersRequest:
    """Parameters for ListDatacenters.  Mirrors Go ``ListDatacentersRequest``."""

    domain_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_list_datacenters_request(self)


@dataclass
class GetDatacenterRequest:
    """Parameters for GetDatacenter.  Mirrors Go ``GetDatacenterRequest``."""

    domain_name: str = ""
    datacenter_id: int = 0

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_get_datacenter_request(self)


@dataclass
class CreateDatacenterRequest(DatacenterRequest):
    """Create datacenter request.  Mirrors Go ``CreateDatacenterRequest``."""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_create_datacenter_request(self)


@dataclass
class UpdateDatacenterRequest(DatacenterRequest):
    """Update datacenter request.  Mirrors Go ``UpdateDatacenterRequest``."""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_update_datacenter_request(self)


@dataclass
class DeleteDatacenterRequest:
    """Parameters for DeleteDatacenter.  Mirrors Go ``DeleteDatacenterRequest``."""

    domain_name: str = ""
    datacenter_id: int = 0

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_delete_datacenter_request(self)


# -- DatacenterResponse / ResourceResponse from common.go ------------

@dataclass
class DatacenterResponse:
    """Response wrapper for datacenter operations.  Mirrors Go ``DatacenterResponse``."""

    status: ResponseStatus | None = None
    resource: Datacenter | None = None

    _FIELDS = [
        ("status", "status", True, ResponseStatus),
        ("resource", "resource", True, Datacenter),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> DatacenterResponse:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


# Datacenter type aliases
ListDatacentersResponse = DatacenterList
GetDatacenterResponse = Datacenter
CreateDatacenterResponse = DatacenterResponse
UpdateDatacenterResponse = DatacenterResponse
DeleteDatacenterResponse = DatacenterResponse


# ===================================================================
# Resource types  (resource.go)
# ===================================================================

@dataclass
class ResourceInstance:
    """Resource instance entry.  Mirrors Go ``ResourceInstance``.

    Note: Go ``ResourceInstance`` embeds ``LoadObject``; in Python the
    ``LoadObject`` fields are flattened into this class.
    """

    datacenter_id: int = 0
    use_default_load_object: bool = False
    load_object: str = ""
    load_object_port: int = 0
    load_servers: list[str] | None = None

    _FIELDS = [
        ("datacenter_id", "datacenterId", False, None),
        ("use_default_load_object", "useDefaultLoadObject", False, None),
        ("load_object", "loadObject", True, None),
        ("load_object_port", "loadObjectPort", True, None),
        ("load_servers", "loadServers", True, None),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> ResourceInstance:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class Resource:
    """GTM resource.  Mirrors Go ``Resource``."""

    type: str = ""
    host_header: str = ""
    least_squares_decay: float = 0.0
    description: str = ""
    leader_string: str = ""
    constrained_property: str = ""
    resource_instances: list[ResourceInstance] | None = None
    aggregation_type: str = ""
    links: list[Link] | None = None
    load_imbalance_percentage: float = 0.0
    upper_bound: int = 0
    name: str = ""
    max_u_multiplicative_increment: float = 0.0
    decay_rate: float = 0.0

    _FIELDS = [
        ("type", "type", True, None),
        ("host_header", "hostHeader", True, None),
        ("least_squares_decay", "leastSquaresDecay", True, None),
        ("description", "description", True, None),
        ("leader_string", "leaderString", True, None),
        ("constrained_property", "constrainedProperty", True, None),
        ("resource_instances", "resourceInstances", True, (ResourceInstance,)),
        ("aggregation_type", "aggregationType", True, None),
        ("links", "links", True, (Link,)),
        ("load_imbalance_percentage", "loadImbalancePercentage", True, None),
        ("upper_bound", "upperBound", True, None),
        ("name", "name", False, None),
        ("max_u_multiplicative_increment", "maxUMultiplicativeIncrement", True, None),
        ("decay_rate", "decayRate", True, None),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> Resource:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]

    def validate(self) -> str | None:
        """Validate resource-level constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_resource(self)


@dataclass
class ResourceList:
    """List of resources.  Mirrors Go ``ResourceList``."""

    resource_items: list[Resource] | None = None

    _FIELDS = [
        ("resource_items", "items", False, (Resource,)),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> ResourceList:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


# -- Resource request / response types --------------------------------

@dataclass
class ResourceRequest:
    """Request body for Create/Update resource.  Mirrors Go ``ResourceRequest``."""

    resource: Resource | None = None
    domain_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_create_resource_request(self)


@dataclass
class GetResourceRequest:
    """Parameters for GetResource.  Mirrors Go ``GetResourceRequest``."""

    domain_name: str = ""
    resource_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_get_resource_request(self)


@dataclass
class ListResourcesRequest:
    """Parameters for ListResources.  Mirrors Go ``ListResourcesRequest``."""

    domain_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_list_resources_request(self)


@dataclass
class DeleteResourceRequest:
    """Parameters for DeleteResource.  Mirrors Go ``DeleteResourceRequest``."""

    domain_name: str = ""
    resource_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_delete_resource_request(self)


@dataclass
class ResourceResponse:
    """Response wrapper for resource operations.  Mirrors Go ``ResourceResponse``."""

    resource: Resource | None = None
    status: ResponseStatus | None = None

    _FIELDS = [
        ("resource", "resource", True, Resource),
        ("status", "status", True, ResponseStatus),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> ResourceResponse:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


# Resource type aliases
GetResourceResponse = Resource
ListResourcesResponse = ResourceList
CreateResourceRequest = ResourceRequest
class UpdateResourceRequest(ResourceRequest):
    """Update resource request — delegates to update-specific validation."""

    def validate(self):
        """Validate the update resource request fields."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_update_resource_request(self)
CreateResourceResponse = ResourceResponse
UpdateResourceResponse = ResourceResponse
DeleteResourceResponse = ResourceResponse


# ===================================================================
# AS Map types  (asmap.go)
# ===================================================================

@dataclass
class ASAssignment:
    """AS assignment entry.  Mirrors Go ``ASAssignment``.

    Go ``ASAssignment`` embeds ``DatacenterBase``; in Python those fields
    are flattened.
    """

    datacenter_id: int = 0
    nickname: str = ""
    as_numbers: list[int] | None = None

    _FIELDS = [
        ("datacenter_id", "datacenterId", False, None),
        ("nickname", "nickname", True, None),
        ("as_numbers", "asNumbers", False, None),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> ASAssignment:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class ASMap:
    """GTM AS map.  Mirrors Go ``ASMap``."""

    default_datacenter: DatacenterBase | None = None
    assignments: list[ASAssignment] | None = None
    name: str = ""
    links: list[Link] | None = None

    _FIELDS = [
        ("default_datacenter", "defaultDatacenter", False, DatacenterBase),
        ("assignments", "assignments", True, (ASAssignment,)),
        ("name", "name", False, None),
        ("links", "links", True, (Link,)),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> ASMap:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]

    def validate(self) -> str | None:
        """Validate AS map constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_as_map(self)


@dataclass
class ASMapList:
    """List of AS maps.  Mirrors Go ``ASMapList``."""

    as_map_items: list[ASMap] | None = None

    _FIELDS = [
        ("as_map_items", "items", False, (ASMap,)),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> ASMapList:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


# -- AS Map request / response types ----------------------------------

@dataclass
class ASMapRequest:
    """Request body for Create/Update AS map.  Mirrors Go ``ASMapRequest``."""

    as_map: ASMap | None = None
    domain_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_create_as_map_request(self)


@dataclass
class GetASMapRequest:
    """Parameters for GetASMap.  Mirrors Go ``GetASMapRequest``."""

    domain_name: str = ""
    as_map_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_get_as_map_request(self)


@dataclass
class ListASMapsRequest:
    """Parameters for ListASMaps.  Mirrors Go ``ListASMapsRequest``."""

    domain_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_list_as_maps_request(self)


@dataclass
class DeleteASMapRequest:
    """Parameters for DeleteASMap.  Mirrors Go ``DeleteASMapRequest``."""

    domain_name: str = ""
    as_map_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_delete_as_map_request(self)


@dataclass
class CreateASMapResponse:
    """Response from CreateASMap.  Mirrors Go ``CreateASMapResponse``."""

    resource: ASMap | None = None
    status: ResponseStatus | None = None

    _FIELDS = [
        ("resource", "resource", True, ASMap),
        ("status", "status", True, ResponseStatus),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> CreateASMapResponse:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class UpdateASMapResponse:
    """Response from UpdateASMap.  Mirrors Go ``UpdateASMapResponse``."""

    resource: ASMap | None = None
    status: ResponseStatus | None = None

    _FIELDS = [
        ("resource", "resource", True, ASMap),
        ("status", "status", True, ResponseStatus),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> UpdateASMapResponse:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class DeleteASMapResponse:
    """Response from DeleteASMap.  Mirrors Go ``DeleteASMapResponse``."""

    resource: ASMap | None = None
    status: ResponseStatus | None = None

    _FIELDS = [
        ("resource", "resource", True, ASMap),
        ("status", "status", True, ResponseStatus),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> DeleteASMapResponse:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


# AS Map type aliases
GetASMapResponse = ASMap
CreateASMapRequest = ASMapRequest
class UpdateASMapRequest(ASMapRequest):
    """Update AS map request — delegates to update-specific validation."""

    def validate(self):
        """Validate the update AS map request fields."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_update_as_map_request(self)


# ===================================================================
# Geo Map types  (geomap.go)
# ===================================================================

@dataclass
class GeoAssignment:
    """Geographic assignment entry.  Mirrors Go ``GeoAssignment``.

    Go ``GeoAssignment`` embeds ``DatacenterBase``; in Python those fields
    are flattened.
    """

    datacenter_id: int = 0
    nickname: str = ""
    countries: list[str] | None = None

    _FIELDS = [
        ("datacenter_id", "datacenterId", False, None),
        ("nickname", "nickname", True, None),
        ("countries", "countries", False, None),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> GeoAssignment:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class GeoMap:
    """GTM geographic map.  Mirrors Go ``GeoMap``."""

    default_datacenter: DatacenterBase | None = None
    assignments: list[GeoAssignment] | None = None
    name: str = ""
    links: list[Link] | None = None

    _FIELDS = [
        ("default_datacenter", "defaultDatacenter", False, DatacenterBase),
        ("assignments", "assignments", True, (GeoAssignment,)),
        ("name", "name", False, None),
        ("links", "links", True, (Link,)),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> GeoMap:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]

    def validate(self) -> str | None:
        """Validate geo map constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_geo_map(self)


@dataclass
class GeoMapList:
    """List of geo maps.  Mirrors Go ``GeoMapList``."""

    geo_map_items: list[GeoMap] | None = None

    _FIELDS = [
        ("geo_map_items", "items", False, (GeoMap,)),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> GeoMapList:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


# -- Geo Map request / response types ---------------------------------

@dataclass
class GeoMapRequest:
    """Request body for Create/Update geo map.  Mirrors Go ``GeoMapRequest``."""

    geo_map: GeoMap | None = None
    domain_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_create_geo_map_request(self)


@dataclass
class GetGeoMapRequest:
    """Parameters for GetGeoMap.  Mirrors Go ``GetGeoMapRequest``."""

    domain_name: str = ""
    geo_map_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_get_geo_map_request(self)


@dataclass
class ListGeoMapsRequest:
    """Parameters for ListGeoMaps.  Mirrors Go ``ListGeoMapsRequest``."""

    domain_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_list_geo_maps_request(self)


@dataclass
class DeleteGeoMapRequest:
    """Parameters for DeleteGeoMap.  Mirrors Go ``DeleteGeoMapRequest``."""

    domain_name: str = ""
    geo_map_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_delete_geo_map_request(self)


@dataclass
class CreateGeoMapResponse:
    """Response from CreateGeoMap.  Mirrors Go ``CreateGeoMapResponse``."""

    resource: GeoMap | None = None
    status: ResponseStatus | None = None

    _FIELDS = [
        ("resource", "resource", True, GeoMap),
        ("status", "status", True, ResponseStatus),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> CreateGeoMapResponse:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class UpdateGeoMapResponse:
    """Response from UpdateGeoMap.  Mirrors Go ``UpdateGeoMapResponse``."""

    resource: GeoMap | None = None
    status: ResponseStatus | None = None

    _FIELDS = [
        ("resource", "resource", True, GeoMap),
        ("status", "status", True, ResponseStatus),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> UpdateGeoMapResponse:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class DeleteGeoMapResponse:
    """Response from DeleteGeoMap.  Mirrors Go ``DeleteGeoMapResponse``."""

    resource: GeoMap | None = None
    status: ResponseStatus | None = None

    _FIELDS = [
        ("resource", "resource", True, GeoMap),
        ("status", "status", True, ResponseStatus),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> DeleteGeoMapResponse:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


# Geo Map type aliases
GetGeoMapResponse = GeoMap
CreateGeoMapRequest = GeoMapRequest
class UpdateGeoMapRequest(GeoMapRequest):
    """Update geo map request — delegates to update-specific validation."""

    def validate(self):
        """Validate the update geo map request fields."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_update_geo_map_request(self)


# ===================================================================
# CIDR Map types  (cidrmap.go)
# ===================================================================

@dataclass
class CIDRAssignment:
    """CIDR assignment entry.  Mirrors Go ``CIDRAssignment``.

    Go ``CIDRAssignment`` embeds ``DatacenterBase``; in Python those fields
    are flattened.
    """

    datacenter_id: int = 0
    nickname: str = ""
    blocks: list[str] | None = None

    _FIELDS = [
        ("datacenter_id", "datacenterId", False, None),
        ("nickname", "nickname", True, None),
        ("blocks", "blocks", False, None),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> CIDRAssignment:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class CIDRMap:
    """GTM CIDR map.  Mirrors Go ``CIDRMap``."""

    default_datacenter: DatacenterBase | None = None
    assignments: list[CIDRAssignment] | None = None
    name: str = ""
    links: list[Link] | None = None

    _FIELDS = [
        ("default_datacenter", "defaultDatacenter", False, DatacenterBase),
        ("assignments", "assignments", True, (CIDRAssignment,)),
        ("name", "name", False, None),
        ("links", "links", True, (Link,)),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> CIDRMap:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]

    def validate(self) -> str | None:
        """Validate CIDR map constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_cidr_map(self)


@dataclass
class CIDRMapList:
    """List of CIDR maps.  Mirrors Go ``CIDRMapList``."""

    cidr_map_items: list[CIDRMap] | None = None

    _FIELDS = [
        ("cidr_map_items", "items", False, (CIDRMap,)),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> CIDRMapList:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


# -- CIDR Map request / response types --------------------------------

@dataclass
class CIDRMapRequest:
    """Request body for Create/Update CIDR map.  Mirrors Go ``CIDRMapRequest``.

    Note: The Go field name is ``CIDR *CIDRMap`` with JSON tag ``"cidrMap"``.
    """

    cidr_map: CIDRMap | None = None
    domain_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_create_cidr_map_request(self)


@dataclass
class GetCIDRMapRequest:
    """Parameters for GetCIDRMap.  Mirrors Go ``GetCIDRMapRequest``."""

    domain_name: str = ""
    cidr_map_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_get_cidr_map_request(self)


@dataclass
class ListCIDRMapsRequest:
    """Parameters for ListCIDRMaps.  Mirrors Go ``ListCIDRMapsRequest``."""

    domain_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_list_cidr_maps_request(self)


@dataclass
class DeleteCIDRMapRequest:
    """Parameters for DeleteCIDRMap.  Mirrors Go ``DeleteCIDRMapRequest``."""

    domain_name: str = ""
    cidr_map_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_delete_cidr_map_request(self)


@dataclass
class CreateCIDRMapResponse:
    """Response from CreateCIDRMap.  Mirrors Go ``CreateCIDRMapResponse``."""

    resource: CIDRMap | None = None
    status: ResponseStatus | None = None

    _FIELDS = [
        ("resource", "resource", True, CIDRMap),
        ("status", "status", True, ResponseStatus),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> CreateCIDRMapResponse:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class UpdateCIDRMapResponse:
    """Response from UpdateCIDRMap.  Mirrors Go ``UpdateCIDRMapResponse``."""

    resource: CIDRMap | None = None
    status: ResponseStatus | None = None

    _FIELDS = [
        ("resource", "resource", True, CIDRMap),
        ("status", "status", True, ResponseStatus),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> UpdateCIDRMapResponse:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class DeleteCIDRMapResponse:
    """Response from DeleteCIDRMap.  Mirrors Go ``DeleteCIDRMapResponse``."""

    resource: CIDRMap | None = None
    status: ResponseStatus | None = None

    _FIELDS = [
        ("resource", "resource", True, CIDRMap),
        ("status", "status", True, ResponseStatus),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> DeleteCIDRMapResponse:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


# CIDR Map type aliases
GetCIDRMapResponse = CIDRMap
CreateCIDRMapRequest = CIDRMapRequest
class UpdateCIDRMapRequest(CIDRMapRequest):
    """Update CIDR map request — delegates to update-specific validation."""

    def validate(self):
        """Validate the update CIDR map request fields."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_update_cidr_map_request(self)


# ===================================================================
# Domain types  (domain.go)
# ===================================================================

@dataclass
class NullPerObjectAttributeStruct:
    """Per-object null field attribute metadata.

    Mirrors Go ``NullPerObjectAttributeStruct``.  PascalCase JSON keys
    match the Go JSON tags exactly.
    """

    core_object_fields: dict[str, str] = field(default_factory=dict)
    child_object_fields: dict[str, Any] = field(default_factory=dict)

    _FIELDS = [
        ("core_object_fields", "CoreObjectFields", False, None),
        ("child_object_fields", "ChildObjectFields", False, None),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> NullPerObjectAttributeStruct:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class NullFieldMapStruct:
    """Null-field mapping across GTM entity types.

    Mirrors Go ``NullFieldMapStruct``.  PascalCase JSON keys match the Go
    JSON tags exactly.
    """

    domain: dict[str, NullPerObjectAttributeStruct] | None = None
    properties: dict[str, NullPerObjectAttributeStruct] | None = None
    datacenters: dict[str, NullPerObjectAttributeStruct] | None = None
    resources: dict[str, NullPerObjectAttributeStruct] | None = None
    cidr_maps: dict[str, NullPerObjectAttributeStruct] | None = None
    geo_maps: dict[str, NullPerObjectAttributeStruct] | None = None
    as_maps: dict[str, NullPerObjectAttributeStruct] | None = None

    _FIELDS = [
        ("domain", "Domain", False, (NullPerObjectAttributeStruct, "dict")),
        ("properties", "Properties", False, (NullPerObjectAttributeStruct, "dict")),
        ("datacenters", "Datacenters", False, (NullPerObjectAttributeStruct, "dict")),
        ("resources", "Resources", False, (NullPerObjectAttributeStruct, "dict")),
        ("cidr_maps", "CidrMaps", False, (NullPerObjectAttributeStruct, "dict")),
        ("geo_maps", "GeoMaps", False, (NullPerObjectAttributeStruct, "dict")),
        ("as_maps", "AsMaps", False, (NullPerObjectAttributeStruct, "dict")),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> NullFieldMapStruct:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class DomainItem:
    """Domain list item.  Mirrors Go ``DomainItem``."""

    acg_id: str = ""
    last_modified: str = ""
    links: list[Link] | None = None
    name: str = ""
    status: str = ""
    last_modified_by: str = ""
    change_id: str = ""
    activation_state: str = ""
    modification_comments: str = ""
    sign_and_serve: bool = False
    sign_and_serve_algorithm: str = ""
    delete_request_id: str = ""

    _FIELDS = [
        ("acg_id", "acgId", False, None),
        ("last_modified", "lastModified", False, None),
        ("links", "links", False, (Link,)),
        ("name", "name", False, None),
        ("status", "status", False, None),
        ("last_modified_by", "lastModifiedBy", False, None),
        ("change_id", "changeId", False, None),
        ("activation_state", "activationState", False, None),
        ("modification_comments", "modificationComments", False, None),
        ("sign_and_serve", "signAndServe", False, None),
        ("sign_and_serve_algorithm", "signAndServeAlgorithm", False, None),
        ("delete_request_id", "deleteRequestId", False, None),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> DomainItem:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class DomainsList:
    """List of domains.  Mirrors Go ``DomainsList``."""

    domain_items: list[DomainItem] | None = None

    _FIELDS = [
        ("domain_items", "items", False, (DomainItem,)),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> DomainsList:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class Domain:
    """GTM domain representation.  Mirrors Go ``Domain`` (43 fields)."""

    name: str = ""
    type: str = ""
    as_maps: list[ASMap] | None = None
    resources: list[Resource] | None = None
    default_unreachable_threshold: float = 0.0
    email_notification_list: list[str] | None = None
    min_pingable_region_fraction: float = 0.0
    default_timeout_penalty: int = 0
    datacenters: list[Datacenter] | None = None
    servermonitor_liveness_count: int = 0
    round_robin_prefix: str = ""
    servermonitor_load_count: int = 0
    ping_interval: int = 0
    max_ttl: int = 0
    load_imbalance_percentage: float = 0.0
    default_health_max: float = 0.0
    last_modified: str = ""
    status: ResponseStatus | None = None
    map_update_interval: int = 0
    max_properties: int = 0
    max_resources: int = 0
    default_ssl_client_private_key: str = ""
    default_error_penalty: int = 0
    links: list[Link] | None = None
    properties: list[Property] | None = None
    max_test_timeout: float = 0.0
    cname_coalescing_enabled: bool = False
    default_health_multiplier: float = 0.0
    servermonitor_pool: str = ""
    load_feedback: bool = False
    min_ttl: int = 0
    geographic_maps: list[GeoMap] | None = None
    cidr_maps: list[CIDRMap] | None = None
    default_max_unreachable_penalty: int = 0
    default_health_threshold: float = 0.0
    last_modified_by: str = ""
    modification_comments: str = ""
    min_test_interval: int = 0
    ping_packet_size: int = 0
    default_ssl_client_certificate: str = ""
    end_user_mapping_enabled: bool = False
    sign_and_serve: bool = False
    sign_and_serve_algorithm: str | None = None

    _FIELDS = [
        ("name", "name", False, None),
        ("type", "type", False, None),
        ("as_maps", "asMaps", True, (ASMap,)),
        ("resources", "resources", True, (Resource,)),
        ("default_unreachable_threshold", "defaultUnreachableThreshold", True, None),
        ("email_notification_list", "emailNotificationList", True, None),
        ("min_pingable_region_fraction", "minPingableRegionFraction", True, None),
        ("default_timeout_penalty", "defaultTimeoutPenalty", True, None),
        ("datacenters", "datacenters", True, (Datacenter,)),
        ("servermonitor_liveness_count", "servermonitorLivenessCount", True, None),
        ("round_robin_prefix", "roundRobinPrefix", True, None),
        ("servermonitor_load_count", "servermonitorLoadCount", True, None),
        ("ping_interval", "pingInterval", True, None),
        ("max_ttl", "maxTTL", True, None),
        ("load_imbalance_percentage", "loadImbalancePercentage", True, None),
        ("default_health_max", "defaultHealthMax", True, None),
        ("last_modified", "lastModified", True, None),
        ("status", "status", True, ResponseStatus),
        ("map_update_interval", "mapUpdateInterval", True, None),
        ("max_properties", "maxProperties", True, None),
        ("max_resources", "maxResources", True, None),
        ("default_ssl_client_private_key", "defaultSslClientPrivateKey", True, None),
        ("default_error_penalty", "defaultErrorPenalty", True, None),
        ("links", "links", True, (Link,)),
        ("properties", "properties", True, (Property,)),
        ("max_test_timeout", "maxTestTimeout", True, None),
        ("cname_coalescing_enabled", "cnameCoalescingEnabled", False, None),
        ("default_health_multiplier", "defaultHealthMultiplier", True, None),
        ("servermonitor_pool", "servermonitorPool", True, None),
        ("load_feedback", "loadFeedback", False, None),
        ("min_ttl", "minTTL", True, None),
        ("geographic_maps", "geographicMaps", True, (GeoMap,)),
        ("cidr_maps", "cidrMaps", True, (CIDRMap,)),
        ("default_max_unreachable_penalty", "defaultMaxUnreachablePenalty", False, None),
        ("default_health_threshold", "defaultHealthThreshold", True, None),
        ("last_modified_by", "lastModifiedBy", True, None),
        ("modification_comments", "modificationComments", True, None),
        ("min_test_interval", "minTestInterval", True, None),
        ("ping_packet_size", "pingPacketSize", True, None),
        ("default_ssl_client_certificate", "defaultSslClientCertificate", True, None),
        ("end_user_mapping_enabled", "endUserMappingEnabled", False, None),
        ("sign_and_serve", "signAndServe", False, None),
        ("sign_and_serve_algorithm", "signAndServeAlgorithm", False, None),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> Domain:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]

    def validate(self) -> str | None:
        """Validate domain constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_domain(self)


# -- Domain query/request helpers ------------------------------------

@dataclass
class DomainQueryArgs:
    """Query parameters for domain requests.  Mirrors Go ``DomainQueryArgs``.

    This struct has no JSON tags in Go — it carries URL query parameters,
    not a JSON body.
    """

    contract_id: str = ""
    group_id: str = ""


@dataclass
class DomainRequest:
    """Request body for Create/Update domain.  Mirrors Go ``DomainRequest``."""

    domain: Domain | None = None
    query_args: DomainQueryArgs | None = None

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_create_domain_request(self)


# -- Domain simple-field request types --------------------------------

@dataclass
class GetDomainStatusRequest:
    """Parameters for GetDomainStatus.  Mirrors Go ``GetDomainStatusRequest``."""

    domain_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_get_domain_status_request(self)


@dataclass
class GetDomainRequest:
    """Parameters for GetDomain.  Mirrors Go ``GetDomainRequest``."""

    domain_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_get_domain_request(self)


@dataclass
class DeleteDomainRequest:
    """Parameters for DeleteDomain (deprecated).  Mirrors Go ``DeleteDomainRequest``."""

    domain_name: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_delete_domain_request(self)


# -- Domain response types -------------------------------------------

@dataclass
class CreateDomainResponse:
    """Response from CreateDomain.  Mirrors Go ``CreateDomainResponse``."""

    resource: Domain | None = None
    status: ResponseStatus | None = None

    _FIELDS = [
        ("resource", "resource", True, Domain),
        ("status", "status", True, ResponseStatus),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> CreateDomainResponse:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class UpdateDomainResponse:
    """Response from UpdateDomain.  Mirrors Go ``UpdateDomainResponse``."""

    resource: Domain | None = None
    status: ResponseStatus | None = None

    _FIELDS = [
        ("resource", "resource", True, Domain),
        ("status", "status", True, ResponseStatus),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> UpdateDomainResponse:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class DeleteDomainResponse:
    """Response from DeleteDomain (deprecated).

    Mirrors Go ``DeleteDomainResponse`` which is defined as
    ``type DeleteDomainResponse ResponseStatus``.  Has the same fields as
    :class:`ResponseStatus`.
    """

    change_id: str = ""
    links: list[Link] | None = None
    message: str = ""
    passing_validation: bool = False
    propagation_status: str = ""
    propagation_status_date: str = ""

    _FIELDS = [
        ("change_id", "changeId", True, None),
        ("links", "links", True, (Link,)),
        ("message", "message", True, None),
        ("passing_validation", "passingValidation", True, None),
        ("propagation_status", "propagationStatus", True, None),
        ("propagation_status_date", "propagationStatusDate", True, None),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> DeleteDomainResponse:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


# -- Bulk domain deletion types --------------------------------------

@dataclass
class DeleteDomainsRequestBody:
    """Body for bulk domain deletion.  Mirrors Go ``DeleteDomainsRequestBody``.

    Go JSON tag maps ``DomainNames`` to ``"domains"``.
    """

    domain_names: list[str] | None = None

    _FIELDS = [
        ("domain_names", "domains", False, None),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> DeleteDomainsRequestBody:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class DeleteDomainsRequest:
    """Request for bulk domain deletion.  Mirrors Go ``DeleteDomainsRequest``."""

    bypass_safety_checks: bool | None = None
    body: DeleteDomainsRequestBody | None = None

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_delete_domains_request(self)


@dataclass
class DeleteDomainsResponse:
    """Response from bulk domain deletion.  Mirrors Go ``DeleteDomainsResponse``."""

    expiration_date: str = ""
    request_id: str = ""

    _FIELDS = [
        ("expiration_date", "expirationDate", False, None),
        ("request_id", "requestId", False, None),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> DeleteDomainsResponse:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


@dataclass
class DeleteDomainsStatusRequest:
    """Request for bulk domain deletion status.  Mirrors Go ``DeleteDomainsStatusRequest``."""

    request_id: str = ""

    def validate(self) -> str | None:
        """Validate request constraints."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_delete_domains_status_request(self)


@dataclass
class DeleteDomainsStatusResponse:
    """Response for bulk domain deletion status.  Mirrors Go ``DeleteDomainsStatusResponse``."""

    domains_submitted: int = 0
    expiration_date: str = ""
    failure_count: int = 0
    is_complete: bool = False
    request_id: str = ""
    success_count: int = 0

    _FIELDS = [
        ("domains_submitted", "domainsSubmitted", False, None),
        ("expiration_date", "expirationDate", False, None),
        ("failure_count", "failureCount", False, None),
        ("is_complete", "isComplete", False, None),
        ("request_id", "requestId", False, None),
        ("success_count", "successCount", False, None),
    ]

    def to_dict(self) -> dict:
        """Serialise to JSON-compatible dict."""
        return _to_dict_impl(self, self._FIELDS)

    @classmethod
    def from_dict(cls, data: dict | None) -> DeleteDomainsStatusResponse:
        """Deserialise from JSON-compatible dict."""
        return _from_dict_impl(cls, data, cls._FIELDS)  # type: ignore[return-value]


# -- Domain type aliases -----------------------------------------------

GetDomainStatusResponse = ResponseStatus
"""Type alias — Go ``GetDomainStatusResponse`` is ``ResponseStatus``."""

GetDomainResponse = Domain
"""Type alias — Go ``GetDomainResponse`` is ``Domain``."""

CreateDomainRequest = DomainRequest
"""Type alias — Go ``CreateDomainRequest`` is ``DomainRequest``."""

class UpdateDomainRequest(DomainRequest):
    """Update domain request — delegates to update-specific validation."""

    def validate(self):
        """Validate the update domain request fields."""
        from akamai.edgegrid.gtm import validation
        return validation.validate_update_domain_request(self)
