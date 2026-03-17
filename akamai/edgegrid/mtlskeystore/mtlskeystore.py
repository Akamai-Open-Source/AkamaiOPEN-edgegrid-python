"""Akamai mTLS Key Store API client.

Provides the Client class with all 9 endpoint methods for managing client
certificates, certificate versions, and account CA certificates in the
Akamai mTLS Origin Key Store.

Mirrors Go pkg/mtlskeystore.MTLSKeystore interface.
"""

import json
import logging
from urllib.parse import urlencode

from akamai.edgegrid.session import Session
from akamai.edgegrid.mtlskeystore.models import (
    AccountCACertificate,
    AssociatedProperty,
    Certificate,
    CertificateBlock,
    ClientCertificateVersion,
    CreateClientCertificateRequest,
    CreateClientCertificateResponse,
    CSRBlock,
    DeleteClientCertificateVersionRequest,
    DeleteClientCertificateVersionResponse,
    GetClientCertificateRequest,
    GetClientCertificateResponse,
    ListAccountCACertificatesRequest,
    ListAccountCACertificatesResponse,
    ListClientCertificatesResponse,
    ListClientCertificateVersionsRequest,
    ListClientCertificateVersionsResponse,
    PatchClientCertificateRequest,
    PatchClientCertificateRequestBody,
    RotateClientCertificateVersionRequest,
    RotateClientCertificateVersionResponse,
    UploadSignedClientCertificateRequest,
    UploadSignedClientCertificateRequestBody,
    ValidationDetail,
    ValidationResult,
)
from akamai.edgegrid.mtlskeystore.errors import (
    Error,
    parse_error_response,
    ErrStructValidation,
    ErrListClientCertificates,
    ErrGetClientCertificate,
    ErrCreateClientCertificate,
    ErrPatchClientCertificate,
    ErrRotateClientCertificateVersion,
    ErrListClientCertificateVersions,
    ErrDeleteClientCertificateVersion,
    ErrUploadClientCertificateVersion,
    ErrListAccountCACertificates,
)
from akamai.edgegrid.mtlskeystore.validation import (
    validate_get_client_certificate_request,
    validate_create_client_certificate_request,
    validate_patch_client_certificate_request,
    validate_rotate_client_certificate_version_request,
    validate_list_client_certificate_versions_request,
    validate_delete_client_certificate_version_request,
    validate_upload_signed_client_certificate_request,
    validate_list_account_ca_certificates_request,
)

logger = logging.getLogger(__name__)


