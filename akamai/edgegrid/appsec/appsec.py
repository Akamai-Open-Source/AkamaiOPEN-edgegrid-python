# pylint: disable=too-many-lines,too-many-public-methods
"""Akamai Application Security API client implementation.

Provides the ``Client`` class implementing all Application Security API
operations: configurations, policies, rules, rate policies, reputation
profiles, match targets, WAF, IP/Geo, malware, SIEM, advanced settings,
and more.

Mirrors Go ``pkg/appsec`` interface and ``appsec`` struct from the
Akamai Open EdgeGrid Go v12 SDK.  The Go package composes ~50+
sub-interfaces into a single ``APPSEC`` interface; this module unifies
all endpoint methods in a single ``Client`` class.
"""

import logging
from dataclasses import asdict
from typing import Any

from akamai.edgegrid.session import Session
from akamai.edgegrid.appsec import models
from akamai.edgegrid.appsec import errors
from akamai.edgegrid.appsec import validation

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------
# Helper: dataclass -> JSON-ready body dict
# -----------------------------------------------------------------------


def _body(obj: Any) -> Any:
    """Convert a dataclass into a JSON-serialisable dict.

    Removes ``None`` values (mirrors Go ``omitempty`` tags) and strips
    path-parameter-only fields that carry ``json:"-"`` semantics (their
    names start with common path-param prefixes or they are documented as
    ``json:"-"`` in the model).

    For raw payloads (``json_payload_raw`` fields) the caller should pass
    the raw value directly instead of calling this helper.
    """
    if obj is None:
        return None
    try:
        raw = asdict(obj)
    except TypeError:
        return obj
    # Strip fields that are path parameters (json:"-" in Go).
    # These are always named config_id, version, policy_id, etc.
    path_params = {
        "config_id", "version", "policy_id", "activation_id",
        "rule_id", "group_id", "rate_policy_id", "reputation_profile_id",
        "target_id", "deny_id", "malware_policy_id", "api_id",
        "constraint_id", "json_payload_raw", "conditions_payload",
        "body", "policy", "request_body", "malware_policy_actions",
    }
    return {
        k: v for k, v in raw.items()
        if v is not None and k not in path_params
    }


# -----------------------------------------------------------------------
# Client
# -----------------------------------------------------------------------


