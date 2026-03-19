"""Request and response models for the CPS API client."""
# pylint: disable=too-many-instance-attributes
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# OCSPStapling constants (enrollments.go lines 221-228)
# ---------------------------------------------------------------------------

OCSP_STAPLING_ON: str = "on"
OCSP_STAPLING_OFF: str = "off"
OCSP_STAPLING_NOT_SET: str = "not-set"


# ---------------------------------------------------------------------------
# Enrollment models (enrollments.go)
# ---------------------------------------------------------------------------

@dataclass
class Contact:
    """Contact information. Mirrors Go Contact struct."""
    address_line_one: str = ""    # json:"addressLineOne"
    address_line_two: str = ""    # json:"addressLineTwo"
    city: str = ""                # json:"city"
    country: str = ""             # json:"country"
    email: str = ""               # json:"email"
    first_name: str = ""          # json:"firstName"
    last_name: str = ""           # json:"lastName"
    organization_name: str = ""   # json:"organizationName"
    phone: str = ""               # json:"phone"
    postal_code: str = ""         # json:"postalCode"
    region: str = ""              # json:"region"
    title: str = ""               # json:"title"


@dataclass
class CSR:
    """Certificate Signing Request. Mirrors Go CSR struct."""
    c: str = ""                     # json:"c"
    cn: str = ""                    # json:"cn"
    l: str = ""                     # json:"l"
    o: str = ""                     # json:"o"
    ou: str = ""                    # json:"ou"
    preferred_trust_chain: str = "" # json:"preferredTrustChain"
    sans: list[str] = field(default_factory=list)  # json:"sans"
    st: str = ""                    # json:"st"


@dataclass
class OCSP:
    """OCSP stapling configuration. Mirrors Go OCSP struct."""
    enabled: bool | None = None  # json:"enabled" — Go: *bool


@dataclass
class AuthenticationOptions:
    """Authentication options for client mutual auth.

    Mirrors Go AuthenticationOptions struct.
    """
    ocsp: OCSP | None = None                    # json:"ocsp"
    send_ca_list_to_client: bool | None = None  # json:"sendCaListToClient"


@dataclass
class ClientMutualAuthentication:
    """Client mutual authentication.

    Mirrors Go ClientMutualAuthentication struct.
    """
    # json:"authenticationOptions"
    authentication_options: AuthenticationOptions | None = None
    set_id: str = ""  # json:"setId"


@dataclass
class DNSNameSettings:
    """DNS name settings. Mirrors Go DNSNameSettings struct."""
    clone_dns_names: bool = False  # json:"cloneDnsNames"
    dns_names: list[str] = field(  # json:"dnsNames"
        default_factory=list)


@dataclass
class NetworkConfiguration:
    """Network configuration.

    Mirrors Go NetworkConfiguration struct.
    """
    # json:"clientMutualAuthentication"
    client_mutual_authentication: (
        ClientMutualAuthentication | None
    ) = None
    disallowed_tls_versions: list[str] = field(  # json:"disallowedTlsVersions"
        default_factory=list)
    dns_name_settings: DNSNameSettings | None = None  # json:"dnsNameSettings"
    geography: str = ""          # json:"geography"
    must_have_ciphers: str = ""  # json:"mustHaveCiphers"
    ocsp_stapling: str = ""      # json:"ocspStapling"
    preferred_ciphers: str = ""  # json:"preferredCiphers"
    quic_enabled: bool = False   # json:"quicEnabled"
    secure_network: str = ""     # json:"secureNetwork"
    sni_only: bool = False       # json:"sniOnly"


@dataclass
class Org:
    """Organization information. Mirrors Go Org struct."""
    address_line_one: str = ""  # json:"addressLineOne"
    address_line_two: str = ""  # json:"addressLineTwo"
    city: str = ""              # json:"city"
    country: str = ""           # json:"country"
    name: str = ""              # json:"name"
    phone: str = ""             # json:"phone"
    postal_code: str = ""       # json:"postalCode"
    region: str = ""            # json:"region"


