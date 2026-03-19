# pylint: disable=too-many-lines,too-many-public-methods
"""Edge DNS API client providing access to Akamai DNS V2 APIs.

Provides the ``Client`` class that mirrors the Go ``pkg/dns.DNS`` interface.
Each public method corresponds 1:1 with a Go interface method, preserving
URL paths, HTTP methods, expected status codes, concurrency locking, and
error-wrapping semantics.

See: https://techdocs.akamai.com/edge-dns/reference/edge-dns-api
"""

from __future__ import annotations

import ipaddress
import logging
import re
import threading
from dataclasses import fields, is_dataclass
from typing import Any, get_args, get_origin, get_type_hints
from urllib.parse import quote

from akamai.edgegrid.session import Session
from akamai.edgegrid.dns import models
from akamai.edgegrid.dns import errors as dns_errors
from akamai.edgegrid.dns import validation

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level write locks — mirror Go sync.Mutex variables
# ---------------------------------------------------------------------------

_zone_record_write_lock = threading.Lock()
_zone_record_sets_write_lock = threading.Lock()
_zone_write_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Go ZoneCreate struct field → JSON key map (mirrors Go zoneStructMap)
# ---------------------------------------------------------------------------

_ZONE_STRUCT_MAP: dict[str, str] = {
    "zone": "zone",
    "type": "type",
    "masters": "masters",
    "comment": "comment",
    "sign_and_serve": "signAndServe",
    "sign_and_serve_algorithm": "signAndServeAlgorithm",
    "tsig_key": "tsigKey",
    "target": "target",
    "end_customer_id": "endCustomerId",
    "outbound_zone_transfer": "outboundZoneTransfer",
    "contract_id": "contractId",
}

# Per-field zone-type gate used by ``_filter_zone_field``.
_ZONE_FIELD_TYPE_GATE: dict[str, str] = {
    "target": "ALIAS",
    "masters": "SECONDARY",
    "tsig_key": "SECONDARY",
}

# First regex: insert underscore between a lowercase/digit and an uppercase letter
_CAMEL_RE1 = re.compile(r"(.)([A-Z][a-z]+)")
# Second regex: insert underscore between a lowercase letter and an uppercase letter
_CAMEL_RE2 = re.compile(r"([a-z0-9])([A-Z])")

# NoneType is used when filtering ``T | None`` unions in _unwrap_optional.
_NONE_TYPE = type(None)  # pylint: disable=invalid-name


# ---------------------------------------------------------------------------
# camelCase / snake_case conversion helpers
# ---------------------------------------------------------------------------


def _camel_to_snake(name: str) -> str:
    """Convert a camelCase or PascalCase name to snake_case.

    Special cases handled:
    - ``recordsets`` → ``record_sets`` (all-lowercase compound word)
    - ``ACL`` → ``acl``
    """
    if name == "recordsets":
        return "record_sets"
    result = _CAMEL_RE1.sub(r"\1_\2", name)
    result = _CAMEL_RE2.sub(r"\1_\2", result)
    return result.lower()


def _snake_to_camel(name: str) -> str:
    """Convert a snake_case name to camelCase.

    Special cases handled:
    - ``record_sets`` → ``recordsets`` (API uses all-lowercase)
    - ``record_type`` → ``type`` (RecordBody JSON tag is ``"type"``)
    - ``acl`` → ``ACL``
    """
    if name == "record_sets":
        return "recordsets"
    if name == "record_type":
        return "type"
    if name == "acl":
        return "ACL"
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


# ---------------------------------------------------------------------------
# Generic dataclass → dict and dict → dataclass helpers
# ---------------------------------------------------------------------------


def _is_dataclass_type(tp: type) -> bool:
    """Return True if *tp* is a dataclass type (not an instance)."""
    try:
        return is_dataclass(tp) and isinstance(tp, type)
    except TypeError:
        return False


def _unwrap_optional(tp: type) -> type:
    """Extract T from ``T | None`` or ``Optional[T]`` unions.

    Returns the original type when it is not an optional union.
    """
    origin = get_origin(tp)
    if origin is not None:
        # Python 3.10 ``X | Y`` creates ``types.UnionType``
        import types as _types  # pylint: disable=import-outside-toplevel
        if origin is _types.UnionType or str(origin) == "typing.Union":
            args = get_args(tp)
            non_none = [a for a in args if a is not _NONE_TYPE]
            if len(non_none) == 1:
                return non_none[0]
    return tp


def _resolve_field_key(
    key: str, field_names: set[str],
) -> str | None:
    """Map a JSON key to the corresponding dataclass field name.

    Returns ``None`` when the key does not correspond to any field.
    """
    snake_key = _camel_to_snake(key)

    # JSON "type" → "record_type" alias (RecordBody / GetRecordResponse)
    if snake_key == "type" and "type" not in field_names:
        if "record_type" in field_names:
            return "record_type"
    # JSON "rdata" → "target" for RecordBody
    if key == "rdata" and "rdata" not in field_names:
        if "target" in field_names:
            return "target"

    if snake_key in field_names:
        return snake_key
    return None


def _coerce_value(
    field_type: type, value: Any,
) -> Any:
    """Coerce *value* according to *field_type*, recursing into dataclasses."""
    real_type = _unwrap_optional(field_type)

    if _is_dataclass_type(real_type) and isinstance(value, dict):
        return _build_response(real_type, value)

    if get_origin(real_type) is list and isinstance(value, list):
        list_args = get_args(real_type)
        if list_args and _is_dataclass_type(list_args[0]):
            return [
                _build_response(list_args[0], item)
                if isinstance(item, dict) else item
                for item in value
            ]
        return value

    return value


def _build_response(cls: type, data: Any) -> Any:
    """Recursively convert a JSON-parsed *data* dict into a dataclass of type *cls*.

    - camelCase JSON keys are translated to snake_case attribute names.
    - Nested dicts are converted to nested dataclass instances.
    - Lists of dicts are converted to lists of dataclass instances.
    - The JSON key ``"type"`` is mapped to ``"record_type"`` when the target
      dataclass has a ``record_type`` field but no ``type`` field.
    """
    if data is None:
        return cls()
    if not isinstance(data, dict):
        return data

    hints = get_type_hints(cls)
    field_names = {f.name for f in fields(cls)}
    kwargs: dict[str, Any] = {}

    for key, value in data.items():
        snake_key = _resolve_field_key(key, field_names)
        if snake_key is None:
            continue

        field_type = hints.get(snake_key)
        if field_type is None:
            kwargs[snake_key] = value
        else:
            kwargs[snake_key] = _coerce_value(field_type, value)

    return cls(**kwargs)


def _convert_struct_to_dict(obj: Any, *, omit_none: bool = True) -> dict[str, Any]:
    """Convert a dataclass instance to a camelCase JSON-serializable dict.

    - snake_case attribute names are converted to camelCase.
    - Nested dataclass instances are recursively converted.
    - ``None`` values are omitted when *omit_none* is True.
    """
    if not is_dataclass(obj):
        return obj  # type: ignore[return-value]

    result: dict[str, Any] = {}
    for fld in fields(obj):
        value = getattr(obj, fld.name)
        if omit_none and value is None:
            continue
        camel_key = _snake_to_camel(fld.name)
        if is_dataclass(value) and not isinstance(value, type):
            result[camel_key] = _convert_struct_to_dict(value, omit_none=omit_none)
        elif isinstance(value, list):
            result[camel_key] = [
                _convert_struct_to_dict(item, omit_none=omit_none)
                if (is_dataclass(item) and not isinstance(item, type))
                else item
                for item in value
            ]
        else:
            result[camel_key] = value
    return result


# ---------------------------------------------------------------------------
# Zone creation filter — mirrors Go filterZoneCreate()
# ---------------------------------------------------------------------------


