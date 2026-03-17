"""Request validation functions for the IAM service client."""

import ipaddress
import re

from akamai.edgegrid.validation import parse_validation_errors
from akamai.edgegrid.iam.errors import ErrStructValidation

# Email regex for validating email format, mirrors Go ozzo-validation is.EmailFormat.
_EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)


def _validate_cidr_format(value):
    """Validate CIDR block notation using ipaddress.ip_network().

    Mirrors Go net.ParseCIDR() validation.

    Args:
        value: CIDR block string to validate.

    Returns:
        Error message string if invalid, None if valid.
    """
    try:
        ipaddress.ip_network(value, strict=False)
        return None
    except ValueError as err:
        return str(err)


def _validate_email_format(value):
    """Validate email address format.

    Mirrors Go ozzo-validation is.EmailFormat rule.

    Args:
        value: Email string to validate.

    Returns:
        Error message string if invalid, None if valid.
    """
    if not _EMAIL_REGEX.match(value):
        return "must be a valid email address"
    return None


# =====================================================================
# Enum validators — return error string or None
# =====================================================================


def validate_client_type(value):
    """Validate ClientType enum value.

    Valid values: CLIENT, SERVICE_ACCOUNT, USER_CLIENT.
    """
    valid = ("CLIENT", "SERVICE_ACCOUNT", "USER_CLIENT")
    if value not in valid:
        return (
            f"value '{value}' is invalid. Must be one of: "
            "'CLIENT', 'SERVICE_ACCOUNT' or 'USER_CLIENT'"
        )
    return None


def validate_credential_status(value):
    """Validate CredentialStatus enum value.

    Valid values: ACTIVE, INACTIVE, DELETED.
    """
    valid = ("ACTIVE", "INACTIVE", "DELETED")
    if value not in valid:
        return (
            f"value '{value}' is invalid. Must be one of: "
            "'ACTIVE', 'INACTIVE' or 'DELETED'"
        )
    return None


def validate_property_user_type(value):
    """Validate PropertyUserType enum value.

    Valid values: all, assigned, blocked.
    """
    valid = ("all", "assigned", "blocked")
    if value not in valid:
        return (
            f"value '{value}' is invalid. Must be one of: "
            "'all', 'assigned' or 'blocked'"
        )
    return None


def validate_authentication(value):
    """Validate Authentication enum value.

    Valid values: MFA, TFA, NONE.
    """
    valid = ("MFA", "TFA", "NONE")
    if value not in valid:
        return (
            f"value '{value}' is invalid. Must be one of: "
            "'MFA', 'TFA' or 'NONE'"
        )
    return None


# =====================================================================
# API Clients validation (api_clients.go)
# =====================================================================