class Client:
    """mTLS Key Store API client.

    Provides methods for managing client certificates, certificate versions,
    and account CA certificates in the Akamai mTLS Origin Key Store.

    Mirrors Go ``pkg/mtlskeystore.MTLSKeystore`` interface.

    See: https://techdocs.akamai.com/mtls-origin-keystore/reference/api
    """

    def __init__(self, session: Session):
        """Initialize the mTLS Key Store client.

        Mirrors Go ``mtlskeystore.Client(sess session.Session, opts ...Option)``.

        :param session: Authenticated Akamai API session.
        """
        self._session = session

    # ------------------------------------------------------------------
    # Pattern 1 methods  (client_certificates.go + account_ca_certificates.go)
    # Error wrapping: fmt.Errorf("%s: %w", ErrSentinel, m.Error(resp))
    # Validation:     fmt.Errorf("%s: %w: %s", sentinel, ErrStructValidation, err)
    # ------------------------------------------------------------------

    def list_client_certificates(self) -> ListClientCertificatesResponse:
        """List client certificates under the account.

        Mirrors Go ``ListClientCertificates`` in client_certificates.go.

        See: https://techdocs.akamai.com/mtls-origin-keystore/reference/get-client-certs

        :returns: ListClientCertificatesResponse with list of certificates.
        :raises ValueError: Wrapping API Error with sentinel on non-200 status.
        """
        logger.debug("ListClientCertificates")
        path = "/mtls-origin-keystore/v1/client-certificates"
        try:
            response, result = self._session.exec(
                "GET", path, expect_json=True,
                error_parser=parse_error_response)
        except Error as exc:
            raise _wrap_error(ErrListClientCertificates, exc) from exc
        if response.status_code != 200:
            raise _wrap_error(
                ErrListClientCertificates,
                parse_error_response(response))
        return _parse_list_client_certificates_response(result)

    def get_client_certificate(
            self, params: GetClientCertificateRequest
    ) -> GetClientCertificateResponse:
        """Get details of a client certificate.

        Mirrors Go ``GetClientCertificate`` in client_certificates.go.

        See: https://techdocs.akamai.com/mtls-origin-keystore/reference/get-client-cert

        :param params: Request containing the certificate ID.
        :returns: GetClientCertificateResponse with certificate details.
        :raises ValueError: On validation failure or non-200 API status.
        """
        logger.debug("GetClientCertificate")
        err = validate_get_client_certificate_request(params)
        if err is not None:
            raise ValueError(
                f"{ErrGetClientCertificate}: {ErrStructValidation}: {err}")
        path = (f"/mtls-origin-keystore/v1/client-certificates"
                f"/{params.certificate_id}")
        try:
            response, result = self._session.exec(
                "GET", path, expect_json=True,
                error_parser=parse_error_response)
        except Error as exc:
            raise _wrap_error(ErrGetClientCertificate, exc) from exc
        if response.status_code != 200:
            raise _wrap_error(
                ErrGetClientCertificate,
                parse_error_response(response))
        return _parse_get_client_certificate_response(result)

    def create_client_certificate(
            self, params: CreateClientCertificateRequest
    ) -> CreateClientCertificateResponse:
        """Create a client certificate.

        Mirrors Go ``CreateClientCertificate`` in client_certificates.go.

        See: https://techdocs.akamai.com/mtls-origin-keystore/reference/post-client-cert

        :param params: Request with certificate creation details.
        :returns: CreateClientCertificateResponse with created certificate.
        :raises ValueError: On validation failure or non-201 API status.
        """
        logger.debug("CreateClientCertificate")
        err = validate_create_client_certificate_request(params)
        if err is not None:
            raise ValueError(
                f"{ErrCreateClientCertificate}: {ErrStructValidation}: {err}")
        path = "/mtls-origin-keystore/v1/client-certificates"
        body = _serialize_create_request(params)
        try:
            response, result = self._session.exec(
                "POST", path, body=body, expect_json=True,
                error_parser=parse_error_response)
        except Error as exc:
            raise _wrap_error(ErrCreateClientCertificate, exc) from exc
        if response.status_code != 201:
            raise _wrap_error(
                ErrCreateClientCertificate,
                parse_error_response(response))
        return _parse_create_client_certificate_response(result)

    def patch_client_certificate(
            self, params: PatchClientCertificateRequest
    ) -> None:
        """Update the client certificate's name or notification emails.

        Mirrors Go ``PatchClientCertificate`` in client_certificates.go.

        See: https://techdocs.akamai.com/mtls-origin-keystore/reference/patch-client-cert

        :param params: Request with certificate ID and update body.
        :raises ValueError: On validation failure or non-200 API status.
        """
        logger.debug("PatchClientCertificate")
        err = validate_patch_client_certificate_request(params)
        if err is not None:
            raise ValueError(
                f"{ErrPatchClientCertificate}: {ErrStructValidation}: {err}")
        path = (f"/mtls-origin-keystore/v1/client-certificates"
                f"/{params.certificate_id}")
        body = _serialize_patch_request_body(params.body)
        try:
            response, _ = self._session.exec(
                "PATCH", path, body=body,
                error_parser=parse_error_response)
        except Error as exc:
            raise _wrap_error(ErrPatchClientCertificate, exc) from exc
        if response.status_code != 200:
            raise _wrap_error(
                ErrPatchClientCertificate,
                parse_error_response(response))

    # ------------------------------------------------------------------
    # Pattern 2 methods  (client_certificate_versions.go)
    # Error wrapping: return nil, m.Error(resp)          [direct, unwrapped]
    # Validation:     fmt.Errorf("%w: validation failed: %s", sentinel, err)
    # ------------------------------------------------------------------

    def rotate_client_certificate_version(
            self, params: RotateClientCertificateVersionRequest
    ) -> RotateClientCertificateVersionResponse:
        """Create a new version in the client certificate.

        Mirrors Go ``RotateClientCertificateVersion`` in
        client_certificate_versions.go.

        See: https://techdocs.akamai.com/mtls-origin-keystore/reference/post-client-cert-version

        :param params: Request containing the certificate ID.
        :returns: RotateClientCertificateVersionResponse with version details.
        :raises ValueError: On validation failure.
        :raises Error: On API error (direct, not wrapped with sentinel).
        """
        logger.debug("Rotating client certificate versions")
        err = validate_rotate_client_certificate_version_request(params)
        if err is not None:
            raise ValueError(
                f"{ErrRotateClientCertificateVersion}: "
                f"validation failed: {err}")
        path = (f"/mtls-origin-keystore/v1/client-certificates"
                f"/{params.certificate_id}/versions")
        response, result = self._session.exec(
            "POST", path, expect_json=True,
            error_parser=parse_error_response)
        if response.status_code != 201:
            raise parse_error_response(response)
        return _parse_rotate_response(result)

    def list_client_certificate_versions(
            self, params: ListClientCertificateVersionsRequest
    ) -> ListClientCertificateVersionsResponse:
        """List versions of a client certificate.

        Mirrors Go ``ListClientCertificateVersions`` in
        client_certificate_versions.go.

        See: https://techdocs.akamai.com/mtls-origin-keystore/reference/get-client-cert-versions

        :param params: Request with certificate ID and optional filter.
        :returns: ListClientCertificateVersionsResponse with version list.
        :raises ValueError: On validation failure.
        :raises Error: On API error (direct, not wrapped with sentinel).
        """
        logger.debug("Fetching client certificate versions")
        err = validate_list_client_certificate_versions_request(params)
        if err is not None:
            raise ValueError(
                f"{ErrListClientCertificateVersions}: "
                f"validation failed: {err}")
        path = (f"/mtls-origin-keystore/v1/client-certificates"
                f"/{params.certificate_id}/versions")
        query_params = None
        if params.include_associated_properties:
            query_params = {"includeAssociatedProperties": "true"}
        response, result = self._session.exec(
            "GET", path, expect_json=True,
            params=query_params,
            error_parser=parse_error_response)
        if response.status_code != 200:
            raise parse_error_response(response)
        return _parse_list_versions_response(result)

    def delete_client_certificate_version(
            self, params: DeleteClientCertificateVersionRequest
    ) -> DeleteClientCertificateVersionResponse | None:
        """Delete a client certificate version.

        Returns ``None`` for 204 No Content (immediate deletion) or a
        :class:`DeleteClientCertificateVersionResponse` for 202 Accepted
        (deletion scheduled).

        Mirrors Go ``DeleteClientCertificateVersion`` in
        client_certificate_versions.go.

        See: https://techdocs.akamai.com/mtls-origin-keystore/reference/delete-client-certificate

        :param params: Request with certificate ID and version number.
        :returns: Response or None (for 204 No Content).
        :raises ValueError: On validation failure.
        :raises Error: On API error (direct, not wrapped with sentinel).
        """
        logger.debug("Deleting client certificate version")
        err = validate_delete_client_certificate_version_request(params)
        if err is not None:
            raise ValueError(
                f"{ErrDeleteClientCertificateVersion}: "
                f"validation failed: {err}")
        path = (f"/mtls-origin-keystore/v1/client-certificates"
                f"/{params.certificate_id}/versions/{params.version}")
        response, result = self._session.exec(
            "DELETE", path, expect_json=True,
            error_parser=parse_error_response)
        # Go returns (nil, nil) for 204 No Content
        if response.status_code == 204:
            return None
        if response.status_code != 202:
            raise parse_error_response(response)
        return _parse_delete_version_response(result)

    def upload_signed_client_certificate(
            self, params: UploadSignedClientCertificateRequest
    ) -> None:
        """Upload a signed THIRD_PARTY client certificate.

        Mirrors Go ``UploadSignedClientCertificate`` in
        client_certificate_versions.go.

        See: https://techdocs.akamai.com/mtls-origin-keystore/reference/post-cert-block

        :param params: Request with certificate ID, version, body, and
            optional acknowledgeAllWarnings flag.
        :raises ValueError: On validation failure.
        :raises Error: On API error (direct, not wrapped with sentinel).
        """
        logger.debug("Uploading signed client certificate")
        err = validate_upload_signed_client_certificate_request(params)
        if err is not None:
            raise ValueError(
                f"{ErrUploadClientCertificateVersion}: "
                f"validation failed: {err}")
        path = (f"/mtls-origin-keystore/v1/client-certificates"
                f"/{params.certificate_id}/versions/{params.version}"
                f"/certificate-block")
        query_params = None
        if params.acknowledge_all_warnings is not None:
            query_params = {
                "acknowledgeAllWarnings":
                    "true" if params.acknowledge_all_warnings else "false"
            }
        body = _serialize_upload_body(params.body)
        response, _ = self._session.exec(
            "POST", path, body=body,
            params=query_params,
            error_parser=parse_error_response)
        if response.status_code != 200:
            raise parse_error_response(response)

    # ------------------------------------------------------------------
    # Pattern 1 — ListAccountCACertificates (account_ca_certificates.go)
    # ------------------------------------------------------------------

    def list_account_ca_certificates(
            self, params: ListAccountCACertificatesRequest
    ) -> ListAccountCACertificatesResponse:
        """List CA certificates under the account.

        Mirrors Go ``ListAccountCACertificates`` in
        account_ca_certificates.go.

        See: https://techdocs.akamai.com/mtls-origin-keystore/reference/get-ca-certs

        :param params: Request with optional status filter list.
        :returns: ListAccountCACertificatesResponse with certificate list.
        :raises ValueError: On validation failure or non-200 API status.
        """
        logger.debug("ListAccountCACertificates")
        err = validate_list_account_ca_certificates_request(params)
        if err is not None:
            raise ValueError(
                f"{ErrListAccountCACertificates}: "
                f"{ErrStructValidation}: {err}")
        path = "/mtls-origin-keystore/v1/ca-certificates"
        query_params = None
        if params.status:
            query_params = {"status": ",".join(params.status)}
        try:
            response, result = self._session.exec(
                "GET", path, expect_json=True,
                params=query_params,
                error_parser=parse_error_response)
        except Error as exc:
            raise _wrap_error(
                ErrListAccountCACertificates, exc) from exc
        if response.status_code != 200:
            raise _wrap_error(
                ErrListAccountCACertificates,
                parse_error_response(response))
        return _parse_list_account_ca_certificates_response(result)