@dataclass
class PendingChange:
    """Pending change information. Mirrors Go PendingChange struct."""
    change_type: str = ""  # json:"changeType"
    location: str = ""     # json:"location"


@dataclass
class ThirdParty:
    """Third-party certificate config. Mirrors Go ThirdParty struct."""
    exclude_sans: bool = False  # json:"excludeSans"


@dataclass
class Enrollment:
    """CPS enrollment object. Mirrors Go Enrollment struct."""
    id: int = 0                             # json:"id"
    production_slots: list[int] = field(    # json:"productionSlots"
        default_factory=list)
    staging_slots: list[int] = field(       # json:"stagingSlots"
        default_factory=list)
    assigned_slots: list[int] = field(      # json:"assignedSlots"
        default_factory=list)
    admin_contact: Contact | None = None    # json:"adminContact"
    auto_renewal_start_time: str = ""       # json:"autoRenewalStartTime"
    certificate_chain_type: str = ""        # json:"certificateChainType"
    certificate_type: str = ""              # json:"certificateType"
    change_management: bool = False         # json:"changeManagement"
    csr: CSR | None = None                  # json:"csr"
    enable_multi_stacked_certificates: bool = False  # json:"enableMultiStackedCertificates"
    location: str = ""                      # json:"location"
    max_allowed_san_names: int = 0          # json:"maxAllowedSanNames"
    max_allowed_wildcard_san_names: int = 0  # json:"maxAllowedWildcardSanNames"
    # json:"networkConfiguration"
    network_configuration: NetworkConfiguration | None = None
    org: Org | None = None                  # json:"org"
    org_id: int | None = None               # json:"orgId" — Go: *int
    pending_changes: list[PendingChange] = field(  # json:"pendingChanges"
        default_factory=list)
    ra: str = ""                            # json:"ra"
    signature_algorithm: str = ""           # json:"signatureAlgorithm"
    tech_contact: Contact | None = None     # json:"techContact"
    third_party: ThirdParty | None = None   # json:"thirdParty"
    validation_type: str = ""               # json:"validationType"


@dataclass
class ListEnrollmentsResponse:
    """Response for ListEnrollments.

    Mirrors Go ListEnrollmentsResponse struct.
    """
    enrollments: list[Enrollment] = field(  # json:"enrollments"
        default_factory=list)


# Go: type GetEnrollmentResponse Enrollment
GetEnrollmentResponse = Enrollment


@dataclass
class EnrollmentRequestBody:
    """Request body for creating/updating enrollment.

    Mirrors Go EnrollmentRequestBody struct.
    """
    admin_contact: Contact | None = None    # json:"adminContact"
    auto_renewal_start_time: str = ""       # json:"autoRenewalStartTime"
    certificate_chain_type: str = ""        # json:"certificateChainType"
    certificate_type: str = ""              # json:"certificateType"
    change_management: bool = False         # json:"changeManagement"
    csr: CSR | None = None                  # json:"csr"
    enable_multi_stacked_certificates: bool = False  # json:"enableMultiStackedCertificates"
    # json:"networkConfiguration"
    network_configuration: NetworkConfiguration | None = None
    org: Org | None = None                  # json:"org"
    org_id: int | None = None               # json:"orgId" — Go: *int
    ra: str = ""                            # json:"ra"
    signature_algorithm: str = ""           # json:"signatureAlgorithm"
    tech_contact: Contact | None = None     # json:"techContact"
    third_party: ThirdParty | None = None   # json:"thirdParty"
    validation_type: str = ""               # json:"validationType"


@dataclass
class CreateEnrollmentResponse:
    """Response for CreateEnrollment.

    Mirrors Go CreateEnrollmentResponse struct.
    """
    id: int = 0                                       # parsed from Location
    enrollment: str = ""                              # json:"enrollment"
    changes: list[str] = field(default_factory=list)  # json:"changes"


@dataclass
class UpdateEnrollmentResponse:
    """Response for UpdateEnrollment.

    Mirrors Go UpdateEnrollmentResponse struct.
    """
    id: int = 0                                       # parsed from Location
    enrollment: str = ""                              # json:"enrollment"
    changes: list[str] = field(default_factory=list)  # json:"changes"


