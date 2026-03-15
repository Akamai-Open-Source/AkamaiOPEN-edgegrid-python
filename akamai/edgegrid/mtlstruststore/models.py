"""Request and response model classes for the mTLS Trust Store API."""
# pylint: disable=too-many-instance-attributes,redefined-builtin

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Type aliases mirroring Go type definitions
# ---------------------------------------------------------------------------
Network = str
AssociationType = str
CertificateStatus = str
VersionStatus = str
ActivationNetwork = str

# ---------------------------------------------------------------------------
# Network constants (from ca_set.go)
# ---------------------------------------------------------------------------
NETWORK_INACTIVE: str = "INACTIVE"
NETWORK_STAGING: str = "STAGING"
NETWORK_PRODUCTION: str = "PRODUCTION"
NETWORK_STAGING_AND_PRODUCTION: str = "STAGING+PRODUCTION"
NETWORK_PRODUCTION_AND_STAGING: str = "PRODUCTION+STAGING"
NETWORK_STAGING_OR_PRODUCTION: str = "STAGING,PRODUCTION"
NETWORK_PRODUCTION_OR_STAGING: str = "PRODUCTION,STAGING"

# CA Set Name validation constants (from ca_set.go)
CA_SET_NAME_PATTERN: str = r'^[%.a-zA-Z0-9_-]+$'
CA_SET_NAME_DESCRIPTION: str = (
    "allowed characters are alphanumerics (a-z, A-Z, 0-9), "
    "underscore (_), hyphen (-), percent (%) and period (.)"
)

# Deletion status constants (from ca_set.go)
DELETION_STATUS_IN_PROGRESS: str = "IN_PROGRESS"
DELETION_STATUS_COMPLETE: str = "COMPLETE"
DELETION_STATUS_FAILED: str = "FAILED"

# CA Set status constants (from ca_set.go)
CA_SET_STATUS_NOT_DELETED: str = "NOT_DELETED"
CA_SET_STATUS_DELETED: str = "DELETED"
CA_SET_STATUS_DELETING: str = "DELETING"

# Association type constants (from ca_set.go)
ASSOCIATION_TYPE_ENROLLMENTS: str = "enrollments"
ASSOCIATION_TYPE_PROPERTIES: str = "properties"

# ActivationNetwork constants (from ca_set_activation.go)
ACTIVATION_NETWORK_STAGING: str = "STAGING"
ACTIVATION_NETWORK_PRODUCTION: str = "PRODUCTION"

# CertificateStatus constants (from ca_set_versions.go)
EXPIRING_CERT: str = "EXPIRING"
EXPIRED_CERT: str = "EXPIRED"
EXPIRED_OR_EXPIRING_CERT: str = "EXPIRING,EXPIRED"
EXPIRING_OR_EXPIRED_CERT: str = "EXPIRED,EXPIRING"
ACTIVE_CERT: str = "ACTIVE"
ACTIVE_OR_EXPIRED_CERT: str = "ACTIVE,EXPIRED"
EXPIRED_OR_ACTIVE_CERT: str = "EXPIRED,ACTIVE"


# ---------------------------------------------------------------------------
# Certificate models (shared by versions and validation)
# ---------------------------------------------------------------------------
@dataclass
class CertificateRequest:
    """Certificate in a version creation/update request. Mirrors Go CertificateRequest."""

    certificate_pem: str = ""
    description: str | None = None

    def to_dict(self) -> dict:
        """Serialize to dict for JSON request body."""
        result: dict[str, object] = {"certificatePem": self.certificate_pem}
        if self.description is not None:
            result["description"] = self.description
        return result


