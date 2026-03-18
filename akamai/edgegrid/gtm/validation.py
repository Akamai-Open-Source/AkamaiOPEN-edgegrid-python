"""GTM request validation functions.

Implements validation functions for all GTM (Global Traffic Management)
request and model types. Each function mirrors the corresponding Go
Validate() method from the AkamaiOPEN-edgegrid-golang/pkg/gtm package.

Request validators return a formatted error string on failure, or None when valid.
Model validators (except validate_domain) follow the same pattern.
validate_domain returns a string error message or None, matching Go's
Domain.Validate() which uses direct length checks instead of ozzo-validation.
"""
# pylint: disable=too-many-lines

from akamai.edgegrid.validation import parse_validation_errors


# ---------------------------------------------------------------------------
# Domain Validations (mirrors pkg/gtm/domain.go)
# ---------------------------------------------------------------------------


def validate_domain(domain) -> str | None:
    """Validate a Domain object.

    Mirrors Go Domain.Validate() which uses direct length checks
    instead of ozzo-validation. Returns an error message string
    if validation fails, or None if the domain is valid.

    Args:
        domain: A Domain object with name and type attributes.

    Returns:
        Error message string if validation fails, None otherwise.
    """
    if len(domain.name) < 1:
        return "Domain is missing Name"
    if len(domain.type) < 1:
        return "Domain is missing Type"
    return None


