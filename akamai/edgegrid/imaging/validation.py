"""Request validation functions for the Imaging API"""

from akamai.edgegrid.validation import parse_validation_errors


# ---------------------------------------------------------------------------
# Policy Network constants (mirrors Go PolicyNetwork typed string in policy.go)
# ---------------------------------------------------------------------------
POLICY_NETWORK_STAGING = "staging"
POLICY_NETWORK_PRODUCTION = "production"

# ---------------------------------------------------------------------------
# PolicySet Network constants (mirrors Go Network typed string in policyset.go)
# ---------------------------------------------------------------------------
NETWORK_STAGING = "staging"
NETWORK_PRODUCTION = "production"
NETWORK_BOTH = ""

# ---------------------------------------------------------------------------
# Region constants (mirrors Go Region typed string in policyset.go)
# ---------------------------------------------------------------------------
REGION_US = "US"
REGION_EMEA = "EMEA"
REGION_ASIA = "ASIA"
REGION_AUSTRALIA = "AUSTRALIA"
REGION_JAPAN = "JAPAN"
REGION_CHINA = "CHINA"
ALL_REGIONS = (
    REGION_US,
    REGION_EMEA,
    REGION_ASIA,
    REGION_AUSTRALIA,
    REGION_JAPAN,
    REGION_CHINA,
)

# ---------------------------------------------------------------------------
# MediaType constants (mirrors Go MediaType typed string in policyset.go)
# ---------------------------------------------------------------------------
TYPE_IMAGE = "IMAGE"
TYPE_VIDEO = "VIDEO"

# ---------------------------------------------------------------------------
# Internal tuples used for membership checks
# ---------------------------------------------------------------------------
_VALID_POLICY_NETWORKS = (POLICY_NETWORK_STAGING, POLICY_NETWORK_PRODUCTION)
_VALID_POLICY_SET_NETWORKS = (NETWORK_STAGING, NETWORK_PRODUCTION, NETWORK_BOTH)
_VALID_TYPES = (TYPE_IMAGE, TYPE_VIDEO)

# ---------------------------------------------------------------------------
# Range constraints for policy durations
# ---------------------------------------------------------------------------
_ROLLOUT_DURATION_MIN = 3600
_ROLLOUT_DURATION_MAX = 604800
_SERVE_STALE_DURATION_MIN = 0
_SERVE_STALE_DURATION_MAX = 2592000


# ===================================================================
# Private helpers — shared validation snippets reused by public funcs
# ===================================================================

def _validate_policy_network(network: str) -> str | None:
    """Return an error string for an invalid policy network value.

    Mirrors Go ``validation.Required, validation.In(PolicyNetworkStaging,
    PolicyNetworkProduction)`` with a custom error message.

    Args:
        network: The network value to validate.

    Returns:
        Error string, or ``None`` if valid.
    """
    if not network:
        return "cannot be blank"
    if network not in _VALID_POLICY_NETWORKS:
        return (
            f"network has to be "
            f"'{POLICY_NETWORK_STAGING}', "
            f"'{POLICY_NETWORK_PRODUCTION}'"
        )
    return None


def _validate_policy_set_network(network: str) -> str | None:
    """Return an error string for an invalid policy-set network value.

    Mirrors Go ``validation.In(NetworkStaging, NetworkProduction,
    NetworkBoth)`` **without** ``validation.Required`` — an empty string
    is a valid value (meaning "both networks").

    Args:
        network: The network value to validate.

    Returns:
        Error string, or ``None`` if valid.
    """
    if network not in _VALID_POLICY_SET_NETWORKS:
        return (
            f"network has to be "
            f"'{NETWORK_STAGING}', "
            f"'{NETWORK_PRODUCTION}' "
            f"or empty for both networks at the same time"
        )
    return None


def _validate_region(region: str) -> str | None:
    """Return an error string for an invalid region value.

    Mirrors Go ``validation.Required, validation.In(RegionUS, …,
    RegionChina)`` with a custom error message that includes the
    actual invalid value.

    Args:
        region: The region value to validate.

    Returns:
        Error string, or ``None`` if valid.
    """
    if not region:
        return "cannot be blank"
    if region not in ALL_REGIONS:
        return (
            f"value '{region}' is invalid. Must be one of: "
            f"'{REGION_US}', "
            f"'{REGION_EMEA}', "
            f"'{REGION_ASIA}', "
            f"'{REGION_AUSTRALIA}', "
            f"'{REGION_JAPAN}', "
            f"'{REGION_CHINA}'"
        )
    return None


