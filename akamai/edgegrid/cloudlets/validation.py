# pylint: disable=too-many-lines
"""Request validation functions for the Cloudlets API client.

Mirrors every ``Validate()`` method in the Go ``pkg/cloudlets`` package.
Validation is performed before HTTP requests are made.  Each function
returns ``None`` when the request is valid, or a formatted error string
describing every violated constraint.
"""

from __future__ import annotations

import re
from datetime import datetime

from akamai.edgegrid.validation import parse_validation_errors
from akamai.edgegrid.cloudlets import models

# ---------------------------------------------------------------------------
# Module-level compiled regex patterns (mirrors Go regexp.MustCompile)
# ---------------------------------------------------------------------------

_NAME_REGEXP = re.compile(r'^[a-z_A-Z0-9]+$')
_PROPERTY_NAME_REGEXP = re.compile(r'^[a-z_A-Z0-9.\-]+$')


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _filter_errors(errors: dict[str, str | None]) -> str | None:
    """Remove ``None`` values and format remaining errors.

    This mirrors Go's ``validation.Errors{...}.Filter()`` pattern which
    discards nil error entries and returns the first collected error set.
    We reuse ``parse_validation_errors`` for consistent formatting.
    """
    filtered = {k: v for k, v in errors.items() if v is not None}
    if not filtered:
        return None
    return parse_validation_errors(filtered)


def _validate_required(value) -> str | None:
    """Return an error when *value* is empty / zero-valued."""
    if value is None:
        return "cannot be blank"
    if isinstance(value, str) and value == "":
        return "cannot be blank"
    if isinstance(value, (int, float)) and value == 0:
        return "cannot be blank"
    return None


def _validate_required_strict(value) -> str | None:
    """Return an error for required fields.

    Unlike ``_validate_required`` this treats ``0`` as valid (used when
    min-value validations follow separately).
    """
    if value is None:
        return "cannot be blank"
    if isinstance(value, str) and value == "":
        return "cannot be blank"
    return None


def _validate_length(value: str, min_len: int, max_len: int) -> str | None:
    """Validate string length is within [min_len, max_len]."""
    length = len(value) if value else 0
    if length < min_len or length > max_len:
        return f"the length must be between {min_len} and {max_len}"
    return None


def _validate_min(value, minimum) -> str | None:
    """Return an error when *value* < *minimum*."""
    if value is not None and value < minimum:
        return f"must be no less than {minimum}"
    return None


def _validate_max(value, maximum) -> str | None:
    """Return an error when *value* > *maximum*."""
    if value is not None and value > maximum:
        return f"must be no greater than {maximum}"
    return None


def _validate_rfc3339(value: str) -> str | None:
    """Validate that *value* is a valid RFC 3339 date string.

    Empty strings are accepted (mirrors Go where zero-value strings
    bypass ``is.UTCTime`` validation).
    """
    if not value:
        return None
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return None
    except (ValueError, AttributeError):
        return "must be a valid RFC3339 date"


def _generate_host_header_rules(
    additional_headers: dict | None,
) -> str | None:
    """Validate the ``host`` key in AdditionalHeaders.

    Mirrors Go ``generateHostHeaderRules``: performs a case-insensitive
    lookup for the ``"host"`` key and, when found, validates that the
    value length is between 1 and 256.
    """
    if not additional_headers:
        return None
    for key, value in additional_headers.items():
        if key.lower() == "host":
            if not value or len(value) < 1 or len(value) > 256:
                return "the length must be between 1 and 256"
    return None


# ---------------------------------------------------------------------------
# Origin validation (loadbalancer.go)
# ---------------------------------------------------------------------------


def validate_list_origins_request(req) -> str | None:
    """Validate ``ListOriginsRequest``.

    Mirrors Go ``ListOriginsRequest.Validate()`` using
    ``edgegriderr.ParseValidationErrors``.
    """
    errors: dict[str, str | None] = {}

    allowed_types = (
        "CUSTOMER", "APPLICATION_LOAD_BALANCER", "NETSTORAGE", "",
    )
    if req.type not in allowed_types:
        errors["Type"] = (
            f"value '{req.type}' is invalid. Must be one of: "
            "'CUSTOMER', 'APPLICATION_LOAD_BALANCER', "
            "'NETSTORAGE' or '' (empty)"
        )

    if not errors:
        return None
    return parse_validation_errors(errors)


def validate_create_origin_request(req) -> str | None:
    """Validate ``CreateOriginRequest``.

    Mirrors Go ``CreateOriginRequest.Validate()`` using
    ``edgegriderr.ParseValidationErrors``.
    """
    errors: dict[str, str | None] = {}

    origin_id_err = _validate_required_strict(req.origin_id)
    if origin_id_err is not None:
        errors["OriginID"] = origin_id_err
    else:
        length_err = _validate_length(req.origin_id, 2, 63)
        if length_err is not None:
            errors["OriginID"] = length_err

    desc_err = _validate_length(
        req.description if req.description else "", 0, 255,
    )
    if desc_err is not None:
        errors["Description"] = desc_err

    if not errors:
        return None
    return parse_validation_errors(errors)


def validate_update_origin_request(req) -> str | None:
    """Validate ``UpdateOriginRequest``.

    Mirrors Go ``UpdateOriginRequest.Validate()`` — same rules as create.
    """
    errors: dict[str, str | None] = {}

    origin_id_err = _validate_required_strict(req.origin_id)
    if origin_id_err is not None:
        errors["OriginID"] = origin_id_err
    else:
        length_err = _validate_length(req.origin_id, 2, 63)
        if length_err is not None:
            errors["OriginID"] = length_err

    desc_err = _validate_length(
        req.description if req.description else "", 0, 255,
    )
    if desc_err is not None:
        errors["Description"] = desc_err

    if not errors:
        return None
    return parse_validation_errors(errors)


# ---------------------------------------------------------------------------
# DataCenter / LivenessSettings / Warning / LoadBalancerVersion validation
# (loadbalancer_version.go)
# ---------------------------------------------------------------------------


