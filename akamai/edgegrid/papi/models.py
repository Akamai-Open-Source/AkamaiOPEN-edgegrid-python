"""Request and response model classes for the PAPI client."""

# pylint: disable=too-many-instance-attributes,invalid-name,too-many-lines

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Type alias
# ---------------------------------------------------------------------------

RuleOptionsMap = dict[str, Any]
"""Type alias for rule behavior/criteria options map.

Mirrors Go ``RuleOptionsMap = map[string]interface{}``.
"""


# ---------------------------------------------------------------------------
# Typed-string constants  – Activation
# ---------------------------------------------------------------------------

ActivationTypeActivate: str = "ACTIVATE"
"""Mirrors Go ``ActivationTypeActivate``."""

ActivationTypeDeactivate: str = "DEACTIVATE"
"""Mirrors Go ``ActivationTypeDeactivate``."""

ActivationNetworkStaging: str = "STAGING"
"""Mirrors Go ``ActivationNetworkStaging``."""

ActivationNetworkProduction: str = "PRODUCTION"
"""Mirrors Go ``ActivationNetworkProduction``."""

ActivationStatusActive: str = "ACTIVE"
"""Mirrors Go ``ActivationStatusActive``."""

ActivationStatusInactive: str = "INACTIVE"
"""Mirrors Go ``ActivationStatusInactive``."""

ActivationStatusNew: str = "NEW"
"""Mirrors Go ``ActivationStatusNew``."""

ActivationStatusPending: str = "PENDING"
"""Mirrors Go ``ActivationStatusPending``."""

ActivationStatusAborted: str = "ABORTED"
"""Mirrors Go ``ActivationStatusAborted``."""

ActivationStatusFailed: str = "FAILED"
"""Mirrors Go ``ActivationStatusFailed``."""

ActivationStatusZone1: str = "ZONE_1"
"""Mirrors Go ``ActivationStatusZone1``."""

ActivationStatusZone2: str = "ZONE_2"
"""Mirrors Go ``ActivationStatusZone2``."""

ActivationStatusZone3: str = "ZONE_3"
"""Mirrors Go ``ActivationStatusZone3``."""

ActivationStatusDeactivating: str = "PENDING_DEACTIVATION"
"""Mirrors Go ``ActivationStatusDeactivating``."""

ActivationStatusCancelling: str = "PENDING_CANCELLATION"
"""Mirrors Go ``ActivationStatusCancelling``."""

ActivationStatusDeactivated: str = "DEACTIVATED"
"""Mirrors Go ``ActivationStatusDeactivated``."""


# ---------------------------------------------------------------------------
# Typed-string constants  – Search
# ---------------------------------------------------------------------------

SearchKeyEdgeHostname: str = "edgeHostname"
"""Mirrors Go ``SearchKeyEdgeHostname``."""

SearchKeyHostname: str = "hostname"
"""Mirrors Go ``SearchKeyHostname``."""

SearchKeyPropertyName: str = "propertyName"
"""Mirrors Go ``SearchKeyPropertyName``."""


# ---------------------------------------------------------------------------
# Typed-string constants  – Rule validate mode / criteria
# ---------------------------------------------------------------------------

RuleValidateModeFast: str = "fast"
"""Mirrors Go ``RuleValidateModeFast``."""

RuleValidateModeFull: str = "full"
"""Mirrors Go ``RuleValidateModeFull``."""

RuleCriteriaMustSatisfyAll: str = "all"
"""Mirrors Go ``RuleCriteriaMustSatisfyAll``."""

RuleCriteriaMustSatisfyAny: str = "any"
"""Mirrors Go ``RuleCriteriaMustSatisfyAny``."""


# ---------------------------------------------------------------------------
# Typed-string constants  – Edge hostname
# ---------------------------------------------------------------------------

EHSecureNetworkStandardTLS: str = "STANDARD_TLS"
"""Mirrors Go ``EHSecureNetworkStandardTLS``."""

EHSecureNetworkSharedCert: str = "SHARED_CERT"
"""Mirrors Go ``EHSecureNetworkSharedCert``."""

EHSecureNetworkEnhancedTLS: str = "ENHANCED_TLS"
"""Mirrors Go ``EHSecureNetworkEnhancedTLS``."""

EHIPVersionV4: str = "IPV4"
"""Mirrors Go ``EHIPVersionV4``."""

EHIPVersionV6Performance: str = "IPV6_PERFORMANCE"
"""Mirrors Go ``EHIPVersionV6Performance``."""

EHIPVersionV6Compliance: str = "IPV6_COMPLIANCE"
"""Mirrors Go ``EHIPVersionV6Compliance``."""

UseCaseGlobal: str = "GLOBAL"
"""Mirrors Go ``UseCaseGlobal``."""

AkamaizedNetDomainRegexPattern: str = (
    r"^[A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?$"
)
"""Regex for akamaized.net domain validation. Mirrors Go constant."""

DefaultEHDomainRegexPattern: str = (
    r"^[A-Za-z0-9](?:[A-Za-z0-9_-]*[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9_-]*[A-Za-z0-9])?)*\.?$"
)
"""Regex for default edge hostname domain validation. Mirrors Go constant."""


# ---------------------------------------------------------------------------
# Typed-string constants  – Include
# ---------------------------------------------------------------------------

IncludeTypeMicroServices: str = "MICROSERVICES"
"""Mirrors Go ``IncludeTypeMicroServices``."""

IncludeTypeCommonSettings: str = "COMMON_SETTINGS"
"""Mirrors Go ``IncludeTypeCommonSettings``."""


# ---------------------------------------------------------------------------
# Typed-string constants  – Compliance
# ---------------------------------------------------------------------------

NoncomplianceReasonNoProductionTraffic: str = "NO_PRODUCTION_TRAFFIC"
"""Mirrors Go ``NoncomplianceReasonNoProductionTraffic``."""

NoncomplianceReasonOther: str = "OTHER"
"""Mirrors Go ``NoncomplianceReasonOther``."""

NoncomplianceReasonEmergency: str = "EMERGENCY"
"""Mirrors Go ``NoncomplianceReasonEmergency``."""

NoncomplianceReasonNone: str = "NONE"
"""Mirrors Go ``NoncomplianceReasonNone``."""


# ---------------------------------------------------------------------------
# Typed-string constants  – Hostname / CnameType
# ---------------------------------------------------------------------------

HostnameCnameTypeEdgeHostname: str = "EDGE_HOSTNAME"
"""Mirrors Go ``HostnameCnameTypeEdgeHostname``."""


# ---------------------------------------------------------------------------
# Typed-string constants  – Version status / activated-on
# ---------------------------------------------------------------------------

VersionStatusActive: str = "ACTIVE"
"""Mirrors Go ``VersionStatusActive``."""

VersionStatusInactive: str = "INACTIVE"
"""Mirrors Go ``VersionStatusInactive``."""

VersionStatusPending: str = "PENDING"
"""Mirrors Go ``VersionStatusPending``."""

VersionStatusDeactivated: str = "DEACTIVATED"
"""Mirrors Go ``VersionStatusDeactivated``."""

VersionProduction: str = "PRODUCTION"
"""Mirrors Go ``VersionProduction``."""

VersionStaging: str = "STAGING"
"""Mirrors Go ``VersionStaging``."""


# ---------------------------------------------------------------------------
# Typed-string constants  – Sort / CertType
# ---------------------------------------------------------------------------

SortAscending: str = "hostname:a"
"""Mirrors Go ``SortAscending``."""

SortDescending: str = "hostname:d"
"""Mirrors Go ``SortDescending``."""

CertTypeCPSManaged: str = "CPS_MANAGED"
"""Mirrors Go ``CertTypeCPSManaged``."""

CertTypeDefault: str = "DEFAULT"
"""Mirrors Go ``CertTypeDefault``."""

CertTypeCCM: str = "CCM"
"""Mirrors Go ``CertTypeCCM``."""


# ---------------------------------------------------------------------------
# Utility function
# ---------------------------------------------------------------------------


def response_link_parse(link: str) -> tuple[str, str | None]:
    """Parse a response link URL and return the last path segment as an ID.

    Mirrors Go ``ResponseLinkParse`` from *response_link.go*.

    Args:
        link: The URL link string to parse.

    Returns:
        Tuple of ``(id_string, error_message_or_none)``.
    """
    try:
        parsed = urlparse(link)
        parts = parsed.path.split("/")
        return parts[-1], None
    except Exception as err:  # pylint: disable=broad-except
        return "", str(err)


# =========================================================================
# Base response
# =========================================================================


@dataclass
class Response:
    """Base PAPI response type embedded in most responses.

    Mirrors Go ``papi.Response``.
    """

    account_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    etag: str = ""
    errors: list | None = None
    warnings: list | None = None


# =========================================================================
# activation.go  models
# =========================================================================