def _validate_media_type(media_type: str) -> str | None:
    """Return an error string for an invalid media type value.

    Mirrors Go ``validation.Required, validation.In(TypeImage,
    TypeVideo)`` with a custom error message that includes the
    actual invalid value.

    Args:
        media_type: The media type value to validate.

    Returns:
        Error string, or ``None`` if valid.
    """
    if not media_type:
        return "cannot be blank"
    if media_type not in _VALID_TYPES:
        return (
            f"value '{media_type}' is invalid. Must be one of: "
            f"'{TYPE_IMAGE}', "
            f"'{TYPE_VIDEO}'"
        )
    return None


def _validate_rollout_duration(value: int | None) -> str | None:
    """Return an error string for an out-of-range rollout duration.

    Mirrors Go ``validation.Min(3600), validation.Max(604800)``
    applied to a ``*int`` (optional integer).  ``None`` is valid
    (the field is not set).

    Args:
        value: Rollout duration in seconds, or ``None``.

    Returns:
        Error string, or ``None`` if valid.
    """
    if value is None:
        return None
    if value < _ROLLOUT_DURATION_MIN:
        return f"must be no less than {_ROLLOUT_DURATION_MIN}"
    if value > _ROLLOUT_DURATION_MAX:
        return f"must be no greater than {_ROLLOUT_DURATION_MAX}"
    return None


def _validate_serve_stale_duration(value: int | None) -> str | None:
    """Return an error string for an out-of-range serve-stale duration.

    Mirrors Go ``validation.Min(0), validation.Max(2592000)``
    applied to a ``*int`` (optional integer).  ``None`` is valid
    (the field is not set).

    Args:
        value: Serve-stale duration in seconds, or ``None``.

    Returns:
        Error string, or ``None`` if valid.
    """
    if value is None:
        return None
    if value < _SERVE_STALE_DURATION_MIN:
        return f"must be no less than {_SERVE_STALE_DURATION_MIN}"
    if value > _SERVE_STALE_DURATION_MAX:
        return f"must be no greater than {_SERVE_STALE_DURATION_MAX}"
    return None


# ===================================================================
# Public validation functions — one per request type
# ===================================================================


def validate_list_policies_request(request) -> str | None:
    """Validate ListPoliciesRequest fields.

    Mirrors Go ``ListPoliciesRequest.Validate()`` (policy.go lines 264-272).

    Args:
        request: A ``ListPoliciesRequest`` instance with ``contract_id``,
                 ``policy_set_id``, and ``network`` attributes.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors = {}
    if not request.contract_id:
        errors["ContractID"] = "cannot be blank"
    if not request.policy_set_id:
        errors["PolicySetID"] = "cannot be blank"
    errors["Network"] = _validate_policy_network(request.network)
    return parse_validation_errors(errors)


def validate_get_policy_request(request) -> str | None:
    """Validate GetPolicyRequest fields.

    Mirrors Go ``GetPolicyRequest.Validate()`` (policy.go lines 275-284).

    Args:
        request: A ``GetPolicyRequest`` instance with ``policy_id``,
                 ``contract_id``, ``policy_set_id``, and ``network``
                 attributes.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors = {}
    if not request.policy_id:
        errors["PolicyID"] = "cannot be blank"
    if not request.contract_id:
        errors["ContractID"] = "cannot be blank"
    if not request.policy_set_id:
        errors["PolicySetID"] = "cannot be blank"
    errors["Network"] = _validate_policy_network(request.network)
    return parse_validation_errors(errors)


