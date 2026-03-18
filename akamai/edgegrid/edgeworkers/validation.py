"""Request validation functions for EdgeWorkers/EdgeKV API."""
# pylint: disable=too-many-lines

import json
from datetime import datetime

from akamai.edgegrid.validation import parse_validation_errors
from akamai.edgegrid.edgeworkers import models


# ===================================================================
# Valid report status and event handler tuples (for In() validation)
# ===================================================================

_VALID_REPORT_STATUSES = (
    models.STATUS_SUCCESS,
    models.STATUS_GENERIC_ERROR,
    models.STATUS_UNKNOWN_EDGE_WORKER_ID,
    models.STATUS_UNIMPLEMENTED_EVENT_HANDLER,
    models.STATUS_RUNTIME_ERROR,
    models.STATUS_EXECUTION_ERROR,
    models.STATUS_TIMEOUT_ERROR,
    models.STATUS_RESOURCE_LIMIT_HIT,
    models.STATUS_CPU_TIMEOUT_ERROR,
    models.STATUS_WALL_TIMEOUT_ERROR,
    models.STATUS_INIT_CPU_TIMEOUT_ERROR,
    models.STATUS_INIT_WALL_TIMEOUT_ERROR,
)

_VALID_EVENT_HANDLERS = (
    models.EVENT_HANDLER_ON_CLIENT_REQUEST,
    models.EVENT_HANDLER_ON_ORIGIN_REQUEST,
    models.EVENT_HANDLER_ON_ORIGIN_RESPONSE,
    models.EVENT_HANDLER_ON_CLIENT_RESPONSE,
    models.EVENT_HANDLER_RESPONSE_PROVIDER,
)


# ===================================================================
# Helper functions
# ===================================================================


def is_json(data: str) -> bool:
    """Check if the given string is valid JSON.

    Mirrors Go IsJSON() from edgekv_items.go.
    """
    try:
        json.loads(data)
        return True
    except (json.JSONDecodeError, TypeError, ValueError):
        return False


def _collect_errors(errors: dict[str, str | None]) -> str | None:
    """Return a formatted error string if any validation errors exist.

    Mirrors Go validation.Errors{...}.Filter() + Error() pattern.
    Keys are sorted alphabetically, separated by '; ', with trailing '.'.

    Returns ``None`` when all values are ``None`` (no errors).
    """
    filtered = {k: v for k, v in errors.items() if v is not None}
    if not filtered:
        return None
    parts = [f"{k}: {v}" for k, v in sorted(filtered.items())]
    return "; ".join(parts) + "."


def _validate_date_format(value: str) -> str | None:
    """Validate date matches Go format '2006-01-02T15:04:05.999Z'.

    Returns error message if invalid, None if valid.
    Empty/None values are treated as valid (caller handles Required).
    Go .999 means optional fractional seconds, so both
    '2023-01-01T00:00:00Z' and '2023-01-01T00:00:00.123Z' are valid.
    """
    if not value:
        return None
    # Try with fractional seconds first, then without
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            datetime.strptime(value, fmt)
            return None
        except ValueError:
            continue
    return (
        f"value '{value}' is invalid. "
        "It must have format '2006-01-02T15:04:05.999Z'"
    )


def _validate_namespace_network(network: str) -> str | None:
    """Validate namespace/EdgeKV network value.

    Mirrors Go validateNetwork() from edgekv_namespaces.go.
    Returns error message if invalid, None if valid.
    """
    if not network:
        return "cannot be blank"
    if network not in (
        models.NAMESPACE_STAGING_NETWORK,
        models.NAMESPACE_PRODUCTION_NETWORK,
    ):
        return (
            f"value '{network}' is invalid. Must be one of: "
            f"'{models.NAMESPACE_STAGING_NETWORK}' or "
            f"'{models.NAMESPACE_PRODUCTION_NETWORK}'"
        )
    return None


def _validate_namespace_name(name: str) -> str | None:
    """Validate namespace name value.

    Mirrors Go validateName() from edgekv_namespaces.go.
    Returns error message if invalid, None if valid.
    """
    if not name:
        return "cannot be blank"
    if len(name) < 1 or len(name) > 32:
        return "the length must be between 1 and 32"
    return None


def _validate_retention(retention: int | None) -> str | None:
    """Validate retention period.

    Mirrors Go validateRetention() from edgekv_namespaces.go.
    Cannot be blank; non-zero value cannot be < 86400 or > 315360000.
    """
    if retention is None:
        return "cannot be blank"
    if (retention < 86400 and retention != 0) or retention > 315360000:
        return (
            "a non zero value specified for retention period "
            "cannot be less than 86400 or more than 315360000"
        )
    return None


