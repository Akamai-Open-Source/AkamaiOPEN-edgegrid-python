"""Akamai Hostname API (HAPI) client package.

Provides access to the Akamai Edge Hostnames APIs for managing
edge hostnames, change requests, and certificates.

See: https://techdocs.akamai.com/edge-hostnames/reference/api
"""

from .hapi import HapiClient
from .models import (
    GetChangeRequestRequest,
    ChangeRequest,
    DeleteEdgeHostnameRequest,
    DeleteEdgeHostnameResponse,
    UpdateEdgeHostnameRequest,
    UpdateEdgeHostnameRequestBody,
    UpdateEdgeHostnameResponse,
    EdgeHostname,
    ChinaCDN,
    UseCase,
    GetEdgeHostnameResponse,
    GetCertificateRequest,
    GetCertificateResponse,
)
from .errors import (
    Error,
    ErrorItem,
    ErrGetChangeRequest,
    ErrDeleteEdgeHostname,
    ErrGetEdgeHostname,
    ErrUpdateEdgeHostname,
    ErrGetCertificate,
    ErrNotFound,
)

__all__ = [
    # Client
    "HapiClient",
    # Models
    "GetChangeRequestRequest",
    "ChangeRequest",
    "DeleteEdgeHostnameRequest",
    "DeleteEdgeHostnameResponse",
    "UpdateEdgeHostnameRequest",
    "UpdateEdgeHostnameRequestBody",
    "UpdateEdgeHostnameResponse",
    "EdgeHostname",
    "ChinaCDN",
    "UseCase",
    "GetEdgeHostnameResponse",
    "GetCertificateRequest",
    "GetCertificateResponse",
    # Errors
    "Error",
    "ErrorItem",
    "ErrGetChangeRequest",
    "ErrDeleteEdgeHostname",
    "ErrGetEdgeHostname",
    "ErrUpdateEdgeHostname",
    "ErrGetCertificate",
    "ErrNotFound",
]
