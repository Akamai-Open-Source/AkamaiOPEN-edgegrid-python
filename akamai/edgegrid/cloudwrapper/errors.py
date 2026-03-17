"""Cloud Wrapper API error types and sentinel errors.

Provides the Error and ErrorItem classes for structured Cloud Wrapper
API error handling, sentinel error constants for each API operation,
and a response parser for extracting errors from HTTP responses.

Mirrors Go pkg/cloudwrapper/errors.go and sentinel declarations from
cloudwrapper.go, configurations.go, capacity.go, locations.go,
multi_cdn.go, and properties.go.
"""

import json
from dataclasses import dataclass, field
from typing import Any

from akamai.edgegrid.utils import unescape_content

# ---------------------------------------------------------------------------
# Error type constants (from errors.go lines 41-43)
# ---------------------------------------------------------------------------
CONFIGURATION_NOT_FOUND_TYPE: str = "/cloud-wrapper/error-types/not-found"
DELETION_NOT_ALLOWED_TYPE: str = "/cloud-wrapper/error-types/forbidden"

# ---------------------------------------------------------------------------
# Sentinel error strings — used for operation-level error identification.
# Each sentinel mirrors a Go errors.New(...) declaration exactly.
# Names use Go convention (Err* prefix) to match Go SDK identifiers.
# ---------------------------------------------------------------------------
# pylint: disable=invalid-name

# From errors.go lines 47-49
ErrConfigurationNotFound: str = "configuration not found"
ErrDeletionNotAllowed: str = "deletion not allowed"

# From cloudwrapper.go line 13
ErrStructValidation: str = "struct validation"

# From configurations.go lines 355-368
ErrGetConfiguration: str = "get configuration"
ErrListConfigurations: str = "list configurations"
ErrCreateConfiguration: str = "create configuration"
ErrUpdateConfiguration: str = "update configuration"
ErrDeleteConfiguration: str = "delete configuration"
ErrActivateConfiguration: str = "activate configuration"

# From capacity.go line 66
ErrListCapacities: str = "list capacities"

# From locations.go line 36
ErrListLocations: str = "list locations"

# From multi_cdn.go lines 56-58
ErrListAuthKeys: str = "list auth keys"
ErrListCDNProviders: str = "list CDN providers"

# From properties.go lines 91-93
ErrListProperties: str = "list properties"
ErrListOrigins: str = "list origins"

# pylint: enable=invalid-name


# ---------------------------------------------------------------------------
# ErrorItem dataclass — mirrors Go cloudwrapper.ErrorItem struct
# (errors.go lines 31-37)
# ---------------------------------------------------------------------------
@dataclass
class ErrorItem:
    """Cloud Wrapper error item.

    Represents an individual validation or constraint error within an
    API error response.  Mirrors Go ``cloudwrapper.ErrorItem`` struct.
    """

    type: str = ""
    title: str = ""
    detail: str = ""
    illegal_value: Any = None     # JSON key: "illegalValue"
    illegal_parameter: str = ""   # JSON key: "illegalParameter"

    @classmethod
    def from_dict(cls, data: dict) -> "ErrorItem":
        """Create an ``ErrorItem`` from a JSON-decoded dictionary.

        Args:
            data: Dictionary with keys matching the Go JSON tags.

        Returns:
            A new ``ErrorItem`` instance.
        """
        return cls(
            type=data.get("type", ""),
            title=data.get("title", ""),
            detail=data.get("detail", ""),
            illegal_value=data.get("illegalValue"),
            illegal_parameter=data.get("illegalParameter", ""),
        )


