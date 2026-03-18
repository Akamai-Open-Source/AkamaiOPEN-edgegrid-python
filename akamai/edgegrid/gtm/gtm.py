"""Akamai GTM (Global Traffic Management) API client.

Provides the :class:`GTMClient` class with methods for managing GTM
domains, properties, datacenters, resources, AS maps, geographic maps,
and CIDR maps.

Mirrors Go ``pkg/gtm`` — ``gtm.go``, ``domain.go``, ``property.go``,
``datacenter.go``, ``resource.go``, ``asmap.go``, ``geomap.go``,
``cidrmap.go``, ``common.go``, and ``errors.go``.

See: https://techdocs.akamai.com/gtm/reference/api
"""
# pylint: disable=too-many-lines

import json
import logging
import urllib.parse
from typing import Any

from akamai.edgegrid.session import Session
from akamai.edgegrid.errors import ErrStructValidation
from akamai.edgegrid.gtm import models
from akamai.edgegrid.gtm import errors as gtm_errors

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants  (mirrors common.go)
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "1.6"
"""Default GTM schema version.  Mirrors Go ``schemaVersion``."""

MAP_DEFAULT_DC = 5400
"""Default Datacenter ID for Maps.  Mirrors Go ``MapDefaultDC``."""

IPV4_DEFAULT_DC = 5401
"""Default Datacenter ID for IPv4 Selector.  Mirrors Go ``Ipv4DefaultDC``."""

