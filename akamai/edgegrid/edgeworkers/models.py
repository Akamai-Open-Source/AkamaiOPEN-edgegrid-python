"""Request and response models for EdgeWorkers/EdgeKV API."""
# pylint: disable=too-many-lines
from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# ActivationNetwork constants
# ---------------------------------------------------------------------------
ACTIVATION_NETWORK_STAGING = "STAGING"
ACTIVATION_NETWORK_PRODUCTION = "PRODUCTION"

# ---------------------------------------------------------------------------
# NamespaceNetwork constants
# ---------------------------------------------------------------------------
NAMESPACE_STAGING_NETWORK = "staging"
NAMESPACE_PRODUCTION_NETWORK = "production"

# ---------------------------------------------------------------------------
# ItemNetwork constants
# ---------------------------------------------------------------------------
ITEM_STAGING_NETWORK = "staging"
ITEM_PRODUCTION_NETWORK = "production"

# ---------------------------------------------------------------------------
# Permission constants
# ---------------------------------------------------------------------------
PERMISSION_READ = "r"
PERMISSION_WRITE = "w"
PERMISSION_DELETE = "d"

# ---------------------------------------------------------------------------
# Report status constants — verbatim from Go v12
# ---------------------------------------------------------------------------
STATUS_SUCCESS = "success"
STATUS_GENERIC_ERROR = "genericError"
STATUS_UNKNOWN_EDGE_WORKER_ID = "unknownEdgeWorkerId"
STATUS_UNIMPLEMENTED_EVENT_HANDLER = "unimplementedEventHandler"
STATUS_RUNTIME_ERROR = "runtimeError"
STATUS_EXECUTION_ERROR = "executionError"
STATUS_TIMEOUT_ERROR = "timeoutError"
STATUS_RESOURCE_LIMIT_HIT = "resourceLimitHit"
STATUS_CPU_TIMEOUT_ERROR = "cpuTimeoutError"
STATUS_WALL_TIMEOUT_ERROR = "wallTimeoutError"
STATUS_INIT_CPU_TIMEOUT_ERROR = "initCpuTimeoutError"
STATUS_INIT_WALL_TIMEOUT_ERROR = "initWallTimeoutError"

# ---------------------------------------------------------------------------
# Event handler constants — verbatim from Go v12
# ---------------------------------------------------------------------------
EVENT_HANDLER_ON_CLIENT_REQUEST = "onClientRequest"
EVENT_HANDLER_ON_ORIGIN_REQUEST = "onOriginRequest"
EVENT_HANDLER_ON_ORIGIN_RESPONSE = "onOriginResponse"
EVENT_HANDLER_ON_CLIENT_RESPONSE = "onClientResponse"
EVENT_HANDLER_RESPONSE_PROVIDER = "responseProvider"


# ===================================================================
# Activation models — from activations.go
# ===================================================================

@dataclass
class ListActivationsRequest:
    """Parameters used to list activations."""

    edge_worker_id: int = 0
    version: str = ""


@dataclass
class ActivateVersion:
    """Request body used to activate a version."""

    network: str = ""
    version: str = ""
    note: str = ""

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        result: dict = {
            "network": self.network,
            "version": self.version,
        }
        if self.note:
            result["note"] = self.note
        return result


@dataclass
class ActivateVersionRequest:
    """Path parameters and request body used to activate an edge worker."""

    edge_worker_id: int = 0
    activate_version: ActivateVersion | None = None


@dataclass
class GetActivationRequest:
    """Path parameters used to fetch edge worker activation."""

    edge_worker_id: int = 0
    activation_id: int = 0


@dataclass
class CancelActivationRequest:
    """Path parameters used to cancel edge worker activation."""

    edge_worker_id: int = 0
    activation_id: int = 0


@dataclass
class Activation:  # pylint: disable=too-many-instance-attributes
    """An activation object."""

    account_id: str = ""
    activation_id: int = 0
    created_by: str = ""
    created_time: str = ""
    edge_worker_id: int = 0
    last_modified_time: str = ""
    network: str = ""
    status: str = ""
    version: str = ""
    note: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> Activation:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            account_id=data.get("accountId", ""),
            activation_id=data.get("activationId", 0),
            created_by=data.get("createdBy", ""),
            created_time=data.get("createdTime", ""),
            edge_worker_id=data.get("edgeWorkerId", 0),
            last_modified_time=data.get("lastModifiedTime", ""),
            network=data.get("network", ""),
            status=data.get("status", ""),
            version=data.get("version", ""),
            note=data.get("note", ""),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "accountId": self.account_id,
            "activationId": self.activation_id,
            "createdBy": self.created_by,
            "createdTime": self.created_time,
            "edgeWorkerId": self.edge_worker_id,
            "lastModifiedTime": self.last_modified_time,
            "network": self.network,
            "status": self.status,
            "version": self.version,
            "note": self.note,
        }


@dataclass
class ListActivationsResponse:
    """Response object returned when listing activations."""

    activations: list[Activation] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> ListActivationsResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            activations=[
                Activation.from_dict(a) for a in data.get("activations", [])
            ],
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "activations": [a.to_dict() for a in self.activations],
        }


# ===================================================================
# Deactivation models — from deactivations.go
# ===================================================================

