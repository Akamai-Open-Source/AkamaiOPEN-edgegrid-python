"""Unit tests for the Application Security API client.

Mirrors all Go pkg/appsec/*_test.go test files.  Every test scenario,
assertion, and fixture from Go is adapted to Python pytest while
preserving VERBATIM ``responseBody`` and ``responseHeaders`` values.
"""
# pylint: disable=too-many-lines

import json

import pytest

from akamai.edgegrid.appsec.errors import Error
from akamai.edgegrid.appsec import models
from akamai.edgegrid.appsec.test.conftest import (
    compact_json,
    load_fixture,
    mock_response,
)


# ---------------------------------------------------------------------------
# Common error response bodies (VERBATIM from Go test files)
# ---------------------------------------------------------------------------

ERROR_FETCHING_PROPERTYS_500 = (
    '{\n    "type": "internal_error",\n'
    '    "title": "Internal Server Error",\n'
    '    "detail": "Error fetching propertys",\n'
    '    "status": 500\n}'
)

ERROR_FETCHING_MATCH_TARGET = (
    '{\n\t\t\t\t"type": "internal_error",\n'
    '\t\t\t\t"title": "Internal Server Error",\n'
    '\t\t\t\t"detail": "Error fetching match target"\n\t\t\t}'
)

ERROR_CREATING_ZONE = (
    '{\n\t\t\t\t"type": "internal_error",\n'
    '\t\t\t\t"title": "Internal Server Error",\n'
    '\t\t\t\t"detail": "Error creating zone"\n\t\t\t}'
)

ERROR_CREATING_DOMAIN = (
    '{\n\t\t\t\t"type": "internal_error",\n'
    '\t\t\t\t"title": "Internal Server Error",\n'
    '\t\t\t\t"detail": "Error creating domain"\n\t\t\t}'
)

ERROR_DELETING_MATCH_TARGET = (
    '{\n\t\t\t\t"type": "internal_error",\n'
    '\t\t\t\t"title": "Internal Server Error",\n'
    '\t\t\t\t"detail": "Error deleting match target"\n\t\t\t}'
)

ERROR_FETCHING_ACTIVATIONS_500 = (
    '{"type":"internal_error","title":"Internal Server Error",'
    '"detail":"Error fetching activations","status":500}'
)

ERROR_SEC_POLICY_DEFAULT_PROTECTIONS_500 = (
    '{"type":"internal_error","title":"Internal Server Error",'
    '"detail":"Error creating security policy with default protections",'
    '"status":500}'
)


# Rapid-rule shared error bodies (VERBATIM from rapid_rule_test.go)
RAPID_BAD_REQUEST = (
    '{\n    "type": '
    '"https://problems.luna.akamaiapis.net/appsec/'
    'error-types/INVALID-INPUT-ERROR",\n'
    '    "title": "Invalid Input Error",\n'
    '    "detail": "configId incorrect type",\n'
    '\t"status": 400\n}'
)
RAPID_INTERNAL_SERVER_ERROR = (
    '{\n    "type": '
    '"https://problems.luna.akamaiapis.net/appsec/'
    'error-types/INVALID-INPUT-ERROR",\n'
    '    "title": "Internal Server Error",\n'
    '    "detail": "The server was unable to complete your request.'
    ' Please try again later.",\n'
    '\t"status": 400\n}'
)

