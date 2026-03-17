# pylint: disable=too-many-instance-attributes,too-many-lines
"""Request and response models for the GTM (Global Traffic Management) API.

Defines all request/response model dataclasses for the Akamai Global Traffic
Management API, ported field-for-field from the Go v12 SDK structs defined
in the ``pkg/gtm`` package.  Every Go struct maps to a Python ``@dataclass``
with identical field names (using JSON tag names as canonical Python
attribute names), types mapped per the Go-to-Python type mapping table,
and required/optional semantics preserved.

Go reference files:
- pkg/gtm/common.go (ResponseStatus, DatacenterResponse, ResourceResponse,
  Link, LoadObject, DatacenterBase)
- pkg/gtm/domain.go (Domain, DomainItem, DomainsList, DomainQueryArgs,
  NullFieldMapStruct, NullPerObjectAttributeStruct, ObjectMap,
  and all domain request/response types)
- pkg/gtm/property.go (TrafficTarget, HTTPHeader, LivenessTest, StaticRRSet,
  Property, PropertyList, and all property request/response types)
- pkg/gtm/datacenter.go (Datacenter, DatacenterList, and all datacenter
  request/response types including default datacenter constants)
- pkg/gtm/resource.go (ResourceInstance, Resource, ResourceList, and all
  resource request/response types)
- pkg/gtm/asmap.go (ASAssignment, ASMap, ASMapList, and all AS map
  request/response types)
- pkg/gtm/geomap.go (GeoAssignment, GeoMap, GeoMapList, and all geo map
  request/response types)
- pkg/gtm/cidrmap.go (CIDRAssignment, CIDRMap, CIDRMapList, and all CIDR
  map request/response types)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Constants from datacenter.go
# ---------------------------------------------------------------------------

MAP_DEFAULT_DC = 5400
"""Default Datacenter ID for Maps. Mirrors Go MapDefaultDC constant."""

IPV4_DEFAULT_DC = 5401
"""Default Datacenter ID for IPv4. Mirrors Go Ipv4DefaultDC constant."""

IPV6_DEFAULT_DC = 5402
"""Default Datacenter ID for IPv6. Mirrors Go Ipv6DefaultDC constant."""


# ---------------------------------------------------------------------------
# Models from common.go
# ---------------------------------------------------------------------------


@dataclass
class Link:
    """Hyperlink within a GTM response payload.

    Mirrors Go pkg/gtm.Link struct.
    """

    rel: str = ""
    href: str = ""


@dataclass
class LoadObject:
    """Load object configuration for a datacenter or resource instance.

    Mirrors Go pkg/gtm.LoadObject struct.
    """

    load_object: str = ""
    load_object_port: int = 0
    load_servers: list[str] = field(default_factory=list)


@dataclass
class DatacenterBase:
    """Base datacenter fields shared by map assignments and default datacenter.

    Mirrors Go pkg/gtm.DatacenterBase struct.
    """

    nickname: str = ""
    datacenter_id: int = 0


@dataclass
class ResponseStatus:
    """Status information returned by GTM API mutations.

    Mirrors Go pkg/gtm.ResponseStatus struct.
    """

    change_id: str = ""
    links: list[Link] = field(default_factory=list)
    message: str = ""
    passing_validation: bool = False
    propagation_status: str = ""
    propagation_status_date: str = ""


# ---------------------------------------------------------------------------
# Models from property.go
# ---------------------------------------------------------------------------


@dataclass
class TrafficTarget:
    """Traffic target directing traffic to a specific datacenter.

    Mirrors Go pkg/gtm.TrafficTarget struct.
    """

    datacenter_id: int = 0
    enabled: bool = False
    weight: float = 0.0
    servers: list[str] = field(default_factory=list)
    name: str = ""
    handout_c_name: str = ""
    precedence: int | None = None


@dataclass
class HTTPHeader:
    """HTTP header sent during liveness tests.

    Mirrors Go pkg/gtm.HTTPHeader struct.
    """

    name: str = ""
    value: str = ""


@dataclass
class LivenessTest:
    """Liveness test configuration for GTM property health checks.

    Mirrors Go pkg/gtm.LivenessTest struct.
    """

    name: str = ""
    error_penalty: float = 0.0
    peer_certificate_verification: bool = False
    test_interval: int = 0
    test_object: str = ""
    links: list[Link] = field(default_factory=list)
    request_string: str = ""
    response_string: str = ""
    http_error3xx: bool = False
    http_error4xx: bool = False
    http_error5xx: bool = False
    http_method: str | None = None
    http_request_body: str | None = None
    disabled: bool = False
    test_object_protocol: str = ""
    test_object_password: str = ""
    test_object_port: int = 0
    ssl_client_private_key: str = ""
    ssl_client_certificate: str = ""
    pre2023_security_posture: bool = False
    disable_nonstandard_port_warning: bool = False
    http_headers: list[HTTPHeader] = field(default_factory=list)
    test_object_username: str = ""
    test_timeout: float = 0.0
    timeout_penalty: float = 0.0
    answers_required: bool = False
    resource_type: str = ""
    recursion_requested: bool = False
    alternate_ca_certificates: list[str] = field(default_factory=list)


@dataclass
class StaticRRSet:
    """Static DNS resource record set.

    Mirrors Go pkg/gtm.StaticRRSet struct.
    """

    type: str = ""
    ttl: int = 0
    rdata: list[str] = field(default_factory=list)


@dataclass
class Property:
    """GTM property configuration.

    Mirrors Go pkg/gtm.Property struct.
    """

    name: str = ""
    type: str = ""
    ipv6: bool = False
    score_aggregation_type: str = ""
    stickiness_bonus_percentage: int = 0
    stickiness_bonus_constant: int = 0
    health_threshold: float = 0.0
    use_computed_targets: bool = False
    backup_ip: str = ""
    balance_by_download_score: bool = False
    static_ttl: int = 0
    static_rr_sets: list[StaticRRSet] = field(default_factory=list)
    last_modified: str = ""
    unreachable_threshold: float = 0.0
    min_live_fraction: float = 0.0
    health_multiplier: float = 0.0
    dynamic_ttl: int = 0
    max_unreachable_penalty: int = 0
    map_name: str = ""
    handout_limit: int = 0
    handout_mode: str = ""
    failover_delay: int = 0
    backup_c_name: str = ""
    failback_delay: int = 0
    load_imbalance_percentage: float = 0.0
    health_max: float = 0.0
    ghost_demand_reporting: bool = False
    comments: str = ""
    cname: str = ""
    weighted_hash_bits_for_ipv4: int = 0
    weighted_hash_bits_for_ipv6: int = 0
    traffic_targets: list[TrafficTarget] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    liveness_tests: list[LivenessTest] = field(default_factory=list)


@dataclass
class PropertyList:
    """List of GTM properties.

    Mirrors Go pkg/gtm.PropertyList struct.
    """

    items: list[Property] = field(default_factory=list)


@dataclass
class PropertyRequest:
    """Base request parameters for property create/update/delete operations.

    Mirrors Go pkg/gtm.PropertyRequest struct.
    """

    property: Property | None = None
    domain_name: str = ""


@dataclass
class GetPropertyRequest:
    """Request parameters for GetProperty.

    Mirrors Go pkg/gtm.GetPropertyRequest struct.
    """

    domain_name: str = ""
    property_name: str = ""


# GetPropertyResponse is a type alias for Property in Go.
GetPropertyResponse = Property
"""Alias for ``Property``. Mirrors Go type alias."""


@dataclass
class ListPropertiesRequest:
    """Request parameters for ListProperties.

    Mirrors Go pkg/gtm.ListPropertiesRequest struct.
    """

    domain_name: str = ""


# CreatePropertyRequest is a type alias for PropertyRequest in Go.
CreatePropertyRequest = PropertyRequest
"""Alias for ``PropertyRequest``. Mirrors Go type alias."""


@dataclass
class CreatePropertyResponse:
    """Response from CreateProperty operation.

    Mirrors Go pkg/gtm.CreatePropertyResponse struct.
    """

    resource: Property | None = None
    status: ResponseStatus | None = None


# UpdatePropertyRequest is a type alias for PropertyRequest in Go.
UpdatePropertyRequest = PropertyRequest
"""Alias for ``PropertyRequest``. Mirrors Go type alias."""


@dataclass
class UpdatePropertyResponse:
    """Response from UpdateProperty operation.

    Mirrors Go pkg/gtm.UpdatePropertyResponse struct.
    """

    resource: Property | None = None
    status: ResponseStatus | None = None


@dataclass
class DeletePropertyRequest:
    """Request parameters for DeleteProperty.

    Mirrors Go pkg/gtm.DeletePropertyRequest struct.
    """

    domain_name: str = ""
    property_name: str = ""


@dataclass
class DeletePropertyResponse:
    """Response from DeleteProperty operation.

    Mirrors Go pkg/gtm.DeletePropertyResponse struct.
    """

    resource: Property | None = None
    status: ResponseStatus | None = None


# ---------------------------------------------------------------------------
# Models from datacenter.go
# ---------------------------------------------------------------------------


@dataclass
class Datacenter:
    """GTM datacenter configuration.

    Mirrors Go pkg/gtm.Datacenter struct.
    """

    city: str = ""
    clone_of: int = 0
    cloud_server_host_header_override: bool = False
    cloud_server_targeting: bool = False
    continent: str = ""
    country: str = ""
    default_load_object: LoadObject | None = None
    latitude: float = 0.0
    links: list[Link] = field(default_factory=list)
    longitude: float = 0.0
    nickname: str = ""
    ping_interval: int = 0
    ping_packet_size: int = 0
    datacenter_id: int = 0
    score_penalty: int = 0
    servermonitor_liveness_count: int = 0
    servermonitor_load_count: int = 0
    servermonitor_pool: str = ""
    state_or_province: str = ""
    virtual: bool = False


@dataclass
class DatacenterList:
    """List of GTM datacenters.

    Mirrors Go pkg/gtm.DatacenterList struct.
    """

    items: list[Datacenter] = field(default_factory=list)


@dataclass
class ListDatacentersRequest:
    """Request parameters for ListDatacenters.

    Mirrors Go pkg/gtm.ListDatacentersRequest struct.
    """

    domain_name: str = ""


@dataclass
class GetDatacenterRequest:
    """Request parameters for GetDatacenter.

    Mirrors Go pkg/gtm.GetDatacenterRequest struct.
    """

    datacenter_id: int = 0
    domain_name: str = ""


@dataclass
class DatacenterRequest:
    """Base request parameters for datacenter create/update operations.

    Mirrors Go pkg/gtm.DatacenterRequest struct.
    """

    datacenter: Datacenter | None = None
    domain_name: str = ""


# CreateDatacenterRequest is a type alias for DatacenterRequest in Go.
CreateDatacenterRequest = DatacenterRequest
"""Alias for ``DatacenterRequest``. Mirrors Go type alias."""


@dataclass
class CreateDatacenterResponse:
    """Response from CreateDatacenter operation.

    Mirrors Go pkg/gtm.CreateDatacenterResponse struct.
    """

    status: ResponseStatus | None = None
    resource: Datacenter | None = None


# UpdateDatacenterRequest is a type alias for DatacenterRequest in Go.
UpdateDatacenterRequest = DatacenterRequest
"""Alias for ``DatacenterRequest``. Mirrors Go type alias."""


@dataclass
class UpdateDatacenterResponse:
    """Response from UpdateDatacenter operation.

    Mirrors Go pkg/gtm.UpdateDatacenterResponse struct.
    """

    status: ResponseStatus | None = None
    resource: Datacenter | None = None


@dataclass
class DeleteDatacenterRequest:
    """Request parameters for DeleteDatacenter.

    Mirrors Go pkg/gtm.DeleteDatacenterRequest struct.
    """

    datacenter_id: int = 0
    domain_name: str = ""


@dataclass
class DeleteDatacenterResponse:
    """Response from DeleteDatacenter operation.

    Mirrors Go pkg/gtm.DeleteDatacenterResponse struct.
    """

    status: ResponseStatus | None = None
    resource: Datacenter | None = None


# ---------------------------------------------------------------------------
# Models from resource.go
# ---------------------------------------------------------------------------


@dataclass
class ResourceInstance:
    """Resource instance within a datacenter.

    Mirrors Go pkg/gtm.ResourceInstance struct.
    The Go struct embeds LoadObject; here the LoadObject fields are
    flattened into this dataclass.
    """

    datacenter_id: int = 0
    use_default_load_object: bool = False
    load_object: str = ""
    load_object_port: int = 0
    load_servers: list[str] = field(default_factory=list)


@dataclass
class Resource:
    """GTM resource configuration.

    Mirrors Go pkg/gtm.Resource struct.
    """

    type: str = ""
    host_header: str = ""
    least_squares_decay: float = 0.0
    description: str = ""
    leader_string: str = ""
    constrained_property: str = ""
    resource_instances: list[ResourceInstance] = field(default_factory=list)
    aggregation_type: str = ""
    links: list[Link] = field(default_factory=list)
    load_imbalance_percentage: float = 0.0
    upper_bound: int = 0
    name: str = ""
    max_u_multiplicative_increment: float = 0.0
    decay_rate: float = 0.0


@dataclass
class ResourceList:
    """List of GTM resources.

    Mirrors Go pkg/gtm.ResourceList struct.
    """

    items: list[Resource] = field(default_factory=list)


@dataclass
class ListResourcesRequest:
    """Request parameters for ListResources.

    Mirrors Go pkg/gtm.ListResourcesRequest struct.
    """

    domain_name: str = ""


@dataclass
class GetResourceRequest:
    """Request parameters for GetResource.

    Mirrors Go pkg/gtm.GetResourceRequest struct.
    """

    domain_name: str = ""
    resource_name: str = ""


# GetResourceResponse is a type alias for Resource in Go.
GetResourceResponse = Resource
"""Alias for ``Resource``. Mirrors Go type alias."""


@dataclass
class ResourceRequest:
    """Base request parameters for resource create/update operations.

    Mirrors Go pkg/gtm.ResourceRequest struct.
    """

    resource: Resource | None = None
    domain_name: str = ""


# CreateResourceRequest is a type alias for ResourceRequest in Go.
CreateResourceRequest = ResourceRequest
"""Alias for ``ResourceRequest``. Mirrors Go type alias."""


@dataclass
class CreateResourceResponse:
    """Response from CreateResource operation.

    Mirrors Go pkg/gtm.CreateResourceResponse struct.
    """

    resource: Resource | None = None
    status: ResponseStatus | None = None


# UpdateResourceRequest is a type alias for ResourceRequest in Go.
UpdateResourceRequest = ResourceRequest
"""Alias for ``ResourceRequest``. Mirrors Go type alias."""


@dataclass
class UpdateResourceResponse:
    """Response from UpdateResource operation.

    Mirrors Go pkg/gtm.UpdateResourceResponse struct.
    """

    resource: Resource | None = None
    status: ResponseStatus | None = None


@dataclass
class DeleteResourceRequest:
    """Request parameters for DeleteResource.

    Mirrors Go pkg/gtm.DeleteResourceRequest struct.
    """

    domain_name: str = ""
    resource_name: str = ""


@dataclass
class DeleteResourceResponse:
    """Response from DeleteResource operation.

    Mirrors Go pkg/gtm.DeleteResourceResponse struct.
    """

    resource: Resource | None = None
    status: ResponseStatus | None = None


# ---------------------------------------------------------------------------
# Models from asmap.go
# ---------------------------------------------------------------------------


@dataclass
class ASAssignment:
    """AS number assignment within an AS map.

    Mirrors Go pkg/gtm.ASAssignment struct.
    The Go struct embeds DatacenterBase; here the DatacenterBase
    fields are flattened into this dataclass.
    """

    nickname: str = ""
    datacenter_id: int = 0
    as_numbers: list[int] = field(default_factory=list)


@dataclass
class ASMap:
    """GTM AS (Autonomous System) map configuration.

    Mirrors Go pkg/gtm.ASMap struct.
    """

    default_datacenter: DatacenterBase | None = None
    assignments: list[ASAssignment] = field(default_factory=list)
    name: str = ""
    links: list[Link] = field(default_factory=list)


@dataclass
class ASMapList:
    """List of GTM AS maps.

    Mirrors Go pkg/gtm.ASMapList struct.
    """

    items: list[ASMap] = field(default_factory=list)


@dataclass
class ListASMapsRequest:
    """Request parameters for ListASMaps.

    Mirrors Go pkg/gtm.ListASMapsRequest struct.
    """

    domain_name: str = ""


@dataclass
class GetASMapRequest:
    """Request parameters for GetASMap.

    Mirrors Go pkg/gtm.GetASMapRequest struct.
    """

    as_map_name: str = ""
    domain_name: str = ""


# GetASMapResponse is a type alias for ASMap in Go.
GetASMapResponse = ASMap
"""Alias for ``ASMap``. Mirrors Go type alias."""


@dataclass
class ASMapRequest:
    """Base request parameters for AS map create/update operations.

    Mirrors Go pkg/gtm.ASMapRequest struct.
    """

    as_map: ASMap | None = None
    domain_name: str = ""


# CreateASMapRequest is a type alias for ASMapRequest in Go.
CreateASMapRequest = ASMapRequest
"""Alias for ``ASMapRequest``. Mirrors Go type alias."""


@dataclass
class CreateASMapResponse:
    """Response from CreateASMap operation.

    Mirrors Go pkg/gtm.CreateASMapResponse struct.
    """

    resource: ASMap | None = None
    status: ResponseStatus | None = None


# UpdateASMapRequest is a type alias for ASMapRequest in Go.
UpdateASMapRequest = ASMapRequest
"""Alias for ``ASMapRequest``. Mirrors Go type alias."""


@dataclass
class UpdateASMapResponse:
    """Response from UpdateASMap operation.

    Mirrors Go pkg/gtm.UpdateASMapResponse struct.
    """

    resource: ASMap | None = None
    status: ResponseStatus | None = None


@dataclass
class DeleteASMapRequest:
    """Request parameters for DeleteASMap.

    Mirrors Go pkg/gtm.DeleteASMapRequest struct.
    """

    as_map_name: str = ""
    domain_name: str = ""


@dataclass
class DeleteASMapResponse:
    """Response from DeleteASMap operation.

    Mirrors Go pkg/gtm.DeleteASMapResponse struct.
    """

    resource: ASMap | None = None
    status: ResponseStatus | None = None


# ---------------------------------------------------------------------------
# Models from geomap.go
# ---------------------------------------------------------------------------


@dataclass
class GeoAssignment:
    """Geographic assignment within a geo map.

    Mirrors Go pkg/gtm.GeoAssignment struct.
    The Go struct embeds DatacenterBase; here the DatacenterBase
    fields are flattened into this dataclass.
    """

    nickname: str = ""
    datacenter_id: int = 0
    countries: list[str] = field(default_factory=list)


@dataclass
class GeoMap:
    """GTM geographic map configuration.

    Mirrors Go pkg/gtm.GeoMap struct.
    """

    default_datacenter: DatacenterBase | None = None
    assignments: list[GeoAssignment] = field(default_factory=list)
    name: str = ""
    links: list[Link] = field(default_factory=list)


@dataclass
class GeoMapList:
    """List of GTM geographic maps.

    Mirrors Go pkg/gtm.GeoMapList struct.
    """

    items: list[GeoMap] = field(default_factory=list)


@dataclass
class ListGeoMapsRequest:
    """Request parameters for ListGeoMaps.

    Mirrors Go pkg/gtm.ListGeoMapsRequest struct.
    """

    domain_name: str = ""


@dataclass
class GetGeoMapRequest:
    """Request parameters for GetGeoMap.

    Mirrors Go pkg/gtm.GetGeoMapRequest struct.
    """

    map_name: str = ""
    domain_name: str = ""


# GetGeoMapResponse is a type alias for GeoMap in Go.
GetGeoMapResponse = GeoMap
"""Alias for ``GeoMap``. Mirrors Go type alias."""


@dataclass
class GeoMapRequest:
    """Base request parameters for geo map create/update operations.

    Mirrors Go pkg/gtm.GeoMapRequest struct.
    """

    geo_map: GeoMap | None = None
    domain_name: str = ""


# CreateGeoMapRequest is a type alias for GeoMapRequest in Go.
CreateGeoMapRequest = GeoMapRequest
"""Alias for ``GeoMapRequest``. Mirrors Go type alias."""


@dataclass
class CreateGeoMapResponse:
    """Response from CreateGeoMap operation.

    Mirrors Go pkg/gtm.CreateGeoMapResponse struct.
    """

    resource: GeoMap | None = None
    status: ResponseStatus | None = None


# UpdateGeoMapRequest is a type alias for GeoMapRequest in Go.
UpdateGeoMapRequest = GeoMapRequest
"""Alias for ``GeoMapRequest``. Mirrors Go type alias."""


@dataclass
class UpdateGeoMapResponse:
    """Response from UpdateGeoMap operation.

    Mirrors Go pkg/gtm.UpdateGeoMapResponse struct.
    """

    resource: GeoMap | None = None
    status: ResponseStatus | None = None


@dataclass
class DeleteGeoMapRequest:
    """Request parameters for DeleteGeoMap.

    Mirrors Go pkg/gtm.DeleteGeoMapRequest struct.
    """

    map_name: str = ""
    domain_name: str = ""


@dataclass
class DeleteGeoMapResponse:
    """Response from DeleteGeoMap operation.

    Mirrors Go pkg/gtm.DeleteGeoMapResponse struct.
    """

    resource: GeoMap | None = None
    status: ResponseStatus | None = None


# ---------------------------------------------------------------------------
# Models from cidrmap.go
# ---------------------------------------------------------------------------


@dataclass
class CIDRAssignment:
    """CIDR block assignment within a CIDR map.

    Mirrors Go pkg/gtm.CIDRAssignment struct.
    The Go struct embeds DatacenterBase; here the DatacenterBase
    fields are flattened into this dataclass.
    """

    nickname: str = ""
    datacenter_id: int = 0
    blocks: list[str] = field(default_factory=list)


@dataclass
class CIDRMap:
    """GTM CIDR map configuration.

    Mirrors Go pkg/gtm.CIDRMap struct.
    """

    default_datacenter: DatacenterBase | None = None
    assignments: list[CIDRAssignment] = field(default_factory=list)
    name: str = ""
    links: list[Link] = field(default_factory=list)


@dataclass
class CIDRMapList:
    """List of GTM CIDR maps.

    Mirrors Go pkg/gtm.CIDRMapList struct.
    """

    items: list[CIDRMap] = field(default_factory=list)


@dataclass
class ListCIDRMapsRequest:
    """Request parameters for ListCIDRMaps.

    Mirrors Go pkg/gtm.ListCIDRMapsRequest struct.
    """

    domain_name: str = ""


@dataclass
class GetCIDRMapRequest:
    """Request parameters for GetCIDRMap.

    Mirrors Go pkg/gtm.GetCIDRMapRequest struct.
    """

    map_name: str = ""
    domain_name: str = ""


# GetCIDRMapResponse is a type alias for CIDRMap in Go.
GetCIDRMapResponse = CIDRMap
"""Alias for ``CIDRMap``. Mirrors Go type alias."""


@dataclass
class CIDRMapRequest:
    """Base request parameters for CIDR map create/update operations.

    Mirrors Go pkg/gtm.CIDRMapRequest struct.
    """

    cidr: CIDRMap | None = None
    domain_name: str = ""


# CreateCIDRMapRequest is a type alias for CIDRMapRequest in Go.
CreateCIDRMapRequest = CIDRMapRequest
"""Alias for ``CIDRMapRequest``. Mirrors Go type alias."""


@dataclass
class CreateCIDRMapResponse:
    """Response from CreateCIDRMap operation.

    Mirrors Go pkg/gtm.CreateCIDRMapResponse struct.
    """

    resource: CIDRMap | None = None
    status: ResponseStatus | None = None


# UpdateCIDRMapRequest is a type alias for CIDRMapRequest in Go.
UpdateCIDRMapRequest = CIDRMapRequest
"""Alias for ``CIDRMapRequest``. Mirrors Go type alias."""


@dataclass
class UpdateCIDRMapResponse:
    """Response from UpdateCIDRMap operation.

    Mirrors Go pkg/gtm.UpdateCIDRMapResponse struct.
    """

    resource: CIDRMap | None = None
    status: ResponseStatus | None = None


@dataclass
class DeleteCIDRMapRequest:
    """Request parameters for DeleteCIDRMap.

    Mirrors Go pkg/gtm.DeleteCIDRMapRequest struct.
    """

    map_name: str = ""
    domain_name: str = ""


@dataclass
class DeleteCIDRMapResponse:
    """Response from DeleteCIDRMap operation.

    Mirrors Go pkg/gtm.DeleteCIDRMapResponse struct.
    """

    resource: CIDRMap | None = None
    status: ResponseStatus | None = None


# ---------------------------------------------------------------------------
# Models from domain.go
# ---------------------------------------------------------------------------


@dataclass
class Domain:
    """GTM domain configuration.

    Mirrors Go pkg/gtm.Domain struct.
    """

    name: str = ""
    type: str = ""
    as_maps: list[ASMap] = field(default_factory=list)
    resources: list[Resource] = field(default_factory=list)
    default_unreachable_threshold: float = 0.0
    email_notification_list: list[str] = field(default_factory=list)
    min_pingable_region_fraction: float = 0.0
    default_timeout_penalty: int = 0
    datacenters: list[Datacenter] = field(default_factory=list)
    servermonitor_liveness_count: int = 0
    round_robin_prefix: str = ""
    servermonitor_load_count: int = 0
    ping_interval: int = 0
    max_ttl: int = 0
    load_imbalance_percentage: float = 0.0
    default_health_max: float = 0.0
    last_modified: str = ""
    status: ResponseStatus | None = None
    map_update_interval: int = 0
    max_properties: int = 0
    max_resources: int = 0
    default_ssl_client_private_key: str = ""
    default_error_penalty: int = 0
    links: list[Link] = field(default_factory=list)
    properties: list[Property] = field(default_factory=list)
    max_test_timeout: float = 0.0
    cname_coalescing_enabled: bool = False
    default_health_multiplier: float = 0.0
    servermonitor_pool: str = ""
    load_feedback: bool = False
    min_ttl: int = 0
    geographic_maps: list[GeoMap] = field(default_factory=list)
    cidr_maps: list[CIDRMap] = field(default_factory=list)
    default_max_unreachable_penalty: int = 0
    default_health_threshold: float = 0.0
    last_modified_by: str = ""
    modification_comments: str = ""
    min_test_interval: int = 0
    ping_packet_size: int = 0
    default_ssl_client_certificate: str = ""
    end_user_mapping_enabled: bool = False
    sign_and_serve: bool = False
    sign_and_serve_algorithm: str | None = None


@dataclass
class DomainQueryArgs:
    """Query parameters for domain requests.

    Mirrors Go pkg/gtm.DomainQueryArgs struct.
    These fields are not serialized to JSON; they are used to
    construct query string parameters on the request URL.
    """

    contract_id: str = ""
    group_id: str = ""


@dataclass
class DomainsList:
    """List of GTM domain summary items.

    Mirrors Go pkg/gtm.DomainsList struct.
    """

    items: list[DomainItem] = field(default_factory=list)


@dataclass
class DomainItem:
    """Summary item for a single GTM domain in a list response.

    Mirrors Go pkg/gtm.DomainItem struct.
    """

    acg_id: str = ""
    last_modified: str = ""
    links: list[Link] = field(default_factory=list)
    name: str = ""
    status: str = ""
    last_modified_by: str = ""
    change_id: str = ""
    activation_state: str = ""
    modification_comments: str = ""
    sign_and_serve: bool = False
    sign_and_serve_algorithm: str = ""
    delete_request_id: str = ""


@dataclass
class GetDomainStatusRequest:
    """Request parameters for GetDomainStatus.

    Mirrors Go pkg/gtm.GetDomainStatusRequest struct.
    """

    domain_name: str = ""


# GetDomainStatusResponse is a type alias for ResponseStatus in Go.
GetDomainStatusResponse = ResponseStatus
"""Alias for ``ResponseStatus``. Mirrors Go type alias."""


@dataclass
class DomainRequest:
    """Base request parameters for domain create/update operations.

    Mirrors Go pkg/gtm.DomainRequest struct.
    """

    domain: Domain | None = None
    query_args: DomainQueryArgs | None = None


@dataclass
class GetDomainRequest:
    """Request parameters for GetDomain.

    Mirrors Go pkg/gtm.GetDomainRequest struct.
    """

    domain_name: str = ""


# GetDomainResponse is a type alias for Domain in Go.
GetDomainResponse = Domain
"""Alias for ``Domain``. Mirrors Go type alias."""


# CreateDomainRequest is a type alias for DomainRequest in Go.
CreateDomainRequest = DomainRequest
"""Alias for ``DomainRequest``. Mirrors Go type alias."""


@dataclass
class CreateDomainResponse:
    """Response from CreateDomain operation.

    Mirrors Go pkg/gtm.CreateDomainResponse struct.
    """

    resource: Domain | None = None
    status: ResponseStatus | None = None


# UpdateDomainRequest is a type alias for DomainRequest in Go.
UpdateDomainRequest = DomainRequest
"""Alias for ``DomainRequest``. Mirrors Go type alias."""


@dataclass
class UpdateDomainResponse:
    """Response from UpdateDomain operation.

    Mirrors Go pkg/gtm.UpdateDomainResponse struct.
    """

    resource: Domain | None = None
    status: ResponseStatus | None = None


@dataclass
class DeleteDomainRequest:
    """Request parameters for DeleteDomain.

    Mirrors Go pkg/gtm.DeleteDomainRequest struct.

    .. deprecated::
        DeleteDomainRequest is deprecated and may be removed in future
        versions. Use DeleteDomainsRequest instead.
    """

    domain_name: str = ""


@dataclass
class DeleteDomainResponse:
    """Response from DeleteDomain operation.

    Mirrors Go pkg/gtm.DeleteDomainResponse struct.

    .. deprecated::
        DeleteDomainResponse is deprecated and may be removed in future
        versions. Use DeleteDomainsResponse instead.
    """

    change_id: str = ""
    links: list[Link] = field(default_factory=list)
    message: str = ""
    passing_validation: bool = False
    propagation_status: str = ""
    propagation_status_date: str = ""


@dataclass
class DeleteDomainsRequest:
    """Request to delete multiple GTM domains.

    Mirrors Go pkg/gtm.DeleteDomainsRequest struct.
    """

    bypass_safety_checks: bool | None = None
    body: DeleteDomainsRequestBody | None = None


@dataclass
class DeleteDomainsRequestBody:
    """Request body for DeleteDomainsRequest.

    Mirrors Go pkg/gtm.DeleteDomainsRequestBody struct.
    """

    domain_names: list[str] = field(default_factory=list)


@dataclass
class DeleteDomainsResponse:
    """Response from DeleteDomains operation.

    Mirrors Go pkg/gtm.DeleteDomainsResponse struct.
    """

    expiration_date: str = ""
    request_id: str = ""


@dataclass
class DeleteDomainsStatusRequest:
    """Request to retrieve status of a delete domains operation.

    Mirrors Go pkg/gtm.DeleteDomainsStatusRequest struct.
    """

    request_id: str = ""


@dataclass
class DeleteDomainsStatusResponse:
    """Response containing status of a delete domains operation.

    Mirrors Go pkg/gtm.DeleteDomainsStatusResponse struct.
    """

    domains_submitted: int = 0
    expiration_date: str = ""
    failure_count: int = 0
    is_complete: bool = False
    request_id: str = ""
    success_count: int = 0


# ---------------------------------------------------------------------------
# Null field map models from domain.go
# ---------------------------------------------------------------------------


@dataclass
class NullPerObjectAttributeStruct:
    """Attribute structure used by NullFieldMap for tracking null-able fields.

    Mirrors Go pkg/gtm.NullPerObjectAttributeStruct struct.
    """

    core_object_fields: dict[str, str] = field(default_factory=dict)
    child_object_fields: dict[str, Any] = field(default_factory=dict)


@dataclass
class NullFieldMapStruct:
    """Map of null-able fields across all GTM object types.

    Mirrors Go pkg/gtm.NullFieldMapStruct struct.
    Used by the NullFieldMap operation to identify which fields
    are set to null in the domain configuration.
    """

    domain: NullPerObjectAttributeStruct = field(
        default_factory=NullPerObjectAttributeStruct
    )
    properties: dict[str, NullPerObjectAttributeStruct] = field(
        default_factory=dict
    )
    datacenters: dict[str, NullPerObjectAttributeStruct] = field(
        default_factory=dict
    )
    resources: dict[str, NullPerObjectAttributeStruct] = field(
        default_factory=dict
    )
    cidr_maps: dict[str, NullPerObjectAttributeStruct] = field(
        default_factory=dict
    )
    geo_maps: dict[str, NullPerObjectAttributeStruct] = field(
        default_factory=dict
    )
    as_maps: dict[str, NullPerObjectAttributeStruct] = field(
        default_factory=dict
    )


# ObjectMap is a type alias for dict in Go (map[string]interface{}).
ObjectMap = dict
"""Alias for ``dict``. Mirrors Go ``ObjectMap`` type alias."""


# ---------------------------------------------------------------------------
# Composite response models from common.go
# ---------------------------------------------------------------------------


@dataclass
class DatacenterResponse:
    """Response containing a single datacenter with status.

    Mirrors Go pkg/gtm.DatacenterResponse struct.
    """

    status: ResponseStatus | None = None
    resource: Datacenter | None = None


@dataclass
class ResourceResponse:
    """Response containing a single resource with status.

    Mirrors Go pkg/gtm.ResourceResponse struct.
    """

    resource: Resource | None = None
    status: ResponseStatus | None = None
