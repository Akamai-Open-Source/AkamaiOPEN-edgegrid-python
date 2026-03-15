"""Request and response model dataclasses for the IAM service client."""
# pylint: disable=too-many-instance-attributes,too-many-lines
from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# AccessLevel constants (from api_clients.go)
# ---------------------------------------------------------------------------
READ_WRITE_LEVEL = "READ-WRITE"
READ_ONLY_LEVEL = "READ-ONLY"
READ_LEVEL = "READ"
CREDENTIAL_READ_ONLY_LEVEL = "CREDENTIAL-READ-ONLY"
CREDENTIAL_READ_WRITE_LEVEL = "CREDENTIAL-READ-WRITE"

# ---------------------------------------------------------------------------
# CredentialStatus constants (from api_clients_credentials.go)
# ---------------------------------------------------------------------------
CREDENTIAL_ACTIVE = "ACTIVE"
CREDENTIAL_INACTIVE = "INACTIVE"
CREDENTIAL_DELETED = "DELETED"

# ---------------------------------------------------------------------------
# ClientType constants (from helper.go)
# ---------------------------------------------------------------------------
USER_CLIENT_TYPE = "USER_CLIENT"
SERVICE_ACCOUNT_CLIENT_TYPE = "SERVICE_ACCOUNT"
CLIENT_CLIENT_TYPE = "CLIENT"

# ---------------------------------------------------------------------------
# PropertyUserType constants (from properties.go)
# ---------------------------------------------------------------------------
PROPERTY_USER_TYPE_ALL = "all"
PROPERTY_USER_TYPE_ASSIGNED = "assigned"
PROPERTY_USER_TYPE_BLOCKED = "blocked"

# ---------------------------------------------------------------------------
# Authentication constants (from user.go)
# ---------------------------------------------------------------------------
MFA_AUTHENTICATION = "MFA"
TFA_AUTHENTICATION = "TFA"
NONE_AUTHENTICATION = "NONE"


# ===========================================================================
# API Clients models (from api_clients.go)
# ===========================================================================


@dataclass
class LockAPIClientRequest:
    """Request parameters for the LockAPIClient endpoint."""
    client_id: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"clientId": self.client_id}

    @classmethod
    def from_dict(cls, data: dict) -> LockAPIClientRequest:
        """Deserialize from dict using JSON field names."""
        return cls(client_id=data.get("clientId", ""))


@dataclass
class UnlockAPIClientRequest:
    """Request parameters for the UnlockAPIClient endpoint."""
    client_id: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"clientId": self.client_id}

    @classmethod
    def from_dict(cls, data: dict) -> UnlockAPIClientRequest:
        """Deserialize from dict using JSON field names."""
        return cls(client_id=data.get("clientId", ""))


@dataclass
class ListAPIClientsActions:
    """Actions available for a listed API client."""
    delete: bool = False
    deactivate_all: bool = False
    edit: bool = False
    lock: bool = False
    transfer: bool = False
    unlock: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "delete": self.delete,
            "deactivateAll": self.deactivate_all,
            "edit": self.edit,
            "lock": self.lock,
            "transfer": self.transfer,
            "unlock": self.unlock,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListAPIClientsActions:
        """Deserialize from dict using JSON field names."""
        return cls(
            delete=data.get("delete", False),
            deactivate_all=data.get("deactivateAll", False),
            edit=data.get("edit", False),
            lock=data.get("lock", False),
            transfer=data.get("transfer", False),
            unlock=data.get("unlock", False),
        )


@dataclass
class APIClientActions:
    """Actions available for a detailed API client view."""
    delete: bool = False
    deactivate_all: bool = False
    edit: bool = False
    edit_apis: bool = False
    edit_auth: bool = False
    edit_groups: bool = False
    edit_ip_acl: bool = False
    edit_switch_account: bool = False
    lock: bool = False
    transfer: bool = False
    unlock: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "delete": self.delete,
            "deactivateAll": self.deactivate_all,
            "edit": self.edit,
            "editApis": self.edit_apis,
            "editAuth": self.edit_auth,
            "editGroups": self.edit_groups,
            "editIpAcl": self.edit_ip_acl,
            "editSwitchAccount": self.edit_switch_account,
            "lock": self.lock,
            "transfer": self.transfer,
            "unlock": self.unlock,
        }

    @classmethod
    def from_dict(cls, data: dict) -> APIClientActions:
        """Deserialize from dict using JSON field names."""
        return cls(
            delete=data.get("delete", False),
            deactivate_all=data.get("deactivateAll", False),
            edit=data.get("edit", False),
            edit_apis=data.get("editApis", False),
            edit_auth=data.get("editAuth", False),
            edit_groups=data.get("editGroups", False),
            edit_ip_acl=data.get("editIpAcl", False),
            edit_switch_account=data.get("editSwitchAccount", False),
            lock=data.get("lock", False),
            transfer=data.get("transfer", False),
            unlock=data.get("unlock", False),
        )


@dataclass
class CredentialActions:
    """Actions available for a credential."""
    deactivate: bool = False
    delete: bool = False
    activate: bool = False
    edit_description: bool = False
    edit_expiration: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "deactivate": self.deactivate,
            "delete": self.delete,
            "activate": self.activate,
            "editDescription": self.edit_description,
            "editExpiration": self.edit_expiration,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CredentialActions:
        """Deserialize from dict using JSON field names."""
        return cls(
            deactivate=data.get("deactivate", False),
            delete=data.get("delete", False),
            activate=data.get("activate", False),
            edit_description=data.get("editDescription", False),
            edit_expiration=data.get("editExpiration", False),
        )


@dataclass
class API:
    """Describes an API endpoint accessible to a client."""
    access_level: str = ""
    api_id: int = 0
    api_name: str = ""
    description: str = ""
    documentation_url: str = ""
    endpoint: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "accessLevel": self.access_level,
            "apiId": self.api_id,
            "apiName": self.api_name,
            "description": self.description,
            "documentationUrl": self.documentation_url,
            "endPoint": self.endpoint,
        }

    @classmethod
    def from_dict(cls, data: dict) -> API:
        """Deserialize from dict using JSON field names."""
        return cls(
            access_level=data.get("accessLevel", ""),
            api_id=data.get("apiId", 0),
            api_name=data.get("apiName", ""),
            description=data.get("description", ""),
            documentation_url=data.get("documentationUrl", ""),
            endpoint=data.get("endPoint", ""),
        )


@dataclass
class APIRequestItem:
    """API access item in a create/update request."""
    api_id: int = 0
    access_level: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "apiId": self.api_id,
            "accessLevel": self.access_level,
        }

    @classmethod
    def from_dict(cls, data: dict) -> APIRequestItem:
        """Deserialize from dict using JSON field names."""
        return cls(
            api_id=data.get("apiId", 0),
            access_level=data.get("accessLevel", ""),
        )


@dataclass
class APIAccess:
    """Describes API access configuration."""
    all_accessible_apis: bool = False
    apis: list[API] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "allAccessibleApis": self.all_accessible_apis,
            "apis": [a.to_dict() for a in self.apis],
        }

    @classmethod
    def from_dict(cls, data: dict) -> APIAccess:
        """Deserialize from dict using JSON field names."""
        return cls(
            all_accessible_apis=data.get("allAccessibleApis", False),
            apis=[API.from_dict(a) for a in data.get("apis") or []],
        )


@dataclass
class APIAccessRequest:
    """API access configuration for create/update requests."""
    all_accessible_apis: bool = False
    apis: list[APIRequestItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "allAccessibleApis": self.all_accessible_apis,
            "apis": [a.to_dict() for a in self.apis],
        }

    @classmethod
    def from_dict(cls, data: dict) -> APIAccessRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            all_accessible_apis=data.get("allAccessibleApis", False),
            apis=[APIRequestItem.from_dict(a) for a in data.get("apis") or []],
        )


@dataclass
class APIClientCredential:
    """Describes an API client credential."""
    actions: CredentialActions | None = None
    client_token: str = ""
    created_on: str = ""
    credential_id: int = 0
    description: str = ""
    expires_on: str = ""
    status: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "clientToken": self.client_token,
            "createdOn": self.created_on,
            "credentialId": self.credential_id,
            "description": self.description,
            "expiresOn": self.expires_on,
            "status": self.status,
        }
        if self.actions is not None:
            result["actions"] = self.actions.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> APIClientCredential:
        """Deserialize from dict using JSON field names."""
        return cls(
            actions=CredentialActions.from_dict(data["actions"]) if data.get("actions") else None,
            client_token=data.get("clientToken", ""),
            created_on=data.get("createdOn", ""),
            credential_id=data.get("credentialId", 0),
            description=data.get("description", ""),
            expires_on=data.get("expiresOn", ""),
            status=data.get("status", ""),
        )


@dataclass
class CreateAPIClientCredential:
    """Describes a newly created API client credential including the secret."""
    actions: CredentialActions | None = None
    client_secret: str = ""
    client_token: str = ""
    created_on: str = ""
    credential_id: int = 0
    description: str = ""
    expires_on: str = ""
    status: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "clientSecret": self.client_secret,
            "clientToken": self.client_token,
            "createdOn": self.created_on,
            "credentialId": self.credential_id,
            "description": self.description,
            "expiresOn": self.expires_on,
            "status": self.status,
        }
        if self.actions is not None:
            result["actions"] = self.actions.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> CreateAPIClientCredential:
        """Deserialize from dict using JSON field names."""
        return cls(
            actions=CredentialActions.from_dict(data["actions"]) if data.get("actions") else None,
            client_secret=data.get("clientSecret", ""),
            client_token=data.get("clientToken", ""),
            created_on=data.get("createdOn", ""),
            credential_id=data.get("credentialId", 0),
            description=data.get("description", ""),
            expires_on=data.get("expiresOn", ""),
            status=data.get("status", ""),
        )


@dataclass
class ClientGroup:
    """Describes a group assigned to an API client."""
    group_id: int = 0
    group_name: str = ""
    is_blocked: bool = False
    parent_group_id: int = 0
    role_description: str = ""
    role_id: int = 0
    role_name: str = ""
    subgroups: list[ClientGroup] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "groupId": self.group_id,
            "groupName": self.group_name,
            "isBlocked": self.is_blocked,
            "parentGroupId": self.parent_group_id,
            "roleDescription": self.role_description,
            "roleId": self.role_id,
            "roleName": self.role_name,
            "subGroups": [s.to_dict() for s in self.subgroups],
        }

    @classmethod
    def from_dict(cls, data: dict) -> ClientGroup:
        """Deserialize from dict using JSON field names."""
        return cls(
            group_id=data.get("groupId", 0),
            group_name=data.get("groupName", ""),
            is_blocked=data.get("isBlocked", False),
            parent_group_id=data.get("parentGroupId", 0),
            role_description=data.get("roleDescription", ""),
            role_id=data.get("roleId", 0),
            role_name=data.get("roleName", ""),
            subgroups=[ClientGroup.from_dict(s) for s in data.get("subGroups") or []],
        )


@dataclass
class ClientGroupRequestItem:
    """Group assignment item for API client create/update requests."""
    group_id: int = 0
    role_id: int = 0
    subgroups: list[ClientGroupRequestItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "groupId": self.group_id,
            "roleId": self.role_id,
            "subGroups": [s.to_dict() for s in self.subgroups],
        }

    @classmethod
    def from_dict(cls, data: dict) -> ClientGroupRequestItem:
        """Deserialize from dict using JSON field names."""
        return cls(
            group_id=data.get("groupId", 0),
            role_id=data.get("roleId", 0),
            subgroups=[ClientGroupRequestItem.from_dict(s) for s in data.get("subGroups") or []],
        )


