# pylint: disable=too-many-lines
"""Cloud Wrapper API request/response models."""
from __future__ import annotations

from dataclasses import dataclass, field


# SamplingFrequency type aliases (Go: SamplingFrequency string)
SAMPLING_FREQUENCY_ZERO: str = "ZERO"
SAMPLING_FREQUENCY_ONE_TENTH: str = "ONE_TENTH"

# ForwardType type aliases (Go: ForwardType string)
FORWARD_TYPE_ORIGIN_ONLY: str = "ORIGIN_ONLY"
FORWARD_TYPE_MIDGRESS_ONLY: str = "MIDGRESS_ONLY"
FORWARD_TYPE_ORIGIN_AND_MIDGRESS: str = "ORIGIN_AND_MIDGRESS"

# RequestType type aliases (Go: RequestType string)
REQUEST_TYPE_EDGE_ONLY: str = "EDGE_ONLY"
REQUEST_TYPE_EDGE_AND_MIDGRESS: str = "EDGE_AND_MIDGRESS"

# StatusType type aliases (Go: StatusType string)
STATUS_ACTIVE: str = "ACTIVE"
STATUS_SAVED: str = "SAVED"
STATUS_IN_PROGRESS: str = "IN_PROGRESS"
STATUS_DELETE_IN_PROGRESS: str = "DELETE_IN_PROGRESS"
STATUS_FAILED: str = "FAILED"

# Unit type aliases (Go: Unit string)
UNIT_GB: str = "GB"
UNIT_TB: str = "TB"

# CapacityType type aliases (Go: CapacityType string)
CAPACITY_TYPE_MEDIA: str = "MEDIA"
CAPACITY_TYPE_WEB_STANDARD_TLS: str = "WEB_STANDARD_TLS"
CAPACITY_TYPE_WEB_ENHANCED_TLS: str = "WEB_ENHANCED_TLS"

# PropertyType type aliases (Go: PropertyType string)
PROPERTY_TYPE_WEB: str = "WEB"
PROPERTY_TYPE_MEDIA: str = "MEDIA"

# OriginType type aliases (Go: OriginType string)
ORIGIN_TYPE_CUSTOMER: str = "CUSTOMER"
ORIGIN_TYPE_NET_STORAGE: str = "NET_STORAGE"


@dataclass
class Capacity:
    """Capacity information shared between configurations and capacity endpoints.

    Go reference: cloudwrapper.Capacity (capacity.go)
    """

    value: int = 0
    unit: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "value": self.value,
            "unit": self.unit,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Capacity:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            value=data.get("value", 0),
            unit=data.get("unit", ""),
        )


@dataclass
class Origin:
    """Origin corresponding to properties in configuration.

    Go reference: cloudwrapper.Origin (configurations.go)
    """

    hostname: str = ""
    origin_id: str = ""
    property_id: int = 0

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "hostname": self.hostname,
            "originId": self.origin_id,
            "propertyId": self.property_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Origin:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            hostname=data.get("hostname", ""),
            origin_id=data.get("originId", ""),
            property_id=data.get("propertyId", 0),
        )


@dataclass
class CDNAuthKey:
    """Auth key configured for a CDN.

    Go reference: cloudwrapper.CDNAuthKey (configurations.go)
    """

    auth_key_name: str = ""
    expiry_date: str = ""
    header_name: str = ""
    secret: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names.

        Fields expiryDate, headerName, secret have omitempty in Go.
        """
        result: dict = {
            "authKeyName": self.auth_key_name,
        }
        if self.expiry_date:
            result["expiryDate"] = self.expiry_date
        if self.header_name:
            result["headerName"] = self.header_name
        if self.secret:
            result["secret"] = self.secret
        return result

    @classmethod
    def from_dict(cls, data: dict) -> CDNAuthKey:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            auth_key_name=data.get("authKeyName", ""),
            expiry_date=data.get("expiryDate", ""),
            header_name=data.get("headerName", ""),
            secret=data.get("secret", ""),
        )


@dataclass
class CDN:
    """CDN added for the configuration.

    Go reference: cloudwrapper.CDN (configurations.go)
    """

    cdn_auth_keys: list[CDNAuthKey] = field(default_factory=list)
    cdn_code: str = ""
    enabled: bool = False
    https_only: bool = False
    ip_acl_cidrs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names.

        Fields cdnAuthKeys, httpsOnly, ipAclCidrs have omitempty in Go.
        """
        result: dict = {
            "cdnCode": self.cdn_code,
            "enabled": self.enabled,
        }
        if self.cdn_auth_keys:
            result["cdnAuthKeys"] = [
                key.to_dict() for key in self.cdn_auth_keys
            ]
        if self.https_only:
            result["httpsOnly"] = self.https_only
        if self.ip_acl_cidrs:
            result["ipAclCidrs"] = list(self.ip_acl_cidrs)
        return result

    @classmethod
    def from_dict(cls, data: dict) -> CDN:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            cdn_auth_keys=[
                CDNAuthKey.from_dict(k)
                for k in data.get("cdnAuthKeys", [])
            ],
            cdn_code=data.get("cdnCode", ""),
            enabled=data.get("enabled", False),
            https_only=data.get("httpsOnly", False),
            ip_acl_cidrs=data.get("ipAclCidrs", []),
        )