@dataclass
class ActivationFallbackInfo:
    """Fallback information for a property activation.

    Mirrors Go ``papi.ActivationFallbackInfo``.
    """

    fast_fallback_attempted: bool = False
    fallback_version: int = 0
    can_fast_fallback: bool = False
    steady_state_time: int = 0
    fast_fallback_expiration_time: int = 0
    fast_fallback_recovery_state: str | None = None


@dataclass
class Activation:
    """Property activation resource.

    Mirrors Go ``papi.Activation``.
    """

    account_id: str = ""
    activation_id: str = ""
    activation_type: str = ""
    use_fast_fallback: bool = False
    fallback_info: ActivationFallbackInfo | None = None
    acknowledge_warnings: list[str] = field(default_factory=list)
    acknowledge_all_warnings: bool = False
    fast_push: bool = False
    fma_activation_state: str = ""
    group_id: str = ""
    ignore_http_errors: bool = False
    property_name: str = ""
    property_id: str = ""
    property_version: int = 0
    network: str = ""
    status: str = ""
    submit_date: str = ""
    update_date: str = ""
    note: str = ""
    notify_emails: list[str] = field(default_factory=list)
    compliance_record: dict | None = None


@dataclass
class CreateActivationRequest:
    """Request body for creating a property activation.

    Mirrors Go ``papi.CreateActivationRequest``.
    """

    property_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    activation: Activation | None = None


@dataclass
class ActivationsItems:
    """Wrapper holding a list of activations.

    Mirrors Go ``papi.ActivationsItems``.
    """

    items: list[Activation] = field(default_factory=list)


@dataclass
class GetActivationsResponse(Response):
    """Response for listing property activations.

    Mirrors Go ``papi.GetActivationsResponse``.
    """

    activations: ActivationsItems | None = None
    retry_after: int = 0


@dataclass
class CreateActivationResponse(Response):
    """Response for creating a property activation.

    Mirrors Go ``papi.CreateActivationResponse``.
    """

    activation_id: str = ""
    activation_link: str = ""


@dataclass
class GetActivationsRequest:
    """Request for listing property activations.

    Mirrors Go ``papi.GetActivationsRequest``.
    """

    property_id: str = ""
    contract_id: str = ""
    group_id: str = ""


@dataclass
class GetActivationRequest:
    """Request for getting a single property activation.

    Mirrors Go ``papi.GetActivationRequest``.
    """

    property_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    activation_id: str = ""


@dataclass
class GetActivationResponse(GetActivationsResponse):
    """Response for getting a single property activation.

    Mirrors Go ``papi.GetActivationResponse``.
    """

    activation: Activation | None = None


@dataclass
class CancelActivationRequest:
    """Request for cancelling a property activation.

    Mirrors Go ``papi.CancelActivationRequest``.
    """

    property_id: str = ""
    activation_id: str = ""
    contract_id: str = ""
    group_id: str = ""


@dataclass
class CancelActivationResponse:
    """Response for cancelling a property activation.

    Mirrors Go ``papi.CancelActivationResponse``.
    """

    activations: ActivationsItems | None = None


# =========================================================================
# property.go  models
# =========================================================================


@dataclass
class PropertyCloneFrom:
    """Clone-from specification when creating a property.

    Mirrors Go ``papi.PropertyCloneFrom``.
    """

    clone_from_version_etag: str = ""
    copy_hostnames: bool = False
    property_id: str = ""
    version: int = 0


@dataclass
class Property:
    """A PAPI property resource.

    Mirrors Go ``papi.Property``.
    """

    account_id: str = ""
    asset_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    latest_version: int = 0
    note: str = ""
    production_version: int | None = None
    property_id: str = ""
    property_name: str = ""
    staging_version: int | None = None
    property_type: str | None = None


@dataclass
class PropertiesItems:
    """Wrapper holding a list of properties.

    Mirrors Go ``papi.PropertiesItems``.
    """

    items: list[Property] = field(default_factory=list)


@dataclass
class GetPropertiesRequest:
    """Request for listing properties.

    Mirrors Go ``papi.GetPropertiesRequest``.
    """

    contract_id: str = ""
    group_id: str = ""


@dataclass
class GetPropertiesResponse(Response):
    """Response for listing properties.

    Mirrors Go ``papi.GetPropertiesResponse``.
    """

    properties: PropertiesItems | None = None


@dataclass
class PropertyCreate:
    """Body for creating a new property.

    Mirrors Go ``papi.PropertyCreate``.
    """

    clone_from: PropertyCloneFrom | None = None
    product_id: str = ""
    property_name: str = ""
    rule_format: str = ""
    use_hostname_bucket: bool = False


@dataclass
class CreatePropertyRequest:
    """Request for creating a property.

    Mirrors Go ``papi.CreatePropertyRequest``.
    """

    contract_id: str = ""
    group_id: str = ""
    property: PropertyCreate | None = None


@dataclass
class CreatePropertyResponse(Response):
    """Response for creating a property.

    Mirrors Go ``papi.CreatePropertyResponse``.
    """

    property_id: str = ""
    property_link: str = ""


@dataclass
class GetPropertyRequest:
    """Request for getting a single property.

    Mirrors Go ``papi.GetPropertyRequest``.
    """

    contract_id: str = ""
    group_id: str = ""
    property_id: str = ""


@dataclass
class GetPropertyResponse(Response):
    """Response for getting a single property.

    Mirrors Go ``papi.GetPropertyResponse``.
    """

    properties: PropertiesItems | None = None
    property: Property | None = None


@dataclass
class RemovePropertyRequest:
    """Request for removing a property.

    Mirrors Go ``papi.RemovePropertyRequest``.
    """

    property_id: str = ""
    contract_id: str = ""
    group_id: str = ""


@dataclass
class RemovePropertyResponse:
    """Response for removing a property.

    Mirrors Go ``papi.RemovePropertyResponse``.
    """

    message: str = ""


@dataclass
class MapPropertyIDToNameRequest:
    """Request to map a property ID to its name.

    Mirrors Go ``papi.MapPropertyIDToNameRequest``.
    """

    property_id: str = ""


@dataclass
class MapPropertyNameToIDRequest:
    """Request to map a property name to its ID.

    Mirrors Go ``papi.MapPropertyNameToIDRequest``.
    """

    group_id: str = ""
    contract_id: str = ""
    name: str = ""


# =========================================================================
# contract.go  models
# =========================================================================


@dataclass
class Contract:
    """A contract resource.

    Mirrors Go ``papi.Contract``.
    """

    contract_id: str = ""
    contract_type_name: str = ""


@dataclass
class ContractsItems:
    """Wrapper holding a list of contracts.

    Mirrors Go ``papi.ContractsItems``.
    """

    items: list[Contract] = field(default_factory=list)


@dataclass
class GetContractsResponse:
    """Response for listing contracts.

    Mirrors Go ``papi.GetContractsResponse``.
    """

    account_id: str = ""
    contracts: ContractsItems | None = None


# =========================================================================
# group.go  models
# =========================================================================


@dataclass
class Group:
    """A group resource.

    Mirrors Go ``papi.Group``.
    """

    group_id: str = ""
    group_name: str = ""
    parent_group_id: str = ""
    contract_ids: list[str] = field(default_factory=list)


@dataclass
class GroupItems:
    """Wrapper holding a list of groups.

    Mirrors Go ``papi.GroupItems``.
    """

    items: list[Group] = field(default_factory=list)


@dataclass
class GetGroupsResponse:
    """Response for listing groups.

    Mirrors Go ``papi.GetGroupsResponse``.
    """

    account_id: str = ""
    account_name: str = ""
    groups: GroupItems | None = None


# =========================================================================
# cpcode.go  models
# =========================================================================


@dataclass
class CPCode:
    """A CP code resource.

    Mirrors Go ``papi.CPCode``.
    """

    cp_code_id: str = ""
    cp_code_name: str = ""
    created_date: str = ""
    product_ids: list[str] = field(default_factory=list)


@dataclass
class CPCodeContract:
    """Contract reference inside a CP code detail.

    Mirrors Go ``papi.CPCodeContract``.
    """

    contract_id: str = ""
    status: str = ""


@dataclass
class CPCodeProduct:
    """Product reference inside a CP code detail.

    Mirrors Go ``papi.CPCodeProduct``.
    """

    product_id: str = ""
    product_name: str = ""


@dataclass
class CPCodeTimeZone:
    """Timezone override for a CP code.

    Mirrors Go ``papi.TimeZone``.
    """

    timezone_id: str = ""
    timezone_value: str = ""


@dataclass
class CPCodeDetailResponse:
    """Detailed CP code resource used in get/update flows.

    Mirrors Go ``papi.CPCodeDetailResponse``.
    """

    id: int = 0
    name: str = ""
    purgeable: bool = False
    account_id: str = ""
    default_time_zone: str = ""
    override_time_zone: CPCodeTimeZone | None = None
    type: str = ""
    contracts: list[CPCodeContract] = field(default_factory=list)
    products: list[CPCodeProduct] = field(default_factory=list)


