# pylint: disable=missing-function-docstring,too-many-lines
"""Unit tests for the CPS (Certificate Provisioning System) API client.

Mirrors all test scenarios from Go ``pkg/cps/*_test.go`` files (12 files)
consolidated into a single pytest module.
"""

import pytest

from akamai.edgegrid.cps.cps import CPSClient
from akamai.edgegrid.cps import models
from akamai.edgegrid.cps import errors as cps_errors

# conftest auto-discovers fixtures (mock_session, cps_client).
# Helper functions are imported explicitly.
from akamai.edgegrid.cps.test.conftest import (
    configure_mock_session,
    make_mock_response,
)


# ===================================================================
# TestClient — mirrors Go TestClient from cps_test.go (62 lines)
# ===================================================================


class TestClient:
    """Verify CPSClient construction.

    Mirrors Go ``TestClient`` from ``cps_test.go``.
    """

    def test_client_creation_default(self, cps_client):
        assert cps_client is not None

    def test_client_with_session(self, mock_session):
        client = CPSClient(mock_session)
        assert client is not None


# ===================================================================
# TestGetChangeStatus — mirrors Go TestGetChangeStatus
# from changes_test.go (lines 14-117)
# ===================================================================


class TestGetChangeStatus:
    """Verify ``get_change_status`` endpoint.

    Mirrors Go ``TestGetChangeStatus`` from ``changes_test.go``.
    """

    def test_200_ok(self, cps_client, mock_session):
        response_body = {
            "statusInfo": {
                "status": "wait-upload-third-party",
                "state": "awaiting-input",
                "description": (
                    "Waiting for you to upload and submit your "
                    "third party certificate and trust chain."
                ),
                "error": None,
                "deploymentSchedule": {
                    "notBefore": None,
                    "notAfter": None,
                },
            },
            "allowedInput": [
                {
                    "type": "third-party-certificate",
                    "requiredToProceed": True,
                    "info": (
                        "/cps/v2/enrollments/1/changes/2"
                        "/input/info/third-party-csr"
                    ),
                    "update": (
                        "/cps/v2/enrollments/1/changes/2"
                        "/input/update/third-party-cert-and-trust-chain"
                    ),
                },
            ],
        }
        configure_mock_session(
            mock_session, "GET",
            "/cps/v2/enrollments/1/changes/2",
            200, response_body,
            accept_header=(
                "application/vnd.akamai.cps.change.v2+json"
            ),
        )
        result = cps_client.get_change_status(1, 2)

        assert result is not None
        assert len(result.allowed_input) == 1
        ai = result.allowed_input[0]
        assert ai.type == "third-party-certificate"
        assert ai.required_to_proceed is True
        assert ai.info == (
            "/cps/v2/enrollments/1/changes/2"
            "/input/info/third-party-csr"
        )
        assert ai.update == (
            "/cps/v2/enrollments/1/changes/2"
            "/input/update/third-party-cert-and-trust-chain"
        )
        assert result.status_info is not None
        assert result.status_info.status == "wait-upload-third-party"
        assert result.status_info.state == "awaiting-input"

        mock_session.exec.assert_called_once()
        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/cps/v2/enrollments/1/changes/2"

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error making request",
            status_code=500,
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_change_status(1, 2)
        err = exc_info.value
        assert cps_errors.ErrGetChangeStatus in err.title
        assert err.status_code == 500

    def test_validation_error(self, cps_client, mock_session):
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_change_status(0, 0)
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()


# ===================================================================
# TestCancelChange — mirrors Go TestCancelChange
# from changes_test.go (lines 120-189)
# ===================================================================


class TestCancelChange:
    """Verify ``cancel_change`` endpoint.

    Mirrors Go ``TestCancelChange`` from ``changes_test.go``.
    """

    def test_200_ok(self, cps_client, mock_session):
        response_body = {
            "change": "/cps/v2/enrollments/1/changes/2",
        }
        configure_mock_session(
            mock_session, "DELETE",
            "/cps/v2/enrollments/1/changes/2",
            200, response_body,
            accept_header=(
                "application/vnd.akamai.cps.change-id.v1+json"
            ),
        )
        result = cps_client.cancel_change(1, 2)

        assert result is not None
        assert result.change == "/cps/v2/enrollments/1/changes/2"

        mock_session.exec.assert_called_once()
        call_args = mock_session.exec.call_args
        assert call_args[0][0] == "DELETE"
        assert call_args[0][1] == "/cps/v2/enrollments/1/changes/2"
        assert call_args[1]["headers"]["Accept"] == (
            "application/vnd.akamai.cps.change-id.v1+json"
        )

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error canceling change",
            status_code=500,
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.cancel_change(1, 2)
        err = exc_info.value
        assert cps_errors.ErrCancelChange in err.title
        assert err.status_code == 500

    def test_validation_error(self, cps_client, mock_session):
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.cancel_change(0, 0)
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()


# ===================================================================
# TestNewError / TestJsonErrorUnmarshalling — mirrors Go
# from errors_test.go (131 lines)
# ===================================================================


class TestNewError:
    """Verify ``parse_cps_error`` with JSON and non-JSON bodies.

    Mirrors Go ``TestNewError`` from ``errors_test.go``.
    """

    def test_valid_response_status_500(self):
        body = '{"type":"a","title":"b","detail":"c"}'
        response = make_mock_response(500, body)
        err = cps_errors.parse_cps_error(response)

        assert err.type == "a"
        assert err.title == "b"
        assert err.detail == "c"
        assert err.status_code == 500

    def test_invalid_response_body(self):
        response = make_mock_response(500, "test")
        err = cps_errors.parse_cps_error(response)

        assert err.title == (
            "Failed to unmarshal error body. CPS API failed. "
            "Check details for more information."
        )
        assert err.detail == "test"
        assert err.status_code == 500


class TestJsonErrorUnmarshalling:
    """Verify ``parse_cps_error`` with HTML, plain text, and XML bodies.

    Mirrors Go ``TestJsonErrorUnmarshalling`` from ``errors_test.go``.
    """

    def test_html_body(self):
        body = "<html>An error</html>"
        response = make_mock_response(503, body)
        err = cps_errors.parse_cps_error(response)

        assert err.title == (
            "Failed to unmarshal error body. CPS API failed. "
            "Check details for more information."
        )
        assert err.detail == body
        assert err.status_code == 503

    def test_text_body(self):
        body = (
            "Your request did not result in a response within the "
            "maximum request time. Please try backing off your rate."
        )
        response = make_mock_response(503, body)
        err = cps_errors.parse_cps_error(response)

        assert err.title == (
            "Failed to unmarshal error body. CPS API failed. "
            "Check details for more information."
        )
        assert err.status_code == 503

    def test_xml_body(self):
        body = "<error>An error</error>"
        response = make_mock_response(503, body)
        err = cps_errors.parse_cps_error(response)

        assert err.title == (
            "Failed to unmarshal error body. CPS API failed. "
            "Check details for more information."
        )
        assert err.status_code == 503


# ===================================================================
# TestGetDeploymentSchedule — mirrors Go TestGetDeploymentSchedule
# from deployment_schedules_test.go (lines 16-113)
# ===================================================================


class TestGetDeploymentSchedule:
    """Verify ``get_deployment_schedule`` endpoint.

    Mirrors Go ``TestGetDeploymentSchedule`` from
    ``deployment_schedules_test.go``.
    """

    def test_200_ok(self, cps_client, mock_session):
        response_body = {
            "notAfter": "2021-11-03T08:02:46.655484Z",
            "notBefore": "2021-10-03T08:02:46.655484Z",
        }
        configure_mock_session(
            mock_session, "GET",
            "/cps/v2/enrollments/10/changes/1/deployment-schedule",
            200, response_body,
            accept_header=(
                "application/vnd.akamai.cps."
                "deployment-schedule.v1+json"
            ),
        )
        result = cps_client.get_deployment_schedule(10, 1)

        assert result is not None
        assert result.not_after == "2021-11-03T08:02:46.655484Z"
        assert result.not_before == "2021-10-03T08:02:46.655484Z"

        mock_session.exec.assert_called_once()
        args = mock_session.exec.call_args
        assert args[0][0] == "GET"
        assert args[0][1] == (
            "/cps/v2/enrollments/10/changes/1/deployment-schedule"
        )

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error making request",
            status_code=500,
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_deployment_schedule(10, 1)
        err = exc_info.value
        assert cps_errors.ErrGetDeploymentSchedule in err.title
        assert err.status_code == 500

    def test_validation_error_missing_change_id(
        self, cps_client, mock_session,
    ):
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_deployment_schedule(10, 0)
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()

    def test_validation_error_missing_enrollment_id(
        self, cps_client, mock_session,
    ):
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_deployment_schedule(0, 1)
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()


# ===================================================================
# TestUpdateDeploymentSchedule — mirrors Go
# TestUpdateDeploymentSchedule from deployment_schedules_test.go
# (lines 115-235)
# ===================================================================