@dataclass
class BOCC:
    """Diagnostic data beacon details.

    Go reference: cloudwrapper.BOCC (configurations.go)
    """

    conditional_sampling_frequency: str = ""
    enabled: bool = False
    forward_type: str = ""
    request_type: str = ""
    sampling_frequency: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names.

        All fields except enabled have omitempty in Go.
        """
        result: dict = {
            "enabled": self.enabled,
        }
        if self.conditional_sampling_frequency:
            result["conditionalSamplingFrequency"] = (
                self.conditional_sampling_frequency
            )
        if self.forward_type:
            result["forwardType"] = self.forward_type
        if self.request_type:
            result["requestType"] = self.request_type
        if self.sampling_frequency:
            result["samplingFrequency"] = self.sampling_frequency
        return result

    @classmethod
    def from_dict(cls, data: dict) -> BOCC:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            conditional_sampling_frequency=data.get(
                "conditionalSamplingFrequency", ""
            ),
            enabled=data.get("enabled", False),
            forward_type=data.get("forwardType", ""),
            request_type=data.get("requestType", ""),
            sampling_frequency=data.get("samplingFrequency", ""),
        )


@dataclass
class DataStreams:
    """Data streams details.

    Go reference: cloudwrapper.DataStreams (configurations.go)
    """

    data_stream_ids: list[int] = field(default_factory=list)
    enabled: bool = False
    sampling_rate: int | None = None

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names.

        Fields dataStreamIds, samplingRate have omitempty in Go.
        """
        result: dict = {
            "enabled": self.enabled,
        }
        if self.data_stream_ids:
            result["dataStreamIds"] = list(self.data_stream_ids)
        if self.sampling_rate is not None:
            result["samplingRate"] = self.sampling_rate
        return result

    @classmethod
    def from_dict(cls, data: dict) -> DataStreams:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            data_stream_ids=data.get("dataStreamIds", []),
            enabled=data.get("enabled", False),
            sampling_rate=data.get("samplingRate"),
        )


