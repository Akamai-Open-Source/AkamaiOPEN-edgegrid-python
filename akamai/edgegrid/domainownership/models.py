# pylint: disable=too-many-instance-attributes
"""Request and response model classes for Domain Ownership API."""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Type aliases — in Python these are simply str aliases.
# ---------------------------------------------------------------------------
ValidationScope = str
ValidationMethod = str

# ---------------------------------------------------------------------------
# Constants matching Go v12 values exactly.
# ---------------------------------------------------------------------------
VALIDATION_SCOPE_HOST: str = "HOST"
VALIDATION_SCOPE_DOMAIN: str = "DOMAIN"
VALIDATION_SCOPE_WILDCARD: str = "WILDCARD"

VALIDATION_METHOD_DNS_CNAME: str = "DNS_CNAME"
VALIDATION_METHOD_DNS_TXT: str = "DNS_TXT"
VALIDATION_METHOD_HTTP: str = "HTTP"


# ---------------------------------------------------------------------------
# Primitive / helper model classes (leaf-level, no forward references).
# ---------------------------------------------------------------------------

@dataclass
class CnameRecord:
    """Holds the CNAME record details.

    JSON field mapping:
        name   -> "name"
        target -> "target"
    """

    name: str = ""
    target: str = ""


@dataclass
class TXTRecord:
    """Holds the TXT record details.

    JSON field mapping:
        name  -> "name"
        value -> "value"
    """

    name: str = ""
    value: str = ""


@dataclass
class HTTPFile:
    """Holds the details for HTTP file validation.

    JSON field mapping:
        path         -> "path"
        content      -> "content"
        content_type -> "contentType"
    """

    path: str = ""
    content: str = ""
    content_type: str = ""


@dataclass
class HTTPRedirect:
    """Holds the details for HTTP redirect validation.

    JSON field mapping:
        from_url -> "from"   (NOTE: 'from' is a Python reserved keyword)
        to       -> "to"
    """

    from_url: str = ""
    to: str = ""


@dataclass
class ValidationChallenge:
    """Contains the validation challenge details for a domain.

    JSON field mapping:
        cname_record    -> "cnameRecord"
        txt_record      -> "txtRecord"
        http_file       -> "httpFile"
        http_redirect   -> "httpRedirect"
        expiration_date -> "expirationDate"
    """

    cname_record: CnameRecord = field(default_factory=CnameRecord)
    txt_record: TXTRecord = field(default_factory=TXTRecord)
    http_file: HTTPFile | None = None
    http_redirect: HTTPRedirect | None = None
    expiration_date: str = ""


@dataclass
class Domain:
    """Represents a domain used in add, validate, and search domain requests.

    JSON field mapping:
        domain_name      -> "domainName"
        validation_scope -> "validationScope"
    """

    domain_name: str = ""
    validation_scope: str = ""


@dataclass
class Metadata:
    """Metadata section of a paginated API response.

    JSON field mapping:
        has_next     -> "hasNext"
        has_previous -> "hasPrevious"
        page         -> "page"
        page_size    -> "pageSize"
        total_items  -> "totalItems"
    """

    has_next: bool = False
    has_previous: bool = False
    page: int = 0
    page_size: int = 0
    total_items: int = 0


@dataclass
class Link:
    """Data to navigate between pages.

    JSON field mapping:
        href -> "href"
        rel  -> "rel"
    """

    href: str = ""
    rel: str = ""


@dataclass
class DomainStatusHistory:
    """Event in the history of domain status changes.

    JSON field mapping:
        domain_status -> "domainStatus"
        modified_date -> "modifiedDate"
        modified_user -> "modifiedUser"
        message       -> "message"
    """

    domain_status: str = ""
    modified_date: str = ""
    modified_user: str = ""
    message: str | None = None


# ---------------------------------------------------------------------------
# Request / Response model classes for domain operations.
# ---------------------------------------------------------------------------

@dataclass
class AddDomainsRequest:
    """Request structure for AddDomains.

    JSON field mapping:
        domains -> "domains"
    """

    domains: list[Domain] = field(default_factory=list)


