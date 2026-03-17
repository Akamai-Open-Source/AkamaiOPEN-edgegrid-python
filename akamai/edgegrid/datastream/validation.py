"""Request validation functions for DataStream API operations.

Each validator returns a formatted error string on failure, or None when valid.

Mirrors Go ``pkg/datastream`` validation methods from ``stream.go``,
``stream_activation.go``, ``properties.go``, and ``connectors.go``.
Each exported function corresponds to a Go ``Validate()`` method and
enforces the exact same constraints using equivalent Python validation.
"""

import re

from . import models

# Custom header name regex compiled at module level.
# Mirrors Go connectors.go line 262:
#   var customHeaderNameRegexp = regexp.MustCompile("^[A-Za-z0-9_-]+$")
CUSTOM_HEADER_NAME_REGEXP = re.compile(r"^[A-Za-z0-9_-]+$")


def _format_errors(errors: dict[str, str]) -> str:
    """Format validation errors matching Go ozzo-validation output.

    Produces ``"key1: msg1; key2: msg2."`` with keys sorted
    alphabetically, matching Go ``validation.Errors.Error()`` output.
    """
    sorted_keys = sorted(errors.keys())
    parts = [f"{key}: {errors[key]}" for key in sorted_keys]
    return "; ".join(parts) + "."


def _validate_custom_headers(
    connector, errors: dict[str, str]
) -> None:
    """Validate custom header name/value pair.

    Shared validation pattern for Splunk, CustomHTTPS, SumoLogic,
    Loggly, NewRelic, Elasticsearch, TrafficPeak, and Dynatrace
    connectors.  Mirrors Go connectors.go custom-header rules.

    Rules per field (evaluated sequentially, first failure wins):

    * CustomHeaderName: Required.When(value != ""),
      When(name != "", Match(regex))
    * CustomHeaderValue: Required.When(name != "")
    """
    name = connector.custom_header_name
    value = connector.custom_header_value

    # CustomHeaderName: Required.When(value != ""),
    #                   When(name != "", Match(regex))
    if value and not name:
        errors["CustomHeaderName"] = "cannot be blank"
    elif name and not CUSTOM_HEADER_NAME_REGEXP.match(name):
        errors["CustomHeaderName"] = "must be in a valid format"

    # CustomHeaderValue: Required.When(name != "")
    if name and not value:
        errors["CustomHeaderValue"] = "cannot be blank"