@dataclass
class MultiCDNSettings:
    """Multi CDN Settings details.

    Go reference: cloudwrapper.MultiCDNSettings (configurations.go)
    """

    bocc: BOCC | None = None
    cdns: list[CDN] = field(default_factory=list)
    data_streams: DataStreams | None = None
    enable_soft_alerts: bool = False
    origins: list[Origin] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names.

        Field enableSoftAlerts has omitempty in Go.
        """
        result: dict = {
            "bocc": (
                self.bocc.to_dict() if self.bocc is not None else None
            ),
            "cdns": [cdn.to_dict() for cdn in self.cdns],
            "dataStreams": (
                self.data_streams.to_dict()
                if self.data_streams is not None else None
            ),
            "origins": [origin.to_dict() for origin in self.origins],
        }
        if self.enable_soft_alerts:
            result["enableSoftAlerts"] = self.enable_soft_alerts
        return result

    @classmethod
    def from_dict(cls, data: dict) -> MultiCDNSettings:
        """Deserialize from dict using Go JSON tag names."""
        bocc_raw = data.get("bocc")
        ds_raw = data.get("dataStreams")
        return cls(
            bocc=(
                BOCC.from_dict(bocc_raw)
                if bocc_raw is not None else None
            ),
            cdns=[CDN.from_dict(c) for c in data.get("cdns", [])],
            data_streams=(
                DataStreams.from_dict(ds_raw)
                if ds_raw is not None else None
            ),
            enable_soft_alerts=data.get("enableSoftAlerts", False),
            origins=[
                Origin.from_dict(o) for o in data.get("origins", [])
            ],
        )


@dataclass
class ConfigLocationReq:
    """Location to be configured for the configuration (request).

    Go reference: cloudwrapper.ConfigLocationReq (configurations.go)
    """

    comments: str = ""
    traffic_type_id: int = 0
    capacity: Capacity = field(default_factory=Capacity)

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "comments": self.comments,
            "trafficTypeId": self.traffic_type_id,
            "capacity": self.capacity.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> ConfigLocationReq:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            comments=data.get("comments", ""),
            traffic_type_id=data.get("trafficTypeId", 0),
            capacity=Capacity.from_dict(data.get("capacity", {})),
        )


@dataclass
class ConfigLocationResp:
    """Location to be configured for the configuration (response).

    Go reference: cloudwrapper.ConfigLocationResp (configurations.go)
    """

    comments: str = ""
    traffic_type_id: int = 0
    capacity: Capacity = field(default_factory=Capacity)
    map_name: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "comments": self.comments,
            "trafficTypeId": self.traffic_type_id,
            "capacity": self.capacity.to_dict(),
            "mapName": self.map_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ConfigLocationResp:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            comments=data.get("comments", ""),
            traffic_type_id=data.get("trafficTypeId", 0),
            capacity=Capacity.from_dict(data.get("capacity", {})),
            map_name=data.get("mapName", ""),
        )


@dataclass
class Configuration:  # pylint: disable=too-many-instance-attributes
    """CloudWrapper configuration.

    Go reference: cloudwrapper.Configuration (configurations.go)
    Exactly 15 fields matching Go struct order.
    """

    capacity_alerts_threshold: int | None = None
    comments: str = ""
    contract_id: str = ""
    config_id: int = 0
    locations: list[ConfigLocationResp] = field(default_factory=list)
    multi_cdn_settings: MultiCDNSettings | None = None
    status: str = ""
    config_name: str = ""
    last_updated_by: str = ""
    last_updated_date: str = ""
    last_activated_by: str | None = None
    last_activated_date: str | None = None
    notification_emails: list[str] = field(default_factory=list)
    property_ids: list[str] = field(default_factory=list)
    retain_idle_objects: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names.

        No omitempty on any field — all fields always included.
        """
        mcdn = self.multi_cdn_settings
        return {
            "capacityAlertsThreshold": self.capacity_alerts_threshold,
            "comments": self.comments,
            "contractId": self.contract_id,
            "configId": self.config_id,
            "locations": [loc.to_dict() for loc in self.locations],
            "multiCdnSettings": (
                mcdn.to_dict() if mcdn is not None else None
            ),
            "status": self.status,
            "configName": self.config_name,
            "lastUpdatedBy": self.last_updated_by,
            "lastUpdatedDate": self.last_updated_date,
            "lastActivatedBy": self.last_activated_by,
            "lastActivatedDate": self.last_activated_date,
            "notificationEmails": list(self.notification_emails),
            "propertyIds": list(self.property_ids),
            "retainIdleObjects": self.retain_idle_objects,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Configuration:
        """Deserialize from dict using Go JSON tag names."""
        mcdn_raw = data.get("multiCdnSettings")
        return cls(
            capacity_alerts_threshold=data.get(
                "capacityAlertsThreshold"
            ),
            comments=data.get("comments", ""),
            contract_id=data.get("contractId", ""),
            config_id=data.get("configId", 0),
            locations=[
                ConfigLocationResp.from_dict(loc)
                for loc in data.get("locations", [])
            ],
            multi_cdn_settings=(
                MultiCDNSettings.from_dict(mcdn_raw)
                if mcdn_raw is not None else None
            ),
            status=data.get("status", ""),
            config_name=data.get("configName", ""),
            last_updated_by=data.get("lastUpdatedBy", ""),
            last_updated_date=data.get("lastUpdatedDate", ""),
            last_activated_by=data.get("lastActivatedBy"),
            last_activated_date=data.get("lastActivatedDate"),
            notification_emails=data.get("notificationEmails", []),
            property_ids=data.get("propertyIds", []),
            retain_idle_objects=data.get("retainIdleObjects", False),
        )


@dataclass
class ListConfigurationsResponse:
    """Response from ListConfigurations.

    Go reference: cloudwrapper.ListConfigurationsResponse (configurations.go)
    """

    configurations: list[Configuration] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "configurations": [
                cfg.to_dict() for cfg in self.configurations
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListConfigurationsResponse:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            configurations=[
                Configuration.from_dict(cfg)
                for cfg in data.get("configurations", [])
            ],
        )


@dataclass
class GetConfigurationRequest:
    """Parameters for GetConfiguration.

    Go reference: cloudwrapper.GetConfigurationRequest (configurations.go)
    """

    config_id: int = 0

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "configId": self.config_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GetConfigurationRequest:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            config_id=data.get("configId", 0),
        )


