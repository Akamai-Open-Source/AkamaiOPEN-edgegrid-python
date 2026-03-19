"""Unit tests for the Imaging API client"""
# pylint: disable=too-many-lines,line-too-long,too-few-public-methods

import json
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.imaging.imaging import Client
from akamai.edgegrid.imaging.errors import (
    Error as ImagingError,
    parse_error_response,
)
from akamai.edgegrid.imaging.models import (
    ListPoliciesRequest,
    ListPoliciesResponse,
    GetPolicyRequest,
    UpsertPolicyRequest,
    DeletePolicyRequest,
    GetPolicyHistoryRequest,
    GetPolicyHistoryResponse,
    RollbackPolicyRequest,
    PolicyResponse,
    PolicyHistoryItem,
    ListPolicySetsRequest,
    GetPolicySetRequest,
    CreatePolicySetRequest,
    UpdatePolicySetRequest,
    DeletePolicySetRequest,
    PolicySet,
    PolicyOutputImage,
    PolicyOutputVideo,
    PolicyInputImage,
    PolicyInputVideo,
    OutputVideo,
    OutputVideoPerceptualQualityVariableInline,
    POLICY_NETWORK_STAGING,
    POLICY_NETWORK_PRODUCTION,
    NETWORK_STAGING,
    NETWORK_PRODUCTION,
)
from akamai.edgegrid.errors import ErrStructValidation


# ---------------------------------------------------------------------------
# Helper / Fixture Utilities
# ---------------------------------------------------------------------------


def _mock_exec_success(session, status_code, response_body):
    """Configure mock session.exec() to return a successful response.

    Mimics Go's httptest.NewTLSServer pattern where the server writes
    a status code and response body.
    """
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.text = response_body

    parsed = {}
    if response_body and response_body.strip():
        try:
            parsed = json.loads(response_body)
        except json.JSONDecodeError:
            pass

    mock_response.json.return_value = parsed
    session.exec.return_value = (mock_response, parsed)
    return mock_response


def _mock_exec_error(session, error):
    """Configure mock session.exec() to raise an API error.

    Mimics Go's error path where the client receives an error HTTP
    response and the error parser raises an ImagingError.
    """
    session.exec.side_effect = error


def _assert_exec_called(session, method, path, headers=None):
    """Assert that session.exec was called with the expected arguments.

    Mirrors Go test assertions on r.URL.String(), r.Method, and r.Header.
    """
    assert session.exec.called, "session.exec was not called"
    args, kwargs = session.exec.call_args
    assert args[0] == method, f"Expected method {method}, got {args[0]}"
    assert args[1] == path, f"Expected path {path}, got {args[1]}"
    if headers is not None:
        actual_headers = kwargs.get("headers", {})
        for key, value in headers.items():
            assert key in actual_headers, f"Missing header {key}"
            assert actual_headers[key] == value, (
                f"Header {key}: expected {value}, got {actual_headers[key]}"
            )


# ===================================================================
# Common error response bodies shared across policy tests
# ===================================================================

_ERR_400_BODY = (
    '{"type": "https://problems.luna.akamaiapis.net/image-policy-manager/IVM_1004",'
    '"title": "Bad Request",'
    '"instance": "52a21f40-9861-4d35-95d0-a603c85cb2ad",'
    '"status": 400,'
    '"detail": "A contract must be specified using the Contract header.",'
    '"problemId": "52a21f40-9861-4d35-95d0-a603c85cb2ad"}'
)

_ERR_401_BODY = (
    '{"type": "https://problems.luna-dev.akamaiapis.net/-/pep-authn/deny",'
    '"title": "Not authorized",'
    '"status": 401,'
    '"detail": "Inactive client token",'
    '"instance": "https://akaa-mgfkwp3rw4k2whym-eyn4wdjeur5lz37c.luna-dev.akamaiapis.net/imaging/v2/network/staging/policysets/",'
    '"method": "GET",'
    '"serverIp": "104.81.220.242",'
    '"clientIp": "22.22.22.22",'
    '"requestId": "124cc33c",'
    '"requestTime": "2022-01-12T16:53:44Z"}'
)

_ERR_403_BODY = (
    '{"type": "https://problems.luna.akamaiapis.net/image-policy-manager/IVM_1002",'
    '"title": "Forbidden",'
    '"instance": "7d633d60-b120-4f28-a0de-ad86aeaf3c68",'
    '"status": 403,'
    '"detail": "User does not have authorization to perform this action.",'
    '"problemId": "7d633d60-b120-4f28-a0de-ad86aeaf3c68"}'
)

_EXPECTED_400 = ImagingError(
    type="https://problems.luna.akamaiapis.net/image-policy-manager/IVM_1004",
    title="Bad Request",
    instance="52a21f40-9861-4d35-95d0-a603c85cb2ad",
    status=400,
    detail="A contract must be specified using the Contract header.",
    problem_id="52a21f40-9861-4d35-95d0-a603c85cb2ad",
)

_EXPECTED_401 = ImagingError(
    type="https://problems.luna-dev.akamaiapis.net/-/pep-authn/deny",
    title="Not authorized",
    status=401,
    detail="Inactive client token",
    instance="https://akaa-mgfkwp3rw4k2whym-eyn4wdjeur5lz37c.luna-dev.akamaiapis.net/imaging/v2/network/staging/policysets/",
    method="GET",
    server_ip="104.81.220.242",
    client_ip="22.22.22.22",
    request_id="124cc33c",
    request_time="2022-01-12T16:53:44Z",
)

_EXPECTED_403 = ImagingError(
    type="https://problems.luna.akamaiapis.net/image-policy-manager/IVM_1002",
    title="Forbidden",
    instance="7d633d60-b120-4f28-a0de-ad86aeaf3c68",
    status=403,
    detail="User does not have authorization to perform this action.",
    problem_id="7d633d60-b120-4f28-a0de-ad86aeaf3c68",
)


# Standard policy params
_STD_POLICY_PARAMS_KWARGS = {
    "network": POLICY_NETWORK_STAGING,
    "contract_id": "3-WNKXX1",
    "policy_set_id": "570f9090-5dbe-11ec-8a0a-71665789c1d8",
    "policy_id": "foo",
}
_STD_POLICY_HEADERS = {
    "Contract": "3-WNKXX1",
    "Policy-Set": "570f9090-5dbe-11ec-8a0a-71665789c1d8",
}


# ===================================================================
# Error Tests (from errors_test.go)
# ===================================================================


class TestNewError:
    """Tests for error response parsing. Mirrors Go TestNewError (3 cases)."""

    @pytest.mark.parametrize("name,response_status,response_body,expected_error", [
        (
            "valid response, status code 400, Bad Request",
            400,
            '{"type":"testType","title":"Bad Request","detail":"error","status":400,"extensionFields":{"requestId":"123"},"problemId":"abc123","requestId":"123"}',
            ImagingError(
                type="testType",
                title="Bad Request",
                detail="error",
                status=400,
                extension_fields={"requestId": "123"},
                problem_id="abc123",
                request_id="123",
            ),
        ),
        (
            "valid response, status code 400, Illegal parameter value",
            400,
            '{"type":"testType","title":"Illegal parameter value","detail":"error","status":400,"extensionFields":{"illegalValue":"abc","parameterName":"param1"},"problemId":"abc123","illegalValue":"abc","parameterName":"param1"}',
            ImagingError(
                type="testType",
                title="Illegal parameter value",
                detail="error",
                status=400,
                extension_fields={"illegalValue": "abc", "parameterName": "param1"},
                problem_id="abc123",
                illegal_value="abc",
                parameter_name="param1",
            ),
        ),
        (
            "invalid response body, assign status code",
            500,
            "test",
            ImagingError(
                title="Failed to unmarshal error body. Image & Video Manager API failed. Check details for more information.",
                detail="test",
                status=500,
            ),
        ),
    ])
    def test_new_error(self, name, response_status, response_body, expected_error):
        """Test error parsing from HTTP response."""
        mock_response = MagicMock()
        mock_response.status_code = response_status
        mock_response.text = response_body

        result = parse_error_response(mock_response)
        assert result == expected_error, f"Case '{name}': {result} != {expected_error}"


class TestAs:
    """Tests for error comparison. Mirrors Go TestAs (4 cases)."""

    @pytest.mark.parametrize("name,err,target,expected", [
        (
            "different error code",
            ImagingError(status=404),
            ImagingError(status=401),
            False,
        ),
        (
            "same error code",
            ImagingError(status=404),
            ImagingError(status=404),
            True,
        ),
        (
            "same error code and error message",
            ImagingError(status=404, title="some error"),
            ImagingError(status=404, title="some error"),
            True,
        ),
        (
            "same error code and different error message",
            ImagingError(status=404, title="some error"),
            ImagingError(status=404, title="other error"),
            False,
        ),
    ])
    def test_is_equivalent(self, name, err, target, expected):
        """Test Error.is_equivalent() mirrors Go Error.Is()."""
        assert err.is_equivalent(target) == expected, f"Case '{name}' failed"