def _validate_stream_configuration(  # pylint: disable=too-many-branches
    sc,
    errors: dict[str, str],
    *,
    require_format: bool,
    require_group: bool,
) -> None:
    """Validate StreamConfiguration fields common to create and update.

    Parameters
    ----------
    sc :
        The ``StreamConfiguration`` instance to validate.
    errors :
        Mutable error accumulator (dict mapping field key to message).
    require_format :
        ``True`` for create (Format has Required + In + When clause).
        ``False`` for update (Format has only In).
    require_group :
        ``True`` for create (GroupID has Required + Min(1)).
        ``False`` for update (GroupID must be In(0)).
    """
    dc = sc.delivery_configuration

    # DeliveryConfiguration: Required — no-op for value-type structs
    # in Go ozzo-validation (structs are never considered empty).
    # Frequency: Required — same; no-op for value-type structs.

    # Delimiter: When(format==STRUCTURED, Required, In(SPACE)),
    #            When(format==JSON, Nil)
    if dc.format == models.FORMAT_TYPE_STRUCTURED:
        if dc.delimiter is None:
            errors[
                "StreamConfiguration.DeliveryConfiguration.Delimiter"
            ] = "cannot be blank"
        elif dc.delimiter != models.DELIMITER_TYPE_SPACE:
            errors[
                "StreamConfiguration.DeliveryConfiguration.Delimiter"
            ] = "must be a valid value"
    elif dc.format == models.FORMAT_TYPE_JSON:
        if dc.delimiter is not None:
            errors[
                "StreamConfiguration.DeliveryConfiguration.Delimiter"
            ] = "must be blank"

    # Format
    if require_format:
        # Create: Required, In(STRUCTURED, JSON),
        #         When(delimiter != nil, Required, In(STRUCTURED))
        if not dc.format:
            errors[
                "StreamConfiguration.DeliveryConfiguration.Format"
            ] = "cannot be blank"
        elif dc.format not in (
            models.FORMAT_TYPE_STRUCTURED,
            models.FORMAT_TYPE_JSON,
        ):
            errors[
                "StreamConfiguration.DeliveryConfiguration.Format"
            ] = "must be a valid value"
        elif (
            dc.delimiter is not None
            and dc.format != models.FORMAT_TYPE_STRUCTURED
        ):
            errors[
                "StreamConfiguration.DeliveryConfiguration.Format"
            ] = "must be a valid value"
    else:
        # Update: In(STRUCTURED, JSON) — skips empty values
        if dc.format and dc.format not in (
            models.FORMAT_TYPE_STRUCTURED,
            models.FORMAT_TYPE_JSON,
        ):
            errors[
                "StreamConfiguration.DeliveryConfiguration.Format"
            ] = "must be a valid value"

    # Frequency.IntervalInSeconds: Required, In(30, 60)
    if dc.frequency.interval_in_seconds == 0:
        errors[
            "StreamConfiguration.DeliveryConfiguration"
            ".Frequency.IntervalInSeconds"
        ] = "cannot be blank"
    elif dc.frequency.interval_in_seconds not in (
        models.INTERVAL_IN_SECONDS_30,
        models.INTERVAL_IN_SECONDS_60,
    ):
        errors[
            "StreamConfiguration.DeliveryConfiguration"
            ".Frequency.IntervalInSeconds"
        ] = "must be a valid value"

    # Destination: Required (interface nil check in Go)
    if sc.destination is None:
        errors["StreamConfiguration.Destination"] = "cannot be blank"

    # ContractId: Required
    if not sc.contract_id:
        errors["StreamConfiguration.ContractId"] = "cannot be blank"

    # DatasetFields: Required
    if not sc.dataset_fields:
        errors["StreamConfiguration.DatasetFields"] = "cannot be blank"

    # GroupID
    if require_group:
        # Create: Required, Min(1)
        if sc.group_id == 0:
            errors["StreamConfiguration.GroupID"] = "cannot be blank"
        elif sc.group_id < 1:
            errors["StreamConfiguration.GroupID"] = (
                "must be no less than 1"
            )
    else:
        # Update: In(0) — skip empty, must be 0
        if sc.group_id != 0:
            errors["StreamConfiguration.GroupID"] = (
                "must be a valid value"
            )

    # Properties: Required
    if not sc.properties:
        errors["StreamConfiguration.Properties"] = "cannot be blank"

    # StreamName: Required
    if not sc.stream_name:
        errors["StreamConfiguration.StreamName"] = "cannot be blank"

    # SamplingPercentage: When(!=0, Min(1), Max(100))
    if sc.sampling_percentage != 0:
        if sc.sampling_percentage < 1:
            errors["StreamConfiguration.SamplingPercentage"] = (
                "must be no less than 1"
            )
        elif sc.sampling_percentage > 100:
            errors["StreamConfiguration.SamplingPercentage"] = (
                "must be no greater than 100"
            )


# ---- Stream request validators ------------------------------------------


def validate_create_stream(request) -> str | None:
    """Validate CreateStreamRequest.

    Mirrors Go ``CreateStreamRequest.Validate()``
    (stream.go lines 225-240).

    Returns
    -------
    str | None
        Formatted error string on failure, ``None`` when valid.
    """
    errors: dict[str, str] = {}
    _validate_stream_configuration(
        request.stream_configuration,
        errors,
        require_format=True,
        require_group=True,
    )
    if errors:
        return _format_errors(errors)
    return None


def validate_get_stream(request) -> str | None:
    """Validate GetStreamRequest.

    Mirrors Go ``GetStreamRequest.Validate()``
    (stream.go lines 243-247).

    Returns
    -------
    str | None
        Formatted error string ``stream_id`` is zero, ``None`` when valid.
    """
    errors: dict[str, str] = {}
    if not request.stream_id:
        errors["streamId"] = "cannot be blank"
    if errors:
        return _format_errors(errors)
    return None


