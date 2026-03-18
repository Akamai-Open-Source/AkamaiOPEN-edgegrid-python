"""Cloud Access Manager API client package.

Provides access to the Akamai Cloud Access Manager API for managing
access keys, versions, and property lookups.

Mirrors the Go ``pkg/cloudaccess`` package public API surface.

Usage::

    >>> from akamai.edgegrid.cloudaccess import CloudAccessClient
    >>> from akamai.edgegrid.session import Session
    >>> session = Session(edgerc_path="~/.edgerc", section="cloudaccess")
    >>> client = CloudAccessClient(session)
    >>> keys = client.list_access_keys(ListAccessKeysRequest())
"""

# pylint: disable=redefined-builtin
from akamai.edgegrid.cloudaccess.cloudaccess import CloudAccessClient
from akamai.edgegrid.cloudaccess.errors import (
    Error,
    ErrorItem,
    ErrAccessKeyNotFound,
    ErrCreateAccessKey,
    ErrCreateAccessKeyVersion,
    ErrDeleteAccessKey,
    ErrDeleteAccessKeyVersion,
    ErrGetAccessKey,
    ErrGetAccessKeyStatus,
    ErrGetAccessKeyVersion,
    ErrGetAccessKeyVersionStatus,
    ErrGetAsyncLookupIDProperties,
    ErrListAccessKeyVersions,
    ErrLookupProperties,
    ErrPerformAsyncLookupProperties,
    ErrUpdateAccessKey,
)
from akamai.edgegrid.cloudaccess.models import (
    # Shared model types
    AccessKeyVersion,
    Credentials,
    Group,
    KeyLink,
    KeyVersion,
    Property,
    RequestInformation,
    SecureNetwork,
    # CDNType constants
    ChinaCDN,
    RussiaCDN,
    # NetworkType constants
    NetworkEnhanced,
    NetworkStandard,
    # AuthType constants
    AuthAOS,
    AuthAVMCloudinary,
    AuthAWS,
    AuthGOOG,
    # ProcessingType constants
    ProcessingDone,
    ProcessingFailed,
    ProcessingInProgress,
    # DeploymentStatus constants
    Active,
    PendingActivation,
    PendingDeletion,
    # LookupStatus constants
    LookupComplete,
    LookupError,
    LookupInProgress,
    LookupPending,
    LookupSubmitted,
    # Request types
    AccessKeyRequest,
    CreateAccessKeyRequest,
    CreateAccessKeyVersionRequest,
    CreateAccessKeyVersionRequestBody,
    DeleteAccessKeyVersionRequest,
    GetAccessKeyStatusRequest,
    GetAccessKeyVersionRequest,
    GetAccessKeyVersionStatusRequest,
    GetAsyncPropertiesLookupIDRequest,
    ListAccessKeysRequest,
    ListAccessKeyVersionsRequest,
    LookupPropertiesRequest,
    PerformAsyncPropertiesLookupRequest,
    UpdateAccessKeyRequest,
    # Response types
    AccessKeyResponse,
    CreateAccessKeyResponse,
    CreateAccessKeyVersionResponse,
    DeleteAccessKeyVersionResponse,
    GetAccessKeyResponse,
    GetAccessKeyStatusResponse,
    GetAccessKeyVersionResponse,
    GetAccessKeyVersionStatusResponse,
    GetAsyncPropertiesLookupIDResponse,
    ListAccessKeysResponse,
    ListAccessKeyVersionsResponse,
    LookupPropertiesResponse,
    PerformAsyncPropertiesLookupResponse,
    UpdateAccessKeyResponse,
)

__all__ = [
    # Client
    "CloudAccessClient",
    # Error types and sentinels
    "Error",
    "ErrorItem",
    "ErrAccessKeyNotFound",
    "ErrCreateAccessKey",
    "ErrCreateAccessKeyVersion",
    "ErrDeleteAccessKey",
    "ErrDeleteAccessKeyVersion",
    "ErrGetAccessKey",
    "ErrGetAccessKeyStatus",
    "ErrGetAccessKeyVersion",
    "ErrGetAccessKeyVersionStatus",
    "ErrGetAsyncLookupIDProperties",
    "ErrListAccessKeyVersions",
    "ErrLookupProperties",
    "ErrPerformAsyncLookupProperties",
    "ErrUpdateAccessKey",
    # Shared model types
    "AccessKeyVersion",
    "Credentials",
    "Group",
    "KeyLink",
    "KeyVersion",
    "Property",
    "RequestInformation",
    "SecureNetwork",
    # CDNType constants
    "ChinaCDN",
    "RussiaCDN",
    # NetworkType constants
    "NetworkEnhanced",
    "NetworkStandard",
    # AuthType constants
    "AuthAOS",
    "AuthAVMCloudinary",
    "AuthAWS",
    "AuthGOOG",
    # ProcessingType constants
    "ProcessingDone",
    "ProcessingFailed",
    "ProcessingInProgress",
    # DeploymentStatus constants
    "Active",
    "PendingActivation",
    "PendingDeletion",
    # LookupStatus constants
    "LookupComplete",
    "LookupError",
    "LookupInProgress",
    "LookupPending",
    "LookupSubmitted",
    # Request types
    "AccessKeyRequest",
    "CreateAccessKeyRequest",
    "CreateAccessKeyVersionRequest",
    "CreateAccessKeyVersionRequestBody",
    "DeleteAccessKeyVersionRequest",
    "GetAccessKeyStatusRequest",
    "GetAccessKeyVersionRequest",
    "GetAccessKeyVersionStatusRequest",
    "GetAsyncPropertiesLookupIDRequest",
    "ListAccessKeysRequest",
    "ListAccessKeyVersionsRequest",
    "LookupPropertiesRequest",
    "PerformAsyncPropertiesLookupRequest",
    "UpdateAccessKeyRequest",
    # Response types
    "AccessKeyResponse",
    "CreateAccessKeyResponse",
    "CreateAccessKeyVersionResponse",
    "DeleteAccessKeyVersionResponse",
    "GetAccessKeyResponse",
    "GetAccessKeyStatusResponse",
    "GetAccessKeyVersionResponse",
    "GetAccessKeyVersionStatusResponse",
    "GetAsyncPropertiesLookupIDResponse",
    "ListAccessKeysResponse",
    "ListAccessKeyVersionsResponse",
    "LookupPropertiesResponse",
    "PerformAsyncPropertiesLookupResponse",
    "UpdateAccessKeyResponse",
]
