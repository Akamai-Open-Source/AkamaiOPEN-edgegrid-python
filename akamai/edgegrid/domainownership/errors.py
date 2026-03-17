# pylint: disable=invalid-name
"""Error types and sentinel errors for Domain Ownership API.

Defines the Error and ErrorDetail dataclasses for RFC 7807 problem detail
responses, a parse_error_response function for extracting errors from HTTP
responses, and all sentinel error constants used by the domain ownership
client.

Mirrors Go pkg/domainownership errors.go, domains.go sentinel errors,
validations.go sentinel errors, and domainownership.go ErrStructValidation.
"""

from dataclasses import dataclass, field
import json
import logging


logger = logging.getLogger(__name__)


@dataclass
class ErrorDetail:
    """Represents a specific problem in the error response.

    Mirrors Go domainownership.ErrorDetail struct with fields matching
    JSON tag names: type, title, detail, problemId, field.

    Attributes:
        type: The error type identifier.
        title: A short human-readable summary of the problem.
        detail: A detailed human-readable explanation of the problem.
        problem_id: A unique identifier for this specific problem occurrence.
        field: The request field that caused the error.
    """

    type: str = ""  # pylint: disable=redefined-builtin
    title: str = ""
    detail: str = ""
    problem_id: str = ""
    field: str = ""


@dataclass
class Error(Exception):
    """Domain Ownership API error response.

    Parses RFC 7807 problem detail responses from the Domain Ownership API.
    Mirrors Go domainownership.Error struct.

    The __str__ method serializes the error as indented JSON using tab
    characters, matching Go's json.MarshalIndent output format. JSON field
    names use camelCase to match Go struct JSON tags.

    Attributes:
        type: The error type identifier.
        title: A short human-readable summary of the problem.
        detail: A detailed human-readable explanation of the problem.
        instance: A URI reference identifying the specific occurrence.
        status: The HTTP status code.
        errors: A list of specific problems in the response.
        problem_id: A unique identifier for this problem occurrence.
    """

    type: str = ""  # pylint: disable=redefined-builtin
    title: str = ""
    detail: str = ""
    instance: str = ""
    status: int = 0
    errors: list[ErrorDetail] = field(default_factory=list)
    problem_id: str = ""

    def __post_init__(self):
        """Initialize the Exception base class."""
        Exception.__init__(self)

    def __str__(self) -> str:
        """Format error as indented JSON.

        Mirrors Go Error.Error() which uses json.MarshalIndent with tab
        indentation. Fields are serialized using JSON tag names (camelCase).
        The ``errors`` key is omitted when the list is empty, matching Go's
        ``omitempty`` JSON tag behavior.

        Returns:
            A formatted string prefixed with ``API error:`` followed by the
            indented JSON representation.
        """
        try:
            data = {
                "type": self.type,
                "title": self.title,
                "detail": self.detail,
                "instance": self.instance,
                "status": self.status,
            }
            if self.errors:
                data["errors"] = [
                    {
                        "type": e.type,
                        "title": e.title,
                        "detail": e.detail,
                        "problemId": e.problem_id,
                        "field": e.field,
                    }
                    for e in self.errors
                ]
            data["problemId"] = self.problem_id
            msg = json.dumps(data, indent="\t")
            return f"API error: \n{msg}"
        except (TypeError, ValueError) as err:
            return f"error marshaling API error: {err}"

    def is_equivalent(self, target) -> bool:
        """Check error equivalence.

        Mirrors Go Error.Is() which uses errors.As to extract the Error
        from the target error chain, then compares status codes and string
        representations.

        Args:
            target: The error to compare against. Can be an Error instance
                or an exception that wraps an Error via __cause__.

        Returns:
            True if this error is equivalent to target.
        """
        if not isinstance(target, Error):
            # Check if target wraps an Error via exception chaining
            if hasattr(target, "__cause__") and isinstance(
                target.__cause__, Error
            ):
                target = target.__cause__
            else:
                return False
        if self is target:
            return True
        if self.status != target.status:
            return False
        return str(self) == str(target)


def parse_error_response(response) -> Error:
    """Parse an API error from an HTTP response.

    Reads the response body, attempts JSON deserialization into an Error
    structure, and falls back to raw text with HTML unescaping on failure.
    Sets the HTTP status code on the resulting Error regardless of parse
    outcome.

    Mirrors Go domainownership.Error() method (errors.go lines 37-60).

    Args:
        response: An HTTP response object (requests.Response) with
            ``text``, ``status_code`` attributes.

    Returns:
        An Error instance populated from the response.
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
        error.type = data.get("type", "")
        error.title = data.get("title", "")
        error.detail = data.get("detail", "")
        error.instance = data.get("instance", "")
        error.problem_id = data.get("problemId", "")
        raw_errors = data.get("errors", [])
        if raw_errors:
            error.errors = [
                ErrorDetail(
                    type=e.get("type", ""),
                    title=e.get("title", ""),
                    detail=e.get("detail", ""),
                    problem_id=e.get("problemId", ""),
                    field=e.get("field", ""),
                )
                for e in raw_errors
            ]
    except (json.JSONDecodeError, AttributeError) as err:
        logger.error("could not unmarshal API error: %s", err)
        error.title = (
            "Failed to unmarshal error body. "
            "Domain Ownership Manager API failed. "
            "Check details for more information."
        )
        error.detail = unescape_content(body)

    error.status = response.status_code
    return error


# ---------------------------------------------------------------------------
# Sentinel error constants
# ---------------------------------------------------------------------------
# These are string constants matching Go errors.New() values used as sentinel
# error identifiers. They enable consistent error identification across the
# service client without relying on error message parsing.

# From domainownership.go line 12
ErrStructValidation = "struct validation"

# From domains.go lines 480-510
ErrAddDomains = "add domains"
ErrDeleteDomain = "delete domain"
ErrDeleteDomains = "delete domains"
ErrListDomains = "list domains"
ErrGetDomain = "get domain"
ErrSearchDomains = "search domains"
ErrDomainEmpty = "cannot be blank"
ErrDomainTooLong = "cannot exceed 200 characters"
ErrDomainInvalidFmt = "invalid name format"
ERR_DOMAIN_NAME_VALIDATION_HINT = (
    "Domain must: not be empty, not begin with '*', "
    "not begin or end with whitespace, "
    "and not exceed 200 characters"
)

# From validations.go lines 71-80
ErrInvalidateDomain = "invalidate domain"
ErrInvalidateDomains = "invalidate domains"
ErrValidateDomains = "validate domains"