def validate_upsert_policy_request(request) -> str | None:
    """Validate UpsertPolicyRequest fields.

    Mirrors Go ``UpsertPolicyRequest.Validate()`` (policy.go lines 287-298).

    Args:
        request: An ``UpsertPolicyRequest`` instance with ``policy_id``,
                 ``contract_id``, ``policy_set_id``, ``network``, and
                 ``policy_input`` attributes.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors = {}
    if not request.policy_id:
        errors["PolicyID"] = "cannot be blank"
    if not request.contract_id:
        errors["ContractID"] = "cannot be blank"
    if not request.policy_set_id:
        errors["PolicySetID"] = "cannot be blank"
    errors["Network"] = _validate_policy_network(request.network)
    if request.policy_input is None:
        errors["Policy"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_delete_policy_request(request) -> str | None:
    """Validate DeletePolicyRequest fields.

    Mirrors Go ``DeletePolicyRequest.Validate()`` (policy.go lines 301-310).
    Identical constraints to ``GetPolicyRequest``.

    Args:
        request: A ``DeletePolicyRequest`` instance with ``policy_id``,
                 ``contract_id``, ``policy_set_id``, and ``network``
                 attributes.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors = {}
    if not request.policy_id:
        errors["PolicyID"] = "cannot be blank"
    if not request.contract_id:
        errors["ContractID"] = "cannot be blank"
    if not request.policy_set_id:
        errors["PolicySetID"] = "cannot be blank"
    errors["Network"] = _validate_policy_network(request.network)
    return parse_validation_errors(errors)


def validate_get_policy_history_request(request) -> str | None:
    """Validate GetPolicyHistoryRequest fields.

    Mirrors Go ``GetPolicyHistoryRequest.Validate()``
    (policy.go lines 313-322).  Identical constraints to
    ``GetPolicyRequest``.

    Args:
        request: A ``GetPolicyHistoryRequest`` instance with ``policy_id``,
                 ``contract_id``, ``policy_set_id``, and ``network``
                 attributes.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors = {}
    if not request.policy_id:
        errors["PolicyID"] = "cannot be blank"
    if not request.contract_id:
        errors["ContractID"] = "cannot be blank"
    if not request.policy_set_id:
        errors["PolicySetID"] = "cannot be blank"
    errors["Network"] = _validate_policy_network(request.network)
    return parse_validation_errors(errors)


def validate_rollback_policy_request(request) -> str | None:
    """Validate RollbackPolicyRequest fields.

    Mirrors Go ``RollbackPolicyRequest.Validate()``
    (policy.go lines 325-334).  Identical constraints to
    ``GetPolicyRequest``.

    Args:
        request: A ``RollbackPolicyRequest`` instance with ``policy_id``,
                 ``contract_id``, ``policy_set_id``, and ``network``
                 attributes.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors = {}
    if not request.policy_id:
        errors["PolicyID"] = "cannot be blank"
    if not request.contract_id:
        errors["ContractID"] = "cannot be blank"
    if not request.policy_set_id:
        errors["PolicySetID"] = "cannot be blank"
    errors["Network"] = _validate_policy_network(request.network)
    return parse_validation_errors(errors)


# -------------------------------------------------------------------
# PolicySet request validations (from policyset.go)
# -------------------------------------------------------------------


def validate_list_policy_sets_request(request) -> str | None:
    """Validate ListPolicySetsRequest fields.

    Mirrors Go ``ListPolicySetsRequest.Validate()``
    (policyset.go lines 128-135).

    Note: ``network`` is NOT required — an empty string means
    "both networks".  Only a non-empty value that is not ``staging``
    or ``production`` triggers an error.

    Args:
        request: A ``ListPolicySetsRequest`` instance with ``contract_id``
                 and ``network`` attributes.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors = {}
    if not request.contract_id:
        errors["ContractID"] = "cannot be blank"
    errors["Network"] = _validate_policy_set_network(request.network)
    return parse_validation_errors(errors)


def validate_get_policy_set_request(request) -> str | None:
    """Validate GetPolicySetRequest fields.

    Mirrors Go ``GetPolicySetRequest.Validate()``
    (policyset.go lines 138-146).

    Args:
        request: A ``GetPolicySetRequest`` instance with ``policy_set_id``,
                 ``contract_id``, and ``network`` attributes.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors = {}
    if not request.policy_set_id:
        errors["PolicySetID"] = "cannot be blank"
    if not request.contract_id:
        errors["ContractID"] = "cannot be blank"
    errors["Network"] = _validate_policy_set_network(request.network)
    return parse_validation_errors(errors)


