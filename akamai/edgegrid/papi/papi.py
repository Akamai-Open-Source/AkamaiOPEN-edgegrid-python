"""Akamai Property Manager API (PAPI) client implementation.

Provides the ``Client`` class implementing all PAPI operations: properties,
activations, hostnames, includes, CP codes, edge hostnames, rules, search,
and more.  Mirrors Go ``pkg/papi`` interface and ``papi`` struct from the
Akamai Open EdgeGrid Go v12 SDK.
"""

# pylint: disable=too-many-lines

import json
import logging
from dataclasses import asdict
from typing import Any

from akamai.edgegrid.session import Session
from akamai.edgegrid.papi import models
from akamai.edgegrid.papi import errors
from akamai.edgegrid.papi import validation
from akamai.edgegrid.utils import unescape_content

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------
# Helper: dataclass → JSON-ready dict with camelCase keys
# -----------------------------------------------------------------------

def _to_body(obj: Any) -> Any:
    """Convert a dataclass (or plain dict/list) into a JSON-serialisable dict.

    Uses :func:`dataclasses.asdict` for dataclass instances and returns
    plain dicts/lists unchanged.  ``None`` is passed through so that
    :meth:`Session.exec` can skip body serialisation.
    """
    if obj is None:
        return None
    try:
        return asdict(obj)
    except TypeError:
        return obj


# -----------------------------------------------------------------------
# WithUsePrefixes factory function
# -----------------------------------------------------------------------

def WithUsePrefixes(use_prefixes: bool) -> bool:  # pylint: disable=invalid-name
    """Create a PAPI option that controls the PAPI-Use-Prefixes header.

    Mirrors Go ``WithUsePrefixes`` option function.  In Python the value
    is passed directly to the ``Client`` constructor.

    Args:
        use_prefixes: Whether PAPI should include ID prefixes in
            requests and responses.

    Returns:
        The boolean value to pass as ``use_prefixes`` to ``Client()``.
    """
    return use_prefixes


# -----------------------------------------------------------------------
# PAPI Client
# -----------------------------------------------------------------------