def validate_update_stream(request) -> str | None:
    """Validate UpdateStreamRequest.

    Mirrors Go ``UpdateStreamRequest.Validate()``
    (stream.go lines 250-265).

    Differences from create validation:

    * Format: ``In(STRUCTURED, JSON)`` only (no ``Required``).
    * GroupID: ``In(0)`` — cannot modify group on update.

    Returns
    -------
    str | None
        Formatted error string on failure, ``None`` when valid.
    """
    errors: dict[str, str] = {}
    _validate_stream_configuration(
        request.stream_configuration,
        errors,
        require_format=False,
        require_group=False,
    )
    if errors:
        return _format_errors(errors)
    return None


def validate_delete_stream(request) -> str | None:
    """Validate DeleteStreamRequest.

    Mirrors Go ``DeleteStreamRequest.Validate()``
    (stream.go lines 268-272).

    Returns
    -------
    str | None
        Formatted error string ``stream_id`` is zero, ``None`` when valid.
    """
    errors: dict[str, str] = {}
    if not request.stream_id:
        errors["streamId"] = "cannot be blank"
    if errors:
        return _format_errors(errors)
    return None


# ---- Activation request validators --------------------------------------


def validate_activate_stream(request) -> str | None:
    """Validate ActivateStreamRequest.

    Mirrors Go ``ActivateStreamRequest.Validate()``
    (stream_activation.go lines 37-41).

    Returns
    -------
    str | None
        Formatted error string ``stream_id`` is zero, ``None`` when valid.
    """
    errors: dict[str, str] = {}
    if not request.stream_id:
        errors["streamId"] = "cannot be blank"
    if errors:
        return _format_errors(errors)
    return None


def validate_deactivate_stream(request) -> str | None:
    """Validate DeactivateStreamRequest.

    Mirrors Go ``DeactivateStreamRequest.Validate()``
    (stream_activation.go lines 44-48).

    Returns
    -------
    str | None
        Formatted error string ``stream_id`` is zero, ``None`` when valid.
    """
    errors: dict[str, str] = {}
    if not request.stream_id:
        errors["streamId"] = "cannot be blank"
    if errors:
        return _format_errors(errors)
    return None


def validate_get_activation_history(request) -> str | None:
    """Validate GetActivationHistoryRequest.

    Mirrors Go ``GetActivationHistoryRequest.Validate()``
    (stream_activation.go lines 51-55).

    Returns
    -------
    str | None
        Formatted error string ``stream_id`` is zero, ``None`` when valid.
    """
    errors: dict[str, str] = {}
    if not request.stream_id:
        errors["streamId"] = "cannot be blank"
    if errors:
        return _format_errors(errors)
    return None


# ---- Properties request validator ----------------------------------------


def validate_get_properties(request) -> str | None:
    """Validate GetPropertiesRequest.

    Mirrors Go ``GetPropertiesRequest.Validate()``
    (properties.go lines 43-47).

    Returns
    -------
    str | None
        Formatted error string ``group_id`` is zero, ``None`` when valid.
    """
    errors: dict[str, str] = {}
    if not request.group_id:
        errors["GroupId"] = "cannot be blank"
    if errors:
        return _format_errors(errors)
    return None


# ---- Connector validators ------------------------------------------------


def validate_s3_connector(connector) -> str | None:
    """Validate S3Connector.

    Mirrors Go ``S3Connector.Validate()``
    (connectors.go lines 270-280).

    Required fields: DestinationType (S3), AccessKey, Bucket,
    DisplayName, Path, Region, SecretAccessKey.

    Returns
    -------
    str | None
        Formatted error string when one or more required fields
        are missing or invalid, ``None`` when valid.
    """
    errors: dict[str, str] = {}
    if not connector.destination_type:
        errors["DestinationType"] = "cannot be blank"
    elif connector.destination_type != models.DESTINATION_TYPE_S3:
        errors["DestinationType"] = "must be a valid value"
    if not connector.access_key:
        errors["AccessKey"] = "cannot be blank"
    if not connector.bucket:
        errors["Bucket"] = "cannot be blank"
    if not connector.display_name:
        errors["DisplayName"] = "cannot be blank"
    if not connector.path:
        errors["Path"] = "cannot be blank"
    if not connector.region:
        errors["Region"] = "cannot be blank"
    if not connector.secret_access_key:
        errors["SecretAccessKey"] = "cannot be blank"
    if errors:
        return _format_errors(errors)
    return None