RAPID_ERROR_400 = Error(
    type="https://problems.luna.akamaiapis.net/appsec/"
         "error-types/INVALID-INPUT-ERROR",
    title="Invalid Input Error",
    detail="configId incorrect type",
    status_code=400,
)
RAPID_ERROR_500 = Error(
    type="https://problems.luna.akamaiapis.net/appsec/"
         "error-types/INVALID-INPUT-ERROR",
    title="Internal Server Error",
    detail="The server was unable to complete your request."
           " Please try again later.",
    status_code=500,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _err_500(detail: str, etype: str = "internal_error",
             status_code: int = 500) -> Error:
    """Build a standard 500 Error sentinel."""
    return Error(
        type=etype,
        title="Internal Server Error",
        detail=detail,
        status_code=status_code,
    )


def _success(client, method_name, request_obj, fixture_path):
    """Run a standard success (200-OK) test using a fixture file."""
    fixture_data = load_fixture(fixture_path)
    compact = compact_json(fixture_data)
    expected = json.loads(compact)

    mock_exec = client._session.exec  # pylint: disable=protected-access
    mock_exec.reset_mock()
    mock_exec.side_effect = None
    mock_exec.return_value = (mock_response(200, expected), expected)
    method = getattr(client, method_name)
    result = method(request_obj)
    assert result == expected


def _error(client, method_name, request_obj, expected_error):
    """Run a standard error-path test."""
    mock_exec = client._session.exec  # pylint: disable=protected-access
    mock_exec.reset_mock()
    mock_exec.return_value = None
    mock_exec.side_effect = expected_error
    with pytest.raises(Error) as exc_info:
        method = getattr(client, method_name)
        method(request_obj)
    assert exc_info.value.is_equivalent(expected_error)


# ===================================================================
# TestClient  (mirrors appsec_test.go – TestClient)
# ===================================================================

class TestClient:  # pylint: disable=too-few-public-methods
    """Client factory tests – mirrors appsec_test.go."""

    def test_client_creation(self, mock_appsec_client):
        """Verify Client instantiation with a mocked session."""
        assert mock_appsec_client is not None
        assert mock_appsec_client._session is not None  # pylint: disable=protected-access


# ===================================================================
# TestErrors  (mirrors errors_test.go)
# ===================================================================

class TestErrors:
    """Error parsing tests – mirrors errors_test.go."""

    def test_new_error_valid_response(self):
        """Test Error.from_response with valid JSON body."""
        body = '{"type":"a","title":"b","detail":"c"}'
        resp = mock_response(500, json.loads(body), text_body=body)
        err = Error.from_response(resp)
        assert err.type == "a"
        assert err.title == "b"
        assert err.detail == "c"
        assert err.status_code == 500

    def test_new_error_invalid_body(self):
        """Test Error.from_response with non-JSON body."""
        resp = mock_response(500, None, text_body="test")
        err = Error.from_response(resp)
        assert err.status_code == 500
        assert err.title != ""

    def test_json_error_unmarshalling_html(self):
        """Test Error.from_response handles HTML response."""
        html = "<html><body>Error</body></html>"
        resp = mock_response(500, None, text_body=html)
        err = Error.from_response(resp)
        assert err.status_code == 500

    def test_json_error_unmarshalling_plain_text(self):
        """Test Error.from_response handles plain-text response."""
        resp = mock_response(500, None, text_body="plain error text")
        err = Error.from_response(resp)
        assert err.status_code == 500

    def test_error_is_equivalent(self):
        """Test Error.is_equivalent comparison."""
        err1 = Error(type="a", title="b", detail="c", status_code=500)
        err2 = Error(type="a", title="b", detail="c", status_code=500)
        assert err1.is_equivalent(err2)

    def test_error_not_equivalent(self):
        """Test Error.is_equivalent returns False for mismatched errors."""
        err1 = Error(type="a", title="b", detail="c", status_code=500)
        err2 = Error(type="x", title="y", detail="z", status_code=400)
        assert not err1.is_equivalent(err2)


# ===================================================================
# TestActivations  (mirrors activations_test.go)
# ===================================================================

class TestActivations:
    """Activation endpoint tests – mirrors activations_test.go."""

    def test_list_activations_200(self, mock_appsec_client):
        """Test GetActivationHistory returns correct response on 200 OK."""
        _success(
            mock_appsec_client, "get_activation_history",
            models.GetActivationHistoryRequest(config_id=43253),
            "TestActivations/ActivationHistory.json",
        )

    def test_list_activations_500(self, mock_appsec_client):
        """Test GetActivationHistory raises Error on 500."""
        _error(
            mock_appsec_client, "get_activation_history",
            models.GetActivationHistoryRequest(config_id=43253),
            _err_500("Error fetching activations"),
        )

    def test_get_activations_200(self, mock_appsec_client):
        """Test GetActivations returns correct response on 200 OK."""
        _success(
            mock_appsec_client, "get_activations",
            models.GetActivationsRequest(activation_id=32415),
            "TestActivations/Activations.json",
        )

    def test_get_activations_500(self, mock_appsec_client):
        """Test GetActivations raises Error on 500."""
        _error(
            mock_appsec_client, "get_activations",
            models.GetActivationsRequest(activation_id=32415),
            _err_500("Error fetching activations"),
        )

    def test_create_activations_200(self, mock_appsec_client):
        """Test CreateActivations returns correct response on 200 OK."""
        _success(
            mock_appsec_client, "create_activations",
            models.CreateActivationsRequest(
                action="ACTIVATE",
                network="STAGING", note="test",
                notification_emails=["test@example.com"],
                activation_configs=[],
            ),
            "TestActivations/Activations.json",
        )

    def test_create_activations_500(self, mock_appsec_client):
        """Test CreateActivations raises Error on 500."""
        _error(
            mock_appsec_client, "create_activations",
            models.CreateActivationsRequest(
                action="ACTIVATE",
                network="STAGING", note="test",
                notification_emails=["test@example.com"],
                activation_configs=[],
            ),
            _err_500("Error fetching activations"),
        )

    def test_remove_activations_200(self, mock_appsec_client):
        """Test RemoveActivations returns correct response on 200 OK."""
        _success(
            mock_appsec_client, "remove_activations",
            models.RemoveActivationsRequest(
                action="DEACTIVATE",
                network="STAGING", note="test",
                notification_emails=["test@example.com"],
                activation_configs=[],
            ),
            "TestActivations/Activations.json",
        )

    def test_remove_activations_500(self, mock_appsec_client):
        """Test RemoveActivations raises Error on 500."""
        _error(
            mock_appsec_client, "remove_activations",
            models.RemoveActivationsRequest(
                action="DEACTIVATE",
                network="STAGING", note="test",
                notification_emails=["test@example.com"],
                activation_configs=[],
            ),
            _err_500("Error fetching activations"),
        )


# ===================================================================
# TestConfigurations  (mirrors configuration_test.go)
# ===================================================================

class TestConfigurations:
    """Configuration endpoint tests – mirrors configuration_test.go."""

    def test_list_configurations_200(self, mock_appsec_client):
        """Test GetConfigurations returns correct response on 200 OK."""
        _success(
            mock_appsec_client, "get_configurations",
            models.GetConfigurationsRequest(),
            "TestConfiguration/Configuration.json",
        )

    def test_list_configurations_500(self, mock_appsec_client):
        """Test GetConfigurations raises Error on 500."""
        _error(
            mock_appsec_client, "get_configurations",
            models.GetConfigurationsRequest(),
            _err_500("Error fetching propertys"),
        )

    def test_get_configuration_200(self, mock_appsec_client):
        """Test GetConfiguration returns correct response on 200 OK."""
        _success(
            mock_appsec_client, "get_configuration",
            models.GetConfigurationRequest(config_id=43253),
            "TestConfiguration/Configuration.json",
        )

    def test_get_configuration_500(self, mock_appsec_client):
        """Test GetConfiguration raises Error on 500."""
        _error(
            mock_appsec_client, "get_configuration",
            models.GetConfigurationRequest(config_id=43253),
            _err_500("Error fetching propertys"),
        )

    def test_create_configuration_201(self, mock_appsec_client):
        """Test CreateConfiguration returns correct response on 201."""
        _success(
            mock_appsec_client, "create_configuration",
            models.CreateConfigurationRequest(
                name="TestConfig", description="test",
                contract_id="ctr_1", group_id=12345,
            ),
            "TestConfiguration/Configuration.json",
        )

    def test_create_configuration_500(self, mock_appsec_client):
        """Test CreateConfiguration raises Error on 500."""
        _error(
            mock_appsec_client, "create_configuration",
            models.CreateConfigurationRequest(
                name="TestConfig", description="test",
                contract_id="ctr_1", group_id=12345,
            ),
            _err_500("Error creating domain"),
        )

    def test_update_configuration_200(self, mock_appsec_client):
        """Test UpdateConfiguration returns correct response on 200 OK."""
        _success(
            mock_appsec_client, "update_configuration",
            models.UpdateConfigurationRequest(
                config_id=43253, name="TestConfig",
                description="updated",
            ),
            "TestConfiguration/Configuration.json",
        )

    def test_update_configuration_500(self, mock_appsec_client):
        """Test UpdateConfiguration raises Error on 500."""
        _error(
            mock_appsec_client, "update_configuration",
            models.UpdateConfigurationRequest(
                config_id=43253, name="TestConfig",
                description="updated",
            ),
            _err_500("Error creating zone"),
        )

    def test_remove_configuration_200(self, mock_appsec_client):
        """Test RemoveConfiguration returns correct response on 200 OK."""
        _success(
            mock_appsec_client, "remove_configuration",
            models.RemoveConfigurationRequest(config_id=43253),
            "TestConfiguration/Configuration.json",
        )

    def test_remove_configuration_500(self, mock_appsec_client):
        """Test RemoveConfiguration raises Error on 500."""
        _error(
            mock_appsec_client, "remove_configuration",
            models.RemoveConfigurationRequest(config_id=43253),
            _err_500("Error deleting match target"),
        )


# ===================================================================
# TestConfigurationClone  (mirrors configuration_clone_test.go)
# ===================================================================

class TestConfigurationClone:
    """Config clone tests – mirrors configuration_clone_test.go."""

    def test_get_configuration_clone_200(self, mock_appsec_client):
        """Test GetConfigurationClone on 200 OK."""
        _success(
            mock_appsec_client, "get_configuration_clone",
            models.GetConfigurationCloneRequest(
                config_id=43253, version=15,
            ),
            "TestConfigurationClone/ConfigurationClone.json",
        )

    def test_get_configuration_clone_500(self, mock_appsec_client):
        """Test GetConfigurationClone raises Error on 500."""
        _error(
            mock_appsec_client, "get_configuration_clone",
            models.GetConfigurationCloneRequest(
                config_id=43253, version=15,
            ),
            _err_500("Error fetching propertys"),
        )

    def test_create_configuration_clone_200(self, mock_appsec_client):
        """Test CreateConfigurationClone on 200 OK."""
        _success(
            mock_appsec_client, "create_configuration_clone",
            models.CreateConfigurationCloneRequest(
                create_from={"configId": 43253, "configVersion": 15},
            ),
            "TestConfigurationClone/ConfigurationClone.json",
        )

    def test_create_configuration_clone_500(self, mock_appsec_client):
        """Test CreateConfigurationClone raises Error on 500."""
        _error(
            mock_appsec_client, "create_configuration_clone",
            models.CreateConfigurationCloneRequest(
                create_from={"configId": 43253, "configVersion": 15},
            ),
            _err_500("Error creating domain"),
        )


# ===================================================================
# TestConfigurationVersion  (mirrors configuration_version_test.go)
# ===================================================================

class TestConfigurationVersion:
    """Config version tests – mirrors configuration_version_test.go."""

    def test_list_configuration_versions_200(self, mock_appsec_client):
        """Test GetConfigurationVersions on 200 OK."""
        _success(
            mock_appsec_client, "get_configuration_versions",
            models.GetConfigurationVersionsRequest(config_id=43253),
            "TestConfigurationVersion/ConfigurationVersion.json",
        )

    def test_list_configuration_versions_500(self, mock_appsec_client):
        """Test GetConfigurationVersions raises Error on 500."""
        _error(
            mock_appsec_client, "get_configuration_versions",
            models.GetConfigurationVersionsRequest(config_id=43253),
            _err_500("Error fetching propertys"),
        )

    def test_get_configuration_version_200(self, mock_appsec_client):
        """Test GetConfigurationVersion on 200 OK."""
        _success(
            mock_appsec_client, "get_configuration_version",
            models.GetConfigurationVersionRequest(
                config_id=43253, version=2,
            ),
            "TestConfigurationVersion/ConfigurationVersion.json",
        )

    def test_get_configuration_version_500(self, mock_appsec_client):
        """Test GetConfigurationVersion raises Error on 500."""
        _error(
            mock_appsec_client, "get_configuration_version",
            models.GetConfigurationVersionRequest(
                config_id=43253, version=2,
            ),
            _err_500("Error fetching propertys"),
        )


# ===================================================================
# TestConfigurationVersionClone  (mirrors configuration_version_clone_test.go)
# ===================================================================

class TestConfigurationVersionClone:
    """Config version clone tests – mirrors configuration_version_clone_test.go."""

    def test_get_configuration_version_clone_200(self, mock_appsec_client):
        """Test GetConfigurationVersionClone on 200 OK."""
        _success(
            mock_appsec_client, "get_configuration_version_clone",
            models.GetConfigurationVersionCloneRequest(
                config_id=43253, version=15,
            ),
            "TestConfigurationVersionClone/ConfigurationVersionClone.json",
        )

    def test_get_configuration_version_clone_500(self, mock_appsec_client):
        """Test GetConfigurationVersionClone raises Error on 500."""
        _error(
            mock_appsec_client, "get_configuration_version_clone",
            models.GetConfigurationVersionCloneRequest(
                config_id=43253, version=15,
            ),
            _err_500("Error fetching propertys"),
        )

    def test_create_configuration_version_clone_200(self, mock_appsec_client):
        """Test CreateConfigurationVersionClone on 200 OK."""
        _success(
            mock_appsec_client, "create_configuration_version_clone",
            models.CreateConfigurationVersionCloneRequest(
                config_id=43253, create_from_version=15,
            ),
            "TestConfigurationVersionClone/ConfigurationVersionClone.json",
        )

    def test_create_configuration_version_clone_500(self, mock_appsec_client):
        """Test CreateConfigurationVersionClone raises Error on 500."""
        _error(
            mock_appsec_client, "create_configuration_version_clone",
            models.CreateConfigurationVersionCloneRequest(
                config_id=43253, create_from_version=15,
            ),
            _err_500("Error creating domain"),
        )


# ===================================================================
# TestSecurityPolicy  (mirrors security_policy_test.go)
# ===================================================================

class TestSecurityPolicy:
    """Security policy tests – mirrors security_policy_test.go."""

    def test_list_security_policies_200(self, mock_appsec_client):
        """Test GetSecurityPolicies on 200 OK."""
        _success(
            mock_appsec_client, "get_security_policies",
            models.GetSecurityPoliciesRequest(
                config_id=43253, version=15,
            ),
            "TestSecurityPolicy/SecurityPolicy.json",
        )

    def test_list_security_policies_500(self, mock_appsec_client):
        """Test GetSecurityPolicies raises Error on 500."""
        _error(
            mock_appsec_client, "get_security_policies",
            models.GetSecurityPoliciesRequest(
                config_id=43253, version=15,
            ),
            _err_500("Error fetching propertys"),
        )

    def test_get_security_policy_200(self, mock_appsec_client):
        """Test GetSecurityPolicy on 200 OK."""
        _success(
            mock_appsec_client, "get_security_policy",
            models.GetSecurityPolicyRequest(
                config_id=43253, version=15, policy_id="AAAA_81230",
            ),
            "TestSecurityPolicy/SecurityPolicy.json",
        )

    def test_get_security_policy_500(self, mock_appsec_client):
        """Test GetSecurityPolicy raises Error on 500."""
        _error(
            mock_appsec_client, "get_security_policy",
            models.GetSecurityPolicyRequest(
                config_id=43253, version=15, policy_id="AAAA_81230",
            ),
            _err_500("Error fetching propertys"),
        )

    def test_create_security_policy_200(self, mock_appsec_client):
        """Test CreateSecurityPolicy on 200 OK."""
        _success(
            mock_appsec_client, "create_security_policy",
            models.CreateSecurityPolicyRequest(
                config_id=43253, version=15,
                policy_name="TestPolicy", policy_prefix="TEST",
            ),
            "TestSecurityPolicy/SecurityPolicy.json",
        )

    def test_create_security_policy_500(self, mock_appsec_client):
        """Test CreateSecurityPolicy raises Error on 500."""
        _error(
            mock_appsec_client, "create_security_policy",
            models.CreateSecurityPolicyRequest(
                config_id=43253, version=15,
                policy_name="TestPolicy", policy_prefix="TEST",
            ),
            _err_500("Error creating domain"),
        )

    def test_create_security_policy_with_default_protections_200(
        self, mock_appsec_client,
    ):
        """Test CreateSecurityPolicyWithDefaultProtections on 200 OK."""
        _success(
            mock_appsec_client,
            "create_security_policy_with_default_protections",
            models.CreateSecurityPolicyWithDefaultProtectionsRequest(
                config_id=43253, version=15,
                policy_name="TestPolicy", policy_prefix="TEST",
            ),
            "TestSecurityPolicy/SecurityPolicy.json",
        )

    def test_create_security_policy_with_default_protections_500(
        self, mock_appsec_client,
    ):
        """Test CreateSecurityPolicyWithDefaultProtections raises Error."""
        _error(
            mock_appsec_client,
            "create_security_policy_with_default_protections",
            models.CreateSecurityPolicyWithDefaultProtectionsRequest(
                config_id=43253, version=15,
                policy_name="TestPolicy", policy_prefix="TEST",
            ),
            _err_500(
                "Error creating security policy with default protections",
            ),
        )

    def test_update_security_policy_200(self, mock_appsec_client):
        """Test UpdateSecurityPolicy on 200 OK."""
        _success(
            mock_appsec_client, "update_security_policy",
            models.UpdateSecurityPolicyRequest(
                config_id=43253, version=15, policy_id="AAAA_81230",
            ),
            "TestSecurityPolicy/SecurityPolicy.json",
        )

    def test_update_security_policy_500(self, mock_appsec_client):
        """Test UpdateSecurityPolicy raises Error on 500."""
        _error(
            mock_appsec_client, "update_security_policy",
            models.UpdateSecurityPolicyRequest(
                config_id=43253, version=15, policy_id="AAAA_81230",
            ),
            _err_500("Error creating zone"),
        )

    def test_remove_security_policy_200(self, mock_appsec_client):
        """Test RemoveSecurityPolicy on 200 OK."""
        _success(
            mock_appsec_client, "remove_security_policy",
            models.RemoveSecurityPolicyRequest(
                config_id=43253, version=15, policy_id="AAAA_81230",
            ),
            "TestSecurityPolicy/SecurityPolicy.json",
        )

    def test_remove_security_policy_500(self, mock_appsec_client):
        """Test RemoveSecurityPolicy raises Error on 500."""
        _error(
            mock_appsec_client, "remove_security_policy",
            models.RemoveSecurityPolicyRequest(
                config_id=43253, version=15, policy_id="AAAA_81230",
            ),
            _err_500("Error deleting match target"),
        )


# ===================================================================
# TestSecurityPolicyClone  (mirrors security_policy_clone_test.go)
# ===================================================================

class TestSecurityPolicyClone:
    """Security policy clone tests – mirrors security_policy_clone_test.go."""

    def test_get_security_policy_clone_200(self, mock_appsec_client):
        """Test GetSecurityPolicyClone on 200 OK."""
        _success(
            mock_appsec_client, "get_security_policy_clone",
            models.GetSecurityPolicyCloneRequest(
                config_id=43253, version=15, policy_id="AAAA_81230",
            ),
            "TestSecurityPolicyClone/SecurityPolicyClone.json",
        )

    def test_get_security_policy_clone_500(self, mock_appsec_client):
        """Test GetSecurityPolicyClone raises Error on 500."""
        _error(
            mock_appsec_client, "get_security_policy_clone",
            models.GetSecurityPolicyCloneRequest(
                config_id=43253, version=15, policy_id="AAAA_81230",
            ),
            _err_500("Error fetching propertys"),
        )

    def test_create_security_policy_clone_200(self, mock_appsec_client):
        """Test CreateSecurityPolicyClone on 200 OK."""
        _success(
            mock_appsec_client, "create_security_policy_clone",
            models.CreateSecurityPolicyCloneRequest(
                config_id=43253, version=15,
            ),
            "TestSecurityPolicyClone/SecurityPolicyClone.json",
        )

    def test_create_security_policy_clone_500(self, mock_appsec_client):
        """Test CreateSecurityPolicyClone raises Error on 500."""
        _error(
            mock_appsec_client, "create_security_policy_clone",
            models.CreateSecurityPolicyCloneRequest(
                config_id=43253, version=15,
            ),
            _err_500("Error creating domain"),
        )


# ===================================================================
# TestPolicyProtections  (mirrors security_policy_protections_test.go)
# ===================================================================

class TestPolicyProtections:
    """Policy protections tests – mirrors security_policy_protections_test.go."""

    def test_get_policy_protections_200(self, mock_appsec_client):
        """Test GetPolicyProtections on 200 OK."""
        _success(
            mock_appsec_client, "get_policy_protections",
            models.GetPolicyProtectionsRequest(
                config_id=43253, version=15, policy_id="AAAA_81230",
            ),
            "TestPolicyProtections/PolicyProtections.json",
        )

    def test_get_policy_protections_500(self, mock_appsec_client):
        """Test GetPolicyProtections raises Error on 500."""
        _error(
            mock_appsec_client, "get_policy_protections",
            models.GetPolicyProtectionsRequest(
                config_id=43253, version=15, policy_id="AAAA_81230",
            ),
            _err_500("Error fetching propertys"),
        )

    def test_update_policy_protections_200(self, mock_appsec_client):
        """Test UpdatePolicyProtections on 200 OK."""
        _success(
            mock_appsec_client, "update_policy_protections",
            models.UpdatePolicyProtectionsRequest(
                config_id=43253, version=15, policy_id="AAAA_81230",
            ),
            "TestPolicyProtections/PolicyProtections.json",
        )

    def test_update_policy_protections_500(self, mock_appsec_client):
        """Test UpdatePolicyProtections raises Error on 500."""
        _error(
            mock_appsec_client, "update_policy_protections",
            models.UpdatePolicyProtectionsRequest(
                config_id=43253, version=15, policy_id="AAAA_81230",
            ),
            _err_500("Error creating zone"),
        )


# ===================================================================
# TestCustomRules  (mirrors custom_rule_test.go)
# ===================================================================

class TestCustomRules:
    """Custom rule tests – mirrors custom_rule_test.go."""

    def test_list_custom_rules_200(self, mock_appsec_client):
        """Test GetCustomRules on 200 OK."""
        _success(
            mock_appsec_client, "get_custom_rules",
            models.GetCustomRulesRequest(config_id=43253),
            "TestCustomRules/CustomRules.json",
        )

    def test_list_custom_rules_500(self, mock_appsec_client):
        """Test GetCustomRules raises Error on 500."""
        _error(
            mock_appsec_client, "get_custom_rules",
            models.GetCustomRulesRequest(config_id=43253),
            _err_500("Error fetching propertys"),
        )

    def test_get_custom_rule_200(self, mock_appsec_client):
        """Test GetCustomRule on 200 OK."""
        _success(
            mock_appsec_client, "get_custom_rule",
            models.GetCustomRuleRequest(config_id=43253, id=60039625),
            "TestCustomRules/CustomRule.json",
        )

    def test_get_custom_rule_500(self, mock_appsec_client):
        """Test GetCustomRule raises Error on 500."""
        _error(
            mock_appsec_client, "get_custom_rule",
            models.GetCustomRuleRequest(config_id=43253, id=60039625),
            _err_500("Error fetching match target"),
        )

    def test_create_custom_rule_201(self, mock_appsec_client):
        """Test CreateCustomRule on 201 Created."""
        _success(
            mock_appsec_client, "create_custom_rule",
            models.CreateCustomRuleRequest(config_id=43253),
            "TestCustomRules/CustomRule.json",
        )

    def test_create_custom_rule_500(self, mock_appsec_client):
        """Test CreateCustomRule raises Error on 500."""
        _error(
            mock_appsec_client, "create_custom_rule",
            models.CreateCustomRuleRequest(config_id=43253),
            _err_500("Error creating domain"),
        )

    def test_update_custom_rule_200(self, mock_appsec_client):
        """Test UpdateCustomRule on 200 Success."""
        _success(
            mock_appsec_client, "update_custom_rule",
            models.UpdateCustomRuleRequest(config_id=43253, id=60039625),
            "TestCustomRules/CustomRule.json",
        )

    def test_update_custom_rule_500(self, mock_appsec_client):
        """Test UpdateCustomRule raises Error on 500."""
        _error(
            mock_appsec_client, "update_custom_rule",
            models.UpdateCustomRuleRequest(config_id=43253, id=60039625),
            _err_500("Error creating zone"),
        )

    def test_remove_custom_rule_200(self, mock_appsec_client):
        """Test RemoveCustomRule on 200 Success."""
        _success(
            mock_appsec_client, "remove_custom_rule",
            models.RemoveCustomRuleRequest(config_id=43253, id=60039625),
            "TestCustomRules/CustomRulesEmpty.json",
        )

    def test_remove_custom_rule_500(self, mock_appsec_client):
        """Test RemoveCustomRule raises Error on 500."""
        _error(
            mock_appsec_client, "remove_custom_rule",
            models.RemoveCustomRuleRequest(config_id=43253, id=60039625),
            _err_500("Error deleting match target"),
        )


# ===================================================================
# TestCustomRuleAction  (mirrors custom_rule_action_test.go)
# ===================================================================

class TestCustomRuleAction:
    """Custom rule action tests – mirrors custom_rule_action_test.go."""

    def test_list_custom_rule_actions_200(self, mock_appsec_client):
        """Test GetCustomRuleActions on 200 OK."""
        _success(
            mock_appsec_client, "get_custom_rule_actions",
            models.GetCustomRuleActionsRequest(
                config_id=43253, version=15, policy_id="AAAA_81230",
            ),
            "TestCustomRuleAction/CustomRuleAction.json",
        )

    def test_list_custom_rule_actions_500(self, mock_appsec_client):
        """Test GetCustomRuleActions raises Error on 500."""
        _error(
            mock_appsec_client, "get_custom_rule_actions",
            models.GetCustomRuleActionsRequest(
                config_id=43253, version=15, policy_id="AAAA_81230",
            ),
            _err_500("Error fetching propertys"),
        )

    def test_get_custom_rule_action_200(self, mock_appsec_client):
        """Test GetCustomRuleAction on 200 OK."""
        _success(
            mock_appsec_client, "get_custom_rule_action",
            models.GetCustomRuleActionRequest(
                config_id=43253, version=15, policy_id="AAAA_81230",
            ),
            "TestCustomRuleAction/CustomRuleAction.json",
        )

    def test_get_custom_rule_action_500(self, mock_appsec_client):
        """Test GetCustomRuleAction raises Error on 500."""
        _error(
            mock_appsec_client, "get_custom_rule_action",
            models.GetCustomRuleActionRequest(
                config_id=43253, version=15, policy_id="AAAA_81230",
            ),
            _err_500("Error fetching propertys"),
        )

    def test_update_custom_rule_action_200(self, mock_appsec_client):
        """Test UpdateCustomRuleAction on 200 OK."""
        _success(
            mock_appsec_client, "update_custom_rule_action",
            models.UpdateCustomRuleActionRequest(
                config_id=43253, version=15, policy_id="AAAA_81230",
                rule_id=12345,
            ),
            "TestCustomRuleAction/CustomRuleAction.json",
        )

    def test_update_custom_rule_action_500(self, mock_appsec_client):
        """Test UpdateCustomRuleAction raises Error on 500."""
        _error(
            mock_appsec_client, "update_custom_rule_action",
            models.UpdateCustomRuleActionRequest(
                config_id=43253, version=15, policy_id="AAAA_81230",
                rule_id=12345,
            ),
            _err_500("Error creating zone"),
        )


# ===================================================================
# TestCustomDeny  (mirrors custom_deny_test.go)
# ===================================================================

class TestCustomDeny:
    """Custom deny tests – mirrors custom_deny_test.go."""

    def test_list_custom_deny_200(self, mock_appsec_client):
        """Test GetCustomDenyList on 200 OK."""
        _success(mock_appsec_client, "get_custom_deny_list",
                 models.GetCustomDenyListRequest(config_id=43253, version=15),
                 "TestCustomDeny/CustomDenyList.json")

    def test_list_custom_deny_500(self, mock_appsec_client):
        """Test GetCustomDenyList raises Error on 500."""
        _error(mock_appsec_client, "get_custom_deny_list",
               models.GetCustomDenyListRequest(config_id=43253, version=15),
               _err_500("Error fetching propertys"))

    def test_get_custom_deny_200(self, mock_appsec_client):
        """Test GetCustomDeny on 200 OK."""
        _success(mock_appsec_client, "get_custom_deny",
                 models.GetCustomDenyRequest(config_id=43253, version=15, id="622919"),
                 "TestCustomDeny/CustomDeny.json")

    def test_get_custom_deny_500(self, mock_appsec_client):
        """Test GetCustomDeny raises Error on 500."""
        _error(mock_appsec_client, "get_custom_deny",
               models.GetCustomDenyRequest(config_id=43253, version=15, id="622919"),
               _err_500("Error fetching match target"))

    def test_create_custom_deny_201(self, mock_appsec_client):
        """Test CreateCustomDeny on 201 Created."""
        _success(mock_appsec_client, "create_custom_deny",
                 models.CreateCustomDenyRequest(config_id=43253, version=15),
                 "TestCustomDeny/CustomDeny.json")

    def test_create_custom_deny_500(self, mock_appsec_client):
        """Test CreateCustomDeny raises Error on 500."""
        _error(mock_appsec_client, "create_custom_deny",
               models.CreateCustomDenyRequest(config_id=43253, version=15),
               _err_500("Error creating domain"))

    def test_update_custom_deny_200(self, mock_appsec_client):
        """Test UpdateCustomDeny on 200 Success."""
        _success(mock_appsec_client, "update_custom_deny",
                 models.UpdateCustomDenyRequest(
                     config_id=43253, version=15, id="deny_custom_622918"),
                 "TestCustomDeny/CustomDeny.json")

    def test_update_custom_deny_500(self, mock_appsec_client):
        """Test UpdateCustomDeny raises Error on 500."""
        _error(mock_appsec_client, "update_custom_deny",
               models.UpdateCustomDenyRequest(
                   config_id=43253, version=15, id="deny_custom_622918"),
               _err_500("Error creating zone"))

    def test_remove_custom_deny_200(self, mock_appsec_client):
        """Test RemoveCustomDeny on 200 Success."""
        _success(mock_appsec_client, "remove_custom_deny",
                 models.RemoveCustomDenyRequest(
                     config_id=43253, version=15, id="deny_custom_622918"),
                 "TestCustomDeny/CustomDeny.json")

    def test_remove_custom_deny_500(self, mock_appsec_client):
        """Test RemoveCustomDeny raises Error on 500."""
        _error(mock_appsec_client, "remove_custom_deny",
               models.RemoveCustomDenyRequest(
                   config_id=43253, version=15, id="deny_custom_622918"),
               _err_500("Error deleting match target"))


# ===================================================================
# TestRatePolicies  (mirrors rate_policy_test.go)
# ===================================================================

class TestRatePolicies:
    """Rate policy tests – mirrors rate_policy_test.go."""

    def test_list_rate_policies_200(self, mock_appsec_client):
        """Test GetRatePolicies on 200 OK."""
        _success(mock_appsec_client, "get_rate_policies",
                 models.GetRatePoliciesRequest(config_id=43253, config_version=15),
                 "TestRatePolicies/RatePolicies.json")

    def test_list_rate_policies_500(self, mock_appsec_client):
        """Test GetRatePolicies raises Error on 500."""
        _error(mock_appsec_client, "get_rate_policies",
               models.GetRatePoliciesRequest(config_id=43253, config_version=15),
               _err_500("Error fetching propertys"))

    def test_get_rate_policy_200(self, mock_appsec_client):
        """Test GetRatePolicy on 200 OK."""
        _success(mock_appsec_client, "get_rate_policy",
                 models.GetRatePolicyRequest(
                     config_id=43253, config_version=15, rate_policy_id=134644),
                 "TestRatePolicies/RatePolicy.json")

    def test_get_rate_policy_500(self, mock_appsec_client):
        """Test GetRatePolicy raises Error on 500."""
        _error(mock_appsec_client, "get_rate_policy",
               models.GetRatePolicyRequest(
                   config_id=43253, config_version=15, rate_policy_id=134644),
               _err_500("Error fetching match target"))

    def test_create_rate_policy_200(self, mock_appsec_client):
        """Test CreateRatePolicy on 200 OK."""
        _success(mock_appsec_client, "create_rate_policy",
                 models.CreateRatePolicyRequest(config_id=43253, config_version=15),
                 "TestRatePolicies/RatePolicy.json")

    def test_create_rate_policy_500(self, mock_appsec_client):
        """Test CreateRatePolicy raises Error on 500."""
        _error(mock_appsec_client, "create_rate_policy",
               models.CreateRatePolicyRequest(config_id=43253, config_version=15),
               _err_500("Error creating domain"))

    def test_update_rate_policy_200(self, mock_appsec_client):
        """Test UpdateRatePolicy on 200 Success."""
        _success(mock_appsec_client, "update_rate_policy",
                 models.UpdateRatePolicyRequest(
                     config_id=43253, config_version=15, rate_policy_id=134644),
                 "TestRatePolicies/RatePolicy.json")

    def test_update_rate_policy_500(self, mock_appsec_client):
        """Test UpdateRatePolicy raises Error on 500."""
        _error(mock_appsec_client, "update_rate_policy",
               models.UpdateRatePolicyRequest(
                   config_id=43253, config_version=15, rate_policy_id=134644),
               _err_500("Error creating zone"))

    def test_remove_rate_policy_200(self, mock_appsec_client):
        """Test RemoveRatePolicy on 200 Success."""
        _success(mock_appsec_client, "remove_rate_policy",
                 models.RemoveRatePolicyRequest(
                     config_id=43253, config_version=15, rate_policy_id=134644),
                 "TestRatePolicies/RatePolicy.json")

    def test_remove_rate_policy_500(self, mock_appsec_client):
        """Test RemoveRatePolicy raises Error on 500."""
        _error(mock_appsec_client, "remove_rate_policy",
               models.RemoveRatePolicyRequest(
                   config_id=43253, config_version=15, rate_policy_id=134644),
               _err_500("Error deleting match target"))


# ===================================================================
# TestRatePolicyAction  (mirrors rate_policy_action_test.go)
# ===================================================================

class TestRatePolicyAction:
    """Rate policy action tests – mirrors rate_policy_action_test.go."""

    def test_list_rate_policy_actions_200(self, mock_appsec_client):
        """Test GetRatePolicyActions on 200 OK."""
        _success(mock_appsec_client, "get_rate_policy_actions",
                 models.GetRatePolicyActionsRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestRatePolicyAction/RatePolicyActions.json")

    def test_list_rate_policy_actions_500(self, mock_appsec_client):
        """Test GetRatePolicyActions raises Error on 500."""
        _error(mock_appsec_client, "get_rate_policy_actions",
               models.GetRatePolicyActionsRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching propertys"))

    def test_update_rate_policy_action_200(self, mock_appsec_client):
        """Test UpdateRatePolicyAction on 200 OK."""
        _success(mock_appsec_client, "update_rate_policy_action",
                 models.UpdateRatePolicyActionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230",
                     rate_policy_id=134644),
                 "TestRatePolicyAction/RatePolicyActions.json")

    def test_update_rate_policy_action_500(self, mock_appsec_client):
        """Test UpdateRatePolicyAction raises Error on 500."""
        _error(mock_appsec_client, "update_rate_policy_action",
               models.UpdateRatePolicyActionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230",
                   rate_policy_id=134644),
               _err_500("Error creating zone"))


# ===================================================================
# TestEval  (mirrors eval_test.go)
# ===================================================================

class TestEval:
    """Eval tests – mirrors eval_test.go."""

    def test_list_eval_200(self, mock_appsec_client):
        """Test GetEvals (list) on 200 OK."""
        _success(mock_appsec_client, "get_evals",
                 models.GetEvalRequest(config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestEval/Eval.json")

    def test_list_eval_500(self, mock_appsec_client):
        """Test GetEvals raises Error on 500."""
        _error(mock_appsec_client, "get_evals",
               models.GetEvalRequest(config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_get_eval_200(self, mock_appsec_client):
        """Test GetEval on 200 OK."""
        _success(mock_appsec_client, "get_eval",
                 models.GetEvalRequest(config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestEval/Eval.json")

    def test_get_eval_500(self, mock_appsec_client):
        """Test GetEval raises Error on 500."""
        _error(mock_appsec_client, "get_eval",
               models.GetEvalRequest(config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_update_eval_200(self, mock_appsec_client):
        """Test UpdateEval on 200 OK."""
        _success(mock_appsec_client, "update_eval",
                 models.UpdateEvalRequest(config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestEval/Eval.json")

    def test_update_eval_500(self, mock_appsec_client):
        """Test UpdateEval raises Error on 500."""
        _error(mock_appsec_client, "update_eval",
               models.UpdateEvalRequest(config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error creating zone"))

    def test_remove_eval_200(self, mock_appsec_client):
        """Test RemoveEval on 200 OK."""
        _success(mock_appsec_client, "remove_eval",
                 models.RemoveEvalRequest(config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestEval/Eval.json")

    def test_remove_eval_500(self, mock_appsec_client):
        """Test RemoveEval raises Error on 500."""
        _error(mock_appsec_client, "remove_eval",
               models.RemoveEvalRequest(config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error creating zone"))


# ===================================================================
# TestEvalRule  (mirrors eval_rule_test.go)
# ===================================================================

class TestEvalRule:
    """Eval rule tests – mirrors eval_rule_test.go."""

    def test_list_eval_rules_200(self, mock_appsec_client):
        """Test GetEvalRules on 200 OK."""
        _success(mock_appsec_client, "get_eval_rules",
                 models.GetEvalRulesRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestEvalRule/EvalRule.json")

    def test_list_eval_rules_500(self, mock_appsec_client):
        """Test GetEvalRules raises Error on 500."""
        _error(mock_appsec_client, "get_eval_rules",
               models.GetEvalRulesRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_get_eval_rule_200(self, mock_appsec_client):
        """Test GetEvalRule on 200 OK."""
        _success(mock_appsec_client, "get_eval_rule",
                 models.GetEvalRuleRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230", rule_id=12345),
                 "TestEvalRule/EvalRule.json")

    def test_get_eval_rule_500(self, mock_appsec_client):
        """Test GetEvalRule raises Error on 500."""
        _error(mock_appsec_client, "get_eval_rule",
               models.GetEvalRuleRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230", rule_id=12345),
               _err_500("Error fetching match target"))

    def test_update_eval_rule_200(self, mock_appsec_client):
        """Test UpdateEvalRule on 200 OK."""
        _success(mock_appsec_client, "update_eval_rule",
                 models.UpdateEvalRuleRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230", rule_id=12345),
                 "TestEvalRule/EvalRule.json")

    def test_update_eval_rule_500(self, mock_appsec_client):
        """Test UpdateEvalRule raises Error on 500."""
        _error(mock_appsec_client, "update_eval_rule",
               models.UpdateEvalRuleRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230", rule_id=12345),
               _err_500("Error creating zone"))


# ===================================================================
# TestEvalGroup  (mirrors eval_group_test.go)
# ===================================================================

class TestEvalGroup:
    """Eval group tests – mirrors eval_group_test.go."""

    def test_list_eval_groups_200(self, mock_appsec_client):
        """Test GetEvalGroups on 200 OK."""
        _success(mock_appsec_client, "get_eval_groups",
                 models.GetAttackGroupsRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestEvalHost/EvalHost.json")

    def test_list_eval_groups_500(self, mock_appsec_client):
        """Test GetEvalGroups raises Error on 500."""
        _error(mock_appsec_client, "get_eval_groups",
               models.GetAttackGroupsRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_get_eval_group_200(self, mock_appsec_client):
        """Test GetEvalGroup on 200 OK."""
        _success(mock_appsec_client, "get_eval_group",
                 models.GetAttackGroupRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230", group="SQL"),
                 "TestEvalHost/EvalHost.json")

    def test_get_eval_group_500(self, mock_appsec_client):
        """Test GetEvalGroup raises Error on 500."""
        _error(mock_appsec_client, "get_eval_group",
               models.GetAttackGroupRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230", group="SQL"),
               _err_500("Error fetching match target"))

    def test_update_eval_group_200(self, mock_appsec_client):
        """Test UpdateEvalGroup on 200 OK."""
        _success(mock_appsec_client, "update_eval_group",
                 models.UpdateAttackGroupRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230", group="SQL"),
                 "TestEvalHost/EvalHost.json")

    def test_update_eval_group_500(self, mock_appsec_client):
        """Test UpdateEvalGroup raises Error on 500."""
        _error(mock_appsec_client, "update_eval_group",
               models.UpdateAttackGroupRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230", group="SQL"),
               _err_500("Error creating zone"))


# ===================================================================
# TestEvalPenaltyBox  (mirrors eval_penalty_box_test.go)
# ===================================================================

class TestEvalPenaltyBox:
    """Eval penalty box tests – mirrors eval_penalty_box_test.go."""

    def test_get_eval_penalty_box_200(self, mock_appsec_client):
        """Test GetEvalPenaltyBox on 200 OK."""
        _success(mock_appsec_client, "get_eval_penalty_box",
                 models.GetPenaltyBoxRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestEvalProtectHost/EvalProtectHost.json")

    def test_get_eval_penalty_box_500(self, mock_appsec_client):
        """Test GetEvalPenaltyBox raises Error on 500."""
        _error(mock_appsec_client, "get_eval_penalty_box",
               models.GetPenaltyBoxRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_update_eval_penalty_box_200(self, mock_appsec_client):
        """Test UpdateEvalPenaltyBox on 200 OK."""
        _success(mock_appsec_client, "update_eval_penalty_box",
                 models.UpdatePenaltyBoxRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230",
                     penalty_box_protection=False, action="deny"),
                 "TestEvalProtectHost/EvalProtectHost.json")

    def test_update_eval_penalty_box_500(self, mock_appsec_client):
        """Test UpdateEvalPenaltyBox raises Error on 500."""
        _error(mock_appsec_client, "update_eval_penalty_box",
               models.UpdatePenaltyBoxRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230",
                   penalty_box_protection=True, action="deny"),
               _err_500("Error creating zone"))


# ===================================================================
# TestEvalPenaltyBoxConditions  (mirrors eval_penalty_box_conditions_test.go)
# ===================================================================

class TestEvalPenaltyBoxConditions:
    """Eval penalty box conditions tests – mirrors eval_penalty_box_conditions_test.go."""

    def test_get_eval_penalty_box_conditions_200(self, mock_appsec_client):
        """Test GetEvalPenaltyBoxConditions on 200 OK."""
        _success(mock_appsec_client, "get_eval_penalty_box_conditions",
                 models.GetPenaltyBoxConditionsRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestEvalProtectHost/EvalProtectHost.json")

    def test_get_eval_penalty_box_conditions_500(self, mock_appsec_client):
        """Test GetEvalPenaltyBoxConditions raises Error on 500."""
        _error(mock_appsec_client, "get_eval_penalty_box_conditions",
               models.GetPenaltyBoxConditionsRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_update_eval_penalty_box_conditions_200(self, mock_appsec_client):
        """Test UpdateEvalPenaltyBoxConditions on 200 OK."""
        _success(mock_appsec_client, "update_eval_penalty_box_conditions",
                 models.UpdatePenaltyBoxConditionsRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230",
                     conditions_payload={"conditionOperator": "AND",
                                         "conditions": [{"type": "filenameMatch"}]}),
                 "TestEvalProtectHost/EvalProtectHost.json")

    def test_update_eval_penalty_box_conditions_500(self, mock_appsec_client):
        """Test UpdateEvalPenaltyBoxConditions raises Error on 500."""
        _error(mock_appsec_client, "update_eval_penalty_box_conditions",
               models.UpdatePenaltyBoxConditionsRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230",
                   conditions_payload={"conditionOperator": "AND",
                                       "conditions": [{"type": "filenameMatch"}]}),
               _err_500("Error creating zone"))


# ===================================================================
# TestAttackGroup  (mirrors attack_group_test.go)
# ===================================================================

class TestAttackGroup:
    """Attack group tests – mirrors attack_group_test.go."""

    def test_list_attack_groups_200(self, mock_appsec_client):
        """Test GetAttackGroups on 200 OK."""
        _success(mock_appsec_client, "get_attack_groups",
                 models.GetAttackGroupsRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestAttackGroup/AttackGroup.json")

    def test_list_attack_groups_500(self, mock_appsec_client):
        """Test GetAttackGroups raises Error on 500."""
        _error(mock_appsec_client, "get_attack_groups",
               models.GetAttackGroupsRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_get_attack_group_200(self, mock_appsec_client):
        """Test GetAttackGroup on 200 OK."""
        _success(mock_appsec_client, "get_attack_group",
                 models.GetAttackGroupRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230", group="SQL"),
                 "TestAttackGroup/AttackGroup.json")

    def test_get_attack_group_500(self, mock_appsec_client):
        """Test GetAttackGroup raises Error on 500."""
        _error(mock_appsec_client, "get_attack_group",
               models.GetAttackGroupRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230", group="SQL"),
               _err_500("Error fetching match target"))

    def test_update_attack_group_200(self, mock_appsec_client):
        """Test UpdateAttackGroup on 200 OK."""
        _success(mock_appsec_client, "update_attack_group",
                 models.UpdateAttackGroupRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230", group="SQL"),
                 "TestAttackGroup/AttackGroup.json")

    def test_update_attack_group_500(self, mock_appsec_client):
        """Test UpdateAttackGroup raises Error on 500."""
        _error(mock_appsec_client, "update_attack_group",
               models.UpdateAttackGroupRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230", group="SQL"),
               _err_500("Error creating zone"))


# ===================================================================
# TestReputationProfile  (mirrors reputation_profile_test.go)
# ===================================================================

class TestReputationProfile:
    """Reputation profile tests – mirrors reputation_profile_test.go."""

    def test_list_reputation_profiles_200(self, mock_appsec_client):
        """Test GetReputationProfiles on 200 OK."""
        _success(mock_appsec_client, "get_reputation_profiles",
                 models.GetReputationProfilesRequest(config_id=43253, config_version=15),
                 "TestReputationProfile/ReputationProfile.json")

    def test_list_reputation_profiles_500(self, mock_appsec_client):
        """Test GetReputationProfiles raises Error on 500."""
        _error(mock_appsec_client, "get_reputation_profiles",
               models.GetReputationProfilesRequest(config_id=43253, config_version=15),
               _err_500("Error fetching propertys"))

    def test_get_reputation_profile_200(self, mock_appsec_client):
        """Test GetReputationProfile on 200 OK."""
        _success(mock_appsec_client, "get_reputation_profile",
                 models.GetReputationProfileRequest(
                     config_id=43253, config_version=15, reputation_profile_id=134644),
                 "TestReputationProfile/ReputationProfile.json")

    def test_get_reputation_profile_500(self, mock_appsec_client):
        """Test GetReputationProfile raises Error on 500."""
        _error(mock_appsec_client, "get_reputation_profile",
               models.GetReputationProfileRequest(
                   config_id=43253, config_version=15, reputation_profile_id=134644),
               _err_500("Error fetching match target"))

    def test_create_reputation_profile_200(self, mock_appsec_client):
        """Test CreateReputationProfile on 200 OK."""
        _success(mock_appsec_client, "create_reputation_profile",
                 models.CreateReputationProfileRequest(config_id=43253, config_version=15),
                 "TestReputationProfile/ReputationProfile.json")

    def test_create_reputation_profile_500(self, mock_appsec_client):
        """Test CreateReputationProfile raises Error on 500."""
        _error(mock_appsec_client, "create_reputation_profile",
               models.CreateReputationProfileRequest(config_id=43253, config_version=15),
               _err_500("Error creating domain"))

    def test_update_reputation_profile_200(self, mock_appsec_client):
        """Test UpdateReputationProfile on 200 OK."""
        _success(mock_appsec_client, "update_reputation_profile",
                 models.UpdateReputationProfileRequest(
                     config_id=43253, config_version=15, reputation_profile_id=134644),
                 "TestReputationProfile/ReputationProfile.json")

    def test_update_reputation_profile_500(self, mock_appsec_client):
        """Test UpdateReputationProfile raises Error on 500."""
        _error(mock_appsec_client, "update_reputation_profile",
               models.UpdateReputationProfileRequest(
                   config_id=43253, config_version=15, reputation_profile_id=134644),
               _err_500("Error creating zone"))

    def test_remove_reputation_profile_200(self, mock_appsec_client):
        """Test RemoveReputationProfile on 200 OK."""
        _success(mock_appsec_client, "remove_reputation_profile",
                 models.RemoveReputationProfileRequest(
                     config_id=43253, config_version=15, reputation_profile_id=134644),
                 "TestReputationProfile/ReputationProfile.json")

    def test_remove_reputation_profile_500(self, mock_appsec_client):
        """Test RemoveReputationProfile raises Error on 500."""
        _error(mock_appsec_client, "remove_reputation_profile",
               models.RemoveReputationProfileRequest(
                   config_id=43253, config_version=15, reputation_profile_id=134644),
               _err_500("Error deleting match target"))


# ===================================================================
# TestReputationProfileAction  (mirrors reputation_profile_action_test.go)
# ===================================================================

class TestReputationProfileAction:
    """Reputation profile action tests – mirrors reputation_profile_action_test.go."""

    def test_list_reputation_profile_actions_200(self, mock_appsec_client):
        """Test GetReputationProfileActions on 200 OK."""
        _success(mock_appsec_client, "get_reputation_profile_actions",
                 models.GetReputationProfileActionsRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestReputationProfileAction/ReputationProfileAction.json")

    def test_list_reputation_profile_actions_500(self, mock_appsec_client):
        """Test GetReputationProfileActions raises Error on 500."""
        _error(mock_appsec_client, "get_reputation_profile_actions",
               models.GetReputationProfileActionsRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching propertys"))

    def test_get_reputation_profile_action_200(self, mock_appsec_client):
        """Test GetReputationProfileAction on 200 OK."""
        _success(mock_appsec_client, "get_reputation_profile_action",
                 models.GetReputationProfileActionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230",
                     reputation_profile_id=134644),
                 "TestReputationProfileAction/ReputationProfileAction.json")

    def test_get_reputation_profile_action_500(self, mock_appsec_client):
        """Test GetReputationProfileAction raises Error on 500."""
        _error(mock_appsec_client, "get_reputation_profile_action",
               models.GetReputationProfileActionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230",
                   reputation_profile_id=134644),
               _err_500("Error fetching match target"))

    def test_update_reputation_profile_action_200(self, mock_appsec_client):
        """Test UpdateReputationProfileAction on 200 OK."""
        _success(mock_appsec_client, "update_reputation_profile_action",
                 models.UpdateReputationProfileActionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230",
                     reputation_profile_id=134644),
                 "TestReputationProfileAction/ReputationProfileAction.json")

    def test_update_reputation_profile_action_500(self, mock_appsec_client):
        """Test UpdateReputationProfileAction raises Error on 500."""
        _error(mock_appsec_client, "update_reputation_profile_action",
               models.UpdateReputationProfileActionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230",
                   reputation_profile_id=134644),
               _err_500("Error creating zone"))


# ===================================================================
# TestReputationAnalysis  (mirrors reputation_analysis_test.go)
# ===================================================================

class TestReputationAnalysis:
    """Reputation analysis tests – mirrors reputation_analysis_test.go."""

    def test_list_reputation_analysis_200(self, mock_appsec_client):
        """Test GetReputationAnalysis (list) on 200 OK."""
        _success(mock_appsec_client, "get_reputation_analysis",
                 models.GetReputationAnalysisRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestReputationAnalysis/ReputationAnalysis.json")

    def test_list_reputation_analysis_500(self, mock_appsec_client):
        """Test GetReputationAnalysis raises Error on 500."""
        _error(mock_appsec_client, "get_reputation_analysis",
               models.GetReputationAnalysisRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching propertys"))

    def test_get_reputation_analysis_200(self, mock_appsec_client):
        """Test GetReputationAnalysis on 200 OK."""
        _success(mock_appsec_client, "get_reputation_analysis",
                 models.GetReputationAnalysisRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestReputationAnalysis/ReputationAnalysis.json")

    def test_get_reputation_analysis_500(self, mock_appsec_client):
        """Test GetReputationAnalysis raises Error on 500."""
        _error(mock_appsec_client, "get_reputation_analysis",
               models.GetReputationAnalysisRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_update_reputation_analysis_200(self, mock_appsec_client):
        """Test UpdateReputationAnalysis on 200 OK."""
        _success(mock_appsec_client, "update_reputation_analysis",
                 models.UpdateReputationAnalysisRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestReputationAnalysis/ReputationAnalysis.json")

    def test_update_reputation_analysis_500(self, mock_appsec_client):
        """Test UpdateReputationAnalysis raises Error on 500."""
        _error(mock_appsec_client, "update_reputation_analysis",
               models.UpdateReputationAnalysisRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error creating zone"))

    def test_remove_reputation_analysis_200(self, mock_appsec_client):
        """Test RemoveReputationAnalysis on 200 OK."""
        _success(mock_appsec_client, "remove_reputation_analysis",
                 models.UpdateReputationAnalysisRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestReputationAnalysis/ReputationAnalysis.json")

    def test_remove_reputation_analysis_500(self, mock_appsec_client):
        """Test RemoveReputationAnalysis raises Error on 500."""
        _error(mock_appsec_client, "remove_reputation_analysis",
               models.UpdateReputationAnalysisRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error deleting match target"))


# ===================================================================
# TestMatchTargets  (mirrors match_target_test.go)
# ===================================================================

class TestMatchTargets:
    """Match target tests – mirrors match_target_test.go."""

    def test_list_match_targets_200(self, mock_appsec_client):
        """Test GetMatchTargets on 200 OK."""
        _success(mock_appsec_client, "get_match_targets",
                 models.GetMatchTargetsRequest(config_id=43253, config_version=15),
                 "TestMatchTargets/MatchTargets.json")

    def test_list_match_targets_500(self, mock_appsec_client):
        """Test GetMatchTargets raises Error on 500."""
        _error(mock_appsec_client, "get_match_targets",
               models.GetMatchTargetsRequest(config_id=43253, config_version=15),
               _err_500("Error fetching propertys"))

    def test_get_match_target_200(self, mock_appsec_client):
        """Test GetMatchTarget on 200 OK."""
        _success(mock_appsec_client, "get_match_target",
                 models.GetMatchTargetRequest(
                     config_id=43253, config_version=15, target_id=3008967),
                 "TestMatchTargets/MatchTarget.json")

    def test_get_match_target_500(self, mock_appsec_client):
        """Test GetMatchTarget raises Error on 500."""
        _error(mock_appsec_client, "get_match_target",
               models.GetMatchTargetRequest(
                   config_id=43253, config_version=15, target_id=3008967),
               _err_500("Error fetching match target"))

    def test_create_match_target_201(self, mock_appsec_client):
        """Test CreateMatchTarget on 201 Created."""
        _success(mock_appsec_client, "create_match_target",
                 models.CreateMatchTargetRequest(config_id=43253, config_version=15),
                 "TestMatchTargets/MatchTarget.json")

    def test_create_match_target_500(self, mock_appsec_client):
        """Test CreateMatchTarget raises Error on 500."""
        _error(mock_appsec_client, "create_match_target",
               models.CreateMatchTargetRequest(config_id=43253, config_version=15),
               _err_500("Error creating domain"))

    def test_update_match_target_200(self, mock_appsec_client):
        """Test UpdateMatchTarget on 200 Success."""
        _success(mock_appsec_client, "update_match_target",
                 models.UpdateMatchTargetRequest(
                     config_id=43253, config_version=15, target_id=3008967),
                 "TestMatchTargets/MatchTarget.json")

    def test_update_match_target_500(self, mock_appsec_client):
        """Test UpdateMatchTarget raises Error on 500."""
        _error(mock_appsec_client, "update_match_target",
               models.UpdateMatchTargetRequest(
                   config_id=43253, config_version=15, target_id=3008967),
               _err_500("Error creating zone"))

    def test_remove_match_target_200(self, mock_appsec_client):
        """Test RemoveMatchTarget on 200 Success."""
        _success(mock_appsec_client, "remove_match_target",
                 models.RemoveMatchTargetRequest(
                     config_id=43253, config_version=15, target_id=3008967),
                 "TestMatchTargets/MatchTargets.json")

    def test_remove_match_target_500(self, mock_appsec_client):
        """Test RemoveMatchTarget raises Error on 500."""
        _error(mock_appsec_client, "remove_match_target",
               models.RemoveMatchTargetRequest(
                   config_id=43253, config_version=15, target_id=3008967),
               _err_500("Error deleting match target"))


# ===================================================================
# TestMatchTargetSequence  (mirrors match_target_sequence_test.go)
# ===================================================================

class TestMatchTargetSequence:
    """Match target sequence tests – mirrors match_target_sequence_test.go."""

    def test_list_match_target_sequence_200(self, mock_appsec_client):
        """Test GetMatchTargetSequence (list) on 200 OK."""
        _success(mock_appsec_client, "get_match_target_sequence",
                 models.GetMatchTargetSequenceRequest(
                     config_id=43253, config_version=15, type="website"),
                 "TestMatchTargetSequence/MatchTargetSequence.json")

    def test_list_match_target_sequence_500(self, mock_appsec_client):
        """Test GetMatchTargetSequence raises Error on 500."""
        _error(mock_appsec_client, "get_match_target_sequence",
               models.GetMatchTargetSequenceRequest(
                   config_id=43253, config_version=15, type="website"),
               _err_500("Error fetching propertys"))

    def test_update_match_target_sequence_200(self, mock_appsec_client):
        """Test UpdateMatchTargetSequence on 200 OK."""
        _success(mock_appsec_client, "update_match_target_sequence",
                 models.UpdateMatchTargetSequenceRequest(
                     config_id=43253, config_version=15),
                 "TestMatchTargetSequence/MatchTargetSequence.json")

    def test_update_match_target_sequence_500(self, mock_appsec_client):
        """Test UpdateMatchTargetSequence raises Error on 500."""
        _error(mock_appsec_client, "update_match_target_sequence",
               models.UpdateMatchTargetSequenceRequest(
                   config_id=43253, config_version=15),
               _err_500("Error creating zone"))


# ===================================================================
# TestRule  (mirrors rule_test.go)
# ===================================================================

class TestRule:
    """Rule tests – mirrors rule_test.go."""

    def test_list_rules_200(self, mock_appsec_client):
        """Test GetRules on 200 OK."""
        _success(mock_appsec_client, "get_rules",
                 models.GetRulesRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestRule/Rules.json")

    def test_list_rules_500(self, mock_appsec_client):
        """Test GetRules raises Error on 500."""
        _error(mock_appsec_client, "get_rules",
               models.GetRulesRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_get_rule_200(self, mock_appsec_client):
        """Test GetRule on 200 OK."""
        _success(mock_appsec_client, "get_rule",
                 models.GetRuleRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230", rule_id=12345),
                 "TestRule/Rule.json")

    def test_get_rule_500(self, mock_appsec_client):
        """Test GetRule raises Error on 500."""
        _error(mock_appsec_client, "get_rule",
               models.GetRuleRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230", rule_id=12345),
               _err_500("Error fetching match target"))

    def test_update_rule_200(self, mock_appsec_client):
        """Test UpdateRule on 200 OK."""
        _success(mock_appsec_client, "update_rule",
                 models.UpdateRuleRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230", rule_id=12345),
                 "TestRule/Rule.json")

    def test_update_rule_500(self, mock_appsec_client):
        """Test UpdateRule raises Error on 500."""
        _error(mock_appsec_client, "update_rule",
               models.UpdateRuleRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230", rule_id=12345),
               _err_500("Error creating zone"))


# ===================================================================
# TestRuleUpgrade  (mirrors rule_upgrade_test.go)
# ===================================================================

class TestRuleUpgrade:
    """Rule upgrade tests – mirrors rule_upgrade_test.go."""

    def test_list_rule_upgrades_200(self, mock_appsec_client):
        """Test GetRuleUpgrade (list) on 200 OK."""
        _success(mock_appsec_client, "get_rule_upgrade",
                 models.GetRuleUpgradeRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestRuleUpgrade/RuleUpgrade.json")

    def test_list_rule_upgrades_500(self, mock_appsec_client):
        """Test GetRuleUpgrade raises Error on 500."""
        _error(mock_appsec_client, "get_rule_upgrade",
               models.GetRuleUpgradeRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_get_rule_upgrade_200(self, mock_appsec_client):
        """Test GetRuleUpgrade on 200 OK."""
        _success(mock_appsec_client, "get_rule_upgrade",
                 models.GetRuleUpgradeRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestRuleUpgrade/RuleUpgrade.json")

    def test_get_rule_upgrade_500(self, mock_appsec_client):
        """Test GetRuleUpgrade raises Error on 500."""
        _error(mock_appsec_client, "get_rule_upgrade",
               models.GetRuleUpgradeRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_update_rule_upgrade_200(self, mock_appsec_client):
        """Test UpdateRuleUpgrade on 200 OK."""
        _success(mock_appsec_client, "update_rule_upgrade",
                 models.UpdateRuleUpgradeRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestRuleUpgrade/RuleUpgrade.json")

    def test_update_rule_upgrade_500(self, mock_appsec_client):
        """Test UpdateRuleUpgrade raises Error on 500."""
        _error(mock_appsec_client, "update_rule_upgrade",
               models.UpdateRuleUpgradeRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error creating zone"))


# ===================================================================
# TestPenaltyBox  (mirrors penalty_box_test.go)
# ===================================================================

class TestPenaltyBox:
    """Penalty box tests – mirrors penalty_box_test.go."""

    def test_get_penalty_box_200(self, mock_appsec_client):
        """Test GetPenaltyBox on 200 OK."""
        _success(mock_appsec_client, "get_penalty_box",
                 models.GetPenaltyBoxRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestPenaltyBox/PenaltyBoxes.json")

    def test_get_penalty_box_500(self, mock_appsec_client):
        """Test GetPenaltyBox raises Error on 500."""
        _error(mock_appsec_client, "get_penalty_box",
               models.GetPenaltyBoxRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_update_penalty_box_200(self, mock_appsec_client):
        """Test UpdatePenaltyBox on 200 OK."""
        _success(mock_appsec_client, "update_penalty_box",
                 models.UpdatePenaltyBoxRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230",
                     penalty_box_protection=True, action="deny"),
                 "TestPenaltyBox/PenaltyBoxes.json")

    def test_update_penalty_box_500(self, mock_appsec_client):
        """Test UpdatePenaltyBox raises Error on 500."""
        _error(mock_appsec_client, "update_penalty_box",
               models.UpdatePenaltyBoxRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230",
                   penalty_box_protection=True, action="deny"),
               _err_500("Error creating zone"))


# ===================================================================
# TestPenaltyBoxConditions  (mirrors penalty_box_conditions_test.go)
# ===================================================================

class TestPenaltyBoxConditions:
    """Penalty box conditions tests – mirrors penalty_box_conditions_test.go."""

    def test_list_penalty_box_conditions_200(self, mock_appsec_client):
        """Test GetPenaltyBoxConditions (list) on 200 OK."""
        _success(mock_appsec_client, "get_penalty_box_conditions",
                 models.GetPenaltyBoxConditionsRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestPenaltyBoxConditions/PenaltyBoxConditions.json")

    def test_list_penalty_box_conditions_500(self, mock_appsec_client):
        """Test GetPenaltyBoxConditions raises Error on 500."""
        _error(mock_appsec_client, "get_penalty_box_conditions",
               models.GetPenaltyBoxConditionsRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_update_penalty_box_conditions_200(self, mock_appsec_client):
        """Test UpdatePenaltyBoxConditions on 200 OK."""
        _success(mock_appsec_client, "update_penalty_box_conditions",
                 models.UpdatePenaltyBoxConditionsRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230",
                     conditions_payload={"conditionOperator": "AND",
                                         "conditions": [{"type": "filenameMatch"}]}),
                 "TestPenaltyBoxConditions/PenaltyBoxConditions.json")

    def test_update_penalty_box_conditions_500(self, mock_appsec_client):
        """Test UpdatePenaltyBoxConditions raises Error on 500."""
        _error(mock_appsec_client, "update_penalty_box_conditions",
               models.UpdatePenaltyBoxConditionsRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230",
                   conditions_payload={"conditionOperator": "AND",
                                       "conditions": [{"type": "filenameMatch"}]}),
               _err_500("Error creating zone"))


# ===================================================================
# TestRapidRule  (mirrors rapid_rule_test.go)
# ===================================================================

# Rapid-rule tests use specific error bodies from Go rapid_rule_test.go
_RAPID_BAD_REQUEST_BODY = (
    '{"type":"https://problems.luna.akamaiapis.net/appsec/error-types/'
    'INVALID-INPUT-ERROR","title":"Invalid Input Error",'
    '"detail":"configId incorrect type","status":400}'
)
_RAPID_INTERNAL_ERROR_BODY = (
    '{"type":"https://problems.luna.akamaiapis.net/appsec/error-types/'
    'INVALID-INPUT-ERROR","title":"Internal Server Error",'
    '"detail":"The server was unable to complete your request. '
    'Please try again later.","status":400}'
)


def _rapid_err_400():
    """Build a 400 Error matching Go badRequest for rapid-rule tests."""
    return Error(
        type=(
            "https://problems.luna.akamaiapis.net/appsec/"
            "error-types/INVALID-INPUT-ERROR"
        ),
        title="Invalid Input Error",
        detail="configId incorrect type",
        status_code=400,
    )


def _rapid_err_500():
    """Build a 500 Error matching Go internalServerError for rapid-rule tests."""
    return Error(
        type=(
            "https://problems.luna.akamaiapis.net/appsec/"
            "error-types/INVALID-INPUT-ERROR"
        ),
        title="Internal Server Error",
        detail="The server was unable to complete your request. Please try again later.",
        status_code=500,
    )


class TestRapidRule:
    """Rapid rule tests – mirrors rapid_rule_test.go."""

    def test_list_rapid_rules_200(self, mock_appsec_client):
        """Test GetRapidRules (list) on 200 OK."""
        _success(mock_appsec_client, "get_rapid_rules",
                 models.GetRapidRulesRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestRapidRule/RapidRules.json")

    def test_list_rapid_rules_400(self, mock_appsec_client):
        """Test GetRapidRules raises Error on 400 bad request."""
        _error(mock_appsec_client, "get_rapid_rules",
               models.GetRapidRulesRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _rapid_err_400())

    def test_list_rapid_rules_500(self, mock_appsec_client):
        """Test GetRapidRules raises Error on 500."""
        _error(mock_appsec_client, "get_rapid_rules",
               models.GetRapidRulesRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _rapid_err_500())

    def test_get_rapid_rules_200(self, mock_appsec_client):
        """Test GetRapidRules (get) on 200 OK."""
        _success(mock_appsec_client, "get_rapid_rules",
                 models.GetRapidRulesRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestRapidRule/RapidRules.json")

    def test_update_rapid_rules_200(self, mock_appsec_client):
        """Test UpdateRapidRules on 200 OK."""
        _success(mock_appsec_client, "update_rapid_rules_default_action",
                 models.UpdateRapidRulesDefaultActionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230",
                     body={"action": "alert"}),
                 "TestRapidRule/RapidRules.json")

    def test_update_rapid_rules_500(self, mock_appsec_client):
        """Test UpdateRapidRules raises Error on 500."""
        _error(mock_appsec_client, "update_rapid_rules_default_action",
               models.UpdateRapidRulesDefaultActionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230",
                   body={"action": "alert"}),
               _rapid_err_500())


# ===================================================================
# TestWAFMode  (mirrors waf_mode_test.go)
# ===================================================================

class TestWAFMode:
    """WAF mode tests – mirrors waf_mode_test.go."""

    def test_list_waf_mode_200(self, mock_appsec_client):
        """Test GetWAFMode (list) on 200 OK."""
        _success(mock_appsec_client, "get_waf_mode",
                 models.GetWAFModeRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestWAFMode/WAFMode.json")

    def test_list_waf_mode_500(self, mock_appsec_client):
        """Test GetWAFMode raises Error on 500."""
        _error(mock_appsec_client, "get_waf_mode",
               models.GetWAFModeRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching propertys"))

    def test_get_waf_mode_200(self, mock_appsec_client):
        """Test GetWAFMode on 200 OK."""
        _success(mock_appsec_client, "get_waf_mode",
                 models.GetWAFModeRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestWAFMode/WAFMode.json")

    def test_get_waf_mode_500(self, mock_appsec_client):
        """Test GetWAFMode raises Error on 500."""
        _error(mock_appsec_client, "get_waf_mode",
               models.GetWAFModeRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_update_waf_mode_200(self, mock_appsec_client):
        """Test UpdateWAFMode on 200 OK."""
        _success(mock_appsec_client, "update_waf_mode",
                 models.UpdateWAFModeRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestWAFMode/WAFMode.json")

    def test_update_waf_mode_500(self, mock_appsec_client):
        """Test UpdateWAFMode raises Error on 500."""
        _error(mock_appsec_client, "update_waf_mode",
               models.UpdateWAFModeRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error creating zone"))


# ===================================================================
# TestWAFProtection  (mirrors waf_protection_test.go)
# ===================================================================

class TestWAFProtection:
    """WAF protection tests – mirrors waf_protection_test.go."""

    def test_list_waf_protection_200(self, mock_appsec_client):
        """Test GetWAFProtection (list) on 200 OK."""
        _success(mock_appsec_client, "get_waf_protections",
                 models.GetWAFProtectionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestWAFProtections/WAFProtections.json")

    def test_list_waf_protection_500(self, mock_appsec_client):
        """Test GetWAFProtection raises Error on 500."""
        _error(mock_appsec_client, "get_waf_protections",
               models.GetWAFProtectionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching propertys"))

    def test_get_waf_protection_200(self, mock_appsec_client):
        """Test GetWAFProtection on 200 OK."""
        _success(mock_appsec_client, "get_waf_protection",
                 models.GetWAFProtectionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestWAFProtections/WAFProtections.json")

    def test_get_waf_protection_500(self, mock_appsec_client):
        """Test GetWAFProtection raises Error on 500."""
        _error(mock_appsec_client, "get_waf_protection",
               models.GetWAFProtectionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_update_waf_protection_200(self, mock_appsec_client):
        """Test UpdateWAFProtection on 200 OK."""
        _success(mock_appsec_client, "update_waf_protection",
                 models.UpdateWAFProtectionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestWAFProtections/WAFProtections.json")

    def test_update_waf_protection_500(self, mock_appsec_client):
        """Test UpdateWAFProtection raises Error on 500."""
        _error(mock_appsec_client, "update_waf_protection",
               models.UpdateWAFProtectionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error creating zone"))


# ===================================================================
# TestIPGeo  (mirrors ip_geo_test.go)
# ===================================================================

class TestIPGeo:
    """IP/Geo tests – mirrors ip_geo_test.go."""

    def test_list_ip_geo_200(self, mock_appsec_client):
        """Test GetIPGeo (list) on 200 OK."""
        _success(mock_appsec_client, "get_ip_geo",
                 models.GetIPGeoRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestIPGeoProtections/IPGeoProtections.json")

    def test_list_ip_geo_500(self, mock_appsec_client):
        """Test GetIPGeo raises Error on 500."""
        _error(mock_appsec_client, "get_ip_geo",
               models.GetIPGeoRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching propertys"))

    def test_get_ip_geo_200(self, mock_appsec_client):
        """Test GetIPGeo on 200 OK."""
        _success(mock_appsec_client, "get_ip_geo",
                 models.GetIPGeoRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestIPGeoProtections/IPGeoProtections.json")

    def test_get_ip_geo_500(self, mock_appsec_client):
        """Test GetIPGeo raises Error on 500."""
        _error(mock_appsec_client, "get_ip_geo",
               models.GetIPGeoRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_update_ip_geo_200(self, mock_appsec_client):
        """Test UpdateIPGeo on 200 OK."""
        _success(mock_appsec_client, "update_ip_geo",
                 models.UpdateIPGeoRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestIPGeoProtections/IPGeoProtections.json")

    def test_update_ip_geo_500(self, mock_appsec_client):
        """Test UpdateIPGeo raises Error on 500."""
        _error(mock_appsec_client, "update_ip_geo",
               models.UpdateIPGeoRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error creating zone"))


# ===================================================================
# TestIPGeoProtection  (mirrors ip_geo_protection_test.go)
# ===================================================================

class TestIPGeoProtection:
    """IP/Geo protection tests – mirrors ip_geo_protection_test.go."""

    def test_list_ip_geo_protection_200(self, mock_appsec_client):
        """Test GetIPGeoProtection (list) on 200 OK."""
        _success(mock_appsec_client, "get_ip_geo_protections",
                 models.GetIPGeoProtectionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestIPGeoProtections/IPGeoProtections.json")

    def test_list_ip_geo_protection_500(self, mock_appsec_client):
        """Test GetIPGeoProtection raises Error on 500."""
        _error(mock_appsec_client, "get_ip_geo_protections",
               models.GetIPGeoProtectionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching propertys"))

    def test_get_ip_geo_protection_200(self, mock_appsec_client):
        """Test GetIPGeoProtection on 200 OK."""
        _success(mock_appsec_client, "get_ip_geo_protection",
                 models.GetIPGeoProtectionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestIPGeoProtections/IPGeoProtections.json")

    def test_get_ip_geo_protection_500(self, mock_appsec_client):
        """Test GetIPGeoProtection raises Error on 500."""
        _error(mock_appsec_client, "get_ip_geo_protection",
               models.GetIPGeoProtectionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_update_ip_geo_protection_200(self, mock_appsec_client):
        """Test UpdateIPGeoProtection on 200 OK."""
        _success(mock_appsec_client, "update_ip_geo_protection",
                 models.UpdateIPGeoProtectionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestIPGeoProtections/IPGeoProtections.json")

    def test_update_ip_geo_protection_500(self, mock_appsec_client):
        """Test UpdateIPGeoProtection raises Error on 500."""
        _error(mock_appsec_client, "update_ip_geo_protection",
               models.UpdateIPGeoProtectionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error creating zone"))


# ===================================================================
# TestRateProtection  (mirrors rate_protection_test.go)
# ===================================================================

class TestRateProtection:
    """Rate protection tests – mirrors rate_protection_test.go."""

    def test_list_rate_protection_200(self, mock_appsec_client):
        """Test GetRateProtection (list) on 200 OK."""
        _success(mock_appsec_client, "get_rate_protections",
                 models.GetRateProtectionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestRateProtections/RateProtections.json")

    def test_list_rate_protection_500(self, mock_appsec_client):
        """Test GetRateProtection raises Error on 500."""
        _error(mock_appsec_client, "get_rate_protections",
               models.GetRateProtectionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching propertys"))

    def test_get_rate_protection_200(self, mock_appsec_client):
        """Test GetRateProtection on 200 OK."""
        _success(mock_appsec_client, "get_rate_protection",
                 models.GetRateProtectionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestRateProtections/RateProtections.json")

    def test_get_rate_protection_500(self, mock_appsec_client):
        """Test GetRateProtection raises Error on 500."""
        _error(mock_appsec_client, "get_rate_protection",
               models.GetRateProtectionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_update_rate_protection_200(self, mock_appsec_client):
        """Test UpdateRateProtection on 200 OK."""
        _success(mock_appsec_client, "update_rate_protection",
                 models.UpdateRateProtectionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestRateProtections/RateProtections.json")

    def test_update_rate_protection_500(self, mock_appsec_client):
        """Test UpdateRateProtection raises Error on 500."""
        _error(mock_appsec_client, "update_rate_protection",
               models.UpdateRateProtectionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error creating zone"))


# ===================================================================
# TestReputationProtection  (mirrors reputation_protection_test.go)
# ===================================================================

class TestReputationProtection:
    """Reputation protection tests – mirrors reputation_protection_test.go."""

    def test_list_reputation_protection_200(self, mock_appsec_client):
        """Test GetReputationProtection (list) on 200 OK."""
        _success(mock_appsec_client, "get_reputation_protections",
                 models.GetReputationProtectionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestReputationProtections/ReputationProtections.json")

    def test_list_reputation_protection_500(self, mock_appsec_client):
        """Test GetReputationProtection raises Error on 500."""
        _error(mock_appsec_client, "get_reputation_protections",
               models.GetReputationProtectionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching propertys"))

    def test_get_reputation_protection_200(self, mock_appsec_client):
        """Test GetReputationProtection on 200 OK."""
        _success(mock_appsec_client, "get_reputation_protection",
                 models.GetReputationProtectionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestReputationProtections/ReputationProtections.json")

    def test_get_reputation_protection_500(self, mock_appsec_client):
        """Test GetReputationProtection raises Error on 500."""
        _error(mock_appsec_client, "get_reputation_protection",
               models.GetReputationProtectionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_update_reputation_protection_200(self, mock_appsec_client):
        """Test UpdateReputationProtection on 200 OK."""
        _success(mock_appsec_client, "update_reputation_protection",
                 models.UpdateReputationProtectionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestReputationProtections/ReputationProtections.json")

    def test_update_reputation_protection_500(self, mock_appsec_client):
        """Test UpdateReputationProtection raises Error on 500."""
        _error(mock_appsec_client, "update_reputation_protection",
               models.UpdateReputationProtectionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error creating zone"))


# ===================================================================
# TestSlowPostProtection  (mirrors slowpost_protection_test.go)
# ===================================================================

class TestSlowPostProtection:
    """Slow post protection tests – mirrors slowpost_protection_test.go."""

    def test_list_slowpost_protection_200(self, mock_appsec_client):
        """Test GetSlowPostProtection (list) on 200 OK."""
        _success(mock_appsec_client, "get_slow_post_protections",
                 models.GetSlowPostProtectionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestSlowPostProtection/SlowPostProtection.json")

    def test_list_slowpost_protection_500(self, mock_appsec_client):
        """Test GetSlowPostProtection raises Error on 500."""
        _error(mock_appsec_client, "get_slow_post_protections",
               models.GetSlowPostProtectionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching propertys"))

    def test_get_slowpost_protection_200(self, mock_appsec_client):
        """Test GetSlowPostProtection on 200 OK."""
        _success(mock_appsec_client, "get_slow_post_protection",
                 models.GetSlowPostProtectionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestSlowPostProtection/SlowPostProtection.json")

    def test_get_slowpost_protection_500(self, mock_appsec_client):
        """Test GetSlowPostProtection raises Error on 500."""
        _error(mock_appsec_client, "get_slow_post_protection",
               models.GetSlowPostProtectionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_update_slowpost_protection_200(self, mock_appsec_client):
        """Test UpdateSlowPostProtection on 200 OK."""
        _success(mock_appsec_client, "update_slow_post_protection",
                 models.UpdateSlowPostProtectionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestSlowPostProtection/SlowPostProtection.json")

    def test_update_slowpost_protection_500(self, mock_appsec_client):
        """Test UpdateSlowPostProtection raises Error on 500."""
        _error(mock_appsec_client, "update_slow_post_protection",
               models.UpdateSlowPostProtectionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error creating zone"))


# ===================================================================
# TestSlowPostProtectionSetting  (mirrors slow_post_protection_setting_test.go)
# ===================================================================

class TestSlowPostProtectionSetting:
    """Slow post protection setting tests – mirrors slow_post_protection_setting_test.go."""

    def test_list_slow_post_settings_200(self, mock_appsec_client):
        """Test GetSlowPostProtectionSettings (list) on 200 OK."""
        _success(mock_appsec_client, "get_slow_post_protection_settings",
                 models.GetSlowPostProtectionSettingsRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestSlowPostProtectionSettings/SlowPostProtectionSettings.json")

    def test_list_slow_post_settings_500(self, mock_appsec_client):
        """Test GetSlowPostProtectionSettings raises Error on 500."""
        _error(mock_appsec_client, "get_slow_post_protection_settings",
               models.GetSlowPostProtectionSettingsRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching propertys"))

    def test_update_slow_post_setting_200(self, mock_appsec_client):
        """Test UpdateSlowPostProtectionSetting on 200 OK."""
        _success(mock_appsec_client, "update_slow_post_protection_setting",
                 models.UpdateSlowPostProtectionSettingRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestSlowPostProtectionSettings/SlowPostProtectionSettings.json")

    def test_update_slow_post_setting_500(self, mock_appsec_client):
        """Test UpdateSlowPostProtectionSetting raises Error on 500."""
        _error(mock_appsec_client, "update_slow_post_protection_setting",
               models.UpdateSlowPostProtectionSettingRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error creating zone"))


# ===================================================================
# TestMalwarePolicy  (mirrors malware_policy_test.go)
# ===================================================================

class TestMalwarePolicy:
    """Malware policy tests – mirrors malware_policy_test.go."""

    def test_get_malware_policy_200(self, mock_appsec_client):
        """Test GetMalwarePolicy on 200 OK."""
        _success(mock_appsec_client, "get_malware_policy",
                 models.GetMalwarePolicyRequest(
                     config_id=43253, config_version=15,
                     malware_policy_id=134644),
                 "TestMalwarePolicy/MalwarePolicy.json")

    def test_get_malware_policy_500(self, mock_appsec_client):
        """Test GetMalwarePolicy raises Error on 500."""
        _error(mock_appsec_client, "get_malware_policy",
               models.GetMalwarePolicyRequest(
                   config_id=43253, config_version=15,
                   malware_policy_id=134644),
               _err_500("Error fetching match target"))

    def test_create_malware_policy_200(self, mock_appsec_client):
        """Test CreateMalwarePolicy on 200 OK."""
        _success(mock_appsec_client, "create_malware_policy",
                 models.CreateMalwarePolicyRequest(
                     config_id=43253, config_version=15,
                     policy={"name": "test_malware_policy"}),
                 "TestMalwarePolicy/MalwarePolicy.json")

    def test_create_malware_policy_500(self, mock_appsec_client):
        """Test CreateMalwarePolicy raises Error on 500."""
        _error(mock_appsec_client, "create_malware_policy",
               models.CreateMalwarePolicyRequest(
                   config_id=43253, config_version=15,
                   policy={"name": "test_malware_policy"}),
               _err_500("Error creating domain"))

    def test_update_malware_policy_200(self, mock_appsec_client):
        """Test UpdateMalwarePolicy on 200 OK."""
        _success(mock_appsec_client, "update_malware_policy",
                 models.UpdateMalwarePolicyRequest(
                     config_id=43253, config_version=15,
                     malware_policy_id=134644,
                     policy={"name": "test_malware_policy"}),
                 "TestMalwarePolicy/MalwarePolicy.json")

    def test_update_malware_policy_500(self, mock_appsec_client):
        """Test UpdateMalwarePolicy raises Error on 500."""
        _error(mock_appsec_client, "update_malware_policy",
               models.UpdateMalwarePolicyRequest(
                   config_id=43253, config_version=15,
                   malware_policy_id=134644,
                   policy={"name": "test_malware_policy"}),
               _err_500("Error creating zone"))

    def test_remove_malware_policy_200(self, mock_appsec_client):
        """Test RemoveMalwarePolicy on 200 OK."""
        _success(mock_appsec_client, "remove_malware_policy",
                 models.RemoveMalwarePolicyRequest(
                     config_id=43253, config_version=15,
                     malware_policy_id=134644),
                 "TestMalwarePolicy/MalwarePolicy.json")

    def test_remove_malware_policy_500(self, mock_appsec_client):
        """Test RemoveMalwarePolicy raises Error on 500."""
        _error(mock_appsec_client, "remove_malware_policy",
               models.RemoveMalwarePolicyRequest(
                   config_id=43253, config_version=15,
                   malware_policy_id=134644),
               _err_500("Error deleting match target"))


# ===================================================================
# TestMalwarePolicyAction  (mirrors malware_policy_action_test.go)
# ===================================================================

class TestMalwarePolicyAction:
    """Malware policy action tests – mirrors malware_policy_action_test.go."""

    def test_list_malware_policy_actions_200(self, mock_appsec_client):
        """Test GetMalwarePolicyActions on 200 OK."""
        _success(mock_appsec_client, "get_malware_policy_actions",
                 models.GetMalwarePolicyActionsRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestMalwarePolicyAction/MalwarePolicyAction.json")

    def test_list_malware_policy_actions_500(self, mock_appsec_client):
        """Test GetMalwarePolicyActions raises Error on 500."""
        _error(mock_appsec_client, "get_malware_policy_actions",
               models.GetMalwarePolicyActionsRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching propertys"))

    def test_update_malware_policy_action_200(self, mock_appsec_client):
        """Test UpdateMalwarePolicyAction on 200 OK."""
        _success(mock_appsec_client, "update_malware_policy_action",
                 models.UpdateMalwarePolicyActionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230",
                     malware_policy_id=134644, action="none",
                     unscanned_action="none"),
                 "TestMalwarePolicyAction/MalwarePolicyAction.json")

    def test_update_malware_policy_action_500(self, mock_appsec_client):
        """Test UpdateMalwarePolicyAction raises Error on 500."""
        _error(mock_appsec_client, "update_malware_policy_action",
               models.UpdateMalwarePolicyActionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230",
                   malware_policy_id=134644, action="alert",
                   unscanned_action="deny"),
               _err_500("Error creating zone"))


# ===================================================================
# TestMalwareContentTypes  (mirrors malware_content_types_test.go)
# ===================================================================

class TestMalwareContentTypes:
    """Malware content types tests – mirrors malware_content_types_test.go."""

    def test_get_malware_content_types_200(self, mock_appsec_client):
        """Test GetMalwareContentTypes on 200 OK."""
        _success(mock_appsec_client, "get_malware_content_types",
                 models.GetMalwareContentTypesRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestMalwareContentTypes/MalwareContentTypes.json")

    def test_get_malware_content_types_500(self, mock_appsec_client):
        """Test GetMalwareContentTypes raises Error on 500."""
        _error(mock_appsec_client, "get_malware_content_types",
               models.GetMalwareContentTypesRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))


# ===================================================================
# TestMalwareProtection  (mirrors malware_protection_test.go)
# ===================================================================

class TestMalwareProtection:
    """Malware protection tests – mirrors malware_protection_test.go."""

    def test_get_malware_protection_200(self, mock_appsec_client):
        """Test GetMalwareProtection on 200 OK."""
        _success(mock_appsec_client, "get_malware_protection",
                 models.GetMalwareProtectionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestMalwareProtection/MalwareProtection.json")

    def test_get_malware_protection_500(self, mock_appsec_client):
        """Test GetMalwareProtection raises Error on 500."""
        _error(mock_appsec_client, "get_malware_protection",
               models.GetMalwareProtectionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_update_malware_protection_200(self, mock_appsec_client):
        """Test UpdateMalwareProtection on 200 OK."""
        _success(mock_appsec_client, "update_malware_protection",
                 models.UpdateMalwareProtectionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestMalwareProtection/MalwareProtection.json")

    def test_update_malware_protection_500(self, mock_appsec_client):
        """Test UpdateMalwareProtection raises Error on 500."""
        _error(mock_appsec_client, "update_malware_protection",
               models.UpdateMalwareProtectionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error creating zone"))


# ===================================================================
# TestApiEndpoints  (mirrors api_endpoints_test.go)
# ===================================================================

class TestApiEndpoints:
    """API endpoints tests – mirrors api_endpoints_test.go."""

    def test_list_api_endpoints_200(self, mock_appsec_client):
        """Test GetApiEndpoints (list) on 200 OK."""
        _success(mock_appsec_client, "get_api_endpoints",
                 models.GetApiEndpointsRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestApiEndpoints/ApiEndpoints.json")

    def test_list_api_endpoints_500(self, mock_appsec_client):
        """Test GetApiEndpoints raises Error on 500."""
        _error(mock_appsec_client, "get_api_endpoints",
               models.GetApiEndpointsRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching propertys"))

    def test_get_api_endpoints_200(self, mock_appsec_client):
        """Test GetApiEndpoints on 200 OK."""
        _success(mock_appsec_client, "get_api_endpoints",
                 models.GetApiEndpointsRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestApiEndpoints/ApiEndpoints.json")

    def test_get_api_endpoints_500(self, mock_appsec_client):
        """Test GetApiEndpoints raises Error on 500."""
        _error(mock_appsec_client, "get_api_endpoints",
               models.GetApiEndpointsRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))


# ===================================================================
# TestApiHostnameCoverage  (mirrors api_hostname_coverage_test.go)
# ===================================================================

class TestApiHostnameCoverage:
    """API hostname coverage tests – mirrors api_hostname_coverage_test.go."""

    def test_list_api_hostname_coverage_200(self, mock_appsec_client):
        """Test GetApiHostnameCoverage (list) on 200 OK."""
        _success(mock_appsec_client, "get_api_hostname_coverage",
                 models.GetApiHostnameCoverageRequest(
                     config_id=43253, version=15),
                 "TestApiHostnameCoverage/ApiHostnameCoverage.json")

    def test_list_api_hostname_coverage_500(self, mock_appsec_client):
        """Test GetApiHostnameCoverage raises Error on 500."""
        _error(mock_appsec_client, "get_api_hostname_coverage",
               models.GetApiHostnameCoverageRequest(
                   config_id=43253, version=15),
               _err_500("Error fetching propertys"))

    def test_get_api_hostname_coverage_200(self, mock_appsec_client):
        """Test GetApiHostnameCoverage on 200 OK."""
        _success(mock_appsec_client, "get_api_hostname_coverage",
                 models.GetApiHostnameCoverageRequest(
                     config_id=43253, version=15),
                 "TestApiHostnameCoverage/ApiHostnameCoverage.json")

    def test_get_api_hostname_coverage_500(self, mock_appsec_client):
        """Test GetApiHostnameCoverage raises Error on 500."""
        _error(mock_appsec_client, "get_api_hostname_coverage",
               models.GetApiHostnameCoverageRequest(
                   config_id=43253, version=15),
               _err_500("Error fetching match target"))


# ===================================================================
# TestApiHostnameCoverageMatchTargets
# (mirrors api_hostname_coverage_match_targets_test.go)
# ===================================================================

class TestApiHostnameCoverageMatchTargets:
    """API hostname coverage match targets tests."""

    def test_list_api_hostname_coverage_match_targets_200(self, mock_appsec_client):
        """Test GetApiHostnameCoverageMatchTargets (list) on 200 OK."""
        _success(mock_appsec_client, "get_api_hostname_coverage_match_targets",
                 models.GetApiHostnameCoverageMatchTargetsRequest(
                     config_id=43253, version=15),
                 "TestApiHostnameCoverageMatchTargets/ApiHostnameCoverageMatchTargets.json")

    def test_list_api_hostname_coverage_match_targets_500(self, mock_appsec_client):
        """Test GetApiHostnameCoverageMatchTargets raises Error on 500."""
        _error(mock_appsec_client, "get_api_hostname_coverage_match_targets",
               models.GetApiHostnameCoverageMatchTargetsRequest(
                   config_id=43253, version=15),
               _err_500("Error fetching propertys"))

    def test_get_api_hostname_coverage_match_targets_200(self, mock_appsec_client):
        """Test GetApiHostnameCoverageMatchTargets on 200 OK."""
        _success(mock_appsec_client, "get_api_hostname_coverage_match_targets",
                 models.GetApiHostnameCoverageMatchTargetsRequest(
                     config_id=43253, version=15),
                 "TestApiHostnameCoverageMatchTargets/ApiHostnameCoverageMatchTargets.json")

    def test_get_api_hostname_coverage_match_targets_500(self, mock_appsec_client):
        """Test GetApiHostnameCoverageMatchTargets raises Error on 500."""
        _error(mock_appsec_client, "get_api_hostname_coverage_match_targets",
               models.GetApiHostnameCoverageMatchTargetsRequest(
                   config_id=43253, version=15),
               _err_500("Error fetching match target"))


# ===================================================================
# TestApiHostnameCoverageOverlapping
# (mirrors api_hostname_coverage_overlapping_test.go)
# ===================================================================

class TestApiHostnameCoverageOverlapping:
    """API hostname coverage overlapping tests."""

    def test_list_api_hostname_coverage_overlapping_200(self, mock_appsec_client):
        """Test GetApiHostnameCoverageOverlapping (list) on 200 OK."""
        _success(mock_appsec_client, "get_api_hostname_coverage_overlapping",
                 models.GetApiHostnameCoverageOverlappingRequest(
                     config_id=43253, version=15),
                 "TestApiHostnameCoverageOverlapping/ApiHostnameCoverageOverlapping.json")

    def test_list_api_hostname_coverage_overlapping_500(self, mock_appsec_client):
        """Test GetApiHostnameCoverageOverlapping raises Error on 500."""
        _error(mock_appsec_client, "get_api_hostname_coverage_overlapping",
               models.GetApiHostnameCoverageOverlappingRequest(
                   config_id=43253, version=15),
               _err_500("Error fetching propertys"))

    def test_get_api_hostname_coverage_overlapping_200(self, mock_appsec_client):
        """Test GetApiHostnameCoverageOverlapping on 200 OK."""
        _success(mock_appsec_client, "get_api_hostname_coverage_overlapping",
                 models.GetApiHostnameCoverageOverlappingRequest(
                     config_id=43253, version=15),
                 "TestApiHostnameCoverageOverlapping/ApiHostnameCoverageOverlapping.json")

    def test_get_api_hostname_coverage_overlapping_500(self, mock_appsec_client):
        """Test GetApiHostnameCoverageOverlapping raises Error on 500."""
        _error(mock_appsec_client, "get_api_hostname_coverage_overlapping",
               models.GetApiHostnameCoverageOverlappingRequest(
                   config_id=43253, version=15),
               _err_500("Error fetching match target"))


# ===================================================================
# TestApiRequestConstraints  (mirrors api_request_constraints_test.go)
# ===================================================================

class TestApiRequestConstraints:
    """API request constraints tests – mirrors api_request_constraints_test.go."""

    def test_list_api_request_constraints_200(self, mock_appsec_client):
        """Test GetApiRequestConstraints (list) on 200 OK."""
        _success(mock_appsec_client, "get_api_request_constraints",
                 models.GetApiRequestConstraintsRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestApiRequestConstraints/ApiRequestConstraints.json")

    def test_list_api_request_constraints_500(self, mock_appsec_client):
        """Test GetApiRequestConstraints raises Error on 500."""
        _error(mock_appsec_client, "get_api_request_constraints",
               models.GetApiRequestConstraintsRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching propertys"))

    def test_get_api_request_constraints_200(self, mock_appsec_client):
        """Test GetApiRequestConstraints on 200 OK."""
        _success(mock_appsec_client, "get_api_request_constraints",
                 models.GetApiRequestConstraintsRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestApiRequestConstraints/ApiRequestConstraints.json")

    def test_get_api_request_constraints_500(self, mock_appsec_client):
        """Test GetApiRequestConstraints raises Error on 500."""
        _error(mock_appsec_client, "get_api_request_constraints",
               models.GetApiRequestConstraintsRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_update_api_request_constraints_200(self, mock_appsec_client):
        """Test UpdateApiRequestConstraints on 200 OK."""
        _success(mock_appsec_client, "update_api_request_constraints",
                 models.UpdateApiRequestConstraintsRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestApiRequestConstraints/ApiRequestConstraints.json")

    def test_update_api_request_constraints_500(self, mock_appsec_client):
        """Test UpdateApiRequestConstraints raises Error on 500."""
        _error(mock_appsec_client, "update_api_request_constraints",
               models.UpdateApiRequestConstraintsRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error creating zone"))

    def test_remove_api_request_constraints_200(self, mock_appsec_client):
        """Test RemoveApiRequestConstraints on 200 OK."""
        _success(mock_appsec_client, "remove_api_request_constraints",
                 models.RemoveApiRequestConstraintsRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestApiRequestConstraints/ApiRequestConstraints.json")

    def test_remove_api_request_constraints_500(self, mock_appsec_client):
        """Test RemoveApiRequestConstraints raises Error on 500."""
        _error(mock_appsec_client, "remove_api_request_constraints",
               models.RemoveApiRequestConstraintsRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error deleting match target"))


# ===================================================================
# TestApiConstraintsProtection  (mirrors api_constraints_protection_test.go)
# ===================================================================

class TestApiConstraintsProtection:
    """API constraints protection tests – mirrors api_constraints_protection_test.go."""

    def test_get_api_constraints_protection_200(self, mock_appsec_client):
        """Test GetAPIConstraintsProtection on 200 OK."""
        _success(mock_appsec_client, "get_api_constraints_protection",
                 models.GetAPIConstraintsProtectionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestAPIConstraintsProtections/APIConstraintsProtections.json")

    def test_get_api_constraints_protection_500(self, mock_appsec_client):
        """Test GetAPIConstraintsProtection raises Error on 500."""
        _error(mock_appsec_client, "get_api_constraints_protection",
               models.GetAPIConstraintsProtectionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_update_api_constraints_protection_200(self, mock_appsec_client):
        """Test UpdateAPIConstraintsProtection on 200 OK."""
        _success(mock_appsec_client, "update_api_constraints_protection",
                 models.UpdateAPIConstraintsProtectionRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestAPIConstraintsProtections/APIConstraintsProtections.json")

    def test_update_api_constraints_protection_500(self, mock_appsec_client):
        """Test UpdateAPIConstraintsProtection raises Error on 500."""
        _error(mock_appsec_client, "update_api_constraints_protection",
               models.UpdateAPIConstraintsProtectionRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error creating zone"))


# ===================================================================
# TestSiemDefinitions  (mirrors siem_definitions_test.go)
# ===================================================================

class TestSiemDefinitions:
    """SIEM definitions tests – mirrors siem_definitions_test.go."""

    def test_get_siem_definitions_200(self, mock_appsec_client):
        """Test GetSiemDefinitions on 200 OK."""
        _success(mock_appsec_client, "get_siem_definitions",
                 models.GetSiemDefinitionsRequest(),
                 "TestSiemDefinitions/SiemDefinitions.json")

    def test_get_siem_definitions_500(self, mock_appsec_client):
        """Test GetSiemDefinitions raises Error on 500."""
        _error(mock_appsec_client, "get_siem_definitions",
               models.GetSiemDefinitionsRequest(),
               _err_500("Error fetching match target"))


# ===================================================================
# TestSiemSettings  (mirrors siem_settings_test.go)
# ===================================================================

class TestSiemSettings:
    """SIEM settings tests – mirrors siem_settings_test.go."""

    def test_list_siem_settings_200(self, mock_appsec_client):
        """Test GetSiemSettings (list) on 200 OK."""
        _success(mock_appsec_client, "get_siem_settings",
                 models.GetSiemSettingsRequest(
                     config_id=43253, version=15),
                 "TestSiemSettings/SiemSettings.json")

    def test_list_siem_settings_500(self, mock_appsec_client):
        """Test GetSiemSettings raises Error on 500."""
        _error(mock_appsec_client, "get_siem_settings",
               models.GetSiemSettingsRequest(
                   config_id=43253, version=15),
               _err_500("Error fetching propertys"))

    def test_get_siem_settings_200(self, mock_appsec_client):
        """Test GetSiemSettings on 200 OK."""
        _success(mock_appsec_client, "get_siem_settings",
                 models.GetSiemSettingsRequest(
                     config_id=43253, version=15),
                 "TestSiemSettings/SiemSettings.json")

    def test_get_siem_settings_500(self, mock_appsec_client):
        """Test GetSiemSettings raises Error on 500."""
        _error(mock_appsec_client, "get_siem_settings",
               models.GetSiemSettingsRequest(
                   config_id=43253, version=15),
               _err_500("Error fetching match target"))

    def test_update_siem_settings_200(self, mock_appsec_client):
        """Test UpdateSiemSettings on 200 OK."""
        _success(mock_appsec_client, "update_siem_settings",
                 models.UpdateSiemSettingsRequest(
                     config_id=43253, version=15),
                 "TestSiemSettings/SiemSettings.json")

    def test_update_siem_settings_500(self, mock_appsec_client):
        """Test UpdateSiemSettings raises Error on 500."""
        _error(mock_appsec_client, "update_siem_settings",
               models.UpdateSiemSettingsRequest(
                   config_id=43253, version=15),
               _err_500("Error creating zone"))

    def test_remove_siem_settings_200(self, mock_appsec_client):
        """Test RemoveSiemSettings on 200 OK."""
        _success(mock_appsec_client, "remove_siem_settings",
                 models.RemoveSiemSettingsRequest(
                     config_id=43253, version=15),
                 "TestSiemSettings/SiemSettings.json")

    def test_remove_siem_settings_500(self, mock_appsec_client):
        """Test RemoveSiemSettings raises Error on 500."""
        _error(mock_appsec_client, "remove_siem_settings",
               models.RemoveSiemSettingsRequest(
                   config_id=43253, version=15),
               _err_500("Error deleting match target"))


# ===================================================================
# TestContractsGroups  (mirrors contracts_groups_test.go)
# ===================================================================

class TestContractsGroups:
    """Contracts groups tests – mirrors contracts_groups_test.go."""

    def test_get_contracts_groups_200(self, mock_appsec_client):
        """Test GetContractsGroups on 200 OK."""
        _success(mock_appsec_client, "get_contracts_groups",
                 models.GetContractsGroupsRequest(),
                 "TestContractsGroups/ContractsGroups.json")

    def test_get_contracts_groups_500(self, mock_appsec_client):
        """Test GetContractsGroups raises Error on 500."""
        _error(mock_appsec_client, "get_contracts_groups",
               models.GetContractsGroupsRequest(),
               _err_500("Error fetching match target"))


# ===================================================================
# TestSelectableHostnames  (mirrors selectable_hostnames_test.go)
# ===================================================================

class TestSelectableHostnames:
    """Selectable hostnames tests – mirrors selectable_hostnames_test.go."""

    def test_list_selectable_hostnames_200(self, mock_appsec_client):
        """Test GetSelectableHostnames (list) on 200 OK."""
        _success(mock_appsec_client, "get_selectable_hostnames",
                 models.GetSelectableHostnamesRequest(
                     config_id=43253, version=15),
                 "TestSelectableHostnames/SelectableHostnames.json")

    def test_list_selectable_hostnames_500(self, mock_appsec_client):
        """Test GetSelectableHostnames raises Error on 500."""
        _error(mock_appsec_client, "get_selectable_hostnames",
               models.GetSelectableHostnamesRequest(
                   config_id=43253, version=15),
               _err_500("Error fetching propertys"))

    def test_get_selectable_hostnames_200(self, mock_appsec_client):
        """Test GetSelectableHostnames on 200 OK."""
        _success(mock_appsec_client, "get_selectable_hostnames",
                 models.GetSelectableHostnamesRequest(
                     config_id=43253, version=15),
                 "TestSelectableHostnames/SelectableHostnames.json")

    def test_get_selectable_hostnames_500(self, mock_appsec_client):
        """Test GetSelectableHostnames raises Error on 500."""
        _error(mock_appsec_client, "get_selectable_hostnames",
               models.GetSelectableHostnamesRequest(
                   config_id=43253, version=15),
               _err_500("Error fetching match target"))


# ===================================================================
# TestSelectedHostnames  (mirrors selected_hostname_test.go)
# ===================================================================

class TestSelectedHostnames:
    """Selected hostnames tests – mirrors selected_hostname_test.go."""

    def test_list_selected_hostnames_200(self, mock_appsec_client):
        """Test GetSelectedHostnames (list) on 200 OK."""
        _success(mock_appsec_client, "get_selected_hostnames",
                 models.GetSelectedHostnamesRequest(
                     config_id=43253, version=15),
                 "TestSelectedHostnames/SelectedHostnames.json")

    def test_list_selected_hostnames_500(self, mock_appsec_client):
        """Test GetSelectedHostnames raises Error on 500."""
        _error(mock_appsec_client, "get_selected_hostnames",
               models.GetSelectedHostnamesRequest(
                   config_id=43253, version=15),
               _err_500("Error fetching propertys"))

    def test_get_selected_hostnames_200(self, mock_appsec_client):
        """Test GetSelectedHostnames on 200 OK."""
        _success(mock_appsec_client, "get_selected_hostnames",
                 models.GetSelectedHostnamesRequest(
                     config_id=43253, version=15),
                 "TestSelectedHostnames/SelectedHostnames.json")

    def test_get_selected_hostnames_500(self, mock_appsec_client):
        """Test GetSelectedHostnames raises Error on 500."""
        _error(mock_appsec_client, "get_selected_hostnames",
               models.GetSelectedHostnamesRequest(
                   config_id=43253, version=15),
               _err_500("Error fetching match target"))

    def test_update_selected_hostname_200(self, mock_appsec_client):
        """Test UpdateSelectedHostname on 200 OK."""
        _success(mock_appsec_client, "update_selected_hostname",
                 models.UpdateSelectedHostnameRequest(
                     config_id=43253, version=15),
                 "TestSelectedHostnames/SelectedHostnames.json")

    def test_update_selected_hostname_500(self, mock_appsec_client):
        """Test UpdateSelectedHostname raises Error on 500."""
        _error(mock_appsec_client, "update_selected_hostname",
               models.UpdateSelectedHostnameRequest(
                   config_id=43253, version=15),
               _err_500("Error creating zone"))


# ===================================================================
# TestWAPSelectedHostnames  (mirrors wap_selected_hostnames_test.go)
# ===================================================================

class TestWAPSelectedHostnames:
    """WAP selected hostnames tests – mirrors wap_selected_hostnames_test.go."""

    def test_get_wap_selected_hostnames_200(self, mock_appsec_client):
        """Test GetWAPSelectedHostnames on 200 OK."""
        _success(mock_appsec_client, "get_wap_selected_hostnames",
                 models.GetWAPSelectedHostnamesRequest(
                     config_id=43253, version=15, security_policy_id="AAAA_81230"),
                 "TestWAPSelectedHostnames/WAPSelectedHostnames.json")

    def test_get_wap_selected_hostnames_500(self, mock_appsec_client):
        """Test GetWAPSelectedHostnames raises Error on 500."""
        _error(mock_appsec_client, "get_wap_selected_hostnames",
               models.GetWAPSelectedHostnamesRequest(
                   config_id=43253, version=15, security_policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_update_wap_selected_hostnames_200(self, mock_appsec_client):
        """Test UpdateWAPSelectedHostnames on 200 OK."""
        _success(mock_appsec_client, "update_wap_selected_hostnames",
                 models.UpdateWAPSelectedHostnamesRequest(
                     config_id=43253, version=15, security_policy_id="AAAA_81230"),
                 "TestWAPSelectedHostnames/WAPSelectedHostnames.json")

    def test_update_wap_selected_hostnames_500(self, mock_appsec_client):
        """Test UpdateWAPSelectedHostnames raises Error on 500."""
        _error(mock_appsec_client, "update_wap_selected_hostnames",
               models.UpdateWAPSelectedHostnamesRequest(
                   config_id=43253, version=15, security_policy_id="AAAA_81230"),
               _err_500("Error creating zone"))


# ===================================================================
# TestWAPBypassNetworkLists  (mirrors wap_bypass_network_lists_test.go)
# ===================================================================

class TestWAPBypassNetworkLists:
    """WAP bypass network lists tests – mirrors wap_bypass_network_lists_test.go."""

    def test_list_wap_bypass_network_lists_200(self, mock_appsec_client):
        """Test GetWAPBypassNetworkLists (list) on 200 OK."""
        _success(mock_appsec_client, "get_wap_bypass_network_lists",
                 models.GetWAPBypassNetworkListsRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestBypassNetworkLists/BypassNetworkLists.json")

    def test_list_wap_bypass_network_lists_500(self, mock_appsec_client):
        """Test GetWAPBypassNetworkLists raises Error on 500."""
        _error(mock_appsec_client, "get_wap_bypass_network_lists",
               models.GetWAPBypassNetworkListsRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching propertys"))

    def test_get_wap_bypass_network_lists_200(self, mock_appsec_client):
        """Test GetWAPBypassNetworkLists on 200 OK."""
        _success(mock_appsec_client, "get_wap_bypass_network_lists",
                 models.GetWAPBypassNetworkListsRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestBypassNetworkLists/BypassNetworkLists.json")

    def test_get_wap_bypass_network_lists_500(self, mock_appsec_client):
        """Test GetWAPBypassNetworkLists raises Error on 500."""
        _error(mock_appsec_client, "get_wap_bypass_network_lists",
               models.GetWAPBypassNetworkListsRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_update_wap_bypass_network_lists_200(self, mock_appsec_client):
        """Test UpdateWAPBypassNetworkLists on 200 OK."""
        _success(mock_appsec_client, "update_wap_bypass_network_lists",
                 models.UpdateWAPBypassNetworkListsRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestBypassNetworkLists/BypassNetworkLists.json")

    def test_update_wap_bypass_network_lists_500(self, mock_appsec_client):
        """Test UpdateWAPBypassNetworkLists raises Error on 500."""
        _error(mock_appsec_client, "update_wap_bypass_network_lists",
               models.UpdateWAPBypassNetworkListsRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error creating zone"))


# ===================================================================
# TestFailoverHostnames  (mirrors failover_hostnames_test.go)
# ===================================================================

class TestFailoverHostnames:
    """Failover hostnames tests – mirrors failover_hostnames_test.go."""

    def test_list_failover_hostnames_200(self, mock_appsec_client):
        """Test GetFailoverHostnames (list) on 200 OK."""
        _success(mock_appsec_client, "get_failover_hostnames",
                 models.GetFailoverHostnamesRequest(
                     config_id=43253),
                 "TestFailoverHostnames/FailoverHostnames.json")

    def test_list_failover_hostnames_500(self, mock_appsec_client):
        """Test GetFailoverHostnames raises Error on 500."""
        _error(mock_appsec_client, "get_failover_hostnames",
               models.GetFailoverHostnamesRequest(
                   config_id=43253),
               _err_500("Error fetching propertys"))

    def test_get_failover_hostnames_200(self, mock_appsec_client):
        """Test GetFailoverHostnames on 200 OK."""
        _success(mock_appsec_client, "get_failover_hostnames",
                 models.GetFailoverHostnamesRequest(
                     config_id=43253),
                 "TestFailoverHostnames/FailoverHostnames.json")

    def test_get_failover_hostnames_500(self, mock_appsec_client):
        """Test GetFailoverHostnames raises Error on 500."""
        _error(mock_appsec_client, "get_failover_hostnames",
               models.GetFailoverHostnamesRequest(
                   config_id=43253),
               _err_500("Error fetching match target"))


# ===================================================================
# TestHostMoveActivations  (mirrors host_move_activations_test.go)
# ===================================================================

class TestHostMoveActivations:
    """Host move activation tests – mirrors host_move_activations_test.go."""

    def test_get_host_move_validation_200(self, mock_appsec_client):
        """Test GetHostMoveValidation on 200 OK."""
        _success(mock_appsec_client, "get_host_move_validation",
                 models.GetHostMoveValidationRequest(
                     config_id=43253, config_version=1, network="STAGING"),
                 "TestHostMoveActivations/HostMoveValidation.json")

    def test_get_host_move_validation_500(self, mock_appsec_client):
        """Test GetHostMoveValidation raises Error on 500."""
        _error(mock_appsec_client, "get_host_move_validation",
               models.GetHostMoveValidationRequest(
                   config_id=43253, config_version=1, network="STAGING"),
               _err_500("Error fetching host move validation"))

    def test_create_activations_with_host_move_200(self, mock_appsec_client):
        """Test CreateActivationsWithHostMove on 200 OK."""
        _success(mock_appsec_client, "create_activations_with_host_move",
                 models.CreateActivationsWithHostMoveRequest(
                     config_id=43253, config_version=1,
                     action="ACTIVATE", network="STAGING",
                     note="Test activation with host move",
                     notification_emails=["test@example.com"]),
                 "TestHostMoveActivations/CreateActivationsWithHostMove.json")

    def test_create_activations_with_host_move_500(self, mock_appsec_client):
        """Test CreateActivationsWithHostMove raises Error on 500."""
        _error(mock_appsec_client, "create_activations_with_host_move",
               models.CreateActivationsWithHostMoveRequest(
                   config_id=43253, config_version=1,
                   action="ACTIVATE", network="STAGING",
                   note="Test activation with host move",
                   notification_emails=["test@example.com"]),
               _err_500("Error creating activation with host move"))


# ===================================================================
# TestExportConfiguration  (mirrors export_configuration_test.go)
# ===================================================================

class TestExportConfiguration:
    """Export configuration tests – mirrors export_configuration_test.go."""

    def test_list_export_configuration_200(self, mock_appsec_client):
        """Test GetExportConfigurations (list) on 200 OK."""
        _success(mock_appsec_client, "get_export_configuration",
                 models.GetExportConfigurationRequest(
                     config_id=43253, version=15),
                 "TestExportConfiguration/ExportConfiguration.json")

    def test_list_export_configuration_500(self, mock_appsec_client):
        """Test GetExportConfigurations raises Error on 500."""
        _error(mock_appsec_client, "get_export_configuration",
               models.GetExportConfigurationRequest(
                   config_id=43253, version=15),
               _err_500("Error fetching propertys"))

    def test_get_export_configuration_200(self, mock_appsec_client):
        """Test GetExportConfiguration on 200 OK."""
        _success(mock_appsec_client, "get_export_configuration",
                 models.GetExportConfigurationRequest(
                     config_id=43253, version=15),
                 "TestExportConfiguration/ExportConfiguration.json")

    def test_get_export_configuration_500(self, mock_appsec_client):
        """Test GetExportConfiguration raises Error on 500."""
        _error(mock_appsec_client, "get_export_configuration",
               models.GetExportConfigurationRequest(
                   config_id=43253, version=15),
               _err_500("Error fetching match target"))


# ===================================================================
# TestVersionNotes  (mirrors version_notes_test.go)
# ===================================================================

class TestVersionNotes:
    """Version notes tests – mirrors version_notes_test.go."""

    def test_list_version_notes_200(self, mock_appsec_client):
        """Test GetVersionNotes (list) on 200 OK."""
        _success(mock_appsec_client, "get_version_notes",
                 models.GetVersionNotesRequest(
                     config_id=43253, version=15),
                 "TestVersionNotes/VersionNotes.json")

    def test_list_version_notes_500(self, mock_appsec_client):
        """Test GetVersionNotes raises Error on 500."""
        _error(mock_appsec_client, "get_version_notes",
               models.GetVersionNotesRequest(
                   config_id=43253, version=15),
               _err_500("Error fetching propertys"))

    def test_get_version_notes_200(self, mock_appsec_client):
        """Test GetVersionNotes on 200 OK."""
        _success(mock_appsec_client, "get_version_notes",
                 models.GetVersionNotesRequest(
                     config_id=43253, version=15),
                 "TestVersionNotes/VersionNotes.json")

    def test_get_version_notes_500(self, mock_appsec_client):
        """Test GetVersionNotes raises Error on 500."""
        _error(mock_appsec_client, "get_version_notes",
               models.GetVersionNotesRequest(
                   config_id=43253, version=15),
               _err_500("Error fetching match target"))

    def test_update_version_notes_200(self, mock_appsec_client):
        """Test UpdateVersionNotes on 200 OK."""
        _success(mock_appsec_client, "update_version_notes",
                 models.UpdateVersionNotesRequest(
                     config_id=43253, version=15),
                 "TestVersionNotes/VersionNotes.json")

    def test_update_version_notes_500(self, mock_appsec_client):
        """Test UpdateVersionNotes raises Error on 500."""
        _error(mock_appsec_client, "update_version_notes",
               models.UpdateVersionNotesRequest(
                   config_id=43253, version=15),
               _err_500("Error creating zone"))


# ===================================================================
# TestThreatIntel  (mirrors threat_intel_test.go)
# ===================================================================

class TestThreatIntel:
    """Threat intel tests – mirrors threat_intel_test.go."""

    def test_list_threat_intel_200(self, mock_appsec_client):
        """Test GetThreatIntel (list) on 200 OK."""
        _success(mock_appsec_client, "get_threat_intel",
                 models.GetThreatIntelRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestThreatIntel/ThreatIntel.json")

    def test_list_threat_intel_500(self, mock_appsec_client):
        """Test GetThreatIntel raises Error on 500."""
        _error(mock_appsec_client, "get_threat_intel",
               models.GetThreatIntelRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching propertys"))

    def test_get_threat_intel_200(self, mock_appsec_client):
        """Test GetThreatIntel on 200 OK."""
        _success(mock_appsec_client, "get_threat_intel",
                 models.GetThreatIntelRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestThreatIntel/ThreatIntel.json")

    def test_get_threat_intel_500(self, mock_appsec_client):
        """Test GetThreatIntel raises Error on 500."""
        _error(mock_appsec_client, "get_threat_intel",
               models.GetThreatIntelRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_update_threat_intel_200(self, mock_appsec_client):
        """Test UpdateThreatIntel on 200 OK."""
        _success(mock_appsec_client, "update_threat_intel",
                 models.UpdateThreatIntelRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestThreatIntel/ThreatIntel.json")

    def test_update_threat_intel_500(self, mock_appsec_client):
        """Test UpdateThreatIntel raises Error on 500."""
        _error(mock_appsec_client, "update_threat_intel",
               models.UpdateThreatIntelRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error creating zone"))


# ===================================================================
# TestTuningRecommendations  (mirrors tuning_recommendations_test.go)
# ===================================================================

class TestTuningRecommendations:
    """Tuning recommendations tests – mirrors tuning_recommendations_test.go."""

    def test_get_tuning_recommendations_200(self, mock_appsec_client):
        """Test GetTuningRecommendations on 200 OK."""
        _success(mock_appsec_client, "get_tuning_recommendations",
                 models.GetTuningRecommendationsRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230"),
                 "TestTuningRecommendations/Recommendations.json")

    def test_get_tuning_recommendations_500(self, mock_appsec_client):
        """Test GetTuningRecommendations raises Error on 500."""
        _error(mock_appsec_client, "get_tuning_recommendations",
               models.GetTuningRecommendationsRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230"),
               _err_500("Error fetching match target"))

    def test_get_attack_group_recommendations_200(self, mock_appsec_client):
        """Test GetAttackGroupRecommendations on 200 OK."""
        _success(mock_appsec_client, "get_attack_group_recommendations",
                 models.GetAttackGroupRecommendationsRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230",
                     group="SQL"),
                 "TestTuningRecommendations/AttackGroupRecommendations.json")

    def test_get_attack_group_recommendations_500(self, mock_appsec_client):
        """Test GetAttackGroupRecommendations raises Error on 500."""
        _error(mock_appsec_client, "get_attack_group_recommendations",
               models.GetAttackGroupRecommendationsRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230",
                   group="SQL"),
               _err_500("Error fetching match target"))

    def test_get_rule_recommendations_200(self, mock_appsec_client):
        """Test GetRuleRecommendations on 200 OK."""
        _success(mock_appsec_client, "get_rule_recommendations",
                 models.GetRuleRecommendationsRequest(
                     config_id=43253, version=15, policy_id="AAAA_81230",
                     rule_id=958008),
                 "TestTuningRecommendations/RuleRecommendations.json")

    def test_get_rule_recommendations_500(self, mock_appsec_client):
        """Test GetRuleRecommendations raises Error on 500."""
        _error(mock_appsec_client, "get_rule_recommendations",
               models.GetRuleRecommendationsRequest(
                   config_id=43253, version=15, policy_id="AAAA_81230",
                   rule_id=958008),
               _err_500("Error fetching match target"))


# ===================================================================
# TestAdvancedSettingsAsePenaltyBox
# (mirrors advanced_settings_ase_penalty_box_test.go)
# ===================================================================

class TestAdvancedSettingsAsePenaltyBox:
    """ASE penalty box advanced settings tests."""

    def test_list_ase_penalty_box_200(self, mock_appsec_client):
        """Test GetAdvancedSettingsAsePenaltyBox (list) on 200 OK."""
        _success(mock_appsec_client, "get_advanced_settings_ase_penalty_box",
                 models.GetAdvancedSettingsAsePenaltyBoxRequest(
                     config_id=43253, version=15),
                 "TestAdvancedSettingsAsePenaltyBox/AdvancedSettingsAsePenaltyBox.json")

    def test_list_ase_penalty_box_500(self, mock_appsec_client):
        """Test GetAdvancedSettingsAsePenaltyBox raises Error on 500."""
        _error(mock_appsec_client, "get_advanced_settings_ase_penalty_box",
               models.GetAdvancedSettingsAsePenaltyBoxRequest(
                   config_id=43253, version=15),
               _err_500("Error fetching propertys"))

    def test_get_ase_penalty_box_200(self, mock_appsec_client):
        """Test GetAdvancedSettingsAsePenaltyBox on 200 OK."""
        _success(mock_appsec_client, "get_advanced_settings_ase_penalty_box",
                 models.GetAdvancedSettingsAsePenaltyBoxRequest(
                     config_id=43253, version=15),
                 "TestAdvancedSettingsAsePenaltyBox/AdvancedSettingsAsePenaltyBox.json")

    def test_get_ase_penalty_box_500(self, mock_appsec_client):
        """Test GetAdvancedSettingsAsePenaltyBox raises Error on 500."""
        _error(mock_appsec_client, "get_advanced_settings_ase_penalty_box",
               models.GetAdvancedSettingsAsePenaltyBoxRequest(
                   config_id=43253, version=15),
               _err_500("Error fetching match target"))

    def test_update_ase_penalty_box_200(self, mock_appsec_client):
        """Test UpdateAdvancedSettingsAsePenaltyBox on 200 OK."""
        _success(mock_appsec_client, "update_advanced_settings_ase_penalty_box",
                 models.UpdateAdvancedSettingsAsePenaltyBoxRequest(
                     config_id=43253, version=15),
                 "TestAdvancedSettingsAsePenaltyBox/AdvancedSettingsAsePenaltyBox.json")

    def test_update_ase_penalty_box_500(self, mock_appsec_client):
        """Test UpdateAdvancedSettingsAsePenaltyBox raises Error on 500."""
        _error(mock_appsec_client, "update_advanced_settings_ase_penalty_box",
               models.UpdateAdvancedSettingsAsePenaltyBoxRequest(
                   config_id=43253, version=15),
               _err_500("Error creating zone"))

    def test_remove_ase_penalty_box_200(self, mock_appsec_client):
        """Test RemoveAdvancedSettingsAsePenaltyBox on 200 OK."""
        _success(mock_appsec_client, "remove_advanced_settings_ase_penalty_box",
                 models.RemoveAdvancedSettingsAsePenaltyBoxRequest(
                     config_id=43253, version=15),
                 "TestAdvancedSettingsAsePenaltyBox/AdvancedSettingsAsePenaltyBox.json")

    def test_remove_ase_penalty_box_500(self, mock_appsec_client):
        """Test RemoveAdvancedSettingsAsePenaltyBox raises Error on 500."""
        _error(mock_appsec_client, "remove_advanced_settings_ase_penalty_box",
               models.RemoveAdvancedSettingsAsePenaltyBoxRequest(
                   config_id=43253, version=15),
               _err_500("Error deleting match target"))


# ===================================================================
# TestAdvancedSettingsAttackPayloadLogging
# (mirrors advanced_settings_attack_payload_logging_test.go)
# ===================================================================

class TestAdvancedSettingsAttackPayloadLogging:
    """Attack payload logging advanced settings tests."""

    def test_list_attack_payload_logging_200(self, mock_appsec_client):
        """Test GetAdvancedSettingsAttackPayloadLogging (list) on 200 OK."""
        _success(
            mock_appsec_client, "get_advanced_settings_attack_payload_logging",
            models.GetAdvancedSettingsAttackPayloadLoggingRequest(
                config_id=43253, version=15),
            "TestAdvancedSettingsAttackPayloadLogging/"
            "AdvancedSettingsAttackPayloadLoggingConfig.json")

    def test_list_attack_payload_logging_500(self, mock_appsec_client):
        """Test GetAdvancedSettingsAttackPayloadLogging raises Error on 500."""
        _error(
            mock_appsec_client, "get_advanced_settings_attack_payload_logging",
            models.GetAdvancedSettingsAttackPayloadLoggingRequest(
                config_id=43253, version=15),
            _err_500("Error fetching propertys"))

    def test_get_attack_payload_logging_policy_200(self, mock_appsec_client):
        """Test GetAdvancedSettingsAttackPayloadLogging per-policy on 200 OK."""
        _success(
            mock_appsec_client, "get_advanced_settings_attack_payload_logging",
            models.GetAdvancedSettingsAttackPayloadLoggingRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            "TestAdvancedSettingsAttackPayloadLogging/"
            "AdvancedSettingsAttackPayloadLoggingPolicy.json")

    def test_get_attack_payload_logging_policy_500(self, mock_appsec_client):
        """Test GetAdvancedSettingsAttackPayloadLogging per-policy raises Error on 500."""
        _error(
            mock_appsec_client, "get_advanced_settings_attack_payload_logging",
            models.GetAdvancedSettingsAttackPayloadLoggingRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            _err_500("Error fetching match target"))

    def test_update_attack_payload_logging_200(self, mock_appsec_client):
        """Test UpdateAdvancedSettingsAttackPayloadLogging on 200 OK."""
        _success(
            mock_appsec_client, "update_advanced_settings_attack_payload_logging",
            models.UpdateAdvancedSettingsAttackPayloadLoggingRequest(
                config_id=43253, version=15),
            "TestAdvancedSettingsAttackPayloadLogging/"
            "AdvancedSettingsAttackPayloadLoggingConfig.json")

    def test_update_attack_payload_logging_500(self, mock_appsec_client):
        """Test UpdateAdvancedSettingsAttackPayloadLogging raises Error on 500."""
        _error(
            mock_appsec_client, "update_advanced_settings_attack_payload_logging",
            models.UpdateAdvancedSettingsAttackPayloadLoggingRequest(
                config_id=43253, version=15),
            _err_500("Error creating zone"))

    def test_update_attack_payload_logging_policy_200(self, mock_appsec_client):
        """Test UpdateAdvancedSettingsAttackPayloadLogging per-policy on 200 OK."""
        _success(
            mock_appsec_client, "update_advanced_settings_attack_payload_logging",
            models.UpdateAdvancedSettingsAttackPayloadLoggingRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            "TestAdvancedSettingsAttackPayloadLogging/"
            "AdvancedSettingsAttackPayloadLoggingPolicy.json")

    def test_update_attack_payload_logging_policy_500(self, mock_appsec_client):
        """Test UpdateAdvancedSettingsAttackPayloadLogging per-policy raises Error."""
        _error(
            mock_appsec_client, "update_advanced_settings_attack_payload_logging",
            models.UpdateAdvancedSettingsAttackPayloadLoggingRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            _err_500("Error creating zone"))

    def test_remove_attack_payload_logging_200(self, mock_appsec_client):
        """Test RemoveAdvancedSettingsAttackPayloadLogging on 200 OK."""
        _success(
            mock_appsec_client, "remove_advanced_settings_attack_payload_logging",
            models.RemoveAdvancedSettingsAttackPayloadLoggingRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            "TestAdvancedSettingsAttackPayloadLogging/"
            "AdvancedSettingsAttackPayloadLoggingPolicy.json")

    def test_remove_attack_payload_logging_500(self, mock_appsec_client):
        """Test RemoveAdvancedSettingsAttackPayloadLogging raises Error on 500."""
        _error(
            mock_appsec_client, "remove_advanced_settings_attack_payload_logging",
            models.RemoveAdvancedSettingsAttackPayloadLoggingRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            _err_500("Error deleting match target"))


# ===================================================================
# TestAdvancedSettingsEvasivePathMatch
# (mirrors advanced_settings_evasive_path_match_test.go)
# ===================================================================

class TestAdvancedSettingsEvasivePathMatch:
    """Evasive path match advanced settings tests."""

    def test_list_evasive_path_match_200(self, mock_appsec_client):
        """Test GetAdvancedSettingsEvasivePathMatch (list) on 200 OK."""
        _success(
            mock_appsec_client, "get_advanced_settings_evasive_path_match",
            models.GetAdvancedSettingsEvasivePathMatchRequest(
                config_id=43253, version=15),
            "TestAdvancedSettingsEvasivePathMatch/"
            "AdvancedSettingsEvasivePathMatch.json")

    def test_list_evasive_path_match_500(self, mock_appsec_client):
        """Test GetAdvancedSettingsEvasivePathMatch raises Error on 500."""
        _error(
            mock_appsec_client, "get_advanced_settings_evasive_path_match",
            models.GetAdvancedSettingsEvasivePathMatchRequest(
                config_id=43253, version=15),
            _err_500("Error fetching propertys"))

    def test_get_evasive_path_match_200(self, mock_appsec_client):
        """Test GetAdvancedSettingsEvasivePathMatch on 200 OK."""
        _success(
            mock_appsec_client, "get_advanced_settings_evasive_path_match",
            models.GetAdvancedSettingsEvasivePathMatchRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            "TestAdvancedSettingsPolicyEvasivePathMatch/"
            "AdvancedSettingsPolicyEvasivePathMatch.json")

    def test_get_evasive_path_match_500(self, mock_appsec_client):
        """Test GetAdvancedSettingsEvasivePathMatch raises Error on 500."""
        _error(
            mock_appsec_client, "get_advanced_settings_evasive_path_match",
            models.GetAdvancedSettingsEvasivePathMatchRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            _err_500("Error fetching match target"))

    def test_update_evasive_path_match_200(self, mock_appsec_client):
        """Test UpdateAdvancedSettingsEvasivePathMatch on 200 OK."""
        _success(
            mock_appsec_client, "update_advanced_settings_evasive_path_match",
            models.UpdateAdvancedSettingsEvasivePathMatchRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            "TestAdvancedSettingsPolicyEvasivePathMatch/"
            "AdvancedSettingsPolicyEvasivePathMatch.json")

    def test_update_evasive_path_match_500(self, mock_appsec_client):
        """Test UpdateAdvancedSettingsEvasivePathMatch raises Error on 500."""
        _error(
            mock_appsec_client, "update_advanced_settings_evasive_path_match",
            models.UpdateAdvancedSettingsEvasivePathMatchRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            _err_500("Error creating zone"))


# ===================================================================
# TestAdvancedSettingsJA4Fingerprint
# (mirrors advanced_settings_ja4_fingerprints_test.go)
# ===================================================================

class TestAdvancedSettingsJA4Fingerprint:
    """JA4 fingerprint advanced settings tests."""

    def test_get_ja4_fingerprint_200(self, mock_appsec_client):
        """Test GetAdvancedSettingsJA4Fingerprint on 200 OK."""
        _success(
            mock_appsec_client, "get_advanced_settings_ja4_fingerprint",
            models.GetAdvancedSettingsJA4FingerprintRequest(
                config_id=43253, version=15),
            "TestAdvancedSettingsJA4Fingerprint/"
            "AdvancedSettingsJA4Fingerprint.json")

    def test_get_ja4_fingerprint_500(self, mock_appsec_client):
        """Test GetAdvancedSettingsJA4Fingerprint raises Error on 500."""
        _error(
            mock_appsec_client, "get_advanced_settings_ja4_fingerprint",
            models.GetAdvancedSettingsJA4FingerprintRequest(
                config_id=43253, version=15),
            _err_500("Error fetching match target"))

    def test_update_ja4_fingerprint_200(self, mock_appsec_client):
        """Test UpdateAdvancedSettingsJA4Fingerprint on 200 OK."""
        _success(
            mock_appsec_client, "update_advanced_settings_ja4_fingerprint",
            models.UpdateAdvancedSettingsJA4FingerprintRequest(
                config_id=43253, version=15),
            "TestAdvancedSettingsJA4Fingerprint/"
            "AdvancedSettingsJA4Fingerprint.json")

    def test_update_ja4_fingerprint_500(self, mock_appsec_client):
        """Test UpdateAdvancedSettingsJA4Fingerprint raises Error on 500."""
        _error(
            mock_appsec_client, "update_advanced_settings_ja4_fingerprint",
            models.UpdateAdvancedSettingsJA4FingerprintRequest(
                config_id=43253, version=15),
            _err_500("Error creating zone"))


# ===================================================================
# TestAdvancedSettingsLogging  (mirrors advanced_settings_logging_test.go)
# ===================================================================

class TestAdvancedSettingsLogging:
    """Logging advanced settings tests."""

    def test_list_logging_200(self, mock_appsec_client):
        """Test GetAdvancedSettingsLogging (list) on 200 OK."""
        _success(
            mock_appsec_client, "get_advanced_settings_logging",
            models.GetAdvancedSettingsLoggingRequest(
                config_id=43253, version=15),
            "TestAdvancedSettingsLogging/AdvancedSettingsLogging.json")

    def test_list_logging_500(self, mock_appsec_client):
        """Test GetAdvancedSettingsLogging raises Error on 500."""
        _error(
            mock_appsec_client, "get_advanced_settings_logging",
            models.GetAdvancedSettingsLoggingRequest(
                config_id=43253, version=15),
            _err_500("Error fetching propertys"))

    def test_get_logging_200(self, mock_appsec_client):
        """Test GetAdvancedSettingsLogging on 200 OK."""
        _success(
            mock_appsec_client, "get_advanced_settings_logging",
            models.GetAdvancedSettingsLoggingRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            "TestAdvancedSettingsPolicyLogging/AdvancedSettingsPolicyLogging.json")

    def test_get_logging_500(self, mock_appsec_client):
        """Test GetAdvancedSettingsLogging raises Error on 500."""
        _error(
            mock_appsec_client, "get_advanced_settings_logging",
            models.GetAdvancedSettingsLoggingRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            _err_500("Error fetching match target"))

    def test_update_logging_200(self, mock_appsec_client):
        """Test UpdateAdvancedSettingsLogging on 200 OK."""
        _success(
            mock_appsec_client, "update_advanced_settings_logging",
            models.UpdateAdvancedSettingsLoggingRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            "TestAdvancedSettingsPolicyLogging/AdvancedSettingsPolicyLogging.json")

    def test_update_logging_500(self, mock_appsec_client):
        """Test UpdateAdvancedSettingsLogging raises Error on 500."""
        _error(
            mock_appsec_client, "update_advanced_settings_logging",
            models.UpdateAdvancedSettingsLoggingRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            _err_500("Error creating zone"))

    def test_remove_logging_200(self, mock_appsec_client):
        """Test RemoveAdvancedSettingsLogging on 200 OK."""
        _success(
            mock_appsec_client, "remove_advanced_settings_logging",
            models.RemoveAdvancedSettingsLoggingRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            "TestAdvancedSettingsPolicyLogging/AdvancedSettingsPolicyLogging.json")

    def test_remove_logging_500(self, mock_appsec_client):
        """Test RemoveAdvancedSettingsLogging raises Error on 500."""
        _error(
            mock_appsec_client, "remove_advanced_settings_logging",
            models.RemoveAdvancedSettingsLoggingRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            _err_500("Error deleting match target"))


# ===================================================================
# TestAdvancedSettingsPIILearning
# (mirrors advanced_settings_pii_learning_test.go)
# ===================================================================

class TestAdvancedSettingsPIILearning:
    """PII learning advanced settings tests."""

    def test_get_pii_learning_200(self, mock_appsec_client):
        """Test GetAdvancedSettingsPIILearning on 200 OK."""
        _success(
            mock_appsec_client, "get_advanced_settings_pii_learning",
            models.GetAdvancedSettingsPIILearningRequest(
                config_id=43253, version=15),
            "TestAdvancedSettingsPIILearning/AdvancedSettingsPIILearning.json")

    def test_get_pii_learning_500(self, mock_appsec_client):
        """Test GetAdvancedSettingsPIILearning raises Error on 500."""
        _error(
            mock_appsec_client, "get_advanced_settings_pii_learning",
            models.GetAdvancedSettingsPIILearningRequest(
                config_id=43253, version=15),
            _err_500("Error fetching match target"))

    def test_update_pii_learning_200(self, mock_appsec_client):
        """Test UpdateAdvancedSettingsPIILearning on 200 OK."""
        _success(
            mock_appsec_client, "update_advanced_settings_pii_learning",
            models.UpdateAdvancedSettingsPIILearningRequest(
                config_id=43253, version=15),
            "TestAdvancedSettingsPIILearning/AdvancedSettingsPIILearning.json")

    def test_update_pii_learning_500(self, mock_appsec_client):
        """Test UpdateAdvancedSettingsPIILearning raises Error on 500."""
        _error(
            mock_appsec_client, "update_advanced_settings_pii_learning",
            models.UpdateAdvancedSettingsPIILearningRequest(
                config_id=43253, version=15),
            _err_500("Error creating zone"))


# ===================================================================
# TestAdvancedSettingsPragma  (mirrors advanced_settings_pragma_test.go)
# ===================================================================

class TestAdvancedSettingsPragma:
    """Pragma advanced settings tests."""

    def test_list_pragma_200(self, mock_appsec_client):
        """Test GetAdvancedSettingsPragma (list) on 200 OK."""
        _success(
            mock_appsec_client, "get_advanced_settings_pragma",
            models.GetAdvancedSettingsPragmaRequest(
                config_id=43253, version=15),
            "TestAdvancedSettingsPragma/AdvancedSettingsPragma.json")

    def test_list_pragma_500(self, mock_appsec_client):
        """Test GetAdvancedSettingsPragma raises Error on 500."""
        _error(
            mock_appsec_client, "get_advanced_settings_pragma",
            models.GetAdvancedSettingsPragmaRequest(
                config_id=43253, version=15),
            _err_500("Error fetching propertys"))

    def test_get_pragma_200(self, mock_appsec_client):
        """Test GetAdvancedSettingsPragma on 200 OK."""
        _success(
            mock_appsec_client, "get_advanced_settings_pragma",
            models.GetAdvancedSettingsPragmaRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            "TestAdvancedSettingsPragma/AdvancedSettingsPragma.json")

    def test_get_pragma_500(self, mock_appsec_client):
        """Test GetAdvancedSettingsPragma raises Error on 500."""
        _error(
            mock_appsec_client, "get_advanced_settings_pragma",
            models.GetAdvancedSettingsPragmaRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            _err_500("Error fetching match target"))

    def test_update_pragma_200(self, mock_appsec_client):
        """Test UpdateAdvancedSettingsPragma on 200 OK."""
        _success(
            mock_appsec_client, "update_advanced_settings_pragma",
            models.UpdateAdvancedSettingsPragmaRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            "TestAdvancedSettingsPragma/AdvancedSettingsPragma.json")

    def test_update_pragma_500(self, mock_appsec_client):
        """Test UpdateAdvancedSettingsPragma raises Error on 500."""
        _error(
            mock_appsec_client, "update_advanced_settings_pragma",
            models.UpdateAdvancedSettingsPragmaRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            _err_500("Error creating zone"))


# ===================================================================
# TestAdvancedSettingsPrefetch  (mirrors advanced_settings_prefetch_test.go)
# ===================================================================

class TestAdvancedSettingsPrefetch:
    """Prefetch advanced settings tests."""

    def test_list_prefetch_200(self, mock_appsec_client):
        """Test GetAdvancedSettingsPrefetch (list) on 200 OK."""
        _success(
            mock_appsec_client, "get_advanced_settings_prefetch",
            models.GetAdvancedSettingsPrefetchRequest(
                config_id=43253, version=15),
            "TestAdvancedSettingsPrefetch/AdvancedSettingsPrefetch.json")

    def test_list_prefetch_500(self, mock_appsec_client):
        """Test GetAdvancedSettingsPrefetch raises Error on 500."""
        _error(
            mock_appsec_client, "get_advanced_settings_prefetch",
            models.GetAdvancedSettingsPrefetchRequest(
                config_id=43253, version=15),
            _err_500("Error fetching propertys"))

    def test_get_prefetch_200(self, mock_appsec_client):
        """Test GetAdvancedSettingsPrefetch on 200 OK."""
        _success(
            mock_appsec_client, "get_advanced_settings_prefetch",
            models.GetAdvancedSettingsPrefetchRequest(
                config_id=43253, version=15),
            "TestAdvancedSettingsPrefetch/AdvancedSettingsPrefetch.json")

    def test_get_prefetch_500(self, mock_appsec_client):
        """Test GetAdvancedSettingsPrefetch raises Error on 500."""
        _error(
            mock_appsec_client, "get_advanced_settings_prefetch",
            models.GetAdvancedSettingsPrefetchRequest(
                config_id=43253, version=15),
            _err_500("Error fetching match target"))

    def test_update_prefetch_200(self, mock_appsec_client):
        """Test UpdateAdvancedSettingsPrefetch on 200 OK."""
        _success(
            mock_appsec_client, "update_advanced_settings_prefetch",
            models.UpdateAdvancedSettingsPrefetchRequest(
                config_id=43253, version=15),
            "TestAdvancedSettingsPrefetch/AdvancedSettingsPrefetch.json")

    def test_update_prefetch_500(self, mock_appsec_client):
        """Test UpdateAdvancedSettingsPrefetch raises Error on 500."""
        _error(
            mock_appsec_client, "update_advanced_settings_prefetch",
            models.UpdateAdvancedSettingsPrefetchRequest(
                config_id=43253, version=15),
            _err_500("Error creating zone"))


# ===================================================================
# TestAdvancedSettingsRequestBody
# (mirrors advanced_settings_request_body_test.go)
# ===================================================================

class TestAdvancedSettingsRequestBody:
    """Request body advanced settings tests."""

    def test_get_request_body_200(self, mock_appsec_client):
        """Test GetAdvancedSettingsRequestBody on 200 OK."""
        _success(
            mock_appsec_client, "get_advanced_settings_request_body",
            models.GetAdvancedSettingsRequestBodyRequest(
                config_id=43253, version=15),
            "TestAdvancedSettingsRequestBody/AdvancedSettingsRequestBody.json")

    def test_get_request_body_500(self, mock_appsec_client):
        """Test GetAdvancedSettingsRequestBody raises Error on 500."""
        _error(
            mock_appsec_client, "get_advanced_settings_request_body",
            models.GetAdvancedSettingsRequestBodyRequest(
                config_id=43253, version=15),
            _err_500("Error fetching match target"))

    def test_get_request_body_policy_200(self, mock_appsec_client):
        """Test GetAdvancedSettingsRequestBody per-policy on 200 OK."""
        _success(
            mock_appsec_client, "get_advanced_settings_request_body",
            models.GetAdvancedSettingsRequestBodyRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            "TestAdvancedSettingsRequestBody/AdvancedSettingsRequestBody.json")

    def test_get_request_body_policy_500(self, mock_appsec_client):
        """Test GetAdvancedSettingsRequestBody per-policy raises Error on 500."""
        _error(
            mock_appsec_client, "get_advanced_settings_request_body",
            models.GetAdvancedSettingsRequestBodyRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            _err_500("Error fetching match target"))

    def test_update_request_body_200(self, mock_appsec_client):
        """Test UpdateAdvancedSettingsRequestBody on 200 OK."""
        _success(
            mock_appsec_client, "update_advanced_settings_request_body",
            models.UpdateAdvancedSettingsRequestBodyRequest(
                config_id=43253, version=15),
            "TestAdvancedSettingsRequestBody/AdvancedSettingsRequestBody.json")

    def test_update_request_body_500(self, mock_appsec_client):
        """Test UpdateAdvancedSettingsRequestBody raises Error on 500."""
        _error(
            mock_appsec_client, "update_advanced_settings_request_body",
            models.UpdateAdvancedSettingsRequestBodyRequest(
                config_id=43253, version=15),
            _err_500("Error creating zone"))

    def test_update_request_body_policy_200(self, mock_appsec_client):
        """Test UpdateAdvancedSettingsRequestBody per-policy on 200 OK."""
        _success(
            mock_appsec_client, "update_advanced_settings_request_body",
            models.UpdateAdvancedSettingsRequestBodyRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            "TestAdvancedSettingsRequestBody/AdvancedSettingsRequestBody.json")

    def test_update_request_body_policy_500(self, mock_appsec_client):
        """Test UpdateAdvancedSettingsRequestBody per-policy raises Error on 500."""
        _error(
            mock_appsec_client, "update_advanced_settings_request_body",
            models.UpdateAdvancedSettingsRequestBodyRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            _err_500("Error creating zone"))

    def test_remove_request_body_200(self, mock_appsec_client):
        """Test RemoveAdvancedSettingsRequestBody on 200 OK."""
        _success(
            mock_appsec_client, "remove_advanced_settings_request_body",
            models.UpdateAdvancedSettingsRequestBodyRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            "TestAdvancedSettingsRequestBody/AdvancedSettingsRequestBody.json")

    def test_remove_request_body_500(self, mock_appsec_client):
        """Test RemoveAdvancedSettingsRequestBody raises Error on 500."""
        _error(
            mock_appsec_client, "remove_advanced_settings_request_body",
            models.UpdateAdvancedSettingsRequestBodyRequest(
                config_id=43253, version=15, policy_id="AAAA_81230"),
            _err_500("Error deleting match target"))