class Client:  # pylint: disable=too-many-public-methods
    """Property Manager API (PAPI) client.

    Provides methods for all PAPI operations: properties, activations,
    hostnames, includes, CP codes, edge hostnames, rules, search, etc.

    Mirrors Go ``pkg/papi.PAPI`` interface and ``papi`` struct.

    Usage::

        >>> from akamai.edgegrid.papi import Client
        >>> from akamai.edgegrid.session import Session
        >>> session = Session(edgerc_path="~/.edgerc", section="papi")
        >>> client = Client(session)
        >>> resp = client.get_groups()
    """

    def __init__(self, session: Session, use_prefixes: bool = True):
        """Initialise PAPI client.

        Args:
            session: Authenticated :class:`Session` for HTTP communication.
            use_prefixes: Send ``PAPI-Use-Prefixes`` header on every
                request (default ``True``).  Mirrors Go ``WithUsePrefixes``.
        """
        self._session = session
        self._use_prefixes = use_prefixes

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _exec(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        method: str,
        path: str,
        *,
        body: Any = None,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        expect_json: bool = True,
    ) -> tuple:
        """Execute a PAPI request with the ``PAPI-Use-Prefixes`` header.

        Mirrors Go ``papi.Exec()`` which injects the header before
        delegating to ``session.Exec()``.
        """
        papi_headers: dict[str, str] = {
            "PAPI-Use-Prefixes": str(self._use_prefixes).lower(),
        }
        if headers:
            papi_headers.update(headers)

        return self._session.exec(
            method,
            path,
            body=body,
            headers=papi_headers,
            params=params,
            expect_json=expect_json,
            error_parser=self._parse_error,
        )

    def _parse_error(self, resp) -> errors.Error:
        """Parse a PAPI error from an HTTP response.

        Mirrors Go ``papi.Error(r *http.Response)`` from ``errors.go``.
        """
        error = errors.Error()
        try:
            body = resp.text
        except Exception as exc:  # pylint: disable=broad-except
            error.status_code = resp.status_code
            error.title = "Failed to read error body"
            error.detail = str(exc)
            return error

        try:
            data = json.loads(body)
            error.type = data.get("type", "")
            error.title = data.get("title", "")
            error.detail = data.get("detail", "")
            error.instance = data.get("instance", "")
            error.behavior_name = data.get("behaviorName", "")
            error.error_location = data.get("errorLocation", "")
            error.status_code = data.get("statusCode", 0)
            error.errors = data.get("errors")
            error.warnings = data.get("warnings")
            error.limit_key = data.get("limitKey", "")
            error.limit = data.get("limit")
            error.remaining = data.get("remaining")
            error.redirect_link = data.get("redirectLink")
            error.activation_link = data.get("activationLink")
        except (json.JSONDecodeError, AttributeError):
            error.title = (
                "Failed to unmarshal error body. PAPI API failed. "
                "Check details for more information."
            )
            error.detail = unescape_content(body)

        error.status_code = resp.status_code
        return error

    # ------------------------------------------------------------------
    # Activations  (activation.go)
    # ------------------------------------------------------------------

    def create_activation(
        self, params: models.CreateActivationRequest
    ) -> models.CreateActivationResponse:
        """Create a new property activation or deactivation request.

        See: https://techdocs.akamai.com/property-mgr/reference/post-property-activations
        """
        logger.debug("CreateActivation")

        err = validation.validate_create_activation_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrCreateActivation}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        # Default activation type to ACTIVATE when empty
        if params.activation and not params.activation.activation_type:
            params.activation.activation_type = models.ActivationTypeActivate

        url = f"/papi/v1/properties/{params.property_id}/activations"
        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id

        resp, result = self._exec(
            "POST", url,
            body=_to_body(params.activation),
            params=query_params or None,
        )
        Session.close_response_body(resp)

        response = models.CreateActivationResponse()
        if isinstance(result, dict):
            response.activation_link = result.get("activationLink", "")
        response.activation_id, _ = models.response_link_parse(
            response.activation_link
        )
        return response

    def get_activations(
        self, params: models.GetActivationsRequest
    ) -> models.GetActivationsResponse:
        """List all activations for a property.

        See: https://techdocs.akamai.com/property-mgr/reference/get-property-activations
        """
        logger.debug("GetActivations")

        err = validation.validate_get_activations_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetActivations}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = f"/papi/v1/properties/{params.property_id}/activations"
        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id

        resp, result = self._exec("GET", url, params=query_params or None)
        Session.close_response_body(resp)

        response = models.GetActivationsResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            act_items = result.get("activations", {})
            if isinstance(act_items, dict):
                response.activations = models.ActivationsItems(
                    items=[
                        _dict_to_activation(a)
                        for a in act_items.get("items", [])
                    ]
                )
        return response

    def get_activation(
        self, params: models.GetActivationRequest
    ) -> models.GetActivationResponse:
        """Get details of a specific property activation.

        See: https://techdocs.akamai.com/property-mgr/reference/get-property-activation
        """
        logger.debug("GetActivation")

        err = validation.validate_get_activation_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetActivation}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/properties/{params.property_id}"
            f"/activations/{params.activation_id}"
        )
        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id

        resp, result = self._exec("GET", url, params=query_params or None)
        Session.close_response_body(resp)

        response = models.GetActivationResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            act_items = result.get("activations", {})
            if isinstance(act_items, dict):
                items = act_items.get("items", [])
                if items:
                    response.activation = _dict_to_activation(items[0])
            # Retry-After header
            retry_after = resp.headers.get("Retry-After")
            if retry_after is not None:
                try:
                    response.retry_after = int(retry_after)
                except (ValueError, TypeError):
                    pass
        return response

    def cancel_activation(
        self, params: models.CancelActivationRequest
    ) -> models.CancelActivationResponse:
        """Cancel an active property activation.

        See: https://techdocs.akamai.com/property-mgr/reference/delete-property-activation
        """
        logger.debug("CancelActivation")

        err = validation.validate_cancel_activation_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrCancelActivation}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/properties/{params.property_id}"
            f"/activations/{params.activation_id}"
        )
        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id

        resp, result = self._exec("DELETE", url, params=query_params or None)
        Session.close_response_body(resp)

        response = models.CancelActivationResponse()
        if isinstance(result, dict):
            act_items = result.get("activations", {})
            if isinstance(act_items, dict):
                items = act_items.get("items", [])
                if items:
                    response.activations = models.ActivationsItems(
                        items=[
                            _dict_to_activation(a) for a in items
                        ]
                    )
        return response

    # ------------------------------------------------------------------
    # Active Property Hostnames  (active_property_hostname.go)
    # ------------------------------------------------------------------

    def list_active_property_hostnames(
        self, params: models.ListActivePropertyHostnamesRequest
    ) -> models.ListActivePropertyHostnamesResponse:
        """List active hostnames for a property.

        See: https://techdocs.akamai.com/property-mgr/reference/get-active-property-hostnames
        """
        logger.debug("ListActivePropertyHostnames")

        err = validation.validate_list_active_property_hostnames_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrListActivePropertyHostnames}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = f"/papi/v1/properties/{params.property_id}/hostnames/active"
        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id
        if params.offset:
            query_params["offset"] = str(params.offset)
        if params.limit:
            query_params["limit"] = str(params.limit)
        if params.sort:
            query_params["sort"] = params.sort
        if params.filter:
            query_params["filter"] = params.filter

        resp, result = self._exec("GET", url, params=query_params or None)
        Session.close_response_body(resp)

        response = models.ListActivePropertyHostnamesResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            response.total_results = result.get("totalResults", 0)
            response.result_count = result.get("resultCount", 0)
            hostnames_data = result.get("hostnames")
            if isinstance(hostnames_data, dict):
                response.hostnames = _dict_to_hostnames_response_items(
                    hostnames_data
                )
        return response

    def get_active_property_hostnames_diff(
        self, params: models.GetActivePropertyHostnamesDiffRequest
    ) -> models.GetActivePropertyHostnamesDiffResponse:
        """Get the diff of active property hostnames.

        See: https://techdocs.akamai.com/property-mgr/reference/get-active-property-hostnames-diff
        """
        logger.debug("GetActivePropertyHostnamesDiff")

        err = validation.validate_get_active_property_hostnames_diff_request(
            params
        )
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetActivePropertyHostnamesDiff}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = f"/papi/v1/properties/{params.property_id}/hostnames/diff"
        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id
        if params.offset:
            query_params["offset"] = str(params.offset)
        if params.limit:
            query_params["limit"] = str(params.limit)

        resp, result = self._exec("GET", url, params=query_params or None)
        Session.close_response_body(resp)

        response = models.GetActivePropertyHostnamesDiffResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            response.property_id = result.get("propertyId", "")
            hostnames_data = result.get("hostnames")
            if isinstance(hostnames_data, dict):
                response.hostnames = _dict_to_hostnames_diff_response_items(
                    hostnames_data
                )
        return response

    def list_active_account_hostnames(
        self, params: models.ListActiveAccountHostnamesRequest
    ) -> models.ListActiveAccountHostnamesResponse:
        """List all active hostnames across an account.

        See: https://techdocs.akamai.com/property-mgr/reference/get-active-account-hostnames
        """
        logger.debug("ListActiveAccountHostnames")

        err = validation.validate_list_active_account_hostnames_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrListActiveAccountHostnames}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = "/papi/v1/hostnames"
        query_params: dict[str, str] = {}
        if params.offset:
            query_params["offset"] = str(params.offset)
        if params.limit:
            query_params["limit"] = str(params.limit)
        if params.sort:
            query_params["sort"] = params.sort
        if params.hostname:
            query_params["hostname"] = params.hostname
        if params.cname_to:
            query_params["cnameTo"] = params.cname_to
        if params.network:
            query_params["network"] = params.network
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id

        resp, result = self._exec("GET", url, params=query_params or None)
        Session.close_response_body(resp)

        response = models.ListActiveAccountHostnamesResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.available_sort = result.get("availableSort", [])
            response.current_sort = result.get("currentSort", "")
            response.default_sort = result.get("defaultSort", "")
            hostnames_data = result.get("hostnames")
            if isinstance(hostnames_data, dict):
                items_raw = hostnames_data.get("items", [])
                response.hostnames = models.ActiveAccountHostnames(
                    items=[
                        _dict_to_active_account_hostname_item(i)
                        for i in items_raw
                    ],
                    current_item_count=hostnames_data.get(
                        "currentItemCount", 0
                    ),
                    next_link=hostnames_data.get("nextLink"),
                    previous_link=hostnames_data.get("previousLink"),
                    total_items=hostnames_data.get("totalItems", 0),
                )
        return response

    # ------------------------------------------------------------------
    # Client Settings  (clientsettings.go)
    # ------------------------------------------------------------------

    def get_client_settings(self) -> models.ClientSettingsBody:
        """Get PAPI client settings.

        See: https://techdocs.akamai.com/property-mgr/reference/get-client-settings
        """
        logger.debug("GetClientSettings")

        url = "/papi/v1/client-settings"
        resp, result = self._exec("GET", url)
        Session.close_response_body(resp)

        if resp.status_code != 200:
            err = self._parse_error(resp)
            err.title = f"{errors.ErrGetClientSettings}: {err.title}"
            raise err

        response = models.ClientSettingsBody()
        if isinstance(result, dict):
            response.rule_format = result.get("ruleFormat", "")
            response.use_prefixes = result.get("usePrefixes", False)
        return response

    def update_client_settings(
        self, params: models.ClientSettingsBody
    ) -> models.ClientSettingsBody:
        """Update PAPI client settings.

        See: https://techdocs.akamai.com/property-mgr/reference/put-client-settings
        """
        logger.debug("UpdateClientSettings")

        url = "/papi/v1/client-settings"
        resp, result = self._exec("PUT", url, body=_to_body(params))
        Session.close_response_body(resp)

        if resp.status_code != 200:
            err = self._parse_error(resp)
            err.title = f"{errors.ErrUpdateClientSettings}: {err.title}"
            raise err

        response = models.ClientSettingsBody()
        if isinstance(result, dict):
            response.rule_format = result.get("ruleFormat", "")
            response.use_prefixes = result.get("usePrefixes", False)
        return response

    # ------------------------------------------------------------------
    # Contracts  (contract.go)
    # ------------------------------------------------------------------

    def get_contracts(self) -> models.GetContractsResponse:
        """List all contracts.

        See: https://techdocs.akamai.com/property-mgr/reference/get-contracts
        """
        logger.debug("GetContracts")

        url = "/papi/v1/contracts"
        resp, result = self._exec("GET", url)
        Session.close_response_body(resp)

        if resp.status_code != 200:
            err = self._parse_error(resp)
            err.title = f"{errors.ErrGetContracts}: {err.title}"
            raise err

        response = models.GetContractsResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            contracts_data = result.get("contracts", {})
            if isinstance(contracts_data, dict):
                response.contracts = models.ContractsItems(
                    items=[
                        _dict_to_contract(c)
                        for c in contracts_data.get("items", [])
                    ]
                )
        return response

    # ------------------------------------------------------------------
    # CP Codes  (cpcode.go)
    # ------------------------------------------------------------------

    def get_cp_codes(
        self, params: models.GetCPCodesRequest
    ) -> models.GetCPCodesResponse:
        """List CP codes for a contract and group.

        See: https://techdocs.akamai.com/property-mgr/reference/get-cpcodes
        """
        logger.debug("GetCPCodes")

        err = validation.validate_get_cp_codes_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetCPCodes}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = "/papi/v1/cpcodes"
        query_params: dict[str, str] = {
            "contractId": params.contract_id,
            "groupId": params.group_id,
        }

        resp, result = self._exec("GET", url, params=query_params)
        Session.close_response_body(resp)

        response = models.GetCPCodesResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            cp_data = result.get("cpcodes", {})
            if isinstance(cp_data, dict):
                response.cp_codes = models.CPCodeItems(
                    items=[
                        _dict_to_cp_code(c)
                        for c in cp_data.get("items", [])
                    ]
                )
        return response

    def get_cp_code(
        self, params: models.GetCPCodeRequest
    ) -> models.GetCPCodesResponse:
        """Get a specific CP code.

        See: https://techdocs.akamai.com/property-mgr/reference/get-cpcode
        """
        logger.debug("GetCPCode")

        err = validation.validate_get_cp_code_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetCPCode}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = f"/papi/v1/cpcodes/{params.cpcode_id}"
        query_params: dict[str, str] = {
            "contractId": params.contract_id,
            "groupId": params.group_id,
        }

        resp, result = self._exec("GET", url, params=query_params)
        Session.close_response_body(resp)

        response = models.GetCPCodesResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            cp_data = result.get("cpcodes", {})
            if isinstance(cp_data, dict):
                response.cp_codes = models.CPCodeItems(
                    items=[
                        _dict_to_cp_code(c)
                        for c in cp_data.get("items", [])
                    ]
                )
        return response

    def get_cp_code_detail(
        self, cpcode_id: int
    ) -> models.CPCodeDetailResponse:
        """Get detailed CP code information from the CPRG API.

        See: https://techdocs.akamai.com/cp-codes/reference/get-cpcode
        """
        logger.debug("GetCPCodeDetail")

        if not cpcode_id:
            raise errors.Error(
                title=f"{errors.ErrGetCPCodeDetail}",
                detail="struct validation: CPCodeID: cannot be blank",
                status_code=0,
            )

        url = f"/cprg/v1/cpcodes/{cpcode_id}"
        resp, result = self._exec("GET", url)
        Session.close_response_body(resp)

        response = models.CPCodeDetailResponse()
        if isinstance(result, dict):
            _populate_cp_code_detail(response, result)
        return response

    def create_cp_code(
        self, params: models.CreateCPCodeRequest
    ) -> models.CreateCPCodeResponse:
        """Create a new CP code.

        See: https://techdocs.akamai.com/property-mgr/reference/post-cpcodes
        """
        logger.debug("CreateCPCode")

        err = validation.validate_create_cp_code_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrCreateCPCode}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = "/papi/v1/cpcodes"
        query_params: dict[str, str] = {
            "contractId": params.contract_id,
            "groupId": params.group_id,
        }

        resp, result = self._exec(
            "POST", url, body=_to_body(params.cpcode), params=query_params
        )
        Session.close_response_body(resp)

        response = models.CreateCPCodeResponse()
        if isinstance(result, dict):
            response.cpcode_link = result.get("cpcodeLink", "")
        response.cpcode_id, _ = models.response_link_parse(
            response.cpcode_link
        )
        return response

    def update_cp_code(
        self, params: models.UpdateCPCodeRequest
    ) -> models.CPCodeDetailResponse:
        """Update an existing CP code via the CPRG API.

        See: https://techdocs.akamai.com/cp-codes/reference/put-cpcode
        """
        logger.debug("UpdateCPCode")

        err = validation.validate_update_cp_code_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrUpdateCPCode}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = f"/cprg/v1/cpcodes/{params.id}"
        resp, result = self._exec("PUT", url, body=_to_body(params))
        Session.close_response_body(resp)

        response = models.CPCodeDetailResponse()
        if isinstance(result, dict):
            _populate_cp_code_detail(response, result)
        return response

    # ------------------------------------------------------------------
    # Domain Ownership Validation  (domain_ownership_validation.go)
    # ------------------------------------------------------------------

    def validate_domains_ownership(
        self, params: models.ValidateDomainsOwnershipRequest
    ) -> models.ValidateDomainsOwnershipResponse:
        """Validate domain ownership for a property.

        See: https://techdocs.akamai.com/property-mgr/reference/post-domain-challenges
        """
        logger.debug("ValidateDomainsOwnership")

        err = validation.validate_validate_domains_ownership_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrValidateDomainsOwnership}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/properties/{params.property_id}"
            f"/domain-ownership-challenges"
        )
        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id

        body = _to_body(getattr(params, "body", None))

        resp, result = self._exec(
            "POST", url, body=body, params=query_params or None
        )
        Session.close_response_body(resp)

        response = models.ValidateDomainsOwnershipResponse()
        if isinstance(result, dict):
            challenges_raw = result.get("challenges", [])
            response.challenges = [
                _dict_to_hostname_validation_details(c)
                for c in challenges_raw
            ]
        return response

    # ------------------------------------------------------------------
    # Edge Hostnames  (edgehostname.go)
    # ------------------------------------------------------------------

    def get_edge_hostnames(
        self, params: models.GetEdgeHostnamesRequest
    ) -> models.GetEdgeHostnamesResponse:
        """List edge hostnames for a contract and group.

        See: https://techdocs.akamai.com/property-mgr/reference/get-edgehostnames
        """
        logger.debug("GetEdgeHostnames")

        err = validation.validate_get_edge_hostnames_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetEdgeHostnames}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = "/papi/v1/edgehostnames"
        query_params: dict[str, str] = {
            "contractId": params.contract_id,
            "groupId": params.group_id,
        }
        options = getattr(params, "options", None)
        if options:
            query_params["options"] = ",".join(options)

        resp, result = self._exec("GET", url, params=query_params)
        Session.close_response_body(resp)

        response = models.GetEdgeHostnamesResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            eh_data = result.get("edgeHostnames", {})
            if isinstance(eh_data, dict):
                response.edge_hostnames = models.EdgeHostnameItems(
                    items=[
                        _dict_to_edge_hostname(e)
                        for e in eh_data.get("items", [])
                    ]
                )
        return response

    def get_edge_hostname(
        self, params: models.GetEdgeHostnameRequest
    ) -> models.GetEdgeHostnamesResponse:
        """Get a specific edge hostname.

        See: https://techdocs.akamai.com/property-mgr/reference/get-edgehostname
        """
        logger.debug("GetEdgeHostname")

        err = validation.validate_get_edge_hostname_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetEdgeHostname}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = f"/papi/v1/edgehostnames/{params.edge_hostname_id}"
        query_params: dict[str, str] = {
            "contractId": params.contract_id,
            "groupId": params.group_id,
        }
        options = getattr(params, "options", None)
        if options:
            query_params["options"] = ",".join(options)

        resp, result = self._exec("GET", url, params=query_params)
        Session.close_response_body(resp)

        response = models.GetEdgeHostnamesResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            eh_data = result.get("edgeHostnames", {})
            if isinstance(eh_data, dict):
                response.edge_hostnames = models.EdgeHostnameItems(
                    items=[
                        _dict_to_edge_hostname(e)
                        for e in eh_data.get("items", [])
                    ]
                )
        return response

    def create_edge_hostname(
        self, params: models.CreateEdgeHostnameRequest
    ) -> models.CreateEdgeHostnameResponse:
        """Create a new edge hostname.

        See: https://techdocs.akamai.com/property-mgr/reference/post-edgehostnames
        """
        logger.debug("CreateEdgeHostname")

        err = validation.validate_create_edge_hostname_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrCreateEdgeHostname}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = "/papi/v1/edgehostnames"
        query_params: dict[str, str] = {
            "contractId": params.contract_id,
            "groupId": params.group_id,
        }
        options = getattr(params, "options", None)
        if options:
            query_params["options"] = ",".join(options)

        resp, result = self._exec(
            "POST", url, body=_to_body(params.edge_hostname),
            params=query_params,
        )
        Session.close_response_body(resp)

        response = models.CreateEdgeHostnameResponse()
        if isinstance(result, dict):
            response.edge_hostname_link = result.get("edgeHostnameLink", "")
        response.edge_hostname_id, _ = models.response_link_parse(
            response.edge_hostname_link
        )
        return response

    # ------------------------------------------------------------------
    # Groups  (group.go)
    # ------------------------------------------------------------------

    def get_groups(self) -> models.GetGroupsResponse:
        """List all groups.

        See: https://techdocs.akamai.com/property-mgr/reference/get-groups
        """
        logger.debug("GetGroups")

        url = "/papi/v1/groups"
        resp, result = self._exec("GET", url)
        Session.close_response_body(resp)

        if resp.status_code != 200:
            err = self._parse_error(resp)
            err.title = f"{errors.ErrGetGroups}: {err.title}"
            raise err

        response = models.GetGroupsResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.account_name = result.get("accountName", "")
            groups_data = result.get("groups", {})
            if isinstance(groups_data, dict):
                response.groups = models.GroupItems(
                    items=[
                        _dict_to_group(g)
                        for g in groups_data.get("items", [])
                    ]
                )
        return response

    # ------------------------------------------------------------------
    # Includes  (include.go)
    # ------------------------------------------------------------------

    def list_includes(
        self, params: models.ListIncludesRequest
    ) -> models.ListIncludesResponse:
        """List includes for a contract.

        See: https://techdocs.akamai.com/property-mgr/reference/get-includes
        """
        logger.debug("ListIncludes")

        err = validation.validate_list_includes_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrListIncludes}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = "/papi/v1/includes"
        query_params: dict[str, str] = {
            "contractId": params.contract_id,
        }
        if params.group_id:
            query_params["groupId"] = params.group_id

        resp, result = self._exec("GET", url, params=query_params)
        Session.close_response_body(resp)

        response = models.ListIncludesResponse()
        if isinstance(result, dict):
            inc_data = result.get("includes", {})
            if isinstance(inc_data, dict):
                response.includes = models.IncludeItems(
                    items=[
                        _dict_to_include(i)
                        for i in inc_data.get("items", [])
                    ]
                )
        return response

    def list_include_parents(
        self, params: models.ListIncludeParentsRequest
    ) -> models.ListIncludeParentsResponse:
        """List parent properties of an include.

        See: https://techdocs.akamai.com/property-mgr/reference/get-include-parents
        """
        logger.debug("ListIncludeParents")

        err = validation.validate_list_include_parents_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrListIncludeParents}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = f"/papi/v1/includes/{params.include_id}/parents"
        resp, result = self._exec("GET", url)
        Session.close_response_body(resp)

        response = models.ListIncludeParentsResponse()
        if isinstance(result, dict):
            parents_data = result.get("properties", {})
            if isinstance(parents_data, dict):
                response.properties = models.ParentPropertyItems(
                    items=[
                        _dict_to_parent_property(p)
                        for p in parents_data.get("items", [])
                    ]
                )
        return response

    def get_include(
        self, params: models.GetIncludeRequest
    ) -> models.GetIncludeResponse:
        """Get details of a specific include.

        See: https://techdocs.akamai.com/property-mgr/reference/get-include
        """
        logger.debug("GetInclude")

        err = validation.validate_get_include_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetInclude}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = f"/papi/v1/includes/{params.include_id}"
        query_params: dict[str, str] = {
            "contractId": params.contract_id,
            "groupId": params.group_id,
        }

        resp, result = self._exec("GET", url, params=query_params)
        Session.close_response_body(resp)

        response = models.GetIncludeResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            inc_data = result.get("includes", {})
            if isinstance(inc_data, dict):
                items = inc_data.get("items", [])
                if items:
                    response.include = _dict_to_include(items[0])
        return response

    def create_include(
        self, params: models.CreateIncludeRequest
    ) -> models.CreateIncludeResponse:
        """Create a new include.

        See: https://techdocs.akamai.com/property-mgr/reference/post-includes
        """
        logger.debug("CreateInclude")

        err = validation.validate_create_include_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrCreateInclude}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = "/papi/v1/includes"
        query_params: dict[str, str] = {
            "contractId": params.contract_id,
            "groupId": params.group_id,
        }

        body = {
            "includeName": params.include_name,
            "includeType": params.include_type,
            "productId": params.product_id,
            "ruleFormat": params.rule_format,
        }
        if params.clone_include_from:
            body["cloneIncludeFrom"] = _to_body(params.clone_include_from)

        resp, result = self._exec(
            "POST", url, body=body, params=query_params
        )

        response = models.CreateIncludeResponse()
        if isinstance(result, dict):
            response.include_link = result.get("includeLink", "")
        response.include_id, _ = models.response_link_parse(
            response.include_link
        )

        Session.close_response_body(resp)
        return response

    def delete_include(
        self, params: models.DeleteIncludeRequest
    ) -> models.DeleteIncludeResponse:
        """Delete an include.

        See: https://techdocs.akamai.com/property-mgr/reference/delete-include
        """
        logger.debug("DeleteInclude")

        err = validation.validate_delete_include_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrDeleteInclude}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = f"/papi/v1/includes/{params.include_id}"
        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id

        resp, result = self._exec(
            "DELETE", url, params=query_params or None
        )
        Session.close_response_body(resp)

        response = models.DeleteIncludeResponse()
        if isinstance(result, dict):
            response.message = result.get("message", "")
        return response

    # ------------------------------------------------------------------
    # Include Rules  (include_rule.go)
    # ------------------------------------------------------------------

    def get_include_rule_tree(
        self, params: models.GetIncludeRuleTreeRequest
    ) -> models.GetIncludeRuleTreeResponse:
        """Get the rule tree of an include version.

        See: https://techdocs.akamai.com/property-mgr/reference/get-include-version-rules
        """
        logger.debug("GetIncludeRuleTree")

        err = validation.validate_get_include_rule_tree_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetIncludeRuleTree}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/includes/{params.include_id}"
            f"/versions/{params.include_version}/rules"
        )
        query_params: dict[str, str] = {
            "contractId": params.contract_id,
            "groupId": params.group_id,
        }
        if params.validate_mode:
            query_params["validateMode"] = params.validate_mode
        if params.validate_rules is False:
            query_params["validateRules"] = "false"

        headers: dict[str, str] = {}
        if params.rule_format:
            accept = (
                f"application/vnd.akamai.papirules."
                f"{params.rule_format}+json"
            )
            headers["Accept"] = accept
            headers["Content-Type"] = accept

        resp, result = self._exec(
            "GET", url, headers=headers or None,
            params=query_params,
        )
        Session.close_response_body(resp)

        response = models.GetIncludeRuleTreeResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            response.include_id = result.get("includeId", "")
            response.include_name = result.get("includeName", "")
            response.include_type = result.get("includeType", "")
            response.include_version = result.get("includeVersion", 0)
            response.etag = result.get("etag", "")
            response.rule_format = result.get("ruleFormat", "")
            rules_data = result.get("rules")
            if isinstance(rules_data, dict):
                response.rules = _dict_to_rules(rules_data)
            response.comments = result.get("comments", "")
        return response

    def update_include_rule_tree(
        self, params: models.UpdateIncludeRuleTreeRequest
    ) -> models.UpdateIncludeRuleTreeResponse:
        """Update the rule tree of an include version.

        See: https://techdocs.akamai.com/property-mgr/reference/put-include-version-rules
        """
        logger.debug("UpdateIncludeRuleTree")

        err = validation.validate_update_include_rule_tree_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrUpdateIncludeRuleTree}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/includes/{params.include_id}"
            f"/versions/{params.include_version}/rules"
        )
        query_params: dict[str, str] = {
            "contractId": params.contract_id,
            "groupId": params.group_id,
        }
        if params.validate_mode:
            query_params["validateMode"] = params.validate_mode
        if getattr(params, "dry_run", False):
            query_params["dryRun"] = "true"

        headers: dict[str, str] = {}
        if params.rule_format:
            accept = (
                f"application/vnd.akamai.papirules."
                f"{params.rule_format}+json"
            )
            headers["Accept"] = accept
            headers["Content-Type"] = accept

        resp, result = self._exec(
            "PUT", url, body=_to_body(params.rules),
            headers=headers or None,
            params=query_params,
        )

        response = models.UpdateIncludeRuleTreeResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            response.include_id = result.get("includeId", "")
            response.include_name = result.get("includeName", "")
            response.include_type = result.get("includeType", "")
            response.include_version = result.get("includeVersion", 0)
            response.etag = result.get("etag", "")
            response.rule_format = result.get("ruleFormat", "")
            rules_data = result.get("rules")
            if isinstance(rules_data, dict):
                response.rules = _dict_to_rules(rules_data)
            response.comments = result.get("comments", "")
            errs_data = result.get("errors")
            if errs_data:
                response.errors = errs_data
            warnings_data = result.get("warnings")
            if warnings_data:
                response.warnings = warnings_data

        response.response_headers = models.UpdateIncludeResponseHeaders(
            elements_per_property_remaining=resp.headers.get(
                "x-limit-elements-per-property-remaining", ""
            ),
            elements_per_property_total=resp.headers.get(
                "x-limit-elements-per-property-limit", ""
            ),
            max_nested_rules_per_include_remaining=resp.headers.get(
                "x-limit-max-nested-rules-per-include-remaining", ""
            ),
            max_nested_rules_per_include_total=resp.headers.get(
                "x-limit-max-nested-rules-per-include-limit", ""
            ),
        )
        Session.close_response_body(resp)
        return response

    # ------------------------------------------------------------------
    # Include Activations  (include_activations.go)
    # ------------------------------------------------------------------

    def activate_include(
        self, params: models.ActivateIncludeRequest
    ) -> models.ActivationIncludeResponse:
        """Activate an include version.

        See: https://techdocs.akamai.com/property-mgr/reference/post-include-activation
        """
        logger.debug("ActivateInclude")

        err = validation.validate_activate_include_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrActivateInclude}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = f"/papi/v1/includes/{params.include_id}/activations"
        body = _build_include_activation_body(params)

        resp, result = self._exec("POST", url, body=body)
        Session.close_response_body(resp)

        response = models.ActivationIncludeResponse()
        if isinstance(result, dict):
            response.activation_link = result.get("activationLink", "")
        response.activation_id, _ = models.response_link_parse(
            response.activation_link
        )
        return response

    def deactivate_include(
        self, params: models.DeactivateIncludeRequest
    ) -> models.DeactivationIncludeResponse:
        """Deactivate an include version.

        See: https://techdocs.akamai.com/property-mgr/reference/post-include-deactivation
        """
        logger.debug("DeactivateInclude")

        err = validation.validate_deactivate_include_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrDeactivateInclude}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = f"/papi/v1/includes/{params.include_id}/activations"
        body = _build_include_activation_body(params)

        resp, result = self._exec("POST", url, body=body)
        Session.close_response_body(resp)

        response = models.DeactivationIncludeResponse()
        if isinstance(result, dict):
            response.activation_link = result.get("activationLink", "")
        response.activation_id, _ = models.response_link_parse(
            response.activation_link
        )
        return response

    def cancel_include_activation(
        self, params: models.CancelIncludeActivationRequest
    ) -> models.CancelIncludeActivationResponse:
        """Cancel an include activation.

        See: https://techdocs.akamai.com/property-mgr/reference/delete-include-activation
        """
        logger.debug("CancelIncludeActivation")

        err = validation.validate_cancel_include_activation_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrCancelIncludeActivation}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/includes/{params.include_id}"
            f"/activations/{params.activation_id}"
        )
        query_params: dict[str, str] = {
            "contractId": params.contract_id,
            "groupId": params.group_id,
        }

        resp, result = self._exec("DELETE", url, params=query_params)
        Session.close_response_body(resp)

        response = models.CancelIncludeActivationResponse()
        if isinstance(result, dict):
            act_data = result.get("activations", {})
            if isinstance(act_data, dict):
                items = act_data.get("items", [])
                if items:
                    response.activations = models.IncludeActivationsRes(
                        items=[
                            _dict_to_include_activation(i)
                            for i in items
                            if isinstance(i, dict)
                        ]
                    )
        return response

    def get_include_activation(
        self, params: models.GetIncludeActivationRequest
    ) -> models.GetIncludeActivationResponse:
        """Get details of a specific include activation.

        See: https://techdocs.akamai.com/property-mgr/reference/get-include-activation
        """
        logger.debug("GetIncludeActivation")

        err = validation.validate_get_include_activation_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetIncludeActivation}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/includes/{params.include_id}"
            f"/activations/{params.activation_id}"
        )

        resp, result = self._exec("GET", url)
        Session.close_response_body(resp)

        response = models.GetIncludeActivationResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            act_data = result.get("activations", {})
            if isinstance(act_data, dict):
                items = act_data.get("items", [])
                if items:
                    response.activation = _dict_to_include_activation(items[0])
            response.validations = result.get("validations")
        return response

    def list_include_activations(
        self, params: models.ListIncludeActivationsRequest
    ) -> models.ListIncludeActivationsResponse:
        """List all activations for an include.

        See: https://techdocs.akamai.com/property-mgr/reference/get-include-activations
        """
        logger.debug("ListIncludeActivations")

        err = validation.validate_list_include_activations_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrListIncludeActivations}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = f"/papi/v1/includes/{params.include_id}/activations"
        query_params: dict[str, str] = {
            "contractId": params.contract_id,
            "groupId": params.group_id,
        }

        resp, result = self._exec("GET", url, params=query_params)
        Session.close_response_body(resp)

        response = models.ListIncludeActivationsResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            act_data = result.get("activations", {})
            if isinstance(act_data, dict):
                response.activations = models.IncludeActivationsRes(
                    items=act_data.get("items", [])
                )
        return response

    # ------------------------------------------------------------------
    # Include Versions  (include_versions.go)
    # ------------------------------------------------------------------

    def create_include_version(
        self, params: models.CreateIncludeVersionRequest
    ) -> models.CreateIncludeVersionResponse:
        """Create a new include version.

        See: https://techdocs.akamai.com/property-mgr/reference/post-include-versions
        """
        logger.debug("CreateIncludeVersion")

        err = validation.validate_create_include_version_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrCreateIncludeVersion}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = f"/papi/v1/includes/{params.include_id}/versions"
        body = {
            "createFromVersion": params.create_from_version,
        }
        if getattr(params, "create_from_version_etag", ""):
            body["createFromVersionEtag"] = params.create_from_version_etag

        resp, result = self._exec("POST", url, body=body)
        Session.close_response_body(resp)

        response = models.CreateIncludeVersionResponse()
        if isinstance(result, dict):
            response.version_link = result.get("versionLink", "")
        vid, _ = models.response_link_parse(response.version_link)
        try:
            response.version = int(vid)
        except (ValueError, TypeError):
            response.version = 0
        return response

    def get_include_version(
        self, params: models.GetIncludeVersionRequest
    ) -> models.GetIncludeVersionResponse:
        """Get details of a specific include version.

        See: https://techdocs.akamai.com/property-mgr/reference/get-include-version
        """
        logger.debug("GetIncludeVersion")

        err = validation.validate_get_include_version_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetIncludeVersion}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/includes/{params.include_id}"
            f"/versions/{params.version}"
        )
        query_params: dict[str, str] = {
            "contractId": params.contract_id,
            "groupId": params.group_id,
        }

        resp, result = self._exec("GET", url, params=query_params)
        Session.close_response_body(resp)

        response = models.GetIncludeVersionResponse()
        if isinstance(result, dict):
            response.include_id = result.get("includeId", "")
            response.include_name = result.get("includeName", "")
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            response.asset_id = result.get("assetId", "")
            response.include_type = result.get("includeType", "")
            versions_data = result.get("versions", {})
            if isinstance(versions_data, dict):
                items = versions_data.get("items", [])
                response.include_versions = models.Versions(
                    items=[
                        _dict_to_include_version(v) for v in items
                    ]
                )
                if items:
                    response.include_version = _dict_to_include_version(
                        items[0]
                    )
        return response

    def list_include_versions(
        self, params: models.ListIncludeVersionsRequest
    ) -> models.ListIncludeVersionsResponse:
        """List all versions of an include.

        See: https://techdocs.akamai.com/property-mgr/reference/get-include-versions
        """
        logger.debug("ListIncludeVersions")

        err = validation.validate_list_include_versions_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrListIncludeVersions}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = f"/papi/v1/includes/{params.include_id}/versions"
        query_params: dict[str, str] = {
            "contractId": params.contract_id,
            "groupId": params.group_id,
        }

        resp, result = self._exec("GET", url, params=query_params)
        Session.close_response_body(resp)

        response = models.ListIncludeVersionsResponse()
        if isinstance(result, dict):
            response.include_id = result.get("includeId", "")
            response.include_name = result.get("includeName", "")
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            response.asset_id = result.get("assetId", "")
            response.include_type = result.get("includeType", "")
            versions_data = result.get("versions", {})
            if isinstance(versions_data, dict):
                response.include_versions = models.Versions(
                    items=[
                        _dict_to_include_version(v)
                        for v in versions_data.get("items", [])
                    ]
                )
        return response

    def list_include_version_available_criteria(
        self, params: models.ListAvailableCriteriaRequest
    ) -> models.AvailableCriteriaResponse:
        """List available criteria for an include version.

        See: https://techdocs.akamai.com/property-mgr/reference/
        get-include-version-available-criteria
        """
        logger.debug("ListIncludeVersionAvailableCriteria")

        err = validation.validate_list_available_criteria_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrListIncludeVersionAvailableCriteria}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/includes/{params.include_id}"
            f"/versions/{params.version}/available-criteria"
        )

        resp, result = self._exec("GET", url)
        Session.close_response_body(resp)

        response = models.AvailableCriteriaResponse()
        if isinstance(result, dict):
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            criteria_data = result.get("availableCriteria", {})
            if isinstance(criteria_data, dict):
                response.available_criteria = models.AvailableCriteria(
                    items=[
                        models.Criteria(
                            name=c.get("name", ""),
                            schema_link=c.get("schemaLink", ""),
                        )
                        for c in criteria_data.get("items", [])
                    ]
                )
        return response

    def list_include_version_available_behaviors(
        self, params: models.ListAvailableBehaviorsRequest
    ) -> models.AvailableBehaviorsResponse:
        """List available behaviors for an include version.

        See: https://techdocs.akamai.com/property-mgr/reference/
        get-include-version-available-behaviors
        """
        logger.debug("ListIncludeVersionAvailableBehaviors")

        err = validation.validate_list_available_behaviors_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrListIncludeVersionAvailableBehaviors}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/includes/{params.include_id}"
            f"/versions/{params.version}/available-behaviors"
        )

        resp, result = self._exec("GET", url)
        Session.close_response_body(resp)

        response = models.AvailableBehaviorsResponse()
        if isinstance(result, dict):
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            beh_data = result.get("availableBehaviors", {})
            if isinstance(beh_data, dict):
                response.available_behaviors = models.AvailableBehaviors(
                    items=[
                        models.Behavior(
                            name=b.get("name", ""),
                            schema_link=b.get("schemaLink", ""),
                        )
                        for b in beh_data.get("items", [])
                    ]
                )
        return response

    # ------------------------------------------------------------------
    # Products  (products.go)
    # ------------------------------------------------------------------

    def get_products(
        self, params: models.GetProductsRequest
    ) -> models.GetProductsResponse:
        """List products for a contract.

        See: https://techdocs.akamai.com/property-mgr/reference/get-products
        """
        logger.debug("GetProducts")

        err = validation.validate_get_products_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetProducts}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = "/papi/v1/products"
        query_params: dict[str, str] = {
            "contractId": params.contract_id,
        }

        resp, result = self._exec("GET", url, params=query_params)
        Session.close_response_body(resp)

        response = models.GetProductsResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            prod_data = result.get("products", {})
            if isinstance(prod_data, dict):
                response.products = models.ProductsItems(
                    items=[
                        models.ProductItem(
                            product_name=p.get("productName", ""),
                            product_id=p.get("productId", ""),
                        )
                        for p in prod_data.get("items", [])
                    ]
                )
        return response

    # ------------------------------------------------------------------
    # Properties  (property.go)
    # ------------------------------------------------------------------

    def get_properties(
        self, params: models.GetPropertiesRequest
    ) -> models.GetPropertiesResponse:
        """List properties for a contract and group.

        See: https://techdocs.akamai.com/property-mgr/reference/get-properties
        """
        logger.debug("GetProperties")

        err = validation.validate_get_properties_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetProperties}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = "/papi/v1/properties"
        query_params: dict[str, str] = {
            "contractId": params.contract_id,
            "groupId": params.group_id,
        }

        resp, result = self._exec("GET", url, params=query_params)
        Session.close_response_body(resp)

        response = models.GetPropertiesResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            prop_data = result.get("properties", {})
            if isinstance(prop_data, dict):
                response.properties = models.PropertiesItems(
                    items=[
                        _dict_to_property(p)
                        for p in prop_data.get("items", [])
                    ]
                )
        return response

    def create_property(
        self, params: models.CreatePropertyRequest
    ) -> models.CreatePropertyResponse:
        """Create a new property.

        See: https://techdocs.akamai.com/property-mgr/reference/post-properties
        """
        logger.debug("CreateProperty")

        err = validation.validate_create_property_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrCreateProperty}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = "/papi/v1/properties"
        query_params: dict[str, str] = {
            "contractId": params.contract_id,
            "groupId": params.group_id,
        }

        resp, result = self._exec(
            "POST", url, body=_to_body(params.property),
            params=query_params,
        )
        Session.close_response_body(resp)

        response = models.CreatePropertyResponse()
        if isinstance(result, dict):
            response.property_link = result.get("propertyLink", "")
        response.property_id, _ = models.response_link_parse(
            response.property_link
        )
        return response

    def get_property(
        self, params: models.GetPropertyRequest
    ) -> models.GetPropertyResponse:
        """Get details of a specific property.

        See: https://techdocs.akamai.com/property-mgr/reference/get-property
        """
        logger.debug("GetProperty")

        err = validation.validate_get_property_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetProperty}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = f"/papi/v1/properties/{params.property_id}"
        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id

        resp, result = self._exec("GET", url, params=query_params or None)
        Session.close_response_body(resp)

        response = models.GetPropertyResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            prop_data = result.get("properties", {})
            if isinstance(prop_data, dict):
                items = prop_data.get("items", [])
                if items:
                    response.property = _dict_to_property(items[0])
        return response

    def remove_property(
        self, params: models.RemovePropertyRequest
    ) -> models.RemovePropertyResponse:
        """Remove a property.

        See: https://techdocs.akamai.com/property-mgr/reference/delete-property
        """
        logger.debug("RemoveProperty")

        err = validation.validate_remove_property_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrRemoveProperty}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = f"/papi/v1/properties/{params.property_id}"
        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id

        resp, result = self._exec(
            "DELETE", url, params=query_params or None
        )
        Session.close_response_body(resp)

        response = models.RemovePropertyResponse()
        if isinstance(result, dict):
            response.message = result.get("message", "")
        return response

    def map_property_name_to_id(
        self, params: models.MapPropertyNameToIDRequest
    ) -> str | None:
        """Map a property name to its property ID.

        Mirrors Go ``MapPropertyNameToID`` which uses SearchProperties
        internally.

        See: https://techdocs.akamai.com/property-mgr/reference/post-search-find-by-value
        """
        logger.debug("MapPropertyNameToID")

        err = validation.validate_map_property_name_to_id_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrMapPropertyNameToID}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        search_req = models.SearchRequest(
            key=models.SearchKeyPropertyName,
            value=params.name,
        )

        search_resp = self.search_properties(search_req)

        if search_resp.versions and search_resp.versions.items:
            for item in search_resp.versions.items:
                if (
                    item.contract_id == params.contract_id
                    and item.group_id == params.group_id
                ):
                    return item.property_id

        raise errors.Error(
            title=f"{errors.ErrNoProperty}",
            detail=f"no property found for name '{params.name}'",
            status_code=0,
        )

    # ------------------------------------------------------------------
    # Property Rules  (rule.go)
    # ------------------------------------------------------------------

    def get_rule_tree(
        self, params: models.GetRuleTreeRequest
    ) -> models.GetRuleTreeResponse:
        """Get the rule tree for a property version.

        See: https://techdocs.akamai.com/property-mgr/reference/get-property-version-rules
        """
        logger.debug("GetRuleTree")

        err = validation.validate_get_rule_tree_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetRuleTree}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/properties/{params.property_id}"
            f"/versions/{params.property_version}/rules"
        )
        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id
        if params.validate_mode:
            query_params["validateMode"] = params.validate_mode
        if params.validate_rules is False:
            query_params["validateRules"] = "false"

        headers: dict[str, str] = {}
        if params.rule_format:
            accept = (
                f"application/vnd.akamai.papirules."
                f"{params.rule_format}+json"
            )
            headers["Accept"] = accept
            headers["Content-Type"] = accept

        resp, result = self._exec(
            "GET", url, headers=headers or None,
            params=query_params or None,
        )
        Session.close_response_body(resp)

        response = models.GetRuleTreeResponse()
        if isinstance(result, dict):
            _populate_rule_tree_response(response, result)
            # Extract ruleFormat from response header if not in body
            if not response.rule_format:
                ct = resp.headers.get("Content-Type", "")
                if "papirules." in ct:
                    # Extract ruleFormat from content-type header
                    parts = ct.split("papirules.")
                    if len(parts) > 1:
                        response.rule_format = parts[1].split("+")[0]
        return response

    def update_rule_tree(
        self, params: models.UpdateRulesRequest
    ) -> models.UpdateRulesResponse:
        """Update the rule tree for a property version.

        See: https://techdocs.akamai.com/property-mgr/reference/put-property-version-rules
        """
        logger.debug("UpdateRuleTree")

        err = validation.validate_update_rules_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrUpdateRuleTree}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/properties/{params.property_id}"
            f"/versions/{params.property_version}/rules"
        )
        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id
        if params.validate_mode:
            query_params["validateMode"] = params.validate_mode
        if getattr(params, "dry_run", False):
            query_params["dryRun"] = "true"

        headers: dict[str, str] = {}
        if params.rule_format:
            accept = (
                f"application/vnd.akamai.papirules."
                f"{params.rule_format}+json"
            )
            headers["Accept"] = accept
            headers["Content-Type"] = accept

        resp, result = self._exec(
            "PUT", url, body=_to_body(params.rules),
            headers=headers or None,
            params=query_params or None,
        )
        Session.close_response_body(resp)

        response = models.UpdateRulesResponse()
        if isinstance(result, dict):
            _populate_rule_tree_response(response, result)
        return response

    # ------------------------------------------------------------------
    # Property Hostnames  (propertyhostname.go)
    # ------------------------------------------------------------------

    def get_property_version_hostnames(
        self, params: models.GetPropertyVersionHostnamesRequest
    ) -> models.GetPropertyVersionHostnamesResponse:
        """Get hostnames for a property version.

        See: https://techdocs.akamai.com/property-mgr/reference/get-property-version-hostnames
        """
        logger.debug("GetPropertyVersionHostnames")

        err = validation.validate_get_property_version_hostnames_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetPropertyVersionHostnames}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/properties/{params.property_id}"
            f"/versions/{params.property_version}/hostnames"
        )
        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id
        if getattr(params, "validate_hostnames", False):
            query_params["validateHostnames"] = "true"
        if getattr(params, "include_cert_status", False):
            query_params["includeCertStatus"] = "true"

        resp, result = self._exec(
            "GET", url, params=query_params or None,
        )
        Session.close_response_body(resp)

        response = models.GetPropertyVersionHostnamesResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            response.property_id = result.get("propertyId", "")
            response.property_version = result.get("propertyVersion", 0)
            response.etag = result.get("etag", "")
            host_data = result.get("hostnames", {})
            if isinstance(host_data, dict):
                response.hostnames = models.HostnameResponseItems(
                    items=[
                        _dict_to_hostname(h)
                        for h in host_data.get("items", [])
                    ]
                )
        return response

    def update_property_version_hostnames(
        self, params: models.UpdatePropertyVersionHostnamesRequest
    ) -> models.UpdatePropertyVersionHostnamesResponse:
        """Update hostnames for a property version.

        See: https://techdocs.akamai.com/property-mgr/reference/put-property-version-hostnames
        """
        logger.debug("UpdatePropertyVersionHostnames")

        err = validation.validate_update_property_version_hostnames_request(
            params
        )
        if err:
            raise errors.Error(
                title=f"{errors.ErrUpdatePropertyVersionHostnames}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/properties/{params.property_id}"
            f"/versions/{params.property_version}/hostnames"
        )
        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id
        if getattr(params, "validate_hostnames", False):
            query_params["validateHostnames"] = "true"
        if getattr(params, "include_cert_status", False):
            query_params["includeCertStatus"] = "true"

        # Default to empty list if hostnames is None
        hostnames = params.hostnames if params.hostnames is not None else []
        body = [_to_body(h) for h in hostnames]

        resp, result = self._exec(
            "PUT", url, body=body, params=query_params or None,
        )
        Session.close_response_body(resp)

        response = models.UpdatePropertyVersionHostnamesResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            response.property_id = result.get("propertyId", "")
            response.property_version = result.get("propertyVersion", 0)
            response.etag = result.get("etag", "")
            host_data = result.get("hostnames", {})
            if isinstance(host_data, dict):
                response.hostnames = models.HostnameResponseItems(
                    items=[
                        _dict_to_hostname(h)
                        for h in host_data.get("items", [])
                    ]
                )
        return response

    def patch_property_version_hostnames(
        self, params: models.PatchPropertyVersionHostnamesRequest
    ) -> models.PatchPropertyVersionHostnamesResponse:
        """Patch hostnames for a property version.

        See: https://techdocs.akamai.com/property-mgr/reference/patch-property-version-hostnames
        """
        logger.debug("PatchPropertyVersionHostnames")

        err = validation.validate_patch_property_version_hostnames_request(
            params
        )
        if err:
            raise errors.Error(
                title=f"{errors.ErrPatchPropertyVersionHostnames}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/properties/{params.property_id}"
            f"/versions/{params.property_version}/hostnames"
        )
        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id
        if getattr(params, "validate_hostnames", False):
            query_params["validateHostnames"] = "true"
        if getattr(params, "include_cert_status", False):
            query_params["includeCertStatus"] = "true"

        resp, result = self._exec(
            "PATCH", url, body=_to_body(params.body),
            params=query_params or None,
        )
        Session.close_response_body(resp)

        response = models.PatchPropertyVersionHostnamesResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            response.property_id = result.get("propertyId", "")
            response.property_version = result.get("propertyVersion", 0)
            response.etag = result.get("etag", "")
            host_data = result.get("hostnames", {})
            if isinstance(host_data, dict):
                response.hostnames = models.HostnameResponseItems(
                    items=[
                        _dict_to_hostname(h)
                        for h in host_data.get("items", [])
                    ]
                )
        return response

    def get_audit_history(
        self, params: models.GetAuditHistoryRequest
    ) -> models.GetAuditHistoryResponse:
        """Get hostname audit history.

        See: https://techdocs.akamai.com/property-mgr/reference/get-hostname-audit-history
        """
        logger.debug("GetAuditHistory")

        err = validation.validate_get_audit_history_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetAuditHistory}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = f"/papi/v1/hostnames/{params.hostname}/audit-history"

        resp, result = self._exec("GET", url)
        Session.close_response_body(resp)

        response = models.GetAuditHistoryResponse()
        if isinstance(result, dict):
            response.hostname = result.get("hostname", "")
            history_data = result.get("history", {})
            if isinstance(history_data, dict):
                response.history = models.HostnameHistory(
                    items=[
                        _dict_to_hostname_history_item(h)
                        for h in history_data.get("items", [])
                    ]
                )
        return response

    # ------------------------------------------------------------------
    # Property Versions  (propertyversion.go)
    # ------------------------------------------------------------------

    def get_property_versions(
        self, params: models.GetPropertyVersionsRequest
    ) -> models.GetPropertyVersionsResponse:
        """List versions of a property.

        See: https://techdocs.akamai.com/property-mgr/reference/get-property-versions
        """
        logger.debug("GetPropertyVersions")

        err = validation.validate_get_property_versions_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetPropertyVersions}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = f"/papi/v1/properties/{params.property_id}/versions"
        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id
        if getattr(params, "limit", 0):
            query_params["limit"] = str(params.limit)
        if getattr(params, "offset", 0):
            query_params["offset"] = str(params.offset)

        resp, result = self._exec("GET", url, params=query_params or None)
        Session.close_response_body(resp)

        response = models.GetPropertyVersionsResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            response.property_id = result.get("propertyId", "")
            response.property_name = result.get("propertyName", "")
            versions_data = result.get("versions", {})
            if isinstance(versions_data, dict):
                response.versions = models.PropertyVersionItems(
                    items=[
                        _dict_to_property_version(v)
                        for v in versions_data.get("items", [])
                    ]
                )
        return response

    def get_property_version(
        self, params: models.GetPropertyVersionRequest
    ) -> models.GetPropertyVersionsResponse:
        """Get details of a specific property version.

        See: https://techdocs.akamai.com/property-mgr/reference/get-property-version
        """
        logger.debug("GetPropertyVersion")

        err = validation.validate_get_property_version_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetPropertyVersion}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/properties/{params.property_id}"
            f"/versions/{params.property_version}"
        )
        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id

        resp, result = self._exec("GET", url, params=query_params or None)
        Session.close_response_body(resp)

        response = models.GetPropertyVersionsResponse()
        if isinstance(result, dict):
            response.property_id = result.get("propertyId", "")
            response.property_name = result.get("propertyName", "")
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            response.asset_id = result.get("assetId", "")
            versions_data = result.get("versions", {})
            if isinstance(versions_data, dict):
                items = versions_data.get("items", [])
                response.versions = models.PropertyVersionItems(
                    items=[
                        _dict_to_property_version(v) for v in items
                    ]
                )
        return response

    def create_property_version(
        self, params: models.CreatePropertyVersionRequest
    ) -> models.CreatePropertyVersionResponse:
        """Create a new property version.

        See: https://techdocs.akamai.com/property-mgr/reference/post-property-versions
        """
        logger.debug("CreatePropertyVersion")

        err = validation.validate_create_property_version_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrCreatePropertyVersion}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = f"/papi/v1/properties/{params.property_id}/versions"

        resp, result = self._exec(
            "POST", url, body=_to_body(params.version)
        )
        Session.close_response_body(resp)

        response = models.CreatePropertyVersionResponse()
        if isinstance(result, dict):
            response.version_link = result.get("versionLink", "")
        return response

    def get_latest_version(
        self, params: models.GetLatestVersionRequest
    ) -> models.GetPropertyVersionsResponse:
        """Get the latest version of a property.

        See: https://techdocs.akamai.com/property-mgr/reference/get-latest-property-version
        """
        logger.debug("GetLatestVersion")

        err = validation.validate_get_latest_version_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetLatestVersion}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = f"/papi/v1/properties/{params.property_id}/versions/latest"
        query_params: dict[str, str] = {}
        if params.activated_on:
            query_params["activatedOn"] = params.activated_on
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id

        resp, result = self._exec("GET", url, params=query_params or None)
        Session.close_response_body(resp)

        response = models.GetPropertyVersionsResponse()
        if isinstance(result, dict):
            response.property_id = result.get("propertyId", "")
            response.property_name = result.get("propertyName", "")
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            response.asset_id = result.get("assetId", "")
            versions_data = result.get("versions", {})
            if isinstance(versions_data, dict):
                items = versions_data.get("items", [])
                response.versions = models.PropertyVersionItems(
                    items=[
                        _dict_to_property_version(v) for v in items
                    ]
                )
        return response

    def get_available_behaviors(
        self, params: models.GetAvailableBehaviorsRequest
    ) -> models.GetBehaviorsResponse:
        """Get available behaviors for a property version.

        See: https://techdocs.akamai.com/property-mgr/reference/get-available-behaviors
        """
        logger.debug("GetAvailableBehaviors")

        err = validation.validate_get_available_behaviors_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetAvailableBehaviors}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/properties/{params.property_id}"
            f"/versions/{params.property_version}/available-behaviors"
        )
        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id

        resp, result = self._exec("GET", url, params=query_params or None)
        Session.close_response_body(resp)

        response = models.GetBehaviorsResponse()
        if isinstance(result, dict):
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            beh_data = result.get("behaviors", result.get("availableBehaviors", {}))
            if isinstance(beh_data, dict):
                response.available_behaviors = models.AvailableBehaviors(
                    items=[
                        models.Behavior(
                            name=b.get("name", ""),
                            schema_link=b.get("schemaLink", ""),
                        )
                        for b in beh_data.get("items", [])
                    ]
                )
        return response

    def get_available_criteria(
        self, params: models.GetAvailableCriteriaRequest
    ) -> models.GetCriteriaResponse:
        """Get available criteria for a property version.

        See: https://techdocs.akamai.com/property-mgr/reference/get-available-criteria
        """
        logger.debug("GetAvailableCriteria")

        err = validation.validate_get_available_criteria_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetAvailableCriteria}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/properties/{params.property_id}"
            f"/versions/{params.property_version}/available-criteria"
        )
        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id

        resp, result = self._exec("GET", url, params=query_params or None)
        Session.close_response_body(resp)

        response = models.GetCriteriaResponse()
        if isinstance(result, dict):
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            crit_data = result.get(
                "criteria", result.get("availableCriteria", {})
            )
            if isinstance(crit_data, dict):
                response.available_criteria = models.AvailableCriteria(
                    items=[
                        models.Criteria(
                            name=c.get("name", ""),
                            schema_link=c.get("schemaLink", ""),
                        )
                        for c in crit_data.get("items", [])
                    ]
                )
        return response

    def list_available_includes(
        self, params: models.ListAvailableIncludesRequest
    ) -> models.ListAvailableIncludesResponse:
        """List available includes for a property version.

        Uses the ``/external-resources`` endpoint.
        Mirrors Go ListAvailableIncludes which uses custom JSON
        unmarshalling to transform a map into an array.

        See: https://techdocs.akamai.com/property-mgr/reference/get-external-resources
        """
        logger.debug("ListAvailableIncludes")

        err = validation.validate_list_available_includes_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrListAvailableIncludes}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/properties/{params.property_id}"
            f"/versions/{params.property_version}/external-resources"
        )
        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id

        resp, result = self._exec("GET", url, params=query_params or None)
        Session.close_response_body(resp)

        response = models.ListAvailableIncludesResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            # Go uses custom UnmarshalJSON that converts map→array
            includes_map = result.get("externalResources", {})
            if isinstance(includes_map, dict):
                inc_list = []
                for _, v in includes_map.items():
                    if isinstance(v, dict):
                        inc_list.append(
                            models.ExternalIncludeData(
                                include_id=v.get("includeId", ""),
                                include_name=v.get("includeName", ""),
                                include_type=v.get("includeType", ""),
                                file_name=v.get("fileName", ""),
                            )
                        )
                response.available_includes = inc_list
            elif isinstance(includes_map, list):
                response.available_includes = [
                    models.ExternalIncludeData(
                        include_id=v.get("includeId", ""),
                        include_name=v.get("includeName", ""),
                        include_type=v.get("includeType", ""),
                        file_name=v.get("fileName", ""),
                    )
                    for v in includes_map
                    if isinstance(v, dict)
                ]
        return response

    def list_referenced_includes(
        self, params: models.ListReferencedIncludesRequest
    ) -> models.ListReferencedIncludesResponse:
        """List referenced includes for a property version.

        See: https://techdocs.akamai.com/property-mgr/reference/get-referenced-includes
        """
        logger.debug("ListReferencedIncludes")

        err = validation.validate_list_referenced_includes_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrListReferencedIncludes}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/properties/{params.property_id}"
            f"/versions/{params.property_version}/includes"
        )
        query_params: dict[str, str] = {
            "contractId": params.contract_id,
            "groupId": params.group_id,
        }

        resp, result = self._exec("GET", url, params=query_params)
        Session.close_response_body(resp)

        response = models.ListReferencedIncludesResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            inc_data = result.get("includes", {})
            if isinstance(inc_data, dict):
                response.includes = models.IncludeItems(
                    items=[
                        _dict_to_include(i)
                        for i in inc_data.get("items", [])
                    ]
                )
        return response

    # ------------------------------------------------------------------
    # Rule Formats  (ruleformats.go)
    # ------------------------------------------------------------------

    def get_rule_formats(self) -> models.GetRuleFormatsResponse:
        """List all available rule formats.

        See: https://techdocs.akamai.com/property-mgr/reference/get-rule-formats
        """
        logger.debug("GetRuleFormats")

        url = "/papi/v1/rule-formats"
        resp, result = self._exec("GET", url)
        Session.close_response_body(resp)

        if resp.status_code != 200:
            err = self._parse_error(resp)
            err.title = f"{errors.ErrGetRuleFormats}: {err.title}"
            raise err

        response = models.GetRuleFormatsResponse()
        if isinstance(result, dict):
            rf_data = result.get("ruleFormats", {})
            if isinstance(rf_data, dict):
                response.rule_formats = models.RuleFormatItems(
                    items=rf_data.get("items", [])
                )
        return response

    # ------------------------------------------------------------------
    # Search  (search.go)
    # ------------------------------------------------------------------

    def search_properties(
        self, params: models.SearchRequest
    ) -> models.SearchResponse:
        """Search for properties by hostname, edge hostname, or property name.

        See: https://techdocs.akamai.com/property-mgr/reference/post-search-find-by-value
        """
        logger.debug("SearchProperties")

        err = validation.validate_search_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrSearchProperties}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = "/papi/v1/search/find-by-value"
        body = {params.key: params.value}

        resp, result = self._exec("POST", url, body=body)
        Session.close_response_body(resp)

        response = models.SearchResponse()
        if isinstance(result, dict):
            versions_data = result.get("versions", {})
            if isinstance(versions_data, dict):
                response.versions = models.SearchItems(
                    items=[
                        _dict_to_search_item(s)
                        for s in versions_data.get("items", [])
                    ]
                )
        return response

    # ------------------------------------------------------------------
    # Hostname Activations  (property_hostname_activation.go)
    # ------------------------------------------------------------------

    def get_property_hostname_activation(
        self, params: models.GetPropertyHostnameActivationRequest
    ) -> models.GetPropertyHostnameActivationResponse:
        """Get a property hostname activation.

        See: https://techdocs.akamai.com/property-mgr/reference/get-hostname-activation
        """
        logger.debug("GetPropertyHostnameActivation")

        err = validation.validate_get_property_hostname_activation_request(
            params
        )
        if err:
            raise errors.Error(
                title=f"{errors.ErrGetPropertyHostnameActivation}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/properties/{params.property_id}"
            f"/hostname-activations/{params.hostname_activation_id}"
        )
        query_params: dict[str, str] = {}
        if params.group_id:
            query_params["groupId"] = params.group_id
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.include_hostnames:
            query_params["includeHostnames"] = "true"

        resp, result = self._exec("GET", url, params=query_params or None)
        Session.close_response_body(resp)

        response = models.GetPropertyHostnameActivationResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            # Unwrap single element from nested hostnameActivations.items
            act_data = result.get("hostnameActivations", {})
            if isinstance(act_data, dict):
                items = act_data.get("items", [])
                if items:
                    response.hostname_activation = (
                        _dict_to_hostname_activation_get_item(items[0])
                    )
        return response

    def list_property_hostname_activations(
        self, params: models.ListPropertyHostnameActivationsRequest
    ) -> models.ListPropertyHostnameActivationsResponse:
        """List property hostname activations.

        See: https://techdocs.akamai.com/property-mgr/reference/get-hostname-activations
        """
        logger.debug("ListPropertyHostnameActivations")

        err = validation.validate_list_property_hostname_activations_request(
            params
        )
        if err:
            raise errors.Error(
                title=f"{errors.ErrListPropertyHostnameActivations}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/properties/{params.property_id}"
            f"/hostname-activations"
        )
        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id
        if params.offset:
            query_params["offset"] = str(params.offset)
        if params.limit:
            query_params["limit"] = str(params.limit)

        resp, result = self._exec("GET", url, params=query_params or None)
        Session.close_response_body(resp)

        response = models.ListPropertyHostnameActivationsResponse()
        if isinstance(result, dict):
            response.account_id = result.get("accountId", "")
            response.contract_id = result.get("contractId", "")
            response.group_id = result.get("groupId", "")
            act_data = result.get("hostnameActivations", {})
            if isinstance(act_data, dict):
                response.hostname_activations = models.HostnameActivationsList(
                    items=[
                        _dict_to_hostname_activation_list_item(a)
                        for a in act_data.get("items", [])
                    ],
                    total_items=act_data.get("totalItems", 0),
                    current_item_count=act_data.get("currentItemCount", 0),
                    next_link=act_data.get("nextLink"),
                    previous_link=act_data.get("previousLink"),
                )
        return response

    def cancel_property_hostname_activation(
        self, params: models.CancelPropertyHostnameActivationRequest
    ) -> models.CancelPropertyHostnameActivationResponse:
        """Cancel a property hostname activation.

        See: https://techdocs.akamai.com/property-mgr/reference/delete-hostname-activation
        """
        logger.debug("CancelPropertyHostnameActivation")

        err = validation.validate_cancel_property_hostname_activation_request(
            params
        )
        if err:
            raise errors.Error(
                title=f"{errors.ErrCancelPropertyHostnameActivation}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = (
            f"/papi/v1/properties/{params.property_id}"
            f"/hostname-activations/{params.hostname_activation_id}"
        )
        query_params: dict[str, str] = {}
        if params.group_id:
            query_params["groupId"] = params.group_id
        if params.contract_id:
            query_params["contractId"] = params.contract_id

        resp, _ = self._exec(
            "DELETE", url, params=query_params or None,
            expect_json=False,
        )

        # 204 No Content means already aborted
        if resp.status_code == 204:
            Session.close_response_body(resp)
            raise errors.Error(
                title=errors.ErrCancelPropertyHostnameActivationAlreadyAborted,
                detail="activation already aborted",
                status_code=204,
            )

        # Re-read body as JSON for non-204
        result_data = None
        try:
            result_data = resp.json()
        except (json.JSONDecodeError, ValueError):
            pass
        Session.close_response_body(resp)

        response = models.CancelPropertyHostnameActivationResponse()
        if isinstance(result_data, dict):
            response.account_id = result_data.get("accountId", "")
            response.contract_id = result_data.get("contractId", "")
            response.group_id = result_data.get("groupId", "")
            act_data = result_data.get("hostnameActivations", {})
            if isinstance(act_data, dict):
                items = act_data.get("items", [])
                if items:
                    response.hostname_activation = (
                        _dict_to_hostname_activation_cancel_item(items[0])
                    )
        return response

    # ------------------------------------------------------------------
    # Hostname Bucket  (property_hostname_bucket.go)
    # ------------------------------------------------------------------

    def patch_property_hostname_bucket(
        self, params: models.PatchPropertyHostnameBucketRequest
    ) -> models.PatchPropertyHostnameBucketResponse:
        """Patch property hostname bucket (add/remove hostnames).

        See: https://techdocs.akamai.com/property-mgr/reference/patch-property-hostnames
        """
        logger.debug("PatchPropertyHostnameBucket")

        err = validation.validate_patch_property_hostname_bucket_request(params)
        if err:
            raise errors.Error(
                title=f"{errors.ErrPatchPropertyHostnameBucket}",
                detail=f"{errors.ErrStructValidation}: {err}",
                status_code=0,
            )

        url = f"/papi/v1/properties/{params.property_id}/hostnames"
        query_params: dict[str, str] = {}
        if params.contract_id:
            query_params["contractId"] = params.contract_id
        if params.group_id:
            query_params["groupId"] = params.group_id

        body = _to_body(getattr(params, "body", None))

        resp, result = self._exec(
            "PATCH", url, body=body, params=query_params or None,
        )
        Session.close_response_body(resp)

        response = models.PatchPropertyHostnameBucketResponse()
        if isinstance(result, dict):
            response.activation_link = result.get("activationLink", "")
            response.hostnames = [
                _dict_to_patch_hostname_item(h)
                for h in result.get("hostnames", [])
            ]
        response.activation_id, _ = models.response_link_parse(
            response.activation_link
        )
        return response


