# pylint: disable=too-many-lines
"""Request validation functions for the Imaging API."""

from akamai.edgegrid.imaging import models
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


# ============================================================================
# Generated transformation type validators
# Ported from Go policy.gen.go Validate() methods (85 validators)
# ============================================================================


def validate_append(obj) -> str | None:
    """Validate Append fields.

    Mirrors Go ``Append.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.image:
        errors["Image"] = "cannot be blank"
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.APPEND_TRANSFORMATION_APPEND,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_append_gravity_priority_variable_inline(obj) -> str | None:
    """Validate AppendGravityPriorityVariableInline fields.

    Mirrors Go ``AppendGravityPriorityVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.value is not None and obj.value not in (
        models.APPEND_GRAVITY_PRIORITY_HORIZONTAL,
        models.APPEND_GRAVITY_PRIORITY_VERTICAL,
    ):
        errors["Value"] = (
            f"value '{obj.value}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_aspect_crop(obj) -> str | None:
    """Validate AspectCrop fields.

    Mirrors Go ``AspectCrop.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.ASPECT_CROP_TRANSFORMATION_ASPECT_CROP,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_background_color(obj) -> str | None:
    """Validate BackgroundColor fields.

    Mirrors Go ``BackgroundColor.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.color:
        errors["Color"] = "cannot be blank"
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.BACKGROUND_COLOR_TRANSFORMATION_BACKGROUND_COLOR,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_blur(obj) -> str | None:
    """Validate Blur fields.

    Mirrors Go ``Blur.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.BLUR_TRANSFORMATION_BLUR,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_boolean_variable_inline(obj) -> str | None:  # pylint: disable=unused-argument
    """Validate BooleanVariableInline fields.

    Mirrors Go ``BooleanVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    return parse_validation_errors(errors)


def validate_box_image_type(obj) -> str | None:
    """Validate BoxImageType fields.

    Mirrors Go ``BoxImageType.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.type:
        errors["Type"] = "cannot be blank"
    elif obj.type not in (models.BOX_IMAGE_TYPE_TYPE,):
        errors["Type"] = (
            f"value '{obj.type}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_box_image_type_post(obj) -> str | None:
    """Validate BoxImageTypePost fields.

    Mirrors Go ``BoxImageTypePost.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.type:
        errors["Type"] = "cannot be blank"
    elif obj.type not in (models.BOX_IMAGE_TYPE_POST_TYPE,):
        errors["Type"] = (
            f"value '{obj.type}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_breakpoints(obj) -> str | None:  # pylint: disable=unused-argument
    """Validate Breakpoints fields.

    Mirrors Go ``Breakpoints.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    return parse_validation_errors(errors)


def validate_chroma_key(obj) -> str | None:
    """Validate ChromaKey fields.

    Mirrors Go ``ChromaKey.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.CHROMA_KEY_TRANSFORMATION_CHROMA_KEY,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_circle_image_type(obj) -> str | None:
    """Validate CircleImageType fields.

    Mirrors Go ``CircleImageType.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.type:
        errors["Type"] = "cannot be blank"
    elif obj.type not in (models.CIRCLE_IMAGE_TYPE_TYPE,):
        errors["Type"] = (
            f"value '{obj.type}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_circle_image_type_post(obj) -> str | None:
    """Validate CircleImageTypePost fields.

    Mirrors Go ``CircleImageTypePost.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.type:
        errors["Type"] = "cannot be blank"
    elif obj.type not in (models.CIRCLE_IMAGE_TYPE_POST_TYPE,):
        errors["Type"] = (
            f"value '{obj.type}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_circle_shape_type(obj) -> str | None:
    """Validate CircleShapeType fields.

    Mirrors Go ``CircleShapeType.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.center:
        errors["Center"] = "cannot be blank"
    if not obj.radius:
        errors["Radius"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_composite(obj) -> str | None:
    """Validate Composite fields.

    Mirrors Go ``Composite.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.image:
        errors["Image"] = "cannot be blank"
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.COMPOSITE_TRANSFORMATION_COMPOSITE,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_composite_placement_variable_inline(obj) -> str | None:
    """Validate CompositePlacementVariableInline fields.

    Mirrors Go ``CompositePlacementVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.value is not None and obj.value not in (
        models.COMPOSITE_PLACEMENT_OVER,
        models.COMPOSITE_PLACEMENT_UNDER,
        models.COMPOSITE_PLACEMENT_MASK,
        models.COMPOSITE_PLACEMENT_STENCIL,
    ):
        errors["Value"] = (
            f"value '{obj.value}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_composite_post(obj) -> str | None:
    """Validate CompositePost fields.

    Mirrors Go ``CompositePost.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.image:
        errors["Image"] = "cannot be blank"
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.COMPOSITE_POST_TRANSFORMATION_COMPOSITE,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_composite_post_placement_variable_inline(obj) -> str | None:
    """Validate CompositePostPlacementVariableInline fields.

    Mirrors Go ``CompositePostPlacementVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.value is not None and obj.value not in (
        models.COMPOSITE_POST_PLACEMENT_OVER,
        models.COMPOSITE_POST_PLACEMENT_UNDER,
        models.COMPOSITE_POST_PLACEMENT_MASK,
        models.COMPOSITE_POST_PLACEMENT_STENCIL,
    ):
        errors["Value"] = (
            f"value '{obj.value}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_composite_post_scale_dimension_variable_inline(obj) -> str | None:
    """Validate CompositePostScaleDimensionVariableInline fields.

    Mirrors Go ``CompositePostScaleDimensionVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.value is not None and obj.value not in (
        models.COMPOSITE_POST_SCALE_DIMENSION_WIDTH,
        models.COMPOSITE_POST_SCALE_DIMENSION_HEIGHT,
    ):
        errors["Value"] = (
            f"value '{obj.value}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_composite_scale_dimension_variable_inline(obj) -> str | None:
    """Validate CompositeScaleDimensionVariableInline fields.

    Mirrors Go ``CompositeScaleDimensionVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.value is not None and obj.value not in (
        models.COMPOSITE_SCALE_DIMENSION_WIDTH,
        models.COMPOSITE_SCALE_DIMENSION_HEIGHT,
    ):
        errors["Value"] = (
            f"value '{obj.value}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_compound(obj) -> str | None:
    """Validate Compound fields.

    Mirrors Go ``Compound.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.COMPOUND_TRANSFORMATION_COMPOUND,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_compound_post(obj) -> str | None:
    """Validate CompoundPost fields.

    Mirrors Go ``CompoundPost.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.COMPOUND_POST_TRANSFORMATION_COMPOUND,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_contrast(obj) -> str | None:
    """Validate Contrast fields.

    Mirrors Go ``Contrast.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.CONTRAST_TRANSFORMATION_CONTRAST,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_crop(obj) -> str | None:
    """Validate Crop fields.

    Mirrors Go ``Crop.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.height:
        errors["Height"] = "cannot be blank"
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.CROP_TRANSFORMATION_CROP,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    if not obj.width:
        errors["Width"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_enum_options(obj) -> str | None:
    """Validate EnumOptions fields.

    Mirrors Go ``EnumOptions.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.id:
        errors["ID"] = "cannot be blank"
    if not obj.value:
        errors["Value"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_face_crop(obj) -> str | None:
    """Validate FaceCrop fields.

    Mirrors Go ``FaceCrop.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.height:
        errors["Height"] = "cannot be blank"
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.FACE_CROP_TRANSFORMATION_FACE_CROP,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    if not obj.width:
        errors["Width"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_face_crop_algorithm_variable_inline(obj) -> str | None:
    """Validate FaceCropAlgorithmVariableInline fields.

    Mirrors Go ``FaceCropAlgorithmVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.value is not None and obj.value not in (
        models.FACE_CROP_ALGORITHM_CASCADE,
        models.FACE_CROP_ALGORITHM_DNN,
    ):
        errors["Value"] = (
            f"value '{obj.value}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_face_crop_focus_variable_inline(obj) -> str | None:
    """Validate FaceCropFocusVariableInline fields.

    Mirrors Go ``FaceCropFocusVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.value is not None and obj.value not in (
        models.FACE_CROP_FOCUS_ALL_FACES,
        models.FACE_CROP_FOCUS_BIGGEST_FACE,
    ):
        errors["Value"] = (
            f"value '{obj.value}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_face_crop_style_variable_inline(obj) -> str | None:
    """Validate FaceCropStyleVariableInline fields.

    Mirrors Go ``FaceCropStyleVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.value is not None and obj.value not in (
        models.FACE_CROP_STYLE_CROP,
        models.FACE_CROP_STYLE_FILL,
        models.FACE_CROP_STYLE_ZOOM,
    ):
        errors["Value"] = (
            f"value '{obj.value}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_feature_crop(obj) -> str | None:
    """Validate FeatureCrop fields.

    Mirrors Go ``FeatureCrop.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.height:
        errors["Height"] = "cannot be blank"
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.FEATURE_CROP_TRANSFORMATION_FEATURE_CROP,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    if not obj.width:
        errors["Width"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_feature_crop_style_variable_inline(obj) -> str | None:
    """Validate FeatureCropStyleVariableInline fields.

    Mirrors Go ``FeatureCropStyleVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.value is not None and obj.value not in (
        models.FEATURE_CROP_STYLE_CROP,
        models.FEATURE_CROP_STYLE_FILL,
        models.FEATURE_CROP_STYLE_ZOOM,
    ):
        errors["Value"] = (
            f"value '{obj.value}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_fit_and_fill(obj) -> str | None:
    """Validate FitAndFill fields.

    Mirrors Go ``FitAndFill.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.height:
        errors["Height"] = "cannot be blank"
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.FIT_AND_FILL_TRANSFORMATION_FIT_AND_FILL,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    if not obj.width:
        errors["Width"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_goop(obj) -> str | None:
    """Validate Goop fields.

    Mirrors Go ``Goop.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.GOOP_TRANSFORMATION_GOOP,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_gravity_post_variable_inline(obj) -> str | None:
    """Validate GravityPostVariableInline fields.

    Mirrors Go ``GravityPostVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.value is not None and obj.value not in (
        models.GRAVITY_POST_NORTH,
        models.GRAVITY_POST_NORTH_EAST,
        models.GRAVITY_POST_NORTH_WEST,
        models.GRAVITY_POST_SOUTH,
        models.GRAVITY_POST_SOUTH_EAST,
        models.GRAVITY_POST_SOUTH_WEST,
        models.GRAVITY_POST_CENTER,
        models.GRAVITY_POST_EAST,
        models.GRAVITY_POST_WEST,
    ):
        errors["Value"] = (
            f"value '{obj.value}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_gravity_variable_inline(obj) -> str | None:
    """Validate GravityVariableInline fields.

    Mirrors Go ``GravityVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.value is not None and obj.value not in (
        models.GRAVITY_NORTH,
        models.GRAVITY_NORTH_EAST,
        models.GRAVITY_NORTH_WEST,
        models.GRAVITY_SOUTH,
        models.GRAVITY_SOUTH_EAST,
        models.GRAVITY_SOUTH_WEST,
        models.GRAVITY_CENTER,
        models.GRAVITY_EAST,
        models.GRAVITY_WEST,
    ):
        errors["Value"] = (
            f"value '{obj.value}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_grayscale(obj) -> str | None:
    """Validate Grayscale fields.

    Mirrors Go ``Grayscale.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.GRAYSCALE_TRANSFORMATION_GRAYSCALE,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_grayscale_type_variable_inline(obj) -> str | None:
    """Validate GrayscaleTypeVariableInline fields.

    Mirrors Go ``GrayscaleTypeVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.value is not None and obj.value not in (
        models.GRAYSCALE_TYPE_REC601,
        models.GRAYSCALE_TYPE_REC709,
        models.GRAYSCALE_TYPE_BRIGHTNESS,
        models.GRAYSCALE_TYPE_LIGHTNESS,
    ):
        errors["Value"] = (
            f"value '{obj.value}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_hsl(obj) -> str | None:
    """Validate HSL fields.

    Mirrors Go ``HSL.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.HSL_TRANSFORMATION_HSL,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_hsv(obj) -> str | None:
    """Validate HSV fields.

    Mirrors Go ``HSV.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.HSV_TRANSFORMATION_HSV,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_if_dimension(obj) -> str | None:
    """Validate IfDimension fields.

    Mirrors Go ``IfDimension.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.IF_DIMENSION_TRANSFORMATION_IF_DIMENSION,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    if not obj.value:
        errors["Value"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_if_dimension_dimension_variable_inline(obj) -> str | None:
    """Validate IfDimensionDimensionVariableInline fields.

    Mirrors Go ``IfDimensionDimensionVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.value is not None and obj.value not in (
        models.IF_DIMENSION_DIMENSION_WIDTH,
        models.IF_DIMENSION_DIMENSION_HEIGHT,
        models.IF_DIMENSION_DIMENSION_BOTH,
    ):
        errors["Value"] = (
            f"value '{obj.value}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_if_dimension_post(obj) -> str | None:
    """Validate IfDimensionPost fields.

    Mirrors Go ``IfDimensionPost.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.IF_DIMENSION_POST_TRANSFORMATION_IF_DIMENSION,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    if not obj.value:
        errors["Value"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_if_dimension_post_dimension_variable_inline(obj) -> str | None:
    """Validate IfDimensionPostDimensionVariableInline fields.

    Mirrors Go ``IfDimensionPostDimensionVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.value is not None and obj.value not in (
        models.IF_DIMENSION_POST_DIMENSION_WIDTH,
        models.IF_DIMENSION_POST_DIMENSION_HEIGHT,
        models.IF_DIMENSION_POST_DIMENSION_BOTH,
    ):
        errors["Value"] = (
            f"value '{obj.value}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_if_orientation(obj) -> str | None:
    """Validate IfOrientation fields.

    Mirrors Go ``IfOrientation.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.IF_ORIENTATION_TRANSFORMATION_IF_ORIENTATION,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_if_orientation_post(obj) -> str | None:
    """Validate IfOrientationPost fields.

    Mirrors Go ``IfOrientationPost.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.IF_ORIENTATION_POST_TRANSFORMATION_IF_ORIENTATION,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_im_query(obj) -> str | None:
    """Validate ImQuery fields.

    Mirrors Go ``ImQuery.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.allowed_transformations:
        errors["AllowedTransformations"] = "cannot be blank"
    elif obj.allowed_transformations not in (
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_APPEND,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_ASPECT_CROP,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_BACKGROUND_COLOR,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_BLUR,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_COMPOSITE,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_CONTRAST,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_CROP,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_CHROMA_KEY,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_FACE_CROP,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_FEATURE_CROP,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_FIT_AND_FILL,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_GOOP,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_GRAYSCALE,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_HSL,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_HSV,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_MAX_COLORS,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_MIRROR,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_MONO_HUE,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_OPACITY,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_REGION_OF_INTEREST_CROP,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_RELATIVE_CROP,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_REMOVE_COLOR,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_RESIZE,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_ROTATE,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_SCALE,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_SHEAR,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_TRIM,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_UNSHARP_MASK,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_IF_DIMENSION,
        models.IM_QUERY_ALLOWED_TRANSFORMATIONS_IF_ORIENTATION,
    ):
        errors["AllowedTransformations"] = (
            f"value '{obj.allowed_transformations}' is invalid"
        )
    if not obj.query:
        errors["Query"] = "cannot be blank"
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.IM_QUERY_TRANSFORMATION_IM_QUERY,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_integer_variable_inline(obj) -> str | None:  # pylint: disable=unused-argument
    """Validate IntegerVariableInline fields.

    Mirrors Go ``IntegerVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    return parse_validation_errors(errors)


def validate_max_colors(obj) -> str | None:
    """Validate MaxColors fields.

    Mirrors Go ``MaxColors.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.colors:
        errors["Colors"] = "cannot be blank"
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.MAX_COLORS_TRANSFORMATION_MAX_COLORS,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_mirror(obj) -> str | None:
    """Validate Mirror fields.

    Mirrors Go ``Mirror.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.MIRROR_TRANSFORMATION_MIRROR,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_mono_hue(obj) -> str | None:
    """Validate MonoHue fields.

    Mirrors Go ``MonoHue.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.MONO_HUE_TRANSFORMATION_MONO_HUE,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_number_variable_inline(obj) -> str | None:  # pylint: disable=unused-argument
    """Validate NumberVariableInline fields.

    Mirrors Go ``NumberVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    return parse_validation_errors(errors)


def validate_opacity(obj) -> str | None:
    """Validate Opacity fields.

    Mirrors Go ``Opacity.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.opacity:
        errors["Opacity"] = "cannot be blank"
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.OPACITY_TRANSFORMATION_OPACITY,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_output_image(obj) -> str | None:
    """Validate OutputImage fields.

    Mirrors Go ``OutputImage.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.allowed_formats is not None and obj.allowed_formats not in (
        models.OUTPUT_IMAGE_ALLOWED_FORMATS_GIF,
        models.OUTPUT_IMAGE_ALLOWED_FORMATS_JPEG,
        models.OUTPUT_IMAGE_ALLOWED_FORMATS_PNG,
        models.OUTPUT_IMAGE_ALLOWED_FORMATS_WEBP,
        models.OUTPUT_IMAGE_ALLOWED_FORMATS_JPEGXR,
        models.OUTPUT_IMAGE_ALLOWED_FORMATS_JPEG2000,
        models.OUTPUT_IMAGE_ALLOWED_FORMATS_AVIF,
    ):
        errors["AllowedFormats"] = (
            f"value '{obj.allowed_formats}' is invalid"
        )
    if obj.forced_formats is not None and obj.forced_formats not in (
        models.OUTPUT_IMAGE_FORCED_FORMATS_GIF,
        models.OUTPUT_IMAGE_FORCED_FORMATS_JPEG,
        models.OUTPUT_IMAGE_FORCED_FORMATS_PNG,
        models.OUTPUT_IMAGE_FORCED_FORMATS_WEBP,
        models.OUTPUT_IMAGE_FORCED_FORMATS_JPEGXR,
        models.OUTPUT_IMAGE_FORCED_FORMATS_JPEG2000,
        models.OUTPUT_IMAGE_FORCED_FORMATS_AVIF,
    ):
        errors["ForcedFormats"] = (
            f"value '{obj.forced_formats}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_output_image_perceptual_quality_variable_inline(obj) -> str | None:
    """Validate OutputImagePerceptualQualityVariableInline fields.

    Mirrors Go ``OutputImagePerceptualQualityVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.value is not None and obj.value not in (
        models.OUTPUT_IMAGE_PERCEPTUAL_QUALITY_HIGH,
        models.OUTPUT_IMAGE_PERCEPTUAL_QUALITY_MEDIUM_HIGH,
        models.OUTPUT_IMAGE_PERCEPTUAL_QUALITY_MEDIUM,
        models.OUTPUT_IMAGE_PERCEPTUAL_QUALITY_MEDIUM_LOW,
        models.OUTPUT_IMAGE_PERCEPTUAL_QUALITY_LOW,
    ):
        errors["Value"] = (
            f"value '{obj.value}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_point_shape_type(obj) -> str | None:
    """Validate PointShapeType fields.

    Mirrors Go ``PointShapeType.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.x:
        errors["X"] = "cannot be blank"
    if not obj.y:
        errors["Y"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_policy_output_image(obj) -> str | None:
    """Validate PolicyOutputImage fields.

    Mirrors Go ``PolicyOutputImage.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.date_created:
        errors["DateCreated"] = "cannot be blank"
    if not obj.id:
        errors["ID"] = "cannot be blank"
    if not obj.previous_version:
        errors["PreviousVersion"] = "cannot be blank"
    if not obj.rollout_info:
        errors["RolloutInfo"] = "cannot be blank"
    if not obj.user:
        errors["User"] = "cannot be blank"
    if not obj.version:
        errors["Version"] = "cannot be blank"
    if obj.video is not None and obj.video not in (models.POLICY_OUTPUT_IMAGE_VIDEO,):
        errors["Video"] = (
            f"value '{obj.video}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_polygon_shape_type(obj) -> str | None:
    """Validate PolygonShapeType fields.

    Mirrors Go ``PolygonShapeType.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.points:
        errors["Points"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_query_variable_inline(obj) -> str | None:
    """Validate QueryVariableInline fields.

    Mirrors Go ``QueryVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.name:
        errors["Name"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_rectangle_shape_type(obj) -> str | None:
    """Validate RectangleShapeType fields.

    Mirrors Go ``RectangleShapeType.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.anchor:
        errors["Anchor"] = "cannot be blank"
    if not obj.height:
        errors["Height"] = "cannot be blank"
    if not obj.width:
        errors["Width"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_region_of_interest_crop(obj) -> str | None:
    """Validate RegionOfInterestCrop fields.

    Mirrors Go ``RegionOfInterestCrop.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.height:
        errors["Height"] = "cannot be blank"
    if not obj.region_of_interest:
        errors["RegionOfInterest"] = "cannot be blank"
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (
        models.REGION_OF_INTEREST_CROP_TRANSFORMATION_REGION_OF_INTEREST_CROP,
    ):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    if not obj.width:
        errors["Width"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_region_of_interest_crop_style_variable_inline(obj) -> str | None:
    """Validate RegionOfInterestCropStyleVariableInline fields.

    Mirrors Go ``RegionOfInterestCropStyleVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.value is not None and obj.value not in (
        models.REGION_OF_INTEREST_CROP_STYLE_CROP,
        models.REGION_OF_INTEREST_CROP_STYLE_FILL,
        models.REGION_OF_INTEREST_CROP_STYLE_ZOOM,
    ):
        errors["Value"] = (
            f"value '{obj.value}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_relative_crop(obj) -> str | None:
    """Validate RelativeCrop fields.

    Mirrors Go ``RelativeCrop.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.RELATIVE_CROP_TRANSFORMATION_RELATIVE_CROP,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_remove_color(obj) -> str | None:
    """Validate RemoveColor fields.

    Mirrors Go ``RemoveColor.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.color:
        errors["Color"] = "cannot be blank"
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.REMOVE_COLOR_TRANSFORMATION_REMOVE_COLOR,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_resize(obj) -> str | None:
    """Validate Resize fields.

    Mirrors Go ``Resize.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.RESIZE_TRANSFORMATION_RESIZE,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_resize_aspect_variable_inline(obj) -> str | None:
    """Validate ResizeAspectVariableInline fields.

    Mirrors Go ``ResizeAspectVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.value is not None and obj.value not in (
        models.RESIZE_ASPECT_FIT,
        models.RESIZE_ASPECT_FILL,
        models.RESIZE_ASPECT_IGNORE,
    ):
        errors["Value"] = (
            f"value '{obj.value}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_resize_type_variable_inline(obj) -> str | None:
    """Validate ResizeTypeVariableInline fields.

    Mirrors Go ``ResizeTypeVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.value is not None and obj.value not in (
        models.RESIZE_TYPE_NORMAL,
        models.RESIZE_TYPE_UPSIZE,
        models.RESIZE_TYPE_DOWNSIZE,
    ):
        errors["Value"] = (
            f"value '{obj.value}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_rollout_info(obj) -> str | None:
    """Validate RolloutInfo fields.

    Mirrors Go ``RolloutInfo.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.end_time:
        errors["EndTime"] = "cannot be blank"
    if not obj.rollout_duration:
        errors["RolloutDuration"] = "cannot be blank"
    if not obj.start_time:
        errors["StartTime"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_rotate(obj) -> str | None:
    """Validate Rotate fields.

    Mirrors Go ``Rotate.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.degrees:
        errors["Degrees"] = "cannot be blank"
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.ROTATE_TRANSFORMATION_ROTATE,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_scale(obj) -> str | None:
    """Validate Scale fields.

    Mirrors Go ``Scale.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.height:
        errors["Height"] = "cannot be blank"
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.SCALE_TRANSFORMATION_SCALE,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    if not obj.width:
        errors["Width"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_shear(obj) -> str | None:
    """Validate Shear fields.

    Mirrors Go ``Shear.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.SHEAR_TRANSFORMATION_SHEAR,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_smart_crop(obj) -> str | None:
    """Validate SmartCrop fields.

    Mirrors Go ``SmartCrop.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.SMART_CROP_TRANSFORMATION_SMART_CROP,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_smart_crop_style_variable_inline(obj) -> str | None:
    """Validate SmartCropStyleVariableInline fields.

    Mirrors Go ``SmartCropStyleVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.value is not None and obj.value not in (
        models.SMART_CROP_STYLE_CROP,
        models.SMART_CROP_STYLE_FILL,
        models.SMART_CROP_STYLE_ZOOM,
    ):
        errors["Value"] = (
            f"value '{obj.value}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_string_variable_inline(obj) -> str | None:  # pylint: disable=unused-argument
    """Validate StringVariableInline fields.

    Mirrors Go ``StringVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    return parse_validation_errors(errors)


def validate_text_image_type(obj) -> str | None:
    """Validate TextImageType fields.

    Mirrors Go ``TextImageType.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.text:
        errors["Text"] = "cannot be blank"
    if not obj.type:
        errors["Type"] = "cannot be blank"
    elif obj.type not in (models.TEXT_IMAGE_TYPE_TYPE,):
        errors["Type"] = (
            f"value '{obj.type}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_text_image_type_post(obj) -> str | None:
    """Validate TextImageTypePost fields.

    Mirrors Go ``TextImageTypePost.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.text:
        errors["Text"] = "cannot be blank"
    if not obj.type:
        errors["Type"] = "cannot be blank"
    elif obj.type not in (models.TEXT_IMAGE_TYPE_POST_TYPE,):
        errors["Type"] = (
            f"value '{obj.type}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_trim(obj) -> str | None:
    """Validate Trim fields.

    Mirrors Go ``Trim.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.TRIM_TRANSFORMATION_TRIM,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_url_image_type(obj) -> str | None:
    """Validate URLImageType fields.

    Mirrors Go ``URLImageType.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.type is not None and obj.type not in (models.URL_IMAGE_TYPE_TYPE,):
        errors["Type"] = (
            f"value '{obj.type}' is invalid"
        )
    if not obj.url:
        errors["URL"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_url_image_type_post(obj) -> str | None:
    """Validate URLImageTypePost fields.

    Mirrors Go ``URLImageTypePost.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.type is not None and obj.type not in (models.URL_IMAGE_TYPE_POST_TYPE,):
        errors["Type"] = (
            f"value '{obj.type}' is invalid"
        )
    if not obj.url:
        errors["URL"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_union_shape_type(obj) -> str | None:
    """Validate UnionShapeType fields.

    Mirrors Go ``UnionShapeType.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.shapes:
        errors["Shapes"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_unsharp_mask(obj) -> str | None:
    """Validate UnsharpMask fields.

    Mirrors Go ``UnsharpMask.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.transformation:
        errors["Transformation"] = "cannot be blank"
    elif obj.transformation not in (models.UNSHARP_MASK_TRANSFORMATION_UNSHARP_MASK,):
        errors["Transformation"] = (
            f"value '{obj.transformation}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_variable(obj) -> str | None:
    """Validate Variable fields.

    Mirrors Go ``Variable.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.default_value:
        errors["DefaultValue"] = "cannot be blank"
    if not obj.name:
        errors["Name"] = "cannot be blank"
    if not obj.type:
        errors["Type"] = "cannot be blank"
    elif obj.type not in (
        models.VARIABLE_TYPE_BOOL,
        models.VARIABLE_TYPE_NUMBER,
        models.VARIABLE_TYPE_URL,
        models.VARIABLE_TYPE_COLOR,
        models.VARIABLE_TYPE_GRAVITY,
        models.VARIABLE_TYPE_PLACEMENT,
        models.VARIABLE_TYPE_SCALE_DIMENSION,
        models.VARIABLE_TYPE_GRAYSCALE_TYPE,
        models.VARIABLE_TYPE_ASPECT,
        models.VARIABLE_TYPE_RESIZE_TYPE,
        models.VARIABLE_TYPE_DIMENSION,
        models.VARIABLE_TYPE_PERCEPTUAL_QUALITY,
        models.VARIABLE_TYPE_STRING,
        models.VARIABLE_TYPE_FOCUS,
    ):
        errors["Type"] = (
            f"value '{obj.type}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_variable_inline(obj) -> str | None:
    """Validate VariableInline fields.

    Mirrors Go ``VariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.var:
        errors["Var"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_output_video(obj) -> str | None:  # pylint: disable=unused-argument
    """Validate OutputVideo fields.

    Mirrors Go ``OutputVideo.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    return parse_validation_errors(errors)


def validate_output_video_perceptual_quality_variable_inline(obj) -> str | None:
    """Validate OutputVideoPerceptualQualityVariableInline fields.

    Mirrors Go ``OutputVideoPerceptualQualityVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.value is not None and obj.value not in (
        models.OUTPUT_VIDEO_PERCEPTUAL_QUALITY_HIGH,
        models.OUTPUT_VIDEO_PERCEPTUAL_QUALITY_MEDIUM_HIGH,
        models.OUTPUT_VIDEO_PERCEPTUAL_QUALITY_MEDIUM,
        models.OUTPUT_VIDEO_PERCEPTUAL_QUALITY_MEDIUM_LOW,
        models.OUTPUT_VIDEO_PERCEPTUAL_QUALITY_LOW,
    ):
        errors["Value"] = (
            f"value '{obj.value}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_output_video_video_adaptive_quality_variable_inline(obj) -> str | None:
    """Validate OutputVideoVideoAdaptiveQualityVariableInline fields.

    Mirrors Go ``OutputVideoVideoAdaptiveQualityVariableInline.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if obj.value is not None and obj.value not in (
        models.OUTPUT_VIDEO_VIDEO_ADAPTIVE_QUALITY_HIGH,
        models.OUTPUT_VIDEO_VIDEO_ADAPTIVE_QUALITY_MEDIUM_HIGH,
        models.OUTPUT_VIDEO_VIDEO_ADAPTIVE_QUALITY_MEDIUM,
        models.OUTPUT_VIDEO_VIDEO_ADAPTIVE_QUALITY_MEDIUM_LOW,
        models.OUTPUT_VIDEO_VIDEO_ADAPTIVE_QUALITY_LOW,
    ):
        errors["Value"] = (
            f"value '{obj.value}' is invalid"
        )
    return parse_validation_errors(errors)


def validate_policy_output_video(obj) -> str | None:
    """Validate PolicyOutputVideo fields.

    Mirrors Go ``PolicyOutputVideo.Validate()`` from policy.gen.go.
    """
    errors: dict[str, str | None] = {}
    if not obj.date_created:
        errors["DateCreated"] = "cannot be blank"
    if not obj.id:
        errors["ID"] = "cannot be blank"
    if not obj.previous_version:
        errors["PreviousVersion"] = "cannot be blank"
    if not obj.rollout_info:
        errors["RolloutInfo"] = "cannot be blank"
    if not obj.user:
        errors["User"] = "cannot be blank"
    if not obj.version:
        errors["Version"] = "cannot be blank"
    if obj.video is not None and obj.video not in (models.POLICY_OUTPUT_VIDEO_VIDEO,):
        errors["Video"] = (
            f"value '{obj.video}' is invalid"
        )
    return parse_validation_errors(errors)