class TestJsonErrorUnmarshalling:
    """Tests for JSON error unmarshalling edge cases.

    Mirrors Go TestJsonErrorUnmarshalling (3 cases).
    """

    @pytest.mark.parametrize("name,response_body,expected_error", [
        (
            "API failure with HTML response",
            "<HTML><HEAD>...</HEAD><BODY>...</BODY></HTML>",
            ImagingError(
                type="",
                title="Failed to unmarshal error body. Image & Video Manager API failed. Check details for more information.",
                detail="<HTML><HEAD>...</HEAD><BODY>...</BODY></HTML>",
            ),
        ),
        (
            "API failure with plain text response",
            "Your request did not succeed as this operation has reached  the limit for your account. Please try after 2024-01-16T15:20:55.945Z",
            ImagingError(
                type="",
                title="Failed to unmarshal error body. Image & Video Manager API failed. Check details for more information.",
                detail="Your request did not succeed as this operation has reached  the limit for your account. Please try after 2024-01-16T15:20:55.945Z",
            ),
        ),
        (
            "API failure with XML response",
            '<Root><Item id="1" name="Example" /></Root>',
            ImagingError(
                type="",
                title="Failed to unmarshal error body. Image & Video Manager API failed. Check details for more information.",
                detail='<Root><Item id="1" name="Example" /></Root>',
            ),
        ),
    ])
    def test_json_error_unmarshalling(self, name, response_body, expected_error):
        """Test error parsing with non-JSON responses."""
        mock_response = MagicMock()
        mock_response.status_code = 0
        mock_response.text = response_body

        result = parse_error_response(mock_response)
        assert result == expected_error, f"Case '{name}': {result} != {expected_error}"


# ===================================================================
# Client Construction Tests (from imaging_test.go)
# ===================================================================


class TestClient:
    """Tests for client construction. Mirrors Go TestClient (2 cases)."""

    def test_no_options_provided(self):
        """No options provided, return default. Mirrors Go case."""
        session = MagicMock()
        client = Client(session)
        assert client._session is session  # pylint: disable=protected-access

    def test_session_stored(self):
        """Session is stored correctly. Mirrors Go 'option provided' case."""
        session = MagicMock()
        client = Client(session)
        assert client._session == session  # pylint: disable=protected-access


# ===================================================================
# Policy Tests (from policy_test.go)
# ===================================================================

# --- Response body constants ---
_LIST_POLICIES_200_OK_BODY = """
{
    "itemKind": "POLICY",
    "items": [
        {
            "id": ".auto",
            "version": 1,
            "previousVersion": 0,
            "rolloutInfo": {
                "startTime": 1626379176,
                "endTime": 1626379177,
                "rolloutDuration": 1
            },
            "video": false,
            "user": "system",
            "dateCreated": "2021-07-15 19:59:35+0000"
        },
        {
            "id": "asd",
            "version": 2,
            "previousVersion": 1,
            "rolloutInfo": {
                "startTime": 1638894035,
                "endTime": 1638894036,
                "rolloutDuration": 1
            },
            "breakpoints": {
                "widths": [
                    320,
                    640,
                    1024,
                    2048,
                    5000
                ]
            },
            "output": {
                "perceptualQuality": "mediumHigh"
            },
            "transformations": [
                {
                    "transformation": "Composite",
                    "xPosition": 0,
                    "yPosition": 0,
                    "gravity": "NorthWest",
                    "placement": "Over",
                    "image": {
                        "type": "Text",
                        "fill": "#000000",
                        "size": 72,
                        "stroke": "#FFFFFF",
                        "strokeSize": 0,
                        "text": "Hello There",
                        "transformation": {
                            "transformation": "Compound",
                            "transformations": []
                        }
                    }
                }
            ],
            "video": false,
            "user": "jsmith",
            "dateCreated": "2021-12-07 16:20:34+0000"
        },
        {
            "id": "cheese",
            "version": 1,
            "previousVersion": 0,
            "rolloutInfo": {
                "startTime": 1628279193,
                "endTime": 1628279194,
                "rolloutDuration": 1
            },
            "breakpoints": {
                "widths": [
                    720,
                    1080,
                    1366,
                    1920,
                    5000
                ]
            },
            "output": {
                "perceptualQuality": "mediumHigh"
            },
            "video": false,
            "user": "jsmith",
            "dateCreated": "2021-08-06 19:46:32+0000"
        },
        {
            "id": "example",
            "version": 9,
            "previousVersion": 8,
            "rolloutInfo": {
                "startTime": 1639680399,
                "endTime": 1639680400,
                "rolloutDuration": 1
            },
            "breakpoints": {
                "widths": [
                    320,
                    640,
                    1024,
                    2048,
                    5000
                ]
            },
            "output": {
                "perceptualQuality": "mediumHigh"
            },
            "transformations": [
                {
                    "transformation": "Blur",
                    "sigma": {
                        "var": "blurVar"
                    }
                },
                {
                    "transformation": "MaxColors",
                    "colors": 2
                }
            ],
            "variables": [
                {
                    "name": "blurVar",
                    "type": "number",
                    "defaultValue": "5"
                }
            ],
            "video": false,
            "user": "foofoo5",
            "dateCreated": "2021-12-16 18:46:38+0000"
        },
        {
            "id": "mgw",
            "version": 1,
            "previousVersion": 0,
            "rolloutInfo": {
                "startTime": 1639680457,
                "endTime": 1639680458,
                "rolloutDuration": 1
            },
            "breakpoints": {
                "widths": [
                    320,
                    640,
                    1024,
                    2048,
                    5000
                ]
            },
            "output": {
                "perceptualQuality": "mediumHigh"
            },
            "transformations": [
                {
                    "transformation": "Blur",
                    "sigma": {
                        "var": "blurVar"
                    }
                },
                {
                    "transformation": "MaxColors",
                    "colors": 2
                }
            ],
            "variables": [
                {
                    "name": "blurVar",
                    "type": "number",
                    "defaultValue": "5"
                }
            ],
            "video": false,
            "user": "foofoo5",
            "dateCreated": "2021-12-16 18:47:36+0000"
        },
        {
            "id": "testPolicy2",
            "version": 1,
            "previousVersion": 0,
            "rolloutInfo": {
                "startTime": 1643052400,
                "endTime": 1643052401,
                "rolloutDuration": 1
            },
            "video": false,
            "user": "jsmith",
            "dateCreated": "2022-01-24 19:26:39+0000"
        },
        {
            "id": "testpolicy",
            "version": 1,
            "previousVersion": 0,
            "rolloutInfo": {
                "startTime": 1643052164,
                "endTime": 1643052165,
                "rolloutDuration": 1
            },
            "video": false,
            "user": "jsmith",
            "dateCreated": "2022-01-24 19:22:43+0000"
        },
        {
            "id": "updatePolicy",
            "version": 2,
            "previousVersion": 1,
            "rolloutInfo": {
                "startTime": 1643055431,
                "endTime": 1643055432,
                "rolloutDuration": 1
            },
            "output": {
                "perceptualQuality": "mediumHigh"
            },
            "video": true,
            "user": "jsmith",
            "dateCreated": "2022-01-24 20:17:10+0000"
        }
    ],
    "totalItems": 8
}"""

_LIST_POLICIES_200_DEEP_BODY = """
{
    "itemKind": "POLICY",
    "items": [
{
	"variables": [
		{
			"name": "ResizeDim",
			"type": "number",
			"defaultValue": "280"
		},
		{
			"name": "ResizeDimWithBorder",
			"type": "number",
			"defaultValue": "260"
		},
		{
			"name": "MinDim",
			"type": "number",
			"defaultValue": "1000"
		},
		{
			"name": "MinDimNew",
			"type": "number",
			"defaultValue": "1450"
		},
		{
			"name": "MaxDimOld",
			"type": "number",
			"defaultValue": "1500"
		}
	],
	"transformations": [
		{
			"transformation": "Trim",
			"fuzz": 0.08,
			"padding": 0
		},
		{
			"transformation": "IfDimension",
			"dimension": "width",
			"value": {
				"var": "MaxDimOld"
			},
			"default": {
				"transformation": "Compound",
				"transformations": [
					{
						"transformation": "IfDimension",
						"dimension": "width",
						"value": {
							"var": "MinDim"
						},
						"lessThan": {
							"transformation": "Compound",
							"transformations": [
								{
									"transformation": "Resize",
									"aspect": "fit",
									"type": "normal",
									"width": {
										"var": "ResizeDimWithBorder"
									},
									"height": {
										"var": "ResizeDimWithBorder"
									}
								},
								{
									"transformation": "Crop",
									"xPosition": 0,
									"yPosition": 0,
									"gravity": "Center",
									"allowExpansion": true,
									"width": {
										"var": "ResizeDim"
									},
									"height": {
										"var": "ResizeDim"
									}
								},
								{
									"transformation": "BackgroundColor",
									"color": "#ffffff"
								}
							]
						},
						"default": {
							"transformation": "Compound",
							"transformations": [
								{
									"transformation": "IfDimension",
									"dimension": "height",
									"value": {
										"var": "MinDim"
									},
									"lessThan": {
										"transformation": "Compound",
										"transformations": [
											{
												"transformation": "Resize",
												"aspect": "fit",
												"type": "normal",
												"width": {
													"var": "ResizeDimWithBorder"
												},
												"height": {
													"var": "ResizeDimWithBorder"
												}
											},
											{
												"transformation": "Crop",
												"xPosition": 0,
												"yPosition": 0,
												"gravity": "Center",
												"allowExpansion": true,
												"width": {
													"var": "ResizeDim"
												},
												"height": {
													"var": "ResizeDim"
												}
											},
											{
												"transformation": "BackgroundColor",
												"color": "#ffffff"
											}
										]
									},
									"default": {
										"transformation": "Compound",
										"transformations": [
											{
												"transformation": "IfDimension",
												"dimension": "height",
												"value": {
													"var": "MaxDimOld"
												},
												"greaterThan": {
													"transformation": "Compound",
													"transformations": [
														{
															"transformation": "Resize",
															"aspect": "fit",
															"type": "normal",
															"width": {
																"var": "ResizeDimWithBorder"
															},
															"height": {
																"var": "ResizeDimWithBorder"
															}
														},
														{
															"transformation": "Crop",
															"xPosition": 0,
															"yPosition": 0,
															"gravity": "Center",
															"allowExpansion": true,
															"width": {
																"var": "ResizeDim"
															},
															"height": {
																"var": "ResizeDim"
															}
														},
														{
															"transformation": "BackgroundColor",
															"color": "#ffffff"
														}
													]
												},
												"default": {
													"transformation": "Compound",
													"transformations": [
														{
															"transformation": "Resize",
															"aspect": "fit",
															"type": "normal",
															"width": {
																"var": "ResizeDim"
															},
															"height": {
																"var": "ResizeDim"
															}
														},
														{
															"transformation": "Crop",
															"xPosition": 0,
															"yPosition": 0,
															"gravity": "Center",
															"allowExpansion": true,
															"width": {
																"var": "ResizeDim"
															},
															"height": {
																"var": "ResizeDim"
															}
														},
														{
															"transformation": "BackgroundColor",
															"color": "#ffffff"
														}
													]
												}
											}
										]
									}
								}
							]
						}
					}
				]
			}
		}
	],
	"breakpoints": {
		"widths": [
			280
		]
	},
	"output": {
		"perceptualQuality": "mediumHigh",
		"adaptiveQuality": 50
	},
	"video": false,
	"id": "multidimension",
	"dateCreated": "2022-01-01 12:00:00+0000",
	"previousVersion": 0,
	"version": 1
        }
    ],
    "totalItems": 8
}"""


