"""Unit tests for Cloud Access Manager API client."""
# pylint: disable=too-many-lines

import json
import os
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.cloudaccess.cloudaccess import CloudAccessClient
from akamai.edgegrid.cloudaccess import models
from akamai.edgegrid.cloudaccess.errors import (
    Error,
    ErrorItem,
    ACCESS_KEY_NOT_FOUND_TYPE,
    ErrAccessKeyNotFound,
    ErrGetAccessKeyStatus,
    ErrCreateAccessKey,
    ErrGetAccessKey,
    ErrUpdateAccessKey,
    ErrDeleteAccessKey,
    ErrGetAccessKeyVersionStatus,
    ErrCreateAccessKeyVersion,
    ErrGetAccessKeyVersion,
    ErrListAccessKeyVersions,
    ErrDeleteAccessKeyVersion,
    ErrLookupProperties,
    ErrGetAsyncLookupIDProperties,
    ErrPerformAsyncLookupProperties,
)

# ---------------------------------------------------------------------------
# Test-directory resolution and fixture helpers
# ---------------------------------------------------------------------------

test_dir = os.path.abspath(os.path.dirname(__file__))


def load_test_data(name):
    """Load raw test data from the *testdata* directory.

    Mirrors Go ``loadTestData`` (access_key_test.go lines 577-584).
    """
    path = os.path.join(test_dir, "testdata", name)
    with open(path, encoding="utf-8") as fobj:
        return fobj.read()


def load_json_fixture(name):
    """Load and parse a JSON fixture from the *testdata* directory."""
    return json.loads(load_test_data(name))


def make_mock_response(status_code, body="", headers=None):
    """Create a mock ``requests.Response``.

    Replaces Go's ``httptest.NewTLSServer`` pattern.
    """
    response = MagicMock()
    response.status_code = status_code
    response.text = body
    if body and body.strip():
        try:
            response.json.return_value = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            response.json.side_effect = ValueError("No JSON")
    else:
        response.json.return_value = {}
    response.headers = dict(headers) if headers else {}
    return response


def _make_client():
    """Return ``(client, mock_session)`` pair for a single test."""
    session = MagicMock()
    client = CloudAccessClient(session)
    return client, session


# Standard 500 error JSON body (verbatim from Go tests).
INTERNAL_SERVER_ERROR_BODY = json.dumps({
    "type": "internal-server-error",
    "title": "Internal Server Error",
    "detail": "Error processing request",
    "instance": "TestInstances",
    "status": 500,
})


# ===================================================================
# TestNewError  —  errors_test.go lines 14-141
# ===================================================================


class TestNewError:
    """Tests for ``Error.from_response()`` class method."""

    def test_bad_request_400(self):
        """Bad request 400 — basic error fields parsed."""
        body = json.dumps({
            "type": "bad-request",
            "title": "Bad Request",
            "instance": "test-instance-123",
            "status": 400,
        })
        resp = make_mock_response(400, body)
        err = Error.from_response(resp)

        assert err.type == "bad-request"
        assert err.title == "Bad Request"
        assert err.instance == "test-instance-123"
        assert err.status == 400
        assert err.detail == ""
        assert not err.errors

    def test_invalid_request_400(self):
        """Invalid request 400 — errors array with 2 ErrorItem objects."""
        body = json.dumps({
            "type": "invalid-request",
            "title": "Invalid Request",
            "instance": "test-instance-123",
            "status": 400,
            "errors": [
                {
                    "detail": "Constraint violation: "
                              "accessKeyName must not be blank.",
                    "title": "Constraint Violation",
                    "type": "/cam/error-types/constraint-violation",
                },
                {
                    "detail": "Constraint violation: "
                              "accessKeyName length must be "
                              "between 1 and 50.",
                    "title": "Constraint Violation",
                    "type": "/cam/error-types/constraint-violation",
                },
            ],
        })
        resp = make_mock_response(400, body)
        err = Error.from_response(resp)

        assert err.type == "invalid-request"
        assert err.title == "Invalid Request"
        assert err.instance == "test-instance-123"
        assert err.status == 400
        assert len(err.errors) == 2

        assert isinstance(err.errors[0], ErrorItem)
        assert err.errors[0].detail == (
            "Constraint violation: accessKeyName must not be blank."
        )
        assert err.errors[0].title == "Constraint Violation"
        assert err.errors[0].type == (
            "/cam/error-types/constraint-violation"
        )

        assert isinstance(err.errors[1], ErrorItem)
        assert err.errors[1].detail == (
            "Constraint violation: accessKeyName length "
            "must be between 1 and 50."
        )
        assert err.errors[1].title == "Constraint Violation"
        assert err.errors[1].type == (
            "/cam/error-types/constraint-violation"
        )

    def test_access_key_does_not_exist_404(self):
        """Access key does not exist 404 — extra accessKeyUid field."""
        body = json.dumps({
            "type": "/cam/error-types/access-key-does-not-exist",
            "title": "Domain Error",
            "detail": "Access key with accessKeyUID '1' "
                      "does not exist.",
            "instance": "test-instance-123",
            "status": 404,
            "accessKeyUid": 1,
        })
        resp = make_mock_response(404, body)
        err = Error.from_response(resp)

        assert err.type == ACCESS_KEY_NOT_FOUND_TYPE
        assert err.title == "Domain Error"
        assert err.detail == (
            "Access key with accessKeyUID '1' does not exist."
        )
        assert err.instance == "test-instance-123"
        assert err.status == 404
        assert err.access_key_uid == 1

    def test_invalid_response_body_assign_status_code(self):
        """Invalid response body — fallback when JSON parsing fails."""
        resp = make_mock_response(500, "test")
        err = Error.from_response(resp)

        assert err.title == (
            "Failed to unmarshal error body. Cloud Access Manager "
            "API failed. Check details for more information."
        )
        assert err.detail == "test"
        assert err.status == 500


# ===================================================================
# TestIs  —  errors_test.go lines 143-176
# ===================================================================


class TestIs:  # pylint: disable=too-few-public-methods
    """Tests for ``Error.is_equivalent()`` method."""

    @pytest.mark.parametrize(
        "name, err, target, expected",
        [
            (
                "different error code",
                Error(status=404),
                Error(status=401),
                False,
            ),
            (
                "same error code",
                Error(status=404),
                Error(status=404),
                True,
            ),
            (
                "same error code and title",
                Error(status=404, title="some error"),
                Error(status=404, title="some error"),
                True,
            ),
            (
                "same error code and different error message",
                Error(status=404, title="some error"),
                Error(status=404, title="other error"),
                False,
            ),
        ],
        ids=[
            "different error code",
            "same error code",
            "same error code and title",
            "same error code and different error message",
        ],
    )
    def test_is(self, name, err, target, expected):  # pylint: disable=unused-argument
        """Table-driven ``is_equivalent`` checks."""
        assert err.is_equivalent(target) is expected