def validate_azure_connector(connector) -> str | None:
    """Validate AzureConnector.

    Mirrors Go ``AzureConnector.Validate()``
    (connectors.go lines 288-297).

    Required fields: DestinationType (AZURE), AccessKey, AccountName,
    DisplayName, ContainerName, Path.

    Returns
    -------
    str | None
        Formatted error string when one or more required fields
        are missing or invalid, ``None`` when valid.
    """
    errors: dict[str, str] = {}
    if not connector.destination_type:
        errors["DestinationType"] = "cannot be blank"
    elif connector.destination_type != models.DESTINATION_TYPE_AZURE:
        errors["DestinationType"] = "must be a valid value"
    if not connector.access_key:
        errors["AccessKey"] = "cannot be blank"
    if not connector.account_name:
        errors["AccountName"] = "cannot be blank"
    if not connector.display_name:
        errors["DisplayName"] = "cannot be blank"
    if not connector.container_name:
        errors["ContainerName"] = "cannot be blank"
    if not connector.path:
        errors["Path"] = "cannot be blank"
    if errors:
        return _format_errors(errors)
    return None


def validate_datadog_connector(connector) -> str | None:
    """Validate DatadogConnector.

    Mirrors Go ``DatadogConnector.Validate()``
    (connectors.go lines 305-312).

    Required fields: DestinationType (DATADOG), AuthToken, DisplayName,
    Endpoint.

    Returns
    -------
    str | None
        Formatted error string when one or more required fields
        are missing or invalid, ``None`` when valid.
    """
    errors: dict[str, str] = {}
    if not connector.destination_type:
        errors["DestinationType"] = "cannot be blank"
    elif connector.destination_type != models.DESTINATION_TYPE_DATADOG:
        errors["DestinationType"] = "must be a valid value"
    if not connector.auth_token:
        errors["AuthToken"] = "cannot be blank"
    if not connector.display_name:
        errors["DisplayName"] = "cannot be blank"
    if not connector.endpoint:
        errors["Endpoint"] = "cannot be blank"
    if errors:
        return _format_errors(errors)
    return None


def validate_splunk_connector(connector) -> str | None:
    """Validate SplunkConnector.

    Mirrors Go ``SplunkConnector.Validate()``
    (connectors.go lines 320-329).

    Required fields: DestinationType (SPLUNK), DisplayName,
    EventCollectorToken, Endpoint.
    Conditional: custom header name/value pairing plus regex.

    Returns
    -------
    str | None
        Formatted error string on failure, ``None`` when valid.
    """
    errors: dict[str, str] = {}
    if not connector.destination_type:
        errors["DestinationType"] = "cannot be blank"
    elif connector.destination_type != models.DESTINATION_TYPE_SPLUNK:
        errors["DestinationType"] = "must be a valid value"
    if not connector.display_name:
        errors["DisplayName"] = "cannot be blank"
    if not connector.event_collector_token:
        errors["EventCollectorToken"] = "cannot be blank"
    if not connector.endpoint:
        errors["Endpoint"] = "cannot be blank"
    _validate_custom_headers(connector, errors)
    if errors:
        return _format_errors(errors)
    return None