def validate_data_center(dc) -> str | None:  # pylint: disable=too-many-branches
    """Validate ``DataCenter``.

    Mirrors Go ``DataCenter.Validate()`` using ``.Filter()``.
    """
    errors: dict[str, str | None] = {}

    continent_req = _validate_required_strict(dc.continent)
    if continent_req is not None:
        errors["Continent"] = continent_req
    else:
        allowed_continents = ("AF", "AS", "EU", "NA", "OC", "OT", "SA")
        if dc.continent not in allowed_continents:
            errors["Continent"] = (
                f"value '{dc.continent}' is invalid. Must be one of: "
                "'AF', 'AS', 'EU', 'NA', 'OC', 'OT', 'SA'"
            )

    country_req = _validate_required_strict(dc.country)
    if country_req is not None:
        errors["Country"] = country_req
    else:
        country_len = _validate_length(dc.country, 2, 2)
        if country_len is not None:
            errors["Country"] = country_len

    hostname_err = _validate_length(
        dc.hostname if dc.hostname else "", 0, 256,
    )
    if hostname_err is not None:
        errors["Hostname"] = hostname_err

    if dc.latitude is None:
        errors["Latitude"] = "cannot be blank"
    else:
        lat_err = _validate_min(dc.latitude, -180)
        if lat_err is None:
            lat_err = _validate_max(dc.latitude, 180)
        if lat_err is not None:
            errors["Latitude"] = lat_err

    if dc.longitude is None:
        errors["Longitude"] = "cannot be blank"
    else:
        lon_err = _validate_min(dc.longitude, -180)
        if lon_err is None:
            lon_err = _validate_max(dc.longitude, 180)
        if lon_err is not None:
            errors["Longitude"] = lon_err

    oid_req = _validate_required_strict(dc.origin_id)
    if oid_req is not None:
        errors["OriginID"] = oid_req
    else:
        oid_len = _validate_length(dc.origin_id, 1, 128)
        if oid_len is not None:
            errors["OriginID"] = oid_len

    if dc.percent is None:
        errors["Percent"] = "cannot be blank"
    else:
        pct_err = _validate_min(dc.percent, 0)
        if pct_err is None:
            pct_err = _validate_max(dc.percent, 100)
        if pct_err is not None:
            errors["Percent"] = pct_err

    return _filter_errors(errors)


def validate_liveness_settings(ls) -> str | None:  # pylint: disable=too-many-branches,too-many-statements
    """Validate ``LivenessSettings``.

    Mirrors Go ``LivenessSettings.Validate()`` using ``.Filter()``.
    """
    errors: dict[str, str | None] = {}

    if ls.host_header:
        hh_err = _validate_length(ls.host_header, 1, 256)
        if hh_err is not None:
            errors["HostHeader"] = hh_err

    ah_err = _generate_host_header_rules(ls.additional_headers)
    if ah_err is not None:
        errors["AdditionalHeaders"] = ah_err

    interval_err = _validate_min(ls.interval, 10)
    if interval_err is None:
        interval_err = _validate_max(ls.interval, 3600)
    if interval_err is not None:
        errors["Interval"] = interval_err

    protocol_upper = (ls.protocol or "").upper()
    if protocol_upper in ("HTTP", "HTTPS"):
        path_req = _validate_required_strict(ls.path)
        if path_req is not None:
            errors["Path"] = path_req
        else:
            path_len = _validate_length(ls.path, 1, 256)
            if path_len is not None:
                errors["Path"] = path_len

    port_req = _validate_required(ls.port)
    if port_req is not None:
        errors["Port"] = port_req
    else:
        port_err = _validate_min(ls.port, 1)
        if port_err is None:
            port_err = _validate_max(ls.port, 65535)
        if port_err is not None:
            errors["Port"] = port_err

    proto_req = _validate_required_strict(ls.protocol)
    if proto_req is not None:
        errors["Protocol"] = proto_req
    else:
        allowed_protocols = ("HTTP", "HTTPS", "TCP", "TCPS")
        if ls.protocol not in allowed_protocols:
            errors["Protocol"] = (
                f"value '{ls.protocol}' is invalid. Must be one of: "
                "'HTTP', 'HTTPS', 'TCP', 'TCPS'"
            )

    if protocol_upper in ("TCP", "TCPS"):
        rs_req = _validate_required_strict(ls.request_string)
        if rs_req is not None:
            errors["RequestString"] = rs_req

    if protocol_upper in ("TCP", "TCPS"):
        resp_req = _validate_required_strict(ls.response_string)
        if resp_req is not None:
            errors["ResponseString"] = resp_req

    if ls.timeout is not None:
        timeout_err = _validate_min(ls.timeout, 0.001)
        if timeout_err is None:
            timeout_err = _validate_max(ls.timeout, 60.0)
        if timeout_err is not None:
            errors["Timeout"] = timeout_err

    return _filter_errors(errors)


def validate_warning(warning) -> str | None:
    """Validate ``Warning``.

    Mirrors Go ``Warning.Validate()``.
    """
    errors: dict[str, str | None] = {}

    detail_req = _validate_required_strict(warning.detail)
    if detail_req is not None:
        errors["Detail"] = detail_req

    jp_err = _validate_length(
        warning.json_pointer if warning.json_pointer else "", 0, 128,
    )
    if jp_err is not None:
        errors["JSONPointer"] = jp_err

    title_req = _validate_required_strict(warning.title)
    if title_req is not None:
        errors["Title"] = title_req

    type_req = _validate_required_strict(warning.type)
    if type_req is not None:
        errors["Type"] = type_req

    return _filter_errors(errors)


def validate_load_balancer_version(version) -> str | None:  # pylint: disable=too-many-branches
    """Validate ``LoadBalancerVersion``.

    Mirrors Go ``LoadBalancerVersion.Validate()`` using ``.Filter()``.
    """
    errors: dict[str, str | None] = {}

    if version.balancing_type:
        allowed_bt = ("WEIGHTED", "PERFORMANCE")
        if version.balancing_type not in allowed_bt:
            errors["BalancingType"] = (
                f"value '{version.balancing_type}' is invalid. "
                "Must be one of: 'WEIGHTED', 'PERFORMANCE' or '' (empty)"
            )

    cd_err = _validate_rfc3339(
        version.created_date if version.created_date else "",
    )
    if cd_err is not None:
        errors["CreatedDate"] = cd_err

    dcs = version.data_centers if version.data_centers else []
    if len(dcs) < 1 or len(dcs) > 199:
        errors["DataCenters"] = "the length must be between 1 and 199"
    else:
        for dc in dcs:
            dc_err = validate_data_center(dc)
            if dc_err is not None:
                errors["DataCenters"] = dc_err
                break

    lmd_err = _validate_rfc3339(
        version.last_modified_date if version.last_modified_date else "",
    )
    if lmd_err is not None:
        errors["LastModifiedDate"] = lmd_err

    if version.liveness_settings is not None:
        ls_err = validate_liveness_settings(version.liveness_settings)
        if ls_err is not None:
            errors["LivenessSettings"] = ls_err

    if version.origin_id:
        oid_err = _validate_length(version.origin_id, 2, 62)
        if oid_err is not None:
            errors["OriginID"] = oid_err

    ver_min = _validate_min(version.version, 0)
    if ver_min is not None:
        errors["Version"] = ver_min

    warnings_list = version.warnings if version.warnings else []
    for w in warnings_list:
        w_err = validate_warning(w)
        if w_err is not None:
            errors["Warnings"] = w_err
            break

    return _filter_errors(errors)


def validate_create_load_balancer_version_request(req) -> str | None:
    """Validate ``CreateLoadBalancerVersionRequest``.

    Mirrors Go using ``edgegriderr.ParseValidationErrors``.
    """
    errors: dict[str, str | None] = {}

    if req.origin_id:
        oid_err = _validate_length(req.origin_id, 2, 62)
        if oid_err is not None:
            errors["OriginID"] = oid_err

    if req.load_balancer_version is not None:
        lbv_err = validate_load_balancer_version(req.load_balancer_version)
        if lbv_err is not None:
            errors["LoadBalancerVersion"] = lbv_err

    if not errors:
        return None
    return parse_validation_errors(errors)