@dataclass
class RemoveEnrollmentResponse:
    """Response for RemoveEnrollment.

    Mirrors Go RemoveEnrollmentResponse struct.
    """
    enrollment: str = ""                              # json:"enrollment"
    changes: list[str] = field(default_factory=list)  # json:"changes"


# ---------------------------------------------------------------------------
# Change models (changes.go, deployment_schedules.go)
# ---------------------------------------------------------------------------

@dataclass
class DeploymentSchedule:
    """Deployment schedule. Mirrors Go DeploymentSchedule struct."""
    not_after: str | None = None   # json:"notAfter" — Go: *string
    not_before: str | None = None  # json:"notBefore" — Go: *string


@dataclass
class StatusInfoError:
    """Status info error. Mirrors Go StatusInfoError struct."""
    code: str = ""         # json:"code"
    description: str = ""  # json:"description"
    timestamp: str = ""    # json:"timestamp"


@dataclass
class StatusInfo:
    """Status info. Mirrors Go StatusInfo struct."""
    # json:"deploymentSchedule"
    deployment_schedule: DeploymentSchedule | None = None
    description: str = ""                   # json:"description"
    error: StatusInfoError | None = None    # json:"error"
    state: str = ""                         # json:"state"
    status: str = ""                        # json:"status"


@dataclass
class AllowedInput:
    """Allowed input for a change. Mirrors Go AllowedInput struct."""
    info: str = ""                     # json:"info"
    required_to_proceed: bool = False  # json:"requiredToProceed"
    type: str = ""                     # json:"type"
    update: str = ""                   # json:"update"


@dataclass
class Change:
    """Change status information. Mirrors Go Change struct."""
    allowed_input: list[AllowedInput] = field(  # json:"allowedInput"
        default_factory=list)
    status_info: StatusInfo | None = None       # json:"statusInfo"


@dataclass
class Certificate:
    """Digital certificate. Mirrors Go Certificate struct."""
    certificate: str = ""  # json:"certificate"
    trust_chain: str = ""  # json:"trustChain"


@dataclass
class CancelChangeResponse:
    """Response for CancelChange.

    Mirrors Go CancelChangeResponse struct.
    """
    change: str = ""  # json:"change"


@dataclass
class Acknowledgement:
    """Acknowledgement request body. Mirrors Go Acknowledgement struct."""
    acknowledgement: str = ""  # json:"acknowledgement"


# ---------------------------------------------------------------------------
# Deployment models (deployments.go)
# ---------------------------------------------------------------------------

@dataclass
class DeploymentCertificate:
    """Certificate in deployment context.

    Mirrors Go DeploymentCertificate struct.
    """
    certificate: str = ""          # json:"certificate"
    expiry: str = ""               # json:"expiry"
    key_algorithm: str = ""        # json:"keyAlgorithm"
    signature_algorithm: str = ""  # json:"signatureAlgorithm"
    trust_chain: str = ""          # json:"trustChain"


@dataclass
class DeploymentNetworkConfiguration:
    """Network config in deployment context.

    Mirrors Go DeploymentNetworkConfiguration struct.
    """
    geography: str = ""          # json:"geography"
    must_have_ciphers: str = ""  # json:"mustHaveCiphers"
    ocsp_stapling: str = ""      # json:"ocspStapling"
    preferred_ciphers: str = ""  # json:"preferredCiphers"
    quic_enabled: bool = False   # json:"quicEnabled"
    secure_network: str = ""     # json:"secureNetwork"
    sni_only: bool = False       # json:"sniOnly"
    disallowed_tls_versions: list[str] = field(  # json:"disallowedTlsVersions"
        default_factory=list)
    dns_names: list[str] = field(  # json:"dnsNames"
        default_factory=list)


