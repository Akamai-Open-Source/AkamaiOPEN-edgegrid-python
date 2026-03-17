"""Cloud Access Manager API client implementation."""

import logging

from akamai.edgegrid.session import Session
from akamai.edgegrid.cloudaccess import errors
from akamai.edgegrid.cloudaccess import models
from akamai.edgegrid.cloudaccess import validation

logger = logging.getLogger(__name__)


class CloudAccessClient:
    """Cloud Access Manager API client.

    Provides methods for managing access keys, versions, and
    property lookups.  Mirrors Go pkg/cloudaccess.CloudAccess
    interface.

    Usage::

        >>> from akamai.edgegrid.session import Session
        >>> session = Session(edgerc_path="~/.edgerc", section="ca")
        >>> client = CloudAccessClient(session)
        >>> keys = client.list_access_keys(
        ...     models.ListAccessKeysRequest()
        ... )
    """

    def __init__(self, session: Session):
        """Initialize the Cloud Access Manager client.

        Mirrors Go cloudaccess.Client() constructor
        (cloudaccess.go line 168).

        :param session: Authenticated session for API communication.
        """
        self._session = session

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _error(self, response):
        """Parse API error from HTTP response.

        Mirrors Go cloudaccess.Error() method (errors.go lines 43-64).
        Reads response body, attempts JSON unmarshal, falls back to
        raw text.

        :param response: HTTP response from the API.
        :returns: Populated Error instance.
        """
        return errors.Error.from_response(response)

    # ------------------------------------------------------------------
    # Access Key methods (from access_key.go)
    # ------------------------------------------------------------------

    def get_access_key_status(
        self, params: models.GetAccessKeyStatusRequest,
    ) -> models.GetAccessKeyStatusResponse:
        """Get the status of an access key creation request.

        See: https://techdocs.akamai.com/cloud-access-mgr/reference/
        get-access-key-create-request

        Mirrors Go GetAccessKeyStatus
        (access_key.go lines 165-191).

        :param params: Request containing request_id.
        :returns: Status of the access key creation request.
        :raises ValueError: If request validation fails.
        :raises errors.Error: If the API returns an error.
        """
        logger.debug("GetAccessKeyStatus")

        err = validation.validate_get_access_key_status_request(params)
        if err:
            raise ValueError(
                f"{errors.ErrGetAccessKeyStatus}: "
                f"struct validation: {err}"
            )

        url = (
            "/cam/v1/access-key-create-requests/"
            f"{params.request_id}"
        )

        response, result = self._session.exec(
            "GET", url,
            expect_json=True,
            error_parser=self._error,
        )

        if response.status_code != 200:
            raise self._error(response)

        return models.GetAccessKeyStatusResponse.from_dict(result)

    def create_access_key(
        self, params: models.CreateAccessKeyRequest,
    ) -> models.CreateAccessKeyResponse:
        """Create a new access key.

        See: https://techdocs.akamai.com/cloud-access-mgr/reference/
        post-access-key

        Mirrors Go CreateAccessKey (access_key.go lines 193-225).
        Captures the Location header from the 202 response.

        :param params: Request body for creating the access key.
        :returns: Response with request_id, retry_after, location.
        :raises ValueError: If request validation fails.
        :raises errors.Error: If the API returns an error.
        """
        logger.debug("CreateAccessKey")

        err = validation.validate_create_access_key_request(params)
        if err:
            raise ValueError(
                f"{errors.ErrCreateAccessKey}: "
                f"struct validation: {err}"
            )

        url = "/cam/v1/access-keys"

        response, result = self._session.exec(
            "POST", url,
            body=params.to_dict(),
            expect_json=True,
            error_parser=self._error,
        )

        if response.status_code != 202:
            raise self._error(response)

        resp = models.CreateAccessKeyResponse.from_dict(result)
        resp.location = response.headers.get("Location", "")
        return resp

    def get_access_key(
        self, params: models.AccessKeyRequest,
    ) -> models.GetAccessKeyResponse:
        """Return details for a specific access key.

        See: https://techdocs.akamai.com/cloud-access-mgr/reference/
        get-access-key

        Mirrors Go GetAccessKey (access_key.go lines 227-258).

        :param params: Request containing access_key_uid.
        :returns: Access key details.
        :raises ValueError: If request validation fails.
        :raises errors.Error: If the API returns an error.
        """
        logger.debug("GetAccessKey")

        err = validation.validate_access_key_request(params)
        if err:
            raise ValueError(
                f"{errors.ErrGetAccessKey}: "
                f"struct validation: {err}"
            )

        url = f"/cam/v1/access-keys/{params.access_key_uid}"

        response, result = self._session.exec(
            "GET", url,
            expect_json=True,
            error_parser=self._error,
        )

        if response.status_code != 200:
            raise self._error(response)

        return models.GetAccessKeyResponse.from_dict(result)

    def list_access_keys(
        self, params: models.ListAccessKeysRequest,
    ) -> models.ListAccessKeysResponse:
        """Return detailed information about all access keys.

        See: https://techdocs.akamai.com/cloud-access-mgr/reference/
        get-access-keys

        Mirrors Go ListAccessKeys (access_key.go lines 260-291).
        No request validation is performed (mirrors Go behaviour).

        :param params: Request with optional version_guid filter.
        :returns: List of access keys.
        :raises errors.Error: If the API returns an error.
        """
        logger.debug("ListAccessKeys")

        url = "/cam/v1/access-keys"
        query_params: dict[str, str] | None = None
        if params.version_guid:
            query_params = {"versionGuid": params.version_guid}

        response, result = self._session.exec(
            "GET", url,
            expect_json=True,
            params=query_params,
            error_parser=self._error,
        )

        if response.status_code != 200:
            raise self._error(response)

        return models.ListAccessKeysResponse.from_dict(result)

    def delete_access_key(
        self, params: models.AccessKeyRequest,
    ) -> None:
        """Delete an access key.

        See: https://techdocs.akamai.com/cloud-access-mgr/reference/
        delete-access-key

        Mirrors Go DeleteAccessKey (access_key.go lines 293-322).
        Returns ``None`` on success (204 No Content).

        :param params: Request containing access_key_uid.
        :raises ValueError: If request validation fails.
        :raises errors.Error: If the API returns an error.
        """
        logger.debug("DeleteAccessKey")

        err = validation.validate_access_key_request(params)
        if err:
            raise ValueError(
                f"{errors.ErrDeleteAccessKey}: "
                f"struct validation: {err}"
            )

        url = f"/cam/v1/access-keys/{params.access_key_uid}"

        response, _ = self._session.exec(
            "DELETE", url,
            error_parser=self._error,
        )

        if response.status_code != 204:
            raise self._error(response)

    def update_access_key(
        self,
        body: models.UpdateAccessKeyRequest,
        params: models.AccessKeyRequest,
    ) -> models.UpdateAccessKeyResponse:
        """Update the name of an access key.

        See: https://techdocs.akamai.com/cloud-access-mgr/reference/
        put-access-key

        Mirrors Go UpdateAccessKey (access_key.go lines 324-358).
        Validates both the URL parameters and the request body.

        :param body: Request body with the new access key name.
        :param params: Request containing access_key_uid.
        :returns: Updated access key information.
        :raises ValueError: If request validation fails.
        :raises errors.Error: If the API returns an error.
        """
        logger.debug("UpdateAccessKey")

        err = validation.validate_access_key_request(params)
        if err:
            raise ValueError(
                f"{errors.ErrUpdateAccessKey}: "
                f"struct validation: {err}"
            )

        err = validation.validate_update_access_key_request(body)
        if err:
            raise ValueError(
                f"{errors.ErrUpdateAccessKey}: "
                f"struct validation: {err}"
            )

        url = f"/cam/v1/access-keys/{params.access_key_uid}"

        response, result = self._session.exec(
            "PUT", url,
            body=body.to_dict(),
            expect_json=True,
            error_parser=self._error,
        )

        if response.status_code != 200:
            raise self._error(response)

        return models.UpdateAccessKeyResponse.from_dict(result)

    # ------------------------------------------------------------------
    # Access Key Version methods (from access_key_version.go)
    # ------------------------------------------------------------------

    def get_access_key_version_status(
        self, params: models.GetAccessKeyVersionStatusRequest,
    ) -> models.GetAccessKeyVersionStatusResponse:
        """Get the status of a version creation request.

        See: https://techdocs.akamai.com/cloud-access-mgr/reference/
        get-access-key-version-create-request

        Mirrors Go GetAccessKeyVersionStatus
        (access_key_version.go lines 158-184).

        :param params: Request containing request_id.
        :returns: Status of the version creation request.
        :raises ValueError: If request validation fails.
        :raises errors.Error: If the API returns an error.
        """
        logger.debug("GetAccessKeyVersionStatus")

        err = validation.validate_get_access_key_version_status_request(
            params,
        )
        if err:
            raise ValueError(
                f"{errors.ErrGetAccessKeyVersionStatus}: "
                f"struct validation: {err}"
            )

        url = (
            "/cam/v1/access-key-version-create-requests/"
            f"{params.request_id}"
        )

        response, result = self._session.exec(
            "GET", url,
            expect_json=True,
            error_parser=self._error,
        )

        if response.status_code != 200:
            raise self._error(response)

        return models.GetAccessKeyVersionStatusResponse.from_dict(
            result,
        )

    def create_access_key_version(
        self, params: models.CreateAccessKeyVersionRequest,
    ) -> models.CreateAccessKeyVersionResponse:
        """Rotate an access key to a new version.

        See: https://techdocs.akamai.com/cloud-access-mgr/reference/
        post-access-key-version

        Mirrors Go CreateAccessKeyVersion
        (access_key_version.go lines 186-213).

        :param params: Request with access_key_uid and body.
        :returns: Response with request_id and retry_after.
        :raises ValueError: If request validation fails.
        :raises errors.Error: If the API returns an error.
        """
        logger.debug("CreateAccessKeyVersion")

        err = validation.validate_create_access_key_version_request(
            params,
        )
        if err:
            raise ValueError(
                f"{errors.ErrCreateAccessKeyVersion}: "
                f"struct validation: {err}"
            )

        url = (
            f"/cam/v1/access-keys/{params.access_key_uid}/versions"
        )

        response, result = self._session.exec(
            "POST", url,
            body=params.body.to_dict(),
            expect_json=True,
            error_parser=self._error,
        )

        if response.status_code != 202:
            raise self._error(response)

        return models.CreateAccessKeyVersionResponse.from_dict(result)

    def get_access_key_version(
        self, params: models.GetAccessKeyVersionRequest,
    ) -> models.GetAccessKeyVersionResponse:
        """Return details for a specific access key version.

        See: https://techdocs.akamai.com/cloud-access-mgr/reference/
        get-access-key-version

        Mirrors Go GetAccessKeyVersion
        (access_key_version.go lines 215-242).

        :param params: Request with access_key_uid and version.
        :returns: Access key version details.
        :raises ValueError: If request validation fails.
        :raises errors.Error: If the API returns an error.
        """
        logger.debug("GetAccessKeyVersion")

        err = validation.validate_get_access_key_version_request(params)
        if err:
            raise ValueError(
                f"{errors.ErrGetAccessKeyVersion}: "
                f"struct validation: {err}"
            )

        url = (
            f"/cam/v1/access-keys/{params.access_key_uid}"
            f"/versions/{params.version}"
        )

        response, result = self._session.exec(
            "GET", url,
            expect_json=True,
            error_parser=self._error,
        )

        if response.status_code != 200:
            raise self._error(response)

        return models.GetAccessKeyVersionResponse.from_dict(result)

    def list_access_key_versions(
        self, params: models.ListAccessKeyVersionsRequest,
    ) -> models.ListAccessKeyVersionsResponse:
        """Return details about all versions for an access key.

        See: https://techdocs.akamai.com/cloud-access-mgr/reference/
        get-access-key-versions

        Mirrors Go ListAccessKeyVersions
        (access_key_version.go lines 244-271).

        :param params: Request containing access_key_uid.
        :returns: List of access key versions.
        :raises ValueError: If request validation fails.
        :raises errors.Error: If the API returns an error.
        """
        logger.debug("ListAccessKeyVersions")

        err = validation.validate_list_access_key_versions_request(
            params,
        )
        if err:
            raise ValueError(
                f"{errors.ErrListAccessKeyVersions}: "
                f"struct validation: {err}"
            )

        url = (
            f"/cam/v1/access-keys/{params.access_key_uid}/versions"
        )

        response, result = self._session.exec(
            "GET", url,
            expect_json=True,
            error_parser=self._error,
        )

        if response.status_code != 200:
            raise self._error(response)

        return models.ListAccessKeyVersionsResponse.from_dict(result)

    def delete_access_key_version(
        self, params: models.DeleteAccessKeyVersionRequest,
    ) -> models.DeleteAccessKeyVersionResponse:
        """Delete a specific version of an access key.

        See: https://techdocs.akamai.com/cloud-access-mgr/reference/
        delete-access-key-version

        Mirrors Go DeleteAccessKeyVersion
        (access_key_version.go lines 273-300).
        Returns a typed response (unlike delete_access_key which
        returns None).

        :param params: Request with access_key_uid and version.
        :returns: Deleted version details.
        :raises ValueError: If request validation fails.
        :raises errors.Error: If the API returns an error.
        """
        logger.debug("DeleteAccessKeyVersion")

        err = validation.validate_delete_access_key_version_request(
            params,
        )
        if err:
            raise ValueError(
                f"{errors.ErrDeleteAccessKeyVersion}: "
                f"struct validation: {err}"
            )

        url = (
            f"/cam/v1/access-keys/{params.access_key_uid}"
            f"/versions/{params.version}"
        )

        response, result = self._session.exec(
            "DELETE", url,
            expect_json=True,
            error_parser=self._error,
        )

        if response.status_code != 202:
            raise self._error(response)

        return models.DeleteAccessKeyVersionResponse.from_dict(result)

    # ------------------------------------------------------------------
    # Property lookup methods (from properties.go)
    # ------------------------------------------------------------------

    def lookup_properties(
        self, params: models.LookupPropertiesRequest,
    ) -> models.LookupPropertiesResponse:
        """Return properties using a specific access key version.

        Gets the data directly.  To avoid latency, use
        get_async_properties_lookup_id followed by
        perform_async_properties_lookup.

        See: https://techdocs.akamai.com/cloud-access-mgr/reference/
        get-access-key-version-properties

        Mirrors Go LookupProperties (properties.go lines 110-140).

        :param params: Request with access_key_uid and version.
        :returns: List of properties using the specified version.
        :raises ValueError: If request validation fails.
        :raises errors.Error: If the API returns an error.
        """
        logger.debug("LookupProperties")

        err = validation.validate_lookup_properties_request(params)
        if err:
            raise ValueError(
                f"{errors.ErrLookupProperties}: "
                f"struct validation: {err}"
            )

        url = (
            f"/cam/v1/access-keys/{params.access_key_uid}"
            f"/versions/{params.version}/properties"
        )

        response, result = self._session.exec(
            "GET", url,
            expect_json=True,
            error_parser=self._error,
        )

        if response.status_code != 200:
            raise self._error(response)

        return models.LookupPropertiesResponse.from_dict(result)

    def get_async_properties_lookup_id(
        self, params: models.GetAsyncPropertiesLookupIDRequest,
    ) -> models.GetAsyncPropertiesLookupIDResponse:
        """Get the unique identifier for an async properties lookup.

        See: https://techdocs.akamai.com/cloud-access-mgr/reference/
        get-async-version-property-lookup

        Mirrors Go GetAsyncPropertiesLookupID
        (properties.go lines 142-172).

        :param params: Request with access_key_uid and version.
        :returns: Response with lookup_id and retry_after.
        :raises ValueError: If request validation fails.
        :raises errors.Error: If the API returns an error.
        """
        logger.debug("GetAsyncPropertiesLookupID")

        err = validation.validate_get_async_properties_lookup_id_request(
            params,
        )
        if err:
            raise ValueError(
                f"{errors.ErrGetAsyncLookupIDProperties}: "
                f"struct validation: {err}"
            )

        url = (
            f"/cam/v1/access-keys/{params.access_key_uid}"
            f"/versions/{params.version}/property-lookup-id"
        )

        response, result = self._session.exec(
            "GET", url,
            expect_json=True,
            error_parser=self._error,
        )

        if response.status_code != 202:
            raise self._error(response)

        return models.GetAsyncPropertiesLookupIDResponse.from_dict(
            result,
        )

    def perform_async_properties_lookup(
        self, params: models.PerformAsyncPropertiesLookupRequest,
    ) -> models.PerformAsyncPropertiesLookupResponse:
        """Return properties via async lookup by lookup_id.

        See: https://techdocs.akamai.com/cloud-access-mgr/reference/
        get-property-lookup

        Mirrors Go PerformAsyncPropertiesLookup
        (properties.go lines 174-204).

        :param params: Request containing lookup_id.
        :returns: Async lookup result with status and properties.
        :raises ValueError: If request validation fails.
        :raises errors.Error: If the API returns an error.
        """
        logger.debug("PerformAsyncPropertiesLookup")

        err = validation.validate_perform_async_properties_lookup_request(
            params,
        )
        if err:
            raise ValueError(
                f"{errors.ErrPerformAsyncLookupProperties}: "
                f"struct validation: {err}"
            )

        url = f"/cam/v1/property-lookups/{params.lookup_id}"

        response, result = self._session.exec(
            "GET", url,
            expect_json=True,
            error_parser=self._error,
        )

        if response.status_code != 200:
            raise self._error(response)

        return models.PerformAsyncPropertiesLookupResponse.from_dict(
            result,
        )
