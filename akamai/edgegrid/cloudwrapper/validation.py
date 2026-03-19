"""Request validation functions for Cloud Wrapper API.

Each exported function mirrors a ``Validate()`` method from the
corresponding Go request struct in ``pkg/cloudwrapper``.  Functions
return a formatted error string matching Go
``edgegriderr.ParseValidationErrors`` output, or ``None`` when
validation passes.

Go reference files
------------------
- ``pkg/cloudwrapper/configurations.go`` lines 198-353
- ``pkg/cloudwrapper/properties.go`` lines 80-87
- ``pkg/cloudwrapper/multi_cdn.go`` lines 46-52
"""

from akamai.edgegrid.cloudwrapper import models
from akamai.edgegrid.validation import parse_validation_errors


# ---------------------------------------------------------------------------
# Public request validators — called by the CloudWrapper client
# ---------------------------------------------------------------------------


def validate_get_configuration_request(req) -> str | None:
    """Validate a *GetConfigurationRequest*.

    Go reference: ``GetConfigurationRequest.Validate()``
    (configurations.go:199-203)

    Args:
        req: A ``GetConfigurationRequest`` instance.

    Returns:
        Formatted error string or ``None``.
    """
    errors: dict = {}
    if not req.config_id:
        errors["ConfigID"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_create_configuration_request(req) -> str | None:
    """Validate a *CreateConfigurationRequest*.

    Go reference: ``CreateConfigurationRequest.Validate()``
    (configurations.go:206-210)

    Args:
        req: A ``CreateConfigurationRequest`` instance.

    Returns:
        Formatted error string or ``None``.
    """
    errors: dict = {}
    if not req.body:
        errors["Body"] = "cannot be blank"
    else:
        body_errors = _validate_create_configuration_request_body(req.body)
        if body_errors:
            errors["Body"] = body_errors
    return parse_validation_errors(errors)


def validate_update_configuration_request(req) -> str | None:
    """Validate an *UpdateConfigurationRequest*.

    Go reference: ``UpdateConfigurationRequest.Validate()``
    (configurations.go:226-231)

    Args:
        req: An ``UpdateConfigurationRequest`` instance.

    Returns:
        Formatted error string or ``None``.
    """
    errors: dict = {}
    if not req.config_id:
        errors["ConfigID"] = "cannot be blank"
    if not req.body:
        errors["Body"] = "cannot be blank"
    else:
        body_errors = _validate_update_configuration_request_body(req.body)
        if body_errors:
            errors["Body"] = body_errors
    return parse_validation_errors(errors)


def validate_delete_configuration_request(req) -> str | None:
    """Validate a *DeleteConfigurationRequest*.

    Go reference: ``DeleteConfigurationRequest.Validate()``
    (configurations.go:245-249)

    Args:
        req: A ``DeleteConfigurationRequest`` instance.

    Returns:
        Formatted error string or ``None``.
    """
    errors: dict = {}
    if not req.config_id:
        errors["ConfigID"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_activate_configuration_request(req) -> str | None:
    """Validate an *ActivateConfigurationRequest*.

    Go reference: ``ActivateConfigurationRequest.Validate()``
    (configurations.go:252-256)

    Args:
        req: An ``ActivateConfigurationRequest`` instance.

    Returns:
        Formatted error string or ``None``.
    """
    errors: dict = {}
    if not req.configuration_ids:
        errors["ConfigurationIDs"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_list_origins_request(req) -> str | None:
    """Validate a *ListOriginsRequest*.

    Go reference: ``ListOriginsRequest.Validate()``
    (properties.go:81-87)

    Args:
        req: A ``ListOriginsRequest`` instance.

    Returns:
        Formatted error string or ``None``.
    """
    errors: dict = {}
    if not req.contract_id:
        errors["ContractID"] = "cannot be blank"
    if not req.group_id:
        errors["GroupID"] = "cannot be blank"
    if not req.property_id:
        errors["PropertyID"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_list_auth_keys_request(req) -> str | None:
    """Validate a *ListAuthKeysRequest*.

    Go reference: ``ListAuthKeysRequest.Validate()``
    (multi_cdn.go:47-52)

    Args:
        req: A ``ListAuthKeysRequest`` instance.

    Returns:
        Formatted error string or ``None``.
    """
    errors: dict = {}
    if not req.cdn_code:
        errors["CDNCode"] = "cannot be blank"
    if not req.contract_id:
        errors["ContractID"] = "cannot be blank"
    return parse_validation_errors(errors)


# ---------------------------------------------------------------------------
# Private body / nested-object validators
# ---------------------------------------------------------------------------


def _validate_create_configuration_request_body(body) -> dict | None:
    """Validate *CreateConfigurationRequestBody* fields.

    Go reference: ``CreateConfigurationRequestBody.Validate()``
    (configurations.go:213-223)
    """
    errors: dict = {}

    _check_capacity_alerts_threshold(body.capacity_alerts_threshold, errors)

    if not body.comments:
        errors["Comments"] = "cannot be blank"
    if not body.config_name:
        errors["ConfigName"] = "cannot be blank"
    if not body.contract_id:
        errors["ContractID"] = "cannot be blank"

    _check_locations(body.locations, errors)

    if body.multi_cdn_settings is not None:
        mcdn_errors = _validate_multi_cdn_settings(body.multi_cdn_settings)
        if mcdn_errors:
            errors["MultiCDNSettings"] = mcdn_errors

    if not body.property_ids:
        errors["PropertyIDs"] = "cannot be blank"

    return errors if errors else None


def _validate_update_configuration_request_body(body) -> dict | None:
    """Validate *UpdateConfigurationRequestBody* fields.

    Go reference: ``UpdateConfigurationRequestBody.Validate()``
    (configurations.go:234-242)
    """
    errors: dict = {}

    _check_capacity_alerts_threshold(body.capacity_alerts_threshold, errors)

    if not body.comments:
        errors["Comments"] = "cannot be blank"

    _check_locations(body.locations, errors)

    if body.multi_cdn_settings is not None:
        mcdn_errors = _validate_multi_cdn_settings(body.multi_cdn_settings)
        if mcdn_errors:
            errors["MultiCDNSettings"] = mcdn_errors

    if not body.property_ids:
        errors["PropertyIDs"] = "cannot be blank"

    return errors if errors else None


# ---------------------------------------------------------------------------
# Shared helpers used by both create and update body validators
# ---------------------------------------------------------------------------


def _check_locations(locations, errors):
    """Validate a list of *ConfigLocationReq* and populate *errors*.

    When the list is empty the ``"Locations"`` key receives a
    ``"cannot be blank"`` message.  Otherwise each individual
    location is validated and indexed element errors are collected.
    """
    if not locations:
        errors["Locations"] = "cannot be blank"
        return
    loc_errors: dict = {}
    for idx, loc in enumerate(locations):
        inner = _validate_config_location_req(loc)
        if inner:
            loc_errors[str(idx)] = inner
    if loc_errors:
        errors["Locations"] = loc_errors


def _check_capacity_alerts_threshold(value, errors):
    """Validate *CapacityAlertsThreshold* range ``[50, 100]``.

    Go reference: ``validation.Min(50), validation.Max(100)``
    (configurations.go:219, 238)
    """
    if value is None:
        return
    if value < 50:
        errors["CapacityAlertsThreshold"] = "must be no less than 50"
    elif value > 100:
        errors["CapacityAlertsThreshold"] = (
            f"value '{value}' is invalid. "
            "Must be between 50 and 100"
        )


# ---------------------------------------------------------------------------
# Nested-struct validators
# ---------------------------------------------------------------------------


def _validate_config_location_req(loc) -> dict | None:
    """Validate a *ConfigLocationReq*.

    Go reference: ``ConfigLocationReq.Validate()``
    (configurations.go:259-265)
    """
    errors: dict = {}

    cap_errors = _validate_capacity(loc.capacity)
    if cap_errors:
        errors["Capacity"] = cap_errors

    if not loc.comments:
        errors["Comments"] = "cannot be blank"
    if not loc.traffic_type_id:
        errors["TrafficTypeID"] = "cannot be blank"

    return errors if errors else None


def _validate_capacity(cap) -> dict | None:
    """Validate a *Capacity* object.

    Go reference: ``Capacity.Validate()``
    (configurations.go:268-273)
    """
    errors: dict = {}

    if not cap.unit:
        errors["Unit"] = "cannot be blank"
    elif cap.unit not in (models.UNIT_GB, models.UNIT_TB):
        errors["Unit"] = (
            f"value '{cap.unit}' is invalid. "
            f"Must be one of: '{models.UNIT_GB}', '{models.UNIT_TB}'"
        )

    if not cap.value:
        errors["Value"] = "cannot be blank"
    elif cap.value < 1:
        errors["Value"] = "must be no less than 1"
    elif cap.value > 10000000000:
        errors["Value"] = "must be no greater than 10000000000"

    return errors if errors else None


def _check_optional_struct(value, key, validator, errors):
    """Validate an optional (pointer-in-Go) nested struct.

    If *value* is ``None`` (Go ``nil``), records ``"cannot be blank"``.
    Otherwise delegates to *validator* and stores any nested errors.
    """
    if value is None:
        errors[key] = "cannot be blank"
        return
    nested = validator(value)
    if nested:
        errors[key] = nested


def _check_element_list(items, key, validator, errors):
    """Validate a required list of elements.

    Records ``"cannot be blank"`` when the list is empty, else
    validates each element and collects indexed errors.
    """
    if not items:
        errors[key] = "cannot be blank"
        return
    elem_errors: dict = {}
    for idx, item in enumerate(items):
        inner = validator(item)
        if inner:
            elem_errors[str(idx)] = inner
    if elem_errors:
        errors[key] = elem_errors


def _check_cdns_field(cdns, errors):
    """Validate the CDNs field with custom + element validation.

    Runs ``_validate_cdns`` first; only runs element-level
    ``_validate_cdn`` when the custom check passes.
    """
    cdns_error = _validate_cdns(cdns)
    if cdns_error is not None:
        errors["CDNs"] = cdns_error
    elif cdns:
        cdns_elem: dict = {}
        for idx, cdn in enumerate(cdns):
            cdn_err = _validate_cdn(cdn)
            if cdn_err:
                cdns_elem[str(idx)] = cdn_err
        if cdns_elem:
            errors["CDNs"] = cdns_elem


def _validate_multi_cdn_settings(settings) -> dict | None:
    """Validate *MultiCDNSettings*.

    Go reference: ``MultiCDNSettings.Validate()``
    (configurations.go:276-283)
    """
    errors: dict = {}

    # BOCC — *BOCC in Go; BOCC | None in Python
    _check_optional_struct(settings.bocc, "BOCC", _validate_bocc, errors)

    # CDNs — custom validator then element validation
    _check_cdns_field(settings.cdns, errors)

    # DataStreams — *DataStreams in Go; DataStreams | None in Python
    _check_optional_struct(
        settings.data_streams, "DataStreams",
        _validate_data_streams, errors,
    )

    # Origins — Required (not empty), element validation
    _check_element_list(settings.origins, "Origins", _validate_origin, errors)

    return errors if errors else None


def _validate_bocc(bocc) -> dict | None:
    """Validate *BOCC* settings.

    Go reference: ``BOCC.Validate()``
    (configurations.go:286-294)

    Note
    ----
    The ``SamplingFrequency`` In-check error message intentionally
    uses ``bocc.request_type`` instead of ``bocc.sampling_frequency``.
    This mirrors a bug in the Go source at line 292.
    """
    errors: dict = {}

    # Enabled — validation.NotNil on bool always passes; no check needed.

    freq_valid = (
        models.SAMPLING_FREQUENCY_ZERO,
        models.SAMPLING_FREQUENCY_ONE_TENTH,
    )

    # ConditionalSamplingFrequency
    _check_bocc_enum(
        errors, "ConditionalSamplingFrequency",
        bocc.conditional_sampling_frequency, freq_valid, bocc.enabled,
    )

    # ForwardType
    _check_bocc_enum(
        errors, "ForwardType",
        bocc.forward_type,
        (
            models.FORWARD_TYPE_ORIGIN_ONLY,
            models.FORWARD_TYPE_MIDGRESS_ONLY,
            models.FORWARD_TYPE_ORIGIN_AND_MIDGRESS,
        ),
        bocc.enabled,
    )

    # RequestType
    _check_bocc_enum(
        errors, "RequestType",
        bocc.request_type,
        (models.REQUEST_TYPE_EDGE_ONLY, models.REQUEST_TYPE_EDGE_AND_MIDGRESS),
        bocc.enabled,
    )

    # SamplingFrequency — Go bug at line 292: the In() error message
    # uses ``b.RequestType`` instead of ``b.SamplingFrequency``.
    # We mirror this exactly by using request_type as display value.
    _check_bocc_enum_with_display(
        errors, "SamplingFrequency",
        bocc.sampling_frequency, bocc.request_type,
        freq_valid, bocc.enabled,
    )

    return errors if errors else None


def _check_bocc_enum(errors, field_name, field_value, valid, required_when):
    """Check a BOCC enum field with conditional ``Required.When``.

    In Go's ozzo-validation, ``Required.When(enabled)`` makes the
    field required only when *enabled* is True.  The ``In(...)`` check
    runs for any non-empty value regardless of the When condition.
    """
    _check_bocc_enum_with_display(
        errors, field_name, field_value, field_value, valid, required_when,
    )


def _check_bocc_enum_with_display(
    errors, field_name, field_value, display_value, valid, required_when,
):  # pylint: disable=too-many-arguments,too-many-positional-arguments
    """Like ``_check_bocc_enum`` but uses *display_value* in messages.

    This variant is needed for SamplingFrequency where the Go source
    erroneously uses ``b.RequestType`` in the error message.
    """
    if required_when and not field_value:
        errors[field_name] = "cannot be blank"
    elif field_value and field_value not in valid:
        quoted = ", ".join(f"'{v}'" for v in valid)
        errors[field_name] = (
            f"value '{display_value}' is invalid. "
            f"Must be one of: {quoted}"
        )


def _validate_cdns(cdns) -> str | None:
    """Validate CDNs list — custom business-rule validator.

    Go reference: ``validateCDNs()``
    (configurations.go:331-353)

    Checks:
    - CDNs must not be empty.
    - At least one CDN must be enabled.
    - Each CDN must have either CDNAuthKeys or IPACLCIDRs.
    """
    if not cdns:
        return "cannot be blank"

    is_enabled = False
    for cdn in cdns:
        if cdn.enabled:
            is_enabled = True
        if not cdn.cdn_auth_keys and not cdn.ip_acl_cidrs:
            return (
                "at least one authentication method is required "
                "for CDN. Either IP ACL or header authentication "
                "must be enabled"
            )
    if not is_enabled:
        return "at least one of CDNs must be enabled"

    return None


def _validate_cdn(cdn) -> dict | None:
    """Validate a single *CDN*.

    Go reference: ``CDN.Validate()``
    (configurations.go:297-303)
    """
    errors: dict = {}

    # CDNAuthKeys — validate each key (element validation)
    if cdn.cdn_auth_keys:
        keys_errors: dict = {}
        for idx, key in enumerate(cdn.cdn_auth_keys):
            key_err = _validate_cdn_auth_key(key)
            if key_err:
                keys_errors[str(idx)] = key_err
        if keys_errors:
            errors["CDNAuthKeys"] = keys_errors

    # Enabled — validation.NotNil on bool always passes; no check needed.

    # CDNCode — Required
    if not cdn.cdn_code:
        errors["CDNCode"] = "cannot be blank"

    return errors if errors else None


def _validate_cdn_auth_key(key) -> dict | None:
    """Validate a *CDNAuthKey*.

    Go reference: ``CDNAuthKey.Validate()``
    (configurations.go:306-311)
    """
    errors: dict = {}

    # AuthKeyName — Required
    if not key.auth_key_name:
        errors["AuthKeyName"] = "cannot be blank"

    # Secret — Length(24, 24); skipped when empty (no Required rule)
    if key.secret and len(key.secret) != 24:
        errors["Secret"] = "the length must be exactly 24"

    return errors if errors else None


def _validate_data_streams(ds) -> dict | None:
    """Validate *DataStreams*.

    Go reference: ``DataStreams.Validate()``
    (configurations.go:314-319)
    """
    errors: dict = {}

    # Enabled — validation.NotNil on bool always passes; no check needed.

    # SamplingRate — When not None: Min(1), Max(100)
    if ds.sampling_rate is not None:
        if ds.sampling_rate < 1:
            errors["SamplingRate"] = "must be no less than 1"
        elif ds.sampling_rate > 100:
            errors["SamplingRate"] = (
                f"value '{ds.sampling_rate}' is invalid. "
                "Must be between 1 and 100"
            )

    return errors if errors else None


def _validate_origin(origin) -> dict | None:
    """Validate an *Origin*.

    Go reference: ``Origin.Validate()``
    (configurations.go:322-328)
    """
    errors: dict = {}
    if not origin.hostname:
        errors["Hostname"] = "cannot be blank"
    if not origin.origin_id:
        errors["OriginID"] = "cannot be blank"
    if not origin.property_id:
        errors["PropertyID"] = "cannot be blank"
    return errors if errors else None