@dataclass
class CPCodeItems:
    """Wrapper holding a list of CP codes.

    Mirrors Go ``papi.CPCodeItems``.
    """

    items: list[CPCode] = field(default_factory=list)


@dataclass
class GetCPCodesRequest:
    """Request for listing CP codes.

    Mirrors Go ``papi.GetCPCodesRequest``.
    """

    contract_id: str = ""
    group_id: str = ""


@dataclass
class GetCPCodesResponse(Response):
    """Response for listing CP codes.

    Mirrors Go ``papi.GetCPCodesResponse``.
    """

    cp_codes: CPCodeItems | None = None


@dataclass
class GetCPCodeRequest:
    """Request for getting a single CP code.

    Mirrors Go ``papi.GetCPCodeRequest``.
    """

    cpcode_id: str = ""
    contract_id: str = ""
    group_id: str = ""


@dataclass
class CreateCPCode:
    """Body for creating a CP code.

    Mirrors Go ``papi.CreateCPCode``.
    """

    product_id: str = ""
    cpcode_name: str = ""


@dataclass
class CreateCPCodeRequest:
    """Request for creating a CP code.

    Mirrors Go ``papi.CreateCPCodeRequest``.
    """

    contract_id: str = ""
    group_id: str = ""
    cpcode: CreateCPCode | None = None


@dataclass
class CreateCPCodeResponse:
    """Response for creating a CP code.

    Mirrors Go ``papi.CreateCPCodeResponse``.
    """

    cpcode_link: str = ""
    cpcode_id: str = ""


@dataclass
class UpdateCPCodeRequest:
    """Request body for updating a CP code.

    Mirrors Go ``papi.UpdateCPCodeRequest``.
    """

    id: int = 0
    name: str = ""
    purgeable: bool | None = None
    override_time_zone: CPCodeTimeZone | None = None
    contracts: list[CPCodeContract] = field(default_factory=list)
    products: list[CPCodeProduct] = field(default_factory=list)


# =========================================================================
# edgehostname.go  models
# =========================================================================


@dataclass
class UseCase:
    """Edge hostname use-case specification.

    Mirrors Go ``papi.UseCase``.
    """

    option: str = ""
    type: str = ""
    use_case: str = ""


@dataclass
class EdgeHostnameGetItem:
    """An edge hostname resource from a GET response.

    Mirrors Go ``papi.EdgeHostnameGetItem``.
    """

    id: str = ""
    domain: str = ""
    product_id: str = ""
    domain_prefix: str = ""
    domain_suffix: str = ""
    status: str = ""
    secure: bool = False
    ip_version_behavior: str = ""
    use_cases: list[UseCase] = field(default_factory=list)


@dataclass
class EdgeHostnameItems:
    """Wrapper holding a list of edge hostnames.

    Mirrors Go ``papi.EdgeHostnameItems``.
    """

    items: list[EdgeHostnameGetItem] = field(default_factory=list)


@dataclass
class GetEdgeHostnamesRequest:
    """Request for listing edge hostnames.

    Mirrors Go ``papi.GetEdgeHostnamesRequest``.
    """

    contract_id: str = ""
    group_id: str = ""
    options: list[str] = field(default_factory=list)


@dataclass
class GetEdgeHostnameRequest:
    """Request for getting a single edge hostname.

    Mirrors Go ``papi.GetEdgeHostnameRequest``.
    """

    edge_hostname_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    options: list[str] = field(default_factory=list)


@dataclass
class GetEdgeHostnamesResponse(Response):
    """Response for listing edge hostnames.

    Mirrors Go ``papi.GetEdgeHostnamesResponse``.
    """

    edge_hostnames: EdgeHostnameItems | None = None


@dataclass
class EdgeHostnameCreate:
    """Body for creating an edge hostname.

    Mirrors Go ``papi.EdgeHostnameCreate``.
    """

    product_id: str = ""
    domain_prefix: str = ""
    domain_suffix: str = ""
    secure: bool = False
    secure_network: str = ""
    slot_number: int = 0
    ip_version_behavior: str = ""
    cert_enrollment_id: int = 0
    use_cases: list[UseCase] = field(default_factory=list)


@dataclass
class CreateEdgeHostnameRequest:
    """Request for creating an edge hostname.

    Mirrors Go ``papi.CreateEdgeHostnameRequest``.
    """

    contract_id: str = ""
    group_id: str = ""
    options: list[str] = field(default_factory=list)
    edge_hostname: EdgeHostnameCreate | None = None


@dataclass
class CreateEdgeHostnameResponse:
    """Response for creating an edge hostname.

    Mirrors Go ``papi.CreateEdgeHostnameResponse``.
    """

    edge_hostname_link: str = ""
    edge_hostname_id: str = ""


@dataclass
class EdgeHostname:
    """Simplified edge hostname model used in older responses.

    Mirrors Go ``papi.EdgeHostname``.
    """

    edge_hostname_id: str = ""
    edge_hostname_domain: str = ""
    product_id: str = ""
    domain_prefix: str = ""
    domain_suffix: str = ""
    ip_version_behavior: str = ""
    secure: bool = False
    map_details_serial_number: int = 0
    map_details_slot_number: int = 0
    map_details_map_domain: str = ""
    use_default_ttl: bool = False
    use_default_map: bool = False
    ttl: int = 0


# =========================================================================
# search.go  models
# =========================================================================


@dataclass
class SearchItem:
    """A single search result item.

    Mirrors Go ``papi.SearchItem``.
    """

    account_id: str = ""
    asset_id: str = ""
    contract_id: str = ""
    edge_hostname: str = ""
    group_id: str = ""
    hostname: str = ""
    production_status: str = ""
    property_id: str = ""
    property_name: str = ""
    property_version: int = 0
    staging_status: str = ""
    updated_by_user: str = ""
    updated_date: str = ""


@dataclass
class SearchItems:
    """Wrapper holding a list of search result items.

    Mirrors Go ``papi.SearchItems``.
    """

    items: list[SearchItem] = field(default_factory=list)


@dataclass
class SearchResponse:
    """Response for a property search.

    Mirrors Go ``papi.SearchResponse``.
    """

    versions: SearchItems | None = None


@dataclass
class SearchRequest:
    """Request for searching properties.

    Mirrors Go ``papi.SearchRequest``.
    """

    key: str = ""
    value: str = ""


# =========================================================================
# rule.go  models
# =========================================================================


@dataclass
class RuleCustomOverride:
    """Custom override for a rule tree.

    Mirrors Go ``papi.RuleCustomOverride``.
    """

    name: str = ""
    override_id: str = ""


@dataclass
class RuleOptions:
    """Options block at the top of a rule tree.

    Mirrors Go ``papi.RuleOptions``.
    """

    is_secure: bool = False


@dataclass
class RuleVariable:
    """A user-defined variable in the rule tree.

    Mirrors Go ``papi.RuleVariable``.
    """

    description: str | None = None
    hidden: bool = False
    name: str = ""
    sensitive: bool = False
    value: str | None = None


@dataclass
class RuleBehavior:
    """A behavior or criteria entry in the rule tree.

    Mirrors Go ``papi.RuleBehavior``.
    """

    locked: bool = False
    name: str = ""
    options: RuleOptionsMap = field(default_factory=dict)
    uuid: str = ""
    template_uuid: str = ""


@dataclass
class Rules:
    """A single rule node in a property rule tree.

    Mirrors Go ``papi.Rules``.
    """

    advanced_override: str = ""
    behaviors: list[RuleBehavior] = field(default_factory=list)
    children: list[Rules] = field(default_factory=list)
    comments: str = ""
    criteria: list[RuleBehavior] = field(default_factory=list)
    criteria_locked: bool = False
    custom_override: RuleCustomOverride | None = None
    name: str = ""
    options: RuleOptions | None = None
    uuid: str = ""
    template_uuid: str = ""
    template_link: str = ""
    variables: list[RuleVariable] = field(default_factory=list)
    criteria_must_satisfy: str = ""


@dataclass
class RulesUpdate:
    """Wrapper used for PUT rule-tree requests.

    Mirrors Go ``papi.RulesUpdate``.
    """

    comments: str = ""
    rules: Rules | None = None


@dataclass
class RuleError:
    """An error entry returned within rule tree operations.

    Mirrors Go ``papi.RuleError``.
    """

    type: str = ""
    title: str = ""
    detail: str = ""
    instance: str = ""
    behavior_name: str = ""
    error_location: str = ""


@dataclass
class RuleWarnings:
    """A warning entry returned within rule tree operations.

    Mirrors Go ``papi.RuleWarnings``.
    """

    title: str = ""
    type: str = ""
    error_location: str = ""
    detail: str = ""
    current_rule_format: str = ""
    suggested_rule_format: str = ""


@dataclass
class GetRuleTreeRequest:
    """Request for getting a property rule tree.

    Mirrors Go ``papi.GetRuleTreeRequest``.
    """

    property_id: str = ""
    property_version: int = 0
    contract_id: str = ""
    group_id: str = ""
    validate_mode: str = ""
    validate_rules: bool = False
    rule_format: str = ""
    original_input: bool | None = None


