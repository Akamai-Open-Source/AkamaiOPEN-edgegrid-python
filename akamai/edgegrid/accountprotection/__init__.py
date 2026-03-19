"""Akamai Account Protection API client package.

Provides access to the Akamai Account Protection APIs for managing
protected operations, general settings, user risk response strategies,
and user allow lists.

See: https://techdocs.akamai.com/account-protector/reference/api

Mirrors Go pkg/accountprotection (account_protection.go) public interface
and Client() factory.
"""

from .accountprotection import AccountProtectionClient
from .models import (
    ListProtectedOperationsRequest,
    GetProtectedOperationByIDRequest,
    CreateProtectedOperationsRequest,
    UpdateProtectedOperationRequest,
    RemoveProtectedOperationRequest,
    GetGeneralSettingsRequest,
    UpsertGeneralSettingsRequest,
    GetUserRiskResponseStrategyRequest,
    UpsertUserRiskResponseStrategyRequest,
    GetUserAllowListIDRequest,
    UpsertUserAllowListIDRequest,
    DeleteUserAllowListIDRequest,
    ListProtectedOperationsResponse,
    Metadata,
)
from .errors import Error, ErrStructValidation

__all__ = [
    "AccountProtectionClient",
    "ListProtectedOperationsRequest",
    "GetProtectedOperationByIDRequest",
    "CreateProtectedOperationsRequest",
    "UpdateProtectedOperationRequest",
    "RemoveProtectedOperationRequest",
    "GetGeneralSettingsRequest",
    "UpsertGeneralSettingsRequest",
    "GetUserRiskResponseStrategyRequest",
    "UpsertUserRiskResponseStrategyRequest",
    "GetUserAllowListIDRequest",
    "UpsertUserAllowListIDRequest",
    "DeleteUserAllowListIDRequest",
    "ListProtectedOperationsResponse",
    "Metadata",
    "Error",
    "ErrStructValidation",
]
