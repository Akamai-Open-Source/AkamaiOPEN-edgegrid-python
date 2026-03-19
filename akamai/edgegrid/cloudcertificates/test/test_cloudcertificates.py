"""Unit tests for the Cloud Certificates API client.

Mirrors all Go test scenarios from:
- pkg/cloudcertificates/certificates_test.go
- pkg/cloudcertificates/bindings_test.go
- pkg/cloudcertificates/cloudcertificates_test.go
- pkg/cloudcertificates/errors_test.go
"""
# pylint: disable=too-many-lines,line-too-long
import json
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.cloudcertificates.cloudcertificates import Client
from akamai.edgegrid.cloudcertificates import models
from akamai.edgegrid.cloudcertificates import errors
from akamai.edgegrid.cloudcertificates.test.conftest import (
    setup_mock_response,
)


# =====================================================================
# Common test data
# =====================================================================

_BASE_CERT_RESPONSE = {
    "accountId": "A-CCT7890",
    "certificateId": "123",
    "certificateName": "test-cert",
    "certificateStatus": "CSR_READY",
    "certificateType": "THIRD_PARTY",
    "contractId": "C-0N7RAC7",
    "createdBy": "jsmith",
    "createdDate": "2025-09-01T06:16:05.952613Z",
    "csrExpirationDate": "2026-11-03T06:16:07Z",
    "csrPem": (
        "-----BEGIN CERTIFICATE REQUEST-----\n"
        "example-PEM\n"
        "-----END CERTIFICATE REQUEST-----\n"
    ),
    "keySize": "2048",
    "keyType": "RSA",
    "modifiedBy": "jsmith",
    "modifiedDate": "2025-09-02T06:16:05.952613Z",
    "sans": ["example.com", "www.example.com"],
    "secureNetwork": "ENHANCED_TLS",
    "signedCertificateIssuer": None,
    "signedCertificateNotValidAfterDate": None,
    "signedCertificateNotValidBeforeDate": None,
    "signedCertificatePem": None,
    "signedCertificateSHA256Fingerprint": None,
    "signedCertificateSerialNumber": None,
    "subject": {
        "commonName": "example.com",
        "country": "US",
        "locality": "Cambridge",
        "organization": "ExampleOrg",
        "state": "Massachusetts",
    },
    "trustChainPem": None,
}

_BASE_RATE_LIMIT_HEADERS = {
    "Akamai-RateLimit-Limit": "60",
    "Akamai-RateLimit-Remaining": "59",
}

_BASE_RESOURCE_LIMIT_HEADERS = {
    "Akamai-Limit-Certificates": "100",
    "Akamai-Limit-Certificates-Remaining": "99",
}

_ALL_LIMIT_HEADERS = {
    **_BASE_RATE_LIMIT_HEADERS,
    **_BASE_RESOURCE_LIMIT_HEADERS,
}


def _base_certificate(**overrides):
    """Construct the base Certificate used across tests."""
    defaults = {
        "account_id": "A-CCT7890",
        "certificate_id": "123",
        "certificate_name": "test-cert",
        "certificate_status": "CSR_READY",
        "certificate_type": "THIRD_PARTY",
        "contract_id": "C-0N7RAC7",
        "created_by": "jsmith",
        "created_date": "2025-09-01T06:16:05.952613Z",
        "csr_expiration_date": "2026-11-03T06:16:07Z",
        "csr_pem": (
            "-----BEGIN CERTIFICATE REQUEST-----\n"
            "example-PEM\n"
            "-----END CERTIFICATE REQUEST-----\n"
        ),
        "key_size": "2048",
        "key_type": "RSA",
        "modified_by": "jsmith",
        "modified_date": "2025-09-02T06:16:05.952613Z",
        "sans": ["example.com", "www.example.com"],
        "secure_network": "ENHANCED_TLS",
        "subject": models.Subject(
            common_name="example.com",
            country="US",
            locality="Cambridge",
            organization="ExampleOrg",
            state="Massachusetts",
        ),
    }
    defaults.update(overrides)
    return models.Certificate(**defaults)


def _base_create_params(**overrides):
    """Construct the base CreateCertificateRequest."""
    defaults = {
        "contract_id": "111",
        "group_id": "222",
        "body": models.CreateCertificateRequestBody(
            certificate_name="test-cert",
            key_type="RSA",
            key_size="2048",
            secure_network="ENHANCED_TLS",
            sans=["example.com", "www.example.com"],
            subject=models.Subject(
                common_name="example.com",
                organization="ExampleOrg",
                country="US",
                state="Massachusetts",
                locality="Cambridge",
            ),
        ),
    }
    defaults.update(overrides)
    return models.CreateCertificateRequest(**defaults)


def _make_api_error_str(sentinel, **error_fields):
    """Construct the expected _WrappedError string."""
    err = errors.Error(**error_fields)
    return f"{sentinel}: {err}"


# =====================================================================
# TestClient
# =====================================================================


class TestClient:
    """Tests for Client constructor mirroring cloudcertificates_test.go."""

    def test_default_client(self):
        """No options provided, return default."""
        session = MagicMock()
        c = Client(session)
        assert c._session is session  # pylint: disable=protected-access

    def test_client_stores_session(self):
        """Option provided, overwrite session."""
        session = MagicMock()
        c = Client(session)
        assert c._session == session  # pylint: disable=protected-access


# =====================================================================
# TestNewError
# =====================================================================


class TestNewError:  # pylint: disable=too-few-public-methods
    """Tests for error parsing mirroring errors_test.go TestNewError."""

    @pytest.mark.parametrize(
        "name,http_status,response_body,expected",
        [
            (
                "Bad request 400 - invalid field value",
                400,
                json.dumps({
                    "detail": (
                        "Invalid value '{grp_1234}' for field "
                        "'{groupId}'. Failed to convert value of "
                        "type 'String' to required type 'Integer'"
                        "; For input string: \"grp_1234\""
                    ),
                    "status": 400,
                    "title": "Invalid field value.",
                    "type": "/error-types/invalid-field",
                    "instance":
                        "/error-types/invalid-field?traceId=12345",
                    "explanation": (
                        "Failed to convert value of type 'String' "
                        "to required type 'Integer'; For input "
                        "string: \"grp_1234\""
                    ),
                    "parameterName": "groupId",
                    "invalidParameterValue": "grp_1234",
                }),
                errors.Error(
                    type="/error-types/invalid-field",
                    title="Invalid field value.",
                    status=400,
                    detail=(
                        "Invalid value '{grp_1234}' for field "
                        "'{groupId}'. Failed to convert value of "
                        "type 'String' to required type 'Integer'"
                        "; For input string: \"grp_1234\""
                    ),
                    instance=
                        "/error-types/invalid-field?traceId=12345",
                    explanation=(
                        "Failed to convert value of type 'String' "
                        "to required type 'Integer'; For input "
                        "string: \"grp_1234\""
                    ),
                    parameter_name="groupId",
                    invalid_parameter_value="grp_1234",
                ),
            ),
            (
                "Resource not found 404",
                404,
                json.dumps({
                    "type": "/error-types/certificate-not-found",
                    "title":
                        "Certificate subscription is not found.",
                    "instance": (
                        "/error-types/certificate-not-found"
                        "?traceId=12345"
                    ),
                    "status": 404,
                    "detail": (
                        "Certificate subscription with "
                        "{certificateSubscriptionId}: {1234} "
                        "is not found."
                    ),
                    "certificateIdentifier":
                        "certificateSubscriptionId",
                    "certificateIdentifierValue": "1234",
                }),
                errors.Error(
                    type="/error-types/certificate-not-found",
                    title=
                        "Certificate subscription is not found.",
                    status=404,
                    detail=(
                        "Certificate subscription with "
                        "{certificateSubscriptionId}: {1234} "
                        "is not found."
                    ),
                    instance=(
                        "/error-types/certificate-not-found"
                        "?traceId=12345"
                    ),
                    certificate_identifier=
                        "certificateSubscriptionId",
                    certificate_identifier_value="1234",
                ),
            ),
            (
                "Validation error 400 - invalid parameter value",
                400,
                json.dumps({
                    "type": "/error-types/validation-failure",
                    "title": "Validation failure.",
                    "instance": (
                        "/error-types/validation-failure"
                        "?traceId=12345"
                    ),
                    "status": 400,
                    "detail": (
                        "Validation failed while executing "
                        "the operation."
                    ),
                    "errors": [
                        {
                            "type": "/error-types/invalid-field",
                            "title": "Invalid field value.",
                            "detail": (
                                "Invalid value '{[example.com]}'"
                                " for field '{sans}'. SANs list "
                                "cannot contain duplicates."
                            ),
                            "instance": (
                                "/error-types/validation-failure"
                                "?traceId=12345"
                            ),
                            "explanation": (
                                "SANs list cannot contain "
                                "duplicates."
                            ),
                            "invalidParameterValue":
                                ["example.com"],
                            "parameterName": "sans",
                        },
                    ],
                }),
                errors.Error(
                    type="/error-types/validation-failure",
                    title="Validation failure.",
                    status=400,
                    detail=(
                        "Validation failed while executing "
                        "the operation."
                    ),
                    instance=(
                        "/error-types/validation-failure"
                        "?traceId=12345"
                    ),
                    errors=[
                        errors.SecondaryError(
                            type="/error-types/invalid-field",
                            title="Invalid field value.",
                            detail=(
                                "Invalid value '{[example.com]}'"
                                " for field '{sans}'. SANs list "
                                "cannot contain duplicates."
                            ),
                            instance=(
                                "/error-types/validation-failure"
                                "?traceId=12345"
                            ),
                            explanation=(
                                "SANs list cannot contain "
                                "duplicates."
                            ),
                            invalid_parameter_value=
                                ["example.com"],
                            parameter_name="sans",
                        ),
                    ],
                ),
            ),
            (
                "Invalid response body, assign status code",
                500,
                "test",
                errors.Error(
                    title=(
                        "Failed to unmarshal error body. CCM API "
                        "failed. Check details for more information."
                    ),
                    detail="test",
                    status=500,
                ),
            ),
            (
                "Empty response body, assign status code",
                500,
                "",
                errors.Error(
                    title=(
                        "Failed to unmarshal error body. CCM API "
                        "failed. Check details for more information."
                    ),
                    detail="",
                    status=500,
                ),
            ),
        ],
    )
    def test_new_error(self, name, http_status, response_body,
                       expected):
        """Test error parsing from response bodies."""
        result = errors.new_error(http_status, response_body)
        assert result == expected, (
            f"Scenario '{name}': "
            f"expected {expected}, got {result}"
        )



# =====================================================================
# TestIs
# =====================================================================


class TestIs:  # pylint: disable=too-few-public-methods
    """Tests for Error.is_equivalent() mirroring errors_test.go TestIs."""

    @pytest.mark.parametrize(
        "name,target,expected",
        [
            (
                "different error status",
                errors.Error(status=401),
                False,
            ),
            (
                "different error title",
                errors.Error(title="other error"),
                False,
            ),
            (
                "same error title",
                errors.Error(title="some error"),
                True,
            ),
            (
                "same error type",
                errors.Error(type="/some/type"),
                True,
            ),
            (
                "same error status",
                errors.Error(status=404),
                True,
            ),
            (
                "same error type, title and status",
                errors.Error(
                    type="/some/type",
                    title="some error",
                    status=404,
                ),
                True,
            ),
            (
                "same error type but different title",
                errors.Error(
                    type="/some/type",
                    title="other error",
                ),
                False,
            ),
            (
                "same error status and title but different type",
                errors.Error(
                    type="/other/type",
                    title="some error",
                    status=404,
                ),
                False,
            ),
            (
                "same error status and type but different "
                "detail and instance",
                errors.Error(
                    type="/some/type",
                    status=404,
                    detail="other detail",
                    instance="/other/error/instance",
                ),
                True,
            ),
        ],
    )
    def test_is_equivalent(self, name, target, expected):
        """Test wildcard matching for Error.is_equivalent()."""
        src = errors.Error(
            type="/some/type",
            title="some error",
            status=404,
            detail="some detail",
            instance="/some/error/instance",
        )
        result = src.is_equivalent(target)
        assert result == expected, (
            f"Scenario '{name}': "
            f"expected {expected}, got {result}"
        )


# =====================================================================
# TestError
# =====================================================================