@dataclass
class GetRuleTreeResponse(Response):
    """Response for getting a property rule tree.

    Mirrors Go ``papi.GetRuleTreeResponse``.
    """

    property_id: str = ""
    property_version: int = 0
    rule_format: str = ""
    rules: Rules | None = None
    comments: str = ""


@dataclass
class UpdateRulesRequest:
    """Request for updating a property rule tree.

    Mirrors Go ``papi.UpdateRulesRequest``.
    """

    property_id: str = ""
    property_version: int = 0
    contract_id: str = ""
    dry_run: bool = False
    group_id: str = ""
    validate_mode: str = ""
    validate_rules: bool = False
    rules: RulesUpdate | None = None


@dataclass
class UpdateRulesResponse:
    """Response for updating a property rule tree.

    Mirrors Go ``papi.UpdateRulesResponse``.
    """

    account_id: str = ""
    contract_id: str = ""
    comments: str = ""
    group_id: str = ""
    property_id: str = ""
    property_version: int = 0
    etag: str = ""
    rule_format: str = ""
    rules: Rules | None = None
    errors: list[RuleError] = field(default_factory=list)
    warnings: list[RuleWarnings] = field(default_factory=list)


# =========================================================================
# ruleformats.go  models
# =========================================================================


@dataclass
class RuleFormatItems:
    """Wrapper holding a list of rule format strings.

    Mirrors Go ``papi.RuleFormatItems``.
    """

    items: list[str] = field(default_factory=list)


@dataclass
class GetRuleFormatsResponse:
    """Response for listing rule formats.

    Mirrors Go ``papi.GetRuleFormatsResponse``.
    """

    rule_formats: RuleFormatItems | None = None


# =========================================================================
# clientsettings.go  models
# =========================================================================


@dataclass
class ClientSettingsBody:
    """Client settings body for getting/updating client settings.

    Mirrors Go ``papi.ClientSettingsBody``.
    """

    rule_format: str = ""
    use_prefixes: bool = False


# =========================================================================
# products.go  models
# =========================================================================


@dataclass
class ProductItem:
    """A product resource.

    Mirrors Go ``papi.ProductItem``.
    """

    product_id: str = ""
    product_name: str = ""


@dataclass
class ProductsItems:
    """Wrapper holding a list of products.

    Mirrors Go ``papi.ProductsItems``.
    """

    items: list[ProductItem] = field(default_factory=list)


@dataclass
class GetProductsRequest:
    """Request for listing products.

    Mirrors Go ``papi.GetProductsRequest``.
    """

    contract_id: str = ""


@dataclass
class GetProductsResponse:
    """Response for listing products.

    Mirrors Go ``papi.GetProductsResponse``.
    """

    account_id: str = ""
    contract_id: str = ""
    products: ProductsItems | None = None


# =========================================================================
# include.go  models
# =========================================================================


@dataclass
class Include:
    """An include resource.

    Mirrors Go ``papi.Include``.
    """

    account_id: str = ""
    asset_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    include_id: str = ""
    include_name: str = ""
    include_type: str = ""
    latest_version: int = 0
    production_version: int | None = None
    staging_version: int | None = None


@dataclass
class IncludeItems:
    """Wrapper holding a list of includes.

    Mirrors Go ``papi.IncludeItems``.
    """

    items: list[Include] = field(default_factory=list)


@dataclass
class ParentProperty:
    """A parent property that references an include.

    Mirrors Go ``papi.ParentProperty``.
    """

    account_id: str = ""
    asset_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    production_version: int | None = None
    property_id: str = ""
    property_name: str = ""
    staging_version: int | None = None


@dataclass
class ParentPropertyItems:
    """Wrapper holding a list of parent properties.

    Mirrors Go ``papi.ParentPropertyItems``.
    """

    items: list[ParentProperty] = field(default_factory=list)


@dataclass
class CloneIncludeFrom:
    """Specification for cloning an include from an existing version.

    Mirrors Go ``papi.CloneIncludeFrom``.
    """

    clone_from_version_etag: str = ""
    include_id: str = ""
    version: int = 0


@dataclass
class CreateIncludeResponseHeaders:
    """Response headers returned when creating an include.

    Mirrors Go ``papi.CreateIncludeResponseHeaders``.
    """

    includes_limit_total: str = ""
    includes_limit_remaining: str = ""


@dataclass
class ListIncludesRequest:
    """Request for listing includes.

    Mirrors Go ``papi.ListIncludesRequest``.
    """

    contract_id: str = ""
    group_id: str = ""


@dataclass
class ListIncludesResponse:
    """Response for listing includes.

    Mirrors Go ``papi.ListIncludesResponse``.
    """

    includes: IncludeItems | None = None


@dataclass
class ListIncludeParentsRequest:
    """Request for listing parent properties of an include.

    Mirrors Go ``papi.ListIncludeParentsRequest``.
    """

    include_id: str = ""


@dataclass
class ListIncludeParentsResponse:
    """Response for listing parent properties of an include.

    Mirrors Go ``papi.ListIncludeParentsResponse``.
    """

    properties: ParentPropertyItems | None = None


@dataclass
class GetIncludeRequest:
    """Request for getting a single include.

    Mirrors Go ``papi.GetIncludeRequest``.
    """

    contract_id: str = ""
    group_id: str = ""
    include_id: str = ""


@dataclass
class GetIncludeResponse:
    """Response for getting a single include.

    Mirrors Go ``papi.GetIncludeResponse``.
    """

    includes: IncludeItems | None = None
    include: Include | None = None


@dataclass
class CreateIncludeRequest:
    """Request for creating an include.

    Mirrors Go ``papi.CreateIncludeRequest``.
    """

    contract_id: str = ""
    group_id: str = ""
    include_name: str = ""
    include_type: str = ""
    product_id: str = ""
    rule_format: str = ""
    clone_include_from: CloneIncludeFrom | None = None


@dataclass
class CreateIncludeResponse:
    """Response for creating an include.

    Mirrors Go ``papi.CreateIncludeResponse``.
    """

    include_id: str = ""
    include_link: str = ""


@dataclass
class DeleteIncludeRequest:
    """Request for deleting an include.

    Mirrors Go ``papi.DeleteIncludeRequest``.
    """

    contract_id: str = ""
    group_id: str = ""
    include_id: str = ""


@dataclass
class DeleteIncludeResponse:
    """Response for deleting an include.

    Mirrors Go ``papi.DeleteIncludeResponse``.
    """

    message: str = ""


# =========================================================================
# include_activations.go  models
# =========================================================================


@dataclass
class ComplianceRecordNone:
    """Compliance record for the NONE reason.

    Mirrors Go ``papi.ComplianceRecordNone``.
    Custom MarshalJSON adds ``noncomplianceReason = "NONE"``.
    """

    customer_email: str = ""
    peer_reviewed_by: str = ""
    unit_tested: bool = False
    ticket_id: str = ""


@dataclass
class ComplianceRecordOther:
    """Compliance record for the OTHER reason.

    Mirrors Go ``papi.ComplianceRecordOther``.
    Custom MarshalJSON adds ``noncomplianceReason = "OTHER"``.
    """

    other_noncompliance_reason: str = ""
    ticket_id: str = ""


@dataclass
class ComplianceRecordNoProductionTraffic:
    """Compliance record for NO_PRODUCTION_TRAFFIC.

    Mirrors Go ``papi.ComplianceRecordNoProductionTraffic``.
    Custom MarshalJSON adds ``noncomplianceReason = "NO_PRODUCTION_TRAFFIC"``.
    """

    ticket_id: str = ""


@dataclass
class ComplianceRecordEmergency:
    """Compliance record for EMERGENCY.

    Mirrors Go ``papi.ComplianceRecordEmergency``.
    Custom MarshalJSON adds ``noncomplianceReason = "EMERGENCY"``.
    """

    ticket_id: str = ""


@dataclass
class IncludeActivation:
    """An include activation resource.

    Mirrors Go ``papi.IncludeActivation``.
    """

    activation_id: str = ""
    network: str = ""
    activation_type: str = ""
    status: str = ""
    submit_date: str = ""
    update_date: str = ""
    note: str = ""
    notify_emails: list[str] = field(default_factory=list)
    fma_activation_state: str = ""
    include_id: str = ""
    include_name: str = ""
    include_type: str = ""
    include_version: int = 0
    compliance_record: dict | None = None


@dataclass
class IncludeActivationsRes:
    """Wrapper holding a list of include activations.

    Mirrors Go ``papi.IncludeActivationsRes``.
    """

    items: list[IncludeActivation] = field(default_factory=list)


