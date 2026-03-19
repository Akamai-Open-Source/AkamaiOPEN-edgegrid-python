# pylint: disable=too-many-instance-attributes,too-many-arguments
"""Request and response models for the Client Lists API.

Every Go struct field in ``pkg/clientlists/client_list.go`` and
``pkg/clientlists/client_list_activation.go`` maps 1-to-1 to a Python
dataclass field.  JSON serialization keys match the Go JSON struct tags.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Type aliases for Go typed-string enumerations
# ---------------------------------------------------------------------------
ClientListType = str
ActivationNetwork = str
ActivationStatus = str
ActivationAction = str

# ---------------------------------------------------------------------------
# ClientListType constants  (Go: client_list.go lines 517-531)
# ---------------------------------------------------------------------------
IP: ClientListType = "IP"
GEO: ClientListType = "GEO"
ASN: ClientListType = "ASN"
TLS_FINGERPRINT: ClientListType = "TLS_FINGERPRINT"
FILE_HASH: ClientListType = "FILE_HASH"
USER: ClientListType = "USER_ID"
DOMAIN: ClientListType = "DOMAIN"

VALID_LIST_TYPES: list[ClientListType] = [
    IP, GEO, ASN, TLS_FINGERPRINT, FILE_HASH, USER, DOMAIN,
]

# ---------------------------------------------------------------------------
# ActivationNetwork constants  (Go: client_list_activation.go lines 88-91)
# ---------------------------------------------------------------------------
STAGING: ActivationNetwork = "STAGING"
PRODUCTION: ActivationNetwork = "PRODUCTION"

# ---------------------------------------------------------------------------
# ActivationStatus constants  (Go: client_list_activation.go lines 93-106)
# ---------------------------------------------------------------------------
INACTIVE: ActivationStatus = "INACTIVE"
PENDING_ACTIVATION: ActivationStatus = "PENDING_ACTIVATION"
ACTIVE: ActivationStatus = "ACTIVE"
DEACTIVATED: ActivationStatus = "DEACTIVATED"
MODIFIED: ActivationStatus = "MODIFIED"
PENDING_DEACTIVATION: ActivationStatus = "PENDING_DEACTIVATION"
FAILED: ActivationStatus = "FAILED"

# ---------------------------------------------------------------------------
# ActivationAction constants  (Go: client_list_activation.go lines 108-111)
# ---------------------------------------------------------------------------
ACTIVATE: ActivationAction = "ACTIVATE"
DEACTIVATE: ActivationAction = "DEACTIVATE"


# ===================================================================
# Data-model classes
# ===================================================================


@dataclass
class ListContent:
    """List content metadata.

    Maps to Go ``ListContent`` (client_list.go lines 44-64).
    """

    name: str = ""
    type: str = ""  # pylint: disable=redefined-builtin
    notes: str = ""
    tags: list[str] = field(default_factory=list)
    list_id: str = ""
    version: int = 0
    items_count: int = 0
    create_date: str = ""
    created_by: str = ""
    update_date: str = ""
    updated_by: str = ""
    production_activation_status: str = ""
    staging_activation_status: str = ""
    production_active_version: int = 0
    staging_active_version: int = 0
    list_type: str = ""
    shared: bool = False
    read_only: bool = False
    deprecated: bool = False

    def to_dict(self) -> dict:
        """Serialize to a dict whose keys match Go JSON struct tags."""
        return {
            "name": self.name,
            "type": self.type,
            "notes": self.notes,
            "tags": list(self.tags),
            "listId": self.list_id,
            "version": self.version,
            "itemsCount": self.items_count,
            "createDate": self.create_date,
            "createdBy": self.created_by,
            "updateDate": self.update_date,
            "updatedBy": self.updated_by,
            "productionActivationStatus": self.production_activation_status,
            "stagingActivationStatus": self.staging_activation_status,
            "productionActiveVersion": self.production_active_version,
            "stagingActiveVersion": self.staging_active_version,
            "listType": self.list_type,
            "shared": self.shared,
            "readOnly": self.read_only,
            "deprecated": self.deprecated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListContent:
        """Deserialize from a dict whose keys use Go JSON struct tags."""
        return cls(
            name=data.get("name", ""),
            type=data.get("type", ""),
            notes=data.get("notes", ""),
            tags=data.get("tags", []),
            list_id=data.get("listId", ""),
            version=data.get("version", 0),
            items_count=data.get("itemsCount", 0),
            create_date=data.get("createDate", ""),
            created_by=data.get("createdBy", ""),
            update_date=data.get("updateDate", ""),
            updated_by=data.get("updatedBy", ""),
            production_activation_status=data.get("productionActivationStatus", ""),
            staging_activation_status=data.get("stagingActivationStatus", ""),
            production_active_version=data.get("productionActiveVersion", 0),
            staging_active_version=data.get("stagingActiveVersion", 0),
            list_type=data.get("listType", ""),
            shared=data.get("shared", False),
            read_only=data.get("readOnly", False),
            deprecated=data.get("deprecated", False),
        )


@dataclass
class ListItemContent:
    """Client list item information.

    Maps to Go ``ListItemContent`` (client_list.go lines 67-81).
    """

    value: str = ""
    username: str = ""
    tags: list[str] = field(default_factory=list)
    description: str = ""
    expiration_date: str = ""
    create_date: str = ""
    created_by: str = ""
    created_version: int = 0
    production_status: str = ""
    staging_status: str = ""
    type: str = ""  # pylint: disable=redefined-builtin
    update_date: str = ""
    updated_by: str = ""

    def to_dict(self) -> dict:
        """Serialize to a dict whose keys match Go JSON struct tags.

        The ``username`` field uses ``omitempty`` in Go, so it is omitted
        when empty.
        """
        result: dict = {"value": self.value}
        if self.username:
            result["username"] = self.username
        result["tags"] = list(self.tags)
        result["description"] = self.description
        result["expirationDate"] = self.expiration_date
        result["createDate"] = self.create_date
        result["createdBy"] = self.created_by
        result["createdVersion"] = self.created_version
        result["productionStatus"] = self.production_status
        result["stagingStatus"] = self.staging_status
        result["type"] = self.type
        result["updateDate"] = self.update_date
        result["updatedBy"] = self.updated_by
        return result

    @classmethod
    def from_dict(cls, data: dict) -> ListItemContent:
        """Deserialize from a dict whose keys use Go JSON struct tags."""
        return cls(
            value=data.get("value", ""),
            username=data.get("username", ""),
            tags=data.get("tags", []),
            description=data.get("description", ""),
            expiration_date=data.get("expirationDate", ""),
            create_date=data.get("createDate", ""),
            created_by=data.get("createdBy", ""),
            created_version=data.get("createdVersion", 0),
            production_status=data.get("productionStatus", ""),
            staging_status=data.get("stagingStatus", ""),
            type=data.get("type", ""),
            update_date=data.get("updateDate", ""),
            updated_by=data.get("updatedBy", ""),
        )


@dataclass
class ListItemPayload:
    """Editable item fields used as create/update/delete payload.

    Maps to Go ``ListItemPayload`` (client_list.go lines 84-89).
    """

    value: str = ""
    tags: list[str] | None = field(default_factory=list)
    description: str = ""
    expiration_date: str = ""

    def to_dict(self) -> dict:
        """Serialize to a dict whose keys match Go JSON struct tags."""
        return {
            "value": self.value,
            "tags": list(self.tags) if self.tags is not None else None,
            "description": self.description,
            "expirationDate": self.expiration_date,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListItemPayload:
        """Deserialize from a dict whose keys use Go JSON struct tags."""
        raw_tags = data.get("tags")
        return cls(
            value=data.get("value", ""),
            tags=list(raw_tags) if raw_tags is not None else [],
            description=data.get("description", ""),
            expiration_date=data.get("expirationDate", ""),
        )


@dataclass
class ClientList(ListContent):
    """List content with items.

    Maps to Go ``ClientList`` (client_list.go lines 37-41).
    Embeds ``ListContent`` via inheritance.
    """

    items: list[ListItemContent] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to a dict whose keys match Go JSON struct tags."""
        result = super().to_dict()
        result["items"] = [item.to_dict() for item in self.items]
        return result

    @classmethod
    def from_dict(cls, data: dict) -> ClientList:
        """Deserialize from a dict whose keys use Go JSON struct tags."""
        return cls(
            name=data.get("name", ""),
            type=data.get("type", ""),
            notes=data.get("notes", ""),
            tags=data.get("tags", []),
            list_id=data.get("listId", ""),
            version=data.get("version", 0),
            items_count=data.get("itemsCount", 0),
            create_date=data.get("createDate", ""),
            created_by=data.get("createdBy", ""),
            update_date=data.get("updateDate", ""),
            updated_by=data.get("updatedBy", ""),
            production_activation_status=data.get("productionActivationStatus", ""),
            staging_activation_status=data.get("stagingActivationStatus", ""),
            production_active_version=data.get("productionActiveVersion", 0),
            staging_active_version=data.get("stagingActiveVersion", 0),
            list_type=data.get("listType", ""),
            shared=data.get("shared", False),
            read_only=data.get("readOnly", False),
            deprecated=data.get("deprecated", False),
            items=[
                ListItemContent.from_dict(i) for i in data.get("items", [])
            ],
        )


