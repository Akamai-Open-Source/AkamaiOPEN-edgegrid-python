# pylint: disable=redefined-builtin
"""DNS-specific error types and sentinel error constants for Edge DNS API.

Provides the DNS ``Error`` dataclass, a DNS error response parser, and all
sentinel error constants for the Akamai Edge DNS API client.  The DNS Error
struct has DIFFERENT fields from the base ``Error`` — it includes
``behavior_name`` and ``error_location`` instead of a generic ``errors``
list.

Mirrors Go ``pkg/dns/errors.go`` for the Error struct and the ``Error()``
response parser, plus all sentinel error variables defined across every Go
DNS source file.
"""

import json
import logging
from dataclasses import dataclass

from akamai.edgegrid.utils import unescape_content

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DNS Error dataclass
# ---------------------------------------------------------------------------


@dataclass
class Error(Exception):
    """DNS API error matching Go ``pkg/dns.Error`` struct.

    Fields map 1:1 with Go JSON tags.  ``status_code`` is populated from
    the HTTP response status code, **not** from the JSON body.

    Go reference::

        type Error struct {
            Type          string `json:"type"`
            Title         string `json:"title"`
            Detail        string `json:"detail"`
            Instance      string `json:"instance,omitempty"`
            BehaviorName  string `json:"behaviorName,omitempty"`
            ErrorLocation string `json:"errorLocation,omitempty"`
            StatusCode    int    `json:"-"`
        }
    """

    type: str = ""
    title: str = ""
    detail: str = ""
    instance: str = ""
    behavior_name: str = ""
    error_location: str = ""
    status_code: int = 0

    def __str__(self) -> str:
        """Format the error as ``Title: ...; Type: ...; Detail: ...``.

        Mirrors Go ``Error.Error()`` at ``errors.go:57-59``::

            fmt.Sprintf("Title: %s; Type: %s; Detail: %s",
                        e.Title, e.Type, e.Detail)
        """
        return f"Title: {self.title}; Type: {self.type}; Detail: {self.detail}"

    def is_equivalent(self, other: "Error") -> bool:
        """Check if this error is equivalent to another ``Error``.

        Mirrors Go ``Error.Is()`` at ``errors.go:62-77``.  Compares by
        ``status_code`` first, then by the string representation.

        Args:
            other: The ``Error`` instance to compare against.

        Returns:
            True if the errors are considered equivalent.
        """
        if not isinstance(other, Error):
            return False
        if self is other:
            return True
        if self.status_code != other.status_code:
            return False
        return str(self) == str(other)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Error):
            return NotImplemented
        return self.is_equivalent(other)

    def __hash__(self) -> int:
        return hash((self.status_code, str(self)))


# ---------------------------------------------------------------------------
# DNS error response parser
# ---------------------------------------------------------------------------


def parse_dns_error_response(response) -> Error:
    """Parse a DNS API error from an HTTP response.

    Reads the response body, attempts JSON parsing, and falls back to raw
    text with HTML unescaping on parse failure.

    Mirrors Go ``dns.Error()`` method at ``errors.go:32-55``.

    Args:
        response: A ``requests.Response`` object.

    Returns:
        An ``Error`` instance populated from the response.
    """
    error = Error()

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
    except (json.JSONDecodeError, AttributeError) as err:
        logger.error("could not unmarshal API error: %s", err)
        error.title = (
            "Failed to unmarshal error body. DNS API failed. "
            "Check details for more information."
        )
        error.detail = unescape_content(body)

    error.status_code = response.status_code

    return error


# ---------------------------------------------------------------------------
# Sentinel error constants
#
# Each constant value matches the Go ``errors.New("...")`` message EXACTLY.
# Grouped by the Go source file in which they are declared.
# ---------------------------------------------------------------------------

# pylint: disable=invalid-name

# errors.go
ErrBadRequest: str = "missing argument"

# authorities.go
ErrGetAuthorities: str = "get authorities"
ErrGetNameServerRecordList: str = "get name server record list"

# data.go
ErrListGroups: str = "list groups"

# record.go
ErrCreateRecord: str = "create record"
ErrUpdateRecord: str = "update record"
ErrDeleteRecord: str = "delete record"

# record_lookup.go
ErrGetRecord: str = "get record"
ErrGetRecordList: str = "get record list"

# recordsets.go
ErrCreateRecordSets: str = "create record sets"
ErrGetRecordSets: str = "get record sets"
ErrUpdateRecordSets: str = "update record sets"

# tsig.go
ErrGetTSIGKey: str = "get tsig key"
ErrDeleteTSIGKey: str = "delete tsig key"
ErrGetTSIGKeyAliases: str = "get tsig key aliases"
ErrUpdateTSIGKey: str = "updated tsig key"
ErrUpdateTSIGKeyBulk: str = "update tsig key for multiple zones"
ErrGetTSIGKeyZones: str = "list zones using tsig key"
ErrListTSIGKeys: str = "get a list of the tsig keys"

# zone.go
ErrGetZone: str = "get zone"
ErrGetChangeList: str = "get change list"
ErrGetMasterZoneFile: str = "get master zone file"
ErrPostMasterZoneFile: str = "post master zone file"
ErrCreateZone: str = "create zone"
ErrSaveChangeList: str = "save change list"
ErrSubmitChangeList: str = "submit change list"
ErrGetZoneNames: str = "get zone names"
ErrGetZoneNameTypes: str = "get zone name types"

# zonebulk.go
ErrGetBulkZoneCreateStatus: str = "get bulk zone create status"
ErrGetBulkZoneDeleteStatus: str = "get bulk zone delete status"
ErrGetBulkZoneCreateResult: str = "get bulk zone create result"
ErrGetBulkZoneDeleteResult: str = "get bulk zone delete result"
ErrCreateBulkZones: str = "create bulk zones"
ErrDeleteBulkZones: str = "delete bulk zones"
