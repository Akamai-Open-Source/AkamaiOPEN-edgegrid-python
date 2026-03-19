"""Akamai API Definitions client implementation.

Provides the Client class with methods for managing API endpoints, endpoint
versions, activations, and resource operations through the Akamai API
Definitions v2 service.

Mirrors Go ``pkg/apidefinitions``: ``apidefinitions.go`` (interface +
constructor), ``endpoints.go`` (8 endpoint methods), ``endpoint_versions.go``
(5 version methods), ``activations.go`` (3 activation methods), and
``resource_operations.go`` (1 search method).

See: https://techdocs.akamai.com/api-gateway/reference/api
"""

import dataclasses
import logging
from urllib.parse import urlencode

from akamai.edgegrid.session import Session
from akamai.edgegrid.errors import ErrStructValidation
from akamai.edgegrid.apidefinitions import errors
from akamai.edgegrid.apidefinitions import models
from akamai.edgegrid.apidefinitions import validation

logger = logging.getLogger(__name__)


# ======================================================================
# JSON serialisation helpers
# ======================================================================

# Overrides for Python field names whose JSON keys do NOT follow a
# simple ``snake_case → camelCase`` algorithm.
_JSON_KEY_OVERRIDES: dict[str, str] = {
    # "EndPoint" with capital P — Akamai convention
    "api_endpoint_name": "apiEndPointName",
    "api_endpoint_id": "apiEndPointId",
    "api_endpoint_hosts": "apiEndPointHosts",
    "api_endpoint_scheme": "apiEndPointScheme",
    "api_endpoint_port": "apiEndPointPort",
    "api_category_ids": "apiCategoryIds",
    "api_resource_base_info": "apiResourceBaseInfo",
    "api_source_id": "apiSourceId",
    "api_source_name": "apiSourceName",
    "api_resources": "apiResources",
    "api_version_info": "apiVersionInfo",
    "api_child_parameters": "apiChildParameters",
    "api_parameter_id": "apiParameterId",
    "api_parameter_required": "apiParameterRequired",
    "api_parameter_type": "apiParameterType",
    "api_parameter_name": "apiParameterName",
    "api_parameter_location": "apiParameterLocation",
    "api_parameter_notes": "apiParameterNotes",
    "api_parameter_restriction": "apiParameterRestriction",
    "api_endpoint_port_is_default": "apiEndPointPortIsDefault",
    # graphQL casing
    "graphql": "graphQL",
    "is_graphql": "isGraphQL",
    # CamelCase special cases
    "import_file_format": "importFileFormat",
    "import_file_source": "importFileSource",
    "import_file_content": "importFileContent",
    "lock_version": "lockVersion",
    "link_header": "linkHeader",
    "api_resources_url": "apiResourcesUrl",
    # Version / activation
    "version_number": "versionNumber",
    "notification_recipients": "notificationRecipients",
    "version_hidden": "versionHidden",
    "base_path": "basePath",
    "contract_id": "contractId",
    "group_id": "groupId",
    "consume_type": "consumeType",
    "schema_validation_level": "schemaValidationLevel",
    "production_version": "productionVersion",
    "staging_version": "stagingVersion",
}

# AkamaiSecurityRestrictions fields use ALL_CAPS JSON keys.
_UPPERCASE_FIELD_NAMES: frozenset[str] = frozenset({
    "max_body_size",
    "max_element_name_length",
    "max_jsonxml_element",
    "max_doc_depth",
    "max_string_length",
    "max_integer_value",
    "positive_security_enabled",
})


def _snake_to_camel(name: str) -> str:
    """Convert a ``snake_case`` Python name to ``camelCase`` JSON key.

    If the name appears in ``_JSON_KEY_OVERRIDES`` the pre-defined
    mapping takes priority.  Otherwise a standard algorithm is applied:
    split on ``_``, leave the first segment lower-case and capitalise
    the first letter of every subsequent segment.
    """
    override = _JSON_KEY_OVERRIDES.get(name)
    if override is not None:
        return override
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _convert_value(value):
    """Recursively convert *value* to a JSON-serialisable form.

    * Dataclass instances with a ``to_json()`` method (e.g.
      ``RestrictionsBool``) are converted via that method.
    * Other dataclass instances are converted via ``_to_json_body()``.
    * Lists and dicts are converted element-wise.
    * Everything else is returned as-is.
    """
    if hasattr(value, "to_json"):
        return value.to_json()
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return _to_json_body(value)
    if isinstance(value, list):
        return [_convert_value(item) for item in value]
    if isinstance(value, dict):
        return {k: _convert_value(v) for k, v in value.items()}
    return value


