# pylint: disable=too-many-lines
"""Comprehensive unit tests for the Bot Manager API client.

Mirrors every Go ``*_test.go`` file in ``pkg/botman/`` — same scenarios,
same assertions, and VERBATIM response body / header values from Go fixtures.
Covers all 97 Go test functions across 34 source files.
"""
import json
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.botman.botman import BotManClient
from akamai.edgegrid.botman import errors
from akamai.edgegrid.botman import models
from akamai.edgegrid.botman.test.conftest import (
    create_mock_response,
    setup_mock_response,
    assert_request_made,
)

# ---------------------------------------------------------------------------
# Common UUIDs — VERBATIM from Go test fixtures
# ---------------------------------------------------------------------------
UUID1 = "b85e3eaa-d334-466d-857e-33308ce416be"
UUID2 = "69acad64-7459-4c1d-9bad-672600150127"
UUID3 = "cc9c3f89-e179-4892-89cf-d5e623ba9dc7"
UUID4 = "10c54ea3-e3cb-4fc0-b0e0-fa3658aebd7b"
UUID5 = "4d64d85a-a07f-485a-bbac-24c60658a1b8"

# Sequence UUIDs (ContentProtectionRuleSequence)
FAKE_UUID1 = "fake3f89-e179-4892-89cf-d5e623ba9dc7"
FAKE_UUID2 = "fake85df-e399-43e8-bb0f-c0d980a88e4f"
FAKE_UUID3 = "fake9b8-4fd5-430e-a061-1c61df1d2ac2"

# Sequence UUIDs (CustomBotCategorySequence / CustomClientSequence)
SEQ_UUID1 = "cc9c3f89-e179-4892-89cf-d5e623ba9dc7"
SEQ_UUID2 = "d79285df-e399-43e8-bb0f-c0d980a88e4f"
SEQ_UUID3 = "afa309b8-4fd5-430e-a061-1c61df1d2ac2"

# Recategorized bot category UUIDs
RCAT_UUID1 = "39cbadc6-0e5b-4077-85e0-69b2cf291aa7"
RCAT_UUID2 = "5eb700c8-cff7-4095-b2fc-5e1120c6ef64"
RCAT_UUID3 = "0d38d0fe-b05d-42f6-a58f-bc98c821793e"
RCAT_UUID4 = "87a152a9-e22c-412c-903f-c7cad42dd755"
RCAT_UUID5 = "b61a3017-7014-4b87-aba8-581f7e07f47e"

# CustomBotCategoryItemSequence category UUID
CBCIS_CAT_UUID = "f4f0cb20-eddb-4421-93d9-90954e509d5f"

# Standard test parameters (from Go test constants)
TEST_CONFIG_ID = 43253
TEST_VERSION = 15
TEST_SECURITY_POLICY_ID = "AAAA_81230"


# ---------------------------------------------------------------------------
# Response body builder helpers — produce VERBATIM Go fixture content
# ---------------------------------------------------------------------------

def _five_items(key, id_field, name_field=None):
    """Build standard 5-item list response body (VERBATIM Go fixture).

    When *name_field* is supplied each item also carries a name entry whose
    value mirrors the positional ``testValue<N>`` pattern so that
    client-side name-based filtering can be exercised.
    """
    items = []
    for idx, uid in enumerate([UUID1, UUID2, UUID3, UUID4, UUID5], start=1):
        item = {id_field: uid, "testKey": f"testValue{idx}"}
        if name_field:
            item[name_field] = f"testValue{idx}"
        items.append(item)
    return json.dumps({key: items})


def _single():
    """Build single-item dict body with no ID."""
    return json.dumps({"testKey": "testValue3"})


def _single_with_id(id_field):
    """Build single-item dict body WITH an ID field."""
    return json.dumps({id_field: UUID3, "testKey": "testValue3"})


def _err(detail="Error fetching data"):
    """Build standard 500 error response body."""
    return json.dumps({
        "type": "internal_error",
        "title": "Internal Server Error",
        "detail": detail,
        "status": 500,
    })


# ---------------------------------------------------------------------------
# Generic assertion helpers
# ---------------------------------------------------------------------------

def _assert_server_error(exc_info, detail="Error fetching data"):
    """Assert a standard 500 server error was raised."""
    err = exc_info.value
    assert err.type == "internal_error"
    assert err.title == "Internal Server Error"
    assert err.detail == detail
    assert err.status_code == 500


def _assert_validation_error(exc_info, *fields):
    """Assert a struct validation error containing expected field(s)."""
    err = exc_info.value
    assert err.type == errors.ErrStructValidation
    for fld in fields:
        assert fld in err.detail, f"Expected '{fld}' in: {err.detail}"


# ===================================================================== #
#  3.0  Core — TestClient  (botman_test.go)
# ===================================================================== #

class TestClient:
    """Tests for BotManClient constructor (mirrors Go TestClient)."""

    def test_client_constructor(self):
        """BotManClient can be instantiated with a session."""
        session = MagicMock()
        client = BotManClient(session)
        assert client is not None

    def test_client_constructor_with_options(self):
        """BotManClient accepts a session and is a BotManClient instance."""
        session = MagicMock()
        client = BotManClient(session)
        assert isinstance(client, BotManClient)


# ===================================================================== #
#  3.1  Error — TestJsonErrorUnmarshalling  (errors_test.go)
# ===================================================================== #

class TestJsonErrorUnmarshalling:  # pylint: disable=too-few-public-methods
    """Tests for Error.from_response with non-JSON bodies (3 scenarios)."""

    @pytest.mark.parametrize("name,body,status_code", [
        (
            "HTML response",
            "<HTML><HEAD>\n<TITLE>Access Denied</TITLE>\n</HEAD><BODY>\n"
            "<H1>Access Denied</H1>\n\nYou don't have permission to access "
            "\"http://akaa-baseurl.luna.akamaiapis.net/\" on this server.<P>\n"
            "Reference&#32;&#35;18.6a3d0e17.1706192932.2215b0e6\n\n"
            "</BODY>\n</HTML>",
            503,
        ),
        (
            "plain text response",
            "Your request did not succeed as this operation has reached "
            " the limit for your account. Please try after "
            "2024-01-16T15:20:55.945Z",
            503,
        ),
        (
            "XML response",
            '<Root><Item id="1" name="Example" /></Root>',
            503,
        ),
    ])
    def test_non_json_error_unmarshalling(self, name, body, status_code):
        """Error.from_response correctly parses non-JSON error bodies."""
        _ = name  # used only as parametrize label
        mock_resp = create_mock_response(status_code, body)
        err = errors.Error.from_response(mock_resp)
        assert err.status_code == status_code
        assert "Failed to unmarshal error body" in err.title


# ===================================================================== #
#  3.2  AkamaiBotCategory  (akamai_bot_category_test.go)
# ===================================================================== #

class TestGetAkamaiBotCategoryList:
    """Tests for get_akamai_bot_category_list (3 scenarios)."""

    def test_200_ok(self, mock_session, botman_client):
        """200 OK — returns all 5 categories."""
        setup_mock_response(mock_session, 200, _five_items("categories", "categoryId"))
        result = botman_client.get_akamai_bot_category_list(
            models.GetAkamaiBotCategoryListRequest())
        assert_request_made(mock_session, "GET", "/appsec/v1/akamai-bot-categories")
        assert len(result.categories) == 5

    def test_200_ok_one_record(self, mock_session, botman_client):
        """200 OK One Record — filter by categoryName returns 1 match."""
        setup_mock_response(mock_session, 200,
                            _five_items("categories", "categoryId",
                                        name_field="categoryName"))
        result = botman_client.get_akamai_bot_category_list(
            models.GetAkamaiBotCategoryListRequest(category_name="testValue3"))
        assert len(result.categories) == 1

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_akamai_bot_category_list(
                models.GetAkamaiBotCategoryListRequest())
        _assert_server_error(exc_info)


# ===================================================================== #
#  3.3  AkamaiBotCategoryAction  (akamai_bot_category_action_test.go)
# ===================================================================== #

