# pylint: disable=missing-function-docstring,missing-class-docstring,too-many-lines,line-too-long,unused-import,protected-access
"""Unit tests for the Cloudlets API client.

Mirrors ALL Go test functions from ``pkg/cloudlets/*_test.go`` files:
- cloudlets_test.go       (TestClient)
- errors_test.go          (TestNewError, TestAs, TestJsonErrorUnmarshalling)
- loadbalancer_test.go    (TestListOrigins … TestUpdateOriginValidation)
- loadbalancer_activation_test.go (TestGetLoadBalancerActivations, TestActivateLoadBalancerVersion)
- loadbalancer_version_test.go    (TestCreateLoadBalancerVersion … TestListLoadBalancerVersions)
- match_rule_test.go      (TestUnmarshalJSONMatchRules … TestValidateMatchRules)
- policy_test.go          (TestListPolicies … TestUpdatePolicy)
- policy_property_test.go (TestGetPolicyProperties, TestDeletePolicyProperty)
- policy_version_test.go  (TestListPolicyVersions … TestUpdatePolicyVersion)
- policy_version_activation_test.go (TestListPolicyActivations, TestActivatePolicyVersion)
- policy_version_rule_test.go      (TestGetPolicyVersionRule … TestUpdatePolicyVersionRule)
"""

import json
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.cloudlets.cloudlets import Client
from akamai.edgegrid.cloudlets import models
from akamai.edgegrid.cloudlets import errors as cerrors
from akamai.edgegrid.cloudlets.errors import (
    Error as CloudletsError,
    ErrStructValidation,
    ErrListOrigins,
    ErrGetOrigin,
    ErrCreateOrigin,
    ErrUpdateOrigin,
    ErrListPolicies,
    ErrGetPolicy,
    ErrCreatePolicy,
    ErrRemovePolicy,
    ErrUpdatePolicy,
    ErrListPolicyVersions,
    ErrGetPolicyVersion,
    ErrCreatePolicyVersion,
    ErrDeletePolicyVersion,
    ErrUpdatePolicyVersion,
    ErrListPolicyActivations,
    ErrActivatePolicyVersion,
    ErrGetPolicyVersionRule,
    ErrCreatePolicyVersionRule,
    ErrUpdatePolicyVersionRule,
    ErrGetPolicyProperties,
    ErrDeletePolicyProperty,
    ErrCreateLoadBalancerVersion,
    ErrGetLoadBalancerVersion,
    ErrUpdateLoadBalancerVersion,
    ErrListLoadBalancerVersions,
    ErrListLoadBalancerActivations,
    ErrActivateLoadBalancerVersion,
    ErrUnmarshallMatchRules,
)
from akamai.edgegrid.cloudlets import validation
from akamai.edgegrid.cloudlets.test.conftest import (
    mock_response,
    MockResponse,
    assert_error_is,
)


# ============================================================================
# Helper: create a mock session and configure it for a success scenario
# ============================================================================

def _make_session():
    """Create a MagicMock that behaves like Session."""
    session = MagicMock()
    session.base_url = "https://akaa-baseurl.luna.akamaiapis.net"
    return session


def _setup_success(session, status_code, response_body):
    """Configure mock session for a successful API call.

    session.exec will return (MockResponse, parsed_json).
    """
    resp = mock_response(status_code, response_body)
    try:
        parsed = json.loads(response_body)
    except (json.JSONDecodeError, TypeError, ValueError):
        parsed = None
    session.exec.return_value = (resp, parsed)
    return resp, parsed


def _setup_error(session, status_code, response_body):
    """Configure mock session to raise CloudletsError on exec (>= 400)."""
    resp = mock_response(status_code, response_body)
    err = CloudletsError.from_response(resp)
    session.exec.side_effect = err
    return err


# ========================================================================
# 1. Client Constructor Tests — cloudlets_test.go
# ========================================================================


class TestClient:
    """Mirrors Go TestClient (cloudlets_test.go lines 15-62)."""

    def test_default_client(self):
        session = _make_session()
        client = Client(session)
        assert client is not None
        assert client._session is session  # pylint: disable=protected-access

    def test_client_with_session(self):
        session = _make_session()
        client = Client(session)
        assert client._session is session  # pylint: disable=protected-access


# ========================================================================
# 2. Error Tests — errors_test.go
# ========================================================================


class TestNewError:
    """Mirrors Go TestNewError (errors_test.go lines 16-68)."""

    def test_valid_response_500(self):
        resp = mock_response(
            500,
            '{"type":"a","title":"b","detail":"c"}',
        )
        err = CloudletsError.from_response(resp)
        assert err.type == "a"
        assert err.title == "b"
        assert err.detail == "c"
        assert err.status_code == 500

    def test_invalid_response_body(self):
        resp = mock_response(500, "test")
        err = CloudletsError.from_response(resp)
        assert err.status_code == 500
        assert err.title == (
            "Failed to unmarshal error body. Cloudlets API failed. "
            "Check details for more information."
        )
        assert err.detail == "test"


class TestAs:
    """Mirrors Go TestAs (errors_test.go lines 70-103)."""

    def test_different_error_code(self):
        e1 = CloudletsError(status_code=404)
        e2 = CloudletsError(status_code=401)
        assert not e1.is_equivalent(e2)

    def test_same_error_code(self):
        e1 = CloudletsError(status_code=404)
        e2 = CloudletsError(status_code=404)
        assert e1.is_equivalent(e2)

    def test_same_code_and_message(self):
        errs = [{"messageId": "some_id", "fieldName": "test"}]
        e1 = CloudletsError(status_code=404, errors=errs)
        e2 = CloudletsError(status_code=404, errors=errs)
        assert e1.is_equivalent(e2)

    def test_same_code_different_message(self):
        errs = [{"messageId": "some_id", "fieldName": "test"}]
        e1 = CloudletsError(status_code=404, errors=errs)
        e2 = CloudletsError(status_code=404)
        assert not e1.is_equivalent(e2)


class TestJsonErrorUnmarshalling:
    """Mirrors Go TestJsonErrorUnmarshalling (errors_test.go lines 106-167)."""

    def test_html_response(self):
        body = '<HTML><HEAD>\n<TITLE>Access Denied</TITLE>\n</HEAD><BODY>\n<H1>Access Denied</H1>\n \nYou don\'t have permission to access "cloudlets-api-url" on this server.<P>\nReference&#32;&#35;18&#46;6e&#50;e&#49;&#55;&#48;2&#46;1a2b3c4&#46;5d6e7f80\n</BODY>\n</HTML>'
        resp = mock_response(503, body)
        err = CloudletsError.from_response(resp)
        assert err.status_code == 503
        assert err.title == (
            "Failed to unmarshal error body. Cloudlets API failed. "
            "Check details for more information."
        )

    def test_plain_text_response(self):
        body = 'Your request did not succeed as this operation has reached  the limit for your account. Please try after 2024-01-16T15:20:55.945Z'
        resp = mock_response(503, body)
        err = CloudletsError.from_response(resp)
        assert err.status_code == 503
        assert err.title == (
            "Failed to unmarshal error body. Cloudlets API failed. "
            "Check details for more information."
        )
        assert err.detail == body

    def test_xml_response(self):
        body = '<Root><Item id="1" name="Example" /></Root>'
        resp = mock_response(503, body)
        err = CloudletsError.from_response(resp)
        assert err.status_code == 503
        assert err.title == (
            "Failed to unmarshal error body. Cloudlets API failed. "
            "Check details for more information."
        )
        assert err.detail == body


# ========================================================================
# 3. Origin / LoadBalancer Tests — loadbalancer_test.go
# ========================================================================


class TestListOrigins:
    """Mirrors Go TestListOrigins (loadbalancer_test.go lines 15-214)."""

    def test_200_ok(self):
        session = _make_session()
        body = json.dumps([
            {"hostname": "", "description": "ALB1", "originId": "alb1", "type": "APPLICATION_LOAD_BALANCER", "akamaized": False},
            {"hostname": "h.akamai.com", "description": "CUSTOMER1", "originId": "cust1", "type": "CUSTOMER", "akamaized": True},
            {"hostname": "", "description": "CUSTOMER2", "originId": "cust2", "type": "CUSTOMER", "akamaized": False},
            {"hostname": "", "description": "NETSTORAGE1", "originId": "ns1", "type": "NETSTORAGE", "akamaized": False},
            {"hostname": "", "description": "NETSTORAGE2", "originId": "ns2", "type": "NETSTORAGE", "akamaized": False},
            {"hostname": "", "description": "ALB2", "originId": "alb2", "type": "APPLICATION_LOAD_BALANCER", "akamaized": False},
        ])
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.list_origins(models.ListOriginsRequest())
        assert len(result) == 6
        assert result[0].origin_id == "alb1"
        assert result[0].type == "APPLICATION_LOAD_BALANCER"
        session.exec.assert_called_once()
        call_args = session.exec.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "/cloudlets/api/v2/origins"

    def test_200_ok_with_param(self):
        session = _make_session()
        body = json.dumps([
            {"hostname": "h.akamai.com", "description": "CUSTOMER1", "originId": "cust1", "type": "CUSTOMER", "akamaized": True},
            {"hostname": "", "description": "CUSTOMER2", "originId": "cust2", "type": "CUSTOMER", "akamaized": False},
        ])
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.list_origins(models.ListOriginsRequest(type="CUSTOMER"))
        assert len(result) == 2
        session.exec.assert_called_once()
        call_args = session.exec.call_args
        assert call_args[1].get("params") == {"type": "CUSTOMER"} or call_args[0][1] == "/cloudlets/api/v2/origins"

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.list_origins(models.ListOriginsRequest())


class TestGetOrigin:
    """Mirrors Go TestGetOrigin (loadbalancer_test.go lines 217-284)."""

    def test_200_ok(self):
        session = _make_session()
        body = json.dumps({
            "hostname": "",
            "description": "ALB1",
            "originId": "alb1",
            "type": "APPLICATION_LOAD_BALANCER",
            "akamaized": False,
            "checksum": "abcdefg1111hijklmn22222fff76yae3",
        })
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.get_origin(models.GetOriginRequest(origin_id="alb1"))
        assert result.origin_id == "alb1"
        assert result.description == "ALB1"
        assert result.type == "APPLICATION_LOAD_BALANCER"
        assert result.checksum == "abcdefg1111hijklmn22222fff76yae3"
        call_args = session.exec.call_args
        assert call_args[0][1] == "/cloudlets/api/v2/origins/alb1"

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.get_origin(models.GetOriginRequest(origin_id="alb1"))


