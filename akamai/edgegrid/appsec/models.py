"""Request and response models for the Application Security API.

This module defines all request and response model classes mirroring the Go
AkamaiOPEN-edgegrid-golang/v12/pkg/appsec structs field-for-field.
Every Go struct is represented as a Python dataclass with identical field names
(converted to snake_case) and types (mapped per the Go-to-Python type mapping).
"""
# pylint: disable=too-many-lines
# pylint: disable=too-many-instance-attributes

from dataclasses import dataclass, field
from typing import Any


# =============================================================================
# Constants
# =============================================================================

# RulesetType constants (from common_const.go)
RULESET_TYPE_ACTIVE: str = "active"
RULESET_TYPE_EVALUATION: str = "evaluation"

# ActionType constants (from common_const.go)
ACTION_TYPE_DENY: str = "deny"
ACTION_TYPE_ALERT: str = "alert"
ACTION_TYPE_NONE: str = "none"

# ActivationValue constants (from activations.go)
ACTIVATION_TYPE_ACTIVATE: str = "ACTIVATE"
ACTIVATION_TYPE_DEACTIVATE: str = "DEACTIVATE"

# NetworkValue constants (from activations.go)
NETWORK_PRODUCTION: str = "PRODUCTION"
NETWORK_STAGING: str = "STAGING"

# StatusValue constants (from activations.go)
STATUS_ACTIVE: str = "ACTIVATED"
STATUS_IN_PROGRESS: str = "ACTIVATION_IN_PROGRESS"
STATUS_INACTIVE: str = "INACTIVE"
STATUS_PENDING: str = "RECEIVED"
STATUS_ABORTED: str = "ABORTED"
STATUS_FAILED: str = "FAILED"
STATUS_DEACTIVATED: str = "DEACTIVATED"
STATUS_PENDING_DEACTIVATION: str = "PENDING_DEACTIVATION"
STATUS_NEW: str = "NEW"

# AttackPayloadType constants (from advanced_settings_attack_payload_logging.go)
ATTACK_PAYLOAD: str = "ATTACK_PAYLOAD"
ATTACK_PAYLOAD_NONE: str = "NONE"

# RequestBodySizeLimit constants (from advanced_settings_request_body.go)
REQUEST_BODY_SIZE_DEFAULT: str = "default"
REQUEST_BODY_SIZE_8KB: str = "8"
REQUEST_BODY_SIZE_16KB: str = "16"
REQUEST_BODY_SIZE_32KB: str = "32"


# =============================================================================
# Type aliases
# =============================================================================

# CustomRuleConditionsValue is a type alias for list[str]
# Mirrors Go: type CustomRuleConditionsValue []string
CustomRuleConditionsValue = list[str]

# CustomRuleConditionsName is a type alias for list[str]
# Mirrors Go: type CustomRuleConditionsName []string
CustomRuleConditionsName = list[str]

# ConditionsValue is a type alias for list[str]
# Mirrors Go: type ConditionsValue []string
ConditionsValue = list[str]

# RuleConditions is a type alias for list[dict]
# Mirrors Go: type RuleConditions []struct{...} from rule.go
RuleConditions = list[dict]

# SpecificHeaderCookieParamXMLOrJSONNames is a type alias for list[dict]
# Mirrors Go: type from attack_group.go
SpecificHeaderCookieParamXMLOrJSONNames = list[dict]

# RuleData is a type alias for list[dict]
# Mirrors Go: type RuleData []struct{ID, Title}
RuleData = list[dict]

# GroupData is a type alias for list[dict]
# Mirrors Go: type GroupData []struct{Group, GroupName}
GroupData = list[dict]

# Evidences is a type alias for list[dict]
# Mirrors Go: type Evidences []struct{HostEvidences, PathEvidences, UserDataEvidences}
Evidences = list[dict]

# AttackPayloadType is a type alias for str
# Mirrors Go: type AttackPayloadType string
AttackPayloadType = str

# RequestBodySizeLimit is a type alias for str
# Mirrors Go: type RequestBodySizeLimit string
RequestBodySizeLimit = str

# ReputationProfileActionsexp is a type alias for list[dict]
# Mirrors Go: type ReputationProfileActionsexp []struct{Action, ID}
ReputationProfileActionsexp = list[dict]

# RatePolicyActionsexp is a type alias for list[dict]
# Mirrors Go: type RatePolicyActionsexp []struct{ID, Ipv4Action, Ipv6Action}
RatePolicyActionsexp = list[dict]

# CustomDenyListexp is a type alias for list[dict]
# Mirrors Go: type CustomDenyListexp []struct{...}
CustomDenyListexp = list[dict]

# CustomRuleActionsexp is a type alias for list[dict]
# Mirrors Go: type CustomRuleActionsexp []struct{Action, ID}
CustomRuleActionsexp = list[dict]

# AtomicConditionsexp is a type alias for list[dict]
# Mirrors Go: type AtomicConditionsexp []struct{...}
AtomicConditionsexp = list[dict]

# HeaderCookieOrParamValuesattackgroup is a type alias for list[dict]
# Mirrors Go: type from export_configuration.go
HeaderCookieOrParamValuesattackgroup = list[dict]

# ConditionsExp is a type alias for list[dict]
# Mirrors Go: type ConditionsExp []struct{...}
ConditionsExp = list[dict]

# RatePoliciesPathValues is a type alias for list[str]
# Mirrors Go: type RatePoliciesPathValues []string
RatePoliciesPathValues = list[str]

# RatePoliciesQueryParameters is a type alias for list[dict]
# Mirrors Go: type RatePoliciesQueryParameters []struct{...}
RatePoliciesQueryParameters = list[dict]

# RatePoliciesQueryParametersValues is a type alias for list[str]
# Mirrors Go: type RatePoliciesQueryParametersValues []string
RatePoliciesQueryParametersValues = list[str]

# RulesetsRules is a type alias for list[dict]
# Mirrors Go: type RulesetsRules []struct{...}
RulesetsRules = list[dict]

# ClientReputationReputationProfileActions is a type alias for list[dict]
# Mirrors Go: type from export_configuration.go
ClientReputationReputationProfileActions = list[dict]

# SecurityPoliciesRatePolicyActions is a type alias for list[dict]
# Mirrors Go: type from export_configuration.go
SecurityPoliciesRatePolicyActions = list[dict]

# SpecificHeaderCookieOrParamNamesPtr is a type alias for list[dict]
# Mirrors Go: type from rule.go
SpecificHeaderCookieOrParamNamesPtr = list[dict]

# AttackGroupAdvancedCriteria is a type alias for list[dict]
# Mirrors Go: type from attack_group.go
AttackGroupAdvancedCriteria = list[dict]

# AttackGroupSpecificHeaderCookieOrParamNameValAdvanced is a type alias for list[dict]
AttackGroupSpecificHeaderCookieOrParamNameValAdvanced = list[dict]

# AttackGroupSpecificHeaderCookieParamXMLOrJSONNamesAdvanced is a type alias for list[dict]
AttackGroupSpecificHeaderCookieParamXMLOrJSONNamesAdvanced = list[dict]

# AttackGroupHeaderCookieOrParamValuesAdvanced is a type alias for list[dict]
AttackGroupHeaderCookieOrParamValuesAdvanced = list[dict]

# AttackGroupException is a type alias for list[dict]
# Mirrors Go: type AttackGroupException struct with
# SpecificHeaderCookieParamXMLOrJSONNames
AttackGroupException = list[dict]


# =============================================================================
# Activations (from activations.go)
# =============================================================================


@dataclass
class ActivationConfigs:
    """Helper struct for activation config items.

    Mirrors Go ActivationConfigs struct from activations.go.
    """
    config_id: int = 0  # json:"configId"
    config_version: int = 0  # json:"configVersion"


@dataclass
class GetActivationsRequest:
    """Request for getting activation status.

    Mirrors Go GetActivationsRequest struct from activations.go.
    """
    activation_id: int = 0  # json:"activationID"


@dataclass
class GetActivationsResponse:
    """Response from getting activation status.

    Mirrors Go GetActivationsResponse struct from activations.go.
    """
    dispatch_count: int = 0  # json:"dispatchCount"
    activation_id: int = 0  # json:"activationId"
    action: str = ""  # json:"action"
    status: str = ""  # json:"status"
    network: str = ""  # json:"network"
    estimate: str = ""  # json:"estimate"
    created_by: str = ""  # json:"createdBy"
    create_date: str = ""  # json:"createDate" (time.Time -> str)
    activation_configs: list[dict] = field(default_factory=list)  # json:"activationConfigs"


@dataclass
class Activation:
    """Nested activation record.

    Mirrors Go Activation struct from activations.go.
    """
    activation_id: int = 0  # json:"activationId"
    version: int = 0  # json:"version"
    status: str = ""  # json:"status"
    network: str = ""  # json:"network"
    activated_by: str = ""  # json:"activatedBy"
    activation_date: str = ""  # json:"activationDate" (time.Time -> str)
    notes: str = ""  # json:"notes"
    notification_emails: list[str] = field(default_factory=list)  # json:"notificationEmails"


@dataclass
class GetActivationHistoryRequest:
    """Request for getting activation history.

    Mirrors Go GetActivationHistoryRequest struct from activations.go.
    """
    config_id: int = 0  # json:"-" (path parameter)


@dataclass
class GetActivationHistoryResponse:
    """Response from getting activation history.

    Mirrors Go GetActivationHistoryResponse struct from activations.go.
    """
    config_id: int = 0  # json:"configId"
    activation_history: list[dict] = field(default_factory=list)  # json:"activationHistory"


@dataclass
class CreateActivationsRequest:
    """Request for creating an activation.

    Mirrors Go CreateActivationsRequest struct from activations.go.
    """
    action: str = ""  # json:"action"
    network: str = ""  # json:"network"
    note: str = ""  # json:"note"
    notification_emails: list[str] = field(default_factory=list)  # json:"notificationEmails"
    activation_configs: list[dict] = field(default_factory=list)  # json:"activationConfigs"


@dataclass
class CreateActivationsResponse:
    """Response from creating an activation.

    Mirrors Go CreateActivationsResponse struct from activations.go.
    """
    dispatch_count: int = 0  # json:"dispatchCount"
    activation_id: int = 0  # json:"activationId"
    action: str = ""  # json:"action"
    status: str = ""  # json:"status"
    network: str = ""  # json:"network"


@dataclass
class RemoveActivationsRequest:
    """Request for removing an activation.

    Mirrors Go RemoveActivationsRequest struct from activations.go.
    """
    activation_id: int = 0  # json:"activationID"
    action: str = ""  # json:"action"
    network: str = ""  # json:"network"
    note: str = ""  # json:"note"
    notification_emails: list[str] = field(default_factory=list)  # json:"notificationEmails"
    activation_configs: list[dict] = field(default_factory=list)  # json:"activationConfigs"


@dataclass
class RemoveActivationsResponse:
    """Response from removing an activation.

    Mirrors Go RemoveActivationsResponse struct from activations.go.
    """
    dispatch_count: int = 0  # json:"dispatchCount"
    activation_id: int = 0  # json:"activationId"
    action: str = ""  # json:"action"
    status: str = ""  # json:"status"
    network: str = ""  # json:"network"


# =============================================================================
# Configuration (from configuration.go)
# =============================================================================


@dataclass
class GetConfigurationsRequest:
    """Request for listing configurations.

    Mirrors Go GetConfigurationsRequest struct from configuration.go.
    """
    config_id: int = 0  # json:"-" (path parameter)
    name: str = ""  # json:"-" (query parameter)


@dataclass
class GetConfigurationsResponse:
    """Response from listing configurations.

    Mirrors Go GetConfigurationsResponse struct from configuration.go.
    """
    configurations: list[dict] = field(default_factory=list)  # json:"configurations"


@dataclass
class GetConfigurationRequest:
    """Request for getting a single configuration.

    Mirrors Go GetConfigurationRequest struct from configuration.go.
    """
    config_id: int = 0  # json:"-" (path parameter)


@dataclass
class GetConfigurationResponse:
    """Response from getting a single configuration.

    Mirrors Go GetConfigurationResponse struct from configuration.go.
    """
    description: str = ""  # json:"description"
    file_type: str = ""  # json:"fileType"
    id: int = 0  # json:"id"
    latest_version: int = 0  # json:"latestVersion"
    name: str = ""  # json:"name"
    staging_version: int | None = None  # json:"stagingVersion"
    target_product: str = ""  # json:"targetProduct"
    production_hostnames: list[str] = field(default_factory=list)  # json:"productionHostnames"
    production_version: int | None = None  # json:"productionVersion"


@dataclass
class CreateConfigurationRequest:
    """Request for creating a configuration.

    Mirrors Go CreateConfigurationRequest struct from configuration.go.
    """
    name: str = ""  # json:"name"
    description: str = ""  # json:"description"
    contract_id: str = ""  # json:"contractId"
    group_id: int = 0  # json:"groupId"
    hostnames: list[str] = field(default_factory=list)  # json:"hostNames"


@dataclass
class CreateConfigurationResponse:
    """Response from creating a configuration.

    Mirrors Go CreateConfigurationResponse (empty body, ID from Location header).
    """


@dataclass
class UpdateConfigurationRequest:
    """Request for updating a configuration.

    Mirrors Go UpdateConfigurationRequest struct from configuration.go.
    """
    config_id: int = 0  # json:"-" (path parameter)
    name: str = ""  # json:"name"
    description: str = ""  # json:"description"


@dataclass
class UpdateConfigurationResponse:
    """Response from updating a configuration.

    Mirrors Go UpdateConfigurationResponse struct from configuration.go.
    """


@dataclass
class RemoveConfigurationRequest:
    """Request for removing a configuration.

    Mirrors Go RemoveConfigurationRequest struct from configuration.go.
    """
    config_id: int = 0  # json:"-" (path parameter)


@dataclass
class RemoveConfigurationResponse:
    """Response from removing a configuration.

    Mirrors Go RemoveConfigurationResponse struct from configuration.go.
    """


# =============================================================================
# Configuration Clone (from configuration_clone.go)
# =============================================================================


@dataclass
class GetConfigurationCloneRequest:
    """Request for getting configuration clone details.

    Mirrors Go GetConfigurationCloneRequest struct from configuration_clone.go.
    """
    config_id: int = 0  # json:"configId"
    config_name: str = ""  # json:"configName"
    version: int = 0  # json:"version"
    version_notes: str = ""  # json:"versionNotes"
    create_date: str = ""  # json:"createDate" (time.Time -> str)
    created_by: str = ""  # json:"createdBy"
    based_on: int = 0  # json:"basedOn"
    production: dict = field(default_factory=dict)  # json:"production" (anonymous struct)
    staging: dict = field(default_factory=dict)  # json:"staging" (anonymous struct)


@dataclass
class GetConfigurationCloneResponse:
    """Response from getting configuration clone details.

    Mirrors Go GetConfigurationCloneResponse struct from configuration_clone.go.
    """
    config_id: int = 0  # json:"configId"
    config_name: str = ""  # json:"configName"
    version: int = 0  # json:"version"
    version_notes: str = ""  # json:"versionNotes"
    create_date: str = ""  # json:"createDate" (time.Time -> str)
    created_by: str = ""  # json:"createdBy"
    based_on: int = 0  # json:"basedOn"
    production: dict = field(default_factory=dict)  # json:"production"
    staging: dict = field(default_factory=dict)  # json:"staging"


@dataclass
class CreateConfigurationCloneRequest:
    """Request for creating a configuration clone.

    Mirrors Go CreateConfigurationCloneRequest struct from configuration_clone.go.
    """
    name: str = ""  # json:"name"
    description: str = ""  # json:"description"
    contract_id: str = ""  # json:"contractId"
    group_id: int = 0  # json:"groupId"
    hostnames: list[str] = field(default_factory=list)  # json:"hostNames"
    create_from: dict = field(default_factory=dict)  # json:"createFrom" (anonymous struct)


@dataclass
class CreateConfigurationCloneResponse:
    """Response from creating a configuration clone.

    Mirrors Go CreateConfigurationCloneResponse struct from configuration_clone.go.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    description: str = ""  # json:"description"
    name: str = ""  # json:"name"


# =============================================================================
# Configuration Version (from configuration_version.go)
# =============================================================================


@dataclass
class EnvironmentStatus:
    """Environment status info for staging/production.

    Mirrors Go EnvironmentStatus struct from configuration_version.go.
    """
    status: str = ""  # json:"status"
    time: str = ""  # json:"time" (time.Time -> str)


@dataclass
class GetConfigurationVersionsRequest:
    """Request for listing configuration versions.

    Mirrors Go GetConfigurationVersionsRequest struct from configuration_version.go.
    """
    config_id: int = 0  # json:"configId"
    config_version: int = 0  # json:"-" (query parameter)


@dataclass
class GetConfigurationVersionsResponse:
    """Response from listing configuration versions.

    Mirrors Go GetConfigurationVersionsResponse struct.
    """
    config_id: int = 0  # json:"configId"
    config_name: str = ""  # json:"configName"
    last_created_version: int = 0  # json:"lastCreatedVersion"
    page: int = 0  # json:"page"
    page_size: int = 0  # json:"pageSize"
    total_size: int = 0  # json:"totalSize"
    version_list: list[dict] = field(default_factory=list)  # json:"versionList"


@dataclass
class GetConfigurationVersionRequest:
    """Request for getting a single configuration version.

    Mirrors Go GetConfigurationVersionRequest struct from configuration_version.go.
    """
    config_id: int = 0  # json:"-" (path parameter)
    version: int = 0  # json:"-" (path parameter)


@dataclass
class GetConfigurationVersionResponse:
    """Response from getting a single configuration version.

    Mirrors Go GetConfigurationVersionResponse struct.
    """
    based_on: int = 0  # json:"basedOn"
    config_id: int = 0  # json:"configId"
    config_name: str = ""  # json:"configName"
    create_date: str = ""  # json:"createDate" (time.Time -> str)
    created_by: str = ""  # json:"createdBy"
    production: dict = field(default_factory=dict)  # json:"production"
    staging: dict = field(default_factory=dict)  # json:"staging"
    version: int = 0  # json:"version"
    version_notes: str = ""  # json:"versionNotes"


# =============================================================================
# Configuration Version Clone (from configuration_version_clone.go)
# =============================================================================


@dataclass
class GetConfigurationVersionCloneRequest:
    """Request for getting configuration version clone details.

    Mirrors Go GetConfigurationVersionCloneRequest struct.
    """
    config_id: int = 0  # json:"configId"
    config_name: str = ""  # json:"configName"
    version: int = 0  # json:"version"
    version_notes: str = ""  # json:"versionNotes"
    create_date: str = ""  # json:"createDate" (time.Time -> str)
    created_by: str = ""  # json:"createdBy"
    based_on: int = 0  # json:"basedOn"
    production: dict = field(default_factory=dict)  # json:"production"
    staging: dict = field(default_factory=dict)  # json:"staging"


@dataclass
class GetConfigurationVersionCloneResponse:
    """Response from getting configuration version clone details.

    Mirrors Go GetConfigurationVersionCloneResponse struct.
    """
    config_id: int = 0  # json:"configId"
    config_name: str = ""  # json:"configName"
    version: int = 0  # json:"version"
    version_notes: str = ""  # json:"versionNotes"
    create_date: str = ""  # json:"createDate"
    created_by: str = ""  # json:"createdBy"
    based_on: int = 0  # json:"basedOn"
    production: dict = field(default_factory=dict)  # json:"production"
    staging: dict = field(default_factory=dict)  # json:"staging"


@dataclass
class CreateConfigurationVersionCloneRequest:
    """Request for creating a configuration version clone.

    Mirrors Go CreateConfigurationVersionCloneRequest struct.
    """
    config_id: int = 0  # json:"-" (path parameter)
    create_from_version: int = 0  # json:"createFromVersion"
    rule_update: bool = False  # json:"ruleUpdate"


@dataclass
class CreateConfigurationVersionCloneResponse:
    """Response from creating a configuration version clone.

    Mirrors Go CreateConfigurationVersionCloneResponse struct.
    """
    config_id: int = 0  # json:"configId"
    config_name: str = ""  # json:"configName"
    version: int = 0  # json:"version"
    version_notes: str = ""  # json:"versionNotes"
    create_date: str = ""  # json:"createDate"
    created_by: str = ""  # json:"createdBy"
    based_on: int = 0  # json:"basedOn"


@dataclass
class RemoveConfigurationVersionCloneRequest:
    """Request for removing a configuration version clone.

    Mirrors Go RemoveConfigurationVersionCloneRequest struct.
    """
    config_id: int = 0  # json:"-" (path parameter)
    version: int = 0  # json:"-" (path parameter)


@dataclass
class RemoveConfigurationVersionCloneResponse:
    """Response from removing a configuration version clone.

    Mirrors Go RemoveConfigurationVersionCloneResponse struct.
    """
    empty: str = ""  # json:"empty"


# =============================================================================
# Security Policy (from security_policy.go)
# =============================================================================


@dataclass
class SecurityControls:
    """Security controls for a policy.

    Mirrors Go SecurityControls struct from security_policy.go.
    """
    apply_api_constraints: bool = False  # json:"applyApiConstraints"
    apply_application_layer_controls: bool = False  # json:"applyApplicationLayerControls"
    apply_account_protection_controls: bool = False  # json:"applyAccountProtectionControls"
    apply_botman_controls: bool = False  # json:"applyBotmanControls"
    apply_malware_controls: bool = False  # json:"applyMalwareControls"
    apply_network_layer_controls: bool = False  # json:"applyNetworkLayerControls"
    apply_rate_controls: bool = False  # json:"applyRateControls"
    apply_reputation_controls: bool = False  # json:"applyReputationControls"
    apply_slow_post_controls: bool = False  # json:"applySlowPostControls"


@dataclass
class ConfigVersion:
    """Configuration version identifier.

    Mirrors Go ConfigVersion struct from advanced_settings_pii_learning.go.
    """
    config_id: int = 0  # ConfigID int64
    version: int = 0  # Version int


@dataclass
class GetSecurityPoliciesRequest:
    """Request for listing security policies.

    Mirrors Go GetSecurityPoliciesRequest struct from security_policy.go.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"


