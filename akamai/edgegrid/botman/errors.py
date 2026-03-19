# pylint: disable=invalid-name
"""Error types for the Akamai Bot Manager API client.

Provides Bot Manager-specific error handling that mirrors the Go
pkg/botman error types from AkamaiOPEN-edgegrid-golang/v12.

Attributes:
    ErrStructValidation: Sentinel value for struct validation failures.
    Error: Represents an error response from the Bot Manager API.
"""

import json
import logging

from akamai.edgegrid.utils import unescape_content

logger = logging.getLogger(__name__)


# ErrStructValidation is the sentinel value for struct validation failures.
# Mirrors Go: var ErrStructValidation = errors.New("struct validation")
ErrStructValidation = "struct validation"


class Error(Exception):
    """Bot Manager API error.

    Represents an error response from the Bot Manager API.
    Mirrors Go pkg/botman.Error struct (errors.go).

    Fields match Go struct fields exactly:
        type:        Error type string (JSON: "type")
        title:       Error title (JSON: "title")
        detail:      Error detail message (JSON: "detail")
        errors:      List of child Error objects (JSON: "errors", omitempty)
        status_code: HTTP status code (JSON: "status", omitempty)

    The __str__ output format matches Go's Error.Error() method:
        "Title: {title}; Type: {type}; Detail: {detail}"
    with child error details appended as ": [{d1}, {d2} ]".
    """

    # pylint: disable=redefined-builtin,too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        type: str = "",
        title: str = "",
        detail: str = "",
        errors: list | None = None,
        status_code: int = 0,
    ):
        """Initialize Error with fields matching Go struct.

        Args:
            type:        Error type string.
            title:       Error title.
            detail:      Error detail message.
            errors:      Optional list of child Error objects.
            status_code: HTTP response status code.
        """
        super().__init__(self._format_message(type, title, detail, errors))
        self.type = type
        self.title = title
        self.detail = detail
        self.errors: list = errors if errors is not None else []
        self.status_code = status_code

    # pylint: enable=redefined-builtin

    @staticmethod
    def _format_message(
        type_val: str, title: str, detail: str, errors: list | None
    ) -> str:
        """Format error message matching Go's Error.Error() method exactly.

        Produces the format: "Title: {title}; Type: {type}; Detail: {detail}"
        If child errors exist, appends ": [{d1}, {d2} ]" to the detail portion.
        Note the trailing space before the closing bracket, matching Go behavior.

        Args:
            type_val: Error type string.
            title:    Error title.
            detail:   Error detail message.
            errors:   Optional list of child Error instances.

        Returns:
            Formatted error string matching Go output exactly.
        """
        detail_str = detail
        if errors:
            child_details = [
                e.detail if isinstance(e, Error) else str(e) for e in errors
            ]
            detail_str += ": [" + ", ".join(child_details) + " ]"
        return f"Title: {title}; Type: {type_val}; Detail: {detail_str}"

    def __str__(self) -> str:
        """Return formatted error string matching Go's Error.Error().

        Returns:
            String in format "Title: ...; Type: ...; Detail: ..."
        """
        return self._format_message(
            self.type, self.title, self.detail, self.errors
        )

    def is_equivalent(self, other: "Error") -> bool:
        """Check error equivalence matching Go's Error.Is() method.

        Mirrors Go pkg/botman.Error.Is() which compares identity first,
        then status_code, then full string representation.

        Args:
            other: Another Error instance to compare against.

        Returns:
            True if the errors are equivalent, False otherwise.
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
        """Parse an Error from an HTTP response.

        Mirrors Go botman.Error() method (the method on *botman receiver,
        not the Error type). Reads the response body, attempts JSON unmarshal
        into Error fields. On JSON parse failure, falls back to raw text with
        HTML entity unescaping via unescape_content.

        The status_code is always set from response.status_code as the final
        step, matching Go's pattern where e.StatusCode = r.StatusCode is
        assigned after all body parsing logic.

        Args:
            response: A requests.Response object.

        Returns:
            An Error instance populated from the response.
        """
        error = cls()

        try:
            body = response.text
        except Exception as err:  # pylint: disable=broad-except
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
            error.status_code = data.get("status", 0)
            raw_errors = data.get("errors", [])
            if raw_errors:
                error.errors = [
                    cls(
                        type=e.get("type", ""),
                        title=e.get("title", ""),
                        detail=e.get("detail", ""),
                        status_code=e.get("status", 0),
                    )
                    for e in raw_errors
                    if isinstance(e, dict)
                ]
        except (json.JSONDecodeError, AttributeError) as err:
            logger.error("could not unmarshal API error: %s", err)
            error.title = (
                "Failed to unmarshal error body. Bot Manager API failed. "
                "Check details for more information."
            )
            error.detail = unescape_content(body)

        error.status_code = response.status_code

        return error
