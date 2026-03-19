"""Request and response models for the DataStream API client."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


# StreamStatus constants
STREAM_STATUS_ACTIVATED = "ACTIVATED"
STREAM_STATUS_DEACTIVATED = "DEACTIVATED"
STREAM_STATUS_ACTIVATING = "ACTIVATING"
STREAM_STATUS_DEACTIVATING = "DEACTIVATING"
STREAM_STATUS_INACTIVE = "INACTIVE"

# DelimiterType constants
DELIMITER_TYPE_SPACE = "SPACE"

# FormatType constants
FORMAT_TYPE_STRUCTURED = "STRUCTURED"
FORMAT_TYPE_JSON = "JSON"

# IntervalInSeconds constants
INTERVAL_IN_SECONDS_30 = 30
INTERVAL_IN_SECONDS_60 = 60

# DestinationType constants
DESTINATION_TYPE_AZURE = "AZURE"
DESTINATION_TYPE_S3 = "S3"
DESTINATION_TYPE_DATADOG = "DATADOG"
DESTINATION_TYPE_SPLUNK = "SPLUNK"
DESTINATION_TYPE_GCS = "GCS"
DESTINATION_TYPE_HTTPS = "HTTPS"
DESTINATION_TYPE_SUMO_LOGIC = "SUMO_LOGIC"
DESTINATION_TYPE_ORACLE = "Oracle_Cloud_Storage"
DESTINATION_TYPE_LOGGLY = "LOGGLY"
DESTINATION_TYPE_NEW_RELIC = "NEWRELIC"
DESTINATION_TYPE_ELASTICSEARCH = "ELASTICSEARCH"
DESTINATION_TYPE_S3_COMPATIBLE = "S3_COMPATIBLE"
DESTINATION_TYPE_TRAFFIC_PEAK = "TRAFFICPEAK"
DESTINATION_TYPE_DYNATRACE = "DYNATRACE"

# AuthenticationType constants
AUTHENTICATION_TYPE_NONE = "NONE"
AUTHENTICATION_TYPE_BASIC = "BASIC"

# TrafficPeakContentType constants
TRAFFIC_PEAK_CONTENT_TYPE_JSON = "application/json"
TRAFFIC_PEAK_CONTENT_TYPE_JSON_UTF8 = "application/json; charset=utf-8"


@runtime_checkable
class AbstractConnector(Protocol):
    """Interface for all connector types.

    Mirrors Go AbstractConnector interface (stream.go lines 129-132).
    Each connector must implement set_destination_type() and validate().
    """

    def set_destination_type(self) -> None:
        """Set the destination type for this connector."""

    def validate(self) -> None:
        """Validate the connector fields.

        Raises ErrStructValidation on failure.
        """


@dataclass
class Frequency:
    """Frequency of collecting and sending logs."""

    interval_in_seconds: int = 0


@dataclass
class DeliveryConfiguration:
    """Configuration for log delivery format and frequency."""

    delimiter: str | None = None
    format: str = ""  # pylint: disable=redefined-builtin
    frequency: Frequency = field(default_factory=Frequency)
    upload_file_prefix: str = ""
    upload_file_suffix: str = ""


@dataclass
class DataSetField:
    """Data set field from the associated template."""

    dataset_field_id: int = 0
    dataset_field_description: str = ""
    dataset_field_json_key: str = ""
    dataset_field_name: str = ""
    dataset_field_group: str = ""


@dataclass
class DatasetFieldID:
    """Dataset field value used in create stream request."""

    dataset_field_id: int = 0


@dataclass
class DataSets:
    """List of data set fields from the template."""

    dataset_fields: list[DataSetField] = field(default_factory=list)


@dataclass
class Property:
    """Brief info about a property monitored in the stream."""

    property_id: int = 0
    property_name: str = ""
    integration_type: str = ""


@dataclass
class PropertyID:
    """Property ID used in create stream request."""

    property_id: int = 0


@dataclass
class PropertyDetails:
    """Detailed property information."""

    hostnames: list[str] = field(default_factory=list)
    product_id: str = ""
    product_name: str = ""
    property_id: int = 0
    property_name: str = ""
    contract_id: str = ""


@dataclass
class PropertiesDetails:
    """Properties belonging to a given group."""

    properties: list[PropertyDetails] = field(default_factory=list)
    group_id: int = 0


@dataclass
class Destination:  # pylint: disable=too-many-instance-attributes
    """Detailed destination configuration in a stream response."""

    authentication_type: str = ""
    compress_logs: bool = False
    destination_type: str = ""
    display_name: str = ""
    path: str = ""
    endpoint: str = ""
    index_name: str = ""
    service_account_name: str = ""
    project_id: str = ""
    service: str = ""
    bucket: str = ""
    tags: str = ""
    region: str = ""
    account_name: str = ""
    namespace: str = ""
    container_name: str = ""
    source: str = ""
    content_type: str = ""
    custom_header_name: str = ""
    custom_header_value: str = ""
    tls_hostname: str = ""
    mtls: str = ""


@dataclass
class DetailedStreamVersion:  # pylint: disable=too-many-instance-attributes
    """Detailed stream version returned from GetStream, CreateStream, etc."""

    contract_id: str = ""
    created_by: str = ""
    created_date: str = ""
    collect_midgress: bool = False
    dataset_fields: list[DataSetField] = field(default_factory=list)
    delivery_configuration: DeliveryConfiguration = field(
        default_factory=DeliveryConfiguration
    )
    destination: Destination = field(default_factory=Destination)
    group_id: int = 0
    latest_version: int = 0
    modified_by: str = ""
    modified_date: str = ""
    notification_emails: list[str] = field(default_factory=list)
    product_id: str = ""
    properties: list[Property] = field(default_factory=list)
    stream_id: int = 0
    stream_name: str = ""
    stream_version: int = 0
    stream_status: str = ""
    integration_type: str = ""
    sampling_percentage: int = 0


@dataclass
class StreamConfiguration:  # pylint: disable=too-many-instance-attributes
    """Stream configuration used for create/update requests."""

    contract_id: str = ""
    collect_midgress: bool = False
    dataset_fields: list[DatasetFieldID] = field(default_factory=list)
    destination: AbstractConnector | None = None
    delivery_configuration: DeliveryConfiguration = field(
        default_factory=DeliveryConfiguration
    )
    group_id: int = 0
    notification_emails: list[str] = field(default_factory=list)
    properties: list[PropertyID] = field(default_factory=list)
    stream_name: str = ""
    sampling_percentage: int = 0


@dataclass
class StreamUpdate:
    """Stream update response containing stream ID and version."""

    stream_id: int = 0
    stream_version: int = 0


@dataclass
class StreamDetails:  # pylint: disable=too-many-instance-attributes
    """Stream details returned from ListStreams."""

    contract_id: str = ""
    created_by: str = ""
    created_date: str = ""
    group_id: int = 0
    latest_version: int = 0
    modified_by: str = ""
    modified_date: str = ""
    properties: list[Property] = field(default_factory=list)
    product_id: str = ""
    stream_id: int = 0
    stream_name: str = ""
    stream_status: str = ""
    stream_version: int = 0
    integration_type: str = ""
    sampling_percentage: int = 0


@dataclass
class ActivationHistoryEntry:
    """Single activation history item."""

    modified_by: str = ""
    modified_date: str = ""
    status: str = ""
    stream_id: int = 0
    stream_version: int = 0


# Request models


@dataclass
class CreateStreamRequest:
    """Parameters for CreateStream."""

    stream_configuration: StreamConfiguration = field(
        default_factory=StreamConfiguration
    )
    activate: bool = False


@dataclass
class GetStreamRequest:
    """Parameters for GetStream."""

    stream_id: int = 0
    version: int | None = None


@dataclass
class UpdateStreamRequest:
    """Parameters for UpdateStream."""

    stream_id: int = 0
    stream_configuration: StreamConfiguration = field(
        default_factory=StreamConfiguration
    )
    activate: bool = False


@dataclass
class DeleteStreamRequest:
    """Parameters for DeleteStream."""

    stream_id: int = 0


@dataclass
class ListStreamsRequest:
    """Parameters for ListStreams."""

    group_id: int | None = None


@dataclass
class ActivateStreamRequest:
    """Parameters for ActivateStream."""

    stream_id: int = 0


@dataclass
class DeactivateStreamRequest:
    """Parameters for DeactivateStream."""

    stream_id: int = 0


@dataclass
class GetActivationHistoryRequest:
    """Parameters for GetActivationHistory."""

    stream_id: int = 0


@dataclass
class GetPropertiesRequest:
    """Parameters for GetProperties."""

    group_id: int = 0


@dataclass
class GetDatasetFieldsRequest:
    """Parameters for GetDatasetFields."""

    product_id: str | None = None


# Connector dataclasses


@dataclass
class S3Connector:
    """Amazon S3 destination connector."""

    destination_type: str = ""
    access_key: str = ""
    bucket: str = ""
    display_name: str = ""
    path: str = ""
    region: str = ""
    secret_access_key: str = ""

    def set_destination_type(self) -> None:
        """Set the destination type to S3."""
        self.destination_type = DESTINATION_TYPE_S3


@dataclass
class AzureConnector:
    """Azure Storage destination connector."""

    destination_type: str = ""
    access_key: str = ""
    account_name: str = ""
    display_name: str = ""
    container_name: str = ""
    path: str = ""

    def set_destination_type(self) -> None:
        """Set the destination type to Azure."""
        self.destination_type = DESTINATION_TYPE_AZURE


@dataclass
class DatadogConnector:  # pylint: disable=too-many-instance-attributes
    """Datadog destination connector."""

    destination_type: str = ""
    auth_token: str = ""
    compress_logs: bool = False
    display_name: str = ""
    service: str = ""
    source: str = ""
    tags: str = ""
    endpoint: str = ""

    def set_destination_type(self) -> None:
        """Set the destination type to Datadog."""
        self.destination_type = DESTINATION_TYPE_DATADOG


@dataclass
class SplunkConnector:  # pylint: disable=too-many-instance-attributes
    """Splunk destination connector."""

    destination_type: str = ""
    compress_logs: bool = False
    display_name: str = ""
    event_collector_token: str = ""
    endpoint: str = ""
    custom_header_name: str = ""
    custom_header_value: str = ""
    tls_hostname: str = ""
    ca_cert: str = ""
    client_cert: str = ""
    client_key: str = ""

    def set_destination_type(self) -> None:
        """Set the destination type to Splunk."""
        self.destination_type = DESTINATION_TYPE_SPLUNK


@dataclass
class GCSConnector:
    """Google Cloud Storage destination connector."""

    destination_type: str = ""
    bucket: str = ""
    display_name: str = ""
    path: str = ""
    private_key: str = ""
    project_id: str = ""
    service_account_name: str = ""

    def set_destination_type(self) -> None:
        """Set the destination type to GCS."""
        self.destination_type = DESTINATION_TYPE_GCS


@dataclass
class CustomHTTPSConnector:  # pylint: disable=too-many-instance-attributes
    """Custom HTTPS endpoint connector."""

    destination_type: str = ""
    authentication_type: str = ""
    compress_logs: bool = False
    display_name: str = ""
    password: str = ""
    endpoint: str = ""
    user_name: str = ""
    content_type: str = ""
    custom_header_name: str = ""
    custom_header_value: str = ""
    tls_hostname: str = ""
    ca_cert: str = ""
    client_cert: str = ""
    client_key: str = ""

    def set_destination_type(self) -> None:
        """Set the destination type to HTTPS."""
        self.destination_type = DESTINATION_TYPE_HTTPS


@dataclass
class SumoLogicConnector:  # pylint: disable=too-many-instance-attributes
    """Sumo Logic destination connector."""

    destination_type: str = ""
    collector_code: str = ""
    compress_logs: bool = False
    display_name: str = ""
    endpoint: str = ""
    content_type: str = ""
    custom_header_name: str = ""
    custom_header_value: str = ""

    def set_destination_type(self) -> None:
        """Set the destination type to Sumo Logic."""
        self.destination_type = DESTINATION_TYPE_SUMO_LOGIC


@dataclass
class OracleCloudStorageConnector:  # pylint: disable=too-many-instance-attributes
    """Oracle Cloud Storage destination connector."""

    destination_type: str = ""
    access_key: str = ""
    bucket: str = ""
    display_name: str = ""
    namespace: str = ""
    path: str = ""
    region: str = ""
    secret_access_key: str = ""

    def set_destination_type(self) -> None:
        """Set the destination type to Oracle Cloud Storage."""
        self.destination_type = DESTINATION_TYPE_ORACLE


@dataclass
class LogglyConnector:  # pylint: disable=too-many-instance-attributes
    """Loggly destination connector."""

    destination_type: str = ""
    display_name: str = ""
    endpoint: str = ""
    auth_token: str = ""
    tags: str = ""
    content_type: str = ""
    custom_header_name: str = ""
    custom_header_value: str = ""

    def set_destination_type(self) -> None:
        """Set the destination type to Loggly."""
        self.destination_type = DESTINATION_TYPE_LOGGLY


@dataclass
class NewRelicConnector:
    """New Relic destination connector."""

    destination_type: str = ""
    display_name: str = ""
    endpoint: str = ""
    auth_token: str = ""
    content_type: str = ""
    custom_header_name: str = ""
    custom_header_value: str = ""

    def set_destination_type(self) -> None:
        """Set the destination type to New Relic."""
        self.destination_type = DESTINATION_TYPE_NEW_RELIC


@dataclass
class ElasticsearchConnector:  # pylint: disable=too-many-instance-attributes
    """Elasticsearch destination connector."""

    destination_type: str = ""
    display_name: str = ""
    endpoint: str = ""
    index_name: str = ""
    user_name: str = ""
    password: str = ""
    content_type: str = ""
    custom_header_name: str = ""
    custom_header_value: str = ""
    tls_hostname: str = ""
    ca_cert: str = ""
    client_cert: str = ""
    client_key: str = ""

    def set_destination_type(self) -> None:
        """Set the destination type to Elasticsearch."""
        self.destination_type = DESTINATION_TYPE_ELASTICSEARCH


@dataclass
class S3CompatibleConnector:  # pylint: disable=too-many-instance-attributes
    """S3-compatible destination connector."""

    destination_type: str = ""
    access_key: str = ""
    bucket: str = ""
    display_name: str = ""
    path: str = ""
    region: str = ""
    secret_access_key: str = ""
    endpoint: str = ""

    def set_destination_type(self) -> None:
        """Set the destination type to S3 Compatible."""
        self.destination_type = DESTINATION_TYPE_S3_COMPATIBLE


@dataclass
class TrafficPeakConnector:  # pylint: disable=too-many-instance-attributes
    """TrafficPeak endpoint connector."""

    destination_type: str = ""
    authentication_type: str = ""
    compress_logs: bool = False
    display_name: str = ""
    password: str = ""
    endpoint: str = ""
    user_name: str = ""
    content_type: str = ""
    custom_header_name: str = ""
    custom_header_value: str = ""

    def set_destination_type(self) -> None:
        """Set the destination type to TrafficPeak."""
        self.destination_type = DESTINATION_TYPE_TRAFFIC_PEAK


@dataclass
class DynatraceConnector:
    """Dynatrace destination connector."""

    destination_type: str = ""
    display_name: str = ""
    endpoint: str = ""
    auth_token: str = ""
    custom_header_name: str = ""
    custom_header_value: str = ""

    def set_destination_type(self) -> None:
        """Set the destination type to Dynatrace."""
        self.destination_type = DESTINATION_TYPE_DYNATRACE