def _is_zero(value: Any) -> bool:
    """Return True when *value* is a Go-style zero value."""
    if value is None:
        return True
    if isinstance(value, str) and value == "":
        return True
    if isinstance(value, bool):
        return not value
    if isinstance(value, (int, float)) and value == 0:
        return True
    if isinstance(value, list) and len(value) == 0:
        return True
    return False


def _filter_zone_field(
    attr_name: str, value: Any, zone_type: str,
) -> tuple[bool, Any]:
    """Decide whether a single ZoneCreate field is included and how.

    Returns ``(include, serialised_value)`` for the given field.
    Mirrors the per-field logic inside Go ``filterZoneCreate()``.
    """
    # Fields gated on a specific zone type
    required_type = _ZONE_FIELD_TYPE_GATE.get(attr_name)
    if required_type is not None:
        if zone_type != required_type:
            return (False, None)
        val = _convert_struct_to_dict(value) if (
            attr_name == "tsig_key" and value is not None
        ) else value
        return (True, val)

    # Fields excluded for ALIAS zones
    if attr_name in ("sign_and_serve", "sign_and_serve_algorithm"):
        return (zone_type != "ALIAS", value)

    # Outbound transfer — include only when non-None
    if attr_name == "outbound_zone_transfer":
        included = value is not None
        val = _convert_struct_to_dict(value, omit_none=False) if included else None
        return (included, val)

    # Default: include with auto dataclass conversion
    serialised = _convert_struct_to_dict(value) if (
        is_dataclass(value) and not isinstance(value, type)
    ) else value
    return (True, serialised)


def _filter_zone_create(zone: models.ZoneCreate) -> dict[str, Any]:
    """Build a filtered dict for zone create / update requests.

    Mirrors Go ``filterZoneCreate()`` at ``zone.go:668-714``.
    Removes fields that are invalid for the given zone type.
    """
    zone_type = zone.type.upper()
    filtered: dict[str, Any] = {}

    for fld in fields(zone):
        json_key = _ZONE_STRUCT_MAP.get(fld.name)
        if json_key is None:
            continue
        value = getattr(zone, fld.name)
        include, serialised = _filter_zone_field(
            fld.name, value, zone_type,
        )
        if include:
            filtered[json_key] = serialised

    return filtered


# ---------------------------------------------------------------------------
# TSIG query string builder — mirrors Go constructTSIGQueryString()
# ---------------------------------------------------------------------------


def _construct_tsig_query_string(tsig_query: models.TSIGQueryString) -> str:
    """Build a query string from a ``TSIGQueryString`` instance.

    Mirrors Go ``constructTSIGQueryString()`` at ``tsig.go:201-249``.
    Uses ``%2C`` as the separator for list fields, matching Go's manual
    encoding behaviour.
    """
    parts: list[str] = []

    # ContractIDs
    if tsig_query.contract_ids:
        contract_list = "%2C".join(tsig_query.contract_ids)
        parts.append("contractIds=" + contract_list)

    # Search
    if tsig_query.search:
        parts.append("search=" + tsig_query.search)

    # SortBy
    if tsig_query.sort_by:
        sort_by_list = "%2C".join(tsig_query.sort_by)
        parts.append("sortBy=" + sort_by_list)

    # GID
    if tsig_query.gid != 0:
        parts.append("gid=" + str(tsig_query.gid))

    query = "&".join(parts)
    if query:
        return "?" + query
    return ""


# ---------------------------------------------------------------------------
# Lock evaluation — mirrors Go localLock()
# ---------------------------------------------------------------------------


def _local_lock(rec_lock: list[bool]) -> bool:
    """Evaluate lock argument.

    Mirrors Go ``localLock()`` at ``record.go:103-110``.
    Returns the first boolean value; defaults to True (lock).
    """
    for lock in rec_lock:
        return lock
    return True


class _ConditionalLock:
    """Context manager that conditionally acquires a threading.Lock.

    When *do_lock* is ``True`` the lock is acquired on ``__enter__`` and
    released on ``__exit__``.  When ``False`` the lock is left untouched.
    """

    __slots__ = ("_lock", "_do_lock")

    def __init__(self, lock: threading.Lock, do_lock: bool) -> None:
        self._lock = lock
        self._do_lock = do_lock

    def __enter__(self) -> None:
        if self._do_lock:
            self._lock.acquire()  # pylint: disable=consider-using-with

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._do_lock:
            self._lock.release()


# ---------------------------------------------------------------------------
# IPv6, LOC padding helpers — mirrors Go fullIPv6, padValue, padCoordinates
# ---------------------------------------------------------------------------


def _full_ipv6(ip_str: str) -> str:
    """Expand an IPv6 address string to its full 32-hex-digit colon form.

    Mirrors Go ``fullIPv6()`` at ``record_lookup.go:87-99``.
    """
    addr = ipaddress.ip_address(ip_str)
    if isinstance(addr, ipaddress.IPv6Address):
        # exploded gives "xxxx:xxxx:..." full form
        return addr.exploded
    # Fallback: return as-is for IPv4
    return ip_str


def _pad_value(val: str) -> str:
    """Strip 'm' suffix and format as ``%.2f``.

    Mirrors Go ``padValue()`` at ``record_lookup.go:101-109``.
    """
    new_str = val.replace("m", "")
    try:
        fval = float(new_str)
    except ValueError:
        return "FAIL"
    return f"{fval:.2f}"


def _pad_coordinates(val: str) -> str:
    """Pad LOC record coordinate string.

    Mirrors Go ``padCoordinates()`` at ``record_lookup.go:111-120``.
    """
    parts = val.split(" ")
    if len(parts) < 12:
        return ""

    (latd, latm, lats, lat_dir, longd, longm, longs, long_dir,
     altitude, size, horiz_precision, vert_precision) = parts[:12]

    return (
        f"{latd} {latm} {lats} {lat_dir} "
        f"{longd} {longm} {longs} {long_dir} "
        f"{_pad_value(altitude)}m "
        f"{_pad_value(size)}m "
        f"{_pad_value(horiz_precision)}m "
        f"{_pad_value(vert_precision)}m"
    )


# ---------------------------------------------------------------------------
# ParseRData resolver functions — one per DNS record type
# Each mirrors the corresponding Go ``resolve*Type()`` function in
# ``record_lookup.go``.
# ---------------------------------------------------------------------------


def _resolve_afsdb_type(
    rdata: list[str],
    new_rdata: list[str],  # pylint: disable=unused-argument
    field_map: dict[str, Any],
) -> None:
    """Resolve AFSDB record fields. Mirrors Go ``resolveAFSDBType``."""
    targets: list[str] = []
    subtype = 0
    for entry in rdata:
        parts = entry.split()
        subtype = int(parts[0])
        targets.append(parts[1])
    field_map["subtype"] = subtype
    field_map["target"] = targets


def _resolve_dnskey_type(
    rdata: list[str],
    new_rdata: list[str],  # pylint: disable=unused-argument
    field_map: dict[str, Any],
) -> None:
    """Resolve DNSKEY record fields. Mirrors Go ``resolveDNSKEYType``."""
    for entry in rdata:
        parts = entry.split()
        field_map["flags"] = int(parts[0])
        field_map["protocol"] = int(parts[1])
        field_map["algorithm"] = int(parts[2])
        field_map["key"] = " ".join(parts[3:])
        break


def _resolve_ds_type(
    rdata: list[str],
    new_rdata: list[str],  # pylint: disable=unused-argument
    field_map: dict[str, Any],
) -> None:
    """Resolve DS record fields. Mirrors Go ``resolveDSType``."""
    for entry in rdata:
        parts = entry.split()
        field_map["keytag"] = int(parts[0])
        field_map["algorithm"] = int(parts[1])
        field_map["digest_type"] = int(parts[2])
        field_map["digest"] = " ".join(parts[3:])
        break


def _resolve_hinfo_type(
    rdata: list[str],
    new_rdata: list[str],  # pylint: disable=unused-argument
    field_map: dict[str, Any],
) -> None:
    """Resolve HINFO record fields. Mirrors Go ``resolveHINFOType``."""
    for entry in rdata:
        parts = entry.split()
        field_map["hardware"] = parts[0]
        field_map["software"] = parts[1]
        break


