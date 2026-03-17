"""Sentinel errors and error types for the Cloud Certificates API client.

Ported from Go ``pkg/cloudcertificates/errors.go`` (179 lines).  Defines the
service-specific :class:`Error` class (both a dataclass and an ``Exception``),
nested validation data structures used in 409 Conflict and 400 Bad Request
responses, sentinel error constants for all operations, and the
:func:`new_error` factory function for parsing HTTP error responses.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

from akamai.edgegrid.utils import unescape_content
from akamai.edgegrid.cloudcertificates.models import Subject

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sentinel error constants — operation errors  (errors.go lines 14-24)
# ---------------------------------------------------------------------------

ErrStructValidation: str = "struct validation"  # pylint: disable=invalid-name
ErrPatchCertificate: str = "patching certificate"  # pylint: disable=invalid-name
ErrUpdateCertificate: str = "updating certificate"  # pylint: disable=invalid-name
ErrListCertificates: str = "listing certificates"  # pylint: disable=invalid-name
ErrCreateCertificate: str = "creating certificate"  # pylint: disable=invalid-name
ErrGetCertificate: str = "getting certificate"  # pylint: disable=invalid-name
ErrDeleteCertificate: str = "deleting certificate"  # pylint: disable=invalid-name
ErrListCertificateBindings: str = "listing certificate bindings"  # pylint: disable=invalid-name
ErrListBindings: str = "listing bindings"  # pylint: disable=invalid-name


# ---------------------------------------------------------------------------
# Nested helper dataclasses  (defined before Error to satisfy type references)
# ---------------------------------------------------------------------------

@dataclass
class ValidationDetail:
    """Detailed message from a certificate validation check.

    Mirrors Go ``ValidationDetail`` struct (errors.go lines 117-125).
    All fields use Go JSON tags for serialisation.

    Attributes:
        detail:   Human-readable description of the issue.
        instance: URI reference identifying the specific occurrence.
        message:  Short message describing the validation problem.
        name:     Name of the field or resource that failed validation.
        status:   Optional HTTP-style status code for this detail entry.
                  ``None`` when not present (Go ``*int``).
        title:    Short summary title of the validation detail.
        type:     URI reference identifying the problem type.
    """

    detail: str = ""
    instance: str = ""
    message: str = ""
    name: str = ""
    status: int | None = None
    title: str = ""
    type: str = ""  # pylint: disable=redefined-builtin

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict, omitting empty/None fields."""

        result: dict = {}
        if self.detail:
            result["detail"] = self.detail
        if self.instance:
            result["instance"] = self.instance
        if self.message:
            result["message"] = self.message
        if self.name:
            result["name"] = self.name
        if self.status is not None:
            result["status"] = self.status
        if self.title:
            result["title"] = self.title
        if self.type:
            result["type"] = self.type
        return result

    @classmethod
    def from_dict(cls, data: dict | None) -> ValidationDetail | None:
        """Deserialise from a camelCase dict.

        Returns ``None`` when *data* is falsy.
        """

        if not data:
            return None
        return cls(
            detail=data.get("detail", ""),
            instance=data.get("instance", ""),
            message=data.get("message", ""),
            name=data.get("name", ""),
            status=data.get("status"),
            title=data.get("title", ""),
            type=data.get("type", ""),
        )


