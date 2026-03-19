"""Request/response models for the Imaging API"""
# pylint: disable=too-many-lines,too-many-instance-attributes
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Field name mapping: Python snake_case <-> JSON camelCase
# ---------------------------------------------------------------------------
_SNAKE_TO_CAMEL: dict[str, str] = {}
_CAMEL_TO_SNAKE: dict[str, str] = {}


def _to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    cached = _SNAKE_TO_CAMEL.get(name)
    if cached is not None:
        return cached
    parts = name.split("_")
    result = parts[0] + "".join(p.capitalize() for p in parts[1:])
    _SNAKE_TO_CAMEL[name] = result
    return result


def _to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    cached = _CAMEL_TO_SNAKE.get(name)
    if cached is not None:
        return cached
    result = re.sub(r"([A-Z])", r"_\1", name).lower().lstrip("_")
    _CAMEL_TO_SNAKE[name] = result
    return result


# ===================================================================
# Policy Network constants (from policy.go)
# ===================================================================
POLICY_NETWORK_STAGING: str = "staging"
POLICY_NETWORK_PRODUCTION: str = "production"

# ===================================================================
# PolicySet Network constants (from policyset.go)
# ===================================================================
NETWORK_STAGING: str = "staging"
NETWORK_PRODUCTION: str = "production"
NETWORK_BOTH: str = ""

# ===================================================================
# Region constants (from policyset.go)
# ===================================================================
REGION_US: str = "US"
REGION_EMEA: str = "EMEA"
REGION_ASIA: str = "ASIA"
REGION_AUSTRALIA: str = "AUSTRALIA"
REGION_JAPAN: str = "JAPAN"
REGION_CHINA: str = "CHINA"

# ===================================================================
# MediaType constants (from policyset.go)
# ===================================================================
TYPE_IMAGE: str = "IMAGE"
TYPE_VIDEO: str = "VIDEO"

# ===================================================================
# AppendGravityPriority constants (from policy.gen.go)
# ===================================================================
APPEND_GRAVITY_PRIORITY_HORIZONTAL: str = "horizontal"
APPEND_GRAVITY_PRIORITY_VERTICAL: str = "vertical"

# ===================================================================
# Transformation name constants (from policy.gen.go)
# ===================================================================
APPEND_TRANSFORMATION_APPEND: str = "Append"
ASPECT_CROP_TRANSFORMATION_ASPECT_CROP: str = "AspectCrop"
BACKGROUND_COLOR_TRANSFORMATION_BACKGROUND_COLOR: str = "BackgroundColor"
BLUR_TRANSFORMATION_BLUR: str = "Blur"
CHROMA_KEY_TRANSFORMATION_CHROMA_KEY: str = "ChromaKey"
COMPOSITE_TRANSFORMATION_COMPOSITE: str = "Composite"
COMPOSITE_POST_TRANSFORMATION_COMPOSITE: str = "Composite"
COMPOUND_TRANSFORMATION_COMPOUND: str = "Compound"
COMPOUND_POST_TRANSFORMATION_COMPOUND: str = "Compound"
CONTRAST_TRANSFORMATION_CONTRAST: str = "Contrast"
CROP_TRANSFORMATION_CROP: str = "Crop"
FACE_CROP_TRANSFORMATION_FACE_CROP: str = "FaceCrop"
FEATURE_CROP_TRANSFORMATION_FEATURE_CROP: str = "FeatureCrop"
FIT_AND_FILL_TRANSFORMATION_FIT_AND_FILL: str = "FitAndFill"
GOOP_TRANSFORMATION_GOOP: str = "Goop"
GRAYSCALE_TRANSFORMATION_GRAYSCALE: str = "Grayscale"
HSL_TRANSFORMATION_HSL: str = "HSL"
HSV_TRANSFORMATION_HSV: str = "HSV"
IF_DIMENSION_TRANSFORMATION_IF_DIMENSION: str = "IfDimension"
IF_DIMENSION_POST_TRANSFORMATION_IF_DIMENSION: str = "IfDimension"
IF_ORIENTATION_TRANSFORMATION_IF_ORIENTATION: str = "IfOrientation"
IF_ORIENTATION_POST_TRANSFORMATION_IF_ORIENTATION: str = "IfOrientation"
IM_QUERY_TRANSFORMATION_IM_QUERY: str = "ImQuery"
MAX_COLORS_TRANSFORMATION_MAX_COLORS: str = "MaxColors"
MIRROR_TRANSFORMATION_MIRROR: str = "Mirror"
MONO_HUE_TRANSFORMATION_MONO_HUE: str = "MonoHue"
OPACITY_TRANSFORMATION_OPACITY: str = "Opacity"
REGION_OF_INTEREST_CROP_TRANSFORMATION_REGION_OF_INTEREST_CROP: str = "RegionOfInterestCrop"
RELATIVE_CROP_TRANSFORMATION_RELATIVE_CROP: str = "RelativeCrop"
REMOVE_COLOR_TRANSFORMATION_REMOVE_COLOR: str = "RemoveColor"
RESIZE_TRANSFORMATION_RESIZE: str = "Resize"
ROTATE_TRANSFORMATION_ROTATE: str = "Rotate"
SCALE_TRANSFORMATION_SCALE: str = "Scale"
SHEAR_TRANSFORMATION_SHEAR: str = "Shear"
SMART_CROP_TRANSFORMATION_SMART_CROP: str = "SmartCrop"
TRIM_TRANSFORMATION_TRIM: str = "Trim"
UNSHARP_MASK_TRANSFORMATION_UNSHARP_MASK: str = "UnsharpMask"

# ===================================================================
# CompositePlacement constants (from policy.gen.go)
# ===================================================================
COMPOSITE_PLACEMENT_OVER: str = "Over"
COMPOSITE_PLACEMENT_UNDER: str = "Under"
COMPOSITE_PLACEMENT_MASK: str = "Mask"
COMPOSITE_PLACEMENT_STENCIL: str = "Stencil"

# ===================================================================
# CompositePostPlacement constants (from policy.gen.go)
# ===================================================================
COMPOSITE_POST_PLACEMENT_OVER: str = "Over"
COMPOSITE_POST_PLACEMENT_UNDER: str = "Under"
COMPOSITE_POST_PLACEMENT_MASK: str = "Mask"
COMPOSITE_POST_PLACEMENT_STENCIL: str = "Stencil"

# ===================================================================
# CompositeScaleDimension constants (from policy.gen.go)
# ===================================================================
COMPOSITE_SCALE_DIMENSION_WIDTH: str = "width"
COMPOSITE_SCALE_DIMENSION_HEIGHT: str = "height"

