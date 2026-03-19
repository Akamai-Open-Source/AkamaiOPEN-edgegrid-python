"""GTM API sentinel error constants and Error class.

Defines all error constants and the GTM-specific Error class used throughout
the GTM client. Mirrors Go pkg/gtm/errors.go Error struct with JSON parsing,
Error() and Is() methods, and module-level sentinel errors from errors.go,
domain.go, property.go, datacenter.go, resource.go, asmap.go, geomap.go,
and cidrmap.go.
"""

import json
import logging
from dataclasses import dataclass

from akamai.edgegrid.utils import unescape_content

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sentinel error constants from errors.go
# ---------------------------------------------------------------------------
# Constant names follow Go naming conventions (ErrXxx) for cross-language
# parity with the Go v12 SDK. These are the exact names used in Go.
# pylint: disable=invalid-name

# ErrNotFound is used when status code is 404 Not Found.
ErrNotFound = "404 Not Found"

# ErrNoDatacenterAssignedToMap occurs when no datacenter is assigned to
# the map target during the creation of a geographic property.
ErrNoDatacenterAssignedToMap = (
    "no datacenter is assigned to map target (all others)"
)

# ErrDomainNotFound occurs when the domain is not found.
ErrDomainNotFound = "domain not found"

# ---------------------------------------------------------------------------
# Sentinel error constants from domain.go
# ---------------------------------------------------------------------------

# ErrGetDomainStatus is returned when GetDomainStatus fails.
ErrGetDomainStatus = "get domain status"

# ErrGetDomain is returned when GetDomain fails.
ErrGetDomain = "get domain"

# ErrCreateDomain is returned when CreateDomain fails.
ErrCreateDomain = "create domain"

# ErrUpdateDomain is returned when UpdateDomain fails.
ErrUpdateDomain = "update domain"

# ErrDeleteDomain is returned when DeleteDomain fails.
# Deprecated: may be removed in future versions.
ErrDeleteDomain = "delete domain"

# ErrDeleteDomains is returned when DeleteDomains fails.
ErrDeleteDomains = "delete domains"

# ErrGetDeleteDomainsStatus is returned when GetDeleteDomainsStatus fails.
ErrGetDeleteDomainsStatus = "get delete domains status"

# ---------------------------------------------------------------------------
# Sentinel error constants from property.go
# ---------------------------------------------------------------------------

# ErrGetProperty is returned when GetProperty fails.
ErrGetProperty = "get property"

# ErrListProperties is returned when ListProperties fails.
ErrListProperties = "list properties"

# ErrCreateProperty is returned when CreateProperty fails.
ErrCreateProperty = "create Property"

# ErrUpdateProperty is returned when UpdateProperty fails.
ErrUpdateProperty = "update Property"

# ErrDeleteProperty is returned when DeleteProperty fails.
ErrDeleteProperty = "delete Property"

# ---------------------------------------------------------------------------
# Sentinel error constants from datacenter.go
# ---------------------------------------------------------------------------

# ErrListDatacenters is returned when ListDatacenters fails.
ErrListDatacenters = "list datacenters"

# ErrGetDatacenter is returned when GetDatacenter fails.
ErrGetDatacenter = "get datacenter"

# ErrCreateDatacenter is returned when CreateDatacenter fails.
ErrCreateDatacenter = "create datacenter"

# ErrUpdateDatacenter is returned when UpdateDatacenter fails.
ErrUpdateDatacenter = "update datacenter"

# ErrDeleteDatacenter is returned when DeleteDatacenter fails.
ErrDeleteDatacenter = "delete datacenter"

# ---------------------------------------------------------------------------
# Sentinel error constants from resource.go
# ---------------------------------------------------------------------------

# ErrListResources is returned when ListResources fails.
ErrListResources = "list resources"

# ErrGetResource is returned when GetResource fails.
ErrGetResource = "get resource"

# ErrCreateResource is returned when CreateResource fails.
ErrCreateResource = "create resource"

# ErrUpdateResource is returned when UpdateResource fails.
ErrUpdateResource = "update resource"

# ErrDeleteResource is returned when DeleteResource fails.
ErrDeleteResource = "delete resource"

# ---------------------------------------------------------------------------
# Sentinel error constants from asmap.go
# ---------------------------------------------------------------------------