@dataclass
class Deactivation:  # pylint: disable=too-many-instance-attributes
    """Response returned by GetDeactivation, DeactivateVersion and ListDeactivation."""

    edge_worker_id: int = 0
    version: str = ""
    deactivation_id: int = 0
    account_id: str = ""
    status: str = ""
    network: str = ""
    note: str = ""
    created_by: str = ""
    created_time: str = ""
    last_modified_time: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> Deactivation:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            edge_worker_id=data.get("edgeWorkerId", 0),
            version=data.get("version", ""),
            deactivation_id=data.get("deactivationId", 0),
            account_id=data.get("accountId", ""),
            status=data.get("status", ""),
            network=data.get("network", ""),
            note=data.get("note", ""),
            created_by=data.get("createdBy", ""),
            created_time=data.get("createdTime", ""),
            last_modified_time=data.get("lastModifiedTime", ""),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        result: dict = {
            "edgeWorkerId": self.edge_worker_id,
            "version": self.version,
            "deactivationId": self.deactivation_id,
            "accountId": self.account_id,
            "status": self.status,
            "network": self.network,
            "createdBy": self.created_by,
            "createdTime": self.created_time,
            "lastModifiedTime": self.last_modified_time,
        }
        if self.note:
            result["note"] = self.note
        return result


@dataclass
class ListDeactivationsRequest:
    """Parameters for the list deactivations request."""

    edge_worker_id: int = 0
    version: str = ""


@dataclass
class DeactivateVersion:
    """Request body used to deactivate a version."""

    network: str = ""
    note: str = ""
    version: str = ""

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        result: dict = {
            "network": self.network,
            "version": self.version,
        }
        if self.note:
            result["note"] = self.note
        return result


@dataclass
class DeactivateVersionRequest:
    """Request parameters for DeactivateVersion."""

    edge_worker_id: int = 0
    deactivate_version: DeactivateVersion | None = None


@dataclass
class GetDeactivationRequest:
    """Request parameters for GetDeactivation."""

    edge_worker_id: int = 0
    deactivation_id: int = 0


@dataclass
class ListDeactivationsResponse:
    """List deactivations response."""

    deactivations: list[Deactivation] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> ListDeactivationsResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            deactivations=[
                Deactivation.from_dict(d) for d in data.get("deactivations", [])
            ],
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "deactivations": [d.to_dict() for d in self.deactivations],
        }


# ===================================================================
# Contracts models — from contracts.go
# ===================================================================

@dataclass
class ListContractsResponse:
    """Response object returned by ListContracts."""

    contract_ids: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> ListContractsResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            contract_ids=list(data.get("contractIds", [])),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "contractIds": list(self.contract_ids),
        }


# ===================================================================
# EdgeKV Access Token models — from edgekv_access_tokens.go
# ===================================================================

@dataclass
class CreateEdgeKVAccessTokenRequest:
    """Parameters used to create EdgeKV access token."""

    allow_on_production: bool = False
    allow_on_staging: bool = False
    name: str = ""
    namespace_permissions: dict[str, list[str]] = field(default_factory=dict)
    restrict_to_edge_worker_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "allowOnProduction": self.allow_on_production,
            "allowOnStaging": self.allow_on_staging,
            "name": self.name,
            "namespacePermissions": {
                k: list(v) for k, v in self.namespace_permissions.items()
            },
            "restrictToEdgeWorkerIds": list(self.restrict_to_edge_worker_ids),
        }


@dataclass
class EdgeKVAccessToken:
    """EdgeKV access token object."""

    expiry: str = ""
    name: str = ""
    uuid: str = ""
    token_activation_status: str | None = None
    issue_date: str | None = None
    latest_refresh_date: str | None = None
    next_scheduled_refresh_date: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> EdgeKVAccessToken:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            expiry=data.get("expiry", ""),
            name=data.get("name", ""),
            uuid=data.get("uuid", ""),
            token_activation_status=data.get("tokenActivationStatus"),
            issue_date=data.get("issueDate"),
            latest_refresh_date=data.get("latestRefreshDate"),
            next_scheduled_refresh_date=data.get("nextScheduledRefreshDate"),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        result: dict = {
            "expiry": self.expiry,
            "name": self.name,
            "uuid": self.uuid,
        }
        if self.token_activation_status is not None:
            result["tokenActivationStatus"] = self.token_activation_status
        if self.issue_date is not None:
            result["issueDate"] = self.issue_date
        if self.latest_refresh_date is not None:
            result["latestRefreshDate"] = self.latest_refresh_date
        if self.next_scheduled_refresh_date is not None:
            result["nextScheduledRefreshDate"] = self.next_scheduled_refresh_date
        return result