@dataclass
class GroupAccess:
    """Describes group access configuration for an API client."""
    clone_authorized_user_groups: bool = False
    groups: list[ClientGroup] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "cloneAuthorizedUserGroups": self.clone_authorized_user_groups,
            "groups": [g.to_dict() for g in self.groups],
        }

    @classmethod
    def from_dict(cls, data: dict) -> GroupAccess:
        """Deserialize from dict using JSON field names."""
        return cls(
            clone_authorized_user_groups=data.get("cloneAuthorizedUserGroups", False),
            groups=[ClientGroup.from_dict(g) for g in data.get("groups") or []],
        )


@dataclass
class GroupAccessRequest:
    """Group access configuration for create/update requests."""
    clone_authorized_user_groups: bool = False
    groups: list[ClientGroupRequestItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "cloneAuthorizedUserGroups": self.clone_authorized_user_groups,
            "groups": [g.to_dict() for g in self.groups],
        }

    @classmethod
    def from_dict(cls, data: dict) -> GroupAccessRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            clone_authorized_user_groups=data.get("cloneAuthorizedUserGroups", False),
            groups=[ClientGroupRequestItem.from_dict(g) for g in data.get("groups") or []],
        )


@dataclass
class IPACL:
    """Describes IP ACL configuration for an API client."""
    cidr: list[str] = field(default_factory=list)
    enable: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "cidr": list(self.cidr),
            "enable": self.enable,
        }

    @classmethod
    def from_dict(cls, data: dict) -> IPACL:
        """Deserialize from dict using JSON field names."""
        return cls(
            cidr=list(data.get("cidr") or []),
            enable=data.get("enable", False),
        )


@dataclass
class CPCodeAccess:
    """Describes CP code access for purge options."""
    all_current_and_new_cp_codes: bool = False
    cp_codes: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "allCurrentAndNewCpcodes": self.all_current_and_new_cp_codes,
            "cpcodes": list(self.cp_codes),
        }

    @classmethod
    def from_dict(cls, data: dict) -> CPCodeAccess:
        """Deserialize from dict using JSON field names."""
        return cls(
            all_current_and_new_cp_codes=data.get("allCurrentAndNewCpcodes", False),
            cp_codes=list(data.get("cpcodes") or []),
        )


@dataclass
class PurgeOptions:
    """Describes purge options for an API client."""
    can_purge_by_cache_tag: bool = False
    can_purge_by_cp_code: bool = False
    cp_code_access: CPCodeAccess | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "canPurgeByCacheTag": self.can_purge_by_cache_tag,
            "canPurgeByCpcode": self.can_purge_by_cp_code,
        }
        if self.cp_code_access is not None:
            result["cpCodeAccess"] = self.cp_code_access.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> PurgeOptions:
        """Deserialize from dict using JSON field names."""
        return cls(
            can_purge_by_cache_tag=data.get("canPurgeByCacheTag", False),
            can_purge_by_cp_code=data.get("canPurgeByCpcode", False),
            cp_code_access=CPCodeAccess.from_dict(data["cpCodeAccess"])
            if data.get("cpCodeAccess") else None,
        )


@dataclass
class APIClient:
    """Describes an API client."""
    access_token: str = ""
    active_credential_count: int = 0
    allow_account_switch: bool = False
    authorized_users: list[str] = field(default_factory=list)
    can_auto_create_credential: bool = False
    client_description: str = ""
    client_id: str = ""
    client_name: str = ""
    client_type: str = ""
    created_by: str = ""
    created_date: str = ""
    is_locked: bool = False
    notification_emails: list[str] = field(default_factory=list)
    service_consumer_token: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "accessToken": self.access_token,
            "activeCredentialCount": self.active_credential_count,
            "allowAccountSwitch": self.allow_account_switch,
            "authorizedUsers": list(self.authorized_users),
            "canAutoCreateCredential": self.can_auto_create_credential,
            "clientDescription": self.client_description,
            "clientId": self.client_id,
            "clientName": self.client_name,
            "clientType": self.client_type,
            "createdBy": self.created_by,
            "createdDate": self.created_date,
            "isLocked": self.is_locked,
            "notificationEmails": list(self.notification_emails),
            "serviceConsumerToken": self.service_consumer_token,
        }

    @classmethod
    def from_dict(cls, data: dict) -> APIClient:
        """Deserialize from dict using JSON field names."""
        return cls(
            access_token=data.get("accessToken", ""),
            active_credential_count=data.get("activeCredentialCount", 0),
            allow_account_switch=data.get("allowAccountSwitch", False),
            authorized_users=list(data.get("authorizedUsers") or []),
            can_auto_create_credential=data.get("canAutoCreateCredential", False),
            client_description=data.get("clientDescription", ""),
            client_id=data.get("clientId", ""),
            client_name=data.get("clientName", ""),
            client_type=data.get("clientType", ""),
            created_by=data.get("createdBy", ""),
            created_date=data.get("createdDate", ""),
            is_locked=data.get("isLocked", False),
            notification_emails=list(data.get("notificationEmails") or []),
            service_consumer_token=data.get("serviceConsumerToken", ""),
        )


@dataclass
class ListAPIClientsRequest:
    """Request parameters for the ListAPIClients endpoint."""
    actions: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"actions": self.actions}

    @classmethod
    def from_dict(cls, data: dict) -> ListAPIClientsRequest:
        """Deserialize from dict using JSON field names."""
        return cls(actions=data.get("actions", False))


@dataclass
class ListAPIClientsItem:
    """Describes an API client in a list response."""
    access_token: str = ""
    actions: ListAPIClientsActions | None = None
    active_credential_count: int = 0
    allow_account_switch: bool = False
    authorized_users: list[str] = field(default_factory=list)
    can_auto_create_credential: bool = False
    client_description: str = ""
    client_id: str = ""
    client_name: str = ""
    client_type: str = ""
    created_by: str = ""
    created_date: str = ""
    is_locked: bool = False
    notification_emails: list[str] = field(default_factory=list)
    service_consumer_token: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "accessToken": self.access_token,
            "activeCredentialCount": self.active_credential_count,
            "allowAccountSwitch": self.allow_account_switch,
            "authorizedUsers": list(self.authorized_users),
            "canAutoCreateCredential": self.can_auto_create_credential,
            "clientDescription": self.client_description,
            "clientId": self.client_id,
            "clientName": self.client_name,
            "clientType": self.client_type,
            "createdBy": self.created_by,
            "createdDate": self.created_date,
            "isLocked": self.is_locked,
            "notificationEmails": list(self.notification_emails),
            "serviceConsumerToken": self.service_consumer_token,
        }
        if self.actions is not None:
            result["actions"] = self.actions.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> ListAPIClientsItem:
        """Deserialize from dict using JSON field names."""
        return cls(
            access_token=data.get("accessToken", ""),
            actions=ListAPIClientsActions.from_dict(data["actions"])
            if data.get("actions") else None,
            active_credential_count=data.get("activeCredentialCount", 0),
            allow_account_switch=data.get("allowAccountSwitch", False),
            authorized_users=list(data.get("authorizedUsers") or []),
            can_auto_create_credential=data.get("canAutoCreateCredential", False),
            client_description=data.get("clientDescription", ""),
            client_id=data.get("clientId", ""),
            client_name=data.get("clientName", ""),
            client_type=data.get("clientType", ""),
            created_by=data.get("createdBy", ""),
            created_date=data.get("createdDate", ""),
            is_locked=data.get("isLocked", False),
            notification_emails=list(data.get("notificationEmails") or []),
            service_consumer_token=data.get("serviceConsumerToken", ""),
        )


@dataclass
class GetAPIClientRequest:
    """Request parameters for the GetAPIClient endpoint."""
    client_id: str = ""
    actions: bool = False
    group_access: bool = False
    api_access: bool = False
    credentials: bool = False
    ip_acl: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "clientId": self.client_id,
            "actions": self.actions,
            "groupAccess": self.group_access,
            "apiAccess": self.api_access,
            "credentials": self.credentials,
            "ipAcl": self.ip_acl,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GetAPIClientRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            client_id=data.get("clientId", ""),
            actions=data.get("actions", False),
            group_access=data.get("groupAccess", False),
            api_access=data.get("apiAccess", False),
            credentials=data.get("credentials", False),
            ip_acl=data.get("ipAcl", False),
        )


@dataclass
class CreateAPIClientResponse:
    """Response for the CreateAPIClient endpoint."""
    access_token: str = ""
    actions: APIClientActions | None = None
    active_credential_count: int = 0
    allow_account_switch: bool = False
    api_access: APIAccess | None = None
    authorized_users: list[str] = field(default_factory=list)
    base_url: str = ""
    can_auto_create_credential: bool = False
    client_description: str = ""
    client_id: str = ""
    client_name: str = ""
    client_type: str = ""
    created_by: str = ""
    created_date: str = ""
    credentials: list[CreateAPIClientCredential] = field(default_factory=list)
    group_access: GroupAccess | None = None
    ip_acl: IPACL | None = None
    is_locked: bool = False
    notification_emails: list[str] = field(default_factory=list)
    purge_options: PurgeOptions | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "accessToken": self.access_token,
            "activeCredentialCount": self.active_credential_count,
            "allowAccountSwitch": self.allow_account_switch,
            "authorizedUsers": list(self.authorized_users),
            "baseURL": self.base_url,
            "canAutoCreateCredential": self.can_auto_create_credential,
            "clientDescription": self.client_description,
            "clientId": self.client_id,
            "clientName": self.client_name,
            "clientType": self.client_type,
            "createdBy": self.created_by,
            "createdDate": self.created_date,
            "credentials": [c.to_dict() for c in self.credentials],
            "isLocked": self.is_locked,
            "notificationEmails": list(self.notification_emails),
        }
        if self.actions is not None:
            result["actions"] = self.actions.to_dict()
        if self.api_access is not None:
            result["apiAccess"] = self.api_access.to_dict()
        if self.group_access is not None:
            result["groupAccess"] = self.group_access.to_dict()
        if self.ip_acl is not None:
            result["ipAcl"] = self.ip_acl.to_dict()
        if self.purge_options is not None:
            result["purgeOptions"] = self.purge_options.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> CreateAPIClientResponse:
        """Deserialize from dict using JSON field names."""
        return cls(
            access_token=data.get("accessToken", ""),
            actions=APIClientActions.from_dict(data["actions"])
            if data.get("actions") else None,
            active_credential_count=data.get("activeCredentialCount", 0),
            allow_account_switch=data.get("allowAccountSwitch", False),
            api_access=APIAccess.from_dict(data["apiAccess"])
            if data.get("apiAccess") else None,
            authorized_users=list(data.get("authorizedUsers") or []),
            base_url=data.get("baseURL", ""),
            can_auto_create_credential=data.get("canAutoCreateCredential", False),
            client_description=data.get("clientDescription", ""),
            client_id=data.get("clientId", ""),
            client_name=data.get("clientName", ""),
            client_type=data.get("clientType", ""),
            created_by=data.get("createdBy", ""),
            created_date=data.get("createdDate", ""),
            credentials=[CreateAPIClientCredential.from_dict(c)
                         for c in data.get("credentials") or []],
            group_access=GroupAccess.from_dict(data["groupAccess"])
            if data.get("groupAccess") else None,
            ip_acl=IPACL.from_dict(data["ipAcl"]) if data.get("ipAcl") else None,
            is_locked=data.get("isLocked", False),
            notification_emails=list(data.get("notificationEmails") or []),
            purge_options=PurgeOptions.from_dict(data["purgeOptions"])
            if data.get("purgeOptions") else None,
        )


