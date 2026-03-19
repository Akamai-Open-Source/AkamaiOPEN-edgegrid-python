"""Request validation functions for all Cloud Certificates API operations.

Each public function mirrors the ``Validate()`` method on the corresponding Go
request struct in ``pkg/cloudcertificates/datamodel.go``.  The exact same
constraints are enforced and the exact same error message strings are produced
so that Go unit-test expectations apply 1:1 to the Python implementation.

Validation errors are raised as :class:`ValueError` with a message in the
format ``"{operation}: struct validation: {field}: {message}"``.
"""
from __future__ import annotations

import re

from akamai.edgegrid.cloudcertificates import errors
from akamai.edgegrid.cloudcertificates import models
from akamai.edgegrid.validation import parse_validation_errors


# ---------------------------------------------------------------------------
# Compiled regex patterns (module-level for reuse across validations)
# ---------------------------------------------------------------------------

_CERT_NAME_RE: re.Pattern[str] = re.compile(r"^[a-zA-Z0-9 ._\-]+$")
"""Mirrors Go ``certificateNameRegexRule`` — allowed characters for certificate
names: letters, digits, spaces, dots, underscores, and hyphens."""

_NON_WHITESPACE_RE: re.Pattern[str] = re.compile(r"\S")
"""Mirrors Go ``regexp.MustCompile(`\\S`)`` used in Subject field validation.
Checks whether the string contains at least one non-whitespace character."""

_SORT_FIELD_RE: re.Pattern[str] = re.compile(
    r"^[+-]?(certificateName|createdDate|modifiedDate|expirationDate)"
    r"(,[+-]?(certificateName|createdDate|modifiedDate|expirationDate))*$"
)
"""Mirrors Go ``sortFieldPat`` — validates the *Sort* query parameter format."""


# ---------------------------------------------------------------------------
# Private helpers — type-level validators
# ---------------------------------------------------------------------------


def _raise_validation_error(
    operation: str,
    field_errors: dict[str, str | dict | None],
) -> None:
    """Format collected *field_errors* and raise :class:`ValueError` if any.

    The resulting message matches the Go pattern produced by
    ``fmt.Errorf("%s: %w: %s", ErrOp, ErrStructValidation,
    edgegriderr.ParseValidationErrors(errs))``.

    Args:
        operation: The sentinel operation string (e.g.
            ``errors.ErrCreateCertificate``).
        field_errors: Mapping of field names to error messages (or ``None``
            for fields that passed validation).  Passed to
            :func:`parse_validation_errors` for formatting.

    Raises:
        ValueError: If at least one non-``None`` error exists.
    """
    formatted = parse_validation_errors(field_errors)
    if formatted is not None:
        raise ValueError(
            f"{operation}: {errors.ErrStructValidation}: {formatted}"
        )


def _validate_certificate_name(name: str | None) -> str | None:
    """Validate a certificate name value.

    Mirrors Go ``certificateNameLengthRule`` (``Length(0, 270)``) and
    ``certificateNameRegexRule`` (``Match(^[a-zA-Z0-9 ._-]+$)``).

    A ``None`` or empty-string value is considered valid (the field is not
    required).  Length is checked before the regex so that the first failing
    rule's message is returned.

    Args:
        name: The certificate name to validate, or ``None``.

    Returns:
        An error message string, or ``None`` if valid.
    """
    if name is None or name == "":
        return None
    if len(name) > 270:
        return "the length must be no more than 270"
    if not _CERT_NAME_RE.match(name):
        return (
            "the input can only contain digits (1-9), letters (a-z, A-Z), "
            "spaces, hyphens, periods, and underscores."
        )
    return None


def _validate_cryptographic_algorithm(value: str) -> str | None:
    """Validate a :pydata:`models.CryptographicAlgorithm` value.

    Mirrors Go ``CryptographicAlgorithm.Validate()``.  An empty string is
    treated as "not provided" and passes without error.

    Args:
        value: The key-type string to validate.

    Returns:
        An error message string, or ``None`` if valid.
    """
    if not value:
        return None
    if value not in (
        models.CryptographicAlgorithmRSA,
        models.CryptographicAlgorithmECDSA,
    ):
        return (
            f"value '{value}' is invalid. Must be either "
            f"'{models.CryptographicAlgorithmRSA}' or "
            f"'{models.CryptographicAlgorithmECDSA}'"
        )
    return None


