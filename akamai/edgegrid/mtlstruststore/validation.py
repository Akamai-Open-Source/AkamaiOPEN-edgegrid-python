"""Request validation functions for the mTLS Trust Store API.

Mirrors every Validate() method from the Go mtlstruststore package:
  - ca_set.go            (CreateCASet, GetCASet, ListCASets, DeleteCASet,
                           ListCASetAssociations, CloneCASet,
                           GetCASetDeletionStatus, ListCASetActivities)
  - ca_set_versions.go   (CreateCASetVersion, ListCASetVersions,
                           UpdateCASetVersion, CloneCASetVersion,
                           GetCASetVersion, GetCASetVersionCertificates)
  - ca_set_activation.go (ActivateCASetVersion, DeactivateCASetVersion,
                           GetCASetVersionActivation,
                           ListCASetVersionActivations,
                           ListCASetActivations)
  - certificate.go       (ValidateCertificatesRequest, ValidateCertificate)

Each public function accepts the corresponding request dataclass and returns
``str | None``  — an error message string when validation fails, or ``None``
when the request is valid.  Error messages match Go test assertions exactly.
"""

import re
from datetime import datetime, timezone

from akamai.edgegrid.validation import parse_validation_errors
from akamai.edgegrid.mtlstruststore import models

# ---------------------------------------------------------------------------
# Compiled regex for CA set name validation
# Mirrors Go: CASetNameRegex = regexp.MustCompile(`^[%.a-zA-Z0-9_-]+$`)
# ---------------------------------------------------------------------------
_CA_SET_NAME_REGEX: re.Pattern[str] = re.compile(r'^[%.a-zA-Z0-9_-]+$')

_CA_SET_NAME_DESCRIPTION: str = (
    "allowed characters are alphanumerics (a-z, A-Z, 0-9), "
    "underscore (_), hyphen (-), percent (%) and period (.)"
)

# ---------------------------------------------------------------------------
# Valid enum value tuples used for In-rule validation
# ---------------------------------------------------------------------------
_VALID_NETWORKS: tuple[str, ...] = (
    "INACTIVE", "STAGING", "PRODUCTION",
    "STAGING+PRODUCTION", "PRODUCTION+STAGING",
    "STAGING,PRODUCTION", "PRODUCTION,STAGING",
)

_VALID_ACTIVATION_NETWORKS: tuple[str, ...] = ("STAGING", "PRODUCTION")

_VALID_ASSOCIATION_TYPES: tuple[str, ...] = ("enrollments", "properties")

_VALID_CERTIFICATE_STATUSES: tuple[str, ...] = (
    models.EXPIRING_CERT,
    models.EXPIRED_CERT,
    models.EXPIRED_OR_EXPIRING_CERT,
    models.EXPIRING_OR_EXPIRED_CERT,
    models.ACTIVE_CERT,
    models.ACTIVE_OR_EXPIRED_CERT,
    models.EXPIRED_OR_ACTIVE_CERT,
)

# Statuses allowed when ExpiryThresholdInDays is provided
_EXPIRY_DAYS_ALLOWED: tuple[str, ...] = (
    models.EXPIRING_CERT,
    models.EXPIRED_CERT,
    models.EXPIRED_OR_EXPIRING_CERT,
)

# Statuses allowed when ExpiryThresholdTimestamp is provided
_EXPIRY_TIMESTAMP_ALLOWED: tuple[str, ...] = (
    models.EXPIRING_CERT,
    models.EXPIRED_CERT,
)


# ===================================================================
# Private helper functions
# ===================================================================


def _validate_ca_set_name_pattern(name: str) -> str | None:
    """Check *non-empty* name against regex and three-period rule.

    Mirrors Go: validation.Match(CASetNameRegex) + validateCASetName().
    Returns the first applicable error message, or ``None`` if valid.
    """
    if not _CA_SET_NAME_REGEX.match(name):
        return _CA_SET_NAME_DESCRIPTION
    if "..." in name:
        return "cannot contain three consecutive periods (...)"
    return None


