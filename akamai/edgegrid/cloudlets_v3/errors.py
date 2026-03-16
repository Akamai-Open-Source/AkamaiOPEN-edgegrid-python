"""Error types and sentinel errors for the Cloudlets V3 API."""
# pylint: disable=invalid-name

import json
from dataclasses import dataclass


@dataclass
class Error(Exception):  # pylint: disable=too-many-instance-attributes
    """Cloudlets V3 API error.

    Mirrors Go Error struct from pkg/cloudlets/v3/errors.go.
    Includes additional Cloudlets-specific fields: requestId, requestTime,
    clientIp, serverIp, method.
    """

    type: str = ""  # pylint: disable=redefined-builtin
    title: str = ""
    instance: str = ""
    status: int = 0
    errors: dict | list | str | None = None
    detail: str = ""
    request_id: str = ""
    request_time: str = ""
    client_ip: str = ""
    server_ip: str = ""
    method: str = ""

    def __str__(self) -> str:
        """Format error as indented JSON.

        Mirrors Go Error.Error() which uses json.MarshalIndent.
        Output format: 'API error: \\n{json}'

        Respects Go JSON omitempty tags:
        - type, title, instance, status, errors, requestId, requestTime,
          clientIp, serverIp, method: omitted when zero/empty/nil
        - detail: always included (no omitempty in Go struct tag)
        """
        error_dict: dict = {}
        if self.type:
            error_dict["type"] = self.type
        if self.title:
            error_dict["title"] = self.title
        if self.instance:
            error_dict["instance"] = self.instance
        if self.status:
            error_dict["status"] = self.status
        if self.errors is not None:
            error_dict["errors"] = self.errors
        error_dict["detail"] = self.detail
        if self.request_id:
            error_dict["requestId"] = self.request_id
        if self.request_time:
            error_dict["requestTime"] = self.request_time
        if self.client_ip:
            error_dict["clientIp"] = self.client_ip
        if self.server_ip:
            error_dict["serverIp"] = self.server_ip
        if self.method:
            error_dict["method"] = self.method

        try:
            msg = json.dumps(error_dict, indent="\t")
            return f"API error: \n{msg}"
        except (TypeError, ValueError) as err:
            return f"error marshaling API error: {err}"

    def is_equivalent(self, other: "Error") -> bool:
        """Check error equivalence.

        Mirrors Go Error.Is() from pkg/cloudlets/v3/errors.go.
        Two errors are equivalent when they have the same status code
        and produce the same string representation.
        """
        if not isinstance(other, Error):
            return False
        if self is other:
            return True
        if self.status != other.status:
            return False
        return str(self) == str(other)


# ---------------------------------------------------------------------------
# Sentinel error constants
# ---------------------------------------------------------------------------
# Each constant mirrors a Go errors.New("...") sentinel from the v3 package.
# The string values match Go sentinel messages character-for-character.
# ---------------------------------------------------------------------------

# From cloudlets.go — struct validation sentinel
ErrStructValidation = "struct validation"

# From errors.go — policy not found sentinel
ErrPolicyNotFound = "policy not found"

# From policy.go — policy operation sentinels
ErrListPolicies = "list shared policies"
ErrCreatePolicy = "create shared policy"
ErrDeletePolicy = "delete shared policy"
ErrGetPolicy = "get shared policy"
ErrUpdatePolicy = "update shared policy"
ErrClonePolicy = "clone policy"

# From list_cloudlets.go — list cloudlets sentinel
ErrListCloudlets = "list cloudlets"

# From policy_version.go — policy version operation sentinels
ErrListPolicyVersions = "list policy versions"
ErrGetPolicyVersion = "get policy versions"
ErrCreatePolicyVersion = "create policy versions"
ErrDeletePolicyVersion = "delete policy versions"
ErrUpdatePolicyVersion = "update policy versions"

# From policy_activation.go — policy activation operation sentinels
ErrListPolicyActivations = "list policy activations"
ErrActivatePolicy = "activate policy"
ErrDeactivatePolicy = "deactivate policy"
ErrGetPolicyActivation = "get policy activation"

# From policy_property.go — policy property operation sentinel
ErrListActivePolicyProperties = "list active policy properties"

# From match_rule.go — match rule unmarshalling error sentinels
ErrUnmarshallMatchCriteriaAP = "unmarshalling MatchCriteriaAP"
ErrUnmarshallMatchCriteriaAS = "unmarshalling MatchCriteriaAS"
ErrUnmarshallMatchCriteriaPR = "unmarshalling MatchCriteriaPR"
ErrUnmarshallMatchCriteriaER = "unmarshalling MatchCriteriaER"
ErrUnmarshallMatchCriteriaFR = "unmarshalling MatchCriteriaFR"
ErrUnmarshallMatchCriteriaRC = "unmarshalling MatchCriteriaRC"
ErrUnmarshallMatchCriteriaVP = "unmarshalling MatchCriteriaVP"
ErrUnmarshallMatchRules = "unmarshalling MatchRules"
