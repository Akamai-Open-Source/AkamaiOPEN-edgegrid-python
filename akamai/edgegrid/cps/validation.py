"""Request validation functions for the CPS API client.

Each validation function mirrors a Go ``Validate()`` method from the
``AkamaiOPEN-edgegrid-golang/pkg/cps`` package.  The functions enforce the
exact same constraints using idiomatic Python and return an error message
string on failure or ``None`` on success.
"""

from akamai.edgegrid.validation import parse_validation_errors
from akamai.edgegrid.cps import errors
from akamai.edgegrid.cps import models


# ---------------------------------------------------------------------------
# Private validation helpers
# ---------------------------------------------------------------------------

def _required(value):
    """Return an error message if *value* is empty / zero / ``None``.

    Mirrors Go's ``validation.Required`` semantics:
    * ``int`` – 0 is treated as empty.
    * ``str`` – ``""`` is treated as empty.
    * Objects / pointers – ``None`` is treated as empty.
    """
    if value is None or value == "" or value == 0:
        return "cannot be blank"
    return None


def _in_values(value, allowed):
    """Return an error message if a non-empty *value* is not in *allowed*.

    Mirrors Go's ``validation.In`` semantics:  empty / ``None`` / zero values
    pass the check (use ``_required`` first to enforce presence).
    """
    if not value:
        return None
    if value not in allowed:
        return "must be a valid value"
    return None


def _format_validation_errors(errs):
    """Format an ``{field: message | None}`` dict into a single string.

    Entries whose value is ``None`` are silently dropped.  Remaining entries
    are sorted alphabetically by field name and joined with ``"; "``.
    Returns ``None`` when there are no errors.
    """
    filtered = {k: v for k, v in errs.items() if v is not None}
    if not filtered:
        return None
    return "; ".join(f"{k}: {v}" for k, v in sorted(filtered.items()))


# ---------------------------------------------------------------------------
# changes.go — GetChangeRequest, GetChangeStatusRequest, CancelChangeRequest
# ---------------------------------------------------------------------------

def validate_get_change_request(enrollment_id, change_id):
    """Validate a *GetChangeRequest*.

    Go reference: ``pkg/cps/changes.go`` – ``GetChangeRequest.Validate()``.
    """
    return _format_validation_errors({
        "EnrollmentID": _required(enrollment_id),
        "ChangeID": _required(change_id),
    })


def validate_get_change_status_request(enrollment_id, change_id):
    """Validate a *GetChangeStatusRequest*.

    Go reference: ``pkg/cps/changes.go`` – ``GetChangeStatusRequest.Validate()``.
    """
    return _format_validation_errors({
        "EnrollmentID": _required(enrollment_id),
        "ChangeID": _required(change_id),
    })


def validate_cancel_change_request(enrollment_id, change_id):
    """Validate a *CancelChangeRequest*.

    Go reference: ``pkg/cps/changes.go`` – ``CancelChangeRequest.Validate()``.
    """
    return _format_validation_errors({
        "EnrollmentID": _required(enrollment_id),
        "ChangeID": _required(change_id),
    })


# ---------------------------------------------------------------------------
# changes.go — AcknowledgementRequest, Acknowledgement, Certificate
# ---------------------------------------------------------------------------

def validate_acknowledgement_request(enrollment_id, change_id, acknowledgement):
    """Validate an *AcknowledgementRequest*.

    Go reference: ``pkg/cps/changes.go`` – ``AcknowledgementRequest.Validate()``.
    The embedded ``Acknowledgement`` struct is validated via
    :func:`validate_acknowledgement` (mirroring Go's automatic nested
    ``Validatable`` call).
    """
    errs = {
        "EnrollmentID": _required(enrollment_id),
        "ChangeID": _required(change_id),
    }
    ack_err = validate_acknowledgement(acknowledgement)
    if ack_err is not None:
        errs["Acknowledgement"] = f"({ack_err})"
    return _format_validation_errors(errs)


