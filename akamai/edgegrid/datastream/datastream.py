"""DataStream API client providing access to Akamai DataStream2 endpoints.

Mirrors Go ``pkg/datastream`` (ds.go, stream.go, stream_activation.go,
properties.go, errors.go) and implements the DS interface with ten
endpoint methods for managing streams, activations, properties and
dataset fields.
"""

import json
import logging

from akamai.edgegrid.session import Session
from akamai.edgegrid.utils import unescape_content
from akamai.edgegrid.datastream.models import (
    ActivateStreamRequest,
    ActivationHistoryEntry,
    CreateStreamRequest,
    DataSetField,
    DataSets,
    DeactivateStreamRequest,
    DeleteStreamRequest,
    DeliveryConfiguration,
    Destination,
    DetailedStreamVersion,
    Frequency,
    GetActivationHistoryRequest,
    GetDatasetFieldsRequest,
    GetPropertiesRequest,
    GetStreamRequest,
    ListStreamsRequest,
    PropertiesDetails,
    Property,
    PropertyDetails,
    StreamConfiguration,
    StreamDetails,
    UpdateStreamRequest,
)
from akamai.edgegrid.datastream.errors import (
    Error,
    ErrActivateStream,
    ErrCreateStream,
    ErrDeactivateStream,
    ErrDeleteStream,
    ErrGetActivationHistory,
    ErrGetDatasetFields,
    ErrGetProperties,
    ErrGetStream,
    ErrListStreams,
    ErrStructValidation,
    ErrUpdateStream,
    RequestErrors,
)
from akamai.edgegrid.datastream.validation import (
    validate_activate_stream,
    validate_create_stream,
    validate_deactivate_stream,
    validate_delete_stream,
    validate_get_activation_history,
    validate_get_properties,
    validate_get_stream,
    validate_update_stream,
)

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------
# Private helpers – camelCase / snake_case conversion
# -------------------------------------------------------------------

# Python field → JSON key for special cases where the standard
# snake_case→camelCase rule does not match Go struct tags.
_PYTHON_TO_JSON: dict[str, str] = {
    "delimiter": "fieldDelimiter",
    "mtls": "mTLS",
}


def _snake_to_camel(name: str) -> str:
    """Convert a *snake_case* identifier to *camelCase*."""
    parts = name.split("_")
    return parts[0] + "".join(w.title() for w in parts[1:])


# -------------------------------------------------------------------
# Private helpers – request body serialisation
# -------------------------------------------------------------------


def _serialize_connector(connector) -> dict:
    """Serialise a connector dataclass to a dict with camelCase keys.

    All concrete connector types (S3Connector, AzureConnector, …) are
    plain dataclasses whose fields map 1-to-1 to Go JSON struct tags via
    the standard snake→camel rule (with the special-case overrides in
    ``_PYTHON_TO_JSON``).
    """
    result: dict = {}
    for field_name, value in vars(connector).items():
        key = _PYTHON_TO_JSON.get(field_name, _snake_to_camel(field_name))
        result[key] = value
    return result


def _serialize_delivery_config(
    delivery: DeliveryConfiguration,
) -> dict:
    """Serialise DeliveryConfiguration to a JSON-compatible dict."""
    result: dict = {
        "format": delivery.format,
        "frequency": {
            "intervalInSeconds": delivery.frequency.interval_in_seconds,
        },
    }
    # Go omitempty – include only when set
    if delivery.delimiter is not None:
        result["fieldDelimiter"] = delivery.delimiter
    if delivery.upload_file_prefix:
        result["uploadFilePrefix"] = delivery.upload_file_prefix
    if delivery.upload_file_suffix:
        result["uploadFileSuffix"] = delivery.upload_file_suffix
    return result