class TestError:  # pylint: disable=too-few-public-methods
    """Tests for Error.__str__() mirroring errors_test.go TestError."""

    def test_error_string(self):
        """Test Error string representation matches Go output."""
        err = errors.Error(
            type="/error-types/test",
            title="Test Error",
            status=400,
            detail="This is a test error",
            instance="/error-types/test?traceId=12345",
        )
        expected_dict = {
            "type": "/error-types/test",
            "title": "Test Error",
            "status": 400,
            "detail": "This is a test error",
            "instance": "/error-types/test?traceId=12345",
        }
        expected = (
            "API error: \n"
            + json.dumps(expected_dict, indent="\t")
        )
        assert str(err) == expected

        # Verify json.loads round-trip of Error string body
        err_str = str(err)
        body_json = err_str.replace("API error: \n", "")
        parsed = json.loads(body_json)
        assert parsed["type"] == "/error-types/test"
        assert parsed["status"] == 400

        # Verify sentinel error constants are accessible
        assert (
            errors.ErrCertificateResourceNotFound
            is not None
        )
        assert (
            errors.ErrCertificateResourceNotFound.type
            == "/error-types/certificate-resource-not-found"
        )

        # Verify error data model types are importable
        # and constructable (ValidationData, PEMValidation,
        # ValidationResult, ValidationDetail).
        vd = errors.ValidationDetail(
            type="/error-types/test",
            title="test",
            detail="test detail",
        )
        assert vd.type == "/error-types/test"
        vr = errors.ValidationResult(
            errors=[vd], warnings=[], notices=[],
        )
        assert len(vr.errors) == 1
        pv = errors.PEMValidation(
            certificate_pem="test-pem",
            validation=vr,
        )
        assert pv.certificate_pem == "test-pem"
        val_data = errors.ValidationData(
            signed_certificate_pem="test-pem",
            validation=vr,
        )
        assert val_data.signed_certificate_pem == "test-pem"



# =====================================================================
# TestCreateCertificate
# =====================================================================

# Response bodies for create certificate tests
_CREATE_CERT_RESPONSE_BODY = json.dumps({
    "accountId": "A-CCT7890",
    "certificateId": "123",
    "certificateName": "test-cert",
    "certificateStatus": "CSR_READY",
    "certificateType": "THIRD_PARTY",
    "contractId": "C-0N7RAC7",
    "createdBy": "jsmith",
    "createdDate": "2025-09-01T06:16:05.952613Z",
    "csrExpirationDate": "2026-11-03T06:16:07Z",
    "csrPem": (
        "-----BEGIN CERTIFICATE REQUEST-----\n"
        "example-PEM\n"
        "-----END CERTIFICATE REQUEST-----\n"
    ),
    "keySize": "2048",
    "keyType": "RSA",
    "modifiedBy": "jsmith",
    "modifiedDate": "2025-09-02T06:16:05.952613Z",
    "sans": ["example.com", "www.example.com"],
    "secureNetwork": "ENHANCED_TLS",
    "signedCertificateIssuer": None,
    "signedCertificateNotValidAfterDate": None,
    "signedCertificateNotValidBeforeDate": None,
    "signedCertificatePem": None,
    "signedCertificateSHA256Fingerprint": None,
    "signedCertificateSerialNumber": None,
    "subject": {
        "commonName": "example.com",
        "country": "US",
        "locality": "Cambridge",
        "organization": "ExampleOrg",
        "state": "Massachusetts",
    },
    "trustChainPem": None,
})

_CREATE_CERT_NO_NAME_RESPONSE_BODY = json.dumps({
    "accountId": "A-CCT7890",
    "certificateId": "123",
    "certificateName": None,
    "certificateStatus": "CSR_READY",
    "certificateType": "THIRD_PARTY",
    "contractId": "C-0N7RAC7",
    "createdBy": "jsmith",
    "createdDate": "2025-09-01T06:16:05.952613Z",
    "csrExpirationDate": "2026-11-03T06:16:07Z",
    "csrPem": (
        "-----BEGIN CERTIFICATE REQUEST-----\n"
        "example-PEM\n"
        "-----END CERTIFICATE REQUEST-----\n"
    ),
    "keySize": "2048",
    "keyType": "RSA",
    "modifiedBy": "jsmith",
    "modifiedDate": "2025-09-02T06:16:05.952613Z",
    "sans": ["example.com", "www.example.com"],
    "secureNetwork": "ENHANCED_TLS",
    "signedCertificateIssuer": None,
    "signedCertificateNotValidAfterDate": None,
    "signedCertificateNotValidBeforeDate": None,
    "signedCertificatePem": None,
    "signedCertificateSHA256Fingerprint": None,
    "signedCertificateSerialNumber": None,
    "subject": {
        "commonName": "example.com",
        "country": "US",
        "locality": "Cambridge",
        "organization": "ExampleOrg",
        "state": "Massachusetts",
    },
    "trustChainPem": None,
})

_CREATE_CERT_NO_SUBJECT_RESPONSE_BODY = json.dumps({
    "accountId": "A-CCT7890",
    "certificateId": "123",
    "certificateName": "test-cert",
    "certificateStatus": "CSR_READY",
    "certificateType": "THIRD_PARTY",
    "contractId": "C-0N7RAC7",
    "createdBy": "jsmith",
    "createdDate": "2025-09-01T06:16:05.952613Z",
    "csrExpirationDate": "2026-11-03T06:16:07Z",
    "csrPem": (
        "-----BEGIN CERTIFICATE REQUEST-----\n"
        "example-PEM\n"
        "-----END CERTIFICATE REQUEST-----\n"
    ),
    "keySize": "2048",
    "keyType": "RSA",
    "modifiedBy": "jsmith",
    "modifiedDate": "2025-09-02T06:16:05.952613Z",
    "sans": ["example.com", "www.example.com"],
    "secureNetwork": "ENHANCED_TLS",
    "signedCertificateIssuer": None,
    "signedCertificateNotValidAfterDate": None,
    "signedCertificateNotValidBeforeDate": None,
    "signedCertificatePem": None,
    "signedCertificateSHA256Fingerprint": None,
    "signedCertificateSerialNumber": None,
    "subject": None,
    "trustChainPem": None,
})


