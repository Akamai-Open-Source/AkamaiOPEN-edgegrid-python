"""Akamai Network Lists API client implementation.

Provides the ``NetworkListsClient`` class for managing Akamai network lists,
activations, descriptions, and subscriptions.

Mirrors Go ``pkg/networklists`` package.
"""

import json
import logging

from akamai.edgegrid.session import Session
from akamai.edgegrid.errors import ErrStructValidation
from akamai.edgegrid.utils import unescape_content
from akamai.edgegrid.networklists.models import (
    CreateActivationsRequest,
    CreateActivationsResponse,
    CreateNetworkListRequest,
    CreateNetworkListResponse,
    GetActivationRequest,
    GetActivationResponse,
    GetActivationsRequest,
    GetActivationsResponse,
    GetNetworkListDescriptionRequest,
    GetNetworkListDescriptionResponse,
    GetNetworkListRequest,
    GetNetworkListResponse,
    GetNetworkListsRequest,
    GetNetworkListsResponse,
    GetNetworkListsResponseListElement,
    GetNetworkListSubscriptionRequest,
    GetNetworkListSubscriptionResponse,
    RemoveActivationsRequest,
    RemoveActivationsResponse,
    RemoveNetworkListRequest,
    RemoveNetworkListResponse,
    RemoveNetworkListSubscriptionRequest,
    RemoveNetworkListSubscriptionResponse,
    UpdateNetworkListDescriptionRequest,
    UpdateNetworkListDescriptionResponse,
    UpdateNetworkListRequest,
    UpdateNetworkListResponse,
    UpdateNetworkListSubscriptionRequest,
    UpdateNetworkListSubscriptionResponse,
    from_dict,
    to_dict,
)
from akamai.edgegrid.networklists.errors import Error
from akamai.edgegrid.networklists.validation import (
    validate_create_network_list_request,
    validate_get_activation_request,
    validate_get_activations_request,
    validate_get_network_list_description_request,
    validate_get_network_list_request,
    validate_remove_network_list_request,
    validate_update_network_list_description_request,
    validate_update_network_list_request,
)

logger = logging.getLogger(__name__)


