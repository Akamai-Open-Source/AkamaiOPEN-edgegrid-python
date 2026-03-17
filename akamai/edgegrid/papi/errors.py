"""Error types and sentinel errors for the PAPI client.

Defines the PAPI-specific Error class (extends base Error with additional fields),
ActivationError, ActivationErrorMessage, and all sentinel error constants mirroring
Go v12 pkg/papi error definitions.
"""

import json
from dataclasses import dataclass, field

from akamai.edgegrid.errors import Error as BaseError


# ---------------------------------------------------------------------------
# PAPI-specific Error class — mirrors Go papi.Error (errors.go lines 13-30)
# ---------------------------------------------------------------------------

@dataclass
class Error(BaseError):  # pylint: disable=too-many-instance-attributes
    """PAPI-specific API error with additional fields.

    Extends base Error with PAPI-specific fields: behavior_name,
    error_location, warnings, limit info, and redirect/activation links.

    Mirrors Go papi.Error struct from errors.go.
    """

    behavior_name: str = ""
    error_location: str = ""
    warnings: dict | list | str | None = None
    limit_key: str = ""
    limit: int | None = None
    remaining: int | None = None
    redirect_link: str | None = None
    activation_link: str | None = None

    def __str__(self) -> str:  # pylint: disable=too-many-branches
        """Format error as indented JSON, matching Go Error.Error().

        Produces output in the form 'API error: \\n{json}' where json uses
        tab indentation and Go camelCase field names. Fields with omitempty
        in the Go struct are omitted when they hold zero values.
        """
        error_dict: dict = {}
        # type — no omitempty, always included
        error_dict["type"] = self.type  # pylint: disable=no-member
        # title — omitempty
        if self.title:
            error_dict["title"] = self.title
        # detail — no omitempty, always included
        error_dict["detail"] = self.detail
        # instance — omitempty
        if self.instance:
            error_dict["instance"] = self.instance
        # behaviorName — omitempty
        if self.behavior_name:
            error_dict["behaviorName"] = self.behavior_name
        # errorLocation — omitempty
        if self.error_location:
            error_dict["errorLocation"] = self.error_location
        # statusCode — omitempty
        if self.status_code:
            error_dict["statusCode"] = self.status_code
        # errors — omitempty (json.RawMessage, nil → omit)
        if self.errors is not None:
            error_dict["errors"] = self.errors
        # warnings — omitempty (json.RawMessage, nil → omit)
        if self.warnings is not None:
            error_dict["warnings"] = self.warnings
        # limitKey — omitempty
        if self.limit_key:
            error_dict["limitKey"] = self.limit_key
        # limit — omitempty (*int, nil → omit)
        if self.limit is not None:
            error_dict["limit"] = self.limit
        # remaining — omitempty (*int, nil → omit)
        if self.remaining is not None:
            error_dict["remaining"] = self.remaining
        # redirectLink — omitempty (*string, nil → omit)
        if self.redirect_link is not None:
            error_dict["redirectLink"] = self.redirect_link
        # activationLink — omitempty (*string, nil → omit)
        if self.activation_link is not None:
            error_dict["activationLink"] = self.activation_link

        try:
            msg = json.dumps(error_dict, indent="\t")
            return f"API error: \n{msg}"
        except (TypeError, ValueError) as err:
            return f"error marshaling API error: {err}"

    def is_equivalent(self, other) -> bool:  # pylint: disable=too-many-return-statements
        """Check error equivalence with PAPI-specific sentinel support.

        Mirrors Go Error.Is() from errors.go lines 94-125.  When the other
        value is one of the five special sentinel error strings, the
        corresponding private checker is invoked.  Otherwise, falls back to
        status code and string comparison.
        """
        if isinstance(other, str):
            if other == ErrSBDNotEnabled:
                return self._is_err_sbd_not_enabled()
            if other == ErrDefaultCertLimitReached:
                return self._is_err_default_cert_limit_reached()
            if other == ErrNotFound:
                return self._is_err_not_found()
            if other == ErrActivationTooFar:
                return self._is_activation_too_far()
            if other == ErrActivationAlreadyActive:
                return self._is_activation_already_active()
            return False

        if isinstance(other, Error):
            if self is other:
                return True
            if self.status_code != other.status_code:
                return False
            return str(self) == str(other)

        return False

    # -- private sentinel checkers mirroring Go helpers (errors.go 149-167) --

    def _is_err_sbd_not_enabled(self) -> bool:
        """StatusCode 403 + specific PAPI type URL. Mirrors Go isErrSBDNotEnabled."""
        return (
            self.status_code == 403
            and self.type  # pylint: disable=no-member
            == "https://problems.luna.akamaiapis.net/papi/v0/"
            "property-version-hostname/"
            "default-cert-provisioning-unavailable"
        )

    def _is_err_default_cert_limit_reached(self) -> bool:
        """StatusCode 429, DEFAULT_CERTS_PER_CONTRACT key, remaining==0.

        Mirrors Go isErrDefaultCertLimitReached.
        """
        return (
            self.status_code == 429
            and self.limit_key == "DEFAULT_CERTS_PER_CONTRACT"
            and self.remaining is not None
            and self.remaining == 0
        )

    def _is_err_not_found(self) -> bool:
        """StatusCode 404. Mirrors Go isErrNotFound."""
        return self.status_code == 404

    def _is_activation_too_far(self) -> bool:
        """StatusCode 400, title/detail match. Mirrors Go isActivationTooFar."""
        return (
            self.status_code == 400
            and self.title == "Error canceling Activation"
            and self.detail == "cancellation_failed.error.activation.toofar"
        )

    def _is_activation_already_active(self) -> bool:
        """StatusCode 422, title match. Mirrors Go isActivationAlreadyActive."""
        return (
            self.status_code == 422
            and self.title == "Activation Unprocessable"
        )