def _validate_nil_or_not_empty_with_length(
    value: str | None,
    max_len: int,
) -> str | None:
    """NilOrNotEmpty + Length(1, max_len).

    * ``None``  -> valid (nil)
    * ``""``    -> "cannot be blank"
    * len > max -> "the length must be between 1 and <max_len>"
    * otherwise -> valid
    """
    if value is None:
        return None
    if not value:
        return "cannot be blank"
    if len(value) > max_len:
        return f"the length must be between 1 and {max_len}"
    return None


def _validate_network(network: str) -> str | None:
    """Validate Network enum value.

    Mirrors Go ``Network.Validate()`` -- skips empty values (In-rule
    semantics).  Error includes the invalid value and all valid options,
    ending with a trailing period.
    """
    if not network:
        return None
    if network in _VALID_NETWORKS:
        return None
    quoted = [f"'{v}'" for v in _VALID_NETWORKS]
    options = ", ".join(quoted[:-1]) + " or " + quoted[-1]
    return f"value '{network}' is invalid. Must be one of: {options}."


def _validate_activation_network(network: str) -> str | None:
    """Validate ActivationNetwork enum value.

    Mirrors Go ``ActivationNetwork.Validate()``.  Note: **no** trailing
    period in the error message (matches Go format string exactly).
    """
    if network in _VALID_ACTIVATION_NETWORKS:
        return None
    return (
        f"value '{network}' is invalid. Must be one of: "
        f"'{_VALID_ACTIVATION_NETWORKS[0]}' or "
        f"'{_VALID_ACTIVATION_NETWORKS[1]}'"
    )


def _validate_association_type(assoc_type: str) -> str | None:
    """Validate AssociationType enum value.

    Mirrors Go ``AssociationType.Validate()`` -- skips empty values.
    Error ends with a trailing period.
    """
    if not assoc_type:
        return None
    if assoc_type in _VALID_ASSOCIATION_TYPES:
        return None
    return (
        f"value '{assoc_type}' is invalid. Must be one of: "
        f"'{_VALID_ASSOCIATION_TYPES[0]}' or "
        f"'{_VALID_ASSOCIATION_TYPES[1]}'."
    )


def _validate_certificate_request(
    cert: models.CertificateRequest,
) -> dict[str, str] | None:
    """Validate a single CertificateRequest inside a version certificate list.

    Mirrors Go ``certificateValidationRules()`` which validates:
      - CertificatePEM: Required
      - Description:    NilOrNotEmpty, Length(1, 255)

    Returns a dict of ``{FieldName: error_msg}`` (for nesting into
    ``parse_validation_errors``), or ``None`` when valid.
    """
    errors: dict[str, str] = {}
    if not cert.certificate_pem:
        errors["CertificatePEM"] = "cannot be blank"
    desc_err = _validate_nil_or_not_empty_with_length(cert.description, 255)
    if desc_err is not None:
        errors["Description"] = desc_err
    return errors if errors else None


def _validate_certificates(
    certificates: list[models.CertificateRequest] | None,
) -> str | dict[str, dict[str, str]] | None:
    """Required + Each(certificateValidationRules).

    Returns:
      - ``"cannot be blank"`` when the list is ``None`` or empty.
      - A numeric-keyed dict of per-certificate error dicts when individual
        certificates fail validation (consumed by ``parse_validation_errors``
        for indexed formatting like ``Certificates[0]: { ... }``).
      - ``None`` when all certificates are valid.
    """
    if not certificates:
        return "cannot be blank"
    cert_errors: dict[str, dict[str, str]] = {}
    for idx, cert in enumerate(certificates):
        cert_err = _validate_certificate_request(cert)
        if cert_err is not None:
            cert_errors[str(idx)] = cert_err
    return cert_errors if cert_errors else None


def _valid_certificate_status_for_expiry_threshold(
    status: str | None,
    allowed_statuses: tuple[str, ...],
) -> str | None:
    """Check that CertificateStatus is present and in the allowed set.

    Mirrors Go ``validCertificateStatusForExpiryThreshold``.
    """
    if status is None:
        return "CertificateStatus must be provided with this field"
    if status not in allowed_statuses:
        statuses_str = "[" + " ".join(allowed_statuses) + "]"
        return (
            "with this field CertificateStatus must be one of: "
            + statuses_str
        )
    return None