def _validate_key_size(value: str) -> str | None:
    """Validate a :pydata:`models.KeySize` value.

    Mirrors Go ``KeySize.Validate()``.  An empty string passes without error.

    Args:
        value: The key-size string to validate.

    Returns:
        An error message string, or ``None`` if valid.
    """
    if not value:
        return None
    if value not in (models.KeySize2048, models.KeySizeP256):
        return (
            f"value '{value}' is invalid. Must be one of: "
            f"'{models.KeySize2048}', or '{models.KeySizeP256}'"
        )
    return None


def _validate_secure_network(value: str) -> str | None:
    """Validate a :pydata:`models.SecureNetwork` value.

    Mirrors Go ``SecureNetwork.Validate()``.  An empty string passes without
    error.

    Args:
        value: The secure-network string to validate.

    Returns:
        An error message string, or ``None`` if valid.
    """
    if not value:
        return None
    if value != models.SecureNetworkEnhancedTLS:
        return (
            f"value '{value}' is invalid. Must be: "
            f"'{models.SecureNetworkEnhancedTLS}'"
        )
    return None


def _validate_required_type(
    value: str,
    type_validator: object,
) -> str | None:
    """Validate a required field that also has type-level validation.

    If *value* is empty (the zero value for Go strings), returns
    ``"cannot be blank"``.  Otherwise delegates to *type_validator* for
    domain-specific checks.

    Args:
        value: The field value to validate.
        type_validator: A callable ``(str) -> str | None`` that validates
            the value when non-empty.

    Returns:
        An error message string, or ``None`` if valid.
    """
    if not value:
        return "cannot be blank"
    return type_validator(value)  # type: ignore[operator]


def _validate_subject_field(
    value: str,
    min_len: int,
    max_len: int,
) -> str | None:
    """Validate a single Subject field (length + non-whitespace check).

    Args:
        value: The field value.
        min_len: Minimum allowed length.
        max_len: Maximum allowed length.

    Returns:
        An error message string, or ``None`` if valid.
    """
    if not value:
        return None
    if min_len == max_len:
        if len(value) != min_len:
            return f"the length must be exactly {min_len}"
    elif not min_len <= len(value) <= max_len:
        return f"the length must be between {min_len} and {max_len}"
    if not _NON_WHITESPACE_RE.search(value):
        return "must be in a valid format"
    return None


def _validate_subject(subject: models.Subject | None) -> str | None:
    """Validate Subject fields and return a pre-formatted error string.

    Mirrors Go ``Subject.Validate()`` which internally calls
    ``edgegriderr.ParseValidationErrors`` and returns the result as a plain
    error — NOT a ``validation.Errors`` map.  This means the outer
    ``ParseValidationErrors`` treats the Subject value as a simple string
    and formats it as ``Subject: <inner formatted string>``.

    Validation rules per field (all skip when the field is empty):
    - **Country**: ``Length(2, 2)`` then ``Match(\\S)``
    - **Locality**: ``Length(1, 128)`` then ``Match(\\S)``
    - **Organization**: ``Length(1, 64)`` then ``Match(\\S)``
    - **State**: ``Length(1, 128)`` then ``Match(\\S)``

    Args:
        subject: The :class:`models.Subject` instance, or ``None``.

    Returns:
        A pre-formatted error string (ready to embed in the outer error
        dict), or ``None`` if all fields are valid.
    """
    if subject is None:
        return None

    field_errors: dict[str, str | dict | None] = {}

    # Country — Length(2, 2) then Match(\S)
    country_err = _validate_subject_field(subject.country, 2, 2)
    if country_err is not None:
        field_errors["Country"] = country_err

    # Locality — Length(1, 128) then Match(\S)
    locality_err = _validate_subject_field(subject.locality, 1, 128)
    if locality_err is not None:
        field_errors["Locality"] = locality_err

    # Organization — Length(1, 64) then Match(\S)
    org_err = _validate_subject_field(subject.organization, 1, 64)
    if org_err is not None:
        field_errors["Organization"] = org_err

    # State — Length(1, 128) then Match(\S)
    state_err = _validate_subject_field(subject.state, 1, 128)
    if state_err is not None:
        field_errors["State"] = state_err

    return parse_validation_errors(field_errors)