# ---------------------------------------------------------------------------
# ActivationErrorMessage — mirrors Go papi.ActivationErrorMessage (lines 44-48)
# ---------------------------------------------------------------------------

@dataclass
class ActivationErrorMessage:
    """Detailed activation error message.

    Mirrors Go papi.ActivationErrorMessage struct from errors.go.
    """

    type: str = ""  # pylint: disable=redefined-builtin
    title: str = ""
    detail: str = ""


# ---------------------------------------------------------------------------
# ActivationError — mirrors Go papi.ActivationError (errors.go lines 33-41)
# ---------------------------------------------------------------------------

@dataclass
class ActivationError(Exception):
    """Activation validation error returned in include activation responses.

    Mirrors Go papi.ActivationError struct from errors.go.
    """

    type: str = ""  # pylint: disable=redefined-builtin
    title: str = ""
    instance: str = ""
    status: int = 0
    errors: list[ActivationErrorMessage] = field(default_factory=list)
    message_id: str = ""
    result: str = ""

    def __str__(self) -> str:
        """Format error as indented JSON, matching Go ActivationError.Error()."""
        error_dict: dict = {}
        # type — no omitempty, always included
        error_dict["type"] = self.type
        # title — omitempty
        if self.title:
            error_dict["title"] = self.title
        # instance — omitempty
        if self.instance:
            error_dict["instance"] = self.instance
        # status — omitempty
        if self.status:
            error_dict["status"] = self.status
        # errors — no omitempty, always included
        errors_list: list = []
        for err_msg in self.errors:
            if isinstance(err_msg, ActivationErrorMessage):
                msg_dict: dict = {"type": err_msg.type}
                if err_msg.title:
                    msg_dict["title"] = err_msg.title
                if err_msg.detail:
                    msg_dict["detail"] = err_msg.detail
                errors_list.append(msg_dict)
            else:
                errors_list.append(err_msg)
        error_dict["errors"] = errors_list
        # messageId — omitempty
        if self.message_id:
            error_dict["messageId"] = self.message_id
        # result — omitempty
        if self.result:
            error_dict["result"] = self.result

        try:
            msg = json.dumps(error_dict, indent="\t")
            return f"API error: \n{msg}"
        except (TypeError, ValueError) as err:
            return f"error marshaling API error: {err}"

    def is_equivalent(self, other) -> bool:
        """Check error equivalence with ActivationError-specific sentinel support.

        Mirrors Go ActivationError.Is() from errors.go lines 128-147.
        """
        if isinstance(other, str):
            if other == ErrMissingComplianceRecord:
                return self._is_missing_compliance_record()
            return False

        if isinstance(other, ActivationError):
            if self is other:
                return True
            if self.status != other.status:
                return False
            return str(self) == str(other)

        return False

    def _is_missing_compliance_record(self) -> bool:
        """Check if MessageID equals 'missing_compliance_record'.

        Mirrors Go isMissingComplianceRecord from errors.go.
        """
        return self.message_id == "missing_compliance_record"


# ---------------------------------------------------------------------------
# Sentinel error constants — string values matching Go errors.New() exactly.
# Names preserve Go PascalCase convention for cross-SDK consistency.
# ---------------------------------------------------------------------------
# pylint: disable=invalid-name

# Core sentinels (from papi.go)
ErrStructValidation = "struct validation"
ErrNotFound = "resource not found"
ErrSBDNotEnabled = "secure-by-default is not enabled"
ErrDefaultCertLimitReached = (
    "the limit for DEFAULT certificates has been reached"
)
ErrMissingComplianceRecord = "compliance record must be specified"
ErrActivationTooFar = "error activation is too far"
ErrActivationAlreadyActive = (
    "error canceling activation, as activation is not pending"
)