# ===================================================================
# CompositePostScaleDimension constants (from policy.gen.go)
# ===================================================================
COMPOSITE_POST_SCALE_DIMENSION_WIDTH: str = "width"
COMPOSITE_POST_SCALE_DIMENSION_HEIGHT: str = "height"

# ===================================================================
# FaceCropAlgorithm constants (from policy.gen.go)
# ===================================================================
FACE_CROP_ALGORITHM_CASCADE: str = "cascade"
FACE_CROP_ALGORITHM_DNN: str = "dnn"

# ===================================================================
# FaceCropFocus constants (from policy.gen.go)
# ===================================================================
FACE_CROP_FOCUS_ALL_FACES: str = "allFaces"
FACE_CROP_FOCUS_BIGGEST_FACE: str = "biggestFace"

# ===================================================================
# FaceCropStyle constants (from policy.gen.go)
# ===================================================================
FACE_CROP_STYLE_CROP: str = "crop"
FACE_CROP_STYLE_FILL: str = "fill"
FACE_CROP_STYLE_ZOOM: str = "zoom"

# ===================================================================
# FeatureCropStyle constants (from policy.gen.go)
# ===================================================================
FEATURE_CROP_STYLE_CROP: str = "crop"
FEATURE_CROP_STYLE_FILL: str = "fill"
FEATURE_CROP_STYLE_ZOOM: str = "zoom"

# ===================================================================
# Gravity constants (from policy.gen.go)
# ===================================================================
GRAVITY_NORTH: str = "North"
GRAVITY_NORTH_EAST: str = "NorthEast"
GRAVITY_NORTH_WEST: str = "NorthWest"
GRAVITY_SOUTH: str = "South"
GRAVITY_SOUTH_EAST: str = "SouthEast"
GRAVITY_SOUTH_WEST: str = "SouthWest"
GRAVITY_CENTER: str = "Center"
GRAVITY_EAST: str = "East"
GRAVITY_WEST: str = "West"

# ===================================================================
# GravityPost constants (from policy.gen.go)
# ===================================================================
GRAVITY_POST_NORTH: str = "North"
GRAVITY_POST_NORTH_EAST: str = "NorthEast"
GRAVITY_POST_NORTH_WEST: str = "NorthWest"
GRAVITY_POST_SOUTH: str = "South"
GRAVITY_POST_SOUTH_EAST: str = "SouthEast"
GRAVITY_POST_SOUTH_WEST: str = "SouthWest"
GRAVITY_POST_CENTER: str = "Center"
GRAVITY_POST_EAST: str = "East"
GRAVITY_POST_WEST: str = "West"

# ===================================================================
# GrayscaleType constants (from policy.gen.go)
# ===================================================================
GRAYSCALE_TYPE_REC601: str = "Rec601"
GRAYSCALE_TYPE_REC709: str = "Rec709"
GRAYSCALE_TYPE_BRIGHTNESS: str = "Brightness"
GRAYSCALE_TYPE_LIGHTNESS: str = "Lightness"

# ===================================================================
# IfDimensionDimension constants (from policy.gen.go)
# ===================================================================
IF_DIMENSION_DIMENSION_WIDTH: str = "width"
IF_DIMENSION_DIMENSION_HEIGHT: str = "height"
IF_DIMENSION_DIMENSION_BOTH: str = "both"

# ===================================================================
# IfDimensionPostDimension constants (from policy.gen.go)
# ===================================================================
IF_DIMENSION_POST_DIMENSION_WIDTH: str = "width"
IF_DIMENSION_POST_DIMENSION_HEIGHT: str = "height"
IF_DIMENSION_POST_DIMENSION_BOTH: str = "both"

# ===================================================================
# ImQueryAllowedTransformations constants (from policy.gen.go)
# ===================================================================
IM_QUERY_ALLOWED_TRANSFORMATIONS_APPEND: str = "Append"
IM_QUERY_ALLOWED_TRANSFORMATIONS_ASPECT_CROP: str = "AspectCrop"
IM_QUERY_ALLOWED_TRANSFORMATIONS_BACKGROUND_COLOR: str = "BackgroundColor"
IM_QUERY_ALLOWED_TRANSFORMATIONS_BLUR: str = "Blur"
IM_QUERY_ALLOWED_TRANSFORMATIONS_CHROMA_KEY: str = "ChromaKey"
IM_QUERY_ALLOWED_TRANSFORMATIONS_COMPOSITE: str = "Composite"
IM_QUERY_ALLOWED_TRANSFORMATIONS_COMPOUND: str = "Compound"
IM_QUERY_ALLOWED_TRANSFORMATIONS_CONTRAST: str = "Contrast"
IM_QUERY_ALLOWED_TRANSFORMATIONS_CROP: str = "Crop"
IM_QUERY_ALLOWED_TRANSFORMATIONS_FACE_CROP: str = "FaceCrop"
IM_QUERY_ALLOWED_TRANSFORMATIONS_FEATURE_CROP: str = "FeatureCrop"
IM_QUERY_ALLOWED_TRANSFORMATIONS_FIT_AND_FILL: str = "FitAndFill"
IM_QUERY_ALLOWED_TRANSFORMATIONS_GOOP: str = "Goop"
IM_QUERY_ALLOWED_TRANSFORMATIONS_GRAYSCALE: str = "Grayscale"
IM_QUERY_ALLOWED_TRANSFORMATIONS_HSL: str = "HSL"
IM_QUERY_ALLOWED_TRANSFORMATIONS_HSV: str = "HSV"
IM_QUERY_ALLOWED_TRANSFORMATIONS_IF_DIMENSION: str = "IfDimension"
IM_QUERY_ALLOWED_TRANSFORMATIONS_IF_ORIENTATION: str = "IfOrientation"
IM_QUERY_ALLOWED_TRANSFORMATIONS_MAX_COLORS: str = "MaxColors"
IM_QUERY_ALLOWED_TRANSFORMATIONS_MIRROR: str = "Mirror"
IM_QUERY_ALLOWED_TRANSFORMATIONS_MONO_HUE: str = "MonoHue"
IM_QUERY_ALLOWED_TRANSFORMATIONS_OPACITY: str = "Opacity"
IM_QUERY_ALLOWED_TRANSFORMATIONS_REGION_OF_INTEREST_CROP: str = "RegionOfInterestCrop"
IM_QUERY_ALLOWED_TRANSFORMATIONS_RELATIVE_CROP: str = "RelativeCrop"
IM_QUERY_ALLOWED_TRANSFORMATIONS_REMOVE_COLOR: str = "RemoveColor"
IM_QUERY_ALLOWED_TRANSFORMATIONS_RESIZE: str = "Resize"
IM_QUERY_ALLOWED_TRANSFORMATIONS_ROTATE: str = "Rotate"
IM_QUERY_ALLOWED_TRANSFORMATIONS_SCALE: str = "Scale"
IM_QUERY_ALLOWED_TRANSFORMATIONS_SHEAR: str = "Shear"
IM_QUERY_ALLOWED_TRANSFORMATIONS_SMART_CROP: str = "SmartCrop"
IM_QUERY_ALLOWED_TRANSFORMATIONS_TRIM: str = "Trim"
IM_QUERY_ALLOWED_TRANSFORMATIONS_UNSHARP_MASK: str = "UnsharpMask"