@dataclass
class CertificateResponse:
    """Certificate details returned in CA set version responses. Mirrors Go CertificateResponse."""

    subject: str = ""
    issuer: str = ""
    end_date: str = ""
    start_date: str = ""
    fingerprint: str = ""
    certificate_pem: str = ""
    serial_number: str = ""
    signature_algorithm: str = ""
    created_date: str = ""
    created_by: str = ""
    description: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> CertificateResponse:
        """Create CertificateResponse from API response dict."""
        return cls(
            subject=data.get("subject", ""),
            issuer=data.get("issuer", ""),
            end_date=data.get("endDate", ""),
            start_date=data.get("startDate", ""),
            fingerprint=data.get("fingerprint", ""),
            certificate_pem=data.get("certificatePem", ""),
            serial_number=data.get("serialNumber", ""),
            signature_algorithm=data.get("signatureAlgorithm", ""),
            created_date=data.get("createdDate", ""),
            created_by=data.get("createdBy", ""),
            description=data.get("description"),
        )


@dataclass
class Warning:
    """Single validation warning. Mirrors Go Warning."""

    context_info: dict[str, Any] | None = None
    type: str = ""
    title: str = ""
    detail: str = ""
    pointer: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> Warning:
        """Create Warning from API response dict."""
        return cls(
            context_info=data.get("contextInfo"),
            type=data.get("type", ""),
            title=data.get("title", ""),
            detail=data.get("detail", ""),
            pointer=data.get("pointer", ""),
        )


@dataclass
class Validation:
    """Validation results for CA set version. Mirrors Go Validation."""

    warnings: list[Warning] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> Validation:
        """Create Validation from API response dict."""
        return cls(
            warnings=[
                Warning.from_dict(w) for w in data.get("warnings", [])
            ],
        )


# ---------------------------------------------------------------------------
# CA Set models (from ca_set.go)
# ---------------------------------------------------------------------------
@dataclass
class CreateCASetRequest:
    """Request body for CreateCASet. Mirrors Go CreateCASetRequest."""

    ca_set_name: str = ""
    description: str | None = None

    def to_dict(self) -> dict:
        """Serialize to dict for JSON request body."""
        result: dict[str, object] = {"caSetName": self.ca_set_name}
        if self.description is not None:
            result["description"] = self.description
        return result


@dataclass
class CASetResponse:
    """Response from CA set operations. Mirrors Go CASetResponse."""

    account_id: str = ""
    ca_set_id: str = ""
    ca_set_link: str = ""
    ca_set_name: str = ""
    ca_set_status: str = ""
    description: str | None = None
    latest_version_link: str | None = None
    latest_version: int | None = None
    staging_version_link: str | None = None
    staging_version: int | None = None
    production_version_link: str | None = None
    production_version: int | None = None
    versions_link: str = ""
    created_date: str = ""
    created_by: str = ""
    deleted_date: str | None = None
    deleted_by: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> CASetResponse:
        """Create CASetResponse from API response dict."""
        return cls(
            account_id=data.get("accountId", ""),
            ca_set_id=data.get("caSetId", ""),
            ca_set_link=data.get("caSetLink", ""),
            ca_set_name=data.get("caSetName", ""),
            ca_set_status=data.get("caSetStatus", ""),
            description=data.get("description"),
            latest_version_link=data.get("latestVersionLink"),
            latest_version=data.get("latestVersion"),
            staging_version_link=data.get("stagingVersionLink"),
            staging_version=data.get("stagingVersion"),
            production_version_link=data.get("productionVersionLink"),
            production_version=data.get("productionVersion"),
            versions_link=data.get("versionsLink", ""),
            created_date=data.get("createdDate", ""),
            created_by=data.get("createdBy", ""),
            deleted_date=data.get("deletedDate"),
            deleted_by=data.get("deletedBy"),
        )


# Type aliases for CA set responses (mirroring Go type aliases)
CreateCASetResponse = CASetResponse
GetCASetResponse = CASetResponse
CloneCASetResponse = CASetResponse


@dataclass
class ListCASetsRequest:
    """Request for ListCASets. Mirrors Go ListCASetsRequest."""

    ca_set_name_prefix: str = ""
    activated_on: str = ""


@dataclass
class ListCASetsResponse:
    """Response from ListCASets. Mirrors Go ListCASetsResponse."""

    ca_sets: list[CASetResponse] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> ListCASetsResponse:
        """Create ListCASetsResponse from API response dict."""
        return cls(
            ca_sets=[
                CASetResponse.from_dict(cs)
                for cs in data.get("caSets", [])
            ],
        )