def _both_expiry_threshold_provided(
    expiry_threshold_in_days: int | None,
) -> str | None:
    """Check that ExpiryThresholdInDays is not set alongside a timestamp.

    Mirrors Go ``bothExpiryThresholdProvided``.
    """
    if expiry_threshold_in_days is not None:
        return (
            "ExpiryThresholdInDays cannot be used with "
            "ExpiryThresholdTimestamp"
        )
    return None


def _valid_certificate_status_for_date(
    status: str | None,
    timestamp_str: str,
) -> str | None:
    """Validate that the expiry-threshold timestamp direction matches status.

    Mirrors Go ``validCertificateStatusForDate``:
      - EXPIRED  + future timestamp -> error
      - EXPIRING + past   timestamp -> error
    """
    if status is None:
        return None
    if not timestamp_str:
        return None
    try:
        timestamp = datetime.fromisoformat(timestamp_str)
    except (ValueError, TypeError):
        return None
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    if status == models.EXPIRED_CERT and timestamp > now:
        return (
            "ExpiryThresholdTimestamp cannot be in the future "
            "for 'EXPIRED' CertificateStatus"
        )
    if status == models.EXPIRING_CERT and timestamp < now:
        return (
            "ExpiryThresholdTimestamp cannot be in the past "
            "for 'EXPIRING' CertificateStatus"
        )
    return None


# ===================================================================
# Public validation functions -- CA Set operations (from ca_set.go)
# ===================================================================


def validate_create_ca_set_request(
    req: models.CreateCASetRequest,
) -> str | None:
    """Validate CreateCASetRequest.

    Mirrors Go ``CreateCASetRequest.Validate()``:
      - CASetName:   Required, Length(3,64), Match(regex), no "..."
      - Description: NilOrNotEmpty, Length(1,255)
    """
    errors: dict[str, str | None] = {}

    name = req.ca_set_name
    if not name:
        errors["CASetName"] = "cannot be blank"
    elif len(name) < 3 or len(name) > 64:
        errors["CASetName"] = "the length must be between 3 and 64"
    else:
        errors["CASetName"] = _validate_ca_set_name_pattern(name)

    errors["Description"] = _validate_nil_or_not_empty_with_length(
        req.description, 255,
    )

    return parse_validation_errors(errors)


def validate_get_ca_set_request(
    req: models.GetCASetRequest,
) -> str | None:
    """Validate GetCASetRequest.

    Mirrors Go ``GetCASetRequest.Validate()``:
      - CASetID: Required, Length(1,0)
    """
    errors: dict[str, str | None] = {}
    errors["CASetID"] = "cannot be blank" if not req.ca_set_id else None
    return parse_validation_errors(errors)


def validate_list_ca_sets_request(
    req: models.ListCASetsRequest,
) -> str | None:
    """Validate ListCASetsRequest.

    Mirrors Go ``ListCASetsRequest.Validate()``:
      - CASetNamePrefix: Length(0,64), Match(regex), no "..."
      - ActivatedOn:     Network.Validate()
    """
    errors: dict[str, str | None] = {}

    prefix = req.ca_set_name_prefix
    if prefix:
        if len(prefix) > 64:
            errors["CASetNamePrefix"] = (
                "the length must be no more than 64"
            )
        else:
            errors["CASetNamePrefix"] = _validate_ca_set_name_pattern(
                prefix,
            )
    else:
        errors["CASetNamePrefix"] = None

    errors["ActivatedOn"] = _validate_network(req.activated_on)

    return parse_validation_errors(errors)


def validate_delete_ca_set_request(
    req: models.DeleteCASetRequest,
) -> str | None:
    """Validate DeleteCASetRequest.

    Mirrors Go ``DeleteCASetRequest.Validate()``:
      - CASetID: Required, Length(1,0)
    """
    errors: dict[str, str | None] = {}
    errors["CASetID"] = "cannot be blank" if not req.ca_set_id else None
    return parse_validation_errors(errors)