# ===================================================================
# OutputImage format constants (from policy.gen.go)
# ===================================================================
OUTPUT_IMAGE_ALLOWED_FORMATS_GIF: str = "gif"
OUTPUT_IMAGE_ALLOWED_FORMATS_JPEG: str = "jpeg"
OUTPUT_IMAGE_ALLOWED_FORMATS_PNG: str = "png"
OUTPUT_IMAGE_ALLOWED_FORMATS_WEBP: str = "webp"
OUTPUT_IMAGE_ALLOWED_FORMATS_JPEGXR: str = "jpegxr"
OUTPUT_IMAGE_ALLOWED_FORMATS_JPEG2000: str = "jpeg2000"
OUTPUT_IMAGE_ALLOWED_FORMATS_AVIF: str = "avif"

OUTPUT_IMAGE_FORCED_FORMATS_GIF: str = "gif"
OUTPUT_IMAGE_FORCED_FORMATS_JPEG: str = "jpeg"
OUTPUT_IMAGE_FORCED_FORMATS_PNG: str = "png"
OUTPUT_IMAGE_FORCED_FORMATS_WEBP: str = "webp"
OUTPUT_IMAGE_FORCED_FORMATS_JPEGXR: str = "jpegxr"
OUTPUT_IMAGE_FORCED_FORMATS_JPEG2000: str = "jpeg2000"
OUTPUT_IMAGE_FORCED_FORMATS_AVIF: str = "avif"

# ===================================================================
# OutputImagePerceptualQuality constants (from policy.gen.go)
# ===================================================================
OUTPUT_IMAGE_PERCEPTUAL_QUALITY_HIGH: str = "high"
OUTPUT_IMAGE_PERCEPTUAL_QUALITY_MEDIUM_HIGH: str = "mediumHigh"
OUTPUT_IMAGE_PERCEPTUAL_QUALITY_MEDIUM: str = "medium"
OUTPUT_IMAGE_PERCEPTUAL_QUALITY_MEDIUM_LOW: str = "mediumLow"
OUTPUT_IMAGE_PERCEPTUAL_QUALITY_LOW: str = "low"

# ===================================================================
# RegionOfInterestCropStyle constants (from policy.gen.go)
# ===================================================================
REGION_OF_INTEREST_CROP_STYLE_CROP: str = "crop"
REGION_OF_INTEREST_CROP_STYLE_FILL: str = "fill"
REGION_OF_INTEREST_CROP_STYLE_ZOOM: str = "zoom"

# ===================================================================
# ResizeAspect constants (from policy.gen.go)
# ===================================================================
RESIZE_ASPECT_FIT: str = "fit"
RESIZE_ASPECT_FILL: str = "fill"
RESIZE_ASPECT_IGNORE: str = "ignore"

# ===================================================================
# ResizeType constants (from policy.gen.go)
# ===================================================================
RESIZE_TYPE_NORMAL: str = "normal"
RESIZE_TYPE_UPSIZE: str = "upsize"
RESIZE_TYPE_DOWNSIZE: str = "downsize"

# ===================================================================
# SmartCropStyle constants (from policy.gen.go)
# ===================================================================
SMART_CROP_STYLE_CROP: str = "crop"
SMART_CROP_STYLE_FILL: str = "fill"
SMART_CROP_STYLE_ZOOM: str = "zoom"

# ===================================================================
# VariableType constants (from policy.gen.go)
# ===================================================================
VARIABLE_TYPE_BOOL: str = "bool"
VARIABLE_TYPE_NUMBER: str = "number"
VARIABLE_TYPE_URL: str = "url"
VARIABLE_TYPE_COLOR: str = "color"
VARIABLE_TYPE_GRAVITY: str = "gravity"
VARIABLE_TYPE_PLACEMENT: str = "placement"
VARIABLE_TYPE_SCALE_DIMENSION: str = "scaleDimension"
VARIABLE_TYPE_GRAYSCALE_TYPE: str = "grayscaleType"
VARIABLE_TYPE_ASPECT: str = "aspect"
VARIABLE_TYPE_RESIZE_TYPE: str = "resizeType"
VARIABLE_TYPE_DIMENSION: str = "dimension"
VARIABLE_TYPE_PERCEPTUAL_QUALITY: str = "perceptualQuality"
VARIABLE_TYPE_STRING: str = "string"
VARIABLE_TYPE_FOCUS: str = "focus"

# ===================================================================
# OutputVideoPerceptualQuality constants (from policy.gen.go)
# ===================================================================
OUTPUT_VIDEO_PERCEPTUAL_QUALITY_HIGH: str = "high"
OUTPUT_VIDEO_PERCEPTUAL_QUALITY_MEDIUM_HIGH: str = "mediumHigh"
OUTPUT_VIDEO_PERCEPTUAL_QUALITY_MEDIUM: str = "medium"
OUTPUT_VIDEO_PERCEPTUAL_QUALITY_MEDIUM_LOW: str = "mediumLow"
OUTPUT_VIDEO_PERCEPTUAL_QUALITY_LOW: str = "low"

# ===================================================================
# OutputVideoVideoAdaptiveQuality constants (from policy.gen.go)
# ===================================================================
OUTPUT_VIDEO_VIDEO_ADAPTIVE_QUALITY_HIGH: str = "high"
OUTPUT_VIDEO_VIDEO_ADAPTIVE_QUALITY_MEDIUM_HIGH: str = "mediumHigh"
OUTPUT_VIDEO_VIDEO_ADAPTIVE_QUALITY_MEDIUM: str = "medium"
OUTPUT_VIDEO_VIDEO_ADAPTIVE_QUALITY_MEDIUM_LOW: str = "mediumLow"
OUTPUT_VIDEO_VIDEO_ADAPTIVE_QUALITY_LOW: str = "low"

# ===================================================================
# Image Type discriminator constants (from policy.gen.go)
# ===================================================================
BOX_IMAGE_TYPE_TYPE: str = "Box"
BOX_IMAGE_TYPE_POST_TYPE: str = "Box"
CIRCLE_IMAGE_TYPE_TYPE: str = "Circle"
CIRCLE_IMAGE_TYPE_POST_TYPE: str = "Circle"
TEXT_IMAGE_TYPE_TYPE: str = "Text"
TEXT_IMAGE_TYPE_POST_TYPE: str = "Text"
URL_IMAGE_TYPE_TYPE: str = "URL"
URL_IMAGE_TYPE_POST_TYPE: str = "URL"