# ------------------------------------------------------------------
# Module-level exported helpers
# ------------------------------------------------------------------

def statuses_to_query_string(statuses: list[str]) -> str:
    """Build URL-encoded query string from a list of status values.

    Mirrors Go ``statusesToQueryString`` in account_ca_certificates.go.
    Joins statuses with commas and URL-encodes the result.

    :param statuses: List of status string values.
    :returns: URL-encoded query string, e.g. ``status=EXPIRED%2CCURRENT``.
    """
    if not statuses:
        return ""
    return urlencode({"status": ",".join(statuses)})


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------

def _wrap_error(sentinel: str, err: Exception) -> ValueError:
    """Wrap an error with a sentinel error message prefix.

    Mirrors Go ``fmt.Errorf("%s: %w", sentinel, err)`` pattern used by
    client_certificates.go and account_ca_certificates.go methods.

    :param sentinel: Sentinel error string constant.
    :param err: The underlying exception to wrap.
    :returns: A new ValueError with the combined message.
    """
    return ValueError(f"{sentinel}: {err}")


# ------------------------------------------------------------------
# Request body serializers
# ------------------------------------------------------------------

def _serialize_create_request(
        params: CreateClientCertificateRequest) -> str:
    """Serialize a CreateClientCertificateRequest to a JSON string.

    Converts Python snake_case attributes to camelCase JSON keys matching
    the Go struct JSON tags exactly.

    :param params: Create certificate request model.
    :returns: JSON string suitable for HTTP request body.
    """
    body: dict = {
        "certificateName": params.certificate_name,
        "contractId": params.contract_id,
        "geography": params.geography,
        "groupId": params.group_id,
        "notificationEmails": params.notification_emails,
        "secureNetwork": params.secure_network,
        "signer": params.signer,
    }
    if params.key_algorithm is not None:
        body["keyAlgorithm"] = params.key_algorithm
    if params.preferred_ca is not None:
        body["preferredCa"] = params.preferred_ca
    if params.subject is not None:
        body["subject"] = params.subject
    return json.dumps(body)


