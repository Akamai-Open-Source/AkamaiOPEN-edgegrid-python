"""Request and response models for the Cloud Access Manager API."""
# pylint: disable=too-many-lines

from __future__ import annotations

from dataclasses import dataclass, field


def _ci_get(data: dict, key: str, default=None):
    """Case-insensitive dictionary key lookup.

    Mirrors Go's encoding/json case-insensitive field matching behavior.
    Go's JSON decoder performs case-insensitive matching when unmarshaling
    JSON into struct fields, so both 'contractId' and 'contractID' match.

    Args:
        data: Dictionary to search.
        key: Key to look up (case-insensitive).
        default: Default value if key is not found.

    Returns:
        Value for the key, or default if not found.
    """
    if key in data:
        return data[key]
    lower_key = key.lower()
    for k, v in data.items():
        if k.lower() == lower_key:
            return v
    return default


# Names must match Go v12 constant identifiers exactly — cannot use UPPER_CASE.
# pylint: disable=invalid-name

# CDNType constants (Go cloudaccess.go lines 141-143)
ChinaCDN: str = "CHINA_CDN"
RussiaCDN: str = "RUSSIA_CDN"

# NetworkType constants (Go cloudaccess.go lines 146-148)
NetworkEnhanced: str = "ENHANCED_TLS"
NetworkStandard: str = "STANDARD_TLS"

# AuthType constants (Go cloudaccess.go lines 151-157)
AuthAWS: str = "AWS4_HMAC_SHA256"
AuthGOOG: str = "GOOG4_HMAC_SHA256"
AuthAOS: str = "AOS4_HMAC_SHA256"
AuthAVMCloudinary: str = "AVM_CLOUDINARY"

# ProcessingType constants (Go cloudaccess.go lines 160-164)
ProcessingInProgress: str = "IN_PROGRESS"
ProcessingFailed: str = "FAILED"
ProcessingDone: str = "DONE"

# DeploymentStatus constants (Go access_key_version.go lines 90-97)
PendingActivation: str = "PENDING_ACTIVATION"
Active: str = "ACTIVE"
PendingDeletion: str = "PENDING_DELETION"

# LookupStatus constants (Go properties.go lines 65-76)
LookupComplete: str = "COMPLETE"
LookupError: str = "ERROR"  # pylint: disable=redefined-builtin
LookupInProgress: str = "IN_PROGRESS"
LookupPending: str = "PENDING"
LookupSubmitted: str = "SUBMITTED"

# pylint: enable=invalid-name


# ===================================================================
# Shared dataclasses (from cloudaccess.go)
# ===================================================================


@dataclass
class SecureNetwork:
    """Additional information about network configuration.

    Mirrors Go SecureNetwork (cloudaccess.go lines 121-124).

    JSON fields:
        additionalCdn (*CDNType, omitempty) -> str | None
        securityNetwork (NetworkType) -> str
    """

    additional_cdn: str | None = None
    security_network: str = ""

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary with camelCase keys."""
        result: dict = {}
        if self.additional_cdn is not None:
            result["additionalCdn"] = self.additional_cdn
        result["securityNetwork"] = self.security_network
        return result

    @classmethod
    def from_dict(cls, data: dict) -> SecureNetwork:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(
            additional_cdn=_ci_get(data, "additionalCdn"),
            security_network=_ci_get(data, "securityNetwork", ""),
        )


@dataclass
class KeyLink:
    """Hypermedia link for an access key.

    Mirrors Go KeyLink (cloudaccess.go lines 99-102).

    JSON fields:
        accessKeyUid (int64) -> int
        link (string) -> str
    """

    access_key_uid: int = 0
    link: str = ""

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary with camelCase keys."""
        return {
            "accessKeyUid": self.access_key_uid,
            "link": self.link,
        }

    @classmethod
    def from_dict(cls, data: dict) -> KeyLink:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(
            access_key_uid=_ci_get(data, "accessKeyUid", 0),
            link=_ci_get(data, "link", ""),
        )


