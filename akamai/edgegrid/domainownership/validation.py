"""Request validation functions for Domain Ownership API.

Provides validation for all domain ownership request types, mirroring the Go v12
``Validate()`` methods defined in ``pkg/domainownership/domains.go`` and
``pkg/domainownership/validations.go``.

Each public function accepts a request dataclass and returns a formatted error
string (via :func:`~akamai.edgegrid.validation.parse_validation_errors`) when
validation fails, or ``None`` when the request is valid.  The formatted error
string does **not** include the operation prefix (e.g. ``"add domains:"``) or
the ``"struct validation:"`` label — callers (the client layer) are responsible
for wrapping the result with the appropriate sentinel‑error context.

Private helper functions perform reusable field‑level checks:
- ``_domain_name_validation`` — mirrors Go ``domainNameValidation``
- ``_scope_validation`` — mirrors Go ``scopeValidation``
- ``_validate_validation_method`` — mirrors Go ``validateValidationMethod``
- ``_validate_domain`` — mirrors Go ``Domain.Validate()``
- ``_validate_validate_domain`` — mirrors Go ``ValidateDomain.Validate()``
- ``_validate_search_body`` — mirrors Go ``SearchDomainsBody.Validate()``
"""

from akamai.edgegrid.domainownership import models
from akamai.edgegrid.domainownership.errors import ERR_DOMAIN_NAME_VALIDATION_HINT
from akamai.edgegrid.validation import parse_validation_errors


# ---------------------------------------------------------------------------
# Private helper — domain name validation
# Mirrors Go domainNameValidation (domains.go lines 391-406)
# ---------------------------------------------------------------------------

def _domain_name_validation(domain_name: str) -> str | None:
    """Validate a single domain name string.

    Checks:
    1. Must not be empty.
    2. Must not exceed 200 characters.
    3. Must not begin with ``*``.
    4. Must not begin or end with a space.

    Args:
        domain_name: The domain name to validate.

    Returns:
        An error message string if invalid, or ``None`` if valid.
    """
    if not domain_name:
        return "cannot be blank"
    if len(domain_name) > 200:
        return f"domain '{domain_name}': cannot exceed 200 characters"
    if domain_name.startswith("*"):
        return f"domain '{domain_name}': invalid name format"
    if domain_name.startswith(" ") or domain_name.endswith(" "):
        return f"domain '{domain_name}': invalid name format"
    return None


# ---------------------------------------------------------------------------
# Private helper — validation scope validation
# Mirrors Go scopeValidation (domains.go lines 461-464)
# ---------------------------------------------------------------------------

def _scope_validation(scope: str) -> str | None:
    """Validate a validation scope value.

    Must be one of ``"HOST"``, ``"DOMAIN"``, or ``"WILDCARD"``.

    Args:
        scope: The validation scope to check.

    Returns:
        An error message string if invalid, or ``None`` if valid.
    """
    if not scope:
        return "cannot be blank"
    valid_scopes = ("HOST", "DOMAIN", "WILDCARD")
    if scope not in valid_scopes:
        return (
            f"value '{scope}' is invalid. "
            "Must be one of: 'HOST', 'DOMAIN' or 'WILDCARD'"
        )
    return None


# ---------------------------------------------------------------------------
# Private helper — validation method validation
# Mirrors Go validateValidationMethod (domains.go lines 466-469)
# ---------------------------------------------------------------------------

def _validate_validation_method(method: str) -> str | None:
    """Validate a validation method value.

    Must be one of ``"DNS_CNAME"``, ``"DNS_TXT"``, or ``"HTTP"``.

    Args:
        method: The validation method to check.

    Returns:
        An error message string if invalid, or ``None`` if valid.
    """
    if not method:
        return "cannot be blank"
    valid_methods = ("DNS_CNAME", "DNS_TXT", "HTTP")
    if method not in valid_methods:
        return "value must be one of: 'DNS_CNAME', 'DNS_TXT' or 'HTTP'"
    return None


# ---------------------------------------------------------------------------
# Private helper — Domain element validation
# Mirrors Go Domain.Validate() (domains.go lines 454-459)
# ---------------------------------------------------------------------------

def _validate_domain(domain: models.Domain) -> dict | None:
    """Validate a :class:`~models.Domain` element.

    Checks ``domain_name`` and ``validation_scope`` fields.

    Args:
        domain: The domain element to validate.

    Returns:
        A dict of ``{FieldName: error_message}`` if invalid, or ``None``.
    """
    errors: dict[str, str] = {}
    dn_err = _domain_name_validation(domain.domain_name)
    if dn_err is not None:
        errors["DomainName"] = dn_err
    vs_err = _scope_validation(domain.validation_scope)
    if vs_err is not None:
        errors["ValidationScope"] = vs_err
    return errors if errors else None


