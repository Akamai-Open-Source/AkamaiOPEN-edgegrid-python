# pylint: disable=too-many-instance-attributes,too-many-branches
"""Imaging API error types and error response parsing"""

import json
import logging
from dataclasses import dataclass

from akamai.edgegrid.utils import unescape_content

logger = logging.getLogger(__name__)


@dataclass
class Error(Exception):
    """Image & Video Manager API error.

    Mirrors Go imaging.Error struct with RFC 7807 problem detail fields
    plus Imaging-specific extension fields.
    """

    type: str = ""
    title: str = ""
    detail: str = ""
    instance: str = ""
    status: int = 0
    problem_id: str = ""
    request_id: str = ""
    illegal_value: str = ""
    parameter_name: str = ""
    extension_fields: dict[str, str] | None = None
    method: str = ""
    server_ip: str = ""
    client_ip: str = ""
    request_time: str = ""
    authz_realm: str = ""

    def __str__(self) -> str:
        """Format error as indented JSON, matching Go's Error() method.

        Mirrors Go json.MarshalIndent behavior with omitempty semantics:
        only non-zero, non-empty fields are included in the JSON output.
        """
        error_dict: dict = {}
        if self.type:
            error_dict["type"] = self.type
        if self.title:
            error_dict["title"] = self.title
        if self.detail:
            error_dict["detail"] = self.detail
        if self.instance:
            error_dict["instance"] = self.instance
        if self.status:
            error_dict["status"] = self.status
        if self.problem_id:
            error_dict["problemId"] = self.problem_id
        if self.request_id:
            error_dict["requestId"] = self.request_id
        if self.illegal_value:
            error_dict["illegalValue"] = self.illegal_value
        if self.parameter_name:
            error_dict["parameterName"] = self.parameter_name
        if self.extension_fields:
            error_dict["extensionFields"] = self.extension_fields
        if self.method:
            error_dict["method"] = self.method
        if self.server_ip:
            error_dict["serverIp"] = self.server_ip
        if self.client_ip:
            error_dict["clientIp"] = self.client_ip
        if self.request_time:
            error_dict["requestTime"] = self.request_time
        if self.authz_realm:
            error_dict["authzRealm"] = self.authz_realm
        try:
            msg = json.dumps(error_dict, indent="\t")
            return f"API error: \n{msg}"
        except (TypeError, ValueError) as err:
            return f"error marshaling API error: {err}"

    def is_equivalent(self, other: "Error") -> bool:
        """Check if this error is equivalent to another error.

        Mirrors Go Error.Is() method: compares status codes first,
        then falls back to full string representation comparison.

        Args:
            other: The target error to compare against.

        Returns:
            True if the errors are considered equivalent.
        """
        if not isinstance(other, Error):
            return False
        if self is other:
            return True
        if self.status != other.status:
            return False
        return str(self) == str(other)


def parse_error_response(response) -> Error:
    """Parse an Imaging API error from an HTTP response.

    Mirrors Go imaging.Error() method:
    1. Read response body text.
    2. Attempt JSON unmarshal into Error fields.
    3. On unmarshal failure: set title to a specific message and
       set detail to the unescaped body content.
    4. Always set status from response status code on unmarshal failure.

    Args:
        response: An HTTP response object (requests.Response) with
            status_code and text attributes.

    Returns:
        An Error instance populated from the response body.
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
        error.type = data.get("type", "")
        error.title = data.get("title", "")
        error.detail = data.get("detail", "")
        error.instance = data.get("instance", "")
        error.status = data.get("status", 0)
        error.problem_id = data.get("problemId", "")
        error.request_id = data.get("requestId", "")
        error.illegal_value = data.get("illegalValue", "")
        error.parameter_name = data.get("parameterName", "")
        error.extension_fields = data.get("extensionFields")
        error.method = data.get("method", "")
        error.server_ip = data.get("serverIp", "")
        error.client_ip = data.get("clientIp", "")
        error.request_time = data.get("requestTime", "")
        error.authz_realm = data.get("authzRealm", "")
    except (json.JSONDecodeError, AttributeError) as err:
        logger.error("could not unmarshal API error: %s", err)
        error.title = (
            "Failed to unmarshal error body. Image & Video Manager API failed."
            " Check details for more information."
        )
        error.detail = unescape_content(body)
        error.status = response.status_code

    return error