def _serialize_patch_request_body(
        body: PatchClientCertificateRequestBody) -> str:
    """Serialize a PatchClientCertificateRequestBody to a JSON string.

    Both fields are optional; only non-None values are included in the
    output (matching Go ``omitempty`` semantics).

    :param body: Patch request body model.
    :returns: JSON string suitable for HTTP request body.
    """
    data: dict = {}
    if body.certificate_name is not None:
        data["certificateName"] = body.certificate_name
    if body.notification_emails is not None:
        data["notificationEmails"] = body.notification_emails
    return json.dumps(data)


def _serialize_upload_body(
        body: UploadSignedClientCertificateRequestBody) -> str:
    """Serialize an UploadSignedClientCertificateRequestBody to JSON.

    :param body: Upload request body model.
    :returns: JSON string suitable for HTTP request body.
    """
    data: dict = {
        "certificate": body.certificate,
    }
    if body.trust_chain is not None:
        data["trustChain"] = body.trust_chain
    return json.dumps(data)


# ------------------------------------------------------------------
# Response parsers
# ------------------------------------------------------------------

def _parse_certificate(data: dict) -> Certificate:
    """Parse a JSON dictionary into a Certificate model.

    :param data: Dictionary from JSON response.
    :returns: Certificate dataclass instance.
    """
    return Certificate(
        certificate_id=data.get("certificateId", ""),
        certificate_name=data.get("certificateName", ""),
        created_by=data.get("createdBy", ""),
        created_date=data.get("createdDate", ""),
        geography=data.get("geography", ""),
        key_algorithm=data.get("keyAlgorithm", ""),
        notification_emails=data.get("notificationEmails", []),
        secure_network=data.get("secureNetwork", ""),
        signer=data.get("signer", ""),
        subject=data.get("subject", ""),
    )


