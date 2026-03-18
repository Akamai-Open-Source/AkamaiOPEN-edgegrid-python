"""Akamai EdgeWorkers and EdgeKV API client package.

Provides access to the Akamai EdgeWorkers and EdgeKV APIs including:
- EdgeWorker ID management (CRUD + clone)
- EdgeWorker version management (CRUD + content bundle)
- Activation and deactivation lifecycle
- EdgeKV namespace management (CRUD + scheduled deletion)
- EdgeKV access token management
- EdgeKV item operations (CRUD)
- EdgeKV group listing
- EdgeKV initialization
- Contract and resource tier queries
- Property queries
- Reporting (summary, detailed, list)
- Permission group queries
- Secure token creation
- Bundle validation
"""

# Client class -----------------------------------------------------------
from .edgeworkers import Client

# Error classes and parsing ----------------------------------------------
from .errors import (
    AdditionalDetail,
    Error as EdgeWorkersError,
    parse_edgeworkers_error,
)

# Error-code constants ---------------------------------------------------
from .errors import (
    ERROR_CODE_NOT_FOUND,
    ERROR_CODE_VERSION_ALREADY_DEACTIVATED,
    ERROR_CODE_VERSION_IS_BEING_DEACTIVATED,
)

# Semantic sentinel errors -----------------------------------------------
from .errors import (
    ErrNotFound,
    ErrVersionAlreadyDeactivated,
    ErrVersionBeingDeactivated,
)

# Operation sentinel errors — activations --------------------------------
from .errors import (
    ErrActivateVersion,
    ErrCancelActivation,
    ErrGetActivation,
    ErrListActivations,
)

# Operation sentinel errors — contracts ----------------------------------
from .errors import ErrListContracts

# Operation sentinel errors — deactivations ------------------------------
from .errors import (
    ErrDeactivateVersion,
    ErrGetDeactivation,
    ErrListDeactivations,
)

# Operation sentinel errors — EdgeKV access tokens -----------------------
from .errors import (
    ErrCreateEdgeKVAccessToken,
    ErrDeleteEdgeKVAccessToken,
    ErrGetEdgeKVAccessToken,
    ErrListEdgeKVAccessToken,
)

# Operation sentinel errors — EdgeKV groups ------------------------------
from .errors import ErrListGroupsWithinNamespace

# Operation sentinel errors — EdgeKV initialize --------------------------
from .errors import (
    ErrGetEdgeKVInitialize,
    ErrInitializeEdgeKV,
)

# Operation sentinel errors — EdgeKV items -------------------------------
from .errors import (
    ErrDeleteItem,
    ErrGetItem,
    ErrListItems,
    ErrUpsertItem,
)

# Operation sentinel errors — EdgeKV namespaces --------------------------
from .errors import (
    ErrCancelScheduledNamespaceDelete,
    ErrCreateEdgeKVNamespace,
    ErrDeleteEdgeKVNamespace,
    ErrGetEdgeKVNamespace,
    ErrGetScheduledDeleteTime,
    ErrListEdgeKVNamespace,
    ErrRescheduleNamespaceDelete,
    ErrUpdateEdgeKVNamespace,
)

# Operation sentinel errors — EdgeWorker IDs -----------------------------
from .errors import (
    ErrCloneEdgeWorkerID,
    ErrCreateEdgeWorkerID,
    ErrDeleteEdgeWorkerID,
    ErrGetEdgeWorkerID,
    ErrListEdgeWorkersID,
    ErrUpdateEdgeWorkerID,
)

# Operation sentinel errors — EdgeWorker versions ------------------------
from .errors import (
    ErrCreateEdgeWorkerVersion,
    ErrDeleteEdgeWorkerVersion,
    ErrGetEdgeWorkerVersion,
    ErrGetEdgeWorkerVersionContent,
    ErrListEdgeWorkerVersions,
)

# Operation sentinel errors — permission groups --------------------------
from .errors import (
    ErrGetPermissionGroup,
    ErrListPermissionGroups,
)