@dataclass
class GetCASetRequest:
    """Request for GetCASet. Mirrors Go GetCASetRequest."""

    ca_set_id: str = ""


@dataclass
class DeleteCASetRequest:
    """Request for DeleteCASet. Mirrors Go DeleteCASetRequest."""

    ca_set_id: str = ""


@dataclass
class ListCASetAssociationsRequest:
    """Request for ListCASetAssociations. Mirrors Go ListCASetAssociationsRequest."""

    ca_set_id: str = ""
    association_type: str = ""


@dataclass
class AssociationHostname:
    """Hostname association data. Mirrors Go AssociationHostname."""

    hostname: str = ""
    network: str = ""
    status: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> AssociationHostname:
        """Create AssociationHostname from API response dict."""
        return cls(
            hostname=data.get("hostName", ""),
            network=data.get("network", ""),
            status=data.get("status", ""),
        )


@dataclass
class AssociationProperty:
    """Property association data. Mirrors Go AssociationProperty."""

    property_id: str = ""
    property_name: str | None = None
    property_link: str = ""
    asset_id: int | None = None
    group_id: int | None = None
    hostnames: list[AssociationHostname] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> AssociationProperty:
        """Create AssociationProperty from API response dict."""
        return cls(
            property_id=data.get("propertyId", ""),
            property_name=data.get("propertyName"),
            property_link=data.get("propertyLink", ""),
            asset_id=data.get("assetId"),
            group_id=data.get("groupId"),
            hostnames=[
                AssociationHostname.from_dict(h)
                for h in data.get("hostnames", [])
            ],
        )


@dataclass
class AssociationEnrollment:
    """Enrollment association data. Mirrors Go AssociationEnrollment."""

    enrollment_id: int = 0
    enrollment_link: str = ""
    staging_slots: list[int] = field(default_factory=list)
    production_slots: list[int] = field(default_factory=list)
    cn: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> AssociationEnrollment:
        """Create AssociationEnrollment from API response dict."""
        return cls(
            enrollment_id=data.get("enrollmentId", 0),
            enrollment_link=data.get("enrollmentLink", ""),
            staging_slots=data.get("stagingSlots", []),
            production_slots=data.get("productionSlots", []),
            cn=data.get("cn", ""),
        )


@dataclass
class Associations:
    """Container for property and enrollment associations. Mirrors Go Associations."""

    properties: list[AssociationProperty] = field(default_factory=list)
    enrollments: list[AssociationEnrollment] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> Associations:
        """Create Associations from API response dict."""
        return cls(
            properties=[
                AssociationProperty.from_dict(p)
                for p in data.get("properties", [])
            ],
            enrollments=[
                AssociationEnrollment.from_dict(e)
                for e in data.get("enrollments", [])
            ],
        )


@dataclass
class ListCASetAssociationsResponse:
    """Response from ListCASetAssociations. Mirrors Go ListCASetAssociationsResponse."""

    associations: Associations = field(default_factory=Associations)

    @classmethod
    def from_dict(cls, data: dict) -> ListCASetAssociationsResponse:
        """Create ListCASetAssociationsResponse from API response dict."""
        assoc_data = data.get("associations", {})
        return cls(
            associations=Associations.from_dict(assoc_data),
        )


@dataclass
class CloneCASetRequest:
    """Request for CloneCASet. Mirrors Go CloneCASetRequest."""

    clone_from_set_id: str = ""
    clone_from_version: int = 0
    new_ca_set_name: str = ""
    new_description: str | None = None

    def to_dict(self) -> dict:
        """Serialize to dict for JSON request body.

        Only caSetName and description are serialized (clone_from_set_id
        goes in the URL and clone_from_version in a query parameter).
        The description field does NOT use omitempty in Go, so it is
        always included (as null when None).
        """
        return {
            "caSetName": self.new_ca_set_name,
            "description": self.new_description,
        }


@dataclass
class GetCASetDeletionStatusRequest:
    """Request for GetCASetDeletionStatus. Mirrors Go GetCASetDeletionStatusRequest."""

    ca_set_id: str = ""