# ===================================================================
# PolicyOutput discriminator constants (from policy.gen.go)
# ===================================================================
POLICY_OUTPUT_IMAGE_VIDEO: bool = False
POLICY_OUTPUT_VIDEO_VIDEO: bool = True


# ###################################################################
# Policy Request/Response Models (from policy.go)
# ###################################################################


@dataclass
class ListPoliciesRequest:
    """Parameters for the ListPolicies request."""
    network: str = ""
    contract_id: str = ""
    policy_set_id: str = ""


@dataclass
class ListPoliciesResponse:
    """Response from ListPolicies operations."""
    item_kind: str = ""
    items: list = field(default_factory=list)
    total_items: int = 0


@dataclass
class GetPolicyRequest:
    """Parameters for the GetPolicy request."""
    policy_id: str = ""
    network: str = ""
    contract_id: str = ""
    policy_set_id: str = ""


@dataclass
class UpsertPolicyRequest:
    """Parameters for the UpsertPolicy request."""
    policy_id: str = ""
    network: str = ""
    contract_id: str = ""
    policy_set_id: str = ""
    policy_input: Any = None


@dataclass
class DeletePolicyRequest:
    """Parameters for the DeletePolicy request."""
    policy_id: str = ""
    network: str = ""
    contract_id: str = ""
    policy_set_id: str = ""


@dataclass
class GetPolicyHistoryRequest:
    """Parameters for the GetPolicyHistory request."""
    policy_id: str = ""
    network: str = ""
    contract_id: str = ""
    policy_set_id: str = ""


@dataclass
class RollbackPolicyRequest:
    """Parameters for the RollbackPolicy request."""
    policy_id: str = ""
    network: str = ""
    contract_id: str = ""
    policy_set_id: str = ""


@dataclass
class PolicyResponse:
    """Response from UpsertPolicy, DeletePolicy and RollbackPolicy."""
    description: str = ""
    id: str = ""
    operation_performed: str = ""


@dataclass
class GetPolicyHistoryResponse:
    """Response from GetPolicyHistory."""
    item_kind: str = ""
    total_items: int = 0
    items: list = field(default_factory=list)


@dataclass
class PolicyHistoryItem:
    """Item in the policy history."""
    id: str = ""
    date_created: str = ""
    policy: str = ""
    action: str = ""
    user: str = ""
    version: int = 0


# ###################################################################
# PolicySet Request/Response Models (from policyset.go)
# ###################################################################


@dataclass
class ListPolicySetsRequest:
    """Parameters for the ListPolicySets request."""
    contract_id: str = ""
    network: str = ""


@dataclass
class GetPolicySetRequest:
    """Parameters for the GetPolicySet request."""
    policy_set_id: str = ""
    contract_id: str = ""
    network: str = ""


@dataclass
class CreatePolicySet:
    """Body of the CreatePolicySet request."""
    name: str = ""
    region: str = ""
    type: str = ""
    default_policy: Any = None


@dataclass
class CreatePolicySetRequest:
    """Parameters for the CreatePolicySet request."""
    contract_id: str = ""
    name: str = ""
    region: str = ""
    type: str = ""
    default_policy: Any = None


@dataclass
class UpdatePolicySet:
    """Body of the UpdatePolicySet request."""
    name: str = ""
    region: str = ""


@dataclass
class UpdatePolicySetRequest:
    """Parameters for the UpdatePolicySet request."""
    policy_set_id: str = ""
    contract_id: str = ""
    name: str = ""
    region: str = ""


@dataclass
class PolicySet:
    """Response from CRU operations on policy sets."""
    id: str = ""
    name: str = ""
    region: str = ""
    type: str = ""
    user: str = ""
    properties: list[str] = field(default_factory=list)
    last_modified: str = ""


@dataclass
class DeletePolicySetRequest:
    """Parameters for the delete PolicySet request."""
    policy_set_id: str = ""
    contract_id: str = ""


# ###################################################################
# Helper / Infrastructure Types (from policy.gen.go)
# ###################################################################


@dataclass
class InlineVariable:
    """Inline variable reference used in VariableInline unmarshal."""
    var: str = ""


@dataclass
class Breakpoints:
    """Breakpoint widths for derivative images/videos."""
    widths: list[int] = field(default_factory=list)


@dataclass
class EnumOptions:
    """Enum option for a variable."""
    id: str = ""
    value: str = ""


@dataclass
class Variable:
    """Declares a variable for use within the policy."""
    default_value: str = ""
    enum_options: list = field(default_factory=list)
    name: str = ""
    postfix: str | None = None
    prefix: str | None = None
    type: str = ""


@dataclass
class RolloutInfo:
    """Rollout timing information for a policy."""
    end_time: int = 0
    rollout_duration: int = 0
    serve_stale_duration: int | None = None
    start_time: int = 0


# ###################################################################
# Variable Inline Types (from policy.gen.go)
# ###################################################################


@dataclass
class BooleanVariableInline:
    """Variable inline for boolean values."""
    name: str | None = None
    value: bool | None = None


@dataclass
class IntegerVariableInline:
    """Variable inline for integer values."""
    name: str | None = None
    value: int | None = None


@dataclass
class NumberVariableInline:
    """Variable inline for floating-point values."""
    name: str | None = None
    value: float | None = None


@dataclass
class StringVariableInline:
    """Variable inline for string values."""
    name: str | None = None
    value: str | None = None


@dataclass
class QueryVariableInline:
    """Variable inline for query variable references (name only)."""
    name: str | None = None


@dataclass
class GravityVariableInline:
    """Variable inline for Gravity enum values."""
    name: str | None = None
    value: str | None = None


@dataclass
class GravityPostVariableInline:
    """Variable inline for GravityPost enum values."""
    name: str | None = None
    value: str | None = None


@dataclass
class AppendGravityPriorityVariableInline:
    """Variable inline for AppendGravityPriority enum values."""
    name: str | None = None
    value: str | None = None


@dataclass
class CompositePlacementVariableInline:
    """Variable inline for CompositePlacement enum values."""
    name: str | None = None
    value: str | None = None


@dataclass
class CompositePostPlacementVariableInline:
    """Variable inline for CompositePostPlacement enum values."""
    name: str | None = None
    value: str | None = None


@dataclass
class CompositeScaleDimensionVariableInline:
    """Variable inline for CompositeScaleDimension enum values."""
    name: str | None = None
    value: str | None = None