def _resolve_naptr_type(
    rdata: list[str],
    new_rdata: list[str],  # pylint: disable=unused-argument
    field_map: dict[str, Any],
) -> None:
    """Resolve NAPTR record fields. Mirrors Go ``resolveNAPTRType``."""
    for entry in rdata:
        parts = entry.split()
        field_map["order"] = int(parts[0])
        field_map["preference"] = int(parts[1])
        field_map["flagsnaptr"] = parts[2]
        field_map["service"] = parts[3]
        field_map["regexp"] = parts[4]
        field_map["replacement"] = parts[5]
        break


def _resolve_nsec3_type(
    rdata: list[str],
    new_rdata: list[str],  # pylint: disable=unused-argument
    field_map: dict[str, Any],
) -> None:
    """Resolve NSEC3 record fields. Mirrors Go ``resolveNSEC3Type``."""
    for entry in rdata:
        parts = entry.split()
        field_map["algorithm"] = int(parts[0])
        field_map["flags"] = int(parts[1])
        field_map["iterations"] = int(parts[2])
        field_map["salt"] = parts[3]
        field_map["next_hashed_owner_name"] = parts[4]
        field_map["type_bitmaps"] = parts[5]
        break


def _resolve_nsec3param_type(
    rdata: list[str],
    new_rdata: list[str],  # pylint: disable=unused-argument
    field_map: dict[str, Any],
) -> None:
    """Resolve NSEC3PARAM record fields. Mirrors Go ``resolveNSEC3PARAMType``."""
    for entry in rdata:
        parts = entry.split()
        field_map["algorithm"] = int(parts[0])
        field_map["flags"] = int(parts[1])
        field_map["iterations"] = int(parts[2])
        field_map["salt"] = parts[3]
        break


def _resolve_rp_type(
    rdata: list[str],
    new_rdata: list[str],  # pylint: disable=unused-argument
    field_map: dict[str, Any],
) -> None:
    """Resolve RP record fields. Mirrors Go ``resolveRPType``."""
    for entry in rdata:
        parts = entry.split()
        field_map["mailbox"] = parts[0]
        field_map["txt"] = parts[1]
        break


def _resolve_rrsig_type(
    rdata: list[str],
    new_rdata: list[str],  # pylint: disable=unused-argument
    field_map: dict[str, Any],
) -> None:
    """Resolve RRSIG record fields. Mirrors Go ``resolveRRSIGType``."""
    for entry in rdata:
        parts = entry.split()
        field_map["type_covered"] = parts[0]
        field_map["algorithm"] = int(parts[1])
        field_map["labels"] = int(parts[2])
        field_map["original_ttl"] = int(parts[3])
        field_map["expiration"] = parts[4]
        field_map["inception"] = parts[5]
        field_map["keytag"] = int(parts[6])
        field_map["signer"] = parts[7]
        field_map["signature"] = " ".join(parts[8:])
        break


def _resolve_srv_type(
    rdata: list[str],
    new_rdata: list[str],
    field_map: dict[str, Any],
) -> None:
    """Resolve SRV record fields. Mirrors Go ``resolveSRVType``."""
    # Check if all entries share same priority, weight, port
    if len(rdata) > 0:
        first_parts = rdata[0].split()
        priority = first_parts[0]
        weight = first_parts[1]
        port = first_parts[2]
        all_same = True
        for entry in rdata[1:]:
            parts = entry.split()
            if parts[0] != priority or parts[1] != weight or parts[2] != port:
                all_same = False
                break
        if all_same:
            field_map["priority"] = int(priority)
            field_map["weight"] = int(weight)
            field_map["port"] = int(port)
            targets = [entry.split()[3] for entry in rdata]
            field_map["target"] = targets
        else:
            # Can't extract common values; remove fields and use raw
            field_map.pop("priority", None)
            field_map.pop("weight", None)
            field_map.pop("port", None)
            new_rdata.clear()
            new_rdata.extend(rdata)
            field_map["target"] = list(rdata)


def _resolve_sshfp_type(
    rdata: list[str],
    new_rdata: list[str],  # pylint: disable=unused-argument
    field_map: dict[str, Any],
) -> None:
    """Resolve SSHFP record fields. Mirrors Go ``resolveSSHFPType``."""
    for entry in rdata:
        parts = entry.split()
        field_map["algorithm"] = int(parts[0])
        field_map["fingerprint_type"] = int(parts[1])
        field_map["fingerprint"] = parts[2]
        break


def _resolve_soa_type(
    rdata: list[str],
    new_rdata: list[str],  # pylint: disable=unused-argument
    field_map: dict[str, Any],
) -> None:
    """Resolve SOA record fields. Mirrors Go ``resolveSOAType``."""
    for entry in rdata:
        parts = entry.split()
        field_map["name_server"] = parts[0]
        field_map["email_address"] = parts[1]
        field_map["serial"] = int(parts[2])
        field_map["refresh"] = int(parts[3])
        field_map["retry"] = int(parts[4])
        field_map["expiry"] = int(parts[5])
        field_map["nxdomain_ttl"] = int(parts[6])
        break


def _resolve_akamaitlc_type(
    rdata: list[str],
    new_rdata: list[str],  # pylint: disable=unused-argument
    field_map: dict[str, Any],
) -> None:
    """Resolve AKAMAITLC record fields. Mirrors Go ``resolveAKAMAITLCType``."""
    for entry in rdata:
        parts = entry.split()
        field_map["answer_type"] = parts[0]
        field_map["dns_name"] = parts[1]
        break


def _resolve_spf_type(
    rdata: list[str],
    new_rdata: list[str],
    field_map: dict[str, Any],
) -> None:
    """Resolve SPF record fields. Mirrors Go ``resolveSPFType``."""
    new_rdata.clear()
    new_rdata.extend(rdata)
    field_map["target"] = list(new_rdata)


def _resolve_txt_type(
    rdata: list[str],
    new_rdata: list[str],
    field_map: dict[str, Any],
) -> None:
    """Resolve TXT record fields. Mirrors Go ``resolveTXTType``."""
    new_rdata.clear()
    new_rdata.extend(rdata)
    field_map["target"] = list(new_rdata)


def _resolve_aaaa_type(
    rdata: list[str],
    new_rdata: list[str],
    field_map: dict[str, Any],
) -> None:
    """Resolve AAAA record fields. Mirrors Go ``resolveAAAAType``."""
    new_rdata.clear()
    for entry in rdata:
        new_rdata.append(_full_ipv6(entry))
    field_map["target"] = list(new_rdata)


def _resolve_loc_type(
    rdata: list[str],
    new_rdata: list[str],
    field_map: dict[str, Any],
) -> None:
    """Resolve LOC record fields. Mirrors Go ``resolveLOCType``."""
    new_rdata.clear()
    for entry in rdata:
        new_rdata.append(_pad_coordinates(entry))
    field_map["target"] = list(new_rdata)


def _resolve_cert_type(
    rdata: list[str],
    new_rdata: list[str],  # pylint: disable=unused-argument
    field_map: dict[str, Any],
) -> None:
    """Resolve CERT record fields. Mirrors Go ``resolveCERTType``."""
    for entry in rdata:
        parts = entry.split()
        try:
            field_map["type_value"] = int(parts[0])
            field_map["type_mnemonic"] = ""
        except ValueError:
            field_map["type_mnemonic"] = parts[0]
            field_map["type_value"] = 0
        field_map["keytag"] = int(parts[1])
        field_map["algorithm"] = int(parts[2])
        field_map["certificate"] = parts[3]
        break


def _resolve_tlsa_type(
    rdata: list[str],
    new_rdata: list[str],  # pylint: disable=unused-argument
    field_map: dict[str, Any],
) -> None:
    """Resolve TLSA record fields. Mirrors Go ``resolveTLSAType``."""
    for entry in rdata:
        parts = entry.split()
        field_map["usage"] = int(parts[0])
        field_map["selector"] = int(parts[1])
        field_map["match_type"] = int(parts[2])
        field_map["certificate"] = parts[3]
        break


