"""Unit tests for the mTLS Key Store API client.

Mirrors ALL Go test scenarios from:
- pkg/mtlskeystore/client_certificates_test.go
- pkg/mtlskeystore/client_certificate_versions_test.go
- pkg/mtlskeystore/account_ca_certificates_test.go
- pkg/mtlskeystore/errors_test.go
- pkg/mtlskeystore/mtlskeystore_test.go

~68 total test scenarios.
"""
# pylint: disable=too-many-lines

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.session import Session
from akamai.edgegrid.mtlskeystore.mtlskeystore import (
    Client,
    statuses_to_query_string,
)
from akamai.edgegrid.mtlskeystore.models import (
    CertificateStatusCurrent,
    CertificateStatusExpired,
    CertificateStatusPrevious,
    CertificateStatusQualifying,
    CreateClientCertificateRequest,
    DeleteClientCertificateVersionRequest,
    GeographyChinaAndCore,
    GeographyCore,
    GetClientCertificateRequest,
    KeyAlgorithmRSA,
    ListAccountCACertificatesRequest,
    ListClientCertificateVersionsRequest,
    PatchClientCertificateRequest,
    PatchClientCertificateRequestBody,
    RotateClientCertificateVersionRequest,
    SecureNetworkEnhancedTLS,
    SecureNetworkStandardTLS,
    SignerAkamai,
    SignerThirdParty,
    UploadSignedClientCertificateRequest,
    UploadSignedClientCertificateRequestBody,
)
from akamai.edgegrid.mtlskeystore.errors import (
    Error,
    ErrClientCertificateNotFound,
    ErrInvalidClientCertificate,
    parse_error_response,
)
from akamai.edgegrid.mtlskeystore.test.conftest import (
    SERVER_ERROR_RESPONSE,
    create_mock_response,
)


# =====================================================================
# TestError — 5 scenarios (mirrors errors_test.go TestError)
# =====================================================================


class TestError:  # pylint: disable=too-few-public-methods
    """Tests for parse_error_response() — parsing HTTP error payloads."""

    @pytest.mark.parametrize(
        "status_code, body, expected",
        [
            (
                400,
                '{\n\t"type": "bad-request",\n\t"title": "Bad Request",'
                '\n\t"instance": "7a51100f-77ac-48dc-bd6b-ca6fcf7e820c",'
                '\n\t"status": 400,'
                '\n\t"detail": "Invalid value for field: groupId",'
                '\n\t"problemId": "7a51100f-77ac-48dc-bd6b-ca6fcf7e820c"\n}',
                Error(
                    title="Bad Request",
                    type="bad-request",
                    detail="Invalid value for field: groupId",
                    status=400,
                    problem_id="7a51100f-77ac-48dc-bd6b-ca6fcf7e820c",
                    instance="7a51100f-77ac-48dc-bd6b-ca6fcf7e820c",
                ),
            ),
            (
                400,
                '{\n\t"type": "bad-request",\n\t"title": "Bad Request",'
                '\n\t"instance": "6225f560-c2d0-4291-974e-cd8037547529",'
                '\n\t"status": 400,'
                '\n\t"detail": "Bad Request",'
                '\n\t"errors": [\n\t\t{\n\t\t\t"type": "error-types/invalid",'
                '\n\t\t\t"title": "Invalid Input",'
                '\n\t\t\t"detail": "Certificate with same name already exists.",'
                '\n\t\t\t"problemId": "d5621f91-e6dc-4b3b-ab37-f085826abc44",'
                '\n\t\t\t"field": "certificateName"\n\t\t}\n\t],'
                '\n\t"problemId": "514c5964-dd71-4f90-98fd-7972db559273"\n}',
                Error(
                    title="Bad Request",
                    type="bad-request",
                    detail="Bad Request",
                    status=400,
                    problem_id="514c5964-dd71-4f90-98fd-7972db559273",
                    instance="6225f560-c2d0-4291-974e-cd8037547529",
                    errors=[
                        Error(
                            title="Invalid Input",
                            type="error-types/invalid",
                            detail=(
                                "Certificate with same name "
                                "already exists."
                            ),
                            problem_id=(
                                "d5621f91-e6dc-4b3b-ab37-f085826abc44"
                            ),
                            field="certificateName",
                        ),
                    ],
                ),
            ),
            (
                404,
                '{\n\t"type": "resource-not-found",'
                '\n\t"title": "Resource Not Found",'
                '\n\t"instance": "a2aa0865-219e-4345-9b4d-44e035f7c246",'
                '\n\t"status": 404,'
                '\n\t"detail": "The requested resource could not be found'
                ' on the server.",'
                '\n\t"problemId": "8346a5d6-a339-4a5b-9dcf-33d482989c78",'
                '\n\t"field": "certificateId"\n}',
                Error(
                    title="Resource Not Found",
                    type="resource-not-found",
                    detail=(
                        "The requested resource could not be found"
                        " on the server."
                    ),
                    status=404,
                    problem_id="8346a5d6-a339-4a5b-9dcf-33d482989c78",
                    instance="a2aa0865-219e-4345-9b4d-44e035f7c246",
                    field="certificateId",
                ),
            ),
            (
                500,
                "test",
                Error(
                    title=(
                        "Failed to unmarshal error body. mTLS Keystore "
                        "API failed. Check details for more information."
                    ),
                    detail="test",
                    status=500,
                ),
            ),
            (
                500,
                "",
                Error(
                    title=(
                        "Failed to unmarshal error body. mTLS Keystore "
                        "API failed. Check details for more information."
                    ),
                    detail="",
                    status=500,
                ),
            ),
        ],
        ids=[
            "Bad request 400",
            "Bad request 400 - nested error",
            "Resource not found 404",
            "Invalid response body, assign status code",
            "Empty response body, assign status code",
        ],
    )
    def test_parse_error_response(
        self, status_code, body, expected
    ):
        """Verify parse_error_response parses HTTP error payloads."""
        response = create_mock_response(status_code, body)
        result = parse_error_response(response)
        assert result.type == expected.type
        assert result.title == expected.title
        assert result.detail == expected.detail
        assert result.status == expected.status
        assert result.problem_id == expected.problem_id
        assert result.instance == expected.instance
        assert result.field == expected.field
        if expected.errors:
            assert len(result.errors) == len(expected.errors)
            for res_err, exp_err in zip(result.errors, expected.errors):
                assert res_err.type == exp_err.type
                assert res_err.title == exp_err.title
                assert res_err.detail == exp_err.detail
                assert res_err.problem_id == exp_err.problem_id
                assert res_err.field == exp_err.field
        else:
            assert not result.errors


# =====================================================================
# TestErrorIs — 7 scenarios (mirrors errors_test.go TestErrorIs)
# =====================================================================


class TestErrorIs:  # pylint: disable=too-few-public-methods
    """Tests for Error.is_equivalent() — sentinel error matching."""

    @pytest.mark.parametrize(
        "err, target, expected",
        [
            (
                Error(status=404),
                None,
                False,
            ),
            (
                Error(status=404),
                ValueError("some error"),
                False,
            ),
            (
                Error(status=404),
                Error(status=404),
                True,
            ),
            (
                Error(status=404, detail="Not Found"),
                Error(status=404, detail="Different Detail"),
                False,
            ),
            (
                Error(status=404, detail="Not Found"),
                Error(status=500, detail="Internal Server Error"),
                False,
            ),
            (
                Error(status=404, detail="Not Found"),
                Error(status=404, detail="Not Found"),
                True,
            ),
            (
                Error(
                    status=404,
                    errors=[Error(status=400, detail="Nested Error")],
                ),
                Error(
                    status=404,
                    errors=[Error(status=400, detail="Nested Error")],
                ),
                True,
            ),
        ],
        ids=[
            "nil target",
            "target not of type Error",
            "both errors are the same instance",
            "same status, different details",
            "completely different errors",
            "same status and detail",
            "nested error comparison",
        ],
    )
    def test_error_is_equivalent(self, err, target, expected):
        """Verify Error.is_equivalent() matches Go Is() semantics."""
        assert err.is_equivalent(target) is expected