# Operation sentinel errors — properties ---------------------------------
from .errors import ErrListProperties

# Operation sentinel errors — reports ------------------------------------
from .errors import (
    ErrGetReport,
    ErrGetSummaryReport,
    ErrListReports,
)

# Operation sentinel errors — resource tiers -----------------------------
from .errors import (
    ErrGetResourceTier,
    ErrListResourceTiers,
)

# Operation sentinel errors — secure tokens ------------------------------
from .errors import ErrCreateSecureToken

# Operation sentinel errors — validations --------------------------------
from .errors import ErrValidateBundle

# Model classes — activations --------------------------------------------
from .models import (
    Activation,
    ActivateVersion,
    ActivateVersionRequest,
    CancelActivationRequest,
    GetActivationRequest,
    ListActivationsRequest,
    ListActivationsResponse,
)

# Model classes — deactivations ------------------------------------------
from .models import (
    Deactivation,
    DeactivateVersion,
    DeactivateVersionRequest,
    GetDeactivationRequest,
    ListDeactivationsRequest,
    ListDeactivationsResponse,
)

# Model classes — contracts ----------------------------------------------
from .models import ListContractsResponse

# Model classes — EdgeKV access tokens -----------------------------------
from .models import (
    CreateEdgeKVAccessTokenRequest,
    CreateEdgeKVAccessTokenResponse,
    DeleteEdgeKVAccessTokenRequest,
    DeleteEdgeKVAccessTokenResponse,
    EdgeKVAccessToken,
    GetEdgeKVAccessTokenRequest,
    GetEdgeKVAccessTokenResponse,
    ListEdgeKVAccessTokensRequest,
    ListEdgeKVAccessTokensResponse,
)

# Model classes — EdgeKV groups ------------------------------------------
from .models import ListGroupsWithinNamespaceRequest

# Model classes — EdgeKV initialization ----------------------------------
from .models import EdgeKVInitializationStatus

# Model classes — EdgeKV items -------------------------------------------
from .models import (
    DeleteItemRequest,
    GetItemRequest,
    ItemsRequestParams,
    ListItemsRequest,
    UpsertItemRequest,
)

# Model classes — EdgeKV namespaces --------------------------------------
from .models import (
    CancelScheduledNamespaceDeleteRequest,
    CreateEdgeKVNamespaceRequest,
    DeleteEdgeKVNamespaceRequest,
    DeleteEdgeKVNamespacesResponse,
    GetEdgeKVNamespaceRequest,
    GetNamespaceResponse,
    GetScheduledDeleteTimeRequest,
    ListEdgeKVNamespacesRequest,
    Namespace,
    NamespaceRequest,
    RescheduleNamespaceDeleteRequest,
    RescheduleNamespaceDeleteResponse,
    ScheduledDeleteTimeRequest,
    ScheduledDeleteTimeResponse,
    UpdateEdgeKVNamespaceRequest,
    UpdateNamespace,
    UpdateNamespaceResponse,
)

# Model classes — EdgeWorker IDs -----------------------------------------
from .models import (
    CloneEdgeWorkerIDRequest,
    CreateEdgeWorkerIDRequest,
    DeleteEdgeWorkerIDRequest,
    EdgeWorkerID,
    EdgeWorkerIDRequestBody,
    GetEdgeWorkerIDRequest,
    ListEdgeWorkersIDRequest,
    ListEdgeWorkersIDResponse,
    UpdateEdgeWorkerIDRequest,
)

# Model classes — EdgeWorker versions ------------------------------------
from .models import (
    Bundle,
    CreateEdgeWorkerVersionRequest,
    DeleteEdgeWorkerVersionRequest,
    EdgeWorkerVersion,
    EdgeWorkerVersionRequest,
    GetEdgeWorkerVersionContentRequest,
    GetEdgeWorkerVersionRequest,
    ListEdgeWorkerVersionsRequest,
    ListEdgeWorkerVersionsResponse,
)

# Model classes — permission groups --------------------------------------
from .models import (
    GetPermissionGroupRequest,
    ListPermissionGroupsResponse,
    PermissionGroup,
)