# ---------------------------------------------------------------------------
# Error dataclass — mirrors Go cloudwrapper.Error struct
# (errors.go lines 13-28)
# ---------------------------------------------------------------------------
@dataclass
class Error(Exception):  # pylint: disable=too-many-instance-attributes
    """Cloud Wrapper API error.

    Mirrors Go ``cloudwrapper.Error`` struct.  Inherits from
    :class:`Exception` so it can be raised when the API returns an
    error response.

    Ref: https://techdocs.akamai.com/cloud-wrapper/reference/errors
    """

    type: str = ""                                     # JSON: "type"  (omitempty)
    title: str = ""                                    # JSON: "title" (omitempty)
    instance: str = ""                                 # JSON: "instance"
    status: int = 0                                    # JSON: "status"
    detail: str = ""                                   # JSON: "detail"
    errors: list = field(default_factory=list)          # JSON: "errors" — list[ErrorItem]
    method: str = ""                                   # JSON: "method"
    server_ip: str = ""                                # JSON: "serverIp"
    client_ip: str = ""                                # JSON: "clientIp"
    request_id: str = ""                               # JSON: "requestId"
    request_time: str = ""                             # JSON: "requestTime"

    def __post_init__(self):
        """Initialise the base ``Exception`` so that ``args`` is set."""
        super().__init__(str(self))

    # -- str / repr --------------------------------------------------------

    def __str__(self) -> str:
        """Format the error as indented JSON.

        Mirrors Go ``Error.Error()`` which uses
        ``json.MarshalIndent(e, "", "\\t")``.
        """
        error_dict: dict = {}

        # Fields with omitempty in Go — only include when non-empty
        if self.type:
            error_dict["type"] = self.type
        if self.title:
            error_dict["title"] = self.title

        # Fields without omitempty — always present
        error_dict["instance"] = self.instance
        error_dict["status"] = self.status
        error_dict["detail"] = self.detail

        # Serialize the nested errors list
        if self.errors:
            error_dict["errors"] = [
                {
                    "type": item.type if isinstance(item, ErrorItem) else "",
                    "title": item.title if isinstance(item, ErrorItem) else "",
                    "detail": item.detail if isinstance(item, ErrorItem) else "",
                    "illegalValue": (
                        item.illegal_value if isinstance(item, ErrorItem) else None
                    ),
                    "illegalParameter": (
                        item.illegal_parameter
                        if isinstance(item, ErrorItem)
                        else ""
                    ),
                }
                for item in self.errors
            ]
        else:
            # Go encodes a nil slice as null; empty Python list → null
            error_dict["errors"] = None

        error_dict["method"] = self.method
        error_dict["serverIp"] = self.server_ip
        error_dict["clientIp"] = self.client_ip
        error_dict["requestId"] = self.request_id
        error_dict["requestTime"] = self.request_time

        try:
            msg = json.dumps(error_dict, indent="\t")
            return f"API error: \n{msg}"
        except (TypeError, ValueError) as err:
            return f"error marshaling API error: {err}"

    # -- sentinel / equality -----------------------------------------------

    def is_equivalent(self, target) -> bool:
        """Check whether this error matches *target*.

        Mirrors Go ``Error.Is()`` (errors.go lines 83-105).  Handles
        sentinel error comparison for
        :data:`ErrConfigurationNotFound` and
        :data:`ErrDeletionNotAllowed`, then falls back to status-code
        and string-representation comparison for ``Error`` instances.

        Args:
            target: A sentinel error string or another ``Error`` instance.

        Returns:
            ``True`` if this error is considered equivalent to *target*.
        """
        # Sentinel error matching
        if target == ErrConfigurationNotFound:
            return self.status == 404 and self.type == CONFIGURATION_NOT_FOUND_TYPE
        if target == ErrDeletionNotAllowed:
            return self.status == 403 and self.type == DELETION_NOT_ALLOWED_TYPE

        # Error-to-Error comparison
        if not isinstance(target, Error):
            return False
        if self is target:
            return True
        if self.status != target.status:
            return False
        return str(self) == str(target)

    # -- deserialization ---------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict) -> "Error":
        """Create an ``Error`` from a JSON-decoded dictionary.

        Maps Go JSON tag names (camelCase) to Python attribute names
        (snake_case).

        Args:
            data: Dictionary with keys matching the Go JSON tags.

        Returns:
            A new ``Error`` instance.
        """
        errors_raw = data.get("errors") or []
        errors_list = [ErrorItem.from_dict(e) for e in errors_raw]
        return cls(
            type=data.get("type", ""),
            title=data.get("title", ""),
            instance=data.get("instance", ""),
            status=data.get("status", 0),
            detail=data.get("detail", ""),
            errors=errors_list,
            method=data.get("method", ""),
            server_ip=data.get("serverIp", ""),
            client_ip=data.get("clientIp", ""),
            request_id=data.get("requestId", ""),
            request_time=data.get("requestTime", ""),
        )


# ---------------------------------------------------------------------------
# Error response parser — mirrors Go cloudwrapper.Error() method
# (errors.go lines 53-72)
# ---------------------------------------------------------------------------

def parse_cloudwrapper_error(response) -> Error:
    """Parse a Cloud Wrapper API error from an HTTP response.

    Attempts to read the response body and parse it as JSON into an
    :class:`Error`.  If the body cannot be read or is not valid JSON, a
    fallback ``Error`` is constructed with the raw body (HTML-unescaped
    via :func:`~akamai.edgegrid.utils.unescape_content`).

    Mirrors Go ``cloudwrapper.Error()`` method (errors.go lines 53-72).

    Args:
        response: A :class:`requests.Response` (or compatible object
            exposing ``.text`` and ``.status_code``).

    Returns:
        An ``Error`` populated from the response.
    """
    result = Error()

    # Step 1 — read response body
    try:
        body = response.text
    except Exception as err:  # pylint: disable=broad-except
        result.status = response.status_code
        result.title = "Failed to read error body"
        result.detail = str(err)
        return result

    # Step 2 — attempt JSON deserialization
    try:
        data = json.loads(body)
        result = Error.from_dict(data)
    except (json.JSONDecodeError, ValueError):
        result.title = (
            "Failed to unmarshal error body. Cloud Wrapper API failed. "
            "Check details for more information."
        )
        result.detail = unescape_content(body)
        result.status = response.status_code

    return result