@dataclass
class CompositePostScaleDimensionVariableInline:
    """Variable inline for CompositePostScaleDimension enum values."""
    name: str | None = None
    value: str | None = None


@dataclass
class FaceCropAlgorithmVariableInline:
    """Variable inline for FaceCropAlgorithm enum values."""
    name: str | None = None
    value: str | None = None


@dataclass
class FaceCropFocusVariableInline:
    """Variable inline for FaceCropFocus enum values."""
    name: str | None = None
    value: str | None = None


@dataclass
class FaceCropStyleVariableInline:
    """Variable inline for FaceCropStyle enum values."""
    name: str | None = None
    value: str | None = None


@dataclass
class FeatureCropStyleVariableInline:
    """Variable inline for FeatureCropStyle enum values."""
    name: str | None = None
    value: str | None = None


@dataclass
class GrayscaleTypeVariableInline:
    """Variable inline for GrayscaleType enum values."""
    name: str | None = None
    value: str | None = None


@dataclass
class IfDimensionDimensionVariableInline:
    """Variable inline for IfDimensionDimension enum values."""
    name: str | None = None
    value: str | None = None


@dataclass
class IfDimensionPostDimensionVariableInline:
    """Variable inline for IfDimensionPostDimension enum values."""
    name: str | None = None
    value: str | None = None


@dataclass
class OutputImagePerceptualQualityVariableInline:
    """Variable inline for OutputImagePerceptualQuality enum values."""
    name: str | None = None
    value: str | None = None


@dataclass
class RegionOfInterestCropStyleVariableInline:
    """Variable inline for RegionOfInterestCropStyle enum values."""
    name: str | None = None
    value: str | None = None


@dataclass
class ResizeAspectVariableInline:
    """Variable inline for ResizeAspect enum values."""
    name: str | None = None
    value: str | None = None


@dataclass
class ResizeTypeVariableInline:
    """Variable inline for ResizeType enum values."""
    name: str | None = None
    value: str | None = None


@dataclass
class SmartCropStyleVariableInline:
    """Variable inline for SmartCropStyle enum values."""
    name: str | None = None
    value: str | None = None


@dataclass
class OutputVideoPerceptualQualityVariableInline:
    """Variable inline for OutputVideoPerceptualQuality enum values."""
    name: str | None = None
    value: str | None = None


@dataclass
class OutputVideoVideoAdaptiveQualityVariableInline:
    """Variable inline for OutputVideoVideoAdaptiveQuality enum values."""
    name: str | None = None
    value: str | None = None


# ###################################################################
# Output Types (from policy.gen.go)
# ###################################################################


@dataclass
class OutputImage:
    """Output settings for image policies."""
    adaptive_quality: int | None = None
    allow_pristine_on_downsize: bool | None = None
    allowed_formats: list[str] = field(default_factory=list)
    forced_formats: list[str] = field(default_factory=list)
    perceptual_quality: OutputImagePerceptualQualityVariableInline | None = None
    perceptual_quality_floor: int | None = None
    prefer_modern_formats: bool | None = None
    quality: IntegerVariableInline | None = None


@dataclass
class OutputVideo:
    """Output settings for video policies."""
    perceptual_quality: OutputVideoPerceptualQualityVariableInline | None = None
    placeholder_video_url: str | None = None
    video_adaptive_quality: OutputVideoVideoAdaptiveQualityVariableInline | None = None


# ###################################################################
# Shape Types (from policy.gen.go)
# ###################################################################


@dataclass
class PointShapeType:
    """A point shape defined by x and y coordinates."""
    x: NumberVariableInline | None = None
    y: NumberVariableInline | None = None


@dataclass
class CircleShapeType:
    """A circle shape defined by center point and radius."""
    center: PointShapeType | None = None
    radius: NumberVariableInline | None = None


@dataclass
class PolygonShapeType:
    """A polygon shape defined by a list of points."""
    points: list = field(default_factory=list)


@dataclass
class RectangleShapeType:
    """A rectangle shape defined by anchor point, width and height."""
    anchor: PointShapeType | None = None
    height: NumberVariableInline | None = None
    width: NumberVariableInline | None = None


@dataclass
class UnionShapeType:
    """A union of multiple shapes."""
    shapes: list = field(default_factory=list)


# ###################################################################
# Image Types (from policy.gen.go)
# ###################################################################


@dataclass
class BoxImageType:
    """A box image with a solid color background."""
    color: StringVariableInline | None = None
    height: NumberVariableInline | None = None
    transformation: Any = None
    type: str | None = None
    width: NumberVariableInline | None = None


@dataclass
class BoxImageTypePost:
    """A box image with a solid color background (post-breakpoint)."""
    color: StringVariableInline | None = None
    height: NumberVariableInline | None = None
    transformation: Any = None
    type: str | None = None
    width: NumberVariableInline | None = None


@dataclass
class CircleImageType:
    """A circle image with a solid color background."""
    color: StringVariableInline | None = None
    diameter: NumberVariableInline | None = None
    transformation: Any = None
    type: str | None = None
    width: NumberVariableInline | None = None


@dataclass
class CircleImageTypePost:
    """A circle image with a solid color background (post-breakpoint)."""
    color: StringVariableInline | None = None
    diameter: NumberVariableInline | None = None
    transformation: Any = None
    type: str | None = None
    width: NumberVariableInline | None = None


@dataclass
class TextImageType:
    """A text image."""
    fill: StringVariableInline | None = None
    size: NumberVariableInline | None = None
    stroke: StringVariableInline | None = None
    stroke_color: StringVariableInline | None = None
    stroke_size: NumberVariableInline | None = None
    text: StringVariableInline | None = None
    transformation: Any = None
    type: str | None = None
    typeface: StringVariableInline | None = None


@dataclass
class TextImageTypePost:
    """A text image (post-breakpoint)."""
    fill: StringVariableInline | None = None
    size: NumberVariableInline | None = None
    stroke: StringVariableInline | None = None
    stroke_color: StringVariableInline | None = None
    stroke_size: NumberVariableInline | None = None
    text: StringVariableInline | None = None
    transformation: Any = None
    type: str | None = None
    typeface: StringVariableInline | None = None


@dataclass
class URLImageType:
    """A URL-sourced image."""
    transformation: Any = None
    type: str | None = None
    url: StringVariableInline | None = None


@dataclass
class URLImageTypePost:
    """A URL-sourced image (post-breakpoint)."""
    transformation: Any = None
    type: str | None = None
    url: StringVariableInline | None = None


# ###################################################################
# Transformation Types (from policy.gen.go)
# ###################################################################