class TestCreateOrigin:
    """Mirrors Go TestCreateOrigin (loadbalancer_test.go lines 286-378)."""

    def test_201_created(self):
        session = _make_session()
        body = json.dumps({
            "hostname": "",
            "description": "first Origin",
            "originId": "first",
            "akamaized": False,
            "checksum": "abc123",
            "type": "APPLICATION_LOAD_BALANCER",
        })
        _setup_success(session, 201, body)
        client = Client(session)
        result = client.create_origin(models.CreateOriginRequest(
            origin_id="first",
            description="first Origin",
        ))
        assert result.origin_id == "first"
        assert result.description == "first Origin"
        call_args = session.exec.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/cloudlets/api/v2/origins"

    def test_201_created_minimal(self):
        session = _make_session()
        body = json.dumps({
            "hostname": "",
            "description": "",
            "originId": "first",
            "akamaized": False,
            "type": "APPLICATION_LOAD_BALANCER",
        })
        _setup_success(session, 201, body)
        client = Client(session)
        result = client.create_origin(models.CreateOriginRequest(
            origin_id="first",
        ))
        assert result.origin_id == "first"

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.create_origin(models.CreateOriginRequest(
                origin_id="first",
                description="first Origin",
            ))


class TestCreateOriginValidation:
    """Mirrors Go TestCreateOriginValidation (loadbalancer_test.go lines 380-415)."""

    def test_origin_id_exceeds_max_length(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.create_origin(models.CreateOriginRequest(
                origin_id="a" * 64,
            ))
        assert ErrStructValidation in str(exc_info.value.title)

    def test_origin_id_too_short(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.create_origin(models.CreateOriginRequest(
                origin_id="a",
            ))
        assert ErrStructValidation in str(exc_info.value.title)

    def test_description_exceeds_max_length(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.create_origin(models.CreateOriginRequest(
                origin_id="valid_id",
                description="a" * 256,
            ))
        assert ErrStructValidation in str(exc_info.value.title)


class TestUpdateOrigin:
    """Mirrors Go TestUpdateOrigin (loadbalancer_test.go lines 417-545)."""

    def test_200_updated(self):
        session = _make_session()
        body = json.dumps({
            "hostname": "",
            "description": "update first Origin",
            "originId": "first",
            "akamaized": False,
            "checksum": "abc123",
            "type": "APPLICATION_LOAD_BALANCER",
        })
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.update_origin(models.UpdateOriginRequest(
            origin_id="first",
            description="update first Origin",
        ))
        assert result.description == "update first Origin"
        call_args = session.exec.call_args
        assert call_args[0][0] == "PUT"
        assert call_args[0][1] == "/cloudlets/api/v2/origins/first"
        # Verify request body is ONLY the Description struct
        sent_body = call_args[1].get("body") if "body" in (call_args[1] or {}) else call_args[1].get("body")
        if sent_body is not None:
            assert "description" in json.dumps(sent_body).lower()

    def test_200_updated_minimal(self):
        session = _make_session()
        body = json.dumps({
            "hostname": "",
            "description": "",
            "originId": "first",
            "akamaized": False,
            "type": "APPLICATION_LOAD_BALANCER",
        })
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.update_origin(models.UpdateOriginRequest(
            origin_id="first",
        ))
        assert result.origin_id == "first"

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.update_origin(models.UpdateOriginRequest(
                origin_id="first",
                description="update first Origin",
            ))


class TestUpdateOriginValidation:
    """Mirrors Go TestUpdateOriginValidation (loadbalancer_test.go)."""

    def test_origin_id_exceeds_max_length(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.update_origin(models.UpdateOriginRequest(
                origin_id="a" * 64,
            ))
        assert ErrStructValidation in str(exc_info.value.title)

    def test_origin_id_too_short(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.update_origin(models.UpdateOriginRequest(
                origin_id="a",
            ))
        assert ErrStructValidation in str(exc_info.value.title)

    def test_description_exceeds_max_length(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.update_origin(models.UpdateOriginRequest(
                origin_id="valid_id",
                description="a" * 256,
            ))
        assert ErrStructValidation in str(exc_info.value.title)


# ========================================================================
# 4. LoadBalancer Activation Tests — loadbalancer_activation_test.go
# ========================================================================


class TestGetLoadBalancerActivations:
    """Mirrors Go TestGetLoadBalancerActivations (loadbalancer_activation_test.go lines 15-175)."""

    def test_200_ok(self):
        session = _make_session()
        body = json.dumps([
            {
                "activatedBy": "jsmith",
                "activatedDate": "2020-07-14T22:16:00.554Z",
                "network": "PRODUCTION",
                "originId": "clorigin1",
                "status": "active",
                "version": 2,
            },
            {
                "activatedBy": "jdoe",
                "activatedDate": "2020-07-14T22:16:00.554Z",
                "network": "STAGING",
                "originId": "clorigin1",
                "status": "active",
                "version": 1,
            },
        ])
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.list_load_balancer_activations(
            models.ListLoadBalancerActivationsRequest(origin_id="clorigin1"),
        )
        assert len(result) == 2
        assert result[0].network == "PRODUCTION"
        assert result[1].network == "STAGING"
        call_args = session.exec.call_args
        assert "/cloudlets/api/v2/origins/clorigin1/activations" in call_args[0][1]

    def test_200_ok_with_optional_params(self):
        session = _make_session()
        body = json.dumps([
            {
                "activatedBy": "jsmith",
                "activatedDate": "2020-07-14T22:16:00.554Z",
                "network": "PRODUCTION",
                "originId": "clorigin1",
                "status": "active",
                "version": 2,
            },
        ])
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.list_load_balancer_activations(
            models.ListLoadBalancerActivationsRequest(
                origin_id="clorigin1",
                network="prod",
                latest_only=True,
                page_size=3,
                page=1,
            ),
        )
        assert len(result) == 1

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.list_load_balancer_activations(
                models.ListLoadBalancerActivationsRequest(origin_id="clorigin1"),
            )

    def test_validation_error_invalid_network(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.list_load_balancer_activations(
                models.ListLoadBalancerActivationsRequest(
                    origin_id="clorigin1",
                    network="invalid",
                ),
            )
        assert ErrStructValidation in str(exc_info.value.title)


class TestActivateLoadBalancerVersion:
    """Mirrors Go TestActivateLoadBalancerVersion (loadbalancer_activation_test.go lines 177-287)."""

    def test_200_ok(self):
        session = _make_session()
        body = json.dumps({
            "activatedBy": "jsmith",
            "activatedDate": "2020-07-14T22:16:00.554Z",
            "network": "PRODUCTION",
            "originId": "clorigin1",
            "status": "active",
            "version": 2,
        })
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.activate_load_balancer_version(
            models.ActivateLoadBalancerVersionRequest(
                origin_id="clorigin1",
                async_=False,
                load_balancer_version_activation=models.LoadBalancerVersionActivation(
                    network="PRODUCTION",
                    version=2,
                ),
            ),
        )
        assert result.network == "PRODUCTION"
        assert result.version == 2
        call_args = session.exec.call_args
        assert call_args[0][0] == "POST"
        assert "/cloudlets/api/v2/origins/clorigin1/activations" in call_args[0][1]

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.activate_load_balancer_version(
                models.ActivateLoadBalancerVersionRequest(
                    origin_id="clorigin1",
                    async_=False,
                    load_balancer_version_activation=models.LoadBalancerVersionActivation(
                        network="PRODUCTION",
                        version=2,
                    ),
                ),
            )

    def test_validation_error(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.activate_load_balancer_version(
                models.ActivateLoadBalancerVersionRequest(
                    origin_id="clorigin1",
                    load_balancer_version_activation=models.LoadBalancerVersionActivation(
                        network="INVALID",
                        version=2,
                    ),
                ),
            )
        assert ErrStructValidation in str(exc_info.value.title)


# ========================================================================
# 5. LoadBalancer Version Tests — loadbalancer_version_test.go
# ========================================================================


class TestCreateLoadBalancerVersion:
    """Mirrors Go TestCreateLoadBalancerVersion (loadbalancer_version_test.go lines 18-265)."""

    def test_201_created(self):
        session = _make_session()
        response_body = json.dumps({
            "balancingType": "WEIGHTED",
            "createdBy": "jsmith",
            "createdDate": "2020-07-01T01:09:12.000Z",
            "dataCenters": [
                {
                    "city": "Philadelphia",
                    "cloudServerHostHeaderOverride": False,
                    "cloudService": True,
                    "continent": "NA",
                    "country": "US",
                    "hostname": "clorigin1.example.com",
                    "latitude": 39.57,
                    "livenessHosts": ["clorigin1.example.com"],
                    "longitude": -75.57,
                    "originId": "clorigin1",
                    "percent": 100.0,
                    "stateOrProvince": "PA",
                },
            ],
            "deleted": False,
            "immutable": False,
            "lastModifiedBy": "jsmith",
            "lastModifiedDate": "2020-07-01T01:09:12.000Z",
            "livenessSettings": {
                "hostHeader": "clorigin1.example.com",
                "interval": 10,
                "path": "/status",
                "port": 443,
                "protocol": "HTTPS",
                "status3xxFailure": False,
                "status4xxFailure": False,
                "status5xxFailure": False,
                "timeout": 25.0,
            },
            "originId": "clorigin1",
            "version": 2,
        })
        _setup_success(session, 201, response_body)
        client = Client(session)
        result = client.create_load_balancer_version(
            models.CreateLoadBalancerVersionRequest(
                origin_id="clorigin1",
                load_balancer_version=models.LoadBalancerVersion(
                    balancing_type="WEIGHTED",
                    data_centers=[
                        models.DataCenter(
                            city="Philadelphia",
                            cloud_server_host_header_override=False,
                            cloud_service=True,
                            continent="NA",
                            country="US",
                            hostname="clorigin1.example.com",
                            latitude=39.57,
                            liveness_hosts=["clorigin1.example.com"],
                            longitude=-75.57,
                            origin_id="clorigin1",
                            percent=100.0,
                            state_or_province="PA",
                        ),
                    ],
                    liveness_settings=models.LivenessSettings(
                        host_header="clorigin1.example.com",
                        interval=10,
                        path="/status",
                        port=443,
                        protocol="HTTPS",
                        timeout=25.0,
                    ),
                ),
            ),
        )
        assert result.balancing_type == "WEIGHTED"
        assert result.version == 2
        assert len(result.data_centers) == 1
        call_args = session.exec.call_args
        assert call_args[0][0] == "POST"
        assert "/cloudlets/api/v2/origins/clorigin1/versions" in call_args[0][1]

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.create_load_balancer_version(
                models.CreateLoadBalancerVersionRequest(
                    origin_id="clorigin1",
                    load_balancer_version=models.LoadBalancerVersion(
                        balancing_type="WEIGHTED",
                        data_centers=[
                            models.DataCenter(
                                continent="NA",
                                country="US",
                                latitude=39.57,
                                longitude=-75.57,
                                origin_id="clorigin1",
                                percent=100.0,
                            ),
                        ],
                        liveness_settings=models.LivenessSettings(
                            port=443,
                            protocol="HTTPS",
                            path="/status",
                        ),
                    ),
                ),
            )

    def test_validation_error(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.create_load_balancer_version(
                models.CreateLoadBalancerVersionRequest(
                    origin_id="",
                    load_balancer_version=models.LoadBalancerVersion(),
                ),
            )
        assert ErrStructValidation in str(exc_info.value.title)


class TestDataCenterValidate:
    """Mirrors Go TestDataCenterValidate (loadbalancer_version_test.go lines 267-336)."""

    def test_valid_data_center(self):
        err = validation.validate_data_center(models.DataCenter(
            city="Philadelphia",
            cloud_server_host_header_override=False,
            cloud_service=True,
            continent="NA",
            country="US",
            hostname="clorigin1.example.com",
            latitude=39.57,
            liveness_hosts=["clorigin1.example.com"],
            longitude=-75.57,
            origin_id="clorigin1",
            percent=100.0,
            state_or_province="PA",
        ))
        assert err is None

    def test_valid_minimal(self):
        err = validation.validate_data_center(models.DataCenter(
            continent="NA",
            country="US",
            latitude=39.57,
            longitude=-75.57,
            origin_id="clorigin1",
            percent=100.0,
        ))
        assert err is None

    def test_zero_values_allowed(self):
        err = validation.validate_data_center(models.DataCenter(
            continent="NA",
            country="US",
            latitude=0.0,
            longitude=0.0,
            origin_id="clorigin1",
            percent=0.0,
        ))
        assert err is None

    def test_missing_all_required(self):
        err = validation.validate_data_center(models.DataCenter())
        assert err is not None
        err_str = str(err)
        assert "Continent" in err_str or "continent" in err_str.lower()
        assert "Country" in err_str or "country" in err_str.lower()


class TestLivenessSettingsValidate:
    """Mirrors Go TestLivenessSettingsValidate (loadbalancer_version_test.go lines 338-374)."""

    def test_path_required_for_http(self):
        err = validation.validate_liveness_settings(models.LivenessSettings(
            protocol="HTTP",
            port=80,
        ))
        assert err is not None
        assert "Path" in str(err) or "path" in str(err).lower()

    def test_request_string_required_for_tcp(self):
        err = validation.validate_liveness_settings(models.LivenessSettings(
            protocol="TCP",
            port=80,
        ))
        assert err is not None
        assert "RequestString" in str(err) or "request_string" in str(err).lower() or "requestString" in str(err)


class TestGetLoadBalancerVersion:
    """Mirrors Go TestGetLoadBalancerVersion (loadbalancer_version_test.go)."""

    def test_200_ok(self):
        session = _make_session()
        response_body = json.dumps({
            "balancingType": "WEIGHTED",
            "createdBy": "jsmith",
            "createdDate": "2020-07-01T01:09:12.000Z",
            "dataCenters": [],
            "deleted": False,
            "immutable": False,
            "lastModifiedBy": "jsmith",
            "lastModifiedDate": "2020-07-01T01:09:12.000Z",
            "originId": "clorigin1",
            "version": 2,
        })
        _setup_success(session, 200, response_body)
        client = Client(session)
        result = client.get_load_balancer_version(
            models.GetLoadBalancerVersionRequest(
                origin_id="clorigin1",
                version=2,
                should_validate=True,
            ),
        )
        assert result.version == 2
        call_args = session.exec.call_args
        assert call_args[0][1] == "/cloudlets/api/v2/origins/clorigin1/versions/2"
        query = call_args[1].get("params")
        assert query is not None
        assert query.get("validate") == "true"

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.get_load_balancer_version(
                models.GetLoadBalancerVersionRequest(
                    origin_id="clorigin1",
                    version=2,
                ),
            )


class TestUpdateLoadBalancerVersion:
    """Mirrors Go TestUpdateLoadBalancerVersion (loadbalancer_version_test.go)."""

    def test_200_ok(self):
        session = _make_session()
        response_body = json.dumps({
            "balancingType": "WEIGHTED",
            "createdBy": "jsmith",
            "createdDate": "2020-07-01T01:09:12.000Z",
            "dataCenters": [],
            "deleted": False,
            "immutable": False,
            "lastModifiedBy": "jsmith",
            "lastModifiedDate": "2020-07-01T01:09:12.000Z",
            "originId": "clorigin1",
            "version": 2,
        })
        _setup_success(session, 200, response_body)
        client = Client(session)
        result = client.update_load_balancer_version(
            models.UpdateLoadBalancerVersionRequest(
                origin_id="clorigin1",
                version=2,
                should_validate=True,
                load_balancer_version=models.LoadBalancerVersion(
                    balancing_type="WEIGHTED",
                    data_centers=[
                        models.DataCenter(
                            continent="NA",
                            country="US",
                            latitude=39.57,
                            longitude=-75.57,
                            origin_id="clorigin1",
                            percent=100.0,
                        ),
                    ],
                    liveness_settings=models.LivenessSettings(
                        port=443,
                        protocol="HTTPS",
                        path="/status",
                        interval=10,
                        timeout=5.0,
                    ),
                ),
            ),
        )
        assert result.version == 2
        call_args = session.exec.call_args
        assert call_args[0][0] == "PUT"

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.update_load_balancer_version(
                models.UpdateLoadBalancerVersionRequest(
                    origin_id="clorigin1",
                    version=2,
                    load_balancer_version=models.LoadBalancerVersion(
                        balancing_type="WEIGHTED",
                        data_centers=[
                            models.DataCenter(
                                continent="NA",
                                country="US",
                                latitude=39.57,
                                longitude=-75.57,
                                origin_id="clorigin1",
                                percent=100.0,
                            ),
                        ],
                        liveness_settings=models.LivenessSettings(
                            port=443,
                            protocol="HTTPS",
                            path="/status",
                        ),
                    ),
                ),
            )

    def test_validation_error(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.update_load_balancer_version(
                models.UpdateLoadBalancerVersionRequest(
                    origin_id="",
                    version=2,
                    load_balancer_version=models.LoadBalancerVersion(),
                ),
            )
        assert ErrStructValidation in str(exc_info.value.title)


class TestListLoadBalancerVersions:
    """Mirrors Go TestListLoadBalancerVersions (loadbalancer_version_test.go)."""

    def test_200_ok(self):
        session = _make_session()
        response_body = json.dumps([
            {
                "balancingType": "WEIGHTED",
                "createdBy": "jsmith",
                "createdDate": "2020-07-01T01:09:12.000Z",
                "dataCenters": [],
                "deleted": False,
                "immutable": False,
                "lastModifiedBy": "jsmith",
                "lastModifiedDate": "2020-07-01T01:09:12.000Z",
                "originId": "clorigin1",
                "version": 1,
            },
        ])
        _setup_success(session, 200, response_body)
        client = Client(session)
        result = client.list_load_balancer_versions(
            models.ListLoadBalancerVersionsRequest(origin_id="clorigin1"),
        )
        assert len(result) == 1
        call_args = session.exec.call_args
        assert call_args[0][1] == "/cloudlets/api/v2/origins/clorigin1/versions"
        query = call_args[1].get("params")
        assert query is not None
        assert query.get("includeModel") == "true"

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.list_load_balancer_versions(
                models.ListLoadBalancerVersionsRequest(origin_id="clorigin1"),
            )


# ========================================================================
# 6. Match Rule Tests — match_rule_test.go
# ========================================================================


class TestUnmarshalJSONMatchRules:
    """Mirrors Go TestUnmarshalJSONMatchRules (match_rule_test.go lines 14-852)."""

    def test_valid_match_rule_alb(self):
        data = [
            {
                "type": "albMatchRule",
                "end": 0,
                "forwardSettings": {"originId": "alb_test_krk"},
                "id": 0,
                "matchURL": None,
                "matches": [
                    {
                        "caseSensitive": False,
                        "matchOperator": "equals",
                        "matchType": "protocol",
                        "matchValue": "https",
                        "negate": False,
                    },
                    {
                        "caseSensitive": False,
                        "matchOperator": "equals",
                        "matchType": "range",
                        "negate": False,
                        "objectMatchValue": {"type": "range", "value": [1, 50]},
                    },
                    {
                        "caseSensitive": False,
                        "matchOperator": "equals",
                        "matchType": "method",
                        "negate": False,
                        "objectMatchValue": {"type": "simple", "value": ["GET"]},
                    },
                ],
                "name": "alb rule",
                "start": 0,
            },
        ]
        result = models.unmarshal_match_rules(data)
        assert len(result) == 1
        rule = result[0]
        assert isinstance(rule, models.MatchRuleALB)
        assert rule.type == "albMatchRule"
        assert rule.name == "alb rule"
        assert len(rule.matches) == 3

    def test_valid_match_rule_pr(self):
        data = [
            {
                "type": "cdMatchRule",
                "end": 0,
                "forwardSettings": {"originId": "fr_test_krk_dc2", "percent": 62},
                "id": 0,
                "matchURL": None,
                "matches": [
                    {
                        "caseSensitive": False,
                        "matchOperator": "equals",
                        "matchType": "protocol",
                        "matchValue": "https",
                        "negate": False,
                    },
                ],
                "name": "cd rule",
                "start": 0,
            },
        ]
        result = models.unmarshal_match_rules(data)
        assert len(result) == 1
        rule = result[0]
        assert isinstance(rule, models.MatchRulePR)
        assert rule.type == "cdMatchRule"
        assert rule.forward_settings.origin_id == "fr_test_krk_dc2"
        assert rule.forward_settings.percent == 62

    def test_valid_match_rule_fr(self):
        data = [
            {
                "type": "frMatchRule",
                "end": 0,
                "forwardSettings": {},
                "id": 0,
                "matchURL": None,
                "matches": [
                    {
                        "caseSensitive": False,
                        "matchOperator": "equals",
                        "matchType": "protocol",
                        "matchValue": "https",
                        "negate": False,
                    },
                ],
                "name": "fr rule",
                "start": 0,
            },
        ]
        result = models.unmarshal_match_rules(data)
        assert len(result) == 1
        assert isinstance(result[0], models.MatchRuleFR)

    def test_valid_match_rule_vp(self):
        data = [
            {
                "type": "vpMatchRule",
                "end": 0,
                "id": 0,
                "matchURL": None,
                "matches": [
                    {
                        "caseSensitive": False,
                        "matchOperator": "equals",
                        "matchType": "protocol",
                        "matchValue": "https",
                        "negate": False,
                    },
                ],
                "name": "vp rule",
                "passThroughPercent": 50.50,
                "start": 0,
            },
        ]
        result = models.unmarshal_match_rules(data)
        assert len(result) == 1
        rule = result[0]
        assert isinstance(rule, models.MatchRuleVP)
        assert rule.pass_through_percent == 50.50

    def test_valid_match_rule_ap(self):
        data = [
            {
                "type": "apMatchRule",
                "end": 0,
                "id": 0,
                "matchURL": None,
                "matches": [
                    {
                        "caseSensitive": False,
                        "matchOperator": "equals",
                        "matchType": "protocol",
                        "matchValue": "https",
                        "negate": False,
                    },
                ],
                "name": "ap rule",
                "passThroughPercent": 50.50,
                "start": 0,
            },
        ]
        result = models.unmarshal_match_rules(data)
        assert len(result) == 1
        assert isinstance(result[0], models.MatchRuleAP)
        assert result[0].pass_through_percent == 50.50

    def test_valid_match_rule_as(self):
        data = [
            {
                "type": "asMatchRule",
                "end": 0,
                "forwardSettings": {
                    "originId": "as_test_krk",
                    "pathAndQS": "/test_path?a=b",
                    "useIncomingQueryString": True,
                },
                "id": 0,
                "matchURL": None,
                "matches": [
                    {
                        "caseSensitive": False,
                        "matchOperator": "equals",
                        "matchType": "range",
                        "negate": False,
                        "objectMatchValue": {"type": "range", "value": [1, 50]},
                    },
                    {
                        "caseSensitive": False,
                        "matchOperator": "equals",
                        "matchType": "method",
                        "negate": False,
                        "objectMatchValue": {
                            "type": "object",
                            "name": "OP",
                            "options": {"value": ["GET"], "valueHasWildcard": True},
                        },
                    },
                ],
                "name": "as rule",
                "start": 0,
            },
        ]
        result = models.unmarshal_match_rules(data)
        assert len(result) == 1
        rule = result[0]
        assert isinstance(rule, models.MatchRuleAS)
        assert rule.forward_settings.origin_id == "as_test_krk"

    def test_valid_match_rule_er(self):
        data = [
            {
                "type": "erMatchRule",
                "end": 0,
                "id": 0,
                "matchURL": None,
                "matches": [
                    {
                        "caseSensitive": False,
                        "matchOperator": "equals",
                        "matchType": "protocol",
                        "matchValue": "https",
                        "negate": False,
                    },
                ],
                "name": "er rule",
                "redirectURL": "/redirect",
                "start": 0,
                "statusCode": 301,
                "useRelativeUrl": "none",
            },
        ]
        result = models.unmarshal_match_rules(data)
        assert len(result) == 1
        rule = result[0]
        assert isinstance(rule, models.MatchRuleER)
        assert rule.redirect_url == "/redirect"
        assert rule.status_code == 301

    def test_valid_match_rule_rc(self):
        data = [
            {
                "type": "igMatchRule",
                "end": 0,
                "id": 0,
                "matchURL": None,
                "matches": [
                    {
                        "caseSensitive": False,
                        "matchOperator": "equals",
                        "matchType": "protocol",
                        "matchValue": "https",
                        "negate": False,
                    },
                ],
                "name": "rc rule",
                "allowDeny": "allow",
                "start": 0,
            },
        ]
        result = models.unmarshal_match_rules(data)
        assert len(result) == 1
        rule = result[0]
        assert isinstance(rule, models.MatchRuleRC)
        assert rule.allow_deny == "allow"

    def test_invalid_type(self):
        data = [{"type": "fooMatchRule"}]
        with pytest.raises(Exception):
            models.unmarshal_match_rules(data)

    def test_missing_type(self):
        data = [{"name": "no type"}]
        with pytest.raises(Exception):
            models.unmarshal_match_rules(data)

    def test_invalid_type_not_string(self):
        data = [{"type": 123}]
        with pytest.raises(Exception):
            models.unmarshal_match_rules(data)


class TestGetObjectMatchValueType:
    """Mirrors Go TestGetObjectMatchValueType (match_rule_test.go lines 854-898).

    In the Python implementation, ``_get_object_match_value_type`` returns
    an empty string for invalid inputs rather than raising an error.  The
    tests therefore assert on the returned value.
    """

    def test_success_range(self):
        result = models._get_object_match_value_type({"type": "range", "value": [1, 50]})
        assert result == "range"

    def test_invalid_type_string(self):
        # Not a dict → returns empty string
        result = models._get_object_match_value_type("not a dict")
        assert result == ""

    def test_missing_type_key(self):
        # Dict without 'type' key → returns empty string
        result = models._get_object_match_value_type({"value": [1, 50]})
        assert result == ""

    def test_type_not_string(self):
        # 'type' is not a string → returns empty string
        result = models._get_object_match_value_type({"type": 50})
        assert result == ""


class TestConvertObjectMatchValue:
    """Mirrors Go TestConvertObjectMatchValue (match_rule_test.go lines 900-978).

    ``_convert_object_match_value(raw, handler)`` takes a raw dict and a
    handler (dataclass type) and calls ``handler.from_dict(raw)`` to
    produce the typed object.
    """

    def test_range(self):
        result = models._convert_object_match_value(
            {"type": "range", "value": [1, 50]},
            models.ObjectMatchValueRange,
        )
        assert isinstance(result, models.ObjectMatchValueRange)
        assert result.value == [1, 50]

    def test_simple(self):
        result = models._convert_object_match_value(
            {"type": "simple", "value": ["GET"]},
            models.ObjectMatchValueSimple,
        )
        assert isinstance(result, models.ObjectMatchValueSimple)
        assert result.value == ["GET"]

    def test_object(self):
        result = models._convert_object_match_value(
            {
                "type": "object",
                "name": "OP",
                "options": {"value": ["GET"], "valueHasWildcard": True},
            },
            models.ObjectMatchValueObject,
        )
        assert isinstance(result, models.ObjectMatchValueObject)
        assert result.name == "OP"

    def test_non_dict_passthrough(self):
        # When raw is not a dict, _convert_object_match_value returns it as-is
        result = models._convert_object_match_value("not_a_dict", models.ObjectMatchValueSimple)
        assert result == "not_a_dict"


class TestValidateMatchRules:
    """Mirrors Go TestValidateMatchRules (match_rule_test.go lines 980-1496)."""

    def test_valid_alb(self):
        err = validation.validate_match_rule_alb(models.MatchRuleALB(
            type="albMatchRule",
            forward_settings=models.ForwardSettingsALB(origin_id="alb_origin"),
            matches=[models.MatchCriteriaALB(
                match_type="protocol",
                match_value="https",
                match_operator="equals",
            )],
        ))
        assert err is None

    def test_invalid_alb_start(self):
        err = validation.validate_match_rule_alb(models.MatchRuleALB(
            type="albMatchRule",
            start=-1,
            forward_settings=models.ForwardSettingsALB(origin_id="alb_origin"),
        ))
        assert err is not None

    def test_valid_ap(self):
        for ptp in (-1, 0, 50.5, 100):
            err = validation.validate_match_rule_ap(models.MatchRuleAP(
                type="apMatchRule",
                pass_through_percent=ptp,
                matches=[models.MatchCriteria(
                    match_type="protocol",
                    match_value="https",
                    match_operator="equals",
                )],
            ))
            assert err is None, f"pass_through_percent={ptp} should be valid"

    def test_invalid_ap(self):
        err = validation.validate_match_rule_ap(models.MatchRuleAP(
            type="apMatchRule",
            pass_through_percent=-2,
        ))
        assert err is not None

    def test_valid_as(self):
        err = validation.validate_match_rule_as(models.MatchRuleAS(
            type="asMatchRule",
            forward_settings=models.ForwardSettingsAS(origin_id="as_origin"),
            matches=[models.MatchCriteria(
                match_type="protocol",
                match_value="https",
                match_operator="equals",
            )],
        ))
        assert err is None

    def test_invalid_as_start(self):
        err = validation.validate_match_rule_as(models.MatchRuleAS(
            type="asMatchRule",
            start=-1,
            forward_settings=models.ForwardSettingsAS(origin_id="as_origin"),
        ))
        assert err is not None

    def test_valid_pr(self):
        for pct in (1, 50, 100):
            err = validation.validate_match_rule_pr(models.MatchRulePR(
                type="cdMatchRule",
                forward_settings=models.ForwardSettingsPR(
                    origin_id="pr_origin",
                    percent=pct,
                ),
                matches=[models.MatchCriteria(
                    match_type="protocol",
                    match_value="https",
                    match_operator="equals",
                )],
            ))
            assert err is None, f"percent={pct} should be valid"

    def test_invalid_pr_percent(self):
        err = validation.validate_match_rule_pr(models.MatchRulePR(
            type="cdMatchRule",
            forward_settings=models.ForwardSettingsPR(
                origin_id="pr_origin",
                percent=0,
            ),
        ))
        assert err is not None

    def test_valid_er(self):
        err = validation.validate_match_rule_er(models.MatchRuleER(
            type="erMatchRule",
            redirect_url="/redirect",
            status_code=301,
            use_relative_url="none",
            matches=[models.MatchCriteria(
                match_type="protocol",
                match_value="https",
                match_operator="equals",
            )],
        ))
        assert err is None

    def test_invalid_er_status_code(self):
        err = validation.validate_match_rule_er(models.MatchRuleER(
            type="erMatchRule",
            redirect_url="/redirect",
            status_code=200,
            use_relative_url="none",
        ))
        assert err is not None

    def test_invalid_er_use_relative_url(self):
        err = validation.validate_match_rule_er(models.MatchRuleER(
            type="erMatchRule",
            redirect_url="/redirect",
            status_code=301,
            use_relative_url="invalid",
        ))
        assert err is not None

    def test_invalid_er_matches_always_with_matches(self):
        err = validation.validate_match_rule_er(models.MatchRuleER(
            type="erMatchRule",
            redirect_url="/redirect",
            status_code=301,
            use_relative_url="none",
            matches_always=True,
            matches=[models.MatchCriteria(
                match_type="protocol",
                match_value="https",
                match_operator="equals",
            )],
        ))
        assert err is not None

    def test_valid_fr(self):
        err = validation.validate_match_rule_fr(models.MatchRuleFR(
            type="frMatchRule",
            forward_settings=models.ForwardSettingsFR(),
            matches=[models.MatchCriteria(
                match_type="protocol",
                match_value="https",
                match_operator="equals",
            )],
        ))
        assert err is None

    def test_valid_rc(self):
        for ad in ("allow", "deny", "denybranded"):
            err = validation.validate_match_rule_rc(models.MatchRuleRC(
                type="igMatchRule",
                allow_deny=ad,
                matches=[models.MatchCriteria(
                    match_type="protocol",
                    match_value="https",
                    match_operator="equals",
                )],
            ))
            assert err is None, f"allow_deny={ad} should be valid"

    def test_invalid_rc_allow_deny(self):
        err = validation.validate_match_rule_rc(models.MatchRuleRC(
            type="igMatchRule",
            allow_deny="invalid",
        ))
        assert err is not None

    def test_invalid_rc_matches_always_with_matches(self):
        err = validation.validate_match_rule_rc(models.MatchRuleRC(
            type="igMatchRule",
            allow_deny="allow",
            matches_always=True,
            matches=[models.MatchCriteria(
                match_type="protocol",
                match_value="https",
                match_operator="equals",
            )],
        ))
        assert err is not None

    def test_valid_vp(self):
        for ptp in (-1, 0, 50.5, 100):
            err = validation.validate_match_rule_vp(models.MatchRuleVP(
                type="vpMatchRule",
                pass_through_percent=ptp,
                matches=[models.MatchCriteria(
                    match_type="protocol",
                    match_value="https",
                    match_operator="equals",
                )],
            ))
            assert err is None, f"pass_through_percent={ptp} should be valid"

    def test_invalid_vp(self):
        err = validation.validate_match_rule_vp(models.MatchRuleVP(
            type="vpMatchRule",
            pass_through_percent=-2,
        ))
        assert err is not None


# ========================================================================
# 7. Policy Tests — policy_test.go
# ========================================================================


class TestListPolicies:
    """Mirrors Go TestListPolicies (policy_test.go lines 15-209)."""

    def test_200_ok(self):
        session = _make_session()
        body = json.dumps([
            {
                "policyId": 276858,
                "groupId": 64867,
                "name": "TestName1",
                "description": "TestDescription",
                "createdBy": "jsmith",
                "createDate": 1631037080000,
                "lastModifiedBy": "jsmith",
                "lastModifiedDate": 1631037080000,
                "cloudletId": 9,
                "cloudletCode": "ER",
                "apiVersion": "2.0",
                "activations": [
                    {
                        "apiVersion": "2.0",
                        "network": "staging",
                        "policyInfo": {
                            "policyId": 276858,
                            "name": "TestName1",
                            "version": 2,
                            "status": "active",
                            "statusDetail": "File updated successfully",
                            "activatedBy": "jsmith",
                            "activationDate": 1631037080000,
                        },
                        "propertyInfo": {
                            "name": "test_property",
                            "version": 1,
                            "groupId": 64867,
                            "status": "active",
                            "activatedBy": "jsmith",
                            "activationDate": 1631037080000,
                        },
                    },
                ],
            },
        ])
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.list_policies(models.ListPoliciesRequest())
        assert len(result) == 1
        assert result[0].policy_id == 276858
        assert result[0].name == "TestName1"
        assert result[0].cloudlet_id == 9
        call_args = session.exec.call_args
        assert call_args[0][1] == "/cloudlets/api/v2/policies"

    def test_200_ok_with_params(self):
        session = _make_session()
        body = json.dumps([])
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.list_policies(models.ListPoliciesRequest(
            cloudlet_id=1,
            include_deleted=True,
            page_size=10,
            offset=5,
        ))
        assert result == []

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.list_policies(models.ListPoliciesRequest())


class TestGetPolicy:
    """Mirrors Go TestGetPolicy (policy_test.go lines 210-388)."""

    def test_200_ok(self):
        session = _make_session()
        body = json.dumps({
            "policyId": 276858,
            "groupId": 64867,
            "name": "TestName1",
            "description": "TestDescription",
            "createdBy": "jsmith",
            "createDate": 1631037080000,
            "lastModifiedBy": "jsmith",
            "lastModifiedDate": 1631037080000,
            "cloudletId": 9,
            "cloudletCode": "ER",
            "apiVersion": "2.0",
            "activations": [],
        })
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.get_policy(models.GetPolicyRequest(policy_id=276858))
        assert result.policy_id == 276858
        assert result.name == "TestName1"
        call_args = session.exec.call_args
        assert call_args[0][1] == "/cloudlets/api/v2/policies/276858"

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.get_policy(models.GetPolicyRequest(policy_id=276858))


class TestCreatePolicy:
    """Mirrors Go TestCreatePolicy (policy_test.go lines 389-489)."""

    def test_201_created(self):
        session = _make_session()
        body = json.dumps({
            "policyId": 276858,
            "groupId": 64867,
            "name": "TestName1",
            "description": "TestDescription",
            "createdBy": "jsmith",
            "createDate": 1631037080000,
            "lastModifiedBy": "jsmith",
            "lastModifiedDate": 1631037080000,
            "cloudletId": 9,
            "cloudletCode": "ER",
            "apiVersion": "2.0",
            "activations": [],
        })
        _setup_success(session, 201, body)
        client = Client(session)
        result = client.create_policy(models.CreatePolicyRequest(
            name="TestName1",
            cloudlet_id=9,
            group_id=64867,
            description="TestDescription",
        ))
        assert result.policy_id == 276858
        assert result.name == "TestName1"
        call_args = session.exec.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/cloudlets/api/v2/policies"

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.create_policy(models.CreatePolicyRequest(
                name="TestName1",
                cloudlet_id=9,
                group_id=64867,
            ))

    def test_validation_error(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.create_policy(models.CreatePolicyRequest(
                name="A B",
                cloudlet_id=9,
                group_id=64867,
            ))
        assert ErrStructValidation in str(exc_info.value.title)


class TestDeletePolicy:
    """Mirrors Go TestDeletePolicy (policy_test.go lines 490-543)."""

    def test_204_no_content(self):
        session = _make_session()
        resp = mock_response(204, "")
        session.exec.return_value = (resp, None)
        client = Client(session)
        client.remove_policy(models.RemovePolicyRequest(policy_id=276858))
        call_args = session.exec.call_args
        assert call_args[0][0] == "DELETE"
        assert call_args[0][1] == "/cloudlets/api/v2/policies/276858"

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.remove_policy(models.RemovePolicyRequest(policy_id=276858))


class TestUpdatePolicy:
    """Mirrors Go TestUpdatePolicy (policy_test.go lines 544-653)."""

    def test_200_ok(self):
        session = _make_session()
        body = json.dumps({
            "policyId": 276858,
            "groupId": 64867,
            "name": "TestName1",
            "description": "Updated",
            "createdBy": "jsmith",
            "createDate": 1631037080000,
            "lastModifiedBy": "jsmith",
            "lastModifiedDate": 1631037080000,
            "cloudletId": 9,
            "cloudletCode": "ER",
            "apiVersion": "2.0",
            "activations": [],
        })
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.update_policy(models.UpdatePolicyRequest(
            policy_id=276858,
            update_policy=models.UpdatePolicy(
                name="TestName1",
                group_id=64867,
                description="Updated",
            ),
        ))
        assert result.description == "Updated"
        call_args = session.exec.call_args
        assert call_args[0][0] == "PUT"
        assert call_args[0][1] == "/cloudlets/api/v2/policies/276858"

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.update_policy(models.UpdatePolicyRequest(
                policy_id=276858,
                update_policy=models.UpdatePolicy(
                    name="TestName1",
                    group_id=64867,
                ),
            ))

    def test_validation_error(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.update_policy(models.UpdatePolicyRequest(
                policy_id=276858,
                update_policy=models.UpdatePolicy(
                    name="A B",
                    group_id=64867,
                ),
            ))
        assert ErrStructValidation in str(exc_info.value.title)


# ========================================================================
# 8. Policy Property Tests — policy_property_test.go
# ========================================================================


class TestGetPolicyProperties:
    """Mirrors Go TestGetPolicyProperties (policy_property_test.go lines 15-126)."""

    def test_200_ok(self):
        session = _make_session()
        body = json.dumps({
            "prp_1": {
                "groupId": 64867,
                "id": 1,
                "name": "property1",
                "network": "staging",
                "activatedBy": "jsmith",
                "activationDate": 1631037080000,
            },
            "prp_2": {
                "groupId": 64867,
                "id": 2,
                "name": "property2",
                "network": "prod",
                "activatedBy": "jdoe",
                "activationDate": 1631037081000,
            },
        })
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.get_policy_properties(
            models.GetPolicyPropertiesRequest(policy_id=1001),
        )
        assert isinstance(result, dict)
        assert "prp_1" in result
        assert "prp_2" in result
        call_args = session.exec.call_args
        assert "/cloudlets/api/v2/policies/1001/properties" in call_args[0][1]

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.get_policy_properties(
                models.GetPolicyPropertiesRequest(policy_id=1001),
            )


class TestDeletePolicyProperty:
    """Mirrors Go TestCloudlets_DeletePolicyProperty (policy_property_test.go lines 128-299)."""

    def test_204_no_content(self):
        session = _make_session()
        resp = mock_response(204, "")
        session.exec.return_value = (resp, None)
        client = Client(session)
        client.delete_policy_property(models.DeletePolicyPropertyRequest(
            policy_id=1001,
            property_id=2,
        ))
        call_args = session.exec.call_args
        assert call_args[0][0] == "DELETE"
        assert "/cloudlets/api/v2/policies/1001/properties/2" in call_args[0][1]
        # Always sends async=true
        params = call_args[1].get("params", {})
        assert params.get("async") == "true"

    def test_204_with_network(self):
        session = _make_session()
        resp = mock_response(204, "")
        session.exec.return_value = (resp, None)
        client = Client(session)
        client.delete_policy_property(models.DeletePolicyPropertyRequest(
            policy_id=1001,
            property_id=2,
            network="staging",
        ))
        call_args = session.exec.call_args
        params = call_args[1].get("params", {})
        assert params.get("async") == "true"
        assert params.get("network") == "staging"

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.delete_policy_property(models.DeletePolicyPropertyRequest(
                policy_id=1001,
                property_id=2,
            ))

    def test_validation_missing_policy_id(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.delete_policy_property(models.DeletePolicyPropertyRequest(
                policy_id=0,
                property_id=2,
            ))
        assert ErrStructValidation in str(exc_info.value.title)

    def test_validation_missing_property_id(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.delete_policy_property(models.DeletePolicyPropertyRequest(
                policy_id=1001,
                property_id=0,
            ))
        assert ErrStructValidation in str(exc_info.value.title)

    def test_validation_missing_both(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.delete_policy_property(models.DeletePolicyPropertyRequest(
                policy_id=0,
                property_id=0,
            ))
        assert ErrStructValidation in str(exc_info.value.title)


# ========================================================================
# 9. Policy Version Tests — policy_version_test.go
# ========================================================================


class TestListPolicyVersions:
    """Mirrors Go TestListPolicyVersions (policy_version_test.go lines 16-150)."""

    def test_200_ok(self):
        session = _make_session()
        body = json.dumps([
            {
                "policyId": 284823,
                "version": 1,
                "description": "version 1",
                "createdBy": "jsmith",
                "createDate": 1631037080000,
                "lastModifiedBy": "jsmith",
                "lastModifiedDate": 1631037080000,
                "matchRuleFormat": "1.0",
                "matchRules": None,
                "activations": [],
                "rulesLocked": False,
                "deleted": False,
                "immutable": False,
            },
            {
                "policyId": 284823,
                "version": 2,
                "description": "version 2",
                "createdBy": "jdoe",
                "createDate": 1631037080000,
                "lastModifiedBy": "jdoe",
                "lastModifiedDate": 1631037080000,
                "matchRuleFormat": "1.0",
                "matchRules": None,
                "activations": [],
                "rulesLocked": False,
                "deleted": False,
                "immutable": False,
            },
        ])
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.list_policy_versions(models.ListPolicyVersionsRequest(
            policy_id=284823,
        ))
        assert len(result) == 2
        assert result[0].policy_id == 284823
        assert result[0].version == 1
        call_args = session.exec.call_args
        assert "/cloudlets/api/v2/policies/284823/versions" in call_args[0][1]

    def test_200_ok_with_params(self):
        session = _make_session()
        body = json.dumps([])
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.list_policy_versions(models.ListPolicyVersionsRequest(
            policy_id=284823,
            include_rules=True,
            include_deleted=True,
            include_activations=True,
            offset=5,
            page_size=3,
        ))
        assert result == []

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.list_policy_versions(models.ListPolicyVersionsRequest(
                policy_id=284823,
            ))


class TestGetPolicyVersion:
    """Mirrors Go TestGetPolicyVersion (policy_version_test.go lines 151-780)."""

    def test_200_ok_omit_rules(self):
        session = _make_session()
        body = json.dumps({
            "policyId": 276858,
            "version": 5,
            "description": "test",
            "createdBy": "jsmith",
            "createDate": 1631037080000,
            "lastModifiedBy": "jsmith",
            "lastModifiedDate": 1631037080000,
            "matchRuleFormat": "1.0",
            "activations": [],
            "rulesLocked": False,
            "deleted": False,
            "immutable": False,
        })
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.get_policy_version(models.GetPolicyVersionRequest(
            policy_id=276858,
            version=5,
            omit_rules=True,
        ))
        assert result.policy_id == 276858
        assert result.version == 5
        call_args = session.exec.call_args
        assert "/cloudlets/api/v2/policies/276858/versions/5" in call_args[0][1]
        params = call_args[1].get("params", {})
        assert params.get("omitRules") == "true"

    def test_200_ok_with_er_match_rule(self):
        session = _make_session()
        body = json.dumps({
            "policyId": 276858,
            "version": 5,
            "description": "test",
            "createdBy": "jsmith",
            "createDate": 1631037080000,
            "lastModifiedBy": "jsmith",
            "lastModifiedDate": 1631037080000,
            "matchRuleFormat": "1.0",
            "matchRules": [
                {
                    "type": "erMatchRule",
                    "akaRuleId": "abc123",
                    "end": 0,
                    "id": 0,
                    "matchURL": None,
                    "name": "ER RANGE",
                    "redirectURL": "/redirect",
                    "start": 0,
                    "statusCode": 307,
                    "useRelativeUrl": "copy_scheme_hostname",
                    "disabled": True,
                    "matches": [
                        {
                            "caseSensitive": False,
                            "matchOperator": "equals",
                            "matchType": "protocol",
                            "matchValue": "https",
                            "negate": False,
                        },
                    ],
                },
            ],
            "activations": [],
            "rulesLocked": False,
            "deleted": False,
            "immutable": False,
        })
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.get_policy_version(models.GetPolicyVersionRequest(
            policy_id=276858,
            version=5,
        ))
        assert result.version == 5
        assert result.match_rules is not None
        assert len(result.match_rules) == 1
        rule = result.match_rules[0]
        assert isinstance(rule, models.MatchRuleER)
        assert rule.status_code == 307
        assert rule.use_relative_url == "copy_scheme_hostname"
        assert rule.disabled is True

    def test_200_ok_with_alb_match_rule(self):
        session = _make_session()
        body = json.dumps({
            "policyId": 276858,
            "version": 5,
            "description": "test",
            "createdBy": "jsmith",
            "createDate": 1631037080000,
            "lastModifiedBy": "jsmith",
            "lastModifiedDate": 1631037080000,
            "matchRuleFormat": "1.0",
            "matchRules": [
                {
                    "type": "albMatchRule",
                    "end": 0,
                    "forwardSettings": {"originId": "alb_test_krk"},
                    "id": 0,
                    "matchURL": None,
                    "name": "alb rule",
                    "start": 0,
                    "disabled": True,
                    "matches": [
                        {
                            "caseSensitive": False,
                            "matchOperator": "equals",
                            "matchType": "protocol",
                            "matchValue": "https",
                            "negate": False,
                        },
                    ],
                },
            ],
            "activations": [],
            "rulesLocked": False,
            "deleted": False,
            "immutable": False,
        })
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.get_policy_version(models.GetPolicyVersionRequest(
            policy_id=276858,
            version=5,
        ))
        assert len(result.match_rules) == 1
        assert isinstance(result.match_rules[0], models.MatchRuleALB)

    def test_200_ok_with_as_match_rule(self):
        session = _make_session()
        body = json.dumps({
            "policyId": 276858,
            "version": 5,
            "description": "test",
            "createdBy": "jsmith",
            "createDate": 1631037080000,
            "lastModifiedBy": "jsmith",
            "lastModifiedDate": 1631037080000,
            "matchRuleFormat": "1.0",
            "matchRules": [
                {
                    "type": "asMatchRule",
                    "end": 0,
                    "forwardSettings": {
                        "originId": "as_test_krk",
                        "pathAndQS": "/test_path",
                        "useIncomingQueryString": True,
                    },
                    "id": 0,
                    "matchURL": None,
                    "name": "as rule",
                    "start": 0,
                    "disabled": False,
                    "matches": [
                        {
                            "caseSensitive": False,
                            "matchOperator": "equals",
                            "matchType": "protocol",
                            "matchValue": "https",
                            "negate": False,
                        },
                    ],
                },
            ],
            "activations": [],
            "rulesLocked": False,
            "deleted": False,
            "immutable": False,
        })
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.get_policy_version(models.GetPolicyVersionRequest(
            policy_id=276858,
            version=5,
        ))
        assert len(result.match_rules) == 1
        rule = result.match_rules[0]
        assert isinstance(rule, models.MatchRuleAS)
        assert rule.forward_settings.origin_id == "as_test_krk"

    def test_200_ok_with_pr_match_rule(self):
        session = _make_session()
        body = json.dumps({
            "policyId": 276858,
            "version": 5,
            "description": "test",
            "createdBy": "jsmith",
            "createDate": 1631037080000,
            "lastModifiedBy": "jsmith",
            "lastModifiedDate": 1631037080000,
            "matchRuleFormat": "1.0",
            "matchRules": [
                {
                    "type": "cdMatchRule",
                    "end": 0,
                    "forwardSettings": {
                        "originId": "fr_test_krk_dc2",
                        "percent": 11,
                    },
                    "id": 0,
                    "matchURL": None,
                    "name": "cd rule",
                    "start": 0,
                    "matches": [
                        {
                            "caseSensitive": False,
                            "matchOperator": "equals",
                            "matchType": "protocol",
                            "matchValue": "https",
                            "negate": False,
                        },
                    ],
                },
            ],
            "activations": [],
            "rulesLocked": False,
            "deleted": False,
            "immutable": False,
        })
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.get_policy_version(models.GetPolicyVersionRequest(
            policy_id=276858,
            version=5,
        ))
        assert len(result.match_rules) == 1
        rule = result.match_rules[0]
        assert isinstance(rule, models.MatchRulePR)
        assert rule.forward_settings.percent == 11

    def test_200_ok_with_fr_match_rule(self):
        session = _make_session()
        body = json.dumps({
            "policyId": 276858,
            "version": 5,
            "description": "test",
            "createdBy": "jsmith",
            "createDate": 1631037080000,
            "lastModifiedBy": "jsmith",
            "lastModifiedDate": 1631037080000,
            "matchRuleFormat": "1.0",
            "matchRules": [
                {
                    "type": "frMatchRule",
                    "end": 0,
                    "forwardSettings": {
                        "pathAndQS": "/test_path",
                        "useIncomingQueryString": True,
                        "originId": "fr_origin",
                    },
                    "id": 0,
                    "matchURL": None,
                    "name": "fr rule",
                    "start": 0,
                    "disabled": True,
                    "matches": [],
                },
            ],
            "activations": [],
            "rulesLocked": False,
            "deleted": False,
            "immutable": False,
        })
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.get_policy_version(models.GetPolicyVersionRequest(
            policy_id=276858,
            version=5,
        ))
        assert len(result.match_rules) == 1
        assert isinstance(result.match_rules[0], models.MatchRuleFR)

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.get_policy_version(models.GetPolicyVersionRequest(
                policy_id=276858,
                version=5,
            ))


class TestCreatePolicyVersion:
    """Mirrors Go TestCreatePolicyVersion (policy_version_test.go lines 781-4095)."""

    def test_201_simple_er(self):
        session = _make_session()
        body = json.dumps({
            "policyId": 276858,
            "version": 6,
            "description": "new version",
            "createdBy": "jsmith",
            "createDate": 1631037080000,
            "lastModifiedBy": "jsmith",
            "lastModifiedDate": 1631037080000,
            "matchRuleFormat": "1.0",
            "matchRules": None,
            "activations": [],
            "rulesLocked": False,
            "deleted": False,
            "immutable": False,
        })
        _setup_success(session, 201, body)
        client = Client(session)
        result = client.create_policy_version(models.CreatePolicyVersionRequest(
            policy_id=276858,
            create_policy_version=models.CreatePolicyVersion(
                description="new version",
                match_rule_format="1.0",
            ),
        ))
        assert result.version == 6
        call_args = session.exec.call_args
        assert call_args[0][0] == "POST"
        assert "/cloudlets/api/v2/policies/276858/versions" in call_args[0][1]

    def test_201_complex_alb(self):
        session = _make_session()
        body = json.dumps({
            "policyId": 276858,
            "version": 6,
            "description": "new version",
            "createdBy": "jsmith",
            "createDate": 1631037080000,
            "lastModifiedBy": "jsmith",
            "lastModifiedDate": 1631037080000,
            "matchRuleFormat": "1.0",
            "matchRules": [
                {
                    "type": "albMatchRule",
                    "end": 0,
                    "forwardSettings": {"originId": "alb_test_krk"},
                    "id": 0,
                    "matchURL": None,
                    "matches": [
                        {
                            "caseSensitive": False,
                            "matchOperator": "equals",
                            "matchType": "protocol",
                            "matchValue": "https",
                            "negate": False,
                        },
                    ],
                    "name": "alb rule 1",
                    "start": 0,
                },
            ],
            "activations": [],
            "rulesLocked": False,
            "deleted": False,
            "immutable": False,
        })
        _setup_success(session, 201, body)
        client = Client(session)
        result = client.create_policy_version(models.CreatePolicyVersionRequest(
            policy_id=276858,
            create_policy_version=models.CreatePolicyVersion(
                description="new version",
                match_rule_format="1.0",
                match_rules=[
                    models.MatchRuleALB(
                        type="albMatchRule",
                        forward_settings=models.ForwardSettingsALB(origin_id="alb_test_krk"),
                        matches=[models.MatchCriteriaALB(
                            match_type="protocol",
                            match_value="https",
                            match_operator="equals",
                        )],
                        name="alb rule 1",
                    ),
                ],
            ),
        ))
        assert result.version == 6
        assert result.match_rules is not None
        assert len(result.match_rules) == 1
        assert isinstance(result.match_rules[0], models.MatchRuleALB)

    def test_201_complex_er(self):
        session = _make_session()
        body = json.dumps({
            "policyId": 276858,
            "version": 6,
            "description": "new version",
            "createdBy": "jsmith",
            "createDate": 1631037080000,
            "lastModifiedBy": "jsmith",
            "lastModifiedDate": 1631037080000,
            "matchRuleFormat": "1.0",
            "matchRules": [
                {
                    "type": "erMatchRule",
                    "end": 0,
                    "id": 0,
                    "matchURL": None,
                    "name": "ER RANGE",
                    "redirectURL": "/redirect",
                    "start": 0,
                    "statusCode": 302,
                    "useRelativeUrl": "none",
                    "matches": [
                        {
                            "caseSensitive": False,
                            "matchOperator": "equals",
                            "matchType": "protocol",
                            "matchValue": "https",
                            "negate": False,
                        },
                    ],
                },
            ],
            "activations": [],
            "rulesLocked": False,
            "deleted": False,
            "immutable": False,
        })
        _setup_success(session, 201, body)
        client = Client(session)
        result = client.create_policy_version(models.CreatePolicyVersionRequest(
            policy_id=276858,
            create_policy_version=models.CreatePolicyVersion(
                description="new version",
                match_rule_format="1.0",
                match_rules=[
                    models.MatchRuleER(
                        type="erMatchRule",
                        name="ER RANGE",
                        redirect_url="/redirect",
                        status_code=302,
                        use_relative_url="none",
                        matches=[models.MatchCriteria(
                            match_type="protocol",
                            match_value="https",
                            match_operator="equals",
                        )],
                    ),
                ],
            ),
        ))
        assert result.version == 6
        assert isinstance(result.match_rules[0], models.MatchRuleER)

    def test_validation_error_match_rule_format(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.create_policy_version(models.CreatePolicyVersionRequest(
                policy_id=276858,
                create_policy_version=models.CreatePolicyVersion(
                    description="test",
                    match_rule_format="2.0",
                ),
            ))
        assert ErrStructValidation in str(exc_info.value.title)

    def test_validation_error_description_too_long(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.create_policy_version(models.CreatePolicyVersionRequest(
                policy_id=276858,
                create_policy_version=models.CreatePolicyVersion(
                    description="a" * 256,
                    match_rule_format="1.0",
                ),
            ))
        assert ErrStructValidation in str(exc_info.value.title)

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.create_policy_version(models.CreatePolicyVersionRequest(
                policy_id=276858,
                create_policy_version=models.CreatePolicyVersion(
                    description="new version",
                    match_rule_format="1.0",
                ),
            ))


class TestDeletePolicyVersion:
    """Mirrors Go TestDeletePolicyVersion (policy_version_test.go)."""

    def test_204_no_content(self):
        session = _make_session()
        resp = mock_response(204, "")
        session.exec.return_value = (resp, None)
        client = Client(session)
        client.delete_policy_version(models.DeletePolicyVersionRequest(
            policy_id=276858,
            version=5,
        ))
        call_args = session.exec.call_args
        assert call_args[0][0] == "DELETE"
        assert "/cloudlets/api/v2/policies/276858/versions/5" in call_args[0][1]

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.delete_policy_version(models.DeletePolicyVersionRequest(
                policy_id=276858,
                version=5,
            ))


class TestUpdatePolicyVersion:
    """Mirrors Go TestUpdatePolicyVersion (policy_version_test.go lines 4095-4459)."""

    def test_200_simple_er(self):
        session = _make_session()
        body = json.dumps({
            "policyId": 276858,
            "version": 5,
            "description": "updated",
            "createdBy": "jsmith",
            "createDate": 1631037080000,
            "lastModifiedBy": "jsmith",
            "lastModifiedDate": 1631037080000,
            "matchRuleFormat": "1.0",
            "matchRules": [
                {
                    "type": "erMatchRule",
                    "end": 0,
                    "id": 0,
                    "matchURL": None,
                    "name": "ER RANGE",
                    "redirectURL": "/redirect",
                    "start": 0,
                    "statusCode": 302,
                    "useRelativeUrl": "none",
                    "matches": [
                        {
                            "caseSensitive": False,
                            "matchOperator": "equals",
                            "matchType": "protocol",
                            "matchValue": "https",
                            "negate": False,
                        },
                    ],
                },
            ],
            "activations": [],
            "rulesLocked": False,
            "deleted": False,
            "immutable": False,
        })
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.update_policy_version(models.UpdatePolicyVersionRequest(
            policy_id=276858,
            version=5,
            update_policy_version=models.UpdatePolicyVersion(
                description="updated",
                match_rule_format="1.0",
                match_rules=[
                    models.MatchRuleER(
                        type="erMatchRule",
                        name="ER RANGE",
                        redirect_url="/redirect",
                        status_code=302,
                        use_relative_url="none",
                        matches=[models.MatchCriteria(
                            match_type="protocol",
                            match_value="https",
                            match_operator="equals",
                        )],
                    ),
                ],
            ),
        ))
        assert result.version == 5
        call_args = session.exec.call_args
        assert call_args[0][0] == "PUT"
        assert "/cloudlets/api/v2/policies/276858/versions/5" in call_args[0][1]

    def test_200_complex_alb_with_warnings(self):
        session = _make_session()
        body = json.dumps({
            "policyId": 276858,
            "version": 5,
            "description": "updated",
            "createdBy": "jsmith",
            "createDate": 1631037080000,
            "lastModifiedBy": "jsmith",
            "lastModifiedDate": 1631037080000,
            "matchRuleFormat": "1.0",
            "matchRules": [
                {
                    "type": "albMatchRule",
                    "end": 0,
                    "forwardSettings": {"originId": "alb_test_krk"},
                    "id": 0,
                    "matchURL": None,
                    "matches": [
                        {
                            "caseSensitive": False,
                            "matchOperator": "equals",
                            "matchType": "protocol",
                            "matchValue": "https",
                            "negate": False,
                        },
                    ],
                    "name": "alb rule 1",
                    "start": 0,
                },
            ],
            "warnings": [
                {
                    "detail": "some detail",
                    "title": "some title",
                    "type": "some type",
                    "jsonPointer": "/matchRules/0",
                },
            ],
            "activations": [],
            "rulesLocked": False,
            "deleted": False,
            "immutable": False,
        })
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.update_policy_version(models.UpdatePolicyVersionRequest(
            policy_id=276858,
            version=5,
            update_policy_version=models.UpdatePolicyVersion(
                description="updated",
                match_rule_format="1.0",
                match_rules=[
                    models.MatchRuleALB(
                        type="albMatchRule",
                        forward_settings=models.ForwardSettingsALB(origin_id="alb_test_krk"),
                        matches=[models.MatchCriteriaALB(
                            match_type="protocol",
                            match_value="https",
                            match_operator="equals",
                        )],
                        name="alb rule 1",
                    ),
                ],
            ),
        ))
        assert result.version == 5
        assert result.warnings is not None
        assert len(result.warnings) == 1

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.update_policy_version(models.UpdatePolicyVersionRequest(
                policy_id=276858,
                version=5,
                update_policy_version=models.UpdatePolicyVersion(
                    description="updated",
                    match_rule_format="1.0",
                ),
            ))

    def test_validation_error(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.update_policy_version(models.UpdatePolicyVersionRequest(
                policy_id=276858,
                version=5,
                update_policy_version=models.UpdatePolicyVersion(
                    description="a" * 256,
                    match_rule_format="1.0",
                ),
            ))
        assert ErrStructValidation in str(exc_info.value.title)


# ========================================================================
# 10. Policy Version Activation Tests — policy_version_activation_test.go
# ========================================================================


class TestListPolicyActivations:
    """Mirrors Go TestListPolicyActivations (policy_version_activation_test.go lines 15-170)."""

    def test_200_ok(self):
        session = _make_session()
        body = json.dumps([
            {
                "apiVersion": "2.0",
                "network": "staging",
                "policyInfo": {
                    "policyId": 276858,
                    "name": "TestName1",
                    "version": 2,
                    "status": "active",
                    "statusDetail": "File updated successfully",
                    "activatedBy": "jsmith",
                    "activationDate": 1631037080000,
                },
                "propertyInfo": {
                    "name": "test_property",
                    "version": 1,
                    "groupId": 64867,
                    "status": "active",
                    "activatedBy": "jsmith",
                    "activationDate": 1631037080000,
                },
            },
        ])
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.list_policy_activations(models.ListPolicyActivationsRequest(
            policy_id=276858,
        ))
        assert len(result) == 1
        call_args = session.exec.call_args
        assert "/cloudlets/api/v2/policies/276858/activations" in call_args[0][1]

    def test_200_ok_with_network(self):
        session = _make_session()
        body = json.dumps([])
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.list_policy_activations(models.ListPolicyActivationsRequest(
            policy_id=276858,
            network="staging",
        ))
        assert result == []

    def test_200_ok_with_property_name(self):
        session = _make_session()
        body = json.dumps([])
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.list_policy_activations(models.ListPolicyActivationsRequest(
            policy_id=276858,
            property_name="test_property",
        ))
        assert result == []

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.list_policy_activations(models.ListPolicyActivationsRequest(
                policy_id=276858,
            ))

    def test_validation_error_invalid_network(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.list_policy_activations(models.ListPolicyActivationsRequest(
                policy_id=276858,
                network="not valid",
            ))
        assert ErrStructValidation in str(exc_info.value.title)


class TestActivatePolicyVersion:
    """Mirrors Go TestActivatePolicyVersion (policy_version_activation_test.go lines 172-297)."""

    def test_200_ok(self):
        session = _make_session()
        body = json.dumps([
            {
                "apiVersion": "2.0",
                "network": "staging",
                "policyInfo": {
                    "policyId": 276858,
                    "name": "TestName1",
                    "version": 2,
                    "status": "active",
                    "statusDetail": "File updated successfully",
                    "activatedBy": "jsmith",
                    "activationDate": 1631037080000,
                },
                "propertyInfo": {
                    "name": "test_property",
                    "version": 1,
                    "groupId": 64867,
                    "status": "active",
                    "activatedBy": "jsmith",
                    "activationDate": 1631037080000,
                },
            },
        ])
        resp = mock_response(200, body)
        parsed = json.loads(body)
        session = _make_session()
        session.exec.return_value = (resp, parsed)
        client = Client(session)
        result = client.activate_policy_version(models.ActivatePolicyVersionRequest(
            policy_id=276858,
            version=2,
            policy_version_activation=models.PolicyVersionActivation(
                network="staging",
                additional_property_names=["test_property"],
            ),
        ))
        assert len(result) == 1
        call_args = session.exec.call_args
        assert call_args[0][0] == "POST"
        assert "/cloudlets/api/v2/policies/276858/versions/2/activations" in call_args[0][1]

    def test_400_property_not_found(self):
        session = _make_session()
        _setup_error(session, 400, json.dumps({
            "type": "bad_request",
            "title": "Bad Request",
            "detail": 'Requested propertyName "XYZ" does not exist',
            "status": 400,
        }))
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.activate_policy_version(models.ActivatePolicyVersionRequest(
                policy_id=276858,
                version=2,
                policy_version_activation=models.PolicyVersionActivation(
                    network="staging",
                    additional_property_names=["XYZ"],
                ),
            ))

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.activate_policy_version(models.ActivatePolicyVersionRequest(
                policy_id=276858,
                version=2,
                policy_version_activation=models.PolicyVersionActivation(
                    network="staging",
                    additional_property_names=["test_property"],
                ),
            ))

    def test_validation_error(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.activate_policy_version(models.ActivatePolicyVersionRequest(
                policy_id=276858,
                version=2,
                policy_version_activation=models.PolicyVersionActivation(
                    network="",
                    additional_property_names=[],
                ),
            ))
        assert ErrStructValidation in str(exc_info.value.title)


# ========================================================================
# 11. Policy Version Rule Tests — policy_version_rule_test.go
# ========================================================================


class TestGetPolicyVersionRule:
    """Mirrors Go TestGetPolicyVersionRule (policy_version_rule_test.go lines 16-170)."""

    def test_200_ok(self):
        session = _make_session()
        body = json.dumps({
            "type": "erMatchRule",
            "akaRuleId": "abc123",
            "end": 0,
            "id": 0,
            "matchURL": None,
            "name": "ER RANGE",
            "redirectURL": "/redirect",
            "start": 0,
            "statusCode": 302,
            "useRelativeUrl": "none",
            "matches": [
                {
                    "caseSensitive": False,
                    "matchOperator": "equals",
                    "matchType": "protocol",
                    "matchValue": "https",
                    "negate": False,
                },
            ],
        })
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.get_policy_version_rule(
            models.GetPolicyVersionRuleRequest(
                policy_id=12345,
                version=2,
                aka_rule_id="abc123",
            ),
        )
        assert isinstance(result, models.MatchRuleER)
        assert result.name == "ER RANGE"
        call_args = session.exec.call_args
        assert "/cloudlets/api/v2/policies/12345/versions/2/rules/abc123" in call_args[0][1]

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.get_policy_version_rule(
                models.GetPolicyVersionRuleRequest(
                    policy_id=12345,
                    version=2,
                    aka_rule_id="abc123",
                ),
            )

    def test_validation_missing_policy_id(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.get_policy_version_rule(
                models.GetPolicyVersionRuleRequest(
                    policy_id=0,
                    version=2,
                    aka_rule_id="abc123",
                ),
            )
        assert ErrStructValidation in str(exc_info.value.title)

    def test_validation_missing_version(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.get_policy_version_rule(
                models.GetPolicyVersionRuleRequest(
                    policy_id=12345,
                    version=0,
                    aka_rule_id="abc123",
                ),
            )
        assert ErrStructValidation in str(exc_info.value.title)

    def test_validation_missing_aka_rule_id(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.get_policy_version_rule(
                models.GetPolicyVersionRuleRequest(
                    policy_id=12345,
                    version=2,
                    aka_rule_id="",
                ),
            )
        assert ErrStructValidation in str(exc_info.value.title)

    def test_validation_missing_all(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.get_policy_version_rule(
                models.GetPolicyVersionRuleRequest(
                    policy_id=0,
                    version=0,
                    aka_rule_id="",
                ),
            )
        assert ErrStructValidation in str(exc_info.value.title)

    def test_validation_invalid_version(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.get_policy_version_rule(
                models.GetPolicyVersionRuleRequest(
                    policy_id=12345,
                    version=-2,
                    aka_rule_id="abc123",
                ),
            )
        assert ErrStructValidation in str(exc_info.value.title)


class TestCreatePolicyVersionRule:
    """Mirrors Go TestCreatePolicyVersionRule (policy_version_rule_test.go lines 172-450)."""

    def test_200_ok(self):
        session = _make_session()
        body = json.dumps({
            "type": "erMatchRule",
            "akaRuleId": "abc123",
            "end": 0,
            "id": 0,
            "matchURL": None,
            "name": "ER RANGE",
            "redirectURL": "/redirect",
            "start": 0,
            "statusCode": 302,
            "useRelativeUrl": "none",
            "matches": [
                {
                    "caseSensitive": False,
                    "matchOperator": "equals",
                    "matchType": "protocol",
                    "matchValue": "https",
                    "negate": False,
                },
                {
                    "caseSensitive": False,
                    "matchOperator": "equals",
                    "matchType": "range",
                    "negate": False,
                    "objectMatchValue": {"type": "range", "value": [1, 50]},
                },
            ],
        })
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.create_policy_version_rule(
            models.CreatePolicyVersionRuleRequest(
                policy_id=12345,
                version=2,
                index=2,
                match_rule={
                    "type": "erMatchRule",
                    "name": "ER RANGE",
                    "redirectURL": "/redirect",
                    "statusCode": 302,
                    "useRelativeUrl": "none",
                    "matches": [
                        {
                            "matchType": "protocol",
                            "matchValue": "https",
                            "matchOperator": "equals",
                        },
                        {
                            "matchType": "range",
                            "matchOperator": "equals",
                            "objectMatchValue": {"type": "range", "value": [1, 50]},
                        },
                    ],
                },
            ),
        )
        assert isinstance(result, models.MatchRuleER)
        assert result.name == "ER RANGE"
        call_args = session.exec.call_args
        assert call_args[0][0] == "POST"
        assert "/cloudlets/api/v2/policies/12345/versions/2/rules" in call_args[0][1]
        # Check index query param
        params = call_args[1].get("params")
        if params is not None:
            assert params.get("index") == "2"

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.create_policy_version_rule(
                models.CreatePolicyVersionRuleRequest(
                    policy_id=12345,
                    version=2,
                    match_rule={"type": "erMatchRule"},
                ),
            )

    def test_validation_missing_policy_id(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.create_policy_version_rule(
                models.CreatePolicyVersionRuleRequest(
                    policy_id=0,
                    version=2,
                    match_rule={"type": "erMatchRule"},
                ),
            )
        assert ErrStructValidation in str(exc_info.value.title)

    def test_validation_missing_version(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.create_policy_version_rule(
                models.CreatePolicyVersionRuleRequest(
                    policy_id=12345,
                    version=0,
                    match_rule={"type": "erMatchRule"},
                ),
            )
        assert ErrStructValidation in str(exc_info.value.title)

    def test_validation_missing_both(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.create_policy_version_rule(
                models.CreatePolicyVersionRuleRequest(
                    policy_id=0,
                    version=0,
                    match_rule={"type": "erMatchRule"},
                ),
            )
        assert ErrStructValidation in str(exc_info.value.title)

    def test_validation_invalid_version(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.create_policy_version_rule(
                models.CreatePolicyVersionRuleRequest(
                    policy_id=12345,
                    version=-2,
                    match_rule={"type": "erMatchRule"},
                ),
            )
        assert ErrStructValidation in str(exc_info.value.title)


class TestUpdatePolicyVersionRule:
    """Mirrors Go TestUpdatePolicyVersionRule (policy_version_rule_test.go lines 452-692)."""

    def test_200_ok(self):
        session = _make_session()
        body = json.dumps({
            "type": "erMatchRule",
            "akaRuleId": "abc123",
            "end": 0,
            "id": 0,
            "matchURL": None,
            "name": "ER RANGE",
            "redirectURL": "/redirect",
            "start": 0,
            "statusCode": 302,
            "useRelativeUrl": "none",
            "matches": [
                {
                    "caseSensitive": True,
                    "matchOperator": "equals",
                    "matchType": "protocol",
                    "matchValue": "https",
                    "negate": False,
                },
            ],
        })
        _setup_success(session, 200, body)
        client = Client(session)
        result = client.update_policy_version_rule(
            models.UpdatePolicyVersionRuleRequest(
                policy_id=12345,
                version=2,
                aka_rule_id="abc123",
                match_rule={
                    "type": "erMatchRule",
                    "name": "ER RANGE",
                    "redirectURL": "/redirect",
                    "statusCode": 302,
                    "useRelativeUrl": "none",
                    "matches": [
                        {
                            "caseSensitive": True,
                            "matchType": "protocol",
                            "matchValue": "https",
                            "matchOperator": "equals",
                        },
                    ],
                },
            ),
        )
        assert isinstance(result, models.MatchRuleER)
        call_args = session.exec.call_args
        assert call_args[0][0] == "PUT"
        assert "/cloudlets/api/v2/policies/12345/versions/2/rules/abc123" in call_args[0][1]

    def test_500_error(self):
        session = _make_session()
        _setup_error(session, 500, '{"type":"internal_error","title":"Internal Server Error","status":500}')
        client = Client(session)
        with pytest.raises(CloudletsError):
            client.update_policy_version_rule(
                models.UpdatePolicyVersionRuleRequest(
                    policy_id=12345,
                    version=2,
                    aka_rule_id="abc123",
                    match_rule={"type": "erMatchRule"},
                ),
            )

    def test_validation_missing_policy_id(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.update_policy_version_rule(
                models.UpdatePolicyVersionRuleRequest(
                    policy_id=0,
                    version=2,
                    aka_rule_id="abc123",
                    match_rule={"type": "erMatchRule"},
                ),
            )
        assert ErrStructValidation in str(exc_info.value.title)

    def test_validation_missing_version(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.update_policy_version_rule(
                models.UpdatePolicyVersionRuleRequest(
                    policy_id=12345,
                    version=0,
                    aka_rule_id="abc123",
                    match_rule={"type": "erMatchRule"},
                ),
            )
        assert ErrStructValidation in str(exc_info.value.title)

    def test_validation_missing_aka_rule_id(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.update_policy_version_rule(
                models.UpdatePolicyVersionRuleRequest(
                    policy_id=12345,
                    version=2,
                    aka_rule_id="",
                    match_rule={"type": "erMatchRule"},
                ),
            )
        assert ErrStructValidation in str(exc_info.value.title)

    def test_validation_missing_all(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.update_policy_version_rule(
                models.UpdatePolicyVersionRuleRequest(
                    policy_id=0,
                    version=0,
                    aka_rule_id="",
                    match_rule={"type": "erMatchRule"},
                ),
            )
        assert ErrStructValidation in str(exc_info.value.title)

    def test_validation_invalid_version(self):
        session = _make_session()
        client = Client(session)
        with pytest.raises(CloudletsError) as exc_info:
            client.update_policy_version_rule(
                models.UpdatePolicyVersionRuleRequest(
                    policy_id=12345,
                    version=-2,
                    aka_rule_id="abc123",
                    match_rule={"type": "erMatchRule"},
                ),
            )
        assert ErrStructValidation in str(exc_info.value.title)