@dataclass
class ActivateOrDeactivateIncludeRequest:
    """Request for activating or deactivating an include.

    Mirrors Go ``papi.ActivateOrDeactivateIncludeRequest``.
    """

    include_id: str = ""
    version: int = 0
    network: str = ""
    note: str = ""
    notify_emails: list[str] = field(default_factory=list)
    acknowledge_warnings: list[str] = field(default_factory=list)
    acknowledge_all_warnings: bool = False
    ignore_http_errors: bool | None = None
    compliance_record: dict | None = None


# Type aliases matching Go type aliases
ActivateIncludeRequest = ActivateOrDeactivateIncludeRequest
"""Alias for ``ActivateOrDeactivateIncludeRequest``. Mirrors Go type alias."""

DeactivateIncludeRequest = ActivateOrDeactivateIncludeRequest
"""Alias for ``ActivateOrDeactivateIncludeRequest``. Mirrors Go type alias."""


@dataclass
class CancelIncludeActivationRequest:
    """Request for cancelling an include activation.

    Mirrors Go ``papi.CancelIncludeActivationRequest``.
    """

    contract_id: str = ""
    group_id: str = ""
    include_id: str = ""
    activation_id: str = ""


@dataclass
class ActivationIncludeResponse:
    """Response for activating an include.

    Mirrors Go ``papi.ActivationIncludeResponse``.
    """

    activation_id: str = ""
    activation_link: str = ""


@dataclass
class DeactivationIncludeResponse:
    """Response for deactivating an include.

    Mirrors Go ``papi.DeactivationIncludeResponse``.
    """

    activation_id: str = ""
    activation_link: str = ""


@dataclass
class ValidationSummary:
    """Summary of validation results.

    Mirrors Go ``papi.ValidationSummary``.
    """

    complete_percent: float = 0.0
    has_validation_error: bool = False
    has_validation_warning: bool = False
    has_system_error: bool = False
    has_client_error: bool = False
    message_state: str = ""
    error_message: str = ""


@dataclass
class ErrorItem:
    """An individual error item in validation progress.

    Mirrors Go ``papi.ErrorItem``.
    """

    version_id: int = 0
    property_name: str = ""
    version_number: int = 0
    has_validation_error: bool = False
    has_validation_warning: bool = False
    validation_results_link: str = ""


@dataclass
class ValidationProgress:
    """Validation progress container.

    Mirrors Go ``papi.ValidationProgress``.
    """

    error_items: list[ErrorItem] = field(default_factory=list)


@dataclass
class Validations:
    """Validation results for an include activation.

    Mirrors Go ``papi.Validations``.
    """

    validation_summary: ValidationSummary | None = None
    validation_progress_item_list: ValidationProgress | None = None
    network: str = ""


@dataclass
class GetIncludeActivationRequest:
    """Request for getting a single include activation.

    Mirrors Go ``papi.GetIncludeActivationRequest``.
    """

    include_id: str = ""
    activation_id: str = ""


@dataclass
class GetIncludeActivationResponse:
    """Response for getting a single include activation.

    Mirrors Go ``papi.GetIncludeActivationResponse``.
    """

    account_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    activations: IncludeActivationsRes | None = None
    validations: Validations | None = None
    activation: IncludeActivation | None = None


@dataclass
class ListIncludeActivationsRequest:
    """Request for listing include activations.

    Mirrors Go ``papi.ListIncludeActivationsRequest``.
    """

    include_id: str = ""
    contract_id: str = ""
    group_id: str = ""


@dataclass
class ListIncludeActivationsResponse:
    """Response for listing include activations.

    Mirrors Go ``papi.ListIncludeActivationsResponse``.
    """

    account_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    activations: IncludeActivationsRes | None = None


# CancelIncludeActivationResponse is an alias in Go
CancelIncludeActivationResponse = ListIncludeActivationsResponse
"""Alias for ``ListIncludeActivationsResponse``. Mirrors Go type alias."""


# =========================================================================
# include_rule.go  models
# =========================================================================


@dataclass
class UpdateIncludeResponseHeaders:
    """Response headers from updating an include rule tree.

    Mirrors Go ``papi.UpdateIncludeResponseHeaders``.
    """

    elements_per_property_remaining: str = ""
    elements_per_property_total: str = ""
    max_nested_rules_per_include_remaining: str = ""
    max_nested_rules_per_include_total: str = ""


@dataclass
class GetIncludeRuleTreeRequest:
    """Request for getting an include rule tree.

    Mirrors Go ``papi.GetIncludeRuleTreeRequest``.
    """

    contract_id: str = ""
    group_id: str = ""
    include_id: str = ""
    include_version: int = 0
    rule_format: str = ""
    validate_mode: str = ""
    validate_rules: bool = False


@dataclass
class GetIncludeRuleTreeResponse(Response):
    """Response for getting an include rule tree.

    Mirrors Go ``papi.GetIncludeRuleTreeResponse``.
    """

    comments: str = ""
    include_id: str = ""
    include_name: str = ""
    include_type: str = ""
    include_version: int = 0
    rule_format: str = ""
    rules: Rules | None = None


@dataclass
class UpdateIncludeRuleTreeRequest:
    """Request for updating an include rule tree.

    Mirrors Go ``papi.UpdateIncludeRuleTreeRequest``.
    """

    contract_id: str = ""
    dry_run: bool = False
    group_id: str = ""
    include_id: str = ""
    include_version: int = 0
    rules: RulesUpdate | None = None
    validate_mode: str = ""
    validate_rules: bool = False


@dataclass
class UpdateIncludeRuleTreeResponse(Response):
    """Response for updating an include rule tree.

    Mirrors Go ``papi.UpdateIncludeRuleTreeResponse``.
    """

    response_headers: UpdateIncludeResponseHeaders | None = None
    comments: str = ""
    include_id: str = ""
    include_name: str = ""
    include_type: str = ""
    include_version: int = 0
    rule_format: str = ""
    rules: Rules | None = None


# =========================================================================
# include_versions.go  models
# =========================================================================


@dataclass
class IncludeVersion:
    """An include version resource.

    Mirrors Go ``papi.IncludeVersion``.
    """

    include_version: int = 0
    updated_by_user: str = ""
    updated_date: str = ""
    production_status: str = ""
    staging_status: str = ""
    etag: str = ""
    note: str = ""


@dataclass
class Versions:
    """Wrapper holding a list of include versions.

    Mirrors Go ``papi.Versions``.
    """

    items: list[IncludeVersion] = field(default_factory=list)


@dataclass
class IncludeVersionRequest:
    """Embedded version creation parameters.

    Mirrors Go ``papi.IncludeVersionRequest``.
    """

    create_from_version: int = 0
    create_from_version_etag: str = ""


@dataclass
class CreateIncludeVersionRequest:
    """Request for creating a new include version.

    Mirrors Go ``papi.CreateIncludeVersionRequest``.
    """

    include_id: str = ""
    create_from_version: int = 0
    create_from_version_etag: str = ""


@dataclass
class CreateIncludeVersionResponse:
    """Response for creating a new include version.

    Mirrors Go ``papi.CreateIncludeVersionResponse``.
    """

    version_link: str = ""
    version: int = 0


@dataclass
class GetIncludeVersionRequest:
    """Request for getting a single include version.

    Mirrors Go ``papi.GetIncludeVersionRequest``.
    """

    include_id: str = ""
    version: int = 0
    contract_id: str = ""
    group_id: str = ""


@dataclass
class ListIncludeVersionsRequest:
    """Request for listing include versions.

    Mirrors Go ``papi.ListIncludeVersionsRequest``.
    """

    include_id: str = ""
    contract_id: str = ""
    group_id: str = ""


@dataclass
class GetIncludeVersionResponse:
    """Response for getting a single include version.

    Mirrors Go ``papi.GetIncludeVersionResponse``.
    """

    include_id: str = ""
    include_name: str = ""
    account_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    asset_id: str = ""
    include_type: str = ""
    include_versions: Versions | None = None
    include_version: IncludeVersion | None = None


@dataclass
class ListIncludeVersionsResponse:
    """Response for listing include versions.

    Mirrors Go ``papi.ListIncludeVersionsResponse``.
    """

    include_id: str = ""
    include_name: str = ""
    account_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    asset_id: str = ""
    include_type: str = ""
    include_versions: Versions | None = None


@dataclass
class Criteria:
    """Available criteria entry for an include.

    Mirrors Go ``papi.Criteria``.
    """

    name: str = ""
    schema_link: str = ""


@dataclass
class AvailableCriteria:
    """Wrapper holding a list of available criteria.

    Mirrors Go ``papi.AvailableCriteria``.
    """

    items: list[Criteria] = field(default_factory=list)


@dataclass
class ListAvailableCriteriaRequest:
    """Request for listing available criteria for an include.

    Mirrors Go ``papi.ListAvailableCriteriaRequest``.
    """

    include_id: str = ""
    version: int = 0


@dataclass
class AvailableCriteriaResponse:
    """Response for listing available criteria.

    Mirrors Go ``papi.AvailableCriteriaResponse``.
    """

    contract_id: str = ""
    group_id: str = ""
    product_id: str = ""
    rule_format: str = ""
    available_criteria: AvailableCriteria | None = None