def _validate_page_size(page_size: int) -> str | None:
    """Validate a PageSize parameter (skips when zero / default).

    Mirrors Go ``Min(1).Error(…), Max(100).Error(…)`` with ozzo-validation's
    zero-value skip semantics (``0`` is the zero value for ``int``).

    Args:
        page_size: Page-size value (0 means not provided).

    Returns:
        An error message string, or ``None`` if valid.
    """
    if page_size == 0:
        return None
    if page_size < 1:
        return "must be 1 or greater"
    if page_size > 100:
        return "cannot be greater than 100"
    return None


def _validate_page(page: int) -> str | None:
    """Validate a Page parameter (skips when zero / default).

    Mirrors Go ``Min(1).Error(…)`` with ozzo-validation's zero-value skip
    semantics.

    Args:
        page: Page number value (0 means not provided).

    Returns:
        An error message string, or ``None`` if valid.
    """
    if page == 0:
        return None
    if page < 1:
        return "must be 1 or greater"
    return None


def _validate_certificate_status(statuses: list[str]) -> str | None:
    """Validate a list of certificate status filter values.

    Mirrors Go ``certificateStatusRule`` which iterates the slice and returns
    an error on the first invalid element using
    ``texts.JoinStringBased``-formatted valid values.

    Args:
        statuses: List of status strings to validate.

    Returns:
        An error message string, or ``None`` if valid.
    """
    if not statuses:
        return None
    valid = {
        models.StatusActive,
        models.StatusReadyForUse,
        models.StatusCSRReady,
    }
    for status in statuses:
        if status not in valid:
            # Go-style slice formatting: [elem1 elem2 ...]
            go_list = "[" + " ".join(statuses) + "]"
            valid_list = ", ".join(
                f"'{s}'"
                for s in [
                    models.StatusActive,
                    models.StatusReadyForUse,
                    models.StatusCSRReady,
                ]
            )
            return (
                f"list '{go_list}' contains invalid element '{status}'. "
                f"Each element must be one of: {valid_list}"
            )
    return None


def _validate_sort(sort: str) -> str | None:
    """Validate a Sort query-parameter value.

    Mirrors Go ``sortValidationRule`` — a comma-separated list of field names
    optionally prefixed by ``+`` or ``-``.  Empty string is valid (not
    provided).

    Args:
        sort: The sort parameter string.

    Returns:
        An error message string, or ``None`` if valid.
    """
    if not sort:
        return None
    if not _SORT_FIELD_RE.match(sort):
        return (
            "must be a comma-separated list of fields, optionally "
            "prefixed by + or - "
            "(e.g. +createdDate,-certificateName)"
        )
    return None


# ---------------------------------------------------------------------------
# Public validation functions (one per Cloud Certificates operation)
# ---------------------------------------------------------------------------