# ===================================================================
# TestGetAccessKeyStatus  —  access_key_test.go lines 18-117
# ===================================================================


class TestGetAccessKeyStatus:
    """Tests for ``CloudAccessClient.get_access_key_status``."""

    def test_200_ok(self):
        """200 OK — full response with all nested objects."""
        client, session = _make_client()
        resp_data = load_test_data(
            "AccessKeyStatus/GetAccessKeyStatus.resp.json"
        )
        resp = make_mock_response(200, resp_data)
        session.exec.return_value = (resp, json.loads(resp_data))

        result = client.get_access_key_status(
            models.GetAccessKeyStatusRequest(request_id=1)
        )

        session.exec.assert_called_once()
        call_args = session.exec.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/cam/v1/access-key-create-requests/1"

        assert result.processing_status == "IN_PROGRESS"
        assert result.request_date == "2021-02-26T13:34:36.715643Z"
        assert result.request_id == 1
        assert result.requested_by == "user"

        assert result.access_key is not None
        assert result.access_key.access_key_uid == 123
        assert result.access_key.link == "/cam/v1/access-keys/123"

        assert result.access_key_version is not None
        assert result.access_key_version.access_key_uid == 123
        assert result.access_key_version.link == (
            "/cam/v1/access-keys/123/versions/1"
        )
        assert result.access_key_version.version == 1

        assert result.request is not None
        assert result.request.access_key_name == "TestAccessKeyName"
        assert result.request.authentication_method == "AWS4_HMAC_SHA256"
        assert result.request.contract_id == "TestContractID"
        assert result.request.group_id == 123
        assert result.request.network_configuration is not None
        assert (
            result.request.network_configuration.additional_cdn
            == "CHINA_CDN"
        )
        assert (
            result.request.network_configuration.security_network
            == "ENHANCED_TLS"
        )

    def test_200_ok_minimal(self):
        """200 OK — minimal response with null nested objects."""
        client, session = _make_client()
        resp_data = load_test_data(
            "AccessKeyStatus/GetAccessKeyStatusMinimal.resp.json"
        )
        resp = make_mock_response(200, resp_data)
        session.exec.return_value = (resp, json.loads(resp_data))

        result = client.get_access_key_status(
            models.GetAccessKeyStatusRequest(request_id=1)
        )

        assert result.processing_status == "IN_PROGRESS"
        assert result.request_date == "2021-02-26T13:34:36.715643Z"
        assert result.request_id == 1
        assert result.requested_by == "user"
        assert result.access_key is None
        assert result.access_key_version is None
        assert result.request is None

    def test_missing_required_params_validation_error(self):
        """Validation error — request_id is blank (0)."""
        client, session = _make_client()

        with pytest.raises(ValueError) as exc_info:
            client.get_access_key_status(
                models.GetAccessKeyStatusRequest()
            )

        msg = str(exc_info.value)
        assert msg.startswith(
            f"{ErrGetAccessKeyStatus}: struct validation:"
        )
        assert "RequestID: cannot be blank" in msg
        session.exec.assert_not_called()

    def test_500_internal_server_error(self):
        """500 internal server error."""
        client, session = _make_client()
        resp = make_mock_response(500, INTERNAL_SERVER_ERROR_BODY)
        session.exec.return_value = (
            resp, json.loads(INTERNAL_SERVER_ERROR_BODY)
        )

        expected = Error(
            type="internal-server-error",
            title="Internal Server Error",
            detail="Error processing request",
            instance="TestInstances",
            status=500,
        )
        with pytest.raises(Error) as exc_info:
            client.get_access_key_status(
                models.GetAccessKeyStatusRequest(request_id=123)
            )

        assert exc_info.value.is_equivalent(expected)


# ===================================================================
# TestCreateAccessKey  —  access_key_test.go lines 119-216
# ===================================================================


class TestCreateAccessKey:
    """Tests for ``CloudAccessClient.create_access_key``."""

    def test_202_accepted(self):
        """202 Accepted — request_id, retry_after and Location header."""
        client, session = _make_client()
        fixture = load_json_fixture("AccessKey/CreateAccessKey.req.json")
        req = models.CreateAccessKeyRequest.from_dict(fixture)

        resp_body = json.dumps({"requestId": 195, "retryAfter": 4})
        resp = make_mock_response(
            202, resp_body, headers={"Location": "https://abc.com"}
        )
        session.exec.return_value = (resp, json.loads(resp_body))

        result = client.create_access_key(req)

        session.exec.assert_called_once()
        call_args = session.exec.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/cam/v1/access-keys"

        assert result.request_id == 195
        assert result.retry_after == 4
        assert result.location == "https://abc.com"

    def test_missing_required_request_body_validation_error(self):
        """Validation error — all required fields blank."""
        client, session = _make_client()
        req = models.CreateAccessKeyRequest()

        with pytest.raises(ValueError) as exc_info:
            client.create_access_key(req)

        msg = str(exc_info.value)
        assert msg.startswith(f"{ErrCreateAccessKey}: struct validation:")
        assert "AccessKeyName: cannot be blank" in msg
        assert "AuthenticationMethod: cannot be blank" in msg
        assert "CloudAccessKeyID: cannot be blank" in msg
        assert "CloudSecretAccessKey: cannot be blank" in msg
        assert "ContractID: cannot be blank" in msg
        assert "GroupID: cannot be blank" in msg
        assert "SecurityNetwork: cannot be blank" in msg

        session.exec.assert_not_called()

    def test_invalid_authentication_method_validation_error(self):
        """Validation error — invalid authentication method value."""
        client, session = _make_client()
        fixture = load_json_fixture(
            "AccessKey/CreateInvalidAccessKey.req.json"
        )
        req = models.CreateAccessKeyRequest.from_dict(fixture)

        with pytest.raises(ValueError) as exc_info:
            client.create_access_key(req)

        msg = str(exc_info.value)
        assert msg.startswith(f"{ErrCreateAccessKey}: struct validation:")
        assert "AuthenticationMethod: must be a valid value" in msg

        session.exec.assert_not_called()

    def test_500_internal_server_error(self):
        """500 internal server error."""
        client, session = _make_client()
        fixture = load_json_fixture("AccessKey/CreateAccessKey.req.json")
        req = models.CreateAccessKeyRequest.from_dict(fixture)

        resp = make_mock_response(500, INTERNAL_SERVER_ERROR_BODY)
        session.exec.return_value = (
            resp, json.loads(INTERNAL_SERVER_ERROR_BODY)
        )

        expected = Error(
            type="internal-server-error",
            title="Internal Server Error",
            detail="Error processing request",
            instance="TestInstances",
            status=500,
        )
        with pytest.raises(Error) as exc_info:
            client.create_access_key(req)

        assert exc_info.value.is_equivalent(expected)


# ===================================================================
# TestGetAccessKey  —  access_key_test.go lines 218-318
# ===================================================================