@dataclass
class ValidationResult:
    """Container for validation results (errors, notices, warnings).

    Mirrors Go ``ValidationResult`` struct (errors.go lines 110-114).

    Attributes:
        errors:   List of error-level validation details.
        notices:  List of informational validation details.
        warnings: List of warning-level validation details.
    """

    errors: list[ValidationDetail] = field(default_factory=list)
    notices: list[ValidationDetail] = field(default_factory=list)
    warnings: list[ValidationDetail] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict, omitting empty lists."""

        result: dict = {}
        if self.errors:
            result["errors"] = [e.to_dict() for e in self.errors]
        if self.notices:
            result["notices"] = [n.to_dict() for n in self.notices]
        if self.warnings:
            result["warnings"] = [w.to_dict() for w in self.warnings]
        return result

    @classmethod
    def from_dict(cls, data: dict | None) -> ValidationResult | None:
        """Deserialise from a camelCase dict.

        Returns ``None`` when *data* is falsy.
        """

        if not data:
            return None
        return cls(
            errors=[
                e for e in (
                    ValidationDetail.from_dict(item) for item in data.get("errors", [])
                ) if e is not None
            ],
            notices=[
                n for n in (
                    ValidationDetail.from_dict(item) for item in data.get("notices", [])
                ) if n is not None
            ],
            warnings=[
                w for w in (
                    ValidationDetail.from_dict(item) for item in data.get("warnings", [])
                ) if w is not None
            ],
        )


@dataclass
class PEMValidation:  # pylint: disable=too-many-instance-attributes
    """PEM certificate with validation details.

    Mirrors Go ``PEMValidation`` struct (errors.go lines 94-107).

    Attributes:
        certificate_pem:     Raw PEM-encoded certificate text.
        created_by:          User / principal that created the certificate.
        created_date:        ISO-8601 creation timestamp.
        display_name:        Human-readable certificate name.
        end_date:            ISO-8601 expiry timestamp.
        fingerprint:         Certificate fingerprint hash.
        issuer:              Certificate issuer (CN / O).
        serial_number:       Certificate serial number.
        signature_algorithm: Signature algorithm used.
        start_date:          ISO-8601 validity start timestamp.
        subject:             Certificate subject information.
        validation:          Validation result for this certificate.
    """

    certificate_pem: str = ""
    created_by: str | None = None
    created_date: str | None = None
    display_name: str | None = None
    end_date: str | None = None
    fingerprint: str | None = None
    issuer: str | None = None
    serial_number: str | None = None
    signature_algorithm: str | None = None
    start_date: str | None = None
    subject: Subject | None = None
    validation: ValidationResult | None = None

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict.

        ``certificatePem`` is always included; optional fields are included
        only when non-``None``.
        """

        result: dict = {"certificatePem": self.certificate_pem}
        if self.created_by is not None:
            result["createdBy"] = self.created_by
        if self.created_date is not None:
            result["createdDate"] = self.created_date
        if self.display_name is not None:
            result["displayName"] = self.display_name
        if self.end_date is not None:
            result["endDate"] = self.end_date
        if self.fingerprint is not None:
            result["fingerprint"] = self.fingerprint
        if self.issuer is not None:
            result["issuer"] = self.issuer
        if self.serial_number is not None:
            result["serialNumber"] = self.serial_number
        if self.signature_algorithm is not None:
            result["signatureAlgorithm"] = self.signature_algorithm
        if self.start_date is not None:
            result["startDate"] = self.start_date
        if self.subject is not None:
            result["subject"] = self.subject.to_dict()
        if self.validation is not None:
            result["validation"] = self.validation.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict | None) -> PEMValidation | None:
        """Deserialise from a camelCase dict.

        Returns ``None`` when *data* is falsy.
        """

        if not data:
            return None
        subject_data = data.get("subject")
        subject_obj: Subject | None = None
        if subject_data and isinstance(subject_data, dict):
            subject_obj = Subject.from_dict(subject_data)
        return cls(
            certificate_pem=data.get("certificatePem", ""),
            created_by=data.get("createdBy"),
            created_date=data.get("createdDate"),
            display_name=data.get("displayName"),
            end_date=data.get("endDate"),
            fingerprint=data.get("fingerprint"),
            issuer=data.get("issuer"),
            serial_number=data.get("serialNumber"),
            signature_algorithm=data.get("signatureAlgorithm"),
            start_date=data.get("startDate"),
            subject=subject_obj,
            validation=ValidationResult.from_dict(data.get("validation")),
        )


