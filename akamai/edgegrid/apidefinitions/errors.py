"""Error types and sentinel errors for the API Definitions API.

Mirrors Go package at pkg/apidefinitions/errors.go and sentinel error
constants from endpoints.go, endpoint_versions.go, activations.go,
and resource_operations.go.
"""

import json
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Error(Exception):  # pylint: disable=too-many-instance-attributes
    """API Definitions error response.

    Parses RFC 7807 problem detail responses from the API Definitions API.
    Mirrors Go Error struct at pkg/apidefinitions/errors.go:11-36.

    All fields correspond 1:1 with Go struct fields using JSON tag names
    as the canonical reference. Pointer types (Go ``*string``, ``*int64``)
    map to ``str | None`` and ``int | None`` in Python.
    """

    # Fields without omitempty in Go — always present in JSON output
    type: str = ""   # pylint: disable=redefined-builtin
    title: str = ""
    detail: str = ""

    # Fields with omitempty in Go — only present when non-zero / non-empty
    instance: str = ""
    status: int = 0

    # Pointer fields with omitempty — only present when not None
    request_instance: str | None = None
    method: str | None = None
    request_time: str | None = None
    behavior_name: str | None = None
    error_location: str | None = None
    domain_prefix: str | None = None
    domain_suffix: str | None = None
    severity: str | None = None
    authz_realm: str | None = None
    server_ip: str | None = None
    client_ip: str | None = None
    request_id: str | None = None
    network: str | None = None
    version_number: int | None = None
    endpoint_id: int | None = None
    endpoint_name: str | None = None

    # Nested errors list — omitted from JSON when empty
    errors: list["Error"] = field(default_factory=list)

    # Mapping of (python_attr, json_key) for fields that use Go omitempty
    # with a truthiness check (non-empty string, non-zero int).
    _omitempty_truthy: tuple = field(
        default=(
            ("instance", "instance"),
            ("status", "status"),
        ),
        init=False,
        repr=False,
        compare=False,
    )

    # Mapping of (python_attr, json_key) for pointer fields that use Go
    # omitempty with a not-None check.
    _omitempty_not_none: tuple = field(
        default=(
            ("request_instance", "requestInstance"),
            ("method", "method"),
            ("request_time", "requestTime"),
            ("behavior_name", "behaviorName"),
            ("error_location", "errorLocation"),
            ("domain_prefix", "domainPrefix"),
            ("domain_suffix", "domainSuffix"),
            ("severity", "severity"),
            ("authz_realm", "authzRealm"),
            ("server_ip", "serverIp"),
            ("client_ip", "clientIp"),
            ("request_id", "requestId"),
            ("network", "network"),
            ("version_number", "versionNumber"),
            ("endpoint_id", "endpointId"),
            ("endpoint_name", "endpointName"),
        ),
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self):
        """Initialize Exception base class for proper exception behaviour."""
        Exception.__init__(self)

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def _to_dict(self) -> dict:
        """Convert to a dict matching Go ``json.MarshalIndent`` output.

        Go JSON ``omitempty`` semantics are reproduced exactly:

        * ``type``, ``title``, ``detail`` — always present (no omitempty).
        * All other scalar fields — present only when non-zero / non-empty.
        * Pointer fields — present only when not ``None``.
        * ``errors`` list — present only when non-empty.

        Returns:
            Dict with camelCase keys matching Go JSON tags.
        """
        result: dict = {
            "type": self.type,
            "title": self.title,
            "detail": self.detail,
        }

        for attr, key in self._omitempty_truthy:
            value = getattr(self, attr)
            if value:
                result[key] = value

        for attr, key in self._omitempty_not_none:
            value = getattr(self, attr)
            if value is not None:
                result[key] = value

        if self.errors:
            result["errors"] = [
                nested._to_dict()  # pylint: disable=protected-access
                if isinstance(nested, Error) else nested
                for nested in self.errors
            ]

        return result

    # ------------------------------------------------------------------
    # Public API — mirrors Go Error.Error() and Error.Is()
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        """Format the error as indented JSON.

        Mirrors Go ``Error.Error()`` at ``errors.go:65-71``.  Uses tab
        indentation to match Go's ``json.MarshalIndent("", "\\t")``.

        Returns:
            Formatted error string prefixed with ``API error:``.
        """
        try:
            msg = json.dumps(self._to_dict(), indent="\t")
            return f"API error: \n{msg}"
        except (TypeError, ValueError) as err:
            return f"error marshaling API error: {err}"

    def is_equivalent(self, target: "Error") -> bool:
        """Check error equivalence by status code and string representation.

        Mirrors Go ``Error.Is()`` at ``errors.go:74-89``.  Two errors are
        considered equivalent when they share the same HTTP status code **and**
        produce the same JSON string representation.

        Args:
            target: Error instance to compare against.

        Returns:
            ``True`` if the errors are equivalent, ``False`` otherwise.
        """
        if not isinstance(target, Error):
            return False
        if self is target:
            return True
        if self.status != target.status:
            return False
        return str(self) == str(target)

    # ------------------------------------------------------------------
    # Factory — mirrors Go apidefinitions.Error() response parser
    # ------------------------------------------------------------------

    @classmethod
    def _from_dict(cls, data: dict) -> "Error":
        """Create an ``Error`` from a JSON-decoded dict with camelCase keys.

        Maps camelCase JSON keys to snake_case Python field names and
        recursively constructs nested ``Error`` instances.

        Args:
            data: Dict decoded from a JSON error response body.

        Returns:
            Fully populated ``Error`` instance.
        """
        nested_errors_data = data.get("errors", [])
        nested_errors = [
            cls._from_dict(item) if isinstance(item, dict) else item
            for item in nested_errors_data
        ] if nested_errors_data else []

        return cls(
            type=data.get("type", ""),
            title=data.get("title", ""),
            detail=data.get("detail", ""),
            instance=data.get("instance", ""),
            status=data.get("status", 0),
            request_instance=data.get("requestInstance"),
            method=data.get("method"),
            request_time=data.get("requestTime"),
            behavior_name=data.get("behaviorName"),
            error_location=data.get("errorLocation"),
            domain_prefix=data.get("domainPrefix"),
            domain_suffix=data.get("domainSuffix"),
            severity=data.get("severity"),
            authz_realm=data.get("authzRealm"),
            server_ip=data.get("serverIp"),
            client_ip=data.get("clientIp"),
            request_id=data.get("requestId"),
            network=data.get("network"),
            version_number=data.get("versionNumber"),
            endpoint_id=data.get("endpointId"),
            endpoint_name=data.get("endpointName"),
            errors=nested_errors,
        )

    @classmethod
    def from_response(cls, response) -> "Error":
        """Parse an ``Error`` from an HTTP response object.

        Mirrors Go ``apidefinitions.Error()`` at ``errors.go:40-63``.

        The method reads the response body, attempts to unmarshal it as
        JSON into the ``Error`` fields, and falls back to storing the raw
        parse failure when the body is not valid JSON.  The HTTP status
        code from the response **always** overrides the ``status`` field
        regardless of what the JSON body contains.

        Args:
            response: HTTP response with ``.text`` and ``.status_code``
                attributes (compatible with ``requests.Response``).

        Returns:
            ``Error`` instance populated from the response.
        """
        error = cls()

        # Step 1 — read the response body text
        try:
            body = response.text
        except Exception as err:  # pylint: disable=broad-except
            logger.error("reading error response body: %s", err)
            error.status = response.status_code
            error.title = "Failed to read error body"
            error.detail = str(err)
            return error

        # Step 2 — attempt JSON unmarshal
        try:
            data = json.loads(body)
            error.type = data.get("type", "")
            error.title = data.get("title", "")
            error.detail = data.get("detail", "")
            error.instance = data.get("instance", "")
            error.request_instance = data.get("requestInstance")
            error.method = data.get("method")
            error.request_time = data.get("requestTime")
            error.behavior_name = data.get("behaviorName")
            error.error_location = data.get("errorLocation")
            error.domain_prefix = data.get("domainPrefix")
            error.domain_suffix = data.get("domainSuffix")
            error.severity = data.get("severity")
            error.authz_realm = data.get("authzRealm")
            error.server_ip = data.get("serverIp")
            error.client_ip = data.get("clientIp")
            error.request_id = data.get("requestId")
            error.network = data.get("network")
            error.version_number = data.get("versionNumber")
            error.endpoint_id = data.get("endpointId")
            error.endpoint_name = data.get("endpointName")
            nested_errors = data.get("errors", [])
            if nested_errors:
                error.errors = [
                    cls._from_dict(item) if isinstance(item, dict) else item
                    for item in nested_errors
                ]
        except (json.JSONDecodeError, AttributeError, TypeError) as err:
            logger.error("could not unmarshal API error: %s", err)
            error.title = "Failed to unmarshal error body"
            error.detail = str(err)

        # Step 3 — HTTP status always wins
        error.status = response.status_code
        return error