@dataclass
class CASetNetworkDeleteStatus:
    """Network-level CA set deletion status. Mirrors Go CASetNetworkDeleteStatus."""

    network: str = ""
    percent_complete: int = 0
    status: str = ""
    failure_reason: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> CASetNetworkDeleteStatus:
        """Create CASetNetworkDeleteStatus from API response dict."""
        return cls(
            network=data.get("network", ""),
            percent_complete=data.get("percentComplete", 0),
            status=data.get("status", ""),
            failure_reason=data.get("failureReason"),
        )


@dataclass
class GetCASetDeletionStatusResponse:
    """Response from GetCASetDeletionStatus. Mirrors Go GetCASetDeletionStatusResponse."""

    status: str = ""
    status_link: str = ""
    ca_set_link: str = ""
    resource_method: str | None = None
    ca_set_id: str = ""
    ca_set_name: str = ""
    estimated_end_time: str | None = None
    end_time: str | None = None
    failure_reason: str | None = None
    start_time: str = ""
    deletions: list[CASetNetworkDeleteStatus] = field(default_factory=list)
    retry_after: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> GetCASetDeletionStatusResponse:
        """Create GetCASetDeletionStatusResponse from API response dict."""
        return cls(
            status=data.get("status", ""),
            status_link=data.get("statusLink", ""),
            ca_set_link=data.get("caSetLink", ""),
            resource_method=data.get("resourceMethod"),
            ca_set_id=data.get("caSetId", ""),
            ca_set_name=data.get("caSetName", ""),
            estimated_end_time=data.get("estimatedEndTime"),
            end_time=data.get("endTime"),
            failure_reason=data.get("failureReason"),
            start_time=data.get("startTime", ""),
            deletions=[
                CASetNetworkDeleteStatus.from_dict(d)
                for d in data.get("deletions", [])
            ],
        )


@dataclass
class CASetActivity:
    """Single CA set activity entry. Mirrors Go CASetActivity."""

    type: str = ""
    network: str | None = None
    version: int | None = None
    activity_date: str = ""
    activity_by: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> CASetActivity:
        """Create CASetActivity from API response dict."""
        return cls(
            type=data.get("type", ""),
            network=data.get("network"),
            version=data.get("version"),
            activity_date=data.get("activityDate", ""),
            activity_by=data.get("activityBy", ""),
        )


@dataclass
class ListCASetActivitiesRequest:
    """Request for ListCASetActivities. Mirrors Go ListCASetActivitiesRequest."""

    ca_set_id: str = ""
    start: str = ""
    end: str = ""


@dataclass
class ListCASetActivitiesResponse:
    """Response from ListCASetActivities. Mirrors Go ListCASetActivitiesResponse."""

    ca_set_id: str = ""
    ca_set_link: str = ""
    ca_set_name: str = ""
    created_date: str = ""
    created_by: str = ""
    ca_set_status: str = ""
    deleted_date: str | None = None
    deleted_by: str | None = None
    activities: list[CASetActivity] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> ListCASetActivitiesResponse:
        """Create ListCASetActivitiesResponse from API response dict."""
        return cls(
            ca_set_id=data.get("caSetID", ""),
            ca_set_link=data.get("caSetLink", ""),
            ca_set_name=data.get("caSetName", ""),
            created_date=data.get("createdDate", ""),
            created_by=data.get("createdBy", ""),
            ca_set_status=data.get("caSetStatus", ""),
            deleted_date=data.get("deletedDate"),
            deleted_by=data.get("deletedBy"),
            activities=[
                CASetActivity.from_dict(a)
                for a in data.get("activities", [])
            ],
        )