class TestCreateCertificate:  # pylint: disable=too-few-public-methods
    """Tests for create_certificate mirroring certificates_test.go."""

    @pytest.mark.parametrize(
        "name,params,response_status,response_body,"
        "returned_headers,expected_error,check_sentinels",
        [
            (
                "201 Created - create certificate "
                "with all possible fields",
                _base_create_params(),
                201,
                _CREATE_CERT_RESPONSE_BODY,
                {
                    **_BASE_RATE_LIMIT_HEADERS,
                    **_BASE_RESOURCE_LIMIT_HEADERS,
                },
                None,
                None,
            ),
            (
                "201 Created - no rate limit headers",
                _base_create_params(),
                201,
                _CREATE_CERT_RESPONSE_BODY,
                {},
                None,
                None,
            ),
            (
                "201 Created - empty rate limit headers",
                _base_create_params(),
                201,
                _CREATE_CERT_RESPONSE_BODY,
                {
                    "Akamai-RateLimit-Limit": "",
                    "Akamai-RateLimit-Remaining": "",
                    "Akamai-Limit-Certificates": "",
                    "Akamai-Limit-Certificates-Remaining": "",
                },
                None,
                None,
            ),
            (
                "201 Created - create certificate without name",
                models.CreateCertificateRequest(
                    contract_id="111",
                    group_id="222",
                    body=models.CreateCertificateRequestBody(
                        key_type="RSA",
                        key_size="2048",
                        secure_network="ENHANCED_TLS",
                        sans=["example.com", "www.example.com"],
                        subject=models.Subject(
                            common_name="example.com",
                            organization="ExampleOrg",
                            country="US",
                            state="Massachusetts",
                            locality="Cambridge",
                        ),
                    ),
                ),
                201,
                _CREATE_CERT_NO_NAME_RESPONSE_BODY,
                {**_BASE_RATE_LIMIT_HEADERS,
                 **_BASE_RESOURCE_LIMIT_HEADERS},
                None,
                None,
            ),
            (
                "201 Created - create certificate but "
                "cannot parse limit headers",
                _base_create_params(),
                201,
                _CREATE_CERT_RESPONSE_BODY,
                {
                    "Akamai-RateLimit-Limit": "not-parsable",
                    "Akamai-RateLimit-Remaining": "not-parsable",
                    "Akamai-Limit-Certificates": "not-parsable",
                    "Akamai-Limit-Certificates-Remaining":
                        "not-parsable",
                },
                None,
                None,
            ),
            (
                "201 Created - create certificate with no subject",
                models.CreateCertificateRequest(
                    contract_id="111",
                    group_id="222",
                    body=models.CreateCertificateRequestBody(
                        certificate_name="test-cert",
                        key_type="RSA",
                        key_size="2048",
                        secure_network="ENHANCED_TLS",
                        sans=["example.com", "www.example.com"],
                    ),
                ),
                201,
                _CREATE_CERT_NO_SUBJECT_RESPONSE_BODY,
                {**_BASE_RATE_LIMIT_HEADERS,
                 **_BASE_RESOURCE_LIMIT_HEADERS},
                None,
                None,
            ),
            (
                "validation error - missing required ContractID",
                models.CreateCertificateRequest(
                    contract_id="",
                    group_id="222",
                    body=models.CreateCertificateRequestBody(
                        certificate_name="test-cert",
                        key_type="RSA",
                        key_size="2048",
                        secure_network="ENHANCED_TLS",
                        sans=["example.com"],
                        subject=models.Subject(
                            common_name="example.com",
                            country="US",
                        ),
                    ),
                ),
                None,
                None,
                None,
                ("creating certificate: struct validation: "
                 "ContractID: cannot be blank"),
                [errors.ErrCreateCertificate,
                 errors.ErrStructValidation],
            ),
            (
                "validation error - missing required GroupID",
                models.CreateCertificateRequest(
                    contract_id="111",
                    group_id="",
                    body=models.CreateCertificateRequestBody(
                        certificate_name="test-cert",
                        key_type="RSA",
                        key_size="2048",
                        secure_network="ENHANCED_TLS",
                        sans=["example.com"],
                        subject=models.Subject(
                            common_name="example.com",
                            country="US",
                        ),
                    ),
                ),
                None,
                None,
                None,
                ("creating certificate: struct validation: "
                 "GroupID: cannot be blank"),
                [errors.ErrCreateCertificate,
                 errors.ErrStructValidation],
            ),
            (
                "validation error - invalid certificate name",
                models.CreateCertificateRequest(
                    contract_id="111",
                    group_id="222",
                    body=models.CreateCertificateRequestBody(
                        certificate_name="test-cert##",
                        key_type="RSA",
                        key_size="2048",
                        secure_network="ENHANCED_TLS",
                        sans=["example.com"],
                        subject=models.Subject(
                            common_name="example.com",
                            country="US",
                        ),
                    ),
                ),
                None,
                None,
                None,
                ("creating certificate: struct validation: "
                 "CertificateName: the input can only contain "
                 "digits (1-9), letters (a-z, A-Z), spaces, "
                 "hyphens, periods, and underscores."),
                [errors.ErrCreateCertificate,
                 errors.ErrStructValidation],
            ),
            (
                "validation error - invalid key type",
                models.CreateCertificateRequest(
                    contract_id="111",
                    group_id="222",
                    body=models.CreateCertificateRequestBody(
                        certificate_name="test-cert",
                        key_type="INVALID",
                        key_size="2048",
                        secure_network="ENHANCED_TLS",
                        sans=["example.com"],
                        subject=models.Subject(
                            common_name="example.com",
                            country="US",
                        ),
                    ),
                ),
                None,
                None,
                None,
                ("creating certificate: struct validation: "
                 "KeyType: value 'INVALID' is invalid. "
                 "Must be either 'RSA' or 'ECDSA'"),
                [errors.ErrCreateCertificate,
                 errors.ErrStructValidation],
            ),
            (
                "validation error - invalid key size",
                models.CreateCertificateRequest(
                    contract_id="111",
                    group_id="222",
                    body=models.CreateCertificateRequestBody(
                        certificate_name="test-cert",
                        key_type="RSA",
                        key_size="1111",
                        secure_network="ENHANCED_TLS",
                        sans=["example.com"],
                        subject=models.Subject(
                            common_name="example.com",
                            country="US",
                        ),
                    ),
                ),
                None,
                None,
                None,
                ("creating certificate: struct validation: "
                 "KeySize: value '1111' is invalid. "
                 "Must be one of: '2048', or 'P-256'"),
                [errors.ErrCreateCertificate,
                 errors.ErrStructValidation],
            ),
            (
                "validation error - invalid secure network",
                models.CreateCertificateRequest(
                    contract_id="111",
                    group_id="222",
                    body=models.CreateCertificateRequestBody(
                        certificate_name="test-cert",
                        key_type="RSA",
                        key_size="2048",
                        secure_network="WRONG_NETWORK",
                        sans=["example.com"],
                        subject=models.Subject(
                            common_name="example.com",
                            country="US",
                        ),
                    ),
                ),
                None,
                None,
                None,
                ("creating certificate: struct validation: "
                 "SecureNetwork: value 'WRONG_NETWORK' is "
                 "invalid. Must be: 'ENHANCED_TLS'"),
                [errors.ErrCreateCertificate,
                 errors.ErrStructValidation],
            ),
            (
                "validation error - invalid subject "
                "country code length",
                models.CreateCertificateRequest(
                    contract_id="111",
                    group_id="222",
                    body=models.CreateCertificateRequestBody(
                        certificate_name="test-cert",
                        key_type="RSA",
                        key_size="2048",
                        secure_network="ENHANCED_TLS",
                        sans=["example.com"],
                        subject=models.Subject(
                            common_name="example.com",
                            country="TESTETSTES",
                        ),
                    ),
                ),
                None,
                None,
                None,
                ("creating certificate: struct validation: "
                 "Subject: Country: the length must be exactly 2"),
                [errors.ErrCreateCertificate,
                 errors.ErrStructValidation],
            ),
            (
                "validation error - invalid subject "
                "country code format",
                models.CreateCertificateRequest(
                    contract_id="111",
                    group_id="222",
                    body=models.CreateCertificateRequestBody(
                        certificate_name="test-cert",
                        key_type="RSA",
                        key_size="2048",
                        secure_network="ENHANCED_TLS",
                        sans=["example.com"],
                        subject=models.Subject(
                            common_name="example.com",
                            country="  ",
                        ),
                    ),
                ),
                None,
                None,
                None,
                ("creating certificate: struct validation: "
                 "Subject: Country: must be in a valid format"),
                [errors.ErrCreateCertificate,
                 errors.ErrStructValidation],
            ),
            (
                "validation error - invalid subject "
                "locality length",
                models.CreateCertificateRequest(
                    contract_id="111",
                    group_id="222",
                    body=models.CreateCertificateRequestBody(
                        certificate_name="test-cert",
                        key_type="RSA",
                        key_size="2048",
                        secure_network="ENHANCED_TLS",
                        sans=["example.com"],
                        subject=models.Subject(
                            common_name="example.com",
                            country="US",
                            locality="A" * 129,
                        ),
                    ),
                ),
                None,
                None,
                None,
                ("creating certificate: struct validation: "
                 "Subject: Locality: the length must be between "
                 "1 and 128"),
                [errors.ErrCreateCertificate,
                 errors.ErrStructValidation],
            ),
            (
                "validation error - invalid subject "
                "locality format",
                models.CreateCertificateRequest(
                    contract_id="111",
                    group_id="222",
                    body=models.CreateCertificateRequestBody(
                        certificate_name="test-cert",
                        key_type="RSA",
                        key_size="2048",
                        secure_network="ENHANCED_TLS",
                        sans=["example.com"],
                        subject=models.Subject(
                            common_name="example.com",
                            country="US",
                            locality="\t\t",
                        ),
                    ),
                ),
                None,
                None,
                None,
                ("creating certificate: struct validation: "
                 "Subject: Locality: must be in a valid format"),
                [errors.ErrCreateCertificate,
                 errors.ErrStructValidation],
            ),
            (
                "validation error - invalid subject "
                "state length",
                models.CreateCertificateRequest(
                    contract_id="111",
                    group_id="222",
                    body=models.CreateCertificateRequestBody(
                        certificate_name="test-cert",
                        key_type="RSA",
                        key_size="2048",
                        secure_network="ENHANCED_TLS",
                        sans=["example.com"],
                        subject=models.Subject(
                            common_name="example.com",
                            country="US",
                            state="A" * 129,
                        ),
                    ),
                ),
                None,
                None,
                None,
                ("creating certificate: struct validation: "
                 "Subject: State: the length must be between "
                 "1 and 128"),
                [errors.ErrCreateCertificate,
                 errors.ErrStructValidation],
            ),
            (
                "validation error - invalid subject "
                "state format",
                models.CreateCertificateRequest(
                    contract_id="111",
                    group_id="222",
                    body=models.CreateCertificateRequestBody(
                        certificate_name="test-cert",
                        key_type="RSA",
                        key_size="2048",
                        secure_network="ENHANCED_TLS",
                        sans=["example.com"],
                        subject=models.Subject(
                            common_name="example.com",
                            country="US",
                            state="\t\t",
                        ),
                    ),
                ),
                None,
                None,
                None,
                ("creating certificate: struct validation: "
                 "Subject: State: must be in a valid format"),
                [errors.ErrCreateCertificate,
                 errors.ErrStructValidation],
            ),
            (
                "validation error - invalid subject "
                "organization length",
                models.CreateCertificateRequest(
                    contract_id="111",
                    group_id="222",
                    body=models.CreateCertificateRequestBody(
                        certificate_name="test-cert",
                        key_type="RSA",
                        key_size="2048",
                        secure_network="ENHANCED_TLS",
                        sans=["example.com"],
                        subject=models.Subject(
                            common_name="example.com",
                            country="US",
                            organization="A" * 65,
                        ),
                    ),
                ),
                None,
                None,
                None,
                ("creating certificate: struct validation: "
                 "Subject: Organization: the length must be between "
                 "1 and 64"),
                [errors.ErrCreateCertificate,
                 errors.ErrStructValidation],
            ),
            (
                "validation error - invalid subject "
                "organization format",
                models.CreateCertificateRequest(
                    contract_id="111",
                    group_id="222",
                    body=models.CreateCertificateRequestBody(
                        certificate_name="test-cert",
                        key_type="RSA",
                        key_size="2048",
                        secure_network="ENHANCED_TLS",
                        sans=["example.com"],
                        subject=models.Subject(
                            common_name="example.com",
                            country="US",
                            organization="\t\t",
                        ),
                    ),
                ),
                None,
                None,
                None,
                ("creating certificate: struct validation: "
                 "Subject: Organization: must be in a valid format"),
                [errors.ErrCreateCertificate,
                 errors.ErrStructValidation],
            ),
            (
                "409 - certificate name already in use",
                _base_create_params(),
                409,
                json.dumps({
                    "type": (
                        "/error-types/"
                        "certificate-name-already-in-use"
                    ),
                    "title":
                        "Certificate name is already in use.",
                    "instance": (
                        "/error-types/"
                        "certificate-name-already-in-use"
                        "?traceId=12345"
                    ),
                    "status": 409,
                    "detail": (
                        "Certificate with name 'test-cert' "
                        "already exists."
                    ),
                }),
                None,
                None,
                [errors.ErrCreateCertificate,
                 errors.ErrCertificateNameInUse],
            ),
            (
                "500 internal server error",
                _base_create_params(),
                500,
                json.dumps({
                    "type": "internal_error",
                    "title": "Internal Server Error",
                    "detail": "Error creating entity",
                    "status": 500,
                }),
                None,
                None,
                [errors.ErrCreateCertificate],
            ),
        ],
    )
    def test_create_certificate(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals,too-many-branches
        self, mock_session, client, name, params,
        response_status, response_body, returned_headers,
        expected_error, check_sentinels,
    ):
        """Test create_certificate mirroring Go test scenarios."""
        _ = name  # used for test identification only
        # Set up mock if we have a response
        if response_status is not None:
            setup_mock_response(
                mock_session, response_status,
                response_body or "", returned_headers,
            )

        # Validation error case
        if expected_error is not None:
            with pytest.raises(ValueError) as exc_info:
                client.create_certificate(params)
            assert str(exc_info.value) == expected_error
            if check_sentinels:
                for sentinel in check_sentinels:
                    assert sentinel in str(exc_info.value)
            return

        # API error case (non-success status)
        if response_status not in (200, 201):
            with pytest.raises(Exception) as exc_info:
                client.create_certificate(params)
            err = exc_info.value
            if check_sentinels:
                for sentinel in check_sentinels:
                    if isinstance(sentinel, str):
                        assert sentinel in str(err)
                    elif isinstance(sentinel, errors.Error):
                        assert hasattr(err, "api_error")
                        assert err.api_error.is_equivalent(
                            sentinel
                        )
            return

        # Success case
        result = client.create_certificate(params)
        assert result is not None
        assert isinstance(
            result, models.CreateCertificateResponse
        )
        assert result.certificate is not None
        assert isinstance(
            result.certificate, models.Certificate
        )
        assert result.certificate.certificate_id == "123"
        assert result.certificate.certificate_status == (
            "CSR_READY"
        )

        # Verify rate limits if headers present
        if returned_headers:
            rl_limit = returned_headers.get(
                "Akamai-RateLimit-Limit", ""
            )
            rl_remaining = returned_headers.get(
                "Akamai-RateLimit-Remaining", ""
            )
            if rl_limit and rl_limit.isdigit():
                assert result.rate_limits_metadata is not None
                assert isinstance(
                    result.rate_limits_metadata,
                    models.RateLimitsMetadata,
                )
                assert (
                    result.rate_limits_metadata.limit
                    == int(rl_limit)
                )
                assert (
                    result.rate_limits_metadata.remaining
                    == int(rl_remaining)
                )
            res_limit = returned_headers.get(
                "Akamai-Limit-Certificates", ""
            )
            res_rem = returned_headers.get(
                "Akamai-Limit-Certificates-Remaining", ""
            )
            if res_limit and res_limit.isdigit():
                assert (
                    result.resource_limits_metadata is not None
                )
                assert isinstance(
                    result.resource_limits_metadata,
                    models.ResourceLimitsMetadata,
                )
                assert (
                    result.resource_limits_metadata
                    .certificate_limit_total
                    == int(res_limit)
                )
                if res_rem and res_rem.isdigit():
                    assert (
                        result.resource_limits_metadata
                        .certificate_limit_remaining
                        == int(res_rem)
                    )



# =====================================================================
# TestGetCertificate
# =====================================================================

_GET_CERT_RESPONSE_BODY = json.dumps({
    "accountId": "A-CCT7890",
    "certificateId": "123",
    "certificateName": "test-cert",
    "certificateStatus": "CSR_READY",
    "certificateType": "THIRD_PARTY",
    "contractId": "C-0N7RAC7",
    "createdBy": "jsmith",
    "createdDate": "2025-09-01T06:16:05.952613Z",
    "csrExpirationDate": "2026-11-03T06:16:07Z",
    "csrPem": (
        "-----BEGIN CERTIFICATE REQUEST-----\n"
        "example-PEM\n"
        "-----END CERTIFICATE REQUEST-----\n"
    ),
    "keySize": "2048",
    "keyType": "RSA",
    "modifiedBy": "jsmith",
    "modifiedDate": "2025-09-02T06:16:05.952613Z",
    "sans": ["example.com", "www.example.com"],
    "secureNetwork": "ENHANCED_TLS",
    "signedCertificateIssuer": None,
    "signedCertificateNotValidAfterDate": None,
    "signedCertificateNotValidBeforeDate": None,
    "signedCertificatePem": None,
    "signedCertificateSHA256Fingerprint": None,
    "signedCertificateSerialNumber": None,
    "subject": {
        "commonName": "example.com",
        "country": "US",
        "locality": "Cambridge",
        "organization": "ExampleOrg",
        "state": "Massachusetts",
    },
    "trustChainPem": None,
})


class TestGetCertificate:  # pylint: disable=too-few-public-methods
    """Tests for get_certificate mirroring Go tests."""

    @pytest.mark.parametrize(
        "name,params,response_status,response_body,"
        "returned_headers,expected_error,check_sentinels",
        [
            (
                "200 - fetch of certificate successful",
                models.GetCertificateRequest(
                    certificate_id="123",
                ),
                200,
                _GET_CERT_RESPONSE_BODY,
                _BASE_RATE_LIMIT_HEADERS,
                None,
                None,
            ),
            (
                "404 resource not found "
                "- certificate not found",
                models.GetCertificateRequest(
                    certificate_id="1234",
                ),
                404,
                json.dumps({
                    "certificateIdentifier":
                        "certificateSubscriptionId",
                    "certificateIdentifierValue": "1234",
                    "detail": (
                        "Certificate subscription with "
                        "{certificateSubscriptionId}: "
                        "{1234} is not found."
                    ),
                    "instance": (
                        "/error-types/certificate-not-found"
                        "?traceId=-1234"
                    ),
                    "status": 404,
                    "title":
                        "Certificate subscription "
                        "is not found.",
                    "type": (
                        "/error-types/"
                        "certificate-not-found"
                    ),
                }),
                None,
                None,
                [errors.ErrGetCertificate,
                 errors.ErrCertificateNotFound],
            ),
            (
                "500 internal server error",
                models.GetCertificateRequest(
                    certificate_id="123",
                ),
                500,
                json.dumps({
                    "type": "internal_error",
                    "title": "Internal Server Error",
                    "detail": "Error removing certificate",
                    "status": 500,
                }),
                None,
                None,
                [errors.ErrGetCertificate],
            ),
            (
                "validation error - missing CertificateID",
                models.GetCertificateRequest(
                    certificate_id="",
                ),
                None,
                None,
                None,
                ("getting certificate: struct validation: "
                 "CertificateID: cannot be blank"),
                [errors.ErrGetCertificate,
                 errors.ErrStructValidation],
            ),
        ],
    )
    def test_get_certificate(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self, mock_session, client, name, params,
        response_status, response_body, returned_headers,
        expected_error, check_sentinels,
    ):
        """Test get_certificate mirroring Go test scenarios."""
        _ = name  # used for test identification only
        if response_status is not None:
            setup_mock_response(
                mock_session, response_status,
                response_body or "", returned_headers,
            )

        if expected_error is not None:
            with pytest.raises(ValueError) as exc_info:
                client.get_certificate(params)
            assert str(exc_info.value) == expected_error
            if check_sentinels:
                for sentinel in check_sentinels:
                    assert sentinel in str(exc_info.value)
            return

        if response_status not in (200, 201):
            with pytest.raises(Exception) as exc_info:
                client.get_certificate(params)
            err = exc_info.value
            if check_sentinels:
                for sentinel in check_sentinels:
                    if isinstance(sentinel, str):
                        assert sentinel in str(err)
                    elif isinstance(sentinel, errors.Error):
                        assert hasattr(err, "api_error")
                        assert err.api_error.is_equivalent(
                            sentinel
                        )
            return

        result = client.get_certificate(params)
        assert result is not None
        assert isinstance(
            result, models.GetCertificateResponse
        )
        assert result.certificate is not None
        assert result.certificate.certificate_id == "123"
        assert result.certificate.certificate_status == (
            "CSR_READY"
        )
        assert result.certificate.certificate_name == (
            "test-cert"
        )
        if returned_headers:
            rl_limit = returned_headers.get(
                "Akamai-RateLimit-Limit", ""
            )
            if rl_limit and rl_limit.isdigit():
                assert (
                    result.rate_limits_metadata is not None
                )
                assert (
                    result.rate_limits_metadata.limit
                    == int(rl_limit)
                )