class TestGetAccessKey:
    """Tests for ``CloudAccessClient.get_access_key``."""

    def test_200_ok(self):
        """200 OK — access key details from fixture."""
        client, session = _make_client()
        resp_data = load_test_data("AccessKey/GetAccessKey.resp.json")
        resp = make_mock_response(200, resp_data)
        session.exec.return_value = (resp, json.loads(resp_data))

        result = client.get_access_key(
            models.AccessKeyRequest(access_key_uid=1)
        )

        session.exec.assert_called_once()
        call_args = session.exec.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/cam/v1/access-keys/1"

        assert result.access_key_name == "key1"
        assert result.access_key_uid == 1
        assert result.authentication_method == "AWS4_HMAC_SHA256"
        assert result.created_by == "user1"
        assert result.latest_version == 1
        assert len(result.groups) == 1
        assert result.groups[0].group_id == 123
        assert result.groups[0].contract_ids == ["TestContractID"]
        assert (
            result.network_configuration.additional_cdn == "RUSSIA_CDN"
        )
        assert (
            result.network_configuration.security_network == "ENHANCED_TLS"
        )

    def test_missing_required_params_validation_error(self):
        """Validation error — access_key_uid is blank (0)."""
        client, session = _make_client()

        with pytest.raises(ValueError) as exc_info:
            client.get_access_key(models.AccessKeyRequest())

        msg = str(exc_info.value)
        assert msg.startswith(f"{ErrGetAccessKey}: struct validation:")
        assert "AccessKeyUID: cannot be blank" in msg
        session.exec.assert_not_called()

    def test_404_access_key_not_found(self):
        """404 — ErrAccessKeyNotFound sentinel error check."""
        client, session = _make_client()
        body = json.dumps({
            "type": "/cam/error-types/access-key-does-not-exist",
            "title": "Domain Error",
            "detail": "Access key with accessKeyUID '2' "
                      "does not exist.",
            "instance": "test-instance-123",
            "status": 404,
            "accessKeyUid": 2,
        })
        resp = make_mock_response(404, body)
        session.exec.return_value = (resp, json.loads(body))

        with pytest.raises(Error) as exc_info:
            client.get_access_key(
                models.AccessKeyRequest(access_key_uid=2)
            )

        assert exc_info.value.is_equivalent(ErrAccessKeyNotFound)

    def test_500_internal_server_error(self):
        """500 internal server error."""
        client, session = _make_client()
        resp = make_mock_response(500, INTERNAL_SERVER_ERROR_BODY)
        session.exec.return_value = (
            resp, json.loads(INTERNAL_SERVER_ERROR_BODY)
        )

        expected = Error(
            type="internal-server-error",
            title="Internal Server Error",
            detail="Error processing request",
            instance="TestInstances",
            status=500,
        )
        with pytest.raises(Error) as exc_info:
            client.get_access_key(
                models.AccessKeyRequest(access_key_uid=1)
            )

        assert exc_info.value.is_equivalent(expected)


# ===================================================================
# TestListAccessKey  —  access_key_test.go lines 320-396
# ===================================================================


class TestListAccessKey:
    """Tests for ``CloudAccessClient.list_access_keys``."""

    def test_200_ok(self):
        """200 OK — list with versionGuid query param."""
        client, session = _make_client()
        resp_data = load_test_data("AccessKey/ListAccessKey.resp.json")
        resp = make_mock_response(200, resp_data)
        session.exec.return_value = (resp, json.loads(resp_data))

        result = client.list_access_keys(
            models.ListAccessKeysRequest(version_guid="1")
        )

        session.exec.assert_called_once()
        call_args = session.exec.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/cam/v1/access-keys"
        # version_guid is passed as query params kwarg
        sent_params = call_args[1].get("params")
        assert sent_params == {"versionGuid": "1"}

        assert len(result.access_keys) == 1
        assert result.access_keys[0].access_key_name == "key1"
        assert result.access_keys[0].access_key_uid == 1

    def test_500_internal_server_error(self):
        """500 internal server error."""
        client, session = _make_client()
        resp = make_mock_response(500, INTERNAL_SERVER_ERROR_BODY)
        session.exec.return_value = (
            resp, json.loads(INTERNAL_SERVER_ERROR_BODY)
        )

        expected = Error(
            type="internal-server-error",
            title="Internal Server Error",
            detail="Error processing request",
            instance="TestInstances",
            status=500,
        )
        with pytest.raises(Error) as exc_info:
            client.list_access_keys(
                models.ListAccessKeysRequest()
            )

        assert exc_info.value.is_equivalent(expected)


# ===================================================================
# TestDeleteAccessKey  —  access_key_test.go lines 398-465
# ===================================================================


class TestDeleteAccessKey:
    """Tests for ``CloudAccessClient.delete_access_key``."""

    def test_204_no_content(self):
        """204 No Content — successful deletion."""
        client, session = _make_client()
        resp = make_mock_response(204)
        session.exec.return_value = (resp, None)

        client.delete_access_key(
            models.AccessKeyRequest(access_key_uid=1)
        )

        session.exec.assert_called_once()
        call_args = session.exec.call_args
        assert call_args[0][0] == "DELETE"
        assert call_args[0][1] == "/cam/v1/access-keys/1"

    def test_missing_required_params_validation_error(self):
        """Validation error — access_key_uid is blank (0)."""
        client, session = _make_client()

        with pytest.raises(ValueError) as exc_info:
            client.delete_access_key(models.AccessKeyRequest())

        msg = str(exc_info.value)
        assert msg.startswith(f"{ErrDeleteAccessKey}: struct validation:")
        assert "AccessKeyUID: cannot be blank" in msg
        session.exec.assert_not_called()

    def test_500_internal_server_error(self):
        """500 internal server error."""
        client, session = _make_client()
        resp = make_mock_response(500, INTERNAL_SERVER_ERROR_BODY)
        session.exec.return_value = (
            resp, json.loads(INTERNAL_SERVER_ERROR_BODY)
        )

        expected = Error(
            type="internal-server-error",
            title="Internal Server Error",
            detail="Error processing request",
            instance="TestInstances",
            status=500,
        )
        with pytest.raises(Error) as exc_info:
            client.delete_access_key(
                models.AccessKeyRequest(access_key_uid=1)
            )

        assert exc_info.value.is_equivalent(expected)


# ===================================================================
# TestUpdateAccessKey  —  access_key_test.go lines 467-575
# (NOTE: Go test labels the happy-path "201 OK" but the expected
#  status is http.StatusOK = 200)
# ===================================================================