@dataclass
class CreateEdgeKVAccessTokenResponse:  # pylint: disable=too-many-instance-attributes
    """Response from EdgeKV access token creation."""

    allow_on_production: bool = False
    allow_on_staging: bool = False
    cpcode: str = ""
    expiry: str = ""
    issue_date: str = ""
    latest_refresh_date: str | None = None
    name: str = ""
    namespace_permissions: dict[str, list[str]] = field(default_factory=dict)
    next_scheduled_refresh_date: str = ""
    restrict_to_edge_worker_ids: list[str] = field(default_factory=list)
    token_activation_status: str = ""
    uuid: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> CreateEdgeKVAccessTokenResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        raw_perms = data.get("namespacePermissions", {})
        perms = {k: list(v) for k, v in raw_perms.items()} if raw_perms else {}
        return cls(
            allow_on_production=data.get("allowOnProduction", False),
            allow_on_staging=data.get("allowOnStaging", False),
            cpcode=data.get("cpcode", ""),
            expiry=data.get("expiry", ""),
            issue_date=data.get("issueDate", ""),
            latest_refresh_date=data.get("latestRefreshDate"),
            name=data.get("name", ""),
            namespace_permissions=perms,
            next_scheduled_refresh_date=data.get(
                "nextScheduledRefreshDate", "",
            ),
            restrict_to_edge_worker_ids=list(
                data.get("restrictToEdgeWorkerIds", []),
            ),
            token_activation_status=data.get("tokenActivationStatus", ""),
            uuid=data.get("uuid", ""),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        result: dict = {
            "allowOnProduction": self.allow_on_production,
            "allowOnStaging": self.allow_on_staging,
            "cpcode": self.cpcode,
            "expiry": self.expiry,
            "issueDate": self.issue_date,
            "name": self.name,
            "namespacePermissions": {
                k: list(v) for k, v in self.namespace_permissions.items()
            },
            "nextScheduledRefreshDate": self.next_scheduled_refresh_date,
            "restrictToEdgeWorkerIds": list(self.restrict_to_edge_worker_ids),
            "tokenActivationStatus": self.token_activation_status,
            "uuid": self.uuid,
        }
        if self.latest_refresh_date is not None:
            result["latestRefreshDate"] = self.latest_refresh_date
        return result


# GetEdgeKVAccessTokenResponse is a type alias for CreateEdgeKVAccessTokenResponse
GetEdgeKVAccessTokenResponse = CreateEdgeKVAccessTokenResponse


@dataclass
class GetEdgeKVAccessTokenRequest:
    """Token name to get."""

    token_name: str = ""


@dataclass
class ListEdgeKVAccessTokensRequest:
    """Request parameters for ListEdgeKVAccessTokens."""

    include_expired: bool = False


@dataclass
class ListEdgeKVAccessTokensResponse:
    """List of EdgeKV access tokens."""

    tokens: list[EdgeKVAccessToken] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> ListEdgeKVAccessTokensResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            tokens=[
                EdgeKVAccessToken.from_dict(t)
                for t in data.get("tokens", [])
            ],
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "tokens": [t.to_dict() for t in self.tokens],
        }


@dataclass
class DeleteEdgeKVAccessTokenRequest:
    """Name of the EdgeKV access token to remove."""

    token_name: str = ""


@dataclass
class DeleteEdgeKVAccessTokenResponse:
    """Response after removal of EdgeKV access token."""

    name: str = ""
    uuid: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> DeleteEdgeKVAccessTokenResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            name=data.get("name", ""),
            uuid=data.get("uuid", ""),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "name": self.name,
            "uuid": self.uuid,
        }


# ===================================================================
# EdgeKV Groups models — from edgekv_groups.go
# ===================================================================

@dataclass
class ListGroupsWithinNamespaceRequest:
    """Parameters used to get groups within a namespace."""

    network: str = ""
    namespace_id: str = ""


# ===================================================================
# EdgeKV Initialize models — from edgekv_initialize.go
# ===================================================================

@dataclass
class EdgeKVInitializationStatus:
    """Response object returned by InitializeEdgeKV and GetEdgeKVInitializeStatus."""

    account_status: str = ""
    cpcode: str = ""
    production_status: str = ""
    staging_status: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> EdgeKVInitializationStatus:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            account_status=data.get("accountStatus", ""),
            cpcode=data.get("cpcode", ""),
            production_status=data.get("productionStatus", ""),
            staging_status=data.get("stagingStatus", ""),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "accountStatus": self.account_status,
            "cpcode": self.cpcode,
            "productionStatus": self.production_status,
            "stagingStatus": self.staging_status,
        }


# ===================================================================
# EdgeKV Items models — from edgekv_items.go
# ===================================================================

@dataclass
class ItemsRequestParams:
    """Parameters used to list items."""

    network: str = ""
    namespace_id: str = ""
    group_id: str = ""


@dataclass
class ListItemsRequest:
    """Request params used to list items."""

    items_request_params: ItemsRequestParams | None = None


@dataclass
class GetItemRequest:
    """Request params used to get a single item."""

    item_id: str = ""
    items_request_params: ItemsRequestParams | None = None


@dataclass
class UpsertItemRequest:
    """Request params and body used to create or update an item."""

    item_id: str = ""
    item_data: str = ""
    items_request_params: ItemsRequestParams | None = None


@dataclass
class DeleteItemRequest:
    """Request params used to delete an item."""

    item_id: str = ""
    items_request_params: ItemsRequestParams | None = None


# ===================================================================
# EdgeKV Namespace models — from edgekv_namespaces.go
# ===================================================================

@dataclass
class ListEdgeKVNamespacesRequest:
    """Parameters used to list namespaces."""

    network: str = ""
    details: bool = False


@dataclass
class GetEdgeKVNamespaceRequest:
    """Parameters used to fetch a namespace."""

    network: str = ""
    name: str = ""


@dataclass
class NamespaceRequest:
    """Namespace object to create a namespace."""

    name: str = ""
    geo_location: str = ""
    retention: int | None = None
    group_id: int | None = None

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        result: dict = {"namespace": self.name}
        if self.geo_location:
            result["geoLocation"] = self.geo_location
        if self.retention is not None:
            result["retentionInSeconds"] = self.retention
        if self.group_id is not None:
            result["groupId"] = self.group_id
        return result


@dataclass
class CreateEdgeKVNamespaceRequest:
    """Path parameter and request body used to create a namespace."""

    network: str = ""
    namespace_request: NamespaceRequest | None = None