# =========================================================================
# Module-level helper functions for response deserialization
# =========================================================================

def _dict_to_activation(data: dict) -> models.Activation:
    """Convert a JSON dict to an Activation model."""
    act = models.Activation()
    act.account_id = data.get("accountId", "")
    act.activation_id = data.get("activationId", "")
    act.activation_type = data.get("activationType", "")
    act.use_fast_fallback = data.get("useFastFallback", False)
    act.fallback_info = data.get("fallbackInfo")
    act.acknowledge_warnings = data.get("acknowledgeWarnings", [])
    act.acknowledge_all_warnings = data.get("acknowledgeAllWarnings", False)
    act.fast_push = data.get("fastPush", False)
    act.fma_activation_state = data.get("fmaActivationState", "")
    act.group_id = data.get("groupId", "")
    act.ignore_http_errors = data.get("ignoreHttpErrors", False)
    act.property_name = data.get("propertyName", "")
    act.property_id = data.get("propertyId", "")
    act.property_version = data.get("propertyVersion", 0)
    act.network = data.get("network", "")
    act.status = data.get("status", "")
    act.submit_date = data.get("submitDate", "")
    act.update_date = data.get("updateDate", "")
    act.note = data.get("note", "")
    act.notify_emails = data.get("notifyEmails", [])
    act.compliance_record = data.get("complianceRecord")
    return act


