"""Request/response model classes for the API Definitions API."""
# pylint: disable=too-many-instance-attributes,too-many-lines

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ===================================================================
# Constants — Activation Network and Status (activations.go:85-102)
# ===================================================================

# NetworkType constants
ACTIVATION_NETWORK_STAGING: str = "STAGING"
ACTIVATION_NETWORK_PRODUCTION: str = "PRODUCTION"

# ActivationStatus constants
ACTIVATION_STATUS_PENDING: str = "PENDING"
ACTIVATION_STATUS_ACTIVE: str = "ACTIVE"
ACTIVATION_STATUS_DEACTIVATED: str = "DEACTIVATED"
ACTIVATION_STATUS_FAILED: str = "FAILED"

# Severity constants
SEVERITY_ERROR: str = "ERROR"
SEVERITY_WARNING: str = "WARNING"


# ===================================================================
# Constants — Endpoint Version Sort and Visibility
#     (endpoint_versions.go:172-199)
# ===================================================================

# ListEndpointVersionSortType constants
DESCRIPTION_SORT: str = "description"
VERSION_NUMBER_SORT: str = "versionNumber"
UPDATE_DATE_SORT: str = "updateDate"
UPDATED_BY_SORT: str = "updatedBy"
BASED_ON_SORT: str = "basedOn"
STAGING_STATUS_SORT: str = "stagingStatus"
PRODUCTION_STATUS_SORT: str = "productionStatus"

# SortOrderType constants
ASC_SORT_ORDER: str = "asc"
DESC_SORT_ORDER: str = "desc"

# Visibility constants
ALL_VISIBILITY: str = "ALL"
ONLY_HIDDEN_VISIBILITY: str = "ONLY_HIDDEN"
ONLY_VISIBLE_VISIBILITY: str = "ONLY_VISIBLE"


# ===================================================================
# Constants — Endpoints (endpoints.go:509-638)
# ===================================================================

# APIResourceMethods constants (endpoints.go:510-523)
API_RESOURCE_METHODS_GET: str = "GET"
API_RESOURCE_METHODS_PUT: str = "PUT"
API_RESOURCE_METHODS_POST: str = "POST"
API_RESOURCE_METHODS_DELETE: str = "DELETE"
API_RESOURCE_METHODS_HEAD: str = "HEAD"
API_RESOURCE_METHODS_PATCH: str = "PATCH"
API_RESOURCE_METHODS_OPTIONS: str = "OPTIONS"

# MaxBodySize constants (endpoints.go:525-541)
MAX_BODY_SIZE_SIZE_6K: str = "SIZE_6K"
MAX_BODY_SIZE_SIZE_8K: str = "SIZE_8K"
MAX_BODY_SIZE_SIZE_12K: str = "SIZE_12K"
MAX_BODY_SIZE_SIZE_16K: str = "SIZE_16K"
MAX_BODY_SIZE_NO_LIMIT: str = "NO_LIMIT"
MAX_BODY_SIZE_NULL: str = ""

# APIParameterLocation constants (endpoints.go:543-556)
API_PARAMETER_LOCATION_QUERY: str = "query"
API_PARAMETER_LOCATION_COOKIE: str = "cookie"
API_PARAMETER_LOCATION_HEADER: str = "header"
API_PARAMETER_LOCATION_PATH: str = "path"
API_PARAMETER_LOCATION_BODY: str = "body"

# APIParameterType constants (endpoints.go:558-567)
API_PARAMETER_TYPE_STRING: str = "string"
API_PARAMETER_TYPE_INTEGER: str = "integer"
API_PARAMETER_TYPE_NUMBER: str = "number"
API_PARAMETER_TYPE_BOOLEAN: str = "boolean"
API_PARAMETER_TYPE_JSONXML: str = "json/xml"

# APIKeyLocation constants (endpoints.go:569-574)
API_KEY_LOCATION_COOKIE: str = "cookie"
API_KEY_LOCATION_HEADER: str = "header"
API_KEY_LOCATION_QUERY: str = "query"

# ConsumeType constants (endpoints.go:576-593)
CONSUME_TYPE_JSON: str = "json"
CONSUME_TYPE_XML: str = "xml"
CONSUME_TYPE_JSONXML: str = "json/xml"
CONSUME_TYPE_URLENCODED: str = "urlencoded"
CONSUME_TYPE_JSON_URLENCODED: str = "json/urlencoded"
CONSUME_TYPE_XML_URLENCODED: str = "xml/urlencoded"
CONSUME_TYPE_JSONXML_URLENCODED: str = "json/xml/urlencoded"
CONSUME_TYPE_ANY: str = "any"
CONSUME_TYPE_NONE: str = "none"

# ImportFileFormat constants (endpoints.go:595-598)
IMPORT_FILE_FORMAT_RAML: str = "raml"
IMPORT_FILE_FORMAT_SWAGGER: str = "swagger"

# ImportFileSource constants (endpoints.go:600-603)
IMPORT_FILE_SOURCE_URL: str = "URL"
IMPORT_FILE_SOURCE_BASE64: str = "BODY_BASE64"

# APIEndpointScheme constants (endpoints.go:605-610)
API_ENDPOINT_SCHEME_HTTP: str = "http"
API_ENDPOINT_SCHEME_HTTPS: str = "https"
API_ENDPOINT_SCHEME_HTTP_HTTPS: str = "http/https"

# APISource constants (endpoints.go:612-615)
API_SOURCE_USER: str = "USER"
API_SOURCE_API_DISCOVERY: str = "API_DISCOVERY"

# SourceType constants (endpoints.go:617-620)
SOURCE_TYPE_SWAGGER: str = "SWAGGER"
SOURCE_TYPE_RAML: str = "RAML"

# ListEndpointSortType constants (endpoints.go:622-625)
NAME_SORT: str = "name"
UPDATE_ENDPOINT_DATE_SORT: str = "updateDate"

# VersionPreference constants (endpoints.go:627-630)
VERSION_PREFERENCE_LAST_UPDATED: str = "LAST_UPDATED"
VERSION_PREFERENCE_ACTIVATED_FIRST: str = "ACTIVATED_FIRST"

# APIVersionInfoLocation constants (endpoints.go:632-637)
API_VERSION_LOCATION_HEADER: str = "HEADER"
API_VERSION_LOCATION_BASE_PATH: str = "BASE_PATH"
API_VERSION_LOCATION_QUERY: str = "QUERY"


# ===================================================================
# Custom Types
# ===================================================================

class RestrictionsBool:
    """Custom boolean type that serializes as 0/1 in JSON.

    Mirrors Go restrictionsBool (endpoints.go:314, 1155-1173).
    In Go JSON: 0 = false, 1 = true.
    """

    def __init__(self, value: bool = False):
        self.value = value

    def __bool__(self) -> bool:
        return self.value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, RestrictionsBool):
            return self.value == other.value
        if isinstance(other, bool):
            return self.value == other
        return NotImplemented

    def __repr__(self) -> str:
        return f"RestrictionsBool({self.value})"

    @staticmethod
    def from_json(data: int) -> RestrictionsBool:
        """Deserialize from JSON 0/1 integer representation.

        Mirrors Go UnmarshalJSON (endpoints.go:1155-1166).
        """
        if data == 0:
            return RestrictionsBool(False)
        if data == 1:
            return RestrictionsBool(True)
        raise ValueError(f"boolean unmarshal error: invalid input {data}")

    def to_json(self) -> int:
        """Serialize to JSON 0/1 integer representation.

        Mirrors Go MarshalJSON (endpoints.go:1168-1173).
        """
        return 1 if self.value else 0


