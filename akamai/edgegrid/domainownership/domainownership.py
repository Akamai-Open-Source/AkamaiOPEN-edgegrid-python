"""Domain Ownership Manager API client implementation.

Mirrors the Go ``pkg/domainownership`` package, providing a Python client
for all nine Domain Ownership API operations: add, delete (single and bulk),
list, get, search, validate, and invalidate domains.
"""

import json
import logging
from dataclasses import asdict
from urllib.parse import quote

from akamai.edgegrid.session import Session
from akamai.edgegrid.domainownership.errors import (
    Error,
    ErrAddDomains,
    ErrDeleteDomain,
    ErrDeleteDomains,
    ErrGetDomain,
    ErrInvalidateDomain,
    ErrInvalidateDomains,
    ErrListDomains,
    ErrSearchDomains,
    ErrStructValidation,
    ErrValidateDomains,
    parse_error_response,
)
from akamai.edgegrid.domainownership.models import (
    AddDomainError,
    AddDomainSuccess,
    AddDomainsRequest,
    AddDomainsResponse,
    CnameRecord,
    DeleteDomainRequest,
    DeleteDomainsRequest,
    Domain,
    DomainItem,
    DomainStatusHistory,
    GetDomainRequest,
    GetDomainResponse,
    HTTPFile,
    HTTPRedirect,
    InvalidateDomainRequest,
    InvalidateDomainResponse,
    InvalidateDomainsRequest,
    InvalidateDomainsResponse,
    Link,
    ListDomainsRequest,
    ListDomainsResponse,
    Metadata,
    SearchDomainItem,
    SearchDomainsRequest,
    SearchDomainsResponse,
    TXTRecord,
    ValidateDomainResponse,
    ValidateDomainsRequest,
    ValidateDomainsResponse,
    ValidationChallenge,
)
from akamai.edgegrid.domainownership.validation import (
    validate_add_domains_request,
    validate_delete_domain_request,
    validate_delete_domains_request,
    validate_get_domain_request,
    validate_invalidate_domain_request,
    validate_invalidate_domains_request,
    validate_list_domains_request,
    validate_search_domains_request,
    validate_validate_domains_request,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Serialization helpers: dataclass -> JSON-compatible dict
# ---------------------------------------------------------------------------


def _domain_to_dict(domain: Domain) -> dict:
    """Serialize a Domain dataclass to a JSON-compatible dict.

    Applies camelCase key names matching Go JSON struct tags and filters
    out fields with ``None`` values (mimicking Go ``omitempty``).
    """
    raw = asdict(domain)
    return {
        "domainName": raw["domain_name"],
        "validationScope": raw["validation_scope"],
    }


def _validate_domain_to_dict(validate_domain) -> dict:
    """Serialize a ValidateDomain dataclass to a JSON-compatible dict.

    ValidateDomain has an additional ``validationMethod`` field compared
    to the plain Domain type.
    """
    raw = asdict(validate_domain)
    return {
        "domainName": raw["domain_name"],
        "validationMethod": raw["validation_method"],
        "validationScope": raw["validation_scope"],
    }


# ---------------------------------------------------------------------------
# Deserialization helpers: JSON dict -> model dataclass
# ---------------------------------------------------------------------------


def _parse_cname_record(data: dict | None) -> CnameRecord:
    """Parse a CnameRecord from a JSON dict."""
    if not data:
        return CnameRecord()
    return CnameRecord(
        name=data.get("name", ""),
        target=data.get("target", ""),
    )


def _parse_txt_record(data: dict | None) -> TXTRecord:
    """Parse a TXTRecord from a JSON dict."""
    if not data:
        return TXTRecord()
    return TXTRecord(
        name=data.get("name", ""),
        value=data.get("value", ""),
    )


def _parse_http_file(data: dict | None) -> HTTPFile | None:
    """Parse an HTTPFile from a JSON dict, or None if absent."""
    if not data:
        return None
    return HTTPFile(
        path=data.get("path", ""),
        content=data.get("content", ""),
        content_type=data.get("contentType", ""),
    )


def _parse_http_redirect(data: dict | None) -> HTTPRedirect | None:
    """Parse an HTTPRedirect from a JSON dict, or None if absent."""
    if not data:
        return None
    return HTTPRedirect(
        from_url=data.get("from", ""),
        to=data.get("to", ""),
    )


def _parse_validation_challenge(
    data: dict | None,
) -> ValidationChallenge | None:
    """Parse a ValidationChallenge from a JSON dict, or None if absent."""
    if not data:
        return None
    return ValidationChallenge(
        cname_record=_parse_cname_record(data.get("cnameRecord")),
        txt_record=_parse_txt_record(data.get("txtRecord")),
        http_file=_parse_http_file(data.get("httpFile")),
        http_redirect=_parse_http_redirect(data.get("httpRedirect")),
        expiration_date=data.get("expirationDate", ""),
    )


def _parse_add_domain_error(data: dict) -> AddDomainError:
    """Parse an AddDomainError from a JSON dict."""
    return AddDomainError(
        detail=data.get("detail", ""),
        domain_name=data.get("domainName", ""),
        title=data.get("title", ""),
        type=data.get("type", ""),
        validation_scope=data.get("validationScope", ""),
    )


def _parse_add_domain_success(data: dict) -> AddDomainSuccess:
    """Parse an AddDomainSuccess from a JSON dict."""
    return AddDomainSuccess(
        account_id=data.get("accountId", ""),
        domain_name=data.get("domainName", ""),
        domain_status=data.get("domainStatus", ""),
        validation_scope=data.get("validationScope", ""),
        validation_method=data.get("validationMethod"),
        validation_requested_by=data.get(
            "validationRequestedBy", ""
        ),
        validation_requested_date=data.get(
            "validationRequestedDate", ""
        ),
        validation_completed_date=data.get("validationCompletedDate"),
        validation_challenge=_parse_validation_challenge(
            data.get("validationChallenge")
        )
        or ValidationChallenge(),
    )


def _parse_add_domains_response(data: dict) -> AddDomainsResponse:
    """Parse an AddDomainsResponse from a JSON dict."""
    return AddDomainsResponse(
        errors=[
            _parse_add_domain_error(e)
            for e in data.get("errors", [])
        ],
        successes=[
            _parse_add_domain_success(s)
            for s in data.get("successes", [])
        ],
    )


def _parse_metadata(data: dict | None) -> Metadata:
    """Parse a Metadata from a JSON dict."""
    if not data:
        return Metadata()
    return Metadata(
        has_next=data.get("hasNext", False),
        has_previous=data.get("hasPrevious", False),
        page=data.get("page", 0),
        page_size=data.get("pageSize", 0),
        total_items=data.get("totalItems", 0),
    )


def _parse_link(data: dict) -> Link:
    """Parse a Link from a JSON dict."""
    return Link(
        href=data.get("href", ""),
        rel=data.get("rel", ""),
    )


def _parse_domain_item(data: dict) -> DomainItem:
    """Parse a DomainItem from a JSON dict."""
    return DomainItem(
        account_id=data.get("accountId", ""),
        domain_name=data.get("domainName", ""),
        domain_status=data.get("domainStatus", ""),
        validation_challenge=_parse_validation_challenge(
            data.get("validationChallenge")
        ),
        validation_completed_date=data.get("validationCompletedDate"),
        validation_method=data.get("validationMethod"),
        validation_requested_by=data.get(
            "validationRequestedBy", ""
        ),
        validation_requested_date=data.get(
            "validationRequestedDate", ""
        ),
        validation_scope=data.get("validationScope", ""),
    )


def _parse_list_domains_response(
    data: dict,
) -> ListDomainsResponse:
    """Parse a ListDomainsResponse from a JSON dict."""
    return ListDomainsResponse(
        domains=[
            _parse_domain_item(d)
            for d in data.get("domains", [])
        ],
        metadata=_parse_metadata(data.get("metadata")),
        links=[_parse_link(lnk) for lnk in data.get("links", [])],
    )


def _parse_domain_status_history(
    data: dict,
) -> DomainStatusHistory:
    """Parse a DomainStatusHistory from a JSON dict."""
    return DomainStatusHistory(
        domain_status=data.get("domainStatus", ""),
        modified_date=data.get("modifiedDate", ""),
        modified_user=data.get("modifiedUser", ""),
        message=data.get("message"),
    )


def _parse_get_domain_response(data: dict) -> GetDomainResponse:
    """Parse a GetDomainResponse from a JSON dict."""
    return GetDomainResponse(
        account_id=data.get("accountId", ""),
        domain_name=data.get("domainName", ""),
        domain_status=data.get("domainStatus", ""),
        domain_status_history=[
            _parse_domain_status_history(h)
            for h in data.get("domainStatusHistory", [])
        ],
        validation_challenge=_parse_validation_challenge(
            data.get("validationChallenge")
        ),
        validation_completed_date=data.get("validationCompletedDate"),
        validation_method=data.get("validationMethod"),
        validation_requested_by=data.get(
            "validationRequestedBy", ""
        ),
        validation_requested_date=data.get(
            "validationRequestedDate", ""
        ),
        validation_scope=data.get("validationScope", ""),
    )


def _parse_search_domain_item(data: dict) -> SearchDomainItem:
    """Parse a SearchDomainItem from a JSON dict."""
    return SearchDomainItem(
        domain_name=data.get("domainName", ""),
        domain_status=data.get("domainStatus", ""),
        validation_scope=data.get("validationScope", ""),
        validation_level=data.get("validationLevel", ""),
        account_id=data.get("accountId"),
        validation_method=data.get("validationMethod"),
        validation_requested_by=data.get("validationRequestedBy"),
        validation_requested_date=data.get(
            "validationRequestedDate"
        ),
        validation_completed_date=data.get(
            "validationCompletedDate"
        ),
        validation_challenge=_parse_validation_challenge(
            data.get("validationChallenge")
        ),
    )


def _parse_search_domains_response(
    data: dict,
) -> SearchDomainsResponse:
    """Parse a SearchDomainsResponse from a JSON dict."""
    return SearchDomainsResponse(
        domains=[
            _parse_search_domain_item(d)
            for d in data.get("domains", [])
        ],
    )


def _parse_validate_domain_response(
    data: dict,
) -> ValidateDomainResponse:
    """Parse a ValidateDomainResponse from a JSON dict."""
    return ValidateDomainResponse(
        domain_name=data.get("domainName", ""),
        domain_status=data.get("domainStatus", ""),
        validation_scope=data.get("validationScope", ""),
    )


def _parse_validate_domains_response(
    data: dict,
) -> ValidateDomainsResponse:
    """Parse a ValidateDomainsResponse from a JSON dict."""
    return ValidateDomainsResponse(
        domains=[
            _parse_validate_domain_response(d)
            for d in data.get("domains", [])
        ],
    )


def _parse_invalidate_domain_response(
    data: dict,
) -> InvalidateDomainResponse:
    """Parse an InvalidateDomainResponse from a JSON dict."""
    return InvalidateDomainResponse(
        domain_name=data.get("domainName", ""),
        domain_status=data.get("domainStatus", ""),
        validation_scope=data.get("validationScope", ""),
    )


def _parse_invalidate_domains_response(
    data: dict,
) -> InvalidateDomainsResponse:
    """Parse an InvalidateDomainsResponse from a JSON dict."""
    return InvalidateDomainsResponse(
        domains=[
            _parse_invalidate_domain_response(d)
            for d in data.get("domains", [])
        ],
    )


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class Client:
    """Domain Ownership Manager API client.

    Provides access to the Domain Ownership Manager API for domain
    validation lifecycle management.  Mirrors the Go
    ``pkg/domainownership.DomainOwnership`` interface, exposing identical
    endpoint methods with equivalent request/response semantics.

    See: https://techdocs.akamai.com/domain-validation/reference/api
    """

    def __init__(self, session: Session):
        """Create a new Domain Ownership client.

        Mirrors Go ``domainownership.Client()`` factory function.

        :param session: Authenticated Akamai API session.
        """
        self._session = session

    # ------------------------------------------------------------------ #
    # Domain operations (mirrors Go domains.go)
    # ------------------------------------------------------------------ #

    def add_domains(
        self, params: AddDomainsRequest
    ) -> AddDomainsResponse:
        """Add domains to validate.

        Expects HTTP 207 Multi-Status.

        See: https://techdocs.akamai.com/domain-validation/reference/post-domains

        :param params: Domains to add.
        :returns: Response containing successes and errors per domain.
        :raises ValueError: On validation failure or API error.
        """
        logger.debug("AddDomains")

        err = validate_add_domains_request(params)
        if err:
            raise ValueError(
                f"{ErrAddDomains}: {ErrStructValidation}:\n{err}"
            )

        path = "/domain-validation/v1/domains"
        body = json.dumps(
            {"domains": [_domain_to_dict(d) for d in params.domains]}
        )

        try:
            resp, result = self._session.post(
                path, body=body, expect_json=True
            )
        except Exception as exc:
            raise ValueError(
                f"{ErrAddDomains}: {exc}"
            ) from exc

        if resp.status_code != 207:
            api_err: Error = parse_error_response(resp)
            raise ValueError(
                f"{ErrAddDomains}: {api_err}"
            ) from api_err

        return _parse_add_domains_response(result)

    def delete_domain(self, params: DeleteDomainRequest) -> None:
        """Delete a single domain.

        Expects HTTP 204 No Content.

        See: https://techdocs.akamai.com/domain-validation/reference/delete-domain

        :param params: Domain name and validation scope.
        :raises ValueError: On validation failure or API error.
        """
        logger.debug("DeleteDomain")

        err = validate_delete_domain_request(params)
        if err:
            raise ValueError(
                f"{ErrDeleteDomain}: {ErrStructValidation}:\n{err}"
            )

        encoded_name = quote(params.domain_name, safe="")
        path = f"/domain-validation/v1/domains/{encoded_name}"
        query = {"validationScope": params.validation_scope}

        try:
            resp, _ = self._session.delete(path, params=query)
        except Exception as exc:
            raise ValueError(
                f"{ErrDeleteDomain}: {exc}"
            ) from exc

        if resp.status_code != 204:
            api_err: Error = parse_error_response(resp)
            raise ValueError(
                f"{ErrDeleteDomain}: {api_err}"
            ) from api_err

    def delete_domains(
        self, params: DeleteDomainsRequest
    ) -> None:
        """Delete multiple domains.

        Expects HTTP 204 No Content.  Sends a JSON body with a DELETE
        request.

        See: https://techdocs.akamai.com/domain-validation/reference/delete-domains

        :param params: Domains to delete.
        :raises ValueError: On validation failure or API error.
        """
        logger.debug("DeleteDomains")

        err = validate_delete_domains_request(params)
        if err:
            # NOTE: Go uses colon-space (not colon-newline) here.
            # Go ``domains.go`` line 585: ``%w: %w: %w``
            raise ValueError(
                f"{ErrDeleteDomains}: {ErrStructValidation}: {err}"
            )

        path = "/domain-validation/v1/domains"
        body = json.dumps(
            {"domains": [_domain_to_dict(d) for d in params.domains]}
        )

        try:
            resp, _ = self._session.delete(path, body=body)
        except Exception as exc:
            raise ValueError(
                f"{ErrDeleteDomains}: {exc}"
            ) from exc

        if resp.status_code != 204:
            api_err: Error = parse_error_response(resp)
            raise ValueError(
                f"{ErrDeleteDomains}: {api_err}"
            ) from api_err

    def list_domains(
        self, params: ListDomainsRequest
    ) -> ListDomainsResponse:
        """List domains.

        Expects HTTP 200 OK.  Supports optional pagination query
        parameters.

        See: https://techdocs.akamai.com/domain-validation/reference/get-domains

        :param params: Optional pagination parameters.
        :returns: Paginated list of domains.
        :raises ValueError: On validation failure or API error.
        """
        logger.debug("ListDomains")

        err = validate_list_domains_request(params)
        if err:
            raise ValueError(
                f"{ErrListDomains}: {ErrStructValidation}:\n{err}"
            )

        path = "/domain-validation/v1/domains"
        query: dict[str, str] = {}
        if params.paginate is not None:
            query["paginate"] = str(params.paginate).lower()
        if params.page != 0:
            query["page"] = str(params.page)
        if params.page_size != 0:
            query["pageSize"] = str(params.page_size)

        try:
            resp, result = self._session.get(
                path, expect_json=True, params=query
            )
        except Exception as exc:
            raise ValueError(
                f"{ErrListDomains}: {exc}"
            ) from exc

        if resp.status_code != 200:
            api_err: Error = parse_error_response(resp)
            raise ValueError(
                f"{ErrListDomains}: {api_err}"
            ) from api_err

        return _parse_list_domains_response(result)

    def get_domain(
        self, params: GetDomainRequest
    ) -> GetDomainResponse:
        """Get a specific domain.

        Expects HTTP 200 OK.  Optionally includes domain status history.

        See: https://techdocs.akamai.com/domain-validation/reference/get-domain

        :param params: Domain name, scope, and optional history flag.
        :returns: Detailed domain information.
        :raises ValueError: On validation failure or API error.
        """
        logger.debug("GetDomain")

        err = validate_get_domain_request(params)
        if err:
            raise ValueError(
                f"{ErrGetDomain}: {ErrStructValidation}:\n{err}"
            )

        encoded_name = quote(params.domain_name, safe="")
        path = f"/domain-validation/v1/domains/{encoded_name}"
        query: dict[str, str] = {
            "validationScope": params.validation_scope,
        }
        if params.include_domain_status_history:
            query["includeDomainStatusHistory"] = "true"

        try:
            resp, result = self._session.get(
                path, expect_json=True, params=query
            )
        except Exception as exc:
            raise ValueError(
                f"{ErrGetDomain}: {exc}"
            ) from exc

        if resp.status_code != 200:
            api_err: Error = parse_error_response(resp)
            raise ValueError(
                f"{ErrGetDomain}: {api_err}"
            ) from api_err

        return _parse_get_domain_response(result)

    def search_domains(
        self, params: SearchDomainsRequest
    ) -> SearchDomainsResponse:
        """Search for domains.

        Expects HTTP 200 OK.  The request body comes from
        ``params.body`` (``SearchDomainsBody``), not the full params
        object.

        See: https://techdocs.akamai.com/domain-validation/reference/post-domains-search

        :param params: Search criteria and optional include-all flag.
        :returns: Matching domains.
        :raises ValueError: On validation failure or API error.
        """
        logger.debug("SearchDomains")

        err = validate_search_domains_request(params)
        if err:
            raise ValueError(
                f"{ErrSearchDomains}: {ErrStructValidation}:\n{err}"
            )

        path = "/domain-validation/v1/domains/search"
        query: dict[str, str] = {}
        if params.include_all:
            query["includeAll"] = "true"

        # Body is params.body (SearchDomainsBody), NOT the full params.
        body = json.dumps(
            {
                "domains": [
                    _domain_to_dict(d)
                    for d in params.body.domains
                ]
            }
        )

        try:
            resp, result = self._session.post(
                path, body=body, expect_json=True, params=query
            )
        except Exception as exc:
            raise ValueError(
                f"{ErrSearchDomains}: {exc}"
            ) from exc

        if resp.status_code != 200:
            api_err: Error = parse_error_response(resp)
            raise ValueError(
                f"{ErrSearchDomains}: {api_err}"
            ) from api_err

        return _parse_search_domains_response(result)

    # ------------------------------------------------------------------ #
    # Validation operations (mirrors Go validations.go)
    # ------------------------------------------------------------------ #

    def validate_domains(
        self, params: ValidateDomainsRequest
    ) -> ValidateDomainsResponse:
        """Trigger domain validation.

        Expects HTTP 200 OK.

        See: https://techdocs.akamai.com/domain-validation/reference/post-domains-validate-now

        :param params: Domains to validate with their methods and scopes.
        :returns: Validation status per domain.
        :raises ValueError: On validation failure or API error.
        """
        logger.debug("ValidateDomains")

        err = validate_validate_domains_request(params)
        if err:
            raise ValueError(
                f"{ErrValidateDomains}: {ErrStructValidation}:\n{err}"
            )

        path = "/domain-validation/v1/domains/validate-now"
        body = json.dumps(
            {
                "domains": [
                    _validate_domain_to_dict(d)
                    for d in params.domains
                ]
            }
        )

        try:
            resp, result = self._session.post(
                path, body=body, expect_json=True
            )
        except Exception as exc:
            raise ValueError(
                f"{ErrValidateDomains}: {exc}"
            ) from exc

        if resp.status_code != 200:
            api_err: Error = parse_error_response(resp)
            raise ValueError(
                f"{ErrValidateDomains}: {api_err}"
            ) from api_err

        return _parse_validate_domains_response(result)

    def invalidate_domain(
        self, params: InvalidateDomainRequest
    ) -> InvalidateDomainResponse:
        """Invalidate a single domain.

        Expects HTTP 200 OK.  Sends a POST with no body — only query
        parameters.

        See: https://techdocs.akamai.com/domain-validation/reference/post-domains-invalidate

        :param params: Domain name and validation scope.
        :returns: Invalidation result.
        :raises ValueError: On validation failure or API error.
        """
        logger.debug("InvalidateDomain")

        err = validate_invalidate_domain_request(params)
        if err:
            raise ValueError(
                f"{ErrInvalidateDomain}: "
                f"{ErrStructValidation}:\n{err}"
            )

        encoded_name = quote(params.domain_name, safe="")
        path = (
            "/domain-validation/v1/domains/invalidate/"
            f"{encoded_name}"
        )
        query = {"validationScope": params.validation_scope}

        try:
            # POST with no body — only query parameters.
            resp, result = self._session.post(
                path, expect_json=True, params=query
            )
        except Exception as exc:
            raise ValueError(
                f"{ErrInvalidateDomain}: {exc}"
            ) from exc

        if resp.status_code != 200:
            api_err: Error = parse_error_response(resp)
            raise ValueError(
                f"{ErrInvalidateDomain}: {api_err}"
            ) from api_err

        return _parse_invalidate_domain_response(result)

    def invalidate_domains(
        self, params: InvalidateDomainsRequest
    ) -> InvalidateDomainsResponse:
        """Invalidate multiple domains.

        Expects HTTP 200 OK.

        See: https://techdocs.akamai.com/domain-validation/reference/
             post-domains-invalidate-multiple

        :param params: Domains to invalidate.
        :returns: Invalidation results per domain.
        :raises ValueError: On validation failure or API error.
        """
        logger.debug("InvalidateDomains")

        err = validate_invalidate_domains_request(params)
        if err:
            raise ValueError(
                f"{ErrInvalidateDomains}: "
                f"{ErrStructValidation}:\n{err}"
            )

        path = "/domain-validation/v1/domains/invalidate"
        body = json.dumps(
            {"domains": [_domain_to_dict(d) for d in params.domains]}
        )

        try:
            resp, result = self._session.post(
                path, body=body, expect_json=True
            )
        except Exception as exc:
            raise ValueError(
                f"{ErrInvalidateDomains}: {exc}"
            ) from exc

        if resp.status_code != 200:
            api_err: Error = parse_error_response(resp)
            raise ValueError(
                f"{ErrInvalidateDomains}: {api_err}"
            ) from api_err

        return _parse_invalidate_domains_response(result)