@dataclass
class GetClientListsRequest:
    """Request parameters for the ``GetClientLists`` method.

    Maps to Go ``GetClientListsRequest`` (client_list.go lines 20-30).
    Fields are used as query parameters, not a JSON body.
    """

    type: list[str] = field(default_factory=list)  # pylint: disable=redefined-builtin
    name: str = ""
    search: str = ""
    include_items: bool = False
    include_deprecated: bool = False
    include_network_list: bool = False
    page: int | None = None
    page_size: int | None = None
    sort: list[str] | None = None

    def to_dict(self) -> dict:
        """Serialize to a dict suitable for query-parameter construction."""
        return {
            "type": list(self.type),
            "name": self.name,
            "search": self.search,
            "includeItems": self.include_items,
            "includeDeprecated": self.include_deprecated,
            "includeNetworkList": self.include_network_list,
            "page": self.page,
            "pageSize": self.page_size,
            "sort": list(self.sort) if self.sort is not None else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GetClientListsRequest:
        """Deserialize from a dict."""
        sort_raw = data.get("sort")
        return cls(
            type=data.get("type", []),
            name=data.get("name", ""),
            search=data.get("search", ""),
            include_items=data.get("includeItems", False),
            include_deprecated=data.get("includeDeprecated", False),
            include_network_list=data.get("includeNetworkList", False),
            page=data.get("page"),
            page_size=data.get("pageSize"),
            sort=list(sort_raw) if sort_raw is not None else None,
        )


@dataclass
class GetClientListsResponse:
    """Response from the ``GetClientLists`` method.

    Maps to Go ``GetClientListsResponse`` (client_list.go lines 33-35).
    """

    content: list[ClientList] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to a dict."""
        return {
            "content": [item.to_dict() for item in self.content],
        }

    @classmethod
    def from_dict(cls, data: dict) -> GetClientListsResponse:
        """Deserialize from a dict."""
        return cls(
            content=[
                ClientList.from_dict(i) for i in data.get("content", [])
            ],
        )


@dataclass
class GetClientListRequest:
    """Request parameters for the ``GetClientList`` method.

    Maps to Go ``GetClientListRequest`` (client_list.go lines 92-95).
    """

    list_id: str = ""
    include_items: bool = False


@dataclass
class GetClientListResponse(ListContent):
    """Response from the ``GetClientList`` method.

    Maps to Go ``GetClientListResponse`` (client_list.go lines 98-104).
    Embeds ``ListContent`` via inheritance.
    """

    contract_id: str = ""
    group_id: int = 0
    group_name: str = ""
    items: list[ListItemContent] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to a dict whose keys match Go JSON struct tags."""
        result = super().to_dict()
        result["contractId"] = self.contract_id
        result["groupId"] = self.group_id
        result["groupName"] = self.group_name
        result["items"] = [item.to_dict() for item in self.items]
        return result

    @classmethod
    def from_dict(cls, data: dict) -> GetClientListResponse:
        """Deserialize from a dict whose keys use Go JSON struct tags."""
        return cls(
            name=data.get("name", ""),
            type=data.get("type", ""),
            notes=data.get("notes", ""),
            tags=data.get("tags", []),
            list_id=data.get("listId", ""),
            version=data.get("version", 0),
            items_count=data.get("itemsCount", 0),
            create_date=data.get("createDate", ""),
            created_by=data.get("createdBy", ""),
            update_date=data.get("updateDate", ""),
            updated_by=data.get("updatedBy", ""),
            production_activation_status=data.get(
                "productionActivationStatus", "",
            ),
            staging_activation_status=data.get(
                "stagingActivationStatus", "",
            ),
            production_active_version=data.get("productionActiveVersion", 0),
            staging_active_version=data.get("stagingActiveVersion", 0),
            list_type=data.get("listType", ""),
            shared=data.get("shared", False),
            read_only=data.get("readOnly", False),
            deprecated=data.get("deprecated", False),
            contract_id=data.get("contractId", ""),
            group_id=data.get("groupId", 0),
            group_name=data.get("groupName", ""),
            items=[
                ListItemContent.from_dict(i) for i in data.get("items", [])
            ],
        )


# CreateClientListResponse is a type alias for GetClientListResponse
# (Go: client_list.go line 118)
CreateClientListResponse = GetClientListResponse


@dataclass
class CreateClientListRequest:
    """Request parameters for the ``CreateClientList`` method.

    Maps to Go ``CreateClientListRequest`` (client_list.go lines 107-115).
    """

    contract_id: str = ""
    group_id: int = 0
    name: str = ""
    type: str = ""  # pylint: disable=redefined-builtin
    notes: str = ""
    tags: list[str] = field(default_factory=list)
    items: list[ListItemPayload] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to a dict whose keys match Go JSON struct tags."""
        return {
            "contractId": self.contract_id,
            "groupId": self.group_id,
            "name": self.name,
            "type": self.type,
            "notes": self.notes,
            "tags": list(self.tags),
            "items": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, data: dict) -> CreateClientListRequest:
        """Deserialize from a dict whose keys use Go JSON struct tags."""
        return cls(
            contract_id=data.get("contractId", ""),
            group_id=data.get("groupId", 0),
            name=data.get("name", ""),
            type=data.get("type", ""),
            notes=data.get("notes", ""),
            tags=data.get("tags", []),
            items=[
                ListItemPayload.from_dict(i) for i in data.get("items", [])
            ],
        )


@dataclass
class UpdateClientList:
    """Body payload for updating a client list.

    Maps to Go ``UpdateClientList`` (client_list.go lines 127-131).
    """

    name: str = ""
    notes: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to a dict whose keys match Go JSON struct tags."""
        return {
            "name": self.name,
            "notes": self.notes,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict) -> UpdateClientList:
        """Deserialize from a dict whose keys use Go JSON struct tags."""
        return cls(
            name=data.get("name", ""),
            notes=data.get("notes", ""),
            tags=data.get("tags", []),
        )


@dataclass
class UpdateClientListRequest(UpdateClientList):
    """Request parameters for the ``UpdateClientList`` method.

    Maps to Go ``UpdateClientListRequest`` (client_list.go lines 121-124).
    Embeds ``UpdateClientList`` via inheritance.
    """

    list_id: str = ""

    def to_dict(self) -> dict:
        """Serialize to a dict whose keys match Go JSON struct tags."""
        result = super().to_dict()
        result["listId"] = self.list_id
        return result

    @classmethod
    def from_dict(cls, data: dict) -> UpdateClientListRequest:
        """Deserialize from a dict whose keys use Go JSON struct tags."""
        return cls(
            name=data.get("name", ""),
            notes=data.get("notes", ""),
            tags=data.get("tags", []),
            list_id=data.get("listId", ""),
        )


@dataclass
class UpdateClientListResponse(ListContent):
    """Response from the ``UpdateClientList`` method.

    Maps to Go ``UpdateClientListResponse`` (client_list.go lines 134-139).
    Embeds ``ListContent`` via inheritance.
    """

    contract_id: str = ""
    group_name: str = ""
    group_id: int = 0

    def to_dict(self) -> dict:
        """Serialize to a dict whose keys match Go JSON struct tags."""
        result = super().to_dict()
        result["contractId"] = self.contract_id
        result["groupName"] = self.group_name
        result["groupId"] = self.group_id
        return result

    @classmethod
    def from_dict(cls, data: dict) -> UpdateClientListResponse:
        """Deserialize from a dict whose keys use Go JSON struct tags."""
        return cls(
            name=data.get("name", ""),
            type=data.get("type", ""),
            notes=data.get("notes", ""),
            tags=data.get("tags", []),
            list_id=data.get("listId", ""),
            version=data.get("version", 0),
            items_count=data.get("itemsCount", 0),
            create_date=data.get("createDate", ""),
            created_by=data.get("createdBy", ""),
            update_date=data.get("updateDate", ""),
            updated_by=data.get("updatedBy", ""),
            production_activation_status=data.get(
                "productionActivationStatus", "",
            ),
            staging_activation_status=data.get(
                "stagingActivationStatus", "",
            ),
            production_active_version=data.get("productionActiveVersion", 0),
            staging_active_version=data.get("stagingActiveVersion", 0),
            list_type=data.get("listType", ""),
            shared=data.get("shared", False),
            read_only=data.get("readOnly", False),
            deprecated=data.get("deprecated", False),
            contract_id=data.get("contractId", ""),
            group_name=data.get("groupName", ""),
            group_id=data.get("groupId", 0),
        )


@dataclass
class UpdateClientListItems:
    """Body payload for updating client list items.

    Maps to Go ``UpdateClientListItems`` (client_list.go lines 148-152).
    """

    append: list[ListItemPayload] = field(default_factory=list)
    update: list[ListItemPayload] = field(default_factory=list)
    delete: list[ListItemPayload] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to a dict whose keys match Go JSON struct tags."""
        return {
            "append": [item.to_dict() for item in self.append],
            "update": [item.to_dict() for item in self.update],
            "delete": [item.to_dict() for item in self.delete],
        }

    @classmethod
    def from_dict(cls, data: dict) -> UpdateClientListItems:
        """Deserialize from a dict whose keys use Go JSON struct tags."""
        return cls(
            append=[
                ListItemPayload.from_dict(i) for i in data.get("append", [])
            ],
            update=[
                ListItemPayload.from_dict(i) for i in data.get("update", [])
            ],
            delete=[
                ListItemPayload.from_dict(i) for i in data.get("delete", [])
            ],
        )


@dataclass
class UpdateClientListItemsRequest(UpdateClientListItems):
    """Request parameters for the ``UpdateClientListItems`` method.

    Maps to Go ``UpdateClientListItemsRequest``
    (client_list.go lines 142-145).  Embeds ``UpdateClientListItems``
    via inheritance.
    """

    list_id: str = ""

    def to_dict(self) -> dict:
        """Serialize to a dict whose keys match Go JSON struct tags."""
        result = super().to_dict()
        result["listId"] = self.list_id
        return result

    @classmethod
    def from_dict(cls, data: dict) -> UpdateClientListItemsRequest:
        """Deserialize from a dict whose keys use Go JSON struct tags."""
        return cls(
            append=[
                ListItemPayload.from_dict(i) for i in data.get("append", [])
            ],
            update=[
                ListItemPayload.from_dict(i) for i in data.get("update", [])
            ],
            delete=[
                ListItemPayload.from_dict(i) for i in data.get("delete", [])
            ],
            list_id=data.get("listId", ""),
        )


@dataclass
class UpdateClientListItemsResponse:
    """Response from the ``UpdateClientListItems`` method.

    Maps to Go ``UpdateClientListItemsResponse``
    (client_list.go lines 155-159).
    """

    appended: list[ListItemContent] = field(default_factory=list)
    updated: list[ListItemContent] = field(default_factory=list)
    deleted: list[ListItemContent] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to a dict whose keys match Go JSON struct tags."""
        return {
            "appended": [item.to_dict() for item in self.appended],
            "updated": [item.to_dict() for item in self.updated],
            "deleted": [item.to_dict() for item in self.deleted],
        }

    @classmethod
    def from_dict(cls, data: dict) -> UpdateClientListItemsResponse:
        """Deserialize from a dict whose keys use Go JSON struct tags."""
        return cls(
            appended=[
                ListItemContent.from_dict(i)
                for i in data.get("appended", [])
            ],
            updated=[
                ListItemContent.from_dict(i)
                for i in data.get("updated", [])
            ],
            deleted=[
                ListItemContent.from_dict(i)
                for i in data.get("deleted", [])
            ],
        )


@dataclass
class DeleteClientListRequest:
    """Request parameters for the ``DeleteClientList`` method.

    Maps to Go ``DeleteClientListRequest`` (client_list.go lines 162-164).
    """

    list_id: str = ""


# TranslateUsernamesRequest is a type alias for list[str]
# (Go: client_list.go line 167)
TranslateUsernamesRequest = list[str]

# TranslateUsernamesResponse is a type alias for dict[str, str]
# (Go: client_list.go line 170)
TranslateUsernamesResponse = dict[str, str]


@dataclass
class GetClientListItemsRequest:
    """Request parameters for the ``GetClientListItems`` method.

    Maps to Go ``GetClientListItemsRequest``
    (client_list.go lines 173-175).
    """

    list_id: str = ""


@dataclass
class GetClientListItemsResponse:
    """Response from the ``GetClientListItems`` method.

    Maps to Go ``GetClientListItemsResponse``
    (client_list.go lines 178-180).  Note: the JSON tag for items is
    ``content``.
    """

    items: list[ListItemContent] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to a dict.

        The Go JSON tag for ``Items`` is ``"content"``.
        """
        return {
            "content": [item.to_dict() for item in self.items],
        }

    @classmethod
    def from_dict(cls, data: dict) -> GetClientListItemsResponse:
        """Deserialize from a dict.

        Reads from the ``"content"`` key per Go JSON tag.
        """
        return cls(
            items=[
                ListItemContent.from_dict(i)
                for i in data.get("content", [])
            ],
        )


# ===================================================================
# Activation models  (Go: client_list_activation.go)
# ===================================================================


@dataclass
class ActivationParams:
    """General activation parameters.

    Maps to Go ``ActivationParams``
    (client_list_activation.go lines 15-21).
    """

    action: str = ""
    comments: str = ""
    network: str = ""
    notification_recipients: list[str] = field(default_factory=list)
    siebel_ticket_id: str = ""

    def to_dict(self) -> dict:
        """Serialize to a dict whose keys match Go JSON struct tags."""
        return {
            "action": self.action,
            "comments": self.comments,
            "network": self.network,
            "notificationRecipients": list(self.notification_recipients),
            "siebelTicketId": self.siebel_ticket_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ActivationParams:
        """Deserialize from a dict whose keys use Go JSON struct tags."""
        return cls(
            action=data.get("action", ""),
            comments=data.get("comments", ""),
            network=data.get("network", ""),
            notification_recipients=data.get("notificationRecipients", []),
            siebel_ticket_id=data.get("siebelTicketId", ""),
        )


@dataclass
class GetActivationRequest:
    """Request parameters for the ``GetActivation`` method.

    Maps to Go ``GetActivationRequest``
    (client_list_activation.go lines 24-26).
    """

    activation_id: int = 0


@dataclass
class GetActivationResponse:
    """Response from the ``GetActivation`` method.

    Maps to Go ``GetActivationResponse``
    (client_list_activation.go lines 29-39).  Flattens embedded
    ``ActivationParams`` fields.
    """

    activation_id: int = 0
    create_date: str = ""
    created_by: str = ""
    fast: bool = False
    initial_activation: bool = False
    activation_status: str = ""
    list_id: str = ""
    version: int = 0
    # Flattened from ActivationParams
    action: str = ""
    comments: str = ""
    network: str = ""
    notification_recipients: list[str] = field(default_factory=list)
    siebel_ticket_id: str = ""

    def to_dict(self) -> dict:
        """Serialize to a dict whose keys match Go JSON struct tags."""
        return {
            "activationId": self.activation_id,
            "createDate": self.create_date,
            "createdBy": self.created_by,
            "fast": self.fast,
            "initialActivation": self.initial_activation,
            "activationStatus": self.activation_status,
            "listId": self.list_id,
            "version": self.version,
            "action": self.action,
            "comments": self.comments,
            "network": self.network,
            "notificationRecipients": list(self.notification_recipients),
            "siebelTicketId": self.siebel_ticket_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GetActivationResponse:
        """Deserialize from a dict whose keys use Go JSON struct tags."""
        return cls(
            activation_id=data.get("activationId", 0),
            create_date=data.get("createDate", ""),
            created_by=data.get("createdBy", ""),
            fast=data.get("fast", False),
            initial_activation=data.get("initialActivation", False),
            activation_status=data.get("activationStatus", ""),
            list_id=data.get("listId", ""),
            version=data.get("version", 0),
            action=data.get("action", ""),
            comments=data.get("comments", ""),
            network=data.get("network", ""),
            notification_recipients=data.get("notificationRecipients", []),
            siebel_ticket_id=data.get("siebelTicketId", ""),
        )


@dataclass
class GetActivationStatusRequest:
    """Request parameters for the ``GetActivationStatus`` method.

    Maps to Go ``GetActivationStatusRequest``
    (client_list_activation.go lines 57-60).
    """

    list_id: str = ""
    network: str = ""


@dataclass
class GetActivationStatusResponse:
    """Response from the ``GetActivationStatus`` method.

    Maps to Go ``GetActivationStatusResponse``
    (client_list_activation.go lines 63-75).
    """

    action: str = ""
    activation_id: int = 0
    activation_status: str = ""
    comments: str = ""
    create_date: str = ""
    created_by: str = ""
    list_id: str = ""
    network: str = ""
    notification_recipients: list[str] = field(default_factory=list)
    siebel_ticket_id: str = ""
    version: int = 0

    def to_dict(self) -> dict:
        """Serialize to a dict whose keys match Go JSON struct tags."""
        return {
            "action": self.action,
            "activationId": self.activation_id,
            "activationStatus": self.activation_status,
            "comments": self.comments,
            "createDate": self.create_date,
            "createdBy": self.created_by,
            "listId": self.list_id,
            "network": self.network,
            "notificationRecipients": list(self.notification_recipients),
            "siebelTicketId": self.siebel_ticket_id,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GetActivationStatusResponse:
        """Deserialize from a dict whose keys use Go JSON struct tags."""
        return cls(
            action=data.get("action", ""),
            activation_id=data.get("activationId", 0),
            activation_status=data.get("activationStatus", ""),
            comments=data.get("comments", ""),
            create_date=data.get("createDate", ""),
            created_by=data.get("createdBy", ""),
            list_id=data.get("listId", ""),
            network=data.get("network", ""),
            notification_recipients=data.get("notificationRecipients", []),
            siebel_ticket_id=data.get("siebelTicketId", ""),
            version=data.get("version", 0),
        )


@dataclass
class CreateActivationRequest:
    """Request parameters for the ``CreateActivation`` method.

    Maps to Go ``CreateActivationRequest``
    (client_list_activation.go lines 42-45).  Flattens embedded
    ``ActivationParams`` fields.
    """

    list_id: str = ""
    # Flattened from ActivationParams
    action: str = ""
    comments: str = ""
    network: str = ""
    notification_recipients: list[str] = field(default_factory=list)
    siebel_ticket_id: str = ""

    def to_dict(self) -> dict:
        """Serialize to a dict whose keys match Go JSON struct tags."""
        return {
            "listId": self.list_id,
            "action": self.action,
            "comments": self.comments,
            "network": self.network,
            "notificationRecipients": list(self.notification_recipients),
            "siebelTicketId": self.siebel_ticket_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CreateActivationRequest:
        """Deserialize from a dict whose keys use Go JSON struct tags."""
        return cls(
            list_id=data.get("listId", ""),
            action=data.get("action", ""),
            comments=data.get("comments", ""),
            network=data.get("network", ""),
            notification_recipients=data.get("notificationRecipients", []),
            siebel_ticket_id=data.get("siebelTicketId", ""),
        )


# ---------------------------------------------------------------------------
# Type aliases for activation models
# (Go: client_list_activation.go lines 48, 51, 54)
# ---------------------------------------------------------------------------

# CreateDeactivationRequest is a type alias for CreateActivationRequest
CreateDeactivationRequest = CreateActivationRequest

# CreateActivationResponse is a type alias for GetActivationStatusResponse
CreateActivationResponse = GetActivationStatusResponse

# CreateDeactivationResponse is a type alias for CreateActivationResponse
CreateDeactivationResponse = CreateActivationResponse