def validate_acknowledgement(acknowledgement):
    """Validate an *Acknowledgement* value.

    Go reference: ``pkg/cps/changes.go`` – ``Acknowledgement.Validate()``.
    The value must be non-empty and one of the two allowed constants:
    ``"acknowledge"`` or ``"deny"``.
    """
    req = _required(acknowledgement)
    if req is not None:
        return _format_validation_errors({"Acknowledgement": req})
    in_err = _in_values(
        acknowledgement,
        [errors.ACKNOWLEDGEMENT_ACKNOWLEDGE, errors.ACKNOWLEDGEMENT_DENY],
    )
    if in_err is not None:
        return _format_validation_errors({"Acknowledgement": in_err})
    return None


def validate_certificate(certificate):
    """Validate a *Certificate* value.

    Go reference: ``pkg/cps/changes.go`` – ``Certificate.Validate()``.
    """
    return _format_validation_errors({
        "Certificate": _required(certificate),
    })


# ---------------------------------------------------------------------------
# enrollments.go — EnrollmentRequestBody, CSR, NetworkConfiguration
# ---------------------------------------------------------------------------

def _validate_body_nested_fields(body, errs):
    """Validate CSR and NetworkConfiguration nested fields.

    Extracted from :func:`validate_enrollment_request_body` to keep within
    pylint's branch limit.  Updates *errs* in place.

    * CSR and NetworkConfiguration implement ``Validatable`` in Go and are
      validated recursively.
    * The ``csr.preferredTrustChain`` conditional rule is enforced here as
      well because it depends on the resolved *csr* reference.
    """
    csr = getattr(body, "csr", None)
    if csr is None:
        errs["csr"] = "cannot be blank"
    else:
        csr_err = validate_csr(csr)
        if csr_err is not None:
            errs["csr"] = f"({csr_err})"

    network_configuration = getattr(body, "network_configuration", None)
    if network_configuration is None:
        errs["networkConfiguration"] = "cannot be blank"
    else:
        nc_err = validate_network_configuration(network_configuration)
        if nc_err is not None:
            errs["networkConfiguration"] = f"({nc_err})"

    # Conditional: csr.preferredTrustChain
    if csr is not None:
        vtype = getattr(body, "validation_type", "")
        if vtype != "dv":
            preferred = getattr(csr, "preferred_trust_chain", "")
            if preferred:
                errs["csr.preferredTrustChain"] = (
                    "must be blank when 'validationType' is not 'dv'"
                )


def validate_enrollment_request_body(body):
    """Validate an *EnrollmentRequestBody*.

    Go reference: ``pkg/cps/enrollments.go`` –
    ``EnrollmentRequestBody.Validate()``.

    Required fields (8): adminContact, certificateType, csr,
    networkConfiguration, org, ra, techContact, validationType.

    Nested structs that implement ``Validatable`` in Go (CSR,
    NetworkConfiguration) are validated recursively.

    Conditional rule: when ``validationType`` is not ``"dv"`` and ``csr``
    is present, ``csr.preferredTrustChain`` must be blank.
    """
    errs = {}

    admin_contact = getattr(body, "admin_contact", None)
    if admin_contact is None:
        errs["adminContact"] = "cannot be blank"

    certificate_type = getattr(body, "certificate_type", "")
    if not certificate_type:
        errs["certificateType"] = "cannot be blank"

    # CSR, NetworkConfiguration, and csr.preferredTrustChain conditional
    _validate_body_nested_fields(body, errs)

    org = getattr(body, "org", None)
    if org is None:
        errs["org"] = "cannot be blank"

    ra = getattr(body, "ra", "")
    if not ra:
        errs["ra"] = "cannot be blank"

    tech_contact = getattr(body, "tech_contact", None)
    if tech_contact is None:
        errs["techContact"] = "cannot be blank"

    validation_type = getattr(body, "validation_type", "")
    if not validation_type:
        errs["validationType"] = "cannot be blank"

    # thirdParty: validated with no rules in Go — always nil.

    return _format_validation_errors(errs)


def validate_csr(csr):
    """Validate a *CSR* struct.

    Go reference: ``pkg/cps/enrollments.go`` – ``CSR.Validate()``.
    """
    cn = getattr(csr, "cn", "")
    return _format_validation_errors({
        "cn": _required(cn),
    })