def validate_gcs_connector(connector) -> str | None:
    """Validate GCSConnector.

    Mirrors Go ``GCSConnector.Validate()``
    (connectors.go lines 337-346).

    Required fields: DestinationType (GCS), Bucket, DisplayName,
    PrivateKey, ProjectId, ServiceAccountName.

    Returns
    -------
    str | None
        Formatted error string when one or more required fields
        are missing or invalid, ``None`` when valid.
    """
    errors: dict[str, str] = {}
    if not connector.destination_type:
        errors["DestinationType"] = "cannot be blank"
    elif connector.destination_type != models.DESTINATION_TYPE_GCS:
        errors["DestinationType"] = "must be a valid value"
    if not connector.bucket:
        errors["Bucket"] = "cannot be blank"
    if not connector.display_name:
        errors["DisplayName"] = "cannot be blank"
    if not connector.private_key:
        errors["PrivateKey"] = "cannot be blank"
    if not connector.project_id:
        errors["ProjectId"] = "cannot be blank"
    if not connector.service_account_name:
        errors["ServiceAccountName"] = "cannot be blank"
    if errors:
        return _format_errors(errors)
    return None


def validate_custom_https_connector(connector) -> str | None:  # pylint: disable=too-many-branches
    """Validate CustomHTTPSConnector.

    Mirrors Go ``CustomHTTPSConnector.Validate()``
    (connectors.go lines 354-365).

    Required fields: DestinationType (HTTPS), AuthenticationType
    (BASIC or NONE), DisplayName, Endpoint.
    Conditional: UserName and Password required when
    AuthenticationType == BASIC.
    Conditional: custom header name/value pairing plus regex.

    Returns
    -------
    str | None
        Formatted error string on failure, ``None`` when valid.
    """
    errors: dict[str, str] = {}
    if not connector.destination_type:
        errors["DestinationType"] = "cannot be blank"
    elif connector.destination_type != models.DESTINATION_TYPE_HTTPS:
        errors["DestinationType"] = "must be a valid value"
    if not connector.authentication_type:
        errors["AuthenticationType"] = "cannot be blank"
    elif connector.authentication_type not in (
        models.AUTHENTICATION_TYPE_BASIC,
        models.AUTHENTICATION_TYPE_NONE,
    ):
        errors["AuthenticationType"] = "must be a valid value"
    if not connector.display_name:
        errors["DisplayName"] = "cannot be blank"
    if not connector.endpoint:
        errors["Endpoint"] = "cannot be blank"
    if connector.authentication_type == models.AUTHENTICATION_TYPE_BASIC:
        if not connector.user_name:
            errors["UserName"] = "cannot be blank"
        if not connector.password:
            errors["Password"] = "cannot be blank"
    _validate_custom_headers(connector, errors)
    if errors:
        return _format_errors(errors)
    return None


def validate_sumo_logic_connector(connector) -> str | None:
    """Validate SumoLogicConnector.

    Mirrors Go ``SumoLogicConnector.Validate()``
    (connectors.go lines 373-382).

    Required fields: DestinationType (SUMO_LOGIC), CollectorCode,
    DisplayName, Endpoint.
    Conditional: custom header name/value pairing plus regex.

    Returns
    -------
    str | None
        Formatted error string on failure, ``None`` when valid.
    """
    errors: dict[str, str] = {}
    if not connector.destination_type:
        errors["DestinationType"] = "cannot be blank"
    elif connector.destination_type != models.DESTINATION_TYPE_SUMO_LOGIC:
        errors["DestinationType"] = "must be a valid value"
    if not connector.collector_code:
        errors["CollectorCode"] = "cannot be blank"
    if not connector.display_name:
        errors["DisplayName"] = "cannot be blank"
    if not connector.endpoint:
        errors["Endpoint"] = "cannot be blank"
    _validate_custom_headers(connector, errors)
    if errors:
        return _format_errors(errors)
    return None


def validate_oracle_cloud_storage_connector(connector) -> str | None:
    """Validate OracleCloudStorageConnector.

    Mirrors Go ``OracleCloudStorageConnector.Validate()``
    (connectors.go lines 390-401).

    Required fields: DestinationType (Oracle_Cloud_Storage), AccessKey,
    Bucket, DisplayName, Namespace, Path, Region, SecretAccessKey.

    Returns
    -------
    str | None
        Formatted error string when one or more required fields
        are missing or invalid, ``None`` when valid.
    """
    errors: dict[str, str] = {}
    if not connector.destination_type:
        errors["DestinationType"] = "cannot be blank"
    elif connector.destination_type != models.DESTINATION_TYPE_ORACLE:
        errors["DestinationType"] = "must be a valid value"
    if not connector.access_key:
        errors["AccessKey"] = "cannot be blank"
    if not connector.bucket:
        errors["Bucket"] = "cannot be blank"
    if not connector.display_name:
        errors["DisplayName"] = "cannot be blank"
    if not connector.namespace:
        errors["Namespace"] = "cannot be blank"
    if not connector.path:
        errors["Path"] = "cannot be blank"
    if not connector.region:
        errors["Region"] = "cannot be blank"
    if not connector.secret_access_key:
        errors["SecretAccessKey"] = "cannot be blank"
    if errors:
        return _format_errors(errors)
    return None