# ---------------------------------------------------------------------------
# CA Set Version models (from ca_set_versions.go)
# ---------------------------------------------------------------------------
@dataclass
class CASetVersion:
    """Single CA set version. Mirrors Go CASetVersion."""

    ca_set_id: str = ""
    version: int = 0
    ca_set_name: str = ""
    version_link: str = ""
    description: str | None = None
    allow_insecure_sha1: bool = False
    staging_status: str = ""
    production_status: str = ""
    created_date: str = ""
    created_by: str = ""
    modified_date: str | None = None
    modified_by: str | None = None
    certificates: list[CertificateResponse] = field(default_factory=list)
    validation: Validation | None = None

    @classmethod
    def from_dict(cls, data: dict) -> CASetVersion:
        """Create CASetVersion from API response dict."""
        validation_data = data.get("validation")
        return cls(
            ca_set_id=data.get("caSetId", ""),
            version=data.get("version", 0),
            ca_set_name=data.get("caSetName", ""),
            version_link=data.get("versionLink", ""),
            description=data.get("description"),
            allow_insecure_sha1=data.get("allowInsecureSha1", False),
            staging_status=data.get("stagingStatus", ""),
            production_status=data.get("productionStatus", ""),
            created_date=data.get("createdDate", ""),
            created_by=data.get("createdBy", ""),
            modified_date=data.get("modifiedDate"),
            modified_by=data.get("modifiedBy"),
            certificates=[
                CertificateResponse.from_dict(c)
                for c in data.get("certificates", [])
            ],
            validation=(
                Validation.from_dict(validation_data)
                if validation_data is not None
                else None
            ),
        )


# Type aliases for CA set version responses (mirroring Go type aliases)
CreateCASetVersionResponse = CASetVersion
CloneCASetVersionResponse = CASetVersion
GetCASetVersionResponse = CASetVersion
UpdateCASetVersionResponse = CASetVersion


@dataclass
class CreateCASetVersionRequest:
    """Request for CreateCASetVersion. Mirrors Go CreateCASetVersionRequest."""

    ca_set_id: str = ""
    body: CreateCASetVersionRequestBody | None = None


@dataclass
class CreateCASetVersionRequestBody:
    """Body of CreateCASetVersion request. Mirrors Go CreateCASetVersionRequestBody."""

    allow_insecure_sha1: bool = False
    description: str | None = None
    certificates: list[CertificateRequest] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict for JSON request body."""
        result: dict[str, object] = {
            "allowInsecureSha1": self.allow_insecure_sha1,
        }
        if self.description is not None:
            result["description"] = self.description
        result["certificates"] = [
            cert.to_dict() for cert in self.certificates
        ]
        return result


@dataclass
class CloneCASetVersionRequest:
    """Request for CloneCASetVersion. Mirrors Go CloneCASetVersionRequest."""

    ca_set_id: str = ""
    version: int = 0


@dataclass
class ListCASetVersionsRequest:
    """Request for ListCASetVersions. Mirrors Go ListCASetVersionsRequest."""

    ca_set_id: str = ""
    include_certificates: bool = False
    active_versions_only: bool = False


@dataclass
class GetCASetVersionRequest:
    """Request for GetCASetVersion. Mirrors Go GetCASetVersionRequest."""

    ca_set_id: str = ""
    version: int = 0


@dataclass
class UpdateCASetVersionRequest:
    """Request for UpdateCASetVersion. Mirrors Go UpdateCASetVersionRequest."""

    ca_set_id: str = ""
    version: int = 0
    body: UpdateCASetVersionRequestBody | None = None


@dataclass
class UpdateCASetVersionRequestBody:
    """Body of UpdateCASetVersion request. Mirrors Go UpdateCASetVersionRequestBody."""

    description: str | None = None
    allow_insecure_sha1: bool = False
    certificates: list[CertificateRequest] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict for JSON request body."""
        result: dict[str, object] = {}
        if self.description is not None:
            result["description"] = self.description
        result["allowInsecureSha1"] = self.allow_insecure_sha1
        result["certificates"] = [
            cert.to_dict() for cert in self.certificates
        ]
        return result


@dataclass
class GetCASetVersionCertificatesRequest:
    """Request for GetCASetVersionCertificates.

    Mirrors Go GetCASetVersionCertificatesRequest.
    """

    ca_set_id: str = ""
    version: int = 0
    certificate_status: str | None = None
    expiry_threshold_in_days: int | None = None
    expiry_threshold_timestamp: str = ""