# Model classes — properties ---------------------------------------------
from .models import (
    ListPropertiesRequest,
    ListPropertiesResponse,
    Property,
)

# Model classes — reports ------------------------------------------------
from .models import (
    Data,
    DataSummary,
    GetReportRequest,
    GetReportResponse,
    GetSummaryReportRequest,
    GetSummaryReportResponse,
    InitObject,
    ListReportsResponse,
    OnRequestAndResponse,
    ReportData,
    ReportResponse,
    Summary,
    Total,
)

# Model classes — resource tiers -----------------------------------------
from .models import (
    EdgeWorkerLimit,
    GetResourceTierRequest,
    ListResourceTiersRequest,
    ListResourceTiersResponse,
    ResourceTier,
)

# Model classes — secure tokens ------------------------------------------
from .models import (
    CreateSecureTokenRequest,
    CreateSecureTokenResponse,
)

# Model classes — validations --------------------------------------------
from .models import (
    ValidateBundleRequest,
    ValidateBundleResponse,
    ValidationIssue,
)

# Network constants ------------------------------------------------------
from .models import (
    ACTIVATION_NETWORK_PRODUCTION,
    ACTIVATION_NETWORK_STAGING,
    ITEM_PRODUCTION_NETWORK,
    ITEM_STAGING_NETWORK,
    NAMESPACE_PRODUCTION_NETWORK,
    NAMESPACE_STAGING_NETWORK,
)

# Permission constants ---------------------------------------------------
from .models import (
    PERMISSION_DELETE,
    PERMISSION_READ,
    PERMISSION_WRITE,
)

# Report status constants ------------------------------------------------
from .models import (
    STATUS_CPU_TIMEOUT_ERROR,
    STATUS_EXECUTION_ERROR,
    STATUS_GENERIC_ERROR,
    STATUS_INIT_CPU_TIMEOUT_ERROR,
    STATUS_INIT_WALL_TIMEOUT_ERROR,
    STATUS_RESOURCE_LIMIT_HIT,
    STATUS_RUNTIME_ERROR,
    STATUS_SUCCESS,
    STATUS_TIMEOUT_ERROR,
    STATUS_UNKNOWN_EDGE_WORKER_ID,
    STATUS_UNIMPLEMENTED_EVENT_HANDLER,
    STATUS_WALL_TIMEOUT_ERROR,
)

# Event handler constants ------------------------------------------------
from .models import (
    EVENT_HANDLER_ON_CLIENT_REQUEST,
    EVENT_HANDLER_ON_CLIENT_RESPONSE,
    EVENT_HANDLER_ON_ORIGIN_REQUEST,
    EVENT_HANDLER_ON_ORIGIN_RESPONSE,
    EVENT_HANDLER_RESPONSE_PROVIDER,
)