@dataclass
class UpdateNamespace:
    """Request body used to update a namespace."""

    name: str = ""
    retention: int | None = None
    group_id: int | None = None

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        result: dict = {"namespace": self.name}
        if self.retention is not None:
            result["retentionInSeconds"] = self.retention
        if self.group_id is not None:
            result["groupId"] = self.group_id
        return result


@dataclass
class UpdateEdgeKVNamespaceRequest:
    """Parameters used to update a namespace."""

    network: str = ""
    update_namespace: UpdateNamespace | None = None


@dataclass
class Namespace:
    """A namespace object."""

    name: str = ""
    geo_location: str = ""
    retention: int | None = None
    group_id: int | None = None

    @classmethod
    def from_dict(cls, data: dict) -> Namespace:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            name=data.get("namespace", ""),
            geo_location=data.get("geoLocation", ""),
            retention=data.get("retentionInSeconds"),
            group_id=data.get("groupId"),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        result: dict = {
            "namespace": self.name,
            "geoLocation": self.geo_location,
        }
        if self.retention is not None:
            result["retentionInSeconds"] = self.retention
        if self.group_id is not None:
            result["groupId"] = self.group_id
        return result


@dataclass
class GetNamespaceResponse:
    """Response object details for the specified namespace."""

    name: str = ""
    geo_location: str = ""
    retention: int | None = None
    group_id: int | None = None
    scheduled_delete_time: str | None = None
    namespace_status: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> GetNamespaceResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            name=data.get("namespace", ""),
            geo_location=data.get("geoLocation", ""),
            retention=data.get("retentionInSeconds"),
            group_id=data.get("groupId"),
            scheduled_delete_time=data.get("scheduledDeleteTime"),
            namespace_status=data.get("namespaceStatus", ""),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        result: dict = {
            "namespace": self.name,
            "geoLocation": self.geo_location,
            "namespaceStatus": self.namespace_status,
        }
        if self.retention is not None:
            result["retentionInSeconds"] = self.retention
        if self.group_id is not None:
            result["groupId"] = self.group_id
        if self.scheduled_delete_time is not None:
            result["scheduledDeleteTime"] = self.scheduled_delete_time
        return result


# UpdateNamespaceResponse is a type alias for GetNamespaceResponse
UpdateNamespaceResponse = GetNamespaceResponse


@dataclass
class ListEdgeKVNamespacesResponse:
    """Response containing list of namespaces."""

    namespaces: list[Namespace] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> ListEdgeKVNamespacesResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            namespaces=[
                Namespace.from_dict(n) for n in data.get("namespaces", [])
            ],
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "namespaces": [n.to_dict() for n in self.namespaces],
        }


@dataclass
class DeleteEdgeKVNamespaceRequest:
    """Request to delete a namespace."""

    network: str = ""
    name: str = ""
    sync: bool = False


@dataclass
class DeleteEdgeKVNamespacesResponse:
    """Response object returned when deleting a namespace."""

    scheduled_delete_time: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> DeleteEdgeKVNamespacesResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            scheduled_delete_time=data.get("scheduledDeleteTime"),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        result: dict = {}
        if self.scheduled_delete_time is not None:
            result["scheduledDeleteTime"] = self.scheduled_delete_time
        return result


@dataclass
class GetScheduledDeleteTimeRequest:
    """Request parameters for fetching the scheduled delete time."""

    network: str = ""
    name: str = ""


@dataclass
class ScheduledDeleteTimeResponse:
    """Response containing the scheduled delete time."""

    scheduled_delete_time: str = ""
    retry_after_header: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> ScheduledDeleteTimeResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            scheduled_delete_time=data.get("scheduledDeleteTime", ""),
            retry_after_header=data.get("retryAfterHeader", ""),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "scheduledDeleteTime": self.scheduled_delete_time,
        }


@dataclass
class ScheduledDeleteTimeRequest:
    """Request containing the scheduled delete time."""

    scheduled_delete_time: str = ""

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "scheduledDeleteTime": self.scheduled_delete_time,
        }


@dataclass
class RescheduleNamespaceDeleteRequest:
    """Request parameters for rescheduling namespace delete."""

    network: str = ""
    name: str = ""
    body: ScheduledDeleteTimeRequest | None = None