# ===================================================================
# Leaf Dataclasses — No references to other custom types
# ===================================================================

@dataclass
class LengthRestriction:
    """Information about length restrictions for string type parameters.

    Mirrors Go LengthRestriction (endpoints.go:446-449).
    """
    length_max: int = 0    # json:"lengthMax"
    length_min: int = 0    # json:"lengthMin"


@dataclass
class RangeRestriction:
    """Information about range restrictions for integer type parameters.

    Mirrors Go RangeRestriction (endpoints.go:452-455).
    """
    range_min: int = 0     # json:"rangeMin"
    range_max: int = 0     # json:"rangeMax"


@dataclass
class NumberRangeRestriction:
    """Information about range restrictions for number type parameters.

    Mirrors Go NumberRangeRestriction (endpoints.go:458-461).
    Uses float64 in Go.
    """
    number_range_min: float = 0.0  # json:"numberRangeMin"
    number_range_max: float = 0.0  # json:"numberRangeMax"


@dataclass
class ArrayRestriction:
    """Information about array restrictions for array type parameters.

    Mirrors Go ArrayRestriction (endpoints.go:464-467).
    """
    max_items: int = 0     # json:"maxItems"
    min_items: int = 0     # json:"minItems"


@dataclass
class XMLConversionRule:
    """Information about an XML representation of a JSON-encoded parameter.

    Mirrors Go XMLConversionRule (endpoints.go:437-443).
    """
    attribute: bool = False    # json:"attribute"
    wrapped: bool = False      # json:"wrapped"
    name: str = ""             # json:"name,omitempty"
    namespace: str = ""        # json:"namespace,omitempty"
    prefix: str = ""           # json:"prefix,omitempty"


@dataclass
class ResponseRestriction:
    """Information about response restrictions.

    Mirrors Go ResponseRestriction (endpoints.go:470-473).
    """
    status_codes: list[int] = field(default_factory=list)  # json:"statusCodes"
    max_body_size: str = ""                                 # json:"maxBodySize,omitempty"


@dataclass
class AllowMethodUndefinedParameters:
    """Flags controlling which parameter locations allow undefined parameters.

    Mirrors Go AllowMethodUndefinedParameters (endpoints.go:393-398).
    """
    cookie: bool = False   # json:"cookie"
    header: bool = False   # json:"header"
    body: bool = False     # json:"body"
    query: bool = False    # json:"query"


@dataclass
class MethodRestrictions:
    """Method-level restriction settings.

    Mirrors Go MethodRestrictions (endpoints.go:388-390).
    """
    allow_method_undefined_parameters: AllowMethodUndefinedParameters | None = None
    # json:"allowMethodUndefinedParameters"


@dataclass
class SecuritySchemeDetail:
    """Details about an API key security scheme.

    Mirrors Go SecuritySchemeDetail (endpoints.go:213-216).
    """
    api_key_name: str = ""          # json:"apiKeyName,omitempty"
    api_key_location: str = ""      # json:"apiKeyLocation"


@dataclass
class SecurityScheme:
    """Security scheme applied to an API endpoint.

    Mirrors Go SecurityScheme (endpoints.go:207-210).
    Both fields are non-pointer in Go.
    """
    security_scheme_type: str = ""                             # json:"securitySchemeType"
    security_scheme_detail: SecuritySchemeDetail | None = None  # json:"securitySchemeDetail"


@dataclass
class Source:
    """Source information for an API endpoint.

    Mirrors Go Source (endpoints.go:265-269).
    """
    type: str = ""                        # json:"type,omitempty"
    api_version: str = ""                 # json:"apiVersion,omitempty"
    specification_version: str = ""       # json:"specificationVersion,omitempty"


@dataclass
class APIVersionInfo:
    """Information about API versioning.

    Mirrors Go APIVersionInfo (endpoints.go:420-424).
    """
    location: str = ""           # json:"location,omitempty"
    parameter_name: str = ""     # json:"parameterName,omitempty"
    value: str = ""              # json:"value,omitempty"


@dataclass
class APIParameterRestriction:
    """Restrictions associated with an API parameter.

    Mirrors Go APIParameterRestriction (endpoints.go:427-434).
    """
    length_restriction: LengthRestriction | None = None
    # json:"lengthRestriction,omitempty"
    range_restriction: RangeRestriction | None = None
    # json:"rangeRestriction,omitempty"
    number_range_restriction: NumberRangeRestriction | None = None
    # json:"numberRangeRestriction,omitempty"
    array_restriction: ArrayRestriction | None = None
    # json:"arrayRestriction,omitempty"
    xml_conversion_rule: XMLConversionRule | None = None
    # json:"xmlConversionRule,omitempty"
    response_restriction: ResponseRestriction | None = None
    # json:"responseRestriction,omitempty"


@dataclass
class EndpointError:
    """Error information for an endpoint state.

    Mirrors Go EndpointError (endpoints.go:280-285).
    """
    timestamp: str = ""       # json:"timestamp"
    status: str = ""          # json:"status"
    type: str = ""            # json:"type"
    version_number: int = 0   # json:"versionNumber"


@dataclass
class VersionState:
    """Represents the activation state of an endpoint version.

    Mirrors Go VersionState (endpoints.go:272-277).
    All fields are pointers in Go.
    """
    version_number: int | None = None          # json:"versionNumber" (*int64)
    status: str | None = None                  # json:"status" (*ActivationStatus)
    timestamp: str | None = None               # json:"timestamp" (*string)
    last_error: EndpointError | None = None    # json:"lastError" (*EndpointError)

    def is_active(self) -> bool:
        """Check if this version state is currently active.

        Mirrors Go VersionState.IsActive() (endpoints.go:869-871):
        return n.Status != nil && *n.Status == ActivationStatusActive
        """
        return self.status is not None and self.status == ACTIVATION_STATUS_ACTIVE


@dataclass
class APIMethod:
    """Method information for an API resource.

    Mirrors Go APIMethod (endpoints.go:252-259).
    """
    api_resource_method_id: int = 0          # json:"apiResourceMethodId"
    api_resource_method_logic_id: int = 0    # json:"apiResourceMethodLogicId"
    api_resource_method: str = ""            # json:"apiResourceMethod"
    is_private: bool = False                 # json:"isPrivate"
    staging_version: VersionState | None = None      # json:"stagingVersion"
    production_version: VersionState | None = None   # json:"productionVersion"