@dataclass
class Deployment:
    """Deployment details. Mirrors Go Deployment struct."""
    ocsp_stapled: bool | None = None         # json:"ocspStapled" — *bool
    ocsp_uris: list[str] = field(            # json:"ocspUris"
        default_factory=list)
    # json:"networkConfiguration"
    network_configuration: DeploymentNetworkConfiguration = field(
        default_factory=DeploymentNetworkConfiguration)
    # json:"primaryCertificate"
    primary_certificate: DeploymentCertificate = field(
        default_factory=DeploymentCertificate)
    # json:"multiStackedCertificates"
    multi_stacked_certificates: list[DeploymentCertificate] = field(
        default_factory=list)


@dataclass
class ListDeploymentsResponse:
    """Response for ListDeployments.

    Mirrors Go ListDeploymentsResponse struct.
    """
    production: Deployment | None = None  # json:"production"
    staging: Deployment | None = None     # json:"staging"


# Go: type GetProductionDeploymentResponse Deployment
GetProductionDeploymentResponse = Deployment

# Go: type GetStagingDeploymentResponse Deployment
GetStagingDeploymentResponse = Deployment


# ---------------------------------------------------------------------------
# Deployment schedule response (deployment_schedules.go)
# ---------------------------------------------------------------------------

@dataclass
class UpdateDeploymentScheduleResponse:
    """Response for UpdateDeploymentSchedule.

    Mirrors Go UpdateDeploymentScheduleResponse struct.
    """
    change: str = ""  # json:"change"


# ---------------------------------------------------------------------------
# DV challenge models (dv_challenges.go)
# ---------------------------------------------------------------------------

@dataclass
class ValidationRecord:
    """Validation attempt record.

    Mirrors Go ValidationRecord struct.
    """
    authorities: list[str] = field(   # json:"authorities"
        default_factory=list)
    hostname: str = ""                # json:"hostname"
    port: str = ""                    # json:"port"
    resolved_ip: list[str] = field(   # json:"resolvedIp"
        default_factory=list)
    tried_ip: str = ""                # json:"triedIp"
    url: str = ""                     # json:"url"
    used_ip: str = ""                 # json:"usedIp"


@dataclass
class Challenge:
    """Domain validation challenge. Mirrors Go Challenge struct."""
    error: str = ""              # json:"error"
    full_path: str = ""          # json:"fullPath"
    redirect_full_path: str = "" # json:"redirectFullPath"
    response_body: str = ""      # json:"responseBody"
    status: str = ""             # json:"status"
    token: str = ""              # json:"token"
    type: str = ""               # json:"type"
    # json:"validationRecords"
    validation_records: list[ValidationRecord] = field(
        default_factory=list)


@dataclass
class DV:
    """Domain Validation entity. Mirrors Go DV struct."""
    challenges: list[Challenge] = field(  # json:"challenges"
        default_factory=list)
    domain: str = ""               # json:"domain"
    error: str = ""                # json:"error"
    expires: str = ""              # json:"expires"
    request_timestamp: str = ""    # json:"requestTimestamp"
    status: str = ""               # json:"status"
    validated_timestamp: str = ""  # json:"validatedTimestamp"
    validation_status: str = ""    # json:"validationStatus"


@dataclass
class DVArray:
    """Array of DV objects. Mirrors Go DVArray struct."""
    dv: list[DV] = field(default_factory=list)  # json:"dv"


# ---------------------------------------------------------------------------
# History models (history.go)
# ---------------------------------------------------------------------------

@dataclass
class DomainHistory:
    """Domain history. Mirrors Go DomainHistory struct."""
    domain: str = ""              # json:"domain"
    challenges: list[Challenge] = field(  # json:"challenges"
        default_factory=list)
    error: str = ""               # json:"error"
    expires: str = ""             # json:"expires"
    full_path: str = ""           # json:"fullPath"
    redirect_full_path: str = ""  # json:"redirectFullPath"
    request_timestamp: str = ""   # json:"requestTimestamp"
    response_body: str = ""       # json:"responseBody"
    status: str = ""              # json:"status"
    token: str = ""               # json:"token"
    validated_timestamp: str = "" # json:"validatedTimestamp"
    # json:"validationRecords"
    validation_records: list[ValidationRecord] = field(
        default_factory=list)
    validation_status: str = ""   # json:"validationStatus"


