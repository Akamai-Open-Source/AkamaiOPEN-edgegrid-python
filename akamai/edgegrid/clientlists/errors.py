"""Error types for the Client Lists API.

Provides the service-specific Error class for Client Lists API responses,
the ErrStructValidation sentinel exception for request validation failures,
and a parse_error_response() function for extracting structured errors from
HTTP responses.

Mirrors Go pkg/clientlists/errors.go.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from akamai.edgegrid.utils import unescape_content

# ErrStructValidation is the sentinel exception for struct validation failures.
# Mirrors Go: var ErrStructValidation = errors.New("struct validation")
# Re-exported from the base errors module so service-level code can import it
# from the service package, matching Go's per-package ErrStructValidation pattern.
# pylint: disable=unused-import
from akamai.edgegrid.errors import ErrStructValidation  # noqa: F401

__all__ = ["Error", "ErrStructValidation", "parse_error_response"]

logger = logging.getLogger(__name__)


# pylint: disable=redefined-builtin
@dataclass
class Error(Exception):
    """Client Lists API error.

    Represents an error response from the Client Lists API. Contains fields
    for the error type, title, detail, instance, behavior name, error location,
    and HTTP status code.

    Mirrors Go pkg/clientlists.Error struct (errors.go lines 13-23).

    Note: The __str__() format for Client Lists uses
    "Title: ...; Type: ...; Detail: ..." which is DIFFERENT from the base
    error's JSON-indented format. This matches Go's Error.Error() exactly.
    """

    type: str = ""
    title: str = ""
    detail: str = ""
    instance: str = ""
    behavior_name: str = ""
    error_location: str = ""
    status_code: int = 0

    def __str__(self) -> str:
        """Format error matching Go's Error.Error() output exactly.

        Produces output in the form:
            Title: <title>; Type: <type>; Detail: <detail>

        Mirrors Go errors.go line 52-54:
            fmt.Sprintf("Title: %s; Type: %s; Detail: %s", e.Title, e.Type, e.Detail)

        Returns:
            Formatted error string.
        """
        return f"Title: {self.title}; Type: {self.type}; Detail: {self.detail}"

    def is_equivalent(self, other: Error) -> bool:
        """Check if this error is equivalent to another Error.

        Mirrors Go's Error.Is() method (errors.go lines 57-72).
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


def parse_error_response(response) -> Error:
    """Parse an API error from an HTTP response.

    Reads the response body, attempts JSON parsing for the Client Lists
    error structure, and falls back to raw text with HTML unescaping
    when JSON parsing fails.

    Mirrors Go clientlists.Error() method (errors.go lines 27-50).

    Args:
        response: A requests.Response object.

    Returns:
        An Error instance populated from the response.
    """
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
        error.behavior_name = data.get("behaviorName", "")
        error.error_location = data.get("errorLocation", "")
    except (json.JSONDecodeError, ValueError) as err:
        logger.error("could not unmarshal API error: %s", err)
        error.title = (
            "Failed to unmarshal error body. Client Lists API failed. "
            "Check details for more information."
        )
        error.detail = unescape_content(body)

    error.status_code = response.status_code
    return error