def validate_loggly_connector(connector) -> str | None:
    """Validate LogglyConnector.

    Mirrors Go ``LogglyConnector.Validate()``
    (connectors.go lines 409-418).

    Required fields: DestinationType (LOGGLY), DisplayName, Endpoint,
    AuthToken.
    Conditional: custom header name/value pairing plus regex.

    Returns
    -------
    str | None
        Formatted error string on failure, ``None`` when valid.
    """
    errors: dict[str, str] = {}
    if not connector.destination_type:
        errors["DestinationType"] = "cannot be blank"
    elif connector.destination_type != models.DESTINATION_TYPE_LOGGLY:
        errors["DestinationType"] = "must be a valid value"
    if not connector.display_name:
        errors["DisplayName"] = "cannot be blank"
    if not connector.endpoint:
        errors["Endpoint"] = "cannot be blank"
    if not connector.auth_token:
        errors["AuthToken"] = "cannot be blank"
    _validate_custom_headers(connector, errors)
    if errors:
        return _format_errors(errors)
    return None


def validate_new_relic_connector(connector) -> str | None:
    """Validate NewRelicConnector.

    Mirrors Go ``NewRelicConnector.Validate()``
    (connectors.go lines 426-435).

    Required fields: DestinationType (NEWRELIC), DisplayName, Endpoint,
    AuthToken.
    Conditional: custom header name/value pairing plus regex.

    Returns
    -------
    str | None
        Formatted error string on failure, ``None`` when valid.
    """
    errors: dict[str, str] = {}
    if not connector.destination_type:
        errors["DestinationType"] = "cannot be blank"
    elif connector.destination_type != models.DESTINATION_TYPE_NEW_RELIC:
        errors["DestinationType"] = "must be a valid value"
    if not connector.display_name:
        errors["DisplayName"] = "cannot be blank"
    if not connector.endpoint:
        errors["Endpoint"] = "cannot be blank"
    if not connector.auth_token:
        errors["AuthToken"] = "cannot be blank"
    _validate_custom_headers(connector, errors)
    if errors:
        return _format_errors(errors)
    return None


def validate_elasticsearch_connector(connector) -> str | None:
    """Validate ElasticsearchConnector.

    Mirrors Go ``ElasticsearchConnector.Validate()``
    (connectors.go lines 443-454).

    Required fields: DestinationType (ELASTICSEARCH), DisplayName,
    Endpoint, UserName, Password, IndexName.
    Conditional: custom header name/value pairing plus regex.

    Returns
    -------
    str | None
        Formatted error string on failure, ``None`` when valid.
    """
    errors: dict[str, str] = {}
    if not connector.destination_type:
        errors["DestinationType"] = "cannot be blank"
    elif connector.destination_type != models.DESTINATION_TYPE_ELASTICSEARCH:
        errors["DestinationType"] = "must be a valid value"
    if not connector.display_name:
        errors["DisplayName"] = "cannot be blank"
    if not connector.endpoint:
        errors["Endpoint"] = "cannot be blank"
    if not connector.user_name:
        errors["UserName"] = "cannot be blank"
    if not connector.password:
        errors["Password"] = "cannot be blank"
    if not connector.index_name:
        errors["IndexName"] = "cannot be blank"
    _validate_custom_headers(connector, errors)
    if errors:
        return _format_errors(errors)
    return None


