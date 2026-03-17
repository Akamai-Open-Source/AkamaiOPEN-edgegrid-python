"""Akamai Cloud Wrapper API client."""

import logging
from urllib.parse import urlencode

from akamai.edgegrid.session import Session
from akamai.edgegrid.cloudwrapper.models import (
    ActivateConfigurationRequest,
    Configuration,
    CreateConfigurationRequest,
    DeleteConfigurationRequest,
    GetConfigurationRequest,
    ListAuthKeysRequest,
    ListAuthKeysResponse,
    ListCapacitiesRequest,
    ListCapacitiesResponse,
    ListCDNProvidersResponse,
    ListConfigurationsResponse,
    ListLocationResponse,
    ListOriginsRequest,
    ListOriginsResponse,
    ListPropertiesRequest,
    ListPropertiesResponse,
    UpdateConfigurationRequest,
)
from akamai.edgegrid.cloudwrapper.errors import (
    Error as CloudWrapperError,
    ErrActivateConfiguration,
    ErrCreateConfiguration,
    ErrDeleteConfiguration,
    ErrGetConfiguration,
    ErrListAuthKeys,
    ErrListCapacities,
    ErrListCDNProviders,
    ErrListConfigurations,
    ErrListLocations,
    ErrListOrigins,
    ErrListProperties,
    ErrStructValidation,
    ErrUpdateConfiguration,
    parse_cloudwrapper_error,
)
from akamai.edgegrid.cloudwrapper.validation import (
    validate_activate_configuration_request,
    validate_create_configuration_request,
    validate_delete_configuration_request,
    validate_get_configuration_request,
    validate_list_auth_keys_request,
    validate_list_origins_request,
    validate_update_configuration_request,
)

logger = logging.getLogger(__name__)


