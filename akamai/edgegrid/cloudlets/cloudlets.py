"""Cloudlets API client implementation.

Mirrors the Go ``pkg/cloudlets`` package, providing methods for
managing Akamai Cloudlets policies, policy versions, activations,
load balancer origins, versions, activations, and match rules.
"""  # pylint: disable=too-many-lines

import logging

from akamai.edgegrid.session import Session
from akamai.edgegrid.cloudlets import errors
from akamai.edgegrid.cloudlets import models
from akamai.edgegrid.cloudlets import validation


logger = logging.getLogger(__name__)


def _bool_param(value: bool) -> str:
    """Return a lowercase boolean string for query parameters.

    Akamai APIs expect ``"true"`` / ``"false"`` (lowercase).
    """
    return "true" if value else "false"


class Client:  # pylint: disable=too-many-public-methods
    """Cloudlets API client.

    Provides methods for managing Akamai Cloudlets policies,
    versions, activations, load balancers, and match rules.

    Mirrors Go ``pkg/cloudlets.Cloudlets`` interface.
    """

    def __init__(self, session: Session) -> None:
        """Initialize the Cloudlets client.

        Args:
            session: An authenticated Session instance for
                making API requests.
        """
        self._session = session

    # ================================================================
    # Origins  (mirrors loadbalancer.go)
    # ================================================================

    def list_origins(
        self,
        params: models.ListOriginsRequest,
    ) -> list[models.OriginResponse]:
        """List all origins of specified type for the current account.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/get-origins

        Mirrors Go ``cloudlets.ListOrigins``.

        Args:
            params: Request parameters; ``type`` filters by origin
                type (use :data:`~models.ORIGIN_TYPE_ALL` to
                list all).

        Returns:
            List of :class:`~models.OriginResponse` entries.

        Raises:
            errors.Error: On validation failure or API error.
        """
        logger.debug('ListOrigins')

        err = validation.validate_list_origins_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrListOrigins}: "
                    f"{errors.ErrStructValidation}:\n{err}"
                ),
            )

        uri = '/cloudlets/api/v2/origins'
        query: dict[str, str] = {}
        if params.type and params.type != models.ORIGIN_TYPE_ALL:
            query['type'] = params.type

        response, result = self._session.exec(
            'GET',
            uri,
            params=query or None,
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return [
            models.OriginResponse.from_dict(item)
            for item in result
        ]

    def get_origin(
        self,
        params: models.GetOriginRequest,
    ) -> models.Origin:
        """Get a specific origin.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/get-origin

        Mirrors Go ``cloudlets.GetOrigin``.

        Args:
            params: Request parameters (origin_id).

        Returns:
            The requested :class:`~models.Origin`.

        Raises:
            errors.Error: On API error.
        """
        logger.debug('GetOrigin')

        uri = f'/cloudlets/api/v2/origins/{params.origin_id}'

        response, result = self._session.exec(
            'GET',
            uri,
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return models.Origin.from_dict(result)

    def create_origin(
        self,
        params: models.CreateOriginRequest,
    ) -> models.Origin:
        """Create a new origin.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/post-origin

        Mirrors Go ``cloudlets.CreateOrigin``.

        Args:
            params: Request payload including origin_id and
                description.

        Returns:
            The newly created :class:`~models.Origin`.

        Raises:
            errors.Error: On validation failure or API error.
        """
        logger.debug('CreateOrigin')

        err = validation.validate_create_origin_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrCreateOrigin}: "
                    f"{errors.ErrStructValidation}:\n{err}"
                ),
            )

        uri = '/cloudlets/api/v2/origins'

        response, result = self._session.exec(
            'POST',
            uri,
            body=params.to_dict(),
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 201:
            raise errors.Error.from_response(response)

        return models.Origin.from_dict(result)

    def update_origin(
        self,
        params: models.UpdateOriginRequest,
    ) -> models.Origin:
        """Update an existing origin.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/put-origin

        Mirrors Go ``cloudlets.UpdateOrigin``.

        The request body contains only the ``Description`` embedded
        struct, not the full request wrapper.

        Args:
            params: Request wrapper with origin_id and
                description payload.

        Returns:
            The updated :class:`~models.Origin`.

        Raises:
            errors.Error: On validation failure or API error.
        """
        logger.debug('UpdateOrigin')

        err = validation.validate_update_origin_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrUpdateOrigin}: "
                    f"{errors.ErrStructValidation}:\n{err}"
                ),
            )

        uri = f'/cloudlets/api/v2/origins/{params.origin_id}'
        # Go sends params.Description (embedded struct) as body.
        body = models.Description(description=params.description).to_dict()

        response, result = self._session.exec(
            'PUT',
            uri,
            body=body,
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return models.Origin.from_dict(result)

    # ================================================================
    # Load Balancer Versions  (mirrors loadbalancer_version.go)
    # ================================================================

    def create_load_balancer_version(
        self,
        params: models.CreateLoadBalancerVersionRequest,
    ) -> models.LoadBalancerVersion:
        """Create a new load balancer version.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/post-origin-version

        Mirrors Go ``cloudlets.CreateLoadBalancerVersion``.

        Args:
            params: Request wrapper containing origin_id and
                the :class:`~models.LoadBalancerVersion` payload.

        Returns:
            The newly created :class:`~models.LoadBalancerVersion`.

        Raises:
            errors.Error: On validation failure or API error.
        """
        logger.debug('CreateLoadBalancerVersion')

        err = validation.validate_create_load_balancer_version_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrCreateLoadBalancerVersion}: "
                    f"{errors.ErrStructValidation}:\n{err}"
                ),
            )

        uri = (
            f'/cloudlets/api/v2/origins/{params.origin_id}'
            '/versions'
        )
        body = params.load_balancer_version.to_dict()

        response, result = self._session.exec(
            'POST',
            uri,
            body=body,
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 201:
            raise errors.Error.from_response(response)

        return models.LoadBalancerVersion.from_dict(result)

    def get_load_balancer_version(
        self,
        params: models.GetLoadBalancerVersionRequest,
    ) -> models.LoadBalancerVersion:
        """Get a specific load balancer version.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/get-origin-version

        Mirrors Go ``cloudlets.GetLoadBalancerVersion``.

        When ``should_validate`` is set, a ``validate=true`` query
        parameter is added.

        Args:
            params: Request parameters (origin_id, version,
                optional should_validate).

        Returns:
            The requested :class:`~models.LoadBalancerVersion`.

        Raises:
            errors.Error: On validation failure or API error.
        """
        logger.debug('GetLoadBalancerVersion')

        err = validation.validate_get_load_balancer_version_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetLoadBalancerVersion}: "
                    f"{errors.ErrStructValidation}:\n{err}"
                ),
            )

        uri = (
            f'/cloudlets/api/v2/origins/{params.origin_id}'
            f'/versions/{params.version}'
        )
        query: dict[str, str] = {}
        if params.should_validate:
            query['validate'] = 'true'

        response, result = self._session.exec(
            'GET',
            uri,
            params=query or None,
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return models.LoadBalancerVersion.from_dict(result)

    def update_load_balancer_version(
        self,
        params: models.UpdateLoadBalancerVersionRequest,
    ) -> models.LoadBalancerVersion:
        """Update an existing load balancer version.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/put-origin-version

        Mirrors Go ``cloudlets.UpdateLoadBalancerVersion``.

        Args:
            params: Request wrapper containing origin_id, version,
                optional should_validate flag, and the
                :class:`~models.LoadBalancerVersion` payload.

        Returns:
            The updated :class:`~models.LoadBalancerVersion`.

        Raises:
            errors.Error: On validation failure or API error.
        """
        logger.debug('UpdateLoadBalancerVersion')

        err = validation.validate_update_load_balancer_version_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrUpdateLoadBalancerVersion}: "
                    f"{errors.ErrStructValidation}:\n{err}"
                ),
            )

        uri = (
            f'/cloudlets/api/v2/origins/{params.origin_id}'
            f'/versions/{params.version}'
        )
        query: dict[str, str] = {}
        if params.should_validate:
            query['validate'] = 'true'

        body = params.load_balancer_version.to_dict()

        response, result = self._session.exec(
            'PUT',
            uri,
            body=body,
            params=query or None,
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return models.LoadBalancerVersion.from_dict(result)

    def list_load_balancer_versions(
        self,
        params: models.ListLoadBalancerVersionsRequest,
    ) -> list[models.LoadBalancerVersion]:
        """List all versions of a load balancer origin.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/get-origin-versions

        Mirrors Go ``cloudlets.ListLoadBalancerVersions``.

        The ``includeModel=true`` query parameter is always set,
        matching Go behaviour.

        Args:
            params: Request parameters (origin_id).

        Returns:
            List of :class:`~models.LoadBalancerVersion` entries.

        Raises:
            errors.Error: On validation failure or API error.
        """
        logger.debug('ListLoadBalancerVersions')

        err = validation.validate_list_load_balancer_versions_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrListLoadBalancerVersions}: "
                    f"{errors.ErrStructValidation}:\n{err}"
                ),
            )

        uri = (
            f'/cloudlets/api/v2/origins/{params.origin_id}'
            '/versions'
        )
        query: dict[str, str] = {'includeModel': 'true'}

        response, result = self._session.exec(
            'GET',
            uri,
            params=query,
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return [
            models.LoadBalancerVersion.from_dict(item)
            for item in result
        ]

    # ================================================================
    # Load Balancer Activations  (mirrors loadbalancer_activation.go)
    # ================================================================

    def list_load_balancer_activations(
        self,
        params: models.ListLoadBalancerActivationsRequest,
    ) -> list[models.LoadBalancerActivation]:
        """List load balancer activations.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/get-origin-activations

        Mirrors Go ``cloudlets.ListLoadBalancerActivations``.

        Args:
            params: Request parameters with origin_id and optional
                filters (network, page_size, page, latest_only).

        Returns:
            List of :class:`~models.LoadBalancerActivation` entries.

        Raises:
            errors.Error: On validation failure or API error.
        """
        logger.debug('ListLoadBalancerActivations')

        err = validation.validate_list_load_balancer_activations_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrListLoadBalancerActivations}: "
                    f"{errors.ErrStructValidation}:\n{err}"
                ),
            )

        uri = (
            f'/cloudlets/api/v2/origins/{params.origin_id}'
            '/activations'
        )
        query: dict[str, str] = {}
        if params.network:
            query['network'] = params.network
        if params.page_size is not None:
            query['pageSize'] = str(params.page_size)
        if params.page is not None:
            query['page'] = str(params.page)
        if params.latest_only:
            query['latestOnly'] = _bool_param(params.latest_only)

        response, result = self._session.exec(
            'GET',
            uri,
            params=query or None,
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return [
            models.LoadBalancerActivation.from_dict(item)
            for item in result
        ]

    def activate_load_balancer_version(
        self,
        params: models.ActivateLoadBalancerVersionRequest,
    ) -> models.LoadBalancerActivation:
        """Activate a load balancer version.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/post-origin-activation

        Mirrors Go ``cloudlets.ActivateLoadBalancerVersion``.

        Args:
            params: Request wrapper containing origin_id, async
                flag, and :class:`~models.LoadBalancerVersionActivation`
                payload.

        Returns:
            The :class:`~models.LoadBalancerActivation` result.

        Raises:
            errors.Error: On validation failure or API error.
        """
        logger.debug('ActivateLoadBalancerVersion')

        err = validation.validate_activate_load_balancer_version_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrActivateLoadBalancerVersion}: "
                    f"{errors.ErrStructValidation}:\n{err}"
                ),
            )

        uri = (
            f'/cloudlets/api/v2/origins/{params.origin_id}'
            '/activations'
        )
        query: dict[str, str] = {
            'async': _bool_param(params.async_),
        }
        body = params.load_balancer_version_activation.to_dict()

        response, result = self._session.exec(
            'POST',
            uri,
            body=body,
            params=query,
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return models.LoadBalancerActivation.from_dict(result)

    # ================================================================
    # Policies  (mirrors policy.go)
    # ================================================================

    def list_policies(
        self,
        params: models.ListPoliciesRequest,
    ) -> list[models.Policy]:
        """List cloudlet policies.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/get-policies

        Mirrors Go ``cloudlets.ListPolicies``.

        Args:
            params: Request parameters with optional filters
                (cloudlet_id, page_size, offset, include_deleted).

        Returns:
            List of :class:`~models.Policy` entries.

        Raises:
            errors.Error: On API error.
        """
        logger.debug('ListPolicies')

        uri = '/cloudlets/api/v2/policies'
        query: dict[str, str] = {}
        if params.cloudlet_id is not None:
            query['cloudletId'] = str(params.cloudlet_id)
        if params.page_size is not None:
            query['pageSize'] = str(params.page_size)
        query['offset'] = str(params.offset)
        query['includeDeleted'] = _bool_param(params.include_deleted)

        response, result = self._session.exec(
            'GET',
            uri,
            params=query,
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return [models.Policy.from_dict(item) for item in result]

    def get_policy(
        self,
        params: models.GetPolicyRequest,
    ) -> models.Policy:
        """Get a specific cloudlet policy.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/get-policy

        Mirrors Go ``cloudlets.GetPolicy``.

        Args:
            params: Request parameters (policy_id).

        Returns:
            The requested :class:`~models.Policy`.

        Raises:
            errors.Error: On API error.
        """
        logger.debug('GetPolicy')

        uri = f'/cloudlets/api/v2/policies/{params.policy_id}'

        response, result = self._session.exec(
            'GET',
            uri,
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return models.Policy.from_dict(result)

    def create_policy(
        self,
        params: models.CreatePolicyRequest,
    ) -> models.Policy:
        """Create a new cloudlet policy.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/post-policy

        Mirrors Go ``cloudlets.CreatePolicy``.

        Args:
            params: Request payload for the new policy.

        Returns:
            The newly created :class:`~models.Policy`.

        Raises:
            errors.Error: On validation failure or API error.
        """
        logger.debug('CreatePolicy')

        err = validation.validate_create_policy_request(params)
        if err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrCreatePolicy}: "
                    f"{errors.ErrStructValidation}: {err}"
                ),
            )

        uri = '/cloudlets/api/v2/policies'

        response, result = self._session.exec(
            'POST',
            uri,
            body=params.to_dict(),
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 201:
            raise errors.Error.from_response(response)

        return models.Policy.from_dict(result)

    def remove_policy(
        self,
        params: models.RemovePolicyRequest,
    ) -> None:
        """Remove (delete) a cloudlet policy.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/delete-policy

        Mirrors Go ``cloudlets.RemovePolicy``.

        Args:
            params: Request parameters (policy_id).

        Raises:
            errors.Error: On API error.
        """
        logger.debug('RemovePolicy')

        uri = f'/cloudlets/api/v2/policies/{params.policy_id}'

        response, _ = self._session.exec(
            'DELETE',
            uri,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 204:
            raise errors.Error.from_response(response)

    def update_policy(
        self,
        params: models.UpdatePolicyRequest,
    ) -> models.Policy:
        """Update an existing cloudlet policy.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/put-policy

        Mirrors Go ``cloudlets.UpdatePolicy``.  The request body
        contains the embedded ``UpdatePolicy`` struct, not the full
        request wrapper.

        Args:
            params: Request wrapper with policy_id and the
                :class:`~models.UpdatePolicy` payload.

        Returns:
            The updated :class:`~models.Policy`.

        Raises:
            errors.Error: On validation failure or API error.
        """
        logger.debug('UpdatePolicy')

        err = validation.validate_update_policy_request(params)
        if err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrUpdatePolicy}: "
                    f"{errors.ErrStructValidation}: {err}"
                ),
            )

        uri = f'/cloudlets/api/v2/policies/{params.policy_id}'
        # Go sends params.UpdatePolicy (embedded struct) as body.
        # Python _promote flattens it via to_dict().
        body = params.to_dict()

        response, result = self._session.exec(
            'PUT',
            uri,
            body=body,
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return models.Policy.from_dict(result)

    # ================================================================
    # Policy Properties  (mirrors policy_property.go)
    # ================================================================

    def get_policy_properties(
        self,
        params: models.GetPolicyPropertiesRequest,
    ) -> dict[str, models.PolicyProperty]:
        """Get policy properties.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/get-policy-properties

        Mirrors Go ``cloudlets.GetPolicyProperties``.

        Args:
            params: Request parameters (policy_id).

        Returns:
            Dictionary mapping property identifiers to
            :class:`~models.PolicyProperty` objects.

        Raises:
            errors.Error: On API error.
        """
        logger.debug('GetPolicyProperties')

        uri = (
            f'/cloudlets/api/v2/policies/{params.policy_id}'
            '/properties'
        )

        response, result = self._session.exec(
            'GET',
            uri,
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return {
            key: models.PolicyProperty.from_dict(val)
            for key, val in result.items()
        }

    def delete_policy_property(
        self,
        params: models.DeletePolicyPropertyRequest,
    ) -> None:
        """Delete a policy-property association.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/delete-policy-property

        Mirrors Go ``cloudlets.DeletePolicyProperty``.

        The ``async=true`` query parameter is always set.

        Args:
            params: Request parameters (policy_id, property_id,
                optional network).

        Raises:
            errors.Error: On validation failure or API error.
        """
        logger.debug('DeletePolicyProperty')

        err = validation.validate_delete_policy_property_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrDeletePolicyProperty}: "
                    f"{errors.ErrStructValidation}:\n{err}"
                ),
            )

        uri = (
            f'/cloudlets/api/v2/policies/{params.policy_id}'
            f'/properties/{params.property_id}'
        )
        query: dict[str, str] = {'async': 'true'}
        if params.network:
            query['network'] = params.network

        response, _ = self._session.exec(
            'DELETE',
            uri,
            params=query,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 204:
            raise errors.Error.from_response(response)

    # ================================================================
    # Policy Versions  (mirrors policy_version.go)
    # ================================================================

    def list_policy_versions(
        self,
        params: models.ListPolicyVersionsRequest,
    ) -> list[models.PolicyVersion]:
        """List all versions of a cloudlet policy.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/get-policy-versions

        Mirrors Go ``cloudlets.ListPolicyVersions``.

        Args:
            params: Request parameters (policy_id) with optional
                filters (offset, include_rules, include_deleted,
                include_activations, page_size).

        Returns:
            List of :class:`~models.PolicyVersion` entries.

        Raises:
            errors.Error: On validation failure or API error.
        """
        logger.debug('ListPolicyVersions')

        err = validation.validate_list_policy_versions_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrListPolicyVersions}: "
                    f"{errors.ErrStructValidation}:\n{err}"
                ),
            )

        uri = (
            f'/cloudlets/api/v2/policies/{params.policy_id}'
            '/versions'
        )
        query: dict[str, str] = {
            'offset': str(params.offset),
            'includeRules': _bool_param(params.include_rules),
            'includeDeleted': _bool_param(params.include_deleted),
            'includeActivations': _bool_param(
                params.include_activations,
            ),
        }
        if params.page_size is not None:
            query['pageSize'] = str(params.page_size)

        response, result = self._session.exec(
            'GET',
            uri,
            params=query,
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return [
            models.PolicyVersion.from_dict(item)
            for item in result
        ]

    def get_policy_version(
        self,
        params: models.GetPolicyVersionRequest,
    ) -> models.PolicyVersion:
        """Get a specific policy version.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/get-policy-version

        Mirrors Go ``cloudlets.GetPolicyVersion``.

        Args:
            params: Request parameters (policy_id, version,
                omit_rules flag).

        Returns:
            The requested :class:`~models.PolicyVersion`.

        Raises:
            errors.Error: On API error.
        """
        logger.debug('GetPolicyVersion')

        uri = (
            f'/cloudlets/api/v2/policies/{params.policy_id}'
            f'/versions/{params.version}'
        )
        query: dict[str, str] = {
            'omitRules': _bool_param(params.omit_rules),
        }

        response, result = self._session.exec(
            'GET',
            uri,
            params=query,
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return models.PolicyVersion.from_dict(result)

    def create_policy_version(
        self,
        params: models.CreatePolicyVersionRequest,
    ) -> models.PolicyVersion:
        """Create a new version of a cloudlet policy.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/post-policy-version

        Mirrors Go ``cloudlets.CreatePolicyVersion``.

        Args:
            params: Request wrapper with policy_id and
                :class:`~models.CreatePolicyVersion` payload.

        Returns:
            The newly created :class:`~models.PolicyVersion`.

        Raises:
            errors.Error: On validation failure or API error.
        """
        logger.debug('CreatePolicyVersion')

        err = validation.validate_create_policy_version_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrCreatePolicyVersion}: "
                    f"{errors.ErrStructValidation}:\n{err}"
                ),
            )

        uri = (
            f'/cloudlets/api/v2/policies/{params.policy_id}'
            '/versions'
        )
        body = params.create_policy_version.to_dict()

        response, result = self._session.exec(
            'POST',
            uri,
            body=body,
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 201:
            raise errors.Error.from_response(response)

        return models.PolicyVersion.from_dict(result)

    def delete_policy_version(
        self,
        params: models.DeletePolicyVersionRequest,
    ) -> None:
        """Delete a cloudlet policy version.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/delete-policy-version

        Mirrors Go ``cloudlets.DeletePolicyVersion``.

        Args:
            params: Request parameters (policy_id, version).

        Raises:
            errors.Error: On API error.
        """
        logger.debug('DeletePolicyVersion')

        uri = (
            f'/cloudlets/api/v2/policies/{params.policy_id}'
            f'/versions/{params.version}'
        )

        response, _ = self._session.exec(
            'DELETE',
            uri,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 204:
            raise errors.Error.from_response(response)

    def update_policy_version(
        self,
        params: models.UpdatePolicyVersionRequest,
    ) -> models.PolicyVersion:
        """Update an existing cloudlet policy version.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/put-policy-version

        Mirrors Go ``cloudlets.UpdatePolicyVersion``.

        The request body contains the embedded
        ``UpdatePolicyVersion`` struct.

        Args:
            params: Request wrapper with policy_id, version, and
                :class:`~models.UpdatePolicyVersion` payload.

        Returns:
            The updated :class:`~models.PolicyVersion`.

        Raises:
            errors.Error: On validation failure or API error.
        """
        logger.debug('UpdatePolicyVersion')

        err = validation.validate_update_policy_version_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrUpdatePolicyVersion}: "
                    f"{errors.ErrStructValidation}:\n{err}"
                ),
            )

        uri = (
            f'/cloudlets/api/v2/policies/{params.policy_id}'
            f'/versions/{params.version}'
        )
        body = params.update_policy_version.to_dict()

        response, result = self._session.exec(
            'PUT',
            uri,
            body=body,
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return models.PolicyVersion.from_dict(result)

    # ================================================================
    # Policy Version Activations  (mirrors policy_version_activation.go)
    # ================================================================

    def list_policy_activations(
        self,
        params: models.ListPolicyActivationsRequest,
    ) -> list[models.PolicyActivation]:
        """List policy activations.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/get-policy-activations

        Mirrors Go ``cloudlets.ListPolicyActivations``.

        Args:
            params: Request parameters (policy_id) with optional
                filters (network, property_name).

        Returns:
            List of :class:`~models.PolicyActivation` entries.

        Raises:
            errors.Error: On validation failure or API error.
        """
        logger.debug('ListPolicyActivations')

        err = validation.validate_list_policy_activations_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrListPolicyActivations}: "
                    f"{errors.ErrStructValidation}:\n{err}"
                ),
            )

        uri = (
            f'/cloudlets/api/v2/policies/{params.policy_id}'
            '/activations'
        )
        query: dict[str, str] = {}
        if params.network:
            query['network'] = params.network
        if params.property_name:
            query['propertyName'] = params.property_name

        response, result = self._session.exec(
            'GET',
            uri,
            params=query or None,
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return [
            models.PolicyActivation.from_dict(item)
            for item in result
        ]

    def activate_policy_version(
        self,
        params: models.ActivatePolicyVersionRequest,
    ) -> list[models.PolicyActivation]:
        """Activate a cloudlet policy version.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/post-policy-version-activations

        Mirrors Go ``cloudlets.ActivatePolicyVersion``.

        Go checks ``resp.StatusCode >= 400`` rather than a specific
        success code; the session auto-raises on >= 400.

        Args:
            params: Request wrapper with policy_id, version,
                and :class:`~models.PolicyVersionActivation`
                payload.

        Returns:
            List of :class:`~models.PolicyActivation` entries.

        Raises:
            errors.Error: On validation failure or API error.
        """
        logger.debug('ActivatePolicyVersion')

        err = validation.validate_activate_policy_version_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrActivatePolicyVersion}: "
                    f"{errors.ErrStructValidation}:\n{err}"
                ),
            )

        uri = (
            f'/cloudlets/api/v2/policies/{params.policy_id}'
            f'/versions/{params.version}/activations'
        )
        body = params.policy_version_activation.to_dict()

        # Go checks >= 400 (default session behaviour).
        # session.exec auto-raises via error_parser on >= 400.
        _, result = self._session.exec(
            'POST',
            uri,
            body=body,
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        return [
            models.PolicyActivation.from_dict(item)
            for item in result
        ]

    # ================================================================
    # Policy Version Rules  (mirrors policy_version_rule.go)
    # ================================================================

    def get_policy_version_rule(
        self,
        params: models.GetPolicyVersionRuleRequest,
    ) -> dict:
        """Get a specific rule of a cloudlet policy version.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/get-policy-version-rule

        Mirrors Go ``cloudlets.GetPolicyVersionRule``.

        The response is a polymorphic match rule deserialized via
        :func:`~models.unmarshal_match_rule`.

        Args:
            params: Request parameters (policy_id, version,
                aka_rule_id).

        Returns:
            Deserialized match rule dictionary.

        Raises:
            errors.Error: On validation failure or API error.
        """
        logger.debug('GetPolicyVersionRule')

        err = validation.validate_get_policy_version_rule_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetPolicyVersionRule}: "
                    f"{errors.ErrStructValidation}:\n{err}"
                ),
            )

        uri = (
            f'/cloudlets/api/v2/policies/{params.policy_id}'
            f'/versions/{params.version}'
            f'/rules/{params.aka_rule_id}'
        )

        response, result = self._session.exec(
            'GET',
            uri,
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return models.unmarshal_match_rule(result)

    def create_policy_version_rule(
        self,
        params: models.CreatePolicyVersionRuleRequest,
    ) -> dict:
        """Create a rule within a cloudlet policy version.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/post-policy-version-rules

        Mirrors Go ``cloudlets.CreatePolicyVersionRule``.

        An ``index`` query parameter is added only when
        ``params.index > 0``.

        Args:
            params: Request parameters (policy_id, version,
                optional index, match_rule body).

        Returns:
            Deserialized match rule dictionary.

        Raises:
            errors.Error: On validation failure or API error.
        """
        logger.debug('CreatePolicyVersionRule')

        err = validation.validate_create_policy_version_rule_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrCreatePolicyVersionRule}: "
                    f"{errors.ErrStructValidation}:\n{err}"
                ),
            )

        uri = (
            f'/cloudlets/api/v2/policies/{params.policy_id}'
            f'/versions/{params.version}/rules'
        )
        query: dict[str, str] = {}
        if params.index > 0:
            query['index'] = str(params.index)

        response, result = self._session.exec(
            'POST',
            uri,
            body=params.match_rule,
            params=query or None,
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return models.unmarshal_match_rule(result)

    def update_policy_version_rule(
        self,
        params: models.UpdatePolicyVersionRuleRequest,
    ) -> dict:
        """Update a rule within a cloudlet policy version.

        See: https://techdocs.akamai.com/cloudlets/v2/reference/put-policy-version-rule

        Mirrors Go ``cloudlets.UpdatePolicyVersionRule``.

        Args:
            params: Request parameters (policy_id, version,
                aka_rule_id, match_rule body).

        Returns:
            Deserialized match rule dictionary.

        Raises:
            errors.Error: On validation failure or API error.
        """
        logger.debug('UpdatePolicyVersionRule')

        err = validation.validate_update_policy_version_rule_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrUpdatePolicyVersionRule}: "
                    f"{errors.ErrStructValidation}:\n{err}"
                ),
            )

        uri = (
            f'/cloudlets/api/v2/policies/{params.policy_id}'
            f'/versions/{params.version}'
            f'/rules/{params.aka_rule_id}'
        )

        response, result = self._session.exec(
            'PUT',
            uri,
            body=params.match_rule,
            expect_json=True,
            error_parser=errors.Error.from_response,
        )

        if response.status_code != 200:
            raise errors.Error.from_response(response)

        return models.unmarshal_match_rule(result)