def validate_s3_compatible_connector(connector) -> str | None:
    """Validate S3CompatibleConnector.

    Mirrors Go ``S3CompatibleConnector.Validate()``
    (connectors.go lines 462-472).

    Required fields: DestinationType (S3_COMPATIBLE), AccessKey, Bucket,
    DisplayName, Endpoint, Region, SecretAccessKey.

    Returns
    -------
    str | None
        Formatted error string when one or more required fields
        are missing or invalid, ``None`` when valid.
    """
    errors: dict[str, str] = {}
    if not connector.destination_type:
        errors["DestinationType"] = "cannot be blank"
    elif connector.destination_type != models.DESTINATION_TYPE_S3_COMPATIBLE:
        errors["DestinationType"] = "must be a valid value"
    if not connector.access_key:
        errors["AccessKey"] = "cannot be blank"
    if not connector.bucket:
        errors["Bucket"] = "cannot be blank"
    if not connector.display_name:
        errors["DisplayName"] = "cannot be blank"
    if not connector.endpoint:
        errors["Endpoint"] = "cannot be blank"
    if not connector.region:
        errors["Region"] = "cannot be blank"
    if not connector.secret_access_key:
        errors["SecretAccessKey"] = "cannot be blank"
    if errors:
        return _format_errors(errors)
    return None


def validate_traffic_peak_connector(connector) -> str | None:  # pylint: disable=too-many-branches
    """Validate TrafficPeakConnector.

    Mirrors Go ``TrafficPeakConnector.Validate()``
    (connectors.go lines 480-492).

    Required fields: DestinationType (TRAFFICPEAK),
    AuthenticationType (BASIC), DisplayName, Endpoint,
    UserName, Password, ContentType (JSON or JSON_UTF8).
    Conditional: custom header name/value pairing plus regex.

    Returns
    -------
    str | None
        Formatted error string on failure, ``None`` when valid.
    """
    errors: dict[str, str] = {}
    if not connector.destination_type:
        errors["DestinationType"] = "cannot be blank"
    elif connector.destination_type != models.DESTINATION_TYPE_TRAFFIC_PEAK:
        errors["DestinationType"] = "must be a valid value"
    if not connector.authentication_type:
        errors["AuthenticationType"] = "cannot be blank"
    elif connector.authentication_type != models.AUTHENTICATION_TYPE_BASIC:
        errors["AuthenticationType"] = "must be a valid value"
    if not connector.display_name:
        errors["DisplayName"] = "cannot be blank"
    if not connector.endpoint:
        errors["Endpoint"] = "cannot be blank"
    if not connector.user_name:
        errors["UserName"] = "cannot be blank"
    if not connector.password:
        errors["Password"] = "cannot be blank"
    if not connector.content_type:
        errors["ContentType"] = "cannot be blank"
    elif connector.content_type not in (
        models.TRAFFIC_PEAK_CONTENT_TYPE_JSON,
        models.TRAFFIC_PEAK_CONTENT_TYPE_JSON_UTF8,
    ):
        errors["ContentType"] = "must be a valid value"
    _validate_custom_headers(connector, errors)
    if errors:
        return _format_errors(errors)
    return None


def validate_dynatrace_connector(connector) -> str | None:
    """Validate DynatraceConnector.

    Mirrors Go ``DynatraceConnector.Validate()``
    (connectors.go lines 500-509).

    Required fields: DestinationType (DYNATRACE), DisplayName, Endpoint,
    AuthToken.
    Conditional: custom header name/value pairing plus regex.

    Returns
    -------
    str | None
        Formatted error string on failure, ``None`` when valid.
    """
    errors: dict[str, str] = {}
    if not connector.destination_type:
        errors["DestinationType"] = "cannot be blank"
    elif connector.destination_type != models.DESTINATION_TYPE_DYNATRACE:
        errors["DestinationType"] = "must be a valid value"
    if not connector.display_name:
        errors["DisplayName"] = "cannot be blank"
    if not connector.endpoint:
        errors["Endpoint"] = "cannot be blank"
    if not connector.auth_token:
        errors["AuthToken"] = "cannot be blank"
    _validate_custom_headers(connector, errors)
    if errors:
        return _format_errors(errors)
    return None