@dataclass
class CreateConfigurationRequestBody:  # pylint: disable=too-many-instance-attributes
    """Request body for CreateConfiguration.

    Go reference: cloudwrapper.CreateConfigurationRequestBody (configurations.go)
    Exactly 9 fields.
    """

    capacity_alerts_threshold: int | None = None
    comments: str = ""
    contract_id: str = ""
    locations: list[ConfigLocationReq] = field(default_factory=list)
    multi_cdn_settings: MultiCDNSettings | None = None
    config_name: str = ""
    notification_emails: list[str] = field(default_factory=list)
    property_ids: list[str] = field(default_factory=list)
    retain_idle_objects: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names.

        capacityAlertsThreshold, multiCdnSettings, notificationEmails,
        retainIdleObjects have omitempty in Go.
        """
        result: dict = {
            "comments": self.comments,
            "contractId": self.contract_id,
            "locations": [loc.to_dict() for loc in self.locations],
            "configName": self.config_name,
            "propertyIds": list(self.property_ids),
        }
        if self.capacity_alerts_threshold is not None:
            result["capacityAlertsThreshold"] = (
                self.capacity_alerts_threshold
            )
        if self.multi_cdn_settings is not None:
            result["multiCdnSettings"] = (
                self.multi_cdn_settings.to_dict()
            )
        if self.notification_emails:
            result["notificationEmails"] = list(
                self.notification_emails
            )
        if self.retain_idle_objects:
            result["retainIdleObjects"] = self.retain_idle_objects
        return result

    @classmethod
    def from_dict(cls, data: dict) -> CreateConfigurationRequestBody:
        """Deserialize from dict using Go JSON tag names."""
        mcdn_raw = data.get("multiCdnSettings")
        return cls(
            capacity_alerts_threshold=data.get(
                "capacityAlertsThreshold"
            ),
            comments=data.get("comments", ""),
            contract_id=data.get("contractId", ""),
            locations=[
                ConfigLocationReq.from_dict(loc)
                for loc in data.get("locations", [])
            ],
            multi_cdn_settings=(
                MultiCDNSettings.from_dict(mcdn_raw)
                if mcdn_raw is not None else None
            ),
            config_name=data.get("configName", ""),
            notification_emails=data.get("notificationEmails", []),
            property_ids=data.get("propertyIds", []),
            retain_idle_objects=data.get("retainIdleObjects", False),
        )


@dataclass
class CreateConfigurationRequest:
    """Parameters for CreateConfiguration.

    Go reference: cloudwrapper.CreateConfigurationRequest (configurations.go)
    """

    activate: bool = False
    body: CreateConfigurationRequestBody = field(
        default_factory=CreateConfigurationRequestBody
    )

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "activate": self.activate,
            "body": self.body.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> CreateConfigurationRequest:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            activate=data.get("activate", False),
            body=CreateConfigurationRequestBody.from_dict(
                data.get("body", {})
            ),
        )


@dataclass
class UpdateConfigurationRequestBody:
    """Request body for UpdateConfiguration.

    Go reference: cloudwrapper.UpdateConfigurationRequestBody (configurations.go)
    Exactly 7 fields — no contract_id, no config_name.
    """

    capacity_alerts_threshold: int | None = None
    comments: str = ""
    locations: list[ConfigLocationReq] = field(default_factory=list)
    multi_cdn_settings: MultiCDNSettings | None = None
    notification_emails: list[str] = field(default_factory=list)
    property_ids: list[str] = field(default_factory=list)
    retain_idle_objects: bool = False

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names.

        capacityAlertsThreshold, multiCdnSettings, notificationEmails,
        retainIdleObjects have omitempty in Go.
        """
        result: dict = {
            "comments": self.comments,
            "locations": [loc.to_dict() for loc in self.locations],
            "propertyIds": list(self.property_ids),
        }
        if self.capacity_alerts_threshold is not None:
            result["capacityAlertsThreshold"] = (
                self.capacity_alerts_threshold
            )
        if self.multi_cdn_settings is not None:
            result["multiCdnSettings"] = (
                self.multi_cdn_settings.to_dict()
            )
        if self.notification_emails:
            result["notificationEmails"] = list(
                self.notification_emails
            )
        if self.retain_idle_objects:
            result["retainIdleObjects"] = self.retain_idle_objects
        return result

    @classmethod
    def from_dict(cls, data: dict) -> UpdateConfigurationRequestBody:
        """Deserialize from dict using Go JSON tag names."""
        mcdn_raw = data.get("multiCdnSettings")
        return cls(
            capacity_alerts_threshold=data.get(
                "capacityAlertsThreshold"
            ),
            comments=data.get("comments", ""),
            locations=[
                ConfigLocationReq.from_dict(loc)
                for loc in data.get("locations", [])
            ],
            multi_cdn_settings=(
                MultiCDNSettings.from_dict(mcdn_raw)
                if mcdn_raw is not None else None
            ),
            notification_emails=data.get("notificationEmails", []),
            property_ids=data.get("propertyIds", []),
            retain_idle_objects=data.get("retainIdleObjects", False),
        )