class Client:  # pylint: disable=too-many-public-methods
    """Application Security API client.

    Provides methods for managing security configurations, policies, rules,
    rate policies, reputation profiles, match targets, and all other AppSec
    features via the Akamai Application Security API.

    Mirrors the Go ``APPSEC`` interface composed of ~50+ sub-interfaces.

    Usage::

        >>> from akamai.edgegrid.session import Session
        >>> from akamai.edgegrid.appsec.appsec import Client
        >>> session = Session(edgerc_path="~/.edgerc", section="default")
        >>> client = Client(session)
    """

    def __init__(self, session: Session) -> None:
        """Initialize the AppSec client.

        Mirrors Go ``appsec.Client(sess session.Session)`` constructor.

        Args:
            session: An authenticated Session instance for making API calls.
        """
        self._session = session

    # Expose sentinel so callers can catch ``Client.ErrBadRequest``
    # without importing the errors module directly.  Go defines the
    # symbol in ``errors.go`` for the same purpose.
    ErrBadRequest = errors.ErrBadRequest

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _exec(  # pylint: disable=too-many-arguments
        self,
        method: str,
        path: str,
        *,
        body: Any = None,
        expect_json: bool = True,
        params: dict[str, str] | None = None,
    ) -> tuple:
        """Execute an AppSec API request.

        Wraps ``session.exec`` with the AppSec-specific error parser so
        that HTTP >= 400 responses produce ``errors.Error`` instances.
        """
        return self._session.exec(
            method,
            path,
            body=body,
            expect_json=expect_json,
            params=params,
            error_parser=errors.Error.from_response,
        )

    # ==================================================================
    # Activations  (activations.go)
    # ==================================================================

    def get_activations(
        self, params: models.GetActivationsRequest
    ) -> dict | models.GetActivationsResponse:
        """Return the status of an activation.

        See: https://techdocs.akamai.com/application-security/reference/get-activation

        Mirrors Go ``appsec.GetActivations``.
        """
        logger.debug("GetActivations")

        err = validation.validate_get_activations_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = f"/appsec/v1/activations/{params.activation_id}"

        _, result = self._exec(
            "GET", uri,
            params={"updateLatestNetworkStatus": "true"},
        )
        return result

    def get_activation_history(
        self, params: models.GetActivationHistoryRequest
    ) -> dict:
        """List the activation history for a configuration.

        See: https://techdocs.akamai.com/application-security/reference/get-activation-history

        Mirrors Go ``appsec.GetActivationHistory``.
        """
        logger.debug("GetActivationHistory")

        err = validation.validate_get_activation_history_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = f"/appsec/v1/configs/{params.config_id}/activations"

        _, result = self._exec("GET", uri)
        return result

    def create_activations(  # pylint: disable=unused-argument
        self,
        params: models.CreateActivationsRequest,
        acknowledge_warnings: bool = False,
    ) -> dict:
        """Activate a configuration.

        If ``acknowledge_warnings`` is ``True`` and warnings are returned
        on the first attempt, a second attempt is made acknowledging the
        warnings.

        Mirrors Go ``appsec.CreateActivations``.
        """
        logger.debug("CreateActivations")

        uri = "/appsec/v1/activations"

        _, result = self._exec("POST", uri, body=_body(params))

        # Two-step: POST then GET the created activation
        activation_id = result.get("activationId", 0) if result else 0
        if activation_id:
            uri_get = f"/appsec/v1/activations/{activation_id}"
            _, result = self._exec("GET", uri_get)

        return result

    def remove_activations(
        self, params: models.RemoveActivationsRequest
    ) -> dict:
        """Deactivate a configuration.

        Mirrors Go ``appsec.RemoveActivations``.
        """
        logger.debug("RemoveActivations")

        uri = "/appsec/v1/activations"

        _, result = self._exec("POST", uri, body=_body(params))
        return result

    # ==================================================================
    # Configuration  (configuration.go)
    # ==================================================================

    def get_configurations(  # pylint: disable=unused-argument
        self, params: models.GetConfigurationsRequest
    ) -> dict | models.GetConfigurationsResponse:
        """List security configurations.

        Returns all security configurations visible to the current user.

        See: https://techdocs.akamai.com/application-security/reference/get-configs

        Mirrors Go ``appsec.GetConfigurations``.
        """
        logger.debug("GetConfigurations")

        uri = "/appsec/v1/configs"

        _, result = self._exec("GET", uri)
        return result

    def get_configuration(
        self, params: models.GetConfigurationRequest
    ) -> dict | models.GetConfigurationResponse:
        """Get a specific security configuration.

        See: https://techdocs.akamai.com/application-security/reference/get-config

        Mirrors Go ``appsec.GetConfiguration``.
        """
        logger.debug("GetConfiguration")

        err = validation.validate_get_configuration_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = f"/appsec/v1/configs/{params.config_id}"

        _, result = self._exec("GET", uri)
        return result

    def create_configuration(
        self, params: models.CreateConfigurationRequest
    ) -> dict | models.CreateConfigurationResponse:
        """Create a new security configuration.

        See: https://techdocs.akamai.com/application-security/reference/post-config

        Mirrors Go ``appsec.CreateConfiguration``.
        """
        logger.debug("CreateConfiguration")

        uri = "/appsec/v1/configs"

        _, result = self._exec("POST", uri, body=_body(params))
        return result

    def update_configuration(
        self, params: models.UpdateConfigurationRequest
    ) -> dict:
        """Update a security configuration name and description.

        See: https://techdocs.akamai.com/application-security/reference/put-config

        Mirrors Go ``appsec.UpdateConfiguration``.
        """
        logger.debug("UpdateConfiguration")

        err = validation.validate_update_configuration_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = f"/appsec/v1/configs/{params.config_id}"

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    def remove_configuration(
        self, params: models.RemoveConfigurationRequest
    ) -> dict:
        """Delete a security configuration.

        See: https://techdocs.akamai.com/application-security/reference/delete-config

        Mirrors Go ``appsec.RemoveConfiguration``.
        """
        logger.debug("RemoveConfiguration")

        err = validation.validate_remove_configuration_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = f"/appsec/v1/configs/{params.config_id}"

        _, result = self._exec("DELETE", uri, expect_json=False)
        return result

    # ==================================================================
    # ConfigurationClone  (configuration_clone.go)
    # ==================================================================

    def get_configuration_clone(
        self, params: models.GetConfigurationCloneRequest
    ) -> dict:
        """Get the details of a configuration version.

        See: https://techdocs.akamai.com/application-security/reference/get-config-version

        Mirrors Go ``appsec.GetConfigurationClone``.
        """
        logger.debug("GetConfigurationClone")

        err = validation.validate_get_configuration_clone_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
        )

        _, result = self._exec("GET", uri)
        return result

    def create_configuration_clone(
        self, params: models.CreateConfigurationCloneRequest
    ) -> dict:
        """Clone a security configuration.

        Mirrors Go ``appsec.CreateConfigurationClone``.
        Note: The Go URI uses a trailing slash on ``/configs/``.
        """
        logger.debug("CreateConfigurationClone")

        err = validation.validate_create_configuration_clone_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = "/appsec/v1/configs/"

        _, result = self._exec("POST", uri, body=_body(params))
        return result

    # ==================================================================
    # ConfigurationVersion  (configuration_version.go)
    # ==================================================================

    def get_configuration_versions(
        self, params: models.GetConfigurationVersionsRequest
    ) -> dict:
        """List configuration versions.

        Mirrors Go ``appsec.GetConfigurationVersions``.
        """
        logger.debug("GetConfigurationVersions")

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions?page=-1&detail=false"
        )
        _, result = self._exec("GET", uri)
        return result

    def get_configuration_version(
        self, params: models.GetConfigurationVersionRequest
    ) -> dict:
        """Get details for a specific configuration version.

        Mirrors Go ``appsec.GetConfigurationVersion``.
        """
        logger.debug("GetConfigurationVersion")

        err = validation.validate_get_configuration_version_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
        )

        _, result = self._exec("GET", uri)
        return result

    # ==================================================================
    # ConfigurationVersionClone  (configuration_version_clone.go)
    # ==================================================================

    def get_configuration_version_clone(
        self, params: models.GetConfigurationVersionCloneRequest
    ) -> dict:
        """Get details of a configuration version clone.

        Mirrors Go ``appsec.GetConfigurationVersionClone``.
        """
        logger.debug("GetConfigurationVersionClone")

        err = validation.validate_get_configuration_version_clone_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
        )

        _, result = self._exec("GET", uri)
        return result

    def remove_configuration_version_clone(
        self, params: models.RemoveConfigurationVersionCloneRequest
    ) -> dict:
        """Delete a configuration version clone.

        Mirrors Go ``appsec.RemoveConfigurationVersionClone``.
        """
        logger.debug("RemoveConfigurationVersionClone")

        err = validation.validate_remove_configuration_version_clone_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
        )

        _, result = self._exec("DELETE", uri)
        return result

    def create_configuration_version_clone(
        self, params: models.CreateConfigurationVersionCloneRequest
    ) -> dict:
        """Clone a configuration version.

        Mirrors Go ``appsec.CreateConfigurationVersionClone``.
        """
        logger.debug("CreateConfigurationVersionClone")

        err = validation.validate_create_configuration_version_clone_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions"
        )

        _, result = self._exec("POST", uri, body=_body(params))
        return result

    # ==================================================================
    # SecurityPolicy  (security_policy.go)
    # ==================================================================

    def get_security_policies(
        self, params: models.GetSecurityPoliciesRequest
    ) -> dict | models.GetSecurityPoliciesResponse:
        """List security policies for a configuration version.

        Mirrors Go ``appsec.GetSecurityPolicies``.
        """
        logger.debug("GetSecurityPolicies")

        err = validation.validate_get_security_policies_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies"
        )

        _, result = self._exec("GET", uri)
        return result

    def get_security_policy(
        self, params: models.GetSecurityPolicyRequest
    ) -> dict:
        """Get a specific security policy.

        Mirrors Go ``appsec.GetSecurityPolicy``.
        """
        logger.debug("GetSecurityPolicy")

        err = validation.validate_get_security_policy_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
        )

        _, result = self._exec("GET", uri)
        return result

    def create_security_policy(
        self, params: models.CreateSecurityPolicyRequest
    ) -> dict:
        """Create a security policy.

        Mirrors Go ``appsec.CreateSecurityPolicy``.
        """
        logger.debug("CreateSecurityPolicy")

        err = validation.validate_create_security_policy_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies"
        )

        _, result = self._exec("POST", uri, body=_body(params))
        return result

    def create_security_policy_with_default_protections(
        self, params: models.CreateSecurityPolicyWithDefaultProtectionsRequest
    ) -> dict:
        """Create a security policy with default protections enabled.

        Mirrors Go ``appsec.CreateSecurityPolicyWithDefaultProtections``.
        """
        logger.debug("CreateSecurityPolicyWithDefaultProtections")

        err = validation.validate_create_security_policy_with_default_protections_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/protections"
        )

        _, result = self._exec("POST", uri, body=_body(params))
        return result

    def update_security_policy(
        self, params: models.UpdateSecurityPolicyRequest
    ) -> dict:
        """Update a security policy.

        Mirrors Go ``appsec.UpdateSecurityPolicy``.
        """
        logger.debug("UpdateSecurityPolicy")

        err = validation.validate_update_security_policy_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    def remove_security_policy(
        self, params: models.RemoveSecurityPolicyRequest
    ) -> dict:
        """Delete a security policy.

        Mirrors Go ``appsec.RemoveSecurityPolicy``.
        """
        logger.debug("RemoveSecurityPolicy")

        err = validation.validate_remove_security_policy_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
        )

        _, result = self._exec("DELETE", uri, expect_json=False)
        return result

    # ==================================================================
    # SecurityPolicyClone  (security_policy_clone.go)
    # ==================================================================

    def get_security_policy_clone(
        self, params: models.GetSecurityPolicyCloneRequest
    ) -> dict:
        """Get details of a security policy clone.

        Mirrors Go ``appsec.GetSecurityPolicyClone``.
        """
        logger.debug("GetSecurityPolicyClone")

        err = validation.validate_get_security_policy_clone_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
        )

        _, result = self._exec("GET", uri)
        return result

    def get_security_policy_clones(
        self, params: models.GetSecurityPolicyClonesRequest
    ) -> dict:
        """List security policy clones for a configuration version.

        Mirrors Go ``appsec.GetSecurityPolicyClones``.
        """
        logger.debug("GetSecurityPolicyClone")

        err = validation.validate_get_security_policy_clones_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies"
        )

        _, result = self._exec(
            "GET", uri,
            params={"detail": "true", "notMatched": "false"},
        )
        return result

    def create_security_policy_clone(
        self, params: models.CreateSecurityPolicyCloneRequest
    ) -> dict:
        """Clone a security policy.

        Mirrors Go ``appsec.CreateSecurityPolicyClone``.
        """
        logger.debug("CreateSecurityPolicyClone")

        err = validation.validate_create_security_policy_clone_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies"
        )

        _, result = self._exec("POST", uri, body=_body(params))
        return result

    # ==================================================================
    # PolicyProtections  (security_policy_protections.go)
    # ==================================================================

    def get_policy_protections(
        self, params: models.GetPolicyProtectionsRequest
    ) -> dict:
        """Get policy protections settings.

        Mirrors Go ``appsec.GetPolicyProtections``.
        """
        logger.debug("GetPolicyProtections")

        err = validation.validate_get_policy_protections_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_policy_protections(
        self, params: models.UpdatePolicyProtectionsRequest
    ) -> dict:
        """Update policy protections settings.

        Mirrors Go ``appsec.UpdatePolicyProtections``.
        """
        logger.debug("UpdatePolicyProtections")

        err = validation.validate_update_policy_protections_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # CustomRule  (custom_rule.go)
    # ==================================================================

    def get_custom_rules(
        self, params: models.GetCustomRulesRequest
    ) -> dict | models.GetCustomRulesResponse:
        """List custom rules for a configuration.

        Mirrors Go ``appsec.GetCustomRules``.
        """
        logger.debug("GetCustomRules")

        err = validation.validate_get_custom_rules_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/custom-rules"
        )

        _, result = self._exec("GET", uri)
        return result

    def get_custom_rule(
        self, params: models.GetCustomRuleRequest
    ) -> dict:
        """Get a specific custom rule.

        Mirrors Go ``appsec.GetCustomRule``.
        """
        logger.debug("GetCustomRule")

        err = validation.validate_get_custom_rule_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/custom-rules/{params.id}"
        )

        _, result = self._exec("GET", uri)
        return result

    def create_custom_rule(
        self, params: models.CreateCustomRuleRequest
    ) -> dict:
        """Create a custom rule.

        Mirrors Go ``appsec.CreateCustomRule``.
        """
        logger.debug("CreateCustomRule")

        err = validation.validate_create_custom_rule_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/custom-rules"
        )

        _, result = self._exec(
            "POST", uri, body=params.json_payload_raw,
        )
        return result

    def update_custom_rule(
        self, params: models.UpdateCustomRuleRequest
    ) -> dict:
        """Update a custom rule.

        Mirrors Go ``appsec.UpdateCustomRule``.
        """
        logger.debug("UpdateCustomRule")

        err = validation.validate_update_custom_rule_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/custom-rules/{params.id}"
        )

        _, result = self._exec(
            "PUT", uri, body=params.json_payload_raw,
        )
        return result

    def remove_custom_rule(
        self, params: models.RemoveCustomRuleRequest
    ) -> dict:
        """Delete a custom rule.

        Mirrors Go ``appsec.RemoveCustomRule``.
        """
        logger.debug("RemoveCustomRule")

        err = validation.validate_remove_custom_rule_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/custom-rules/{params.id}"
        )

        _, result = self._exec("DELETE", uri, expect_json=False)
        return result

    def get_custom_rules_usage(
        self, params: models.GetCustomRulesUsageRequest
    ) -> dict:
        """Get usage info for custom rules in a configuration version.

        Mirrors Go ``appsec.GetCustomRulesUsage``.
        """
        logger.debug("GetCustomRulesUsage")

        err = validation.validate_get_custom_rules_usage_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/custom-rules/usage"
        )

        _, result = self._exec(
            "POST", uri, body=params.request_body,
        )
        return result

    # ==================================================================
    # CustomRuleAction  (custom_rule_action.go)
    # ==================================================================

    def get_custom_rule_actions(
        self, params: models.GetCustomRuleActionsRequest
    ) -> dict:
        """List custom rule actions for a policy.

        Mirrors Go ``appsec.GetCustomRuleActions``.
        """
        logger.debug("GetCustomRuleActions")

        err = validation.validate_get_custom_rule_actions_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/custom-rules"
        )

        _, result = self._exec("GET", uri)
        return result

    def get_custom_rule_action(
        self, params: models.GetCustomRuleActionRequest
    ) -> dict:
        """Get the action for a specific custom rule in a policy.

        Mirrors Go ``appsec.GetCustomRuleAction``.
        """
        logger.debug("GetCustomRuleAction")

        err = validation.validate_get_custom_rule_action_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/custom-rules/{params.rule_id}"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_custom_rule_action(
        self, params: models.UpdateCustomRuleActionRequest
    ) -> dict:
        """Update the action for a custom rule in a policy.

        Mirrors Go ``appsec.UpdateCustomRuleAction``.
        """
        logger.debug("UpdateCustomRuleAction")

        err = validation.validate_update_custom_rule_action_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/custom-rules/{params.rule_id}"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # CustomDeny  (custom_deny.go)
    # ==================================================================

    def get_custom_deny_list(
        self, params: models.GetCustomDenyListRequest
    ) -> dict:
        """List custom deny actions for a configuration version.

        Mirrors Go ``appsec.GetCustomDenyList``.
        """
        logger.debug("GetCustomDenyList")

        err = validation.validate_get_custom_deny_list_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/custom-deny"
        )

        _, result = self._exec("GET", uri)
        return result

    def get_custom_deny(
        self, params: models.GetCustomDenyRequest
    ) -> dict:
        """Get a specific custom deny action.

        Mirrors Go ``appsec.GetCustomDeny``.
        """
        logger.debug("GetCustomDeny")

        err = validation.validate_get_custom_deny_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/custom-deny/{params.id}"
        )

        _, result = self._exec("GET", uri)
        return result

    def create_custom_deny(
        self, params: models.CreateCustomDenyRequest
    ) -> dict:
        """Create a custom deny action.

        Mirrors Go ``appsec.CreateCustomDeny``.
        """
        logger.debug("CreateCustomDeny")

        err = validation.validate_create_custom_deny_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/custom-deny"
        )

        _, result = self._exec(
            "POST", uri, body=params.json_payload_raw,
        )
        return result

    def update_custom_deny(
        self, params: models.UpdateCustomDenyRequest
    ) -> dict:
        """Update a custom deny action.

        Mirrors Go ``appsec.UpdateCustomDeny``.
        """
        logger.debug("UpdateCustomDeny")

        err = validation.validate_update_custom_deny_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/custom-deny/{params.id}"
        )

        _, result = self._exec(
            "PUT", uri, body=params.json_payload_raw,
        )
        return result

    def remove_custom_deny(
        self, params: models.RemoveCustomDenyRequest
    ) -> dict:
        """Delete a custom deny action.

        Mirrors Go ``appsec.RemoveCustomDeny``.
        """
        logger.debug("RemoveCustomDeny")

        err = validation.validate_remove_custom_deny_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/custom-deny/{params.id}"
        )

        _, result = self._exec("DELETE", uri, expect_json=False)
        return result

    # ==================================================================
    # RatePolicy  (rate_policy.go)
    # ==================================================================

    def get_rate_policies(
        self, params: models.GetRatePoliciesRequest
    ) -> dict | models.GetRatePoliciesResponse:
        """List rate policies for a configuration version.

        Mirrors Go ``appsec.GetRatePolicies``.
        """
        logger.debug("GetRatePolicies")

        err = validation.validate_get_rate_policies_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/rate-policies"
        )

        _, result = self._exec("GET", uri)
        return result

    def get_rate_policy(
        self, params: models.GetRatePolicyRequest
    ) -> dict:
        """Get a specific rate policy.

        Mirrors Go ``appsec.GetRatePolicy``.
        """
        logger.debug("GetRatePolicy")

        err = validation.validate_get_rate_policy_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/rate-policies/{params.rate_policy_id}"
        )

        _, result = self._exec("GET", uri)
        return result

    def create_rate_policy(
        self, params: models.CreateRatePolicyRequest
    ) -> dict:
        """Create a rate policy.

        Mirrors Go ``appsec.CreateRatePolicy``.
        """
        logger.debug("CreateRatePolicy")

        err = validation.validate_create_rate_policy_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/rate-policies"
        )

        _, result = self._exec(
            "POST", uri, body=params.json_payload_raw,
        )
        return result

    def update_rate_policy(
        self, params: models.UpdateRatePolicyRequest
    ) -> dict:
        """Update a rate policy.

        Mirrors Go ``appsec.UpdateRatePolicy``.
        """
        logger.debug("UpdateRatePolicy")

        err = validation.validate_update_rate_policy_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/rate-policies/{params.rate_policy_id}"
        )

        _, result = self._exec(
            "PUT", uri, body=params.json_payload_raw,
        )
        return result

    def remove_rate_policy(
        self, params: models.RemoveRatePolicyRequest
    ) -> dict:
        """Delete a rate policy.

        Mirrors Go ``appsec.RemoveRatePolicy``.
        """
        logger.debug("RemoveRatePolicy")

        err = validation.validate_remove_rate_policy_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/rate-policies/{params.rate_policy_id}"
        )

        _, result = self._exec("DELETE", uri, expect_json=False)
        return result

    # ==================================================================
    # RatePolicyAction  (rate_policy_action.go)
    # ==================================================================

    def get_rate_policy_actions(
        self, params: models.GetRatePolicyActionsRequest
    ) -> dict:
        """List rate policy actions for a policy.

        Mirrors Go ``appsec.GetRatePolicyActions``.
        """
        logger.debug("GetRatePolicyActions")

        err = validation.validate_get_rate_policy_actions_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/rate-policies"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_rate_policy_action(
        self, params: models.UpdateRatePolicyActionRequest
    ) -> dict:
        """Update the action for a rate policy in a policy.

        Mirrors Go ``appsec.UpdateRatePolicyAction``.
        """
        logger.debug("UpdateRatePolicyAction")

        err = validation.validate_update_rate_policy_action_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/rate-policies/{params.rate_policy_id}"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # Eval  (eval.go)
    # ==================================================================

    def get_evals(
        self, params: models.GetEvalsRequest
    ) -> dict:
        """Get evaluation mode settings for a policy (plural variant).

        Mirrors Go ``appsec.GetEvals``.
        """
        logger.debug("GetEvals")

        err = validation.validate_get_evals_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/mode"
        )

        _, result = self._exec("GET", uri)
        return result

    def get_eval(
        self, params: models.GetEvalRequest
    ) -> dict:
        """Get evaluation mode settings for a policy.

        Mirrors Go ``appsec.GetEval``.
        """
        logger.debug("GetEval")

        err = validation.validate_get_eval_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/mode"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_eval(
        self, params: models.UpdateEvalRequest
    ) -> dict:
        """Update evaluation mode for a policy.

        Mirrors Go ``appsec.UpdateEval``.
        """
        logger.debug("UpdateEval")

        err = validation.validate_update_eval_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/eval"
        )

        _, result = self._exec("POST", uri, body=_body(params))
        return result

    def remove_eval(
        self, params: models.RemoveEvalRequest
    ) -> dict:
        """Remove evaluation mode from a policy.

        Mirrors Go ``appsec.RemoveEval``.
        """
        logger.debug("RemoveEval")

        err = validation.validate_remove_eval_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/eval"
        )

        _, result = self._exec("POST", uri, body=_body(params))
        return result

    # ==================================================================
    # EvalRule  (eval_rule.go)
    # ==================================================================

    def get_eval_rules(
        self, params: models.GetEvalRulesRequest
    ) -> dict:
        """List evaluation rules for a policy.

        Mirrors Go ``appsec.GetEvalRules``.
        """
        logger.debug("GetEvalRules")

        err = validation.validate_get_eval_rules_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/eval-rules"
        )

        _, result = self._exec(
            "GET", uri,
            params={"includeConditionException": "true"},
        )
        return result

    def get_eval_rule(
        self, params: models.GetEvalRuleRequest
    ) -> dict:
        """Get a specific evaluation rule.

        Mirrors Go ``appsec.GetEvalRule``.
        """
        logger.debug("GetEvalRule")

        err = validation.validate_get_eval_rule_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/eval-rules/{params.rule_id}"
        )

        _, result = self._exec(
            "GET", uri,
            params={"includeConditionException": "true"},
        )
        return result

    def update_eval_rule(
        self, params: models.UpdateEvalRuleRequest
    ) -> dict:
        """Update an evaluation rule action and condition/exception.

        Mirrors Go ``appsec.UpdateEvalRule``.
        """
        logger.debug("UpdateEvalRule")

        err = validation.validate_update_eval_rule_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/eval-rules/{params.rule_id}"
            f"/action-condition-exception"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # EvalGroup  (eval_group.go)
    # ==================================================================

    def get_eval_groups(
        self, params: models.GetAttackGroupsRequest
    ) -> dict:
        """List evaluation attack groups for a policy.

        Mirrors Go ``appsec.GetEvalGroups``.
        """
        logger.debug("GetEvalGroups")

        err = validation.validate_get_attack_groups_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/eval-groups"
        )

        _, result = self._exec(
            "GET", uri,
            params={"includeConditionException": "true"},
        )
        return result

    def get_eval_group(
        self, params: models.GetAttackGroupRequest
    ) -> dict:
        """Get a specific evaluation attack group.

        Mirrors Go ``appsec.GetEvalGroup``.
        """
        logger.debug("GetEvalGroup")

        err = validation.validate_get_attack_group_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/eval-groups/{params.group}"
        )

        _, result = self._exec(
            "GET", uri,
            params={"includeConditionException": "true"},
        )
        return result

    def update_eval_group(
        self, params: models.UpdateAttackGroupRequest
    ) -> dict:
        """Update an evaluation attack group.

        Mirrors Go ``appsec.UpdateEvalGroup``.
        """
        logger.debug("UpdateEvalGroup")

        err = validation.validate_update_attack_group_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/eval-groups/{params.group}"
            f"/action-condition-exception"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # EvalPenaltyBox  (eval_penalty_box.go)
    # ==================================================================

    def get_eval_penalty_box(
        self, params: models.GetPenaltyBoxRequest
    ) -> dict:
        """Get eval penalty box settings for a policy.

        Mirrors Go ``appsec.GetEvalPenaltyBox``.
        """
        logger.debug("GetEvalPenaltyBox")

        err = validation.validate_get_penalty_box_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/eval-penalty-box"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_eval_penalty_box(
        self, params: models.UpdatePenaltyBoxRequest
    ) -> dict:
        """Update eval penalty box settings for a policy.

        Mirrors Go ``appsec.UpdateEvalPenaltyBox``.
        """
        logger.debug("UpdateEvalPenaltyBox")

        err = validation.validate_update_penalty_box_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/eval-penalty-box"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # EvalPenaltyBoxConditions  (eval_penalty_box_conditions.go)
    # ==================================================================

    def get_eval_penalty_box_conditions(
        self, params: models.GetPenaltyBoxConditionsRequest
    ) -> dict:
        """Get eval penalty box conditions for a policy.

        Mirrors Go ``appsec.GetEvalPenaltyBoxConditions``.
        """
        logger.debug("GetEvalPenaltyBoxConditions")

        err = validation.validate_get_penalty_box_conditions_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/eval-penalty-box/conditions"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_eval_penalty_box_conditions(
        self, params: models.UpdatePenaltyBoxConditionsRequest
    ) -> dict:
        """Update eval penalty box conditions for a policy.

        Mirrors Go ``appsec.UpdateEvalPenaltyBoxConditions``.
        """
        logger.debug("UpdateEvalPenaltyBoxConditions")

        err = validation.validate_update_penalty_box_conditions_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/eval-penalty-box/conditions"
        )

        _, result = self._exec(
            "PUT", uri, body=params.conditions_payload,
        )
        return result

    # ==================================================================
    # AttackGroup  (attack_group.go)
    # ==================================================================

    def get_attack_groups(
        self, params: models.GetAttackGroupsRequest
    ) -> dict | models.GetAttackGroupsResponse:
        """List attack groups for a policy.

        Mirrors Go ``appsec.GetAttackGroups``.
        """
        logger.debug("GetAttackGroups")

        err = validation.validate_get_attack_groups_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/attack-groups"
        )

        _, result = self._exec(
            "GET", uri,
            params={"includeConditionException": "true"},
        )
        return result

    def get_attack_group(
        self, params: models.GetAttackGroupRequest
    ) -> dict:
        """Get a specific attack group.

        Mirrors Go ``appsec.GetAttackGroup``.
        """
        logger.debug("GetAttackGroup")

        err = validation.validate_get_attack_group_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/attack-groups/{params.group}"
        )

        _, result = self._exec(
            "GET", uri,
            params={"includeConditionException": "true"},
        )
        return result

    def update_attack_group(
        self, params: models.UpdateAttackGroupRequest
    ) -> dict:
        """Update an attack group action and condition/exception.

        Mirrors Go ``appsec.UpdateAttackGroup``.
        """
        logger.debug("UpdateAttackGroup")

        err = validation.validate_update_attack_group_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/attack-groups/{params.group}"
            f"/action-condition-exception"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # ReputationProfile  (reputation_profile.go)
    # ==================================================================

    def get_reputation_profiles(
        self, params: models.GetReputationProfilesRequest
    ) -> dict:
        """List reputation profiles for a config version.

        Mirrors Go ``appsec.GetReputationProfiles``.
        """
        logger.debug("GetReputationProfiles")

        err = validation.validate_get_reputation_profiles_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/reputation-profiles"
        )

        _, result = self._exec("GET", uri)
        return result

    def get_reputation_profile(
        self, params: models.GetReputationProfileRequest
    ) -> dict:
        """Get a specific reputation profile.

        Mirrors Go ``appsec.GetReputationProfile``.
        """
        logger.debug("GetReputationProfile")

        err = validation.validate_get_reputation_profile_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/reputation-profiles/{params.reputation_profile_id}"
        )

        _, result = self._exec("GET", uri)
        return result

    def create_reputation_profile(
        self, params: models.CreateReputationProfileRequest
    ) -> dict:
        """Create a reputation profile.

        Mirrors Go ``appsec.CreateReputationProfile``.
        """
        logger.debug("CreateReputationProfile")

        err = validation.validate_create_reputation_profile_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/reputation-profiles"
        )

        _, result = self._exec(
            "POST", uri, body=params.json_payload_raw,
        )
        return result

    def update_reputation_profile(
        self, params: models.UpdateReputationProfileRequest
    ) -> dict:
        """Update a reputation profile.

        Mirrors Go ``appsec.UpdateReputationProfile``.
        """
        logger.debug("UpdateReputationProfile")

        err = validation.validate_update_reputation_profile_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/reputation-profiles/{params.reputation_profile_id}"
        )

        _, result = self._exec(
            "PUT", uri, body=params.json_payload_raw,
        )
        return result

    def remove_reputation_profile(
        self, params: models.RemoveReputationProfileRequest
    ) -> dict:
        """Remove a reputation profile.

        Mirrors Go ``appsec.RemoveReputationProfile``.
        """
        logger.debug("RemoveReputationProfile")

        err = validation.validate_remove_reputation_profile_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/reputation-profiles/{params.reputation_profile_id}"
        )

        _, result = self._exec("DELETE", uri)
        return result

    # ==================================================================
    # ReputationProfileAction  (reputation_profile_action.go)
    # ==================================================================

    def get_reputation_profile_actions(
        self, params: models.GetReputationProfileActionsRequest
    ) -> dict:
        """List reputation profile actions for a policy.

        Mirrors Go ``appsec.GetReputationProfileActions``.
        """
        logger.debug("GetReputationProfileActions")

        err = validation.validate_get_reputation_profile_actions_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/reputation-profiles"
        )

        _, result = self._exec("GET", uri)
        return result

    def get_reputation_profile_action(
        self, params: models.GetReputationProfileActionRequest
    ) -> dict:
        """Get a specific reputation profile action.

        Mirrors Go ``appsec.GetReputationProfileAction``.
        """
        logger.debug("GetReputationProfileAction")

        err = validation.validate_get_reputation_profile_action_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/reputation-profiles/{params.reputation_profile_id}"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_reputation_profile_action(
        self, params: models.UpdateReputationProfileActionRequest
    ) -> dict:
        """Update a reputation profile action.

        Mirrors Go ``appsec.UpdateReputationProfileAction``.
        """
        logger.debug("UpdateReputationProfileAction")

        err = validation.validate_update_reputation_profile_action_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/reputation-profiles/{params.reputation_profile_id}"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # ReputationAnalysis  (reputation_analysis.go)
    # ==================================================================

    def get_reputation_analysis(
        self, params: models.GetReputationAnalysisRequest
    ) -> dict:
        """Get reputation analysis settings for a policy.

        Mirrors Go ``appsec.GetReputationAnalysis``.
        """
        logger.debug("GetReputationAnalysis")

        err = validation.validate_get_reputation_analysis_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/reputation-analysis"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_reputation_analysis(
        self, params: models.UpdateReputationAnalysisRequest
    ) -> dict:
        """Update reputation analysis settings for a policy.

        Mirrors Go ``appsec.UpdateReputationAnalysis``.
        """
        logger.debug("UpdateReputationAnalysis")

        err = validation.validate_update_reputation_analysis_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/reputation-analysis"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    def remove_reputation_analysis(
        self, params: models.RemoveReputationAnalysisRequest
    ) -> dict:
        """Remove reputation analysis settings for a policy.

        Mirrors Go ``appsec.RemoveReputationAnalysis``.
        """
        logger.debug("RemoveReputationAnalysis")

        err = validation.validate_remove_reputation_analysis_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/reputation-analysis"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # MatchTarget  (match_target.go)
    # ==================================================================

    def get_match_targets(
        self, params: models.GetMatchTargetsRequest
    ) -> dict | models.GetMatchTargetsResponse:
        """List match targets for a config version.

        Mirrors Go ``appsec.GetMatchTargets``.
        """
        logger.debug("GetMatchTargets")

        err = validation.validate_get_match_targets_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/match-targets"
        )

        _, result = self._exec("GET", uri)
        return result

    def get_match_target(
        self, params: models.GetMatchTargetRequest
    ) -> dict:
        """Get a specific match target.

        Mirrors Go ``appsec.GetMatchTarget``.
        """
        logger.debug("GetMatchTarget")

        err = validation.validate_get_match_target_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/match-targets/{params.target_id}"
        )

        _, result = self._exec(
            "GET", uri,
            params={"includeChildObjectName": "true"},
        )
        return result

    def create_match_target(
        self, params: models.CreateMatchTargetRequest
    ) -> dict:
        """Create a match target.

        Mirrors Go ``appsec.CreateMatchTarget``.
        """
        logger.debug("CreateMatchTarget")

        err = validation.validate_create_match_target_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/match-targets"
        )

        _, result = self._exec(
            "POST", uri, body=params.json_payload_raw,
        )
        return result

    def update_match_target(
        self, params: models.UpdateMatchTargetRequest
    ) -> dict:
        """Update a match target.

        Mirrors Go ``appsec.UpdateMatchTarget``.
        """
        logger.debug("UpdateMatchTarget")

        err = validation.validate_update_match_target_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/match-targets/{params.target_id}"
        )

        _, result = self._exec(
            "PUT", uri, body=params.json_payload_raw,
        )
        return result

    def remove_match_target(
        self, params: models.RemoveMatchTargetRequest
    ) -> dict:
        """Remove a match target.

        Mirrors Go ``appsec.RemoveMatchTarget``.
        """
        logger.debug("RemoveMatchTarget")

        err = validation.validate_remove_match_target_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/match-targets/{params.target_id}"
        )

        _, result = self._exec("DELETE", uri)
        return result

    # ==================================================================
    # MatchTargetSequence  (match_target_sequence.go)
    # ==================================================================

    def get_match_target_sequence(
        self, params: models.GetMatchTargetSequenceRequest
    ) -> dict:
        """Get match target sequence for a configuration.

        Mirrors Go ``appsec.GetMatchTargetSequence``.
        """
        logger.debug("GetMatchTargetSequence")

        err = validation.validate_get_match_target_sequence_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/match-targets/sequence"
        )

        qp: dict[str, str] = {}


        _, result = self._exec("GET", uri, params=qp if qp else None)
        return result

    def update_match_target_sequence(
        self, params: models.UpdateMatchTargetSequenceRequest
    ) -> dict:
        """Update match target sequence.

        Mirrors Go ``appsec.UpdateMatchTargetSequence``.
        """
        logger.debug("UpdateMatchTargetSequence")

        err = validation.validate_update_match_target_sequence_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/match-targets/sequence"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # Rule  (rule.go)
    # ==================================================================

    def get_rules(
        self, params: models.GetRulesRequest
    ) -> dict:
        """List rules for a policy.

        Mirrors Go ``appsec.GetRules``.
        """
        logger.debug("GetRules")

        err = validation.validate_get_rules_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/rules"
        )

        _, result = self._exec(
            "GET", uri,
            params={"includeConditionException": "true"},
        )
        return result

    def get_rule(
        self, params: models.GetRuleRequest
    ) -> dict:
        """Get a specific rule.

        Mirrors Go ``appsec.GetRule``.
        """
        logger.debug("GetRule")

        err = validation.validate_get_rule_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/rules/{params.rule_id}"
        )

        _, result = self._exec(
            "GET", uri,
            params={"includeConditionException": "true"},
        )
        return result

    def update_rule(
        self, params: models.UpdateRuleRequest
    ) -> dict:
        """Update a rule action and condition/exception.

        Mirrors Go ``appsec.UpdateRule``.
        """
        logger.debug("UpdateRule")

        err = validation.validate_update_rule_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/rules/{params.rule_id}"
            f"/action-condition-exception"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    def update_rule_condition_exception(
        self, params: models.UpdateConditionExceptionRequest
    ) -> dict:
        """Update a rule's condition/exception without changing its action.

        Mirrors Go ``appsec.UpdateRuleConditionException``.
        """
        logger.debug("UpdateRuleConditionException")

        err = validation.validate_update_condition_exception_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/rules/{params.rule_id}"
            f"/condition-exception"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # RuleUpgrade  (rule_upgrade.go)
    # ==================================================================

    def get_rule_upgrade(
        self, params: models.GetRuleUpgradeRequest
    ) -> dict:
        """Get rule upgrade details for a policy.

        Mirrors Go ``appsec.GetRuleUpgrade``.
        """
        logger.debug("GetRuleUpgrade")

        err = validation.validate_get_rule_upgrade_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/rules/upgrade-details"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_rule_upgrade(
        self, params: models.UpdateRuleUpgradeRequest
    ) -> dict:
        """Upgrade KRS rules for a policy.

        Mirrors Go ``appsec.UpdateRuleUpgrade``.
        """
        logger.debug("UpdateRuleUpgrade")

        err = validation.validate_update_rule_upgrade_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/rules"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # PenaltyBox  (penalty_box.go)
    # ==================================================================

    def get_penalty_box(
        self, params: models.GetPenaltyBoxRequest
    ) -> dict:
        """Get penalty box settings for a policy.

        Mirrors Go ``appsec.GetPenaltyBox``.
        """
        logger.debug("GetPenaltyBox")

        err = validation.validate_get_penalty_box_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/penalty-box"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_penalty_box(
        self, params: models.UpdatePenaltyBoxRequest
    ) -> dict:
        """Update penalty box settings for a policy.

        Mirrors Go ``appsec.UpdatePenaltyBox``.
        """
        logger.debug("UpdatePenaltyBox")

        err = validation.validate_update_penalty_box_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/penalty-box"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # PenaltyBoxConditions  (penalty_box_conditions.go)
    # ==================================================================

    def get_penalty_box_conditions(
        self, params: models.GetPenaltyBoxConditionsRequest
    ) -> dict:
        """Get penalty box conditions for a policy.

        Mirrors Go ``appsec.GetPenaltyBoxConditions``.
        """
        logger.debug("GetPenaltyBoxConditions")

        err = validation.validate_get_penalty_box_conditions_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/penalty-box/conditions"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_penalty_box_conditions(
        self, params: models.UpdatePenaltyBoxConditionsRequest
    ) -> dict:
        """Update penalty box conditions for a policy.

        Mirrors Go ``appsec.UpdatePenaltyBoxConditions``.
        """
        logger.debug("UpdatePenaltyBoxConditions")

        err = validation.validate_update_penalty_box_conditions_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/penalty-box/conditions"
        )

        _, result = self._exec(
            "PUT", uri, body=params.conditions_payload,
        )
        return result

    # ==================================================================
    # RapidRule  (rapid_rule.go)
    # ==================================================================

    def get_rapid_rules(
        self, params: models.GetRapidRulesRequest
    ) -> dict:
        """List rapid rules for a policy.

        If ``rule_id`` is set, filters to that single rule.

        Mirrors Go ``appsec.GetRapidRules``.
        """
        logger.debug("GetRapidRules")

        err = validation.validate_get_rapid_rules_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/rapid-rules"
        )

        qp: dict[str, str] = {}
        if params.include_expiry_details:
            qp["includeExpiryDetails"] = "true"

        _, result = self._exec("GET", uri, params=qp if qp else None)

        if params.rule_id and result:
            rules = result.get("ruleActions", [])
            filtered = [r for r in rules if r.get("id") == params.rule_id]
            return {"ruleActions": filtered}

        return result

    def update_rapid_rule_exception(
        self, params: models.UpdateRapidRuleExceptionRequest
    ) -> dict:
        """Update a rapid rule condition/exception.

        Mirrors Go ``appsec.UpdateRapidRuleException``.
        """
        logger.debug("UpdateRapidRuleException")

        err = validation.validate_update_rapid_rule_exception_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/rapid-rules/{params.rule_id}"
            f"/condition-exception"
        )

        _, result = self._exec("PUT", uri, body=params.body)
        return result

    def get_rapid_rules_default_action(
        self, params: models.GetRapidRulesRequest
    ) -> dict:
        """Get rapid rules default action for a policy.

        Mirrors Go ``appsec.GetRapidRulesDefaultAction``.
        """
        logger.debug("GetRapidRulesDefaultAction")

        err = validation.validate_get_rapid_rules_default_action_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/rapid-rules/action"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_rapid_rules_default_action(
        self,
        params: models.UpdateRapidRulesDefaultActionRequest,
    ) -> dict:
        """Update rapid rules default action for a policy.

        Mirrors Go ``appsec.UpdateRapidRulesDefaultAction``.
        """
        logger.debug("UpdateRapidRulesDefaultAction")

        err = validation.validate_update_rapid_rules_default_action_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/rapid-rules/action"
        )

        _, result = self._exec("PUT", uri, body=_body(params.body))
        return result

    def get_rapid_rules_status(
        self, params: models.GetRapidRulesRequest
    ) -> dict:
        """Get rapid rules status for a policy.

        Mirrors Go ``appsec.GetRapidRulesStatus``.
        """
        logger.debug("GetRapidRulesStatus")

        err = validation.validate_get_rapid_rules_status_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/rapid-rules/status"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_rapid_rules_status(
        self, params: models.UpdateRapidRulesStatusRequest
    ) -> dict:
        """Update rapid rules status for a policy.

        Mirrors Go ``appsec.UpdateRapidRulesStatus``.
        """
        logger.debug("UpdateRapidRulesStatus")

        err = validation.validate_update_rapid_rules_status_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/rapid-rules/status"
        )

        _, result = self._exec("PUT", uri, body=_body(params.body))
        return result

    def update_rapid_rule_action(
        self, params: models.UpdateRapidRuleActionRequest
    ) -> dict:
        """Update a rapid rule action.

        Mirrors Go ``appsec.UpdateRapidRuleAction``.
        """
        logger.debug("UpdateRapidRuleAction")

        err = validation.validate_update_rapid_rule_action_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/rapid-rules/{params.rule_id}"
            f"/versions/{params.rule_version}"
            f"/action"
        )

        _, result = self._exec("PUT", uri, body=_body(params.body))
        return result

    def update_rapid_rule_action_lock(
        self, params: models.UpdateRapidRuleActionLockRequest
    ) -> dict:
        """Update a rapid rule action lock.

        Mirrors Go ``appsec.UpdateRapidRuleActionLock``.
        """
        logger.debug("UpdateRapidRuleActionLock")

        err = validation.validate_update_rapid_rule_action_lock_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/rapid-rules/{params.rule_id}"
            f"/lock"
        )

        _, result = self._exec("PUT", uri, body=_body(params.body))
        return result

    # ==================================================================
    # WAFMode  (waf_mode.go)
    # ==================================================================

    def get_waf_mode(
        self, params: models.GetWAFModeRequest
    ) -> dict | models.GetWAFModeResponse:
        """Get WAF mode for a policy.

        Mirrors Go ``appsec.GetWAFMode``.
        """
        logger.debug("GetWAFMode")

        err = validation.validate_get_waf_mode_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/mode"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_waf_mode(
        self, params: models.UpdateWAFModeRequest
    ) -> dict:
        """Update WAF mode for a policy.

        Mirrors Go ``appsec.UpdateWAFMode``.
        """
        logger.debug("UpdateWAFMode")

        err = validation.validate_update_waf_mode_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/mode"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # WAFProtection  (waf_protection.go)
    # ==================================================================

    def get_waf_protection(
        self, params: models.GetWAFProtectionRequest
    ) -> dict:
        """Get WAF protection settings for a policy.

        Mirrors Go ``appsec.GetWAFProtection``.
        """
        logger.debug("GetWAFProtection")

        err = validation.validate_get_waf_protection_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_waf_protection(
        self, params: models.UpdateWAFProtectionRequest
    ) -> dict:
        """Update WAF protection settings for a policy.

        Mirrors Go ``appsec.UpdateWAFProtection``.
        """
        logger.debug("UpdateWAFProtection")

        err = validation.validate_update_waf_protection_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    def get_waf_protections(
        self, params: models.GetWAFProtectionsRequest
    ) -> dict:
        """Get WAF protections status for a policy (plural variant).

        Mirrors Go ``appsec.GetWAFProtections``.
        """
        logger.debug("GetWAFProtections")

        err = validation.validate_get_waf_protections_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("GET", uri)
        return result

    # ==================================================================
    # IPGeo  (ip_geo.go)
    # ==================================================================

    def get_ip_geo(
        self, params: models.GetIPGeoRequest
    ) -> dict | models.GetIPGeoResponse:
        """Get IP/Geo firewall settings for a policy.

        Mirrors Go ``appsec.GetIPGeo``.
        """
        logger.debug("GetIPGeo")

        err = validation.validate_get_ip_geo_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/ip-geo-firewall"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_ip_geo(
        self, params: models.UpdateIPGeoRequest
    ) -> dict:
        """Update IP/Geo firewall settings for a policy.

        Mirrors Go ``appsec.UpdateIPGeo``.
        """
        logger.debug("UpdateIPGeo")

        err = validation.validate_update_ip_geo_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/ip-geo-firewall"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # IPGeoProtection  (ip_geo_protection.go)
    # ==================================================================

    def get_ip_geo_protection(
        self, params: models.GetIPGeoProtectionRequest
    ) -> dict:
        """Get IP/Geo protection status for a policy.

        Mirrors Go ``appsec.GetIPGeoProtection``.
        """
        logger.debug("GetIPGeoProtection")

        err = validation.validate_get_ip_geo_protection_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_ip_geo_protection(
        self, params: models.UpdateIPGeoProtectionRequest
    ) -> dict:
        """Update IP/Geo protection status for a policy.

        Mirrors Go ``appsec.UpdateIPGeoProtection``.
        """
        logger.debug("UpdateIPGeoProtection")

        err = validation.validate_update_ip_geo_protection_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    def get_ip_geo_protections(
        self, params: models.GetIPGeoProtectionsRequest
    ) -> dict:
        """Get IP/Geo protections status for a policy (plural variant).

        Mirrors Go ``appsec.GetIPGeoProtections``.
        """
        logger.debug("GetIPGeoProtections")

        err = validation.validate_get_ip_geo_protections_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("GET", uri)
        return result

    # ==================================================================
    # RateProtection  (rate_protection.go)
    # ==================================================================

    def get_rate_protection(
        self, params: models.GetRateProtectionRequest
    ) -> dict:
        """Get rate control protection status for a policy.

        Mirrors Go ``appsec.GetRateProtection``.
        """
        logger.debug("GetRateProtection")

        err = validation.validate_get_rate_protection_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_rate_protection(
        self, params: models.UpdateRateProtectionRequest
    ) -> dict:
        """Update rate control protection status for a policy.

        Mirrors Go ``appsec.UpdateRateProtection``.
        """
        logger.debug("UpdateRateProtection")

        err = validation.validate_update_rate_protection_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    def get_rate_protections(
        self, params: models.GetRateProtectionsRequest
    ) -> dict:
        """Get rate control protections status for a policy (plural variant).

        Mirrors Go ``appsec.GetRateProtections``.
        """
        logger.debug("GetRateProtections")

        err = validation.validate_get_rate_protections_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("GET", uri)
        return result

    # ==================================================================
    # ReputationProtection  (reputation_protection.go)
    # ==================================================================

    def get_reputation_protection(
        self, params: models.GetReputationProtectionRequest
    ) -> dict:
        """Get reputation protection status for a policy.

        Mirrors Go ``appsec.GetReputationProtection``.
        """
        logger.debug("GetReputationProtection")

        err = validation.validate_get_reputation_protection_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_reputation_protection(
        self, params: models.UpdateReputationProtectionRequest
    ) -> dict:
        """Update reputation protection status for a policy.

        Mirrors Go ``appsec.UpdateReputationProtection``.
        """
        logger.debug("UpdateReputationProtection")

        err = validation.validate_update_reputation_protection_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    def get_reputation_protections(
        self, params: models.GetReputationProtectionsRequest
    ) -> dict:
        """Get reputation protections status for a policy (plural variant).

        Mirrors Go ``appsec.GetReputationProtections``.
        """
        logger.debug("GetReputationProtections")

        err = validation.validate_get_reputation_protections_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("GET", uri)
        return result

    def remove_reputation_protection(
        self, params: models.RemoveReputationProtectionRequest
    ) -> dict:
        """Remove reputation protection for a policy.

        Mirrors Go ``appsec.RemoveReputationProtection``.
        """
        logger.debug("RemoveReputationProtection")

        err = validation.validate_remove_reputation_protection_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # SlowPostProtection  (slowpost_protection.go)
    # ==================================================================

    def get_slow_post_protection(
        self, params: models.GetSlowPostProtectionRequest
    ) -> dict:
        """Get slow POST protection status for a policy.

        Mirrors Go ``appsec.GetSlowPostProtection``.
        """
        logger.debug("GetSlowPostProtection")

        err = validation.validate_get_slow_post_protection_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_slow_post_protection(
        self, params: models.UpdateSlowPostProtectionRequest
    ) -> dict:
        """Update slow POST protection status for a policy.

        Mirrors Go ``appsec.UpdateSlowPostProtection``.
        """
        logger.debug("UpdateSlowPostProtection")

        err = validation.validate_update_slow_post_protection_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    def get_slow_post_protections(
        self, params: models.GetSlowPostProtectionsRequest
    ) -> dict:
        """Get slow POST protections status for a policy (plural variant).

        Mirrors Go ``appsec.GetSlowPostProtections``.
        """
        logger.debug("GetSlowPostProtections")

        err = validation.validate_get_slow_post_protections_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("GET", uri)
        return result

    # ==================================================================
    # SlowPostProtectionSetting  (slow_post_protection_setting.go)
    # ==================================================================

    def get_slow_post_protection_settings(
        self, params: models.GetSlowPostProtectionSettingsRequest
    ) -> dict:
        """List slow POST protection settings for a policy.

        Mirrors Go ``appsec.GetSlowPostProtectionSettings``.
        """
        logger.debug("GetSlowPostProtectionSettings")

        err = validation.validate_get_slow_post_protection_settings_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/slow-post"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_slow_post_protection_setting(
        self, params: models.UpdateSlowPostProtectionSettingRequest
    ) -> dict:
        """Update slow POST protection setting for a policy.

        Mirrors Go ``appsec.UpdateSlowPostProtectionSetting``.
        """
        logger.debug("UpdateSlowPostProtectionSetting")

        err = validation.validate_update_slow_post_protection_setting_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/slow-post"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # MalwarePolicy  (malware_policy.go)
    # ==================================================================

    def get_malware_policies(
        self, params: models.GetMalwarePoliciesRequest
    ) -> dict:
        """List malware policies for a config version.

        Mirrors Go ``appsec.GetMalwarePolicies``.
        """
        logger.debug("GetMalwarePolicies")

        err = validation.validate_get_malware_policies_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/malware-policies"
        )

        _, result = self._exec("GET", uri)
        return result

    def get_malware_policy(
        self, params: models.GetMalwarePolicyRequest
    ) -> dict:
        """Get a specific malware policy.

        Mirrors Go ``appsec.GetMalwarePolicy``.
        """
        logger.debug("GetMalwarePolicy")

        err = validation.validate_get_malware_policy_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/malware-policies/{params.malware_policy_id}"
        )

        _, result = self._exec("GET", uri)
        return result

    def create_malware_policy(
        self, params: models.CreateMalwarePolicyRequest
    ) -> dict:
        """Create a malware policy.

        Mirrors Go ``appsec.CreateMalwarePolicy``.
        """
        logger.debug("CreateMalwarePolicy")

        err = validation.validate_create_malware_policy_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/malware-policies"
        )

        _, result = self._exec("POST", uri, body=params.policy)
        return result

    def update_malware_policy(
        self, params: models.UpdateMalwarePolicyRequest
    ) -> dict:
        """Update a malware policy.

        Mirrors Go ``appsec.UpdateMalwarePolicy``.
        """
        logger.debug("UpdateMalwarePolicy")

        err = validation.validate_update_malware_policy_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/malware-policies/{params.malware_policy_id}"
        )

        _, result = self._exec("PUT", uri, body=params.policy)
        return result

    def remove_malware_policy(
        self, params: models.RemoveMalwarePolicyRequest
    ) -> dict:
        """Remove a malware policy.

        Mirrors Go ``appsec.RemoveMalwarePolicy``.
        """
        logger.debug("RemoveMalwarePolicy")

        err = validation.validate_remove_malware_policy_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/malware-policies/{params.malware_policy_id}"
        )

        _, result = self._exec("DELETE", uri)
        return result

    # ==================================================================
    # MalwarePolicyAction  (malware_policy_action.go)
    # ==================================================================

    def get_malware_policy_actions(
        self, params: models.GetMalwarePolicyActionsRequest
    ) -> dict:
        """List malware policy actions for a policy.

        Mirrors Go ``appsec.GetMalwarePolicyActions``.
        """
        logger.debug("GetMalwarePolicyActions")

        err = validation.validate_get_malware_policy_actions_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/malware-policies"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_malware_policy_action(
        self, params: models.UpdateMalwarePolicyActionRequest
    ) -> dict:
        """Update a malware policy action.

        Mirrors Go ``appsec.UpdateMalwarePolicyAction``.
        """
        logger.debug("UpdateMalwarePolicyAction")

        err = validation.validate_update_malware_policy_action_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/malware-policies/{params.malware_policy_id}"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    def update_malware_policy_actions(
        self, params: models.UpdateMalwarePolicyActionsRequest
    ) -> dict:
        """Update all malware policy actions for a policy.

        Mirrors Go ``appsec.UpdateMalwarePolicyActions``.
        """
        logger.debug("UpdateMalwarePolicyActions")

        err = validation.validate_update_malware_policy_actions_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/malware-policies"
        )

        _, result = self._exec(
            "PUT", uri, body=params.malware_policy_actions,
        )
        return result

    # ==================================================================
    # MalwareContentTypes  (malware_content_types.go)
    # ==================================================================

    def get_malware_content_types(
        self, params: models.GetMalwareContentTypesRequest
    ) -> dict:
        """Get malware content types for a config version.

        Mirrors Go ``appsec.GetMalwareContentTypes``.
        """
        logger.debug("GetMalwareContentTypes")

        err = validation.validate_get_malware_content_types_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/malware-policies/content-types"
        )

        _, result = self._exec("GET", uri)
        return result

    # ==================================================================
    # MalwareProtection  (malware_protection.go)
    # ==================================================================

    def get_malware_protection(
        self, params: models.GetMalwareProtectionRequest
    ) -> dict:
        """Get malware protection status for a policy.

        Mirrors Go ``appsec.GetMalwareProtection``.
        """
        logger.debug("GetMalwareProtection")

        err = validation.validate_get_malware_protection_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_malware_protection(
        self, params: models.UpdateMalwareProtectionRequest
    ) -> dict:
        """Update malware protection status for a policy.

        Mirrors Go ``appsec.UpdateMalwareProtection``.
        """
        logger.debug("UpdateMalwareProtection")

        err = validation.validate_update_malware_protection_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    def get_malware_protections(
        self, params: models.GetMalwareProtectionsRequest
    ) -> dict:
        """Get malware protections status for a policy (plural variant).

        Mirrors Go ``appsec.GetMalwareProtections`` (deprecated).
        """
        logger.debug("GetMalwareProtections")

        err = validation.validate_get_malware_protections_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("GET", uri)
        return result

    # ==================================================================
    # ApiEndpoints  (api_endpoints.go)
    # ==================================================================

    def get_api_endpoints(
        self, params: models.GetApiEndpointsRequest
    ) -> dict:
        """List API endpoints for a config version, optionally per policy.

        Mirrors Go ``appsec.GetApiEndpoints``.
        """
        logger.debug("GetApiEndpoints")

        err = validation.validate_get_api_endpoints_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        if params.policy_id:
            uri = (
                f"/appsec/v1/configs/{params.config_id}"
                f"/versions/{params.version}"
                f"/security-policies/{params.policy_id}"
                f"/api-endpoints"
            )
        else:
            uri = (
                f"/appsec/v1/configs/{params.config_id}"
                f"/versions/{params.version}"
                f"/api-endpoints"
            )

        _, result = self._exec("GET", uri)

        if params.name and result:
            eps = result.get("apiEndpoints", [])
            filtered = [e for e in eps if e.get("name") == params.name]
            return {"apiEndpoints": filtered}

        return result

    # ==================================================================
    # ApiHostnameCoverage  (api_hostname_coverage.go)
    # ==================================================================

    def get_api_hostname_coverage(  # pylint: disable=unused-argument
        self, params: models.GetApiHostnameCoverageRequest
    ) -> dict:
        """Get API hostname coverage.

        Mirrors Go ``appsec.GetApiHostnameCoverage``.
        """
        logger.debug("GetApiHostnameCoverage")

        uri = "/appsec/v1/hostname-coverage"

        _, result = self._exec("GET", uri)
        return result

    # ==================================================================
    # ApiHostnameCoverageMatchTargets
    #   (api_hostname_coverage_match_targets.go)
    # ==================================================================

    def get_api_hostname_coverage_match_targets(
        self,
        params: models.GetApiHostnameCoverageMatchTargetsRequest,
    ) -> dict:
        """Get hostname coverage match targets.

        Mirrors Go ``appsec.GetApiHostnameCoverageMatchTargets``.
        """
        logger.debug("GetApiHostnameCoverageMatchTargets")

        err = validation.validate_get_api_hostname_coverage_match_targets_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/hostname-coverage/match-targets"
        )

        _, result = self._exec(
            "GET", uri,
            params={"hostname": params.hostname},
        )
        return result

    # ==================================================================
    # ApiHostnameCoverageOverlapping
    #   (api_hostname_coverage_overlapping.go)
    # ==================================================================

    def get_api_hostname_coverage_overlapping(
        self,
        params: models.GetApiHostnameCoverageOverlappingRequest,
    ) -> dict:
        """Get overlapping hostname coverage.

        Mirrors Go ``appsec.GetApiHostnameCoverageOverlapping``.
        """
        logger.debug("GetApiHostnameCoverageOverlapping")

        err = validation.validate_get_api_hostname_coverage_overlapping_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/hostname-coverage/overlapping"
        )

        _, result = self._exec(
            "GET", uri,
            params={"hostname": params.hostname},
        )
        return result

    # ==================================================================
    # ApiRequestConstraints  (api_request_constraints.go)
    # ==================================================================

    def get_api_request_constraints(
        self, params: models.GetApiRequestConstraintsRequest
    ) -> dict:
        """Get API request constraints for a policy.

        Mirrors Go ``appsec.GetApiRequestConstraints``.
        """
        logger.debug("GetApiRequestConstraints")

        err = validation.validate_get_api_request_constraints_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/api-request-constraints"
        )

        _, result = self._exec("GET", uri)

        if params.api_id and result:
            eps = result.get("apiEndpoints", [])
            filtered = [e for e in eps if e.get("id") == params.api_id]
            return {"apiEndpoints": filtered}

        return result

    def update_api_request_constraints(
        self, params: models.UpdateApiRequestConstraintsRequest
    ) -> dict:
        """Update API request constraints.

        Mirrors Go ``appsec.UpdateApiRequestConstraints``.
        """
        logger.debug("UpdateApiRequestConstraints")

        err = validation.validate_update_api_request_constraints_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        if params.api_id:
            uri = (
                f"/appsec/v1/configs/{params.config_id}"
                f"/versions/{params.version}"
                f"/security-policies/{params.policy_id}"
                f"/api-request-constraints/{params.api_id}"
            )
        else:
            uri = (
                f"/appsec/v1/configs/{params.config_id}"
                f"/versions/{params.version}"
                f"/security-policies/{params.policy_id}"
                f"/api-request-constraints"
            )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    def remove_api_request_constraints(
        self, params: models.RemoveApiRequestConstraintsRequest
    ) -> dict:
        """Remove API request constraints.

        Mirrors Go ``appsec.RemoveApiRequestConstraints``.
        """
        logger.debug("RemoveApiRequestConstraints")

        err = validation.validate_remove_api_request_constraints_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        if params.api_id:
            uri = (
                f"/appsec/v1/configs/{params.config_id}"
                f"/versions/{params.version}"
                f"/security-policies/{params.policy_id}"
                f"/api-request-constraints/{params.api_id}"
            )
        else:
            uri = (
                f"/appsec/v1/configs/{params.config_id}"
                f"/versions/{params.version}"
                f"/security-policies/{params.policy_id}"
                f"/api-request-constraints"
            )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # ApiConstraintsProtection  (api_constraints_protection.go)
    # ==================================================================

    def get_api_constraints_protection(
        self, params: models.GetAPIConstraintsProtectionRequest
    ) -> dict:
        """Get API constraints protection status for a policy.

        Mirrors Go ``appsec.GetApiConstraintsProtection``.
        """
        logger.debug("GetApiConstraintsProtection")

        err = validation.validate_get_api_constraints_protection_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_api_constraints_protection(
        self, params: models.UpdateAPIConstraintsProtectionRequest
    ) -> dict:
        """Update API constraints protection status for a policy.

        Mirrors Go ``appsec.UpdateApiConstraintsProtection``.
        """
        logger.debug("UpdateApiConstraintsProtection")

        err = validation.validate_update_api_constraints_protection_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/protections"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # SiemDefinitions  (siem_definitions.go)
    # ==================================================================

    def get_siem_definitions(  # pylint: disable=unused-argument
        self, params: models.GetSiemDefinitionsRequest
    ) -> dict:
        """Get SIEM version definitions.

        Mirrors Go ``appsec.GetSiemDefinitions``.
        """
        logger.debug("GetSiemDefinitions")

        uri = "/appsec/v1/siem-definitions"

        _, result = self._exec("GET", uri)
        return result

    # ==================================================================
    # SiemSettings  (siem_settings.go)
    # ==================================================================

    def get_siem_settings(
        self, params: models.GetSiemSettingsRequest
    ) -> dict:
        """Get SIEM settings for a config version.

        Mirrors Go ``appsec.GetSiemSettings``.
        """
        logger.debug("GetSiemSettings")

        err = validation.validate_get_siem_settings_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/siem"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_siem_settings(
        self, params: models.UpdateSiemSettingsRequest
    ) -> dict:
        """Update SIEM settings for a config version.

        Mirrors Go ``appsec.UpdateSiemSettings``.
        """
        logger.debug("UpdateSiemSettings")

        err = validation.validate_update_siem_settings_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/siem"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    def remove_siem_settings(
        self, params: models.RemoveSiemSettingsRequest
    ) -> dict:
        """Remove (reset) SIEM settings for a config version.

        Mirrors Go ``appsec.RemoveSiemSettings``.  Uses PUT, not DELETE.
        """
        logger.debug("RemoveSiemSettings")

        err = validation.validate_remove_siem_settings_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/siem"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # ContractsGroups  (contracts_groups.go)
    # ==================================================================

    def get_contracts_groups(  # pylint: disable=unused-argument
        self, params: models.GetContractsGroupsRequest
    ) -> dict:
        """List contracts and groups.

        Mirrors Go ``appsec.GetContractsGroups``.
        """
        logger.debug("GetContractsGroups")

        uri = "/appsec/v1/contracts-groups"

        _, result = self._exec("GET", uri)
        return result

    # ==================================================================
    # SelectableHostnames  (selectable_hostnames.go)
    # ==================================================================

    def get_selectable_hostnames(
        self, params: models.GetSelectableHostnamesRequest
    ) -> dict:
        """Get selectable hostnames.

        Uses config/version path if ``config_id`` is set; otherwise uses
        contract/group path.

        Mirrors Go ``appsec.GetSelectableHostnames``.
        """
        logger.debug("GetSelectableHostnames")

        if params.config_id:
            uri = (
                f"/appsec/v1/configs/{params.config_id}"
                f"/versions/{params.version}"
                f"/selectable-hostnames"
            )
        else:
            uri = (
                f"/appsec/v1/contracts/{params.contract_id}"
                f"/groups/{params.group_id}"
                f"/selectable-hostnames"
            )

        _, result = self._exec("GET", uri)
        return result

    # ==================================================================
    # SelectedHostname  (selected_hostname.go)
    # ==================================================================

    def get_selected_hostname(
        self, params: models.GetSelectedHostnameRequest
    ) -> dict:
        """Get selected hostname for a config version (singular).

        Mirrors Go ``appsec.GetSelectedHostname``.
        """
        logger.debug("GetSelectedHostname")

        err = validation.validate_get_selected_hostname_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/selected-hostnames"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_selected_hostnames(
        self, params: models.UpdateSelectedHostnamesRequest
    ) -> dict:
        """Update selected hostnames for a config version (plural).

        Mirrors Go ``appsec.UpdateSelectedHostnames``.
        """
        logger.debug("UpdateSelectedHostnames")

        err = validation.validate_update_selected_hostnames_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/selected-hostnames"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    def get_selected_hostnames(
        self, params: models.GetSelectedHostnamesRequest
    ) -> dict:
        """Get selected hostnames for a config version.

        Mirrors Go ``appsec.GetSelectedHostnames``.
        """
        logger.debug("GetSelectedHostnames")

        err = validation.validate_get_selected_hostnames_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/selected-hostnames"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_selected_hostname(
        self, params: models.UpdateSelectedHostnameRequest
    ) -> dict:
        """Update selected hostnames for a config version.

        Mirrors Go ``appsec.UpdateSelectedHostname``.
        """
        logger.debug("UpdateSelectedHostname")

        err = validation.validate_update_selected_hostname_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/selected-hostnames"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # WAPSelectedHostnames  (wap_selected_hostnames.go)
    # ==================================================================

    def get_wap_selected_hostnames(
        self, params: models.GetWAPSelectedHostnamesRequest
    ) -> dict:
        """Get WAP selected hostnames for a policy.

        Mirrors Go ``appsec.GetWAPSelectedHostnames``.
        """
        logger.debug("GetWAPSelectedHostnames")

        err = validation.validate_get_wap_selected_hostnames_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/wap-selected-hostnames"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_wap_selected_hostnames(
        self, params: models.UpdateWAPSelectedHostnamesRequest
    ) -> dict:
        """Update WAP selected hostnames for a policy.

        Mirrors Go ``appsec.UpdateWAPSelectedHostnames``.
        """
        logger.debug("UpdateWAPSelectedHostnames")

        err = validation.validate_update_wap_selected_hostnames_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.security_policy_id}"
            f"/wap-selected-hostnames"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # WAPBypassNetworkLists  (wap_bypass_network_lists.go)
    # ==================================================================

    def get_wap_bypass_network_lists(
        self, params: models.GetWAPBypassNetworkListsRequest
    ) -> dict:
        """Get WAP bypass network lists for a policy.

        Mirrors Go ``appsec.GetWAPBypassNetworkLists``.
        """
        logger.debug("GetWAPBypassNetworkLists")

        err = validation.validate_get_wap_bypass_network_lists_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/bypass-network-lists"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_wap_bypass_network_lists(
        self, params: models.UpdateWAPBypassNetworkListsRequest
    ) -> dict:
        """Update WAP bypass network lists for a policy.

        Mirrors Go ``appsec.UpdateWAPBypassNetworkLists``.
        """
        logger.debug("UpdateWAPBypassNetworkLists")

        err = validation.validate_update_wap_bypass_network_lists_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/bypass-network-lists"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    def remove_wap_bypass_network_lists(
        self, params: models.RemoveWAPBypassNetworkListsRequest
    ) -> dict:
        """Remove WAP bypass network lists for a policy.

        Mirrors Go ``appsec.RemoveWAPBypassNetworkLists``.
        """
        logger.debug("RemoveWAPBypassNetworkLists")

        err = validation.validate_remove_wap_bypass_network_lists_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/bypass-network-lists"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # FailoverHostnames  (failover_hostnames.go)
    # ==================================================================

    def get_failover_hostnames(
        self, params: models.GetFailoverHostnamesRequest
    ) -> dict:
        """Get failover hostnames for a config.

        Mirrors Go ``appsec.GetFailoverHostnames``.
        """
        logger.debug("GetFailoverHostnames")

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/failover-hostnames"
        )

        _, result = self._exec("GET", uri)
        return result

    # ==================================================================
    # HostMoveActivations  (host_move_activations.go)
    # ==================================================================

    def get_host_move_validation(
        self, params: models.GetHostMoveValidationRequest
    ) -> dict:
        """Get host move validation for a config version and network.

        Mirrors Go ``appsec.GetHostMoveValidation``.
        """
        logger.debug("GetHostMoveValidation")

        err = validation.validate_get_host_move_validation_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/network/{params.network}"
            f"/host-move-validation"
        )

        _, result = self._exec("GET", uri)
        return result

    def create_activations_with_host_move(
        self,
        params: models.CreateActivationsWithHostMoveRequest,
    ) -> dict:
        """Create an activation with host move.

        Mirrors Go ``appsec.CreateActivationsWithHostMove``.
        """
        logger.debug("CreateActivationsWithHostMove")

        err = validation.validate_create_activations_with_host_move_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.config_version}"
            f"/activations-with-host-move"
        )

        _, result = self._exec("POST", uri, body=_body(params))
        return result

    # ==================================================================
    # ExportConfiguration  (export_configuration.go)
    # ==================================================================

    def get_export_configuration(
        self, params: models.GetExportConfigurationRequest
    ) -> dict | models.GetExportConfigurationResponse:
        """Export a security configuration version.

        Mirrors Go ``appsec.GetExportConfiguration``.
        """
        logger.debug("GetExportConfiguration")

        err = validation.validate_get_export_configuration_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/export/configs/{params.config_id}"
            f"/versions/{params.version}"
        )

        qp: dict[str, str] = {}
        if params.source:
            qp["source"] = params.source

        _, result = self._exec("GET", uri, params=qp if qp else None)
        return result

    # ==================================================================
    # VersionNotes  (version_notes.go)
    # ==================================================================

    def get_version_notes(
        self, params: models.GetVersionNotesRequest
    ) -> dict:
        """Get version notes for a config version.

        Mirrors Go ``appsec.GetVersionNotes``.
        """
        logger.debug("GetVersionNotes")

        err = validation.validate_get_version_notes_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/version-notes"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_version_notes(
        self, params: models.UpdateVersionNotesRequest
    ) -> dict:
        """Update version notes for a config version.

        Mirrors Go ``appsec.UpdateVersionNotes``.
        """
        logger.debug("UpdateVersionNotes")

        err = validation.validate_update_version_notes_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/version-notes"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # ThreatIntel  (threat_intel.go)
    # ==================================================================

    def get_threat_intel(
        self, params: models.GetThreatIntelRequest
    ) -> dict:
        """Get threat intelligence settings for a policy.

        Mirrors Go ``appsec.GetThreatIntel``.
        """
        logger.debug("GetThreatIntel")

        err = validation.validate_get_threat_intel_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/threat-intel"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_threat_intel(
        self, params: models.UpdateThreatIntelRequest
    ) -> dict:
        """Update threat intelligence settings for a policy.

        Mirrors Go ``appsec.UpdateThreatIntel``.
        """
        logger.debug("UpdateThreatIntel")

        err = validation.validate_update_threat_intel_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/threat-intel"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # TuningRecommendations  (tuning_recommendations.go)
    # ==================================================================

    def get_tuning_recommendations(
        self, params: models.GetTuningRecommendationsRequest
    ) -> dict:
        """Get tuning recommendations for a policy.

        Mirrors Go ``appsec.GetTuningRecommendations``.
        """
        logger.debug("GetTuningRecommendations")

        err = validation.validate_get_tuning_recommendations_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/recommendations"
        )

        _, result = self._exec(
            "GET", uri,
            params={
                "standardException": "true",
                "type": params.ruleset_type,
            },
        )
        return result

    def get_attack_group_recommendations(
        self,
        params: models.GetAttackGroupRecommendationsRequest,
    ) -> dict:
        """Get recommendations for a specific attack group.

        Mirrors Go ``appsec.GetAttackGroupRecommendations``.
        """
        logger.debug("GetAttackGroupRecommendations")

        err = validation.validate_get_attack_group_recommendations_request(
            params,
        )
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/recommendations/attack-groups/{params.group}"
        )

        _, result = self._exec(
            "GET", uri,
            params={
                "standardException": "true",
                "type": params.ruleset_type,
            },
        )
        return result

    def get_rule_recommendations(
        self, params: models.GetRuleRecommendationsRequest
    ) -> dict:
        """Get recommendations for a specific rule.

        Mirrors Go ``appsec.GetRuleRecommendations``.
        """
        logger.debug("GetRuleRecommendations")

        err = validation.validate_get_rule_recommendations_request(params)
        if err is not None:
            raise errors.Error(
                title=f"{errors.ErrStructValidation}: {err}",
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/security-policies/{params.policy_id}"
            f"/recommendations/rules/{params.rule_id}"
        )

        _, result = self._exec(
            "GET", uri,
            params={
                "standardException": "true",
                "type": params.ruleset_type,
            },
        )
        return result

    # ==================================================================
    # Advanced Settings — ASE Penalty Box  (advanced_settings_ase_penalty_box.go)
    # ==================================================================

    def get_advanced_settings_ase_penalty_box(
        self,
        params: models.GetAdvancedSettingsAsePenaltyBoxRequest,
    ) -> dict:
        """Return ASE penalty box advanced settings for a configuration.

        See:
        https://techdocs.akamai.com/application-security/reference/get-advanced-settings-ase-penalty-box

        Mirrors Go ``appsec.GetAdvancedSettingsAsePenaltyBox``.
        """
        logger.debug("GetAdvancedSettingsAsePenaltyBox")

        err = validation.validate_get_advanced_settings_ase_penalty_box_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/advanced-settings/ase-penalty-box"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_advanced_settings_ase_penalty_box(
        self,
        params: models.UpdateAdvancedSettingsAsePenaltyBoxRequest,
    ) -> dict:
        """Update ASE penalty box advanced settings for a configuration.

        See:
        https://techdocs.akamai.com/application-security/reference/put-advanced-settings-ase-penalty-box

        Mirrors Go ``appsec.UpdateAdvancedSettingsAsePenaltyBox``.
        """
        logger.debug("UpdateAdvancedSettingsAsePenaltyBox")

        err = validation.validate_update_advanced_settings_ase_penalty_box_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/advanced-settings/ase-penalty-box"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    def remove_advanced_settings_ase_penalty_box(
        self,
        params: models.RemoveAdvancedSettingsAsePenaltyBoxRequest,
    ) -> dict:
        """Reset ASE penalty box advanced settings to defaults.

        Mirrors Go ``appsec.RemoveAdvancedSettingsAsePenaltyBox``, which
        calls ``UpdateAdvancedSettingsAsePenaltyBox`` with
        ``blockDuration=10`` and clears all other fields.
        """
        logger.debug("RemoveAdvancedSettingsAsePenaltyBox")

        err = validation.validate_remove_advanced_settings_ase_penalty_box_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        update_req = models.UpdateAdvancedSettingsAsePenaltyBoxRequest(
            config_id=params.config_id,
            version=params.version,
            block_duration=10,
        )
        resp = self.update_advanced_settings_ase_penalty_box(update_req)
        return resp

    # ==================================================================
    # Advanced Settings — Attack Payload Logging
    #   (advanced_settings_attack_payload_logging.go)
    # ==================================================================

    def _attack_payload_logging_uri(
        self, config_id: int, version: int, policy_id: str
    ) -> str:
        """Build URI for attack payload logging, policy-level or config-level."""
        if policy_id:
            return (
                f"/appsec/v1/configs/{config_id}"
                f"/versions/{version}"
                f"/security-policies/{policy_id}"
                f"/advanced-settings/logging/attack-payload"
            )
        return (
            f"/appsec/v1/configs/{config_id}"
            f"/versions/{version}"
            f"/advanced-settings/logging/attack-payload"
        )

    def get_advanced_settings_attack_payload_logging(
        self,
        params: models.GetAdvancedSettingsAttackPayloadLoggingRequest,
    ) -> dict:
        """Return attack payload logging settings for a config or policy.

        See:
        https://techdocs.akamai.com/application-security/reference/get-advanced-settings-attack-payload-logging

        Mirrors Go ``appsec.GetAdvancedSettingsAttackPayloadLogging``.
        """
        logger.debug("GetAdvancedSettingsAttackPayloadLogging")

        err = validation.validate_get_advanced_settings_attack_payload_logging_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        uri = self._attack_payload_logging_uri(
            params.config_id, params.version, params.policy_id,
        )

        _, result = self._exec("GET", uri)
        return result

    def update_advanced_settings_attack_payload_logging(
        self,
        params: models.UpdateAdvancedSettingsAttackPayloadLoggingRequest,
    ) -> dict:
        """Update attack payload logging settings for a config or policy.

        See:
        https://techdocs.akamai.com/application-security/reference/put-advanced-settings-attack-payload-logging

        Mirrors Go ``appsec.UpdateAdvancedSettingsAttackPayloadLogging``.
        """
        logger.debug("UpdateAdvancedSettingsAttackPayloadLogging")

        err = validation.validate_update_advanced_settings_attack_payload_logging_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        uri = self._attack_payload_logging_uri(
            params.config_id, params.version, params.policy_id,
        )

        _, result = self._exec(
            "PUT", uri, body=params.json_payload_raw,
        )
        return result

    def remove_advanced_settings_attack_payload_logging(
        self,
        params: models.RemoveAdvancedSettingsAttackPayloadLoggingRequest,
    ) -> dict:
        """Remove (reset) attack payload logging settings.

        Uses PUT (not DELETE) to reset the settings.

        See:
        https://techdocs.akamai.com/application-security/reference/put-advanced-settings-attack-payload-logging

        Mirrors Go ``appsec.RemoveAdvancedSettingsAttackPayloadLogging``.
        """
        logger.debug("RemoveAdvancedSettingsAttackPayloadLogging")

        err = validation.validate_remove_advanced_settings_attack_payload_logging_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        uri = self._attack_payload_logging_uri(
            params.config_id, params.version, params.policy_id,
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # Advanced Settings — Evasive Path Match
    #   (advanced_settings_evasive_path_match.go)
    # ==================================================================

    def _evasive_path_match_uri(
        self, config_id: int, version: int, policy_id: str
    ) -> str:
        """Build URI for evasive path match, policy-level or config-level."""
        if policy_id:
            return (
                f"/appsec/v1/configs/{config_id}"
                f"/versions/{version}"
                f"/security-policies/{policy_id}"
                f"/advanced-settings/evasive-path-match"
            )
        return (
            f"/appsec/v1/configs/{config_id}"
            f"/versions/{version}"
            f"/advanced-settings/evasive-path-match"
        )

    def get_advanced_settings_evasive_path_match(
        self,
        params: models.GetAdvancedSettingsEvasivePathMatchRequest,
    ) -> dict:
        """Return evasive path match settings for a configuration or policy.

        See:
        https://techdocs.akamai.com/application-security/reference/get-advanced-settings-evasive-path-match

        Mirrors Go ``appsec.GetAdvancedSettingsEvasivePathMatch``.
        """
        logger.debug("GetAdvancedSettingsEvasivePathMatch")

        err = validation.validate_get_advanced_settings_evasive_path_match_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        uri = self._evasive_path_match_uri(
            params.config_id, params.version, params.policy_id,
        )

        _, result = self._exec("GET", uri)
        return result

    def update_advanced_settings_evasive_path_match(
        self,
        params: models.UpdateAdvancedSettingsEvasivePathMatchRequest,
    ) -> dict:
        """Update evasive path match settings for a configuration or policy.

        See:
        https://techdocs.akamai.com/application-security/reference/put-advanced-settings-evasive-path-match

        Mirrors Go ``appsec.UpdateAdvancedSettingsEvasivePathMatch``.
        """
        logger.debug("UpdateAdvancedSettingsEvasivePathMatch")

        err = validation.validate_update_advanced_settings_evasive_path_match_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        uri = self._evasive_path_match_uri(
            params.config_id, params.version, params.policy_id,
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    def remove_advanced_settings_evasive_path_match(
        self,
        params: models.RemoveAdvancedSettingsEvasivePathMatchRequest,
    ) -> dict:
        """Remove evasive path match settings for a config or policy.

        Mirrors Go ``appsec.RemoveAdvancedSettingsEvasivePathMatch`` — calls
        ``update_advanced_settings_evasive_path_match`` with
        ``enable_path_match`` set to ``False``.
        """
        logger.debug("RemoveAdvancedSettingsEvasivePathMatch")

        err = validation.validate_remove_advanced_settings_evasive_path_match_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        request = models.UpdateAdvancedSettingsEvasivePathMatchRequest(
            config_id=params.config_id,
            version=params.version,
            policy_id=params.policy_id,
            enable_path_match=False,
        )
        self.update_advanced_settings_evasive_path_match(request)

        return {
            "configId": params.config_id,
            "version": params.version,
            "policyId": params.policy_id,
            "enablePathMatch": False,
        }

    # ==================================================================
    # Advanced Settings — JA4 Fingerprint
    #   (advanced_settings_ja4_fingerprints.go)
    # ==================================================================

    def get_advanced_settings_ja4_fingerprint(
        self,
        params: models.GetAdvancedSettingsJA4FingerprintRequest,
    ) -> dict:
        """Return JA4 fingerprint advanced settings for a configuration.

        See:
        https://techdocs.akamai.com/application-security/reference/get-advanced-settings-ja4-fingerprint

        Mirrors Go ``appsec.GetAdvancedSettingsJA4Fingerprint``.
        """
        logger.debug("GetAdvancedSettingsJA4Fingerprint")

        err = validation.validate_get_advanced_settings_ja4_fingerprint_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/advanced-settings/ja4-fingerprint"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_advanced_settings_ja4_fingerprint(
        self,
        params: models.UpdateAdvancedSettingsJA4FingerprintRequest,
    ) -> dict:
        """Update JA4 fingerprint advanced settings for a configuration.

        See:
        https://techdocs.akamai.com/application-security/reference/put-advanced-settings-ja4-fingerprint

        Mirrors Go ``appsec.UpdateAdvancedSettingsJA4Fingerprint``.
        """
        logger.debug("UpdateAdvancedSettingsJA4Fingerprint")

        err = validation.validate_update_advanced_settings_ja4_fingerprint_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/advanced-settings/ja4-fingerprint"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    def remove_advanced_settings_ja4_fingerprint(
        self,
        params: models.RemoveAdvancedSettingsJA4FingerprintRequest,
    ) -> dict:
        """Remove JA4 fingerprint settings for a configuration.

        Mirrors Go ``appsec.RemoveAdvancedSettingsJA4Fingerprint``.
        """
        logger.debug("RemoveAdvancedSettingsJA4Fingerprint")

        err = validation.validate_remove_advanced_settings_ja4_fingerprint_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/advanced-settings/ja4-fingerprint"
        )

        request = models.UpdateAdvancedSettingsJA4FingerprintRequest(
            config_id=params.config_id,
            version=params.version,
            header_names=None,
        )

        _, result = self._exec("PUT", uri, body=_body(request))
        return result

    # ==================================================================
    # Advanced Settings — Logging  (advanced_settings_logging.go)
    # ==================================================================

    def _logging_uri(
        self, config_id: int, version: int, policy_id: str
    ) -> str:
        """Build URI for logging settings, policy-level or config-level."""
        if policy_id:
            return (
                f"/appsec/v1/configs/{config_id}"
                f"/versions/{version}"
                f"/security-policies/{policy_id}"
                f"/advanced-settings/logging"
            )
        return (
            f"/appsec/v1/configs/{config_id}"
            f"/versions/{version}"
            f"/advanced-settings/logging"
        )

    def get_advanced_settings_logging(
        self,
        params: models.GetAdvancedSettingsLoggingRequest,
    ) -> dict:
        """Return logging settings for a configuration or policy.

        See:
        https://techdocs.akamai.com/application-security/reference/get-advanced-settings-logging

        Mirrors Go ``appsec.GetAdvancedSettingsLogging``.
        """
        logger.debug("GetAdvancedSettingsLogging")

        err = validation.validate_get_advanced_settings_logging_request(params)
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        uri = self._logging_uri(
            params.config_id, params.version, params.policy_id,
        )

        _, result = self._exec("GET", uri)
        return result

    def update_advanced_settings_logging(
        self,
        params: models.UpdateAdvancedSettingsLoggingRequest,
    ) -> dict:
        """Update logging settings for a configuration or policy.

        See:
        https://techdocs.akamai.com/application-security/reference/put-advanced-settings-logging

        Mirrors Go ``appsec.UpdateAdvancedSettingsLogging``.
        """
        logger.debug("UpdateAdvancedSettingsLogging")

        err = validation.validate_update_advanced_settings_logging_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        uri = self._logging_uri(
            params.config_id, params.version, params.policy_id,
        )

        _, result = self._exec(
            "PUT", uri, body=params.json_payload_raw,
        )
        return result

    def remove_advanced_settings_logging(
        self,
        params: models.RemoveAdvancedSettingsLoggingRequest,
    ) -> dict:
        """Remove (reset) logging settings for a configuration or policy.

        Uses PUT (not DELETE) to reset the settings.

        See:
        https://techdocs.akamai.com/application-security/reference/put-advanced-settings-logging

        Mirrors Go ``appsec.RemoveAdvancedSettingsLogging``.
        """
        logger.debug("RemoveAdvancedSettingsLogging")

        err = validation.validate_remove_advanced_settings_logging_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        uri = self._logging_uri(
            params.config_id, params.version, params.policy_id,
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # Advanced Settings — PII Learning  (advanced_settings_pii_learning.go)
    # ==================================================================

    def get_advanced_settings_pii_learning(
        self,
        params: models.GetAdvancedSettingsPIILearningRequest,
    ) -> dict:
        """Return PII learning settings for a configuration.

        See:
        https://techdocs.akamai.com/application-security/reference/get-advanced-settings-pii-learning

        Mirrors Go ``appsec.GetAdvancedSettingsPIILearning``.
        """
        logger.debug("GetAdvancedSettingsPIILearning")

        err = validation.validate_get_advanced_settings_pii_learning_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/advanced-settings/pii-learning"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_advanced_settings_pii_learning(
        self,
        params: models.UpdateAdvancedSettingsPIILearningRequest,
    ) -> dict:
        """Update PII learning settings for a configuration.

        Body is ``{"enablePiiLearning": <value>}`` matching Go's inline
        anonymous struct.

        See:
        https://techdocs.akamai.com/application-security/reference/put-advanced-settings-pii-learning

        Mirrors Go ``appsec.UpdateAdvancedSettingsPIILearning``.
        """
        logger.debug("UpdateAdvancedSettingsPIILearning")

        err = validation.validate_update_advanced_settings_pii_learning_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/advanced-settings/pii-learning"
        )

        _, result = self._exec(
            "PUT", uri,
            body={"enablePiiLearning": params.enable_pii_learning},
        )
        return result

    # ==================================================================
    # Advanced Settings — Pragma Header
    #   (advanced_settings_pragma_header.go)
    # ==================================================================

    def _pragma_uri(
        self, config_id: int, version: int, policy_id: str
    ) -> str:
        """Build URI for pragma header settings, policy-level or config-level."""
        if policy_id:
            return (
                f"/appsec/v1/configs/{config_id}"
                f"/versions/{version}"
                f"/security-policies/{policy_id}"
                f"/advanced-settings/pragma-header"
            )
        return (
            f"/appsec/v1/configs/{config_id}"
            f"/versions/{version}"
            f"/advanced-settings/pragma-header"
        )

    def get_advanced_settings_pragma(
        self,
        params: models.GetAdvancedSettingsPragmaRequest,
    ) -> dict:
        """Return pragma header settings for a configuration or policy.

        See:
        https://techdocs.akamai.com/application-security/reference/get-advanced-settings-pragma-header

        Mirrors Go ``appsec.GetAdvancedSettingsPragma``.
        """
        logger.debug("GetAdvancedSettingsPragma")

        err = validation.validate_get_advanced_settings_pragma_request(params)
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        uri = self._pragma_uri(
            params.config_id, params.version, params.policy_id,
        )

        _, result = self._exec("GET", uri)
        return result

    def update_advanced_settings_pragma(
        self,
        params: models.UpdateAdvancedSettingsPragmaRequest,
    ) -> dict:
        """Update pragma header settings for a configuration or policy.

        See:
        https://techdocs.akamai.com/application-security/reference/put-advanced-settings-pragma-header

        Mirrors Go ``appsec.UpdateAdvancedSettingsPragma``.
        """
        logger.debug("UpdateAdvancedSettingsPragma")

        err = validation.validate_update_advanced_settings_pragma_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        uri = self._pragma_uri(
            params.config_id, params.version, params.policy_id,
        )

        _, result = self._exec(
            "PUT", uri, body=params.json_payload_raw,
        )
        return result

    # ==================================================================
    # Advanced Settings — Prefetch  (advanced_settings_prefetch.go)
    # ==================================================================

    def get_advanced_settings_prefetch(
        self,
        params: models.GetAdvancedSettingsPrefetchRequest,
    ) -> dict:
        """Return prefetch settings for a configuration.

        See:
        https://techdocs.akamai.com/application-security/reference/get-advanced-settings-prefetch

        Mirrors Go ``appsec.GetAdvancedSettingsPrefetch``.
        """
        logger.debug("GetAdvancedSettingsPrefetch")

        err = validation.validate_get_advanced_settings_prefetch_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/advanced-settings/prefetch"
        )

        _, result = self._exec("GET", uri)
        return result

    def update_advanced_settings_prefetch(
        self,
        params: models.UpdateAdvancedSettingsPrefetchRequest,
    ) -> dict:
        """Update prefetch settings for a configuration.

        See:
        https://techdocs.akamai.com/application-security/reference/put-advanced-settings-prefetch

        Mirrors Go ``appsec.UpdateAdvancedSettingsPrefetch``.
        """
        logger.debug("UpdateAdvancedSettingsPrefetch")

        err = validation.validate_update_advanced_settings_prefetch_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        uri = (
            f"/appsec/v1/configs/{params.config_id}"
            f"/versions/{params.version}"
            f"/advanced-settings/prefetch"
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    # ==================================================================
    # Advanced Settings — Request Body
    #   (advanced_settings_request_body.go)
    # ==================================================================

    def _request_body_uri(
        self, config_id: int, version: int, policy_id: str
    ) -> str:
        """Build URI for request body settings, policy-level or config-level."""
        if policy_id:
            return (
                f"/appsec/v1/configs/{config_id}"
                f"/versions/{version}"
                f"/security-policies/{policy_id}"
                f"/advanced-settings/request-body"
            )
        return (
            f"/appsec/v1/configs/{config_id}"
            f"/versions/{version}"
            f"/advanced-settings/request-body"
        )

    def get_advanced_settings_request_body(
        self,
        params: models.GetAdvancedSettingsRequestBodyRequest,
    ) -> dict:
        """Return request body inspection settings for a config or policy.

        See:
        https://techdocs.akamai.com/application-security/reference/get-advanced-settings-request-body

        Mirrors Go ``appsec.GetAdvancedSettingsRequestBody``.
        """
        logger.debug("GetAdvancedSettingsRequestBody")

        err = validation.validate_get_advanced_settings_request_body_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        uri = self._request_body_uri(
            params.config_id, params.version, params.policy_id,
        )

        _, result = self._exec("GET", uri)
        return result

    def update_advanced_settings_request_body(
        self,
        params: models.UpdateAdvancedSettingsRequestBodyRequest,
    ) -> dict:
        """Update request body inspection settings for a config or policy.

        See:
        https://techdocs.akamai.com/application-security/reference/put-advanced-settings-request-body

        Mirrors Go ``appsec.UpdateAdvancedSettingsRequestBody``.
        """
        logger.debug("UpdateAdvancedSettingsRequestBody")

        err = validation.validate_update_advanced_settings_request_body_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        uri = self._request_body_uri(
            params.config_id, params.version, params.policy_id,
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result

    def remove_advanced_settings_request_body(
        self,
        params: models.RemoveAdvancedSettingsRequestBodyRequest,
    ) -> dict:
        """Remove request body inspection settings for a config or policy.

        Mirrors Go ``appsec.RemoveAdvancedSettingsRequestBody``.
        """
        logger.debug("RemoveAdvancedSettingsRequestBody")

        err = validation.validate_remove_advanced_settings_request_body_request(
            params
        )
        if err is not None:
            raise errors.Error(
                title=str(errors.ErrStructValidation), detail=err
            )

        uri = self._request_body_uri(
            params.config_id, params.version, params.policy_id,
        )

        _, result = self._exec("PUT", uri, body=_body(params))
        return result
