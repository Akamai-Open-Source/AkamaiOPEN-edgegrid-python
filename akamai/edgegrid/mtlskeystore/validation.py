"""Request validation functions for the mTLS Key Store API.

Every Go request struct has a ``Validate()`` method; this module provides
the Python equivalents.  Each public function receives a request model
instance and returns ``str | None``:

* ``None``  — the request is valid (no validation errors).
* ``str``   — a formatted, multi-line validation error message.

Validation rules are extracted verbatim from:

* ``pkg/mtlskeystore/client_certificates.go``
* ``pkg/mtlskeystore/client_certificate_versions.go``
* ``pkg/mtlskeystore/account_ca_certificates.go``

Error messages **must** match the corresponding Go unit-test assertions
character-for-character.
"""

from akamai.edgegrid.validation import parse_validation_errors

# ---------------------------------------------------------------------------
# Valid enum value sets — used by the public validation functions
# ---------------------------------------------------------------------------

_VALID_GEOGRAPHIES = ("CORE", "RUSSIA_AND_CORE", "CHINA_AND_CORE")
_VALID_KEY_ALGORITHMS = ("RSA", "ECDSA")
_VALID_SECURE_NETWORKS = ("STANDARD_TLS", "ENHANCED_TLS")
_VALID_SIGNERS = ("AKAMAI", "THIRD_PARTY")
_VALID_CERTIFICATE_STATUSES = ("CURRENT", "EXPIRED", "PREVIOUS", "QUALIFYING")

# ---------------------------------------------------------------------------
# Private helper validators
# ---------------------------------------------------------------------------


def _validate_required_int(value: int) -> str | None:
    """Return ``'cannot be blank'`` when *value* is zero/falsy.

    Mirrors Go ``ozzo-validation``'s ``Required`` rule for integer fields
    where ``0`` is treated as the zero-value ("blank").
    """
    if not value:
        return "cannot be blank"
    return None


def _validate_required_str(value: str) -> str | None:
    """Return ``'cannot be blank'`` when *value* is empty/falsy."""
    if not value:
        return "cannot be blank"
    return None


def _validate_required_str_with_length(
    value: str, min_len: int, max_len: int
) -> str | None:
    """Validate a required string with a length constraint.

    Mirrors Go ``validation.Required, validation.Length(min, max)``.
    """
    if not value:
        return "cannot be blank"
    if 0 < max_len < len(value):
        return (
            f"the length must be between {min_len} and {max_len}"
        )
    return None


def _validate_required_list(value: list | None) -> str | None:
    """Return ``'cannot be blank'`` when *value* is ``None`` or empty."""
    if value is None or (isinstance(value, list) and len(value) == 0):
        return "cannot be blank"
    return None


def _validate_enum(value: str, allowed: tuple[str, ...]) -> str | None:
    """Validate a **required** enum field.

    Returns ``'cannot be blank'`` when *value* is empty, or an
    ``'is invalid. Must be one of: …'`` message when *value* is not in
    *allowed*.
    """
    if not value:
        return "cannot be blank"
    if value not in allowed:
        quoted = ", ".join(f"'{v}'" for v in allowed)
        return f"value '{value}' is invalid. Must be one of: {quoted}"
    return None


def _validate_optional_enum(
    value: str | None, allowed: tuple[str, ...]
) -> str | None:
    """Validate an **optional** enum field (``None`` ⇒ no error).

    Mirrors Go ``validation.By(keyAlgorithmValidate)`` where a nil pointer
    is accepted without error.
    """
    if value is None:
        return None
    if value not in allowed:
        quoted = ", ".join(f"'{v}'" for v in allowed)
        return f"value '{value}' is invalid. Must be one of: {quoted}"
    return None


# ---------------------------------------------------------------------------
# Public validation functions (8 total — one per Go Validate() method)
# ---------------------------------------------------------------------------


def validate_get_client_certificate_request(req) -> str | None:
    """Validate a :class:`GetClientCertificateRequest`.

    Mirrors Go ``GetClientCertificateRequest.Validate()``.
    """
    errors: dict[str, str | None] = {
        "CertificateID": _validate_required_int(req.certificate_id),
    }
    return parse_validation_errors(errors)


def validate_create_client_certificate_request(req) -> str | None:
    """Validate a :class:`CreateClientCertificateRequest`.

    Mirrors Go ``CreateClientCertificateRequest.Validate()``.
    """
    # PreferredCA has a conditional rule: it may only be set when
    # Signer is "AKAMAI".  Mirrors Go ``preferredCAValidate(r)``.
    preferred_ca_error: str | None = None
    if req.preferred_ca is not None:
        if req.signer != "AKAMAI":
            preferred_ca_error = (
                f"preferredCA can only be set when Signer is "
                f"'AKAMAI', but got '{req.signer}'"
            )

    errors: dict[str, str | None] = {
        "CertificateName": _validate_required_str_with_length(
            req.certificate_name, 1, 64
        ),
        "ContractID": _validate_required_str(req.contract_id),
        "Geography": _validate_enum(req.geography, _VALID_GEOGRAPHIES),
        "GroupID": _validate_required_int(req.group_id),
        "KeyAlgorithm": _validate_optional_enum(
            req.key_algorithm, _VALID_KEY_ALGORITHMS
        ),
        "NotificationEmails": _validate_required_list(
            req.notification_emails
        ),
        "PreferredCA": preferred_ca_error,
        "SecureNetwork": _validate_enum(
            req.secure_network, _VALID_SECURE_NETWORKS
        ),
        "Signer": _validate_enum(req.signer, _VALID_SIGNERS),
    }
    return parse_validation_errors(errors)