def validate_unlock_api_client_request(request):
    """Validate UnlockAPIClientRequest fields."""
    errors = {}
    if not request.client_id:
        errors["ClientID"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_create_api_client_request(request):
    """Validate CreateAPIClientRequest fields."""
    errors = {}
    api_access_err = validate_api_access_request(request.api_access)
    if api_access_err:
        errors["APIAccess"] = api_access_err
    if request.authorized_users is None:
        errors["AuthorizedUsers"] = "cannot be blank"
    elif len(request.authorized_users) < 1:
        errors["AuthorizedUsers"] = "the length must be no less than 1"
    if not request.client_type:
        errors["ClientType"] = "cannot be blank"
    else:
        ct_err = validate_client_type(request.client_type)
        if ct_err:
            errors["ClientType"] = ct_err
    group_access_err = validate_group_access_request(request.group_access)
    if group_access_err:
        errors["GroupAccess"] = group_access_err
    if request.purge_options is not None:
        purge_err = validate_purge_options(request.purge_options)
        if purge_err:
            errors["PurgeOptions"] = purge_err
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_api_access_request(access):
    """Validate APIAccessRequest fields (nested, Filter pattern).

    When AllAccessibleAPIs is false, APIs list is required.
    """
    errors = {}
    if not access.all_accessible_apis:
        if access.apis is None:
            errors["APIs"] = "cannot be blank"
    return errors if errors else None


def validate_api_request_item(item):
    """Validate APIRequestItem fields (nested, Filter pattern).

    AccessLevel must be a valid enum; APIID is required.
    """
    errors = {}
    if not item.access_level:
        errors["AccessLevel"] = "cannot be blank"
    else:
        valid_levels = (
            "READ-ONLY", "READ-WRITE", "READ",
            "CREDENTIAL-READ-ONLY", "CREDENTIAL-READ-WRITE",
        )
        if item.access_level not in valid_levels:
            errors["AccessLevel"] = (
                f"value '{item.access_level}' is invalid. Must be one of: "
                "'READ-ONLY', 'READ-WRITE', 'READ', "
                "'CREDENTIAL-READ-ONLY' or 'CREDENTIAL-READ-WRITE'"
            )
    if not item.api_id:
        errors["APIID"] = "cannot be blank"
    return errors if errors else None


def validate_group_access_request(access):
    """Validate GroupAccessRequest fields (nested, Filter pattern).

    When CloneAuthorizedUserGroups is false, Groups list is required.
    """
    errors = {}
    if not access.clone_authorized_user_groups:
        if access.groups is None:
            errors["Groups"] = "cannot be blank"
    return errors if errors else None


def validate_client_group_request_item(group):
    """Validate ClientGroupRequestItem fields (nested, Filter pattern)."""
    errors = {}
    if not group.group_id:
        errors["GroupID"] = "cannot be blank"
    if not group.role_id:
        errors["RoleID"] = "cannot be blank"
    return errors if errors else None


def validate_update_api_client_request(request):
    """Validate UpdateAPIClientRequest fields."""
    errors = {}
    if request.body is None:
        errors["Body"] = "cannot be blank"
    else:
        body_err = validate_update_api_client_request_body(request.body)
        if body_err:
            errors["Body"] = body_err
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_update_api_client_request_body(body):
    """Validate UpdateAPIClientRequestBody fields (nested, Filter pattern)."""
    errors = {}
    if not body.client_name:
        errors["ClientName"] = "cannot be blank"
    api_access_err = validate_api_access_request(body.api_access)
    if api_access_err:
        errors["APIAccess"] = api_access_err
    if body.authorized_users is None:
        errors["AuthorizedUsers"] = "cannot be blank"
    elif len(body.authorized_users) < 1:
        errors["AuthorizedUsers"] = "the length must be no less than 1"
    if not body.client_type:
        errors["ClientType"] = "cannot be blank"
    else:
        ct_err = validate_client_type(body.client_type)
        if ct_err:
            errors["ClientType"] = ct_err
    group_access_err = validate_group_access_request(body.group_access)
    if group_access_err:
        errors["GroupAccess"] = group_access_err
    if body.purge_options is not None:
        purge_err = validate_purge_options(body.purge_options)
        if purge_err:
            errors["PurgeOptions"] = purge_err
    return errors if errors else None


def validate_purge_options(options):
    """Validate PurgeOptions fields (nested, Filter pattern)."""
    errors = {}
    if options.cp_code_access is not None:
        cp_err = validate_cp_code_access(options.cp_code_access)
        if cp_err:
            errors["CPCodeAccess"] = cp_err
    return errors if errors else None


def validate_cp_code_access(access):
    """Validate CPCodeAccess fields (nested, Filter pattern).

    When AllCurrentAndNewCPCodes is false, CPCodes must not be None.
    """
    errors = {}
    if not access.all_current_and_new_cp_codes:
        if access.cp_codes is None:
            errors["CPCodes"] = "is required"
    return errors if errors else None


# =====================================================================
# API Client Credentials validation (api_clients_credentials.go)
# =====================================================================


def validate_get_credential_request(request):
    """Validate GetCredentialRequest fields."""
    errors = {}
    if not request.credential_id:
        errors["CredentialID"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_update_credential_request(request):
    """Validate UpdateCredentialRequest fields."""
    errors = {}
    if not request.credential_id:
        errors["CredentialID"] = "cannot be blank"
    if request.body is None:
        errors["Body"] = "cannot be blank"
    else:
        body_err = validate_update_credential_request_body(request.body)
        if body_err:
            errors["Body"] = body_err
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_update_credential_request_body(body):
    """Validate UpdateCredentialRequestBody fields (nested, Filter pattern)."""
    errors = {}
    if not body.expires_on:
        errors["ExpiresOn"] = "cannot be blank"
    if not body.status:
        errors["Status"] = "cannot be blank"
    else:
        status_err = validate_credential_status(body.status)
        if status_err:
            errors["Status"] = status_err
    return errors if errors else None


def validate_delete_credential_request(request):
    """Validate DeleteCredentialRequest fields."""
    errors = {}
    if not request.credential_id:
        errors["CredentialID"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_deactivate_credential_request(request):
    """Validate DeactivateCredentialRequest fields."""
    errors = {}
    if not request.credential_id:
        errors["CredentialID"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


# =====================================================================
# Blocked Properties validation (blocked_properties.go)
# =====================================================================


def validate_list_blocked_properties_request(request):
    """Validate ListBlockedPropertiesRequest fields."""
    errors = {}
    if not request.identity_id:
        errors["IdentityID"] = "cannot be blank"
    if not request.group_id:
        errors["GroupID"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_update_blocked_properties_request(request):
    """Validate UpdateBlockedPropertiesRequest fields."""
    errors = {}
    if not request.identity_id:
        errors["IdentityID"] = "cannot be blank"
    if not request.group_id:
        errors["GroupID"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


# =====================================================================
# CIDR validation (cidr.go)
# =====================================================================


def validate_create_cidr_block_request(request):
    """Validate CreateCIDRBlockRequest fields.

    CIDRBlock must be non-empty and valid CIDR notation.
    """
    errors = {}
    if not request.cidr_block:
        errors["CIDRBlock"] = "cannot be blank"
    else:
        cidr_err = _validate_cidr_format(request.cidr_block)
        if cidr_err:
            errors["CIDRBlock"] = cidr_err
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_get_cidr_block_request(request):
    """Validate GetCIDRBlockRequest fields."""
    errors = {}
    if not request.cidr_block_id:
        errors["CIDRBlockID"] = "cannot be blank"
    elif request.cidr_block_id < 1:
        errors["CIDRBlockID"] = "must be no less than 1"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_update_cidr_block_request(request):
    """Validate UpdateCIDRBlockRequest fields."""
    errors = {}
    if not request.cidr_block_id:
        errors["CIDRBlockID"] = "cannot be blank"
    elif request.cidr_block_id < 1:
        errors["CIDRBlockID"] = "must be no less than 1"
    if request.body is None:
        errors["Body"] = "cannot be blank"
    else:
        body_err = validate_update_cidr_block_request_body(request.body)
        if body_err:
            errors["Body"] = body_err
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_update_cidr_block_request_body(body):
    """Validate UpdateCIDRBlockRequestBody fields (nested, Filter pattern).

    CIDRBlock must be non-empty and valid CIDR notation.
    """
    errors = {}
    if not body.cidr_block:
        errors["CIDRBlock"] = "cannot be blank"
    else:
        cidr_err = _validate_cidr_format(body.cidr_block)
        if cidr_err:
            errors["CIDRBlock"] = cidr_err
    return errors if errors else None


def validate_delete_cidr_block_request(request):
    """Validate DeleteCIDRBlockRequest fields."""
    errors = {}
    if not request.cidr_block_id:
        errors["CIDRBlockID"] = "cannot be blank"
    elif request.cidr_block_id < 1:
        errors["CIDRBlockID"] = "must be no less than 1"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_validate_cidr_block_request(request):
    """Validate ValidateCIDRBlockRequest fields.

    CIDRBlock must be non-empty and valid CIDR notation.
    """
    errors = {}
    if not request.cidr_block:
        errors["CIDRBlock"] = "cannot be blank"
    else:
        cidr_err = _validate_cidr_format(request.cidr_block)
        if cidr_err:
            errors["CIDRBlock"] = cidr_err
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


# =====================================================================
# Groups validation (groups.go)
# =====================================================================


def validate_get_group_request(request):
    """Validate GetGroupRequest fields."""
    errors = {}
    if not request.group_id:
        errors["GroupID"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_group_request(request):
    """Validate GroupRequest fields (nested, Filter pattern)."""
    errors = {}
    if not request.group_id:
        errors["GroupID"] = "cannot be blank"
    if not request.group_name:
        errors["GroupName"] = "cannot be blank"
    return errors if errors else None


def validate_move_group_request(request):
    """Validate MoveGroupRequest fields."""
    errors = {}
    if not request.destination_group_id:
        errors["DestinationGroupID"] = "cannot be blank"
    if not request.source_group_id:
        errors["SourceGroupID"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_list_affected_users_request(request):
    """Validate ListAffectedUsersRequest fields.

    UserType is optional but must be lostAccess or gainAccess if set.
    """
    errors = {}
    if not request.destination_group_id:
        errors["DestinationGroupID"] = "cannot be blank"
    if not request.source_group_id:
        errors["SourceGroupID"] = "cannot be blank"
    if request.user_type:
        valid_types = ("lostAccess", "gainAccess")
        if request.user_type not in valid_types:
            errors["UserType"] = "must be a valid value"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_remove_group_request(request):
    """Validate RemoveGroupRequest fields."""
    errors = {}
    if not request.group_id:
        errors["GroupID"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


# =====================================================================
# Helper validation (helper.go)
# =====================================================================


def validate_list_allowed_cp_codes_request(request):
    """Validate ListAllowedCPCodesRequest fields."""
    errors = {}
    if not request.user_name:
        errors["UserName"] = "cannot be blank"
    if request.body is None:
        errors["Body"] = "cannot be blank"
    else:
        body_err = validate_list_allowed_cp_codes_request_body(request.body)
        if body_err:
            errors["Body"] = body_err
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_list_allowed_cp_codes_request_body(body):
    """Validate ListAllowedCPCodesRequestBody fields (nested, Filter pattern).

    Groups are required only when ClientType is SERVICE_ACCOUNT.
    """
    errors = {}
    if not body.client_type:
        errors["ClientType"] = "cannot be blank"
    else:
        valid = ("CLIENT", "USER_CLIENT", "SERVICE_ACCOUNT")
        if body.client_type not in valid:
            errors["ClientType"] = (
                f"value '{body.client_type}' is invalid. "
                "Must be one of: 'CLIENT' or 'USER_CLIENT' "
                "or 'SERVICE_ACCOUNT'"
            )
    if body.client_type == "SERVICE_ACCOUNT":
        if not body.groups:
            errors["Groups"] = "cannot be blank"
    return errors if errors else None


def validate_list_allowed_apis_request(request):
    """Validate ListAllowedAPIsRequest fields.

    ClientType is optional but must be a valid enum if provided.
    """
    errors = {}
    if not request.user_name:
        errors["UserName"] = "cannot be blank"
    if request.client_type:
        valid = ("CLIENT", "USER_CLIENT", "SERVICE_ACCOUNT")
        if request.client_type not in valid:
            errors["ClientType"] = (
                f"value '{request.client_type}' is invalid. "
                "Must be one of: 'CLIENT' or 'USER_CLIENT' "
                "or 'SERVICE_ACCOUNT'"
            )
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_list_accessible_groups_request(request):
    """Validate ListAccessibleGroupsRequest fields."""
    errors = {}
    if not request.user_name:
        errors["UserName"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


# =====================================================================
# Properties validation (properties.go)
# =====================================================================


def validate_list_users_for_property_request(request):
    """Validate ListUsersForPropertyRequest fields.

    UserType validation is always applied (direct call, not skippable).
    """
    errors = {}
    if not request.property_id:
        errors["PropertyID"] = "cannot be blank"
    errors["UserType"] = validate_property_user_type(request.user_type)
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_get_property_request(request):
    """Validate GetPropertyRequest fields."""
    errors = {}
    if not request.property_id:
        errors["PropertyID"] = "cannot be blank"
    if not request.group_id:
        errors["GroupID"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_map_property_id_to_name_request(request):
    """Validate MapPropertyIDToNameRequest fields."""
    errors = {}
    if not request.property_id:
        errors["PropertyID"] = "cannot be blank"
    if not request.group_id:
        errors["GroupID"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_move_property_request(request):
    """Validate MovePropertyRequest fields."""
    errors = {}
    if not request.property_id:
        errors["PropertyID"] = "cannot be blank"
    if request.body is None:
        errors["Body"] = "cannot be blank"
    else:
        body_err = validate_move_property_request_body(request.body)
        if body_err:
            errors["Body"] = body_err
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_move_property_request_body(body):
    """Validate MovePropertyRequestBody fields (nested, Filter pattern)."""
    errors = {}
    if not body.destination_group_id:
        errors["DestinationGroupID"] = "cannot be blank"
    if not body.source_group_id:
        errors["SourceGroupID"] = "cannot be blank"
    return errors if errors else None


def validate_block_users_request(request):
    """Validate BlockUsersRequest fields."""
    errors = {}
    if not request.property_id:
        errors["PropertyID"] = "cannot be blank"
    if request.body is None:
        errors["Body"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_block_user_item(item):
    """Validate BlockUserItem fields.

    Uses ParseValidationErrors pattern (top-level, raises).
    """
    errors = {}
    if not item.ui_identity_id:
        errors["UIIdentityID"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


# =====================================================================
# Roles validation (roles.go)
# =====================================================================


def validate_create_role_request(request):
    """Validate CreateRoleRequest fields."""
    errors = {}
    if not request.name:
        errors["Name"] = "cannot be blank"
    if not request.description:
        errors["Description"] = "cannot be blank"
    if request.granted_roles is None:
        errors["GrantedRoles"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_get_role_request(request):
    """Validate GetRoleRequest fields."""
    errors = {}
    if not request.id:
        errors["ID"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_update_role_request(request):
    """Validate UpdateRoleRequest fields."""
    errors = {}
    if not request.id:
        errors["ID"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_delete_role_request(request):
    """Validate DeleteRoleRequest fields."""
    errors = {}
    if not request.id:
        errors["ID"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


# =====================================================================
# Support validation (support.go)
# =====================================================================


def validate_list_states_request(request):
    """Validate ListStatesRequest fields."""
    errors = {}
    if not request.country:
        errors["Country"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


# =====================================================================
# User validation (user.go)
# =====================================================================


def validate_auth_grant(grant):
    """Validate AuthGrant fields.

    Uses ParseValidationErrors pattern (top-level, raises).
    """
    errors = {}
    if not grant.group_id:
        errors["GroupID"] = "cannot be blank"
    if grant.role_id is None:
        errors["RoleID"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_create_user_request(request):
    """Validate CreateUserRequest fields.

    Email must be valid format. AdditionalAuthentication is an enum.
    """
    errors = {}
    if not request.country:
        errors["Country"] = "cannot be blank"
    if not request.email:
        errors["Email"] = "cannot be blank"
    else:
        email_err = _validate_email_format(request.email)
        if email_err:
            errors["Email"] = email_err
    if not request.first_name:
        errors["FirstName"] = "cannot be blank"
    if not request.last_name:
        errors["LastName"] = "cannot be blank"
    if request.auth_grants is None:
        errors["AuthGrants"] = "cannot be blank"
    if not request.additional_authentication:
        errors["AdditionalAuthentication"] = "cannot be blank"
    else:
        auth_err = validate_authentication(
            request.additional_authentication
        )
        if auth_err:
            errors["AdditionalAuthentication"] = auth_err
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_get_user_request(request):
    """Validate GetUserRequest fields."""
    errors = {}
    if not request.identity_id:
        errors["IdentityID"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_update_user_info_request(request):
    """Validate UpdateUserInfoRequest fields.

    Validates IdentityID and nested User fields.
    """
    errors = {}
    if not request.identity_id:
        errors["IdentityID"] = "cannot be blank"
    if not request.user.first_name:
        errors["FirstName"] = "cannot be blank"
    if not request.user.last_name:
        errors["LastName"] = "cannot be blank"
    if not request.user.country:
        errors["Country"] = "cannot be blank"
    if not request.user.time_zone:
        errors["TimeZone"] = "cannot be blank"
    if not request.user.preferred_language:
        errors["PreferredLanguage"] = "cannot be blank"
    if request.user.session_time_out is None:
        errors["SessionTimeOut"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_update_user_notifications_request(request):
    """Validate UpdateUserNotificationsRequest fields."""
    errors = {}
    if not request.identity_id:
        errors["IdentityID"] = "cannot be blank"
    if request.notifications is None:
        errors["Notifications"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_update_user_auth_grants_request(request):
    """Validate UpdateUserAuthGrantsRequest fields."""
    errors = {}
    if not request.identity_id:
        errors["IdentityID"] = "cannot be blank"
    if request.auth_grants is None:
        errors["AuthGrants"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_remove_user_request(request):
    """Validate RemoveUserRequest fields.

    Note: error key is 'uiIdentity', not 'IdentityID', matching Go.
    """
    errors = {}
    if not request.identity_id:
        errors["uiIdentity"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_update_mfa_request(request):
    """Validate UpdateMFARequest fields.

    Value is a required Authentication enum. IdentityID is NOT validated
    in the Go reference (only Value is checked).
    """
    errors = {}
    if not request.value:
        errors["Value"] = "cannot be blank"
    else:
        auth_err = validate_authentication(request.value)
        if auth_err:
            errors["Value"] = auth_err
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


# =====================================================================
# User Lock validation (user_lock.go)
# =====================================================================


def validate_lock_user_request(request):
    """Validate LockUserRequest fields."""
    errors = {}
    if not request.identity_id:
        errors["IdentityID"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_unlock_user_request(request):
    """Validate UnlockUserRequest fields."""
    errors = {}
    if not request.identity_id:
        errors["IdentityID"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


# =====================================================================
# User Password validation (user_password.go)
# =====================================================================


def validate_reset_user_password_request(request):
    """Validate ResetUserPasswordRequest fields."""
    errors = {}
    if not request.identity_id:
        errors["IdentityID"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)


def validate_set_user_password_request(request):
    """Validate SetUserPasswordRequest fields."""
    errors = {}
    if not request.identity_id:
        errors["IdentityID"] = "cannot be blank"
    if not request.new_password:
        errors["NewPassword"] = "cannot be blank"
    result = parse_validation_errors(errors)
    if result:
        raise ErrStructValidation(result)