@dataclass
class RescheduleNamespaceDeleteResponse:
    """Response containing the rescheduled delete time."""

    scheduled_delete_time: ScheduledDeleteTimeResponse | None = None
    retry_after_header: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> RescheduleNamespaceDeleteResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        sdt_data = data.get("scheduledDeleteTime")
        sdt = None
        if isinstance(sdt_data, dict):
            sdt = ScheduledDeleteTimeResponse.from_dict(sdt_data)
        elif isinstance(sdt_data, str):
            sdt = ScheduledDeleteTimeResponse(
                scheduled_delete_time=sdt_data,
            )
        return cls(
            scheduled_delete_time=sdt,
            retry_after_header=data.get("retryAfterHeader", ""),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        result: dict = {}
        if self.scheduled_delete_time is not None:
            result["scheduledDeleteTime"] = (
                self.scheduled_delete_time.to_dict()
            )
        return result


@dataclass
class CancelScheduledNamespaceDeleteRequest:
    """Request parameters for canceling scheduled namespace delete."""

    network: str = ""
    name: str = ""


# ===================================================================
# EdgeWorkerID models — from edgeworker_id.go
# ===================================================================

@dataclass
class GetEdgeWorkerIDRequest:
    """Parameters used to get an EdgeWorkerID."""

    edge_worker_id: int = 0


@dataclass
class DeleteEdgeWorkerIDRequest:
    """Parameters used to delete an EdgeWorkerID."""

    edge_worker_id: int = 0


@dataclass
class EdgeWorkerID:  # pylint: disable=too-many-instance-attributes
    """An EdgeWorkerID object."""

    edge_worker_id: int = 0
    name: str = ""
    account_id: str = ""
    group_id: int = 0
    resource_tier_id: int = 0
    source_edge_worker_id: int = 0
    created_by: str = ""
    created_time: str = ""
    last_modified_by: str = ""
    last_modified_time: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> EdgeWorkerID:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            edge_worker_id=data.get("edgeWorkerId", 0),
            name=data.get("name", ""),
            account_id=data.get("accountId", ""),
            group_id=data.get("groupId", 0),
            resource_tier_id=data.get("resourceTierId", 0),
            source_edge_worker_id=data.get("sourceEdgeWorkerId", 0),
            created_by=data.get("createdBy", ""),
            created_time=data.get("createdTime", ""),
            last_modified_by=data.get("lastModifiedBy", ""),
            last_modified_time=data.get("lastModifiedTime", ""),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        result: dict = {
            "edgeWorkerId": self.edge_worker_id,
            "name": self.name,
            "accountId": self.account_id,
            "groupId": self.group_id,
            "resourceTierId": self.resource_tier_id,
            "createdBy": self.created_by,
            "createdTime": self.created_time,
            "lastModifiedBy": self.last_modified_by,
            "lastModifiedTime": self.last_modified_time,
        }
        if self.source_edge_worker_id:
            result["sourceEdgeWorkerId"] = self.source_edge_worker_id
        return result


@dataclass
class ListEdgeWorkersIDRequest:
    """Query parameters used to list EdgeWorkerIDs."""

    group_id: int = 0
    resource_tier_id: int = 0


@dataclass
class ListEdgeWorkersIDResponse:
    """Response object returned by ListEdgeWorkersID."""

    edge_workers: list[EdgeWorkerID] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> ListEdgeWorkersIDResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            edge_workers=[
                EdgeWorkerID.from_dict(e)
                for e in data.get("edgeWorkerIds", [])
            ],
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "edgeWorkerIds": [e.to_dict() for e in self.edge_workers],
        }


@dataclass
class CreateEdgeWorkerIDRequest:
    """Body parameters used to create EdgeWorkerID."""

    name: str = ""
    group_id: int = 0
    resource_tier_id: int = 0

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "name": self.name,
            "groupId": self.group_id,
            "resourceTierId": self.resource_tier_id,
        }


@dataclass
class EdgeWorkerIDRequestBody:
    """Body parameters used to update or clone EdgeWorkerID."""

    name: str = ""
    group_id: int = 0
    resource_tier_id: int = 0

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "name": self.name,
            "groupId": self.group_id,
            "resourceTierId": self.resource_tier_id,
        }


@dataclass
class UpdateEdgeWorkerIDRequest:
    """Body and path parameters used to update EdgeWorkerID."""

    body: EdgeWorkerIDRequestBody | None = None
    edge_worker_id: int = 0


@dataclass
class CloneEdgeWorkerIDRequest:
    """Body and path parameters used to clone EdgeWorkerID."""

    body: EdgeWorkerIDRequestBody | None = None
    edge_worker_id: int = 0


# ===================================================================
# EdgeWorkerVersion models — from edgeworker_version.go
# ===================================================================

@dataclass
class EdgeWorkerVersionRequest:
    """Common request parameters for version operations."""

    edge_worker_id: int = 0
    version: str = ""


# Type aliases for version operations
GetEdgeWorkerVersionRequest = EdgeWorkerVersionRequest
GetEdgeWorkerVersionContentRequest = EdgeWorkerVersionRequest
DeleteEdgeWorkerVersionRequest = EdgeWorkerVersionRequest


@dataclass
class EdgeWorkerVersion:
    """An EdgeWorkerVersion object."""

    edge_worker_id: int = 0
    version: str = ""
    account_id: str = ""
    checksum: str = ""
    sequence_number: int = 0
    created_by: str = ""
    created_time: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> EdgeWorkerVersion:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            edge_worker_id=data.get("edgeWorkerId", 0),
            version=data.get("version", ""),
            account_id=data.get("accountId", ""),
            checksum=data.get("checksum", ""),
            sequence_number=data.get("sequenceNumber", 0),
            created_by=data.get("createdBy", ""),
            created_time=data.get("createdTime", ""),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "edgeWorkerId": self.edge_worker_id,
            "version": self.version,
            "accountId": self.account_id,
            "checksum": self.checksum,
            "sequenceNumber": self.sequence_number,
            "createdBy": self.created_by,
            "createdTime": self.created_time,
        }


@dataclass
class ListEdgeWorkerVersionsRequest:
    """Query parameters used to list EdgeWorkerVersions."""

    edge_worker_id: int = 0


@dataclass
class ListEdgeWorkerVersionsResponse:
    """Response object returned by ListEdgeWorkerVersions."""

    edge_worker_versions: list[EdgeWorkerVersion] = field(
        default_factory=list,
    )

    @classmethod
    def from_dict(cls, data: dict) -> ListEdgeWorkerVersionsResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            edge_worker_versions=[
                EdgeWorkerVersion.from_dict(v)
                for v in data.get("versions", [])
            ],
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "versions": [v.to_dict() for v in self.edge_worker_versions],
        }


