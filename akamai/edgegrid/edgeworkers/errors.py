"""Error types and sentinel errors for EdgeWorkers/EdgeKV API.

Defines the EdgeWorkers-specific ``Error`` class (extending the
base ``Error``), the ``AdditionalDetail`` dataclass, a response-body parser
(``parse_edgeworkers_error``), error-code constants, and every operation
sentinel error constant used across the EdgeWorkers / EdgeKV package.

Mirrors Go ``pkg/edgeworkers/errors.go`` plus sentinel ``var Err…`` constants
declared in every other source file in the package.
"""

import json
from dataclasses import dataclass

from akamai.edgegrid.errors import Error as BaseError
from akamai.edgegrid.utils import unescape_content

# ---------------------------------------------------------------------------
# Error-code constants  (Go errors.go, lines 38-42)
# ---------------------------------------------------------------------------
ERROR_CODE_NOT_FOUND: str = "EKV_9000"
ERROR_CODE_VERSION_IS_BEING_DEACTIVATED: str = "EW1031"
ERROR_CODE_VERSION_ALREADY_DEACTIVATED: str = "EW1032"

# ---------------------------------------------------------------------------
# Special semantic sentinel errors  (Go errors.go, lines 44-51)
# These mirror Go naming conventions (``var Err… = errors.New("…")``).
# ---------------------------------------------------------------------------
# pylint: disable=invalid-name
ErrNotFound: str = "specified edgeKV resource does not exist"
ErrVersionBeingDeactivated: str = "version is being deactivated"
ErrVersionAlreadyDeactivated: str = "version is already deactivated"

# ---------------------------------------------------------------------------
# Operation sentinel errors — collected from ALL Go source files.
# Each Go ``var Err… = errors.New("…")`` maps to a Python string constant.
# ---------------------------------------------------------------------------

# From activations.go
ErrListActivations: str = "list activations"
ErrGetActivation: str = "get activation"
ErrActivateVersion: str = "activate version"
ErrCancelActivation: str = "cancel activation"

# From contracts.go
ErrListContracts: str = "list contracts"

# From deactivations.go
ErrListDeactivations: str = "list deactivations"
ErrDeactivateVersion: str = "deactivate version"
ErrGetDeactivation: str = "get deactivation"

# From edgekv_access_tokens.go
ErrCreateEdgeKVAccessToken: str = "create an EdgeKV access token"
ErrGetEdgeKVAccessToken: str = "get an EdgeKV access token"
ErrListEdgeKVAccessToken: str = "list EdgeKV access tokens"
ErrDeleteEdgeKVAccessToken: str = "delete an EdgeKV access token"

# From edgekv_groups.go
ErrListGroupsWithinNamespace: str = "list groups within namespace"

# From edgekv_initialize.go
ErrInitializeEdgeKV: str = "initialize EdgeKV"
ErrGetEdgeKVInitialize: str = "get EdgeKV initialization status"

# From edgekv_items.go
ErrListItems: str = "list items"
ErrGetItem: str = "get item"
ErrUpsertItem: str = "create or update item"
ErrDeleteItem: str = "delete item"

# From edgekv_namespaces.go
ErrListEdgeKVNamespace: str = "list EdgeKV namespaces"
ErrGetEdgeKVNamespace: str = "get an EdgeKV namespace"
ErrCreateEdgeKVNamespace: str = "create an EdgeKV namespace"
ErrUpdateEdgeKVNamespace: str = "update an EdgeKV namespace"
ErrDeleteEdgeKVNamespace: str = "delete an EdgeKV namespace"
ErrGetScheduledDeleteTime: str = (
    "get scheduled delete time for an EdgeKV namespace"
)
ErrRescheduleNamespaceDelete: str = (
    "change the scheduled time of an EdgeKV namespace delete"
)
ErrCancelScheduledNamespaceDelete: str = (
    "cancel the scheduled namespace delete"
)