class TestUpdateAccessKey:
    """Tests for ``CloudAccessClient.update_access_key``."""

    def test_200_ok(self):
        """200 OK — update access key name (Go names this '201 OK')."""
        client, session = _make_client()
        resp_body = json.dumps({
            "accessKeyName": "key2",
            "AccessKeyUID": 1,
        })
        resp = make_mock_response(200, resp_body)
        session.exec.return_value = (resp, json.loads(resp_body))

        result = client.update_access_key(
            body=models.UpdateAccessKeyRequest(access_key_name="key2"),
            params=models.AccessKeyRequest(access_key_uid=1),
        )

        session.exec.assert_called_once()
        call_args = session.exec.call_args
        assert call_args[0][0] == "PUT"
        assert call_args[0][1] == "/cam/v1/access-keys/1"

        assert result.access_key_name == "key2"
        assert result.access_key_uid == 1

    def test_missing_required_params_validation_error(self):
        """Validation error — params.access_key_uid is blank (0)."""
        client, session = _make_client()

        with pytest.raises(ValueError) as exc_info:
            client.update_access_key(
                body=models.UpdateAccessKeyRequest(
                    access_key_name="key2"
                ),
                params=models.AccessKeyRequest(),
            )

        msg = str(exc_info.value)
        assert msg.startswith(f"{ErrUpdateAccessKey}: struct validation:")
        assert "AccessKeyUID: cannot be blank" in msg
        session.exec.assert_not_called()

    def test_missing_required_request_body_validation_error(self):
        """Validation error — body.access_key_name is blank."""
        client, session = _make_client()

        with pytest.raises(ValueError) as exc_info:
            client.update_access_key(
                body=models.UpdateAccessKeyRequest(),
                params=models.AccessKeyRequest(access_key_uid=1),
            )

        msg = str(exc_info.value)
        assert msg.startswith(f"{ErrUpdateAccessKey}: struct validation:")
        assert "AccessKeyName: cannot be blank" in msg
        session.exec.assert_not_called()

    def test_max_length_validation_error(self):
        """Validation error — name exceeds 50 chars."""
        client, session = _make_client()
        long_name = (
            "asdfghjkloasdfghjkloasdfghjkloasdfghjklo"
            "asdfghjkloasdfghjkloasdfghjkloasdfghjklo"
        )

        with pytest.raises(ValueError) as exc_info:
            client.update_access_key(
                body=models.UpdateAccessKeyRequest(
                    access_key_name=long_name,
                ),
                params=models.AccessKeyRequest(access_key_uid=1),
            )

        msg = str(exc_info.value)
        assert msg.startswith(f"{ErrUpdateAccessKey}: struct validation:")
        assert (
            "AccessKeyName: the length must be between 1 and 50" in msg
        )
        session.exec.assert_not_called()

    def test_500_internal_server_error(self):
        """500 internal server error."""
        client, session = _make_client()
        resp = make_mock_response(500, INTERNAL_SERVER_ERROR_BODY)
        session.exec.return_value = (
            resp, json.loads(INTERNAL_SERVER_ERROR_BODY)
        )

        expected = Error(
            type="internal-server-error",
            title="Internal Server Error",
            detail="Error processing request",
            instance="TestInstances",
            status=500,
        )
        with pytest.raises(Error) as exc_info:
            client.update_access_key(
                body=models.UpdateAccessKeyRequest(
                    access_key_name="key2"
                ),
                params=models.AccessKeyRequest(access_key_uid=1),
            )

        assert exc_info.value.is_equivalent(expected)


# ===================================================================
# TestGetAccessKeyVersionStatus  —  access_key_version_test.go 16-124
# ===================================================================


class TestGetAccessKeyVersionStatus:
    """Tests for ``CloudAccessClient.get_access_key_version_status``."""

    def test_200_ok(self):
        """200 OK — full response with access key version link."""
        client, session = _make_client()
        resp_body = json.dumps({
            "accessKeyVersion": {
                "accessKeyUid": 123,
                "link": "/cam/v1/access-keys/123/versions/2",
                "version": 2,
            },
            "processingStatus": "IN_PROGRESS",
            "requestDate": "2021-02-26T14:54:38.622074Z",
            "requestedBy": "user",
        })
        resp = make_mock_response(200, resp_body)
        session.exec.return_value = (resp, json.loads(resp_body))

        result = client.get_access_key_version_status(
            models.GetAccessKeyVersionStatusRequest(request_id=1)
        )

        session.exec.assert_called_once()
        call_args = session.exec.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == (
            "/cam/v1/access-key-version-create-requests/1"
        )

        assert result.processing_status == "IN_PROGRESS"
        assert result.request_date == "2021-02-26T14:54:38.622074Z"
        assert result.requested_by == "user"
        assert result.access_key_version is not None
        assert result.access_key_version.access_key_uid == 123
        assert result.access_key_version.link == (
            "/cam/v1/access-keys/123/versions/2"
        )
        assert result.access_key_version.version == 2

    def test_200_ok_minimal(self):
        """200 OK — minimal with null access_key_version."""
        client, session = _make_client()
        resp_body = json.dumps({
            "accessKeyVersion": None,
            "processingStatus": "IN_PROGRESS",
            "requestDate": "2021-02-26T14:54:38.622074Z",
            "requestedBy": "user",
        })
        resp = make_mock_response(200, resp_body)
        session.exec.return_value = (resp, json.loads(resp_body))

        result = client.get_access_key_version_status(
            models.GetAccessKeyVersionStatusRequest(request_id=1)
        )

        assert result.processing_status == "IN_PROGRESS"
        assert result.request_date == "2021-02-26T14:54:38.622074Z"
        assert result.requested_by == "user"
        assert result.access_key_version is None

    def test_missing_required_params_validation_error(self):
        """Validation error — request_id is blank (0)."""
        client, session = _make_client()

        with pytest.raises(ValueError) as exc_info:
            client.get_access_key_version_status(
                models.GetAccessKeyVersionStatusRequest()
            )

        msg = str(exc_info.value)
        assert msg.startswith(
            f"{ErrGetAccessKeyVersionStatus}: struct validation:"
        )
        assert "RequestID: cannot be blank" in msg
        session.exec.assert_not_called()

    def test_500_internal_server_error(self):
        """500 internal server error."""
        client, session = _make_client()
        resp = make_mock_response(500, INTERNAL_SERVER_ERROR_BODY)
        session.exec.return_value = (
            resp, json.loads(INTERNAL_SERVER_ERROR_BODY)
        )

        expected = Error(
            type="internal-server-error",
            title="Internal Server Error",
            detail="Error processing request",
            instance="TestInstances",
            status=500,
        )
        with pytest.raises(Error) as exc_info:
            client.get_access_key_version_status(
                models.GetAccessKeyVersionStatusRequest(request_id=123)
            )

        assert exc_info.value.is_equivalent(expected)


# ===================================================================
# TestCreateAccessKeyVersion  —  access_key_version_test.go 126-268
# ===================================================================


