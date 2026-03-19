# pylint: disable=too-many-instance-attributes
"""Request and response data models for the HAPI service client.

Defines all request and response dataclasses for the Akamai
Hostname API (HAPI), mirroring Go pkg/hapi structs field-for-field.

Go reference files:
- pkg/hapi/change_requests.go (GetChangeRequest, ChangeRequest)
- pkg/hapi/edgehostname.go (all edge hostname structs)
"""

from dataclasses import dataclass, field


# === Shared Models ===

@dataclass
class ChinaCDN:
    """China CDN settings for an edge hostname.

    Mirrors Go pkg/hapi.ChinaCDN struct.
    """
    is_china_cdn: bool = False
    custom_china_cdn_map: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "ChinaCDN":
        """Create ChinaCDN from a parsed JSON dictionary.

        Args:
            data: Dictionary from JSON response body.

        Returns:
            Populated ChinaCDN instance.
        """
        if data is None:
            return cls()
        return cls(
            is_china_cdn=data.get("isChinaCdn", False),
            custom_china_cdn_map=data.get("customChinaCdnMap", ""),
        )


@dataclass
class UseCase:
    """Use-case attribute in EdgeHostname.

    Mirrors Go pkg/hapi.UseCase struct.
    """
    type: str = ""
    option: str = ""
    use_case: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "UseCase":
        """Create UseCase from a parsed JSON dictionary.

        Args:
            data: Dictionary from JSON response body.

        Returns:
            Populated UseCase instance.
        """
        return cls(
            type=data.get("type", ""),
            option=data.get("option", ""),
            use_case=data.get("useCase", ""),
        )


@dataclass
class EdgeHostname:
    """Edge hostname data shared across responses.

    Mirrors Go pkg/hapi.EdgeHostname struct.
    """
    edge_hostname_id: int = 0
    record_name: str = ""
    dns_zone: str = ""
    security_type: str = ""
    use_default_ttl: bool = False
    use_default_map: bool = False
    ttl: int = 0
    map: str = ""
    slot_number: int = 0
    ip_version_behavior: str = ""
    comments: str = ""
    china_cdn: ChinaCDN = field(default_factory=ChinaCDN)
    custom_target: str = ""
    is_edge_ip_binding_enabled: bool = False
    map_alias: str = ""
    product_id: str = ""
    serial_number: int = 0
    use_cases: list[UseCase] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "EdgeHostname":
        """Create EdgeHostname from a parsed JSON dictionary.

        Args:
            data: Dictionary from JSON response body.

        Returns:
            Populated EdgeHostname instance.
        """
        china_cdn_data = data.get("chinaCdn")
        use_cases_data = data.get("useCases", [])

        return cls(
            edge_hostname_id=data.get("edgeHostnameId", 0),
            record_name=data.get("recordName", ""),
            dns_zone=data.get("dnsZone", ""),
            security_type=data.get("securityType", ""),
            use_default_ttl=data.get("useDefaultTtl", False),
            use_default_map=data.get("useDefaultMap", False),
            ttl=data.get("ttl", 0),
            map=data.get("map", ""),
            slot_number=data.get("slotNumber", 0),
            ip_version_behavior=data.get("ipVersionBehavior", ""),
            comments=data.get("comments", ""),
            china_cdn=(
                ChinaCDN.from_dict(china_cdn_data)
                if china_cdn_data
                else ChinaCDN()
            ),
            custom_target=data.get("customTarget", ""),
            is_edge_ip_binding_enabled=data.get(
                "isEdgeIPBindingEnabled", False
            ),
            map_alias=data.get("mapAlias", ""),
            product_id=data.get("productId", ""),
            serial_number=data.get("serialNumber", 0),
            use_cases=(
                [UseCase.from_dict(uc) for uc in use_cases_data]
                if use_cases_data
                else []
            ),
        )


# === Request Models ===

@dataclass
class GetChangeRequestRequest:
    """Request to get a change request by ID.

    Mirrors Go pkg/hapi.GetChangeRequest struct.
    """
    change_id: int = 0


@dataclass
class DeleteEdgeHostnameRequest:
    """Request to delete an edge hostname.

    Mirrors Go pkg/hapi.DeleteEdgeHostnameRequest struct.
    Fields are used to construct the URL and query parameters
    (not serialized to JSON).
    """
    dns_zone: str = ""
    record_name: str = ""
    status_update_email: list[str] = field(default_factory=list)
    comments: str = ""


