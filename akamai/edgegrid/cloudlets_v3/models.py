"""Request and response models for the Cloudlets V3 API."""
# This module mirrors Go v12 struct definitions field-for-field.
# Field names like 'type' and 'id' shadow Python builtins to match Go JSON tags.
# Constant names use Go PascalCase convention for parity.
# pylint: disable=redefined-builtin,invalid-name,too-many-instance-attributes,too-many-lines

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Module-level helper functions
# ---------------------------------------------------------------------------


def _to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase for JSON serialization.

    Handles standard conversions. Special cases like matchURL, redirectURL,
    checkIPs, pathAndQS require explicit mapping in individual methods.
    """
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def _is_zero(value) -> bool:
    """Check if a value is considered empty for Go omitempty semantics.

    In Go JSON encoding, omitempty skips zero values: false for bool,
    0 for numeric, empty string, nil for pointer/slice/map.
    """
    if value is None:
        return True
    if isinstance(value, bool):
        return not value
    if isinstance(value, (int, float)):
        return value == 0
    if isinstance(value, str):
        return value == ""
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


# ---------------------------------------------------------------------------
# Type aliases — Go typed string constants
# ---------------------------------------------------------------------------

# PolicyType (from policy.go)
PolicyType = str
PolicyTypeShared: str = "SHARED"

# CloudletType (from policy.go)
CloudletType = str
CloudletTypeAP: str = "AP"
CloudletTypeAS: str = "AS"
CloudletTypeCD: str = "CD"
CloudletTypeER: str = "ER"
CloudletTypeFR: str = "FR"
CloudletTypeIG: str = "IG"

# PolicyActivationOperation (from policy_activation.go)
PolicyActivationOperation = str
OperationActivation: str = "ACTIVATION"
OperationDeactivation: str = "DEACTIVATION"

# ActivationStatus (from policy_activation.go)
ActivationStatus = str
ActivationStatusInProgress: str = "IN_PROGRESS"
ActivationStatusSuccess: str = "SUCCESS"
ActivationStatusFailed: str = "FAILED"

# Network (from policy_activation.go)
Network = str
StagingNetwork: str = "STAGING"
ProductionNetwork: str = "PRODUCTION"

# MatchRuleType (from match_rule.go)
MatchRuleType = str
MatchRuleTypeAP: str = "apMatchRule"
MatchRuleTypeAS: str = "asMatchRule"
MatchRuleTypePR: str = "cdMatchRule"
MatchRuleTypeER: str = "erMatchRule"
MatchRuleTypeFR: str = "frMatchRule"
MatchRuleTypeRC: str = "igMatchRule"
MatchRuleTypeVP: str = "vpMatchRule"

# MatchRuleFormat (from match_rule.go)
MatchRuleFormat = str
MatchRuleFormat10: str = "1.0"

# MatchOperator (from match_rule.go)
MatchOperator = str
MatchOperatorContains: str = "contains"
MatchOperatorExists: str = "exists"
MatchOperatorEquals: str = "equals"

# AllowDeny (from match_rule.go)
AllowDeny = str
Allow: str = "allow"
Deny: str = "deny"
DenyBranded: str = "denybranded"

# CheckIPs (from match_rule.go)
CheckIPs = str
CheckIPsConnectingIP: str = "CONNECTING_IP"
CheckIPsXFFHeaders: str = "XFF_HEADERS"
CheckIPsConnectingIPXFFHeaders: str = "CONNECTING_IP XFF_HEADERS"

# ObjectMatchValue types (from match_rule.go)
ObjectMatchValueRangeType = str
Range: str = "range"

ObjectMatchValueSimpleType = str
Simple: str = "simple"

ObjectMatchValueObjectType = str
Object: str = "object"


# ---------------------------------------------------------------------------
# Shared types — Warning, Link, Page
# ---------------------------------------------------------------------------


@dataclass
class Warning:
    """Warning information regarding policy version requests.

    Mirrors Go Warning struct from warning.go.
    All JSON fields have omitempty.
    """

    detail: str = ""
    json_pointer: str = ""
    status: int = 0
    title: str = ""
    type: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> Warning:
        """Create Warning from a JSON dict."""
        if not data:
            return cls()
        return cls(
            detail=data.get("detail", ""),
            json_pointer=data.get("jsonPointer", ""),
            status=data.get("status", 0),
            title=data.get("title", ""),
            type=data.get("type", ""),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict with omitempty semantics."""
        result: dict = {}
        if self.detail:
            result["detail"] = self.detail
        if self.json_pointer:
            result["jsonPointer"] = self.json_pointer
        if self.status:
            result["status"] = self.status
        if self.title:
            result["title"] = self.title
        if self.type:
            result["type"] = self.type
        return result


@dataclass
class Link:
    """Hypermedia link for result set navigation.

    Mirrors Go Link struct from policy_property.go.
    No omitempty on any field.
    """

    href: str = ""
    rel: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> Link:
        """Create Link from a JSON dict."""
        if not data:
            return cls()
        return cls(href=data.get("href", ""), rel=data.get("rel", ""))

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict."""
        return {"href": self.href, "rel": self.rel}


@dataclass
class Page:
    """Pagination information.

    Mirrors Go Page struct from policy_property.go.
    No omitempty on any field.
    """

    number: int = 0
    size: int = 0
    total_elements: int = 0
    total_pages: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> Page:
        """Create Page from a JSON dict."""
        if not data:
            return cls()
        return cls(
            number=data.get("number", 0),
            size=data.get("size", 0),
            total_elements=data.get("totalElements", 0),
            total_pages=data.get("totalPages", 0),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict."""
        return {
            "number": self.number,
            "size": self.size,
            "totalElements": self.total_elements,
            "totalPages": self.total_pages,
        }


# ---------------------------------------------------------------------------
# Policy property types (from policy_property.go)
# ---------------------------------------------------------------------------


@dataclass
class ListActivePolicyPropertiesRequest:
    """Request for ListActivePolicyProperties.

    Mirrors Go struct from policy_property.go.
    All fields used for URL path/query params (json:"-").
    """

    policy_id: int = 0
    page: int = 0
    size: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> ListActivePolicyPropertiesRequest:
        """Create from a dict."""
        if not data:
            return cls()
        return cls(
            policy_id=data.get("policyId", 0),
            page=data.get("page", 0),
            size=data.get("size", 0),
        )

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "policyId": self.policy_id,
            "page": self.page,
            "size": self.size,
        }