__all__ = [
    # Client
    "Client",
    # Error classes and parsing
    "EdgeWorkersError",
    "AdditionalDetail",
    "parse_edgeworkers_error",
    # Error-code constants
    "ERROR_CODE_NOT_FOUND",
    "ERROR_CODE_VERSION_IS_BEING_DEACTIVATED",
    "ERROR_CODE_VERSION_ALREADY_DEACTIVATED",
    # Semantic sentinel errors
    "ErrNotFound",
    "ErrVersionBeingDeactivated",
    "ErrVersionAlreadyDeactivated",
    # Operation sentinel errors — activations
    "ErrListActivations",
    "ErrGetActivation",
    "ErrActivateVersion",
    "ErrCancelActivation",
    # Operation sentinel errors — contracts
    "ErrListContracts",
    # Operation sentinel errors — deactivations
    "ErrListDeactivations",
    "ErrDeactivateVersion",
    "ErrGetDeactivation",
    # Operation sentinel errors — EdgeKV access tokens
    "ErrCreateEdgeKVAccessToken",
    "ErrGetEdgeKVAccessToken",
    "ErrListEdgeKVAccessToken",
    "ErrDeleteEdgeKVAccessToken",
    # Operation sentinel errors — EdgeKV groups
    "ErrListGroupsWithinNamespace",
    # Operation sentinel errors — EdgeKV initialize
    "ErrInitializeEdgeKV",
    "ErrGetEdgeKVInitialize",
    # Operation sentinel errors — EdgeKV items
    "ErrListItems",
    "ErrGetItem",
    "ErrUpsertItem",
    "ErrDeleteItem",
    # Operation sentinel errors — EdgeKV namespaces
    "ErrListEdgeKVNamespace",
    "ErrGetEdgeKVNamespace",
    "ErrCreateEdgeKVNamespace",
    "ErrUpdateEdgeKVNamespace",
    "ErrDeleteEdgeKVNamespace",
    "ErrGetScheduledDeleteTime",
    "ErrRescheduleNamespaceDelete",
    "ErrCancelScheduledNamespaceDelete",
    # Operation sentinel errors — EdgeWorker IDs
    "ErrGetEdgeWorkerID",
    "ErrListEdgeWorkersID",
    "ErrCreateEdgeWorkerID",
    "ErrUpdateEdgeWorkerID",
    "ErrCloneEdgeWorkerID",
    "ErrDeleteEdgeWorkerID",
    # Operation sentinel errors — EdgeWorker versions
    "ErrGetEdgeWorkerVersion",
    "ErrListEdgeWorkerVersions",
    "ErrGetEdgeWorkerVersionContent",
    "ErrCreateEdgeWorkerVersion",
    "ErrDeleteEdgeWorkerVersion",
    # Operation sentinel errors — permission groups
    "ErrGetPermissionGroup",
    "ErrListPermissionGroups",
    # Operation sentinel errors — properties
    "ErrListProperties",
    # Operation sentinel errors — reports
    "ErrGetSummaryReport",
    "ErrGetReport",
    "ErrListReports",
    # Operation sentinel errors — resource tiers
    "ErrListResourceTiers",
    "ErrGetResourceTier",
    # Operation sentinel errors — secure tokens
    "ErrCreateSecureToken",
    # Operation sentinel errors — validations
    "ErrValidateBundle",
    # Model classes — activations
    "ListActivationsRequest",
    "ActivateVersionRequest",
    "ActivateVersion",
    "GetActivationRequest",
    "CancelActivationRequest",
    "Activation",
    "ListActivationsResponse",
    # Model classes — deactivations
    "Deactivation",
    "ListDeactivationsRequest",
    "DeactivateVersion",
    "DeactivateVersionRequest",
    "GetDeactivationRequest",
    "ListDeactivationsResponse",
    # Model classes — contracts
    "ListContractsResponse",
    # Model classes — EdgeKV access tokens
    "CreateEdgeKVAccessTokenRequest",
    "EdgeKVAccessToken",
    "CreateEdgeKVAccessTokenResponse",
    "GetEdgeKVAccessTokenResponse",
    "GetEdgeKVAccessTokenRequest",
    "ListEdgeKVAccessTokensRequest",
    "ListEdgeKVAccessTokensResponse",
    "DeleteEdgeKVAccessTokenRequest",
    "DeleteEdgeKVAccessTokenResponse",
    # Model classes — EdgeKV groups
    "ListGroupsWithinNamespaceRequest",
    # Model classes — EdgeKV initialization
    "EdgeKVInitializationStatus",
    # Model classes — EdgeKV items
    "ItemsRequestParams",
    "ListItemsRequest",
    "GetItemRequest",
    "UpsertItemRequest",
    "DeleteItemRequest",
    # Model classes — EdgeKV namespaces
    "ListEdgeKVNamespacesRequest",
    "GetEdgeKVNamespaceRequest",
    "NamespaceRequest",
    "CreateEdgeKVNamespaceRequest",
    "UpdateNamespace",
    "UpdateEdgeKVNamespaceRequest",
    "Namespace",
    "GetNamespaceResponse",
    "UpdateNamespaceResponse",
    "DeleteEdgeKVNamespaceRequest",
    "DeleteEdgeKVNamespacesResponse",
    "GetScheduledDeleteTimeRequest",
    "ScheduledDeleteTimeResponse",
    "ScheduledDeleteTimeRequest",
    "RescheduleNamespaceDeleteRequest",
    "RescheduleNamespaceDeleteResponse",
    "CancelScheduledNamespaceDeleteRequest",
    # Model classes — EdgeWorker IDs
    "GetEdgeWorkerIDRequest",
    "DeleteEdgeWorkerIDRequest",
    "EdgeWorkerID",
    "ListEdgeWorkersIDRequest",
    "ListEdgeWorkersIDResponse",
    "CreateEdgeWorkerIDRequest",
    "EdgeWorkerIDRequestBody",
    "UpdateEdgeWorkerIDRequest",
    "CloneEdgeWorkerIDRequest",
    # Model classes — EdgeWorker versions
    "EdgeWorkerVersionRequest",
    "GetEdgeWorkerVersionRequest",
    "GetEdgeWorkerVersionContentRequest",
    "DeleteEdgeWorkerVersionRequest",
    "EdgeWorkerVersion",
    "ListEdgeWorkerVersionsRequest",
    "ListEdgeWorkerVersionsResponse",
    "CreateEdgeWorkerVersionRequest",
    "Bundle",
    # Model classes — permission groups
    "GetPermissionGroupRequest",
    "PermissionGroup",
    "ListPermissionGroupsResponse",
    # Model classes — properties
    "ListPropertiesRequest",
    "Property",
    "ListPropertiesResponse",
    # Model classes — reports
    "GetSummaryReportRequest",
    "Summary",
    "Total",
    "DataSummary",
    "GetSummaryReportResponse",
    "GetReportRequest",
    "OnRequestAndResponse",
    "InitObject",
    "Data",
    "ReportData",
    "GetReportResponse",
    "ReportResponse",
    "ListReportsResponse",
    # Model classes — resource tiers
    "ListResourceTiersRequest",
    "GetResourceTierRequest",
    "EdgeWorkerLimit",
    "ResourceTier",
    "ListResourceTiersResponse",
    # Model classes — secure tokens
    "CreateSecureTokenRequest",
    "CreateSecureTokenResponse",
    # Model classes — validations
    "ValidateBundleRequest",
    "ValidationIssue",
    "ValidateBundleResponse",
    # Network constants
    "ACTIVATION_NETWORK_STAGING",
    "ACTIVATION_NETWORK_PRODUCTION",
    "NAMESPACE_STAGING_NETWORK",
    "NAMESPACE_PRODUCTION_NETWORK",
    "ITEM_STAGING_NETWORK",
    "ITEM_PRODUCTION_NETWORK",
    # Permission constants
    "PERMISSION_READ",
    "PERMISSION_WRITE",
    "PERMISSION_DELETE",
    # Report status constants
    "STATUS_SUCCESS",
    "STATUS_GENERIC_ERROR",
    "STATUS_UNKNOWN_EDGE_WORKER_ID",
    "STATUS_UNIMPLEMENTED_EVENT_HANDLER",
    "STATUS_RUNTIME_ERROR",
    "STATUS_EXECUTION_ERROR",
    "STATUS_TIMEOUT_ERROR",
    "STATUS_RESOURCE_LIMIT_HIT",
    "STATUS_CPU_TIMEOUT_ERROR",
    "STATUS_WALL_TIMEOUT_ERROR",
    "STATUS_INIT_CPU_TIMEOUT_ERROR",
    "STATUS_INIT_WALL_TIMEOUT_ERROR",
    # Event handler constants
    "EVENT_HANDLER_ON_CLIENT_REQUEST",
    "EVENT_HANDLER_ON_ORIGIN_REQUEST",
    "EVENT_HANDLER_ON_ORIGIN_RESPONSE",
    "EVENT_HANDLER_ON_CLIENT_RESPONSE",
    "EVENT_HANDLER_RESPONSE_PROVIDER",
]