@dataclass
class APIResourceBaseInfo:
    """Base information for an API resource.

    Mirrors Go APIResourceBaseInfo (endpoints.go:235-249).
    """
    created_by: str | None = None            # json:"createdBy,omitempty" (*string)
    create_date: str | None = None           # json:"createDate,omitempty" (*string)
    update_date: str | None = None           # json:"updateDate,omitempty" (*string)
    updated_by: str | None = None            # json:"updatedBy,omitempty" (*string)
    lock_version: int = 0                    # json:"lockVersion"
    api_resource_id: int = 0                 # json:"apiResourceId"
    api_resource_name: str = ""              # json:"apiResourceName"
    resource_path: str = ""                  # json:"resourcePath"
    description: str | None = None           # json:"description,omitempty" (*string)
    link: str | None = None                  # json:"link,omitempty" (*string)
    api_resource_cloned_from_id: int = 0     # json:"apiResourceClonedFromId"
    api_resource_logic_id: int = 0           # json:"apiResourceLogicId"
    private: bool = False                    # json:"private"


@dataclass
class APIParameter:
    """Parameter definition for an API resource method.

    Mirrors Go APIParameter (endpoints.go:401-414).
    """
    api_parameter_name: str = ""                   # json:"apiParameterName"
    api_parameter_required: bool = False            # json:"apiParameterRequired"
    api_parameter_location: str = ""                # json:"apiParameterLocation"
    path_param_location_id: int | None = None      # json:"pathParamLocationId,omitempty" (*int64)
    api_parameter_type: str = ""                   # json:"apiParameterType"
    array: bool | None = None                      # json:"array,omitempty" (*bool)
    api_parameter_notes: str | None = None         # json:"apiParameterNotes,omitempty" (*string)
    api_parameter_restriction: APIParameterRestriction | None = None
    # json:"apiParameterRestriction,omitempty" (*APIParameterRestriction)
    api_child_parameters: list[APIParameter] = field(default_factory=list)
    # json:"apiChildParameters"
    api_parameter_id: int | None = None            # json:"apiParameterId,omitempty" (*int64)
    api_param_logic_id: int | None = None          # json:"apiParamLogicId,omitempty" (*int64)
    api_resource_meth_param_id: int | None = None  # json:"apiResourceMethParamId"


@dataclass
class APIResourceMethod:
    """Method definition for an API resource.

    Mirrors Go APIResourceMethod (endpoints.go:361-367).
    """
    api_resource_method_id: int | None = None        # json:"apiResourceMethodId" (*int64)
    api_resource_method_logic_id: int | None = None  # json:"apiResourceMethodLogicId" (*int64)
    api_resource_method: str = ""                     # json:"apiResourceMethod"
    api_parameters: list[APIParameter] = field(default_factory=list)
    # json:"apiParameters,omitempty"
    method_restrictions: MethodRestrictions | None = None
    # json:"methodRestrictions,omitempty" (*MethodRestrictions)


@dataclass
class APIResourceMethodRes:
    """Resource method response with additional metadata.

    Mirrors Go APIResourceMethodRes (endpoints.go:370-385).
    """
    api_resource_method_id: int = 0                  # json:"apiResourceMethodId"
    api_resource_method: str = ""                    # json:"apiResourceMethod"
    api_resource_method_logic_id: int = 0            # json:"apiResourceMethodLogicId"
    api_parameters: list[APIParameter] = field(default_factory=list)
    # json:"apiParameters"
    api_resource_name: str = ""                      # json:"apiResourceName"
    create_date: str = ""                            # json:"createDate"
    create_by: str = ""                              # json:"createBy"
    description: str = ""                            # json:"description"
    link: str = ""                                   # json:"link"
    lock_version: int = 0                            # json:"lockVersion"
    private: bool = False                            # json:"private"
    resource_path: str = ""                          # json:"resourcePath"
    update_date: str = ""                            # json:"updateDate"
    updated_by: str = ""                             # json:"updatedBy"


@dataclass
class APIResource:
    """Resource definition for an API endpoint.

    Mirrors Go APIResource (endpoints.go:317-333).
    """
    api_resource_cloned_from_id: int | None = None  # json:"apiResourceClonedFromId" (*int64)
    api_resource_id: int | None = None               # json:"apiResourceId,omitempty" (*int64)
    api_resource_logic_id: int | None = None          # json:"apiResourceLogicId,omitempty" (*int64)
    api_resource_method_name_lists: list[str] = field(default_factory=list)
    # json:"apiResourceMethodNameLists,omitempty"
    api_resource_methods: list[APIResourceMethod] = field(default_factory=list)
    # json:"apiResourceMethods,omitempty"
    api_resource_name: str = ""                      # json:"apiResourceName"
    create_date: str = ""                            # json:"createDate,omitempty"
    created_by: str = ""                             # json:"createdBy,omitempty"
    description: str = ""                            # json:"description,omitempty" (not pointer)
    link: str | None = None                          # json:"link,omitempty" (*string)
    lock_version: int | None = None                  # json:"lockVersion,omitempty" (*int64)
    private: bool | None = None                      # json:"private,omitempty" (*bool)
    resource_path: str = ""                          # json:"resourcePath"
    update_date: str = ""                            # json:"updateDate,omitempty"
    updated_by: str = ""                             # json:"updatedBy,omitempty"


@dataclass
class APIResourceRes:
    """Resource response with method results.

    Mirrors Go APIResourceRes (endpoints.go:336-342).
    """
    api_resource_cloned_from_id: int | None = None   # json:"apiResourceClonedFromId" (*int64)
    api_resource_id: int = 0                         # json:"apiResourceId"
    api_resource_logic_id: int = 0                   # json:"apiResourceLogicId"
    api_resource_method_name_lists: list[str] = field(default_factory=list)
    # json:"apiResourceMethodNameLists"
    api_resource_methods_res: list[APIResourceMethodRes] = field(default_factory=list)
    # json:"apiResourceMethodsRes"


@dataclass
class APIParameterRes:
    """API parameter response representation.

    Mirrors Go APIParameterRes (endpoints.go:345-358).
    """
    api_parameter_id: int = 0                      # json:"apiParameterId"
    api_parameter_name: str = ""                   # json:"apiParameterName"
    api_parameter_required: bool = False            # json:"apiParameterRequired"
    api_parameter_location: str = ""               # json:"apiParameterLocation"
    path_param_location_id: int = 0                # json:"pathParamLocationId"
    api_parameter_type: str = ""                   # json:"apiParameterType"
    array: bool = False                            # json:"array"
    api_param_logic_id: int = 0                    # json:"apiParamLogicId"
    api_resource_meth_param_id: int = 0            # json:"apiResourceMethParamId"
    api_parameter_notes: str = ""                  # json:"apiParameterNotes"
    api_parameter_restriction: APIParameterRestriction | None = None
    # json:"apiParameterRestriction"
    api_child_parameters: list[APIParameterRes] = field(default_factory=list)
    # json:"apiChildParameters"


# ===================================================================
# AkamaiSecurityRestrictions — uses RestrictionsBool
# (endpoints.go:288-312)
# ===================================================================