# =====================================================================
# TestClient — 2 scenarios (mirrors mtlskeystore_test.go TestClient)
# =====================================================================


class TestClient:
    """Tests for Client constructor."""

    def test_no_options_default(self):
        """Client(session) stores the session reference."""
        session = MagicMock(spec=Session)
        cli = Client(session)
        # pylint: disable=protected-access
        assert cli._session is session

    def test_none_session(self):
        """Client(None) stores None."""
        cli = Client(None)
        # pylint: disable=protected-access
        assert cli._session is None


# =====================================================================
# Helper: build a mock session that returns (response, parsed_json)
# =====================================================================


def _mock_exec_success(mock_session, status_code, body_str):
    """Configure mock_session.exec to return a success response.

    Parses *body_str* as JSON and wires mock_session.exec.return_value
    to ``(response, parsed_json)``.
    """
    resp = create_mock_response(status_code, body_str)
    parsed = json.loads(body_str) if body_str.strip() else None
    mock_session.exec.return_value = (resp, parsed)


def _mock_exec_error(mock_session, status_code, body_str):
    """Configure mock_session.exec to raise an Error (API error path).

    Builds an Error from the body and sets mock_session.exec.side_effect.
    """
    resp = create_mock_response(status_code, body_str)
    error = parse_error_response(resp)
    mock_session.exec.side_effect = error


# =====================================================================
# TestCreateClientCertificate — 9 scenarios
# =====================================================================


class TestCreateClientCertificate:
    """Tests for Client.create_client_certificate()."""

    # --- Response bodies (VERBATIM from Go test fixtures) ---

    RESPONSE_201_ALL = """{
    "certificateId": 1234,
    "certificateName": "test-certificate1",
    "createdBy": "jsmith",
    "createdDate": "2023-01-01T00:00:00Z",
    "geography": "CORE",
    "keyAlgorithm": "RSA",
    "notificationEmails": [
        "jsmith@akamai.com",
        "jkowalski@akamai.com"
    ],
    "secureNetwork": "STANDARD_TLS",
    "signer": "AKAMAI",
    "subject": "/C=US/O=Akamai Technologies, Inc./OU=123 test-contract 12345/CN=test-certificate1"
}"""

    RESPONSE_201_REQUIRED = """{
    "certificateId": 1234,
    "certificateName": "test-certificate1",
    "createdBy": "jsmith",
    "createdDate": "2023-01-01T00:00:00Z",
    "geography": "CHINA_AND_CORE",
    "keyAlgorithm": "RSA",
    "notificationEmails": [
        "jsmith@akamai.com",
        "jkowalski@akamai.com"
    ],
    "secureNetwork": "ENHANCED_TLS",
    "signer": "THIRD_PARTY",
    "subject": "/C=US/O=Akamai Technologies, Inc./OU=123 test-contract 12345/CN=test-certificate1"
}"""

    EXPECTED_BODY_ALL = {
        "certificateName": "test-certificate1",
        "contractId": "test-contract",
        "geography": "CORE",
        "groupId": 12345,
        "keyAlgorithm": "RSA",
        "notificationEmails": [
            "jsmith@akamai.com",
            "jkowalski@akamai.com",
        ],
        "preferredCa": "AKAMAI",
        "secureNetwork": "STANDARD_TLS",
        "signer": "AKAMAI",
        "subject": "CN=test-certificate1",
    }

    EXPECTED_BODY_REQUIRED = {
        "certificateName": "test-certificate1",
        "contractId": "test-contract",
        "geography": "CHINA_AND_CORE",
        "groupId": 12345,
        "notificationEmails": [
            "jsmith@akamai.com",
            "jkowalski@akamai.com",
        ],
        "secureNetwork": "ENHANCED_TLS",
        "signer": "THIRD_PARTY",
    }

    def test_201_created_all_params(self, mock_session, client):
        """201 Created — full request with all optional fields."""
        _mock_exec_success(mock_session, 201, self.RESPONSE_201_ALL)
        req = CreateClientCertificateRequest(
            certificate_name="test-certificate1",
            contract_id="test-contract",
            geography=GeographyCore,
            group_id=12345,
            key_algorithm=KeyAlgorithmRSA,
            notification_emails=[
                "jsmith@akamai.com",
                "jkowalski@akamai.com",
            ],
            preferred_ca="AKAMAI",
            secure_network=SecureNetworkStandardTLS,
            signer=SignerAkamai,
            subject="CN=test-certificate1",
        )
        result = client.create_client_certificate(req)
        assert result.certificate_id == 1234
        assert result.certificate_name == "test-certificate1"
        assert result.created_by == "jsmith"
        assert result.created_date == "2023-01-01T00:00:00Z"
        assert result.geography == "CORE"
        assert result.key_algorithm == "RSA"
        assert result.notification_emails == [
            "jsmith@akamai.com",
            "jkowalski@akamai.com",
        ]
        assert result.secure_network == "STANDARD_TLS"
        assert result.signer == "AKAMAI"
        assert result.subject == (
            "/C=US/O=Akamai Technologies, Inc."
            "/OU=123 test-contract 12345/CN=test-certificate1"
        )
        # Verify request was sent correctly
        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == (
            "/mtls-origin-keystore/v1/client-certificates"
        )
        sent_body = json.loads(call_args[1]["body"])
        assert sent_body == self.EXPECTED_BODY_ALL

    def test_201_created_required_only(self, mock_session, client):
        """201 Created — only required fields, no optional."""
        _mock_exec_success(mock_session, 201, self.RESPONSE_201_REQUIRED)
        req = CreateClientCertificateRequest(
            certificate_name="test-certificate1",
            contract_id="test-contract",
            geography=GeographyChinaAndCore,
            group_id=12345,
            notification_emails=[
                "jsmith@akamai.com",
                "jkowalski@akamai.com",
            ],
            secure_network=SecureNetworkEnhancedTLS,
            signer=SignerThirdParty,
        )
        result = client.create_client_certificate(req)
        assert result.certificate_id == 1234
        assert result.geography == "CHINA_AND_CORE"
        assert result.secure_network == "ENHANCED_TLS"
        assert result.signer == "THIRD_PARTY"
        # Verify request body
        call_args = mock_session.exec.call_args
        sent_body = json.loads(call_args[1]["body"])
        assert sent_body == self.EXPECTED_BODY_REQUIRED

    def test_validation_empty_request(self, client):
        """Validation: empty request — 7 required fields blank."""
        req = CreateClientCertificateRequest()
        with pytest.raises(ValueError) as exc_info:
            client.create_client_certificate(req)
        msg = str(exc_info.value)
        assert "create client certificate: struct validation:" in msg
        assert "CertificateName: cannot be blank" in msg
        assert "ContractID: cannot be blank" in msg
        assert "Geography: cannot be blank" in msg
        assert "GroupID: cannot be blank" in msg
        assert "NotificationEmails: cannot be blank" in msg
        assert "SecureNetwork: cannot be blank" in msg
        assert "Signer: cannot be blank" in msg

    def test_validation_incorrect_geography(self, client):
        """Validation: invalid geography value."""
        req = CreateClientCertificateRequest(
            certificate_name="test",
            contract_id="ctr",
            geography="test-geography",
            group_id=1,
            notification_emails=["a@b.com"],
            secure_network=SecureNetworkStandardTLS,
            signer=SignerAkamai,
        )
        with pytest.raises(ValueError) as exc_info:
            client.create_client_certificate(req)
        msg = str(exc_info.value)
        assert (
            "Geography: value 'test-geography' is invalid. "
            "Must be one of: 'CORE', 'RUSSIA_AND_CORE', 'CHINA_AND_CORE'"
        ) in msg

    def test_validation_incorrect_secure_network(self, client):
        """Validation: invalid secureNetwork value."""
        req = CreateClientCertificateRequest(
            certificate_name="test",
            contract_id="ctr",
            geography=GeographyCore,
            group_id=1,
            notification_emails=["a@b.com"],
            secure_network="test-secure-network",
            signer=SignerAkamai,
        )
        with pytest.raises(ValueError) as exc_info:
            client.create_client_certificate(req)
        msg = str(exc_info.value)
        assert (
            "SecureNetwork: value 'test-secure-network' is invalid. "
            "Must be one of: 'STANDARD_TLS', 'ENHANCED_TLS'"
        ) in msg

    def test_validation_incorrect_key_algorithm(self, client):
        """Validation: invalid keyAlgorithm value."""
        req = CreateClientCertificateRequest(
            certificate_name="test",
            contract_id="ctr",
            geography=GeographyCore,
            group_id=1,
            notification_emails=["a@b.com"],
            secure_network=SecureNetworkStandardTLS,
            signer=SignerAkamai,
            key_algorithm="test-key-algorithm",
        )
        with pytest.raises(ValueError) as exc_info:
            client.create_client_certificate(req)
        msg = str(exc_info.value)
        assert (
            "KeyAlgorithm: value 'test-key-algorithm' is invalid. "
            "Must be one of: 'RSA', 'ECDSA'"
        ) in msg

    def test_validation_incorrect_signer(self, client):
        """Validation: invalid signer value."""
        req = CreateClientCertificateRequest(
            certificate_name="test",
            contract_id="ctr",
            geography=GeographyCore,
            group_id=1,
            notification_emails=["a@b.com"],
            secure_network=SecureNetworkStandardTLS,
            signer="test-signer",
        )
        with pytest.raises(ValueError) as exc_info:
            client.create_client_certificate(req)
        msg = str(exc_info.value)
        assert (
            "Signer: value 'test-signer' is invalid. "
            "Must be one of: 'AKAMAI', 'THIRD_PARTY'"
        ) in msg

    def test_validation_preferred_ca_in_third_party(self, client):
        """Validation: preferredCA set with Signer=THIRD_PARTY."""
        req = CreateClientCertificateRequest(
            certificate_name="test",
            contract_id="ctr",
            geography=GeographyCore,
            group_id=1,
            notification_emails=["a@b.com"],
            secure_network=SecureNetworkStandardTLS,
            signer=SignerThirdParty,
            preferred_ca="AKAMAI",
        )
        with pytest.raises(ValueError) as exc_info:
            client.create_client_certificate(req)
        msg = str(exc_info.value)
        assert (
            "PreferredCA: preferredCA can only be set when "
            "Signer is 'AKAMAI', but got 'THIRD_PARTY'"
        ) in msg

    def test_500_internal_server_error(self, mock_session, client):
        """500 Internal Server Error — error parsed correctly."""
        _mock_exec_error(mock_session, 500, SERVER_ERROR_RESPONSE)
        req = CreateClientCertificateRequest(
            certificate_name="test-certificate1",
            contract_id="test-contract",
            geography=GeographyCore,
            group_id=12345,
            notification_emails=["jsmith@akamai.com"],
            secure_network=SecureNetworkStandardTLS,
            signer=SignerAkamai,
        )
        with pytest.raises(ValueError) as exc_info:
            client.create_client_certificate(req)
        cause = exc_info.value.__cause__
        assert isinstance(cause, Error)
        expected = Error(
            type="internal-server-error",
            title="Internal Server Error",
            detail="Error making request",
            instance="TestInstances",
            status=500,
        )
        assert cause.is_equivalent(expected)


