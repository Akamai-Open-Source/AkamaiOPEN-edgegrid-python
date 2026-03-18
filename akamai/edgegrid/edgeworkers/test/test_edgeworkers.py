# pylint: disable=missing-function-docstring,too-many-lines,line-too-long
"""Unit tests for EdgeWorkers/EdgeKV API client.

Mirrors all 18 Go test files from pkg/edgeworkers/*_test.go.
Test scenarios, assertions, responseBody/responseHeaders values are
copied verbatim from Go test fixtures.
"""

import json
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.edgeworkers.edgeworkers import Client
from akamai.edgegrid.edgeworkers import models
from akamai.edgegrid.edgeworkers import errors as ew_errors
from akamai.edgegrid.edgeworkers.errors import (
    Error as EdgeWorkersError,
    parse_edgeworkers_error,
)
from akamai.edgegrid.errors import ErrStructValidation

# Import conftest helpers for fixtures and assertions
from akamai.edgegrid.edgeworkers.test.conftest import (
    make_mock_response, load_fixture, load_fixture_text,
    assert_request,
)


# ===================================================================
# Activations Tests  (mirrors activations_test.go)
# ===================================================================


class TestListActivations:
    """Tests for Client.list_activations — mirrors Go TestListActivations."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("list_activations.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.list_activations(
            models.ListActivationsRequest(edge_worker_id=42),
        )

        assert_request(mock_session, "GET",
                       "/edgeworkers/v1/ids/42/activations")
        assert len(result.activations) == 2
        act0 = result.activations[0]
        assert act0.edge_worker_id == 42
        assert act0.version == "2"
        assert act0.activation_id == 3
        assert act0.account_id == "B-M-1KQK3WU"
        assert act0.status == "PENDING"
        assert act0.network == "PRODUCTION"
        assert act0.created_by == "jdoe"
        assert act0.note == "activation note3"
        act1 = result.activations[1]
        assert act1.edge_worker_id == 42
        assert act1.version == "1"
        assert act1.activation_id == 1
        assert act1.network == "STAGING"
        assert act1.note == "activation note1"

    def test_200_ok_with_version_query(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("list_activations_version.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.list_activations(
            models.ListActivationsRequest(
                edge_worker_id=42, version="1"),
        )

        assert len(result.activations) == 1
        assert result.activations[0].version == "1"

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError) as exc_info:
            edgeworkers_client.list_activations(
                models.ListActivationsRequest(edge_worker_id=42),
            )

        err = exc_info.value
        assert err.status == 500
        assert err.error_code == "EW4303"

    def test_validation_missing_edge_worker_id(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.list_activations(
                models.ListActivationsRequest(),
            )
        assert "struct validation" in str(exc_info.value)


class TestGetActivation:
    """Tests for Client.get_activation — mirrors Go TestGetActivation."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("get_activation.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.get_activation(
            models.GetActivationRequest(
                edge_worker_id=42, activation_id=1),
        )

        assert_request(mock_session, "GET",
                       "/edgeworkers/v1/ids/42/activations/1")
        assert result.edge_worker_id == 42
        assert result.activation_id == 1
        assert result.version == "1"
        assert result.status == "IN_PROGRESS"
        assert result.network == "STAGING"

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.get_activation(
                models.GetActivationRequest(
                    edge_worker_id=42, activation_id=1),
            )

    def test_validation_missing_edge_worker_id(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation):
            edgeworkers_client.get_activation(
                models.GetActivationRequest(activation_id=1),
            )

    def test_validation_missing_activation_id(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation):
            edgeworkers_client.get_activation(
                models.GetActivationRequest(edge_worker_id=42),
            )


