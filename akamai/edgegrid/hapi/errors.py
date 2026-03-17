# pylint: disable=invalid-name,too-many-instance-attributes
"""Error types and sentinel errors for the HAPI service client."""

import json
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ErrorItem:
    """Represents a single error item in an HAPI error response.

    Mirrors Go hapi.ErrorItem struct.
    """

    key: str = ""
    value: str = ""


@dataclass
class Error(Exception):
    """HAPI API error response.

    Parses and represents structured error responses from the Akamai
    Hostname API. Supports sentinel error comparison.

    Mirrors Go pkg/hapi.Error struct.
    """

    type: str = ""
    title: str = ""
    detail: str = ""
    instance: str = ""
    request_instance: str = ""
    method: str = ""
    request_time: str = ""
    behavior_name: str = ""
    error_location: str = ""
    status: int = 0
    domain_prefix: str = ""
    domain_suffix: str = ""
    errors: list[ErrorItem] = field(default_factory=list)

    def __str__(self) -> str:
        """Format error as indented JSON.

        Mirrors Go Error.Error() method which uses json.MarshalIndent.
        Fields without omitempty in Go (type, title, detail) are always
        included. All other fields are only included when non-zero.
        """
        error_dict: dict = {}
        # type, title, detail have no omitempty in Go — always include
        error_dict["type"] = self.type
        error_dict["title"] = self.title
        error_dict["detail"] = self.detail
        # Remaining fields have omitempty — include only when non-zero
        if self.instance:
            error_dict["instance"] = self.instance
        if self.request_instance:
            error_dict["requestInstance"] = self.request_instance
        if self.method:
            error_dict["method"] = self.method
        if self.request_time:
            error_dict["requestTime"] = self.request_time
        if self.behavior_name:
            error_dict["behaviorName"] = self.behavior_name
        if self.error_location:
            error_dict["errorLocation"] = self.error_location
        if self.status:
            error_dict["status"] = self.status
        if self.domain_prefix:
            error_dict["domainPrefix"] = self.domain_prefix
        if self.domain_suffix:
            error_dict["domainSuffix"] = self.domain_suffix
        if self.errors:
            error_dict["errors"] = [
                {k: v for k, v in [("key", e.key), ("value", e.value)] if v}
                for e in self.errors
            ]
        try:
            msg = json.dumps(error_dict, indent="\t")
            return f"API error: \n{msg}"
        except (TypeError, ValueError) as err:
            return f"error marshaling API error: {err}"

    def __eq__(self, other) -> bool:
        """Check equality. Mirrors Go Error.Is() method.

        Special case: if other is ErrNotFound sentinel, check if status is 404.
        Otherwise compare by status code and string representation.
        """
        if isinstance(other, _SentinelError) and other.message == "not found":
            return self.status == 404
        if not isinstance(other, Error):
            return NotImplemented
        if self is other:
            return True
        if self.status != other.status:
            return False
        return str(self) == str(other)

    def __hash__(self):
        return id(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Error":
        """Create Error from parsed JSON dict.

        Args:
            data: Dictionary from JSON response body

        Returns:
            Populated Error instance
        """
        errors_data = data.get("errors", [])
        error_items: list[ErrorItem] = []
        if isinstance(errors_data, list):
            for item in errors_data:
                if isinstance(item, dict):
                    error_items.append(
                        ErrorItem(
                            key=item.get("key", ""),
                            value=item.get("value", ""),
                        )
                    )

        return cls(
            type=data.get("type", ""),
            title=data.get("title", ""),
            detail=data.get("detail", ""),
            instance=data.get("instance", ""),
            request_instance=data.get("requestInstance", ""),
            method=data.get("method", ""),
            request_time=data.get("requestTime", ""),
            behavior_name=data.get("behaviorName", ""),
            error_location=data.get("errorLocation", ""),
            status=data.get("status", 0),
            domain_prefix=data.get("domainPrefix", ""),
            domain_suffix=data.get("domainSuffix", ""),
            errors=error_items,
        )


class _SentinelError(Exception):
    """Internal sentinel error type for service-specific error constants.

    Mirrors Go's errors.New("sentinel message") pattern.
    """

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"_SentinelError({self.message!r})"


# Sentinel error constants — mirrors Go var declarations
# hapi.go line 15
ErrStructValidation = _SentinelError("struct validation")

# change_requests.go line 35
ErrGetChangeRequest = _SentinelError("get change request")

# edgehostname.go lines 186-196
ErrDeleteEdgeHostname = _SentinelError("delete edge hostname")
ErrGetEdgeHostname = _SentinelError("get edge hostname")
ErrUpdateEdgeHostname = _SentinelError("update edge hostname")
ErrGetCertificate = _SentinelError("get edge hostname certificate")
ErrNotFound = _SentinelError("not found")


def parse_hapi_error(response) -> Error:
    """Parse an HAPI API error from an HTTP response.

    Reads the response body, attempts JSON parsing for structured error,
    falls back to raw text with HTML unescaping on parse failure.

    Mirrors Go pkg/hapi.hapi.Error(r *http.Response) method.

    Args:
        response: A requests.Response object

    Returns:
        An Error instance populated from the response
    """
    # Lazy import to avoid circular imports
    from akamai.edgegrid.utils import unescape_content  # pylint: disable=import-outside-toplevel

    error = Error()

    try:
        body = response.text
    except Exception as err:  # pylint: disable=broad-exception-caught
        logger.error("reading error response body: %s", err)
        error.status = response.status_code
        error.title = "Failed to read error body"
        error.detail = str(err)
        return error

    try:
        data = json.loads(body)
        error = Error.from_dict(data)
    except (json.JSONDecodeError, AttributeError) as err:
        logger.error("could not unmarshal API error: %s", err)
        error.title = (
            "Failed to unmarshal error body. HAPI API failed. "
            "Check details for more information."
        )
        error.detail = unescape_content(body)

    error.status = response.status_code

    return error