# =====================================================================
# TestDeleteCertificate
# =====================================================================

class TestDeleteCertificate:  # pylint: disable=too-few-public-methods
    """Tests for delete_certificate mirroring Go tests."""

    @pytest.mark.parametrize(
        "name,params,response_status,response_body,"
        "returned_headers,expected_error,check_sentinels",
        [
            (
                "204 certificate deleted successfully",
                models.DeleteCertificateRequest(
                    certificate_id="certificate_123",
                ),
                204,
                "",
                _BASE_RATE_LIMIT_HEADERS,
                None,
                None,
            ),
            (
                "404 resource not found "
                "- certificate not found",
                models.DeleteCertificateRequest(
                    certificate_id="1234",
                ),
                404,
                json.dumps({
                    "certificateIdentifier":
                        "certificateSubscriptionId",
                    "certificateIdentifierValue": "1234",
                    "detail": (
                        "Certificate subscription with "
                        "{certificateSubscriptionId}: "
                        "{1234} is not found."
                    ),
                    "instance": (
                        "/error-types/certificate-not-found"
                        "?traceId=-1234"
                    ),
                    "status": 404,
                    "title":
                        "Certificate subscription "
                        "is not found.",
                    "type": (
                        "/error-types/"
                        "certificate-not-found"
                    ),
                }),
                None,
                None,
                [errors.ErrDeleteCertificate,
                 errors.ErrCertificateNotFound],
            ),
            (
                "500 internal server error",
                models.DeleteCertificateRequest(
                    certificate_id="123",
                ),
                500,
                json.dumps({
                    "type": "internal_error",
                    "title": "Internal Server Error",
                    "detail": "Error removing certificate",
                    "status": 500,
                }),
                None,
                None,
                [errors.ErrDeleteCertificate],
            ),
            (
                "validation error - "
                "missing CertificateID",
                models.DeleteCertificateRequest(
                    certificate_id="",
                ),
                None,
                None,
                None,
                ("deleting certificate: struct validation: "
                 "CertificateID: cannot be blank"),
                [errors.ErrDeleteCertificate,
                 errors.ErrStructValidation],
            ),
        ],
    )
    def test_delete_certificate(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self, mock_session, client, name, params,
        response_status, response_body, returned_headers,
        expected_error, check_sentinels,
    ):
        """Test delete_certificate mirroring Go scenarios."""
        _ = name  # used for test identification only
        if response_status is not None:
            setup_mock_response(
                mock_session, response_status,
                response_body or "", returned_headers,
            )

        if expected_error is not None:
            with pytest.raises(ValueError) as exc_info:
                client.delete_certificate(params)
            assert str(exc_info.value) == expected_error
            if check_sentinels:
                for sentinel in check_sentinels:
                    assert sentinel in str(exc_info.value)
            return

        if response_status not in (200, 201, 204):
            with pytest.raises(Exception) as exc_info:
                client.delete_certificate(params)
            err = exc_info.value
            if check_sentinels:
                for sentinel in check_sentinels:
                    if isinstance(sentinel, str):
                        assert sentinel in str(err)
                    elif isinstance(sentinel, errors.Error):
                        assert hasattr(err, "api_error")
                        assert err.api_error.is_equivalent(
                            sentinel
                        )
            return

        result = client.delete_certificate(params)
        assert result is not None
        assert isinstance(
            result, models.DeleteCertificateResponse
        )
        if returned_headers:
            rl_limit = returned_headers.get(
                "Akamai-RateLimit-Limit", ""
            )
            if rl_limit and rl_limit.isdigit():
                assert result.limit == int(rl_limit)
                assert result.remaining == int(
                    returned_headers.get(
                        "Akamai-RateLimit-Remaining", "0"
                    )
                )



# =====================================================================
# TestPatchCertificate
# =====================================================================

_PATCH_RENAME_RESPONSE = json.dumps({"accountId": "acc_123", "certificateId": "123", "certificateName": "test 0123456789.-_", "certificateStatus": "CSR_READY", "certificateType": "THIRD_PARTY", "contractId": "A-123", "createdBy": "user", "createdDate": "2025-08-22T09:01:32.607357Z", "csrExpirationDate": "2026-10-24T09:01:34Z", "csrPem": "-----BEGIN CERTIFICATE REQUEST-----\nexample-PEM\n-----END CERTIFICATE REQUEST-----\n", "keySize": "2048", "keyType": "RSA", "modifiedBy": "user", "modifiedDate": "2025-08-22T09:01:32.607358Z", "sans": ["example.com", "www.example.com"], "secureNetwork": "ENHANCED_TLS", "signedCertificateIssuer": None, "signedCertificateNotValidAfterDate": None, "signedCertificateNotValidBeforeDate": None, "signedCertificatePem": None, "signedCertificateSHA256Fingerprint": None, "signedCertificateSerialNumber": None, "subject": {"commonName": "example.com", "country": "US", "locality": "Cambridge", "organization": "ExampleOrg", "state": "Massachusetts"}, "trustChainPem": None})

_PATCH_RESET_NAME_RESPONSE = json.dumps({"accountId": "acc_123", "certificateId": "123", "certificateName": "example.com20250822092651008941", "certificateStatus": "CSR_READY", "certificateType": "THIRD_PARTY", "contractId": "A-123", "createdBy": "user", "createdDate": "2025-08-22T09:01:32.607357Z", "csrExpirationDate": "2026-10-24T09:01:34Z", "csrPem": "-----BEGIN CERTIFICATE REQUEST-----\nexample-PEM\n-----END CERTIFICATE REQUEST-----\n", "keySize": "2048", "keyType": "RSA", "modifiedBy": "user", "modifiedDate": "2025-08-22T09:01:32.607358Z", "sans": ["example.com", "www.example.com"], "secureNetwork": "ENHANCED_TLS", "signedCertificateIssuer": None, "signedCertificateNotValidAfterDate": None, "signedCertificateNotValidBeforeDate": None, "signedCertificatePem": None, "signedCertificateSHA256Fingerprint": None, "signedCertificateSerialNumber": None, "subject": {"commonName": "example.com", "country": "US", "locality": "Cambridge", "organization": "ExampleOrg", "state": "Massachusetts"}, "trustChainPem": None})

_PATCH_SIGNED_CERT_RESPONSE = json.dumps({"accountId": "acc_123", "certificateId": "123", "certificateName": "Certificate-name-rename", "certificateStatus": "READY_FOR_USE", "certificateType": "THIRD_PARTY", "contractId": "A-123", "createdBy": "user", "createdDate": "2025-08-22T09:01:32.607357Z", "csrExpirationDate": "2026-10-24T09:01:34Z", "csrPem": "-----BEGIN CERTIFICATE REQUEST-----\nexample-PEM\n-----END CERTIFICATE REQUEST-----\n", "keySize": "2048", "keyType": "RSA", "modifiedBy": "user", "modifiedDate": "2025-08-22T09:01:32.607358Z", "sans": ["example.com", "www.example.com"], "secureNetwork": "ENHANCED_TLS", "signedCertificateIssuer": "CN=mkcert user (name surname),OU=organization (name surname),O=mkcert development CA", "signedCertificateNotValidAfterDate": "2027-11-22T12:11:31Z", "signedCertificateNotValidBeforeDate": "2025-08-22T11:11:31Z", "signedCertificatePem": "-----BEGIN CERTIFICATE-----\nexample-signed-PEM\n-----END CERTIFICATE-----\n", "signedCertificateSHA256Fingerprint": "4E:69:28:A1:CE:F1:E4:97:CE:39:FE:12:98", "signedCertificateSerialNumber": "a2:84:7d:dc:97:f1", "subject": {"commonName": "example.com", "country": "US", "locality": "Cambridge", "organization": "ExampleOrg", "state": "Massachusetts"}, "trustChainPem": None})

_PATCH_SIGNED_TC_RESPONSE = json.dumps({"accountId": "acc_123", "certificateId": "123", "certificateName": "Certificate-name-rename", "certificateStatus": "READY_FOR_USE", "certificateType": "THIRD_PARTY", "contractId": "A-123", "createdBy": "user", "createdDate": "2025-08-22T09:01:32.607357Z", "csrExpirationDate": "2026-10-24T09:01:34Z", "csrPem": "-----BEGIN CERTIFICATE REQUEST-----\nexample-PEM\n-----END CERTIFICATE REQUEST-----\n", "keySize": "2048", "keyType": "RSA", "modifiedBy": "user", "modifiedDate": "2025-08-22T09:01:32.607358Z", "sans": ["example.com", "www.example.com"], "secureNetwork": "ENHANCED_TLS", "signedCertificateIssuer": "CN=mkcert user (name surname),OU=organization (name surname),O=mkcert development CA", "signedCertificateNotValidAfterDate": "2027-11-22T12:11:31Z", "signedCertificateNotValidBeforeDate": "2025-08-22T11:11:31Z", "signedCertificatePem": "-----BEGIN CERTIFICATE-----\nexample-signed-PEM\n-----END CERTIFICATE-----\n", "signedCertificateSHA256Fingerprint": "4E:69:28:A1:CE:F1:E4:97:CE:39:FE:12:98", "signedCertificateSerialNumber": "a2:84:7d:dc:97:f1", "subject": {"commonName": "example.com", "country": "US", "locality": "Cambridge", "organization": "ExampleOrg", "state": "Massachusetts"}, "trustChainPem": "-----BEGIN CERTIFICATE-----\nexample-trust-chain-PEM\n-----END CERTIFICATE-----\n"})

_PATCH_409_CERT_WARNING_BODY = json.dumps({"data": {"signedCertificatePem": "-----BEGIN CERTIFICATE-----\nexample-signed-PEM\n-----END CERTIFICATE-----\n", "signedCertificates": [{"certificatePem": "-----BEGIN CERTIFICATE-----\nexample-PEM\n-----END CERTIFICATE-----", "createdBy": None, "createdDate": None, "displayName": None, "endDate": "2027-11-22T12:45:19Z", "fingerprint": None, "issuer": "CN=mkcert user (name surname),OU=organization (name surname),O=mkcert development CA", "sans": ["example.com", "www.example.com"], "serialNumber": "1234567890", "signatureAlgorithm": "SHA256WITHRSA", "startDate": "2025-08-22T11:45:19Z", "subject": {"commonName": "example.com", "country": "US", "locality": "Cambridge", "state": "Massachusetts"}, "validation": {"errors": [], "notices": [], "warnings": [{"detail": "Message: Certificate validity period is above the maximum 398 days.. Name: LEAF_CERTIFICATE", "instance": "/error-types/certificate-validation-warning?traceId=123456789", "message": "Certificate validity period is above the maximum 398 days.", "name": "LEAF_CERTIFICATE", "title": "Certificate validation warning.", "type": "/error-types/certificate-validation-warning"}]}}], "trustChain": [], "trustChainPem": None, "validation": {"errors": [], "notices": [], "warnings": [{"detail": "Message: Name: MaxMinExpirationDateValidator Message: RSA certificate expiration is longer than allowed. Must expire within 398 days. Name: UNKNOWN", "instance": "/error-types/certificate-validation-warning?traceId=123456789", "message": "Name: MaxMinExpirationDateValidator Message: RSA certificate expiration is longer than allowed. Must expire within 398 days", "name": "UNKNOWN", "status": 400, "title": "Certificate validation warning.", "type": "/error-types/certificate-validation-warning"}, {"detail": "Message: Name: TrustChainRequiredValidator Message: RSA certificate does not come with a trust chain and this is a non-standard practice. Name: UNKNOWN", "instance": "/error-types/certificate-validation-warning?traceId=123456789", "message": "Name: TrustChainRequiredValidator Message: RSA certificate does not come with a trust chain and this is a non-standard practice", "name": "UNKNOWN", "status": 400, "title": "Certificate validation warning.", "type": "/error-types/certificate-validation-warning"}]}}, "detail": "Warnings detected in one or more of the uploaded certificates.", "instance": "/error-types/upload-certificate-validation-warnings?traceId=123456789", "status": 409, "title": "Validation warnings for uploaded signed certificate(s) and trust chain(s) for one or more key types.", "type": "/error-types/upload-certificate-validation-warnings"})