@dataclass
class KeyVersion:
    """Version details with hypermedia link.

    Mirrors Go KeyVersion (cloudaccess.go lines 105-109).

    JSON fields:
        accessKeyUid (int64) -> int
        link (string) -> str
        version (int64) -> int
    """

    access_key_uid: int = 0
    link: str = ""
    version: int = 0

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary with camelCase keys."""
        return {
            "accessKeyUid": self.access_key_uid,
            "link": self.link,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> KeyVersion:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(
            access_key_uid=_ci_get(data, "accessKeyUid", 0),
            link=_ci_get(data, "link", ""),
            version=_ci_get(data, "version", 0),
        )


@dataclass
class RequestInformation:
    """Information about a request to create an access key.

    Mirrors Go RequestInformation (cloudaccess.go lines 112-118).

    JSON fields:
        accessKeyName (string) -> str
        authenticationMethod (AuthType) -> str
        contractId (string) -> str
        groupId (int64) -> int
        networkConfiguration (*SecureNetwork) -> SecureNetwork | None
    """

    access_key_name: str = ""
    authentication_method: str = ""
    contract_id: str = ""
    group_id: int = 0
    network_configuration: SecureNetwork | None = None

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary with camelCase keys."""
        result: dict = {
            "accessKeyName": self.access_key_name,
            "authenticationMethod": self.authentication_method,
            "contractId": self.contract_id,
            "groupId": self.group_id,
        }
        if self.network_configuration is not None:
            result["networkConfiguration"] = self.network_configuration.to_dict()
        else:
            result["networkConfiguration"] = None
        return result

    @classmethod
    def from_dict(cls, data: dict) -> RequestInformation:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        net_cfg_data = _ci_get(data, "networkConfiguration")
        return cls(
            access_key_name=_ci_get(data, "accessKeyName", ""),
            authentication_method=_ci_get(data, "authenticationMethod", ""),
            contract_id=_ci_get(data, "contractId", ""),
            group_id=_ci_get(data, "groupId", 0),
            network_configuration=(
                SecureNetwork.from_dict(net_cfg_data)
                if net_cfg_data
                else None
            ),
        )


# ===================================================================
# Access Key types (from access_key.go)
# ===================================================================