@dataclass
class ValidationData:
    """Certificate and trust-chain validation details.

    Mirrors Go ``ValidationData`` struct (errors.go lines 85-91).

    Attributes:
        signed_certificate_pem: PEM text of the signed leaf certificate.
        signed_certificates:    Per-certificate validation entries.
        trust_chain:            Per-certificate validation for the trust chain.
        trust_chain_pem:        PEM text of the entire trust chain.
        validation:             Overall validation result.
    """

    signed_certificate_pem: str = ""
    signed_certificates: list[PEMValidation] = field(default_factory=list)
    trust_chain: list[PEMValidation] = field(default_factory=list)
    trust_chain_pem: str | None = None
    validation: ValidationResult | None = None

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict, omitting empty/None fields."""

        result: dict = {}
        if self.signed_certificate_pem:
            result["signedCertificatePem"] = self.signed_certificate_pem
        if self.signed_certificates:
            result["signedCertificates"] = [
                sc.to_dict() for sc in self.signed_certificates
            ]
        if self.trust_chain:
            result["trustChain"] = [tc.to_dict() for tc in self.trust_chain]
        if self.trust_chain_pem is not None:
            result["trustChainPem"] = self.trust_chain_pem
        if self.validation is not None:
            result["validation"] = self.validation.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict | None) -> ValidationData | None:
        """Deserialise from a camelCase dict.

        Returns ``None`` when *data* is falsy.
        """

        if not data:
            return None
        return cls(
            signed_certificate_pem=data.get("signedCertificatePem", ""),
            signed_certificates=[
                sc for sc in (
                    PEMValidation.from_dict(item)
                    for item in data.get("signedCertificates", [])
                ) if sc is not None
            ],
            trust_chain=[
                tc for tc in (
                    PEMValidation.from_dict(item)
                    for item in data.get("trustChain", [])
                ) if tc is not None
            ],
            trust_chain_pem=data.get("trustChainPem"),
            validation=ValidationResult.from_dict(data.get("validation")),
        )


@dataclass
class SecondaryError:
    """Detailed error within a validation-failure response.

    Mirrors Go ``SecondaryError`` struct (errors.go lines 73-82).
    Note that ``invalid_parameter_value`` is a *list* of strings (Go
    ``[]string``), unlike the single-string field on :class:`Error`.

    Attributes:
        type:                    URI problem type.
        title:                   Short summary.
        detail:                  Human-readable explanation.
        instance:                Occurrence URI.
        explanation:             Extended human-readable explanation.
        invalid_parameter_value: List of invalid values for the parameter.
        parameter_name:          Name of the invalid parameter.
    """

    type: str = ""  # pylint: disable=redefined-builtin
    title: str = ""
    detail: str = ""
    instance: str = ""
    explanation: str = ""
    invalid_parameter_value: list[str] = field(default_factory=list)
    parameter_name: str = ""

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict, omitting empty fields."""

        result: dict = {}
        if self.type:
            result["type"] = self.type
        if self.title:
            result["title"] = self.title
        if self.detail:
            result["detail"] = self.detail
        if self.instance:
            result["instance"] = self.instance
        if self.explanation:
            result["explanation"] = self.explanation
        if self.invalid_parameter_value:
            result["invalidParameterValue"] = list(self.invalid_parameter_value)
        if self.parameter_name:
            result["parameterName"] = self.parameter_name
        return result

    @classmethod
    def from_dict(cls, data: dict | None) -> SecondaryError | None:
        """Deserialise from a camelCase dict.

        Returns ``None`` when *data* is falsy.
        """

        if not data:
            return None
        raw_ipv = data.get("invalidParameterValue")
        return cls(
            type=data.get("type", ""),
            title=data.get("title", ""),
            detail=data.get("detail", ""),
            instance=data.get("instance", ""),
            explanation=data.get("explanation", ""),
            invalid_parameter_value=list(raw_ipv) if raw_ipv else [],
            parameter_name=data.get("parameterName", ""),
        )


