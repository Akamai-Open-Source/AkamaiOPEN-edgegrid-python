"""EdgeWorkers and EdgeKV API client.

Provides access to the Akamai EdgeWorkers and EdgeKV APIs.
Mirrors Go pkg/edgeworkers.Edgeworkers interface with all endpoint methods.
"""
# pylint: disable=too-many-lines

import json
import logging

from akamai.edgegrid.errors import ErrStructValidation
from akamai.edgegrid.session import Session
from akamai.edgegrid.edgeworkers import errors
from akamai.edgegrid.edgeworkers import models
from akamai.edgegrid.edgeworkers import validation

logger = logging.getLogger(__name__)


class Client:  # pylint: disable=too-many-public-methods
    """EdgeWorkers and EdgeKV API client.

    Provides methods for managing EdgeWorkers, EdgeKV namespaces,
    access tokens, items, activations, deactivations, and more.
    Mirrors Go pkg/edgeworkers.Edgeworkers interface.
    """

    def __init__(self, session: Session) -> None:
        """Initialize EdgeWorkers client.

        Args:
            session: Authenticated Akamai API session.
        """
        self._session = session

    @staticmethod
    def _check_validation(sentinel: str, err: str | None) -> None:
        """Raise ErrStructValidation if validation returned an error.

        Args:
            sentinel: Operation-specific sentinel error string.
            err: Validation error string, or None if valid.
        """
        if err:
            raise ErrStructValidation(
                f"{sentinel}: struct validation: {err}"
            )

    # ------------------------------------------------------------------ #
    # Activations
    # ------------------------------------------------------------------ #

    def list_activations(
        self, params: models.ListActivationsRequest
    ) -> models.ListActivationsResponse:
        """List all activations for an EdgeWorker.

        Args:
            params: Request parameters including edge_worker_id and
                optional version filter.

        Returns:
            ListActivationsResponse with activation records.
        """
        logger.debug("ListActivations")
        self._check_validation(
            errors.ErrListActivations,
            validation.validate_list_activations_request(params),
        )

        path = f"/edgeworkers/v1/ids/{params.edge_worker_id}/activations"
        query: dict[str, str] = {}
        if params.version:
            query["version"] = params.version

        resp, result = self._session.exec(
            "GET", path,
            expect_json=True,
            params=query or None,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.ListActivationsResponse.from_dict(result)

    def get_activation(
        self, params: models.GetActivationRequest
    ) -> models.Activation:
        """Get details of a specific activation.

        Args:
            params: Request with edge_worker_id and activation_id.

        Returns:
            Activation details.
        """
        logger.debug("GetActivation")
        self._check_validation(
            errors.ErrGetActivation,
            validation.validate_get_activation_request(params),
        )

        path = (
            f"/edgeworkers/v1/ids/{params.edge_worker_id}"
            f"/activations/{params.activation_id}"
        )

        resp, result = self._session.exec(
            "GET", path,
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.Activation.from_dict(result)

    def activate_version(
        self, params: models.ActivateVersionRequest
    ) -> models.Activation:
        """Activate an EdgeWorker version on a network.

        Args:
            params: Request with edge_worker_id and ActivateVersion body
                containing network, version, and optional note.

        Returns:
            Activation details for the newly created activation.
        """
        logger.debug("ActivateVersion")
        self._check_validation(
            errors.ErrActivateVersion,
            validation.validate_activate_version_request(params),
        )
        if params.activate_version is not None:
            self._check_validation(
                errors.ErrActivateVersion,
                validation.validate_activate_version(
                    params.activate_version
                ),
            )

        path = f"/edgeworkers/v1/ids/{params.edge_worker_id}/activations"

        resp, result = self._session.exec(
            "POST", path,
            body=params.activate_version.to_dict(),
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 201:
            raise errors.parse_edgeworkers_error(resp)

        return models.Activation.from_dict(result)

    def cancel_pending_activation(
        self, params: models.CancelActivationRequest
    ) -> models.Activation:
        """Cancel a pending activation.

        Args:
            params: Request with edge_worker_id and activation_id.

        Returns:
            Updated activation details.
        """
        logger.debug("CancelPendingActivation")
        self._check_validation(
            errors.ErrCancelActivation,
            validation.validate_cancel_activation_request(params),
        )

        path = (
            f"/edgeworkers/v1/ids/{params.edge_worker_id}"
            f"/activations/{params.activation_id}"
        )

        resp, result = self._session.exec(
            "DELETE", path,
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.Activation.from_dict(result)

    # ------------------------------------------------------------------ #
    # Contracts
    # ------------------------------------------------------------------ #

    def list_contracts(self) -> models.ListContractsResponse:
        """List contracts available for EdgeWorkers.

        Returns:
            ListContractsResponse containing contract IDs.
        """
        logger.debug("ListContracts")

        resp, result = self._session.exec(
            "GET", "/edgeworkers/v1/contracts",
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.ListContractsResponse.from_dict(result)

    # ------------------------------------------------------------------ #
    # Deactivations
    # ------------------------------------------------------------------ #

    def list_deactivations(
        self, params: models.ListDeactivationsRequest
    ) -> models.ListDeactivationsResponse:
        """List all deactivations for an EdgeWorker.

        Args:
            params: Request with edge_worker_id and optional version
                filter.

        Returns:
            ListDeactivationsResponse with deactivation records.
        """
        logger.debug("ListDeactivations")
        self._check_validation(
            errors.ErrListDeactivations,
            validation.validate_list_deactivations_request(params),
        )

        path = (
            f"/edgeworkers/v1/ids/{params.edge_worker_id}/deactivations"
        )
        query: dict[str, str] = {}
        if params.version:
            query["version"] = params.version

        resp, result = self._session.exec(
            "GET", path,
            expect_json=True,
            params=query or None,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.ListDeactivationsResponse.from_dict(result)

    def get_deactivation(
        self, params: models.GetDeactivationRequest
    ) -> models.Deactivation:
        """Get details of a specific deactivation.

        Args:
            params: Request with edge_worker_id and deactivation_id.

        Returns:
            Deactivation details.
        """
        logger.debug("GetDeactivation")
        self._check_validation(
            errors.ErrGetDeactivation,
            validation.validate_get_deactivation_request(params),
        )

        path = (
            f"/edgeworkers/v1/ids/{params.edge_worker_id}"
            f"/deactivations/{params.deactivation_id}"
        )

        resp, result = self._session.exec(
            "GET", path,
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.Deactivation.from_dict(result)

    def deactivate_version(
        self, params: models.DeactivateVersionRequest
    ) -> models.Deactivation:
        """Deactivate an EdgeWorker version on a network.

        Args:
            params: Request with edge_worker_id and DeactivateVersion
                body containing network, version, and optional note.

        Returns:
            Deactivation details for the newly created deactivation.
        """
        logger.debug("DeactivateVersion")
        self._check_validation(
            errors.ErrDeactivateVersion,
            validation.validate_deactivate_version_request(params),
        )
        if params.deactivate_version is not None:
            self._check_validation(
                errors.ErrDeactivateVersion,
                validation.validate_deactivate_version(
                    params.deactivate_version
                ),
            )

        path = (
            f"/edgeworkers/v1/ids/{params.edge_worker_id}/deactivations"
        )

        resp, result = self._session.exec(
            "POST", path,
            body=params.deactivate_version.to_dict(),
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 201:
            raise errors.parse_edgeworkers_error(resp)

        return models.Deactivation.from_dict(result)

    # ------------------------------------------------------------------ #
    # EdgeKV Access Tokens
    # ------------------------------------------------------------------ #

    def create_edgekv_access_token(
        self, params: models.CreateEdgeKVAccessTokenRequest
    ) -> models.CreateEdgeKVAccessTokenResponse:
        """Create an EdgeKV access token.

        Args:
            params: Token creation request including name, namespace
                permissions, and expiry.

        Returns:
            CreateEdgeKVAccessTokenResponse with the new token details.
        """
        logger.debug("CreateEdgeKVAccessToken")
        self._check_validation(
            errors.ErrCreateEdgeKVAccessToken,
            validation.validate_create_edgekv_access_token_request(
                params
            ),
        )

        resp, result = self._session.exec(
            "POST", "/edgekv/v1/tokens",
            body=params.to_dict(),
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.CreateEdgeKVAccessTokenResponse.from_dict(result)

    def get_edgekv_access_token(
        self, params: models.GetEdgeKVAccessTokenRequest
    ) -> models.GetEdgeKVAccessTokenResponse:
        """Get details of an EdgeKV access token.

        Args:
            params: Request with token_name.

        Returns:
            Token details.
        """
        logger.debug("GetEdgeKVAccessToken")
        self._check_validation(
            errors.ErrGetEdgeKVAccessToken,
            validation.validate_get_edgekv_access_token_request(params),
        )

        path = f"/edgekv/v1/tokens/{params.token_name}"

        resp, result = self._session.exec(
            "GET", path,
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.GetEdgeKVAccessTokenResponse.from_dict(result)

    def list_edgekv_access_tokens(
        self, params: models.ListEdgeKVAccessTokensRequest
    ) -> models.ListEdgeKVAccessTokensResponse:
        """List all EdgeKV access tokens.

        Args:
            params: Request with include_expired flag.

        Returns:
            ListEdgeKVAccessTokensResponse with all tokens.
        """
        logger.debug("ListEdgeKVAccessTokens")

        query = {
            "includeExpired": str(params.include_expired).lower(),
        }

        resp, result = self._session.exec(
            "GET", "/edgekv/v1/tokens",
            expect_json=True,
            params=query,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.ListEdgeKVAccessTokensResponse.from_dict(result)

    def delete_edgekv_access_token(
        self, params: models.DeleteEdgeKVAccessTokenRequest
    ) -> models.DeleteEdgeKVAccessTokenResponse:
        """Delete an EdgeKV access token.

        Args:
            params: Request with token_name.

        Returns:
            DeleteEdgeKVAccessTokenResponse confirmation.
        """
        logger.debug("DeleteEdgeKVAccessToken")
        self._check_validation(
            errors.ErrDeleteEdgeKVAccessToken,
            validation.validate_delete_edgekv_access_token_request(
                params
            ),
        )

        path = f"/edgekv/v1/tokens/{params.token_name}"

        resp, result = self._session.exec(
            "DELETE", path,
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.DeleteEdgeKVAccessTokenResponse.from_dict(result)

    # ------------------------------------------------------------------ #
    # EdgeKV Groups
    # ------------------------------------------------------------------ #

    def list_groups_within_namespace(
        self, params: models.ListGroupsWithinNamespaceRequest
    ) -> list[str]:
        """List groups within an EdgeKV namespace.

        Args:
            params: Request with network and namespace_id.

        Returns:
            List of group ID strings.
        """
        logger.debug("ListGroupsWithinNamespace")
        self._check_validation(
            errors.ErrListGroupsWithinNamespace,
            validation.validate_list_groups_within_namespace_request(
                params
            ),
        )

        path = (
            f"/edgekv/v1/networks/{params.network}"
            f"/namespaces/{params.namespace_id}/groups"
        )

        resp, result = self._session.exec(
            "GET", path,
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return result if isinstance(result, list) else []

    # ------------------------------------------------------------------ #
    # EdgeKV Initialize
    # ------------------------------------------------------------------ #

    def initialize_edgekv(self) -> models.EdgeKVInitializationStatus:
        """Initialize the EdgeKV database.

        Returns:
            EdgeKVInitializationStatus with initialization state.
        """
        logger.debug("InitializeEdgeKV")

        resp, result = self._session.exec(
            "PUT", "/edgekv/v1/initialize",
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 201:
            raise errors.parse_edgeworkers_error(resp)

        return models.EdgeKVInitializationStatus.from_dict(result)

    def get_edgekv_initialization_status(
        self,
    ) -> models.EdgeKVInitializationStatus:
        """Get EdgeKV initialization status.

        Returns:
            EdgeKVInitializationStatus with current state.
        """
        logger.debug("GetEdgeKVInitializationStatus")

        resp, result = self._session.exec(
            "GET", "/edgekv/v1/initialize",
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.EdgeKVInitializationStatus.from_dict(result)

    # ------------------------------------------------------------------ #
    # EdgeKV Items
    # ------------------------------------------------------------------ #

    def list_items(
        self, params: models.ListItemsRequest
    ) -> list[str]:
        """List items within an EdgeKV namespace group.

        Args:
            params: Request with items_request_params (network,
                namespace_id, group_id).

        Returns:
            List of item key strings.
        """
        logger.debug("ListItems")
        if params.items_request_params is not None:
            self._check_validation(
                errors.ErrListItems,
                validation.validate_items_request_params(
                    params.items_request_params
                ),
            )
        self._check_validation(
            errors.ErrListItems,
            validation.validate_list_items_request(params),
        )

        irp = params.items_request_params
        path = (
            f"/edgekv/v1/networks/{irp.network}"
            f"/namespaces/{irp.namespace_id}"
            f"/groups/{irp.group_id}"
        )

        resp, result = self._session.exec(
            "GET", path,
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return result if isinstance(result, list) else []

    def get_item(self, params: models.GetItemRequest) -> str:
        """Get an item value from EdgeKV.

        Args:
            params: Request with items_request_params and item_id.

        Returns:
            Raw item value as string.
        """
        logger.debug("GetItem")
        if params.items_request_params is not None:
            self._check_validation(
                errors.ErrGetItem,
                validation.validate_items_request_params(
                    params.items_request_params
                ),
            )
        self._check_validation(
            errors.ErrGetItem,
            validation.validate_get_item_request(params),
        )

        irp = params.items_request_params
        path = (
            f"/edgekv/v1/networks/{irp.network}"
            f"/namespaces/{irp.namespace_id}"
            f"/groups/{irp.group_id}"
            f"/items/{params.item_id}"
        )

        resp, _ = self._session.exec(
            "GET", path,
            expect_json=False,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return resp.text

    def upsert_item(
        self, params: models.UpsertItemRequest
    ) -> str:
        """Create or update an item in EdgeKV.

        If item_data is not valid JSON, sends with Content-Type
        text/plain. Otherwise uses application/json.

        Args:
            params: Request with items_request_params, item_id,
                and item_data.

        Returns:
            Raw response text confirming the operation.
        """
        logger.debug("UpsertItem")
        if params.items_request_params is not None:
            self._check_validation(
                errors.ErrUpsertItem,
                validation.validate_items_request_params(
                    params.items_request_params
                ),
            )
        self._check_validation(
            errors.ErrUpsertItem,
            validation.validate_upsert_item_request(params),
        )

        irp = params.items_request_params
        path = (
            f"/edgekv/v1/networks/{irp.network}"
            f"/namespaces/{irp.namespace_id}"
            f"/groups/{irp.group_id}"
            f"/items/{params.item_id}"
        )

        headers: dict[str, str] = {}
        if not validation.is_json(params.item_data):
            headers["Content-Type"] = "text/plain"

        resp, _ = self._session.exec(
            "PUT", path,
            body=params.item_data,
            expect_json=False,
            headers=headers or None,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return resp.text

    def delete_item(self, params: models.DeleteItemRequest) -> str:
        """Delete an item from EdgeKV.

        Args:
            params: Request with items_request_params and item_id.

        Returns:
            Raw response text confirming the deletion.
        """
        logger.debug("DeleteItem")
        if params.items_request_params is not None:
            self._check_validation(
                errors.ErrDeleteItem,
                validation.validate_items_request_params(
                    params.items_request_params
                ),
            )
        self._check_validation(
            errors.ErrDeleteItem,
            validation.validate_delete_item_request(params),
        )

        irp = params.items_request_params
        path = (
            f"/edgekv/v1/networks/{irp.network}"
            f"/namespaces/{irp.namespace_id}"
            f"/groups/{irp.group_id}"
            f"/items/{params.item_id}"
        )

        resp, _ = self._session.exec(
            "DELETE", path,
            expect_json=False,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return resp.text

    # ------------------------------------------------------------------ #
    # EdgeKV Namespaces
    # ------------------------------------------------------------------ #

    def list_edgekv_namespaces(
        self, params: models.ListEdgeKVNamespacesRequest
    ) -> models.ListEdgeKVNamespacesResponse:
        """List EdgeKV namespaces on a network.

        Args:
            params: Request with network and optional details flag.

        Returns:
            ListEdgeKVNamespacesResponse with namespace listings.
        """
        logger.debug("ListEdgeKVNamespaces")
        self._check_validation(
            errors.ErrListEdgeKVNamespace,
            validation.validate_list_edgekv_namespaces_request(params),
        )

        path = (
            f"/edgekv/v1/networks/{params.network}/namespaces"
        )
        query: dict[str, str] = {}
        if params.details:
            query["details"] = "on"

        resp, result = self._session.exec(
            "GET", path,
            expect_json=True,
            params=query or None,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.ListEdgeKVNamespacesResponse.from_dict(result)

    def get_edgekv_namespace(
        self, params: models.GetEdgeKVNamespaceRequest
    ) -> models.GetNamespaceResponse:
        """Get details of an EdgeKV namespace.

        Args:
            params: Request with network and namespace name.

        Returns:
            GetNamespaceResponse with namespace details.
        """
        logger.debug("GetEdgeKVNamespace")
        self._check_validation(
            errors.ErrGetEdgeKVNamespace,
            validation.validate_get_edgekv_namespace_request(params),
        )

        path = (
            f"/edgekv/v1/networks/{params.network}"
            f"/namespaces/{params.name}"
        )

        resp, result = self._session.exec(
            "GET", path,
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.GetNamespaceResponse.from_dict(result)

    def create_edgekv_namespace(
        self, params: models.CreateEdgeKVNamespaceRequest
    ) -> models.Namespace:
        """Create a new EdgeKV namespace.

        Args:
            params: Request with network and namespace configuration
                including name, retention, and group_id.

        Returns:
            Namespace details for the newly created namespace.
        """
        logger.debug("CreateEdgeKVNamespace")
        self._check_validation(
            errors.ErrCreateEdgeKVNamespace,
            validation.validate_create_edgekv_namespace_request(params),
        )

        path = (
            f"/edgekv/v1/networks/{params.network}/namespaces"
        )

        resp, result = self._session.exec(
            "POST", path,
            body=params.namespace_request.to_dict(),
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.Namespace.from_dict(result)

    def update_edgekv_namespace(
        self, params: models.UpdateEdgeKVNamespaceRequest
    ) -> models.UpdateNamespaceResponse:
        """Update an EdgeKV namespace.

        Args:
            params: Request with network, name, and update body.

        Returns:
            UpdateNamespaceResponse with updated namespace details.
        """
        logger.debug("UpdateEdgeKVNamespace")
        self._check_validation(
            errors.ErrUpdateEdgeKVNamespace,
            validation.validate_update_edgekv_namespace_request(params),
        )

        path = (
            f"/edgekv/v1/networks/{params.network}"
            f"/namespaces/{params.update_namespace.name}"
        )

        resp, result = self._session.exec(
            "PUT", path,
            body=params.update_namespace.to_dict(),
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.UpdateNamespaceResponse.from_dict(result)

    def delete_edgekv_namespace(
        self, params: models.DeleteEdgeKVNamespaceRequest
    ) -> models.DeleteEdgeKVNamespacesResponse:
        """Delete an EdgeKV namespace.

        When sync is True, expects 200 OK. When sync is False,
        expects 202 Accepted with optional scheduled delete time.

        Args:
            params: Request with network, name, and sync flag.

        Returns:
            DeleteEdgeKVNamespacesResponse with optional scheduled
            delete time.
        """
        logger.debug("DeleteEdgeKVNamespace")
        self._check_validation(
            errors.ErrDeleteEdgeKVNamespace,
            validation.validate_delete_edgekv_namespace_request(params),
        )

        path = (
            f"/edgekv/v1/networks/{params.network}"
            f"/namespaces/{params.name}"
        )
        query: dict[str, str] = {}
        if params.sync:
            query["sync"] = "true"

        resp, _ = self._session.exec(
            "DELETE", path,
            expect_json=False,
            params=query or None,
            error_parser=errors.parse_edgeworkers_error,
        )
        expected_status = 200 if params.sync else 202
        if resp.status_code != expected_status:
            raise errors.parse_edgeworkers_error(resp)

        if resp.text and resp.text.strip():
            data = json.loads(resp.text)
            return models.DeleteEdgeKVNamespacesResponse.from_dict(data)
        return models.DeleteEdgeKVNamespacesResponse()

    def get_namespace_scheduled_delete_time(
        self, params: models.GetScheduledDeleteTimeRequest
    ) -> models.ScheduledDeleteTimeResponse:
        """Get the scheduled delete time for a namespace.

        Also reads the Retry-After response header.

        Args:
            params: Request with network and namespace name.

        Returns:
            ScheduledDeleteTimeResponse with scheduled time and
            retry_after_header.
        """
        logger.debug("GetNamespaceScheduledDeleteTime")
        self._check_validation(
            errors.ErrGetScheduledDeleteTime,
            validation.validate_get_scheduled_delete_time_request(
                params
            ),
        )

        path = (
            f"/edgekv/v1/networks/{params.network}"
            f"/namespaces/{params.name}/status/scheduled-delete"
        )

        resp, result = self._session.exec(
            "GET", path,
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        sdt_resp = models.ScheduledDeleteTimeResponse.from_dict(result)
        sdt_resp.retry_after_header = resp.headers.get(
            "Retry-After", ""
        )
        return sdt_resp

    def reschedule_namespace_delete(
        self, params: models.RescheduleNamespaceDeleteRequest
    ) -> models.RescheduleNamespaceDeleteResponse:
        """Reschedule a namespace deletion.

        Reads both the response body (ScheduledDeleteTimeResponse)
        and the Retry-After response header.

        Args:
            params: Request with network, name, and body containing
                the new scheduled delete time.

        Returns:
            RescheduleNamespaceDeleteResponse with scheduled delete
            time and retry_after_header.
        """
        logger.debug("RescheduleNamespaceDelete")
        self._check_validation(
            errors.ErrRescheduleNamespaceDelete,
            validation.validate_reschedule_namespace_delete_request(
                params
            ),
        )

        path = (
            f"/edgekv/v1/networks/{params.network}"
            f"/namespaces/{params.name}/status/scheduled-delete"
        )

        resp, result = self._session.exec(
            "PUT", path,
            body=params.body.to_dict(),
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        sdt = None
        if result:
            sdt = models.ScheduledDeleteTimeResponse.from_dict(result)
        return models.RescheduleNamespaceDeleteResponse(
            scheduled_delete_time=sdt,
            retry_after_header=resp.headers.get("Retry-After", ""),
        )

    def cancel_scheduled_namespace_delete(
        self, params: models.CancelScheduledNamespaceDeleteRequest
    ) -> None:
        """Cancel a scheduled namespace deletion.

        Args:
            params: Request with network and namespace name.
        """
        logger.debug("CancelScheduledNamespaceDelete")
        self._check_validation(
            errors.ErrCancelScheduledNamespaceDelete,
            validation.validate_cancel_scheduled_namespace_delete_request(
                params
            ),
        )

        path = (
            f"/edgekv/v1/networks/{params.network}"
            f"/namespaces/{params.name}/status/scheduled-delete"
        )

        resp, _ = self._session.exec(
            "DELETE", path,
            expect_json=False,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 204:
            raise errors.parse_edgeworkers_error(resp)

    # ------------------------------------------------------------------ #
    # EdgeWorker IDs
    # ------------------------------------------------------------------ #

    def get_edge_worker_id(
        self, params: models.GetEdgeWorkerIDRequest
    ) -> models.EdgeWorkerID:
        """Get an EdgeWorker ID.

        Args:
            params: Request with edge_worker_id.

        Returns:
            EdgeWorkerID details.
        """
        logger.debug("GetEdgeWorkerID")
        self._check_validation(
            errors.ErrGetEdgeWorkerID,
            validation.validate_get_edge_worker_id_request(params),
        )

        path = f"/edgeworkers/v1/ids/{params.edge_worker_id}"

        resp, result = self._session.exec(
            "GET", path,
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.EdgeWorkerID.from_dict(result)

    def list_edge_workers_id(
        self, params: models.ListEdgeWorkersIDRequest
    ) -> models.ListEdgeWorkersIDResponse:
        """List EdgeWorker IDs with optional filters.

        Args:
            params: Request with optional group_id and
                resource_tier_id filters.

        Returns:
            ListEdgeWorkersIDResponse with EdgeWorker ID listings.
        """
        logger.debug("ListEdgeWorkersID")

        query: dict[str, str] = {}
        if params.group_id:
            query["groupId"] = str(params.group_id)
        if params.resource_tier_id:
            query["resourceTierId"] = str(params.resource_tier_id)

        resp, result = self._session.exec(
            "GET", "/edgeworkers/v1/ids",
            expect_json=True,
            params=query or None,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.ListEdgeWorkersIDResponse.from_dict(result)

    def create_edge_worker_id(
        self, params: models.CreateEdgeWorkerIDRequest
    ) -> models.EdgeWorkerID:
        """Create a new EdgeWorker ID.

        Args:
            params: Request with name, group_id, and
                resource_tier_id.

        Returns:
            EdgeWorkerID for the newly created EdgeWorker.
        """
        logger.debug("CreateEdgeWorkerID")
        self._check_validation(
            errors.ErrCreateEdgeWorkerID,
            validation.validate_create_edge_worker_id_request(params),
        )

        resp, result = self._session.exec(
            "POST", "/edgeworkers/v1/ids",
            body=params.to_dict(),
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 201:
            raise errors.parse_edgeworkers_error(resp)

        return models.EdgeWorkerID.from_dict(result)

    def update_edge_worker_id(
        self, params: models.UpdateEdgeWorkerIDRequest
    ) -> models.EdgeWorkerID:
        """Update an EdgeWorker ID.

        Args:
            params: Request with edge_worker_id and body containing
                name, group_id, and resource_tier_id.

        Returns:
            Updated EdgeWorkerID details.
        """
        logger.debug("UpdateEdgeWorkerID")
        self._check_validation(
            errors.ErrUpdateEdgeWorkerID,
            validation.validate_update_edge_worker_id_request(params),
        )

        path = f"/edgeworkers/v1/ids/{params.edge_worker_id}"

        resp, result = self._session.exec(
            "PUT", path,
            body=params.body.to_dict(),
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.EdgeWorkerID.from_dict(result)

    def clone_edge_worker_id(
        self, params: models.CloneEdgeWorkerIDRequest
    ) -> models.EdgeWorkerID:
        """Clone an EdgeWorker ID.

        Args:
            params: Request with edge_worker_id and body containing
                the target configuration.

        Returns:
            EdgeWorkerID for the cloned EdgeWorker.
        """
        logger.debug("CloneEdgeWorkerID")
        self._check_validation(
            errors.ErrCloneEdgeWorkerID,
            validation.validate_clone_edge_worker_id_request(params),
        )

        path = f"/edgeworkers/v1/ids/{params.edge_worker_id}/clone"

        resp, result = self._session.exec(
            "POST", path,
            body=params.body.to_dict(),
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.EdgeWorkerID.from_dict(result)

    def delete_edge_worker_id(
        self, params: models.DeleteEdgeWorkerIDRequest
    ) -> None:
        """Delete an EdgeWorker ID.

        Args:
            params: Request with edge_worker_id.
        """
        logger.debug("DeleteEdgeWorkerID")
        self._check_validation(
            errors.ErrDeleteEdgeWorkerID,
            validation.validate_delete_edge_worker_id_request(params),
        )

        path = f"/edgeworkers/v1/ids/{params.edge_worker_id}"

        resp, _ = self._session.exec(
            "DELETE", path,
            expect_json=False,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 204:
            raise errors.parse_edgeworkers_error(resp)

    # ------------------------------------------------------------------ #
    # EdgeWorker Versions
    # ------------------------------------------------------------------ #

    def get_edge_worker_version(
        self, params: models.GetEdgeWorkerVersionRequest
    ) -> models.EdgeWorkerVersion:
        """Get an EdgeWorker version.

        Args:
            params: Request with edge_worker_id and version.

        Returns:
            EdgeWorkerVersion details.
        """
        logger.debug("GetEdgeWorkerVersion")
        self._check_validation(
            errors.ErrGetEdgeWorkerVersion,
            validation.validate_get_edge_worker_version_request(params),
        )

        path = (
            f"/edgeworkers/v1/ids/{params.edge_worker_id}"
            f"/versions/{params.version}"
        )

        resp, result = self._session.exec(
            "GET", path,
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.EdgeWorkerVersion.from_dict(result)

    def list_edge_worker_versions(
        self, params: models.ListEdgeWorkerVersionsRequest
    ) -> models.ListEdgeWorkerVersionsResponse:
        """List versions of an EdgeWorker.

        Args:
            params: Request with edge_worker_id.

        Returns:
            ListEdgeWorkerVersionsResponse with version listings.
        """
        logger.debug("ListEdgeWorkerVersions")
        self._check_validation(
            errors.ErrListEdgeWorkerVersions,
            validation.validate_list_edge_worker_versions_request(
                params
            ),
        )

        path = (
            f"/edgeworkers/v1/ids/{params.edge_worker_id}/versions"
        )

        resp, result = self._session.exec(
            "GET", path,
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.ListEdgeWorkerVersionsResponse.from_dict(result)

    def get_edge_worker_version_content(
        self, params: models.GetEdgeWorkerVersionContentRequest
    ) -> models.Bundle:
        """Get the content bundle for an EdgeWorker version.

        Sets Accept header to application/gzip and returns raw
        bytes wrapped in a Bundle.

        Args:
            params: Request with edge_worker_id and version.

        Returns:
            Bundle containing the raw gzip content bytes.
        """
        logger.debug("GetEdgeWorkerVersionContent")
        self._check_validation(
            errors.ErrGetEdgeWorkerVersionContent,
            validation.validate_get_edge_worker_version_content_request(
                params
            ),
        )

        path = (
            f"/edgeworkers/v1/ids/{params.edge_worker_id}"
            f"/versions/{params.version}/content"
        )

        resp, _ = self._session.exec(
            "GET", path,
            expect_json=False,
            headers={"Accept": "application/gzip"},
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.Bundle(data=resp.content)

    def create_edge_worker_version(
        self, params: models.CreateEdgeWorkerVersionRequest
    ) -> models.EdgeWorkerVersion:
        """Create a new EdgeWorker version by uploading a bundle.

        Sets Content-Type to application/gzip and sends raw
        bundle bytes.

        Args:
            params: Request with edge_worker_id and content_bundle
                bytes.

        Returns:
            EdgeWorkerVersion for the newly created version.
        """
        logger.debug("CreateEdgeWorkerVersion")
        self._check_validation(
            errors.ErrCreateEdgeWorkerVersion,
            validation.validate_create_edge_worker_version_request(
                params
            ),
        )

        path = (
            f"/edgeworkers/v1/ids/{params.edge_worker_id}/versions"
        )

        resp, result = self._session.exec(
            "POST", path,
            body=params.content_bundle,
            expect_json=True,
            headers={"Content-Type": "application/gzip"},
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 201:
            raise errors.parse_edgeworkers_error(resp)

        return models.EdgeWorkerVersion.from_dict(result)

    def delete_edge_worker_version(
        self, params: models.DeleteEdgeWorkerVersionRequest
    ) -> None:
        """Delete an EdgeWorker version.

        Args:
            params: Request with edge_worker_id and version.
        """
        logger.debug("DeleteEdgeWorkerVersion")
        self._check_validation(
            errors.ErrDeleteEdgeWorkerVersion,
            validation.validate_delete_edge_worker_version_request(
                params
            ),
        )

        path = (
            f"/edgeworkers/v1/ids/{params.edge_worker_id}"
            f"/versions/{params.version}"
        )

        resp, _ = self._session.exec(
            "DELETE", path,
            expect_json=False,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 204:
            raise errors.parse_edgeworkers_error(resp)

    # ------------------------------------------------------------------ #
    # Permission Groups
    # ------------------------------------------------------------------ #

    def get_permission_group(
        self, params: models.GetPermissionGroupRequest
    ) -> models.PermissionGroup:
        """Get a permission group.

        Args:
            params: Request with group_id.

        Returns:
            PermissionGroup details.
        """
        logger.debug("GetPermissionGroup")
        self._check_validation(
            errors.ErrGetPermissionGroup,
            validation.validate_get_permission_group_request(params),
        )

        path = f"/edgeworkers/v1/groups/{params.group_id}"

        resp, result = self._session.exec(
            "GET", path,
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.PermissionGroup.from_dict(result)

    def list_permission_groups(
        self,
    ) -> models.ListPermissionGroupsResponse:
        """List all permission groups.

        Returns:
            ListPermissionGroupsResponse with group listings.
        """
        logger.debug("ListPermissionGroups")

        resp, result = self._session.exec(
            "GET", "/edgeworkers/v1/groups",
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.ListPermissionGroupsResponse.from_dict(result)

    # ------------------------------------------------------------------ #
    # Properties
    # ------------------------------------------------------------------ #

    def list_properties(
        self, params: models.ListPropertiesRequest
    ) -> models.ListPropertiesResponse:
        """List properties associated with an EdgeWorker.

        Args:
            params: Request with edge_worker_id and active_only flag.

        Returns:
            ListPropertiesResponse with property listings.
        """
        logger.debug("ListProperties")
        self._check_validation(
            errors.ErrListProperties,
            validation.validate_list_properties_request(params),
        )

        path = (
            f"/edgeworkers/v1/ids/{params.edge_worker_id}/properties"
        )
        query = {
            "activeOnly": str(params.active_only).lower(),
        }

        resp, result = self._session.exec(
            "GET", path,
            expect_json=True,
            params=query,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.ListPropertiesResponse.from_dict(result)

    # ------------------------------------------------------------------ #
    # Reports
    # ------------------------------------------------------------------ #

    def get_summary_report(
        self, params: models.GetSummaryReportRequest
    ) -> models.GetSummaryReportResponse:
        """Get a summary report for EdgeWorkers (report ID 1).

        Args:
            params: Request with edge_worker, start, and optional
                end, status, and event_handler filters.

        Returns:
            GetSummaryReportResponse with summary report data.
        """
        logger.debug("GetSummaryReport")
        self._check_validation(
            errors.ErrGetSummaryReport,
            validation.validate_get_summary_report_request(params),
        )

        query: dict[str, str] = {
            "edgeWorker": params.edge_worker,
            "start": params.start,
        }
        if params.end:
            query["end"] = params.end
        if params.status is not None:
            query["status"] = params.status
        if params.event_handler is not None:
            query["eventHandler"] = params.event_handler

        resp, result = self._session.exec(
            "GET", "/edgeworkers/v1/reports/1",
            expect_json=True,
            params=query,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.GetSummaryReportResponse.from_dict(result)

    def get_report(
        self, params: models.GetReportRequest
    ) -> models.GetReportResponse:
        """Get a specific report for EdgeWorkers.

        Args:
            params: Request with report_id, edge_worker, start, and
                optional end, status, and event_handler filters.

        Returns:
            GetReportResponse with report data.
        """
        logger.debug("GetReport")
        self._check_validation(
            errors.ErrGetReport,
            validation.validate_get_report_request(params),
        )

        path = f"/edgeworkers/v1/reports/{params.report_id}"
        query: dict[str, str] = {
            "edgeWorker": params.edge_worker,
            "start": params.start,
        }
        if params.end:
            query["end"] = params.end
        if params.status is not None:
            query["status"] = params.status
        if params.event_handler is not None:
            query["eventHandler"] = params.event_handler

        resp, result = self._session.exec(
            "GET", path,
            expect_json=True,
            params=query,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.GetReportResponse.from_dict(result)

    def list_reports(self) -> models.ListReportsResponse:
        """List available EdgeWorker reports.

        Returns:
            ListReportsResponse with available report definitions.
        """
        logger.debug("ListReports")

        resp, result = self._session.exec(
            "GET", "/edgeworkers/v1/reports",
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.ListReportsResponse.from_dict(result)

    # ------------------------------------------------------------------ #
    # Resource Tiers
    # ------------------------------------------------------------------ #

    def list_resource_tiers(
        self, params: models.ListResourceTiersRequest
    ) -> models.ListResourceTiersResponse:
        """List resource tiers for a contract.

        Args:
            params: Request with contract_id.

        Returns:
            ListResourceTiersResponse with tier listings.
        """
        logger.debug("ListResourceTiers")
        self._check_validation(
            errors.ErrListResourceTiers,
            validation.validate_list_resource_tiers_request(params),
        )

        query = {"contractId": params.contract_id}

        resp, result = self._session.exec(
            "GET", "/edgeworkers/v1/resource-tiers",
            expect_json=True,
            params=query,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.ListResourceTiersResponse.from_dict(result)

    def get_resource_tier(
        self, params: models.GetResourceTierRequest
    ) -> models.ResourceTier:
        """Get the resource tier for an EdgeWorker.

        Args:
            params: Request with edge_worker_id.

        Returns:
            ResourceTier details.
        """
        logger.debug("GetResourceTier")
        self._check_validation(
            errors.ErrGetResourceTier,
            validation.validate_get_resource_tier_request(params),
        )

        path = (
            f"/edgeworkers/v1/ids/{params.edge_worker_id}/resource-tier"
        )

        resp, result = self._session.exec(
            "GET", path,
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.ResourceTier.from_dict(result)

    # ------------------------------------------------------------------ #
    # Secure Tokens
    # ------------------------------------------------------------------ #

    def create_secure_token(
        self, params: models.CreateSecureTokenRequest
    ) -> models.CreateSecureTokenResponse:
        """Create a secure token for EdgeWorker debugging.

        Args:
            params: Request with token configuration.

        Returns:
            CreateSecureTokenResponse with the generated token.
        """
        logger.debug("CreateSecureToken")
        self._check_validation(
            errors.ErrCreateSecureToken,
            validation.validate_create_secure_token_request(params),
        )

        resp, result = self._session.exec(
            "POST", "/edgeworkers/v1/secure-token",
            body=params.to_dict(),
            expect_json=True,
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 201:
            raise errors.parse_edgeworkers_error(resp)

        return models.CreateSecureTokenResponse.from_dict(result)

    # ------------------------------------------------------------------ #
    # Validations
    # ------------------------------------------------------------------ #

    def validate_bundle(
        self, params: models.ValidateBundleRequest
    ) -> models.ValidateBundleResponse:
        """Validate an EdgeWorker bundle without creating a version.

        Sets Content-Type to application/gzip and sends raw
        bundle bytes.

        Args:
            params: Request with bundle bytes to validate.

        Returns:
            ValidateBundleResponse with validation results.
        """
        logger.debug("ValidateBundle")
        self._check_validation(
            errors.ErrValidateBundle,
            validation.validate_validate_bundle_request(params),
        )

        resp, result = self._session.exec(
            "POST", "/edgeworkers/v1/validations",
            body=params.bundle,
            expect_json=True,
            headers={"Content-Type": "application/gzip"},
            error_parser=errors.parse_edgeworkers_error,
        )
        if resp.status_code != 200:
            raise errors.parse_edgeworkers_error(resp)

        return models.ValidateBundleResponse.from_dict(result)
