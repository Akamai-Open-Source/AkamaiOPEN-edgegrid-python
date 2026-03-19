# pylint: disable=too-many-instance-attributes,too-many-lines,redefined-builtin
"""Request and response models for Edge DNS API.

This module contains all request/response model dataclasses for the Akamai
Edge DNS API, ported field-for-field from the Go v12 SDK structs defined in
the ``pkg/dns`` package.  Every Go struct maps to a Python ``@dataclass``
with identical field names (using JSON tag names as canonical Python
attribute names), types mapped per the Go-to-Python type mapping table,
and required/optional semantics preserved.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Models from authorities.go
# ---------------------------------------------------------------------------


@dataclass
class Contract:
    """Maps to Go dns.Contract.

    Contains a contract ID and a list of currently assigned Akamai
    authoritative nameservers.
    """

    contract_id: str = ""
    authorities: list[str] = field(default_factory=list)


@dataclass
class AuthorityResponse:
    """Maps to Go dns.AuthorityResponse.

    Contains a response with a list of one or more Contracts.
    """

    contracts: list[Contract] = field(default_factory=list)


@dataclass
class GetAuthoritiesRequest:
    """Maps to Go dns.GetAuthoritiesRequest.

    Contains request parameters for GetAuthorities.
    """

    contract_ids: str = ""


@dataclass
class GetAuthoritiesResponse:
    """Maps to Go dns.GetAuthoritiesResponse.

    Contains the response data from GetAuthorities operation.
    """

    contracts: list[Contract] = field(default_factory=list)


@dataclass
class GetNameServerRecordListRequest:
    """Maps to Go dns.GetNameServerRecordListRequest.

    Contains request parameters for GetNameServerRecordList.
    """

    contract_ids: str = ""


# ---------------------------------------------------------------------------
# Models from data.go
# ---------------------------------------------------------------------------


@dataclass
class Group:
    """Maps to Go dns.Group.

    Contains the information of a particular group.
    """

    group_id: int = 0
    group_name: str = ""
    contract_ids: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)


@dataclass
class ListGroupRequest:
    """Maps to Go dns.ListGroupRequest.

    Contains request parameters for ListGroups.
    """

    group_id: str = ""


@dataclass
class ListGroupResponse:
    """Maps to Go dns.ListGroupResponse.

    Lists the groups accessible to the current user.
    """

    groups: list[Group] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Models from record.go
# ---------------------------------------------------------------------------


@dataclass
class RecordBody:
    """Maps to Go dns.RecordBody.

    Contains request body for a DNS record.
    """

    name: str = ""
    record_type: str = ""
    ttl: int = 0
    active: bool = False
    target: list[str] = field(default_factory=list)


@dataclass
class CreateRecordRequest:
    """Maps to Go dns.CreateRecordRequest (alias for RecordRequest).

    Contains request parameters for CreateRecord.
    """

    record: RecordBody | None = None
    zone: str = ""
    rec_lock: list[bool] = field(default_factory=list)


@dataclass
class UpdateRecordRequest:
    """Maps to Go dns.UpdateRecordRequest (alias for RecordRequest).

    Contains request parameters for UpdateRecord.
    """

    record: RecordBody | None = None
    zone: str = ""
    rec_lock: list[bool] = field(default_factory=list)


@dataclass
class DeleteRecordRequest:
    """Maps to Go dns.DeleteRecordRequest.

    Contains request parameters for DeleteRecord.
    """

    zone: str = ""
    name: str = ""
    record_type: str = ""
    rec_lock: list[bool] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Models from record_lookup.go
# ---------------------------------------------------------------------------


@dataclass
class GetRecordRequest:
    """Maps to Go dns.GetRecordRequest (alias for RdataRequest).

    Contains request parameters for GetRecord.
    """

    zone: str = ""
    name: str = ""
    record_type: str = ""


@dataclass
class GetRecordResponse:
    """Maps to Go dns.GetRecordResponse.

    Contains the response data from GetRecord operation.
    """

    name: str = ""
    record_type: str = ""
    ttl: int = 0
    active: bool = False
    target: list[str] = field(default_factory=list)


@dataclass
class GetRecordListRequest:
    """Maps to Go dns.GetRecordListRequest.

    Contains request parameters for GetRecordList.
    """

    zone: str = ""
    record_type: str = ""


@dataclass
class GetRecordListResponse:
    """Maps to Go dns.GetRecordListResponse.

    Contains the response data from GetRecordList operation.
    """

    metadata: Metadata | None = None
    record_sets: list[RecordSet] = field(default_factory=list)


@dataclass
class GetRdataRequest:
    """Maps to Go dns.GetRdataRequest (alias for RdataRequest).

    Contains request parameters for GetRdata.
    """

    zone: str = ""
    name: str = ""
    record_type: str = ""


# ---------------------------------------------------------------------------
# Models from recordsets.go
# ---------------------------------------------------------------------------


@dataclass
class RecordSetQueryArgs:
    """Maps to Go dns.RecordSetQueryArgs.

    Contains query parameters for recordset request.
    """

    page: int = 0
    page_size: int = 0
    search: str = ""
    show_all: bool = False
    sort_by: str = ""
    types: str = ""


@dataclass
class RecordSet:
    """Maps to Go dns.RecordSet.

    Contains record set metadata.
    """

    name: str = ""
    type: str = ""
    ttl: int = 0
    rdata: list[str] = field(default_factory=list)


@dataclass
class RecordSets:
    """Maps to Go dns.RecordSets.

    Used for Create and Update record sets.  Contains a list of
    RecordSet objects.
    """

    record_sets: list[RecordSet] = field(default_factory=list)


@dataclass
class Metadata:
    """Maps to Go dns.Metadata.

    Contains metadata of RecordSet response.
    """

    last_page: int = 0
    page: int = 0
    page_size: int = 0
    show_all: bool = False
    total_elements: int = 0


@dataclass
class GetRecordSetsRequest:
    """Maps to Go dns.GetRecordSetsRequest.

    Contains request parameters for GetRecordSets.
    """

    zone: str = ""
    query_args: RecordSetQueryArgs | None = None


@dataclass
class GetRecordSetsResponse:
    """Maps to Go dns.GetRecordSetsResponse.

    Contains the response data from GetRecordSets operation.
    """

    metadata: Metadata | None = None
    record_sets: list[RecordSet] = field(default_factory=list)


@dataclass
class CreateRecordSetsRequest:
    """Maps to Go dns.CreateRecordSetsRequest (alias for RecordSetsRequest).

    Contains request parameters for CreateRecordSets.
    """

    record_sets: RecordSets | None = None
    zone: str = ""
    rec_lock: list[bool] = field(default_factory=list)


@dataclass
class UpdateRecordSetsRequest:
    """Maps to Go dns.UpdateRecordSetsRequest (alias for RecordSetsRequest).

    Contains request parameters for UpdateRecordSets.
    """

    record_sets: RecordSets | None = None
    zone: str = ""
    rec_lock: list[bool] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Models from tsig.go
# ---------------------------------------------------------------------------


@dataclass
class TSIGQueryString:
    """Maps to Go dns.TSIGQueryString.

    Contains TSIG query parameters.
    """

    contract_ids: list[str] = field(default_factory=list)
    search: str = ""
    sort_by: list[str] = field(default_factory=list)
    gid: int = 0


@dataclass
class TSIGKey:
    """Maps to Go dns.TSIGKey.

    Contains TSIG key data.
    """

    name: str = ""
    algorithm: str = ""
    secret: str = ""


@dataclass
class GetTSIGKeyRequest:
    """Maps to Go dns.GetTSIGKeyRequest.

    Contains request parameters for GetTSIGKey.
    """

    zone: str = ""


@dataclass
class GetTSIGKeyResponse:
    """Maps to Go dns.GetTSIGKeyResponse.

    Contains the response data from GetTSIGKey operation.
    Embeds TSIGKey fields directly.
    """

    name: str = ""
    algorithm: str = ""
    secret: str = ""
    zone_count: int = 0


@dataclass
class DeleteTSIGKeyRequest:
    """Maps to Go dns.DeleteTSIGKeyRequest.

    Contains request parameters for DeleteTSIGKey.
    """

    zone: str = ""


@dataclass
class GetTSIGKeyAliasesRequest:
    """Maps to Go dns.GetTSIGKeyAliasesRequest.

    Contains request parameters for GetTSIGKeyAliases.
    """

    zone: str = ""


@dataclass
class GetTSIGKeyAliasesResponse:
    """Maps to Go dns.GetTSIGKeyAliasesResponse.

    Contains the response data from GetTSIGKeyAliases operation.
    """

    zones: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)


@dataclass
class TSIGKeyResponse:
    """Maps to Go dns.TSIGKeyResponse.

    Contains TSIG key GET response.  Embeds TSIGKey fields directly.
    """

    name: str = ""
    algorithm: str = ""
    secret: str = ""
    zone_count: int = 0


@dataclass
class TSIGKeyBulkPost:
    """Maps to Go dns.TSIGKeyBulkPost.

    Contains a TSIG key and a list of names of zones that should use the
    key.  Used with bulk update function.
    """

    key: TSIGKey | None = None
    zones: list[str] = field(default_factory=list)


@dataclass
class TSIGZoneAliases:
    """Maps to Go dns.TSIGZoneAliases.

    Contains a list of zone aliases.
    """

    aliases: list[str] = field(default_factory=list)


@dataclass
class TSIGReportMeta:
    """Maps to Go dns.TSIGReportMeta.

    Contains metadata for TSIGReport response.
    """

    total_elements: int = 0
    search: str = ""
    contracts: list[str] = field(default_factory=list)
    gid: int = 0
    sort_by: list[str] = field(default_factory=list)


@dataclass
class TSIGReportResponse:
    """Maps to Go dns.TSIGReportResponse.

    Contains response with a list of the TSIG keys used by zones.
    """

    metadata: TSIGReportMeta | None = None
    keys: list[TSIGKeyResponse] = field(default_factory=list)


@dataclass
class UpdateTSIGKeyRequest:
    """Maps to Go dns.UpdateTSIGKeyRequest.

    Contains request parameters for UpdateTSIGKey.
    """

    tsig_key: TSIGKey | None = None
    zone: str = ""


@dataclass
class UpdateTSIGKeyBulkRequest:
    """Maps to Go dns.UpdateTSIGKeyBulkRequest.

    Contains request parameters for UpdateTSIGKeyBulk.
    """

    tsig_key_bulk: TSIGKeyBulkPost | None = None


@dataclass
class GetTSIGKeyZonesRequest:
    """Maps to Go dns.GetTSIGKeyZonesRequest.

    Contains request parameters for GetTSIGKeyZones.
    """

    tsig_key: TSIGKey | None = None


@dataclass
class GetTSIGKeyZonesResponse:
    """Maps to Go dns.GetTSIGKeyZonesResponse.

    Contains the response data from GetTSIGKeyZones operation.
    """

    zones: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)


@dataclass
class ListTSIGKeysRequest:
    """Maps to Go dns.ListTSIGKeysRequest.

    Contains request parameters for ListTSIGKeys.
    """

    tsig_query: TSIGQueryString | None = None


@dataclass
class ListTSIGKeysResponse:
    """Maps to Go dns.ListTSIGKeysResponse.

    Contains the response data from ListTSIGKeys operation.
    """

    metadata: TSIGReportMeta | None = None
    keys: list[TSIGKeyResponse] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Models from zone.go
# ---------------------------------------------------------------------------


@dataclass
class ZoneQueryString:
    """Maps to Go dns.ZoneQueryString.

    Contains zone query parameters.
    """

    contract: str = ""
    group: str = ""


@dataclass
class OutboundZoneTransfer:
    """Maps to Go dns.OutboundZoneTransfer.

    Contains OutboundZoneTransfer request parameters.
    """

    acl: list[str] = field(default_factory=list)
    enabled: bool = False
    notify_targets: list[str] = field(default_factory=list)
    tsig_key: TSIGKey | None = None


@dataclass
class ZoneCreate:
    """Maps to Go dns.ZoneCreate.

    Contains zone create request data.
    """

    zone: str = ""
    type: str = ""
    masters: list[str] = field(default_factory=list)
    comment: str = ""
    sign_and_serve: bool = False
    sign_and_serve_algorithm: str = ""
    tsig_key: TSIGKey | None = None
    target: str = ""
    end_customer_id: str = ""
    contract_id: str = ""
    outbound_zone_transfer: OutboundZoneTransfer | None = None


@dataclass
class ZoneResponse:
    """Maps to Go dns.ZoneResponse.

    Contains zone response data.
    """

    zone: str = ""
    type: str = ""
    masters: list[str] = field(default_factory=list)
    comment: str = ""
    sign_and_serve: bool = False
    sign_and_serve_algorithm: str = ""
    tsig_key: TSIGKey | None = None
    target: str = ""
    end_customer_id: str = ""
    contract_id: str = ""
    alias_count: int = 0
    activation_state: str = ""
    last_activation_date: str = ""
    last_modified_by: str = ""
    last_modified_date: str = ""
    version_id: str = ""
    outbound_zone_transfer: OutboundZoneTransfer | None = None


@dataclass
class ListMetadata:
    """Maps to Go dns.ListMetadata.

    Contains metadata for List Zones request.
    """

    contract_ids: list[str] = field(default_factory=list)
    page: int = 0
    page_size: int = 0
    show_all: bool = False
    total_elements: int = 0


@dataclass
class ZoneListResponse:
    """Maps to Go dns.ZoneListResponse.

    Contains response for List Zones request.
    """

    metadata: ListMetadata | None = None
    zones: list[ZoneResponse] = field(default_factory=list)


@dataclass
class GetZoneResponse(ZoneResponse):
    """Maps to Go dns.GetZoneResponse.

    Alias for ZoneResponse.  In Go this is defined as
    ``type GetZoneResponse ZoneResponse``.
    """


@dataclass
class GetChangeListResponse:
    """Maps to Go dns.GetChangeListResponse.

    Contains metadata about a change list.
    """

    zone: str = ""
    change_tag: str = ""
    zone_version_id: str = ""
    last_modified_date: str = ""
    stale: bool = False


@dataclass
class ZoneNameListResponse:
    """Maps to Go dns.ZoneNameListResponse.

    Contains a response with a list of zone names and aliases.
    """

    zones: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)


@dataclass
class GetZoneNamesResponse:
    """Maps to Go dns.GetZoneNamesResponse.

    Contains record set names for a zone.
    """

    names: list[str] = field(default_factory=list)


@dataclass
class GetZoneNameTypesResponse:
    """Maps to Go dns.GetZoneNameTypesResponse.

    Contains record set types for a zone.
    """

    types: list[str] = field(default_factory=list)


@dataclass
class GetZoneRequest:
    """Maps to Go dns.GetZoneRequest.

    Contains request parameters for GetZone.
    """

    zone: str = ""


@dataclass
class GetChangeListRequest:
    """Maps to Go dns.GetChangeListRequest.

    Contains request parameters for GetChangeList.
    """

    zone: str = ""


@dataclass
class ListZonesRequest:
    """Maps to Go dns.ListZonesRequest.

    Contains request parameters for ListZones.
    """

    contract_ids: str = ""
    page: int = 0
    page_size: int = 0
    search: str = ""
    show_all: bool = False
    sort_by: str = ""
    types: str = ""


@dataclass
class GetMasterZoneFileRequest:
    """Maps to Go dns.GetMasterZoneFileRequest.

    Contains request parameters for GetMasterZoneFile.
    """

    zone: str = ""


@dataclass
class PostMasterZoneFileRequest:
    """Maps to Go dns.PostMasterZoneFileRequest.

    Contains request parameters for PostMasterZoneFile.
    """

    zone: str = ""
    file_data: str = ""


@dataclass
class CreateZoneRequest:
    """Maps to Go dns.CreateZoneRequest.

    Contains request parameters for CreateZone.
    """

    create_zone: ZoneCreate | None = None
    zone_query_string: ZoneQueryString | None = None
    clear_conn: list[bool] = field(default_factory=list)


@dataclass
class SaveChangeListRequest:
    """Maps to Go dns.SaveChangeListRequest (alias for ZoneCreate).

    Contains request parameters for SaveChangeList.
    """

    zone: str = ""
    type: str = ""
    masters: list[str] = field(default_factory=list)
    comment: str = ""
    sign_and_serve: bool = False
    sign_and_serve_algorithm: str = ""
    tsig_key: TSIGKey | None = None
    target: str = ""
    end_customer_id: str = ""
    contract_id: str = ""
    outbound_zone_transfer: OutboundZoneTransfer | None = None


@dataclass
class SubmitChangeListRequest:
    """Maps to Go dns.SubmitChangeListRequest (alias for ZoneCreate).

    Contains request parameters for SubmitChangeList.
    """

    zone: str = ""
    type: str = ""
    masters: list[str] = field(default_factory=list)
    comment: str = ""
    sign_and_serve: bool = False
    sign_and_serve_algorithm: str = ""
    tsig_key: TSIGKey | None = None
    target: str = ""
    end_customer_id: str = ""
    contract_id: str = ""
    outbound_zone_transfer: OutboundZoneTransfer | None = None


@dataclass
class UpdateZoneRequest:
    """Maps to Go dns.UpdateZoneRequest.

    Contains request parameters for UpdateZone.
    """

    create_zone: ZoneCreate | None = None


@dataclass
class GetZoneNamesRequest:
    """Maps to Go dns.GetZoneNamesRequest.

    Contains request parameters for GetZoneNames.
    """

    zone: str = ""


@dataclass
class GetZoneNameTypesRequest:
    """Maps to Go dns.GetZoneNameTypesRequest.

    Contains request parameters for GetZoneNameTypes.
    """

    zone: str = ""
    zone_name: str = ""


@dataclass
class SecRecords:
    """Maps to Go dns.SecRecords.

    Represents a set of DNSSEC records for a DNS zone.
    """

    dnskey_record: str = ""
    ds_record: str = ""
    expected_ttl: int = 0
    last_modified_date: str = ""


@dataclass
class SecStatus:
    """Maps to Go dns.SecStatus.

    Represents the DNSSEC status for a DNS zone.
    """

    zone: str = ""
    alerts: list[str] = field(default_factory=list)
    current_records: SecRecords | None = None
    new_records: SecRecords | None = None


@dataclass
class GetZonesDNSSecStatusRequest:
    """Maps to Go dns.GetZonesDNSSecStatusRequest.

    Used to get the DNSSEC status for one or more zones.
    """

    zones: list[str] = field(default_factory=list)


@dataclass
class GetZonesDNSSecStatusResponse:
    """Maps to Go dns.GetZonesDNSSecStatusResponse.

    Represents a list of DNSSEC statuses for DNS zones specified
    in the GetZonesDNSSecStatus request.
    """

    dns_sec_statuses: list[SecStatus] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Models from zonebulk.go
# ---------------------------------------------------------------------------


@dataclass
class BulkZonesCreate:
    """Maps to Go dns.BulkZonesCreate.

    Contains the list of zones to create in bulk.
    """

    zones: list[ZoneCreate] = field(default_factory=list)


@dataclass
class BulkZonesResponse:
    """Maps to Go dns.BulkZonesResponse.

    Contains the response from a bulk zone create or delete request.
    """

    request_id: str = ""
    expiration_date: str = ""


@dataclass
class BulkStatusResponse:
    """Maps to Go dns.BulkStatusResponse.

    Contains status information for a bulk operation.
    """

    request_id: str = ""
    zones_submitted: int = 0
    success_count: int = 0
    failure_count: int = 0
    is_complete: bool = False
    expiration_date: str = ""


@dataclass
class BulkFailedZone:
    """Maps to Go dns.BulkFailedZone.

    Contains information about a zone that failed during bulk operation.
    """

    zone: str = ""
    failure_reason: str = ""


@dataclass
class BulkCreateResultResponse:
    """Maps to Go dns.BulkCreateResultResponse.

    Contains the result of a bulk zone create operation.
    """

    request_id: str = ""
    successfully_created_zones: list[str] = field(default_factory=list)
    failed_zones: list[BulkFailedZone] = field(default_factory=list)


@dataclass
class BulkDeleteResultResponse:
    """Maps to Go dns.BulkDeleteResultResponse.

    Contains the result of a bulk zone delete operation.
    """

    request_id: str = ""
    successfully_deleted_zones: list[str] = field(default_factory=list)
    failed_zones: list[BulkFailedZone] = field(default_factory=list)


@dataclass
class GetBulkZoneCreateStatusRequest:
    """Maps to Go dns.GetBulkZoneCreateStatusRequest.

    Contains the request parameters for GetBulkZoneCreateStatus.
    """

    request_id: str = ""


@dataclass
class GetBulkZoneCreateStatusResponse:
    """Maps to Go dns.GetBulkZoneCreateStatusResponse.

    Contains the response for GetBulkZoneCreateStatus.
    """

    request_id: str = ""
    zones_submitted: int = 0
    success_count: int = 0
    failure_count: int = 0
    is_complete: bool = False
    expiration_date: str = ""


@dataclass
class GetBulkZoneDeleteStatusRequest:
    """Maps to Go dns.GetBulkZoneDeleteStatusRequest.

    Contains the request parameters for GetBulkZoneDeleteStatus.
    """

    request_id: str = ""


@dataclass
class GetBulkZoneDeleteStatusResponse:
    """Maps to Go dns.GetBulkZoneDeleteStatusResponse.

    Contains the response for GetBulkZoneDeleteStatus.
    """

    request_id: str = ""
    zones_submitted: int = 0
    success_count: int = 0
    failure_count: int = 0
    is_complete: bool = False
    expiration_date: str = ""


@dataclass
class GetBulkZoneCreateResultRequest:
    """Maps to Go dns.GetBulkZoneCreateResultRequest.

    Contains the request parameters for GetBulkZoneCreateResult.
    """

    request_id: str = ""


@dataclass
class GetBulkZoneCreateResultResponse:
    """Maps to Go dns.GetBulkZoneCreateResultResponse.

    Contains the response for GetBulkZoneCreateResult.
    """

    request_id: str = ""
    successfully_created_zones: list[str] = field(default_factory=list)
    failed_zones: list[BulkFailedZone] = field(default_factory=list)


@dataclass
class GetBulkZoneDeleteResultRequest:
    """Maps to Go dns.GetBulkZoneDeleteResultRequest.

    Contains the request parameters for GetBulkZoneDeleteResult.
    """

    request_id: str = ""


@dataclass
class GetBulkZoneDeleteResultResponse:
    """Maps to Go dns.GetBulkZoneDeleteResultResponse.

    Contains the response for GetBulkZoneDeleteResult.
    """

    request_id: str = ""
    successfully_deleted_zones: list[str] = field(default_factory=list)
    failed_zones: list[BulkFailedZone] = field(default_factory=list)


@dataclass
class CreateBulkZonesRequest:
    """Maps to Go dns.CreateBulkZonesRequest.

    Contains the request parameters for CreateBulkZones.
    """

    bulk_zones: BulkZonesCreate | None = None
    zone_query_string: ZoneQueryString | None = None


@dataclass
class CreateBulkZonesResponse:
    """Maps to Go dns.CreateBulkZonesResponse.

    Contains the response for CreateBulkZones.
    """

    request_id: str = ""
    expiration_date: str = ""


@dataclass
class DeleteBulkZonesRequest:
    """Maps to Go dns.DeleteBulkZonesRequest.

    Contains the request parameters for DeleteBulkZones.
    """

    zones_list: ZoneNameListResponse | None = None
    bypass_safety_checks: bool | None = None


@dataclass
class DeleteBulkZonesResponse:
    """Maps to Go dns.DeleteBulkZonesResponse.

    Contains the response for DeleteBulkZones.
    """

    request_id: str = ""
    expiration_date: str = ""