class TestListPolicies:
    """Tests for list_policies. Mirrors Go TestListPolicies (7 cases)."""

    def _assert_list_policies_8_items(self, result):
        """Validate the 8-policy response (7 image + 1 video)."""
        assert isinstance(result, ListPoliciesResponse)
        assert result.item_kind == "POLICY"
        assert result.total_items == 8
        assert len(result.items) == 8

        # .auto
        p0 = result.items[0]
        assert isinstance(p0, PolicyOutputImage)
        assert p0.id == ".auto"
        assert p0.version == 1
        assert p0.previous_version == 0
        assert p0.rollout_info == {"startTime": 1626379176, "endTime": 1626379177, "rolloutDuration": 1}
        assert p0.video is False
        assert p0.user == "system"
        assert p0.date_created == "2021-07-15 19:59:35+0000"

        # asd
        p1 = result.items[1]
        assert isinstance(p1, PolicyOutputImage)
        assert p1.id == "asd"
        assert p1.version == 2
        assert p1.breakpoints == {"widths": [320, 640, 1024, 2048, 5000]}
        assert p1.output == {"perceptualQuality": "mediumHigh"}
        assert len(p1.transformations) == 1
        assert p1.transformations[0]["transformation"] == "Composite"
        assert p1.transformations[0]["image"]["type"] == "Text"

        # cheese
        p2 = result.items[2]
        assert isinstance(p2, PolicyOutputImage)
        assert p2.id == "cheese"
        assert p2.breakpoints == {"widths": [720, 1080, 1366, 1920, 5000]}

        # example
        p3 = result.items[3]
        assert isinstance(p3, PolicyOutputImage)
        assert p3.id == "example"
        assert p3.version == 9
        assert len(p3.transformations) == 2
        assert p3.transformations[0]["transformation"] == "Blur"
        assert p3.transformations[1]["transformation"] == "MaxColors"
        assert len(p3.variables) == 1
        assert p3.variables[0]["name"] == "blurVar"

        # mgw
        p4 = result.items[4]
        assert isinstance(p4, PolicyOutputImage)
        assert p4.id == "mgw"

        # testPolicy2
        p5 = result.items[5]
        assert isinstance(p5, PolicyOutputImage)
        assert p5.id == "testPolicy2"

        # testpolicy
        p6 = result.items[6]
        assert isinstance(p6, PolicyOutputImage)
        assert p6.id == "testpolicy"

        # updatePolicy (VIDEO)
        p7 = result.items[7]
        assert isinstance(p7, PolicyOutputVideo)
        assert p7.id == "updatePolicy"
        assert p7.video is True
        assert p7.output == {"perceptualQuality": "mediumHigh"}

    def test_200_ok(self):
        """200 OK — 8 policies (7 image + 1 video). Mirrors Go case."""
        session = MagicMock()
        _mock_exec_success(session, 200, _LIST_POLICIES_200_OK_BODY)
        client = Client(session)

        result = client.list_policies(ListPoliciesRequest(
            network=POLICY_NETWORK_STAGING,
            contract_id="3-WNKXX1",
            policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
        ))
        _assert_exec_called(session, "GET", "/imaging/v2/network/staging/policies",
                            headers=_STD_POLICY_HEADERS)
        self._assert_list_policies_8_items(result)

    def test_200_ok_very_deep(self):
        """200 OK very deep — deeply nested IfDimension transformations."""
        session = MagicMock()
        _mock_exec_success(session, 200, _LIST_POLICIES_200_DEEP_BODY)
        client = Client(session)

        result = client.list_policies(ListPoliciesRequest(
            network=POLICY_NETWORK_STAGING,
            contract_id="3-WNKXX1",
            policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
        ))

        assert result.item_kind == "POLICY"
        assert result.total_items == 8
        assert len(result.items) == 1

        p0 = result.items[0]
        assert isinstance(p0, PolicyOutputImage)
        assert p0.id == "multidimension"
        assert p0.version == 1
        assert p0.previous_version == 0
        assert p0.breakpoints == {"widths": [280]}
        assert p0.output == {"perceptualQuality": "mediumHigh", "adaptiveQuality": 50}
        assert len(p0.variables) == 5
        assert p0.variables[0]["name"] == "ResizeDim"
        assert p0.variables[4]["name"] == "MaxDimOld"
        assert len(p0.transformations) == 2
        assert p0.transformations[0]["transformation"] == "Trim"
        assert p0.transformations[1]["transformation"] == "IfDimension"

    def test_400_bad_request(self):
        """400 Bad request. Mirrors Go case."""
        session = MagicMock()
        _mock_exec_error(session, _EXPECTED_400)
        client = Client(session)

        with pytest.raises(ImagingError) as exc_info:
            client.list_policies(ListPoliciesRequest(
                network=POLICY_NETWORK_STAGING,
                contract_id="3-WNKXX1",
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
            ))
        assert exc_info.value.status == 400
        assert exc_info.value.title == "Bad Request"

    def test_401_not_authorized(self):
        """401 Not authorized. Mirrors Go case."""
        session = MagicMock()
        _mock_exec_error(session, _EXPECTED_401)
        client = Client(session)

        with pytest.raises(ImagingError) as exc_info:
            client.list_policies(ListPoliciesRequest(
                network=POLICY_NETWORK_STAGING,
                contract_id="3-WNKXX1",
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
            ))
        assert exc_info.value.status == 401

    def test_403_forbidden(self):
        """403 Forbidden. Mirrors Go case."""
        session = MagicMock()
        _mock_exec_error(session, _EXPECTED_403)
        client = Client(session)

        with pytest.raises(ImagingError) as exc_info:
            client.list_policies(ListPoliciesRequest(
                network=POLICY_NETWORK_STAGING,
                contract_id="3-WNKXX1",
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
            ))
        assert exc_info.value.status == 403

    def test_invalid_network(self):
        """Validation error for invalid network. Mirrors Go case."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.list_policies(ListPoliciesRequest(
                contract_id="3-WNKXX1",
                network="foo",
            ))

    def test_missing_contract(self):
        """Validation error for missing contract. Mirrors Go case."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.list_policies(ListPoliciesRequest(
                network=POLICY_NETWORK_PRODUCTION,
            ))


_GET_POLICY_IMAGE_BODY = """
        {
            "id": "foo",
            "version": 2,
            "previousVersion": 1,
            "rolloutInfo": {
                "startTime": 1638894035,
                "endTime": 1638894036,
                "rolloutDuration": 1
            },
            "breakpoints": {
                "widths": [
                    320,
                    640,
                    1024,
                    2048,
                    5000
                ]
            },
            "output": {
                "perceptualQuality": "mediumHigh"
            },
            "transformations": [
				{
					"transformation": "Append",
					"gravity": "Center",
					"gravityPriority": "horizontal",
					"preserveMinorDimension": true,
					"image": {
						"type": "Text",
						"fill": "#000000",
						"size": 72,
						"stroke": "#FFFFFF",
						"strokeSize": 0,
						"text": "test",
						"transformation": {
							"transformation": "Compound",
							"transformations": []
						}
					}
				},
				{
					"transformation": "RegionOfInterestCrop",
					"style": "fill",
					"gravity": "Center",
					"width": 7,
					"height": 8,
					"regionOfInterest": {
						"anchor": {
							"x": 4,
							"y": 5
						},
						"width": 8,
						"height": 9
					}
				},
                {
                    "transformation": "Composite",
                    "xPosition": 0,
                    "yPosition": 0,
                    "gravity": "NorthWest",
                    "placement": "Over",
                    "image": {
                        "type": "Text",
                        "fill": "#000000",
                        "size": 72,
                        "stroke": "#FFFFFF",
                        "strokeSize": 0,
                        "text": "Hello There",
                        "transformation": {
                            "transformation": "Compound",
                            "transformations": []
                        }
                    }
                }
            ],
            "video": false,
            "user": "jsmith",
            "dateCreated": "2021-12-07 16:20:34+0000"
}"""