def _to_json_body(obj):
    """Convert a dataclass instance to a JSON-serialisable ``dict``.

    Recursively transforms field names from ``snake_case`` to the
    JSON key expected by the Akamai API, omits ``None`` values
    (mirroring Go ``omitempty`` for pointer fields), and delegates
    to ``_convert_value`` for nested structures.

    Args:
        obj: A dataclass instance to serialise.

    Returns:
        A ``dict`` ready for ``json.dumps``.
    """
    if not dataclasses.is_dataclass(obj) or isinstance(obj, type):
        return obj

    is_uppercase_class = type(obj).__name__ == "AkamaiSecurityRestrictions"
    result: dict = {}

    for field in dataclasses.fields(obj):
        value = getattr(obj, field.name)
        if value is None:
            continue

        if is_uppercase_class and field.name in _UPPERCASE_FIELD_NAMES:
            json_key = field.name.upper()
        else:
            json_key = _snake_to_camel(field.name)

        result[json_key] = _convert_value(value)

    return result


def _wrap_error(sentinel: str, err: errors.Error) -> errors.Error:
    """Wrap an API error with a sentinel string prefix.

    Creates a new ``Error`` instance that preserves all fields of the
    original and prepends *sentinel* to the ``title``.  This mirrors
    Go's ``fmt.Errorf("%s: %%w", sentinel, err)`` wrapping pattern.
    """
    return errors.Error(
        type=err.type,
        title=f"{sentinel}: {err.title}" if err.title else sentinel,
        detail=err.detail,
        instance=err.instance,
        status=err.status,
        request_instance=err.request_instance,
        method=err.method,
        request_time=err.request_time,
        behavior_name=err.behavior_name,
        error_location=err.error_location,
        domain_prefix=err.domain_prefix,
        domain_suffix=err.domain_suffix,
        severity=err.severity,
        authz_realm=err.authz_realm,
        server_ip=err.server_ip,
        client_ip=err.client_ip,
        request_id=err.request_id,
        network=err.network,
        version_number=err.version_number,
        endpoint_id=err.endpoint_id,
        endpoint_name=err.endpoint_name,
        errors=err.errors,
    )


# ======================================================================
# Client class
# ======================================================================