@dataclass
class AddDomainError:
    """Error encountered while adding a domain.

    JSON field mapping:
        detail           -> "detail"
        domain_name      -> "domainName"
        title            -> "title"
        type             -> "type"
        validation_scope -> "validationScope"
    """

    detail: str = ""
    domain_name: str = ""
    title: str = ""
    type: str = ""
    validation_scope: str = ""


@dataclass
class AddDomainSuccess:
    """Successful addition of a domain.

    JSON field mapping:
        account_id               -> "accountId"
        domain_name              -> "domainName"
        domain_status            -> "domainStatus"
        validation_scope         -> "validationScope"
        validation_method        -> "validationMethod"
        validation_requested_by  -> "validationRequestedBy"
        validation_requested_date -> "validationRequestedDate"
        validation_completed_date -> "validationCompletedDate"
        validation_challenge     -> "validationChallenge"
    """

    account_id: str = ""
    domain_name: str = ""
    domain_status: str = ""
    validation_scope: str = ""
    validation_method: str | None = None
    validation_requested_by: str = ""
    validation_requested_date: str = ""
    validation_completed_date: str | None = None
    validation_challenge: ValidationChallenge = field(
        default_factory=ValidationChallenge
    )


@dataclass
class AddDomainsResponse:
    """Response structure for AddDomains.

    JSON field mapping:
        errors    -> "errors"
        successes -> "successes"
    """

    errors: list[AddDomainError] = field(default_factory=list)
    successes: list[AddDomainSuccess] = field(default_factory=list)


@dataclass
class DeleteDomainRequest:
    """Request structure for DeleteDomain.  Type alias of Domain.

    JSON field mapping:
        domain_name      -> "domainName"
        validation_scope -> "validationScope"
    """

    domain_name: str = ""
    validation_scope: str = ""


@dataclass
class DeleteDomainsRequest:
    """Request structure for DeleteDomains.

    JSON field mapping:
        domains -> "domains"
    """

    domains: list[Domain] = field(default_factory=list)


@dataclass
class ListDomainsRequest:
    """Request parameters for listing domains.

    JSON field mapping:
        paginate  -> (query parameter)
        page      -> (query parameter)
        page_size -> (query parameter "pageSize")
    """

    paginate: bool | None = None
    page: int = 0
    page_size: int = 0


@dataclass
class DomainItem:
    """Single domain in the list response.

    JSON field mapping:
        account_id               -> "accountId"
        domain_name              -> "domainName"
        domain_status            -> "domainStatus"
        validation_challenge     -> "validationChallenge"
        validation_completed_date -> "validationCompletedDate"
        validation_method        -> "validationMethod"
        validation_requested_by  -> "validationRequestedBy"
        validation_requested_date -> "validationRequestedDate"
        validation_scope         -> "validationScope"
    """

    account_id: str = ""
    domain_name: str = ""
    domain_status: str = ""
    validation_challenge: ValidationChallenge | None = None
    validation_completed_date: str | None = None
    validation_method: str | None = None
    validation_requested_by: str = ""
    validation_requested_date: str = ""
    validation_scope: str = ""


@dataclass
class ListDomainsResponse:
    """Response from listing domains.

    JSON field mapping:
        domains  -> "domains"
        metadata -> "metadata"
        links    -> "links"
    """

    domains: list[DomainItem] = field(default_factory=list)
    metadata: Metadata = field(default_factory=Metadata)
    links: list[Link] = field(default_factory=list)


@dataclass
class GetDomainRequest:
    """Request parameters for getting a specific domain.

    Fields are passed as path/query parameters (no JSON tags in Go).
    """

    domain_name: str = ""
    validation_scope: str = ""
    include_domain_status_history: bool = False


@dataclass
class GetDomainResponse:
    """Response from getting a specific domain.

    JSON field mapping:
        account_id               -> "accountId"
        domain_name              -> "domainName"
        domain_status            -> "domainStatus"
        domain_status_history    -> "domainStatusHistory"
        validation_challenge     -> "validationChallenge"
        validation_completed_date -> "validationCompletedDate"
        validation_method        -> "validationMethod"
        validation_requested_by  -> "validationRequestedBy"
        validation_requested_date -> "validationRequestedDate"
        validation_scope         -> "validationScope"
    """

    account_id: str = ""
    domain_name: str = ""
    domain_status: str = ""
    domain_status_history: list[DomainStatusHistory] = field(
        default_factory=list
    )
    validation_challenge: ValidationChallenge | None = None
    validation_completed_date: str | None = None
    validation_method: str | None = None
    validation_requested_by: str = ""
    validation_requested_date: str = ""
    validation_scope: str = ""