_GET_POLICY_IMAGE_POST_BREAK_BODY = """
        {
            "id": "foo",
            "version": 2,
            "previousVersion": 1,
            "rolloutInfo": {
                "startTime": 1638894035,
                "endTime": 1638894036,
                "rolloutDuration": 1
            },
            "breakpoints": {
                "widths": [
                    320,
                    640,
                    1024,
                    2048,
                    5000
                ]
            },
            "output": {
                "perceptualQuality": "mediumHigh"
            },
            "transformations": [
				{
					"transformation": "Append",
					"gravity": "Center",
					"gravityPriority": "horizontal",
					"preserveMinorDimension": true,
					"image": {
						"type": "Text",
						"fill": "#000000",
						"size": 72,
						"stroke": "#FFFFFF",
						"strokeSize": 0,
						"text": "test",
						"transformation": {
							"transformation": "Compound",
							"transformations": []
						}
					}
				},
				{
					"transformation": "RegionOfInterestCrop",
					"style": "fill",
					"gravity": "Center",
					"width": 7,
					"height": 8,
					"regionOfInterest": {
						"anchor": {
							"x": 4,
							"y": 5
						},
						"width": 8,
						"height": 9
					}
				},
                {
                    "transformation": "Composite",
                    "xPosition": 0,
                    "yPosition": 0,
                    "gravity": "NorthWest",
                    "placement": "Over",
                    "image": {
                        "type": "Text",
                        "fill": "#000000",
                        "size": 72,
                        "stroke": "#FFFFFF",
                        "strokeSize": 0,
                        "text": "Hello There",
                        "transformation": {
                            "transformation": "Compound",
                            "transformations": []
                        }
                    }
                }
            ],
			"postBreakpointTransformations": [
					{
						"transformation": "IfDimension",
						"dimension": "width",
						"value": {
							"var": "MaxDimOld"
						},
						"default": {
							"transformation": "Compound",
							"transformations": [
								{
									"transformation": "IfDimension",
									"dimension": "width",
									"value": {
										"var": "MinDim"
									},
									"lessThan": {
										"transformation": "Compound",
										"transformations": [
											{
												"transformation": "BackgroundColor",
												"color": "#ffffff"
											},
											{
												"transformation": "BackgroundColor",
												"color": "#00ffff"
											}
										]
									}
								}
							]
						}
					},
					{
					  "transformation": "Composite",
					  "xPosition": 0,
					  "yPosition": 0,
					  "gravity": "NorthWest",
					  "placement": "Over",
					  "image": {
						"type": "Text",
						"fill": "#000000",
						"size": 72,
						"stroke": "#FFFFFF",
						"strokeSize": 0,
						"text": "test",
						"transformation": {
						  "transformation": "Compound",
						  "transformations": []
						}
					  }
					}
				],
            "video": false,
            "user": "jsmith",
            "dateCreated": "2021-12-07 16:20:34+0000"
}"""

_GET_POLICY_VIDEO_BODY = """
	       {
	           "id": "foo",
	           "version": 2,
	           "previousVersion": 1,
	           "rolloutInfo": {
	               "startTime": 1643055431,
	               "endTime": 1643055432,
	               "rolloutDuration": 1
	           },
	           "output": {
	               "perceptualQuality": "mediumHigh"
	           },
	           "video": true,
	           "user": "jsmith",
	           "dateCreated": "2022-01-24 20:17:10+0000"
	}"""


class TestGetPolicy:
    """Tests for get_policy. Mirrors Go TestGetPolicy (8 cases)."""

    def test_200_ok_image(self):
        """200 OK - image policy with Append, RegionOfInterestCrop, Composite."""
        session = MagicMock()
        _mock_exec_success(session, 200, _GET_POLICY_IMAGE_BODY)
        client = Client(session)

        result = client.get_policy(GetPolicyRequest(**_STD_POLICY_PARAMS_KWARGS))
        _assert_exec_called(session, "GET", "/imaging/v2/network/staging/policies/foo",
                            headers=_STD_POLICY_HEADERS)

        assert isinstance(result, PolicyOutputImage)
        assert result.id == "foo"
        assert result.version == 2
        assert result.previous_version == 1
        assert result.rollout_info == {"startTime": 1638894035, "endTime": 1638894036, "rolloutDuration": 1}
        assert result.breakpoints == {"widths": [320, 640, 1024, 2048, 5000]}
        assert result.output == {"perceptualQuality": "mediumHigh"}
        assert len(result.transformations) == 3
        assert result.transformations[0]["transformation"] == "Append"
        assert result.transformations[1]["transformation"] == "RegionOfInterestCrop"
        assert result.transformations[2]["transformation"] == "Composite"
        assert result.video is False
        assert result.user == "jsmith"
        assert result.date_created == "2021-12-07 16:20:34+0000"

    def test_200_ok_image_post_break_transformation(self):
        """200 OK - image with postBreakpointTransformations."""
        session = MagicMock()
        _mock_exec_success(session, 200, _GET_POLICY_IMAGE_POST_BREAK_BODY)
        client = Client(session)

        result = client.get_policy(GetPolicyRequest(**_STD_POLICY_PARAMS_KWARGS))

        assert isinstance(result, PolicyOutputImage)
        assert result.id == "foo"
        assert len(result.transformations) == 3
        assert len(result.post_breakpoint_transformations) == 2
        assert result.post_breakpoint_transformations[0]["transformation"] == "IfDimension"
        assert result.post_breakpoint_transformations[1]["transformation"] == "Composite"

    def test_200_ok_video(self):
        """200 OK - video policy. Mirrors Go case."""
        session = MagicMock()
        _mock_exec_success(session, 200, _GET_POLICY_VIDEO_BODY)
        client = Client(session)

        result = client.get_policy(GetPolicyRequest(**_STD_POLICY_PARAMS_KWARGS))

        assert isinstance(result, PolicyOutputVideo)
        assert result.id == "foo"
        assert result.version == 2
        assert result.previous_version == 1
        assert result.rollout_info == {"startTime": 1643055431, "endTime": 1643055432, "rolloutDuration": 1}
        assert result.output == {"perceptualQuality": "mediumHigh"}
        assert result.video is True
        assert result.user == "jsmith"

    def test_400_bad_request(self):
        """400 Bad request. Mirrors Go case."""
        session = MagicMock()
        _mock_exec_error(session, _EXPECTED_400)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.get_policy(GetPolicyRequest(**_STD_POLICY_PARAMS_KWARGS))
        assert exc_info.value.status == 400

    def test_401_not_authorized(self):
        """401 Not authorized. Mirrors Go case."""
        session = MagicMock()
        _mock_exec_error(session, _EXPECTED_401)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.get_policy(GetPolicyRequest(**_STD_POLICY_PARAMS_KWARGS))
        assert exc_info.value.status == 401

    def test_403_forbidden(self):
        """403 Forbidden. Mirrors Go case."""
        session = MagicMock()
        _mock_exec_error(session, _EXPECTED_403)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.get_policy(GetPolicyRequest(**_STD_POLICY_PARAMS_KWARGS))
        assert exc_info.value.status == 403

    def test_invalid_network(self):
        """Validation: invalid network."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.get_policy(GetPolicyRequest(
                contract_id="3-WNKXX1", network="foo",
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8", policy_id="foo",
            ))

    def test_missing_contract(self):
        """Validation: missing contract."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.get_policy(GetPolicyRequest(
                network=POLICY_NETWORK_PRODUCTION,
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8", policy_id="foo",
            ))

    def test_missing_policy_id(self):
        """Validation: missing policy id."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.get_policy(GetPolicyRequest(
                network=POLICY_NETWORK_PRODUCTION, contract_id="3-WNKXX1",
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
            ))

    def test_missing_policy_set_id(self):
        """Validation: missing policy set id."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.get_policy(GetPolicyRequest(
                network=POLICY_NETWORK_PRODUCTION, policy_id="foo", contract_id="3-WNKXX1",
            ))


_UPSERT_RESPONSE_BODY = '{"operationPerformed": "UPDATED", "description": "Policy foo updated.", "id": "foo"}'


