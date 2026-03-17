# pylint: disable=invalid-name
"""Error types for the Application Security API client.

Defines the AppSec-specific Error class and sentinel error constants,
mirroring Go pkg/appsec/errors.go and appsec.go.
"""

import json
import logging
from dataclasses import dataclass

from akamai.edgegrid.utils import unescape_content

logger = logging.getLogger(__name__)


# Sentinel errors — mirrors Go var declarations in errors.go and appsec.go

# ErrBadRequest is returned when a required parameter is missing.
# Mirrors Go: ErrBadRequest = errors.New("missing argument")
ErrBadRequest = "missing argument"

# ErrStructValidation is returned when given struct validation failed.
# Mirrors Go: ErrStructValidation = errors.New("struct validation")
ErrStructValidation = "struct validation"

# ErrRequestCreation is returned when creating an HTTP request failed.
# Mirrors Go: ErrRequestCreation = errors.New("HTTP request failure")
ErrRequestCreation = "HTTP request failure"

# ErrAPICallFailure is returned when an AppSec OpenAPI call failed.
# Mirrors Go: ErrAPICallFailure = errors.New("API call failure")
ErrAPICallFailure = "API call failure"


@dataclass
class Error(Exception):
    """Application Security API error.

    Parses error responses from the Akamai Application Security API.
    Mirrors Go pkg/appsec Error struct with identical fields.

    The Error struct has the following fields from Go:
    - Type:          string  json:"type"
    - Title:         string  json:"title"
    - Detail:        string  json:"detail"
    - Instance:      string  json:"instance,omitempty"
    - BehaviorName:  string  json:"behaviorName,omitempty"
    - ErrorLocation: string  json:"errorLocation,omitempty"
    - StatusCode:    int     json:"-"
    """

    # pylint: disable=redefined-builtin
    type: str = ""
    title: str = ""
    detail: str = ""
    instance: str = ""
    behavior_name: str = ""
    error_location: str = ""
    status_code: int = 0

    def __str__(self) -> str:
        """Format error as 'Title: ...; Type: ...; Detail: ...'.

        Mirrors Go Error.Error() method exactly:
        fmt.Sprintf("Title: %s; Type: %s; Detail: %s", e.Title, e.Type, e.Detail)
        """
        return f"Title: {self.title}; Type: {self.type}; Detail: {self.detail}"

    def is_equivalent(self, other: "Error") -> bool:
        """Check if this error is equivalent to another Error.

        Mirrors Go Error.Is() method:
        1. Check if both are Error instances
        2. Check if same object reference
        3. Compare StatusCode
        4. Compare Error() string output

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

    @classmethod
    def from_response(cls, response) -> "Error":
        """Parse an AppSec API error from an HTTP response.

        Mirrors Go (p *appsec) Error(r *http.Response) error method:
        1. Read response body
        2. Try JSON unmarshal into Error fields
        3. On failure: set fallback title + unescape content for detail
        4. Set StatusCode from response status code

        Args:
            response: A requests.Response object.

        Returns:
            An Error instance populated from the response.
        """
        error = cls()

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
        except (json.JSONDecodeError, AttributeError) as err:
            logger.error("could not unmarshal API error: %s", err)
            error.title = (
                "Failed to unmarshal error body. "
                "Application Security API failed. "
                "Check details for more information."
            )
            error.detail = unescape_content(body)

        error.status_code = response.status_code
        return error