def validate_list_ca_set_associations_request(
    req: models.ListCASetAssociationsRequest,
) -> str | None:
    """Validate ListCASetAssociationsRequest.

    Mirrors Go ``ListCASetAssociationsRequest.Validate()``:
      - CASetID:         Required, Length(1,0)
      - AssociationType: AssociationType.Validate()
    """
    errors: dict[str, str | None] = {}
    errors["CASetID"] = "cannot be blank" if not req.ca_set_id else None
    errors["AssociationType"] = _validate_association_type(
        req.association_type,
    )
    return parse_validation_errors(errors)


def validate_clone_ca_set_request(
    req: models.CloneCASetRequest,
) -> str | None:
    """Validate CloneCASetRequest.

    Mirrors Go ``CloneCASetRequest.Validate()``:
      - CloneFromSetID:  Required
      - CloneFromVersion: Min(1)   (skipped when 0)
      - NewCASetName:    Required, Length(3,64), Match(regex), no "..."
      - NewDescription:  NilOrNotEmpty, Length(1,255)
    """
    errors: dict[str, str | None] = {}

    errors["CloneFromSetID"] = (
        "cannot be blank" if not req.clone_from_set_id else None
    )

    # Min(1) skips zero values in ozzo-validation
    if req.clone_from_version != 0 and req.clone_from_version < 1:
        errors["CloneFromVersion"] = "must be no less than 1"
    else:
        errors["CloneFromVersion"] = None

    name = req.new_ca_set_name
    if not name:
        errors["NewCASetName"] = "cannot be blank"
    elif len(name) < 3 or len(name) > 64:
        errors["NewCASetName"] = "the length must be between 3 and 64"
    else:
        errors["NewCASetName"] = _validate_ca_set_name_pattern(name)

    errors["NewDescription"] = _validate_nil_or_not_empty_with_length(
        req.new_description, 255,
    )

    return parse_validation_errors(errors)


def validate_get_ca_set_deletion_status_request(
    req: models.GetCASetDeletionStatusRequest,
) -> str | None:
    """Validate GetCASetDeletionStatusRequest.

    Mirrors Go ``GetCASetDeletionStatusRequest.Validate()``:
      - CASetID: Required, Length(1,0)
    """
    errors: dict[str, str | None] = {}
    errors["CASetID"] = "cannot be blank" if not req.ca_set_id else None
    return parse_validation_errors(errors)


def validate_list_ca_set_activities_request(
    req: models.ListCASetActivitiesRequest,
) -> str | None:
    """Validate ListCASetActivitiesRequest.

    Mirrors Go ``ListCASetActivitiesRequest.Validate()``:
      - CASetID: Required, Length(1,0)
    """
    errors: dict[str, str | None] = {}
    errors["CASetID"] = "cannot be blank" if not req.ca_set_id else None
    return parse_validation_errors(errors)


# ===================================================================
# Public validation functions -- Version operations
#                                (ca_set_versions.go)
# ===================================================================


def validate_create_ca_set_version_request(
    req: models.CreateCASetVersionRequest,
) -> str | None:
    """Validate CreateCASetVersionRequest.

    Mirrors Go ``CreateCASetVersionRequest.Validate()``:
      - CASetID:      Required
      - Description:  NilOrNotEmpty, Length(1,255)  (from Body)
      - Certificates: Required, Each(certificateValidationRules)  (Body)
    """
    errors: dict[str, str | dict | None] = {}

    errors["CASetID"] = "cannot be blank" if not req.ca_set_id else None

    body = req.body
    if body is None:
        errors["Description"] = None
        errors["Certificates"] = "cannot be blank"
    else:
        errors["Description"] = _validate_nil_or_not_empty_with_length(
            body.description, 255,
        )
        errors["Certificates"] = _validate_certificates(body.certificates)

    return parse_validation_errors(errors)


def validate_list_ca_set_versions_request(
    req: models.ListCASetVersionsRequest,
) -> str | None:
    """Validate ListCASetVersionsRequest.

    Mirrors Go ``ListCASetVersionsRequest.Validate()``:
      - CASetID: Required
    """
    errors: dict[str, str | None] = {}
    errors["CASetID"] = "cannot be blank" if not req.ca_set_id else None
    return parse_validation_errors(errors)


