"""Akamai Application Security API client package.

Provides a Python client for the Akamai Application Security API,
mirroring the Go v12 pkg/appsec package.
"""

from akamai.edgegrid.appsec.appsec import Client
from akamai.edgegrid.appsec.errors import (
    Error,
    ErrBadRequest,
)

__all__ = [
    "Client",
    "Error",
    "ErrBadRequest",
]