def _serialize_stream_config(config: StreamConfiguration) -> dict:
    """Serialise *StreamConfiguration* for CreateStream / UpdateStream.

    Applies camelCase key mapping and Go ``omitempty`` semantics so
    that ``json.Marshal`` behaviour is matched.
    """
    result: dict = {
        "contractId": config.contract_id,
        "datasetFields": [
            {"datasetFieldId": fld.dataset_field_id}
            for fld in config.dataset_fields
        ],
        "deliveryConfiguration": _serialize_delivery_config(
            config.delivery_configuration
        ),
        "properties": [
            {"propertyId": prop.property_id}
            for prop in config.properties
        ],
        "streamName": config.stream_name,
    }
    # omitempty: include only when non-zero
    if config.collect_midgress:
        result["collectMidgress"] = config.collect_midgress
    if config.group_id:
        result["groupId"] = config.group_id
    if config.notification_emails:
        result["notificationEmails"] = config.notification_emails
    if config.sampling_percentage:
        result["samplingPercentage"] = config.sampling_percentage
    # Destination is a concrete connector instance
    if config.destination is not None:
        result["destination"] = _serialize_connector(config.destination)
    return result


# -------------------------------------------------------------------
# Private helpers – response body deserialisation
# -------------------------------------------------------------------


def _parse_frequency(data: dict) -> Frequency:
    """Deserialise a ``Frequency`` from a JSON dict."""
    return Frequency(
        interval_in_seconds=data.get("intervalInSeconds", 0),
    )


def _parse_delivery_config(data: dict) -> DeliveryConfiguration:
    """Deserialise a ``DeliveryConfiguration`` from a JSON dict."""
    return DeliveryConfiguration(
        delimiter=data.get("fieldDelimiter"),
        format=data.get("format", ""),
        frequency=_parse_frequency(data.get("frequency", {})),
        upload_file_prefix=data.get("uploadFilePrefix", ""),
        upload_file_suffix=data.get("uploadFileSuffix", ""),
    )


def _parse_destination(data: dict) -> Destination:
    """Deserialise a ``Destination`` from a JSON dict."""
    return Destination(
        authentication_type=data.get("authenticationType", ""),
        compress_logs=data.get("compressLogs", False),
        destination_type=data.get("destinationType", ""),
        display_name=data.get("displayName", ""),
        path=data.get("path", ""),
        endpoint=data.get("endpoint", ""),
        index_name=data.get("indexName", ""),
        service_account_name=data.get("serviceAccountName", ""),
        project_id=data.get("projectId", ""),
        service=data.get("service", ""),
        bucket=data.get("bucket", ""),
        tags=data.get("tags", ""),
        region=data.get("region", ""),
        account_name=data.get("accountName", ""),
        namespace=data.get("namespace", ""),
        container_name=data.get("containerName", ""),
        source=data.get("source", ""),
        content_type=data.get("contentType", ""),
        custom_header_name=data.get("customHeaderName", ""),
        custom_header_value=data.get("customHeaderValue", ""),
        tls_hostname=data.get("tlsHostname", ""),
        mtls=data.get("mTLS", ""),
    )


def _parse_data_set_field(data: dict) -> DataSetField:
    """Deserialise a ``DataSetField`` from a JSON dict."""
    return DataSetField(
        dataset_field_id=data.get("datasetFieldId", 0),
        dataset_field_description=data.get(
            "datasetFieldDescription", ""
        ),
        dataset_field_json_key=data.get("datasetFieldJsonKey", ""),
        dataset_field_name=data.get("datasetFieldName", ""),
        dataset_field_group=data.get("datasetFieldGroup", ""),
    )


def _parse_property(data: dict) -> Property:
    """Deserialise a ``Property`` from a JSON dict."""
    return Property(
        property_id=data.get("propertyId", 0),
        property_name=data.get("propertyName", ""),
        integration_type=data.get("integrationType", ""),
    )


def _parse_property_details(data: dict) -> PropertyDetails:
    """Deserialise a ``PropertyDetails`` from a JSON dict."""
    return PropertyDetails(
        hostnames=data.get("hostnames", []),
        product_id=data.get("productId", ""),
        product_name=data.get("productName", ""),
        property_id=data.get("propertyId", 0),
        property_name=data.get("propertyName", ""),
        contract_id=data.get("contractId", ""),
    )


