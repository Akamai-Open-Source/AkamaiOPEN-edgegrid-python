"""Sentinel errors and error types for the IAM API client.

Mirrors Go pkg/iam/errors.go — defines the IAMError class (RFC 7807 response
parsing with IAM-specific fields), ErrStructValidation exception, error
response parser functions, and all sentinel error constants from the IAM
package.
"""

import json
import logging
from dataclasses import dataclass

from akamai.edgegrid.utils import unescape_content

logger = logging.getLogger(__name__)


@dataclass
class IAMError(Exception):  # pylint: disable=too-many-instance-attributes
    """IAM API error with additional fields specific to IAM responses.

    Mirrors Go pkg/iam.Error struct which extends the base error pattern
    with BehaviorName, ErrorLocation, Warnings, and HTTPStatus fields.

    Fields map 1:1 to Go Error struct JSON tags:
        Type          -> type
        Title         -> title
        Detail        -> detail
        Instance      -> instance      (omitempty)
        BehaviorName  -> behavior_name  (omitempty)
        ErrorLocation -> error_location (omitempty)
        StatusCode    -> status_code    (omitempty)
        Errors        -> errors         (omitempty, json.RawMessage)
        Warnings      -> warnings       (omitempty, json.RawMessage)
        HTTPStatus    -> http_status    (omitempty)
    """

    type: str = ""  # pylint: disable=redefined-builtin
    title: str = ""
    detail: str = ""
    instance: str = ""
    behavior_name: str = ""
    error_location: str = ""
    status_code: int = 0
    errors: list | dict | str | None = None
    warnings: list | dict | str | None = None
    http_status: int = 0

    def __str__(self) -> str:
        """Format error as indented JSON, matching Go's Error() method.

        Produces output identical to Go's json.MarshalIndent with tab
        indentation, prefixed with 'API error: \\n'. Only includes
        non-zero/non-empty fields beyond the three required fields
        (type, title, detail), matching Go's omitempty semantics.
        """
        error_dict: dict = {
            "type": self.type,
            "title": self.title,
            "detail": self.detail,
        }
        if self.instance:
            error_dict["instance"] = self.instance
        if self.behavior_name:
            error_dict["behaviorName"] = self.behavior_name
        if self.error_location:
            error_dict["errorLocation"] = self.error_location
        if self.status_code:
            error_dict["statusCode"] = self.status_code
        if self.errors is not None:
            error_dict["errors"] = self.errors
        if self.warnings is not None:
            error_dict["warnings"] = self.warnings
        if self.http_status:
            error_dict["httpStatus"] = self.http_status
        try:
            msg = json.dumps(error_dict, indent="\t")
            return f"API error: \n{msg}"
        except (TypeError, ValueError) as err:
            return f"error marshaling API error: {err}"

    def is_equivalent(self, other: 'IAMError') -> bool:
        """Check if this error is equivalent to another IAMError.

        Mirrors Go's Error.Is() method: compare by status_code first,
        then by full string representation.

        Args:
            other: Another IAMError instance to compare against.

        Returns:
            True if the errors are semantically equivalent.
        """
        if not isinstance(other, IAMError):
            return False
        if self is other:
            return True
        if self.status_code != other.status_code:
            return False
        return str(self) == str(other)


# ErrStructValidation is the sentinel value for struct validation failures.
# Mirrors Go: var ErrStructValidation = errors.New("struct validation")
ErrStructValidation = "struct validation"  # pylint: disable=invalid-name


def parse_iam_error_response(response) -> IAMError:
    """Parse an IAM API error from an HTTP response.

    Reads the response body, attempts JSON parsing for RFC 7807 structure,
    falls back to raw text with HTML unescaping on parse failure.

    Mirrors Go pkg/iam errors.go Error() method (lines 30-53):
      1. Read response body
      2. Attempt json.Unmarshal into Error struct
      3. On failure, set title to unmarshal failure message and detail
         to UnescapeContent(body)
      4. Set StatusCode from HTTP response status

    Args:
        response: An HTTP response object with .text and .status_code
                  attributes (e.g., requests.Response).

    Returns:
        IAMError populated from the response body.
    """
    error = IAMError()

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
        error.status_code = data.get("statusCode", 0)
        error.errors = data.get("errors")
        error.warnings = data.get("warnings")
        error.http_status = data.get("httpStatus", 0)
    except (json.JSONDecodeError, AttributeError) as err:
        logger.error("could not unmarshal API error: %s", err)
        error.title = (
            "Failed to unmarshal error body. IAM API failed. "
            "Check details for more information."
        )
        error.detail = unescape_content(body)

    error.status_code = response.status_code

    return error