@dataclass
class Behavior:
    """Available behavior entry for an include.

    Mirrors Go ``papi.Behavior``.
    """

    name: str = ""
    schema_link: str = ""


@dataclass
class AvailableBehaviors:
    """Wrapper holding a list of available behaviors.

    Mirrors Go ``papi.AvailableBehaviors``.
    """

    items: list[Behavior] = field(default_factory=list)


@dataclass
class ListAvailableBehaviorsRequest:
    """Request for listing available behaviors for an include.

    Mirrors Go ``papi.ListAvailableBehaviorsRequest``.
    """

    include_id: str = ""
    version: int = 0


@dataclass
class AvailableBehaviorsResponse:
    """Response for listing available behaviors.

    Mirrors Go ``papi.AvailableBehaviorsResponse``.
    """

    contract_id: str = ""
    group_id: str = ""
    product_id: str = ""
    rule_format: str = ""
    available_behaviors: AvailableBehaviors | None = None


# =========================================================================
# propertyhostname.go  models
# =========================================================================


@dataclass
class ValidationCname:
    """CNAME used for domain validation.

    Mirrors Go ``papi.ValidationCname``.
    """

    hostname: str = ""
    target: str = ""


@dataclass
class StatusItem:
    """Status entry for certificate staging/production.

    Mirrors Go ``papi.StatusItem``.
    """

    status: str = ""


@dataclass
class CertStatusItem:
    """Certificate status with staging and production details.

    Mirrors Go ``papi.CertStatusItem``.
    """

    validation_cname: ValidationCname | None = None
    staging: list[StatusItem] = field(default_factory=list)
    production: list[StatusItem] = field(default_factory=list)


@dataclass
class CCMCertStatus:
    """CCM certificate status per environment and key type.

    Mirrors Go ``papi.CCMCertStatus``.
    """

    ecdsa_production_status: str = ""
    ecdsa_staging_status: str = ""
    rsa_production_status: str = ""
    rsa_staging_status: str = ""


@dataclass
class CCMCertificates:
    """CCM certificate IDs and links.

    Mirrors Go ``papi.CCMCertificates``.
    """

    ecdsa_cert_id: str = ""
    ecdsa_cert_link: str = ""
    rsa_cert_id: str = ""
    rsa_cert_link: str = ""


@dataclass
class MTLS:
    """mTLS configuration for a hostname.

    Mirrors Go ``papi.MTLS``.
    """

    ca_set_id: str = ""
    ca_set_link: str = ""
    check_client_ocsp: bool = False
    send_ca_set_client: bool = False


@dataclass
class TLSConfiguration:
    """TLS configuration for a hostname.

    Mirrors Go ``papi.TLSConfiguration``.
    """

    cipher_profile: str = ""
    disallowed_tls_versions: list[str] = field(default_factory=list)
    staple_server_ocsp_response: bool = False
    fips_mode: bool = False


@dataclass
class FileContentMethod:
    """File content method for HTTP domain validation.

    Mirrors Go ``papi.FileContentMethod``.
    """

    body: str = ""
    url: str = ""


@dataclass
class RedirectMethod:
    """Redirect method for HTTP domain validation.

    Mirrors Go ``papi.RedirectMethod``.
    """

    http_redirect_from: str = ""
    http_redirect_to: str = ""


@dataclass
class ValidationHTTP:
    """HTTP-based domain validation details.

    Mirrors Go ``papi.ValidationHTTP``.
    """

    file_content_method: FileContentMethod | None = None
    redirect_method: RedirectMethod | None = None


@dataclass
class ValidationTXT:
    """TXT record-based domain validation details.

    Mirrors Go ``papi.ValidationTXT``.
    """

    challenge_token: str = ""
    hostname: str = ""


@dataclass
class DomainOwnershipVerification:
    """Domain ownership verification details on a hostname.

    Mirrors Go ``papi.DomainOwnershipVerification``.
    """

    status: str = ""
    challenge_token_expiry_date: str | None = None
    validation_cname: ValidationCname | None = None
    validation_http: ValidationHTTP | None = None
    validation_txt: ValidationTXT | None = None


@dataclass
class CertStatus:
    """Legacy cert status on a hostname.

    Mirrors Go ``papi.CertStatus`` (standalone struct).
    """

    validation_cname: ValidationCname | None = None
    hostname: str = ""
    target: str = ""
    status: str = ""


@dataclass
class Hostname:
    """A hostname entry on a property version.

    Mirrors Go ``papi.Hostname``.
    """

    cname_type: str = ""
    edge_hostname_id: str = ""
    cname_from: str = ""
    cname_to: str = ""
    cert_provisioning_type: str = ""
    cert_status: CertStatusItem | None = None
    ccm_cert_status: CCMCertStatus | None = None
    ccm_certificates: CCMCertificates | None = None
    mtls: MTLS | None = None
    tls_configuration: TLSConfiguration | None = None
    domain_ownership_verification: DomainOwnershipVerification | None = None


@dataclass
class HostnameResponseItems:
    """Wrapper holding a list of hostnames.

    Mirrors Go ``papi.HostnameResponseItems``.
    """

    items: list[Hostname] = field(default_factory=list)


@dataclass
class HostnameAdd:
    """A hostname to add via PATCH.

    Mirrors Go ``papi.HostnameAdd``.
    """

    cname_from: str = ""
    cname_type: str = ""
    cname_to: str = ""
    cert_provisioning_type: str = ""
    edge_hostname_id: str = ""
    mtls: MTLS | None = None
    tls_configuration: TLSConfiguration | None = None
    ccm_certificates: CCMCertificates | None = None


@dataclass
class GetPropertyVersionHostnamesRequest:
    """Request for getting property version hostnames.

    Mirrors Go ``papi.GetPropertyVersionHostnamesRequest``.
    """

    property_id: str = ""
    property_version: int = 0
    contract_id: str = ""
    group_id: str = ""
    validate_hostnames: bool = False
    include_cert_status: bool = False


@dataclass
class GetPropertyVersionHostnamesResponse:
    """Response for getting property version hostnames.

    Mirrors Go ``papi.GetPropertyVersionHostnamesResponse``.
    """

    account_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    property_id: str = ""
    property_version: int = 0
    etag: str = ""
    property_name: str = ""
    hostnames: HostnameResponseItems | None = None


@dataclass
class UpdatePropertyVersionHostnamesRequest:
    """Request for updating property version hostnames (PUT).

    Mirrors Go ``papi.UpdatePropertyVersionHostnamesRequest``.
    """

    property_id: str = ""
    property_version: int = 0
    contract_id: str = ""
    group_id: str = ""
    validate_hostnames: bool = False
    include_cert_status: bool = False
    hostnames: list[Hostname] = field(default_factory=list)


@dataclass
class UpdatePropertyVersionHostnamesResponse:
    """Response for updating property version hostnames.

    Mirrors Go ``papi.UpdatePropertyVersionHostnamesResponse``.
    """

    account_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    property_id: str = ""
    property_version: int = 0
    etag: str = ""
    property_name: str = ""
    hostnames: HostnameResponseItems | None = None


@dataclass
class PatchPropertyVersionHostnamesRequestBody:
    """Body for patching property version hostnames.

    Mirrors Go ``papi.PatchPropertyVersionHostnamesRequestBody``.
    """

    add: list[HostnameAdd] = field(default_factory=list)
    remove: list[str] = field(default_factory=list)


@dataclass
class PatchPropertyVersionHostnamesRequest:
    """Request for patching property version hostnames (PATCH).

    Mirrors Go ``papi.PatchPropertyVersionHostnamesRequest``.
    """

    property_id: str = ""
    property_version: int = 0
    contract_id: str = ""
    group_id: str = ""
    validate_hostnames: bool = False
    include_cert_status: bool = False
    body: PatchPropertyVersionHostnamesRequestBody | None = None


@dataclass
class PatchPropertyVersionHostnamesResponse:
    """Response for patching property version hostnames.

    Mirrors Go ``papi.PatchPropertyVersionHostnamesResponse``.
    """

    account_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    etag: str = ""
    property_id: str = ""
    property_name: str = ""
    property_version: int = 0
    hostnames: HostnameResponseItems | None = None


@dataclass
class HostnameHistoryItem:
    """A single entry in hostname audit history.

    Mirrors Go ``papi.HostnameHistoryItem``.
    """

    action: str = ""
    cert_provisioning_type: str = ""
    cname_to: str = ""
    contract_id: str = ""
    edge_hostname_id: str = ""
    group_id: str = ""
    network: str = ""
    property_id: str = ""
    timestamp: str = ""
    user: str = ""


@dataclass
class HostnameHistory:
    """Wrapper holding hostname audit history items.

    Mirrors Go ``papi.HostnameHistory``.
    """

    items: list[HostnameHistoryItem] = field(default_factory=list)


@dataclass
class GetAuditHistoryRequest:
    """Request for getting hostname audit history.

    Mirrors Go ``papi.GetAuditHistoryRequest``.
    """

    hostname: str = ""