# ---------------------------------------------------------------------------
# Private helper — ValidateDomain element validation
# Mirrors Go ValidateDomain.Validate() (validations.go lines 97-103)
# ---------------------------------------------------------------------------

def _validate_validate_domain(domain: models.ValidateDomain) -> dict | None:
    """Validate a :class:`~models.ValidateDomain` element.

    Checks ``domain_name``, ``validation_scope``, and ``validation_method``.

    Args:
        domain: The validate-domain element to validate.

    Returns:
        A dict of ``{FieldName: error_message}`` if invalid, or ``None``.
    """
    errors: dict[str, str] = {}
    dn_err = _domain_name_validation(domain.domain_name)
    if dn_err is not None:
        errors["DomainName"] = dn_err
    vs_err = _scope_validation(domain.validation_scope)
    if vs_err is not None:
        errors["ValidationScope"] = vs_err
    vm_err = _validate_validation_method(domain.validation_method)
    if vm_err is not None:
        errors["ValidationMethod"] = vm_err
    return errors if errors else None


# ---------------------------------------------------------------------------
# Private helper — SearchDomainsBody validation
# Mirrors Go SearchDomainsBody.Validate() (domains.go lines 447-451)
# ---------------------------------------------------------------------------

def _validate_search_body(body: models.SearchDomainsBody) -> dict | None:
    """Validate a :class:`~models.SearchDomainsBody`.

    Checks that ``domains`` is non-empty and validates each element.

    Args:
        body: The search-domains body to validate.

    Returns:
        A dict of nested errors if invalid, or ``None`` if valid.
    """
    if not body.domains:
        return {"Domains": "cannot be blank"}
    element_errors: dict[str, dict] = {}
    for idx, domain in enumerate(body.domains):
        domain_err = _validate_domain(domain)
        if domain_err is not None:
            element_errors[str(idx)] = domain_err
    if element_errors:
        return {"Domains": element_errors}
    return None


# ===================================================================
# Public validation functions — one per request type (9 total)
# ===================================================================


def validate_add_domains_request(
    req: models.AddDomainsRequest,
) -> str | None:
    """Validate :class:`~models.AddDomainsRequest` parameters.

    Mirrors Go ``AddDomainsRequest.Validate()`` (domains.go lines 372-389).
    When the error output contains ``"DomainName"``, appends the domain-name
    validation hint.

    Args:
        req: The add-domains request to validate.

    Returns:
        Formatted error string, or ``None`` if the request is valid.
    """
    if not req.domains:
        return parse_validation_errors({"Domains": "cannot be blank"})

    element_errors: dict[str, dict] = {}
    for idx, domain in enumerate(req.domains):
        domain_err = _validate_domain(domain)
        if domain_err is not None:
            element_errors[str(idx)] = domain_err

    if element_errors:
        result = parse_validation_errors({"Domains": element_errors})
        if result is not None and "DomainName" in result:
            result += f"\nHint: {ERR_DOMAIN_NAME_VALIDATION_HINT}"
        return result

    return None


def validate_list_domains_request(
    req: models.ListDomainsRequest,
) -> str | None:
    """Validate :class:`~models.ListDomainsRequest` parameters.

    Mirrors Go ``ListDomainsRequest.Validate()`` (domains.go lines 409-414).

    Validation rules (applied only when the field value is non-zero):
    - ``PageSize``: if ``Paginate`` is explicitly ``False``, must be 0;
      otherwise must be between 10 and 1000 inclusive.
    - ``Page``: if ``Paginate`` is explicitly ``False``, must be 0.

    Args:
        req: The list-domains request to validate.

    Returns:
        Formatted error string, or ``None`` if the request is valid.
    """
    errors: dict[str, str] = {}

    # PageSize validation — only when PageSize != 0
    if req.page_size != 0:
        if req.paginate is not None and not req.paginate:
            errors["PageSize"] = "must be 0 when Paginate is false"
        elif req.page_size < 10:
            errors["PageSize"] = "must be no less than 10"
        elif req.page_size > 1000:
            errors["PageSize"] = "must be no greater than 1000"

    # Page validation — only when Page != 0
    if req.page != 0:
        if req.paginate is not None and not req.paginate:
            errors["Page"] = "must be 0 when Paginate is false"

    if not errors:
        return None
    return parse_validation_errors(errors)


def validate_get_domain_request(
    req: models.GetDomainRequest,
) -> str | None:
    """Validate :class:`~models.GetDomainRequest` parameters.

    Mirrors Go ``GetDomainRequest.Validate()`` (domains.go lines 417-422).

    Args:
        req: The get-domain request to validate.

    Returns:
        Formatted error string, or ``None`` if the request is valid.
    """
    errors: dict[str, str | None] = {
        "DomainName": _domain_name_validation(req.domain_name),
        "ValidationScope": _scope_validation(req.validation_scope),
    }
    return parse_validation_errors(errors)