# From edgeworker_id.go
ErrGetEdgeWorkerID: str = "get an EdgeWorker ID"
ErrListEdgeWorkersID: str = "list EdgeWorkers IDs"
ErrCreateEdgeWorkerID: str = "create an EdgeWorker ID"
ErrUpdateEdgeWorkerID: str = "update an EdgeWorker ID"
ErrCloneEdgeWorkerID: str = "clone an EdgeWorker ID"
ErrDeleteEdgeWorkerID: str = "delete an EdgeWorker ID"

# From edgeworker_version.go
ErrGetEdgeWorkerVersion: str = "get an EdgeWorker Version"
ErrListEdgeWorkerVersions: str = "list EdgeWorkers Versions"
ErrGetEdgeWorkerVersionContent: str = (
    "get an EdgeWorker Version Content Bundle"
)
ErrCreateEdgeWorkerVersion: str = "create an EdgeWorker Version"
ErrDeleteEdgeWorkerVersion: str = "delete an EdgeWorker Version"

# From permission_group.go
ErrGetPermissionGroup: str = "get a permission group"
ErrListPermissionGroups: str = "list permission groups"

# From properties.go
ErrListProperties: str = "list properties"

# From report.go
ErrGetSummaryReport: str = "get summary overview for EdgeWorker reports"
ErrGetReport: str = "get an EdgeWorker report"
ErrListReports: str = "get EdgeWorker reports"

# From resource_tier.go
ErrListResourceTiers: str = "list resource tiers"
ErrGetResourceTier: str = "get a resource tier"

# From secure_tokens.go
ErrCreateSecureToken: str = "create secure token"

# From validations.go
ErrValidateBundle: str = "validate a bundle"
# pylint: enable=invalid-name


# ---------------------------------------------------------------------------
# AdditionalDetail — mirrors Go ``Additional`` struct
# ---------------------------------------------------------------------------
@dataclass
class AdditionalDetail:
    """Additional detail embedded in EdgeWorkers / EdgeKV error responses.

    Mirrors Go ``pkg/edgeworkers.Additional`` struct which contains a single
    ``RequestID`` field (JSON tag ``"requestId"``).
    """

    request_id: str = ""


# ---------------------------------------------------------------------------
# Error — mirrors Go ``pkg/edgeworkers.Error`` struct
# ---------------------------------------------------------------------------
@dataclass
class Error(BaseError):  # pylint: disable=too-many-instance-attributes
    """EdgeWorkers / EdgeKV specific API error.

    Extends the base ``Error`` class with EdgeWorkers-specific fields such
    as ``error_code``, ``method``, ``server_ip``, ``client_ip``,
    ``request_id``, ``request_time``, ``authz_realm``, and
    ``additional_detail``.

    Mirrors the Go ``pkg/edgeworkers.Error`` struct (13 fields + nested
    ``Additional``).
    """

    # Fields matching Go Error struct JSON tags.  The parent ``BaseError``
    # also declares ``type``, ``title``, ``detail``, and ``instance`` — the
    # redeclarations here keep them at the child-dataclass position, which
    # is deliberate so that ``__str__`` and ``is_equivalent`` operate on
    # a consistent field set specific to EdgeWorkers.
    type: str = ""
    title: str = ""
    detail: str = ""
    instance: str = ""
    status: int = 0
    error_code: str = ""
    method: str = ""
    server_ip: str = ""
    client_ip: str = ""
    request_id: str = ""
    request_time: str = ""
    authz_realm: str = ""
    additional_detail: AdditionalDetail | None = None

    # Mapping of (Python attribute, JSON key) for serialization.
    _json_fields: tuple = (
        ("type", "type"),
        ("title", "title"),
        ("detail", "detail"),
        ("instance", "instance"),
        ("status", "status"),
        ("error_code", "errorCode"),
        ("method", "method"),
        ("server_ip", "serverIp"),
        ("client_ip", "clientIp"),
        ("request_id", "requestId"),
        ("request_time", "requestTime"),
        ("authz_realm", "authzRealm"),
    )

    # ------------------------------------------------------------------
    # String representation
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        """Format the error as indented JSON.

        Mirrors Go ``func (e *Error) Error() string`` which uses
        ``json.MarshalIndent``.  Fields with zero-values are omitted to
        replicate Go's ``omitempty`` JSON tag semantics.
        """
        error_dict: dict = {}
        for attr, key in self._json_fields:
            val = getattr(self, attr)
            if val:
                error_dict[key] = val
        if self.additional_detail and self.additional_detail.request_id:
            error_dict["additionalDetail"] = {
                "requestId": self.additional_detail.request_id
            }
        try:
            msg = json.dumps(error_dict, indent="\t")
            return f"API error: \n{msg}"
        except (TypeError, ValueError) as err:
            return f"error marshaling API error: {err}"

    # ------------------------------------------------------------------
    # Error equivalence
    # ------------------------------------------------------------------
    def _matches_sentinel(self, sentinel: str) -> bool:
        """Check if this error matches a well-known sentinel string.

        Returns ``True`` when the combination of ``status`` and
        ``error_code`` matches the sentinel's expected values.
        """
        if sentinel == ErrNotFound:
            return (
                self.status == 404
                and self.error_code == ERROR_CODE_NOT_FOUND
            )
        if sentinel == ErrVersionBeingDeactivated:
            return (
                self.error_code == ERROR_CODE_VERSION_IS_BEING_DEACTIVATED
            )
        if sentinel == ErrVersionAlreadyDeactivated:
            return (
                self.error_code == ERROR_CODE_VERSION_ALREADY_DEACTIVATED
            )
        return False

    def is_equivalent(self, other) -> bool:
        """Check error equivalence.

        Mirrors Go ``func (e *Error) Is(target error) bool``.

        Special sentinel-error handling (when *other* is a ``str``):

        * ``ErrNotFound``: matches when ``status == 404`` **and**
          ``error_code == "EKV_9000"``.
        * ``ErrVersionBeingDeactivated``: matches when
          ``error_code == "EW1031"``.
        * ``ErrVersionAlreadyDeactivated``: matches when
          ``error_code == "EW1032"``.

        When *other* is another ``Error`` the comparison falls
        through to a status check and then a full string-representation
        comparison.
        """
        if isinstance(other, str):
            return self._matches_sentinel(other)
        if not isinstance(other, Error):
            return False
        if self is other:
            return True
        return self.status == other.status and str(self) == str(other)