@dataclass
class GetSecurityPoliciesResponse:
    """Response from listing security policies.

    Mirrors Go GetSecurityPoliciesResponse struct from security_policy.go.
    """
    policies: list[dict] = field(default_factory=list)  # json:"policies"


@dataclass
class GetSecurityPolicyRequest:
    """Request for getting a single security policy.

    Mirrors Go GetSecurityPolicyRequest struct from security_policy.go.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"


@dataclass
class GetSecurityPolicyResponse:
    """Response from getting a single security policy.

    Mirrors Go GetSecurityPolicyResponse struct from security_policy.go.
    """
    config_id: int = 0  # json:"-"
    policy_id: str = ""  # json:"policyId"
    policy_name: str = ""  # json:"policyName"
    default_settings: bool = False  # json:"defaultSettings"
    policy_security_controls: dict | None = None  # json:"policySecurityControls"
    version: int = 0  # json:"-"


@dataclass
class CreateSecurityPolicyRequest:
    """Request for creating a security policy.

    Mirrors Go CreateSecurityPolicyRequest struct from security_policy.go.
    """
    config_id: int = 0  # json:"-" (path parameter)
    version: int = 0  # json:"-" (path parameter)
    policy_name: str = ""  # json:"policyName"
    policy_prefix: str = ""  # json:"policyPrefix"


@dataclass
class CreateSecurityPolicyResponse:
    """Response from creating a security policy.

    Mirrors Go CreateSecurityPolicyResponse struct.
    """


@dataclass
class CreateSecurityPolicyWithDefaultProtectionsRequest:
    """Request for creating a security policy with default protections.

    Mirrors Go CreateSecurityPolicyWithDefaultProtectionsRequest struct.
    Embeds ConfigVersion.
    """
    config_id: int = 0  # from ConfigVersion (int64)
    version: int = 0  # from ConfigVersion
    policy_name: str = ""  # json:"policyName"
    policy_prefix: str = ""  # json:"policyPrefix"


@dataclass
class UpdateSecurityPolicyRequest:
    """Request for updating a security policy.

    Mirrors Go UpdateSecurityPolicyRequest struct from security_policy.go.
    """
    config_id: int = 0  # json:"-" (path parameter)
    version: int = 0  # json:"-" (path parameter)
    policy_id: str = ""  # json:"-" (path parameter)
    policy_name: str = ""  # json:"policyName"


@dataclass
class UpdateSecurityPolicyResponse:
    """Response from updating a security policy.

    Mirrors Go UpdateSecurityPolicyResponse struct from security_policy.go.
    """
    config_id: int = 0  # json:"-"
    policy_id: str = ""  # json:"policyId"
    policy_name: str = ""  # json:"policyName"
    default_settings: bool = False  # json:"defaultSettings"
    policy_security_controls: dict | None = None  # json:"policySecurityControls"
    version: int = 0  # json:"-"


@dataclass
class RemoveSecurityPolicyRequest:
    """Request for removing a security policy.

    Mirrors Go RemoveSecurityPolicyRequest struct from security_policy.go.
    """
    config_id: int = 0  # json:"-" (path parameter)
    version: int = 0  # json:"-" (path parameter)
    policy_id: str = ""  # json:"-" (path parameter)


@dataclass
class RemoveSecurityPolicyResponse:
    """Response from removing a security policy.

    Mirrors Go RemoveSecurityPolicyResponse struct from security_policy.go.
    """
    config_id: int = 0  # json:"-"
    policy_id: str = ""  # json:"policyId"
    policy_name: str = ""  # json:"policyName"
    policy_security_controls: dict | None = None  # json:"policySecurityControls"
    version: int = 0  # json:"-"


# =============================================================================
# Security Policy Clone (from security_policy_clone.go)
# =============================================================================


@dataclass
class Policies:
    """Policy info in clone responses.

    Mirrors Go Policies struct from security_policy_clone.go.
    """
    has_rate_policy_with_api_key: bool = False  # json:"hasRatePolicyWithApiKey"
    policy_id: str = ""  # json:"policyId"
    policy_name: str = ""  # json:"policyName"
    policy_security_controls: dict | None = None  # json:"policySecurityControls"


@dataclass
class SecurityPolicyCloneResponse:
    """Clone list response.

    Mirrors Go SecurityPolicyCloneResponse struct from security_policy_clone.go.
    """
    config_id: int = 0  # json:"configId"
    policies: list[dict] = field(default_factory=list)  # json:"policies"
    version: int = 0  # json:"version"


@dataclass
class GetSecurityPolicyClonesRequest:
    """Request for listing security policy clones.

    Mirrors Go GetSecurityPolicyClonesRequest struct.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"


@dataclass
class GetSecurityPolicyClonesResponse:
    """Response from listing security policy clones.

    Mirrors Go GetSecurityPolicyClonesResponse struct.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policies: list[dict] = field(default_factory=list)  # json:"policies"


@dataclass
class GetSecurityPolicyCloneRequest:
    """Request for getting a single security policy clone.

    Mirrors Go GetSecurityPolicyCloneRequest struct.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"


@dataclass
class GetSecurityPolicyCloneResponse:
    """Response from getting a single security policy clone.

    Mirrors Go GetSecurityPolicyCloneResponse struct.
    """
    config_id: int = 0  # json:"configId"
    policy_id: str = ""  # json:"policyId"
    policy_name: str = ""  # json:"policyName"
    policy_security_controls: dict | None = None  # json:"policySecurityControls"
    version: int = 0  # json:"version"


@dataclass
class CreateSecurityPolicyCloneRequest:
    """Request for creating a security policy clone.

    Mirrors Go CreateSecurityPolicyCloneRequest struct.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    create_from_security_policy: str = ""  # json:"createFromSecurityPolicy"
    policy_name: str = ""  # json:"policyName"
    policy_prefix: str = ""  # json:"policyPrefix"


@dataclass
class CreateSecurityPolicyCloneResponse:
    """Response from creating a security policy clone.

    Mirrors Go CreateSecurityPolicyCloneResponse struct.
    """
    has_rate_policy_with_api_key: bool = False  # json:"hasRatePolicyWithApiKey"
    policy_id: str = ""  # json:"policyId"
    policy_name: str = ""  # json:"policyName"
    policy_security_controls: dict | None = None  # json:"policySecurityControls"


@dataclass
class CreateSecurityPolicyClonePost:
    """POST body for creating a security policy clone.

    Mirrors Go CreateSecurityPolicyClonePost struct.
    """
    create_from_security_policy: str = ""  # json:"createFromSecurityPolicy"
    policy_name: str = ""  # json:"policyName"
    policy_prefix: str = ""  # json:"policyPrefix"


@dataclass
class CreateSecurityPolicyClonePostResponse:
    """Response from POST creating a security policy clone.

    Mirrors Go CreateSecurityPolicyClonePostResponse struct.
    """
    config_id: int = 0  # json:"configId"
    policy_id: str = ""  # json:"policyId"
    policy_name: str = ""  # json:"policyName"
    policy_security_controls: dict | None = None  # json:"policySecurityControls"
    version: int = 0  # json:"version"


# =============================================================================
# Security Policy Protections (from security_policy_protections.go)
# =============================================================================


@dataclass
class GetPolicyProtectionsRequest:
    """Request for getting policy protections.

    Mirrors Go GetPolicyProtectionsRequest struct.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"


@dataclass
class UpdatePolicyProtectionsRequest:
    """Request for updating policy protections.

    Mirrors Go UpdatePolicyProtectionsRequest struct.
    """
    config_id: int = 0  # json:"-" (path parameter)
    version: int = 0  # json:"-" (path parameter)
    policy_id: str = ""  # json:"-" (path parameter)
    apply_api_constraints: bool = False  # json:"applyApiConstraints"
    apply_application_layer_controls: bool = False  # json:"applyApplicationLayerControls"
    apply_botman_controls: bool = False  # json:"applyBotmanControls"
    apply_network_layer_controls: bool = False  # json:"applyNetworkLayerControls"
    apply_rate_controls: bool = False  # json:"applyRateControls"
    apply_reputation_controls: bool = False  # json:"applyReputationControls"
    apply_slow_post_controls: bool = False  # json:"applySlowPostControls"
    apply_malware_controls: bool = False  # json:"applyMalwareControls"


@dataclass
class PolicyProtectionsResponse:
    """Response from getting/updating policy protections.

    Mirrors Go PolicyProtectionsResponse struct (9 Apply bools).
    """
    apply_api_constraints: bool = False  # json:"applyApiConstraints"
    apply_account_protection_controls: bool = False  # json:"applyAccountProtectionControls"
    apply_application_layer_controls: bool = False  # json:"applyApplicationLayerControls"
    apply_botman_controls: bool = False  # json:"applyBotmanControls"
    apply_malware_controls: bool = False  # json:"applyMalwareControls"
    apply_network_layer_controls: bool = False  # json:"applyNetworkLayerControls"
    apply_rate_controls: bool = False  # json:"applyRateControls"
    apply_reputation_controls: bool = False  # json:"applyReputationControls"
    apply_slow_post_controls: bool = False  # json:"applySlowPostControls"


# =============================================================================
# Custom Rule (from custom_rule.go)
# =============================================================================


@dataclass
class Policy:
    """Policy reference in custom rule usage.

    Mirrors Go Policy struct from custom_rule.go.
    """
    policy_id: str = ""  # json:"policyId"
    policy_name: str = ""  # json:"policyName"


@dataclass
class CustomRuleUsage:
    """Custom rule usage info.

    Mirrors Go CustomRuleUsage struct from custom_rule.go.
    """
    policies: list[dict] = field(default_factory=list)  # json:"policies"
    rule_id: int = 0  # json:"ruleId"


@dataclass
class RuleIDs:
    """List of rule IDs for usage lookup.

    Mirrors Go RuleIDs struct from custom_rule.go.
    """
    ids: list[int] = field(default_factory=list)  # json:"ids"


@dataclass
class CustomRuleEffectivePeriod:
    """Effective time period for custom rules.

    Mirrors Go CustomRuleEffectivePeriod struct from custom_rule.go.
    """
    end_date: str = ""  # json:"endDate"
    start_date: str = ""  # json:"startDate"
    status: str = ""  # json:"status"


@dataclass
class CustomRuleResponse:
    """Custom rule details.

    Mirrors Go CustomRuleResponse struct from custom_rule.go.
    """
    id: int = 0  # json:"id"
    name: str = ""  # json:"name"
    description: str = ""  # json:"description"
    version: int = 0  # json:"-"
    rule_activated: bool = False  # json:"-"
    structured: bool = False  # json:"-"
    tag: list[str] = field(default_factory=list)  # json:"tag"
    conditions: list[dict] = field(default_factory=list)  # json:"conditions"
    effective_time_period: dict | None = None  # json:"effectiveTimePeriod"
    sampling_rate: int = 0  # json:"samplingRate"
    logging_options: Any = None  # json:"loggingOptions" (json.RawMessage)
    operation: str = ""  # json:"operation"
    staging_only: bool = False  # json:"stagingOnly"


@dataclass
class GetCustomRulesUsageRequest:
    """Request for getting custom rules usage.

    Mirrors Go GetCustomRulesUsageRequest struct from custom_rule.go.
    """
    config_id: int = 0  # json:"-" (path parameter)
    version: int = 0  # json:"-" (path parameter)
    request_body: dict | None = None  # json:"-" (RuleIDs)


@dataclass
class GetCustomRulesUsageResponse:
    """Response from getting custom rules usage.

    Mirrors Go GetCustomRulesUsageResponse struct from custom_rule.go.
    """
    rules: list[dict] = field(default_factory=list)  # json:"rules"


@dataclass
class GetCustomRulesRequest:
    """Request for listing custom rules.

    Mirrors Go GetCustomRulesRequest struct from custom_rule.go.
    """
    config_id: int = 0  # json:"-" (path parameter)
    id: int = 0  # json:"-" (path parameter)


@dataclass
class GetCustomRulesResponse:
    """Response from listing custom rules.

    Mirrors Go GetCustomRulesResponse struct from custom_rule.go.
    """
    custom_rules: list[dict] = field(default_factory=list)  # json:"customRules"


@dataclass
class GetCustomRuleRequest:
    """Request for getting a single custom rule.

    Mirrors Go GetCustomRuleRequest struct from custom_rule.go.
    """
    config_id: int = 0  # json:"-" (path parameter)
    id: int = 0  # json:"-" (path parameter)


# GetCustomRuleResponse is an alias for CustomRuleResponse
GetCustomRuleResponse = CustomRuleResponse


@dataclass
class CreateCustomRuleRequest:
    """Request for creating a custom rule.

    Mirrors Go CreateCustomRuleRequest struct from custom_rule.go.
    """
    config_id: int = 0  # json:"-" (path parameter)
    version: int = 0  # json:"-"
    json_payload_raw: Any = None  # json:"-" (json.RawMessage, not serialized)


@dataclass
class CreateCustomRuleResponse:
    """Response from creating a custom rule.

    Mirrors Go CreateCustomRuleResponse struct from custom_rule.go.
    """
    id: int = 0  # json:"id"
    name: str = ""  # json:"name"
    description: str = ""  # json:"description"
    tag: list[str] = field(default_factory=list)  # json:"tag"
    conditions: list[dict] = field(default_factory=list)  # json:"conditions"
    effective_time_period: dict | None = None  # json:"effectiveTimePeriod"
    sampling_rate: int = 0  # json:"samplingRate"
    logging_options: Any = None  # json:"loggingOptions"
    operation: str = ""  # json:"operation"
    staging_only: bool = False  # json:"stagingOnly"


@dataclass
class UpdateCustomRuleRequest:
    """Request for updating a custom rule.

    Mirrors Go UpdateCustomRuleRequest struct from custom_rule.go.
    """
    config_id: int = 0  # json:"-" (path parameter)
    id: int = 0  # json:"-" (path parameter)
    version: int = 0  # json:"-"
    json_payload_raw: Any = None  # json:"-" (json.RawMessage)


@dataclass
class UpdateCustomRuleResponse:
    """Response from updating a custom rule.

    Mirrors Go UpdateCustomRuleResponse struct.
    """


@dataclass
class RemoveCustomRuleRequest:
    """Request for removing a custom rule.

    Mirrors Go RemoveCustomRuleRequest struct from custom_rule.go.
    """
    config_id: int = 0  # json:"-" (path parameter)
    id: int = 0  # json:"-" (path parameter)


@dataclass
class RemoveCustomRuleResponse:
    """Response from removing a custom rule.

    Mirrors Go RemoveCustomRuleResponse struct.
    """


# =============================================================================
# Custom Rule Action (from custom_rule_action.go)
# =============================================================================


@dataclass
class GetCustomRuleActionsRequest:
    """Request for listing custom rule actions.

    Mirrors Go GetCustomRuleActionsRequest struct.
    """
    config_id: int = 0  # json:"-" (path parameter)
    version: int = 0  # json:"-" (path parameter)
    policy_id: str = ""  # json:"-" (path parameter)
    rule_id: int = 0  # json:"-"


@dataclass
class GetCustomRuleActionsResponse:
    """Response from listing custom rule actions.

    Mirrors Go GetCustomRuleActionsResponse struct.
    """


@dataclass
class GetCustomRuleActionRequest:
    """Request for getting a single custom rule action.

    Mirrors Go GetCustomRuleActionRequest struct.
    """
    config_id: int = 0  # json:"-" (path parameter)
    version: int = 0  # json:"-" (path parameter)
    policy_id: str = ""  # json:"-" (path parameter)
    rule_id: int = 0  # json:"-"


@dataclass
class GetCustomRuleActionResponse:
    """Response from getting a single custom rule action.

    Mirrors Go GetCustomRuleActionResponse struct.
    """
    action: str = ""  # json:"action"
    can_use_advanced_actions: bool = False  # json:"canUseAdvancedActions"
    link: str = ""  # json:"link"
    name: str = ""  # json:"name"
    rule_id: int = 0  # json:"id"


@dataclass
class UpdateCustomRuleActionRequest:
    """Request for updating a custom rule action.

    Mirrors Go UpdateCustomRuleActionRequest struct.
    """
    config_id: int = 0  # json:"-" (path parameter)
    version: int = 0  # json:"-" (path parameter)
    policy_id: str = ""  # json:"-" (path parameter)
    rule_id: int = 0  # json:"-"
    action: str = ""  # json:"action"


@dataclass
class UpdateCustomRuleActionResponse:
    """Response from updating a custom rule action.

    Mirrors Go UpdateCustomRuleActionResponse struct.
    """
    action: str = ""  # json:"action"
    can_use_advanced_actions: bool = False  # json:"canUseAdvancedActions"
    link: str = ""  # json:"link"
    name: str = ""  # json:"name"
    rule_id: int = 0  # json:"id"


# =============================================================================
# Custom Deny (from custom_deny.go)
# =============================================================================


@dataclass
class GetCustomDenyListRequest:
    """Request for listing custom deny actions.

    Mirrors Go GetCustomDenyListRequest struct from custom_deny.go.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    id: str = ""  # json:"-"


@dataclass
class GetCustomDenyListResponse:
    """Response from listing custom deny actions.

    Mirrors Go GetCustomDenyListResponse struct from custom_deny.go.
    """
    custom_deny_list: list[dict] = field(default_factory=list)  # json:"customDenyList"


@dataclass
class GetCustomDenyRequest:
    """Request for getting a single custom deny.

    Mirrors Go GetCustomDenyRequest struct from custom_deny.go.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    id: str = ""  # json:"-"


@dataclass
class GetCustomDenyResponse:
    """Response from getting a single custom deny.

    Mirrors Go GetCustomDenyResponse struct from custom_deny.go.
    """
    description: str = ""  # json:"description"
    name: str = ""  # json:"name"
    id: str = ""  # json:"id"
    parameters: list[dict] = field(default_factory=list)  # json:"parameters"


@dataclass
class CreateCustomDenyRequest:
    """Request for creating a custom deny.

    Mirrors Go CreateCustomDenyRequest struct from custom_deny.go.
    """
    config_id: int = 0  # json:"-" (path parameter)
    version: int = 0  # json:"-" (path parameter)
    json_payload_raw: Any = None  # json:"-" (json.RawMessage)


@dataclass
class CreateCustomDenyResponse:
    """Response from creating a custom deny.

    Mirrors Go CreateCustomDenyResponse struct from custom_deny.go.
    """
    description: str = ""  # json:"description"
    name: str = ""  # json:"name"
    id: str = ""  # json:"id"
    parameters: list[dict] = field(default_factory=list)  # json:"parameters"


@dataclass
class UpdateCustomDenyRequest:
    """Request for updating a custom deny.

    Mirrors Go UpdateCustomDenyRequest struct from custom_deny.go.
    """
    config_id: int = 0  # json:"-" (path parameter)
    version: int = 0  # json:"-" (path parameter)
    id: str = ""  # json:"-"
    json_payload_raw: Any = None  # json:"-" (json.RawMessage)


@dataclass
class UpdateCustomDenyResponse:
    """Response from updating a custom deny.

    Mirrors Go UpdateCustomDenyResponse struct from custom_deny.go.
    """
    description: str = ""  # json:"description"
    name: str = ""  # json:"name"
    id: str = ""  # json:"id"
    parameters: list[dict] = field(default_factory=list)  # json:"parameters"


@dataclass
class RemoveCustomDenyRequest:
    """Request for removing a custom deny.

    Mirrors Go RemoveCustomDenyRequest struct from custom_deny.go.
    """
    config_id: int = 0  # json:"-" (path parameter)
    version: int = 0  # json:"-" (path parameter)
    id: str = ""  # json:"-"


@dataclass
class RemoveCustomDenyResponse:
    """Response from removing a custom deny.

    Mirrors Go RemoveCustomDenyResponse struct from custom_deny.go.
    """
    empty: str = ""  # json:"empty"


# =============================================================================
# Rate Policy (from rate_policy.go)
# =============================================================================


@dataclass
class RatePolicyPath:
    """Path match for rate policies.

    Mirrors Go RatePolicyPath struct from rate_policy.go.
    """
    positive_match: bool = False  # json:"positiveMatch"
    values: list[str] = field(default_factory=list)  # json:"values"


@dataclass
class RatePolicyFileExtensions:
    """File extension match for rate policies.

    Mirrors Go RatePolicyFileExtensions struct from rate_policy.go.
    """
    positive_match: bool = False  # json:"positiveMatch"
    values: list[str] = field(default_factory=list)  # json:"values"


