"""Request validation functions for the HAPI service client.

Implements validation for all HAPI request types that have ``Validate()``
methods in the Go v12 SDK.  Each function mirrors the corresponding Go
validation logic field-for-field, preserving identical error messages and
field-name keys (PascalCase, matching Go struct field names).

Go reference:
    ``pkg/hapi/edgehostname.go`` lines 152-183 — four ``Validate()`` methods.
    ``pkg/edgegriderr/errors.go`` — ``ParseValidationErrors()`` formatting.
"""

from akamai.edgegrid.validation import parse_validation_errors


def validate_delete_edge_hostname_request(request) -> str | None:
    """Validate DeleteEdgeHostnameRequest fields.

    Mirrors Go ``DeleteEdgeHostnameRequest.Validate()``.
    Checks: DNSZone required, RecordName required.

    Args:
        request: DeleteEdgeHostnameRequest instance with ``dns_zone``
            and ``record_name`` attributes.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors: dict[str, str | dict | None] = {}
    if not request.dns_zone:
        errors["DNSZone"] = "cannot be blank"
    if not request.record_name:
        errors["RecordName"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_update_edge_hostname_request(request) -> str | None:
    """Validate UpdateEdgeHostnameRequest fields.

    Mirrors Go ``UpdateEdgeHostnameRequest.Validate()``.
    Checks: DNSZone required, RecordName required, Body items validated
    individually via ``validate_update_edge_hostname_request_body``.

    In Go, ``validation.Validate(r.Body)`` iterates through the slice and
    calls each element's ``Validate()`` method.  Errors are collected with
    numeric keys (the slice index) and passed to
    ``edgegriderr.ParseValidationErrors`` for formatting.

    Args:
        request: UpdateEdgeHostnameRequest instance with ``dns_zone``,
            ``record_name``, and ``body`` attributes.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors: dict[str, str | dict | None] = {}
    if not request.dns_zone:
        errors["DNSZone"] = "cannot be blank"
    if not request.record_name:
        errors["RecordName"] = "cannot be blank"

    # Validate Body items — mirrors Go validation.Validate(r.Body)
    # which calls each Body item's Validate() and collects errors
    # with the slice index as the key.
    if request.body:
        body_errors: dict[str, dict] = {}
        for i, item in enumerate(request.body):
            item_error = validate_update_edge_hostname_request_body(item)
            if item_error is not None:
                body_errors[str(i)] = item_error
        if body_errors:
            errors["Body"] = body_errors

    return parse_validation_errors(errors)


def validate_update_edge_hostname_request_body(body) -> dict | None:
    """Validate UpdateEdgeHostnameRequestBody fields.

    Mirrors Go ``UpdateEdgeHostnameRequestBody.Validate()``.
    Checks:

    - **Path**: required; must be one of ``"/ttl"`` or
      ``"/ipVersionBehavior"``.
    - **Op**: required; must be ``"replace"``.
    - **Value**: required.

    .. important::

        The Go method uses ``.Filter()`` (not ``ParseValidationErrors``),
        so this function returns the raw errors dict rather than a
        formatted string.  The caller
        (``validate_update_edge_hostname_request``) passes these nested
        dicts to ``parse_validation_errors`` for formatting.

    Args:
        body: UpdateEdgeHostnameRequestBody instance with ``path``,
            ``op``, and ``value`` attributes.

    Returns:
        Dictionary of field-name to error-message, or ``None`` if valid.
    """
    errors: dict[str, str] = {}

    # Path — mirrors Go: validation.Required +
    #   validation.In("/ttl", "/ipVersionBehavior").Error(...)
    if not body.path:
        errors["Path"] = "cannot be blank"
    elif body.path not in ("/ttl", "/ipVersionBehavior"):
        errors["Path"] = (
            f"value '{body.path}' is invalid. "
            "Must be one of: '/ttl' or '/ipVersionBehavior'"
        )

    # Op — mirrors Go: validation.Required +
    #   validation.In("replace").Error(...)
    if not body.op:
        errors["Op"] = "cannot be blank"
    elif body.op != "replace":
        errors["Op"] = (
            f"value '{body.op}' is invalid. Must use 'replace'"
        )

    # Value — mirrors Go: validation.Required
    if not body.value:
        errors["Value"] = "cannot be blank"

    if not errors:
        return None
    return errors


def validate_get_certificate_request(request) -> str | None:
    """Validate GetCertificateRequest fields.

    Mirrors Go ``GetCertificateRequest.Validate()``.
    Checks: DNSZone required, RecordName required.

    Args:
        request: GetCertificateRequest instance with ``dns_zone``
            and ``record_name`` attributes.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors: dict[str, str | dict | None] = {}
    if not request.dns_zone:
        errors["DNSZone"] = "cannot be blank"
    if not request.record_name:
        errors["RecordName"] = "cannot be blank"
    return parse_validation_errors(errors)