# =====================================================================
# TestPatchClientCertificate — 10 scenarios
# =====================================================================

# Patch 404 response body (VERBATIM from Go)
PATCH_404_BODY = """{
\t"type": "not-found",
\t"title": "Not Found",
\t"detail": "Client certificate not found",
\t"instance": "TestInstances",
\t"status": 404
}"""


class TestPatchClientCertificate:
    """Tests for Client.patch_client_certificate()."""

    def test_200_ok_both_fields(self, mock_session, client):
        """200 OK — CertificateName and NotificationEmails."""
        _mock_exec_success(mock_session, 200, "{}")
        req = PatchClientCertificateRequest(
            certificate_id=1234,
            body=PatchClientCertificateRequestBody(
                certificate_name="test-certificate1",
                notification_emails=["jsmith@akamai.com"],
            ),
        )
        client.patch_client_certificate(req)
        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "PATCH"
        assert call_args[0][1] == (
            "/mtls-origin-keystore/v1/client-certificates/1234"
        )
        sent_body = json.loads(call_args[1]["body"])
        assert sent_body == {
            "certificateName": "test-certificate1",
            "notificationEmails": ["jsmith@akamai.com"],
        }

    def test_200_ok_certificate_name_only(self, mock_session, client):
        """200 OK — only CertificateName, nil NotificationEmails."""
        _mock_exec_success(mock_session, 200, "{}")
        req = PatchClientCertificateRequest(
            certificate_id=1234,
            body=PatchClientCertificateRequestBody(
                certificate_name="test-certificate1",
                notification_emails=None,
            ),
        )
        client.patch_client_certificate(req)
        sent_body = json.loads(
            mock_session.exec.call_args[1]["body"]
        )
        assert sent_body == {"certificateName": "test-certificate1"}

    def test_200_ok_notification_emails_only(
        self, mock_session, client
    ):
        """200 OK — only NotificationEmails, nil CertificateName."""
        _mock_exec_success(mock_session, 200, "{}")
        req = PatchClientCertificateRequest(
            certificate_id=1234,
            body=PatchClientCertificateRequestBody(
                certificate_name=None,
                notification_emails=["jsmith@akamai.com"],
            ),
        )
        client.patch_client_certificate(req)
        sent_body = json.loads(
            mock_session.exec.call_args[1]["body"]
        )
        assert sent_body == {
            "notificationEmails": ["jsmith@akamai.com"]
        }

    def test_validation_missing_certificate_id(self, client):
        """Validation: missing CertificateID."""
        req = PatchClientCertificateRequest(
            body=PatchClientCertificateRequestBody(
                certificate_name="test-certificate1",
                notification_emails=["jsmith@akamai.com"],
            ),
        )
        with pytest.raises(ValueError) as exc_info:
            client.patch_client_certificate(req)
        assert (
            "patch client certificate: struct validation: "
            "CertificateID: cannot be blank"
        ) == str(exc_info.value)

    def test_validation_empty_body(self, client):
        """Validation: empty request body — both fields missing."""
        req = PatchClientCertificateRequest(
            certificate_id=1234,
            body=PatchClientCertificateRequestBody(),
        )
        with pytest.raises(ValueError) as exc_info:
            client.patch_client_certificate(req)
        assert (
            "patch client certificate: struct validation: "
            "Body: CertificateName or NotificationEmails "
            "must be provided"
        ) == str(exc_info.value)

    def test_validation_nil_both_fields(self, client):
        """Validation: nil CertificateName and nil NotificationEmails."""
        req = PatchClientCertificateRequest(
            certificate_id=1234,
            body=PatchClientCertificateRequestBody(
                certificate_name=None,
                notification_emails=None,
            ),
        )
        with pytest.raises(ValueError) as exc_info:
            client.patch_client_certificate(req)
        assert (
            "patch client certificate: struct validation: "
            "Body: CertificateName or NotificationEmails "
            "must be provided"
        ) == str(exc_info.value)

    def test_validation_empty_certificate_name(self, client):
        """Validation: CertificateName is empty string."""
        req = PatchClientCertificateRequest(
            certificate_id=1234,
            body=PatchClientCertificateRequestBody(
                certificate_name="",
                notification_emails=None,
            ),
        )
        with pytest.raises(ValueError) as exc_info:
            client.patch_client_certificate(req)
        assert (
            "patch client certificate: struct validation: "
            "Body: {\n\tCertificateName: value is invalid\n}"
        ) == str(exc_info.value)

    def test_validation_certificate_name_too_long(self, client):
        """Validation: CertificateName longer than 64 characters."""
        long_name = (
            "test-certificate1-test-certificate1-"
            "test-certificate1-test-certificate1-"
            "test-certificate1"
        )
        req = PatchClientCertificateRequest(
            certificate_id=1234,
            body=PatchClientCertificateRequestBody(
                certificate_name=long_name,
                notification_emails=None,
            ),
        )
        with pytest.raises(ValueError) as exc_info:
            client.patch_client_certificate(req)
        assert (
            "patch client certificate: struct validation: "
            "Body: {\n\tCertificateName: value '" + long_name
            + "' is invalid. Must be between 1 and 64 characters\n}"
        ) == str(exc_info.value)

    def test_404_not_found(self, mock_session, client):
        """404 Not Found — error parsed and compared."""
        _mock_exec_error(mock_session, 404, PATCH_404_BODY)
        req = PatchClientCertificateRequest(
            certificate_id=1,
            body=PatchClientCertificateRequestBody(
                certificate_name="test-certificate1",
                notification_emails=None,
            ),
        )
        with pytest.raises(ValueError) as exc_info:
            client.patch_client_certificate(req)
        cause = exc_info.value.__cause__
        assert isinstance(cause, Error)
        expected = Error(
            type="not-found",
            title="Not Found",
            detail="Client certificate not found",
            instance="TestInstances",
            status=404,
        )
        assert cause.is_equivalent(expected)

    def test_500_internal_server_error(self, mock_session, client):
        """500 Internal Server Error — error parsed correctly."""
        _mock_exec_error(mock_session, 500, SERVER_ERROR_RESPONSE)
        req = PatchClientCertificateRequest(
            certificate_id=1234,
            body=PatchClientCertificateRequestBody(
                certificate_name="test-certificate1",
                notification_emails=["jsmith@akamai.com"],
            ),
        )
        with pytest.raises(ValueError) as exc_info:
            client.patch_client_certificate(req)
        cause = exc_info.value.__cause__
        assert isinstance(cause, Error)
        expected = Error(
            type="internal-server-error",
            title="Internal Server Error",
            detail="Error making request",
            instance="TestInstances",
            status=500,
        )
        assert cause.is_equivalent(expected)