class TestUpdateDeploymentSchedule:
    """Verify ``update_deployment_schedule`` endpoint.

    Mirrors Go ``TestUpdateDeploymentSchedule`` from
    ``deployment_schedules_test.go``.
    """

    def test_200_ok(self, cps_client, mock_session):
        response_body = {"change": "test_change"}
        configure_mock_session(
            mock_session, "PUT",
            "/cps/v2/enrollments/10/changes/1/deployment-schedule",
            200, response_body,
            accept_header=(
                "application/vnd.akamai.cps.change-id.v1+json"
            ),
            content_type_header=(
                "application/vnd.akamai.cps."
                "deployment-schedule.v1+json; charset=utf-8"
            ),
        )
        schedule = models.DeploymentSchedule(
            not_after="2021-11-03T08:02:46.655484Z",
            not_before="2021-10-03T08:02:46.655484Z",
        )
        result = cps_client.update_deployment_schedule(10, 1, schedule)

        assert result is not None
        assert result.change == "test_change"

        mock_session.exec.assert_called_once()
        args = mock_session.exec.call_args
        assert args[0][0] == "PUT"
        assert args[0][1] == (
            "/cps/v2/enrollments/10/changes/1/deployment-schedule"
        )

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error making request",
            status_code=500,
        )
        schedule = models.DeploymentSchedule(
            not_after="2021-11-03T08:02:46.655484Z",
            not_before="2021-10-03T08:02:46.655484Z",
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.update_deployment_schedule(10, 1, schedule)
        err = exc_info.value
        assert cps_errors.ErrUpdateDeploymentSchedule in err.title
        assert err.status_code == 500

    def test_validation_error_missing_change_id(
        self, cps_client, mock_session,
    ):
        schedule = models.DeploymentSchedule(
            not_after="2021-11-03T08:02:46.655484Z",
            not_before="2021-10-03T08:02:46.655484Z",
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.update_deployment_schedule(10, 0, schedule)
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()

    def test_validation_error_missing_enrollment_id(
        self, cps_client, mock_session,
    ):
        schedule = models.DeploymentSchedule(
            not_after="2021-11-03T08:02:46.655484Z",
            not_before="2021-10-03T08:02:46.655484Z",
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.update_deployment_schedule(0, 1, schedule)
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()


# ===================================================================
# Deployment response body helpers — verbatim from Go
# deployments_test.go
# ===================================================================


def _deployment_body():
    """Return a single deployment dict (verbatim from Go)."""
    return {
        "ocspStapled": False,
        "ocspUris": [],
        "networkConfiguration": {
            "geography": "core",
            "mustHaveCiphers": "ak-akamai-2020q1",
            "ocspStapling": "on",
            "preferredCiphers": "ak-akamai-2020q1",
            "quicEnabled": False,
            "secureNetwork": "standard-tls",
            "sniOnly": True,
            "disallowedTlsVersions": ["TLSv1", "TLSv1_1"],
            "dnsNames": [
                "san2.example.com", "san1.example.com",
            ],
        },
        "primaryCertificate": {
            "certificate": (
                "-----BEGIN CERTIFICATE-----\n"
                "MIID <sample - removed for readability>"
                " .... 93Nvw==\n"
                "-----END CERTIFICATE-----"
            ),
            "expiry": "2022-02-05T13:21:21Z",
            "signatureAlgorithm": "SHA-256",
            "trustChain": (
                "-----BEGIN CERTIFICATE-----\n"
                "MIID <sample - removed for readability>"
                " .... Qs/v0=\n"
                "-----END CERTIFICATE-----"
            ),
        },
        "multiStackedCertificates": [
            {
                "certificate": (
                    "-----BEGIN CERTIFICATE-----\n"
                    "MIID <sample - removed for readability>"
                    " .... nMweq/\n"
                    "-----END CERTIFICATE-----"
                ),
                "expiry": "2022-02-05T13:21:20Z",
                "signatureAlgorithm": "SHA-256",
                "trustChain": (
                    "-----BEGIN CERTIFICATE-----\n"
                    "MIID <sample - removed for readability>"
                    " .... KEUp0=\n"
                    "-----END CERTIFICATE-----"
                ),
            },
        ],
    }


def _deployment_body_staging_trust_chain():
    """Staging variant with slightly different trust chain."""
    body = _deployment_body()
    body["primaryCertificate"]["trustChain"] = (
        "-----BEGIN CERTIFICATE-----\n"
        "MIID <sample - removed for readability>"
        " .... 9JQs/v0=\n"
        "-----END CERTIFICATE-----"
    )
    return body


def _assert_deployment_fields(dep, trust_chain_suffix="Qs/v0="):
    """Verify common deployment field assertions."""
    assert dep.ocsp_stapled is False
    assert dep.ocsp_uris == []
    nc = dep.network_configuration
    assert nc.geography == "core"
    assert nc.must_have_ciphers == "ak-akamai-2020q1"
    assert nc.ocsp_stapling == "on"
    assert nc.preferred_ciphers == "ak-akamai-2020q1"
    assert nc.quic_enabled is False
    assert nc.secure_network == "standard-tls"
    assert nc.sni_only is True
    assert nc.disallowed_tls_versions == ["TLSv1", "TLSv1_1"]
    assert nc.dns_names == [
        "san2.example.com", "san1.example.com",
    ]
    pc = dep.primary_certificate
    assert pc.expiry == "2022-02-05T13:21:21Z"
    assert pc.signature_algorithm == "SHA-256"
    assert trust_chain_suffix in pc.trust_chain
    assert len(dep.multi_stacked_certificates) == 1
    msc = dep.multi_stacked_certificates[0]
    assert msc.expiry == "2022-02-05T13:21:20Z"
    assert msc.signature_algorithm == "SHA-256"


# ===================================================================
# TestListDeployments — mirrors Go TestListDeployments
# from deployments_test.go (lines 15-224)
# ===================================================================


class TestListDeployments:
    """Verify ``list_deployments`` endpoint.

    Mirrors Go ``TestListDeployments`` from ``deployments_test.go``.
    """

    def test_200_ok(self, cps_client, mock_session):
        response_body = {
            "production": _deployment_body(),
            "staging": _deployment_body_staging_trust_chain(),
        }
        configure_mock_session(
            mock_session, "GET",
            "/cps/v2/enrollments/10/deployments",
            200, response_body,
            accept_header=(
                "application/vnd.akamai.cps.deployments.v8+json"
            ),
        )
        result = cps_client.list_deployments(10)

        assert result is not None
        assert result.production is not None
        _assert_deployment_fields(result.production)
        assert result.staging is not None
        _assert_deployment_fields(
            result.staging, trust_chain_suffix="9JQs/v0=",
        )

        mock_session.exec.assert_called_once()
        args = mock_session.exec.call_args
        assert args[0][0] == "GET"
        assert args[0][1] == "/cps/v2/enrollments/10/deployments"

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error making request",
            status_code=500,
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.list_deployments(500)
        err = exc_info.value
        assert cps_errors.ErrListDeployments in err.title
        assert err.status_code == 500


# ===================================================================
# TestGetProductionDeployment — mirrors Go from deployments_test.go
# (lines 227-368)
# ===================================================================


class TestGetProductionDeployment:
    """Verify ``get_production_deployment`` endpoint.

    Mirrors Go ``TestGetProductionDeployment`` from
    ``deployments_test.go``.
    """

    def test_200_ok(self, cps_client, mock_session):
        response_body = _deployment_body()
        configure_mock_session(
            mock_session, "GET",
            "/cps/v2/enrollments/10/deployments/production",
            200, response_body,
            accept_header=(
                "application/vnd.akamai.cps.deployment.v8+json"
            ),
        )
        result = cps_client.get_production_deployment(10)

        assert result is not None
        _assert_deployment_fields(result)

        mock_session.exec.assert_called_once()
        args = mock_session.exec.call_args
        assert args[0][0] == "GET"
        assert args[0][1] == (
            "/cps/v2/enrollments/10/deployments/production"
        )

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error making request",
            status_code=500,
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_production_deployment(500)
        err = exc_info.value
        assert cps_errors.ErrGetProductionDeployment in err.title
        assert err.status_code == 500

    def test_validation_error(self, cps_client, mock_session):
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_production_deployment(0)
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()


# ===================================================================
# TestGetStagingDeployment — mirrors Go TestGetStagingDeployment
# from deployments_test.go (lines 371-514)
# ===================================================================


class TestGetStagingDeployment:
    """Verify ``get_staging_deployment`` endpoint.

    Mirrors Go ``TestGetStagingDeployment`` from
    ``deployments_test.go``.
    """

    def test_200_ok(self, cps_client, mock_session):
        response_body = _deployment_body()
        configure_mock_session(
            mock_session, "GET",
            "/cps/v2/enrollments/10/deployments/staging",
            200, response_body,
            accept_header=(
                "application/vnd.akamai.cps.deployment.v8+json"
            ),
        )
        result = cps_client.get_staging_deployment(10)

        assert result is not None
        _assert_deployment_fields(result)

        mock_session.exec.assert_called_once()
        args = mock_session.exec.call_args
        assert args[0][0] == "GET"
        assert args[0][1] == (
            "/cps/v2/enrollments/10/deployments/staging"
        )

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error making request",
            status_code=500,
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_staging_deployment(500)
        err = exc_info.value
        assert cps_errors.ErrGetStagingDeployment in err.title
        assert err.status_code == 500

    def test_validation_error(self, cps_client, mock_session):
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_staging_deployment(0)
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()


# ===================================================================
# TestGetChangeLetsEncryptChallenges — mirrors Go from
# dv_challenges_test.go (lines 14-128)
# ===================================================================


class TestGetChangeLetsEncryptChallenges:
    """Verify ``get_change_lets_encrypt_challenges`` endpoint.

    Mirrors Go ``TestGetChangeLetsEncryptChallenges`` from
    ``dv_challenges_test.go``.
    """

    def test_200_ok(self, cps_client, mock_session):
        response_body = {
            "dv": [
                {
                    "status": "Awaiting user",
                    "error": (
                        "The domain is not ready for validation."
                    ),
                    "validationStatus": "RESPONSE_ERROR",
                    "requestTimestamp": "2018-09-05T15:55:49Z",
                    "validatedTimestamp": "2018-09-05T17:53:22Z",
                    "expires": "2018-09-06T17:55:17Z",
                    "challenges": [
                        {
                            "type": "dns-01",
                            "status": "pending",
                            "error": None,
                            "token": (
                                "cGBnw-3YO7rUhq61EuuHqcGr"
                                "YkaQWALAgi8szTqRoHA"
                            ),
                            "responseBody": (
                                "0yVISDJjpXR7BXzR5QgfA51t"
                                "t-I6aKremGnPwK_lvH4"
                            ),
                            "fullPath": (
                                "_acme-challenge."
                                "www.cps-example-dv.com."
                            ),
                            "redirectFullPath": "",
                            "validationRecords": [],
                        },
                    ],
                    "domain": "www.cps-example-dv.com",
                },
            ],
        }
        configure_mock_session(
            mock_session, "GET",
            "/cps/v2/enrollments/1/changes/2"
            "/input/info/lets-encrypt-challenges",
            200, response_body,
            accept_header=(
                "application/vnd.akamai.cps."
                "dv-challenges.v2+json"
            ),
        )
        result = cps_client.get_change_lets_encrypt_challenges(1, 2)

        assert result is not None
        assert len(result.dv) == 1
        dv_item = result.dv[0]
        assert dv_item.domain == "www.cps-example-dv.com"
        assert dv_item.status == "Awaiting user"
        assert dv_item.validation_status == "RESPONSE_ERROR"
        assert dv_item.request_timestamp == "2018-09-05T15:55:49Z"
        assert dv_item.validated_timestamp == "2018-09-05T17:53:22Z"
        assert dv_item.expires == "2018-09-06T17:55:17Z"
        assert len(dv_item.challenges) == 1
        ch = dv_item.challenges[0]
        assert ch.type == "dns-01"
        assert ch.status == "pending"
        assert ch.full_path == (
            "_acme-challenge.www.cps-example-dv.com."
        )
        assert ch.validation_records == []

        mock_session.exec.assert_called_once()

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error making request",
            status_code=500,
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_change_lets_encrypt_challenges(1, 2)
        err = exc_info.value
        assert (
            cps_errors.ErrGetChangeLetsEncryptChallenges in err.title
        )
        assert err.status_code == 500

    def test_validation_error(self, cps_client, mock_session):
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_change_lets_encrypt_challenges(0, 0)
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()


# ===================================================================
# TestAcknowledgeDVChallenges — mirrors Go from
# dv_challenges_test.go (lines 131-201)
# ===================================================================


class TestAcknowledgeDVChallenges:
    """Verify ``acknowledge_dv_challenges`` endpoint.

    Mirrors Go ``TestAcknowledgeDVChallenges`` from
    ``dv_challenges_test.go``.
    """

    def test_204_no_content(self, cps_client, mock_session):
        configure_mock_session(
            mock_session, "POST",
            "/cps/v2/enrollments/1/changes/2"
            "/input/update/lets-encrypt-challenges-completed",
            204, None,
            accept_header=(
                "application/vnd.akamai.cps.change-id.v1+json"
            ),
            content_type_header=(
                "application/vnd.akamai.cps."
                "acknowledgement.v1+json; charset=utf-8"
            ),
        )
        cps_client.acknowledge_dv_challenges(
            1, 2, cps_errors.ACKNOWLEDGEMENT_ACKNOWLEDGE,
        )

        mock_session.exec.assert_called_once()
        args = mock_session.exec.call_args
        assert args[0][0] == "POST"
        assert (
            "/lets-encrypt-challenges-completed" in args[0][1]
        )

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error making request",
            status_code=500,
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.acknowledge_dv_challenges(
                1, 2, cps_errors.ACKNOWLEDGEMENT_ACKNOWLEDGE,
            )
        err = exc_info.value
        assert (
            cps_errors.ErrAcknowledgeLetsEncryptChallenges in err.title
        )
        assert err.status_code == 500

    def test_validation_error(self, cps_client, mock_session):
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.acknowledge_dv_challenges(0, 0, "acknowledge")
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()


# ===================================================================
# Enrollment response body helpers — verbatim from Go
# enrollments_test.go
# ===================================================================


def _enrollment_1_body():
    """Return enrollment 1 dict (third-party, verbatim from Go)."""
    return {
        "id": 1,
        "productionSlots": [11],
        "stagingSlots": [22],
        "assignedSlots": [33],
        "location": "/cps-api/enrollments/1",
        "ra": "third-party",
        "validationType": "third-party",
        "certificateType": "third-party",
        "certificateChainType": "default",
        "networkConfiguration": {
            "geography": "core",
            "secureNetwork": "standard-tls",
            "mustHaveCiphers": "ak-akamai-2020q1",
            "preferredCiphers": "ak-akamai-2020q1",
            "disallowedTlsVersions": ["TLSv1", "TLSv1_1"],
            "sniOnly": True,
            "quicEnabled": False,
            "dnsNameSettings": {
                "cloneDnsNames": True,
                "dnsNames": [
                    "res-sqa2-3pss-4111-10-1-3CV382-ui.com",
                    "san1.res-sqa2-3pss-4111-10-1-3CV382-ui.com",
                ],
            },
            "ocspStapling": "on",
            "clientMutualAuthentication": None,
        },
        "signatureAlgorithm": None,
        "changeManagement": False,
        "csr": {
            "cn": "res-sqa2-3pss-4111-10-1-3CV382-ui.com",
            "c": "IN",
            "st": "KA",
            "l": "BLR",
            "o": "Akamai",
            "ou": "ETG",
            "sans": [
                "san1.res-sqa2-3pss-4111-10-1-3CV382-ui.com",
                "res-sqa2-3pss-4111-10-1-3CV382-ui.com",
            ],
            "preferredTrustChain": None,
        },
        "org": {
            "name": "Akamai",
            "addressLineOne": "EGL",
            "addressLineTwo": "",
            "city": "BLR",
            "region": "KA",
            "postalCode": "71",
            "country": "IN",
            "phone": "12",
        },
        "adminContact": {
            "firstName": "R1",
            "lastName": "D1",
            "phone": "4356",
            "email": "rd1@akamai.com",
            "addressLineOne": "EGL",
            "addressLineTwo": "",
            "city": "BLR",
            "country": "IN",
            "organizationName": "Akamai",
            "postalCode": "71",
            "region": "KA",
            "title": None,
        },
        "techContact": {
            "firstName": "R2",
            "lastName": "D2",
            "phone": "6456",
            "email": "rd2@akamai.com",
            "addressLineOne": "150 Broadway",
            "addressLineTwo": "",
            "city": "Cambridge",
            "country": "US",
            "organizationName": "Akamai Technologies",
            "postalCode": "02142",
            "region": "Massachusetts",
            "title": None,
        },
        "thirdParty": {"excludeSans": True},
        "enableMultiStackedCertificates": False,
        "autoRenewalStartTime": None,
        "pendingChanges": [
            {
                "location": "/cps-api/enrollments/1/changes/2",
                "changeType": "new-certificate",
            },
        ],
        "maxAllowedSanNames": 100,
        "maxAllowedWildcardSanNames": 100,
    }


def _enrollment_2_body():
    """Return enrollment 2 dict (DV/SAN, verbatim from Go)."""
    return {
        "id": 2,
        "productionSlots": [22],
        "stagingSlots": [33],
        "assignedSlots": [44],
        "location": "/cps-api/enrollments/2",
        "ra": "lets-encrypt",
        "validationType": "dv",
        "certificateType": "san",
        "certificateChainType": "default",
        "networkConfiguration": {
            "geography": "core",
            "secureNetwork": "enhanced-tls",
            "mustHaveCiphers": "ak-akamai-default-2017q3",
            "preferredCiphers": "ak-akamai-default-2017q3",
            "disallowedTlsVersions": ["TLSv1", "TLSv1_1"],
            "sniOnly": True,
            "quicEnabled": False,
            "dnsNameSettings": {
                "cloneDnsNames": True,
                "dnsNames": [
                    "jmm.20210504-dsa12.faden.me",
                ],
            },
            "ocspStapling": "on",
            "clientMutualAuthentication": None,
        },
        "signatureAlgorithm": "SHA-256",
        "changeManagement": False,
        "csr": {
            "cn": "jmm.20210504-dsa12.faden.me",
            "c": "US",
            "st": "MA",
            "l": "Cambridge",
            "o": "Akamai Technologies, Inc.",
            "ou": None,
            "sans": ["jmm.20210504-dsa12.faden.me"],
            "preferredTrustChain": None,
        },
        "org": {
            "name": "Akamai Technologies, Inc.",
            "addressLineOne": "150 Broadway",
            "addressLineTwo": None,
            "city": "Cambridge",
            "region": "MA",
            "postalCode": "02142",
            "country": "US",
            "phone": "617-444-3000",
        },
        "adminContact": {
            "firstName": "R3",
            "lastName": "D3",
            "phone": "8577068086",
            "email": "rd3@nomail-akamai.com",
            "addressLineOne": None,
            "addressLineTwo": None,
            "city": None,
            "country": None,
            "organizationName": None,
            "postalCode": None,
            "region": None,
            "title": None,
        },
        "techContact": {
            "firstName": "R4",
            "lastName": "D4",
            "phone": "617-444-3000",
            "email": "rd4@akamai.com",
            "addressLineOne": None,
            "addressLineTwo": None,
            "city": None,
            "country": None,
            "organizationName": None,
            "postalCode": None,
            "region": None,
            "title": None,
        },
        "thirdParty": None,
        "enableMultiStackedCertificates": False,
        "autoRenewalStartTime": None,
        "pendingChanges": [
            {
                "location": "/cps-api/enrollments/2/changes/2",
                "changeType": "new-certificate",
            },
        ],
        "maxAllowedSanNames": 100,
        "maxAllowedWildcardSanNames": 25,
    }


def _enrollment_3_body():
    """Return enrollment 3 dict (third-party multi-stacked)."""
    return {
        "id": 3,
        "productionSlots": [33],
        "stagingSlots": [44],
        "assignedSlots": [55],
        "location": "/cps-api/enrollments/3",
        "ra": "third-party",
        "validationType": "third-party",
        "certificateType": "third-party",
        "certificateChainType": "default",
        "networkConfiguration": {
            "geography": "core",
            "secureNetwork": "enhanced-tls",
            "mustHaveCiphers": "ak-akamai-2020q1",
            "preferredCiphers": "ak-akamai-2020q1",
            "disallowedTlsVersions": ["TLSv1", "TLSv1_1"],
            "sniOnly": True,
            "quicEnabled": False,
            "dnsNameSettings": {
                "cloneDnsNames": True,
                "dnsNames": [
                    "san1-submishr-ghj1-mediatest.com",
                    "san2-submishr-ghj1-mediatest.com",
                    "submishr-ghj1-mediatest.com",
                ],
            },
            "ocspStapling": "on",
            "clientMutualAuthentication": None,
        },
        "signatureAlgorithm": None,
        "changeManagement": False,
        "csr": {
            "cn": "submishr-ghj1-mediatest.com",
            "c": "IN",
            "st": "karnataka",
            "l": "Bangalore",
            "o": "Akamai",
            "ou": "",
            "sans": [
                "san1-submishr-ghj1-mediatest.com",
                "san2-submishr-ghj1-mediatest.com",
                "submishr-ghj1-mediatest.com",
            ],
        },
        "org": {
            "name": "Akamai",
            "addressLineOne": "EGL",
            "addressLineTwo": "Bangalore",
            "city": "Bangalore",
            "region": "karnataka",
            "postalCode": "560071",
            "country": "IN",
            "phone": "34234353453",
        },
        "adminContact": {
            "firstName": "DevQA",
            "lastName": "Tester",
            "phone": "6173000033",
            "email": "devqa@tester.com",
            "addressLineOne": None,
            "addressLineTwo": None,
            "city": None,
            "country": None,
            "organizationName": None,
            "postalCode": None,
            "region": None,
            "title": None,
        },
        "techContact": {
            "firstName": "John",
            "lastName": "Doe",
            "phone": "111000111",
            "email": "john@example.com",
            "addressLineOne": None,
            "addressLineTwo": None,
            "city": None,
            "country": None,
            "organizationName": None,
            "postalCode": None,
            "region": None,
            "title": None,
        },
        "thirdParty": {"excludeSans": False},
        "enableMultiStackedCertificates": True,
        "autoRenewalStartTime": None,
        "pendingChanges": [
            {
                "location": "/cps-api/enrollments/3/changes/30",
                "changeType": "new-certificate",
            },
        ],
        "maxAllowedSanNames": 100,
        "maxAllowedWildcardSanNames": 100,
    }


# ===================================================================
# TestListEnrollments — mirrors Go TestListEnrollments
# from enrollments_test.go (lines 14-511)
# ===================================================================


class TestListEnrollments:
    """Verify ``list_enrollments`` endpoint.

    Mirrors Go ``TestListEnrollments`` from ``enrollments_test.go``.
    """

    def test_200_ok(self, cps_client, mock_session):
        response_body = {
            "enrollments": [
                _enrollment_1_body(),
                _enrollment_2_body(),
                _enrollment_3_body(),
            ],
        }
        configure_mock_session(
            mock_session, "GET",
            "/cps/v2/enrollments",
            200, response_body,
            accept_header=(
                "application/vnd.akamai.cps.enrollments.v11+json"
            ),
        )
        result = cps_client.list_enrollments("Contract-123")

        assert result is not None
        assert len(result.enrollments) == 3

        # Verify first enrollment (third-party)
        e1 = result.enrollments[0]
        assert e1.id == 1
        assert e1.production_slots == [11]
        assert e1.staging_slots == [22]
        assert e1.assigned_slots == [33]
        assert e1.ra == "third-party"
        assert e1.validation_type == "third-party"
        assert e1.certificate_type == "third-party"
        assert e1.admin_contact.first_name == "R1"
        assert e1.admin_contact.last_name == "D1"
        assert e1.tech_contact.first_name == "R2"
        assert e1.csr.cn == (
            "res-sqa2-3pss-4111-10-1-3CV382-ui.com"
        )
        assert e1.third_party is not None
        assert e1.third_party.exclude_sans is True
        assert len(e1.pending_changes) == 1

        # Verify second enrollment (DV)
        e2 = result.enrollments[1]
        assert e2.id == 2
        assert e2.ra == "lets-encrypt"
        assert e2.validation_type == "dv"
        assert e2.certificate_type == "san"
        assert e2.admin_contact.first_name == "R3"
        assert e2.third_party is None

        # Verify third enrollment (multi-stacked)
        e3 = result.enrollments[2]
        assert e3.id == 3
        assert e3.enable_multi_stacked_certificates is True
        assert e3.third_party is not None
        assert e3.third_party.exclude_sans is False

        mock_session.exec.assert_called_once()
        args = mock_session.exec.call_args
        assert args[0][0] == "GET"
        assert args[0][1] == "/cps/v2/enrollments"
        assert args[1]["params"]["contractId"] == "Contract-123"

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error making request",
            status_code=500,
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.list_enrollments("1")
        err = exc_info.value
        assert cps_errors.ErrListEnrollments in err.title
        assert err.status_code == 500

    def test_validation_error(self, cps_client, mock_session):
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.list_enrollments("")
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()


# ===================================================================
# GetEnrollment response body helpers
# ===================================================================


def _get_enrollment_third_party_body():
    """Return GetEnrollment 200 OK third-party (verbatim from Go)."""
    return {
        "id": 1,
        "productionSlots": [11],
        "stagingSlots": [22],
        "assignedSlots": [33],
        "location": "/cps-api/enrollments/1",
        "ra": "third-party",
        "validationType": "third-party",
        "certificateType": "third-party",
        "certificateChainType": "default",
        "networkConfiguration": {
            "geography": "core",
            "secureNetwork": "enhanced-tls",
            "mustHaveCiphers": "ak-akamai-default",
            "preferredCiphers": "ak-akamai-default-interim",
            "disallowedTlsVersions": ["TLSv1"],
            "sniOnly": True,
            "quicEnabled": False,
            "dnsNameSettings": {
                "cloneDnsNames": False,
                "dnsNames": ["san1.example.com"],
            },
            "ocspStapling": "on",
            "clientMutualAuthentication": {
                "setId": (
                    "Custom_CPS-6134b_B-3-1AHBENT.xml"
                ),
                "authenticationOptions": {
                    "sendCaListToClient": False,
                    "ocsp": {"enabled": False},
                },
            },
        },
        "signatureAlgorithm": None,
        "changeManagement": True,
        "csr": {
            "cn": "www.example.com",
            "c": "US",
            "st": "MA",
            "l": "Cambridge",
            "o": "Akamai",
            "ou": "WebEx",
            "sans": ["www.example.com"],
            "preferredTrustChain": None,
        },
        "org": {
            "name": "Akamai Technologies",
            "addressLineOne": "150 Broadway",
            "addressLineTwo": None,
            "city": "Cambridge",
            "region": "MA",
            "postalCode": "02142",
            "country": "US",
            "phone": "617-555-0111",
        },
        "adminContact": {
            "firstName": "R1",
            "lastName": "D1",
            "phone": "617-555-0111",
            "email": "r1d1@akamai.com",
            "addressLineOne": "150 Broadway",
            "addressLineTwo": None,
            "city": "Cambridge",
            "country": "US",
            "organizationName": "Akamai",
            "postalCode": "02142",
            "region": "MA",
            "title": "Administrator",
        },
        "techContact": {
            "firstName": "R2",
            "lastName": "D2",
            "phone": "617-555-0111",
            "email": "r2d2@akamai.com",
            "addressLineOne": "150 Broadway",
            "addressLineTwo": None,
            "city": "Cambridge",
            "country": "US",
            "organizationName": "Akamai",
            "postalCode": "02142",
            "region": "MA",
            "title": "Technical Engineer",
        },
        "thirdParty": {"excludeSans": False},
        "enableMultiStackedCertificates": False,
        "autoRenewalStartTime": None,
        "pendingChanges": [
            {
                "location": "/cps-api/enrollments/1/changes/2",
                "changeType": "new-certificate",
            },
        ],
        "maxAllowedSanNames": 100,
        "maxAllowedWildcardSanNames": 100,
    }


def _get_enrollment_dv_body():
    """Return GetEnrollment 200 OK DV (verbatim from Go)."""
    return {
        "id": 1,
        "productionSlots": [],
        "stagingSlots": [],
        "assignedSlots": [12345],
        "location": "/cps/v2/enrollments/1",
        "ra": "lets-encrypt",
        "validationType": "dv",
        "certificateType": "san",
        "certificateChainType": "default",
        "networkConfiguration": {
            "geography": "core",
            "secureNetwork": "enhanced-tls",
            "mustHaveCiphers": "ak-akamai-default",
            "preferredCiphers": "ak-akamai-default-interim",
            "disallowedTlsVersions": ["TLSv1"],
            "sniOnly": True,
            "quicEnabled": False,
            "dnsNameSettings": {
                "cloneDnsNames": False,
                "dnsNames": ["san1.example.com"],
            },
            "ocspStapling": "on",
            "clientMutualAuthentication": {
                "setId": (
                    "Custom_CPS-6134b_B-3-1AHBENT.xml"
                ),
                "authenticationOptions": {
                    "sendCaListToClient": False,
                    "ocsp": {"enabled": False},
                },
            },
        },
        "signatureAlgorithm": "SHA-256",
        "changeManagement": True,
        "csr": {
            "cn": "www.example-test.com",
            "c": "US",
            "st": "MA",
            "l": "Cambridge",
            "o": "Akamai",
            "ou": "WebEx",
            "sans": ["www.example-test.com"],
            "preferredTrustChain": "intermediate-a",
        },
        "org": {
            "name": "Akamai Technologies",
            "addressLineOne": "1 Address",
            "addressLineTwo": None,
            "city": "Cambridge",
            "region": "MA",
            "postalCode": "012345",
            "country": "US",
            "phone": "555-111-1111",
        },
        "orgId": None,
        "adminContact": {
            "firstName": "R1",
            "lastName": "D1",
            "phone": "617-555-0111",
            "email": "r1d1@akamai.com",
            "addressLineOne": "150 Broadway",
            "addressLineTwo": None,
            "city": "Cambridge",
            "country": "US",
            "organizationName": "Akamai",
            "postalCode": "02142",
            "region": "MA",
            "title": "Administrator",
        },
        "techContact": {
            "firstName": "R2",
            "lastName": "D2",
            "phone": "617-555-0111",
            "email": "r2d2@akamai.com",
            "addressLineOne": "150 Broadway",
            "addressLineTwo": None,
            "city": "Cambridge",
            "country": "US",
            "organizationName": "Akamai",
            "postalCode": "02142",
            "region": "MA",
            "title": "Technical Engineer",
        },
        "thirdParty": None,
        "enableMultiStackedCertificates": False,
        "autoRenewalStartTime": None,
        "pendingChanges": [
            {
                "location": "/cps-api/enrollments/1/changes/1",
                "changeType": "new-certificate",
            },
        ],
        "maxAllowedSanNames": 100,
        "maxAllowedWildcardSanNames": 25,
    }


# ===================================================================
# TestGetEnrollment — mirrors Go TestGetEnrollment
# from enrollments_test.go (lines 514-928)
# ===================================================================


class TestGetEnrollment:
    """Verify ``get_enrollment`` endpoint.

    Mirrors Go ``TestGetEnrollment`` from ``enrollments_test.go``.
    """

    def test_200_ok_third_party(self, cps_client, mock_session):
        response_body = _get_enrollment_third_party_body()
        configure_mock_session(
            mock_session, "GET",
            "/cps/v2/enrollments/1",
            200, response_body,
            accept_header=(
                "application/vnd.akamai.cps.enrollment.v11+json"
            ),
        )
        result = cps_client.get_enrollment(1)

        assert result is not None
        assert result.id == 1
        assert result.ra == "third-party"
        assert result.validation_type == "third-party"
        assert result.certificate_type == "third-party"
        assert result.change_management is True
        assert result.csr.cn == "www.example.com"
        nc = result.network_configuration
        assert nc.client_mutual_authentication is not None
        assert nc.client_mutual_authentication.set_id == (
            "Custom_CPS-6134b_B-3-1AHBENT.xml"
        )
        auth = nc.client_mutual_authentication.authentication_options
        assert auth.send_ca_list_to_client is False
        assert auth.ocsp.enabled is False
        assert result.admin_contact.email == "r1d1@akamai.com"
        assert result.tech_contact.email == "r2d2@akamai.com"
        assert result.third_party is not None
        assert result.third_party.exclude_sans is False

        mock_session.exec.assert_called_once()
        args = mock_session.exec.call_args
        assert args[0][0] == "GET"
        assert args[0][1] == "/cps/v2/enrollments/1"

    def test_200_ok_dv(self, cps_client, mock_session):
        response_body = _get_enrollment_dv_body()
        configure_mock_session(
            mock_session, "GET",
            "/cps/v2/enrollments/1",
            200, response_body,
            accept_header=(
                "application/vnd.akamai.cps.enrollment.v11+json"
            ),
        )
        result = cps_client.get_enrollment(1)

        assert result is not None
        assert result.id == 1
        assert result.ra == "lets-encrypt"
        assert result.validation_type == "dv"
        assert result.certificate_type == "san"
        assert result.signature_algorithm == "SHA-256"
        assert result.csr.cn == "www.example-test.com"
        assert result.csr.preferred_trust_chain == "intermediate-a"
        assert result.assigned_slots == [12345]
        assert result.third_party is None
        assert result.max_allowed_wildcard_san_names == 25

        mock_session.exec.assert_called_once()

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error making request",
            status_code=500,
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_enrollment(1)
        err = exc_info.value
        assert cps_errors.ErrGetEnrollment in err.title
        assert err.status_code == 500

    def test_validation_error(self, cps_client, mock_session):
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_enrollment(0)
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()


# ===================================================================
# Enrollment request body helper
# ===================================================================


def _third_party_enrollment_body():
    """Build a minimal third-party EnrollmentRequestBody for tests."""
    return models.EnrollmentRequestBody(
        admin_contact=models.Contact(
            first_name="R1", last_name="D1",
            phone="617-555-0111", email="r1d1@akamai.com",
        ),
        certificate_type="third-party",
        csr=models.CSR(
            cn="www.example.com", c="US", st="MA",
            l="Cambridge", o="Akamai", ou="WebEx",
        ),
        network_configuration=models.NetworkConfiguration(),
        org=models.Org(name="Akamai"),
        ra="third-party",
        tech_contact=models.Contact(
            first_name="R2", last_name="D2",
            phone="617-555-0111", email="r2d2@akamai.com",
        ),
        validation_type="third-party",
    )


def _dv_enrollment_body():
    """Build a minimal DV EnrollmentRequestBody for tests."""
    return models.EnrollmentRequestBody(
        admin_contact=models.Contact(
            first_name="R1", last_name="D1",
            phone="617-555-0111", email="r1d1@akamai.com",
        ),
        certificate_type="san",
        csr=models.CSR(
            cn="www.example.com", c="US", st="MA",
            l="Cambridge", o="Akamai", ou="WebEx",
            preferred_trust_chain="intermediate-a",
        ),
        network_configuration=models.NetworkConfiguration(),
        org=models.Org(name="Akamai"),
        ra="lets-encrypt",
        tech_contact=models.Contact(
            first_name="R2", last_name="D2",
            phone="617-555-0111", email="r2d2@akamai.com",
        ),
        validation_type="dv",
    )


_CREATE_RESPONSE_BODY = {
    "enrollment": "/cps-api/enrollments/1",
    "changes": ["/cps-api/enrollments/1/changes/10002"],
}


# ===================================================================
# TestCreateEnrollment — mirrors Go TestCreateEnrollment
# from enrollments_test.go (lines 931-1208)
# ===================================================================


class TestCreateEnrollment:
    """Verify ``create_enrollment`` endpoint.

    Mirrors Go ``TestCreateEnrollment`` from ``enrollments_test.go``.
    """

    def test_202_accepted(self, cps_client, mock_session):
        response_body = dict(_CREATE_RESPONSE_BODY)
        configure_mock_session(
            mock_session, "POST",
            "/cps/v2/enrollments",
            202, response_body,
            accept_header=(
                "application/vnd.akamai.cps"
                ".enrollment-status.v1+json"
            ),
            content_type_header=(
                "application/vnd.akamai.cps"
                ".enrollment.v11+json; charset=utf-8"
            ),
        )
        body = _third_party_enrollment_body()
        result = cps_client.create_enrollment(
            "ctr-1", body,
            deploy_not_after="12-12-2021",
            deploy_not_before="12-07-2020",
        )

        assert result is not None
        assert result.enrollment == "/cps-api/enrollments/1"
        assert len(result.changes) == 1
        assert result.id == 1

        mock_session.exec.assert_called_once()
        args = mock_session.exec.call_args
        assert args[0][0] == "POST"
        assert args[0][1] == "/cps/v2/enrollments"
        assert args[1]["params"]["contractId"] == "ctr-1"
        assert args[1]["params"]["deploy-not-after"] == "12-12-2021"
        assert args[1]["params"]["deploy-not-before"] == "12-07-2020"

    def test_202_accepted_allow_duplicate_cn(
        self, cps_client, mock_session,
    ):
        response_body = dict(_CREATE_RESPONSE_BODY)
        configure_mock_session(
            mock_session, "POST",
            "/cps/v2/enrollments",
            202, response_body,
            accept_header=(
                "application/vnd.akamai.cps"
                ".enrollment-status.v1+json"
            ),
            content_type_header=(
                "application/vnd.akamai.cps"
                ".enrollment.v11+json; charset=utf-8"
            ),
        )
        body = _third_party_enrollment_body()
        body.org_id = 10
        result = cps_client.create_enrollment(
            "ctr-1", body,
            deploy_not_after="12-12-2021",
            deploy_not_before="12-07-2020",
            allow_duplicate_cn=True,
        )

        assert result is not None
        assert result.id == 1

        args = mock_session.exec.call_args
        assert args[1]["params"]["allow-duplicate-cn"] == "true"

    def test_202_accepted_dv_enrollment(
        self, cps_client, mock_session,
    ):
        response_body = dict(_CREATE_RESPONSE_BODY)
        configure_mock_session(
            mock_session, "POST",
            "/cps/v2/enrollments",
            202, response_body,
            accept_header=(
                "application/vnd.akamai.cps"
                ".enrollment-status.v1+json"
            ),
            content_type_header=(
                "application/vnd.akamai.cps"
                ".enrollment.v11+json; charset=utf-8"
            ),
        )
        body = _dv_enrollment_body()
        result = cps_client.create_enrollment(
            "ctr-1", body,
            deploy_not_after="12-12-2021",
            deploy_not_before="12-07-2020",
        )

        assert result is not None
        assert result.id == 1

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error creating enrollment",
            status_code=500,
        )
        body = _third_party_enrollment_body()
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.create_enrollment(
                "ctr-1", body,
                deploy_not_after="12-12-2021",
                deploy_not_before="12-07-2020",
            )
        err = exc_info.value
        assert cps_errors.ErrCreateEnrollment in err.title
        assert err.status_code == 500

    def test_validation_error_empty_body(
        self, cps_client, mock_session,
    ):
        body = models.EnrollmentRequestBody()
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.create_enrollment("ctr-1", body)
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()

    def test_validation_error_preferred_trust_chain_non_dv(
        self, cps_client, mock_session,
    ):
        body = _third_party_enrollment_body()
        body.csr = models.CSR(
            cn="www.example.com", c="US", st="MA",
            l="Cambridge", o="Akamai", ou="WebEx",
            preferred_trust_chain="intermediate-a",
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.create_enrollment("ctr-1", body)
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()

    def test_invalid_location(self, cps_client, mock_session):
        response_body = {
            "enrollment": "abc",
            "changes": ["/cps-api/enrollments/1/changes/10002"],
        }
        configure_mock_session(
            mock_session, "POST",
            "/cps/v2/enrollments",
            202, response_body,
        )
        body = _third_party_enrollment_body()
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.create_enrollment("ctr-1", body)
        err = exc_info.value
        assert "failed to parse location" in err.title


# ===================================================================
# TestUpdateEnrollment — mirrors Go TestUpdateEnrollment
# from enrollments_test.go (lines 1211-1490)
# ===================================================================


class TestUpdateEnrollment:
    """Verify ``update_enrollment`` endpoint.

    Mirrors Go ``TestUpdateEnrollment`` from ``enrollments_test.go``.
    Note: Go uses ``ErrCreateEnrollment`` for validation sentinel
    (this is a Go bug that we mirror).
    """

    def test_202_accepted(self, cps_client, mock_session):
        response_body = dict(_CREATE_RESPONSE_BODY)
        configure_mock_session(
            mock_session, "PUT",
            "/cps/v2/enrollments/1",
            202, response_body,
            accept_header=(
                "application/vnd.akamai.cps"
                ".enrollment-status.v1+json"
            ),
            content_type_header=(
                "application/vnd.akamai.cps"
                ".enrollment.v11+json; charset=utf-8"
            ),
        )
        body = _third_party_enrollment_body()
        body.org_id = 20
        result = cps_client.update_enrollment(
            1, body,
            allow_cancel_pending_changes=True,
            allow_staging_bypass=True,
            deploy_not_after="12-12-2021",
            deploy_not_before="12-07-2020",
            force_renewal=True,
            renewal_date_check_override=True,
        )

        assert result is not None
        assert result.enrollment == "/cps-api/enrollments/1"
        assert result.id == 1

        args = mock_session.exec.call_args
        assert args[0][0] == "PUT"
        assert args[0][1] == "/cps/v2/enrollments/1"
        params = args[1]["params"]
        assert params["allow-cancel-pending-changes"] == "true"
        assert params["allow-staging-bypass"] == "true"
        assert params["force-renewal"] == "true"
        assert params["renewal-date-check-override"] == "true"
        assert params["deploy-not-after"] == "12-12-2021"
        assert params["deploy-not-before"] == "12-07-2020"

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error updating enrollment",
            status_code=500,
        )
        body = _third_party_enrollment_body()
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.update_enrollment(
                1, body,
                deploy_not_after="12-12-2021",
                deploy_not_before="12-07-2020",
            )
        err = exc_info.value
        assert cps_errors.ErrUpdateEnrollment in err.title
        assert err.status_code == 500

    def test_validation_error(self, cps_client, mock_session):
        body = models.EnrollmentRequestBody()
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.update_enrollment(0, body)
        err = exc_info.value
        # NOTE: Go bug — uses ErrCreateEnrollment for validation.
        assert cps_errors.ErrCreateEnrollment in err.title
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()

    def test_validation_error_preferred_trust_chain(
        self, cps_client, mock_session,
    ):
        body = _third_party_enrollment_body()
        body.csr = models.CSR(
            cn="www.example.com", c="US", st="MA",
            l="Cambridge", o="Akamai", ou="WebEx",
            preferred_trust_chain="intermediate-a",
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.update_enrollment(1, body)
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()

    def test_invalid_location_url(self, cps_client, mock_session):
        response_body = {
            "enrollment": "abc",
            "changes": ["/cps-api/enrollments/1/changes/10002"],
        }
        configure_mock_session(
            mock_session, "PUT",
            "/cps/v2/enrollments/1",
            202, response_body,
        )
        body = _third_party_enrollment_body()
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.update_enrollment(
                1, body,
                allow_cancel_pending_changes=True,
                allow_staging_bypass=True,
                deploy_not_after="12-12-2021",
                deploy_not_before="12-07-2020",
                force_renewal=True,
                renewal_date_check_override=True,
            )
        err = exc_info.value
        assert "failed to parse location" in err.title


# ===================================================================
# TestRemoveEnrollment — mirrors Go TestRemoveEnrollment
# from enrollments_test.go (lines 1493-1643)
# ===================================================================


class TestRemoveEnrollment:
    """Verify ``remove_enrollment`` endpoint.

    Mirrors Go ``TestRemoveEnrollment`` from ``enrollments_test.go``.
    """

    def test_200_ok(self, cps_client, mock_session):
        response_body = {
            "enrollment": "/cps-api/enrollments/1",
            "changes": [
                "/cps-api/enrollments/1/changes/10002",
            ],
        }
        configure_mock_session(
            mock_session, "DELETE",
            "/cps/v2/enrollments/1",
            200, response_body,
            accept_header=(
                "application/vnd.akamai.cps"
                ".enrollment-status.v1+json"
            ),
        )
        result = cps_client.remove_enrollment(
            1,
            allow_cancel_pending_changes=True,
            deploy_not_after="12-12-2021",
            deploy_not_before="12-07-2021",
        )

        assert result is not None
        assert result.enrollment == "/cps-api/enrollments/1"
        assert len(result.changes) == 1

        args = mock_session.exec.call_args
        assert args[0][0] == "DELETE"
        assert args[0][1] == "/cps/v2/enrollments/1"
        params = args[1]["params"]
        assert params["allow-cancel-pending-changes"] == "true"
        assert params["deploy-not-after"] == "12-12-2021"
        assert params["deploy-not-before"] == "12-07-2021"

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error removing enrollment",
            status_code=500,
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.remove_enrollment(
                1,
                allow_cancel_pending_changes=True,
                deploy_not_after="12-12-2021",
                deploy_not_before="12-07-2021",
            )
        err = exc_info.value
        assert cps_errors.ErrRemoveEnrollment in err.title
        assert err.status_code == 500

    def test_validation_error(self, cps_client, mock_session):
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.remove_enrollment(0)
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()


# ===================================================================
# History PEM certificate constants — verbatim from Go
# history_test.go
# ===================================================================

_PEM_CERT = (
    "-----BEGIN CERTIFICATE-----\n"
    "MIIDpDCCAgygAwIBAgIQG7UFcE+swJPyIGzHEPrWTzANBgkqhkiG9w0BAQsFADCB\n"
    "jTEeMBwGA1UEChMVbWtjZXJ0IGRldmVsb3BtZW50IENBMTEwLwYDVQQLDCh3emFn\n"
    "cmFqY0BrcmstbXAwNmMgKFdvamNpZWNoIFphZ3JhamN6dWspMTgwNgYDVQQDDC9t\n"
    "a2NlcnQgd3phZ3JhamNAa3JrLW1wMDZjIChXb2pjaWVjaCBaYWdyYWpjenVrKTAe\n"
    "Fw0yMjA3MjAwNjE0MjlaFw0yNDEwMjAwNjE0MjlaMGsxCzAJBgNVBAYTAlBMMQ0w\n"
    "CwYDVQQIEwR0ZXN0MQ0wCwYDVQQHEwR0ZXN0MQ0wCwYDVQQKEwR0ZXN0MQ0wCwYD\n"
    "VQQLEwR0ZXN0MSAwHgYDVQQDExdjcHMud3phLXRlc3QwMDEuYWthdGVzdDBZMBMG\n"
    "ByqGSM49AgEGCCqGSM49AwEHA0IABLAKxSxwaZgqpFVHhFi6feDQ6A8Q0S71p/mP\n"
    "uwkUD1zNvmyKPzDflAWDGTyocC8aCzGCHiFdt6CRhCy25RwDK2mjbDBqMA4GA1Ud\n"
    "DwEB/wQEAwIFoDATBgNVHSUEDDAKBggrBgEFBQcDATAfBgNVHSMEGDAWgBTpiXDW\n"
    "LsgNHer9dSJuuzAt6LBpWzAiBgNVHREEGzAZghdjcHMud3phLXRlc3QwMDEuYWth\n"
    "dGVzdDANBgkqhkiG9w0BAQsFAAOCAYEAiXmq64svercHBIFbHfNPrRns3ccrOy0U\n"
    "+zHks6uSGEO2S/wnAhDtpK2D103SnddRK4WXDF3w0F/GCqrXGmWbKQvzukaUTBbl\n"
    "eO4Wy36qwc/SypvjzZsPI2q2E6e7uONcB2cL6UA18aEO/w9X4jTfWS5zMV1zPO3N\n"
    "aozEFRXrziFYGrPAJ9o2RldScHU9stl0TcIiuDWzUqPxvseGBuEMFNtVko590cJA\n"
    "l36muto6uC0XV8RtEaMAfbHe1yC64AJd+DzQP47ORQSR3L2+jA8oDQ9pJ+meiBA6\n"
    "At6AJpI1MsekXleRHnZxacUMVYzdk4c472xst+0ueHyMdaIbWgii54csrDfy2vPw\n"
    "ZwDNm437wJQvqg4RcUrOd5IoM37UCDfyisU9csY4yMXFxwwKFQtIk4Bn+lGbWdjC\n"
    "F+NSS+ujtHl0d5rg12QXegbWtFIol+E/ntxG4uS97dpldO2+cQCMM8RGsXA75teL\n"
    "4+HRwu0IEa7aaZZAVDZUA2U6wtAmhFM3\n"
    "-----END CERTIFICATE-----"
)

_PEM_CSR = (
    "-----BEGIN CERTIFICATE REQUEST-----\n"
    "MIIBJTCBzQIBADBrMQswCQYDVQQGEwJQTDENMAsGA1UECAwEdGVzdDENMAsGA1UE\n"
    "BwwEdGVzdDENMAsGA1UECgwEdGVzdDENMAsGA1UECwwEdGVzdDEgMB4GA1UEAwwX\n"
    "Y3BzLnd6YS10ZXN0MDAxLmFrYXRlc3QwWTATBgcqhkjOPQIBBggqhkjOPQMBBwNC\n"
    "AASwCsUscGmYKqRVR4RYun3g0OgPENEu9af5j7sJFA9czb5sij8w35QFgxk8qHAv\n"
    "Ggsxgh4hXbegkYQstuUcAytpoAAwCgYIKoZIzj0EAwIDRwAwRAIgZdTQC7pGlBQj\n"
    "5QHwPy/XFpXhgkssPkPGiyU+Ooauq6ACICCb/nP+DaEs193RFm6MBpScJAxf1F0r\n"
    "e9qtJn4af/6h\n"
    "-----END CERTIFICATE REQUEST-----"
)


# ===================================================================
# TestGetDVHistory — mirrors Go TestGetDVHistory
# from history_test.go (lines 14-187)
# ===================================================================


class TestGetDVHistory:
    """Verify ``get_dv_history`` endpoint.

    Mirrors Go ``TestGetDVHistory`` from ``history_test.go``.
    """

    def test_200_ok(self, cps_client, mock_session):
        response_body = {
            "results": [
                {
                    "domain": "bartdtest.sqa-il.com",
                    "domainHistory": [
                        {
                            "domain": "bartdtest.sqa-il.com",
                            "responseBody": (
                                "zVylMi1AXeE6XbLprYQayt3iojtMSuhE"
                                "LHwhJ2t2pfs.xI50JalgaT8I71x4Fcar"
                                "zkEx1UemXcsDqndvWaQqDgc"
                            ),
                            "fullPath": (
                                "http://bartdtest.sqa-il.com"
                                "/.well-known/acme-challenge/"
                                "zVylMi1AXeE6XbLprYQayt3iojtMSuhE"
                                "LHwhJ2t2pfs"
                            ),
                            "token": (
                                "zVylMi1AXeE6XbLprYQayt3iojtMSuhE"
                                "LHwhJ2t2pfs"
                            ),
                            "status": "Error",
                            "error": "Expired authorization",
                            "validationStatus": "EXPIRED",
                            "requestTimestamp": (
                                "2022-05-18T20:12:05Z"
                            ),
                            "validatedTimestamp": (
                                "2022-05-25T20:14:05Z"
                            ),
                            "expires": "2022-05-25T20:12:05Z",
                            "redirectFullPath": (
                                "http://dcv.akamai.com"
                                "/.well-known/acme-challenge/"
                                "zVylMi1AXeE6XbLprYQayt3iojtMSuhE"
                                "LHwhJ2t2pfs"
                            ),
                            "validationRecords": [],
                            "challenges": [
                                {
                                    "type": "http-01",
                                    "status": "pending",
                                    "error": None,
                                    "token": (
                                        "zVylMi1AXeE6XbLprYQay"
                                        "t3iojtMSuhELHwhJ2t2pfs"
                                    ),
                                    "responseBody": (
                                        "zVylMi1AXeE6XbLprYQay"
                                        "t3iojtMSuhELHwhJ2t2pfs"
                                        ".xI50JalgaT8I71x4Fcar"
                                        "zkEx1UemXcsDqndvWaQqDgc"
                                    ),
                                    "fullPath": (
                                        "http://bartdtest.sqa-il"
                                        ".com/.well-known/"
                                        "acme-challenge/"
                                        "zVylMi1AXeE6XbLprYQay"
                                        "t3iojtMSuhELHwhJ2t2pfs"
                                    ),
                                    "redirectFullPath": (
                                        "http://dcv.akamai.com"
                                        "/.well-known/"
                                        "acme-challenge/"
                                        "zVylMi1AXeE6XbLprYQay"
                                        "t3iojtMSuhELHwhJ2t2pfs"
                                    ),
                                    "validationRecords": [],
                                },
                                {
                                    "type": "dns-01",
                                    "status": "pending",
                                    "error": None,
                                    "token": (
                                        "zVylMi1AXeE6XbLprYQay"
                                        "t3iojtMSuhELHwhJ2t2pfs"
                                    ),
                                    "responseBody": (
                                        "qyxqdksaqsLTbWIt0im_ob"
                                        "0wYRUVH_Nfe91rmTD3bn0"
                                    ),
                                    "fullPath": (
                                        "_acme-challenge."
                                        "bartdtest.sqa-il.com."
                                    ),
                                    "redirectFullPath": "",
                                    "validationRecords": [],
                                },
                            ],
                        },
                        {
                            "domain": "bartdtest.sqa-il.com",
                            "responseBody": (
                                "7LwF89FciEFJZb_CUO0xogHQEh-r2iwN"
                                "6R4BNHvLSoI.QzVNu9F4w2DPQOMaqyiw"
                                "Ltnih04pcfunDeZx-LK3h24"
                            ),
                            "fullPath": (
                                "http://bartdtest.sqa-il.com"
                                "/.well-known/acme-challenge/"
                                "7LwF89FciEFJZb_CUO0xogHQEh-r2iwN"
                                "6R4BNHvLSoI"
                            ),
                            "token": (
                                "7LwF89FciEFJZb_CUO0xogHQEh-r2iwN"
                                "6R4BNHvLSoI"
                            ),
                            "status": "Error",
                            "error": "Expired authorization",
                            "validationStatus": "EXPIRED",
                            "requestTimestamp": (
                                "2022-05-25T20:14:35Z"
                            ),
                            "validatedTimestamp": (
                                "2022-06-01T20:15:13Z"
                            ),
                            "expires": "2022-06-01T20:14:35Z",
                            "redirectFullPath": (
                                "http://dcv.akamai.com"
                                "/.well-known/acme-challenge/"
                                "7LwF89FciEFJZb_CUO0xogHQEh-r2iwN"
                                "6R4BNHvLSoI"
                            ),
                            "validationRecords": [],
                            "challenges": [
                                {
                                    "type": "http-01",
                                    "status": "pending",
                                    "error": None,
                                    "token": (
                                        "7LwF89FciEFJZb_CUO0xo"
                                        "gHQEh-r2iwN6R4BNHvLSoI"
                                    ),
                                    "responseBody": (
                                        "7LwF89FciEFJZb_CUO0xo"
                                        "gHQEh-r2iwN6R4BNHvLSoI"
                                        ".QzVNu9F4w2DPQOMaqyiw"
                                        "Ltnih04pcfunDeZx-LK3h24"
                                    ),
                                    "fullPath": (
                                        "http://bartdtest.sqa-il"
                                        ".com/.well-known/"
                                        "acme-challenge/"
                                        "7LwF89FciEFJZb_CUO0xo"
                                        "gHQEh-r2iwN6R4BNHvLSoI"
                                    ),
                                    "redirectFullPath": (
                                        "http://dcv.akamai.com"
                                        "/.well-known/"
                                        "acme-challenge/"
                                        "7LwF89FciEFJZb_CUO0xo"
                                        "gHQEh-r2iwN6R4BNHvLSoI"
                                    ),
                                    "validationRecords": [],
                                },
                                {
                                    "type": "dns-01",
                                    "status": "pending",
                                    "error": None,
                                    "token": (
                                        "7LwF89FciEFJZb_CUO0xo"
                                        "gHQEh-r2iwN6R4BNHvLSoI"
                                    ),
                                    "responseBody": (
                                        "fNnU1Y9bCKG1jET8px-yE"
                                        "5cSd9HXMg-n6N1rCL0BqdE"
                                    ),
                                    "fullPath": (
                                        "_acme-challenge."
                                        "bartdtest.sqa-il.com."
                                    ),
                                    "redirectFullPath": "",
                                    "validationRecords": [],
                                },
                            ],
                        },
                    ],
                },
            ],
        }
        configure_mock_session(
            mock_session, "GET",
            "/cps/v2/enrollments/28926/dv-history",
            200, response_body,
            accept_header=(
                "application/vnd.akamai.cps.dv-history.v1+json"
            ),
        )
        result = cps_client.get_dv_history(28926)

        assert result is not None
        assert len(result.results) == 1
        r = result.results[0]
        assert r.domain == "bartdtest.sqa-il.com"
        assert len(r.domain_history) == 2
        dh0 = r.domain_history[0]
        assert dh0.status == "Error"
        assert dh0.error == "Expired authorization"
        assert dh0.validation_status == "EXPIRED"
        assert len(dh0.challenges) == 2
        assert dh0.challenges[0].type == "http-01"
        assert dh0.challenges[1].type == "dns-01"

        mock_session.exec.assert_called_once()
        args = mock_session.exec.call_args
        assert args[0][0] == "GET"
        assert args[0][1] == (
            "/cps/v2/enrollments/28926/dv-history"
        )

    def test_404_not_found(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type=(
                "https://akaa-wb66l66toq4ewuc4-haxhlepvmnlgidlc"
                ".luna-dev.akamaiapis.net/cps/v2/"
                "error-types/not-found"
            ),
            title="Not Found",
            status_code=404,
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_dv_history(28926000)
        err = exc_info.value
        assert cps_errors.ErrGetDVHistory in err.title
        assert err.status_code == 404

    def test_validation_error(self, cps_client, mock_session):
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_dv_history(0)
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()


# ===================================================================
# TestGetCertificateHistory — mirrors Go TestGetCertificateHistory
# from history_test.go (lines 190-333)
# ===================================================================


class TestGetCertificateHistory:
    """Verify ``get_certificate_history`` endpoint.

    Mirrors Go ``TestGetCertificateHistory`` from ``history_test.go``.
    """

    def test_200_ok(self, cps_client, mock_session):
        response_body = {
            "certificates": [
                {
                    "deploymentStatus": "active",
                    "geography": "core",
                    "multiStackedCertificates": [],
                    "primaryCertificate": {
                        "certificate": _PEM_CERT,
                        "expiry": "2024-10-20T06:14:29Z",
                        "keyAlgorithm": "ECDSA",
                        "trustChain": "",
                    },
                    "ra": "third-party",
                    "slots": [757836],
                    "stagingStatus": "active",
                    "type": "third-party",
                },
            ],
        }
        configure_mock_session(
            mock_session, "GET",
            "/cps/v2/enrollments/28926/history/certificates",
            200, response_body,
            accept_header=(
                "application/vnd.akamai.cps"
                ".certificate-history.v2+json"
            ),
        )
        result = cps_client.get_certificate_history(28926)

        assert result is not None
        assert len(result.certificates) == 1
        cert = result.certificates[0]
        assert cert.deployment_status == "active"
        assert cert.geography == "core"
        assert cert.ra == "third-party"
        assert cert.slots == [757836]
        assert cert.staging_status == "active"
        assert cert.type == "third-party"
        pc = cert.primary_certificate
        assert pc.key_algorithm == "ECDSA"
        assert pc.expiry == "2024-10-20T06:14:29Z"
        assert "BEGIN CERTIFICATE" in pc.certificate
        assert cert.multi_stacked_certificates == []

        mock_session.exec.assert_called_once()
        args = mock_session.exec.call_args
        assert args[0][0] == "GET"
        assert args[0][1] == (
            "/cps/v2/enrollments/28926/history/certificates"
        )

    def test_404_not_found(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type=(
                "https://akaa-wb66l66toq4ewuc4-haxhlepvmnlgidlc"
                ".luna-dev.akamaiapis.net/cps/v2/"
                "error-types/not-found"
            ),
            title="Not Found",
            status_code=404,
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_certificate_history(28926000)
        err = exc_info.value
        assert cps_errors.ErrGetCertificateHistory in err.title
        assert err.status_code == 404

    def test_validation_error(self, cps_client, mock_session):
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_certificate_history(0)
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()


# ===================================================================
# TestGetChangeHistory — mirrors Go TestGetChangeHistory
# from history_test.go (lines 336-448)
# ===================================================================


class TestGetChangeHistory:
    """Verify ``get_change_history`` endpoint.

    Mirrors Go ``TestGetChangeHistory`` from ``history_test.go``.
    """

    def test_200_ok(self, cps_client, mock_session):
        response_body = {
            "changes": [
                {
                    "action": "new-certificate",
                    "actionDescription": "Create New Certificate",
                    "businessCaseId": None,
                    "createdBy": "wzagrajc",
                    "createdOn": "2022-07-18T12:05:41Z",
                    "lastUpdated": "2022-07-21T21:40:00Z",
                    "multiStackedCertificates": [],
                    "primaryCertificate": {
                        "certificate": _PEM_CERT,
                        "trustChain": None,
                        "csr": _PEM_CSR,
                        "keyAlgorithm": "ECDSA",
                    },
                    "primaryCertificateOrderDetails": None,
                    "ra": "third-party",
                    "status": "completed",
                },
            ],
        }
        configure_mock_session(
            mock_session, "GET",
            "/cps/v2/enrollments/28926/history/changes",
            200, response_body,
            accept_header=(
                "application/vnd.akamai.cps"
                ".change-history.v5+json"
            ),
        )
        result = cps_client.get_change_history(28926)

        assert result is not None
        assert len(result.changes) == 1
        ch = result.changes[0]
        assert ch.action == "new-certificate"
        assert ch.action_description == "Create New Certificate"
        assert ch.status == "completed"
        assert ch.created_by == "wzagrajc"
        assert ch.ra == "third-party"
        pc = ch.primary_certificate
        assert pc.key_algorithm == "ECDSA"
        assert "BEGIN CERTIFICATE" in pc.certificate
        assert "BEGIN CERTIFICATE REQUEST" in pc.csr

        mock_session.exec.assert_called_once()
        args = mock_session.exec.call_args
        assert args[0][0] == "GET"
        assert args[0][1] == (
            "/cps/v2/enrollments/28926/history/changes"
        )

    def test_404_not_found(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type=(
                "https://akaa-wb66l66toq4ewuc4-haxhlepvmnlgidlc"
                ".luna-dev.akamaiapis.net/cps/v2/"
                "error-types/not-found"
            ),
            title="Not Found",
            status_code=404,
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_change_history(28926000)
        err = exc_info.value
        assert cps_errors.ErrGetChangeHistory in err.title
        assert err.status_code == 404

    def test_validation_error(self, cps_client, mock_session):
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_change_history(0)
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()


# ===================================================================
# TestGetChangeManagementInfo — mirrors Go
# TestGetChangeManagementInfo from change_management_info_test.go
# (lines 14-143)
# ===================================================================


class TestGetChangeManagementInfo:
    """Verify ``get_change_management_info`` endpoint.

    Mirrors Go ``TestGetChangeManagementInfo`` from
    ``change_management_info_test.go``.
    """

    def test_200_ok(self, cps_client, mock_session):
        response_body = {
            "acknowledgementDeadline": None,
            "validationResultHash": (
                "da39a3ee5e6b4b0d3255bfef95601890afd80709"
            ),
            "pendingState": {
                "pendingNetworkConfiguration": {
                    "dnsNameSettings": None,
                    "mustHaveCiphers": (
                        "ak-akamai-default2016q3"
                    ),
                    "networkType": None,
                    "ocspStapling": "not-set",
                    "preferredCiphers": "ak-akamai-default",
                    "quicEnabled": "false",
                    "sniOnly": "false",
                    "disallowedTlsVersions": ["TLSv1_2"],
                },
                "pendingCertificates": [
                    {
                        "certificateType": "third-party",
                        "fullCertificate": (
                            "-----BEGIN CERTIFICATE-----"
                            "\\n...\\n"
                            "-----END CERTIFICATE-----"
                        ),
                        "keyAlgorithm": "RSA",
                        "ocspStapled": "false",
                        "ocspUris": None,
                        "signatureAlgorithm": "SHA-256",
                    },
                ],
            },
            "validationResult": {
                "errors": None,
                "warnings": [
                    {
                        "message": (
                            "[SAN name [san9.example.com] "
                            "removed from certificate is "
                            "still live on the network., "
                            "SAN name [san8.example.com] "
                            "removed from certificate is "
                            "still live on the network.]"
                        ),
                        "messageCode": "no-code",
                    },
                ],
            },
        }
        configure_mock_session(
            mock_session, "GET",
            (
                "/cps/v2/enrollments/1/changes/2"
                "/input/info/change-management-info"
            ),
            200, response_body,
            accept_header=(
                "application/vnd.akamai.cps"
                ".change-management-info.v5+json"
            ),
        )
        result = cps_client.get_change_management_info(1, 2)

        assert result is not None
        assert result.acknowledgement_deadline is None
        assert result.validation_result_hash == (
            "da39a3ee5e6b4b0d3255bfef95601890afd80709"
        )
        ps = result.pending_state
        assert ps is not None
        pnc = ps.pending_network_configuration
        assert pnc.must_have_ciphers == (
            "ak-akamai-default2016q3"
        )
        assert pnc.disallowed_tls_versions == ["TLSv1_2"]
        assert len(ps.pending_certificates) == 1
        pc = ps.pending_certificates[0]
        assert pc.certificate_type == "third-party"
        assert pc.key_algorithm == "RSA"
        vr = result.validation_result
        assert vr is not None
        assert len(vr.warnings) == 1
        assert "san9.example.com" in vr.warnings[0].message

        mock_session.exec.assert_called_once()
        args = mock_session.exec.call_args
        assert args[0][0] == "GET"
        assert "/change-management-info" in args[0][1]

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error making request",
            status_code=500,
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_change_management_info(1, 2)
        err = exc_info.value
        assert cps_errors.ErrGetChangeManagementInfo in err.title
        assert err.status_code == 500

    def test_validation_error(self, cps_client, mock_session):
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_change_management_info(0, 0)
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()


# ===================================================================
# TestGetChangeDeploymentInfo — mirrors Go
# TestGetChangeDeploymentInfo from change_management_info_test.go
# (lines 146-255)
# ===================================================================


class TestGetChangeDeploymentInfo:
    """Verify ``get_change_deployment_info`` endpoint.

    Mirrors Go ``TestGetChangeDeploymentInfo`` from
    ``change_management_info_test.go``.
    Note: Go has NO validation error test for this function.
    """

    def test_200_ok(self, cps_client, mock_session):
        response_body = {
            "networkConfiguration": {
                "geography": "core",
                "secureNetwork": "enhanced-tls",
                "mustHaveCiphers": "ak-akamai-2020q1",
                "preferredCiphers": "ak-akamai-2020q1",
                "disallowedTlsVersions": [
                    "TLSv1_1", "TLSv1",
                ],
                "ocspStapling": "not-set",
                "sniOnly": False,
                "quicEnabled": False,
                "dnsNames": None,
            },
            "primaryCertificate": {
                "signatureAlgorithm": "SHA-1",
                "certificate": (
                    "-----BEGIN CERTIFICATE-----"
                    "\\n...\\n"
                    "-----END CERTIFICATE-----"
                ),
                "trustChain": "",
                "expiry": "2023-08-25T13:02:15Z",
                "keyAlgorithm": "RSA",
            },
            "multiStackedCertificates": [],
            "ocspUris": [],
            "ocspStapled": False,
        }
        configure_mock_session(
            mock_session, "GET",
            (
                "/cps/v2/enrollments/1/changes/2"
                "/input/info/change-management-info"
            ),
            200, response_body,
            accept_header=(
                "application/vnd.akamai.cps.deployment.v8+json"
            ),
        )
        result = cps_client.get_change_deployment_info(1, 2)

        assert result is not None
        nc = result.network_configuration
        assert nc.geography == "core"
        assert nc.secure_network == "enhanced-tls"
        assert nc.must_have_ciphers == "ak-akamai-2020q1"
        pc = result.primary_certificate
        assert pc.signature_algorithm == "SHA-1"
        assert pc.key_algorithm == "RSA"
        assert pc.expiry == "2023-08-25T13:02:15Z"
        assert result.ocsp_stapled is False
        assert result.multi_stacked_certificates == []

        mock_session.exec.assert_called_once()
        args = mock_session.exec.call_args
        assert args[0][0] == "GET"

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error making request",
            status_code=500,
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_change_deployment_info(1, 2)
        err = exc_info.value
        assert cps_errors.ErrGetChangeDeploymentInfo in err.title
        assert err.status_code == 500


# ===================================================================
# TestAcknowledgeChangeManagement — mirrors Go
# TestAcknowledgeChangeManagement from
# change_management_info_test.go (lines 258-346)
# ===================================================================


class TestAcknowledgeChangeManagement:
    """Verify ``acknowledge_change_management`` endpoint.

    Mirrors Go ``TestAcknowledgeChangeManagement`` from
    ``change_management_info_test.go``.
    Note: Go has NO validation error test for this function.
    """

    def test_200_ok(self, cps_client, mock_session):
        configure_mock_session(
            mock_session, "POST",
            (
                "/cps/v2/enrollments/1/changes/2"
                "/input/update/change-management-ack"
            ),
            200, {},
            accept_header=(
                "application/vnd.akamai.cps.change-id.v1+json"
            ),
            content_type_header=(
                "application/vnd.akamai.cps"
                ".acknowledgement.v1+json; charset=utf-8"
            ),
        )
        cps_client.acknowledge_change_management(
            1, 2,
            cps_errors.ACKNOWLEDGEMENT_ACKNOWLEDGE,
        )

        mock_session.exec.assert_called_once()
        args = mock_session.exec.call_args
        assert args[0][0] == "POST"
        assert "/change-management-ack" in args[0][1]

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error making request",
            status_code=500,
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.acknowledge_change_management(
                1, 2,
                cps_errors.ACKNOWLEDGEMENT_ACKNOWLEDGE,
            )
        err = exc_info.value
        assert (
            cps_errors.ErrAcknowledgeChangeManagement in err.title
        )
        assert err.status_code == 500


# ===================================================================
# TestGetChangePostVerificationWarnings — mirrors Go
# TestGetChangePostVerificationWarnings from
# post_verification_warnings_test.go (lines 14-84)
# ===================================================================


class TestGetChangePostVerificationWarnings:
    """Verify ``get_change_post_verification_warnings`` endpoint.

    Mirrors Go ``TestGetChangePostVerificationWarnings`` from
    ``post_verification_warnings_test.go``.
    """

    def test_200_ok(self, cps_client, mock_session):
        response_body = {"warnings": "some warning"}
        configure_mock_session(
            mock_session, "GET",
            (
                "/cps/v2/enrollments/1/changes/2"
                "/input/info/post-verification-warnings"
            ),
            200, response_body,
            accept_header=(
                "application/vnd.akamai.cps.warnings.v1+json"
            ),
        )
        result = (
            cps_client.get_change_post_verification_warnings(1, 2)
        )

        assert result is not None
        assert result.warnings == "some warning"

        mock_session.exec.assert_called_once()
        args = mock_session.exec.call_args
        assert args[0][0] == "GET"
        assert "/post-verification-warnings" in args[0][1]

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error making request",
            status_code=500,
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_change_post_verification_warnings(1, 2)
        err = exc_info.value
        assert (
            cps_errors.ErrGetChangePostVerificationWarnings
            in err.title
        )
        assert err.status_code == 500

    def test_validation_error(self, cps_client, mock_session):
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_change_post_verification_warnings(0, 0)
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()


# ===================================================================
# TestAcknowledgePostVerificationWarnings — mirrors Go
# TestAcknowledgePostVerificationWarnings from
# post_verification_warnings_test.go (lines 87-163)
# ===================================================================


class TestAcknowledgePostVerificationWarnings:
    """Verify ``acknowledge_post_verification_warnings`` endpoint.

    Mirrors Go ``TestAcknowledgePostVerificationWarnings`` from
    ``post_verification_warnings_test.go``.
    """

    def test_200_ok(self, cps_client, mock_session):
        configure_mock_session(
            mock_session, "POST",
            (
                "/cps/v2/enrollments/1/changes/2"
                "/input/update/"
                "post-verification-warnings-ack"
            ),
            200, {},
            accept_header=(
                "application/vnd.akamai.cps.change-id.v1+json"
            ),
            content_type_header=(
                "application/vnd.akamai.cps"
                ".acknowledgement.v1+json; charset=utf-8"
            ),
        )
        cps_client.acknowledge_post_verification_warnings(
            1, 2,
            cps_errors.ACKNOWLEDGEMENT_ACKNOWLEDGE,
        )

        mock_session.exec.assert_called_once()
        args = mock_session.exec.call_args
        assert args[0][0] == "POST"
        assert (
            "/post-verification-warnings-ack" in args[0][1]
        )

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error making request",
            status_code=500,
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.acknowledge_post_verification_warnings(
                1, 2,
                cps_errors.ACKNOWLEDGEMENT_ACKNOWLEDGE,
            )
        err = exc_info.value
        assert (
            cps_errors.ErrAcknowledgePostVerificationWarnings
            in err.title
        )
        assert err.status_code == 500

    def test_validation_error(self, cps_client, mock_session):
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.acknowledge_post_verification_warnings(
                0, 0, "acknowledge",
            )
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()


# ===================================================================
# TestGetPreVerificationWarnings — mirrors Go
# TestGetPreVerificationWarnings from
# pre_verification_warnings_test.go (lines 14-84)
# ===================================================================


class TestGetPreVerificationWarnings:
    """Verify ``get_change_pre_verification_warnings`` endpoint.

    Mirrors Go ``TestGetPreVerificationWarnings`` from
    ``pre_verification_warnings_test.go``.
    """

    def test_200_ok(self, cps_client, mock_session):
        response_body = {"warnings": "some warning"}
        configure_mock_session(
            mock_session, "GET",
            (
                "/cps/v2/enrollments/1/changes/2"
                "/input/info/pre-verification-warnings"
            ),
            200, response_body,
            accept_header=(
                "application/vnd.akamai.cps.warnings.v1+json"
            ),
        )
        result = (
            cps_client.get_change_pre_verification_warnings(1, 2)
        )

        assert result is not None
        assert result.warnings == "some warning"

        mock_session.exec.assert_called_once()
        args = mock_session.exec.call_args
        assert args[0][0] == "GET"
        assert "/pre-verification-warnings" in args[0][1]

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error making request",
            status_code=500,
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_change_pre_verification_warnings(1, 2)
        err = exc_info.value
        assert (
            cps_errors.ErrGetChangePreVerificationWarnings
            in err.title
        )
        assert err.status_code == 500

    def test_validation_error(self, cps_client, mock_session):
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_change_pre_verification_warnings(0, 0)
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()


# ===================================================================
# TestAcknowledgePreVerificationWarnings — mirrors Go
# TestAcknowledgePreVerificationWarnings from
# pre_verification_warnings_test.go (lines 87-160)
# ===================================================================


class TestAcknowledgePreVerificationWarnings:
    """Verify ``acknowledge_pre_verification_warnings`` endpoint.

    Mirrors Go ``TestAcknowledgePreVerificationWarnings`` from
    ``pre_verification_warnings_test.go``.
    Note: Go test expects 204 No Content on success.
    """

    def test_204_no_content(self, cps_client, mock_session):
        configure_mock_session(
            mock_session, "POST",
            (
                "/cps/v2/enrollments/1/changes/2"
                "/input/update/"
                "pre-verification-warnings-ack"
            ),
            204, {},
            accept_header=(
                "application/vnd.akamai.cps.change-id.v1+json"
            ),
            content_type_header=(
                "application/vnd.akamai.cps"
                ".acknowledgement.v1+json; charset=utf-8"
            ),
        )
        cps_client.acknowledge_pre_verification_warnings(
            1, 2, "acknowledge",
        )

        mock_session.exec.assert_called_once()
        args = mock_session.exec.call_args
        assert args[0][0] == "POST"
        assert (
            "/pre-verification-warnings-ack" in args[0][1]
        )

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error making request",
            status_code=500,
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.acknowledge_pre_verification_warnings(
                1, 2, "acknowledge",
            )
        err = exc_info.value
        assert (
            cps_errors.ErrAcknowledgePreVerificationWarnings
            in err.title
        )
        assert err.status_code == 500

    def test_validation_error(self, cps_client, mock_session):
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.acknowledge_pre_verification_warnings(
                0, 0, "acknowledge",
            )
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()


# ===================================================================
# TestGetChangeThirdPartyCSR — mirrors Go
# TestGetChangeThirdPartyCSR from third_party_csr_test.go
# (lines 14-87)
# ===================================================================


class TestGetChangeThirdPartyCSR:
    """Verify ``get_change_third_party_csr`` endpoint.

    Mirrors Go ``TestGetChangeThirdPartyCSR`` from
    ``third_party_csr_test.go``.
    """

    def test_200_ok(self, cps_client, mock_session):
        response_body = {
            "csrs": [
                {
                    "csr": (
                        "-----BEGIN CERTIFICATE REQUEST-----"
                        "\\n...\\n"
                        "-----END CERTIFICATE REQUEST-----"
                    ),
                    "keyAlgorithm": "RSA",
                },
                {
                    "csr": (
                        "-----BEGIN CERTIFICATE REQUEST-----"
                        "\\n...\\n"
                        "-----END CERTIFICATE REQUEST-----"
                    ),
                    "keyAlgorithm": "ECDSA",
                },
            ],
        }
        configure_mock_session(
            mock_session, "GET",
            (
                "/cps/v2/enrollments/1/changes/2"
                "/input/info/third-party-csr"
            ),
            200, response_body,
            accept_header=(
                "application/vnd.akamai.cps.csr.v2+json"
            ),
        )
        result = cps_client.get_change_third_party_csr(1, 2)

        assert result is not None
        assert len(result.csrs) == 2
        assert result.csrs[0].key_algorithm == "RSA"
        assert result.csrs[1].key_algorithm == "ECDSA"
        assert "BEGIN CERTIFICATE REQUEST" in result.csrs[0].csr

        mock_session.exec.assert_called_once()
        args = mock_session.exec.call_args
        assert args[0][0] == "GET"
        assert "/third-party-csr" in args[0][1]

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error making request",
            status_code=500,
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_change_third_party_csr(1, 2)
        err = exc_info.value
        assert cps_errors.ErrGetChangeThirdPartyCSR in err.title
        assert err.status_code == 500

    def test_validation_error(self, cps_client, mock_session):
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.get_change_third_party_csr(0, 0)
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()


# ===================================================================
# TestUploadThirdPartyCertAndTrustChain — mirrors Go
# TestUploadThirdPartyCertAndTrustChain from
# third_party_csr_test.go (lines 90-198)
# ===================================================================


class TestUploadThirdPartyCertAndTrustChain:
    """Verify ``upload_third_party_cert_and_trust_chain`` endpoint.

    Mirrors Go ``TestUploadThirdPartyCertAndTrustChain`` from
    ``third_party_csr_test.go``.
    """

    def test_200_ok(self, cps_client, mock_session):
        configure_mock_session(
            mock_session, "POST",
            (
                "/cps/v2/enrollments/1/changes/2"
                "/input/update/"
                "third-party-cert-and-trust-chain"
            ),
            200, {},
            accept_header=(
                "application/vnd.akamai.cps.change-id.v1+json"
            ),
            content_type_header=(
                "application/vnd.akamai.cps"
                ".certificate-and-trust-chain"
                ".v2+json; charset=utf-8"
            ),
        )
        certs = models.ThirdPartyCertificates(
            certificates_and_trust_chains=[
                models.CertificateAndTrustChain(
                    certificate=(
                        "-----BEGIN CERTIFICATE-----"
                        "\\n...\\n"
                        "-----END CERTIFICATE-----"
                    ),
                    trust_chain="",
                    key_algorithm="RSA",
                ),
                models.CertificateAndTrustChain(
                    certificate=(
                        "-----BEGIN CERTIFICATE-----"
                        "\\n...\\n"
                        "-----END CERTIFICATE-----"
                    ),
                    trust_chain="",
                    key_algorithm="ECDSA",
                ),
            ],
        )
        cps_client.upload_third_party_cert_and_trust_chain(
            1, 2, certs,
        )

        mock_session.exec.assert_called_once()
        args = mock_session.exec.call_args
        assert args[0][0] == "POST"
        assert (
            "/third-party-cert-and-trust-chain" in args[0][1]
        )

    def test_500_internal_server_error(self, cps_client, mock_session):
        mock_session.exec.side_effect = cps_errors.Error(
            type="internal_error",
            title="Internal Server Error",
            detail="Error making request",
            status_code=500,
        )
        certs = models.ThirdPartyCertificates(
            certificates_and_trust_chains=[],
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.upload_third_party_cert_and_trust_chain(
                1, 2, certs,
            )
        err = exc_info.value
        assert (
            cps_errors.ErrUploadThirdPartyCertAndTrustChain
            in err.title
        )
        assert err.status_code == 500

    def test_validation_error(self, cps_client, mock_session):
        certs = models.ThirdPartyCertificates(
            certificates_and_trust_chains=[],
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.upload_third_party_cert_and_trust_chain(
                0, 0, certs,
            )
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()

    def test_validation_error_invalid_key_algorithm(
        self, cps_client, mock_session,
    ):
        certs = models.ThirdPartyCertificates(
            certificates_and_trust_chains=[
                models.CertificateAndTrustChain(
                    certificate="test",
                    trust_chain="",
                    key_algorithm="invalid",
                ),
            ],
        )
        with pytest.raises(cps_errors.Error) as exc_info:
            cps_client.upload_third_party_cert_and_trust_chain(
                123, 123, certs,
            )
        err = exc_info.value
        assert cps_errors.ErrStructValidation in err.title
        mock_session.exec.assert_not_called()