@dataclass
class AkamaiSecurityRestrictions:
    """Akamai security restriction settings for an API endpoint.

    Mirrors Go AkamaiSecurityRestrictions (endpoints.go:288-312).
    Fields with *restrictionsBool type use RestrictionsBool | None.
    JSON tags are UPPERCASE.
    """
    max_jsonxml_element: int | None = None
    # json:"MAX_JSONXML_ELEMENT,omitempty" (*int64)
    max_element_name_length: int | None = None
    # json:"MAX_ELEMENT_NAME_LENGTH,omitempty" (*int64)
    max_string_length: int | None = None
    # json:"MAX_STRING_LENGTH,omitempty" (*int64)
    max_integer_value: int | None = None
    # json:"MAX_INTEGER_VALUE,omitempty" (*int64)
    max_doc_depth: int | None = None
    # json:"MAX_DOC_DEPTH,omitempty" (*int64)
    max_body_size: int | None = None
    # json:"MAX_BODY_SIZE,omitempty" (*int64)
    positive_security_version: int | None = None
    # json:"POSITIVE_SECURITY_VERSION,omitempty" (*int64)
    positive_security_enabled: RestrictionsBool | None = None
    # json:"POSITIVE_SECURITY_ENABLED"
    allow_undefined_resources: RestrictionsBool | None = None
    # json:"ALLOW_UNDEFINED_RESOURCES"
    allow_only_spec_undefined_methods: RestrictionsBool | None = None
    # json:"ALLOW_ONLY_SPEC_UNDEFINED_METHODS"
    allow_undefined_method_get: RestrictionsBool | None = None
    # json:"ALLOW_UNDEFINED_METHOD_GET"
    allow_undefined_method_post: RestrictionsBool | None = None
    # json:"ALLOW_UNDEFINED_METHOD_POST"
    allow_undefined_method_put: RestrictionsBool | None = None
    # json:"ALLOW_UNDEFINED_METHOD_PUT"
    allow_undefined_method_delete: RestrictionsBool | None = None
    # json:"ALLOW_UNDEFINED_METHOD_DELETE"
    allow_undefined_method_head: RestrictionsBool | None = None
    # json:"ALLOW_UNDEFINED_METHOD_HEAD"
    allow_undefined_method_options: RestrictionsBool | None = None
    # json:"ALLOW_UNDEFINED_METHOD_OPTIONS"
    allow_undefined_method_patch: RestrictionsBool | None = None
    # json:"ALLOW_UNDEFINED_METHOD_PATCH"
    allow_undefined_params: RestrictionsBool | None = None
    # json:"ALLOW_UNDEFINED_PARAMS"
    allow_undefined_spec_params: RestrictionsBool | None = None
    # json:"ALLOW_UNDEFINED_SPEC_PARAMS"
    allow_undefined_cookie_params: RestrictionsBool | None = None
    # json:"ALLOW_UNDEFINED_COOKIE_PARAMS"
    allow_undefined_query_params: RestrictionsBool | None = None
    # json:"ALLOW_UNDEFINED_QUERY_PARAMS"
    allow_undefined_body_params: RestrictionsBool | None = None
    # json:"ALLOW_UNDEFINED_BODY_PARAMS"
    allow_undefined_header_params: RestrictionsBool | None = None
    # json:"ALLOW_UNDEFINED_HEADER_PARAMS"


@dataclass
class APISourceDiff:
    """Diff information between API source and saved values.

    Mirrors Go APISourceDiff (endpoints.go:74-78).
    """
    name: str = ""             # json:"name"
    source_value: str = ""     # json:"sourceValue"
    saved_value: str = ""      # json:"savedValue"


# ===================================================================
# Endpoint Hierarchy (endpoints.go:20-71)
# Go uses struct embedding; Python duplicates fields for each level
# ===================================================================

@dataclass
class Endpoint:
    """Holds configuration for an API endpoint.

    Mirrors Go Endpoint (endpoints.go:20-55).
    """
    api_endpoint_id: int = 0                       # json:"apiEndPointId"
    api_endpoint_name: str = ""                    # json:"apiEndPointName"
    description: str | None = None                 # json:"description" (*string)
    base_path: str = ""                            # json:"basePath"
    consume_type: str | None = None                # json:"consumeType" (*ConsumeType)
    api_endpoint_scheme: str | None = None         # json:"apiEndPointScheme" (*APIEndpointScheme)
    api_endpoint_version: int = 0                  # json:"apiEndPointVersion"
    contract_id: str = ""                          # json:"contractId"
    group_id: int = 0                              # json:"groupId"
    version_number: int = 0                        # json:"versionNumber"
    cloned_from_version: int | None = None         # json:"clonedFromVersion" (*int64)
    locked: bool = False                           # json:"locked"
    staging_version: VersionState | None = None    # json:"stagingVersion"
    production_version: VersionState | None = None  # json:"productionVersion"
    protected_by_api_key: bool = False             # json:"protectedByApiKey"
    api_gateway_enabled: bool = False              # json:"apiGatewayEnabled"
    case_sensitive: bool = False                   # json:"caseSensitive"
    api_endpoint_hosts: list[str] = field(default_factory=list)
    # json:"apiEndPointHosts"
    api_category_ids: list[int] = field(default_factory=list)
    # json:"apiCategoryIds"
    api_resource_base_info: list[APIResourceBaseInfo] = field(default_factory=list)
    # json:"apiResourceBaseInfo"
    source: Source | None = None                   # json:"source" (*Source)
    api_version_info: APIVersionInfo | None = None  # json:"apiVersionInfo" (*APIVersionInfo)
    positive_constrains_enabled: bool = False       # json:"positiveConstrainsEnabled"
    version_hidden: bool = False                   # json:"versionHidden"
    endpoint_hidden: bool = False                  # json:"endpointHidden"
    is_graphql: bool = False                       # json:"isGraphQL,omitempty"
    match_path_segment_param: bool = False         # json:"matchPathSegmentParam"
    available_actions: list[str] = field(default_factory=list)
    # json:"availableActions"
    api_source: str | None = None                  # json:"apiSource" (*string)
    lock_version: int = 0                          # json:"lockVersion"
    updated_by: str = ""                           # json:"updatedBy"
    created_by: str = ""                           # json:"createdBy"
    create_date: str = ""                          # json:"createDate"
    update_date: str = ""                          # json:"updateDate"


@dataclass
class EndpointDetail:
    """Endpoint with security details.

    Mirrors Go EndpointDetail (endpoints.go:58-62).
    Embeds all Endpoint fields + SecurityScheme + AkamaiSecurityRestrictions.
    """
    # Endpoint fields (embedded)
    api_endpoint_id: int = 0
    api_endpoint_name: str = ""
    description: str | None = None
    base_path: str = ""
    consume_type: str | None = None
    api_endpoint_scheme: str | None = None
    api_endpoint_version: int = 0
    contract_id: str = ""
    group_id: int = 0
    version_number: int = 0
    cloned_from_version: int | None = None
    locked: bool = False
    staging_version: VersionState | None = None
    production_version: VersionState | None = None
    protected_by_api_key: bool = False
    api_gateway_enabled: bool = False
    case_sensitive: bool = False
    api_endpoint_hosts: list[str] = field(default_factory=list)
    api_category_ids: list[int] = field(default_factory=list)
    api_resource_base_info: list[APIResourceBaseInfo] = field(default_factory=list)
    source: Source | None = None
    api_version_info: APIVersionInfo | None = None
    positive_constrains_enabled: bool = False
    version_hidden: bool = False
    endpoint_hidden: bool = False
    is_graphql: bool = False
    match_path_segment_param: bool = False
    available_actions: list[str] = field(default_factory=list)
    api_source: str | None = None
    lock_version: int = 0
    updated_by: str = ""
    created_by: str = ""
    create_date: str = ""
    update_date: str = ""
    # EndpointDetail-specific fields
    security_scheme: SecurityScheme | None = None
    # json:"securityScheme,omitempty" (*SecurityScheme)
    akamai_security_restrictions: AkamaiSecurityRestrictions | None = None
    # json:"akamaiSecurityRestrictions,omitempty" (*AkamaiSecurityRestrictions)