@dataclass
class Credentials:
    """Credentials for signing API requests to a cloud origin.

    Mirrors Go Credentials (access_key.go lines 45-48).

    JSON fields:
        cloudAccessKeyId (string) -> str
        cloudSecretAccessKey (string) -> str
    """

    cloud_access_key_id: str = ""
    cloud_secret_access_key: str = ""

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary with camelCase keys."""
        return {
            "cloudAccessKeyId": self.cloud_access_key_id,
            "cloudSecretAccessKey": self.cloud_secret_access_key,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Credentials:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(
            cloud_access_key_id=_ci_get(data, "cloudAccessKeyId", ""),
            cloud_secret_access_key=_ci_get(data, "cloudSecretAccessKey", ""),
        )


@dataclass
class Group:
    """Group assignment for an access key.

    Mirrors Go Group (access_key.go lines 78-82).

    JSON fields:
        contractIds ([]string) -> list[str]
        groupId (int64) -> int
        groupName (*string) -> str | None
    """

    contract_ids: list[str] = field(default_factory=list)
    group_id: int = 0
    group_name: str | None = None

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary with camelCase keys."""
        return {
            "contractIds": list(self.contract_ids),
            "groupId": self.group_id,
            "groupName": self.group_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Group:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(
            contract_ids=_ci_get(data, "contractIds", []),
            group_id=_ci_get(data, "groupId", 0),
            group_name=_ci_get(data, "groupName"),
        )


@dataclass
class GetAccessKeyStatusRequest:
    """Parameters for the GetAccessKeyStatus operation.

    Mirrors Go GetAccessKeyStatusRequest (access_key.go lines 30-32).
    """

    request_id: int = 0

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary."""
        return {"requestId": self.request_id}

    @classmethod
    def from_dict(cls, data: dict) -> GetAccessKeyStatusRequest:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(request_id=_ci_get(data, "requestId", 0))


@dataclass
class GetAccessKeyStatusResponse:  # pylint: disable=too-many-instance-attributes
    """Response from the GetAccessKeyStatus operation.

    Mirrors Go GetAccessKeyStatusResponse (access_key.go lines 18-28).

    JSON fields:
        accessKey (*KeyLink) -> KeyLink | None
        accessKeyVersion (*KeyVersion) -> KeyVersion | None
        authenticationMethod (string) -> str
        processingStatus (ProcessingType) -> str
        request (*RequestInformation) -> RequestInformation | None
        requestDate (time.Time) -> str
        requestId (int64) -> int
        requestedBy (string) -> str
    """

    access_key: KeyLink | None = None
    access_key_version: KeyVersion | None = None
    authentication_method: str = ""
    processing_status: str = ""
    request: RequestInformation | None = None
    request_date: str = ""
    request_id: int = 0
    requested_by: str = ""

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary with camelCase keys."""
        return {
            "accessKey": self.access_key.to_dict() if self.access_key else None,
            "accessKeyVersion": (
                self.access_key_version.to_dict()
                if self.access_key_version
                else None
            ),
            "authenticationMethod": self.authentication_method,
            "processingStatus": self.processing_status,
            "request": (
                self.request.to_dict() if self.request else None
            ),
            "requestDate": self.request_date,
            "requestId": self.request_id,
            "requestedBy": self.requested_by,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GetAccessKeyStatusResponse:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        ak_data = _ci_get(data, "accessKey")
        akv_data = _ci_get(data, "accessKeyVersion")
        req_data = _ci_get(data, "request")
        return cls(
            access_key=KeyLink.from_dict(ak_data) if ak_data else None,
            access_key_version=(
                KeyVersion.from_dict(akv_data) if akv_data else None
            ),
            authentication_method=_ci_get(data, "authenticationMethod", ""),
            processing_status=_ci_get(data, "processingStatus", ""),
            request=(
                RequestInformation.from_dict(req_data)
                if req_data
                else None
            ),
            request_date=_ci_get(data, "requestDate", ""),
            request_id=_ci_get(data, "requestId", 0),
            requested_by=_ci_get(data, "requestedBy", ""),
        )


@dataclass
class CreateAccessKeyRequest:
    """Request body for the CreateAccessKey operation.

    Mirrors Go CreateAccessKeyRequest (access_key.go lines 35-42).

    JSON fields:
        accessKeyName (string) -> str
        authenticationMethod (string) -> str
        contractId (string) -> str
        credentials (Credentials) -> Credentials
        groupId (int64) -> int
        networkConfiguration (SecureNetwork) -> SecureNetwork
    """

    access_key_name: str = ""
    authentication_method: str = ""
    contract_id: str = ""
    credentials: Credentials = field(default_factory=Credentials)
    group_id: int = 0
    network_configuration: SecureNetwork = field(default_factory=SecureNetwork)

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary with camelCase keys."""
        return {
            "accessKeyName": self.access_key_name,
            "authenticationMethod": self.authentication_method,
            "contractId": self.contract_id,
            "credentials": self.credentials.to_dict(),
            "groupId": self.group_id,
            "networkConfiguration": self.network_configuration.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> CreateAccessKeyRequest:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        creds_data = _ci_get(data, "credentials", {})
        net_cfg_data = _ci_get(data, "networkConfiguration", {})
        return cls(
            access_key_name=_ci_get(data, "accessKeyName", ""),
            authentication_method=_ci_get(data, "authenticationMethod", ""),
            contract_id=_ci_get(data, "contractId", ""),
            credentials=Credentials.from_dict(creds_data),
            group_id=_ci_get(data, "groupId", 0),
            network_configuration=SecureNetwork.from_dict(net_cfg_data),
        )


@dataclass
class CreateAccessKeyResponse:
    """Response from the CreateAccessKey operation.

    Mirrors Go CreateAccessKeyResponse (access_key.go lines 51-55).

    JSON fields:
        requestId (int64, omitempty) -> int
        retryAfter (int64, omitempty) -> int
    The location field is captured from the HTTP response Location header.
    """

    request_id: int = 0
    retry_after: int = 0
    location: str = ""

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary with camelCase keys."""
        return {
            "requestId": self.request_id,
            "retryAfter": self.retry_after,
            "location": self.location,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CreateAccessKeyResponse:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(
            request_id=_ci_get(data, "requestId", 0),
            retry_after=_ci_get(data, "retryAfter", 0),
        )


@dataclass
class AccessKeyRequest:
    """Request parameters for GetAccessKey, UpdateAccessKey, DeleteAccessKey.

    Mirrors Go AccessKeyRequest (access_key.go lines 58-60).
    """

    access_key_uid: int = 0

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary."""
        return {"accessKeyUid": self.access_key_uid}

    @classmethod
    def from_dict(cls, data: dict) -> AccessKeyRequest:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(access_key_uid=_ci_get(data, "accessKeyUid", 0))


@dataclass
class AccessKeyResponse:  # pylint: disable=too-many-instance-attributes
    """Response item containing access key details.

    Mirrors Go AccessKeyResponse (access_key.go lines 63-72).

    JSON fields:
        accessKeyUid (int64) -> int
        accessKeyName (string) -> str
        authenticationMethod (string) -> str
        networkConfiguration (*SecureNetwork) -> SecureNetwork | None
        latestVersion (int64) -> int
        groups ([]Group) -> list[Group]
        createdBy (string) -> str
        createdTime (time.Time) -> str
    """

    access_key_uid: int = 0
    access_key_name: str = ""
    authentication_method: str = ""
    network_configuration: SecureNetwork | None = None
    latest_version: int = 0
    groups: list[Group] = field(default_factory=list)
    created_by: str = ""
    created_time: str = ""

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary with camelCase keys."""
        return {
            "accessKeyUid": self.access_key_uid,
            "accessKeyName": self.access_key_name,
            "authenticationMethod": self.authentication_method,
            "networkConfiguration": (
                self.network_configuration.to_dict()
                if self.network_configuration
                else None
            ),
            "latestVersion": self.latest_version,
            "groups": [g.to_dict() for g in self.groups],
            "createdBy": self.created_by,
            "createdTime": self.created_time,
        }

    @classmethod
    def from_dict(cls, data: dict) -> AccessKeyResponse:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        net_cfg_data = _ci_get(data, "networkConfiguration")
        groups_data = _ci_get(data, "groups", [])
        return cls(
            access_key_uid=_ci_get(data, "accessKeyUid", 0),
            access_key_name=_ci_get(data, "accessKeyName", ""),
            authentication_method=_ci_get(data, "authenticationMethod", ""),
            network_configuration=(
                SecureNetwork.from_dict(net_cfg_data)
                if net_cfg_data
                else None
            ),
            latest_version=_ci_get(data, "latestVersion", 0),
            groups=[Group.from_dict(g) for g in groups_data],
            created_by=_ci_get(data, "createdBy", ""),
            created_time=_ci_get(data, "createdTime", ""),
        )


# GetAccessKeyResponse is a type alias for AccessKeyResponse (Go line 75)
GetAccessKeyResponse = AccessKeyResponse


@dataclass
class ListAccessKeysRequest:
    """Request parameters for the ListAccessKeys operation.

    Mirrors Go ListAccessKeysRequest (access_key.go lines 85-87).
    """

    version_guid: str = ""

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary."""
        return {"versionGuid": self.version_guid}

    @classmethod
    def from_dict(cls, data: dict) -> ListAccessKeysRequest:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(version_guid=_ci_get(data, "versionGuid", ""))


@dataclass
class ListAccessKeysResponse:
    """Response from the ListAccessKeys operation.

    Mirrors Go ListAccessKeysResponse (access_key.go lines 90-92).

    JSON fields:
        accessKeys ([]AccessKeyResponse) -> list[AccessKeyResponse]
    """

    access_keys: list[AccessKeyResponse] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary with camelCase keys."""
        return {
            "accessKeys": [ak.to_dict() for ak in self.access_keys],
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListAccessKeysResponse:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        keys_data = _ci_get(data, "accessKeys", [])
        return cls(
            access_keys=[
                AccessKeyResponse.from_dict(ak) for ak in keys_data
            ],
        )


@dataclass
class UpdateAccessKeyRequest:
    """Request body for the UpdateAccessKey operation.

    Mirrors Go UpdateAccessKeyRequest (access_key.go lines 95-97).

    JSON fields:
        accessKeyName (string, omitempty) -> str
    """

    access_key_name: str = ""

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary with camelCase keys."""
        result: dict = {}
        if self.access_key_name:
            result["accessKeyName"] = self.access_key_name
        return result

    @classmethod
    def from_dict(cls, data: dict) -> UpdateAccessKeyRequest:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(access_key_name=_ci_get(data, "accessKeyName", ""))


@dataclass
class UpdateAccessKeyResponse:
    """Response from the UpdateAccessKey operation.

    Mirrors Go UpdateAccessKeyResponse (access_key.go lines 100-103).

    JSON fields:
        accessKeyUid (int64) -> int
        accessKeyName (string) -> str
    """

    access_key_uid: int = 0
    access_key_name: str = ""

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary with camelCase keys."""
        return {
            "accessKeyUid": self.access_key_uid,
            "accessKeyName": self.access_key_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> UpdateAccessKeyResponse:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(
            access_key_uid=_ci_get(data, "accessKeyUid", 0),
            access_key_name=_ci_get(data, "accessKeyName", ""),
        )


# ===================================================================
# Access Key Version types (from access_key_version.go)
# ===================================================================


@dataclass
class AccessKeyVersion:
    """Access key version details.

    Mirrors Go AccessKeyVersion (access_key_version.go lines 76-84).

    JSON fields:
        accessKeyUid (int64) -> int
        cloudAccessKeyId (*string) -> str | None
        createdBy (string) -> str
        createdTime (time.Time) -> str
        deploymentStatus (DeploymentStatus) -> str
        version (int64) -> int
        versionGuid (string) -> str
    """

    access_key_uid: int = 0
    cloud_access_key_id: str | None = None
    created_by: str = ""
    created_time: str = ""
    deployment_status: str = ""
    version: int = 0
    version_guid: str = ""

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary with camelCase keys."""
        return {
            "accessKeyUid": self.access_key_uid,
            "cloudAccessKeyId": self.cloud_access_key_id,
            "createdBy": self.created_by,
            "createdTime": self.created_time,
            "deploymentStatus": self.deployment_status,
            "version": self.version,
            "versionGuid": self.version_guid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> AccessKeyVersion:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(
            access_key_uid=_ci_get(data, "accessKeyUid", 0),
            cloud_access_key_id=_ci_get(data, "cloudAccessKeyId"),
            created_by=_ci_get(data, "createdBy", ""),
            created_time=_ci_get(data, "createdTime", ""),
            deployment_status=_ci_get(data, "deploymentStatus", ""),
            version=_ci_get(data, "version", 0),
            version_guid=_ci_get(data, "versionGuid", ""),
        )


@dataclass
class GetAccessKeyVersionStatusRequest:
    """Parameters for the GetAccessKeyVersionStatus operation.

    Mirrors Go GetAccessKeyVersionStatusRequest
    (access_key_version.go lines 25-27).
    """

    request_id: int = 0

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary."""
        return {"requestId": self.request_id}

    @classmethod
    def from_dict(cls, data: dict) -> GetAccessKeyVersionStatusRequest:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(request_id=_ci_get(data, "requestId", 0))


@dataclass
class GetAccessKeyVersionStatusResponse:
    """Response from the GetAccessKeyVersionStatus operation.

    Mirrors Go GetAccessKeyVersionStatusResponse
    (access_key_version.go lines 17-23).

    JSON fields:
        accessKeyVersion (*KeyVersion) -> KeyVersion | None
        processingStatus (ProcessingType) -> str
        requestDate (time.Time) -> str
        requestedBy (string) -> str
    """

    access_key_version: KeyVersion | None = None
    processing_status: str = ""
    request_date: str = ""
    requested_by: str = ""

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary with camelCase keys."""
        return {
            "accessKeyVersion": (
                self.access_key_version.to_dict()
                if self.access_key_version
                else None
            ),
            "processingStatus": self.processing_status,
            "requestDate": self.request_date,
            "requestedBy": self.requested_by,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GetAccessKeyVersionStatusResponse:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        akv_data = _ci_get(data, "accessKeyVersion")
        return cls(
            access_key_version=(
                KeyVersion.from_dict(akv_data) if akv_data else None
            ),
            processing_status=_ci_get(data, "processingStatus", ""),
            request_date=_ci_get(data, "requestDate", ""),
            requested_by=_ci_get(data, "requestedBy", ""),
        )


@dataclass
class CreateAccessKeyVersionRequestBody:
    """Body payload for the CreateAccessKeyVersion operation.

    Mirrors Go CreateAccessKeyVersionRequestBody
    (access_key_version.go lines 36-39).

    JSON fields:
        cloudAccessKeyId (string) -> str
        cloudSecretAccessKey (string) -> str
    """

    cloud_access_key_id: str = ""
    cloud_secret_access_key: str = ""

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary with camelCase keys."""
        return {
            "cloudAccessKeyId": self.cloud_access_key_id,
            "cloudSecretAccessKey": self.cloud_secret_access_key,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CreateAccessKeyVersionRequestBody:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(
            cloud_access_key_id=_ci_get(data, "cloudAccessKeyId", ""),
            cloud_secret_access_key=_ci_get(
                data, "cloudSecretAccessKey", ""
            ),
        )


@dataclass
class CreateAccessKeyVersionRequest:
    """Parameters for the CreateAccessKeyVersion operation.

    Mirrors Go CreateAccessKeyVersionRequest
    (access_key_version.go lines 30-33).
    """

    access_key_uid: int = 0
    body: CreateAccessKeyVersionRequestBody = field(
        default_factory=CreateAccessKeyVersionRequestBody
    )

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "accessKeyUid": self.access_key_uid,
            "body": self.body.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> CreateAccessKeyVersionRequest:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        body_data = _ci_get(data, "body", {})
        return cls(
            access_key_uid=_ci_get(data, "accessKeyUid", 0),
            body=CreateAccessKeyVersionRequestBody.from_dict(body_data),
        )


@dataclass
class CreateAccessKeyVersionResponse:
    """Response from the CreateAccessKeyVersion operation.

    Mirrors Go CreateAccessKeyVersionResponse
    (access_key_version.go lines 42-45).

    JSON fields:
        requestId (int64) -> int
        retryAfter (int64) -> int
    """

    request_id: int = 0
    retry_after: int = 0

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary with camelCase keys."""
        return {
            "requestId": self.request_id,
            "retryAfter": self.retry_after,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CreateAccessKeyVersionResponse:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(
            request_id=_ci_get(data, "requestId", 0),
            retry_after=_ci_get(data, "retryAfter", 0),
        )


@dataclass
class GetAccessKeyVersionRequest:
    """Parameters for the GetAccessKeyVersion operation.

    Mirrors Go GetAccessKeyVersionRequest
    (access_key_version.go lines 48-51).
    """

    version: int = 0
    access_key_uid: int = 0

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "version": self.version,
            "accessKeyUid": self.access_key_uid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GetAccessKeyVersionRequest:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(
            version=_ci_get(data, "version", 0),
            access_key_uid=_ci_get(data, "accessKeyUid", 0),
        )


# GetAccessKeyVersionResponse is a type alias (Go line 54)
GetAccessKeyVersionResponse = AccessKeyVersion


@dataclass
class ListAccessKeyVersionsRequest:
    """Parameters for the ListAccessKeyVersions operation.

    Mirrors Go ListAccessKeyVersionsRequest
    (access_key_version.go lines 57-59).
    """

    access_key_uid: int = 0

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary."""
        return {"accessKeyUid": self.access_key_uid}

    @classmethod
    def from_dict(cls, data: dict) -> ListAccessKeyVersionsRequest:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(access_key_uid=_ci_get(data, "accessKeyUid", 0))


@dataclass
class ListAccessKeyVersionsResponse:
    """Response from the ListAccessKeyVersions operation.

    Mirrors Go ListAccessKeyVersionsResponse
    (access_key_version.go lines 62-64).

    JSON fields:
        accessKeyVersions ([]AccessKeyVersion) -> list[AccessKeyVersion]
    """

    access_key_versions: list[AccessKeyVersion] = field(
        default_factory=list
    )

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary with camelCase keys."""
        return {
            "accessKeyVersions": [
                v.to_dict() for v in self.access_key_versions
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListAccessKeyVersionsResponse:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        versions_data = _ci_get(data, "accessKeyVersions", [])
        return cls(
            access_key_versions=[
                AccessKeyVersion.from_dict(v) for v in versions_data
            ],
        )


@dataclass
class DeleteAccessKeyVersionRequest:
    """Parameters for the DeleteAccessKeyVersion operation.

    Mirrors Go DeleteAccessKeyVersionRequest
    (access_key_version.go lines 67-70).
    """

    version: int = 0
    access_key_uid: int = 0

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "version": self.version,
            "accessKeyUid": self.access_key_uid,
        }

    @classmethod
    def from_dict(cls, data: dict) -> DeleteAccessKeyVersionRequest:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(
            version=_ci_get(data, "version", 0),
            access_key_uid=_ci_get(data, "accessKeyUid", 0),
        )


# DeleteAccessKeyVersionResponse is a type alias (Go line 73)
DeleteAccessKeyVersionResponse = AccessKeyVersion


# ===================================================================
# Property types (from properties.go)
# ===================================================================


@dataclass
class Property:
    """Property related to an access key version.

    Mirrors Go Property (properties.go lines 28-35).

    JSON fields:
        accessKeyUid (int64) -> int
        version (int64) -> int
        propertyId (string) -> str
        propertyName (string) -> str
        productionVersion (*int64) -> int | None
        stagingVersion (*int64) -> int | None
    """

    access_key_uid: int = 0
    version: int = 0
    property_id: str = ""
    property_name: str = ""
    production_version: int | None = None
    staging_version: int | None = None

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary with camelCase keys."""
        return {
            "accessKeyUid": self.access_key_uid,
            "version": self.version,
            "propertyId": self.property_id,
            "propertyName": self.property_name,
            "productionVersion": self.production_version,
            "stagingVersion": self.staging_version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Property:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(
            access_key_uid=_ci_get(data, "accessKeyUid", 0),
            version=_ci_get(data, "version", 0),
            property_id=_ci_get(data, "propertyId", ""),
            property_name=_ci_get(data, "propertyName", ""),
            production_version=_ci_get(data, "productionVersion"),
            staging_version=_ci_get(data, "stagingVersion"),
        )


@dataclass
class LookupPropertiesRequest:
    """Parameters for the LookupProperties operation.

    Mirrors Go LookupPropertiesRequest (properties.go lines 17-20).
    """

    access_key_uid: int = 0
    version: int = 0

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "accessKeyUid": self.access_key_uid,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> LookupPropertiesRequest:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(
            access_key_uid=_ci_get(data, "accessKeyUid", 0),
            version=_ci_get(data, "version", 0),
        )


@dataclass
class LookupPropertiesResponse:
    """Response from the LookupProperties operation.

    Mirrors Go LookupPropertiesResponse (properties.go lines 23-25).

    JSON fields:
        properties ([]Property) -> list[Property]
    """

    properties: list[Property] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary with camelCase keys."""
        return {
            "properties": [p.to_dict() for p in self.properties],
        }

    @classmethod
    def from_dict(cls, data: dict) -> LookupPropertiesResponse:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        props_data = _ci_get(data, "properties", [])
        return cls(
            properties=[Property.from_dict(p) for p in props_data],
        )


@dataclass
class GetAsyncPropertiesLookupIDRequest:
    """Parameters for the GetAsyncPropertiesLookupID operation.

    Mirrors Go GetAsyncPropertiesLookupIDRequest
    (properties.go lines 38-41).
    """

    access_key_uid: int = 0
    version: int = 0

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary."""
        return {
            "accessKeyUid": self.access_key_uid,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GetAsyncPropertiesLookupIDRequest:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(
            access_key_uid=_ci_get(data, "accessKeyUid", 0),
            version=_ci_get(data, "version", 0),
        )


@dataclass
class GetAsyncPropertiesLookupIDResponse:
    """Response from the GetAsyncPropertiesLookupID operation.

    Mirrors Go GetAsyncPropertiesLookupIDResponse
    (properties.go lines 44-47).

    JSON fields:
        lookupId (int64) -> int
        retryAfter (int64) -> int
    """

    lookup_id: int = 0
    retry_after: int = 0

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary with camelCase keys."""
        return {
            "lookupId": self.lookup_id,
            "retryAfter": self.retry_after,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GetAsyncPropertiesLookupIDResponse:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(
            lookup_id=_ci_get(data, "lookupId", 0),
            retry_after=_ci_get(data, "retryAfter", 0),
        )


@dataclass
class PerformAsyncPropertiesLookupRequest:
    """Parameters for the PerformAsyncPropertiesLookup operation.

    Mirrors Go PerformAsyncPropertiesLookupRequest
    (properties.go lines 50-52).
    """

    lookup_id: int = 0

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary."""
        return {"lookupId": self.lookup_id}

    @classmethod
    def from_dict(cls, data: dict) -> PerformAsyncPropertiesLookupRequest:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        return cls(lookup_id=_ci_get(data, "lookupId", 0))


@dataclass
class PerformAsyncPropertiesLookupResponse:
    """Response from the PerformAsyncPropertiesLookup operation.

    Mirrors Go PerformAsyncPropertiesLookupResponse
    (properties.go lines 55-59).

    JSON fields:
        lookupId (int64) -> int
        lookupStatus (LookupStatus) -> str
        properties ([]Property) -> list[Property]
    """

    lookup_id: int = 0
    lookup_status: str = ""
    properties: list[Property] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dictionary with camelCase keys."""
        return {
            "lookupId": self.lookup_id,
            "lookupStatus": self.lookup_status,
            "properties": [p.to_dict() for p in self.properties],
        }

    @classmethod
    def from_dict(cls, data: dict) -> PerformAsyncPropertiesLookupResponse:
        """Deserialize from a JSON-parsed dictionary (case-insensitive keys)."""
        if not data:
            return cls()
        props_data = _ci_get(data, "properties", [])
        return cls(
            lookup_id=_ci_get(data, "lookupId", 0),
            lookup_status=_ci_get(data, "lookupStatus", ""),
            properties=[Property.from_dict(p) for p in props_data],
        )