# Activation sentinels (from activation.go)
ErrCreateActivation = "creating activation"
ErrGetActivations = "fetching activations"
ErrGetActivation = "fetching activation"
ErrCancelActivation = "canceling activation"

# Active property hostname sentinels (from active_property_hostname.go)
ErrListActivePropertyHostnames = "fetching active property hostnames"
ErrGetActivePropertyHostnamesDiff = "fetching active property hostnames diff"
ErrListActiveAccountHostnames = "fetching active account hostnames"

# Client settings sentinels (from clientsettings.go)
ErrGetClientSettings = "fetching client settings"
ErrUpdateClientSettings = "updating client settings"

# Contract sentinels (from contract.go)
ErrGetContracts = "fetching contracts"

# CP code sentinels (from cpcode.go)
ErrGetCPCodes = "fetching CP Codes"
ErrGetCPCode = "fetching CP Code"
ErrGetCPCodeDetail = "fetching CP Code Detail"
ErrCreateCPCode = "creating CP Code"
ErrUpdateCPCode = "updating CP Code"

# Domain ownership validation sentinels (from domain_ownership_validation.go)
ErrValidateDomainsOwnership = "validating domains ownership"

# Edge hostname sentinels (from edgehostname.go)
ErrGetEdgeHostnames = "fetching edge hostnames"
ErrGetEdgeHostname = "fetching edge hostname"
ErrCreateEdgeHostname = "creating edge hostname"

# Group sentinels (from group.go)
ErrGetGroups = "fetching groups"

# Include sentinels (from include.go)
ErrListIncludes = "list Includes"
ErrListIncludeParents = "list Include Parents"
ErrGetInclude = "get an Include"
ErrCreateInclude = "create an Include"
ErrDeleteInclude = "delete an Include"

# Include activation sentinels (from include_activations.go)
ErrActivateInclude = "activate include"
ErrDeactivateInclude = "deactivate include"
ErrCancelIncludeActivation = "cancel include activation"
ErrGetIncludeActivation = "get include activation"
ErrListIncludeActivations = "list include activations"

# Include rule sentinels (from include_rule.go)
ErrGetIncludeRuleTree = "fetching include rule tree"
ErrUpdateIncludeRuleTree = "updating include rule tree"

# Include version sentinels (from include_versions.go)
ErrCreateIncludeVersion = "create an include version"
ErrGetIncludeVersion = "get an include version"
ErrListIncludeVersions = "list include versions"
ErrListIncludeVersionAvailableCriteria = (
    "list include version available criteria"
)
ErrListIncludeVersionAvailableBehaviors = (
    "list include version available behaviors"
)

# Product sentinels (from products.go)
ErrGetProducts = "fetching products"

# Property sentinels (from property.go)
ErrGetProperties = "fetching properties"
ErrGetProperty = "fetching property"
ErrCreateProperty = "creating property"
ErrRemoveProperty = "removing property"
ErrMapPropertyIDToName = "map property by ID"
ErrMapPropertyNameToID = "map property by name"
ErrNoProperty = "no such property"

# Property hostname activation sentinels (from property_hostname_activation.go)
ErrGetPropertyHostnameActivation = "fetching hostname activation"
ErrListPropertyHostnameActivations = "fetching hostname activations"
ErrCancelPropertyHostnameActivation = "canceling hostname activation"
ErrCancelPropertyHostnameActivationAlreadyAborted = (
    "activation already aborted"
)

# Property hostname bucket sentinels (from property_hostname_bucket.go)
ErrPatchPropertyHostnameBucket = "patching property hostname bucket"

# Property version hostname sentinels (from propertyhostname.go)
ErrGetPropertyVersionHostnames = "fetching hostnames"
ErrUpdatePropertyVersionHostnames = "updating hostnames"
ErrPatchPropertyVersionHostnames = "patching hostnames"
ErrGetAuditHistory = "getting audit history"

# Property version sentinels (from propertyversion.go)
ErrGetPropertyVersions = "fetching property versions"
ErrGetPropertyVersion = "fetching property version"
ErrGetLatestVersion = "fetching latest property version"
ErrCreatePropertyVersion = "creating property version"
ErrGetAvailableBehaviors = "fetching available behaviors"
ErrGetAvailableCriteria = "fetching available criteria"
ErrListAvailableIncludes = "fetching available includes"
ErrListReferencedIncludes = "fetching referenced includes"

# Response link sentinels (from response_link.go)
ErrInvalidResponseLink = "response link URL is invalid"

# Rule sentinels (from rule.go)
ErrGetRuleTree = "fetching rule tree"
ErrUpdateRuleTree = "updating rule tree"

# Rule format sentinels (from ruleformats.go)
ErrGetRuleFormats = "fetching rule formats"

# Search sentinels (from search.go)
ErrSearchProperties = "searching for properties"