def _parse_list_client_certificates_response(
        data: dict) -> ListClientCertificatesResponse:
    """Parse a ListClientCertificates API response.

    :param data: Dictionary from JSON response.
    :returns: ListClientCertificatesResponse instance.
    """
    certs = [
        _parse_certificate(c)
        for c in data.get("certificates", [])
    ]
    return ListClientCertificatesResponse(certificates=certs)


def _parse_get_client_certificate_response(
        data: dict) -> GetClientCertificateResponse:
    """Parse a GetClientCertificate API response.

    :param data: Dictionary from JSON response (single certificate object).
    :returns: GetClientCertificateResponse instance.
    """
    return GetClientCertificateResponse(
        certificate_id=data.get("certificateId", ""),
        certificate_name=data.get("certificateName", ""),
        created_by=data.get("createdBy", ""),
        created_date=data.get("createdDate", ""),
        geography=data.get("geography", ""),
        key_algorithm=data.get("keyAlgorithm", ""),
        notification_emails=data.get("notificationEmails", []),
        secure_network=data.get("secureNetwork", ""),
        signer=data.get("signer", ""),
        subject=data.get("subject", ""),
    )


def _parse_create_client_certificate_response(
        data: dict) -> CreateClientCertificateResponse:
    """Parse a CreateClientCertificate API response.

    :param data: Dictionary from JSON response.
    :returns: CreateClientCertificateResponse instance.
    """
    return CreateClientCertificateResponse(
        certificate_id=data.get("certificateId", ""),
        certificate_name=data.get("certificateName", ""),
        created_by=data.get("createdBy", ""),
        created_date=data.get("createdDate", ""),
        geography=data.get("geography", ""),
        key_algorithm=data.get("keyAlgorithm", ""),
        notification_emails=data.get("notificationEmails", []),
        secure_network=data.get("secureNetwork", ""),
        signer=data.get("signer", ""),
        subject=data.get("subject", ""),
    )