def validate_get_domain_status_request(request) -> str | None:
    """Validate GetDomainStatusRequest.

    Mirrors Go GetDomainStatusRequest.Validate().
    Required: DomainName.

    Args:
        request: A GetDomainStatusRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_get_domain_request(request) -> str | None:
    """Validate GetDomainRequest.

    Mirrors Go GetDomainRequest.Validate().
    Required: DomainName.

    Args:
        request: A GetDomainRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_create_domain_request(request) -> str | None:
    """Validate CreateDomainRequest.

    Mirrors Go CreateDomainRequest.Validate().
    Required: Domain (the Domain object itself must not be None).

    Args:
        request: A CreateDomainRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if request.domain is None:
        errors["Domain"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_update_domain_request(request) -> str | None:
    """Validate UpdateDomainRequest.

    Mirrors Go UpdateDomainRequest.Validate().
    Required: Domain.

    Args:
        request: An UpdateDomainRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if request.domain is None:
        errors["Domain"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_delete_domain_request(request) -> str | None:
    """Validate DeleteDomainRequest (deprecated).

    Mirrors Go DeleteDomainRequest.Validate().
    Required: DomainName.

    Args:
        request: A DeleteDomainRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_delete_domains_request(request) -> str | None:
    """Validate DeleteDomainsRequest.

    Mirrors Go DeleteDomainsRequest.Validate().
    Required: DomainNames (from request.body.domain_names) must be
    a non-empty list where each element is a non-empty string.
    Uses validation.Required + validation.Each(validation.Required)
    pattern from Go.

    Args:
        request: A DeleteDomainsRequest object with body.domain_names.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.body.domain_names:
        errors["DomainNames"] = "cannot be blank"
    else:
        element_errors = {}
        for i, name in enumerate(request.body.domain_names):
            if not name:
                element_errors[str(i)] = "cannot be blank"
        if element_errors:
            errors["DomainNames"] = element_errors
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_delete_domains_status_request(request) -> str | None:
    """Validate DeleteDomainsStatusRequest.

    Mirrors Go DeleteDomainsStatusRequest.Validate().
    Required: RequestID.

    Args:
        request: A DeleteDomainsStatusRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.request_id:
        errors["RequestID"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


# ---------------------------------------------------------------------------
# Property Validations (mirrors pkg/gtm/property.go)
# ---------------------------------------------------------------------------


def validate_property(prop) -> str | None:
    """Validate a Property object.

    Mirrors Go Property.Validate(). Required fields: Name, Type,
    ScoreAggregationType (error key is 'ScoreAggregationTypes'),
    HandoutMode.

    When property type is 'ranked-failover', also validates traffic
    targets via validate_ranked_failover_traffic_targets().

    Args:
        prop: A Property object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not prop.name:
        errors["Name"] = "cannot be blank"
    if not prop.type:
        errors["Type"] = "cannot be blank"
    if not prop.score_aggregation_type:
        errors["ScoreAggregationTypes"] = "cannot be blank"
    if not prop.handout_mode:
        errors["HandoutMode"] = "cannot be blank"

    if prop.type == "ranked-failover":
        err = validate_ranked_failover_traffic_targets(
            prop.traffic_targets
        )
        if err is not None:
            errors["TrafficTargets"] = err

    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_ranked_failover_traffic_targets(traffic_targets) -> str | None:
    """Validate traffic targets for ranked-failover property type.

    Mirrors Go validateRankedFailoverTrafficTargets(). Enforces:
    - At least one traffic target must exist
    - Each precedence value must be between 0 and 255
    - Only one target may have the lowest (primary) precedence

    Args:
        traffic_targets: List of TrafficTarget objects with
            precedence attribute (int | None).

    Returns:
        Error message string if validation fails, None otherwise.
    """
    if not traffic_targets:
        return "no traffic targets are enabled"

    precedence_counter = {}
    min_precedence = 256

    for target in traffic_targets:
        if target.precedence is None:
            precedence_counter[0] = precedence_counter.get(0, 0) + 1
            min_precedence = 0
        else:
            if target.precedence > 255 or target.precedence < 0:
                return (
                    "'Precedence' value has to be between 0 and 255"
                )
            precedence_counter[target.precedence] = (
                precedence_counter.get(target.precedence, 0) + 1
            )
            min_precedence = min(min_precedence, target.precedence)

    if precedence_counter.get(min_precedence, 0) > 1:
        return (
            "property cannot have multiple primary traffic targets "
            "(targets with lowest precedence)"
        )

    return None


def validate_get_property_request(request) -> str | None:
    """Validate GetPropertyRequest.

    Mirrors Go GetPropertyRequest.Validate().
    Required: DomainName, PropertyName.

    Args:
        request: A GetPropertyRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    if not request.property_name:
        errors["PropertyName"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_list_properties_request(request) -> str | None:
    """Validate ListPropertiesRequest.

    Mirrors Go ListPropertiesRequest.Validate().
    Required: DomainName.

    Args:
        request: A ListPropertiesRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_create_property_request(request) -> str | None:
    """Validate CreatePropertyRequest.

    Mirrors Go CreatePropertyRequest.Validate().
    Required: DomainName, Property.

    Args:
        request: A CreatePropertyRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    if request.property is None:
        errors["Property"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_update_property_request(request) -> str | None:
    """Validate UpdatePropertyRequest.

    Mirrors Go UpdatePropertyRequest.Validate().
    Required: DomainName, Property.

    Args:
        request: An UpdatePropertyRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    if request.property is None:
        errors["Property"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_delete_property_request(request) -> str | None:
    """Validate DeletePropertyRequest.

    Mirrors Go DeletePropertyRequest.Validate().
    Required: DomainName, PropertyName.

    Args:
        request: A DeletePropertyRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    if not request.property_name:
        errors["PropertyName"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


# ---------------------------------------------------------------------------
# Datacenter Validations (mirrors pkg/gtm/datacenter.go)
# ---------------------------------------------------------------------------


def validate_datacenter(datacenter) -> str | None:
    """Validate a Datacenter object.

    Mirrors Go Datacenter.Validate(). In Go, DatacenterID is validated
    with validation.Validate(d.DatacenterID) WITHOUT validation.Required,
    which is effectively a no-op for int types (always passes).

    Args:
        datacenter: A Datacenter object.

    Returns:
        Always None (validation always passes).
    """
    # Go: validation.Validate(d.DatacenterID) without Required — always passes
    _ = datacenter
    errors = {}
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_list_datacenters_request(request) -> str | None:
    """Validate ListDatacentersRequest.

    Mirrors Go ListDatacentersRequest.Validate().
    Required: DomainName.

    Args:
        request: A ListDatacentersRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_get_datacenter_request(request) -> str | None:
    """Validate GetDatacenterRequest.

    Mirrors Go GetDatacenterRequest.Validate().
    Required: DatacenterID, DomainName.

    Args:
        request: A GetDatacenterRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.datacenter_id:
        errors["DatacenterID"] = "cannot be blank"
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_create_datacenter_request(request) -> str | None:
    """Validate CreateDatacenterRequest.

    Mirrors Go CreateDatacenterRequest.Validate().
    Required: DomainName, Datacenter.

    Args:
        request: A CreateDatacenterRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    if request.datacenter is None:
        errors["Datacenter"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_update_datacenter_request(request) -> str | None:
    """Validate UpdateDatacenterRequest.

    Mirrors Go UpdateDatacenterRequest.Validate().
    Required: DomainName, Datacenter.

    Args:
        request: An UpdateDatacenterRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    if request.datacenter is None:
        errors["Datacenter"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_delete_datacenter_request(request) -> str | None:
    """Validate DeleteDatacenterRequest.

    Mirrors Go DeleteDatacenterRequest.Validate().
    Required: DomainName, DatacenterID.

    Args:
        request: A DeleteDatacenterRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    if not request.datacenter_id:
        errors["DatacenterID"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


# ---------------------------------------------------------------------------
# Resource Validations (mirrors pkg/gtm/resource.go)
# ---------------------------------------------------------------------------


def validate_resource(resource) -> str | None:
    """Validate a Resource object.

    Mirrors Go Resource.Validate().
    Required: Name, Type, AggregationType.

    Args:
        resource: A Resource object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not resource.name:
        errors["Name"] = "cannot be blank"
    if not resource.type:
        errors["Type"] = "cannot be blank"
    if not resource.aggregation_type:
        errors["AggregationType"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_list_resources_request(request) -> str | None:
    """Validate ListResourcesRequest.

    Mirrors Go ListResourcesRequest.Validate().
    Required: DomainName.

    Args:
        request: A ListResourcesRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_get_resource_request(request) -> str | None:
    """Validate GetResourceRequest.

    Mirrors Go GetResourceRequest.Validate().
    Required: DomainName, ResourceName.

    Args:
        request: A GetResourceRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    if not request.resource_name:
        errors["ResourceName"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_create_resource_request(request) -> str | None:
    """Validate CreateResourceRequest.

    Mirrors Go CreateResourceRequest.Validate().
    Required: DomainName, Resource.

    Args:
        request: A CreateResourceRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    if request.resource is None:
        errors["Resource"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_update_resource_request(request) -> str | None:
    """Validate UpdateResourceRequest.

    Mirrors Go UpdateResourceRequest.Validate().
    Required: DomainName, Resource.

    Args:
        request: An UpdateResourceRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    if request.resource is None:
        errors["Resource"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_delete_resource_request(request) -> str | None:
    """Validate DeleteResourceRequest.

    Mirrors Go DeleteResourceRequest.Validate().
    Required: DomainName, ResourceName.

    Args:
        request: A DeleteResourceRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    if not request.resource_name:
        errors["ResourceName"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


# ---------------------------------------------------------------------------
# ASMap Validations (mirrors pkg/gtm/asmap.go)
# ---------------------------------------------------------------------------


def validate_as_map(as_map) -> str | None:
    """Validate an ASMap object.

    Mirrors Go ASMap.Validate().
    Required: Name, DefaultDatacenter, Assignments.

    Args:
        as_map: An ASMap object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not as_map.name:
        errors["Name"] = "cannot be blank"
    if as_map.default_datacenter is None:
        errors["DefaultDatacenter"] = "cannot be blank"
    if not as_map.assignments:
        errors["Assignments"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_list_as_maps_request(request) -> str | None:
    """Validate ListASMapsRequest.

    Mirrors Go ListASMapsRequest.Validate().
    Required: DomainName.

    Args:
        request: A ListASMapsRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_get_as_map_request(request) -> str | None:
    """Validate GetASMapRequest.

    Mirrors Go GetASMapRequest.Validate().
    Required: ASMapName, DomainName.

    Args:
        request: A GetASMapRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.as_map_name:
        errors["ASMapName"] = "cannot be blank"
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_create_as_map_request(request) -> str | None:
    """Validate CreateASMapRequest.

    Mirrors Go CreateASMapRequest.Validate().
    Required: DomainName, ASMap.

    Args:
        request: A CreateASMapRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    if request.as_map is None:
        errors["ASMap"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_update_as_map_request(request) -> str | None:
    """Validate UpdateASMapRequest.

    Mirrors Go UpdateASMapRequest.Validate().
    Required: DomainName, ASMap.

    Args:
        request: An UpdateASMapRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    if request.as_map is None:
        errors["ASMap"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_delete_as_map_request(request) -> str | None:
    """Validate DeleteASMapRequest.

    Mirrors Go DeleteASMapRequest.Validate().
    Required: DomainName, ASMapName.

    Args:
        request: A DeleteASMapRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    if not request.as_map_name:
        errors["ASMapName"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


# ---------------------------------------------------------------------------
# GeoMap Validations (mirrors pkg/gtm/geomap.go)
# ---------------------------------------------------------------------------


def validate_geo_map(geo_map) -> str | None:
    """Validate a GeoMap object.

    Mirrors Go GeoMap.Validate().
    Required: Name, DefaultDatacenter.

    Note: Go source validates only Name and DefaultDatacenter for GeoMap
    (no Assignments validation, unlike ASMap).

    Args:
        geo_map: A GeoMap object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not geo_map.name:
        errors["Name"] = "cannot be blank"
    if geo_map.default_datacenter is None:
        errors["DefaultDatacenter"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_list_geo_maps_request(request) -> str | None:
    """Validate ListGeoMapsRequest.

    Mirrors Go ListGeoMapsRequest.Validate().
    Required: DomainName.

    Args:
        request: A ListGeoMapsRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_get_geo_map_request(request) -> str | None:
    """Validate GetGeoMapRequest.

    Mirrors Go GetGeoMapRequest.Validate().
    Required: MapName, DomainName.

    Args:
        request: A GetGeoMapRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.map_name:
        errors["MapName"] = "cannot be blank"
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_create_geo_map_request(request) -> str | None:
    """Validate CreateGeoMapRequest.

    Mirrors Go CreateGeoMapRequest.Validate().
    Required: DomainName, GeoMap.

    Args:
        request: A CreateGeoMapRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    if request.geo_map is None:
        errors["GeoMap"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_update_geo_map_request(request) -> str | None:
    """Validate UpdateGeoMapRequest.

    Mirrors Go UpdateGeoMapRequest.Validate().
    Required: DomainName, GeoMap.

    Args:
        request: An UpdateGeoMapRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    if request.geo_map is None:
        errors["GeoMap"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_delete_geo_map_request(request) -> str | None:
    """Validate DeleteGeoMapRequest.

    Mirrors Go DeleteGeoMapRequest.Validate().
    Required: DomainName, MapName.

    Args:
        request: A DeleteGeoMapRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    if not request.map_name:
        errors["MapName"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


# ---------------------------------------------------------------------------
# CIDRMap Validations (mirrors pkg/gtm/cidrmap.go)
# ---------------------------------------------------------------------------


def validate_cidr_map(cidr_map) -> str | None:
    """Validate a CIDRMap object.

    Mirrors Go CIDRMap.Validate().
    Required: Name.

    Note: Go source validates only Name for CIDRMap (no DefaultDatacenter
    or Assignments validation).

    Args:
        cidr_map: A CIDRMap object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not cidr_map.name:
        errors["Name"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_list_cidr_maps_request(request) -> str | None:
    """Validate ListCIDRMapsRequest.

    Mirrors Go ListCIDRMapsRequest.Validate().
    Required: DomainName.

    Args:
        request: A ListCIDRMapsRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_get_cidr_map_request(request) -> str | None:
    """Validate GetCIDRMapRequest.

    Mirrors Go GetCIDRMapRequest.Validate().
    Required: MapName, DomainName.

    Args:
        request: A GetCIDRMapRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.map_name:
        errors["MapName"] = "cannot be blank"
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_create_cidr_map_request(request) -> str | None:
    """Validate CreateCIDRMapRequest.

    Mirrors Go CreateCIDRMapRequest.Validate().
    Required: DomainName, CIDRMap.

    Args:
        request: A CreateCIDRMapRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    if request.cidr_map is None:
        errors["CIDRMap"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_update_cidr_map_request(request) -> str | None:
    """Validate UpdateCIDRMapRequest.

    Mirrors Go UpdateCIDRMapRequest.Validate().
    Required: DomainName, CIDRMap.

    Args:
        request: An UpdateCIDRMapRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    if request.cidr_map is None:
        errors["CIDRMap"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None


def validate_delete_cidr_map_request(request) -> str | None:
    """Validate DeleteCIDRMapRequest.

    Mirrors Go DeleteCIDRMapRequest.Validate().
    Required: DomainName, MapName.

    Args:
        request: A DeleteCIDRMapRequest object.

    Returns:
        Formatted error string on failure, None when valid.
    """
    errors = {}
    if not request.domain_name:
        errors["DomainName"] = "cannot be blank"
    if not request.map_name:
        errors["MapName"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result is not None:
        return result
    return None