@dataclass
class EndpointWithResources:
    """Endpoint with security details and associated resources.

    Mirrors Go EndpointWithResources (endpoints.go:65-71).
    Embeds all EndpointDetail fields + APIResources + metadata.
    """
    # Endpoint fields (embedded via EndpointDetail)
    api_endpoint_id: int = 0
    api_endpoint_name: str = ""
    description: str | None = None
    base_path: str = ""
    consume_type: str | None = None
    api_endpoint_scheme: str | None = None
    api_endpoint_version: int = 0
    contract_id: str = ""
    group_id: int = 0
    version_number: int = 0
    cloned_from_version: int | None = None
    locked: bool = False
    staging_version: VersionState | None = None
    production_version: VersionState | None = None
    protected_by_api_key: bool = False
    api_gateway_enabled: bool = False
    case_sensitive: bool = False
    api_endpoint_hosts: list[str] = field(default_factory=list)
    api_category_ids: list[int] = field(default_factory=list)
    api_resource_base_info: list[APIResourceBaseInfo] = field(default_factory=list)
    source: Source | None = None
    api_version_info: APIVersionInfo | None = None
    positive_constrains_enabled: bool = False
    version_hidden: bool = False
    endpoint_hidden: bool = False
    is_graphql: bool = False
    match_path_segment_param: bool = False
    available_actions: list[str] = field(default_factory=list)
    api_source: str | None = None
    lock_version: int = 0
    updated_by: str = ""
    created_by: str = ""
    create_date: str = ""
    update_date: str = ""
    # EndpointDetail-specific fields
    security_scheme: SecurityScheme | None = None
    akamai_security_restrictions: AkamaiSecurityRestrictions | None = None
    # EndpointWithResources-specific fields
    api_resources: list[APIResource] = field(default_factory=list)
    # json:"apiResources"
    discovered_pii_ids: list[int] = field(default_factory=list)
    # json:"discoveredPiiIds"
    production_status: str | None = None   # json:"productionStatus" (*string)
    staging_status: str | None = None      # json:"stagingStatus" (*string)


# ===================================================================
# Request / Response models — endpoints.go
# ===================================================================

@dataclass
class RegisterEndpointRequest:
    """Request body for registering a new API endpoint.

    Mirrors Go RegisterEndpointRequest (endpoints.go:81-102).
    """
    security_scheme: SecurityScheme | None = None
    # json:"securityScheme,omitempty" (*SecurityScheme)
    akamai_security_restrictions: AkamaiSecurityRestrictions | None = None
    # json:"akamaiSecurityRestrictions,omitempty" (*AkamaiSecurityRestrictions)
    version_number: int = 0                       # json:"versionNumber,omitempty"
    api_endpoint_name: str = ""                   # json:"apiEndPointName"
    description: str = ""                         # json:"description,omitempty" (not a pointer)
    discovered_pii_ids: list[int] = field(default_factory=list)
    # json:"discoveredPiiIds,omitempty"
    base_path: str = ""                           # json:"basePath,omitempty"
    api_endpoint_scheme: str = ""                  # json:"apiEndPointScheme,omitempty"
    consume_type: str = ""                         # json:"consumeType,omitempty"
    api_endpoint_hosts: list[str] = field(default_factory=list)
    # json:"apiEndPointHosts"
    api_category_ids: list[int] = field(default_factory=list)
    # json:"apiCategoryIds,omitempty"
    case_sensitive: bool | None = None             # json:"caseSensitive,omitempty" (*bool)
    match_path_segment_param: bool | None = None   # json:"matchPathSegmentParam,omitempty" (*bool)
    is_graphql: bool | None = None                 # json:"isGraphQL,omitempty" (*bool)
    api_resources: list[APIResource] = field(default_factory=list)
    # json:"apiResources,omitempty"
    api_version_info: APIVersionInfo | None = None  # json:"apiVersionInfo,omitempty"
    api_source: str = ""                           # json:"apiSource,omitempty"
    api_gateway_enabled: bool | None = None        # json:"apiGatewayEnabled,omitempty"
    contract_id: str = ""                           # json:"contractId"
    group_id: int = 0                               # json:"groupId"


@dataclass
class RegisterEndpointFromFileRequest:
    """Request body for registering an API endpoint from an import file.

    Mirrors Go RegisterEndpointFromFileRequest (endpoints.go:111-119).
    """
    contract_id: str = ""                  # json:"contractId"
    group_id: int = 0                      # json:"groupId"
    import_file_content: str | None = None  # json:"importFileContent,omitempty" (*string)
    import_file_format: str = ""            # json:"importFileFormat"
    import_file_source: str = ""            # json:"importFileSource"
    import_url: str | None = None           # json:"importUrl,omitempty" (*string)
    root: str | None = None                 # json:"root,omitempty" (*string)


@dataclass
class ShowEndpointRequest:
    """Request to show (unhide) an API endpoint.

    Mirrors Go ShowEndpointRequest (endpoints.go:122-124).
    """
    api_endpoint_id: int = 0  # no json tag (path param)


@dataclass
class ShowEndpointResponse(EndpointWithResources):
    """Response from showing an API endpoint.

    Mirrors Go ShowEndpointResponse (endpoints.go:127-129).
    Embeds EndpointWithResources.
    """


@dataclass
class HideEndpointRequest:
    """Request to hide an API endpoint.

    Mirrors Go HideEndpointRequest (endpoints.go:132-134).
    """
    api_endpoint_id: int = 0  # no json tag (path param)


@dataclass
class HideEndpointResponse(EndpointWithResources):
    """Response from hiding an API endpoint.

    Mirrors Go HideEndpointResponse (endpoints.go:137-139).
    Embeds EndpointWithResources.
    """


@dataclass
class GetEndpointRequest:
    """Request to get an API endpoint.

    Mirrors Go GetEndpointRequest (endpoints.go:142-144).
    """
    api_endpoint_id: int = 0  # no json tag (path param)


@dataclass
class DeleteEndpointRequest:
    """Request to delete an API endpoint.

    Mirrors Go DeleteEndpointRequest (endpoints.go:150-152).
    """
    api_endpoint_id: int = 0  # no json tag (path param)