@dataclass
class HistoryResult:
    """DV history result. Mirrors Go HistoryResult struct."""
    domain: str = ""  # json:"domain"
    domain_history: list[DomainHistory] = field(  # json:"domainHistory"
        default_factory=list)


@dataclass
class GetDVHistoryResponse:
    """Response for GetDVHistory.

    Mirrors Go GetDVHistoryResponse struct.
    """
    results: list[HistoryResult] = field(  # json:"results"
        default_factory=list)


@dataclass
class CertificateObject:
    """Certificate for enrollment.

    Mirrors Go CertificateObject struct.
    """
    certificate: str = ""    # json:"certificate"
    expiry: str = ""         # json:"expiry"
    key_algorithm: str = ""  # json:"keyAlgorithm"
    trust_chain: str = ""    # json:"trustChain"


@dataclass
class HistoryCertificate:
    """Certificate history entry.

    Mirrors Go HistoryCertificate struct.
    """
    deployment_status: str = ""  # json:"deploymentStatus"
    geography: str = ""          # json:"geography"
    # json:"multiStackedCertificates"
    multi_stacked_certificates: list[CertificateObject] = field(
        default_factory=list)
    # json:"primaryCertificate"
    primary_certificate: CertificateObject = field(
        default_factory=CertificateObject)
    ra: str = ""                              # json:"ra"
    slots: list[int] = field(                 # json:"slots"
        default_factory=list)
    staging_status: str = ""                  # json:"stagingStatus"
    type: str = ""                            # json:"type"


@dataclass
class GetCertificateHistoryResponse:
    """Response for GetCertificateHistory.

    Mirrors Go GetCertificateHistoryResponse struct.
    """
    certificates: list[HistoryCertificate] = field(  # json:"certificates"
        default_factory=list)


@dataclass
class CertificateOrderDetails:
    """CA order details for a change.

    Mirrors Go CertificateOrderDetails struct.
    """
    order_id: str = ""  # json:"orderId"


@dataclass
class CertificateChangeHistory:
    """Certificate in change history.

    Mirrors Go CertificateChangeHistory struct.
    """
    certificate: str = ""    # json:"certificate"
    trust_chain: str = ""    # json:"trustChain"
    csr: str = ""            # json:"csr"
    key_algorithm: str = ""  # json:"keyAlgorithm"


@dataclass
class ChangeHistory:
    """Change history entry. Mirrors Go ChangeHistory struct."""
    action: str = ""              # json:"action"
    action_description: str = ""  # json:"actionDescription"
    business_case_id: str = ""    # json:"businessCaseId"
    created_by: str = ""          # json:"createdBy"
    created_on: str = ""          # json:"createdOn"
    last_updated: str = ""        # json:"lastUpdated"
    # json:"multiStackedCertificates"
    multi_stacked_certificates: list[CertificateChangeHistory] = field(
        default_factory=list)
    # json:"primaryCertificate"
    primary_certificate: CertificateChangeHistory = field(
        default_factory=CertificateChangeHistory)
    # json:"primaryCertificateOrderDetails"
    primary_certificate_order_details: CertificateOrderDetails = field(
        default_factory=CertificateOrderDetails)
    ra: str = ""      # json:"ra"
    status: str = ""  # json:"status"


@dataclass
class GetChangeHistoryResponse:
    """Response for GetChangeHistory.

    Mirrors Go GetChangeHistoryResponse struct.
    """
    changes: list[ChangeHistory] = field(  # json:"changes"
        default_factory=list)


# ---------------------------------------------------------------------------
# Change management info models (change_management_info.go)
# ---------------------------------------------------------------------------

@dataclass
class PendingCertificate:
    """Pending certificate snapshot.

    Mirrors Go PendingCertificate struct.
    """
    certificate_type: str = ""     # json:"certificateType"
    full_certificate: str = ""     # json:"fullCertificate"
    ocsp_stapled: str = ""         # json:"ocspStapled"
    ocsp_uris: list[str] = field(  # json:"ocspUris"
        default_factory=list)
    signature_algorithm: str = ""  # json:"signatureAlgorithm"
    key_algorithm: str = ""        # json:"keyAlgorithm"