IPV6_DEFAULT_DC = 5402
"""Default Datacenter ID for IPv6 Selector.  Mirrors Go ``Ipv6DefaultDC``."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _version_headers(method: str = "GET") -> dict[str, str]:
    """Build request headers with GTM schema version.

    Mirrors Go ``setVersionHeader`` from ``common.go``.
    Sets the ``Accept`` header unconditionally and additionally sets
    ``Content-Type`` for non-GET methods.

    Args:
        method: HTTP method string (e.g. ``"GET"``, ``"POST"``).

    Returns:
        Dictionary of HTTP headers with schema-versioned media types.
    """
    headers: dict[str, str] = {
        "Accept": f"application/vnd.config-gtm.v{SCHEMA_VERSION}+json",
    }
    if method != "GET":
        headers["Content-Type"] = (
            f"application/vnd.config-gtm.v{SCHEMA_VERSION}+json"
        )
    return headers


def _make_first_char_upper_case(orig_string: str) -> str:
    """Capitalise the first character of *orig_string*.

    Mirrors Go ``makeFirstCharUpperCase`` from ``domain.go``.
    Special-cases ``"cname"`` → ``"CName"`` to match Go behaviour.

    Args:
        orig_string: Input string.

    Returns:
        String with the first character upper-cased.
    """
    if not orig_string:
        return orig_string
    chars = list(orig_string)
    chars[0] = chars[0].upper()
    # Go hack: special-case "cname" → "CName"
    if orig_string == "cname":
        chars[1] = chars[1].upper()
    return "".join(chars)


def _scan_nested_dict_nulls(
    obj_data: dict[str, Any], object_map: dict[str, str]
) -> None:
    """Scan a nested dict for ``None`` values and record them.

    Args:
        obj_data: Nested dict to scan.
        object_map: Target map that receives null-field keys.
    """
    for nested_name, nested_value in obj_data.items():
        if nested_value is None:
            object_map[_make_first_char_upper_case(nested_name)] = ""


def _is_non_primitive_list(obj_data: list[Any]) -> bool:
    """Return ``True`` if *obj_data* is a non-empty list of complex objects."""
    return (
        len(obj_data) > 0
        and not isinstance(obj_data[0], (str, int, float, bool))
    )


def _process_single_object(
    obj: dict[str, Any],
) -> tuple[str, models.NullPerObjectAttributeStruct]:
    """Extract null-field metadata from a single raw JSON object.

    Returns:
        A ``(key, NullPerObjectAttributeStruct)`` tuple where *key* is
        ``datacenterId`` (preferred), ``name``, or ``"unknown"``.
    """
    object_name = ""
    object_dc_id = ""
    object_map: dict[str, str] = {}
    object_child_list: dict[str, Any] = {}

    for obj_field, obj_data in obj.items():
        if obj_data is None:
            object_map[_make_first_char_upper_case(obj_field)] = ""
        elif isinstance(obj_data, dict):
            _scan_nested_dict_nulls(obj_data, object_map)
        elif isinstance(obj_data, list) and _is_non_primitive_list(obj_data):
            object_child_list[
                _make_first_char_upper_case(obj_field)
            ] = _process_object_list(obj_data)
        else:
            if obj_field == "name":
                object_name = str(obj_data)
            if obj_field == "datacenterId":
                object_dc_id = str(obj_data)

    null_fields = models.NullPerObjectAttributeStruct(
        core_object_fields=object_map,
        child_object_fields=object_child_list,
    )

    key = object_dc_id or object_name or "unknown"
    return key, null_fields


def _process_object_list(
    object_list: list[Any],
) -> dict[str, models.NullPerObjectAttributeStruct]:
    """Process a list of raw JSON objects to extract null-field mappings.

    Mirrors Go ``processObjectList`` from ``domain.go`` (lines 634-695).
    Each object in *object_list* is a ``dict`` (JSON object) whose keys
    are inspected for ``None`` values.  Nested dicts are scanned for
    ``None`` values as well, and nested lists of non-primitive elements
    are recursively processed.

    The result is keyed by ``datacenterId`` (preferred), ``name``, or
    ``"unknown"`` — matching Go precedence.

    Args:
        object_list: List of raw JSON-deserialized dicts.

    Returns:
        Mapping of identifier → :class:`~models.NullPerObjectAttributeStruct`.
    """
    null_objects: dict[str, models.NullPerObjectAttributeStruct] = {}

    for obj in object_list:
        if not isinstance(obj, dict):
            continue
        key, null_fields = _process_single_object(obj)
        null_objects[key] = null_fields

    return null_objects


def _build_query_string(query_args: models.DomainQueryArgs | None) -> str:
    """Build a URL query string from optional domain query arguments.

    Args:
        query_args: Optional domain query arguments.

    Returns:
        URL-encoded query string (without leading ``?``), or empty string.
    """
    if query_args is None:
        return ""
    params: dict[str, str] = {}
    if query_args.contract_id:
        params["contractId"] = query_args.contract_id
    if query_args.group_id:
        params["gid"] = query_args.group_id
    if not params:
        return ""
    return urllib.parse.urlencode(params)


# ---------------------------------------------------------------------------
# GTMClient
# ---------------------------------------------------------------------------


class GTMClient:  # pylint: disable=too-many-public-methods
    """Akamai GTM (Global Traffic Management) API client.

    Provides methods for managing GTM domains, properties, datacenters,
    resources, AS maps, geographic maps, and CIDR maps.

    Mirrors Go ``pkg/gtm.GTM`` interface and ``gtm`` struct.

    See: https://techdocs.akamai.com/gtm/reference/api

    Usage::

        >>> from akamai.edgegrid.session import Session
        >>> from akamai.edgegrid.gtm.gtm import GTMClient
        >>> session = Session(edgerc_path="~/.edgerc", section="default")
        >>> client = GTMClient(session)
        >>> domains = client.list_domains()
    """

    def __init__(self, session: Session) -> None:
        """Initialise GTM client.

        Mirrors Go ``gtm.Client()`` constructor.

        Args:
            session: Authenticated Akamai session providing ``exec()``.
        """
        self._session = session

    # ---------------------------------------------------------------
    # Domain methods  (domain.go)
    # ---------------------------------------------------------------

    def null_field_map(
        self, domain: models.Domain
    ) -> models.NullFieldMapStruct:
        """Retrieve a map of null fields for the given domain.

        Fetches the domain as raw JSON (``ObjectMap``) and inspects every
        field for ``None`` values, recursing into nested object lists for
        properties, datacenters, resources, CIDR maps, geographic maps,
        and AS maps.

        Mirrors Go ``(g *gtm) NullFieldMap`` from ``domain.go``.

        Args:
            domain: Domain object (``name`` and ``type`` must be set).

        Returns:
            :class:`~models.NullFieldMapStruct` with null-field metadata.

        Raises:
            ErrStructValidation: If domain validation fails.
        """
        logger.debug("NullFieldMap")

        err = domain.validate()
        if err is not None:
            raise ErrStructValidation(f"domain validation failed. {err}")

        url = f"/config-gtm/v1/domains/{domain.name}"
        headers = _version_headers("GET")

        _, result = self._session.exec(
            "GET", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        # result is the raw ObjectMap (dict[str, Any])
        obj_map: models.ObjectMap = result if result else {}
        null_field_map = models.NullFieldMapStruct()
        domain_map: dict[str, str] = {}

        for key, value in obj_map.items():
            if value is None:
                domain_map[_make_first_char_upper_case(key)] = ""
                continue

            if not isinstance(value, list):
                continue

            if key == "properties":
                null_field_map.properties = _process_object_list(value)
            elif key == "datacenters":
                null_field_map.datacenters = _process_object_list(value)
            elif key == "resources":
                null_field_map.resources = _process_object_list(value)
            elif key == "cidrMaps":
                null_field_map.cidr_maps = _process_object_list(value)
            elif key == "geographicMaps":
                null_field_map.geo_maps = _process_object_list(value)
            elif key == "asMaps":
                null_field_map.as_maps = _process_object_list(value)

        dom_fields = models.NullPerObjectAttributeStruct(
            core_object_fields=domain_map,
            child_object_fields={},
        )
        null_field_map.domain = {domain.name: dom_fields}

        return null_field_map

    def get_domain_status(
        self, params: models.GetDomainStatusRequest
    ) -> models.GetDomainStatusResponse:
        """Retrieve current status for the given domain name.

        Mirrors Go ``GetDomainStatus``.

        See: https://techdocs.akamai.com/gtm/reference/get-status-current

        Args:
            params: Request containing the domain name.

        Returns:
            :class:`~models.GetDomainStatusResponse` (alias for
            :class:`~models.ResponseStatus`).

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("GetDomainStatus")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrGetDomainStatus}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}/status/current"
        )
        headers = _version_headers("GET")

        _, result = self._session.exec(
            "GET", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.ResponseStatus.from_dict(result)

    def list_domains(self) -> list[models.DomainItem]:
        """Retrieve all GTM domains.

        Mirrors Go ``ListDomains``.

        See: https://techdocs.akamai.com/gtm/reference/get-domains

        Returns:
            List of :class:`~models.DomainItem`.

        Raises:
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("ListDomains")

        url = "/config-gtm/v1/domains"
        headers = _version_headers("GET")

        _, result = self._session.exec(
            "GET", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        domains_list = models.DomainsList.from_dict(result)
        return domains_list.domain_items or []

    def get_domain(
        self, params: models.GetDomainRequest
    ) -> models.GetDomainResponse:
        """Retrieve a domain with the given domain name.

        Mirrors Go ``GetDomain``.

        See: https://techdocs.akamai.com/gtm/reference/get-domain

        Args:
            params: Request containing the domain name.

        Returns:
            :class:`~models.GetDomainResponse` (alias for
            :class:`~models.Domain`).

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("GetDomain")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrGetDomain}: struct validation: {err}"
            )

        url = f"/config-gtm/v1/domains/{params.domain_name}"
        headers = _version_headers("GET")

        _, result = self._session.exec(
            "GET", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.Domain.from_dict(result)

    def create_domain(
        self, params: models.CreateDomainRequest
    ) -> models.CreateDomainResponse:
        """Create a new GTM domain.

        Mirrors Go ``CreateDomain``.

        See: https://techdocs.akamai.com/gtm/reference/post-domain

        Args:
            params: Request containing the domain object and optional
                query arguments (``contractId``, ``gid``).

        Returns:
            :class:`~models.CreateDomainResponse` with resource and status.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("CreateDomain")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrCreateDomain}: struct validation: {err}"
            )

        url = "/config-gtm/v1/domains"
        query_string = _build_query_string(params.query_args)
        if query_string:
            url = f"{url}?{query_string}"

        headers = _version_headers("POST")
        body = params.domain.to_dict() if params.domain else None

        _, result = self._session.exec(
            "POST", url,
            body=body,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.CreateDomainResponse.from_dict(result)

    def update_domain(
        self, params: models.UpdateDomainRequest
    ) -> models.UpdateDomainResponse:
        """Update an existing GTM domain.

        Mirrors Go ``UpdateDomain``.

        See: https://techdocs.akamai.com/gtm/reference/put-domain

        Args:
            params: Request containing the domain object and optional
                query arguments (``contractId``, ``gid``).

        Returns:
            :class:`~models.UpdateDomainResponse` with resource and status.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("UpdateDomain")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrUpdateDomain}: struct validation: {err}"
            )

        url = f"/config-gtm/v1/domains/{params.domain.name}"
        query_string = _build_query_string(params.query_args)
        if query_string:
            url = f"{url}?{query_string}"

        headers = _version_headers("PUT")
        body = params.domain.to_dict() if params.domain else None

        _, result = self._session.exec(
            "PUT", url,
            body=body,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.UpdateDomainResponse.from_dict(result)

    def delete_domain(
        self, params: models.DeleteDomainRequest
    ) -> models.DeleteDomainResponse:
        """Delete a GTM domain.

        .. deprecated::
            ``DeleteDomain`` is deprecated and may be removed in future
            versions.

        Mirrors Go ``DeleteDomain``.

        Args:
            params: Request containing the domain name.

        Returns:
            :class:`~models.DeleteDomainResponse`.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("DeleteDomain")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrDeleteDomain}: struct validation: {err}"
            )

        url = f"/config-gtm/v1/domains/{params.domain_name}"
        headers = _version_headers("DELETE")

        _, result = self._session.exec(
            "DELETE", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.DeleteDomainResponse.from_dict(result)

    def delete_domains(
        self, params: models.DeleteDomainsRequest
    ) -> models.DeleteDomainsResponse:
        """Submit a request to delete one or more domains.

        Mirrors Go ``DeleteDomains``.

        Args:
            params: Request containing the domain names to delete and
                optional ``bypass_safety_checks`` flag.

        Returns:
            :class:`~models.DeleteDomainsResponse`.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("DeleteDomains")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrDeleteDomains}: struct validation: {err}"
            )

        url = "/config-gtm/v1/domains/delete-requests"
        query_params: dict[str, str] = {}
        if params.bypass_safety_checks is not None:
            query_params["bypassSafetyChecks"] = json.dumps(
                params.bypass_safety_checks
            )
        if query_params:
            url = f"{url}?{urllib.parse.urlencode(query_params)}"

        headers = _version_headers("POST")
        body = params.body.to_dict() if params.body else None

        _, result = self._session.exec(
            "POST", url,
            body=body,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.DeleteDomainsResponse.from_dict(result)

    def get_delete_domains_status(
        self, params: models.DeleteDomainsStatusRequest
    ) -> models.DeleteDomainsStatusResponse:
        """Retrieve the current status of a bulk domain deletion request.

        Mirrors Go ``GetDeleteDomainsStatus``.

        Args:
            params: Request containing the deletion request ID.

        Returns:
            :class:`~models.DeleteDomainsStatusResponse`.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("GetDeleteDomainsStatus")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrGetDeleteDomainsStatus}: "
                f"struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/delete-requests/{params.request_id}"
        )
        headers = _version_headers("GET")

        _, result = self._session.exec(
            "GET", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.DeleteDomainsStatusResponse.from_dict(result)

    # ---------------------------------------------------------------
    # Property methods  (property.go)
    # ---------------------------------------------------------------

    def list_properties(
        self, params: models.ListPropertiesRequest
    ) -> list[models.Property]:
        """Retrieve all properties for the given domain.

        Mirrors Go ``ListProperties``.

        See: https://techdocs.akamai.com/gtm/reference/get-properties

        Args:
            params: Request containing the domain name.

        Returns:
            List of :class:`~models.Property`.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("ListProperties")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrListProperties}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}/properties"
        )
        headers = _version_headers("GET")

        _, result = self._session.exec(
            "GET", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        prop_list = models.PropertyList.from_dict(result)
        return prop_list.property_items or []

    def get_property(
        self, params: models.GetPropertyRequest
    ) -> models.GetPropertyResponse:
        """Retrieve a property with the given domain and property names.

        Mirrors Go ``GetProperty``.

        See: https://techdocs.akamai.com/gtm/reference/get-property

        Args:
            params: Request containing domain name and property name.

        Returns:
            :class:`~models.GetPropertyResponse` (alias for
            :class:`~models.Property`).

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("GetProperty")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrGetProperty}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/properties/{params.property_name}"
        )
        headers = _version_headers("GET")

        _, result = self._session.exec(
            "GET", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.Property.from_dict(result)

    def create_property(
        self, params: models.CreatePropertyRequest
    ) -> models.CreatePropertyResponse:
        """Create a property in the given domain.

        Mirrors Go ``CreateProperty``.  Uses HTTP PUT (not POST).

        See: https://techdocs.akamai.com/gtm/reference/put-property

        Args:
            params: Request containing domain name and property object.

        Returns:
            :class:`~models.CreatePropertyResponse` with resource and status.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("CreateProperty")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrCreateProperty}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/properties/{params.property.name}"
        )
        headers = _version_headers("PUT")
        body = params.property.to_dict() if params.property else None

        _, result = self._session.exec(
            "PUT", url,
            body=body,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.CreatePropertyResponse.from_dict(result)

    def update_property(
        self, params: models.UpdatePropertyRequest
    ) -> models.UpdatePropertyResponse:
        """Update a property in the given domain.

        Mirrors Go ``UpdateProperty``.

        See: https://techdocs.akamai.com/gtm/reference/put-property

        Args:
            params: Request containing domain name and property object.

        Returns:
            :class:`~models.UpdatePropertyResponse` with resource and status.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("UpdateProperty")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrUpdateProperty}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/properties/{params.property.name}"
        )
        headers = _version_headers("PUT")
        body = params.property.to_dict() if params.property else None

        _, result = self._session.exec(
            "PUT", url,
            body=body,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.UpdatePropertyResponse.from_dict(result)

    def delete_property(
        self, params: models.DeletePropertyRequest
    ) -> models.DeletePropertyResponse:
        """Delete a property from the given domain.

        Mirrors Go ``DeleteProperty``.

        See: https://techdocs.akamai.com/gtm/reference/delete-property

        Args:
            params: Request containing domain name and property name.

        Returns:
            :class:`~models.DeletePropertyResponse` with resource and status.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("DeleteProperty")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrDeleteProperty}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/properties/{params.property_name}"
        )
        headers = _version_headers("DELETE")

        _, result = self._session.exec(
            "DELETE", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.DeletePropertyResponse.from_dict(result)

    # ---------------------------------------------------------------
    # Datacenter methods  (datacenter.go)
    # ---------------------------------------------------------------

    def list_datacenters(
        self, params: models.ListDatacentersRequest
    ) -> list[models.Datacenter]:
        """Retrieve all datacenters for the given domain.

        Mirrors Go ``ListDatacenters``.

        See: https://techdocs.akamai.com/gtm/reference/get-datacenters

        Args:
            params: Request containing the domain name.

        Returns:
            List of :class:`~models.Datacenter`.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("ListDatacenters")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrListDatacenters}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}/datacenters"
        )
        headers = _version_headers("GET")

        _, result = self._session.exec(
            "GET", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        dc_list = models.DatacenterList.from_dict(result)
        return dc_list.datacenter_items or []

    def get_datacenter(
        self, params: models.GetDatacenterRequest
    ) -> models.Datacenter:
        """Retrieve a datacenter with the given ID.

        Mirrors Go ``GetDatacenter``.  Note: datacenter ID is an ``int``.

        See: https://techdocs.akamai.com/gtm/reference/get-datacenter

        Args:
            params: Request containing domain name and datacenter ID.

        Returns:
            :class:`~models.Datacenter`.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("GetDatacenter")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrGetDatacenter}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/datacenters/{params.datacenter_id}"
        )
        headers = _version_headers("GET")

        _, result = self._session.exec(
            "GET", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.Datacenter.from_dict(result)

    def create_datacenter(
        self, params: models.CreateDatacenterRequest
    ) -> models.CreateDatacenterResponse:
        """Create a datacenter in the given domain.

        Mirrors Go ``CreateDatacenter``.

        See: https://techdocs.akamai.com/gtm/reference/post-datacenter

        Args:
            params: Request containing domain name and datacenter object.

        Returns:
            :class:`~models.CreateDatacenterResponse` (alias for
            :class:`~models.DatacenterResponse`).

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("CreateDatacenter")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrCreateDatacenter}: "
                f"struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}/datacenters"
        )
        headers = _version_headers("POST")
        body = params.datacenter.to_dict() if params.datacenter else None

        _, result = self._session.exec(
            "POST", url,
            body=body,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.DatacenterResponse.from_dict(result)

    def update_datacenter(
        self, params: models.UpdateDatacenterRequest
    ) -> models.UpdateDatacenterResponse:
        """Update a datacenter in the given domain.

        Mirrors Go ``UpdateDatacenter``.

        See: https://techdocs.akamai.com/gtm/reference/put-datacenter

        Args:
            params: Request containing domain name and datacenter object.

        Returns:
            :class:`~models.UpdateDatacenterResponse` (alias for
            :class:`~models.DatacenterResponse`).

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("UpdateDatacenter")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrUpdateDatacenter}: "
                f"struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/datacenters/{params.datacenter.datacenter_id}"
        )
        headers = _version_headers("PUT")
        body = params.datacenter.to_dict() if params.datacenter else None

        _, result = self._session.exec(
            "PUT", url,
            body=body,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.DatacenterResponse.from_dict(result)

    def delete_datacenter(
        self, params: models.DeleteDatacenterRequest
    ) -> models.DeleteDatacenterResponse:
        """Delete a datacenter from the given domain.

        Mirrors Go ``DeleteDatacenter``.

        See: https://techdocs.akamai.com/gtm/reference/delete-datacenter

        Args:
            params: Request containing domain name and datacenter ID.

        Returns:
            :class:`~models.DeleteDatacenterResponse` (alias for
            :class:`~models.DatacenterResponse`).

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("DeleteDatacenter")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrDeleteDatacenter}: "
                f"struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/datacenters/{params.datacenter_id}"
        )
        headers = _version_headers("DELETE")

        _, result = self._session.exec(
            "DELETE", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.DatacenterResponse.from_dict(result)

    def create_maps_default_datacenter(
        self, domain_name: str
    ) -> models.Datacenter:
        """Create the default datacenter for maps.

        Mirrors Go ``CreateMapsDefaultDatacenter``.

        Args:
            domain_name: Name of the GTM domain.

        Returns:
            :class:`~models.Datacenter` for the default maps datacenter.
        """
        logger.debug("CreateMapsDefaultDatacenter")
        return self._create_default_dc(MAP_DEFAULT_DC, domain_name)

    def create_ipv4_default_datacenter(
        self, domain_name: str
    ) -> models.Datacenter:
        """Create the default datacenter for IPv4 selector.

        Mirrors Go ``CreateIPv4DefaultDatacenter``.

        Args:
            domain_name: Name of the GTM domain.

        Returns:
            :class:`~models.Datacenter` for the IPv4 default datacenter.
        """
        logger.debug("CreateIPv4DefaultDatacenter")
        return self._create_default_dc(IPV4_DEFAULT_DC, domain_name)

    def create_ipv6_default_datacenter(
        self, domain_name: str
    ) -> models.Datacenter:
        """Create the default datacenter for IPv6 selector.

        Mirrors Go ``CreateIPv6DefaultDatacenter``.

        Args:
            domain_name: Name of the GTM domain.

        Returns:
            :class:`~models.Datacenter` for the IPv6 default datacenter.
        """
        logger.debug("CreateIPv6DefaultDatacenter")
        return self._create_default_dc(IPV6_DEFAULT_DC, domain_name)

    def _create_default_dc(
        self, default_id: int, domain_name: str
    ) -> models.Datacenter:
        """Create a default datacenter identified by *default_id*.

        Mirrors Go ``createDefaultDC`` from ``datacenter.go`` (lines 270-316).

        First attempts to retrieve the datacenter — if it already exists,
        it is returned as-is.  If a 404 Not Found error is received, the
        datacenter is created via POST to the appropriate default URL suffix.

        Args:
            default_id: Default datacenter ID (5400, 5401, or 5402).
            domain_name: Name of the GTM domain.

        Returns:
            :class:`~models.Datacenter`.

        Raises:
            ValueError: If *default_id* is not a valid default DC ID.
            gtm_errors.Error: If the API returns an error other than 404.
        """
        if default_id not in (
            MAP_DEFAULT_DC, IPV4_DEFAULT_DC, IPV6_DEFAULT_DC
        ):
            raise ValueError(
                "invalid default datacenter id provided for creation"
            )

        # Check if default datacenter already exists
        try:
            return self.get_datacenter(
                models.GetDatacenterRequest(
                    datacenter_id=default_id,
                    domain_name=domain_name,
                )
            )
        except gtm_errors.Error as api_error:
            if api_error.status_code != 404:
                raise

        # Build URL suffix for the specific default datacenter type
        base_url = (
            f"/config-gtm/v1/domains/{domain_name}/datacenters/"
        )
        suffix_map = {
            MAP_DEFAULT_DC: "default-datacenter-for-maps",
            IPV4_DEFAULT_DC: "datacenter-for-ip-version-selector-ipv4",
            IPV6_DEFAULT_DC: "datacenter-for-ip-version-selector-ipv6",
        }
        default_url = base_url + suffix_map[default_id]

        headers = _version_headers("POST")

        _, result = self._session.exec(
            "POST", default_url,
            body="",
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        dc_response = models.DatacenterResponse.from_dict(result)
        return dc_response.resource

    # ---------------------------------------------------------------
    # Resource methods  (resource.go)
    # ---------------------------------------------------------------

    def list_resources(
        self, params: models.ListResourcesRequest
    ) -> list[models.Resource]:
        """Retrieve all resources for the given domain.

        Mirrors Go ``ListResources``.

        See: https://techdocs.akamai.com/gtm/reference/get-resources

        Args:
            params: Request containing the domain name.

        Returns:
            List of :class:`~models.Resource`.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("ListResources")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrListResources}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}/resources"
        )
        headers = _version_headers("GET")

        _, result = self._session.exec(
            "GET", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        res_list = models.ResourceList.from_dict(result)
        return res_list.resource_items or []

    def get_resource(
        self, params: models.GetResourceRequest
    ) -> models.GetResourceResponse:
        """Retrieve a resource with the given domain and resource names.

        Mirrors Go ``GetResource``.

        See: https://techdocs.akamai.com/gtm/reference/get-resource

        Args:
            params: Request containing domain name and resource name.

        Returns:
            :class:`~models.GetResourceResponse` (alias for
            :class:`~models.Resource`).

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("GetResource")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrGetResource}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/resources/{params.resource_name}"
        )
        headers = _version_headers("GET")

        _, result = self._session.exec(
            "GET", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.Resource.from_dict(result)

    def create_resource(
        self, params: models.CreateResourceRequest
    ) -> models.CreateResourceResponse:
        """Create a resource in the given domain.

        Mirrors Go ``CreateResource``.  Uses HTTP PUT (not POST).

        See: https://techdocs.akamai.com/gtm/reference/put-resource

        Args:
            params: Request containing domain name and resource object.

        Returns:
            :class:`~models.CreateResourceResponse` (alias for
            :class:`~models.ResourceResponse`).

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("CreateResource")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrCreateResource}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/resources/{params.resource.name}"
        )
        headers = _version_headers("PUT")
        body = params.resource.to_dict() if params.resource else None

        _, result = self._session.exec(
            "PUT", url,
            body=body,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.ResourceResponse.from_dict(result)

    def update_resource(
        self, params: models.UpdateResourceRequest
    ) -> models.UpdateResourceResponse:
        """Update a resource in the given domain.

        Mirrors Go ``UpdateResource``.

        See: https://techdocs.akamai.com/gtm/reference/put-resource

        Args:
            params: Request containing domain name and resource object.

        Returns:
            :class:`~models.UpdateResourceResponse` (alias for
            :class:`~models.ResourceResponse`).

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("UpdateResource")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrUpdateResource}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/resources/{params.resource.name}"
        )
        headers = _version_headers("PUT")
        body = params.resource.to_dict() if params.resource else None

        _, result = self._session.exec(
            "PUT", url,
            body=body,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.ResourceResponse.from_dict(result)

    def delete_resource(
        self, params: models.DeleteResourceRequest
    ) -> models.DeleteResourceResponse:
        """Delete a resource from the given domain.

        Mirrors Go ``DeleteResource``.

        See: https://techdocs.akamai.com/gtm/reference/delete-resource

        Args:
            params: Request containing domain name and resource name.

        Returns:
            :class:`~models.DeleteResourceResponse` (alias for
            :class:`~models.ResourceResponse`).

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("DeleteResource")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrDeleteResource}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/resources/{params.resource_name}"
        )
        headers = _version_headers("DELETE")

        _, result = self._session.exec(
            "DELETE", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.ResourceResponse.from_dict(result)

    # ---------------------------------------------------------------
    # AS Map methods  (asmap.go)
    # ---------------------------------------------------------------

    def list_as_maps(
        self, params: models.ListASMapsRequest
    ) -> list[models.ASMap]:
        """Retrieve all AS maps for the given domain.

        Mirrors Go ``ListASMaps``.

        See: https://techdocs.akamai.com/gtm/reference/get-as-maps

        Args:
            params: Request containing the domain name.

        Returns:
            List of :class:`~models.ASMap`.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("ListASMaps")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrListASMaps}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}/as-maps"
        )
        headers = _version_headers("GET")

        _, result = self._session.exec(
            "GET", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        as_list = models.ASMapList.from_dict(result)
        return as_list.as_map_items or []

    def get_as_map(
        self, params: models.GetASMapRequest
    ) -> models.GetASMapResponse:
        """Retrieve an AS map with the given domain and map names.

        Mirrors Go ``GetASMap``.

        See: https://techdocs.akamai.com/gtm/reference/get-as-map

        Args:
            params: Request containing domain name and AS map name.

        Returns:
            :class:`~models.GetASMapResponse` (alias for
            :class:`~models.ASMap`).

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("GetASMap")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrGetASMap}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/as-maps/{params.map_name}"
        )
        headers = _version_headers("GET")

        _, result = self._session.exec(
            "GET", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.ASMap.from_dict(result)

    def create_as_map(
        self, params: models.CreateASMapRequest
    ) -> models.CreateASMapResponse:
        """Create an AS map in the given domain.

        Mirrors Go ``CreateASMap``.  Uses HTTP PUT (not POST).

        See: https://techdocs.akamai.com/gtm/reference/put-as-map

        Args:
            params: Request containing domain name and AS map object.

        Returns:
            :class:`~models.CreateASMapResponse` with resource and status.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("CreateASMap")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrCreateASMap}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/as-maps/{params.as_map.name}"
        )
        headers = _version_headers("PUT")
        body = params.as_map.to_dict() if params.as_map else None

        _, result = self._session.exec(
            "PUT", url,
            body=body,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.CreateASMapResponse.from_dict(result)

    def update_as_map(
        self, params: models.UpdateASMapRequest
    ) -> models.UpdateASMapResponse:
        """Update an AS map in the given domain.

        Mirrors Go ``UpdateASMap``.

        See: https://techdocs.akamai.com/gtm/reference/put-as-map

        Args:
            params: Request containing domain name and AS map object.

        Returns:
            :class:`~models.UpdateASMapResponse` with resource and status.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("UpdateASMap")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrUpdateASMap}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/as-maps/{params.as_map.name}"
        )
        headers = _version_headers("PUT")
        body = params.as_map.to_dict() if params.as_map else None

        _, result = self._session.exec(
            "PUT", url,
            body=body,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.UpdateASMapResponse.from_dict(result)

    def delete_as_map(
        self, params: models.DeleteASMapRequest
    ) -> models.DeleteASMapResponse:
        """Delete an AS map from the given domain.

        Mirrors Go ``DeleteASMap``.

        See: https://techdocs.akamai.com/gtm/reference/delete-as-map

        Args:
            params: Request containing domain name and AS map name.

        Returns:
            :class:`~models.DeleteASMapResponse` with resource and status.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("DeleteASMap")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrDeleteASMap}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/as-maps/{params.map_name}"
        )
        headers = _version_headers("DELETE")

        _, result = self._session.exec(
            "DELETE", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.DeleteASMapResponse.from_dict(result)

    # ---------------------------------------------------------------
    # Geo Map methods  (geomap.go)
    # ---------------------------------------------------------------

    def list_geo_maps(
        self, params: models.ListGeoMapsRequest
    ) -> list[models.GeoMap]:
        """Retrieve all geographic maps for the given domain.

        Mirrors Go ``ListGeoMaps``.

        See: https://techdocs.akamai.com/gtm/reference/get-geographic-maps

        Args:
            params: Request containing the domain name.

        Returns:
            List of :class:`~models.GeoMap`.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("ListGeoMaps")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrListGeoMaps}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/geographic-maps"
        )
        headers = _version_headers("GET")

        _, result = self._session.exec(
            "GET", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        geo_list = models.GeoMapList.from_dict(result)
        return geo_list.geo_map_items or []

    def get_geo_map(
        self, params: models.GetGeoMapRequest
    ) -> models.GetGeoMapResponse:
        """Retrieve a geographic map with the given domain and map names.

        Mirrors Go ``GetGeoMap``.

        See: https://techdocs.akamai.com/gtm/reference/get-geographic-map

        Args:
            params: Request containing domain name and geo map name.

        Returns:
            :class:`~models.GetGeoMapResponse` (alias for
            :class:`~models.GeoMap`).

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("GetGeoMap")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrGetGeoMap}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/geographic-maps/{params.map_name}"
        )
        headers = _version_headers("GET")

        _, result = self._session.exec(
            "GET", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.GeoMap.from_dict(result)

    def create_geo_map(
        self, params: models.CreateGeoMapRequest
    ) -> models.CreateGeoMapResponse:
        """Create a geographic map in the given domain.

        Mirrors Go ``CreateGeoMap``.  Uses HTTP PUT (not POST).

        See: https://techdocs.akamai.com/gtm/reference/put-geographic-map

        Args:
            params: Request containing domain name and geo map object.

        Returns:
            :class:`~models.CreateGeoMapResponse` with resource and status.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("CreateGeoMap")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrCreateGeoMap}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/geographic-maps/{params.geo_map.name}"
        )
        headers = _version_headers("PUT")
        body = params.geo_map.to_dict() if params.geo_map else None

        _, result = self._session.exec(
            "PUT", url,
            body=body,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.CreateGeoMapResponse.from_dict(result)

    def update_geo_map(
        self, params: models.UpdateGeoMapRequest
    ) -> models.UpdateGeoMapResponse:
        """Update a geographic map in the given domain.

        Mirrors Go ``UpdateGeoMap``.

        See: https://techdocs.akamai.com/gtm/reference/put-geographic-map

        Args:
            params: Request containing domain name and geo map object.

        Returns:
            :class:`~models.UpdateGeoMapResponse` with resource and status.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("UpdateGeoMap")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrUpdateGeoMap}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/geographic-maps/{params.geo_map.name}"
        )
        headers = _version_headers("PUT")
        body = params.geo_map.to_dict() if params.geo_map else None

        _, result = self._session.exec(
            "PUT", url,
            body=body,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.UpdateGeoMapResponse.from_dict(result)

    def delete_geo_map(
        self, params: models.DeleteGeoMapRequest
    ) -> models.DeleteGeoMapResponse:
        """Delete a geographic map from the given domain.

        Mirrors Go ``DeleteGeoMap``.

        See: https://techdocs.akamai.com/gtm/reference/delete-geographic-map

        Args:
            params: Request containing domain name and geo map name.

        Returns:
            :class:`~models.DeleteGeoMapResponse` with resource and status.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("DeleteGeoMap")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrDeleteGeoMap}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/geographic-maps/{params.map_name}"
        )
        headers = _version_headers("DELETE")

        _, result = self._session.exec(
            "DELETE", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.DeleteGeoMapResponse.from_dict(result)

    # ---------------------------------------------------------------
    # CIDR Map methods  (cidrmap.go)
    # ---------------------------------------------------------------

    def list_cidr_maps(
        self, params: models.ListCIDRMapsRequest
    ) -> list[models.CIDRMap]:
        """Retrieve all CIDR maps for the given domain.

        Mirrors Go ``ListCIDRMaps``.

        See: https://techdocs.akamai.com/gtm/reference/get-cidr-maps

        Args:
            params: Request containing the domain name.

        Returns:
            List of :class:`~models.CIDRMap`.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("ListCIDRMaps")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrListCIDRMaps}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}/cidr-maps"
        )
        headers = _version_headers("GET")

        _, result = self._session.exec(
            "GET", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        cidr_list = models.CIDRMapList.from_dict(result)
        return cidr_list.cidr_map_items or []

    def get_cidr_map(
        self, params: models.GetCIDRMapRequest
    ) -> models.GetCIDRMapResponse:
        """Retrieve a CIDR map with the given domain and map names.

        Mirrors Go ``GetCIDRMap``.

        See: https://techdocs.akamai.com/gtm/reference/get-cidr-map

        Args:
            params: Request containing domain name and CIDR map name.

        Returns:
            :class:`~models.GetCIDRMapResponse` (alias for
            :class:`~models.CIDRMap`).

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("GetCIDRMap")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrGetCIDRMap}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/cidr-maps/{params.map_name}"
        )
        headers = _version_headers("GET")

        _, result = self._session.exec(
            "GET", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.CIDRMap.from_dict(result)

    def create_cidr_map(
        self, params: models.CreateCIDRMapRequest
    ) -> models.CreateCIDRMapResponse:
        """Create a CIDR map in the given domain.

        Mirrors Go ``CreateCIDRMap``.  Uses HTTP PUT (not POST).

        See: https://techdocs.akamai.com/gtm/reference/put-cidr-map

        Args:
            params: Request containing domain name and CIDR map object.

        Returns:
            :class:`~models.CreateCIDRMapResponse` with resource and status.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("CreateCIDRMap")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrCreateCIDRMap}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/cidr-maps/{params.cidr_map.name}"
        )
        headers = _version_headers("PUT")
        body = params.cidr_map.to_dict() if params.cidr_map else None

        _, result = self._session.exec(
            "PUT", url,
            body=body,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.CreateCIDRMapResponse.from_dict(result)

    def update_cidr_map(
        self, params: models.UpdateCIDRMapRequest
    ) -> models.UpdateCIDRMapResponse:
        """Update a CIDR map in the given domain.

        Mirrors Go ``UpdateCIDRMap``.

        See: https://techdocs.akamai.com/gtm/reference/put-cidr-map

        Args:
            params: Request containing domain name and CIDR map object.

        Returns:
            :class:`~models.UpdateCIDRMapResponse` with resource and status.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("UpdateCIDRMap")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrUpdateCIDRMap}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/cidr-maps/{params.cidr_map.name}"
        )
        headers = _version_headers("PUT")
        body = params.cidr_map.to_dict() if params.cidr_map else None

        _, result = self._session.exec(
            "PUT", url,
            body=body,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.UpdateCIDRMapResponse.from_dict(result)

    def delete_cidr_map(
        self, params: models.DeleteCIDRMapRequest
    ) -> models.DeleteCIDRMapResponse:
        """Delete a CIDR map from the given domain.

        Mirrors Go ``DeleteCIDRMap``.

        See: https://techdocs.akamai.com/gtm/reference/delete-cidr-map

        Args:
            params: Request containing domain name and CIDR map name.

        Returns:
            :class:`~models.DeleteCIDRMapResponse` with resource and status.

        Raises:
            ErrStructValidation: If request validation fails.
            gtm_errors.Error: If the API returns an error.
        """
        logger.debug("DeleteCIDRMap")

        err = params.validate()
        if err is not None:
            raise ErrStructValidation(
                f"{gtm_errors.ErrDeleteCIDRMap}: struct validation: {err}"
            )

        url = (
            f"/config-gtm/v1/domains/{params.domain_name}"
            f"/cidr-maps/{params.map_name}"
        )
        headers = _version_headers("DELETE")

        _, result = self._session.exec(
            "DELETE", url,
            expect_json=True,
            headers=headers,
            error_parser=gtm_errors.Error.from_response,
        )

        return models.DeleteCIDRMapResponse.from_dict(result)
