"""Request and response model dataclasses for the Cloudlets API."""
# pylint: disable=too-many-lines
from __future__ import annotations

import dataclasses as _dc
from dataclasses import dataclass, field
from typing import Any


# ============================================================================
# Module-level JSON serialization helpers (private)
# ============================================================================

# Non-standard snake_case → camelCase overrides
_GLOBAL_KEY_OVERRIDES: dict[str, str] = {
    "match_url": "matchURL",
    "redirect_url": "redirectURL",
    "check_ips": "checkIPs",
    "path_and_qs": "pathAndQS",
    "dry_run": "dryrun",
    "status_3xx_failure": "status3xxFailure",
    "status_4xx_failure": "status4xxFailure",
    "status_5xx_failure": "status5xxFailure",
}


def _snake_to_camel(name: str) -> str:
    """Convert a snake_case name to camelCase."""
    name = name.rstrip("_")
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _get_json_key(
    python_name: str, overrides: dict[str, str | None] | None = None
) -> str | None:
    """Return the JSON key for *python_name*, or ``None`` to exclude."""
    if overrides and python_name in overrides:
        return overrides[python_name]
    if python_name in _GLOBAL_KEY_OVERRIDES:
        return _GLOBAL_KEY_OVERRIDES[python_name]
    return _snake_to_camel(python_name)


def _is_empty(value: Any) -> bool:
    """Return ``True`` when *value* represents a Go zero-value (omitempty)."""
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


def _serialize_value(value: Any) -> Any:
    """Recursively convert *value* for JSON output."""
    if value is None:
        return None
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    return value


def _to_dict(obj: Any) -> dict:
    """Generic ``to_dict`` implementation for model dataclasses.

    Reads class-level ``_excludes``, ``_omitempty``, ``_overrides`` and
    ``_promote`` attributes to control serialization behaviour.
    """
    cls = type(obj)
    excludes: frozenset = getattr(cls, "_excludes", frozenset())
    omitempty: frozenset = getattr(cls, "_omitempty", frozenset())
    overrides: dict = getattr(cls, "_overrides", {})
    promote: frozenset = getattr(cls, "_promote", frozenset())

    result: dict = {}
    for fld in _dc.fields(obj):
        name = fld.name
        if name in excludes:
            continue
        json_key = _get_json_key(name, overrides)
        if json_key is None:
            continue
        value = getattr(obj, name)
        # Promoted (embedded) field — flatten its dict into the result
        if name in promote:
            if value is not None and hasattr(value, "to_dict"):
                result.update(value.to_dict())
            continue
        if name in omitempty and _is_empty(value):
            continue
        result[json_key] = _serialize_value(value)
    return result


def _build_json_to_python(cls: type, overrides: dict) -> dict[str, str]:
    """Build a reverse map from JSON key → Python attribute name."""
    mapping: dict[str, str] = {}
    for fld in _dc.fields(cls):
        json_key = _get_json_key(fld.name, overrides)
        if json_key is not None:
            mapping[json_key] = fld.name
    return mapping