def _parse_certificate_block(data: dict | None) -> CertificateBlock | None:
    """Parse a certificateBlock JSON object.

    :param data: Dictionary or None.
    :returns: CertificateBlock instance or None.
    """
    if data is None:
        return None
    return CertificateBlock(
        certificate=data.get("certificate", ""),
        key_algorithm=data.get("keyAlgorithm", ""),
        trust_chain=data.get("trustChain"),
    )


def _parse_csr_block(data: dict | None) -> CSRBlock | None:
    """Parse a csrBlock JSON object.

    :param data: Dictionary or None.
    :returns: CSRBlock instance or None.
    """
    if data is None:
        return None
    return CSRBlock(
        csr=data.get("csr", ""),
        key_algorithm=data.get("keyAlgorithm", ""),
    )


def _parse_validation_detail(data: dict) -> ValidationDetail:
    """Parse a single validation detail entry.

    :param data: Dictionary from JSON.
    :returns: ValidationDetail instance.
    """
    return ValidationDetail(
        message=data.get("message", ""),
        reason=data.get("reason", ""),
        type=data.get("type", ""),
    )


def _parse_validation_result(
        data: dict | None) -> ValidationResult:
    """Parse a validation result containing errors and warnings lists.

    :param data: Dictionary or None.
    :returns: ValidationResult instance (empty lists if data is None).
    """
    if data is None:
        return ValidationResult(errors=[], warnings=[])
    return ValidationResult(
        errors=[
            _parse_validation_detail(d)
            for d in data.get("errors", [])
        ],
        warnings=[
            _parse_validation_detail(d)
            for d in data.get("warnings", [])
        ],
    )


def _parse_associated_property(data: dict) -> AssociatedProperty:
    """Parse an associated property entry.

    Note: The Go JSON tag for this field is ``properties`` (not
    ``associatedProperties``).

    :param data: Dictionary from JSON.
    :returns: AssociatedProperty instance.
    """
    return AssociatedProperty(
        asset_id=data.get("assetId", ""),
        group_id=data.get("groupId", 0),
        property_name=data.get("propertyName", ""),
        property_version=data.get("propertyVersion", 0),
    )


def _parse_rotate_response(
        data: dict) -> RotateClientCertificateVersionResponse:
    """Parse a RotateClientCertificateVersion API response.

    :param data: Dictionary from JSON response.
    :returns: RotateClientCertificateVersionResponse instance.
    """
    return RotateClientCertificateVersionResponse(
        version=data.get("version", 0),
        version_guid=data.get("versionGuid", ""),
        version_alias=data.get("versionAlias"),
        certificate_block=_parse_certificate_block(
            data.get("certificateBlock")),
        created_by=data.get("createdBy", ""),
        created_date=data.get("createdDate", ""),
        csr_block=_parse_csr_block(data.get("csrBlock")),
        expiry_date=data.get("expiryDate"),
        issued_date=data.get("issuedDate"),
        issuer=data.get("issuer"),
        key_algorithm=data.get("keyAlgorithm", ""),
        elliptic_curve=data.get("ellipticCurve"),
        key_size_in_bytes=data.get("keySizeInBytes"),
        signature_algorithm=data.get("signatureAlgorithm"),
        status=data.get("status", ""),
        subject=data.get("subject"),
    )