def _validate_group_id(group_id: int | None) -> str | None:
    """Validate group ID for namespace operations.

    Mirrors Go validateGroupID() from edgekv_namespaces.go.
    Cannot be blank; cannot be less than 0.
    """
    if group_id is None:
        return "cannot be blank"
    if group_id < 0:
        return "cannot be less than 0"
    return None


def _validate_report_status(status: str | None) -> str | None:
    """Validate optional report status field.

    Mirrors Go NilOrNotEmpty + In() pattern from report.go.
    None is valid (optional). Empty string is invalid. Non-empty must
    be one of the valid status values.
    """
    if status is None:
        return None
    if status == "":
        return "cannot be blank"
    if status not in _VALID_REPORT_STATUSES:
        return (
            f"value '{status}' is invalid. Must be one of: "
            "'success', 'genericError', 'unknownEdgeWorkerId', "
            "'unimplementedEventHandler', 'runtimeError', "
            "'executionError', 'timeoutError', 'resourceLimitHit', "
            "'cpuTimeoutError', 'wallTimeoutError', "
            "'initCpuTimeoutError' or 'initWallTimeoutError'"
        )
    return None


def _validate_report_event_handler(event_handler: str | None) -> str | None:
    """Validate optional report event handler field.

    Mirrors Go NilOrNotEmpty + In() pattern from report.go.
    None is valid (optional). Empty string is invalid. Non-empty must
    be one of the valid event handler values.
    """
    if event_handler is None:
        return None
    if event_handler == "":
        return "cannot be blank"
    if event_handler not in _VALID_EVENT_HANDLERS:
        return (
            f"value '{event_handler}' is invalid. Must be one of: "
            "'onClientRequest', 'onOriginRequest', "
            "'onOriginResponse', 'onClientResponse' "
            "or 'responseProvider'"
        )
    return None


# ===================================================================
# Activation validators — from activations.go
# ===================================================================


def validate_list_activations_request(
    request: models.ListActivationsRequest,
) -> None:
    """Validate ListActivationsRequest. EdgeWorkerID required."""
    errors: dict[str, str | None] = {}
    if not request.edge_worker_id:
        errors["EdgeWorkerID"] = "cannot be blank"
    return _collect_errors(errors)


def validate_get_activation_request(
    request: models.GetActivationRequest,
) -> None:
    """Validate GetActivationRequest. EdgeWorkerID and ActivationID required."""
    errors: dict[str, str | None] = {}
    if not request.activation_id:
        errors["ActivationID"] = "cannot be blank"
    if not request.edge_worker_id:
        errors["EdgeWorkerID"] = "cannot be blank"
    return _collect_errors(errors)


def validate_activate_version_request(
    request: models.ActivateVersionRequest,
) -> None:
    """Validate ActivateVersionRequest.

    EdgeWorkerID required. ActivateVersion struct required (not None).
    """
    errors: dict[str, str | None] = {}
    if request.activate_version is None:
        errors["ActivateVersion"] = "cannot be blank"
    if not request.edge_worker_id:
        errors["EdgeWorkerID"] = "cannot be blank"
    return _collect_errors(errors)


def validate_activate_version(
    request: models.ActivateVersion,
) -> None:
    """Validate ActivateVersion struct.

    Network required and must be STAGING or PRODUCTION.
    Version required.
    """
    errors: dict[str, str | None] = {}
    if not request.network:
        errors["Network"] = "cannot be blank"
    elif request.network not in (
        models.ACTIVATION_NETWORK_STAGING,
        models.ACTIVATION_NETWORK_PRODUCTION,
    ):
        errors["Network"] = (
            f"value '{request.network}' is invalid. "
            "Must be one of: 'STAGING' or 'PRODUCTION'"
        )
    if not request.version:
        errors["Version"] = "cannot be blank"
    return _collect_errors(errors)


def validate_cancel_activation_request(
    request: models.CancelActivationRequest,
) -> None:
    """Validate CancelActivationRequest.

    EdgeWorkerID and ActivationID required.
    """
    errors: dict[str, str | None] = {}
    if not request.activation_id:
        errors["ActivationID"] = "cannot be blank"
    if not request.edge_worker_id:
        errors["EdgeWorkerID"] = "cannot be blank"
    return _collect_errors(errors)