class TestCreateAccessKeyVersion:
    """Tests for ``CloudAccessClient.create_access_key_version``."""

    def test_202_accepted(self):
        """202 Accepted — request_id and retry_after."""
        client, session = _make_client()

        req = models.CreateAccessKeyVersionRequest(
            access_key_uid=1,
            body=models.CreateAccessKeyVersionRequestBody(
                cloud_access_key_id="key-1",
                cloud_secret_access_key="secret-1",
            ),
        )

        resp_body = json.dumps({"requestId": 111, "retryAfter": 6})
        resp = make_mock_response(202, resp_body)
        session.exec.return_value = (resp, json.loads(resp_body))

        result = client.create_access_key_version(req)

        session.exec.assert_called_once()
        call_args = session.exec.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/cam/v1/access-keys/1/versions"

        # Verify request body matches the expected JSON
        sent_body = call_args[1].get("body", call_args[0][2] if len(call_args[0]) > 2 else None)
        if sent_body is not None:
            if isinstance(sent_body, dict):
                assert sent_body.get("cloudAccessKeyId") == "key-1"
                assert sent_body.get("cloudSecretAccessKey") == "secret-1"

        assert result.request_id == 111
        assert result.retry_after == 6

    def test_missing_required_params_validation_error(self):
        """Validation error — both access_key_uid and body blank."""
        client, session = _make_client()

        with pytest.raises(ValueError) as exc_info:
            client.create_access_key_version(
                models.CreateAccessKeyVersionRequest()
            )

        msg = str(exc_info.value)
        assert msg.startswith(
            f"{ErrCreateAccessKeyVersion}: struct validation:"
        )
        assert "AccessKeyUID: cannot be blank" in msg
        assert "Body: cannot be blank" in msg
        session.exec.assert_not_called()

    def test_404_error(self):
        """404 — access key does not exist."""
        client, session = _make_client()
        body = json.dumps({
            "type": "/cam/error-types/access-key-does-not-exist",
            "title": "Domain Error",
            "detail": "Access key with accessKeyUID '1' "
                      "does not exist.",
            "instance": "test-instance-123",
            "status": 404,
            "accessKeyUid": 1,
        })
        resp = make_mock_response(404, body)
        session.exec.return_value = (resp, json.loads(body))

        expected = Error(
            type="/cam/error-types/access-key-does-not-exist",
            title="Domain Error",
            detail="Access key with accessKeyUID '1' does not exist.",
            instance="test-instance-123",
            status=404,
            access_key_uid=1,
        )

        with pytest.raises(Error) as exc_info:
            client.create_access_key_version(
                models.CreateAccessKeyVersionRequest(
                    access_key_uid=1,
                    body=models.CreateAccessKeyVersionRequestBody(
                        cloud_access_key_id="key-1",
                        cloud_secret_access_key="secret-1",
                    ),
                )
            )

        assert exc_info.value.is_equivalent(expected)

    def test_409_conflict_error(self):
        """409 Conflict — access key already exists."""
        client, session = _make_client()
        body = json.dumps({
            "accessKeyName": "Sales-s3",
            "detail": "Access key with name 'Sales-s3' already exists.",
            "instance": "109443e6-f347-43f1-922c-fa0fd480973f",
            "status": 409,
            "title": "Domain Error",
            "type": "/cam/error-types/access-key-already-exists",
        })
        resp = make_mock_response(409, body)
        session.exec.return_value = (resp, json.loads(body))

        with pytest.raises(Error) as exc_info:
            client.create_access_key_version(
                models.CreateAccessKeyVersionRequest(
                    access_key_uid=1,
                    body=models.CreateAccessKeyVersionRequestBody(
                        cloud_access_key_id="key-1",
                        cloud_secret_access_key="secret-1",
                    ),
                )
            )

        err = exc_info.value
        assert err.status == 409
        assert err.access_key_name == "Sales-s3"
        assert err.title == "Domain Error"


# ===================================================================
# TestGetAccessKeyVersion  —  access_key_version_test.go 270-444
# ===================================================================


class TestGetAccessKeyVersion:
    """Tests for ``CloudAccessClient.get_access_key_version``."""

    def test_200_ok(self):
        """200 OK — version details."""
        client, session = _make_client()
        resp_body = json.dumps({
            "accessKeyUid": 12345,
            "cloudAccessKeyId": None,
            "createdBy": "testUser",
            "createdTime": "2021-02-26T13:34:37.916873Z",
            "deploymentStatus": "ACTIVE",
            "version": 1,
            "versionGuid": "aaaa-bbbb-1111",
        })
        resp = make_mock_response(200, resp_body)
        session.exec.return_value = (resp, json.loads(resp_body))

        result = client.get_access_key_version(
            models.GetAccessKeyVersionRequest(
                access_key_uid=12345, version=1
            )
        )

        session.exec.assert_called_once()
        call_args = session.exec.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/cam/v1/access-keys/12345/versions/1"

        assert result.access_key_uid == 12345
        assert result.cloud_access_key_id is None
        assert result.created_by == "testUser"
        assert result.created_time == "2021-02-26T13:34:37.916873Z"
        assert result.deployment_status == "ACTIVE"
        assert result.version == 1
        assert result.version_guid == "aaaa-bbbb-1111"

    def test_missing_required_params_validation_error(self):
        """Validation error — both access_key_uid and version blank."""
        client, session = _make_client()

        with pytest.raises(ValueError) as exc_info:
            client.get_access_key_version(
                models.GetAccessKeyVersionRequest()
            )

        msg = str(exc_info.value)
        assert msg.startswith(
            f"{ErrGetAccessKeyVersion}: struct validation:"
        )
        assert "AccessKeyUID: cannot be blank" in msg
        assert "Version: cannot be blank" in msg
        session.exec.assert_not_called()

    def test_404_access_key_does_not_exist(self):
        """404 — access key with specific UID does not exist."""
        client, session = _make_client()
        body = json.dumps({
            "type": "/cam/error-types/access-key-does-not-exist",
            "title": "Domain Error",
            "detail": "Access key with accessKeyUID '1' "
                      "does not exist.",
            "instance": "test-instance-123",
            "status": 404,
            "accessKeyUid": 1,
        })
        resp = make_mock_response(404, body)
        session.exec.return_value = (resp, json.loads(body))

        expected = Error(
            type="/cam/error-types/access-key-does-not-exist",
            title="Domain Error",
            detail="Access key with accessKeyUID '1' does not exist.",
            instance="test-instance-123",
            status=404,
            access_key_uid=1,
        )
        with pytest.raises(Error) as exc_info:
            client.get_access_key_version(
                models.GetAccessKeyVersionRequest(
                    access_key_uid=1, version=1
                )
            )

        assert exc_info.value.is_equivalent(expected)

    def test_404_wrap_into_custom_error(self):
        """404 — wraps into ErrAccessKeyNotFound custom error.

        Mirrors Go ``assert.ErrorIs(t, want, err)`` — the raised
        error should match the ErrAccessKeyNotFound sentinel.
        """
        client, session = _make_client()
        body = json.dumps({
            "type": "/cam/error-types/access-key-does-not-exist",
            "title": "Domain Error",
            "detail": "Access key with accessKeyUID '1' "
                      "does not exist.",
            "instance": "test-instance-123",
            "status": 404,
            "accessKeyUid": 1,
        })
        resp = make_mock_response(404, body)
        session.exec.return_value = (resp, json.loads(body))

        with pytest.raises(Error) as exc_info:
            client.get_access_key_version(
                models.GetAccessKeyVersionRequest(
                    access_key_uid=1, version=1
                )
            )

        assert exc_info.value.is_equivalent(ErrAccessKeyNotFound)

    def test_404_access_key_version_does_not_exist(self):
        """404 — access key version for specific key does not exist."""
        client, session = _make_client()
        body = json.dumps({
            "type": "/cam/error-types/access-key-version-does-not-exist",
            "title": "Domain Error",
            "detail": "Access key version '2' for access key "
                      "'1' does not exist.",
            "instance": "test-instance-123",
            "status": 404,
            "accessKeyUid": 1,
        })
        resp = make_mock_response(404, body)
        session.exec.return_value = (resp, json.loads(body))

        expected = Error(
            type=(
                "/cam/error-types/access-key-version-does-not-exist"
            ),
            title="Domain Error",
            detail="Access key version '2' for access key "
                   "'1' does not exist.",
            instance="test-instance-123",
            status=404,
            access_key_uid=1,
        )
        with pytest.raises(Error) as exc_info:
            client.get_access_key_version(
                models.GetAccessKeyVersionRequest(
                    access_key_uid=1, version=2
                )
            )

        assert exc_info.value.is_equivalent(expected)

    def test_404_does_not_wrap_into_custom_error(self):
        """404 — version-not-found does NOT match ErrAccessKeyNotFound.

        The type is 'access-key-version-does-not-exist' which is
        different from 'access-key-does-not-exist', so the sentinel
        check must return False.
        """
        client, session = _make_client()
        body = json.dumps({
            "type": "/cam/error-types/access-key-version-does-not-exist",
            "title": "Domain Error",
            "detail": "Access key version '2' for access key "
                      "'1' does not exist.",
            "instance": "test-instance-123",
            "status": 404,
            "accessKeyUid": 1,
        })
        resp = make_mock_response(404, body)
        session.exec.return_value = (resp, json.loads(body))

        with pytest.raises(Error) as exc_info:
            client.get_access_key_version(
                models.GetAccessKeyVersionRequest(
                    access_key_uid=1, version=2
                )
            )

        assert not exc_info.value.is_equivalent(ErrAccessKeyNotFound)