# =====================================================================
# TestGetClientCertificate — 4 scenarios
# =====================================================================

# Get 404 response body (VERBATIM from Go)
GET_404_BODY = """{
\t"type": "not-found",
\t"title": "Not Found",
\t"detail": "Client certificate not found",
\t"instance": "TestInstances",
\t"status": 404
}"""

# Shared Get response body (VERBATIM from Go)
GET_RESPONSE_200 = """{
    "certificateId": 1234,
    "certificateName": "test-certificate1",
    "createdBy": "jsmith",
    "createdDate": "2023-01-01T00:00:00Z",
    "geography": "CORE",
    "keyAlgorithm": "RSA",
    "notificationEmails": [
        "jsmith@akamai.com",
        "jkowalski@akamai.com"
    ],
    "secureNetwork": "STANDARD_TLS",
    "signer": "AKAMAI",
    "subject": "/C=US/O=Akamai Technologies, Inc./OU=123 test-contract 12345/CN=test-certificate1"
}"""


class TestGetClientCertificate:
    """Tests for Client.get_client_certificate()."""

    def test_200_ok(self, mock_session, client):
        """200 OK — full certificate details returned."""
        _mock_exec_success(mock_session, 200, GET_RESPONSE_200)
        req = GetClientCertificateRequest(certificate_id=1234)
        result = client.get_client_certificate(req)
        assert result.certificate_id == 1234
        assert result.certificate_name == "test-certificate1"
        assert result.created_by == "jsmith"
        assert result.created_date == "2023-01-01T00:00:00Z"
        assert result.geography == "CORE"
        assert result.key_algorithm == "RSA"
        assert result.notification_emails == [
            "jsmith@akamai.com",
            "jkowalski@akamai.com",
        ]
        assert result.secure_network == "STANDARD_TLS"
        assert result.signer == "AKAMAI"
        assert result.subject == (
            "/C=US/O=Akamai Technologies, Inc."
            "/OU=123 test-contract 12345/CN=test-certificate1"
        )
        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == (
            "/mtls-origin-keystore/v1/client-certificates/1234"
        )

    def test_validation_error(self, client):
        """Validation: CertificateID is 0."""
        req = GetClientCertificateRequest(certificate_id=0)
        with pytest.raises(ValueError) as exc_info:
            client.get_client_certificate(req)
        assert (
            "get client certificate: struct validation: "
            "CertificateID: cannot be blank"
        ) == str(exc_info.value)

    def test_404_not_found(self, mock_session, client):
        """404 Not Found — error parsed and compared."""
        _mock_exec_error(mock_session, 404, GET_404_BODY)
        req = GetClientCertificateRequest(certificate_id=1)
        with pytest.raises(ValueError) as exc_info:
            client.get_client_certificate(req)
        cause = exc_info.value.__cause__
        assert isinstance(cause, Error)
        expected = Error(
            type="not-found",
            title="Not Found",
            detail="Client certificate not found",
            instance="TestInstances",
            status=404,
        )
        assert cause.is_equivalent(expected)

    def test_500_internal_server_error(self, mock_session, client):
        """500 Internal Server Error — error parsed correctly."""
        _mock_exec_error(mock_session, 500, SERVER_ERROR_RESPONSE)
        req = GetClientCertificateRequest(certificate_id=1234)
        with pytest.raises(ValueError) as exc_info:
            client.get_client_certificate(req)
        cause = exc_info.value.__cause__
        assert isinstance(cause, Error)
        expected = Error(
            type="internal-server-error",
            title="Internal Server Error",
            detail="Error making request",
            instance="TestInstances",
            status=500,
        )
        assert cause.is_equivalent(expected)


# =====================================================================
# TestListClientCertificates — 2 scenarios
# =====================================================================

# List response body (VERBATIM from Go)
LIST_CERTS_RESPONSE_200 = """{
    "certificates": [
        {
            "certificateId": 1234,
            "certificateName": "test-certificate1",
            "createdBy": "jsmith",
            "createdDate": "2023-01-01T00:00:00Z",
            "geography": "CORE",
            "keyAlgorithm": "RSA",
            "notificationEmails": [
                "jsmith@akamai.com",
                "jkowalski@akamai.com"
            ],
            "secureNetwork": "STANDARD_TLS",
            "signer": "AKAMAI",
            "subject": "/C=US/O=Akamai Technologies, Inc./OU=123 test-contract 12345/CN=test-certificate1"
        },
        {
            "certificateId": 12345,
            "certificateName": "test-certificate2",
            "createdBy": "jsmith",
            "createdDate": "2023-01-02T00:00:00Z",
            "geography": "CORE",
            "keyAlgorithm": "RSA",
            "notificationEmails": [
                "jsmith@akamai.com",
                "jkowalski@akamai.com"
            ],
            "secureNetwork": "STANDARD_TLS",
            "signer": "AKAMAI",
            "subject": "/C=US/O=Akamai Technologies, Inc./OU=123 test-contract 12345/CN=test-certificate2"
        }
    ]
}"""