class NetworkListsClient:
    """Client for the Akamai Network Lists API.

    Provides access to the Akamai Network Lists API for managing network
    lists, activations, descriptions, and subscriptions.

    See: https://techdocs.akamai.com/network-lists/reference/api

    Mirrors Go ``pkg/networklists.NetworkList`` interface.
    """

    def __init__(self, session: Session) -> None:
        """Initialize the Network Lists client.

        Mirrors Go ``Client()`` factory which wraps a ``session.Session``.

        Args:
            session: Authenticated Session instance for making API calls.
        """
        self._session = session

    # ------------------------------------------------------------------
    # Error parsing
    # ------------------------------------------------------------------

    def _parse_error(self, response) -> Error:
        """Parse an HTTP error response into a service-specific Error.

        Reads response body, attempts JSON unmarshal into the Error struct.
        On JSON parse failure the title is set to a specific failure message
        and the detail is set to the unescaped body content.  On body read
        failure the title is ``"Failed to read error body"`` and the detail
        is the error message.

        Mirrors Go ``(p *networklists) Error(r *http.Response) error``.

        Args:
            response: The HTTP response object from which to parse the error.

        Returns:
            An ``Error`` instance populated from the response body.
        """
        error = Error()

        try:
            body = response.text
        except Exception as err:  # pylint: disable=broad-except
            logger.error("reading error response body: %s", err)
            error.status_code = response.status_code
            error.title = "Failed to read error body"
            error.detail = str(err)
            return error

        try:
            data = json.loads(body)
            error.type = data.get("type", "")
            error.title = data.get("title", "")
            error.detail = data.get("detail", "")
            error.instance = data.get("instance", "")
            error.behavior_name = data.get("behaviorName", "")
            error.error_location = data.get("errorLocation", "")
        except (json.JSONDecodeError, ValueError) as err:
            logger.error("could not unmarshal API error: %s", err)
            error.title = (
                "Failed to unmarshal error body. Network Lists API failed. "
                "Check details for more information."
            )
            error.detail = unescape_content(body)

        error.status_code = response.status_code
        return error

    # ------------------------------------------------------------------
    # Activation methods
    # ------------------------------------------------------------------

    def get_activations(
        self, params: GetActivationsRequest,
    ) -> GetActivationsResponse:
        """Get activation status for a network list in an environment.

        ``GET /network-list/v2/network-lists/{uniqueId}/environments/
        {network}/status``

        Mirrors Go ``GetActivations``.

        Args:
            params: Request containing *uniqueId* and *network*.

        Returns:
            Activation status response.

        Raises:
            ErrStructValidation: If required fields are missing.
            Error: If the API returns a non-success status.
        """
        validation_errors = validate_get_activations_request(params)
        if validation_errors:
            raise ErrStructValidation(
                f"get activations: struct validation:\n{validation_errors}"
            )

        uri = (
            f"/network-list/v2/network-lists/{params.unique_id}"
            f"/environments/{params.network}/status"
        )
        _, data = self._session.get(
            uri, expect_json=True, error_parser=self._parse_error,
        )
        return from_dict(GetActivationsResponse, data or {})

    def get_activation(
        self, params: GetActivationRequest,
    ) -> GetActivationResponse:
        """Get details of a specific activation.

        ``GET /network-list/v2/activations/{activationId}``

        Mirrors Go ``GetActivation``.

        Args:
            params: Request containing *activationId*.

        Returns:
            Activation detail response.

        Raises:
            ErrStructValidation: If required fields are missing.
            Error: If the API returns a non-success status.
        """
        validation_errors = validate_get_activation_request(params)
        if validation_errors:
            raise ErrStructValidation(
                f"get activation: struct validation:\n{validation_errors}"
            )

        uri = f"/network-list/v2/activations/{params.activation_id}"
        _, data = self._session.get(
            uri, expect_json=True, error_parser=self._parse_error,
        )
        return from_dict(GetActivationResponse, data or {})

    def create_activations(
        self, params: CreateActivationsRequest,
    ) -> CreateActivationsResponse:
        """Activate a network list in an environment.

        Two-step process mirroring Go ``CreateActivations``:

        1. ``POST /network-list/v2/network-lists/{uniqueId}/environments/
           {network}/activate``
        2. ``GET  /network-list/v2/network-lists/{uniqueId}/environments/
           {network}/status``

        Returns the result of the GET status call, not the POST.

        Args:
            params: Request containing *uniqueId*, *network*, and
                activation details.

        Returns:
            Activation status response from the GET call.

        Raises:
            Error: If the API returns a non-success status.
        """
        body = to_dict(params)

        uri_activate = (
            f"/network-list/v2/network-lists/{params.unique_id}"
            f"/environments/{params.network}/activate"
        )
        self._session.post(
            uri_activate,
            body=body,
            expect_json=True,
            error_parser=self._parse_error,
        )

        uri_status = (
            f"/network-list/v2/network-lists/{params.unique_id}"
            f"/environments/{params.network}/status"
        )
        _, data = self._session.get(
            uri_status, expect_json=True, error_parser=self._parse_error,
        )
        return from_dict(CreateActivationsResponse, data or {})

    def remove_activations(
        self, params: RemoveActivationsRequest,
    ) -> RemoveActivationsResponse:
        """Deactivate a network list in an environment.

        ``POST /network-list/v2/network-lists/{uniqueId}/environments/
        {network}/deactivate``

        Mirrors Go ``RemoveActivations``.  Expects 200 OK or 204 No Content.

        Args:
            params: Request containing *uniqueId*, *network*, and
                deactivation details.

        Returns:
            Deactivation status response.

        Raises:
            Error: If the API returns a non-success status.
        """
        body = to_dict(params)

        uri = (
            f"/network-list/v2/network-lists/{params.unique_id}"
            f"/environments/{params.network}/deactivate"
        )
        _, data = self._session.post(
            uri, body=body, expect_json=True, error_parser=self._parse_error,
        )
        if data is None:
            return RemoveActivationsResponse()
        return from_dict(RemoveActivationsResponse, data)

    # ------------------------------------------------------------------
    # Network list methods
    # ------------------------------------------------------------------

    def get_network_lists(
        self, params: GetNetworkListsRequest,
    ) -> GetNetworkListsResponse:
        """Get all network lists, optionally filtered by name and type.

        ``GET /network-list/v2/network-lists``

        Client-side filtering is applied after receiving the full response:
        items are retained when ``(Name matches OR Name filter is empty)
        AND (Type matches OR Type filter is empty)``.

        Mirrors Go ``GetNetworkLists`` including client-side filtering
        logic (network_list.go lines 325-336).

        Args:
            params: Request with optional *name* and *type* filters.

        Returns:
            Response with matching network lists and links.

        Raises:
            Error: If the API returns a non-success status.
        """
        uri = "/network-list/v2/network-lists"
        _, data = self._session.get(
            uri, expect_json=True, error_parser=self._parse_error,
        )
        result = from_dict(GetNetworkListsResponse, data or {})

        # No filter needed when both name and type are empty.
        if not params.name and not params.type:
            return result

        # Client-side filtering matching Go implementation exactly.
        filtered = GetNetworkListsResponse()
        filtered.links = result.links
        filtered_items: list[GetNetworkListsResponseListElement] = [
            item
            for item in result.network_lists
            if (not params.name or item.name == params.name)
            and (not params.type or item.type == params.type)
        ]
        filtered.network_lists = filtered_items
        return filtered

    def get_network_list(
        self, params: GetNetworkListRequest,
    ) -> GetNetworkListResponse:
        """Get a specific network list by unique ID.

        ``GET /network-list/v2/network-lists/{uniqueId}``

        Mirrors Go ``GetNetworkList``.

        Args:
            params: Request containing *uniqueId*.

        Returns:
            Network list details.

        Raises:
            ErrStructValidation: If required fields are missing.
            Error: If the API returns a non-success status.
        """
        validation_errors = validate_get_network_list_request(params)
        if validation_errors:
            raise ErrStructValidation(
                f"get network list: struct validation:\n{validation_errors}"
            )

        uri = f"/network-list/v2/network-lists/{params.unique_id}"
        _, data = self._session.get(
            uri, expect_json=True, error_parser=self._parse_error,
        )
        return from_dict(GetNetworkListResponse, data or {})

    def create_network_list(
        self, params: CreateNetworkListRequest,
    ) -> CreateNetworkListResponse:
        """Create a new network list.

        ``POST /network-list/v2/network-lists``

        Mirrors Go ``CreateNetworkList``.  Expects 200 OK or 201 Created.

        Args:
            params: Request containing network list details.

        Returns:
            Created network list response.

        Raises:
            ErrStructValidation: If required fields are missing.
            Error: If the API returns a non-success status.
        """
        validation_errors = validate_create_network_list_request(params)
        if validation_errors:
            raise ErrStructValidation(
                "create network list: struct validation:\n"
                f"{validation_errors}"
            )

        body = to_dict(params)
        uri = "/network-list/v2/network-lists"
        _, data = self._session.post(
            uri, body=body, expect_json=True, error_parser=self._parse_error,
        )
        return from_dict(CreateNetworkListResponse, data or {})

    def update_network_list(
        self, params: UpdateNetworkListRequest,
    ) -> UpdateNetworkListResponse:
        """Update an existing network list.

        ``PUT /network-list/v2/network-lists/{uniqueId}``

        Mirrors Go ``UpdateNetworkList``.  Expects 200 OK or 201 Created.

        Args:
            params: Request containing updated network list details.

        Returns:
            Updated network list response.

        Raises:
            ErrStructValidation: If required fields are missing.
            Error: If the API returns a non-success status.
        """
        validation_errors = validate_update_network_list_request(params)
        if validation_errors:
            raise ErrStructValidation(
                "update network list: struct validation:\n"
                f"{validation_errors}"
            )

        body = to_dict(params)
        uri = f"/network-list/v2/network-lists/{params.unique_id}"
        _, data = self._session.put(
            uri, body=body, expect_json=True, error_parser=self._parse_error,
        )
        return from_dict(UpdateNetworkListResponse, data or {})

    def remove_network_list(
        self, params: RemoveNetworkListRequest,
    ) -> RemoveNetworkListResponse:
        """Remove a network list by unique ID.

        ``DELETE /network-list/v2/network-lists/{uniqueId}``

        Mirrors Go ``RemoveNetworkList``.  Expects 200 OK or 204 No Content.

        Args:
            params: Request containing *uniqueId*.

        Returns:
            Removal status response.

        Raises:
            ErrStructValidation: If required fields are missing.
            Error: If the API returns a non-success status.
        """
        validation_errors = validate_remove_network_list_request(params)
        if validation_errors:
            raise ErrStructValidation(
                "remove network list: struct validation:\n"
                f"{validation_errors}"
            )

        uri = f"/network-list/v2/network-lists/{params.unique_id}"
        _, data = self._session.delete(
            uri, expect_json=True, error_parser=self._parse_error,
        )
        if data is None:
            return RemoveNetworkListResponse()
        return from_dict(RemoveNetworkListResponse, data)

    # ------------------------------------------------------------------
    # Description methods
    # ------------------------------------------------------------------

    def get_network_list_description(
        self, params: GetNetworkListDescriptionRequest,
    ) -> GetNetworkListDescriptionResponse:
        """Get the description of a specific network list.

        ``GET /network-list/v2/network-lists/{uniqueId}``

        Mirrors Go ``GetNetworkListDescription``.

        Args:
            params: Request containing *uniqueId*.

        Returns:
            Network list description response.

        Raises:
            ErrStructValidation: If required fields are missing.
            Error: If the API returns a non-success status.
        """
        validation_errors = validate_get_network_list_description_request(
            params,
        )
        if validation_errors:
            raise ErrStructValidation(
                "get network list description: struct validation:\n"
                f"{validation_errors}"
            )

        uri = f"/network-list/v2/network-lists/{params.unique_id}"
        _, data = self._session.get(
            uri, expect_json=True, error_parser=self._parse_error,
        )
        return from_dict(GetNetworkListDescriptionResponse, data or {})

    def update_network_list_description(
        self, params: UpdateNetworkListDescriptionRequest,
    ) -> UpdateNetworkListDescriptionResponse:
        """Update the description of a network list.

        ``PUT /network-list/v2/network-lists/{uniqueId}/details``

        Mirrors Go ``UpdateNetworkListDescription``.  Expects 200, 201,
        or 204.

        Args:
            params: Request containing *uniqueId* and updated description.

        Returns:
            Update confirmation response.

        Raises:
            ErrStructValidation: If required fields are missing.
            Error: If the API returns a non-success status.
        """
        validation_errors = validate_update_network_list_description_request(
            params,
        )
        if validation_errors:
            raise ErrStructValidation(
                "update network list description: struct validation:\n"
                f"{validation_errors}"
            )

        body = to_dict(params)
        uri = f"/network-list/v2/network-lists/{params.unique_id}/details"
        _, data = self._session.put(
            uri, body=body, expect_json=True, error_parser=self._parse_error,
        )
        if data is not None:
            return from_dict(UpdateNetworkListDescriptionResponse, data)
        return UpdateNetworkListDescriptionResponse()

    # ------------------------------------------------------------------
    # Subscription methods
    # ------------------------------------------------------------------

    def get_network_list_subscription(
        self, params: GetNetworkListSubscriptionRequest,
    ) -> GetNetworkListSubscriptionResponse:
        """Get notification subscriptions for network lists.

        ``GET /network-list/v2/notifications/subscriptions``

        Mirrors Go ``GetNetworkListSubscription``.  The *params* argument
        is accepted for interface consistency but is not used (matches Go
        which ignores the ``_`` parameter).

        Args:
            params: Request (not used, accepted for interface consistency).

        Returns:
            Subscription details response.

        Raises:
            Error: If the API returns a non-success status.
        """
        _ = params  # Go ignores this parameter.
        uri = "/network-list/v2/notifications/subscriptions"
        _, data = self._session.get(
            uri, expect_json=True, error_parser=self._parse_error,
        )
        return from_dict(GetNetworkListSubscriptionResponse, data or {})

    def update_network_list_subscription(
        self, params: UpdateNetworkListSubscriptionRequest,
    ) -> UpdateNetworkListSubscriptionResponse:
        """Subscribe to notifications for network lists.

        ``POST /network-list/v2/notifications/subscribe``

        Mirrors Go ``UpdateNetworkListSubscription``.  Expects 200, 201,
        or 204.

        Args:
            params: Request containing *recipients* and *uniqueIds*.

        Returns:
            Subscription update confirmation.

        Raises:
            Error: If the API returns a non-success status.
        """
        body = to_dict(params)
        uri = "/network-list/v2/notifications/subscribe"
        _, data = self._session.post(
            uri, body=body, expect_json=True, error_parser=self._parse_error,
        )
        if data is not None:
            return from_dict(UpdateNetworkListSubscriptionResponse, data)
        return UpdateNetworkListSubscriptionResponse()

    def remove_network_list_subscription(
        self, params: RemoveNetworkListSubscriptionRequest,
    ) -> RemoveNetworkListSubscriptionResponse:
        """Unsubscribe from notifications for network lists.

        ``POST /network-list/v2/notifications/unsubscribe``

        Mirrors Go ``RemoveNetworkListSubscription``.  Expects 200, 201,
        or 204.

        Args:
            params: Request containing *recipients* and *uniqueIds*.

        Returns:
            Unsubscription confirmation.

        Raises:
            Error: If the API returns a non-success status.
        """
        body = to_dict(params)
        uri = "/network-list/v2/notifications/unsubscribe"
        _, data = self._session.post(
            uri, body=body, expect_json=True, error_parser=self._parse_error,
        )
        if data is not None:
            return from_dict(RemoveNetworkListSubscriptionResponse, data)
        return RemoveNetworkListSubscriptionResponse()