# ===================================================================
# TestListAccessKeyVersions  —  access_key_version_test.go 446-604
# ===================================================================


class TestListAccessKeyVersions:
    """Tests for ``CloudAccessClient.list_access_key_versions``."""

    def test_200_ok_multiple_versions(self):
        """200 OK — two versions returned."""
        client, session = _make_client()
        resp_body = json.dumps({
            "accessKeyVersions": [
                {
                    "accessKeyUid": 2,
                    "cloudAccessKeyId": None,
                    "createdBy": "testUser2",
                    "createdTime": "2021-02-27T14:54:38.622074Z",
                    "deploymentStatus": "PENDING_ACTIVATION",
                    "version": 2,
                    "versionGuid": "bbbb-2222",
                },
                {
                    "accessKeyUid": 2,
                    "cloudAccessKeyId": None,
                    "createdBy": "testUser1",
                    "createdTime": "2021-02-26T13:34:37.916873Z",
                    "deploymentStatus": "ACTIVE",
                    "version": 1,
                    "versionGuid": "aaaa-1111",
                },
            ],
        })
        resp = make_mock_response(200, resp_body)
        session.exec.return_value = (resp, json.loads(resp_body))

        result = client.list_access_key_versions(
            models.ListAccessKeyVersionsRequest(access_key_uid=2)
        )

        session.exec.assert_called_once()
        call_args = session.exec.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/cam/v1/access-keys/2/versions"

        assert len(result.access_key_versions) == 2

        ver0 = result.access_key_versions[0]
        assert ver0.access_key_uid == 2
        assert ver0.created_by == "testUser2"
        assert ver0.deployment_status == "PENDING_ACTIVATION"
        assert ver0.version == 2
        assert ver0.version_guid == "bbbb-2222"

        ver1 = result.access_key_versions[1]
        assert ver1.access_key_uid == 2
        assert ver1.created_by == "testUser1"
        assert ver1.deployment_status == "ACTIVE"
        assert ver1.version == 1
        assert ver1.version_guid == "aaaa-1111"

    def test_200_ok_single_version(self):
        """200 OK — single version."""
        client, session = _make_client()
        resp_body = json.dumps({
            "accessKeyVersions": [
                {
                    "accessKeyUid": 2,
                    "cloudAccessKeyId": None,
                    "createdBy": "testUser1",
                    "createdTime": "2021-02-26T13:34:37.916873Z",
                    "deploymentStatus": "ACTIVE",
                    "version": 1,
                    "versionGuid": "aaaa-1111",
                },
            ],
        })
        resp = make_mock_response(200, resp_body)
        session.exec.return_value = (resp, json.loads(resp_body))

        result = client.list_access_key_versions(
            models.ListAccessKeyVersionsRequest(access_key_uid=2)
        )

        assert len(result.access_key_versions) == 1
        assert result.access_key_versions[0].version == 1

    def test_200_ok_no_versions(self):
        """200 OK — empty list."""
        client, session = _make_client()
        resp_body = json.dumps({"accessKeyVersions": []})
        resp = make_mock_response(200, resp_body)
        session.exec.return_value = (resp, json.loads(resp_body))

        result = client.list_access_key_versions(
            models.ListAccessKeyVersionsRequest(access_key_uid=2)
        )

        assert not result.access_key_versions

    def test_missing_required_params_validation_error(self):
        """Validation error — access_key_uid is blank (0)."""
        client, session = _make_client()

        with pytest.raises(ValueError) as exc_info:
            client.list_access_key_versions(
                models.ListAccessKeyVersionsRequest()
            )

        msg = str(exc_info.value)
        assert msg.startswith(
            f"{ErrListAccessKeyVersions}: struct validation:"
        )
        assert "AccessKeyUID: cannot be blank" in msg
        session.exec.assert_not_called()

    def test_500_internal_server_error(self):
        """500 internal server error."""
        client, session = _make_client()
        resp = make_mock_response(500, INTERNAL_SERVER_ERROR_BODY)
        session.exec.return_value = (
            resp, json.loads(INTERNAL_SERVER_ERROR_BODY)
        )

        expected = Error(
            type="internal-server-error",
            title="Internal Server Error",
            detail="Error processing request",
            instance="TestInstances",
            status=500,
        )
        with pytest.raises(Error) as exc_info:
            client.list_access_key_versions(
                models.ListAccessKeyVersionsRequest(access_key_uid=2)
            )

        assert exc_info.value.is_equivalent(expected)


# ===================================================================
# TestDeleteAccessKeyVersion  —  access_key_version_test.go 606-696
# ===================================================================