@dataclass
class RatePolicyMatchOption:
    """Match option for rate policies.

    Mirrors Go RatePolicyMatchOption struct from rate_policy.go.
    """
    positive_match: bool = False  # json:"positiveMatch"
    type: str = ""  # json:"type"
    values: list[str] = field(default_factory=list)  # json:"values"


@dataclass
class RatePoliciesHosts:
    """Host match for rate policies.

    Mirrors Go RatePoliciesHosts struct from rate_policy.go.
    """
    values: list[str] | None = None  # json:"values" (*[]string)
    positive_match: Any = None  # json:"positiveMatch" (*json.RawMessage)


@dataclass
class RatePolicyCondition:
    """Condition for rate policies.

    Mirrors Go RatePolicyCondition struct from rate_policy.go.
    """
    atomic_conditions: list[dict] = field(default_factory=list)  # json:"atomicConditions"


@dataclass
class RatePolicyAPISelectors:
    """API selectors for rate policies.

    Mirrors Go RatePolicyAPISelectors struct from rate_policy.go.
    """
    api_definition_ids: list[int] = field(default_factory=list)  # json:"apiDefinitionIds"
    resource_ids: list[int] = field(default_factory=list)  # json:"resourceIds"


@dataclass
class RatePolicyBodyParameters:
    """Body parameters for rate policies.

    Mirrors Go RatePolicyBodyParameters struct from rate_policy.go.
    """
    name: str = ""  # json:"name"
    positive_match: bool = False  # json:"positiveMatch"
    values: list[str] = field(default_factory=list)  # json:"values"


@dataclass
class RatePolicyQueryParameters:
    """Query parameters for rate policies.

    Mirrors Go RatePolicyQueryParameters struct from rate_policy.go.
    """
    name: str = ""  # json:"name"
    positive_match: bool = False  # json:"positiveMatch"
    values: list[str] = field(default_factory=list)  # json:"values"


@dataclass
class GetRatePoliciesRequest:
    """Request for listing rate policies.

    Mirrors Go GetRatePoliciesRequest struct from rate_policy.go.
    """
    config_id: int = 0  # json:"configId"
    config_version: int = 0  # json:"configVersion"


@dataclass
class GetRatePoliciesResponse:
    """Response from listing rate policies.

    Mirrors Go GetRatePoliciesResponse struct from rate_policy.go.
    """
    rate_policies: list[dict] = field(default_factory=list)  # json:"ratePolicies"


@dataclass
class GetRatePolicyRequest:
    """Request for getting a single rate policy.

    Mirrors Go GetRatePolicyRequest struct from rate_policy.go.
    """
    config_id: int = 0  # json:"configId"
    config_version: int = 0  # json:"configVersion"
    rate_policy_id: int = 0  # json:"ratePolicyId"


@dataclass
class GetRatePolicyResponse:
    """Response from getting a single rate policy.

    Mirrors Go GetRatePolicyResponse struct from rate_policy.go.
    """


@dataclass
class CreateRatePolicyRequest:
    """Request for creating a rate policy.

    Mirrors Go CreateRatePolicyRequest struct from rate_policy.go.
    """
    id: int = 0  # json:"-"
    config_id: int = 0  # json:"-"
    config_version: int = 0  # json:"-"
    json_payload_raw: Any = None  # json:"-" (json.RawMessage)


@dataclass
class CreateRatePolicyResponse:
    """Response from creating a rate policy.

    Mirrors Go CreateRatePolicyResponse struct from rate_policy.go.
    """
    id: int = 0  # json:"id"
    config_id: int = 0  # json:"configId"
    config_version: int = 0  # json:"configVersion"
    match_type: str = ""  # json:"matchType"
    type: str = ""  # json:"type"
    name: str = ""  # json:"name"
    description: str = ""  # json:"description"
    average_threshold: int = 0  # json:"averageThreshold"
    burst_threshold: int = 0  # json:"burstThreshold"


@dataclass
class UpdateRatePolicyRequest:
    """Request for updating a rate policy.

    Mirrors Go UpdateRatePolicyRequest struct from rate_policy.go.
    """
    rate_policy_id: int = 0  # json:"-"
    config_id: int = 0  # json:"-"
    config_version: int = 0  # json:"-"
    json_payload_raw: Any = None  # json:"-" (json.RawMessage)


@dataclass
class UpdateRatePolicyResponse:
    """Response from updating a rate policy.

    Mirrors Go UpdateRatePolicyResponse struct from rate_policy.go.
    """


@dataclass
class RemoveRatePolicyRequest:
    """Request for removing a rate policy.

    Mirrors Go RemoveRatePolicyRequest struct from rate_policy.go.
    """
    config_id: int = 0  # json:"-"
    config_version: int = 0  # json:"-"
    rate_policy_id: int = 0  # json:"-"


@dataclass
class RemoveRatePolicyResponse:
    """Response from removing a rate policy.

    Mirrors Go RemoveRatePolicyResponse struct from rate_policy.go.
    """


# =============================================================================
# Rate Policy Action (from rate_policy_action.go)
# =============================================================================


@dataclass
class RatePolicyActionPost:
    """Rate policy action data.

    Mirrors Go RatePolicyActionPost struct from rate_policy_action.go.
    """
    id: int = 0  # json:"id"
    ipv4_action: str = ""  # json:"ipv4Action"
    ipv6_action: str = ""  # json:"ipv6Action"


@dataclass
class GetRatePolicyActionsRequest:
    """Request for listing rate policy actions.

    Mirrors Go GetRatePolicyActionsRequest struct from rate_policy_action.go.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"
    rate_policy_id: int = 0  # json:"-"
    ipv4_action: str = ""  # json:"ipv4Action"
    ipv6_action: str = ""  # json:"ipv6Action"


@dataclass
class GetRatePolicyActionsResponse:
    """Response from listing rate policy actions.

    Mirrors Go GetRatePolicyActionsResponse struct from rate_policy_action.go.
    """
    rate_policy_actions: list[dict] = field(default_factory=list)  # json:"ratePolicyActions"


@dataclass
class UpdateRatePolicyActionRequest:
    """Request for updating a rate policy action.

    Mirrors Go UpdateRatePolicyActionRequest struct from rate_policy_action.go.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"
    rate_policy_id: int = 0  # json:"id"
    ipv4_action: str = ""  # json:"ipv4Action"
    ipv6_action: str = ""  # json:"ipv6Action"


@dataclass
class UpdateRatePolicyActionResponse:
    """Response from updating a rate policy action.

    Mirrors Go UpdateRatePolicyActionResponse struct from rate_policy_action.go.
    """
    id: int = 0  # json:"id"
    ipv4_action: str = ""  # json:"ipv4Action"
    ipv6_action: str = ""  # json:"ipv6Action"


# =============================================================================
# Eval (from eval.go)
# =============================================================================


@dataclass
class GetEvalsRequest:
    """Request for listing evals.

    Mirrors Go GetEvalsRequest struct from eval.go.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"
    current: str = ""  # json:"current"
    mode: str = ""  # json:"mode"
    eval: str = ""  # json:"eval"


@dataclass
class GetEvalsResponse:
    """Response from listing evals.

    Mirrors Go GetEvalsResponse struct from eval.go.
    """
    current: str = ""  # json:"current"
    mode: str = ""  # json:"mode"
    eval: str = ""  # json:"eval"
    evaluating: str = ""  # json:"evaluating"
    expires: str = ""  # json:"expires"


@dataclass
class GetEvalRequest:
    """Request for getting a single eval.

    Mirrors Go GetEvalRequest struct from eval.go.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"
    current: str = ""  # json:"current"
    mode: str = ""  # json:"mode"
    eval: str = ""  # json:"eval"


@dataclass
class GetEvalResponse:
    """Response from getting a single eval.

    Mirrors Go GetEvalResponse struct from eval.go.
    """
    current: str = ""  # json:"current"
    mode: str = ""  # json:"mode"
    eval: str = ""  # json:"eval"
    evaluating: str = ""  # json:"evaluating"
    expires: str = ""  # json:"expires"


@dataclass
class UpdateEvalRequest:
    """Request for updating an eval.

    Mirrors Go UpdateEvalRequest struct from eval.go.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"
    eval: str = ""  # json:"eval"


@dataclass
class UpdateEvalResponse:
    """Response from updating an eval.

    Mirrors Go UpdateEvalResponse struct from eval.go.
    """
    current: str = ""  # json:"current"
    eval: str = ""  # json:"eval"
    mode: str = ""  # json:"mode"


@dataclass
class RemoveEvalRequest:
    """Request for removing an eval.

    Mirrors Go RemoveEvalRequest struct from eval.go.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"
    eval: str = ""  # json:"eval"


@dataclass
class RemoveEvalResponse:
    """Response from removing an eval.

    Mirrors Go RemoveEvalResponse struct from eval.go.
    """
    current: str = ""  # json:"current"
    eval: str = ""  # json:"eval"
    mode: str = ""  # json:"mode"


# =============================================================================
# Eval Rule (from eval_rule.go)
# =============================================================================


@dataclass
class GetEvalRulesRequest:
    """Request for listing eval rules.

    Mirrors Go GetEvalRulesRequest struct from eval_rule.go.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"
    rule_id: int = 0  # json:"-"


@dataclass
class GetEvalRulesResponse:
    """Response from listing eval rules.

    Mirrors Go GetEvalRulesResponse struct from eval_rule.go.
    """
    rules: list[dict] = field(default_factory=list)  # json:"rules"


@dataclass
class GetEvalRuleRequest:
    """Request for getting a single eval rule.

    Mirrors Go GetEvalRuleRequest struct from eval_rule.go.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"
    rule_id: int = 0  # json:"-"


@dataclass
class GetEvalRuleResponse:
    """Response from getting a single eval rule.

    Mirrors Go GetEvalRuleResponse struct from eval_rule.go.
    """
    action: str = ""  # json:"action"
    condition_exception: dict | None = None  # json:"conditionException" (*RuleConditionException)


@dataclass
class UpdateEvalRuleRequest:
    """Request for updating an eval rule.

    Mirrors Go UpdateEvalRuleRequest struct from eval_rule.go.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"
    rule_id: int = 0  # json:"-"
    action: str = ""  # json:"action"
    json_payload_raw: Any = None  # json:"-" (json.RawMessage)


@dataclass
class UpdateEvalRuleResponse:
    """Response from updating an eval rule.

    Mirrors Go UpdateEvalRuleResponse struct from eval_rule.go.
    """
    action: str = ""  # json:"action"
    condition_exception: dict | None = None  # json:"conditionException"


# RuleConditionException is defined in rule.go section below


# =============================================================================
# Attack Group (from attack_group.go)
# =============================================================================


@dataclass
class AttackGroupConditions:
    """Conditions for attack group exceptions.

    Mirrors Go AttackGroupConditions struct from attack_group.go.
    """
    positive_match: bool = False  # json:"positiveMatch"
    value: list[str] = field(default_factory=list)  # json:"value"
    name: list[str] = field(default_factory=list)  # json:"name"


@dataclass
class AttackGroupConditionException:
    """Condition exception for attack groups.

    Mirrors Go AttackGroupConditionException struct from attack_group.go.
    """
    advanced_exceptions_list: dict | None = None  # json:"advancedExceptions"
    exception: dict | None = None  # json:"exception"


@dataclass
class AttackGroupAdvancedExceptions:
    """Advanced exceptions for attack groups.

    Mirrors Go AttackGroupAdvancedExceptions struct from attack_group.go.
    """
    condition_operator: str = ""  # json:"conditionOperator"
    conditions: Any = None  # json:"conditions" (*AttackGroupAdvancedCriteria)
    header_cookie_or_param_values: Any = None  # json:"headerCookieOrParamValues"
    specific_header_cookie_or_param_name_value: Any = None  # specificHeaderCookieOrParamNameValue
    specific_header_cookie_param_xml_or_json_names: Any = None


# AdvancedExceptions is a type alias for AttackGroupAdvancedExceptions
# Mirrors Go: type AdvancedExceptions = AttackGroupAdvancedExceptions
AdvancedExceptions = AttackGroupAdvancedExceptions


@dataclass
class GetAttackGroupsRequest:
    """Request for listing attack groups.

    Mirrors Go GetAttackGroupsRequest struct from attack_group.go.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"
    group: str = ""  # json:"group"


@dataclass
class GetAttackGroupsResponse:
    """Response from listing attack groups.

    Mirrors Go GetAttackGroupsResponse struct from attack_group.go.
    """
    attack_group_actions: list[dict] = field(default_factory=list)  # json:"attackGroupActions"


@dataclass
class GetAttackGroupRequest:
    """Request for getting a single attack group.

    Mirrors Go GetAttackGroupRequest struct from attack_group.go.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"
    group: str = ""  # json:"group"


@dataclass
class GetAttackGroupResponse:
    """Response from getting a single attack group.

    Mirrors Go GetAttackGroupResponse struct from attack_group.go.
    """
    action: str = ""  # json:"action"
    condition_exception: dict | None = None  # json:"conditionException"


@dataclass
class UpdateAttackGroupRequest:
    """Request for updating an attack group.

    Mirrors Go UpdateAttackGroupRequest struct from attack_group.go.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"
    group: str = ""  # json:"group"
    action: str = ""  # json:"action"
    json_payload_raw: Any = None  # json:"-" (json.RawMessage)


@dataclass
class UpdateAttackGroupResponse:
    """Response from updating an attack group.

    Mirrors Go UpdateAttackGroupResponse struct from attack_group.go.
    """
    action: str = ""  # json:"action"
    condition_exception: dict | None = None  # json:"conditionException"


# =============================================================================
# Reputation Profile (from reputation_profile.go)
# =============================================================================


@dataclass
class ReputationProfileCondition:
    """Condition for reputation profiles.

    Mirrors Go ReputationProfileCondition struct from reputation_profile.go.
    """
    atomic_conditions: list[dict] = field(default_factory=list)  # json:"atomicConditions"
    positive_match: Any = None  # json:"positiveMatch" (*json.RawMessage)


@dataclass
class GetReputationProfileResponseCondition:
    """Condition in get reputation profile response.

    Mirrors Go GetReputationProfileResponseCondition struct.
    """
    atomic_conditions: list[dict] = field(default_factory=list)  # json:"atomicConditions"
    positive_match: Any = None  # json:"positiveMatch" (*json.RawMessage)


@dataclass
class GetReputationProfilesRequest:
    """Request for listing reputation profiles.

    Mirrors Go GetReputationProfilesRequest struct from reputation_profile.go.
    """
    config_id: int = 0  # json:"configId"
    config_version: int = 0  # json:"configVersion"
    reputation_profile_id: int = 0  # json:"-"


@dataclass
class GetReputationProfilesResponse:
    """Response from listing reputation profiles.

    Mirrors Go GetReputationProfilesResponse struct from reputation_profile.go.
    """
    reputation_profiles: list[dict] = field(default_factory=list)  # json:"reputationProfiles"


@dataclass
class GetReputationProfileRequest:
    """Request for getting a single reputation profile.

    Mirrors Go GetReputationProfileRequest struct from reputation_profile.go.
    """
    config_id: int = 0  # json:"configId"
    config_version: int = 0  # json:"configVersion"
    reputation_profile_id: int = 0  # json:"-"


@dataclass
class GetReputationProfileResponse:
    """Response from getting a single reputation profile.

    Mirrors Go GetReputationProfileResponse struct from reputation_profile.go.
    """
    condition: dict | None = None  # json:"condition"
    context: str = ""  # json:"context"
    id: int = 0  # json:"id"
    name: str = ""  # json:"name"
    shared_ip_handling: str = ""  # json:"sharedIpHandling"
    threshold: int = 0  # json:"threshold"


@dataclass
class CreateReputationProfileRequest:
    """Request for creating a reputation profile.

    Mirrors Go CreateReputationProfileRequest struct from reputation_profile.go.
    """
    config_id: int = 0  # json:"-"
    config_version: int = 0  # json:"-"
    json_payload_raw: Any = None  # json:"-" (json.RawMessage)


@dataclass
class CreateReputationProfileResponse:
    """Response from creating a reputation profile.

    Mirrors Go CreateReputationProfileResponse struct from reputation_profile.go.
    """
    id: int = 0  # json:"id"
    name: str = ""  # json:"name"
    context: str = ""  # json:"context"
    description: str = ""  # json:"description"
    threshold: int = 0  # json:"threshold"
    shared_ip_handling: str = ""  # json:"sharedIpHandling"


@dataclass
class UpdateReputationProfileRequest:
    """Request for updating a reputation profile.

    Mirrors Go UpdateReputationProfileRequest struct from reputation_profile.go.
    """
    config_id: int = 0  # json:"-"
    config_version: int = 0  # json:"-"
    reputation_profile_id: int = 0  # json:"-"
    json_payload_raw: Any = None  # json:"-" (json.RawMessage)


@dataclass
class UpdateReputationProfileResponse:
    """Response from updating a reputation profile.

    Mirrors Go UpdateReputationProfileResponse struct.
    """


@dataclass
class RemoveReputationProfileRequest:
    """Request for removing a reputation profile.

    Mirrors Go RemoveReputationProfileRequest struct from reputation_profile.go.
    """
    config_id: int = 0  # json:"-"
    config_version: int = 0  # json:"-"
    reputation_profile_id: int = 0  # json:"-"


@dataclass
class RemoveReputationProfileResponse:
    """Response from removing a reputation profile.

    Mirrors Go RemoveReputationProfileResponse struct.
    """


# =============================================================================
# Reputation Profile Action (from reputation_profile_action.go)
# =============================================================================


@dataclass
class ReputationProfileActionPost:
    """Reputation profile action data.

    Mirrors Go ReputationProfileActionPost struct from reputation_profile_action.go.
    """
    action: str = ""  # json:"action"
    id: int = 0  # json:"id"


@dataclass
class GetReputationProfileActionsRequest:
    """Request for listing reputation profile actions.

    Mirrors Go GetReputationProfileActionsRequest struct.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"
    reputation_profile_id: int = 0  # json:"-"
    action: str = ""  # json:"action"


@dataclass
class GetReputationProfileActionsResponse:
    """Response from listing reputation profile actions.

    Mirrors Go GetReputationProfileActionsResponse struct.
    """
    reputation_profiles: list[dict] = field(default_factory=list)  # json:"reputationProfiles"


@dataclass
class GetReputationProfileActionRequest:
    """Request for getting a single reputation profile action.

    Mirrors Go GetReputationProfileActionRequest struct.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"
    reputation_profile_id: int = 0  # json:"-"


@dataclass
class GetReputationProfileActionResponse:
    """Response from getting a single reputation profile action.

    Mirrors Go GetReputationProfileActionResponse struct.
    """
    action: str = ""  # json:"action"
    id: int = 0  # json:"id"


@dataclass
class UpdateReputationProfileActionRequest:
    """Request for updating a reputation profile action.

    Mirrors Go UpdateReputationProfileActionRequest struct.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"
    reputation_profile_id: int = 0  # json:"-"
    action: str = ""  # json:"action"


@dataclass
class UpdateReputationProfileActionResponse:
    """Response from updating a reputation profile action.

    Mirrors Go UpdateReputationProfileActionResponse struct.
    """
    action: str = ""  # json:"action"
    id: int = 0  # json:"id"


# =============================================================================
# Reputation Analysis (from reputation_analysis.go)
# =============================================================================


@dataclass
class GetReputationAnalysisRequest:
    """Request for getting reputation analysis.

    Mirrors Go GetReputationAnalysisRequest struct from reputation_analysis.go.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"


@dataclass
class GetReputationAnalysisResponse:
    """Response from getting reputation analysis.

    Mirrors Go GetReputationAnalysisResponse struct from reputation_analysis.go.
    """
    forward_to_http_header: bool = False  # json:"forwardToHTTPHeader"
    forward_shared_ip_to_http_header_and_siem: bool = False  # forwardSharedIPToHTTPHeaderAndSIEM


@dataclass
class UpdateReputationAnalysisRequest:
    """Request for updating reputation analysis.

    Mirrors Go UpdateReputationAnalysisRequest struct from reputation_analysis.go.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"
    forward_to_http_header: bool = False  # json:"forwardToHTTPHeader"
    forward_shared_ip_to_http_header_and_siem: bool = False  # forwardSharedIPToHTTPHeaderAndSIEM


@dataclass
class UpdateReputationAnalysisResponse:
    """Response from updating reputation analysis.

    Mirrors Go UpdateReputationAnalysisResponse struct from reputation_analysis.go.
    """
    forward_to_http_header: bool = False  # json:"forwardToHTTPHeader"
    forward_shared_ip_to_http_header_and_siem: bool = False  # forwardSharedIPToHTTPHeaderAndSIEM


@dataclass
class RemoveReputationAnalysisRequest:
    """Request for removing reputation analysis.

    Mirrors Go RemoveReputationAnalysisRequest struct from reputation_analysis.go.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"
    forward_to_http_header: bool = False  # json:"forwardToHTTPHeader"
    forward_shared_ip_to_http_header_and_siem: bool = False  # forwardSharedIPToHTTPHeaderAndSIEM