class TestListClientCertificates:
    """Tests for Client.list_client_certificates()."""

    def test_200_ok(self, mock_session, client):
        """200 OK — 2 certificates in response."""
        _mock_exec_success(
            mock_session, 200, LIST_CERTS_RESPONSE_200
        )
        result = client.list_client_certificates()
        assert len(result.certificates) == 2

        cert1 = result.certificates[0]
        assert cert1.certificate_id == 1234
        assert cert1.certificate_name == "test-certificate1"
        assert cert1.created_by == "jsmith"
        assert cert1.created_date == "2023-01-01T00:00:00Z"
        assert cert1.geography == "CORE"
        assert cert1.key_algorithm == "RSA"
        assert cert1.secure_network == "STANDARD_TLS"
        assert cert1.signer == "AKAMAI"

        cert2 = result.certificates[1]
        assert cert2.certificate_id == 12345
        assert cert2.certificate_name == "test-certificate2"
        assert cert2.created_date == "2023-01-02T00:00:00Z"

        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == (
            "/mtls-origin-keystore/v1/client-certificates"
        )

    def test_500_internal_server_error(self, mock_session, client):
        """500 Internal Server Error — error parsed correctly."""
        _mock_exec_error(mock_session, 500, SERVER_ERROR_RESPONSE)
        with pytest.raises(ValueError) as exc_info:
            client.list_client_certificates()
        cause = exc_info.value.__cause__
        assert isinstance(cause, Error)
        expected = Error(
            type="internal-server-error",
            title="Internal Server Error",
            detail="Error making request",
            instance="TestInstances",
            status=500,
        )
        assert cause.is_equivalent(expected)


# =====================================================================
# Shared 404 body for version-related endpoints (VERBATIM from Go)
# =====================================================================

VERSIONS_404_BODY = """{
    "detail": "The requested resource could not be found on the server.",
    "field": "certificateId",
    "instance": "32be8a77-cc41-495e-94d8-cb536afea149",
    "problemId": "32be8a77-cc41-495e-94d8-cb536afea149",
    "status": 404,
    "title": "Resource Not Found",
    "type": "resource-not-found",
    "value": "180131"
}"""


# =====================================================================
# TestRotateClientCertificateVersion — 3 scenarios
# =====================================================================

# Rotate response body (VERBATIM from Go)
ROTATE_RESPONSE_201 = """{
    "certificateBlock": {
        "certificate": "",
        "keyAlgorithm": "RSA",
        "trustChain": ""
    },
    "createdBy": "jperez",
    "createdDate": "2024-03-08T10:26:30Z",
    "csrBlock": {
        "csr": "-----BEGIN CERTIFICATE REQUEST-----...-----END CERTIFICATE REQUEST-----",
        "keyAlgorithm": "RSA"
    },
    "issuedDate": null,
    "expiryDate": null,
    "issuer": "1360 Account CA G366",
    "keyAlgorithm": "RSA",
    "keySizeInBytes": "2048",
    "signatureAlgorithm": "SHA256_WITH_RSA",
    "status": "DEPLOYMENT_PENDING",
    "subject": "/C=US/O=Akamai Technologies/OU=KMI/CN=/",
    "validation": {
        "errors": [],
        "warnings": []
    },
    "version": 4,
    "versionGuid": "13d16e57-22fa-4475-af0a-b2b745115128"
}"""


class TestRotateClientCertificateVersion:
    """Tests for Client.rotate_client_certificate_version()."""

    def test_201_successful(self, mock_session, client):
        """201 — Successful rotate client certificate version."""
        _mock_exec_success(mock_session, 201, ROTATE_RESPONSE_201)
        req = RotateClientCertificateVersionRequest(
            certificate_id=123,
        )
        result = client.rotate_client_certificate_version(req)
        assert result.version == 4
        assert result.version_guid == (
            "13d16e57-22fa-4475-af0a-b2b745115128"
        )
        assert result.certificate_block is not None
        assert result.certificate_block.certificate == ""
        assert result.certificate_block.key_algorithm == "RSA"
        assert result.certificate_block.trust_chain == ""
        assert result.created_by == "jperez"
        assert result.created_date == "2024-03-08T10:26:30Z"
        assert result.csr_block is not None
        assert result.csr_block.csr == (
            "-----BEGIN CERTIFICATE REQUEST-----"
            "...-----END CERTIFICATE REQUEST-----"
        )
        assert result.csr_block.key_algorithm == "RSA"
        assert result.issued_date is None
        assert result.expiry_date is None
        assert result.issuer == "1360 Account CA G366"
        assert result.key_algorithm == "RSA"
        assert result.key_size_in_bytes == "2048"
        assert result.signature_algorithm == "SHA256_WITH_RSA"
        assert result.status == "DEPLOYMENT_PENDING"
        assert result.subject == (
            "/C=US/O=Akamai Technologies/OU=KMI/CN=/"
        )
        # Verify request
        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == (
            "/mtls-origin-keystore/v1/client-certificates"
            "/123/versions"
        )

    def test_validation_missing_certificate_id(self, client):
        """Validation: CertificateID cannot be blank."""
        req = RotateClientCertificateVersionRequest()
        with pytest.raises(ValueError) as exc_info:
            client.rotate_client_certificate_version(req)
        assert (
            "rotating client certificate version: "
            "validation failed: CertificateID: cannot be blank"
        ) == str(exc_info.value)

    def test_404_not_found(self, mock_session, client):
        """404 — Client Certificate not found."""
        _mock_exec_error(mock_session, 404, VERSIONS_404_BODY)
        req = RotateClientCertificateVersionRequest(
            certificate_id=123,
        )
        with pytest.raises(ValueError) as exc_info:
            client.rotate_client_certificate_version(req)
        cause = exc_info.value.__cause__
        assert isinstance(cause, Error)
        assert cause.is_equivalent(ErrClientCertificateNotFound)


# =====================================================================
# TestGetClientCertificateVersions (ListVersions) — 4 scenarios
# =====================================================================

# ListVersions response body (VERBATIM from Go)
LIST_VERSIONS_RESPONSE_200 = """{
    "versions": [
        {
            "certificateBlock": {
                "certificate": "",
                "keyAlgorithm": "RSA",
                "trustChain": ""
            },
            "createdBy": "jperez",
            "createdDate": "2024-03-08T10:26:30Z",
            "csrBlock": {
                "csr": "-----BEGIN CERTIFICATE REQUEST-----...-----END CERTIFICATE REQUEST-----",
                "keyAlgorithm": "RSA"
            },
            "issuedDate": null,
            "expiryDate": null,
            "issuer": "1360 Account CA G366",
            "keyAlgorithm": "RSA",
            "keySizeInBytes": "2048",
            "signatureAlgorithm": "SHA256_WITH_RSA",
            "status": "DEPLOYMENT_PENDING",
            "subject": "/C=US/O=Akamai Technologies/OU=KMI/CN=/",
            "validation": {
                "errors": [],
                "warnings": []
            },
            "version": 4,
            "versionGuid": "13d16e57-22fa-4475-af0a-b2b745115128"
        }
    ]
}"""

# ListVersions with properties response body (VERBATIM from Go)
LIST_VERSIONS_WITH_PROPS_RESPONSE_200 = """{
    "versions": [
        {
            "certificateBlock": {
                "certificate": "",
                "keyAlgorithm": "RSA",
                "trustChain": ""
            },
            "createdBy": "jperez",
            "createdDate": "2024-03-08T10:26:30Z",
            "csrBlock": {
                "csr": "-----BEGIN CERTIFICATE REQUEST-----...-----END CERTIFICATE REQUEST-----",
                "keyAlgorithm": "RSA"
            },
            "issuedDate": null,
            "expiryDate": null,
            "issuer": "1360 Account CA G366",
            "keyAlgorithm": "RSA",
            "keySizeInBytes": "2048",
            "signatureAlgorithm": "SHA256_WITH_RSA",
            "status": "DEPLOYMENT_PENDING",
            "subject": "/C=US/O=Akamai Technologies/OU=KMI/CN=/",
            "validation": {
                "errors": [],
                "warnings": []
            },
            "version": 4,
            "versionGuid": "13d16e57-22fa-4475-af0a-b2b745115128",
            "properties": [
                {
                    "assetId": 111111,
                    "groupId": 222222,
                    "propertyName": "propertyName",
                    "propertyVersion": 3
                }
            ]
        }
    ]
}"""