# ---------------------------------------------------------------------------
# Error parsing from HTTP response
# ---------------------------------------------------------------------------
def parse_edgeworkers_error(response) -> Error:
    """Parse an EdgeWorkers API error from an HTTP response.

    Attempts to read the response body as JSON and populate all
    ``Error`` fields.  If the body is not valid JSON the
    function falls back to HTML-unescaped plain text in the ``detail``
    field.

    Mirrors Go ``func (e *edgeworkers) Error(r *http.Response) error``.

    Args:
        response: A ``requests.Response`` (or compatible) object.

    Returns:
        A populated ``Error`` instance.
    """
    error = Error()

    # Read the response body — mirrors Go ioutil.ReadAll(r.Body)
    try:
        body = response.text
    except Exception as err:  # pylint: disable=broad-except
        error.status = response.status_code
        error.title = "Failed to read error body"
        error.detail = str(err)
        return error

    # Attempt JSON unmarshal — mirrors Go json.Unmarshal(body, &result)
    try:
        data = json.loads(body)
        error.type = data.get("type", "")
        error.title = data.get("title", "")
        error.detail = data.get("detail", "")
        error.instance = data.get("instance", "")
        error.status = data.get("status", 0)
        error.error_code = data.get("errorCode", "")
        error.method = data.get("method", "")
        error.server_ip = data.get("serverIp", "")
        error.client_ip = data.get("clientIp", "")
        error.request_id = data.get("requestId", "")
        error.request_time = data.get("requestTime", "")
        error.authz_realm = data.get("authzRealm", "")
        additional = data.get("additionalDetail")
        if additional and isinstance(additional, dict):
            error.additional_detail = AdditionalDetail(
                request_id=additional.get("requestId", "")
            )
    except (json.JSONDecodeError, AttributeError):
        error.title = (
            "Failed to unmarshal error body. Edgeworkers API failed. "
            "Check details for more information."
        )
        error.detail = unescape_content(body)
        error.status = response.status_code

    return error