@dataclass
class ListPolicyPropertiesItem:
    """Active property information.

    Mirrors Go struct from policy_property.go.
    No omitempty. Note: policy_version maps to JSON "version".
    """

    group_id: int = 0
    id: int = 0
    name: str = ""
    network: str = ""
    policy_version: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> ListPolicyPropertiesItem:
        """Create from a JSON dict."""
        if not data:
            return cls()
        return cls(
            group_id=data.get("groupId", 0),
            id=data.get("id", 0),
            name=data.get("name", ""),
            network=data.get("network", ""),
            policy_version=data.get("version", 0),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict."""
        return {
            "groupId": self.group_id,
            "id": self.id,
            "name": self.name,
            "network": self.network,
            "version": self.policy_version,
        }


@dataclass
class ListActivePolicyPropertiesResponse:
    """Response from ListActivePolicyProperties.

    Mirrors Go struct from policy_property.go.
    All fields have omitempty. policy_properties maps to JSON "content".
    """

    page: Page | None = None
    policy_properties: list[ListPolicyPropertiesItem] | None = field(
        default=None
    )
    links: list[Link] | None = field(default=None)

    @classmethod
    def from_dict(
        cls, data: dict
    ) -> ListActivePolicyPropertiesResponse:
        """Create from a JSON dict."""
        if not data:
            return cls()
        pg = data.get("page")
        content = data.get("content")
        lks = data.get("links")
        return cls(
            page=Page.from_dict(pg) if pg else None,
            policy_properties=(
                [ListPolicyPropertiesItem.from_dict(p) for p in content]
                if content
                else None
            ),
            links=(
                [Link.from_dict(lk) for lk in lks] if lks else None
            ),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict with omitempty."""
        result: dict = {}
        if self.page is not None:
            result["page"] = self.page.to_dict()
        if self.policy_properties is not None:
            result["content"] = [
                p.to_dict() for p in self.policy_properties
            ]
        if self.links is not None:
            result["links"] = [lk.to_dict() for lk in self.links]
        return result


# ---------------------------------------------------------------------------
# Policy types (from policy.go)
# ---------------------------------------------------------------------------


@dataclass
class ListPoliciesRequest:
    """Request for ListPolicies.

    Mirrors Go ListPoliciesRequest from policy.go.
    All fields used for query params (json:"-").
    """

    page: int = 0
    size: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> ListPoliciesRequest:
        """Create from a dict."""
        if not data:
            return cls()
        return cls(
            page=data.get("page", 0),
            size=data.get("size", 0),
        )

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {"page": self.page, "size": self.size}


@dataclass
class CreatePolicyRequest:
    """Request for CreatePolicy.

    Mirrors Go CreatePolicyRequest from policy.go.
    description and policy_type have omitempty; others do not.
    """

    cloudlet_type: str = ""
    description: str | None = None
    group_id: int = 0
    name: str = ""
    policy_type: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> CreatePolicyRequest:
        """Create from a JSON dict."""
        if not data:
            return cls()
        return cls(
            cloudlet_type=data.get("cloudletType", ""),
            description=data.get("description"),
            group_id=data.get("groupId", 0),
            name=data.get("name", ""),
            policy_type=data.get("policyType", ""),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict."""
        result: dict = {
            "cloudletType": self.cloudlet_type,
            "groupId": self.group_id,
            "name": self.name,
        }
        if self.description is not None:
            result["description"] = self.description
        if self.policy_type:
            result["policyType"] = self.policy_type
        return result


@dataclass
class DeletePolicyRequest:
    """Request for DeletePolicy.

    Mirrors Go DeletePolicyRequest from policy.go.
    PolicyID used for URL path (json:"-").
    """

    policy_id: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> DeletePolicyRequest:
        """Create from a dict."""
        if not data:
            return cls()
        return cls(policy_id=data.get("policyId", 0))

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {"policyId": self.policy_id}


@dataclass
class GetPolicyRequest:
    """Request for GetPolicy.

    Mirrors Go GetPolicyRequest from policy.go.
    PolicyID used for URL path (json:"-").
    """

    policy_id: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> GetPolicyRequest:
        """Create from a dict."""
        if not data:
            return cls()
        return cls(policy_id=data.get("policyId", 0))

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {"policyId": self.policy_id}


@dataclass
class UpdatePolicyRequestBody:
    """Body for UpdatePolicy request.

    Mirrors Go UpdatePolicyRequestBody from policy.go.
    group_id: no omitempty. description: omitempty (pointer).
    """

    group_id: int = 0
    description: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> UpdatePolicyRequestBody:
        """Create from a JSON dict."""
        if not data:
            return cls()
        return cls(
            group_id=data.get("groupId", 0),
            description=data.get("description"),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict."""
        result: dict = {"groupId": self.group_id}
        if self.description is not None:
            result["description"] = self.description
        return result


@dataclass
class UpdatePolicyRequest:
    """Request for UpdatePolicy.

    Mirrors Go UpdatePolicyRequest from policy.go.
    PolicyID for URL path, Body for HTTP body.
    """

    policy_id: int = 0
    body: UpdatePolicyRequestBody | None = None

    @classmethod
    def from_dict(cls, data: dict) -> UpdatePolicyRequest:
        """Create from a dict."""
        if not data:
            return cls()
        bd = data.get("body")
        return cls(
            policy_id=data.get("policyId", 0),
            body=UpdatePolicyRequestBody.from_dict(bd) if bd else None,
        )

    def to_dict(self) -> dict:
        """Serialize to dict."""
        result: dict = {"policyId": self.policy_id}
        if self.body is not None:
            result["body"] = self.body.to_dict()
        return result


@dataclass
class ClonePolicyRequestBody:
    """Body for ClonePolicy request.

    Mirrors Go ClonePolicyRequestBody from policy.go.
    additional_versions: omitempty. group_id, new_name: no omitempty.
    """

    additional_versions: list[int] | None = field(default=None)
    group_id: int = 0
    new_name: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> ClonePolicyRequestBody:
        """Create from a JSON dict."""
        if not data:
            return cls()
        return cls(
            additional_versions=data.get("additionalVersions"),
            group_id=data.get("groupId", 0),
            new_name=data.get("newName", ""),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict."""
        result: dict = {
            "groupId": self.group_id,
            "newName": self.new_name,
        }
        if self.additional_versions is not None:
            result["additionalVersions"] = self.additional_versions
        return result


@dataclass
class ClonePolicyRequest:
    """Request for ClonePolicy.

    Mirrors Go ClonePolicyRequest from policy.go.
    PolicyID for URL path, Body for HTTP body.
    """

    policy_id: int = 0
    body: ClonePolicyRequestBody | None = None

    @classmethod
    def from_dict(cls, data: dict) -> ClonePolicyRequest:
        """Create from a dict."""
        if not data:
            return cls()
        bd = data.get("body")
        return cls(
            policy_id=data.get("policyId", 0),
            body=(
                ClonePolicyRequestBody.from_dict(bd) if bd else None
            ),
        )

    def to_dict(self) -> dict:
        """Serialize to dict."""
        result: dict = {"policyId": self.policy_id}
        if self.body is not None:
            result["body"] = self.body.to_dict()
        return result


@dataclass
class CurrentActivations:
    """Current activation state for production and staging.

    Mirrors Go CurrentActivations from policy.go.
    No omitempty — both fields always serialized.
    """

    production: ActivationInfo | None = None
    staging: ActivationInfo | None = None

    @classmethod
    def from_dict(cls, data: dict) -> CurrentActivations:
        """Create from a JSON dict."""
        if not data:
            return cls()
        prod = data.get("production")
        stg = data.get("staging")
        return cls(
            production=(
                ActivationInfo.from_dict(prod) if prod else None
            ),
            staging=ActivationInfo.from_dict(stg) if stg else None,
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict (no omitempty)."""
        return {
            "production": (
                self.production.to_dict()
                if self.production is not None
                else None
            ),
            "staging": (
                self.staging.to_dict()
                if self.staging is not None
                else None
            ),
        }


@dataclass
class ActivationInfo:
    """Activation info with effective and latest activations.

    Mirrors Go ActivationInfo from policy.go.
    No omitempty — fields always serialized (null when nil).
    """

    effective: PolicyActivation | None = None
    latest: PolicyActivation | None = None

    @classmethod
    def from_dict(cls, data: dict) -> ActivationInfo:
        """Create from a JSON dict."""
        if not data:
            return cls()
        eff = data.get("effective")
        lat = data.get("latest")
        return cls(
            effective=(
                PolicyActivation.from_dict(eff) if eff else None
            ),
            latest=PolicyActivation.from_dict(lat) if lat else None,
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict (no omitempty)."""
        return {
            "effective": (
                self.effective.to_dict()
                if self.effective is not None
                else None
            ),
            "latest": (
                self.latest.to_dict()
                if self.latest is not None
                else None
            ),
        }


@dataclass
class Policy:
    """Policy resource representation.

    Mirrors Go Policy from policy.go.
    description: omitempty (pointer). All other fields: no omitempty.
    modified_date is a pointer but no omitempty (serializes as null).
    """

    cloudlet_type: str = ""
    created_by: str = ""
    created_date: str = ""
    current_activations: CurrentActivations | None = None
    description: str | None = None
    group_id: int = 0
    id: int = 0
    links: list[Link] | None = field(default=None)
    modified_by: str = ""
    modified_date: str | None = None
    name: str = ""
    policy_type: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> Policy:
        """Create from a JSON dict."""
        if not data:
            return cls()
        ca = data.get("currentActivations")
        lks = data.get("links")
        return cls(
            cloudlet_type=data.get("cloudletType", ""),
            created_by=data.get("createdBy", ""),
            created_date=data.get("createdDate", ""),
            current_activations=(
                CurrentActivations.from_dict(ca) if ca else None
            ),
            description=data.get("description"),
            group_id=data.get("groupId", 0),
            id=data.get("id", 0),
            links=(
                [Link.from_dict(lk) for lk in lks] if lks else None
            ),
            modified_by=data.get("modifiedBy", ""),
            modified_date=data.get("modifiedDate"),
            name=data.get("name", ""),
            policy_type=data.get("policyType", ""),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict."""
        result: dict = {
            "cloudletType": self.cloudlet_type,
            "createdBy": self.created_by,
            "createdDate": self.created_date,
            "currentActivations": (
                self.current_activations.to_dict()
                if self.current_activations is not None
                else None
            ),
            "groupId": self.group_id,
            "id": self.id,
            "links": (
                [lk.to_dict() for lk in self.links]
                if self.links is not None
                else None
            ),
            "modifiedBy": self.modified_by,
            "modifiedDate": self.modified_date,
            "name": self.name,
            "policyType": self.policy_type,
        }
        if self.description is not None:
            result["description"] = self.description
        return result


@dataclass
class ListPoliciesResponse:
    """Response from ListPolicies.

    Mirrors Go ListPoliciesResponse from policy.go.
    No omitempty on any field.
    """

    content: list[Policy] | None = field(default=None)
    links: list[Link] | None = field(default=None)
    page: Page | None = None

    @classmethod
    def from_dict(cls, data: dict) -> ListPoliciesResponse:
        """Create from a JSON dict."""
        if not data:
            return cls()
        ct = data.get("content")
        lks = data.get("links")
        pg = data.get("page")
        return cls(
            content=(
                [Policy.from_dict(p) for p in ct] if ct else None
            ),
            links=(
                [Link.from_dict(lk) for lk in lks] if lks else None
            ),
            page=Page.from_dict(pg) if pg else None,
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict (no omitempty)."""
        return {
            "content": (
                [p.to_dict() for p in self.content]
                if self.content is not None
                else None
            ),
            "links": (
                [lk.to_dict() for lk in self.links]
                if self.links is not None
                else None
            ),
            "page": (
                self.page.to_dict()
                if self.page is not None
                else None
            ),
        }


# ---------------------------------------------------------------------------
# ListCloudlets types (from list_cloudlets.go)
# ---------------------------------------------------------------------------


@dataclass
class ListCloudletsItem:
    """Cloudlet type information.

    Mirrors Go ListCloudletsItem from list_cloudlets.go.
    No omitempty on any field.
    """

    cloudlet_name: str = ""
    cloudlet_type: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> ListCloudletsItem:
        """Create from a JSON dict."""
        if not data:
            return cls()
        return cls(
            cloudlet_name=data.get("cloudletName", ""),
            cloudlet_type=data.get("cloudletType", ""),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict."""
        return {
            "cloudletName": self.cloudlet_name,
            "cloudletType": self.cloudlet_type,
        }


# ---------------------------------------------------------------------------
# PolicyVersion types (from policy_version.go)
# ---------------------------------------------------------------------------


@dataclass
class ListPolicyVersionsItem:
    """Policy version summary in list responses.

    Mirrors Go ListPolicyVersionsItem from policy_version.go.
    description: omitempty. modified_date: pointer, no omitempty.
    policy_version maps to JSON "version".
    """

    created_by: str = ""
    created_date: str = ""
    description: str | None = None
    id: int = 0
    immutable: bool = False
    links: list[Link] | None = field(default=None)
    modified_by: str = ""
    modified_date: str | None = None
    policy_id: int = 0
    policy_version: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> ListPolicyVersionsItem:
        """Create from a JSON dict."""
        if not data:
            return cls()
        lks = data.get("links")
        return cls(
            created_by=data.get("createdBy", ""),
            created_date=data.get("createdDate", ""),
            description=data.get("description"),
            id=data.get("id", 0),
            immutable=data.get("immutable", False),
            links=(
                [Link.from_dict(lk) for lk in lks] if lks else None
            ),
            modified_by=data.get("modifiedBy", ""),
            modified_date=data.get("modifiedDate"),
            policy_id=data.get("policyId", 0),
            policy_version=data.get("version", 0),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict."""
        result: dict = {
            "createdBy": self.created_by,
            "createdDate": self.created_date,
            "id": self.id,
            "immutable": self.immutable,
            "links": (
                [lk.to_dict() for lk in self.links]
                if self.links is not None
                else None
            ),
            "modifiedBy": self.modified_by,
            "modifiedDate": self.modified_date,
            "policyId": self.policy_id,
            "version": self.policy_version,
        }
        if self.description is not None:
            result["description"] = self.description
        return result


@dataclass
class ListPolicyVersions:
    """Response listing policy versions.

    Mirrors Go ListPolicyVersions from policy_version.go.
    No omitempty. policy_versions maps to JSON "content".
    """

    policy_versions: list[ListPolicyVersionsItem] | None = field(
        default=None
    )
    links: list[Link] | None = field(default=None)
    page: Page | None = None

    @classmethod
    def from_dict(cls, data: dict) -> ListPolicyVersions:
        """Create from a JSON dict."""
        if not data:
            return cls()
        ct = data.get("content")
        lks = data.get("links")
        pg = data.get("page")
        return cls(
            policy_versions=(
                [ListPolicyVersionsItem.from_dict(v) for v in ct]
                if ct
                else None
            ),
            links=(
                [Link.from_dict(lk) for lk in lks] if lks else None
            ),
            page=Page.from_dict(pg) if pg else None,
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict (no omitempty)."""
        return {
            "content": (
                [v.to_dict() for v in self.policy_versions]
                if self.policy_versions is not None
                else None
            ),
            "links": (
                [lk.to_dict() for lk in self.links]
                if self.links is not None
                else None
            ),
            "page": (
                self.page.to_dict()
                if self.page is not None
                else None
            ),
        }


@dataclass
class MatchRulesWarning:
    """Warning associated with match rules in a policy version.

    Mirrors Go MatchRulesWarning from policy_version.go.
    All fields have omitempty.
    """

    detail: str = ""
    json_pointer: str = ""
    title: str = ""
    type: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> MatchRulesWarning:
        """Create from a JSON dict."""
        if not data:
            return cls()
        return cls(
            detail=data.get("detail", ""),
            json_pointer=data.get("jsonPointer", ""),
            title=data.get("title", ""),
            type=data.get("type", ""),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict with omitempty."""
        result: dict = {}
        if self.detail:
            result["detail"] = self.detail
        if self.json_pointer:
            result["jsonPointer"] = self.json_pointer
        if self.title:
            result["title"] = self.title
        if self.type:
            result["type"] = self.type
        return result


@dataclass
class PolicyVersion:
    """Full policy version with match rules.

    Mirrors Go PolicyVersion from policy_version.go.
    description, match_rules, match_rules_warnings: omitempty.
    modified_date: pointer, no omitempty. policy_version -> JSON "version".
    """

    created_by: str = ""
    created_date: str = ""
    description: str | None = None
    id: int = 0
    immutable: bool = False
    match_rules: list | None = field(default=None)
    match_rules_warnings: list[MatchRulesWarning] | None = field(
        default=None
    )
    modified_by: str = ""
    modified_date: str | None = None
    policy_id: int = 0
    policy_version: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> PolicyVersion:
        """Create from a JSON dict."""
        if not data:
            return cls()
        mr = data.get("matchRules")
        mrw = data.get("matchRulesWarnings")
        return cls(
            created_by=data.get("createdBy", ""),
            created_date=data.get("createdDate", ""),
            description=data.get("description"),
            id=data.get("id", 0),
            immutable=data.get("immutable", False),
            match_rules=(
                deserialize_match_rules(mr)
                if mr is not None
                else None
            ),
            match_rules_warnings=(
                [MatchRulesWarning.from_dict(w) for w in mrw]
                if mrw
                else None
            ),
            modified_by=data.get("modifiedBy", ""),
            modified_date=data.get("modifiedDate"),
            policy_id=data.get("policyId", 0),
            policy_version=data.get("version", 0),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict."""
        result: dict = {
            "createdBy": self.created_by,
            "createdDate": self.created_date,
            "id": self.id,
            "immutable": self.immutable,
            "modifiedBy": self.modified_by,
            "modifiedDate": self.modified_date,
            "policyId": self.policy_id,
            "version": self.policy_version,
        }
        if self.description is not None:
            result["description"] = self.description
        if self.match_rules is not None:
            result["matchRules"] = [
                r.to_dict() for r in self.match_rules
            ]
        if self.match_rules_warnings is not None:
            result["matchRulesWarnings"] = [
                w.to_dict() for w in self.match_rules_warnings
            ]
        return result


@dataclass
class ListPolicyVersionsRequest:
    """Request for ListPolicyVersions.

    Mirrors Go ListPolicyVersionsRequest from policy_version.go.
    All fields used for URL/query params (json:"-").
    """

    policy_id: int = 0
    page: int = 0
    size: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> ListPolicyVersionsRequest:
        """Create from a dict."""
        if not data:
            return cls()
        return cls(
            policy_id=data.get("policyId", 0),
            page=data.get("page", 0),
            size=data.get("size", 0),
        )

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "policyId": self.policy_id,
            "page": self.page,
            "size": self.size,
        }


@dataclass
class GetPolicyVersionRequest:
    """Request for GetPolicyVersion.

    Mirrors Go GetPolicyVersionRequest from policy_version.go.
    All fields used for URL path (json:"-").
    """

    policy_id: int = 0
    policy_version: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> GetPolicyVersionRequest:
        """Create from a dict."""
        if not data:
            return cls()
        return cls(
            policy_id=data.get("policyId", 0),
            policy_version=data.get("policyVersion", 0),
        )

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "policyId": self.policy_id,
            "policyVersion": self.policy_version,
        }


@dataclass
class CreatePolicyVersion:
    """Body content for creating a policy version.

    Mirrors Go CreatePolicyVersion from policy_version.go.
    Both fields have omitempty.
    """

    description: str | None = None
    match_rules: list | None = field(default=None)

    @classmethod
    def from_dict(cls, data: dict) -> CreatePolicyVersion:
        """Create from a JSON dict."""
        if not data:
            return cls()
        mr = data.get("matchRules")
        return cls(
            description=data.get("description"),
            match_rules=(
                deserialize_match_rules(mr)
                if mr is not None
                else None
            ),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict with omitempty."""
        result: dict = {}
        if self.description is not None:
            result["description"] = self.description
        if self.match_rules is not None:
            result["matchRules"] = [
                r.to_dict() for r in self.match_rules
            ]
        return result


@dataclass
class CreatePolicyVersionRequest:
    """Request for CreatePolicyVersion.

    Mirrors Go CreatePolicyVersionRequest from policy_version.go.
    Embeds CreatePolicyVersion and adds PolicyID.
    """

    policy_id: int = 0
    create_policy_version: CreatePolicyVersion | None = None

    @classmethod
    def from_dict(cls, data: dict) -> CreatePolicyVersionRequest:
        """Create from a dict."""
        if not data:
            return cls()
        cpv = data.get("createPolicyVersion")
        return cls(
            policy_id=data.get("policyId", 0),
            create_policy_version=(
                CreatePolicyVersion.from_dict(cpv) if cpv else None
            ),
        )

    def to_dict(self) -> dict:
        """Serialize to dict."""
        result: dict = {"policyId": self.policy_id}
        if self.create_policy_version is not None:
            result["createPolicyVersion"] = (
                self.create_policy_version.to_dict()
            )
        return result


@dataclass
class UpdatePolicyVersion:
    """Body content for updating a policy version.

    Mirrors Go UpdatePolicyVersion from policy_version.go.
    Both fields have omitempty.
    """

    description: str | None = None
    match_rules: list | None = field(default=None)

    @classmethod
    def from_dict(cls, data: dict) -> UpdatePolicyVersion:
        """Create from a JSON dict."""
        if not data:
            return cls()
        mr = data.get("matchRules")
        return cls(
            description=data.get("description"),
            match_rules=(
                deserialize_match_rules(mr)
                if mr is not None
                else None
            ),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict with omitempty."""
        result: dict = {}
        if self.description is not None:
            result["description"] = self.description
        if self.match_rules is not None:
            result["matchRules"] = [
                r.to_dict() for r in self.match_rules
            ]
        return result


@dataclass
class DeletePolicyVersionRequest:
    """Request for DeletePolicyVersion.

    Mirrors Go DeletePolicyVersionRequest from policy_version.go.
    All fields used for URL path (json:"-").
    """

    policy_id: int = 0
    policy_version: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> DeletePolicyVersionRequest:
        """Create from a dict."""
        if not data:
            return cls()
        return cls(
            policy_id=data.get("policyId", 0),
            policy_version=data.get("policyVersion", 0),
        )

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "policyId": self.policy_id,
            "policyVersion": self.policy_version,
        }


@dataclass
class UpdatePolicyVersionRequest:
    """Request for UpdatePolicyVersion.

    Mirrors Go UpdatePolicyVersionRequest from policy_version.go.
    Embeds UpdatePolicyVersion plus PolicyID and PolicyVersion.
    """

    policy_id: int = 0
    policy_version: int = 0
    update_policy_version: UpdatePolicyVersion | None = None

    @classmethod
    def from_dict(cls, data: dict) -> UpdatePolicyVersionRequest:
        """Create from a dict."""
        if not data:
            return cls()
        upv = data.get("updatePolicyVersion")
        return cls(
            policy_id=data.get("policyId", 0),
            policy_version=data.get("policyVersion", 0),
            update_policy_version=(
                UpdatePolicyVersion.from_dict(upv) if upv else None
            ),
        )

    def to_dict(self) -> dict:
        """Serialize to dict."""
        result: dict = {
            "policyId": self.policy_id,
            "policyVersion": self.policy_version,
        }
        if self.update_policy_version is not None:
            result["updatePolicyVersion"] = (
                self.update_policy_version.to_dict()
            )
        return result


# ---------------------------------------------------------------------------
# PolicyActivation types (from policy_activation.go)
# ---------------------------------------------------------------------------


@dataclass
class ListPolicyActivationsRequest:
    """Request for ListPolicyActivations.

    Mirrors Go ListPolicyActivationsRequest from policy_activation.go.
    All fields used for URL/query params (json:"-").
    """

    policy_id: int = 0
    page: int = 0
    size: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> ListPolicyActivationsRequest:
        """Create from a dict."""
        if not data:
            return cls()
        return cls(
            policy_id=data.get("policyId", 0),
            page=data.get("page", 0),
            size=data.get("size", 0),
        )

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "policyId": self.policy_id,
            "page": self.page,
            "size": self.size,
        }


@dataclass
class GetPolicyActivationRequest:
    """Request for GetPolicyActivation.

    Mirrors Go GetPolicyActivationRequest from policy_activation.go.
    All fields used for URL path (json:"-").
    """

    policy_id: int = 0
    activation_id: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> GetPolicyActivationRequest:
        """Create from a dict."""
        if not data:
            return cls()
        return cls(
            policy_id=data.get("policyId", 0),
            activation_id=data.get("activationId", 0),
        )

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "policyId": self.policy_id,
            "activationId": self.activation_id,
        }


@dataclass
class ActivatePolicyRequest:
    """Request for ActivatePolicy.

    Mirrors Go ActivatePolicyRequest from policy_activation.go.
    All fields used for URL path/body (json:"-").
    """

    policy_id: int = 0
    network: str = ""
    policy_version: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> ActivatePolicyRequest:
        """Create from a dict."""
        if not data:
            return cls()
        return cls(
            policy_id=data.get("policyId", 0),
            network=data.get("network", ""),
            policy_version=data.get("policyVersion", 0),
        )

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "policyId": self.policy_id,
            "network": self.network,
            "policyVersion": self.policy_version,
        }


@dataclass
class DeactivatePolicyRequest:
    """Request for DeactivatePolicy.

    Mirrors Go DeactivatePolicyRequest from policy_activation.go.
    All fields used for URL path/body (json:"-").
    """

    policy_id: int = 0
    network: str = ""
    policy_version: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> DeactivatePolicyRequest:
        """Create from a dict."""
        if not data:
            return cls()
        return cls(
            policy_id=data.get("policyId", 0),
            network=data.get("network", ""),
            policy_version=data.get("policyVersion", 0),
        )

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return {
            "policyId": self.policy_id,
            "network": self.network,
            "policyVersion": self.policy_version,
        }


@dataclass
class PolicyActivation:
    """Policy activation resource.

    Mirrors Go PolicyActivation from policy_activation.go.
    No omitempty on any field. finish_date is pointer, no omitempty.
    """

    created_by: str = ""
    created_date: str = ""
    finish_date: str | None = None
    id: int = 0
    network: str = ""
    operation: str = ""
    policy_id: int = 0
    status: str = ""
    policy_version: int = 0
    policy_version_deleted: bool = False
    links: list[Link] | None = field(default=None)

    @classmethod
    def from_dict(cls, data: dict) -> PolicyActivation:
        """Create from a JSON dict."""
        if not data:
            return cls()
        lks = data.get("links")
        return cls(
            created_by=data.get("createdBy", ""),
            created_date=data.get("createdDate", ""),
            finish_date=data.get("finishDate"),
            id=data.get("id", 0),
            network=data.get("network", ""),
            operation=data.get("operation", ""),
            policy_id=data.get("policyId", 0),
            status=data.get("status", ""),
            policy_version=data.get("policyVersion", 0),
            policy_version_deleted=data.get(
                "policyVersionDeleted", False
            ),
            links=(
                [Link.from_dict(lk) for lk in lks] if lks else None
            ),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict (no omitempty)."""
        return {
            "createdBy": self.created_by,
            "createdDate": self.created_date,
            "finishDate": self.finish_date,
            "id": self.id,
            "network": self.network,
            "operation": self.operation,
            "policyId": self.policy_id,
            "status": self.status,
            "policyVersion": self.policy_version,
            "policyVersionDeleted": self.policy_version_deleted,
            "links": (
                [lk.to_dict() for lk in self.links]
                if self.links is not None
                else None
            ),
        }


@dataclass
class PolicyActivations:
    """Paginated list of policy activations.

    Mirrors Go PolicyActivations from policy_activation.go.
    No omitempty. policy_activations maps to JSON "content".
    """

    page: Page | None = None
    policy_activations: list[PolicyActivation] | None = field(
        default=None
    )
    links: list[Link] | None = field(default=None)

    @classmethod
    def from_dict(cls, data: dict) -> PolicyActivations:
        """Create from a JSON dict."""
        if not data:
            return cls()
        pg = data.get("page")
        ct = data.get("content")
        lks = data.get("links")
        return cls(
            page=Page.from_dict(pg) if pg else None,
            policy_activations=(
                [PolicyActivation.from_dict(a) for a in ct]
                if ct
                else None
            ),
            links=(
                [Link.from_dict(lk) for lk in lks] if lks else None
            ),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict (no omitempty)."""
        return {
            "page": (
                self.page.to_dict()
                if self.page is not None
                else None
            ),
            "content": (
                [a.to_dict() for a in self.policy_activations]
                if self.policy_activations is not None
                else None
            ),
            "links": (
                [lk.to_dict() for lk in self.links]
                if self.links is not None
                else None
            ),
        }


# ---------------------------------------------------------------------------
# Match rule support types (from match_rule.go)
# ---------------------------------------------------------------------------


@dataclass
class Options:
    """Options for ObjectMatchValueObject.

    Mirrors Go Options from match_rule.go.
    All fields have omitempty.
    """

    value: list[str] | None = field(default=None)
    value_has_wildcard: bool = False
    value_case_sensitive: bool = False
    value_escaped: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> Options:
        """Create from a JSON dict."""
        if not data:
            return cls()
        return cls(
            value=data.get("value"),
            value_has_wildcard=data.get("valueHasWildcard", False),
            value_case_sensitive=data.get(
                "valueCaseSensitive", False
            ),
            value_escaped=data.get("valueEscaped", False),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict with omitempty."""
        result: dict = {}
        if self.value is not None:
            result["value"] = self.value
        if self.value_has_wildcard:
            result["valueHasWildcard"] = self.value_has_wildcard
        if self.value_case_sensitive:
            result["valueCaseSensitive"] = self.value_case_sensitive
        if self.value_escaped:
            result["valueEscaped"] = self.value_escaped
        return result


@dataclass
class ObjectMatchValueObject:
    """Object-type match value with named options.

    Mirrors Go ObjectMatchValueObject from match_rule.go.
    All fields have omitempty.
    """

    name: str = ""
    type: str = ""
    name_case_sensitive: bool = False
    name_has_wildcard: bool = False
    options: Options | None = None

    @classmethod
    def from_dict(cls, data: dict) -> ObjectMatchValueObject:
        """Create from a JSON dict."""
        if not data:
            return cls()
        opts = data.get("options")
        return cls(
            name=data.get("name", ""),
            type=data.get("type", ""),
            name_case_sensitive=data.get(
                "nameCaseSensitive", False
            ),
            name_has_wildcard=data.get("nameHasWildcard", False),
            options=Options.from_dict(opts) if opts else None,
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict with omitempty."""
        result: dict = {}
        if self.name:
            result["name"] = self.name
        if self.type:
            result["type"] = self.type
        if self.name_case_sensitive:
            result["nameCaseSensitive"] = self.name_case_sensitive
        if self.name_has_wildcard:
            result["nameHasWildcard"] = self.name_has_wildcard
        if self.options is not None:
            result["options"] = self.options.to_dict()
        return result


@dataclass
class ObjectMatchValueSimple:
    """Simple-type match value with string array.

    Mirrors Go ObjectMatchValueSimple from match_rule.go.
    All fields have omitempty.
    """

    type: str = ""
    value: list[str] | None = field(default=None)

    @classmethod
    def from_dict(cls, data: dict) -> ObjectMatchValueSimple:
        """Create from a JSON dict."""
        if not data:
            return cls()
        return cls(
            type=data.get("type", ""),
            value=data.get("value"),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict with omitempty."""
        result: dict = {}
        if self.type:
            result["type"] = self.type
        if self.value is not None:
            result["value"] = self.value
        return result


@dataclass
class ObjectMatchValueRange:
    """Range-type match value with integer array.

    Mirrors Go ObjectMatchValueRange from match_rule.go.
    All fields have omitempty.
    """

    type: str = ""
    value: list[int] | None = field(default=None)

    @classmethod
    def from_dict(cls, data: dict) -> ObjectMatchValueRange:
        """Create from a JSON dict."""
        if not data:
            return cls()
        return cls(
            type=data.get("type", ""),
            value=data.get("value"),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict with omitempty."""
        result: dict = {}
        if self.type:
            result["type"] = self.type
        if self.value is not None:
            result["value"] = self.value
        return result


# ---------------------------------------------------------------------------
# ObjectMatchValue deserialization helpers
# ---------------------------------------------------------------------------

# Handlers for AP, PR, ER, FR, RC match criteria (object + simple)
_SIMPLE_OBJECT_OMV_HANDLERS: dict[str, type] = {
    "simple": ObjectMatchValueSimple,
    "object": ObjectMatchValueObject,
}

# Handlers for AS match criteria (object + simple + range)
_ALL_OMV_HANDLERS: dict[str, type] = {
    "simple": ObjectMatchValueSimple,
    "range": ObjectMatchValueRange,
    "object": ObjectMatchValueObject,
}


def _deserialize_object_match_value(
    data: Any, handlers: dict[str, type],
    rule_type_label: str = "",
) -> Any:
    """Deserialize objectMatchValue based on its type field.

    Args:
        data: Raw objectMatchValue dict from JSON.
        handlers: Map of type string to class constructor.
        rule_type_label: Label for error messages (e.g.
            'MatchCriteriaPR').

    Returns:
        Typed ObjectMatchValue instance, or None.

    Raises:
        ValueError: If the objectMatchValue type is not in the
            allowed handlers map.
    """
    if not data or not isinstance(data, dict):
        return data
    omv_type = data.get("type", "")
    handler = handlers.get(omv_type)
    if handler is not None:
        return handler.from_dict(data)
    if omv_type:
        label = rule_type_label or "MatchCriteria"
        raise ValueError(
            f"unmarshalling MatchRules: "
            f"unmarshalling {label}: "
            f"objectMatchValue has unexpected type: '{omv_type}'"
        )
    return data


# ---------------------------------------------------------------------------
# MatchCriteria (from match_rule.go)
# ---------------------------------------------------------------------------


@dataclass
class MatchCriteria:
    """Base match criteria for all cloudlet match rule types.

    Mirrors Go MatchCriteria from match_rule.go.
    case_sensitive and negate: no omitempty (always serialized).
    All other fields: omitempty.
    """

    match_type: str = ""
    match_value: str = ""
    match_operator: str = ""
    case_sensitive: bool = False
    negate: bool = False
    check_ips: str = ""
    object_match_value: Any = None

    @classmethod
    def from_dict(cls, data: dict) -> MatchCriteria:
        """Create from a JSON dict with automatic OMV resolution.

        Resolves objectMatchValue to the correct typed class based
        on its 'type' field, accepting all three variants.
        """
        if not data:
            return cls()
        omv_raw = data.get("objectMatchValue")
        omv = _deserialize_object_match_value(
            omv_raw, _ALL_OMV_HANDLERS
        )
        return cls(
            match_type=data.get("matchType", ""),
            match_value=data.get("matchValue", ""),
            match_operator=data.get("matchOperator", ""),
            case_sensitive=data.get("caseSensitive", False),
            negate=data.get("negate", False),
            check_ips=data.get("checkIPs", ""),
            object_match_value=omv,
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict."""
        result: dict = {
            "caseSensitive": self.case_sensitive,
            "negate": self.negate,
        }
        if self.match_type:
            result["matchType"] = self.match_type
        if self.match_value:
            result["matchValue"] = self.match_value
        if self.match_operator:
            result["matchOperator"] = self.match_operator
        if self.check_ips:
            result["checkIPs"] = self.check_ips
        if self.object_match_value is not None:
            if hasattr(self.object_match_value, "to_dict"):
                result["objectMatchValue"] = (
                    self.object_match_value.to_dict()
                )
            else:
                result["objectMatchValue"] = (
                    self.object_match_value
                )
        return result


# Type aliases for per-rule match criteria (Go type aliases)
MatchCriteriaAP = MatchCriteria
MatchCriteriaAS = MatchCriteria
MatchCriteriaPR = MatchCriteria
MatchCriteriaER = MatchCriteria
MatchCriteriaFR = MatchCriteria
MatchCriteriaRC = MatchCriteria


def _deserialize_criteria_list(
    data: list | None, handlers: dict[str, type],
    rule_type_label: str = "",
) -> list[MatchCriteria] | None:
    """Deserialize a list of match criteria dicts.

    Each criterion's objectMatchValue is resolved using the given
    OMV type handlers.
    """
    if data is None:
        return None
    result: list[MatchCriteria] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        omv_raw = item.get("objectMatchValue")
        omv = _deserialize_object_match_value(
            omv_raw, handlers, rule_type_label=rule_type_label,
        )
        criteria = MatchCriteria(
            match_type=item.get("matchType", ""),
            match_value=item.get("matchValue", ""),
            match_operator=item.get("matchOperator", ""),
            case_sensitive=item.get("caseSensitive", False),
            negate=item.get("negate", False),
            check_ips=item.get("checkIPs", ""),
            object_match_value=omv,
        )
        result.append(criteria)
    return result if result else None


# ---------------------------------------------------------------------------
# ForwardSettings types (from match_rule.go)
# ---------------------------------------------------------------------------


@dataclass
class ForwardSettingsAS:
    """Forward settings for API Prioritization (AS) match rules.

    Mirrors Go ForwardSettingsAS from match_rule.go.
    All fields have omitempty.
    """

    path_and_qs: str = ""
    use_incoming_query_string: bool = False
    origin_id: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> ForwardSettingsAS:
        """Create from a JSON dict."""
        if not data:
            return cls()
        return cls(
            path_and_qs=data.get("pathAndQS", ""),
            use_incoming_query_string=data.get(
                "useIncomingQueryString", False
            ),
            origin_id=data.get("originId", ""),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict with omitempty."""
        result: dict = {}
        if self.path_and_qs:
            result["pathAndQS"] = self.path_and_qs
        if self.use_incoming_query_string:
            result["useIncomingQueryString"] = (
                self.use_incoming_query_string
            )
        if self.origin_id:
            result["originId"] = self.origin_id
        return result


@dataclass
class ForwardSettingsPR:
    """Forward settings for Phased Release (PR/CD) match rules.

    Mirrors Go ForwardSettingsPR from match_rule.go.
    No omitempty on any field.
    """

    origin_id: str = ""
    percent: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> ForwardSettingsPR:
        """Create from a JSON dict."""
        if not data:
            return cls()
        return cls(
            origin_id=data.get("originId", ""),
            percent=data.get("percent", 0),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict (no omitempty)."""
        return {
            "originId": self.origin_id,
            "percent": self.percent,
        }


@dataclass
class ForwardSettingsFR:
    """Forward settings for Forward Rewrite (FR) match rules.

    Mirrors Go ForwardSettingsFR from match_rule.go.
    All fields have omitempty.
    """

    path_and_qs: str = ""
    use_incoming_query_string: bool = False
    origin_id: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> ForwardSettingsFR:
        """Create from a JSON dict."""
        if not data:
            return cls()
        return cls(
            path_and_qs=data.get("pathAndQS", ""),
            use_incoming_query_string=data.get(
                "useIncomingQueryString", False
            ),
            origin_id=data.get("originId", ""),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict with omitempty."""
        result: dict = {}
        if self.path_and_qs:
            result["pathAndQS"] = self.path_and_qs
        if self.use_incoming_query_string:
            result["useIncomingQueryString"] = (
                self.use_incoming_query_string
            )
        if self.origin_id:
            result["originId"] = self.origin_id
        return result


# ---------------------------------------------------------------------------
# MatchRule types (from match_rule.go)
# ---------------------------------------------------------------------------


@dataclass
class MatchRuleAP:
    """Application Load Balancer (AP) match rule.

    Mirrors Go MatchRuleAP from match_rule.go.
    pass_through_percent: no omitempty (always serialized, nullable).
    All other fields: omitempty.
    """

    name: str = ""
    type: str = ""
    start: int = 0
    end: int = 0
    id: int = 0
    matches: list[MatchCriteriaAP] | None = field(default=None)
    match_url: str = ""
    pass_through_percent: float | None = None
    disabled: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> MatchRuleAP:
        """Create from a JSON dict."""
        if not data:
            return cls()
        matches_raw = data.get("matches")
        matches = _deserialize_criteria_list(
            matches_raw, _SIMPLE_OBJECT_OMV_HANDLERS,
            rule_type_label="MatchCriteriaAP",
        )
        return cls(
            name=data.get("name", ""),
            type=data.get("type", ""),
            start=data.get("start", 0),
            end=data.get("end", 0),
            id=data.get("id", 0),
            matches=matches,
            match_url=data.get("matchURL", ""),
            pass_through_percent=data.get("passThroughPercent"),
            disabled=data.get("disabled", False),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict."""
        result: dict = {}
        if self.name:
            result["name"] = self.name
        if self.type:
            result["type"] = self.type
        if self.start:
            result["start"] = self.start
        if self.end:
            result["end"] = self.end
        if self.id:
            result["id"] = self.id
        if self.matches is not None:
            result["matches"] = [m.to_dict() for m in self.matches]
        if self.match_url:
            result["matchURL"] = self.match_url
        # passThroughPercent: no omitempty — always included
        result["passThroughPercent"] = self.pass_through_percent
        if self.disabled:
            result["disabled"] = self.disabled
        return result


@dataclass
class MatchRuleAS:
    """API Prioritization (AS) match rule.

    Mirrors Go MatchRuleAS from match_rule.go.
    forward_settings: no omitempty (always serialized).
    All other fields: omitempty.
    """

    name: str = ""
    type: str = ""
    start: int = 0
    end: int = 0
    id: int = 0
    matches: list[MatchCriteriaAS] | None = field(default=None)
    match_url: str = ""
    forward_settings: ForwardSettingsAS | None = None
    disabled: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> MatchRuleAS:
        """Create from a JSON dict."""
        if not data:
            return cls()
        matches_raw = data.get("matches")
        matches = _deserialize_criteria_list(
            matches_raw, _ALL_OMV_HANDLERS
        )
        fs_raw = data.get("forwardSettings")
        return cls(
            name=data.get("name", ""),
            type=data.get("type", ""),
            start=data.get("start", 0),
            end=data.get("end", 0),
            id=data.get("id", 0),
            matches=matches,
            match_url=data.get("matchURL", ""),
            forward_settings=(
                ForwardSettingsAS.from_dict(fs_raw)
                if fs_raw is not None else None
            ),
            disabled=data.get("disabled", False),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict."""
        result: dict = {}
        if self.name:
            result["name"] = self.name
        if self.type:
            result["type"] = self.type
        if self.start:
            result["start"] = self.start
        if self.end:
            result["end"] = self.end
        if self.id:
            result["id"] = self.id
        if self.matches is not None:
            result["matches"] = [m.to_dict() for m in self.matches]
        if self.match_url:
            result["matchURL"] = self.match_url
        # forwardSettings: no omitempty — always included
        if self.forward_settings is not None:
            result["forwardSettings"] = (
                self.forward_settings.to_dict()
            )
        else:
            result["forwardSettings"] = {}
        if self.disabled:
            result["disabled"] = self.disabled
        return result


@dataclass
class MatchRulePR:
    """Phased Release (PR / CD cloudlet) match rule.

    Mirrors Go MatchRulePR from match_rule.go.
    forward_settings: no omitempty (always serialized).
    All other fields: omitempty.
    """

    name: str = ""
    type: str = ""
    start: int = 0
    end: int = 0
    id: int = 0
    matches: list[MatchCriteriaPR] | None = field(default=None)
    match_url: str = ""
    forward_settings: ForwardSettingsPR | None = None
    disabled: bool = False
    matches_always: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> MatchRulePR:
        """Create from a JSON dict."""
        if not data:
            return cls()
        matches_raw = data.get("matches")
        matches = _deserialize_criteria_list(
            matches_raw, _SIMPLE_OBJECT_OMV_HANDLERS,
            rule_type_label="MatchCriteriaPR",
        )
        fs_raw = data.get("forwardSettings")
        return cls(
            name=data.get("name", ""),
            type=data.get("type", ""),
            start=data.get("start", 0),
            end=data.get("end", 0),
            id=data.get("id", 0),
            matches=matches,
            match_url=data.get("matchURL", ""),
            forward_settings=(
                ForwardSettingsPR.from_dict(fs_raw)
                if fs_raw is not None else None
            ),
            disabled=data.get("disabled", False),
            matches_always=data.get("matchesAlways", False),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict."""
        result: dict = {}
        if self.name:
            result["name"] = self.name
        if self.type:
            result["type"] = self.type
        if self.start:
            result["start"] = self.start
        if self.end:
            result["end"] = self.end
        if self.id:
            result["id"] = self.id
        if self.matches is not None:
            result["matches"] = [m.to_dict() for m in self.matches]
        if self.match_url:
            result["matchURL"] = self.match_url
        # forwardSettings: no omitempty — always included
        if self.forward_settings is not None:
            result["forwardSettings"] = (
                self.forward_settings.to_dict()
            )
        else:
            result["forwardSettings"] = ForwardSettingsPR().to_dict()
        if self.disabled:
            result["disabled"] = self.disabled
        if self.matches_always:
            result["matchesAlways"] = self.matches_always
        return result


@dataclass
class MatchRuleER:
    """Edge Redirector (ER) match rule.

    Mirrors Go MatchRuleER from match_rule.go.
    Fields without omitempty (always serialized):
        use_relative_url, status_code, redirect_url,
        use_incoming_query_string, use_incoming_scheme_and_host.
    All other fields: omitempty.
    """

    name: str = ""
    type: str = ""
    start: int = 0
    end: int = 0
    id: int = 0
    matches: list[MatchCriteriaER] | None = field(default=None)
    matches_always: bool = False
    use_relative_url: str = ""
    status_code: int = 0
    redirect_url: str = ""
    match_url: str = ""
    use_incoming_query_string: bool = False
    use_incoming_scheme_and_host: bool = False
    disabled: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> MatchRuleER:
        """Create from a JSON dict."""
        if not data:
            return cls()
        matches_raw = data.get("matches")
        matches = _deserialize_criteria_list(
            matches_raw, _SIMPLE_OBJECT_OMV_HANDLERS,
            rule_type_label="MatchCriteriaER",
        )
        return cls(
            name=data.get("name", ""),
            type=data.get("type", ""),
            start=data.get("start", 0),
            end=data.get("end", 0),
            id=data.get("id", 0),
            matches=matches,
            matches_always=data.get("matchesAlways", False),
            use_relative_url=data.get("useRelativeUrl", ""),
            status_code=data.get("statusCode", 0),
            redirect_url=data.get("redirectURL", ""),
            match_url=data.get("matchURL", ""),
            use_incoming_query_string=data.get(
                "useIncomingQueryString", False
            ),
            use_incoming_scheme_and_host=data.get(
                "useIncomingSchemeAndHost", False
            ),
            disabled=data.get("disabled", False),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict."""
        result: dict = {}
        if self.name:
            result["name"] = self.name
        if self.type:
            result["type"] = self.type
        if self.start:
            result["start"] = self.start
        if self.end:
            result["end"] = self.end
        if self.id:
            result["id"] = self.id
        if self.matches is not None:
            result["matches"] = [m.to_dict() for m in self.matches]
        if self.matches_always:
            result["matchesAlways"] = self.matches_always
        # Fields without omitempty — always included
        result["useRelativeUrl"] = self.use_relative_url
        result["statusCode"] = self.status_code
        result["redirectURL"] = self.redirect_url
        if self.match_url:
            result["matchURL"] = self.match_url
        result["useIncomingQueryString"] = (
            self.use_incoming_query_string
        )
        result["useIncomingSchemeAndHost"] = (
            self.use_incoming_scheme_and_host
        )
        if self.disabled:
            result["disabled"] = self.disabled
        return result


@dataclass
class MatchRuleFR:
    """Forward Rewrite (FR) match rule.

    Mirrors Go MatchRuleFR from match_rule.go.
    forward_settings: no omitempty (always serialized).
    All other fields: omitempty.
    """

    name: str = ""
    type: str = ""
    start: int = 0
    end: int = 0
    id: int = 0
    matches: list[MatchCriteriaFR] | None = field(default=None)
    match_url: str = ""
    forward_settings: ForwardSettingsFR | None = None
    disabled: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> MatchRuleFR:
        """Create from a JSON dict."""
        if not data:
            return cls()
        matches_raw = data.get("matches")
        matches = _deserialize_criteria_list(
            matches_raw, _SIMPLE_OBJECT_OMV_HANDLERS,
            rule_type_label="MatchCriteriaFR",
        )
        fs_raw = data.get("forwardSettings")
        return cls(
            name=data.get("name", ""),
            type=data.get("type", ""),
            start=data.get("start", 0),
            end=data.get("end", 0),
            id=data.get("id", 0),
            matches=matches,
            match_url=data.get("matchURL", ""),
            forward_settings=(
                ForwardSettingsFR.from_dict(fs_raw)
                if fs_raw is not None else None
            ),
            disabled=data.get("disabled", False),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict."""
        result: dict = {}
        if self.name:
            result["name"] = self.name
        if self.type:
            result["type"] = self.type
        if self.start:
            result["start"] = self.start
        if self.end:
            result["end"] = self.end
        if self.id:
            result["id"] = self.id
        if self.matches is not None:
            result["matches"] = [m.to_dict() for m in self.matches]
        if self.match_url:
            result["matchURL"] = self.match_url
        # forwardSettings: no omitempty — always included
        if self.forward_settings is not None:
            result["forwardSettings"] = (
                self.forward_settings.to_dict()
            )
        else:
            result["forwardSettings"] = {}
        if self.disabled:
            result["disabled"] = self.disabled
        return result


@dataclass
class MatchRuleRC:
    """Request Control (RC / IG cloudlet) match rule.

    Mirrors Go MatchRuleRC from match_rule.go.
    allow_deny: no omitempty (always serialized).
    All other fields: omitempty.
    """

    name: str = ""
    type: str = ""
    start: int = 0
    end: int = 0
    id: int = 0
    matches: list[MatchCriteriaRC] | None = field(default=None)
    matches_always: bool = False
    allow_deny: str = ""
    disabled: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> MatchRuleRC:
        """Create from a JSON dict."""
        if not data:
            return cls()
        matches_raw = data.get("matches")
        matches = _deserialize_criteria_list(
            matches_raw, _SIMPLE_OBJECT_OMV_HANDLERS,
            rule_type_label="MatchCriteriaRC",
        )
        return cls(
            name=data.get("name", ""),
            type=data.get("type", ""),
            start=data.get("start", 0),
            end=data.get("end", 0),
            id=data.get("id", 0),
            matches=matches,
            matches_always=data.get("matchesAlways", False),
            allow_deny=data.get("allowDeny", ""),
            disabled=data.get("disabled", False),
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-ready dict."""
        result: dict = {}
        if self.name:
            result["name"] = self.name
        if self.type:
            result["type"] = self.type
        if self.start:
            result["start"] = self.start
        if self.end:
            result["end"] = self.end
        if self.id:
            result["id"] = self.id
        if self.matches is not None:
            result["matches"] = [m.to_dict() for m in self.matches]
        if self.matches_always:
            result["matchesAlways"] = self.matches_always
        # allowDeny: no omitempty — always included
        result["allowDeny"] = self.allow_deny
        if self.disabled:
            result["disabled"] = self.disabled
        return result


# ---------------------------------------------------------------------------
# MatchRules type alias and deserialization
# ---------------------------------------------------------------------------

# MatchRules is a list of match-rule objects of varying types.
MatchRules = list

# Map from match rule type string to Python dataclass.
# Mirrors Go matchRuleHandlers from match_rule.go.
_MATCH_RULE_HANDLERS: dict[str, type] = {
    "apMatchRule": MatchRuleAP,
    "asMatchRule": MatchRuleAS,
    "cdMatchRule": MatchRulePR,
    "erMatchRule": MatchRuleER,
    "frMatchRule": MatchRuleFR,
    "igMatchRule": MatchRuleRC,
}


def deserialize_match_rules(data: list | None) -> list | None:
    """Deserialize a JSON array of match rule dicts into typed objects.

    Inspects each element's ``"type"`` field and dispatches to the
    corresponding match rule class.  Mirrors Go ``UnmarshalJSON`` on
    ``MatchRules`` from match_rule.go.

    Args:
        data: List of raw match rule dicts from a JSON response, or
              *None*.

    Returns:
        List of typed match rule instances (e.g. :class:`MatchRuleAP`,
        :class:`MatchRuleER`, …), or *None* when *data* is *None*.

    Raises:
        ValueError: If a match rule dict contains an unrecognised
            ``"type"`` value, a non-string type, or a missing type.
    """
    if data is None:
        return None
    if not isinstance(data, list):
        raise ValueError(
            "unmarshalling MatchRules: expected a list"
        )
    result: list = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError(
                "unmarshalling MatchRules: "
                "match rule entry should be an object"
            )
        if "type" not in item:
            raise ValueError(
                "unmarshalling MatchRules: "
                "match rule entry should contain 'type' field"
            )
        rule_type = item["type"]
        if not isinstance(rule_type, str):
            raise ValueError(
                "unmarshalling MatchRules: "
                "'type' field on match rule entry should be a string"
            )
        handler = _MATCH_RULE_HANDLERS.get(rule_type)
        if handler is None:
            raise ValueError(
                "unmarshalling MatchRules: "
                f"unsupported match rule type: {rule_type}"
            )
        result.append(handler.from_dict(item))
    return result if result else None
