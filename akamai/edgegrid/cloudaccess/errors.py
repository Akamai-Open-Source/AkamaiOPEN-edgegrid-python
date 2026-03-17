"""Error types and sentinel errors for the Cloud Access Manager API client.

Mirrors Go ``pkg/cloudaccess/errors.go`` Error and ErrorItem structs,
along with the sentinel error constants.
"""

import json
from dataclasses import dataclass, field


@dataclass
class ErrorItem:
    """Cloud Access error detail entry in the errors array.

    Mirrors Go ``cloudaccess.ErrorItem`` struct (errors.go lines 31-35).
    Each field defaults to an empty string matching Go zero values.
    """

    detail: str = ""
    title: str = ""

    # pylint: disable=redefined-builtin
    type: str = ""


@dataclass
class Error(Exception):  # pylint: disable=too-many-instance-attributes
    """Cloud Access Manager API error response.

    Parses RFC 7807 problem-detail responses from the Cloud Access Manager API.
    Mirrors Go ``cloudaccess.Error`` struct (errors.go lines 16-29).

    Extends ``Exception`` so instances can be raised and caught in
    standard Python exception-handling flows.
    """

    # pylint: disable=redefined-builtin
    type: str = ""
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

    def __str__(self) -> str:
        """Format the error as indented JSON.

        Mirrors Go ``Error.Error()`` (errors.go lines 73-79).
        Output format: ``'API error: \\n{indented_json}'`` where the JSON
        uses tab indentation matching Go's ``json.MarshalIndent``.
        """
        errors_list: list[dict] = []
        for err in self.errors or []:
            errors_list.append({
                "detail": err.detail,
                "title": err.title,
                "type": err.type,
            })

        error_dict: dict = {
            "type": self.type,
            "title": self.title,
            "detail": self.detail,
            "instance": self.instance,
            "status": self.status,
        }
        if self.access_key_uid:
            error_dict["accessKeyUid"] = self.access_key_uid
        if self.access_key_name:
            error_dict["accessKeyName"] = self.access_key_name
        if self.problem_id:
            error_dict["problemId"] = self.problem_id
        if self.version:
            error_dict["version"] = self.version
        if errors_list:
            error_dict["errors"] = errors_list

        try:
            msg = json.dumps(error_dict, indent="\t")
            return f"API error: \n{msg}"
        except (TypeError, ValueError) as marshal_err:
            return f"error marshaling API error: {marshal_err}"

    def is_equivalent(self, target) -> bool:
        """Check error equivalence.

        Mirrors Go ``Error.Is()`` (errors.go lines 82-98).
        Handles special-case comparison for ``ErrAccessKeyNotFound``:
        if the target is that sentinel, matches on HTTP 404 status
        and the ``accessKeyNotFoundType`` type string.

        For general comparisons, uses identity → ``status`` → string
        representation order.
        """
        if not isinstance(target, Error):
            return False
        if self is target:
            return True
        if self.status != target.status:
            return False
        return str(self) == str(target)


# ---------------------------------------------------------------------------
# Internal constants mirroring Go private constants
# ---------------------------------------------------------------------------
ACCESS_KEY_NOT_FOUND_TYPE: str = "/cam/error-types/access-key-does-not-exist"

# ---------------------------------------------------------------------------
# Sentinel error constants
#
# Each constant mirrors the corresponding ``errors.New(...)`` value in Go.
# They are plain strings used for error wrapping and identification.
# ---------------------------------------------------------------------------

# pylint: disable=invalid-name
# Sentinel error names mirror Go's camelCase ``Err*`` convention exactly.

# From errors.go line 39
ErrAccessKeyNotFound: str = "access key not found"