def validate_get_load_balancer_version_request(req) -> str | None:
    """Validate ``GetLoadBalancerVersionRequest``.

    Mirrors Go using ``edgegriderr.ParseValidationErrors``.
    """
    errors: dict[str, str | None] = {}

    if req.origin_id:
        oid_err = _validate_length(req.origin_id, 2, 62)
        if oid_err is not None:
            errors["OriginID"] = oid_err

    ver_min = _validate_min(req.version, 0)
    if ver_min is not None:
        errors["Version"] = ver_min

    if not errors:
        return None
    return parse_validation_errors(errors)


def validate_update_load_balancer_version_request(req) -> str | None:
    """Validate ``UpdateLoadBalancerVersionRequest``.

    Mirrors Go using ``edgegriderr.ParseValidationErrors``.
    """
    errors: dict[str, str | None] = {}

    if req.origin_id:
        oid_err = _validate_length(req.origin_id, 2, 62)
        if oid_err is not None:
            errors["OriginID"] = oid_err

    ver_min = _validate_min(req.version, 0)
    if ver_min is not None:
        errors["Version"] = ver_min

    if req.load_balancer_version is not None:
        lbv_err = validate_load_balancer_version(req.load_balancer_version)
        if lbv_err is not None:
            errors["LoadBalancerVersion"] = lbv_err

    if not errors:
        return None
    return parse_validation_errors(errors)


def validate_list_load_balancer_versions_request(req) -> str | None:
    """Validate ``ListLoadBalancerVersionsRequest``.

    Mirrors Go using ``edgegriderr.ParseValidationErrors``.
    """
    errors: dict[str, str | None] = {}

    oid_req = _validate_required_strict(req.origin_id)
    if oid_req is not None:
        errors["OriginID"] = oid_req
    else:
        oid_len = _validate_length(req.origin_id, 2, 62)
        if oid_len is not None:
            errors["OriginID"] = oid_len

    if not errors:
        return None
    return parse_validation_errors(errors)


# ---------------------------------------------------------------------------
# Load balancer activation validation (loadbalancer_activation.go)
# ---------------------------------------------------------------------------


def validate_activate_load_balancer_version_request(req) -> str | None:
    """Validate ``ActivateLoadBalancerVersionRequest``.

    Mirrors Go using ``edgegriderr.ParseValidationErrors``.
    """
    errors: dict[str, str | None] = {}

    oid_req = _validate_required_strict(req.origin_id)
    if oid_req is not None:
        errors["OriginID"] = oid_req

    if req.load_balancer_version_activation is not None:
        act_err = validate_load_balancer_version_activation(
            req.load_balancer_version_activation,
        )
        if act_err is not None:
            errors["LoadBalancerVersionActivation"] = act_err

    if not errors:
        return None
    return parse_validation_errors(errors)


def validate_list_load_balancer_activations_request(req) -> str | None:
    """Validate ``ListLoadBalancerActivationsRequest``.

    Mirrors Go using ``edgegriderr.ParseValidationErrors``.
    """
    errors: dict[str, str | None] = {}

    oid_req = _validate_required_strict(req.origin_id)
    if oid_req is not None:
        errors["OriginID"] = oid_req

    if req.network:
        allowed_networks = ("staging", "prod")
        if req.network not in allowed_networks:
            errors["Network"] = (
                f"value '{req.network}' is invalid. Must be one of: "
                "'staging', 'prod' or '' (empty)"
            )

    if not errors:
        return None
    return parse_validation_errors(errors)


def validate_load_balancer_version_activation(act) -> str | None:
    """Validate ``LoadBalancerVersionActivation``.

    Mirrors Go using ``.Filter()``.
    """
    errors: dict[str, str | None] = {}

    net_req = _validate_required_strict(act.network)
    if net_req is not None:
        errors["Network"] = net_req
    else:
        allowed = ("STAGING", "PRODUCTION")
        if act.network not in allowed:
            errors["Network"] = (
                f"value '{act.network}' is invalid. Must be one of: "
                "'STAGING', 'PRODUCTION'"
            )

    ver_min = _validate_min(act.version, 0)
    if ver_min is not None:
        errors["Version"] = ver_min

    return _filter_errors(errors)


# ---------------------------------------------------------------------------
# Policy validation (policy.go)
# ---------------------------------------------------------------------------


def validate_create_policy_request(req) -> str | None:
    """Validate ``CreatePolicyRequest``.

    Mirrors Go ``CreatePolicyRequest.Validate()`` using ``.Filter()``.
    """
    errors: dict[str, str | None] = {}

    name_req = _validate_required_strict(req.name)
    if name_req is not None:
        errors["Name"] = name_req
    else:
        name_len = _validate_length(req.name, 0, 64)
        if name_len is not None:
            errors["Name"] = name_len
        elif not _NAME_REGEXP.match(req.name):
            errors["Name"] = "must be in a valid format"

    if req.property_name and not _PROPERTY_NAME_REGEXP.match(
        req.property_name,
    ):
        errors["PropertyName"] = "must be in a valid format"

    cid_err = _validate_min(req.cloudlet_id, 0)
    if cid_err is None:
        cid_err = _validate_max(req.cloudlet_id, 13)
    if cid_err is not None:
        errors["CloudletID"] = cid_err

    desc_err = _validate_length(
        req.description if req.description else "", 0, 255,
    )
    if desc_err is not None:
        errors["Description"] = desc_err

    return _filter_errors(errors)


def validate_update_policy_request(req) -> str | None:
    """Validate ``UpdatePolicyRequest``.

    Mirrors Go ``UpdatePolicyRequest.Validate()`` using ``.Filter()``.
    Name is NOT required (unlike create).
    """
    errors: dict[str, str | None] = {}

    if req.update_policy is not None:
        up = req.update_policy

        if up.name:
            name_len = _validate_length(up.name, 0, 64)
            if name_len is not None:
                errors["Name"] = name_len
            elif not _NAME_REGEXP.match(up.name):
                errors["Name"] = "must be in a valid format"

        desc_err = _validate_length(
            up.description if up.description else "", 0, 255,
        )
        if desc_err is not None:
            errors["Description"] = desc_err

        if up.property_name and not _PROPERTY_NAME_REGEXP.match(
            up.property_name,
        ):
            errors["PropertyName"] = "must be in a valid format"

    return _filter_errors(errors)


# ---------------------------------------------------------------------------
# Policy property validation (policy_property.go)
# ---------------------------------------------------------------------------


def validate_delete_policy_property_request(req) -> str | None:
    """Validate ``DeletePolicyPropertyRequest``.

    Mirrors Go using ``edgegriderr.ParseValidationErrors``.
    """
    errors: dict[str, str | None] = {}

    pid_req = _validate_required(req.policy_id)
    if pid_req is not None:
        errors["PolicyID"] = pid_req

    propid_req = _validate_required(req.property_id)
    if propid_req is not None:
        errors["PropertyID"] = propid_req

    if not errors:
        return None
    return parse_validation_errors(errors)


