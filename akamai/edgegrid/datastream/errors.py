"""Error types and sentinel errors for the DataStream API client.

Mirrors Go ``pkg/datastream/errors.go`` Error and RequestErrors structs,
along with all sentinel error constants from ``ds.go``, ``stream.go``,
``stream_activation.go``, and ``properties.go``.
"""

import json
from dataclasses import dataclass, field


@dataclass
class RequestErrors:
    """Optional error detail entry in the errors array.

    Mirrors Go ``datastream.RequestErrors`` struct (errors.go lines 25-30).
    Each field defaults to an empty string matching Go zero values.
    """

    # pylint: disable=redefined-builtin
    type: str = ""
    title: str = ""
    detail: str = ""
    instance: str = ""


@dataclass
class Error(Exception):
    """DataStream API error response.

    Parses RFC 7807 problem-detail responses from the DataStream2 API.
    Mirrors Go ``datastream.Error`` struct (errors.go lines 15-22).

    Extends ``Exception`` so instances can be raised and caught in
    standard Python exception-handling flows.
    """

    # pylint: disable=redefined-builtin
    type: str = ""
    title: str = ""
    detail: str = ""
    instance: str = ""
    status_code: int = 0
    errors: list[RequestErrors] = field(default_factory=list)

    def __post_init__(self):
        """Initialise the ``Exception`` base with this error's string form."""
        super().__init__(str(self))

    def __str__(self) -> str:
        """Format the error as indented JSON.

        Mirrors Go ``Error.Error()`` (errors.go lines 59-65).
        Output format: ``'API error: \\n{indented_json}'`` where the JSON
        uses tab indentation matching Go's ``json.MarshalIndent``.
        """
        errors_list: list[dict] = []
        for err in self.errors or []:
            err_dict: dict = {"type": err.type, "title": err.title}
            if err.instance:
                err_dict["instance"] = err.instance
            err_dict["detail"] = err.detail
            errors_list.append(err_dict)

        error_dict = {
            "type": self.type,
            "title": self.title,
            "detail": self.detail,
            "instance": self.instance,
            "statusCode": self.status_code,
            "errors": errors_list,
        }
        try:
            msg = json.dumps(error_dict, indent="\t")
            return f"API error: \n{msg}"
        except (TypeError, ValueError) as marshal_err:
            return f"error marshaling API error: {marshal_err}"

    def is_equivalent(self, target) -> bool:
        """Check error equivalence.

        Mirrors Go ``Error.Is()`` (errors.go lines 68-83).
        Comparison order: identity → ``status_code`` → string representation.
        """
        if not isinstance(target, Error):
            return False
        if self is target:
            return True
        if self.status_code != target.status_code:
            return False
        return str(self) == str(target)


# ErrStructValidation is the sentinel value for struct validation failures.
# Mirrors Go: var ErrStructValidation = errors.New("struct validation")
ErrStructValidation = "struct validation"


# ---------------------------------------------------------------------------
# Sentinel error constants
#
# Each constant mirrors the corresponding ``errors.New(...)`` value in Go.
# They are plain strings used for error wrapping and identification.
# ---------------------------------------------------------------------------

# pylint: disable=invalid-name
# Sentinel error names mirror Go's camelCase ``Err*`` convention exactly.

# From stream.go lines 274-285
ErrCreateStream: str = "creating stream"
ErrGetStream: str = "fetching stream information"
ErrUpdateStream: str = "updating stream"
ErrDeleteStream: str = "deleting stream"
ErrListStreams: str = "listing streams"

# From stream_activation.go lines 57-63
ErrActivateStream: str = "activate stream"
ErrDeactivateStream: str = "deactivate stream"
ErrGetActivationHistory: str = "view activation history"

# From properties.go lines 49-53
ErrGetProperties: str = "list properties"
ErrGetDatasetFields: str = "list data set fields"

# pylint: enable=invalid-name