# ===================================================================
# Deactivation validators — from deactivations.go
# ===================================================================


def validate_list_deactivations_request(
    request: models.ListDeactivationsRequest,
) -> None:
    """Validate ListDeactivationsRequest. EdgeWorkerID required."""
    errors: dict[str, str | None] = {}
    if not request.edge_worker_id:
        errors["EdgeWorkerID"] = "cannot be blank"
    return _collect_errors(errors)


def validate_deactivate_version_request(
    request: models.DeactivateVersionRequest,
) -> None:
    """Validate DeactivateVersionRequest.

    EdgeWorkerID required. DeactivateVersion struct required (not None).
    """
    errors: dict[str, str | None] = {}
    if request.deactivate_version is None:
        errors["DeactivateVersion"] = "cannot be blank"
    if not request.edge_worker_id:
        errors["EdgeWorkerID"] = "cannot be blank"
    return _collect_errors(errors)


def validate_deactivate_version(
    request: models.DeactivateVersion,
) -> None:
    """Validate DeactivateVersion struct.

    Network required and must be STAGING or PRODUCTION.
    Version required.
    """
    errors: dict[str, str | None] = {}
    if not request.network:
        errors["Network"] = "cannot be blank"
    elif request.network not in (
        models.ACTIVATION_NETWORK_STAGING,
        models.ACTIVATION_NETWORK_PRODUCTION,
    ):
        errors["Network"] = (
            f"value '{request.network}' is invalid. "
            "Must be one of: 'STAGING' or 'PRODUCTION'"
        )
    if not request.version:
        errors["Version"] = "cannot be blank"
    return _collect_errors(errors)


def validate_get_deactivation_request(
    request: models.GetDeactivationRequest,
) -> None:
    """Validate GetDeactivationRequest.

    EdgeWorkerID and DeactivationID required.
    """
    errors: dict[str, str | None] = {}
    if not request.deactivation_id:
        errors["DeactivationID"] = "cannot be blank"
    if not request.edge_worker_id:
        errors["EdgeWorkerID"] = "cannot be blank"
    return _collect_errors(errors)


# ===================================================================
# EdgeKV Access Token validators — from edgekv_access_tokens.go
# ===================================================================


def validate_create_edgekv_access_token_request(  # pylint: disable=too-many-branches
    request: models.CreateEdgeKVAccessTokenRequest,
) -> None:
    """Validate CreateEdgeKVAccessTokenRequest.

    At least one of AllowOnProduction or AllowOnStaging must be true.
    Name required with length 1-32. NamespacePermissions required with
    valid permission values (r, w, d).
    """
    errors: dict[str, str | None] = {}

    # AllowOnProduction: Required.When(!AllowOnStaging)
    # AllowOnStaging: Required.When(!AllowOnProduction)
    if not request.allow_on_production and not request.allow_on_staging:
        errors["AllowOnProduction"] = (
            "at least one of AllowOnProduction or "
            "AllowOnStaging has to be provided"
        )
        errors["AllowOnStaging"] = (
            "at least one of AllowOnProduction or "
            "AllowOnStaging has to be provided"
        )

    # Name: Required, Length(1, 32)
    if not request.name:
        errors["Name"] = "cannot be blank"
    elif len(request.name) > 32:
        errors["Name"] = "the length must be between 1 and 32"

    # NamespacePermissions.Names: Required, Each(Required)
    # Go extracts map keys as []string, validates Required + Each(Required)
    namespaces = (
        list(request.namespace_permissions.keys())
        if request.namespace_permissions
        else []
    )
    if not namespaces:
        errors["NamespacePermissions.Names"] = "cannot be blank"
    else:
        ns_name_errors: dict[str, str] = {}
        for idx, ns_name in enumerate(namespaces):
            if not ns_name:
                ns_name_errors[str(idx)] = "cannot be blank"
        if ns_name_errors:
            parts = [
                f"{k}: {v}"
                for k, v in sorted(
                    ns_name_errors.items(),
                    key=lambda x: int(x[0]),
                )
            ]
            errors["NamespacePermissions.Names"] = (
                "(" + "; ".join(parts) + ".)"
            )

    # NamespacePermissions: Required, Each(Required, Each(Required, In))
    if not request.namespace_permissions:
        errors["NamespacePermissions"] = "cannot be blank"
    else:
        ns_perm_errors: dict[str, str] = {}
        for ns_name, perms in request.namespace_permissions.items():
            if not perms:
                ns_perm_errors[ns_name] = "cannot be blank"
            else:
                inner_errors: dict[str, str] = {}
                for idx, perm in enumerate(perms):
                    if not perm:
                        inner_errors[str(idx)] = "cannot be blank"
                    elif perm not in (
                        models.PERMISSION_READ,
                        models.PERMISSION_WRITE,
                        models.PERMISSION_DELETE,
                    ):
                        inner_errors[str(idx)] = (
                            "must be a valid value"
                        )
                if inner_errors:
                    iparts = [
                        f"{k}: {v}"
                        for k, v in sorted(
                            inner_errors.items(),
                            key=lambda x: int(x[0]),
                        )
                    ]
                    ns_perm_errors[ns_name] = (
                        "(" + "; ".join(iparts) + ".)"
                    )
        if ns_perm_errors:
            parts = [
                f"{k}: {v}" for k, v in sorted(ns_perm_errors.items())
            ]
            errors["NamespacePermissions"] = (
                "(" + "; ".join(parts) + ".)"
            )

    return _collect_errors(errors)


