"""Cloud Certificates API client for Akamai CCM.

Provides the :class:`Client` class with all eight Cloud Certificates API
endpoint methods.  Mirrors Go ``pkg/cloudcertificates`` interface exactly:

- Certificate CRUD: create, get, patch, update, delete
- Listing: list_certificates, list_certificate_bindings, list_bindings

Every method validates the request before making any HTTP call, extracts
Akamai rate-limit / resource-limit metadata from response headers, and
wraps API error responses with the corresponding sentinel constant.

Ported from Go ``pkg/cloudcertificates/cloudcertificates.go``,
``certificates.go``, and ``bindings.go``.
"""

import logging

from akamai.edgegrid.session import Session
from akamai.edgegrid.cloudcertificates import models
from akamai.edgegrid.cloudcertificates import errors
from akamai.edgegrid.cloudcertificates import validation

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# HTTP response header names — mirror Go constants in certificates.go
# ---------------------------------------------------------------------------

_HDR_RATE_LIMIT_LIMIT = "Akamai-RateLimit-Limit"
_HDR_RATE_LIMIT_REMAINING = "Akamai-RateLimit-Remaining"
_HDR_LIMIT_CERTIFICATES = "Akamai-Limit-Certificates"
_HDR_LIMIT_CERTIFICATES_REMAINING = "Akamai-Limit-Certificates-Remaining"


# ---------------------------------------------------------------------------
# Internal error wrapper
# ---------------------------------------------------------------------------


class _WrappedError(Exception):
    """Combine an operation sentinel with a service-specific API error.

    Mirrors Go ``fmt.Errorf("%w: %w", ErrXxx, c.Error(resp))``.
    The resulting ``str()`` reproduces the same format so that Python
    test assertions against error message strings are compatible with
    Go test expectations.

    Attributes:
        sentinel:  Operation sentinel string (e.g. ``errors.ErrCreateCertificate``).
        api_error: Parsed :class:`errors.Error` from the HTTP response.
    """

    def __init__(self, sentinel: str, api_error: errors.Error) -> None:
        self.sentinel = sentinel
        self.api_error = api_error
        super().__init__(f"{sentinel}: {api_error}")


# ---------------------------------------------------------------------------
# Internal helper functions
# ---------------------------------------------------------------------------


def _make_error_parser(sentinel: str):
    """Return an ``error_parser`` callback for :meth:`Session.exec`.

    When ``Session.exec`` receives an HTTP response with status >= 400 it
    delegates error handling to the callable returned here.  The callback
    parses the response body into a service-specific :class:`errors.Error`
    and wraps it with the operation *sentinel* before returning the
    exception to be raised.

    Args:
        sentinel: Operation sentinel constant (e.g. ``errors.ErrCreateCertificate``).

    Returns:
        A callable ``(response) -> Exception``.
    """

    def _parser(response) -> Exception:
        api_error = errors.Error.from_response(response)
        return _WrappedError(sentinel, api_error)

    return _parser


def _parse_int_header(response, header_name: str) -> int | None:
    """Safely parse a single integer-valued HTTP response header.

    Returns the parsed ``int`` on success.  If the header is missing,
    empty, or contains a non-numeric value, logs a warning and returns
    ``None``.  Mirrors Go ``strconv.ParseInt`` error handling.

    Args:
        response: A ``requests.Response`` (or compatible) object.
        header_name: HTTP header to read.

    Returns:
        Parsed integer or ``None`` on failure.
    """
    raw = response.headers.get(header_name, "")
    if raw:
        try:
            return int(raw)
        except ValueError:
            logger.warning(
                "cannot parse %s header: %s", header_name, raw,
            )
    return None


def _extract_rate_limit_headers(response) -> models.RateLimitsMetadata:
    """Extract Akamai rate-limit metadata from HTTP response headers.

    Mirrors Go ``extractRateLimitHeaders`` (certificates.go lines 280-298).
    Parses ``Akamai-RateLimit-Limit`` and ``Akamai-RateLimit-Remaining``
    headers.  Unparseable or missing values are logged at WARNING level
    and result in ``None`` for the corresponding field.

    Args:
        response: A ``requests.Response`` (or compatible) object.

    Returns:
        Populated :class:`models.RateLimitsMetadata`.
    """
    limit = _parse_int_header(response, _HDR_RATE_LIMIT_LIMIT)
    remaining = _parse_int_header(response, _HDR_RATE_LIMIT_REMAINING)
    return models.RateLimitsMetadata(limit=limit, remaining=remaining)