class TestListClientCertificateVersions:
    """Tests for Client.list_client_certificate_versions()."""

    def test_200_successful(self, mock_session, client):
        """200 — Successful get client certificate versions."""
        _mock_exec_success(
            mock_session, 200, LIST_VERSIONS_RESPONSE_200
        )
        req = ListClientCertificateVersionsRequest(
            certificate_id=123,
        )
        result = client.list_client_certificate_versions(req)
        assert len(result.versions) == 1
        ver = result.versions[0]
        assert ver.version == 4
        assert ver.version_guid == (
            "13d16e57-22fa-4475-af0a-b2b745115128"
        )
        assert ver.certificate_block is not None
        assert ver.certificate_block.certificate == ""
        assert ver.certificate_block.key_algorithm == "RSA"
        assert ver.created_by == "jperez"
        assert ver.created_date == "2024-03-08T10:26:30Z"
        assert ver.csr_block is not None
        assert ver.csr_block.csr == (
            "-----BEGIN CERTIFICATE REQUEST-----"
            "...-----END CERTIFICATE REQUEST-----"
        )
        assert ver.issued_date is None
        assert ver.expiry_date is None
        assert ver.issuer == "1360 Account CA G366"
        assert ver.key_algorithm == "RSA"
        assert ver.key_size_in_bytes == "2048"
        assert ver.signature_algorithm == "SHA256_WITH_RSA"
        assert ver.status == "DEPLOYMENT_PENDING"
        assert ver.subject == (
            "/C=US/O=Akamai Technologies/OU=KMI/CN=/"
        )
        assert ver.validation.errors == []
        assert ver.validation.warnings == []
        assert ver.associated_properties == []
        # Verify path has NO query params
        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == (
            "/mtls-origin-keystore/v1/client-certificates"
            "/123/versions"
        )

    def test_200_with_associated_properties(
        self, mock_session, client
    ):
        """200 — with includeAssociatedProperties=true."""
        _mock_exec_success(
            mock_session, 200,
            LIST_VERSIONS_WITH_PROPS_RESPONSE_200,
        )
        req = ListClientCertificateVersionsRequest(
            certificate_id=123,
            include_associated_properties=True,
        )
        result = client.list_client_certificate_versions(req)
        assert len(result.versions) == 1
        ver = result.versions[0]
        assert len(ver.associated_properties) == 1
        prop = ver.associated_properties[0]
        assert prop.asset_id == 111111
        assert prop.group_id == 222222
        assert prop.property_name == "propertyName"
        assert prop.property_version == 3
        # Verify query param
        call_args = mock_session.exec.call_args
        assert call_args[1].get("params") == {
            "includeAssociatedProperties": "true"
        }

    def test_validation_missing_certificate_id(self, client):
        """Validation: CertificateID cannot be blank."""
        req = ListClientCertificateVersionsRequest()
        with pytest.raises(ValueError) as exc_info:
            client.list_client_certificate_versions(req)
        assert (
            "fetching client certificate versions: "
            "validation failed: CertificateID: cannot be blank"
        ) == str(exc_info.value)

    def test_404_not_found(self, mock_session, client):
        """404 — Client Certificate not found."""
        _mock_exec_error(mock_session, 404, VERSIONS_404_BODY)
        req = ListClientCertificateVersionsRequest(
            certificate_id=123,
        )
        with pytest.raises(ValueError) as exc_info:
            client.list_client_certificate_versions(req)
        cause = exc_info.value.__cause__
        assert isinstance(cause, Error)
        assert cause.is_equivalent(ErrClientCertificateNotFound)


# =====================================================================
# TestDeleteClientCertificateVersion — 5 scenarios
# =====================================================================

# Delete 202 response body (VERBATIM from Go)
DELETE_RESPONSE_202 = """{
    "message": "It's being scheduled to delete on 2024-05-10T00:00:00Z. The delete request will be cancelled automatically if it is used again in any delivery configuration."
}"""


class TestDeleteClientCertificateVersion:
    """Tests for Client.delete_client_certificate_version()."""

    def test_202_accepted(self, mock_session, client):
        """202 — Successful submitted deletion request."""
        _mock_exec_success(mock_session, 202, DELETE_RESPONSE_202)
        req = DeleteClientCertificateVersionRequest(
            certificate_id=123,
            version=1,
        )
        result = client.delete_client_certificate_version(req)
        assert result is not None
        assert result.message == (
            "It's being scheduled to delete on "
            "2024-05-10T00:00:00Z. The delete request will be "
            "cancelled automatically if it is used again in any "
            "delivery configuration."
        )
        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "DELETE"
        assert call_args[0][1] == (
            "/mtls-origin-keystore/v1/client-certificates"
            "/123/versions/1"
        )

    def test_204_no_content(self, mock_session, client):
        """204 — Successful deletion, returns None."""
        resp = create_mock_response(204, "")
        mock_session.exec.return_value = (resp, None)
        req = DeleteClientCertificateVersionRequest(
            certificate_id=123,
            version=1,
        )
        result = client.delete_client_certificate_version(req)
        assert result is None

    def test_validation_missing_certificate_id(self, client):
        """Validation: missing CertificateID."""
        req = DeleteClientCertificateVersionRequest(version=1)
        with pytest.raises(ValueError) as exc_info:
            client.delete_client_certificate_version(req)
        assert (
            "deleting client certificate version: "
            "validation failed: CertificateID: cannot be blank"
        ) == str(exc_info.value)

    def test_validation_missing_version(self, client):
        """Validation: missing Version."""
        req = DeleteClientCertificateVersionRequest(
            certificate_id=123,
        )
        with pytest.raises(ValueError) as exc_info:
            client.delete_client_certificate_version(req)
        assert (
            "deleting client certificate version: "
            "validation failed: Version: cannot be blank"
        ) == str(exc_info.value)

    def test_404_not_found(self, mock_session, client):
        """404 — Client Certificate not found."""
        _mock_exec_error(mock_session, 404, VERSIONS_404_BODY)
        req = DeleteClientCertificateVersionRequest(
            certificate_id=123,
            version=1,
        )
        with pytest.raises(ValueError) as exc_info:
            client.delete_client_certificate_version(req)
        cause = exc_info.value.__cause__
        assert isinstance(cause, Error)
        assert cause.is_equivalent(ErrClientCertificateNotFound)


# =====================================================================
# TestUploadClientCertificateVersion — 9 scenarios
# =====================================================================

# Upload 400 Duplicate error body (VERBATIM from Go)
UPLOAD_400_DUPLICATE_BODY = """{
    "detail": "Bad Request",
    "errors": [
        {
            "detail": "Certificate with same name already exists.",
            "field": "certificateName",
            "problemId": "00c4e7b5-dc7b-43f9-9f18-de8de3c82527",
            "title": "Invalid Input",
            "type": "error-types/invalid"
        }
    ],
    "instance": "/f311c60f-9914-4e23-be2c-db8dbb711a8a",
    "status": 400,
    "title": "Bad Request",
    "type": "bad-request"
}"""

# Upload 400 Invalid error body (VERBATIM from Go)
UPLOAD_400_INVALID_BODY = """{
    "detail": "Bad Request",
    "errors": [
        {
            "detail": "Certificate is either invalid or cannot not be accepted.",
            "field": "certificate",
            "problemId": "f1658521-6e7d-4051-89e6-5dce765029af",
            "title": "Invalid Input",
            "type": "error-types/invalid"
        }
    ],
    "instance": "7cc378a1-ba9e-41a6-8255-27ee0a5a3897",
    "problemId": "7cc378a1-ba9e-41a6-8255-27ee0a5a3897",
    "status": 400,
    "title": "Bad Request",
    "type": "bad-request"
}"""

CERT_PEM = "-----BEGIN CERTIFICATE-----....-----END CERTIFICATE-----"