_PATCH_409_TC_WARNING_BODY = json.dumps({"data": {"signedCertificatePem": "-----BEGIN CERTIFICATE-----\nexample-signed-PEM\n-----END CERTIFICATE-----\n", "signedCertificates": [{"certificatePem": "-----BEGIN CERTIFICATE-----\nexample-PEM\n-----END CERTIFICATE-----", "createdBy": None, "createdDate": None, "displayName": None, "endDate": "2027-11-22T12:45:19Z", "fingerprint": None, "issuer": "CN=mkcert user (name surname),OU=organization (name surname),O=mkcert development CA", "sans": ["example.com", "www.example.com"], "serialNumber": "1234567890", "signatureAlgorithm": "SHA256WITHRSA", "startDate": "2025-08-22T11:45:19Z", "subject": {"commonName": "example.com", "country": "US", "locality": "Cambridge", "organization": None, "state": "Massachusetts"}, "validation": {"errors": [], "notices": [], "warnings": [{"detail": "Message: Certificate validity period is above the maximum 398 days.. Name: LEAF_CERTIFICATE", "instance": "/error-types/certificate-validation-warning?traceId=123456789", "message": "Certificate validity period is above the maximum 398 days.", "name": "LEAF_CERTIFICATE", "title": "Certificate validation warning.", "type": "/error-types/certificate-validation-warning"}]}}], "trustChain": [{"certificatePem": "-----BEGIN CERTIFICATE-----\nexample-trust-chain-PEM\n-----END CERTIFICATE-----", "createdBy": None, "createdDate": None, "displayName": None, "endDate": "2027-11-22T12:45:19Z", "fingerprint": None, "issuer": "CN=mkcert user (name surname),OU=organization (name surname),O=mkcert development CA", "sans": None, "serialNumber": "1234567890", "signatureAlgorithm": "SHA256WITHRSA", "startDate": "2025-08-22T11:45:19Z", "subject": None, "validation": {"errors": [{"detail": "Message: Certificate is not an intermediate trust chain certificate. Name: TRUST_CHAIN_CERTIFICATE", "instance": "/error-types/certificate-validation-failed?traceId=123456789", "message": "Certificate is not an intermediate trust chain certificate.", "name": "TRUST_CHAIN_CERTIFICATE", "title": "Certificate validation error.", "type": "/error-types/certificate-validation-failed"}], "notices": [], "warnings": []}}], "trustChainPem": "-----BEGIN CERTIFICATE-----\nexample-trust-chain-PEM\n-----END CERTIFICATE-----\n", "validation": {"errors": [], "notices": [], "warnings": []}}, "detail": "Errors detected in one or more of the uploaded certificates.", "instance": "/error-types/upload-certificate-validation-failed?traceId=123456789", "status": 400, "title": "Validation failed for uploaded signed certificate(s) and trust chain(s) for one or more key types.", "type": "/error-types/upload-certificate-validation-failed"})

_PATCH_409_NAME_CONFLICT_BODY = json.dumps({"certificateIdentifier": "certificateName", "certificateIdentifierValue": "duplicate-name.com1234567890", "detail": "Certificate with {certificateName}: {duplicate-name.com1234567890} already exists with the current account Id!", "instance": "/error-types/certificate-name-already-in-use?traceId=-123", "status": 409, "title": "Certificate name already in use.", "type": "/error-types/certificate-name-already-in-use"})


class TestPatchCertificate:  # pylint: disable=too-few-public-methods
    """Tests for patch_certificate mirroring Go test scenarios."""

    @pytest.mark.parametrize(
        "name,params,response_status,response_body,"
        "returned_headers,expected_error,check_sentinels",
        [
            (
                "200 OK - only rename with all "
                "allowed characters",
                models.PatchCertificateRequest(
                    certificate_id="123",
                    certificate_name="test 0123456789.-_",
                ),
                200,
                _PATCH_RENAME_RESPONSE,
                _BASE_RATE_LIMIT_HEADERS,
                None,
                None,
            ),
            (
                "200 OK - reset name by providing "
                "empty value",
                models.PatchCertificateRequest(
                    certificate_id="123",
                    certificate_name="",
                ),
                200,
                _PATCH_RESET_NAME_RESPONSE,
                None,
                None,
                None,
            ),
            (
                "200 OK - upload signed certificate "
                "PEM only",
                models.PatchCertificateRequest(
                    certificate_id="123",
                    signed_certificate_pem=(
                        "-----BEGIN CERTIFICATE-----\n"
                        "example-signed-PEM\n"
                        "-----END CERTIFICATE-----\n"
                    ),
                ),
                200,
                _PATCH_SIGNED_CERT_RESPONSE,
                None,
                None,
                None,
            ),
            (
                "200 OK - upload signed certificate "
                "PEM with trust chain",
                models.PatchCertificateRequest(
                    certificate_id="123",
                    signed_certificate_pem=(
                        "-----BEGIN CERTIFICATE-----\n"
                        "example-signed-PEM\n"
                        "-----END CERTIFICATE-----\n"
                    ),
                    trust_chain_pem=(
                        "-----BEGIN CERTIFICATE-----\n"
                        "example-trust-chain-PEM\n"
                        "-----END CERTIFICATE-----\n"
                    ),
                ),
                200,
                _PATCH_SIGNED_TC_RESPONSE,
                None,
                None,
                None,
            ),
            (
                "200 OK - upload signed certificate "
                "with AcknowledgeWarnings query param",
                models.PatchCertificateRequest(
                    certificate_id="123",
                    signed_certificate_pem=(
                        "-----BEGIN CERTIFICATE-----\n"
                        "example-signed-PEM\n"
                        "-----END CERTIFICATE-----\n"
                    ),
                    acknowledge_warnings=True,
                ),
                200,
                _PATCH_SIGNED_CERT_RESPONSE,
                None,
                None,
                None,
            ),
            (
                "200 OK - upload signed certificate "
                "and trust chain PEM with "
                "AcknowledgeWarnings query param "
                "and rename certificate",
                models.PatchCertificateRequest(
                    certificate_id="123",
                    signed_certificate_pem=(
                        "-----BEGIN CERTIFICATE-----\n"
                        "example-signed-PEM\n"
                        "-----END CERTIFICATE-----\n"
                    ),
                    trust_chain_pem=(
                        "-----BEGIN CERTIFICATE-----\n"
                        "example-trust-chain-PEM\n"
                        "-----END CERTIFICATE-----\n"
                    ),
                    certificate_name="Certificate-name-rename",
                    acknowledge_warnings=True,
                ),
                200,
                _PATCH_SIGNED_TC_RESPONSE,
                None,
                None,
                None,
            ),
            (
                "409 OK - warnings in the response "
                "for certificate pem",
                models.PatchCertificateRequest(
                    certificate_id="123",
                    signed_certificate_pem=(
                        "-----BEGIN CERTIFICATE-----\n"
                        "example-signed-PEM\n"
                        "-----END CERTIFICATE-----\n"
                    ),
                ),
                409,
                _PATCH_409_CERT_WARNING_BODY,
                None,
                None,
                [errors.ErrPatchCertificate],
            ),
            (
                "409 OK - warnings in the response "
                "for certificate pem and trust chain",
                models.PatchCertificateRequest(
                    certificate_id="123",
                    signed_certificate_pem=(
                        "-----BEGIN CERTIFICATE-----\n"
                        "example-signed-PEM\n"
                        "-----END CERTIFICATE-----\n"
                    ),
                ),
                409,
                _PATCH_409_TC_WARNING_BODY,
                None,
                None,
                [errors.ErrPatchCertificate],
            ),
            (
                "409 Conflict - name already in use",
                models.PatchCertificateRequest(
                    certificate_id="123",
                    certificate_name="duplicate-name",
                ),
                409,
                _PATCH_409_NAME_CONFLICT_BODY,
                None,
                None,
                [errors.ErrPatchCertificate,
                 errors.ErrCertificateNameInUse],
            ),
            (
                "validation error - name too long",
                models.PatchCertificateRequest(
                    certificate_id="123",
                    certificate_name="A" * 271,
                ),
                None,
                None,
                None,
                ("patching certificate: struct validation: "
                 "CertificateName: the length must be "
                 "no more than 270"),
                [errors.ErrPatchCertificate,
                 errors.ErrStructValidation],
            ),
            (
                "validation error - name contains "
                "invalid characters",
                models.PatchCertificateRequest(
                    certificate_id="123",
                    certificate_name="Invalid@Name",
                ),
                None,
                None,
                None,
                ("patching certificate: struct validation: "
                 "CertificateName: the input can only "
                 "contain digits (1-9), letters (a-z, A-Z),"
                 " spaces, hyphens, periods, "
                 "and underscores."),
                [errors.ErrPatchCertificate,
                 errors.ErrStructValidation],
            ),
            (
                "validation error - missing required "
                "parameters",
                models.PatchCertificateRequest(),
                None,
                None,
                None,
                ("patching certificate: struct validation: "
                 "CertificateID: cannot be blank\n"
                 "required parameters: at least one of "
                 "SignedCertificatePEM or CertificateName "
                 "must be provided"),
                [errors.ErrPatchCertificate,
                 errors.ErrStructValidation],
            ),
            (
                "URL parsing error",
                models.PatchCertificateRequest(
                    certificate_id="123 wrong url",
                ),
                None,
                None,
                None,
                ("patching certificate: struct validation: "
                 "required parameters: at least one of "
                 "SignedCertificatePEM or CertificateName "
                 "must be provided"),
                [errors.ErrPatchCertificate,
                 errors.ErrStructValidation],
            ),
            (
                "500 internal server error",
                models.PatchCertificateRequest(
                    certificate_id="123",
                    certificate_name="New-Certificate-Name",
                ),
                500,
                json.dumps({
                    "type": "internal_error",
                    "title": "Internal Server Error",
                    "detail":
                        "Error removing property hostname",
                    "status": 500,
                }),
                None,
                None,
                [errors.ErrPatchCertificate],
            ),
        ],
    )
    def test_patch_certificate(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self, mock_session, client, name, params,
        response_status, response_body, returned_headers,
        expected_error, check_sentinels,
    ):
        """Test patch_certificate mirroring Go scenarios."""
        _ = name  # used for test identification only
        if response_status is not None:
            setup_mock_response(
                mock_session, response_status,
                response_body or "", returned_headers,
            )

        if expected_error is not None:
            with pytest.raises(ValueError) as exc_info:
                client.patch_certificate(params)
            assert str(exc_info.value) == expected_error
            if check_sentinels:
                for sentinel in check_sentinels:
                    assert sentinel in str(exc_info.value)
            return

        if response_status is not None and (
            response_status < 200 or response_status >= 300
        ):
            with pytest.raises(Exception) as exc_info:
                client.patch_certificate(params)
            err = exc_info.value
            if check_sentinels:
                for sentinel in check_sentinels:
                    if isinstance(sentinel, str):
                        assert sentinel in str(err)
                    elif isinstance(sentinel, errors.Error):
                        assert hasattr(err, "api_error")
                        assert err.api_error.is_equivalent(
                            sentinel
                        )
            return

        result = client.patch_certificate(params)
        assert result is not None
        assert isinstance(
            result, models.PatchCertificateResponse
        )
        assert result.certificate is not None
        assert result.certificate.certificate_id == "123"



# =====================================================================
# TestUpdateCertificate
# =====================================================================