@dataclass
class Append:
    """Appends an image to another image."""
    gravity: GravityVariableInline | None = None
    gravity_priority: AppendGravityPriorityVariableInline | None = None
    image: Any = None
    preserve_minor_dimension: BooleanVariableInline | None = None
    transformation: str | None = None


@dataclass
class AspectCrop:
    """Crops an image to a specified aspect ratio."""
    allow_expansion: BooleanVariableInline | None = None
    height: NumberVariableInline | None = None
    transformation: str | None = None
    width: NumberVariableInline | None = None
    x_position: NumberVariableInline | None = None
    y_position: NumberVariableInline | None = None


@dataclass
class BackgroundColor:
    """Sets the background color for an image."""
    color: StringVariableInline | None = None
    transformation: str | None = None


@dataclass
class Blur:
    """Applies a Gaussian blur to the image."""
    sigma: NumberVariableInline | None = None
    transformation: str | None = None


@dataclass
class ChromaKey:
    """Applies chroma key (green screen) effect."""
    hue: NumberVariableInline | None = None
    hue_feather: NumberVariableInline | None = None
    hue_tolerance: NumberVariableInline | None = None
    lightness_feather: NumberVariableInline | None = None
    lightness_tolerance: NumberVariableInline | None = None
    saturation_feather: NumberVariableInline | None = None
    saturation_tolerance: NumberVariableInline | None = None
    transformation: str | None = None


@dataclass
class Composite:
    """Composites an image over or under another image."""
    gravity: GravityVariableInline | None = None
    image: Any = None
    placement: CompositePlacementVariableInline | None = None
    scale: NumberVariableInline | None = None
    scale_dimension: CompositeScaleDimensionVariableInline | None = None
    transformation: str | None = None
    x_position: IntegerVariableInline | None = None
    y_position: IntegerVariableInline | None = None


@dataclass
class CompositePost:
    """Composites an image (post-breakpoint variant)."""
    gravity: GravityPostVariableInline | None = None
    image: Any = None
    placement: CompositePostPlacementVariableInline | None = None
    scale: NumberVariableInline | None = None
    scale_dimension: CompositePostScaleDimensionVariableInline | None = None
    transformation: str | None = None
    x_position: IntegerVariableInline | None = None
    y_position: IntegerVariableInline | None = None


@dataclass
class Compound:
    """Applies a set of transformations as a single compound operation."""
    transformation: str | None = None
    transformations: list = field(default_factory=list)


@dataclass
class CompoundPost:
    """Applies post-breakpoint transformations as a compound operation."""
    transformation: str | None = None
    transformations: list = field(default_factory=list)


@dataclass
class Contrast:
    """Adjusts the brightness and contrast of an image."""
    brightness: NumberVariableInline | None = None
    contrast: NumberVariableInline | None = None
    transformation: str | None = None


@dataclass
class Crop:
    """Crops an image to specified dimensions."""
    allow_expansion: BooleanVariableInline | None = None
    gravity: GravityVariableInline | None = None
    height: NumberVariableInline | None = None
    transformation: str | None = None
    width: NumberVariableInline | None = None
    x_position: IntegerVariableInline | None = None
    y_position: IntegerVariableInline | None = None


@dataclass
class FaceCrop:
    """Crops an image based on face detection."""
    algorithm: FaceCropAlgorithmVariableInline | None = None
    confidence: NumberVariableInline | None = None
    fail_gravity: GravityVariableInline | None = None
    focus: FaceCropFocusVariableInline | None = None
    gravity: GravityVariableInline | None = None
    height: NumberVariableInline | None = None
    padding: NumberVariableInline | None = None
    style: FaceCropStyleVariableInline | None = None
    transformation: str | None = None
    width: NumberVariableInline | None = None


@dataclass
class FeatureCrop:
    """Crops an image based on feature detection."""
    fail_gravity: GravityVariableInline | None = None
    feature_radius: NumberVariableInline | None = None
    gravity: GravityVariableInline | None = None
    height: NumberVariableInline | None = None
    max_features: IntegerVariableInline | None = None
    min_feature_quality: NumberVariableInline | None = None
    padding: NumberVariableInline | None = None
    style: FeatureCropStyleVariableInline | None = None
    transformation: str | None = None
    width: NumberVariableInline | None = None


@dataclass
class FitAndFill:
    """Fits and fills an image to specified dimensions."""
    fill_transformation: Any = None
    height: NumberVariableInline | None = None
    transformation: str | None = None
    width: NumberVariableInline | None = None


@dataclass
class Goop:
    """Applies a goop distortion effect."""
    chaos: NumberVariableInline | None = None
    density: NumberVariableInline | None = None
    power: NumberVariableInline | None = None
    seed: IntegerVariableInline | None = None
    transformation: str | None = None


@dataclass
class Grayscale:
    """Converts an image to grayscale."""
    transformation: str | None = None
    type: GrayscaleTypeVariableInline | None = None


@dataclass
class HSL:
    """Adjusts hue, saturation, and lightness."""
    hue: NumberVariableInline | None = None
    lightness: NumberVariableInline | None = None
    saturation: NumberVariableInline | None = None
    transformation: str | None = None


@dataclass
class HSV:
    """Adjusts hue, saturation, and value."""
    hue: NumberVariableInline | None = None
    saturation: NumberVariableInline | None = None
    transformation: str | None = None
    value: NumberVariableInline | None = None


@dataclass
class IfDimension:
    """Conditional transformation based on image dimensions."""
    default: Any = None
    dimension: IfDimensionDimensionVariableInline | None = None
    equal: Any = None
    greater_than: Any = None
    less_than: Any = None
    transformation: str | None = None
    value: IntegerVariableInline | None = None


@dataclass
class IfDimensionPost:
    """Conditional transformation based on dimensions (post-breakpoint)."""
    default: Any = None
    dimension: IfDimensionPostDimensionVariableInline | None = None
    equal: Any = None
    greater_than: Any = None
    less_than: Any = None
    transformation: str | None = None
    value: IntegerVariableInline | None = None


@dataclass
class IfOrientation:
    """Conditional transformation based on image orientation."""
    default: Any = None
    landscape: Any = None
    portrait: Any = None
    square: Any = None
    transformation: str | None = None


@dataclass
class IfOrientationPost:
    """Conditional transformation based on orientation (post-breakpoint)."""
    default: Any = None
    landscape: Any = None
    portrait: Any = None
    square: Any = None
    transformation: str | None = None


@dataclass
class ImQuery:
    """Enables image manipulation via query parameters."""
    allowed_transformations: list[str] = field(default_factory=list)
    query_var: QueryVariableInline | None = None
    transformation: str | None = None


@dataclass
class MaxColors:
    """Reduces the number of colors in an image."""
    colors: IntegerVariableInline | None = None
    transformation: str | None = None


