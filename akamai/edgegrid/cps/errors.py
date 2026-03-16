# pylint: disable=invalid-name
"""CPS service sentinel errors and error response handling."""

import json
import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# Title constant used in enrollment-not-found detection
# Mirrors Go enrollmentNotFoundTitle from errors.go line 11
ENROLLMENT_NOT_FOUND_TITLE = "Not Found"

# Acknowledgement parameter constants
# From changes.go lines 88-93
ACKNOWLEDGEMENT_ACKNOWLEDGE = "acknowledge"
ACKNOWLEDGEMENT_DENY = "deny"

# ---------------------------------------------------------------------------
# Sentinel error constants (string values EXACTLY match Go errors.New(...))
# ---------------------------------------------------------------------------

# From cps.go line 13
ErrStructValidation = "struct validation"

# From errors.go line 14
ErrEnrollmentNotFound = "enrollment not found"

# From location_url.go line 12
ErrInvalidLocation = "location URL is invalid"

# From changes.go lines 143-146
ErrGetChangeStatus = "fetching change"
ErrCancelChange = "canceling change"

# From deployments.go lines 83-88
ErrListDeployments = "list deployments"
ErrGetProductionDeployment = "get production deployment"
ErrGetStagingDeployment = "get staging deployment"

# From deployment_schedules.go lines 56-59
ErrGetDeploymentSchedule = "get deployment schedule"
ErrUpdateDeploymentSchedule = "update deployment schedule"

# From dv_challenges.go lines 56-59
ErrGetChangeLetsEncryptChallenges = "fetching change for lets-encrypt-challenges"
ErrAcknowledgeLetsEncryptChallenges = "acknowledging lets-encrypt-challenges"

# From enrollments.go lines 304-313
ErrListEnrollments = "fetching enrollments"
ErrGetEnrollment = "fetching enrollment"
ErrCreateEnrollment = "create enrollment"
ErrUpdateEnrollment = "update enrollment"
ErrRemoveEnrollment = "remove enrollment"

# From history.go lines 117-122
ErrGetDVHistory = "get dv history"
ErrGetCertificateHistory = "get certificate history"
ErrGetChangeHistory = "get change history"

# From change_management_info.go lines 66-71
ErrGetChangeManagementInfo = "get change management info"
ErrGetChangeDeploymentInfo = "get change deployment info"
ErrAcknowledgeChangeManagement = "acknowledging change management"

# From post_verification_warnings.go lines 20-23
ErrGetChangePostVerificationWarnings = "get post-verification-warnings"
ErrAcknowledgePostVerificationWarnings = "acknowledging post-verification-warnings"

# From pre_verification_warnings.go lines 21-24
ErrGetChangePreVerificationWarnings = "fetching pre-verification-warnings"
ErrAcknowledgePreVerificationWarnings = "acknowledging pre-verification-warnings"

# From third_party_csr.go lines 72-75
ErrGetChangeThirdPartyCSR = "get change third-party csr"
ErrUploadThirdPartyCertAndTrustChain = "upload third-party cert and trust chain"


# ---------------------------------------------------------------------------
# CPS-specific error class
# ---------------------------------------------------------------------------


@dataclass
class CPSError(Exception):
    """CPS API error response.

    Parses CPS-specific RFC 7807 error responses.
    Mirrors Go pkg/cps.Error struct from errors.go.
    """

    # pylint: disable=too-many-instance-attributes,redefined-builtin
    type: str = ""
    title: str = ""
    detail: str = ""
    instance: str = ""
    behavior_name: str = ""
    error_location: str = ""
    status_code: int = 0
    errors: Any = None
    warnings: Any = None

    def __str__(self) -> str:
        """Format error as indented JSON.

        Mirrors Go Error.Error() method from errors.go lines 57-63.
        Uses json.MarshalIndent equivalent with tab indentation.
        Only includes fields with non-zero/non-empty/non-None values,
        matching Go's ``omitempty`` JSON tag behavior.
        """
        error_dict: dict[str, Any] = {}
        if self.type:
            error_dict["type"] = self.type
        if self.title:
            error_dict["title"] = self.title
        if self.detail:
            error_dict["detail"] = self.detail
        if self.instance:
            error_dict["instance"] = self.instance
        if self.behavior_name:
            error_dict["behaviorName"] = self.behavior_name
        if self.error_location:
            error_dict["errorLocation"] = self.error_location
        if self.status_code:
            error_dict["statusCode"] = self.status_code
        if self.errors is not None:
            error_dict["errors"] = self.errors
        if self.warnings is not None:
            error_dict["warnings"] = self.warnings
        try:
            msg = json.dumps(error_dict, indent="\t")
            return f"API error: \n{msg}"
        except (TypeError, ValueError) as err:
            return f"error marshaling API error: {err}"

    def is_equivalent(self, target) -> bool:
        """Check error equivalence.

        Mirrors Go Error.Is() method from errors.go lines 66-84.

        Special case: if *target* is the ``ErrEnrollmentNotFound`` sentinel
        string, checks that ``status_code == 404`` and
        ``title == "Not Found"``.

        For CPSError targets, compares by status_code first, then by
        string representation.

        Args:
            target: Either a sentinel error string or another CPSError.

        Returns:
            True when this error is equivalent to *target*.
        """
        if isinstance(target, str) and target == ErrEnrollmentNotFound:
            return (
                self.status_code == 404
                and self.title == ENROLLMENT_NOT_FOUND_TITLE
            )

        if not isinstance(target, CPSError):
            return False
        if self is target:
            return True
        if self.status_code != target.status_code:
            return False
        return str(self) == str(target)


# ---------------------------------------------------------------------------
# Error response parser
# ---------------------------------------------------------------------------


def parse_cps_error(response) -> CPSError:
    """Parse a CPS API error from an HTTP response.

    Reads the response body and attempts JSON parsing.  Falls back to raw
    text when the body is not valid JSON.  Always sets ``status_code``
    from the HTTP response status.

    Mirrors Go ``(c *cps) Error(r *http.Response)`` from errors.go
    lines 32-55.

    Args:
        response: A ``requests.Response`` object (or compatible).

    Returns:
        A populated ``CPSError`` instance.
    """
    error = CPSError()

    try:
        body = response.text
    except Exception as err:  # pylint: disable=broad-exception-caught
        logger.error("reading error response body: %s", err)
        error.status_code = response.status_code
        error.title = "Failed to read error body"
        error.detail = str(err)
        return error

    try:
        data = json.loads(body)
        error.type = data.get("type", "")
        error.title = data.get("title", "")
        error.detail = data.get("detail", "")
        error.instance = data.get("instance", "")
        error.behavior_name = data.get("behaviorName", "")
        error.error_location = data.get("errorLocation", "")
        error.status_code = data.get("statusCode", 0)
        error.errors = data.get("errors")
        error.warnings = data.get("warnings")
    except (json.JSONDecodeError, AttributeError) as err:
        logger.error("could not unmarshal API error: %s", err)
        error.title = (
            "Failed to unmarshal error body. CPS API failed. "
            "Check details for more information."
        )
        error.detail = body

    error.status_code = response.status_code
    return error
