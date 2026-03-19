"""Client Lists API client implementation.

Provides the ``Client`` class with all endpoint methods for the Akamai
Client Lists APIs.  Each public method mirrors the corresponding Go
``ClientLists`` interface method (``pkg/clientlists/clientlists.go``)
with exact endpoint URIs, HTTP methods, expected status codes, request
body serialization, query-parameter encoding, and error handling.

Mirrors Go files:
- ``pkg/clientlists/clientlists.go``  — interface + constructor
- ``pkg/clientlists/client_list.go``  — list CRUD (8 methods)
- ``pkg/clientlists/client_list_activation.go`` — activations (4 methods)
- ``pkg/clientlists/errors.go`` — error parsing pattern
"""

import logging
from urllib.parse import urlencode, quote

from akamai.edgegrid.session import Session
from akamai.edgegrid.clientlists import errors
from akamai.edgegrid.clientlists import models
from akamai.edgegrid.clientlists import validation

logger = logging.getLogger(__name__)


class Client:
    """Client Lists API client.

    Provides access to Akamai Client Lists APIs.
    See: https://techdocs.akamai.com/client-lists/reference/api

    Mirrors Go ``pkg/clientlists.ClientLists`` interface and the
    ``clientlists`` struct.  Exactly 12 public methods corresponding 1-to-1
    with the Go interface.
    """

    def __init__(self, session: Session):
        """Initialize Client Lists API client.

        Mirrors Go ``clientlists.Client()`` constructor.

        :param session: Authenticated Akamai API session.
        """
        self._session = session

    # ------------------------------------------------------------------
    # List CRUD operations (mirrors client_list.go)
    # ------------------------------------------------------------------

    @staticmethod
    def _build_get_lists_query(
        params: models.GetClientListsRequest,
    ) -> list[tuple[str, str]]:
        """Build query-parameter tuples for ``get_client_lists``.

        Repeated keys (``type``, ``sort``) are added individually so
        :func:`urllib.parse.urlencode` produces ``type=IP&type=GEO``
        encoding — matching Go ``url.Values.Add`` behaviour.
        """
        parts: list[tuple[str, str]] = []
        if params.name:
            parts.append(("name", params.name))
        if params.type:
            for list_type in params.type:
                parts.append(("type", list_type))
        if params.search:
            parts.append(("search", params.search))
        if params.include_items:
            parts.append(("includeItems", "true"))
        if params.include_deprecated:
            parts.append(("includeDeprecated", "true"))
        if params.include_network_list:
            parts.append(("includeNetworkList", "true"))
        if params.page is not None:
            parts.append(("page", str(params.page)))
        if params.page_size is not None:
            parts.append(("pageSize", str(params.page_size)))
        if params.sort:
            for sort_key in params.sort:
                parts.append(("sort", sort_key))
        return parts

    def get_client_lists(
        self, params: models.GetClientListsRequest,
    ) -> models.GetClientListsResponse:
        """List all client lists accessible for an authenticated user.

        See: https://techdocs.akamai.com/client-lists/reference/get-lists

        Mirrors Go ``clientlists.GetClientLists``
        (client_list.go lines 183-248).

        :param params: Request parameters with optional filters.
        :returns: Response containing matching client lists.
        :raises errors.ErrStructValidation: If request validation fails.
        :raises errors.Error: If the API returns an error response.
        """
        logger.debug("GetClientLists")

        validation.validate_get_client_lists_request(params.type)

        query_parts = self._build_get_lists_query(params)

        uri = "/client-list/v1/lists"
        if query_parts:
            uri += "?" + urlencode(query_parts)

        response, result = self._session.exec(
            "GET", uri,
            expect_json=True,
            error_parser=errors.parse_error_response,
        )

        if response.status_code != 200:
            raise errors.parse_error_response(response)

        return models.GetClientListsResponse.from_dict(result)

    def get_client_list(
        self, params: models.GetClientListRequest,
    ) -> models.GetClientListResponse:
        """Retrieve client list with a specific list id.

        See: https://techdocs.akamai.com/client-lists/reference/get-list

        Mirrors Go ``clientlists.GetClientList``
        (client_list.go lines 250-286).

        :param params: Request parameters containing list ID.
        :returns: Response with client list details.
        :raises errors.ErrStructValidation: If request validation fails.
        :raises errors.Error: If the API returns an error response.
        """
        logger.debug("GetClientList")

        validation.validate_get_client_list_request(params.list_id)

        uri = f"/client-list/v1/lists/{quote(params.list_id, safe='')}"
        if params.include_items:
            uri += "?" + urlencode([("includeItems", "true")])

        response, result = self._session.exec(
            "GET", uri,
            expect_json=True,
            error_parser=errors.parse_error_response,
        )

        if response.status_code != 200:
            raise errors.parse_error_response(response)

        return models.GetClientListResponse.from_dict(result)

    def create_client_list(
        self, params: models.CreateClientListRequest,
    ) -> models.CreateClientListResponse:
        """Create a new client list.

        See: https://techdocs.akamai.com/client-lists/reference/post-create-list

        Mirrors Go ``clientlists.CreateClientList``
        (client_list.go lines 346-371).

        :param params: Request parameters with list definition.
        :returns: Response with the created client list details.
        :raises errors.ErrStructValidation: If request validation fails.
        :raises errors.Error: If the API returns an error response.
        """
        logger.debug("CreateClientList")

        validation.validate_create_client_list_request(
            params.name, params.type,
        )

        response, result = self._session.exec(
            "POST", "/client-list/v1/lists",
            body=params.to_dict(),
            expect_json=True,
            error_parser=errors.parse_error_response,
        )

        if response.status_code != 201:
            raise errors.parse_error_response(response)

        return models.CreateClientListResponse.from_dict(result)

    def update_client_list(
        self, params: models.UpdateClientListRequest,
    ) -> models.UpdateClientListResponse:
        """Update an existing client list.

        See: https://techdocs.akamai.com/client-lists/reference/put-update-list

        Mirrors Go ``clientlists.UpdateClientList``
        (client_list.go lines 288-315).  Only the embedded
        ``UpdateClientList`` fields (name, notes, tags) are sent as
        the request body — ``ListID`` is used solely in the URL path.

        :param params: Request parameters with list ID and update fields.
        :returns: Response with the updated client list details.
        :raises errors.ErrStructValidation: If request validation fails.
        :raises errors.Error: If the API returns an error response.
        """
        logger.debug("UpdateClientList")

        validation.validate_update_client_list_request(params.list_id)

        uri = f"/client-list/v1/lists/{quote(params.list_id, safe='')}"

        # Send only the UpdateClientList portion (name, notes, tags).
        # Mirrors Go: p.Exec(req, &rval, &params.UpdateClientList)
        body = {
            "name": params.name,
            "notes": params.notes,
            "tags": list(params.tags),
        }

        response, result = self._session.exec(
            "PUT", uri,
            body=body,
            expect_json=True,
            error_parser=errors.parse_error_response,
        )

        if response.status_code != 200:
            raise errors.parse_error_response(response)

        return models.UpdateClientListResponse.from_dict(result)

    def update_client_list_items(
        self, params: models.UpdateClientListItemsRequest,
    ) -> models.UpdateClientListItemsResponse:
        """Update items/entries of an existing client list.

        See: https://techdocs.akamai.com/client-lists/reference/post-update-items

        Mirrors Go ``clientlists.UpdateClientListItems``
        (client_list.go lines 317-344).  Only the embedded
        ``UpdateClientListItems`` fields (append, update, delete) are sent
        as the request body.

        :param params: Request parameters with list ID and item changes.
        :returns: Response with the appended, updated, and deleted items.
        :raises errors.ErrStructValidation: If request validation fails.
        :raises errors.Error: If the API returns an error response.
        """
        logger.debug("UpdateClientListItems")

        validation.validate_update_client_list_items_request(params.list_id)

        uri = (
            f"/client-list/v1/lists/"
            f"{quote(params.list_id, safe='')}/items"
        )

        # Send only the UpdateClientListItems portion.
        # Mirrors Go: p.Exec(req, &rval, &params.UpdateClientListItems)
        body = {
            "append": [item.to_dict() for item in params.append],
            "update": [item.to_dict() for item in params.update],
            "delete": [item.to_dict() for item in params.delete],
        }

        response, result = self._session.exec(
            "POST", uri,
            body=body,
            expect_json=True,
            error_parser=errors.parse_error_response,
        )

        if response.status_code != 200:
            raise errors.parse_error_response(response)

        return models.UpdateClientListItemsResponse.from_dict(result)

    def delete_client_list(
        self, params: models.DeleteClientListRequest,
    ) -> None:
        """Remove a client list.

        See: https://techdocs.akamai.com/client-lists/reference/delete-list

        Mirrors Go ``clientlists.DeleteClientList``
        (client_list.go lines 373-398).  Returns ``None`` on success
        (HTTP 204 No Content).

        :param params: Request parameters containing list ID.
        :raises errors.ErrStructValidation: If request validation fails.
        :raises errors.Error: If the API returns an error response.
        """
        logger.debug("DeleteClientList")

        validation.validate_delete_client_list_request(params.list_id)

        uri = (
            f"/client-list/v1/lists/"
            f"{quote(params.list_id, safe='')}"
        )

        response, _ = self._session.exec(
            "DELETE", uri,
            error_parser=errors.parse_error_response,
        )

        if response.status_code != 204:
            raise errors.parse_error_response(response)

    def translate_usernames(
        self,
        params: models.TranslateUsernamesRequest,
    ) -> models.TranslateUsernamesResponse:
        """Translate usernames into UUIDs.

        Mirrors Go ``clientlists.TranslateUsernames``
        (client_list.go lines 400-425).

        Note: This endpoint uses the ``/appsec/v1/`` path prefix, NOT
        ``/client-list/v1/``.

        :param params: List of username strings to translate.
        :returns: Mapping of username to UUID.
        :raises errors.ErrStructValidation: If request validation fails.
        :raises errors.Error: If the API returns an error response.
        """
        logger.debug("TranslateUsernames")

        validation.validate_translate_usernames_request(list(params))

        response, result = self._session.exec(
            "POST", "/appsec/v1/search/user/external-uuid",
            body=list(params),
            expect_json=True,
            error_parser=errors.parse_error_response,
        )

        if response.status_code != 200:
            raise errors.parse_error_response(response)

        return result

    def get_client_list_items(
        self, params: models.GetClientListItemsRequest,
    ) -> models.GetClientListItemsResponse:
        """Retrieve the items of a specific client list.

        See: https://techdocs.akamai.com/client-lists/reference/get-items

        Mirrors Go ``clientlists.GetClientListItems``
        (client_list.go lines 427-460).

        :param params: Request parameters containing list ID.
        :returns: Response with list items.
        :raises errors.ErrStructValidation: If request validation fails.
        :raises errors.Error: If the API returns an error response.
        """
        logger.debug("GetClientListItems")

        validation.validate_get_client_list_items_request(params.list_id)

        uri = (
            f"/client-list/v1/lists/"
            f"{quote(params.list_id, safe='')}"
            f"/items?showUsernames=true"
        )

        response, result = self._session.exec(
            "GET", uri,
            expect_json=True,
            error_parser=errors.parse_error_response,
        )

        if response.status_code != 200:
            raise errors.parse_error_response(response)

        return models.GetClientListItemsResponse.from_dict(result)

    # ------------------------------------------------------------------
    # Activation operations (mirrors client_list_activation.go)
    # ------------------------------------------------------------------

    def get_activation(
        self, params: models.GetActivationRequest,
    ) -> models.GetActivationResponse:
        """Retrieve details of a specified activation ID.

        See: https://techdocs.akamai.com/client-lists/reference/get-retrieve-activation-status

        Mirrors Go ``clientlists.GetActivation``
        (client_list_activation.go lines 236-264).

        :param params: Request parameters containing activation ID.
        :returns: Response with activation details.
        :raises errors.ErrStructValidation: If request validation fails.
        :raises errors.Error: If the API returns an error response.
        """
        logger.debug("Get Activation")

        validation.validate_get_activation_request(params.activation_id)

        uri = f"/client-list/v1/activations/{params.activation_id}"

        response, result = self._session.exec(
            "GET", uri,
            expect_json=True,
            error_parser=errors.parse_error_response,
        )

        if response.status_code != 200:
            raise errors.parse_error_response(response)

        return models.GetActivationResponse.from_dict(result)

    def get_activation_status(
        self, params: models.GetActivationStatusRequest,
    ) -> models.GetActivationStatusResponse:
        """Retrieve activation status for a client list in a network.

        See: https://techdocs.akamai.com/client-lists/reference/get-activation-status

        Mirrors Go ``clientlists.GetActivationStatus``
        (client_list_activation.go lines 206-234).

        :param params: Request parameters with list ID and network.
        :returns: Response with activation status details.
        :raises errors.ErrStructValidation: If request validation fails.
        :raises errors.Error: If the API returns an error response.
        """
        logger.debug("Get Activation Status")

        validation.validate_get_activation_status_request(
            params.list_id, params.network,
        )

        uri = (
            f"/client-list/v1/lists/"
            f"{quote(params.list_id, safe='')}"
            f"/environments/"
            f"{quote(params.network, safe='')}"
            f"/status"
        )

        response, result = self._session.exec(
            "GET", uri,
            expect_json=True,
            error_parser=errors.parse_error_response,
        )

        if response.status_code != 200:
            raise errors.parse_error_response(response)

        return models.GetActivationStatusResponse.from_dict(result)

    def create_activation(
        self, params: models.CreateActivationRequest,
    ) -> models.CreateActivationResponse:
        """Activate a client list.

        See: https://techdocs.akamai.com/client-lists/reference/post-activate-list

        Mirrors Go ``clientlists.CreateActivation``
        (client_list_activation.go lines 146-174).  Only the embedded
        ``ActivationParams`` fields are sent as the request body — the
        ``ListID`` is used solely in the URL path.

        :param params: Request parameters with list ID and activation
            settings.
        :returns: Response with activation status.
        :raises errors.ErrStructValidation: If request validation fails.
        :raises errors.Error: If the API returns an error response.
        """
        logger.debug("Create Activation")

        validation.validate_create_activation_request(
            params.list_id, params.network,
        )

        uri = (
            f"/client-list/v1/lists/"
            f"{quote(params.list_id, safe='')}"
            f"/activations"
        )

        # Send only ActivationParams portion (not ListID).
        # Mirrors Go: p.Exec(req, &rval, params.ActivationParams)
        body = {
            "action": params.action,
            "comments": params.comments,
            "network": params.network,
            "notificationRecipients": list(
                params.notification_recipients,
            ),
            "siebelTicketId": params.siebel_ticket_id,
        }

        response, result = self._session.exec(
            "POST", uri,
            body=body,
            expect_json=True,
            error_parser=errors.parse_error_response,
        )

        if response.status_code != 200:
            raise errors.parse_error_response(response)

        return models.CreateActivationResponse.from_dict(result)

    def create_deactivation(
        self, params: models.CreateDeactivationRequest,
    ) -> models.CreateDeactivationResponse:
        """Deactivate a client list.

        See: https://techdocs.akamai.com/client-lists/reference/post-activate-list

        Mirrors Go ``clientlists.CreateDeactivation``
        (client_list_activation.go lines 176-204).  Only the embedded
        ``ActivationParams`` fields are sent as the request body.

        :param params: Request parameters with list ID and deactivation
            settings.
        :returns: Response with deactivation status.
        :raises errors.ErrStructValidation: If request validation fails.
        :raises errors.Error: If the API returns an error response.
        """
        logger.debug("Create Deactivation")

        validation.validate_create_deactivation_request(
            params.list_id, params.network,
        )

        uri = (
            f"/client-list/v1/lists/"
            f"{quote(params.list_id, safe='')}"
            f"/activations"
        )

        # Send only ActivationParams portion (not ListID).
        # Mirrors Go: p.Exec(req, &rval, params.ActivationParams)
        body = {
            "action": params.action,
            "comments": params.comments,
            "network": params.network,
            "notificationRecipients": list(
                params.notification_recipients,
            ),
            "siebelTicketId": params.siebel_ticket_id,
        }

        response, result = self._session.exec(
            "POST", uri,
            body=body,
            expect_json=True,
            error_parser=errors.parse_error_response,
        )

        if response.status_code != 200:
            raise errors.parse_error_response(response)

        return models.CreateDeactivationResponse.from_dict(result)