def validate_network_configuration(config):
    """Validate a *NetworkConfiguration* struct.

    Go reference: ``pkg/cps/enrollments.go`` –
    ``NetworkConfiguration.Validate()``.

    ``ocspStapling`` must be one of the allowed values if set.  An empty
    value is acceptable (no ``Required`` rule in Go).
    """
    ocsp_stapling = getattr(config, "ocsp_stapling", "")
    return _format_validation_errors({
        "ocspStapling": _in_values(
            ocsp_stapling,
            [models.OCSP_STAPLING_ON,
             models.OCSP_STAPLING_OFF,
             models.OCSP_STAPLING_NOT_SET],
        ),
    })


# ---------------------------------------------------------------------------
# enrollments.go — List / Get / Create / Update / Remove Enrollment
# ---------------------------------------------------------------------------

def validate_list_enrollments_request(contract_id):
    """Validate a *ListEnrollmentsRequest*.

    Go reference: ``pkg/cps/enrollments.go`` –
    ``ListEnrollmentsRequest.Validate()``.
    """
    return _format_validation_errors({
        "contractId": _required(contract_id),
    })


def validate_get_enrollment_request(enrollment_id):
    """Validate a *GetEnrollmentRequest*.

    Go reference: ``pkg/cps/enrollments.go`` –
    ``GetEnrollmentRequest.Validate()``.
    """
    return _format_validation_errors({
        "enrollmentId": _required(enrollment_id),
    })


def validate_create_enrollment_request(body, contract_id):
    """Validate a *CreateEnrollmentRequest*.

    Go reference: ``pkg/cps/enrollments.go`` –
    ``CreateEnrollmentRequest.Validate()``.

    The *body* (``EnrollmentRequestBody``) must be non-``None`` and is
    validated recursively via :func:`validate_enrollment_request_body`.
    """
    errs = {}
    if body is None:
        errs["enrollment"] = "cannot be blank"
    else:
        body_err = validate_enrollment_request_body(body)
        if body_err is not None:
            errs["enrollment"] = f"({body_err})"
    if not contract_id:
        errs["contractId"] = "cannot be blank"
    return _format_validation_errors(errs)


def validate_update_enrollment_request(body, enrollment_id):
    """Validate an *UpdateEnrollmentRequest*.

    Go reference: ``pkg/cps/enrollments.go`` –
    ``UpdateEnrollmentRequest.Validate()``.
    """
    errs = {}
    if body is None:
        errs["enrollment"] = "cannot be blank"
    else:
        body_err = validate_enrollment_request_body(body)
        if body_err is not None:
            errs["enrollment"] = f"({body_err})"
    eid_err = _required(enrollment_id)
    if eid_err is not None:
        errs["enrollmentId"] = eid_err
    return _format_validation_errors(errs)


def validate_remove_enrollment_request(enrollment_id):
    """Validate a *RemoveEnrollmentRequest*.

    Go reference: ``pkg/cps/enrollments.go`` –
    ``RemoveEnrollmentRequest.Validate()``.
    """
    return _format_validation_errors({
        "enrollmentId": _required(enrollment_id),
    })


# ---------------------------------------------------------------------------
# deployments.go — List / Get Deployment
# ---------------------------------------------------------------------------

def validate_list_deployments_request(enrollment_id):
    """Validate a *ListDeploymentsRequest*.

    Go reference: ``pkg/cps/deployments.go`` –
    ``ListDeploymentsRequest.Validate()``.
    """
    return _format_validation_errors({
        "EnrollmentID": _required(enrollment_id),
    })


def validate_get_deployment_request(enrollment_id):
    """Validate a *GetDeploymentRequest*.

    Go reference: ``pkg/cps/deployments.go`` –
    ``GetDeploymentRequest.Validate()``.
    """
    return _format_validation_errors({
        "EnrollmentID": _required(enrollment_id),
    })


# ---------------------------------------------------------------------------
# deployment_schedules.go — Get / Update DeploymentSchedule
# ---------------------------------------------------------------------------

def validate_get_deployment_schedule_request(change_id, enrollment_id):
    """Validate a *GetDeploymentScheduleRequest*.

    Go reference: ``pkg/cps/deployment_schedules.go`` –
    ``GetDeploymentScheduleRequest.Validate()``.
    """
    return _format_validation_errors({
        "ChangeID": _required(change_id),
        "EnrollmentID": _required(enrollment_id),
    })