# ErrListASMaps is returned when ListASMaps fails.
ErrListASMaps = "list asmaps"

# ErrGetASMap is returned when GetASMap fails.
ErrGetASMap = "get asmap"

# ErrCreateASMap is returned when CreateASMap fails.
ErrCreateASMap = "create asmap"

# ErrUpdateASMap is returned when UpdateASMap fails.
ErrUpdateASMap = "update asmap"

# ErrDeleteASMap is returned when DeleteASMap fails.
ErrDeleteASMap = "delete asmap"

# ---------------------------------------------------------------------------
# Sentinel error constants from geomap.go
# ---------------------------------------------------------------------------

# ErrListGeoMaps is returned when ListGeoMaps fails.
ErrListGeoMaps = "list geomaps"

# ErrGetGeoMap is returned when GetGeoMap fails.
ErrGetGeoMap = "get geomap"

# ErrCreateGeoMap is returned when CreateGeoMap fails.
ErrCreateGeoMap = "create geomap"

# ErrUpdateGeoMap is returned when UpdateGeoMap fails.
ErrUpdateGeoMap = "update geomap"

# ErrDeleteGeoMap is returned when DeleteGeoMap fails.
ErrDeleteGeoMap = "delete geomap"

# ---------------------------------------------------------------------------
# Sentinel error constants from cidrmap.go
# ---------------------------------------------------------------------------

# ErrListCIDRMaps is returned when ListCIDRMaps fails.
ErrListCIDRMaps = "list cidrmaps"

# ErrGetCIDRMap is returned when GetCIDRMap fails.
ErrGetCIDRMap = "get cidrmap"

# ErrCreateCIDRMap is returned when CreateCIDRMap fails.
ErrCreateCIDRMap = "create cidrmap"

# ErrUpdateCIDRMap is returned when UpdateCIDRMap fails.
ErrUpdateCIDRMap = "update cidrmap"

# ErrDeleteCIDRMap is returned when DeleteCIDRMap fails.
ErrDeleteCIDRMap = "delete cidrmap"

# pylint: enable=invalid-name


def _parse_nested_error(err_data):
    """Parse a nested error entry from JSON data.

    Handles recursive parsing of nested error objects within the errors
    list of a GTM API error response. Mirrors Go json.Unmarshal behavior
    for the []Error field.

    Args:
        err_data: A dict (from JSON) or other value representing an error.

    Returns:
        An Error instance if err_data is a dict, otherwise the original value.
    """
    if isinstance(err_data, dict):
        nested_errors_raw = err_data.get("errors")
        nested_errors = None
        if nested_errors_raw is not None:
            nested_errors = [
                _parse_nested_error(sub) for sub in nested_errors_raw
            ]
        return Error(
            type=err_data.get("type", ""),
            title=err_data.get("title", ""),
            detail=err_data.get("detail", ""),
            instance=err_data.get("instance", ""),
            behavior_name=err_data.get("behaviorName", ""),
            error_location=err_data.get("errorLocation", ""),
            errors=nested_errors,
        )
    return err_data