def _parse_client_certificate_version(
        data: dict) -> ClientCertificateVersion:
    """Parse a single client certificate version entry.

    :param data: Dictionary from JSON response.
    :returns: ClientCertificateVersion instance.
    """
    return ClientCertificateVersion(
        version=data.get("version", 0),
        version_guid=data.get("versionGuid", ""),
        version_alias=data.get("versionAlias"),
        certificate_block=_parse_certificate_block(
            data.get("certificateBlock")),
        certificate_submitted_by=data.get("certificateSubmittedBy"),
        certificate_submitted_date=data.get("certificateSubmittedDate"),
        created_by=data.get("createdBy", ""),
        created_date=data.get("createdDate", ""),
        csr_block=_parse_csr_block(data.get("csrBlock")),
        delete_requested_date=data.get("deleteRequestedDate"),
        expiry_date=data.get("expiryDate"),
        issued_date=data.get("issuedDate"),
        issuer=data.get("issuer"),
        key_algorithm=data.get("keyAlgorithm", ""),
        elliptic_curve=data.get("ellipticCurve"),
        key_size_in_bytes=data.get("keySizeInBytes"),
        scheduled_delete_date=data.get("scheduledDeleteDate"),
        signature_algorithm=data.get("signatureAlgorithm"),
        status=data.get("status", ""),
        subject=data.get("subject"),
        validation=_parse_validation_result(data.get("validation")),
        associated_properties=[
            _parse_associated_property(p)
            for p in data.get("properties", [])
        ],
    )


def _parse_list_versions_response(
        data: dict) -> ListClientCertificateVersionsResponse:
    """Parse a ListClientCertificateVersions API response.

    :param data: Dictionary from JSON response.
    :returns: ListClientCertificateVersionsResponse instance.
    """
    versions = [
        _parse_client_certificate_version(v)
        for v in data.get("versions", [])
    ]
    return ListClientCertificateVersionsResponse(versions=versions)


def _parse_delete_version_response(
        data: dict) -> DeleteClientCertificateVersionResponse:
    """Parse a DeleteClientCertificateVersion API response (202 Accepted).

    :param data: Dictionary from JSON response.
    :returns: DeleteClientCertificateVersionResponse instance.
    """
    return DeleteClientCertificateVersionResponse(
        message=data.get("message", ""),
    )


def _parse_account_ca_certificate(
        data: dict) -> AccountCACertificate:
    """Parse a single account CA certificate entry.

    :param data: Dictionary from JSON response.
    :returns: AccountCACertificate instance.
    """
    return AccountCACertificate(
        account_id=data.get("accountId", ""),
        certificate=data.get("certificate", ""),
        common_name=data.get("commonName", ""),
        created_by=data.get("createdBy", ""),
        created_date=data.get("createdDate", ""),
        expiry_date=data.get("expiryDate", ""),
        id=data.get("id", 0),
        issued_date=data.get("issuedDate", ""),
        key_algorithm=data.get("keyAlgorithm", ""),
        key_size_in_bytes=data.get("keySizeInBytes", 0),
        qualification_date=data.get("qualificationDate"),
        signature_algorithm=data.get("signatureAlgorithm", ""),
        status=data.get("status", ""),
        subject=data.get("subject", ""),
        version=data.get("version", 0),
    )


def _parse_list_account_ca_certificates_response(
        data: dict) -> ListAccountCACertificatesResponse:
    """Parse a ListAccountCACertificates API response.

    :param data: Dictionary from JSON response.
    :returns: ListAccountCACertificatesResponse instance.
    """
    certs = [
        _parse_account_ca_certificate(c)
        for c in data.get("certificates", [])
    ]
    return ListAccountCACertificatesResponse(certificates=certs)