@dataclass
class GetAuditHistoryResponse:
    """Response for getting hostname audit history.

    Mirrors Go ``papi.GetAuditHistoryResponse``.
    """

    hostname: str = ""
    history: HostnameHistory | None = None


# =========================================================================
# propertyversion.go  models
# =========================================================================


@dataclass
class PropertyVersionGetItem:
    """A property version resource.

    Mirrors Go ``papi.PropertyVersionGetItem``.
    """

    property_version: int = 0
    updated_by_user: str = ""
    updated_date: str = ""
    production_status: str = ""
    staging_status: str = ""
    etag: str = ""
    production_etag: str = ""
    staging_etag: str = ""
    note: str = ""
    rule_format: str = ""


@dataclass
class PropertyVersionItems:
    """Wrapper holding a list of property versions.

    Mirrors Go ``papi.PropertyVersionItems``.
    """

    items: list[PropertyVersionGetItem] = field(default_factory=list)


@dataclass
class GetPropertyVersionsRequest:
    """Request for listing property versions.

    Mirrors Go ``papi.GetPropertyVersionsRequest``.
    """

    property_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    limit: int = 0
    offset: int = 0


@dataclass
class GetPropertyVersionsResponse:
    """Response for listing property versions.

    Mirrors Go ``papi.GetPropertyVersionsResponse``.
    """

    property_id: str = ""
    property_name: str = ""
    account_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    asset_id: str = ""
    versions: PropertyVersionItems | None = None


@dataclass
class GetPropertyVersionRequest:
    """Request for getting a single property version.

    Mirrors Go ``papi.GetPropertyVersionRequest``.
    """

    property_id: str = ""
    property_version: int = 0
    contract_id: str = ""
    group_id: str = ""


@dataclass
class PropertyVersionCreate:
    """Body for creating a new property version.

    Mirrors Go ``papi.PropertyVersionCreate``.
    """

    create_from_version: int = 0
    create_from_version_etag: str = ""


@dataclass
class CreatePropertyVersionRequest:
    """Request for creating a new property version.

    Mirrors Go ``papi.CreatePropertyVersionRequest``.
    """

    property_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    version: PropertyVersionCreate | None = None


@dataclass
class CreatePropertyVersionResponse:
    """Response for creating a new property version.

    Mirrors Go ``papi.CreatePropertyVersionResponse``.
    """

    version_link: str = ""


@dataclass
class GetLatestVersionRequest:
    """Request for getting the latest property version.

    Mirrors Go ``papi.GetLatestVersionRequest``.
    """

    property_id: str = ""
    activated_on: str = ""
    contract_id: str = ""
    group_id: str = ""


@dataclass
class GetAvailableItemsRequest:
    """Base request for available behaviors/criteria on a property.

    Mirrors Go ``papi.GetAvailableItemsRequest``.
    """

    property_id: str = ""
    property_version: int = 0
    contract_id: str = ""
    group_id: str = ""


# Type aliases matching Go
GetAvailableBehaviorsRequest = GetAvailableItemsRequest
"""Alias for ``GetAvailableItemsRequest``. Mirrors Go type alias."""

GetAvailableCriteriaRequest = GetAvailableItemsRequest
"""Alias for ``GetAvailableItemsRequest``. Mirrors Go type alias."""

GetBehaviorsResponse = AvailableBehaviorsResponse
"""Alias for ``AvailableBehaviorsResponse``. Mirrors Go type alias."""

GetCriteriaResponse = AvailableCriteriaResponse
"""Alias for ``AvailableCriteriaResponse``. Mirrors Go type alias."""


@dataclass
class ExternalIncludeData:
    """Include data for externally available/referenced includes.

    Mirrors Go ``papi.ExternalIncludeData``.
    """

    include_id: str = ""
    include_name: str = ""
    include_type: str = ""
    file_name: str = ""
    product_name: str = ""
    rule_format: str = ""


@dataclass
class ListAvailableReferencedIncludesRequest:
    """Request for listing available or referenced includes for a property.

    Mirrors Go ``papi.ListAvailableReferencedIncludesRequest``.
    """

    property_id: str = ""
    property_version: int = 0
    contract_id: str = ""
    group_id: str = ""


# Type aliases matching Go
ListAvailableIncludesRequest = ListAvailableReferencedIncludesRequest
"""Alias for ``ListAvailableReferencedIncludesRequest``. Mirrors Go."""

ListReferencedIncludesRequest = ListAvailableReferencedIncludesRequest
"""Alias for ``ListAvailableReferencedIncludesRequest``. Mirrors Go."""


@dataclass
class ListAvailableIncludesResponse:
    """Response for listing available includes for a property.

    Mirrors Go ``papi.ListAvailableIncludesResponse``.
    """

    available_includes: list[ExternalIncludeData] = field(default_factory=list)


@dataclass
class ListReferencedIncludesResponse:
    """Response for listing referenced includes for a property.

    Mirrors Go ``papi.ListReferencedIncludesResponse``.
    """

    includes: IncludeItems | None = None


# =========================================================================
# active_property_hostname.go  models
# =========================================================================


@dataclass
class HostnameItem:
    """Hostname item in active property hostname responses.

    Mirrors Go ``papi.HostnameItem``.
    """

    ccm_cert_status: CCMCertStatus | None = None
    ccm_certificates: CCMCertificates | None = None
    cert_status: CertStatusItem | None = None
    cname_from: str = ""
    cname_type: str = ""
    mtls: MTLS | None = None
    production_cert_type: str = ""
    production_cname_to: str = ""
    production_edge_hostname_id: str = ""
    staging_cert_type: str = ""
    staging_cname_to: str = ""
    staging_edge_hostname_id: str = ""
    tls_configuration: TLSConfiguration | None = None


@dataclass
class HostnameDiffItem:
    """Hostname diff item comparing staging and production.

    Mirrors Go ``papi.HostnameDiffItem``.
    """

    cname_from: str = ""
    production_cert_provisioning_type: str = ""
    production_cname_to: str = ""
    production_cname_type: str = ""
    production_edge_hostname_id: str = ""
    staging_cert_provisioning_type: str = ""
    staging_cname_to: str = ""
    staging_cname_type: str = ""
    staging_edge_hostname_id: str = ""


@dataclass
class ActiveAccountHostnameItem:
    """Hostname item in account-wide active hostname listing.

    Mirrors Go ``papi.ActiveAccountHostnameItem``.
    """

    cname_from: str = ""
    contract_id: str = ""
    group_id: str = ""
    latest_version: int = 0
    property_id: str = ""
    property_name: str = ""
    property_type: str = ""
    production_cert_type: str | None = None
    production_cname_to: str | None = None
    production_cname_type: str | None = None
    production_edge_hostname_id: str | None = None
    production_product_id: str | None = None
    staging_cert_type: str | None = None
    staging_cname_to: str | None = None
    staging_cname_type: str | None = None
    staging_edge_hostname_id: str | None = None
    staging_product_id: str | None = None


@dataclass
class ActivePropertyHostname:
    """Active property hostname details.

    Mirrors Go ``papi.ActivePropertyHostname`` export from the schema,
    mapping to the response structure of active property hostname items.
    """

    hostname: str = ""
    hostname_id: str = ""
    property_id: str = ""
    staging_details: HostnameItem | None = None
    production_details: HostnameItem | None = None


@dataclass
class HostnamesResponseItems:
    """Wrapper holding active property hostname items with pagination.

    Mirrors Go ``papi.HostnamesResponseItems`` (used by
    ``ListActivePropertyHostnamesResponse``).
    """

    items: list[HostnameItem] = field(default_factory=list)
    current_item_count: int = 0
    next_link: str | None = None
    previous_link: str | None = None
    total_items: int = 0


@dataclass
class HostnamesDiffResponseItems:
    """Wrapper holding hostname diff items with pagination.

    Mirrors Go ``papi.HostnamesDiffResponseItems``.
    """

    items: list[HostnameDiffItem] = field(default_factory=list)
    current_item_count: int = 0
    next_link: str | None = None
    previous_link: str | None = None
    total_items: int = 0


@dataclass
class ActiveAccountHostnames:
    """Wrapper holding active account hostname items with pagination.

    Mirrors Go ``papi.ActiveAccountHostnames``.
    """

    items: list[ActiveAccountHostnameItem] = field(default_factory=list)
    current_item_count: int = 0
    next_link: str | None = None
    previous_link: str | None = None
    total_items: int = 0


@dataclass
class ListActivePropertyHostnamesRequest:
    """Request for listing active property hostnames.

    Mirrors Go ``papi.ListActivePropertyHostnamesRequest``.
    """

    property_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    offset: int = 0
    limit: int = 0
    sort: str = ""
    filter: str = ""


@dataclass
class ListActivePropertyHostnamesResponse:
    """Response for listing active property hostnames.

    Mirrors Go ``papi.ListActivePropertyHostnamesResponse``.
    """

    hostnames: HostnamesResponseItems | None = None
    account_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    total_results: int = 0
    result_count: int = 0