def validate_patch_client_certificate_request(req) -> str | None:
    """Validate a :class:`PatchClientCertificateRequest`.

    Mirrors Go ``PatchClientCertificateRequest.Validate()`` **and**
    ``PatchClientCertificateRequestBody.Validate()``.
    """
    errors: dict[str, str | dict | None] = {
        "CertificateID": _validate_required_int(req.certificate_id),
        "Body": _validate_patch_body(req.body),
    }
    return parse_validation_errors(errors)


def _validate_patch_body(body) -> str | dict | None:
    """Validate a :class:`PatchClientCertificateRequestBody`.

    Mirrors Go ``PatchClientCertificateRequestBody.Validate()``:

    * Both ``CertificateName`` and ``NotificationEmails`` are ``None``
      ⇒ plain-string error.
    * ``CertificateName`` is non-``None`` ⇒ validate it (may return a
      nested ``dict`` that ``parse_validation_errors`` wraps in ``{ }``.
    * Otherwise (only ``NotificationEmails`` provided) ⇒ valid.
    """
    if body.certificate_name is None and body.notification_emails is None:
        return "CertificateName or NotificationEmails must be provided"

    if body.certificate_name is not None:
        cert_name_error = _validate_patch_certificate_name(
            body.certificate_name
        )
        if cert_name_error is not None:
            return {"CertificateName": cert_name_error}

    return None


def _validate_patch_certificate_name(name: str) -> str | None:
    """Validate the ``CertificateName`` field inside a patch body.

    Mirrors Go:

    .. code-block:: go

        validation.Validate(r.CertificateName,
            validation.Required.Error("value is invalid"),
            validation.Length(1, 64).Error("value '…' is invalid. …"))
    """
    if not name:
        return "value is invalid"
    if len(name) > 64:
        return (
            f"value '{name}' is invalid. "
            f"Must be between 1 and 64 characters"
        )
    return None


def validate_rotate_client_certificate_version_request(req) -> str | None:
    """Validate a :class:`RotateClientCertificateVersionRequest`.

    Mirrors Go ``RotateClientCertificateVersionRequest.Validate()``.
    """
    errors: dict[str, str | None] = {
        "CertificateID": _validate_required_int(req.certificate_id),
    }
    return parse_validation_errors(errors)


def validate_list_client_certificate_versions_request(req) -> str | None:
    """Validate a :class:`ListClientCertificateVersionsRequest`.

    Mirrors Go ``ListClientCertificateVersionsRequest.Validate()``.
    """
    errors: dict[str, str | None] = {
        "CertificateID": _validate_required_int(req.certificate_id),
    }
    return parse_validation_errors(errors)


def validate_delete_client_certificate_version_request(req) -> str | None:
    """Validate a :class:`DeleteClientCertificateVersionRequest`.

    Mirrors Go ``DeleteClientCertificateVersionRequest.Validate()``.
    """
    errors: dict[str, str | None] = {
        "CertificateID": _validate_required_int(req.certificate_id),
        "Version": _validate_required_int(req.version),
    }
    return parse_validation_errors(errors)


def validate_upload_signed_client_certificate_request(req) -> str | None:
    """Validate a :class:`UploadSignedClientCertificateRequest`.

    Mirrors Go ``UploadSignedClientCertificateRequest.Validate()`` **and**
    ``UploadSignedClientCertificateRequestBody.Validate()``.
    """
    errors: dict[str, str | dict | None] = {
        "CertificateID": _validate_required_int(req.certificate_id),
        "Version": _validate_required_int(req.version),
        "Body": _validate_upload_body(req.body),
    }
    return parse_validation_errors(errors)


def _validate_upload_body(body) -> dict | None:
    """Validate a :class:`UploadSignedClientCertificateRequestBody`.

    Mirrors Go ``UploadSignedClientCertificateRequestBody.Validate()``:

    * ``Certificate`` is required and must be non-empty.
    * ``TrustChain`` is validated **only** when it is not ``None``
      (``validation.When(v.TrustChain != nil, validation.Required)``).
    """
    inner: dict[str, str | None] = {}

    # Certificate: required, Length(1, 0) means min=1, max=unlimited
    if not body.certificate:
        inner["Certificate"] = "cannot be blank"

    # TrustChain: validated only when not None
    if body.trust_chain is not None and not body.trust_chain:
        inner["TrustChain"] = "cannot be blank"

    if inner:
        return inner
    return None


def validate_list_account_ca_certificates_request(req) -> str | None:
    """Validate a :class:`ListAccountCACertificatesRequest`.

    Mirrors Go ``ListAccountCACertificatesRequest.Validate()`` with
    ``statusRule``.
    """
    errors: dict[str, str | None] = {
        "Status": _validate_status_list(req.status),
    }
    return parse_validation_errors(errors)


def _validate_status_list(statuses: list[str]) -> str | None:
    """Validate that every element in *statuses* is a known status value.

    Mirrors Go ``statusRule`` which iterates over the slice and returns
    an error for the **first** invalid element, using Go's default
    ``[]string`` formatting (space-separated, bracket-wrapped).
    """
    if not statuses:
        return None

    for status in statuses:
        if status not in _VALID_CERTIFICATE_STATUSES:
            # Go formats the list as "[EL1 EL2 EL3]" via %s on a
            # []string.  Reproduce exactly.
            list_repr = "[" + " ".join(statuses) + "]"
            return (
                f"list '{list_repr}' contains invalid element "
                f"'{status}'. Each element must be one of: "
                f"'CURRENT', 'EXPIRED', 'PREVIOUS', or 'QUALIFYING'"
            )
    return None