@dataclass
class EndpointResponse:
    """Full endpoint response model.

    Mirrors Go EndpointResponse (endpoints.go:155-189).
    """
    contract_id: str = ""                          # json:"contractId"
    group_id: int = 0                              # json:"groupId"
    api_endpoint_id: int = 0                       # json:"apiEndPointId"
    api_endpoint_version: int = 0                  # json:"apiEndPointVersion" (not pointer)
    version_number: int = 0                        # json:"versionNumber"
    api_endpoint_name: str = ""                    # json:"apiEndPointName"
    description: str | None = None                 # json:"description" (*string)
    base_path: str = ""                            # json:"basePath"
    cloned_from_version: int | None = None         # json:"clonedFromVersion" (*int64)
    api_endpoint_locked: bool = False              # json:"apiEndPointLocked"
    api_endpoint_scheme: str | None = None         # json:"apiEndPointScheme" (*APIEndpointScheme)
    consume_type: str | None = None                # json:"consumeType" (*ConsumeType)
    api_endpoint_hosts: list[str] = field(default_factory=list)
    # json:"apiEndPointHosts"
    api_category_ids: list[int] = field(default_factory=list)
    # json:"apiCategoryIds"
    lock_version: int = 0                          # json:"lockVersion"
    updated_by: str = ""                           # json:"updatedBy"
    created_by: str = ""                           # json:"createdBy"
    create_date: str = ""                          # json:"createDate"
    update_date: str = ""                          # json:"updateDate"
    positive_constrains_enabled: bool = False       # json:"positiveConstrainsEnabled"
    case_sensitive: bool = False                    # json:"caseSensitive" (not pointer)
    match_path_segment_param: bool = False         # json:"matchPathSegmentParam"
    source: Source | None = None                   # json:"source" (*Source)
    staging_version: VersionState | None = None    # json:"stagingVersion" (not pointer in Go)
    production_version: VersionState | None = None  # json:"productionVersion" (not pointer in Go)
    protected_by_api_key: bool = False             # json:"protectedByApiKey"
    is_graphql: bool = False                       # json:"isGraphQL,omitempty"
    available_actions: list[str] = field(default_factory=list)
    # json:"availableActions"
    version_hidden: bool = False                   # json:"versionHidden"
    endpoint_hidden: bool = False                  # json:"endpointHidden"
    api_source: str | None = None                  # json:"apiSource" (*string)
    api_gateway_enabled: bool = False              # json:"apiGatewayEnabled" (not pointer)
    api_version_info: APIVersionInfo | None = None  # json:"apiVersionInfo" (*APIVersionInfo)


@dataclass
class ListEndpointsRequest:
    """Request parameters for listing API endpoints.

    Mirrors Go ListEndpointsRequest (endpoints.go:192-204).
    All fields are query params (no json tags).
    """
    pii_only: bool = False              # PIIOnly
    page: int = 0                       # Page
    page_size: int = 0                  # PageSize
    category: str = ""                  # Category
    contains: str = ""                  # Contains
    sort_by: str = ""                   # SortBy (ListEndpointSortType)
    sort_order: str = ""                # SortOrder (SortOrderType)
    version_preference: str = ""        # VersionPreference
    show: str = ""                      # Show (Visibility)
    contract_id: str = ""               # ContractID
    group_id: int = 0                   # GroupID


@dataclass
class RegisterEndpointResponse(EndpointWithResources):
    """Response from registering an API endpoint.

    Mirrors Go RegisterEndpointResponse (endpoints.go:219-221).
    Embeds EndpointWithResources.
    """


@dataclass
class ListEndpointsResponse:
    """Response from listing API endpoints.

    Mirrors Go ListEndpointsResponse (endpoints.go:227-232).
    """
    total_size: int = 0                        # json:"totalSize"
    page: int = 0                              # json:"page"
    page_size: int = 0                         # json:"pageSize"
    api_endpoints: list[Endpoint] = field(default_factory=list)
    # json:"apiEndPoints"


# ===================================================================
# Endpoint Version models (endpoint_versions.go)
# ===================================================================

@dataclass
class ListEndpointVersionsRequest:
    """Request parameters for listing endpoint versions.

    Mirrors Go ListEndpointVersionsRequest (endpoint_versions.go:17-24).
    All fields are path/query params (no json tags).
    """
    api_endpoint_id: int = 0     # APIEndpointID
    page: int = 0                # Page
    page_size: int = 0           # PageSize
    sort_by: str = ""            # SortBy (ListEndpointVersionSortType)
    sort_order: str = ""         # SortOrder (SortOrderType)
    visibility: str = ""         # Show (Visibility)


@dataclass
class EndpointVersionRequest:
    """Base request type for endpoint version operations.

    Mirrors Go EndpointVersionRequest (endpoint_versions.go:36-39).
    Used as base for Delete/Clone/Get version requests.
    """
    version_number: int = 0      # VersionNumber
    api_endpoint_id: int = 0     # APIEndpointID


@dataclass
class UpdateEndpointVersionRequest:
    """Request to update an endpoint version.

    Mirrors Go UpdateEndpointVersionRequest (endpoint_versions.go:51-55).
    """
    version_number: int = 0                        # VersionNumber
    api_endpoint_id: int = 0                       # APIEndpointID
    body: UpdateEndpointVersionRequestBody | None = None  # Body


@dataclass
class ListEndpointVersionsResponse:
    """Response from listing endpoint versions.

    Mirrors Go ListEndpointVersionsResponse (endpoint_versions.go:58-65).
    """
    total_size: int = 0                  # json:"totalSize"
    page: int = 0                        # json:"page"
    page_size: int = 0                   # json:"pageSize"
    api_endpoint_id: int = 0             # json:"apiEndPointId"
    api_endpoint_name: str = ""          # json:"apiEndPointName"
    api_versions: list[APIVersion] = field(default_factory=list)
    # json:"apiVersions"


@dataclass
class APIVersion:
    """Summary of an API endpoint version.

    Mirrors Go APIVersion (endpoint_versions.go:77-96).
    """
    create_date: str = ""                    # json:"createDate"
    created_by: str = ""                     # json:"createdBy"
    update_date: str = ""                    # json:"updateDate"
    updated_by: str = ""                     # json:"updatedBy"
    api_endpoint_version_id: int = 0         # json:"apiEndPointVersionId"
    base_path: str = ""                      # json:"basePath"
    version_number: int = 0                  # json:"versionNumber"
    description: str | None = None           # json:"description" (*string)
    based_on: int | None = None              # json:"basedOn" (*int64)
    staging_status: str | None = None        # json:"stagingStatus" (*ActivationStatus)
    production_status: str | None = None     # json:"productionStatus" (*ActivationStatus)
    staging_date: str | None = None          # json:"stagingDate" (*string)
    production_date: str | None = None       # json:"productionDate" (*string)
    is_version_locked: bool = False          # json:"isVersionLocked"
    hidden: bool = False                     # json:"hidden"
    available_actions: list[str] = field(default_factory=list)
    # json:"availableActions"
    cloning_status: str | None = None        # json:"cloningStatus" (*string)
    lock_version: int = 0                    # json:"lockVersion"


