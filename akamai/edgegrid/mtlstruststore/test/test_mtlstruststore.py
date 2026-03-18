# pylint: disable=missing-function-docstring,missing-class-docstring
# pylint: disable=too-many-lines,line-too-long,too-few-public-methods
"""Unit tests for the mTLS Trust Store API client.

Mirrors all Go test scenarios from pkg/mtlstruststore/*_test.go files.
All responseBody and responseHeaders values are used VERBATIM from Go tests.
"""

import json
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.mtlstruststore.mtlstruststore import Client
from akamai.edgegrid.mtlstruststore import models
from akamai.edgegrid.mtlstruststore import errors
from akamai.edgegrid.mtlstruststore.test.conftest import (
    create_mock_response,
    assert_request,
)


# ---------------------------------------------------------------------------
# TestClient — from mtlstruststore_test.go
# ---------------------------------------------------------------------------

class TestClient:
    """Tests for Client constructor — mirrors Go TestClient."""

    def test_no_options_default(self, mock_session):
        client = Client(mock_session)
        assert client._session is not None  # pylint: disable=protected-access

    def test_with_session(self, mock_session):
        client = Client(mock_session)
        assert client._session is mock_session  # pylint: disable=protected-access


# ---------------------------------------------------------------------------
# TestNewError — from errors_test.go
# ---------------------------------------------------------------------------

class TestNewError:
    """Tests for error parsing — mirrors Go TestNewError."""

    @pytest.mark.parametrize("name, response_body, status_code, expected", [
        (
            "Bad request 400",
            '{"contextInfo":{"parameterName":"caSetId"},"detail":"Parameter caSetId is not valid.","status":400,"title":"Invalid parameter value.","type":"/mtls-edge-truststore/error-types/path-variable-query-param-type-mismatch"}',
            400,
            {
                "type": "/mtls-edge-truststore/error-types/path-variable-query-param-type-mismatch",
                "title": "Invalid parameter value.",
                "detail": "Parameter caSetId is not valid.",
                "status": 400,
                "context_info": {"parameterName": "caSetId"},
            },
        ),
        (
            "Invalid request 400",
            '{"detail":"Request is invalid.","errors":[{"detail":"Unknown query parameter names found: test","pointer":"/test","type":"/mtls-edge-truststore/error-types/unknown-query-parameters"}],"status":400,"title":"Invalid request.","type":"/mtls-edge-truststore/error-types/unknown-query-parameters"}',
            400,
            {
                "type": "/mtls-edge-truststore/error-types/unknown-query-parameters",
                "title": "Invalid request.",
                "detail": "Request is invalid.",
                "status": 400,
                "errors": [
                    {
                        "detail": "Unknown query parameter names found: test",
                        "pointer": "/test",
                        "type": "/mtls-edge-truststore/error-types/unknown-query-parameters",
                        "context_info": None,
                    },
                ],
            },
        ),
        (
            "CASet does not exists 404",
            '{"contextInfo":{"caSetId":0},"detail":"CA set with caSetId 0 is not found.","status":404,"title":"CA set is not found.","type":"/mtls-edge-truststore/error-types/ca-set-not-found"}',
            404,
            {
                "type": "/mtls-edge-truststore/error-types/ca-set-not-found",
                "title": "CA set is not found.",
                "detail": "CA set with caSetId 0 is not found.",
                "status": 404,
                "context_info": {"caSetId": 0},
            },
        ),
        (
            "invalid response body, assign status code",
            "test",
            500,
            {
                "type": "",
                "title": "Failed to unmarshal error body. mTLS Truststore API failed. Check details for more information.",
                "detail": "test",
                "status": 500,
            },
        ),
    ])
    def test_error_parsing(self, name, response_body, status_code, expected):  # pylint: disable=unused-argument
        mock_response = create_mock_response(status_code, response_body)
        client = Client(MagicMock())
        error = client._parse_error(mock_response)  # pylint: disable=protected-access

        assert error.status == expected["status"]
        assert error.title == expected["title"]
        assert error.detail == expected["detail"]
        assert error.type == expected.get("type", "")

        if "context_info" in expected:
            assert error.context_info == expected["context_info"]
        if "errors" in expected:
            assert error.errors is not None
            assert len(error.errors) == len(expected["errors"])
            for actual_item, expected_item in zip(error.errors, expected["errors"]):
                assert actual_item.detail == expected_item["detail"]
                assert actual_item.pointer == expected_item["pointer"]
                assert actual_item.type == expected_item["type"]


# ---------------------------------------------------------------------------
# TestIs — from errors_test.go
# ---------------------------------------------------------------------------

class TestIs:
    """Tests for Error.is_equivalent — mirrors Go TestIs."""

    @pytest.mark.parametrize("name, err, target, expected", [
        (
            "different error code",
            errors.Error(type="/mtls-edge-truststore/error-types/ca-set-not-found", title="CA set is not found.", status=404),
            errors.Error(type="/mtls-edge-truststore/error-types/ca-set-not-found", title="CA set is not found.", status=401),
            False,
        ),
        (
            "same error code",
            errors.Error(type="/mtls-edge-truststore/error-types/ca-set-not-found", title="CA set is not found.", status=404),
            errors.Error(type="/mtls-edge-truststore/error-types/ca-set-not-found", title="CA set is not found.", status=404),
            True,
        ),
        (
            "same error code and title",
            errors.Error(type="/mtls-edge-truststore/error-types/ca-set-not-found", title="CA set is not found.", status=404),
            errors.Error(type="/mtls-edge-truststore/error-types/ca-set-not-found", title="CA set is not found.", status=404),
            True,
        ),
        (
            "same error code and different error message",
            errors.Error(type="/mtls-edge-truststore/error-types/ca-set-not-found", title="CA set is not found.", status=404),
            errors.Error(type="/mtls-edge-truststore/error-types/ca-set-not-found", title="Different title", status=404),
            False,
        ),
    ])
    def test_is(self, name, err, target, expected):  # pylint: disable=unused-argument
        assert err.is_equivalent(target) is expected


# ---------------------------------------------------------------------------
# TestCreateCASet — from ca_set_test.go
# ---------------------------------------------------------------------------

