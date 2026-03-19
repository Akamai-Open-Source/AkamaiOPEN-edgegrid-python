"""Sentinel errors and Error class for the mTLS Trust Store API."""
# pylint: disable=invalid-name

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ErrorItem:
    """Details about an individual error in an API response.

    Mirrors Go mtlstruststore.ErrorItem struct field-for-field.
    """

    detail: str = ""
    pointer: str = ""
    context_info: dict[str, Any] | None = None
    title: str = ""
    type: str = ""  # pylint: disable=redefined-builtin


@dataclass
class Error(Exception):  # pylint: disable=too-many-instance-attributes
    """mTLS Trust Store API error.

    Parses RFC 7807 problem detail responses from the mTLS Trust Store
    API.  Mirrors Go mtlstruststore.Error struct exactly.

    Fields match Go struct JSON tags:

    * type       – Error type URI identifier
    * title      – Human-readable error title
    * detail     – Detailed error description
    * status     – HTTP response status code
    * context_info – Contextual information (optional)
    * instance   – Error instance identifier (optional)
    * errors     – Nested error items (optional)
    * pointer    – JSON pointer to the offending field (optional)
    """

    type: str = ""  # pylint: disable=redefined-builtin
    title: str = ""
    detail: str = ""
    status: int = 0
    context_info: dict[str, Any] | None = None
    instance: str = ""
    errors: list[ErrorItem] | None = field(default=None)
    pointer: str = ""

    def __str__(self) -> str:
        """Format error as indented JSON.

        Mirrors Go ``Error.Error()`` which calls
        ``json.MarshalIndent(e, "", "\\t")``.
        """
        try:
            msg = json.dumps(self._to_dict(), indent="\t")
            return f"API error: \n{msg}"
        except (TypeError, ValueError) as err:
            return f"error marshaling API error: {err}"

    def _to_dict(self) -> dict[str, Any]:
        """Build a dict for JSON serialisation, omitting empty fields."""
        result: dict[str, Any] = {}
        if self.type:
            result["type"] = self.type
        if self.title:
            result["title"] = self.title
        if self.detail:
            result["detail"] = self.detail
        if self.status:
            result["status"] = self.status
        if self.context_info is not None:
            result["contextInfo"] = self.context_info
        if self.instance:
            result["instance"] = self.instance
        if self.errors is not None:
            result["errors"] = [
                {
                    k: v
                    for k, v in {
                        "detail": item.detail,
                        "pointer": item.pointer,
                        "contextInfo": item.context_info,
                        "title": item.title,
                        "type": item.type,
                    }.items()
                    if v
                }
                for item in self.errors
            ]
        if self.pointer:
            result["pointer"] = self.pointer
        return result

    def is_equivalent(self, target) -> bool:
        """Check whether this error matches *target*.

        Mirrors Go ``Error.Is()`` with the full matcher table.

        When *target* is a sentinel error string the matcher table is
        consulted: ``True`` is returned only when this error's
        ``status`` and ``type`` both match the table entry.

        When *target* is an ``Error`` instance the comparison falls
        through to status then string-representation equality.

        Args:
            target: A sentinel error string constant or an ``Error``.

        Returns:
            ``True`` if this error is equivalent to *target*.
        """
        if isinstance(target, str):
            for sentinel, status, err_type in _ERROR_MATCHERS:
                if target == sentinel:
                    if (
                        self.status == status
                        and self.type == err_type
                    ):
                        return True
            return False

        if isinstance(target, Error):
            if self is target:
                return True
            if self.status != target.status:
                return False
            return str(self) == str(target)

        return False


# ErrStructValidation is the sentinel value for struct validation failures.
# Mirrors Go: var ErrStructValidation = errors.New("struct validation")
ErrStructValidation = "struct validation"


# ---------------------------------------------------------------------------
# Error type URI constants (private).
# Mirrors Go ``const ( … )`` block in errors.go lines 60-111.
# ---------------------------------------------------------------------------