def _dict_to_property(data: dict) -> models.Property:
    """Convert a JSON dict to a Property model."""
    item = models.Property()
    item.account_id = data.get("accountId", "")
    item.asset_id = data.get("assetId", "")
    item.contract_id = data.get("contractId", "")
    item.group_id = data.get("groupId", "")
    item.latest_version = data.get("latestVersion", 0)
    item.note = data.get("note", "")
    item.production_version = data.get("productionVersion")
    item.property_id = data.get("propertyId", "")
    item.property_name = data.get("propertyName", "")
    item.staging_version = data.get("stagingVersion")
    item.property_type = data.get("propertyType")
    return item


def _dict_to_contract(data: dict) -> models.Contract:
    """Convert a JSON dict to a Contract model."""
    item = models.Contract()
    item.contract_id = data.get("contractId", "")
    item.contract_type_name = data.get("contractTypeName", "")
    return item


def _dict_to_group(data: dict) -> models.Group:
    """Convert a JSON dict to a GroupItem model."""
    item = models.Group()
    item.group_name = data.get("groupName", "")
    item.group_id = data.get("groupId", "")
    item.parent_group_id = data.get("parentGroupId")
    item.contract_ids = data.get("contractIds", [])
    return item


def _dict_to_cp_code(data: dict) -> models.CPCode:
    """Convert a JSON dict to a CPCode model."""
    item = models.CPCode()
    item.cp_code_id = data.get("cpcodeId", "")
    item.cp_code_name = data.get("cpcodeName", "")
    item.product_ids = data.get("productIds", [])
    item.created_date = data.get("createdDate", "")
    return item