@dataclass
class GetActivePropertyHostnamesDiffRequest:
    """Request for getting active property hostname diffs.

    Mirrors Go ``papi.GetActivePropertyHostnamesDiffRequest``.
    """

    property_id: str = ""
    offset: int = 0
    limit: int = 0
    contract_id: str = ""
    group_id: str = ""


@dataclass
class GetActivePropertyHostnamesDiffResponse:
    """Response for getting active property hostname diffs.

    Mirrors Go ``papi.GetActivePropertyHostnamesDiffResponse``.
    """

    account_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    property_id: str = ""
    hostnames: HostnamesDiffResponseItems | None = None


@dataclass
class ListActiveAccountHostnamesRequest:
    """Request for listing all active hostnames across an account.

    Mirrors Go ``papi.ListActiveAccountHostnamesRequest``.
    """

    offset: int = 0
    limit: int = 0
    sort: str = ""
    hostname: str = ""
    cname_to: str = ""
    network: str = ""
    contract_id: str = ""
    group_id: str = ""


@dataclass
class ListActiveAccountHostnamesResponse:
    """Response for listing all active hostnames across an account.

    Mirrors Go ``papi.ListActiveAccountHostnamesResponse``.
    """

    account_id: str = ""
    available_sort: list[str] = field(default_factory=list)
    current_sort: str = ""
    default_sort: str = ""
    hostnames: ActiveAccountHostnames | None = None


# =========================================================================
# domain_ownership_validation.go  models
# =========================================================================


@dataclass
class ValidateDomainsOwnershipRequestBody:
    """Body for domain ownership validation requests.

    Mirrors Go ``papi.ValidateDomainsOwnershipRequestBody``.
    """

    hostnames: list[str] = field(default_factory=list)


@dataclass
class HostnameValidationDetails:
    """Validation details for a single hostname.

    Mirrors Go ``papi.HostnameValidationDetails``.
    """

    hostname: str = ""
    domain_validation_status: str = ""
    validation_scope: str | None = None
    challenge_token_expiry_date: str | None = None
    validation_cname: ValidationCname | None = None
    validation_txt: ValidationTXT | None = None
    validation_http: ValidationHTTP | None = None


@dataclass
class ValidateDomainsOwnershipRequest:
    """Request for validating domain ownership.

    Mirrors Go ``papi.ValidateDomainsOwnershipRequest``.
    """

    property_id: str = ""
    contract_id: str = ""
    group_id: str = ""


@dataclass
class ValidateDomainsOwnershipResponse:
    """Response for domain ownership validation.

    Mirrors Go ``papi.ValidateDomainsOwnershipResponse``.
    """

    challenges: list[HostnameValidationDetails] = field(default_factory=list)


# =========================================================================
# property_hostname_activation.go  models
# =========================================================================


@dataclass
class PropertyHostnameItem:
    """Hostname item within a property hostname activation.

    Mirrors Go ``papi.PropertyHostnameItem``.
    """

    cert_provisioning_type: str = ""
    cname_from: str = ""
    cname_to: str = ""
    edge_hostname_id: str = ""
    cert_status: CertStatusItem | None = None
    action: str = ""


@dataclass
class HostnameActivationListItem:
    """Item in a property hostname activation list.

    Mirrors Go ``papi.HostnameActivationListItem``.
    """

    activation_type: str = ""
    hostname_activation_id: str = ""
    property_name: str = ""
    property_id: str = ""
    network: str = ""
    status: str = ""
    submit_date: str = ""
    update_date: str = ""
    note: str = ""
    notify_emails: list[str] = field(default_factory=list)


@dataclass
class HostnameActivationGetItem:
    """Detailed item from getting a single property hostname activation.

    Mirrors Go ``papi.HostnameActivationGetItem``.
    """

    activation_type: str = ""
    hostname_activation_id: str = ""
    property_name: str = ""
    property_id: str = ""
    network: str = ""
    status: str = ""
    submit_date: str = ""
    update_date: str = ""
    note: str = ""
    notify_emails: list[str] = field(default_factory=list)
    hostnames: list[PropertyHostnameItem] = field(default_factory=list)


@dataclass
class HostnameActivationCancelItem:
    """Item from cancelling a property hostname activation.

    Mirrors Go ``papi.HostnameActivationCancelItem``.
    """

    activation_type: str = ""
    hostname_activation_id: str = ""
    property_name: str = ""
    property_id: str = ""
    network: str = ""
    status: str = ""
    submit_date: str = ""
    update_date: str = ""
    note: str = ""
    notify_emails: list[str] = field(default_factory=list)
    property_version: int = 0


@dataclass
class HostnameActivationsList:
    """Wrapper holding property hostname activation list items.

    Mirrors Go ``papi.HostnameActivationsList``.
    """

    items: list[HostnameActivationListItem] = field(default_factory=list)
    total_items: int = 0
    current_item_count: int = 0
    next_link: str | None = None
    previous_link: str | None = None


@dataclass
class PropertyHostnameActivation:
    """Property hostname activation resource.

    Mirrors Go ``papi.PropertyHostnameActivation`` export schema.
    """

    activation_id: str = ""
    status: str = ""
    submit_date: str = ""
    update_date: str = ""
    submitted_hostnames: list[PropertyHostnameItem] = field(
        default_factory=list
    )
    note: str = ""
    network: str = ""
    notify_emails: list[str] = field(default_factory=list)


@dataclass
class GetPropertyHostnameActivationRequest:
    """Request for getting a single property hostname activation.

    Mirrors Go ``papi.GetPropertyHostnameActivationRequest``.
    """

    property_id: str = ""
    hostname_activation_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    include_hostnames: bool = False


@dataclass
class GetPropertyHostnameActivationResponse:
    """Response for getting a single property hostname activation.

    Mirrors Go ``papi.GetPropertyHostnameActivationResponse``.
    """

    account_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    hostname_activation: HostnameActivationGetItem | None = None


@dataclass
class ListPropertyHostnameActivationsRequest:
    """Request for listing property hostname activations.

    Mirrors Go ``papi.ListPropertyHostnameActivationsRequest``.
    """

    property_id: str = ""
    offset: int = 0
    limit: int = 0
    contract_id: str = ""
    group_id: str = ""


@dataclass
class ListPropertyHostnameActivationsResponse:
    """Response for listing property hostname activations.

    Mirrors Go ``papi.ListPropertyHostnameActivationsResponse``.
    """

    account_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    hostname_activations: HostnameActivationsList | None = None


@dataclass
class CancelPropertyHostnameActivationRequest:
    """Request for cancelling a property hostname activation.

    Mirrors Go ``papi.CancelPropertyHostnameActivationRequest``.
    """

    property_id: str = ""
    hostname_activation_id: str = ""
    contract_id: str = ""
    group_id: str = ""


@dataclass
class CancelPropertyHostnameActivationResponse:
    """Response for cancelling a property hostname activation.

    Mirrors Go ``papi.CancelPropertyHostnameActivationResponse``.
    """

    account_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    hostname_activation: HostnameActivationCancelItem | None = None


# =========================================================================
# property_hostname_bucket.go  models
# =========================================================================


@dataclass
class PatchPropertyHostnameBucketAdd:
    """A hostname to add in a hostname bucket patch.

    Mirrors Go ``papi.PatchPropertyHostnameBucketAdd``.
    """

    edge_hostname_id: str = ""
    cert_provisioning_type: str = ""
    cname_type: str = ""
    cname_from: str = ""


@dataclass
class PatchHostnameItem:
    """A hostname item returned from a hostname bucket patch.

    Mirrors Go ``papi.PatchHostnameItem``.
    """

    cert_provisioning_type: str = ""
    cname_from: str = ""
    cname_to: str = ""
    cname_type: str = ""
    edge_hostname_id: str = ""
    cert_status: CertStatusItem | None = None
    action: str = ""


@dataclass
class PatchPropertyHostnameBucketBody:
    """Body for a hostname bucket patch request.

    Mirrors Go ``papi.PatchPropertyHostnameBucketBody``.
    """

    add: list[PatchPropertyHostnameBucketAdd] = field(default_factory=list)
    remove: list[str] = field(default_factory=list)
    network: str = ""
    notify_emails: list[str] = field(default_factory=list)
    note: str = ""


@dataclass
class PatchPropertyHostnameBucketRequest:
    """Request for patching a property hostname bucket.

    Mirrors Go ``papi.PatchPropertyHostnameBucketRequest``.
    """

    property_id: str = ""
    contract_id: str = ""
    group_id: str = ""
    add: list[PatchPropertyHostnameBucketAdd] = field(default_factory=list)
    remove: list[str] = field(default_factory=list)


@dataclass
class PatchPropertyHostnameBucketResponse:
    """Response for patching a property hostname bucket.

    Mirrors Go ``papi.PatchPropertyHostnameBucketResponse``.
    """