class TestPutPolicy:
    """Tests for upsert_policy. Mirrors Go TestPutPolicy (9 cases)."""

    def test_200_ok_image(self):
        """200 OK - image upsert. Mirrors Go case."""
        session = MagicMock()
        _mock_exec_success(session, 200, _UPSERT_RESPONSE_BODY)
        client = Client(session)

        result = client.upsert_policy(UpsertPolicyRequest(
            network=POLICY_NETWORK_STAGING,
            contract_id="3-WNKXX1",
            policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
            policy_id="foo",
            policy_input=PolicyInputImage(
                breakpoints={"widths": [320, 640, 1024, 2048, 5000]},
                output={"perceptualQuality": "mediumHigh"},
                transformations=[{
                    "transformation": "Composite",
                    "xPosition": 0,
                    "yPosition": 0,
                    "gravity": "NorthWest",
                    "placement": "Over",
                    "image": {
                        "type": "Text",
                        "fill": "#000000",
                        "size": 72,
                        "stroke": "#FFFFFF",
                        "strokeSize": 0,
                        "text": "Hello There",
                        "transformation": {
                            "transformation": "Compound",
                        },
                    },
                }],
            ),
        ))

        _assert_exec_called(session, "PUT", "/imaging/v2/network/staging/policies/foo",
                            headers=_STD_POLICY_HEADERS)
        assert isinstance(result, PolicyResponse)
        assert result.operation_performed == "UPDATED"
        assert result.description == "Policy foo updated."
        assert result.id == "foo"

        # Verify request body was sent
        call_kwargs = session.exec.call_args[1]
        body = call_kwargs.get("body", {})
        assert "breakpoints" in body
        assert body["breakpoints"] == {"widths": [320, 640, 1024, 2048, 5000]}
        assert "transformations" in body

    def test_200_ok_video(self):
        """200 OK - video upsert. Mirrors Go case."""
        session = MagicMock()
        _mock_exec_success(session, 200, _UPSERT_RESPONSE_BODY)
        client = Client(session)

        result = client.upsert_policy(UpsertPolicyRequest(
            network=POLICY_NETWORK_STAGING,
            contract_id="3-WNKXX1",
            policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
            policy_id="foo",
            policy_input=PolicyInputVideo(
                output={"perceptualQuality": "mediumHigh"},
            ),
        ))

        _assert_exec_called(session, "PUT", "/imaging/v2/network/staging/policies/foo",
                            headers=_STD_POLICY_HEADERS)
        assert result.operation_performed == "UPDATED"
        assert result.id == "foo"

    def test_400_bad_request(self):
        """400 Bad request. Mirrors Go case."""
        session = MagicMock()
        _mock_exec_error(session, _EXPECTED_400)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.upsert_policy(UpsertPolicyRequest(
                network=POLICY_NETWORK_STAGING, contract_id="3-WNKXX1",
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
                policy_id="foo", policy_input=PolicyInputImage(),
            ))
        assert exc_info.value.status == 400

    def test_401_not_authorized(self):
        """401 Not authorized. Mirrors Go case."""
        session = MagicMock()
        _mock_exec_error(session, _EXPECTED_401)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.upsert_policy(UpsertPolicyRequest(
                network=POLICY_NETWORK_STAGING, contract_id="3-WNKXX1",
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
                policy_id="foo", policy_input=PolicyInputImage(),
            ))
        assert exc_info.value.status == 401

    def test_403_forbidden(self):
        """403 Forbidden. Mirrors Go case."""
        session = MagicMock()
        _mock_exec_error(session, _EXPECTED_403)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.upsert_policy(UpsertPolicyRequest(
                network=POLICY_NETWORK_STAGING, contract_id="3-WNKXX1",
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
                policy_id="foo", policy_input=PolicyInputImage(),
            ))
        assert exc_info.value.status == 403

    def test_invalid_network(self):
        """Validation: invalid network."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.upsert_policy(UpsertPolicyRequest(
                contract_id="3-WNKXX1", network="foo",
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8", policy_id="foo",
            ))

    def test_missing_contract(self):
        """Validation: missing contract."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.upsert_policy(UpsertPolicyRequest(
                network=POLICY_NETWORK_PRODUCTION,
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8", policy_id="foo",
            ))

    def test_missing_policy_id(self):
        """Validation: missing policy id."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.upsert_policy(UpsertPolicyRequest(
                network=POLICY_NETWORK_PRODUCTION, contract_id="3-WNKXX1",
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
            ))

    def test_missing_policy_set_id(self):
        """Validation: missing policy set id."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.upsert_policy(UpsertPolicyRequest(
                network=POLICY_NETWORK_PRODUCTION, policy_id="foo", contract_id="3-WNKXX1",
            ))

    def test_missing_policy(self):
        """Validation: missing policy input."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.upsert_policy(UpsertPolicyRequest(
                network=POLICY_NETWORK_PRODUCTION, policy_id="foo",
                contract_id="3-WNKXX1",
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
            ))


class TestDeletePolicy:
    """Tests for delete_policy. Mirrors Go TestDeletePolicy (8 cases)."""

    def test_200_ok(self):
        """200 OK - successful deletion."""
        session = MagicMock()
        body = '{"operationPerformed": "DELETED", "description": "Policy foo deleted.", "id": "foo"}'
        _mock_exec_success(session, 200, body)
        client = Client(session)

        result = client.delete_policy(DeletePolicyRequest(**_STD_POLICY_PARAMS_KWARGS))
        _assert_exec_called(session, "DELETE", "/imaging/v2/network/staging/policies/foo",
                            headers=_STD_POLICY_HEADERS)
        assert result.operation_performed == "DELETED"
        assert result.description == "Policy foo deleted."
        assert result.id == "foo"

    def test_400_bad_request(self):
        """400 Bad request."""
        session = MagicMock()
        _mock_exec_error(session, _EXPECTED_400)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.delete_policy(DeletePolicyRequest(**_STD_POLICY_PARAMS_KWARGS))
        assert exc_info.value.status == 400

    def test_401_not_authorized(self):
        """401 Not authorized."""
        session = MagicMock()
        _mock_exec_error(session, _EXPECTED_401)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.delete_policy(DeletePolicyRequest(**_STD_POLICY_PARAMS_KWARGS))
        assert exc_info.value.status == 401

    def test_403_forbidden(self):
        """403 Forbidden."""
        session = MagicMock()
        _mock_exec_error(session, _EXPECTED_403)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.delete_policy(DeletePolicyRequest(**_STD_POLICY_PARAMS_KWARGS))
        assert exc_info.value.status == 403

    def test_invalid_network(self):
        """Validation: invalid network."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.delete_policy(DeletePolicyRequest(
                contract_id="3-WNKXX1", network="foo",
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8", policy_id="foo",
            ))

    def test_missing_contract(self):
        """Validation: missing contract."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.delete_policy(DeletePolicyRequest(
                network=POLICY_NETWORK_PRODUCTION,
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8", policy_id="foo",
            ))

    def test_missing_policy_id(self):
        """Validation: missing policy id."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.delete_policy(DeletePolicyRequest(
                network=POLICY_NETWORK_PRODUCTION, contract_id="3-WNKXX1",
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
            ))

    def test_missing_policy_set_id(self):
        """Validation: missing policy set id."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.delete_policy(DeletePolicyRequest(
                network=POLICY_NETWORK_PRODUCTION, policy_id="foo", contract_id="3-WNKXX1",
            ))


# Embedded policy JSON strings from GetPolicyHistory test data (verbatim from Go)
_HISTORY_POLICY_1 = (
    '{"breakpoints":{"widths":[320,640,1024,2048,5000]},"output":{"perceptualQuality":"mediumHigh"},"transformations":[{"transformation":"Composite","xPosition":0,"yPosition":0,"gravity":"NorthWest","placement":"Over","image":{"type":"Text","fill":"#000000","size":72,"stroke":"#FFFFFF","strokeSize":0,"text":"Hello There","transformation":{"transformation":"Compound","transformations":[]}}}],"video":false}'
)
_HISTORY_POLICY_2 = (
    '{"breakpoints":{"widths":[320,640,1024,2048,5000]},"output":{"perceptualQuality":"mediumHigh"},"transformations":[{"transformation":"Composite","xPosition":0,"yPosition":0,"gravity":"NorthWest","placement":"Over","image":{"type":"Text","fill":"#000000","size":72,"stroke":"#FFFFFF","strokeSize":0,"text":"Hello","transformation":{"transformation":"Compound","transformations":[]}}}],"video":false}'
)


_HISTORY_200_BODY = (
    '{"itemKind": "POLICIESLOG", "items": [{"id": "foo", "dateCreated": "2021-12-07 16:20:34+0000", "action": "UPSERT", "user": "jsmith", "version": 2, "policy": "{\\"breakpoints\\":{\\"widths\\":[320,640,1024,2048,5000]},\\"output\\":{\\"perceptualQuality\\":\\"mediumHigh\\"},\\"transformations\\":[{\\"transformation\\":\\"Composite\\",\\"xPosition\\":0,\\"yPosition\\":0,\\"gravity\\":\\"NorthWest\\",\\"placement\\":\\"Over\\",\\"image\\":{\\"type\\":\\"Text\\",\\"fill\\":\\"#000000\\",\\"size\\":72,\\"stroke\\":\\"#FFFFFF\\",\\"strokeSize\\":0,\\"text\\":\\"Hello There\\",\\"transformation\\":{\\"transformation\\":\\"Compound\\",\\"transformations\\":[]}}}],\\"video\\":false}"}, {"id": "asd", "dateCreated": "2021-12-07 16:18:39+0000", "action": "UPSERT", "user": "asmith", "version": 1, "policy": "{\\"breakpoints\\":{\\"widths\\":[320,640,1024,2048,5000]},\\"output\\":{\\"perceptualQuality\\":\\"mediumHigh\\"},\\"transformations\\":[{\\"transformation\\":\\"Composite\\",\\"xPosition\\":0,\\"yPosition\\":0,\\"gravity\\":\\"NorthWest\\",\\"placement\\":\\"Over\\",\\"image\\":{\\"type\\":\\"Text\\",\\"fill\\":\\"#000000\\",\\"size\\":72,\\"stroke\\":\\"#FFFFFF\\",\\"strokeSize\\":0,\\"text\\":\\"Hello\\",\\"transformation\\":{\\"transformation\\":\\"Compound\\",\\"transformations\\":[]}}}],\\"video\\":false}"}], "totalItems": 2}'
)


class TestGetPolicyHistory:
    """Tests for get_policy_history. Mirrors Go TestGetPolicyHistory (8 cases)."""

    def test_200_ok(self):
        """200 OK - 2 history items."""
        session = MagicMock()
        _mock_exec_success(session, 200, _HISTORY_200_BODY)
        client = Client(session)

        result = client.get_policy_history(GetPolicyHistoryRequest(**_STD_POLICY_PARAMS_KWARGS))
        _assert_exec_called(session, "GET", "/imaging/v2/network/staging/policies/history/foo",
                            headers=_STD_POLICY_HEADERS)

        assert isinstance(result, GetPolicyHistoryResponse)
        assert result.item_kind == "POLICIESLOG"
        assert result.total_items == 2
        assert len(result.items) == 2

        item0 = result.items[0]
        assert isinstance(item0, PolicyHistoryItem)
        assert item0.id == "foo"
        assert item0.date_created == "2021-12-07 16:20:34+0000"
        assert item0.action == "UPSERT"
        assert item0.user == "jsmith"
        assert item0.version == 2
        assert item0.policy == _HISTORY_POLICY_1

        item1 = result.items[1]
        assert item1.id == "asd"
        assert item1.date_created == "2021-12-07 16:18:39+0000"
        assert item1.action == "UPSERT"
        assert item1.user == "asmith"
        assert item1.version == 1
        assert item1.policy == _HISTORY_POLICY_2

    def test_400_bad_request(self):
        """400 Bad request."""
        session = MagicMock()
        _mock_exec_error(session, _EXPECTED_400)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.get_policy_history(GetPolicyHistoryRequest(**_STD_POLICY_PARAMS_KWARGS))
        assert exc_info.value.status == 400

    def test_401_not_authorized(self):
        """401 Not authorized."""
        session = MagicMock()
        _mock_exec_error(session, _EXPECTED_401)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.get_policy_history(GetPolicyHistoryRequest(**_STD_POLICY_PARAMS_KWARGS))
        assert exc_info.value.status == 401

    def test_403_forbidden(self):
        """403 Forbidden."""
        session = MagicMock()
        _mock_exec_error(session, _EXPECTED_403)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.get_policy_history(GetPolicyHistoryRequest(**_STD_POLICY_PARAMS_KWARGS))
        assert exc_info.value.status == 403

    def test_invalid_network(self):
        """Validation: invalid network."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.get_policy_history(GetPolicyHistoryRequest(
                contract_id="3-WNKXX1", network="foo",
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8", policy_id="foo",
            ))

    def test_missing_contract(self):
        """Validation: missing contract."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.get_policy_history(GetPolicyHistoryRequest(
                network=POLICY_NETWORK_PRODUCTION,
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8", policy_id="foo",
            ))

    def test_missing_policy_id(self):
        """Validation: missing policy id."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.get_policy_history(GetPolicyHistoryRequest(
                network=POLICY_NETWORK_PRODUCTION, contract_id="3-WNKXX1",
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
            ))

    def test_missing_policy_set_id(self):
        """Validation: missing policy set id."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.get_policy_history(GetPolicyHistoryRequest(
                network=POLICY_NETWORK_PRODUCTION, policy_id="foo", contract_id="3-WNKXX1",
            ))


class TestRollbackPolicy:
    """Tests for rollback_policy. Mirrors Go TestRollbackPolicy (8 cases)."""

    def test_200_ok(self):
        """200 OK - successful rollback."""
        session = MagicMock()
        body = '{"operationPerformed": "UPDATED", "description": "Policy foo has been rolled back to version 3.", "id": "foo"}'
        _mock_exec_success(session, 200, body)
        client = Client(session)

        result = client.rollback_policy(RollbackPolicyRequest(**_STD_POLICY_PARAMS_KWARGS))
        _assert_exec_called(session, "PUT", "/imaging/v2/network/staging/policies/rollback/foo",
                            headers=_STD_POLICY_HEADERS)
        assert result.operation_performed == "UPDATED"
        assert result.description == "Policy foo has been rolled back to version 3."
        assert result.id == "foo"

    def test_400_bad_request(self):
        """400 Bad request."""
        session = MagicMock()
        _mock_exec_error(session, _EXPECTED_400)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.rollback_policy(RollbackPolicyRequest(**_STD_POLICY_PARAMS_KWARGS))
        assert exc_info.value.status == 400

    def test_401_not_authorized(self):
        """401 Not authorized."""
        session = MagicMock()
        _mock_exec_error(session, _EXPECTED_401)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.rollback_policy(RollbackPolicyRequest(**_STD_POLICY_PARAMS_KWARGS))
        assert exc_info.value.status == 401

    def test_403_forbidden(self):
        """403 Forbidden."""
        session = MagicMock()
        _mock_exec_error(session, _EXPECTED_403)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.rollback_policy(RollbackPolicyRequest(**_STD_POLICY_PARAMS_KWARGS))
        assert exc_info.value.status == 403

    def test_invalid_network(self):
        """Validation: invalid network."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.rollback_policy(RollbackPolicyRequest(
                contract_id="3-WNKXX1", network="foo",
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8", policy_id="foo",
            ))

    def test_missing_contract(self):
        """Validation: missing contract."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.rollback_policy(RollbackPolicyRequest(
                network=POLICY_NETWORK_PRODUCTION,
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8", policy_id="foo",
            ))

    def test_missing_policy_id(self):
        """Validation: missing policy id."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.rollback_policy(RollbackPolicyRequest(
                network=POLICY_NETWORK_PRODUCTION, contract_id="3-WNKXX1",
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
            ))

    def test_missing_policy_set_id(self):
        """Validation: missing policy set id."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.rollback_policy(RollbackPolicyRequest(
                network=POLICY_NETWORK_PRODUCTION, policy_id="foo", contract_id="3-WNKXX1",
            ))


# ==========================================
# PolicySet-specific error body constants
# ==========================================

_PS_LIST_ERR_400_BODY = '{"type": "https://problems.luna.akamaiapis.net/image-policy-manager/IVM_1004", "title": "Bad Request", "instance": "52a21f40-9861-4d35-95d0-a603c85cb2ad", "status": 400, "detail": "A contract must be specified using the ContractID header.", "problemId": "52a21f40-9861-4d35-95d0-a603c85cb2ad"}'

_PS_LIST_EXPECTED_400 = ImagingError(
    type="https://problems.luna.akamaiapis.net/image-policy-manager/IVM_1004",
    title="Bad Request",
    instance="52a21f40-9861-4d35-95d0-a603c85cb2ad",
    status=400,
    detail="A contract must be specified using the ContractID header.",
    problem_id="52a21f40-9861-4d35-95d0-a603c85cb2ad",
)

_PS_LIST_ERR_401_BODY = '{"type": "https://problems.luna-dev.akamaiapis.net/-/pep-authn/deny", "title": "Not authorized", "status": 401, "detail": "Inactive client token", "instance": "https://akaa-mgfkwp3rw4k2whym-eyn4wdjeur5lz37c.luna-dev.akamaiapis.net/imaging/v2/network/staging/policysets/", "method": "GET", "serverIp": "104.81.220.242", "clientIp": "22.22.22.22", "requestId": "124cc33c", "requestTime": "2022-01-12T16:53:44Z"}'

_PS_LIST_EXPECTED_401 = ImagingError(
    type="https://problems.luna-dev.akamaiapis.net/-/pep-authn/deny",
    title="Not authorized",
    status=401,
    detail="Inactive client token",
    instance="https://akaa-mgfkwp3rw4k2whym-eyn4wdjeur5lz37c.luna-dev.akamaiapis.net/imaging/v2/network/staging/policysets/",
    method="GET",
    server_ip="104.81.220.242",
    client_ip="22.22.22.22",
    request_id="124cc33c",
    request_time="2022-01-12T16:53:44Z",
)

_PS_LIST_ERR_403_BODY = '{"type": "https://problems.luna-dev.akamaiapis.net/-/pep-authz/deny", "title": "Forbidden", "status": 403, "detail": "The client does not have the grant needed for the request", "instance": "https://akaa-75xqbs7cot5jts7q-yjgmpc4nakckpt44.luna-dev.akamaiapis.net/imaging/v2/network/staging/policysets/", "authzRealm": "xlnausb2pov4jvuo.kh6prvchvniqn5zp", "method": "GET", "serverIp": "104.81.220.242", "clientIp": "22.22.22.22", "requestId": "1254027a", "requestTime": "2022-01-12T16:56:56Z"}'

_PS_LIST_EXPECTED_403 = ImagingError(
    type="https://problems.luna-dev.akamaiapis.net/-/pep-authz/deny",
    title="Forbidden",
    status=403,
    detail="The client does not have the grant needed for the request",
    instance="https://akaa-75xqbs7cot5jts7q-yjgmpc4nakckpt44.luna-dev.akamaiapis.net/imaging/v2/network/staging/policysets/",
    authz_realm="xlnausb2pov4jvuo.kh6prvchvniqn5zp",
    method="GET",
    server_ip="104.81.220.242",
    client_ip="22.22.22.22",
    request_id="1254027a",
    request_time="2022-01-12T16:56:56Z",
)

_STD_PS_HEADERS = {"Contract": "3-WNKXX1"}


class TestListPolicySets:
    """Tests for list_policy_sets. Mirrors Go TestListPolicySets (7 cases)."""

    def test_200_ok_both_networks(self):
        """200 OK - both networks (no network specified)."""
        session = MagicMock()
        body = (
            '[{"name": "terraform_beta_v2", "id": "570e9090-5dbe-11ec-8a0a-71665789c1d8", '
            '"type": "IMAGE", "region": "US", "properties": ["jsmith_sqa2"], '
            '"user": "jsmith", "lastModified": "2021-12-15 15:47:42+0000"}, '
            '{"name": "my_example_token", "id": "57c73ae0-5204-11ec-8a0a-71665789c1d8", '
            '"type": "IMAGE", "region": "US", "properties": [], '
            '"user": "jsmith", "lastModified": "2021-11-30 17:38:35+0000"}, '
            '{"name": "terraform_demo-1104268", "id": "terraform_demo-1104268", '
            '"type": "IMAGE", "region": "US", "properties": ["jsmith_sqa2"], '
            '"user": "System", "lastModified": "2021-12-15 15:51:54+0000"}]'
        )
        _mock_exec_success(session, 200, body)
        client = Client(session)

        result = client.list_policy_sets(ListPolicySetsRequest(contract_id="3-WNKXX1"))
        _assert_exec_called(session, "GET", "/imaging/v2/policysets", headers=_STD_PS_HEADERS)

        assert len(result) == 3
        assert isinstance(result[0], PolicySet)

        assert result[0].name == "terraform_beta_v2"
        assert result[0].id == "570e9090-5dbe-11ec-8a0a-71665789c1d8"
        assert result[0].type == "IMAGE"
        assert result[0].region == "US"
        assert result[0].properties == ["jsmith_sqa2"]
        assert result[0].user == "jsmith"
        assert result[0].last_modified == "2021-12-15 15:47:42+0000"

        assert result[1].name == "my_example_token"
        assert result[1].id == "57c73ae0-5204-11ec-8a0a-71665789c1d8"
        assert result[1].properties == []
        assert result[1].user == "jsmith"
        assert result[1].last_modified == "2021-11-30 17:38:35+0000"

        assert result[2].name == "terraform_demo-1104268"
        assert result[2].id == "terraform_demo-1104268"
        assert result[2].properties == ["jsmith_sqa2"]
        assert result[2].user == "System"
        assert result[2].last_modified == "2021-12-15 15:51:54+0000"

    def test_200_ok_staging_network(self):
        """200 OK - staging network."""
        session = MagicMock()
        body = (
            '[{"name": "terraform_beta_v2", "id": "570e9090-5dbe-11ec-8a0a-71665789c1d8", '
            '"type": "IMAGE", "region": "US", "properties": ["jsmith_sqa2"], '
            '"user": "jsmith", "lastModified": "2021-12-15 15:47:42+0000"}, '
            '{"name": "terraform_demo-1104268", "id": "terraform_demo-1104268", '
            '"type": "IMAGE", "region": "US", "properties": ["jsmith_sqa2"], '
            '"user": "System", "lastModified": "2021-12-15 15:51:54+0000"}]'
        )
        _mock_exec_success(session, 200, body)
        client = Client(session)

        result = client.list_policy_sets(ListPolicySetsRequest(
            contract_id="3-WNKXX1", network=NETWORK_STAGING,
        ))
        _assert_exec_called(session, "GET", "/imaging/v2/network/staging/policysets",
                            headers=_STD_PS_HEADERS)

        assert len(result) == 2
        assert result[0].name == "terraform_beta_v2"
        assert result[1].name == "terraform_demo-1104268"

    def test_400_bad_request(self):
        """400 Bad request."""
        session = MagicMock()
        _mock_exec_error(session, _PS_LIST_EXPECTED_400)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.list_policy_sets(ListPolicySetsRequest(contract_id="3-WNKXX1"))
        assert exc_info.value.status == 400

    def test_401_not_authorized(self):
        """401 Not authorized."""
        session = MagicMock()
        _mock_exec_error(session, _PS_LIST_EXPECTED_401)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.list_policy_sets(ListPolicySetsRequest(contract_id="3-WNKXX1"))
        assert exc_info.value.status == 401

    def test_403_forbidden(self):
        """403 Forbidden."""
        session = MagicMock()
        _mock_exec_error(session, _PS_LIST_EXPECTED_403)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.list_policy_sets(ListPolicySetsRequest(contract_id="3-WNKXX1"))
        assert exc_info.value.status == 403

    def test_invalid_network(self):
        """Validation: invalid network."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.list_policy_sets(ListPolicySetsRequest(
                contract_id="3-WNKXX1", network="foo",
            ))

    def test_missing_contract(self):
        """Validation: missing contract."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.list_policy_sets(ListPolicySetsRequest(
                network=NETWORK_PRODUCTION,
            ))


class TestGetPolicySet:
    """Tests for get_policy_set. Mirrors Go TestGetPolicySet (6 cases)."""

    def test_200_ok_both_networks(self):
        """200 OK for both networks (no network specified)."""
        session = MagicMock()
        body = (
            '{"id": "570f9090-5dbe-11ec-8a0a-71665789c1d8", '
            '"name": "terraform_beta_v2", "region": "US", '
            '"type": "IMAGE", "properties": ["jsmith_sqa2"], '
            '"user": "jsmith", "lastModified": "2021-12-15 15:47:42+0000"}'
        )
        _mock_exec_success(session, 200, body)
        client = Client(session)

        result = client.get_policy_set(GetPolicySetRequest(
            policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
            contract_id="3-WNKXX1",
        ))
        _assert_exec_called(session, "GET",
                            "/imaging/v2/policysets/570f9090-5dbe-11ec-8a0a-71665789c1d8",
                            headers=_STD_PS_HEADERS)

        assert result.id == "570f9090-5dbe-11ec-8a0a-71665789c1d8"
        assert result.name == "terraform_beta_v2"
        assert result.region == "US"
        assert result.type == "IMAGE"
        assert result.properties == ["jsmith_sqa2"]
        assert result.user == "jsmith"
        assert result.last_modified == "2021-12-15 15:47:42+0000"

    def test_200_ok_staging_network(self):
        """200 OK for staging network."""
        session = MagicMock()
        body = (
            '{"id": "570f9090-5dbe-11ec-8a0a-71665789c1d8", '
            '"name": "terraform_beta_v2", "region": "US", '
            '"type": "IMAGE", "properties": ["jsmith_sqa2"], '
            '"user": "jsmith", "lastModified": "2021-12-15 15:47:42+0000"}'
        )
        _mock_exec_success(session, 200, body)
        client = Client(session)

        result = client.get_policy_set(GetPolicySetRequest(
            policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
            contract_id="3-WNKXX1",
            network=NETWORK_STAGING,
        ))
        _assert_exec_called(session, "GET",
                            "/imaging/v2/network/staging/policysets/570f9090-5dbe-11ec-8a0a-71665789c1d8",
                            headers=_STD_PS_HEADERS)

        assert result.id == "570f9090-5dbe-11ec-8a0a-71665789c1d8"
        assert result.name == "terraform_beta_v2"

    def test_404_not_found(self):
        """404 Not found."""
        session = MagicMock()
        expected = ImagingError(
            type="https://problems.luna.akamaiapis.net/image-policy-manager/IVM_9000",
            title="Not Found",
            instance="21bde25b-c9a5-4987-b1d5-0c3b92f77b2e",
            status=404,
            detail="Policy set does not exist.",
            extension_fields={"requestId": "5f94ea1284bf1800"},
            problem_id="21bde25b-c9a5-4987-b1d5-0c3b92f77b2e",
            request_id="5f94ea1284bf1800",
        )
        _mock_exec_error(session, expected)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.get_policy_set(GetPolicySetRequest(
                policy_set_id="570f9090-5dbe-11ec-8a0a",
                contract_id="3-WNKXX1",
            ))
        assert exc_info.value.status == 404
        assert exc_info.value.detail == "Policy set does not exist."

    def test_missing_policy_set_id(self):
        """Validation: missing PolicySetId."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.get_policy_set(GetPolicySetRequest(
                contract_id="3-WNKXX1", network=NETWORK_PRODUCTION,
            ))

    def test_invalid_network(self):
        """Validation: invalid network."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.get_policy_set(GetPolicySetRequest(
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
                contract_id="3-WNKXX1", network="foo",
            ))

    def test_missing_contract(self):
        """Validation: missing contract."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.get_policy_set(GetPolicySetRequest(
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
                network=NETWORK_PRODUCTION,
            ))