class TestGetAkamaiBotCategoryActionList:
    """Tests for get_akamai_bot_category_action_list (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             f"/akamai-bot-category-actions")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK — returns all 5 actions."""
        setup_mock_response(mock_session, 200, _five_items("actions", "categoryId"))
        r = botman_client.get_akamai_bot_category_action_list(
            models.GetAkamaiBotCategoryActionListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID))
        assert_request_made(mock_session, "GET", self._path)
        assert len(r.akamai_bot_category_actions) == 5

    def test_200_ok_one_record(self, mock_session, botman_client):
        """200 OK One Record — filter by CategoryID."""
        setup_mock_response(mock_session, 200, _five_items("actions", "categoryId"))
        r = botman_client.get_akamai_bot_category_action_list(
            models.GetAkamaiBotCategoryActionListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID, category_id=UUID3))
        assert len(r.akamai_bot_category_actions) == 1

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_akamai_bot_category_action_list(
                models.GetAkamaiBotCategoryActionListRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_akamai_bot_category_action_list(
                models.GetAkamaiBotCategoryActionListRequest(
                    version=TEST_VERSION, security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_akamai_bot_category_action_list(
                models.GetAkamaiBotCategoryActionListRequest(
                    config_id=TEST_CONFIG_ID, security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "Version")


class TestGetAkamaiBotCategoryAction:
    """Tests for get_akamai_bot_category_action (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             f"/akamai-bot-category-actions/{UUID3}")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.get_akamai_bot_category_action(
            models.GetAkamaiBotCategoryActionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID, category_id=UUID3))
        assert_request_made(mock_session, "GET", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_akamai_bot_category_action(
                models.GetAkamaiBotCategoryActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID, category_id=UUID3))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_akamai_bot_category_action(
                models.GetAkamaiBotCategoryActionRequest(
                    version=TEST_VERSION, security_policy_id=TEST_SECURITY_POLICY_ID,
                    category_id=UUID3))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_akamai_bot_category_action(
                models.GetAkamaiBotCategoryActionRequest(
                    config_id=TEST_CONFIG_ID, security_policy_id=TEST_SECURITY_POLICY_ID,
                    category_id=UUID3))
        _assert_validation_error(exc_info, "Version")

    def test_missing_category_id(self, botman_client):
        """Validation error — missing CategoryID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_akamai_bot_category_action(
                models.GetAkamaiBotCategoryActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "CategoryID")


class TestUpdateAkamaiBotCategoryAction:
    """Tests for update_akamai_bot_category_action (6 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             f"/akamai-bot-category-actions/{UUID3}")
    _payload = {"categoryId": UUID3, "testKey": "testValue3"}

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.update_akamai_bot_category_action(
            models.UpdateAkamaiBotCategoryActionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID,
                category_id=UUID3, json_payload=self._payload))
        assert_request_made(mock_session, "PUT", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_akamai_bot_category_action(
                models.UpdateAkamaiBotCategoryActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    category_id=UUID3, json_payload=self._payload))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_akamai_bot_category_action(
                models.UpdateAkamaiBotCategoryActionRequest(
                    version=TEST_VERSION, security_policy_id=TEST_SECURITY_POLICY_ID,
                    category_id=UUID3, json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_akamai_bot_category_action(
                models.UpdateAkamaiBotCategoryActionRequest(
                    config_id=TEST_CONFIG_ID, security_policy_id=TEST_SECURITY_POLICY_ID,
                    category_id=UUID3, json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_category_id(self, botman_client):
        """Validation error — missing CategoryID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_akamai_bot_category_action(
                models.UpdateAkamaiBotCategoryActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "CategoryID")

    def test_missing_json_payload(self, botman_client):
        """Validation error — missing JsonPayload."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_akamai_bot_category_action(
                models.UpdateAkamaiBotCategoryActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID, category_id=UUID3))
        _assert_validation_error(exc_info, "JsonPayload")


# ===================================================================== #
#  3.4  AkamaiDefinedBot  (akamai_defined_bot_test.go)
# ===================================================================== #

class TestGetAkamaiDefinedBotList:
    """Tests for get_akamai_defined_bot_list (3 scenarios)."""

    def test_200_ok(self, mock_session, botman_client):
        """200 OK — returns all 5 bots."""
        setup_mock_response(mock_session, 200, _five_items("bots", "botId"))
        r = botman_client.get_akamai_defined_bot_list(
            models.GetAkamaiDefinedBotListRequest())
        assert_request_made(mock_session, "GET", "/appsec/v1/akamai-defined-bots")
        assert len(r.bots) == 5

    def test_200_ok_one_record(self, mock_session, botman_client):
        """200 OK One Record — filter by botName."""
        setup_mock_response(mock_session, 200,
                            _five_items("bots", "botId",
                                        name_field="botName"))
        r = botman_client.get_akamai_defined_bot_list(
            models.GetAkamaiDefinedBotListRequest(bot_name="testValue3"))
        assert len(r.bots) == 1

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_akamai_defined_bot_list(
                models.GetAkamaiDefinedBotListRequest())
        _assert_server_error(exc_info)


# ===================================================================== #
#  3.5  BotAnalyticsCookie  (bot_analytics_cookie_test.go)
# ===================================================================== #

class TestGetBotAnalyticsCookie:
    """Tests for get_bot_analytics_cookie (4 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/advanced-settings/bot-analytics-cookie")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.get_bot_analytics_cookie(
            models.GetBotAnalyticsCookieRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        assert_request_made(mock_session, "GET", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_analytics_cookie(
                models.GetBotAnalyticsCookieRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_analytics_cookie(
                models.GetBotAnalyticsCookieRequest(version=TEST_VERSION))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_analytics_cookie(
                models.GetBotAnalyticsCookieRequest(config_id=TEST_CONFIG_ID))
        _assert_validation_error(exc_info, "Version")


class TestUpdateBotAnalyticsCookie:
    """Tests for update_bot_analytics_cookie (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/advanced-settings/bot-analytics-cookie")
    _payload = {"testKey": "testValue3"}

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.update_bot_analytics_cookie(
            models.UpdateBotAnalyticsCookieRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                json_payload=self._payload))
        assert_request_made(mock_session, "PUT", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_bot_analytics_cookie(
                models.UpdateBotAnalyticsCookieRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_bot_analytics_cookie(
                models.UpdateBotAnalyticsCookieRequest(
                    version=TEST_VERSION, json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_bot_analytics_cookie(
                models.UpdateBotAnalyticsCookieRequest(
                    config_id=TEST_CONFIG_ID, json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_json_payload(self, botman_client):
        """Validation error — missing JsonPayload."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_bot_analytics_cookie(
                models.UpdateBotAnalyticsCookieRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "JsonPayload")


# ===================================================================== #
#  3.6  BotAnalyticsCookieValues  (bot_analytics_cookie_values_test.go)
# ===================================================================== #

class TestGetBotAnalyticsCookieValues:
    """Tests for get_bot_analytics_cookie_values (2 scenarios, no params)."""

    def test_200_ok(self, mock_session, botman_client):
        """200 OK — returns values dict."""
        body = json.dumps({"values": ["testValue1", "testValue2", "testValue3",
                                      "testValue4", "testValue5"]})
        setup_mock_response(mock_session, 200, body)
        r = botman_client.get_bot_analytics_cookie_values()
        assert_request_made(mock_session, "GET", "/appsec/v1/bot-analytics-cookie-values")
        assert len(r.get("values", [])) == 5

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_analytics_cookie_values()
        _assert_server_error(exc_info)


# ===================================================================== #
#  3.7  BotCategoryException  (bot_category_exception_test.go)
# ===================================================================== #

class TestGetBotCategoryException:
    """Tests for get_bot_category_exception (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             "/bot-category-exceptions")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.get_bot_category_exception(
            models.GetBotCategoryExceptionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID))
        assert_request_made(mock_session, "GET", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_category_exception(
                models.GetBotCategoryExceptionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_category_exception(
                models.GetBotCategoryExceptionRequest(
                    version=TEST_VERSION, security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_category_exception(
                models.GetBotCategoryExceptionRequest(
                    config_id=TEST_CONFIG_ID, security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error — missing SecurityPolicyID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_category_exception(
                models.GetBotCategoryExceptionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "SecurityPolicyID")


class TestUpdateBotCategoryException:
    """Tests for update_bot_category_exception (6 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             "/bot-category-exceptions")
    _payload = {"testKey": "testValue3"}

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.update_bot_category_exception(
            models.UpdateBotCategoryExceptionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID,
                json_payload=self._payload))
        assert_request_made(mock_session, "PUT", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_bot_category_exception(
                models.UpdateBotCategoryExceptionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_bot_category_exception(
                models.UpdateBotCategoryExceptionRequest(
                    version=TEST_VERSION, security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_bot_category_exception(
                models.UpdateBotCategoryExceptionRequest(
                    config_id=TEST_CONFIG_ID, security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error — missing SecurityPolicyID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_bot_category_exception(
                models.UpdateBotCategoryExceptionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "SecurityPolicyID")

    def test_missing_json_payload(self, botman_client):
        """Validation error — missing JsonPayload."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_bot_category_exception(
                models.UpdateBotCategoryExceptionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "JsonPayload")


# ===================================================================== #
#  3.8  BotDetection  (bot_detection_test.go)
# ===================================================================== #

class TestGetBotDetectionList:
    """Tests for get_bot_detection_list (3 scenarios)."""

    def test_200_ok(self, mock_session, botman_client):
        """200 OK — returns all 5 detections."""
        setup_mock_response(mock_session, 200, _five_items("detections", "detectionId"))
        r = botman_client.get_bot_detection_list(
            models.GetBotDetectionListRequest())
        assert_request_made(mock_session, "GET", "/appsec/v1/bot-detections")
        assert len(r.detections) == 5

    def test_200_ok_one_record(self, mock_session, botman_client):
        """200 OK One Record — filter by DetectionName."""
        setup_mock_response(mock_session, 200,
                            _five_items("detections", "detectionId",
                                        name_field="detectionName"))
        r = botman_client.get_bot_detection_list(
            models.GetBotDetectionListRequest(detection_name="testValue3"))
        assert len(r.detections) == 1

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_detection_list(
                models.GetBotDetectionListRequest())
        _assert_server_error(exc_info)


# ===================================================================== #
#  3.9  BotDetectionAction  (bot_detection_action_test.go)
# ===================================================================== #

class TestGetBotDetectionActionList:
    """Tests for get_bot_detection_action_list (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             "/bot-detection-actions")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK — returns all 5 actions."""
        setup_mock_response(mock_session, 200, _five_items("actions", "detectionId"))
        r = botman_client.get_bot_detection_action_list(
            models.GetBotDetectionActionListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID))
        assert_request_made(mock_session, "GET", self._path)
        assert len(r.bot_detection_actions) == 5

    def test_200_ok_one_record(self, mock_session, botman_client):
        """200 OK One Record — filter by DetectionID."""
        setup_mock_response(mock_session, 200, _five_items("actions", "detectionId"))
        r = botman_client.get_bot_detection_action_list(
            models.GetBotDetectionActionListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID, detection_id=UUID3))
        assert len(r.bot_detection_actions) == 1

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error fetching actions"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_detection_action_list(
                models.GetBotDetectionActionListRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_server_error(exc_info, "Error fetching actions")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_detection_action_list(
                models.GetBotDetectionActionListRequest(
                    version=TEST_VERSION, security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version_and_security_policy_id(self, botman_client):
        """Validation error — missing Version and SecurityPolicyID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_detection_action_list(
                models.GetBotDetectionActionListRequest(config_id=TEST_CONFIG_ID))
        _assert_validation_error(exc_info, "SecurityPolicyID", "Version")


class TestGetBotDetectionAction:
    """Tests for get_bot_detection_action (6 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             f"/bot-detection-actions/{UUID3}")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.get_bot_detection_action(
            models.GetBotDetectionActionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID, detection_id=UUID3))
        assert_request_made(mock_session, "GET", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error fetching match target"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_detection_action(
                models.GetBotDetectionActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID, detection_id=UUID3))
        _assert_server_error(exc_info, "Error fetching match target")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_detection_action(
                models.GetBotDetectionActionRequest(
                    version=TEST_VERSION, security_policy_id=TEST_SECURITY_POLICY_ID,
                    detection_id=UUID3))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_detection_action(
                models.GetBotDetectionActionRequest(
                    config_id=TEST_CONFIG_ID, security_policy_id=TEST_SECURITY_POLICY_ID,
                    detection_id=UUID3))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error — missing SecurityPolicyID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_detection_action(
                models.GetBotDetectionActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION, detection_id=UUID3))
        _assert_validation_error(exc_info, "SecurityPolicyID")

    def test_missing_detection_id(self, botman_client):
        """Validation error — missing DetectionID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_detection_action(
                models.GetBotDetectionActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "DetectionID")


class TestUpdateBotDetectionAction:
    """Tests for update_bot_detection_action (7 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             f"/bot-detection-actions/{UUID3}")
    _payload = {"detectionId": UUID3, "testKey": "testValue3"}

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.update_bot_detection_action(
            models.UpdateBotDetectionActionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID,
                detection_id=UUID3, json_payload=self._payload))
        assert_request_made(mock_session, "PUT", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_bot_detection_action(
                models.UpdateBotDetectionActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    detection_id=UUID3, json_payload=self._payload))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_bot_detection_action(
                models.UpdateBotDetectionActionRequest(
                    version=TEST_VERSION, security_policy_id=TEST_SECURITY_POLICY_ID,
                    detection_id=UUID3, json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_bot_detection_action(
                models.UpdateBotDetectionActionRequest(
                    config_id=TEST_CONFIG_ID, security_policy_id=TEST_SECURITY_POLICY_ID,
                    detection_id=UUID3, json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error — missing SecurityPolicyID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_bot_detection_action(
                models.UpdateBotDetectionActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    detection_id=UUID3, json_payload=self._payload))
        _assert_validation_error(exc_info, "SecurityPolicyID")

    def test_missing_detection_id(self, botman_client):
        """Validation error — missing DetectionID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_bot_detection_action(
                models.UpdateBotDetectionActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "DetectionID")

    def test_missing_json_payload(self, botman_client):
        """Validation error — missing JsonPayload."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_bot_detection_action(
                models.UpdateBotDetectionActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID, detection_id=UUID3))
        _assert_validation_error(exc_info, "JsonPayload")


# ===================================================================== #
#  3.10  BotEndpointCoverageReport  (bot_endpoint_coverage_report_test.go)
# ===================================================================== #

class TestGetBotEndpointCoverageReport:
    """Tests for get_bot_endpoint_coverage_report (8 scenarios)."""

    _account_path = "/appsec/v1/bot-endpoint-coverage-report"
    _config_path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
                    "/bot-endpoint-coverage-report")
    _body = json.dumps({
        "operations": [
            {"operationId": UUID1, "testKey": "testValue1"},
            {"operationId": UUID2, "testKey": "testValue2"},
            {"operationId": UUID3, "testKey": "testValue3"},
            {"operationId": UUID4, "testKey": "testValue4"},
            {"operationId": UUID5, "testKey": "testValue5"},
        ]
    })

    def test_200_ok(self, mock_session, botman_client):
        """200 OK — account-level (no config)."""
        setup_mock_response(mock_session, 200, self._body)
        r = botman_client.get_bot_endpoint_coverage_report(
            models.GetBotEndpointCoverageReportRequest())
        assert_request_made(mock_session, "GET", self._account_path)
        assert len(r.operations) == 5

    def test_200_ok_one_record(self, mock_session, botman_client):
        """200 OK One Record — filter by OperationID."""
        setup_mock_response(mock_session, 200, self._body)
        r = botman_client.get_bot_endpoint_coverage_report(
            models.GetBotEndpointCoverageReportRequest(operation_id=UUID3))
        assert len(r.operations) == 1

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error — account-level."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_endpoint_coverage_report(
                models.GetBotEndpointCoverageReportRequest())
        _assert_server_error(exc_info)

    def test_200_ok_with_config(self, mock_session, botman_client):
        """200 OK With config — config-level path."""
        setup_mock_response(mock_session, 200, self._body)
        r = botman_client.get_bot_endpoint_coverage_report(
            models.GetBotEndpointCoverageReportRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        assert_request_made(mock_session, "GET", self._config_path)
        assert len(r.operations) == 5

    def test_200_ok_one_record_with_config(self, mock_session, botman_client):
        """200 OK One Record with config."""
        setup_mock_response(mock_session, 200, self._body)
        r = botman_client.get_bot_endpoint_coverage_report(
            models.GetBotEndpointCoverageReportRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION, operation_id=UUID3))
        assert len(r.operations) == 1

    def test_500_error_with_config(self, mock_session, botman_client):
        """500 internal server error — config-level."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_endpoint_coverage_report(
                models.GetBotEndpointCoverageReportRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — Version set but ConfigID missing."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_endpoint_coverage_report(
                models.GetBotEndpointCoverageReportRequest(version=TEST_VERSION))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — ConfigID set but Version missing."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_endpoint_coverage_report(
                models.GetBotEndpointCoverageReportRequest(config_id=TEST_CONFIG_ID))
        _assert_validation_error(exc_info, "Version")


# ===================================================================== #
#  3.11  BotManagementSetting  (bot_management_setting_test.go)
# ===================================================================== #

class TestGetBotManagementSetting:
    """Tests for get_bot_management_setting (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             "/bot-management-settings")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.get_bot_management_setting(
            models.GetBotManagementSettingRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID))
        assert_request_made(mock_session, "GET", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_management_setting(
                models.GetBotManagementSettingRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_management_setting(
                models.GetBotManagementSettingRequest(
                    version=TEST_VERSION, security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_management_setting(
                models.GetBotManagementSettingRequest(
                    config_id=TEST_CONFIG_ID, security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error — missing SecurityPolicyID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_bot_management_setting(
                models.GetBotManagementSettingRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "SecurityPolicyID")


class TestUpdateBotManagementSetting:
    """Tests for update_bot_management_setting (6 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             "/bot-management-settings")
    _payload = {"testKey": "testValue3"}

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.update_bot_management_setting(
            models.UpdateBotManagementSettingRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID,
                json_payload=self._payload))
        assert_request_made(mock_session, "PUT", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_bot_management_setting(
                models.UpdateBotManagementSettingRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_bot_management_setting(
                models.UpdateBotManagementSettingRequest(
                    version=TEST_VERSION, security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_bot_management_setting(
                models.UpdateBotManagementSettingRequest(
                    config_id=TEST_CONFIG_ID, security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error — missing SecurityPolicyID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_bot_management_setting(
                models.UpdateBotManagementSettingRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "SecurityPolicyID")

    def test_missing_json_payload(self, botman_client):
        """Validation error — missing JsonPayload."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_bot_management_setting(
                models.UpdateBotManagementSettingRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "JsonPayload")


# ===================================================================== #
#  3.12  ChallengeAction  (challenge_action_test.go)
# ===================================================================== #

class TestGetChallengeActionList:
    """Tests for get_challenge_action_list (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/response-actions/challenge-actions")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK — returns all 5 actions."""
        setup_mock_response(mock_session, 200,
                            _five_items("challengeActions", "actionId"))
        r = botman_client.get_challenge_action_list(
            models.GetChallengeActionListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        assert_request_made(mock_session, "GET", self._path)
        assert len(r.challenge_actions) == 5

    def test_200_ok_one_record(self, mock_session, botman_client):
        """200 OK One Record — filter by ActionID."""
        setup_mock_response(mock_session, 200,
                            _five_items("challengeActions", "actionId"))
        r = botman_client.get_challenge_action_list(
            models.GetChallengeActionListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION, action_id=UUID3))
        assert len(r.challenge_actions) == 1

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_challenge_action_list(
                models.GetChallengeActionListRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_challenge_action_list(
                models.GetChallengeActionListRequest(version=TEST_VERSION))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_challenge_action_list(
                models.GetChallengeActionListRequest(config_id=TEST_CONFIG_ID))
        _assert_validation_error(exc_info, "Version")


class TestGetChallengeAction:
    """Tests for get_challenge_action (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/response-actions/challenge-actions/{UUID3}")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.get_challenge_action(
            models.GetChallengeActionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION, action_id=UUID3))
        assert_request_made(mock_session, "GET", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_challenge_action(
                models.GetChallengeActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION, action_id=UUID3))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_challenge_action(
                models.GetChallengeActionRequest(
                    version=TEST_VERSION, action_id=UUID3))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_challenge_action(
                models.GetChallengeActionRequest(
                    config_id=TEST_CONFIG_ID, action_id=UUID3))
        _assert_validation_error(exc_info, "Version")

    def test_missing_action_id(self, botman_client):
        """Validation error — missing ActionID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_challenge_action(
                models.GetChallengeActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "ActionID")


class TestCreateChallengeAction:
    """Tests for create_challenge_action (5 scenarios, expects 201)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/response-actions/challenge-actions")
    _payload = {"testKey": "testValue3"}

    def test_201_created(self, mock_session, botman_client):
        """201 Created."""
        setup_mock_response(mock_session, 201, _single())
        r = botman_client.create_challenge_action(
            models.CreateChallengeActionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                json_payload=self._payload))
        assert_request_made(mock_session, "POST", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error creating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_challenge_action(
                models.CreateChallengeActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_server_error(exc_info, "Error creating data")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_challenge_action(
                models.CreateChallengeActionRequest(
                    version=TEST_VERSION, json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_challenge_action(
                models.CreateChallengeActionRequest(
                    config_id=TEST_CONFIG_ID, json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_json_payload(self, botman_client):
        """Validation error — missing JsonPayload."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_challenge_action(
                models.CreateChallengeActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "JsonPayload")


class TestUpdateChallengeAction:
    """Tests for update_challenge_action (6 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/response-actions/challenge-actions/{UUID3}")
    _payload = {"actionId": UUID3, "testKey": "testValue3"}

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.update_challenge_action(
            models.UpdateChallengeActionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                action_id=UUID3, json_payload=self._payload))
        assert_request_made(mock_session, "PUT", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_challenge_action(
                models.UpdateChallengeActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    action_id=UUID3, json_payload=self._payload))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_challenge_action(
                models.UpdateChallengeActionRequest(
                    version=TEST_VERSION, action_id=UUID3,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_challenge_action(
                models.UpdateChallengeActionRequest(
                    config_id=TEST_CONFIG_ID, action_id=UUID3,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_action_id(self, botman_client):
        """Validation error — missing ActionID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_challenge_action(
                models.UpdateChallengeActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "ActionID")

    def test_missing_json_payload(self, botman_client):
        """Validation error — missing JsonPayload."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_challenge_action(
                models.UpdateChallengeActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    action_id=UUID3))
        _assert_validation_error(exc_info, "JsonPayload")


class TestRemoveChallengeAction:
    """Tests for remove_challenge_action (5 scenarios, expects 204)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/response-actions/challenge-actions/{UUID3}")

    def test_204_no_content(self, mock_session, botman_client):
        """204 No Content."""
        setup_mock_response(mock_session, 204, "{}")
        botman_client.remove_challenge_action(
            models.RemoveChallengeActionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION, action_id=UUID3))
        assert_request_made(mock_session, "DELETE", self._path)

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error deleting match target"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_challenge_action(
                models.RemoveChallengeActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    action_id=UUID3))
        _assert_server_error(exc_info, "Error deleting match target")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_challenge_action(
                models.RemoveChallengeActionRequest(
                    version=TEST_VERSION, action_id=UUID3))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_challenge_action(
                models.RemoveChallengeActionRequest(
                    config_id=TEST_CONFIG_ID, action_id=UUID3))
        _assert_validation_error(exc_info, "Version")

    def test_missing_action_id(self, botman_client):
        """Validation error — missing ActionID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_challenge_action(
                models.RemoveChallengeActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "ActionID")


class TestUpdateGoogleReCaptchaSecretKey:
    """Tests for update_google_recaptcha_secret_key (6 scenarios, expects 204)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/response-actions/challenge-actions/{UUID3}/google-recaptcha-secret-key")

    def test_204_no_content(self, mock_session, botman_client):
        """204 No Content."""
        setup_mock_response(mock_session, 204, "{}")
        botman_client.update_google_recaptcha_secret_key(
            models.UpdateGoogleReCaptchaSecretKeyRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                action_id=UUID3, secret_key="test-secret-key"))
        assert_request_made(mock_session, "PUT", self._path)

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_google_recaptcha_secret_key(
                models.UpdateGoogleReCaptchaSecretKeyRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    action_id=UUID3, secret_key="test-secret-key"))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_google_recaptcha_secret_key(
                models.UpdateGoogleReCaptchaSecretKeyRequest(
                    version=TEST_VERSION, action_id=UUID3,
                    secret_key="test-secret-key"))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_google_recaptcha_secret_key(
                models.UpdateGoogleReCaptchaSecretKeyRequest(
                    config_id=TEST_CONFIG_ID, action_id=UUID3,
                    secret_key="test-secret-key"))
        _assert_validation_error(exc_info, "Version")

    def test_missing_action_id(self, botman_client):
        """Validation error — missing ActionID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_google_recaptcha_secret_key(
                models.UpdateGoogleReCaptchaSecretKeyRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    secret_key="test-secret-key"))
        _assert_validation_error(exc_info, "ActionID")

    def test_missing_secret_key(self, botman_client):
        """Validation error — missing SecretKey."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_google_recaptcha_secret_key(
                models.UpdateGoogleReCaptchaSecretKeyRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    action_id=UUID3))
        _assert_validation_error(exc_info, "SecretKey")


# ===================================================================== #
#  3.13  ChallengeInjectionRules  (challenge_injection_rules_test.go)
# ===================================================================== #

class TestGetChallengeInjectionRules:
    """Tests for get_challenge_injection_rules (4 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/advanced-settings/challenge-injection-rules")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.get_challenge_injection_rules(
            models.GetChallengeInjectionRulesRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        assert_request_made(mock_session, "GET", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_challenge_injection_rules(
                models.GetChallengeInjectionRulesRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_challenge_injection_rules(
                models.GetChallengeInjectionRulesRequest(version=TEST_VERSION))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_challenge_injection_rules(
                models.GetChallengeInjectionRulesRequest(config_id=TEST_CONFIG_ID))
        _assert_validation_error(exc_info, "Version")


class TestUpdateChallengeInjectionRules:
    """Tests for update_challenge_injection_rules (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/advanced-settings/challenge-injection-rules")
    _payload = {"testKey": "testValue3"}

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.update_challenge_injection_rules(
            models.UpdateChallengeInjectionRulesRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                json_payload=self._payload))
        assert_request_made(mock_session, "PUT", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_challenge_injection_rules(
                models.UpdateChallengeInjectionRulesRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_challenge_injection_rules(
                models.UpdateChallengeInjectionRulesRequest(
                    version=TEST_VERSION, json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_challenge_injection_rules(
                models.UpdateChallengeInjectionRulesRequest(
                    config_id=TEST_CONFIG_ID, json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_json_payload(self, botman_client):
        """Validation error — missing JsonPayload."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_challenge_injection_rules(
                models.UpdateChallengeInjectionRulesRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "JsonPayload")


# ===================================================================== #
#  3.14  ClientSideSecurity  (client_side_security_test.go)
# ===================================================================== #

class TestGetClientSideSecurity:
    """Tests for get_client_side_security (4 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/advanced-settings/client-side-security")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.get_client_side_security(
            models.GetClientSideSecurityRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        assert_request_made(mock_session, "GET", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_client_side_security(
                models.GetClientSideSecurityRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_client_side_security(
                models.GetClientSideSecurityRequest(version=TEST_VERSION))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_client_side_security(
                models.GetClientSideSecurityRequest(config_id=TEST_CONFIG_ID))
        _assert_validation_error(exc_info, "Version")


class TestUpdateClientSideSecurity:
    """Tests for update_client_side_security (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/advanced-settings/client-side-security")
    _payload = {"testKey": "testValue3"}

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.update_client_side_security(
            models.UpdateClientSideSecurityRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                json_payload=self._payload))
        assert_request_made(mock_session, "PUT", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_client_side_security(
                models.UpdateClientSideSecurityRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_client_side_security(
                models.UpdateClientSideSecurityRequest(
                    version=TEST_VERSION, json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_client_side_security(
                models.UpdateClientSideSecurityRequest(
                    config_id=TEST_CONFIG_ID, json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_json_payload(self, botman_client):
        """Validation error — missing JsonPayload."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_client_side_security(
                models.UpdateClientSideSecurityRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "JsonPayload")


# ===================================================================== #
#  3.15  ConditionalAction  (conditonal_action_test.go)
# ===================================================================== #

class TestGetConditionalActionList:
    """Tests for get_conditional_action_list (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/response-actions/conditional-actions")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK — returns all 5 actions."""
        setup_mock_response(mock_session, 200,
                            _five_items("conditionalActions", "actionId"))
        r = botman_client.get_conditional_action_list(
            models.GetConditionalActionListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        assert_request_made(mock_session, "GET", self._path)
        assert len(r.conditional_actions) == 5

    def test_200_ok_one_record(self, mock_session, botman_client):
        """200 OK One Record — filter by ActionID."""
        setup_mock_response(mock_session, 200,
                            _five_items("conditionalActions", "actionId"))
        r = botman_client.get_conditional_action_list(
            models.GetConditionalActionListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION, action_id=UUID3))
        assert len(r.conditional_actions) == 1

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_conditional_action_list(
                models.GetConditionalActionListRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_conditional_action_list(
                models.GetConditionalActionListRequest(version=TEST_VERSION))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_conditional_action_list(
                models.GetConditionalActionListRequest(config_id=TEST_CONFIG_ID))
        _assert_validation_error(exc_info, "Version")


class TestGetConditionalAction:
    """Tests for get_conditional_action (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/response-actions/conditional-actions/{UUID3}")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.get_conditional_action(
            models.GetConditionalActionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION, action_id=UUID3))
        assert_request_made(mock_session, "GET", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_conditional_action(
                models.GetConditionalActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION, action_id=UUID3))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_conditional_action(
                models.GetConditionalActionRequest(
                    version=TEST_VERSION, action_id=UUID3))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_conditional_action(
                models.GetConditionalActionRequest(
                    config_id=TEST_CONFIG_ID, action_id=UUID3))
        _assert_validation_error(exc_info, "Version")

    def test_missing_action_id(self, botman_client):
        """Validation error — missing ActionID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_conditional_action(
                models.GetConditionalActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "ActionID")


class TestCreateConditionalAction:
    """Tests for create_conditional_action (5 scenarios, expects 201)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/response-actions/conditional-actions")
    _payload = {"testKey": "testValue3"}

    def test_201_created(self, mock_session, botman_client):
        """201 Created."""
        setup_mock_response(mock_session, 201, _single())
        r = botman_client.create_conditional_action(
            models.CreateConditionalActionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                json_payload=self._payload))
        assert_request_made(mock_session, "POST", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error creating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_conditional_action(
                models.CreateConditionalActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_server_error(exc_info, "Error creating data")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_conditional_action(
                models.CreateConditionalActionRequest(
                    version=TEST_VERSION, json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_conditional_action(
                models.CreateConditionalActionRequest(
                    config_id=TEST_CONFIG_ID, json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_json_payload(self, botman_client):
        """Validation error — missing JsonPayload."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_conditional_action(
                models.CreateConditionalActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "JsonPayload")


class TestUpdateConditionalAction:
    """Tests for update_conditional_action (6 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/response-actions/conditional-actions/{UUID3}")
    _payload = {"actionId": UUID3, "testKey": "testValue3"}

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.update_conditional_action(
            models.UpdateConditionalActionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                action_id=UUID3, json_payload=self._payload))
        assert_request_made(mock_session, "PUT", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_conditional_action(
                models.UpdateConditionalActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    action_id=UUID3, json_payload=self._payload))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_conditional_action(
                models.UpdateConditionalActionRequest(
                    version=TEST_VERSION, action_id=UUID3,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_conditional_action(
                models.UpdateConditionalActionRequest(
                    config_id=TEST_CONFIG_ID, action_id=UUID3,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_action_id(self, botman_client):
        """Validation error — missing ActionID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_conditional_action(
                models.UpdateConditionalActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "ActionID")

    def test_missing_json_payload(self, botman_client):
        """Validation error — missing JsonPayload."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_conditional_action(
                models.UpdateConditionalActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    action_id=UUID3))
        _assert_validation_error(exc_info, "JsonPayload")


class TestRemoveConditionalAction:
    """Tests for remove_conditional_action (5 scenarios, expects 204)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/response-actions/conditional-actions/{UUID3}")

    def test_204_no_content(self, mock_session, botman_client):
        """204 No Content."""
        setup_mock_response(mock_session, 204, "{}")
        botman_client.remove_conditional_action(
            models.RemoveConditionalActionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION, action_id=UUID3))
        assert_request_made(mock_session, "DELETE", self._path)

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error deleting match target"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_conditional_action(
                models.RemoveConditionalActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    action_id=UUID3))
        _assert_server_error(exc_info, "Error deleting match target")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_conditional_action(
                models.RemoveConditionalActionRequest(
                    version=TEST_VERSION, action_id=UUID3))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_conditional_action(
                models.RemoveConditionalActionRequest(
                    config_id=TEST_CONFIG_ID, action_id=UUID3))
        _assert_validation_error(exc_info, "Version")

    def test_missing_action_id(self, botman_client):
        """Validation error — missing ActionID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_conditional_action(
                models.RemoveConditionalActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "ActionID")


# ===================================================================== #
#  3.16  ContentProtectionJavaScriptInjectionRule
# ===================================================================== #

class TestGetContentProtectionJavaScriptInjectionRuleList:
    """Tests for get list (7 scenarios incl SecurityPolicyID)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             "/content-protection-javascript-injection-rules")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK — returns all 5 rules."""
        setup_mock_response(mock_session, 200,
                            _five_items("contentProtectionJavaScriptInjectionRules",
                                        "contentProtectionJavaScriptInjectionRuleId"))
        r = botman_client.get_content_protection_javascript_injection_rule_list(
            models.GetContentProtectionJavaScriptInjectionRuleListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID))
        assert_request_made(mock_session, "GET", self._path)
        assert len(r.content_protection_javascript_injection_rules) == 5

    def test_200_ok_one_record(self, mock_session, botman_client):
        """200 OK One Record — filter by RuleID."""
        setup_mock_response(mock_session, 200,
                            _five_items("contentProtectionJavaScriptInjectionRules",
                                        "contentProtectionJavaScriptInjectionRuleId"))
        r = botman_client.get_content_protection_javascript_injection_rule_list(
            models.GetContentProtectionJavaScriptInjectionRuleListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID,
                content_protection_javascript_injection_rule_id=UUID3))
        assert len(r.content_protection_javascript_injection_rules) == 1

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_content_protection_javascript_injection_rule_list(
                models.GetContentProtectionJavaScriptInjectionRuleListRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_content_protection_javascript_injection_rule_list(
                models.GetContentProtectionJavaScriptInjectionRuleListRequest(
                    version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_content_protection_javascript_injection_rule_list(
                models.GetContentProtectionJavaScriptInjectionRuleListRequest(
                    config_id=TEST_CONFIG_ID,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error — missing SecurityPolicyID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_content_protection_javascript_injection_rule_list(
                models.GetContentProtectionJavaScriptInjectionRuleListRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "SecurityPolicyID")


class TestGetContentProtectionJavaScriptInjectionRule:
    """Tests for get single rule (6 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             f"/content-protection-javascript-injection-rules/{UUID3}")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.get_content_protection_javascript_injection_rule(
            models.GetContentProtectionJavaScriptInjectionRuleRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID,
                content_protection_javascript_injection_rule_id=UUID3))
        assert_request_made(mock_session, "GET", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_content_protection_javascript_injection_rule(
                models.GetContentProtectionJavaScriptInjectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_javascript_injection_rule_id=UUID3))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_content_protection_javascript_injection_rule(
                models.GetContentProtectionJavaScriptInjectionRuleRequest(
                    version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_javascript_injection_rule_id=UUID3))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_content_protection_javascript_injection_rule(
                models.GetContentProtectionJavaScriptInjectionRuleRequest(
                    config_id=TEST_CONFIG_ID,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_javascript_injection_rule_id=UUID3))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error — missing SecurityPolicyID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_content_protection_javascript_injection_rule(
                models.GetContentProtectionJavaScriptInjectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    content_protection_javascript_injection_rule_id=UUID3))
        _assert_validation_error(exc_info, "SecurityPolicyID")

    def test_missing_rule_id(self, botman_client):
        """Validation error — missing RuleID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_content_protection_javascript_injection_rule(
                models.GetContentProtectionJavaScriptInjectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info,
                                 "ContentProtectionJavaScriptInjectionRuleID")


class TestCreateContentProtectionJavaScriptInjectionRule:
    """Tests for create rule (6 scenarios, expects 201)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             "/content-protection-javascript-injection-rules")
    _payload = {"testKey": "testValue3"}

    def test_201_created(self, mock_session, botman_client):
        """201 Created."""
        setup_mock_response(mock_session, 201, _single())
        r = botman_client.create_content_protection_javascript_injection_rule(
            models.CreateContentProtectionJavaScriptInjectionRuleRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID,
                json_payload=self._payload))
        assert_request_made(mock_session, "POST", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error creating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_content_protection_javascript_injection_rule(
                models.CreateContentProtectionJavaScriptInjectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_server_error(exc_info, "Error creating data")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_content_protection_javascript_injection_rule(
                models.CreateContentProtectionJavaScriptInjectionRuleRequest(
                    version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_content_protection_javascript_injection_rule(
                models.CreateContentProtectionJavaScriptInjectionRuleRequest(
                    config_id=TEST_CONFIG_ID,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error — missing SecurityPolicyID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_content_protection_javascript_injection_rule(
                models.CreateContentProtectionJavaScriptInjectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "SecurityPolicyID")

    def test_missing_json_payload(self, botman_client):
        """Validation error — missing JsonPayload."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_content_protection_javascript_injection_rule(
                models.CreateContentProtectionJavaScriptInjectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "JsonPayload")


class TestUpdateContentProtectionJavaScriptInjectionRule:
    """Tests for update rule (7 scenarios incl RuleID)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             f"/content-protection-javascript-injection-rules/{UUID3}")
    _payload = {"testKey": "testValue3"}

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.update_content_protection_javascript_injection_rule(
            models.UpdateContentProtectionJavaScriptInjectionRuleRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID,
                content_protection_javascript_injection_rule_id=UUID3,
                json_payload=self._payload))
        assert_request_made(mock_session, "PUT", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_content_protection_javascript_injection_rule(
                models.UpdateContentProtectionJavaScriptInjectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_javascript_injection_rule_id=UUID3,
                    json_payload=self._payload))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_content_protection_javascript_injection_rule(
                models.UpdateContentProtectionJavaScriptInjectionRuleRequest(
                    version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_javascript_injection_rule_id=UUID3,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_content_protection_javascript_injection_rule(
                models.UpdateContentProtectionJavaScriptInjectionRuleRequest(
                    config_id=TEST_CONFIG_ID,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_javascript_injection_rule_id=UUID3,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error — missing SecurityPolicyID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_content_protection_javascript_injection_rule(
                models.UpdateContentProtectionJavaScriptInjectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    content_protection_javascript_injection_rule_id=UUID3,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "SecurityPolicyID")

    def test_missing_rule_id(self, botman_client):
        """Validation error — missing RuleID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_content_protection_javascript_injection_rule(
                models.UpdateContentProtectionJavaScriptInjectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_validation_error(exc_info,
                                 "ContentProtectionJavaScriptInjectionRuleID")

    def test_missing_json_payload(self, botman_client):
        """Validation error — missing JsonPayload."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_content_protection_javascript_injection_rule(
                models.UpdateContentProtectionJavaScriptInjectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_javascript_injection_rule_id=UUID3))
        _assert_validation_error(exc_info, "JsonPayload")


class TestRemoveContentProtectionJavaScriptInjectionRule:
    """Tests for remove rule (6 scenarios, expects 204)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             f"/content-protection-javascript-injection-rules/{UUID3}")

    def test_204_no_content(self, mock_session, botman_client):
        """204 No Content."""
        setup_mock_response(mock_session, 204, "{}")
        botman_client.remove_content_protection_javascript_injection_rule(
            models.RemoveContentProtectionJavaScriptInjectionRuleRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID,
                content_protection_javascript_injection_rule_id=UUID3))
        assert_request_made(mock_session, "DELETE", self._path)

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error deleting match target"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_content_protection_javascript_injection_rule(
                models.RemoveContentProtectionJavaScriptInjectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_javascript_injection_rule_id=UUID3))
        _assert_server_error(exc_info, "Error deleting match target")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_content_protection_javascript_injection_rule(
                models.RemoveContentProtectionJavaScriptInjectionRuleRequest(
                    version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_javascript_injection_rule_id=UUID3))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_content_protection_javascript_injection_rule(
                models.RemoveContentProtectionJavaScriptInjectionRuleRequest(
                    config_id=TEST_CONFIG_ID,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_javascript_injection_rule_id=UUID3))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error — missing SecurityPolicyID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_content_protection_javascript_injection_rule(
                models.RemoveContentProtectionJavaScriptInjectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    content_protection_javascript_injection_rule_id=UUID3))
        _assert_validation_error(exc_info, "SecurityPolicyID")

    def test_missing_rule_id(self, botman_client):
        """Validation error — missing RuleID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_content_protection_javascript_injection_rule(
                models.RemoveContentProtectionJavaScriptInjectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info,
                                 "ContentProtectionJavaScriptInjectionRuleID")


# ===================================================================== #
#  3.17  ContentProtectionRule  (content_protection_rule_test.go)
# ===================================================================== #

class TestGetContentProtectionRuleList:
    """Tests for get list (7 scenarios incl SecurityPolicyID)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             "/content-protection-rules")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200,
                            _five_items("contentProtectionRules",
                                        "contentProtectionRuleId"))
        r = botman_client.get_content_protection_rule_list(
            models.GetContentProtectionRuleListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID))
        assert_request_made(mock_session, "GET", self._path)
        assert len(r.content_protection_rules) == 5

    def test_200_ok_one_record(self, mock_session, botman_client):
        """200 OK One Record — filter by RuleID."""
        setup_mock_response(mock_session, 200,
                            _five_items("contentProtectionRules",
                                        "contentProtectionRuleId"))
        r = botman_client.get_content_protection_rule_list(
            models.GetContentProtectionRuleListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID,
                content_protection_rule_id=UUID3))
        assert len(r.content_protection_rules) == 1

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_content_protection_rule_list(
                models.GetContentProtectionRuleListRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_content_protection_rule_list(
                models.GetContentProtectionRuleListRequest(
                    version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_content_protection_rule_list(
                models.GetContentProtectionRuleListRequest(
                    config_id=TEST_CONFIG_ID,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error — missing SecurityPolicyID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_content_protection_rule_list(
                models.GetContentProtectionRuleListRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "SecurityPolicyID")


class TestGetContentProtectionRule:
    """Tests for get single rule (6 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             f"/content-protection-rules/{UUID3}")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.get_content_protection_rule(
            models.GetContentProtectionRuleRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID,
                content_protection_rule_id=UUID3))
        assert_request_made(mock_session, "GET", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_content_protection_rule(
                models.GetContentProtectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_rule_id=UUID3))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_content_protection_rule(
                models.GetContentProtectionRuleRequest(
                    version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_rule_id=UUID3))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_content_protection_rule(
                models.GetContentProtectionRuleRequest(
                    config_id=TEST_CONFIG_ID,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_rule_id=UUID3))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error — missing SecurityPolicyID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_content_protection_rule(
                models.GetContentProtectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    content_protection_rule_id=UUID3))
        _assert_validation_error(exc_info, "SecurityPolicyID")

    def test_missing_rule_id(self, botman_client):
        """Validation error — missing ContentProtectionRuleID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_content_protection_rule(
                models.GetContentProtectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "ContentProtectionRuleID")


class TestCreateContentProtectionRule:
    """Tests for create rule (6 scenarios, expects 201)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             "/content-protection-rules")
    _payload = {"testKey": "testValue3"}

    def test_201_created(self, mock_session, botman_client):
        """201 Created."""
        setup_mock_response(mock_session, 201, _single())
        r = botman_client.create_content_protection_rule(
            models.CreateContentProtectionRuleRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID,
                json_payload=self._payload))
        assert_request_made(mock_session, "POST", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error creating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_content_protection_rule(
                models.CreateContentProtectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_server_error(exc_info, "Error creating data")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_content_protection_rule(
                models.CreateContentProtectionRuleRequest(
                    version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_content_protection_rule(
                models.CreateContentProtectionRuleRequest(
                    config_id=TEST_CONFIG_ID,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error — missing SecurityPolicyID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_content_protection_rule(
                models.CreateContentProtectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "SecurityPolicyID")

    def test_missing_json_payload(self, botman_client):
        """Validation error — missing JsonPayload."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_content_protection_rule(
                models.CreateContentProtectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "JsonPayload")


class TestUpdateContentProtectionRule:
    """Tests for update rule (7 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             f"/content-protection-rules/{UUID3}")
    _payload = {"testKey": "testValue3"}

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.update_content_protection_rule(
            models.UpdateContentProtectionRuleRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID,
                content_protection_rule_id=UUID3,
                json_payload=self._payload))
        assert_request_made(mock_session, "PUT", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_content_protection_rule(
                models.UpdateContentProtectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_rule_id=UUID3,
                    json_payload=self._payload))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_content_protection_rule(
                models.UpdateContentProtectionRuleRequest(
                    version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_rule_id=UUID3,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_content_protection_rule(
                models.UpdateContentProtectionRuleRequest(
                    config_id=TEST_CONFIG_ID,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_rule_id=UUID3,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error — missing SecurityPolicyID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_content_protection_rule(
                models.UpdateContentProtectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    content_protection_rule_id=UUID3,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "SecurityPolicyID")

    def test_missing_rule_id(self, botman_client):
        """Validation error — missing ContentProtectionRuleID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_content_protection_rule(
                models.UpdateContentProtectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "ContentProtectionRuleID")

    def test_missing_json_payload(self, botman_client):
        """Validation error — missing JsonPayload."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_content_protection_rule(
                models.UpdateContentProtectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_rule_id=UUID3))
        _assert_validation_error(exc_info, "JsonPayload")


class TestRemoveContentProtectionRule:
    """Tests for remove rule (6 scenarios, expects 204)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             f"/content-protection-rules/{UUID3}")

    def test_204_no_content(self, mock_session, botman_client):
        """204 No Content."""
        setup_mock_response(mock_session, 204, "{}")
        botman_client.remove_content_protection_rule(
            models.RemoveContentProtectionRuleRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID,
                content_protection_rule_id=UUID3))
        assert_request_made(mock_session, "DELETE", self._path)

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error deleting match target"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_content_protection_rule(
                models.RemoveContentProtectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_rule_id=UUID3))
        _assert_server_error(exc_info, "Error deleting match target")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_content_protection_rule(
                models.RemoveContentProtectionRuleRequest(
                    version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_rule_id=UUID3))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_content_protection_rule(
                models.RemoveContentProtectionRuleRequest(
                    config_id=TEST_CONFIG_ID,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_rule_id=UUID3))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error — missing SecurityPolicyID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_content_protection_rule(
                models.RemoveContentProtectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    content_protection_rule_id=UUID3))
        _assert_validation_error(exc_info, "SecurityPolicyID")

    def test_missing_rule_id(self, botman_client):
        """Validation error — missing ContentProtectionRuleID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_content_protection_rule(
                models.RemoveContentProtectionRuleRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "ContentProtectionRuleID")


# ===================================================================== #
#  3.18  ContentProtectionRuleSequence
# ===================================================================== #

# VERBATIM sequence UUIDs from Go test
_CPRS_SEQ = ["fake3f89-e179-4892-89cf-d5e623ba9dc7",
             "fake85df-e399-43e8-bb0f-c0d980a88e4f",
             "fake9b8-4fd5-430e-a061-1c61df1d2ac2"]
_CPRS_BODY = json.dumps({"contentProtectionRuleSequence": _CPRS_SEQ})


class TestGetContentProtectionRuleSequence:
    """Tests for get sequence (5 scenarios) — typed response."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             "/content-protection-rule-sequence")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK — typed response with sequence list."""
        setup_mock_response(mock_session, 200, _CPRS_BODY)
        r = botman_client.get_content_protection_rule_sequence(
            models.GetContentProtectionRuleSequenceRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID))
        assert_request_made(mock_session, "GET", self._path)
        assert r.content_protection_rule_sequence == _CPRS_SEQ

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_content_protection_rule_sequence(
                models.GetContentProtectionRuleSequenceRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_content_protection_rule_sequence(
                models.GetContentProtectionRuleSequenceRequest(
                    version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_content_protection_rule_sequence(
                models.GetContentProtectionRuleSequenceRequest(
                    config_id=TEST_CONFIG_ID,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error — missing SecurityPolicyID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_content_protection_rule_sequence(
                models.GetContentProtectionRuleSequenceRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "SecurityPolicyID")


class TestUpdateContentProtectionRuleSequence:
    """Tests for update sequence (6 scenarios) — typed response."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             "/content-protection-rule-sequence")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK — typed response."""
        setup_mock_response(mock_session, 200, _CPRS_BODY)
        cprs_obj = models.ContentProtectionRuleUUIDSequence(
            content_protection_rule_sequence=_CPRS_SEQ)
        r = botman_client.update_content_protection_rule_sequence(
            models.UpdateContentProtectionRuleSequenceRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID,
                content_protection_rule_sequence=cprs_obj))
        assert_request_made(mock_session, "PUT", self._path)
        assert r.content_protection_rule_sequence == _CPRS_SEQ

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        cprs_obj = models.ContentProtectionRuleUUIDSequence(
            content_protection_rule_sequence=_CPRS_SEQ)
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_content_protection_rule_sequence(
                models.UpdateContentProtectionRuleSequenceRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_rule_sequence=cprs_obj))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        cprs_obj = models.ContentProtectionRuleUUIDSequence(
            content_protection_rule_sequence=_CPRS_SEQ)
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_content_protection_rule_sequence(
                models.UpdateContentProtectionRuleSequenceRequest(
                    version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_rule_sequence=cprs_obj))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        cprs_obj = models.ContentProtectionRuleUUIDSequence(
            content_protection_rule_sequence=_CPRS_SEQ)
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_content_protection_rule_sequence(
                models.UpdateContentProtectionRuleSequenceRequest(
                    config_id=TEST_CONFIG_ID,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    content_protection_rule_sequence=cprs_obj))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error — missing SecurityPolicyID."""
        cprs_obj = models.ContentProtectionRuleUUIDSequence(
            content_protection_rule_sequence=_CPRS_SEQ)
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_content_protection_rule_sequence(
                models.UpdateContentProtectionRuleSequenceRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    content_protection_rule_sequence=cprs_obj))
        _assert_validation_error(exc_info, "SecurityPolicyID")

    def test_missing_sequence(self, botman_client):
        """Validation error — missing Sequence."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_content_protection_rule_sequence(
                models.UpdateContentProtectionRuleSequenceRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "ContentProtectionRuleSequence")


# ===================================================================== #
#  3.19  CustomBotCategory  (custom_bot_category_test.go)
# ===================================================================== #

class TestGetCustomBotCategoryList:
    """Tests for get list (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/custom-bot-categories")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200,
                            _five_items("categories", "categoryId"))
        r = botman_client.get_custom_bot_category_list(
            models.GetCustomBotCategoryListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        assert_request_made(mock_session, "GET", self._path)
        assert len(r.categories) == 5

    def test_200_ok_one_record(self, mock_session, botman_client):
        """200 OK One Record — filter by CategoryID."""
        setup_mock_response(mock_session, 200,
                            _five_items("categories", "categoryId"))
        r = botman_client.get_custom_bot_category_list(
            models.GetCustomBotCategoryListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                category_id=UUID3))
        assert len(r.categories) == 1

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_bot_category_list(
                models.GetCustomBotCategoryListRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_bot_category_list(
                models.GetCustomBotCategoryListRequest(version=TEST_VERSION))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_bot_category_list(
                models.GetCustomBotCategoryListRequest(config_id=TEST_CONFIG_ID))
        _assert_validation_error(exc_info, "Version")


class TestGetCustomBotCategory:
    """Tests for get single (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/custom-bot-categories/{UUID3}")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.get_custom_bot_category(
            models.GetCustomBotCategoryRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION, category_id=UUID3))
        assert_request_made(mock_session, "GET", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_bot_category(
                models.GetCustomBotCategoryRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION, category_id=UUID3))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_bot_category(
                models.GetCustomBotCategoryRequest(
                    version=TEST_VERSION, category_id=UUID3))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_bot_category(
                models.GetCustomBotCategoryRequest(
                    config_id=TEST_CONFIG_ID, category_id=UUID3))
        _assert_validation_error(exc_info, "Version")

    def test_missing_category_id(self, botman_client):
        """Validation error — missing CategoryID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_bot_category(
                models.GetCustomBotCategoryRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "CategoryID")


class TestCreateCustomBotCategory:
    """Tests for create (5 scenarios, expects 201)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/custom-bot-categories")
    _payload = {"testKey": "testValue3"}

    def test_201_created(self, mock_session, botman_client):
        """201 Created."""
        setup_mock_response(mock_session, 201, _single())
        r = botman_client.create_custom_bot_category(
            models.CreateCustomBotCategoryRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                json_payload=self._payload))
        assert_request_made(mock_session, "POST", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error creating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_custom_bot_category(
                models.CreateCustomBotCategoryRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_server_error(exc_info, "Error creating data")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_custom_bot_category(
                models.CreateCustomBotCategoryRequest(
                    version=TEST_VERSION, json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_custom_bot_category(
                models.CreateCustomBotCategoryRequest(
                    config_id=TEST_CONFIG_ID, json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_json_payload(self, botman_client):
        """Validation error — missing JsonPayload."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_custom_bot_category(
                models.CreateCustomBotCategoryRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "JsonPayload")


class TestUpdateCustomBotCategory:
    """Tests for update (6 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/custom-bot-categories/{UUID3}")
    _payload = {"categoryId": UUID3, "testKey": "testValue3"}

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.update_custom_bot_category(
            models.UpdateCustomBotCategoryRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                category_id=UUID3, json_payload=self._payload))
        assert_request_made(mock_session, "PUT", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_bot_category(
                models.UpdateCustomBotCategoryRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    category_id=UUID3, json_payload=self._payload))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_bot_category(
                models.UpdateCustomBotCategoryRequest(
                    version=TEST_VERSION, category_id=UUID3,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_bot_category(
                models.UpdateCustomBotCategoryRequest(
                    config_id=TEST_CONFIG_ID, category_id=UUID3,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_category_id(self, botman_client):
        """Validation error — missing CategoryID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_bot_category(
                models.UpdateCustomBotCategoryRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "CategoryID")

    def test_missing_json_payload(self, botman_client):
        """Validation error — missing JsonPayload."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_bot_category(
                models.UpdateCustomBotCategoryRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    category_id=UUID3))
        _assert_validation_error(exc_info, "JsonPayload")


class TestRemoveCustomBotCategory:
    """Tests for remove (5 scenarios, expects 204)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/custom-bot-categories/{UUID3}")

    def test_204_no_content(self, mock_session, botman_client):
        """204 No Content."""
        setup_mock_response(mock_session, 204, "{}")
        botman_client.remove_custom_bot_category(
            models.RemoveCustomBotCategoryRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION, category_id=UUID3))
        assert_request_made(mock_session, "DELETE", self._path)

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error deleting match target"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_custom_bot_category(
                models.RemoveCustomBotCategoryRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    category_id=UUID3))
        _assert_server_error(exc_info, "Error deleting match target")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_custom_bot_category(
                models.RemoveCustomBotCategoryRequest(
                    version=TEST_VERSION, category_id=UUID3))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_custom_bot_category(
                models.RemoveCustomBotCategoryRequest(
                    config_id=TEST_CONFIG_ID, category_id=UUID3))
        _assert_validation_error(exc_info, "Version")

    def test_missing_category_id(self, botman_client):
        """Validation error — missing CategoryID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_custom_bot_category(
                models.RemoveCustomBotCategoryRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "CategoryID")


# ===================================================================== #
#  3.20  CustomBotCategoryAction
# ===================================================================== #

class TestGetCustomBotCategoryActionList:
    """Tests for get list (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             "/custom-bot-category-actions")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200,
                            _five_items("actions", "categoryId"))
        r = botman_client.get_custom_bot_category_action_list(
            models.GetCustomBotCategoryActionListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID))
        assert_request_made(mock_session, "GET", self._path)
        assert len(r.actions) == 5

    def test_200_ok_one_record(self, mock_session, botman_client):
        """200 OK One Record — filter by CategoryID."""
        setup_mock_response(mock_session, 200,
                            _five_items("actions", "categoryId"))
        r = botman_client.get_custom_bot_category_action_list(
            models.GetCustomBotCategoryActionListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID, category_id=UUID3))
        assert len(r.actions) == 1

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_bot_category_action_list(
                models.GetCustomBotCategoryActionListRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_bot_category_action_list(
                models.GetCustomBotCategoryActionListRequest(
                    version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_bot_category_action_list(
                models.GetCustomBotCategoryActionListRequest(
                    config_id=TEST_CONFIG_ID,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "Version")


class TestGetCustomBotCategoryAction:
    """Tests for get single (6 scenarios incl SecurityPolicyID + CategoryID)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             f"/custom-bot-category-actions/{UUID3}")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.get_custom_bot_category_action(
            models.GetCustomBotCategoryActionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID, category_id=UUID3))
        assert_request_made(mock_session, "GET", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_bot_category_action(
                models.GetCustomBotCategoryActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID, category_id=UUID3))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_bot_category_action(
                models.GetCustomBotCategoryActionRequest(
                    version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID, category_id=UUID3))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_bot_category_action(
                models.GetCustomBotCategoryActionRequest(
                    config_id=TEST_CONFIG_ID,
                    security_policy_id=TEST_SECURITY_POLICY_ID, category_id=UUID3))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error — missing SecurityPolicyID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_bot_category_action(
                models.GetCustomBotCategoryActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    category_id=UUID3))
        _assert_validation_error(exc_info, "SecurityPolicyID")

    def test_missing_category_id(self, botman_client):
        """Validation error — missing CategoryID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_bot_category_action(
                models.GetCustomBotCategoryActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "CategoryID")


class TestUpdateCustomBotCategoryAction:
    """Tests for update (7 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/security-policies/{TEST_SECURITY_POLICY_ID}"
             f"/custom-bot-category-actions/{UUID3}")
    _payload = {"categoryId": UUID3, "testKey": "testValue3"}

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.update_custom_bot_category_action(
            models.UpdateCustomBotCategoryActionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID,
                category_id=UUID3, json_payload=self._payload))
        assert_request_made(mock_session, "PUT", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_bot_category_action(
                models.UpdateCustomBotCategoryActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    category_id=UUID3, json_payload=self._payload))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_bot_category_action(
                models.UpdateCustomBotCategoryActionRequest(
                    version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    category_id=UUID3, json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_bot_category_action(
                models.UpdateCustomBotCategoryActionRequest(
                    config_id=TEST_CONFIG_ID,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    category_id=UUID3, json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error — missing SecurityPolicyID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_bot_category_action(
                models.UpdateCustomBotCategoryActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    category_id=UUID3, json_payload=self._payload))
        _assert_validation_error(exc_info, "SecurityPolicyID")

    def test_missing_category_id(self, botman_client):
        """Validation error — missing CategoryID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_bot_category_action(
                models.UpdateCustomBotCategoryActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "CategoryID")

    def test_missing_json_payload(self, botman_client):
        """Validation error — missing JsonPayload."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_bot_category_action(
                models.UpdateCustomBotCategoryActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    category_id=UUID3))
        _assert_validation_error(exc_info, "JsonPayload")


# ===================================================================== #
#  3.21  CustomBotCategoryItemSequence
# ===================================================================== #

_CBCIS_PATH_BASE = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
                    "/custom-bot-categories")
_CBCIS_UUID = "f4f0cb20-b5a4-4a06-a26d-f40de2021132"
_CBCIS_SEQ = [UUID1, UUID2, UUID3]
_CBCIS_BODY = json.dumps({"sequence": _CBCIS_SEQ})


class TestGetCustomBotCategoryItemSequence:
    """Tests for get item sequence (5 scenarios) — typed response."""

    _path = f"{_CBCIS_PATH_BASE}/{_CBCIS_UUID}/custom-bot-category-item-sequence"

    def test_200_ok(self, mock_session, botman_client):
        """200 OK — typed response."""
        setup_mock_response(mock_session, 200, _CBCIS_BODY)
        r = botman_client.get_custom_bot_category_item_sequence(
            models.GetCustomBotCategoryItemSequenceRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                category_id=_CBCIS_UUID))
        assert_request_made(mock_session, "GET", self._path)
        assert r.sequence == _CBCIS_SEQ

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_bot_category_item_sequence(
                models.GetCustomBotCategoryItemSequenceRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    category_id=_CBCIS_UUID))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_bot_category_item_sequence(
                models.GetCustomBotCategoryItemSequenceRequest(
                    version=TEST_VERSION, category_id=_CBCIS_UUID))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_bot_category_item_sequence(
                models.GetCustomBotCategoryItemSequenceRequest(
                    config_id=TEST_CONFIG_ID, category_id=_CBCIS_UUID))
        _assert_validation_error(exc_info, "Version")

    def test_missing_category_id(self, botman_client):
        """Validation error — missing CategoryID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_bot_category_item_sequence(
                models.GetCustomBotCategoryItemSequenceRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "CategoryID")


class TestUpdateCustomBotCategoryItemSequence:
    """Tests for update item sequence (6 scenarios) — typed response."""

    _path = f"{_CBCIS_PATH_BASE}/{_CBCIS_UUID}/custom-bot-category-item-sequence"

    def test_200_ok(self, mock_session, botman_client):
        """200 OK — typed response."""
        setup_mock_response(mock_session, 200, _CBCIS_BODY)
        seq_obj = models.UUIDSequence(sequence=_CBCIS_SEQ)
        r = botman_client.update_custom_bot_category_item_sequence(
            models.UpdateCustomBotCategoryItemSequenceRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                category_id=_CBCIS_UUID, sequence=seq_obj))
        assert_request_made(mock_session, "PUT", self._path)
        assert r.sequence == _CBCIS_SEQ

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        seq_obj = models.UUIDSequence(sequence=_CBCIS_SEQ)
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_bot_category_item_sequence(
                models.UpdateCustomBotCategoryItemSequenceRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    category_id=_CBCIS_UUID, sequence=seq_obj))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        seq_obj = models.UUIDSequence(sequence=_CBCIS_SEQ)
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_bot_category_item_sequence(
                models.UpdateCustomBotCategoryItemSequenceRequest(
                    version=TEST_VERSION, category_id=_CBCIS_UUID,
                    sequence=seq_obj))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        seq_obj = models.UUIDSequence(sequence=_CBCIS_SEQ)
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_bot_category_item_sequence(
                models.UpdateCustomBotCategoryItemSequenceRequest(
                    config_id=TEST_CONFIG_ID, category_id=_CBCIS_UUID,
                    sequence=seq_obj))
        _assert_validation_error(exc_info, "Version")

    def test_missing_category_id(self, botman_client):
        """Validation error — missing CategoryID."""
        seq_obj = models.UUIDSequence(sequence=_CBCIS_SEQ)
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_bot_category_item_sequence(
                models.UpdateCustomBotCategoryItemSequenceRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    sequence=seq_obj))
        _assert_validation_error(exc_info, "CategoryID")

    def test_missing_sequence(self, botman_client):
        """Validation error — missing Sequence."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_bot_category_item_sequence(
                models.UpdateCustomBotCategoryItemSequenceRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    category_id=_CBCIS_UUID))
        _assert_validation_error(exc_info, "Sequence")


# ===================================================================== #
#  3.22  CustomBotCategorySequence
# ===================================================================== #

_CBCS_SEQ = [UUID3, SEQ_UUID2, SEQ_UUID3]
_CBCS_BODY = json.dumps({"sequence": _CBCS_SEQ})


class TestGetCustomBotCategorySequence:
    """Tests for get sequence (4 scenarios) — typed response."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/custom-bot-category-sequence")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK — typed response."""
        setup_mock_response(mock_session, 200, _CBCS_BODY)
        r = botman_client.get_custom_bot_category_sequence(
            models.GetCustomBotCategorySequenceRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        assert_request_made(mock_session, "GET", self._path)
        assert r.sequence == _CBCS_SEQ

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_bot_category_sequence(
                models.GetCustomBotCategorySequenceRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_bot_category_sequence(
                models.GetCustomBotCategorySequenceRequest(version=TEST_VERSION))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_bot_category_sequence(
                models.GetCustomBotCategorySequenceRequest(config_id=TEST_CONFIG_ID))
        _assert_validation_error(exc_info, "Version")


class TestUpdateCustomBotCategorySequence:
    """Tests for update sequence (5 scenarios) — typed response."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/custom-bot-category-sequence")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK — typed response."""
        setup_mock_response(mock_session, 200, _CBCS_BODY)
        r = botman_client.update_custom_bot_category_sequence(
            models.UpdateCustomBotCategorySequenceRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                sequence=_CBCS_SEQ))
        assert_request_made(mock_session, "PUT", self._path)
        assert r.sequence == _CBCS_SEQ

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_bot_category_sequence(
                models.UpdateCustomBotCategorySequenceRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    sequence=_CBCS_SEQ))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_bot_category_sequence(
                models.UpdateCustomBotCategorySequenceRequest(
                    version=TEST_VERSION, sequence=_CBCS_SEQ))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_bot_category_sequence(
                models.UpdateCustomBotCategorySequenceRequest(
                    config_id=TEST_CONFIG_ID, sequence=_CBCS_SEQ))
        _assert_validation_error(exc_info, "Version")

    def test_missing_sequence(self, botman_client):
        """Validation error — missing Sequence."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_bot_category_sequence(
                models.UpdateCustomBotCategorySequenceRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "Sequence")


# ===================================================================== #
#  3.23  CustomClient  (custom_client_test.go) — full CRUD
# ===================================================================== #

class TestGetCustomClientList:
    """Tests for get list (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/custom-clients")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200,
                            _five_items("customClients", "customClientId"))
        r = botman_client.get_custom_client_list(
            models.GetCustomClientListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        assert_request_made(mock_session, "GET", self._path)
        assert len(r.custom_clients) == 5

    def test_200_ok_one_record(self, mock_session, botman_client):
        """200 OK One Record — filter by CustomClientID."""
        setup_mock_response(mock_session, 200,
                            _five_items("customClients", "customClientId"))
        r = botman_client.get_custom_client_list(
            models.GetCustomClientListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                custom_client_id=UUID3))
        assert len(r.custom_clients) == 1

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_client_list(
                models.GetCustomClientListRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_client_list(
                models.GetCustomClientListRequest(version=TEST_VERSION))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_client_list(
                models.GetCustomClientListRequest(config_id=TEST_CONFIG_ID))
        _assert_validation_error(exc_info, "Version")


class TestGetCustomClient:
    """Tests for get single (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/custom-clients/{UUID3}")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.get_custom_client(
            models.GetCustomClientRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                custom_client_id=UUID3))
        assert_request_made(mock_session, "GET", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_client(
                models.GetCustomClientRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    custom_client_id=UUID3))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error — missing ConfigID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_client(
                models.GetCustomClientRequest(
                    version=TEST_VERSION, custom_client_id=UUID3))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error — missing Version."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_client(
                models.GetCustomClientRequest(
                    config_id=TEST_CONFIG_ID, custom_client_id=UUID3))
        _assert_validation_error(exc_info, "Version")

    def test_missing_custom_client_id(self, botman_client):
        """Validation error — missing CustomClientID."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_client(
                models.GetCustomClientRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "CustomClientID")


class TestCreateCustomClient:
    """Tests for create (5 scenarios, expects 201)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/custom-clients")
    _payload = {"testKey": "testValue3"}

    def test_201_created(self, mock_session, botman_client):
        """201 Created."""
        setup_mock_response(mock_session, 201, _single())
        r = botman_client.create_custom_client(
            models.CreateCustomClientRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                json_payload=self._payload))
        assert_request_made(mock_session, "POST", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error creating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_custom_client(
                models.CreateCustomClientRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_server_error(exc_info, "Error creating data")

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_custom_client(
                models.CreateCustomClientRequest(
                    version=TEST_VERSION, json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_custom_client(
                models.CreateCustomClientRequest(
                    config_id=TEST_CONFIG_ID, json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_json_payload(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_custom_client(
                models.CreateCustomClientRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "JsonPayload")


class TestUpdateCustomClient:
    """Tests for update (6 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/custom-clients/{UUID3}")
    _payload = {"customClientId": UUID3, "testKey": "testValue3"}

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.update_custom_client(
            models.UpdateCustomClientRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                custom_client_id=UUID3, json_payload=self._payload))
        assert_request_made(mock_session, "PUT", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_client(
                models.UpdateCustomClientRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    custom_client_id=UUID3, json_payload=self._payload))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_client(
                models.UpdateCustomClientRequest(
                    version=TEST_VERSION, custom_client_id=UUID3,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_client(
                models.UpdateCustomClientRequest(
                    config_id=TEST_CONFIG_ID, custom_client_id=UUID3,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_custom_client_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_client(
                models.UpdateCustomClientRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "CustomClientID")

    def test_missing_json_payload(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_client(
                models.UpdateCustomClientRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    custom_client_id=UUID3))
        _assert_validation_error(exc_info, "JsonPayload")


class TestRemoveCustomClient:
    """Tests for remove (5 scenarios, expects 204)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/custom-clients/{UUID3}")

    def test_204_no_content(self, mock_session, botman_client):
        """204 No Content."""
        setup_mock_response(mock_session, 204, "{}")
        botman_client.remove_custom_client(
            models.RemoveCustomClientRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                custom_client_id=UUID3))
        assert_request_made(mock_session, "DELETE", self._path)

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error deleting match target"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_custom_client(
                models.RemoveCustomClientRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    custom_client_id=UUID3))
        _assert_server_error(exc_info, "Error deleting match target")

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_custom_client(
                models.RemoveCustomClientRequest(
                    version=TEST_VERSION, custom_client_id=UUID3))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_custom_client(
                models.RemoveCustomClientRequest(
                    config_id=TEST_CONFIG_ID, custom_client_id=UUID3))
        _assert_validation_error(exc_info, "Version")

    def test_missing_custom_client_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_custom_client(
                models.RemoveCustomClientRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "CustomClientID")


# ===================================================================== #
#  3.24  CustomClientSequence
# ===================================================================== #

_CCS_SEQ = [UUID3, SEQ_UUID2, SEQ_UUID3]
_CCS_BODY = json.dumps({"sequence": _CCS_SEQ})


class TestGetCustomClientSequence:
    """Tests for get sequence (4 scenarios) — typed response."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/custom-client-sequence")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK — typed response."""
        setup_mock_response(mock_session, 200, _CCS_BODY)
        r = botman_client.get_custom_client_sequence(
            models.GetCustomClientSequenceRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        assert_request_made(mock_session, "GET", self._path)
        assert r.sequence == _CCS_SEQ

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_client_sequence(
                models.GetCustomClientSequenceRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_client_sequence(
                models.GetCustomClientSequenceRequest(version=TEST_VERSION))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_client_sequence(
                models.GetCustomClientSequenceRequest(config_id=TEST_CONFIG_ID))
        _assert_validation_error(exc_info, "Version")


class TestUpdateCustomClientSequence:
    """Tests for update sequence (5 scenarios) — typed response."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/custom-client-sequence")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK — typed response."""
        setup_mock_response(mock_session, 200, _CCS_BODY)
        r = botman_client.update_custom_client_sequence(
            models.UpdateCustomClientSequenceRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                sequence=_CCS_SEQ))
        assert_request_made(mock_session, "PUT", self._path)
        assert r.sequence == _CCS_SEQ

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_client_sequence(
                models.UpdateCustomClientSequenceRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    sequence=_CCS_SEQ))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_client_sequence(
                models.UpdateCustomClientSequenceRequest(
                    version=TEST_VERSION, sequence=_CCS_SEQ))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_client_sequence(
                models.UpdateCustomClientSequenceRequest(
                    config_id=TEST_CONFIG_ID, sequence=_CCS_SEQ))
        _assert_validation_error(exc_info, "Version")

    def test_missing_sequence(self, botman_client):
        """Validation error — missing Sequence."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_client_sequence(
                models.UpdateCustomClientSequenceRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "Sequence")


# ===================================================================== #
#  3.25  CustomCode  (custom_code_test.go)
# ===================================================================== #

class TestGetCustomCode:
    """Tests for get_custom_code (4 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/advanced-settings/transactional-endpoint-protection/custom-code")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.get_custom_code(
            models.GetCustomCodeRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        assert_request_made(mock_session, "GET", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_code(
                models.GetCustomCodeRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_code(
                models.GetCustomCodeRequest(version=TEST_VERSION))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_code(
                models.GetCustomCodeRequest(config_id=TEST_CONFIG_ID))
        _assert_validation_error(exc_info, "Version")


class TestUpdateCustomCode:
    """Tests for update_custom_code (5 scenarios, accepts 200/201/204)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/advanced-settings/transactional-endpoint-protection/custom-code")
    _payload = {"testKey": "testValue3"}

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.update_custom_code(
            models.UpdateCustomCodeRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                json_payload=self._payload))
        assert_request_made(mock_session, "PUT", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_code(
                models.UpdateCustomCodeRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_code(
                models.UpdateCustomCodeRequest(
                    version=TEST_VERSION, json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_code(
                models.UpdateCustomCodeRequest(
                    config_id=TEST_CONFIG_ID, json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_json_payload(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_code(
                models.UpdateCustomCodeRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "JsonPayload")


# ===================================================================== #
#  3.26  CustomDefinedBot  (custom_defined_bot_test.go) — full CRUD
# ===================================================================== #

class TestGetCustomDefinedBotList:
    """Tests for get list (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/custom-defined-bots")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200,
                            _five_items("bots", "botId"))
        r = botman_client.get_custom_defined_bot_list(
            models.GetCustomDefinedBotListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        assert_request_made(mock_session, "GET", self._path)
        assert len(r.bots) == 5

    def test_200_ok_one_record(self, mock_session, botman_client):
        """200 OK One Record — filter by BotID."""
        setup_mock_response(mock_session, 200,
                            _five_items("bots", "botId"))
        r = botman_client.get_custom_defined_bot_list(
            models.GetCustomDefinedBotListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                bot_id=UUID3))
        assert len(r.bots) == 1

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_defined_bot_list(
                models.GetCustomDefinedBotListRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_defined_bot_list(
                models.GetCustomDefinedBotListRequest(version=TEST_VERSION))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_defined_bot_list(
                models.GetCustomDefinedBotListRequest(config_id=TEST_CONFIG_ID))
        _assert_validation_error(exc_info, "Version")


class TestGetCustomDefinedBot:
    """Tests for get single (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/custom-defined-bots/{UUID3}")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.get_custom_defined_bot(
            models.GetCustomDefinedBotRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                bot_id=UUID3))
        assert_request_made(mock_session, "GET", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_defined_bot(
                models.GetCustomDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    bot_id=UUID3))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_defined_bot(
                models.GetCustomDefinedBotRequest(
                    version=TEST_VERSION, bot_id=UUID3))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_defined_bot(
                models.GetCustomDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, bot_id=UUID3))
        _assert_validation_error(exc_info, "Version")

    def test_missing_bot_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_defined_bot(
                models.GetCustomDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "BotID")


class TestCreateCustomDefinedBot:
    """Tests for create (5 scenarios, expects 201)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/custom-defined-bots")
    _payload = {"testKey": "testValue3"}

    def test_201_created(self, mock_session, botman_client):
        """201 Created."""
        setup_mock_response(mock_session, 201, _single())
        r = botman_client.create_custom_defined_bot(
            models.CreateCustomDefinedBotRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                json_payload=self._payload))
        assert_request_made(mock_session, "POST", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error creating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_custom_defined_bot(
                models.CreateCustomDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_server_error(exc_info, "Error creating data")

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_custom_defined_bot(
                models.CreateCustomDefinedBotRequest(
                    version=TEST_VERSION, json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_custom_defined_bot(
                models.CreateCustomDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_json_payload(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_custom_defined_bot(
                models.CreateCustomDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "JsonPayload")


class TestUpdateCustomDefinedBot:
    """Tests for update (6 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/custom-defined-bots/{UUID3}")
    _payload = {"botId": UUID3, "testKey": "testValue3"}

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.update_custom_defined_bot(
            models.UpdateCustomDefinedBotRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                bot_id=UUID3, json_payload=self._payload))
        assert_request_made(mock_session, "PUT", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_defined_bot(
                models.UpdateCustomDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    bot_id=UUID3, json_payload=self._payload))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_defined_bot(
                models.UpdateCustomDefinedBotRequest(
                    version=TEST_VERSION, bot_id=UUID3,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_defined_bot(
                models.UpdateCustomDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, bot_id=UUID3,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_bot_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_defined_bot(
                models.UpdateCustomDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "BotID")

    def test_missing_json_payload(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_defined_bot(
                models.UpdateCustomDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    bot_id=UUID3))
        _assert_validation_error(exc_info, "JsonPayload")


class TestRemoveCustomDefinedBot:
    """Tests for remove (5 scenarios, expects 204)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/custom-defined-bots/{UUID3}")

    def test_204_no_content(self, mock_session, botman_client):
        """204 No Content."""
        setup_mock_response(mock_session, 204, "{}")
        botman_client.remove_custom_defined_bot(
            models.RemoveCustomDefinedBotRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                bot_id=UUID3))
        assert_request_made(mock_session, "DELETE", self._path)

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error deleting match target"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_custom_defined_bot(
                models.RemoveCustomDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    bot_id=UUID3))
        _assert_server_error(exc_info, "Error deleting match target")

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_custom_defined_bot(
                models.RemoveCustomDefinedBotRequest(
                    version=TEST_VERSION, bot_id=UUID3))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_custom_defined_bot(
                models.RemoveCustomDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, bot_id=UUID3))
        _assert_validation_error(exc_info, "Version")

    def test_missing_bot_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_custom_defined_bot(
                models.RemoveCustomDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "BotID")


# ===================================================================== #
#  3.27  CustomDenyAction  (custom_deny_action_test.go) — full CRUD
# ===================================================================== #

class TestGetCustomDenyActionList:
    """Tests for get list (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/custom-deny-actions")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200,
                            _five_items("customDenyActions", "actionId"))
        r = botman_client.get_custom_deny_action_list(
            models.GetCustomDenyActionListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        assert_request_made(mock_session, "GET", self._path)
        assert len(r.custom_deny_actions) == 5

    def test_200_ok_one_record(self, mock_session, botman_client):
        """200 OK One Record — filter by ActionID."""
        setup_mock_response(mock_session, 200,
                            _five_items("customDenyActions", "actionId"))
        r = botman_client.get_custom_deny_action_list(
            models.GetCustomDenyActionListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                action_id=UUID3))
        assert len(r.custom_deny_actions) == 1

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_deny_action_list(
                models.GetCustomDenyActionListRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_deny_action_list(
                models.GetCustomDenyActionListRequest(version=TEST_VERSION))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_deny_action_list(
                models.GetCustomDenyActionListRequest(config_id=TEST_CONFIG_ID))
        _assert_validation_error(exc_info, "Version")


class TestGetCustomDenyAction:
    """Tests for get single (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/custom-deny-actions/{UUID3}")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.get_custom_deny_action(
            models.GetCustomDenyActionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                action_id=UUID3))
        assert_request_made(mock_session, "GET", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_deny_action(
                models.GetCustomDenyActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    action_id=UUID3))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_deny_action(
                models.GetCustomDenyActionRequest(
                    version=TEST_VERSION, action_id=UUID3))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_deny_action(
                models.GetCustomDenyActionRequest(
                    config_id=TEST_CONFIG_ID, action_id=UUID3))
        _assert_validation_error(exc_info, "Version")

    def test_missing_action_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_custom_deny_action(
                models.GetCustomDenyActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "ActionID")


class TestCreateCustomDenyAction:
    """Tests for create (5 scenarios, expects 201)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/custom-deny-actions")
    _payload = {"testKey": "testValue3"}

    def test_201_created(self, mock_session, botman_client):
        """201 Created."""
        setup_mock_response(mock_session, 201, _single())
        r = botman_client.create_custom_deny_action(
            models.CreateCustomDenyActionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                json_payload=self._payload))
        assert_request_made(mock_session, "POST", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error creating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_custom_deny_action(
                models.CreateCustomDenyActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_server_error(exc_info, "Error creating data")

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_custom_deny_action(
                models.CreateCustomDenyActionRequest(
                    version=TEST_VERSION, json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_custom_deny_action(
                models.CreateCustomDenyActionRequest(
                    config_id=TEST_CONFIG_ID, json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_json_payload(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_custom_deny_action(
                models.CreateCustomDenyActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "JsonPayload")


class TestUpdateCustomDenyAction:
    """Tests for update (6 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/custom-deny-actions/{UUID3}")
    _payload = {"actionId": UUID3, "testKey": "testValue3"}

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.update_custom_deny_action(
            models.UpdateCustomDenyActionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                action_id=UUID3, json_payload=self._payload))
        assert_request_made(mock_session, "PUT", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_deny_action(
                models.UpdateCustomDenyActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    action_id=UUID3, json_payload=self._payload))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_deny_action(
                models.UpdateCustomDenyActionRequest(
                    version=TEST_VERSION, action_id=UUID3,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_deny_action(
                models.UpdateCustomDenyActionRequest(
                    config_id=TEST_CONFIG_ID, action_id=UUID3,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_action_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_deny_action(
                models.UpdateCustomDenyActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "ActionID")

    def test_missing_json_payload(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_custom_deny_action(
                models.UpdateCustomDenyActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    action_id=UUID3))
        _assert_validation_error(exc_info, "JsonPayload")


class TestRemoveCustomDenyAction:
    """Tests for remove (5 scenarios, expects 204)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/custom-deny-actions/{UUID3}")

    def test_204_no_content(self, mock_session, botman_client):
        """204 No Content."""
        setup_mock_response(mock_session, 204, "{}")
        botman_client.remove_custom_deny_action(
            models.RemoveCustomDenyActionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                action_id=UUID3))
        assert_request_made(mock_session, "DELETE", self._path)

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error deleting match target"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_custom_deny_action(
                models.RemoveCustomDenyActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    action_id=UUID3))
        _assert_server_error(exc_info, "Error deleting match target")

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_custom_deny_action(
                models.RemoveCustomDenyActionRequest(
                    version=TEST_VERSION, action_id=UUID3))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_custom_deny_action(
                models.RemoveCustomDenyActionRequest(
                    config_id=TEST_CONFIG_ID, action_id=UUID3))
        _assert_validation_error(exc_info, "Version")

    def test_missing_action_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_custom_deny_action(
                models.RemoveCustomDenyActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "ActionID")


# ===================================================================== #
#  3.28  JavascriptInjection  (javascript_injection_test.go)
# ===================================================================== #

_JI_PATH = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
            f"/security-policies/{TEST_SECURITY_POLICY_ID}/javascript-injection")


class TestGetJavascriptInjection:
    """Tests for get_javascript_injection (5 scenarios)."""

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.get_javascript_injection(
            models.GetJavascriptInjectionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID))
        assert_request_made(mock_session, "GET", _JI_PATH)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_javascript_injection(
                models.GetJavascriptInjectionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_javascript_injection(
                models.GetJavascriptInjectionRequest(
                    version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_javascript_injection(
                models.GetJavascriptInjectionRequest(
                    config_id=TEST_CONFIG_ID,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_javascript_injection(
                models.GetJavascriptInjectionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "SecurityPolicyID")


class TestUpdateJavascriptInjection:
    """Tests for update_javascript_injection (6 scenarios)."""

    _payload = {"testKey": "testValue3"}

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.update_javascript_injection(
            models.UpdateJavascriptInjectionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID,
                json_payload=self._payload))
        assert_request_made(mock_session, "PUT", _JI_PATH)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_javascript_injection(
                models.UpdateJavascriptInjectionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_javascript_injection(
                models.UpdateJavascriptInjectionRequest(
                    version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_javascript_injection(
                models.UpdateJavascriptInjectionRequest(
                    config_id=TEST_CONFIG_ID,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_javascript_injection(
                models.UpdateJavascriptInjectionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "SecurityPolicyID")

    def test_missing_json_payload(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_javascript_injection(
                models.UpdateJavascriptInjectionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "JsonPayload")


# ===================================================================== #
#  3.29  RecategorizedAkamaiDefinedBot  — typed CRUD
# ===================================================================== #

_RECAT_PATH = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
               "/recategorized-akamai-defined-bots")
_RECAT_BOT_UUIDS = [
    "39cbadc6-d61d-4109-b25d-fd0e91a3a51a",
    "5eb700c8-5b25-40e5-8bb7-1dd48b08d0f7",
    "0d38d0fe-a086-4e18-9358-7cbe6df520df",
    "87a152a9-22ab-4e14-82fe-730e5e410a40",
    "b61a3017-ceda-4a59-a0a3-bcf06b005bd2",
]
_RECAT_CAT_UUIDS = [
    "39cbadc6-d61d-4109-b25d-fd0e91a3a51a",
    "5eb700c8-5b25-40e5-8bb7-1dd48b08d0f7",
    "0d38d0fe-a086-4e18-9358-7cbe6df520df",
    "87a152a9-22ab-4e14-82fe-730e5e410a40",
    "b61a3017-ceda-4a59-a0a3-bcf06b005bd2",
]
_RECAT_LIST_BODY = json.dumps({"recategorizedBots": [
    {"botId": _RECAT_BOT_UUIDS[i], "customBotCategoryId": _RECAT_CAT_UUIDS[i]}
    for i in range(5)
]})
_RECAT_SINGLE_BOT = _RECAT_BOT_UUIDS[2]
_RECAT_SINGLE_CAT = _RECAT_CAT_UUIDS[2]
_RECAT_SINGLE_BODY = json.dumps(
    {"botId": _RECAT_SINGLE_BOT, "customBotCategoryId": _RECAT_SINGLE_CAT}
)


class TestGetRecategorizedAkamaiDefinedBotList:
    """Tests for list (5 scenarios) — typed response."""

    def test_200_ok(self, mock_session, botman_client):
        """200 OK — 5 records."""
        setup_mock_response(mock_session, 200, _RECAT_LIST_BODY)
        r = botman_client.get_recategorized_akamai_defined_bot_list(
            models.GetRecategorizedAkamaiDefinedBotListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        assert_request_made(mock_session, "GET", _RECAT_PATH)
        assert len(r.bots) == 5

    def test_200_ok_one_record(self, mock_session, botman_client):
        """200 OK One Record — filter by BotID."""
        setup_mock_response(mock_session, 200, _RECAT_LIST_BODY)
        r = botman_client.get_recategorized_akamai_defined_bot_list(
            models.GetRecategorizedAkamaiDefinedBotListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                bot_id=_RECAT_SINGLE_BOT))
        assert len(r.bots) == 1
        assert r.bots[0].bot_id == _RECAT_SINGLE_BOT

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_recategorized_akamai_defined_bot_list(
                models.GetRecategorizedAkamaiDefinedBotListRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_recategorized_akamai_defined_bot_list(
                models.GetRecategorizedAkamaiDefinedBotListRequest(
                    version=TEST_VERSION))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_recategorized_akamai_defined_bot_list(
                models.GetRecategorizedAkamaiDefinedBotListRequest(
                    config_id=TEST_CONFIG_ID))
        _assert_validation_error(exc_info, "Version")


class TestGetRecategorizedAkamaiDefinedBot:
    """Tests for get single (5 scenarios) — typed response."""

    _path = f"{_RECAT_PATH}/{_RECAT_SINGLE_BOT}"

    def test_200_ok(self, mock_session, botman_client):
        """200 OK — typed response."""
        setup_mock_response(mock_session, 200, _RECAT_SINGLE_BODY)
        r = botman_client.get_recategorized_akamai_defined_bot(
            models.GetRecategorizedAkamaiDefinedBotRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                bot_id=_RECAT_SINGLE_BOT))
        assert_request_made(mock_session, "GET", self._path)
        assert r.bot_id == _RECAT_SINGLE_BOT
        assert r.category_id == _RECAT_SINGLE_CAT

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_recategorized_akamai_defined_bot(
                models.GetRecategorizedAkamaiDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    bot_id=_RECAT_SINGLE_BOT))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_recategorized_akamai_defined_bot(
                models.GetRecategorizedAkamaiDefinedBotRequest(
                    version=TEST_VERSION, bot_id=_RECAT_SINGLE_BOT))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_recategorized_akamai_defined_bot(
                models.GetRecategorizedAkamaiDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, bot_id=_RECAT_SINGLE_BOT))
        _assert_validation_error(exc_info, "Version")

    def test_missing_bot_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_recategorized_akamai_defined_bot(
                models.GetRecategorizedAkamaiDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "BotID")


class TestCreateRecategorizedAkamaiDefinedBot:
    """Tests for create (5 scenarios, expects 201) — typed response."""

    def test_201_created(self, mock_session, botman_client):
        """201 Created — typed response."""
        setup_mock_response(mock_session, 201, _RECAT_SINGLE_BODY)
        r = botman_client.create_recategorized_akamai_defined_bot(
            models.CreateRecategorizedAkamaiDefinedBotRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                bot_id=_RECAT_SINGLE_BOT,
                category_id=_RECAT_SINGLE_CAT))
        assert_request_made(mock_session, "POST", _RECAT_PATH)
        assert r.bot_id == _RECAT_SINGLE_BOT
        assert r.category_id == _RECAT_SINGLE_CAT

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error creating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_recategorized_akamai_defined_bot(
                models.CreateRecategorizedAkamaiDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    bot_id=_RECAT_SINGLE_BOT,
                    category_id=_RECAT_SINGLE_CAT))
        _assert_server_error(exc_info, "Error creating data")

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_recategorized_akamai_defined_bot(
                models.CreateRecategorizedAkamaiDefinedBotRequest(
                    version=TEST_VERSION, bot_id=_RECAT_SINGLE_BOT,
                    category_id=_RECAT_SINGLE_CAT))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_recategorized_akamai_defined_bot(
                models.CreateRecategorizedAkamaiDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, bot_id=_RECAT_SINGLE_BOT,
                    category_id=_RECAT_SINGLE_CAT))
        _assert_validation_error(exc_info, "Version")

    def test_missing_bot_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_recategorized_akamai_defined_bot(
                models.CreateRecategorizedAkamaiDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    category_id=_RECAT_SINGLE_CAT))
        _assert_validation_error(exc_info, "BotID")


class TestUpdateRecategorizedAkamaiDefinedBot:
    """Tests for update (6 scenarios) — typed response."""

    _path = f"{_RECAT_PATH}/{_RECAT_SINGLE_BOT}"

    def test_200_ok(self, mock_session, botman_client):
        """200 OK — typed response."""
        setup_mock_response(mock_session, 200, _RECAT_SINGLE_BODY)
        r = botman_client.update_recategorized_akamai_defined_bot(
            models.UpdateRecategorizedAkamaiDefinedBotRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                bot_id=_RECAT_SINGLE_BOT,
                category_id=_RECAT_SINGLE_CAT))
        assert_request_made(mock_session, "PUT", self._path)
        assert r.bot_id == _RECAT_SINGLE_BOT

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error creating zone"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_recategorized_akamai_defined_bot(
                models.UpdateRecategorizedAkamaiDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    bot_id=_RECAT_SINGLE_BOT,
                    category_id=_RECAT_SINGLE_CAT))
        _assert_server_error(exc_info, "Error creating zone")

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_recategorized_akamai_defined_bot(
                models.UpdateRecategorizedAkamaiDefinedBotRequest(
                    version=TEST_VERSION, bot_id=_RECAT_SINGLE_BOT,
                    category_id=_RECAT_SINGLE_CAT))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_recategorized_akamai_defined_bot(
                models.UpdateRecategorizedAkamaiDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, bot_id=_RECAT_SINGLE_BOT,
                    category_id=_RECAT_SINGLE_CAT))
        _assert_validation_error(exc_info, "Version")

    def test_missing_bot_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_recategorized_akamai_defined_bot(
                models.UpdateRecategorizedAkamaiDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    category_id=_RECAT_SINGLE_CAT))
        _assert_validation_error(exc_info, "BotID")

    def test_missing_category_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_recategorized_akamai_defined_bot(
                models.UpdateRecategorizedAkamaiDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    bot_id=_RECAT_SINGLE_BOT))
        _assert_validation_error(exc_info, "CategoryID")


class TestRemoveRecategorizedAkamaiDefinedBot:
    """Tests for remove (5 scenarios, expects 204)."""

    _path = f"{_RECAT_PATH}/{_RECAT_SINGLE_BOT}"

    def test_204_no_content(self, mock_session, botman_client):
        """204 No Content."""
        setup_mock_response(mock_session, 204, "{}")
        botman_client.remove_recategorized_akamai_defined_bot(
            models.RemoveRecategorizedAkamaiDefinedBotRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                bot_id=_RECAT_SINGLE_BOT))
        assert_request_made(mock_session, "DELETE", self._path)

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error deleting match target"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_recategorized_akamai_defined_bot(
                models.RemoveRecategorizedAkamaiDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    bot_id=_RECAT_SINGLE_BOT))
        _assert_server_error(exc_info, "Error deleting match target")

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_recategorized_akamai_defined_bot(
                models.RemoveRecategorizedAkamaiDefinedBotRequest(
                    version=TEST_VERSION, bot_id=_RECAT_SINGLE_BOT))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_recategorized_akamai_defined_bot(
                models.RemoveRecategorizedAkamaiDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, bot_id=_RECAT_SINGLE_BOT))
        _assert_validation_error(exc_info, "Version")

    def test_missing_bot_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_recategorized_akamai_defined_bot(
                models.RemoveRecategorizedAkamaiDefinedBotRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "BotID")


# ===================================================================== #
#  3.30  ResponseAction  (response_action_test.go) — list only
# ===================================================================== #

class TestGetResponseActionList:
    """Tests for list (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/response-actions")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200,
                            _five_items("responseActions", "actionId"))
        r = botman_client.get_response_action_list(
            models.GetResponseActionListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        assert_request_made(mock_session, "GET", self._path)
        assert len(r.response_actions) == 5

    def test_200_ok_one_record(self, mock_session, botman_client):
        """200 OK One Record — filter by ActionID."""
        setup_mock_response(mock_session, 200,
                            _five_items("responseActions", "actionId"))
        r = botman_client.get_response_action_list(
            models.GetResponseActionListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                action_id=UUID3))
        assert len(r.response_actions) == 1

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_response_action_list(
                models.GetResponseActionListRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_response_action_list(
                models.GetResponseActionListRequest(version=TEST_VERSION))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_response_action_list(
                models.GetResponseActionListRequest(config_id=TEST_CONFIG_ID))
        _assert_validation_error(exc_info, "Version")


# ===================================================================== #
#  3.31  ServeAlternateAction  (serve_alternate_action_test.go) — full CRUD
# ===================================================================== #

class TestGetServeAlternateActionList:
    """Tests for get list (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/response-actions/serve-alternate-actions")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200,
                            _five_items("serveAlternateActions", "actionId"))
        r = botman_client.get_serve_alternate_action_list(
            models.GetServeAlternateActionListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        assert_request_made(mock_session, "GET", self._path)
        assert len(r.serve_alternate_actions) == 5

    def test_200_ok_one_record(self, mock_session, botman_client):
        """200 OK One Record — filter by ActionID."""
        setup_mock_response(mock_session, 200,
                            _five_items("serveAlternateActions", "actionId"))
        r = botman_client.get_serve_alternate_action_list(
            models.GetServeAlternateActionListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                action_id=UUID3))
        assert len(r.serve_alternate_actions) == 1

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_serve_alternate_action_list(
                models.GetServeAlternateActionListRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_serve_alternate_action_list(
                models.GetServeAlternateActionListRequest(version=TEST_VERSION))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_serve_alternate_action_list(
                models.GetServeAlternateActionListRequest(
                    config_id=TEST_CONFIG_ID))
        _assert_validation_error(exc_info, "Version")


class TestGetServeAlternateAction:
    """Tests for get single (5 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/response-actions/serve-alternate-actions/{UUID3}")

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.get_serve_alternate_action(
            models.GetServeAlternateActionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                action_id=UUID3))
        assert_request_made(mock_session, "GET", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_serve_alternate_action(
                models.GetServeAlternateActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    action_id=UUID3))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_serve_alternate_action(
                models.GetServeAlternateActionRequest(
                    version=TEST_VERSION, action_id=UUID3))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_serve_alternate_action(
                models.GetServeAlternateActionRequest(
                    config_id=TEST_CONFIG_ID, action_id=UUID3))
        _assert_validation_error(exc_info, "Version")

    def test_missing_action_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_serve_alternate_action(
                models.GetServeAlternateActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "ActionID")


class TestCreateServeAlternateAction:
    """Tests for create (5 scenarios, expects 201)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/response-actions/serve-alternate-actions")
    _payload = {"testKey": "testValue3"}

    def test_201_created(self, mock_session, botman_client):
        """201 Created."""
        setup_mock_response(mock_session, 201, _single())
        r = botman_client.create_serve_alternate_action(
            models.CreateServeAlternateActionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                json_payload=self._payload))
        assert_request_made(mock_session, "POST", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error creating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_serve_alternate_action(
                models.CreateServeAlternateActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_server_error(exc_info, "Error creating data")

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_serve_alternate_action(
                models.CreateServeAlternateActionRequest(
                    version=TEST_VERSION, json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_serve_alternate_action(
                models.CreateServeAlternateActionRequest(
                    config_id=TEST_CONFIG_ID, json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_json_payload(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_serve_alternate_action(
                models.CreateServeAlternateActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "JsonPayload")


class TestUpdateServeAlternateAction:
    """Tests for update (6 scenarios)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/response-actions/serve-alternate-actions/{UUID3}")
    _payload = {"actionId": UUID3, "testKey": "testValue3"}

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.update_serve_alternate_action(
            models.UpdateServeAlternateActionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                action_id=UUID3, json_payload=self._payload))
        assert_request_made(mock_session, "PUT", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_serve_alternate_action(
                models.UpdateServeAlternateActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    action_id=UUID3, json_payload=self._payload))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_serve_alternate_action(
                models.UpdateServeAlternateActionRequest(
                    version=TEST_VERSION, action_id=UUID3,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_serve_alternate_action(
                models.UpdateServeAlternateActionRequest(
                    config_id=TEST_CONFIG_ID, action_id=UUID3,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_action_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_serve_alternate_action(
                models.UpdateServeAlternateActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "ActionID")

    def test_missing_json_payload(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_serve_alternate_action(
                models.UpdateServeAlternateActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    action_id=UUID3))
        _assert_validation_error(exc_info, "JsonPayload")


class TestRemoveServeAlternateAction:
    """Tests for remove (5 scenarios, expects 204)."""

    _path = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             f"/response-actions/serve-alternate-actions/{UUID3}")

    def test_204_no_content(self, mock_session, botman_client):
        """204 No Content."""
        setup_mock_response(mock_session, 204, "{}")
        botman_client.remove_serve_alternate_action(
            models.RemoveServeAlternateActionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                action_id=UUID3))
        assert_request_made(mock_session, "DELETE", self._path)

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error deleting match target"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_serve_alternate_action(
                models.RemoveServeAlternateActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    action_id=UUID3))
        _assert_server_error(exc_info, "Error deleting match target")

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_serve_alternate_action(
                models.RemoveServeAlternateActionRequest(
                    version=TEST_VERSION, action_id=UUID3))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_serve_alternate_action(
                models.RemoveServeAlternateActionRequest(
                    config_id=TEST_CONFIG_ID, action_id=UUID3))
        _assert_validation_error(exc_info, "Version")

    def test_missing_action_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_serve_alternate_action(
                models.RemoveServeAlternateActionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "ActionID")


# ===================================================================== #
#  3.32  TransactionalEndpoint  (transactional_endpoint_test.go) — full CRUD
# ===================================================================== #

_TE_BASE = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
            f"/security-policies/{TEST_SECURITY_POLICY_ID}"
            "/transactional-endpoints")
_TE_OP_ID = UUID3


class TestGetTransactionalEndpointList:
    """Tests for get list (7 scenarios incl SecurityPolicyID)."""

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200,
                            _five_items("operations", "operationId"))
        r = botman_client.get_transactional_endpoint_list(
            models.GetTransactionalEndpointListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID))
        assert_request_made(mock_session, "GET", _TE_BASE)
        assert len(r.operations) == 5

    def test_200_ok_one_record(self, mock_session, botman_client):
        """200 OK One Record — filter by OperationID."""
        setup_mock_response(mock_session, 200,
                            _five_items("operations", "operationId"))
        r = botman_client.get_transactional_endpoint_list(
            models.GetTransactionalEndpointListRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID,
                operation_id=_TE_OP_ID))
        assert len(r.operations) == 1

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_transactional_endpoint_list(
                models.GetTransactionalEndpointListRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_transactional_endpoint_list(
                models.GetTransactionalEndpointListRequest(
                    version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_transactional_endpoint_list(
                models.GetTransactionalEndpointListRequest(
                    config_id=TEST_CONFIG_ID,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_transactional_endpoint_list(
                models.GetTransactionalEndpointListRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "SecurityPolicyID")


class TestGetTransactionalEndpoint:
    """Tests for get single (6 scenarios)."""

    _path = f"{_TE_BASE}/{_TE_OP_ID}"

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.get_transactional_endpoint(
            models.GetTransactionalEndpointRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID,
                operation_id=_TE_OP_ID))
        assert_request_made(mock_session, "GET", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_transactional_endpoint(
                models.GetTransactionalEndpointRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    operation_id=_TE_OP_ID))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_transactional_endpoint(
                models.GetTransactionalEndpointRequest(
                    version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    operation_id=_TE_OP_ID))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_transactional_endpoint(
                models.GetTransactionalEndpointRequest(
                    config_id=TEST_CONFIG_ID,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    operation_id=_TE_OP_ID))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_transactional_endpoint(
                models.GetTransactionalEndpointRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    operation_id=_TE_OP_ID))
        _assert_validation_error(exc_info, "SecurityPolicyID")

    def test_missing_operation_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_transactional_endpoint(
                models.GetTransactionalEndpointRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "OperationID")


class TestCreateTransactionalEndpoint:
    """Tests for create (6 scenarios, expects 201)."""

    _payload = {"testKey": "testValue3"}

    def test_201_created(self, mock_session, botman_client):
        """201 Created."""
        setup_mock_response(mock_session, 201, _single())
        r = botman_client.create_transactional_endpoint(
            models.CreateTransactionalEndpointRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID,
                json_payload=self._payload))
        assert_request_made(mock_session, "POST", _TE_BASE)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error creating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_transactional_endpoint(
                models.CreateTransactionalEndpointRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_server_error(exc_info, "Error creating data")

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_transactional_endpoint(
                models.CreateTransactionalEndpointRequest(
                    version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_transactional_endpoint(
                models.CreateTransactionalEndpointRequest(
                    config_id=TEST_CONFIG_ID,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_transactional_endpoint(
                models.CreateTransactionalEndpointRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "SecurityPolicyID")

    def test_missing_json_payload(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.create_transactional_endpoint(
                models.CreateTransactionalEndpointRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "JsonPayload")


class TestUpdateTransactionalEndpoint:
    """Tests for update (7 scenarios)."""

    _path = f"{_TE_BASE}/{_TE_OP_ID}"
    _payload = {"operationId": _TE_OP_ID, "testKey": "testValue3"}

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.update_transactional_endpoint(
            models.UpdateTransactionalEndpointRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID,
                operation_id=_TE_OP_ID, json_payload=self._payload))
        assert_request_made(mock_session, "PUT", self._path)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error creating zone"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_transactional_endpoint(
                models.UpdateTransactionalEndpointRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    operation_id=_TE_OP_ID, json_payload=self._payload))
        _assert_server_error(exc_info, "Error creating zone")

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_transactional_endpoint(
                models.UpdateTransactionalEndpointRequest(
                    version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    operation_id=_TE_OP_ID, json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_transactional_endpoint(
                models.UpdateTransactionalEndpointRequest(
                    config_id=TEST_CONFIG_ID,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    operation_id=_TE_OP_ID, json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_transactional_endpoint(
                models.UpdateTransactionalEndpointRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    operation_id=_TE_OP_ID, json_payload=self._payload))
        _assert_validation_error(exc_info, "SecurityPolicyID")

    def test_missing_operation_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_transactional_endpoint(
                models.UpdateTransactionalEndpointRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    json_payload=self._payload))
        _assert_validation_error(exc_info, "OperationID")

    def test_missing_json_payload(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_transactional_endpoint(
                models.UpdateTransactionalEndpointRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    operation_id=_TE_OP_ID))
        _assert_validation_error(exc_info, "JsonPayload")


class TestRemoveTransactionalEndpoint:
    """Tests for remove (6 scenarios, expects 204)."""

    _path = f"{_TE_BASE}/{_TE_OP_ID}"

    def test_204_no_content(self, mock_session, botman_client):
        """204 No Content."""
        setup_mock_response(mock_session, 204, "{}")
        botman_client.remove_transactional_endpoint(
            models.RemoveTransactionalEndpointRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                security_policy_id=TEST_SECURITY_POLICY_ID,
                operation_id=_TE_OP_ID))
        assert_request_made(mock_session, "DELETE", self._path)

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error deleting match target"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_transactional_endpoint(
                models.RemoveTransactionalEndpointRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    operation_id=_TE_OP_ID))
        _assert_server_error(exc_info, "Error deleting match target")

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_transactional_endpoint(
                models.RemoveTransactionalEndpointRequest(
                    version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    operation_id=_TE_OP_ID))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_transactional_endpoint(
                models.RemoveTransactionalEndpointRequest(
                    config_id=TEST_CONFIG_ID,
                    security_policy_id=TEST_SECURITY_POLICY_ID,
                    operation_id=_TE_OP_ID))
        _assert_validation_error(exc_info, "Version")

    def test_missing_security_policy_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_transactional_endpoint(
                models.RemoveTransactionalEndpointRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    operation_id=_TE_OP_ID))
        _assert_validation_error(exc_info, "SecurityPolicyID")

    def test_missing_operation_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.remove_transactional_endpoint(
                models.RemoveTransactionalEndpointRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    security_policy_id=TEST_SECURITY_POLICY_ID))
        _assert_validation_error(exc_info, "OperationID")


# ===================================================================== #
#  3.33  TransactionalEndpointProtection
# ===================================================================== #

_TEP_PATH = (f"/appsec/v1/configs/{TEST_CONFIG_ID}/versions/{TEST_VERSION}"
             "/advanced-settings/transactional-endpoint-protection")


class TestGetTransactionalEndpointProtection:
    """Tests for get (4 scenarios)."""

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.get_transactional_endpoint_protection(
            models.GetTransactionalEndpointProtectionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        assert_request_made(mock_session, "GET", _TEP_PATH)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err())
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_transactional_endpoint_protection(
                models.GetTransactionalEndpointProtectionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_server_error(exc_info)

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_transactional_endpoint_protection(
                models.GetTransactionalEndpointProtectionRequest(
                    version=TEST_VERSION))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.get_transactional_endpoint_protection(
                models.GetTransactionalEndpointProtectionRequest(
                    config_id=TEST_CONFIG_ID))
        _assert_validation_error(exc_info, "Version")


class TestUpdateTransactionalEndpointProtection:
    """Tests for update (5 scenarios)."""

    _payload = {"testKey": "testValue3"}

    def test_200_ok(self, mock_session, botman_client):
        """200 OK."""
        setup_mock_response(mock_session, 200, _single())
        r = botman_client.update_transactional_endpoint_protection(
            models.UpdateTransactionalEndpointProtectionRequest(
                config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                json_payload=self._payload))
        assert_request_made(mock_session, "PUT", _TEP_PATH)
        assert r == json.loads(_single())

    def test_500_error(self, mock_session, botman_client):
        """500 internal server error."""
        setup_mock_response(mock_session, 500, _err("Error updating data"))
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_transactional_endpoint_protection(
                models.UpdateTransactionalEndpointProtectionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION,
                    json_payload=self._payload))
        _assert_server_error(exc_info, "Error updating data")

    def test_missing_config_id(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_transactional_endpoint_protection(
                models.UpdateTransactionalEndpointProtectionRequest(
                    version=TEST_VERSION, json_payload=self._payload))
        _assert_validation_error(exc_info, "ConfigID")

    def test_missing_version(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_transactional_endpoint_protection(
                models.UpdateTransactionalEndpointProtectionRequest(
                    config_id=TEST_CONFIG_ID, json_payload=self._payload))
        _assert_validation_error(exc_info, "Version")

    def test_missing_json_payload(self, botman_client):
        """Validation error."""
        with pytest.raises(errors.Error) as exc_info:
            botman_client.update_transactional_endpoint_protection(
                models.UpdateTransactionalEndpointProtectionRequest(
                    config_id=TEST_CONFIG_ID, version=TEST_VERSION))
        _assert_validation_error(exc_info, "JsonPayload")