class TestUploadClientCertificateVersion:
    """Tests for Client.upload_signed_client_certificate()."""

    def test_200_successful(self, mock_session, client):
        """200 — Successful upload of a signed client certificate."""
        _mock_exec_success(mock_session, 200, "{}")
        req = UploadSignedClientCertificateRequest(
            certificate_id=123,
            version=1,
            body=UploadSignedClientCertificateRequestBody(
                certificate=CERT_PEM,
            ),
        )
        client.upload_signed_client_certificate(req)
        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == (
            "/mtls-origin-keystore/v1/client-certificates"
            "/123/versions/1/certificate-block"
        )
        sent_body = json.loads(call_args[1]["body"])
        assert sent_body == {"certificate": CERT_PEM}

    def test_validation_missing_certificate_id(self, client):
        """Validation: missing CertificateID."""
        req = UploadSignedClientCertificateRequest(
            version=1,
            body=UploadSignedClientCertificateRequestBody(
                certificate=CERT_PEM,
            ),
        )
        with pytest.raises(ValueError) as exc_info:
            client.upload_signed_client_certificate(req)
        assert (
            "uploading client certificate version: "
            "validation failed: CertificateID: cannot be blank"
        ) == str(exc_info.value)

    def test_validation_missing_version_and_certificate(self, client):
        """Validation: missing Version and Certificate."""
        req = UploadSignedClientCertificateRequest(
            certificate_id=123,
        )
        with pytest.raises(ValueError) as exc_info:
            client.upload_signed_client_certificate(req)
        msg = str(exc_info.value)
        assert "uploading client certificate version:" in msg
        assert "validation failed:" in msg
        assert "Body: {\n\tCertificate: cannot be blank\n}" in msg
        assert "Version: cannot be blank" in msg

    def test_validation_missing_certificate(self, client):
        """Validation: Version provided, missing Certificate."""
        req = UploadSignedClientCertificateRequest(
            certificate_id=123,
            version=1,
        )
        with pytest.raises(ValueError) as exc_info:
            client.upload_signed_client_certificate(req)
        assert (
            "uploading client certificate version: "
            "validation failed: "
            "Body: {\n\tCertificate: cannot be blank\n}"
        ) == str(exc_info.value)

    def test_validation_empty_certificate(self, client):
        """Validation: Certificate is empty string."""
        req = UploadSignedClientCertificateRequest(
            certificate_id=123,
            version=1,
            body=UploadSignedClientCertificateRequestBody(
                certificate="",
            ),
        )
        with pytest.raises(ValueError) as exc_info:
            client.upload_signed_client_certificate(req)
        assert (
            "uploading client certificate version: "
            "validation failed: "
            "Body: {\n\tCertificate: cannot be blank\n}"
        ) == str(exc_info.value)

    def test_validation_empty_trust_chain(self, client):
        """Validation: TrustChain is empty string."""
        req = UploadSignedClientCertificateRequest(
            certificate_id=123,
            version=1,
            body=UploadSignedClientCertificateRequestBody(
                certificate=CERT_PEM,
                trust_chain="",
            ),
        )
        with pytest.raises(ValueError) as exc_info:
            client.upload_signed_client_certificate(req)
        assert (
            "uploading client certificate version: "
            "validation failed: "
            "Body: {\n\tTrustChain: cannot be blank\n}"
        ) == str(exc_info.value)

    def test_404_not_found(self, mock_session, client):
        """404 — Client Certificate not found."""
        _mock_exec_error(mock_session, 404, VERSIONS_404_BODY)
        req = UploadSignedClientCertificateRequest(
            certificate_id=123,
            version=1,
            body=UploadSignedClientCertificateRequestBody(
                certificate=CERT_PEM,
                trust_chain=CERT_PEM,
            ),
        )
        with pytest.raises(ValueError) as exc_info:
            client.upload_signed_client_certificate(req)
        cause = exc_info.value.__cause__
        assert isinstance(cause, Error)
        assert cause.is_equivalent(ErrClientCertificateNotFound)

    def test_400_duplicate_certificate(self, mock_session, client):
        """400 — Duplicate Certificate name."""
        _mock_exec_error(
            mock_session, 400, UPLOAD_400_DUPLICATE_BODY
        )
        req = UploadSignedClientCertificateRequest(
            certificate_id=123,
            version=1,
            body=UploadSignedClientCertificateRequestBody(
                certificate=CERT_PEM,
                trust_chain=CERT_PEM,
            ),
        )
        with pytest.raises(ValueError) as exc_info:
            client.upload_signed_client_certificate(req)
        cause = exc_info.value.__cause__
        assert isinstance(cause, Error)
        assert cause.is_equivalent(ErrInvalidClientCertificate)

    def test_400_invalid_certificate(self, mock_session, client):
        """400 — Client Certificate is invalid."""
        _mock_exec_error(
            mock_session, 400, UPLOAD_400_INVALID_BODY
        )
        req = UploadSignedClientCertificateRequest(
            certificate_id=123,
            version=1,
            body=UploadSignedClientCertificateRequestBody(
                certificate=CERT_PEM,
                trust_chain=CERT_PEM,
            ),
        )
        with pytest.raises(ValueError) as exc_info:
            client.upload_signed_client_certificate(req)
        cause = exc_info.value.__cause__
        assert isinstance(cause, Error)
        assert cause.is_equivalent(ErrInvalidClientCertificate)


# =====================================================================
# TestListAccountCACertificates — 5 scenarios
# =====================================================================

# 200 OK - multiple entries, no query param (VERBATIM from Go)
LIST_ACCOUNT_CA_RESPONSE_200_MULTI = """{
    "certificates": [
        {
            "accountId": "test_account",
            "certificate": "-----BEGIN CERTIFICATE-----\\nCERTIFICATE CONTENT\\n-----END CERTIFICATE-----\\n",
            "commonName": "Test Common Name",
            "createdBy": "Test User",
            "createdDate": "2025-03-24T15:43:50Z",
            "expiryDate": "2028-03-24T15:46:06Z",
            "id": 1,
            "issuedDate": "2025-03-24T15:46:06Z",
            "keyAlgorithm": "RSA",
            "keySizeInBytes": 4096,
            "signatureAlgorithm": "SHA256_WITH_RSA",
            "status": "CURRENT",
            "subject": "/C=Test Country/O=Test Organization, Inc./OU=Test Organization Unit/CN=Test Common Name/",
            "version": 1
        },
        {
            "accountId": "test_account",
            "certificate": "-----BEGIN CERTIFICATE-----\\nCERTIFICATE CONTENT\\n-----END CERTIFICATE-----\\n",
            "commonName": "Test Common Name",
            "createdBy": "Test User",
            "createdDate": "2025-03-24T15:43:50Z",
            "expiryDate": "2028-03-24T15:46:06Z",
            "id": 2,
            "issuedDate": "2025-03-24T15:46:06Z",
            "keyAlgorithm": "RSA",
            "keySizeInBytes": 4096,
            "signatureAlgorithm": "SHA256_WITH_RSA",
            "status": "EXPIRED",
            "subject": "/C=Test Country/O=Test Organization, Inc./OU=Test Organization Unit/CN=Test Common Name/",
            "version": 2
        },
        {
            "accountId": "test_account",
            "certificate": "-----BEGIN CERTIFICATE-----\\nCERTIFICATE CONTENT\\n-----END CERTIFICATE-----\\n",
            "commonName": "Test Common Name",
            "createdBy": "Test User",
            "createdDate": "2025-03-24T15:43:50Z",
            "expiryDate": "2028-03-24T15:46:06Z",
            "id": 3,
            "issuedDate": "2025-03-24T15:46:06Z",
            "keyAlgorithm": "RSA",
            "keySizeInBytes": 4096,
            "qualificationDate": "2025-03-25T15:46:06Z",
            "signatureAlgorithm": "SHA256_WITH_RSA",
            "status": "CURRENT",
            "subject": "/C=Test Country/O=Test Organization, Inc./OU=Test Organization Unit/CN=Test Common Name/",
            "version": 3
        }
    ]
}"""