def _resolve_svcb_type(
    rdata: list[str],
    new_rdata: list[str],  # pylint: disable=unused-argument
    field_map: dict[str, Any],
) -> None:
    """Resolve SVCB record fields. Mirrors Go ``resolveSVCBType``."""
    for entry in rdata:
        parts = entry.split(None, 2)
        field_map["svc_priority"] = int(parts[0])
        field_map["target_name"] = parts[1]
        if len(parts) > 2:
            field_map["svc_params"] = parts[2]
        break


def _resolve_https_type(
    rdata: list[str],
    new_rdata: list[str],
    field_map: dict[str, Any],
) -> None:
    """Resolve HTTPS record fields. Mirrors Go ``resolveHTTPSType``.

    Identical logic to SVCB.
    """
    _resolve_svcb_type(rdata, new_rdata, field_map)


# Map of record type name → resolver function
_RDATA_RESOLVERS: dict[str, Any] = {
    "AFSDB": _resolve_afsdb_type,
    "DNSKEY": _resolve_dnskey_type,
    "DS": _resolve_ds_type,
    "HINFO": _resolve_hinfo_type,
    "NAPTR": _resolve_naptr_type,
    "NSEC3": _resolve_nsec3_type,
    "NSEC3PARAM": _resolve_nsec3param_type,
    "RP": _resolve_rp_type,
    "RRSIG": _resolve_rrsig_type,
    "SRV": _resolve_srv_type,
    "SSHFP": _resolve_sshfp_type,
    "SOA": _resolve_soa_type,
    "AKAMAITLC": _resolve_akamaitlc_type,
    "SPF": _resolve_spf_type,
    "TXT": _resolve_txt_type,
    "AAAA": _resolve_aaaa_type,
    "LOC": _resolve_loc_type,
    "CERT": _resolve_cert_type,
    "TLSA": _resolve_tlsa_type,
    "SVCB": _resolve_svcb_type,
    "HTTPS": _resolve_https_type,
}


# ===================================================================
# Client class
# ===================================================================


