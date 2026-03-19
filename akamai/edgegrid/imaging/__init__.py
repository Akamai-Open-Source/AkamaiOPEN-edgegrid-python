"""Akamai Image & Video Manager API client package"""

from akamai.edgegrid.imaging.imaging import (
    Client,
    ERR_LIST_POLICIES,
    ERR_GET_POLICY,
    ERR_UPSERT_POLICY,
    ERR_DELETE_POLICY,
    ERR_GET_POLICY_HISTORY,
    ERR_ROLLBACK_POLICY,
    ERR_LIST_POLICY_SETS,
    ERR_GET_POLICY_SET,
    ERR_CREATE_POLICY_SET,
    ERR_UPDATE_POLICY_SET,
    ERR_DELETE_POLICY_SET,
)
from akamai.edgegrid.imaging.errors import Error
from akamai.edgegrid.imaging.models import (
    # Policy request/response types
    ListPoliciesRequest,
    ListPoliciesResponse,
    GetPolicyRequest,
    UpsertPolicyRequest,
    DeletePolicyRequest,
    GetPolicyHistoryRequest,
    GetPolicyHistoryResponse,
    RollbackPolicyRequest,
    PolicyResponse,
    PolicyHistoryItem,
    # PolicySet request/response types
    ListPolicySetsRequest,
    GetPolicySetRequest,
    CreatePolicySetRequest,
    UpdatePolicySetRequest,
    DeletePolicySetRequest,
    PolicySet,
    # Policy input/output types
    PolicyInputImage,
    PolicyInputVideo,
    PolicyOutputImage,
    PolicyOutputVideo,
    # Network constants
    POLICY_NETWORK_STAGING,
    POLICY_NETWORK_PRODUCTION,
    NETWORK_STAGING,
    NETWORK_PRODUCTION,
    NETWORK_BOTH,
    # Region constants
    REGION_US,
    REGION_EMEA,
    REGION_ASIA,
    REGION_AUSTRALIA,
    REGION_JAPAN,
    REGION_CHINA,
    # MediaType constants
    TYPE_IMAGE,
    TYPE_VIDEO,
)

__all__ = [
    # Client
    "Client",
    # Error
    "Error",
    # Policy request/response types
    "ListPoliciesRequest",
    "ListPoliciesResponse",
    "GetPolicyRequest",
    "UpsertPolicyRequest",
    "DeletePolicyRequest",
    "GetPolicyHistoryRequest",
    "GetPolicyHistoryResponse",
    "RollbackPolicyRequest",
    "PolicyResponse",
    "PolicyHistoryItem",
    # PolicySet request/response types
    "ListPolicySetsRequest",
    "GetPolicySetRequest",
    "CreatePolicySetRequest",
    "UpdatePolicySetRequest",
    "DeletePolicySetRequest",
    "PolicySet",
    # Policy input/output types
    "PolicyInputImage",
    "PolicyInputVideo",
    "PolicyOutputImage",
    "PolicyOutputVideo",
    # Network constants
    "POLICY_NETWORK_STAGING",
    "POLICY_NETWORK_PRODUCTION",
    "NETWORK_STAGING",
    "NETWORK_PRODUCTION",
    "NETWORK_BOTH",
    # Region constants
    "REGION_US",
    "REGION_EMEA",
    "REGION_ASIA",
    "REGION_AUSTRALIA",
    "REGION_JAPAN",
    "REGION_CHINA",
    # MediaType constants
    "TYPE_IMAGE",
    "TYPE_VIDEO",
    # Sentinel errors
    "ERR_LIST_POLICIES",
    "ERR_GET_POLICY",
    "ERR_UPSERT_POLICY",
    "ERR_DELETE_POLICY",
    "ERR_GET_POLICY_HISTORY",
    "ERR_ROLLBACK_POLICY",
    "ERR_LIST_POLICY_SETS",
    "ERR_GET_POLICY_SET",
    "ERR_CREATE_POLICY_SET",
    "ERR_UPDATE_POLICY_SET",
    "ERR_DELETE_POLICY_SET",
]