@dataclass
class GetAPIClientResponse:
    """Response for the GetAPIClient endpoint."""
    access_token: str = ""
    actions: APIClientActions | None = None
    active_credential_count: int = 0
    allow_account_switch: bool = False
    api_access: APIAccess | None = None
    authorized_users: list[str] = field(default_factory=list)
    base_url: str = ""
    can_auto_create_credential: bool = False
    client_description: str = ""
    client_id: str = ""
    client_name: str = ""
    client_type: str = ""
    created_by: str = ""
    created_date: str = ""
    credentials: list[APIClientCredential] = field(default_factory=list)
    group_access: GroupAccess | None = None
    ip_acl: IPACL | None = None
    is_locked: bool = False
    notification_emails: list[str] = field(default_factory=list)
    purge_options: PurgeOptions | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "accessToken": self.access_token,
            "activeCredentialCount": self.active_credential_count,
            "allowAccountSwitch": self.allow_account_switch,
            "authorizedUsers": list(self.authorized_users),
            "baseURL": self.base_url,
            "canAutoCreateCredential": self.can_auto_create_credential,
            "clientDescription": self.client_description,
            "clientId": self.client_id,
            "clientName": self.client_name,
            "clientType": self.client_type,
            "createdBy": self.created_by,
            "createdDate": self.created_date,
            "credentials": [c.to_dict() for c in self.credentials],
            "isLocked": self.is_locked,
            "notificationEmails": list(self.notification_emails),
        }
        if self.actions is not None:
            result["actions"] = self.actions.to_dict()
        if self.api_access is not None:
            result["apiAccess"] = self.api_access.to_dict()
        if self.group_access is not None:
            result["groupAccess"] = self.group_access.to_dict()
        if self.ip_acl is not None:
            result["ipAcl"] = self.ip_acl.to_dict()
        if self.purge_options is not None:
            result["purgeOptions"] = self.purge_options.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> GetAPIClientResponse:
        """Deserialize from dict using JSON field names."""
        return cls(
            access_token=data.get("accessToken", ""),
            actions=APIClientActions.from_dict(data["actions"])
            if data.get("actions") else None,
            active_credential_count=data.get("activeCredentialCount", 0),
            allow_account_switch=data.get("allowAccountSwitch", False),
            api_access=APIAccess.from_dict(data["apiAccess"])
            if data.get("apiAccess") else None,
            authorized_users=list(data.get("authorizedUsers") or []),
            base_url=data.get("baseURL", ""),
            can_auto_create_credential=data.get("canAutoCreateCredential", False),
            client_description=data.get("clientDescription", ""),
            client_id=data.get("clientId", ""),
            client_name=data.get("clientName", ""),
            client_type=data.get("clientType", ""),
            created_by=data.get("createdBy", ""),
            created_date=data.get("createdDate", ""),
            credentials=[APIClientCredential.from_dict(c)
                         for c in data.get("credentials") or []],
            group_access=GroupAccess.from_dict(data["groupAccess"])
            if data.get("groupAccess") else None,
            ip_acl=IPACL.from_dict(data["ipAcl"]) if data.get("ipAcl") else None,
            is_locked=data.get("isLocked", False),
            notification_emails=list(data.get("notificationEmails") or []),
            purge_options=PurgeOptions.from_dict(data["purgeOptions"])
            if data.get("purgeOptions") else None,
        )


@dataclass
class CreateAPIClientRequest:
    """Request body for the CreateAPIClient endpoint."""
    allow_account_switch: bool = False
    api_access: APIAccessRequest | None = None
    authorized_users: list[str] = field(default_factory=list)
    can_auto_create_credential: bool = False
    client_description: str = ""
    client_name: str = ""
    client_type: str = ""
    create_credential: bool = False
    group_access: GroupAccessRequest | None = None
    ip_acl: IPACL | None = None
    notification_emails: list[str] = field(default_factory=list)
    purge_options: PurgeOptions | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "allowAccountSwitch": self.allow_account_switch,
            "authorizedUsers": list(self.authorized_users),
            "canAutoCreateCredential": self.can_auto_create_credential,
            "clientDescription": self.client_description,
            "clientName": self.client_name,
            "clientType": self.client_type,
            "createCredential": self.create_credential,
            "notificationEmails": list(self.notification_emails),
        }
        if self.api_access is not None:
            result["apiAccess"] = self.api_access.to_dict()
        if self.group_access is not None:
            result["groupAccess"] = self.group_access.to_dict()
        if self.ip_acl is not None:
            result["ipAcl"] = self.ip_acl.to_dict()
        if self.purge_options is not None:
            result["purgeOptions"] = self.purge_options.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> CreateAPIClientRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            allow_account_switch=data.get("allowAccountSwitch", False),
            api_access=APIAccessRequest.from_dict(data["apiAccess"])
            if data.get("apiAccess") else None,
            authorized_users=list(data.get("authorizedUsers") or []),
            can_auto_create_credential=data.get("canAutoCreateCredential", False),
            client_description=data.get("clientDescription", ""),
            client_name=data.get("clientName", ""),
            client_type=data.get("clientType", ""),
            create_credential=data.get("createCredential", False),
            group_access=GroupAccessRequest.from_dict(data["groupAccess"])
            if data.get("groupAccess") else None,
            ip_acl=IPACL.from_dict(data["ipAcl"]) if data.get("ipAcl") else None,
            notification_emails=list(data.get("notificationEmails") or []),
            purge_options=PurgeOptions.from_dict(data["purgeOptions"])
            if data.get("purgeOptions") else None,
        )


@dataclass
class UpdateAPIClientRequestBody:
    """Request body for updating an API client."""
    allow_account_switch: bool = False
    api_access: APIAccessRequest | None = None
    authorized_users: list[str] = field(default_factory=list)
    can_auto_create_credential: bool = False
    client_description: str = ""
    client_name: str = ""
    client_type: str = ""
    group_access: GroupAccessRequest | None = None
    ip_acl: IPACL | None = None
    notification_emails: list[str] = field(default_factory=list)
    purge_options: PurgeOptions | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "allowAccountSwitch": self.allow_account_switch,
            "authorizedUsers": list(self.authorized_users),
            "canAutoCreateCredential": self.can_auto_create_credential,
            "clientDescription": self.client_description,
            "clientName": self.client_name,
            "clientType": self.client_type,
            "notificationEmails": list(self.notification_emails),
        }
        if self.api_access is not None:
            result["apiAccess"] = self.api_access.to_dict()
        if self.group_access is not None:
            result["groupAccess"] = self.group_access.to_dict()
        if self.ip_acl is not None:
            result["ipAcl"] = self.ip_acl.to_dict()
        if self.purge_options is not None:
            result["purgeOptions"] = self.purge_options.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> UpdateAPIClientRequestBody:
        """Deserialize from dict using JSON field names."""
        return cls(
            allow_account_switch=data.get("allowAccountSwitch", False),
            api_access=APIAccessRequest.from_dict(data["apiAccess"])
            if data.get("apiAccess") else None,
            authorized_users=list(data.get("authorizedUsers") or []),
            can_auto_create_credential=data.get("canAutoCreateCredential", False),
            client_description=data.get("clientDescription", ""),
            client_name=data.get("clientName", ""),
            client_type=data.get("clientType", ""),
            group_access=GroupAccessRequest.from_dict(data["groupAccess"])
            if data.get("groupAccess") else None,
            ip_acl=IPACL.from_dict(data["ipAcl"]) if data.get("ipAcl") else None,
            notification_emails=list(data.get("notificationEmails") or []),
            purge_options=PurgeOptions.from_dict(data["purgeOptions"])
            if data.get("purgeOptions") else None,
        )


@dataclass
class UpdateAPIClientRequest:
    """Request for the UpdateAPIClient endpoint."""
    client_id: str = ""
    body: UpdateAPIClientRequestBody | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {"clientId": self.client_id}
        if self.body is not None:
            result["body"] = self.body.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> UpdateAPIClientRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            client_id=data.get("clientId", ""),
            body=UpdateAPIClientRequestBody.from_dict(data["body"])
            if data.get("body") else None,
        )


@dataclass
class DeleteAPIClientRequest:
    """Request parameters for the DeleteAPIClient endpoint."""
    client_id: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"clientId": self.client_id}

    @classmethod
    def from_dict(cls, data: dict) -> DeleteAPIClientRequest:
        """Deserialize from dict using JSON field names."""
        return cls(client_id=data.get("clientId", ""))


# ===========================================================================
# Credential models (from api_clients_credentials.go)
# ===========================================================================


@dataclass
class CreateCredentialRequest:
    """Request parameters for the CreateCredential endpoint."""
    client_id: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"clientId": self.client_id}

    @classmethod
    def from_dict(cls, data: dict) -> CreateCredentialRequest:
        """Deserialize from dict using JSON field names."""
        return cls(client_id=data.get("clientId", ""))


@dataclass
class ListCredentialsRequest:
    """Request parameters for the ListCredentials endpoint."""
    client_id: str = ""
    actions: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "clientId": self.client_id,
            "actions": self.actions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListCredentialsRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            client_id=data.get("clientId", ""),
            actions=data.get("actions", False),
        )


@dataclass
class GetCredentialRequest:
    """Request parameters for the GetCredential endpoint."""
    credential_id: int = 0
    client_id: str = ""
    actions: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "credentialId": self.credential_id,
            "clientId": self.client_id,
            "actions": self.actions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GetCredentialRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            credential_id=data.get("credentialId", 0),
            client_id=data.get("clientId", ""),
            actions=data.get("actions", False),
        )


@dataclass
class UpdateCredentialRequestBody:
    """Request body for updating a credential."""
    description: str = ""
    expires_on: str = ""
    status: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "expiresOn": self.expires_on,
            "status": self.status,
        }
        if self.description:
            result["description"] = self.description
        return result

    @classmethod
    def from_dict(cls, data: dict) -> UpdateCredentialRequestBody:
        """Deserialize from dict using JSON field names."""
        return cls(
            description=data.get("description", ""),
            expires_on=data.get("expiresOn", ""),
            status=data.get("status", ""),
        )


@dataclass
class UpdateCredentialRequest:
    """Request for the UpdateCredential endpoint."""
    credential_id: int = 0
    client_id: str = ""
    body: UpdateCredentialRequestBody | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "credentialId": self.credential_id,
            "clientId": self.client_id,
        }
        if self.body is not None:
            result["body"] = self.body.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> UpdateCredentialRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            credential_id=data.get("credentialId", 0),
            client_id=data.get("clientId", ""),
            body=UpdateCredentialRequestBody.from_dict(data["body"])
            if data.get("body") else None,
        )


@dataclass
class DeleteCredentialRequest:
    """Request parameters for the DeleteCredential endpoint."""
    credential_id: int = 0
    client_id: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "credentialId": self.credential_id,
            "clientId": self.client_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> DeleteCredentialRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            credential_id=data.get("credentialId", 0),
            client_id=data.get("clientId", ""),
        )


@dataclass
class DeactivateCredentialRequest:
    """Request parameters for the DeactivateCredential endpoint."""
    credential_id: int = 0
    client_id: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "credentialId": self.credential_id,
            "clientId": self.client_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> DeactivateCredentialRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            credential_id=data.get("credentialId", 0),
            client_id=data.get("clientId", ""),
        )


@dataclass
class DeactivateCredentialsRequest:
    """Request parameters for the DeactivateCredentials endpoint."""
    client_id: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"clientId": self.client_id}

    @classmethod
    def from_dict(cls, data: dict) -> DeactivateCredentialsRequest:
        """Deserialize from dict using JSON field names."""
        return cls(client_id=data.get("clientId", ""))


@dataclass
class CreateCredentialResponse:
    """Response for the CreateCredential endpoint."""
    client_secret: str = ""
    client_token: str = ""
    created_on: str = ""
    credential_id: int = 0
    description: str = ""
    expires_on: str = ""
    status: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "clientSecret": self.client_secret,
            "clientToken": self.client_token,
            "createdOn": self.created_on,
            "credentialId": self.credential_id,
            "description": self.description,
            "expiresOn": self.expires_on,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CreateCredentialResponse:
        """Deserialize from dict using JSON field names."""
        return cls(
            client_secret=data.get("clientSecret", ""),
            client_token=data.get("clientToken", ""),
            created_on=data.get("createdOn", ""),
            credential_id=data.get("credentialId", 0),
            description=data.get("description", ""),
            expires_on=data.get("expiresOn", ""),
            status=data.get("status", ""),
        )


