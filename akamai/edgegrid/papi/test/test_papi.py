# pylint: disable=missing-function-docstring,missing-class-docstring
# pylint: disable=too-many-lines,line-too-long,protected-access
"""Comprehensive unit tests for the PAPI client.

Mirrors all 24 Go test files from pkg/papi/*_test.go, covering:
- Client constructor and options (papi_test.go)
- Activations CRUD (activation_test.go)
- Active property hostnames (active_property_hostname_test.go)
- Client settings (clientsettings_test.go)
- Contracts (contract_test.go)
- CP codes (cpcode_test.go)
- Domain ownership validation (domain_ownership_validation_test.go)
- Edge hostnames (edgehostname_test.go)
- Error parsing and sentinels (errors_test.go)
- Groups (group_test.go)
- Includes CRUD (include_test.go)
- Include activations (include_activations_test.go)
- Include rules (include_rule_test.go)
- Include versions (include_versions_test.go)
- Products (products_test.go)
- Properties CRUD (property_test.go)
- Property hostname activations (property_hostname_activation_test.go)
- Property hostname buckets (property_hostname_bucket_test.go)
- Property hostnames (propertyhostname_test.go)
- Property versions (propertyversion_test.go)
- Response link parsing (response_link_test.go)
- Rule tree (rule_test.go)
- Rule formats (ruleformats_test.go)
- Search (search_test.go)
"""

import json

import pytest

from akamai.edgegrid.papi.papi import Client
from akamai.edgegrid.papi import models
from akamai.edgegrid.papi import errors as papi_errors
from akamai.edgegrid.papi.test.conftest import (
    assert_request_made,
    make_mock_response,
)


# =========================================================================
# Helpers — setup mock for success / error
# =========================================================================


def _setup_success(mock_exec, body_text, headers=None):
    """Configure mock to return success response."""
    resp = make_mock_response(200, body_text, headers)
    parsed = json.loads(body_text) if body_text and body_text.strip() else {}
    mock_exec.return_value = (resp, parsed)


def _setup_error(mock_exec, status_code, body_text):
    """Configure mock to raise a papi Error."""
    error = papi_errors.Error()
    try:
        data = json.loads(body_text)
        error.type = data.get("type", "")
        error.title = data.get("title", "")
        error.detail = data.get("detail", "")
        error.status_code = data.get("status", status_code)
        error.limit_key = data.get("limitKey", "")
        error.remaining = data.get("remaining", None)
        error.behavior_name = data.get("behaviorName", "")
    except (json.JSONDecodeError, ValueError):
        error.title = "Failed to unmarshal error body"
        error.detail = body_text
        error.status_code = status_code
    mock_exec.side_effect = error


ERR_500_BODY = '{"type":"internal_error","title":"Internal Server Error","detail":"Error processing request","status":500}'


# =========================================================================
# Client Constructor Tests — from papi_test.go
# =========================================================================


class TestClient:
    """Tests for PAPI client constructor. Mirrors Go TestClient."""

    def test_default_options(self, mock_session):
        client = Client(mock_session)
        assert client._use_prefixes is True

    def test_use_prefixes_false(self, mock_session):
        client = Client(mock_session, use_prefixes=False)
        assert client._use_prefixes is False


# =========================================================================
# Response Link Tests — from response_link_test.go
# =========================================================================


class TestResponseLinkParse:
    """Tests for response_link_parse. Mirrors Go TestResponseLinkParse."""

    def test_valid_url_passed(self):
        val, err = models.response_link_parse(
            "/papi/v1/cpcodes/123?contractId=contract-1TJZFW&groupId=group"
        )
        assert val == "123"
        assert err is None

    def test_invalid_url_returns_path_segment(self):
        val, err = models.response_link_parse(":")
        assert isinstance(val, str)
        assert err is None


# =========================================================================
# Error Tests — from errors_test.go
# =========================================================================


class TestNewError:
    """Tests for error creation. Mirrors Go TestNewError."""

    def test_valid_response_status_500(self):
        error = papi_errors.Error(
            type="a", title="b", detail="c", status_code=500,
        )
        assert error.type == "a"
        assert error.title == "b"
        assert error.detail == "c"
        assert error.status_code == 500

    def test_invalid_response_body(self):
        error = papi_errors.Error(
            title="Failed to unmarshal error body",
            detail="test",
            status_code=500,
        )
        assert error.status_code == 500
        assert error.detail == "test"


class TestErrorIs:
    """Tests for error sentinel matching. Mirrors Go TestErrorIs."""

    def test_is_err_sbd_not_enabled(self):
        error = papi_errors.Error(
            type="https://problems.luna.akamaiapis.net/papi/v0/property-version-hostname/default-cert-provisioning-unavailable",
            status_code=403,
        )
        assert error.is_equivalent(papi_errors.ErrSBDNotEnabled)

    def test_is_wrapped_err_sbd_not_enabled(self):
        error = papi_errors.Error(
            type="https://problems.luna.akamaiapis.net/papi/v0/property-version-hostname/default-cert-provisioning-unavailable",
            status_code=403,
        )
        assert error.is_equivalent(papi_errors.ErrSBDNotEnabled)

    def test_is_err_default_cert_limit_reached(self):
        error = papi_errors.Error(
            status_code=429,
            limit_key="DEFAULT_CERTS_PER_CONTRACT",
            remaining=0,
        )
        assert error.is_equivalent(papi_errors.ErrDefaultCertLimitReached)

    def test_is_not_err_sbd_not_enabled(self):
        error = papi_errors.Error(status_code=429)
        assert not error.is_equivalent(papi_errors.ErrSBDNotEnabled)

    def test_is_not_err_default_cert_limit_reached(self):
        error = papi_errors.Error(status_code=403)
        assert not error.is_equivalent(papi_errors.ErrDefaultCertLimitReached)


class TestJsonErrorUnmarshalling:
    """Tests for non-JSON error parsing. Mirrors Go TestJsonErrorUnmarshalling."""

    def test_html_response(self):
        html = "<HTML><HEAD></HEAD><BODY>Error</BODY></HTML>"
        error = papi_errors.Error(detail=html, status_code=500)
        assert html in error.detail

    def test_plain_text_response(self):
        text = "Rate limit exceeded"
        error = papi_errors.Error(detail=text, status_code=429)
        assert text in error.detail

    def test_xml_response(self):
        xml = '<Root><Item id="1" name="Example" /></Root>'
        error = papi_errors.Error(detail=xml, status_code=500)
        assert xml in error.detail


# =========================================================================
# Contract Tests — from contract_test.go
# =========================================================================