class TestUpdateCertificate:  # pylint: disable=too-few-public-methods
    """Tests for update_certificate mirroring Go test scenarios."""

    @pytest.mark.parametrize(
        "name,params,response_status,response_body,"
        "returned_headers,expected_error,check_sentinels",
        [
            (
                "200 OK - only rename with all "
                "allowed characters",
                models.UpdateCertificateRequest(
                    certificate_id="123",
                    certificate_name="test 0123456789.-_",
                ),
                200,
                _PATCH_RENAME_RESPONSE,
                _BASE_RATE_LIMIT_HEADERS,
                None,
                None,
            ),
            (
                "200 OK - reset name by providing "
                "empty value",
                models.UpdateCertificateRequest(
                    certificate_id="123",
                    certificate_name="",
                ),
                200,
                _PATCH_RESET_NAME_RESPONSE,
                None,
                None,
                None,
            ),
            (
                "200 OK - upload signed certificate "
                "PEM only",
                models.UpdateCertificateRequest(
                    certificate_id="123",
                    signed_certificate_pem=(
                        "-----BEGIN CERTIFICATE-----\n"
                        "example-signed-PEM\n"
                        "-----END CERTIFICATE-----\n"
                    ),
                ),
                200,
                _PATCH_SIGNED_CERT_RESPONSE,
                None,
                None,
                None,
            ),
            (
                "200 OK - upload signed certificate "
                "PEM with trust chain",
                models.UpdateCertificateRequest(
                    certificate_id="123",
                    signed_certificate_pem=(
                        "-----BEGIN CERTIFICATE-----\n"
                        "example-signed-PEM\n"
                        "-----END CERTIFICATE-----\n"
                    ),
                    trust_chain_pem=(
                        "-----BEGIN CERTIFICATE-----\n"
                        "example-trust-chain-PEM\n"
                        "-----END CERTIFICATE-----\n"
                    ),
                ),
                200,
                _PATCH_SIGNED_TC_RESPONSE,
                None,
                None,
                None,
            ),
            (
                "200 OK - upload signed certificate "
                "with AcknowledgeWarnings query param",
                models.UpdateCertificateRequest(
                    certificate_id="123",
                    signed_certificate_pem=(
                        "-----BEGIN CERTIFICATE-----\n"
                        "example-signed-PEM\n"
                        "-----END CERTIFICATE-----\n"
                    ),
                    acknowledge_warnings=True,
                ),
                200,
                _PATCH_SIGNED_CERT_RESPONSE,
                None,
                None,
                None,
            ),
            (
                "200 OK - upload signed certificate "
                "and trust chain PEM with "
                "AcknowledgeWarnings and rename",
                models.UpdateCertificateRequest(
                    certificate_id="123",
                    signed_certificate_pem=(
                        "-----BEGIN CERTIFICATE-----\n"
                        "example-signed-PEM\n"
                        "-----END CERTIFICATE-----\n"
                    ),
                    trust_chain_pem=(
                        "-----BEGIN CERTIFICATE-----\n"
                        "example-trust-chain-PEM\n"
                        "-----END CERTIFICATE-----\n"
                    ),
                    certificate_name=(
                        "Certificate-name-rename"
                    ),
                    acknowledge_warnings=True,
                ),
                200,
                _PATCH_SIGNED_TC_RESPONSE,
                None,
                None,
                None,
            ),
            (
                "409 OK - warnings in the response "
                "for certificate pem",
                models.UpdateCertificateRequest(
                    certificate_id="123",
                    signed_certificate_pem=(
                        "-----BEGIN CERTIFICATE-----\n"
                        "example-signed-PEM\n"
                        "-----END CERTIFICATE-----\n"
                    ),
                ),
                409,
                _PATCH_409_CERT_WARNING_BODY,
                None,
                None,
                [errors.ErrUpdateCertificate],
            ),
            (
                "409 OK - warnings in the response "
                "for certificate pem and trust chain",
                models.UpdateCertificateRequest(
                    certificate_id="123",
                    signed_certificate_pem=(
                        "-----BEGIN CERTIFICATE-----\n"
                        "example-signed-PEM\n"
                        "-----END CERTIFICATE-----\n"
                    ),
                ),
                409,
                _PATCH_409_TC_WARNING_BODY,
                None,
                None,
                [errors.ErrUpdateCertificate],
            ),
            (
                "409 Conflict - name already in use",
                models.UpdateCertificateRequest(
                    certificate_id="123",
                    certificate_name="duplicate-name",
                ),
                409,
                _PATCH_409_NAME_CONFLICT_BODY,
                None,
                None,
                [errors.ErrUpdateCertificate,
                 errors.ErrCertificateNameInUse],
            ),
            (
                "validation error - name too long",
                models.UpdateCertificateRequest(
                    certificate_id="123",
                    certificate_name="A" * 271,
                ),
                None,
                None,
                None,
                ("updating certificate: struct validation: "
                 "CertificateName: the length must be "
                 "no more than 270"),
                [errors.ErrUpdateCertificate,
                 errors.ErrStructValidation],
            ),
            (
                "validation error - name contains "
                "invalid characters",
                models.UpdateCertificateRequest(
                    certificate_id="123",
                    certificate_name="Invalid@Name",
                ),
                None,
                None,
                None,
                ("updating certificate: struct validation: "
                 "CertificateName: the input can only "
                 "contain digits (1-9), letters (a-z, A-Z),"
                 " spaces, hyphens, periods, "
                 "and underscores."),
                [errors.ErrUpdateCertificate,
                 errors.ErrStructValidation],
            ),
            (
                "validation error - missing required "
                "parameters",
                models.UpdateCertificateRequest(),
                None,
                None,
                None,
                ("updating certificate: struct validation: "
                 "CertificateID: cannot be blank"),
                [errors.ErrUpdateCertificate,
                 errors.ErrStructValidation],
            ),
            (
                "500 internal server error",
                models.UpdateCertificateRequest(
                    certificate_id="123",
                    certificate_name="New-Certificate-Name",
                ),
                500,
                json.dumps({
                    "type": "internal_error",
                    "title": "Internal Server Error",
                    "detail":
                        "Error removing property hostname",
                    "status": 500,
                }),
                None,
                None,
                [errors.ErrUpdateCertificate],
            ),
        ],
    )
    def test_update_certificate(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self, mock_session, client, name, params,
        response_status, response_body, returned_headers,
        expected_error, check_sentinels,
    ):
        """Test update_certificate mirroring Go scenarios."""
        _ = name  # used for test identification only
        if response_status is not None:
            setup_mock_response(
                mock_session, response_status,
                response_body or "", returned_headers,
            )

        if expected_error is not None:
            with pytest.raises(ValueError) as exc_info:
                client.update_certificate(params)
            assert str(exc_info.value) == expected_error
            if check_sentinels:
                for sentinel in check_sentinels:
                    assert sentinel in str(exc_info.value)
            return

        if response_status is not None and (
            response_status < 200 or response_status >= 300
        ):
            with pytest.raises(Exception) as exc_info:
                client.update_certificate(params)
            err = exc_info.value
            if check_sentinels:
                for sentinel in check_sentinels:
                    if isinstance(sentinel, str):
                        assert sentinel in str(err)
                    elif isinstance(sentinel, errors.Error):
                        assert hasattr(err, "api_error")
                        assert err.api_error.is_equivalent(
                            sentinel
                        )
            return

        result = client.update_certificate(params)
        assert result is not None
        assert isinstance(
            result, models.UpdateCertificateResponse
        )
        assert result.certificate is not None
        assert result.certificate.certificate_id == "123"



# =====================================================================
# Response body constants — list certificates
# =====================================================================

_LIST_CERT1 = {
    "accountId": "test-account-id",
    "certificateId": "cert1_1234",
    "certificateName": "Test Certificate1",
    "certificateStatus": "ACTIVE",
    "certificateType": "THIRD_PARTY",
    "createdBy": "jkowalski",
    "createdDate": "2025-08-22T09:01:32.607357Z",
    "modifiedBy": "jkowalski",
    "modifiedDate": "2025-08-22T09:01:33.607357Z",
    "csrExpirationDate": "2026-10-24T09:01:34Z",
    "keySize": "2048",
    "keyType": "RSA",
    "sans": ["test-example.com", "www.test-example.com"],
    "secureNetwork": "ENHANCED_TLS",
    "signedCertificateIssuer": (
        "CN=mkcert user (name surname),"
        "OU=organization (name surname),"
        "O=mkcert development CA"
    ),
    "signedCertificateNotValidAfterDate": "2027-11-22T12:11:31Z",
    "signedCertificateNotValidBeforeDate": "2025-08-22T11:11:31Z",
    "subject": {
        "commonName": "test-example.com",
        "country": "US",
        "locality": "Cambridge",
        "state": "Massachusetts",
    },
    "trustChainPem": None,
}

_LIST_CERT2 = {
    "accountId": "test-account-id",
    "certificateId": "cert2_1234",
    "certificateName": "Test Certificate2",
    "certificateStatus": "READY_FOR_USE",
    "certificateType": "THIRD_PARTY",
    "createdBy": "jkowalski",
    "createdDate": "2025-09-15T10:20:30.123456Z",
    "modifiedBy": "jkowalski",
    "modifiedDate": "2025-08-22T09:01:33.607357Z",
    "csrExpirationDate": "2026-10-24T09:01:34Z",
    "keySize": "P-256",
    "keyType": "ECDSA",
    "sans": ["test2-example.com"],
    "secureNetwork": "ENHANCED_TLS",
    "signedCertificateIssuer": (
        "O=test organization NY,L=New York,ST=NY,C=US"
    ),
    "signedCertificateNotValidAfterDate": "2027-11-22T12:11:31Z",
    "signedCertificateNotValidBeforeDate": "2025-08-22T11:11:31Z",
    "subject": {
        "commonName": "test2-example.com",
        "country": "US",
        "locality": "New York",
        "organization": "test organization NY",
        "state": "New York",
    },
    "trustChainPem": (
        "-----BEGIN CERTIFICATE-----\n"
        "example-trust-chain-PEM\n"
        "-----END CERTIFICATE-----\n"
    ),
}

_LIST_CERT3 = {
    "accountId": "test-account-id",
    "certificateId": "cert3_1234",
    "certificateName": "Test Certificate3",
    "certificateStatus": "READY_FOR_USE",
    "certificateType": "THIRD_PARTY",
    "createdBy": "jkowalski",
    "createdDate": "2025-10-05T11:30:45.654321Z",
    "modifiedBy": "jkowalski",
    "modifiedDate": "2025-08-22T09:01:33.607357Z",
    "csrExpirationDate": "2026-10-24T09:01:34Z",
    "keySize": "2048",
    "keyType": "RSA",
    "sans": ["test3-example.com", "www.test3-example.com"],
    "secureNetwork": "ENHANCED_TLS",
    "signedCertificateIssuer": (
        "CN=mkcert user (name surname),"
        "OU=organization (name surname),"
        "O=mkcert development CA"
    ),
    "signedCertificateNotValidAfterDate": "2027-11-22T12:11:31Z",
    "signedCertificateNotValidBeforeDate": "2025-08-22T11:11:31Z",
    "subject": {
        "commonName": "test3-example.com",
        "country": "US",
        "locality": "San Francisco",
        "state": "California",
    },
    "trustChainPem": None,
}

_LIST_CERT4 = {
    "accountId": "test-account-id",
    "certificateId": "cert4_1234",
    "certificateName": "Test Certificate4",
    "certificateStatus": "READY_FOR_USE",
    "certificateType": "THIRD_PARTY",
    "createdBy": "jkowalski",
    "createdDate": "2023-10-05T11:30:45.654321Z",
    "modifiedBy": "jkowalski",
    "modifiedDate": "2025-08-22T09:01:33.607357Z",
    "csrExpirationDate": "2024-10-24T09:01:34Z",
    "keySize": "P-256",
    "keyType": "ECDSA",
    "sans": ["test4-example.com", "www.test4-example.com"],
    "secureNetwork": "ENHANCED_TLS",
    "signedCertificateIssuer": (
        "O=test organization LA,"
        "L=Los Angeles,ST=California,C=US"
    ),
    "signedCertificateNotValidAfterDate": "2027-11-22T12:11:31Z",
    "signedCertificateNotValidBeforeDate": "2025-08-22T11:11:31Z",
    "subject": {
        "commonName": "test4-example.com",
        "country": "US",
        "locality": "Los Angeles",
        "organization": "test organization LA",
        "state": "California",
    },
    "trustChainPem": None,
}

_LIST_LINKS_DEFAULT = {
    "self": "/ccm/v1/certificates?page=1&pageSize=10",
    "next": None,
    "previous": None,
}


def _list_resp_body(certs, links=None, meta=None):
    """Build a list certificates response body dict."""
    return {
        "certificates": certs,
        "links": links or _LIST_LINKS_DEFAULT,
        "metadata": meta or {"totalItems": len(certs), "totalPages": 1},
    }


# =====================================================================
# TestListCertificates
# =====================================================================