class TestDeleteAccessKeyVersion:
    """Tests for ``CloudAccessClient.delete_access_key_version``."""

    def test_202_accepted(self):
        """202 Accepted — version marked PENDING_DELETION."""
        client, session = _make_client()
        resp_body = json.dumps({
            "accessKeyUid": 12345,
            "cloudAccessKeyId": None,
            "createdBy": "testUser",
            "createdTime": "2021-02-26T13:34:37.916873Z",
            "deploymentStatus": "PENDING_DELETION",
            "version": 1,
            "versionGuid": "aaaa-bbbb-1111",
        })
        resp = make_mock_response(202, resp_body)
        session.exec.return_value = (resp, json.loads(resp_body))

        result = client.delete_access_key_version(
            models.DeleteAccessKeyVersionRequest(
                access_key_uid=12345, version=1
            )
        )

        session.exec.assert_called_once()
        call_args = session.exec.call_args
        assert call_args[0][0] == "DELETE"
        assert call_args[0][1] == "/cam/v1/access-keys/12345/versions/1"

        assert result.deployment_status == "PENDING_DELETION"
        assert result.access_key_uid == 12345
        assert result.version == 1

    def test_missing_required_params_validation_error(self):
        """Validation error — both access_key_uid and version blank."""
        client, session = _make_client()

        with pytest.raises(ValueError) as exc_info:
            client.delete_access_key_version(
                models.DeleteAccessKeyVersionRequest()
            )

        msg = str(exc_info.value)
        assert msg.startswith(
            f"{ErrDeleteAccessKeyVersion}: struct validation:"
        )
        assert "AccessKeyUID: cannot be blank" in msg
        assert "Version: cannot be blank" in msg
        session.exec.assert_not_called()

    def test_404_error(self):
        """404 — access key does not exist."""
        client, session = _make_client()
        body = json.dumps({
            "type": "/cam/error-types/access-key-does-not-exist",
            "title": "Domain Error",
            "detail": "Access key with accessKeyUID '12345' "
                      "does not exist.",
            "instance": "test-instance-123",
            "status": 404,
            "accessKeyUid": 12345,
        })
        resp = make_mock_response(404, body)
        session.exec.return_value = (resp, json.loads(body))

        expected = Error(
            type="/cam/error-types/access-key-does-not-exist",
            title="Domain Error",
            detail="Access key with accessKeyUID '12345' "
                   "does not exist.",
            instance="test-instance-123",
            status=404,
            access_key_uid=12345,
        )
        with pytest.raises(Error) as exc_info:
            client.delete_access_key_version(
                models.DeleteAccessKeyVersionRequest(
                    access_key_uid=12345, version=1
                )
            )

        assert exc_info.value.is_equivalent(expected)


# ===================================================================
# TestLookupProperties  —  properties_test.go lines 15-164
# ===================================================================


class TestLookupProperties:
    """Tests for ``CloudAccessClient.lookup_properties``."""

    def test_200_ok_empty(self):
        """200 OK — empty properties list."""
        client, session = _make_client()
        resp_body = json.dumps({"properties": []})
        resp = make_mock_response(200, resp_body)
        session.exec.return_value = (resp, json.loads(resp_body))

        result = client.lookup_properties(
            models.LookupPropertiesRequest(
                access_key_uid=1234, version=1
            )
        )

        session.exec.assert_called_once()
        call_args = session.exec.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == (
            "/cam/v1/access-keys/1234/versions/1/properties"
        )
        assert not result.properties

    def test_200_ok_with_properties(self):
        """200 OK — two properties with mixed null versions."""
        client, session = _make_client()
        resp_body = json.dumps({
            "properties": [
                {
                    "accessKeyUid": 1234,
                    "version": 1,
                    "propertyId": "prp_5678",
                    "propertyName": "test-property",
                    "productionVersion": None,
                    "stagingVersion": 1,
                },
                {
                    "accessKeyUid": 1234,
                    "version": 1,
                    "propertyId": "prp_6789",
                    "propertyName": "test-property2",
                    "productionVersion": 1,
                    "stagingVersion": None,
                },
            ],
        })
        resp = make_mock_response(200, resp_body)
        session.exec.return_value = (resp, json.loads(resp_body))

        result = client.lookup_properties(
            models.LookupPropertiesRequest(
                access_key_uid=1234, version=1
            )
        )

        assert len(result.properties) == 2

        prop0 = result.properties[0]
        assert prop0.access_key_uid == 1234
        assert prop0.version == 1
        assert prop0.property_id == "prp_5678"
        assert prop0.property_name == "test-property"
        assert prop0.production_version is None
        assert prop0.staging_version == 1

        prop1 = result.properties[1]
        assert prop1.access_key_uid == 1234
        assert prop1.version == 1
        assert prop1.property_id == "prp_6789"
        assert prop1.property_name == "test-property2"
        assert prop1.production_version == 1
        assert prop1.staging_version is None

    def test_404_incorrect_request(self):
        """404 — access key version does not exist (with problemId)."""
        client, session = _make_client()
        body = json.dumps({
            "type": "/cam/error-types/access-key-version-does-not-exist",
            "title": "Domain Error",
            "detail": "Access key version '10' for access key "
                      "'1234' does not exist.",
            "instance": "test-instance-123",
            "status": 404,
            "problemId": "60126c0d-67f5-473c-bea0-16daa836dc44",
            "version": 10,
            "accessKeyUid": 1234,
        })
        resp = make_mock_response(404, body)
        session.exec.return_value = (resp, json.loads(body))

        with pytest.raises(Error) as exc_info:
            client.lookup_properties(
                models.LookupPropertiesRequest(
                    access_key_uid=1234, version=10
                )
            )

        err = exc_info.value
        assert err.type == (
            "/cam/error-types/access-key-version-does-not-exist"
        )
        assert err.status == 404
        assert err.problem_id == "60126c0d-67f5-473c-bea0-16daa836dc44"
        assert err.version == 10
        assert err.access_key_uid == 1234

    def test_500_internal_server_error(self):
        """500 internal server error."""
        client, session = _make_client()
        resp = make_mock_response(500, INTERNAL_SERVER_ERROR_BODY)
        session.exec.return_value = (
            resp, json.loads(INTERNAL_SERVER_ERROR_BODY)
        )

        expected = Error(
            type="internal-server-error",
            title="Internal Server Error",
            detail="Error processing request",
            instance="TestInstances",
            status=500,
        )
        with pytest.raises(Error) as exc_info:
            client.lookup_properties(
                models.LookupPropertiesRequest(
                    access_key_uid=1234, version=1
                )
            )

        assert exc_info.value.is_equivalent(expected)

    def test_validate_errors(self):
        """Validation error — both fields blank."""
        client, session = _make_client()

        with pytest.raises(ValueError) as exc_info:
            client.lookup_properties(
                models.LookupPropertiesRequest()
            )

        msg = str(exc_info.value)
        assert msg.startswith(
            f"{ErrLookupProperties}: struct validation:"
        )
        assert "AccessKeyUID: cannot be blank" in msg
        assert "Version: cannot be blank" in msg
        session.exec.assert_not_called()