@dataclass
class RemoveReputationAnalysisResponse:
    """Response from removing reputation analysis.

    Mirrors Go RemoveReputationAnalysisResponse struct from reputation_analysis.go.
    """
    forward_to_http_header: bool = False  # json:"forwardToHTTPHeader"
    forward_shared_ip_to_http_header_and_siem: bool = False  # forwardSharedIPToHTTPHeaderAndSIEM


# =============================================================================
# Match Target (from match_target.go)
# =============================================================================


@dataclass
class BypassNetworkList:
    """Bypass network list reference.

    Mirrors Go anonymous struct in match_target.go BypassNetworkLists.
    """
    name: str = ""  # json:"name"
    id: str = ""  # json:"id"


@dataclass
class GetMatchTargetsRequest:
    """Request for listing match targets.

    Mirrors Go GetMatchTargetsRequest struct from match_target.go.
    """
    config_id: int = 0  # json:"configId"
    config_version: int = 0  # json:"configVersion"
    target_id: int = 0  # json:"-"


@dataclass
class GetMatchTargetsResponse:
    """Response from listing match targets.

    Mirrors Go GetMatchTargetsResponse struct from match_target.go.
    """
    match_targets: dict = field(default_factory=dict)  # json:"matchTargets"


@dataclass
class GetMatchTargetRequest:
    """Request for getting a single match target.

    Mirrors Go GetMatchTargetRequest struct from match_target.go.
    """
    config_id: int = 0  # json:"configId"
    config_version: int = 0  # json:"configVersion"
    target_id: int = 0  # json:"-"


@dataclass
class GetMatchTargetResponse:
    """Response from getting a single match target.

    Mirrors Go GetMatchTargetResponse struct from match_target.go.
    """
    type: str = ""  # json:"type"
    apis: list[dict] = field(default_factory=list)  # json:"apis"
    default_file: str = ""  # json:"defaultFile"
    hostnames: list[str] = field(default_factory=list)  # json:"hostnames"
    file_paths: list[str] = field(default_factory=list)  # json:"filePaths"
    file_extensions: list[str] = field(default_factory=list)  # json:"fileExtensions"
    target_id: int = 0  # json:"targetId"


@dataclass
class CreateMatchTargetRequest:
    """Request for creating a match target.

    Mirrors Go CreateMatchTargetRequest struct from match_target.go.
    """
    type: str = ""  # json:"-"
    config_id: int = 0  # json:"-"
    config_version: int = 0  # json:"-"
    json_payload_raw: Any = None  # json:"-" (json.RawMessage)


@dataclass
class CreateMatchTargetResponse:
    """Response from creating a match target.

    Mirrors Go CreateMatchTargetResponse struct from match_target.go.
    """
    m_type: str = ""  # json:"type"
    target_id: int = 0  # json:"targetId"
    hostnames: list[str] = field(default_factory=list)  # json:"hostnames"
    file_paths: list[str] = field(default_factory=list)  # json:"filePaths"
    file_extensions: list[str] = field(default_factory=list)  # json:"fileExtensions"


@dataclass
class UpdateMatchTargetRequest:
    """Request for updating a match target.

    Mirrors Go UpdateMatchTargetRequest struct from match_target.go.
    """
    config_id: int = 0  # json:"-"
    config_version: int = 0  # json:"-"
    json_payload_raw: Any = None  # json:"-" (json.RawMessage)
    target_id: int = 0  # json:"-"


@dataclass
class UpdateMatchTargetResponse:
    """Response from updating a match target.

    Mirrors Go UpdateMatchTargetResponse struct from match_target.go.
    """
    type: str = ""  # json:"type"
    config_id: int = 0  # json:"configId"
    config_version: int = 0  # json:"configVersion"
    target_id: int = 0  # json:"targetId"


@dataclass
class RemoveMatchTargetRequest:
    """Request for removing a match target.

    Mirrors Go RemoveMatchTargetRequest struct from match_target.go.
    """
    config_id: int = 0  # json:"-"
    config_version: int = 0  # json:"-"
    target_id: int = 0  # json:"-"


@dataclass
class RemoveMatchTargetResponse:
    """Response from removing a match target.

    Mirrors Go RemoveMatchTargetResponse struct from match_target.go.
    """
    type: str = ""  # json:"type"
    config_id: int = 0  # json:"configId"
    config_version: int = 0  # json:"configVersion"
    target_id: int = 0  # json:"targetId"


# =============================================================================
# Match Target Sequence (from match_target_sequence.go)
# =============================================================================


@dataclass
class MatchTargetItem:
    """Item in match target sequence.

    Mirrors Go MatchTargetItem struct from match_target_sequence.go.
    """
    sequence: int = 0  # json:"sequence"
    target_id: int = 0  # json:"targetId"


@dataclass
class GetMatchTargetSequenceRequest:
    """Request for getting match target sequence.

    Mirrors Go GetMatchTargetSequenceRequest struct.
    """
    config_id: int = 0  # json:"configId"
    config_version: int = 0  # json:"configVersion"
    type: str = ""  # json:"type"


@dataclass
class GetMatchTargetSequenceResponse:
    """Response from getting match target sequence.

    Mirrors Go GetMatchTargetSequenceResponse struct.
    """
    target_sequence: list[dict] = field(default_factory=list)  # json:"targetSequence"
    type: str = ""  # json:"type"


@dataclass
class UpdateMatchTargetSequenceRequest:
    """Request for updating match target sequence.

    Mirrors Go UpdateMatchTargetSequenceRequest struct.
    """
    config_id: int = 0  # json:"-"
    config_version: int = 0  # json:"-"
    target_sequence: list[dict] = field(default_factory=list)  # json:"targetSequence"
    type: str = ""  # json:"type"


@dataclass
class UpdateMatchTargetSequenceResponse:
    """Response from updating match target sequence.

    Mirrors Go UpdateMatchTargetSequenceResponse struct.
    """
    target_sequence: list[dict] = field(default_factory=list)  # json:"targetSequence"
    type: str = ""  # json:"type"


# =============================================================================
# Rule (from rule.go) — KEY FILE
# =============================================================================


@dataclass
class SpecificHeaderCookieOrParamNameValuePtr:
    """Specific header/cookie/param name-value pair.

    Mirrors Go SpecificHeaderCookieOrParamNameValuePtr struct from rule.go.
    """
    name: Any = None  # json:"name" (*json.RawMessage)
    selector: str = ""  # json:"selector"
    value: Any = None  # json:"value" (*json.RawMessage)


@dataclass
class SpecificHeaderCookieOrParamPrefixPtr:
    """Specific header/cookie/param prefix.

    Mirrors Go SpecificHeaderCookieOrParamPrefixPtr struct from rule.go.
    """
    prefix: str = ""  # json:"prefix"
    selector: str = ""  # json:"selector"


@dataclass
class RuleException:
    """Exception configuration for a rule.

    Mirrors Go RuleException struct from rule.go.
    """
    any_header_cookie_or_param: list[str] = field(default_factory=list)  # anyHeaderCookieOrParam
    header_cookie_or_param_values: list[str] = field(default_factory=list)
    specific_header_cookie_or_param_name_value: list[dict] = field(default_factory=list)
    specific_header_cookie_or_param_names: list[dict] | None = None
    specific_header_cookie_or_param_prefix: list[dict] = field(default_factory=list)
    specific_header_cookie_param_xml_or_json_names: list[dict] = field(default_factory=list)


@dataclass
class RuleConditionException:
    """Combined conditions and exceptions for a rule.

    Mirrors Go RuleConditionException struct from rule.go.
    """
    conditions: list[dict] | None = None  # json:"conditions" (*RuleConditions)
    exception: dict | None = None  # json:"exception" (*RuleException)
    advanced_exceptions_list: dict | None = None  # json:"advancedExceptions" (*AdvancedExceptions)


@dataclass
class GetRulesRequest:
    """Request for listing rules.

    Mirrors Go GetRulesRequest struct from rule.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    rule_id: int = 0  # json:"-"


@dataclass
class GetRulesResponse:
    """Response from listing rules.

    Mirrors Go GetRulesResponse struct from rule.go.
    """
    rules: list[dict] = field(default_factory=list)  # json:"ruleActions"


@dataclass
class GetRuleRequest:
    """Request for getting a single rule.

    Mirrors Go GetRuleRequest struct from rule.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    rule_id: int = 0  # json:"-"


@dataclass
class GetRuleResponse:
    """Response from getting a single rule.

    Mirrors Go GetRuleResponse struct from rule.go.
    """
    action: str = ""  # json:"action"
    condition_exception: dict | None = None  # json:"conditionException"


@dataclass
class UpdateRuleRequest:
    """Request for updating a rule.

    Mirrors Go UpdateRuleRequest struct from rule.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    rule_id: int = 0  # json:"-"
    action: str = ""  # json:"action"
    json_payload_raw: Any = None  # json:"conditionException" (json.RawMessage)


@dataclass
class UpdateRuleResponse:
    """Response from updating a rule.

    Mirrors Go UpdateRuleResponse struct from rule.go.
    """
    action: str = ""  # json:"action"
    condition_exception: dict | None = None  # json:"conditionException"


@dataclass
class UpdateConditionExceptionRequest:
    """Request for updating condition exception.

    Mirrors Go UpdateConditionExceptionRequest struct from rule.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    rule_id: int = 0  # json:"-"
    conditions: list[dict] | None = None  # json:"conditions"
    exception: dict | None = None  # json:"exception"
    advanced_exceptions_list: dict | None = None  # json:"advancedExceptions"


@dataclass
class UpdateConditionExceptionResponse:
    """Response from updating condition exception.

    Mirrors Go UpdateConditionExceptionResponse struct from rule.go.
    Empty response.
    """


# =============================================================================
# Rule Upgrade (from rule_upgrade.go)
# =============================================================================


@dataclass
class RulesetUpdateData:
    """Data about ruleset updates.

    Mirrors Go RulesetUpdateData struct from rule_upgrade.go.
    """
    deleted_rules: list[dict] | None = None  # json:"deletedRules" (*RuleData)
    new_rules: list[dict] | None = None  # json:"newRules" (*RuleData)
    updated_rules: list[dict] | None = None  # json:"updatedRules" (*RuleData)
    deleted_attack_groups: list[dict] | None = None  # json:"deletedAttackGroups" (*GroupData)
    updated_attack_groups: list[dict] | None = None  # json:"updatedAttackGroups" (*GroupData)
    new_attack_groups: list[dict] | None = None  # json:"newAttackGroups" (*GroupData)


@dataclass
class GetRuleUpgradeRequest:
    """Request for getting rule upgrade details.

    Mirrors Go GetRuleUpgradeRequest struct from rule_upgrade.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"


@dataclass
class GetRuleUpgradeResponse:
    """Response from getting rule upgrade details.

    Mirrors Go GetRuleUpgradeResponse struct from rule_upgrade.go.
    """
    current: str = ""  # json:"current"
    evaluating: str = ""  # json:"evaluating"
    latest: str = ""  # json:"latest"
    krs_to_eval_updates: dict | None = None  # json:"KRSToEvalUpdates" (*RulesetUpdateData)
    eval_to_eval_updates: dict | None = None  # json:"evalToEvalUpdates" (*RulesetUpdateData)
    krs_to_latest_updates: dict | None = None  # json:"KRSToLatestUpdates" (*RulesetUpdateData)


@dataclass
class UpdateRuleUpgradeRequest:
    """Request for updating rule upgrade.

    Mirrors Go UpdateRuleUpgradeRequest struct from rule_upgrade.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    upgrade: str = ""  # json:"upgrade"
    mode: str = ""  # json:"mode"


@dataclass
class UpdateRuleUpgradeResponse:
    """Response from updating rule upgrade.

    Mirrors Go UpdateRuleUpgradeResponse struct from rule_upgrade.go.
    """
    current: str = ""  # json:"current"
    mode: str = ""  # json:"mode"
    eval: str = ""  # json:"eval"


# =============================================================================
# Penalty Box (from penalty_box.go)
# =============================================================================


@dataclass
class GetPenaltyBoxRequest:
    """Request for getting penalty box settings.

    Mirrors Go GetPenaltyBoxRequest struct from penalty_box.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    action: str = ""  # json:"action"
    penalty_box_protection: bool = False  # json:"penaltyBoxProtection"


@dataclass
class GetPenaltyBoxResponse:
    """Response from getting penalty box settings.

    Mirrors Go GetPenaltyBoxResponse struct from penalty_box.go.
    """
    action: str = ""  # json:"action"
    penalty_box_protection: bool = False  # json:"penaltyBoxProtection"


@dataclass
class UpdatePenaltyBoxRequest:
    """Request for updating penalty box settings.

    Mirrors Go UpdatePenaltyBoxRequest struct from penalty_box.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    action: str = ""  # json:"action"
    penalty_box_protection: bool = False  # json:"penaltyBoxProtection"


@dataclass
class UpdatePenaltyBoxResponse:
    """Response from updating penalty box settings.

    Mirrors Go UpdatePenaltyBoxResponse struct from penalty_box.go.
    """
    action: str = ""  # json:"action"
    penalty_box_protection: bool = False  # json:"penaltyBoxProtection"


# =============================================================================
# Penalty Box Conditions (from penalty_box_conditions.go)
# =============================================================================


@dataclass
class PenaltyBoxConditionsPayload:
    """Payload for penalty box conditions.

    Mirrors Go PenaltyBoxConditionsPayload struct from penalty_box_conditions.go.
    """
    condition_operator: str = ""  # json:"conditionOperator"
    conditions: list[dict] | None = None  # json:"conditions" (*RuleConditions)


@dataclass
class GetPenaltyBoxConditionsRequest:
    """Request for getting penalty box conditions.

    Mirrors Go GetPenaltyBoxConditionsRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"


# GetPenaltyBoxConditionsResponse is an alias for PenaltyBoxConditionsPayload
GetPenaltyBoxConditionsResponse = PenaltyBoxConditionsPayload


@dataclass
class UpdatePenaltyBoxConditionsRequest:
    """Request for updating penalty box conditions.

    Mirrors Go UpdatePenaltyBoxConditionsRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    conditions_payload: dict | None = None  # json:"conditionsPayload"


# UpdatePenaltyBoxConditionsResponse is an alias for PenaltyBoxConditionsPayload
UpdatePenaltyBoxConditionsResponse = PenaltyBoxConditionsPayload


# =============================================================================
# Rapid Rule (from rapid_rule.go)
# =============================================================================


@dataclass
class PolicyRapidRule:
    """Rapid rule in a security policy.

    Mirrors Go PolicyRapidRule struct from rapid_rule.go.
    """
    id: int = 0  # json:"id"
    action: str = ""  # json:"action"
    lock: bool = False  # json:"lock"
    name: str = ""  # json:"title"
    version: int = 0  # json:"version"
    risk_score_groups: list[dict] = field(default_factory=list)  # json:"riskScoreGroups"
    condition_exception: dict | None = None  # json:"conditionException"
    expired: bool | None = None  # json:"expired" (*bool)
    expire_in_days: int | None = None  # json:"expireInDays" (*int64)


@dataclass
class GetRapidRulesRequest:
    """Request for getting rapid rules.

    Mirrors Go GetRapidRulesRequest struct from rapid_rule.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    rule_id: int = 0  # json:"-"
    include_expiry_details: bool = False  # json:"-"


@dataclass
class GetRapidRulesResponse:
    """Response from getting rapid rules.

    Mirrors Go GetRapidRulesResponse struct from rapid_rule.go.
    """
    rules: list[dict] = field(default_factory=list)  # json:"ruleActions"


# GetRapidRulesDefaultActionRequest is an alias for GetRapidRulesRequest
GetRapidRulesDefaultActionRequest = GetRapidRulesRequest


@dataclass
class GetRapidRulesDefaultActionResponse:
    """Response from getting rapid rules default action.

    Mirrors Go GetRapidRulesDefaultActionResponse struct from rapid_rule.go.
    """
    action: str = ""  # json:"action"


# GetRapidRulesStatusRequest is an alias for GetRapidRulesRequest
GetRapidRulesStatusRequest = GetRapidRulesRequest


@dataclass
class GetRapidRulesStatusResponse:
    """Response from getting rapid rules status.

    Mirrors Go GetRapidRulesStatusResponse struct from rapid_rule.go.
    """
    enabled: bool = False  # json:"enabled"


@dataclass
class UpdateRapidRulesStatusRequestBody:
    """Request body for updating rapid rules status.

    Mirrors Go UpdateRapidRulesStatusRequestBody struct from rapid_rule.go.
    """
    enabled: bool | None = None  # json:"enabled" (*bool)


@dataclass
class UpdateRapidRulesStatusRequest:
    """Request for updating rapid rules status.

    Mirrors Go UpdateRapidRulesStatusRequest struct from rapid_rule.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    body: dict | None = None  # json:"-" (*UpdateRapidRulesStatusRequestBody)


# UpdateRapidRulesStatusResponse is an alias for GetRapidRulesStatusResponse
UpdateRapidRulesStatusResponse = GetRapidRulesStatusResponse


@dataclass
class UpdateRapidRulesDefaultActionRequestBody:
    """Request body for updating rapid rules default action.

    Mirrors Go UpdateRapidRulesDefaultActionRequestBody struct.
    """
    action: str = ""  # json:"action"


@dataclass
class UpdateRapidRulesDefaultActionRequest:
    """Request for updating rapid rules default action.

    Mirrors Go UpdateRapidRulesDefaultActionRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    body: dict | None = None  # json:"-" (*UpdateRapidRulesDefaultActionRequestBody)


# UpdateRapidRulesDefaultActionResponse is an alias for GetRapidRulesDefaultActionResponse
UpdateRapidRulesDefaultActionResponse = GetRapidRulesDefaultActionResponse


@dataclass
class UpdateRapidRuleActionLockRequestBody:
    """Request body for updating rapid rule action lock.

    Mirrors Go UpdateRapidRuleActionLockRequestBody struct.
    """
    enabled: bool | None = None  # json:"enabled" (*bool)


@dataclass
class UpdateRapidRuleActionLockRequest:
    """Request for updating rapid rule action lock.

    Mirrors Go UpdateRapidRuleActionLockRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    rule_id: int = 0  # json:"-"
    body: dict | None = None  # json:"-" (*UpdateRapidRuleActionLockRequestBody)


# UpdateRapidRuleActionLockResponse is an alias for GetRapidRulesStatusResponse
UpdateRapidRuleActionLockResponse = GetRapidRulesStatusResponse


@dataclass
class UpdateRapidRuleActionRequestBody:
    """Request body for updating rapid rule action.

    Mirrors Go UpdateRapidRuleActionRequestBody struct.
    """
    action: str = ""  # json:"action"


@dataclass
class UpdateRapidRuleActionRequest:
    """Request for updating rapid rule action.

    Mirrors Go UpdateRapidRuleActionRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    rule_id: int = 0  # json:"-"
    rule_version: int = 0  # json:"-"
    body: dict | None = None  # json:"-" (*UpdateRapidRuleActionRequestBody)


@dataclass
class UpdateRapidRuleActionResponse:
    """Response from updating rapid rule action.

    Mirrors Go UpdateRapidRuleActionResponse struct.
    """
    action: str = ""  # json:"action"
    lock: bool = False  # json:"lock"


@dataclass
class UpdateRapidRuleExceptionRequest:
    """Request for updating rapid rule exception.

    Mirrors Go UpdateRapidRuleExceptionRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    rule_id: int = 0  # json:"-"
    body: dict | None = None  # json:"-" (*RuleConditionException)


# UpdateRapidRuleExceptionResponse is an alias for RuleConditionException
UpdateRapidRuleExceptionResponse = RuleConditionException


@dataclass
class RapidRuleDetails:
    """Detailed rapid rule info.

    Mirrors Go RapidRuleDetails struct from rapid_rule.go.
    """
    id: int = 0  # json:"id"
    action: str = ""  # json:"action"
    lock: bool = False  # json:"lock"
    name: str = ""  # json:"title"
    attack_group: str = ""  # json:"attackGroup"
    attack_group_exception: dict | None = None  # json:"attackGroupException"
    condition_exception: dict | None = None  # json:"conditionException"
    expired: bool | None = None  # json:"expired" (*bool)
    expire_in_days: int | None = None  # json:"expireInDays" (*int64)


@dataclass
class RuleDefinition:
    """Individual rule definition.

    Mirrors Go RuleDefinition struct from rapid_rule.go.
    """
    id: int | None = None  # json:"id" (*int64)
    action: str | None = None  # json:"action" (*string)
    lock: bool | None = None  # json:"lock" (*bool)
    condition_exception: dict | None = None  # json:"conditionException"


# =============================================================================
# WAF Mode (from waf_mode.go)
# =============================================================================


@dataclass
class GetWAFModeRequest:
    """Request for getting WAF mode.

    Mirrors Go GetWAFModeRequest struct from waf_mode.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    current: str = ""  # json:"current"
    mode: str = ""  # json:"mode"
    eval: str = ""  # json:"eval"


@dataclass
class GetWAFModeResponse:
    """Response from getting WAF mode.

    Mirrors Go GetWAFModeResponse struct from waf_mode.go.
    """
    current: str = ""  # json:"current"
    mode: str = ""  # json:"mode"
    eval: str = ""  # json:"eval"
    evaluating: str = ""  # json:"evaluating"
    expires: str = ""  # json:"expires"


@dataclass
class UpdateWAFModeRequest:
    """Request for updating WAF mode.

    Mirrors Go UpdateWAFModeRequest struct from waf_mode.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    mode: str = ""  # json:"mode"