@dataclass
class UpdateEdgeHostnameRequestBody:
    """Individual JSON Patch operation for edge hostname update.

    Mirrors Go pkg/hapi.UpdateEdgeHostnameRequestBody struct.
    Serialized to JSON as part of the PATCH request body.
    """
    op: str = ""
    path: str = ""
    value: str = ""


@dataclass
class UpdateEdgeHostnameRequest:
    """Request to update an edge hostname via JSON Patch.

    Mirrors Go pkg/hapi.UpdateEdgeHostnameRequest struct.
    DNSZone and RecordName build the URL; StatusUpdateEmail and
    Comments become query parameters; Body is serialized as the
    JSON Patch request body.
    """
    dns_zone: str = ""
    record_name: str = ""
    status_update_email: list[str] = field(default_factory=list)
    comments: str = ""
    body: list[UpdateEdgeHostnameRequestBody] = field(default_factory=list)


@dataclass
class GetCertificateRequest:
    """Request to get a certificate for an edge hostname.

    Mirrors Go pkg/hapi.GetCertificateRequest struct.
    """
    dns_zone: str = ""
    record_name: str = ""


# === Response Models ===

@dataclass
class ChangeRequest:
    """Response containing change request status and details.

    Mirrors Go pkg/hapi.ChangeRequest struct.
    Note: change_id maps from Go int64 to Python int.
    """
    action: str = ""
    change_id: int = 0
    comments: str = ""
    edge_hostnames: list[EdgeHostname] = field(default_factory=list)
    status: str = ""
    status_message: str = ""
    status_update_email: str = ""
    status_update_date: str = ""
    submit_date: str = ""
    submitter: str = ""
    submitter_email: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "ChangeRequest":
        """Create ChangeRequest from a parsed JSON dictionary.

        Args:
            data: Dictionary from JSON response body.

        Returns:
            Populated ChangeRequest instance.
        """
        edge_hostnames_data = data.get("edgeHostnames", [])
        return cls(
            action=data.get("action", ""),
            change_id=data.get("changeId", 0),
            comments=data.get("comments", ""),
            edge_hostnames=(
                [EdgeHostname.from_dict(eh) for eh in edge_hostnames_data]
                if edge_hostnames_data
                else []
            ),
            status=data.get("status", ""),
            status_message=data.get("statusMessage", ""),
            status_update_email=data.get("statusUpdateEmail", ""),
            status_update_date=data.get("statusUpdateDate", ""),
            submit_date=data.get("submitDate", ""),
            submitter=data.get("submitter", ""),
            submitter_email=data.get("submitterEmail", ""),
        )


@dataclass
class DeleteEdgeHostnameResponse:
    """Response from deleting an edge hostname.

    Mirrors Go pkg/hapi.DeleteEdgeHostnameResponse struct.
    """
    action: str = ""
    change_id: int = 0
    comments: str = ""
    status: str = ""
    status_message: str = ""
    status_update_date: str = ""
    status_update_email: str = ""
    submit_date: str = ""
    submitter: str = ""
    submitter_email: str = ""
    edge_hostnames: list[EdgeHostname] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "DeleteEdgeHostnameResponse":
        """Create DeleteEdgeHostnameResponse from a parsed JSON dictionary.

        Args:
            data: Dictionary from JSON response body.

        Returns:
            Populated DeleteEdgeHostnameResponse instance.
        """
        edge_hostnames_data = data.get("edgeHostnames", [])
        return cls(
            action=data.get("action", ""),
            change_id=data.get("changeId", 0),
            comments=data.get("comments", ""),
            status=data.get("status", ""),
            status_message=data.get("statusMessage", ""),
            status_update_date=data.get("statusUpdateDate", ""),
            status_update_email=data.get("statusUpdateEmail", ""),
            submit_date=data.get("submitDate", ""),
            submitter=data.get("submitter", ""),
            submitter_email=data.get("submitterEmail", ""),
            edge_hostnames=(
                [EdgeHostname.from_dict(eh) for eh in edge_hostnames_data]
                if edge_hostnames_data
                else []
            ),
        )