@dataclass
class EndpointVersionResponse:
    """Full endpoint version response body.

    Mirrors Go EndpointVersionResponse (endpoint_versions.go:99-143).
    """
    security_scheme: SecurityScheme | None = None
    # json:"securityScheme" (*SecurityScheme)
    akamai_security_restrictions: AkamaiSecurityRestrictions | None = None
    # json:"akamaiSecurityRestrictions" (*AkamaiSecurityRestrictions)
    contract_id: str = ""                          # json:"contractId"
    group_id: int = 0                              # json:"groupId"
    api_endpoint_id: int = 0                       # json:"apiEndPointId"
    api_endpoint_version: int | None = None        # json:"apiEndPointVersion" (*int64)
    version_number: int = 0                        # json:"versionNumber"
    api_endpoint_name: str = ""                    # json:"apiEndPointName"
    description: str | None = None                 # json:"description" (*string)
    base_path: str = ""                            # json:"basePath"
    cloned_from_version: int | None = None         # json:"clonedFromVersion" (*int64)
    api_endpoint_locked: bool = False              # json:"apiEndPointLocked"
    api_endpoint_scheme: str | None = None         # json:"apiEndPointScheme" (*string)
    consume_type: str | None = None                # json:"consumeType" (*string)
    api_endpoint_hosts: list[str] = field(default_factory=list)
    # json:"apiEndPointHosts"
    api_category_ids: list[int] = field(default_factory=list)
    # json:"apiCategoryIds"
    lock_version: int = 0                          # json:"lockVersion"
    updated_by: str = ""                           # json:"updatedBy"
    created_by: str = ""                           # json:"createdBy"
    create_date: str = ""                          # json:"createDate"
    update_date: str = ""                          # json:"updateDate"
    positive_constrains_enabled: bool = False       # json:"positiveConstrainsEnabled"
    case_sensitive: bool | None = None             # json:"caseSensitive" (*bool)
    match_path_segment_param: bool = False         # json:"matchPathSegmentParam"
    source: Source | None = None                   # json:"source" (*Source)
    staging_version: VersionState | None = None    # json:"stagingVersion" (*VersionState)
    production_version: VersionState | None = None  # json:"productionVersion" (*VersionState)
    production_status: str | None = None           # json:"productionStatus" (*string)
    staging_status: str | None = None              # json:"stagingStatus" (*string)
    protected_by_api_key: bool = False             # json:"protectedByApiKey"
    is_graphql: bool = False                       # json:"isGraphQL"
    available_actions: list[str] = field(default_factory=list)
    # json:"availableActions"
    version_hidden: bool = False                   # json:"versionHidden"
    endpoint_hidden: bool = False                  # json:"endpointHidden"
    api_source: str | None = None                  # json:"apiSource" (*string)
    api_source_details: list[APISourceDiff] = field(default_factory=list)
    # json:"apiSourceDetails"
    cloning_status: str | None = None              # json:"cloningStatus" (*string)
    api_gateway_enabled: bool | None = None        # json:"apiGatewayEnabled" (*bool)
    graphql: bool = False                          # json:"graphQL"
    discovered_pii_ids: list[int] = field(default_factory=list)
    # json:"discoveredPiiIds"
    api_version_info: APIVersionInfo | None = None  # json:"apiVersionInfo" (*APIVersionInfo)
    api_resources: list[APIResource] = field(default_factory=list)
    # json:"apiResources"
    locked: bool = False                           # json:"locked"


@dataclass
class UpdateEndpointVersionRequestBody:
    """Body for updating an endpoint version.

    Mirrors Go UpdateEndpointVersionRequestBody (endpoint_versions.go:146-169).
    """
    security_scheme: SecurityScheme | None = None
    # json:"securityScheme" (*SecurityScheme)
    akamai_security_restrictions: AkamaiSecurityRestrictions | None = None
    # json:"akamaiSecurityRestrictions,omitempty" (*AkamaiSecurityRestrictions)
    contract_id: str = ""                          # json:"contractId"
    group_id: int = 0                              # json:"groupId"
    api_endpoint_id: int = 0                       # json:"apiEndPointId"
    api_endpoint_version: int | None = None        # json:"apiEndPointVersion" (*int64)
    version_number: int = 0                        # json:"versionNumber"
    api_endpoint_name: str = ""                    # json:"apiEndPointName"
    description: str | None = None                 # json:"description" (*string)
    base_path: str = ""                            # json:"basePath,omitempty"
    api_endpoint_scheme: str | None = None         # json:"apiEndPointScheme" (*APIEndpointScheme)
    consume_type: str | None = None                # json:"consumeType,omitempty" (*ConsumeType)
    api_endpoint_hosts: list[str] = field(default_factory=list)
    # json:"apiEndPointHosts"
    api_category_ids: list[int] = field(default_factory=list)
    # json:"apiCategoryIds"
    lock_version: int = 0                          # json:"lockVersion"
    case_sensitive: bool | None = None             # json:"caseSensitive,omitempty" (*bool)
    match_path_segment_param: bool = False         # json:"matchPathSegmentParam"
    is_graphql: bool = False                       # json:"isGraphQL"
    api_gateway_enabled: bool | None = None        # json:"apiGatewayEnabled,omitempty"
    graphql: bool = False                          # json:"graphQL"
    api_version_info: APIVersionInfo | None = None  # json:"apiVersionInfo,omitempty"
    api_resources: list[APIResource] = field(default_factory=list)
    # json:"apiResources,omitempty"


# ===================================================================
# Activation models (activations.go)
# ===================================================================

@dataclass
class VerifyVersionRequestBody:
    """Body for verifying an endpoint version.

    Mirrors Go VerifyVersionRequestBody (activations.go:31-33).
    """
    networks: list[str] = field(default_factory=list)  # json:"networks"


@dataclass
class VerifyVersionRequest:
    """Request to verify an endpoint version.

    Mirrors Go VerifyVersionRequest (activations.go:17-21).
    """
    version_number: int = 0                       # VersionNumber
    api_endpoint_id: int = 0                      # APIEndpointID
    body: VerifyVersionRequestBody | None = None  # Body


@dataclass
class ActivationRequestBody:
    """Body for activating an endpoint version.

    Mirrors Go ActivationRequestBody (activations.go:36-40).
    """
    networks: list[str] = field(default_factory=list)
    # json:"networks"
    notes: str = ""                            # json:"notes,omitempty"
    notification_recipients: list[str] = field(default_factory=list)
    # json:"notificationRecipients,omitempty"


@dataclass
class ActivateVersionRequest:
    """Request to activate an endpoint version.

    Mirrors Go ActivateVersionRequest (activations.go:24-28).
    """
    version_number: int = 0                    # VersionNumber
    api_endpoint_id: int = 0                   # APIEndpointID
    body: ActivationRequestBody | None = None  # Body


@dataclass
class ActivateVersionResponse:
    """Response from activating an endpoint version.

    Mirrors Go ActivateVersionResponse (activations.go:43-47).
    Note: Go fields have NO json tags.
    """
    networks: list[str] = field(default_factory=list)
    # Networks []NetworkType (no json tag)
    notes: str = ""
    # Notes string (no json tag)
    notification_recipients: list[str] = field(default_factory=list)
    # NotificationRecipients []string (no json tag)


@dataclass
class DeactivateVersionRequest:
    """Request to deactivate an endpoint version.

    Mirrors Go DeactivateVersionRequest (activations.go:50-54).
    """
    version_number: int = 0                    # VersionNumber
    api_endpoint_id: int = 0                   # APIEndpointID
    body: ActivationRequestBody | None = None  # Body


@dataclass
class DeactivateVersionResponse:
    """Response from deactivating an endpoint version.

    Mirrors Go DeactivateVersionResponse (activations.go:57-61).
    Note: Go fields have NO json tags.
    """
    networks: list[str] = field(default_factory=list)
    # Networks []NetworkType (no json tag)
    notes: str = ""
    # Notes string (no json tag)
    notification_recipients: list[str] = field(default_factory=list)
    # NotificationRecipients []string (no json tag)