@dataclass
class Bundle:
    """Content bundle of an Edgeworker Version.

    In Go, this wraps io.Reader.  In Python, wraps raw bytes.
    """

    data: bytes = b""


@dataclass
class CreateEdgeWorkerVersionRequest:
    """Parameters used to create EdgeWorkerVersion."""

    edge_worker_id: int = 0
    content_bundle: bytes | None = None


# ===================================================================
# Permission Group models — from permission_group.go
# ===================================================================

@dataclass
class GetPermissionGroupRequest:
    """Parameters used to get a permission group."""

    group_id: str = ""


@dataclass
class PermissionGroup:
    """A single permission group object."""

    id: int = 0  # pylint: disable=invalid-name
    name: str = ""
    capabilities: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> PermissionGroup:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            id=data.get("groupId", 0),
            name=data.get("groupName", ""),
            capabilities=list(data.get("capabilities", [])),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "groupId": self.id,
            "groupName": self.name,
            "capabilities": list(self.capabilities),
        }


@dataclass
class ListPermissionGroupsResponse:
    """Response object returned by ListPermissionGroups."""

    permission_groups: list[PermissionGroup] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> ListPermissionGroupsResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            permission_groups=[
                PermissionGroup.from_dict(g)
                for g in data.get("groups", [])
            ],
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "groups": [g.to_dict() for g in self.permission_groups],
        }


# ===================================================================
# Properties models — from properties.go
# ===================================================================

@dataclass
class ListPropertiesRequest:
    """Parameters used to list properties."""

    edge_worker_id: int = 0
    active_only: bool = False


@dataclass
class Property:
    """A single property object."""

    id: int = 0  # pylint: disable=invalid-name
    name: str = ""
    staging_version: int = 0
    production_version: int = 0
    latest_version: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> Property:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            id=data.get("propertyId", 0),
            name=data.get("propertyName", ""),
            staging_version=data.get("stagingVersion", 0),
            production_version=data.get("productionVersion", 0),
            latest_version=data.get("latestVersion", 0),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "propertyId": self.id,
            "propertyName": self.name,
            "stagingVersion": self.staging_version,
            "productionVersion": self.production_version,
            "latestVersion": self.latest_version,
        }


@dataclass
class ListPropertiesResponse:
    """Response object returned by ListProperties."""

    properties: list[Property] = field(default_factory=list)
    limited_access_to_properties: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> ListPropertiesResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            properties=[
                Property.from_dict(p) for p in data.get("properties", [])
            ],
            limited_access_to_properties=data.get(
                "limitedAccessToProperties", False,
            ),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "properties": [p.to_dict() for p in self.properties],
            "limitedAccessToProperties": self.limited_access_to_properties,
        }


# ===================================================================
# Report models — from report.go
# ===================================================================

@dataclass
class GetSummaryReportRequest:
    """Parameters used to get summary report."""

    start: str = ""
    end: str = ""
    edge_worker: str = ""
    status: str | None = None
    event_handler: str | None = None


@dataclass
class Summary:
    """Data object for memory usage, init/exec duration."""

    avg: float = 0.0
    min: float = 0.0  # pylint: disable=redefined-builtin
    max: float = 0.0  # pylint: disable=redefined-builtin

    @classmethod
    def from_dict(cls, data: dict) -> Summary:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            avg=float(data.get("avg", 0.0)),
            min=float(data.get("min", 0.0)),
            max=float(data.get("max", 0.0)),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "avg": self.avg,
            "min": self.min,
            "max": self.max,
        }


@dataclass
class Total:
    """Total count for Successes, Invocations, Errors."""

    total: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> Total:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(total=data.get("total", 0))

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {"total": self.total}


@dataclass
class DataSummary:
    """Reports summary overview data."""

    memory: Summary | None = None
    successes: Total | None = None
    init_duration: Summary | None = None
    exec_duration: Summary | None = None
    errors: Total | None = None
    invocations: Total | None = None

    @classmethod
    def from_dict(cls, data: dict) -> DataSummary:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            memory=Summary.from_dict(data["memory"])
            if data.get("memory") is not None else None,
            successes=Total.from_dict(data["successes"])
            if data.get("successes") is not None else None,
            init_duration=Summary.from_dict(data["initDuration"])
            if data.get("initDuration") is not None else None,
            exec_duration=Summary.from_dict(data["execDuration"])
            if data.get("execDuration") is not None else None,
            errors=Total.from_dict(data["errors"])
            if data.get("errors") is not None else None,
            invocations=Total.from_dict(data["invocations"])
            if data.get("invocations") is not None else None,
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        result: dict = {}
        if self.memory is not None:
            result["memory"] = self.memory.to_dict()
        if self.successes is not None:
            result["successes"] = self.successes.to_dict()
        if self.init_duration is not None:
            result["initDuration"] = self.init_duration.to_dict()
        if self.exec_duration is not None:
            result["execDuration"] = self.exec_duration.to_dict()
        if self.errors is not None:
            result["errors"] = self.errors.to_dict()
        if self.invocations is not None:
            result["invocations"] = self.invocations.to_dict()
        return result