@dataclass
class Credential:
    """Describes an API credential."""
    client_token: str = ""
    created_on: str = ""
    credential_id: int = 0
    description: str = ""
    expires_on: str = ""
    status: str = ""
    max_allowed_expiry: str = ""
    actions: CredentialActions | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "clientToken": self.client_token,
            "createdOn": self.created_on,
            "credentialId": self.credential_id,
            "description": self.description,
            "expiresOn": self.expires_on,
            "status": self.status,
            "maxAllowedExpiry": self.max_allowed_expiry,
        }
        if self.actions is not None:
            result["actions"] = self.actions.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> Credential:
        """Deserialize from dict using JSON field names."""
        return cls(
            client_token=data.get("clientToken", ""),
            created_on=data.get("createdOn", ""),
            credential_id=data.get("credentialId", 0),
            description=data.get("description", ""),
            expires_on=data.get("expiresOn", ""),
            status=data.get("status", ""),
            max_allowed_expiry=data.get("maxAllowedExpiry", ""),
            actions=CredentialActions.from_dict(data["actions"])
            if data.get("actions") else None,
        )


@dataclass
class UpdateCredentialResponse:
    """Response for the UpdateCredential endpoint."""
    status: str = ""
    expires_on: str = ""
    description: str | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "status": self.status,
            "expiresOn": self.expires_on,
        }
        if self.description is not None:
            result["description"] = self.description
        return result

    @classmethod
    def from_dict(cls, data: dict) -> UpdateCredentialResponse:
        """Deserialize from dict using JSON field names."""
        return cls(
            status=data.get("status", ""),
            expires_on=data.get("expiresOn", ""),
            description=data.get("description"),
        )


# ===========================================================================
# Blocked Properties models (from blocked_properties.go)
# ===========================================================================


@dataclass
class ListBlockedPropertiesRequest:
    """Request parameters for the ListBlockedProperties endpoint."""
    identity_id: str = ""
    group_id: int = 0

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "identityId": self.identity_id,
            "groupId": self.group_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListBlockedPropertiesRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            identity_id=data.get("identityId", ""),
            group_id=data.get("groupId", 0),
        )


@dataclass
class UpdateBlockedPropertiesRequest:
    """Request for the UpdateBlockedProperties endpoint."""
    identity_id: str = ""
    group_id: int = 0
    body: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "identityId": self.identity_id,
            "groupId": self.group_id,
            "body": list(self.body),
        }

    @classmethod
    def from_dict(cls, data: dict) -> UpdateBlockedPropertiesRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            identity_id=data.get("identityId", ""),
            group_id=data.get("groupId", 0),
            body=list(data.get("body") or []),
        )


# ===========================================================================
# CIDR models (from cidr.go)
# ===========================================================================


@dataclass
class CIDRActions:
    """Actions available for a CIDR block."""
    delete: bool = False
    edit: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "delete": self.delete,
            "edit": self.edit,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CIDRActions:
        """Deserialize from dict using JSON field names."""
        return cls(
            delete=data.get("delete", False),
            edit=data.get("edit", False),
        )


@dataclass
class CIDRBlock:
    """Describes a CIDR block in the IP allowlist."""
    actions: CIDRActions | None = None
    cidr_block: str = ""
    cidr_block_id: int = 0
    comments: str | None = None
    created_by: str = ""
    created_date: str = ""
    enabled: bool = False
    modified_by: str = ""
    modified_date: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "cidrBlock": self.cidr_block,
            "cidrBlockId": self.cidr_block_id,
            "createdBy": self.created_by,
            "createdDate": self.created_date,
            "enabled": self.enabled,
            "modifiedBy": self.modified_by,
            "modifiedDate": self.modified_date,
        }
        if self.actions is not None:
            result["actions"] = self.actions.to_dict()
        if self.comments is not None:
            result["comments"] = self.comments
        return result

    @classmethod
    def from_dict(cls, data: dict) -> CIDRBlock:
        """Deserialize from dict using JSON field names."""
        return cls(
            actions=CIDRActions.from_dict(data["actions"]) if data.get("actions") else None,
            cidr_block=data.get("cidrBlock", ""),
            cidr_block_id=data.get("cidrBlockId", 0),
            comments=data.get("comments"),
            created_by=data.get("createdBy", ""),
            created_date=data.get("createdDate", ""),
            enabled=data.get("enabled", False),
            modified_by=data.get("modifiedBy", ""),
            modified_date=data.get("modifiedDate", ""),
        )


@dataclass
class ListCIDRBlocksRequest:
    """Request parameters for the ListCIDRBlocks endpoint."""
    actions: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"actions": self.actions}

    @classmethod
    def from_dict(cls, data: dict) -> ListCIDRBlocksRequest:
        """Deserialize from dict using JSON field names."""
        return cls(actions=data.get("actions", False))


@dataclass
class CreateCIDRBlockRequestBody:
    """Request body for creating a CIDR block."""
    cidr_block: str = ""
    comments: str | None = None
    enabled: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "cidrBlock": self.cidr_block,
            "enabled": self.enabled,
        }
        if self.comments is not None:
            result["comments"] = self.comments
        return result

    @classmethod
    def from_dict(cls, data: dict) -> CreateCIDRBlockRequestBody:
        """Deserialize from dict using JSON field names."""
        return cls(
            cidr_block=data.get("cidrBlock", ""),
            comments=data.get("comments"),
            enabled=data.get("enabled", False),
        )


@dataclass
class CreateCIDRBlockRequest:
    """Request for the CreateCIDRBlock endpoint."""
    body: CreateCIDRBlockRequestBody | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {}
        if self.body is not None:
            result["body"] = self.body.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> CreateCIDRBlockRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            body=CreateCIDRBlockRequestBody.from_dict(data["body"])
            if data.get("body") else None,
        )


@dataclass
class GetCIDRBlockRequest:
    """Request parameters for the GetCIDRBlock endpoint."""
    cidr_block_id: int = 0

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"cidrBlockId": self.cidr_block_id}

    @classmethod
    def from_dict(cls, data: dict) -> GetCIDRBlockRequest:
        """Deserialize from dict using JSON field names."""
        return cls(cidr_block_id=data.get("cidrBlockId", 0))


@dataclass
class UpdateCIDRBlockRequestBody:
    """Request body for updating a CIDR block."""
    cidr_block: str = ""
    comments: str | None = None
    enabled: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "cidrBlock": self.cidr_block,
            "enabled": self.enabled,
        }
        if self.comments is not None:
            result["comments"] = self.comments
        return result

    @classmethod
    def from_dict(cls, data: dict) -> UpdateCIDRBlockRequestBody:
        """Deserialize from dict using JSON field names."""
        return cls(
            cidr_block=data.get("cidrBlock", ""),
            comments=data.get("comments"),
            enabled=data.get("enabled", False),
        )


@dataclass
class UpdateCIDRBlockRequest:
    """Request for the UpdateCIDRBlock endpoint."""
    cidr_block_id: int = 0
    body: UpdateCIDRBlockRequestBody | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {"cidrBlockId": self.cidr_block_id}
        if self.body is not None:
            result["body"] = self.body.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> UpdateCIDRBlockRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            cidr_block_id=data.get("cidrBlockId", 0),
            body=UpdateCIDRBlockRequestBody.from_dict(data["body"])
            if data.get("body") else None,
        )


@dataclass
class DeleteCIDRBlockRequest:
    """Request parameters for the DeleteCIDRBlock endpoint."""
    cidr_block_id: int = 0

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"cidrBlockId": self.cidr_block_id}

    @classmethod
    def from_dict(cls, data: dict) -> DeleteCIDRBlockRequest:
        """Deserialize from dict using JSON field names."""
        return cls(cidr_block_id=data.get("cidrBlockId", 0))


@dataclass
class ValidateCIDRBlockRequest:
    """Request for the ValidateCIDRBlock endpoint."""
    cidr_block: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"cidrBlock": self.cidr_block}

    @classmethod
    def from_dict(cls, data: dict) -> ValidateCIDRBlockRequest:
        """Deserialize from dict using JSON field names."""
        return cls(cidr_block=data.get("cidrBlock", ""))


# ===========================================================================
# Group models (from groups.go)
# ===========================================================================


@dataclass
class GroupActions:
    """Actions available for a group."""
    delete: bool = False
    edit: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "delete": self.delete,
            "edit": self.edit,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GroupActions:
        """Deserialize from dict using JSON field names."""
        return cls(
            delete=data.get("delete", False),
            edit=data.get("edit", False),
        )


@dataclass
class Group:
    """Describes a group in the account hierarchy."""
    actions: GroupActions | None = None
    created_by: str = ""
    created_date: str = ""
    group_id: int = 0
    group_name: str = ""
    modified_by: str = ""
    modified_date: str = ""
    parent_group_id: int = 0
    sub_groups: list[Group] | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "createdBy": self.created_by,
            "createdDate": self.created_date,
            "groupId": self.group_id,
            "groupName": self.group_name,
            "modifiedBy": self.modified_by,
            "modifiedDate": self.modified_date,
            "parentGroupId": self.parent_group_id,
        }
        if self.actions is not None:
            result["actions"] = self.actions.to_dict()
        if self.sub_groups is not None:
            result["subGroups"] = [g.to_dict() for g in self.sub_groups]
        return result

    @classmethod
    def from_dict(cls, data: dict) -> Group:
        """Deserialize from dict using JSON field names."""
        raw_sub = data.get("subGroups")
        return cls(
            actions=GroupActions.from_dict(data["actions"]) if data.get("actions") else None,
            created_by=data.get("createdBy", ""),
            created_date=data.get("createdDate", ""),
            group_id=data.get("groupId", 0),
            group_name=data.get("groupName", ""),
            modified_by=data.get("modifiedBy", ""),
            modified_date=data.get("modifiedDate", ""),
            parent_group_id=data.get("parentGroupId", 0),
            sub_groups=[Group.from_dict(g) for g in raw_sub] if raw_sub is not None else None,
        )


@dataclass
class GetGroupRequest:
    """Request parameters for the GetGroup endpoint."""
    group_id: int = 0
    actions: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "groupId": self.group_id,
            "actions": self.actions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GetGroupRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            group_id=data.get("groupId", 0),
            actions=data.get("actions", False),
        )


@dataclass
class GroupUser:
    """Describes a user within a group."""
    account_id: str = ""
    email: str = ""
    first_name: str = ""
    identity_id: str = ""
    last_login_date: str = ""
    last_name: str = ""
    user_name: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "accountId": self.account_id,
            "email": self.email,
            "firstName": self.first_name,
            "uiIdentityId": self.identity_id,
            "lastLoginDate": self.last_login_date,
            "lastName": self.last_name,
            "uiUserName": self.user_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GroupUser:
        """Deserialize from dict using JSON field names."""
        return cls(
            account_id=data.get("accountId", ""),
            email=data.get("email", ""),
            first_name=data.get("firstName", ""),
            identity_id=data.get("uiIdentityId", ""),
            last_login_date=data.get("lastLoginDate", ""),
            last_name=data.get("lastName", ""),
            user_name=data.get("uiUserName", ""),
        )


@dataclass
class GroupRequest:
    """Request body for creating or renaming a group."""
    group_id: int = 0
    group_name: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"groupName": self.group_name}

    @classmethod
    def from_dict(cls, data: dict) -> GroupRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            group_id=data.get("groupId", 0),
            group_name=data.get("groupName", ""),
        )


@dataclass
class MoveGroupRequest:
    """Request for the MoveGroup endpoint."""
    source_group_id: int = 0
    destination_group_id: int = 0

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "sourceGroupId": self.source_group_id,
            "destinationGroupId": self.destination_group_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> MoveGroupRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            source_group_id=data.get("sourceGroupId", 0),
            destination_group_id=data.get("destinationGroupId", 0),
        )