@dataclass
class VerifyVersionAlert:
    """Alert from verifying an endpoint version.

    Mirrors Go VerifyVersionAlert (activations.go:76-79).
    """
    detail: str = ""     # json:"detail"
    severity: str = ""   # json:"severity"


# ===================================================================
# Resource Operations models (resource_operations.go)
# ===================================================================

@dataclass
class VersionDetail:
    """Version detail used in resource operation search results.

    Mirrors Go VersionDetail (resource_operations.go:31-35).
    Note: Different from VersionState — uses plain types, not pointers.
    """
    status: str = ""           # json:"status"
    timestamp: str = ""        # json:"timestamp"
    version_number: int = 0    # json:"versionNumber"


@dataclass
class Condition:
    """Condition associated with a resource operation.

    Mirrors Go Condition (resource_operations.go:53-56).
    """
    api_parameter_id: int = 0    # json:"apiParameterId"
    value: str = ""              # json:"value,omitempty"


@dataclass
class OperationMetadata:
    """Metadata for an operation.

    Mirrors Go OperationMetadata (resource_operations.go:59-61).
    """
    is_active: bool = False  # json:"isActive"


@dataclass
class ParameterDetail:
    """Detail of a parameter in an operation.

    Mirrors Go ParameterDetail (resource_operations.go:69-72).
    """
    parameter_id: int = 0        # json:"parameterId"
    used_for_login: Any = None   # json:"usedForLogin" (interface{})


@dataclass
class OperationParameter:
    """Parameter associated with a resource operation.

    Mirrors Go OperationParameter (resource_operations.go:64-66).
    """
    username: ParameterDetail | None = None  # json:"username"


@dataclass
class ResourceMetadata:
    """Metadata for an API resource in search results.

    Mirrors Go ResourceMetadata (resource_operations.go:101-105).
    Note: Go uses plain int (not int64) for these fields.
    """
    methods_enabled: int = 0           # json:"methodsEnabled"
    methods_with_operations: int = 0   # json:"methodsWithOperations"
    operation_count: int = 0           # json:"operationCount"


@dataclass
class ResourceMethod:
    """Method definition for a resource in search results.

    Mirrors Go ResourceMethod (resource_operations.go:92-98).
    """
    api_parameters: list[APIParameter] = field(default_factory=list)
    # json:"apiParameters"
    api_resource_method: str = ""              # json:"apiResourceMethod"
    api_resource_method_id: int = 0            # json:"apiResourceMethodId"
    api_resource_method_logic_id: int = 0      # json:"apiResourceMethodLogicId"
    method_restrictions: Any = None            # json:"methodRestrictions" (interface{})


@dataclass
class Operation:
    """Represents an operation for an API resource.

    Mirrors Go Operation (resource_operations.go:38-50).
    """
    api_endpoint_id: int = 0                            # json:"apiEndPointId"
    api_resource_id: int = 0                            # json:"apiResourceId"
    api_resource_logic_id: int = 0                      # json:"apiResourceLogicId"
    conditions: list[Condition] = field(default_factory=list)
    # json:"conditions,omitempty"
    link: str = ""                                      # json:"link"
    metadata: OperationMetadata | None = None            # json:"metadata"
    method: str = ""                                    # json:"method"
    operation_id: str = ""                              # json:"operationId"
    operation_name: str = ""                            # json:"operationName"
    operation_purpose: str = ""                         # json:"operationPurpose"
    operation_parameter: OperationParameter | None = None
    # json:"operationParameter,omitempty" (*OperationParameter)


@dataclass
class Resource:
    """Represents an API resource in search results.

    Mirrors Go Resource (resource_operations.go:75-89).
    Note: LockVersion is plain int in Go (not int64).
    """
    api_endpoint_id: int = 0                            # json:"apiEndPointId"
    api_resource_id: int = 0                            # json:"apiResourceId"
    api_resource_logic_id: int = 0                      # json:"apiResourceLogicId"
    api_resource_methods: list[ResourceMethod] = field(default_factory=list)
    # json:"apiResourceMethods"
    api_resource_name: str = ""                         # json:"apiResourceName"
    create_date: str = ""                               # json:"createDate"
    created_by: str = ""                                # json:"createdBy"
    link: str = ""                                      # json:"link"
    lock_version: int = 0                               # json:"lockVersion"
    metadata: ResourceMetadata | None = None             # json:"metadata"
    resource_path: str = ""                             # json:"resourcePath"
    update_date: str = ""                               # json:"updateDate"
    updated_by: str = ""                                # json:"updatedBy"


@dataclass
class APIEndpoint:
    """API endpoint information in resource operation search results.

    Mirrors Go APIEndpoint (resource_operations.go:19-28).
    Note: Different from Endpoint — used in search results context.
    """
    api_endpoint_hosts: list[str] = field(default_factory=list)
    # json:"apiEndPointHosts"
    api_endpoint_id: int = 0                   # json:"apiEndPointId"
    api_endpoint_name: str = ""                # json:"apiEndPointName"
    base_path: str = ""                        # json:"basePath"
    case_sensitive: bool = False               # json:"caseSensitive"
    link: str = ""                             # json:"link"
    production_version: VersionDetail | None = None   # json:"productionVersion" (*VersionDetail)
    staging_version: VersionDetail | None = None      # json:"stagingVersion" (*VersionDetail)


@dataclass
class SearchResourceOperationsResponse:
    """Response from searching resource operations.

    Mirrors Go SearchResourceOperationsResponse (resource_operations.go:12-16).
    """
    api_endpoints: list[APIEndpoint] = field(default_factory=list)
    # json:"apiEndPoints"
    operations: list[Operation] = field(default_factory=list)
    # json:"operations"
    resources: list[Resource] = field(default_factory=list)
    # json:"resources"


# ===================================================================
# Type Aliases
# ===================================================================

# endpoints.go:147 — GetEndpointResponse = EndpointDetail
GetEndpointResponse = EndpointDetail

# endpoints.go:224 — RegisterEndpointFromFileResponse = RegisterEndpointResponse
RegisterEndpointFromFileResponse = RegisterEndpointResponse

# endpoints.go:476 — ListUserEntitlementsResponse = []string
ListUserEntitlementsResponse = list[str]

# endpoint_versions.go:42 — DeleteEndpointVersionRequest = EndpointVersionRequest
DeleteEndpointVersionRequest = EndpointVersionRequest

# endpoint_versions.go:45 — CloneEndpointVersionRequest = EndpointVersionRequest
CloneEndpointVersionRequest = EndpointVersionRequest

# endpoint_versions.go:48 — GetEndpointVersionRequest = EndpointVersionRequest
GetEndpointVersionRequest = EndpointVersionRequest

# endpoint_versions.go:68 — GetEndpointVersionResponse = EndpointVersionResponse
GetEndpointVersionResponse = EndpointVersionResponse

# endpoint_versions.go:71 — CloneEndpointVersionResponse = EndpointVersionResponse
CloneEndpointVersionResponse = EndpointVersionResponse

# endpoint_versions.go:74 — UpdateEndpointVersionResponse = EndpointVersionResponse
UpdateEndpointVersionResponse = EndpointVersionResponse

# activations.go:64 — VerifyVersionResponse = []VerifyVersionAlert
VerifyVersionResponse = list[VerifyVersionAlert]