def create_error_from_response(response, sentinel_msg: str) -> IAMError:
    """Create an IAMError from response, wrapping with sentinel error message.

    Mirrors Go pattern: fmt.Errorf("%s: %w", ErrXxx, i.Error(resp))
    Parses the response into an IAMError and prefixes the title with
    the sentinel error message.

    Args:
        response: An HTTP response object with .text and .status_code
                  attributes (e.g., requests.Response).
        sentinel_msg: The sentinel error string to prefix (e.g.,
                      ErrGetAPIClient = "get api client").

    Returns:
        IAMError with title prefixed by the sentinel message.
    """
    error = parse_iam_error_response(response)
    if error.title:
        error.title = f"{sentinel_msg}: {error.title}"
    else:
        error.title = sentinel_msg
    return error


# ---------------------------------------------------------------------------
# Sentinel error constants — VERBATIM from Go source errors.New("...")
# These string values MUST match Go IAM package exactly.
# ---------------------------------------------------------------------------

# pylint: disable=invalid-name

# From api_clients.go
ErrLockAPIClient: str = "lock api client"
ErrUnlockAPIClient: str = "unlock api client"
ErrListAPIClients: str = "list api clients"
ErrGetAPIClient: str = "get api client"
ErrCreateAPIClient: str = "create api client"
ErrUpdateAPIClient: str = "update api client"
ErrDeleteAPIClient: str = "delete api client"

# From api_clients_credentials.go
ErrCreateCredential: str = "create credential"
ErrListCredentials: str = "list credentials"
ErrGetCredential: str = "get credential"
ErrUpdateCredential: str = "update credential"
ErrDeleteCredential: str = "delete credential"
ErrDeactivateCredential: str = "deactivate credential"
ErrDeactivateCredentials: str = "deactivate credentials"

# From blocked_properties.go
ErrListBlockedProperties: str = "list blocked properties"
ErrUpdateBlockedProperties: str = "update blocked properties"

# From cidr.go
ErrListCIDRBlocks: str = "list CIDR blocks"
ErrCreateCIDRBlock: str = "create CIDR block"
ErrGetCIDRBlock: str = "get CIDR block"
ErrUpdateCIDRBlock: str = "update CIDR block"
ErrDeleteCIDRBlock: str = "delete CIDR block"
ErrValidateCIDRBlock: str = "validate CIDR block"

# From groups.go
ErrCreateGroup: str = "create group"
ErrGetGroup: str = "get group"
ErrListAffectedUsers: str = "list affected users"
ErrListGroups: str = "list groups"
ErrRemoveGroup: str = "remove group"
ErrUpdateGroupName: str = "update group name"
ErrMoveGroup: str = "move group"

# From helper.go
ErrListAllowedCPCodes: str = "list allowed CP codes"
ErrListAuthorizedUsers: str = "list authorized users"
ErrListAllowedAPIs: str = "list allowed APIs"
ErrAccessibleGroups: str = "list accessible groups"

# From ip_allowlist.go — Go source uses lowercase "ip"
ErrDisableIPAllowlist: str = "disable ip allowlist"
ErrEnableIPAllowlist: str = "enable ip allowlist"
ErrGetIPAllowlistStatus: str = "get ip allowlist status"

# From properties.go — Go source uses "map property by id/name"
ErrListProperties: str = "list properties"
ErrListUsersForProperty: str = "list users for property"
ErrGetProperty: str = "get property"
ErrMoveProperty: str = "move property"
ErrMapPropertyIDToName: str = "map property by id"
ErrMapPropertyNameToID: str = "map property by name"
ErrNoProperty: str = "no such property"
ErrBlockUsers: str = "block users"

# From roles.go — Go uses "a role" for CRUD operations
ErrCreateRole: str = "create a role"
ErrGetRole: str = "get a role"
ErrUpdateRole: str = "update a role"
ErrDeleteRole: str = "delete a role"
ErrListRoles: str = "list roles"
ErrListGrantableRoles: str = "list grantable roles"

# From support.go
ErrGetPasswordPolicy: str = "get password policy"
ErrListProducts: str = "list products"
ErrListStates: str = "list states"
ErrListTimeoutPolicies: str = "list timeout policies"
ErrListAccountSwitchKeys: str = "list account switch keys"
ErrSupportedContactTypes: str = "supported contact types"
ErrSupportedCountries: str = "supported countries"
ErrSupportedLanguages: str = "supported languages"
ErrSupportedTimezones: str = "supported timezones"

# From user.go
ErrCreateUser: str = "create user"
ErrGetUser: str = "get user"
ErrListUsers: str = "list users"
ErrRemoveUser: str = "remove user"
ErrUpdateUserAuthGrants: str = "update user auth grants"
ErrUpdateUserInfo: str = "update user info"
ErrUpdateUserNotifications: str = "update user notifications"
ErrUpdateMFA: str = "update user's authentication method"
ErrResetMFA: str = "reset user's authentication method"

# From user_lock.go
ErrLockUser: str = "lock user"
ErrUnlockUser: str = "unlock user"

# From user_password.go
ErrResetUserPassword: str = "reset user password"
ErrSetUserPassword: str = "set user password"
