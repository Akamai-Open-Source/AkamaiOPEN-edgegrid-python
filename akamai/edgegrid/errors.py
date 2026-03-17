"""Base error types for Akamai API responses.

Provides the base Error class shared across all 22+ Akamai service clients,
sentinel exception classes for common error conditions, and a response parser
for RFC 7807 problem detail payloads.

Mirrors the common error patterns found in every Go v12 pkg/*/errors.go file.
"""

import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Error(Exception):
    """Base API error class for Akamai API responses.

    Parses RFC 7807 problem detail responses from Akamai APIs.
    This is the base class that service-specific error classes can
    extend with additional fields.

    Mirrors the common Error struct pattern found across all
    Go v12 pkg/*/errors.go.
    """

    # pylint: disable=redefined-builtin
    type: str = ""
    title: str = ""
    detail: str = ""
    instance: str = ""
    status_code: int = 0
    errors: list | dict | str | None = None

    def __str__(self) -> str:
        """Format error as indented JSON, matching Go's Error() method.

        Produces output in the form:
            API error:
            {
                "type": "...",
                "title": "...",
                ...
            }

        Fields with empty/zero/None values that have omitempty semantics
        in Go are excluded from the JSON output.
        """
        error_dict = {
            "type": self.type,
            "title": self.title,
            "detail": self.detail,
        }
        if self.instance:
            error_dict["instance"] = self.instance
        if self.status_code:
            error_dict["statusCode"] = self.status_code
        if self.errors is not None:
            error_dict["errors"] = self.errors
        try:
            msg = json.dumps(error_dict, indent="\t")
            return f"API error: \n{msg}"
        except (TypeError, ValueError) as err:
            return f"error marshaling API error: {err}"

    def is_equivalent(self, other: "Error") -> bool:
        """Check if this error is equivalent to another Error.

        Mirrors Go's Error.Is() method for sentinel error comparison.
        Compares by status_code first, then by full string representation.

        Args:
            other: The Error instance to compare against.

        Returns:
            True if the errors are considered equivalent.
        """
        if not isinstance(other, Error):
            return False
        if self is other:
            return True
        if self.status_code != other.status_code:
            return False
        return str(self) == str(other)


class ErrStructValidation(Exception):
    """Sentinel exception raised when request struct validation fails.

    Mirrors Go's edgegriderr pattern where validation errors prevent
    HTTP requests from being made. Raised by validation functions
    before any HTTP request is sent.
    """

    def __init__(self, message: str = "struct validation"):
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return self.message


class ErrInvalidArgument(Exception):
    """Raised when invalid arguments are provided.

    Mirrors Go pkg/session/request.go ErrInvalidArgument sentinel error.
    """


class ErrMarshaling(Exception):
    """Raised when JSON marshaling of request body fails.

    Mirrors Go pkg/session/request.go ErrMarshaling sentinel error.
    """


class ErrUnmarshaling(Exception):
    """Raised when JSON unmarshaling of response body fails.

    Mirrors Go pkg/session/request.go ErrUnmarshaling sentinel error.
    """


def parse_error_response(response) -> Error:
    """Parse an API error from an HTTP response.

    Reads the response body, attempts JSON parsing for RFC 7807 structure,
    falls back to raw text with HTML unescaping on parse failure.

    Mirrors the common Error() method pattern across all Go service
    packages (e.g., pkg/iam/errors.go, pkg/papi/errors.go).

    Args:
        response: A requests.Response object.

    Returns:
        An Error instance populated from the response.
    """
    # Lazy import to avoid circular dependencies between modules
    # pylint: disable=import-outside-toplevel
    from akamai.edgegrid.utils import unescape_content

    error = Error()

    try:
        body = response.text
    except Exception as err:  # pylint: disable=broad-exception-caught
        logger.error("reading error response body: %s", err)
        error.status_code = response.status_code
        error.title = "Failed to read error body"
        error.detail = str(err)
        return error

    try:
        data = json.loads(body)
        error.type = data.get("type", "")
        error.title = data.get("title", "")
        error.detail = data.get("detail", "")
        error.instance = data.get("instance", "")
        error.status_code = (
            data.get("statusCode", 0) or data.get("httpStatus", 0)
        )
        error.errors = data.get("errors")
    except (json.JSONDecodeError, AttributeError) as err:
        logger.error("could not unmarshal API error: %s", err)
        error.title = (
            "Failed to unmarshal error body. API failed. "
            "Check details for more information."
        )
        error.detail = unescape_content(body)

    error.status_code = response.status_code

    return error