@dataclass
class ListAffectedUsersRequest:
    """Request parameters for the ListAffectedUsers endpoint."""
    destination_group_id: int = 0
    source_group_id: int = 0
    user_type: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "destinationGroupId": self.destination_group_id,
            "sourceGroupId": self.source_group_id,
            "userType": self.user_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListAffectedUsersRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            destination_group_id=data.get("destinationGroupId", 0),
            source_group_id=data.get("sourceGroupId", 0),
            user_type=data.get("userType", ""),
        )


@dataclass
class ListGroupsRequest:
    """Request parameters for the ListGroups endpoint."""
    actions: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"actions": self.actions}

    @classmethod
    def from_dict(cls, data: dict) -> ListGroupsRequest:
        """Deserialize from dict using JSON field names."""
        return cls(actions=data.get("actions", False))


@dataclass
class RemoveGroupRequest:
    """Request parameters for the RemoveGroup endpoint."""
    group_id: int = 0

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"groupId": self.group_id}

    @classmethod
    def from_dict(cls, data: dict) -> RemoveGroupRequest:
        """Deserialize from dict using JSON field names."""
        return cls(group_id=data.get("groupId", 0))


# ===========================================================================
# Helper models (from helper.go)
# ===========================================================================


@dataclass
class AllowedCPCodesGroup:
    """Describes a group with allowed CP codes."""
    group_id: int = 0
    role_id: int = 0
    group_name: str = ""
    is_blocked: bool = False
    parent_group_id: int = 0
    role_description: str = ""
    role_name: str = ""
    sub_groups: list[AllowedCPCodesGroup] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "groupId": self.group_id,
            "roleId": self.role_id,
            "groupName": self.group_name,
            "isBlocked": self.is_blocked,
            "parentGroupId": self.parent_group_id,
            "roleDescription": self.role_description,
            "roleName": self.role_name,
            "subGroups": [s.to_dict() for s in self.sub_groups],
        }

    @classmethod
    def from_dict(cls, data: dict) -> AllowedCPCodesGroup:
        """Deserialize from dict using JSON field names."""
        return cls(
            group_id=data.get("groupId", 0),
            role_id=data.get("roleId", 0),
            group_name=data.get("groupName", ""),
            is_blocked=data.get("isBlocked", False),
            parent_group_id=data.get("parentGroupId", 0),
            role_description=data.get("roleDescription", ""),
            role_name=data.get("roleName", ""),
            sub_groups=[AllowedCPCodesGroup.from_dict(s) for s in data.get("subGroups") or []],
        )


@dataclass
class ListAllowedCPCodesRequestBody:
    """Request body for listing allowed CP codes."""
    client_type: str = ""
    groups: list[ClientGroupRequestItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "clientType": self.client_type,
            "groups": [g.to_dict() for g in self.groups],
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListAllowedCPCodesRequestBody:
        """Deserialize from dict using JSON field names."""
        return cls(
            client_type=data.get("clientType", ""),
            groups=[ClientGroupRequestItem.from_dict(g) for g in data.get("groups") or []],
        )


@dataclass
class ListAllowedCPCodesRequest:
    """Request for the ListAllowedCPCodes endpoint."""
    user_name: str = ""
    body: ListAllowedCPCodesRequestBody | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {"userName": self.user_name}
        if self.body is not None:
            result["body"] = self.body.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> ListAllowedCPCodesRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            user_name=data.get("userName", ""),
            body=ListAllowedCPCodesRequestBody.from_dict(data["body"])
            if data.get("body") else None,
        )


@dataclass
class ListAllowedAPIsRequest:
    """Request parameters for the ListAllowedAPIs endpoint."""
    user_name: str = ""
    client_type: str = ""
    allow_account_switch: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "userName": self.user_name,
            "clientType": self.client_type,
            "allowAccountSwitch": self.allow_account_switch,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListAllowedAPIsRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            user_name=data.get("userName", ""),
            client_type=data.get("clientType", ""),
            allow_account_switch=data.get("allowAccountSwitch", False),
        )


@dataclass
class ListAccessibleGroupsRequest:
    """Request parameters for the ListAccessibleGroups endpoint."""
    user_name: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"userName": self.user_name}

    @classmethod
    def from_dict(cls, data: dict) -> ListAccessibleGroupsRequest:
        """Deserialize from dict using JSON field names."""
        return cls(user_name=data.get("userName", ""))


@dataclass
class ListAllowedCPCodesResponseItem:
    """Describes an allowed CP code."""
    name: str = ""
    value: int = 0

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "name": self.name,
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListAllowedCPCodesResponseItem:
        """Deserialize from dict using JSON field names."""
        return cls(
            name=data.get("name", ""),
            value=data.get("value", 0),
        )


@dataclass
class AuthorizedUser:
    """Describes an authorized user."""
    first_name: str = ""
    last_name: str = ""
    username: str = ""
    email: str = ""
    ui_identity_id: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "firstName": self.first_name,
            "lastName": self.last_name,
            "username": self.username,
            "email": self.email,
            "uiIdentityId": self.ui_identity_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> AuthorizedUser:
        """Deserialize from dict using JSON field names."""
        return cls(
            first_name=data.get("firstName", ""),
            last_name=data.get("lastName", ""),
            username=data.get("username", ""),
            email=data.get("email", ""),
            ui_identity_id=data.get("uiIdentityId", ""),
        )


@dataclass
class AccessibleSubGroup:
    """Describes an accessible sub-group."""
    group_id: int = 0
    group_name: str = ""
    parent_group_id: int = 0
    sub_groups: list[AccessibleSubGroup] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "groupId": self.group_id,
            "groupName": self.group_name,
            "parentGroupId": self.parent_group_id,
            "subGroups": [s.to_dict() for s in self.sub_groups],
        }

    @classmethod
    def from_dict(cls, data: dict) -> AccessibleSubGroup:
        """Deserialize from dict using JSON field names."""
        return cls(
            group_id=data.get("groupId", 0),
            group_name=data.get("groupName", ""),
            parent_group_id=data.get("parentGroupId", 0),
            sub_groups=[AccessibleSubGroup.from_dict(s) for s in data.get("subGroups") or []],
        )


@dataclass
class AccessibleGroup:
    """Describes an accessible group."""
    group_id: int = 0
    role_id: int = 0
    group_name: str = ""
    role_name: str = ""
    is_blocked: bool = False
    role_description: str = ""
    sub_groups: list[AccessibleSubGroup] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "groupId": self.group_id,
            "roleId": self.role_id,
            "groupName": self.group_name,
            "roleName": self.role_name,
            "isBlocked": self.is_blocked,
            "roleDescription": self.role_description,
            "subGroups": [s.to_dict() for s in self.sub_groups],
        }

    @classmethod
    def from_dict(cls, data: dict) -> AccessibleGroup:
        """Deserialize from dict using JSON field names."""
        return cls(
            group_id=data.get("groupId", 0),
            role_id=data.get("roleId", 0),
            group_name=data.get("groupName", ""),
            role_name=data.get("roleName", ""),
            is_blocked=data.get("isBlocked", False),
            role_description=data.get("roleDescription", ""),
            sub_groups=[AccessibleSubGroup.from_dict(s) for s in data.get("subGroups") or []],
        )


@dataclass
class AllowedAPI:
    """Describes an allowed API."""
    access_levels: list[str] = field(default_factory=list)
    api_id: int = 0
    api_name: str = ""
    description: str = ""
    documentation_url: str = ""
    endpoint: str = ""
    has_access: bool = False
    service_provider_id: int = 0

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "accessLevels": list(self.access_levels),
            "apiId": self.api_id,
            "apiName": self.api_name,
            "description": self.description,
            "documentationUrl": self.documentation_url,
            "endPoint": self.endpoint,
            "hasAccess": self.has_access,
            "serviceProviderId": self.service_provider_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> AllowedAPI:
        """Deserialize from dict using JSON field names."""
        return cls(
            access_levels=list(data.get("accessLevels") or []),
            api_id=data.get("apiId", 0),
            api_name=data.get("apiName", ""),
            description=data.get("description", ""),
            documentation_url=data.get("documentationUrl", ""),
            endpoint=data.get("endPoint", ""),
            has_access=data.get("hasAccess", False),
            service_provider_id=data.get("serviceProviderId", 0),
        )


# ===========================================================================
# IP Allowlist models (from ip_allowlist.go)
# ===========================================================================


@dataclass
class GetIPAllowlistStatusResponse:
    """Response for the GetIPAllowlistStatus endpoint."""
    enabled: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"enabled": self.enabled}

    @classmethod
    def from_dict(cls, data: dict) -> GetIPAllowlistStatusResponse:
        """Deserialize from dict using JSON field names."""
        return cls(enabled=data.get("enabled", False))


# ===========================================================================
# Property models (from properties.go)
# ===========================================================================


@dataclass
class PropertyActions:
    """Actions available for a property."""
    move: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"move": self.move}

    @classmethod
    def from_dict(cls, data: dict) -> PropertyActions:
        """Deserialize from dict using JSON field names."""
        return cls(move=data.get("move", False))


@dataclass
class Property:
    """Describes a property."""
    property_id: int = 0
    property_name: str = ""
    property_type_description: str = ""
    group_id: int = 0
    group_name: str = ""
    actions: PropertyActions | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "propertyId": self.property_id,
            "propertyName": self.property_name,
            "propertyTypeDescription": self.property_type_description,
            "groupId": self.group_id,
            "groupName": self.group_name,
        }
        if self.actions is not None:
            result["actions"] = self.actions.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> Property:
        """Deserialize from dict using JSON field names."""
        return cls(
            property_id=data.get("propertyId", 0),
            property_name=data.get("propertyName", ""),
            property_type_description=data.get("propertyTypeDescription", ""),
            group_id=data.get("groupId", 0),
            group_name=data.get("groupName", ""),
            actions=PropertyActions.from_dict(data["actions"])
            if data.get("actions") else None,
        )


@dataclass
class ListPropertiesRequest:
    """Request parameters for the ListProperties endpoint."""
    group_id: int = 0
    actions: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "groupId": self.group_id,
            "actions": self.actions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListPropertiesRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            group_id=data.get("groupId", 0),
            actions=data.get("actions", False),
        )


@dataclass
class ListUsersForPropertyRequest:
    """Request parameters for the ListUsersForProperty endpoint."""
    property_id: int = 0
    user_type: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "propertyId": self.property_id,
            "userType": self.user_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListUsersForPropertyRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            property_id=data.get("propertyId", 0),
            user_type=data.get("userType", ""),
        )


@dataclass
class GetPropertyRequest:
    """Request parameters for the GetProperty endpoint."""
    property_id: int = 0
    group_id: int = 0

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "propertyId": self.property_id,
            "groupId": self.group_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GetPropertyRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            property_id=data.get("propertyId", 0),
            group_id=data.get("groupId", 0),
        )


@dataclass
class GetPropertyResponse:
    """Response for the GetProperty endpoint."""
    arl_config_file: str = ""
    created_by: str = ""
    created_date: str = ""
    group_id: int = 0
    group_name: str = ""
    modified_by: str = ""
    modified_date: str = ""
    property_id: int = 0
    property_name: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "arlConfigFile": self.arl_config_file,
            "createdBy": self.created_by,
            "createdDate": self.created_date,
            "groupId": self.group_id,
            "groupName": self.group_name,
            "modifiedBy": self.modified_by,
            "modifiedDate": self.modified_date,
            "propertyId": self.property_id,
            "propertyName": self.property_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GetPropertyResponse:
        """Deserialize from dict using JSON field names."""
        return cls(
            arl_config_file=data.get("arlConfigFile", ""),
            created_by=data.get("createdBy", ""),
            created_date=data.get("createdDate", ""),
            group_id=data.get("groupId", 0),
            group_name=data.get("groupName", ""),
            modified_by=data.get("modifiedBy", ""),
            modified_date=data.get("modifiedDate", ""),
            property_id=data.get("propertyId", 0),
            property_name=data.get("propertyName", ""),
        )