@dataclass
class UpdateEdgeHostnameResponse:
    """Response from updating an edge hostname.

    Mirrors Go pkg/hapi.UpdateEdgeHostnameResponse struct.
    """
    action: str = ""
    change_id: int = 0
    comments: str = ""
    status: str = ""
    status_message: str = ""
    status_update_date: str = ""
    status_update_email: str = ""
    submit_date: str = ""
    submitter: str = ""
    submitter_email: str = ""
    edge_hostnames: list[EdgeHostname] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "UpdateEdgeHostnameResponse":
        """Create UpdateEdgeHostnameResponse from a parsed JSON dictionary.

        Args:
            data: Dictionary from JSON response body.

        Returns:
            Populated UpdateEdgeHostnameResponse instance.
        """
        edge_hostnames_data = data.get("edgeHostnames", [])
        return cls(
            action=data.get("action", ""),
            change_id=data.get("changeId", 0),
            comments=data.get("comments", ""),
            status=data.get("status", ""),
            status_message=data.get("statusMessage", ""),
            status_update_date=data.get("statusUpdateDate", ""),
            status_update_email=data.get("statusUpdateEmail", ""),
            submit_date=data.get("submitDate", ""),
            submitter=data.get("submitter", ""),
            submitter_email=data.get("submitterEmail", ""),
            edge_hostnames=(
                [EdgeHostname.from_dict(eh) for eh in edge_hostnames_data]
                if edge_hostnames_data
                else []
            ),
        )


@dataclass
class GetEdgeHostnameResponse:
    """Response containing edge hostname details.

    Mirrors Go pkg/hapi.GetEdgeHostnameResponse struct.
    """
    edge_hostname_id: int = 0
    record_name: str = ""
    dns_zone: str = ""
    security_type: str = ""
    use_default_ttl: bool = False
    use_default_map: bool = False
    ip_version_behavior: str = ""
    product_id: str = ""
    ttl: int = 0
    map: str = ""
    slot_number: int = 0
    comments: str = ""
    serial_number: int = 0
    custom_target: str = ""
    china_cdn: ChinaCDN = field(default_factory=ChinaCDN)
    is_edge_ip_binding_enabled: bool = False
    map_alias: str = ""
    use_cases: list[UseCase] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "GetEdgeHostnameResponse":
        """Create GetEdgeHostnameResponse from a parsed JSON dictionary.

        Args:
            data: Dictionary from JSON response body.

        Returns:
            Populated GetEdgeHostnameResponse instance.
        """
        china_cdn_data = data.get("chinaCdn")
        use_cases_data = data.get("useCases", [])

        return cls(
            edge_hostname_id=data.get("edgeHostnameId", 0),
            record_name=data.get("recordName", ""),
            dns_zone=data.get("dnsZone", ""),
            security_type=data.get("securityType", ""),
            use_default_ttl=data.get("useDefaultTtl", False),
            use_default_map=data.get("useDefaultMap", False),
            ip_version_behavior=data.get("ipVersionBehavior", ""),
            product_id=data.get("productId", ""),
            ttl=data.get("ttl", 0),
            map=data.get("map", ""),
            slot_number=data.get("slotNumber", 0),
            comments=data.get("comments", ""),
            serial_number=data.get("serialNumber", 0),
            custom_target=data.get("customTarget", ""),
            china_cdn=(
                ChinaCDN.from_dict(china_cdn_data)
                if china_cdn_data
                else ChinaCDN()
            ),
            is_edge_ip_binding_enabled=data.get(
                "isEdgeIPBindingEnabled", False
            ),
            map_alias=data.get("mapAlias", ""),
            use_cases=(
                [UseCase.from_dict(uc) for uc in use_cases_data]
                if use_cases_data
                else []
            ),
        )


@dataclass
class GetCertificateResponse:
    """Response containing edge hostname certificate details.

    Mirrors Go pkg/hapi.GetCertificateResponse struct.

    Note: expiration_date is stored as an ISO 8601 string
    (Go time.Time maps to str per the type mapping convention).
    Note: serial_number is str (not int) because certificate
    serial numbers are colon-delimited hex strings.
    """
    available_domains: list[str] = field(default_factory=list)
    certificate_id: str = ""
    certificate_type: str = ""
    common_name: str = ""
    expiration_date: str = ""
    serial_number: str = ""
    slot_number: int = 0
    status: str = ""
    validation_type: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "GetCertificateResponse":
        """Create GetCertificateResponse from a parsed JSON dictionary.

        Args:
            data: Dictionary from JSON response body.

        Returns:
            Populated GetCertificateResponse instance.
        """
        return cls(
            available_domains=data.get("availableDomains", []),
            certificate_id=data.get("certificateId", ""),
            certificate_type=data.get("certificateType", ""),
            common_name=data.get("commonName", ""),
            expiration_date=data.get("expirationDate", ""),
            serial_number=data.get("serialNumber", ""),
            slot_number=data.get("slotNumber", 0),
            status=data.get("status", ""),
            validation_type=data.get("validationType", ""),
        )