_CA_SET_NOT_FOUND_TYPE = (
    "/mtls-edge-truststore/error-types/ca-set-not-found"
)
_CA_SET_BOUND_TO_HOSTNAME = (
    "/mtls-edge-truststore/error-types/ca-set-bound-to-hostname"
)
_CA_SET_IN_USE_BY_HOSTNAMES = (
    "/mtls-edge-truststore/error-types/ca-set-in-use-by-hostnames"
)
_CA_SET_IN_USE_BY_ENROLLMENTS = (
    "/mtls-edge-truststore/error-types/ca-set-in-use-by-enrollments"
)
_CA_SET_IN_USE_BY_HOSTNAMES_AND_NOT_ENROLLMENTS = (
    "/mtls-edge-truststore/error-types/"
    "ca-set-in-use-by-ccm-hostnames-and-not-cps-enrollments"
)
_CA_SET_ACTIVATION_NOT_FOUND_TYPE = (
    "/mtls-edge-truststore/error-types/"
    "activation-or-deactivation-request-not-found"
)
_CA_SET_DELETE_REQUEST_IN_PROGRESS = (
    "/mtls-edge-truststore/error-types/"
    "delete-ca-set-request-in-progress"
)
_CA_SET_IN_USE_BY_BOTH_ENROLLMENTS_AND_HOSTNAMES = (
    "/mtls-edge-truststore/error-types/"
    "ca-set-in-use-by-both-enrollments-and-hostnames"
)
_CA_SET_NAME_NOT_UNIQUE = (
    "/mtls-edge-truststore/error-types/ca-set-name-is-not-unique"
)
_CA_SET_LIMIT_REACHED = (
    "/mtls-edge-truststore/error-types/ca-set-limit-reached"
)
_CA_SET_CANNOT_BE_DELETED_ACTIVE_VERSIONS = (
    "/mtls-edge-truststore/error-types/"
    "ca-set-cannot-be-deleted-active-versions"
)
_CA_SET_VERSION_DUPLICATE = (
    "/mtls-edge-truststore/error-types/duplicate-ca-set-version"
)
_CA_SET_VERSION_NOT_FOUND_TYPE = (
    "/mtls-edge-truststore/error-types/ca-set-version-not-found"
)
_CA_SET_VERSION_LIMIT_REACHED = (
    "/mtls-edge-truststore/error-types/ca-set-version-limit-reached"
)
_CA_SET_VERSION_IS_ACTIVE = (
    "/mtls-edge-truststore/error-types/ca-set-version-is-active"
)
_CA_SET_VERSION_IS_ACTIVE_ON_NETWORK = (
    "/mtls-edge-truststore/error-types/"
    "ca-set-version-already-active-on-network"
)
_CA_SET_VERSION_WAS_PREVIOUSLY_ACTIVE = (
    "/mtls-edge-truststore/error-types/"
    "ca-set-version-was-previously-active"
)
_CERTIFICATE_VALIDATION_FAILED_FOR_CREATE = (
    "/mtls-edge-truststore/error-types/"
    "certificate-validation-failure-create"
)
_CERTIFICATE_VALIDATION_FAILED_FOR_UPDATE = (
    "/mtls-edge-truststore/error-types/"
    "certificate-validation-failure-update"
)
_CERTIFICATE_VALIDATION_FAILED_FOR_ACTIVATION = (
    "/mtls-edge-truststore/error-types/"
    "certificate-validation-failure-activate"
)
_CERTIFICATE_LIMIT_REACHED = (
    "/mtls-edge-truststore/error-types/certificate-limit-reached"
)
_ANOTHER_ACTIVATION_IN_PROGRESS = (
    "/mtls-edge-truststore/error-types/"
    "another-activation-request-in-progress-in-the-ca-set"
)
_ANOTHER_DEACTIVATION_IN_PROGRESS = (
    "/mtls-edge-truststore/error-types/"
    "another-deactivation-request-in-progress-in-the-ca-set"
)
_ACTIVATION_DEACTIVATION_IN_PROGRESS = (
    "/mtls-edge-truststore/error-types/"
    "ca-set-cannot-be-deleted-in-progress-version-activations"
)
_CA_SET_VERSION_NOT_ACTIVE_ON_NETWORK = (
    "/mtls-edge-truststore/error-types/"
    "ca-set-version-not-active-on-network"
)
_FETCH_ASSOCIATIONS_TIMEOUT = (
    "/mtls-edge-truststore/error-types/"
    "cannot-get-ca-set-associations-timeout"
)
_MISSING_CA_CERT_VERSION = (
    "/mtls-edge-truststore/error-types/missing-caset-version"
)
_NO_ACTIVE_CERT_DELETIONS = (
    "/mtls-edge-truststore/error-types/no-active-cert-deletions"
)
_CERT_VALIDATION_FAILURE = (
    "/mtls-edge-truststore/error-types/"
    "certificate-validation-failure"
)
_UNKNOWN_QUERY_PARAMETERS = (
    "/mtls-edge-truststore/error-types/unknown-query-parameters"
)
_JSON_SCHEMA_VALIDATION = (
    "/mtls-edge-truststore/error-types/"
    "json-schema-validation-error"
)
_ANOTHER_ACTIVATION_JUST_COMPLETED = (
    "/mtls-edge-truststore/error-types/"
    "another-activation-just-completed-in-the-ca-set"
)
_PATH_VARIABLE_QUERY_PARAM_TYPE_MISMATCH = (
    "/mtls-edge-truststore/error-types/"
    "path-variable-query-param-type-mismatch"
)
_UNAUTHORIZED = (
    "/mtls-edge-truststore/error-types/unauthorized"
)
_INTERNAL_ERROR = (
    "/mtls-edge-truststore/error-types/internal-error"
)
_FORBIDDEN = (
    "/mtls-edge-truststore/error-types/forbidden"
)
_FIND_ASSOCIATIONS_FAILED_FOR_ENROLLMENTS_WITH_HOSTNAMES_LINKED = (
    "/mtls-edge-truststore/error-types/"
    "find-associations-failed-for-enrollments"
    "-with-hostnames-linked"
)
_FIND_ASSOCIATIONS_FAILED = (
    "/mtls-edge-truststore/error-types/find-associations-failed"
)
_FIND_ASSOCIATIONS_FAILED_FOR_HOSTNAMES_WITH_ENROLLMENTS_LINKED = (
    "/mtls-edge-truststore/error-types/"
    "find-associations-failed-for-hostnames"
    "-with-enrollments-linked"
)
_FIND_ASSOCIATIONS_FAILED_FOR_ENROLLMENTS_WITH_EMPTY_HOSTNAMES = (
    "/mtls-edge-truststore/error-types/"
    "find-associations-failed-for-enrollments"
    "-with-empty-hostnames"
)
_FIND_ASSOCIATIONS_FAILED_FOR_HOSTNAMES_ENROLLMENTS_NOT_LINKED = (
    "/mtls-edge-truststore/error-types/"
    "find-associations-failed-for-ccm-hostnames"
    "-but-cps-enrollments-not-linked-to-ca-set"
)
_FETCH_ASSOCIATIONS_FAILED_FOR_HOSTNAMES = (
    "/mtls-edge-truststore/error-types/"
    "fetch-associations-failed-for-hostnames"
)
_FETCH_ASSOCIATIONS_FAILED_FOR_ENROLLMENTS = (
    "/mtls-edge-truststore/error-types/"
    "fetch-associations-failed-for-enrollments"
)
_FETCH_ASSOCIATIONS_FAILED = (
    "/mtls-edge-truststore/error-types/fetch-associations-failed"
)
_MEDIA_TYPE_NOT_SUPPORTED = (
    "/mtls-edge-truststore/error-types/media-type-not-supported"
)
_MEDIA_TYPE_NOT_ACCEPTABLE = (
    "/mtls-edge-truststore/error-types/media-type-not-acceptable"
)
_INVALID_JSON = (
    "/mtls-edge-truststore/error-types/invalid-json"
)
_INVALID_FIELD = (
    "/mtls-edge-truststore/error-types/invalid-field"
)
_MISSING_REQUIRED_QUERY_PARAMETER = (
    "/mtls-edge-truststore/error-types/"
    "missing-required-query-parameter"
)
_CA_SET_NAME_VALIDATION_FAILURE = (
    "/mtls-edge-truststore/error-types/"
    "ca-set-name-validation-failure"
)