def _parse_detailed_stream(data: dict) -> DetailedStreamVersion:
    """Deserialise a ``DetailedStreamVersion`` from a JSON dict."""
    return DetailedStreamVersion(
        contract_id=data.get("contractId", ""),
        created_by=data.get("createdBy", ""),
        created_date=data.get("createdDate", ""),
        collect_midgress=data.get("collectMidgress", False),
        dataset_fields=[
            _parse_data_set_field(f)
            for f in data.get("datasetFields", [])
        ],
        delivery_configuration=_parse_delivery_config(
            data.get("deliveryConfiguration", {})
        ),
        destination=_parse_destination(
            data.get("destination", {})
        ),
        group_id=data.get("groupId", 0),
        latest_version=data.get("latestVersion", 0),
        modified_by=data.get("modifiedBy", ""),
        modified_date=data.get("modifiedDate", ""),
        notification_emails=data.get("notificationEmails", []),
        product_id=data.get("productId", ""),
        properties=[
            _parse_property(p)
            for p in data.get("properties", [])
        ],
        stream_id=data.get("streamId", 0),
        stream_name=data.get("streamName", ""),
        stream_version=data.get("streamVersion", 0),
        stream_status=data.get("streamStatus", ""),
        integration_type=data.get("integrationType", ""),
        sampling_percentage=data.get("samplingPercentage", 0),
    )


def _parse_stream_details(data: dict) -> StreamDetails:
    """Deserialise a ``StreamDetails`` from a JSON dict."""
    return StreamDetails(
        contract_id=data.get("contractId", ""),
        created_by=data.get("createdBy", ""),
        created_date=data.get("createdDate", ""),
        group_id=data.get("groupId", 0),
        latest_version=data.get("latestVersion", 0),
        modified_by=data.get("modifiedBy", ""),
        modified_date=data.get("modifiedDate", ""),
        properties=[
            _parse_property(p)
            for p in data.get("properties", [])
        ],
        product_id=data.get("productId", ""),
        stream_id=data.get("streamId", 0),
        stream_name=data.get("streamName", ""),
        stream_status=data.get("streamStatus", ""),
        stream_version=data.get("streamVersion", 0),
        integration_type=data.get("integrationType", ""),
        sampling_percentage=data.get("samplingPercentage", 0),
    )


def _parse_activation_entry(
    data: dict,
) -> ActivationHistoryEntry:
    """Deserialise an ``ActivationHistoryEntry`` from a JSON dict."""
    return ActivationHistoryEntry(
        modified_by=data.get("modifiedBy", ""),
        modified_date=data.get("modifiedDate", ""),
        status=data.get("status", ""),
        stream_id=data.get("streamId", 0),
        stream_version=data.get("streamVersion", 0),
    )


def _parse_properties_details(data: dict) -> PropertiesDetails:
    """Deserialise a ``PropertiesDetails`` from a JSON dict."""
    return PropertiesDetails(
        properties=[
            _parse_property_details(p)
            for p in data.get("properties", [])
        ],
        group_id=data.get("groupId", 0),
    )


def _parse_data_sets(data: dict) -> DataSets:
    """Deserialise a ``DataSets`` from a JSON dict."""
    return DataSets(
        dataset_fields=[
            _parse_data_set_field(f)
            for f in data.get("datasetFields", [])
        ],
    )


# -------------------------------------------------------------------
# Client class
# -------------------------------------------------------------------


