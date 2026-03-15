# pylint: disable=too-many-instance-attributes,invalid-name
"""Request/response models for the mTLS Key Store API."""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Geography constants (from client_certificates.go lines 135-143)
# ---------------------------------------------------------------------------

GeographyCore = "CORE"
GeographyRussiaAndCore = "RUSSIA_AND_CORE"
GeographyChinaAndCore = "CHINA_AND_CORE"

# ---------------------------------------------------------------------------
# CryptographicAlgorithm constants (from client_certificates.go lines 145-149)
# ---------------------------------------------------------------------------

KeyAlgorithmRSA = "RSA"
KeyAlgorithmECDSA = "ECDSA"

# ---------------------------------------------------------------------------
# SecureNetwork constants (from client_certificates.go lines 151-155)
# ---------------------------------------------------------------------------

SecureNetworkStandardTLS = "STANDARD_TLS"
SecureNetworkEnhancedTLS = "ENHANCED_TLS"

# ---------------------------------------------------------------------------
# Signer constants (from client_certificates.go lines 157-161)
# ---------------------------------------------------------------------------

SignerAkamai = "AKAMAI"
SignerThirdParty = "THIRD_PARTY"

# ---------------------------------------------------------------------------
# CertificateStatus constants (from account_ca_certificates.go lines 82-94)
# ---------------------------------------------------------------------------

CertificateStatusCurrent = "CURRENT"
CertificateStatusExpired = "EXPIRED"
CertificateStatusPrevious = "PREVIOUS"
CertificateStatusQualifying = "QUALIFYING"

# ---------------------------------------------------------------------------
# CertificateVersionStatus constants
# (from client_certificate_versions.go lines 259-271)
# ---------------------------------------------------------------------------

CertificateVersionStatusAwaitingSigned = "AWAITING_SIGNED_CERTIFICATE"
CertificateVersionStatusDeploymentPending = "DEPLOYMENT_PENDING"
CertificateVersionStatusDeployed = "DEPLOYED"
CertificateVersionStatusDeletePending = "DELETE_PENDING"

# ---------------------------------------------------------------------------
# Client Certificate models (from client_certificates.go)
# ---------------------------------------------------------------------------


@dataclass
class Certificate:
    """A single client certificate."""

    certificate_id: int = 0
    certificate_name: str = ""
    created_by: str = ""
    created_date: str = ""
    geography: str = ""
    key_algorithm: str = ""
    notification_emails: list[str] = field(default_factory=list)
    secure_network: str = ""
    signer: str = ""
    subject: str = ""


@dataclass
class ListClientCertificatesResponse:
    """Response from ListClientCertificates API."""

    certificates: list[Certificate] = field(default_factory=list)


@dataclass
class GetClientCertificateRequest:
    """Request to get a client certificate."""

    certificate_id: int = 0


@dataclass
class GetClientCertificateResponse:
    """Response from GetClientCertificate API. Same fields as Certificate."""

    certificate_id: int = 0
    certificate_name: str = ""
    created_by: str = ""
    created_date: str = ""
    geography: str = ""
    key_algorithm: str = ""
    notification_emails: list[str] = field(default_factory=list)
    secure_network: str = ""
    signer: str = ""
    subject: str = ""


@dataclass
class CreateClientCertificateRequest:
    """Request to create a client certificate."""

    certificate_name: str = ""
    contract_id: str = ""
    geography: str = ""
    group_id: int = 0
    key_algorithm: str | None = None
    notification_emails: list[str] = field(default_factory=list)
    preferred_ca: str | None = None
    secure_network: str = ""
    signer: str = ""
    subject: str | None = None


@dataclass
class CreateClientCertificateResponse:
    """Response from CreateClientCertificate API. Same fields as Certificate."""

    certificate_id: int = 0
    certificate_name: str = ""
    created_by: str = ""
    created_date: str = ""
    geography: str = ""
    key_algorithm: str = ""
    notification_emails: list[str] = field(default_factory=list)
    secure_network: str = ""
    signer: str = ""
    subject: str = ""


@dataclass
class PatchClientCertificateRequestBody:
    """Body of PatchClientCertificate request."""

    certificate_name: str | None = None
    notification_emails: list[str] | None = None


@dataclass
class PatchClientCertificateRequest:
    """Request to update client certificate name or notification emails."""

    certificate_id: int = 0
    body: PatchClientCertificateRequestBody = field(
        default_factory=PatchClientCertificateRequestBody
    )


# ---------------------------------------------------------------------------
# Client Certificate Version models
# (from client_certificate_versions.go)
# ---------------------------------------------------------------------------