def validate_get_edgekv_access_token_request(
    request: models.GetEdgeKVAccessTokenRequest,
) -> None:
    """Validate GetEdgeKVAccessTokenRequest.

    TokenName required with length 1-32.
    """
    errors: dict[str, str | None] = {}
    if not request.token_name:
        errors["TokenName"] = "cannot be blank"
    elif len(request.token_name) > 32:
        errors["TokenName"] = "the length must be between 1 and 32"
    return _collect_errors(errors)


def validate_delete_edgekv_access_token_request(
    request: models.DeleteEdgeKVAccessTokenRequest,
) -> None:
    """Validate DeleteEdgeKVAccessTokenRequest.

    TokenName required with length 1-32.
    """
    errors: dict[str, str | None] = {}
    if not request.token_name:
        errors["TokenName"] = "cannot be blank"
    elif len(request.token_name) > 32:
        errors["TokenName"] = "the length must be between 1 and 32"
    return _collect_errors(errors)


# ===================================================================
# EdgeKV Groups validator — from edgekv_groups.go
# Uses parse_validation_errors instead of _collect_errors.
# ===================================================================


def validate_list_groups_within_namespace_request(
    request: models.ListGroupsWithinNamespaceRequest,
) -> str | None:
    """Validate ListGroupsWithinNamespaceRequest.

    Network and NamespaceID required.
    Uses edgegriderr.ParseValidationErrors pattern.
    """
    errors: dict[str, str | None] = {}
    if not request.network:
        errors["Network"] = "cannot be blank"
    if not request.namespace_id:
        errors["NamespaceID"] = "cannot be blank"

    filtered = {k: v for k, v in errors.items() if v is not None}
    if filtered:
        parsed = parse_validation_errors(filtered)
        if parsed:
            return parsed
    return None


# ===================================================================
# EdgeKV Items validators — from edgekv_items.go
# ===================================================================


def validate_items_request_params(
    request: models.ItemsRequestParams,
) -> None:
    """Validate ItemsRequestParams.

    Network required and must be 'staging' or 'production'.
    NamespaceID and GroupID required.
    """
    errors: dict[str, str | None] = {}
    if not request.group_id:
        errors["GroupID"] = "cannot be blank"
    if not request.namespace_id:
        errors["NamespaceID"] = "cannot be blank"
    if not request.network:
        errors["Network"] = "cannot be blank"
    elif request.network not in (
        models.ITEM_STAGING_NETWORK,
        models.ITEM_PRODUCTION_NETWORK,
    ):
        errors["Network"] = (
            f"value '{request.network}' is invalid. Must be one of: "
            f"'{models.ITEM_STAGING_NETWORK}' or "
            f"'{models.ITEM_PRODUCTION_NETWORK}'"
        )
    return _collect_errors(errors)


def validate_list_items_request(
    request: models.ListItemsRequest,
) -> None:
    """Validate ListItemsRequest. ItemsRequestParams required."""
    errors: dict[str, str | None] = {}
    if request.items_request_params is None:
        errors["ItemsRequestParams"] = "cannot be blank"
    return _collect_errors(errors)


def validate_get_item_request(
    request: models.GetItemRequest,
) -> None:
    """Validate GetItemRequest.

    ItemID and ItemsRequestParams required.
    """
    errors: dict[str, str | None] = {}
    if not request.item_id:
        errors["ItemID"] = "cannot be blank"
    if request.items_request_params is None:
        errors["ItemsRequestParams"] = "cannot be blank"
    return _collect_errors(errors)


