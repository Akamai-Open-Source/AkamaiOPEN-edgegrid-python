"""Request/response model dataclasses for the Cloud Certificates API client.

Ported from Go ``pkg/cloudcertificates/datamodel.go``.  Every Go struct maps
to a Python :func:`dataclasses.dataclass`.  Field names are derived from the
Go JSON tags converted to *snake_case*; types follow the Go-to-Python mapping
(``string`` → ``str``, ``*string`` → ``str | None``, ``int64`` → ``int``,
``time.Time`` → ``str``, ``[]T`` → ``list[T]``).
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields as dataclass_fields


# ---------------------------------------------------------------------------
# Type aliases — mirror Go typed-string constants
# ---------------------------------------------------------------------------

CertificateStatus = str
CryptographicAlgorithm = str
SecureNetwork = str
KeySize = str
Network = str


# ---------------------------------------------------------------------------
# Constants — mirror Go ``const`` block (datamodel.go lines 31-63)
# ---------------------------------------------------------------------------

# CertificateStatus values
StatusActive: CertificateStatus = "ACTIVE"  # pylint: disable=invalid-name
StatusReadyForUse: CertificateStatus = "READY_FOR_USE"  # pylint: disable=invalid-name
StatusCSRReady: CertificateStatus = "CSR_READY"  # pylint: disable=invalid-name

# CryptographicAlgorithm values
CryptographicAlgorithmRSA: CryptographicAlgorithm = "RSA"  # pylint: disable=invalid-name
CryptographicAlgorithmECDSA: CryptographicAlgorithm = "ECDSA"  # pylint: disable=invalid-name

# SecureNetwork values
SecureNetworkEnhancedTLS: SecureNetwork = "ENHANCED_TLS"  # pylint: disable=invalid-name

# KeySize values
KeySize2048: KeySize = "2048"  # pylint: disable=invalid-name
KeySizeP256: KeySize = "P-256"  # pylint: disable=invalid-name

# Network (binding network) values
NetworkStaging: Network = "STAGING"  # pylint: disable=invalid-name
NetworkProduction: Network = "PRODUCTION"  # pylint: disable=invalid-name

# Sort field validation regex pattern (single-field component)
SortFieldPat: str = (  # pylint: disable=invalid-name
    r"[+\-]?(modifiedDate|expirationDate|createdDate|certificateName)"
)


# ---------------------------------------------------------------------------
# Internal helpers — camelCase ↔ snake_case JSON field mapping
# ---------------------------------------------------------------------------

_SNAKE_TO_CAMEL: dict[str, str] = {
    "self_link": "self",
    "signed_certificate_sha256_fingerprint": (
        "signedCertificateSHA256Fingerprint"
    ),
}

_CAMEL_TO_SNAKE: dict[str, str] = {v: k for k, v in _SNAKE_TO_CAMEL.items()}


def _to_camel(name: str) -> str:
    """Convert a *snake_case* Python name to the *camelCase* JSON key."""
    if name in _SNAKE_TO_CAMEL:
        return _SNAKE_TO_CAMEL[name]
    parts = name.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


def _serialize(val: object) -> object:
    """Recursively prepare *val* for JSON serialisation."""
    if val is None:
        return None
    if isinstance(val, list):
        return [_serialize(v) for v in val]
    if hasattr(val, "to_dict"):
        return val.to_dict()  # type: ignore[union-attr]
    return val


def _model_to_dict(obj: object) -> dict:
    """Generic helper: convert any model dataclass to a camelCase dict."""
    out: dict = {}
    for fld in dataclass_fields(obj):  # type: ignore[arg-type]
        out[_to_camel(fld.name)] = _serialize(getattr(obj, fld.name))
    return out


# ---------------------------------------------------------------------------
# Domain dataclasses
# ---------------------------------------------------------------------------


@dataclass
class Subject:
    """Certificate subject information (X.509 fields).

    Mirrors Go ``Subject`` struct.
    """

    common_name: str = ""
    organization: str = ""
    country: str = ""
    state: str = ""
    locality: str = ""

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict for JSON output."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> Subject | None:
        """Deserialise from a camelCase dict.  Returns ``None`` if *data* is
        falsy."""
        if not data:
            return None
        return cls(
            common_name=data.get("commonName", ""),
            organization=data.get("organization", ""),
            country=data.get("country", ""),
            state=data.get("state", ""),
            locality=data.get("locality", ""),
        )


@dataclass
class RateLimitsMetadata:
    """API rate-limit information extracted from HTTP response headers.

    Mirrors Go ``RateLimitsMetadata`` struct.
    """

    limit: int | None = None
    remaining: int | None = None

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> RateLimitsMetadata | None:
        """Deserialise from a camelCase dict."""
        if not data:
            return None
        return cls(
            limit=data.get("limit"),
            remaining=data.get("remaining"),
        )


@dataclass
class ResourceLimitsMetadata:
    """Resource-limit information extracted from HTTP response headers.

    Mirrors Go ``ResourceLimitsMetadata`` struct.
    """

    certificate_limit_total: int | None = None
    certificate_limit_remaining: int | None = None

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> ResourceLimitsMetadata | None:
        """Deserialise from a camelCase dict."""
        if not data:
            return None
        return cls(
            certificate_limit_total=data.get("certificateLimitTotal"),
            certificate_limit_remaining=data.get(
                "certificateLimitRemaining"
            ),
        )


@dataclass
class Certificate:  # pylint: disable=too-many-instance-attributes
    """Cloud certificate domain model (24 fields).

    Mirrors Go ``Certificate`` struct.  ``time.Time`` fields are represented
    as ISO-8601 / RFC-3339 strings; pointer fields map to ``T | None``.
    """

    certificate_id: str = ""
    certificate_name: str = ""
    sans: list[str] = field(default_factory=list)
    subject: Subject | None = None
    certificate_type: str = ""
    key_type: str = ""
    key_size: str = ""
    secure_network: str = ""
    contract_id: str = ""
    account_id: str = ""
    created_date: str = ""
    created_by: str = ""
    modified_date: str = ""
    modified_by: str = ""
    certificate_status: str = ""
    csr_pem: str = ""
    csr_expiration_date: str = ""
    signed_certificate_pem: str | None = None
    signed_certificate_not_valid_after_date: str | None = None
    signed_certificate_not_valid_before_date: str | None = None
    signed_certificate_serial_number: str | None = None
    signed_certificate_sha256_fingerprint: str | None = None
    signed_certificate_issuer: str | None = None
    trust_chain_pem: str | None = None

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> Certificate | None:
        """Deserialise from a camelCase dict."""
        if not data:
            return None
        return cls(
            certificate_id=data.get("certificateId", ""),
            certificate_name=data.get("certificateName", ""),
            sans=data.get("sans") or [],
            subject=Subject.from_dict(data.get("subject")),
            certificate_type=data.get("certificateType", ""),
            key_type=data.get("keyType", ""),
            key_size=data.get("keySize", ""),
            secure_network=data.get("secureNetwork", ""),
            contract_id=data.get("contractId", ""),
            account_id=data.get("accountId", ""),
            created_date=data.get("createdDate", ""),
            created_by=data.get("createdBy", ""),
            modified_date=data.get("modifiedDate", ""),
            modified_by=data.get("modifiedBy", ""),
            certificate_status=data.get("certificateStatus", ""),
            csr_pem=data.get("csrPem", ""),
            csr_expiration_date=data.get("csrExpirationDate", ""),
            signed_certificate_pem=data.get("signedCertificatePem"),
            signed_certificate_not_valid_after_date=data.get(
                "signedCertificateNotValidAfterDate"
            ),
            signed_certificate_not_valid_before_date=data.get(
                "signedCertificateNotValidBeforeDate"
            ),
            signed_certificate_serial_number=data.get(
                "signedCertificateSerialNumber"
            ),
            signed_certificate_sha256_fingerprint=data.get(
                "signedCertificateSHA256Fingerprint"
            ),
            signed_certificate_issuer=data.get(
                "signedCertificateIssuer"
            ),
            trust_chain_pem=data.get("trustChainPem"),
        )


@dataclass
class CertificateBinding:
    """Binding between a certificate and a CDN hostname.

    Mirrors Go ``CertificateBinding`` struct.  ``certificate_id`` uses
    ``int | str`` because Go declares the field as ``json.Number`` which
    can be either a JSON number or a JSON string.
    """

    certificate_id: int | str = 0
    hostname: str = ""
    network: str = ""
    resource_type: str = ""

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> CertificateBinding | None:
        """Deserialise from a camelCase dict."""
        if not data:
            return None
        return cls(
            certificate_id=data.get("certificateId", 0),
            hostname=data.get("hostname", ""),
            network=data.get("network", ""),
            resource_type=data.get("resourceType", ""),
        )


@dataclass
class Links:
    """Pagination and navigation links for list responses.

    Mirrors Go ``Links`` struct.  The JSON key ``"self"`` is mapped to
    the Python attribute ``self_link`` because *self* is a reserved word.
    """

    self_link: str = ""
    next: str | None = None  # pylint: disable=redefined-builtin
    previous: str | None = None

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> Links | None:
        """Deserialise from a camelCase dict."""
        if not data:
            return None
        return cls(
            self_link=data.get("self", ""),
            next=data.get("next"),
            previous=data.get("previous"),
        )


@dataclass
class ListMetadata:
    """Pagination metadata for list responses.

    Mirrors Go ``ListMetadata`` struct.
    """

    total_items: int = 0
    total_pages: int = 0

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> ListMetadata | None:
        """Deserialise from a camelCase dict."""
        if not data:
            return None
        return cls(
            total_items=data.get("totalItems", 0),
            total_pages=data.get("totalPages", 0),
        )


# ---------------------------------------------------------------------------
# Request body types
# ---------------------------------------------------------------------------


@dataclass
class CreateCertificateRequestBody:
    """Body payload for certificate-creation requests.

    Mirrors Go ``CreateCertificateRequestBody`` struct.
    """

    certificate_name: str = ""
    key_type: str = ""
    key_size: str = ""
    secure_network: str = ""
    sans: list[str] = field(default_factory=list)
    subject: Subject | None = None

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(
        cls, data: dict | None
    ) -> CreateCertificateRequestBody | None:
        """Deserialise from a camelCase dict."""
        if not data:
            return None
        return cls(
            certificate_name=data.get("certificateName", ""),
            key_type=data.get("keyType", ""),
            key_size=data.get("keySize", ""),
            secure_network=data.get("secureNetwork", ""),
            sans=data.get("sans") or [],
            subject=Subject.from_dict(data.get("subject")),
        )


# ---------------------------------------------------------------------------
# Request types
# ---------------------------------------------------------------------------


@dataclass
class CreateCertificateRequest:
    """Request parameters for creating a certificate.

    ``contract_id`` and ``group_id`` are query parameters; the actual
    JSON body is in the ``body`` field.

    Mirrors Go ``CreateCertificateRequest`` struct.
    """

    contract_id: str = ""
    group_id: str = ""
    body: CreateCertificateRequestBody | None = None

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(
        cls, data: dict | None
    ) -> CreateCertificateRequest | None:
        """Deserialise from a camelCase dict."""
        if not data:
            return None
        return cls(
            contract_id=data.get("contractId", ""),
            group_id=data.get("groupId", ""),
            body=CreateCertificateRequestBody.from_dict(
                data.get("body")
            ),
        )


@dataclass
class GetCertificateRequest:
    """Request parameters for retrieving a certificate.

    Mirrors Go ``GetCertificateRequest`` struct.
    """

    certificate_id: str = ""

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(
        cls, data: dict | None
    ) -> GetCertificateRequest | None:
        """Deserialise from a camelCase dict."""
        if not data:
            return None
        return cls(certificate_id=data.get("certificateId", ""))


@dataclass
class DeleteCertificateRequest:
    """Request parameters for deleting a certificate.

    Mirrors Go ``DeleteCertificateRequest`` struct.
    """

    certificate_id: str = ""

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(
        cls, data: dict | None
    ) -> DeleteCertificateRequest | None:
        """Deserialise from a camelCase dict."""
        if not data:
            return None
        return cls(certificate_id=data.get("certificateId", ""))


@dataclass
class PatchCertificateRequest:
    """Request parameters for patching (partial update of) a certificate.

    ``signed_certificate_pem`` and ``trust_chain_pem`` are Go value-type
    strings (empty == not provided).  ``certificate_name`` is a Go pointer
    (``None`` == don't change, ``""`` == reset to default).

    Mirrors Go ``PatchCertificateRequest`` struct.
    """

    certificate_id: str = ""
    signed_certificate_pem: str = ""
    trust_chain_pem: str = ""
    certificate_name: str | None = None
    acknowledge_warnings: bool = False

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(
        cls, data: dict | None
    ) -> PatchCertificateRequest | None:
        """Deserialise from a camelCase dict."""
        if not data:
            return None
        return cls(
            certificate_id=data.get("certificateId", ""),
            signed_certificate_pem=data.get(
                "signedCertificatePem", ""
            ),
            trust_chain_pem=data.get("trustChainPem", ""),
            certificate_name=data.get("certificateName"),
            acknowledge_warnings=data.get(
                "acknowledgeWarnings", False
            ),
        )


@dataclass
class UpdateCertificateRequest:
    """Request parameters for updating (full replacement of) a certificate.

    Field semantics match :class:`PatchCertificateRequest`.

    Mirrors Go ``UpdateCertificateRequest`` struct.
    """

    certificate_id: str = ""
    signed_certificate_pem: str = ""
    trust_chain_pem: str = ""
    certificate_name: str | None = None
    acknowledge_warnings: bool = False

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(
        cls, data: dict | None
    ) -> UpdateCertificateRequest | None:
        """Deserialise from a camelCase dict."""
        if not data:
            return None
        return cls(
            certificate_id=data.get("certificateId", ""),
            signed_certificate_pem=data.get(
                "signedCertificatePem", ""
            ),
            trust_chain_pem=data.get("trustChainPem", ""),
            certificate_name=data.get("certificateName"),
            acknowledge_warnings=data.get(
                "acknowledgeWarnings", False
            ),
        )


@dataclass
class ListCertificatesRequest:  # pylint: disable=too-many-instance-attributes
    """Request parameters for listing certificates.

    Mirrors Go ``ListCertificatesRequest`` struct.
    """

    contract_id: str = ""
    group_id: str = ""
    certificate_status: list[str] = field(default_factory=list)
    expiring_in_days: int | None = None
    domain: str = ""
    certificate_name: str = ""
    key_type: str = ""
    issuer: str = ""
    include_certificate_materials: bool = False
    page_size: int = 0
    page: int = 0
    sort: str = ""

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(
        cls, data: dict | None
    ) -> ListCertificatesRequest | None:
        """Deserialise from a camelCase dict."""
        if not data:
            return None
        return cls(
            contract_id=data.get("contractId", ""),
            group_id=data.get("groupId", ""),
            certificate_status=data.get("certificateStatus") or [],
            expiring_in_days=data.get("expiringInDays"),
            domain=data.get("domain", ""),
            certificate_name=data.get("certificateName", ""),
            key_type=data.get("keyType", ""),
            issuer=data.get("issuer", ""),
            include_certificate_materials=data.get(
                "includeCertificateMaterials", False
            ),
            page_size=data.get("pageSize", 0),
            page=data.get("page", 0),
            sort=data.get("sort", ""),
        )


@dataclass
class ListCertificateBindingsRequest:
    """Request parameters for listing certificate bindings.

    Mirrors Go ``ListCertificateBindingsRequest`` struct.
    """

    certificate_id: str = ""
    page: int = 0
    page_size: int = 0

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(
        cls, data: dict | None
    ) -> ListCertificateBindingsRequest | None:
        """Deserialise from a camelCase dict."""
        if not data:
            return None
        return cls(
            certificate_id=data.get("certificateId", ""),
            page=data.get("page", 0),
            page_size=data.get("pageSize", 0),
        )


@dataclass
class ListBindingsRequest:
    """Request parameters for listing all certificate bindings.

    Mirrors Go ``ListBindingsRequest`` struct.
    """

    contract_id: str = ""
    group_id: str = ""
    domain: str = ""
    network: str = ""
    expiring_in_days: int | None = None
    page_size: int = 0
    page: int = 0

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(
        cls, data: dict | None
    ) -> ListBindingsRequest | None:
        """Deserialise from a camelCase dict."""
        if not data:
            return None
        return cls(
            contract_id=data.get("contractId", ""),
            group_id=data.get("groupId", ""),
            domain=data.get("domain", ""),
            network=data.get("network", ""),
            expiring_in_days=data.get("expiringInDays"),
            page_size=data.get("pageSize", 0),
            page=data.get("page", 0),
        )


# ---------------------------------------------------------------------------
# Response types
# ---------------------------------------------------------------------------


@dataclass
class CreateCertificateResponse:
    """Response for certificate creation.

    The ``certificate`` field is parsed from the JSON response body.
    ``resource_limits_metadata`` and ``rate_limits_metadata`` are
    extracted from HTTP response headers by the client layer.

    Mirrors Go ``CreateCertificateResponse`` struct (embedded
    ``Certificate`` plus metadata).
    """

    certificate: Certificate | None = None
    resource_limits_metadata: ResourceLimitsMetadata | None = None
    rate_limits_metadata: RateLimitsMetadata | None = None

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(
        cls, data: dict | None
    ) -> CreateCertificateResponse | None:
        """Deserialise from a camelCase dict.

        ``data`` may contain the certificate fields at the top level
        (as Go embeds the struct), plus an optional
        ``resourceLimitsMetadata`` and ``rateLimitsMetadata`` key.
        """
        if not data:
            return None
        rlm_raw = data.get("resourceLimitsMetadata")
        rlm = ResourceLimitsMetadata.from_dict(rlm_raw)
        rate_raw = data.get("rateLimitsMetadata")
        rate = RateLimitsMetadata.from_dict(rate_raw)
        cert = Certificate.from_dict(data)
        return cls(
            certificate=cert,
            resource_limits_metadata=rlm,
            rate_limits_metadata=rate,
        )


@dataclass
class GetCertificateResponse:
    """Response for retrieving a certificate.

    Mirrors Go ``GetCertificateResponse`` struct.
    """

    certificate: Certificate | None = None
    rate_limits_metadata: RateLimitsMetadata | None = None

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(
        cls, data: dict | None
    ) -> GetCertificateResponse | None:
        """Deserialise from a camelCase dict."""
        if not data:
            return None
        rate_raw = data.get("rateLimitsMetadata")
        rate = RateLimitsMetadata.from_dict(rate_raw)
        cert = Certificate.from_dict(data)
        return cls(certificate=cert, rate_limits_metadata=rate)


@dataclass
class PatchCertificateResponse:
    """Response for patching a certificate.

    Mirrors Go ``PatchCertificateResponse`` struct.
    """

    certificate: Certificate | None = None
    rate_limits_metadata: RateLimitsMetadata | None = None

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(
        cls, data: dict | None
    ) -> PatchCertificateResponse | None:
        """Deserialise from a camelCase dict."""
        if not data:
            return None
        rate_raw = data.get("rateLimitsMetadata")
        rate = RateLimitsMetadata.from_dict(rate_raw)
        cert = Certificate.from_dict(data)
        return cls(certificate=cert, rate_limits_metadata=rate)


@dataclass
class UpdateCertificateResponse:
    """Response for updating a certificate.

    Mirrors Go ``UpdateCertificateResponse`` struct.
    """

    certificate: Certificate | None = None
    rate_limits_metadata: RateLimitsMetadata | None = None

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(
        cls, data: dict | None
    ) -> UpdateCertificateResponse | None:
        """Deserialise from a camelCase dict."""
        if not data:
            return None
        rate_raw = data.get("rateLimitsMetadata")
        rate = RateLimitsMetadata.from_dict(rate_raw)
        cert = Certificate.from_dict(data)
        return cls(certificate=cert, rate_limits_metadata=rate)


# DeleteCertificateResponse is a type alias for RateLimitsMetadata.
# In Go: ``type DeleteCertificateResponse = RateLimitsMetadata``.
DeleteCertificateResponse = RateLimitsMetadata


@dataclass
class ListCertificatesResponse:
    """Response for listing certificates.

    Mirrors Go ``ListCertificatesResponse`` struct.
    """

    certificates: list[Certificate] = field(default_factory=list)
    links: Links | None = None
    metadata: ListMetadata | None = None
    rate_limits: RateLimitsMetadata | None = None

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(
        cls, data: dict | None
    ) -> ListCertificatesResponse | None:
        """Deserialise from a camelCase dict."""
        if not data:
            return None
        raw_certs = data.get("certificates") or []
        certs = [
            c
            for raw in raw_certs
            if (c := Certificate.from_dict(raw)) is not None
        ]
        return cls(
            certificates=certs,
            links=Links.from_dict(data.get("links")),
            metadata=ListMetadata.from_dict(data.get("metadata")),
            rate_limits=RateLimitsMetadata.from_dict(
                data.get("rateLimitsMetadata")
            ),
        )


@dataclass
class ListCertificateBindingsResponse:
    """Response for listing certificate bindings.

    Mirrors Go ``ListCertificateBindingsResponse`` struct.
    """

    bindings: list[CertificateBinding] = field(default_factory=list)
    links: Links | None = None

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(
        cls, data: dict | None
    ) -> ListCertificateBindingsResponse | None:
        """Deserialise from a camelCase dict."""
        if not data:
            return None
        raw_bindings = data.get("bindings") or []
        bindings = [
            b
            for raw in raw_bindings
            if (b := CertificateBinding.from_dict(raw)) is not None
        ]
        return cls(
            bindings=bindings,
            links=Links.from_dict(data.get("links")),
        )


@dataclass
class ListBindingsResponse:
    """Response for listing all bindings.

    Mirrors Go ``ListBindingsResponse`` struct.
    """

    bindings: list[CertificateBinding] = field(default_factory=list)
    links: Links | None = None

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict."""
        return _model_to_dict(self)

    @classmethod
    def from_dict(
        cls, data: dict | None
    ) -> ListBindingsResponse | None:
        """Deserialise from a camelCase dict."""
        if not data:
            return None
        raw_bindings = data.get("bindings") or []
        bindings = [
            b
            for raw in raw_bindings
            if (b := CertificateBinding.from_dict(raw)) is not None
        ]
        return cls(
            bindings=bindings,
            links=Links.from_dict(data.get("links")),
        )