@dataclass
class ListCASetVersionsResponse:
    """Response from ListCASetVersions. Mirrors Go ListCASetVersionsResponse."""

    versions: list[CASetVersion] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> ListCASetVersionsResponse:
        """Create ListCASetVersionsResponse from API response dict."""
        return cls(
            versions=[
                CASetVersion.from_dict(v)
                for v in data.get("versions", [])
            ],
        )


@dataclass
class GetCASetVersionCertificatesResponse:
    """Response from GetCASetVersionCertificates.

    Mirrors Go GetCASetVersionCertificatesResponse.
    """

    ca_set_id: str = ""
    version: int = 0
    ca_set_name: str = ""
    certificates: list[CertificateResponse] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> GetCASetVersionCertificatesResponse:
        """Create GetCASetVersionCertificatesResponse from API response dict."""
        return cls(
            ca_set_id=data.get("caSetId", ""),
            version=data.get("version", 0),
            ca_set_name=data.get("caSetName", ""),
            certificates=[
                CertificateResponse.from_dict(c)
                for c in data.get("certificates", [])
            ],
        )


# ---------------------------------------------------------------------------
# Activation models (from ca_set_activation.go)
# ---------------------------------------------------------------------------


@dataclass
class ActivateCASetVersionRequest:
    """Request for ActivateCASetVersion.

    Mirrors Go ActivateCASetVersionRequest.
    ca_set_id and version go in the URL path (json:"-"),
    network is serialized in the JSON body.
    """

    ca_set_id: str = ""
    version: int = 0
    network: str = ""

    def to_dict(self) -> dict:
        """Serialize to dict for JSON request body (only network)."""
        return {"network": self.network}


# Go: type DeactivateCASetVersionRequest = ActivateCASetVersionRequest
DeactivateCASetVersionRequest = ActivateCASetVersionRequest


@dataclass
class ActivateCASetVersionResponse:
    """Response from ActivateCASetVersion.

    Mirrors Go ActivateCASetVersionResponse.
    """

    activation_id: int = 0
    activation_link: str = ""
    ca_set_id: str = ""
    ca_set_name: str = ""
    ca_set_link: str = ""
    created_by: str = ""
    created_date: str = ""
    failure_reason: str | None = None
    modified_by: str | None = None
    modified_date: str | None = None
    network: str = ""
    activation_status: str = ""
    activation_type: str = ""
    percent_complete: int = 0
    version: int = 0
    version_link: str = ""
    retry_after: str = ""
    validation: Validation | None = None

    @classmethod
    def from_dict(cls, data: dict) -> ActivateCASetVersionResponse:
        """Create ActivateCASetVersionResponse from API response dict."""
        raw_validation = data.get("validation")
        validation = (
            Validation.from_dict(raw_validation)
            if raw_validation is not None
            else None
        )
        return cls(
            activation_id=data.get("activationId", 0),
            activation_link=data.get("activationLink", ""),
            ca_set_id=data.get("caSetId", ""),
            ca_set_name=data.get("caSetName", ""),
            ca_set_link=data.get("caSetLink", ""),
            created_by=data.get("createdBy", ""),
            created_date=data.get("createdDate", ""),
            failure_reason=data.get("failureReason"),
            modified_by=data.get("modifiedBy"),
            modified_date=data.get("modifiedDate"),
            network=data.get("network", ""),
            activation_status=data.get("activationStatus", ""),
            activation_type=data.get("activationType", ""),
            percent_complete=data.get("percentComplete", 0),
            version=data.get("version", 0),
            version_link=data.get("versionLink", ""),
            retry_after=data.get("retryAfter", ""),
            validation=validation,
        )


# Go type aliases
DeactivateCASetVersionResponse = ActivateCASetVersionResponse
GetCASetVersionActivationResponse = ActivateCASetVersionResponse


@dataclass
class GetCASetVersionActivationRequest:
    """Request for GetCASetVersionActivation.

    Mirrors Go GetCASetVersionActivationRequest.
    """

    ca_set_id: str = ""
    version: int = 0
    activation_id: int = 0


@dataclass
class ListCASetVersionActivationsRequest:
    """Request for ListCASetVersionActivations.

    Mirrors Go ListCASetVersionActivationsRequest.
    """

    ca_set_id: str = ""
    version: int = 0