def _populate_cp_code_detail(response, data: dict) -> None:
    """Populate CPCodeDetailResponse from a JSON dict."""
    response.id = data.get("id", 0)
    response.name = data.get("name", "")
    response.purgeable = data.get("purgeable", False)
    response.account_id = data.get("accountId", "")
    response.default_time_zone = data.get("defaultTimeZone", "")
    response.type = data.get("type", "")
    override_tz = data.get("overrideTimeZone")
    if isinstance(override_tz, dict):
        response.override_time_zone = models.CPCodeTimeZone(
            timezone_id=override_tz.get("timezoneId", ""),
            timezone_value=override_tz.get("timezoneValue", ""),
        )
    else:
        response.override_time_zone = override_tz
    contracts = data.get("contracts", [])
    response.contracts = [
        models.CPCodeContract(
            contract_id=c.get("contractId", ""),
            status=c.get("status", ""),
        ) if isinstance(c, dict) else c
        for c in contracts
    ]
    products = data.get("products", [])
    response.products = [
        models.CPCodeProduct(
            product_id=p.get("productId", ""),
            product_name=p.get("productName", ""),
        ) if isinstance(p, dict) else p
        for p in products
    ]


def _dict_to_edge_hostname(data: dict) -> models.EdgeHostnameGetItem:
    """Convert a JSON dict to an EdgeHostnameGetItem model."""
    item = models.EdgeHostnameGetItem()
    item.id = data.get("edgeHostnameId", "")
    item.domain = data.get("edgeHostnameDomain", "")
    item.product_id = data.get("productId", "")
    item.domain_prefix = data.get("domainPrefix", "")
    item.domain_suffix = data.get("domainSuffix", "")
    item.secure = data.get("secure", False)
    item.ip_version_behavior = data.get("ipVersionBehavior", "")
    item.status = data.get("status", "")
    item.use_cases = data.get("useCases", [])
    return item