@dataclass
class UpdateWAFModeResponse:
    """Response from updating WAF mode.

    Mirrors Go UpdateWAFModeResponse struct from waf_mode.go.
    """
    current: str = ""  # json:"current"
    mode: str = ""  # json:"mode"


# =============================================================================
# WAF Protection (from waf_protection.go)
# =============================================================================


@dataclass
class GetWAFProtectionRequest:
    """Request for getting WAF protection status.

    Mirrors Go GetWAFProtectionRequest struct from waf_protection.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    apply_application_layer_controls: bool = False  # json:"applyApplicationLayerControls"


# GetWAFProtectionResponse is an alias for ProtectionsResponse
# Defined after ProtectionsResponse below


@dataclass
class GetWAFProtectionsRequest:
    """Request for getting WAF protections (plural, deprecated).

    Mirrors Go GetWAFProtectionsRequest struct from waf_protection.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    apply_application_layer_controls: bool = False  # json:"applyApplicationLayerControls"


# GetWAFProtectionsResponse is an alias for ProtectionsResponse
# Defined after ProtectionsResponse below


@dataclass
class UpdateWAFProtectionRequest:
    """Request for updating WAF protection.

    Mirrors Go UpdateWAFProtectionRequest struct from waf_protection.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    apply_application_layer_controls: bool = False  # json:"applyApplicationLayerControls"


# UpdateWAFProtectionResponse is an alias for ProtectionsResponse
# Defined after ProtectionsResponse below


# =============================================================================
# IP Geo (from ip_geo.go)
# =============================================================================


@dataclass
class IPGeoNetworkLists:
    """Network lists for IP/Geo controls.

    Mirrors Go IPGeoNetworkLists struct from ip_geo.go.
    """
    network_list: list[str] = field(default_factory=list)  # json:"networkList"
    action: str = ""  # json:"action,omitempty"


@dataclass
class IPGeoGeoControls:
    """Geo controls for IP/Geo.

    Mirrors Go IPGeoGeoControls struct from ip_geo.go.
    """
    blocked_ip_network_lists: dict | None = None  # blockedIPNetworkLists


@dataclass
class IPGeoASNControls:
    """ASN controls for IP/Geo.

    Mirrors Go IPGeoASNControls struct from ip_geo.go.
    """
    blocked_ip_network_lists: dict | None = None  # blockedIPNetworkLists


@dataclass
class IPGeoIPControls:
    """IP controls for IP/Geo.

    Mirrors Go IPGeoIPControls struct from ip_geo.go.
    """
    allowed_ip_network_lists: dict | None = None  # allowedIPNetworkLists
    blocked_ip_network_lists: dict | None = None  # blockedIPNetworkLists


@dataclass
class UkraineGeoControl:
    """Ukraine geo control settings.

    Mirrors Go UkraineGeoControl struct from ip_geo.go.
    """
    action: str = ""  # json:"action"


@dataclass
class GetIPGeoRequest:
    """Request for getting IP/Geo settings.

    Mirrors Go GetIPGeoRequest struct from ip_geo.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"


@dataclass
class IPGeoFirewall:
    """IP Geo firewall settings.

    Mirrors Go IPGeoFirewall struct from ip_geo.go.
    """
    block: str = ""  # json:"block"
    geo_controls: dict | None = None  # json:"geoControls"
    ip_controls: dict | None = None  # json:"ipControls"
    asn_controls: dict | None = None  # json:"asnControls"
    ukraine_geo_controls: dict | None = None  # json:"ukraineGeoControls"


# GetIPGeoResponse is an alias for IPGeoFirewall
GetIPGeoResponse = IPGeoFirewall


@dataclass
class UpdateIPGeoRequest:
    """Request for updating IP/Geo settings.

    Mirrors Go UpdateIPGeoRequest struct from ip_geo.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    block: str = ""  # json:"block"
    geo_controls: dict | None = None  # json:"geoControls"
    ip_controls: dict | None = None  # json:"ipControls"
    asn_controls: dict | None = None  # json:"asnControls"
    ukraine_geo_controls: dict | None = None  # json:"ukraineGeoControls"


# UpdateIPGeoResponse is an alias for IPGeoFirewall
UpdateIPGeoResponse = IPGeoFirewall


# =============================================================================
# IP Geo Protection (from ip_geo_protection.go)
# =============================================================================


@dataclass
class GetIPGeoProtectionRequest:
    """Request for getting IP/Geo protection status.

    Mirrors Go GetIPGeoProtectionRequest struct from ip_geo_protection.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"


# GetIPGeoProtectionResponse is an alias for ProtectionsResponse
# Defined after ProtectionsResponse below


@dataclass
class GetIPGeoProtectionsRequest:
    """Request for getting IP/Geo protections (plural, deprecated).

    Mirrors Go GetIPGeoProtectionsRequest struct from ip_geo_protection.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"


# GetIPGeoProtectionsResponse is an alias for ProtectionsResponse


@dataclass
class UpdateIPGeoProtectionRequest:
    """Request for updating IP/Geo protection.

    Mirrors Go UpdateIPGeoProtectionRequest struct from ip_geo_protection.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    apply_network_layer_controls: bool = False  # json:"applyNetworkLayerControls"


# UpdateIPGeoProtectionResponse is an alias for ProtectionsResponse


# =============================================================================
# Rate Protection (from rate_protection.go)
# =============================================================================


@dataclass
class GetRateProtectionRequest:
    """Request for getting rate protection status.

    Mirrors Go GetRateProtectionRequest struct from rate_protection.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    apply_rate_controls: bool = False  # json:"applyRateControls"


# GetRateProtectionResponse is an alias for ProtectionsResponse


@dataclass
class GetRateProtectionsRequest:
    """Request for getting rate protections (plural, deprecated).

    Mirrors Go GetRateProtectionsRequest struct from rate_protection.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    apply_rate_controls: bool = False  # json:"applyRateControls"


# GetRateProtectionsResponse is an alias for ProtectionsResponse


@dataclass
class UpdateRateProtectionRequest:
    """Request for updating rate protection.

    Mirrors Go UpdateRateProtectionRequest struct from rate_protection.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    apply_rate_controls: bool = False  # json:"applyRateControls"


# UpdateRateProtectionResponse is an alias for ProtectionsResponse


# =============================================================================
# Reputation Protection (from reputation_protection.go)
# =============================================================================


@dataclass
class GetReputationProtectionRequest:
    """Request for getting reputation protection status.

    Mirrors Go GetReputationProtectionRequest struct from reputation_protection.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    apply_reputation_controls: bool = False  # json:"applyReputationControls"


# GetReputationProtectionResponse is an alias for ProtectionsResponse


@dataclass
class GetReputationProtectionsRequest:
    """Request for getting reputation protections (plural, deprecated).

    Mirrors Go GetReputationProtectionsRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    apply_reputation_controls: bool = False  # json:"applyReputationControls"


# GetReputationProtectionsResponse is an alias for ProtectionsResponse


@dataclass
class UpdateReputationProtectionRequest:
    """Request for updating reputation protection.

    Mirrors Go UpdateReputationProtectionRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    apply_reputation_controls: bool = False  # json:"applyReputationControls"


# UpdateReputationProtectionResponse is an alias for ProtectionsResponse


@dataclass
class RemoveReputationProtectionRequest:
    """Request for removing reputation protection (deprecated).

    Mirrors Go RemoveReputationProtectionRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    apply_reputation_controls: bool = False  # json:"applyReputationControls"


# RemoveReputationProtectionResponse is an alias for ProtectionsResponse


# =============================================================================
# Slow Post Protection (from slowpost_protection.go)
# =============================================================================


@dataclass
class GetSlowPostProtectionRequest:
    """Request for getting slow post protection status.

    Mirrors Go GetSlowPostProtectionRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    apply_slow_post_controls: bool = False  # json:"applySlowPostControls"


# GetSlowPostProtectionResponse is an alias for ProtectionsResponse


@dataclass
class GetSlowPostProtectionsRequest:
    """Request for getting slow post protections (plural, deprecated).

    Mirrors Go GetSlowPostProtectionsRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    apply_slow_post_controls: bool = False  # json:"applySlowPostControls"


# GetSlowPostProtectionsResponse is an alias for ProtectionsResponse


@dataclass
class UpdateSlowPostProtectionRequest:
    """Request for updating slow post protection.

    Mirrors Go UpdateSlowPostProtectionRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    apply_slow_post_controls: bool = False  # json:"applySlowPostControls"


# UpdateSlowPostProtectionResponse is an alias for ProtectionsResponse


# =============================================================================
# ProtectionsResponse (from api_constraints_protection.go) and all aliases
# =============================================================================


@dataclass
class ProtectionsResponse:
    """Shared protections response used by all protection endpoints.

    Mirrors Go ProtectionsResponse struct from api_constraints_protection.go.
    """
    apply_api_constraints: bool = False  # json:"applyApiConstraints,omitempty"
    apply_application_layer_controls: bool = False  # json:"applyApplicationLayerControls,omitempty"
    apply_botman_controls: bool = False  # json:"applyBotmanControls,omitempty"
    apply_malware_controls: bool = False  # json:"applyMalwareControls,omitempty"
    apply_network_layer_controls: bool = False  # json:"applyNetworkLayerControls,omitempty"
    apply_rate_controls: bool = False  # json:"applyRateControls,omitempty"
    apply_reputation_controls: bool = False  # json:"applyReputationControls,omitempty"
    apply_slow_post_controls: bool = False  # json:"applySlowPostControls,omitempty"


# Protection response aliases — all point to ProtectionsResponse
GetWAFProtectionResponse = ProtectionsResponse
GetWAFProtectionsResponse = ProtectionsResponse
UpdateWAFProtectionResponse = ProtectionsResponse
GetIPGeoProtectionResponse = ProtectionsResponse
GetIPGeoProtectionsResponse = ProtectionsResponse
UpdateIPGeoProtectionResponse = ProtectionsResponse
GetRateProtectionResponse = ProtectionsResponse
GetRateProtectionsResponse = ProtectionsResponse
UpdateRateProtectionResponse = ProtectionsResponse
GetReputationProtectionResponse = ProtectionsResponse
GetReputationProtectionsResponse = ProtectionsResponse
UpdateReputationProtectionResponse = ProtectionsResponse
RemoveReputationProtectionResponse = ProtectionsResponse
GetSlowPostProtectionResponse = ProtectionsResponse
GetSlowPostProtectionsResponse = ProtectionsResponse
UpdateSlowPostProtectionResponse = ProtectionsResponse


# =============================================================================
# Slow Post Protection Setting (from slow_post_protection_setting.go)
# =============================================================================


@dataclass
class SlowPostProtectionSettingSlowRateThreshold:
    """Slow rate threshold for slow post protection.

    Mirrors Go SlowPostProtectionSettingSlowRateThreshold struct.
    """
    rate: int = 0  # json:"rate"
    period: int = 0  # json:"period"


@dataclass
class SlowPostProtectionSettingDurationThreshold:
    """Duration threshold for slow post protection.

    Mirrors Go SlowPostProtectionSettingDurationThreshold struct.
    """
    timeout: int = 0  # json:"timeout"


@dataclass
class GetSlowPostProtectionSettingsRequest:
    """Request for getting slow post protection settings.

    Mirrors Go GetSlowPostProtectionSettingsRequest struct.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"
    action: str = ""  # json:"action"
    slow_rate_threshold: dict | None = None  # json:"slowRateThreshold"
    duration_threshold: dict | None = None  # json:"durationThreshold"


@dataclass
class GetSlowPostProtectionSettingsResponse:
    """Response from getting slow post protection settings.

    Mirrors Go GetSlowPostProtectionSettingsResponse struct.
    """
    action: str = ""  # json:"action"
    slow_rate_threshold: dict | None = None  # json:"slowRateThreshold"
    duration_threshold: dict | None = None  # json:"durationThreshold"


@dataclass
class UpdateSlowPostProtectionSettingRequest:
    """Request for updating slow post protection setting.

    Mirrors Go UpdateSlowPostProtectionSettingRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    action: str = ""  # json:"action"
    slow_rate_threshold: dict | None = None  # json:"slowRateThreshold"
    duration_threshold: dict | None = None  # json:"durationThreshold"


@dataclass
class UpdateSlowPostProtectionSettingResponse:
    """Response from updating slow post protection setting.

    Mirrors Go UpdateSlowPostProtectionSettingResponse struct.
    """
    action: str = ""  # json:"action"
    slow_rate_threshold: dict | None = None  # json:"slowRateThreshold"
    duration_threshold: dict | None = None  # json:"durationThreshold"


# =============================================================================
# Malware Policy (from malware_policy.go)
# =============================================================================


@dataclass
class EncodedContentAttribute:
    """Encoded content attribute for malware content types.

    Mirrors Go EncodedContentAttribute struct from malware_policy.go.
    """
    path: str = ""  # json:"path"
    encoding: list[str] = field(default_factory=list)  # json:"encoding"


@dataclass
class ContentType:
    """Content type for malware policy.

    Mirrors Go ContentType struct from malware_policy.go.
    """
    name: str = ""  # json:"name"
    encoded_content_attributes: list[dict] = field(default_factory=list)  # encodedContentAttributes


@dataclass
class MalwarePolicyBody:
    """Malware policy body.

    Mirrors Go MalwarePolicyBody struct from malware_policy.go.
    """
    malware_policy_id: int = 0  # json:"id"
    name: str = ""  # json:"name"
    description: str = ""  # json:"description"
    hostnames: list[str] = field(default_factory=list)  # json:"hostnames"
    paths: list[str] = field(default_factory=list)  # json:"paths"
    content_types: list[dict] = field(default_factory=list)  # json:"contentTypes"
    log_filename: str = ""  # json:"logFilename"
    allow_list_id: int = 0  # json:"allowlistId"
    block_list_id: int = 0  # json:"blocklistId"


@dataclass
class CreateMalwarePolicyRequest:
    """Request for creating a malware policy.

    Mirrors Go CreateMalwarePolicyRequest struct from malware_policy.go.
    """
    config_id: int = 0  # json:"-"
    config_version: int = 0  # json:"-"
    policy: dict | None = None  # json:"-" (*MalwarePolicyBody)


@dataclass
class MalwarePolicyResponse:
    """Response from malware policy operations.

    Mirrors Go MalwarePolicyResponse struct from malware_policy.go.
    """
    malware_policy_id: int = 0  # json:"id"
    name: str = ""  # json:"name"
    description: str = ""  # json:"description"
    hostnames: list[str] = field(default_factory=list)  # json:"hostnames"
    paths: list[str] = field(default_factory=list)  # json:"paths"
    content_types: list[dict] = field(default_factory=list)  # json:"contentTypes"


@dataclass
class GetMalwarePolicyRequest:
    """Request for getting a malware policy.

    Mirrors Go GetMalwarePolicyRequest struct from malware_policy.go.
    """
    config_id: int = 0  # json:"-"
    config_version: int = 0  # json:"-"
    malware_policy_id: int = 0  # json:"-"


@dataclass
class GetMalwarePoliciesRequest:
    """Request for listing malware policies.

    Mirrors Go GetMalwarePoliciesRequest struct from malware_policy.go.
    """
    config_id: int = 0  # json:"-"
    config_version: int = 0  # json:"-"
    malware_policy_id: int = 0  # json:"-"


@dataclass
class MalwarePoliciesResponse:
    """Response from listing malware policies.

    Mirrors Go MalwarePoliciesResponse struct from malware_policy.go.
    """
    malware_policies: list[dict] = field(default_factory=list)  # json:"malwarePolicies"


@dataclass
class UpdateMalwarePolicyRequest:
    """Request for updating a malware policy.

    Mirrors Go UpdateMalwarePolicyRequest struct from malware_policy.go.
    """
    config_id: int = 0  # json:"-"
    config_version: int = 0  # json:"-"
    malware_policy_id: int = 0  # json:"-"
    policy: dict | None = None  # json:"-" (*MalwarePolicyBody)


@dataclass
class RemoveMalwarePolicyRequest:
    """Request for removing a malware policy.

    Mirrors Go RemoveMalwarePolicyRequest struct from malware_policy.go.
    """
    config_id: int = 0  # json:"-"
    config_version: int = 0  # json:"-"
    malware_policy_id: int = 0  # json:"-"


# =============================================================================
# Malware Policy Action (from malware_policy_action.go)
# =============================================================================


@dataclass
class MalwarePolicyActionBody:
    """Malware policy action body.

    Mirrors Go MalwarePolicyActionBody struct from malware_policy_action.go.
    """
    malware_policy_id: int = 0  # json:"id"
    action: str = ""  # json:"action"
    unscanned_action: str = ""  # json:"unscannedAction"


@dataclass
class GetMalwarePolicyActionsRequest:
    """Request for getting malware policy actions.

    Mirrors Go GetMalwarePolicyActionsRequest struct.
    """
    config_id: int = 0  # json:"configID"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyID"
    malware_policy_id: int = 0  # json:"id"


@dataclass
class GetMalwarePolicyActionsResponse:
    """Response from getting malware policy actions.

    Mirrors Go GetMalwarePolicyActionsResponse struct.
    """
    malware_policy_actions: list[dict] = field(default_factory=list)  # json:"malwarePolicyActions"


@dataclass
class UpdateMalwarePolicyActionRequest:
    """Request for updating a single malware policy action.

    Mirrors Go UpdateMalwarePolicyActionRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    malware_policy_id: int = 0  # json:"-"
    action: str = ""  # json:"action"
    unscanned_action: str = ""  # json:"unscannedAction"


@dataclass
class UpdateMalwarePolicyActionResponse:
    """Response from updating a single malware policy action.

    Mirrors Go UpdateMalwarePolicyActionResponse struct.
    """
    malware_policy_actions: list[dict] = field(default_factory=list)  # json:"malwarePolicyActions"


@dataclass
class UpdateMalwarePolicyActionsRequest:
    """Request for updating multiple malware policy actions.

    Mirrors Go UpdateMalwarePolicyActionsRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    malware_policy_actions: Any = None  # json:"-" (json.RawMessage)


# UpdateMalwarePolicyActionsResponse is an alias for GetMalwarePolicyActionsResponse
UpdateMalwarePolicyActionsResponse = GetMalwarePolicyActionsResponse


# =============================================================================
# Malware Content Types (from malware_content_types.go)
# =============================================================================


@dataclass
class GetMalwareContentTypesRequest:
    """Request for getting malware content types.

    Mirrors Go GetMalwareContentTypesRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"


@dataclass
class GetMalwareContentTypesResponse:
    """Response from getting malware content types.

    Mirrors Go GetMalwareContentTypesResponse struct.
    """
    content_types: list[dict] = field(default_factory=list)  # json:"malwareContentTypes"


# =============================================================================
# Malware Protection (from malware_protection.go)
# =============================================================================


@dataclass
class GetMalwareProtectionRequest:
    """Request for getting malware protection status.

    Mirrors Go GetMalwareProtectionRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"


@dataclass
class GetMalwareProtectionResponse:
    """Response from getting malware protection status.

    Mirrors Go GetMalwareProtectionResponse struct.
    """
    apply_malware_controls: bool = False  # json:"applyMalwareControls"


@dataclass
class GetMalwareProtectionsRequest:
    """Request for getting malware protections (plural).

    Mirrors Go GetMalwareProtectionsRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"


@dataclass
class GetMalwareProtectionsResponse:
    """Response from getting malware protections (plural).

    Mirrors Go GetMalwareProtectionsResponse struct.
    """
    apply_malware_controls: bool = False  # json:"applyMalwareControls"


@dataclass
class UpdateMalwareProtectionRequest:
    """Request for updating malware protection.

    Mirrors Go UpdateMalwareProtectionRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    apply_malware_controls: bool = False  # json:"applyMalwareControls"


@dataclass
class UpdateMalwareProtectionResponse:
    """Response from updating malware protection.

    Mirrors Go UpdateMalwareProtectionResponse struct.
    """
    apply_malware_controls: bool = False  # json:"applyMalwareControls"


# =============================================================================
# API Endpoints (from api_endpoints.go)
# =============================================================================


@dataclass
class GetApiEndpointsRequest:
    """Request for getting API endpoints.

    Mirrors Go GetApiEndpointsRequest struct from api_endpoints.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    name: str = ""  # json:"-"
    api_id: int = 0  # json:"-"


@dataclass
class GetApiEndpointsResponse:
    """Response from getting API endpoints.

    Mirrors Go GetApiEndpointsResponse struct from api_endpoints.go.
    """
    api_endpoints: list[dict] = field(default_factory=list)  # json:"apiEndpoints"


@dataclass
class Hostnames:
    """Hostnames wrapper.

    Mirrors Go Hostnames struct from api_endpoints.go.
    """
    values: list[str] = field(default_factory=list)  # json:"values"


# =============================================================================
# API Hostname Coverage (from api_hostname_coverage.go)
# =============================================================================


@dataclass
class ConfigurationHostnameCoverage:
    """Configuration reference in hostname coverage.

    Mirrors Go ConfigurationHostnameCoverage struct.
    """
    id: int = 0  # json:"id"
    name: str = ""  # json:"name"
    version: int = 0  # json:"version"


@dataclass
class GetApiHostnameCoverageRequest:
    """Request for getting API hostname coverage.

    Mirrors Go GetApiHostnameCoverageRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    hostname: str = ""  # json:"-"