def validate_upsert_item_request(
    request: models.UpsertItemRequest,
) -> None:
    """Validate UpsertItemRequest.

    ItemID, ItemData, and ItemsRequestParams required.
    """
    errors: dict[str, str | None] = {}
    if not request.item_data:
        errors["ItemData"] = "cannot be blank"
    if not request.item_id:
        errors["ItemID"] = "cannot be blank"
    if request.items_request_params is None:
        errors["ItemsRequestParams"] = "cannot be blank"
    return _collect_errors(errors)


def validate_delete_item_request(
    request: models.DeleteItemRequest,
) -> None:
    """Validate DeleteItemRequest.

    ItemID and ItemsRequestParams required.
    """
    errors: dict[str, str | None] = {}
    if not request.item_id:
        errors["ItemID"] = "cannot be blank"
    if request.items_request_params is None:
        errors["ItemsRequestParams"] = "cannot be blank"
    return _collect_errors(errors)


# ===================================================================
# EdgeKV Namespace validators — from edgekv_namespaces.go
# ===================================================================


def validate_list_edgekv_namespaces_request(
    request: models.ListEdgeKVNamespacesRequest,
) -> None:
    """Validate ListEdgeKVNamespacesRequest. Network required."""
    errors: dict[str, str | None] = {}
    errors["Network"] = _validate_namespace_network(request.network)
    return _collect_errors(errors)


def validate_get_edgekv_namespace_request(
    request: models.GetEdgeKVNamespaceRequest,
) -> None:
    """Validate GetEdgeKVNamespaceRequest.

    Network and Name required (name length 1-32).
    """
    errors: dict[str, str | None] = {}
    errors["Name"] = _validate_namespace_name(request.name)
    errors["Network"] = _validate_namespace_network(request.network)
    return _collect_errors(errors)


def validate_create_edgekv_namespace_request(
    request: models.CreateEdgeKVNamespaceRequest,
) -> None:
    """Validate CreateEdgeKVNamespaceRequest.

    Network, Name (1-32), Retention, and GroupID required.
    Retention non-zero must be between 86400 and 315360000.
    GroupID cannot be negative.
    """
    errors: dict[str, str | None] = {}
    errors["Network"] = _validate_namespace_network(request.network)

    if request.namespace_request is None:
        errors["Name"] = "cannot be blank"
        errors["Retention"] = "cannot be blank"
        errors["GroupID"] = "cannot be blank"
    else:
        errors["Name"] = _validate_namespace_name(
            request.namespace_request.name,
        )
        retention_err = _validate_retention(
            request.namespace_request.retention,
        )
        if retention_err:
            errors["Retention"] = retention_err
        group_id_err = _validate_group_id(
            request.namespace_request.group_id,
        )
        if group_id_err:
            errors["GroupID"] = group_id_err

    return _collect_errors(errors)


def validate_update_edgekv_namespace_request(
    request: models.UpdateEdgeKVNamespaceRequest,
) -> None:
    """Validate UpdateEdgeKVNamespaceRequest.

    Same constraints as CreateEdgeKVNamespaceRequest.
    """
    errors: dict[str, str | None] = {}
    errors["Network"] = _validate_namespace_network(request.network)

    if request.update_namespace is None:
        errors["Name"] = "cannot be blank"
        errors["Retention"] = "cannot be blank"
        errors["GroupID"] = "cannot be blank"
    else:
        errors["Name"] = _validate_namespace_name(
            request.update_namespace.name,
        )
        retention_err = _validate_retention(
            request.update_namespace.retention,
        )
        if retention_err:
            errors["Retention"] = retention_err
        group_id_err = _validate_group_id(
            request.update_namespace.group_id,
        )
        if group_id_err:
            errors["GroupID"] = group_id_err

    return _collect_errors(errors)


def validate_delete_edgekv_namespace_request(
    request: models.DeleteEdgeKVNamespaceRequest,
) -> None:
    """Validate DeleteEdgeKVNamespaceRequest.

    Network and Name required.
    """
    errors: dict[str, str | None] = {}
    errors["Name"] = _validate_namespace_name(request.name)
    errors["Network"] = _validate_namespace_network(request.network)
    return _collect_errors(errors)


