# pylint: disable=missing-function-docstring,line-too-long,too-many-lines
# pylint: disable=unsubscriptable-object,missing-class-docstring,too-many-public-methods
"""Unit tests for the Cloudlets V3 API client.

Mirrors all Go test scenarios from pkg/cloudlets/v3/*_test.go.
"""

import json
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.cloudlets_v3.cloudlets_v3 import (
    Client,
    CloudletsV3Client,
)
from akamai.edgegrid.cloudlets_v3.models import (  # pylint: disable=no-name-in-module
    _deserialize_object_match_value,
    _ALL_OMV_HANDLERS,
    _SIMPLE_OBJECT_OMV_HANDLERS,
)
from akamai.edgegrid.cloudlets_v3 import errors
from akamai.edgegrid.cloudlets_v3 import models
from akamai.edgegrid.cloudlets_v3 import validation
from akamai.edgegrid.cloudlets_v3.models import deserialize_match_rules


# ---------------------------------------------------------------------------
# Helpers / Constants
# ---------------------------------------------------------------------------

STANDARD_500_BODY = {
    "type": "internal_error",
    "title": "Internal Server Error",
    "status": 500,
    "requestId": "1",
    "requestTime": "12:00",
    "clientIp": "1.1.1.1",
    "serverIp": "2.2.2.2",
    "method": "GET",
}


def _api_error(body=None, status=500):
    """Build an errors.Error simulating what _parse_error returns."""
    body = body or STANDARD_500_BODY
    err = errors.Error()
    err.type = body.get("type", "")
    err.title = body.get("title", "")
    err.detail = body.get("detail", "")
    err.instance = body.get("instance", "")
    err.status = status
    err.errors = body.get("errors")
    err.request_id = body.get("requestId", "")
    err.request_time = body.get("requestTime", "")
    err.client_ip = body.get("clientIp", "")
    err.server_ip = body.get("serverIp", "")
    err.method = body.get("method", "")
    return err


