"""Image & Video Manager API client"""

import logging
from typing import Any

from akamai.edgegrid.session import Session
from akamai.edgegrid.errors import ErrStructValidation
from akamai.edgegrid.imaging import errors
from akamai.edgegrid.imaging import validation
from akamai.edgegrid.imaging.models import (
    ListPoliciesRequest,
    ListPoliciesResponse,
    GetPolicyRequest,
    UpsertPolicyRequest,
    DeletePolicyRequest,
    GetPolicyHistoryRequest,
    GetPolicyHistoryResponse,
    RollbackPolicyRequest,
    PolicyResponse,
    ListPolicySetsRequest,
    GetPolicySetRequest,
    CreatePolicySetRequest,
    UpdatePolicySetRequest,
    DeletePolicySetRequest,
    PolicySet,
    PolicyHistoryItem,
    unmarshal_policy_output,
    unmarshal_policy_outputs,
    model_to_dict,
    dict_to_model,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sentinel error strings (mirrors Go var declarations in policy.go
# and policyset.go).  These constants identify the operation that failed
# and are embedded in validation / API error messages to match Go's
# fmt.Errorf("%s: %w", ErrXxx, …) wrapping pattern.
# ---------------------------------------------------------------------------
ERR_LIST_POLICIES = "list policies"
ERR_GET_POLICY = "get policy"
ERR_UPSERT_POLICY = "upsert policy"
ERR_DELETE_POLICY = "delete policy"
ERR_GET_POLICY_HISTORY = "get policy history"
ERR_ROLLBACK_POLICY = "rollback policy"
ERR_LIST_POLICY_SETS = "list policy sets"
ERR_GET_POLICY_SET = "get policy set"
ERR_CREATE_POLICY_SET = "create policy set"
ERR_UPDATE_POLICY_SET = "update policy set"
ERR_DELETE_POLICY_SET = "delete policy set"


class Client:
    """Image & Video Manager API client.

    Provides access to the Akamai Image & Video Manager APIs for managing
    image and video optimisation policies and policy sets.

    Mirrors Go ``imaging.Imaging`` interface and ``imaging`` struct.

    Usage::

        >>> from akamai.edgegrid.session import Session
        >>> from akamai.edgegrid.imaging.imaging import Client
        >>> session = Session(edgerc_path="~/.edgerc")
        >>> client = Client(session)
    """

    def __init__(self, session: Session):
        """Initialise an Imaging API client.

        :param session: Authenticated Akamai API session.
        """
        self._session = session

    # ------------------------------------------------------------------
    # Policy Methods
    # ------------------------------------------------------------------

    def list_policies(
        self, params: ListPoliciesRequest
    ) -> ListPoliciesResponse:
        """List all Policies for the given network and account.

        See: https://techdocs.akamai.com/ivm/reference/get-policies
        """
        logger.debug("ListPolicies")

        err = validation.validate_list_policies_request(params)
        if err:
            raise ErrStructValidation(
                f"{ERR_LIST_POLICIES}: struct validation:\n{err}"
            )

        uri = f"/imaging/v2/network/{params.network}/policies"
        headers = {
            "Contract": params.contract_id,
            "Policy-Set": params.policy_set_id,
        }

        response, result = self._session.exec(
            "GET",
            uri,
            headers=headers,
            expect_json=True,
            error_parser=errors.parse_error_response,
        )
        Session.close_response_body(response)

        result = result or {}
        resp = dict_to_model(result, ListPoliciesResponse)
        resp.items = unmarshal_policy_outputs(result.get("items"))
        return resp

    def get_policy(self, params: GetPolicyRequest) -> Any:
        """Get specific policy by PolicyID.

        Returns ``PolicyOutputImage`` or ``PolicyOutputVideo`` based on
        the ``video`` boolean discriminator field in the response payload.

        See: https://techdocs.akamai.com/ivm/reference/get-policy
        """
        logger.debug("GetPolicy")

        err = validation.validate_get_policy_request(params)
        if err:
            raise ErrStructValidation(
                f"{ERR_GET_POLICY}: struct validation:\n{err}"
            )

        uri = (
            f"/imaging/v2/network/{params.network}"
            f"/policies/{params.policy_id}"
        )
        headers = {
            "Contract": params.contract_id,
            "Policy-Set": params.policy_set_id,
        }

        response, result = self._session.exec(
            "GET",
            uri,
            headers=headers,
            expect_json=True,
            error_parser=errors.parse_error_response,
        )
        Session.close_response_body(response)

        return unmarshal_policy_output(result or {})

    def upsert_policy(
        self, params: UpsertPolicyRequest
    ) -> PolicyResponse:
        """Create or update the configuration for a policy.

        See: https://techdocs.akamai.com/ivm/reference/put-policy
        """
        logger.debug("UpsertPolicy")

        err = validation.validate_upsert_policy_request(params)
        if err:
            raise ErrStructValidation(
                f"{ERR_UPSERT_POLICY}: struct validation:\n{err}"
            )

        uri = (
            f"/imaging/v2/network/{params.network}"
            f"/policies/{params.policy_id}"
        )
        headers = {
            "Contract": params.contract_id,
            "Policy-Set": params.policy_set_id,
        }

        body = model_to_dict(params.policy_input)

        response, result = self._session.exec(
            "PUT",
            uri,
            body=body,
            headers=headers,
            expect_json=True,
            error_parser=errors.parse_error_response,
        )
        Session.close_response_body(response)

        return dict_to_model(result, PolicyResponse)

    def delete_policy(
        self, params: DeletePolicyRequest
    ) -> PolicyResponse:
        """Delete a policy.

        See: https://techdocs.akamai.com/ivm/reference/delete-policy
        """
        logger.debug("DeletePolicy")

        err = validation.validate_delete_policy_request(params)
        if err:
            raise ErrStructValidation(
                f"{ERR_DELETE_POLICY}: struct validation:\n{err}"
            )

        uri = (
            f"/imaging/v2/network/{params.network}"
            f"/policies/{params.policy_id}"
        )
        headers = {
            "Contract": params.contract_id,
            "Policy-Set": params.policy_set_id,
        }

        response, result = self._session.exec(
            "DELETE",
            uri,
            headers=headers,
            expect_json=True,
            error_parser=errors.parse_error_response,
        )
        Session.close_response_body(response)

        return dict_to_model(result, PolicyResponse)

    def get_policy_history(
        self, params: GetPolicyHistoryRequest
    ) -> GetPolicyHistoryResponse:
        """Retrieve history of changes for a policy.

        See: https://techdocs.akamai.com/ivm/reference/get-policy-history
        """
        logger.debug("GetPolicyHistory")

        err = validation.validate_get_policy_history_request(params)
        if err:
            raise ErrStructValidation(
                f"{ERR_GET_POLICY_HISTORY}: struct validation:\n{err}"
            )

        uri = (
            f"/imaging/v2/network/{params.network}"
            f"/policies/history/{params.policy_id}"
        )
        headers = {
            "Contract": params.contract_id,
            "Policy-Set": params.policy_set_id,
        }

        response, result = self._session.exec(
            "GET",
            uri,
            headers=headers,
            expect_json=True,
            error_parser=errors.parse_error_response,
        )
        Session.close_response_body(response)

        result = result or {}
        resp = dict_to_model(result, GetPolicyHistoryResponse)
        resp.items = [
            dict_to_model(item, PolicyHistoryItem)
            for item in result.get("items", [])
        ]
        return resp

    def rollback_policy(
        self, params: RollbackPolicyRequest
    ) -> PolicyResponse:
        """Revert a policy to its previous version and deploy to the network.

        See: https://techdocs.akamai.com/ivm/reference/put-rollback-policy
        """
        logger.debug("RollbackPolicy")

        err = validation.validate_rollback_policy_request(params)
        if err:
            raise ErrStructValidation(
                f"{ERR_ROLLBACK_POLICY}: struct validation:\n{err}"
            )

        uri = (
            f"/imaging/v2/network/{params.network}"
            f"/policies/rollback/{params.policy_id}"
        )
        headers = {
            "Contract": params.contract_id,
            "Policy-Set": params.policy_set_id,
        }

        response, result = self._session.exec(
            "PUT",
            uri,
            headers=headers,
            expect_json=True,
            error_parser=errors.parse_error_response,
        )
        Session.close_response_body(response)

        return dict_to_model(result, PolicyResponse)

    # ------------------------------------------------------------------
    # PolicySet Methods
    # ------------------------------------------------------------------

    def list_policy_sets(
        self, params: ListPolicySetsRequest
    ) -> list[PolicySet]:
        """List all PolicySets of specified type for the current account.

        When ``network`` is an empty string (``NetworkBoth``), the URI
        omits the network segment.

        See: https://techdocs.akamai.com/ivm/reference/get-policysets
        """
        logger.debug("ListPolicySets")

        err = validation.validate_list_policy_sets_request(params)
        if err:
            raise ErrStructValidation(
                f"{ERR_LIST_POLICY_SETS}: struct validation:\n{err}"
            )

        # URI depends on network value (mirrors Go policyset.go lines 192-196)
        if params.network:
            uri = f"/imaging/v2/network/{params.network}/policysets"
        else:
            uri = "/imaging/v2/policysets"

        headers = {"Contract": params.contract_id}

        response, result = self._session.exec(
            "GET",
            uri,
            headers=headers,
            expect_json=True,
            error_parser=errors.parse_error_response,
        )
        Session.close_response_body(response)

        if not result:
            return []
        return [dict_to_model(item, PolicySet) for item in result]

    def get_policy_set(
        self, params: GetPolicySetRequest
    ) -> PolicySet:
        """Get specific PolicySet by PolicySetID.

        When ``network`` is an empty string (``NetworkBoth``), the URI
        omits the network segment.

        See: https://techdocs.akamai.com/ivm/reference/get-policyset
        """
        logger.debug("GetPolicySet")

        err = validation.validate_get_policy_set_request(params)
        if err:
            raise ErrStructValidation(
                f"{ERR_GET_POLICY_SET}: struct validation:\n{err}"
            )

        # URI depends on network value (mirrors Go policyset.go lines 232-236)
        if params.network:
            uri = (
                f"/imaging/v2/network/{params.network}"
                f"/policysets/{params.policy_set_id}"
            )
        else:
            uri = f"/imaging/v2/policysets/{params.policy_set_id}"

        headers = {"Contract": params.contract_id}

        response, result = self._session.exec(
            "GET",
            uri,
            headers=headers,
            expect_json=True,
            error_parser=errors.parse_error_response,
        )
        Session.close_response_body(response)

        return dict_to_model(result, PolicySet)

    def create_policy_set(
        self, params: CreatePolicySetRequest
    ) -> PolicySet:
        """Create configuration for a PolicySet.

        See: https://techdocs.akamai.com/ivm/reference/post-policyset
        """
        logger.debug("CreatePolicySet")

        err = validation.validate_create_policy_set_request(params)
        if err:
            raise ErrStructValidation(
                f"{ERR_CREATE_POLICY_SET}: struct validation:\n{err}"
            )

        uri = "/imaging/v2/policysets"
        headers = {"Contract": params.contract_id}

        # Build the request body matching Go's CreatePolicySet struct
        # JSON tags: name, region, type, defaultPolicy (omitempty)
        body: dict[str, Any] = {
            "name": params.name,
            "region": params.region,
            "type": params.type,
        }
        if params.default_policy is not None:
            body["defaultPolicy"] = model_to_dict(params.default_policy)

        response, result = self._session.exec(
            "POST",
            uri,
            body=body,
            headers=headers,
            expect_json=True,
            error_parser=errors.parse_error_response,
        )
        Session.close_response_body(response)

        return dict_to_model(result, PolicySet)

    def update_policy_set(
        self, params: UpdatePolicySetRequest
    ) -> PolicySet:
        """Update configuration for a PolicySet.

        See: https://techdocs.akamai.com/ivm/reference/put-policyset
        """
        logger.debug("UpdatePolicySet")

        err = validation.validate_update_policy_set_request(params)
        if err:
            raise ErrStructValidation(
                f"{ERR_UPDATE_POLICY_SET}: struct validation:\n{err}"
            )

        uri = f"/imaging/v2/policysets/{params.policy_set_id}"
        headers = {"Contract": params.contract_id}

        # Build the request body matching Go's UpdatePolicySet struct
        # JSON tags: name, region
        body = {
            "name": params.name,
            "region": params.region,
        }

        response, result = self._session.exec(
            "PUT",
            uri,
            body=body,
            headers=headers,
            expect_json=True,
            error_parser=errors.parse_error_response,
        )
        Session.close_response_body(response)

        return dict_to_model(result, PolicySet)

    def delete_policy_set(
        self, params: DeletePolicySetRequest
    ) -> None:
        """Delete configuration for a PolicySet.

        See: https://techdocs.akamai.com/ivm/reference/delete-policyset
        """
        logger.debug("DeletePolicySet")

        err = validation.validate_delete_policy_set_request(params)
        if err:
            raise ErrStructValidation(
                f"{ERR_DELETE_POLICY_SET}: struct validation:\n{err}"
            )

        uri = f"/imaging/v2/policysets/{params.policy_set_id}"
        headers = {"Contract": params.contract_id}

        response, _ = self._session.exec(
            "DELETE",
            uri,
            headers=headers,
            error_parser=errors.parse_error_response,
        )
        Session.close_response_body(response)