@dataclass
class UpdateConfigurationRequest:
    """Parameters for UpdateConfiguration.

    Go reference: cloudwrapper.UpdateConfigurationRequest (configurations.go)
    """

    config_id: int = 0
    activate: bool = False
    body: UpdateConfigurationRequestBody = field(
        default_factory=UpdateConfigurationRequestBody
    )

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "configId": self.config_id,
            "activate": self.activate,
            "body": self.body.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> UpdateConfigurationRequest:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            config_id=data.get("configId", 0),
            activate=data.get("activate", False),
            body=UpdateConfigurationRequestBody.from_dict(
                data.get("body", {})
            ),
        )


@dataclass
class DeleteConfigurationRequest:
    """Parameters for DeleteConfiguration.

    Go reference: cloudwrapper.DeleteConfigurationRequest (configurations.go)
    """

    config_id: int = 0

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "configId": self.config_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> DeleteConfigurationRequest:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            config_id=data.get("configId", 0),
        )


@dataclass
class ActivateConfigurationRequest:
    """Parameters for ActivateConfiguration.

    Go reference: cloudwrapper.ActivateConfigurationRequest (configurations.go)
    configuration_ids is list[int] (Go: []int, NOT []int64).
    """

    configuration_ids: list[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "configurationIds": list(self.configuration_ids),
        }

    @classmethod
    def from_dict(cls, data: dict) -> ActivateConfigurationRequest:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            configuration_ids=data.get("configurationIds", []),
        )


# ---------------------------------------------------------------------------
# Properties / Origins models (properties.go)
# ---------------------------------------------------------------------------


@dataclass
class Property:
    """Property object.

    Go reference: cloudwrapper.Property (properties.go)
    """

    group_id: int = 0
    contract_id: str = ""
    property_id: int = 0
    property_name: str = ""
    type: str = ""  # Go: PropertyType

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "groupId": self.group_id,
            "contractId": self.contract_id,
            "propertyId": self.property_id,
            "propertyName": self.property_name,
            "type": self.type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Property:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            group_id=data.get("groupId", 0),
            contract_id=data.get("contractId", ""),
            property_id=data.get("propertyId", 0),
            property_name=data.get("propertyName", ""),
            type=data.get("type", ""),
        )


@dataclass
class Behavior:
    """Behavior information.

    Go reference: cloudwrapper.Behavior (properties.go)
    """

    hostname: str = ""
    origin_type: str = ""  # Go: OriginType

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "hostname": self.hostname,
            "originType": self.origin_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Behavior:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            hostname=data.get("hostname", ""),
            origin_type=data.get("originType", ""),
        )


@dataclass
class Child:
    """Children rules in a property.

    Go reference: cloudwrapper.Child (properties.go)
    """

    name: str = ""
    behaviors: list[Behavior] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "name": self.name,
            "behaviors": [b.to_dict() for b in self.behaviors],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Child:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            name=data.get("name", ""),
            behaviors=[
                Behavior.from_dict(b)
                for b in data.get("behaviors", [])
            ],
        )