@dataclass
class GetApiHostnameCoverageResponse:
    """Response from getting API hostname coverage.

    Mirrors Go GetApiHostnameCoverageResponse struct.
    """
    hostname_coverage: list[dict] = field(default_factory=list)  # json:"hostnameCoverage"


# =============================================================================
# API Hostname Coverage Match Targets
# (from api_hostname_coverage_match_targets.go)
# =============================================================================


@dataclass
class HostnameCoverageMatchTargetBypassNetworkLists:
    """Bypass network lists in hostname coverage match targets.

    Mirrors Go anonymous struct inside HostnameCoverageMatchTarget.
    """
    id: str = ""  # json:"id"
    name: str = ""  # json:"name"


@dataclass
class HostnameCoverageMatchTargetEffectiveSecurityControls:
    """Effective security controls in hostname coverage match targets.

    Mirrors Go anonymous struct inside HostnameCoverageMatchTarget.
    """
    apply_account_protection_controls: bool = False  # json:"applyAccountProtectionControls"
    apply_application_layer_controls: bool = False  # json:"applyApplicationLayerControls"
    apply_botman_controls: bool = False  # json:"applyBotmanControls"
    apply_network_layer_controls: bool = False  # json:"applyNetworkLayerControls"
    apply_rate_controls: bool = False  # json:"applyRateControls"
    apply_reputation_controls: bool = False  # json:"applyReputationControls"
    apply_slow_post_controls: bool = False  # json:"applySlowPostControls"


@dataclass
class GetApiHostnameCoverageMatchTargetsRequest:
    """Request for getting hostname coverage match targets.

    Mirrors Go GetApiHostnameCoverageMatchTargetsRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    hostname: str = ""  # json:"-"


@dataclass
class GetApiHostnameCoverageMatchTargetsResponse:
    """Response from getting hostname coverage match targets.

    Mirrors Go GetApiHostnameCoverageMatchTargetsResponse struct.
    """
    match_targets: dict = field(default_factory=dict)  # json:"matchTargets"


# =============================================================================
# API Hostname Coverage Overlapping
# (from api_hostname_coverage_overlapping.go)
# =============================================================================


@dataclass
class GetApiHostnameCoverageOverlappingRequest:
    """Request for getting hostname coverage overlapping.

    Mirrors Go GetApiHostnameCoverageOverlappingRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    hostname: str = ""  # json:"-"


@dataclass
class GetApiHostnameCoverageOverlappingResponse:
    """Response from getting hostname coverage overlapping.

    Mirrors Go GetApiHostnameCoverageOverlappingResponse struct.
    """
    over_lapping_list: list[dict] = field(default_factory=list)  # json:"overLappingList"


# =============================================================================
# API Request Constraints (from api_request_constraints.go)
# =============================================================================


@dataclass
class ApiEndpoint:
    """API endpoint with action.

    Mirrors Go ApiEndpoint struct from api_request_constraints.go.
    """
    id: int = 0  # json:"id"
    action: str = ""  # json:"action"


@dataclass
class GetApiRequestConstraintsRequest:
    """Request for getting API request constraints.

    Mirrors Go GetApiRequestConstraintsRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    api_id: int = 0  # json:"-"


@dataclass
class GetApiRequestConstraintsResponse:
    """Response from getting API request constraints.

    Mirrors Go GetApiRequestConstraintsResponse struct.
    """
    api_endpoints: list[dict] = field(default_factory=list)  # json:"apiEndpoints"


@dataclass
class UpdateApiRequestConstraintsRequest:
    """Request for updating API request constraints.

    Mirrors Go UpdateApiRequestConstraintsRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    api_id: int = 0  # json:"-"
    action: str = ""  # json:"action"


@dataclass
class UpdateApiRequestConstraintsResponse:
    """Response from updating API request constraints.

    Mirrors Go UpdateApiRequestConstraintsResponse struct.
    """
    action: str = ""  # json:"action"


@dataclass
class RemoveApiRequestConstraintsRequest:
    """Request for removing API request constraints.

    Mirrors Go RemoveApiRequestConstraintsRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    api_id: int = 0  # json:"-"
    action: str = ""  # json:"action"


@dataclass
class RemoveApiRequestConstraintsResponse:
    """Response from removing API request constraints.

    Mirrors Go RemoveApiRequestConstraintsResponse struct.
    """
    action: str = ""  # json:"action"


# =============================================================================
# API Constraints Protection (from api_constraints_protection.go)
# =============================================================================


@dataclass
class GetAPIConstraintsProtectionRequest:
    """Request for getting API constraints protection status.

    Mirrors Go GetAPIConstraintsProtectionRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    apply_api_constraints: bool = False  # json:"applyApiConstraints"


# GetAPIConstraintsProtectionResponse is an alias for ProtectionsResponse
GetAPIConstraintsProtectionResponse = ProtectionsResponse


@dataclass
class UpdateAPIConstraintsProtectionRequest:
    """Request for updating API constraints protection.

    Mirrors Go UpdateAPIConstraintsProtectionRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    apply_api_constraints: bool = False  # json:"applyApiConstraints"


# UpdateAPIConstraintsProtectionResponse is an alias for ProtectionsResponse
UpdateAPIConstraintsProtectionResponse = ProtectionsResponse


# =============================================================================
# SIEM Definitions (from siem_definitions.go)
# =============================================================================


@dataclass
class GetSiemDefinitionsRequest:
    """Request for getting SIEM definitions.

    Mirrors Go GetSiemDefinitionsRequest struct from siem_definitions.go.
    """
    id: int = 0  # json:"id"
    siem_definition_name: str = ""  # json:"name"


@dataclass
class GetSiemDefinitionsResponse:
    """Response from getting SIEM definitions.

    Mirrors Go GetSiemDefinitionsResponse struct from siem_definitions.go.
    """
    siem_definitions: list[dict] = field(default_factory=list)  # json:"siemDefinitions"


# =============================================================================
# SIEM Settings (from siem_settings.go)
# =============================================================================


@dataclass
class Exception:  # pylint: disable=redefined-builtin
    """SIEM exception configuration.

    Mirrors Go Exception struct from siem_settings.go.
    """
    protection: str = ""  # json:"protection"
    action_types: list[str] = field(default_factory=list)  # json:"actionTypes"


@dataclass
class GetSiemSettingsRequest:
    """Request for getting SIEM settings.

    Mirrors Go GetSiemSettingsRequest struct from siem_settings.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"


@dataclass
class GetSiemSettingsResponse:
    """Response from getting SIEM settings.

    Mirrors Go GetSiemSettingsResponse struct from siem_settings.go.
    """
    enable_for_all_policies: bool = False  # json:"enableForAllPolicies"
    enable_siem: bool = False  # json:"enableSiem"
    enabled_botman_siem_events: bool = False  # json:"enabledBotmanSiemEvents"
    include_ja4_fingerprint_to_siem: bool | None = None  # includeJA4FingerprintToSiem
    siem_definition_id: int = 0  # json:"siemDefinitionId"
    firewall_policy_ids: list[str] = field(default_factory=list)  # json:"firewallPolicyIds"
    exceptions: list[dict] = field(default_factory=list)  # json:"exceptions"
    username_to_siem: bool | None = None  # json:"usernameToSiem,omitempty" (*bool)


@dataclass
class GetSiemSettingRequest:
    """Request for getting SIEM setting (singular, deprecated).

    Mirrors Go GetSiemSettingRequest struct from siem_settings.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"


@dataclass
class GetSiemSettingResponse:
    """Response from getting SIEM setting (singular, deprecated).

    Mirrors Go GetSiemSettingResponse struct from siem_settings.go.
    """
    enable_for_all_policies: bool = False  # json:"enableForAllPolicies"
    enable_siem: bool = False  # json:"enableSiem"
    enabled_botman_siem_events: bool | None = None  # json:"enabledBotmanSiemEvents" (*bool)
    include_ja4_fingerprint_to_siem: bool | None = None  # includeJA4FingerprintToSiem
    siem_definition_id: int = 0  # json:"siemDefinitionId"
    firewall_policy_ids: list[str] = field(default_factory=list)  # json:"firewallPolicyIds"
    exceptions: list[dict] = field(default_factory=list)  # json:"exceptions"


@dataclass
class UpdateSiemSettingsRequest:
    """Request for updating SIEM settings.

    Mirrors Go UpdateSiemSettingsRequest struct from siem_settings.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    enable_for_all_policies: bool = False  # json:"enableForAllPolicies"
    enable_siem: bool = False  # json:"enableSiem"
    enabled_botman_siem_events: bool = False  # json:"enabledBotmanSiemEvents"
    include_ja4_fingerprint_to_siem: bool | None = None  # includeJA4FingerprintToSiem,omitempty
    siem_definition_id: int = 0  # json:"siemDefinitionId"
    firewall_policy_ids: list[str] = field(default_factory=list)  # json:"firewallPolicyIds"
    exceptions: list[dict] = field(default_factory=list)  # json:"exceptions"
    username_to_siem: bool | None = None  # json:"usernameToSiem,omitempty" (*bool)


@dataclass
class UpdateSiemSettingsResponse:
    """Response from updating SIEM settings.

    Mirrors Go UpdateSiemSettingsResponse struct from siem_settings.go.
    """
    enable_for_all_policies: bool = False  # json:"enableForAllPolicies"
    enable_siem: bool = False  # json:"enableSiem"
    enabled_botman_siem_events: bool = False  # json:"enabledBotmanSiemEvents"
    include_ja4_fingerprint_to_siem: bool | None = None  # includeJA4FingerprintToSiem
    siem_definition_id: int = 0  # json:"siemDefinitionId"
    firewall_policy_ids: list[str] = field(default_factory=list)  # json:"firewallPolicyIds"
    exceptions: list[dict] = field(default_factory=list)  # json:"exceptions"
    username_to_siem: bool | None = None  # json:"usernameToSiem,omitempty" (*bool)


@dataclass
class RemoveSiemSettingsRequest:
    """Request for removing SIEM settings.

    Mirrors Go RemoveSiemSettingsRequest struct from siem_settings.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    enable_for_all_policies: bool = False  # json:"enableForAllPolicies"
    enable_siem: bool = False  # json:"enableSiem"
    enabled_botman_siem_events: bool = False  # json:"enabledBotmanSiemEvents"
    include_ja4_fingerprint_to_siem: bool | None = None  # includeJA4FingerprintToSiem,omitempty
    siem_definition_id: int = 0  # json:"siemDefinitionId"
    firewall_policy_ids: list[str] = field(default_factory=list)  # json:"firewallPolicyIds"


@dataclass
class RemoveSiemSettingsResponse:
    """Response from removing SIEM settings.

    Mirrors Go RemoveSiemSettingsResponse struct from siem_settings.go.
    """
    enable_for_all_policies: bool = False  # json:"enableForAllPolicies"
    enable_siem: bool = False  # json:"enableSiem"
    enabled_botman_siem_events: bool = False  # json:"enabledBotmanSiemEvents"
    include_ja4_fingerprint_to_siem: bool | None = None  # includeJA4FingerprintToSiem
    siem_definition_id: int = 0  # json:"siemDefinitionId"
    firewall_policy_ids: list[str] = field(default_factory=list)  # json:"firewallPolicyIds"


# =============================================================================
# Contracts Groups (from contracts_groups.go)
# =============================================================================


@dataclass
class GetContractsGroupsRequest:
    """Request for getting contracts and groups.

    Mirrors Go GetContractsGroupsRequest struct from contracts_groups.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    contract_id: str = ""  # json:"contractId"
    group_id: int = 0  # json:"groupId"


@dataclass
class GetContractsGroupsResponse:
    """Response from getting contracts and groups.

    Mirrors Go GetContractsGroupsResponse struct from contracts_groups.go.
    """
    contract_groups: list[dict] = field(default_factory=list)  # json:"contract_groups"


# =============================================================================
# Selectable Hostnames (from selectable_hostnames.go)
# =============================================================================


@dataclass
class GetSelectableHostnamesRequest:
    """Request for getting selectable hostnames.

    Mirrors Go GetSelectableHostnamesRequest struct from selectable_hostnames.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    contract_id: str = ""  # json:"-"
    group_id: int = 0  # json:"-"


@dataclass
class GetSelectableHostnamesResponse:
    """Response from getting selectable hostnames.

    Mirrors Go GetSelectableHostnamesResponse struct from selectable_hostnames.go.
    """
    available_set: list[dict] = field(default_factory=list)  # json:"availableSet"
    config_id: int = 0  # json:"configId"
    config_version: int = 0  # json:"configVersion"
    protect_arl_inclusion_host: bool = False  # json:"protectARLInclusionHost"


# =============================================================================
# Selected Hostname (from selected_hostname.go)
# =============================================================================


@dataclass
class Hostname:
    """Individual hostname.

    Mirrors Go Hostname struct from selected_hostname.go.
    """
    hostname: str = ""  # json:"hostname"


@dataclass
class GetSelectedHostnamesRequest:
    """Request for getting selected hostnames.

    Mirrors Go GetSelectedHostnamesRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    hostname_list: list[dict] = field(default_factory=list)  # json:"hostnameList"


@dataclass
class GetSelectedHostnamesResponse:
    """Response from getting selected hostnames.

    Mirrors Go GetSelectedHostnamesResponse struct.
    """
    hostname_list: list[dict] = field(default_factory=list)  # json:"hostnameList"


@dataclass
class GetSelectedHostnameRequest:
    """Request for getting selected hostname (singular, deprecated).

    Mirrors Go GetSelectedHostnameRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    hostname_list: list[dict] = field(default_factory=list)  # json:"hostnameList"


@dataclass
class GetSelectedHostnameResponse:
    """Response from getting selected hostname (singular, deprecated).

    Mirrors Go GetSelectedHostnameResponse struct.
    """
    hostname_list: list[dict] = field(default_factory=list)  # json:"hostnameList"


@dataclass
class UpdateSelectedHostnamesRequest:
    """Request for updating selected hostnames.

    Mirrors Go UpdateSelectedHostnamesRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    hostname_list: list[dict] = field(default_factory=list)  # json:"hostnameList"


@dataclass
class UpdateSelectedHostnamesResponse:
    """Response from updating selected hostnames.

    Mirrors Go UpdateSelectedHostnamesResponse struct.
    """
    hostname_list: list[dict] = field(default_factory=list)  # json:"hostnameList"


@dataclass
class UpdateSelectedHostnameRequest:
    """Request for updating selected hostname (singular, deprecated).

    Mirrors Go UpdateSelectedHostnameRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    hostname_list: list[dict] = field(default_factory=list)  # json:"hostnameList"


@dataclass
class UpdateSelectedHostnameResponse:
    """Response from updating selected hostname (singular, deprecated).

    Mirrors Go UpdateSelectedHostnameResponse struct.
    """
    hostname_list: list[dict] = field(default_factory=list)  # json:"hostnameList"


# =============================================================================
# WAP Selected Hostnames (from wap_selected_hostnames.go)
# =============================================================================


@dataclass
class GetWAPSelectedHostnamesRequest:
    """Request for getting WAP selected hostnames.

    Mirrors Go GetWAPSelectedHostnamesRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    security_policy_id: str = ""  # json:"-"


@dataclass
class GetWAPSelectedHostnamesResponse:
    """Response from getting WAP selected hostnames.

    Mirrors Go GetWAPSelectedHostnamesResponse struct.
    """
    protected_hosts: list[str] = field(default_factory=list)  # json:"protectedHostnames"
    evaluated_hosts: list[str] = field(default_factory=list)  # json:"evalHostnames"


@dataclass
class UpdateWAPSelectedHostnamesRequest:
    """Request for updating WAP selected hostnames.

    Mirrors Go UpdateWAPSelectedHostnamesRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    security_policy_id: str = ""  # json:"-"
    protected_hosts: list[str] = field(default_factory=list)  # json:"protectedHostnames"
    evaluated_hosts: list[str] = field(default_factory=list)  # json:"evalHostnames"


@dataclass
class UpdateWAPSelectedHostnamesResponse:
    """Response from updating WAP selected hostnames.

    Mirrors Go UpdateWAPSelectedHostnamesResponse struct.
    """
    protected_hosts: list[str] = field(default_factory=list)  # json:"protectedHostnames"
    evaluated_hosts: list[str] = field(default_factory=list)  # json:"evalHostnames"


# =============================================================================
# WAP Bypass Network Lists (from wap_bypass_network_lists.go)
# =============================================================================


@dataclass
class NetworkList:
    """Network list reference.

    Mirrors Go NetworkList struct from wap_bypass_network_lists.go.
    """
    name: str = ""  # json:"name"
    id: str = ""  # json:"id"


@dataclass
class GetWAPBypassNetworkListsRequest:
    """Request for getting WAP bypass network lists.

    Mirrors Go GetWAPBypassNetworkListsRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"


@dataclass
class IPNetworkListsList:
    """IP network lists container.

    Mirrors Go IPNetworkListsList struct from wap_bypass_network_lists.go.
    """
    network_list: list[str] = field(default_factory=list)  # json:"networkList"


@dataclass
class GeoControlsList:
    """Geo controls container.

    Mirrors Go GeoControlsList struct from wap_bypass_network_lists.go.
    """
    blocked_ip_network_lists: dict | None = None  # json:"blockedIPNetworkLists"


@dataclass
class IPControlsLists:
    """IP controls container.

    Mirrors Go IPControlsLists struct from wap_bypass_network_lists.go.
    """
    allowed_ip_network_lists: dict | None = None  # json:"allowedIPNetworkLists"
    blocked_ip_network_lists: dict | None = None  # json:"blockedIPNetworkLists"


@dataclass
class GetWAPBypassNetworkListsResponse:
    """Response from getting WAP bypass network lists.

    Mirrors Go GetWAPBypassNetworkListsResponse struct.
    """
    network_lists: list[dict] = field(default_factory=list)  # json:"networkLists"


@dataclass
class UpdateWAPBypassNetworkListsRequest:
    """Request for updating WAP bypass network lists.

    Mirrors Go UpdateWAPBypassNetworkListsRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    network_lists: list[dict] = field(default_factory=list)  # json:"networkLists"


@dataclass
class UpdateWAPBypassNetworkListsResponse:
    """Response from updating WAP bypass network lists.

    Mirrors Go UpdateWAPBypassNetworkListsResponse struct.
    """
    block: str = ""  # json:"block"
    geo_controls: dict | None = None  # json:"geoControls"
    ip_controls: dict | None = None  # json:"ipControls"


@dataclass
class RemoveWAPBypassNetworkListsRequest:
    """Request for removing WAP bypass network lists.

    Mirrors Go RemoveWAPBypassNetworkListsRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    network_lists: list[dict] = field(default_factory=list)  # json:"networkLists"


@dataclass
class RemoveWAPBypassNetworkListsResponse:
    """Response from removing WAP bypass network lists.

    Mirrors Go RemoveWAPBypassNetworkListsResponse struct.
    """
    network_lists: list[dict] = field(default_factory=list)  # json:"networkLists"


# =============================================================================
# Failover Hostnames (from failover_hostnames.go)
# =============================================================================


@dataclass
class GetFailoverHostnamesRequest:
    """Request for getting failover hostnames.

    Mirrors Go GetFailoverHostnamesRequest struct from failover_hostnames.go.
    """
    config_id: int = 0  # json:"-"


@dataclass
class GetFailoverHostnamesResponse:
    """Response from getting failover hostnames.

    Mirrors Go GetFailoverHostnamesResponse struct from failover_hostnames.go.
    """
    config_id: int = 0  # json:"configId"
    config_version: int = 0  # json:"configVersion"
    hostname_list: list[dict] = field(default_factory=list)  # json:"hostnameList"


# =============================================================================
# Host Move Activations (from host_move_activations.go)
# =============================================================================


@dataclass
class ConfigInfo:
    """Configuration info for host move.

    Mirrors Go ConfigInfo struct from host_move_activations.go.
    """
    config_id: int = 0  # json:"configId"
    config_name: str = ""  # json:"configName"
    config_version: int = 0  # json:"configVersion"
    invalid_hosts: list[str] = field(default_factory=list)  # json:"invalidHosts"


@dataclass
class HostToMove:
    """Host to move details.

    Mirrors Go HostToMove struct from host_move_activations.go.
    """
    allowed: bool = False  # json:"allowed"
    from_config: dict | None = None  # json:"fromConfig"
    host: str = ""  # json:"host"
    to_config: dict | None = None  # json:"toConfig"


@dataclass
class GetHostMoveValidationRequest:
    """Request for getting host move validation.

    Mirrors Go GetHostMoveValidationRequest struct.
    """
    config_id: int = 0  # json:"-"
    config_version: int = 0  # json:"-"
    network: str = ""  # json:"-"


@dataclass
class GetHostMoveValidationResponse:
    """Response from getting host move validation.

    Mirrors Go GetHostMoveValidationResponse struct.
    """
    hosts_to_move: list[dict] = field(default_factory=list)  # json:"hostsToMove"
    network: str = ""  # json:"network"