@dataclass
class MovePropertyRequestBody:
    """Request body for moving a property."""
    destination_group_id: int = 0
    source_group_id: int = 0

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "destinationGroupId": self.destination_group_id,
            "sourceGroupId": self.source_group_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> MovePropertyRequestBody:
        """Deserialize from dict using JSON field names."""
        return cls(
            destination_group_id=data.get("destinationGroupId", 0),
            source_group_id=data.get("sourceGroupId", 0),
        )


@dataclass
class MovePropertyRequest:
    """Request for the MoveProperty endpoint."""
    property_id: int = 0
    body: MovePropertyRequestBody | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {"propertyId": self.property_id}
        if self.body is not None:
            result["body"] = self.body.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> MovePropertyRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            property_id=data.get("propertyId", 0),
            body=MovePropertyRequestBody.from_dict(data["body"])
            if data.get("body") else None,
        )


@dataclass
class BlockUserItem:
    """Describes a user to block on a property."""
    ui_identity_id: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"uiIdentityId": self.ui_identity_id}

    @classmethod
    def from_dict(cls, data: dict) -> BlockUserItem:
        """Deserialize from dict using JSON field names."""
        return cls(ui_identity_id=data.get("uiIdentityId", ""))


@dataclass
class BlockUsersRequest:
    """Request for the BlockUsers endpoint."""
    property_id: int = 0
    body: list[BlockUserItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "propertyId": self.property_id,
            "body": [b.to_dict() for b in self.body],
        }

    @classmethod
    def from_dict(cls, data: dict) -> BlockUsersRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            property_id=data.get("propertyId", 0),
            body=[BlockUserItem.from_dict(b) for b in data.get("body") or []],
        )


@dataclass
class UsersForProperty:
    """Describes a user associated with a property."""
    first_name: str = ""
    is_blocked: bool = False
    last_name: str = ""
    ui_identity_id: str = ""
    ui_user_name: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "firstName": self.first_name,
            "isBlocked": self.is_blocked,
            "lastName": self.last_name,
            "uiIdentityId": self.ui_identity_id,
            "uiUserName": self.ui_user_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> UsersForProperty:
        """Deserialize from dict using JSON field names."""
        return cls(
            first_name=data.get("firstName", ""),
            is_blocked=data.get("isBlocked", False),
            last_name=data.get("lastName", ""),
            ui_identity_id=data.get("uiIdentityId", ""),
            ui_user_name=data.get("uiUserName", ""),
        )


@dataclass
class MapPropertyIDToNameRequest:
    """Request parameters for the MapPropertyIDToName endpoint."""
    property_id: int = 0
    group_id: int = 0

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "propertyId": self.property_id,
            "groupId": self.group_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> MapPropertyIDToNameRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            property_id=data.get("propertyId", 0),
            group_id=data.get("groupId", 0),
        )


# ===========================================================================
# Role models (from roles.go)
# ===========================================================================


@dataclass
class GrantedRoleID:
    """Identifies a role to grant."""
    id: int = 0

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"grantedRoleId": self.id}

    @classmethod
    def from_dict(cls, data: dict) -> GrantedRoleID:
        """Deserialize from dict using JSON field names."""
        return cls(id=data.get("grantedRoleId", 0))


@dataclass
class RoleRequest:
    """Request body for creating or updating a role."""
    name: str = ""
    description: str = ""
    granted_roles: list[GrantedRoleID] | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "roleName": self.name,
            "roleDescription": self.description,
        }
        if self.granted_roles is not None:
            result["grantedRoles"] = [r.to_dict() for r in self.granted_roles]
        return result

    @classmethod
    def from_dict(cls, data: dict) -> RoleRequest:
        """Deserialize from dict using JSON field names."""
        raw_roles = data.get("grantedRoles")
        return cls(
            name=data.get("roleName", ""),
            description=data.get("roleDescription", ""),
            granted_roles=[GrantedRoleID.from_dict(r) for r in raw_roles]
            if raw_roles is not None else None,
        )


@dataclass
class GetRoleRequest:
    """Request parameters for the GetRole endpoint."""
    id: int = 0
    actions: bool = False
    granted_roles: bool = False
    users: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "id": self.id,
            "actions": self.actions,
            "grantedRoles": self.granted_roles,
            "users": self.users,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GetRoleRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            id=data.get("id", 0),
            actions=data.get("actions", False),
            granted_roles=data.get("grantedRoles", False),
            users=data.get("users", False),
        )


@dataclass
class UpdateRoleRequest:
    """Request for the UpdateRole endpoint."""
    id: int = 0
    name: str = ""
    description: str = ""
    granted_roles: list[GrantedRoleID] | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "roleName": self.name,
            "roleDescription": self.description,
        }
        if self.granted_roles is not None:
            result["grantedRoles"] = [r.to_dict() for r in self.granted_roles]
        return result

    @classmethod
    def from_dict(cls, data: dict) -> UpdateRoleRequest:
        """Deserialize from dict using JSON field names."""
        raw_roles = data.get("grantedRoles")
        return cls(
            id=data.get("id", 0),
            name=data.get("roleName", ""),
            description=data.get("roleDescription", ""),
            granted_roles=[GrantedRoleID.from_dict(r) for r in raw_roles]
            if raw_roles is not None else None,
        )


@dataclass
class DeleteRoleRequest:
    """Request parameters for the DeleteRole endpoint."""
    id: int = 0

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"id": self.id}

    @classmethod
    def from_dict(cls, data: dict) -> DeleteRoleRequest:
        """Deserialize from dict using JSON field names."""
        return cls(id=data.get("id", 0))


@dataclass
class ListRolesRequest:
    """Request parameters for the ListRoles endpoint."""
    group_id: int | None = None
    actions: bool = False
    ignore_context: bool = False
    users: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "actions": self.actions,
            "ignoreContext": self.ignore_context,
            "users": self.users,
        }
        if self.group_id is not None:
            result["groupId"] = self.group_id
        return result

    @classmethod
    def from_dict(cls, data: dict) -> ListRolesRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            group_id=data.get("groupId"),
            actions=data.get("actions", False),
            ignore_context=data.get("ignoreContext", False),
            users=data.get("users", False),
        )


@dataclass
class RoleAction:
    """Actions available for a role."""
    delete: bool = False
    edit: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "delete": self.delete,
            "edit": self.edit,
        }

    @classmethod
    def from_dict(cls, data: dict) -> RoleAction:
        """Deserialize from dict using JSON field names."""
        return cls(
            delete=data.get("delete", False),
            edit=data.get("edit", False),
        )


@dataclass
class RoleGrantedRole:
    """Describes a granted role within a role."""
    description: str = ""
    role_id: int = 0
    role_name: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "grantedRoleDescription": self.description,
            "grantedRoleId": self.role_id,
            "grantedRoleName": self.role_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> RoleGrantedRole:
        """Deserialize from dict using JSON field names."""
        return cls(
            description=data.get("grantedRoleDescription", ""),
            role_id=data.get("grantedRoleId", 0),
            role_name=data.get("grantedRoleName", ""),
        )


@dataclass
class RoleUser:
    """Describes a user assigned to a role."""
    account_id: str = ""
    email: str = ""
    first_name: str = ""
    last_login_date: str = ""
    last_name: str = ""
    ui_identity_id: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "accountId": self.account_id,
            "email": self.email,
            "firstName": self.first_name,
            "lastLoginDate": self.last_login_date,
            "lastName": self.last_name,
            "uiIdentityId": self.ui_identity_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> RoleUser:
        """Deserialize from dict using JSON field names."""
        return cls(
            account_id=data.get("accountId", ""),
            email=data.get("email", ""),
            first_name=data.get("firstName", ""),
            last_login_date=data.get("lastLoginDate", ""),
            last_name=data.get("lastName", ""),
            ui_identity_id=data.get("uiIdentityId", ""),
        )


@dataclass
class Role:
    """Describes a role."""
    actions: RoleAction | None = None
    created_by: str = ""
    created_date: str = ""
    granted_roles: list[RoleGrantedRole] | None = None
    modified_by: str = ""
    modified_date: str = ""
    role_description: str = ""
    role_id: int = 0
    role_name: str = ""
    users: list[RoleUser] | None = None
    type: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "createdBy": self.created_by,
            "createdDate": self.created_date,
            "modifiedBy": self.modified_by,
            "modifiedDate": self.modified_date,
            "roleDescription": self.role_description,
            "roleId": self.role_id,
            "roleName": self.role_name,
            "type": self.type,
        }
        if self.actions is not None:
            result["actions"] = self.actions.to_dict()
        if self.granted_roles is not None:
            result["grantedRoles"] = [r.to_dict() for r in self.granted_roles]
        if self.users is not None:
            result["users"] = [u.to_dict() for u in self.users]
        return result

    @classmethod
    def from_dict(cls, data: dict) -> Role:
        """Deserialize from dict using JSON field names."""
        raw_granted = data.get("grantedRoles")
        raw_users = data.get("users")
        return cls(
            actions=RoleAction.from_dict(data["actions"]) if data.get("actions") else None,
            created_by=data.get("createdBy", ""),
            created_date=data.get("createdDate", ""),
            granted_roles=[RoleGrantedRole.from_dict(r) for r in raw_granted]
            if raw_granted is not None else None,
            modified_by=data.get("modifiedBy", ""),
            modified_date=data.get("modifiedDate", ""),
            role_description=data.get("roleDescription", ""),
            role_id=data.get("roleId", 0),
            role_name=data.get("roleName", ""),
            users=[RoleUser.from_dict(u) for u in raw_users]
            if raw_users is not None else None,
            type=data.get("type", ""),
        )


# ===========================================================================
# Support models (from support.go)
# ===========================================================================


@dataclass
class GetPasswordPolicyResponse:
    """Response for the GetPasswordPolicy endpoint."""
    case_dif: int = 0
    max_repeating: int = 0
    min_digits: int = 0
    min_length: int = 0
    min_letters: int = 0
    min_non_alpha: int = 0
    min_reuse: int = 0
    pw_class: str = ""
    rotate_frequency: int = 0

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "caseDif": self.case_dif,
            "maxRepeating": self.max_repeating,
            "minDigits": self.min_digits,
            "minLength": self.min_length,
            "minLetters": self.min_letters,
            "minNonAlpha": self.min_non_alpha,
            "minReuse": self.min_reuse,
            "pwclass": self.pw_class,
            "rotateFrequency": self.rotate_frequency,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GetPasswordPolicyResponse:
        """Deserialize from dict using JSON field names."""
        return cls(
            case_dif=data.get("caseDif", 0),
            max_repeating=data.get("maxRepeating", 0),
            min_digits=data.get("minDigits", 0),
            min_length=data.get("minLength", 0),
            min_letters=data.get("minLetters", 0),
            min_non_alpha=data.get("minNonAlpha", 0),
            min_reuse=data.get("minReuse", 0),
            pw_class=data.get("pwclass", ""),
            rotate_frequency=data.get("rotateFrequency", 0),
        )


@dataclass
class TimeoutPolicy:
    """Describes a session timeout policy."""
    name: str = ""
    value: int = 0

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "name": self.name,
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TimeoutPolicy:
        """Deserialize from dict using JSON field names."""
        return cls(
            name=data.get("name", ""),
            value=data.get("value", 0),
        )


@dataclass
class ListStatesRequest:
    """Request parameters for the ListStates endpoint."""
    country: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"country": self.country}

    @classmethod
    def from_dict(cls, data: dict) -> ListStatesRequest:
        """Deserialize from dict using JSON field names."""
        return cls(country=data.get("country", ""))


@dataclass
class ListAccountSwitchKeysRequest:
    """Request parameters for the ListAccountSwitchKeys endpoint."""
    client_id: str = ""
    search: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "clientId": self.client_id,
            "search": self.search,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListAccountSwitchKeysRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            client_id=data.get("clientId", ""),
            search=data.get("search", ""),
        )