@dataclass
class SearchDomainsBody:
    """Body of the search domains request.

    JSON field mapping:
        domains -> "domains"
    """

    domains: list[Domain] = field(default_factory=list)


@dataclass
class SearchDomainsRequest:
    """Request parameters for searching domains.

    Fields:
        include_all -> query parameter "includeAll"
        body        -> JSON request body (SearchDomainsBody)
    """

    include_all: bool = False
    body: SearchDomainsBody = field(default_factory=SearchDomainsBody)


@dataclass
class SearchDomainItem:
    """Single domain in the search response.

    JSON field mapping:
        domain_name              -> "domainName"
        domain_status            -> "domainStatus"
        validation_scope         -> "validationScope"
        validation_level         -> "validationLevel"
        account_id               -> "accountId"
        validation_method        -> "validationMethod"
        validation_requested_by  -> "validationRequestedBy"
        validation_requested_date -> "validationRequestedDate"
        validation_completed_date -> "validationCompletedDate"
        validation_challenge     -> "validationChallenge"
    """

    domain_name: str = ""
    domain_status: str = ""
    validation_scope: str = ""
    validation_level: str = ""
    account_id: str | None = None
    validation_method: str | None = None
    validation_requested_by: str | None = None
    validation_requested_date: str | None = None
    validation_completed_date: str | None = None
    validation_challenge: ValidationChallenge | None = None


@dataclass
class SearchDomainsResponse:
    """Response from searching domains.

    JSON field mapping:
        domains -> "domains"
    """

    domains: list[SearchDomainItem] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Request / Response model classes for validation operations.
# ---------------------------------------------------------------------------

@dataclass
class ValidateDomain:
    """Structure for validating a domain.

    JSON field mapping:
        domain_name       -> "domainName"
        validation_method -> "validationMethod"
        validation_scope  -> "validationScope"
    """

    domain_name: str = ""
    validation_method: str = ""
    validation_scope: str = ""


@dataclass
class ValidateDomainResponse:
    """Response structure for Validate and Invalidate Domain.

    JSON field mapping:
        domain_name      -> "domainName"
        domain_status    -> "domainStatus"
        validation_scope -> "validationScope"
    """

    domain_name: str = ""
    domain_status: str = ""
    validation_scope: str = ""


@dataclass
class ValidateDomainsRequest:
    """Request structure for ValidateDomains.

    JSON field mapping:
        domains -> "domains"
    """

    domains: list[ValidateDomain] = field(default_factory=list)


@dataclass
class ValidateDomainsResponse:
    """Response structure for ValidateDomains.

    JSON field mapping:
        domains -> "domains"
    """

    domains: list[ValidateDomainResponse] = field(default_factory=list)


@dataclass
class InvalidateDomainRequest:
    """Request structure for InvalidateDomain.  Type alias of Domain.

    JSON field mapping:
        domain_name      -> "domainName"
        validation_scope -> "validationScope"
    """

    domain_name: str = ""
    validation_scope: str = ""


@dataclass
class InvalidateDomainResponse:
    """Response structure for InvalidateDomain.

    JSON field mapping:
        domain_name      -> "domainName"
        domain_status    -> "domainStatus"
        validation_scope -> "validationScope"
    """

    domain_name: str = ""
    domain_status: str = ""
    validation_scope: str = ""


@dataclass
class InvalidateDomainsRequest:
    """Request structure for InvalidateDomains.

    JSON field mapping:
        domains -> "domains"
    """

    domains: list[Domain] = field(default_factory=list)


@dataclass
class InvalidateDomainsResponse:
    """Response structure for InvalidateDomains.

    JSON field mapping:
        domains -> "domains"
    """

    domains: list[InvalidateDomainResponse] = field(default_factory=list)