@dataclass
class AcknowledgedInvalidHostsByConfig:
    """Acknowledged invalid hosts by config.

    Mirrors Go AcknowledgedInvalidHostsByConfig struct.
    """
    config_id: int = 0  # json:"configId"
    invalid_hosts: list[str] = field(default_factory=list)  # json:"invalidHosts"


@dataclass
class ActivationConfig:
    """Activation config for host move.

    Mirrors Go ActivationConfig struct from host_move_activations.go.
    """
    config_id: int = 0  # json:"configId"
    config_name: str = ""  # json:"configName"
    config_version: int = 0  # json:"configVersion"


@dataclass
class CreateActivationsWithHostMoveRequest:
    """Request for creating activations with host move.

    Mirrors Go CreateActivationsWithHostMoveRequest struct.
    """
    config_id: int = 0  # json:"-"
    config_version: int = 0  # json:"-"
    action: str = ""  # json:"action"
    network: str = ""  # json:"network"
    note: str = ""  # json:"note"
    notification_emails: list[str] = field(default_factory=list)  # json:"notificationEmails"
    acknowledged_invalid_hosts: list[str] = field(default_factory=list)  # acknowledgedInvalidHosts
    acknowledged_invalid_hosts_by_config: list[dict] = field(default_factory=list)
    hosts_to_move: list[dict] = field(default_factory=list)  # json:"hostsToMove"
    support_id: str = ""  # json:"supportId"


@dataclass
class CreateActivationsWithHostMoveResponse:
    """Response from creating activations with host move.

    Mirrors Go CreateActivationsWithHostMoveResponse struct.
    """
    action: str = ""  # json:"action"
    activation_configs: list[dict] = field(default_factory=list)  # json:"activationConfigs"
    activation_id: int = 0  # json:"activationId"
    create_date: str = ""  # json:"createDate" (time.Time -> str)
    created_by: str = ""  # json:"createdBy"
    network: str = ""  # json:"network"
    status: str = ""  # json:"status"


# =============================================================================
# Version Notes (from version_notes.go)
# =============================================================================


@dataclass
class GetVersionNotesRequest:
    """Request for getting version notes.

    Mirrors Go GetVersionNotesRequest struct from version_notes.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"


@dataclass
class GetVersionNotesResponse:
    """Response from getting version notes.

    Mirrors Go GetVersionNotesResponse struct from version_notes.go.
    """
    notes: str = ""  # json:"notes"


@dataclass
class UpdateVersionNotesRequest:
    """Request for updating version notes.

    Mirrors Go UpdateVersionNotesRequest struct from version_notes.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    notes: str = ""  # json:"notes"


@dataclass
class UpdateVersionNotesResponse:
    """Response from updating version notes.

    Mirrors Go UpdateVersionNotesResponse struct from version_notes.go.
    """
    notes: str = ""  # json:"notes"


# =============================================================================
# Threat Intel (from threat_intel.go)
# =============================================================================


@dataclass
class GetThreatIntelRequest:
    """Request for getting threat intel settings.

    Mirrors Go GetThreatIntelRequest struct from threat_intel.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"


@dataclass
class GetThreatIntelResponse:
    """Response from getting threat intel settings.

    Mirrors Go GetThreatIntelResponse struct from threat_intel.go.
    """
    threat_intel: str = ""  # json:"threatIntel"


@dataclass
class UpdateThreatIntelRequest:
    """Request for updating threat intel settings.

    Mirrors Go UpdateThreatIntelRequest struct from threat_intel.go.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    threat_intel: str = ""  # json:"threatIntel"


@dataclass
class UpdateThreatIntelResponse:
    """Response from updating threat intel settings.

    Mirrors Go UpdateThreatIntelResponse struct from threat_intel.go.
    """
    threat_intel: str = ""  # json:"threatIntel"


# =============================================================================
# Tuning Recommendations (from tuning_recommendations.go)
# =============================================================================


@dataclass
class AttackGroupRecommendation:
    """Attack group tuning recommendation.

    Mirrors Go AttackGroupRecommendation struct from tuning_recommendations.go.
    """
    description: str = ""  # json:"description"
    evidence: list[dict] | None = None  # json:"evidences" (*Evidences)
    exception: dict | None = None  # json:"exception" (*AttackGroupException)
    group: str = ""  # json:"group"


@dataclass
class RuleRecommendation:
    """Rule tuning recommendation.

    Mirrors Go RuleRecommendation struct from tuning_recommendations.go.
    """
    description: str = ""  # json:"description"
    evidence: list[dict] | None = None  # json:"evidences" (*Evidences)
    exception: dict | None = None  # json:"exception" (*RuleException)
    rule_id: int = 0  # json:"ruleId"


@dataclass
class GetTuningRecommendationsRequest:
    """Request for getting tuning recommendations.

    Mirrors Go GetTuningRecommendationsRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    ruleset_type: str = ""  # json:"-"


@dataclass
class GetAttackGroupRecommendationsRequest:
    """Request for getting attack group recommendations.

    Mirrors Go GetAttackGroupRecommendationsRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    group: str = ""  # json:"-"
    ruleset_type: str = ""  # json:"-"


@dataclass
class GetRuleRecommendationsRequest:
    """Request for getting rule recommendations.

    Mirrors Go GetRuleRecommendationsRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    rule_id: int = 0  # json:"-"
    ruleset_type: str = ""  # json:"-"


@dataclass
class GetTuningRecommendationsResponse:
    """Response from getting tuning recommendations.

    Mirrors Go GetTuningRecommendationsResponse struct.
    """
    attack_group_recommendations: list[dict] = field(default_factory=list)
    rule_recommendations: list[dict] = field(default_factory=list)  # json:"ruleRecommendations"
    evaluation_period_start: str = ""  # json:"evaluationPeriodStart" (time.Time -> str)
    evaluation_period_end: str = ""  # json:"evaluationPeriodEnd" (time.Time -> str)


# GetAttackGroupRecommendationsResponse is an alias for AttackGroupRecommendation
GetAttackGroupRecommendationsResponse = AttackGroupRecommendation

# GetRuleRecommendationsResponse is an alias for RuleRecommendation
GetRuleRecommendationsResponse = RuleRecommendation


# =============================================================================
# Advanced Settings: ASE Penalty Box
# (from advanced_settings_ase_penalty_box.go)
# =============================================================================


@dataclass
class QualificationExclusions:
    """Qualification exclusions for ASE penalty box.

    Mirrors Go QualificationExclusions struct.
    """
    attack_groups: list[str] = field(default_factory=list)  # json:"attackGroups"
    rules: list[int] = field(default_factory=list)  # json:"rules"


@dataclass
class AkamaiManagedExclusions:
    """Akamai managed exclusions for ASE penalty box.

    Mirrors Go AkamaiManagedExclusions struct.
    """
    rules: list[int] = field(default_factory=list)  # json:"rules"
    last_updated: str = ""  # json:"lastUpdated"


@dataclass
class GetAdvancedSettingsAsePenaltyBoxRequest:
    """Request for getting ASE penalty box advanced settings.

    Mirrors Go GetAdvancedSettingsAsePenaltyBoxRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"


@dataclass
class GetAdvancedSettingsAsePenaltyBoxResponse:
    """Response from getting ASE penalty box advanced settings.

    Mirrors Go GetAdvancedSettingsAsePenaltyBoxResponse struct.
    """
    request_count: int = 0  # json:"requestCount"
    block_duration: int = 0  # json:"blockDuration"
    client_identifiers: list[str] = field(default_factory=list)  # json:"clientIdentifiers"
    akamai_managed_exclusions: dict | None = None  # json:"akamaiManagedExclusions"
    qualification_exclusions: dict | None = None  # json:"qualificationExclusions"


@dataclass
class UpdateAdvancedSettingsAsePenaltyBoxRequest:
    """Request for updating ASE penalty box advanced settings.

    Mirrors Go UpdateAdvancedSettingsAsePenaltyBoxRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    block_duration: int = 0  # json:"blockDuration"
    qualification_exclusions: dict | None = None  # json:"qualificationExclusions"


@dataclass
class UpdateAdvancedSettingsAsePenaltyBoxResponse:
    """Response from updating ASE penalty box advanced settings.

    Mirrors Go UpdateAdvancedSettingsAsePenaltyBoxResponse struct.
    """
    request_count: int = 0  # json:"requestCount"
    block_duration: int = 0  # json:"blockDuration"
    client_identifiers: list[str] = field(default_factory=list)  # json:"clientIdentifiers"
    akamai_managed_exclusions: dict | None = None  # json:"akamaiManagedExclusions"
    qualification_exclusions: dict | None = None  # json:"qualificationExclusions"


@dataclass
class RemoveAdvancedSettingsAsePenaltyBoxRequest:
    """Request for removing ASE penalty box advanced settings.

    Mirrors Go RemoveAdvancedSettingsAsePenaltyBoxRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"


@dataclass
class RemoveAdvancedSettingsAsePenaltyBoxResponse:
    """Response from removing ASE penalty box advanced settings.

    Mirrors Go RemoveAdvancedSettingsAsePenaltyBoxResponse struct.
    """
    request_count: int = 0  # json:"requestCount"
    block_duration: int = 0  # json:"blockDuration"
    client_identifiers: list[str] = field(default_factory=list)  # json:"clientIdentifiers"
    akamai_managed_exclusions: dict | None = None  # json:"akamaiManagedExclusions"
    qualification_exclusions: dict | None = None  # json:"qualificationExclusions"


# =============================================================================
# Advanced Settings: Attack Payload Logging
# (from advanced_settings_attack_payload_logging.go)
# =============================================================================


@dataclass
class AttackPayloadLoggingRequestBody:
    """Attack payload logging request body type.

    Mirrors Go AttackPayloadLoggingRequestBody struct.
    """
    type: str = ""  # json:"type" (AttackPayloadType)


@dataclass
class AttackPayloadLoggingResponseBody:
    """Attack payload logging response body type.

    Mirrors Go AttackPayloadLoggingResponseBody struct.
    """
    type: str = ""  # json:"type" (AttackPayloadType)


@dataclass
class GetAdvancedSettingsAttackPayloadLoggingRequest:
    """Request for getting attack payload logging.

    Mirrors Go GetAdvancedSettingsAttackPayloadLoggingRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"


@dataclass
class GetAdvancedSettingsAttackPayloadLoggingResponse:
    """Response from getting attack payload logging.

    Mirrors Go GetAdvancedSettingsAttackPayloadLoggingResponse struct.
    """
    override: bool = False  # json:"override"
    enabled: bool = False  # json:"enabled"
    request_body: dict | None = None  # json:"requestBody"
    response_body: dict | None = None  # json:"responseBody"


@dataclass
class UpdateAdvancedSettingsAttackPayloadLoggingRequest:
    """Request for updating attack payload logging.

    Mirrors Go UpdateAdvancedSettingsAttackPayloadLoggingRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    json_payload_raw: Any = None  # json:"-" (json.RawMessage)


@dataclass
class UpdateAdvancedSettingsAttackPayloadLoggingResponse:
    """Response from updating attack payload logging.

    Mirrors Go UpdateAdvancedSettingsAttackPayloadLoggingResponse struct.
    """
    override: bool = False  # json:"override"
    enabled: bool = False  # json:"enabled"
    request_body: dict | None = None  # json:"requestBody"
    response_body: dict | None = None  # json:"responseBody"


@dataclass
class RemoveAdvancedSettingsAttackPayloadLoggingRequest:
    """Request for removing attack payload logging.

    Mirrors Go RemoveAdvancedSettingsAttackPayloadLoggingRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    override: bool = False  # json:"override"
    enabled: bool = False  # json:"enabled"
    request_body: dict | None = None  # json:"requestBody"
    response_body: dict | None = None  # json:"responseBody"


@dataclass
class RemoveAdvancedSettingsAttackPayloadLoggingResponse:
    """Response from removing attack payload logging.

    Mirrors Go RemoveAdvancedSettingsAttackPayloadLoggingResponse struct.
    """
    override: bool = False  # json:"override"
    enabled: bool = False  # json:"enabled"
    request_body: dict | None = None  # json:"requestBody"
    response_body: dict | None = None  # json:"responseBody"


# =============================================================================
# Advanced Settings: Evasive Path Match
# (from advanced_settings_evasive_path_match.go)
# =============================================================================


@dataclass
class GetAdvancedSettingsEvasivePathMatchRequest:
    """Request for getting evasive path match settings.

    Mirrors Go GetAdvancedSettingsEvasivePathMatchRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"


@dataclass
class GetAdvancedSettingsEvasivePathMatchResponse:
    """Response from getting evasive path match settings.

    Mirrors Go GetAdvancedSettingsEvasivePathMatchResponse struct.
    """
    enable_path_match: bool = False  # json:"enablePathMatch"


@dataclass
class UpdateAdvancedSettingsEvasivePathMatchRequest:
    """Request for updating evasive path match settings.

    Mirrors Go UpdateAdvancedSettingsEvasivePathMatchRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    enable_path_match: bool = False  # json:"enablePathMatch"


@dataclass
class UpdateAdvancedSettingsEvasivePathMatchResponse:
    """Response from updating evasive path match settings.

    Mirrors Go UpdateAdvancedSettingsEvasivePathMatchResponse struct.
    """
    enable_path_match: bool = False  # json:"enablePathMatch"


@dataclass
class RemoveAdvancedSettingsEvasivePathMatchRequest:
    """Request for removing evasive path match settings.

    Mirrors Go RemoveAdvancedSettingsEvasivePathMatchRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    enable_path_match: bool = False  # json:"enablePathMatch"


@dataclass
class RemoveAdvancedSettingsEvasivePathMatchResponse:
    """Response from removing evasive path match settings.

    Mirrors Go RemoveAdvancedSettingsEvasivePathMatchResponse struct.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    policy_id: str = ""  # json:"policyId"
    enable_path_match: bool = False  # json:"enablePathMatch"


# =============================================================================
# Advanced Settings: JA4 Fingerprints
# (from advanced_settings_ja4_fingerprints.go)
# =============================================================================


@dataclass
class GetAdvancedSettingsJA4FingerprintRequest:
    """Request for getting JA4 fingerprint settings.

    Mirrors Go GetAdvancedSettingsJA4FingerprintRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"


@dataclass
class GetAdvancedSettingsJA4FingerprintResponse:
    """Response from getting JA4 fingerprint settings.

    Mirrors Go GetAdvancedSettingsJA4FingerprintResponse struct.
    """
    header_names: list[str] = field(default_factory=list)  # json:"headerNames"


@dataclass
class UpdateAdvancedSettingsJA4FingerprintRequest:
    """Request for updating JA4 fingerprint settings.

    Mirrors Go UpdateAdvancedSettingsJA4FingerprintRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    header_names: list[str] = field(default_factory=list)  # json:"headerNames,omitempty"


@dataclass
class UpdateAdvancedSettingsJA4FingerprintResponse:
    """Response from updating JA4 fingerprint settings.

    Mirrors Go UpdateAdvancedSettingsJA4FingerprintResponse struct.
    """
    header_names: list[str] = field(default_factory=list)  # json:"headerNames"


@dataclass
class RemoveAdvancedSettingsJA4FingerprintRequest:
    """Request for removing JA4 fingerprint settings.

    Mirrors Go RemoveAdvancedSettingsJA4FingerprintRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"


@dataclass
class RemoveAdvancedSettingsJA4FingerprintResponse:
    """Response from removing JA4 fingerprint settings.

    Mirrors Go RemoveAdvancedSettingsJA4FingerprintResponse struct.
    """
    header_names: list[str] = field(default_factory=list)  # json:"headerNames"


# =============================================================================
# Advanced Settings: Logging
# (from advanced_settings_logging.go)
# =============================================================================


@dataclass
class AdvancedSettingsCookies:
    """Cookie logging settings.

    Mirrors Go AdvancedSettingsCookies struct.
    """
    type: str = ""  # json:"type"
    values: list[str] = field(default_factory=list)  # json:"values,omitempty"


@dataclass
class AdvancedSettingsCustomHeaders:
    """Custom header logging settings.

    Mirrors Go AdvancedSettingsCustomHeaders struct.
    """
    type: str = ""  # json:"type"
    values: list[str] = field(default_factory=list)  # json:"values,omitempty"


@dataclass
class AdvancedSettingsStandardHeaders:
    """Standard header logging settings.

    Mirrors Go AdvancedSettingsStandardHeaders struct.
    """
    type: str = ""  # json:"type"
    values: list[str] = field(default_factory=list)  # json:"values,omitempty"


@dataclass
class GetAdvancedSettingsLoggingRequest:
    """Request for getting logging settings.

    Mirrors Go GetAdvancedSettingsLoggingRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"


@dataclass
class GetAdvancedSettingsLoggingResponse:
    """Response from getting logging settings.

    Mirrors Go GetAdvancedSettingsLoggingResponse struct.
    """
    override: Any = None  # json:"override" (json.RawMessage)
    allow_sampling: bool = False  # json:"allowSampling"
    cookies: dict | None = None  # json:"cookies"
    custom_headers: dict | None = None  # json:"customHeaders"
    standard_headers: dict | None = None  # json:"standardHeaders"


@dataclass
class UpdateAdvancedSettingsLoggingRequest:
    """Request for updating logging settings.

    Mirrors Go UpdateAdvancedSettingsLoggingRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    json_payload_raw: Any = None  # json:"-" (json.RawMessage)


@dataclass
class UpdateAdvancedSettingsLoggingResponse:
    """Response from updating logging settings.

    Mirrors Go UpdateAdvancedSettingsLoggingResponse struct.
    """
    override: Any = None  # json:"override"
    allow_sampling: bool = False  # json:"allowSampling"
    cookies: dict | None = None  # json:"cookies"
    custom_headers: dict | None = None  # json:"customHeaders"
    standard_headers: dict | None = None  # json:"standardHeaders"


@dataclass
class RemoveAdvancedSettingsLoggingRequest:
    """Request for removing logging settings.

    Mirrors Go RemoveAdvancedSettingsLoggingRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    override: bool = False  # json:"override"
    allow_sampling: bool = False  # json:"allowSampling"


@dataclass
class RemoveAdvancedSettingsLoggingResponse:
    """Response from removing logging settings.

    Mirrors Go RemoveAdvancedSettingsLoggingResponse struct.
    """
    override: Any = None  # json:"override"
    allow_sampling: bool = False  # json:"allowSampling"
    cookies: dict | None = None  # json:"cookies"
    custom_headers: dict | None = None  # json:"customHeaders"
    standard_headers: dict | None = None  # json:"standardHeaders"


# =============================================================================
# Advanced Settings: PII Learning
# (from advanced_settings_pii_learning.go)
# =============================================================================


@dataclass
class GetAdvancedSettingsPIILearningRequest:
    """Request for getting PII learning settings.

    Mirrors Go GetAdvancedSettingsPIILearningRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"


@dataclass
class UpdateAdvancedSettingsPIILearningRequest:
    """Request for updating PII learning settings.

    Mirrors Go UpdateAdvancedSettingsPIILearningRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    enable_pii_learning: bool = False  # json:"enablePiiLearning"


@dataclass
class AdvancedSettingsPIILearningResponse:
    """Response for PII learning settings.

    Mirrors Go AdvancedSettingsPIILearningResponse struct.
    """
    enable_pii_learning: bool = False  # json:"enablePiiLearning"


# =============================================================================
# Advanced Settings: Pragma Header
# (from advanced_settings_pragma_header.go)
# =============================================================================


@dataclass
class ExcludeCondition:
    """Exclude condition for pragma header settings.

    Mirrors Go ExcludeCondition struct.
    """
    type: str = ""  # json:"type,omitempty"
    positive_match: bool = False  # json:"positiveMatch"
    header: str = ""  # json:"header,omitempty"
    value: list[str] = field(default_factory=list)  # json:"value,omitempty"
    name: list[str] = field(default_factory=list)  # json:"name,omitempty"
    value_case: bool = False  # json:"valueCase"
    value_wildcard: bool = False  # json:"valueWildcard"
    use_headers: bool = False  # json:"useHeaders"


@dataclass
class GetAdvancedSettingsPragmaRequest:
    """Request for getting pragma header settings.

    Mirrors Go GetAdvancedSettingsPragmaRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    group: str = ""  # json:"-"


@dataclass
class GetAdvancedSettingsPragmaResponse:
    """Response from getting pragma header settings.

    Mirrors Go GetAdvancedSettingsPragmaResponse struct.
    """
    action: str = ""  # json:"action"
    condition_operator: str = ""  # json:"conditionOperator"
    exclude_condition: list[dict] = field(default_factory=list)  # json:"excludeCondition"


@dataclass
class UpdateAdvancedSettingsPragmaRequest:
    """Request for updating pragma header settings.

    Mirrors Go UpdateAdvancedSettingsPragmaRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    json_payload_raw: Any = None  # json:"-" (json.RawMessage)


@dataclass
class UpdateAdvancedSettingsPragmaResponse:
    """Response from updating pragma header settings.

    Mirrors Go UpdateAdvancedSettingsPragmaResponse struct.
    """
    action: str = ""  # json:"action"
    condition_operator: str = ""  # json:"conditionOperator"
    exclude_condition: list[dict] = field(default_factory=list)  # json:"excludeCondition"


# =============================================================================
# Advanced Settings: Prefetch
# (from advanced_settings_prefetch.go)
# =============================================================================


@dataclass
class GetAdvancedSettingsPrefetchRequest:
    """Request for getting prefetch settings.

    Mirrors Go GetAdvancedSettingsPrefetchRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    group: str = ""  # json:"-"