class CloudWrapperClient:
    """Cloud Wrapper API client.

    Provides access to all Cloud Wrapper API operations including
    configurations, capacities, locations, multi-CDN settings, and
    properties.

    Mirrors Go ``pkg/cloudwrapper.CloudWrapper`` interface (12 methods).
    """

    def __init__(self, session: Session):
        """Initialize Cloud Wrapper client with an authenticated session.

        Mirrors Go ``cloudwrapper.Client(sess session.Session)``
        constructor.

        Args:
            session: An authenticated Session instance providing
                EdgeGrid-signed HTTP request execution.
        """
        self._session = session

    # -- Configurations ---------------------------------------------------

    def get_configuration(
        self, params: GetConfigurationRequest,
    ) -> Configuration:
        """Get a specific Cloud Wrapper configuration.

        See: https://techdocs.akamai.com/cloud-wrapper/reference/get-configuration

        Mirrors Go ``cloudwrapper.GetConfiguration``.

        Args:
            params: Request parameters containing config_id.

        Returns:
            The requested Configuration.

        Raises:
            CloudWrapperError: On validation failure or API error.
        """
        logger.debug("GetConfiguration")

        err = validate_get_configuration_request(params)
        if err is not None:
            raise CloudWrapperError(
                title=(
                    f"{ErrGetConfiguration}: "
                    f"{ErrStructValidation}: {err}"
                ),
            )

        uri = (
            f"/cloud-wrapper/v1/configurations/{params.config_id}"
        )

        response, result = self._exec(
            ErrGetConfiguration, "GET", uri, expect_json=True,
        )

        if response.status_code != 200:
            raise self._response_error(
                ErrGetConfiguration, response,
            )

        return Configuration.from_dict(result)

    def list_configurations(self) -> ListConfigurationsResponse:
        """List all Cloud Wrapper configurations on your contract.

        See: https://techdocs.akamai.com/cloud-wrapper/reference/get-configurations

        Mirrors Go ``cloudwrapper.ListConfigurations``.

        Returns:
            Response containing list of configurations.

        Raises:
            CloudWrapperError: On API error.
        """
        logger.debug("ListConfigurations")

        uri = "/cloud-wrapper/v1/configurations"

        response, result = self._exec(
            ErrListConfigurations, "GET", uri, expect_json=True,
        )

        if response.status_code != 200:
            raise self._response_error(
                ErrListConfigurations, response,
            )

        return ListConfigurationsResponse.from_dict(result)

    def create_configuration(
        self, params: CreateConfigurationRequest,
    ) -> Configuration:
        """Create a Cloud Wrapper configuration.

        See: https://techdocs.akamai.com/cloud-wrapper/reference/post-configuration

        Mirrors Go ``cloudwrapper.CreateConfiguration``.

        Args:
            params: Request parameters with activate flag and body.

        Returns:
            The created Configuration.

        Raises:
            CloudWrapperError: On validation failure or API error.
        """
        logger.debug("CreateConfiguration")

        err = validate_create_configuration_request(params)
        if err is not None:
            raise CloudWrapperError(
                title=(
                    f"{ErrCreateConfiguration}: "
                    f"{ErrStructValidation}: {err}"
                ),
            )

        query = urlencode(
            {"activate": str(params.activate).lower()},
        )
        uri = f"/cloud-wrapper/v1/configurations?{query}"

        response, result = self._exec(
            ErrCreateConfiguration, "POST", uri,
            body=params.body.to_dict(), expect_json=True,
        )

        if response.status_code != 201:
            raise self._response_error(
                ErrCreateConfiguration, response,
            )

        return Configuration.from_dict(result)

    def update_configuration(
        self, params: UpdateConfigurationRequest,
    ) -> Configuration:
        """Update a saved or inactive configuration.

        See: https://techdocs.akamai.com/cloud-wrapper/reference/put-configuration

        Mirrors Go ``cloudwrapper.UpdateConfiguration``.

        Args:
            params: Request parameters with config_id, activate flag,
                and body.

        Returns:
            The updated Configuration.

        Raises:
            CloudWrapperError: On validation failure or API error.
        """
        logger.debug("UpdateConfiguration")

        err = validate_update_configuration_request(params)
        if err is not None:
            raise CloudWrapperError(
                title=(
                    f"{ErrUpdateConfiguration}: "
                    f"{ErrStructValidation}: {err}"
                ),
            )

        query = urlencode(
            {"activate": str(params.activate).lower()},
        )
        uri = (
            f"/cloud-wrapper/v1/configurations"
            f"/{params.config_id}?{query}"
        )

        response, result = self._exec(
            ErrUpdateConfiguration, "PUT", uri,
            body=params.body.to_dict(), expect_json=True,
        )

        if response.status_code != 200:
            raise self._response_error(
                ErrUpdateConfiguration, response,
            )

        return Configuration.from_dict(result)

    def delete_configuration(
        self, params: DeleteConfigurationRequest,
    ) -> None:
        """Delete a configuration.

        See: https://techdocs.akamai.com/cloud-wrapper/reference/delete-configuration

        Mirrors Go ``cloudwrapper.DeleteConfiguration``.

        Args:
            params: Request parameters containing config_id.

        Raises:
            CloudWrapperError: On validation failure or API error.
        """
        logger.debug("DeleteConfiguration")

        err = validate_delete_configuration_request(params)
        if err is not None:
            raise CloudWrapperError(
                title=(
                    f"{ErrDeleteConfiguration}: "
                    f"{ErrStructValidation}: {err}"
                ),
            )

        uri = (
            f"/cloud-wrapper/v1/configurations/{params.config_id}"
        )

        response, _ = self._exec(
            ErrDeleteConfiguration, "DELETE", uri,
        )

        if response.status_code != 202:
            raise self._response_error(
                ErrDeleteConfiguration, response,
            )

    def activate_configuration(
        self, params: ActivateConfigurationRequest,
    ) -> None:
        """Activate a Cloud Wrapper configuration.

        See: https://techdocs.akamai.com/cloud-wrapper/reference/post-configuration-activations

        Mirrors Go ``cloudwrapper.ActivateConfiguration``.

        Args:
            params: Request parameters with configuration IDs.

        Raises:
            CloudWrapperError: On validation failure or API error.
        """
        logger.debug("ActivateConfiguration")

        err = validate_activate_configuration_request(params)
        if err is not None:
            raise CloudWrapperError(
                title=(
                    f"{ErrActivateConfiguration}: "
                    f"{ErrStructValidation}: {err}"
                ),
            )

        uri = "/cloud-wrapper/v1/configurations/activate"

        response, _ = self._exec(
            ErrActivateConfiguration, "POST", uri,
            body=params.to_dict(),
        )

        if response.status_code != 204:
            raise self._response_error(
                ErrActivateConfiguration, response,
            )

    # -- Capacities -------------------------------------------------------

    def list_capacities(
        self, params: ListCapacitiesRequest,
    ) -> ListCapacitiesResponse:
        """Fetch capacities available for given contract IDs.

        If no contract IDs are provided, lists all available capacity
        locations.

        See: https://techdocs.akamai.com/cloud-wrapper/reference/get-capacity-inventory

        Mirrors Go ``cloudwrapper.ListCapacities``.

        Args:
            params: Request parameters with optional contract_ids.

        Returns:
            Response containing list of location capacities.

        Raises:
            CloudWrapperError: On API error.
        """
        logger.debug("ListCapacities")

        query_pairs = [
            ("contractIds", cid)
            for cid in params.contract_ids
        ]

        uri = "/cloud-wrapper/v1/capacity"
        if query_pairs:
            uri = f"{uri}?{urlencode(query_pairs)}"

        response, result = self._exec(
            ErrListCapacities, "GET", uri, expect_json=True,
        )

        if response.status_code != 200:
            raise self._response_error(
                ErrListCapacities, response,
            )

        return ListCapacitiesResponse.from_dict(result)

    # -- Locations --------------------------------------------------------

    def list_locations(self) -> ListLocationResponse:
        """Return list of available Cloud Wrapper locations.

        See: https://techdocs.akamai.com/cloud-wrapper/reference/get-locations

        Mirrors Go ``cloudwrapper.ListLocations``.

        Returns:
            Response containing list of locations.

        Raises:
            CloudWrapperError: On API error.
        """
        logger.debug("ListLocations")

        uri = "/cloud-wrapper/v1/locations"

        response, result = self._exec(
            ErrListLocations, "GET", uri, expect_json=True,
        )

        if response.status_code != 200:
            raise self._response_error(
                ErrListLocations, response,
            )

        return ListLocationResponse.from_dict(result)

    # -- Multi-CDN --------------------------------------------------------

    def list_auth_keys(
        self, params: ListAuthKeysRequest,
    ) -> ListAuthKeysResponse:
        """List CDN auth keys for a contract and CDN code.

        See: https://techdocs.akamai.com/cloud-wrapper/reference/get-auth-keys

        Mirrors Go ``cloudwrapper.ListAuthKeys``.

        Args:
            params: Request parameters with contract_id and cdn_code.

        Returns:
            Response containing list of CDN auth keys.

        Raises:
            CloudWrapperError: On validation failure or API error.
        """
        logger.debug("ListAuthKeys")

        err = validate_list_auth_keys_request(params)
        if err is not None:
            raise CloudWrapperError(
                title=(
                    f"{ErrListAuthKeys}: "
                    f"{ErrStructValidation}: {err}"
                ),
            )

        query = urlencode({
            "cdnCode": params.cdn_code,
            "contractId": params.contract_id,
        })
        uri = f"/cloud-wrapper/v1/multi-cdn/auth-keys?{query}"

        response, result = self._exec(
            ErrListAuthKeys, "GET", uri, expect_json=True,
        )

        if response.status_code != 200:
            raise self._response_error(
                ErrListAuthKeys, response,
            )

        return ListAuthKeysResponse.from_dict(result)

    def list_cdn_providers(self) -> ListCDNProvidersResponse:
        """List CDN providers.

        See: https://techdocs.akamai.com/cloud-wrapper/reference/get-providers

        Mirrors Go ``cloudwrapper.ListCDNProviders``.

        Returns:
            Response containing list of CDN providers.

        Raises:
            CloudWrapperError: On API error.
        """
        logger.debug("ListCDNProviders")

        uri = "/cloud-wrapper/v1/multi-cdn/providers"

        response, result = self._exec(
            ErrListCDNProviders, "GET", uri, expect_json=True,
        )

        if response.status_code != 200:
            raise self._response_error(
                ErrListCDNProviders, response,
            )

        return ListCDNProvidersResponse.from_dict(result)

    # -- Properties -------------------------------------------------------

    def list_properties(
        self, params: ListPropertiesRequest,
    ) -> ListPropertiesResponse:
        """List unused properties.

        See: https://techdocs.akamai.com/cloud-wrapper/reference/get-properties

        Mirrors Go ``cloudwrapper.ListProperties``.

        Args:
            params: Request parameters with unused flag and optional
                contract_ids.

        Returns:
            Response containing list of properties.

        Raises:
            CloudWrapperError: On API error.
        """
        logger.debug("ListProperties")

        # Build query pairs matching Go url.Values ordering
        # (alphabetical key sort via url.Values.Encode())
        query_pairs = [
            ("unused", str(params.unused).lower()),
        ]
        for cid in params.contract_ids:
            query_pairs.append(("contractIds", cid))
        query_pairs.sort(key=lambda x: x[0])

        uri = (
            f"/cloud-wrapper/v1/properties"
            f"?{urlencode(query_pairs)}"
        )

        response, result = self._exec(
            ErrListProperties, "GET", uri, expect_json=True,
        )

        if response.status_code != 200:
            raise self._response_error(
                ErrListProperties, response,
            )

        return ListPropertiesResponse.from_dict(result)

    def list_origins(
        self, params: ListOriginsRequest,
    ) -> ListOriginsResponse:
        """List property origins.

        See: https://techdocs.akamai.com/cloud-wrapper/reference/get-origins

        Mirrors Go ``cloudwrapper.ListOrigins``.

        Args:
            params: Request parameters with property_id, contract_id,
                and group_id.

        Returns:
            Response containing origins with children and defaults.

        Raises:
            CloudWrapperError: On validation failure or API error.
        """
        logger.debug("ListOrigins")

        err = validate_list_origins_request(params)
        if err is not None:
            raise CloudWrapperError(
                title=(
                    f"{ErrListOrigins}: "
                    f"{ErrStructValidation}: {err}"
                ),
            )

        query = urlencode({
            "contractId": params.contract_id,
            "groupId": str(params.group_id),
        })
        uri = (
            f"/cloud-wrapper/v1/properties"
            f"/{params.property_id}/origins?{query}"
        )

        response, result = self._exec(
            ErrListOrigins, "GET", uri, expect_json=True,
        )

        if response.status_code != 200:
            raise self._response_error(
                ErrListOrigins, response,
            )

        return ListOriginsResponse.from_dict(result)

    # -- Private helpers --------------------------------------------------

    def _exec(self, sentinel, method, uri, **kwargs):
        """Execute HTTP request with cloudwrapper error handling.

        Wraps ``Session.exec()`` to provide operation-level error
        wrapping that mirrors Go ``fmt.Errorf`` patterns.

        For HTTP responses with status >= 400, the error is parsed
        using ``parse_cloudwrapper_error`` and wrapped with the
        operation sentinel.  For network or request failures, the
        exception is wrapped similarly.

        Args:
            sentinel: Operation error string
                (e.g., ErrGetConfiguration).
            method: HTTP method (GET, POST, PUT, DELETE).
            uri: Request URI path with query string if applicable.
            **kwargs: Forwarded to ``Session.exec()`` — accepts
                ``body``, ``expect_json``, and ``headers``.

        Returns:
            Tuple of (response, parsed_body_or_None).

        Raises:
            CloudWrapperError: Wrapping any error with sentinel.
        """
        try:
            return self._session.exec(
                method,
                uri,
                error_parser=lambda resp: (
                    self._response_error(sentinel, resp)
                ),
                **kwargs,
            )
        except CloudWrapperError:
            raise
        except Exception as exc:
            raise CloudWrapperError(
                title=f"{sentinel}: request failed: {exc}",
            ) from exc

    @staticmethod
    def _response_error(sentinel, response):
        """Parse API error from response and wrap with sentinel.

        Reads the response body, attempts JSON deserialization into
        a ``CloudWrapperError``, and prefixes the error title with
        the operation sentinel string.

        Mirrors Go pattern::

            fmt.Errorf("%s: %w", sentinel, c.Error(resp))

        Args:
            sentinel: Operation error string.
            response: The HTTP response to parse.

        Returns:
            A CloudWrapperError with sentinel-prefixed title.
        """
        error = parse_cloudwrapper_error(response)
        new_title = (
            f"{sentinel}: {error.title}" if error.title
            else sentinel
        )
        return CloudWrapperError(
            type=error.type,
            title=new_title,
            instance=error.instance,
            status=error.status,
            detail=error.detail,
            errors=error.errors,
            method=error.method,
            server_ip=error.server_ip,
            client_ip=error.client_ip,
            request_id=error.request_id,
            request_time=error.request_time,
        )