class TestCreateCASet:
    """Tests for create_ca_set — mirrors Go TestCreateCASet."""

    def test_201_created(self, mock_session):
        response_body = '{"accountId":"A-CCOUNT","caSetId":"199","caSetName":"test","description":"description","createdDate":"2025-04-01T15:33:48.464941Z","createdBy":"tester"}'
        mock_response = create_mock_response(
            201, response_body,
            headers={"Location": "/mtls-edge-truststore/v2/ca-sets/199"},
        )
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.create_ca_set(models.CreateCASetRequest(
            ca_set_name="test",
            description="description",
        ))
        assert result.account_id == "A-CCOUNT"
        assert result.ca_set_id == "199"
        assert result.ca_set_name == "test"
        assert result.description == "description"
        assert result.created_date == "2025-04-01T15:33:48.464941Z"
        assert result.created_by == "tester"

    def test_missing_required_request_param_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.create_ca_set(models.CreateCASetRequest())
        assert errors.ErrCreateCASet in exc.value.title
        assert "CASetName: cannot be blank" in exc.value.detail

    def test_name_too_short_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.create_ca_set(models.CreateCASetRequest(ca_set_name="a"))
        assert errors.ErrCreateCASet in exc.value.title
        assert "CASetName: the length must be between 3 and 64" in exc.value.detail

    def test_invalid_name_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.create_ca_set(models.CreateCASetRequest(ca_set_name="###A"))
        assert errors.ErrCreateCASet in exc.value.title
        assert "CASetName:" in exc.value.detail

    def test_invalid_name_with_triple_periods_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.create_ca_set(models.CreateCASetRequest(ca_set_name="AAA...A"))
        assert errors.ErrCreateCASet in exc.value.title
        assert "cannot contain three consecutive periods" in exc.value.detail

    def test_500_internal_server_error(self, mock_session):
        response_body = '{"type":"internal_error","title":"Internal Server Error","detail":"Error processing request","status":500}'
        mock_response = create_mock_response(500, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.create_ca_set(models.CreateCASetRequest(
                ca_set_name="test",
                description="description",
            ))
        assert exc.value.is_equivalent(errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error processing request",
            status=500,
        ))

    def test_409_duplicate_ca_set(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-name-is-not-unique","title":"CA set with the same name exists in the account.","detail":"CA set with the name test already exists.","status":409,"contextInfo":{"caSetName":"test"}}'
        mock_response = create_mock_response(409, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.create_ca_set(models.CreateCASetRequest(
                ca_set_name="test",
                description="description",
            ))
        assert exc.value.type == "/mtls-edge-truststore/error-types/ca-set-name-is-not-unique"
        assert exc.value.title == "CA set with the same name exists in the account."
        assert exc.value.detail == "CA set with the name test already exists."
        assert exc.value.status == 409
        assert exc.value.context_info == {"caSetName": "test"}

    def test_415_wrong_content_type_header(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/media-type-not-supported","title":"Unsupported Media Type.","detail":"Content type \'text/plain\' not supported.","status":415}'
        mock_response = create_mock_response(415, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.create_ca_set(models.CreateCASetRequest(
                ca_set_name="test",
                description="description",
            ))
        assert exc.value.is_equivalent(errors.ErrMediaTypeNotSupported)

    def test_400_json_schema_validation(self, mock_session):
        response_body = '{"contextInfo":{"message":"instance type (integer) does not match any allowed primitive type (allowed: [\\"string\\"])"},"instance":"/mtls-edge-truststore/error-types/json-schema-validation-error/12345a6c78caa9bb","pointer":"/caSetName","status":400,"title":"Body failed JSON schema validation.","type":"/mtls-edge-truststore/error-types/json-schema-validation-error"}'
        mock_response = create_mock_response(400, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.create_ca_set(models.CreateCASetRequest(
                ca_set_name="test",
                description="description",
            ))
        assert exc.value.status == 400
        assert exc.value.title == "Body failed JSON schema validation."
        assert exc.value.type == "/mtls-edge-truststore/error-types/json-schema-validation-error"
        assert exc.value.pointer == "/caSetName"
        assert exc.value.instance == "/mtls-edge-truststore/error-types/json-schema-validation-error/12345a6c78caa9bb"


# ---------------------------------------------------------------------------
# TestGetCASet — from ca_set_test.go
# ---------------------------------------------------------------------------

class TestGetCASet:
    """Tests for get_ca_set — mirrors Go TestGetCASet."""

    def test_200_ok(self, mock_session):
        response_body = '{"accountId":"A-CCOUNT","caSetId":"199","caSetLink":"/mtls-edge-truststore/v2/ca-sets/199","caSetName":"test","caSetStatus":"NOT_DELETED","createdBy":"jdoe","createdDate":"2025-04-01T15:33:48.464941Z","deletedBy":null,"deletedDate":null,"description":"","latestVersion":null,"latestVersionLink":null,"productionVersion":null,"productionVersionLink":null,"stagingVersion":null,"stagingVersionLink":null,"versionsLink":"/mtls-edge-truststore/v2/ca-sets/199/versions/"}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.get_ca_set(models.GetCASetRequest(ca_set_id="199"))
        assert result.account_id == "A-CCOUNT"
        assert result.ca_set_id == "199"
        assert result.ca_set_link == "/mtls-edge-truststore/v2/ca-sets/199"
        assert result.ca_set_name == "test"
        assert result.ca_set_status == "NOT_DELETED"
        assert result.created_by == "jdoe"
        assert result.created_date == "2025-04-01T15:33:48.464941Z"
        assert result.deleted_by is None
        assert result.deleted_date is None
        assert result.description == ""
        assert result.latest_version is None
        assert result.staging_version is None
        assert result.production_version is None
        assert result.versions_link == "/mtls-edge-truststore/v2/ca-sets/199/versions/"

    def test_missing_required_params_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set(models.GetCASetRequest())
        assert errors.ErrGetCASet in exc.value.title
        assert "CASetID: cannot be blank" in exc.value.detail

    def test_404_ca_set_not_found(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-not-found","title":"CA set is not found.","status":404,"detail":"CA set with caSetId 10 is not found.","contextInfo":{"caSetId":"10"}}'
        mock_response = create_mock_response(404, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set(models.GetCASetRequest(ca_set_id="10"))
        assert exc.value.is_equivalent(errors.ErrGetCASetNotFound)

    def test_500_internal_server_error(self, mock_session):
        response_body = '{"type":"internal_error","title":"Internal Server Error","detail":"Error processing request","status":500}'
        mock_response = create_mock_response(500, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set(models.GetCASetRequest(ca_set_id="10"))
        assert exc.value.is_equivalent(errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error processing request",
            status=500,
        ))


# ---------------------------------------------------------------------------
# TestListCASets — from ca_set_test.go
# ---------------------------------------------------------------------------

class TestListCASets:
    """Tests for list_ca_sets — mirrors Go TestListCASets."""

    def test_200_ok(self, mock_session):
        response_body = '{"caSets":[{"accountId":"A-CCOUNT","caSetId":"199","caSetName":"test","description":"description","createdDate":"2025-04-01T15:33:48.464941Z","createdBy":"tester","modifiedDate":"2025-04-01T15:33:48.464941Z","modifiedBy":"tester2"},{"accountId":"A-CCOUNT2","caSetId":"200","caSetName":"test2","description":"description2","createdDate":"2025-04-01T15:33:48.464941Z","createdBy":"tester2"},{"accountId":"A-CCOUNT3","caSetId":"201","caSetName":"test3","createdDate":"2025-04-01T15:33:48.464941Z","createdBy":"tester3"}]}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.list_ca_sets(models.ListCASetsRequest())
        assert len(result.ca_sets) == 3
        assert result.ca_sets[0].ca_set_id == "199"
        assert result.ca_sets[1].ca_set_id == "200"
        assert result.ca_sets[2].ca_set_id == "201"
        assert result.ca_sets[2].description is None

    def test_200_ok_with_query_params(self, mock_session):
        response_body = '{"caSets":[{"accountId":"A-CCOUNT","caSetId":"199","caSetName":"test","description":"description","createdDate":"2025-04-01T15:33:48.464941Z","createdBy":"tester"}]}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.list_ca_sets(models.ListCASetsRequest(
            ca_set_name_prefix="test",
            activated_on="STAGING",
        ))
        assert len(result.ca_sets) == 1
        assert result.ca_sets[0].ca_set_name == "test"

    def test_200_ok_with_non_lower_case_network(self, mock_session):
        response_body = '{"caSets":[]}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.list_ca_sets(models.ListCASetsRequest(
            ca_set_name_prefix="foo",
            activated_on="PRODUCTION",
        ))
        assert len(result.ca_sets) == 0

    def test_200_ok_staging_production(self, mock_session):
        response_body = '{"caSets":[{"accountId":"A-CCOUNT","caSetId":"199","caSetName":"test","description":"description","createdDate":"2025-04-01T15:33:48.464941Z","createdBy":"tester"}]}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.list_ca_sets(models.ListCASetsRequest(
            activated_on="STAGING+PRODUCTION",
        ))
        assert len(result.ca_sets) == 1

    def test_invalid_activated_on_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.list_ca_sets(models.ListCASetsRequest(activated_on="PROD"))
        assert errors.ErrListCASets in exc.value.title
        assert "ActivatedOn:" in exc.value.detail

    def test_ca_set_name_prefix_too_long_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.list_ca_sets(models.ListCASetsRequest(
                ca_set_name_prefix="A" * 65,
            ))
        assert errors.ErrListCASets in exc.value.title
        assert "CASetNamePrefix:" in exc.value.detail

    def test_invalid_name_prefix_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.list_ca_sets(models.ListCASetsRequest(
                ca_set_name_prefix="###A",
            ))
        assert errors.ErrListCASets in exc.value.title
        assert "CASetNamePrefix:" in exc.value.detail

    def test_triple_periods_in_prefix_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.list_ca_sets(models.ListCASetsRequest(
                ca_set_name_prefix="AAA...A",
            ))
        assert errors.ErrListCASets in exc.value.title
        assert "cannot contain three consecutive periods" in exc.value.detail

    def test_500_internal_server_error(self, mock_session):
        response_body = '{"type":"internal_error","title":"Internal Server Error","detail":"Error processing request","status":500}'
        mock_response = create_mock_response(500, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.list_ca_sets(models.ListCASetsRequest())
        assert exc.value.status == 500


# ---------------------------------------------------------------------------
# TestDeleteCASet — from ca_set_test.go
# ---------------------------------------------------------------------------

class TestDeleteCASet:
    """Tests for delete_ca_set — mirrors Go TestDeleteCASet."""

    def test_202_accepted(self, mock_session):
        mock_response = create_mock_response(202)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        client.delete_ca_set(models.DeleteCASetRequest(ca_set_id="199"))

    def test_missing_required_params_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.delete_ca_set(models.DeleteCASetRequest())
        assert errors.ErrDeleteCASet in exc.value.title
        assert "CASetID: cannot be blank" in exc.value.detail

    def test_500_internal_server_error(self, mock_session):
        response_body = '{"type":"internal_error","title":"Internal Server Error","detail":"Error processing request","status":500}'
        mock_response = create_mock_response(500, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.delete_ca_set(models.DeleteCASetRequest(ca_set_id="199"))
        assert exc.value.status == 500

    def test_409_defense_edge_bound(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-bound-to-hostname","title":"CA set is in use.","detail":"Cannot delete the CA set test. It is currently in use by one or more Defense Edge CA set in properties.","status":409,"contextInfo":{"caSetId":"1","caSetName":"test"}}'
        mock_response = create_mock_response(409, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.delete_ca_set(models.DeleteCASetRequest(ca_set_id="1"))
        assert exc.value.is_equivalent(errors.ErrCASetBoundToHostname)

    def test_404_ca_set_not_found(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-not-found","title":"CA set is not found.","status":404,"detail":"CA set with caSetId 10 is not found.","contextInfo":{"caSetId":"10"}}'
        mock_response = create_mock_response(404, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.delete_ca_set(models.DeleteCASetRequest(ca_set_id="10"))
        assert exc.value.is_equivalent(errors.ErrDeleteCASetNotFound)

    def test_409_activation_deactivation_in_progress_prod(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-cannot-be-deleted-in-progress-version-activations","title":"CA set cannot be deleted as there are in progress version activations","detail":"Cannot delete CA set 1 as there are in progress version activations.","status":409,"contextInfo":{"caSetId":"1","caSetName":"test","productionStatus":"IN_PROGRESS","stagingStatus":"INACTIVE"}}'
        mock_response = create_mock_response(409, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.delete_ca_set(models.DeleteCASetRequest(ca_set_id="1"))
        assert exc.value.is_equivalent(errors.ErrDeleteActivationDeactivationInProgress)

    def test_409_activation_deactivation_in_progress_staging(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-cannot-be-deleted-in-progress-version-activations","title":"CA set cannot be deleted as there are in progress version activations","detail":"Cannot delete CA set 1 as there are in progress version activations.","status":409,"contextInfo":{"caSetId":"1","caSetName":"test","productionStatus":"INACTIVE","stagingStatus":"IN_PROGRESS"}}'
        mock_response = create_mock_response(409, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.delete_ca_set(models.DeleteCASetRequest(ca_set_id="1"))
        assert exc.value.is_equivalent(errors.ErrDeleteActivationDeactivationInProgress)

    def test_409_activation_deactivation_in_progress_both(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-cannot-be-deleted-in-progress-version-activations","title":"CA set cannot be deleted as there are in progress version activations","detail":"Cannot delete CA set 1 as there are in progress version activations.","status":409,"contextInfo":{"caSetId":"1","caSetName":"test","productionStatus":"IN_PROGRESS","stagingStatus":"IN_PROGRESS"}}'
        mock_response = create_mock_response(409, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.delete_ca_set(models.DeleteCASetRequest(ca_set_id="1"))
        assert exc.value.is_equivalent(errors.ErrDeleteActivationDeactivationInProgress)

    def test_409_deletion_in_progress_both(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/delete-ca-set-request-in-progress","title":"DELETE request is in progress for the CA set on the network.","detail":"Cannot delete CA set 1 as it is being deleted on one or more networks.","status":409,"contextInfo":{"caSetId":"1","caSetName":"test","productionStatus":"IN_PROGRESS","stagingStatus":"IN_PROGRESS","deletionLink":"/mtls-edge-truststore/v2/ca-sets/1/status/delete"}}'
        mock_response = create_mock_response(409, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.delete_ca_set(models.DeleteCASetRequest(ca_set_id="1"))
        assert exc.value.is_equivalent(errors.ErrCASetDeleteRequestInProgress)

    def test_409_deletion_in_progress_one_network(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/delete-ca-set-request-in-progress","title":"DELETE request is in progress for the CA set on the network.","detail":"Cannot delete CA set 1 as it is being deleted on one or more networks.","status":409,"contextInfo":{"caSetId":"1","caSetName":"test","productionStatus":"IN_PROGRESS","stagingStatus":"COMPLETE","deletionLink":"/mtls-edge-truststore/v2/ca-sets/1/status/delete"}}'
        mock_response = create_mock_response(409, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.delete_ca_set(models.DeleteCASetRequest(ca_set_id="1"))
        assert exc.value.is_equivalent(errors.ErrCASetDeleteRequestInProgress)

    def test_400_unknown_query_params(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/unknown-query-parameters","title":"Invalid request.","detail":"Request is invalid.","status":400,"errors":[{"detail":"Unknown query parameter names found: test","pointer":"/test","type":"/mtls-edge-truststore/error-types/unknown-query-parameters"}]}'
        mock_response = create_mock_response(400, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.delete_ca_set(models.DeleteCASetRequest(ca_set_id="199"))
        assert exc.value.is_equivalent(errors.ErrUnknownQueryParameters)


# ---------------------------------------------------------------------------
# TestListCASetAssociations — from ca_set_test.go
# ---------------------------------------------------------------------------

class TestListCASetAssociations:
    """Tests for list_ca_set_associations — mirrors Go TestListCASetAssociations."""

    def test_200_ok_no_associations(self, mock_session):
        response_body = '{"associations":{"properties":[],"enrollments":null}}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.list_ca_set_associations(
            models.ListCASetAssociationsRequest(ca_set_id="1"))
        assert not result.associations.properties
        assert not result.associations.enrollments

    def test_200_ok_navigable_property(self, mock_session):
        response_body = '{"associations":{"properties":[{"propertyId":"123","propertyName":"test-prp-name","propertyLink":"/papi/v1/properties/123","assetId":123456,"groupId":345,"hostnames":[{"hostName":"example.com","network":"STAGING","status":"ATTACHED"}]}],"enrollments":null}}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.list_ca_set_associations(
            models.ListCASetAssociationsRequest(
                ca_set_id="1", association_type="properties"))
        assert len(result.associations.properties) == 1
        prop = result.associations.properties[0]
        assert prop.property_id == "123"
        assert prop.property_name == "test-prp-name"
        assert prop.property_link == "/papi/v1/properties/123"
        assert prop.asset_id == 123456
        assert prop.group_id == 345
        assert len(prop.hostnames) == 1
        assert prop.hostnames[0].hostname == "example.com"
        assert prop.hostnames[0].network == "STAGING"
        assert prop.hostnames[0].status == "ATTACHED"

    def test_200_ok_non_navigable_property(self, mock_session):
        response_body = '{"associations":{"properties":[{"propertyId":"123","propertyLink":"/papi/v1/properties/123","hostnames":[{"hostName":"example.com","network":"STAGING","status":"ATTACHED"}]}],"enrollments":null}}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.list_ca_set_associations(
            models.ListCASetAssociationsRequest(ca_set_id="1"))
        assert len(result.associations.properties) == 1
        prop = result.associations.properties[0]
        assert prop.property_id == "123"
        assert prop.property_name is None
        assert prop.property_link == "/papi/v1/properties/123"
        assert prop.asset_id is None
        assert prop.group_id is None
        assert len(prop.hostnames) == 1
        assert prop.hostnames[0].hostname == "example.com"

    def test_200_ok_enrollments(self, mock_session):
        response_body = '{"associations":{"properties":null,"enrollments":[{"enrollmentId":123456,"enrollmentLink":"/cps/v2/enrollments/123456","stagingSlots":[78956],"productionSlots":[78956,56478],"cn":"example1.com"},{"enrollmentId":123457,"enrollmentLink":"/cps/v2/enrollments/123457","stagingSlots":[23456],"productionSlots":[23456],"cn":"example2.com"}]}}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.list_ca_set_associations(
            models.ListCASetAssociationsRequest(
                ca_set_id="1", association_type="enrollments"))
        assert not result.associations.properties
        assert len(result.associations.enrollments) == 2
        e1 = result.associations.enrollments[0]
        assert e1.enrollment_id == 123456
        assert e1.enrollment_link == "/cps/v2/enrollments/123456"
        assert e1.staging_slots == [78956]
        assert e1.production_slots == [78956, 56478]
        assert e1.cn == "example1.com"
        e2 = result.associations.enrollments[1]
        assert e2.enrollment_id == 123457
        assert e2.cn == "example2.com"

    def test_missing_required_params_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.list_ca_set_associations(models.ListCASetAssociationsRequest())
        assert errors.ErrListCASetAssociations in exc.value.title
        assert "CASetID: cannot be blank" in exc.value.detail

    def test_invalid_association_type_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.list_ca_set_associations(
                models.ListCASetAssociationsRequest(
                    ca_set_id="199", association_type="INVALID"))
        assert errors.ErrListCASetAssociations in exc.value.title
        assert "AssociationType:" in exc.value.detail

    def test_404_ca_set_not_found(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-not-found","title":"CA set is not found.","status":404,"detail":"CA set with caSetId 10 is not found.","contextInfo":{"caSetId":"10"}}'
        mock_response = create_mock_response(404, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.list_ca_set_associations(
                models.ListCASetAssociationsRequest(ca_set_id="10"))
        assert exc.value.is_equivalent(errors.ErrGetCASetNotFound)

    def test_504_gateway_timeout(self, mock_session):
        response_body = '{"contextInfo":{"caSetId":1,"caSetName":"caSetName-1"},"detail":"There are issues fetching the information about associations at this time. The request timed out. Try again later.","status":504,"title":"Couldn\'t fetch associations details. Timeout occurred.","type":"/mtls-edge-truststore/error-types/cannot-get-ca-set-associations-timeout"}'
        mock_response = create_mock_response(504, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.list_ca_set_associations(
                models.ListCASetAssociationsRequest(ca_set_id="1"))
        assert exc.value.is_equivalent(errors.ErrFetchAssociationsTimeout)


# ---------------------------------------------------------------------------
# TestCloneCASet — from ca_set_test.go
# ---------------------------------------------------------------------------

class TestCloneCASet:
    """Tests for clone_ca_set — mirrors Go TestCloneCASet."""

    def test_201_created_no_version(self, mock_session):
        response_body = '{"accountId":"1-ACC","caSetId":"2","caSetLink":"/mtls-edge-truststore/v2/ca-sets/2","caSetName":"new-set","caSetStatus":"NOT_DELETED","createdBy":"user1","createdDate":"2025-04-10T07:03:32.987904Z","deletedBy":null,"deletedDate":null,"description":"New CA Set","latestVersion":1,"latestVersionLink":"/mtls-edge-truststore/v2/ca-sets/2/versions/1","productionVersion":null,"productionVersionLink":null,"stagingVersion":null,"stagingVersionLink":null,"versionsLink":"/mtls-edge-truststore/v2/ca-sets/2/versions/"}'
        mock_response = create_mock_response(201, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.clone_ca_set(models.CloneCASetRequest(
            clone_from_set_id="1",
            new_ca_set_name="new-set",
            new_description="New CA Set",
        ))
        assert result.account_id == "1-ACC"
        assert result.ca_set_id == "2"
        assert result.ca_set_link == "/mtls-edge-truststore/v2/ca-sets/2"
        assert result.ca_set_name == "new-set"
        assert result.ca_set_status == "NOT_DELETED"
        assert result.created_by == "user1"
        assert result.created_date == "2025-04-10T07:03:32.987904Z"
        assert result.deleted_by is None
        assert result.deleted_date is None
        assert result.description == "New CA Set"
        assert result.latest_version == 1
        assert result.latest_version_link == "/mtls-edge-truststore/v2/ca-sets/2/versions/1"
        assert result.production_version is None
        assert result.staging_version is None
        assert result.versions_link == "/mtls-edge-truststore/v2/ca-sets/2/versions/"

    def test_201_created_with_version(self, mock_session):
        response_body = '{"accountId":"1-ACC","caSetId":"2","caSetLink":"/mtls-edge-truststore/v2/ca-sets/2","caSetName":"new-set","caSetStatus":"NOT_DELETED","createdBy":"user1","createdDate":"2025-04-10T07:03:32.987904Z","deletedBy":null,"deletedDate":null,"description":null,"latestVersion":1,"latestVersionLink":"/mtls-edge-truststore/v2/ca-sets/2/versions/1","productionVersion":null,"productionVersionLink":null,"stagingVersion":null,"stagingVersionLink":null,"versionsLink":"/mtls-edge-truststore/v2/ca-sets/2/versions/"}'
        mock_response = create_mock_response(201, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.clone_ca_set(models.CloneCASetRequest(
            clone_from_set_id="1",
            clone_from_version=2,
            new_ca_set_name="new-set",
        ))
        assert result.account_id == "1-ACC"
        assert result.ca_set_id == "2"
        assert result.description is None

    def test_missing_ca_set_id_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.clone_ca_set(models.CloneCASetRequest())
        assert errors.ErrCloneCASet in exc.value.title
        assert "CloneFromSetID: cannot be blank" in exc.value.detail
        assert "NewCASetName: cannot be blank" in exc.value.detail

    def test_missing_ca_set_name_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.clone_ca_set(models.CloneCASetRequest(
                clone_from_set_id="1",
            ))
        assert errors.ErrCloneCASet in exc.value.title
        assert "NewCASetName: cannot be blank" in exc.value.detail

    def test_name_too_short_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.clone_ca_set(models.CloneCASetRequest(
                clone_from_set_id="1",
                new_ca_set_name="a",
            ))
        assert errors.ErrCloneCASet in exc.value.title
        assert "NewCASetName: the length must be between 3 and 64" in exc.value.detail

    def test_invalid_name_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.clone_ca_set(models.CloneCASetRequest(
                clone_from_set_id="1",
                new_ca_set_name="#edgegrid",
                new_description="New CA Set",
            ))
        assert errors.ErrCloneCASet in exc.value.title
        assert "NewCASetName:" in exc.value.detail

    def test_triple_periods_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.clone_ca_set(models.CloneCASetRequest(
                clone_from_set_id="1",
                new_ca_set_name="abc...cba",
            ))
        assert errors.ErrCloneCASet in exc.value.title
        assert "cannot contain three consecutive periods" in exc.value.detail

    def test_400_no_version(self, mock_session):
        response_body = '{"contextInfo":{"caSetId":"1","caSetName":"test1"},"detail":"CA set with caSetId 1 does not contain any versions. At least one version must be present to clone the CA set.","status":400,"title":"CA set does not contain any versions.","type":"/mtls-edge-truststore/error-types/missing-caset-version"}'
        mock_response = create_mock_response(400, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.clone_ca_set(models.CloneCASetRequest(
                clone_from_set_id="1",
                new_ca_set_name="new-set",
            ))
        assert exc.value.is_equivalent(errors.ErrMissingCASetVersion)

    def test_404_ca_set_not_found(self, mock_session):
        response_body = '{"contextInfo":{"caSetId":2},"detail":"Cannot clone CA set as the CA set with caSetId 2 is not found.","status":404,"title":"CA set is not found.","type":"/mtls-edge-truststore/error-types/ca-set-not-found"}'
        mock_response = create_mock_response(404, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.clone_ca_set(models.CloneCASetRequest(
                clone_from_set_id="2",
                new_ca_set_name="new-set",
            ))
        assert exc.value.is_equivalent(errors.ErrGetCASetNotFound)

    def test_404_ca_set_version_not_found(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-version-not-found","title":"CA set version not found","status":404,"detail":"Cannot clone CA set as the CA set version with version 2 is not found in the CA set under caSetName test1.","contextInfo":{"caSetName":"test1","caSetId":"1","version":2}}'
        mock_response = create_mock_response(404, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.clone_ca_set(models.CloneCASetRequest(
                clone_from_set_id="1",
                clone_from_version=2,
                new_ca_set_name="new-set",
            ))
        assert exc.value.is_equivalent(errors.ErrGetCASetVersionNotFound)

    def test_409_duplicate_name(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-name-is-not-unique","title":"CA set name already exists","status":409,"detail":"CA set with caSetName new-set cannot be created as another CA set with the same name exists in the account with accountId 1-ACC.","contextInfo":{"caSetName":"new-set","accountId":"1-ACC"}}'
        mock_response = create_mock_response(409, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.clone_ca_set(models.CloneCASetRequest(
                clone_from_set_id="1",
                new_ca_set_name="new-set",
            ))
        assert exc.value.is_equivalent(errors.ErrCASetNameNotUnique)

    def test_422_ca_set_limit_reached(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-limit-reached","title":"Cannot create a new CA set. Maximum allowed CA set limit has been reached.","status":422,"detail":"Cannot create CA set as you have already reached or exceeded the maximum allowed CA set limit of 2 for your account. Please delete any unused or unwanted CA sets before you attempt to create a new CA set.","contextInfo":{"accountId":"1-ACC","currentSetCount":2,"limit":2}}'
        mock_response = create_mock_response(422, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.clone_ca_set(models.CloneCASetRequest(
                clone_from_set_id="1",
                new_ca_set_name="new-set",
            ))
        assert exc.value.is_equivalent(errors.ErrCASetLimitReached)


# ---------------------------------------------------------------------------
# TestGetCASetDeletionStatus — from ca_set_test.go
# ---------------------------------------------------------------------------

class TestGetCASetDeletionStatus:
    """Tests for get_ca_set_deletion_status — mirrors Go TestGetCASetDeletionStatus."""

    def test_202_accepted(self, mock_session):
        response_body = '{"caSetId":"1","caSetLink":"/mtls-edge-truststore/v2/ca-sets/1","caSetName":"test1","deletions":[{"failureReason":null,"network":"PRODUCTION","percentComplete":0,"status":"IN_PROGRESS"},{"failureReason":null,"network":"STAGING","percentComplete":0,"status":"IN_PROGRESS"}],"endTime":null,"estimatedEndTime":"2025-04-15T12:25:02.183294Z","failureReason":null,"resourceMethod":"delete","startTime":"2025-04-15T12:10:02.039140Z","status":"IN_PROGRESS","statusLink":"/mtls-edge-truststore/v2/ca-sets/1/status/delete"}'
        mock_response = create_mock_response(202, response_body,
                                             {"Retry-After": "Tue, 15 Apr 2025 12:15:02 GMT"})
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.get_ca_set_deletion_status(
            models.GetCASetDeletionStatusRequest(ca_set_id="1"))
        assert result.ca_set_id == "1"
        assert result.ca_set_name == "test1"
        assert result.status == "IN_PROGRESS"
        assert len(result.deletions) == 2
        assert result.deletions[0].network == "PRODUCTION"
        assert result.deletions[0].status == "IN_PROGRESS"
        assert result.deletions[0].percent_complete == 0
        assert result.deletions[1].network == "STAGING"
        assert result.deletions[1].status == "IN_PROGRESS"
        assert result.estimated_end_time == "2025-04-15T12:25:02.183294Z"
        assert result.start_time == "2025-04-15T12:10:02.039140Z"
        assert result.end_time is None
        assert result.retry_after is not None

    def test_200_ok(self, mock_session):
        response_body = '{"caSetId":"1","caSetLink":"/mtls-edge-truststore/v2/ca-sets/1","caSetName":"test1","deletions":[{"failureReason":null,"network":"PRODUCTION","percentComplete":100,"status":"COMPLETE"},{"failureReason":null,"network":"STAGING","percentComplete":100,"status":"COMPLETE"}],"endTime":"2025-04-15T12:13:30.082193Z","estimatedEndTime":null,"failureReason":null,"resourceMethod":"delete","startTime":"2025-04-15T12:10:02.039140Z","status":"COMPLETE","statusLink":"/mtls-edge-truststore/v2/ca-sets/1/status/delete"}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.get_ca_set_deletion_status(
            models.GetCASetDeletionStatusRequest(ca_set_id="1"))
        assert result.status == "COMPLETE"
        assert len(result.deletions) == 2
        assert result.deletions[0].status == "COMPLETE"
        assert result.deletions[0].percent_complete == 100
        assert result.deletions[1].status == "COMPLETE"
        assert result.end_time == "2025-04-15T12:13:30.082193Z"
        assert result.retry_after == ""

    def test_207_multi_status(self, mock_session):
        response_body = '{"caSetId":"1","caSetLink":"/mtls-edge-truststore/v2/ca-sets/1","caSetName":"test1","deletions":[{"failureReason":"Reason for failure","network":"STAGING","percentComplete":100,"status":"FAILED"},{"network":"PRODUCTION","percentComplete":100,"status":"COMPLETE"}],"endTime":"2025-04-15T12:13:30.082193Z","failureReason":"Indication of which network had a failure in deletion.","resourceMethod":"delete","startTime":"2025-04-15T12:10:02.039140Z","status":"FAILED","statusLink":"/mtls-edge-truststore/v2/ca-sets/1/status/delete"}'
        mock_response = create_mock_response(202, response_body,
                                             {"Retry-After": "Tue, 15 Apr 2025 12:15:02 GMT"})
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.get_ca_set_deletion_status(
            models.GetCASetDeletionStatusRequest(ca_set_id="1"))
        assert result.status == "FAILED"
        assert result.failure_reason == "Indication of which network had a failure in deletion."
        assert len(result.deletions) == 2
        assert result.deletions[0].network == "STAGING"
        assert result.deletions[0].status == "FAILED"
        assert result.deletions[0].failure_reason == "Reason for failure"
        assert result.deletions[1].network == "PRODUCTION"
        assert result.deletions[1].status == "COMPLETE"
        assert result.retry_after is not None

    def test_missing_required_params_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set_deletion_status(
                models.GetCASetDeletionStatusRequest())
        assert errors.ErrGetCASetDeletionStatus in exc.value.title
        assert "CASetID: cannot be blank" in exc.value.detail

    def test_404_no_active_deletion(self, mock_session):
        response_body = '{"contextInfo":{"caSetId":"1"},"detail":"No active deletions were found for CA Certificate Set with set ID 1.","status":400,"title":"No active cert deletions found","type":"/mtls-edge-truststore/error-types/no-active-cert-deletions"}'
        mock_response = create_mock_response(400, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set_deletion_status(
                models.GetCASetDeletionStatusRequest(ca_set_id="1"))
        assert exc.value.is_equivalent(errors.ErrNoActiveCertDeletions)

    def test_404_ca_set_not_found(self, mock_session):
        response_body = '{"contextInfo":{"caSetId":"2"},"detail":"Cannot get CA set deletions as the CA set with caSetId 2 is not found.","status":404,"title":"CA set is not found.","type":"/mtls-edge-truststore/error-types/ca-set-not-found"}'
        mock_response = create_mock_response(404, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set_deletion_status(
                models.GetCASetDeletionStatusRequest(ca_set_id="2"))
        assert exc.value.is_equivalent(errors.ErrGetCASetNotFound)


# ---------------------------------------------------------------------------
# TestListCASetActivities — from ca_set_test.go
# ---------------------------------------------------------------------------

class TestListCASetActivities:
    """Tests for list_ca_set_activities — mirrors Go TestListCASetActivities."""

    def test_200_no_query_params(self, mock_session):
        response_body = '{"activities":[{"activityBy":"user1","activityDate":"2025-04-18T11:30:35.866481Z","network":"PRODUCTION","type":"DELETE_CA_SET","version":null},{"activityBy":"user1","activityDate":"2025-04-18T11:30:35.852930Z","network":"STAGING","type":"DELETE_CA_SET","version":null},{"activityBy":"user1","activityDate":"2025-04-16T13:14:46.183261Z","network":null,"type":"CREATE_CA_SET_VERSION","version":2},{"activityBy":"user1","activityDate":"2025-04-15T13:35:48.292127Z","network":null,"type":"CREATE_CA_SET_VERSION","version":1},{"activityBy":"user1","activityDate":"2025-04-15T13:35:48.257574Z","network":null,"type":"CREATE_CA_SET","version":null}],"caSetId":"1","caSetLink":"/mtls-edge-truststore/v2/ca-sets/1","caSetName":"test1","caSetStatus":"DELETED","createdBy":"user1","createdDate":"2025-04-15T13:35:48.211999Z","deletedBy":"user1","deletedDate":"2025-04-18T11:31:40.225213Z"}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.list_ca_set_activities(
            models.ListCASetActivitiesRequest(ca_set_id="1"))
        assert len(result.activities) == 5
        assert result.activities[0].type == "DELETE_CA_SET"
        assert result.activities[0].activity_by == "user1"
        assert result.activities[0].network == "PRODUCTION"
        assert result.activities[0].version is None
        assert result.activities[2].type == "CREATE_CA_SET_VERSION"
        assert result.activities[2].version == 2
        assert result.activities[2].network is None
        assert result.ca_set_id == "1"
        assert result.ca_set_name == "test1"
        assert result.ca_set_status == "DELETED"
        assert result.deleted_by == "user1"

    def test_200_all_query_params(self, mock_session):
        response_body = '{"activities":[{"action":"ACTIVATE","actionedBy":"test-user2","actionedDate":"2025-04-15T14:00:00Z","version":1,"network":"STAGING"}]}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.list_ca_set_activities(
            models.ListCASetActivitiesRequest(
                ca_set_id="199",
                start="2025-04-15T14:00:00Z",
                end="2025-04-17T14:00:00Z",
            ))
        assert len(result.activities) == 1

    def test_missing_required_params_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.list_ca_set_activities(models.ListCASetActivitiesRequest())
        assert errors.ErrListCASetActivities in exc.value.title
        assert "CASetID: cannot be blank" in exc.value.detail

    def test_404_ca_set_not_found(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-not-found","title":"CA set is not found.","status":404,"detail":"CA set with caSetId 10 is not found.","contextInfo":{"caSetId":"10"}}'
        mock_response = create_mock_response(404, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.list_ca_set_activities(
                models.ListCASetActivitiesRequest(ca_set_id="10"))
        assert exc.value.is_equivalent(errors.ErrGetCASetNotFound)


# ---------------------------------------------------------------------------
# TestValidateCertificates — from certificate_test.go
# ---------------------------------------------------------------------------

class TestValidateCertificates:
    """Tests for validate_certificates — mirrors Go TestValidateCertificates."""

    def test_200_valid_certs(self, mock_session):
        response_body = '{"allowInsecureSha1":false,"certificates":[{"certificatePem":"-----BEGIN CERTIFICATE-----\\nCERT1\\n-----END CERTIFICATE-----","endDate":"2033-04-22T22:49:13Z","fingerprint":"aeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeae","issuer":"EMAILADDRESS=test1@example.com, CN=duplicate-test-cn.com, OU=Media BU, O=Akamai, L=SF, ST=CA, C=US","serialNumber":"dfdfdfdfdfdfdfdfdfdfdfdfdfdfdfdfdfdfdfdf","signatureAlgorithm":"SHA256WITHRSA","startDate":"2023-04-25T22:49:13Z","subject":"EMAILADDRESS=test1@example.com, CN=duplicate-test-cn.com, OU=Media BU, O=Akamai, L=SF, ST=CA, C=US"},{"certificatePem":"-----BEGIN CERTIFICATE-----\\nCERT2\\n-----END CERTIFICATE-----","description":"desc","endDate":"2033-04-22T23:22:06Z","fingerprint":"bcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbc","issuer":"EMAILADDRESS=test2@example.com, CN=test-example1.com, OU=Media BU, O=Akamai, L=SF, ST=CA, C=US","serialNumber":"a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1","signatureAlgorithm":"SHA256WITHRSA","startDate":"2023-04-25T23:22:06Z","subject":"EMAILADDRESS=test2@example.com, CN=test-example1.com, OU=Media BU, O=Akamai, L=SF, ST=CA, C=US"}],"validation":{"warnings":[]}}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.validate_certificates(models.ValidateCertificatesRequest(
            certificates=[
                models.ValidateCertificate(
                    certificate_pem="-----BEGIN CERTIFICATE-----\nCERT1\n-----END CERTIFICATE-----",
                ),
                models.ValidateCertificate(
                    certificate_pem="-----BEGIN CERTIFICATE-----\nCERT2\n-----END CERTIFICATE-----",
                    description="desc",
                ),
            ],
        ))
        assert result.allow_insecure_sha1 is False
        assert len(result.certificates) == 2
        assert result.certificates[0].certificate_pem == "-----BEGIN CERTIFICATE-----\nCERT1\n-----END CERTIFICATE-----"
        assert result.certificates[0].end_date == "2033-04-22T22:49:13Z"
        assert result.certificates[0].fingerprint == "aeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeae"
        assert result.certificates[0].issuer == "EMAILADDRESS=test1@example.com, CN=duplicate-test-cn.com, OU=Media BU, O=Akamai, L=SF, ST=CA, C=US"
        assert result.certificates[0].serial_number == "dfdfdfdfdfdfdfdfdfdfdfdfdfdfdfdfdfdfdfdf"
        assert result.certificates[0].signature_algorithm == "SHA256WITHRSA"
        assert result.certificates[0].start_date == "2023-04-25T22:49:13Z"
        assert result.certificates[0].subject == "EMAILADDRESS=test1@example.com, CN=duplicate-test-cn.com, OU=Media BU, O=Akamai, L=SF, ST=CA, C=US"
        assert result.certificates[1].certificate_pem == "-----BEGIN CERTIFICATE-----\nCERT2\n-----END CERTIFICATE-----"
        assert result.certificates[1].description == "desc"
        assert result.certificates[1].end_date == "2033-04-22T23:22:06Z"
        assert result.certificates[1].fingerprint == "bcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbc"
        assert result.certificates[1].serial_number == "a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1"
        assert not result.validation.warnings
        assert_request(mock_session, "POST", "/mtls-edge-truststore/v2/certificates/validate")

    def test_200_valid_certs_with_duplication_warning(self, mock_session):
        response_body = '{"allowInsecureSha1":false,"certificates":[{"certificatePem":"-----BEGIN CERTIFICATE-----\\nCERT1\\n-----END CERTIFICATE-----","endDate":"2033-04-22T22:49:13Z","fingerprint":"aeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeae","issuer":"EMAILADDRESS=test1@example.com, CN=duplicate-test-cn.com, OU=Media BU, O=Akamai, L=SF, ST=CA, C=US","serialNumber":"dfdfdfdfdfdfdfdfdfdfdfdfdfdfdfdfdfdfdfdf","signatureAlgorithm":"SHA256WITHRSA","startDate":"2023-04-25T22:49:13Z","subject":"EMAILADDRESS=test1@example.com, CN=duplicate-test-cn.com, OU=Media BU, O=Akamai, L=SF, ST=CA, C=US"},{"certificatePem":"-----BEGIN CERTIFICATE-----\\nCERT1\\n-----END CERTIFICATE-----","endDate":"2033-04-22T22:49:13Z","fingerprint":"aeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeae","issuer":"EMAILADDRESS=test1@example.com, CN=duplicate-test-cn.com, OU=Media BU, O=Akamai, L=SF, ST=CA, C=US","serialNumber":"dfdfdfdfdfdfdfdfdfdfdfdfdfdfdfdfdfdfdfdf","signatureAlgorithm":"SHA256WITHRSA","startDate":"2023-04-25T22:49:13Z","subject":"EMAILADDRESS=test1@example.com, CN=duplicate-test-cn.com, OU=Media BU, O=Akamai, L=SF, ST=CA, C=US"}],"validation":{"warnings":[{"contextInfo":{"fingerPrint":"aeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeae"},"detail":"The certificate with the fingerprint aeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeae has been submitted more than once. Duplicate certificates are not allowed.","pointer":"/certificates/1","title":"Duplicate certificate has been submitted in the certificates.","type":"/mtls-edge-truststore/v2/error-types/duplicate-certificate"}]}}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.validate_certificates(models.ValidateCertificatesRequest(
            certificates=[
                models.ValidateCertificate(
                    certificate_pem="-----BEGIN CERTIFICATE-----\nCERT1\n-----END CERTIFICATE-----",
                ),
                models.ValidateCertificate(
                    certificate_pem="-----BEGIN CERTIFICATE-----\nCERT1\n-----END CERTIFICATE-----",
                ),
            ],
        ))
        assert result.allow_insecure_sha1 is False
        assert len(result.certificates) == 2
        assert len(result.validation.warnings) == 1
        assert result.validation.warnings[0].type == "/mtls-edge-truststore/v2/error-types/duplicate-certificate"
        assert result.validation.warnings[0].title == "Duplicate certificate has been submitted in the certificates."
        assert result.validation.warnings[0].pointer == "/certificates/1"
        assert result.validation.warnings[0].detail == "The certificate with the fingerprint aeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeaeae has been submitted more than once. Duplicate certificates are not allowed."

    def test_missing_required_params_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.validate_certificates(models.ValidateCertificatesRequest())
        assert errors.ErrValidateCertificates in exc.value.title
        assert "Certificates: cannot be blank" in exc.value.detail

    def test_certificate_empty_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.validate_certificates(models.ValidateCertificatesRequest(
                certificates=[models.ValidateCertificate(certificate_pem="")],
            ))
        assert errors.ErrValidateCertificates in exc.value.title
        assert "CertificatePEM: cannot be blank" in exc.value.detail

    def test_400_invalid_certificate(self, mock_session):
        response_body = '{"errors":[{"contextInfo":{"certificatePem":"malformed","description":"desc"},"detail":"Certificate PEM string is missing -----BEGIN CERTIFICATE----- header.","pointer":"/certificates/0"}],"status":400,"title":"Certificate(s) has failed validation.","type":"/mtls-edge-truststore/error-types/certificate-validation-failure"}'
        mock_response = create_mock_response(400, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.validate_certificates(models.ValidateCertificatesRequest(
                certificates=[
                    models.ValidateCertificate(
                        certificate_pem="malformed",
                        description="desc",
                    ),
                ],
            ))
        assert exc.value.is_equivalent(errors.ErrCertValidationFailure)

    def test_400_expired_certificate_as_duplicate(self, mock_session):
        response_body = '{"errors":[{"contextInfo":{"checkDate":"2025-03-06T10:00:21Z","expiryDate":"2023-04-23T17:00:34Z","fingerPrint":"bcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbc","subject":"EMAILADDRESS=test1@example.com, CN=duplicate-test-cn.com, OU=Media BU, O=Akamai, L=SF, ST=CA, C=US"},"detail":"The certificate with subject EMAILADDRESS=test1@example.com, CN=duplicate-test-cn.com, OU=Media BU, O=Akamai, L=SF, ST=CA, C=US and fingerprint bcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbc has expired. Expiry date is 2023-04-23T17:00:34Z. The check was performed on 2025-03-06T10:00:21Z.","pointer":"/certificates/0"},{"contextInfo":{"checkDate":"2025-03-06T10:00:21Z","expiryDate":"2023-04-23T17:00:34Z","fingerPrint":"bcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbc","subject":"EMAILADDRESS=test1@example.com, CN=duplicate-test-cn.com, OU=Media BU, O=Akamai, L=SF, ST=CA, C=US"},"detail":"The certificate with subject EMAILADDRESS=test1@example.com, CN=duplicate-test-cn.com, OU=Media BU, O=Akamai, L=SF, ST=CA, C=US and fingerprint bcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbc has expired. Expiry date is 2023-04-23T17:00:34Z. The check was performed on 2025-03-06T10:00:21Z.","pointer":"/certificates/1"}],"status":400,"title":"Certificate(s) has failed validation.","type":"/mtls-edge-truststore/error-types/certificate-validation-failure"}'
        mock_response = create_mock_response(400, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.validate_certificates(models.ValidateCertificatesRequest(
                certificates=[
                    models.ValidateCertificate(
                        certificate_pem="malformed",
                        description="desc",
                    ),
                ],
            ))
        assert exc.value.is_equivalent(errors.ErrCertValidationFailure)
        assert len(exc.value.errors) == 2


# ---------------------------------------------------------------------------
# TestActivateCASetVersion — from ca_set_activation_test.go
# ---------------------------------------------------------------------------

class TestActivateCASetVersion:
    """Tests for activate_ca_set_version — mirrors Go TestActivateCASetVersion."""

    def test_202_accepted(self, mock_session):
        response_body = '{"activationId":84707,"activationLink":"/mtls-edge-truststore/v2/ca-sets/199/versions/1/activations/84707","caSetId":"199","caSetName":"test1","caSetLink":"/mtls-edge-truststore/v2/ca-sets/199","createdBy":"jsmith@example.com","createdDate":"2023-06-01T23:02:29.876589Z","failureReason":null,"modifiedBy":null,"modifiedDate":null,"network":"STAGING","activationStatus":"IN_PROGRESS","activationType":"ACTIVATE","percentComplete":0,"validation":{"warnings":[]},"version":1,"versionLink":"/mtls-edge-truststore/v2/ca-sets/199/versions/1"}'
        mock_response = create_mock_response(202, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.activate_ca_set_version(models.ActivateCASetVersionRequest(
            ca_set_id="199",
            version=1,
            network="PRODUCTION",
        ))
        assert result.activation_id == 84707
        assert result.activation_link == "/mtls-edge-truststore/v2/ca-sets/199/versions/1/activations/84707"
        assert result.ca_set_id == "199"
        assert result.ca_set_name == "test1"
        assert result.ca_set_link == "/mtls-edge-truststore/v2/ca-sets/199"
        assert result.created_by == "jsmith@example.com"
        assert result.created_date == "2023-06-01T23:02:29.876589Z"
        assert result.failure_reason is None
        assert result.modified_by is None
        assert result.modified_date is None
        assert result.network == "STAGING"
        assert result.activation_status == "IN_PROGRESS"
        assert result.activation_type == "ACTIVATE"
        assert result.percent_complete == 0
        assert result.version == 1
        assert result.version_link == "/mtls-edge-truststore/v2/ca-sets/199/versions/1"
        assert not result.validation.warnings
        assert_request(mock_session, "POST",
                       "/mtls-edge-truststore/v2/ca-sets/199/versions/1/activate",
                       {"network": "PRODUCTION"})

    def test_202_accepted_with_warning(self, mock_session):
        response_body = '{"activationId":84707,"activationLink":"/mtls-edge-truststore/v2/ca-sets/199/versions/1/activations/84707","caSetId":"199","caSetName":"test1","caSetLink":"/mtls-edge-truststore/v2/ca-sets/199","createdBy":"jsmith@example.com","createdDate":"2023-06-01T23:02:29.876589Z","failureReason":null,"modifiedBy":null,"modifiedDate":null,"network":"STAGING","activationStatus":"IN_PROGRESS","activationType":"ACTIVATE","percentComplete":0,"validation":{"warnings":[{"detail":"A request was submitted to activate the CA set version on production without activating on staging first. While this is allowed, it is highly recommended to first deploy the CA set version on staging network and ensure that there are no issues in serving the traffic.","title":"Request was submitted to activate the CA set version on production without activating on staging first.","type":"/mtls-edge-truststore/error-types/activate-version-on-production-without-activating-on-staging"}]},"version":1,"versionLink":"/mtls-edge-truststore/v2/ca-sets/199/versions/1"}'
        mock_response = create_mock_response(202, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.activate_ca_set_version(models.ActivateCASetVersionRequest(
            ca_set_id="199",
            version=1,
            network="PRODUCTION",
        ))
        assert len(result.validation.warnings) == 1
        assert result.validation.warnings[0].type == "/mtls-edge-truststore/error-types/activate-version-on-production-without-activating-on-staging"
        assert result.validation.warnings[0].title == "Request was submitted to activate the CA set version on production without activating on staging first."

    def test_missing_required_params_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.activate_ca_set_version(models.ActivateCASetVersionRequest())
        assert errors.ErrActivateCASetVersion in exc.value.title
        assert "CASetID: cannot be blank" in exc.value.detail
        assert "Network: cannot be blank" in exc.value.detail
        assert "Version: cannot be blank" in exc.value.detail

    def test_invalid_network_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.activate_ca_set_version(models.ActivateCASetVersionRequest(
                ca_set_id="199", version=1, network="foo"))
        assert errors.ErrActivateCASetVersion in exc.value.title
        assert "Network:" in exc.value.detail
        assert "'STAGING' or 'PRODUCTION'" in exc.value.detail

    def test_409_cannot_be_activated(self, mock_session):
        response_body = '{"contextInfo":{"caSetId":"199","caSetName":"DXE-5498","network":"STAGING","version":1},"detail":"CA set version with version 1 cannot be activated as it is already active on the STAGING network.","instance":"/mtls-edge-truststore/error-types/ca-set-version-already-active-on-network/1916882c5af2b20b","status":409,"title":"CA set version cannot be activated as it is already active on the network.","type":"/mtls-edge-truststore/error-types/ca-set-version-already-active-on-network"}'
        mock_response = create_mock_response(409, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.activate_ca_set_version(models.ActivateCASetVersionRequest(
                ca_set_id="199", version=1, network="STAGING"))
        assert exc.value.is_equivalent(
            errors.ErrCASetVersionIsActiveOnNetworkCannotBeActivated)

    def test_500_internal_server_error(self, mock_session):
        response_body = '{"type":"internal-server-error","title":"Internal Server Error","detail":"Error processing request","instance":"TestInstances","status":500}'
        mock_response = create_mock_response(500, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.activate_ca_set_version(models.ActivateCASetVersionRequest(
                ca_set_id="199", version=1, network="PRODUCTION"))
        assert exc.value.status == 500


# ---------------------------------------------------------------------------
# TestDeactivateCASetVersion — from ca_set_activation_test.go
# ---------------------------------------------------------------------------

class TestDeactivateCASetVersion:
    """Tests for deactivate_ca_set_version — mirrors Go TestDeactivateCASetVersion."""

    def test_202_accepted(self, mock_session):
        response_body = '{"activationId":84707,"activationLink":"/mtls-edge-truststore/v2/ca-sets/199/versions/1/activations/84707","caSetId":"199","caSetName":"test1","caSetLink":"/mtls-edge-truststore/v2/ca-sets/199","createdBy":"jsmith@example.com","createdDate":"2023-06-01T23:02:29.876589Z","failureReason":null,"modifiedBy":null,"modifiedDate":null,"network":"STAGING","activationStatus":"IN_PROGRESS","activationType":"DEACTIVATE","percentComplete":0,"validation":{"warnings":[]},"version":1,"versionLink":"/mtls-edge-truststore/v2/ca-sets/199/versions/1"}'
        mock_response = create_mock_response(202, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.deactivate_ca_set_version(models.DeactivateCASetVersionRequest(
            ca_set_id="199",
            version=1,
            network="PRODUCTION",
        ))
        assert result.activation_id == 84707
        assert result.activation_link == "/mtls-edge-truststore/v2/ca-sets/199/versions/1/activations/84707"
        assert result.ca_set_id == "199"
        assert result.ca_set_name == "test1"
        assert result.ca_set_link == "/mtls-edge-truststore/v2/ca-sets/199"
        assert result.created_by == "jsmith@example.com"
        assert result.created_date == "2023-06-01T23:02:29.876589Z"
        assert result.failure_reason is None
        assert result.modified_by is None
        assert result.modified_date is None
        assert result.network == "STAGING"
        assert result.activation_status == "IN_PROGRESS"
        assert result.activation_type == "DEACTIVATE"
        assert result.percent_complete == 0
        assert result.version == 1
        assert result.version_link == "/mtls-edge-truststore/v2/ca-sets/199/versions/1"
        assert not result.validation.warnings
        assert_request(mock_session, "POST",
                       "/mtls-edge-truststore/v2/ca-sets/199/versions/1/deactivate",
                       {"network": "PRODUCTION"})

    def test_202_accepted_with_warning(self, mock_session):
        response_body = '{"activationId":84707,"activationLink":"/mtls-edge-truststore/v2/ca-sets/199/versions/1/activations/84707","caSetId":"199","caSetName":"test1","caSetLink":"/mtls-edge-truststore/v2/ca-sets/199","createdBy":"jsmith@example.com","createdDate":"2023-06-01T23:02:29.876589Z","failureReason":null,"modifiedBy":null,"modifiedDate":null,"network":"STAGING","activationStatus":"IN_PROGRESS","activationType":"DEACTIVATE","percentComplete":0,"validation":{"warnings":[{"detail":"Example warning detail","title":"Example warning title","type":"/mtls-edge-truststore/error-types/example-type"}]},"version":1,"versionLink":"/mtls-edge-truststore/v2/ca-sets/199/versions/1"}'
        mock_response = create_mock_response(202, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.deactivate_ca_set_version(models.DeactivateCASetVersionRequest(
            ca_set_id="199",
            version=1,
            network="PRODUCTION",
        ))
        assert len(result.validation.warnings) == 1
        assert result.validation.warnings[0].type == "/mtls-edge-truststore/error-types/example-type"
        assert result.validation.warnings[0].title == "Example warning title"
        assert result.validation.warnings[0].detail == "Example warning detail"

    def test_409_in_use_by_enrollments_and_hostnames(self, mock_session):
        response_body = '{"contextInfo":{"associations":{"enrollments":[{"cn":"some.domain.com","enrollmentId":12345,"enrollmentLink":"/cps/v2/enrollments/12345","productionSlots":[],"stagingSlots":[123466]},{"cn":"some.domain.com","enrollmentId":12345,"enrollmentLink":"/cps/v2/enrollments/12345","productionSlots":[],"stagingSlots":[123456]}],"properties":[{"hostnames":[{"hostname":"some.domain.com","network":"PRODUCTION"},{"hostname":"some.domain.com","network":"STAGING"}],"propertyId":"1234567"}]},"caSetId":"132965","caSetName":"jsmith-mets-tpc-delete-test-3"},"detail":"CA set with caSetId 132965 is linked to several Certificate Provisioning System enrollments and Property Manager hostnames. You need to unlink the CA set from the enrollments and hostnames to proceed. See accompanying data for enrollment and hostname details.","instance":"/mtls-edge-truststore/error-types/ca-set-in-use-by-both-enrollments-and-hostnames/f2869f68451b8408","status":409,"title":"CA set is linked to both enrollments and hostnames.","type":"/mtls-edge-truststore/error-types/ca-set-in-use-by-both-enrollments-and-hostnames"}'
        mock_response = create_mock_response(409, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.deactivate_ca_set_version(models.DeactivateCASetVersionRequest(
                ca_set_id="199", version=1, network="PRODUCTION"))
        assert exc.value.is_equivalent(
            errors.ErrCASetInUseByBothEnrollmentsAndHostnames)

    def test_409_in_use_by_hostname(self, mock_session):
        response_body = '{"contextInfo":{"associations":{"properties":[{"hostnames":[{"hostname":"example-3.com"}],"propertyId":"2"}]},"caSetId":1,"caSetName":"foo","network":"PRODUCTION"},"detail":"CA set cannot be deactivated CA set with caSetId 1 links to several Property Manager hostnames. You need to unlink the CA set from the hostnames to proceed. See accompanying response data for hostname details.","status":409,"title":"CA set is linked to hostnames.","type":"/mtls-edge-truststore/error-types/ca-set-bound-to-hostname"}'
        mock_response = create_mock_response(409, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.deactivate_ca_set_version(models.DeactivateCASetVersionRequest(
                ca_set_id="199", version=1, network="PRODUCTION"))
        assert exc.value.is_equivalent(errors.ErrCASetBoundToHostname)

    def test_409_another_activation_in_progress(self, mock_session):
        response_body = '{"contextInfo":{"activationLink":"/mtls-edge-truststore/v2/ca-sets/199/versions/1/activations/1","activationType":"DEACTIVATE","caSetId":199,"caSetName":"foo","network":"PRODUCTION","version":1},"detail":"CA set with caSetId 1 and version 1 cannot be DEACTIVATED as another activation request is in progress for the CA set on the PRODUCTION network. Hypermedia link to the activation is attached.","status":409,"title":"Another activation request is in progress in the CA set.","type":"/mtls-edge-truststore/error-types/another-activation-request-in-progress-in-the-ca-set"}'
        mock_response = create_mock_response(409, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.deactivate_ca_set_version(models.DeactivateCASetVersionRequest(
                ca_set_id="199", version=1, network="PRODUCTION"))
        assert exc.value.is_equivalent(errors.ErrAnotherActivationInProgress)

    def test_409_another_deactivation_in_progress(self, mock_session):
        response_body = '{"contextInfo":{"activationLink":"/mtls-edge-truststore/v2/ca-sets/1/versions/1/activations/1","activationType":"DEACTIVATE","caSetId":1,"caSetName":"caSetName-1","network":"STAGING","version":1},"detail":"CA set version with version 1 cannot be DEACTIVATED as another deactivation request is in progress for the CA set with caSetId 1 on the STAGING network. Hypermedia link to the deactivation is attached.","status":409,"title":"Another deactivation request is in progress in the CA set.","type":"/mtls-edge-truststore/error-types/another-deactivation-request-in-progress-in-the-ca-set"}'
        mock_response = create_mock_response(409, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.deactivate_ca_set_version(models.DeactivateCASetVersionRequest(
                ca_set_id="199", version=1, network="PRODUCTION"))
        assert exc.value.is_equivalent(errors.ErrAnotherDeactivationInProgress)

    def test_409_not_active_on_network(self, mock_session):
        response_body = '{"contextInfo":{"caSetId":199,"caSetName":"foo","network":"STAGING","version":1},"detail":"CA set version with version 1 cannot be deactivated as it is not active on the STAGING network.","status":409,"title":"CA set version cannot be deactivated as it is not active on the network.","type":"/mtls-edge-truststore/error-types/ca-set-version-not-active-on-network"}'
        mock_response = create_mock_response(409, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.deactivate_ca_set_version(models.DeactivateCASetVersionRequest(
                ca_set_id="199", version=1, network="PRODUCTION"))
        assert exc.value.is_equivalent(errors.ErrCASetVersionNotActiveOnNetwork)

    def test_409_cannot_be_deactivated(self, mock_session):
        response_body = '{"contextInfo":{"caSetId":"199","caSetName":"DXE-5498","network":"STAGING","version":1},"detail":"CA set version with version 1 cannot be deactivated as it is not active on the STAGING network.","instance":"/mtls-edge-truststore/error-types/ca-set-version-not-active-on-network/0d0a2fb6c1c58594","status":409,"title":"CA set version cannot be deactivated as it is not active on the network.","type":"/mtls-edge-truststore/error-types/ca-set-version-not-active-on-network"}'
        mock_response = create_mock_response(409, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.deactivate_ca_set_version(models.DeactivateCASetVersionRequest(
                ca_set_id="199", version=1, network="STAGING"))
        assert exc.value.is_equivalent(
            errors.ErrCASetVersionNotActiveOnNetworkCannotBeDeactivated)

    def test_missing_required_params_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.deactivate_ca_set_version(
                models.DeactivateCASetVersionRequest())
        assert errors.ErrDeactivateCASetVersion in exc.value.title
        assert "CASetID: cannot be blank" in exc.value.detail
        assert "Network: cannot be blank" in exc.value.detail
        assert "Version: cannot be blank" in exc.value.detail

    def test_invalid_network_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.deactivate_ca_set_version(models.DeactivateCASetVersionRequest(
                ca_set_id="199", version=1, network="foo"))
        assert errors.ErrDeactivateCASetVersion in exc.value.title
        assert "Network:" in exc.value.detail

    def test_500_internal_server_error(self, mock_session):
        response_body = '{"type":"internal-server-error","title":"Internal Server Error","detail":"Error processing request","instance":"TestInstances","status":500}'
        mock_response = create_mock_response(500, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.deactivate_ca_set_version(models.DeactivateCASetVersionRequest(
                ca_set_id="199", version=1, network="PRODUCTION"))
        assert exc.value.status == 500


# ---------------------------------------------------------------------------
# TestGetCASetVersionActivation — from ca_set_activation_test.go
# ---------------------------------------------------------------------------

class TestGetCASetVersionActivation:
    """Tests for get_ca_set_version_activation — mirrors Go TestGetCASetVersionActivation."""

    def test_202_accepted_with_retry_after(self, mock_session):
        response_body = '{"activationId":84572,"activationLink":"/mtls-edge-truststore/v2/ca-sets/1000/versions/1000/activations/84572","caSetId":"1000","caSetName":"test1","caSetLink":"/mtls-edge-truststore/v2/ca-sets/1000","percentComplete":0,"validation":null,"version":1,"versionLink":"/mtls-edge-truststore/v2/ca-sets/1000/versions/1","network":"STAGING","activationType":"ACTIVATE","activationStatus":"IN_PROGRESS","createdDate":"2023-01-10T11:00:00.494383Z","createdBy":"someone","failureReason":null,"modifiedDate":"2023-01-10T12:00:00.771298Z","modifiedBy":"someone"}'
        mock_response = create_mock_response(
            202, response_body,
            {"Retry-After": "Tue, 10 Jan 2023 11:05:00 GMT"})
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.get_ca_set_version_activation(
            models.GetCASetVersionActivationRequest(
                ca_set_id="1000", version=1, activation_id=84572))
        assert result.activation_id == 84572
        assert result.activation_link == "/mtls-edge-truststore/v2/ca-sets/1000/versions/1000/activations/84572"
        assert result.ca_set_id == "1000"
        assert result.ca_set_name == "test1"
        assert result.percent_complete == 0
        assert result.network == "STAGING"
        assert result.activation_type == "ACTIVATE"
        assert result.activation_status == "IN_PROGRESS"
        assert result.created_by == "someone"
        assert result.modified_by == "someone"
        assert result.modified_date == "2023-01-10T12:00:00.771298Z"
        assert result.retry_after != ""

    def test_200_ok(self, mock_session):
        response_body = '{"activationId":84572,"activationLink":"/mtls-edge-truststore/v2/ca-sets/1000/versions/1000/activations/84572","caSetId":"1000","caSetName":"test1","caSetLink":"/mtls-edge-truststore/v2/ca-sets/1000","percentComplete":100,"version":1,"versionLink":"/mtls-edge-truststore/v2/ca-sets/1000/versions/1","network":"STAGING","activationType":"ACTIVATE","activationStatus":"COMPLETE","createdDate":"2023-01-10T11:00:00.494383Z","createdBy":"someone","failureReason":null,"modifiedDate":"2023-01-10T12:00:00.771298Z","modifiedBy":"someone"}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.get_ca_set_version_activation(
            models.GetCASetVersionActivationRequest(
                ca_set_id="1000", version=1, activation_id=84572))
        assert result.activation_id == 84572
        assert result.activation_status == "COMPLETE"
        assert result.percent_complete == 100
        assert result.modified_by == "someone"
        assert result.retry_after == ""

    def test_missing_required_params_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set_version_activation(
                models.GetCASetVersionActivationRequest())
        assert errors.ErrGetCASetVersionActivation in exc.value.title
        assert "ActivationID: cannot be blank" in exc.value.detail
        assert "CASetID: cannot be blank" in exc.value.detail
        assert "Version: cannot be blank" in exc.value.detail

    def test_404_ca_set_not_found(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-not-found","title":"CA set not found.","status":404,"detail":"Cannot get activation or deactivation status as the CA set with caSetId 10 is not found.","contextInfo":{"caSetId":"10"}}'
        mock_response = create_mock_response(404, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set_version_activation(
                models.GetCASetVersionActivationRequest(
                    ca_set_id="10", version=1, activation_id=84572))
        assert exc.value.is_equivalent(errors.ErrGetCASetNotFound)

    def test_404_version_not_found(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-version-not-found","title":"CA set version not found","status":404,"detail":"Cannot get activation or deactivation status as the version 12 is not found in the CA set under caSetName test1.","contextInfo":{"caSetName":"test1","caSetId":"2","version":12}}'
        mock_response = create_mock_response(404, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set_version_activation(
                models.GetCASetVersionActivationRequest(
                    ca_set_id="2", version=12, activation_id=84572))
        assert exc.value.is_equivalent(errors.ErrGetCASetVersionNotFound)

    def test_404_activation_not_found(self, mock_session):
        response_body = '{"contextInfo":{"activationId":2,"caSetId":"2","caSetName":"caSetName-1","version":1},"detail":"Cannot get activation or deactivation status as the activation or deactivation request with activationId 2 is not found in CA set version with version 1 under CA set with caSetId 2.","status":404,"title":"Activation or Deactivation Request is not found.","type":"/mtls-edge-truststore/error-types/activation-or-deactivation-request-not-found"}'
        mock_response = create_mock_response(404, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set_version_activation(
                models.GetCASetVersionActivationRequest(
                    ca_set_id="2", version=1, activation_id=2))
        assert exc.value.is_equivalent(errors.ErrGetCASetActivationNotFound)

    def test_500_internal_server_error(self, mock_session):
        response_body = '{"type":"internal-server-error","title":"Internal Server Error","detail":"Error processing request","instance":"TestInstances","status":500}'
        mock_response = create_mock_response(500, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set_version_activation(
                models.GetCASetVersionActivationRequest(
                    ca_set_id="199", version=1, activation_id=84572))
        assert exc.value.status == 500


# ---------------------------------------------------------------------------
# TestListCASetVersionActivations — from ca_set_activation_test.go
# ---------------------------------------------------------------------------

class TestListCASetVersionActivations:
    """Tests for list_ca_set_version_activations — mirrors Go TestListCASetVersionActivations."""

    def test_200_ok(self, mock_session):
        response_body = '{"activations":[{"activationId":84571,"activationLink":"/mtls-edge-truststore/v2/ca-sets/1000/versions/2/activations/84571","caSetId":"1000","caSetName":"test1","caSetLink":"/mtls-edge-truststore/v2/ca-sets/1000","percentComplete":100,"validation":null,"version":2,"versionLink":"/mtls-edge-truststore/v2/ca-sets/1000/versions/3","network":"STAGING","activationType":"DEACTIVATE","activationStatus":"COMPLETE","createdDate":"2023-01-11T11:00:00.385674Z","createdBy":"someone","failureReason":null,"modifiedDate":"2023-01-11T12:00:00.358292Z","modifiedBy":"someone"}]}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.list_ca_set_version_activations(
            models.ListCASetVersionActivationsRequest(
                ca_set_id="1000", version=2))
        assert len(result.activations) == 1
        assert result.activations[0].activation_id == 84571
        assert result.activations[0].activation_status == "COMPLETE"
        assert result.activations[0].activation_type == "DEACTIVATE"
        assert result.activations[0].percent_complete == 100
        assert result.activations[0].ca_set_name == "test1"
        assert result.activations[0].modified_by == "someone"

    def test_404_ca_set_not_found(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-not-found","title":"CA set not found.","status":404,"detail":"Cannot get CA set activations as the CA set with caSetId 1000 is not found.","contextInfo":{"caSetId":"1000"}}'
        mock_response = create_mock_response(404, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.list_ca_set_version_activations(
                models.ListCASetVersionActivationsRequest(
                    ca_set_id="1000", version=2))
        assert exc.value.is_equivalent(errors.ErrGetCASetNotFound)

    def test_404_version_not_found(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-version-not-found","title":"CA set version not found","status":404,"detail":"Cannot get CA set activations as the CA set version with version 2 is not found in the CA set under caSetName foo.","contextInfo":{"caSetName":"foo","caSetId":"1000","version":2}}'
        mock_response = create_mock_response(404, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.list_ca_set_version_activations(
                models.ListCASetVersionActivationsRequest(
                    ca_set_id="1000", version=2))
        assert exc.value.is_equivalent(errors.ErrGetCASetVersionNotFound)

    def test_missing_required_params_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.list_ca_set_version_activations(
                models.ListCASetVersionActivationsRequest())
        assert errors.ErrListCASetVersionActivations in exc.value.title
        assert "CASetID: cannot be blank" in exc.value.detail

    def test_500_internal_server_error(self, mock_session):
        response_body = '{"type":"internal_error","title":"Internal Server Error","detail":"Error processing request","status":500}'
        mock_response = create_mock_response(500, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.list_ca_set_version_activations(
                models.ListCASetVersionActivationsRequest(
                    ca_set_id="199", version=1))
        assert exc.value.status == 500


# ---------------------------------------------------------------------------
# TestListCASetActivations — from ca_set_activation_test.go
# ---------------------------------------------------------------------------

class TestListCASetActivations:
    """Tests for list_ca_set_activations — mirrors Go TestListCASetActivations."""

    def test_200_ok(self, mock_session):
        response_body = '{"activations":[{"activationId":"1","caSetId":"199","version":1,"network":"PRODUCTION","status":"ACTIVE","createdDate":"2025-04-01T15:33:48.464941Z","createdBy":"tester","completedDate":"2025-04-01T15:43:48.464941Z","validation":{"warnings":[]}},{"activationId":"2","caSetId":"199","version":1,"network":"STAGING","status":"ACTIVE","createdDate":"2025-04-01T15:33:48.464941Z","createdBy":"tester","completedDate":"2025-04-01T15:43:48.464941Z","validation":{"warnings":[]}}]}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.list_ca_set_activations(
            models.ListCASetActivationsRequest(ca_set_id="199"))
        assert len(result.activations) == 2
        assert result.activations[0].activation_id == "1"
        assert result.activations[0].network == "PRODUCTION"
        assert result.activations[1].activation_id == "2"
        assert result.activations[1].network == "STAGING"

    def test_404_ca_set_not_found(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-not-found","title":"CA set is not found.","status":404,"detail":"CA set with caSetId 199 is not found."}'
        mock_response = create_mock_response(404, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.list_ca_set_activations(
                models.ListCASetActivationsRequest(ca_set_id="199"))
        assert exc.value.is_equivalent(errors.ErrGetCASetNotFound)

    def test_missing_required_params_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.list_ca_set_activations(
                models.ListCASetActivationsRequest())
        assert errors.ErrListCASetActivations in exc.value.title
        assert "CASetID: cannot be blank" in exc.value.detail

    def test_500_internal_server_error(self, mock_session):
        response_body = '{"type":"internal_error","title":"Internal Server Error","detail":"Error processing request","status":500}'
        mock_response = create_mock_response(500, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.list_ca_set_activations(
                models.ListCASetActivationsRequest(ca_set_id="199"))
        assert exc.value.status == 500


# ---------------------------------------------------------------------------
# TestCreateCASetVersion — from ca_set_versions_test.go
# ---------------------------------------------------------------------------

class TestCreateCASetVersion:
    """Tests for create_ca_set_version — mirrors Go TestCreateCASetVersion."""

    def test_201_successful_creation(self, mock_session):
        response_body = '{"caSetId":"123","version":1,"caSetName":"Test CA Set","versionLink":"/mtls-edge-truststore/v2/ca-sets/123/versions/1","description":"Test CA Set Version","allowInsecureSha1":false,"stagingStatus":"PENDING","productionStatus":"PENDING","createdDate":"2025-04-10T00:00:00.739971Z","createdBy":"tester","modifiedDate":"2025-04-10T00:00:00.347834Z","modifiedBy":"tester","certificates":[{"subject":"Test Subject","issuer":"Test Issuer","endDate":"2025-12-31T00:00:00Z","startDate":"2025-01-01T00:00:00Z","fingerprint":"abc123","certificatePem":"-----BEGIN CERTIFICATE-----\\n...\\n-----END CERTIFICATE-----","serialNumber":"123456789","signatureAlgorithm":"SHA256WithRSA","createdDate":"2025-04-10T00:00:00.489392Z","createdBy":"tester"}],"validation":{"warnings":[]}}'
        mock_response = create_mock_response(201, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.create_ca_set_version(models.CreateCASetVersionRequest(
            ca_set_id="123",
            body=models.CreateCASetVersionRequestBody(
                allow_insecure_sha1=False,
                description="Test CA Set Version",
                certificates=[
                    models.CertificateRequest(
                        certificate_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"),
                ],
            ),
        ))
        assert result.ca_set_id == "123"
        assert result.version == 1
        assert result.ca_set_name == "Test CA Set"
        assert result.version_link == "/mtls-edge-truststore/v2/ca-sets/123/versions/1"
        assert result.description == "Test CA Set Version"
        assert result.allow_insecure_sha1 is False
        assert result.staging_status == "PENDING"
        assert result.production_status == "PENDING"
        assert len(result.certificates) == 1
        assert result.certificates[0].subject == "Test Subject"
        assert result.certificates[0].fingerprint == "abc123"
        assert not result.validation.warnings

    def test_201_without_description(self, mock_session):
        response_body = '{"caSetId":"123","version":1,"caSetName":"Test CA Set","versionLink":"/mtls-edge-truststore/v2/ca-sets/123/versions/1","description":null,"allowInsecureSha1":false,"stagingStatus":"PENDING","productionStatus":"PENDING","createdDate":"2025-04-10T00:00:00.739971Z","createdBy":"tester","modifiedDate":"2025-04-10T00:00:00.347834Z","modifiedBy":"tester","certificates":[{"subject":"Test Subject","issuer":"Test Issuer","endDate":"2025-12-31T00:00:00Z","startDate":"2025-01-01T00:00:00Z","fingerprint":"abc123","certificatePem":"-----BEGIN CERTIFICATE-----\\n...\\n-----END CERTIFICATE-----","serialNumber":"123456789","signatureAlgorithm":"SHA256WithRSA","createdDate":"2025-04-10T00:00:00.489392Z","createdBy":"tester"}],"validation":{"warnings":[]}}'
        mock_response = create_mock_response(201, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.create_ca_set_version(models.CreateCASetVersionRequest(
            ca_set_id="123",
            body=models.CreateCASetVersionRequestBody(
                allow_insecure_sha1=False,
                description=None,
                certificates=[
                    models.CertificateRequest(
                        certificate_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"),
                ],
            ),
        ))
        assert result.description is None
        assert result.ca_set_id == "123"

    def test_201_without_version_description(self, mock_session):
        response_body = '{"caSetId":"123","version":1,"caSetName":"Test CA Set","versionLink":"/mtls-edge-truststore/v2/ca-sets/123/versions/1","description":null,"allowInsecureSha1":false,"stagingStatus":"PENDING","productionStatus":"PENDING","createdDate":"2025-04-10T00:00:00.739971Z","createdBy":"tester","modifiedDate":"2025-04-10T00:00:00.347834Z","modifiedBy":"tester","certificates":[{"subject":"Test Subject","issuer":"Test Issuer","endDate":"2025-12-31T00:00:00Z","startDate":"2025-01-01T00:00:00Z","fingerprint":"abc123","certificatePem":"-----BEGIN CERTIFICATE-----\\n...\\n-----END CERTIFICATE-----","serialNumber":"123456789","signatureAlgorithm":"SHA256WithRSA","createdDate":"2025-04-10T00:00:00.489392Z","createdBy":"tester"}],"validation":{"warnings":[]}}'
        mock_response = create_mock_response(201, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.create_ca_set_version(models.CreateCASetVersionRequest(
            ca_set_id="123",
            body=models.CreateCASetVersionRequestBody(
                allow_insecure_sha1=False,
                certificates=[
                    models.CertificateRequest(
                        certificate_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"),
                ],
            ),
        ))
        assert result.description is None

    def test_201_with_duplicate_cert_warning(self, mock_session):
        response_body = '{"caSetId":"123","version":1,"caSetName":"Test CA Set","versionLink":"/mtls-edge-truststore/v2/ca-sets/123/versions/1","description":"Test CA Set Version","allowInsecureSha1":false,"stagingStatus":"PENDING","productionStatus":"PENDING","createdDate":"2025-04-10T00:00:00.739971Z","createdBy":"tester","modifiedDate":"2025-04-10T00:00:00.347834Z","modifiedBy":"tester","certificates":[{"subject":"Test Subject","issuer":"Test Issuer","endDate":"2025-12-31T00:00:00Z","startDate":"2025-01-01T00:00:00Z","fingerprint":"abc123","certificatePem":"-----BEGIN CERTIFICATE-----\\n...\\n-----END CERTIFICATE-----","serialNumber":"123456789","signatureAlgorithm":"SHA256WithRSA","createdDate":"2025-04-10T00:00:00.489392Z","createdBy":"tester"}],"validation":{"warnings":[{"contextInfo":{"description":null,"fingerprint":"abc123"},"detail":"The certificate with the fingerprint abc123 has been submitted more than once. Duplicate certificates are not allowed.","pointer":"/certificates/1","title":"Duplicate certificate has been submitted in the certificates.","type":"/mtls-edge-truststore/error-types/duplicate-certificate"}]}}'
        mock_response = create_mock_response(201, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.create_ca_set_version(models.CreateCASetVersionRequest(
            ca_set_id="123",
            body=models.CreateCASetVersionRequestBody(
                allow_insecure_sha1=False,
                description="Test CA Set Version",
                certificates=[
                    models.CertificateRequest(certificate_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"),
                    models.CertificateRequest(certificate_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"),
                ],
            ),
        ))
        assert len(result.validation.warnings) == 1
        assert result.validation.warnings[0].type == "/mtls-edge-truststore/error-types/duplicate-certificate"

    def test_validation_error_description_too_long(self, mock_session):
        client = Client(mock_session)
        long_desc = "Test CA Set Version is a critical step in validating and ensuring the correct version of the Certificate Authority (CA) configuration is applied. It involves thorough checks, validation steps, and the verification of certificates to confirm functionality and compliance."
        with pytest.raises(errors.Error) as exc:
            client.create_ca_set_version(models.CreateCASetVersionRequest(
                ca_set_id="123",
                body=models.CreateCASetVersionRequestBody(
                    allow_insecure_sha1=False, description=long_desc,
                    certificates=[models.CertificateRequest(certificate_pem="cert")],
                ),
            ))
        assert errors.ErrCreateCASetVersion in exc.value.title
        assert "Description: the length must be between 1 and 255" in exc.value.detail

    def test_validation_error_missing_ca_set_id(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.create_ca_set_version(models.CreateCASetVersionRequest(
                body=models.CreateCASetVersionRequestBody(
                    allow_insecure_sha1=False, description="Missing CASetID",
                    certificates=[models.CertificateRequest(certificate_pem="cert")],
                ),
            ))
        assert errors.ErrCreateCASetVersion in exc.value.title
        assert "CASetID: cannot be blank" in exc.value.detail

    def test_validation_error_missing_certificates(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.create_ca_set_version(models.CreateCASetVersionRequest(
                ca_set_id="1",
                body=models.CreateCASetVersionRequestBody(
                    allow_insecure_sha1=False, description="Missing CASetID",
                ),
            ))
        assert errors.ErrCreateCASetVersion in exc.value.title
        assert "Certificates: cannot be blank" in exc.value.detail

    def test_validation_error_missing_certificate_pem(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.create_ca_set_version(models.CreateCASetVersionRequest(
                ca_set_id="1",
                body=models.CreateCASetVersionRequestBody(
                    allow_insecure_sha1=False, description="Missing CASetID",
                    certificates=[models.CertificateRequest()],
                ),
            ))
        assert errors.ErrCreateCASetVersion in exc.value.title
        assert "CertificatePEM: cannot be blank" in exc.value.detail

    def test_validation_error_cert_description_too_long(self, mock_session):
        client = Client(mock_session)
        long_desc = "Test CA Set Version is a critical step in validating and ensuring the correct version of the Certificate Authority (CA) configuration is applied. It involves thorough checks, validation steps, and the verification of certificates to confirm functionality and compliance."
        with pytest.raises(errors.Error) as exc:
            client.create_ca_set_version(models.CreateCASetVersionRequest(
                ca_set_id="123",
                body=models.CreateCASetVersionRequestBody(
                    allow_insecure_sha1=False,
                    certificates=[models.CertificateRequest(certificate_pem="cert", description=long_desc)],
                ),
            ))
        assert errors.ErrCreateCASetVersion in exc.value.title
        assert "Description: the length must be between 1 and 255" in exc.value.detail

    def test_error_ca_set_not_found(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-not-found","title":"CA set is not found.","status":404,"detail":"Cannot create a CA set version as the CA set with caSetId 123 is not found.","contextInfo":{"caSetId":"123"}}'
        mock_response = create_mock_response(404, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.create_ca_set_version(models.CreateCASetVersionRequest(
                ca_set_id="123",
                body=models.CreateCASetVersionRequestBody(
                    allow_insecure_sha1=False, description="Test CA Set Version",
                    certificates=[models.CertificateRequest(certificate_pem="cert")],
                ),
            ))
        assert exc.value.is_equivalent(errors.ErrGetCASetNotFound)

    def test_error_version_limit_reached(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-version-limit-reached","title":"Maximum allowed CA set version\u0027s limit has been reached.","status":422,"detail":"Cannot create CA set version as you have already reached or exceeded the maximum allowed CA set version limit of 10 for the CA set with caSetId 1.","contextInfo":{"caSetName":"test","caSetId":"1","maxVersionsPerCaSet":10}}'
        mock_response = create_mock_response(422, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.create_ca_set_version(models.CreateCASetVersionRequest(
                ca_set_id="1",
                body=models.CreateCASetVersionRequestBody(
                    allow_insecure_sha1=False, description="Test CA Set Version",
                    certificates=[models.CertificateRequest(certificate_pem="cert")],
                ),
            ))
        assert exc.value.is_equivalent(errors.ErrCASetVersionLimitReached)

    def test_error_certificate_limit_reached(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/certificate-limit-reached","title":"Submitted certificates exceed the maximum allowed certificates limit.","status":422,"detail":"The maximum number of certificates allowed per CA set version is 300. Number of submitted certificates is 302.","contextInfo":{"caSetName":"test","caSetId":"1","maxCertificatesPerVersion":300,"submittedCertificatesCount":302}}'
        mock_response = create_mock_response(422, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.create_ca_set_version(models.CreateCASetVersionRequest(
                ca_set_id="1",
                body=models.CreateCASetVersionRequestBody(
                    allow_insecure_sha1=False, description="Test CA Set Version",
                    certificates=[models.CertificateRequest(certificate_pem="cert")],
                ),
            ))
        assert exc.value.is_equivalent(errors.ErrCertificateLimitReached)

    def test_error_certificate_validation_failed(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/certificate-validation-failure-create","title":"Cannot create the ca set version as the certificate(s) has failed validation.","status":400,"contextInfo":{"caSetId":"131803","caSetName":"sup-m2-bugjam6"},"errors":[{"detail":"SHA1WITHRSA algo error","pointer":"/certificates/0","contextInfo":{"description":null,"fingerPrint":"abc","signatureAlgorithm":"SHA1WITHRSA","subject":"test"}}]}'
        mock_response = create_mock_response(400, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.create_ca_set_version(models.CreateCASetVersionRequest(
                ca_set_id="131803",
                body=models.CreateCASetVersionRequestBody(
                    allow_insecure_sha1=False, description="Test CA Set Version",
                    certificates=[models.CertificateRequest(certificate_pem="cert")],
                ),
            ))
        assert exc.value.is_equivalent(errors.ErrCertificateValidationFailedForCreate)

    def test_error_deletion_in_progress(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/delete-ca-set-request-in-progress","title":"DELETE request is in progress for the CA set on the network.","status":409,"detail":"Cannot create CA set version as the CA set is being deleted on one or more networks.","contextInfo":{"caSetId":"1","caSetName":"caSetName-73f58a4e","deletionLink":"/mtls-edge-truststore/v2/ca-sets/1/status/delete","productionStatus":"IN_PROGRESS","stagingStatus":"IN_PROGRESS","version":1}}'
        mock_response = create_mock_response(409, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.create_ca_set_version(models.CreateCASetVersionRequest(
                ca_set_id="1",
                body=models.CreateCASetVersionRequestBody(
                    allow_insecure_sha1=False, description="Test CA Set Version",
                    certificates=[models.CertificateRequest(certificate_pem="cert")],
                ),
            ))
        assert exc.value.is_equivalent(errors.ErrCASetDeleteRequestInProgress)

    def test_error_duplicate_version(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/duplicate-ca-set-version","title":"A version with same certificates exists in the CA set.","status":422,"detail":"A version with same certificates exists in the CA set.","contextInfo":{"caSetName":"t\u00e9st","caSetId":"1","versionLink":"/tcm-api/ca-sets/1/versions/1"}}'
        mock_response = create_mock_response(422, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.create_ca_set_version(models.CreateCASetVersionRequest(
                ca_set_id="1",
                body=models.CreateCASetVersionRequestBody(
                    allow_insecure_sha1=False, description="Test CA Set Version",
                    certificates=[models.CertificateRequest(certificate_pem="cert")],
                ),
            ))
        assert exc.value.is_equivalent(errors.ErrCASetVersionIsDuplicate)

    def test_internal_server_error(self, mock_session):
        response_body = '{"type":"internal_error","title":"Internal Server Error","detail":"Error processing request","status":500}'
        mock_response = create_mock_response(500, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.create_ca_set_version(models.CreateCASetVersionRequest(
                ca_set_id="123",
                body=models.CreateCASetVersionRequestBody(
                    allow_insecure_sha1=False, description="Test CA Set Version",
                    certificates=[models.CertificateRequest(certificate_pem="cert")],
                ),
            ))
        assert exc.value.is_equivalent(errors.Error(type="internal_error", title="Internal Server Error", detail="Error processing request", status=500))


# ---------------------------------------------------------------------------
# TestCloneCASetVersion — from ca_set_versions_test.go
# ---------------------------------------------------------------------------

class TestCloneCASetVersion:
    """Tests for clone_ca_set_version — mirrors Go TestCloneCASetVersion."""

    def test_201_created(self, mock_session):
        response_body = '{"caSetId":"123","version":2,"caSetName":"Test CA Set","versionLink":"/mtls-edge-truststore/v2/ca-sets/123/versions/2","description":"Cloned version","allowInsecureSha1":false,"stagingStatus":"PENDING","productionStatus":"PENDING","createdDate":"2025-04-10T00:00:00.739971Z","createdBy":"tester","modifiedDate":"2025-04-10T00:00:00.347834Z","modifiedBy":"tester","certificates":[{"subject":"Test Subject","issuer":"Test Issuer","endDate":"2025-12-31T00:00:00Z","startDate":"2025-01-01T00:00:00Z","fingerprint":"abc123","certificatePem":"-----BEGIN CERTIFICATE-----\\n...\\n-----END CERTIFICATE-----","serialNumber":"123456789","signatureAlgorithm":"SHA256WithRSA","createdDate":"2025-04-10T00:00:00.489392Z","createdBy":"tester"}],"validation":{"warnings":[]}}'
        mock_response = create_mock_response(201, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.clone_ca_set_version(models.CloneCASetVersionRequest(
            ca_set_id="123",
            version=1,
        ))
        assert result.ca_set_id == "123"
        assert result.version == 2
        assert result.version_link == "/mtls-edge-truststore/v2/ca-sets/123/versions/2"

    def test_201_created_with_warnings(self, mock_session):
        response_body = '{"caSetId":"123","version":2,"caSetName":"Test CA Set","versionLink":"/mtls-edge-truststore/v2/ca-sets/123/versions/2","description":"Cloned version","allowInsecureSha1":true,"stagingStatus":"PENDING","productionStatus":"PENDING","createdDate":"2025-04-10T00:00:00.739971Z","createdBy":"tester","modifiedDate":"2025-04-10T00:00:00.347834Z","modifiedBy":"tester","certificates":[{"subject":"Test Subject","issuer":"Test Issuer","endDate":"2025-12-31T00:00:00Z","startDate":"2025-01-01T00:00:00Z","fingerprint":"abc123","certificatePem":"-----BEGIN CERTIFICATE-----\\n...\\n-----END CERTIFICATE-----","serialNumber":"123456789","signatureAlgorithm":"SHA1WITHRSA","createdDate":"2025-04-10T00:00:00.489392Z","createdBy":"tester"}],"validation":{"warnings":[{"contextInfo":{"description":null,"fingerprint":"abc123"},"detail":"Certificate with fingerprint abc123 uses an insecure signature algorithm (SHA1WITHRSA).","pointer":"/certificates/0","title":"Insecure signature algorithm","type":"/mtls-edge-truststore/error-types/insecure-signature-algorithm"}]}}'
        mock_response = create_mock_response(201, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.clone_ca_set_version(models.CloneCASetVersionRequest(
            ca_set_id="123",
            version=1,
        ))
        assert len(result.validation.warnings) == 1
        assert result.allow_insecure_sha1 is True

    def test_missing_required_params_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.clone_ca_set_version(models.CloneCASetVersionRequest())
        assert errors.ErrCloneCASetVersion in exc.value.title
        assert "CASetID: cannot be blank" in exc.value.detail

    def test_404_ca_set_not_found(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-not-found","title":"CA set is not found.","status":404,"detail":"CA set with caSetId 123 is not found."}'
        mock_response = create_mock_response(404, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.clone_ca_set_version(models.CloneCASetVersionRequest(
                ca_set_id="123", version=1))
        assert exc.value.is_equivalent(errors.ErrGetCASetNotFound)

    def test_404_version_not_found(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-version-not-found","title":"CA set version is not found.","status":404,"detail":"CA set version is not found."}'
        mock_response = create_mock_response(404, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.clone_ca_set_version(models.CloneCASetVersionRequest(
                ca_set_id="123", version=99))
        assert exc.value.is_equivalent(errors.ErrGetCASetVersionNotFound)

    def test_409_deletion_in_progress(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/delete-ca-set-request-in-progress","title":"DELETE request is in progress for the CA set on the network.","status":409,"detail":"Cannot clone CA set version."}'
        mock_response = create_mock_response(409, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.clone_ca_set_version(models.CloneCASetVersionRequest(
                ca_set_id="123", version=1))
        assert exc.value.is_equivalent(errors.ErrCASetDeleteRequestInProgress)

    def test_422_version_limit_reached(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-version-limit-reached","title":"Maximum allowed CA set version\u0027s limit has been reached.","status":422,"detail":"Cannot clone CA set version."}'
        mock_response = create_mock_response(422, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.clone_ca_set_version(models.CloneCASetVersionRequest(
                ca_set_id="123", version=1))
        assert exc.value.is_equivalent(errors.ErrCASetVersionLimitReached)

    def test_500_internal_server_error(self, mock_session):
        response_body = '{"type":"internal_error","title":"Internal Server Error","detail":"Error processing request","status":500}'
        mock_response = create_mock_response(500, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.clone_ca_set_version(models.CloneCASetVersionRequest(
                ca_set_id="123", version=1))
        assert exc.value.status == 500


# ---------------------------------------------------------------------------
# TestGetCASetVersion — from ca_set_versions_test.go
# ---------------------------------------------------------------------------

class TestGetCASetVersion:
    """Tests for get_ca_set_version — mirrors Go TestGetCASetVersion."""

    def test_200_ok(self, mock_session):
        response_body = '{"caSetId":"123","version":1,"caSetName":"Test CA Set","versionLink":"/mtls-edge-truststore/v2/ca-sets/123/versions/1","description":"Test version","allowInsecureSha1":false,"stagingStatus":"ACTIVE","productionStatus":"PENDING","createdDate":"2025-04-10T00:00:00.739971Z","createdBy":"tester","modifiedDate":"2025-04-10T00:00:00.347834Z","modifiedBy":"tester","certificates":[{"subject":"Test Subject","issuer":"Test Issuer","endDate":"2025-12-31T00:00:00Z","startDate":"2025-01-01T00:00:00Z","fingerprint":"abc123","certificatePem":"-----BEGIN CERTIFICATE-----\\n...\\n-----END CERTIFICATE-----","serialNumber":"123456789","signatureAlgorithm":"SHA256WithRSA","createdDate":"2025-04-10T00:00:00.489392Z","createdBy":"tester"}],"validation":{"warnings":[]}}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.get_ca_set_version(models.GetCASetVersionRequest(
            ca_set_id="123", version=1))
        assert result.ca_set_id == "123"
        assert result.version == 1
        assert result.staging_status == "ACTIVE"
        assert len(result.certificates) == 1

    def test_missing_required_params_validation_error(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set_version(models.GetCASetVersionRequest())
        assert errors.ErrGetCASetVersion in exc.value.title
        assert "CASetID: cannot be blank" in exc.value.detail

    def test_404_ca_set_not_found(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-not-found","title":"CA set is not found.","status":404,"detail":"CA set with caSetId 123 is not found."}'
        mock_response = create_mock_response(404, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set_version(models.GetCASetVersionRequest(
                ca_set_id="123", version=1))
        assert exc.value.is_equivalent(errors.ErrGetCASetNotFound)

    def test_404_version_not_found(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-version-not-found","title":"CA set version is not found.","status":404,"detail":"CA set version is not found."}'
        mock_response = create_mock_response(404, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set_version(models.GetCASetVersionRequest(
                ca_set_id="123", version=99))
        assert exc.value.is_equivalent(errors.ErrGetCASetVersionNotFound)


# ---------------------------------------------------------------------------
# TestUpdateCASetVersion — from ca_set_versions_test.go
# ---------------------------------------------------------------------------

class TestUpdateCASetVersion:
    """Tests for update_ca_set_version — mirrors Go TestUpdateCASetVersion."""

    def test_200_successful_update(self, mock_session):
        response_body = '{"caSetId":"123","version":1,"caSetName":"Test CA Set","versionLink":"/mtls-edge-truststore/v2/ca-sets/123/versions/1","description":"Test CA Set Version","allowInsecureSha1":false,"stagingStatus":"PENDING","productionStatus":"PENDING","createdDate":"2025-04-10T00:00:00.986647Z","createdBy":"tester","modifiedDate":"2025-04-10T00:00:00.029349Z","modifiedBy":"tester","certificates":[{"subject":"Test Subject","issuer":"Test Issuer","endDate":"2025-12-31T00:00:00Z","startDate":"2025-01-01T00:00:00Z","fingerprint":"abc123","certificatePem":"-----BEGIN CERTIFICATE-----\\n...\\n-----END CERTIFICATE-----","serialNumber":"123456789","signatureAlgorithm":"SHA256WithRSA","createdDate":"2025-04-10T00:00:00.959343Z","createdBy":"tester"}],"validation":{"warnings":[]}}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.update_ca_set_version(models.UpdateCASetVersionRequest(
            ca_set_id="123",
            version=1,
            body=models.UpdateCASetVersionRequestBody(
                allow_insecure_sha1=False,
                description="Test CA Set Version",
                certificates=[
                    models.CertificateRequest(
                        certificate_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
                    ),
                ],
            ),
        ))
        assert result.ca_set_id == "123"
        assert result.version == 1
        assert result.description == "Test CA Set Version"
        assert result.allow_insecure_sha1 is False
        assert len(result.certificates) == 1
        assert len(result.validation.warnings) == 0
        expected_body = {"allowInsecureSha1": False, "certificates": [{"certificatePem": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"}], "description": "Test CA Set Version"}
        assert_request(mock_session, "PUT", "/mtls-edge-truststore/v2/ca-sets/123/versions/1", expected_body)

    def test_200_successful_update_missing_description(self, mock_session):
        response_body = '{"caSetId":"123","version":1,"caSetName":"Test CA Set","versionLink":"/mtls-edge-truststore/v2/ca-sets/123/versions/1","allowInsecureSha1":false,"stagingStatus":"PENDING","productionStatus":"PENDING","createdDate":"2025-04-10T00:00:00.986647Z","createdBy":"tester","modifiedDate":"2025-04-10T00:00:00.029349Z","modifiedBy":"tester","certificates":[{"subject":"Test Subject","issuer":"Test Issuer","endDate":"2025-12-31T00:00:00Z","startDate":"2025-01-01T00:00:00Z","fingerprint":"abc123","certificatePem":"-----BEGIN CERTIFICATE-----\\n...\\n-----END CERTIFICATE-----","serialNumber":"123456789","signatureAlgorithm":"SHA256WithRSA","createdDate":"2025-04-10T00:00:00.959343Z","createdBy":"tester"}],"validation":{"warnings":[]}}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.update_ca_set_version(models.UpdateCASetVersionRequest(
            ca_set_id="123",
            version=1,
            body=models.UpdateCASetVersionRequestBody(
                allow_insecure_sha1=False,
                certificates=[
                    models.CertificateRequest(
                        certificate_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
                    ),
                ],
            ),
        ))
        assert result.ca_set_id == "123"
        assert result.description is None
        expected_body = {"allowInsecureSha1": False, "certificates": [{"certificatePem": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"}]}
        assert_request(mock_session, "PUT", "/mtls-edge-truststore/v2/ca-sets/123/versions/1", expected_body)

    def test_200_with_duplicated_certificates_warning(self, mock_session):
        response_body = '{"caSetId":"123","version":1,"caSetName":"Test CA Set","versionLink":"/mtls-edge-truststore/v2/ca-sets/123/versions/1","description":"Test CA Set Version","allowInsecureSha1":false,"stagingStatus":"PENDING","productionStatus":"PENDING","createdDate":"2025-04-10T00:00:00.986647Z","createdBy":"tester","modifiedDate":"2025-04-10T00:00:00.029349Z","modifiedBy":"tester","certificates":[{"subject":"Test Subject","issuer":"Test Issuer","endDate":"2025-12-31T00:00:00Z","startDate":"2025-01-01T00:00:00Z","fingerprint":"abc123","certificatePem":"-----BEGIN CERTIFICATE-----\\n...\\n-----END CERTIFICATE-----","serialNumber":"123456789","signatureAlgorithm":"SHA256WithRSA","createdDate":"2025-04-10T00:00:00.959343Z","createdBy":"tester"}],"validation":{"warnings":[{"contextInfo":{"description":null,"fingerprint":"abc123"},"detail":"The certificate with the fingerprint abc123 has been submitted more than once. Duplicate certificates are not allowed.","pointer":"/certificates/1","title":"Duplicate certificate has been submitted in the certificates.","type":"/mtls-edge-truststore/error-types/duplicate-certificate"}]}}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.update_ca_set_version(models.UpdateCASetVersionRequest(
            ca_set_id="123",
            version=1,
            body=models.UpdateCASetVersionRequestBody(
                allow_insecure_sha1=False,
                description="Test CA Set Version",
                certificates=[
                    models.CertificateRequest(certificate_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"),
                    models.CertificateRequest(certificate_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"),
                ],
            ),
        ))
        assert len(result.validation.warnings) == 1
        assert result.validation.warnings[0].type == "/mtls-edge-truststore/error-types/duplicate-certificate"

    def test_validation_error_description_too_long(self, mock_session):
        client = Client(mock_session)
        long_desc = "Test CA Set Version is a critical step in validating and ensuring the correct version of the Certificate Authority (CA) configuration is applied. It involves thorough checks, validation steps, and the verification of certificates to confirm functionality and compliance."
        with pytest.raises(errors.Error) as exc:
            client.update_ca_set_version(models.UpdateCASetVersionRequest(
                ca_set_id="123",
                version=1,
                body=models.UpdateCASetVersionRequestBody(
                    allow_insecure_sha1=False,
                    description=long_desc,
                    certificates=[models.CertificateRequest(certificate_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----")],
                ),
            ))
        assert errors.ErrUpdateCASetVersion in exc.value.title
        assert "Description: the length must be between 1 and 255" in exc.value.detail

    def test_validation_error_missing_ca_set_id(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.update_ca_set_version(models.UpdateCASetVersionRequest(
                version=1,
                body=models.UpdateCASetVersionRequestBody(
                    allow_insecure_sha1=False,
                    description="Missing CASetID",
                    certificates=[models.CertificateRequest(certificate_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----")],
                ),
            ))
        assert errors.ErrUpdateCASetVersion in exc.value.title
        assert "CASetID: cannot be blank" in exc.value.detail

    def test_validation_error_missing_version(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.update_ca_set_version(models.UpdateCASetVersionRequest(
                ca_set_id="1",
                body=models.UpdateCASetVersionRequestBody(
                    allow_insecure_sha1=False,
                    description="Missing CASetID",
                    certificates=[models.CertificateRequest(certificate_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----")],
                ),
            ))
        assert errors.ErrUpdateCASetVersion in exc.value.title
        assert "Version: cannot be blank" in exc.value.detail

    def test_validation_error_missing_certificates(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.update_ca_set_version(models.UpdateCASetVersionRequest(
                ca_set_id="1",
                version=1,
                body=models.UpdateCASetVersionRequestBody(
                    allow_insecure_sha1=False,
                    description="Missing Version",
                ),
            ))
        assert errors.ErrUpdateCASetVersion in exc.value.title
        assert "Certificates: cannot be blank" in exc.value.detail

    def test_validation_error_missing_certificate_pem(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.update_ca_set_version(models.UpdateCASetVersionRequest(
                ca_set_id="1",
                version=1,
                body=models.UpdateCASetVersionRequestBody(
                    allow_insecure_sha1=False,
                    description="Missing CASetID",
                    certificates=[models.CertificateRequest()],
                ),
            ))
        assert errors.ErrUpdateCASetVersion in exc.value.title
        assert "Certificates[0]" in exc.value.detail
        assert "CertificatePEM: cannot be blank" in exc.value.detail

    def test_404_ca_set_not_found(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-not-found","title":"CA set is not found.","status":404,"detail":"Cannot create a CA set version as the CA set with caSetId 123 is not found.","contextInfo":{"caSetId":"123"}}'
        mock_response = create_mock_response(404, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.update_ca_set_version(models.UpdateCASetVersionRequest(
                ca_set_id="123", version=1,
                body=models.UpdateCASetVersionRequestBody(
                    allow_insecure_sha1=False,
                    description="Test CA Set Version",
                    certificates=[models.CertificateRequest(certificate_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----")],
                ),
            ))
        assert exc.value.is_equivalent(errors.ErrGetCASetNotFound)

    def test_404_version_not_found(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-version-not-found","title":"CA set is not found.","status":404,"detail":"Cannot create a CA set version as the CA set with caSetId 123 is not found.","contextInfo":{"caSetName":"test1","caSetId":"2","version":12}}'
        mock_response = create_mock_response(404, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.update_ca_set_version(models.UpdateCASetVersionRequest(
                ca_set_id="123", version=12,
                body=models.UpdateCASetVersionRequestBody(
                    allow_insecure_sha1=False,
                    description="Test CA Set Version",
                    certificates=[models.CertificateRequest(certificate_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----")],
                ),
            ))
        assert exc.value.is_equivalent(errors.ErrGetCASetVersionNotFound)

    def test_409_deletion_in_progress(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/delete-ca-set-request-in-progress","title":"DELETE request is in progress for the CA set on the network.","status":409,"detail":"Cannot update CA set version as the CA set is being deleted on one or more networks.","contextInfo":{"caSetId":"1","caSetName":"caSetName-123","deletionLink":"/mtls-edge-truststore/v2/ca-sets/1/status/delete","productionStatus":"IN_PROGRESS","stagingStatus":"IN_PROGRESS","version":1}}'
        mock_response = create_mock_response(409, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.update_ca_set_version(models.UpdateCASetVersionRequest(
                ca_set_id="1", version=1,
                body=models.UpdateCASetVersionRequestBody(
                    allow_insecure_sha1=False,
                    description="Test CA Set Version",
                    certificates=[models.CertificateRequest(certificate_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----")],
                ),
            ))
        assert exc.value.is_equivalent(errors.ErrCASetDeleteRequestInProgress)

    def test_422_version_active_being_activated(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-version-is-active","title":"CA set version is currently active.","status":422,"detail":"Cannot update the CA set version with version 1 as it is active on production network.","contextInfo":{"caSetId":"1","caSetName":"t\u00e9st","version":1}}'
        mock_response = create_mock_response(422, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.update_ca_set_version(models.UpdateCASetVersionRequest(
                ca_set_id="1", version=1,
                body=models.UpdateCASetVersionRequestBody(
                    allow_insecure_sha1=False,
                    description="Test CA Set Version",
                    certificates=[models.CertificateRequest(certificate_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----")],
                ),
            ))
        assert exc.value.is_equivalent(errors.ErrCASetVersionIsActive)

    def test_422_version_active_production(self, mock_session):
        response_body = '{"contextInfo":{"caSetId":"1","caSetName":"t\u00e9st","version":1},"detail":"Cannot update the CA set version with version 1 as it is active on production network.","status":422,"title":"CA set version is currently active.","type":"/mtls-edge-truststore/error-types/ca-set-version-is-active"}'
        mock_response = create_mock_response(422, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.update_ca_set_version(models.UpdateCASetVersionRequest(
                ca_set_id="1", version=1,
                body=models.UpdateCASetVersionRequestBody(
                    allow_insecure_sha1=False,
                    description="Test CA Set Version",
                    certificates=[models.CertificateRequest(certificate_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----")],
                ),
            ))
        assert exc.value.is_equivalent(errors.ErrCASetVersionIsActive)

    def test_422_version_active_staging(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-version-is-active","title":"CA set version is currently active.","status":422,"detail":"Cannot update the CA set version with version 1 as it is  active on staging network/s.","contextInfo":{"caSetName":"t\u00e9st","caSetId":"1","version":1}}'
        mock_response = create_mock_response(422, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.update_ca_set_version(models.UpdateCASetVersionRequest(
                ca_set_id="1", version=1,
                body=models.UpdateCASetVersionRequestBody(
                    allow_insecure_sha1=False,
                    description="Test CA Set Version",
                    certificates=[models.CertificateRequest(certificate_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----")],
                ),
            ))
        assert exc.value.is_equivalent(errors.ErrCASetVersionIsActive)

    def test_422_version_was_previously_active(self, mock_session):
        response_body = '{"contextInfo":{"caSetId":"123","caSetName":"1.13_bc_testing-COPY","version":1},"detail":"Cannot update the CA set version with version 1 as it was previously active on one ore more networks.","status":422,"title":"CA set version was previously active.","type":"/mtls-edge-truststore/error-types/ca-set-version-was-previously-active"}'
        mock_response = create_mock_response(422, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.update_ca_set_version(models.UpdateCASetVersionRequest(
                ca_set_id="123", version=1,
                body=models.UpdateCASetVersionRequestBody(
                    allow_insecure_sha1=False,
                    description="Test CA Set Version",
                    certificates=[models.CertificateRequest(certificate_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----")],
                ),
            ))
        assert exc.value.is_equivalent(errors.ErrCASetVersionWasPreviouslyActive)

    def test_400_invalid_certificates(self, mock_session):
        response_body = '{"contextInfo":{"caSetId":"123","caSetName":"test ca set","version":1},"errors":[{"contextInfo":{"description":"new description","fingerPrint":"fingerebc8de3270598ec1fa62c92a20ef86d53bca415978b40733afaa8b09082","signatureAlgorithm":"SHA1WITHRSA","subject":"EMAILADDRESS=test@akamai.com, CN=test, OU=DELIVERY, O=AKAMAI, L=BLR, ST=KA, C=IN"},"detail":"The certificate with subject EMAILADDRESS=test@akamai.com, CN=test, OU=DELIVERY, O=AKAMAI, L=BLR, ST=KA, C=IN and fingerprint fingerebc8de3270598ec1fa62c92a20ef86d53bca415978b40733afaa8b09082 uses disallowed signature algorithm SHA1WITHRSA. Allow InsecureSha1 option is not set. This is not allowed.","pointer":"/certificates/0"}],"status":400,"title":"Cannot update the ca set version as the certificate(s) has failed validation.","type":"/mtls-edge-truststore/error-types/certificate-validation-failure-update"}'
        mock_response = create_mock_response(400, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.update_ca_set_version(models.UpdateCASetVersionRequest(
                ca_set_id="123", version=1,
                body=models.UpdateCASetVersionRequestBody(
                    allow_insecure_sha1=False,
                    description="Test CA Set Version",
                    certificates=[models.CertificateRequest(certificate_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----")],
                ),
            ))
        assert exc.value.is_equivalent(errors.ErrCertificateValidationFailedForUpdate)

    def test_422_certificate_limit_reached(self, mock_session):
        response_body = '{"contextInfo":{"caSetId":"123","caSetName":"sveerava-test-13456111","maxCertificatesPerVersion":1,"submittedCertificatesCount":2,"version":2},"detail":"The maximum number of certificates allowed per CA set version is 1. Number of submitted certificates is 2.","status":422,"title":"Submitted certificates exceed the maximum allowed certificates limit.","type":"/mtls-edge-truststore/error-types/certificate-limit-reached"}'
        mock_response = create_mock_response(422, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.update_ca_set_version(models.UpdateCASetVersionRequest(
                ca_set_id="123", version=2,
                body=models.UpdateCASetVersionRequestBody(
                    allow_insecure_sha1=False,
                    description="Test CA Set Version",
                    certificates=[models.CertificateRequest(certificate_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----")],
                ),
            ))
        assert exc.value.is_equivalent(errors.ErrCertificateLimitReached)

    def test_500_internal_server_error(self, mock_session):
        response_body = '{"type":"internal_error","title":"Internal Server Error","detail":"Error processing request","status":500}'
        mock_response = create_mock_response(500, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.update_ca_set_version(models.UpdateCASetVersionRequest(
                ca_set_id="123", version=1,
                body=models.UpdateCASetVersionRequestBody(
                    allow_insecure_sha1=False,
                    description="Test CA Set Version",
                    certificates=[models.CertificateRequest(certificate_pem="-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----")],
                ),
            ))
        assert exc.value.status == 500
        assert exc.value.title == "Internal Server Error"


# ---------------------------------------------------------------------------
# TestListCASetVersions — from ca_set_versions_test.go
# ---------------------------------------------------------------------------

class TestListCASetVersions:
    """Tests for list_ca_set_versions — mirrors Go TestListCASetVersions."""

    def test_200_no_query_params(self, mock_session):
        response_body = '{"versions":[{"version":1,"versionLink":"/mtls-edge-truststore/v2/ca-sets/1000/versions/1","caSetId":"1000","caSetName":"test1","description":"Optional description for this version.","allowInsecureSha1":false,"stagingStatus":"ACTIVE","productionStatus":"INACTIVE","createdDate":"2023-01-10T11:00:00.435643Z","createdBy":"jsmith","modifiedDate":"2023-01-10T12:00:00.925684Z","modifiedBy":"jsmith","certificates":[{"subject":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate.tcm-11-example.com","issuer":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=tcm-13-example.com","endDate":"2020-04-07T17:33:39Z","startDate":"2019-04-08T17:33:39Z","fingerprint":"1E:DD:AD:32:C3:54:3F:C3:6F:7F:94:51:8D:5E:F7:ED:7C:DB:5D:A5","certificatePem":"-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----","serialNumber":"11612024106234270900","signatureAlgorithm":"SHA256WITHRSA","createdDate":"2020-04-07T17:33:39.247917Z","createdBy":"jsmith2","description":"Optional description for the certificate"},{"subject":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate1.tcm-11-example.com","issuer":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate.tcm-11-example.com","endDate":"2020-04-07T17:43:58Z","startDate":"2019-04-08T17:43:58Z","fingerprint":"1F:DD:AD:32:C3:54:3F:C3:6F:7F:04:51:8D:5E:F7:ED:7C:DB:5D:A5","certificatePem":"-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----","serialNumber":"11612024106234270901","signatureAlgorithm":"SHA256WITHRSA","createdDate":"2020-04-07T17:33:39.883429Z","createdBy":"jsmith2","description":"Optional description for the certificate"}],"validation":null},{"caSetId":"1000","caSetName":"test1","version":2,"versionLink":"/mtls-edge-truststore/v2/ca-sets/1000/versions/2","description":null,"allowInsecureSha1":true,"stagingStatus":"ACTIVE","productionStatus":"INACTIVE","createdDate":"2023-01-10T11:00:00.876324Z","createdBy":"jsmith","modifiedDate":"2023-01-10T12:00:00.897323Z","modifiedBy":"jsmith","certificates":[{"subject":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate.tcm-11-example.com","issuer":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=tcm-13-example.com","endDate":"2020-04-07T17:33:39Z","startDate":"2019-04-08T17:33:39Z","fingerprint":"1E:DD:AD:32:C3:54:3F:C3:6F:7F:94:51:8D:5E:F7:ED:7C:DB:5D:A5","certificatePem":"-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----","serialNumber":"11612024106234270900","signatureAlgorithm":"SHA256WITHRSA","createdDate":"2020-04-07T17:33:39.247917Z","createdBy":"jsmith2","description":"Optional description for the certificate"},{"subject":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate1.tcm-11-example.com","issuer":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate.tcm-11-example.com","endDate":"2020-04-07T17:43:58Z","startDate":"2019-04-08T17:43:58Z","fingerprint":"1F:DD:AD:32:C3:54:3F:C3:6F:7F:04:51:8D:5E:F7:ED:7C:DB:5D:A6","certificatePem":"-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----","serialNumber":"11612024106234270901","signatureAlgorithm":"SHA256WITHRSA","createdDate":"2020-04-07T17:33:39.738219Z","createdBy":"jsmith2","description":"Optional description for the certificate"}],"validation":null}]}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.list_ca_set_versions(models.ListCASetVersionsRequest(
            ca_set_id="123",
        ))
        assert len(result.versions) == 2
        assert result.versions[0].version == 1
        assert result.versions[0].ca_set_id == "1000"
        assert result.versions[0].description == "Optional description for this version."
        assert result.versions[1].version == 2
        assert result.versions[1].description is None
        assert result.versions[1].allow_insecure_sha1 is True
        assert_request(mock_session, "GET", "/mtls-edge-truststore/v2/ca-sets/123/versions")

    def test_200_with_active_versions_and_include_certs(self, mock_session):
        response_body = '{"versions":[{"version":1,"versionLink":"/mtls-edge-truststore/v2/ca-sets/1000/versions/1","caSetId":"1000","caSetName":"test1","description":"Optional description for this version.","allowInsecureSha1":false,"stagingStatus":"ACTIVE","productionStatus":"ACTIVE","createdDate":"2023-01-10T11:00:00.633918Z","createdBy":"jsmith","modifiedDate":"2023-01-10T12:00:00.733190Z","modifiedBy":"jsmith","certificates":[{"subject":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate.tcm-11-example.com","issuer":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=tcm-13-example.com","endDate":"2020-04-07T17:33:39Z","startDate":"2019-04-08T17:33:39Z","fingerprint":"1E:DD:AD:32:C3:54:3F:C3:6F:7F:94:51:8D:5E:F7:ED:7C:DB:5D:A5","certificatePem":"-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----","serialNumber":"11612024106234270900","signatureAlgorithm":"SHA256WITHRSA","createdDate":"2020-04-07T17:33:39.110283Z","createdBy":"jsmith2","description":"Optional description for the certificate"},{"subject":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate1.tcm-11-example.com","issuer":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate.tcm-11-example.com","endDate":"2020-04-07T17:43:58Z","startDate":"2019-04-08T17:43:58Z","fingerprint":"1F:DD:AD:32:C3:54:3F:C3:6F:7F:04:51:8D:5E:F7:ED:7C:DB:5D:A5","certificatePem":"-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----","serialNumber":"11612024106234270901","signatureAlgorithm":"SHA256WITHRSA","createdDate":"2020-04-07T17:33:39.110553Z","createdBy":"jsmith2","description":"Optional description for the certificate"}],"validation":null},{"caSetId":"1000","caSetName":"test1","version":2,"versionLink":"/mtls-edge-truststore/v2/ca-sets/1000/versions/2","description":null,"allowInsecureSha1":true,"stagingStatus":"ACTIVE","productionStatus":"ACTIVE","createdDate":"2023-01-10T11:00:00.633919Z","createdBy":"jsmith","modifiedDate":"2023-01-10T12:00:00.733191Z","modifiedBy":"jsmith","certificates":[{"subject":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate.tcm-11-example.com","issuer":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=tcm-13-example.com","endDate":"2020-04-07T17:33:39Z","startDate":"2019-04-08T17:33:39Z","fingerprint":"1E:DD:AD:32:C3:54:3F:C3:6F:7F:94:51:8D:5E:F7:ED:7C:DB:5D:A5","certificatePem":"-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----","serialNumber":"11612024106234270900","signatureAlgorithm":"SHA256WITHRSA","createdDate":"2020-04-07T17:33:39.110284Z","createdBy":"jsmith2","description":"Optional description for the certificate"},{"subject":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate1.tcm-11-example.com","issuer":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate.tcm-11-example.com","endDate":"2020-04-07T17:43:58Z","startDate":"2019-04-08T17:43:58Z","fingerprint":"1F:DD:AD:32:C3:54:3F:C3:6F:7F:04:51:8D:5E:F7:ED:7C:DB:5D:A6","certificatePem":"-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----","serialNumber":"11612024106234270901","signatureAlgorithm":"SHA256WITHRSA","createdDate":"2020-04-07T17:33:39.110443Z","createdBy":"jsmith2","description":"Optional description for the certificate"}],"validation":null}]}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.list_ca_set_versions(models.ListCASetVersionsRequest(
            ca_set_id="123",
            include_certificates=True,
            active_versions_only=True,
        ))
        assert len(result.versions) == 2
        assert result.versions[0].production_status == "ACTIVE"
        assert result.versions[1].production_status == "ACTIVE"

    def test_200_with_active_versions_only(self, mock_session):
        response_body = '{"versions":[{"version":1,"versionLink":"/mtls-edge-truststore/v2/ca-sets/1000/versions/1","caSetId":"1000","caSetName":"test1","description":"Optional description for this version.","allowInsecureSha1":false,"stagingStatus":"ACTIVE","productionStatus":"ACTIVE","createdDate":"2023-01-10T11:00:00.633918Z","createdBy":"jsmith","modifiedDate":"2023-01-10T12:00:00.733190Z","modifiedBy":"jsmith","validation":null},{"caSetId":"1000","caSetName":"test1","version":2,"versionLink":"/mtls-edge-truststore/v2/ca-sets/1000/versions/2","description":null,"allowInsecureSha1":true,"stagingStatus":"ACTIVE","productionStatus":"ACTIVE","createdDate":"2023-01-10T11:00:00.633919Z","createdBy":"jsmith","modifiedDate":"2023-01-10T12:00:00.733191Z","modifiedBy":"jsmith","validation":null}]}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.list_ca_set_versions(models.ListCASetVersionsRequest(
            ca_set_id="1000",
            active_versions_only=True,
        ))
        assert len(result.versions) == 2

    def test_validation_error_missing_ca_set_id(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.list_ca_set_versions(models.ListCASetVersionsRequest())
        assert errors.ErrListCASetVersions in exc.value.title
        assert "CASetID: cannot be blank" in exc.value.detail

    def test_404_ca_set_not_found(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-not-found","title":"CA set not found.","status":404,"detail":"Cannot get CA set version as the CA set with caSetId 123 is not found.","contextInfo":{"caSetId":"123"}}'
        mock_response = create_mock_response(404, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.list_ca_set_versions(models.ListCASetVersionsRequest(ca_set_id="123"))
        assert exc.value.is_equivalent(errors.ErrGetCASetNotFound)


# ---------------------------------------------------------------------------
# TestGetCASetVersionCertificates — from ca_set_versions_test.go
# ---------------------------------------------------------------------------

class TestGetCASetVersionCertificates:
    """Tests for get_ca_set_version_certificates — mirrors Go TestGetCASetVersionCertificates."""

    def test_200_no_filters(self, mock_session):
        response_body = '{"caSetId":"123","caSetName":"test1","version":1,"certificates":[{"subject":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate.tcm-11-example.com","issuer":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=tcm-13-example.com","endDate":"2020-04-07T17:33:39Z","startDate":"2019-04-08T17:33:39Z","fingerprint":"1E:DD:AD:32:C3:54:3F:C3:6F:7F:94:51:8D:5E:F7:ED:7C:DB:5D:A5","certificatePem":"-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----","serialNumber":"11612024106234272000","signatureAlgorithm":"SHA256WITHRSA","createdDate":"2020-04-07T17:33:39.110283Z","description":"Optional description for the certificate","createdBy":"jsmith2"},{"subject":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate1.tcm-11-example.com","issuer":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate.tcm-11-example.com","endDate":"2020-04-07T17:43:58Z","startDate":"2019-04-08T17:43:58Z","fingerprint":"1F:DD:AD:32:C3:54:3F:C3:6F:7F:04:51:8D:5E:F7:ED:7C:DB:5D:A5","certificatePem":"-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----","serialNumber":"11612024106234272000","signatureAlgorithm":"SHA256WITHRSA","createdDate":"2020-04-07T17:33:39.110284Z","description":"Optional description for the certificate","createdBy":"jsmith2"}]}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.get_ca_set_version_certificates(
            models.GetCASetVersionCertificatesRequest(
                ca_set_id="123", version=1))
        assert result.ca_set_id == "123"
        assert result.ca_set_name == "test1"
        assert result.version == 1
        assert len(result.certificates) == 2
        assert result.certificates[0].fingerprint == "1E:DD:AD:32:C3:54:3F:C3:6F:7F:94:51:8D:5E:F7:ED:7C:DB:5D:A5"
        assert result.certificates[1].fingerprint == "1F:DD:AD:32:C3:54:3F:C3:6F:7F:04:51:8D:5E:F7:ED:7C:DB:5D:A5"
        assert_request(mock_session, "GET", "/mtls-edge-truststore/v2/ca-sets/123/versions/1/certificates")

    def test_200_expiring_expired_status(self, mock_session):
        response_body = '{"caSetId":"123","caSetName":"test1","version":1,"certificates":[{"subject":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate.tcm-11-example.com","issuer":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=tcm-13-example.com","endDate":"2020-04-07T17:33:39Z","startDate":"2019-04-08T17:33:39Z","fingerprint":"1E:DD:AD:32:C3:54:3F:C3:6F:7F:94:51:8D:5E:F7:ED:7C:DB:5D:A5","certificatePem":"-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----","serialNumber":"11612024106234272000","signatureAlgorithm":"SHA256WITHRSA","createdDate":"2020-04-07T17:33:39.110283Z","description":"Optional description for the certificate","createdBy":"jsmith2"},{"subject":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate1.tcm-11-example.com","issuer":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate.tcm-11-example.com","endDate":"2020-04-07T17:43:58Z","startDate":"2019-04-08T17:43:58Z","fingerprint":"1F:DD:AD:32:C3:54:3F:C3:6F:7F:04:51:8D:5E:F7:ED:7C:DB:5D:A5","certificatePem":"-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----","serialNumber":"11612024106234272000","signatureAlgorithm":"SHA256WITHRSA","createdDate":"2020-04-07T17:33:39.110284Z","description":"Optional description for the certificate","createdBy":"jsmith2"}]}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.get_ca_set_version_certificates(
            models.GetCASetVersionCertificatesRequest(
                ca_set_id="123", version=1,
                certificate_status=models.EXPIRED_OR_EXPIRING_CERT))
        assert len(result.certificates) == 2

    def test_200_expired_with_threshold_days(self, mock_session):
        response_body = '{"caSetId":"123","caSetName":"test1","version":1,"certificates":[{"subject":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate.tcm-11-example.com","issuer":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=tcm-13-example.com","endDate":"2020-04-07T17:33:39Z","startDate":"2019-04-08T17:33:39Z","fingerprint":"1E:DD:AD:32:C3:54:3F:C3:6F:7F:94:51:8D:5E:F7:ED:7C:DB:5D:A5","certificatePem":"-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----","serialNumber":"11612024106234272000","signatureAlgorithm":"SHA256WITHRSA","createdDate":"2020-04-07T17:33:39.110283Z","description":"Optional description for the certificate","createdBy":"jsmith2"},{"subject":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate1.tcm-11-example.com","issuer":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate.tcm-11-example.com","endDate":"2020-04-07T17:43:58Z","startDate":"2019-04-08T17:43:58Z","fingerprint":"1F:DD:AD:32:C3:54:3F:C3:6F:7F:04:51:8D:5E:F7:ED:7C:DB:5D:A5","certificatePem":"-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----","serialNumber":"11612024106234272000","signatureAlgorithm":"SHA256WITHRSA","createdDate":"2020-04-07T17:33:39.110284Z","description":"Optional description for the certificate","createdBy":"jsmith2"}]}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.get_ca_set_version_certificates(
            models.GetCASetVersionCertificatesRequest(
                ca_set_id="123", version=1,
                expiry_threshold_in_days=10,
                certificate_status=models.EXPIRED_CERT))
        assert len(result.certificates) == 2

    def test_200_expired_with_threshold_timestamp(self, mock_session):
        response_body = '{"caSetId":"123","caSetName":"test1","version":1,"certificates":[{"subject":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate1.tcm-11-example.com","issuer":"C=US,ST=MA,L=Cambridge,O=Akamai,CN=intermediate.tcm-11-example.com","endDate":"2020-04-07T17:43:58Z","startDate":"2019-04-08T17:43:58Z","fingerprint":"1F:DD:AD:32:C3:54:3F:C3:6F:7F:04:51:8D:5E:F7:ED:7C:DB:5D:A5","certificatePem":"-----BEGIN CERTIFICATE-----...-----END CERTIFICATE-----","serialNumber":"11612024106234272000","signatureAlgorithm":"SHA256WITHRSA","createdDate":"2020-04-07T17:33:39.110284Z","description":"Optional description for the certificate","createdBy":"jsmith2"}]}'
        mock_response = create_mock_response(200, response_body)
        mock_session.exec.return_value = (mock_response, json.loads(response_body))
        client = Client(mock_session)
        result = client.get_ca_set_version_certificates(
            models.GetCASetVersionCertificatesRequest(
                ca_set_id="123", version=1,
                expiry_threshold_timestamp="2020-04-07T17:40:00Z",
                certificate_status=models.EXPIRED_CERT))
        assert len(result.certificates) == 1

    def test_validation_error_missing_ca_set_id_and_version(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set_version_certificates(
                models.GetCASetVersionCertificatesRequest())
        assert errors.ErrGetCASetVersionCertificates in exc.value.title
        assert "CASetID: cannot be blank" in exc.value.detail
        assert "Version: cannot be blank" in exc.value.detail

    def test_validation_error_invalid_certificate_status(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set_version_certificates(
                models.GetCASetVersionCertificatesRequest(
                    ca_set_id="123", version=1,
                    certificate_status="EXPIRY"))
        assert errors.ErrGetCASetVersionCertificates in exc.value.title
        assert "CertificateStatus" in exc.value.detail

    def test_validation_error_invalid_status_for_expiry_threshold_days(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set_version_certificates(
                models.GetCASetVersionCertificatesRequest(
                    ca_set_id="123", version=1,
                    expiry_threshold_in_days=10,
                    certificate_status=models.ACTIVE_CERT))
        assert errors.ErrGetCASetVersionCertificates in exc.value.title
        assert "ExpiryThresholdInDays" in exc.value.detail

    def test_validation_error_invalid_status_for_expiry_threshold_timestamp(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set_version_certificates(
                models.GetCASetVersionCertificatesRequest(
                    ca_set_id="123", version=1,
                    expiry_threshold_timestamp="2023-01-01T00:00:00Z",
                    certificate_status=models.ACTIVE_CERT))
        assert errors.ErrGetCASetVersionCertificates in exc.value.title
        assert "ExpiryThresholdTimestamp" in exc.value.detail

    def test_validation_error_missing_status_with_threshold_days(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set_version_certificates(
                models.GetCASetVersionCertificatesRequest(
                    ca_set_id="123", version=1,
                    expiry_threshold_in_days=10))
        assert errors.ErrGetCASetVersionCertificates in exc.value.title
        assert "ExpiryThresholdInDays" in exc.value.detail
        assert "CertificateStatus must be provided" in exc.value.detail

    def test_validation_error_missing_status_with_threshold_timestamp(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set_version_certificates(
                models.GetCASetVersionCertificatesRequest(
                    ca_set_id="123", version=1,
                    expiry_threshold_timestamp="2023-01-01T00:00:00Z"))
        assert errors.ErrGetCASetVersionCertificates in exc.value.title
        assert "ExpiryThresholdTimestamp" in exc.value.detail
        assert "CertificateStatus must be provided" in exc.value.detail

    def test_validation_error_both_thresholds_set(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set_version_certificates(
                models.GetCASetVersionCertificatesRequest(
                    ca_set_id="123", version=1,
                    certificate_status=models.EXPIRED_CERT,
                    expiry_threshold_in_days=10,
                    expiry_threshold_timestamp="2023-01-01T00:00:00Z"))
        assert errors.ErrGetCASetVersionCertificates in exc.value.title
        assert "ExpiryThresholdInDays cannot be used with ExpiryThresholdTimestamp" in exc.value.detail

    def test_validation_error_past_timestamp_with_expiring(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set_version_certificates(
                models.GetCASetVersionCertificatesRequest(
                    ca_set_id="123", version=1,
                    certificate_status=models.EXPIRING_CERT,
                    expiry_threshold_timestamp="2023-01-01T00:00:00Z"))
        assert errors.ErrGetCASetVersionCertificates in exc.value.title
        assert "ExpiryThresholdTimestamp" in exc.value.detail

    def test_validation_error_future_timestamp_with_expired(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set_version_certificates(
                models.GetCASetVersionCertificatesRequest(
                    ca_set_id="123", version=1,
                    certificate_status=models.EXPIRED_CERT,
                    expiry_threshold_timestamp="3023-01-01T00:00:00Z"))
        assert errors.ErrGetCASetVersionCertificates in exc.value.title
        assert "ExpiryThresholdTimestamp" in exc.value.detail

    def test_404_ca_set_not_found(self, mock_session):
        response_body = '{"type":"/mtls-edge-truststore/error-types/ca-set-not-found","title":"CA set not found.","status":404,"detail":"Cannot get CA set version as the CA set with caSetId 123 is not found.","contextInfo":{"caSetId":"123"}}'
        mock_response = create_mock_response(404, response_body)
        mock_session.exec.return_value = (mock_response, None)
        client = Client(mock_session)
        with pytest.raises(errors.Error) as exc:
            client.get_ca_set_version_certificates(
                models.GetCASetVersionCertificatesRequest(
                    ca_set_id="123", version=1))
        assert exc.value.is_equivalent(errors.ErrGetCASetNotFound)