def validate_update_ca_set_version_request(
    req: models.UpdateCASetVersionRequest,
) -> str | None:
    """Validate UpdateCASetVersionRequest.

    Mirrors Go ``UpdateCASetVersionRequest.Validate()``:
      - CASetID:      Required
      - Version:      Required
      - Description:  NilOrNotEmpty, Length(1,255)  (from Body)
      - Certificates: Required, Each(certificateValidationRules)  (Body)
    """
    errors: dict[str, str | dict | None] = {}

    errors["CASetID"] = "cannot be blank" if not req.ca_set_id else None
    errors["Version"] = (
        "cannot be blank" if req.version == 0 else None
    )

    body = req.body
    if body is None:
        errors["Description"] = None
        errors["Certificates"] = "cannot be blank"
    else:
        errors["Description"] = _validate_nil_or_not_empty_with_length(
            body.description, 255,
        )
        errors["Certificates"] = _validate_certificates(body.certificates)

    return parse_validation_errors(errors)


def validate_clone_ca_set_version_request(
    req: models.CloneCASetVersionRequest,
) -> str | None:
    """Validate CloneCASetVersionRequest.

    Mirrors Go ``CloneCASetVersionRequest.Validate()``:
      - CASetID: Required
      - Version: Required
    """
    errors: dict[str, str | None] = {}
    errors["CASetID"] = "cannot be blank" if not req.ca_set_id else None
    errors["Version"] = (
        "cannot be blank" if req.version == 0 else None
    )
    return parse_validation_errors(errors)


def validate_get_ca_set_version_request(
    req: models.GetCASetVersionRequest,
) -> str | None:
    """Validate GetCASetVersionRequest.

    Mirrors Go ``GetCASetVersionRequest.Validate()``:
      - CASetID: Required
      - Version: Required
    """
    errors: dict[str, str | None] = {}
    errors["CASetID"] = "cannot be blank" if not req.ca_set_id else None
    errors["Version"] = (
        "cannot be blank" if req.version == 0 else None
    )
    return parse_validation_errors(errors)


def validate_get_ca_set_version_certificates_request(
    req: models.GetCASetVersionCertificatesRequest,
) -> str | None:
    """Validate GetCASetVersionCertificatesRequest.

    This is the most complex validation in the package. Mirrors Go
    ``GetCASetVersionCertificatesRequest.Validate()`` with conditional
    rules for CertificateStatus, ExpiryThresholdInDays, and
    ExpiryThresholdTimestamp.
    """
    errors: dict[str, str | None] = {}

    errors["CASetID"] = "cannot be blank" if not req.ca_set_id else None
    errors["Version"] = (
        "cannot be blank" if req.version == 0 else None
    )

    # --- CertificateStatus ---
    # When(status != nil, In(7 values).Error(custom msg))
    status = req.certificate_status
    if status is not None and status not in _VALID_CERTIFICATE_STATUSES:
        quoted = [f"'{s}'" for s in _VALID_CERTIFICATE_STATUSES]
        options = ", ".join(quoted[:-1]) + ", or " + quoted[-1]
        errors["CertificateStatus"] = (
            f"value must be one of: {options}"
        )
    else:
        errors["CertificateStatus"] = None

    # --- ExpiryThresholdInDays ---
    # When(days != nil, By(validCertificateStatusForExpiryThreshold(
    #     status, [EXPIRING, EXPIRED, EXPIRING,EXPIRED])))
    days = req.expiry_threshold_in_days
    if days is not None:
        errors["ExpiryThresholdInDays"] = (
            _valid_certificate_status_for_expiry_threshold(
                status, _EXPIRY_DAYS_ALLOWED,
            )
        )
    else:
        errors["ExpiryThresholdInDays"] = None

    # --- ExpiryThresholdTimestamp ---
    # When(!timestamp.IsZero(),
    #     By(statusCheck),
    #     By(bothCheck)),
    # By(dateCheck)       <-- always runs (outside When block)
    ts = req.expiry_threshold_timestamp
    ts_err: str | None = None
    if ts:  # non-empty = non-zero in Go
        # First: check status is valid for timestamp
        ts_err = _valid_certificate_status_for_expiry_threshold(
            status, _EXPIRY_TIMESTAMP_ALLOWED,
        )
        if ts_err is None:
            # Second: check no dual-threshold
            ts_err = _both_expiry_threshold_provided(days)
    # Always: check date direction (outside When block)
    if ts_err is None:
        ts_err = _valid_certificate_status_for_date(status, ts)
    errors["ExpiryThresholdTimestamp"] = ts_err

    return parse_validation_errors(errors)