# ---------------------------------------------------------------------------
# Sentinel error string constants from errors.go (lines 113-272).
# Each mirrors a Go ``var Err* = errors.New(…)`` definition.
# ---------------------------------------------------------------------------

ErrGetCASetNotFound = "ca set not found"
ErrGetCASetVersionNotFound = "ca set version not found"
ErrGetCASetActivationNotFound = "ca set activation not found"
ErrDeleteCASetNotFound = "ca set not found"
ErrDeleteActivationDeactivationInProgress = (
    "ca set cannot be deleted due to in progress activations"
)
ErrCASetDeleteRequestInProgress = "delete ca set request in progress"
ErrCASetVersionIsActive = "ca set version is currently active"
ErrCASetVersionIsActiveOnNetwork = (
    "ca set version is currently active on network"
)
ErrCASetVersionWasPreviouslyActive = (
    "ca set version was previously active"
)
ErrCertificateValidationFailedForCreate = (
    "one or more certificates is invalid"
)
ErrCertificateValidationFailedForUpdate = (
    "one or more certificates is invalid"
)
ErrCertificateValidationFailedForActivation = (
    "one or more certificates is invalid"
)
ErrCertificateLimitReached = (
    "submitted certificates exceed the maximum allowed "
    "certificates limit"
)
ErrCASetVersionLimitReached = (
    "maximum allowed ca set version's limit has been reached"
)
ErrCASetVersionIsDuplicate = (
    "a version with same certificates exists in the ca set"
)
ErrCASetBoundToHostname = "ca set bound to hostname"
ErrCASetInUseByHostnames = "ca set already in use by hostnames"
ErrAnotherActivationInProgress = (
    "another activation request in progress in the ca set"
)
ErrAnotherDeactivationInProgress = (
    "another deactivation request in progress in the ca set"
)
ErrCASetVersionNotActiveOnNetwork = (
    "ca set version not active on network"
)
ErrCASetVersionNotActiveOnNetworkCannotBeDeactivated = (
    "ca set version cannot be deactivated as it is not active "
    "on the network"
)
ErrCASetVersionIsActiveOnNetworkCannotBeActivated = (
    "ca set version cannot be activated as it is already active "
    "on the network"
)
ErrFetchAssociationsTimeout = (
    "fetching associations for ca set got timed out"
)
ErrMissingCASetVersion = "ca set does not contain any version"
ErrCASetNameNotUnique = "ca set name is not unique"
ErrCASetLimitReached = "reached ca set limit"
ErrNoActiveCertDeletions = "no active ca set deletion"
ErrCertValidationFailure = "certificates validation failed"
ErrUnknownQueryParameters = "the query parameter is not allowed"
ErrJSONSchemaValidation = "JSON schema is not valid"
ErrAnotherActivationJustCompletedIinTheCASet = (
    "another activation request in progress in the ca set"
)
ErrPathVariableQueryParamTypeMismatch = (
    "path variable query parameter type mismatch"
)
ErrUnauthorized = "unauthorized request"
ErrInternalError = "internal error"
ErrForbidden = "forbidden request"
ErrCASetInUseByEnrollments = "ca set bound to slot in CPS"
ErrCASetInUseByHostnamesAndNotEnrollments = (
    "ca set linked to hostnames and not to enrollments"
)
ErrCASetInUseByBothEnrollmentsAndHostnames = (
    "ca set is linked to both enrollments and hostnames"
)
ErrFindAssociationsFailedForEnrollmentsWithHostnamesLinked = (
    "ca set is linked to hostnames and could be "
    "linked to enrollments"
)
ErrFindAssociationsFailed = "ca set could be linked to hostnames"
ErrCASetCannotBeDeletedActiveVersions = (
    "ca set cannot be deleted due to active versions"
)
ErrFindAssociationsFailedForHostnamesWithEnrollmentsLinked = (
    "ca set is linked to enrollments and could be "
    "linked to hostnames"
)
ErrFetchAssociationsFailedForHostnames = (
    "fetch complete association details for hostnames "
    "is not possible"
)
ErrFetchAssociationsFailedForEnrollments = (
    "fetch complete association details for enrollments "
    "is not possible"
)
ErrFetchAssociationsFailed = (
    "fetch complete association details is not possible"
)
ErrFindAssociationsFailedForEnrollmentsWithEmptyHostnames = (
    "ca set could be linked to hostnames"
)
ErrFindAssociationsFailedForHostnamesEnrollmentsNotLinked = (
    "ca set is not linked to enrollments and could be "
    "linked to hostnames"
)
ErrMediaTypeNotSupported = "media type is not supported"
ErrMediaTypeNotAcceptable = "media type is not acceptable"
ErrInvalidJSON = "invalid json"
ErrInvalidField = "invalid field"
ErrMissingRequiredQueryParameter = "missing required query parameter"
ErrCASetNameValidationFailure = "ca set name validation failure"


