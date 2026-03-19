"""Error types and sentinel errors for the mTLS Key Store API."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from akamai.edgegrid.utils import unescape_content

logger = logging.getLogger(__name__)

# Internal type constants matching Go errors.go lines 51-52
_RESOURCE_NOT_FOUND_TYPE = "resource-not-found"
_BAD_REQUEST_TYPE = "bad-request"

# Sentinel error constants use Go-style names to match the Go SDK exactly.
# pylint: disable=invalid-name

# Sentinel error from mtlskeystore.go line 12
ErrStructValidation = "struct validation"

# Sentinel errors from client_certificates.go lines 164-176
ErrListClientCertificates = "list client certificates"
ErrGetClientCertificate = "get client certificate"
ErrCreateClientCertificate = "create client certificate"
ErrPatchClientCertificate = "patch client certificate"

# Sentinel errors from client_certificate_versions.go lines 273-285
ErrRotateClientCertificateVersion = "rotating client certificate version"
ErrListClientCertificateVersions = "fetching client certificate versions"
ErrDeleteClientCertificateVersion = "deleting client certificate version"
ErrUploadClientCertificateVersion = "uploading client certificate version"

# Sentinel error from account_ca_certificates.go line 97
ErrListAccountCACertificates = "list account ca certificates"

# Sentinel errors from errors.go lines 54-61
# NOTE: ErrClientCertificateNotFound has "on the serve" (missing 'r') — verbatim from Go source
ErrClientCertificateNotFound = (
    "the requested resource could not be found on the serve"
)
ErrInvalidClientCertificate = (
    "certificate is either invalid or cannot not be accepted"
)
ErrDuplicateClientCertificate = "certificate with same name already exists"

# pylint: enable=invalid-name


@dataclass
class Error(Exception):  # pylint: disable=too-many-instance-attributes
    """mTLS Key Store API error.

    Represents an RFC 7807 problem detail response from the mTLS Key Store API.
    Mirrors Go ``pkg/mtlskeystore.Error`` struct with all 10 fields.

    Fields without ``omitempty`` in Go (title, type, detail, status,
    problemId, instance) are always serialized to JSON. Fields with
    ``omitempty`` (field, parameter, value, errors) are only serialized
    when non-empty.
    """

    title: str = ""
    type: str = ""
    detail: str = ""
    status: int = 0
    problem_id: str = ""
    instance: str = ""
    field: str = ""
    parameter: str = ""
    value: str = ""
    errors: list[Error] | None = None

    def __str__(self) -> str:
        """Return string representation matching Go's JSON-indented format.

        Produces output identical to Go's ``json.MarshalIndent(e, "", "\\t")``,
        prefixed with ``"API error: \\n"``.
        """
        try:
            error_dict = self._to_dict()
            msg = json.dumps(error_dict, indent="\t")
            return f"API error: \n{msg}"
        except (TypeError, ValueError) as err:
            return f"error marshaling API error: {err} "

    def _to_dict(self) -> dict:
        """Convert to dict with camelCase keys matching Go JSON tags.

        Fields without ``omitempty`` are always included.
        Fields with ``omitempty`` are only included when non-empty.
        Key order matches Go struct field declaration order.
        """
        result = {
            "title": self.title,
            "type": self.type,
            "detail": self.detail,
            "status": self.status,
            "problemId": self.problem_id,
            "instance": self.instance,
        }
        if self.field:
            result["field"] = self.field
        if self.parameter:
            result["parameter"] = self.parameter
        if self.value:
            result["value"] = self.value
        if self.errors:
            # Access within same class hierarchy is intentional
            result["errors"] = [
                e._to_dict() for e in self.errors  # pylint: disable=protected-access
            ]
        return result

    def is_equivalent(self, target) -> bool:  # pylint: disable=too-many-return-statements
        """Check if this error matches a target error or sentinel.

        Mirrors Go ``Error.Is()`` method for sentinel error comparison and
        Error-to-Error comparison by status code and string representation.

        Sentinel matching rules (from errors.go lines 73-93):
        - ``ErrClientCertificateNotFound``: status == 404 AND
          type == "resource-not-found"
        - ``ErrInvalidClientCertificate``: status == 400 AND
          type == "bad-request"
        - ``ErrDuplicateClientCertificate``: status == 400 AND
          type == "bad-request" (same condition as ErrInvalidClientCertificate)

        Args:
            target: A sentinel error string, an Error instance, or None.

        Returns:
            True if this error is equivalent to the target.
        """
        if target is None:
            return False

        # Check string sentinel matching
        if isinstance(target, str):
            if target == ErrClientCertificateNotFound:
                return (self.status == 404
                        and self.type == _RESOURCE_NOT_FOUND_TYPE)
            if target in (ErrInvalidClientCertificate,
                          ErrDuplicateClientCertificate):
                return (self.status == 400
                        and self.type == _BAD_REQUEST_TYPE)
            return False

        # Check Error instance matching
        if not isinstance(target, Error):
            return False

        if self is target:
            return True

        if self.status != target.status:
            return False

        return str(self) == str(target)


def _parse_nested_error(data: dict) -> Error:
    """Parse a nested error from a JSON dictionary.

    Creates an Error instance from a dict with camelCase keys matching
    Go JSON tags. Recursively parses nested errors arrays.

    Args:
        data: Dictionary with error fields using camelCase keys.

    Returns:
        An Error instance populated from the dictionary.
    """
    error = Error()
    error.title = data.get("title", "")
    error.type = data.get("type", "")
    error.detail = data.get("detail", "")
    error.status = data.get("status", 0)
    error.problem_id = data.get("problemId", "")
    error.instance = data.get("instance", "")
    error.field = data.get("field", "")
    error.parameter = data.get("parameter", "")
    error.value = data.get("value", "")
    raw_errors = data.get("errors")
    if raw_errors:
        error.errors = [_parse_nested_error(e) for e in raw_errors]
    return error


def parse_error_response(response) -> Error:
    """Parse an error from the mTLS Key Store API response.

    Reads the response body, attempts JSON parsing for RFC 7807 structure,
    falls back to raw text with HTML unescaping on parse failure. Always
    overrides status from the HTTP response status code.

    Mirrors Go ``mtlskeystore.Error()`` method in errors.go lines 31-49.

    Args:
        response: A ``requests.Response``-like object with ``status_code``
            and ``text`` attributes.

    Returns:
        An Error instance populated from the response.
    """
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
        error.title = data.get("title", "")
        error.type = data.get("type", "")
        error.detail = data.get("detail", "")
        error.status = data.get("status", 0)
        error.problem_id = data.get("problemId", "")
        error.instance = data.get("instance", "")
        error.field = data.get("field", "")
        error.parameter = data.get("parameter", "")
        error.value = data.get("value", "")
        raw_errors = data.get("errors")
        if raw_errors:
            error.errors = [_parse_nested_error(e) for e in raw_errors]
    except (json.JSONDecodeError, AttributeError) as err:
        logger.error("could not unmarshal API error: %s", err)
        error.title = (
            "Failed to unmarshal error body. mTLS Keystore API failed. "
            "Check details for more information."
        )
        error.detail = unescape_content(body)

    error.status = response.status_code
    return error
