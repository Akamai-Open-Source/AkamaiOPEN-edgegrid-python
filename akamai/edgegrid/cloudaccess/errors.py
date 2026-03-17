"""Error types for Cloud Access Manager API.

Defines the service-specific ``Error`` and ``ErrorItem`` data classes for
parsing RFC 7807 error responses, as well as sentinel error string constants
for every Cloud Access Manager API operation.

Mirrors Go ``pkg/cloudaccess/errors.go`` plus sentinel error variables from
``access_key.go``, ``access_key_version.go``, and ``properties.go``.
"""

import json
import logging
from dataclasses import dataclass, field

from akamai.edgegrid.utils import unescape_content

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Error type URI constant (Go: const accessKeyNotFoundType)
# ---------------------------------------------------------------------------
ACCESS_KEY_NOT_FOUND_TYPE: str = "/cam/error-types/access-key-does-not-exist"


# ---------------------------------------------------------------------------
# Sentinel error constants
#
# Each value mirrors the corresponding ``errors.New(...)`` string in Go.
# They are plain strings used for error wrapping and identification.
# Names intentionally mirror Go convention (ErrXxx) for cross-SDK consistency.
# ---------------------------------------------------------------------------

# pylint: disable=invalid-name

# From errors.go line 40
ErrAccessKeyNotFound: str = "access key not found"

# From access_key.go lines 148-163
ErrGetAccessKeyStatus: str = "get the status of an access key"
ErrCreateAccessKey: str = "create an access key"
ErrGetAccessKey: str = "get an access key"
ErrUpdateAccessKey: str = "update an access key"
ErrDeleteAccessKey: str = "delete an access key"

# From access_key_version.go lines 145-156
ErrGetAccessKeyVersionStatus: str = "get the status of an access key version"
ErrCreateAccessKeyVersion: str = "create access key version"
ErrGetAccessKeyVersion: str = "get access key version"
ErrListAccessKeyVersions: str = "list access key versions"
ErrDeleteAccessKeyVersion: str = "delete access key version"

# From properties.go lines 101-108
ErrLookupProperties: str = "lookup properties"
ErrGetAsyncLookupIDProperties: str = "get lookup properties id async"
ErrPerformAsyncLookupProperties: str = "perform async lookup properties"

# pylint: enable=invalid-name


# ---------------------------------------------------------------------------
# Error data classes
# ---------------------------------------------------------------------------


@dataclass
class ErrorItem:
    """A single error item in a Cloud Access Manager error response.

    Mirrors Go ``cloudaccess.ErrorItem`` struct (errors.go lines 30-34).
    Each field defaults to an empty string matching Go zero values.

    Attributes:
        detail: Error detail message.
        title:  Error title.
        type:   Error type URI.
    """

    detail: str = ""
    title: str = ""
    # The built-in name ``type`` is intentionally reused to match the Go
    # struct field name exactly.
    type: str = ""  # pylint: disable=redefined-builtin