# ===================================================================
# Public validation functions -- Activation operations
#                                (ca_set_activation.go)
# ===================================================================


def validate_activate_ca_set_version_request(
    req: models.ActivateCASetVersionRequest,
) -> str | None:
    """Validate ActivateCASetVersionRequest.

    Mirrors Go ``ActivateCASetVersionRequest.Validate()``:
      - CASetID: Required
      - Version: Required
      - Network: Required, ActivationNetwork.Validate()
    """
    errors: dict[str, str | None] = {}
    errors["CASetID"] = "cannot be blank" if not req.ca_set_id else None
    errors["Version"] = (
        "cannot be blank" if req.version == 0 else None
    )
    network = req.network
    if not network:
        errors["Network"] = "cannot be blank"
    else:
        errors["Network"] = _validate_activation_network(network)
    return parse_validation_errors(errors)


def validate_deactivate_ca_set_version_request(
    req: models.ActivateCASetVersionRequest,
) -> str | None:
    """Validate DeactivateCASetVersionRequest.

    DeactivateCASetVersionRequest is an alias for
    ActivateCASetVersionRequest in the models -- identical validation.
    """
    return validate_activate_ca_set_version_request(req)


def validate_get_ca_set_version_activation_request(
    req: models.GetCASetVersionActivationRequest,
) -> str | None:
    """Validate GetCASetVersionActivationRequest.

    Mirrors Go ``GetCASetVersionActivationRequest.Validate()``:
      - CASetID:      Required
      - Version:      Required
      - ActivationID: Required
    """
    errors: dict[str, str | None] = {}
    errors["ActivationID"] = (
        "cannot be blank" if req.activation_id == 0 else None
    )
    errors["CASetID"] = "cannot be blank" if not req.ca_set_id else None
    errors["Version"] = (
        "cannot be blank" if req.version == 0 else None
    )
    return parse_validation_errors(errors)


def validate_list_ca_set_version_activations_request(
    req: models.ListCASetVersionActivationsRequest,
) -> str | None:
    """Validate ListCASetVersionActivationsRequest.

    Mirrors Go ``ListCASetVersionActivationsRequest.Validate()``:
      - CASetID: Required
      - Version: Required
    """
    errors: dict[str, str | None] = {}
    errors["CASetID"] = "cannot be blank" if not req.ca_set_id else None
    errors["Version"] = (
        "cannot be blank" if req.version == 0 else None
    )
    return parse_validation_errors(errors)


def validate_list_ca_set_activations_request(
    req: models.ListCASetActivationsRequest,
) -> str | None:
    """Validate ListCASetActivationsRequest.

    Mirrors Go ``ListCASetActivationsRequest.Validate()``:
      - CASetID: Required
    """
    errors: dict[str, str | None] = {}
    errors["CASetID"] = "cannot be blank" if not req.ca_set_id else None
    return parse_validation_errors(errors)


# ===================================================================
# Public validation functions -- Certificate operations
#                                (certificate.go)
# ===================================================================


def validate_validate_certificates_request(
    req: models.ValidateCertificatesRequest,
) -> str | None:
    """Validate ValidateCertificatesRequest.

    Mirrors Go ``ValidateCertificatesRequest.Validate()`` which only
    checks ``Certificates: Required`` -- no per-item validation.
    """
    errors: dict[str, str | None] = {}
    errors["Certificates"] = (
        "cannot be blank" if not req.certificates else None
    )
    return parse_validation_errors(errors)


def validate_validate_certificate(
    cert: models.ValidateCertificate,
) -> str | None:
    """Validate a single ValidateCertificate.

    Mirrors Go ``ValidateCertificate.Validate()`` which uses
    ``validation.Errors{...}.Filter()`` -- same as parse_validation_errors
    with the error dict.
    """
    errors: dict[str, str | None] = {}
    errors["CertificatePEM"] = (
        "cannot be blank" if not cert.certificate_pem else None
    )
    return parse_validation_errors(errors)
