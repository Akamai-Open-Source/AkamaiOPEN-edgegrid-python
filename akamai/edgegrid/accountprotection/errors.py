"""Error types for the Account Protection API client.

Defines the service-specific Error class for parsing API error responses
and the ErrStructValidation sentinel for validation failures.

Mirrors Go pkg/accountprotection/errors.go.
"""

from dataclasses import dataclass, field


class ErrStructValidation(Exception):
    """Raised when request struct validation fails.

    Mirrors Go's ErrStructValidation sentinel error from account_protection.go
    (line 13): var ErrStructValidation = errors.New("struct validation")

    Attributes:
        message: Human-readable validation failure description.
    """

    def __init__(self, message: str = "struct validation"):
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        """Return the validation error message."""
        return self.message


@dataclass
class Error(Exception):
    """Account Protection API error.

    Parses error responses from the Account Protection API endpoints.
    Mirrors Go pkg/accountprotection Error struct (errors.go lines 14-31).

    Fields match Go struct JSON tags exactly:
        type       -> type       (str, json:"type")
        title      -> title      (str, json:"title")
        detail     -> detail     (str, json:"detail")
        errors     -> errors     (list[Error], json:"errors,omitempty")
        status_code -> status_code (int, json:"status,omitempty")
    """

    type: str = ""
    title: str = ""
    detail: str = ""
    errors: list = field(default_factory=list)
    status_code: int = 0

    def __post_init__(self):
        """Initialize the Exception base class with the string representation."""
        Exception.__init__(self, str(self))

    def __str__(self) -> str:
        """Format error as string.

        EXACTLY mirrors Go's Error.Error() method (errors.go lines 60-69):
            'Title: {title}; Type: {type}; Detail: {detail}'

        If nested errors exist, appends child details:
            ': [{detail1}, {detail2} ]'

        Note the space before ']' — this matches Go's strings.Join + " ]" format.
        """
        detail = self.detail
        if self.errors:
            child_details = [err.detail for err in self.errors]
            detail += ": [" + ", ".join(child_details) + " ]"
        return f"Title: {self.title}; Type: {self.type}; Detail: {detail}"

    def is_equivalent(self, target) -> bool:
        """Check equivalence with another Error.

        EXACTLY mirrors Go's Error.Is() method (errors.go lines 73-88):
            1. If target is not an Error, attempt to unwrap it
            2. If self is target (same object), return True
            3. If status codes differ, return False
            4. Compare string representations

        Args:
            target: The error to compare against. Can be an Error instance
                    or an exception wrapping an Error.

        Returns:
            True if the errors are considered equivalent, False otherwise.
        """
        if not isinstance(target, Error):
            # Attempt to unwrap: mirrors Go's errors.As(target, &t)
            # Check __cause__ (raise ... from ...) and __context__ (implicit chaining)
            cause = getattr(target, "__cause__", None)
            if cause is not None and isinstance(cause, Error):
                target = cause
            else:
                context = getattr(target, "__context__", None)
                if context is not None and isinstance(context, Error):
                    target = context
                elif hasattr(target, "args") and target.args:
                    # Check if Error is wrapped as an argument (fmt.Errorf %w equivalent)
                    found = False
                    for arg in target.args:
                        if isinstance(arg, Error):
                            target = arg
                            found = True
                            break
                    if not found:
                        return False
                else:
                    return False

        if self is target:
            return True

        if self.status_code != target.status_code:
            return False

        return str(self) == str(target)