@dataclass
class AccountSwitchKey:
    """Describes an account switch key."""
    account_name: str = ""
    account_switch_key: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "accountName": self.account_name,
            "accountSwitchKey": self.account_switch_key,
        }

    @classmethod
    def from_dict(cls, data: dict) -> AccountSwitchKey:
        """Deserialize from dict using JSON field names."""
        return cls(
            account_name=data.get("accountName", ""),
            account_switch_key=data.get("accountSwitchKey", ""),
        )


@dataclass
class Timezone:
    """Describes a timezone."""
    description: str = ""
    offset: str = ""
    posix: str = ""
    timezone: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "description": self.description,
            "offset": self.offset,
            "posix": self.posix,
            "timezone": self.timezone,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Timezone:
        """Deserialize from dict using JSON field names."""
        return cls(
            description=data.get("description", ""),
            offset=data.get("offset", ""),
            posix=data.get("posix", ""),
            timezone=data.get("timezone", ""),
        )


# ===========================================================================
# User models (from user.go)
# ===========================================================================


@dataclass
class UserNotificationOptions:
    """Notification options for a user."""
    new_user: bool = False
    password_expiry: bool = False
    proactive: list[str] = field(default_factory=list)
    upgrade: list[str] = field(default_factory=list)
    api_client_credential_expiry: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "newUserNotification": self.new_user,
            "passwordExpiry": self.password_expiry,
            "proactive": list(self.proactive),
            "upgrade": list(self.upgrade),
            "apiClientCredentialExpiryNotification": self.api_client_credential_expiry,
        }

    @classmethod
    def from_dict(cls, data: dict) -> UserNotificationOptions:
        """Deserialize from dict using JSON field names."""
        return cls(
            new_user=data.get("newUserNotification", False),
            password_expiry=data.get("passwordExpiry", False),
            proactive=list(data.get("proactive") or []),
            upgrade=list(data.get("upgrade") or []),
            api_client_credential_expiry=data.get("apiClientCredentialExpiryNotification", False),
        )


@dataclass
class UserNotifications:
    """Notification settings for a user."""
    enable_email: bool = False
    options: UserNotificationOptions | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "enableEmailNotifications": self.enable_email,
        }
        if self.options is not None:
            result["options"] = self.options.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> UserNotifications:
        """Deserialize from dict using JSON field names."""
        return cls(
            enable_email=data.get("enableEmailNotifications", False),
            options=UserNotificationOptions.from_dict(data["options"])
            if data.get("options") else None,
        )


@dataclass
class UserActions:
    """Actions available for a user."""
    api_client: bool = False
    delete: bool = False
    edit: bool = False
    is_cloneable: bool = False
    reset_password: bool = False
    third_party_access: bool = False
    can_edit_tfa: bool = False
    can_edit_mfa: bool = False
    can_edit_none: bool = False
    edit_profile: bool = False
    edit_role: bool = False
    can_generate_bypass_code: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "apiClient": self.api_client,
            "delete": self.delete,
            "edit": self.edit,
            "isCloneable": self.is_cloneable,
            "resetPassword": self.reset_password,
            "thirdPartyAccess": self.third_party_access,
            "canEditTFA": self.can_edit_tfa,
            "canEditMFA": self.can_edit_mfa,
            "canEditNone": self.can_edit_none,
            "editProfile": self.edit_profile,
            "editRole": self.edit_role,
            "canGenerateBypassCode": self.can_generate_bypass_code,
        }

    @classmethod
    def from_dict(cls, data: dict) -> UserActions:
        """Deserialize from dict using JSON field names."""
        return cls(
            api_client=data.get("apiClient", False),
            delete=data.get("delete", False),
            edit=data.get("edit", False),
            is_cloneable=data.get("isCloneable", False),
            reset_password=data.get("resetPassword", False),
            third_party_access=data.get("thirdPartyAccess", False),
            can_edit_tfa=data.get("canEditTFA", False),
            can_edit_mfa=data.get("canEditMFA", False),
            can_edit_none=data.get("canEditNone", False),
            edit_profile=data.get("editProfile", False),
            edit_role=data.get("editRole", False),
            can_generate_bypass_code=data.get("canGenerateBypassCode", False),
        )


@dataclass
class AuthGrant:
    """Describes an authorization grant for a user."""
    group_id: int = 0
    group_name: str = ""
    is_blocked: bool = False
    role_description: str = ""
    role_id: int | None = None
    role_name: str = ""
    subgroups: list[AuthGrant] | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "groupId": self.group_id,
            "groupName": self.group_name,
            "isBlocked": self.is_blocked,
            "roleDescription": self.role_description,
            "roleName": self.role_name,
        }
        if self.role_id is not None:
            result["roleId"] = self.role_id
        if self.subgroups is not None:
            result["subGroups"] = [s.to_dict() for s in self.subgroups]
        return result

    @classmethod
    def from_dict(cls, data: dict) -> AuthGrant:
        """Deserialize from dict using JSON field names."""
        raw_sub = data.get("subGroups")
        return cls(
            group_id=data.get("groupId", 0),
            group_name=data.get("groupName", ""),
            is_blocked=data.get("isBlocked", False),
            role_description=data.get("roleDescription", ""),
            role_id=data.get("roleId"),
            role_name=data.get("roleName", ""),
            subgroups=[AuthGrant.from_dict(s) for s in raw_sub]
            if raw_sub is not None else None,
        )


@dataclass
class AuthGrantRequest:
    """Authorization grant for create/update user requests."""
    group_id: int = 0
    is_blocked: bool = False
    role_id: int | None = None
    subgroups: list[AuthGrantRequest] | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "groupId": self.group_id,
            "isBlocked": self.is_blocked,
        }
        if self.role_id is not None:
            result["roleId"] = self.role_id
        if self.subgroups is not None:
            result["subGroups"] = [s.to_dict() for s in self.subgroups]
        return result

    @classmethod
    def from_dict(cls, data: dict) -> AuthGrantRequest:
        """Deserialize from dict using JSON field names."""
        raw_sub = data.get("subGroups")
        return cls(
            group_id=data.get("groupId", 0),
            is_blocked=data.get("isBlocked", False),
            role_id=data.get("roleId"),
            subgroups=[AuthGrantRequest.from_dict(s) for s in raw_sub]
            if raw_sub is not None else None,
        )