def _extract_resource_limit_headers(
    response,
) -> models.ResourceLimitsMetadata:
    """Extract Akamai certificate resource-limit metadata from headers.

    Mirrors the resource-limit header parsing in Go ``CreateCertificate``
    (certificates.go lines 199-213).  Parses ``Akamai-Limit-Certificates``
    and ``Akamai-Limit-Certificates-Remaining`` headers.  Only processes
    non-empty header values.

    Args:
        response: A ``requests.Response`` (or compatible) object.

    Returns:
        Populated :class:`models.ResourceLimitsMetadata`.
    """
    total = _parse_int_header(response, _HDR_LIMIT_CERTIFICATES)
    remaining = _parse_int_header(
        response, _HDR_LIMIT_CERTIFICATES_REMAINING,
    )
    return models.ResourceLimitsMetadata(
        certificate_limit_total=total,
        certificate_limit_remaining=remaining,
    )


def _build_patch_request_body(
    params: models.PatchCertificateRequest,
) -> list[dict]:
    """Build a JSON Patch (RFC 6902) request body for certificate patching.

    Mirrors Go ``buildPatchRequestBody`` (certificates.go lines 145-171).
    Patch operations are appended in strict order:

    1. ``signedCertificatePem``  → op ``add``     (if non-empty)
    2. ``trustChainPem``         → op ``add``     (if non-empty)
    3. ``certificateName``       → op ``replace`` (if not ``None``)

    Args:
        params: Validated patch request parameters.

    Returns:
        List of JSON Patch operation dicts.
    """
    patches: list[dict] = []

    if params.signed_certificate_pem:
        patches.append(
            {
                "op": "add",
                "path": "/signedCertificatePem",
                "value": params.signed_certificate_pem,
            }
        )

    if params.trust_chain_pem:
        patches.append(
            {
                "op": "add",
                "path": "/trustChainPem",
                "value": params.trust_chain_pem,
            }
        )

    if params.certificate_name is not None:
        patches.append(
            {
                "op": "replace",
                "path": "/certificateName",
                "value": params.certificate_name,
            }
        )

    return patches


def _build_create_body(
    body: models.CreateCertificateRequestBody,
) -> dict:
    """Build the JSON request body for certificate creation.

    Respects Go ``omitempty`` semantics: ``certificateName`` is omitted
    when empty; ``subject`` is omitted when ``None``.  Field order matches
    Go struct declaration for deterministic JSON output.

    Args:
        body: Validated request body parameters.

    Returns:
        Dict ready for JSON serialisation.
    """
    result: dict = {}

    # CertificateName — json:"certificateName,omitempty"
    if body.certificate_name:
        result["certificateName"] = body.certificate_name

    # KeyType — json:"keyType" (always included)
    result["keyType"] = body.key_type

    # KeySize — json:"keySize" (always included)
    result["keySize"] = body.key_size

    # SecureNetwork — json:"secureNetwork" (always included)
    result["secureNetwork"] = body.secure_network

    # SANs — json:"sans" (always included)
    result["sans"] = body.sans

    # Subject — json:"subject,omitempty" (pointer, omit when None)
    if body.subject is not None:
        result["subject"] = body.subject.to_dict()

    return result


def _build_list_certificates_params(
    params: models.ListCertificatesRequest,
) -> dict[str, str]:
    """Build query parameters for the list certificates endpoint.

    Mirrors Go ``ListCertificates`` query parameter construction.
    Only non-empty / non-default values are included so that the
    resulting URL contains only explicitly supplied filters.

    Args:
        params: Validated list request parameters.

    Returns:
        Dict of query parameters (string keys and values).
    """
    query: dict[str, str] = {}
    if params.contract_id:
        query["contractId"] = params.contract_id
    if params.group_id:
        query["groupId"] = params.group_id
    if params.certificate_status:
        query["certificateStatus"] = ",".join(params.certificate_status)
    if params.expiring_in_days is not None:
        query["expiringInDays"] = str(params.expiring_in_days)
    if params.domain:
        query["domain"] = params.domain
    if params.certificate_name:
        query["certificateName"] = params.certificate_name
    if params.key_type:
        query["keyType"] = params.key_type
    if params.issuer:
        query["issuer"] = params.issuer
    if params.include_certificate_materials:
        query["includeCertificateMaterials"] = str(
            params.include_certificate_materials
        ).lower()
    if params.page_size > 0:
        query["pageSize"] = str(params.page_size)
    if params.page > 0:
        query["page"] = str(params.page)
    if params.sort:
        query["sort"] = params.sort
    return query