@dataclass
class GetSummaryReportResponse:
    """Response object returned by GetSummaryReport."""

    report_id: int = 0
    name: str = ""
    description: str = ""
    start: str = ""
    end: str = ""
    data: DataSummary | None = None
    unavailable: bool | None = None

    @classmethod
    def from_dict(cls, data: dict) -> GetSummaryReportResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            report_id=data.get("reportId", 0),
            name=data.get("name", ""),
            description=data.get("description", ""),
            start=data.get("start", ""),
            end=data.get("end", ""),
            data=DataSummary.from_dict(data["data"])
            if data.get("data") is not None else None,
            unavailable=data.get("unavailable"),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        result: dict = {
            "reportId": self.report_id,
            "name": self.name,
            "description": self.description,
            "start": self.start,
            "end": self.end,
        }
        if self.data is not None:
            result["data"] = self.data.to_dict()
        if self.unavailable is not None:
            result["unavailable"] = self.unavailable
        return result


@dataclass
class GetReportRequest:
    """Parameters used to get report."""

    report_id: int = 0
    start: str = ""
    end: str = ""
    edge_worker: str = ""
    status: str | None = None
    event_handler: str | None = None


@dataclass
class OnRequestAndResponse:
    """Object structure for event handler fields."""

    status: str | None = None
    start_date_time: str = ""
    edge_worker_version: str = ""
    exec_duration: Summary | None = None
    invocations: int = 0
    memory: Summary | None = None

    @classmethod
    def from_dict(cls, data: dict) -> OnRequestAndResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            status=data.get("status"),
            start_date_time=data.get("startDateTime", ""),
            edge_worker_version=data.get("edgeWorkerVersion", ""),
            exec_duration=Summary.from_dict(data["execDuration"])
            if data.get("execDuration") is not None else None,
            invocations=data.get("invocations", 0),
            memory=Summary.from_dict(data["memory"])
            if data.get("memory") is not None else None,
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        result: dict = {
            "startDateTime": self.start_date_time,
            "edgeWorkerVersion": self.edge_worker_version,
            "invocations": self.invocations,
        }
        if self.status is not None:
            result["status"] = self.status
        if self.exec_duration is not None:
            result["execDuration"] = self.exec_duration.to_dict()
        if self.memory is not None:
            result["memory"] = self.memory.to_dict()
        return result


@dataclass
class InitObject:
    """Object structure for Init field."""

    start_date_time: str = ""
    edge_worker_version: str = ""
    init_duration: Summary | None = None
    invocations: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> InitObject:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            start_date_time=data.get("startDateTime", ""),
            edge_worker_version=data.get("edgeWorkerVersion", ""),
            init_duration=Summary.from_dict(data["initDuration"])
            if data.get("initDuration") is not None else None,
            invocations=data.get("invocations", 0),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        result: dict = {
            "startDateTime": self.start_date_time,
            "edgeWorkerVersion": self.edge_worker_version,
            "invocations": self.invocations,
        }
        if self.init_duration is not None:
            result["initDuration"] = self.init_duration.to_dict()
        return result


def _list_orar_from_dict(items: list | None) -> list[OnRequestAndResponse] | None:
    """Deserialize a list of OnRequestAndResponse from raw dicts."""
    if items is None:
        return None
    return [OnRequestAndResponse.from_dict(i) for i in items]


def _list_orar_to_dict(items: list[OnRequestAndResponse] | None) -> list[dict] | None:
    """Serialize a list of OnRequestAndResponse to dicts."""
    if items is None:
        return None
    return [i.to_dict() for i in items]


@dataclass
class Data:
    """Data object for report details."""

    on_client_request: list[OnRequestAndResponse] | None = None
    on_origin_request: list[OnRequestAndResponse] | None = None
    on_origin_response: list[OnRequestAndResponse] | None = None
    on_client_response: list[OnRequestAndResponse] | None = None
    response_provider: list[OnRequestAndResponse] | None = None
    init: list[InitObject] | None = None

    @classmethod
    def from_dict(cls, data: dict) -> Data:
        """Deserialize from JSON dict using Go JSON tag names."""
        init_raw = data.get("init")
        return cls(
            on_client_request=_list_orar_from_dict(
                data.get("onClientRequest"),
            ),
            on_origin_request=_list_orar_from_dict(
                data.get("onOriginRequest"),
            ),
            on_origin_response=_list_orar_from_dict(
                data.get("onOriginResponse"),
            ),
            on_client_response=_list_orar_from_dict(
                data.get("onClientResponse"),
            ),
            response_provider=_list_orar_from_dict(
                data.get("responseProvider"),
            ),
            init=[InitObject.from_dict(i) for i in init_raw]
            if init_raw is not None else None,
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        result: dict = {}
        if self.on_client_request is not None:
            result["onClientRequest"] = _list_orar_to_dict(
                self.on_client_request,
            )
        if self.on_origin_request is not None:
            result["onOriginRequest"] = _list_orar_to_dict(
                self.on_origin_request,
            )
        if self.on_origin_response is not None:
            result["onOriginResponse"] = _list_orar_to_dict(
                self.on_origin_response,
            )
        if self.on_client_response is not None:
            result["onClientResponse"] = _list_orar_to_dict(
                self.on_client_response,
            )
        if self.response_provider is not None:
            result["responseProvider"] = _list_orar_to_dict(
                self.response_provider,
            )
        if self.init is not None:
            result["init"] = [i.to_dict() for i in self.init]
        return result


@dataclass
class ReportData:
    """Report data."""

    edge_worker_id: int = 0
    data: Data | None = None

    @classmethod
    def from_dict(cls, raw: dict) -> ReportData:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            edge_worker_id=raw.get("edgeWorkerId", 0),
            data=Data.from_dict(raw["data"])
            if raw.get("data") is not None else None,
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        result: dict = {"edgeWorkerId": self.edge_worker_id}
        if self.data is not None:
            result["data"] = self.data.to_dict()
        return result


@dataclass
class GetReportResponse:
    """Response object returned by GetReport."""

    report_id: int = 0
    name: str = ""
    description: str = ""
    start: str = ""
    end: str = ""
    data: list[ReportData] = field(default_factory=list)

    @classmethod
    def from_dict(cls, raw: dict) -> GetReportResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            report_id=raw.get("reportId", 0),
            name=raw.get("name", ""),
            description=raw.get("description", ""),
            start=raw.get("start", ""),
            end=raw.get("end", ""),
            data=[ReportData.from_dict(d) for d in raw.get("data", [])],
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "reportId": self.report_id,
            "name": self.name,
            "description": self.description,
            "start": self.start,
            "end": self.end,
            "data": [d.to_dict() for d in self.data],
        }