def validate_get_scheduled_delete_time_request(
    request: models.GetScheduledDeleteTimeRequest,
) -> None:
    """Validate GetScheduledDeleteTimeRequest.

    Network and Name required.
    """
    errors: dict[str, str | None] = {}
    errors["Name"] = _validate_namespace_name(request.name)
    errors["Network"] = _validate_namespace_network(request.network)
    return _collect_errors(errors)


def validate_reschedule_namespace_delete_request(
    request: models.RescheduleNamespaceDeleteRequest,
) -> None:
    """Validate RescheduleNamespaceDeleteRequest.

    Network, Name, and Body required.
    """
    errors: dict[str, str | None] = {}
    if request.body is None:
        errors["Body"] = "cannot be blank"
    errors["Name"] = _validate_namespace_name(request.name)
    errors["Network"] = _validate_namespace_network(request.network)
    return _collect_errors(errors)


def validate_cancel_scheduled_namespace_delete_request(
    request: models.CancelScheduledNamespaceDeleteRequest,
) -> None:
    """Validate CancelScheduledNamespaceDeleteRequest.

    Network and Name required.
    """
    errors: dict[str, str | None] = {}
    errors["Name"] = _validate_namespace_name(request.name)
    errors["Network"] = _validate_namespace_network(request.network)
    return _collect_errors(errors)


# ===================================================================
# EdgeWorkerID validators — from edgeworker_id.go
# ===================================================================


def validate_get_edge_worker_id_request(
    request: models.GetEdgeWorkerIDRequest,
) -> None:
    """Validate GetEdgeWorkerIDRequest. EdgeWorkerID required."""
    errors: dict[str, str | None] = {}
    if not request.edge_worker_id:
        errors["EdgeWorkerID"] = "cannot be blank"
    return _collect_errors(errors)


def validate_create_edge_worker_id_request(
    request: models.CreateEdgeWorkerIDRequest,
) -> None:
    """Validate CreateEdgeWorkerIDRequest.

    Name, GroupID, and ResourceTierID required.
    """
    errors: dict[str, str | None] = {}
    if not request.group_id:
        errors["GroupID"] = "cannot be blank"
    if not request.name:
        errors["Name"] = "cannot be blank"
    if not request.resource_tier_id:
        errors["ResourceTierID"] = "cannot be blank"
    return _collect_errors(errors)


def validate_update_edge_worker_id_request(
    request: models.UpdateEdgeWorkerIDRequest,
) -> None:
    """Validate UpdateEdgeWorkerIDRequest.

    Body.Name, Body.GroupID, Body.ResourceTierID, and EdgeWorkerID required.
    """
    errors: dict[str, str | None] = {}
    if not request.edge_worker_id:
        errors["EdgeWorkerID"] = "cannot be blank"
    if request.body is None:
        errors["GroupID"] = "cannot be blank"
        errors["Name"] = "cannot be blank"
        errors["ResourceTierID"] = "cannot be blank"
    else:
        if not request.body.group_id:
            errors["GroupID"] = "cannot be blank"
        if not request.body.name:
            errors["Name"] = "cannot be blank"
        if not request.body.resource_tier_id:
            errors["ResourceTierID"] = "cannot be blank"
    return _collect_errors(errors)


def validate_clone_edge_worker_id_request(
    request: models.CloneEdgeWorkerIDRequest,
) -> None:
    """Validate CloneEdgeWorkerIDRequest.

    Body.Name, Body.GroupID, Body.ResourceTierID, and EdgeWorkerID required.
    """
    errors: dict[str, str | None] = {}
    if not request.edge_worker_id:
        errors["EdgeWorkerID"] = "cannot be blank"
    if request.body is None:
        errors["GroupID"] = "cannot be blank"
        errors["Name"] = "cannot be blank"
        errors["ResourceTierID"] = "cannot be blank"
    else:
        if not request.body.group_id:
            errors["GroupID"] = "cannot be blank"
        if not request.body.name:
            errors["Name"] = "cannot be blank"
        if not request.body.resource_tier_id:
            errors["ResourceTierID"] = "cannot be blank"
    return _collect_errors(errors)


def validate_delete_edge_worker_id_request(
    request: models.DeleteEdgeWorkerIDRequest,
) -> None:
    """Validate DeleteEdgeWorkerIDRequest. EdgeWorkerID required."""
    errors: dict[str, str | None] = {}
    if not request.edge_worker_id:
        errors["EdgeWorkerID"] = "cannot be blank"
    return _collect_errors(errors)