def validate_create_policy_set_request(request) -> str | None:
    """Validate CreatePolicySetRequest fields.

    Mirrors Go ``CreatePolicySetRequest.Validate()``
    (policyset.go lines 149-160).

    Args:
        request: A ``CreatePolicySetRequest`` instance with ``contract_id``,
                 ``name``, ``region``, ``type``, and ``default_policy``
                 attributes.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors = {}
    if not request.contract_id:
        errors["ContractID"] = "cannot be blank"
    if not request.name:
        errors["Name"] = "cannot be blank"
    errors["Region"] = _validate_region(request.region)
    errors["Type"] = _validate_media_type(request.type)

    # Delegate to the appropriate PolicyInput validator when present.
    # Mirrors Go: "DefaultPolicy": validation.Validate(v.DefaultPolicy)
    default_policy_err = None
    if request.default_policy is not None:
        if hasattr(request.default_policy, "serve_stale_duration"):
            default_policy_err = validate_policy_input_image(
                request.default_policy
            )
        else:
            default_policy_err = validate_policy_input_video(
                request.default_policy
            )
    errors["DefaultPolicy"] = default_policy_err

    return parse_validation_errors(errors)


def validate_update_policy_set_request(request) -> str | None:
    """Validate UpdatePolicySetRequest fields.

    Mirrors Go ``UpdatePolicySetRequest.Validate()``
    (policyset.go lines 163-171).

    Args:
        request: An ``UpdatePolicySetRequest`` instance with
                 ``contract_id``, ``name``, and ``region`` attributes.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors = {}
    if not request.contract_id:
        errors["ContractID"] = "cannot be blank"
    if not request.name:
        errors["Name"] = "cannot be blank"
    errors["Region"] = _validate_region(request.region)
    return parse_validation_errors(errors)


def validate_delete_policy_set_request(request) -> str | None:
    """Validate DeletePolicySetRequest fields.

    Mirrors Go ``DeletePolicySetRequest.Validate()``
    (policyset.go lines 174-180).

    Args:
        request: A ``DeletePolicySetRequest`` instance with
                 ``policy_set_id`` and ``contract_id`` attributes.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors = {}
    if not request.policy_set_id:
        errors["PolicySetID"] = "cannot be blank"
    if not request.contract_id:
        errors["ContractID"] = "cannot be blank"
    return parse_validation_errors(errors)


# -------------------------------------------------------------------
# Policy input validations (from policy.go)
# -------------------------------------------------------------------


def validate_policy_input_image(policy) -> str | None:
    """Validate PolicyInputImage fields.

    Mirrors Go ``PolicyInputImage.Validate()``
    (policy.go lines 182-199).

    Validates numeric range constraints for ``rollout_duration``
    (3600–604800 seconds) and ``serve_stale_duration``
    (0–2 592 000 seconds).  Sub-type delegation (breakpoints, hosts,
    output, transformations, variables) is performed by the ozzo
    ``validation.Validate`` / ``validation.Each`` calls in Go; here
    those produce ``None`` (no error) and are filtered out by
    ``parse_validation_errors``.

    Args:
        policy: A ``PolicyInputImage`` instance.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {}
    errors["RolloutDuration"] = _validate_rollout_duration(
        policy.rollout_duration
    )
    errors["ServeStaleDuration"] = _validate_serve_stale_duration(
        policy.serve_stale_duration
    )
    return parse_validation_errors(errors)


def validate_policy_input_video(policy) -> str | None:
    """Validate PolicyInputVideo fields.

    Mirrors Go ``PolicyInputVideo.Validate()``
    (policy.go lines 202-213).

    Validates the numeric range constraint for ``rollout_duration``
    (3600–604800 seconds).  Sub-type delegation (breakpoints, hosts,
    output, variables) is performed by the ozzo ``validation.Validate``
    / ``validation.Each`` calls in Go; here those produce ``None``
    (no error) and are filtered out by ``parse_validation_errors``.

    Args:
        policy: A ``PolicyInputVideo`` instance.

    Returns:
        Formatted error string, or ``None`` if valid.
    """
    errors: dict[str, str | None] = {}
    errors["RolloutDuration"] = _validate_rollout_duration(
        policy.rollout_duration
    )
    return parse_validation_errors(errors)