@dataclass
class Error(Exception):  # pylint: disable=too-many-instance-attributes
    """GTM API error response.

    Mirrors Go pkg/gtm/errors.go Error struct. Parses RFC 7807 problem
    detail responses from the GTM API with additional GTM-specific fields
    (behavior_name and error_location).

    Attributes:
        type: Error type URI (RFC 7807).
        title: Short human-readable error summary.
        detail: Detailed human-readable error description.
        instance: URI reference identifying the specific occurrence.
        behavior_name: GTM-specific behavior name (omitted when empty).
        error_location: GTM-specific error location (omitted when empty).
        status_code: HTTP response status code (not serialized to JSON).
        errors: Nested list of sub-errors, or None.
    """

    type: str = ""  # pylint: disable=redefined-builtin
    title: str = ""
    detail: str = ""
    instance: str = ""
    behavior_name: str = ""
    error_location: str = ""
    status_code: int = 0
    errors: list["Error"] | None = None

    def __str__(self) -> str:
        """Format error as indented JSON.

        Mirrors Go Error.Error() method which uses json.MarshalIndent
        with tab indentation and returns the format:
        ``API error: \\n<json>``.

        Returns:
            JSON-formatted error string prefixed with ``API error:``.
        """
        error_dict = self._to_json_dict()
        try:
            msg = json.dumps(error_dict, indent="\t")
            return f"API error: \n{msg}"
        except (TypeError, ValueError) as err:
            return f"error marshaling API error: {err}"

    def _to_json_dict(self) -> dict:
        """Convert to JSON-serializable dict matching Go JSON tags.

        Implements the same serialization behavior as Go's json.Marshal:

        - ``type``, ``title``, ``detail``: always included (no omitempty).
        - ``instance``, ``behaviorName``, ``errorLocation``: omitted when
          empty (omitempty).
        - ``StatusCode``: never included (``json:"-"``).
        - ``errors``: always included (``null`` when None).

        Returns:
            Dictionary suitable for ``json.dumps`` serialization.
        """
        result: dict = {
            "type": self.type,
            "title": self.title,
            "detail": self.detail,
        }
        if self.instance:
            result["instance"] = self.instance
        if self.behavior_name:
            result["behaviorName"] = self.behavior_name
        if self.error_location:
            result["errorLocation"] = self.error_location
        if self.errors is not None:
            result["errors"] = [
                e._to_json_dict()  # pylint: disable=protected-access
                if isinstance(e, Error) else e
                for e in self.errors
            ]
        else:
            result["errors"] = None
        return result

    def is_equivalent(self, target) -> bool:
        """Check error equivalence.

        Mirrors Go Error.Is() method (errors.go lines 74-102).
        Handles special sentinel error patterns (ErrNotFound,
        ErrNoDatacenterAssignedToMap, ErrDomainNotFound) and general
        Error-to-Error comparison.

        Args:
            target: A sentinel error string constant or another Error
                instance to compare against.

        Returns:
            True if this error is equivalent to the target.
        """
        # Check sentinel: ErrNotFound -> status 404
        if target == ErrNotFound:
            return self.status_code == 404

        # Check sentinel: ErrNoDatacenterAssignedToMap
        if target == ErrNoDatacenterAssignedToMap:
            return (
                "no datacenter is assigned to map target (all others)"
                in self.detail
            )

        # Check sentinel: ErrDomainNotFound -> status 400 + detail match
        if target == ErrDomainNotFound:
            return (
                self.status_code == 400
                and "domains could not be found" in self.detail
            )

        # General Error comparison
        if not isinstance(target, Error):
            return False

        return (
            self is target
            or (
                self.status_code == target.status_code
                and str(self) == str(target)
            )
        )

    @classmethod
    def from_response(cls, response) -> "Error":
        """Parse GTM API error from HTTP response.

        Mirrors Go gtm.Error() method (errors.go lines 40-63).

        Flow:
            1. Read response body text.
            2. Try JSON unmarshal into Error fields.
            3. On unmarshal failure: set title to failure message and
               detail to ``unescape_content(body)``.
            4. Always set status_code from response.

        Args:
            response: HTTP response object (requests.Response).

        Returns:
            Populated Error instance with parsed error details.
        """
        error = cls()

        # Step 1: Read body
        try:
            body = response.text
        except Exception as err:  # pylint: disable=broad-exception-caught
            logger.error("reading error response body: %s", err)
            error.status_code = response.status_code
            error.title = "Failed to read error body"
            error.detail = str(err)
            return error

        # Step 2: Try JSON unmarshal
        try:
            data = json.loads(body)
            error.type = data.get("type", "")
            error.title = data.get("title", "")
            error.detail = data.get("detail", "")
            error.instance = data.get("instance", "")
            error.behavior_name = data.get("behaviorName", "")
            error.error_location = data.get("errorLocation", "")
            raw_errors = data.get("errors")
            if raw_errors is not None:
                error.errors = [
                    _parse_nested_error(err_item)
                    for err_item in raw_errors
                ]
            else:
                error.errors = None
        except (json.JSONDecodeError, AttributeError) as err:
            # Step 3: Unmarshal failure - set title and unescape body
            logger.error("could not unmarshal API error: %s", err)
            error.title = (
                "Failed to unmarshal error body. GTM API failed. "
                "Check details for more information."
            )
            error.detail = unescape_content(body)

        # Step 4: Always set status code
        error.status_code = response.status_code

        return error