# ===================================================================
# EdgeWorkerVersion validators — from edgeworker_version.go
# ===================================================================


def validate_get_edge_worker_version_request(
    request: models.GetEdgeWorkerVersionRequest,
) -> None:
    """Validate GetEdgeWorkerVersionRequest.

    EdgeWorkerID and Version required.
    """
    errors: dict[str, str | None] = {}
    if not request.edge_worker_id:
        errors["EdgeWorkerID"] = "cannot be blank"
    if not request.version:
        errors["Version"] = "cannot be blank"
    return _collect_errors(errors)


def validate_list_edge_worker_versions_request(
    request: models.ListEdgeWorkerVersionsRequest,
) -> None:
    """Validate ListEdgeWorkerVersionsRequest. EdgeWorkerID required."""
    errors: dict[str, str | None] = {}
    if not request.edge_worker_id:
        errors["EdgeWorkerID"] = "cannot be blank"
    return _collect_errors(errors)


def validate_create_edge_worker_version_request(
    request: models.CreateEdgeWorkerVersionRequest,
) -> None:
    """Validate CreateEdgeWorkerVersionRequest.

    EdgeWorkerID required. ContentBundle (Reader) must not be None.
    """
    errors: dict[str, str | None] = {}
    if request.content_bundle is None:
        errors["ContentBundle.Reader"] = "is required"
    if not request.edge_worker_id:
        errors["EdgeWorkerID"] = "cannot be blank"
    return _collect_errors(errors)


def validate_get_edge_worker_version_content_request(
    request: models.GetEdgeWorkerVersionContentRequest,
) -> None:
    """Validate GetEdgeWorkerVersionContentRequest.

    EdgeWorkerID and Version required.
    """
    errors: dict[str, str | None] = {}
    if not request.edge_worker_id:
        errors["EdgeWorkerID"] = "cannot be blank"
    if not request.version:
        errors["Version"] = "cannot be blank"
    return _collect_errors(errors)


def validate_delete_edge_worker_version_request(
    request: models.DeleteEdgeWorkerVersionRequest,
) -> None:
    """Validate DeleteEdgeWorkerVersionRequest.

    EdgeWorkerID and Version required.
    """
    errors: dict[str, str | None] = {}
    if not request.edge_worker_id:
        errors["EdgeWorkerID"] = "cannot be blank"
    if not request.version:
        errors["Version"] = "cannot be blank"
    return _collect_errors(errors)


# ===================================================================
# Permission Group validator — from permission_group.go
# ===================================================================


def validate_get_permission_group_request(
    request: models.GetPermissionGroupRequest,
) -> None:
    """Validate GetPermissionGroupRequest. GroupID required."""
    errors: dict[str, str | None] = {}
    if not request.group_id:
        errors["GroupID"] = "cannot be blank"
    return _collect_errors(errors)


# ===================================================================
# Properties validator — from properties.go
# ===================================================================


def validate_list_properties_request(
    request: models.ListPropertiesRequest,
) -> None:
    """Validate ListPropertiesRequest. EdgeWorkerID required."""
    errors: dict[str, str | None] = {}
    if not request.edge_worker_id:
        errors["EdgeWorkerID"] = "cannot be blank"
    return _collect_errors(errors)


# ===================================================================
# Report validators — from report.go
# ===================================================================


def validate_get_summary_report_request(
    request: models.GetSummaryReportRequest,
) -> None:
    """Validate GetSummaryReportRequest.

    Start required with date format. End optional but format-validated.
    EdgeWorker required. Status and EventHandler optional (NilOrNotEmpty)
    with In() validation.
    """
    errors: dict[str, str | None] = {}

    # EdgeWorker: Required
    if not request.edge_worker:
        errors["EdgeWorker"] = "cannot be blank"

    # End: Date format only (not Required)
    end_err = _validate_date_format(request.end)
    if end_err:
        errors["End"] = end_err

    # EventHandler: NilOrNotEmpty, In()
    eh_err = _validate_report_event_handler(request.event_handler)
    if eh_err:
        errors["EventHandler"] = eh_err

    # Start: Required, Date format
    if not request.start:
        errors["Start"] = "cannot be blank"
    else:
        start_err = _validate_date_format(request.start)
        if start_err:
            errors["Start"] = start_err

    # Status: NilOrNotEmpty, In()
    status_err = _validate_report_status(request.status)
    if status_err:
        errors["Status"] = status_err

    return _collect_errors(errors)


