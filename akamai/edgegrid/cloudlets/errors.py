# pylint: disable=invalid-name,too-many-instance-attributes,too-many-arguments,too-many-positional-arguments
"""Cloudlets API error types and sentinel error constants.

Provides the :class:`Error` class for structured Cloudlets API error
handling and sentinel error constants for each API operation.

Mirrors Go ``pkg/cloudlets/errors.go`` and sentinel declarations from
``cloudlets.go``, ``policy.go``, ``policy_version.go``,
``policy_version_activation.go``, ``policy_version_rule.go``,
``policy_property.go``, ``loadbalancer.go``, ``loadbalancer_version.go``,
``loadbalancer_activation.go``, and ``match_rule.go``.
"""

import json

from akamai.edgegrid.utils import unescape_content


class Error(Exception):
    """Cloudlets API error response.

    Represents a structured error returned by the Akamai Cloudlets API.
    Fields mirror the Go ``cloudlets.Error`` struct defined in
    ``pkg/cloudlets/errors.go``.

    JSON serialization uses camelCase keys matching Go JSON tags.
    All fields carry ``omitempty`` — empty/zero values are omitted in
    the JSON output produced by :meth:`__str__`.
    """

    def __init__(
        self,
        type_="",
        title="",
        detail="",
        instance="",
        behavior_name="",
        error_location="",
        status_code=0,
        errors=None,
        warnings=None,
    ):
        """Initialize a Cloudlets Error.

        Args:
            type_: Error type URI (Go JSON tag: ``type``).
            title: Human-readable error title (Go JSON tag: ``title``).
            detail: Detailed error description (Go JSON tag: ``detail``).
            instance: Error instance identifier (Go JSON tag: ``instance``).
            behavior_name: Associated behavior name
                (Go JSON tag: ``behaviorName``).
            error_location: Location of the error
                (Go JSON tag: ``errorLocation``).
            status_code: HTTP status code (Go JSON tag: ``statusCode``).
            errors: Raw error details, preserved as-is from the JSON
                payload (Go JSON tag: ``errors``).
            warnings: Raw warning details, preserved as-is from the JSON
                payload (Go JSON tag: ``warnings``).
        """
        super().__init__(title)
        self.type = type_
        self.title = title
        self.detail = detail
        self.instance = instance
        self.behavior_name = behavior_name
        self.error_location = error_location
        self.status_code = status_code
        self.errors = errors
        self.warnings = warnings

    def __str__(self):
        """Format the error as indented JSON.

        Mirrors Go ``Error.Error()`` method which uses
        ``json.MarshalIndent(e, "", "\\t")``.

        Returns:
            ``"API error: \\n"`` followed by tab-indented JSON, or on
            marshal failure ``"error marshaling API error: <err>"``.
        """
        try:
            msg = json.dumps(self.to_dict(), indent="\t")
            return f"API error: \n{msg}"
        except (TypeError, ValueError) as err:
            return f"error marshaling API error: {err}"

    def to_dict(self):
        """Serialize to a dict with camelCase keys matching Go JSON tags.

        Fields with empty/default values are omitted to match Go
        ``omitempty`` behavior.

        Returns:
            Dictionary with camelCase keys suitable for JSON
            serialization.
        """
        result = {}
        if self.type:
            result["type"] = self.type
        if self.title:
            result["title"] = self.title
        if self.detail:
            result["detail"] = self.detail
        if self.instance:
            result["instance"] = self.instance
        if self.behavior_name:
            result["behaviorName"] = self.behavior_name
        if self.error_location:
            result["errorLocation"] = self.error_location
        if self.status_code:
            result["statusCode"] = self.status_code
        if self.errors is not None:
            result["errors"] = self.errors
        if self.warnings is not None:
            result["warnings"] = self.warnings
        return result

    def is_equivalent(self, other):
        """Compare errors by status code and string representation.

        Mirrors Go ``Error.Is()`` method (errors.go lines 63-78).

        Comparison steps:

        1. *other* must be an :class:`Error` instance.
        2. Identity comparison (``self is other``).
        3. Status codes must match.
        4. Full string representations must match.

        Args:
            other: Another :class:`Error` instance to compare against.

        Returns:
            ``True`` if this error is equivalent to *other*.
        """
        if not isinstance(other, Error):
            return False
        if self is other:
            return True
        if self.status_code != other.status_code:
            return False
        return str(self) == str(other)

    @classmethod
    def from_response(cls, response):
        """Parse an Error from an HTTP response.

        Mirrors the Go ``cloudlets.Error(r *http.Response)`` function
        (errors.go lines 29-52).  Reads the response body, attempts
        JSON deserialization, and falls back to an HTML-unescaped body
        on parse failure.

        Args:
            response: A :class:`requests.Response` object (or compatible
                object exposing ``.text`` and ``.status_code``).

        Returns:
            An :class:`Error` instance populated from the response.
        """
        try:
            body = response.text
        except Exception as err:  # pylint: disable=broad-exception-caught
            return cls(
                status_code=response.status_code,
                title="Failed to read error body",
                detail=str(err),
            )

        try:
            data = json.loads(body)
        except (json.JSONDecodeError, TypeError, ValueError):
            return cls(
                status_code=response.status_code,
                title=(
                    "Failed to unmarshal error body. Cloudlets API failed. "
                    "Check details for more information."
                ),
                detail=unescape_content(body),
            )

        return cls(
            type_=data.get("type", ""),
            title=data.get("title", ""),
            detail=data.get("detail", ""),
            instance=data.get("instance", ""),
            behavior_name=data.get("behaviorName", ""),
            error_location=data.get("errorLocation", ""),
            status_code=response.status_code,
            errors=data.get("errors"),
            warnings=data.get("warnings"),
        )