@dataclass
class Error(Exception):  # pylint: disable=too-many-instance-attributes
    """Cloud Access Manager API error.

    Parses and represents error responses from the Cloud Access Manager API.
    For details on possible error types, refer to:
    https://techdocs.akamai.com/cloud-access-mgr/reference/errors

    Mirrors Go ``cloudaccess.Error`` struct (errors.go lines 16-27).
    Extends ``Exception`` so instances can be raised and caught in standard
    Python exception-handling flows.

    Attributes:
        type:            Error type URI.
        title:           Short, human-readable summary.
        detail:          Longer human-readable explanation.
        instance:        URI reference identifying the specific occurrence.
        status:          HTTP status code.
        access_key_uid:  UID of the access key (omitempty).
        access_key_name: Name of the access key (omitempty).
        problem_id:      Unique problem identifier (omitempty).
        version:         Access key version number.
        errors:          List of nested error items (omitempty).
    """

    type: str = ""  # pylint: disable=redefined-builtin
    title: str = ""
    detail: str = ""
    instance: str = ""
    status: int = 0
    access_key_uid: int = 0
    access_key_name: str = ""
    problem_id: str = ""
    version: int = 0
    errors: list[ErrorItem] = field(default_factory=list)

    def __post_init__(self):
        """Initialise the ``Exception`` base with this error's string form."""
        super().__init__(str(self))

    # ------------------------------------------------------------------
    # String representation — mirrors Go Error.Error()
    # ------------------------------------------------------------------

    def __str__(self) -> str:
        """Format error as indented JSON string.

        Mirrors Go ``Error.Error()`` (errors.go lines 66-72).
        Output format: ``"API error: \\n{tab-indented json}"``
        """
        error_dict = self._to_dict()
        try:
            msg = json.dumps(error_dict, indent="\t")
            return f"API error: \n{msg}"
        except (TypeError, ValueError) as err:
            return f"error marshaling API error: {err}"

    def _to_dict(self) -> dict:
        """Convert to dictionary matching Go ``json.MarshalIndent`` output.

        Non-omitempty fields are ALWAYS included (even when zero-valued).
        omitempty fields (``accessKeyUid``, ``accessKeyName``, ``problemId``,
        ``errors``) are only included when non-zero/non-empty.
        ``version`` is NOT omitempty — always present.
        """
        result: dict = {
            "type": self.type,
            "title": self.title,
            "detail": self.detail,
            "instance": self.instance,
            "status": self.status,
        }
        # omitempty fields — include only when non-zero / non-empty
        if self.access_key_uid:
            result["accessKeyUid"] = self.access_key_uid
        if self.access_key_name:
            result["accessKeyName"] = self.access_key_name
        if self.problem_id:
            result["problemId"] = self.problem_id
        # version is NOT omitempty in Go — always present
        result["version"] = self.version
        if self.errors:
            result["errors"] = [
                {"detail": e.detail, "title": e.title, "type": e.type}
                for e in self.errors
            ]
        return result

    # ------------------------------------------------------------------
    # Equivalence check — mirrors Go Error.Is()
    # ------------------------------------------------------------------

    def is_equivalent(self, target) -> bool:
        """Check error equivalence.

        Mirrors Go ``Error.Is()`` (errors.go lines 75-94).

        Special case: if *target* is the ``ErrAccessKeyNotFound`` sentinel
        string, returns ``True`` when ``status == 404`` **and**
        ``type == ACCESS_KEY_NOT_FOUND_TYPE``.

        For ``Error``-vs-``Error`` comparison, uses identity check, then
        status comparison, then full string-representation comparison.
        """
        if isinstance(target, str) and target == ErrAccessKeyNotFound:
            return (
                self.status == 404
                and self.type == ACCESS_KEY_NOT_FOUND_TYPE
            )

        if not isinstance(target, Error):
            return False
        if self is target:
            return True
        if self.status != target.status:
            return False
        return str(self) == str(target)

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    @classmethod
    def from_response(cls, response) -> "Error":
        """Parse an ``Error`` from an HTTP response.

        Mirrors Go ``cloudaccess.Error()`` method (errors.go lines 43-64).
        Reads the response body, attempts JSON unmarshal, and falls back to
        raw text with HTML unescaping when JSON parsing fails.  The HTTP
        status code from *response* **always** overrides any status value
        found in the JSON payload.

        Args:
            response: A ``requests.Response`` object.

        Returns:
            Populated ``Error`` instance.
        """
        error = cls()

        # Step 1: read body (mirrors Go io.ReadAll)
        try:
            body = response.text
        except Exception as err:  # pylint: disable=broad-except
            logger.error("reading error response body: %s", err)
            error.status = response.status_code
            error.title = "Failed to read error body"
            error.detail = str(err)
            return error

        # Step 2: attempt JSON unmarshal
        try:
            data = json.loads(body)
            error.type = data.get("type", "")
            error.title = data.get("title", "")
            error.detail = data.get("detail", "")
            error.instance = data.get("instance", "")
            error.access_key_uid = data.get("accessKeyUid", 0)
            error.access_key_name = data.get("accessKeyName", "")
            error.problem_id = data.get("problemId", "")
            error.version = data.get("version", 0)
            raw_errors = data.get("errors", [])
            if raw_errors:
                error.errors = [
                    ErrorItem(
                        detail=e.get("detail", ""),
                        title=e.get("title", ""),
                        type=e.get("type", ""),
                    )
                    for e in raw_errors
                ]
        except (json.JSONDecodeError, AttributeError) as err:
            logger.error("could not unmarshal API error: %s", err)
            error.title = (
                "Failed to unmarshal error body. Cloud Access Manager "
                "API failed. Check details for more information."
            )
            error.detail = unescape_content(body)

        # Step 3: always override status with actual HTTP status code
        error.status = response.status_code
        return error

    @classmethod
    def from_dict(cls, data: dict) -> "Error":
        """Create an ``Error`` from a dictionary (JSON-parsed payload).

        Useful for constructing ``Error`` instances from already-parsed JSON
        without going through an HTTP response object.

        Args:
            data: Dictionary with camelCase keys matching Go JSON tags.

        Returns:
            Populated ``Error`` instance.
        """
        raw_errors = data.get("errors", [])
        error_items = [
            ErrorItem(
                detail=e.get("detail", ""),
                title=e.get("title", ""),
                type=e.get("type", ""),
            )
            for e in raw_errors
        ] if raw_errors else []

        return cls(
            type=data.get("type", ""),
            title=data.get("title", ""),
            detail=data.get("detail", ""),
            instance=data.get("instance", ""),
            status=data.get("status", 0),
            access_key_uid=data.get("accessKeyUid", 0),
            access_key_name=data.get("accessKeyName", ""),
            problem_id=data.get("problemId", ""),
            version=data.get("version", 0),
            errors=error_items,
        )
