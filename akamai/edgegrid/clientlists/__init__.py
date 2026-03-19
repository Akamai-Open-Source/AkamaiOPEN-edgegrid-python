"""Client Lists API client package.

Provides access to Akamai Client Lists APIs for managing IP, GEO, ASN,
TLS Fingerprint, File Hash, User, and Domain client lists, including
list CRUD operations, item management, and activation lifecycle.

See: https://techdocs.akamai.com/client-lists/reference/api
"""

from akamai.edgegrid.clientlists.clientlists import Client
from akamai.edgegrid.clientlists.models import (
    # ClientListType constants
    IP,
    GEO,
    ASN,
    TLS_FINGERPRINT,
    FILE_HASH,
    USER,
    DOMAIN,
    VALID_LIST_TYPES,
    # ActivationNetwork constants
    STAGING,
    PRODUCTION,
    # ActivationStatus constants
    INACTIVE,
    PENDING_ACTIVATION,
    ACTIVE,
    DEACTIVATED,
    MODIFIED,
    PENDING_DEACTIVATION,
    FAILED,
    # ActivationAction constants
    ACTIVATE,
    DEACTIVATE,
    # Data models
    ListContent,
    ListItemContent,
    ListItemPayload,
    ClientList,
    ActivationParams,
    # Request/Response types
    GetClientListsRequest,
    GetClientListsResponse,
    GetClientListRequest,
    GetClientListResponse,
    CreateClientListRequest,
    CreateClientListResponse,
    UpdateClientList,
    UpdateClientListRequest,
    UpdateClientListResponse,
    UpdateClientListItems,
    UpdateClientListItemsRequest,
    UpdateClientListItemsResponse,
    DeleteClientListRequest,
    TranslateUsernamesRequest,
    TranslateUsernamesResponse,
    GetClientListItemsRequest,
    GetClientListItemsResponse,
    GetActivationRequest,
    GetActivationResponse,
    GetActivationStatusRequest,
    GetActivationStatusResponse,
    CreateActivationRequest,
    CreateActivationResponse,
    CreateDeactivationRequest,
    CreateDeactivationResponse,
)
from akamai.edgegrid.clientlists.errors import (
    Error,
    ErrStructValidation,
    parse_error_response,
)

__all__ = [
    "Client",
    # ClientListType constants
    "IP",
    "GEO",
    "ASN",
    "TLS_FINGERPRINT",
    "FILE_HASH",
    "USER",
    "DOMAIN",
    "VALID_LIST_TYPES",
    # ActivationNetwork constants
    "STAGING",
    "PRODUCTION",
    # ActivationStatus constants
    "INACTIVE",
    "PENDING_ACTIVATION",
    "ACTIVE",
    "DEACTIVATED",
    "MODIFIED",
    "PENDING_DEACTIVATION",
    "FAILED",
    # ActivationAction constants
    "ACTIVATE",
    "DEACTIVATE",
    # Data models
    "ListContent",
    "ListItemContent",
    "ListItemPayload",
    "ClientList",
    "ActivationParams",
    # Request/Response types
    "GetClientListsRequest",
    "GetClientListsResponse",
    "GetClientListRequest",
    "GetClientListResponse",
    "CreateClientListRequest",
    "CreateClientListResponse",
    "UpdateClientList",
    "UpdateClientListRequest",
    "UpdateClientListResponse",
    "UpdateClientListItems",
    "UpdateClientListItemsRequest",
    "UpdateClientListItemsResponse",
    "DeleteClientListRequest",
    "TranslateUsernamesRequest",
    "TranslateUsernamesResponse",
    "GetClientListItemsRequest",
    "GetClientListItemsResponse",
    "GetActivationRequest",
    "GetActivationResponse",
    "GetActivationStatusRequest",
    "GetActivationStatusResponse",
    "CreateActivationRequest",
    "CreateActivationResponse",
    "CreateDeactivationRequest",
    "CreateDeactivationResponse",
    # Errors
    "Error",
    "ErrStructValidation",
    "parse_error_response",
]
