"""mTLS Trust Store API client — mirrors Go ``MTLSTruststore`` interface."""

import json
import logging
from email.utils import parsedate_to_datetime

from akamai.edgegrid.session import Session
from akamai.edgegrid.utils import unescape_content
from akamai.edgegrid.mtlstruststore import models
from akamai.edgegrid.mtlstruststore import errors
from akamai.edgegrid.mtlstruststore import validation

logger = logging.getLogger(__name__)


class Client:
    """mTLS Trust Store API client for CA sets, versions, activations, and certificates."""

    def __init__(self, session: Session):
        """Initialize with an authenticated :class:`Session`."""
        self._session = session

    def create_ca_set(
        self,
        params: models.CreateCASetRequest,
    ) -> models.CreateCASetResponse:
        """POST /mtls-edge-truststore/v2/ca-sets — create a new CA set."""
        logger.debug("CreateCASet")

        validation_error = validation.validate_create_ca_set_request(params)
        if validation_error is not None:
            raise errors.Error(
                title=f"{errors.ErrCreateCASet}",
                detail=f"{errors.ErrStructValidation}: {validation_error}",
            )

        path = "/mtls-edge-truststore/v2/ca-sets"
        body = params.to_dict()

        response, result = self._session.exec(
            "POST", path, body=body, expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 201:
            raise self._parse_error(response)

        return models.CreateCASetResponse.from_dict(result)

    def get_ca_set(
        self,
        params: models.GetCASetRequest,
    ) -> models.GetCASetResponse:
        """GET /mtls-edge-truststore/v2/ca-sets/{caSetId} — get a CA set."""
        logger.debug("GetCASet")

        validation_error = validation.validate_get_ca_set_request(params)
        if validation_error is not None:
            raise errors.Error(
                title=f"{errors.ErrGetCASet}",
                detail=f"{errors.ErrStructValidation}: {validation_error}",
            )

        path = (
            f"/mtls-edge-truststore/v2/ca-sets/{params.ca_set_id}"
        )

        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise self._parse_error(response)

        return models.GetCASetResponse.from_dict(result)

    def list_ca_sets(
        self,
        params: models.ListCASetsRequest,
    ) -> models.ListCASetsResponse:
        """GET /mtls-edge-truststore/v2/ca-sets — list CA sets."""
        logger.debug("ListCASets")

        validation_error = validation.validate_list_ca_sets_request(params)
        if validation_error is not None:
            raise errors.Error(
                title=f"{errors.ErrListCASets}",
                detail=f"{errors.ErrStructValidation}: {validation_error}",
            )

        path = "/mtls-edge-truststore/v2/ca-sets"
        query_params: dict[str, str] = {}
        if params.ca_set_name_prefix:
            query_params["caSetNamePrefix"] = params.ca_set_name_prefix
        if params.activated_on:
            query_params["activatedOn"] = params.activated_on

        response, result = self._session.exec(
            "GET", path, expect_json=True,
            params=query_params or None,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise self._parse_error(response)

        return models.ListCASetsResponse.from_dict(result)

    def delete_ca_set(
        self,
        params: models.DeleteCASetRequest,
    ) -> None:
        """DELETE /mtls-edge-truststore/v2/ca-sets/{caSetId} — delete a CA set."""
        logger.debug("DeleteCASet")

        validation_error = validation.validate_delete_ca_set_request(params)
        if validation_error is not None:
            raise errors.Error(
                title=f"{errors.ErrDeleteCASet}",
                detail=f"{errors.ErrStructValidation}: {validation_error}",
            )

        path = (
            f"/mtls-edge-truststore/v2/ca-sets/{params.ca_set_id}"
        )

        response, _ = self._session.exec(
            "DELETE", path,
            error_parser=self._parse_error,
        )

        if response.status_code != 202:
            raise self._parse_error(response)

    def list_ca_set_associations(
        self,
        params: models.ListCASetAssociationsRequest,
    ) -> models.ListCASetAssociationsResponse:
        """GET …/{caSetId}/associations — list CA set associations."""
        logger.debug("ListCASetAssociations")

        validation_error = (
            validation.validate_list_ca_set_associations_request(params)
        )
        if validation_error is not None:
            raise errors.Error(
                title=f"{errors.ErrListCASetAssociations}",
                detail=f"{errors.ErrStructValidation}: {validation_error}",
            )

        path = (
            f"/mtls-edge-truststore/v2/ca-sets/"
            f"{params.ca_set_id}/associations"
        )
        query_params: dict[str, str] = {}
        if params.association_type:
            query_params["associationType"] = params.association_type

        response, result = self._session.exec(
            "GET", path, expect_json=True,
            params=query_params or None,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise self._parse_error(response)

        return models.ListCASetAssociationsResponse.from_dict(result)

    def clone_ca_set(
        self,
        params: models.CloneCASetRequest,
    ) -> models.CloneCASetResponse:
        """POST …/{cloneFromSetId}/clone — clone a CA set."""
        logger.debug("CloneCASet")

        validation_error = validation.validate_clone_ca_set_request(params)
        if validation_error is not None:
            raise errors.Error(
                title=f"{errors.ErrCloneCASet}",
                detail=f"{errors.ErrStructValidation}: {validation_error}",
            )

        path = (
            f"/mtls-edge-truststore/v2/ca-sets/"
            f"{params.clone_from_set_id}/clone"
        )
        query_params: dict[str, str] = {}
        if params.clone_from_version != 0:
            query_params["cloneFromVersion"] = str(
                params.clone_from_version
            )

        body = params.to_dict()

        response, result = self._session.exec(
            "POST", path, body=body, expect_json=True,
            params=query_params or None,
            error_parser=self._parse_error,
        )

        if response.status_code != 201:
            raise self._parse_error(response)

        return models.CloneCASetResponse.from_dict(result)

    def get_ca_set_deletion_status(
        self,
        params: models.GetCASetDeletionStatusRequest,
    ) -> models.GetCASetDeletionStatusResponse:
        """GET …/{caSetId}/status/delete — get deletion status (parses Retry-After)."""
        logger.debug("GetCASetDeletionStatus")

        validation_error = (
            validation.validate_get_ca_set_deletion_status_request(params)
        )
        if validation_error is not None:
            raise errors.Error(
                title=f"{errors.ErrGetCASetDeletionStatus}",
                detail=f"{errors.ErrStructValidation}: {validation_error}",
            )

        path = (
            f"/mtls-edge-truststore/v2/ca-sets/"
            f"{params.ca_set_id}/status/delete"
        )

        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code not in (200, 202, 207):
            raise self._parse_error(response)

        parsed = models.GetCASetDeletionStatusResponse.from_dict(result)

        retry_after_header = response.headers.get("Retry-After", "")
        if retry_after_header:
            try:
                after = parsedate_to_datetime(retry_after_header)
                parsed.retry_after = after.isoformat()
            except (ValueError, TypeError) as err:
                raise errors.Error(
                    title=f"{errors.ErrGetCASetDeletionStatus}",
                    detail=(
                        f"failed to parse Retry-After header: {err}"
                    ),
                ) from err

        return parsed

    def list_ca_set_activities(
        self,
        params: models.ListCASetActivitiesRequest,
    ) -> models.ListCASetActivitiesResponse:
        """GET …/{caSetId}/activities — list CA set activities."""
        logger.debug("ListCASetActivities")

        validation_error = (
            validation.validate_list_ca_set_activities_request(params)
        )
        if validation_error is not None:
            raise errors.Error(
                title=f"{errors.ErrListCASetActivities}",
                detail=f"{errors.ErrStructValidation}: {validation_error}",
            )

        path = (
            f"/mtls-edge-truststore/v2/ca-sets/"
            f"{params.ca_set_id}/activities"
        )
        query_params: dict[str, str] = {}
        if params.start:
            query_params["start"] = params.start
        if params.end:
            query_params["end"] = params.end

        response, result = self._session.exec(
            "GET", path, expect_json=True,
            params=query_params or None,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise self._parse_error(response)

        return models.ListCASetActivitiesResponse.from_dict(result)

    def create_ca_set_version(
        self,
        params: models.CreateCASetVersionRequest,
    ) -> models.CreateCASetVersionResponse:
        """POST …/{caSetId}/versions — create a new CA set version."""
        logger.debug("CreateCASetVersion")

        validation_error = (
            validation.validate_create_ca_set_version_request(params)
        )
        if validation_error is not None:
            raise errors.Error(
                title=f"{errors.ErrCreateCASetVersion}",
                detail=f"{errors.ErrStructValidation}: {validation_error}",
            )

        path = (
            f"/mtls-edge-truststore/v2/ca-sets/"
            f"{params.ca_set_id}/versions"
        )
        body = params.body.to_dict() if params.body is not None else {}

        response, result = self._session.exec(
            "POST", path, body=body, expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 201:
            raise self._parse_error(response)

        return models.CreateCASetVersionResponse.from_dict(result)

    def clone_ca_set_version(
        self,
        params: models.CloneCASetVersionRequest,
    ) -> models.CloneCASetVersionResponse:
        """POST …/{caSetId}/versions/{version}/clone — clone a version."""
        logger.debug("CloneCASetVersion")

        validation_error = (
            validation.validate_clone_ca_set_version_request(params)
        )
        if validation_error is not None:
            raise errors.Error(
                title=f"{errors.ErrCloneCASetVersion}",
                detail=f"{errors.ErrStructValidation}: {validation_error}",
            )

        path = (
            f"/mtls-edge-truststore/v2/ca-sets/"
            f"{params.ca_set_id}/versions/{params.version}/clone"
        )

        response, result = self._session.exec(
            "POST", path, expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 201:
            raise self._parse_error(response)

        return models.CloneCASetVersionResponse.from_dict(result)

    def get_ca_set_version(
        self,
        params: models.GetCASetVersionRequest,
    ) -> models.GetCASetVersionResponse:
        """GET …/{caSetId}/versions/{version} — get a CA set version."""
        logger.debug("GetCASetVersion")

        validation_error = (
            validation.validate_get_ca_set_version_request(params)
        )
        if validation_error is not None:
            raise errors.Error(
                title=f"{errors.ErrGetCASetVersion}",
                detail=f"{errors.ErrStructValidation}: {validation_error}",
            )

        path = (
            f"/mtls-edge-truststore/v2/ca-sets/"
            f"{params.ca_set_id}/versions/{params.version}"
        )

        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise self._parse_error(response)

        return models.GetCASetVersionResponse.from_dict(result)

    def list_ca_set_versions(
        self,
        params: models.ListCASetVersionsRequest,
    ) -> models.ListCASetVersionsResponse:
        """GET …/{caSetId}/versions — list CA set versions."""
        logger.debug("ListCASetVersions")

        validation_error = (
            validation.validate_list_ca_set_versions_request(params)
        )
        if validation_error is not None:
            raise errors.Error(
                title=f"{errors.ErrListCASetVersions}",
                detail=f"{errors.ErrStructValidation}: {validation_error}",
            )

        path = (
            f"/mtls-edge-truststore/v2/ca-sets/"
            f"{params.ca_set_id}/versions"
        )
        query_params: dict[str, str] = {}
        if params.include_certificates:
            query_params["includeCertificates"] = str(
                params.include_certificates
            ).lower()
        if params.active_versions_only:
            query_params["activeVersionsOnly"] = str(
                params.active_versions_only
            ).lower()

        response, result = self._session.exec(
            "GET", path, expect_json=True,
            params=query_params or None,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise self._parse_error(response)

        return models.ListCASetVersionsResponse.from_dict(result)

    def get_ca_set_version_certificates(
        self,
        params: models.GetCASetVersionCertificatesRequest,
    ) -> models.GetCASetVersionCertificatesResponse:
        """GET …/{caSetId}/versions/{version}/certificates — get version certs."""
        logger.debug("GetCASetVersionCertificates")

        validation_error = (
            validation.validate_get_ca_set_version_certificates_request(
                params,
            )
        )
        if validation_error is not None:
            raise errors.Error(
                title=f"{errors.ErrGetCASetVersionCertificates}",
                detail=f"{errors.ErrStructValidation}: {validation_error}",
            )

        path = (
            f"/mtls-edge-truststore/v2/ca-sets/"
            f"{params.ca_set_id}/versions/"
            f"{params.version}/certificates"
        )
        query_params: dict[str, str] = {}
        if params.certificate_status is not None:
            query_params["certificateStatus"] = params.certificate_status
        if params.expiry_threshold_in_days is not None:
            query_params["expiryThresholdInDays"] = str(
                params.expiry_threshold_in_days
            )
        if params.expiry_threshold_timestamp:
            query_params["expiryThresholdTimestamp"] = (
                params.expiry_threshold_timestamp
            )

        response, result = self._session.exec(
            "GET", path, expect_json=True,
            params=query_params or None,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise self._parse_error(response)

        return models.GetCASetVersionCertificatesResponse.from_dict(result)

    def update_ca_set_version(
        self,
        params: models.UpdateCASetVersionRequest,
    ) -> models.UpdateCASetVersionResponse:
        """PUT …/{caSetId}/versions/{version} — update a CA set version."""
        logger.debug("UpdateCASetVersion")

        validation_error = (
            validation.validate_update_ca_set_version_request(params)
        )
        if validation_error is not None:
            raise errors.Error(
                title=f"{errors.ErrUpdateCASetVersion}",
                detail=f"{errors.ErrStructValidation}: {validation_error}",
            )

        path = (
            f"/mtls-edge-truststore/v2/ca-sets/"
            f"{params.ca_set_id}/versions/{params.version}"
        )
        body = params.body.to_dict() if params.body is not None else {}

        response, result = self._session.exec(
            "PUT", path, body=body, expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise self._parse_error(response)

        return models.UpdateCASetVersionResponse.from_dict(result)

    def activate_ca_set_version(
        self,
        params: models.ActivateCASetVersionRequest,
    ) -> models.ActivateCASetVersionResponse:
        """POST …/{version}/activate — activate a CA set version."""
        logger.debug("ActivateCASetVersion")

        validation_error = (
            validation.validate_activate_ca_set_version_request(params)
        )
        if validation_error is not None:
            raise errors.Error(
                title=f"{errors.ErrActivateCASetVersion}",
                detail=f"{errors.ErrStructValidation}: {validation_error}",
            )

        path = (
            f"/mtls-edge-truststore/v2/ca-sets/"
            f"{params.ca_set_id}/versions/"
            f"{params.version}/activate"
        )
        body = params.to_dict()

        response, result = self._session.exec(
            "POST", path, body=body, expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 202:
            raise self._parse_error(response)

        return models.ActivateCASetVersionResponse.from_dict(result)

    def deactivate_ca_set_version(
        self,
        params: models.DeactivateCASetVersionRequest,
    ) -> models.DeactivateCASetVersionResponse:
        """POST …/{version}/deactivate — deactivate a CA set version."""
        logger.debug("DeactivateCASetVersion")

        validation_error = (
            validation.validate_deactivate_ca_set_version_request(params)
        )
        if validation_error is not None:
            raise errors.Error(
                title=f"{errors.ErrDeactivateCASetVersion}",
                detail=f"{errors.ErrStructValidation}: {validation_error}",
            )

        path = (
            f"/mtls-edge-truststore/v2/ca-sets/"
            f"{params.ca_set_id}/versions/"
            f"{params.version}/deactivate"
        )
        body = params.to_dict()

        response, result = self._session.exec(
            "POST", path, body=body, expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 202:
            raise self._parse_error(response)

        return models.DeactivateCASetVersionResponse.from_dict(result)

    def get_ca_set_version_activation(
        self,
        params: models.GetCASetVersionActivationRequest,
    ) -> models.GetCASetVersionActivationResponse:
        """GET …/activations/{activationId} — get activation (parses Retry-After)."""
        logger.debug("GetCASetVersionActivation")

        validation_error = (
            validation.validate_get_ca_set_version_activation_request(
                params,
            )
        )
        if validation_error is not None:
            raise errors.Error(
                title=f"{errors.ErrGetCASetVersionActivation}",
                detail=f"{errors.ErrStructValidation}: {validation_error}",
            )

        path = (
            f"/mtls-edge-truststore/v2/ca-sets/"
            f"{params.ca_set_id}/versions/"
            f"{params.version}/activations/"
            f"{params.activation_id}"
        )

        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code not in (200, 202):
            raise self._parse_error(response)

        parsed = models.GetCASetVersionActivationResponse.from_dict(result)

        retry_after_header = response.headers.get("Retry-After", "")
        if retry_after_header:
            try:
                after = parsedate_to_datetime(retry_after_header)
                parsed.retry_after = after.isoformat()
            except (ValueError, TypeError) as err:
                raise errors.Error(
                    title=f"{errors.ErrGetCASetVersionActivation}",
                    detail=(
                        f"failed to parse Retry-After header: {err}"
                    ),
                ) from err

        return parsed

    def list_ca_set_version_activations(
        self,
        params: models.ListCASetVersionActivationsRequest,
    ) -> models.ListCASetVersionActivationsResponse:
        """GET …/{version}/activations — list version activations."""
        logger.debug("ListCASetVersionActivations")

        validation_error = (
            validation.validate_list_ca_set_version_activations_request(
                params,
            )
        )
        if validation_error is not None:
            raise errors.Error(
                title=f"{errors.ErrListCASetVersionActivations}",
                detail=f"{errors.ErrStructValidation}: {validation_error}",
            )

        path = (
            f"/mtls-edge-truststore/v2/ca-sets/"
            f"{params.ca_set_id}/versions/"
            f"{params.version}/activations"
        )

        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise self._parse_error(response)

        return models.ListCASetVersionActivationsResponse.from_dict(result)

    def list_ca_set_activations(
        self,
        params: models.ListCASetActivationsRequest,
    ) -> models.ListCASetActivationsResponse:
        """GET …/{caSetId}/activations — list all CA set activations."""
        logger.debug("ListCASetActivations")

        validation_error = (
            validation.validate_list_ca_set_activations_request(params)
        )
        if validation_error is not None:
            raise errors.Error(
                title=f"{errors.ErrListCASetActivations}",
                detail=f"{errors.ErrStructValidation}: {validation_error}",
            )

        path = (
            f"/mtls-edge-truststore/v2/ca-sets/"
            f"{params.ca_set_id}/activations"
        )

        response, result = self._session.exec(
            "GET", path, expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise self._parse_error(response)

        return models.ListCASetActivationsResponse.from_dict(result)

    def validate_certificates(
        self,
        params: models.ValidateCertificatesRequest,
    ) -> models.ValidateCertificatesResponse:
        """POST /mtls-edge-truststore/v2/certificates/validate — validate certs."""
        logger.debug("ValidateCertificates")

        validation_error = (
            validation.validate_validate_certificates_request(params)
        )
        if validation_error is not None:
            raise errors.Error(
                title=f"{errors.ErrValidateCertificates}",
                detail=f"{errors.ErrStructValidation}: {validation_error}",
            )

        path = "/mtls-edge-truststore/v2/certificates/validate"
        body = params.to_dict()

        response, result = self._session.exec(
            "POST", path, body=body, expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise self._parse_error(response)

        return models.ValidateCertificatesResponse.from_dict(result)

    def _parse_error(self, response) -> errors.Error:
        """Parse an RFC 7807 error from *response*, falling back to plain text."""
        error = errors.Error()

        try:
            body = response.text
        except Exception as err:  # pylint: disable=broad-except
            logger.error("reading error response body: %s", err)
            error.status = response.status_code
            error.title = "Failed to read error body"
            error.detail = str(err)
            return error

        try:
            data = json.loads(body)
            error.type = data.get("type", "")
            error.title = data.get("title", "")
            error.detail = data.get("detail", "")
            error.instance = data.get("instance", "")
            error.context_info = data.get("contextInfo")
            error.pointer = data.get("pointer", "")
            error.status = data.get("status", 0)

            raw_errors = data.get("errors")
            if raw_errors and isinstance(raw_errors, list):
                error.errors = []
                for item in raw_errors:
                    error.errors.append(errors.ErrorItem(
                        detail=item.get("detail", ""),
                        pointer=item.get("pointer", ""),
                        context_info=item.get("contextInfo"),
                        title=item.get("title", ""),
                        type=item.get("type", ""),
                    ))
        except (json.JSONDecodeError, AttributeError) as err:
            logger.error("could not unmarshal API error: %s", err)
            error.title = (
                "Failed to unmarshal error body. mTLS Truststore API "
                "failed. Check details for more information."
            )
            error.detail = unescape_content(body)

        error.status = response.status_code

        return error