@dataclass
class PendingNetworkConfiguration:
    """Pending network configuration.

    Mirrors Go PendingNetworkConfiguration struct.
    """
    # json:"dnsNameSettings"
    dns_name_settings: DNSNameSettings | None = None
    must_have_ciphers: str = ""  # json:"mustHaveCiphers"
    network_type: str = ""       # json:"networkType"
    ocsp_stapling: str = ""      # json:"ocspStapling"
    preferred_ciphers: str = ""  # json:"preferredCiphers"
    quic_enabled: str = ""       # json:"quicEnabled"
    sni_only: str = ""           # json:"sniOnly"
    disallowed_tls_versions: list[str] = field(  # json:"disallowedTlsVersions"
        default_factory=list)


@dataclass
class PendingState:
    """Pending state snapshot. Mirrors Go PendingState struct."""
    # json:"pendingCertificates"
    pending_certificates: list[PendingCertificate] = field(
        default_factory=list)
    # json:"pendingNetworkConfiguration"
    pending_network_configuration: PendingNetworkConfiguration = field(
        default_factory=PendingNetworkConfiguration)


@dataclass
class ValidationMessage:
    """Validation message. Mirrors Go ValidationMessage struct."""
    message: str = ""       # json:"message"
    message_code: str = ""  # json:"messageCode"


@dataclass
class ValidationResult:
    """Validation result. Mirrors Go ValidationResult struct."""
    errors: list[ValidationMessage] = field(    # json:"errors"
        default_factory=list)
    warnings: list[ValidationMessage] = field(  # json:"warnings"
        default_factory=list)


@dataclass
class ChangeManagementInfoResponse:
    """Response for GetChangeManagementInfo.

    Mirrors Go ChangeManagementInfoResponse struct.
    """
    # json:"acknowledgementDeadline" — Go: *string
    acknowledgement_deadline: str | None = None
    validation_result_hash: str = ""  # json:"validationResultHash"
    pending_state: PendingState = field(  # json:"pendingState"
        default_factory=PendingState)
    # json:"validationResult"
    validation_result: ValidationResult | None = None


# Go: type ChangeDeploymentInfoResponse Deployment
ChangeDeploymentInfoResponse = Deployment


# ---------------------------------------------------------------------------
# Verification warning models
# (post_verification_warnings.go, pre_verification_warnings.go)
# ---------------------------------------------------------------------------

@dataclass
class PostVerificationWarnings:
    """Post-verification warnings.

    Mirrors Go PostVerificationWarnings struct.
    """
    warnings: str = ""  # json:"warnings"


@dataclass
class PreVerificationWarnings:
    """Pre-verification warnings.

    Mirrors Go PreVerificationWarnings struct.
    """
    warnings: str = ""  # json:"warnings"


# ---------------------------------------------------------------------------
# Third-party CSR models (third_party_csr.go)
# ---------------------------------------------------------------------------

@dataclass
class CertSigningRequest:
    """Certificate signing request.

    Mirrors Go CertSigningRequest struct.
    """
    csr: str = ""            # json:"csr"
    key_algorithm: str = ""  # json:"keyAlgorithm"


@dataclass
class ThirdPartyCSRResponse:
    """Response for GetChangeThirdPartyCSR.

    Mirrors Go ThirdPartyCSRResponse struct.
    """
    csrs: list[CertSigningRequest] = field(  # json:"csrs"
        default_factory=list)


@dataclass
class CertificateAndTrustChain:
    """Certificate with trust chain.

    Mirrors Go CertificateAndTrustChain struct.
    """
    certificate: str = ""    # json:"certificate"
    trust_chain: str = ""    # json:"trustChain"
    key_algorithm: str = ""  # json:"keyAlgorithm"


@dataclass
class ThirdPartyCertificates:
    """Third-party certificates.

    Mirrors Go ThirdPartyCertificates struct.
    """
    # json:"certificatesAndTrustChains"
    certificates_and_trust_chains: list[
        CertificateAndTrustChain
    ] = field(default_factory=list)