# ---------------------------------------------------------------------------
# Sentinel error constants — struct validation
# ---------------------------------------------------------------------------
# From cloudlets.go line 13
ErrStructValidation: str = "struct validation"

# ---------------------------------------------------------------------------
# Sentinel error constants — policies (from policy.go lines 150-158)
# ---------------------------------------------------------------------------
ErrListPolicies: str = "list policies"
ErrGetPolicy: str = "get policy"
ErrCreatePolicy: str = "create policy"
ErrRemovePolicy: str = "remove policy"
ErrUpdatePolicy: str = "update policy"

# ---------------------------------------------------------------------------
# Sentinel error constants — policy versions (from policy_version.go
# lines 121-129)
# ---------------------------------------------------------------------------
ErrListPolicyVersions: str = "list policy versions"
ErrGetPolicyVersion: str = "get policy versions"
ErrCreatePolicyVersion: str = "create policy versions"
ErrDeletePolicyVersion: str = "delete policy versions"
ErrUpdatePolicyVersion: str = "update policy versions"

# ---------------------------------------------------------------------------
# Sentinel error constants — policy version activations
# (from policy_version_activation.go lines 44-46)
# ---------------------------------------------------------------------------
ErrListPolicyActivations: str = "list policy activations"
ErrActivatePolicyVersion: str = "activate policy version"

# ---------------------------------------------------------------------------
# Sentinel error constants — policy version rules
# (from policy_version_rule.go lines 75-79)
# ---------------------------------------------------------------------------
ErrGetPolicyVersionRule: str = "get policy version rule"
ErrCreatePolicyVersionRule: str = "create policy version rule"
ErrUpdatePolicyVersionRule: str = "update policy version rule"

# ---------------------------------------------------------------------------
# Sentinel error constants — policy properties
# (from policy_property.go lines 60-62)
# ---------------------------------------------------------------------------
ErrGetPolicyProperties: str = "get policy properties"
ErrDeletePolicyProperty: str = "delete policy property"

# ---------------------------------------------------------------------------
# Sentinel error constants — origins / load balancers
# (from loadbalancer.go lines 75-81)
# ---------------------------------------------------------------------------
ErrListOrigins: str = "list origins"
ErrGetOrigin: str = "get origin"
ErrCreateOrigin: str = "create origin"
ErrUpdateOrigin: str = "update origin"

# ---------------------------------------------------------------------------
# Sentinel error constants — load balancer versions
# (from loadbalancer_version.go lines 107-113)
# ---------------------------------------------------------------------------
ErrCreateLoadBalancerVersion: str = "create origin version"
ErrGetLoadBalancerVersion: str = "get origin version"
ErrUpdateLoadBalancerVersion: str = "update origin version"
ErrListLoadBalancerVersions: str = "list origin versions"

# ---------------------------------------------------------------------------
# Sentinel error constants — load balancer activations
# (from loadbalancer_activation.go lines 83-85)
# ---------------------------------------------------------------------------
ErrListLoadBalancerActivations: str = "list load balancer activations"
ErrActivateLoadBalancerVersion: str = "activate load balancer version"

# ---------------------------------------------------------------------------
# Sentinel error constants — match rules (from match_rule.go lines 328-344)
# ---------------------------------------------------------------------------
ErrUnmarshallMatchCriteriaALB: str = "unmarshalling MatchCriteriaALB"
ErrUnmarshallMatchCriteriaAP: str = "unmarshalling MatchCriteriaAP"
ErrUnmarshallMatchCriteriaAS: str = "unmarshalling MatchCriteriaAS"
ErrUnmarshallMatchCriteriaPR: str = "unmarshalling MatchCriteriaPR"
ErrUnmarshallMatchCriteriaER: str = "unmarshalling MatchCriteriaER"
ErrUnmarshallMatchCriteriaFR: str = "unmarshalling MatchCriteriaFR"
ErrUnmarshallMatchCriteriaRC: str = "unmarshalling MatchCriteriaRC"
ErrUnmarshallMatchCriteriaVP: str = "unmarshalling MatchCriteriaVP"
ErrUnmarshallMatchRules: str = "unmarshalling MatchRules"