# 200 OK - single entry with query param (VERBATIM from Go)
LIST_ACCOUNT_CA_RESPONSE_200_SINGLE = """{
    "certificates": [
        {
            "accountId": "test_account",
            "certificate": "-----BEGIN CERTIFICATE-----\\nCERTIFICATE CONTENT\\n-----END CERTIFICATE-----\\n",
            "commonName": "Test Common Name",
            "createdBy": "Test User",
            "createdDate": "2025-03-24T15:43:50Z",
            "expiryDate": "2028-03-24T15:46:06Z",
            "id": 1,
            "issuedDate": "2025-03-24T15:46:06Z",
            "keyAlgorithm": "RSA",
            "keySizeInBytes": 4096,
            "signatureAlgorithm": "SHA256_WITH_RSA",
            "status": "CURRENT",
            "subject": "/C=Test Country/O=Test Organization, Inc./OU=Test Organization Unit/CN=Test Common Name/",
            "version": 1
        },
        {
            "accountId": "test_account",
            "certificate": "-----BEGIN CERTIFICATE-----\\nCERTIFICATE CONTENT\\n-----END CERTIFICATE-----\\n",
            "commonName": "Test Common Name",
            "createdBy": "Test User",
            "createdDate": "2025-03-24T15:43:50Z",
            "expiryDate": "2028-03-24T15:46:06Z",
            "id": 3,
            "issuedDate": "2025-03-24T15:46:06Z",
            "keyAlgorithm": "RSA",
            "keySizeInBytes": 4096,
            "qualificationDate": "2025-03-25T15:46:06Z",
            "signatureAlgorithm": "SHA256_WITH_RSA",
            "status": "CURRENT",
            "subject": "/C=Test Country/O=Test Organization, Inc./OU=Test Organization Unit/CN=Test Common Name/",
            "version": 3
        }
    ]
}"""

# 200 OK - no entries (VERBATIM from Go)
LIST_ACCOUNT_CA_RESPONSE_200_EMPTY = """{
    "certificates": []
}"""


class TestListAccountCACertificates:
    """Tests for Client.list_account_ca_certificates()."""

    def _assert_common_ca_fields(self, cert):
        """Verify fields shared by all test CA certificates."""
        assert cert.account_id == "test_account"
        assert cert.certificate == (
            "-----BEGIN CERTIFICATE-----\n"
            "CERTIFICATE CONTENT\n"
            "-----END CERTIFICATE-----\n"
        )
        assert cert.common_name == "Test Common Name"
        assert cert.created_by == "Test User"
        assert cert.created_date == "2025-03-24T15:43:50Z"
        assert cert.expiry_date == "2028-03-24T15:46:06Z"
        assert cert.issued_date == "2025-03-24T15:46:06Z"
        assert cert.key_algorithm == "RSA"
        assert cert.key_size_in_bytes == 4096
        assert cert.signature_algorithm == "SHA256_WITH_RSA"
        assert cert.subject == (
            "/C=Test Country/O=Test Organization, Inc."
            "/OU=Test Organization Unit/CN=Test Common Name/"
        )

    def test_200_multiple_no_query(self, mock_session, client):
        """200 OK — multiple entries, no status filter."""
        _mock_exec_success(
            mock_session, 200,
            LIST_ACCOUNT_CA_RESPONSE_200_MULTI,
        )
        req = ListAccountCACertificatesRequest()
        result = client.list_account_ca_certificates(req)
        assert len(result.certificates) == 3

        c1 = result.certificates[0]
        self._assert_common_ca_fields(c1)
        assert c1.id == 1
        assert c1.version == 1
        assert c1.status == "CURRENT"
        assert c1.qualification_date is None

        c2 = result.certificates[1]
        self._assert_common_ca_fields(c2)
        assert c2.id == 2
        assert c2.version == 2
        assert c2.status == "EXPIRED"
        assert c2.qualification_date is None

        c3 = result.certificates[2]
        self._assert_common_ca_fields(c3)
        assert c3.id == 3
        assert c3.version == 3
        assert c3.status == "CURRENT"
        assert c3.qualification_date == (
            "2025-03-25T15:46:06Z"
        )

        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == (
            "/mtls-origin-keystore/v1/ca-certificates"
        )

    def test_200_single_with_query(self, mock_session, client):
        """200 OK — single entry with status=CURRENT."""
        _mock_exec_success(
            mock_session, 200,
            LIST_ACCOUNT_CA_RESPONSE_200_SINGLE,
        )
        req = ListAccountCACertificatesRequest(
            status=[CertificateStatusCurrent],
        )
        result = client.list_account_ca_certificates(req)
        assert len(result.certificates) == 2

        c1 = result.certificates[0]
        assert c1.id == 1
        assert c1.status == "CURRENT"

        c3 = result.certificates[1]
        assert c3.id == 3
        assert c3.status == "CURRENT"
        assert c3.qualification_date == (
            "2025-03-25T15:46:06Z"
        )

        call_args = mock_session.exec.call_args
        assert call_args[1].get("params") == {
            "status": "CURRENT"
        }

    def test_200_empty_combined_query(
        self, mock_session, client
    ):
        """200 OK — no entries with combined query params."""
        _mock_exec_success(
            mock_session, 200,
            LIST_ACCOUNT_CA_RESPONSE_200_EMPTY,
        )
        req = ListAccountCACertificatesRequest(
            status=[
                CertificateStatusExpired,
                CertificateStatusCurrent,
                CertificateStatusPrevious,
            ],
        )
        result = client.list_account_ca_certificates(req)
        assert len(result.certificates) == 0

        call_args = mock_session.exec.call_args
        assert call_args[1].get("params") == {
            "status": "EXPIRED,CURRENT,PREVIOUS"
        }

    def test_validation_wrong_status(self, client):
        """Validation: wrong status value."""
        req = ListAccountCACertificatesRequest(
            status=[
                "SOME_WRONG_STATUS",
                CertificateStatusCurrent,
                CertificateStatusPrevious,
            ],
        )
        with pytest.raises(ValueError) as exc_info:
            client.list_account_ca_certificates(req)
        assert str(exc_info.value) == (
            "list account ca certificates: struct validation: "
            "Status: list '[SOME_WRONG_STATUS CURRENT PREVIOUS]'"
            " contains invalid element 'SOME_WRONG_STATUS'. "
            "Each element must be one of: 'CURRENT', 'EXPIRED',"
            " 'PREVIOUS', or 'QUALIFYING'"
        )

    def test_500_server_error(self, mock_session, client):
        """500 — Internal server error."""
        _mock_exec_error(
            mock_session, 500, SERVER_ERROR_RESPONSE
        )
        req = ListAccountCACertificatesRequest()
        with pytest.raises(ValueError) as exc_info:
            client.list_account_ca_certificates(req)
        cause = exc_info.value.__cause__
        assert isinstance(cause, Error)
        assert cause.status == 500
        assert cause.type == "internal-server-error"
        assert cause.title == "Internal Server Error"
        assert cause.detail == "Error making request"
        assert cause.instance == "TestInstances"


# =====================================================================
# TestStatusesToQueryString — 3 scenarios
# =====================================================================


class TestStatusesToQueryString:
    """Tests for the statuses_to_query_string utility function."""

    def test_single_status(self):
        """Single status converts to query string."""
        result = statuses_to_query_string(
            [CertificateStatusCurrent]
        )
        assert result == "status=CURRENT"

    def test_multiple_statuses(self):
        """Multiple statuses are comma-separated and encoded."""
        result = statuses_to_query_string([
            CertificateStatusCurrent,
            CertificateStatusExpired,
        ])
        assert result == "status=CURRENT%2CEXPIRED"

    def test_all_statuses(self):
        """All four statuses are comma-separated and encoded."""
        result = statuses_to_query_string([
            CertificateStatusCurrent,
            CertificateStatusExpired,
            CertificateStatusPrevious,
            CertificateStatusQualifying,
        ])
        assert result == (
            "status=CURRENT%2CEXPIRED%2CPREVIOUS%2CQUALIFYING"
        )
