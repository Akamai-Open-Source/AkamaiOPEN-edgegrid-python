"""Request validation functions for Edge DNS API.

Each Go ``Validate()`` method on a request struct maps to a Python validation
function.  Two patterns exist:

**Pattern A** — ozzo-validation ``Required`` check via
``parse_validation_errors`` (most common).  Returns ``None`` when valid or a
formatted error string on failure.

**Pattern B** — Manual validation that raises ``ValueError`` directly,
mirroring Go's ``fmt.Errorf()`` calls (used by ``validate_record_body``,
``validate_zone``, ``validate_record_sets``).

Error field names in the ``errors`` dict intentionally use the **Go
PascalCase** names (e.g. ``"ContractIDs"``) so that formatted output matches
the Go SDK exactly.

Mirrors Go ``pkg/dns`` — authorities, record, record_lookup, recordsets,
tsig, zone, and zonebulk validation methods.
"""

from akamai.edgegrid.validation import parse_validation_errors


# ---------------------------------------------------------------------------
# authorities.go
# ---------------------------------------------------------------------------


def validate_get_authorities_request(request) -> str | None:
    """Validate ``GetAuthoritiesRequest``.

    Mirrors Go ``GetAuthoritiesRequest.Validate()``.

    Args:
        request: A request object with a ``contract_ids`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.contract_ids:
        errors["ContractIDs"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_get_name_server_record_list_request(request) -> str | None:
    """Validate ``GetNameServerRecordListRequest``.

    Mirrors Go ``GetNameServerRecordListRequest.Validate()``.

    Args:
        request: A request object with a ``contract_ids`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.contract_ids:
        errors["ContractIDs"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


# ---------------------------------------------------------------------------
# record.go
# ---------------------------------------------------------------------------


def validate_create_record_request(request) -> str | None:
    """Validate ``CreateRecordRequest``.

    Mirrors Go ``CreateRecordRequest.Validate()``.

    Args:
        request: A request object with ``zone`` and ``record`` attributes.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.zone:
        errors["Zone"] = "cannot be blank"
    if request.record is None:
        errors["Record"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_update_record_request(request) -> str | None:
    """Validate ``UpdateRecordRequest``.

    Mirrors Go ``UpdateRecordRequest.Validate()``.

    Args:
        request: A request object with ``zone`` and ``record`` attributes.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.zone:
        errors["Zone"] = "cannot be blank"
    if request.record is None:
        errors["Record"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_delete_record_request(request) -> str | None:
    """Validate ``DeleteRecordRequest``.

    Mirrors Go ``DeleteRecordRequest.Validate()``.

    Args:
        request: A request object with ``zone``, ``name``, and
            ``record_type`` attributes.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.zone:
        errors["Zone"] = "cannot be blank"
    if not request.name:
        errors["Name"] = "cannot be blank"
    if not request.record_type:
        errors["RecordType"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_record_body(record) -> str | None:
    """Validate a ``RecordBody`` object.

    Uses manual validation matching Go ``RecordBody.Validate()`` — raises
    ``ValueError`` on the first failed check.

    Args:
        record: A record object with ``name``, ``record_type``, ``ttl``,
            and ``target`` attributes.

    Returns:
        ``None`` if valid.

    Raises:
        ValueError: If any required field is missing or zero-valued.
    """
    if len(record.name) < 1:
        raise ValueError("RecordBody is missing Name")
    if len(record.record_type) < 1:
        raise ValueError("RecordBody is missing RecordType")
    if record.ttl == 0:
        raise ValueError("RecordBody is missing TTL")
    if len(record.target) < 1:
        raise ValueError("RecordBody is missing Target")


# ---------------------------------------------------------------------------
# record_lookup.go
# ---------------------------------------------------------------------------


def validate_get_record_request(request) -> str | None:
    """Validate ``GetRecordRequest``.

    Mirrors Go ``GetRecordRequest.Validate()``.

    Args:
        request: A request object with ``zone``, ``name``, and
            ``record_type`` attributes.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.zone:
        errors["Zone"] = "cannot be blank"
    if not request.name:
        errors["Name"] = "cannot be blank"
    if not request.record_type:
        errors["RecordType"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_get_record_list_request(request) -> str | None:
    """Validate ``GetRecordListRequest``.

    Mirrors Go ``GetRecordListRequest.Validate()``.

    Args:
        request: A request object with ``zone`` and ``record_type``
            attributes.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.zone:
        errors["Zone"] = "cannot be blank"
    if not request.record_type:
        errors["RecordType"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_get_rdata_request(request) -> str | None:
    """Validate ``GetRdataRequest``.

    Mirrors Go ``GetRdataRequest.Validate()``.

    Args:
        request: A request object with ``zone``, ``name``, and
            ``record_type`` attributes.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.zone:
        errors["Zone"] = "cannot be blank"
    if not request.name:
        errors["Name"] = "cannot be blank"
    if not request.record_type:
        errors["RecordType"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


# ---------------------------------------------------------------------------
# recordsets.go
# ---------------------------------------------------------------------------


def validate_get_record_sets_request(request) -> str | None:
    """Validate ``GetRecordSetsRequest``.

    Mirrors Go ``GetRecordSetsRequest.Validate()``.

    Args:
        request: A request object with a ``zone`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.zone:
        errors["Zone"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_create_record_sets_request(request) -> str | None:
    """Validate ``CreateRecordSetsRequest``.

    Mirrors Go ``CreateRecordSetsRequest.Validate()``.

    Args:
        request: A request object with ``zone`` and ``record_sets``
            attributes.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.zone:
        errors["Zone"] = "cannot be blank"
    if request.record_sets is None:
        errors["RecordSets"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_update_record_sets_request(request) -> str | None:
    """Validate ``UpdateRecordSetsRequest``.

    Mirrors Go ``UpdateRecordSetsRequest.Validate()``.

    Args:
        request: A request object with ``zone`` and ``record_sets``
            attributes.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.zone:
        errors["Zone"] = "cannot be blank"
    if request.record_sets is None:
        errors["RecordSets"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_record_sets(record_sets) -> str | None:
    """Validate a ``RecordSets`` object.

    Uses manual validation matching Go ``RecordSets.Validate()`` — raises
    ``ValueError`` when the list is empty or an individual record set has
    missing fields.

    Args:
        record_sets: An object with a ``record_sets`` list attribute, where
            each element has ``name``, ``type``, ``ttl``, and ``rdata``
            attributes.

    Returns:
        ``None`` if valid.

    Raises:
        ValueError: If the record set list is empty or any record set has
            blank required fields.
    """
    if len(record_sets.record_sets) < 1:
        raise ValueError("request initiated with empty recordsets list")
    for rec in record_sets.record_sets:
        errors: dict[str, str] = {}
        if not rec.name:
            errors["Name"] = "cannot be blank"
        if not rec.type:
            errors["Type"] = "cannot be blank"
        if not rec.ttl:
            errors["TTL"] = "cannot be blank"
        if not rec.rdata:
            errors["Rdata"] = "cannot be blank"
        filtered = {k: v for k, v in errors.items() if v is not None}
        if filtered:
            msg = parse_validation_errors(filtered)
            if msg:
                raise ValueError(msg)


# ---------------------------------------------------------------------------
# tsig.go
# ---------------------------------------------------------------------------


def validate_get_tsig_key_request(request) -> str | None:
    """Validate ``GetTSIGKeyRequest``.

    Mirrors Go ``GetTSIGKeyRequest.Validate()``.

    Args:
        request: A request object with a ``zone`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.zone:
        errors["Zone"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_delete_tsig_key_request(request) -> str | None:
    """Validate ``DeleteTSIGKeyRequest``.

    Mirrors Go ``DeleteTSIGKeyRequest.Validate()``.

    Args:
        request: A request object with a ``zone`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.zone:
        errors["Zone"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_get_tsig_key_aliases_request(request) -> str | None:
    """Validate ``GetTSIGKeyAliasesRequest``.

    Mirrors Go ``GetTSIGKeyAliasesRequest.Validate()``.

    Args:
        request: A request object with a ``zone`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.zone:
        errors["Zone"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_update_tsig_key_request(request) -> str | None:
    """Validate ``UpdateTSIGKeyRequest``.

    Mirrors Go ``UpdateTSIGKeyRequest.Validate()``.  The ``TsigKey`` field
    is validated via its own ``Validate()`` method (not a ``Required``
    check), so it is only validated when present.

    Args:
        request: A request object with ``zone`` and ``tsig_key`` attributes.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str | None] = {}
    if not request.zone:
        errors["Zone"] = "cannot be blank"
    if request.tsig_key is not None:
        key_err = validate_tsig_key(request.tsig_key)
        if key_err:
            errors["TsigKey"] = key_err
    return parse_validation_errors(errors) if errors else None


def validate_update_tsig_key_bulk_request(request) -> str | None:
    """Validate ``UpdateTSIGKeyBulkRequest``.

    Mirrors Go ``UpdateTSIGKeyBulkRequest.Validate()``.

    Args:
        request: A request object with a ``tsig_key_bulk`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if request.tsig_key_bulk is None:
        errors["TSIGKeyBulk"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_get_tsig_key_zones_request(request) -> str | None:
    """Validate ``GetTSIGKeyZonesRequest``.

    Mirrors Go ``GetTSIGKeyZonesRequest.Validate()``.

    Args:
        request: A request object with a ``tsig_key`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if request.tsig_key is None:
        errors["TsigKey"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_tsig_key(key) -> str | None:
    """Validate a ``TSIGKey`` object.

    Mirrors Go ``TSIGKey.Validate()``.

    Args:
        key: A TSIG key object with ``name``, ``algorithm``, and ``secret``
            attributes.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not key.name:
        errors["Name"] = "cannot be blank"
    if not key.algorithm:
        errors["Algorithm"] = "cannot be blank"
    if not key.secret:
        errors["Secret"] = "cannot be blank"
    filtered = {k: v for k, v in errors.items() if v is not None}
    if filtered:
        return parse_validation_errors(filtered)
    return None


def validate_tsig_key_bulk_post(bulk) -> str | None:
    """Validate a ``TSIGKeyBulkPost`` object.

    Mirrors Go ``TSIGKeyBulkPost.Validate()``.

    Args:
        bulk: A bulk post object with ``key`` and ``zones`` attributes.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if bulk.key is None:
        errors["Key"] = "cannot be blank"
    if not bulk.zones:
        errors["Zones"] = "cannot be blank"
    filtered = {k: v for k, v in errors.items() if v is not None}
    if filtered:
        return parse_validation_errors(filtered)
    return None


# ---------------------------------------------------------------------------
# zone.go
# ---------------------------------------------------------------------------


def validate_get_zone_request(request) -> str | None:
    """Validate ``GetZoneRequest``.

    Mirrors Go ``GetZoneRequest.Validate()``.

    Args:
        request: A request object with a ``zone`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.zone:
        errors["Zone"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_get_change_list_request(request) -> str | None:
    """Validate ``GetChangeListRequest``.

    Mirrors Go ``GetChangeListRequest.Validate()``.

    Args:
        request: A request object with a ``zone`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.zone:
        errors["Zone"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_get_master_zone_file_request(request) -> str | None:
    """Validate ``GetMasterZoneFileRequest``.

    Mirrors Go ``GetMasterZoneFileRequest.Validate()``.

    Args:
        request: A request object with a ``zone`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.zone:
        errors["Zone"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_post_master_zone_file_request(request) -> str | None:
    """Validate ``PostMasterZoneFileRequest``.

    Mirrors Go ``PostMasterZoneFileRequest.Validate()``.

    Args:
        request: A request object with a ``zone`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.zone:
        errors["Zone"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_create_zone_request(request) -> str | None:
    """Validate ``CreateZoneRequest``.

    Mirrors Go ``CreateZoneRequest.Validate()``.  Note: Go checks
    ``ZoneQueryString`` (required), not the ``Zone`` field.

    Args:
        request: A request object with a ``zone_query_string`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if request.zone_query_string is None:
        errors["ZoneQueryString"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_save_change_list_request(request) -> str | None:
    """Validate ``SaveChangeListRequest``.

    Mirrors Go ``SaveChangeListRequest.Validate()``.

    Args:
        request: A request object with a ``zone`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.zone:
        errors["Zone"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_submit_change_list_request(request) -> str | None:
    """Validate ``SubmitChangeListRequest``.

    Mirrors Go ``SubmitChangeListRequest.Validate()``.

    Args:
        request: A request object with a ``zone`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.zone:
        errors["Zone"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_get_zone_names_request(request) -> str | None:
    """Validate ``GetZoneNamesRequest``.

    Mirrors Go ``GetZoneNamesRequest.Validate()``.

    Args:
        request: A request object with a ``zone`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.zone:
        errors["Zone"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_get_zone_name_types_request(request) -> str | None:
    """Validate ``GetZoneNameTypesRequest``.

    Mirrors Go ``GetZoneNameTypesRequest.Validate()``.

    Args:
        request: A request object with ``zone`` and ``zone_name`` attributes.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.zone:
        errors["Zone"] = "cannot be blank"
    if not request.zone_name:
        errors["ZoneName"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_get_zones_dnssec_status_request(request) -> str | None:
    """Validate ``GetZonesDNSSecStatusRequest``.

    Mirrors Go ``GetZonesDNSSecStatusRequest.Validate()``.

    Args:
        request: A request object with a ``zones`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.zones:
        errors["Zones"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_zone(zone) -> str | None:
    """Validate a ``ZoneCreate`` object.

    Uses manual validation matching Go ``ValidateZone()`` — raises
    ``ValueError`` on the first failed check.

    Note: The Go code contains a deliberate typo ``"filed"`` (instead of
    ``"field"``) for the ``SignAndServeAlgorithm`` error message.  This is
    preserved exactly to maintain parity with the Go SDK.

    Args:
        zone: A zone create object with ``zone``, ``type``, ``target``,
            ``masters``, ``sign_and_serve``, ``sign_and_serve_algorithm``,
            and ``tsig_key`` attributes.

    Returns:
        ``None`` if valid.

    Raises:
        ValueError: If any zone type constraint is violated.
    """
    if not zone.zone:
        raise ValueError("field Zone name is required")
    z_type = zone.type.upper()
    if z_type not in ("PRIMARY", "SECONDARY", "ALIAS"):
        raise ValueError("invalid zone type")
    if z_type != "SECONDARY" and zone.tsig_key is not None:
        raise ValueError(f"TsigKey is invalid for {z_type} zone type")
    if z_type == "ALIAS":
        if not zone.target:
            raise ValueError("field Target is required for Alias zone type")
        if zone.masters:
            raise ValueError("field Masters is invalid for Alias zone type")
        if zone.sign_and_serve:
            raise ValueError(
                "field SignAndServe is invalid for Alias zone type"
            )
        if zone.sign_and_serve_algorithm:
            raise ValueError(
                "filed SignAndServeAlgorithm is invalid for Alias zone type"
            )
        return None
    # Primary or Secondary
    if zone.target:
        raise ValueError(f"field Target is invalid for {z_type} zone type")
    if zone.masters and z_type == "PRIMARY":
        raise ValueError("field Masters is invalid for Primary zone type")
    return None


# ---------------------------------------------------------------------------
# zonebulk.go
# ---------------------------------------------------------------------------


def validate_get_bulk_zone_create_status_request(request) -> str | None:
    """Validate ``GetBulkZoneCreateStatusRequest``.

    Mirrors Go ``GetBulkZoneCreateStatusRequest.Validate()``.

    Args:
        request: A request object with a ``request_id`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.request_id:
        errors["RequestID"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_get_bulk_zone_delete_status_request(request) -> str | None:
    """Validate ``GetBulkZoneDeleteStatusRequest``.

    Mirrors Go ``GetBulkZoneDeleteStatusRequest.Validate()``.

    Args:
        request: A request object with a ``request_id`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.request_id:
        errors["RequestID"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_get_bulk_zone_create_result_request(request) -> str | None:
    """Validate ``GetBulkZoneCreateResultRequest``.

    Mirrors Go ``GetBulkZoneCreateResultRequest.Validate()``.

    Args:
        request: A request object with a ``request_id`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.request_id:
        errors["RequestID"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_get_bulk_zone_delete_result_request(request) -> str | None:
    """Validate ``GetBulkZoneDeleteResultRequest``.

    Mirrors Go ``GetBulkZoneDeleteResultRequest.Validate()``.

    Args:
        request: A request object with a ``request_id`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if not request.request_id:
        errors["RequestID"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_create_bulk_zones_request(request) -> str | None:
    """Validate ``CreateBulkZonesRequest``.

    Mirrors Go ``CreateBulkZonesRequest.Validate()``.

    Args:
        request: A request object with a ``bulk_zones`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if request.bulk_zones is None:
        errors["BulkZones"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None


def validate_delete_bulk_zones_request(request) -> str | None:
    """Validate ``DeleteBulkZonesRequest``.

    Mirrors Go ``DeleteBulkZonesRequest.Validate()``.

    Args:
        request: A request object with a ``zones_list`` attribute.

    Returns:
        Formatted error string or ``None`` if valid.
    """
    errors: dict[str, str] = {}
    if request.zones_list is None:
        errors["ZonesList"] = "cannot be blank"
    return parse_validation_errors(errors) if errors else None