@dataclass
class RotateClientCertificateVersionRequest:
    """Request to create a new client certificate version."""

    certificate_id: int = 0


@dataclass
class CertificateBlock:
    """Certificate block for THIRD_PARTY client certificates."""

    certificate: str = ""
    key_algorithm: str = ""
    trust_chain: str = ""


@dataclass
class CSRBlock:
    """Certificate Signing Request for THIRD_PARTY client certificates."""

    csr: str = ""
    key_algorithm: str = ""


@dataclass
class ValidationDetail:
    """Individual validation error or warning."""

    message: str = ""
    reason: str = ""
    type: str = ""


@dataclass
class ValidationResult:
    """Holds validation errors and warnings."""

    errors: list[ValidationDetail] = field(default_factory=list)
    warnings: list[ValidationDetail] = field(default_factory=list)


@dataclass
class AssociatedProperty:
    """Property associated with a client certificate version."""

    asset_id: int = 0
    group_id: int = 0
    property_name: str = ""
    property_version: int = 0


@dataclass
class RotateClientCertificateVersionResponse:
    """Response from creating a new client certificate version."""

    version: int = 0
    version_guid: str = ""
    version_alias: str | None = None
    certificate_block: CertificateBlock | None = None
    created_by: str = ""
    created_date: str = ""
    csr_block: CSRBlock | None = None
    expiry_date: str | None = None
    issued_date: str | None = None
    issuer: str | None = None
    key_algorithm: str = ""
    elliptic_curve: str | None = None
    key_size_in_bytes: str | None = None
    signature_algorithm: str | None = None
    status: str = ""
    subject: str | None = None


@dataclass
class ListClientCertificateVersionsRequest:
    """Request to list client certificate versions."""

    certificate_id: int = 0
    include_associated_properties: bool = False


@dataclass
class ListClientCertificateVersionsResponse:
    """Response from listing client certificate versions."""

    versions: list[ClientCertificateVersion] = field(default_factory=list)


@dataclass
class ClientCertificateVersion:
    """A version of a client certificate."""

    version: int = 0
    version_guid: str = ""
    version_alias: str | None = None
    certificate_block: CertificateBlock | None = None
    certificate_submitted_by: str | None = None
    certificate_submitted_date: str | None = None
    created_by: str = ""
    created_date: str = ""
    csr_block: CSRBlock | None = None
    delete_requested_date: str | None = None
    expiry_date: str | None = None
    issued_date: str | None = None
    issuer: str | None = None
    key_algorithm: str = ""
    elliptic_curve: str | None = None
    key_size_in_bytes: str | None = None
    scheduled_delete_date: str | None = None
    signature_algorithm: str | None = None
    status: str = ""
    subject: str | None = None
    validation: ValidationResult = field(
        default_factory=ValidationResult
    )
    associated_properties: list[AssociatedProperty] = field(
        default_factory=list
    )


@dataclass
class DeleteClientCertificateVersionRequest:
    """Request to delete a client certificate version."""

    certificate_id: int = 0
    version: int = 0


@dataclass
class DeleteClientCertificateVersionResponse:
    """Response from deleting a client certificate version."""

    message: str = ""


@dataclass
class UploadSignedClientCertificateRequestBody:
    """Body for UploadSignedClientCertificate request."""

    certificate: str = ""
    trust_chain: str | None = None


@dataclass
class UploadSignedClientCertificateRequest:
    """Request to upload a signed client certificate."""

    certificate_id: int = 0
    version: int = 0
    acknowledge_all_warnings: bool | None = None
    body: UploadSignedClientCertificateRequestBody = field(
        default_factory=UploadSignedClientCertificateRequestBody
    )


# ---------------------------------------------------------------------------
# Account CA Certificate models (from account_ca_certificates.go)
# ---------------------------------------------------------------------------


@dataclass
class ListAccountCACertificatesRequest:
    """Request to list account CA certificates."""

    status: list[str] = field(default_factory=list)


@dataclass
class AccountCACertificate:  # pylint: disable=redefined-builtin
    """A CA certificate under the account."""

    account_id: str = ""
    certificate: str = ""
    common_name: str = ""
    created_by: str = ""
    created_date: str = ""
    expiry_date: str = ""
    id: int = 0
    issued_date: str = ""
    key_algorithm: str = ""
    key_size_in_bytes: int = 0
    qualification_date: str | None = None
    signature_algorithm: str = ""
    status: str = ""
    subject: str = ""
    version: int = 0


@dataclass
class ListAccountCACertificatesResponse:
    """Response from ListAccountCACertificates."""

    certificates: list[AccountCACertificate] = field(default_factory=list)