# ---------------------------------------------------------------------------
# Operation sentinel errors from ca_set.go (lines 391-408).
# ---------------------------------------------------------------------------

ErrCreateCASet = "create ca set failed"
ErrGetCASet = "get ca set failed"
ErrListCASets = "list ca sets failed"
ErrDeleteCASet = "delete ca set failed"
ErrListCASetAssociations = "list ca sets associations failed"
ErrCloneCASet = "clone ca set failed"
ErrGetCASetDeletionStatus = "list ca set deletion status failed"
ErrListCASetActivities = "get ca set activities failed"
ErrValidateCertificates = "validate certificates failed"


# ---------------------------------------------------------------------------
# Operation sentinel errors from ca_set_versions.go (lines 258-271).
# ---------------------------------------------------------------------------

ErrCreateCASetVersion = "creating a CA set version"
ErrCloneCASetVersion = "cloning a CA set version"
ErrGetCASetVersion = "fetching a CA set version"
ErrListCASetVersions = "fetching CA set versions"
ErrGetCASetVersionCertificates = (
    "fetching certificates for a CA set version"
)
ErrUpdateCASetVersion = "updating a CA set version"


# ---------------------------------------------------------------------------
# Operation sentinel errors from ca_set_activation.go (lines 148-158).
# ---------------------------------------------------------------------------