def validate_create_certificate(
    params: models.CreateCertificateRequest,
) -> None:
    """Validate a :class:`~models.CreateCertificateRequest`.

    Mirrors Go ``CreateCertificateRequest.Validate()``.

    Required fields: ContractID, GroupID, KeyType, KeySize, SecureNetwork,
    SANs.  CertificateName and Subject are optional but validated when
    provided.

    Args:
        params: The request to validate.

    Raises:
        ValueError: If any validation constraint is violated.
    """
    field_errors: dict[str, str | dict | None] = {}

    # Resolve body (Go struct is value-type, Python model defaults to None)
    body = (
        params.body
        if params.body is not None
        else models.CreateCertificateRequestBody()
    )

    # ContractID — Required
    if not params.contract_id:
        field_errors["ContractID"] = "cannot be blank"

    # GroupID — Required
    if not params.group_id:
        field_errors["GroupID"] = "cannot be blank"

    # CertificateName — Length(0, 270) + Match (optional, validated when
    # non-empty)
    cert_name_err = _validate_certificate_name(body.certificate_name)
    if cert_name_err is not None:
        field_errors["CertificateName"] = cert_name_err

    # KeyType — Required + CryptographicAlgorithm.Validate()
    key_type_err = _validate_required_type(
        body.key_type, _validate_cryptographic_algorithm
    )
    if key_type_err is not None:
        field_errors["KeyType"] = key_type_err

    # KeySize — Required + KeySize.Validate()
    key_size_err = _validate_required_type(
        body.key_size, _validate_key_size
    )
    if key_size_err is not None:
        field_errors["KeySize"] = key_size_err

    # SANs — Required
    if not body.sans:
        field_errors["SANs"] = "cannot be blank"

    # SecureNetwork — Required + SecureNetwork.Validate()
    sn_err = _validate_required_type(
        body.secure_network, _validate_secure_network
    )
    if sn_err is not None:
        field_errors["SecureNetwork"] = sn_err

    # Subject — Subject.Validate() (returns pre-formatted string)
    subject_err = _validate_subject(body.subject)
    if subject_err is not None:
        field_errors["Subject"] = subject_err

    _raise_validation_error(errors.ErrCreateCertificate, field_errors)


def validate_get_certificate(
    params: models.GetCertificateRequest,
) -> None:
    """Validate a :class:`~models.GetCertificateRequest`.

    Mirrors Go ``GetCertificateRequest.Validate()``.

    Args:
        params: The request to validate.

    Raises:
        ValueError: If CertificateID is blank.
    """
    field_errors: dict[str, str | dict | None] = {}
    if not params.certificate_id:
        field_errors["CertificateID"] = "cannot be blank"
    _raise_validation_error(errors.ErrGetCertificate, field_errors)


def validate_delete_certificate(
    params: models.DeleteCertificateRequest,
) -> None:
    """Validate a :class:`~models.DeleteCertificateRequest`.

    Mirrors Go ``DeleteCertificateRequest.Validate()``.

    Args:
        params: The request to validate.

    Raises:
        ValueError: If CertificateID is blank.
    """
    field_errors: dict[str, str | dict | None] = {}
    if not params.certificate_id:
        field_errors["CertificateID"] = "cannot be blank"
    _raise_validation_error(errors.ErrDeleteCertificate, field_errors)


def validate_patch_certificate(
    params: models.PatchCertificateRequest,
) -> None:
    """Validate a :class:`~models.PatchCertificateRequest`.

    Mirrors Go ``PatchCertificateRequest.Validate()``.

    CertificateID is required.  At least one of SignedCertificatePEM or
    CertificateName must be provided.  When CertificateName is not ``None``
    it is validated for length and character restrictions.

    Args:
        params: The request to validate.

    Raises:
        ValueError: If any validation constraint is violated.
    """
    field_errors: dict[str, str | dict | None] = {}

    # CertificateID — Required
    if not params.certificate_id:
        field_errors["CertificateID"] = "cannot be blank"

    # CertificateName — Length(0, 270) + Match (when not None)
    if params.certificate_name is not None:
        cert_name_err = _validate_certificate_name(params.certificate_name)
        if cert_name_err is not None:
            field_errors["CertificateName"] = cert_name_err

    # Custom rule: at least one of SignedCertificatePEM or CertificateName
    if not params.signed_certificate_pem and params.certificate_name is None:
        field_errors["required parameters"] = (
            "at least one of SignedCertificatePEM or CertificateName "
            "must be provided"
        )

    _raise_validation_error(errors.ErrPatchCertificate, field_errors)


def validate_update_certificate(
    params: models.UpdateCertificateRequest,
) -> None:
    """Validate an :class:`~models.UpdateCertificateRequest`.

    Mirrors Go ``UpdateCertificateRequest.Validate()``.

    CertificateID is always required.  SignedCertificatePEM is required
    when TrustChainPEM is provided (non-empty).  CertificateName is
    validated for length and characters when not ``None``.

    Args:
        params: The request to validate.

    Raises:
        ValueError: If any validation constraint is violated.
    """
    field_errors: dict[str, str | dict | None] = {}

    # CertificateID — Required
    if not params.certificate_id:
        field_errors["CertificateID"] = "cannot be blank"

    # CertificateName — Length(0, 270) + Match (when not None)
    if params.certificate_name is not None:
        cert_name_err = _validate_certificate_name(params.certificate_name)
        if cert_name_err is not None:
            field_errors["CertificateName"] = cert_name_err

    # SignedCertificatePEM — Required.When(TrustChainPEM != "")
    if params.trust_chain_pem and not params.signed_certificate_pem:
        field_errors["SignedCertificatePEM"] = "cannot be blank"

    _raise_validation_error(errors.ErrUpdateCertificate, field_errors)


