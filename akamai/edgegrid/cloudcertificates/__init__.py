"""Cloud Certificates API client for Akamai CCM (Cloud Certificate Manager).

Provides the :class:`Client` class with all eight Cloud Certificates API
endpoint methods, service-specific error types and sentinel constants,
and all request/response model dataclasses.

Ported from Go ``pkg/cloudcertificates/cloudcertificates.go``.

Usage::

    from akamai.edgegrid.cloudcertificates import Client
    from akamai.edgegrid.cloudcertificates import (
        CreateCertificateRequest, CreateCertificateResponse,
        Error, ErrGetCertificate,
    )
"""

from akamai.edgegrid.cloudcertificates.cloudcertificates import Client
from akamai.edgegrid.cloudcertificates.errors import (
    Error,
    ErrStructValidation,
    ErrPatchCertificate,
    ErrUpdateCertificate,
    ErrListCertificates,
    ErrCreateCertificate,
    ErrGetCertificate,
    ErrDeleteCertificate,
    ErrListCertificateBindings,
    ErrListBindings,
    ErrCertificateNameInUse,
    ErrCertificateNotFound,
    ErrCertificateResourceNotFound,
    PEMValidation,
    SecondaryError,
    ValidationData,
    ValidationDetail,
    ValidationResult,
)
from akamai.edgegrid.cloudcertificates.models import (
    # Constants
    StatusActive,
    StatusReadyForUse,
    StatusCSRReady,
    CryptographicAlgorithmRSA,
    CryptographicAlgorithmECDSA,
    SecureNetworkEnhancedTLS,
    KeySize2048,
    KeySizeP256,
    NetworkStaging,
    NetworkProduction,
    SortFieldPat,
    # Type aliases
    CertificateStatus,
    CryptographicAlgorithm,
    SecureNetwork,
    KeySize,
    Network,
    # Domain types
    Certificate,
    Subject,
    CertificateBinding,
    Links,
    ListMetadata,
    ResourceLimitsMetadata,
    RateLimitsMetadata,
    # Request body type
    CreateCertificateRequestBody,
    # Request types
    CreateCertificateRequest,
    GetCertificateRequest,
    PatchCertificateRequest,
    UpdateCertificateRequest,
    DeleteCertificateRequest,
    ListCertificatesRequest,
    ListCertificateBindingsRequest,
    ListBindingsRequest,
    # Response types
    CreateCertificateResponse,
    GetCertificateResponse,
    PatchCertificateResponse,
    UpdateCertificateResponse,
    DeleteCertificateResponse,
    ListCertificatesResponse,
    ListCertificateBindingsResponse,
    ListBindingsResponse,
)

__all__ = [
    # Client
    "Client",
    # Errors
    "Error",
    "ErrStructValidation",
    "ErrPatchCertificate",
    "ErrUpdateCertificate",
    "ErrListCertificates",
    "ErrCreateCertificate",
    "ErrGetCertificate",
    "ErrDeleteCertificate",
    "ErrListCertificateBindings",
    "ErrListBindings",
    "ErrCertificateNameInUse",
    "ErrCertificateNotFound",
    "ErrCertificateResourceNotFound",
    "PEMValidation",
    "SecondaryError",
    "ValidationData",
    "ValidationDetail",
    "ValidationResult",
    # Model constants
    "StatusActive",
    "StatusReadyForUse",
    "StatusCSRReady",
    "CryptographicAlgorithmRSA",
    "CryptographicAlgorithmECDSA",
    "SecureNetworkEnhancedTLS",
    "KeySize2048",
    "KeySizeP256",
    "NetworkStaging",
    "NetworkProduction",
    "SortFieldPat",
    # Type aliases
    "CertificateStatus",
    "CryptographicAlgorithm",
    "SecureNetwork",
    "KeySize",
    "Network",
    # Domain types
    "Certificate",
    "Subject",
    "CertificateBinding",
    "Links",
    "ListMetadata",
    "ResourceLimitsMetadata",
    "RateLimitsMetadata",
    # Request body type
    "CreateCertificateRequestBody",
    # Request types
    "CreateCertificateRequest",
    "GetCertificateRequest",
    "PatchCertificateRequest",
    "UpdateCertificateRequest",
    "DeleteCertificateRequest",
    "ListCertificatesRequest",
    "ListCertificateBindingsRequest",
    "ListBindingsRequest",
    # Response types
    "CreateCertificateResponse",
    "GetCertificateResponse",
    "PatchCertificateResponse",
    "UpdateCertificateResponse",
    "DeleteCertificateResponse",
    "ListCertificatesResponse",
    "ListCertificateBindingsResponse",
    "ListBindingsResponse",
]
