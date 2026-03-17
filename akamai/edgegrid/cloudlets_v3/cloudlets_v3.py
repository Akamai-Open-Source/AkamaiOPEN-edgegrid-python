"""Akamai Cloudlets V3 API client.

Implements all 17 endpoint methods defined in the Go ``Cloudlets``
interface (``pkg/cloudlets/v3/cloudlets.go`` lines 18-103).
"""

import json
import logging
from urllib.parse import urlencode

from akamai.edgegrid.session import Session
from akamai.edgegrid.cloudlets_v3 import errors
from akamai.edgegrid.cloudlets_v3 import models
from akamai.edgegrid.cloudlets_v3 import validation
from akamai.edgegrid.utils import unescape_content

logger = logging.getLogger(__name__)


def Client(session: Session) -> "CloudletsV3Client":  # pylint: disable=invalid-name
    """Return a new Cloudlets V3 client instance.

    Mirrors Go ``Client()`` constructor from cloudlets.go line 117.

    Args:
        session: An authenticated Session instance.

    Returns:
        A CloudletsV3Client configured with the given session.
    """
    return CloudletsV3Client(session)


class CloudletsV3Client:  # pylint: disable=too-many-public-methods
    """Cloudlets V3 API client.

    Provides access to the Akamai Cloudlets V3 APIs with methods
    mirroring the Go Cloudlets interface (cloudlets.go lines 18-103).
    """

    def __init__(self, session: Session):
        """Initialize the Cloudlets V3 client.

        Args:
            session: An authenticated Session instance.
        """
        self._session = session

    # Private helpers

    def _parse_error(self, response) -> errors.Error:
        """Parse an error from the HTTP response.

        Mirrors Go ``(c *cloudlets) Error(r *http.Response)`` from
        errors.go lines 32-54.

        Args:
            response: The HTTP response containing the error.

        Returns:
            A service-specific Error with parsed error details.
        """
        error = errors.Error()
        try:
            body = response.text
        except Exception as exc:  # pylint: disable=broad-except
            logger.error(
                "reading error response body: %s", exc
            )
            error.status = response.status_code
            error.title = "Failed to read error body"
            return error

        try:
            data = json.loads(body)
            error.type = data.get("type", "")
            error.title = data.get("title", "")
            error.detail = data.get("detail", "")
            error.instance = data.get("instance", "")
            error.status = data.get("status", 0)
            error.errors = data.get("errors")
            error.request_id = data.get("requestId", "")
            error.request_time = data.get("requestTime", "")
            error.client_ip = data.get("clientIp", "")
            error.server_ip = data.get("serverIp", "")
            error.method = data.get("method", "")
        except (json.JSONDecodeError, AttributeError) as exc:
            logger.error("could not unmarshal API error: %s", exc)
            error.title = (
                "Failed to unmarshal error body. Cloudlets API "
                "failed. Check details for more information."
            )
            error.detail = unescape_content(body)

        error.status = response.status_code
        return error

    # ListCloudlets — list_cloudlets.go lines 25-48

    def list_cloudlets(
        self,
    ) -> list[models.ListCloudletsItem]:
        """Return details of available Cloudlets.

        See: https://techdocs.akamai.com/cloudlets/reference/get-cloudlets
        """
        logger.debug("ListCloudlets")

        path = "/cloudlets/v3/cloudlet-info"

        try:
            response, data = self._session.exec(
                "GET",
                path,
                expect_json=True,
                error_parser=self._parse_error,
            )
        except errors.Error as api_err:
            raise RuntimeError(
                f"{errors.ErrListCloudlets}: {api_err}"
            ) from api_err
        except Exception as exc:
            raise RuntimeError(
                f"{errors.ErrListCloudlets}: "
                f"request failed: {exc}"
            ) from exc

        if response.status_code != 200:
            api_err = self._parse_error(response)
            raise RuntimeError(
                f"{errors.ErrListCloudlets}: {api_err}"
            )

        return [
            models.ListCloudletsItem.from_dict(item)
            for item in (data or [])
        ]

    # ListPolicies — policy.go lines 212-252

    def list_policies(
        self, params: models.ListPoliciesRequest
    ) -> models.ListPoliciesResponse:
        """Return shared policies available within your group.

        See: https://techdocs.akamai.com/cloudlets/reference/get-policies
        """
        logger.debug("ListPolicies")

        val_err = validation.validate_list_policies_request(params)
        if val_err is not None:
            raise ValueError(
                f"{errors.ErrListPolicies}: "
                f"{errors.ErrStructValidation}: {val_err}"
            )

        path = "/cloudlets/v3/policies"
        query: dict[str, str] = {}
        if params.size != 0:
            query["size"] = str(params.size)
        if params.page != 0:
            query["page"] = str(params.page)
        if query:
            path = f"{path}?{urlencode(query)}"

        try:
            response, data = self._session.exec(
                "GET",
                path,
                expect_json=True,
                error_parser=self._parse_error,
            )
        except errors.Error as api_err:
            raise RuntimeError(
                f"{errors.ErrListPolicies}: {api_err}"
            ) from api_err
        except Exception as exc:
            raise RuntimeError(
                f"{errors.ErrListPolicies}: "
                f"request failed: {exc}"
            ) from exc

        if response.status_code != 200:
            api_err = self._parse_error(response)
            raise RuntimeError(
                f"{errors.ErrListPolicies}: {api_err}"
            )

        return models.ListPoliciesResponse.from_dict(data)

    # CreatePolicy — policy.go lines 254-281

    def create_policy(
        self, params: models.CreatePolicyRequest
    ) -> models.Policy:
        """Create a shared policy for a specific Cloudlet type.

        See: https://techdocs.akamai.com/cloudlets/reference/post-policy
        """
        logger.debug("CreatePolicy")

        val_err = validation.validate_create_policy_request(params)
        if val_err is not None:
            raise ValueError(
                f"{errors.ErrCreatePolicy}: "
                f"{errors.ErrStructValidation}: {val_err}"
            )

        path = "/cloudlets/v3/policies"

        try:
            response, data = self._session.exec(
                "POST",
                path,
                body=params.to_dict(),
                expect_json=True,
                error_parser=self._parse_error,
            )
        except errors.Error as api_err:
            raise RuntimeError(
                f"{errors.ErrCreatePolicy}: {api_err}"
            ) from api_err
        except Exception as exc:
            raise RuntimeError(
                f"{errors.ErrCreatePolicy}: "
                f"request failed: {exc}"
            ) from exc

        if response.status_code != 201:
            api_err = self._parse_error(response)
            raise RuntimeError(
                f"{errors.ErrCreatePolicy}: {api_err}"
            )

        return models.Policy.from_dict(data)

    # DeletePolicy — policy.go lines 283-309

    def delete_policy(
        self, params: models.DeletePolicyRequest
    ) -> None:
        """Delete an existing Cloudlets policy.

        See: https://techdocs.akamai.com/cloudlets/reference/delete-policy
        """
        logger.debug("DeletePolicy")

        val_err = validation.validate_delete_policy_request(params)
        if val_err is not None:
            raise ValueError(
                f"{errors.ErrDeletePolicy}: "
                f"{errors.ErrStructValidation}: {val_err}"
            )

        path = f"/cloudlets/v3/policies/{params.policy_id}"

        try:
            response, _ = self._session.exec(
                "DELETE",
                path,
                error_parser=self._parse_error,
            )
        except errors.Error as api_err:
            raise RuntimeError(
                f"{errors.ErrDeletePolicy}: {api_err}"
            ) from api_err
        except Exception as exc:
            raise RuntimeError(
                f"{errors.ErrDeletePolicy}: "
                f"request failed: {exc}"
            ) from exc

        if response.status_code != 204:
            api_err = self._parse_error(response)
            raise RuntimeError(
                f"{errors.ErrDeletePolicy}: {api_err}"
            )

    # GetPolicy — policy.go lines 311-342

    def get_policy(
        self, params: models.GetPolicyRequest
    ) -> models.Policy:
        """Return information about a shared policy.

        See: https://techdocs.akamai.com/cloudlets/reference/get-policy
        """
        logger.debug("GetPolicy")

        val_err = validation.validate_get_policy_request(params)
        if val_err is not None:
            raise ValueError(
                f"{errors.ErrGetPolicy}: "
                f"{errors.ErrStructValidation}: {val_err}"
            )

        path = f"/cloudlets/v3/policies/{params.policy_id}"

        try:
            response, data = self._session.exec(
                "GET",
                path,
                expect_json=True,
                error_parser=self._parse_error,
            )
        except errors.Error as api_err:
            if api_err.status == 404:
                raise RuntimeError(
                    f"{errors.ErrGetPolicy}: "
                    f"{errors.ErrPolicyNotFound}: {api_err}"
                ) from api_err
            raise RuntimeError(
                f"{errors.ErrGetPolicy}: {api_err}"
            ) from api_err
        except Exception as exc:
            raise RuntimeError(
                f"{errors.ErrGetPolicy}: "
                f"request failed: {exc}"
            ) from exc

        if response.status_code != 200:
            api_err = self._parse_error(response)
            raise RuntimeError(
                f"{errors.ErrGetPolicy}: {api_err}"
            )

        return models.Policy.from_dict(data)

    # UpdatePolicy — policy.go lines 344-371

    def update_policy(
        self, params: models.UpdatePolicyRequest
    ) -> models.Policy:
        """Update an existing policy.

        See: https://techdocs.akamai.com/cloudlets/reference/put-policy
        """
        logger.debug("UpdatePolicy")

        val_err = validation.validate_update_policy_request(params)
        if val_err is not None:
            raise ValueError(
                f"{errors.ErrUpdatePolicy}: "
                f"{errors.ErrStructValidation}: {val_err}"
            )

        path = f"/cloudlets/v3/policies/{params.policy_id}"

        try:
            response, data = self._session.exec(
                "PUT",
                path,
                body=params.body.to_dict(),
                expect_json=True,
                error_parser=self._parse_error,
            )
        except errors.Error as api_err:
            raise RuntimeError(
                f"{errors.ErrUpdatePolicy}: {api_err}"
            ) from api_err
        except Exception as exc:
            raise RuntimeError(
                f"{errors.ErrUpdatePolicy}: "
                f"request failed: {exc}"
            ) from exc

        if response.status_code != 200:
            api_err = self._parse_error(response)
            raise RuntimeError(
                f"{errors.ErrUpdatePolicy}: {api_err}"
            )

        return models.Policy.from_dict(data)

    # ClonePolicy — policy.go lines 373-400

    def clone_policy(
        self, params: models.ClonePolicyRequest
    ) -> models.Policy:
        """Clone a policy into a new shared policy.

        See: https://techdocs.akamai.com/cloudlets/reference/post-policy-clone
        """
        logger.debug("ClonePolicy")

        val_err = validation.validate_clone_policy_request(params)
        if val_err is not None:
            raise ValueError(
                f"{errors.ErrClonePolicy}: "
                f"{errors.ErrStructValidation}: {val_err}"
            )

        path = (
            f"/cloudlets/v3/policies/{params.policy_id}/clone"
        )

        try:
            response, data = self._session.exec(
                "POST",
                path,
                body=params.body.to_dict(),
                expect_json=True,
                error_parser=self._parse_error,
            )
        except errors.Error as api_err:
            raise RuntimeError(
                f"{errors.ErrClonePolicy}: {api_err}"
            ) from api_err
        except Exception as exc:
            raise RuntimeError(
                f"{errors.ErrClonePolicy}: "
                f"request failed: {exc}"
            ) from exc

        if response.status_code != 200:
            api_err = self._parse_error(response)
            raise RuntimeError(
                f"{errors.ErrClonePolicy}: {api_err}"
            )

        return models.Policy.from_dict(data)

    # ListActivePolicyProperties — policy_property.go lines 69-108

    def list_active_policy_properties(
        self, params: models.ListActivePolicyPropertiesRequest
    ) -> models.ListActivePolicyPropertiesResponse:
        """Return active properties assigned to the policy.

        See: https://techdocs.akamai.com/cloudlets/reference/get-policy-properties
        """
        logger.debug("ListActivePolicyProperties")

        val_err = (
            validation
            .validate_list_active_policy_properties_request(params)
        )
        if val_err is not None:
            raise ValueError(
                f"{errors.ErrListActivePolicyProperties}: "
                f"{errors.ErrStructValidation}: {val_err}"
            )

        path = (
            f"/cloudlets/v3/policies/"
            f"{params.policy_id}/properties"
        )
        query: dict[str, str] = {}
        if params.page != 0:
            query["page"] = str(params.page)
        if params.size != 0:
            query["size"] = str(params.size)
        if query:
            path = f"{path}?{urlencode(query)}"

        try:
            response, data = self._session.exec(
                "GET",
                path,
                expect_json=True,
                error_parser=self._parse_error,
            )
        except errors.Error as api_err:
            raise RuntimeError(
                f"{errors.ErrListActivePolicyProperties}: "
                f"{api_err}"
            ) from api_err
        except Exception as exc:
            raise RuntimeError(
                f"{errors.ErrListActivePolicyProperties}: "
                f"request failed: {exc}"
            ) from exc

        if response.status_code != 200:
            api_err = self._parse_error(response)
            raise RuntimeError(
                f"{errors.ErrListActivePolicyProperties}: "
                f"{api_err}"
            )

        return (
            models.ListActivePolicyPropertiesResponse.from_dict(
                data
            )
        )

    # ListPolicyVersions — policy_version.go lines 156-193

    def list_policy_versions(
        self, params: models.ListPolicyVersionsRequest
    ) -> models.ListPolicyVersions:
        """List policy versions by policyID.

        See: https://techdocs.akamai.com/cloudlets/reference/get-policy-versions
        """
        logger.debug("ListPolicyVersions")

        val_err = (
            validation.validate_list_policy_versions_request(
                params
            )
        )
        if val_err is not None:
            raise ValueError(
                f"{errors.ErrListPolicyVersions}: "
                f"{errors.ErrStructValidation}:\n{val_err}"
            )

        path = (
            f"/cloudlets/v3/policies/"
            f"{params.policy_id}/versions"
        )
        query: dict[str, str] = {}
        query["page"] = str(params.page)
        if params.size != 0:
            query["size"] = str(params.size)
        path = f"{path}?{urlencode(query)}"

        try:
            response, data = self._session.exec(
                "GET",
                path,
                expect_json=True,
                error_parser=self._parse_error,
            )
        except errors.Error as api_err:
            raise RuntimeError(
                f"{errors.ErrListPolicyVersions}: {api_err}"
            ) from api_err
        except Exception as exc:
            raise RuntimeError(
                f"{errors.ErrListPolicyVersions}: "
                f"request failed: {exc}"
            ) from exc

        if response.status_code != 200:
            api_err = self._parse_error(response)
            raise RuntimeError(
                f"{errors.ErrListPolicyVersions}: {api_err}"
            )

        return models.ListPolicyVersions.from_dict(data)

    # GetPolicyVersion — policy_version.go lines 195-219

    def get_policy_version(
        self, params: models.GetPolicyVersionRequest
    ) -> models.PolicyVersion:
        """Get policy version by policyID and version.

        See: https://techdocs.akamai.com/cloudlets/reference/get-policy-version
        """
        logger.debug("GetPolicyVersion")

        path = (
            f"/cloudlets/v3/policies/{params.policy_id}"
            f"/versions/{params.policy_version}"
        )

        try:
            response, data = self._session.exec(
                "GET",
                path,
                expect_json=True,
                error_parser=self._parse_error,
            )
        except errors.Error as api_err:
            raise RuntimeError(
                f"{errors.ErrGetPolicyVersion}: {api_err}"
            ) from api_err
        except Exception as exc:
            raise RuntimeError(
                f"{errors.ErrGetPolicyVersion}: "
                f"request failed: {exc}"
            ) from exc

        if response.status_code != 200:
            api_err = self._parse_error(response)
            raise RuntimeError(
                f"{errors.ErrGetPolicyVersion}: {api_err}"
            )

        return models.PolicyVersion.from_dict(data)

    # CreatePolicyVersion — policy_version.go lines 221-249

    def create_policy_version(
        self, params: models.CreatePolicyVersionRequest
    ) -> models.PolicyVersion:
        """Create a policy version.

        See: https://techdocs.akamai.com/cloudlets/reference/post-policy-version
        """
        logger.debug("CreatePolicyVersion")

        val_err = (
            validation.validate_create_policy_version_request(
                params
            )
        )
        if val_err is not None:
            raise ValueError(
                f"{errors.ErrCreatePolicyVersion}: "
                f"{errors.ErrStructValidation}:\n{val_err}"
            )

        path = (
            f"/cloudlets/v3/policies/"
            f"{params.policy_id}/versions"
        )
        body = (
            params.create_policy_version.to_dict()
            if params.create_policy_version is not None
            else {}
        )

        try:
            response, data = self._session.exec(
                "POST",
                path,
                body=body,
                expect_json=True,
                error_parser=self._parse_error,
            )
        except errors.Error as api_err:
            raise RuntimeError(
                f"{errors.ErrCreatePolicyVersion}: {api_err}"
            ) from api_err
        except Exception as exc:
            raise RuntimeError(
                f"{errors.ErrCreatePolicyVersion}: "
                f"request failed: {exc}"
            ) from exc

        if response.status_code != 201:
            api_err = self._parse_error(response)
            raise RuntimeError(
                f"{errors.ErrCreatePolicyVersion}: {api_err}"
            )

        return models.PolicyVersion.from_dict(data)

    # DeletePolicyVersion — policy_version.go lines 251-277

    def delete_policy_version(
        self, params: models.DeletePolicyVersionRequest
    ) -> None:
        """Delete a policy version.

        See: https://techdocs.akamai.com/cloudlets/reference/delete-policy-version
        """
        logger.debug("DeletePolicyVersion")

        val_err = (
            validation.validate_delete_policy_version_request(
                params
            )
        )
        if val_err is not None:
            raise ValueError(
                f"{errors.ErrDeletePolicyVersion}: "
                f"{errors.ErrStructValidation}:\n{val_err}"
            )

        path = (
            f"/cloudlets/v3/policies/{params.policy_id}"
            f"/versions/{params.policy_version}"
        )

        try:
            response, _ = self._session.exec(
                "DELETE",
                path,
                error_parser=self._parse_error,
            )
        except errors.Error as api_err:
            raise RuntimeError(
                f"{errors.ErrDeletePolicyVersion}: {api_err}"
            ) from api_err
        except Exception as exc:
            raise RuntimeError(
                f"{errors.ErrDeletePolicyVersion}: "
                f"request failed: {exc}"
            ) from exc

        if response.status_code != 204:
            api_err = self._parse_error(response)
            raise RuntimeError(
                f"{errors.ErrDeletePolicyVersion}: {api_err}"
            )

    # UpdatePolicyVersion — policy_version.go lines 279-307

    def update_policy_version(
        self, params: models.UpdatePolicyVersionRequest
    ) -> models.PolicyVersion:
        """Update a policy version.

        See: https://techdocs.akamai.com/cloudlets/reference/put-policy-version
        """
        logger.debug("UpdatePolicyVersion")

        val_err = (
            validation.validate_update_policy_version_request(
                params
            )
        )
        if val_err is not None:
            raise ValueError(
                f"{errors.ErrUpdatePolicyVersion}: "
                f"{errors.ErrStructValidation}:\n{val_err}"
            )

        path = (
            f"/cloudlets/v3/policies/{params.policy_id}"
            f"/versions/{params.policy_version}"
        )
        body = (
            params.update_policy_version.to_dict()
            if params.update_policy_version is not None
            else {}
        )

        try:
            response, data = self._session.exec(
                "PUT",
                path,
                body=body,
                expect_json=True,
                error_parser=self._parse_error,
            )
        except errors.Error as api_err:
            raise RuntimeError(
                f"{errors.ErrUpdatePolicyVersion}: {api_err}"
            ) from api_err
        except Exception as exc:
            raise RuntimeError(
                f"{errors.ErrUpdatePolicyVersion}: "
                f"request failed: {exc}"
            ) from exc

        if response.status_code != 200:
            api_err = self._parse_error(response)
            raise RuntimeError(
                f"{errors.ErrUpdatePolicyVersion}: {api_err}"
            )

        return models.PolicyVersion.from_dict(data)

    # ListPolicyActivations — policy_activation.go lines 152-190

    def list_policy_activations(
        self, params: models.ListPolicyActivationsRequest
    ) -> models.PolicyActivations:
        """Return activation history for the selected policy.

        See: https://techdocs.akamai.com/cloudlets/reference/get-policy-activations
        """
        logger.debug("ListPolicyActivations")

        val_err = (
            validation.validate_list_policy_activations_request(
                params
            )
        )
        if val_err is not None:
            raise ValueError(
                f"{errors.ErrListPolicyActivations}: "
                f"{errors.ErrStructValidation}: {val_err}"
            )

        path = (
            f"/cloudlets/v3/policies/"
            f"{params.policy_id}/activations"
        )
        query: dict[str, str] = {}
        if params.size != 0:
            query["size"] = str(params.size)
        if params.page != 0:
            query["page"] = str(params.page)
        if query:
            path = f"{path}?{urlencode(query)}"

        try:
            response, data = self._session.exec(
                "GET",
                path,
                expect_json=True,
                error_parser=self._parse_error,
            )
        except errors.Error as api_err:
            raise RuntimeError(
                f"{errors.ErrListPolicyActivations}: "
                f"{api_err}"
            ) from api_err
        except Exception as exc:
            raise RuntimeError(
                f"{errors.ErrListPolicyActivations}: "
                f"request failed: {exc}"
            ) from exc

        if response.status_code != 200:
            api_err = self._parse_error(response)
            raise RuntimeError(
                f"{errors.ErrListPolicyActivations}: "
                f"{api_err}"
            )

        return models.PolicyActivations.from_dict(data)

    # ActivatePolicy — policy_activation.go lines 192-223

    def activate_policy(
        self, params: models.ActivatePolicyRequest
    ) -> models.PolicyActivation:
        """Activate the selected cloudlet policy version.

        See: https://techdocs.akamai.com/cloudlets/reference/post-policy-activations
        """
        logger.debug("ActivatePolicy")

        val_err = (
            validation.validate_activate_policy_request(params)
        )
        if val_err is not None:
            raise ValueError(
                f"{errors.ErrActivatePolicy}: "
                f"{errors.ErrStructValidation}: {val_err}"
            )

        path = (
            f"/cloudlets/v3/policies/"
            f"{params.policy_id}/activations"
        )
        body = {
            "operation": models.OperationActivation,
            "network": params.network,
            "policyVersion": params.policy_version,
        }

        try:
            response, data = self._session.exec(
                "POST",
                path,
                body=body,
                expect_json=True,
                error_parser=self._parse_error,
            )
        except errors.Error as api_err:
            raise RuntimeError(
                f"{errors.ErrActivatePolicy}: {api_err}"
            ) from api_err
        except Exception as exc:
            raise RuntimeError(
                f"{errors.ErrActivatePolicy}: "
                f"request failed: {exc}"
            ) from exc

        if response.status_code != 202:
            api_err = self._parse_error(response)
            raise RuntimeError(
                f"{errors.ErrActivatePolicy}: {api_err}"
            )

        return models.PolicyActivation.from_dict(data)

    # DeactivatePolicy — policy_activation.go lines 225-256

    def deactivate_policy(
        self, params: models.DeactivatePolicyRequest
    ) -> models.PolicyActivation:
        """Deactivate the selected cloudlet policy version.

        See: https://techdocs.akamai.com/cloudlets/reference/post-policy-activations
        """
        logger.debug("DeactivatePolicy")

        val_err = (
            validation.validate_deactivate_policy_request(params)
        )
        if val_err is not None:
            raise ValueError(
                f"{errors.ErrDeactivatePolicy}: "
                f"{errors.ErrStructValidation}: {val_err}"
            )

        path = (
            f"/cloudlets/v3/policies/"
            f"{params.policy_id}/activations"
        )
        body = {
            "operation": models.OperationDeactivation,
            "network": params.network,
            "policyVersion": params.policy_version,
        }

        try:
            response, data = self._session.exec(
                "POST",
                path,
                body=body,
                expect_json=True,
                error_parser=self._parse_error,
            )
        except errors.Error as api_err:
            raise RuntimeError(
                f"{errors.ErrDeactivatePolicy}: {api_err}"
            ) from api_err
        except Exception as exc:
            raise RuntimeError(
                f"{errors.ErrDeactivatePolicy}: "
                f"request failed: {exc}"
            ) from exc

        if response.status_code != 202:
            api_err = self._parse_error(response)
            raise RuntimeError(
                f"{errors.ErrDeactivatePolicy}: {api_err}"
            )

        return models.PolicyActivation.from_dict(data)

    # GetPolicyActivation — policy_activation.go lines 258-283

    def get_policy_activation(
        self, params: models.GetPolicyActivationRequest
    ) -> models.PolicyActivation:
        """Get the selected policy activation.

        See: https://techdocs.akamai.com/cloudlets/reference/get-policy-activation
        """
        logger.debug("GetPolicyActivation")

        val_err = (
            validation.validate_get_policy_activation_request(
                params
            )
        )
        if val_err is not None:
            raise ValueError(
                f"{errors.ErrGetPolicyActivation}: "
                f"{errors.ErrStructValidation}: {val_err}"
            )

        path = (
            f"/cloudlets/v3/policies/{params.policy_id}"
            f"/activations/{params.activation_id}"
        )

        try:
            response, data = self._session.exec(
                "GET",
                path,
                expect_json=True,
                error_parser=self._parse_error,
            )
        except errors.Error as api_err:
            raise RuntimeError(
                f"{errors.ErrGetPolicyActivation}: {api_err}"
            ) from api_err
        except Exception as exc:
            raise RuntimeError(
                f"{errors.ErrGetPolicyActivation}: "
                f"request failed: {exc}"
            ) from exc

        if response.status_code != 200:
            api_err = self._parse_error(response)
            raise RuntimeError(
                f"{errors.ErrGetPolicyActivation}: {api_err}"
            )

        return models.PolicyActivation.from_dict(data)