@dataclass
class GetAdvancedSettingsPrefetchResponse:
    """Response from getting prefetch settings.

    Mirrors Go GetAdvancedSettingsPrefetchResponse struct.
    """
    all_extensions: bool = False  # json:"allExtensions"
    enable_app_layer: bool = False  # json:"enableAppLayer"
    enable_rate_controls: bool = False  # json:"enableRateControls"
    extensions: list[str] = field(default_factory=list)  # json:"extensions"


@dataclass
class UpdateAdvancedSettingsPrefetchRequest:
    """Request for updating prefetch settings.

    Mirrors Go UpdateAdvancedSettingsPrefetchRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    all_extensions: bool = False  # json:"allExtensions"
    enable_app_layer: bool = False  # json:"enableAppLayer"
    enable_rate_controls: bool = False  # json:"enableRateControls"
    extensions: list[str] = field(default_factory=list)  # json:"extensions"


@dataclass
class UpdateAdvancedSettingsPrefetchResponse:
    """Response from updating prefetch settings.

    Mirrors Go UpdateAdvancedSettingsPrefetchResponse struct.
    """
    all_extensions: bool = False  # json:"allExtensions"
    enable_app_layer: bool = False  # json:"enableAppLayer"
    enable_rate_controls: bool = False  # json:"enableRateControls"
    extensions: list[str] = field(default_factory=list)  # json:"extensions"


@dataclass
class RemoveAdvancedSettingsPrefetchRequest:
    """Request for removing prefetch settings.

    Mirrors Go RemoveAdvancedSettingsPrefetchRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    action: str = ""  # json:"action"


@dataclass
class RemoveAdvancedSettingsPrefetchResponse:
    """Response from removing prefetch settings.

    Mirrors Go RemoveAdvancedSettingsPrefetchResponse struct.
    """
    action: str = ""  # json:"action"


# =============================================================================
# Advanced Settings: Request Body
# (from advanced_settings_request_body.go)
# =============================================================================


@dataclass
class GetAdvancedSettingsRequestBodyRequest:
    """Request for getting request body settings.

    Mirrors Go GetAdvancedSettingsRequestBodyRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"


@dataclass
class GetAdvancedSettingsRequestBodyResponse:
    """Response from getting request body settings.

    Mirrors Go GetAdvancedSettingsRequestBodyResponse struct.
    """
    request_body_inspection_limit_in_kb: str = ""  # json:"requestBodyInspectionLimitInKB"
    request_body_inspection_limit_override: bool = False  # json:"override"


@dataclass
class UpdateAdvancedSettingsRequestBodyRequest:
    """Request for updating request body settings.

    Mirrors Go UpdateAdvancedSettingsRequestBodyRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    request_body_inspection_limit_in_kb: str = ""  # json:"requestBodyInspectionLimitInKB"
    request_body_inspection_limit_override: bool = False  # json:"override"


@dataclass
class UpdateAdvancedSettingsRequestBodyResponse:
    """Response from updating request body settings.

    Mirrors Go UpdateAdvancedSettingsRequestBodyResponse struct.
    """
    request_body_inspection_limit_in_kb: str = ""  # json:"requestBodyInspectionLimitInKB"
    request_body_inspection_limit_override: bool = False  # json:"override"


@dataclass
class RemoveAdvancedSettingsRequestBodyRequest:
    """Request for removing request body settings.

    Mirrors Go RemoveAdvancedSettingsRequestBodyRequest struct.
    """
    config_id: int = 0  # json:"-"
    version: int = 0  # json:"-"
    policy_id: str = ""  # json:"-"
    request_body_inspection_limit_in_kb: str = ""  # json:"requestBodyInspectionLimitInKB"
    request_body_inspection_limit_override: bool = False  # json:"override"


@dataclass
class RemoveAdvancedSettingsRequestBodyResponse:
    """Response from removing request body settings.

    Mirrors Go RemoveAdvancedSettingsRequestBodyResponse struct.
    """
    request_body_inspection_limit_in_kb: str = ""  # json:"requestBodyInspectionLimitInKB"
    request_body_inspection_limit_override: bool = False  # json:"override"


# =============================================================================
# Export Configuration
# (from export_configuration.go - LARGEST section with many helper types)
# =============================================================================


@dataclass
class GetExportConfigurationRequest:
    """Request for getting export configuration.

    Mirrors Go GetExportConfigurationRequest struct.
    """
    config_id: int = 0  # json:"configId"
    version: int = 0  # json:"version"
    source: str = ""  # json:"source,omitempty"


@dataclass
class EvaluatingSecurityPolicy:
    """Evaluating security policy returned from export configuration.

    Mirrors Go EvaluatingSecurityPolicy struct.
    """
    effective_security_controls: dict | None = None  # json:"effectiveSecurityControls"
    hostnames: list[str] = field(default_factory=list)  # json:"hostnames,omitempty"
    security_policy_id: str = ""  # json:"id"


@dataclass
class GetExportConfigurationResponse:
    """Response from getting export configuration.

    Mirrors Go GetExportConfigurationResponse struct.
    This is the most complex response struct in the AppSec package.
    Many fields use inline anonymous Go structs, represented as
    dict or list[dict] in Python.
    """
    config_id: int = 0  # json:"configId"
    config_name: str = ""  # json:"configName"
    version: int = 0  # json:"version"
    based_on: int = 0  # json:"basedOn"
    staging: dict | None = None  # json:"staging" (anonymous struct with status)
    production: dict | None = None  # json:"production" (anonymous struct with status)
    target_product: str = ""  # json:"targetProduct"
    create_date: str = ""  # json:"-" (time.Time)
    created_by: str = ""  # json:"createdBy"
    selected_hosts: list[str] = field(default_factory=list)  # json:"selectedHosts"
    selectable_hosts: list[str] = field(default_factory=list)  # json:"selectableHosts"
    rate_policies: list[dict] = field(default_factory=list)  # json:"ratePolicies"
    reputation_profiles: list[dict] = field(default_factory=list)  # json:"reputationProfiles"
    custom_rules: list[dict] = field(default_factory=list)  # json:"customRules"
    rulesets: list[dict] = field(default_factory=list)  # json:"rulesets"
    match_targets: dict | None = None  # json:"matchTargets"
    security_policies: list[dict] = field(default_factory=list)  # json:"securityPolicies"
    siem: dict | None = None  # json:"siem,omitempty"
    advanced_options: dict | None = None  # json:"advancedOptions,omitempty"
    custom_deny_list: list[dict] | None = None  # json:"customDenyList,omitempty"
    evaluating: dict | None = None  # json:"evaluating,omitempty"
    malware_policies: list[dict] = field(default_factory=list)  # json:"malwarePolicies,omitempty"
    custom_bot_categories: list[dict] = field(default_factory=list)  # customBotCategories,omitempty
    custom_defined_bots: list[dict] = field(default_factory=list)  # customDefinedBots,omitempty
    custom_bot_category_sequence: list[str] = field(default_factory=list)
    custom_clients: list[dict] = field(default_factory=list)  # json:"customClients,omitempty"
    custom_client_sequence: list[str] = field(default_factory=list)
    response_actions: dict | None = None  # json:"responseActions,omitempty"
    advanced_settings: dict | None = None  # json:"advancedSettings,omitempty"
    evaluating_security_policy: list[dict] = field(default_factory=list)  # internal helper


# --- Export Configuration Helper Types ---


@dataclass
class RatePoliciesPath:
    """Rate policies path for export configuration.

    Mirrors Go RatePoliciesPath struct.
    """
    positive_match: bool = False  # json:"positiveMatch"
    values: list[str] | None = None  # json:"values,omitempty" (*RatePoliciesPathValues)


@dataclass
class SlowRateThresholdExp:
    """Slow rate threshold for export configuration.

    Mirrors Go SlowRateThresholdExp struct.
    """
    period: int = 0  # json:"period"
    rate: int = 0  # json:"rate"


@dataclass
class DurationThresholdExp:
    """Duration threshold for export configuration.

    Mirrors Go DurationThresholdExp struct.
    """
    timeout: int = 0  # json:"timeout"


@dataclass
class SlowPostexp:
    """Slow post settings for export configuration.

    Mirrors Go SlowPostexp struct.
    """
    action: str = ""  # json:"action"
    slow_rate_threshold: dict | None = None  # json:"slowRateThreshold,omitempty"
    duration_threshold: dict | None = None  # json:"durationThreshold,omitempty"


@dataclass
class AdvancedOptionsexp:
    """Advanced options for export configuration.

    Mirrors Go AdvancedOptionsexp struct.
    """
    logging: dict | None = None  # json:"logging"
    attack_payload_logging: dict | None = None  # json:"attackPayloadLogging"
    evasive_path_match: dict | None = None  # json:"evasivePathMatch,omitempty"
    ja4_fingerprint: dict | None = None  # json:"ja4Fingerprint,omitempty"
    prefetch: dict | None = None  # json:"prefetch"
    pragma_header: dict | None = None  # json:"pragmaHeader,omitempty"
    ase_penalty_box: dict | None = None  # json:"asePenaltyBox,omitempty"
    request_body: dict | None = None  # json:"requestBody,omitempty"
    pii_learning: dict | None = None  # json:"piiLearning,omitempty"


@dataclass
class Siemexp:
    """SIEM settings for export configuration.

    Mirrors Go Siemexp struct.
    """
    enable_for_all_policies: bool = False  # json:"enableForAllPolicies,omitempty"
    enable_siem: bool = False  # json:"enableSiem"
    enabled_botman_siem_events: bool = False  # json:"enabledBotmanSiemEvents,omitempty"
    include_ja4_fingerprint_to_siem: bool | None = None  # includeJA4FingerprintToSiem,omitempty
    firewall_policy_ids: list[str] = field(default_factory=list)  # firewallPolicyIds,omitempty
    siem_definition_id: int = 0  # json:"siemDefinitionId,omitempty"


@dataclass
class PenaltyBoxexp:
    """Penalty box settings for export configuration.

    Mirrors Go PenaltyBoxexp struct.
    """
    action: str = ""  # json:"action"
    penalty_box_protection: bool = False  # json:"penaltyBoxProtection"


@dataclass
class APIRequestConstraintsexp:
    """API request constraints for export configuration.

    Mirrors Go APIRequestConstraintsexp struct.
    """
    action: str = ""  # json:"action,omitempty"
    api_endpoints: list[dict] = field(default_factory=list)  # json:"apiEndpoints,omitempty"


@dataclass
class Evaluationexp:
    """Evaluation settings for export configuration.

    Mirrors Go Evaluationexp struct.
    """
    attack_group_actions: list[dict] = field(default_factory=list)  # json:"attackGroupActions"
    evaluation_id: int = 0  # json:"evaluationId"
    evaluation_version: int = 0  # json:"evaluationVersion"
    rule_actions: list[dict] = field(default_factory=list)  # json:"ruleActions"
    ruleset_version_id: int = 0  # json:"rulesetVersionId"


@dataclass
class ConditionReputationProfile:
    """Condition for reputation profile in export configuration.

    Mirrors Go ConditionReputationProfile struct.
    """
    atomic_conditions: list[dict] | None = None  # json:"atomicConditions,omitempty"
    can_delete: bool = False  # json:"-"
    config_version_id: int = 0  # json:"-"
    id: int = 0  # json:"-"
    name: str = ""  # json:"-"
    positive_match: Any = None  # json:"positiveMatch,omitempty" (json.RawMessage)
    uuid: str = ""  # json:"-"
    version: int = 0  # json:"-"


@dataclass
class SpecificHeaderCookieOrParamNameValueexp:
    """Specific header, cookie, or param name value for export.

    Mirrors Go SpecificHeaderCookieOrParamNameValueexp struct.
    """
    name: Any = None  # json:"name,omitempty" (json.RawMessage)
    selector: str = ""  # json:"selector,omitempty"
    value: Any = None  # json:"value,omitempty" (json.RawMessage)


@dataclass
class Loggingexp:
    """Logging settings for export configuration.

    Mirrors Go Loggingexp struct.
    """
    allow_sampling: bool = False  # json:"allowSampling"
    cookies: dict | None = None  # json:"cookies" (anonymous struct)
    custom_headers: dict | None = None  # json:"customHeaders" (anonymous struct)
    standard_headers: dict | None = None  # json:"standardHeaders" (anonymous struct)


@dataclass
class LoggingOverridesexp:
    """Logging overrides for export configuration.

    Mirrors Go LoggingOverridesexp struct.
    """
    allow_sampling: bool = False  # json:"allowSampling"
    cookies: dict | None = None  # json:"cookies" (anonymous struct)
    custom_headers: dict | None = None  # json:"customHeaders" (anonymous struct)
    override: bool = False  # json:"override"
    standard_headers: dict | None = None  # json:"standardHeaders" (anonymous struct)


@dataclass
class AttackPayloadLoggingExp:
    """Attack payload logging for export configuration.

    Mirrors Go AttackPayloadLogging struct (note: exported name AttackPayloadLoggingExp).
    """
    enabled: bool = False  # json:"enabled"
    request_body: dict | None = None  # json:"requestBody" (anonymous struct)
    response_body: dict | None = None  # json:"responseBody" (anonymous struct)


@dataclass
class AttackPayloadLoggingOverrides:
    """Attack payload logging overrides for export configuration.

    Mirrors Go AttackPayloadLoggingOverrides struct.
    """
    enabled: bool = False  # json:"enabled"
    request_body: dict | None = None  # json:"requestBody" (anonymous struct)
    response_body: dict | None = None  # json:"responseBody" (anonymous struct)
    override: bool = False  # json:"override"


@dataclass
class EvasivePathMatchexp:
    """Evasive path match for export configuration.

    Mirrors Go EvasivePathMatchexp struct.
    """
    enable_path_match: bool = False  # json:"enabled"


@dataclass
class JA4Fingerprintexp:
    """JA4 fingerprint for export configuration.

    Mirrors Go JA4Fingerprintexp struct.
    """
    header_names: list[str] = field(default_factory=list)  # json:"headerNames,omitempty"


@dataclass
class AsePenaltyBoxexp:
    """ASE penalty box for export configuration.

    Mirrors Go AsePenaltyBoxexp struct.
    """
    request_count: int = 0  # json:"requestCount"
    block_duration: int = 0  # json:"blockDuration"
    client_identifiers: list[str] = field(default_factory=list)  # json:"clientIdentifiers"
    akamai_managed_exclusions: dict | None = None  # json:"akamaiManagedExclusions" (anonymous)
    qualification_exclusions: dict | None = None  # json:"qualificationExclusions" (anonymous)


@dataclass
class PIILearningexp:
    """PII learning for export configuration.

    Mirrors Go PIILearningexp struct.
    """
    enable_pii_learning: bool = False  # json:"enabled"


@dataclass
class PrefetchExp:
    """Prefetch settings for export configuration.

    Mirrors Go Prefetch struct (note: exported name PrefetchExp).
    """
    all_extensions: bool = False  # json:"allExtensions"
    enable_app_layer: bool = False  # json:"enableAppLayer"
    enable_rate_controls: bool = False  # json:"enableRateControls"
    extensions: list[str] = field(default_factory=list)  # json:"extensions,omitempty"


@dataclass
class RequestBodyExp:
    """Request body settings for export configuration.

    Mirrors Go RequestBody struct (note: exported name RequestBodyExp).
    """
    request_body_inspection_limit_in_kb: str = ""  # json:"requestBodyInspectionLimitInKB"
    request_body_inspection_limit_override: bool = False  # json:"override"


@dataclass
class SecurityPoliciesPenaltyBox:
    """Security policies penalty box for export configuration.

    Mirrors Go SecurityPoliciesPenaltyBox struct.
    """
    action: str = ""  # json:"action,omitempty"
    penalty_box_protection: bool = False  # json:"penaltyBoxProtection,omitempty"


@dataclass
class SecurityPoliciesPenaltyBoxConditions:
    """Security policies penalty box conditions for export configuration.

    Mirrors Go SecurityPoliciesPenaltyBoxConditions struct.
    """
    condition_operator: str = ""  # json:"conditionOperator,omitempty"
    conditions: Any = None  # json:"conditions,omitempty" (*RuleConditions)


@dataclass
class WebApplicationFirewallEvaluation:
    """WAF evaluation for export configuration.

    Mirrors Go WebApplicationFirewallEvaluation struct.
    """
    attack_group_actions: list[dict] = field(default_factory=list)  # attackGroupActions,omitempty
    evaluation_id: int = 0  # json:"evaluationId"
    evaluation_version: int = 0  # json:"evaluationVersion"
    rule_actions: list[dict] = field(default_factory=list)  # json:"ruleActions,omitempty"
    ruleset_version_id: int = 0  # json:"rulesetVersionId"


@dataclass
class AdvancedSettingsExp:
    """Advanced settings for export configuration.

    Mirrors Go AdvancedSettings struct (note: exported name AdvancedSettingsExp).
    """
    bot_analytics_cookie_settings: dict | None = None  # json:"botAnalyticsCookieSettings,omitempty"
    client_side_security_settings: dict | None = None  # json:"clientSideSecuritySettings,omitempty"
    transactional_endpoint_protection_settings: dict | None = None
    user_risk_response_strategy_settings: dict | None = None
    user_allow_list_id_settings: dict | None = None  # json:"userAllowListIdSettings,omitempty"


@dataclass
class ResponseActions:
    """Response actions for export configuration.

    Mirrors Go ResponseActions struct.
    """
    challenge_actions: list[dict] = field(default_factory=list)  # json:"challengeActions,omitempty"
    conditional_actions: list[dict] = field(default_factory=list)  # conditionalActions,omitempty
    custom_deny_actions: list[dict] = field(default_factory=list)  # customDenyActions,omitempty
    serve_alternate_actions: list[dict] = field(default_factory=list)
    challenge_interception_rules: dict | None = None  # json:"challengeInterceptionRules,omitempty"
    challenge_injection_rules: dict | None = None  # json:"challengeInjectionRules,omitempty"


@dataclass
class BotManagement:
    """Bot management for export configuration.

    Mirrors Go BotManagement struct.
    """
    akamai_bot_category_actions: list[dict] = field(default_factory=list)
    bot_detection_actions: list[dict] = field(default_factory=list)  # botDetectionActions,omitempty
    bot_management_settings: dict | None = None  # json:"botManagementSettings,omitempty"
    custom_bot_category_actions: list[dict] = field(default_factory=list)
    javascript_injection_rules: dict | None = None  # json:"javascriptInjectionRules,omitempty"
    transactional_endpoints: dict | None = None  # json:"transactionalEndpoints,omitempty"
    content_protection_rules: list[dict] = field(default_factory=list)
    content_protection_rule_sequence: list[str] = field(default_factory=list)
    content_protection_java_script_injection_rules: list[dict] = field(default_factory=list)


@dataclass
class AccountProtectionExp:
    """Account protection for export configuration.

    Mirrors Go AccountProtection struct (note: exported name AccountProtectionExp).
    """
    general_settings: dict | None = None  # json:"generalSettings,omitempty"
    transactional_endpoints: list[dict] = field(default_factory=list)


@dataclass
class TransactionalEndpoints:
    """Transactional endpoints for export configuration.

    Mirrors Go TransactionalEndpoints struct.
    """
    bot_protection: list[dict] = field(default_factory=list)  # json:"botProtection,omitempty"
    bot_protection_exceptions: dict | None = None  # json:"botProtectionExceptions,omitempty"


# =============================================================================
# Export Configuration Type Aliases
# (from export_configuration.go - typed list/slice aliases)
# =============================================================================

# ReputationProfileActionsexp is a list of action/id dicts
ReputationProfileActionsexp = list[dict]

# RatePolicyActionsexp is a list of id/ipv4/ipv6 action dicts
RatePolicyActionsexp = list[dict]

# CustomDenyListexp is a list of custom deny entry dicts
CustomDenyListexp = list[dict]

# CustomRuleActionsexp is a list of action/id dicts
CustomRuleActionsexp = list[dict]

# HeaderCookieOrParamValuesattackgroup is a list of criteria/values dicts
HeaderCookieOrParamValuesattackgroup = list[dict]

# AtomicConditionsexp is a list of condition dicts
AtomicConditionsexp = list[dict]

# ConditionsExp is a list of condition dicts with type/match fields
ConditionsExp = list[dict]

# RulesetsRules is a list of rule definition dicts
RulesetsRules = list[dict]

# ClientReputationReputationProfileActions is a list of action/id dicts
ClientReputationReputationProfileActions = list[dict]

# SecurityPoliciesRatePolicyActions is a list of id/ipv4/ipv6 action dicts
SecurityPoliciesRatePolicyActions = list[dict]

# RatePoliciesQueryParameters is a list of query parameter dicts
RatePoliciesQueryParameters = list[dict]

# RatePoliciesPathValues is a list of strings
RatePoliciesPathValues = list[str]

# RatePoliciesQueryParametersValues is a list of strings
RatePoliciesQueryParametersValues = list[str]