def validate_update_deployment_schedule_request(change_id, enrollment_id):
    """Validate an *UpdateDeploymentScheduleRequest*.

    Go reference: ``pkg/cps/deployment_schedules.go`` –
    ``UpdateDeploymentScheduleRequest.Validate()``.
    """
    return _format_validation_errors({
        "ChangeID": _required(change_id),
        "EnrollmentID": _required(enrollment_id),
    })


# ---------------------------------------------------------------------------
# history.go — DV / Certificate / Change History
# ---------------------------------------------------------------------------

def validate_get_dv_history_request(enrollment_id):
    """Validate a *GetDVHistoryRequest*.

    Go reference: ``pkg/cps/history.go`` –
    ``GetDVHistoryRequest.Validate()``.
    """
    return _format_validation_errors({
        "EnrollmentID": _required(enrollment_id),
    })


def validate_get_certificate_history_request(enrollment_id):
    """Validate a *GetCertificateHistoryRequest*.

    Go reference: ``pkg/cps/history.go`` –
    ``GetCertificateHistoryRequest.Validate()``.
    """
    return _format_validation_errors({
        "EnrollmentID": _required(enrollment_id),
    })


def validate_get_change_history_request(enrollment_id):
    """Validate a *GetChangeHistoryRequest*.

    Go reference: ``pkg/cps/history.go`` –
    ``GetChangeHistoryRequest.Validate()``.
    """
    return _format_validation_errors({
        "EnrollmentID": _required(enrollment_id),
    })


# ---------------------------------------------------------------------------
# third_party_csr.go — Upload / ThirdPartyCertificates / CertAndTrustChain
# ---------------------------------------------------------------------------

def validate_upload_third_party_cert_request(enrollment_id, change_id,
                                             certificates):
    """Validate an *UploadThirdPartyCertAndTrustChainRequest*.

    Go reference: ``pkg/cps/third_party_csr.go`` –
    ``UploadThirdPartyCertAndTrustChainRequest.Validate()``.

    Uses :func:`~akamai.edgegrid.validation.parse_validation_errors`
    (mirroring Go's ``edgegriderr.ParseValidationErrors``).

    Chains into :func:`validate_third_party_certificates` so that nested
    ``CertificateAndTrustChain`` entries are also validated (matching
    ozzo-validation's ``Validatable`` interface traversal).
    """
    errs = {
        "EnrollmentID": _required(enrollment_id),
        "ChangeID": _required(change_id),
        "Certificates": _required(certificates),
    }
    basic = parse_validation_errors(errs)
    if basic is not None:
        return basic
    # Chain into nested ThirdPartyCertificates / CertificateAndTrustChain
    # validation (mirrors Go's ozzo Validatable interface traversal).
    return validate_third_party_certificates(certificates)


def validate_third_party_certificates(certs):
    """Validate *ThirdPartyCertificates*.

    Go reference: ``pkg/cps/third_party_csr.go`` –
    ``ThirdPartyCertificates.Validate()``.

    In Go, ``validation.Field(&r.CertificatesAndTrustChains)`` triggers
    element-level ``Validatable`` calls for each ``CertificateAndTrustChain``.
    """
    if certs is None:
        return None
    chains = getattr(certs, "certificates_and_trust_chains", None)
    if not chains:
        return None
    for entry in chains:
        entry_err = validate_certificate_and_trust_chain(entry)
        if entry_err is not None:
            return entry_err
    return None


def validate_certificate_and_trust_chain(cert):
    """Validate a *CertificateAndTrustChain* entry.

    Go reference: ``pkg/cps/third_party_csr.go`` –
    ``CertificateAndTrustChain.Validate()``.

    ``Certificate`` must be non-empty.  ``KeyAlgorithm`` must be non-empty
    *and* one of ``"RSA"`` or ``"ECDSA"``; an invalid value produces a
    custom error message that includes the actual value.
    """
    certificate = getattr(cert, "certificate", "")
    key_algorithm = getattr(cert, "key_algorithm", "")

    errs = {
        "Certificate": _required(certificate),
    }

    req = _required(key_algorithm)
    if req is not None:
        errs["KeyAlgorithm"] = req
    elif key_algorithm not in ("RSA", "ECDSA"):
        errs["KeyAlgorithm"] = (
            f"value '{key_algorithm}' is invalid. "
            f"Must be one of: 'RSA', 'ECDSA'"
        )

    return _format_validation_errors(errs)