@dataclass
class ReportResponse:
    """Report type object."""

    report_id: int = 0
    name: str = ""
    description: str = ""
    unavailable: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> ReportResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            report_id=data.get("reportId", 0),
            name=data.get("name", ""),
            description=data.get("description", ""),
            unavailable=data.get("unavailable", False),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "reportId": self.report_id,
            "name": self.name,
            "description": self.description,
            "unavailable": self.unavailable,
        }


@dataclass
class ListReportsResponse:
    """List of report types."""

    reports: list[ReportResponse] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> ListReportsResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            reports=[
                ReportResponse.from_dict(r) for r in data.get("reports", [])
            ],
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "reports": [r.to_dict() for r in self.reports],
        }


# ===================================================================
# Resource Tier models — from resource_tier.go
# ===================================================================

@dataclass
class ListResourceTiersRequest:
    """Parameters used to list resource tiers."""

    contract_id: str = ""


@dataclass
class GetResourceTierRequest:
    """Parameters used to get a resource tier."""

    edge_worker_id: int = 0


@dataclass
class EdgeWorkerLimit:
    """A single edgeworker limit object."""

    limit_name: str = ""
    limit_value: int = 0
    limit_unit: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> EdgeWorkerLimit:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            limit_name=data.get("limitName", ""),
            limit_value=data.get("limitValue", 0),
            limit_unit=data.get("limitUnit", ""),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "limitName": self.limit_name,
            "limitValue": self.limit_value,
            "limitUnit": self.limit_unit,
        }


@dataclass
class ResourceTier:
    """A single resource tier object."""

    id: int = 0  # pylint: disable=invalid-name
    name: str = ""
    edge_worker_limits: list[EdgeWorkerLimit] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> ResourceTier:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            id=data.get("resourceTierId", 0),
            name=data.get("resourceTierName", ""),
            edge_worker_limits=[
                EdgeWorkerLimit.from_dict(lim)
                for lim in data.get("edgeWorkerLimits", [])
            ],
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "resourceTierId": self.id,
            "resourceTierName": self.name,
            "edgeWorkerLimits": [
                lim.to_dict() for lim in self.edge_worker_limits
            ],
        }


@dataclass
class ListResourceTiersResponse:
    """Response object returned by ListResourceTiers."""

    resource_tiers: list[ResourceTier] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> ListResourceTiersResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            resource_tiers=[
                ResourceTier.from_dict(t)
                for t in data.get("resourceTiers", [])
            ],
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "resourceTiers": [t.to_dict() for t in self.resource_tiers],
        }


# ===================================================================
# Secure Token models — from secure_tokens.go
# ===================================================================

@dataclass
class CreateSecureTokenRequest:
    """Parameters for CreateSecureToken."""

    acl: str = ""
    expiry: int = 0
    hostname: str = ""
    network: str = ""
    property_id: str = ""
    url: str = ""

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        result: dict = {}
        if self.acl:
            result["acl"] = self.acl
        if self.expiry:
            result["expiry"] = self.expiry
        if self.hostname:
            result["hostname"] = self.hostname
        if self.network:
            result["network"] = self.network
        if self.property_id:
            result["propertyId"] = self.property_id
        if self.url:
            result["url"] = self.url
        return result


@dataclass
class CreateSecureTokenResponse:
    """Response from CreateSecureToken."""

    akamai_ew_trace: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> CreateSecureTokenResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            akamai_ew_trace=data.get("akamaiEwTrace", ""),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "akamaiEwTrace": self.akamai_ew_trace,
        }


# ===================================================================
# Validation models — from validations.go
# ===================================================================

@dataclass
class ValidateBundleRequest:
    """Request bundle parameter to validate."""

    bundle: bytes | None = None


@dataclass
class ValidationIssue:
    """A single validation error or warning."""

    type: str = ""  # pylint: disable=redefined-builtin
    message: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> ValidationIssue:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            type=data.get("type", ""),
            message=data.get("message", ""),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "type": self.type,
            "message": self.message,
        }


@dataclass
class ValidateBundleResponse:
    """Response object returned by ValidateBundle."""

    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> ValidateBundleResponse:
        """Deserialize from JSON dict using Go JSON tag names."""
        return cls(
            errors=[
                ValidationIssue.from_dict(e)
                for e in data.get("errors", [])
            ],
            warnings=[
                ValidationIssue.from_dict(w)
                for w in data.get("warnings", [])
            ],
        )

    def to_dict(self) -> dict:
        """Serialize to JSON dict using Go JSON tag names."""
        return {
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
        }