# ---------------------------------------------------------------------------
# Policy version validation (policy_version.go)
# ---------------------------------------------------------------------------


def validate_list_policy_versions_request(req) -> str | None:
    """Validate ``ListPolicyVersionsRequest``.

    Mirrors Go using ``edgegriderr.ParseValidationErrors``.
    """
    errors: dict[str, str | None] = {}

    pid_req = _validate_required(req.policy_id)
    if pid_req is not None:
        errors["PolicyID"] = pid_req

    offset_min = _validate_min(req.offset, 0)
    if offset_min is not None:
        errors["Offset"] = offset_min

    if not errors:
        return None
    return parse_validation_errors(errors)


def validate_create_policy_version_request(req) -> str | None:
    """Validate ``CreatePolicyVersionRequest``.

    Mirrors Go using ``edgegriderr.ParseValidationErrors``.
    """
    errors: dict[str, str | None] = {}

    if req.create_policy_version is not None:
        cpv = req.create_policy_version

        desc_err = _validate_length(
            cpv.description if cpv.description else "", 0, 255,
        )
        if desc_err is not None:
            errors["Description"] = desc_err

        if cpv.match_rule_format:
            if cpv.match_rule_format not in ("1.0",):
                errors["MatchRuleFormat"] = (
                    f"value '{cpv.match_rule_format}' is invalid. "
                    "Must be one of: '1.0' or '' (empty)"
                )

        rules = cpv.match_rules if cpv.match_rules else []
        if len(rules) > 5000:
            errors["MatchRules"] = (
                "the length must be between 0 and 5000"
            )

    if not errors:
        return None
    return parse_validation_errors(errors)


def validate_update_policy_version_request(req) -> str | None:
    """Validate ``UpdatePolicyVersionRequest``.

    Mirrors Go — same rules as create policy version.
    """
    errors: dict[str, str | None] = {}

    if req.update_policy_version is not None:
        upv = req.update_policy_version

        desc_err = _validate_length(
            upv.description if upv.description else "", 0, 255,
        )
        if desc_err is not None:
            errors["Description"] = desc_err

        if upv.match_rule_format:
            if upv.match_rule_format not in ("1.0",):
                errors["MatchRuleFormat"] = (
                    f"value '{upv.match_rule_format}' is invalid. "
                    "Must be one of: '1.0' or '' (empty)"
                )

        rules = upv.match_rules if upv.match_rules else []
        if len(rules) > 5000:
            errors["MatchRules"] = (
                "the length must be between 0 and 5000"
            )

    if not errors:
        return None
    return parse_validation_errors(errors)


# ---------------------------------------------------------------------------
# Policy version activation validation (policy_version_activation.go)
# ---------------------------------------------------------------------------


def validate_list_policy_activations_request(req) -> str | None:
    """Validate ``ListPolicyActivationsRequest``.

    Mirrors Go using ``edgegriderr.ParseValidationErrors``.
    """
    errors: dict[str, str | None] = {}

    pid_req = _validate_required(req.policy_id)
    if pid_req is not None:
        errors["PolicyID"] = pid_req

    if req.network:
        allowed_networks = ("staging", "prod")
        if req.network not in allowed_networks:
            errors["Network"] = (
                f"value '{req.network}' is invalid. Must be one of: "
                "'staging', 'prod' or '' (empty)"
            )

    if not errors:
        return None
    return parse_validation_errors(errors)


def validate_activate_policy_version_request(req) -> str | None:
    """Validate ``ActivatePolicyVersionRequest``.

    Mirrors Go using ``edgegriderr.ParseValidationErrors``.
    """
    errors: dict[str, str | None] = {}

    pid_req = _validate_required(req.policy_id)
    if pid_req is not None:
        errors["PolicyID"] = pid_req

    ver_req = _validate_required(req.version)
    if ver_req is not None:
        errors["Version"] = ver_req

    pva = req.policy_version_activation
    if pva is not None:
        if not pva.additional_property_names:
            errors["RequestBody.AdditionalPropertyNames"] = (
                "cannot be blank"
            )

        net_req = _validate_required_strict(pva.network)
        if net_req is not None:
            errors["RequestBody.Network"] = net_req
        else:
            allowed = ("staging", "prod")
            if pva.network not in allowed:
                errors["RequestBody.Network"] = (
                    f"value '{pva.network}' is invalid. Must be one of: "
                    "'staging', 'prod'"
                )

    if not errors:
        return None
    return parse_validation_errors(errors)


# ---------------------------------------------------------------------------
# Policy version rule validation (policy_version_rule.go)
# ---------------------------------------------------------------------------


def validate_get_policy_version_rule_request(req) -> str | None:
    """Validate ``GetPolicyVersionRuleRequest``.

    Mirrors Go using ``edgegriderr.ParseValidationErrors``.
    """
    errors: dict[str, str | None] = {}

    ver_req = _validate_required(req.version)
    if ver_req is not None:
        errors["Version"] = ver_req
    else:
        ver_min = _validate_min(req.version, 1)
        if ver_min is not None:
            errors["Version"] = ver_min

    aka_req = _validate_required_strict(req.aka_rule_id)
    if aka_req is not None:
        errors["AkaRuleID"] = aka_req

    pid_req = _validate_required(req.policy_id)
    if pid_req is not None:
        errors["PolicyID"] = pid_req

    if not errors:
        return None
    return parse_validation_errors(errors)


def validate_create_policy_version_rule_request(req) -> str | None:
    """Validate ``CreatePolicyVersionRuleRequest``.

    Mirrors Go using ``edgegriderr.ParseValidationErrors``.
    """
    errors: dict[str, str | None] = {}

    ver_req = _validate_required(req.version)
    if ver_req is not None:
        errors["Version"] = ver_req
    else:
        ver_min = _validate_min(req.version, 1)
        if ver_min is not None:
            errors["Version"] = ver_min

    pid_req = _validate_required(req.policy_id)
    if pid_req is not None:
        errors["PolicyID"] = pid_req

    idx_min = _validate_min(req.index, 0)
    if idx_min is not None:
        errors["Index"] = idx_min

    if not errors:
        return None
    return parse_validation_errors(errors)


def validate_update_policy_version_rule_request(req) -> str | None:
    """Validate ``UpdatePolicyVersionRuleRequest``.

    Mirrors Go using ``edgegriderr.ParseValidationErrors``.
    """
    errors: dict[str, str | None] = {}

    ver_req = _validate_required(req.version)
    if ver_req is not None:
        errors["Version"] = ver_req
    else:
        ver_min = _validate_min(req.version, 1)
        if ver_min is not None:
            errors["Version"] = ver_min

    aka_req = _validate_required_strict(req.aka_rule_id)
    if aka_req is not None:
        errors["AkaRuleID"] = aka_req

    pid_req = _validate_required(req.policy_id)
    if pid_req is not None:
        errors["PolicyID"] = pid_req

    if not errors:
        return None
    return parse_validation_errors(errors)