class TestCreatePolicySet:
    """Tests for create_policy_set. Mirrors Go TestCreatePolicySet (10 cases)."""

    def test_201_created(self):
        """201 created - simple creation."""
        session = MagicMock()
        body = (
            '{"name": "my_example_token", '
            '"id": "29467ef0-751d-11ec-7a0a-71665789c1d8", '
            '"type": "IMAGE", "region": "US", '
            '"properties": [], "user": "ftzgvvigljhoq5ia", '
            '"lastModified": "2022-01-14 09:34:25+0000"}'
        )
        _mock_exec_success(session, 201, body)
        client = Client(session)

        result = client.create_policy_set(CreatePolicySetRequest(
            contract_id="3-WNKXX1",
            name="my_example_token",
            type="IMAGE",
            region="US",
        ))
        _assert_exec_called(session, "POST", "/imaging/v2/policysets", headers=_STD_PS_HEADERS)

        # Verify request body
        call_kwargs = session.exec.call_args
        req_body = call_kwargs.kwargs.get("body", call_kwargs[1].get("body")) if call_kwargs.kwargs else call_kwargs[1].get("body")
        assert req_body == {"name": "my_example_token", "region": "US", "type": "IMAGE"}

        assert result.name == "my_example_token"
        assert result.id == "29467ef0-751d-11ec-7a0a-71665789c1d8"
        assert result.type == "IMAGE"
        assert result.region == "US"
        assert not result.properties
        assert result.user == "ftzgvvigljhoq5ia"
        assert result.last_modified == "2022-01-14 09:34:25+0000"

    def test_201_created_with_default_policy(self):
        """201 created with default policy (PolicyInputVideo)."""
        session = MagicMock()
        body = (
            '{"name": "my_example_token", '
            '"id": "29467ef0-751d-11ec-7a0a-71665789c1d8", '
            '"type": "IMAGE", "region": "US", '
            '"properties": [], "user": "ftzgvvigljhoq5ia", '
            '"lastModified": "2022-01-14 09:34:25+0000"}'
        )
        _mock_exec_success(session, 201, body)
        client = Client(session)

        default_policy = PolicyInputVideo(
            output=OutputVideo(
                perceptual_quality=OutputVideoPerceptualQualityVariableInline(
                    value="mediumHigh",
                ),
            ),
        )
        result = client.create_policy_set(CreatePolicySetRequest(
            contract_id="3-WNKXX1",
            name="my_example_token",
            type="IMAGE",
            region="US",
            default_policy=default_policy,
        ))
        _assert_exec_called(session, "POST", "/imaging/v2/policysets", headers=_STD_PS_HEADERS)

        # Verify request body includes defaultPolicy
        call_kwargs = session.exec.call_args
        req_body = call_kwargs.kwargs.get("body", call_kwargs[1].get("body")) if call_kwargs.kwargs else call_kwargs[1].get("body")
        assert "defaultPolicy" in req_body
        # model_to_dict serialises VariableInline types as nested dicts
        assert req_body["defaultPolicy"]["output"]["perceptualQuality"]["value"] == "mediumHigh"

        assert result.name == "my_example_token"
        assert result.id == "29467ef0-751d-11ec-7a0a-71665789c1d8"

    def test_400_bad_request(self):
        """400 Bad request."""
        session = MagicMock()
        expected = ImagingError(
            type="https://problems.luna.akamaiapis.net/image-policy-manager/IVM_1004",
            title="Bad Request",
            instance="5ea0274b-2322-4a0a-92ee-fabaa5a84d41",
            status=400,
            detail="A contract must be specified using the ContractID header.",
            problem_id="5ea0274b-2322-4a0a-92ee-fabaa5a84d41",
        )
        _mock_exec_error(session, expected)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.create_policy_set(CreatePolicySetRequest(
                contract_id="3-WNKXX1",
                name="my_example_token",
                type="IMAGE",
                region="US",
            ))
        assert exc_info.value.status == 400

    def test_missing_policy_set_id(self):
        """Validation: missing PolicySetId (empty CreatePolicySet fields)."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.create_policy_set(CreatePolicySetRequest(
                contract_id="3-WNKXX1",
            ))

    def test_missing_contract(self):
        """Validation: missing contract."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.create_policy_set(CreatePolicySetRequest(
                name="my_example_token",
                type="IMAGE",
                region="US",
            ))

    def test_missing_name(self):
        """Validation: missing name."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.create_policy_set(CreatePolicySetRequest(
                contract_id="3-WNKXX1",
                type="IMAGE",
                region="US",
            ))

    def test_missing_type(self):
        """Validation: missing type."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.create_policy_set(CreatePolicySetRequest(
                contract_id="3-WNKXX1",
                name="my_example_token",
                region="US",
            ))

    def test_invalid_type(self):
        """Validation: invalid type."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.create_policy_set(CreatePolicySetRequest(
                contract_id="3-WNKXX1",
                name="my_example_token",
                type="INVALID",
                region="US",
            ))

    def test_missing_region(self):
        """Validation: missing region."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.create_policy_set(CreatePolicySetRequest(
                contract_id="3-WNKXX1",
                name="my_example_token",
                type="IMAGE",
            ))

    def test_invalid_region(self):
        """Validation: invalid region."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.create_policy_set(CreatePolicySetRequest(
                contract_id="3-WNKXX1",
                name="my_example_token",
                type="IMAGE",
                region="INVALID",
            ))

    def test_validation_error(self):
        """Validation: empty request."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.create_policy_set(CreatePolicySetRequest())


