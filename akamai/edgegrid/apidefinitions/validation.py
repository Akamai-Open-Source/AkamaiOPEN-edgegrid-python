"""Request validation functions for the API Definitions API.

Every Go ``Validate()`` method on a request or typed-value struct maps to
a Python function ``validate_*(...) -> str | None``.  Enum validators return
a formatted error string matching the Go error verbatim, or ``None`` when
valid.  Request validators aggregate field errors through
``parse_validation_errors`` (mirroring ``edgegriderr.ParseValidationErrors``).

Go reference files:
    - ``pkg/apidefinitions/activations.go``
    - ``pkg/apidefinitions/endpoint_versions.go``
    - ``pkg/apidefinitions/endpoints.go``
"""
# pylint: disable=too-many-lines

import re
import urllib.parse

from akamai.edgegrid.apidefinitions import models
from akamai.edgegrid.validation import parse_validation_errors


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+"
    r"@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)


def _is_valid_email(email: str) -> bool:
    """Check whether *email* matches a standard email format.

    Mirrors Go ``validators.EmailFormat`` from ozzo-validation ``is`` package.
    """
    return _EMAIL_PATTERN.match(email) is not None


def _is_empty_dataclass(obj) -> bool:
    """Return ``True`` when *obj* equals a freshly-constructed default instance.

    Equivalent to Go ``reflect.ValueOf(v).IsZero()`` for structs.
    Used for ``NilOrNotEmpty`` / ``Required`` semantics on nested objects.
    """
    return obj == type(obj)()


# ===================================================================
# Activation validators  (activations.go)
# ===================================================================

def validate_network_type(n: str) -> str | None:
    """Validate ``NetworkType`` value.

    Mirrors Go ``NetworkType.Validate()`` at activations.go:114-118.
    """
    valid = (models.ACTIVATION_NETWORK_STAGING,
             models.ACTIVATION_NETWORK_PRODUCTION)
    if n not in valid:
        return (
            f"value '{n}' is invalid. Must be one of: "
            f"'{models.ACTIVATION_NETWORK_STAGING}', "
            f"'{models.ACTIVATION_NETWORK_PRODUCTION}' "
        )
    return None


def _collect_verify_version_request_body_errors(b) -> dict | None:
    """Collect ``VerifyVersionRequestBody`` errors as a dict."""
    errors: dict = {}
    if not b.networks:
        errors["Networks"] = "cannot be blank"
    return errors or None


def validate_verify_version_request_body(b) -> str | None:
    """Validate ``VerifyVersionRequestBody``.

    Mirrors Go ``VerifyVersionRequestBody.Validate()``
    at activations.go:148-152.
    """
    errs = _collect_verify_version_request_body_errors(b)
    if not errs:
        return None
    return parse_validation_errors(errs)


def _collect_activation_request_body_errors(b) -> dict | None:
    """Collect ``ActivationRequestBody`` errors as a dict."""
    errors: dict = {}
    if not b.networks:
        errors["Networks"] = "cannot be blank"
    if b.notification_recipients:
        recipient_errors: dict = {}
        for i, email in enumerate(b.notification_recipients):
            if not _is_valid_email(email):
                recipient_errors[str(i)] = "must be a valid email address."
        if recipient_errors:
            errors["NotificationRecipients"] = recipient_errors
    return errors or None


def validate_activation_request_body(b) -> str | None:
    """Validate ``ActivationRequestBody``.

    Mirrors Go ``ActivationRequestBody.Validate()``
    at activations.go:155-160.
    """
    errs = _collect_activation_request_body_errors(b)
    if not errs:
        return None
    return parse_validation_errors(errs)


def validate_verify_version_request(r) -> str | None:
    """Validate ``VerifyVersionRequest``.

    Mirrors Go ``VerifyVersionRequest.Validate()``
    at activations.go:121-127.
    """
    errors: dict = {}
    if not r.api_endpoint_id:
        errors["APIEndpointID"] = "cannot be blank"
    if not r.version_number:
        errors["VersionNumber"] = "cannot be blank"
    if r.body is None:
        errors["Body"] = "cannot be blank"
    else:
        body_err = _collect_verify_version_request_body_errors(r.body)
        if body_err:
            errors["Body"] = body_err
    return parse_validation_errors(errors)


def validate_activate_version_request(r) -> str | None:
    """Validate ``ActivateVersionRequest``.

    Mirrors Go ``ActivateVersionRequest.Validate()``
    at activations.go:130-136.
    """
    errors: dict = {}
    if not r.api_endpoint_id:
        errors["APIEndpointID"] = "cannot be blank"
    if not r.version_number:
        errors["VersionNumber"] = "cannot be blank"
    if r.body is None:
        errors["Body"] = "cannot be blank"
    else:
        body_err = _collect_activation_request_body_errors(r.body)
        if body_err:
            errors["Body"] = body_err
    return parse_validation_errors(errors)


def validate_deactivate_version_request(r) -> str | None:
    """Validate ``DeactivateVersionRequest``.

    Mirrors Go ``DeactivateVersionRequest.Validate()``
    at activations.go:139-145.
    """
    errors: dict = {}
    if not r.api_endpoint_id:
        errors["APIEndpointID"] = "cannot be blank"
    if not r.version_number:
        errors["VersionNumber"] = "cannot be blank"
    if r.body is None:
        errors["Body"] = "cannot be blank"
    else:
        body_err = _collect_activation_request_body_errors(r.body)
        if body_err:
            errors["Body"] = body_err
    return parse_validation_errors(errors)