def validate_delete_domain_request(
    req: models.DeleteDomainRequest,
) -> str | None:
    """Validate :class:`~models.DeleteDomainRequest` parameters.

    Mirrors Go ``DeleteDomainRequest.Validate()`` (domains.go lines 425-430).

    Args:
        req: The delete-domain request to validate.

    Returns:
        Formatted error string, or ``None`` if the request is valid.
    """
    errors: dict[str, str | None] = {
        "DomainName": _domain_name_validation(req.domain_name),
        "ValidationScope": _scope_validation(req.validation_scope),
    }
    return parse_validation_errors(errors)


def validate_delete_domains_request(
    req: models.DeleteDomainsRequest,
) -> str | None:
    """Validate :class:`~models.DeleteDomainsRequest` parameters.

    Mirrors Go ``DeleteDomainsRequest.Validate()`` (domains.go lines 433-437).
    Unlike :func:`validate_add_domains_request`, does **not** append a
    domain-name validation hint.

    Args:
        req: The delete-domains request to validate.

    Returns:
        Formatted error string, or ``None`` if the request is valid.
    """
    if not req.domains:
        return parse_validation_errors({"Domains": "cannot be blank"})

    element_errors: dict[str, dict] = {}
    for idx, domain in enumerate(req.domains):
        domain_err = _validate_domain(domain)
        if domain_err is not None:
            element_errors[str(idx)] = domain_err

    if element_errors:
        return parse_validation_errors({"Domains": element_errors})

    return None


def validate_search_domains_request(
    req: models.SearchDomainsRequest,
) -> str | None:
    """Validate :class:`~models.SearchDomainsRequest` parameters.

    Mirrors Go ``SearchDomainsRequest.Validate()`` (domains.go lines 440-444)
    combined with ``SearchDomainsBody.Validate()`` (domains.go lines 447-451).

    Go's ozzo-validation cascades into ``SearchDomainsBody.Validate()``
    automatically; this function replicates that behavior by delegating to
    :func:`_validate_search_body`.

    Args:
        req: The search-domains request to validate.

    Returns:
        Formatted error string, or ``None`` if the request is valid.
    """
    body_errors = _validate_search_body(req.body)
    if body_errors is not None:
        return parse_validation_errors({"Body": body_errors})
    return None


def validate_validate_domains_request(
    req: models.ValidateDomainsRequest,
) -> str | None:
    """Validate :class:`~models.ValidateDomainsRequest` parameters.

    Mirrors Go ``ValidateDomainsRequest.Validate()`` (validations.go
    lines 90-94) combined with ``ValidateDomain.Validate()`` (validations.go
    lines 97-103).

    Args:
        req: The validate-domains request to validate.

    Returns:
        Formatted error string, or ``None`` if the request is valid.
    """
    if not req.domains:
        return parse_validation_errors({"Domains": "cannot be blank"})

    element_errors: dict[str, dict] = {}
    for idx, domain in enumerate(req.domains):
        domain_err = _validate_validate_domain(domain)
        if domain_err is not None:
            element_errors[str(idx)] = domain_err

    if element_errors:
        return parse_validation_errors({"Domains": element_errors})

    return None


def validate_invalidate_domain_request(
    req: models.InvalidateDomainRequest,
) -> str | None:
    """Validate :class:`~models.InvalidateDomainRequest` parameters.

    Mirrors Go ``InvalidateDomainRequest.Validate()`` (validations.go
    lines 106-111).

    Args:
        req: The invalidate-domain request to validate.

    Returns:
        Formatted error string, or ``None`` if the request is valid.
    """
    errors: dict[str, str | None] = {
        "DomainName": _domain_name_validation(req.domain_name),
        "ValidationScope": _scope_validation(req.validation_scope),
    }
    return parse_validation_errors(errors)


def validate_invalidate_domains_request(
    req: models.InvalidateDomainsRequest,
) -> str | None:
    """Validate :class:`~models.InvalidateDomainsRequest` parameters.

    Mirrors Go ``InvalidateDomainsRequest.Validate()`` (validations.go
    lines 83-87).

    Args:
        req: The invalidate-domains request to validate.

    Returns:
        Formatted error string, or ``None`` if the request is valid.
    """
    if not req.domains:
        return parse_validation_errors({"Domains": "cannot be blank"})

    element_errors: dict[str, dict] = {}
    for idx, domain in enumerate(req.domains):
        domain_err = _validate_domain(domain)
        if domain_err is not None:
            element_errors[str(idx)] = domain_err

    if element_errors:
        return parse_validation_errors({"Domains": element_errors})

    return None