ErrActivateCASetVersion = "activate ca set version failed"
ErrDeactivateCASetVersion = "deactivate ca set version failed"
ErrGetCASetVersionActivation = (
    "get ca set version activation failed"
)
ErrListCASetVersionActivations = (
    "list ca set version activations failed"
)
ErrListCASetActivations = "list ca set activations failed"


# ---------------------------------------------------------------------------
# Matcher table for Error.is_equivalent().
# Mirrors Go errors.go Is() method (lines 316-368).
# Each tuple: (sentinel_error, http_status, error_type_uri).
# ---------------------------------------------------------------------------

_ERROR_MATCHERS: list[tuple[str, int, str]] = [
    (ErrGetCASetNotFound, 404,
     _CA_SET_NOT_FOUND_TYPE),
    (ErrGetCASetVersionNotFound, 404,
     _CA_SET_VERSION_NOT_FOUND_TYPE),
    (ErrGetCASetActivationNotFound, 404,
     _CA_SET_ACTIVATION_NOT_FOUND_TYPE),
    (ErrDeleteCASetNotFound, 404,
     _CA_SET_NOT_FOUND_TYPE),
    (ErrDeleteActivationDeactivationInProgress, 409,
     _ACTIVATION_DEACTIVATION_IN_PROGRESS),
    (ErrCASetDeleteRequestInProgress, 409,
     _CA_SET_DELETE_REQUEST_IN_PROGRESS),
    (ErrCASetVersionIsActive, 422,
     _CA_SET_VERSION_IS_ACTIVE),
    (ErrCASetVersionIsActiveOnNetwork, 409,
     _CA_SET_VERSION_IS_ACTIVE_ON_NETWORK),
    (ErrCASetVersionIsActiveOnNetworkCannotBeActivated, 409,
     _CA_SET_VERSION_IS_ACTIVE_ON_NETWORK),
    (ErrCASetVersionWasPreviouslyActive, 422,
     _CA_SET_VERSION_WAS_PREVIOUSLY_ACTIVE),
    (ErrCertificateValidationFailedForCreate, 400,
     _CERTIFICATE_VALIDATION_FAILED_FOR_CREATE),
    (ErrCertificateValidationFailedForUpdate, 400,
     _CERTIFICATE_VALIDATION_FAILED_FOR_UPDATE),
    (ErrCertificateValidationFailedForActivation, 400,
     _CERTIFICATE_VALIDATION_FAILED_FOR_ACTIVATION),
    (ErrCertificateLimitReached, 422,
     _CERTIFICATE_LIMIT_REACHED),
    (ErrCASetVersionLimitReached, 422,
     _CA_SET_VERSION_LIMIT_REACHED),
    (ErrCASetVersionIsDuplicate, 422,
     _CA_SET_VERSION_DUPLICATE),
    (ErrCASetInUseByEnrollments, 409,
     _CA_SET_IN_USE_BY_ENROLLMENTS),
    (ErrCASetInUseByHostnamesAndNotEnrollments, 409,
     _CA_SET_IN_USE_BY_HOSTNAMES_AND_NOT_ENROLLMENTS),
    (ErrCASetBoundToHostname, 409,
     _CA_SET_BOUND_TO_HOSTNAME),
    (ErrCASetInUseByHostnames, 409,
     _CA_SET_IN_USE_BY_HOSTNAMES),
    (ErrCASetInUseByBothEnrollmentsAndHostnames, 409,
     _CA_SET_IN_USE_BY_BOTH_ENROLLMENTS_AND_HOSTNAMES),
    (ErrAnotherActivationInProgress, 409,
     _ANOTHER_ACTIVATION_IN_PROGRESS),
    (ErrAnotherDeactivationInProgress, 409,
     _ANOTHER_DEACTIVATION_IN_PROGRESS),
    (ErrCASetVersionNotActiveOnNetwork, 409,
     _CA_SET_VERSION_NOT_ACTIVE_ON_NETWORK),
    (ErrCASetVersionNotActiveOnNetworkCannotBeDeactivated, 409,
     _CA_SET_VERSION_NOT_ACTIVE_ON_NETWORK),
    (ErrFetchAssociationsTimeout, 504,
     _FETCH_ASSOCIATIONS_TIMEOUT),
    (ErrMissingCASetVersion, 400,
     _MISSING_CA_CERT_VERSION),
    (ErrCASetNameNotUnique, 409,
     _CA_SET_NAME_NOT_UNIQUE),
    (ErrCASetLimitReached, 422,
     _CA_SET_LIMIT_REACHED),
    (ErrNoActiveCertDeletions, 400,
     _NO_ACTIVE_CERT_DELETIONS),
    (ErrCertValidationFailure, 400,
     _CERT_VALIDATION_FAILURE),
    (ErrUnknownQueryParameters, 400,
     _UNKNOWN_QUERY_PARAMETERS),
    (ErrJSONSchemaValidation, 409,
     _JSON_SCHEMA_VALIDATION),
    (ErrAnotherActivationJustCompletedIinTheCASet, 400,
     _ANOTHER_ACTIVATION_JUST_COMPLETED),
    (ErrPathVariableQueryParamTypeMismatch, 400,
     _PATH_VARIABLE_QUERY_PARAM_TYPE_MISMATCH),
    (ErrUnauthorized, 401,
     _UNAUTHORIZED),
    (ErrInternalError, 500,
     _INTERNAL_ERROR),
    (ErrForbidden, 403,
     _FORBIDDEN),
    (ErrFindAssociationsFailedForEnrollmentsWithHostnamesLinked,
     500,
     _FIND_ASSOCIATIONS_FAILED_FOR_ENROLLMENTS_WITH_HOSTNAMES_LINKED),
    (ErrFindAssociationsFailed, 500,
     _FIND_ASSOCIATIONS_FAILED),
    (ErrCASetCannotBeDeletedActiveVersions, 400,
     _CA_SET_CANNOT_BE_DELETED_ACTIVE_VERSIONS),
    (ErrFindAssociationsFailedForHostnamesWithEnrollmentsLinked,
     500,
     _FIND_ASSOCIATIONS_FAILED_FOR_HOSTNAMES_WITH_ENROLLMENTS_LINKED),
    (ErrFetchAssociationsFailedForHostnames, 500,
     _FETCH_ASSOCIATIONS_FAILED_FOR_HOSTNAMES),
    (ErrFetchAssociationsFailedForEnrollments, 500,
     _FETCH_ASSOCIATIONS_FAILED_FOR_ENROLLMENTS),
    (ErrFetchAssociationsFailed, 500,
     _FETCH_ASSOCIATIONS_FAILED),
    (ErrFindAssociationsFailedForEnrollmentsWithEmptyHostnames,
     500,
     _FIND_ASSOCIATIONS_FAILED_FOR_ENROLLMENTS_WITH_EMPTY_HOSTNAMES),
    (ErrFindAssociationsFailedForHostnamesEnrollmentsNotLinked,
     500,
     _FIND_ASSOCIATIONS_FAILED_FOR_HOSTNAMES_ENROLLMENTS_NOT_LINKED),
    (ErrMediaTypeNotSupported, 415,
     _MEDIA_TYPE_NOT_SUPPORTED),
    (ErrMediaTypeNotAcceptable, 406,
     _MEDIA_TYPE_NOT_ACCEPTABLE),
    (ErrInvalidJSON, 400,
     _INVALID_JSON),
    (ErrInvalidField, 400,
     _INVALID_FIELD),
    (ErrMissingRequiredQueryParameter, 400,
     _MISSING_REQUIRED_QUERY_PARAMETER),
    (ErrCASetNameValidationFailure, 400,
     _CA_SET_NAME_VALIDATION_FAILURE),
]