@dataclass
class ListPropertiesRequest:
    """Parameters for ListProperties.

    Go reference: cloudwrapper.ListPropertiesRequest (properties.go)
    """

    unused: bool = False
    contract_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "unused": self.unused,
            "contractIds": list(self.contract_ids),
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListPropertiesRequest:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            unused=data.get("unused", False),
            contract_ids=data.get("contractIds", []),
        )


@dataclass
class ListPropertiesResponse:
    """Response from ListProperties.

    Go reference: cloudwrapper.ListPropertiesResponse (properties.go)
    """

    properties: list[Property] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "properties": [p.to_dict() for p in self.properties],
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListPropertiesResponse:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            properties=[
                Property.from_dict(p)
                for p in data.get("properties", [])
            ],
        )


@dataclass
class ListOriginsRequest:
    """Parameters for ListOrigins.

    Go reference: cloudwrapper.ListOriginsRequest (properties.go)
    """

    property_id: int = 0
    contract_id: str = ""
    group_id: int = 0

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "propertyId": self.property_id,
            "contractId": self.contract_id,
            "groupId": self.group_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListOriginsRequest:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            property_id=data.get("propertyId", 0),
            contract_id=data.get("contractId", ""),
            group_id=data.get("groupId", 0),
        )


@dataclass
class ListOriginsResponse:
    """Response from ListOrigins.

    Go reference: cloudwrapper.ListOriginsResponse (properties.go)
    Has both 'children' and 'default' fields. 'default' is NOT a Python
    keyword; it is valid as a dataclass attribute name.
    """

    children: list[Child] = field(default_factory=list)
    default: list[Behavior] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "children": [c.to_dict() for c in self.children],
            "default": [b.to_dict() for b in self.default],
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListOriginsResponse:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            children=[
                Child.from_dict(c)
                for c in data.get("children", [])
            ],
            default=[
                Behavior.from_dict(b)
                for b in data.get("default", [])
            ],
        )


# ---------------------------------------------------------------------------
# Capacity models (capacity.go)
# ---------------------------------------------------------------------------


@dataclass
class LocationCapacity:
    """Location capacity information.

    Go reference: cloudwrapper.LocationCapacity (capacity.go)
    Exactly 7 fields with 3 nested Capacity objects.
    """

    location_id: int = 0
    location_name: str = ""
    contract_id: str = ""
    type: str = ""  # Go: CapacityType
    approved_capacity: Capacity = field(default_factory=Capacity)
    assigned_capacity: Capacity = field(default_factory=Capacity)
    unassigned_capacity: Capacity = field(default_factory=Capacity)

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "locationId": self.location_id,
            "locationName": self.location_name,
            "contractId": self.contract_id,
            "type": self.type,
            "approvedCapacity": self.approved_capacity.to_dict(),
            "assignedCapacity": self.assigned_capacity.to_dict(),
            "unassignedCapacity": self.unassigned_capacity.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> LocationCapacity:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            location_id=data.get("locationId", 0),
            location_name=data.get("locationName", ""),
            contract_id=data.get("contractId", ""),
            type=data.get("type", ""),
            approved_capacity=Capacity.from_dict(
                data.get("approvedCapacity", {})
            ),
            assigned_capacity=Capacity.from_dict(
                data.get("assignedCapacity", {})
            ),
            unassigned_capacity=Capacity.from_dict(
                data.get("unassignedCapacity", {})
            ),
        )


@dataclass
class ListCapacitiesRequest:
    """Parameters for ListCapacities.

    Go reference: cloudwrapper.ListCapacitiesRequest (capacity.go)
    """

    contract_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "contractIds": list(self.contract_ids),
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListCapacitiesRequest:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            contract_ids=data.get("contractIds", []),
        )


@dataclass
class ListCapacitiesResponse:
    """Response from ListCapacities.

    Go reference: cloudwrapper.ListCapacitiesResponse (capacity.go)
    """

    capacities: list[LocationCapacity] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "capacities": [c.to_dict() for c in self.capacities],
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListCapacitiesResponse:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            capacities=[
                LocationCapacity.from_dict(c)
                for c in data.get("capacities", [])
            ],
        )


# ---------------------------------------------------------------------------
# Location models (locations.go)
# ---------------------------------------------------------------------------