@dataclass
class Error(Exception):  # pylint: disable=too-many-instance-attributes
    """Cloud Certificates service-specific API error.

    Both a dataclass and an ``Exception`` so that it can be raised.
    Mirrors Go ``Error`` struct (errors.go lines 56-70).

    Fields without ``omitempty`` in Go (type, title, status, detail, instance)
    are always serialised; the rest are included only when non-empty / non-None.

    Attributes:
        type:                       URI problem type (RFC 7807).
        title:                      Short human-readable summary.
        status:                     HTTP status code returned by the API.
        detail:                     Human-readable explanation.
        instance:                   URI identifying the specific occurrence.
        certificate_identifier:     Name of the identifier used in the request.
        certificate_identifier_value: Value of the identifier used in the request.
        data:                       Validation data attached to 409 Conflict responses.
        explanation:                Extended explanation.
        errors:                     List of secondary validation errors.
        invalid_parameter_value:    Single invalid value string.
        parameter_name:             Parameter whose value was invalid.
    """

    type: str = ""  # pylint: disable=redefined-builtin
    title: str = ""
    status: int = 0
    detail: str = ""
    instance: str = ""
    certificate_identifier: str = ""
    certificate_identifier_value: str = ""
    data: ValidationData | None = None
    explanation: str = ""
    errors: list[SecondaryError] = field(default_factory=list)
    invalid_parameter_value: str = ""
    parameter_name: str = ""

    # -- string representation -----------------------------------------------

    def __str__(self) -> str:
        """Return JSON representation matching Go ``Error()`` method.

        Format::

            API error:
            {<tab-indented JSON>}

        Only base fields (type, title, status, detail, instance) are always
        present; optional fields are included when non-empty (``omitempty``).
        """

        try:
            return f"API error: \n{json.dumps(self.to_dict(), indent='\t')}"
        except (TypeError, ValueError) as exc:
            return f"error marshaling API error: {exc} "

    # -- wildcard comparison --------------------------------------------------

    def is_equivalent(self, target: Error) -> bool:
        """Wildcard error comparison matching Go ``Is()`` method.

        Only compares *type*, *title*, and *status*.  An empty string (or zero
        for status) on *target* means "don't check this field" (wildcard).

        Mirrors Go errors.go lines 162-178.

        Args:
            target: Error instance to compare against.

        Returns:
            ``True`` when every non-wildcard field on *target* matches *self*.
        """

        if not isinstance(target, Error):
            return False

        ignore_type = target.type == ""
        ignore_status = target.status == 0
        ignore_title = target.title == ""
        match_type = target.type == self.type
        match_status = target.status == self.status
        match_title = target.title == self.title

        return (
            (match_type or ignore_type)
            and (match_status or ignore_status)
            and (match_title or ignore_title)
        )

    # -- HTTP response parsing ------------------------------------------------

    @classmethod
    def from_response(cls, response) -> Error:
        """Parse an HTTP error response into an :class:`Error`.

        Mirrors Go ``cloudcertificates.Error(r *http.Response)`` method
        (errors.go lines 128-149).

        1. Read the response body text.
        2. Attempt JSON deserialisation into an ``Error``.
        3. On failure, store the (HTML-unescaped) raw body as ``detail``.
        4. Always set ``status`` from the HTTP response status code.

        Args:
            response: A ``requests.Response`` (or compatible) object exposing
                ``status_code`` (int) and ``text`` (str) attributes.

        Returns:
            Fully populated :class:`Error`.
        """

        try:
            body = response.text
        except Exception:  # pylint: disable=broad-exception-caught
            logger.error("reading error response body: %s", response)
            return cls(
                status=getattr(response, "status_code", 0),
                title="Failed to read error body",
                detail=str(response),
            )

        err = cls()
        try:
            data = json.loads(body)
            if isinstance(data, dict):
                err = cls.from_dict(data)
            else:
                raise TypeError("response body is not a JSON object")
        except (json.JSONDecodeError, TypeError):
            logger.error("could not unmarshal API error: %s", body)
            err.title = (
                "Failed to unmarshal error body. CCM API failed. "
                "Check details for more information."
            )
            err.detail = unescape_content(body)

        err.status = getattr(response, "status_code", 0)
        return err

    # -- serialisation --------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialise to a camelCase dict matching Go JSON output.

        Base fields (type, title, status, detail, instance) are always
        included.  Optional fields are included only when non-empty
        (``omitempty`` semantics).
        """

        result: dict = {
            "type": self.type,
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
            "instance": self.instance,
        }
        if self.certificate_identifier:
            result["certificateIdentifier"] = self.certificate_identifier
        if self.certificate_identifier_value:
            result["certificateIdentifierValue"] = (
                self.certificate_identifier_value
            )
        if self.data is not None:
            result["data"] = self.data.to_dict()
        if self.explanation:
            result["explanation"] = self.explanation
        if self.errors:
            result["errors"] = [e.to_dict() for e in self.errors]
        if self.invalid_parameter_value:
            result["invalidParameterValue"] = self.invalid_parameter_value
        if self.parameter_name:
            result["parameterName"] = self.parameter_name
        return result

    @classmethod
    def from_dict(cls, data: dict | None) -> Error:
        """Deserialise from a camelCase dict.

        Returns a default :class:`Error` when *data* is falsy.
        """

        if not data:
            return cls()

        parsed_errors: list[SecondaryError] = []
        for item in data.get("errors") or []:
            secondary = SecondaryError.from_dict(item)
            if secondary is not None:
                parsed_errors.append(secondary)

        return cls(
            type=data.get("type", ""),
            title=data.get("title", ""),
            status=data.get("status", 0),
            detail=data.get("detail", ""),
            instance=data.get("instance", ""),
            certificate_identifier=data.get("certificateIdentifier", ""),
            certificate_identifier_value=data.get(
                "certificateIdentifierValue", ""
            ),
            data=ValidationData.from_dict(data.get("data")),
            explanation=data.get("explanation", ""),
            errors=parsed_errors,
            invalid_parameter_value=data.get("invalidParameterValue", ""),
            parameter_name=data.get("parameterName", ""),
        )


# ---------------------------------------------------------------------------
# Domain sentinel errors — Error instances  (errors.go lines 43-52)
# These use ``is_equivalent()`` wildcard matching:  only ``type`` is set,
# so comparison ignores title, status, and all other fields.
# ---------------------------------------------------------------------------

ErrCertificateNameInUse: Error = Error(  # pylint: disable=invalid-name
    type="/error-types/certificate-name-already-in-use",
)
ErrCertificateNotFound: Error = Error(  # pylint: disable=invalid-name
    type="/error-types/certificate-not-found",
)
ErrCertificateResourceNotFound: Error = Error(  # pylint: disable=invalid-name
    type="/error-types/certificate-resource-not-found",
)


# ---------------------------------------------------------------------------
# Factory function
# ---------------------------------------------------------------------------

def new_error(status_code: int, body: dict | str) -> Error:
    """Parse a pre-read HTTP response body into a Cloud Certificates Error.

    Mirrors the response-parsing logic of Go
    ``cloudcertificates.Error(r *http.Response)`` but operates on an
    already-read body (either a parsed *dict* or a raw *str*).

    Args:
        status_code: HTTP response status code.
        body:        Response body — a parsed JSON dict or a raw string.

    Returns:
        Fully populated :class:`Error` with *status* set.
    """

    if isinstance(body, dict):
        err = Error.from_dict(body)
        err.status = status_code
        return err

    err = Error()
    try:
        data = json.loads(body)
        if isinstance(data, dict):
            err = Error.from_dict(data)
        else:
            raise TypeError("response body is not a JSON object")
    except (json.JSONDecodeError, TypeError):
        logger.error("could not unmarshal API error: %s", body)
        err.title = (
            "Failed to unmarshal error body. CCM API failed. "
            "Check details for more information."
        )
        err.detail = unescape_content(str(body))

    err.status = status_code
    return err