@dataclass
class Mirror:
    """Mirrors an image horizontally or vertically."""
    horizontal: BooleanVariableInline | None = None
    transformation: str | None = None
    vertical: BooleanVariableInline | None = None


@dataclass
class MonoHue:
    """Applies a monochromatic hue to an image."""
    hue: NumberVariableInline | None = None
    transformation: str | None = None


@dataclass
class Opacity:
    """Adjusts the opacity of an image."""
    opacity: NumberVariableInline | None = None
    transformation: str | None = None


@dataclass
class RegionOfInterestCrop:
    """Crops to a region of interest."""
    gravity: GravityVariableInline | None = None
    height: IntegerVariableInline | None = None
    region_of_interest: Any = None
    style: RegionOfInterestCropStyleVariableInline | None = None
    transformation: str | None = None
    width: IntegerVariableInline | None = None


@dataclass
class RelativeCrop:
    """Crops from each edge of the image by relative amounts."""
    east: IntegerVariableInline | None = None
    north: IntegerVariableInline | None = None
    south: IntegerVariableInline | None = None
    transformation: str | None = None
    west: IntegerVariableInline | None = None


@dataclass
class RemoveColor:
    """Removes a specific color from an image."""
    color: StringVariableInline | None = None
    feather: NumberVariableInline | None = None
    tolerance: NumberVariableInline | None = None
    transformation: str | None = None


@dataclass
class Resize:
    """Resizes an image to specified dimensions."""
    aspect: ResizeAspectVariableInline | None = None
    height: NumberVariableInline | None = None
    transformation: str | None = None
    type: ResizeTypeVariableInline | None = None
    width: NumberVariableInline | None = None


@dataclass
class Rotate:
    """Rotates an image by a specified number of degrees."""
    degrees: NumberVariableInline | None = None
    transformation: str | None = None


@dataclass
class Scale:
    """Scales an image by width and height factors."""
    height: NumberVariableInline | None = None
    transformation: str | None = None
    width: NumberVariableInline | None = None


@dataclass
class Shear:
    """Applies a shear transformation to an image."""
    transformation: str | None = None
    x_shear: NumberVariableInline | None = None
    y_shear: NumberVariableInline | None = None


@dataclass
class SmartCrop:
    """Crops an image using content-aware algorithms."""
    debug: BooleanVariableInline | None = None
    height: NumberVariableInline | None = None
    sloppy: BooleanVariableInline | None = None
    style: SmartCropStyleVariableInline | None = None
    transformation: str | None = None
    width: NumberVariableInline | None = None


@dataclass
class Trim:
    """Trims uniform-color borders from an image."""
    fuzz: NumberVariableInline | None = None
    padding: IntegerVariableInline | None = None
    transformation: str | None = None


@dataclass
class UnsharpMask:
    """Applies an unsharp mask to an image."""
    gain: NumberVariableInline | None = None
    sigma: NumberVariableInline | None = None
    threshold: NumberVariableInline | None = None
    transformation: str | None = None


# ###################################################################
# Policy Input/Output Types (from policy.go + policy.gen.go)
# ###################################################################


@dataclass
class PolicyInputImage:
    """Input policy details for images."""
    breakpoints: Breakpoints | None = None
    hosts: list[str] = field(default_factory=list)
    output: OutputImage | None = None
    post_breakpoint_transformations: list = field(default_factory=list)
    rollout_duration: int | None = None
    serve_stale_duration: int | None = None
    transformations: list = field(default_factory=list)
    variables: list = field(default_factory=list)


@dataclass
class PolicyInputVideo:
    """Input policy details for videos."""
    breakpoints: Breakpoints | None = None
    hosts: list[str] = field(default_factory=list)
    output: OutputVideo | None = None
    rollout_duration: int | None = None
    variables: list = field(default_factory=list)


@dataclass
class PolicyOutputImage:
    """Output policy details for images."""
    breakpoints: Breakpoints | None = None
    date_created: str = ""
    hosts: list[str] = field(default_factory=list)
    id: str = ""
    output: OutputImage | None = None
    post_breakpoint_transformations: list = field(default_factory=list)
    previous_version: int = 0
    rollout_info: RolloutInfo | None = None
    transformations: list = field(default_factory=list)
    user: str = ""
    variables: list = field(default_factory=list)
    version: int = 0
    video: bool | None = None


@dataclass
class PolicyOutputVideo:
    """Output policy details for videos."""
    breakpoints: Breakpoints | None = None
    date_created: str = ""
    hosts: list[str] = field(default_factory=list)
    id: str = ""
    output: OutputVideo | None = None
    previous_version: int = 0
    rollout_info: RolloutInfo | None = None
    user: str = ""
    variables: list = field(default_factory=list)
    version: int = 0
    video: bool | None = None


# ###################################################################
# Transformation Handler Maps (mirrors Go TransformationHandlers)
# ###################################################################

TRANSFORMATION_HANDLERS: dict[str, type] = {
    "Append": Append,
    "AspectCrop": AspectCrop,
    "BackgroundColor": BackgroundColor,
    "Blur": Blur,
    "ChromaKey": ChromaKey,
    "Composite": Composite,
    "Compound": Compound,
    "Contrast": Contrast,
    "Crop": Crop,
    "FaceCrop": FaceCrop,
    "FeatureCrop": FeatureCrop,
    "FitAndFill": FitAndFill,
    "Goop": Goop,
    "Grayscale": Grayscale,
    "HSL": HSL,
    "HSV": HSV,
    "IfDimension": IfDimension,
    "IfOrientation": IfOrientation,
    "ImQuery": ImQuery,
    "MaxColors": MaxColors,
    "Mirror": Mirror,
    "MonoHue": MonoHue,
    "Opacity": Opacity,
    "RegionOfInterestCrop": RegionOfInterestCrop,
    "RelativeCrop": RelativeCrop,
    "RemoveColor": RemoveColor,
    "Resize": Resize,
    "Rotate": Rotate,
    "Scale": Scale,
    "Shear": Shear,
    "SmartCrop": SmartCrop,
    "Trim": Trim,
    "UnsharpMask": UnsharpMask,
}

POST_BREAKPOINT_TRANSFORMATION_HANDLERS: dict[str, type] = {
    "BackgroundColor": BackgroundColor,
    "Blur": Blur,
    "ChromaKey": ChromaKey,
    "Compound": CompoundPost,
    "Composite": CompositePost,
    "Contrast": Contrast,
    "Goop": Goop,
    "Grayscale": Grayscale,
    "HSL": HSL,
    "HSV": HSV,
    "IfDimension": IfDimensionPost,
    "IfOrientation": IfOrientationPost,
    "MaxColors": MaxColors,
    "Mirror": Mirror,
    "MonoHue": MonoHue,
    "Opacity": Opacity,
    "RemoveColor": RemoveColor,
    "UnsharpMask": UnsharpMask,
}