# ===================================================================
# Endpoint-version validators  (endpoint_versions.go)
# ===================================================================

def validate_list_endpoint_version_sort_type(s: str) -> str | None:
    """Validate ``ListEndpointVersionSortType``.

    Mirrors Go ``ListEndpointVersionSortType.Validate()``
    at endpoint_versions.go:215-219.
    """
    valid = (
        models.DESCRIPTION_SORT, models.VERSION_NUMBER_SORT,
        models.UPDATE_DATE_SORT, models.UPDATED_BY_SORT,
        models.BASED_ON_SORT, models.STAGING_STATUS_SORT,
        models.PRODUCTION_STATUS_SORT,
    )
    if s not in valid:
        return (
            f"value '{s}' is invalid. Must be one of: "
            f"'{models.DESCRIPTION_SORT}', "
            f"'{models.VERSION_NUMBER_SORT}', "
            f"'{models.UPDATE_DATE_SORT}', "
            f"'{models.UPDATED_BY_SORT}', "
            f"'{models.BASED_ON_SORT}', "
            f"'{models.STAGING_STATUS_SORT}', "
            f"'{models.PRODUCTION_STATUS_SORT}'."
        )
    return None


def validate_sort_order_type(s: str) -> str | None:
    """Validate ``SortOrderType``.

    Mirrors Go ``SortOrderType.Validate()``
    at endpoint_versions.go:222-226.
    """
    valid = (models.ASC_SORT_ORDER, models.DESC_SORT_ORDER)
    if s not in valid:
        return (
            f"value '{s}' is invalid. Must be one of: "
            f"'{models.ASC_SORT_ORDER}', "
            f"'{models.DESC_SORT_ORDER}'."
        )
    return None


def validate_visibility(v: str) -> str | None:
    """Validate ``Visibility``.

    Mirrors Go ``Visibility.Validate()``
    at endpoint_versions.go:229-233.
    """
    valid = (models.ALL_VISIBILITY, models.ONLY_HIDDEN_VISIBILITY,
             models.ONLY_VISIBLE_VISIBILITY)
    if v not in valid:
        return (
            f"value '{v}' is invalid. Must be one of: "
            f"'{models.ALL_VISIBILITY}', "
            f"'{models.ONLY_HIDDEN_VISIBILITY}', "
            f"'{models.ONLY_VISIBLE_VISIBILITY}'."
        )
    return None


def validate_list_endpoint_versions_request(r) -> str | None:
    """Validate ``ListEndpointVersionsRequest``.

    Mirrors Go ``ListEndpointVersionsRequest.Validate()``
    at endpoint_versions.go:236-243.
    """
    errors: dict = {}
    if not r.api_endpoint_id:
        errors["APIEndpointID"] = "cannot be blank"
    if r.sort_by:
        sort_err = validate_list_endpoint_version_sort_type(r.sort_by)
        if sort_err:
            errors["SortBy"] = sort_err
    if r.sort_order:
        order_err = validate_sort_order_type(r.sort_order)
        if order_err:
            errors["SortOrder"] = order_err
    # Python model field is 'visibility'; Go field key is 'Show'.
    show = getattr(r, "visibility", getattr(r, "show", ""))
    if show:
        show_err = validate_visibility(show)
        if show_err:
            errors["Show"] = show_err
    return parse_validation_errors(errors)


