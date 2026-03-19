"""Error types for the Network Lists API client.

Mirrors Go pkg/networklists/errors.go — defines the service-specific
Error struct and ErrBadRequest sentinel error.
"""

from __future__ import annotations

from dataclasses import dataclass


class ErrBadRequest(Exception):
    """Raised when a required parameter is missing.

    Mirrors Go ``ErrBadRequest = errors.New("missing argument")``.
    """

    def __init__(self, message: str = "missing argument"):
        super().__init__(message)


@dataclass
class Error(Exception):
    """Network Lists API error.

    Mirrors Go ``pkg/networklists.Error`` struct.  Parses error responses
    from the Network Lists API.

    Fields match Go struct JSON tags exactly:

    * type – Error type identifier
    * title – Human-readable error title
    * detail – Detailed error description
    * instance – Error instance identifier (optional)
    * behavior_name – Behavior name context (optional)
    * error_location – Error location context (optional)
    * status_code – HTTP response status code (not serialised to JSON)
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
        """Format error string matching Go's ``Error()`` method exactly.

        Go format::

            Title: %s; Type: %s; Detail: %s
        """
        return f"Title: {self.title}; Type: {self.type}; Detail: {self.detail}"

    def is_equivalent(self, target: Error) -> bool:
        """Check error equivalence, mirroring Go's ``Is()`` method.

        Comparison logic (matching Go exactly):

        1. If *target* is not an ``Error``, return ``False``
        2. If *self* is *target* (same object), return ``True``
        3. If status codes differ, return ``False``
        4. Compare string representations
        """
        if not isinstance(target, Error):
            return False
        if self is target:
            return True
        if self.status_code != target.status_code:
            return False
        return str(self) == str(target)