IMAGE_TYPE_HANDLERS: dict[str, type] = {
    "Box": BoxImageType,
    "Circle": CircleImageType,
    "Text": TextImageType,
    "URL": URLImageType,
}

IMAGE_TYPE_POST_HANDLERS: dict[str, type] = {
    "Box": BoxImageTypePost,
    "Circle": CircleImageTypePost,
    "Text": TextImageTypePost,
    "URL": URLImageTypePost,
}

SHAPE_TYPE_HANDLERS: dict[str, type] = {
    "CircleShapeType": CircleShapeType,
    "PointShapeType": PointShapeType,
    "PolygonShapeType": PolygonShapeType,
    "RectangleShapeType": RectangleShapeType,
    "UnionShapeType": UnionShapeType,
}

# Python snake_case -> JSON camelCase override map for non-trivial mappings
_FIELD_OVERRIDES: dict[str, str] = {
    "item_kind": "itemKind",
    "total_items": "totalItems",
    "policy_id": "policyId",
    "contract_id": "contractId",
    "policy_set_id": "policySetId",
    "policy_input": "policyInput",
    "operation_performed": "operationPerformed",
    "date_created": "dateCreated",
    "default_value": "defaultValue",
    "enum_options": "enumOptions",
    "last_modified": "lastModified",
    "default_policy": "defaultPolicy",
    "adaptive_quality": "adaptiveQuality",
    "allow_pristine_on_downsize": "allowPristineOnDownsize",
    "allowed_formats": "allowedFormats",
    "forced_formats": "forcedFormats",
    "perceptual_quality": "perceptualQuality",
    "perceptual_quality_floor": "perceptualQualityFloor",
    "prefer_modern_formats": "preferModernFormats",
    "placeholder_video_url": "placeholderVideoUrl",
    "video_adaptive_quality": "videoAdaptiveQuality",
    "end_time": "endTime",
    "rollout_duration": "rolloutDuration",
    "serve_stale_duration": "serveStaleDuration",
    "start_time": "startTime",
    "post_breakpoint_transformations": "postBreakpointTransformations",
    "previous_version": "previousVersion",
    "rollout_info": "rolloutInfo",
    "gravity_priority": "gravityPriority",
    "preserve_minor_dimension": "preserveMinorDimension",
    "allow_expansion": "allowExpansion",
    "x_position": "xPosition",
    "y_position": "yPosition",
    "hue_feather": "hueFeather",
    "hue_tolerance": "hueTolerance",
    "lightness_feather": "lightnessFeather",
    "lightness_tolerance": "lightnessTolerance",
    "saturation_feather": "saturationFeather",
    "saturation_tolerance": "saturationTolerance",
    "scale_dimension": "scaleDimension",
    "fill_transformation": "fillTransformation",
    "fail_gravity": "failGravity",
    "feature_radius": "featureRadius",
    "max_features": "maxFeatures",
    "min_feature_quality": "minFeatureQuality",
    "greater_than": "greaterThan",
    "less_than": "lessThan",
    "allowed_transformations": "allowedTransformations",
    "query_var": "queryVar",
    "region_of_interest": "regionOfInterest",
    "stroke_color": "strokeColor",
    "stroke_size": "strokeSize",
    "x_shear": "xShear",
    "y_shear": "yShear",
}

# Reverse lookup: JSON camelCase -> Python snake_case
_JSON_TO_SNAKE: dict[str, str] = {v: k for k, v in _FIELD_OVERRIDES.items()}


def _snake_to_json(name: str) -> str:
    """Convert a Python snake_case field name to its JSON camelCase equivalent."""
    override = _FIELD_OVERRIDES.get(name)
    if override is not None:
        return override
    return _to_camel(name)


def _json_to_snake(name: str) -> str:
    """Convert a JSON camelCase field name to Python snake_case."""
    override = _JSON_TO_SNAKE.get(name)
    if override is not None:
        return override
    return _to_snake(name)


# ###################################################################
# JSON Serialization / Deserialization Helpers
# ###################################################################


def model_to_dict(obj) -> dict:
    """Convert a model dataclass to a JSON-serializable dict.

    Uses JSON tag names (camelCase) and omits None values and empty
    collections to mirror Go's ``omitempty`` JSON tag behaviour.
    """
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if not hasattr(obj, "__dataclass_fields__"):
        return obj  # type: ignore[return-value]

    result: dict[str, Any] = {}
    for py_name in obj.__dataclass_fields__:
        value = getattr(obj, py_name)
        json_name = _snake_to_json(py_name)

        # omitempty: skip None, empty strings on non-required fields,
        # empty lists, and zero ints where the Go type uses a pointer
        if value is None:
            continue
        if isinstance(value, list):
            if not value:
                continue
            value = [model_to_dict(item) if hasattr(item, "__dataclass_fields__") else item
                     for item in value]
        elif hasattr(value, "__dataclass_fields__"):
            value = model_to_dict(value)

        result[json_name] = value
    return result


def dict_to_model(data: dict | None, model_class: type):
    """Convert a JSON dict to a model dataclass instance.

    Maps camelCase JSON keys to snake_case Python fields and recursively
    deserialises nested dataclass types based on type annotations.
    """
    if data is None:
        return model_class()
    if not isinstance(data, dict):
        return model_class()

    kwargs: dict[str, Any] = {}
    fields = model_class.__dataclass_fields__

    for json_key, json_value in data.items():
        py_key = _json_to_snake(json_key)
        if py_key not in fields:
            continue
        kwargs[py_key] = json_value

    return model_class(**kwargs)


# ###################################################################
# Polymorphic Deserialization (mirrors Go unmarshal functions)
# ###################################################################


def unmarshal_policy_output(data: dict) -> PolicyOutputImage | PolicyOutputVideo:
    """Unmarshal a policy output dict into PolicyOutputImage or PolicyOutputVideo.

    Uses the ``video`` boolean field as the discriminator.
    Mirrors Go ``unmarshallPolicyOutput()``.
    """
    if data is None:
        return PolicyOutputImage()

    is_video = data.get("video", False)
    if is_video:
        return dict_to_model(data, PolicyOutputVideo)
    return dict_to_model(data, PolicyOutputImage)


def unmarshal_policy_outputs(data: list[dict] | None) -> list:
    """Unmarshal a list of policy output dicts.

    Mirrors Go ``PolicyOutputs.UnmarshalJSON()``.
    """
    if not data:
        return []
    return [unmarshal_policy_output(item) for item in data]