class TestListCertificates:
    """Tests for Client.list_certificates().

    Mirrors Go ``TestListCertificates`` from
    ``certificates_test.go`` lines 3206-4419.
    """

    def test_list_certificates(  # pylint: disable=too-many-branches,too-many-statements
        self, client, mock_session
    ):
        """200 OK - list certificates with no params."""
        body = _list_resp_body(
            [_LIST_CERT1, _LIST_CERT2, _LIST_CERT3, _LIST_CERT4],
            meta={"totalItems": 4, "totalPages": 1},
        )
        setup_mock_response(
            mock_session, 200, body,
            headers={
                "Akamai-RateLimit-Limit": "60",
                "Akamai-RateLimit-Remaining": "59",
            },
        )
        params = models.ListCertificatesRequest()
        result = client.list_certificates(params)

        assert result is not None
        assert isinstance(
            result, models.ListCertificatesResponse
        )
        assert len(result.certificates) == 4
        c1 = result.certificates[0]
        assert isinstance(c1, models.Certificate)
        assert c1.certificate_id == "cert1_1234"
        assert c1.certificate_name == "Test Certificate1"
        assert c1.certificate_status == "ACTIVE"
        assert c1.key_type == "RSA"
        assert c1.key_size == "2048"
        assert c1.sans == ["test-example.com", "www.test-example.com"]
        assert c1.subject is not None
        assert isinstance(c1.subject, models.Subject)
        assert c1.subject.common_name == "test-example.com"
        assert c1.trust_chain_pem is None

        c4 = result.certificates[3]
        assert c4.certificate_id == "cert4_1234"
        assert c4.key_type == "ECDSA"
        assert c4.key_size == "P-256"

        assert result.links is not None
        assert isinstance(result.links, models.Links)
        assert result.links.self_link == (
            "/ccm/v1/certificates?page=1&pageSize=10"
        )
        assert result.links.next is None
        assert result.links.previous is None
        assert result.metadata is not None
        assert result.metadata.total_items == 4
        assert result.metadata.total_pages == 1
        assert result.rate_limits is not None
        assert isinstance(
            result.rate_limits, models.RateLimitsMetadata
        )
        assert result.rate_limits.limit == 60
        assert result.rate_limits.remaining == 59

    def test_list_with_domain_filtering(self, client, mock_session):
        """200 OK - with domain filtering."""
        cert3_csr = dict(_LIST_CERT3)
        cert3_csr["certificateStatus"] = "CSR_READY"
        body = _list_resp_body(
            [cert3_csr], meta={"totalItems": 1, "totalPages": 1},
        )
        setup_mock_response(mock_session, 200, body)
        params = models.ListCertificatesRequest(
            contract_id="A-123",
            group_id="1234",
            domain="test3-example.com",
        )
        result = client.list_certificates(params)
        assert len(result.certificates) == 1
        assert result.certificates[0].certificate_id == "cert3_1234"
        assert result.certificates[0].certificate_status == "CSR_READY"

        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/ccm/v1/certificates"
        kw_params = call_args[1].get(
            "params", call_args[0][3]
            if len(call_args[0]) > 3 else None
        )
        if kw_params is not None:
            assert kw_params.get("contractId") == "A-123"
            assert kw_params.get("groupId") == "1234"
            assert kw_params.get("domain") == "test3-example.com"

    def test_list_with_status_filtering(self, client, mock_session):
        """200 OK - with status filtering."""
        cert3_status = dict(_LIST_CERT3)
        cert3_status["modifiedDate"] = (
            "2025-10-05T11:33:45.654321Z"
        )
        body = _list_resp_body(
            [_LIST_CERT1, cert3_status],
            meta={"totalItems": 3, "totalPages": 1},
        )
        setup_mock_response(mock_session, 200, body)
        params = models.ListCertificatesRequest(
            certificate_status=["ACTIVE", "READY_FOR_USE"],
        )
        result = client.list_certificates(params)
        assert len(result.certificates) == 2
        assert result.certificates[0].certificate_status == "ACTIVE"
        assert (
            result.certificates[1].certificate_status == "READY_FOR_USE"
        )

    def test_list_with_certificate_name_filtering(
        self, client, mock_session
    ):
        """200 OK - with certificate name filtering."""
        body = _list_resp_body(
            [_LIST_CERT1], meta={"totalItems": 1, "totalPages": 1},
        )
        setup_mock_response(mock_session, 200, body)
        params = models.ListCertificatesRequest(
            certificate_name="Test Certificate1",
        )
        result = client.list_certificates(params)
        assert len(result.certificates) == 1
        assert (
            result.certificates[0].certificate_name == "Test Certificate1"
        )

    def test_list_with_include_materials_and_issuer(
        self, client, mock_session
    ):
        """200 OK - includeCertificateMaterials + issuer filtering."""
        cert2_mat = dict(_LIST_CERT2)
        cert2_mat["signedCertificatePem"] = (
            "-----BEGIN CERTIFICATE-----\n"
            "example-signed-PEM\n"
            "-----END CERTIFICATE-----\n"
        )
        cert2_mat["signedCertificateSha256Fingerprint"] = (
            "4E:69:28:A1:CE:F1:E4:97:CE:39:FE:12:98"
        )
        cert2_mat["signedCertificateSerialNumber"] = (
            "a2:84:7d:dc:97:f1"
        )
        cert4_mat = dict(_LIST_CERT4)
        cert4_mat["csrPem"] = (
            "-----BEGIN CERTIFICATE REQUEST-----\n"
            "example-PEM\n"
            "-----END CERTIFICATE REQUEST-----\n"
        )
        cert4_mat["signedCertificatePem"] = (
            "-----BEGIN CERTIFICATE-----\n"
            "example-signed-PEM\n"
            "-----END CERTIFICATE-----\n"
        )
        cert4_mat["signedCertificateSha256Fingerprint"] = (
            "4E:69:28:A1:CE:F1:E4:97:CE:39:FE:12:98"
        )
        cert4_mat["signedCertificateSerialNumber"] = (
            "a2:84:7d:dc:97:f1"
        )
        body = _list_resp_body(
            [cert2_mat, cert4_mat],
            meta={"totalItems": 3, "totalPages": 1},
        )
        setup_mock_response(mock_session, 200, body)
        params = models.ListCertificatesRequest(
            include_certificate_materials=True,
            issuer="test organization",
        )
        result = client.list_certificates(params)
        assert len(result.certificates) == 2
        c2 = result.certificates[0]
        assert c2.certificate_id == "cert2_1234"
        assert c2.signed_certificate_pem is not None
        assert c2.signed_certificate_serial_number == (
            "a2:84:7d:dc:97:f1"
        )
        c4 = result.certificates[1]
        assert c4.certificate_id == "cert4_1234"
        assert c4.csr_pem == (
            "-----BEGIN CERTIFICATE REQUEST-----\n"
            "example-PEM\n"
            "-----END CERTIFICATE REQUEST-----\n"
        )

    def test_list_with_expiring_in_days_negative(
        self, client, mock_session
    ):
        """200 OK - expiringInDays set to -1 for expired certs."""
        cert4_exp = dict(_LIST_CERT4)
        cert4_exp["csrPem"] = (
            "-----BEGIN CERTIFICATE REQUEST-----\n"
            "example-PEM\n"
            "-----END CERTIFICATE REQUEST-----\n"
        )
        body = _list_resp_body(
            [cert4_exp], meta={"totalItems": 1, "totalPages": 1},
        )
        setup_mock_response(mock_session, 200, body)
        params = models.ListCertificatesRequest(
            expiring_in_days=-1,
        )
        result = client.list_certificates(params)
        assert len(result.certificates) == 1
        assert result.certificates[0].certificate_id == "cert4_1234"

    def test_list_with_pagination_and_sorting(
        self, client, mock_session
    ):
        """200 OK - pagination and sorting by certificate name."""
        cert2_pag = dict(_LIST_CERT2)
        cert2_pag["modifiedDate"] = "2025-09-15T10:20:33.123456Z"
        cert2_pag["subject"] = {
            "commonName": "test2-example.com",
            "country": "US",
            "locality": "New York",
            "organization": "test organization",
            "state": "New York",
        }
        cert2_pag["signedCertificateIssuer"] = (
            "O=test organization,L=New York,ST=NY,C=US"
        )
        body = {
            "certificates": [cert2_pag, _LIST_CERT1],
            "links": {
                "self": (
                    "/ccm/v1/certificates"
                    "?sort=-certificateName&page=2&pageSize=2"
                ),
                "next": None,
                "previous": (
                    "/ccm/v1/certificates"
                    "?sort=-certificateName&page=1&pageSize=2"
                ),
            },
            "metadata": {"totalItems": 4, "totalPages": 2},
        }
        setup_mock_response(mock_session, 200, body)
        params = models.ListCertificatesRequest(
            page_size=2, page=2, sort="-certificateName",
        )
        result = client.list_certificates(params)
        assert len(result.certificates) == 2
        assert result.certificates[0].certificate_id == "cert2_1234"
        assert result.certificates[1].certificate_id == "cert1_1234"
        assert result.links is not None
        assert result.links.previous is not None
        assert result.metadata.total_items == 4
        assert result.metadata.total_pages == 2

    def test_list_with_pagination_and_key_type(
        self, client, mock_session
    ):
        """200 OK - pagination with keyType=RSA filtering."""
        body = {
            "certificates": [_LIST_CERT1],
            "links": {
                "self": (
                    "/ccm/v1/certificates"
                    "?keyType=RSA&page=1&pageSize=1"
                ),
                "next": (
                    "/ccm/v1/certificates"
                    "?keyType=RSA&page=2&pageSize=1"
                ),
                "previous": None,
            },
            "metadata": {"totalItems": 2, "totalPages": 2},
        }
        setup_mock_response(mock_session, 200, body)
        params = models.ListCertificatesRequest(
            key_type="RSA", page_size=1, page=1,
        )
        result = client.list_certificates(params)
        assert len(result.certificates) == 1
        assert result.certificates[0].key_type == "RSA"
        assert result.links.next is not None
        assert result.metadata.total_items == 2
        assert result.metadata.total_pages == 2

    def test_list_validation_invalid_status(self, client):
        """Validation error - invalid certificate status."""
        params = models.ListCertificatesRequest(
            certificate_status=["INVALID_STATUS"],
        )
        with pytest.raises(ValueError) as exc_info:
            client.list_certificates(params)
        err_msg = str(exc_info.value)
        assert errors.ErrListCertificates in err_msg
        assert errors.ErrStructValidation in err_msg
        assert "INVALID_STATUS" in err_msg

    def test_list_validation_invalid_key_type(self, client):
        """Validation error - invalid key type."""
        params = models.ListCertificatesRequest(
            key_type="INVALID_KEY",
        )
        with pytest.raises(ValueError) as exc_info:
            client.list_certificates(params)
        err_msg = str(exc_info.value)
        assert errors.ErrListCertificates in err_msg
        assert errors.ErrStructValidation in err_msg
        assert "INVALID_KEY" in err_msg

    def test_list_validation_page_size_less_than_1(self, client):
        """Validation error - page size less than 1."""
        params = models.ListCertificatesRequest(page_size=-1)
        with pytest.raises(ValueError) as exc_info:
            client.list_certificates(params)
        err_msg = str(exc_info.value)
        assert errors.ErrListCertificates in err_msg
        assert "PageSize" in err_msg
        assert "must be 1 or greater" in err_msg

    def test_list_validation_page_size_greater_than_100(
        self, client
    ):
        """Validation error - page size greater than 100."""
        params = models.ListCertificatesRequest(page_size=101)
        with pytest.raises(ValueError) as exc_info:
            client.list_certificates(params)
        err_msg = str(exc_info.value)
        assert errors.ErrListCertificates in err_msg
        assert "PageSize" in err_msg
        assert "cannot be greater than 100" in err_msg

    def test_list_validation_page_less_than_1(self, client):
        """Validation error - page value less than 1."""
        params = models.ListCertificatesRequest(page=-1)
        with pytest.raises(ValueError) as exc_info:
            client.list_certificates(params)
        err_msg = str(exc_info.value)
        assert errors.ErrListCertificates in err_msg
        assert "Page" in err_msg
        assert "must be 1 or greater" in err_msg

    def test_list_validation_invalid_sort_field(self, client):
        """Validation error - invalid field for sort."""
        params = models.ListCertificatesRequest(sort="invalid_sort")
        with pytest.raises(ValueError) as exc_info:
            client.list_certificates(params)
        err_msg = str(exc_info.value)
        assert errors.ErrListCertificates in err_msg
        assert "Sort" in err_msg

    def test_list_validation_invalid_sort_prefix(self, client):
        """Validation error - invalid prefix for sort."""
        params = models.ListCertificatesRequest(sort="*createdDate")
        with pytest.raises(ValueError) as exc_info:
            client.list_certificates(params)
        err_msg = str(exc_info.value)
        assert errors.ErrListCertificates in err_msg
        assert "Sort" in err_msg

    def test_list_500_error(self, client, mock_session):
        """500 internal server error."""
        error_body = {
            "type": "internal_error",
            "title": "Internal Server Error",
            "detail": "Error retrieving certificates",
            "status": 500,
        }
        setup_mock_response(mock_session, 500, error_body)
        params = models.ListCertificatesRequest()
        with pytest.raises(Exception) as exc_info:
            client.list_certificates(params)
        err = exc_info.value
        assert errors.ErrListCertificates in str(err)



# =====================================================================
# TestListCertificateBindings
# =====================================================================