# ======================================================================
# Sentinel error constants
#
# Names use Go-style ``ErrXxx`` naming to match the Go v12 SDK exactly.
# ======================================================================

# pylint: disable=invalid-name

# --- endpoint operations (pkg/apidefinitions/endpoints.go:873-890) ---
ErrGetEndpoint: str = "get endpoint"
ErrListEndpoints: str = "list endpoints"
ErrRegisterEndpoint: str = "register endpoint"
ErrRegisterEndpointFromFile: str = "register endpoint from file"
ErrListUserEntitlements: str = "list user entitlements"
ErrShowEndpoint: str = "show endpoint"
ErrHideEndpoint: str = "hide endpoint"
ErrDeleteEndpoint: str = "delete endpoint"

# --- endpoint version operations (endpoint_versions.go:201-212) ---
ErrGetEndpointVersion: str = "get endpoint version"
ErrDeleteEndpointVersion: str = "delete endpoint version"
ErrListEndpointVersions: str = "list endpoint versions"
ErrCloneEndpointVersion: str = "clone endpoint version"
ErrUpdateEndpointVersion: str = "update endpoint version"

# --- activation operations (activations.go:104-111) ---
ErrVerifyVersion: str = "verify version"
ErrActivateVersion: str = "activate version"
ErrDeactivateVersion: str = "deactivate version"

# --- resource operations (resource_operations.go:108-111) ---
ErrSearchResourceAndOperations: str = "list resources and operations"

# pylint: enable=invalid-name