# ---------------------------------------------------------------------------
# MatchRules validation (match_rule.go)
# ---------------------------------------------------------------------------


def validate_match_rules(rules) -> str | None:
    """Validate ``MatchRules``.

    Mirrors Go ``MatchRules.Validate()`` using
    ``edgegriderr.ParseValidationErrors``.
    """
    errors: dict[str, str | None] = {}

    match_rules = rules if rules else []
    if len(match_rules) > 5000:
        errors["MatchRules"] = "the length must be between 0 and 5000"

    if not errors:
        return None
    return parse_validation_errors(errors)


# ---------------------------------------------------------------------------
# Internal helpers for match rule / match criteria validation
# ---------------------------------------------------------------------------


def _pass_through_percent_validation(value) -> str | None:
    """Validate ``PassThroughPercent``.

    Mirrors Go ``passThroughPercentValidation``.
    The value must not be None, min -1, max 100.
    """
    if value is None:
        return "cannot be blank"
    if not isinstance(value, (int, float)):
        return f"type {type(value).__name__} is invalid. Must be *float64"
    if value < -1:
        return "must be no less than -1"
    if value > 100:
        return "must be no greater than 100"
    return None


def _object_match_value_simple_or_object_validation(value) -> str | None:
    """Validate ObjectMatchValue is Simple or Object type.

    Mirrors Go ``objectMatchValueSimpleOrObjectValidation``.
    """
    if value is None:
        return None
    if isinstance(
        value,
        (models.ObjectMatchValueObject, models.ObjectMatchValueSimple),
    ):
        return None
    type_name = type(value).__name__
    return (
        f"type {type_name} is invalid. "
        "Must be one of: 'simple' or 'object'"
    )