def _mock_response(status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    return resp


# ===================================================================
# TestClient — from cloudlets_test.go
# ===================================================================


class TestClient:
    """Mirrors Go TestClient (cloudlets_test.go lines 30-61)."""

    def test_no_options_provided_return_default(self, mock_session):
        result = Client(mock_session)
        assert isinstance(result, CloudletsV3Client)

    def test_client_stores_session(self, mock_session):
        result = Client(mock_session)
        # pylint: disable=protected-access
        assert result._session is mock_session


# ===================================================================
# TestNewError — from errors_test.go lines 16-67
# ===================================================================


class TestNewError:
    """Mirrors Go TestNewError — tests _parse_error."""

    def test_valid_response_status_code_500(self, mock_session):
        client_inst = Client(mock_session)
        resp = MagicMock()
        resp.status_code = 500
        resp.text = '{"type":"a","title":"b","detail":"c"}'
        # pylint: disable=protected-access
        err = client_inst._parse_error(resp)
        assert err.type == "a"
        assert err.title == "b"
        assert err.detail == "c"
        assert err.status == 500

    def test_invalid_response_body_assign_status_code(self, mock_session):
        client_inst = Client(mock_session)
        resp = MagicMock()
        resp.status_code = 500
        resp.text = "test"
        # pylint: disable=protected-access
        err = client_inst._parse_error(resp)
        assert err.title == (
            "Failed to unmarshal error body. Cloudlets API "
            "failed. Check details for more information."
        )
        assert err.detail == "test"
        assert err.status == 500


# ===================================================================
# TestAs — from errors_test.go lines 70-103
# ===================================================================


class TestAs:
    """Mirrors Go TestAs — tests Error.is_equivalent()."""

    def test_different_error_code(self):
        err_a = errors.Error()
        err_a.status = 404
        err_b = errors.Error()
        err_b.status = 401
        assert err_a.is_equivalent(err_b) is False

    def test_same_error_code(self):
        err_a = errors.Error()
        err_a.status = 404
        err_b = errors.Error()
        err_b.status = 404
        assert err_a.is_equivalent(err_b) is True

    def test_same_error_code_and_error_message(self):
        some_error = "some error"
        err_a = errors.Error()
        err_a.status = 404
        err_a.errors = some_error
        err_b = errors.Error()
        err_b.status = 404
        err_b.errors = some_error
        assert err_a.is_equivalent(err_b) is True

    def test_same_error_code_and_different_error_message(self):
        some_error = "some error"
        err_a = errors.Error()
        err_a.status = 404
        err_a.errors = some_error
        err_b = errors.Error()
        err_b.status = 404
        assert err_a.is_equivalent(err_b) is False


# ===================================================================
# TestJsonErrorUnmarshalling — from errors_test.go lines 106-161
# ===================================================================


class TestJsonErrorUnmarshalling:
    """Mirrors Go TestJsonErrorUnmarshalling."""

    def test_api_failure_with_html_response(self, mock_session):
        client_inst = Client(mock_session)
        resp = MagicMock()
        resp.status_code = 0
        resp.text = "<HTML><HEAD>...</HEAD><BODY>...</BODY></HTML>"
        # pylint: disable=protected-access
        err = client_inst._parse_error(resp)
        assert err.type == ""
        assert err.title == (
            "Failed to unmarshal error body. Cloudlets API "
            "failed. Check details for more information."
        )
        assert err.detail == "<HTML><HEAD>...</HEAD><BODY>...</BODY></HTML>"

    def test_api_failure_with_plain_text_response(self, mock_session):
        client_inst = Client(mock_session)
        resp = MagicMock()
        resp.status_code = 0
        resp.text = (
            "Your request did not succeed as this operation has reached "
            " the limit for your account. Please try after "
            "2024-01-16T15:20:55.945Z"
        )
        # pylint: disable=protected-access
        err = client_inst._parse_error(resp)
        assert err.type == ""
        assert err.title == (
            "Failed to unmarshal error body. Cloudlets API "
            "failed. Check details for more information."
        )
        assert err.detail == (
            "Your request did not succeed as this operation has reached "
            " the limit for your account. Please try after "
            "2024-01-16T15:20:55.945Z"
        )

    def test_api_failure_with_xml_response(self, mock_session):
        client_inst = Client(mock_session)
        resp = MagicMock()
        resp.status_code = 0
        resp.text = '<Root><Item id="1" name="Example" /></Root>'
        # pylint: disable=protected-access
        err = client_inst._parse_error(resp)
        assert err.type == ""
        assert err.title == (
            "Failed to unmarshal error body. Cloudlets API "
            "failed. Check details for more information."
        )
        assert err.detail == '<Root><Item id="1" name="Example" /></Root>'


# ===================================================================
# TestListCloudlets — from list_cloudlets_test.go
# ===================================================================


class TestListCloudlets:
    """Mirrors Go TestListCloudlets (list_cloudlets_test.go)."""

    def test_200_ok(self, mock_session, client):
        data = [
            {"cloudletName": "API_PRIORITIZATION", "cloudletType": "AP"},
            {"cloudletName": "AUDIENCE_SEGMENTATION", "cloudletType": "AS"},
            {"cloudletName": "EDGE_REDIRECTOR", "cloudletType": "ER"},
            {"cloudletName": "FORWARD_REWRITE", "cloudletType": "FR"},
            {"cloudletName": "PHASED_RELEASE", "cloudletType": "CD"},
            {"cloudletName": "REQUEST_CONTROL", "cloudletType": "IG"},
        ]
        mock_session.exec.return_value = (_mock_response(200), data)

        result = client.list_cloudlets()
        assert len(result) == 6
        assert result[0].cloudlet_name == "API_PRIORITIZATION"
        assert result[0].cloudlet_type == "AP"
        assert result[1].cloudlet_name == "AUDIENCE_SEGMENTATION"
        assert result[1].cloudlet_type == "AS"
        assert result[2].cloudlet_name == "EDGE_REDIRECTOR"
        assert result[2].cloudlet_type == "ER"
        assert result[3].cloudlet_name == "FORWARD_REWRITE"
        assert result[3].cloudlet_type == "FR"
        assert result[4].cloudlet_name == "PHASED_RELEASE"
        assert result[4].cloudlet_type == "CD"
        assert result[5].cloudlet_name == "REQUEST_CONTROL"
        assert result[5].cloudlet_type == "IG"

        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/cloudlets/v3/cloudlet-info"

    def test_500_internal_server_error(self, mock_session, client):
        mock_session.exec.side_effect = _api_error()
        with pytest.raises(RuntimeError) as exc_info:
            client.list_cloudlets()
        assert errors.ErrListCloudlets in str(exc_info.value)


# ===================================================================
# Policy response data factories
# ===================================================================


def _minimal_policy_response_data():
    """Return a minimal policy JSON dict matching Go test fixtures."""
    return {
        "cloudletType": "FR",
        "createdBy": "User1",
        "createdDate": "2023-10-23T11:21:19.896Z",
        "currentActivations": {
            "production": {"effective": None, "latest": None},
            "staging": {"effective": None, "latest": None},
        },
        "description": None,
        "groupId": 1,
        "id": 11,
        "links": [{"href": "Link1", "rel": "self"}],
        "modifiedBy": "User1",
        "modifiedDate": "2023-10-23T11:21:19.896Z",
        "name": "TestName",
        "policyType": "SHARED",
    }


def _activation_data(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    created_by, activation_id, href, network, policy_id,
    status="SUCCESS", policy_version=1,
):
    """Build a PolicyActivation dict for embedding in policy responses."""
    return {
        "createdBy": created_by,
        "createdDate": "2023-10-23T11:21:19.896Z",
        "finishDate": "2023-10-23T11:22:57.589Z",
        "id": activation_id,
        "links": [{"href": href, "rel": "self"}],
        "network": network,
        "operation": "ACTIVATION",
        "policyId": policy_id,
        "policyVersion": policy_version,
        "policyVersionDeleted": False,
        "status": status,
    }


def _policy_with_activations_data():
    """Policy response with full activation data from Go tests."""
    return {
        "cloudletType": "CD",
        "createdBy": "User1",
        "createdDate": "2023-10-23T11:21:19.896Z",
        "currentActivations": {
            "production": {
                "effective": _activation_data("User1", 123, "Link1", "PRODUCTION", 1234),
                "latest": _activation_data("User1", 321, "Link2", "PRODUCTION", 4321),
            },
            "staging": {
                "effective": _activation_data("User3", 789, "Link3", "STAGING", 6789),
                "latest": _activation_data("User3", 987, "Link4", "STAGING", 9876),
            },
        },
        "description": "Test",
        "groupId": 1,
        "id": 22,
        "links": [{"href": "Link5", "rel": "self"}],
        "modifiedBy": "User1",
        "modifiedDate": "2023-10-23T11:21:19.896Z",
        "name": "TestName",
        "policyType": "SHARED",
    }


_LIST_POLICIES_LINKS = [
    {"href": "/cloudlets/v3/policies?page=0&size=1000", "rel": "self"}
]

_LIST_POLICIES_PAGE = {
    "number": 0,
    "size": 1000,
    "totalElements": 54,
    "totalPages": 1,
}


# ===================================================================
# TestListPolicies — from policy_test.go lines 18-490
# ===================================================================


class TestListPolicies:
    """Mirrors Go TestListPolicies."""

    def test_200_ok_two_policies(self, mock_session, client):
        minimal_policy = {
            "cloudletType": "CD",
            "createdBy": "User1",
            "createdDate": "2023-10-23T11:21:19.896Z",
            "currentActivations": {
                "production": {"effective": None, "latest": None},
                "staging": {"effective": None, "latest": None},
            },
            "description": None,
            "groupId": 1,
            "id": 11,
            "links": [{"href": "Link1", "rel": "self"}],
            "modifiedBy": "User2",
            "modifiedDate": "2023-10-23T11:21:19.896Z",
            "name": "Name1",
            "policyType": "SHARED",
        }
        data = {
            "content": [minimal_policy, _policy_with_activations_data()],
            "links": _LIST_POLICIES_LINKS,
            "page": _LIST_POLICIES_PAGE,
        }
        mock_session.exec.return_value = (_mock_response(200), data)
        result = client.list_policies(models.ListPoliciesRequest())
        assert len(result.content) == 2
        assert result.content[0].id == 11
        assert result.content[0].name == "Name1"
        assert result.content[1].id == 22
        assert result.content[1].description == "Test"
        # Verify activation nesting
        act = result.content[1].current_activations
        assert act.production.effective.id == 123
        assert act.production.latest.id == 321
        assert act.staging.effective.id == 789
        assert act.staging.latest.id == 987
        assert result.page.total_elements == 54

        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/cloudlets/v3/policies"

    def test_200_ok_with_query_params(self, mock_session, client):
        data = {
            "content": [_minimal_policy_response_data()],
            "links": _LIST_POLICIES_LINKS,
            "page": _LIST_POLICIES_PAGE,
        }
        mock_session.exec.return_value = (_mock_response(200), data)
        params = models.ListPoliciesRequest(page=2, size=12)
        result = client.list_policies(params)
        assert len(result.content) == 1

        call_args = mock_session.exec.call_args
        path = call_args[0][1]
        assert "page=2" in path
        assert "size=12" in path

    def test_200_ok_empty_content(self, mock_session, client):
        data = {
            "content": [],
            "links": _LIST_POLICIES_LINKS,
            "page": {
                "number": 0, "size": 1000,
                "totalElements": 0, "totalPages": 1,
            },
        }
        mock_session.exec.return_value = (_mock_response(200), data)
        result = client.list_policies(models.ListPoliciesRequest())
        assert result.content is None or len(result.content) == 0

    def test_validation_errors_size_and_page(self):
        """Size < 10 and negative page."""
        err = validation.validate_list_policies_request(
            models.ListPoliciesRequest(page=-2, size=5)
        )
        assert err is not None
        assert "Page: must be no less than 0" in err
        assert "Size: must be no less than 10" in err

    def test_500_internal_server_error(self, mock_session, client):
        mock_session.exec.side_effect = _api_error()
        with pytest.raises(RuntimeError) as exc_info:
            client.list_policies(models.ListPoliciesRequest())
        assert errors.ErrListPolicies in str(exc_info.value)


# ===================================================================
# TestCreatePolicy — from policy_test.go lines 492-679
# ===================================================================


class TestCreatePolicy:
    """Mirrors Go TestCreatePolicy."""

    def test_200_ok_minimal_data(self, mock_session, client):
        data = _minimal_policy_response_data()
        mock_session.exec.return_value = (_mock_response(201), data)
        params = models.CreatePolicyRequest(
            cloudlet_type=models.CloudletTypeFR,
            group_id=1,
            name="TestName",
        )
        result = client.create_policy(params)
        assert result.cloudlet_type == "FR"
        assert result.name == "TestName"
        assert result.id == 11

        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/cloudlets/v3/policies"
        body = call_args[1].get("body") if call_args[1] else call_args[0][2]
        assert body["cloudletType"] == "FR"
        assert body["groupId"] == 1
        assert body["name"] == "TestName"

    def test_200_ok_all_data(self, mock_session, client):
        data = _minimal_policy_response_data()
        data["description"] = "Description"
        mock_session.exec.return_value = (_mock_response(201), data)
        params = models.CreatePolicyRequest(
            cloudlet_type=models.CloudletTypeFR,
            description="Description",
            group_id=1,
            name="TestName",
            policy_type=models.PolicyTypeShared,
        )
        result = client.create_policy(params)
        assert result.description == "Description"

    def test_validation_errors(self):
        params = models.CreatePolicyRequest(
            cloudlet_type="Wrong Cloudlet Type",
            description="Too long description" * 20,
            group_id=1,
            name="TestName not match",
            policy_type="Wrong Policy Type",
        )
        err = validation.validate_create_policy_request(params)
        assert err is not None
        assert "CloudletType: value 'Wrong Cloudlet Type' is invalid. Must be one of: 'AP', 'AS', 'CD', 'ER', 'FR', 'IG'" in err
        assert "Description: the length must be no more than 255" in err
        assert "Name: value 'TestName not match' is invalid. Must be of format: ^[a-z_A-Z0-9]+$" in err
        assert "PolicyType: value 'Wrong Policy Type' is invalid. Must be 'SHARED'" in err

    def test_validation_errors_missing_required_params(self):
        params = models.CreatePolicyRequest()
        err = validation.validate_create_policy_request(params)
        assert err is not None
        assert "CloudletType: cannot be blank" in err
        assert "GroupID: cannot be blank" in err
        assert "Name: cannot be blank" in err


# ===================================================================
# TestDeletePolicy — from policy_test.go lines 681-722
# ===================================================================


class TestDeletePolicy:
    """Mirrors Go TestDeletePolicy."""

    def test_204(self, mock_session, client):
        mock_session.exec.return_value = (_mock_response(204), None)
        client.delete_policy(models.DeletePolicyRequest(policy_id=1))

        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "DELETE"
        assert call_args[0][1] == "/cloudlets/v3/policies/1"

    def test_validation_errors_missing_required_param(self):
        err = validation.validate_delete_policy_request(
            models.DeletePolicyRequest()
        )
        assert err is not None
        assert "PolicyID: cannot be blank" in err


# ===================================================================
# TestGetPolicy — from policy_test.go lines 724-1159
# ===================================================================


class TestGetPolicy:
    """Mirrors Go TestGetPolicy."""

    def test_200_ok_minimal_data(self, mock_session, client):
        data = _minimal_policy_response_data()
        mock_session.exec.return_value = (_mock_response(200), data)
        result = client.get_policy(models.GetPolicyRequest(policy_id=1))
        assert result.cloudlet_type == "FR"
        assert result.id == 11
        assert result.name == "TestName"

        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/cloudlets/v3/policies/1"

    def test_200_ok_with_activation_information(self, mock_session, client):
        data = _minimal_policy_response_data()
        data["currentActivations"] = {
            "production": {
                "effective": _activation_data("User1", 123, "Link1", "PRODUCTION", 1234),
                "latest": _activation_data("User1", 321, "Link2", "PRODUCTION", 4321),
            },
            "staging": {
                "effective": _activation_data("User3", 789, "Link3", "STAGING", 6789),
                "latest": _activation_data("User3", 987, "Link4", "STAGING", 9876),
            },
        }
        mock_session.exec.return_value = (_mock_response(200), data)
        result = client.get_policy(models.GetPolicyRequest(policy_id=1))
        act = result.current_activations
        assert act.production.effective.id == 123
        assert act.production.latest.id == 321
        assert act.staging.effective.id == 789
        assert act.staging.latest.id == 987

    def test_404_policy_not_found(self, mock_session, client):
        mock_session.exec.side_effect = _api_error(status=404)
        with pytest.raises(RuntimeError) as exc_info:
            client.get_policy(models.GetPolicyRequest(policy_id=1))
        assert errors.ErrPolicyNotFound in str(exc_info.value)

    def test_500_internal_server_error(self, mock_session, client):
        mock_session.exec.side_effect = _api_error()
        with pytest.raises(RuntimeError) as exc_info:
            client.get_policy(models.GetPolicyRequest(policy_id=1))
        assert errors.ErrGetPolicy in str(exc_info.value)

    def test_validation_errors_missing_required_param(self):
        err = validation.validate_get_policy_request(
            models.GetPolicyRequest()
        )
        assert err is not None
        assert "PolicyID: cannot be blank" in err


# ===================================================================
# TestUpdatePolicy — from policy_test.go lines 1161-1491
# ===================================================================


class TestUpdatePolicy:
    """Mirrors Go TestUpdatePolicy."""

    def test_200_ok(self, mock_session, client):
        data = _minimal_policy_response_data()
        mock_session.exec.return_value = (_mock_response(200), data)
        params = models.UpdatePolicyRequest(
            policy_id=1,
            body=models.UpdatePolicyRequestBody(
                group_id=1,
                description="Description",
            ),
        )
        result = client.update_policy(params)
        assert result.id == 11

        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "PUT"
        assert call_args[0][1] == "/cloudlets/v3/policies/1"

    def test_200_ok_with_activation_information(self, mock_session, client):
        data = _policy_with_activations_data()
        mock_session.exec.return_value = (_mock_response(200), data)
        params = models.UpdatePolicyRequest(
            policy_id=1,
            body=models.UpdatePolicyRequestBody(group_id=1),
        )
        result = client.update_policy(params)
        act = result.current_activations
        assert act.production.effective.id == 123

    def test_validation_errors_missing_policy_id(self):
        err = validation.validate_update_policy_request(
            models.UpdatePolicyRequest(
                body=models.UpdatePolicyRequestBody(group_id=1),
            )
        )
        assert err is not None
        assert "PolicyID: cannot be blank" in err

    def test_validation_errors_missing_body(self):
        err = validation.validate_update_policy_request(
            models.UpdatePolicyRequest(policy_id=1)
        )
        assert err is not None
        assert "Body: cannot be blank" in err

    def test_500_internal_server_error(self, mock_session, client):
        mock_session.exec.side_effect = _api_error()
        with pytest.raises(RuntimeError) as exc_info:
            client.update_policy(models.UpdatePolicyRequest(
                policy_id=1,
                body=models.UpdatePolicyRequestBody(group_id=1),
            ))
        assert errors.ErrUpdatePolicy in str(exc_info.value)


# ===================================================================
# TestClonePolicy — from policy_test.go lines 1492-1824
# ===================================================================


class TestClonePolicy:
    """Mirrors Go TestClonePolicy."""

    def test_200_ok(self, mock_session, client):
        data = _minimal_policy_response_data()
        mock_session.exec.return_value = (_mock_response(200), data)
        params = models.ClonePolicyRequest(
            policy_id=1,
            body=models.ClonePolicyRequestBody(
                new_name="ClonedPolicy",
                group_id=1,
            ),
        )
        result = client.clone_policy(params)
        assert result.id == 11

        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/cloudlets/v3/policies/1/clone"

    def test_200_ok_minimal_body(self, mock_session, client):
        data = _minimal_policy_response_data()
        mock_session.exec.return_value = (_mock_response(200), data)
        params = models.ClonePolicyRequest(
            policy_id=1,
            body=models.ClonePolicyRequestBody(new_name="ClonedPolicy"),
        )
        result = client.clone_policy(params)
        assert result.id == 11

    def test_validation_errors_missing_policy_id(self):
        err = validation.validate_clone_policy_request(
            models.ClonePolicyRequest(
                body=models.ClonePolicyRequestBody(new_name="ClonedPolicy"),
            )
        )
        assert err is not None
        assert "PolicyID: cannot be blank" in err

    def test_validation_errors_missing_body(self):
        err = validation.validate_clone_policy_request(
            models.ClonePolicyRequest(policy_id=1)
        )
        assert err is not None
        assert "Body: cannot be blank" in err

    def test_validation_errors_missing_new_name(self):
        err = validation.validate_clone_policy_request(
            models.ClonePolicyRequest(
                policy_id=1,
                body=models.ClonePolicyRequestBody(),
            )
        )
        assert err is not None
        assert "NewName: cannot be blank" in err

    def test_500_internal_server_error(self, mock_session, client):
        mock_session.exec.side_effect = _api_error()
        with pytest.raises(RuntimeError) as exc_info:
            client.clone_policy(models.ClonePolicyRequest(
                policy_id=1,
                body=models.ClonePolicyRequestBody(
                    new_name="ClonedPolicy",
                    group_id=1,
                ),
            ))
        assert errors.ErrClonePolicy in str(exc_info.value)


# ===================================================================
# TestListPolicyActivations — from policy_activation_test.go
# ===================================================================


class TestListPolicyActivations:

    def test_200_ok(self, mock_session, client):
        body = {
            "content": [
                {
                    "createdBy": "testUser",
                    "createdDate": "2023-10-25T10:33:47.982Z",
                    "finishDate": None,
                    "id": 234,
                    "network": "STAGING",
                    "operation": "DEACTIVATION",
                    "policyId": 1234,
                    "status": "IN_PROGRESS",
                    "policyVersion": 1,
                    "policyVersionDeleted": False,
                    "links": [
                        {"href": "/cloudlets/v3/policies/1234/activations/234", "rel": "self"}
                    ]
                },
                {
                    "createdBy": "testUser",
                    "createdDate": "2023-10-23T11:21:19.896Z",
                    "finishDate": "2023-10-23T11:22:57.589Z",
                    "id": 123,
                    "network": "STAGING",
                    "operation": "ACTIVATION",
                    "policyId": 1234,
                    "status": "SUCCESS",
                    "policyVersion": 1,
                    "policyVersionDeleted": False,
                    "links": [
                        {"href": "/cloudlets/v3/policies/1234/activations/123", "rel": "self"}
                    ]
                },
            ],
            "page": {
                "number": 0,
                "size": 1000,
                "totalElements": 2,
                "totalPages": 1,
            },
            "links": [
                {"href": "/cloudlets/v3/policies/1234/activations?page=0&size=1000", "rel": "self"}
            ],
        }
        mock_session.exec.return_value = (_mock_response(200), body)
        result = client.list_policy_activations(
            models.ListPolicyActivationsRequest(policy_id=1234)
        )
        assert result.page.number == 0
        assert result.page.total_elements == 2
        assert len(result.policy_activations) == 2
        act0 = result.policy_activations[0]
        assert act0.id == 234
        assert act0.operation == "DEACTIVATION"
        assert act0.status == "IN_PROGRESS"
        assert act0.finish_date is None
        act1 = result.policy_activations[1]
        assert act1.id == 123
        assert act1.operation == "ACTIVATION"
        assert act1.status == "SUCCESS"
        assert act1.finish_date == "2023-10-23T11:22:57.589Z"
        call_args = mock_session.exec.call_args
        assert call_args[0][1] == "/cloudlets/v3/policies/1234/activations"

    def test_200_ok_with_query_params(self, mock_session, client):
        body = {
            "content": [],
            "page": {
                "number": 1,
                "size": 10,
                "totalElements": 0,
                "totalPages": 0,
            },
            "links": [
                {"href": "/cloudlets/v3/policies/1234/activations?page=0&size=10", "rel": "first"},
                {"href": "/cloudlets/v3/policies/1234/activations?page=0&size=10", "rel": "prev"},
                {"href": "/cloudlets/v3/policies/1234/activations?page=1&size=10", "rel": "self"},
                {"href": "/cloudlets/v3/policies/1234/activations?page=0&size=10", "rel": "last"},
            ],
        }
        mock_session.exec.return_value = (_mock_response(200), body)
        result = client.list_policy_activations(
            models.ListPolicyActivationsRequest(policy_id=1234, page=1, size=10)
        )
        assert result.page.number == 1
        assert result.page.size == 10
        assert len(result.links) == 4

    def test_500_internal_server_error(self, mock_session, client):
        mock_session.exec.side_effect = _api_error()
        with pytest.raises(RuntimeError) as exc_info:
            client.list_policy_activations(
                models.ListPolicyActivationsRequest(policy_id=1234)
            )
        assert errors.ErrListPolicyActivations in str(exc_info.value)

    def test_validation_errors(self):
        err = validation.validate_list_policy_activations_request(
            models.ListPolicyActivationsRequest(page=-1, size=5)
        )
        assert err is not None
        assert "PolicyID: cannot be blank" in err


# ===================================================================
# TestActivatePolicy — from policy_activation_test.go
# ===================================================================


class TestActivatePolicy:

    def test_202_accepted(self, mock_session, client):
        body = {
            "createdBy": "testUser",
            "createdDate": "2023-10-25T10:33:47.982Z",
            "finishDate": None,
            "id": 123,
            "network": "STAGING",
            "operation": "ACTIVATION",
            "policyId": 1234,
            "status": "IN_PROGRESS",
            "policyVersion": 1,
            "policyVersionDeleted": False,
        }
        mock_session.exec.return_value = (_mock_response(202), body)
        result = client.activate_policy(
            models.ActivatePolicyRequest(
                policy_id=1234,
                network=models.StagingNetwork,
                policy_version=1,
            )
        )
        assert result.id == 123
        assert result.network == "STAGING"
        assert result.operation == "ACTIVATION"
        assert result.status == "IN_PROGRESS"
        assert result.finish_date is None
        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/cloudlets/v3/policies/1234/activations"

    def test_500_internal_server_error(self, mock_session, client):
        mock_session.exec.side_effect = _api_error()
        with pytest.raises(RuntimeError) as exc_info:
            client.activate_policy(
                models.ActivatePolicyRequest(
                    policy_id=1234,
                    network=models.StagingNetwork,
                    policy_version=1,
                )
            )
        assert errors.ErrActivatePolicy in str(exc_info.value)

    def test_validation_errors(self):
        err = validation.validate_activate_policy_request(
            models.ActivatePolicyRequest()
        )
        assert err is not None
        assert "PolicyID: cannot be blank" in err
        assert "PolicyVersion: cannot be blank" in err
        assert "Network: cannot be blank" in err


# ===================================================================
# TestDeactivatePolicy — from policy_activation_test.go
# ===================================================================


class TestDeactivatePolicy:

    def test_202_accepted(self, mock_session, client):
        body = {
            "createdBy": "testUser",
            "createdDate": "2023-10-25T10:33:47.982Z",
            "finishDate": None,
            "id": 123,
            "network": "STAGING",
            "operation": "DEACTIVATION",
            "policyId": 1234,
            "status": "IN_PROGRESS",
            "policyVersion": 1,
            "policyVersionDeleted": False,
        }
        mock_session.exec.return_value = (_mock_response(202), body)
        result = client.deactivate_policy(
            models.DeactivatePolicyRequest(
                policy_id=1234,
                network=models.StagingNetwork,
                policy_version=1,
            )
        )
        assert result.id == 123
        assert result.operation == "DEACTIVATION"
        assert result.status == "IN_PROGRESS"
        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/cloudlets/v3/policies/1234/activations"

    def test_500_internal_server_error(self, mock_session, client):
        mock_session.exec.side_effect = _api_error()
        with pytest.raises(RuntimeError) as exc_info:
            client.deactivate_policy(
                models.DeactivatePolicyRequest(
                    policy_id=1234,
                    network=models.ProductionNetwork,
                    policy_version=1,
                )
            )
        assert errors.ErrDeactivatePolicy in str(exc_info.value)

    def test_validation_errors(self):
        err = validation.validate_deactivate_policy_request(
            models.DeactivatePolicyRequest(network="OTHER")
        )
        assert err is not None
        assert "PolicyID: cannot be blank" in err
        assert "PolicyVersion: cannot be blank" in err
        assert "Network:" in err


# ===================================================================
# TestGetPolicyActivation — from policy_activation_test.go
# ===================================================================


class TestGetPolicyActivation:

    def test_200_ok(self, mock_session, client):
        body = {
            "createdBy": "testUser",
            "createdDate": "2023-10-23T11:21:19.896Z",
            "finishDate": "2023-10-23T11:22:57.589Z",
            "id": 123,
            "network": "STAGING",
            "operation": "ACTIVATION",
            "policyId": 1234,
            "status": "SUCCESS",
            "policyVersion": 1,
            "policyVersionDeleted": False,
            "links": [
                {"href": "/cloudlets/v3/policies/1234/activations/123", "rel": "self"}
            ],
        }
        mock_session.exec.return_value = (_mock_response(200), body)
        result = client.get_policy_activation(
            models.GetPolicyActivationRequest(policy_id=1234, activation_id=123)
        )
        assert result.id == 123
        assert result.status == "SUCCESS"
        assert result.finish_date == "2023-10-23T11:22:57.589Z"
        assert result.created_date == "2023-10-23T11:21:19.896Z"
        call_args = mock_session.exec.call_args
        assert call_args[0][1] == "/cloudlets/v3/policies/1234/activations/123"

    def test_404_not_found(self, mock_session, client):
        err_body = {
            "type": "/cloudlets/v3/error-types/not-found",
            "title": "Not found",
            "instance": "testInstance",
            "status": 404,
            "errors": [{"detail": "Activation with id '1' not found.", "title": "Not found"}],
        }
        mock_session.exec.side_effect = _api_error(body=err_body, status=404)
        with pytest.raises(RuntimeError) as exc_info:
            client.get_policy_activation(
                models.GetPolicyActivationRequest(policy_id=1234, activation_id=1)
            )
        assert errors.ErrGetPolicyActivation in str(exc_info.value)

    def test_500_internal_server_error(self, mock_session, client):
        mock_session.exec.side_effect = _api_error()
        with pytest.raises(RuntimeError) as exc_info:
            client.get_policy_activation(
                models.GetPolicyActivationRequest(policy_id=1234, activation_id=123)
            )
        assert errors.ErrGetPolicyActivation in str(exc_info.value)

    def test_validation_errors(self):
        err = validation.validate_get_policy_activation_request(
            models.GetPolicyActivationRequest()
        )
        assert err is not None
        assert "PolicyID: cannot be blank" in err
        assert "ActivationID: cannot be blank" in err


# ===================================================================
# TestListActivePolicyProperties — from policy_property_test.go
# ===================================================================


class TestListActivePolicyProperties:

    def test_200_ok_no_query_params(self, mock_session, client):
        body = {
            "page": {
                "number": 0, "size": 1000,
                "totalElements": 2, "totalPages": 1,
            },
            "content": [
                {
                    "groupId": 5, "id": 1234, "name": "property",
                    "network": "PRODUCTION", "version": 1,
                },
                {
                    "groupId": 5, "id": 1233, "name": "property",
                    "network": "STAGING", "version": 1,
                },
            ],
            "links": [
                {"href": "/cloudlets/v3/policies/101/properties?page=0&size=1000", "rel": "self"}
            ],
        }
        mock_session.exec.return_value = (_mock_response(200), body)
        result = client.list_active_policy_properties(
            models.ListActivePolicyPropertiesRequest(policy_id=5)
        )
        assert len(result.policy_properties) == 2
        assert result.policy_properties[0].name == "property"
        assert result.policy_properties[0].id == 1234
        assert result.policy_properties[0].network == "PRODUCTION"
        assert result.policy_properties[1].id == 1233
        assert result.policy_properties[1].network == "STAGING"
        assert result.page.total_elements == 2

    def test_200_ok_with_query_params(self, mock_session, client):
        body = {
            "content": [],
            "page": {
                "number": 50,
                "size": 1000,
                "totalElements": 0,
                "totalPages": 0,
            },
            "links": [],
        }
        mock_session.exec.return_value = (_mock_response(200), body)
        result = client.list_active_policy_properties(
            models.ListActivePolicyPropertiesRequest(policy_id=5, page=50, size=1000)
        )
        assert result.page.number == 50

    def test_200_ok_empty(self, mock_session, client):
        body = {
            "content": [],
            "page": {
                "number": 0,
                "size": 1000,
                "totalElements": 0,
                "totalPages": 0,
            },
            "links": [],
        }
        mock_session.exec.return_value = (_mock_response(200), body)
        result = client.list_active_policy_properties(
            models.ListActivePolicyPropertiesRequest(policy_id=5, size=1000)
        )
        assert result.policy_properties is None or len(result.policy_properties) == 0

    def test_validation_errors_missing_required(self):
        err = validation.validate_list_active_policy_properties_request(
            models.ListActivePolicyPropertiesRequest()
        )
        assert err is not None
        assert "PolicyID: cannot be blank" in err

    def test_validation_errors_size_and_page(self):
        err = validation.validate_list_active_policy_properties_request(
            models.ListActivePolicyPropertiesRequest(policy_id=1, page=-2, size=5)
        )
        assert err is not None
        assert "Page: must be no less than 0" in err
        assert "Size: must be no less than 10" in err

    def test_500_internal_server_error(self, mock_session, client):
        mock_session.exec.side_effect = _api_error()
        with pytest.raises(RuntimeError) as exc_info:
            client.list_active_policy_properties(
                models.ListActivePolicyPropertiesRequest(policy_id=1)
            )
        assert errors.ErrListActivePolicyProperties in str(exc_info.value)

    def test_404_not_found(self, mock_session, client):
        err_body = {
            "type": "/cloudlets/v3/error-types/not-found",
            "title": "Not found",
            "instance": "TestInstance",
            "status": 404,
            "errors": [{"detail": "Policy with id 1 not found.", "title": "Not found"}],
        }
        mock_session.exec.side_effect = _api_error(body=err_body, status=404)
        with pytest.raises(RuntimeError) as exc_info:
            client.list_active_policy_properties(
                models.ListActivePolicyPropertiesRequest(policy_id=1)
            )
        assert errors.ErrListActivePolicyProperties in str(exc_info.value)


# ===================================================================
# TestListPolicyVersions — from policy_version_test.go
# ===================================================================


class TestListPolicyVersions:

    def test_200_ok(self, mock_session, client):
        body = {
            "content": [
                {
                    "createdBy": "jsmith",
                    "createdDate": "2023-10-19T08:50:47.350Z",
                    "description": None,
                    "immutable": False,
                    "modifiedBy": "jsmith",
                    "modifiedDate": "2023-10-19T08:50:47.350Z",
                    "policyId": 670790,
                    "version": 3,
                },
                {
                    "createdBy": "jsmith",
                    "createdDate": "2023-10-18T07:44:25.854Z",
                    "description": None,
                    "immutable": True,
                    "modifiedBy": "jsmith",
                    "modifiedDate": "2023-10-18T07:44:25.854Z",
                    "policyId": 670790,
                    "version": 2,
                },
                {
                    "createdBy": "jsmith",
                    "createdDate": "2023-10-17T12:09:10.326Z",
                    "description": "Description for the first version",
                    "immutable": True,
                    "modifiedBy": "jsmith",
                    "modifiedDate": "2023-10-17T12:16:33.533Z",
                    "policyId": 670790,
                    "version": 1,
                },
            ],
            "page": {
                "number": 0,
                "size": 1000,
                "totalElements": 3,
                "totalPages": 1,
            },
            "links": [
                {"href": "/cloudlets/v3/policies/670790/versions?page=0&size=1000", "rel": "self"}
            ],
        }
        mock_session.exec.return_value = (_mock_response(200), body)
        result = client.list_policy_versions(
            models.ListPolicyVersionsRequest(policy_id=670790)
        )
        assert len(result.policy_versions) == 3
        assert result.policy_versions[0].policy_version == 3
        assert result.policy_versions[2].description == "Description for the first version"
        assert result.page.total_elements == 3
        call_args = mock_session.exec.call_args
        assert "/cloudlets/v3/policies/670790/versions" in call_args[0][1]

    def test_200_ok_with_params(self, mock_session, client):
        body = {
            "content": [],
            "page": {
                "number": 4,
                "size": 10,
                "totalElements": 0,
                "totalPages": 0,
            },
            "links": [
                {"href": "/cloudlets/v3/policies/670790/versions?page=0&size=10", "rel": "first"},
                {"href": "/cloudlets/v3/policies/670790/versions?page=3&size=10", "rel": "prev"},
                {"href": "/cloudlets/v3/policies/670790/versions?page=4&size=10", "rel": "self"},
                {"href": "/cloudlets/v3/policies/670790/versions?page=4&size=10", "rel": "last"},
            ],
        }
        mock_session.exec.return_value = (_mock_response(200), body)
        result = client.list_policy_versions(
            models.ListPolicyVersionsRequest(policy_id=670790, page=4, size=10)
        )
        assert result.page.number == 4
        assert len(result.links) == 4

    def test_500_internal_server_error(self, mock_session, client):
        mock_session.exec.side_effect = _api_error()
        with pytest.raises(RuntimeError) as exc_info:
            client.list_policy_versions(
                models.ListPolicyVersionsRequest(policy_id=284823)
            )
        assert errors.ErrListPolicyVersions in str(exc_info.value)


# ===================================================================
# TestGetPolicyVersion — from policy_version_test.go
# ===================================================================


class TestGetPolicyVersion:

    def test_200_ok_no_match_rules(self, mock_session, client):
        body = {
            "createdBy": "jsmith",
            "createdDate": "2023-10-17T12:09:10.326Z",
            "description": "test description",
            "immutable": False,
            "matchRules": None,
            "modifiedBy": "jsmith",
            "modifiedDate": "2023-10-17T12:16:33.533Z",
            "policyId": 670798,
            "version": 2,
        }
        mock_session.exec.return_value = (_mock_response(200), body)
        result = client.get_policy_version(
            models.GetPolicyVersionRequest(policy_id=670798, policy_version=2)
        )
        assert result.policy_id == 670798
        assert result.policy_version == 2
        assert result.description == "test description"
        assert result.match_rules is None
        call_args = mock_session.exec.call_args
        assert call_args[0][1] == "/cloudlets/v3/policies/670798/versions/2"

    def test_200_ok_er_with_disabled_rule(self, mock_session, client):
        body = {
            "createdBy": "jsmith",
            "createdDate": "2023-10-19T08:50:47.350Z",
            "description": None,
            "modifiedBy": "jsmith",
            "modifiedDate": "2023-10-19T08:50:47.350Z",
            "matchRules": [
                {
                    "type": "erMatchRule",
                    "end": 0,
                    "id": 0,
                    "matchURL": None,
                    "name": "er_rule",
                    "redirectURL": "/path",
                    "start": 0,
                    "statusCode": 301,
                    "useIncomingQueryString": False,
                    "useIncomingSchemeAndHost": False,
                    "useRelativeUrl": "none",
                    "disabled": True,
                }
            ],
            "policyId": 276858,
            "version": 1,
        }
        mock_session.exec.return_value = (_mock_response(200), body)
        result = client.get_policy_version(
            models.GetPolicyVersionRequest(policy_id=276858, policy_version=1)
        )
        assert len(result.match_rules) == 1
        rule = result.match_rules[0]
        assert isinstance(rule, models.MatchRuleER)
        assert rule.name == "er_rule"
        assert rule.disabled is True
        assert rule.status_code == 301
        assert rule.redirect_url == "/path"
        assert rule.use_relative_url == "none"

    def test_200_ok_as_rule(self, mock_session, client):
        body = {
            "createdBy": "jsmith",
            "createdDate": "2023-10-19T08:50:47.350Z",
            "description": None,
            "modifiedBy": "jsmith",
            "modifiedDate": "2023-10-19T08:50:47.350Z",
            "matchRules": [
                {
                    "type": "asMatchRule",
                    "end": 0,
                    "id": 0,
                    "matchURL": None,
                    "matches": [
                        {
                            "caseSensitive": False,
                            "matchOperator": "equals",
                            "matchType": "range",
                            "negate": False,
                            "objectMatchValue": {
                                "type": "range",
                                "value": [1, 25]
                            }
                        }
                    ],
                    "name": "as_rule",
                    "start": 0,
                    "disabled": False,
                    "forwardSettings": {
                        "originId": "originremote2",
                        "pathAndQS": None,
                        "useIncomingQueryString": False,
                    }
                }
            ],
            "policyId": 355557,
            "version": 2,
        }
        mock_session.exec.return_value = (_mock_response(200), body)
        result = client.get_policy_version(
            models.GetPolicyVersionRequest(policy_id=355557, policy_version=2)
        )
        assert len(result.match_rules) == 1
        rule = result.match_rules[0]
        assert isinstance(rule, models.MatchRuleAS)
        assert rule.forward_settings.origin_id == "originremote2"

    def test_200_ok_pr_rule(self, mock_session, client):
        body = {
            "createdBy": "jsmith",
            "createdDate": "2023-10-19T08:50:47.350Z",
            "description": None,
            "modifiedBy": "jsmith",
            "modifiedDate": "2023-10-19T08:50:47.350Z",
            "matchRules": [
                {
                    "type": "cdMatchRule",
                    "end": 0,
                    "id": 0,
                    "matchURL": None,
                    "matches": [
                        {
                            "caseSensitive": False,
                            "matchOperator": "equals",
                            "matchType": "method",
                            "negate": False,
                            "objectMatchValue": {
                                "type": "simple",
                                "value": ["GET"]
                            }
                        }
                    ],
                    "name": "pr_rule",
                    "start": 0,
                    "forwardSettings": {
                        "originId": "fr_test_krk_dc2",
                        "percent": 11
                    }
                }
            ],
            "policyId": 276858,
            "version": 6,
        }
        mock_session.exec.return_value = (_mock_response(200), body)
        result = client.get_policy_version(
            models.GetPolicyVersionRequest(policy_id=276858, policy_version=6)
        )
        assert len(result.match_rules) == 1
        rule = result.match_rules[0]
        assert isinstance(rule, models.MatchRulePR)
        assert rule.forward_settings.origin_id == "fr_test_krk_dc2"
        assert rule.forward_settings.percent == 11

    def test_200_ok_er_rule_with_disabled_false(self, mock_session, client):
        body = {
            "createdBy": "jsmith",
            "createdDate": "2023-10-19T08:50:47.350Z",
            "description": None,
            "modifiedBy": "jsmith",
            "modifiedDate": "2023-10-19T08:50:47.350Z",
            "matchRules": [
                {
                    "type": "erMatchRule",
                    "end": 0,
                    "id": 0,
                    "matchURL": None,
                    "name": "rul3",
                    "redirectURL": "/abc/sss",
                    "start": 0,
                    "statusCode": 307,
                    "useIncomingQueryString": False,
                    "useIncomingSchemeAndHost": True,
                    "useRelativeUrl": "copy_scheme_hostname",
                    "disabled": False,
                }
            ],
            "policyId": 276858,
            "version": 6,
        }
        mock_session.exec.return_value = (_mock_response(200), body)
        result = client.get_policy_version(
            models.GetPolicyVersionRequest(policy_id=276858, policy_version=6)
        )
        rule = result.match_rules[0]
        assert isinstance(rule, models.MatchRuleER)
        assert rule.use_relative_url == "copy_scheme_hostname"
        assert rule.use_incoming_scheme_and_host is True
        assert rule.status_code == 307

    def test_200_ok_fr_with_disabled_rule(self, mock_session, client):
        body = {
            "createdBy": "jsmith",
            "createdDate": "2023-10-19T08:50:47.350Z",
            "description": None,
            "modifiedBy": "jsmith",
            "modifiedDate": "2023-10-19T08:50:47.350Z",
            "matchRules": [
                {
                    "type": "frMatchRule",
                    "end": 0,
                    "id": 0,
                    "matchURL": None,
                    "name": "rule 1",
                    "start": 0,
                    "disabled": True,
                    "forwardSettings": {
                        "pathAndQS": "/test_images/simpleimg.jpg",
                        "useIncomingQueryString": True,
                        "originId": "1234"
                    }
                }
            ],
            "policyId": 276858,
            "version": 6,
        }
        mock_session.exec.return_value = (_mock_response(200), body)
        result = client.get_policy_version(
            models.GetPolicyVersionRequest(policy_id=276858, policy_version=6)
        )
        rule = result.match_rules[0]
        assert isinstance(rule, models.MatchRuleFR)
        assert rule.disabled is True
        assert rule.forward_settings.path_and_qs == "/test_images/simpleimg.jpg"

    def test_500_internal_server_error(self, mock_session, client):
        mock_session.exec.side_effect = _api_error()
        with pytest.raises(RuntimeError) as exc_info:
            client.get_policy_version(
                models.GetPolicyVersionRequest(policy_id=1, policy_version=2)
            )
        assert errors.ErrGetPolicyVersion in str(exc_info.value)


# ===================================================================
# TestCreatePolicyVersion — from policy_version_test.go
# ===================================================================


class TestCreatePolicyVersion:

    def test_201_simple_er(self, mock_session, client):
        body = {
            "createdBy": "jsmith",
            "createdDate": "2023-10-19T08:50:47.350Z",
            "description": "Description for the policy",
            "modifiedBy": "jsmith",
            "modifiedDate": "2023-10-19T08:50:47.350Z",
            "matchRules": None,
            "policyId": 276858,
            "version": 2,
        }
        mock_session.exec.return_value = (_mock_response(201), body)
        result = client.create_policy_version(
            models.CreatePolicyVersionRequest(
                policy_id=276858,
                create_policy_version=models.CreatePolicyVersion(
                    description="Description for the policy",
                ),
            )
        )
        assert result.policy_id == 276858
        assert result.policy_version == 2
        assert result.description == "Description for the policy"
        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/cloudlets/v3/policies/276858/versions"

    def test_201_complex_as(self, mock_session, client):
        body = {
            "createdBy": "jsmith",
            "createdDate": "2023-10-19T08:50:47.350Z",
            "description": None,
            "modifiedBy": "jsmith",
            "modifiedDate": "2023-10-19T08:50:47.350Z",
            "matchRules": [
                {
                    "type": "asMatchRule",
                    "end": 0,
                    "id": 0,
                    "matchURL": None,
                    "matches": [
                        {
                            "caseSensitive": False,
                            "matchOperator": "equals",
                            "matchType": "range",
                            "negate": False,
                            "objectMatchValue": {
                                "type": "range",
                                "value": [1, 25]
                            }
                        },
                        {
                            "caseSensitive": False,
                            "matchOperator": "equals",
                            "matchType": "method",
                            "negate": False,
                            "objectMatchValue": {
                                "type": "simple",
                                "value": ["GET"]
                            }
                        },
                        {
                            "caseSensitive": False,
                            "matchOperator": "equals",
                            "matchType": "header",
                            "negate": False,
                            "objectMatchValue": {
                                "type": "object",
                                "name": "AS",
                                "options": {
                                    "value": ["text/html*", "text/css*", "application/x-javascript*"],
                                    "valueHasWildcard": True
                                }
                            }
                        }
                    ],
                    "name": "rul3",
                    "start": 0,
                    "forwardSettings": {
                        "originId": "originremote2",
                        "pathAndQS": None,
                        "useIncomingQueryString": False
                    }
                }
            ],
            "policyId": 355557,
            "version": 2,
        }
        mock_session.exec.return_value = (_mock_response(201), body)
        result = client.create_policy_version(
            models.CreatePolicyVersionRequest(
                policy_id=355557,
                create_policy_version=models.CreatePolicyVersion(
                    match_rules=[
                        models.MatchRuleAS(
                            type="asMatchRule",
                            name="rul3",
                            matches=[
                                models.MatchCriteria(
                                    match_operator="equals",
                                    match_type="range",
                                    object_match_value=models.ObjectMatchValueRange(
                                        type="range", value=[1, 25]
                                    ),
                                ),
                                models.MatchCriteria(
                                    match_operator="equals",
                                    match_type="method",
                                    object_match_value=models.ObjectMatchValueSimple(
                                        type="simple", value=["GET"]
                                    ),
                                ),
                                models.MatchCriteria(
                                    match_operator="equals",
                                    match_type="header",
                                    object_match_value=models.ObjectMatchValueObject(
                                        type="object",
                                        name="AS",
                                        options=models.Options(
                                            value=["text/html*", "text/css*", "application/x-javascript*"],
                                            value_has_wildcard=True,
                                        ),
                                    ),
                                ),
                            ],
                            forward_settings=models.ForwardSettingsAS(
                                origin_id="originremote2",
                            ),
                        ),
                    ],
                ),
            )
        )
        assert result.policy_id == 355557
        assert len(result.match_rules) == 1
        assert isinstance(result.match_rules[0], models.MatchRuleAS)

    def test_201_complex_pr(self, mock_session, client):
        body = {
            "createdBy": "jsmith",
            "createdDate": "2023-10-19T08:50:47.350Z",
            "description": None,
            "modifiedBy": "jsmith",
            "modifiedDate": "2023-10-19T08:50:47.350Z",
            "matchRules": [
                {
                    "type": "cdMatchRule",
                    "end": 0,
                    "id": 0,
                    "matchURL": None,
                    "matches": [
                        {"caseSensitive": True, "matchOperator": "equals", "matchType": "hostname", "matchValue": "3333.dom", "negate": False},
                        {"caseSensitive": False, "matchOperator": "equals", "matchType": "cookie", "matchValue": "cookie=cookievalue", "negate": False},
                        {"caseSensitive": False, "matchOperator": "equals", "matchType": "extension", "matchValue": "txt", "negate": False}
                    ],
                    "name": "rul3",
                    "start": 0,
                    "forwardSettings": {"originId": "some_origin", "percent": 10}
                },
                {
                    "type": "cdMatchRule",
                    "end": 0,
                    "id": 0,
                    "matchURL": "ddd.aaa",
                    "name": "rule 2",
                    "start": 0,
                    "forwardSettings": {"originId": "some_origin", "percent": 10}
                },
                {
                    "type": "cdMatchRule",
                    "end": 0,
                    "id": 0,
                    "matchURL": "abc.com",
                    "name": "r1",
                    "start": 0,
                    "forwardSettings": {"originId": "some_origin", "percent": 10}
                }
            ],
            "policyId": 276858,
            "version": 6,
        }
        mock_session.exec.return_value = (_mock_response(201), body)
        result = client.create_policy_version(
            models.CreatePolicyVersionRequest(
                policy_id=276858,
                create_policy_version=models.CreatePolicyVersion(
                    match_rules=[
                        models.MatchRulePR(
                            type="cdMatchRule", name="rul3",
                            forward_settings=models.ForwardSettingsPR(origin_id="some_origin", percent=10),
                            matches=[
                                models.MatchCriteria(case_sensitive=True, match_operator="equals", match_type="hostname", match_value="3333.dom"),
                                models.MatchCriteria(match_operator="equals", match_type="cookie", match_value="cookie=cookievalue"),
                                models.MatchCriteria(match_operator="equals", match_type="extension", match_value="txt"),
                            ],
                        ),
                        models.MatchRulePR(type="cdMatchRule", name="rule 2", match_url="ddd.aaa",
                                           forward_settings=models.ForwardSettingsPR(origin_id="some_origin", percent=10)),
                        models.MatchRulePR(type="cdMatchRule", name="r1", match_url="abc.com",
                                           forward_settings=models.ForwardSettingsPR(origin_id="some_origin", percent=10)),
                    ],
                ),
            )
        )
        assert result.policy_id == 276858
        assert len(result.match_rules) == 3
        assert isinstance(result.match_rules[0], models.MatchRulePR)
        assert result.match_rules[1].match_url == "ddd.aaa"

    def test_201_complex_er(self, mock_session, client):
        body = {
            "createdBy": "jsmith",
            "createdDate": "2023-10-19T08:50:47.350Z",
            "description": None,
            "modifiedBy": "jsmith",
            "modifiedDate": "2023-10-19T08:50:47.350Z",
            "matchRules": [
                {
                    "type": "erMatchRule", "end": 0, "id": 0, "matchURL": None,
                    "matches": [
                        {"caseSensitive": True, "matchOperator": "equals", "matchType": "hostname", "matchValue": "3333.dom", "negate": False},
                        {"caseSensitive": False, "matchOperator": "equals", "matchType": "cookie", "matchValue": "cookie=cookievalue", "negate": False},
                        {"caseSensitive": False, "matchOperator": "equals", "matchType": "extension", "matchValue": "txt", "negate": False}
                    ],
                    "name": "rul3", "redirectURL": "/abc/sss", "start": 0, "statusCode": 307,
                    "useIncomingQueryString": False, "useIncomingSchemeAndHost": True, "useRelativeUrl": "copy_scheme_hostname"
                },
                {
                    "type": "erMatchRule", "end": 0, "id": 0, "matchURL": "ddd.aaa",
                    "name": "rule 2", "redirectURL": "sss.com", "start": 0, "statusCode": 301,
                    "useIncomingQueryString": True, "useRelativeUrl": "none"
                },
                {
                    "type": "erMatchRule", "end": 0, "id": 0, "matchURL": "abc.com",
                    "name": "r1", "redirectURL": "/ddd", "start": 0, "statusCode": 301,
                    "useIncomingQueryString": False, "useIncomingSchemeAndHost": True, "useRelativeUrl": "copy_scheme_hostname"
                }
            ],
            "policyId": 276858,
            "version": 6,
        }
        mock_session.exec.return_value = (_mock_response(201), body)
        result = client.create_policy_version(
            models.CreatePolicyVersionRequest(policy_id=276858, create_policy_version=models.CreatePolicyVersion(
                match_rules=[
                    models.MatchRuleER(type="erMatchRule", name="rul3", use_relative_url="copy_scheme_hostname",
                                       status_code=307, redirect_url="/abc/sss",
                                       matches=[
                                           models.MatchCriteria(case_sensitive=True, match_operator="equals", match_type="hostname", match_value="3333.dom"),
                                           models.MatchCriteria(match_operator="equals", match_type="cookie", match_value="cookie=cookievalue"),
                                           models.MatchCriteria(match_operator="equals", match_type="extension", match_value="txt"),
                                       ]),
                    models.MatchRuleER(type="erMatchRule", name="rule 2", match_url="ddd.aaa", redirect_url="sss.com",
                                       status_code=301, use_relative_url="none", use_incoming_query_string=True),
                    models.MatchRuleER(type="erMatchRule", name="r1", match_url="abc.com", status_code=301, redirect_url="/ddd",
                                       use_incoming_scheme_and_host=True, use_relative_url="copy_scheme_hostname"),
                ],
            ))
        )
        assert len(result.match_rules) == 3
        assert result.match_rules[0].status_code == 307

    def test_201_complex_fr(self, mock_session, client):
        body = {
            "createdBy": "jsmith",
            "createdDate": "2023-10-19T08:50:47.350Z",
            "description": None,
            "modifiedBy": "jsmith",
            "modifiedDate": "2023-10-19T08:50:47.350Z",
            "matchRules": [
                {
                    "type": "frMatchRule", "akaRuleId": "893947a3d5a85c1b", "end": 0,
                    "forwardSettings": {"pathAndQS": "/test_images/otherimage.jpg", "useIncomingQueryString": True, "originId": "1234"},
                    "id": 0, "matchURL": None,
                    "matches": [
                        {"caseSensitive": True, "matchOperator": "equals", "matchType": "hostname", "matchValue": "3333.dom", "negate": False},
                        {"caseSensitive": False, "matchOperator": "equals", "matchType": "cookie", "matchValue": "cookie=cookievalue", "negate": False},
                        {"caseSensitive": False, "matchOperator": "equals", "matchType": "extension", "matchValue": "txt", "negate": False}
                    ],
                    "name": "rul3", "start": 0
                },
                {
                    "type": "frMatchRule", "akaRuleId": "aa379d230efcded0", "end": 0,
                    "forwardSettings": {"pathAndQS": "/test_images/simpleimg.jpg", "useIncomingQueryString": True, "originId": "1234"},
                    "id": 0, "matchURL": "ddd.aaa", "name": "rule 1", "start": 0
                },
                {
                    "type": "frMatchRule", "akaRuleId": "1afe03d843996766", "end": 0,
                    "forwardSettings": {"pathAndQS": "/test_images/otherimage.jpg", "useIncomingQueryString": True, "originId": "1234"},
                    "id": 0, "matchURL": "abc.com", "name": "rule 2", "start": 0
                }
            ],
            "policyId": 276858,
            "version": 6,
        }
        mock_session.exec.return_value = (_mock_response(201), body)
        result = client.create_policy_version(
            models.CreatePolicyVersionRequest(policy_id=276858, create_policy_version=models.CreatePolicyVersion(
                match_rules=[
                    models.MatchRuleFR(type="frMatchRule", name="rul3",
                                       forward_settings=models.ForwardSettingsFR(path_and_qs="/test_images/simpleimg.jpg", use_incoming_query_string=True, origin_id="1234"),
                                       matches=[
                                           models.MatchCriteria(case_sensitive=True, match_operator="equals", match_type="hostname", match_value="3333.dom"),
                                           models.MatchCriteria(match_operator="equals", match_type="cookie", match_value="cookie=cookievalue"),
                                           models.MatchCriteria(match_operator="equals", match_type="extension", match_value="txt"),
                                       ]),
                    models.MatchRuleFR(type="frMatchRule", name="rule 1", match_url="ddd.aaa",
                                       forward_settings=models.ForwardSettingsFR(path_and_qs="/test_images/simpleimg.jpg", use_incoming_query_string=True, origin_id="1234")),
                    models.MatchRuleFR(type="frMatchRule", name="rule 2", match_url="abc.com",
                                       forward_settings=models.ForwardSettingsFR(path_and_qs="/test_images/otherimage.jpg", use_incoming_query_string=True, origin_id="1234")),
                ],
            ))
        )
        assert len(result.match_rules) == 3
        assert isinstance(result.match_rules[0], models.MatchRuleFR)

    def test_201_complex_ap_simple(self, mock_session, client):
        body = {
            "createdBy": "jsmith",
            "createdDate": "2023-10-19T08:50:47.350Z",
            "description": None,
            "modifiedBy": "jsmith",
            "modifiedDate": "2023-10-19T08:50:47.350Z",
            "matchRules": [
                {
                    "type": "apMatchRule", "end": 0, "id": 0, "matchURL": None,
                    "matches": [
                        {"caseSensitive": True, "matchOperator": "equals", "matchType": "method", "negate": False,
                         "objectMatchValue": {"type": "simple", "value": ["GET"]}}
                    ],
                    "name": "rul3", "start": 0, "useIncomingQueryString": False, "passThroughPercent": -1
                }
            ],
            "policyId": 276858,
            "version": 6,
        }
        mock_session.exec.return_value = (_mock_response(201), body)
        result = client.create_policy_version(
            models.CreatePolicyVersionRequest(policy_id=276858, create_policy_version=models.CreatePolicyVersion(
                match_rules=[
                    models.MatchRuleAP(type="apMatchRule", name="rul3", pass_through_percent=0.0,
                                       matches=[
                                           models.MatchCriteria(case_sensitive=True, match_operator="equals", match_type="method",
                                                                object_match_value=models.ObjectMatchValueSimple(type="simple", value=["GET"])),
                                       ]),
                ],
            ))
        )
        assert len(result.match_rules) == 1
        assert isinstance(result.match_rules[0], models.MatchRuleAP)

    def test_201_complex_ap_object(self, mock_session, client):
        body = {
            "createdBy": "jsmith",
            "createdDate": "2023-10-19T08:50:47.350Z",
            "description": None,
            "modifiedBy": "jsmith",
            "modifiedDate": None,
            "matchRules": [
                {
                    "type": "apMatchRule", "end": 0, "id": 0, "matchURL": None,
                    "matches": [
                        {"caseSensitive": False, "matchOperator": "equals", "matchType": "header", "negate": False,
                         "objectMatchValue": {"type": "object", "name": "AP", "options": {"value": ["y"], "valueHasWildcard": True}}}
                    ],
                    "name": "rul3", "start": 0, "passThroughPercent": -1
                }
            ],
            "policyId": 276858,
            "version": 6,
        }
        mock_session.exec.return_value = (_mock_response(201), body)
        result = client.create_policy_version(
            models.CreatePolicyVersionRequest(policy_id=276858, create_policy_version=models.CreatePolicyVersion(
                match_rules=[
                    models.MatchRuleAP(type="apMatchRule", name="rul3", pass_through_percent=-1.0,
                                       matches=[
                                           models.MatchCriteria(match_operator="equals", match_type="header",
                                                                object_match_value=models.ObjectMatchValueObject(
                                                                    type="object", name="AP",
                                                                    options=models.Options(value=["y"], value_has_wildcard=True))),
                                       ]),
                ],
            ))
        )
        assert result.modified_date is None
        assert result.match_rules[0].pass_through_percent == -1.0

    def test_201_complex_rc(self, mock_session, client):
        body = {
            "createdBy": "jsmith",
            "createdDate": "2023-10-19T08:50:47.350Z",
            "description": None,
            "modifiedBy": "jsmith",
            "modifiedDate": "2023-10-19T08:50:47.350Z",
            "matchRules": [
                {
                    "type": "igMatchRule", "end": 0, "id": 0, "matchesAlways": False,
                    "matches": [
                        {"caseSensitive": False, "matchOperator": "equals", "matchType": "protocol", "negate": False, "matchValue": "https"},
                        {"caseSensitive": True, "matchOperator": "equals", "matchType": "method", "negate": False,
                         "objectMatchValue": {"type": "simple", "value": ["GET"]}},
                        {"matchOperator": "equals", "matchType": "header", "negate": False,
                         "objectMatchValue": {"type": "object", "name": "RC",
                                              "options": {"value": ["text/html*", "text/css*", "application/x-javascript*"], "valueHasWildcard": True}}}
                    ],
                    "name": "rul3", "start": 0, "allowDeny": "denybranded"
                }
            ],
            "policyId": 276858,
            "version": 6,
        }
        mock_session.exec.return_value = (_mock_response(201), body)
        result = client.create_policy_version(
            models.CreatePolicyVersionRequest(policy_id=276858, create_policy_version=models.CreatePolicyVersion(
                match_rules=[
                    models.MatchRuleRC(type="igMatchRule", name="rul3", allow_deny="denybranded",
                                       matches=[
                                           models.MatchCriteria(match_operator="equals", match_type="protocol", match_value="https"),
                                           models.MatchCriteria(case_sensitive=True, match_operator="equals", match_type="method",
                                                                object_match_value=models.ObjectMatchValueSimple(type="simple", value=["GET"])),
                                           models.MatchCriteria(match_operator="equals", match_type="header",
                                                                object_match_value=models.ObjectMatchValueObject(
                                                                    type="object", name="RC",
                                                                    options=models.Options(value=["text/html*", "text/css*", "application/x-javascript*"], value_has_wildcard=True))),
                                       ]),
                ],
            ))
        )
        assert len(result.match_rules) == 1
        assert isinstance(result.match_rules[0], models.MatchRuleRC)

    def test_201_complex_pr_omv_simple(self, mock_session, client):
        body = {
            "createdBy": "jsmith", "createdDate": "2023-10-19T08:50:47.350Z",
            "description": None, "modifiedBy": "jsmith",
            "modifiedDate": "2023-10-19T08:50:47.350Z",
            "matchRules": [
                {"type": "cdMatchRule", "end": 0, "id": 0, "matchURL": None,
                 "matches": [
                     {"caseSensitive": False, "matchOperator": "equals", "matchType": "protocol",
                      "matchValue": "https", "negate": False},
                     {"caseSensitive": False, "matchOperator": "equals", "matchType": "method",
                      "negate": False,
                      "objectMatchValue": {"type": "simple", "value": ["GET"]}}
                 ],
                 "name": "rul3", "start": 0,
                 "forwardSettings": {"originId": "some_origin", "percent": 10}
                }
            ],
            "policyId": 276858, "version": 6
        }
        mock_session.exec.return_value = (_mock_response(201), body)
        result = client.create_policy_version(
            models.CreatePolicyVersionRequest(
                policy_id=276858,
                create_policy_version=models.CreatePolicyVersion(
                    match_rules=[
                        models.MatchRulePR(type="cdMatchRule", end=0, match_url=None,
                                           matches=[
                                               models.MatchCriteria(case_sensitive=False, match_operator="equals",
                                                                    match_type="protocol", match_value="https", negate=False),
                                               models.MatchCriteria(case_sensitive=False, match_operator="equals",
                                                                    match_type="method", negate=False,
                                                                    object_match_value=models.ObjectMatchValueSimple(type="simple", value=["GET"])),
                                           ],
                                           name="rul3", start=0,
                                           forward_settings=models.ForwardSettingsPR(origin_id="some_origin", percent=10)),
                    ],
                ),
            )
        )
        assert result.policy_id == 276858
        assert result.policy_version == 6
        assert len(result.match_rules) == 1
        assert isinstance(result.match_rules[0], models.MatchRulePR)
        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/cloudlets/v3/policies/276858/versions"

    def test_201_complex_pr_omv_object(self, mock_session, client):
        body = {
            "createdBy": "jsmith", "createdDate": "2023-10-19T08:50:47.350Z",
            "description": None, "modifiedBy": "jsmith",
            "modifiedDate": "2023-10-19T08:50:47.350Z",
            "matchRules": [
                {"type": "cdMatchRule", "end": 0, "id": 0, "matchURL": None,
                 "matches": [
                     {"caseSensitive": False, "matchOperator": "equals", "matchType": "header",
                      "negate": False,
                      "objectMatchValue": {
                          "type": "object", "name": "PR",
                          "nameCaseSensitive": False, "nameHasWildcard": False,
                          "options": {"value": ["text/html*", "text/css*", "application/x-javascript*"],
                                      "valueCaseSensitive": False, "valueHasWildcard": True}
                      }}
                 ],
                 "name": "rul3", "start": 0,
                 "forwardSettings": {"originId": "some_origin", "percent": 10}
                }
            ],
            "policyId": 276858, "version": 6
        }
        mock_session.exec.return_value = (_mock_response(201), body)
        result = client.create_policy_version(
            models.CreatePolicyVersionRequest(
                policy_id=276858,
                create_policy_version=models.CreatePolicyVersion(
                    match_rules=[
                        models.MatchRulePR(type="cdMatchRule", end=0, match_url=None,
                                           matches=[
                                               models.MatchCriteria(case_sensitive=False, match_operator="equals",
                                                                    match_type="header", negate=False,
                                                                    object_match_value=models.ObjectMatchValueObject(
                                                                        type="object", name="PR",
                                                                        name_case_sensitive=False, name_has_wildcard=False,
                                                                        options=models.Options(
                                                                            value=["text/html*", "text/css*", "application/x-javascript*"],
                                                                            value_case_sensitive=False, value_has_wildcard=True))),
                                           ],
                                           name="rul3", start=0,
                                           forward_settings=models.ForwardSettingsPR(origin_id="some_origin", percent=10)),
                    ],
                ),
            )
        )
        assert result.policy_id == 276858
        assert len(result.match_rules) == 1
        assert isinstance(result.match_rules[0], models.MatchRulePR)

    def test_validation_error_pr_missing_forward_settings(self):
        with pytest.raises(ValueError) as exc_info:
            client = CloudletsV3Client(MagicMock())
            client.create_policy_version(
                models.CreatePolicyVersionRequest(
                    policy_id=276858,
                    create_policy_version=models.CreatePolicyVersion(
                        match_rules=[
                            models.MatchRulePR(type="cdMatchRule",
                                               matches=[
                                                   models.MatchCriteria(case_sensitive=False, match_operator="equals",
                                                                        match_type="hostname", match_value="www.example.com", negate=False),
                                                   models.MatchCriteria(case_sensitive=False, match_operator="equals",
                                                                        match_type="cookie", match_value="session=abc", negate=False),
                                                   models.MatchCriteria(case_sensitive=False, match_operator="equals",
                                                                        match_type="extension", match_value="html", negate=False),
                                               ],
                                               name="rul1"),
                            models.MatchRulePR(type="cdMatchRule", match_url="ddd.aaa", name="rule2"),
                            models.MatchRulePR(type="cdMatchRule", match_url="abc.com", name="r1"),
                        ],
                    ),
                )
            )
        assert errors.ErrStructValidation in str(exc_info.value)

    def test_201_complex_er_omv_simple(self, mock_session, client):
        body = {
            "createdBy": "jsmith", "createdDate": "2023-10-19T08:50:47.350Z",
            "description": None, "modifiedBy": "jsmith",
            "modifiedDate": "2023-10-19T08:50:47.350Z",
            "matchRules": [
                {"type": "erMatchRule", "end": 0, "id": 0, "matchURL": None,
                 "matches": [
                     {"caseSensitive": False, "matchOperator": "equals", "matchType": "protocol",
                      "matchValue": "https", "negate": False},
                     {"caseSensitive": False, "matchOperator": "equals", "matchType": "method",
                      "negate": False,
                      "objectMatchValue": {"type": "simple", "value": ["GET"]}}
                 ],
                 "name": "rul3", "start": 0,
                 "redirectURL": "/abc/sss", "statusCode": 307,
                 "useIncomingQueryString": False,
                 "useIncomingSchemeAndHost": True,
                 "useRelativeUrl": "copy_scheme_hostname"
                }
            ],
            "policyId": 276858, "version": 2
        }
        mock_session.exec.return_value = (_mock_response(201), body)
        result = client.create_policy_version(
            models.CreatePolicyVersionRequest(
                policy_id=276858,
                create_policy_version=models.CreatePolicyVersion(
                    match_rules=[
                        models.MatchRuleER(type="erMatchRule", end=0, match_url=None,
                                           matches=[
                                               models.MatchCriteria(case_sensitive=False, match_operator="equals",
                                                                    match_type="protocol", match_value="https", negate=False),
                                               models.MatchCriteria(case_sensitive=False, match_operator="equals",
                                                                    match_type="method", negate=False,
                                                                    object_match_value=models.ObjectMatchValueSimple(type="simple", value=["GET"])),
                                           ],
                                           name="rul3", start=0,
                                           redirect_url="/abc/sss", status_code=307,
                                           use_incoming_query_string=False, use_incoming_scheme_and_host=True,
                                           use_relative_url="copy_scheme_hostname"),
                    ],
                ),
            )
        )
        assert result.policy_id == 276858
        assert len(result.match_rules) == 1
        assert isinstance(result.match_rules[0], models.MatchRuleER)

    def test_201_complex_er_omv_object(self, mock_session, client):
        body = {
            "createdBy": "jsmith", "createdDate": "2023-10-19T08:50:47.350Z",
            "description": None, "modifiedBy": "jsmith",
            "modifiedDate": "2023-10-19T08:50:47.350Z",
            "matchRules": [
                {"type": "erMatchRule", "end": 0, "id": 0, "matchURL": None,
                 "matches": [
                     {"caseSensitive": False, "matchOperator": "equals", "matchType": "header",
                      "negate": False,
                      "objectMatchValue": {
                          "type": "object", "name": "ER",
                          "nameCaseSensitive": False, "nameHasWildcard": False,
                          "options": {"value": ["text/html*", "text/css*", "application/x-javascript*"],
                                      "valueCaseSensitive": False, "valueHasWildcard": True}
                      }}
                 ],
                 "name": "rul3", "start": 0,
                 "redirectURL": "/abc/sss", "statusCode": 307,
                 "useIncomingQueryString": False,
                 "useIncomingSchemeAndHost": True,
                 "useRelativeUrl": "copy_scheme_hostname"
                }
            ],
            "policyId": 276858, "version": 2
        }
        mock_session.exec.return_value = (_mock_response(201), body)
        result = client.create_policy_version(
            models.CreatePolicyVersionRequest(
                policy_id=276858,
                create_policy_version=models.CreatePolicyVersion(
                    match_rules=[
                        models.MatchRuleER(type="erMatchRule", end=0, match_url=None,
                                           matches=[
                                               models.MatchCriteria(case_sensitive=False, match_operator="equals",
                                                                    match_type="header", negate=False,
                                                                    object_match_value=models.ObjectMatchValueObject(
                                                                        type="object", name="ER",
                                                                        name_case_sensitive=False, name_has_wildcard=False,
                                                                        options=models.Options(
                                                                            value=["text/html*", "text/css*", "application/x-javascript*"],
                                                                            value_case_sensitive=False, value_has_wildcard=True))),
                                           ],
                                           name="rul3", start=0,
                                           redirect_url="/abc/sss", status_code=307,
                                           use_incoming_query_string=False, use_incoming_scheme_and_host=True,
                                           use_relative_url="copy_scheme_hostname"),
                    ],
                ),
            )
        )
        assert result.policy_id == 276858
        assert len(result.match_rules) == 1
        assert isinstance(result.match_rules[0], models.MatchRuleER)

    def test_201_er_empty_no_use_relative_url(self, mock_session, client):
        body = {
            "createdBy": "jsmith", "createdDate": "2023-10-19T08:50:47.350Z",
            "description": None, "modifiedBy": "jsmith",
            "modifiedDate": "2023-10-19T08:50:47.350Z",
            "matchRules": [
                {"type": "erMatchRule", "end": 0, "id": 0, "matchURL": "ddd.aaa",
                 "name": "rule 2", "redirectURL": "sss.com", "start": 0, "statusCode": 301,
                 "useIncomingQueryString": True},
                {"type": "erMatchRule", "end": 0, "id": 0, "matchURL": "abc.com",
                 "name": "r1", "redirectURL": "/ddd", "start": 0, "statusCode": 301,
                 "useIncomingQueryString": False,
                 "useIncomingSchemeAndHost": True,
                 "useRelativeUrl": "copy_scheme_hostname"},
                {"type": "erMatchRule", "end": 0, "id": 0,
                 "name": "rul3", "redirectURL": "/abc/sss",
                 "start": 0, "statusCode": 307}
            ],
            "policyId": 276858, "version": 6
        }
        mock_session.exec.return_value = (_mock_response(201), body)
        result = client.create_policy_version(
            models.CreatePolicyVersionRequest(
                policy_id=276858,
                create_policy_version=models.CreatePolicyVersion(
                    match_rules=[
                        models.MatchRuleER(type="erMatchRule", match_url="ddd.aaa",
                                           name="rule 2", redirect_url="sss.com",
                                           status_code=301,
                                           use_incoming_query_string=True),
                        models.MatchRuleER(type="erMatchRule", match_url="abc.com",
                                           name="r1", redirect_url="/ddd",
                                           status_code=301,
                                           use_incoming_scheme_and_host=True,
                                           use_relative_url=""),
                        models.MatchRuleER(type="erMatchRule",
                                           name="rul3",
                                           redirect_url="/abc/sss", status_code=307),
                    ],
                ),
            )
        )
        assert result.policy_id == 276858
        assert len(result.match_rules) == 3

    def test_201_complex_fr_omv_object(self, mock_session, client):
        body = {
            "createdBy": "jsmith", "createdDate": "2023-10-19T08:50:47.350Z",
            "description": "New version 1630480693371", "modifiedBy": "jsmith",
            "modifiedDate": "2023-10-19T08:50:47.350Z",
            "matchRules": [
                {"type": "frMatchRule", "end": 0, "id": 0, "matchURL": None,
                 "matches": [
                     {"caseSensitive": False, "matchOperator": "equals", "matchType": "header",
                      "negate": False,
                      "objectMatchValue": {
                          "type": "object", "name": "Accept",
                          "nameCaseSensitive": False, "nameHasWildcard": False,
                          "options": {"value": ["asd", "qwe"], "valueCaseSensitive": True}
                      }}
                 ],
                 "name": "rul3", "start": 0,
                 "forwardSettings": {}
                }
            ],
            "policyId": 139743, "version": 798
        }
        mock_session.exec.return_value = (_mock_response(201), body)
        result = client.create_policy_version(
            models.CreatePolicyVersionRequest(
                policy_id=139743,
                create_policy_version=models.CreatePolicyVersion(
                    description="New version 1630480693371",
                    match_rules=[
                        models.MatchRuleFR(type="frMatchRule", end=0, match_url=None,
                                           matches=[
                                               models.MatchCriteria(case_sensitive=False, match_operator="equals",
                                                                    match_type="header", negate=False,
                                                                    object_match_value=models.ObjectMatchValueObject(
                                                                        type="object", name="Accept",
                                                                        name_case_sensitive=False, name_has_wildcard=False,
                                                                        options=models.Options(
                                                                            value=["asd", "qwe"],
                                                                            value_case_sensitive=True))),
                                           ],
                                           name="rul3", start=0,
                                           forward_settings=models.ForwardSettingsFR()),
                    ],
                ),
            )
        )
        assert result.policy_id == 139743
        assert result.policy_version == 798
        assert len(result.match_rules) == 1
        assert isinstance(result.match_rules[0], models.MatchRuleFR)

    def test_201_complex_fr_omv_simple(self, mock_session, client):
        body = {
            "createdBy": "jsmith", "createdDate": "2023-10-19T08:50:47.350Z",
            "description": "New version 1630480693371", "modifiedBy": "jsmith",
            "modifiedDate": "2023-10-19T08:50:47.350Z",
            "matchRules": [
                {"type": "frMatchRule", "end": 0, "id": 0, "matchURL": None,
                 "matches": [
                     {"caseSensitive": False, "matchOperator": "equals", "matchType": "protocol",
                      "matchValue": "https", "negate": False},
                     {"caseSensitive": False, "matchOperator": "equals", "matchType": "method",
                      "negate": False,
                      "objectMatchValue": {"type": "simple", "value": ["GET"]}}
                 ],
                 "name": "rul3", "start": 0,
                 "forwardSettings": {"pathAndQS": "/test_images/otherimage.jpg", "useIncomingQueryString": True}
                }
            ],
            "policyId": 139743, "version": 798
        }
        mock_session.exec.return_value = (_mock_response(201), body)
        result = client.create_policy_version(
            models.CreatePolicyVersionRequest(
                policy_id=139743,
                create_policy_version=models.CreatePolicyVersion(
                    description="New version 1630480693371",
                    match_rules=[
                        models.MatchRuleFR(type="frMatchRule", end=0, match_url=None,
                                           matches=[
                                               models.MatchCriteria(case_sensitive=False, match_operator="equals",
                                                                    match_type="protocol", match_value="https", negate=False),
                                               models.MatchCriteria(case_sensitive=False, match_operator="equals",
                                                                    match_type="method", negate=False,
                                                                    object_match_value=models.ObjectMatchValueSimple(type="simple", value=["GET"])),
                                           ],
                                           name="rul3", start=0,
                                           forward_settings=models.ForwardSettingsFR(
                                               path_and_qs="/test_images/otherimage.jpg",
                                               use_incoming_query_string=True)),
                    ],
                ),
            )
        )
        assert result.policy_id == 139743
        assert result.policy_version == 798
        assert len(result.match_rules) == 1
        assert isinstance(result.match_rules[0], models.MatchRuleFR)

    def test_validation_error_range_omv_pr(self):
        err = validation.validate_match_rules([
            models.MatchRulePR(type="cdMatchRule", name="rul3",
                               forward_settings=models.ForwardSettingsPR(origin_id="some_origin", percent=10),
                               matches=[models.MatchCriteria(match_operator="equals", match_type="header",
                                                             object_match_value=models.ObjectMatchValueRange(type="range", value=[1, 50]))]),
        ])
        assert err is not None

    def test_validation_error_range_omv_er(self):
        err = validation.validate_match_rules([
            models.MatchRuleER(type="erMatchRule", name="rul3", use_relative_url="copy_scheme_hostname",
                               status_code=307, redirect_url="/abc/sss",
                               matches=[models.MatchCriteria(match_operator="equals", match_type="header",
                                                             object_match_value=models.ObjectMatchValueRange(type="range", value=[1, 50]))]),
        ])
        assert err is not None

    def test_validation_error_range_omv_rc(self):
        err = validation.validate_match_rules([
            models.MatchRuleRC(type="igMatchRule", name="rul3", allow_deny="allow",
                               matches=[models.MatchCriteria(match_operator="equals", match_type="header",
                                                             object_match_value=models.ObjectMatchValueRange(type="range", value=[1, 50]))]),
        ])
        assert err is not None

    def test_validation_error_range_omv_ap(self):
        err = validation.validate_match_rules([
            models.MatchRuleAP(type="apMatchRule", name="rul3", pass_through_percent=50.50,
                               matches=[models.MatchCriteria(match_operator="equals", match_type="header",
                                                             object_match_value=models.ObjectMatchValueRange(type="range", value=[1, 50]))]),
        ])
        assert err is not None

    def test_validation_error_rc_missing_allow_deny(self):
        err = validation.validate_match_rules([
            models.MatchRuleRC(type="igMatchRule", name="rul3"),
        ])
        assert err is not None

    def test_validation_error_ap_missing_pass_through(self):
        err = validation.validate_match_rules([
            models.MatchRuleAP(type="apMatchRule", name="rul3"),
        ])
        assert err is not None

    def test_validation_error_ap_out_of_range(self):
        err = validation.validate_match_rules([
            models.MatchRuleAP(type="apMatchRule", name="rul3", pass_through_percent=101.0),
        ])
        assert err is not None

    def test_500_internal_server_error(self, mock_session, client):
        mock_session.exec.side_effect = _api_error()
        with pytest.raises(RuntimeError) as exc_info:
            client.create_policy_version(
                models.CreatePolicyVersionRequest(policy_id=1)
            )
        assert errors.ErrCreatePolicyVersion in str(exc_info.value)


# ===================================================================
# TestDeletePolicyVersion — from policy_version_test.go
# ===================================================================


class TestDeletePolicyVersion:

    def test_204_no_content(self, mock_session, client):
        mock_session.exec.return_value = (_mock_response(204), None)
        client.delete_policy_version(
            models.DeletePolicyVersionRequest(policy_id=276858, policy_version=5)
        )
        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "DELETE"
        assert call_args[0][1] == "/cloudlets/v3/policies/276858/versions/5"

    def test_validation_errors(self):
        err = validation.validate_delete_policy_version_request(
            models.DeletePolicyVersionRequest()
        )
        assert err is not None

    def test_500_internal_server_error(self, mock_session, client):
        mock_session.exec.side_effect = _api_error()
        with pytest.raises(RuntimeError) as exc_info:
            client.delete_policy_version(
                models.DeletePolicyVersionRequest(policy_id=1, policy_version=2)
            )
        assert errors.ErrDeletePolicyVersion in str(exc_info.value)


# ===================================================================
# TestUpdatePolicyVersion — from policy_version_test.go
# ===================================================================


class TestUpdatePolicyVersion:

    def test_201_updated_simple_er(self, mock_session, client):
        body = {
            "createdBy": "jsmith",
            "createdDate": "2023-10-19T08:50:47.350Z",
            "description": "Updated description",
            "modifiedBy": "jsmith",
            "modifiedDate": "2023-10-19T08:50:47.350Z",
            "matchRules": None,
            "policyId": 276858,
            "version": 5,
        }
        mock_session.exec.return_value = (_mock_response(200), body)
        result = client.update_policy_version(
            models.UpdatePolicyVersionRequest(
                policy_id=276858,
                policy_version=5,
                update_policy_version=models.UpdatePolicyVersion(
                    description="Updated description",
                ),
            )
        )
        assert result.policy_id == 276858
        assert result.description == "Updated description"
        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "PUT"
        assert call_args[0][1] == "/cloudlets/v3/policies/276858/versions/5"

    def test_201_updated_with_warnings(self, mock_session, client):
        body = {
            "createdBy": "jsmith",
            "createdDate": "2023-10-19T08:50:47.350Z",
            "description": None,
            "modifiedBy": "jsmith",
            "modifiedDate": "2023-10-19T08:50:47.350Z",
            "matchRules": [
                {
                    "type": "erMatchRule", "end": 0, "id": 0, "matchURL": None,
                    "name": "er_rule", "redirectURL": "/path", "start": 0,
                    "statusCode": 301, "useIncomingQueryString": False,
                    "useIncomingSchemeAndHost": False, "useRelativeUrl": "none"
                }
            ],
            "matchRulesWarnings": [
                {
                    "detail": "No match match conditions.",
                    "jsonPointer": "/matchRules/0",
                    "title": "Irrelevant Match Rule",
                    "type": "/cloudlets/v3/warning-types/irrelevant-match-rules"
                }
            ],
            "policyId": 276858,
            "version": 5,
        }
        mock_session.exec.return_value = (_mock_response(200), body)
        result = client.update_policy_version(
            models.UpdatePolicyVersionRequest(
                policy_id=276858,
                policy_version=5,
                update_policy_version=models.UpdatePolicyVersion(
                    match_rules=[
                        models.MatchRuleER(type="erMatchRule", name="er_rule",
                                           redirect_url="/path", status_code=301,
                                           use_relative_url="none"),
                    ],
                ),
            )
        )
        assert result.match_rules_warnings is not None
        assert len(result.match_rules_warnings) == 1
        assert result.match_rules_warnings[0].detail == "No match match conditions."
        assert result.match_rules_warnings[0].json_pointer == "/matchRules/0"

    def test_500_internal_server_error(self, mock_session, client):
        mock_session.exec.side_effect = _api_error()
        with pytest.raises(RuntimeError) as exc_info:
            client.update_policy_version(
                models.UpdatePolicyVersionRequest(
                    policy_id=276858,
                    policy_version=3,
                    update_policy_version=models.UpdatePolicyVersion(),
                )
            )
        assert errors.ErrUpdatePolicyVersion in str(exc_info.value)

    def test_validation_error(self):
        err = validation.validate_update_policy_version_request(
            models.UpdatePolicyVersionRequest(
                policy_id=276858,
                policy_version=5,
                update_policy_version=models.UpdatePolicyVersion(
                    description="A" * 256,
                ),
            )
        )
        assert err is not None


# ===================================================================
# TestUnmarshalJSONMatchRules — from match_rule_test.go
# ===================================================================


class TestUnmarshalJSONMatchRules:
    """Mirrors Go TestUnmarshalJSONMatchRules from match_rule_test.go."""

    def test_invalid_match_rule_xx(self):
        raw = json.dumps([{"type": "xxMatchRule", "name": "r1"}])
        data = json.loads(raw)
        with pytest.raises(ValueError) as exc_info:
            deserialize_match_rules(data)
        assert "unsupported match rule type: xxMatchRule" in str(exc_info.value)

    def test_invalid_type_not_string(self):
        data = [{"type": 1, "name": "r1"}]
        with pytest.raises(ValueError) as exc_info:
            deserialize_match_rules(data)
        assert "'type' field on match rule entry should be a string" in str(exc_info.value)

    def test_invalid_json(self):
        with pytest.raises((json.JSONDecodeError, ValueError, TypeError)):
            deserialize_match_rules("not-valid-json")

    def test_missing_type(self):
        data = [{"name": "r1"}]
        with pytest.raises(ValueError) as exc_info:
            deserialize_match_rules(data)
        assert "match rule entry should contain 'type' field" in str(exc_info.value)

    def test_invalid_omv_type_for_pr_range(self):
        data = [
            {
                "type": "cdMatchRule",
                "name": "rul3",
                "forwardSettings": {"originId": "some_origin", "percent": 10},
                "matches": [
                    {"matchOperator": "equals", "matchType": "header", "negate": False,
                     "objectMatchValue": {"type": "range", "value": [1, 50]}}
                ]
            }
        ]
        with pytest.raises(ValueError) as exc_info:
            deserialize_match_rules(data)
        assert "objectMatchValue has unexpected type: 'range'" in str(exc_info.value)

    def test_invalid_omv_type_for_er_range(self):
        data = [
            {
                "type": "erMatchRule",
                "name": "rul3", "statusCode": 307, "redirectURL": "/abc/sss",
                "useRelativeUrl": "copy_scheme_hostname",
                "matches": [
                    {"matchOperator": "equals", "matchType": "header", "negate": False,
                     "objectMatchValue": {"type": "range", "value": [1, 50]}}
                ]
            }
        ]
        with pytest.raises(ValueError) as exc_info:
            deserialize_match_rules(data)
        assert "objectMatchValue has unexpected type: 'range'" in str(exc_info.value)

    def test_invalid_omv_type_for_fr_range(self):
        data = [
            {
                "type": "frMatchRule",
                "name": "rul3", "forwardSettings": {},
                "matches": [
                    {"matchOperator": "equals", "matchType": "header", "negate": False,
                     "objectMatchValue": {"type": "range", "value": [1, 50]}}
                ]
            }
        ]
        with pytest.raises(ValueError) as exc_info:
            deserialize_match_rules(data)
        assert "objectMatchValue has unexpected type: 'range'" in str(exc_info.value)

    def test_invalid_omv_type_for_ap_range(self):
        data = [
            {
                "type": "apMatchRule",
                "name": "rul3", "passThroughPercent": 50.5,
                "matches": [
                    {"matchOperator": "equals", "matchType": "header", "negate": False,
                     "objectMatchValue": {"type": "range", "value": [1, 50]}}
                ]
            }
        ]
        with pytest.raises(ValueError) as exc_info:
            deserialize_match_rules(data)
        assert "objectMatchValue has unexpected type: 'range'" in str(exc_info.value)

    def test_invalid_omv_type_for_rc_range(self):
        data = [
            {
                "type": "igMatchRule",
                "name": "rul3", "allowDeny": "allow",
                "matches": [
                    {"matchOperator": "equals", "matchType": "header", "negate": False,
                     "objectMatchValue": {"type": "range", "value": [1, 50]}}
                ]
            }
        ]
        with pytest.raises(ValueError) as exc_info:
            deserialize_match_rules(data)
        assert "objectMatchValue has unexpected type: 'range'" in str(exc_info.value)

    def test_valid_pr(self):
        data = [
            {
                "type": "cdMatchRule",
                "end": 0, "id": 0, "matchURL": None,
                "matches": [
                    {"caseSensitive": False, "matchOperator": "equals", "matchType": "protocol",
                     "matchValue": "https", "negate": False},
                    {"caseSensitive": False, "matchOperator": "equals", "matchType": "method",
                     "negate": False,
                     "objectMatchValue": {"type": "simple", "value": ["GET"]}}
                ],
                "name": "rul3", "start": 0,
                "forwardSettings": {"originId": "some_origin", "percent": 10}
            }
        ]
        result = deserialize_match_rules(data)
        assert len(result) == 1
        assert isinstance(result[0], models.MatchRulePR)
        assert result[0].forward_settings.origin_id == "some_origin"

    def test_valid_fr(self):
        data = [
            {
                "type": "frMatchRule",
                "end": 0, "id": 0, "matchURL": None,
                "matches": [
                    {"caseSensitive": False, "matchOperator": "equals", "matchType": "protocol",
                     "matchValue": "https", "negate": False},
                    {"caseSensitive": False, "matchOperator": "equals", "matchType": "method",
                     "negate": False,
                     "objectMatchValue": {"type": "simple", "value": ["GET"]}}
                ],
                "name": "rul3", "start": 0,
                "forwardSettings": {}
            }
        ]
        result = deserialize_match_rules(data)
        assert len(result) == 1
        assert isinstance(result[0], models.MatchRuleFR)

    def test_valid_ap(self):
        data = [
            {
                "type": "apMatchRule",
                "end": 0, "id": 0, "matchURL": None,
                "passThroughPercent": 50.50,
                "matches": [
                    {"caseSensitive": False, "matchOperator": "equals", "matchType": "protocol",
                     "matchValue": "https", "negate": False},
                    {"caseSensitive": False, "matchOperator": "equals", "matchType": "method",
                     "negate": False,
                     "objectMatchValue": {"type": "simple", "value": ["GET"]}}
                ],
                "name": "rul3", "start": 0
            }
        ]
        result = deserialize_match_rules(data)
        assert len(result) == 1
        assert isinstance(result[0], models.MatchRuleAP)
        assert result[0].pass_through_percent == 50.50

    def test_valid_as(self):
        data = [
            {
                "type": "asMatchRule",
                "end": 0, "id": 0, "matchURL": "http://source.com/test1",
                "matches": [
                    {"caseSensitive": False, "matchOperator": "equals", "matchType": "range",
                     "negate": False,
                     "objectMatchValue": {"type": "range", "value": [1, 100]}},
                    {"caseSensitive": False, "matchOperator": "equals", "matchType": "header",
                     "negate": False,
                     "objectMatchValue": {
                         "type": "object", "name": "Accept-Charset",
                         "options": {"value": ["utf-8"]}
                     }}
                ],
                "name": "rul3", "start": 0,
                "forwardSettings": {"originId": "originremote", "pathAndQS": "/test", "useIncomingQueryString": True}
            }
        ]
        result = deserialize_match_rules(data)
        assert len(result) == 1
        assert isinstance(result[0], models.MatchRuleAS)
        assert result[0].match_url == "http://source.com/test1"

    def test_valid_er(self):
        data = [
            {
                "type": "erMatchRule",
                "end": 0, "id": 0, "matchURL": None,
                "name": "rul3",
                "redirectURL": "/abc/sss",
                "start": 0, "statusCode": 307,
                "useIncomingQueryString": False,
                "useIncomingSchemeAndHost": True,
                "useRelativeUrl": "copy_scheme_hostname"
            }
        ]
        result = deserialize_match_rules(data)
        assert len(result) == 1
        assert isinstance(result[0], models.MatchRuleER)
        assert result[0].status_code == 307

    def test_valid_rc(self):
        data = [
            {
                "type": "igMatchRule",
                "end": 0, "id": 0,
                "matches": [
                    {"caseSensitive": False, "matchOperator": "equals", "matchType": "protocol",
                     "matchValue": "https", "negate": False},
                    {"caseSensitive": False, "matchOperator": "equals", "matchType": "method",
                     "negate": False,
                     "objectMatchValue": {"type": "simple", "value": ["GET"]}}
                ],
                "name": "rul3", "start": 0,
                "allowDeny": "allow"
            }
        ]
        result = deserialize_match_rules(data)
        assert len(result) == 1
        assert isinstance(result[0], models.MatchRuleRC)
        assert result[0].allow_deny == "allow"


# ===================================================================
# TestValidateMatchRules — from match_rule_test.go
# ===================================================================


class TestValidateMatchRules:
    """Mirror Go TestValidateMatchRules: tests match rule validation for all types."""

    def test_valid_match_rules_ap(self):
        rules = [
            models.MatchRuleAP(type="apMatchRule", pass_through_percent=-1.0),
            models.MatchRuleAP(type="apMatchRule", pass_through_percent=50.5),
            models.MatchRuleAP(type="apMatchRule", pass_through_percent=0.0),
            models.MatchRuleAP(type="apMatchRule", pass_through_percent=100.0),
        ]
        err = validation.validate_match_rules(rules)
        assert err is None

    def test_invalid_match_rules_ap(self):
        rules = [
            models.MatchRuleAP(type="matchRule"),
            models.MatchRuleAP(type="apMatchRule", pass_through_percent=101.0),
            models.MatchRuleAP(type="apMatchRule", pass_through_percent=-2.0),
        ]
        err = validation.validate_match_rules(rules)
        assert err is not None
        assert "PassThroughPercent: cannot be blank" in err
        assert "Type: value 'matchRule' is invalid. Must be: 'apMatchRule'" in err
        assert "must be no greater than 100" in err
        assert "must be no less than -1" in err

    def test_valid_match_rules_as(self):
        rules = [
            models.MatchRuleAS(type="asMatchRule",
                               forward_settings=models.ForwardSettingsAS(origin_id="origin1")),
            models.MatchRuleAS(type="asMatchRule",
                               forward_settings=models.ForwardSettingsAS(origin_id="origin2"),
                               matches=[
                                   models.MatchCriteria(match_type="range", match_operator="equals",
                                                        object_match_value=models.ObjectMatchValueRange(type="range", value=[1, 25]))
                               ]),
        ]
        err = validation.validate_match_rules(rules)
        assert err is None

    def test_invalid_match_rules_as(self):
        rules = [
            models.MatchRuleAS(type="matchRule",
                               forward_settings=models.ForwardSettingsAS(origin_id="origin1")),
            models.MatchRuleAS(type="asMatchRule",
                               forward_settings=models.ForwardSettingsAS(origin_id="origin1"),
                               matches=[
                                   models.MatchCriteria(match_type="range", match_operator="equals",
                                                        object_match_value=models.ObjectMatchValueRange(type="range", value=[25, 1]))
                               ]),
        ]
        err = validation.validate_match_rules(rules)
        assert err is not None
        assert "Type: value 'matchRule' is invalid. Must be: 'asMatchRule'" in err

    def test_valid_match_rules_cd(self):
        rules = [
            models.MatchRulePR(type="cdMatchRule",
                               forward_settings=models.ForwardSettingsPR(origin_id="origin1", percent=10)),
            models.MatchRulePR(type="cdMatchRule",
                               forward_settings=models.ForwardSettingsPR(origin_id="origin2", percent=1)),
        ]
        err = validation.validate_match_rules(rules)
        assert err is None

    def test_invalid_match_rules_cd(self):
        rules = [
            models.MatchRulePR(type="cdMatchRule"),
            models.MatchRulePR(type="cdMatchRule",
                               forward_settings=models.ForwardSettingsPR(origin_id="origin1")),
            models.MatchRulePR(type="cdMatchRule",
                               forward_settings=models.ForwardSettingsPR(origin_id="origin1", percent=101)),
            models.MatchRulePR(type="cdMatchRule",
                               forward_settings=models.ForwardSettingsPR(origin_id="origin1", percent=-1)),
            models.MatchRulePR(type="cdMatchRule",
                               forward_settings=models.ForwardSettingsPR(percent=10)),
        ]
        err = validation.validate_match_rules(rules)
        assert err is not None

    def test_valid_match_rules_er(self):
        rules = [
            models.MatchRuleER(type="erMatchRule", status_code=301, redirect_url="/path",
                               use_relative_url="copy_scheme_hostname"),
            models.MatchRuleER(type="erMatchRule", status_code=302, redirect_url="/path",
                               use_relative_url="none"),
            models.MatchRuleER(type="erMatchRule", status_code=303, redirect_url="/path",
                               matches_always=True),
            models.MatchRuleER(type="erMatchRule", status_code=307, redirect_url="/path",
                               matches=[
                                   models.MatchCriteria(match_type="hostname", match_operator="equals",
                                                        match_value="example.com"),
                               ]),
        ]
        err = validation.validate_match_rules(rules)
        assert err is None

    def test_invalid_match_rules_er(self):
        rules = [
            models.MatchRuleER(type="matchRule", status_code=301, redirect_url="/path"),
            models.MatchRuleER(type="erMatchRule", status_code=404, redirect_url="/path"),
            models.MatchRuleER(type="erMatchRule", status_code=301, redirect_url="/path",
                               use_relative_url="test"),
            models.MatchRuleER(type="erMatchRule", status_code=301, redirect_url="/path",
                               matches_always=True,
                               matches=[models.MatchCriteria(match_type="hostname", match_operator="equals", match_value="x")]),
        ]
        err = validation.validate_match_rules(rules)
        assert err is not None
        assert "Type: value 'matchRule' is invalid. Must be: 'erMatchRule'" in err

    def test_valid_match_rules_fr(self):
        rules = [
            models.MatchRuleFR(type="frMatchRule",
                               forward_settings=models.ForwardSettingsFR(path_and_qs="/test")),
            models.MatchRuleFR(type="frMatchRule",
                               forward_settings=models.ForwardSettingsFR(path_and_qs="/img.jpg")),
        ]
        err = validation.validate_match_rules(rules)
        assert err is None

    def test_invalid_match_rules_fr(self):
        rules = [
            models.MatchRuleFR(type="matchRule",
                               forward_settings=models.ForwardSettingsFR(path_and_qs="/test")),
            models.MatchRuleFR(type="frMatchRule",
                               forward_settings=models.ForwardSettingsFR()),
        ]
        err = validation.validate_match_rules(rules)
        assert err is not None
        assert "Type: value 'matchRule' is invalid. Must be: 'frMatchRule'" in err

    def test_valid_match_rules_rc(self):
        rules = [
            models.MatchRuleRC(type="igMatchRule", allow_deny="allow"),
            models.MatchRuleRC(type="igMatchRule", allow_deny="deny"),
            models.MatchRuleRC(type="igMatchRule", allow_deny="denybranded"),
        ]
        err = validation.validate_match_rules(rules)
        assert err is None

    def test_invalid_match_rules_rc(self):
        rules = [
            models.MatchRuleRC(type="matchRule", allow_deny="allow"),
            models.MatchRuleRC(type="igMatchRule", allow_deny="allowBranded"),
            models.MatchRuleRC(type="igMatchRule", allow_deny="allow",
                               matches_always=True,
                               matches=[models.MatchCriteria(match_type="hostname", match_operator="equals", match_value="x")]),
        ]
        err = validation.validate_match_rules(rules)
        assert err is not None
        assert "Type: value 'matchRule' is invalid. Must be: 'igMatchRule'" in err

    def test_valid_match_criteria_match_value(self):
        rules = [
            models.MatchRuleER(type="erMatchRule", status_code=301, redirect_url="/path",
                               matches=[
                                   models.MatchCriteria(match_type="hostname", match_operator="equals",
                                                        match_value="example.com"),
                               ]),
        ]
        err = validation.validate_match_rules(rules)
        assert err is None

    def test_valid_match_criteria_object_match_value(self):
        rules = [
            models.MatchRuleER(type="erMatchRule", status_code=301, redirect_url="/path",
                               matches=[
                                   models.MatchCriteria(match_type="header", match_operator="equals",
                                                        object_match_value=models.ObjectMatchValueObject(
                                                            type="object", name="Accept")),
                               ]),
        ]
        err = validation.validate_match_rules(rules)
        assert err is None

    def test_invalid_match_criteria_both_or_neither(self):
        rules_both = [
            models.MatchRuleER(type="erMatchRule", status_code=301, redirect_url="/path",
                               matches=[
                                   models.MatchCriteria(match_type="hostname", match_operator="equals",
                                                        match_value="example.com",
                                                        object_match_value=models.ObjectMatchValueSimple(type="simple", value=["GET"])),
                               ]),
        ]
        err = validation.validate_match_rules(rules_both)
        assert err is not None

        rules_neither = [
            models.MatchRuleER(type="erMatchRule", status_code=301, redirect_url="/path",
                               matches=[
                                   models.MatchCriteria(match_type="hostname", match_operator="equals"),
                               ]),
        ]
        err2 = validation.validate_match_rules(rules_neither)
        assert err2 is not None


# ===================================================================
# TestGetObjectMatchValueType — from match_rule_test.go lines 565-610
# Tests the type extraction from raw objectMatchValue dicts.
# In Python, this is embedded in _deserialize_object_match_value.
# ===================================================================


class TestGetObjectMatchValueType:
    """Mirror Go TestGetObjectMatchValueType: tests type extraction from raw OMV dicts."""

    def test_success_getting_type(self):
        """Success getting objectMatchValue type from a valid dict."""
        data = {"type": "range", "value": [1, 50]}
        result = _deserialize_object_match_value(data, _ALL_OMV_HANDLERS)
        assert isinstance(result, models.ObjectMatchValueRange)
        assert result.type == "range"

    def test_error_invalid_type_not_map(self):
        """Error getting objectMatchValue type - input is a string, not a dict."""
        result = _deserialize_object_match_value("stringType", _ALL_OMV_HANDLERS)
        # Python implementation returns non-dict input as-is (no error)
        assert result == "stringType"

    def test_error_missing_type_field(self):
        """Error getting objectMatchValue type - missing 'type' field."""
        data = {"value": [1, 50]}
        result = _deserialize_object_match_value(data, _ALL_OMV_HANDLERS)
        # Python implementation returns dict as-is when type field is empty/missing
        assert result == data

    def test_error_type_not_string(self):
        """Error getting objectMatchValue type - type field is integer, not string."""
        data = {"type": 50, "value": [1, 50]}
        # In Python, non-string type (int 50) won't match handler keys and is truthy,
        # so it raises ValueError — equivalent to Go's "'type' should be a string" error
        with pytest.raises(ValueError) as exc_info:
            _deserialize_object_match_value(data, _ALL_OMV_HANDLERS)
        assert "objectMatchValue has unexpected type" in str(exc_info.value)


# ===================================================================
# TestConvertObjectMatchValue — from match_rule_test.go lines 611-690
# Tests conversion of raw dict to typed ObjectMatchValue objects.
# In Python, this is _deserialize_object_match_value.
# ===================================================================


class TestConvertObjectMatchValue:
    """Mirror Go TestConvertObjectMatchValue: tests converting raw dict to typed OMV."""

    def test_convert_range(self):
        """Success converting objectMatchValueRange."""
        data = {"type": "range", "value": [1, 50]}
        result = _deserialize_object_match_value(data, _ALL_OMV_HANDLERS)
        assert isinstance(result, models.ObjectMatchValueRange)
        assert result.type == "range"
        assert result.value == [1, 50]

    def test_convert_simple(self):
        """Success converting objectMatchValueSimple."""
        data = {"type": "simple", "value": ["GET"]}
        result = _deserialize_object_match_value(data, _ALL_OMV_HANDLERS)
        assert isinstance(result, models.ObjectMatchValueSimple)
        assert result.type == "simple"
        assert result.value == ["GET"]

    def test_convert_object(self):
        """Success converting objectMatchValueObject with Options."""
        data = {
            "type": "object",
            "name": "ER",
            "options": {
                "value": ["text/html*", "text/css*", "application/x-javascript*"],
                "valueHasWildcard": True,
            },
        }
        result = _deserialize_object_match_value(data, _ALL_OMV_HANDLERS)
        assert isinstance(result, models.ObjectMatchValueObject)
        assert result.type == "object"
        assert result.name == "ER"
        assert result.options is not None
        assert result.options.value == [
            "text/html*", "text/css*", "application/x-javascript*"
        ]
        assert result.options.value_has_wildcard is True

    def test_error_type_mismatch(self):
        """Error converting objectMatchValue - unsupported type for handler set."""
        data = {"type": "range", "value": [1, 50]}
        # Using _SIMPLE_OBJECT_OMV_HANDLERS which does NOT include 'range'
        with pytest.raises(ValueError) as exc_info:
            _deserialize_object_match_value(data, _SIMPLE_OBJECT_OMV_HANDLERS, "MatchCriteria")
        assert "objectMatchValue has unexpected type: 'range'" in str(exc_info.value)


# ===================================================================
# TestIndividualMatchRuleValidators — directly exercise each
# type-specific validation function per schema members_accessed
# ===================================================================


class TestIndividualMatchRuleValidators:
    """Directly test individual match-rule validators from validation module."""

    def test_validate_match_rule_ap_valid(self):
        rule = models.MatchRuleAP(
            type="apMatchRule", pass_through_percent=50.0,
        )
        result = validation.validate_match_rule_ap(rule)
        assert result is None

    def test_validate_match_rule_ap_invalid(self):
        rule = models.MatchRuleAP(type="wrong", pass_through_percent=-2)
        result = validation.validate_match_rule_ap(rule)
        assert result is not None
        assert "PassThroughPercent" in result

    def test_validate_match_rule_as_valid(self):
        rule = models.MatchRuleAS(
            type="asMatchRule",
            forward_settings=models.ForwardSettingsAS(
                origin_id="origin1",
                path_and_qs="/path",
                use_incoming_query_string=True,
            ),
        )
        result = validation.validate_match_rule_as(rule)
        assert result is None

    def test_validate_match_rule_as_invalid(self):
        rule = models.MatchRuleAS(type="wrong")
        result = validation.validate_match_rule_as(rule)
        assert result is not None
        assert "Type" in result

    def test_validate_match_rule_pr_valid(self):
        rule = models.MatchRulePR(
            type="cdMatchRule",
            forward_settings=models.ForwardSettingsPR(
                origin_id="origin1",
                percent=10.0,
            ),
        )
        result = validation.validate_match_rule_pr(rule)
        assert result is None

    def test_validate_match_rule_pr_invalid(self):
        rule = models.MatchRulePR(type="wrong")
        result = validation.validate_match_rule_pr(rule)
        assert result is not None
        assert "Type" in result

    def test_validate_match_rule_er_valid(self):
        rule = models.MatchRuleER(
            type="erMatchRule",
            redirect_url="/redirect",
            status_code=301,
        )
        result = validation.validate_match_rule_er(rule)
        assert result is None

    def test_validate_match_rule_er_invalid(self):
        rule = models.MatchRuleER(type="wrong")
        result = validation.validate_match_rule_er(rule)
        assert result is not None
        assert "Type" in result

    def test_validate_match_rule_fr_valid(self):
        rule = models.MatchRuleFR(
            type="frMatchRule",
            forward_settings=models.ForwardSettingsFR(
                origin_id="origin1",
                path_and_qs="/path",
                use_incoming_query_string=True,
            ),
        )
        result = validation.validate_match_rule_fr(rule)
        assert result is None

    def test_validate_match_rule_fr_invalid(self):
        rule = models.MatchRuleFR(type="wrong")
        result = validation.validate_match_rule_fr(rule)
        assert result is not None
        assert "Type" in result

    def test_validate_match_rule_rc_valid(self):
        rule = models.MatchRuleRC(
            type="igMatchRule",
            allow_deny="allow",
        )
        result = validation.validate_match_rule_rc(rule)
        assert result is None

    def test_validate_match_rule_rc_invalid(self):
        rule = models.MatchRuleRC(type="wrong")
        result = validation.validate_match_rule_rc(rule)
        assert result is not None
        assert "Type" in result


# ===================================================================
# TestModelsAndConstants — verify all schema members_accessed are
# exercised: model instantiation, constant values, response types.
# ===================================================================


class TestModelsAndConstants:
    """Verify all model types and constants from schema members_accessed."""

    def test_list_policies_response(self):
        resp = models.ListPoliciesResponse(content=[])
        assert isinstance(resp, models.ListPoliciesResponse)

    def test_current_activations(self):
        obj = models.CurrentActivations()
        assert isinstance(obj, models.CurrentActivations)

    def test_activation_info(self):
        obj = models.ActivationInfo()
        assert isinstance(obj, models.ActivationInfo)

    def test_list_cloudlets_item(self):
        item = models.ListCloudletsItem(cloudlet_name="TEST", cloudlet_type="AP")
        assert item.cloudlet_type == models.CloudletTypeAP

    def test_list_policy_versions_item(self):
        item = models.ListPolicyVersionsItem()
        assert isinstance(item, models.ListPolicyVersionsItem)

    def test_match_rules_warning(self):
        warn = models.MatchRulesWarning(detail="test", title="title", type="type")
        assert warn.detail == "test"

    def test_list_active_policy_properties_response(self):
        resp = models.ListActivePolicyPropertiesResponse()
        assert isinstance(resp, models.ListActivePolicyPropertiesResponse)

    def test_list_policy_properties_item(self):
        item = models.ListPolicyPropertiesItem()
        assert isinstance(item, models.ListPolicyPropertiesItem)

    @pytest.mark.parametrize("constant,expected", [
        (models.CloudletTypeAP, "AP"),
        (models.CloudletTypeAS, "AS"),
        (models.CloudletTypeCD, "CD"),
        (models.CloudletTypeFR, "FR"),
        (models.OperationActivation, "ACTIVATION"),
        (models.OperationDeactivation, "DEACTIVATION"),
        (models.ActivationStatusSuccess, "SUCCESS"),
        (models.ActivationStatusInProgress, "IN_PROGRESS"),
        (models.MatchRuleFormat10, "1.0"),
        (models.PolicyTypeShared, "SHARED"),
        (models.StagingNetwork, "STAGING"),
        (models.ProductionNetwork, "PRODUCTION"),
    ])
    def test_constants(self, constant, expected):
        assert constant == expected