class Client:
    """Edge DNS API client.

    Provides access to Akamai DNS V2 APIs including zone management,
    record operations, TSIG key management, and bulk zone operations.

    Mirrors Go ``pkg/dns.DNS`` interface and ``dns`` struct.

    API failures raise :class:`~akamai.edgegrid.dns.errors.Error`
    (aliased as ``dns_errors.Error``) containing the RFC 7807 error
    payload returned by the server.

    Usage::

        >>> from akamai.edgegrid.session import Session
        >>> from akamai.edgegrid.dns.dns import Client
        >>> sess = Session(base_url="https://akaa-xxx.luna.akamaiapis.net",
        ...                client_token="tok", client_secret="sec", access_token="acc")
        >>> client = Client(sess)
        >>> zones = client.list_zones(ListZonesRequest())
    """

    #: Reference to the DNS-specific Error class for ``isinstance`` checks.
    Error = dns_errors.Error

    def __init__(self, session: Session) -> None:
        """Initialize DNS client with an authenticated session.

        Mirrors Go ``dns.Client(sess session.Session, opts ...Option) DNS``.

        Args:
            session: An authenticated :class:`~akamai.edgegrid.session.Session`.

        Raises:
            ValueError: If *session* is ``None``.
        """
        if session is None:
            raise ValueError(
                f"{dns_errors.ErrBadRequest}: session must not be None"
            )
        self._session = session

    # -----------------------------------------------------------------
    # Authorities — mirrors authorities.go
    # -----------------------------------------------------------------

    def get_authorities(
        self, params: models.GetAuthoritiesRequest
    ) -> models.GetAuthoritiesResponse:
        """Get a list of authoritative name servers for the specified contracts.

        See: https://techdocs.akamai.com/edge-dns/reference/get-data-authorities
        Mirrors Go ``dns.GetAuthorities``.
        """
        logger.debug("GetAuthorities")

        err = validation.validate_get_authorities_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrGetAuthorities}: struct validation: {err}"
            )

        url = f"/config-dns/v2/data/authorities?contractIds={params.contract_ids}"

        _, resp = self._session.exec(
            "GET", url, expect_json=True,
            error_parser=dns_errors.parse_dns_error_response,
        )

        return _build_response(models.GetAuthoritiesResponse, resp)

    def get_name_server_record_list(
        self, params: models.GetNameServerRecordListRequest
    ) -> list[str]:
        """Get a flattened list of name server records across contracts.

        See: https://techdocs.akamai.com/edge-dns/reference/get-data-authorities
        Mirrors Go ``dns.GetNameServerRecordList``.
        """
        logger.debug("GetNameServerRecordList")

        err = validation.validate_get_name_server_record_list_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrGetNameServerRecordList}: struct validation: {err}"
            )

        ns_response = self.get_authorities(
            models.GetAuthoritiesRequest(contract_ids=params.contract_ids)
        )

        result: list[str] = []
        for contract in ns_response.contracts:
            result.extend(contract.authorities)

        return result

    # -----------------------------------------------------------------
    # Data — mirrors data.go
    # -----------------------------------------------------------------

    def list_groups(
        self, params: models.ListGroupRequest
    ) -> models.ListGroupResponse:
        """List groups associated with the current user.

        See: https://techdocs.akamai.com/edge-dns/reference/get-data-groups
        Mirrors Go ``dns.ListGroups``.

        Raises ``dns_errors.ErrListGroups`` context on failure.
        """
        logger.debug("ListGroups")

        url = "/config-dns/v2/data/groups"
        query_params: dict[str, str] = {}
        if params.group_id:
            query_params["gid"] = params.group_id

        try:
            _, resp = self._session.exec(
                "GET", url, params=query_params, expect_json=True,
                error_parser=dns_errors.parse_dns_error_response,
            )
        except Exception as exc:
            raise type(exc)(
                f"{dns_errors.ErrListGroups}: {exc}"
            ) from exc

        return _build_response(models.ListGroupResponse, resp)

    # -----------------------------------------------------------------
    # Records — mirrors record.go
    # -----------------------------------------------------------------

    def create_record(self, params: models.CreateRecordRequest) -> None:
        """Create a record set in the specified zone.

        Uses a write lock for SOA serial value consistency.

        See: https://techdocs.akamai.com/edge-dns/reference/post-zones-zone-names-name-types-type
        Mirrors Go ``dns.CreateRecord``.
        """
        with _ConditionalLock(
            _zone_record_write_lock, _local_lock(params.rec_lock)
        ):
            logger.debug("CreateRecord")

            err = validation.validate_create_record_request(params)
            if err is not None:
                raise ValueError(
                    f"{dns_errors.ErrCreateRecord}: struct validation: {err}"
                )

            try:
                validation.validate_record_body(params.record)
            except ValueError as exc:
                raise ValueError(
                    f"{dns_errors.ErrCreateRecord}: struct validation: {exc}"
                ) from exc

            body = _convert_struct_to_dict(params.record)
            url = (
                f"/config-dns/v2/zones/{params.zone}"
                f"/names/{params.record.name}"
                f"/types/{params.record.record_type}"
            )

            _resp, _ = self._session.exec(
                "POST", url, body=body,
                error_parser=dns_errors.parse_dns_error_response,
            )
            Session.close_response_body(_resp)

    def update_record(self, params: models.UpdateRecordRequest) -> None:
        """Replace a record set in the specified zone.

        Uses a write lock for SOA serial value consistency.

        See: https://techdocs.akamai.com/edge-dns/reference/put-zones-zone-names-name-types-type
        Mirrors Go ``dns.UpdateRecord``.
        """
        with _ConditionalLock(
            _zone_record_write_lock, _local_lock(params.rec_lock)
        ):
            logger.debug("UpdateRecord")

            err = validation.validate_update_record_request(params)
            if err is not None:
                raise ValueError(
                    f"{dns_errors.ErrUpdateRecord}: struct validation: {err}"
                )

            try:
                validation.validate_record_body(params.record)
            except ValueError as exc:
                raise ValueError(
                    f"{dns_errors.ErrUpdateRecord}: struct validation: {exc}"
                ) from exc

            body = _convert_struct_to_dict(params.record)
            url = (
                f"/config-dns/v2/zones/{params.zone}"
                f"/names/{params.record.name}"
                f"/types/{params.record.record_type}"
            )

            _resp, _ = self._session.exec(
                "PUT", url, body=body,
                error_parser=dns_errors.parse_dns_error_response,
            )
            Session.close_response_body(_resp)

    def delete_record(self, params: models.DeleteRecordRequest) -> None:
        """Delete a record set from the specified zone.

        Uses a write lock for SOA serial value consistency.

        See: https://techdocs.akamai.com/edge-dns/reference/delete-zones-zone-names-name-types-type
        Mirrors Go ``dns.DeleteRecord``.
        """
        with _ConditionalLock(
            _zone_record_write_lock, _local_lock(params.rec_lock)
        ):
            logger.debug("DeleteRecord")

            err = validation.validate_delete_record_request(params)
            if err is not None:
                raise ValueError(
                    f"{dns_errors.ErrDeleteRecord}: struct validation: {err}"
                )

            url = (
                f"/config-dns/v2/zones/{params.zone}"
                f"/names/{params.name}"
                f"/types/{params.record_type}"
            )

            _resp, _ = self._session.exec(
                "DELETE", url,
                error_parser=dns_errors.parse_dns_error_response,
            )
            Session.close_response_body(_resp)

    # -----------------------------------------------------------------
    # Record Lookup — mirrors record_lookup.go
    # -----------------------------------------------------------------

    def get_record(
        self, params: models.GetRecordRequest
    ) -> models.GetRecordResponse:
        """Get a record set as a ``RecordBody``.

        See: https://techdocs.akamai.com/edge-dns/reference/get-zones-zone-names-name-types-type
        Mirrors Go ``dns.GetRecord``.
        """
        logger.debug("GetRecord")

        err = validation.validate_get_record_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrGetRecord}: struct validation: {err}"
            )

        url = (
            f"/config-dns/v2/zones/{params.zone}"
            f"/names/{params.name}"
            f"/types/{params.record_type}"
        )

        _, resp = self._session.exec(
            "GET", url, expect_json=True,
            error_parser=dns_errors.parse_dns_error_response,
        )

        return _build_response(models.GetRecordResponse, resp)

    def get_record_list(
        self, params: models.GetRecordListRequest
    ) -> models.GetRecordListResponse:
        """Get a list of record sets for a zone filtered by type.

        See: https://techdocs.akamai.com/edge-dns/reference/get-zones-zone-recordsets
        Mirrors Go ``dns.GetRecordList``.
        """
        logger.debug("GetRecordList")

        err = validation.validate_get_record_list_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrGetRecordList}: struct validation: {err}"
            )

        url = (
            f"/config-dns/v2/zones/{params.zone}"
            f"/recordsets?types={params.record_type}&showAll=true"
        )

        _, resp = self._session.exec(
            "GET", url, expect_json=True,
            error_parser=dns_errors.parse_dns_error_response,
        )

        return _build_response(models.GetRecordListResponse, resp)

    def get_rdata(self, params: models.GetRdataRequest) -> list[str]:
        """Retrieve record RDATA, applying normalisation for AAAA and LOC types.

        See: https://techdocs.akamai.com/edge-dns/reference/get-zones-zone-recordsets
        Mirrors Go ``dns.GetRdata``.
        """
        logger.debug("GetRdata")

        err = validation.validate_get_rdata_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrGetRecordList}: struct validation: {err}"
            )

        records = self.get_record_list(
            models.GetRecordListRequest(zone=params.zone, record_type=params.record_type)
        )

        target_rdata: list[str] = []
        for rec in records.record_sets:
            if rec.name == params.name:
                target_rdata = list(rec.rdata) if rec.rdata else []
                break

        return self.process_rdata(target_rdata, params.record_type)

    def process_rdata(self, rdata: list[str], rtype: str) -> list[str]:
        """Normalise RDATA entries for AAAA (expand IPv6) and LOC (pad coordinates).

        Mirrors Go ``dns.ProcessRdata``.
        """
        logger.debug("ProcessRdata")
        rtype_upper = rtype.upper()

        if rtype_upper == "AAAA":
            return [_full_ipv6(entry) for entry in rdata]

        if rtype_upper == "LOC":
            return [_pad_coordinates(entry) for entry in rdata]

        return rdata

    def parse_rdata(self, rtype: str, rdata: list[str]) -> dict[str, Any]:
        """Parse RDATA entries and return a map of resolved field values.

        Supports 21 record types via specialised resolver functions.  For
        unknown types the default handler stores the raw RDATA as ``target``.

        Mirrors Go ``dns.ParseRData``.
        """
        logger.debug("ParseRData")

        field_map: dict[str, Any] = {}
        new_rdata: list[str] = list(rdata)

        resolver = _RDATA_RESOLVERS.get(rtype.upper())
        if resolver is not None:
            resolver(rdata, new_rdata, field_map)
        else:
            # Default resolver — store raw target
            field_map["target"] = list(rdata)

        return field_map

    # -----------------------------------------------------------------
    # Record Sets — mirrors recordsets.go
    # -----------------------------------------------------------------

    def get_record_sets(
        self, params: models.GetRecordSetsRequest
    ) -> models.GetRecordSetsResponse:
        """Get record sets with optional query filters.

        See: https://techdocs.akamai.com/edge-dns/reference/get-zones-zone-recordsets
        Mirrors Go ``dns.GetRecordSets``.
        """
        logger.debug("GetRecordSets")

        err = validation.validate_get_record_sets_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrGetRecordSets}: struct validation: {err}"
            )

        query_params: dict[str, Any] = {}
        if params.query_args is not None:
            qa = params.query_args
            if qa.page is not None:
                query_params["page"] = qa.page
            if qa.page_size is not None:
                query_params["pageSize"] = qa.page_size
            if qa.search:
                query_params["search"] = qa.search
            if qa.show_all is not None:
                query_params["showAll"] = str(qa.show_all).lower()
            if qa.sort_by:
                query_params["sortBy"] = qa.sort_by
            if qa.types:
                query_params["types"] = qa.types

        url = f"/config-dns/v2/zones/{params.zone}/recordsets"

        _, resp = self._session.exec(
            "GET", url, params=query_params, expect_json=True,
            error_parser=dns_errors.parse_dns_error_response,
        )

        return _build_response(models.GetRecordSetsResponse, resp)

    def create_record_sets(
        self, params: models.CreateRecordSetsRequest
    ) -> None:
        """Create multiple record sets in a zone.

        Uses a write lock for SOA serial value consistency.

        See: https://techdocs.akamai.com/edge-dns/reference/post-zones-zone-recordsets
        Mirrors Go ``dns.CreateRecordSets``.
        """
        with _ConditionalLock(
            _zone_record_sets_write_lock, _local_lock(params.rec_lock)
        ):
            logger.debug("CreateRecordSets")

            err = validation.validate_create_record_sets_request(params)
            if err is not None:
                raise ValueError(
                    f"{dns_errors.ErrCreateRecordSets}: struct validation: {err}"
                )

            try:
                validation.validate_record_sets(params.record_sets)
            except ValueError as exc:
                raise ValueError(
                    f"{dns_errors.ErrCreateRecordSets}: struct validation: {exc}"
                ) from exc

            body = _convert_struct_to_dict(params.record_sets)
            url = f"/config-dns/v2/zones/{params.zone}/recordsets"

            _resp, _ = self._session.exec(
                "POST", url, body=body,
                error_parser=dns_errors.parse_dns_error_response,
            )
            Session.close_response_body(_resp)

    def update_record_sets(
        self, params: models.UpdateRecordSetsRequest
    ) -> None:
        """Replace the list of record sets in a zone.

        Uses a write lock for SOA serial value consistency.

        See: https://techdocs.akamai.com/edge-dns/reference/put-zones-zone-recordsets
        Mirrors Go ``dns.UpdateRecordSets``.
        """
        with _ConditionalLock(
            _zone_record_sets_write_lock, _local_lock(params.rec_lock)
        ):
            logger.debug("UpdateRecordSets")

            err = validation.validate_update_record_sets_request(params)
            if err is not None:
                raise ValueError(
                    f"{dns_errors.ErrUpdateRecordSets}: struct validation: {err}"
                )

            try:
                validation.validate_record_sets(params.record_sets)
            except ValueError as exc:
                raise ValueError(
                    f"{dns_errors.ErrUpdateRecordSets}: struct validation: {exc}"
                ) from exc

            body = _convert_struct_to_dict(params.record_sets)
            url = f"/config-dns/v2/zones/{params.zone}/recordsets"

            _resp, _ = self._session.exec(
                "PUT", url, body=body,
                error_parser=dns_errors.parse_dns_error_response,
            )
            Session.close_response_body(_resp)

    # -----------------------------------------------------------------
    # TSIG Keys — mirrors tsig.go
    # -----------------------------------------------------------------

    def list_tsig_keys(
        self, params: models.ListTSIGKeysRequest
    ) -> models.ListTSIGKeysResponse:
        """List TSIG keys.

        See: https://techdocs.akamai.com/edge-dns/reference/get-keys
        Mirrors Go ``dns.ListTSIGKeys``.

        Raises ``dns_errors.ErrListTSIGKeys`` context on failure.
        """
        logger.debug("ListTSIGKeys")

        query_string = _construct_tsig_query_string(params.tsig_query)
        url = f"/config-dns/v2/keys{query_string}"

        try:
            _, resp = self._session.exec(
                "GET", url, expect_json=True,
                error_parser=dns_errors.parse_dns_error_response,
            )
        except Exception as exc:
            raise type(exc)(
                f"{dns_errors.ErrListTSIGKeys}: {exc}"
            ) from exc

        return _build_response(models.ListTSIGKeysResponse, resp)

    def get_tsig_key_zones(
        self, params: models.GetTSIGKeyZonesRequest
    ) -> models.GetTSIGKeyZonesResponse:
        """Get zones that use a specific TSIG key.

        See: https://techdocs.akamai.com/edge-dns/reference/post-keys-used-by
        Mirrors Go ``dns.GetTSIGKeyZones``.
        """
        logger.debug("GetTSIGKeyZones")

        err = validation.validate_get_tsig_key_zones_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrGetTSIGKeyZones}: struct validation: {err}"
            )

        body = _convert_struct_to_dict(params.tsig_key)
        url = "/config-dns/v2/keys/used-by"

        _, resp = self._session.exec(
            "POST", url, body=body, expect_json=True,
            error_parser=dns_errors.parse_dns_error_response,
        )

        return _build_response(models.GetTSIGKeyZonesResponse, resp)

    def get_tsig_key_aliases(
        self, params: models.GetTSIGKeyAliasesRequest
    ) -> models.GetTSIGKeyAliasesResponse:
        """Get TSIG key aliases for a zone.

        See: https://techdocs.akamai.com/edge-dns/reference/get-zones-zone-key-used-by
        Mirrors Go ``dns.GetTSIGKeyAliases``.
        """
        logger.debug("GetTSIGKeyAliases")

        err = validation.validate_get_tsig_key_aliases_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrGetTSIGKeyAliases}: struct validation: {err}"
            )

        url = f"/config-dns/v2/zones/{params.zone}/key/used-by"

        _, resp = self._session.exec(
            "GET", url, expect_json=True,
            error_parser=dns_errors.parse_dns_error_response,
        )

        return _build_response(models.GetTSIGKeyAliasesResponse, resp)

    def update_tsig_key_bulk(
        self, params: models.UpdateTSIGKeyBulkRequest
    ) -> None:
        """Bulk-update the TSIG key for multiple zones.

        See: https://techdocs.akamai.com/edge-dns/reference/post-keys-bulk-update
        Mirrors Go ``dns.UpdateTSIGKeyBulk``.
        """
        logger.debug("UpdateTSIGKeyBulk")

        err = validation.validate_update_tsig_key_bulk_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrUpdateTSIGKeyBulk}: struct validation: {err}"
            )

        try:
            validation.validate_tsig_key_bulk_post(params.tsig_key_bulk)
        except ValueError as exc:
            raise ValueError(
                f"{dns_errors.ErrUpdateTSIGKeyBulk}: struct validation: {exc}"
            ) from exc

        body = _convert_struct_to_dict(params.tsig_key_bulk)
        url = "/config-dns/v2/keys/bulk-update"

        _resp, _ = self._session.exec(
            "POST", url, body=body,
            error_parser=dns_errors.parse_dns_error_response,
        )
        Session.close_response_body(_resp)

    def get_tsig_key(
        self, params: models.GetTSIGKeyRequest
    ) -> models.GetTSIGKeyResponse:
        """Get the TSIG key for a zone.

        See: https://techdocs.akamai.com/edge-dns/reference/get-zones-zone-key
        Mirrors Go ``dns.GetTSIGKey``.
        """
        logger.debug("GetTSIGKey")

        err = validation.validate_get_tsig_key_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrGetTSIGKey}: struct validation: {err}"
            )

        url = f"/config-dns/v2/zones/{params.zone}/key"

        _, resp = self._session.exec(
            "GET", url, expect_json=True,
            error_parser=dns_errors.parse_dns_error_response,
        )

        return _build_response(models.GetTSIGKeyResponse, resp)

    def delete_tsig_key(
        self, params: models.DeleteTSIGKeyRequest
    ) -> None:
        """Delete the TSIG key for a zone.

        See: https://techdocs.akamai.com/edge-dns/reference/delete-zones-zone-key
        Mirrors Go ``dns.DeleteTSIGKey``.
        """
        logger.debug("DeleteTSIGKey")

        err = validation.validate_delete_tsig_key_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrDeleteTSIGKey}: struct validation: {err}"
            )

        url = f"/config-dns/v2/zones/{params.zone}/key"

        _resp, _ = self._session.exec(
            "DELETE", url,
            error_parser=dns_errors.parse_dns_error_response,
        )
        Session.close_response_body(_resp)

    def update_tsig_key(
        self, params: models.UpdateTSIGKeyRequest
    ) -> None:
        """Update the TSIG key for a zone.

        See: https://techdocs.akamai.com/edge-dns/reference/put-zones-zone-key
        Mirrors Go ``dns.UpdateTSIGKey``.
        """
        logger.debug("UpdateTSIGKey")

        err = validation.validate_update_tsig_key_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrUpdateTSIGKey}: struct validation: {err}"
            )

        try:
            validation.validate_tsig_key(params.tsig_key)
        except ValueError as exc:
            raise ValueError(
                f"{dns_errors.ErrUpdateTSIGKey}: struct validation: {exc}"
            ) from exc

        body = _convert_struct_to_dict(params.tsig_key)
        url = f"/config-dns/v2/zones/{params.zone}/key"

        _resp, _ = self._session.exec(
            "PUT", url, body=body,
            error_parser=dns_errors.parse_dns_error_response,
        )
        Session.close_response_body(_resp)

    # -----------------------------------------------------------------
    # Zones — mirrors zone.go
    # -----------------------------------------------------------------

    def list_zones(
        self, params: models.ListZonesRequest
    ) -> models.ZoneListResponse:
        """List all zones matching the query parameters.

        See: https://techdocs.akamai.com/edge-dns/reference/get-zones
        Mirrors Go ``dns.ListZones``.
        """
        logger.debug("ListZones")

        query_params: dict[str, Any] = {}
        if params.page:
            query_params["page"] = params.page
        if params.page_size:
            query_params["pageSize"] = params.page_size
        if params.search:
            query_params["search"] = params.search
        if params.show_all:
            query_params["showAll"] = str(params.show_all).lower()
        if params.sort_by:
            query_params["sortBy"] = params.sort_by
        if params.types:
            query_params["types"] = params.types
        if params.contract_ids:
            query_params["contractIds"] = params.contract_ids

        url = "/config-dns/v2/zones"

        _, resp = self._session.exec(
            "GET", url, params=query_params, expect_json=True,
            error_parser=dns_errors.parse_dns_error_response,
        )

        return _build_response(models.ZoneListResponse, resp)

    def get_zone(
        self, params: models.GetZoneRequest
    ) -> models.GetZoneResponse:
        """Get zone metadata.

        See: https://techdocs.akamai.com/edge-dns/reference/get-zones-zone
        Mirrors Go ``dns.GetZone``.
        """
        logger.debug("GetZone")

        err = validation.validate_get_zone_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrGetZone}: struct validation: {err}"
            )

        url = f"/config-dns/v2/zones/{params.zone}"

        _, resp = self._session.exec(
            "GET", url, expect_json=True,
            error_parser=dns_errors.parse_dns_error_response,
        )

        return _build_response(models.GetZoneResponse, resp)

    def get_change_list(
        self, params: models.GetChangeListRequest
    ) -> models.GetChangeListResponse:
        """Get the change list for a zone.

        See: https://techdocs.akamai.com/edge-dns/reference/get-changelists-zone
        Mirrors Go ``dns.GetChangeList``.
        """
        logger.debug("GetChangeList")

        err = validation.validate_get_change_list_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrGetChangeList}: struct validation: {err}"
            )

        url = f"/config-dns/v2/changelists/{params.zone}"

        _, resp = self._session.exec(
            "GET", url, expect_json=True,
            error_parser=dns_errors.parse_dns_error_response,
        )

        return _build_response(models.GetChangeListResponse, resp)

    def get_master_zone_file(
        self, params: models.GetMasterZoneFileRequest
    ) -> str:
        """Get the master zone file contents as text.

        See: https://techdocs.akamai.com/edge-dns/reference/get-zones-zone-zone-file
        Mirrors Go ``dns.GetMasterZoneFile``.

        Note: Uses ``Accept: text/dns`` header.
        """
        logger.debug("GetMasterZoneFile")

        err = validation.validate_get_master_zone_file_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrGetMasterZoneFile}: struct validation: {err}"
            )

        url = f"/config-dns/v2/zones/{params.zone}/zone-file"

        response, _ = self._session.exec(
            "GET", url,
            headers={"Accept": "text/dns"},
            error_parser=dns_errors.parse_dns_error_response,
        )

        return response.text

    def post_master_zone_file(
        self, params: models.PostMasterZoneFileRequest
    ) -> None:
        """Update the master zone file.

        See: https://techdocs.akamai.com/edge-dns/reference/post-zones-zone-zone-file
        Mirrors Go ``dns.PostMasterZoneFile``.

        Note: Uses ``Content-Type: text/dns`` header.
        """
        logger.debug("PostMasterZoneFile")

        err = validation.validate_post_master_zone_file_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrPostMasterZoneFile}: struct validation: {err}"
            )

        url = f"/config-dns/v2/zones/{params.zone}/zone-file"

        file_data = params.file_data
        if isinstance(file_data, str):
            file_data = file_data.encode("utf-8")

        _resp, _ = self._session.exec(
            "POST", url, body=file_data,
            headers={"Content-Type": "text/dns"},
            error_parser=dns_errors.parse_dns_error_response,
        )
        Session.close_response_body(_resp)

    def create_zone(
        self, params: models.CreateZoneRequest
    ) -> None:
        """Create a new zone.

        Uses a zone write lock. Builds request body via ``_filter_zone_create``.

        See: https://techdocs.akamai.com/edge-dns/reference/post-zones
        Mirrors Go ``dns.CreateZone``.
        """
        with _zone_write_lock:
            logger.debug("CreateZone")

            err = validation.validate_create_zone_request(params)
            if err is not None:
                raise ValueError(
                    f"{dns_errors.ErrCreateZone}: struct validation: {err}"
                )

            try:
                validation.validate_zone(params.create_zone)
            except ValueError as exc:
                raise ValueError(
                    f"{dns_errors.ErrCreateZone}: struct validation: {exc}"
                ) from exc

            body = _filter_zone_create(params.create_zone)

            query_params: dict[str, str] = {}
            if params.zone_query_string is not None:
                zqs = params.zone_query_string
                if zqs.contract:
                    query_params["contractId"] = zqs.contract
                if zqs.group:
                    query_params["gid"] = zqs.group

            url = "/config-dns/v2/zones"

            _resp, _ = self._session.exec(
                "POST", url, body=body, params=query_params,
                error_parser=dns_errors.parse_dns_error_response,
            )
            Session.close_response_body(_resp)

            if (params.clear_conn
                    and params.create_zone.type.upper() == "PRIMARY"):
                Session.close_response_body(None)

    def save_change_list(
        self, params: models.SaveChangeListRequest
    ) -> None:
        """Save a change list for a zone.

        Uses a zone write lock.

        See: https://techdocs.akamai.com/edge-dns/reference/post-changelists
        Mirrors Go ``dns.SaveChangeList``.
        """
        with _zone_write_lock:
            logger.debug("SaveChangeList")

            err = validation.validate_save_change_list_request(params)
            if err is not None:
                raise ValueError(
                    f"{dns_errors.ErrSaveChangeList}: struct validation: {err}"
                )

            url = (
                "/config-dns/v2/changelists"
                f"?zone={quote(params.zone, safe='')}"
            )

            _resp, _ = self._session.exec(
                "POST", url, body="",
                error_parser=dns_errors.parse_dns_error_response,
            )
            Session.close_response_body(_resp)

    def submit_change_list(
        self, params: models.SubmitChangeListRequest
    ) -> None:
        """Submit a change list for a zone.

        Uses a zone write lock.

        See: https://techdocs.akamai.com/edge-dns/reference/post-changelists-zone-submit
        Mirrors Go ``dns.SubmitChangeList``.
        """
        with _zone_write_lock:
            logger.debug("SubmitChangeList")

            err = validation.validate_submit_change_list_request(params)
            if err is not None:
                raise ValueError(
                    f"{dns_errors.ErrSubmitChangeList}: struct validation: {err}"
                )

            url = f"/config-dns/v2/changelists/{params.zone}/submit"

            _resp, _ = self._session.exec(
                "POST", url, body="",
                error_parser=dns_errors.parse_dns_error_response,
            )
            Session.close_response_body(_resp)

    def update_zone(
        self, params: models.UpdateZoneRequest
    ) -> None:
        """Update a zone.

        Uses a zone write lock. Validates the zone and builds the body via
        ``_filter_zone_create``.

        See: https://techdocs.akamai.com/edge-dns/reference/put-zones-zone
        Mirrors Go ``dns.UpdateZone``.
        """
        with _zone_write_lock:
            logger.debug("UpdateZone")

            try:
                validation.validate_zone(params.create_zone)
            except ValueError as exc:
                raise ValueError(
                    f"{dns_errors.ErrGetZone}: struct validation: {exc}"
                ) from exc

            body = _filter_zone_create(params.create_zone)
            url = f"/config-dns/v2/zones/{params.create_zone.zone}"

            _resp, _ = self._session.exec(
                "PUT", url, body=body,
                error_parser=dns_errors.parse_dns_error_response,
            )
            Session.close_response_body(_resp)

    def get_zone_names(
        self, params: models.GetZoneNamesRequest
    ) -> models.GetZoneNamesResponse:
        """Get record names in a zone.

        See: https://techdocs.akamai.com/edge-dns/reference/get-zones-zone-names
        Mirrors Go ``dns.GetZoneNames``.
        """
        logger.debug("GetZoneNames")

        err = validation.validate_get_zone_names_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrGetZoneNames}: struct validation: {err}"
            )

        url = f"/config-dns/v2/zones/{params.zone}/names"

        _, resp = self._session.exec(
            "GET", url, expect_json=True,
            error_parser=dns_errors.parse_dns_error_response,
        )

        return _build_response(models.GetZoneNamesResponse, resp)

    def get_zone_name_types(
        self, params: models.GetZoneNameTypesRequest
    ) -> models.GetZoneNameTypesResponse:
        """Get record types for a specific name in a zone.

        See: https://techdocs.akamai.com/edge-dns/reference/get-zones-zone-names-name-types
        Mirrors Go ``dns.GetZoneNameTypes``.
        """
        logger.debug("GetZoneNameTypes")

        err = validation.validate_get_zone_name_types_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrGetZoneNameTypes}: struct validation: {err}"
            )

        url = f"/config-dns/v2/zones/{params.zone}/names/{params.zone_name}/types"

        _, resp = self._session.exec(
            "GET", url, expect_json=True,
            error_parser=dns_errors.parse_dns_error_response,
        )

        return _build_response(models.GetZoneNameTypesResponse, resp)

    def get_zones_dnssec_status(
        self, params: models.GetZonesDNSSecStatusRequest
    ) -> models.GetZonesDNSSecStatusResponse:
        """Get DNSSEC status for the specified zones.

        See: https://techdocs.akamai.com/edge-dns/reference/post-zones-dns-sec-status
        Mirrors Go ``dns.GetZonesDNSSecStatus``.
        """
        logger.debug("GetZonesDNSSecStatus")

        err = validation.validate_get_zones_dnssec_status_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrGetZone}: struct validation: {err}"
            )

        body = {"zones": params.zones}
        url = "/config-dns/v2/zones/dns-sec-status"

        _, resp = self._session.exec(
            "POST", url, body=body, expect_json=True,
            error_parser=dns_errors.parse_dns_error_response,
        )

        return _build_response(models.GetZonesDNSSecStatusResponse, resp)

    # -----------------------------------------------------------------
    # Bulk Zones — mirrors zonebulk.go
    # -----------------------------------------------------------------

    def create_bulk_zones(
        self, params: models.CreateBulkZonesRequest
    ) -> models.CreateBulkZonesResponse:
        """Submit a bulk zone-create request.

        See: https://techdocs.akamai.com/edge-dns/reference/post-zones-create-requests
        Mirrors Go ``dns.CreateBulkZones``.
        """
        logger.debug("CreateBulkZones")

        err = validation.validate_create_bulk_zones_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrCreateBulkZones}: struct validation: {err}"
            )

        body = _convert_struct_to_dict(params.bulk_zones)

        query_params: dict[str, str] = {}
        if params.zone_query_string is not None:
            zqs = params.zone_query_string
            if zqs.contract:
                query_params["contractId"] = zqs.contract
            if zqs.group:
                query_params["gid"] = zqs.group

        url = "/config-dns/v2/zones/create-requests"

        _, resp = self._session.exec(
            "POST", url, body=body, params=query_params, expect_json=True,
            error_parser=dns_errors.parse_dns_error_response,
        )

        return _build_response(models.CreateBulkZonesResponse, resp)

    def delete_bulk_zones(
        self, params: models.DeleteBulkZonesRequest
    ) -> models.DeleteBulkZonesResponse:
        """Submit a bulk zone-delete request.

        See: https://techdocs.akamai.com/edge-dns/reference/post-zones-delete-requests
        Mirrors Go ``dns.DeleteBulkZones``.
        """
        logger.debug("DeleteBulkZones")

        err = validation.validate_delete_bulk_zones_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrDeleteBulkZones}: struct validation: {err}"
            )

        body = _convert_struct_to_dict(params.zones_list)

        query_params: dict[str, str] = {}
        if params.bypass_safety_checks is not None:
            query_params["bypassSafetyChecks"] = str(
                params.bypass_safety_checks
            ).lower()

        url = "/config-dns/v2/zones/delete-requests"

        _, resp = self._session.exec(
            "POST", url, body=body, params=query_params, expect_json=True,
            error_parser=dns_errors.parse_dns_error_response,
        )

        return _build_response(models.DeleteBulkZonesResponse, resp)

    def get_bulk_zone_create_status(
        self, params: models.GetBulkZoneCreateStatusRequest
    ) -> models.GetBulkZoneCreateStatusResponse:
        """Get the status of a bulk zone-create request.

        See: https://techdocs.akamai.com/edge-dns/reference/get-zones-create-requests-requestid
        Mirrors Go ``dns.GetBulkZoneCreateStatus``.
        """
        logger.debug("GetBulkZoneCreateStatus")

        err = validation.validate_get_bulk_zone_create_status_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrGetBulkZoneCreateStatus}: struct validation: {err}"
            )

        url = f"/config-dns/v2/zones/create-requests/{params.request_id}"

        _, resp = self._session.exec(
            "GET", url, expect_json=True,
            error_parser=dns_errors.parse_dns_error_response,
        )

        return _build_response(models.GetBulkZoneCreateStatusResponse, resp)

    def get_bulk_zone_delete_status(
        self, params: models.GetBulkZoneDeleteStatusRequest
    ) -> models.GetBulkZoneDeleteStatusResponse:
        """Get the status of a bulk zone-delete request.

        See: https://techdocs.akamai.com/edge-dns/reference/get-zones-delete-requests-requestid
        Mirrors Go ``dns.GetBulkZoneDeleteStatus``.
        """
        logger.debug("GetBulkZoneDeleteStatus")

        err = validation.validate_get_bulk_zone_delete_status_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrGetBulkZoneDeleteStatus}: struct validation: {err}"
            )

        url = f"/config-dns/v2/zones/delete-requests/{params.request_id}"

        _, resp = self._session.exec(
            "GET", url, expect_json=True,
            error_parser=dns_errors.parse_dns_error_response,
        )

        return _build_response(models.GetBulkZoneDeleteStatusResponse, resp)

    def get_bulk_zone_create_result(
        self, params: models.GetBulkZoneCreateResultRequest
    ) -> models.GetBulkZoneCreateResultResponse:
        """Get the result of a bulk zone-create request.

        See: https://techdocs.akamai.com/edge-dns/reference/
             get-zones-create-requests-requestid-result
        Mirrors Go ``dns.GetBulkZoneCreateResult``.
        """
        logger.debug("GetBulkZoneCreateResult")

        err = validation.validate_get_bulk_zone_create_result_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrGetBulkZoneCreateResult}: struct validation: {err}"
            )

        url = f"/config-dns/v2/zones/create-requests/{params.request_id}/result"

        _, resp = self._session.exec(
            "GET", url, expect_json=True,
            error_parser=dns_errors.parse_dns_error_response,
        )

        return _build_response(models.GetBulkZoneCreateResultResponse, resp)

    def get_bulk_zone_delete_result(
        self, params: models.GetBulkZoneDeleteResultRequest
    ) -> models.GetBulkZoneDeleteResultResponse:
        """Get the result of a bulk zone-delete request.

        See: https://techdocs.akamai.com/edge-dns/reference/
             get-zones-delete-requests-requestid-result
        Mirrors Go ``dns.GetBulkZoneDeleteResult``.
        """
        logger.debug("GetBulkZoneDeleteResult")

        err = validation.validate_get_bulk_zone_delete_result_request(params)
        if err is not None:
            raise ValueError(
                f"{dns_errors.ErrGetBulkZoneDeleteResult}: struct validation: {err}"
            )

        url = f"/config-dns/v2/zones/delete-requests/{params.request_id}/result"

        _, resp = self._session.exec(
            "GET", url, expect_json=True,
            error_parser=dns_errors.parse_dns_error_response,
        )

        return _build_response(models.GetBulkZoneDeleteResultResponse, resp)