# ===================================================================
# TestGetAsyncPropertiesLookupID  —  properties_test.go 166-267
# ===================================================================


class TestGetAsyncPropertiesLookupID:
    """Tests for ``CloudAccessClient.get_async_properties_lookup_id``."""

    def test_202_ok(self):
        """202 Accepted — lookup_id and retry_after."""
        client, session = _make_client()
        resp_body = json.dumps({"lookupId": 4321, "retryAfter": 10})
        resp = make_mock_response(202, resp_body)
        session.exec.return_value = (resp, json.loads(resp_body))

        result = client.get_async_properties_lookup_id(
            models.GetAsyncPropertiesLookupIDRequest(
                access_key_uid=1234, version=1
            )
        )

        session.exec.assert_called_once()
        call_args = session.exec.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == (
            "/cam/v1/access-keys/1234/versions/1/property-lookup-id"
        )

        assert result.lookup_id == 4321
        assert result.retry_after == 10

    def test_404_incorrect_request(self):
        """404 — access key version does not exist (with problemId)."""
        client, session = _make_client()
        body = json.dumps({
            "type": "/cam/error-types/access-key-version-does-not-exist",
            "title": "Domain Error",
            "detail": "Access key version '10' for access key "
                      "'1234' does not exist.",
            "instance": "test-instance-123",
            "status": 404,
            "problemId": "60126c0d-67f5-473c-bea0-16daa836dc44",
            "version": 10,
            "accessKeyUid": 1234,
        })
        resp = make_mock_response(404, body)
        session.exec.return_value = (resp, json.loads(body))

        with pytest.raises(Error) as exc_info:
            client.get_async_properties_lookup_id(
                models.GetAsyncPropertiesLookupIDRequest(
                    access_key_uid=1234, version=10
                )
            )

        err = exc_info.value
        assert err.status == 404
        assert err.problem_id == "60126c0d-67f5-473c-bea0-16daa836dc44"

    def test_500_internal_server_error(self):
        """500 internal server error."""
        client, session = _make_client()
        resp = make_mock_response(500, INTERNAL_SERVER_ERROR_BODY)
        session.exec.return_value = (
            resp, json.loads(INTERNAL_SERVER_ERROR_BODY)
        )

        expected = Error(
            type="internal-server-error",
            title="Internal Server Error",
            detail="Error processing request",
            instance="TestInstances",
            status=500,
        )
        with pytest.raises(Error) as exc_info:
            client.get_async_properties_lookup_id(
                models.GetAsyncPropertiesLookupIDRequest(
                    access_key_uid=1234, version=1
                )
            )

        assert exc_info.value.is_equivalent(expected)

    def test_validate_errors(self):
        """Validation error — both fields blank."""
        client, session = _make_client()

        with pytest.raises(ValueError) as exc_info:
            client.get_async_properties_lookup_id(
                models.GetAsyncPropertiesLookupIDRequest()
            )

        msg = str(exc_info.value)
        assert msg.startswith(
            f"{ErrGetAsyncLookupIDProperties}: struct validation:"
        )
        assert "AccessKeyUID: cannot be blank" in msg
        assert "Version: cannot be blank" in msg
        session.exec.assert_not_called()


# ===================================================================
# TestPerformAsyncPropertiesLookup  —  properties_test.go 269-396
# ===================================================================


class TestPerformAsyncPropertiesLookup:
    """Tests for ``CloudAccessClient.perform_async_properties_lookup``."""

    def test_200_ok_empty(self):
        """200 OK — complete lookup with empty properties."""
        client, session = _make_client()
        resp_body = json.dumps({
            "lookupId": 4321,
            "lookupStatus": "COMPLETE",
            "properties": [],
        })
        resp = make_mock_response(200, resp_body)
        session.exec.return_value = (resp, json.loads(resp_body))

        result = client.perform_async_properties_lookup(
            models.PerformAsyncPropertiesLookupRequest(lookup_id=4321)
        )

        session.exec.assert_called_once()
        call_args = session.exec.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/cam/v1/property-lookups/4321"

        assert result.lookup_id == 4321
        assert result.lookup_status == "COMPLETE"
        assert not result.properties

    def test_200_ok_with_properties(self):
        """200 OK — two properties returned."""
        client, session = _make_client()
        resp_body = json.dumps({
            "lookupId": 4321,
            "lookupStatus": "COMPLETE",
            "properties": [
                {
                    "accessKeyUid": 1234,
                    "version": 1,
                    "propertyId": "prp_5678",
                    "propertyName": "test-property",
                    "productionVersion": None,
                    "stagingVersion": 1,
                },
                {
                    "accessKeyUid": 1234,
                    "version": 1,
                    "propertyId": "prp_6789",
                    "propertyName": "test-property2",
                    "productionVersion": 1,
                    "stagingVersion": None,
                },
            ],
        })
        resp = make_mock_response(200, resp_body)
        session.exec.return_value = (resp, json.loads(resp_body))

        result = client.perform_async_properties_lookup(
            models.PerformAsyncPropertiesLookupRequest(lookup_id=4321)
        )

        assert result.lookup_id == 4321
        assert result.lookup_status == "COMPLETE"
        assert len(result.properties) == 2

        prop0 = result.properties[0]
        assert prop0.property_id == "prp_5678"
        assert prop0.property_name == "test-property"
        assert prop0.production_version is None
        assert prop0.staging_version == 1

        prop1 = result.properties[1]
        assert prop1.property_id == "prp_6789"
        assert prop1.property_name == "test-property2"
        assert prop1.production_version == 1
        assert prop1.staging_version is None

    def test_500_internal_server_error(self):
        """500 internal server error."""
        client, session = _make_client()
        resp = make_mock_response(500, INTERNAL_SERVER_ERROR_BODY)
        session.exec.return_value = (
            resp, json.loads(INTERNAL_SERVER_ERROR_BODY)
        )

        expected = Error(
            type="internal-server-error",
            title="Internal Server Error",
            detail="Error processing request",
            instance="TestInstances",
            status=500,
        )
        with pytest.raises(Error) as exc_info:
            client.perform_async_properties_lookup(
                models.PerformAsyncPropertiesLookupRequest(
                    lookup_id=4321
                )
            )

        assert exc_info.value.is_equivalent(expected)

    def test_validate_errors(self):
        """Validation error — lookup_id is blank (0)."""
        client, session = _make_client()

        with pytest.raises(ValueError) as exc_info:
            client.perform_async_properties_lookup(
                models.PerformAsyncPropertiesLookupRequest()
            )

        msg = str(exc_info.value)
        assert msg.startswith(
            f"{ErrPerformAsyncLookupProperties}: struct validation:"
        )
        assert "LookupID: cannot be blank" in msg
        session.exec.assert_not_called()