def _dict_to_search_item(data: dict) -> models.SearchItem:
    """Convert a JSON dict to a SearchItem model."""
    item = models.SearchItem()
    item.account_id = data.get("accountId", "")
    item.asset_id = data.get("assetId", "")
    item.contract_id = data.get("contractId", "")
    item.group_id = data.get("groupId", "")
    item.edge_hostname = data.get("edgeHostname", "")
    item.hostname = data.get("hostname", "")
    item.production_status = data.get("productionStatus", "")
    item.property_id = data.get("propertyId", "")
    item.property_name = data.get("propertyName", "")
    item.property_version = data.get("propertyVersion", 0)
    item.staging_status = data.get("stagingStatus", "")
    item.updated_by_user = data.get("updatedByUser", "")
    item.updated_date = data.get("updatedDate", "")
    return item


def _dict_to_include(data: dict) -> models.Include:
    """Convert a JSON dict to an Include model."""
    item = models.Include()
    item.account_id = data.get("accountId", "")
    item.asset_id = data.get("assetId", "")
    item.contract_id = data.get("contractId", "")
    item.group_id = data.get("groupId", "")
    item.include_id = data.get("includeId", "")
    item.include_name = data.get("includeName", "")
    item.include_type = data.get("includeType", "")
    item.latest_version = data.get("latestVersion", 0)
    item.staging_version = data.get("stagingVersion")
    item.production_version = data.get("productionVersion")
    return item