class TestUpdatePolicySet:
    """Tests for update_policy_set. Mirrors Go TestUpdatePolicySet (9 cases)."""

    def test_200_updated(self):
        """200 updated."""
        session = MagicMock()
        body = (
            '{"name": "my_renamed_token", '
            '"id": "1385f880-7477-11ec-8a0a-71665789c1d8", '
            '"type": "IMAGE", "region": "US", '
            '"properties": [], "user": "ftzgvvigljhoq5ib", '
            '"lastModified": "2022-01-14 10:35:11+0000"}'
        )
        _mock_exec_success(session, 200, body)
        client = Client(session)

        result = client.update_policy_set(UpdatePolicySetRequest(
            policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
            contract_id="3-WNKXX1",
            name="my_renamed_token_2",
            region="US",
        ))
        _assert_exec_called(session, "PUT",
                            "/imaging/v2/policysets/570f9090-5dbe-11ec-8a0a-71665789c1d8",
                            headers=_STD_PS_HEADERS)

        # Verify request body
        call_kwargs = session.exec.call_args
        req_body = call_kwargs.kwargs.get("body", call_kwargs[1].get("body")) if call_kwargs.kwargs else call_kwargs[1].get("body")
        assert req_body == {"name": "my_renamed_token_2", "region": "US"}

        assert result.name == "my_renamed_token"
        assert result.id == "1385f880-7477-11ec-8a0a-71665789c1d8"
        assert result.type == "IMAGE"
        assert result.region == "US"
        assert not result.properties
        assert result.user == "ftzgvvigljhoq5ib"
        assert result.last_modified == "2022-01-14 10:35:11+0000"

    def test_400_bad_request(self):
        """400 Bad request."""
        session = MagicMock()
        expected = ImagingError(
            type="https://problems.luna.akamaiapis.net/image-policy-manager/IVM_9000",
            title="Bad Request",
            instance="b10b7635-b1ab-4742-bd88-82a6fcdd791a",
            status=400,
            detail="Policy Set does not exist.",
            extension_fields={"requestId": "5f9605d49c62d759"},
            problem_id="b10b7635-b1ab-4742-bd88-82a6fcdd791a",
            request_id="5f9605d49c62d759",
        )
        _mock_exec_error(session, expected)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.update_policy_set(UpdatePolicySetRequest(
                policy_set_id="second",
                contract_id="3-WNKXX1",
                name="my_renamed_token",
                region="US",
            ))
        assert exc_info.value.status == 400

    def test_500_internal_server_error(self):
        """500 Internal server error."""
        session = MagicMock()
        expected = ImagingError(
            type="https://problems.luna.akamaiapis.net/image-policy-manager/IVM_9000",
            title="Internal Server Error",
            instance="3692e138-f0b7-4479-b12a-48cdee93cf4d",
            status=500,
            detail="An unexpected error has occurred",
            extension_fields={"requestId": "5f960786419d5e8d"},
            problem_id="3692e138-f0b7-4479-b12a-48cdee93cf4d",
            request_id="5f960786419d5e8d",
        )
        _mock_exec_error(session, expected)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.update_policy_set(UpdatePolicySetRequest(
                policy_set_id="second",
                contract_id="3-WNKXX1",
                name="my_renamed_token",
                region="EMEA",
            ))
        assert exc_info.value.status == 500

    def test_missing_policy_set_id(self):
        """Validation: missing PolicySetId."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.update_policy_set(UpdatePolicySetRequest(
                contract_id="3-WNKXX1",
            ))

    def test_missing_contract(self):
        """Validation: missing contract."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.update_policy_set(UpdatePolicySetRequest(
                name="my_example_token",
                region="US",
            ))

    def test_missing_name(self):
        """Validation: missing name."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.update_policy_set(UpdatePolicySetRequest(
                contract_id="3-WNKXX1",
                region="US",
            ))

    def test_missing_region(self):
        """Validation: missing region."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.update_policy_set(UpdatePolicySetRequest(
                contract_id="3-WNKXX1",
                name="my_example_token",
            ))

    def test_invalid_region(self):
        """Validation: invalid region."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.update_policy_set(UpdatePolicySetRequest(
                contract_id="3-WNKXX1",
                name="my_example_token",
                region="INVALID",
            ))

    def test_validation_error(self):
        """Validation: empty request."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.update_policy_set(UpdatePolicySetRequest())