def _object_match_value_simple_or_range_or_object_validation(
    value,
) -> str | None:
    """Validate ObjectMatchValue is Simple, Range, or Object type.

    Mirrors Go ``objectMatchValueSimpleOrRangeOrObjectValidation``.
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
    type_name = type(value).__name__
    return (
        f"type {type_name} is invalid. "
        "Must be one of: 'simple', 'range' or 'object'"
    )


def _validate_matches_always_mutual_exclusion(
    matches: list,
    matches_always: bool,
) -> str | None:
    """Validate Matches/MatchesAlways mutual exclusion.

    When ``matches_always`` is True, ``matches`` must be empty.
    """
    if matches_always and matches:
        return (
            'only one of [ "Matches", "MatchesAlways" ] can be specified'
        )
    return None


# ---------------------------------------------------------------------------
# Match rule type validators (match_rule.go — 8 variants)
# ---------------------------------------------------------------------------


def validate_match_rule_alb(rule) -> str | None:
    """Validate ``MatchRuleALB``.

    Mirrors Go ``MatchRuleALB.Validate()`` using ``.Filter()``.
    """
    errors: dict[str, str | None] = {}

    type_req = _validate_required_strict(rule.type)
    if type_req is not None:
        errors["Type"] = type_req
    elif rule.type != "albMatchRule":
        errors["Type"] = (
            f"value '{rule.type}' is invalid. "
            "Must be: 'albMatchRule'"
        )

    errors["Name"] = _validate_length(
        rule.name if rule.name else "", 0, 8192,
    )
    errors["Start"] = _validate_min(rule.start, 0)
    errors["End"] = _validate_min(rule.end, 0)
    errors["MatchURL"] = _validate_length(
        rule.match_url if rule.match_url else "", 0, 8192,
    )

    fs = rule.forward_settings
    if fs is None:
        errors["ForwardSettings.OriginID"] = "cannot be blank"
    else:
        fs_oid_req = _validate_required_strict(fs.origin_id)
        if fs_oid_req is not None:
            errors["ForwardSettings.OriginID"] = fs_oid_req
        else:
            errors["ForwardSettings.OriginID"] = _validate_length(
                fs.origin_id, 0, 8192,
            )

    matches = rule.matches if rule.matches else []
    for mc in matches:
        mc_err = validate_match_criteria_alb(mc)
        if mc_err is not None:
            errors["Matches"] = mc_err
            break

    return _filter_errors(errors)


def validate_match_rule_ap(rule) -> str | None:
    """Validate ``MatchRuleAP``.

    Mirrors Go ``MatchRuleAP.Validate()`` using ``.Filter()``.
    """
    errors: dict[str, str | None] = {}

    type_req = _validate_required_strict(rule.type)
    if type_req is not None:
        errors["Type"] = type_req
    elif rule.type != "apMatchRule":
        errors["Type"] = (
            f"value '{rule.type}' is invalid. "
            "Must be: 'apMatchRule'"
        )

    errors["Name"] = _validate_length(
        rule.name if rule.name else "", 0, 8192,
    )
    errors["Start"] = _validate_min(rule.start, 0)
    errors["End"] = _validate_min(rule.end, 0)
    errors["MatchURL"] = _validate_length(
        rule.match_url if rule.match_url else "", 0, 8192,
    )
    errors["PassThroughPercent"] = _pass_through_percent_validation(
        rule.pass_through_percent,
    )

    matches = rule.matches if rule.matches else []
    for mc in matches:
        mc_err = validate_match_criteria_ap(mc)
        if mc_err is not None:
            errors["Matches"] = mc_err
            break

    return _filter_errors(errors)


def validate_match_rule_as(rule) -> str | None:
    """Validate ``MatchRuleAS``.

    Mirrors Go ``MatchRuleAS.Validate()`` using ``.Filter()``.
    """
    errors: dict[str, str | None] = {}

    type_req = _validate_required_strict(rule.type)
    if type_req is not None:
        errors["Type"] = type_req
    elif rule.type != "asMatchRule":
        errors["Type"] = (
            f"value '{rule.type}' is invalid. "
            "Must be: 'asMatchRule'"
        )

    errors["Name"] = _validate_length(
        rule.name if rule.name else "", 0, 8192,
    )
    errors["Start"] = _validate_min(rule.start, 0)
    errors["End"] = _validate_min(rule.end, 0)
    errors["MatchURL"] = _validate_length(
        rule.match_url if rule.match_url else "", 0, 8192,
    )

    matches = rule.matches if rule.matches else []
    for mc in matches:
        mc_err = validate_match_criteria_as(mc)
        if mc_err is not None:
            errors["Matches"] = mc_err
            break

    if rule.forward_settings is None:
        errors["ForwardSettings"] = "cannot be blank"
    else:
        fs = rule.forward_settings
        if fs.path_and_qs:
            errors["ForwardSettings.PathAndQS"] = _validate_length(
                fs.path_and_qs, 1, 8192,
            )
        if fs.origin_id:
            errors["ForwardSettings.OriginID"] = _validate_length(
                fs.origin_id, 0, 8192,
            )

    return _filter_errors(errors)


def validate_match_rule_pr(rule) -> str | None:
    """Validate ``MatchRulePR``.

    Mirrors Go ``MatchRulePR.Validate()`` using ``.Filter()``.
    """
    errors: dict[str, str | None] = {}

    type_req = _validate_required_strict(rule.type)
    if type_req is not None:
        errors["Type"] = type_req
    elif rule.type != "cdMatchRule":
        errors["Type"] = (
            f"value '{rule.type}' is invalid. "
            "Must be: 'cdMatchRule'"
        )

    errors["Name"] = _validate_length(
        rule.name if rule.name else "", 0, 8192,
    )
    errors["Start"] = _validate_min(rule.start, 0)
    errors["End"] = _validate_min(rule.end, 0)
    errors["MatchURL"] = _validate_length(
        rule.match_url if rule.match_url else "", 0, 8192,
    )

    if rule.forward_settings is None:
        errors["ForwardSettings"] = "cannot be blank"
    else:
        fs = rule.forward_settings
        fs_oid_req = _validate_required_strict(fs.origin_id)
        if fs_oid_req is not None:
            errors["ForwardSettings.OriginID"] = fs_oid_req
        else:
            errors["ForwardSettings.OriginID"] = _validate_length(
                fs.origin_id, 0, 8192,
            )

        pct_req = _validate_required(fs.percent)
        if pct_req is not None:
            errors["ForwardSettings.Percent"] = pct_req
        else:
            pct_err = _validate_min(fs.percent, 1)
            if pct_err is None:
                pct_err = _validate_max(fs.percent, 100)
            if pct_err is not None:
                errors["ForwardSettings.Percent"] = pct_err

    matches = rule.matches if rule.matches else []
    for mc in matches:
        mc_err = validate_match_criteria_pr(mc)
        if mc_err is not None:
            errors["Matches"] = mc_err
            break

    errors["Matches/MatchesAlways"] = _validate_matches_always_mutual_exclusion(
        rule.matches if rule.matches else [],
        rule.matches_always,
    )

    return _filter_errors(errors)


def validate_match_rule_er(rule) -> str | None:
    """Validate ``MatchRuleER``.

    Mirrors Go ``MatchRuleER.Validate()`` using ``.Filter()``.
    """
    errors: dict[str, str | None] = {}

    type_req = _validate_required_strict(rule.type)
    if type_req is not None:
        errors["Type"] = type_req
    elif rule.type != "erMatchRule":
        errors["Type"] = (
            f"value '{rule.type}' is invalid. "
            "Must be: 'erMatchRule'"
        )

    errors["Name"] = _validate_length(
        rule.name if rule.name else "", 0, 8192,
    )
    errors["Start"] = _validate_min(rule.start, 0)
    errors["End"] = _validate_min(rule.end, 0)
    errors["MatchURL"] = _validate_length(
        rule.match_url if rule.match_url else "", 0, 8192,
    )

    rurl_req = _validate_required_strict(rule.redirect_url)
    if rurl_req is not None:
        errors["RedirectURL"] = rurl_req
    else:
        errors["RedirectURL"] = _validate_length(
            rule.redirect_url, 1, 8192,
        )

    if rule.use_relative_url:
        allowed = ("none", "copy_scheme_hostname", "relative_url")
        if rule.use_relative_url not in allowed:
            errors["UseRelativeURL"] = (
                f"value '{rule.use_relative_url}' is invalid. "
                "Must be one of: 'none', 'copy_scheme_hostname', "
                "'relative_url' or '' (empty)"
            )

    sc_req = _validate_required(rule.status_code)
    if sc_req is not None:
        errors["StatusCode"] = sc_req
    else:
        allowed_codes = (301, 302, 303, 307, 308)
        if rule.status_code not in allowed_codes:
            errors["StatusCode"] = (
                f"value '{rule.status_code}' is invalid. "
                "Must be one of: 301, 302, 303, 307 or 308"
            )

    matches = rule.matches if rule.matches else []
    for mc in matches:
        mc_err = validate_match_criteria_er(mc)
        if mc_err is not None:
            errors["Matches"] = mc_err
            break

    errors["Matches/MatchesAlways"] = _validate_matches_always_mutual_exclusion(
        rule.matches if rule.matches else [],
        rule.matches_always,
    )

    return _filter_errors(errors)


def validate_match_rule_fr(rule) -> str | None:
    """Validate ``MatchRuleFR``.

    Mirrors Go ``MatchRuleFR.Validate()`` using ``.Filter()``.
    """
    errors: dict[str, str | None] = {}

    type_req = _validate_required_strict(rule.type)
    if type_req is not None:
        errors["Type"] = type_req
    elif rule.type != "frMatchRule":
        errors["Type"] = (
            f"value '{rule.type}' is invalid. "
            "Must be: 'frMatchRule'"
        )

    errors["Name"] = _validate_length(
        rule.name if rule.name else "", 0, 8192,
    )
    errors["Start"] = _validate_min(rule.start, 0)
    errors["End"] = _validate_min(rule.end, 0)
    errors["MatchURL"] = _validate_length(
        rule.match_url if rule.match_url else "", 0, 8192,
    )

    matches = rule.matches if rule.matches else []
    for mc in matches:
        mc_err = validate_match_criteria_fr(mc)
        if mc_err is not None:
            errors["Matches"] = mc_err
            break

    if rule.forward_settings is None:
        errors["ForwardSettings"] = "cannot be blank"
    else:
        fs = rule.forward_settings
        if fs.path_and_qs:
            errors["ForwardSettings.PathAndQS"] = _validate_length(
                fs.path_and_qs, 1, 8192,
            )
        if fs.origin_id:
            errors["ForwardSettings.OriginID"] = _validate_length(
                fs.origin_id, 0, 8192,
            )

    return _filter_errors(errors)


def validate_match_rule_rc(rule) -> str | None:
    """Validate ``MatchRuleRC``.

    Mirrors Go ``MatchRuleRC.Validate()`` using ``.Filter()``.
    """
    errors: dict[str, str | None] = {}

    type_req = _validate_required_strict(rule.type)
    if type_req is not None:
        errors["Type"] = type_req
    elif rule.type != "igMatchRule":
        errors["Type"] = (
            f"value '{rule.type}' is invalid. "
            "Must be: 'igMatchRule'"
        )

    errors["Name"] = _validate_length(
        rule.name if rule.name else "", 0, 8192,
    )
    errors["Start"] = _validate_min(rule.start, 0)
    errors["End"] = _validate_min(rule.end, 0)

    matches = rule.matches if rule.matches else []
    for mc in matches:
        mc_err = validate_match_criteria_rc(mc)
        if mc_err is not None:
            errors["Matches"] = mc_err
            break

    errors["Matches/MatchesAlways"] = _validate_matches_always_mutual_exclusion(
        rule.matches if rule.matches else [],
        rule.matches_always,
    )

    ad_req = _validate_required_strict(rule.allow_deny)
    if ad_req is not None:
        errors["AllowDeny"] = ad_req
    else:
        allowed = ("allow", "deny", "denybranded")
        if rule.allow_deny not in allowed:
            errors["AllowDeny"] = (
                f"value '{rule.allow_deny}' is invalid. "
                "Must be one of: 'allow', 'deny' or 'denybranded'"
            )

    return _filter_errors(errors)


def validate_match_rule_vp(rule) -> str | None:
    """Validate ``MatchRuleVP``.

    Mirrors Go ``MatchRuleVP.Validate()`` using ``.Filter()``.
    """
    errors: dict[str, str | None] = {}

    type_req = _validate_required_strict(rule.type)
    if type_req is not None:
        errors["Type"] = type_req
    elif rule.type != "vpMatchRule":
        errors["Type"] = (
            f"value '{rule.type}' is invalid. "
            "Must be: 'vpMatchRule'"
        )

    errors["Name"] = _validate_length(
        rule.name if rule.name else "", 0, 8192,
    )
    errors["Start"] = _validate_min(rule.start, 0)
    errors["End"] = _validate_min(rule.end, 0)
    errors["MatchURL"] = _validate_length(
        rule.match_url if rule.match_url else "", 0, 8192,
    )
    errors["PassThroughPercent"] = _pass_through_percent_validation(
        rule.pass_through_percent,
    )

    matches = rule.matches if rule.matches else []
    for mc in matches:
        mc_err = validate_match_criteria_vp(mc)
        if mc_err is not None:
            errors["Matches"] = mc_err
            break

    return _filter_errors(errors)


# ---------------------------------------------------------------------------
# Match criteria validators (match_rule.go — 8 variants)
# ---------------------------------------------------------------------------

_MATCH_TYPES_ALB = (
    "clientip", "continent", "cookie", "countrycode",
    "deviceCharacteristics", "extension", "header", "hostname",
    "method", "path", "protocol", "proxy", "query", "regioncode",
    "range",
)

_MATCH_TYPES_AP = (
    "header", "hostname", "path", "extension", "query", "cookie",
    "deviceCharacteristics", "clientip", "continent", "countrycode",
    "regioncode", "protocol", "method", "proxy",
)

_MATCH_TYPES_AS = (
    "header", "hostname", "path", "extension", "query", "range",
    "regex", "cookie", "deviceCharacteristics", "clientip",
    "continent", "countrycode", "regioncode", "protocol", "method",
    "proxy",
)

_MATCH_TYPES_ER = (
    "header", "hostname", "path", "extension", "query", "regex",
    "cookie", "deviceCharacteristics", "clientip", "continent",
    "countrycode", "regioncode", "protocol", "method", "proxy",
)

_MATCH_OPERATORS = ("contains", "exists", "equals")

_CHECK_IPS = (
    "CONNECTING_IP", "XFF_HEADERS", "CONNECTING_IP XFF_HEADERS",
)


def _validate_match_criteria_common(  # pylint: disable=too-many-branches
    mc,
    allowed_match_types: tuple,
    match_type_error: str,
    match_type_required: bool,
    omv_validator,
) -> dict[str, str | None]:
    """Shared match-criteria validation logic.

    Returns a dict of field -> error pairs (values may be ``None``).
    """
    errors: dict[str, str | None] = {}

    # MatchType
    if match_type_required:
        mt_req = _validate_required_strict(mc.match_type)
        if mt_req is not None:
            errors["MatchType"] = mt_req
        elif mc.match_type not in allowed_match_types:
            errors["MatchType"] = match_type_error
    else:
        if mc.match_type and mc.match_type not in allowed_match_types:
            errors["MatchType"] = match_type_error

    # MatchValue / ObjectMatchValue cross-validation
    omv = mc.object_match_value
    mv = mc.match_value if mc.match_value else ""

    if omv is None:
        if not mv:
            errors["MatchValue"] = (
                "cannot be blank when ObjectMatchValue is blank"
            )
        else:
            mv_len = _validate_length(mv, 1, 8192)
            if mv_len is not None:
                errors["MatchValue"] = mv_len
    else:
        if mv:
            errors["MatchValue"] = (
                "must be blank when ObjectMatchValue is set"
            )

    if mv:
        if omv is not None:
            errors["ObjectMatchValue"] = (
                "must be blank when MatchValue is set"
            )
    else:
        if omv is None:
            errors["ObjectMatchValue"] = (
                "cannot be blank when MatchValue is blank"
            )
        else:
            omv_err = omv_validator(omv)
            if omv_err is not None:
                errors["ObjectMatchValue"] = omv_err

    # MatchOperator
    if mc.match_operator:
        if mc.match_operator not in _MATCH_OPERATORS:
            errors["MatchOperator"] = (
                f"value '{mc.match_operator}' is invalid. "
                "Must be one of: 'contains', 'exists', "
                "'equals' or '' (empty)"
            )

    # CheckIPs
    if mc.check_ips:
        if mc.check_ips not in _CHECK_IPS:
            errors["CheckIPs"] = (
                f"value '{mc.check_ips}' is invalid. "
                "Must be one of: 'CONNECTING_IP', 'XFF_HEADERS', "
                "'CONNECTING_IP XFF_HEADERS' or '' (empty)"
            )

    return errors


def _fmt_mt_err_alb(match_type: str) -> str:
    return (
        f"value '{match_type}' is invalid. Must be one of: "
        "'clientip', 'continent', 'cookie', 'countrycode', "
        "'deviceCharacteristics', 'extension', 'header', "
        "'hostname', 'method', 'path', 'protocol', 'proxy', "
        "'query', 'regioncode', 'range' or '' (empty)"
    )


def _fmt_mt_err_ap(match_type: str) -> str:
    return (
        f"value '{match_type}' is invalid. Must be one of: "
        "'header', 'hostname', 'path', 'extension', 'query', "
        "'cookie', 'deviceCharacteristics', 'clientip', "
        "'continent', 'countrycode', 'regioncode', 'protocol', "
        "'method', 'proxy'"
    )


def _fmt_mt_err_as(match_type: str) -> str:
    return (
        f"value '{match_type}' is invalid. Must be one of: "
        "'header', 'hostname', 'path', 'extension', 'query', "
        "'range', 'regex', 'cookie', 'deviceCharacteristics', "
        "'clientip', 'continent', 'countrycode', 'regioncode', "
        "'protocol', 'method', 'proxy'"
    )


def _fmt_mt_err_er(match_type: str) -> str:
    return (
        f"value '{match_type}' is invalid. Must be one of: "
        "'header', 'hostname', 'path', 'extension', 'query', "
        "'regex', 'cookie', 'deviceCharacteristics', 'clientip', "
        "'continent', 'countrycode', 'regioncode', 'protocol', "
        "'method', 'proxy' or '' (empty)"
    )


def _fmt_mt_err_fr(match_type: str) -> str:
    return (
        f"value '{match_type}' is invalid. Must be one of: "
        "'header', 'hostname', 'path', 'extension', 'query', "
        "'regex', 'cookie', 'deviceCharacteristics', 'clientip', "
        "'continent', 'countrycode', 'regioncode', 'protocol', "
        "'method', 'proxy'"
    )


def _fmt_mt_err_rc(match_type: str) -> str:
    return (
        f"value '{match_type}' is invalid. Must be one of: "
        "'header', 'hostname', 'path', 'extension', 'query', "
        "'cookie', 'deviceCharacteristics', 'clientip', "
        "'continent', 'countrycode', 'regioncode', 'protocol', "
        "'method', 'proxy'"
    )


def _fmt_mt_err_vp(match_type: str) -> str:
    return (
        f"value '{match_type}' is invalid. Must be one of: "
        "'header', 'hostname', 'path', 'extension', 'query', "
        "'cookie', 'deviceCharacteristics', 'clientip', "
        "'continent', 'countrycode', 'regioncode', 'protocol', "
        "'method', 'proxy'"
    )


def validate_match_criteria_alb(mc) -> str | None:
    """Validate ``MatchCriteriaALB``.

    Mirrors Go ``MatchCriteriaALB.Validate()`` using ``.Filter()``.
    """
    errors = _validate_match_criteria_common(
        mc,
        allowed_match_types=_MATCH_TYPES_ALB,
        match_type_error=_fmt_mt_err_alb(mc.match_type),
        match_type_required=False,
        omv_validator=(
            _object_match_value_simple_or_range_or_object_validation
        ),
    )
    return _filter_errors(errors)


def validate_match_criteria_ap(mc) -> str | None:
    """Validate ``MatchCriteriaAP``.

    Mirrors Go ``MatchCriteriaAP.Validate()`` using ``.Filter()``.
    """
    errors = _validate_match_criteria_common(
        mc,
        allowed_match_types=_MATCH_TYPES_AP,
        match_type_error=_fmt_mt_err_ap(mc.match_type),
        match_type_required=False,
        omv_validator=_object_match_value_simple_or_object_validation,
    )
    return _filter_errors(errors)


def validate_match_criteria_as(mc) -> str | None:
    """Validate ``MatchCriteriaAS``.

    Mirrors Go ``MatchCriteriaAS.Validate()`` using ``.Filter()``.
    """
    errors = _validate_match_criteria_common(
        mc,
        allowed_match_types=_MATCH_TYPES_AS,
        match_type_error=_fmt_mt_err_as(mc.match_type),
        match_type_required=False,
        omv_validator=(
            _object_match_value_simple_or_range_or_object_validation
        ),
    )
    return _filter_errors(errors)


def validate_match_criteria_pr(mc) -> str | None:
    """Validate ``MatchCriteriaPR``.

    Mirrors Go ``MatchCriteriaPR.Validate()`` using ``.Filter()``.
    """
    errors = _validate_match_criteria_common(
        mc,
        allowed_match_types=_MATCH_TYPES_AP,
        match_type_error=_fmt_mt_err_ap(mc.match_type),
        match_type_required=False,
        omv_validator=_object_match_value_simple_or_object_validation,
    )
    return _filter_errors(errors)


def validate_match_criteria_er(mc) -> str | None:
    """Validate ``MatchCriteriaER``.

    Mirrors Go ``MatchCriteriaER.Validate()`` using ``.Filter()``.
    Includes special case: ObjectMatchValue not supported with
    MatchType ``'query'``.
    """
    errors = _validate_match_criteria_common(
        mc,
        allowed_match_types=_MATCH_TYPES_ER,
        match_type_error=_fmt_mt_err_er(mc.match_type),
        match_type_required=False,
        omv_validator=_object_match_value_simple_or_object_validation,
    )

    # ER special case (Go lines 602-604)
    if mc.match_type == "query" and mc.object_match_value is not None:
        errors["ObjectMatchValue"] = (
            "ObjectMatchValue not supported with MatchType 'query'"
        )

    return _filter_errors(errors)


def validate_match_criteria_fr(mc) -> str | None:
    """Validate ``MatchCriteriaFR``.

    Mirrors Go ``MatchCriteriaFR.Validate()`` using ``.Filter()``.
    MatchType is **required**.
    """
    errors = _validate_match_criteria_common(
        mc,
        allowed_match_types=_MATCH_TYPES_ER,
        match_type_error=_fmt_mt_err_fr(mc.match_type),
        match_type_required=True,
        omv_validator=_object_match_value_simple_or_object_validation,
    )
    return _filter_errors(errors)


def validate_match_criteria_rc(mc) -> str | None:
    """Validate ``MatchCriteriaRC``.

    Mirrors Go ``MatchCriteriaRC.Validate()`` using ``.Filter()``.
    MatchType is **required**.
    """
    errors = _validate_match_criteria_common(
        mc,
        allowed_match_types=_MATCH_TYPES_AP,
        match_type_error=_fmt_mt_err_rc(mc.match_type),
        match_type_required=True,
        omv_validator=_object_match_value_simple_or_object_validation,
    )
    return _filter_errors(errors)


def validate_match_criteria_vp(mc) -> str | None:
    """Validate ``MatchCriteriaVP``.

    Mirrors Go ``MatchCriteriaVP.Validate()`` using ``.Filter()``.
    """
    errors = _validate_match_criteria_common(
        mc,
        allowed_match_types=_MATCH_TYPES_AP,
        match_type_error=_fmt_mt_err_vp(mc.match_type),
        match_type_required=False,
        omv_validator=_object_match_value_simple_or_object_validation,
    )
    return _filter_errors(errors)


# ---------------------------------------------------------------------------
# ObjectMatchValue validators (match_rule.go)
# ---------------------------------------------------------------------------


def validate_object_match_value_range(omv) -> str | None:
    """Validate ``ObjectMatchValueRange``.

    Mirrors Go ``ObjectMatchValueRange.Validate()`` using ``.Filter()``.
    """
    errors: dict[str, str | None] = {}

    if omv.type != "range":
        errors["Type"] = (
            f"value '{omv.type}' is invalid. Must be: 'range'"
        )

    return _filter_errors(errors)


def validate_object_match_value_simple(omv) -> str | None:
    """Validate ``ObjectMatchValueSimple``.

    Mirrors Go ``ObjectMatchValueSimple.Validate()`` using ``.Filter()``.
    """
    errors: dict[str, str | None] = {}

    if omv.type != "simple":
        errors["Type"] = (
            f"value '{omv.type}' is invalid. Must be: 'simple'"
        )

    return _filter_errors(errors)


def validate_object_match_value_object(omv) -> str | None:
    """Validate ``ObjectMatchValueObject``.

    Mirrors Go ``ObjectMatchValueObject.Validate()`` using ``.Filter()``.
    """
    errors: dict[str, str | None] = {}

    name_req = _validate_required_strict(omv.name)
    if name_req is not None:
        errors["Name"] = name_req
    else:
        name_len = _validate_length(omv.name, 0, 8192)
        if name_len is not None:
            errors["Name"] = name_len

    type_req = _validate_required_strict(omv.type)
    if type_req is not None:
        errors["Type"] = type_req
    elif omv.type != "object":
        errors["Type"] = (
            f"value '{omv.type}' is invalid. Must be: 'object'"
        )

    return _filter_errors(errors)