@dataclass
class TrafficTypeItem:
    """TrafficType object for a location.

    Go reference: cloudwrapper.TrafficTypeItem (locations.go)
    map_name is str (NOT str | None — no pointer in Go).
    """

    traffic_type_id: int = 0
    traffic_type: str = ""
    map_name: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "trafficTypeId": self.traffic_type_id,
            "trafficType": self.traffic_type,
            "mapName": self.map_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TrafficTypeItem:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            traffic_type_id=data.get("trafficTypeId", 0),
            traffic_type=data.get("trafficType", ""),
            map_name=data.get("mapName", ""),
        )


@dataclass
class Location:
    """Location object.

    Go reference: cloudwrapper.Location (locations.go)
    """

    location_id: int = 0
    location_name: str = ""
    multi_cdn_location_id: str = ""
    traffic_types: list[TrafficTypeItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "locationId": self.location_id,
            "locationName": self.location_name,
            "multiCdnLocationId": self.multi_cdn_location_id,
            "trafficTypes": [
                t.to_dict() for t in self.traffic_types
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Location:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            location_id=data.get("locationId", 0),
            location_name=data.get("locationName", ""),
            multi_cdn_location_id=data.get(
                "multiCdnLocationId", ""
            ),
            traffic_types=[
                TrafficTypeItem.from_dict(t)
                for t in data.get("trafficTypes", [])
            ],
        )


@dataclass
class ListLocationResponse:
    """Response from ListLocations.

    Go reference: cloudwrapper.ListLocationResponse (locations.go)
    """

    locations: list[Location] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "locations": [loc.to_dict() for loc in self.locations],
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListLocationResponse:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            locations=[
                Location.from_dict(loc)
                for loc in data.get("locations", [])
            ],
        )


# ---------------------------------------------------------------------------
# Multi-CDN models (multi_cdn.go)
# ---------------------------------------------------------------------------


@dataclass
class MultiCDNAuthKey:
    """CDN auth key information from the multi-CDN endpoint.

    Go reference: cloudwrapper.MultiCDNAuthKey (multi_cdn.go)
    CRITICAL: Only 3 fields — NO secret field.
    This is DIFFERENT from CDNAuthKey (configurations.go) which has 4 fields.
    """

    auth_key_name: str = ""
    expiry_date: str = ""
    header_name: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "authKeyName": self.auth_key_name,
            "expiryDate": self.expiry_date,
            "headerName": self.header_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> MultiCDNAuthKey:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            auth_key_name=data.get("authKeyName", ""),
            expiry_date=data.get("expiryDate", ""),
            header_name=data.get("headerName", ""),
        )


@dataclass
class CDNProvider:
    """CDN provider information.

    Go reference: cloudwrapper.CDNProvider (multi_cdn.go)
    """

    cdn_code: str = ""
    cdn_name: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "cdnCode": self.cdn_code,
            "cdnName": self.cdn_name,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CDNProvider:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            cdn_code=data.get("cdnCode", ""),
            cdn_name=data.get("cdnName", ""),
        )


@dataclass
class ListAuthKeysRequest:
    """Parameters for ListAuthKeys.

    Go reference: cloudwrapper.ListAuthKeysRequest (multi_cdn.go)
    """

    contract_id: str = ""
    cdn_code: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "contractId": self.contract_id,
            "cdnCode": self.cdn_code,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListAuthKeysRequest:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            contract_id=data.get("contractId", ""),
            cdn_code=data.get("cdnCode", ""),
        )


@dataclass
class ListAuthKeysResponse:
    """Response from ListAuthKeys.

    Go reference: cloudwrapper.ListAuthKeysResponse (multi_cdn.go)
    """

    cdn_auth_keys: list[MultiCDNAuthKey] = field(
        default_factory=list
    )

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "cdnAuthKeys": [
                k.to_dict() for k in self.cdn_auth_keys
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListAuthKeysResponse:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            cdn_auth_keys=[
                MultiCDNAuthKey.from_dict(k)
                for k in data.get("cdnAuthKeys", [])
            ],
        )


@dataclass
class ListCDNProvidersResponse:
    """Response from ListCDNProviders.

    Go reference: cloudwrapper.ListCDNProvidersResponse (multi_cdn.go)
    """

    cdn_providers: list[CDNProvider] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict using Go JSON tag names."""
        return {
            "cdnProviders": [
                p.to_dict() for p in self.cdn_providers
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> ListCDNProvidersResponse:
        """Deserialize from dict using Go JSON tag names."""
        return cls(
            cdn_providers=[
                CDNProvider.from_dict(p)
                for p in data.get("cdnProviders", [])
            ],
        )