def _dict_to_parent_property(data: dict) -> models.ParentProperty:
    """Convert a JSON dict to a ParentProperty model."""
    item = models.ParentProperty()
    item.account_id = data.get("accountId", "")
    item.asset_id = data.get("assetId", "")
    item.contract_id = data.get("contractId", "")
    item.group_id = data.get("groupId", "")
    item.production_version = data.get("productionVersion")
    item.property_id = data.get("propertyId", "")
    item.property_name = data.get("propertyName", "")
    item.staging_version = data.get("stagingVersion")
    return item


def _dict_to_include_activation(data: dict) -> models.IncludeActivation:
    """Convert a JSON dict to an IncludeActivation model."""
    item = models.IncludeActivation()
    item.activation_id = data.get("activationId", "")
    item.network = data.get("network", "")
    item.activation_type = data.get("activationType", "")
    item.status = data.get("status", "")
    item.submit_date = data.get("submitDate", "")
    item.update_date = data.get("updateDate", "")
    item.note = data.get("note", "")
    item.notify_emails = data.get("notifyEmails", [])
    item.fma_activation_state = data.get("fmaActivationState", "")
    item.fallback_info = data.get("fallbackInfo")
    item.include_id = data.get("includeId", "")
    item.include_name = data.get("includeName", "")
    item.include_type = data.get("includeType", "")
    item.include_version = data.get("includeVersion", 0)
    return item


def _dict_to_include_version(data: dict) -> models.IncludeVersion:
    """Convert a JSON dict to an IncludeVersion model."""
    item = models.IncludeVersion()
    item.include_version = data.get("includeVersion", 0)
    item.updated_by_user = data.get("updatedByUser", "")
    item.updated_date = data.get("updatedDate", "")
    item.production_status = data.get("productionStatus", "")
    item.staging_status = data.get("stagingStatus", "")
    item.etag = data.get("etag", "")
    item.note = data.get("note", "")
    return item


def _dict_to_rule_behavior(data: dict) -> models.RuleBehavior:
    """Convert a JSON dict to a RuleBehavior model."""
    return models.RuleBehavior(
        locked=data.get("locked", False),
        name=data.get("name", ""),
        options=data.get("options", {}),
        uuid=data.get("uuid", ""),
        template_uuid=data.get("templateUuid", ""),
    )


def _dict_to_rule_variable(data: dict) -> models.RuleVariable:
    """Convert a JSON dict to a RuleVariable model."""
    return models.RuleVariable(
        description=data.get("description"),
        hidden=data.get("hidden", False),
        name=data.get("name", ""),
        sensitive=data.get("sensitive", False),
        value=data.get("value"),
    )


def _dict_to_rules(data: dict) -> models.Rules:
    """Convert a JSON dict to a Rules model."""
    rules = models.Rules()
    rules.name = data.get("name", "")
    rules.criteria_locked = data.get("criteriaLocked", False)
    rules.criteria_must_satisfy = data.get("criteriaMustSatisfy", "")
    rules.options = data.get("options")
    rules.behaviors = [
        _dict_to_rule_behavior(b)
        for b in data.get("behaviors", [])
        if isinstance(b, dict)
    ]
    rules.criteria = [
        _dict_to_rule_behavior(c)
        for c in data.get("criteria", [])
        if isinstance(c, dict)
    ]
    rules.children = [
        _dict_to_rules(ch)
        for ch in data.get("children", [])
        if isinstance(ch, dict)
    ]
    rules.variables = [
        _dict_to_rule_variable(v)
        for v in data.get("variables", [])
        if isinstance(v, dict)
    ]
    rules.comments = data.get("comments", "")
    rules.custom_override = data.get("customOverride")
    rules.uuid = data.get("uuid", "")
    rules.template_uuid = data.get("templateUuid", "")
    rules.template_link = data.get("templateLink", "")
    rules.advanced_override = data.get("advancedOverride", "")
    return rules


def _populate_rule_tree_response(response, data: dict) -> None:
    """Populate a rule tree response (GetRuleTreeResponse or UpdateRulesResponse)."""
    response.account_id = data.get("accountId", "")
    response.contract_id = data.get("contractId", "")
    response.group_id = data.get("groupId", "")
    response.property_id = data.get("propertyId", "")
    response.property_name = data.get("propertyName", "")
    response.property_version = data.get("propertyVersion", 0)
    response.etag = data.get("etag", "")
    response.rule_format = data.get("ruleFormat", "")
    rules_data = data.get("rules")
    if isinstance(rules_data, dict):
        response.rules = _dict_to_rules(rules_data)
    response.comments = data.get("comments", "")
    errs_data = data.get("errors")
    if errs_data:
        response.errors = errs_data
    warnings_data = data.get("warnings")
    if warnings_data:
        response.warnings = warnings_data