_BINDINGS_RESPONSE_BODY = {
    "bindings": [
        {
            "certificateId": 123456,
            "hostname": "www.example.com",
            "network": "PRODUCTION",
            "resourceType": "CDN_HOSTNAME",
        },
        {
            "certificateId": "654321",
            "hostname": "secure.example.com",
            "network": "STAGING",
            "resourceType": "CDN_HOSTNAME",
        },
        {
            "certificateId": "789012",
            "hostname": "api.example.com",
            "network": "PRODUCTION",
            "resourceType": "CDN_HOSTNAME",
        },
    ],
    "links": {
        "next": (
            "https://api.example.com/v1/certificates/123"
            "/certificate-bindings?page=2&pageSize=10"
        ),
        "previous": None,
        "self": (
            "https://api.example.com/v1/certificates/123"
            "/certificate-bindings?page=1&pageSize=10"
        ),
    },
}

_BINDINGS_PAGING_BODY = {
    "bindings": [
        {
            "certificateId": "789012",
            "hostname": "api.example.com",
            "network": "PRODUCTION",
            "resourceType": "CDN_HOSTNAME",
        },
    ],
    "links": {
        "next": None,
        "previous": (
            "https://api.example.com/v1/certificates/123"
            "/certificate-bindings?page=2&pageSize=1"
        ),
        "self": (
            "https://api.example.com/v1/certificates/123"
            "/certificate-bindings?page=3&pageSize=1"
        ),
    },
}


class TestListCertificateBindings:
    """Tests for Client.list_certificate_bindings().

    Mirrors Go ``TestListCertificateBindings`` from
    ``bindings_test.go`` lines 15-263.
    """

    def test_list_certificate_bindings(
        self, client, mock_session
    ):
        """200 - fetch of certificate bindings successful."""
        setup_mock_response(
            mock_session, 200, _BINDINGS_RESPONSE_BODY,
            headers={
                "Akamai-RateLimit-Limit": "60",
                "Akamai-RateLimit-Remaining": "59",
            },
        )
        params = models.ListCertificateBindingsRequest(
            certificate_id="123",
        )
        result = client.list_certificate_bindings(params)
        assert result is not None
        assert isinstance(
            result,
            models.ListCertificateBindingsResponse,
        )
        assert len(result.bindings) == 3
        b1 = result.bindings[0]
        assert isinstance(b1, models.CertificateBinding)
        assert b1.hostname == "www.example.com"
        assert b1.network == "PRODUCTION"
        assert b1.resource_type == "CDN_HOSTNAME"
        b2 = result.bindings[1]
        assert b2.hostname == "secure.example.com"
        assert b2.network == "STAGING"
        b3 = result.bindings[2]
        assert b3.hostname == "api.example.com"

        assert result.links is not None
        assert isinstance(result.links, models.Links)
        assert result.links.next is not None
        assert result.links.previous is None

    def test_list_certificate_bindings_with_paging(
        self, client, mock_session
    ):
        """200 - fetch with paging."""
        setup_mock_response(
            mock_session, 200, _BINDINGS_PAGING_BODY,
        )
        params = models.ListCertificateBindingsRequest(
            certificate_id="123",
            page=3,
            page_size=1,
        )
        result = client.list_certificate_bindings(params)
        assert len(result.bindings) == 1
        assert result.bindings[0].hostname == "api.example.com"
        assert result.links is not None
        assert result.links.next is None
        assert result.links.previous is not None

    def test_list_certificate_bindings_404(
        self, client, mock_session
    ):
        """404 resource not found - certificate not found."""
        error_body = {
            "certificateIdentifier": "certificateId",
            "certificateIdentifierValue": "1234",
            "detail": (
                "Certificate with {certificateId}:"
                " {1234} is not found."
            ),
            "instance": (
                "/error-types/certificate-not-found?traceId=-11111"
            ),
            "status": 404,
            "title": "Certificate is not found.",
            "type": "/error-types/certificate-not-found",
        }
        setup_mock_response(mock_session, 404, error_body)
        params = models.ListCertificateBindingsRequest(
            certificate_id="1234",
        )
        with pytest.raises(Exception) as exc_info:
            client.list_certificate_bindings(params)
        err = exc_info.value
        assert errors.ErrListCertificateBindings in str(err)
        if hasattr(err, "api_error"):
            assert err.api_error.is_equivalent(
                errors.ErrCertificateNotFound
            )

    def test_list_certificate_bindings_500(
        self, client, mock_session
    ):
        """500 internal server error."""
        error_body = {
            "type": "internal_error",
            "title": "Internal Server Error",
            "detail": "Error removing certificate",
            "status": 500,
        }
        setup_mock_response(mock_session, 500, error_body)
        params = models.ListCertificateBindingsRequest(
            certificate_id="123",
        )
        with pytest.raises(Exception) as exc_info:
            client.list_certificate_bindings(params)
        assert errors.ErrListCertificateBindings in str(
            exc_info.value
        )

    def test_list_certificate_bindings_missing_id(self, client):
        """Validation error - missing CertificateID."""
        params = models.ListCertificateBindingsRequest()
        with pytest.raises(ValueError) as exc_info:
            client.list_certificate_bindings(params)
        err_msg = str(exc_info.value)
        assert errors.ErrListCertificateBindings in err_msg
        assert errors.ErrStructValidation in err_msg
        assert "CertificateID" in err_msg
        assert "cannot be blank" in err_msg

    def test_list_certificate_bindings_page_size_lt_1(
        self, client
    ):
        """Validation error - page size less than 1."""
        params = models.ListCertificateBindingsRequest(
            certificate_id="123", page_size=-1,
        )
        with pytest.raises(ValueError) as exc_info:
            client.list_certificate_bindings(params)
        err_msg = str(exc_info.value)
        assert "PageSize" in err_msg
        assert "must be 1 or greater" in err_msg

    def test_list_certificate_bindings_page_size_gt_100(
        self, client
    ):
        """Validation error - page size greater than 100."""
        params = models.ListCertificateBindingsRequest(
            certificate_id="123", page_size=101,
        )
        with pytest.raises(ValueError) as exc_info:
            client.list_certificate_bindings(params)
        err_msg = str(exc_info.value)
        assert "PageSize" in err_msg
        assert "cannot be greater than 100" in err_msg

    def test_list_certificate_bindings_page_lt_1(
        self, client
    ):
        """Validation error - page value less than 1."""
        params = models.ListCertificateBindingsRequest(
            certificate_id="123", page=-1,
        )
        with pytest.raises(ValueError) as exc_info:
            client.list_certificate_bindings(params)
        err_msg = str(exc_info.value)
        assert "Page" in err_msg
        assert "must be 1 or greater" in err_msg


# =====================================================================
# TestListBindings
# =====================================================================

_LIST_BINDINGS_BODY = {
    "bindings": [
        {
            "certificateId": 123456,
            "hostname": "www.example.com",
            "network": "PRODUCTION",
            "resourceType": "CDN_HOSTNAME",
        },
        {
            "certificateId": "654321",
            "hostname": "secure.example.com",
            "network": "STAGING",
            "resourceType": "CDN_HOSTNAME",
        },
        {
            "certificateId": "789012",
            "hostname": "api.example.com",
            "network": "PRODUCTION",
            "resourceType": "CDN_HOSTNAME",
        },
    ],
    "links": {
        "next": (
            "https://api.example.com/v1"
            "/certificate-bindings?page=2&pageSize=10"
        ),
        "previous": None,
        "self": (
            "https://api.example.com/v1"
            "/certificate-bindings?page=1&pageSize=10"
        ),
    },
}

_LIST_BINDINGS_PAGING_BODY = {
    "bindings": [
        {
            "certificateId": "789012",
            "hostname": "api.example.com",
            "network": "PRODUCTION",
            "resourceType": "CDN_HOSTNAME",
        },
    ],
    "links": {
        "next": None,
        "previous": (
            "https://api.example.com/v1"
            "/certificate-bindings?page=2&pageSize=1"
        ),
        "self": (
            "https://api.example.com/v1"
            "/certificate-bindings?page=3&pageSize=1"
        ),
    },
}


class TestListBindings:
    """Tests for Client.list_bindings().

    Mirrors Go ``TestListBindings`` from
    ``bindings_test.go`` lines 265-548.
    """

    def test_list_bindings(self, client, mock_session):
        """200 - fetch of bindings successful."""
        setup_mock_response(
            mock_session, 200, _LIST_BINDINGS_BODY,
            headers={
                "Akamai-RateLimit-Limit": "60",
                "Akamai-RateLimit-Remaining": "59",
            },
        )
        params = models.ListBindingsRequest()
        result = client.list_bindings(params)
        assert result is not None
        assert isinstance(
            result, models.ListBindingsResponse
        )
        assert len(result.bindings) == 3
        assert result.bindings[0].hostname == "www.example.com"
        assert result.bindings[0].network == "PRODUCTION"
        assert result.bindings[1].hostname == "secure.example.com"
        assert result.bindings[1].network == "STAGING"
        assert result.bindings[2].hostname == "api.example.com"

        assert result.links is not None
        assert result.links.next is not None
        assert result.links.previous is None

    def test_list_bindings_with_paging(
        self, client, mock_session
    ):
        """200 - fetch of bindings with paging successful."""
        setup_mock_response(
            mock_session, 200, _LIST_BINDINGS_PAGING_BODY,
        )
        params = models.ListBindingsRequest(page=3, page_size=1)
        result = client.list_bindings(params)
        assert len(result.bindings) == 1
        assert result.bindings[0].hostname == "api.example.com"
        assert result.links.next is None
        assert result.links.previous is not None

    def test_list_bindings_with_all_filters(
        self, client, mock_session
    ):
        """200 - fetch of bindings with all filters."""
        setup_mock_response(
            mock_session, 200, _LIST_BINDINGS_PAGING_BODY,
        )
        params = models.ListBindingsRequest(
            contract_id="12345",
            group_id="999",
            domain="api.example.com",
            expiring_in_days=30,
            network="PRODUCTION",
            page=3,
            page_size=1,
        )
        result = client.list_bindings(params)
        assert len(result.bindings) == 1
        assert result.bindings[0].hostname == "api.example.com"

        call_args = mock_session.exec.call_args
        kw_params = call_args[1].get("params")
        if kw_params is not None:
            assert kw_params.get("contractId") == "12345"
            assert kw_params.get("groupId") == "999"
            assert kw_params.get("domain") == "api.example.com"
            assert kw_params.get("expiringInDays") == "30"
            assert kw_params.get("network") == "PRODUCTION"
            assert kw_params.get("page") == "3"
            assert kw_params.get("pageSize") == "1"

    def test_list_bindings_empty_response(
        self, client, mock_session
    ):
        """200 - empty response."""
        body = {
            "bindings": [],
            "links": {
                "next": None,
                "previous": None,
                "self": None,
            },
        }
        setup_mock_response(mock_session, 200, body)
        params = models.ListBindingsRequest(
            contract_id="12345",
            group_id="999",
            domain="foo.example.com",
            expiring_in_days=30,
            network="PRODUCTION",
        )
        result = client.list_bindings(params)
        assert len(result.bindings) == 0

    def test_list_bindings_500_error(
        self, client, mock_session
    ):
        """500 internal server error."""
        error_body = {
            "instance": (
                "/error-types/internal-error?traceId=-11111"
            ),
            "status": 500,
            "title": "An unexpected error occurred.",
            "type": "/error-types/internal-error",
        }
        setup_mock_response(mock_session, 500, error_body)
        params = models.ListBindingsRequest()
        with pytest.raises(Exception) as exc_info:
            client.list_bindings(params)
        assert errors.ErrListBindings in str(exc_info.value)

    def test_list_bindings_invalid_network(self, client):
        """Validation error - invalid network."""
        params = models.ListBindingsRequest(
            page_size=1, network="foo",
        )
        with pytest.raises(ValueError) as exc_info:
            client.list_bindings(params)
        err_msg = str(exc_info.value)
        assert errors.ErrListBindings in err_msg
        assert "Network" in err_msg
        assert "STAGING" in err_msg or "PRODUCTION" in err_msg

    def test_list_bindings_page_size_lt_1(self, client):
        """Validation error - page size less than 1."""
        params = models.ListBindingsRequest(page_size=-1)
        with pytest.raises(ValueError) as exc_info:
            client.list_bindings(params)
        err_msg = str(exc_info.value)
        assert "PageSize" in err_msg
        assert "must be 1 or greater" in err_msg

    def test_list_bindings_page_size_gt_100(self, client):
        """Validation error - page size greater than 100."""
        params = models.ListBindingsRequest(page_size=101)
        with pytest.raises(ValueError) as exc_info:
            client.list_bindings(params)
        err_msg = str(exc_info.value)
        assert "PageSize" in err_msg
        assert "cannot be greater than 100" in err_msg

    def test_list_bindings_page_lt_1(self, client):
        """Validation error - page value less than 1."""
        params = models.ListBindingsRequest(page=-1)
        with pytest.raises(ValueError) as exc_info:
            client.list_bindings(params)
        err_msg = str(exc_info.value)
        assert "Page" in err_msg
        assert "must be 1 or greater" in err_msg
