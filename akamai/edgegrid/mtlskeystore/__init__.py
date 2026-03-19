"""Akamai mTLS Key Store API client package.

Provides the ``Client`` class and all request/response models for
managing client certificates, certificate versions, and account CA
certificates in the Akamai mTLS Origin Key Store.

Mirrors Go ``pkg/mtlskeystore`` package surface.

Usage example::

    from akamai.edgegrid import EdgeGridAuth, EdgeRc
    from akamai.edgegrid.session import Session
    from akamai.edgegrid.mtlskeystore import (
        Client,
        GetClientCertificateRequest,
    )

    edgerc = EdgeRc("~/.edgerc")
    session = Session(edgerc=edgerc, section="default")
    client = Client(session)
    response = client.list_client_certificates()
"""

from akamai.edgegrid.mtlskeystore.mtlskeystore import Client
from akamai.edgegrid.mtlskeystore.models import (
    AccountCACertificate,
    AssociatedProperty,
    Certificate,
    CertificateBlock,
    CertificateStatusCurrent,
    CertificateStatusExpired,
    CertificateStatusPrevious,
    CertificateStatusQualifying,
    CertificateVersionStatusAwaitingSigned,
    CertificateVersionStatusDeletePending,
    CertificateVersionStatusDeployed,
    CertificateVersionStatusDeploymentPending,
    ClientCertificateVersion,
    CreateClientCertificateRequest,
    CreateClientCertificateResponse,
    CSRBlock,
    DeleteClientCertificateVersionRequest,
    DeleteClientCertificateVersionResponse,
    GeographyChinaAndCore,
    GeographyCore,
    GeographyRussiaAndCore,
    GetClientCertificateRequest,
    GetClientCertificateResponse,
    KeyAlgorithmECDSA,
    KeyAlgorithmRSA,
    ListAccountCACertificatesRequest,
    ListAccountCACertificatesResponse,
    ListClientCertificatesResponse,
    ListClientCertificateVersionsRequest,
    ListClientCertificateVersionsResponse,
    PatchClientCertificateRequest,
    PatchClientCertificateRequestBody,
    RotateClientCertificateVersionRequest,
    RotateClientCertificateVersionResponse,
    SecureNetworkEnhancedTLS,
    SecureNetworkStandardTLS,
    SignerAkamai,
    SignerThirdParty,
    UploadSignedClientCertificateRequest,
    UploadSignedClientCertificateRequestBody,
    ValidationDetail,
    ValidationResult,
)
from akamai.edgegrid.mtlskeystore.errors import (
    Error,
    ErrClientCertificateNotFound,
    ErrCreateClientCertificate,
    ErrDeleteClientCertificateVersion,
    ErrDuplicateClientCertificate,
    ErrGetClientCertificate,
    ErrInvalidClientCertificate,
    ErrListAccountCACertificates,
    ErrListClientCertificates,
    ErrListClientCertificateVersions,
    ErrPatchClientCertificate,
    ErrRotateClientCertificateVersion,
    ErrStructValidation,
    ErrUploadClientCertificateVersion,
)

__all__ = [
    # Client
    "Client",
    # Model classes
    "AccountCACertificate",
    "AssociatedProperty",
    "Certificate",
    "CertificateBlock",
    "ClientCertificateVersion",
    "CreateClientCertificateRequest",
    "CreateClientCertificateResponse",
    "CSRBlock",
    "DeleteClientCertificateVersionRequest",
    "DeleteClientCertificateVersionResponse",
    "GetClientCertificateRequest",
    "GetClientCertificateResponse",
    "ListAccountCACertificatesRequest",
    "ListAccountCACertificatesResponse",
    "ListClientCertificatesResponse",
    "ListClientCertificateVersionsRequest",
    "ListClientCertificateVersionsResponse",
    "PatchClientCertificateRequest",
    "PatchClientCertificateRequestBody",
    "RotateClientCertificateVersionRequest",
    "RotateClientCertificateVersionResponse",
    "UploadSignedClientCertificateRequest",
    "UploadSignedClientCertificateRequestBody",
    "ValidationDetail",
    "ValidationResult",
    # Geography constants
    "GeographyChinaAndCore",
    "GeographyCore",
    "GeographyRussiaAndCore",
    # Key algorithm constants
    "KeyAlgorithmECDSA",
    "KeyAlgorithmRSA",
    # Secure network constants
    "SecureNetworkEnhancedTLS",
    "SecureNetworkStandardTLS",
    # Signer constants
    "SignerAkamai",
    "SignerThirdParty",
    # Certificate status constants
    "CertificateStatusCurrent",
    "CertificateStatusExpired",
    "CertificateStatusPrevious",
    "CertificateStatusQualifying",
    # Certificate version status constants
    "CertificateVersionStatusAwaitingSigned",
    "CertificateVersionStatusDeletePending",
    "CertificateVersionStatusDeployed",
    "CertificateVersionStatusDeploymentPending",
    # Error class
    "Error",
    # Sentinel error constants
    "ErrClientCertificateNotFound",
    "ErrCreateClientCertificate",
    "ErrDeleteClientCertificateVersion",
    "ErrDuplicateClientCertificate",
    "ErrGetClientCertificate",
    "ErrInvalidClientCertificate",
    "ErrListAccountCACertificates",
    "ErrListClientCertificates",
    "ErrListClientCertificateVersions",
    "ErrPatchClientCertificate",
    "ErrRotateClientCertificateVersion",
    "ErrStructValidation",
    "ErrUploadClientCertificateVersion",
]