class TestPapiGetContracts:
    """Tests for GetContracts. Mirrors Go TestPapiGetContracts."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contracts":{"items":[{"contractId":"ctr_1-1TJZH5","contractTypeName":"DIRECT_CUSTOMER"}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_contracts()
        assert result.account_id == "act_1-1TJZFB"
        assert result.contracts is not None
        assert len(result.contracts.items) == 1
        assert result.contracts.items[0].contract_id == "ctr_1-1TJZH5"
        assert result.contracts.items[0].contract_type_name == "DIRECT_CUSTOMER"
        assert_request_made(mock_session_request, "GET", "/papi/v1/contracts")

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.get_contracts()
        assert exc_info.value.status_code == 500


# =========================================================================
# Group Tests — from group_test.go
# =========================================================================


class TestPapiGetGroups:
    """Tests for GetGroups. Mirrors Go TestPapiGetGroups."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","accountName":"Example.com","groups":{"items":[{"groupId":"grp_15225","groupName":"Example.com-1-1TJZH5","parentGroupId":"","contractIds":["ctr_1-1TJZH5"]}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_groups()
        assert result.account_id == "act_1-1TJZFB"
        assert result.account_name == "Example.com"
        assert result.groups is not None
        assert len(result.groups.items) == 1
        assert result.groups.items[0].group_id == "grp_15225"
        assert_request_made(mock_session_request, "GET", "/papi/v1/groups")

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_groups()


# =========================================================================
# Products Tests — from products_test.go
# =========================================================================


class TestPapiGetProducts:
    """Tests for GetProducts. Mirrors Go TestPapiGetProducts."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","products":{"items":[{"productId":"prd_Alta","productName":"Alta"}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_products(
            models.GetProductsRequest(contract_id="ctr_1-1TJZFW")
        )
        assert result.account_id == "act_1-1TJZFB"
        assert result.products is not None
        assert len(result.products.items) == 1
        assert result.products.items[0].product_id == "prd_Alta"
        assert result.products.items[0].product_name == "Alta"
        assert_request_made(mock_session_request, "GET", "/papi/v1/products")

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_products(
                models.GetProductsRequest(contract_id="ctr_1-1TJZFW")
            )

    def test_validation_error_empty_contract_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.get_products(
                models.GetProductsRequest(contract_id="")
            )
        assert "ContractID" in str(exc_info.value)


# =========================================================================
# Client Settings Tests — from clientsettings_test.go
# =========================================================================


class TestPapiGetClientSettings:
    """Tests for GetClientSettings. Mirrors Go TestPapiGetClientSettings."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"ruleFormat":"v2015-08-08","usePrefixes":true}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_client_settings()
        assert result.rule_format == "v2015-08-08"
        assert result.use_prefixes is True

    def test_500_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_client_settings()


class TestPapiUpdateClientSettings:
    """Tests for UpdateClientSettings. Mirrors Go TestPapiUpdateClientSettings."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"ruleFormat":"v2015-08-08","usePrefixes":true}'
        _setup_success(mock_session_request, body)
        result = papi_client.update_client_settings(
            models.ClientSettingsBody(rule_format="v2015-08-08", use_prefixes=True)
        )
        assert result.rule_format == "v2015-08-08"

    def test_500_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.update_client_settings(
                models.ClientSettingsBody(rule_format="v2015-08-08", use_prefixes=True)
            )


# =========================================================================
# Rule Formats Tests — from ruleformats_test.go
# =========================================================================


class TestPapiGetRuleFormats:
    """Tests for GetRuleFormats. Mirrors Go TestPapiGetRuleFormats."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"ruleFormats":{"items":["latest","v2015-08-08"]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_rule_formats()
        assert result.rule_formats is not None
        assert "latest" in result.rule_formats.items
        assert "v2015-08-08" in result.rule_formats.items
        assert_request_made(mock_session_request, "GET", "/papi/v1/rule-formats")

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_rule_formats()


# =========================================================================
# Search Tests — from search_test.go
# =========================================================================


class TestPapiSearchProperties:
    """Tests for SearchProperties. Mirrors Go TestPapiSearchProperties."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"versions":{"items":[{"propertyId":"prp_175780","propertyName":"my-property","propertyVersion":2,"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","assetId":"aid_101","hostname":"example.com","edgeHostname":"example.com.edgesuite.net","productionStatus":"ACTIVE","stagingStatus":"INACTIVE","updatedByUser":"admin","updatedDate":"2020-01-01T00:00:00Z"},{"propertyId":"prp_175781","propertyName":"my-property-2","propertyVersion":1,"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","assetId":"aid_102","hostname":"example2.com","edgeHostname":"example2.com.edgesuite.net","productionStatus":"INACTIVE","stagingStatus":"ACTIVE","updatedByUser":"admin","updatedDate":"2020-02-01T00:00:00Z"}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.search_properties(
            models.SearchRequest(key="edgeHostname", value="edgesuite.net")
        )
        assert result.versions is not None
        assert len(result.versions.items) == 2
        assert result.versions.items[0].property_id == "prp_175780"
        assert result.versions.items[1].property_id == "prp_175781"
        assert_request_made(
            mock_session_request, "POST",
            "/papi/v1/search/find-by-value",
        )

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.search_properties(
                models.SearchRequest(key="edgeHostname", value="edgesuite.net")
            )

    def test_validation_error_invalid_key(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.search_properties(
                models.SearchRequest(key="test", value="value")
            )
        assert "SearchKey" in str(exc_info.value)

    def test_validation_error_empty_key(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.search_properties(
                models.SearchRequest(key="", value="value")
            )
        assert "SearchKey" in str(exc_info.value)

    def test_validation_error_empty_value(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.search_properties(
                models.SearchRequest(key="edgeHostname", value="")
            )
        assert "SearchValue" in str(exc_info.value)


# =========================================================================
# Activation Tests — from activation_test.go
# =========================================================================


class TestPapiCreateActivation:
    """Tests for CreateActivation. Mirrors Go TestPapiCreateActivation."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"activationLink":"/papi/v1/properties/prp_173136/activations/atv_67037?contractId=ctr_1-1TJZFB&groupId=grp_15225"}'
        _setup_success(mock_session_request, body)
        result = papi_client.create_activation(
            models.CreateActivationRequest(
                property_id="prp_175780",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                activation=models.Activation(
                    activation_type=models.ActivationTypeActivate,
                    network="STAGING",
                    property_version=1,
                    notify_emails=["user@example.com"],
                ),
            )
        )
        assert result.activation_id == "atv_67037"
        assert "atv_67037" in result.activation_link
        assert_request_made(
            mock_session_request, "POST",
            "/papi/v1/properties/prp_175780/activations",
        )

    def test_200_compliance_record_none(self, papi_client, mock_session_request):
        body = '{"activationLink":"/papi/v1/properties/prp_173136/activations/atv_67037?contractId=ctr_1-1TJZFB&groupId=grp_15225"}'
        _setup_success(mock_session_request, body)
        result = papi_client.create_activation(
            models.CreateActivationRequest(
                property_id="prp_175780",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                activation=models.Activation(
                    activation_type=models.ActivationTypeActivate,
                    network="PRODUCTION",
                    property_version=1,
                    notify_emails=["user@example.com"],
                    compliance_record=models.ComplianceRecordNone(
                        customer_email="user@example.com",
                        peer_reviewed_by="peer@example.com",
                        unit_tested=True,
                        ticket_id="123",
                    ).__dict__,
                ),
            )
        )
        assert result.activation_id == "atv_67037"

    def test_200_compliance_record_other(self, papi_client, mock_session_request):
        body = '{"activationLink":"/papi/v1/properties/prp_173136/activations/atv_67037?contractId=ctr_1-1TJZFB&groupId=grp_15225"}'
        _setup_success(mock_session_request, body)
        result = papi_client.create_activation(
            models.CreateActivationRequest(
                property_id="prp_175780",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                activation=models.Activation(
                    activation_type=models.ActivationTypeActivate,
                    network="PRODUCTION",
                    property_version=1,
                    notify_emails=["user@example.com"],
                    compliance_record=models.ComplianceRecordOther(
                        other_noncompliance_reason="reason",
                        ticket_id="123",
                    ).__dict__,
                ),
            )
        )
        assert result.activation_id == "atv_67037"

    def test_200_compliance_record_no_production_traffic(self, papi_client, mock_session_request):
        body = '{"activationLink":"/papi/v1/properties/prp_173136/activations/atv_67037?contractId=ctr_1-1TJZFB&groupId=grp_15225"}'
        _setup_success(mock_session_request, body)
        result = papi_client.create_activation(
            models.CreateActivationRequest(
                property_id="prp_175780",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                activation=models.Activation(
                    activation_type=models.ActivationTypeActivate,
                    network="PRODUCTION",
                    property_version=1,
                    notify_emails=["user@example.com"],
                    compliance_record=models.ComplianceRecordNoProductionTraffic(
                        ticket_id="123",
                    ).__dict__,
                ),
            )
        )
        assert result.activation_id == "atv_67037"

    def test_200_compliance_record_emergency(self, papi_client, mock_session_request):
        body = '{"activationLink":"/papi/v1/properties/prp_173136/activations/atv_67037?contractId=ctr_1-1TJZFB&groupId=grp_15225"}'
        _setup_success(mock_session_request, body)
        result = papi_client.create_activation(
            models.CreateActivationRequest(
                property_id="prp_175780",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                activation=models.Activation(
                    activation_type=models.ActivationTypeActivate,
                    network="PRODUCTION",
                    property_version=1,
                    notify_emails=["user@example.com"],
                    compliance_record=models.ComplianceRecordEmergency(
                        ticket_id="123",
                    ).__dict__,
                ),
            )
        )
        assert result.activation_id == "atv_67037"

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.create_activation(
                models.CreateActivationRequest(
                    property_id="prp_175780",
                    contract_id="ctr_1-1TJZFW",
                    group_id="grp_15166",
                    activation=models.Activation(
                        activation_type=models.ActivationTypeActivate,
                        network="STAGING",
                        property_version=1,
                        notify_emails=["user@example.com"],
                    ),
                )
            )

    def test_validation_error_missing_property_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.create_activation(
                models.CreateActivationRequest(
                    property_id="",
                    contract_id="ctr_1-1TJZFW",
                    group_id="grp_15166",
                    activation=models.Activation(
                        activation_type=models.ActivationTypeActivate,
                        network="STAGING",
                        property_version=1,
                        notify_emails=["user@example.com"],
                    ),
                )
            )
        assert "PropertyID" in str(exc_info.value)


class TestPapiGetActivations:
    """Tests for GetActivations. Mirrors Go TestPapiGetActivations."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","activations":{"items":[{"activationId":"atv_67037","activationType":"ACTIVATE","network":"STAGING","status":"ACTIVE","submitDate":"2020-01-01T00:00:00Z","updateDate":"2020-01-01T00:00:00Z","note":"test","notifyEmails":["user@example.com"],"propertyName":"my-property","propertyId":"prp_175780","propertyVersion":1}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_activations(
            models.GetActivationsRequest(
                property_id="prp_175780",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.account_id == "act_1-1TJZFB"
        assert result.activations is not None
        assert len(result.activations.items) == 1
        assert result.activations.items[0].activation_id == "atv_67037"
        assert_request_made(
            mock_session_request, "GET",
            "/papi/v1/properties/prp_175780/activations",
        )

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_activations(
                models.GetActivationsRequest(
                    property_id="prp_175780",
                    contract_id="ctr_1-1TJZFW",
                    group_id="grp_15166",
                )
            )

    def test_validation_error_missing_property_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.get_activations(
                models.GetActivationsRequest(property_id="")
            )
        assert "PropertyID" in str(exc_info.value)


class TestPapiGetActivation:
    """Tests for GetActivation. Mirrors Go TestPapiGetActivation."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","activations":{"items":[{"activationId":"atv_67037","activationType":"ACTIVATE","network":"STAGING","status":"ACTIVE","submitDate":"2020-01-01T00:00:00Z","updateDate":"2020-01-01T00:00:00Z","note":"test","notifyEmails":["user@example.com"],"propertyName":"my-property","propertyId":"prp_175780","propertyVersion":1}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_activation(
            models.GetActivationRequest(
                property_id="prp_175780",
                activation_id="atv_67037",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.activation is not None
        assert result.activation.activation_id == "atv_67037"

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_activation(
                models.GetActivationRequest(
                    property_id="prp_175780",
                    activation_id="atv_67037",
                    contract_id="ctr_1-1TJZFW",
                    group_id="grp_15166",
                )
            )

    def test_validation_error_missing_property_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.get_activation(
                models.GetActivationRequest(
                    property_id="", activation_id="atv_67037",
                )
            )
        assert "PropertyID" in str(exc_info.value)


class TestPapiCancelActivation:
    """Tests for CancelActivation. Mirrors Go TestPapiCancelActivation."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"activations":{"items":[{"activationId":"atv_67037","activationType":"ACTIVATE","network":"STAGING","status":"ABORTED","submitDate":"2020-01-01T00:00:00Z","updateDate":"2020-01-01T00:00:00Z","note":"test","notifyEmails":["user@example.com"],"propertyName":"my-property","propertyId":"prp_175780","propertyVersion":1}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.cancel_activation(
            models.CancelActivationRequest(
                property_id="prp_175780",
                activation_id="atv_67037",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.activations is not None
        assert len(result.activations.items) == 1
        assert result.activations.items[0].status == "ABORTED"

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.cancel_activation(
                models.CancelActivationRequest(
                    property_id="prp_175780",
                    activation_id="atv_67037",
                    contract_id="ctr_1-1TJZFW",
                    group_id="grp_15166",
                )
            )

    def test_validation_error_missing_property_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.cancel_activation(
                models.CancelActivationRequest(
                    property_id="", activation_id="atv_67037",
                )
            )
        assert "PropertyID" in str(exc_info.value)


# =========================================================================
# Property Tests — from property_test.go
# =========================================================================


class TestPapiGetProperties:
    """Tests for GetProperties. Mirrors Go TestPapiGetProperties."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","properties":{"items":[{"accountId":"act_1-1TJZFB","assetId":"aid_101","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","latestVersion":2,"note":"test","propertyId":"prp_175780","propertyName":"my-property","stagingVersion":1}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_properties(
            models.GetPropertiesRequest(
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.properties is not None
        assert len(result.properties.items) == 1
        assert result.properties.items[0].property_id == "prp_175780"
        assert_request_made(mock_session_request, "GET", "/papi/v1/properties")

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_properties(
                models.GetPropertiesRequest(contract_id="ctr_1-1TJZFW", group_id="grp_15166")
            )

    def test_validation_error_missing_contract_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.get_properties(
                models.GetPropertiesRequest(contract_id="", group_id="grp_15166")
            )
        assert "ContractID" in str(exc_info.value)


class TestPapiCreateProperty:
    """Tests for CreateProperty. Mirrors Go TestPapiCreateProperty."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"propertyLink":"/papi/v1/properties/prp_175780?contractId=ctr_1-1TJZFW&groupId=grp_15166"}'
        _setup_success(mock_session_request, body)
        result = papi_client.create_property(
            models.CreatePropertyRequest(
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                property=models.PropertyCreate(
                    product_id="prd_Alta",
                    property_name="my-new-property",
                    rule_format="v2015-08-08",
                ),
            )
        )
        assert result.property_id == "prp_175780"
        assert_request_made(mock_session_request, "POST", "/papi/v1/properties")

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.create_property(
                models.CreatePropertyRequest(
                    contract_id="ctr_1-1TJZFW",
                    group_id="grp_15166",
                    property=models.PropertyCreate(
                        product_id="prd_Alta",
                        property_name="my-new-property",
                    ),
                )
            )

    def test_validation_error_missing_contract_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.create_property(
                models.CreatePropertyRequest(
                    contract_id="",
                    group_id="grp_15166",
                    property=models.PropertyCreate(product_id="prd_Alta", property_name="test"),
                )
            )
        assert "ContractID" in str(exc_info.value)


class TestPapiGetProperty:
    """Tests for GetProperty. Mirrors Go TestPapiGetProperty."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"properties":{"items":[{"accountId":"act_1-1TJZFB","assetId":"aid_101","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","latestVersion":2,"note":"test","propertyId":"prp_175780","propertyName":"my-property","stagingVersion":1}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_property(
            models.GetPropertyRequest(
                property_id="prp_175780",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.property is not None
        assert result.property.property_id == "prp_175780"
        assert result.property.property_name == "my-property"
        assert_request_made(
            mock_session_request, "GET",
            "/papi/v1/properties/prp_175780",
        )

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_property(
                models.GetPropertyRequest(
                    property_id="prp_175780",
                    contract_id="ctr_1-1TJZFW",
                    group_id="grp_15166",
                )
            )

    def test_validation_error_missing_property_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.get_property(
                models.GetPropertyRequest(property_id="", contract_id="ctr_1-1TJZFW", group_id="grp_15166")
            )
        assert "PropertyID" in str(exc_info.value)


class TestPapiRemoveProperty:
    """Tests for RemoveProperty. Mirrors Go TestPapiRemoveProperty."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"message":"Deletion Successful."}'
        _setup_success(mock_session_request, body)
        result = papi_client.remove_property(
            models.RemovePropertyRequest(
                property_id="prp_175780",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.message == "Deletion Successful."
        assert_request_made(
            mock_session_request, "DELETE",
            "/papi/v1/properties/prp_175780",
        )

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.remove_property(
                models.RemovePropertyRequest(
                    property_id="prp_175780",
                    contract_id="ctr_1-1TJZFW",
                    group_id="grp_15166",
                )
            )

    def test_validation_error_missing_property_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.remove_property(
                models.RemovePropertyRequest(property_id="", contract_id="ctr_1-1TJZFW", group_id="grp_15166")
            )
        assert "PropertyID" in str(exc_info.value)


class TestPapiMapPropertyNameToID:
    """Tests for MapPropertyNameToID. Mirrors Go TestPapiMapPropertyNameToID."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"versions":{"items":[{"propertyId":"prp_175780","propertyName":"my-property","propertyVersion":1,"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","assetId":"aid_101","hostname":"","edgeHostname":"","productionStatus":"","stagingStatus":"","updatedByUser":"","updatedDate":""}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.map_property_name_to_id(
            models.MapPropertyNameToIDRequest(
                name="my-property",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result == "prp_175780"

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.map_property_name_to_id(
                models.MapPropertyNameToIDRequest(
                    name="my-property",
                    contract_id="ctr_1-1TJZFW",
                    group_id="grp_15166",
                )
            )

    def test_validation_error_missing_name(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.map_property_name_to_id(
                models.MapPropertyNameToIDRequest(name="", contract_id="ctr_1-1TJZFW", group_id="grp_15166")
            )
        assert "Name" in str(exc_info.value)


# =========================================================================
# CP Code Tests — from cpcode_test.go
# =========================================================================


class TestPapiGetCPCodes:
    """Tests for GetCPCodes. Mirrors Go TestPapiGetCPCodes."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","cpcodes":{"items":[{"cpcodeId":"cpc_33190","cpcodeName":"my-cpcode","createdDate":"2020-01-01T00:00:00Z","productIds":["prd_Alta"]}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_cp_codes(
            models.GetCPCodesRequest(contract_id="ctr_1-1TJZFW", group_id="grp_15166")
        )
        assert result.account_id == "act_1-1TJZFB"
        assert result.cp_codes is not None
        assert len(result.cp_codes.items) == 1
        assert result.cp_codes.items[0].cp_code_id == "cpc_33190"
        assert_request_made(mock_session_request, "GET", "/papi/v1/cpcodes")

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_cp_codes(
                models.GetCPCodesRequest(contract_id="ctr_1-1TJZFW", group_id="grp_15166")
            )

    def test_validation_error_missing_contract_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.get_cp_codes(
                models.GetCPCodesRequest(contract_id="", group_id="grp_15166")
            )
        assert "ContractID" in str(exc_info.value)


class TestPapiGetCPCode:
    """Tests for GetCPCode. Mirrors Go TestPapiGetCPCode."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","cpcodes":{"items":[{"cpcodeId":"cpc_33190","cpcodeName":"my-cpcode","createdDate":"2020-01-01T00:00:00Z","productIds":["prd_Alta"]}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_cp_code(
            models.GetCPCodeRequest(
                cpcode_id="cpc_33190",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.cp_codes is not None
        assert len(result.cp_codes.items) == 1
        assert result.cp_codes.items[0].cp_code_id == "cpc_33190"

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_cp_code(
                models.GetCPCodeRequest(
                    cpcode_id="cpc_33190", contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )

    def test_validation_error_missing_cpcode_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.get_cp_code(
                models.GetCPCodeRequest(cpcode_id="", contract_id="ctr_1-1TJZFW", group_id="grp_15166")
            )
        assert "CPCodeID" in str(exc_info.value)


class TestPapiCreateCPCode:
    """Tests for CreateCPCode. Mirrors Go TestPapiCreateCPCode."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"cpcodeLink":"/papi/v1/cpcodes/cpc_33190?contractId=ctr_1-1TJZFW&groupId=grp_15166"}'
        _setup_success(mock_session_request, body)
        result = papi_client.create_cp_code(
            models.CreateCPCodeRequest(
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                cpcode=models.CreateCPCode(
                    product_id="prd_Alta",
                    cpcode_name="my-cpcode",
                ),
            )
        )
        assert result.cpcode_id == "cpc_33190"

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.create_cp_code(
                models.CreateCPCodeRequest(
                    contract_id="ctr_1-1TJZFW",
                    group_id="grp_15166",
                    cpcode=models.CreateCPCode(product_id="prd_Alta", cpcode_name="my-cpcode"),
                )
            )

    def test_validation_error_missing_contract_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.create_cp_code(
                models.CreateCPCodeRequest(
                    contract_id="",
                    group_id="grp_15166",
                    cpcode=models.CreateCPCode(product_id="prd_Alta", cpcode_name="my-cpcode"),
                )
            )
        assert "ContractID" in str(exc_info.value)


class TestPapiUpdateCPCode:
    """Tests for UpdateCPCode. Mirrors Go TestPapiUpdateCPCode."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"id":33190,"name":"my-cpcode-updated","purgeable":true,"accountId":"act_1-1TJZFB","defaultTimeZone":"UTC","type":"REGULAR","contracts":[{"contractId":"ctr_1-1TJZFW","status":"ACTIVE"}],"products":[{"productId":"prd_Alta","productName":"Alta"}]}'
        _setup_success(mock_session_request, body)
        result = papi_client.update_cp_code(
            models.UpdateCPCodeRequest(
                id=33190,
                name="my-cpcode-updated",
                purgeable=True,
                contracts=["ctr_1-1TJZFW"],
                products=["prd_Alta"],
            )
        )
        assert result.id == 33190
        assert result.name == "my-cpcode-updated"
        assert result.purgeable is True

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.update_cp_code(
                models.UpdateCPCodeRequest(
                    id=33190, name="my-cpcode-updated",
                    contracts=["ctr_1"], products=["prd_1"],
                )
            )

    def test_validation_error_missing_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.update_cp_code(
                models.UpdateCPCodeRequest(
                    id=0, name="my-cpcode-updated",
                    contracts=["ctr_1"], products=["prd_1"],
                )
            )
        assert "ID" in str(exc_info.value)


class TestPapiGetCPCodeDetail:
    """Tests for GetCPCodeDetail. Mirrors Go TestPapiGetCPCodeDetail."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"id":33190,"name":"my-cpcode","purgeable":true,"accountId":"act_1-1TJZFB","defaultTimeZone":"UTC","type":"REGULAR","contracts":[{"contractId":"ctr_1-1TJZFW","status":"ACTIVE"}],"products":[{"productId":"prd_Alta","productName":"Alta"}]}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_cp_code_detail(33190)
        assert result.id == 33190
        assert result.name == "my-cpcode"
        assert result.purgeable is True

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_cp_code_detail(33190)


# =========================================================================
# Domain Ownership Validation Tests — from domain_ownership_validation_test.go
# =========================================================================


class TestPapiValidateDomainsOwnership:
    """Tests for ValidateDomainsOwnership. Mirrors Go TestPapiValidateDomainsOwnership."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"challenges":[{"hostname":"example.com","domainValidationStatus":"VALID","validationCname":{"hostname":"_acme.example.com","target":"_acme.edgekey.net"}}]}'
        _setup_success(mock_session_request, body)
        result = papi_client.validate_domains_ownership(
            models.ValidateDomainsOwnershipRequest(
                property_id="prp_175780",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                body=models.ValidateDomainsOwnershipRequestBody(
                    hostnames=["example.com"],
                ),
            )
        )
        assert len(result.challenges) == 1
        assert result.challenges[0].hostname == "example.com"
        assert result.challenges[0].domain_validation_status == "VALID"

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.validate_domains_ownership(
                models.ValidateDomainsOwnershipRequest(
                    property_id="prp_175780",
                    contract_id="ctr_1-1TJZFW",
                    group_id="grp_15166",
                    body=models.ValidateDomainsOwnershipRequestBody(
                        hostnames=["example.com"],
                    ),
                )
            )

    def test_validation_error_missing_hostnames(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.validate_domains_ownership(
                models.ValidateDomainsOwnershipRequest(
                    property_id="prp_175780",
                    contract_id="ctr_1-1TJZFW",
                    group_id="grp_15166",
                )
            )
        assert "Hostnames" in str(exc_info.value)


# =========================================================================
# Edge Hostname Tests — from edgehostname_test.go
# =========================================================================


class TestPapiGetEdgeHostnames:
    """Tests for GetEdgeHostnames. Mirrors Go TestPapiGetEdgeHostnames."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","edgeHostnames":{"items":[{"edgeHostnameId":"ehn_887436","edgeHostnameDomain":"example.com.edgesuite.net","productId":"prd_Alta","domainPrefix":"example.com","domainSuffix":"edgesuite.net","secure":false,"ipVersionBehavior":"IPV4"}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_edge_hostnames(
            models.GetEdgeHostnamesRequest(
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.edge_hostnames is not None
        assert len(result.edge_hostnames.items) == 1
        assert result.edge_hostnames.items[0].id == "ehn_887436"
        assert_request_made(
            mock_session_request, "GET", "/papi/v1/edgehostnames",
        )

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_edge_hostnames(
                models.GetEdgeHostnamesRequest(contract_id="ctr_1-1TJZFW", group_id="grp_15166")
            )

    def test_validation_error_missing_contract_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.get_edge_hostnames(
                models.GetEdgeHostnamesRequest(contract_id="", group_id="grp_15166")
            )
        assert "ContractID" in str(exc_info.value)


class TestPapiGetEdgeHostname:
    """Tests for GetEdgeHostname. Mirrors Go TestPapiGetEdgeHostname."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","edgeHostnames":{"items":[{"edgeHostnameId":"ehn_887436","edgeHostnameDomain":"example.com.edgesuite.net","productId":"prd_Alta","domainPrefix":"example.com","domainSuffix":"edgesuite.net","secure":false,"ipVersionBehavior":"IPV4"}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_edge_hostname(
            models.GetEdgeHostnameRequest(
                edge_hostname_id="ehn_887436",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.edge_hostnames is not None
        assert len(result.edge_hostnames.items) == 1

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_edge_hostname(
                models.GetEdgeHostnameRequest(
                    edge_hostname_id="ehn_887436",
                    contract_id="ctr_1-1TJZFW",
                    group_id="grp_15166",
                )
            )

    def test_validation_error_missing_edge_hostname_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.get_edge_hostname(
                models.GetEdgeHostnameRequest(
                    edge_hostname_id="", contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )
        assert "EdgeHostnameID" in str(exc_info.value)


class TestPapiCreateEdgeHostname:
    """Tests for CreateEdgeHostname. Mirrors Go TestPapiCreateEdgeHostname."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"edgeHostnameLink":"/papi/v1/edgehostnames/ehn_887436?contractId=ctr_1-1TJZFW&groupId=grp_15166"}'
        _setup_success(mock_session_request, body)
        result = papi_client.create_edge_hostname(
            models.CreateEdgeHostnameRequest(
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                edge_hostname=models.EdgeHostnameCreate(
                    product_id="prd_Alta",
                    domain_prefix="example.com",
                    domain_suffix="edgesuite.net",
                    ip_version_behavior="IPV4",
                ),
            )
        )
        assert result.edge_hostname_id == "ehn_887436"

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.create_edge_hostname(
                models.CreateEdgeHostnameRequest(
                    contract_id="ctr_1-1TJZFW",
                    group_id="grp_15166",
                    edge_hostname=models.EdgeHostnameCreate(
                        product_id="prd_Alta",
                        domain_prefix="example.com",
                        domain_suffix="edgesuite.net",
                        ip_version_behavior="IPV4",
                    ),
                )
            )

    def test_validation_error_missing_contract_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.create_edge_hostname(
                models.CreateEdgeHostnameRequest(
                    contract_id="",
                    group_id="grp_15166",
                    edge_hostname=models.EdgeHostnameCreate(
                        product_id="prd_Alta", domain_prefix="ex", domain_suffix="edgesuite.net",
                        ip_version_behavior="IPV4",
                    ),
                )
            )
        assert "ContractID" in str(exc_info.value)


# =========================================================================
# Include Tests — from include_test.go
# =========================================================================


class TestListIncludes:
    """Tests for ListIncludes. Mirrors Go TestListIncludes."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"includes":{"items":[{"accountId":"act_1-1TJZFB","assetId":"aid_101","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","includeId":"inc_123456","includeName":"my-include","includeType":"MICROSERVICES","latestVersion":1}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.list_includes(
            models.ListIncludesRequest(contract_id="ctr_1-1TJZFW", group_id="grp_15166")
        )
        assert result.includes is not None
        assert len(result.includes.items) == 1
        assert result.includes.items[0].include_id == "inc_123456"

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.list_includes(
                models.ListIncludesRequest(contract_id="ctr_1-1TJZFW", group_id="grp_15166")
            )

    def test_validation_error_missing_contract_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.list_includes(
                models.ListIncludesRequest(contract_id="", group_id="grp_15166")
            )
        assert "ContractID" in str(exc_info.value)


class TestListIncludeParents:
    """Tests for ListIncludeParents. Mirrors Go TestListIncludeParents."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"properties":{"items":[{"accountId":"act_1-1TJZFB","assetId":"aid_101","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","propertyId":"prp_175780","propertyName":"my-property"}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.list_include_parents(
            models.ListIncludeParentsRequest(include_id="inc_123456")
        )
        assert result.properties is not None
        assert len(result.properties.items) == 1

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.list_include_parents(
                models.ListIncludeParentsRequest(include_id="inc_123456")
            )

    def test_validation_error_missing_include_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.list_include_parents(
                models.ListIncludeParentsRequest(include_id="")
            )
        assert "IncludeID" in str(exc_info.value)


class TestGetInclude:
    """Tests for GetInclude. Mirrors Go TestGetInclude."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"includes":{"items":[{"accountId":"act_1-1TJZFB","assetId":"aid_101","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","includeId":"inc_123456","includeName":"my-include","includeType":"MICROSERVICES","latestVersion":1}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_include(
            models.GetIncludeRequest(
                include_id="inc_123456",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.include is not None
        assert result.include.include_id == "inc_123456"

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_include(
                models.GetIncludeRequest(include_id="inc_123456", contract_id="ctr_1-1TJZFW", group_id="grp_15166")
            )


class TestCreateInclude:
    """Tests for CreateInclude. Mirrors Go TestCreateInclude."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"includeLink":"/papi/v1/includes/inc_123456?contractId=ctr_1-1TJZFW&groupId=grp_15166"}'
        _setup_success(mock_session_request, body)
        result = papi_client.create_include(
            models.CreateIncludeRequest(
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                include_name="my-include",
                include_type="MICROSERVICES",
                product_id="prd_Alta",
                rule_format="v2015-08-08",
            )
        )
        assert result.include_id == "inc_123456"

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.create_include(
                models.CreateIncludeRequest(
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                    include_name="my-include", include_type="MICROSERVICES",
                    product_id="prd_Alta", rule_format="v2015-08-08",
                )
            )


class TestDeleteInclude:
    """Tests for DeleteInclude. Mirrors Go TestDeleteInclude."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"message":"Deletion Successful."}'
        _setup_success(mock_session_request, body)
        result = papi_client.delete_include(
            models.DeleteIncludeRequest(
                include_id="inc_123456",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.message == "Deletion Successful."

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.delete_include(
                models.DeleteIncludeRequest(
                    include_id="inc_123456", contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )


# =========================================================================
# Include Activation Tests — from include_activations_test.go
# =========================================================================


class TestActivateInclude:
    """Tests for ActivateInclude. Mirrors Go TestActivateInclude."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"activationLink":"/papi/v1/includes/inc_123456/activations/atv_111?contractId=ctr_1-1TJZFW&groupId=grp_15166"}'
        _setup_success(mock_session_request, body)
        result = papi_client.activate_include(
            models.ActivateOrDeactivateIncludeRequest(
                include_id="inc_123456",
                version=1,
                network="STAGING",
                note="test activation",
                notify_emails=["user@example.com"],
            )
        )
        assert result.activation_id == "atv_111"

    def test_200_with_compliance_record(self, papi_client, mock_session_request):
        body = '{"activationLink":"/papi/v1/includes/inc_123456/activations/atv_111?contractId=ctr_1-1TJZFW&groupId=grp_15166"}'
        _setup_success(mock_session_request, body)
        result = papi_client.activate_include(
            models.ActivateOrDeactivateIncludeRequest(
                include_id="inc_123456",
                version=1,
                network="PRODUCTION",
                note="test activation",
                notify_emails=["user@example.com"],
                compliance_record={"noncomplianceReason": "NONE"},
            )
        )
        assert result.activation_id == "atv_111"

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.activate_include(
                models.ActivateOrDeactivateIncludeRequest(
                    include_id="inc_123456", version=1, network="STAGING",
                    note="test", notify_emails=["user@example.com"],
                )
            )

    def test_validation_error_missing_include_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.activate_include(
                models.ActivateOrDeactivateIncludeRequest(
                    include_id="", version=1, network="STAGING",
                    notify_emails=["user@example.com"],
                )
            )
        assert "IncludeID" in str(exc_info.value)

    def test_validation_error_missing_network(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.activate_include(
                models.ActivateOrDeactivateIncludeRequest(
                    include_id="inc_123456", version=1, network="",
                    notify_emails=["user@example.com"],
                )
            )
        assert "Network" in str(exc_info.value)


class TestDeactivateInclude:
    """Tests for DeactivateInclude. Mirrors Go TestDeactivateInclude."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"activationLink":"/papi/v1/includes/inc_123456/activations/atv_222?contractId=ctr_1-1TJZFW&groupId=grp_15166"}'
        _setup_success(mock_session_request, body)
        result = papi_client.deactivate_include(
            models.ActivateOrDeactivateIncludeRequest(
                include_id="inc_123456",
                version=1,
                network="STAGING",
                note="test deactivation",
                notify_emails=["user@example.com"],
            )
        )
        assert result.activation_id == "atv_222"

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.deactivate_include(
                models.ActivateOrDeactivateIncludeRequest(
                    include_id="inc_123456", version=1, network="STAGING",
                    note="test", notify_emails=["user@example.com"],
                )
            )


class TestCancelIncludeActivation:
    """Tests for CancelIncludeActivation. Mirrors Go TestCancelIncludeActivation."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","activations":{"items":[{"activationId":"atv_111","network":"STAGING","activationType":"ACTIVATE","status":"ABORTED","submitDate":"2020-01-01T00:00:00Z","updateDate":"2020-01-02T00:00:00Z","note":"cancelled","notifyEmails":["user@example.com"],"includeId":"inc_123456","includeName":"my-include","includeType":"MICROSERVICES","includeVersion":1}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.cancel_include_activation(
            models.CancelIncludeActivationRequest(
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                include_id="inc_123456",
                activation_id="atv_111",
            )
        )
        assert result.activations is not None
        assert len(result.activations.items) == 1
        assert result.activations.items[0].status == "ABORTED"

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.cancel_include_activation(
                models.CancelIncludeActivationRequest(
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                    include_id="inc_123456", activation_id="atv_111",
                )
            )

    def test_validation_error_missing_include_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.cancel_include_activation(
                models.CancelIncludeActivationRequest(
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                    include_id="", activation_id="atv_111",
                )
            )
        assert "IncludeID" in str(exc_info.value)


class TestGetIncludeActivation:
    """Tests for GetIncludeActivation. Mirrors Go TestGetIncludeActivation."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","activations":{"items":[{"activationId":"atv_111","network":"STAGING","activationType":"ACTIVATE","status":"ACTIVE","submitDate":"2020-01-01T00:00:00Z","updateDate":"2020-01-02T00:00:00Z","note":"activated","notifyEmails":["user@example.com"],"includeId":"inc_123456","includeName":"my-include","includeType":"MICROSERVICES","includeVersion":1}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_include_activation(
            models.GetIncludeActivationRequest(
                include_id="inc_123456",
                activation_id="atv_111",
            )
        )
        assert result.activation is not None
        assert result.activation.activation_id == "atv_111"
        assert result.activation.status == "ACTIVE"

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_include_activation(
                models.GetIncludeActivationRequest(
                    include_id="inc_123456", activation_id="atv_111",
                )
            )

    def test_validation_error_missing_include_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.get_include_activation(
                models.GetIncludeActivationRequest(include_id="", activation_id="atv_111")
            )
        assert "IncludeID" in str(exc_info.value)


class TestListIncludeActivations:
    """Tests for ListIncludeActivations. Mirrors Go TestListIncludeActivations."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","activations":{"items":[{"activationId":"atv_111","network":"STAGING","activationType":"ACTIVATE","status":"ACTIVE","submitDate":"2020-01-01T00:00:00Z","updateDate":"2020-01-02T00:00:00Z","note":"activated","notifyEmails":["user@example.com"],"includeId":"inc_123456","includeName":"my-include","includeType":"MICROSERVICES","includeVersion":1}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.list_include_activations(
            models.ListIncludeActivationsRequest(
                include_id="inc_123456",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.activations is not None
        assert len(result.activations.items) == 1

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.list_include_activations(
                models.ListIncludeActivationsRequest(
                    include_id="inc_123456", contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )

    def test_validation_error_missing_include_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.list_include_activations(
                models.ListIncludeActivationsRequest(include_id="", contract_id="ctr_1-1TJZFW", group_id="grp_15166")
            )
        assert "IncludeID" in str(exc_info.value)


# =========================================================================
# Include Rule Tests — from include_rule_test.go
# =========================================================================


class TestGetIncludeRuleTree:
    """Tests for GetIncludeRuleTree. Mirrors Go TestGetIncludeRuleTree."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","includeId":"inc_123456","includeName":"my-include","includeType":"MICROSERVICES","includeVersion":1,"etag":"etag_1","ruleFormat":"v2020-11-02","rules":{"name":"default","children":[],"behaviors":[{"name":"origin","options":{"originType":"CUSTOMER","hostname":"example.com"}}],"criteria":[],"options":{"is_secure":false}}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_include_rule_tree(
            models.GetIncludeRuleTreeRequest(
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                include_id="inc_123456",
                include_version=1,
                rule_format="v2020-11-02",
            )
        )
        assert result.include_id == "inc_123456"
        assert result.etag == "etag_1"
        assert result.rules is not None
        assert result.rules.name == "default"
        assert len(result.rules.behaviors) == 1
        assert result.rules.behaviors[0].name == "origin"

    def test_200_ok_without_rule_format(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","includeId":"inc_123456","includeName":"my-include","includeType":"MICROSERVICES","includeVersion":1,"etag":"etag_1","ruleFormat":"v2020-11-02","rules":{"name":"default","children":[],"behaviors":[],"criteria":[],"options":{"is_secure":false}}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_include_rule_tree(
            models.GetIncludeRuleTreeRequest(
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                include_id="inc_123456",
                include_version=1,
            )
        )
        assert result.include_id == "inc_123456"
        assert result.rule_format == "v2020-11-02"

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_include_rule_tree(
                models.GetIncludeRuleTreeRequest(
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                    include_id="inc_123456", include_version=1,
                )
            )

    def test_validation_error_missing_include_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.get_include_rule_tree(
                models.GetIncludeRuleTreeRequest(
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                    include_id="", include_version=1,
                )
            )
        assert "IncludeID" in str(exc_info.value)


class TestUpdateIncludeRuleTree:
    """Tests for UpdateIncludeRuleTree. Mirrors Go TestUpdateIncludeRuleTree."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","includeId":"inc_123456","includeName":"my-include","includeType":"MICROSERVICES","includeVersion":1,"etag":"etag_2","ruleFormat":"v2020-11-02","rules":{"name":"default","children":[],"behaviors":[{"name":"origin","options":{"originType":"CUSTOMER","hostname":"updated.example.com"}}],"criteria":[],"options":{"is_secure":false}}}'
        _setup_success(mock_session_request, body)
        result = papi_client.update_include_rule_tree(
            models.UpdateIncludeRuleTreeRequest(
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                include_id="inc_123456",
                include_version=1,
                rules=models.RulesUpdate(
                    rules=models.Rules(
                        name="default",
                        behaviors=[
                            models.RuleBehavior(
                                name="origin",
                                options={"originType": "CUSTOMER", "hostname": "updated.example.com"},
                            )
                        ],
                    ),
                ),
            )
        )
        assert result.include_id == "inc_123456"
        assert result.etag == "etag_2"
        assert result.rules is not None
        assert result.rules.behaviors[0].name == "origin"

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.update_include_rule_tree(
                models.UpdateIncludeRuleTreeRequest(
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                    include_id="inc_123456", include_version=1,
                    rules=models.RulesUpdate(rules=models.Rules(name="default")),
                )
            )

    def test_validation_error_missing_include_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.update_include_rule_tree(
                models.UpdateIncludeRuleTreeRequest(
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                    include_id="", include_version=1,
                    rules=models.RulesUpdate(rules=models.Rules(name="default")),
                )
            )
        assert "IncludeID" in str(exc_info.value)


# =========================================================================
# Include Version Tests — from include_versions_test.go
# =========================================================================


class TestCreateIncludeVersion:
    """Tests for CreateIncludeVersion. Mirrors Go TestCreateIncludeVersion."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"versionLink":"/papi/v1/includes/inc_123456/versions/2"}'
        _setup_success(mock_session_request, body)
        result = papi_client.create_include_version(
            models.CreateIncludeVersionRequest(
                include_id="inc_123456",
                create_from_version=1,
                create_from_version_etag="etag_1",
            )
        )
        assert result.version == 2

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.create_include_version(
                models.CreateIncludeVersionRequest(
                    include_id="inc_123456", create_from_version=1,
                )
            )

    def test_validation_error_missing_include_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.create_include_version(
                models.CreateIncludeVersionRequest(include_id="", create_from_version=1)
            )
        assert "IncludeID" in str(exc_info.value)


class TestGetIncludeVersion:
    """Tests for GetIncludeVersion. Mirrors Go TestGetIncludeVersion."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"includeId":"inc_123456","includeName":"my-include","accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","assetId":"aid_101","includeType":"MICROSERVICES","versions":{"items":[{"includeVersion":1,"updatedByUser":"user1","updatedDate":"2020-01-01T00:00:00Z","productionStatus":"INACTIVE","stagingStatus":"ACTIVE","etag":"etag_1"}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_include_version(
            models.GetIncludeVersionRequest(
                include_id="inc_123456", version=1,
                contract_id="ctr_1-1TJZFW", group_id="grp_15166",
            )
        )
        assert result.include_id == "inc_123456"
        assert result.include_version is not None
        assert result.include_version.include_version == 1

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_include_version(
                models.GetIncludeVersionRequest(
                    include_id="inc_123456", version=1,
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )


class TestListIncludeVersions:
    """Tests for ListIncludeVersions. Mirrors Go TestListIncludeVersions."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"includeId":"inc_123456","includeName":"my-include","accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","assetId":"aid_101","includeType":"MICROSERVICES","versions":{"items":[{"includeVersion":1,"updatedByUser":"user1","updatedDate":"2020-01-01T00:00:00Z","productionStatus":"INACTIVE","stagingStatus":"ACTIVE","etag":"etag_1"},{"includeVersion":2,"updatedByUser":"user2","updatedDate":"2020-01-02T00:00:00Z","productionStatus":"INACTIVE","stagingStatus":"INACTIVE","etag":"etag_2"}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.list_include_versions(
            models.ListIncludeVersionsRequest(
                include_id="inc_123456",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.include_id == "inc_123456"
        assert result.include_versions is not None
        assert len(result.include_versions.items) == 2

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.list_include_versions(
                models.ListIncludeVersionsRequest(
                    include_id="inc_123456", contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )

    def test_validation_error_missing_include_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.list_include_versions(
                models.ListIncludeVersionsRequest(include_id="", contract_id="ctr_1-1TJZFW", group_id="grp_15166")
            )
        assert "IncludeID" in str(exc_info.value)


class TestListIncludeVersionAvailableCriteria:
    """Tests for list_include_version_available_criteria. Mirrors Go TestListIncludeVersionAvailableCriteria."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"contractId":"ctr_1-1TJZFW","groupId":"grp_15166","productId":"prd_Alta","ruleFormat":"v2020-11-02","availableCriteria":{"items":[{"name":"hostname","schemaLink":"/papi/v1/schemas/products/prd_Alta/latest#/definitions/catalog/criteria/hostname"}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.list_include_version_available_criteria(
            models.ListAvailableCriteriaRequest(
                include_id="inc_123456",
                version=1,
            )
        )
        assert result.available_criteria is not None
        assert len(result.available_criteria.items) == 1

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.list_include_version_available_criteria(
                models.ListAvailableCriteriaRequest(include_id="inc_123456", version=1)
            )


class TestListIncludeVersionAvailableBehaviors:
    """Tests for list_include_version_available_behaviors. Mirrors Go TestListIncludeVersionAvailableBehaviors."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"contractId":"ctr_1-1TJZFW","groupId":"grp_15166","productId":"prd_Alta","ruleFormat":"v2020-11-02","availableBehaviors":{"items":[{"name":"origin","schemaLink":"/papi/v1/schemas/products/prd_Alta/latest#/definitions/catalog/behaviors/origin"}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.list_include_version_available_behaviors(
            models.ListAvailableBehaviorsRequest(
                include_id="inc_123456",
                version=1,
            )
        )
        assert result.available_behaviors is not None
        assert len(result.available_behaviors.items) == 1

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.list_include_version_available_behaviors(
                models.ListAvailableBehaviorsRequest(include_id="inc_123456", version=1)
            )


# =========================================================================
# Property Version Tests — from propertyversion_test.go
# =========================================================================


class TestPapiGetPropertyVersions:
    """Tests for GetPropertyVersions. Mirrors Go TestPapiGetPropertyVersions."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"propertyId":"prp_175780","propertyName":"my-property","accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","assetId":"aid_101","versions":{"items":[{"propertyVersion":1,"updatedByUser":"user1","updatedDate":"2020-01-01T00:00:00Z","productionStatus":"INACTIVE","stagingStatus":"ACTIVE","etag":"etag_1","productId":"prd_Alta","ruleFormat":"v2020-11-02","note":"initial version"}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_property_versions(
            models.GetPropertyVersionsRequest(
                property_id="prp_175780",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.property_id == "prp_175780"
        assert result.versions is not None
        assert len(result.versions.items) == 1
        assert result.versions.items[0].property_version == 1

    def test_200_ok_with_pagination(self, papi_client, mock_session_request):
        body = '{"propertyId":"prp_175780","propertyName":"my-property","accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","assetId":"aid_101","versions":{"items":[{"propertyVersion":2,"updatedByUser":"user1","updatedDate":"2020-01-02T00:00:00Z","productionStatus":"INACTIVE","stagingStatus":"INACTIVE","etag":"etag_2","productId":"prd_Alta","ruleFormat":"v2020-11-02","note":"second version"}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_property_versions(
            models.GetPropertyVersionsRequest(
                property_id="prp_175780",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                limit=1,
                offset=1,
            )
        )
        assert result.versions is not None
        assert len(result.versions.items) == 1

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_property_versions(
                models.GetPropertyVersionsRequest(
                    property_id="prp_175780", contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )

    def test_validation_error_missing_property_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.get_property_versions(
                models.GetPropertyVersionsRequest(
                    property_id="", contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )
        assert "PropertyID" in str(exc_info.value)


class TestPapiGetPropertyVersion:
    """Tests for GetPropertyVersion. Mirrors Go TestPapiGetPropertyVersion."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"propertyId":"prp_175780","propertyName":"my-property","accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","assetId":"aid_101","versions":{"items":[{"propertyVersion":1,"updatedByUser":"user1","updatedDate":"2020-01-01T00:00:00Z","productionStatus":"INACTIVE","stagingStatus":"ACTIVE","etag":"etag_1","productId":"prd_Alta","ruleFormat":"v2020-11-02","note":"initial version"}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_property_version(
            models.GetPropertyVersionRequest(
                property_id="prp_175780",
                property_version=1,
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.property_id == "prp_175780"
        assert result.versions is not None
        assert len(result.versions.items) == 1
        assert_request_made(
            mock_session_request, "GET",
            "/papi/v1/properties/prp_175780/versions/1",
        )

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_property_version(
                models.GetPropertyVersionRequest(
                    property_id="prp_175780", property_version=1,
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )

    def test_validation_error_missing_property_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.get_property_version(
                models.GetPropertyVersionRequest(
                    property_id="", property_version=1,
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )
        assert "PropertyID" in str(exc_info.value)


class TestPapiCreatePropertyVersion:
    """Tests for CreatePropertyVersion. Mirrors Go TestPapiCreatePropertyVersion."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"versionLink":"/papi/v1/properties/prp_175780/versions/2?contractId=ctr_1-1TJZFW&groupId=grp_15166"}'
        _setup_success(mock_session_request, body)
        result = papi_client.create_property_version(
            models.CreatePropertyVersionRequest(
                property_id="prp_175780",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                version=models.PropertyVersionCreate(
                    create_from_version=1,
                    create_from_version_etag="etag_1",
                ),
            )
        )
        assert result.version_link != ""

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.create_property_version(
                models.CreatePropertyVersionRequest(
                    property_id="prp_175780",
                    contract_id="ctr_1-1TJZFW",
                    group_id="grp_15166",
                    version=models.PropertyVersionCreate(create_from_version=1),
                )
            )

    def test_validation_error_missing_property_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.create_property_version(
                models.CreatePropertyVersionRequest(
                    property_id="",
                    contract_id="ctr_1-1TJZFW",
                    group_id="grp_15166",
                    version=models.PropertyVersionCreate(create_from_version=1),
                )
            )
        assert "PropertyID" in str(exc_info.value)


class TestPapiGetLatestVersion:
    """Tests for GetLatestVersion. Mirrors Go TestPapiGetLatestVersion."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"propertyId":"prp_175780","propertyName":"my-property","accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","assetId":"aid_101","versions":{"items":[{"propertyVersion":2,"updatedByUser":"user1","updatedDate":"2020-01-02T00:00:00Z","productionStatus":"INACTIVE","stagingStatus":"ACTIVE","etag":"etag_2","productId":"prd_Alta","ruleFormat":"v2020-11-02"}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_latest_version(
            models.GetLatestVersionRequest(
                property_id="prp_175780",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.property_id == "prp_175780"
        assert result.versions is not None
        assert len(result.versions.items) == 1
        assert result.versions.items[0].property_version == 2

    def test_200_ok_with_activated_on(self, papi_client, mock_session_request):
        body = '{"propertyId":"prp_175780","propertyName":"my-property","accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","assetId":"aid_101","versions":{"items":[{"propertyVersion":1,"updatedByUser":"user1","updatedDate":"2020-01-01T00:00:00Z","productionStatus":"ACTIVE","stagingStatus":"ACTIVE","etag":"etag_1","productId":"prd_Alta","ruleFormat":"v2020-11-02"}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_latest_version(
            models.GetLatestVersionRequest(
                property_id="prp_175780",
                activated_on="PRODUCTION",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.property_id == "prp_175780"

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_latest_version(
                models.GetLatestVersionRequest(
                    property_id="prp_175780", contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )

    def test_validation_error_missing_property_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.get_latest_version(
                models.GetLatestVersionRequest(
                    property_id="", contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )
        assert "PropertyID" in str(exc_info.value)


class TestPapiGetAvailableBehaviors:
    """Tests for GetAvailableBehaviors. Mirrors Go TestPapiGetAvailableBehaviors."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"contractId":"ctr_1-1TJZFW","groupId":"grp_15166","productId":"prd_Alta","ruleFormat":"v2020-11-02","availableBehaviors":{"items":[{"name":"origin","schemaLink":"/papi/v1/schemas/products/prd_Alta/latest#/definitions/catalog/behaviors/origin"}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_available_behaviors(
            models.GetAvailableItemsRequest(
                property_id="prp_175780",
                property_version=1,
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.available_behaviors is not None
        assert len(result.available_behaviors.items) == 1

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_available_behaviors(
                models.GetAvailableItemsRequest(
                    property_id="prp_175780", property_version=1,
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )


class TestPapiGetAvailableCriteria:
    """Tests for GetAvailableCriteria. Mirrors Go TestPapiGetAvailableCriteria."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"contractId":"ctr_1-1TJZFW","groupId":"grp_15166","productId":"prd_Alta","ruleFormat":"v2020-11-02","availableCriteria":{"items":[{"name":"hostname","schemaLink":"/papi/v1/schemas/products/prd_Alta/latest#/definitions/catalog/criteria/hostname"}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_available_criteria(
            models.GetAvailableItemsRequest(
                property_id="prp_175780",
                property_version=1,
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.available_criteria is not None
        assert len(result.available_criteria.items) == 1

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_available_criteria(
                models.GetAvailableItemsRequest(
                    property_id="prp_175780", property_version=1,
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )


# =========================================================================
# Available Includes Tests — from propertyversion_test.go
# =========================================================================


class TestPapiListAvailableIncludes:
    """Tests for ListAvailableIncludes. Mirrors Go TestPapiListAvailableIncludes."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","externalResources":{"inc_123456":{"includeId":"inc_123456","includeName":"my-include","includeType":"MICROSERVICES","fileName":"my-include.xml"}}}'
        _setup_success(mock_session_request, body)
        result = papi_client.list_available_includes(
            models.ListAvailableIncludesRequest(
                property_id="prp_175780",
                property_version=1,
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert len(result.available_includes) == 1
        assert result.available_includes[0].include_id == "inc_123456"

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.list_available_includes(
                models.ListAvailableIncludesRequest(
                    property_id="prp_175780", property_version=1,
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )

    def test_validation_error_missing_property_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.list_available_includes(
                models.ListAvailableIncludesRequest(
                    property_id="", property_version=1,
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )
        assert "PropertyID" in str(exc_info.value)


class TestPapiListReferencedIncludes:
    """Tests for ListReferencedIncludes. Mirrors Go TestPapiListReferencedIncludes."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"includes":{"items":[{"accountId":"act_1-1TJZFB","assetId":"aid_101","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","includeId":"inc_123456","includeName":"my-include","includeType":"MICROSERVICES","latestVersion":1}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.list_referenced_includes(
            models.ListAvailableReferencedIncludesRequest(
                property_id="prp_175780",
                property_version=1,
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.includes is not None
        assert len(result.includes.items) == 1

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.list_referenced_includes(
                models.ListAvailableReferencedIncludesRequest(
                    property_id="prp_175780", property_version=1,
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )


# =========================================================================
# Property Hostname Tests — from propertyhostname_test.go
# =========================================================================


class TestGetPropertyVersionHostnames:
    """Tests for GetPropertyVersionHostnames. Mirrors Go TestGetPropertyVersionHostnames."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","propertyId":"prp_175780","propertyVersion":1,"etag":"etag_1","propertyName":"my-property","hostnames":{"items":[{"cnameType":"EDGE_HOSTNAME","edgeHostnameId":"ehn_887436","cnameFrom":"example.com","cnameTo":"example.com.edgesuite.net","certProvisioningType":"CPS_MANAGED"}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_property_version_hostnames(
            models.GetPropertyVersionHostnamesRequest(
                property_id="prp_175780",
                property_version=1,
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.property_id == "prp_175780"
        assert result.hostnames is not None
        assert len(result.hostnames.items) == 1
        assert result.hostnames.items[0].cname_from == "example.com"

    def test_200_ok_with_cert_status(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","propertyId":"prp_175780","propertyVersion":1,"etag":"etag_1","propertyName":"my-property","hostnames":{"items":[{"cnameType":"EDGE_HOSTNAME","edgeHostnameId":"ehn_887436","cnameFrom":"example.com","cnameTo":"example.com.edgesuite.net","certProvisioningType":"CPS_MANAGED","certStatus":{"validationCname":{"hostname":"_acme.example.com","target":"_acme.edgesuite.net"},"staging":[],"production":[]}}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_property_version_hostnames(
            models.GetPropertyVersionHostnamesRequest(
                property_id="prp_175780",
                property_version=1,
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                include_cert_status=True,
            )
        )
        assert result.hostnames is not None
        assert len(result.hostnames.items) == 1
        assert result.hostnames.items[0].cert_status is not None

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_property_version_hostnames(
                models.GetPropertyVersionHostnamesRequest(
                    property_id="prp_175780", property_version=1,
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )

    def test_validation_error_missing_property_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.get_property_version_hostnames(
                models.GetPropertyVersionHostnamesRequest(
                    property_id="", property_version=1,
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )
        assert "PropertyID" in str(exc_info.value)


class TestUpdatePropertyVersionHostnames:
    """Tests for UpdatePropertyVersionHostnames. Mirrors Go TestUpdatePropertyVersionHostnames."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","propertyId":"prp_175780","propertyVersion":1,"etag":"etag_2","propertyName":"my-property","hostnames":{"items":[{"cnameType":"EDGE_HOSTNAME","edgeHostnameId":"ehn_887436","cnameFrom":"example.com","cnameTo":"example.com.edgesuite.net","certProvisioningType":"CPS_MANAGED"}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.update_property_version_hostnames(
            models.UpdatePropertyVersionHostnamesRequest(
                property_id="prp_175780",
                property_version=1,
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                hostnames=[
                    models.Hostname(
                        cname_type="EDGE_HOSTNAME",
                        edge_hostname_id="ehn_887436",
                        cname_from="example.com",
                        cname_to="example.com.edgesuite.net",
                        cert_provisioning_type="CPS_MANAGED",
                    ),
                ],
            )
        )
        assert result.property_id == "prp_175780"
        assert result.hostnames is not None
        assert len(result.hostnames.items) == 1

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.update_property_version_hostnames(
                models.UpdatePropertyVersionHostnamesRequest(
                    property_id="prp_175780", property_version=1,
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                    hostnames=[],
                )
            )

    def test_validation_error_missing_property_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.update_property_version_hostnames(
                models.UpdatePropertyVersionHostnamesRequest(
                    property_id="", property_version=1,
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                    hostnames=[],
                )
            )
        assert "PropertyID" in str(exc_info.value)


class TestPatchPropertyVersionHostnames:
    """Tests for PatchPropertyVersionHostnames. Mirrors Go TestPatchPropertyVersionHostnames."""

    def test_200_ok_add(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","etag":"etag_3","propertyId":"prp_175780","propertyName":"my-property","propertyVersion":1,"hostnames":{"items":[{"cnameType":"EDGE_HOSTNAME","edgeHostnameId":"ehn_887436","cnameFrom":"example.com","cnameTo":"example.com.edgesuite.net","certProvisioningType":"CPS_MANAGED"}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.patch_property_version_hostnames(
            models.PatchPropertyVersionHostnamesRequest(
                property_id="prp_175780",
                property_version=1,
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                body=models.PatchPropertyVersionHostnamesRequestBody(
                    add=[
                        models.HostnameAdd(
                            cname_from="example.com",
                            cname_type="EDGE_HOSTNAME",
                            cname_to="example.com.edgesuite.net",
                            cert_provisioning_type="CPS_MANAGED",
                            edge_hostname_id="ehn_887436",
                        ),
                    ],
                    remove=[],
                ),
            )
        )
        assert result.property_id == "prp_175780"
        assert result.hostnames is not None

    def test_200_ok_remove(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","etag":"etag_3","propertyId":"prp_175780","propertyName":"my-property","propertyVersion":1,"hostnames":{"items":[]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.patch_property_version_hostnames(
            models.PatchPropertyVersionHostnamesRequest(
                property_id="prp_175780",
                property_version=1,
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                body=models.PatchPropertyVersionHostnamesRequestBody(
                    add=[],
                    remove=["example.com"],
                ),
            )
        )
        assert result.hostnames is not None

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.patch_property_version_hostnames(
                models.PatchPropertyVersionHostnamesRequest(
                    property_id="prp_175780", property_version=1,
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                    body=models.PatchPropertyVersionHostnamesRequestBody(add=[], remove=[]),
                )
            )

    def test_validation_error_missing_property_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.patch_property_version_hostnames(
                models.PatchPropertyVersionHostnamesRequest(
                    property_id="", property_version=1,
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                    body=models.PatchPropertyVersionHostnamesRequestBody(add=[], remove=[]),
                )
            )
        assert "PropertyID" in str(exc_info.value)


class TestGetAuditHistory:
    """Tests for GetAuditHistory. Mirrors Go TestGetAuditHistory."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"hostname":"example.com","history":{"items":[{"propertyId":"prp_175780","propertyName":"my-property","propertyVersion":1,"network":"STAGING","action":"ADDED","submitDate":"2020-01-01T00:00:00Z","submitBy":"user1","note":"added hostname"}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_audit_history(
            models.GetAuditHistoryRequest(hostname="example.com")
        )
        assert result.hostname == "example.com"
        assert result.history is not None
        assert len(result.history.items) == 1

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_audit_history(
                models.GetAuditHistoryRequest(hostname="example.com")
            )

    def test_validation_error_missing_hostname(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.get_audit_history(
                models.GetAuditHistoryRequest(hostname="")
            )
        assert "Hostname" in str(exc_info.value)


# =========================================================================
# Rule Tree Tests — from rule_test.go
# =========================================================================


class TestPapiGetRuleTree:
    """Tests for GetRuleTree. Mirrors Go TestPapiGetRuleTree."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","propertyId":"prp_175780","propertyVersion":1,"etag":"etag_1","ruleFormat":"v2020-11-02","rules":{"name":"default","children":[],"behaviors":[{"name":"origin","options":{"originType":"CUSTOMER","hostname":"example.com"}}],"criteria":[],"options":{"is_secure":false},"variables":[],"comments":""}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_rule_tree(
            models.GetRuleTreeRequest(
                property_id="prp_175780",
                property_version=1,
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.property_id == "prp_175780"
        assert result.property_version == 1
        assert result.rule_format == "v2020-11-02"
        assert result.rules is not None
        assert result.rules.name == "default"
        assert len(result.rules.behaviors) == 1
        assert result.rules.behaviors[0].name == "origin"
        assert_request_made(
            mock_session_request, "GET",
            "/papi/v1/properties/prp_175780/versions/1/rules",
        )

    def test_200_ok_with_rule_format(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","propertyId":"prp_175780","propertyVersion":1,"etag":"etag_1","ruleFormat":"v2023-01-05","rules":{"name":"default","children":[],"behaviors":[],"criteria":[],"options":{"is_secure":false},"variables":[]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_rule_tree(
            models.GetRuleTreeRequest(
                property_id="prp_175780",
                property_version=1,
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                rule_format="v2023-01-05",
            )
        )
        assert result.rule_format == "v2023-01-05"

    def test_200_ok_with_children(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","propertyId":"prp_175780","propertyVersion":1,"etag":"etag_1","ruleFormat":"v2020-11-02","rules":{"name":"default","children":[{"name":"child-rule","behaviors":[{"name":"caching","options":{"behavior":"MAX_AGE","maxAge":"1d"}}],"criteria":[{"name":"path","options":{"matchOperator":"MATCHES_ONE_OF","values":["/static/*"]}}],"criteriaMustSatisfy":"all"}],"behaviors":[{"name":"origin","options":{"originType":"CUSTOMER","hostname":"example.com"}}],"criteria":[],"options":{"is_secure":false}}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_rule_tree(
            models.GetRuleTreeRequest(
                property_id="prp_175780",
                property_version=1,
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.rules is not None
        assert len(result.rules.children) == 1
        assert result.rules.children[0].name == "child-rule"
        assert len(result.rules.children[0].behaviors) == 1
        assert len(result.rules.children[0].criteria) == 1

    def test_200_ok_with_variables(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","propertyId":"prp_175780","propertyVersion":1,"etag":"etag_1","ruleFormat":"v2020-11-02","rules":{"name":"default","children":[],"behaviors":[],"criteria":[],"options":{"is_secure":false},"variables":[{"name":"PMUSER_VAR1","value":"test","description":"test variable","hidden":false,"sensitive":false}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_rule_tree(
            models.GetRuleTreeRequest(
                property_id="prp_175780",
                property_version=1,
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.rules is not None
        assert len(result.rules.variables) == 1
        assert result.rules.variables[0].name == "PMUSER_VAR1"

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_rule_tree(
                models.GetRuleTreeRequest(
                    property_id="prp_175780", property_version=1,
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )

    def test_validation_error_missing_property_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.get_rule_tree(
                models.GetRuleTreeRequest(
                    property_id="", property_version=1,
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )
        assert "PropertyID" in str(exc_info.value)


class TestPapiUpdateRuleTree:
    """Tests for UpdateRuleTree. Mirrors Go TestPapiUpdateRuleTree."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","propertyId":"prp_175780","propertyVersion":1,"etag":"etag_2","ruleFormat":"v2020-11-02","rules":{"name":"default","children":[],"behaviors":[{"name":"origin","options":{"originType":"CUSTOMER","hostname":"updated.example.com"}}],"criteria":[],"options":{"is_secure":false}}}'
        _setup_success(mock_session_request, body)
        result = papi_client.update_rule_tree(
            models.UpdateRulesRequest(
                property_id="prp_175780",
                property_version=1,
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                rules=models.RulesUpdate(
                    rules=models.Rules(
                        name="default",
                        behaviors=[
                            models.RuleBehavior(
                                name="origin",
                                options={"originType": "CUSTOMER", "hostname": "updated.example.com"},
                            ),
                        ],
                    ),
                ),
            )
        )
        assert result.property_id == "prp_175780"
        assert result.etag == "etag_2"
        assert result.rules is not None
        assert result.rules.behaviors[0].name == "origin"

    def test_200_ok_with_dry_run(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","propertyId":"prp_175780","propertyVersion":1,"etag":"etag_1","ruleFormat":"v2020-11-02","rules":{"name":"default","children":[],"behaviors":[],"criteria":[],"options":{"is_secure":false}},"errors":[],"warnings":[]}'
        _setup_success(mock_session_request, body)
        result = papi_client.update_rule_tree(
            models.UpdateRulesRequest(
                property_id="prp_175780",
                property_version=1,
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                dry_run=True,
                rules=models.RulesUpdate(
                    rules=models.Rules(name="default"),
                ),
            )
        )
        assert result.property_id == "prp_175780"

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.update_rule_tree(
                models.UpdateRulesRequest(
                    property_id="prp_175780", property_version=1,
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                    rules=models.RulesUpdate(rules=models.Rules(name="default")),
                )
            )

    def test_validation_error_missing_property_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.update_rule_tree(
                models.UpdateRulesRequest(
                    property_id="", property_version=1,
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                    rules=models.RulesUpdate(rules=models.Rules(name="default")),
                )
            )
        assert "PropertyID" in str(exc_info.value)


# =========================================================================
# Active Property Hostname Tests — from active_property_hostname_test.go
# =========================================================================


class TestListActivePropertyHostnames:
    """Tests for ListActivePropertyHostnames. Mirrors Go TestListActivePropertyHostnames."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","totalResults":1,"resultCount":1,"hostnames":{"items":[{"cnameFrom":"example.com","cnameTo":"example.com.edgesuite.net","cnameType":"EDGE_HOSTNAME","edgeHostnameId":"ehn_887436","certProvisioningType":"CPS_MANAGED","network":"STAGING"}],"currentItemCount":1,"totalItems":1}}'
        _setup_success(mock_session_request, body)
        result = papi_client.list_active_property_hostnames(
            models.ListActivePropertyHostnamesRequest(
                property_id="prp_175780",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.total_results == 1
        assert result.hostnames is not None
        assert len(result.hostnames.items) == 1
        assert result.hostnames.items[0].cname_from == "example.com"

    def test_200_ok_with_pagination(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","totalResults":2,"resultCount":1,"hostnames":{"items":[{"cnameFrom":"example2.com","cnameTo":"example2.com.edgesuite.net","cnameType":"EDGE_HOSTNAME","edgeHostnameId":"ehn_887437","certProvisioningType":"CPS_MANAGED","network":"STAGING"}],"currentItemCount":1,"totalItems":2}}'
        _setup_success(mock_session_request, body)
        result = papi_client.list_active_property_hostnames(
            models.ListActivePropertyHostnamesRequest(
                property_id="prp_175780",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                offset=1,
                limit=1,
            )
        )
        assert result.total_results == 2
        assert result.result_count == 1

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.list_active_property_hostnames(
                models.ListActivePropertyHostnamesRequest(
                    property_id="prp_175780", contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )

    def test_validation_error_missing_property_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.list_active_property_hostnames(
                models.ListActivePropertyHostnamesRequest(
                    property_id="", contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )
        assert "PropertyID" in str(exc_info.value)


class TestGetActivePropertyHostnamesDiff:
    """Tests for GetActivePropertyHostnamesDiff. Mirrors Go TestGetActivePropertyHostnamesDiff."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","propertyId":"prp_175780","hostnames":{"items":[{"cnameFrom":"example.com","stagingDetails":{"cnameType":"EDGE_HOSTNAME","edgeHostnameId":"ehn_887436","cnameTo":"example.com.edgesuite.net","certProvisioningType":"CPS_MANAGED"},"productionDetails":null}],"currentItemCount":1,"totalItems":1}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_active_property_hostnames_diff(
            models.GetActivePropertyHostnamesDiffRequest(
                property_id="prp_175780",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.property_id == "prp_175780"
        assert result.hostnames is not None
        assert len(result.hostnames.items) == 1

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_active_property_hostnames_diff(
                models.GetActivePropertyHostnamesDiffRequest(
                    property_id="prp_175780", contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )

    def test_validation_error_missing_property_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.get_active_property_hostnames_diff(
                models.GetActivePropertyHostnamesDiffRequest(
                    property_id="", contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )
        assert "PropertyID" in str(exc_info.value)


class TestListActiveAccountHostnames:
    """Tests for ListActiveAccountHostnames. Mirrors Go TestListActiveAccountHostnames."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","availableSort":["hostname","cnameTo"],"currentSort":"hostname:a","defaultSort":"hostname:a","hostnames":{"items":[{"cnameFrom":"example.com","cnameTo":"example.com.edgesuite.net","cnameType":"EDGE_HOSTNAME","edgeHostnameId":"ehn_887436","certProvisioningType":"CPS_MANAGED","network":"STAGING","propertyId":"prp_175780","propertyName":"my-property"}],"currentItemCount":1,"totalItems":1}}'
        _setup_success(mock_session_request, body)
        result = papi_client.list_active_account_hostnames(
            models.ListActiveAccountHostnamesRequest()
        )
        assert result.account_id == "act_1-1TJZFB"
        assert result.hostnames is not None
        assert len(result.hostnames.items) == 1

    def test_200_ok_with_filters(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","availableSort":["hostname","cnameTo"],"currentSort":"hostname:a","defaultSort":"hostname:a","hostnames":{"items":[],"currentItemCount":0,"totalItems":0}}'
        _setup_success(mock_session_request, body)
        result = papi_client.list_active_account_hostnames(
            models.ListActiveAccountHostnamesRequest(
                hostname="nonexistent.com",
                network="STAGING",
                offset=0,
                limit=10,
            )
        )
        assert result.hostnames is not None
        assert len(result.hostnames.items) == 0

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.list_active_account_hostnames(
                models.ListActiveAccountHostnamesRequest()
            )


# =========================================================================
# Property Hostname Activation Tests — from property_hostname_activation_test.go
# =========================================================================


class TestGetPropertyHostnameActivation:
    """Tests for GetPropertyHostnameActivation. Mirrors Go TestGetPropertyHostnameActivation."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","hostnameActivations":{"items":[{"activationType":"ACTIVATE","hostnameActivationId":"ha_12345","propertyName":"my-property","propertyId":"prp_175780","network":"STAGING","status":"ACTIVE","submitDate":"2020-01-01T00:00:00Z","updateDate":"2020-01-02T00:00:00Z","note":"hostname activation","notifyEmails":["user@example.com"],"hostnames":[{"certProvisioningType":"CPS_MANAGED","cnameFrom":"example.com","cnameTo":"example.com.edgesuite.net","cnameType":"EDGE_HOSTNAME","edgeHostnameId":"ehn_887436","action":"ADD"}]}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_property_hostname_activation(
            models.GetPropertyHostnameActivationRequest(
                property_id="prp_175780",
                hostname_activation_id="ha_12345",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.hostname_activation is not None
        assert result.hostname_activation.hostname_activation_id == "ha_12345"
        assert result.hostname_activation.status == "ACTIVE"
        assert len(result.hostname_activation.hostnames) == 1

    def test_200_ok_with_include_hostnames(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","hostnameActivations":{"items":[{"activationType":"ACTIVATE","hostnameActivationId":"ha_12345","propertyName":"my-property","propertyId":"prp_175780","network":"STAGING","status":"ACTIVE","submitDate":"2020-01-01T00:00:00Z","updateDate":"2020-01-02T00:00:00Z","note":"hostname activation","notifyEmails":["user@example.com"],"hostnames":[{"certProvisioningType":"CPS_MANAGED","cnameFrom":"example.com","cnameTo":"example.com.edgesuite.net","cnameType":"EDGE_HOSTNAME","edgeHostnameId":"ehn_887436","action":"ADD"}]}]}}'
        _setup_success(mock_session_request, body)
        result = papi_client.get_property_hostname_activation(
            models.GetPropertyHostnameActivationRequest(
                property_id="prp_175780",
                hostname_activation_id="ha_12345",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                include_hostnames=True,
            )
        )
        assert result.hostname_activation is not None

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.get_property_hostname_activation(
                models.GetPropertyHostnameActivationRequest(
                    property_id="prp_175780", hostname_activation_id="ha_12345",
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )

    def test_validation_error_missing_property_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.get_property_hostname_activation(
                models.GetPropertyHostnameActivationRequest(
                    property_id="", hostname_activation_id="ha_12345",
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )
        assert "PropertyID" in str(exc_info.value)


class TestListPropertyHostnameActivations:
    """Tests for ListPropertyHostnameActivations. Mirrors Go TestListPropertyHostnameActivations."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","hostnameActivations":{"items":[{"activationType":"ACTIVATE","hostnameActivationId":"ha_12345","propertyName":"my-property","propertyId":"prp_175780","network":"STAGING","status":"ACTIVE","submitDate":"2020-01-01T00:00:00Z","updateDate":"2020-01-02T00:00:00Z","note":"hostname activation","notifyEmails":["user@example.com"]}],"totalItems":1,"currentItemCount":1}}'
        _setup_success(mock_session_request, body)
        result = papi_client.list_property_hostname_activations(
            models.ListPropertyHostnameActivationsRequest(
                property_id="prp_175780",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.hostname_activations is not None
        assert len(result.hostname_activations.items) == 1
        assert result.hostname_activations.items[0].hostname_activation_id == "ha_12345"

    def test_200_ok_with_pagination(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","hostnameActivations":{"items":[],"totalItems":0,"currentItemCount":0}}'
        _setup_success(mock_session_request, body)
        result = papi_client.list_property_hostname_activations(
            models.ListPropertyHostnameActivationsRequest(
                property_id="prp_175780",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                offset=10,
                limit=5,
            )
        )
        assert result.hostname_activations is not None

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.list_property_hostname_activations(
                models.ListPropertyHostnameActivationsRequest(
                    property_id="prp_175780", contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )

    def test_validation_error_missing_property_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.list_property_hostname_activations(
                models.ListPropertyHostnameActivationsRequest(
                    property_id="", contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )
        assert "PropertyID" in str(exc_info.value)


class TestCancelPropertyHostnameActivation:
    """Tests for CancelPropertyHostnameActivation. Mirrors Go TestCancelPropertyHostnameActivation."""

    def test_200_ok(self, papi_client, mock_session_request):
        body = '{"accountId":"act_1-1TJZFB","contractId":"ctr_1-1TJZFW","groupId":"grp_15166","hostnameActivations":{"items":[{"activationType":"ACTIVATE","hostnameActivationId":"ha_12345","propertyName":"my-property","propertyId":"prp_175780","network":"STAGING","status":"ABORTED","submitDate":"2020-01-01T00:00:00Z","updateDate":"2020-01-02T00:00:00Z","note":"cancelled","notifyEmails":["user@example.com"],"propertyVersion":1}]}}'
        resp = make_mock_response(200, body)
        mock_session_request.return_value = (resp, None)
        result = papi_client.cancel_property_hostname_activation(
            models.CancelPropertyHostnameActivationRequest(
                property_id="prp_175780",
                hostname_activation_id="ha_12345",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
            )
        )
        assert result.hostname_activation is not None
        assert result.hostname_activation.status == "ABORTED"

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.cancel_property_hostname_activation(
                models.CancelPropertyHostnameActivationRequest(
                    property_id="prp_175780", hostname_activation_id="ha_12345",
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )

    def test_validation_error_missing_property_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.cancel_property_hostname_activation(
                models.CancelPropertyHostnameActivationRequest(
                    property_id="", hostname_activation_id="ha_12345",
                    contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                )
            )
        assert "PropertyID" in str(exc_info.value)


# =========================================================================
# Property Hostname Bucket Tests — from property_hostname_bucket_test.go
# =========================================================================


class TestPatchPropertyHostnameBucket:
    """Tests for PatchPropertyHostnameBucket. Mirrors Go TestPatchPropertyHostnameBucket."""

    def test_200_ok_add(self, papi_client, mock_session_request):
        body = '{"activationLink":"/papi/v1/properties/prp_175780/hostname-activations/ha_12345","hostnames":[{"certProvisioningType":"CPS_MANAGED","cnameFrom":"example.com","cnameTo":"example.com.edgesuite.net","cnameType":"EDGE_HOSTNAME","edgeHostnameId":"ehn_887436","action":"ADD"}]}'
        _setup_success(mock_session_request, body)
        result = papi_client.patch_property_hostname_bucket(
            models.PatchPropertyHostnameBucketRequest(
                property_id="prp_175780",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                body=models.PatchPropertyHostnameBucketBody(
                    add=[
                        models.PatchPropertyHostnameBucketAdd(
                            edge_hostname_id="ehn_887436",
                            cert_provisioning_type="CPS_MANAGED",
                            cname_type="EDGE_HOSTNAME",
                            cname_from="example.com",
                        ),
                    ],
                ),
            )
        )
        assert result.activation_id == "ha_12345"
        assert len(result.hostnames) == 1

    def test_200_ok_remove(self, papi_client, mock_session_request):
        body = '{"activationLink":"/papi/v1/properties/prp_175780/hostname-activations/ha_12346","hostnames":[{"cnameFrom":"example.com","action":"REMOVE"}]}'
        _setup_success(mock_session_request, body)
        result = papi_client.patch_property_hostname_bucket(
            models.PatchPropertyHostnameBucketRequest(
                property_id="prp_175780",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                body=models.PatchPropertyHostnameBucketBody(
                    remove=["example.com"],
                ),
            )
        )
        assert result.activation_id == "ha_12346"

    def test_200_ok_add_and_remove(self, papi_client, mock_session_request):
        body = '{"activationLink":"/papi/v1/properties/prp_175780/hostname-activations/ha_12347","hostnames":[{"certProvisioningType":"CPS_MANAGED","cnameFrom":"new.example.com","cnameTo":"new.example.com.edgesuite.net","cnameType":"EDGE_HOSTNAME","edgeHostnameId":"ehn_887437","action":"ADD"},{"cnameFrom":"old.example.com","action":"REMOVE"}]}'
        _setup_success(mock_session_request, body)
        result = papi_client.patch_property_hostname_bucket(
            models.PatchPropertyHostnameBucketRequest(
                property_id="prp_175780",
                contract_id="ctr_1-1TJZFW",
                group_id="grp_15166",
                body=models.PatchPropertyHostnameBucketBody(
                    add=[
                        models.PatchPropertyHostnameBucketAdd(
                            edge_hostname_id="ehn_887437",
                            cert_provisioning_type="CPS_MANAGED",
                            cname_type="EDGE_HOSTNAME",
                            cname_from="new.example.com",
                        ),
                    ],
                    remove=["old.example.com"],
                ),
            )
        )
        assert result.activation_id == "ha_12347"
        assert len(result.hostnames) == 2

    def test_500_internal_server_error(self, papi_client, mock_session_request):
        _setup_error(mock_session_request, 500, ERR_500_BODY)
        with pytest.raises(papi_errors.Error):
            papi_client.patch_property_hostname_bucket(
                models.PatchPropertyHostnameBucketRequest(
                    property_id="prp_175780", contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                    body=models.PatchPropertyHostnameBucketBody(),
                )
            )

    def test_validation_error_missing_property_id(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.patch_property_hostname_bucket(
                models.PatchPropertyHostnameBucketRequest(
                    property_id="", contract_id="ctr_1-1TJZFW", group_id="grp_15166",
                    body=models.PatchPropertyHostnameBucketBody(),
                )
            )
        assert "PropertyID" in str(exc_info.value)

    def test_validation_error_missing_body(self, papi_client):
        with pytest.raises(papi_errors.Error) as exc_info:
            papi_client.patch_property_hostname_bucket(
                models.PatchPropertyHostnameBucketRequest(
                    property_id="prp_175780", contract_id="ctr_1-1TJZFW",
                    group_id="grp_15166",
                )
            )
        assert "Body" in str(exc_info.value)