@dataclass
class UserBasicInfo:
    """Basic user profile information."""
    first_name: str = ""
    last_name: str = ""
    user_name: str = ""
    email: str = ""
    phone: str = ""
    time_zone: str = ""
    job_title: str = ""
    tfa_enabled: bool = False
    secondary_email: str = ""
    mobile_phone: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    country: str = ""
    contact_type: str = ""
    preferred_language: str = ""
    session_time_out: int | None = None
    additional_authentication: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "firstName": self.first_name,
            "lastName": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "timeZone": self.time_zone,
            "jobTitle": self.job_title,
            "tfaEnabled": self.tfa_enabled,
            "secondaryEmail": self.secondary_email,
            "mobilePhone": self.mobile_phone,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zipCode": self.zip_code,
            "country": self.country,
            "contactType": self.contact_type,
            "preferredLanguage": self.preferred_language,
            "additionalAuthentication": self.additional_authentication,
        }
        if self.user_name:
            result["uiUserName"] = self.user_name
        if self.session_time_out is not None:
            result["sessionTimeOut"] = self.session_time_out
        return result

    @classmethod
    def from_dict(cls, data: dict) -> UserBasicInfo:
        """Deserialize from dict using JSON field names."""
        return cls(
            first_name=data.get("firstName", ""),
            last_name=data.get("lastName", ""),
            user_name=data.get("uiUserName", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            time_zone=data.get("timeZone", ""),
            job_title=data.get("jobTitle", ""),
            tfa_enabled=data.get("tfaEnabled", False),
            secondary_email=data.get("secondaryEmail", ""),
            mobile_phone=data.get("mobilePhone", ""),
            address=data.get("address", ""),
            city=data.get("city", ""),
            state=data.get("state", ""),
            zip_code=data.get("zipCode", ""),
            country=data.get("country", ""),
            contact_type=data.get("contactType", ""),
            preferred_language=data.get("preferredLanguage", ""),
            session_time_out=data.get("sessionTimeOut"),
            additional_authentication=data.get("additionalAuthentication", ""),
        )


@dataclass
class CreateUserRequest:
    """Request body for creating a user."""
    first_name: str = ""
    last_name: str = ""
    user_name: str = ""
    email: str = ""
    phone: str = ""
    time_zone: str = ""
    job_title: str = ""
    tfa_enabled: bool = False
    secondary_email: str = ""
    mobile_phone: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    country: str = ""
    contact_type: str = ""
    preferred_language: str = ""
    session_time_out: int | None = None
    additional_authentication: str = ""
    auth_grants: list[AuthGrantRequest] | None = None
    notifications: UserNotifications | None = None
    send_email: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names.

        Note: send_email is a query parameter (json:"-") and is excluded
        from the serialized body.
        """
        result: dict = {
            "firstName": self.first_name,
            "lastName": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "timeZone": self.time_zone,
            "jobTitle": self.job_title,
            "tfaEnabled": self.tfa_enabled,
            "secondaryEmail": self.secondary_email,
            "mobilePhone": self.mobile_phone,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zipCode": self.zip_code,
            "country": self.country,
            "contactType": self.contact_type,
            "preferredLanguage": self.preferred_language,
            "additionalAuthentication": self.additional_authentication,
        }
        if self.user_name:
            result["uiUserName"] = self.user_name
        if self.session_time_out is not None:
            result["sessionTimeOut"] = self.session_time_out
        if self.auth_grants is not None:
            result["authGrants"] = [g.to_dict() for g in self.auth_grants]
        if self.notifications is not None:
            result["notifications"] = self.notifications.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> CreateUserRequest:
        """Deserialize from dict using JSON field names."""
        raw_grants = data.get("authGrants")
        return cls(
            first_name=data.get("firstName", ""),
            last_name=data.get("lastName", ""),
            user_name=data.get("uiUserName", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            time_zone=data.get("timeZone", ""),
            job_title=data.get("jobTitle", ""),
            tfa_enabled=data.get("tfaEnabled", False),
            secondary_email=data.get("secondaryEmail", ""),
            mobile_phone=data.get("mobilePhone", ""),
            address=data.get("address", ""),
            city=data.get("city", ""),
            state=data.get("state", ""),
            zip_code=data.get("zipCode", ""),
            country=data.get("country", ""),
            contact_type=data.get("contactType", ""),
            preferred_language=data.get("preferredLanguage", ""),
            session_time_out=data.get("sessionTimeOut"),
            additional_authentication=data.get("additionalAuthentication", ""),
            auth_grants=[AuthGrantRequest.from_dict(g) for g in raw_grants]
            if raw_grants is not None else None,
            notifications=UserNotifications.from_dict(data["notifications"])
            if data.get("notifications") else None,
            send_email=data.get("sendEmail", False),
        )


@dataclass
class ListUsersRequest:
    """Request parameters for the ListUsers endpoint."""
    group_id: int | None = None
    auth_grants: bool = False
    actions: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "authGrants": self.auth_grants,
            "actions": self.actions,
        }
        if self.group_id is not None:
            result["groupId"] = self.group_id
        return result

    @classmethod
    def from_dict(cls, data: dict) -> ListUsersRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            group_id=data.get("groupId"),
            auth_grants=data.get("authGrants", False),
            actions=data.get("actions", False),
        )


@dataclass
class GetUserRequest:
    """Request parameters for the GetUser endpoint."""
    identity_id: str = ""
    actions: bool = False
    auth_grants: bool = False
    notifications: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "identityId": self.identity_id,
            "actions": self.actions,
            "authGrants": self.auth_grants,
            "notifications": self.notifications,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GetUserRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            identity_id=data.get("identityId", ""),
            actions=data.get("actions", False),
            auth_grants=data.get("authGrants", False),
            notifications=data.get("notifications", False),
        )


@dataclass
class UpdateUserInfoRequest:
    """Request for the UpdateUserInfo endpoint."""
    identity_id: str = ""
    user: UserBasicInfo | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {"identityId": self.identity_id}
        if self.user is not None:
            result["user"] = self.user.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> UpdateUserInfoRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            identity_id=data.get("identityId", ""),
            user=UserBasicInfo.from_dict(data["user"]) if data.get("user") else None,
        )


@dataclass
class UpdateUserNotificationsRequest:
    """Request for the UpdateUserNotifications endpoint."""
    identity_id: str = ""
    notifications: UserNotifications | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {"identityId": self.identity_id}
        if self.notifications is not None:
            result["notifications"] = self.notifications.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> UpdateUserNotificationsRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            identity_id=data.get("identityId", ""),
            notifications=UserNotifications.from_dict(data["notifications"])
            if data.get("notifications") else None,
        )


@dataclass
class UpdateUserAuthGrantsRequest:
    """Request for the UpdateUserAuthGrants endpoint."""
    identity_id: str = ""
    auth_grants: list[AuthGrantRequest] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "identityId": self.identity_id,
            "authGrants": [g.to_dict() for g in self.auth_grants],
        }

    @classmethod
    def from_dict(cls, data: dict) -> UpdateUserAuthGrantsRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            identity_id=data.get("identityId", ""),
            auth_grants=[AuthGrantRequest.from_dict(g)
                         for g in data.get("authGrants") or []],
        )


@dataclass
class RemoveUserRequest:
    """Request parameters for the RemoveUser endpoint."""
    identity_id: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"identityId": self.identity_id}

    @classmethod
    def from_dict(cls, data: dict) -> RemoveUserRequest:
        """Deserialize from dict using JSON field names."""
        return cls(identity_id=data.get("identityId", ""))


@dataclass
class User:
    """Describes a user."""
    first_name: str = ""
    last_name: str = ""
    user_name: str = ""
    email: str = ""
    phone: str = ""
    time_zone: str = ""
    job_title: str = ""
    tfa_enabled: bool = False
    secondary_email: str = ""
    mobile_phone: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    country: str = ""
    contact_type: str = ""
    preferred_language: str = ""
    session_time_out: int | None = None
    additional_authentication: str = ""
    identity_id: str = ""
    is_locked: bool = False
    last_login_date: str = ""
    password_expiry_date: str = ""
    tfa_configured: bool = False
    email_update_pending: bool = False
    auth_grants: list[AuthGrant] | None = None
    notifications: UserNotifications | None = None
    actions: UserActions | None = None
    user_status: str = ""
    account_id: str = ""
    additional_authentication_configured: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "firstName": self.first_name,
            "lastName": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "timeZone": self.time_zone,
            "jobTitle": self.job_title,
            "tfaEnabled": self.tfa_enabled,
            "secondaryEmail": self.secondary_email,
            "mobilePhone": self.mobile_phone,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zipCode": self.zip_code,
            "country": self.country,
            "contactType": self.contact_type,
            "preferredLanguage": self.preferred_language,
            "additionalAuthentication": self.additional_authentication,
            "uiIdentityId": self.identity_id,
            "isLocked": self.is_locked,
            "lastLoginDate": self.last_login_date,
            "passwordExpiryDate": self.password_expiry_date,
            "tfaConfigured": self.tfa_configured,
            "emailUpdatePending": self.email_update_pending,
            "userStatus": self.user_status,
            "accountId": self.account_id,
            "additionalAuthenticationConfigured": self.additional_authentication_configured,
        }
        if self.user_name:
            result["uiUserName"] = self.user_name
        if self.session_time_out is not None:
            result["sessionTimeOut"] = self.session_time_out
        if self.auth_grants is not None:
            result["authGrants"] = [g.to_dict() for g in self.auth_grants]
        if self.notifications is not None:
            result["notifications"] = self.notifications.to_dict()
        if self.actions is not None:
            result["actions"] = self.actions.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict) -> User:
        """Deserialize from dict using JSON field names."""
        raw_grants = data.get("authGrants")
        return cls(
            first_name=data.get("firstName", ""),
            last_name=data.get("lastName", ""),
            user_name=data.get("uiUserName", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            time_zone=data.get("timeZone", ""),
            job_title=data.get("jobTitle", ""),
            tfa_enabled=data.get("tfaEnabled", False),
            secondary_email=data.get("secondaryEmail", ""),
            mobile_phone=data.get("mobilePhone", ""),
            address=data.get("address", ""),
            city=data.get("city", ""),
            state=data.get("state", ""),
            zip_code=data.get("zipCode", ""),
            country=data.get("country", ""),
            contact_type=data.get("contactType", ""),
            preferred_language=data.get("preferredLanguage", ""),
            session_time_out=data.get("sessionTimeOut"),
            additional_authentication=data.get("additionalAuthentication", ""),
            identity_id=data.get("uiIdentityId", ""),
            is_locked=data.get("isLocked", False),
            last_login_date=data.get("lastLoginDate", ""),
            password_expiry_date=data.get("passwordExpiryDate", ""),
            tfa_configured=data.get("tfaConfigured", False),
            email_update_pending=data.get("emailUpdatePending", False),
            auth_grants=[AuthGrant.from_dict(g) for g in raw_grants]
            if raw_grants is not None else None,
            notifications=UserNotifications.from_dict(data["notifications"])
            if data.get("notifications") else None,
            actions=UserActions.from_dict(data["actions"])
            if data.get("actions") else None,
            user_status=data.get("userStatus", ""),
            account_id=data.get("accountId", ""),
            additional_authentication_configured=data.get(
                "additionalAuthenticationConfigured", False),
        )


@dataclass
class UserListItem:
    """Describes a user in a list response."""
    first_name: str = ""
    last_name: str = ""
    user_name: str = ""
    email: str = ""
    tfa_enabled: bool = False
    identity_id: str = ""
    is_locked: bool = False
    last_login_date: str = ""
    tfa_configured: bool = False
    account_id: str = ""
    actions: UserActions | None = None
    auth_grants: list[AuthGrant] | None = None
    additional_authentication: str = ""
    additional_authentication_configured: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        result: dict = {
            "firstName": self.first_name,
            "lastName": self.last_name,
            "email": self.email,
            "tfaEnabled": self.tfa_enabled,
            "uiIdentityId": self.identity_id,
            "isLocked": self.is_locked,
            "lastLoginDate": self.last_login_date,
            "tfaConfigured": self.tfa_configured,
            "accountId": self.account_id,
            "additionalAuthentication": self.additional_authentication,
            "additionalAuthenticationConfigured": self.additional_authentication_configured,
        }
        if self.user_name:
            result["uiUserName"] = self.user_name
        if self.actions is not None:
            result["actions"] = self.actions.to_dict()
        if self.auth_grants is not None:
            result["authGrants"] = [g.to_dict() for g in self.auth_grants]
        return result

    @classmethod
    def from_dict(cls, data: dict) -> UserListItem:
        """Deserialize from dict using JSON field names."""
        raw_grants = data.get("authGrants")
        return cls(
            first_name=data.get("firstName", ""),
            last_name=data.get("lastName", ""),
            user_name=data.get("uiUserName", ""),
            email=data.get("email", ""),
            tfa_enabled=data.get("tfaEnabled", False),
            identity_id=data.get("uiIdentityId", ""),
            is_locked=data.get("isLocked", False),
            last_login_date=data.get("lastLoginDate", ""),
            tfa_configured=data.get("tfaConfigured", False),
            account_id=data.get("accountId", ""),
            actions=UserActions.from_dict(data["actions"])
            if data.get("actions") else None,
            auth_grants=[AuthGrant.from_dict(g) for g in raw_grants]
            if raw_grants is not None else None,
            additional_authentication=data.get("additionalAuthentication", ""),
            additional_authentication_configured=data.get(
                "additionalAuthenticationConfigured", False),
        )


@dataclass
class UpdateMFARequest:
    """Request for the UpdateMFA endpoint."""
    identity_id: str = ""
    value: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"value": self.value}

    @classmethod
    def from_dict(cls, data: dict) -> UpdateMFARequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            identity_id=data.get("identityId", ""),
            value=data.get("value", ""),
        )


@dataclass
class ResetMFARequest:
    """Request for the ResetMFA endpoint."""
    identity_id: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"identityId": self.identity_id}

    @classmethod
    def from_dict(cls, data: dict) -> ResetMFARequest:
        """Deserialize from dict using JSON field names."""
        return cls(identity_id=data.get("identityId", ""))


# ===========================================================================
# User Lock models (from user_lock.go)
# ===========================================================================


@dataclass
class LockUserRequest:
    """Request parameters for the LockUser endpoint."""
    identity_id: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"identityId": self.identity_id}

    @classmethod
    def from_dict(cls, data: dict) -> LockUserRequest:
        """Deserialize from dict using JSON field names."""
        return cls(identity_id=data.get("identityId", ""))


@dataclass
class UnlockUserRequest:
    """Request parameters for the UnlockUser endpoint."""
    identity_id: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"identityId": self.identity_id}

    @classmethod
    def from_dict(cls, data: dict) -> UnlockUserRequest:
        """Deserialize from dict using JSON field names."""
        return cls(identity_id=data.get("identityId", ""))


# ===========================================================================
# User Password models (from user_password.go)
# ===========================================================================


@dataclass
class ResetUserPasswordRequest:
    """Request parameters for the ResetUserPassword endpoint."""
    identity_id: str = ""
    send_email: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {
            "identityId": self.identity_id,
            "sendEmail": self.send_email,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ResetUserPasswordRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            identity_id=data.get("identityId", ""),
            send_email=data.get("sendEmail", False),
        )


@dataclass
class ResetUserPasswordResponse:
    """Response for the ResetUserPassword endpoint."""
    new_password: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names."""
        return {"newPassword": self.new_password}

    @classmethod
    def from_dict(cls, data: dict) -> ResetUserPasswordResponse:
        """Deserialize from dict using JSON field names."""
        return cls(new_password=data.get("newPassword", ""))


@dataclass
class SetUserPasswordRequest:
    """Request for the SetUserPassword endpoint."""
    identity_id: str = ""
    new_password: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using JSON field names.

        Note: identity_id is a URL parameter (json:"-") and is excluded
        from the serialized body.
        """
        return {"newPassword": self.new_password}

    @classmethod
    def from_dict(cls, data: dict) -> SetUserPasswordRequest:
        """Deserialize from dict using JSON field names."""
        return cls(
            identity_id=data.get("identityId", ""),
            new_password=data.get("newPassword", ""),
        )


# ===========================================================================
# Type aliases
# ===========================================================================

LockAPIClientResponse = APIClient
UnlockAPIClientResponse = APIClient
ListAPIClientsResponse = list[ListAPIClientsItem]
UpdateAPIClientResponse = GetAPIClientResponse
ListCredentialsResponse = list[Credential]
GetCredentialResponse = Credential
ListCIDRBlocksResponse = list[CIDRBlock]
CreateCIDRBlockResponse = list[CIDRBlock]
GetCIDRBlockResponse = CIDRBlock
UpdateCIDRBlockResponse = CIDRBlock
CreateRoleRequest = RoleRequest
MapPropertyNameToIDRequest = str
ListPropertiesResponse = list[Property]
ListUsersForPropertyResponse = list[UsersForProperty]
BlockUsersResponse = list[UsersForProperty]
BlockUsersRequestBody = list[BlockUserItem]
ListAllowedCPCodesResponse = list[ListAllowedCPCodesResponseItem]
ListAuthorizedUsersResponse = list[AuthorizedUser]
ListAccessibleGroupsResponse = list[AccessibleGroup]
ListAllowedAPIsResponse = list[AllowedAPI]
ListAccountSwitchKeysResponse = list[AccountSwitchKey]