@dataclass
class ListCASetVersionActivationsResponse:
    """Response from ListCASetVersionActivations.

    Mirrors Go ListCASetVersionActivationsResponse.
    """

    activations: list[ActivateCASetVersionResponse] = field(
        default_factory=list
    )

    @classmethod
    def from_dict(cls, data: dict) -> ListCASetVersionActivationsResponse:
        """Create ListCASetVersionActivationsResponse from API response dict."""
        return cls(
            activations=[
                ActivateCASetVersionResponse.from_dict(a)
                for a in data.get("activations", [])
            ],
        )


@dataclass
class ListCASetActivationsRequest:
    """Request for ListCASetActivations.

    Mirrors Go ListCASetActivationsRequest.
    """

    ca_set_id: str = ""


@dataclass
class ListCASetActivationsResponse:
    """Response from ListCASetActivations.

    Mirrors Go ListCASetActivationsResponse.
    """

    activations: list[ActivateCASetVersionResponse] = field(
        default_factory=list
    )

    @classmethod
    def from_dict(cls, data: dict) -> ListCASetActivationsResponse:
        """Create ListCASetActivationsResponse from API response dict."""
        return cls(
            activations=[
                ActivateCASetVersionResponse.from_dict(a)
                for a in data.get("activations", [])
            ],
        )


# ---------------------------------------------------------------------------
# Certificate validation models (from certificate.go)
# ---------------------------------------------------------------------------


@dataclass
class ValidateCertificate:
    """Single certificate for validation. Mirrors Go ValidateCertificate."""

    certificate_pem: str = ""
    description: str | None = None


@dataclass
class ValidateCertificatesRequest:
    """Request for ValidateCertificates. Mirrors Go ValidateCertificatesRequest."""

    allow_insecure_sha1: bool = False
    certificates: list[ValidateCertificate] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dict for JSON request body."""
        certs = []
        for cert in self.certificates:
            cert_dict: dict[str, object] = {
                "certificatePem": cert.certificate_pem,
            }
            if cert.description is not None:
                cert_dict["description"] = cert.description
            certs.append(cert_dict)
        return {
            "allowInsecureSha1": self.allow_insecure_sha1,
            "certificates": certs,
        }


@dataclass
class ValidateCertificateResponse:
    """Single certificate validation result.

    Mirrors Go ValidateCertificateResponse.
    """

    certificate_pem: str = ""
    end_date: str = ""
    fingerprint: str = ""
    issuer: str = ""
    serial_number: str = ""
    signature_algorithm: str = ""
    start_date: str = ""
    subject: str = ""
    description: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> ValidateCertificateResponse:
        """Create ValidateCertificateResponse from API response dict."""
        return cls(
            certificate_pem=data.get("certificatePem", ""),
            end_date=data.get("endDate", ""),
            fingerprint=data.get("fingerprint", ""),
            issuer=data.get("issuer", ""),
            serial_number=data.get("serialNumber", ""),
            signature_algorithm=data.get("signatureAlgorithm", ""),
            start_date=data.get("startDate", ""),
            subject=data.get("subject", ""),
            description=data.get("description"),
        )


@dataclass
class ValidateCertificatesResponse:
    """Response from ValidateCertificates.

    Mirrors Go ValidateCertificatesResponse.
    """

    allow_insecure_sha1: bool = False
    certificates: list[ValidateCertificateResponse] = field(
        default_factory=list
    )
    validation: Validation = field(default_factory=Validation)

    @classmethod
    def from_dict(cls, data: dict) -> ValidateCertificatesResponse:
        """Create ValidateCertificatesResponse from API response dict."""
        raw_validation = data.get("validation")
        validation = (
            Validation.from_dict(raw_validation)
            if raw_validation is not None
            else Validation()
        )
        return cls(
            allow_insecure_sha1=data.get("allowInsecureSha1", False),
            certificates=[
                ValidateCertificateResponse.from_dict(c)
                for c in data.get("certificates", [])
            ],
            validation=validation,
        )