def _build_update_body(
    params: models.UpdateCertificateRequest,
) -> dict:
    """Build the JSON request body for certificate update (PUT).

    Mirrors Go ``UpdateCertificateRequest`` JSON marshaling with tags:
    - ``CertificateID``:       ``json:"-"``         (excluded)
    - ``SignedCertificatePEM``: ``json:"...,omitempty"`` (if non-empty)
    - ``TrustChainPEM``:       ``json:"...,omitempty"`` (if non-empty)
    - ``CertificateName``:     ``json:"...,omitempty"`` (if not None)
    - ``AcknowledgeWarnings``: ``json:"-"``         (excluded)

    Args:
        params: Validated update request parameters.

    Returns:
        Dict ready for JSON serialisation.
    """
    result: dict = {}

    if params.signed_certificate_pem:
        result["signedCertificatePem"] = params.signed_certificate_pem

    if params.trust_chain_pem:
        result["trustChainPem"] = params.trust_chain_pem

    if params.certificate_name is not None:
        result["certificateName"] = params.certificate_name

    return result


# ---------------------------------------------------------------------------
# Client class — mirrors Go CloudCertificates interface
# ---------------------------------------------------------------------------


class Client:
    """Cloud Certificates API client.

    Provides methods for managing cloud certificates including CRUD
    operations, certificate bindings, and listing operations with
    pagination support.

    Mirrors Go ``pkg/cloudcertificates.CloudCertificates`` interface
    (8 methods) and the private ``cloudcertificates`` struct.

    Args:
        session: An authenticated :class:`~akamai.edgegrid.session.Session`
            wrapping ``requests.Session`` with ``EdgeGridAuth``.

    Example::

        from akamai.edgegrid.session import Session
        from akamai.edgegrid.cloudcertificates.cloudcertificates import Client
        from akamai.edgegrid.cloudcertificates.models import (
            GetCertificateRequest,
        )

        sess = Session(edgerc_path="~/.edgerc", section="default")
        client = Client(sess)
        resp = client.get_certificate(
            GetCertificateRequest(certificate_id="12345")
        )
        print(resp.certificate.certificate_name)
    """

    def __init__(self, session: Session) -> None:
        """Initialise the Cloud Certificates client.

        Mirrors Go ``Client(sess session.Session, ...Option)`` factory.

        Args:
            session: Authenticated Akamai API session.
        """
        self._session = session

    # -----------------------------------------------------------------
    # CreateCertificate — POST /ccm/v1/certificates
    # -----------------------------------------------------------------

    def create_certificate(
        self, params: models.CreateCertificateRequest
    ) -> models.CreateCertificateResponse:
        """Create a new cloud certificate.

        Mirrors Go ``CreateCertificate`` (certificates.go lines 173-218).

        ``POST /ccm/v1/certificates?contractId=...&groupId=...``

        Args:
            params: Validated request containing contract/group IDs and
                certificate body (SANs, Subject, key type/size, network).

        Returns:
            Response containing the created :class:`~models.Certificate`
            plus resource-limit and rate-limit metadata from headers.

        Raises:
            ValueError: If request validation fails.
            _WrappedError: If the API returns an error response.
        """
        validation.validate_create_certificate(params)

        body_obj = (
            params.body
            if params.body is not None
            else models.CreateCertificateRequestBody()
        )

        query_params = {
            "contractId": params.contract_id,
            "groupId": params.group_id,
        }

        body = _build_create_body(body_obj)

        response, result = self._session.exec(
            "POST",
            "/ccm/v1/certificates",
            body=body,
            expect_json=True,
            params=query_params,
            error_parser=_make_error_parser(errors.ErrCreateCertificate),
        )

        if response.status_code != 201:
            raise _WrappedError(
                errors.ErrCreateCertificate,
                errors.Error.from_response(response),
            )

        cert = models.Certificate.from_dict(result)
        resource_limits = _extract_resource_limit_headers(response)
        rate_limits = _extract_rate_limit_headers(response)

        return models.CreateCertificateResponse(
            certificate=cert,
            resource_limits_metadata=resource_limits,
            rate_limits_metadata=rate_limits,
        )

    # -----------------------------------------------------------------
    # GetCertificate — GET /ccm/v1/certificates/{certificateID}
    # -----------------------------------------------------------------

    def get_certificate(
        self, params: models.GetCertificateRequest
    ) -> models.GetCertificateResponse:
        """Retrieve a cloud certificate by ID.

        Mirrors Go ``GetCertificate`` (certificates.go lines 221-249).

        ``GET /ccm/v1/certificates/{certificateID}``

        Args:
            params: Request containing the certificate ID.

        Returns:
            Response with the :class:`~models.Certificate` and
            rate-limit metadata.

        Raises:
            ValueError: If request validation fails.
            _WrappedError: If the API returns an error response.
        """
        validation.validate_get_certificate(params)

        path = f"/ccm/v1/certificates/{params.certificate_id}"

        response, result = self._session.exec(
            "GET",
            path,
            expect_json=True,
            error_parser=_make_error_parser(errors.ErrGetCertificate),
        )

        if response.status_code != 200:
            raise _WrappedError(
                errors.ErrGetCertificate,
                errors.Error.from_response(response),
            )

        cert = models.Certificate.from_dict(result)
        rate_limits = _extract_rate_limit_headers(response)

        return models.GetCertificateResponse(
            certificate=cert,
            rate_limits_metadata=rate_limits,
        )

    # -----------------------------------------------------------------
    # PatchCertificate — PATCH /ccm/v1/certificates/{certificateID}
    # -----------------------------------------------------------------

    def patch_certificate(
        self, params: models.PatchCertificateRequest
    ) -> models.PatchCertificateResponse:
        """Partially update a certificate using JSON Patch (RFC 6902).

        Mirrors Go ``PatchCertificate`` (certificates.go lines 70-102).

        ``PATCH /ccm/v1/certificates/{certificateID}``

        Uses ``Content-Type: application/json-patch+json`` and builds a
        patch array with ``add`` operations for PEM fields and a
        ``replace`` operation for certificate name changes.

        Args:
            params: Request containing certificate ID and patch fields.

        Returns:
            Response with the updated :class:`~models.Certificate` and
            rate-limit metadata.

        Raises:
            ValueError: If request validation fails.
            _WrappedError: If the API returns an error response.
        """
        validation.validate_patch_certificate(params)

        path = f"/ccm/v1/certificates/{params.certificate_id}"
        patch_body = _build_patch_request_body(params)

        query_params: dict[str, str] | None = None
        if params.acknowledge_warnings:
            query_params = {"acknowledgeWarnings": "true"}

        response, result = self._session.exec(
            "PATCH",
            path,
            body=patch_body,
            expect_json=True,
            headers={"Content-Type": "application/json-patch+json"},
            params=query_params,
            error_parser=_make_error_parser(errors.ErrPatchCertificate),
        )

        if response.status_code != 200:
            raise _WrappedError(
                errors.ErrPatchCertificate,
                errors.Error.from_response(response),
            )

        cert = models.Certificate.from_dict(result)
        rate_limits = _extract_rate_limit_headers(response)

        return models.PatchCertificateResponse(
            certificate=cert,
            rate_limits_metadata=rate_limits,
        )

    # -----------------------------------------------------------------
    # UpdateCertificate — PUT /ccm/v1/certificates/{certificateID}
    # -----------------------------------------------------------------

    def update_certificate(
        self, params: models.UpdateCertificateRequest
    ) -> models.UpdateCertificateResponse:
        """Fully update a certificate (PUT replacement).

        Mirrors Go ``UpdateCertificate`` (certificates.go lines 104-143).

        ``PUT /ccm/v1/certificates/{certificateID}``

        Args:
            params: Request containing certificate ID and full update
                fields.

        Returns:
            Response with the updated :class:`~models.Certificate` and
            rate-limit metadata.

        Raises:
            ValueError: If request validation fails.
            _WrappedError: If the API returns an error response.
        """
        validation.validate_update_certificate(params)

        path = f"/ccm/v1/certificates/{params.certificate_id}"
        body = _build_update_body(params)

        query_params: dict[str, str] | None = None
        if params.acknowledge_warnings:
            query_params = {"acknowledgeWarnings": "true"}

        response, result = self._session.exec(
            "PUT",
            path,
            body=body,
            expect_json=True,
            params=query_params,
            error_parser=_make_error_parser(errors.ErrUpdateCertificate),
        )

        if response.status_code != 200:
            raise _WrappedError(
                errors.ErrUpdateCertificate,
                errors.Error.from_response(response),
            )

        cert = models.Certificate.from_dict(result)
        rate_limits = _extract_rate_limit_headers(response)

        return models.UpdateCertificateResponse(
            certificate=cert,
            rate_limits_metadata=rate_limits,
        )

    # -----------------------------------------------------------------
    # DeleteCertificate — DELETE /ccm/v1/certificates/{certificateID}
    # -----------------------------------------------------------------

    def delete_certificate(
        self, params: models.DeleteCertificateRequest
    ) -> models.DeleteCertificateResponse:
        """Delete a cloud certificate by ID.

        Mirrors Go ``DeleteCertificate`` (certificates.go lines 251-278).

        ``DELETE /ccm/v1/certificates/{certificateID}``

        Expects HTTP 204 No Content on success.  The response contains
        only rate-limit metadata extracted from headers.

        Args:
            params: Request containing the certificate ID.

        Returns:
            :class:`~models.RateLimitsMetadata` (aliased as
            ``DeleteCertificateResponse``) with rate-limit header values.

        Raises:
            ValueError: If request validation fails.
            _WrappedError: If the API returns an error response.
        """
        validation.validate_delete_certificate(params)

        path = f"/ccm/v1/certificates/{params.certificate_id}"

        response, _ = self._session.exec(
            "DELETE",
            path,
            error_parser=_make_error_parser(errors.ErrDeleteCertificate),
        )

        if response.status_code != 204:
            raise _WrappedError(
                errors.ErrDeleteCertificate,
                errors.Error.from_response(response),
            )

        rate_limits = _extract_rate_limit_headers(response)

        # DeleteCertificateResponse is a type alias for RateLimitsMetadata.
        return models.DeleteCertificateResponse(
            limit=rate_limits.limit,
            remaining=rate_limits.remaining,
        )

    # -----------------------------------------------------------------
    # ListCertificates — GET /ccm/v1/certificates
    # -----------------------------------------------------------------

    def list_certificates(
        self, params: models.ListCertificatesRequest
    ) -> models.ListCertificatesResponse:
        """List cloud certificates with filtering and pagination.

        Mirrors Go ``ListCertificates`` (certificates.go lines 22-68).

        ``GET /ccm/v1/certificates``

        Supports optional filters for contract, group, status, domain,
        expiration, key type, issuer, sorting, and pagination.
        Certificate status values are comma-separated in the query string
        (mirrors Go ``UseCommaSeparatedQuery``).

        Args:
            params: Request containing optional filter and pagination
                parameters.

        Returns:
            Response with list of :class:`~models.Certificate` objects,
            pagination :class:`~models.Links`, :class:`~models.ListMetadata`,
            and rate-limit metadata.

        Raises:
            ValueError: If request validation fails.
            _WrappedError: If the API returns an error response.
        """
        validation.validate_list_certificates(params)

        query_params = _build_list_certificates_params(params)

        response, result = self._session.exec(
            "GET",
            "/ccm/v1/certificates",
            expect_json=True,
            params=query_params if query_params else None,
            error_parser=_make_error_parser(errors.ErrListCertificates),
        )

        if response.status_code != 200:
            raise _WrappedError(
                errors.ErrListCertificates,
                errors.Error.from_response(response),
            )

        # Parse response body fields
        raw_certs = (result or {}).get("certificates") or []
        certs = [
            c
            for raw in raw_certs
            if (c := models.Certificate.from_dict(raw)) is not None
        ]
        links_obj = models.Links.from_dict((result or {}).get("links"))
        metadata_obj = models.ListMetadata.from_dict(
            (result or {}).get("metadata")
        )
        rate_limits = _extract_rate_limit_headers(response)

        return models.ListCertificatesResponse(
            certificates=certs,
            links=links_obj,
            metadata=metadata_obj,
            rate_limits=rate_limits,
        )

    # -----------------------------------------------------------------
    # ListCertificateBindings — GET /ccm/v1/certificates/{id}/certificate-bindings
    # -----------------------------------------------------------------

    def list_certificate_bindings(
        self, params: models.ListCertificateBindingsRequest
    ) -> models.ListCertificateBindingsResponse:
        """List bindings for a specific certificate.

        Mirrors Go ``ListCertificateBindings``
        (bindings.go lines 13-43).

        ``GET /ccm/v1/certificates/{certificateID}/certificate-bindings``

        Args:
            params: Request containing the certificate ID and optional
                pagination parameters.

        Returns:
            Response with list of :class:`~models.CertificateBinding`
            objects and pagination :class:`~models.Links`.

        Raises:
            ValueError: If request validation fails.
            _WrappedError: If the API returns an error response.
        """
        validation.validate_list_certificate_bindings(params)

        path = (
            f"/ccm/v1/certificates/{params.certificate_id}"
            f"/certificate-bindings"
        )

        query_params: dict[str, str] = {}
        if params.page_size > 0:
            query_params["pageSize"] = str(params.page_size)
        if params.page > 0:
            query_params["page"] = str(params.page)

        response, result = self._session.exec(
            "GET",
            path,
            expect_json=True,
            params=query_params if query_params else None,
            error_parser=_make_error_parser(
                errors.ErrListCertificateBindings
            ),
        )

        if response.status_code != 200:
            raise _WrappedError(
                errors.ErrListCertificateBindings,
                errors.Error.from_response(response),
            )

        raw_bindings = (result or {}).get("bindings") or []
        binding_list = [
            b
            for raw in raw_bindings
            if (b := models.CertificateBinding.from_dict(raw)) is not None
        ]
        links_obj = models.Links.from_dict((result or {}).get("links"))

        return models.ListCertificateBindingsResponse(
            bindings=binding_list,
            links=links_obj,
        )

    # -----------------------------------------------------------------
    # ListBindings — GET /ccm/v1/certificate-bindings
    # -----------------------------------------------------------------

    def list_bindings(
        self, params: models.ListBindingsRequest
    ) -> models.ListBindingsResponse:
        """List all certificate bindings across all certificates.

        Mirrors Go ``ListBindings`` (bindings.go lines 45-82).

        ``GET /ccm/v1/certificate-bindings``

        Supports optional filters for contract, group, domain, network,
        expiration, and pagination.

        Args:
            params: Request containing optional filter and pagination
                parameters.

        Returns:
            Response with list of :class:`~models.CertificateBinding`
            objects and pagination :class:`~models.Links`.

        Raises:
            ValueError: If request validation fails.
            _WrappedError: If the API returns an error response.
        """
        validation.validate_list_bindings(params)

        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id
        if params.expiring_in_days is not None:
            query_params["expiringInDays"] = str(params.expiring_in_days)
        if params.domain:
            query_params["domain"] = params.domain
        if params.network:
            query_params["network"] = params.network
        if params.page_size > 0:
            query_params["pageSize"] = str(params.page_size)
        if params.page > 0:
            query_params["page"] = str(params.page)

        response, result = self._session.exec(
            "GET",
            "/ccm/v1/certificate-bindings",
            expect_json=True,
            params=query_params if query_params else None,
            error_parser=_make_error_parser(errors.ErrListBindings),
        )

        if response.status_code != 200:
            raise _WrappedError(
                errors.ErrListBindings,
                errors.Error.from_response(response),
            )

        raw_bindings = (result or {}).get("bindings") or []
        binding_list = [
            b
            for raw in raw_bindings
            if (b := models.CertificateBinding.from_dict(raw)) is not None
        ]
        links_obj = models.Links.from_dict((result or {}).get("links"))

        return models.ListBindingsResponse(
            bindings=binding_list,
            links=links_obj,
        )