class TestDeletePolicySet:
    """Tests for delete_policy_set. Mirrors Go TestDeletePolicySet (7 cases)."""

    def test_204_no_content(self):
        """204 no content (deleted)."""
        session = MagicMock()
        # delete_policy_set does not use expect_json, so exec returns (response, None)
        mock_response = MagicMock()
        mock_response.status_code = 204
        session.exec.return_value = (mock_response, None)
        client = Client(session)

        client.delete_policy_set(DeletePolicySetRequest(
            policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
            contract_id="3-WNKXX1",
        ))
        _assert_exec_called(session, "DELETE",
                            "/imaging/v2/policysets/570f9090-5dbe-11ec-8a0a-71665789c1d8",
                            headers=_STD_PS_HEADERS)

    def test_400_bad_request(self):
        """400 Bad request."""
        session = MagicMock()
        expected = ImagingError(
            type="https://problems.luna.akamaiapis.net/image-policy-manager/IVM_1004",
            title="Bad Request",
            instance="1a7387db-7056-4ae9-8cdf-5f23e0645487",
            status=400,
            detail="A contract must be specified using the ContractID header.",
            problem_id="1a7387db-7056-4ae9-8cdf-5f23e0645487",
        )
        _mock_exec_error(session, expected)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.delete_policy_set(DeletePolicySetRequest(
                policy_set_id="second",
                contract_id="3-WNKXX1",
            ))
        assert exc_info.value.status == 400

    def test_401_not_authorized(self):
        """401 Not authorized."""
        session = MagicMock()
        expected = ImagingError(
            type="https://problems.luna-dev.akamaiapis.net/-/pep-authn/deny",
            title="Not authorized",
            status=401,
            detail="Inactive client token",
            instance="https://akaa-p3wvjp6bqtotgpjh-fbk2vczjtq7b5l6a.luna-dev.akamaiapis.net/imaging/v2/policysets/058d9da0-7477-11ec-8a0a-71665789c1d8",
            method="DELETE",
            server_ip="104.81.220.242",
            client_ip="22.22.22.22",
            request_id="981a7be",
            request_time="2022-01-14T09:22:54Z",
        )
        _mock_exec_error(session, expected)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.delete_policy_set(DeletePolicySetRequest(
                policy_set_id="second",
                contract_id="3-WNKAA1",
            ))
        assert exc_info.value.status == 401

    def test_404_not_found(self):
        """404 Not found."""
        session = MagicMock()
        expected = ImagingError(
            type="https://problems.luna.akamaiapis.net/image-policy-manager/IVM_3001",
            title="Not Found",
            instance="3da0fcf0-4fb9-4b80-986c-4f9993436189",
            status=404,
            detail="That policy set does not exist.",
            problem_id="3da0fcf0-4fb9-4b80-986c-4f9993436189",
        )
        _mock_exec_error(session, expected)
        client = Client(session)
        with pytest.raises(ImagingError) as exc_info:
            client.delete_policy_set(DeletePolicySetRequest(
                policy_set_id="second",
                contract_id="3-WNKXX1",
            ))
        assert exc_info.value.status == 404

    def test_missing_policy_set_id(self):
        """Validation: missing PolicySetId."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.delete_policy_set(DeletePolicySetRequest(
                contract_id="3-WNKXX1",
            ))

    def test_missing_contract(self):
        """Validation: missing contract."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.delete_policy_set(DeletePolicySetRequest(
                policy_set_id="570f9090-5dbe-11ec-8a0a-71665789c1d8",
            ))

    def test_validation_error(self):
        """Validation: empty request."""
        session = MagicMock()
        client = Client(session)
        with pytest.raises(ErrStructValidation):
            client.delete_policy_set(DeletePolicySetRequest())