def validate_get_report_request(
    request: models.GetReportRequest,
) -> None:
    """Validate GetReportRequest.

    ReportID required with Min(2). Same date/status/handler validation
    as GetSummaryReportRequest.
    """
    errors: dict[str, str | None] = {}

    # EdgeWorker: Required
    if not request.edge_worker:
        errors["EdgeWorker"] = "cannot be blank"

    # End: Date format only (not Required)
    end_err = _validate_date_format(request.end)
    if end_err:
        errors["End"] = end_err

    # EventHandler: NilOrNotEmpty, In()
    eh_err = _validate_report_event_handler(request.event_handler)
    if eh_err:
        errors["EventHandler"] = eh_err

    # ReportID: Required, Min(2)
    if not request.report_id:
        errors["ReportID"] = "cannot be blank"
    elif request.report_id < 2:
        errors["ReportID"] = "must be no less than 2"

    # Start: Required, Date format
    if not request.start:
        errors["Start"] = "cannot be blank"
    else:
        start_err = _validate_date_format(request.start)
        if start_err:
            errors["Start"] = start_err

    # Status: NilOrNotEmpty, In()
    status_err = _validate_report_status(request.status)
    if status_err:
        errors["Status"] = status_err

    return _collect_errors(errors)


# ===================================================================
# Resource Tier validators — from resource_tier.go
# ===================================================================


def validate_list_resource_tiers_request(
    request: models.ListResourceTiersRequest,
) -> None:
    """Validate ListResourceTiersRequest. ContractID required."""
    errors: dict[str, str | None] = {}
    if not request.contract_id:
        errors["ContractID"] = "cannot be blank"
    return _collect_errors(errors)


def validate_get_resource_tier_request(
    request: models.GetResourceTierRequest,
) -> None:
    """Validate GetResourceTierRequest. EdgeWorkerID required."""
    errors: dict[str, str | None] = {}
    if not request.edge_worker_id:
        errors["EdgeWorkerID"] = "cannot be blank"
    return _collect_errors(errors)


# ===================================================================
# Secure Token validator — from secure_tokens.go
# ===================================================================


def validate_create_secure_token_request(
    request: models.CreateSecureTokenRequest,
) -> None:
    """Validate CreateSecureTokenRequest.

    ACL and URL are mutually exclusive. Expiry between 1 and 720.
    Hostname or PropertyID required (at least one). Network optional
    but if provided must be STAGING or PRODUCTION.
    """
    errors: dict[str, str | None] = {}

    # ACL: Empty.When(URL != "")
    if request.url and request.acl:
        errors["ACL"] = (
            "If you specify an acl don't specify a url."
        )

    # Expiry: Min(1), Max(720) — skip when zero value (Go ozzo-validation
    # skips Min/Max rules for the zero value of a type; int zero = 0).
    if request.expiry != 0:
        if request.expiry < 1:
            errors["Expiry"] = "must be no less than 1"
        elif request.expiry > 720:
            errors["Expiry"] = "must be no greater than 720"

    # Hostname: Required.When(PropertyID == "")
    if not request.property_id and not request.hostname:
        errors["Hostname"] = (
            "To create an authentication token, provide either "
            "the hostname, or the propertyId"
        )

    # Network: In(STAGING, PRODUCTION) — empty is valid
    if request.network and request.network not in (
        models.ACTIVATION_NETWORK_STAGING,
        models.ACTIVATION_NETWORK_PRODUCTION,
    ):
        errors["Network"] = (
            f"value '{request.network}' is invalid. "
            "Must be one of: 'STAGING', 'PRODUCTION' or '' (empty)"
        )

    # PropertyID: Required.When(Hostname == "")
    if not request.hostname and not request.property_id:
        errors["PropertyID"] = (
            "To create an authentication token, provide either "
            "the hostname, or the propertyId"
        )

    # URL: Empty.When(ACL != "")
    # Note: Go source has leading space in error message (verbatim match)
    if request.acl and request.url:
        errors["URL"] = (
            " If you specify a url don't specify an acl"
        )

    return _collect_errors(errors)


# ===================================================================
# Validate Bundle validator — from validations.go
# ===================================================================


def validate_validate_bundle_request(
    request: models.ValidateBundleRequest,
) -> None:
    """Validate ValidateBundleRequest. Bundle (Reader) must not be None."""
    errors: dict[str, str | None] = {}
    if request.bundle is None:
        errors["Bundle.Reader"] = "is required"
    return _collect_errors(errors)