def _from_dict(cls: type, data: dict | None) -> Any:  # pylint: disable=too-many-locals
    """Generic ``from_dict`` implementation for model dataclasses.

    Reads class-level ``_excludes``, ``_overrides``, ``_nested``,
    ``_nested_list``, ``_nested_dict_val`` and ``_promote_from`` attributes
    to control deserialization behaviour.
    """
    if data is None:
        return None

    excludes: frozenset = getattr(cls, "_excludes", frozenset())
    overrides: dict = getattr(cls, "_overrides", {})
    nested: dict = getattr(cls, "_nested", {})
    nested_list: dict = getattr(cls, "_nested_list", {})
    nested_dict_val: dict = getattr(cls, "_nested_dict_val", {})
    promote_from: dict = getattr(cls, "_promote_from", {})

    json_to_py = _build_json_to_python(cls, overrides)

    kwargs: dict = {}
    for json_key, value in data.items():
        py_name = json_to_py.get(json_key)
        if py_name is None or py_name in excludes:
            continue
        if py_name in nested and isinstance(value, dict):
            kwargs[py_name] = nested[py_name].from_dict(value)
        elif py_name in nested_list and isinstance(value, list):
            item_cls = nested_list[py_name]
            kwargs[py_name] = [
                item_cls.from_dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        elif py_name in nested_dict_val and isinstance(value, dict):
            val_cls = nested_dict_val[py_name]
            kwargs[py_name] = {
                k: val_cls.from_dict(v) if isinstance(v, dict) else v
                for k, v in value.items()
            }
        else:
            kwargs[py_name] = value

    # Promoted (embedded) fields — construct from the whole flat dict
    for py_name, promote_cls in promote_from.items():
        if py_name not in kwargs:
            kwargs[py_name] = promote_cls.from_dict(data)

    return cls(**kwargs)


# ============================================================================
# Constants — Origin types
# ============================================================================

ORIGIN_TYPE_ALL: str = ""
ORIGIN_TYPE_CUSTOMER: str = "CUSTOMER"
ORIGIN_TYPE_APPLICATION_LOAD_BALANCER: str = "APPLICATION_LOAD_BALANCER"
ORIGIN_TYPE_NETSTORAGE: str = "NETSTORAGE"

# ============================================================================
# Constants — Policy activation status
# ============================================================================

POLICY_ACTIVATION_STATUS_ACTIVE: str = "active"
POLICY_ACTIVATION_STATUS_DEACTIVATED: str = "deactivated"
POLICY_ACTIVATION_STATUS_INACTIVE: str = "inactive"
POLICY_ACTIVATION_STATUS_PENDING: str = "pending"
POLICY_ACTIVATION_STATUS_FAILED: str = "failed"

# ============================================================================
# Constants — Balancing types
# ============================================================================

BALANCING_TYPE_WEIGHTED: str = "WEIGHTED"
BALANCING_TYPE_PERFORMANCE: str = "PERFORMANCE"

# ============================================================================
# Constants — Load balancer activation status
# ============================================================================

LB_ACTIVATION_STATUS_ACTIVE: str = "active"
LB_ACTIVATION_STATUS_DEACTIVATED: str = "deactivated"
LB_ACTIVATION_STATUS_INACTIVE: str = "inactive"
LB_ACTIVATION_STATUS_PENDING: str = "pending"
LB_ACTIVATION_STATUS_FAILED: str = "failed"

# ============================================================================
# Constants — Load balancer activation network
# ============================================================================

LB_ACTIVATION_NETWORK_STAGING: str = "STAGING"
LB_ACTIVATION_NETWORK_PRODUCTION: str = "PRODUCTION"
NETWORK_PARAM_STAGING: str = "staging"
NETWORK_PARAM_PRODUCTION: str = "prod"

# ============================================================================
# Constants — Policy activation network
# ============================================================================

POLICY_ACTIVATION_NETWORK_STAGING: str = "staging"
POLICY_ACTIVATION_NETWORK_PRODUCTION: str = "prod"

# ============================================================================
# Constants — Match rule types
# ============================================================================

MATCH_RULE_TYPE_ALB: str = "albMatchRule"
MATCH_RULE_TYPE_AP: str = "apMatchRule"
MATCH_RULE_TYPE_AS: str = "asMatchRule"
MATCH_RULE_TYPE_PR: str = "cdMatchRule"
MATCH_RULE_TYPE_ER: str = "erMatchRule"
MATCH_RULE_TYPE_FR: str = "frMatchRule"
MATCH_RULE_TYPE_RC: str = "igMatchRule"
MATCH_RULE_TYPE_VP: str = "vpMatchRule"

# ============================================================================
# Constants — Match rule format
# ============================================================================

MATCH_RULE_FORMAT_10: str = "1.0"

# ============================================================================
# Constants — Match operator
# ============================================================================

MATCH_OPERATOR_CONTAINS: str = "contains"
MATCH_OPERATOR_EXISTS: str = "exists"
MATCH_OPERATOR_EQUALS: str = "equals"

# ============================================================================
# Constants — Allow / Deny
# ============================================================================

ALLOW: str = "allow"
DENY: str = "deny"
DENY_BRANDED: str = "denybranded"

# ============================================================================
# Constants — CheckIPs
# ============================================================================

CHECK_IPS_CONNECTING_IP: str = "CONNECTING_IP"
CHECK_IPS_XFF_HEADERS: str = "XFF_HEADERS"
CHECK_IPS_CONNECTING_IP_XFF_HEADERS: str = "CONNECTING_IP XFF_HEADERS"

# ============================================================================
# Constants — ObjectMatchValue types
# ============================================================================

OBJECT_MATCH_VALUE_RANGE: str = "range"
OBJECT_MATCH_VALUE_SIMPLE: str = "simple"
OBJECT_MATCH_VALUE_OBJECT: str = "object"


# ============================================================================
# Model dataclasses — Warning
# ============================================================================


@dataclass
class Warning:  # pylint: disable=redefined-builtin
    """Cloudlet API warning message."""

    detail: str = ""
    json_pointer: str = ""
    status: int = 0
    title: str = ""
    type: str = ""

    _omitempty = frozenset({"detail", "json_pointer", "status", "title", "type"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Warning:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


# ============================================================================
# Model dataclasses — Origin types (loadbalancer.go)
# ============================================================================


@dataclass
class Description:
    """Embedded description payload."""

    description: str = ""

    _omitempty = frozenset({"description"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Description:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class Origin:
    """Cloudlet origin definition."""

    origin_id: str = ""
    description: str = ""
    akamaized: bool = False
    checksum: str = ""
    type: str = ""

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Origin:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class OriginResponse:
    """Origin response with hostname (Go embeds Origin)."""

    hostname: str = ""
    origin_id: str = ""
    description: str = ""
    akamaized: bool = False
    checksum: str = ""
    type: str = ""

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> OriginResponse:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class ListOriginsRequest:
    """Request parameters for listing origins."""

    type: str = ""

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ListOriginsRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class GetOriginRequest:
    """Request parameters for getting a single origin."""

    origin_id: str = ""

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> GetOriginRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class CreateOriginRequest:
    """Request payload for creating an origin (embeds Description)."""

    origin_id: str = ""
    description: str = ""

    _omitempty = frozenset({"description"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> CreateOriginRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class UpdateOriginRequest:
    """Request payload for updating an origin (embeds Description)."""

    origin_id: str = ""
    description: str = ""

    _excludes = frozenset({"origin_id"})
    _omitempty = frozenset({"description"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> UpdateOriginRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


# ============================================================================
# Model dataclasses — Policy types (policy.go)
# ============================================================================


@dataclass
class PolicyInfo:
    """Policy activation information."""

    policy_id: int = 0
    name: str = ""
    version: int = 0
    status: str = ""
    status_detail: str = ""
    activated_by: str = ""
    activation_date: int = 0

    _omitempty = frozenset({"status_detail"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> PolicyInfo:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class PropertyInfo:
    """Property activation information."""

    name: str = ""
    version: int = 0
    group_id: int = 0
    status: str = ""
    activated_by: str = ""
    activation_date: int = 0

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> PropertyInfo:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class PolicyActivation:
    """A single activation entry for a policy."""

    api_version: str = ""
    network: str = ""
    policy_info: PolicyInfo | None = None
    property_info: PropertyInfo | None = None

    _nested = {"policy_info": PolicyInfo, "property_info": PropertyInfo}

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> PolicyActivation:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class Policy:  # pylint: disable=too-many-instance-attributes
    """Cloudlet policy definition."""

    location: str = ""
    policy_id: int = 0
    group_id: int = 0
    name: str = ""
    description: str = ""
    created_by: str = ""
    create_date: float = 0.0
    last_modified_by: str = ""
    last_modified_date: float = 0.0
    activations: list[PolicyActivation] = field(default_factory=list)
    cloudlet_id: int = 0
    cloudlet_code: str = ""
    api_version: str = ""
    deleted: bool = False

    _nested_list = {"activations": PolicyActivation}

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Policy:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class GetPolicyRequest:
    """Request parameters for getting a single policy."""

    policy_id: int = 0

    _excludes = frozenset({"policy_id"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> GetPolicyRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class CreatePolicyRequest:
    """Request payload for creating a policy."""

    name: str = ""
    cloudlet_id: int = 0
    description: str = ""
    property_name: str = ""
    group_id: int = 0

    _omitempty = frozenset({"description", "property_name", "group_id"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> CreatePolicyRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class UpdatePolicy:
    """Body portion of an update-policy request."""

    name: str = ""
    description: str = ""
    property_name: str = ""
    group_id: int = 0
    deleted: bool = False

    _omitempty = frozenset(
        {"name", "description", "property_name", "group_id", "deleted"}
    )

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> UpdatePolicy:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class UpdatePolicyRequest:
    """Request wrapper for updating a policy (Go embeds UpdatePolicy)."""

    update_policy: UpdatePolicy | None = None
    policy_id: int = 0

    _excludes = frozenset({"policy_id"})
    _promote = frozenset({"update_policy"})
    _promote_from = {"update_policy": UpdatePolicy}

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> UpdatePolicyRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class ListPoliciesRequest:
    """Request parameters for listing policies."""

    cloudlet_id: int | None = None
    include_deleted: bool = False
    offset: int = 0
    page_size: int | None = None

    _excludes = frozenset(
        {"cloudlet_id", "include_deleted", "offset", "page_size"}
    )

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ListPoliciesRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class RemovePolicyRequest:
    """Request parameters for removing a policy."""

    policy_id: int = 0

    _excludes = frozenset({"policy_id"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> RemovePolicyRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


# ============================================================================
# Model dataclasses — LoadBalancer version types (loadbalancer_version.go)
# ============================================================================


@dataclass
class DataCenter:  # pylint: disable=too-many-instance-attributes
    """Load balancer data center configuration."""

    city: str = ""
    cloud_server_host_header_override: bool = False
    cloud_service: bool = False
    continent: str = ""
    country: str = ""
    hostname: str = ""
    latitude: float | None = None
    liveness_hosts: list[str] = field(default_factory=list)
    longitude: float | None = None
    origin_id: str = ""
    percent: float | None = None
    state_or_province: str | None = None

    _omitempty = frozenset({
        "city", "cloud_server_host_header_override", "hostname",
        "liveness_hosts", "state_or_province",
    })

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> DataCenter:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class LivenessSettings:  # pylint: disable=too-many-instance-attributes
    """Load balancer liveness check configuration."""

    host_header: str = ""
    additional_headers: dict[str, str] = field(default_factory=dict)
    interval: int = 0
    path: str = ""
    peer_certificate_verification: bool = False
    port: int = 0
    protocol: str = ""
    request_string: str = ""
    response_string: str = ""
    status_3xx_failure: bool = False
    status_4xx_failure: bool = False
    status_5xx_failure: bool = False
    timeout: float = 0.0

    _omitempty = frozenset({
        "host_header", "additional_headers", "interval", "path",
        "peer_certificate_verification", "request_string", "response_string",
        "status_3xx_failure", "status_4xx_failure", "status_5xx_failure",
        "timeout",
    })

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> LivenessSettings:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class LoadBalancerVersion:  # pylint: disable=too-many-instance-attributes
    """Load balancer version definition."""

    balancing_type: str = ""
    created_by: str = ""
    created_date: str = ""
    data_centers: list[DataCenter] = field(default_factory=list)
    deleted: bool = False
    description: str = ""
    immutable: bool = False
    last_modified_by: str = ""
    last_modified_date: str = ""
    liveness_settings: LivenessSettings | None = None
    origin_id: str = ""
    version: int = 0
    warnings: list[Warning] = field(default_factory=list)

    # Note: Go JSON tag for origin_id is "originID" (capital D)
    _overrides = {"origin_id": "originID"}
    _omitempty = frozenset({
        "balancing_type", "created_by", "created_date", "data_centers",
        "description", "last_modified_by", "last_modified_date",
        "liveness_settings", "version", "warnings",
    })
    _nested = {"liveness_settings": LivenessSettings}
    _nested_list = {"data_centers": DataCenter, "warnings": Warning}

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> LoadBalancerVersion:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class CreateLoadBalancerVersionRequest:
    """Request wrapper for creating a load balancer version."""

    origin_id: str = ""
    load_balancer_version: LoadBalancerVersion | None = None

    _excludes = frozenset({"origin_id", "load_balancer_version"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> CreateLoadBalancerVersionRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class GetLoadBalancerVersionRequest:
    """Request parameters for getting a load balancer version."""

    origin_id: str = ""
    version: int = 0
    should_validate: bool = False

    _excludes = frozenset({"origin_id", "version", "should_validate"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> GetLoadBalancerVersionRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class UpdateLoadBalancerVersionRequest:
    """Request wrapper for updating a load balancer version."""

    origin_id: str = ""
    should_validate: bool = False
    version: int = 0
    load_balancer_version: LoadBalancerVersion | None = None

    _excludes = frozenset({
        "origin_id", "should_validate", "version", "load_balancer_version",
    })

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> UpdateLoadBalancerVersionRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class ListLoadBalancerVersionsRequest:
    """Request parameters for listing load balancer versions."""

    origin_id: str = ""

    _excludes = frozenset({"origin_id"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ListLoadBalancerVersionsRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


# ============================================================================
# Model dataclasses — LoadBalancer activation types (loadbalancer_activation.go)
# ============================================================================


@dataclass
class LoadBalancerVersionActivation:
    """Payload for activating a load balancer version."""

    network: str = ""
    dry_run: bool = False
    version: int = 0

    _overrides = {"dry_run": "dryrun"}

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> LoadBalancerVersionActivation:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class LoadBalancerActivation:
    """Load balancer activation status record."""

    activated_by: str = ""
    activated_date: str = ""
    network: str = ""
    origin_id: str = ""
    status: str = ""
    dry_run: bool = False
    version: int = 0

    _overrides = {"dry_run": "dryrun"}
    _omitempty = frozenset({
        "activated_by", "activated_date", "network", "origin_id",
        "status", "version",
    })

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> LoadBalancerActivation:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class ListLoadBalancerActivationsRequest:
    """Request parameters for listing load balancer activations."""

    origin_id: str = ""
    network: str = ""
    latest_only: bool = False
    page_size: int | None = None
    page: int | None = None

    _excludes = frozenset({
        "origin_id", "network", "latest_only", "page_size", "page",
    })

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ListLoadBalancerActivationsRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class ActivateLoadBalancerVersionRequest:
    """Request wrapper for activating a load balancer version."""

    origin_id: str = ""
    async_: bool = False
    load_balancer_version_activation: LoadBalancerVersionActivation | None = None

    _excludes = frozenset({
        "origin_id", "async_", "load_balancer_version_activation",
    })

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ActivateLoadBalancerVersionRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


# ============================================================================
# Model dataclasses — Policy version types (policy_version.go)
# ============================================================================


@dataclass
class CreatePolicyVersion:
    """Body for creating a new policy version."""

    description: str = ""
    match_rule_format: str = ""
    match_rules: list = field(default_factory=list)

    _omitempty = frozenset({"description", "match_rule_format", "match_rules"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> CreatePolicyVersion:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class UpdatePolicyVersion:
    """Body for updating an existing policy version."""

    description: str = ""
    match_rule_format: str = ""
    match_rules: list = field(default_factory=list)
    deleted: bool = False

    _omitempty = frozenset({
        "description", "match_rule_format", "match_rules",
    })

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> UpdatePolicyVersion:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class PolicyVersion:  # pylint: disable=too-many-instance-attributes
    """A specific version of a cloudlets policy."""

    location: str = ""
    revision_id: int = 0
    policy_id: int = 0
    version: int = 0
    description: str = ""
    created_by: str = ""
    create_date: int = 0
    last_modified_by: str = ""
    last_modified_date: int = 0
    rules_locked: bool = False
    activations: list[PolicyActivation] = field(default_factory=list)
    match_rules: list = field(default_factory=list)
    match_rule_format: str = ""
    deleted: bool = False
    warnings: list[Warning] = field(default_factory=list)

    _omitempty = frozenset({
        "location", "revision_id", "policy_id", "version", "description",
        "created_by", "create_date", "last_modified_by", "last_modified_date",
        "activations", "match_rules", "match_rule_format", "warnings",
    })
    _nested_list = {"activations": PolicyActivation, "warnings": Warning}

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> PolicyVersion:
        """Deserialize from a dict with camelCase JSON keys.

        Overrides the generic helper so that ``matchRules`` is routed
        through :func:`unmarshal_match_rules` for polymorphic dispatch.
        """
        result = _from_dict(cls, data)
        if result is not None and isinstance(data, dict):
            raw_rules = data.get("matchRules")
            if raw_rules is not None:
                result.match_rules = unmarshal_match_rules(raw_rules)
        return result


@dataclass
class ListPolicyVersionsRequest:
    """Request parameters for listing policy versions."""

    policy_id: int = 0
    include_rules: bool = False
    include_deleted: bool = False
    include_activations: bool = False
    offset: int = 0
    page_size: int | None = None

    _excludes = frozenset({
        "policy_id", "include_rules", "include_deleted",
        "include_activations", "offset", "page_size",
    })

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ListPolicyVersionsRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class GetPolicyVersionRequest:
    """Request parameters for getting a policy version."""

    policy_id: int = 0
    version: int = 0
    omit_rules: bool = False

    _excludes = frozenset({"policy_id", "version", "omit_rules"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> GetPolicyVersionRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class CreatePolicyVersionRequest:
    """Request wrapper for creating a policy version."""

    create_policy_version: CreatePolicyVersion | None = None
    policy_id: int = 0

    _excludes = frozenset({"create_policy_version", "policy_id"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> CreatePolicyVersionRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class DeletePolicyVersionRequest:
    """Request parameters for deleting a policy version."""

    policy_id: int = 0
    version: int = 0

    _excludes = frozenset({"policy_id", "version"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> DeletePolicyVersionRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class UpdatePolicyVersionRequest:
    """Request wrapper for updating a policy version."""

    update_policy_version: UpdatePolicyVersion | None = None
    policy_id: int = 0
    version: int = 0

    _excludes = frozenset({
        "update_policy_version", "policy_id", "version",
    })

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> UpdatePolicyVersionRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


# ============================================================================
# Model dataclasses — Policy version activation (policy_version_activation.go)
# ============================================================================


@dataclass
class PolicyVersionActivation:
    """Payload for activating a policy version."""

    network: str = ""
    additional_property_names: list[str] = field(default_factory=list)

    _omitempty = frozenset({"additional_property_names"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> PolicyVersionActivation:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class ListPolicyActivationsRequest:
    """Request parameters for listing policy activations."""

    policy_id: int = 0
    network: str = ""
    property_name: str = ""

    _excludes = frozenset({"policy_id", "network", "property_name"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ListPolicyActivationsRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class ActivatePolicyVersionRequest:
    """Request wrapper for activating a policy version."""

    policy_id: int = 0
    async_: bool = False
    version: int = 0
    policy_version_activation: PolicyVersionActivation | None = None

    _excludes = frozenset({
        "policy_id", "async_", "version", "policy_version_activation",
    })

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ActivatePolicyVersionRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


# ============================================================================
# Model dataclasses — Policy property types (policy_property.go)
# ============================================================================


@dataclass
class CloudletsOrigin:
    """A cloudlet origin entry within a network status."""

    origin_id: str = ""
    hostname: str = ""
    type: str = ""
    checksum: str = ""
    description: str = ""

    # Go JSON tag for origin_id is "id"
    _overrides = {"origin_id": "id"}

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> CloudletsOrigin:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class NetworkStatus:
    """Activation status for a specific network."""

    activated_by: str = ""
    activation_date: str = ""
    version: int = 0
    cloudlets_origins: dict[str, CloudletsOrigin] = field(default_factory=dict)
    referenced_policies: list[str] = field(default_factory=list)

    _nested_dict_val = {"cloudlets_origins": CloudletsOrigin}

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> NetworkStatus:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class PolicyProperty:
    """A property associated with a cloudlet policy."""

    group_id: int = 0
    id: int = 0
    name: str = ""
    newest_version: NetworkStatus | None = None
    production: NetworkStatus | None = None
    staging: NetworkStatus | None = None

    _nested = {
        "newest_version": NetworkStatus,
        "production": NetworkStatus,
        "staging": NetworkStatus,
    }

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> PolicyProperty:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class GetPolicyPropertiesRequest:
    """Request parameters for listing policy properties."""

    policy_id: int = 0

    _excludes = frozenset({"policy_id"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> GetPolicyPropertiesRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class DeletePolicyPropertyRequest:
    """Request parameters for deleting a policy property binding."""

    policy_id: int = 0
    property_id: int = 0
    network: str = ""

    _excludes = frozenset({"policy_id", "property_id", "network"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> DeletePolicyPropertyRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


# ============================================================================
# Model dataclasses — Policy version rule types (policy_version_rule.go)
# ============================================================================


@dataclass
class GetPolicyVersionRuleRequest:
    """Request parameters for getting a policy version rule."""

    aka_rule_id: str = ""
    version: int = 0
    policy_id: int = 0

    _excludes = frozenset({"aka_rule_id", "version", "policy_id"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> GetPolicyVersionRuleRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class CreatePolicyVersionRuleRequest:
    """Request wrapper for creating a policy version rule."""

    version: int = 0
    policy_id: int = 0
    index: int = 0
    match_rule: dict | None = None

    _excludes = frozenset({"version", "policy_id", "index", "match_rule"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> CreatePolicyVersionRuleRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class UpdatePolicyVersionRuleRequest:
    """Request wrapper for updating a policy version rule."""

    aka_rule_id: str = ""
    version: int = 0
    policy_id: int = 0
    match_rule: dict | None = None

    _excludes = frozenset({
        "aka_rule_id", "version", "policy_id", "match_rule",
    })

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> UpdatePolicyVersionRuleRequest:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


# ============================================================================
# Model dataclasses — Match rule types (match_rule.go)
# ============================================================================


@dataclass
class Options:
    """Matching option values within an ObjectMatchValueObject."""

    value: list[str] = field(default_factory=list)
    value_has_wildcard: bool = False
    value_case_sensitive: bool = False
    value_escaped: bool = False

    _omitempty = frozenset({
        "value", "value_has_wildcard", "value_case_sensitive", "value_escaped",
    })

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Options:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class ObjectMatchValueObject:
    """Object-typed object match value in match criteria."""

    name: str = ""
    type: str = ""
    name_case_sensitive: bool = False
    name_has_wildcard: bool = False
    options: Options | None = None

    _omitempty = frozenset({
        "name", "name_case_sensitive", "name_has_wildcard", "options",
    })
    _nested = {"options": Options}

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ObjectMatchValueObject:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class ObjectMatchValueSimple:
    """Simple-typed object match value in match criteria."""

    type: str = ""
    value: list[str] = field(default_factory=list)

    _omitempty = frozenset({"value"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ObjectMatchValueSimple:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class ObjectMatchValueRange:
    """Range-typed object match value in match criteria."""

    type: str = ""
    value: list[int] = field(default_factory=list)

    _omitempty = frozenset({"value"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ObjectMatchValueRange:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class MatchCriteria:
    """Base match criteria shared by all cloudlet match rule types."""

    match_type: str = ""
    match_value: str = ""
    match_operator: str = ""
    case_sensitive: bool = False
    negate: bool = False
    check_ips: str = ""
    object_match_value: Any = None

    _omitempty = frozenset({
        "match_type", "match_value", "match_operator",
        "check_ips", "object_match_value",
    })

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> MatchCriteria:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


# Type aliases for cloudlet-type-specific match criteria.
# In Go these are declared as separate types but have identical fields.
MatchCriteriaALB = MatchCriteria
MatchCriteriaAP = MatchCriteria
MatchCriteriaAS = MatchCriteria
MatchCriteriaPR = MatchCriteria
MatchCriteriaER = MatchCriteria
MatchCriteriaFR = MatchCriteria
MatchCriteriaRC = MatchCriteria
MatchCriteriaVP = MatchCriteria


@dataclass
class ForwardSettingsALB:
    """Forward settings for Application Load Balancer match rules."""

    origin_id: str = ""

    _omitempty = frozenset({"origin_id"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ForwardSettingsALB:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class ForwardSettingsAS:
    """Forward settings for API Prioritization match rules."""

    path_and_qs: str = ""
    use_incoming_query_string: bool = False
    origin_id: str = ""

    _omitempty = frozenset({
        "path_and_qs", "use_incoming_query_string", "origin_id",
    })

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ForwardSettingsAS:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class ForwardSettingsPR:
    """Forward settings for Phased Release match rules."""

    origin_id: str = ""
    percent: int = 0

    _omitempty = frozenset({"origin_id"})

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ForwardSettingsPR:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class ForwardSettingsFR:
    """Forward settings for Forward Rewrite match rules."""

    path_and_qs: str = ""
    use_incoming_query_string: bool = False
    origin_id: str = ""

    _omitempty = frozenset({
        "path_and_qs", "use_incoming_query_string", "origin_id",
    })

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ForwardSettingsFR:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


# ============================================================================
# Model dataclasses — Match rule variants (match_rule.go)
# ============================================================================


@dataclass
class MatchRuleALB:  # pylint: disable=too-many-instance-attributes
    """Application Load Balancer match rule."""

    name: str = ""
    type: str = ""
    start: int = 0
    end: int = 0
    id: int = 0
    matches: list[MatchCriteria] = field(default_factory=list)
    match_url: str = ""
    matches_always: bool = False
    forward_settings: ForwardSettingsALB | None = None
    disabled: bool = False
    aka_rule_id: str = ""
    location: str = ""

    _omitempty = frozenset({
        "name", "start", "end", "id", "matches", "match_url",
        "matches_always", "forward_settings", "disabled",
        "aka_rule_id", "location",
    })
    _nested = {"forward_settings": ForwardSettingsALB}
    _nested_list = {"matches": MatchCriteria}

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> MatchRuleALB:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class MatchRuleAP:  # pylint: disable=too-many-instance-attributes
    """Audience Segmentation (AP) match rule."""

    name: str = ""
    type: str = ""
    start: int = 0
    end: int = 0
    id: int = 0
    matches: list[MatchCriteria] = field(default_factory=list)
    match_url: str = ""
    pass_through_percent: float | None = None
    disabled: bool = False
    aka_rule_id: str = ""
    location: str = ""

    _omitempty = frozenset({
        "name", "start", "end", "id", "matches", "match_url",
        "pass_through_percent", "disabled", "aka_rule_id", "location",
    })
    _nested_list = {"matches": MatchCriteria}

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> MatchRuleAP:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class MatchRuleAS:  # pylint: disable=too-many-instance-attributes
    """API Prioritization (AS) match rule."""

    name: str = ""
    type: str = ""
    start: int = 0
    end: int = 0
    id: int = 0
    matches: list[MatchCriteria] = field(default_factory=list)
    match_url: str = ""
    forward_settings: ForwardSettingsAS | None = None
    disabled: bool = False
    aka_rule_id: str = ""
    location: str = ""

    _omitempty = frozenset({
        "name", "start", "end", "id", "matches", "match_url",
        "forward_settings", "disabled", "aka_rule_id", "location",
    })
    _nested = {"forward_settings": ForwardSettingsAS}
    _nested_list = {"matches": MatchCriteria}

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> MatchRuleAS:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class MatchRulePR:  # pylint: disable=too-many-instance-attributes
    """Phased Release (PR) match rule."""

    name: str = ""
    type: str = ""
    start: int = 0
    end: int = 0
    id: int = 0
    matches: list[MatchCriteria] = field(default_factory=list)
    match_url: str = ""
    forward_settings: ForwardSettingsPR | None = None
    disabled: bool = False
    matches_always: bool = False
    aka_rule_id: str = ""
    location: str = ""

    _omitempty = frozenset({
        "name", "start", "end", "id", "matches", "match_url",
        "forward_settings", "disabled", "matches_always",
        "aka_rule_id", "location",
    })
    _nested = {"forward_settings": ForwardSettingsPR}
    _nested_list = {"matches": MatchCriteria}

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> MatchRulePR:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class MatchRuleER:  # pylint: disable=too-many-instance-attributes
    """Edge Redirector (ER) match rule."""

    name: str = ""
    type: str = ""
    start: int = 0
    end: int = 0
    id: int = 0
    matches: list[MatchCriteria] = field(default_factory=list)
    matches_always: bool = False
    use_relative_url: str = ""
    status_code: int = 0
    redirect_url: str = ""
    match_url: str = ""
    use_incoming_query_string: bool = False
    use_incoming_scheme_and_host: bool = False
    disabled: bool = False
    aka_rule_id: str = ""
    location: str = ""

    _omitempty = frozenset({
        "name", "start", "end", "id", "matches", "matches_always",
        "use_relative_url", "status_code", "redirect_url", "match_url",
        "use_incoming_query_string", "use_incoming_scheme_and_host",
        "disabled", "aka_rule_id", "location",
    })
    _nested_list = {"matches": MatchCriteria}

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> MatchRuleER:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class MatchRuleFR:  # pylint: disable=too-many-instance-attributes
    """Forward Rewrite (FR) match rule."""

    name: str = ""
    type: str = ""
    start: int = 0
    end: int = 0
    id: int = 0
    matches: list[MatchCriteria] = field(default_factory=list)
    match_url: str = ""
    forward_settings: ForwardSettingsFR | None = None
    disabled: bool = False
    aka_rule_id: str = ""
    location: str = ""

    _omitempty = frozenset({
        "name", "start", "end", "id", "matches", "match_url",
        "forward_settings", "disabled", "aka_rule_id", "location",
    })
    _nested = {"forward_settings": ForwardSettingsFR}
    _nested_list = {"matches": MatchCriteria}

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> MatchRuleFR:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class MatchRuleRC:  # pylint: disable=too-many-instance-attributes
    """Request Control (RC) match rule."""

    name: str = ""
    type: str = ""
    start: int = 0
    end: int = 0
    id: int = 0
    matches: list[MatchCriteria] = field(default_factory=list)
    matches_always: bool = False
    allow_deny: str = ""
    disabled: bool = False
    aka_rule_id: str = ""
    location: str = ""

    _omitempty = frozenset({
        "name", "start", "end", "id", "matches", "matches_always",
        "allow_deny", "disabled", "aka_rule_id", "location",
    })
    _nested_list = {"matches": MatchCriteria}

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> MatchRuleRC:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


@dataclass
class MatchRuleVP:  # pylint: disable=too-many-instance-attributes
    """Visitor Prioritization (VP) match rule."""

    name: str = ""
    type: str = ""
    start: int = 0
    end: int = 0
    id: int = 0
    matches: list[MatchCriteria] = field(default_factory=list)
    match_url: str = ""
    pass_through_percent: float | None = None
    disabled: bool = False
    aka_rule_id: str = ""
    location: str = ""

    _omitempty = frozenset({
        "name", "start", "end", "id", "matches", "match_url",
        "pass_through_percent", "disabled", "aka_rule_id", "location",
    })
    _nested_list = {"matches": MatchCriteria}

    def to_dict(self) -> dict:
        """Serialize to a dict with camelCase JSON keys."""
        return _to_dict(self)

    @classmethod
    def from_dict(cls, data: dict) -> MatchRuleVP:
        """Deserialize from a dict with camelCase JSON keys."""
        return _from_dict(cls, data)


# ============================================================================
# Polymorphic deserialization helpers (mirrors Go UnmarshalJSON)
# ============================================================================

# Handler maps for dispatching match rules by their "type" field.
_MATCH_RULE_HANDLERS: dict[str, type] = {
    "albMatchRule": MatchRuleALB,
    "apMatchRule": MatchRuleAP,
    "asMatchRule": MatchRuleAS,
    "cdMatchRule": MatchRulePR,
    "erMatchRule": MatchRuleER,
    "frMatchRule": MatchRuleFR,
    "igMatchRule": MatchRuleRC,
    "vpMatchRule": MatchRuleVP,
}

# ObjectMatchValue handler maps.
# ALB and AS accept all three types.
_OBJECT_MATCH_VALUE_ALL: dict[str, type] = {
    "object": ObjectMatchValueObject,
    "simple": ObjectMatchValueSimple,
    "range": ObjectMatchValueRange,
}

# AP, PR, ER, FR, RC, VP accept only simple and object types.
_OBJECT_MATCH_VALUE_SIMPLE_OBJECT: dict[str, type] = {
    "object": ObjectMatchValueObject,
    "simple": ObjectMatchValueSimple,
}

# Mapping of match-rule type string → ObjectMatchValue handler map.
_OBJECT_MATCH_VALUE_MAP: dict[str, dict[str, type]] = {
    "albMatchRule": _OBJECT_MATCH_VALUE_ALL,
    "asMatchRule": _OBJECT_MATCH_VALUE_ALL,
    "apMatchRule": _OBJECT_MATCH_VALUE_SIMPLE_OBJECT,
    "cdMatchRule": _OBJECT_MATCH_VALUE_SIMPLE_OBJECT,
    "erMatchRule": _OBJECT_MATCH_VALUE_SIMPLE_OBJECT,
    "frMatchRule": _OBJECT_MATCH_VALUE_SIMPLE_OBJECT,
    "igMatchRule": _OBJECT_MATCH_VALUE_SIMPLE_OBJECT,
    "vpMatchRule": _OBJECT_MATCH_VALUE_SIMPLE_OBJECT,
}


def _get_object_match_value_type(raw: Any) -> str:
    """Extract the ``type`` string from an ObjectMatchValue dict.

    Mirrors Go ``getObjectMatchValueType``.
    """
    if isinstance(raw, dict):
        val = raw.get("type")
        if isinstance(val, str):
            return val
    return ""


def _convert_object_match_value(raw: Any, handler: type) -> Any:
    """Convert a raw dict into the appropriate ObjectMatchValue dataclass.

    Mirrors Go ``convertObjectMatchValue``.
    """
    if isinstance(raw, dict):
        return handler.from_dict(raw)
    return raw


def _unmarshal_match_criteria(
    criteria_list: list | None,
    rule_type: str,
) -> list[MatchCriteria]:
    """Deserialize a list of match criteria dicts, resolving ObjectMatchValue.

    For each criterion that has an ``objectMatchValue`` entry, the value is
    dispatched to the correct ObjectMatchValue dataclass based on its
    ``type`` field and the owning rule type.
    """
    if not criteria_list:
        return []

    handlers = _OBJECT_MATCH_VALUE_MAP.get(rule_type, _OBJECT_MATCH_VALUE_SIMPLE_OBJECT)
    result: list[MatchCriteria] = []
    for item in criteria_list:
        mc = MatchCriteria.from_dict(item) if isinstance(item, dict) else item
        if isinstance(item, dict):
            omv_raw = item.get("objectMatchValue")
            if omv_raw is not None and isinstance(omv_raw, dict):
                omv_type = _get_object_match_value_type(omv_raw)
                handler = handlers.get(omv_type)
                if handler is not None:
                    mc.object_match_value = _convert_object_match_value(omv_raw, handler)
                else:
                    mc.object_match_value = omv_raw
        result.append(mc)
    return result


def unmarshal_match_rule(data: dict) -> Any:
    """Deserialize a single match-rule dict into the correct dataclass.

    Dispatches on the ``type`` field of *data*, mirroring Go
    ``unmarshalRule`` / ``policyMatchRule.UnmarshalJSON``.

    Args:
        data: A dict with at least a ``"type"`` key indicating the rule kind.

    Returns:
        An instance of the appropriate ``MatchRule*`` dataclass, or
        *data* unchanged if the type is unrecognised.
    """
    rule_type = data.get("type")
    if rule_type is None:
        raise ValueError("missing 'type' field in match rule data")
    handler_cls = _MATCH_RULE_HANDLERS.get(rule_type)
    if handler_cls is None:
        raise ValueError(f"unknown match rule type: {rule_type!r}")

    rule = handler_cls.from_dict(data)

    # Resolve polymorphic ObjectMatchValue within each match criterion.
    matches_raw = data.get("matches")
    if matches_raw:
        rule.matches = _unmarshal_match_criteria(matches_raw, rule_type)

    return rule


def unmarshal_match_rules(data: list) -> list:
    """Deserialize a list of match-rule dicts into typed dataclass instances.

    Mirrors Go ``MatchRules.UnmarshalJSON``.

    Args:
        data: A JSON-decoded list of rule dicts.

    Returns:
        A list of ``MatchRule*`` dataclass instances.
    """
    if not data:
        return []
    return [unmarshal_match_rule(item) if isinstance(item, dict) else item
            for item in data]


def normalize_policy_activation_network(value: str) -> str:
    """Normalize a network identifier to its canonical form.

    Mirrors Go ``PolicyActivationNetwork.UnmarshalJSON`` which maps
    STAGING/staging → ``"staging"`` and PRODUCTION/production/prod → ``"prod"``.

    Args:
        value: Raw network string (case-insensitive variants accepted).

    Returns:
        Canonical network string (``"staging"`` or ``"prod"``), or the
        original value if it does not match a known alias.
    """
    _mapping: dict[str, str] = {
        "STAGING": "staging",
        "staging": "staging",
        "PRODUCTION": "prod",
        "production": "prod",
        "prod": "prod",
    }
    return _mapping.get(value, value)