class TestActivateVersion:
    """Tests for Client.activate_version — mirrors Go TestActivateVersion."""

    def test_201_created(self, mock_session, edgeworkers_client):
        fixture = load_fixture("activate_version.json")
        mock_resp = make_mock_response(201, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.activate_version(
            models.ActivateVersionRequest(
                edge_worker_id=42,
                activate_version=models.ActivateVersion(
                    network="STAGING", version="1",
                    note="activation note1",
                ),
            ),
        )

        assert_request(
            mock_session, "POST",
            "/edgeworkers/v1/ids/42/activations",
            expected_body={
                "network": "STAGING", "version": "1",
                "note": "activation note1",
            },
        )
        assert result.activation_id == 1
        assert result.status == "PRESUBMIT"
        assert result.network == "STAGING"

    def test_201_created_no_note(self, mock_session, edgeworkers_client):
        fixture = load_fixture("activate_version_no_note.json")
        mock_resp = make_mock_response(201, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.activate_version(
            models.ActivateVersionRequest(
                edge_worker_id=42,
                activate_version=models.ActivateVersion(
                    network="STAGING", version="1",
                ),
            ),
        )

        assert_request(
            mock_session, "POST",
            "/edgeworkers/v1/ids/42/activations",
            expected_body={"network": "STAGING", "version": "1"},
        )
        assert result.activation_id == 1

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.activate_version(
                models.ActivateVersionRequest(
                    edge_worker_id=42,
                    activate_version=models.ActivateVersion(
                        network="STAGING", version="1",
                    ),
                ),
            )

    def test_validation_missing_edge_worker_id(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation):
            edgeworkers_client.activate_version(
                models.ActivateVersionRequest(
                    activate_version=models.ActivateVersion(
                        network="STAGING", version="1",
                    ),
                ),
            )

    def test_validation_missing_activate_version(self,
                                                  edgeworkers_client):
        with pytest.raises(ErrStructValidation):
            edgeworkers_client.activate_version(
                models.ActivateVersionRequest(edge_worker_id=42),
            )

    def test_validation_invalid_network(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.activate_version(
                models.ActivateVersionRequest(
                    edge_worker_id=42,
                    activate_version=models.ActivateVersion(
                        network="INVALID", version="1",
                    ),
                ),
            )
        assert "struct validation" in str(exc_info.value)


class TestCancelPendingActivation:
    """Tests for Client.cancel_pending_activation."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("cancel_activation.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.cancel_pending_activation(
            models.CancelActivationRequest(
                edge_worker_id=42, activation_id=1),
        )

        assert_request(mock_session, "DELETE",
                       "/edgeworkers/v1/ids/42/activations/1")
        assert result.status == "CANCELED"

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.cancel_pending_activation(
                models.CancelActivationRequest(
                    edge_worker_id=42, activation_id=1),
            )

    def test_validation_missing_edge_worker_id(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation):
            edgeworkers_client.cancel_pending_activation(
                models.CancelActivationRequest(activation_id=1),
            )

    def test_validation_missing_activation_id(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation):
            edgeworkers_client.cancel_pending_activation(
                models.CancelActivationRequest(edge_worker_id=42),
            )


# ===================================================================
# Contracts Tests  (mirrors contracts_test.go)
# ===================================================================


class TestListContracts:
    """Tests for Client.list_contracts — mirrors Go TestListContracts."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("list_contracts.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.list_contracts()

        assert_request(mock_session, "GET", "/edgeworkers/v1/contracts")
        assert result.contract_ids == ["1-599K", "B-M-28QYF3M"]

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError) as exc_info:
            edgeworkers_client.list_contracts()

        err = exc_info.value
        assert err.status == 500
        assert err.error_code == "EW4303"


# ===================================================================
# Deactivations Tests  (mirrors deactivations_test.go)
# ===================================================================


class TestListDeactivations:
    """Tests for Client.list_deactivations."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("list_deactivations.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.list_deactivations(
            models.ListDeactivationsRequest(edge_worker_id=42),
        )

        assert_request(mock_session, "GET",
                       "/edgeworkers/v1/ids/42/deactivations")
        assert len(result.deactivations) == 3
        d0 = result.deactivations[0]
        assert d0.edge_worker_id == 42
        assert d0.deactivation_id == 3
        assert d0.status == "PENDING"
        assert d0.network == "PRODUCTION"
        assert d0.note == "EdgeWorker ID 42 is no longer used in production."

    def test_200_ok_with_version_query(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("list_deactivations_version.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.list_deactivations(
            models.ListDeactivationsRequest(
                edge_worker_id=41, version="2"),
        )

        assert len(result.deactivations) == 2
        assert result.deactivations[0].edge_worker_id == 41

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.list_deactivations(
                models.ListDeactivationsRequest(edge_worker_id=42),
            )

    def test_validation_missing_edge_worker_id(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation):
            edgeworkers_client.list_deactivations(
                models.ListDeactivationsRequest(),
            )


class TestGetDeactivation:
    """Tests for Client.get_deactivation."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("get_deactivation.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.get_deactivation(
            models.GetDeactivationRequest(
                edge_worker_id=1, deactivation_id=2),
        )

        assert_request(mock_session, "GET",
                       "/edgeworkers/v1/ids/1/deactivations/2")
        assert result.edge_worker_id == 1
        assert result.deactivation_id == 2
        assert result.status == "COMPLETE"
        assert result.network == "PRODUCTION"
        assert result.note == "not used"

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.get_deactivation(
                models.GetDeactivationRequest(
                    edge_worker_id=1, deactivation_id=2),
            )

    def test_validation_missing_edge_worker_id(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation):
            edgeworkers_client.get_deactivation(
                models.GetDeactivationRequest(deactivation_id=2),
            )

    def test_validation_missing_deactivation_id(self,
                                                 edgeworkers_client):
        with pytest.raises(ErrStructValidation):
            edgeworkers_client.get_deactivation(
                models.GetDeactivationRequest(edge_worker_id=1),
            )


class TestDeactivateVersion:
    """Tests for Client.deactivate_version."""

    def test_201_created(self, mock_session, edgeworkers_client):
        fixture = load_fixture("deactivate_version.json")
        mock_resp = make_mock_response(201, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.deactivate_version(
            models.DeactivateVersionRequest(
                edge_worker_id=1,
                deactivate_version=models.DeactivateVersion(
                    network="PRODUCTION", version="123",
                    note="not used",
                ),
            ),
        )

        assert_request(
            mock_session, "POST",
            "/edgeworkers/v1/ids/1/deactivations",
            expected_body={
                "network": "PRODUCTION", "version": "123",
                "note": "not used",
            },
        )
        assert result.deactivation_id == 1
        assert result.status == "PRESUBMIT"

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.deactivate_version(
                models.DeactivateVersionRequest(
                    edge_worker_id=1,
                    deactivate_version=models.DeactivateVersion(
                        network="PRODUCTION", version="123",
                    ),
                ),
            )

    def test_validation_missing_edge_worker_id(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation):
            edgeworkers_client.deactivate_version(
                models.DeactivateVersionRequest(
                    deactivate_version=models.DeactivateVersion(
                        network="STAGING", version="1",
                    ),
                ),
            )

    def test_validation_missing_deactivate_version(self,
                                                    edgeworkers_client):
        with pytest.raises(ErrStructValidation):
            edgeworkers_client.deactivate_version(
                models.DeactivateVersionRequest(edge_worker_id=1),
            )

    def test_validation_invalid_network(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.deactivate_version(
                models.DeactivateVersionRequest(
                    edge_worker_id=1,
                    deactivate_version=models.DeactivateVersion(
                        network="INVALID", version="1",
                    ),
                ),
            )
        assert "struct validation" in str(exc_info.value)


# ===================================================================
# EdgeKV Access Tokens Tests  (mirrors edgekv_access_tokens_test.go)
# ===================================================================


class TestCreateEdgeKVAccessToken:
    """Tests for Client.create_edgekv_access_token."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("create_edgekv_access_token.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.create_edgekv_access_token(
            models.CreateEdgeKVAccessTokenRequest(
                allow_on_production=True,
                allow_on_staging=False,
                name="devexp-token-1",
                namespace_permissions={
                    "default": ["r", "w", "d"],
                    "devexp-jsmith-test": ["r", "w"],
                },
                restrict_to_edge_worker_ids=["1234", "5678"],
            ),
        )

        assert_request(mock_session, "POST", "/edgekv/v1/tokens",
                       expected_body={
                           "allowOnProduction": True,
                           "allowOnStaging": False,
                           "name": "devexp-token-1",
                           "namespacePermissions": {
                               "default": ["r", "w", "d"],
                               "devexp-jsmith-test": ["r", "w"],
                           },
                           "restrictToEdgeWorkerIds": ["1234", "5678"],
                       })
        assert result.name == "devexp-token-1"
        assert result.uuid == "1ab0e94b-c47e-568e-ab3e-1921ffcefe0c"
        assert result.allow_on_production is True
        assert result.allow_on_staging is False

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.create_edgekv_access_token(
                models.CreateEdgeKVAccessTokenRequest(
                    allow_on_production=True,
                    allow_on_staging=True,
                    name="test-token",
                    namespace_permissions={"default": ["r"]},
                ),
            )

    def test_validation_missing_name(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation):
            edgeworkers_client.create_edgekv_access_token(
                models.CreateEdgeKVAccessTokenRequest(
                    allow_on_production=True,
                    allow_on_staging=True,
                    namespace_permissions={"default": ["r"]},
                ),
            )

    def test_validation_missing_namespace_permissions(
            self, edgeworkers_client):
        with pytest.raises(ErrStructValidation):
            edgeworkers_client.create_edgekv_access_token(
                models.CreateEdgeKVAccessTokenRequest(
                    allow_on_production=True,
                    allow_on_staging=True,
                    name="test-token",
                ),
            )


class TestGetEdgeKVAccessToken:
    """Tests for Client.get_edgekv_access_token."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("get_edgekv_access_token.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.get_edgekv_access_token(
            models.GetEdgeKVAccessTokenRequest(
                token_name="devexp-token-1"),
        )

        assert_request(mock_session, "GET",
                       "/edgekv/v1/tokens/devexp-token-1")
        assert result.name == "devexp-token-1"
        assert result.uuid == "10b0e94b-c47e-568e-ab3e-1921ffcefe0c"

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.get_edgekv_access_token(
                models.GetEdgeKVAccessTokenRequest(
                    token_name="devexp-token-1"),
            )

    def test_validation_missing_token_name(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation):
            edgeworkers_client.get_edgekv_access_token(
                models.GetEdgeKVAccessTokenRequest(),
            )


class TestListEdgeKVAccessTokens:
    """Tests for Client.list_edgekv_access_tokens."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("list_edgekv_access_tokens.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.list_edgekv_access_tokens(
            models.ListEdgeKVAccessTokensRequest(
                include_expired=False),
        )

        assert len(result.tokens) == 2
        assert result.tokens[0].name == "my_token"
        assert result.tokens[1].name == "token1"

    def test_200_ok_with_include_expired(self, mock_session,
                                         edgeworkers_client):
        fixture = load_fixture(
            "list_edgekv_access_tokens_include_expired.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.list_edgekv_access_tokens(
            models.ListEdgeKVAccessTokensRequest(
                include_expired=True),
        )

        assert len(result.tokens) == 2

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.list_edgekv_access_tokens(
                models.ListEdgeKVAccessTokensRequest(
                    include_expired=False),
            )


class TestDeleteEdgeKVAccessToken:
    """Tests for Client.delete_edgekv_access_token."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("delete_edgekv_access_token.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.delete_edgekv_access_token(
            models.DeleteEdgeKVAccessTokenRequest(
                token_name="devexp-token-3"),
        )

        assert_request(mock_session, "DELETE",
                       "/edgekv/v1/tokens/devexp-token-3")
        assert result.name == "devexp-token-3"
        assert result.uuid == "cc0a9045-e654-5f17-9b37-6ab6e565803f"

    def test_validation_missing_token_name(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation):
            edgeworkers_client.delete_edgekv_access_token(
                models.DeleteEdgeKVAccessTokenRequest(),
            )


# ===================================================================
# EdgeKV Groups Tests  (mirrors edgekv_groups_test.go)
# ===================================================================


class TestListGroupsWithinNamespace:
    """Tests for Client.list_groups_within_namespace."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("list_groups_within_namespace.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.list_groups_within_namespace(
            models.ListGroupsWithinNamespaceRequest(
                network="staging", namespace_id="test_namespace"),
        )

        assert_request(
            mock_session, "GET",
            "/edgekv/v1/networks/staging/namespaces"
            "/test_namespace/groups",
        )
        assert result == ["test_group_name"]

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        error_body = {
            "type": "https://problems.luna-dev.akamaiapis.net/-/resource-impl/forward-origin-error",
            "title": "Server Error",
            "status": 500,
            "instance": "host_name/edgeworkers/v1/groups",
            "method": "GET",
            "serverIp": "104.81.220.111",
            "clientIp": "89.64.55.111",
            "requestId": "a73affa111",
            "requestTime": "2021-12-06T10:27:11Z",
        }
        mock_resp = make_mock_response(500, body=error_body)
        mock_resp.text = json.dumps(error_body)
        mock_session.exec.return_value = (mock_resp, error_body)

        with pytest.raises(EdgeWorkersError) as exc_info:
            edgeworkers_client.list_groups_within_namespace(
                models.ListGroupsWithinNamespaceRequest(
                    network="staging",
                    namespace_id="test_namespace"),
            )

        err = exc_info.value
        assert err.status == 500
        assert err.method == "GET"

    def test_validation_missing_namespace_id(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.list_groups_within_namespace(
                models.ListGroupsWithinNamespaceRequest(
                    network="staging"),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_network(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.list_groups_within_namespace(
                models.ListGroupsWithinNamespaceRequest(
                    namespace_id="test_namespace"),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_both(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.list_groups_within_namespace(
                models.ListGroupsWithinNamespaceRequest(),
            )
        assert "struct validation" in str(exc_info.value)


# ===================================================================
# EdgeKV Initialize Tests  (mirrors edgekv_initialize_test.go)
# ===================================================================


class TestInitializeEdgeKV:
    """Tests for Client.initialize_edgekv."""

    def test_201_created(self, mock_session, edgeworkers_client):
        fixture = load_fixture("initialize_edgekv.json")
        mock_resp = make_mock_response(201, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.initialize_edgekv()

        assert_request(mock_session, "PUT", "/edgekv/v1/initialize")
        assert result.account_status == "INITIALIZED"
        assert result.cpcode == "123456"
        assert result.production_status == "INITIALIZED"
        assert result.staging_status == "INITIALIZED"

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        error_body = {
            "type": "https://learn.akamai.com",
            "title": "Internal Server Error",
            "detail": "An internal error occurred.",
            "instance": "/edgeKV/error-instances/abc",
            "status": 500,
            "errorCode": "EKV_0000",
            "additionalDetail": {"requestId": "test_req_id"},
        }
        mock_resp = make_mock_response(500, body=error_body)
        mock_resp.text = json.dumps(error_body)
        mock_session.exec.return_value = (mock_resp, error_body)

        with pytest.raises(EdgeWorkersError) as exc_info:
            edgeworkers_client.initialize_edgekv()

        err = exc_info.value
        assert err.status == 500

    def test_503_service_unavailable(self, mock_session,
                                     edgeworkers_client):
        error_body = {
            "type": "https://learn.akamai.com",
            "title": "Service Unavailable",
            "detail": "Service is temporarily unavailable.",
            "instance": "/edgeKV/error-instances/abc",
            "status": 503,
            "errorCode": "EKV_0000",
            "additionalDetail": {"requestId": "test_req_id"},
        }
        mock_resp = make_mock_response(503, body=error_body)
        mock_resp.text = json.dumps(error_body)
        mock_session.exec.return_value = (mock_resp, error_body)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.initialize_edgekv()


class TestGetEdgeKVInitializationStatus:
    """Tests for Client.get_edgekv_initialization_status."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("get_edgekv_initialization_status.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.get_edgekv_initialization_status()

        assert_request(mock_session, "GET", "/edgekv/v1/initialize")
        assert result.account_status == "INITIALIZED"
        assert result.cpcode == "123456"

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        error_body = {
            "type": "https://learn.akamai.com",
            "title": "Internal Server Error",
            "detail": "An internal error occurred.",
            "instance": "/edgeKV/error-instances/abc",
            "status": 500,
            "errorCode": "EKV_0000",
            "additionalDetail": {"requestId": "test_req_id"},
        }
        mock_resp = make_mock_response(500, body=error_body)
        mock_resp.text = json.dumps(error_body)
        mock_session.exec.return_value = (mock_resp, error_body)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.get_edgekv_initialization_status()


# ===================================================================
# EdgeKV Items Tests  (mirrors edgekv_items_test.go)
# ===================================================================


class TestListItems:
    """Tests for Client.list_items."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("list_items.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.list_items(
            models.ListItemsRequest(
                items_request_params=models.ItemsRequestParams(
                    network="staging",
                    namespace_id="marketing",
                    group_id="countries",
                ),
            ),
        )

        assert_request(
            mock_session, "GET",
            "/edgekv/v1/networks/staging/namespaces"
            "/marketing/groups/countries",
        )
        assert result == ["US", "DE"]

    def test_validation_incorrect_network(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.list_items(
                models.ListItemsRequest(
                    items_request_params=models.ItemsRequestParams(
                        network="stag",
                        namespace_id="marketing",
                        group_id="countries",
                    ),
                ),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_network(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.list_items(
                models.ListItemsRequest(
                    items_request_params=models.ItemsRequestParams(
                        namespace_id="marketing",
                        group_id="countries",
                    ),
                ),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_namespace_id(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.list_items(
                models.ListItemsRequest(
                    items_request_params=models.ItemsRequestParams(
                        network="staging",
                        group_id="countries",
                    ),
                ),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_group_id(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.list_items(
                models.ListItemsRequest(
                    items_request_params=models.ItemsRequestParams(
                        network="staging",
                        namespace_id="marketing",
                    ),
                ),
            )
        assert "struct validation" in str(exc_info.value)

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        error_body = {
            "type": "https://learn.akamai.com",
            "title": "Internal Server Error",
            "detail": "An internal error occurred.",
            "instance": "/edgeKV/error-instances/abc",
            "status": 500,
            "errorCode": "EKV_0000",
            "additionalDetail": {"requestId": "test_req_id"},
        }
        mock_resp = make_mock_response(500, body=error_body)
        mock_resp.text = json.dumps(error_body)
        mock_session.exec.return_value = (mock_resp, error_body)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.list_items(
                models.ListItemsRequest(
                    items_request_params=models.ItemsRequestParams(
                        network="staging",
                        namespace_id="marketing",
                        group_id="countries",
                    ),
                ),
            )


class TestGetItem:
    """Tests for Client.get_item."""

    def test_200_ok_text(self, mock_session, edgeworkers_client):
        text_content = load_fixture_text("get_item_text.txt")
        mock_resp = make_mock_response(200)
        mock_resp.text = text_content
        mock_session.exec.return_value = (mock_resp, None)

        result = edgeworkers_client.get_item(
            models.GetItemRequest(
                item_id="key1",
                items_request_params=models.ItemsRequestParams(
                    network="staging",
                    namespace_id="marketing",
                    group_id="countries",
                ),
            ),
        )

        assert_request(
            mock_session, "GET",
            "/edgekv/v1/networks/staging/namespaces"
            "/marketing/groups/countries/items/key1",
        )
        assert result == text_content

    def test_200_ok_json(self, mock_session, edgeworkers_client):
        fixture = load_fixture("get_item_json.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, None)

        result = edgeworkers_client.get_item(
            models.GetItemRequest(
                item_id="key1",
                items_request_params=models.ItemsRequestParams(
                    network="staging",
                    namespace_id="marketing",
                    group_id="countries",
                ),
            ),
        )
        assert result == json.dumps(fixture)

    def test_validation_missing_item_id(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.get_item(
                models.GetItemRequest(
                    items_request_params=models.ItemsRequestParams(
                        network="staging",
                        namespace_id="marketing",
                        group_id="countries",
                    ),
                ),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_incorrect_network(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.get_item(
                models.GetItemRequest(
                    item_id="key1",
                    items_request_params=models.ItemsRequestParams(
                        network="stag",
                        namespace_id="marketing",
                        group_id="countries",
                    ),
                ),
            )
        assert "struct validation" in str(exc_info.value)

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        error_body = {
            "type": "https://learn.akamai.com",
            "title": "Internal Server Error",
            "detail": "An internal error occurred.",
            "instance": "/edgeKV/error-instances/abc",
            "status": 500,
            "errorCode": "EKV_0000",
            "additionalDetail": {"requestId": "test_req_id"},
        }
        mock_resp = make_mock_response(500, body=error_body)
        mock_resp.text = json.dumps(error_body)
        mock_session.exec.return_value = (mock_resp, error_body)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.get_item(
                models.GetItemRequest(
                    item_id="key1",
                    items_request_params=models.ItemsRequestParams(
                        network="staging",
                        namespace_id="marketing",
                        group_id="countries",
                    ),
                ),
            )


class TestUpsertItem:
    """Tests for Client.upsert_item."""

    def test_200_ok_string_value(self, mock_session, edgeworkers_client):
        text_content = load_fixture_text("upsert_item.txt")
        mock_resp = make_mock_response(200)
        mock_resp.text = text_content
        mock_session.exec.return_value = (mock_resp, None)

        result = edgeworkers_client.upsert_item(
            models.UpsertItemRequest(
                item_id="key1",
                item_data="English",
                items_request_params=models.ItemsRequestParams(
                    network="staging",
                    namespace_id="marketing",
                    group_id="countries",
                ),
            ),
        )

        assert_request(
            mock_session, "PUT",
            "/edgekv/v1/networks/staging/namespaces"
            "/marketing/groups/countries/items/key1",
        )
        assert result == text_content

    def test_200_ok_json_value(self, mock_session, edgeworkers_client):
        text_content = load_fixture_text("upsert_item.txt")
        mock_resp = make_mock_response(200)
        mock_resp.text = text_content
        mock_session.exec.return_value = (mock_resp, None)

        result = edgeworkers_client.upsert_item(
            models.UpsertItemRequest(
                item_id="key1",
                item_data='{"country": "US"}',
                items_request_params=models.ItemsRequestParams(
                    network="staging",
                    namespace_id="marketing",
                    group_id="countries",
                ),
            ),
        )

        assert_request(
            mock_session, "PUT",
            "/edgekv/v1/networks/staging/namespaces"
            "/marketing/groups/countries/items/key1",
        )
        assert result == text_content

    def test_validation_missing_item_id(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.upsert_item(
                models.UpsertItemRequest(
                    item_data="English",
                    items_request_params=models.ItemsRequestParams(
                        network="staging",
                        namespace_id="marketing",
                        group_id="countries",
                    ),
                ),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_item_data(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.upsert_item(
                models.UpsertItemRequest(
                    item_id="key1",
                    items_request_params=models.ItemsRequestParams(
                        network="staging",
                        namespace_id="marketing",
                        group_id="countries",
                    ),
                ),
            )
        assert "struct validation" in str(exc_info.value)

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        error_body = {
            "type": "https://learn.akamai.com",
            "title": "Internal Server Error",
            "detail": "An internal error occurred.",
            "instance": "/edgeKV/error-instances/abc",
            "status": 500,
            "errorCode": "EKV_0000",
            "additionalDetail": {"requestId": "test_req_id"},
        }
        mock_resp = make_mock_response(500, body=error_body)
        mock_resp.text = json.dumps(error_body)
        mock_session.exec.return_value = (mock_resp, error_body)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.upsert_item(
                models.UpsertItemRequest(
                    item_id="key1",
                    item_data="English",
                    items_request_params=models.ItemsRequestParams(
                        network="staging",
                        namespace_id="marketing",
                        group_id="countries",
                    ),
                ),
            )


class TestDeleteItem:
    """Tests for Client.delete_item."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        text_content = load_fixture_text("delete_item.txt")
        mock_resp = make_mock_response(200)
        mock_resp.text = text_content
        mock_session.exec.return_value = (mock_resp, None)

        result = edgeworkers_client.delete_item(
            models.DeleteItemRequest(
                item_id="key1",
                items_request_params=models.ItemsRequestParams(
                    network="staging",
                    namespace_id="marketing",
                    group_id="countries",
                ),
            ),
        )

        assert_request(
            mock_session, "DELETE",
            "/edgekv/v1/networks/staging/namespaces"
            "/marketing/groups/countries/items/key1",
        )
        assert result == text_content

    def test_validation_missing_item_id(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.delete_item(
                models.DeleteItemRequest(
                    items_request_params=models.ItemsRequestParams(
                        network="staging",
                        namespace_id="marketing",
                        group_id="countries",
                    ),
                ),
            )
        assert "struct validation" in str(exc_info.value)

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        error_body = {
            "type": "https://learn.akamai.com",
            "title": "Internal Server Error",
            "detail": "An internal error occurred.",
            "instance": "/edgeKV/error-instances/abc",
            "status": 500,
            "errorCode": "EKV_0000",
            "additionalDetail": {"requestId": "test_req_id"},
        }
        mock_resp = make_mock_response(500, body=error_body)
        mock_resp.text = json.dumps(error_body)
        mock_session.exec.return_value = (mock_resp, error_body)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.delete_item(
                models.DeleteItemRequest(
                    item_id="key1",
                    items_request_params=models.ItemsRequestParams(
                        network="staging",
                        namespace_id="marketing",
                        group_id="countries",
                    ),
                ),
            )


# ===================================================================
# EdgeKV Namespaces Tests  (mirrors edgekv_namespaces_test.go)
# ===================================================================


class TestListEdgeKVNamespaces:
    """Tests for Client.list_edgekv_namespaces."""

    def test_200_ok_production(self, mock_session, edgeworkers_client):
        fixture = load_fixture("list_namespaces.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.list_edgekv_namespaces(
            models.ListEdgeKVNamespacesRequest(network="production"),
        )

        assert_request(
            mock_session, "GET",
            "/edgekv/v1/networks/production/namespaces",
        )
        assert len(result.namespaces) == 3
        assert result.namespaces[0].name == "testNs_1"
        assert result.namespaces[1].name == "testNs_2"
        assert result.namespaces[2].name == "testNs_3"

    def test_200_ok_staging(self, mock_session, edgeworkers_client):
        fixture = load_fixture("list_namespaces.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.list_edgekv_namespaces(
            models.ListEdgeKVNamespacesRequest(network="staging"),
        )

        assert_request(
            mock_session, "GET",
            "/edgekv/v1/networks/staging/namespaces",
        )
        assert len(result.namespaces) == 3

    def test_200_ok_details_on(self, mock_session, edgeworkers_client):
        fixture = load_fixture("list_namespaces_details.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.list_edgekv_namespaces(
            models.ListEdgeKVNamespacesRequest(
                network="production", details=True),
        )

        assert_request(
            mock_session, "GET",
            "/edgekv/v1/networks/production/namespaces",
        )
        assert len(result.namespaces) == 3
        assert result.namespaces[0].name == "testNs_1"
        assert result.namespaces[0].geo_location == "EU"
        assert result.namespaces[0].retention == 0
        assert result.namespaces[1].name == "testNs_2"
        assert result.namespaces[1].retention == 86400
        assert result.namespaces[1].geo_location == "JP"
        assert result.namespaces[1].group_id == 123
        assert result.namespaces[2].name == "testNs_3"
        assert result.namespaces[2].retention == 315360000
        assert result.namespaces[2].geo_location == "US"
        assert result.namespaces[2].group_id == 234

    def test_validation_invalid_network(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.list_edgekv_namespaces(
                models.ListEdgeKVNamespacesRequest(network="invalid"),
            )
        assert "struct validation" in str(exc_info.value)

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        error_body = {
            "type": "https://learn.akamai.com",
            "title": "Internal Server Error",
            "detail": "An internal error occurred.",
            "instance": "/edgeKV/error-instances/abc",
            "status": 500,
            "errorCode": "EKV_0000",
            "additionalDetail": {"requestId": "test_req_id"},
        }
        mock_resp = make_mock_response(500, body=error_body)
        mock_resp.text = json.dumps(error_body)
        mock_session.exec.return_value = (mock_resp, error_body)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.list_edgekv_namespaces(
                models.ListEdgeKVNamespacesRequest(network="production"),
            )


class TestGetEdgeKVNamespace:
    """Tests for Client.get_edgekv_namespace."""

    def test_200_ok_production(self, mock_session, edgeworkers_client):
        fixture = load_fixture("get_namespace.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.get_edgekv_namespace(
            models.GetEdgeKVNamespaceRequest(
                network="production", name="testNs"),
        )

        assert_request(
            mock_session, "GET",
            "/edgekv/v1/networks/production/namespaces/testNs",
        )
        assert result.name == "testNs"
        assert result.retention == 86400
        assert result.geo_location == "EU"
        assert result.namespace_status == "READY"
        assert result.group_id == 123456

    def test_200_ok_staging(self, mock_session, edgeworkers_client):
        fixture = load_fixture("get_namespace_staging.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.get_edgekv_namespace(
            models.GetEdgeKVNamespaceRequest(
                network="staging", name="testNs"),
        )

        assert_request(
            mock_session, "GET",
            "/edgekv/v1/networks/staging/namespaces/testNs",
        )
        assert result.name == "testNs"
        assert result.geo_location == "US"

    def test_200_ok_deleting(self, mock_session, edgeworkers_client):
        fixture = load_fixture("get_namespace_deleting.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.get_edgekv_namespace(
            models.GetEdgeKVNamespaceRequest(
                network="production", name="testNs"),
        )

        assert result.name == "testNs"
        assert result.namespace_status == "DELETING"
        assert result.scheduled_delete_time == \
            "2025-06-12T10:38:33.779Z"

    def test_validation_missing_network(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.get_edgekv_namespace(
                models.GetEdgeKVNamespaceRequest(name="testNs"),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_name(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.get_edgekv_namespace(
                models.GetEdgeKVNamespaceRequest(network="staging"),
            )
        assert "struct validation" in str(exc_info.value)

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        error_body = {
            "type": "https://learn.akamai.com",
            "title": "Internal Server Error",
            "detail": "An internal error occurred.",
            "instance": "/edgeKV/error-instances/abc",
            "status": 500,
            "errorCode": "EKV_0000",
            "additionalDetail": {"requestId": "test_req_id"},
        }
        mock_resp = make_mock_response(500, body=error_body)
        mock_resp.text = json.dumps(error_body)
        mock_session.exec.return_value = (mock_resp, error_body)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.get_edgekv_namespace(
                models.GetEdgeKVNamespaceRequest(
                    network="production", name="testNs"),
            )


class TestCreateEdgeKVNamespace:
    """Tests for Client.create_edgekv_namespace."""

    def test_200_ok_production(self, mock_session, edgeworkers_client):
        fixture = load_fixture("create_namespace.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.create_edgekv_namespace(
            models.CreateEdgeKVNamespaceRequest(
                network="production",
                namespace_request=models.NamespaceRequest(
                    name="testNs",
                    geo_location="EU",
                    retention=0,
                    group_id=0,
                ),
            ),
        )

        assert_request(
            mock_session, "POST",
            "/edgekv/v1/networks/production/namespaces",
        )
        assert result.name == "testNs"
        assert result.geo_location == "EU"

    def test_200_ok_staging(self, mock_session, edgeworkers_client):
        fixture = load_fixture("create_namespace_staging.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.create_edgekv_namespace(
            models.CreateEdgeKVNamespaceRequest(
                network="staging",
                namespace_request=models.NamespaceRequest(
                    name="testNs",
                    geo_location="US",
                    retention=86400,
                    group_id=123,
                ),
            ),
        )

        assert_request(
            mock_session, "POST",
            "/edgekv/v1/networks/staging/namespaces",
        )
        assert result.name == "testNs"
        assert result.geo_location == "US"
        assert result.retention == 86400
        assert result.group_id == 123

    def test_validation_missing_network(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.create_edgekv_namespace(
                models.CreateEdgeKVNamespaceRequest(
                    namespace_request=models.NamespaceRequest(
                        name="testNs",
                        geo_location="EU",
                    ),
                ),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_namespace_request(self,
                                                   edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.create_edgekv_namespace(
                models.CreateEdgeKVNamespaceRequest(network="staging"),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_name(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.create_edgekv_namespace(
                models.CreateEdgeKVNamespaceRequest(
                    network="staging",
                    namespace_request=models.NamespaceRequest(
                        geo_location="EU",
                    ),
                ),
            )
        assert "struct validation" in str(exc_info.value)

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        error_body = {
            "type": "https://learn.akamai.com",
            "title": "Internal Server Error",
            "detail": "An internal error occurred.",
            "instance": "/edgeKV/error-instances/abc",
            "status": 500,
            "errorCode": "EKV_0000",
            "additionalDetail": {"requestId": "test_req_id"},
        }
        mock_resp = make_mock_response(500, body=error_body)
        mock_resp.text = json.dumps(error_body)
        mock_session.exec.return_value = (mock_resp, error_body)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.create_edgekv_namespace(
                models.CreateEdgeKVNamespaceRequest(
                    network="production",
                    namespace_request=models.NamespaceRequest(
                        name="testNs",
                        geo_location="EU",
                        retention=0,
                        group_id=0,
                    ),
                ),
            )


class TestUpdateEdgeKVNamespace:
    """Tests for Client.update_edgekv_namespace."""

    def test_200_ok_production(self, mock_session, edgeworkers_client):
        fixture = load_fixture("update_namespace.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.update_edgekv_namespace(
            models.UpdateEdgeKVNamespaceRequest(
                network="production",
                update_namespace=models.UpdateNamespace(
                    name="testNs",
                    retention=86410,
                    group_id=123456,
                ),
            ),
        )

        assert_request(
            mock_session, "PUT",
            "/edgekv/v1/networks/production/namespaces/testNs",
        )
        assert result.name == "testNs"
        assert result.retention == 86410
        assert result.group_id == 123456
        assert result.namespace_status == "READY"

    def test_200_ok_staging(self, mock_session, edgeworkers_client):
        fixture = load_fixture("update_namespace_staging.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.update_edgekv_namespace(
            models.UpdateEdgeKVNamespaceRequest(
                network="staging",
                update_namespace=models.UpdateNamespace(
                    name="testNs",
                    retention=86410,
                    group_id=123456,
                ),
            ),
        )

        assert_request(
            mock_session, "PUT",
            "/edgekv/v1/networks/staging/namespaces/testNs",
        )
        assert result.name == "testNs"

    def test_validation_missing_network(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.update_edgekv_namespace(
                models.UpdateEdgeKVNamespaceRequest(
                    update_namespace=models.UpdateNamespace(
                        name="testNs"),
                ),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_update_namespace(self,
                                                  edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.update_edgekv_namespace(
                models.UpdateEdgeKVNamespaceRequest(
                    network="production"),
            )
        assert "struct validation" in str(exc_info.value)

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        error_body = {
            "type": "https://learn.akamai.com",
            "title": "Internal Server Error",
            "detail": "An internal error occurred.",
            "instance": "/edgeKV/error-instances/abc",
            "status": 500,
            "errorCode": "EKV_0000",
            "additionalDetail": {"requestId": "test_req_id"},
        }
        mock_resp = make_mock_response(500, body=error_body)
        mock_resp.text = json.dumps(error_body)
        mock_session.exec.return_value = (mock_resp, error_body)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.update_edgekv_namespace(
                models.UpdateEdgeKVNamespaceRequest(
                    network="production",
                    update_namespace=models.UpdateNamespace(
                        name="testNs",
                        retention=86410,
                        group_id=0,
                    ),
                ),
            )


class TestDeleteEdgeKVNamespace:
    """Tests for Client.delete_edgekv_namespace."""

    def test_200_ok_synchronous(self, mock_session, edgeworkers_client):
        text_body = json.dumps({
            "operationPerformed": "DELETED",
            "description": (
                "Namespace 'testNs' was successfully deleted."
            ),
            "id": "1234567",
        })
        mock_resp = make_mock_response(200)
        mock_resp.text = text_body
        mock_session.exec.return_value = (mock_resp, None)

        edgeworkers_client.delete_edgekv_namespace(
            models.DeleteEdgeKVNamespaceRequest(
                network="production", name="testNs", sync=True),
        )

        assert_request(
            mock_session, "DELETE",
            "/edgekv/v1/networks/production/namespaces/testNs",
        )

    def test_202_ok_asynchronous(self, mock_session,
                                  edgeworkers_client):
        text_body = json.dumps({
            "scheduledDeleteTime": "2025-05-08T14:16:05.350Z",
        })
        mock_resp = make_mock_response(202)
        mock_resp.text = text_body
        mock_session.exec.return_value = (mock_resp, None)

        result = edgeworkers_client.delete_edgekv_namespace(
            models.DeleteEdgeKVNamespaceRequest(
                network="production", name="testNs", sync=False),
        )

        assert_request(
            mock_session, "DELETE",
            "/edgekv/v1/networks/production/namespaces/testNs",
        )
        assert result.scheduled_delete_time == \
            "2025-05-08T14:16:05.350Z"

    def test_validation_missing_network(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.delete_edgekv_namespace(
                models.DeleteEdgeKVNamespaceRequest(name="testNs"),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_name(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.delete_edgekv_namespace(
                models.DeleteEdgeKVNamespaceRequest(
                    network="production"),
            )
        assert "struct validation" in str(exc_info.value)

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        error_body = {
            "type": "https://learn.akamai.com",
            "title": "Internal Server Error",
            "detail": "An internal error occurred.",
            "instance": "/edgeKV/error-instances/abc",
            "status": 500,
            "errorCode": "EKV_0000",
            "additionalDetail": {"requestId": "test_req_id"},
        }
        mock_resp = make_mock_response(500, body=error_body)
        mock_resp.text = json.dumps(error_body)
        mock_session.exec.return_value = (mock_resp, error_body)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.delete_edgekv_namespace(
                models.DeleteEdgeKVNamespaceRequest(
                    network="production",
                    name="testNs",
                    sync=True,
                ),
            )


class TestGetScheduledDeleteTime:
    """Tests for Client.get_namespace_scheduled_delete_time."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("get_scheduled_delete_time.json")
        mock_resp = make_mock_response(
            200, body=fixture,
            headers={"Retry-After": "120"},
        )
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.get_namespace_scheduled_delete_time(
            models.GetScheduledDeleteTimeRequest(
                network="production", name="testNs"),
        )

        assert_request(
            mock_session, "GET",
            "/edgekv/v1/networks/production/namespaces"
            "/testNs/status/scheduled-delete",
        )
        assert result.scheduled_delete_time == \
            "2025-06-05T09:58:37.565Z"
        assert result.retry_after_header == "120"

    def test_validation_missing_network(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.get_namespace_scheduled_delete_time(
                models.GetScheduledDeleteTimeRequest(name="testNs"),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_name(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.get_namespace_scheduled_delete_time(
                models.GetScheduledDeleteTimeRequest(
                    network="production"),
            )
        assert "struct validation" in str(exc_info.value)

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        error_body = {
            "type": "https://learn.akamai.com",
            "title": "Internal Server Error",
            "detail": "An internal error occurred.",
            "instance": "/edgeKV/error-instances/abc",
            "status": 500,
            "errorCode": "EKV_0000",
            "additionalDetail": {"requestId": "test_req_id"},
        }
        mock_resp = make_mock_response(500, body=error_body)
        mock_resp.text = json.dumps(error_body)
        mock_session.exec.return_value = (mock_resp, error_body)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.get_namespace_scheduled_delete_time(
                models.GetScheduledDeleteTimeRequest(
                    network="production", name="testNs"),
            )


class TestRescheduleNamespaceDelete:
    """Tests for Client.reschedule_namespace_delete."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("reschedule_namespace_delete.json")
        mock_resp = make_mock_response(
            200, body=fixture,
            headers={"Retry-After": "300"},
        )
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.reschedule_namespace_delete(
            models.RescheduleNamespaceDeleteRequest(
                network="production",
                name="testNs",
                body=models.ScheduledDeleteTimeRequest(
                    scheduled_delete_time=(
                        "2025-06-05T19:58:37.565Z"
                    ),
                ),
            ),
        )

        assert_request(
            mock_session, "PUT",
            "/edgekv/v1/networks/production/namespaces"
            "/testNs/status/scheduled-delete",
        )
        assert result.scheduled_delete_time.scheduled_delete_time \
            == "2025-06-05T19:58:37.565Z"
        assert result.retry_after_header == "300"

    def test_validation_missing_network(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.reschedule_namespace_delete(
                models.RescheduleNamespaceDeleteRequest(
                    name="testNs",
                    body=models.ScheduledDeleteTimeRequest(
                        scheduled_delete_time="2025-06-05T19:58:37Z"),
                ),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_name(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.reschedule_namespace_delete(
                models.RescheduleNamespaceDeleteRequest(
                    network="production",
                    body=models.ScheduledDeleteTimeRequest(
                        scheduled_delete_time="2025-06-05T19:58:37Z"),
                ),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_body(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.reschedule_namespace_delete(
                models.RescheduleNamespaceDeleteRequest(
                    network="production", name="testNs"),
            )
        assert "struct validation" in str(exc_info.value)


class TestCancelScheduledNamespaceDelete:
    """Tests for Client.cancel_scheduled_namespace_delete."""

    def test_204_no_content(self, mock_session, edgeworkers_client):
        mock_resp = make_mock_response(204)
        mock_session.exec.return_value = (mock_resp, None)

        result = edgeworkers_client.cancel_scheduled_namespace_delete(
            models.CancelScheduledNamespaceDeleteRequest(
                network="production", name="testNs"),
        )

        assert_request(
            mock_session, "DELETE",
            "/edgekv/v1/networks/production/namespaces"
            "/testNs/status/scheduled-delete",
        )
        assert result is None

    def test_validation_missing_network(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.cancel_scheduled_namespace_delete(
                models.CancelScheduledNamespaceDeleteRequest(
                    name="testNs"),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_name(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.cancel_scheduled_namespace_delete(
                models.CancelScheduledNamespaceDeleteRequest(
                    network="production"),
            )
        assert "struct validation" in str(exc_info.value)


# ===================================================================
# EdgeWorker ID Tests  (mirrors edgeworker_id_test.go)
# ===================================================================


class TestGetEdgeWorkerID:
    """Tests for Client.get_edge_worker_id."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("get_edgeworker_id.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.get_edge_worker_id(
            models.GetEdgeWorkerIDRequest(edge_worker_id=12345),
        )

        assert_request(
            mock_session, "GET", "/edgeworkers/v1/ids/12345",
        )
        assert result.edge_worker_id == 12345
        assert result.name == "EdgeWorkerID"
        assert result.account_id == "B-123-WNKA6P"
        assert result.group_id == 12345
        assert result.resource_tier_id == 123
        assert result.created_by == "jbond"
        assert result.created_time == "2021-04-19T07:08:37Z"
        assert result.last_modified_by == "jbond"
        assert result.last_modified_time == "2021-04-19T07:08:37Z"

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError) as exc_info:
            edgeworkers_client.get_edge_worker_id(
                models.GetEdgeWorkerIDRequest(edge_worker_id=12345),
            )
        assert exc_info.value.status == 500

    def test_403_forbidden(self, mock_session, edgeworkers_client):
        fixture = load_fixture("error_403_forbidden.json")
        mock_resp = make_mock_response(403, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError) as exc_info:
            edgeworkers_client.get_edge_worker_id(
                models.GetEdgeWorkerIDRequest(edge_worker_id=12345),
            )
        assert exc_info.value.status == 403

    def test_validation_missing_edge_worker_id(self,
                                                edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.get_edge_worker_id(
                models.GetEdgeWorkerIDRequest(),
            )
        assert "struct validation" in str(exc_info.value)


class TestListEdgeWorkersID:
    """Tests for Client.list_edge_workers_id."""

    def test_200_ok_no_query(self, mock_session, edgeworkers_client):
        fixture = load_fixture("list_edgeworkers_id.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.list_edge_workers_id(
            models.ListEdgeWorkersIDRequest(),
        )

        assert_request(
            mock_session, "GET", "/edgeworkers/v1/ids",
        )
        assert len(result.edge_workers) == 2
        assert result.edge_workers[0].edge_worker_id == 12345
        assert result.edge_workers[0].name == "edgeworker"
        assert result.edge_workers[0].group_id == 54321
        assert result.edge_workers[1].edge_worker_id == 12346
        assert result.edge_workers[1].name == "edgeworker-first"

    def test_200_ok_with_params(self, mock_session, edgeworkers_client):
        fixture = load_fixture("list_edgeworkers_id_with_params.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.list_edge_workers_id(
            models.ListEdgeWorkersIDRequest(
                group_id=54321, resource_tier_id=234),
        )

        assert_request(
            mock_session, "GET", "/edgeworkers/v1/ids",
        )
        assert len(result.edge_workers) == 2
        assert result.edge_workers[0].resource_tier_id == 234
        assert result.edge_workers[1].resource_tier_id == 234

    def test_200_ok_empty(self, mock_session, edgeworkers_client):
        fixture = load_fixture("list_edgeworkers_id_empty.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.list_edge_workers_id(
            models.ListEdgeWorkersIDRequest(),
        )

        assert len(result.edge_workers) == 0

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.list_edge_workers_id(
                models.ListEdgeWorkersIDRequest(),
            )


class TestCreateEdgeWorkerID:
    """Tests for Client.create_edge_worker_id."""

    def test_201_created(self, mock_session, edgeworkers_client):
        fixture = load_fixture("create_edgeworker_id.json")
        mock_resp = make_mock_response(201, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.create_edge_worker_id(
            models.CreateEdgeWorkerIDRequest(
                name="New EdgeWorkerID",
                group_id=12345,
                resource_tier_id=123,
            ),
        )

        assert_request(
            mock_session, "POST", "/edgeworkers/v1/ids",
        )
        assert result.edge_worker_id == 83969
        assert result.name == "New EdgeWorkerID"
        assert result.group_id == 12345
        assert result.resource_tier_id == 123

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.create_edge_worker_id(
                models.CreateEdgeWorkerIDRequest(
                    name="New EdgeWorkerID",
                    group_id=12345,
                    resource_tier_id=123,
                ),
            )

    def test_validation_missing_name(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.create_edge_worker_id(
                models.CreateEdgeWorkerIDRequest(
                    group_id=12345,
                    resource_tier_id=123,
                ),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_group_id(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.create_edge_worker_id(
                models.CreateEdgeWorkerIDRequest(
                    name="New EdgeWorkerID",
                    resource_tier_id=123,
                ),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_resource_tier_id(self,
                                                  edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.create_edge_worker_id(
                models.CreateEdgeWorkerIDRequest(
                    name="New EdgeWorkerID",
                    group_id=12345,
                ),
            )
        assert "struct validation" in str(exc_info.value)


class TestUpdateEdgeWorkerID:
    """Tests for Client.update_edge_worker_id."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("update_edgeworker_id.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.update_edge_worker_id(
            models.UpdateEdgeWorkerIDRequest(
                edge_worker_id=54321,
                body=models.EdgeWorkerIDRequestBody(
                    name="Update EdgeWorkerID",
                    group_id=12345,
                    resource_tier_id=123,
                ),
            ),
        )

        assert_request(
            mock_session, "PUT", "/edgeworkers/v1/ids/54321",
        )
        assert result.edge_worker_id == 54321
        assert result.name == "Update EdgeWorkerID"
        assert result.group_id == 12345

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.update_edge_worker_id(
                models.UpdateEdgeWorkerIDRequest(
                    edge_worker_id=54321,
                    body=models.EdgeWorkerIDRequestBody(
                        name="Update EdgeWorkerID",
                        group_id=12345,
                        resource_tier_id=123,
                    ),
                ),
            )

    def test_validation_missing_edge_worker_id(self,
                                                edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.update_edge_worker_id(
                models.UpdateEdgeWorkerIDRequest(
                    body=models.EdgeWorkerIDRequestBody(
                        name="Update EdgeWorkerID",
                        group_id=12345,
                        resource_tier_id=123,
                    ),
                ),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_body(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.update_edge_worker_id(
                models.UpdateEdgeWorkerIDRequest(
                    edge_worker_id=54321),
            )
        assert "struct validation" in str(exc_info.value)


class TestCloneEdgeWorkerID:
    """Tests for Client.clone_edge_worker_id."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("clone_edgeworker_id.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.clone_edge_worker_id(
            models.CloneEdgeWorkerIDRequest(
                edge_worker_id=54321,
                body=models.EdgeWorkerIDRequestBody(
                    name="Clone EdgeWorkerID",
                    group_id=12345,
                    resource_tier_id=123,
                ),
            ),
        )

        assert_request(
            mock_session, "POST",
            "/edgeworkers/v1/ids/54321/clone",
        )
        assert result.edge_worker_id == 54322
        assert result.name == "Clone EdgeWorkerID"
        assert result.source_edge_worker_id == 54321

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.clone_edge_worker_id(
                models.CloneEdgeWorkerIDRequest(
                    edge_worker_id=54321,
                    body=models.EdgeWorkerIDRequestBody(
                        name="Clone EdgeWorkerID",
                        group_id=12345,
                        resource_tier_id=123,
                    ),
                ),
            )

    def test_validation_missing_edge_worker_id(self,
                                                edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.clone_edge_worker_id(
                models.CloneEdgeWorkerIDRequest(
                    body=models.EdgeWorkerIDRequestBody(
                        name="Clone EdgeWorkerID",
                        group_id=12345,
                        resource_tier_id=123,
                    ),
                ),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_body(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.clone_edge_worker_id(
                models.CloneEdgeWorkerIDRequest(
                    edge_worker_id=54321),
            )
        assert "struct validation" in str(exc_info.value)


class TestDeleteEdgeWorkerID:
    """Tests for Client.delete_edge_worker_id."""

    def test_204_no_content(self, mock_session, edgeworkers_client):
        mock_resp = make_mock_response(204)
        mock_session.exec.return_value = (mock_resp, None)

        result = edgeworkers_client.delete_edge_worker_id(
            models.DeleteEdgeWorkerIDRequest(edge_worker_id=54321),
        )

        assert_request(
            mock_session, "DELETE", "/edgeworkers/v1/ids/54321",
        )
        assert result is None

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.delete_edge_worker_id(
                models.DeleteEdgeWorkerIDRequest(
                    edge_worker_id=54321),
            )

    def test_validation_missing_edge_worker_id(self,
                                                edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.delete_edge_worker_id(
                models.DeleteEdgeWorkerIDRequest(),
            )
        assert "struct validation" in str(exc_info.value)


# ===================================================================
# EdgeWorker Version Tests  (mirrors edgeworker_version_test.go)
# ===================================================================


class TestGetEdgeWorkerVersion:
    """Tests for Client.get_edge_worker_version."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("get_edgeworker_version.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.get_edge_worker_version(
            models.GetEdgeWorkerVersionRequest(
                edge_worker_id=12345, version="1.2.3"),
        )

        assert_request(
            mock_session, "GET",
            "/edgeworkers/v1/ids/12345/versions/1.2.3",
        )
        assert result.edge_worker_id == 12345
        assert result.version == "1.2.3"
        assert result.account_id == "B-123-WNKA6P"
        assert result.checksum == \
            "868f28f16c26f46d418d83e24973520534d9ea4e4dbfd8a69ab00c1c37f28ca4"
        assert result.sequence_number == 3
        assert result.created_by == "jbond"
        assert result.created_time == "2021-04-19T07:08:37Z"

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.get_edge_worker_version(
                models.GetEdgeWorkerVersionRequest(
                    edge_worker_id=12345, version="1.2.3"),
            )

    def test_403_forbidden(self, mock_session, edgeworkers_client):
        fixture = load_fixture("error_403_forbidden.json")
        mock_resp = make_mock_response(403, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError) as exc_info:
            edgeworkers_client.get_edge_worker_version(
                models.GetEdgeWorkerVersionRequest(
                    edge_worker_id=12345, version="1.2.3"),
            )
        assert exc_info.value.status == 403

    def test_validation_missing_edge_worker_id(self,
                                                edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.get_edge_worker_version(
                models.GetEdgeWorkerVersionRequest(version="1.2.3"),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_version(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.get_edge_worker_version(
                models.GetEdgeWorkerVersionRequest(
                    edge_worker_id=12345),
            )
        assert "struct validation" in str(exc_info.value)


class TestListEdgeWorkerVersions:
    """Tests for Client.list_edge_worker_versions."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("list_edgeworker_versions.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.list_edge_worker_versions(
            models.ListEdgeWorkerVersionsRequest(
                edge_worker_id=88334),
        )

        assert_request(
            mock_session, "GET",
            "/edgeworkers/v1/ids/88334/versions",
        )
        assert len(result.edge_worker_versions) == 2
        assert result.edge_worker_versions[0].edge_worker_id == 88334
        assert result.edge_worker_versions[0].version == "1.23"
        assert result.edge_worker_versions[0].sequence_number == 3
        assert result.edge_worker_versions[1].version == "1.24.5"
        assert result.edge_worker_versions[1].sequence_number == 4

    def test_200_ok_empty(self, mock_session, edgeworkers_client):
        fixture = load_fixture("list_edgeworker_versions_empty.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.list_edge_worker_versions(
            models.ListEdgeWorkerVersionsRequest(
                edge_worker_id=88334),
        )

        assert len(result.edge_worker_versions) == 0

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.list_edge_worker_versions(
                models.ListEdgeWorkerVersionsRequest(
                    edge_worker_id=88334),
            )

    def test_validation_missing_edge_worker_id(self,
                                                edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.list_edge_worker_versions(
                models.ListEdgeWorkerVersionsRequest(),
            )
        assert "struct validation" in str(exc_info.value)


class TestGetEdgeWorkerVersionContent:
    """Tests for Client.get_edge_worker_version_content."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        bundle_bytes = b"\x1f\x8b\x08\x00test-gzip-content"
        mock_resp = make_mock_response(200)
        mock_resp.content = bundle_bytes
        mock_session.exec.return_value = (mock_resp, None)

        result = edgeworkers_client.get_edge_worker_version_content(
            models.GetEdgeWorkerVersionContentRequest(
                edge_worker_id=12345, version="1.2.3"),
        )

        assert_request(
            mock_session, "GET",
            "/edgeworkers/v1/ids/12345/versions/1.2.3/content",
        )
        assert isinstance(result, models.Bundle)
        assert result.data == bundle_bytes

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.get_edge_worker_version_content(
                models.GetEdgeWorkerVersionContentRequest(
                    edge_worker_id=12345, version="1.2.3"),
            )

    def test_validation_missing_edge_worker_id(self,
                                                edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.get_edge_worker_version_content(
                models.GetEdgeWorkerVersionContentRequest(
                    version="1.2.3"),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_version(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.get_edge_worker_version_content(
                models.GetEdgeWorkerVersionContentRequest(
                    edge_worker_id=12345),
            )
        assert "struct validation" in str(exc_info.value)


class TestCreateEdgeWorkerVersion:
    """Tests for Client.create_edge_worker_version."""

    def test_201_created(self, mock_session, edgeworkers_client):
        fixture = load_fixture("create_edgeworker_version.json")
        mock_resp = make_mock_response(201, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)
        bundle_bytes = b"\x1f\x8b\x08\x00test-gzip-content"

        result = edgeworkers_client.create_edge_worker_version(
            models.CreateEdgeWorkerVersionRequest(
                edge_worker_id=88334,
                content_bundle=bundle_bytes,
            ),
        )

        assert_request(
            mock_session, "POST",
            "/edgeworkers/v1/ids/88334/versions",
        )
        assert result.edge_worker_id == 88334
        assert result.version == "1.23"
        assert result.sequence_number == 24

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.create_edge_worker_version(
                models.CreateEdgeWorkerVersionRequest(
                    edge_worker_id=88334,
                    content_bundle=b"\x1f\x8b\x08\x00test",
                ),
            )

    def test_validation_missing_edge_worker_id(self,
                                                edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.create_edge_worker_version(
                models.CreateEdgeWorkerVersionRequest(
                    content_bundle=b"\x1f\x8b"),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_content_bundle(self,
                                                edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.create_edge_worker_version(
                models.CreateEdgeWorkerVersionRequest(
                    edge_worker_id=88334),
            )
        assert "struct validation" in str(exc_info.value)


class TestDeleteEdgeWorkerVersion:
    """Tests for Client.delete_edge_worker_version."""

    def test_204_no_content(self, mock_session, edgeworkers_client):
        mock_resp = make_mock_response(204)
        mock_session.exec.return_value = (mock_resp, None)

        result = edgeworkers_client.delete_edge_worker_version(
            models.DeleteEdgeWorkerVersionRequest(
                edge_worker_id=12345, version="1.2.3"),
        )

        assert_request(
            mock_session, "DELETE",
            "/edgeworkers/v1/ids/12345/versions/1.2.3",
        )
        assert result is None

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.delete_edge_worker_version(
                models.DeleteEdgeWorkerVersionRequest(
                    edge_worker_id=12345, version="1.2.3"),
            )

    def test_validation_missing_edge_worker_id(self,
                                                edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.delete_edge_worker_version(
                models.DeleteEdgeWorkerVersionRequest(
                    version="1.2.3"),
            )
        assert "struct validation" in str(exc_info.value)


# ===================================================================
# EdgeWorkers Client Tests  (mirrors edgeworkers_test.go)
# ===================================================================


class TestClient:
    """Tests for Client constructor."""

    def test_default_constructor(self, mock_session):
        client = Client(mock_session)
        assert client is not None

    def test_constructor_with_session(self):
        session = MagicMock()
        client = Client(session)
        assert client is not None


# ===================================================================
# Errors Tests  (mirrors errors_test.go)
# ===================================================================


class TestNewError:
    """Tests for error parsing from HTTP responses."""

    def test_valid_response_status_500(self):
        body = {
            "type": "a",
            "title": "b",
            "detail": "c",
            "status": 500,
        }
        mock_resp = make_mock_response(500, body=body)
        mock_resp.text = json.dumps(body)

        err = parse_edgeworkers_error(mock_resp)

        assert isinstance(err, EdgeWorkersError)
        assert err.type == "a"
        assert err.title == "b"
        assert err.detail == "c"
        assert err.status == 500

    def test_invalid_response_body(self):
        mock_resp = make_mock_response(500)
        mock_resp.text = "test"

        err = parse_edgeworkers_error(mock_resp)

        assert isinstance(err, EdgeWorkersError)
        assert err.status == 500
        assert err.detail == "test"


class TestErrorIs:
    """Tests for Error.is_equivalent method."""

    def test_different_error_code(self):
        err = EdgeWorkersError(status=404, title="Not Found")
        other = EdgeWorkersError(status=401, title="Unauthorized")
        assert not err.is_equivalent(other)

    def test_same_error_code(self):
        err = EdgeWorkersError(status=404, title="Not Found")
        other = EdgeWorkersError(status=404, title="Not Found")
        assert err.is_equivalent(other)

    def test_same_error_code_and_title(self):
        err = EdgeWorkersError(
            status=404, title="Not Found",
            detail="resource missing",
        )
        other = EdgeWorkersError(
            status=404, title="Not Found",
            detail="resource missing",
        )
        assert err.is_equivalent(other)

    def test_same_error_code_different_message(self):
        err = EdgeWorkersError(
            status=404, title="Not Found",
            detail="resource A missing",
        )
        other = EdgeWorkersError(
            status=404, title="Not Found",
            detail="resource B missing",
        )
        assert not err.is_equivalent(other)

    def test_sentinel_not_found(self):
        err = EdgeWorkersError(
            status=404, error_code="EKV_9000",
            title="Not Found",
        )
        assert err.is_equivalent(ew_errors.ErrNotFound)

    def test_sentinel_version_being_deactivated(self):
        err = EdgeWorkersError(
            status=409, error_code="EW1031",
            title="Conflict",
        )
        assert err.is_equivalent(ew_errors.ErrVersionBeingDeactivated)

    def test_sentinel_version_already_deactivated(self):
        err = EdgeWorkersError(
            status=409, error_code="EW1032",
            title="Conflict",
        )
        assert err.is_equivalent(
            ew_errors.ErrVersionAlreadyDeactivated,
        )


class TestValidationErrorsParsing:
    """Tests for non-JSON error response handling."""

    def test_html_response(self):
        html_body = (
            "<HTML><HEAD></HEAD><BODY>An error occurred while"
            " processing your request</BODY></HTML>"
        )
        mock_resp = make_mock_response(500)
        mock_resp.text = html_body

        err = parse_edgeworkers_error(mock_resp)

        assert isinstance(err, EdgeWorkersError)
        assert err.status == 500
        assert err.detail == html_body

    def test_plain_text_response(self):
        text_body = "rate limit exceeded"
        mock_resp = make_mock_response(429)
        mock_resp.text = text_body

        err = parse_edgeworkers_error(mock_resp)

        assert isinstance(err, EdgeWorkersError)
        assert err.status == 429
        assert err.detail == text_body

    def test_xml_response(self):
        xml_body = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<error><message>fail</message></error>"
        )
        mock_resp = make_mock_response(500)
        mock_resp.text = xml_body

        err = parse_edgeworkers_error(mock_resp)

        assert isinstance(err, EdgeWorkersError)
        assert err.status == 500
        assert err.detail == xml_body


# ===================================================================
# Permission Group Tests  (mirrors permission_group_test.go)
# ===================================================================


class TestGetPermissionGroup:
    """Tests for Client.get_permission_group."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("get_permission_group.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.get_permission_group(
            models.GetPermissionGroupRequest(group_id="123"),
        )

        assert_request(
            mock_session, "GET", "/edgeworkers/v1/groups/123",
        )
        assert result.id == 123
        assert result.name == "Permission Group"
        assert "VIEW" in result.capabilities
        assert "ACTIVATE" in result.capabilities
        assert len(result.capabilities) == 8

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.get_permission_group(
                models.GetPermissionGroupRequest(group_id="123"),
            )

    def test_validation_missing_group_id(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.get_permission_group(
                models.GetPermissionGroupRequest(),
            )
        assert "struct validation" in str(exc_info.value)


class TestListPermissionGroups:
    """Tests for Client.list_permission_groups."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("list_permission_groups.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.list_permission_groups()

        assert_request(
            mock_session, "GET", "/edgeworkers/v1/groups",
        )
        assert len(result.permission_groups) == 3
        assert result.permission_groups[0].id == 11111
        assert result.permission_groups[0].name == \
            "First test group"
        assert result.permission_groups[1].id == 22222
        assert result.permission_groups[1].name == \
            "Second test group"
        assert result.permission_groups[2].id == 33333
        assert result.permission_groups[2].name == \
            "Third test group"

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.list_permission_groups()


# ===================================================================
# Properties Tests  (mirrors properties_test.go)
# ===================================================================


class TestListProperties:
    """Tests for Client.list_properties."""

    def test_200_ok_no_query(self, mock_session, edgeworkers_client):
        fixture = load_fixture("list_properties.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.list_properties(
            models.ListPropertiesRequest(edge_worker_id=123),
        )

        assert_request(
            mock_session, "GET",
            "/edgeworkers/v1/ids/123/properties",
        )
        assert len(result.properties) == 3
        assert result.properties[0].id == 1
        assert result.properties[0].name == "property_name_1"
        assert result.properties[0].latest_version == 1
        assert result.properties[1].id == 2
        assert result.properties[2].id == 3

    def test_200_ok_active_only(self, mock_session,
                                 edgeworkers_client):
        fixture = load_fixture("list_properties_active_only.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.list_properties(
            models.ListPropertiesRequest(
                edge_worker_id=123, active_only=True),
        )

        assert_request(
            mock_session, "GET",
            "/edgeworkers/v1/ids/123/properties",
        )
        assert len(result.properties) == 2
        assert result.properties[0].id == 100
        assert result.properties[0].name == "property1"
        assert result.properties[0].production_version == 2
        assert result.properties[1].id == 101
        assert result.properties[1].name == "property2"
        assert result.properties[1].staging_version == 1
        assert result.limited_access_to_properties is False

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.list_properties(
                models.ListPropertiesRequest(edge_worker_id=123),
            )

    def test_validation_missing_edge_worker_id(self,
                                                edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.list_properties(
                models.ListPropertiesRequest(),
            )
        assert "struct validation" in str(exc_info.value)


# ===================================================================
# Report Tests  (mirrors report_test.go)
# ===================================================================


class TestGetSummaryReport:
    """Tests for Client.get_summary_report."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("get_summary_report.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.get_summary_report(
            models.GetSummaryReportRequest(
                start="2022-01-10T03:00:00Z",
                end="2022-01-14T13:22:28Z",
                edge_worker="42",
            ),
        )

        assert_request(
            mock_session, "GET", "/edgeworkers/v1/reports/1",
        )
        assert result.report_id == 1
        assert result.name == "Overall summary"
        assert result.start == "2022-01-10T03:00:00Z"
        assert result.end == "2022-01-14T13:22:28Z"

        assert result.data is not None
        assert result.data.memory.avg == 3607.069168
        assert result.data.memory.min == 0.0
        assert result.data.memory.max == 458044.0
        assert result.data.successes.total == 88119
        assert result.data.init_duration.avg == 1.2559162420382166
        assert result.data.init_duration.min == 0.33
        assert result.data.init_duration.max == 28.975
        assert result.data.exec_duration.avg == 0.11508884576538543
        assert result.data.exec_duration.min == 0.005
        assert result.data.exec_duration.max == 9.415
        assert result.data.errors.total == 0
        assert result.data.invocations.total == 88119

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.get_summary_report(
                models.GetSummaryReportRequest(
                    start="2022-01-10T03:00:00Z",
                    edge_worker="42",
                ),
            )

    def test_validation_missing_start(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.get_summary_report(
                models.GetSummaryReportRequest(edge_worker="42"),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_edge_worker(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.get_summary_report(
                models.GetSummaryReportRequest(
                    start="2022-01-10T03:00:00Z"),
            )
        assert "struct validation" in str(exc_info.value)


class TestGetReport:
    """Tests for Client.get_report."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("get_report_id2.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.get_report(
            models.GetReportRequest(
                report_id=2,
                start="2022-01-10T03:00:00Z",
                end="2022-01-17T10:43:15Z",
                edge_worker="37017",
            ),
        )

        assert_request(
            mock_session, "GET", "/edgeworkers/v1/reports/2",
        )
        assert result.report_id == 2
        assert result.start == "2022-01-10T03:00:00Z"
        assert result.end == "2022-01-17T10:43:15Z"
        assert len(result.data) > 0
        assert result.data[0].edge_worker_id == 37017
        assert result.data[0].data is not None
        assert len(result.data[0].data.on_client_request) == 2
        assert result.data[0].data.on_client_request[0].invocations \
            == 8

    def test_200_ok_empty_data(self, mock_session, edgeworkers_client):
        fixture = load_fixture("get_report_empty_data.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.get_report(
            models.GetReportRequest(
                report_id=4,
                start="2021-12-04T00:00:00Z",
                end="2022-01-01T00:00:00Z",
                edge_worker="42",
            ),
        )

        assert result.report_id == 4
        assert len(result.data) == 0

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.get_report(
                models.GetReportRequest(
                    report_id=2,
                    start="2022-01-10T03:00:00Z",
                    edge_worker="42",
                ),
            )

    def test_validation_missing_report_id(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.get_report(
                models.GetReportRequest(
                    start="2022-01-10T03:00:00Z",
                    edge_worker="42",
                ),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_start(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.get_report(
                models.GetReportRequest(
                    report_id=2, edge_worker="42"),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_missing_edge_worker(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.get_report(
                models.GetReportRequest(
                    report_id=2,
                    start="2022-01-10T03:00:00Z"),
            )
        assert "struct validation" in str(exc_info.value)


class TestListReports:
    """Tests for Client.list_reports."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("list_reports.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.list_reports()

        assert_request(
            mock_session, "GET", "/edgeworkers/v1/reports",
        )
        assert len(result.reports) == 4
        assert result.reports[0].report_id == 1
        assert result.reports[0].name == "Overall summary"
        assert result.reports[1].report_id == 2
        assert result.reports[2].report_id == 3
        assert result.reports[3].report_id == 4

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.list_reports()


# ===================================================================
# Resource Tier Tests  (mirrors resource_tier_test.go)
# ===================================================================


class TestListResourceTiers:
    """Tests for Client.list_resource_tiers."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("list_resource_tiers.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.list_resource_tiers(
            models.ListResourceTiersRequest(contract_id="1-ABC"),
        )

        assert_request(
            mock_session, "GET",
            "/edgeworkers/v1/resource-tiers",
        )
        assert len(result.resource_tiers) == 2
        assert result.resource_tiers[0].id == 100
        assert result.resource_tiers[0].name == "Basic Compute"
        assert len(result.resource_tiers[0].edge_worker_limits) == 2
        assert result.resource_tiers[0].edge_worker_limits[0] \
            .limit_name == \
            "Maximum CPU time during initialization"
        assert result.resource_tiers[0].edge_worker_limits[0] \
            .limit_value == 30
        assert result.resource_tiers[0].edge_worker_limits[0] \
            .limit_unit == "MILLISECOND"
        assert result.resource_tiers[1].id == 200
        assert result.resource_tiers[1].name == "Dynamic Compute"

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.list_resource_tiers(
                models.ListResourceTiersRequest(contract_id="1-ABC"),
            )

    def test_validation_missing_contract_id(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.list_resource_tiers(
                models.ListResourceTiersRequest(),
            )
        assert "struct validation" in str(exc_info.value)


class TestGetResourceTier:
    """Tests for Client.get_resource_tier."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("get_resource_tier.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.get_resource_tier(
            models.GetResourceTierRequest(edge_worker_id=12345),
        )

        assert_request(
            mock_session, "GET",
            "/edgeworkers/v1/ids/12345/resource-tier",
        )
        assert result.id == 100
        assert result.name == "Basic Compute"
        assert len(result.edge_worker_limits) == 2

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.get_resource_tier(
                models.GetResourceTierRequest(edge_worker_id=12345),
            )

    def test_validation_missing_edge_worker_id(self,
                                                edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.get_resource_tier(
                models.GetResourceTierRequest(),
            )
        assert "struct validation" in str(exc_info.value)


# ===================================================================
# Secure Token Tests  (mirrors secure_tokens_test.go)
# ===================================================================


class TestCreateSecureToken:
    """Tests for Client.create_secure_token."""

    def test_201_created(self, mock_session, edgeworkers_client):
        fixture = load_fixture("create_secure_token.json")
        mock_resp = make_mock_response(201, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.create_secure_token(
            models.CreateSecureTokenRequest(
                acl="/*",
                expiry=15,
                hostname="test.devexp.akamai.com",
            ),
        )

        assert_request(
            mock_session, "POST",
            "/edgeworkers/v1/secure-token",
        )
        assert result.akamai_ew_trace.startswith("st=")

    def test_201_created_hostname_only(self, mock_session,
                                        edgeworkers_client):
        fixture = load_fixture("create_secure_token.json")
        mock_resp = make_mock_response(201, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.create_secure_token(
            models.CreateSecureTokenRequest(
                hostname="test.devexp.akamai.com",
            ),
        )

        assert_request(
            mock_session, "POST",
            "/edgeworkers/v1/secure-token",
        )
        assert result.akamai_ew_trace is not None

    def test_201_created_hostname_and_property_id(
        self, mock_session, edgeworkers_client,
    ):
        fixture = load_fixture("create_secure_token.json")
        mock_resp = make_mock_response(201, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.create_secure_token(
            models.CreateSecureTokenRequest(
                hostname="test.devexp.akamai.com",
                property_id="200153206",
            ),
        )

        assert_request(
            mock_session, "POST",
            "/edgeworkers/v1/secure-token",
        )
        assert result.akamai_ew_trace is not None

    def test_validation_empty_request(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.create_secure_token(
                models.CreateSecureTokenRequest(),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_both_acl_and_url(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.create_secure_token(
                models.CreateSecureTokenRequest(
                    acl="/*",
                    url="/test",
                    hostname="test.devexp.akamai.com",
                    expiry=15,
                ),
            )
        assert "struct validation" in str(exc_info.value)

    def test_validation_expiry_too_high(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.create_secure_token(
                models.CreateSecureTokenRequest(
                    acl="/*",
                    hostname="test.devexp.akamai.com",
                    expiry=1440,
                ),
            )
        assert "struct validation" in str(exc_info.value)

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.create_secure_token(
                models.CreateSecureTokenRequest(
                    acl="/*",
                    expiry=15,
                    hostname="test.devexp.akamai.com",
                    network="STAGING",
                ),
            )


# ===================================================================
# Validation (Bundle) Tests  (mirrors validations_test.go)
# ===================================================================


class TestValidateBundle:
    """Tests for Client.validate_bundle."""

    def test_200_ok(self, mock_session, edgeworkers_client):
        fixture = load_fixture("validate_bundle_empty.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.validate_bundle(
            models.ValidateBundleRequest(
                bundle=b"\x1f\x8b\x08\x00test-gzip-content"),
        )

        assert_request(
            mock_session, "POST",
            "/edgeworkers/v1/validations",
        )
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_200_ok_with_error(self, mock_session, edgeworkers_client):
        fixture = load_fixture("validate_bundle_error.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.validate_bundle(
            models.ValidateBundleRequest(
                bundle=b"\x1f\x8b\x08\x00test-gzip-content"),
        )

        assert len(result.errors) == 1
        assert result.errors[0].type == "INVALID_GZIP_FORMAT"
        assert result.errors[0].message == "invalid GZIP file format"
        assert len(result.warnings) == 0

    def test_200_ok_with_warning(self, mock_session,
                                  edgeworkers_client):
        fixture = load_fixture("validate_bundle_warning.json")
        mock_resp = make_mock_response(200, body=fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        result = edgeworkers_client.validate_bundle(
            models.ValidateBundleRequest(
                bundle=b"\x1f\x8b\x08\x00test-gzip-content"),
        )

        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert result.warnings[0].type == \
            "ACCESS_TOKEN_EXPIRING_SOON"
        assert result.warnings[0].message == "token expiring soon"

    def test_500_internal_server_error(self, mock_session,
                                       edgeworkers_client):
        fixture = load_fixture("error_500.json")
        mock_resp = make_mock_response(500, body=fixture)
        mock_resp.text = json.dumps(fixture)
        mock_session.exec.return_value = (mock_resp, fixture)

        with pytest.raises(EdgeWorkersError):
            edgeworkers_client.validate_bundle(
                models.ValidateBundleRequest(
                    bundle=b"\x1f\x8b\x08\x00test"),
            )

    def test_validation_missing_bundle(self, edgeworkers_client):
        with pytest.raises(ErrStructValidation) as exc_info:
            edgeworkers_client.validate_bundle(
                models.ValidateBundleRequest(),
            )
        assert "struct validation" in str(exc_info.value)
