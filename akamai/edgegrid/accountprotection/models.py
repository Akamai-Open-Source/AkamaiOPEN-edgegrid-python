"""Request and response models for the Account Protection API.

Defines dataclasses mirroring Go structs field-for-field from:
- pkg/accountprotection/protected_operation.go
- pkg/accountprotection/general_settings.go
- pkg/accountprotection/user_risk_response_strategy.go
- pkg/accountprotection/user_allow_list_id.go

Each Go struct maps to a Python dataclass with identical field names
(converted from PascalCase to snake_case), types (mapped per Go-to-Python
type rules), and required/optional semantics. Default values match Go
zero-value semantics allowing instantiation without all fields.
"""

from dataclasses import dataclass, field
from typing import Any


# === Response Models (from protected_operation.go lines 89-108) ===


@dataclass
class Metadata:
    """Metadata for Account Protection API responses.

    Mirrors Go Metadata struct (protected_operation.go lines 99-108).

    JSON field mapping:
    - configId -> config_id
    - configVersion -> config_version
    - securityPolicyId -> security_policy_id
    """

    config_id: int = 0
    config_version: int = 0
    security_policy_id: str = ""


@dataclass
class ListProtectedOperationsResponse:
    """Response for list/get/create protected operations.

    Mirrors Go ListProtectedOperationsResponse struct
    (protected_operation.go lines 90-96).

    JSON field mapping:
    - metadata -> metadata (Metadata)
    - operations -> operations (list[dict[str, Any]])
    """

    metadata: Metadata = field(default_factory=Metadata)
    operations: list[dict[str, Any]] = field(default_factory=list)


# === Protected Operation Request Models (from protected_operation.go lines 13-87) ===


@dataclass
class ListProtectedOperationsRequest:
    """Request to list protected operations for a configuration.

    Mirrors Go ListProtectedOperationsRequest struct
    (protected_operation.go lines 15-24).
    """

    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""


@dataclass
class GetProtectedOperationByIDRequest:
    """Request to get a protected operation by operation ID.

    Mirrors Go GetProtectedOperationByIDRequest struct
    (protected_operation.go lines 27-39).
    """

    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    operation_id: str = ""


@dataclass
class CreateProtectedOperationsRequest:
    """Request to create protected operations.

    Mirrors Go CreateProtectedOperationsRequest struct
    (protected_operation.go lines 42-54).

    json_payload maps to Go json.RawMessage (raw JSON payload).
    """

    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    json_payload: str | bytes | dict | list | None = None


@dataclass
class UpdateProtectedOperationRequest:
    """Request to update a protected operation.

    Mirrors Go UpdateProtectedOperationRequest struct
    (protected_operation.go lines 57-72).

    json_payload maps to Go json.RawMessage (raw JSON payload).
    """

    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    operation_id: str = ""
    json_payload: str | bytes | dict | list | None = None


@dataclass
class RemoveProtectedOperationRequest:
    """Request to remove a protected operation.

    Mirrors Go RemoveProtectedOperationRequest struct
    (protected_operation.go lines 75-87).
    """

    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    operation_id: str = ""


# === General Settings Request Models (from general_settings.go lines 13-41) ===


@dataclass
class GetGeneralSettingsRequest:
    """Request to get general settings for account protection.

    Mirrors Go GetGeneralSettingsRequest struct
    (general_settings.go lines 15-24).
    """

    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""


@dataclass
class UpsertGeneralSettingsRequest:
    """Request to upsert general settings for account protection.

    Mirrors Go UpsertGeneralSettingsRequest struct
    (general_settings.go lines 27-40).

    json_payload maps to Go json.RawMessage (raw JSON payload).
    """

    config_id: int = 0
    version: int = 0
    security_policy_id: str = ""
    json_payload: str | bytes | dict | list | None = None


# === User Risk Response Strategy Request Models ===
# (from user_risk_response_strategy.go lines 13-34)


@dataclass
class GetUserRiskResponseStrategyRequest:
    """Request to get user risk response strategy.

    Mirrors Go GetUserRiskResponseStrategyRequest struct
    (user_risk_response_strategy.go lines 15-21).
    """

    config_id: int = 0
    version: int = 0


@dataclass
class UpsertUserRiskResponseStrategyRequest:
    """Request to upsert user risk response strategy.

    Mirrors Go UpsertUserRiskResponseStrategyRequest struct
    (user_risk_response_strategy.go lines 24-33).

    json_payload maps to Go json.RawMessage (raw JSON payload).
    """

    config_id: int = 0
    version: int = 0
    json_payload: str | bytes | dict | list | None = None


# === User Allow List ID Request Models (from user_allow_list_id.go lines 13-43) ===


@dataclass
class GetUserAllowListIDRequest:
    """Request to get user allow list ID.

    Mirrors Go GetUserAllowListIDRequest struct
    (user_allow_list_id.go lines 15-21).
    """

    config_id: int = 0
    version: int = 0


@dataclass
class UpsertUserAllowListIDRequest:
    """Request to upsert user allow list ID.

    Mirrors Go UpsertUserAllowListIDRequest struct
    (user_allow_list_id.go lines 24-33).

    json_payload maps to Go json.RawMessage (raw JSON payload).
    """

    config_id: int = 0
    version: int = 0
    json_payload: str | bytes | dict | list | None = None


@dataclass
class DeleteUserAllowListIDRequest:
    """Request to delete user allow list ID.

    Mirrors Go DeleteUserAllowListIDRequest struct
    (user_allow_list_id.go lines 36-42).
    """

    config_id: int = 0
    version: int = 0