class Client:
    """API Definitions client for Akamai API Definitions v2.

    Implements 17 endpoint methods mirroring the Go
    ``pkg/apidefinitions.APIDefinitions`` interface.

    Mirrors Go ``pkg/apidefinitions.apidefinitions`` struct
    with embedded ``session.Session``.

    See: https://techdocs.akamai.com/api-gateway/reference/api
    """

    def __init__(self, session: Session):
        """Initialise the API Definitions client.

        Mirrors Go ``apidefinitions.Client(sess session.Session,
        opts ...Option) APIDefinitions`` at apidefinitions.go:114-123.

        :param session: Authenticated Akamai API session providing
            signed HTTP request execution via EdgeGridAuth.
        """
        self._session = session

    # ------------------------------------------------------------------
    # Endpoint methods (endpoints.go)
    # ------------------------------------------------------------------

    def get_endpoint(
        self, params: models.GetEndpointRequest
    ) -> models.GetEndpointResponse:
        """Return information about an API endpoint."""
        logger.debug("GetEndpoint")

        validation_error = validation.validate_get_endpoint_request(params)
        if validation_error is not None:
            raise ErrStructValidation(
                f"{errors.ErrGetEndpoint}: struct validation: "
                f"{validation_error}"
            )

        uri = f"/api-definitions/v2/endpoints/{params.api_endpoint_id}"

        try:
            _, result = self._session.exec(
                "GET", uri,
                expect_json=True,
                error_parser=errors.Error.from_response,
            )
        except errors.Error as err:
            raise _wrap_error(errors.ErrGetEndpoint, err) from err
        except Exception as err:
            raise errors.Error(
                title=f"{errors.ErrGetEndpoint}: {err}"
            ) from err

        return result

    def register_endpoint(
        self, params: models.RegisterEndpointRequest
    ) -> models.RegisterEndpointResponse:
        """Register a new API endpoint."""
        logger.debug("RegisterEndpoint")

        validation_error = validation.validate_register_endpoint_request(
            params
        )
        if validation_error is not None:
            raise ErrStructValidation(
                f"{errors.ErrRegisterEndpoint}: struct validation: "
                f"{validation_error}"
            )

        uri = "/api-definitions/v2/endpoints"
        body = _to_json_body(params)

        try:
            _, result = self._session.exec(
                "POST", uri,
                body=body,
                expect_json=True,
                error_parser=errors.Error.from_response,
            )
        except errors.Error as err:
            raise _wrap_error(errors.ErrRegisterEndpoint, err) from err
        except Exception as err:
            raise errors.Error(
                title=f"{errors.ErrRegisterEndpoint}: {err}"
            ) from err

        return result

    def register_endpoint_from_file(
        self, params: models.RegisterEndpointFromFileRequest
    ) -> models.RegisterEndpointFromFileResponse:
        """Register an API endpoint from a file spec."""
        logger.debug("RegisterEndpointFromFile")

        validation_error = (
            validation.validate_register_endpoint_from_file_request(params)
        )
        if validation_error is not None:
            raise ErrStructValidation(
                f"{errors.ErrRegisterEndpointFromFile}: struct validation: "
                f"{validation_error}"
            )

        uri = "/api-definitions/v2/endpoints/files"
        body = _to_json_body(params)

        try:
            _, result = self._session.exec(
                "POST", uri,
                body=body,
                expect_json=True,
                error_parser=errors.Error.from_response,
            )
        except errors.Error as err:
            raise _wrap_error(
                errors.ErrRegisterEndpointFromFile, err
            ) from err
        except Exception as err:
            raise errors.Error(
                title=f"{errors.ErrRegisterEndpointFromFile}: {err}"
            ) from err

        return result

    def show_endpoint(
        self, params: models.ShowEndpointRequest
    ) -> models.ShowEndpointResponse:
        """Make an API endpoint visible."""
        logger.debug("ShowEndpoint")

        validation_error = validation.validate_show_endpoint_request(params)
        if validation_error is not None:
            raise ErrStructValidation(
                f"{errors.ErrShowEndpoint}: struct validation: "
                f"{validation_error}"
            )

        uri = (
            f"/api-definitions/v2/endpoints/{params.api_endpoint_id}/show"
        )

        try:
            _, result = self._session.exec(
                "POST", uri,
                expect_json=True,
                error_parser=errors.Error.from_response,
            )
        except errors.Error as err:
            raise _wrap_error(errors.ErrShowEndpoint, err) from err
        except Exception as err:
            raise errors.Error(
                title=f"{errors.ErrShowEndpoint}: {err}"
            ) from err

        return result

    def hide_endpoint(
        self, params: models.HideEndpointRequest
    ) -> models.HideEndpointResponse:
        """Hide an API endpoint from view."""
        logger.debug("HideEndpoint")

        validation_error = validation.validate_hide_endpoint_request(params)
        if validation_error is not None:
            raise ErrStructValidation(
                f"{errors.ErrHideEndpoint}: struct validation: "
                f"{validation_error}"
            )

        uri = (
            f"/api-definitions/v2/endpoints/{params.api_endpoint_id}/hide"
        )

        try:
            _, result = self._session.exec(
                "POST", uri,
                expect_json=True,
                error_parser=errors.Error.from_response,
            )
        except errors.Error as err:
            raise _wrap_error(errors.ErrHideEndpoint, err) from err
        except Exception as err:
            raise errors.Error(
                title=f"{errors.ErrHideEndpoint}: {err}"
            ) from err

        return result

    def delete_endpoint(
        self, params: models.DeleteEndpointRequest
    ) -> None:
        """Delete an API endpoint (204 No Content)."""
        logger.debug("DeleteEndpoint")

        validation_error = validation.validate_delete_endpoint_request(params)
        if validation_error is not None:
            raise ErrStructValidation(
                f"{errors.ErrDeleteEndpoint}: struct validation: "
                f"{validation_error}"
            )

        uri = f"/api-definitions/v2/endpoints/{params.api_endpoint_id}"

        try:
            self._session.exec(
                "DELETE", uri,
                error_parser=errors.Error.from_response,
            )
        except errors.Error as err:
            raise _wrap_error(errors.ErrDeleteEndpoint, err) from err
        except Exception as err:
            raise errors.Error(
                title=f"{errors.ErrDeleteEndpoint}: {err}"
            ) from err

    # pylint: disable=too-many-branches
    def list_endpoints(
        self, params: models.ListEndpointsRequest
    ) -> models.ListEndpointsResponse:
        """List API endpoints matching filter criteria."""
        logger.debug("ListEndpoints")

        validation_error = validation.validate_list_endpoints_request(params)
        if validation_error is not None:
            raise ErrStructValidation(
                f"{errors.ErrListEndpoints}: struct validation: "
                f"{validation_error}"
            )

        # Build query params — mirrors Go endpoints.go:1040-1084
        page = params.page if params.page > 0 else 1
        page_size = params.page_size if params.page_size > 0 else 25
        query: dict[str, str] = {
            "page": str(page),
            "pageSize": str(page_size),
        }
        if params.category:
            query["category"] = params.category
        if params.contains:
            query["contains"] = params.contains
        if params.sort_by:
            query["sortBy"] = params.sort_by
        if params.sort_order:
            query["sortOrder"] = params.sort_order
        if params.version_preference:
            query["versionPreference"] = params.version_preference
        if params.show:
            query["show"] = params.show
        if params.contract_id:
            query["contractId"] = params.contract_id
        if params.group_id:
            query["groupId"] = str(params.group_id)

        uri = f"/api-definitions/v2/endpoints?{urlencode(query)}"

        try:
            _, result = self._session.exec(
                "GET", uri,
                expect_json=True,
                error_parser=errors.Error.from_response,
            )
        except errors.Error as err:
            raise _wrap_error(errors.ErrListEndpoints, err) from err
        except Exception as err:
            raise errors.Error(
                title=f"{errors.ErrListEndpoints}: {err}"
            ) from err

        return result

    def list_user_entitlements(
        self,
    ) -> models.ListUserEntitlementsResponse:
        """List API-category entitlements for the user."""
        logger.debug("ListUserEntitlements")

        uri = "/api-definitions/v2/endpoints/user-entitlements"

        try:
            _, result = self._session.exec(
                "GET", uri,
                expect_json=True,
                error_parser=errors.Error.from_response,
            )
        except errors.Error as err:
            raise _wrap_error(
                errors.ErrListUserEntitlements, err
            ) from err
        except Exception as err:
            raise errors.Error(
                title=f"{errors.ErrListUserEntitlements}: {err}"
            ) from err

        return result

    # ------------------------------------------------------------------
    # Endpoint version methods (endpoint_versions.go)
    # ------------------------------------------------------------------

    def list_endpoint_versions(
        self, params: models.ListEndpointVersionsRequest
    ) -> models.ListEndpointVersionsResponse:
        """List versions for an API endpoint."""
        logger.debug("ListEndpointVersions")

        validation_error = (
            validation.validate_list_endpoint_versions_request(params)
        )
        if validation_error is not None:
            raise ErrStructValidation(
                f"{errors.ErrListEndpointVersions}: struct validation: "
                f"{validation_error}"
            )

        # Build query params — mirrors Go endpoint_versions.go:342-358
        query: dict[str, str] = {}
        if params.page:
            query["page"] = str(params.page)
        if params.page_size:
            query["pageSize"] = str(params.page_size)
        if params.sort_by:
            query["sortBy"] = params.sort_by
        if params.sort_order:
            query["sortOrder"] = params.sort_order
        if params.visibility:
            query["show"] = params.visibility

        base = (
            f"/api-definitions/v2/endpoints/"
            f"{params.api_endpoint_id}/versions"
        )
        if query:
            uri = f"{base}?{urlencode(query)}"
        else:
            uri = base

        try:
            _, result = self._session.exec(
                "GET", uri,
                expect_json=True,
                error_parser=errors.Error.from_response,
            )
        except errors.Error as err:
            raise _wrap_error(
                errors.ErrListEndpointVersions, err
            ) from err
        except Exception as err:
            raise errors.Error(
                title=f"{errors.ErrListEndpointVersions}: {err}"
            ) from err

        return result

    def get_endpoint_version(
        self, params: models.GetEndpointVersionRequest
    ) -> models.GetEndpointVersionResponse:
        """Return detailed info about an endpoint version."""
        logger.debug("GetEndpointVersion")

        validation_error = (
            validation.validate_get_endpoint_version_request(params)
        )
        if validation_error is not None:
            raise ErrStructValidation(
                f"{errors.ErrGetEndpointVersion}: struct validation: "
                f"{validation_error}"
            )

        uri = (
            f"/api-definitions/v2/endpoints/{params.api_endpoint_id}"
            f"/versions/{params.version_number}/resources-detail"
        )

        try:
            _, result = self._session.exec(
                "GET", uri,
                expect_json=True,
                error_parser=errors.Error.from_response,
            )
        except errors.Error as err:
            raise _wrap_error(
                errors.ErrGetEndpointVersion, err
            ) from err
        except Exception as err:
            raise errors.Error(
                title=f"{errors.ErrGetEndpointVersion}: {err}"
            ) from err

        return result

    def update_endpoint_version(
        self, params: models.UpdateEndpointVersionRequest
    ) -> models.UpdateEndpointVersionResponse:
        """Update an endpoint version (sends params.body)."""
        logger.debug("UpdateEndpointVersion")

        validation_error = (
            validation.validate_update_endpoint_version_request(params)
        )
        if validation_error is not None:
            raise ErrStructValidation(
                f"{errors.ErrUpdateEndpointVersion}: struct validation: "
                f"{validation_error}"
            )

        uri = (
            f"/api-definitions/v2/endpoints/{params.api_endpoint_id}"
            f"/versions/{params.version_number}"
        )
        body = _to_json_body(params.body) if params.body is not None else None

        try:
            _, result = self._session.exec(
                "PUT", uri,
                body=body,
                expect_json=True,
                error_parser=errors.Error.from_response,
            )
        except errors.Error as err:
            raise _wrap_error(
                errors.ErrUpdateEndpointVersion, err
            ) from err
        except Exception as err:
            raise errors.Error(
                title=f"{errors.ErrUpdateEndpointVersion}: {err}"
            ) from err

        return result

    def clone_endpoint_version(
        self, params: models.CloneEndpointVersionRequest
    ) -> models.CloneEndpointVersionResponse:
        """Clone an endpoint version."""
        logger.debug("CloneEndpointVersion")

        validation_error = (
            validation.validate_clone_endpoint_version_request(params)
        )
        if validation_error is not None:
            raise ErrStructValidation(
                f"{errors.ErrCloneEndpointVersion}: struct validation: "
                f"{validation_error}"
            )

        uri = (
            f"/api-definitions/v2/endpoints/{params.api_endpoint_id}"
            f"/versions/{params.version_number}/cloneVersion"
        )

        try:
            _, result = self._session.exec(
                "POST", uri,
                expect_json=True,
                error_parser=errors.Error.from_response,
            )
        except errors.Error as err:
            raise _wrap_error(
                errors.ErrCloneEndpointVersion, err
            ) from err
        except Exception as err:
            raise errors.Error(
                title=f"{errors.ErrCloneEndpointVersion}: {err}"
            ) from err

        return result

    def delete_endpoint_version(
        self, params: models.DeleteEndpointVersionRequest
    ) -> None:
        """Delete an endpoint version (204 No Content)."""
        logger.debug("DeleteEndpointVersion")

        validation_error = (
            validation.validate_delete_endpoint_version_request(params)
        )
        if validation_error is not None:
            raise ErrStructValidation(
                f"{errors.ErrDeleteEndpointVersion}: struct validation: "
                f"{validation_error}"
            )

        uri = (
            f"/api-definitions/v2/endpoints/{params.api_endpoint_id}"
            f"/versions/{params.version_number}"
        )

        try:
            self._session.exec(
                "DELETE", uri,
                error_parser=errors.Error.from_response,
            )
        except errors.Error as err:
            raise _wrap_error(
                errors.ErrDeleteEndpointVersion, err
            ) from err
        except Exception as err:
            raise errors.Error(
                title=f"{errors.ErrDeleteEndpointVersion}: {err}"
            ) from err

    # ------------------------------------------------------------------
    # Activation methods (activations.go)
    # ------------------------------------------------------------------

    def activate_version(
        self, params: models.ActivateVersionRequest
    ) -> models.ActivateVersionResponse:
        """Activate an endpoint version."""
        logger.debug("ActivateVersion")

        validation_error = (
            validation.validate_activate_version_request(params)
        )
        if validation_error is not None:
            raise ErrStructValidation(
                f"{errors.ErrActivateVersion}: struct validation: "
                f"{validation_error}"
            )

        uri = (
            f"/api-definitions/v2/endpoints/{params.api_endpoint_id}"
            f"/versions/{params.version_number}/activate"
        )
        body = _to_json_body(params.body) if params.body is not None else None

        try:
            _, result = self._session.exec(
                "POST", uri,
                body=body,
                expect_json=True,
                error_parser=errors.Error.from_response,
            )
        except errors.Error as err:
            raise _wrap_error(errors.ErrActivateVersion, err) from err
        except Exception as err:
            raise errors.Error(
                title=f"{errors.ErrActivateVersion}: {err}"
            ) from err

        return result

    def deactivate_version(
        self, params: models.DeactivateVersionRequest
    ) -> models.DeactivateVersionResponse:
        """Deactivate an endpoint version."""
        logger.debug("DeactivateVersion")

        validation_error = (
            validation.validate_deactivate_version_request(params)
        )
        if validation_error is not None:
            raise ErrStructValidation(
                f"{errors.ErrDeactivateVersion}: struct validation: "
                f"{validation_error}"
            )

        uri = (
            f"/api-definitions/v2/endpoints/{params.api_endpoint_id}"
            f"/versions/{params.version_number}/deactivate"
        )
        body = _to_json_body(params.body) if params.body is not None else None

        try:
            _, result = self._session.exec(
                "POST", uri,
                body=body,
                expect_json=True,
                error_parser=errors.Error.from_response,
            )
        except errors.Error as err:
            raise _wrap_error(
                errors.ErrDeactivateVersion, err
            ) from err
        except Exception as err:
            raise errors.Error(
                title=f"{errors.ErrDeactivateVersion}: {err}"
            ) from err

        return result

    def verify_version(
        self, params: models.VerifyVersionRequest
    ) -> models.VerifyVersionResponse:
        """Verify an endpoint version before activation.

        Returns a list of :class:`~models.VerifyVersionAlert` items
        (type-aliased as *VerifyVersionResponse*).
        """
        logger.debug("VerifyVersion")

        validation_error = (
            validation.validate_verify_version_request(params)
        )
        if validation_error is not None:
            raise ErrStructValidation(
                f"{errors.ErrVerifyVersion}: struct validation: "
                f"{validation_error}"
            )

        uri = (
            f"/api-definitions/v2/endpoints/{params.api_endpoint_id}"
            f"/versions/{params.version_number}/activate/verify"
        )
        body = _to_json_body(params.body) if params.body is not None else None

        try:
            _, result = self._session.exec(
                "POST", uri,
                body=body,
                expect_json=True,
                error_parser=errors.Error.from_response,
            )
        except errors.Error as err:
            raise _wrap_error(errors.ErrVerifyVersion, err) from err
        except Exception as err:
            raise errors.Error(
                title=f"{errors.ErrVerifyVersion}: {err}"
            ) from err

        return result

    # ------------------------------------------------------------------
    # Resource operations (resource_operations.go)
    # ------------------------------------------------------------------

    def search_resource_operations(
        self,
    ) -> models.SearchResourceOperationsResponse:
        """Search available resource operations."""
        logger.debug("SearchResourceOperations")

        uri = "/api-definitions/v2/search-operations"

        try:
            _, result = self._session.exec(
                "GET", uri,
                expect_json=True,
                error_parser=errors.Error.from_response,
            )
        except errors.Error as err:
            raise _wrap_error(
                errors.ErrSearchResourceAndOperations, err
            ) from err
        except Exception as err:
            raise errors.Error(
                title=f"{errors.ErrSearchResourceAndOperations}: {err}"
            ) from err

        return result