def _dict_to_hostname(data: dict) -> models.Hostname:
    """Convert a JSON dict to a Hostname model."""
    item = models.Hostname()
    item.cname_type = data.get("cnameType", "")
    item.edge_hostname_id = data.get("edgeHostnameId", "")
    item.cname_from = data.get("cnameFrom", "")
    item.cname_to = data.get("cnameTo", "")
    item.cert_provisioning_type = data.get("certProvisioningType", "")
    item.cert_status = data.get("certStatus")
    item.mtls = data.get("mtls")
    item.ccm_certificates = data.get("ccmCertificates")
    item.tls_configuration = data.get("tlsConfiguration")
    item.domain_ownership_verification = data.get("domainOwnershipVerification")
    return item


def _dict_to_property_version(data: dict) -> models.PropertyVersionGetItem:
    """Convert a JSON dict to a PropertyVersionGetItem model."""
    item = models.PropertyVersionGetItem()
    item.property_version = data.get("propertyVersion", 0)
    item.updated_by_user = data.get("updatedByUser", "")
    item.updated_date = data.get("updatedDate", "")
    item.production_status = data.get("productionStatus", "")
    item.staging_status = data.get("stagingStatus", "")
    item.etag = data.get("etag", "")
    item.note = data.get("note", "")
    item.rule_format = data.get("ruleFormat", "")
    return item


def _dict_to_hostname_history_item(data: dict) -> models.HostnameHistoryItem:
    """Convert a JSON dict to a HostnameHistoryItem model."""
    item = models.HostnameHistoryItem()
    item.cname_from = data.get("cnameFrom", "")
    item.cname_to = data.get("cnameTo", "")
    item.cname_type = data.get("cnameType", "")
    item.edge_hostname_id = data.get("edgeHostnameId", "")
    item.cert_provisioning_type = data.get("certProvisioningType", "")
    item.property_id = data.get("propertyId", "")
    item.property_version = data.get("propertyVersion", 0)
    item.activation_type = data.get("activationType", "")
    item.network = data.get("network", "")
    item.active = data.get("active", False)
    item.submit_date = data.get("submitDate", "")
    return item


def _dict_to_hostnames_response_items(
    data: dict,
) -> models.HostnamesResponseItems:
    """Convert a JSON dict to HostnamesResponseItems."""
    return models.HostnamesResponseItems(
        items=[
            _dict_to_hostname_item(h) for h in data.get("items", [])
        ],
        current_item_count=data.get("currentItemCount", 0),
        next_link=data.get("nextLink"),
        previous_link=data.get("previousLink"),
        total_items=data.get("totalItems", 0),
    )


def _dict_to_hostnames_diff_response_items(
    data: dict,
) -> models.HostnamesDiffResponseItems:
    """Convert a JSON dict to HostnamesDiffResponseItems."""
    return models.HostnamesDiffResponseItems(
        items=[
            _dict_to_hostname_diff_item(h) for h in data.get("items", [])
        ],
        current_item_count=data.get("currentItemCount", 0),
        next_link=data.get("nextLink"),
        previous_link=data.get("previousLink"),
        total_items=data.get("totalItems", 0),
    )


def _dict_to_hostname_item(data: dict) -> models.HostnameItem:
    """Convert a JSON dict to a HostnameItem model."""
    item = models.HostnameItem()
    item.ccm_cert_status = data.get("ccmCertStatus")
    item.ccm_certificates = data.get("ccmCertificates")
    item.cert_status = data.get("certStatus")
    item.cname_from = data.get("cnameFrom", "")
    item.cname_type = data.get("cnameType", "")
    item.mtls = data.get("mtls")
    item.production_cert_type = data.get("productionCertType", "")
    item.production_cname_to = data.get("productionCnameTo", "")
    item.production_edge_hostname_id = data.get("productionEdgeHostnameId", "")
    item.staging_cert_type = data.get("stagingCertType", "")
    item.staging_cname_to = data.get("stagingCnameTo", "")
    item.staging_edge_hostname_id = data.get("stagingEdgeHostnameId", "")
    item.tls_configuration = data.get("tlsConfiguration")
    return item


def _dict_to_hostname_diff_item(data: dict) -> models.HostnameDiffItem:
    """Convert a JSON dict to a HostnameDiffItem model."""
    item = models.HostnameDiffItem()
    item.cname_from = data.get("cnameFrom", "")
    item.production_cert_provisioning_type = data.get(
        "productionCertProvisioningType", ""
    )
    item.production_cname_to = data.get("productionCnameTo", "")
    item.production_cname_type = data.get("productionCnameType", "")
    item.production_edge_hostname_id = data.get("productionEdgeHostnameId", "")
    item.staging_cert_provisioning_type = data.get(
        "stagingCertProvisioningType", ""
    )
    item.staging_cname_to = data.get("stagingCnameTo", "")
    item.staging_cname_type = data.get("stagingCnameType", "")
    item.staging_edge_hostname_id = data.get("stagingEdgeHostnameId", "")
    return item


def _dict_to_active_account_hostname_item(
    data: dict,
) -> models.ActiveAccountHostnameItem:
    """Convert a JSON dict to an ActiveAccountHostnameItem model."""
    item = models.ActiveAccountHostnameItem()
    item.cname_from = data.get("cnameFrom", "")
    item.contract_id = data.get("contractId", "")
    item.group_id = data.get("groupId", "")
    item.latest_version = data.get("latestVersion", 0)
    item.property_id = data.get("propertyId", "")
    item.property_name = data.get("propertyName", "")
    item.property_type = data.get("propertyType", "")
    item.production_cert_type = data.get("productionCertType")
    item.production_cname_to = data.get("productionCnameTo")
    item.production_cname_type = data.get("productionCnameType")
    item.production_edge_hostname_id = data.get("productionEdgeHostnameId")
    item.production_product_id = data.get("productionProductId")
    item.staging_cert_type = data.get("stagingCertType")
    item.staging_cname_to = data.get("stagingCnameTo")
    item.staging_cname_type = data.get("stagingCnameType")
    item.staging_edge_hostname_id = data.get("stagingEdgeHostnameId")
    item.staging_product_id = data.get("stagingProductId")
    return item


def _dict_to_hostname_validation_details(
    data: dict,
) -> models.HostnameValidationDetails:
    """Convert a JSON dict to HostnameValidationDetails."""
    item = models.HostnameValidationDetails()
    item.hostname = data.get("hostname", "")
    item.domain_validation_status = data.get("domainValidationStatus", "")
    item.validation_scope = data.get("validationScope")
    item.challenge_token_expiry_date = data.get("challengeTokenExpiryDate")
    vc = data.get("validationCname")
    if isinstance(vc, dict):
        item.validation_cname = models.ValidationCname(
            hostname=vc.get("hostname", ""),
            target=vc.get("target", ""),
        )
    vt = data.get("validationTxt")
    if isinstance(vt, dict):
        item.validation_txt = models.ValidationTXT(
            challenge_token=vt.get("challengeToken", ""),
            hostname=vt.get("hostname", ""),
        )
    vh = data.get("validationHttp")
    if isinstance(vh, dict):
        fcm = vh.get("fileContentMethod")
        rm = vh.get("redirectMethod")
        vhttp = models.ValidationHTTP()
        if isinstance(fcm, dict):
            vhttp.file_content_method = models.FileContentMethod(
                body=fcm.get("body", ""),
                url=fcm.get("url", ""),
            )
        if isinstance(rm, dict):
            vhttp.redirect_method = models.RedirectMethod(
                http_redirect_from=rm.get("httpRedirectFrom", ""),
                http_redirect_to=rm.get("httpRedirectTo", ""),
            )
        item.validation_http = vhttp
    return item


def _dict_to_hostname_activation_get_item(
    data: dict,
) -> models.HostnameActivationGetItem:
    """Convert a JSON dict to HostnameActivationGetItem."""
    item = models.HostnameActivationGetItem()
    item.activation_type = data.get("activationType", "")
    item.hostname_activation_id = data.get("hostnameActivationId", "")
    item.property_name = data.get("propertyName", "")
    item.property_id = data.get("propertyId", "")
    item.network = data.get("network", "")
    item.status = data.get("status", "")
    item.submit_date = data.get("submitDate", "")
    item.update_date = data.get("updateDate", "")
    item.note = data.get("note", "")
    item.notify_emails = data.get("notifyEmails", [])
    item.hostnames = [
        _dict_to_property_hostname_item(h)
        for h in data.get("hostnames", [])
    ]
    return item


def _dict_to_hostname_activation_list_item(
    data: dict,
) -> models.HostnameActivationListItem:
    """Convert a JSON dict to HostnameActivationListItem."""
    item = models.HostnameActivationListItem()
    item.activation_type = data.get("activationType", "")
    item.hostname_activation_id = data.get("hostnameActivationId", "")
    item.property_name = data.get("propertyName", "")
    item.property_id = data.get("propertyId", "")
    item.network = data.get("network", "")
    item.status = data.get("status", "")
    item.submit_date = data.get("submitDate", "")
    item.update_date = data.get("updateDate", "")
    item.note = data.get("note", "")
    item.notify_emails = data.get("notifyEmails", [])
    return item


def _dict_to_hostname_activation_cancel_item(
    data: dict,
) -> models.HostnameActivationCancelItem:
    """Convert a JSON dict to HostnameActivationCancelItem."""
    item = models.HostnameActivationCancelItem()
    item.activation_type = data.get("activationType", "")
    item.hostname_activation_id = data.get("hostnameActivationId", "")
    item.property_name = data.get("propertyName", "")
    item.property_id = data.get("propertyId", "")
    item.network = data.get("network", "")
    item.status = data.get("status", "")
    item.submit_date = data.get("submitDate", "")
    item.update_date = data.get("updateDate", "")
    item.note = data.get("note", "")
    item.notify_emails = data.get("notifyEmails", [])
    item.property_version = data.get("propertyVersion", 0)
    return item


def _dict_to_property_hostname_item(
    data: dict,
) -> models.PropertyHostnameItem:
    """Convert a JSON dict to PropertyHostnameItem."""
    item = models.PropertyHostnameItem()
    item.cert_provisioning_type = data.get("certProvisioningType", "")
    item.cname_from = data.get("cnameFrom", "")
    item.cname_to = data.get("cnameTo", "")
    item.edge_hostname_id = data.get("edgeHostnameId", "")
    item.action = data.get("action", "")
    cs = data.get("certStatus")
    if isinstance(cs, dict):
        item.cert_status = _dict_to_cert_status_item(cs)
    return item


def _dict_to_patch_hostname_item(data: dict) -> models.PatchHostnameItem:
    """Convert a JSON dict to PatchHostnameItem."""
    item = models.PatchHostnameItem()
    item.cert_provisioning_type = data.get("certProvisioningType", "")
    item.cname_from = data.get("cnameFrom", "")
    item.cname_to = data.get("cnameTo", "")
    item.cname_type = data.get("cnameType", "")
    item.edge_hostname_id = data.get("edgeHostnameId", "")
    item.action = data.get("action", "")
    cs = data.get("certStatus")
    if isinstance(cs, dict):
        item.cert_status = _dict_to_cert_status_item(cs)
    return item


def _dict_to_cert_status_item(data: dict) -> models.CertStatusItem:
    """Convert a JSON dict to CertStatusItem."""
    item = models.CertStatusItem()
    vc = data.get("validationCname")
    if isinstance(vc, dict):
        item.validation_cname = models.ValidationCname(
            hostname=vc.get("hostname", ""),
            target=vc.get("target", ""),
        )
    item.staging = data.get("staging", [])
    item.production = data.get("production", [])
    return item


def _build_include_activation_body(params) -> dict:
    """Build the request body for include activation/deactivation.

    Used by both activate_include and deactivate_include.
    """
    body: dict[str, Any] = {
        "includeVersion": params.version,
        "network": params.network,
        "note": getattr(params, "note", ""),
        "notifyEmails": getattr(params, "notify_emails", []),
    }
    act_type = getattr(params, "activation_type", "")
    if act_type:
        body["activationType"] = act_type
    compliance = getattr(params, "compliance_record", None)
    if compliance is not None:
        body["complianceRecord"] = _to_body(compliance)
    return body
