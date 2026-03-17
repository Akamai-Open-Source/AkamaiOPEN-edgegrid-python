"""Akamai Hostname API (HAPI) client implementation.

Provides the HapiClient class with methods for managing edge hostnames,
change requests, and certificates through the Akamai HAPI service.

Mirrors Go pkg/hapi: hapi.go (interface + constructor), change_requests.go
(GetChangeRequest), and edgehostname.go (DeleteEdgeHostname, GetEdgeHostname,
UpdateEdgeHostname, GetCertificate).

See: https://techdocs.akamai.com/edge-hostnames/reference/api
"""

import json
import logging

from akamai.edgegrid.session import Session
from akamai.edgegrid.errors import ErrStructValidation
from akamai.edgegrid.hapi import models
from akamai.edgegrid.hapi import errors
from akamai.edgegrid.hapi import validation

logger = logging.getLogger(__name__)


class HapiClient:
    """Client for the Akamai Hostname API (HAPI).

    Provides access to the Akamai Edge Hostnames APIs for managing
    edge hostnames, change requests, and certificates.

    Implements exactly 5 endpoint methods mirroring the Go pkg/hapi.HAPI
    interface:
    1. GetChangeRequest  — GET    /hapi/v1/change-requests/{ChangeID}
    2. DeleteEdgeHostname — DELETE /hapi/v1/dns-zones/{zone}/edge-hostnames/{record}
    3. GetEdgeHostname    — GET    /hapi/v1/edge-hostnames/{id}
    4. UpdateEdgeHostname — PATCH  /hapi/v1/dns-zones/{zone}/edge-hostnames/{record}
    5. GetCertificate     — GET    /hapi/v1/dns-zones/{zone}/edge-hostnames/{record}/certificate

    Mirrors Go pkg/hapi.hapi struct embedding session.Session.

    See: https://techdocs.akamai.com/edge-hostnames/reference/api
    """

    def __init__(self, session: Session):
        """Initialize HAPI client.

        Mirrors Go hapi.Client(sess session.Session, opts ...Option) HAPI.

        :param session: Authenticated Akamai API session providing
            signed HTTP request execution via EdgeGridAuth.
        """
        self._session = session

    def get_change_request(
        self, params: models.GetChangeRequestRequest
    ) -> models.ChangeRequest:
        """Request status and details for a change specified by change ID.

        Mirrors Go hapi.GetChangeRequest (change_requests.go lines 37-60).
        See: https://techdocs.akamai.com/edge-hostnames/reference/get-changeid

        :param params: Request containing the ChangeID to look up.
        :returns: ChangeRequest with status and details of the change.
        :raises errors._SentinelError: With ErrGetChangeRequest message when
            the API request fails (wraps the HAPI Error).
        """
        logger.debug("GetChangeRequest")

        uri = f"/hapi/v1/change-requests/{params.change_id}"

        try:
            _, result = self._session.exec(
                "GET", uri,
                expect_json=True,
                error_parser=errors.parse_hapi_error,
            )
        except errors.Error as err:
            raise type(errors.ErrGetChangeRequest)(
                f"{errors.ErrGetChangeRequest}: {err}"
            ) from err
        except Exception as err:
            raise type(errors.ErrGetChangeRequest)(
                f"{errors.ErrGetChangeRequest}: {err}"
            ) from err

        return models.ChangeRequest.from_dict(result)

    def delete_edge_hostname(
        self, params: models.DeleteEdgeHostnameRequest
    ) -> models.DeleteEdgeHostnameResponse:
        """Delete a specific edge hostname.

        You must have an Admin or Technical role.  You can delete any
        hostname that is not currently part of an active Property Manager
        configuration.

        Mirrors Go hapi.DeleteEdgeHostname (edgehostname.go lines 198-239).
        See: https://techdocs.akamai.com/edge-hostnames/reference/delete-edgehostname

        :param params: Request with DNSZone, RecordName, and optional
            StatusUpdateEmail and Comments.
        :returns: DeleteEdgeHostnameResponse with change details.
        :raises ErrStructValidation: When request validation fails before
            any HTTP request is made.
        :raises errors._SentinelError: With ErrDeleteEdgeHostname message
            when the API request fails.
        """
        logger.debug("DeleteEdgeHostname")

        # Validate request — mirrors Go line 202
        validation_error = validation.validate_delete_edge_hostname_request(
            params
        )
        if validation_error is not None:
            raise ErrStructValidation(
                f"{errors.ErrDeleteEdgeHostname}: struct validation: "
                f"{validation_error}"
            )

        uri = (
            f"/hapi/v1/dns-zones/{params.dns_zone}"
            f"/edge-hostnames/{params.record_name}"
        )

        # Build query parameters — mirrors Go lines 216-224
        query_params: dict[str, str] = {}
        if params.status_update_email:
            query_params["statusUpdateEmail"] = ",".join(
                params.status_update_email
            )
        if params.comments:
            query_params["comments"] = params.comments

        try:
            _, result = self._session.exec(
                "DELETE", uri,
                params=query_params if query_params else None,
                expect_json=True,
                error_parser=errors.parse_hapi_error,
            )
        except errors.Error as err:
            raise type(errors.ErrDeleteEdgeHostname)(
                f"{errors.ErrDeleteEdgeHostname}: {err}"
            ) from err
        except Exception as err:
            raise type(errors.ErrDeleteEdgeHostname)(
                f"{errors.ErrDeleteEdgeHostname}: {err}"
            ) from err

        return models.DeleteEdgeHostnameResponse.from_dict(result)

    def get_edge_hostname(
        self, edge_hostname_id: int
    ) -> models.GetEdgeHostnameResponse:
        """Get details for a specific edge hostname.

        Includes product ID, IP version behavior, and China CDN or
        Edge IP Binding status.

        Mirrors Go hapi.GetEdgeHostname (edgehostname.go lines 241-264).
        Note: Takes a raw integer parameter, not a request struct.
        See: https://techdocs.akamai.com/edge-hostnames/reference/get-edgehostnameid

        :param edge_hostname_id: The unique identifier of the edge hostname.
        :returns: GetEdgeHostnameResponse with hostname details including
            product ID, IP version behavior, and security information.
        :raises errors._SentinelError: With ErrGetEdgeHostname message when
            the API request fails.
        """
        logger.debug("GetEdgeHostname")

        uri = f"/hapi/v1/edge-hostnames/{edge_hostname_id}"

        try:
            _, result = self._session.exec(
                "GET", uri,
                expect_json=True,
                error_parser=errors.parse_hapi_error,
            )
        except errors.Error as err:
            raise type(errors.ErrGetEdgeHostname)(
                f"{errors.ErrGetEdgeHostname}: {err}"
            ) from err
        except Exception as err:
            raise type(errors.ErrGetEdgeHostname)(
                f"{errors.ErrGetEdgeHostname}: {err}"
            ) from err

        return models.GetEdgeHostnameResponse.from_dict(result)

    def update_edge_hostname(
        self, request: models.UpdateEdgeHostnameRequest
    ) -> models.UpdateEdgeHostnameResponse:
        """Update edge hostname TTL or IP version behavior via JSON Patch.

        Submits a JSON Patch (RFC 6902) document to modify an edge hostname.
        The Content-Type is set to application/json-patch+json as required
        by the API.

        Mirrors Go hapi.UpdateEdgeHostname (edgehostname.go lines 266-311).
        See: https://techdocs.akamai.com/edge-hostnames/reference/patch-edgehostnames

        :param request: Request with DNSZone, RecordName, Body containing
            JSON Patch operations, and optional StatusUpdateEmail and Comments.
        :returns: UpdateEdgeHostnameResponse with change details.
        :raises ErrStructValidation: When request validation fails before
            any HTTP request is made.
        :raises errors._SentinelError: With ErrUpdateEdgeHostname message
            when the API request fails.
        """
        logger.debug("UpdateEdgeHostname")

        # Validate request — mirrors Go line 270-272
        validation_error = validation.validate_update_edge_hostname_request(
            request
        )
        if validation_error is not None:
            raise ErrStructValidation(
                f"{errors.ErrUpdateEdgeHostname}: struct validation: "
                f"{validation_error}"
            )

        uri = (
            f"/hapi/v1/dns-zones/{request.dns_zone}"
            f"/edge-hostnames/{request.record_name}"
        )

        # Build JSON Patch body — mirrors Go buildBody (lines 349-355).
        # Pre-serialize to JSON string since Content-Type is
        # application/json-patch+json (not application/json). Session
        # will send the string body as-is.
        body_data = [
            {"op": b.op, "path": b.path, "value": b.value}
            for b in request.body
        ]
        body = json.dumps(body_data)

        # Build query parameters — mirrors Go lines 286-294
        query_params: dict[str, str] = {}
        if request.status_update_email:
            query_params["statusUpdateEmail"] = ",".join(
                request.status_update_email
            )
        if request.comments:
            query_params["comments"] = request.comments

        # Set Content-Type to application/json-patch+json — Go line 296
        headers = {"Content-Type": "application/json-patch+json"}

        try:
            _, result = self._session.exec(
                "PATCH", uri,
                body=body,
                params=query_params if query_params else None,
                expect_json=True,
                headers=headers,
                error_parser=errors.parse_hapi_error,
            )
        except errors.Error as err:
            raise type(errors.ErrUpdateEdgeHostname)(
                f"{errors.ErrUpdateEdgeHostname}: {err}"
            ) from err
        except Exception as err:
            raise type(errors.ErrUpdateEdgeHostname)(
                f"{errors.ErrUpdateEdgeHostname}: {err}"
            ) from err

        return models.UpdateEdgeHostnameResponse.from_dict(result)

    def get_certificate(
        self, params: models.GetCertificateRequest
    ) -> models.GetCertificateResponse:
        """Get the certificate associated with an enhanced TLS edge hostname.

        Mirrors Go hapi.GetCertificate (edgehostname.go lines 313-347).
        Handles 404 responses as a distinct ErrNotFound condition.
        See: https://techdocs.akamai.com/edge-hostnames/reference/get-edge-hostname-certificate

        :param params: Request with DNSZone and RecordName identifying the
            edge hostname whose certificate to retrieve.
        :returns: GetCertificateResponse with certificate details.
        :raises ErrStructValidation: When request validation fails before
            any HTTP request is made.
        :raises errors._SentinelError: With ErrGetCertificate message when
            the API request fails, or ErrNotFound for 404 responses.
        """
        logger.debug("GetCertificate")

        # Validate request — mirrors Go line 317-319
        validation_error = validation.validate_get_certificate_request(params)
        if validation_error is not None:
            raise ErrStructValidation(
                f"{errors.ErrGetCertificate}: struct validation: "
                f"{validation_error}"
            )

        uri = (
            f"/hapi/v1/dns-zones/{params.dns_zone}"
            f"/edge-hostnames/{params.record_name}/certificate"
        )

        try:
            _, result = self._session.exec(
                "GET", uri,
                expect_json=True,
                error_parser=errors.parse_hapi_error,
            )
        except errors.Error as err:
            # Handle 404 as ErrNotFound — mirrors Go lines 339-341:
            # fmt.Errorf("%s: %s: %w", ErrGetCertificate, ErrNotFound,
            #            h.Error(resp))
            if err.status == 404:
                raise type(errors.ErrGetCertificate)(
                    f"{errors.ErrGetCertificate}: "
                    f"{errors.ErrNotFound}: {err}"
                ) from err
            raise type(errors.ErrGetCertificate)(
                f"{errors.ErrGetCertificate}: {err}"
            ) from err
        except Exception as err:
            raise type(errors.ErrGetCertificate)(
                f"{errors.ErrGetCertificate}: {err}"
            ) from err

        return models.GetCertificateResponse.from_dict(result)