def validate_endpoint_version_request(r) -> str | None:
    """Validate ``EndpointVersionRequest``.

    Mirrors Go ``EndpointVersionRequest.Validate()``
    at endpoint_versions.go:246-251.
    """
    errors: dict = {}
    if not r.api_endpoint_id:
        errors["APIEndpointID"] = "cannot be blank"
    if not r.version_number:
        errors["VersionNumber"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_get_endpoint_version_request(r) -> str | None:
    """Validate ``GetEndpointVersionRequest``.

    Delegates to ``validate_endpoint_version_request``.
    Mirrors Go ``GetEndpointVersionRequest.Validate()``
    at endpoint_versions.go:254-256.
    """
    return validate_endpoint_version_request(r)


def validate_clone_endpoint_version_request(r) -> str | None:
    """Validate ``CloneEndpointVersionRequest``.

    Delegates to ``validate_endpoint_version_request``.
    Mirrors Go ``CloneEndpointVersionRequest.Validate()``
    at endpoint_versions.go:259-261.
    """
    return validate_endpoint_version_request(r)


def validate_delete_endpoint_version_request(r) -> str | None:
    """Validate ``DeleteEndpointVersionRequest``.

    Delegates to ``validate_endpoint_version_request``.
    Mirrors Go ``DeleteEndpointVersionRequest.Validate()``
    at endpoint_versions.go:264-266.
    """
    return validate_endpoint_version_request(r)


# ---------------------------------------------------------------------------
# UpdateEndpointVersionRequestBody nested helpers
# ---------------------------------------------------------------------------

def _collect_update_endpoint_version_request_body_errors(  # pylint: disable=too-many-branches
        e) -> dict | None:
    """Collect ``UpdateEndpointVersionRequestBody`` validation errors."""
    errors: dict = {}

    # Required scalars
    if not e.api_endpoint_id:
        errors["APIEndpointID"] = "cannot be blank"
    if not e.api_endpoint_name:
        errors["APIEndpointName"] = "cannot be blank"
    if not e.contract_id:
        errors["ContractID"] = "cannot be blank"
    if not e.group_id:
        errors["GroupID"] = "cannot be blank"
    if not e.api_endpoint_hosts:
        errors["APIEndpointHosts"] = "cannot be blank"

    # Optional enum-typed fields — validate only when set
    if e.consume_type is not None:
        ct_err = validate_consume_type(e.consume_type)
        if ct_err:
            errors["ConsumeType"] = ct_err

    if e.api_endpoint_scheme is not None:
        aes_err = validate_api_endpoint_scheme(e.api_endpoint_scheme)
        if aes_err:
            errors["APIEndpointScheme"] = aes_err

    # Optional nested struct fields — validate only when non-None
    if e.security_scheme is not None:
        ss_err = _collect_security_scheme_errors(e.security_scheme)
        if ss_err:
            errors["SecurityScheme"] = ss_err

    if e.akamai_security_restrictions is not None:
        asr_err = _collect_akamai_security_restrictions_errors(
            e.akamai_security_restrictions)
        if asr_err:
            errors["AkamaiSecurityRestrictions"] = asr_err

    if e.api_version_info is not None:
        vi_err = _collect_api_version_info_errors(e.api_version_info)
        if vi_err:
            errors["APIVersionInfo"] = vi_err

    # Slice of validatable items
    if e.api_resources:
        res_errors: dict = {}
        for i, resource in enumerate(e.api_resources):
            res_err = _collect_api_resource_errors(resource)
            if res_err:
                res_errors[str(i)] = res_err
        if res_errors:
            errors["APIResources"] = res_errors

    return errors or None


def validate_update_endpoint_version_request_body(e) -> str | None:
    """Validate ``UpdateEndpointVersionRequestBody``.

    Mirrors Go ``UpdateEndpointVersionRequestBody.Validate()``
    at endpoint_versions.go:278-292.
    """
    errs = _collect_update_endpoint_version_request_body_errors(e)
    if not errs:
        return None
    return parse_validation_errors(errs)


def validate_update_endpoint_version_request(u) -> str | None:
    """Validate ``UpdateEndpointVersionRequest``.

    Mirrors Go ``UpdateEndpointVersionRequest.Validate()``
    at endpoint_versions.go:269-275.
    """
    errors: dict = {}
    if not u.api_endpoint_id:
        errors["APIEndpointID"] = "cannot be blank"
    if not u.version_number:
        errors["VersionNumber"] = "cannot be blank"
    if u.body is None:
        errors["Body"] = "cannot be blank"
    else:
        body_err = _collect_update_endpoint_version_request_body_errors(u.body)
        if body_err:
            errors["Body"] = body_err
    return parse_validation_errors(errors)


# ---------------------------------------------------------------------------
# Typed-value validators (endpoint_versions.go)
# ---------------------------------------------------------------------------

def validate_consume_type(c: str) -> str | None:
    """Validate ``ConsumeType``.

    Mirrors Go ``ConsumeType.Validate()``
    at endpoint_versions.go:295-299.

    Note: the Go source contains a typo ``in invalid``; we reproduce it.
    """
    valid = (
        models.CONSUME_TYPE_JSON, models.CONSUME_TYPE_XML,
        models.CONSUME_TYPE_JSONXML, models.CONSUME_TYPE_ANY,
        models.CONSUME_TYPE_URLENCODED, models.CONSUME_TYPE_JSON_URLENCODED,
        models.CONSUME_TYPE_XML_URLENCODED,
        models.CONSUME_TYPE_JSONXML_URLENCODED,
        models.CONSUME_TYPE_NONE,
    )
    if c not in valid:
        return (
            f"value '{c}' in invalid. Must be one of: "
            f"'{models.CONSUME_TYPE_JSON}', "
            f"'{models.CONSUME_TYPE_XML}', "
            f"'{models.CONSUME_TYPE_JSONXML}', "
            f"'{models.CONSUME_TYPE_ANY}', "
            f"'{models.CONSUME_TYPE_URLENCODED}', "
            f"'{models.CONSUME_TYPE_JSON_URLENCODED}', "
            f"'{models.CONSUME_TYPE_XML_URLENCODED}', "
            f"'{models.CONSUME_TYPE_JSONXML_URLENCODED}', "
            f"'{models.CONSUME_TYPE_NONE}'"
        )
    return None


def validate_api_endpoint_scheme(s: str) -> str | None:
    """Validate ``APIEndpointScheme``.

    Mirrors Go ``APIEndpointScheme.Validate()``
    at endpoint_versions.go:302-306.
    """
    valid = (
        models.API_ENDPOINT_SCHEME_HTTP,
        models.API_ENDPOINT_SCHEME_HTTPS,
        models.API_ENDPOINT_SCHEME_HTTP_HTTPS,
    )
    if s not in valid:
        return (
            f"value '{s}' is invalid. Must be one of: "
            f"'{models.API_ENDPOINT_SCHEME_HTTP}', "
            f"'{models.API_ENDPOINT_SCHEME_HTTPS}', "
            f"'{models.API_ENDPOINT_SCHEME_HTTP_HTTPS}'"
        )
    return None


def validate_api_source(s: str) -> str | None:
    """Validate ``APISource``.

    Mirrors Go ``APISource.Validate()``
    at endpoint_versions.go:309-313.
    """
    valid = (models.API_SOURCE_USER, models.API_SOURCE_API_DISCOVERY)
    if s not in valid:
        return (
            f"value '{s}' is invalid. Must be one of: "
            f"'{models.API_SOURCE_USER}', "
            f"'{models.API_SOURCE_API_DISCOVERY}'"
        )
    return None


def validate_source_type(s: str) -> str | None:
    """Validate ``SourceType``.

    Mirrors Go ``SourceType.Validate()``
    at endpoint_versions.go:316-320.
    """
    valid = (models.SOURCE_TYPE_SWAGGER, models.SOURCE_TYPE_RAML)
    if s not in valid:
        return (
            f"value '{s}' is invalid. Must be one of: "
            f"'{models.SOURCE_TYPE_SWAGGER}', "
            f"'{models.SOURCE_TYPE_RAML}'"
        )
    return None


def _collect_source_errors(s) -> dict | None:
    """Collect ``Source`` validation errors."""
    errors: dict = {}
    if s.type:
        t_err = validate_source_type(s.type)
        if t_err:
            errors["Type"] = t_err
    return errors or None


def validate_source(s) -> str | None:
    """Validate ``Source``.

    Mirrors Go ``Source.Validate()``
    at endpoint_versions.go:323-327.
    """
    errs = _collect_source_errors(s)
    if not errs:
        return None
    return parse_validation_errors(errs)


# ===================================================================
# Endpoint validators  (endpoints.go)
# ===================================================================

def validate_get_endpoint_request(r) -> str | None:
    """Validate ``GetEndpointRequest``.

    Mirrors Go ``GetEndpointRequest.Validate()``
    at endpoints.go:641-645.
    """
    errors: dict = {}
    if not r.api_endpoint_id:
        errors["APIEndpointID"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_show_endpoint_request(r) -> str | None:
    """Validate ``ShowEndpointRequest``.

    Mirrors Go ``ShowEndpointRequest.Validate()``
    at endpoints.go:648-652.
    """
    errors: dict = {}
    if not r.api_endpoint_id:
        errors["APIEndpointID"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_hide_endpoint_request(r) -> str | None:
    """Validate ``HideEndpointRequest``.

    Mirrors Go ``HideEndpointRequest.Validate()``
    at endpoints.go:655-659.
    """
    errors: dict = {}
    if not r.api_endpoint_id:
        errors["APIEndpointID"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_delete_endpoint_request(r) -> str | None:
    """Validate ``DeleteEndpointRequest``.

    Mirrors Go ``DeleteEndpointRequest.Validate()``
    at endpoints.go:662-666.
    """
    errors: dict = {}
    if not r.api_endpoint_id:
        errors["APIEndpointID"] = "cannot be blank"
    return parse_validation_errors(errors)


def validate_list_endpoint_sort_type(s: str) -> str | None:
    """Validate ``ListEndpointSortType``.

    Mirrors Go ``ListEndpointSortType.Validate()``
    at endpoints.go:669-673.
    """
    valid = (models.NAME_SORT, models.UPDATE_ENDPOINT_DATE_SORT)
    if s not in valid:
        return (
            f"value '{s}' is not valid. Must be one of: "
            f"'{models.NAME_SORT}' or "
            f"'{models.UPDATE_ENDPOINT_DATE_SORT}'"
        )
    return None


def validate_version_preference(v: str) -> str | None:
    """Validate ``VersionPreference``.

    Mirrors Go ``VersionPreference.Validate()``
    at endpoints.go:676-680.
    """
    valid = (
        models.VERSION_PREFERENCE_LAST_UPDATED,
        models.VERSION_PREFERENCE_ACTIVATED_FIRST,
    )
    if v not in valid:
        return (
            f"value '{v}' is not valid. Must be one of: "
            f"'{models.VERSION_PREFERENCE_LAST_UPDATED}', "
            f"'{models.VERSION_PREFERENCE_ACTIVATED_FIRST}' "
            "or '' (empty)"
        )
    return None


def validate_list_endpoints_request(r) -> str | None:
    """Validate ``ListEndpointsRequest``.

    Mirrors Go ``ListEndpointsRequest.Validate()``
    at endpoints.go:683-690.
    """
    errors: dict = {}
    if r.sort_by:
        sort_err = validate_list_endpoint_sort_type(r.sort_by)
        if sort_err:
            errors["SortBy"] = sort_err
    if r.sort_order:
        order_err = validate_sort_order_type(r.sort_order)
        if order_err:
            errors["SortOrder"] = order_err
    if r.version_preference:
        vp_err = validate_version_preference(r.version_preference)
        if vp_err:
            errors["VersionPreference"] = vp_err
    if r.show:
        show_err = validate_visibility(r.show)
        if show_err:
            errors["Show"] = show_err
    return parse_validation_errors(errors)


# ---------------------------------------------------------------------------
# SecurityScheme nested helpers
# ---------------------------------------------------------------------------

def _collect_security_scheme_detail_errors(s) -> dict | None:
    """Collect ``SecuritySchemeDetail`` validation errors."""
    errors: dict = {}
    if not s.api_key_location:
        errors["APIKeyLocation"] = "cannot be blank"
    else:
        loc_err = validate_api_key_location(s.api_key_location)
        if loc_err:
            errors["APIKeyLocation"] = loc_err
    if not s.api_key_name:
        errors["APIKeyName"] = "cannot be blank"
    return errors or None


def _collect_security_scheme_errors(s) -> dict | None:
    """Collect ``SecurityScheme`` validation errors."""
    errors: dict = {}
    if not s.security_scheme_type:
        errors["SecuritySchemeType"] = "cannot be blank"
    elif s.security_scheme_type != "apikey":
        errors["SecuritySchemeType"] = (
            f"value '{s.security_scheme_type}' is not valid. "
            "Must be: 'apikey'"
        )
    if s.security_scheme_detail is None or _is_empty_dataclass(
            s.security_scheme_detail):
        errors["SecuritySchemeDetail"] = "cannot be blank"
    else:
        detail_err = _collect_security_scheme_detail_errors(
            s.security_scheme_detail)
        if detail_err:
            errors["SecuritySchemeDetail"] = detail_err
    return errors or None


def validate_security_scheme(s) -> str | None:
    """Validate ``SecurityScheme``.

    Mirrors Go ``SecurityScheme.Validate()``
    at endpoints.go:693-698.
    """
    errs = _collect_security_scheme_errors(s)
    if not errs:
        return None
    return parse_validation_errors(errs)


def validate_api_key_location(loc: str) -> str | None:
    """Validate ``APIKeyLocation``.

    Mirrors Go ``APIKeyLocation.Validate()``
    at endpoints.go:701-705.
    """
    valid = (
        models.API_KEY_LOCATION_COOKIE,
        models.API_KEY_LOCATION_HEADER,
        models.API_KEY_LOCATION_QUERY,
    )
    if loc not in valid:
        return (
            f"value '{loc}' is not valid. Must be one of: "
            f"'{models.API_KEY_LOCATION_COOKIE}', "
            f"'{models.API_KEY_LOCATION_HEADER}', "
            f"'{models.API_KEY_LOCATION_QUERY}'"
        )
    return None


def validate_security_scheme_detail(s) -> str | None:
    """Validate ``SecuritySchemeDetail``.

    Mirrors Go ``SecuritySchemeDetail.Validate()``
    at endpoints.go:708-713.
    """
    errs = _collect_security_scheme_detail_errors(s)
    if not errs:
        return None
    return parse_validation_errors(errs)


# ---------------------------------------------------------------------------
# APIParameterRestriction nested helpers
# ---------------------------------------------------------------------------

def _collect_length_restriction_errors(r) -> dict | None:
    """Collect ``LengthRestriction`` validation errors."""
    errors: dict = {}
    if r.length_max is not None and r.length_max < 0:
        errors["LengthMax"] = "must be no less than 0"
    if r.length_min is not None and r.length_min < 0:
        errors["LengthMin"] = "must be no less than 0"
    return errors or None


def _collect_response_restriction_errors(r) -> dict | None:
    """Collect ``ResponseRestriction`` validation errors."""
    errors: dict = {}
    max_body = getattr(r, "max_body_size", None)
    if max_body is not None:
        mb_err = validate_max_body_size(max_body)
        if mb_err:
            errors["MaxBodySize"] = mb_err
    return errors or None


def _collect_api_parameter_restriction_errors(r) -> dict | None:
    """Collect ``APIParameterRestriction`` validation errors."""
    errors: dict = {}
    if r.length_restriction is not None:
        lr_err = _collect_length_restriction_errors(r.length_restriction)
        if lr_err:
            errors["LengthRestriction"] = lr_err
    # ArrayRestriction: Go has no Validate() — always passes
    if r.response_restriction is not None:
        rr_err = _collect_response_restriction_errors(r.response_restriction)
        if rr_err:
            errors["ResponseRestriction"] = rr_err
    return errors or None


def validate_api_parameter_restriction(r) -> str | None:
    """Validate ``APIParameterRestriction``.

    Mirrors Go ``APIParameterRestriction.Validate()``
    at endpoints.go:716-722.
    """
    errs = _collect_api_parameter_restriction_errors(r)
    if not errs:
        return None
    return parse_validation_errors(errs)


def validate_length_restriction(r) -> str | None:
    """Validate ``LengthRestriction``.

    Mirrors Go ``LengthRestriction.Validate()``
    at endpoints.go:725-730.
    """
    errs = _collect_length_restriction_errors(r)
    if not errs:
        return None
    return parse_validation_errors(errs)


def validate_max_body_size(m: str) -> str | None:
    """Validate ``MaxBodySize``.

    Mirrors Go ``MaxBodySize.Validate()``
    at endpoints.go:733-737.
    """
    valid = (
        models.MAX_BODY_SIZE_SIZE_6K,
        models.MAX_BODY_SIZE_SIZE_8K,
        models.MAX_BODY_SIZE_SIZE_12K,
        models.MAX_BODY_SIZE_SIZE_16K,
        models.MAX_BODY_SIZE_NO_LIMIT,
        models.MAX_BODY_SIZE_NULL,
    )
    if m not in valid:
        return (
            f"value '{m}' is not valid. Must be one of: "
            f"'{models.MAX_BODY_SIZE_SIZE_6K}', "
            f"'{models.MAX_BODY_SIZE_SIZE_8K}', "
            f"'{models.MAX_BODY_SIZE_SIZE_12K}', "
            f"'{models.MAX_BODY_SIZE_SIZE_16K}', "
            f"'{models.MAX_BODY_SIZE_NO_LIMIT}' or "
            f"{models.MAX_BODY_SIZE_NULL}"
        )
    return None


def validate_response_restriction(r) -> str | None:
    """Validate ``ResponseRestriction``.

    Mirrors Go ``ResponseRestriction.Validate()``
    at endpoints.go:740-744.
    """
    errs = _collect_response_restriction_errors(r)
    if not errs:
        return None
    return parse_validation_errors(errs)


def validate_api_parameter_location(loc: str) -> str | None:
    """Validate ``APIParameterLocation``.

    Mirrors Go ``APIParameterLocation.Validate()``
    at endpoints.go:747-751.
    """
    valid = (
        models.API_PARAMETER_LOCATION_QUERY,
        models.API_PARAMETER_LOCATION_HEADER,
        models.API_PARAMETER_LOCATION_PATH,
        models.API_PARAMETER_LOCATION_COOKIE,
        models.API_PARAMETER_LOCATION_BODY,
    )
    if loc not in valid:
        return (
            f"value '{loc}' is not valid. Must be one of: "
            f"'{models.API_PARAMETER_LOCATION_QUERY}', "
            f"'{models.API_PARAMETER_LOCATION_HEADER}', "
            f"'{models.API_PARAMETER_LOCATION_PATH}', "
            f"'{models.API_PARAMETER_LOCATION_COOKIE}', "
            f"'{models.API_PARAMETER_LOCATION_BODY}'"
        )
    return None


def validate_api_parameter_type(t: str) -> str | None:
    """Validate ``APIParameterType``.

    Mirrors Go ``APIParameterType.Validate()``
    at endpoints.go:754-758.
    """
    valid = (
        models.API_PARAMETER_TYPE_STRING,
        models.API_PARAMETER_TYPE_INTEGER,
        models.API_PARAMETER_TYPE_NUMBER,
        models.API_PARAMETER_TYPE_BOOLEAN,
        models.API_PARAMETER_TYPE_JSONXML,
    )
    if t not in valid:
        return (
            f"value '{t}' is not valid. Must be one of "
            f"'{models.API_PARAMETER_TYPE_STRING}', "
            f"'{models.API_PARAMETER_TYPE_INTEGER}', "
            f"'{models.API_PARAMETER_TYPE_NUMBER}', "
            f"'{models.API_PARAMETER_TYPE_BOOLEAN}', "
            f"or '{models.API_PARAMETER_TYPE_JSONXML}'"
        )
    return None


# ---------------------------------------------------------------------------
# APIParameter / APIResource nested helpers
# ---------------------------------------------------------------------------

def _collect_api_parameter_errors(p) -> dict | None:
    """Collect ``APIParameter`` validation errors."""
    errors: dict = {}
    if not p.api_parameter_name:
        errors["APIParameterName"] = "cannot be blank"
    if not p.api_parameter_location:
        errors["APIParameterLocation"] = "cannot be blank"
    else:
        loc_err = validate_api_parameter_location(p.api_parameter_location)
        if loc_err:
            errors["APIParameterLocation"] = loc_err
    if not p.api_parameter_type:
        errors["APIParameterType"] = "cannot be blank"
    else:
        t_err = validate_api_parameter_type(p.api_parameter_type)
        if t_err:
            errors["APIParameterType"] = t_err
    if p.api_parameter_restriction is not None:
        apr_err = _collect_api_parameter_restriction_errors(
            p.api_parameter_restriction)
        if apr_err:
            errors["APIParameterRestriction"] = apr_err
    return errors or None


def validate_api_parameter(p) -> str | None:
    """Validate ``APIParameter``.

    Mirrors Go ``APIParameter.Validate()``
    at endpoints.go:761-768.
    """
    errs = _collect_api_parameter_errors(p)
    if not errs:
        return None
    return parse_validation_errors(errs)


def validate_api_resource_methods(m: str) -> str | None:
    """Validate ``APIResourceMethods``.

    Mirrors Go ``APIResourceMethods.Validate()``
    at endpoints.go:771-775.
    """
    valid = (
        models.API_RESOURCE_METHODS_GET,
        models.API_RESOURCE_METHODS_PUT,
        models.API_RESOURCE_METHODS_POST,
        models.API_RESOURCE_METHODS_DELETE,
        models.API_RESOURCE_METHODS_HEAD,
        models.API_RESOURCE_METHODS_PATCH,
        models.API_RESOURCE_METHODS_OPTIONS,
    )
    if m not in valid:
        return (
            f"value '{m}' is not valid. Must be one of: "
            f"'{models.API_RESOURCE_METHODS_GET}', "
            f"'{models.API_RESOURCE_METHODS_PUT}', "
            f"'{models.API_RESOURCE_METHODS_POST}', "
            f"'{models.API_RESOURCE_METHODS_DELETE}', "
            f"'{models.API_RESOURCE_METHODS_HEAD}', "
            f"'{models.API_RESOURCE_METHODS_PATCH}', "
            f"'{models.API_RESOURCE_METHODS_OPTIONS}'"
        )
    return None


def _collect_api_resource_method_errors(a) -> dict | None:
    """Collect ``APIResourceMethod`` validation errors."""
    errors: dict = {}
    if not a.api_resource_method:
        errors["APIResourceMethod"] = "cannot be blank"
    else:
        m_err = validate_api_resource_methods(a.api_resource_method)
        if m_err:
            errors["APIResourceMethod"] = m_err
    if a.api_parameters:
        param_errors: dict = {}
        for i, param in enumerate(a.api_parameters):
            pe = _collect_api_parameter_errors(param)
            if pe:
                param_errors[str(i)] = pe
        if param_errors:
            errors["APIParameters"] = param_errors
    return errors or None


def validate_api_resource_method(a) -> str | None:
    """Validate ``APIResourceMethod``.

    Mirrors Go ``APIResourceMethod.Validate()``
    at endpoints.go:778-783.
    """
    errs = _collect_api_resource_method_errors(a)
    if not errs:
        return None
    return parse_validation_errors(errs)


def _collect_api_resource_errors(a) -> dict | None:
    """Collect ``APIResource`` validation errors."""
    errors: dict = {}
    if not a.api_resource_name:
        errors["APIResourceName"] = "cannot be blank"
    if not a.resource_path:
        errors["ResourcePath"] = "cannot be blank"
    if a.api_resource_methods:
        method_errors: dict = {}
        for i, method in enumerate(a.api_resource_methods):
            me = _collect_api_resource_method_errors(method)
            if me:
                method_errors[str(i)] = me
        if method_errors:
            errors["APIResourceMethods"] = method_errors
    return errors or None


def validate_api_resource(a) -> str | None:
    """Validate ``APIResource``.

    Mirrors Go ``APIResource.Validate()``
    at endpoints.go:786-792.
    """
    errs = _collect_api_resource_errors(a)
    if not errs:
        return None
    return parse_validation_errors(errs)


# ---------------------------------------------------------------------------
# AkamaiSecurityRestrictions
# ---------------------------------------------------------------------------

def _collect_akamai_security_restrictions_errors(r) -> dict | None:
    """Collect ``AkamaiSecurityRestrictions`` validation errors."""
    errors: dict = {}
    if r.positive_security_version is not None:
        if r.positive_security_version not in (1, 2):
            errors["POSITIVE_SECURITY_VERSION"] = (
                f"value {r.positive_security_version} is not valid. "
                "Must be one of 1, 2"
            )
    return errors or None


def validate_akamai_security_restrictions(r) -> str | None:
    """Validate ``AkamaiSecurityRestrictions``.

    Mirrors Go ``AkamaiSecurityRestrictions.Validate()``
    at endpoints.go:795-799.
    """
    errs = _collect_akamai_security_restrictions_errors(r)
    if not errs:
        return None
    return parse_validation_errors(errs)


# ---------------------------------------------------------------------------
# APIVersionInfo
# ---------------------------------------------------------------------------

def validate_api_version_info_location(loc: str) -> str | None:
    """Validate ``APIVersionInfoLocation``.

    Mirrors Go ``APIVersionInfoLocation.Validate()``
    at endpoints.go:802-806.
    """
    valid = (
        models.API_VERSION_LOCATION_HEADER,
        models.API_VERSION_LOCATION_BASE_PATH,
        models.API_VERSION_LOCATION_QUERY,
    )
    if loc not in valid:
        return (
            f"value '{loc}' is not valid. Must be one of "
            f"'{models.API_VERSION_LOCATION_HEADER}', "
            f"'{models.API_VERSION_LOCATION_BASE_PATH}', "
            f"'{models.API_VERSION_LOCATION_QUERY}'"
        )
    return None


def _collect_api_version_info_errors(a) -> dict | None:
    """Collect ``APIVersionInfo`` validation errors."""
    errors: dict = {}
    if not a.location:
        errors["Location"] = "cannot be blank"
    else:
        loc_err = validate_api_version_info_location(a.location)
        if loc_err:
            errors["Location"] = loc_err
    return errors or None


def validate_api_version_info(a) -> str | None:
    """Validate ``APIVersionInfo``.

    Mirrors Go ``APIVersionInfo.Validate()``
    at endpoints.go:809-813.
    """
    errs = _collect_api_version_info_errors(a)
    if not errs:
        return None
    return parse_validation_errors(errs)


# ===================================================================
# RegisterEndpointRequest  (endpoints.go:816-830)
# ===================================================================

def validate_register_endpoint_request(r) -> str | None:  # pylint: disable=too-many-branches,too-many-locals,too-many-statements
    """Validate ``RegisterEndpointRequest``.

    Mirrors Go ``RegisterEndpointRequest.Validate()``
    at endpoints.go:816-830.
    """
    errors: dict = {}

    # Required scalars
    if not r.api_endpoint_name:
        errors["APIEndpointName"] = "cannot be blank"
    if not r.api_endpoint_hosts:
        errors["APIEndpointHosts"] = "cannot be blank"
    if not r.contract_id:
        errors["ContractID"] = "cannot be blank"
    if not r.group_id:
        errors["GroupID"] = "cannot be blank"

    # BasePath: must not end with '/'
    base_path = getattr(r, "base_path", "")
    if base_path and base_path.endswith("/"):
        errors["BasePath"] = "basePath should not end with `/`"

    # Optional enum-typed fields — validate when non-empty
    api_scheme = getattr(r, "api_endpoint_scheme", "")
    if api_scheme:
        aes_err = validate_api_endpoint_scheme(api_scheme)
        if aes_err:
            errors["APIEndpointScheme"] = aes_err

    consume = getattr(r, "consume_type", "")
    if consume:
        ct_err = validate_consume_type(consume)
        if ct_err:
            errors["ConsumeType"] = ct_err

    api_source = getattr(r, "api_source", "")
    if api_source:
        as_err = validate_api_source(api_source)
        if as_err:
            errors["APISource"] = as_err

    # Slice of validatable items
    api_resources = getattr(r, "api_resources", None) or []
    if api_resources:
        res_errors: dict = {}
        for i, resource in enumerate(api_resources):
            re_err = _collect_api_resource_errors(resource)
            if re_err:
                res_errors[str(i)] = re_err
        if res_errors:
            errors["APIResources"] = res_errors

    # NilOrNotEmpty: APIVersionInfo
    api_version_info = getattr(r, "api_version_info", None)
    if api_version_info is not None:
        if _is_empty_dataclass(api_version_info):
            errors["APIVersionInfo"] = "cannot be blank"
        else:
            vi_err = _collect_api_version_info_errors(api_version_info)
            if vi_err:
                errors["APIVersionInfo"] = vi_err

    # NilOrNotEmpty: AkamaiSecurityRestrictions
    akamai_sec = getattr(r, "akamai_security_restrictions", None)
    if akamai_sec is not None:
        if _is_empty_dataclass(akamai_sec):
            errors["AkamaiSecurityRestrictions"] = "cannot be blank"
        else:
            asr_err = _collect_akamai_security_restrictions_errors(akamai_sec)
            if asr_err:
                errors["AkamaiSecurityRestrictions"] = asr_err

    return parse_validation_errors(errors)


# ===================================================================
# Import-from-file validators  (endpoints.go:833-866)
# ===================================================================

def validate_import_file_format(f: str) -> str | None:
    """Validate ``ImportFileFormat``.

    Mirrors Go ``ImportFileFormat.Validate()``
    at endpoints.go:833-837.
    """
    valid = (models.IMPORT_FILE_FORMAT_SWAGGER, models.IMPORT_FILE_FORMAT_RAML)
    if f not in valid:
        return (
            f"value '{f}' is not valid. Must be one of: "
            f"'{models.IMPORT_FILE_FORMAT_SWAGGER}', "
            f"'{models.IMPORT_FILE_FORMAT_RAML}'"
        )
    return None


def validate_import_file_source(f: str) -> str | None:
    """Validate ``ImportFileSource``.

    Mirrors Go ``ImportFileSource.Validate()``
    at endpoints.go:840-844.
    """
    valid = (models.IMPORT_FILE_SOURCE_URL, models.IMPORT_FILE_SOURCE_BASE64)
    if f not in valid:
        return (
            f"value '{f}' is not valid. Must be one of: "
            f"'{models.IMPORT_FILE_SOURCE_URL}', "
            f"'{models.IMPORT_FILE_SOURCE_BASE64}'"
        )
    return None


def validate_register_endpoint_from_file_request(r) -> str | None:  # pylint: disable=too-many-branches
    """Validate ``RegisterEndpointFromFileRequest``.

    Mirrors Go ``RegisterEndpointFromFileRequest.Validate()``
    at endpoints.go:847-866.

    Includes conditional validation based on ``import_file_source``:
    - When ``BODY_BASE64``: ``import_file_content`` required,
      ``import_url`` forbidden.
    - When ``URL``: ``import_url`` required (must be valid URL),
      ``import_file_content`` forbidden.
    """
    errors: dict = {}

    # Required scalars
    if not r.contract_id:
        errors["ContractID"] = "cannot be blank"
    if not r.group_id:
        errors["GroupID"] = "cannot be blank"
    if not r.import_file_format:
        errors["ImportFileFormat"] = "cannot be blank"
    else:
        fmt_err = validate_import_file_format(r.import_file_format)
        if fmt_err:
            errors["ImportFileFormat"] = fmt_err
    if not r.import_file_source:
        errors["ImportFileSource"] = "cannot be blank"
    else:
        src_err = validate_import_file_source(r.import_file_source)
        if src_err:
            errors["ImportFileSource"] = src_err

    # Conditional: ImportFileContent
    if r.import_file_source == models.IMPORT_FILE_SOURCE_BASE64:
        if not r.import_file_content:
            errors["ImportFileContent"] = (
                "must be set when ImportFileSource=='BODY_BASE64'"
            )
    elif r.import_file_source == models.IMPORT_FILE_SOURCE_URL:
        if r.import_file_content:
            errors["ImportFileContent"] = (
                "must not be set when ImportFileSource=='URL'"
            )

    # Conditional: ImportURL
    if r.import_file_source == models.IMPORT_FILE_SOURCE_URL:
        if not r.import_url:
            errors["ImportURL"] = (
                "required field when ImportFileSource=='URL'"
            )
        else:
            parsed = urllib.parse.urlparse(r.import_url)
            if not (parsed.scheme and parsed.netloc):
                errors["ImportURL"] = (
                    "must be a valid URL when ImportFileSource=='URL'"
                )
    elif r.import_url:
        errors["ImportURL"] = (
            "should not be set when ImportFileSource=='BODY_BASE64'"
        )

    return parse_validation_errors(errors)