def validate_list_certificates(
    params: models.ListCertificatesRequest,
) -> None:
    """Validate a :class:`~models.ListCertificatesRequest`.

    Mirrors Go ``ListCertificatesRequest.Validate()``.

    All fields are optional; validation only fires for non-default values.

    Args:
        params: The request to validate.

    Raises:
        ValueError: If any validation constraint is violated.
    """
    field_errors: dict[str, str | dict | None] = {}

    # CertificateStatus — certificateStatusRule (when non-empty list)
    status_err = _validate_certificate_status(params.certificate_status)
    if status_err is not None:
        field_errors["CertificateStatus"] = status_err

    # KeyType — CryptographicAlgorithm.Validate() (when non-empty)
    if params.key_type:
        key_type_err = _validate_cryptographic_algorithm(params.key_type)
        if key_type_err is not None:
            field_errors["KeyType"] = key_type_err

    # Page — Min(1) (when non-zero)
    page_err = _validate_page(params.page)
    if page_err is not None:
        field_errors["Page"] = page_err

    # PageSize — Min(1), Max(100) (when non-zero)
    page_size_err = _validate_page_size(params.page_size)
    if page_size_err is not None:
        field_errors["PageSize"] = page_size_err

    # Sort — sortValidationRule (when non-empty)
    sort_err = _validate_sort(params.sort)
    if sort_err is not None:
        field_errors["Sort"] = sort_err

    _raise_validation_error(errors.ErrListCertificates, field_errors)


def validate_list_certificate_bindings(
    params: models.ListCertificateBindingsRequest,
) -> None:
    """Validate a :class:`~models.ListCertificateBindingsRequest`.

    Mirrors Go ``ListCertificateBindingsRequest.Validate()``.

    Args:
        params: The request to validate.

    Raises:
        ValueError: If any validation constraint is violated.
    """
    field_errors: dict[str, str | dict | None] = {}

    # CertificateID — Required
    if not params.certificate_id:
        field_errors["CertificateID"] = "cannot be blank"

    # Page — Min(1) (when non-zero)
    page_err = _validate_page(params.page)
    if page_err is not None:
        field_errors["Page"] = page_err

    # PageSize — Min(1), Max(100) (when non-zero)
    page_size_err = _validate_page_size(params.page_size)
    if page_size_err is not None:
        field_errors["PageSize"] = page_size_err

    _raise_validation_error(
        errors.ErrListCertificateBindings, field_errors
    )


def validate_list_bindings(
    params: models.ListBindingsRequest,
) -> None:
    """Validate a :class:`~models.ListBindingsRequest`.

    Mirrors Go ``ListBindingsRequest.Validate()``.

    Args:
        params: The request to validate.

    Raises:
        ValueError: If any validation constraint is violated.
    """
    field_errors: dict[str, str | dict | None] = {}

    # Network — In(STAGING, PRODUCTION) (when non-empty)
    if params.network and params.network not in (
        models.NetworkStaging,
        models.NetworkProduction,
    ):
        field_errors["Network"] = (
            f"must be either '{models.NetworkStaging}' or "
            f"'{models.NetworkProduction}'"
        )

    # Page — Min(1) (when non-zero)
    page_err = _validate_page(params.page)
    if page_err is not None:
        field_errors["Page"] = page_err

    # PageSize — Min(1), Max(100) (when non-zero)
    page_size_err = _validate_page_size(params.page_size)
    if page_size_err is not None:
        field_errors["PageSize"] = page_size_err

    _raise_validation_error(errors.ErrListBindings, field_errors)