class Client:  # pylint: disable=too-many-public-methods
    """DataStream API client.

    Provides methods for managing DataStream2 configurations including
    stream CRUD operations, activations, properties, and dataset fields.

    Mirrors Go ``pkg/datastream`` DS interface.

    See: https://techdocs.akamai.com/datastream2/reference/api
    """

    def __init__(self, session: Session):
        """Initialise the DataStream client.

        :param session: An authenticated :class:`Session` providing HTTP
            request execution.
        """
        self._session = session

    # ------------------------------------------------------------------
    # Private – error response parsing
    # ------------------------------------------------------------------

    def _parse_error(self, response) -> Error:
        """Parse an API error from *response*.

        Mirrors Go ``ds.Error()`` in ``errors.go``.  Reads the response
        body, attempts JSON unmarshal into an :class:`Error`, and falls
        back to raw text with HTML un-escaping when JSON parsing fails.
        """
        try:
            body = response.text
        except Exception:  # pylint: disable=broad-except
            logger.error(
                "reading error response body: %s",
                response.status_code,
            )
            return Error(
                status_code=response.status_code,
                title="Failed to read error body",
                detail=str(response.status_code),
            )

        try:
            data = json.loads(body)
            errors_list: list[RequestErrors] = []
            for entry in data.get("errors", []):
                errors_list.append(
                    RequestErrors(
                        type=entry.get("type", ""),
                        title=entry.get("title", ""),
                        detail=entry.get("detail", ""),
                        instance=entry.get("instance", ""),
                    )
                )
            return Error(
                type=data.get("type", ""),
                title=data.get("title", ""),
                detail=data.get("detail", ""),
                instance=data.get("instance", ""),
                status_code=response.status_code,
                errors=errors_list,
            )
        except (json.JSONDecodeError, AttributeError, TypeError):
            logger.error(
                "could not unmarshal API error: %s", body
            )
            return Error(
                title=(
                    "Failed to unmarshal error body. "
                    "DataStream2 API failed. "
                    "Check details for more information."
                ),
                detail=unescape_content(body),
                status_code=response.status_code,
            )

    # ------------------------------------------------------------------
    # Stream CRUD
    # ------------------------------------------------------------------

    def create_stream(
        self, params: CreateStreamRequest,
    ) -> DetailedStreamVersion:
        """Create a stream.

        :param params: Stream creation parameters including the full
            stream configuration and the ``activate`` flag.
        :returns: The newly created stream version details.
        :raises ValueError: On request validation failure.
        :raises Error: On API error response.

        See: https://techdocs.akamai.com/datastream2/v3/reference/post-stream-cdn
        """
        logger.debug("CreateStream")

        # Set destination type before validation (Go stream.go:291)
        params.stream_configuration.destination.set_destination_type()

        validation_err = validate_create_stream(params)
        if validation_err is not None:
            raise ValueError(
                f"{ErrCreateStream}: "
                f"{ErrStructValidation}: "
                f"{validation_err}"
            )

        path = "/datastream-config-api/v3/log/cdn/streams"
        query = {"activate": str(params.activate).lower()}
        body = _serialize_stream_config(
            params.stream_configuration,
        )

        response, data = self._session.exec(
            "POST",
            path,
            body=body,
            expect_json=True,
            params=query,
            error_parser=self._parse_error,
        )

        if response.status_code != 201:
            raise ValueError(
                f"{ErrCreateStream}: "
                f"{self._parse_error(response)}"
            )

        return _parse_detailed_stream(data)

    def get_stream(
        self, params: GetStreamRequest,
    ) -> DetailedStreamVersion:
        """Get stream details.

        :param params: Request identifying the stream by ID and
            optionally by version number.
        :returns: The detailed stream version.
        :raises ValueError: On request validation failure.
        :raises Error: On API error response.

        See: https://techdocs.akamai.com/datastream2/v3/reference/get-stream
        """
        logger.debug("GetStream")

        validation_err = validate_get_stream(params)
        if validation_err is not None:
            raise ValueError(
                f"{ErrGetStream}: "
                f"{ErrStructValidation}: "
                f"{validation_err}"
            )

        path = (
            "/datastream-config-api/v3/log/cdn/streams/"
            f"{params.stream_id}"
        )
        query: dict[str, str] = {}
        if params.version is not None:
            query["version"] = str(params.version)

        response, data = self._session.exec(
            "GET",
            path,
            expect_json=True,
            params=query or None,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise ValueError(
                f"{ErrGetStream}: "
                f"{self._parse_error(response)}"
            )

        return _parse_detailed_stream(data)

    def update_stream(
        self, params: UpdateStreamRequest,
    ) -> DetailedStreamVersion:
        """Update a stream.

        :param params: Stream update parameters including the stream
            ID, full stream configuration, and the ``activate`` flag.
        :returns: The updated stream version details.
        :raises ValueError: On request validation failure.
        :raises Error: On API error response.

        See: https://techdocs.akamai.com/datastream2/v3/reference/put-stream-cdn
        """
        logger.debug("UpdateStream")

        # Set destination type before validation (Go stream.go:368)
        params.stream_configuration.destination.set_destination_type()

        validation_err = validate_update_stream(params)
        if validation_err is not None:
            raise ValueError(
                f"{ErrUpdateStream}: "
                f"{ErrStructValidation}: "
                f"{validation_err}"
            )

        path = (
            "/datastream-config-api/v3/log/cdn/streams/"
            f"{params.stream_id}"
        )
        query = {"activate": str(params.activate).lower()}
        body = _serialize_stream_config(
            params.stream_configuration,
        )

        response, data = self._session.exec(
            "PUT",
            path,
            body=body,
            expect_json=True,
            params=query,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise ValueError(
                f"{ErrUpdateStream}: "
                f"{self._parse_error(response)}"
            )

        return _parse_detailed_stream(data)

    def delete_stream(
        self, params: DeleteStreamRequest,
    ) -> None:
        """Delete a stream.

        :param params: Request identifying the stream to delete.
        :raises ValueError: On request validation failure.
        :raises Error: On API error response.

        See: https://techdocs.akamai.com/datastream2/v3/reference/delete-stream
        """
        logger.debug("DeleteStream")

        validation_err = validate_delete_stream(params)
        if validation_err is not None:
            raise ValueError(
                f"{ErrDeleteStream}: "
                f"{ErrStructValidation}: "
                f"{validation_err}"
            )

        path = (
            "/datastream-config-api/v3/log/cdn/streams/"
            f"{params.stream_id}"
        )

        response, _ = self._session.exec(
            "DELETE",
            path,
            error_parser=self._parse_error,
        )

        if response.status_code != 204:
            raise ValueError(
                f"{ErrDeleteStream}: "
                f"{self._parse_error(response)}"
            )

    def list_streams(
        self, params: ListStreamsRequest,
    ) -> list[StreamDetails]:
        """Retrieve list of streams.

        :param params: Optional filter by *group_id*.
        :returns: A list of stream summaries.
        :raises Error: On API error response.

        See: https://techdocs.akamai.com/datastream2/v3/reference/get-streams
        """
        logger.debug("ListStreams")

        path = "/datastream-config-api/v3/log/cdn/streams"
        query: dict[str, str] = {}
        if params.group_id is not None:
            query["groupId"] = str(params.group_id)

        response, data = self._session.exec(
            "GET",
            path,
            expect_json=True,
            params=query or None,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise ValueError(
                f"{ErrListStreams}: "
                f"{self._parse_error(response)}"
            )

        return [
            _parse_stream_details(item)
            for item in (data or [])
        ]

    # ------------------------------------------------------------------
    # Activation
    # ------------------------------------------------------------------

    def activate_stream(
        self, params: ActivateStreamRequest,
    ) -> DetailedStreamVersion:
        """Activate stream with given ID.

        :param params: Request identifying the stream to activate.
        :returns: The activated stream version details.
        :raises ValueError: On request validation failure.
        :raises Error: On API error response.

        See: https://techdocs.akamai.com/datastream2/v3/reference/post-stream-activate
        """
        logger.debug("ActivateStream")

        validation_err = validate_activate_stream(params)
        if validation_err is not None:
            raise ValueError(
                f"{ErrActivateStream}: "
                f"{ErrStructValidation}: "
                f"{validation_err}"
            )

        path = (
            "/datastream-config-api/v3/log/cdn/streams/"
            f"{params.stream_id}/activate"
        )

        response, data = self._session.exec(
            "POST",
            path,
            expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise ValueError(
                f"{ErrActivateStream}: "
                f"{self._parse_error(response)}"
            )

        return _parse_detailed_stream(data)

    def deactivate_stream(
        self, params: DeactivateStreamRequest,
    ) -> DetailedStreamVersion:
        """Deactivate stream with given ID.

        :param params: Request identifying the stream to deactivate.
        :returns: The deactivated stream version details.
        :raises ValueError: On request validation failure.
        :raises Error: On API error response.

        See: https://techdocs.akamai.com/datastream2/v3/reference/post-stream-deactivate
        """
        logger.debug("DeactivateStream")

        validation_err = validate_deactivate_stream(params)
        if validation_err is not None:
            raise ValueError(
                f"{ErrDeactivateStream}: "
                f"{ErrStructValidation}: "
                f"{validation_err}"
            )

        path = (
            "/datastream-config-api/v3/log/cdn/streams/"
            f"{params.stream_id}/deactivate"
        )

        response, data = self._session.exec(
            "POST",
            path,
            expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise ValueError(
                f"{ErrDeactivateStream}: "
                f"{self._parse_error(response)}"
            )

        return _parse_detailed_stream(data)

    def get_activation_history(
        self, params: GetActivationHistoryRequest,
    ) -> list[ActivationHistoryEntry]:
        """Return activation history for all versions of a stream.

        :param params: Request identifying the stream.
        :returns: A list of activation history entries.
        :raises ValueError: On request validation failure.
        :raises Error: On API error response.

        See: https://techdocs.akamai.com/datastream2/v3/reference/get-stream-activation-history
        """
        logger.debug("GetActivationHistory")

        validation_err = validate_get_activation_history(params)
        if validation_err is not None:
            raise ValueError(
                f"{ErrGetActivationHistory}: "
                f"{ErrStructValidation}: "
                f"{validation_err}"
            )

        path = (
            "/datastream-config-api/v3/log/cdn/streams/"
            f"{params.stream_id}/activation-history"
        )

        response, data = self._session.exec(
            "GET",
            path,
            expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise ValueError(
                f"{ErrGetActivationHistory}: "
                f"{self._parse_error(response)}"
            )

        return [
            _parse_activation_entry(item)
            for item in (data or [])
        ]

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    def get_properties(
        self, params: GetPropertiesRequest,
    ) -> PropertiesDetails:
        """Get properties active on production and staging for a group.

        :param params: Request identifying the group.
        :returns: Properties details for the group.
        :raises ValueError: On request validation failure.
        :raises Error: On API error response.

        See: https://techdocs.akamai.com/datastream2/v3/reference/get-properties-cdn
        """
        logger.debug("GetProperties")

        validation_err = validate_get_properties(params)
        if validation_err is not None:
            raise ValueError(
                f"{ErrGetProperties}: "
                f"{ErrStructValidation}: "
                f"{validation_err}"
            )

        path = (
            "/datastream-config-api/v3/log/cdn/groups/"
            f"{params.group_id}/properties"
        )

        response, data = self._session.exec(
            "GET",
            path,
            expect_json=True,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise ValueError(
                f"{ErrGetProperties}: "
                f"{self._parse_error(response)}"
            )

        return _parse_properties_details(data)

    def get_dataset_fields(
        self, params: GetDatasetFieldsRequest,
    ) -> DataSets:
        """Get groups of data set fields available in the template.

        :param params: Optional filter by *product_id*.
        :returns: Available dataset field groups.
        :raises Error: On API error response.

        See: https://techdocs.akamai.com/datastream2/v3/reference/get-dataset-fields
        """
        logger.debug("GetDatasetFields")

        path = "/datastream-config-api/v3/log/cdn/datasets-fields"
        query: dict[str, str] = {}
        if params.product_id is not None:
            query["productId"] = params.product_id

        response, data = self._session.exec(
            "GET",
            path,
            expect_json=True,
            params=query or None,
            error_parser=self._parse_error,
        )

        if response.status_code != 200:
            raise ValueError(
                f"{ErrGetDatasetFields}: "
                f"{self._parse_error(response)}"
            )

        return _parse_data_sets(data)
