# pylint: disable=missing-function-docstring,missing-class-docstring,too-many-lines
"""Unit tests for Domain Ownership Manager API client.

Mirrors all Go test scenarios from domainownership_test.go, domains_test.go,
errors_test.go, and validations_test.go.
"""

import json
from unittest.mock import MagicMock

import pytest

from akamai.edgegrid.domainownership.domainownership import Client
from akamai.edgegrid.domainownership import models
from akamai.edgegrid.domainownership import errors as err_mod


# ------------------------------------------------------------------ #
# Local helper – thin mock response builder (mirrors conftest utility)
# ------------------------------------------------------------------ #

def _mock_resp(status_code, body=""):
    """Return a ``MagicMock`` imitating an HTTP response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = body
    resp.headers = {}
    if body:
        try:
            resp.json.return_value = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            resp.json.side_effect = ValueError("No JSON")
    else:
        resp.json.side_effect = ValueError("No JSON")
    resp.content = body.encode("utf-8") if body else b""
    return resp


# ------------------------------------------------------------------ #
# TestClient – mirrors Go TestClient (domainownership_test.go:34-62)
# ------------------------------------------------------------------ #

class TestClient:
    """Test Client factory function."""

    def test_default_client(self, mock_session):
        client = Client(mock_session)
        assert client._session is mock_session  # pylint: disable=protected-access

    def test_client_stores_session(self):
        session = MagicMock()
        client = Client(session)
        assert client._session is session  # pylint: disable=protected-access


# ------------------------------------------------------------------ #
# TestNewError – mirrors Go TestNewError (errors_test.go:14-188)
# ------------------------------------------------------------------ #

class TestNewError:
    """Test error response parsing from HTTP responses."""

    def test_bad_request_400_missing_parameter(self, error_parser):
        body = (
            '{"detail": "Required parameter \'validationScope\' is missing.",'
            ' "status": 400, "title": "Bad Request", "type": "bad-request"}'
        )
        result = error_parser(400, body)
        expected = err_mod.Error(
            type="bad-request",
            title="Bad Request",
            detail="Required parameter 'validationScope' is missing.",
            status=400,
        )
        assert result == expected

    def test_bad_request_400_invalid_check(self, error_parser):
        body = json.dumps({
            "type": "bad-request",
            "title": "Bad Request",
            "instance": "d87ca377-f864-4054-bfa8-f567c44567c5",
            "status": 400,
            "detail":
                "Oops, something wasn't right. Please correct the errors.",
            "errors": [
                {
                    "type": "error-types/invalid",
                    "title": "Invalid Check",
                    "detail":
                        "Domain cannot be invalidated for the current state.",
                    "field": "domains[0].domainName",
                    "problemId": "d87ca377-f864-4054-bfa8-f567c44567c5",
                }
            ],
            "problemId": "d87ca377-f864-4054-bfa8-f567c44567c5",
        })
        result = error_parser(400, body)
        expected = err_mod.Error(
            type="bad-request",
            title="Bad Request",
            instance="d87ca377-f864-4054-bfa8-f567c44567c5",
            detail=(
                "Oops, something wasn't right. "
                "Please correct the errors."
            ),
            status=400,
            errors=[
                err_mod.ErrorDetail(
                    type="error-types/invalid",
                    title="Invalid Check",
                    detail=(
                        "Domain cannot be invalidated "
                        "for the current state."
                    ),
                    field="domains[0].domainName",
                    problem_id="d87ca377-f864-4054-bfa8-f567c44567c5",
                ),
            ],
            problem_id="d87ca377-f864-4054-bfa8-f567c44567c5",
        )
        assert result == expected

    def test_bad_request_400_invalid_value(self, error_parser):
        body = json.dumps({
            "type": "bad-request",
            "title": "Bad Request",
            "instance": "f5334872-80ae-437c-89ed-fee729f3a8de",
            "status": 400,
            "detail":
                "Invalid value 'a' for query parameter validationScope.",
            "errors": [
                {
                    "type": "error-types/invalid",
                    "title": "Invalid Value",
                    "detail":
                        "Invalid value 'a' for query parameter "
                        "validationScope.",
                    "field": "validationScope",
                    "problemId": "f5334872-80ae-437c-89ed-fee729f3a8de",
                }
            ],
            "problemId": "f5334872-80ae-437c-89ed-fee729f3a8de",
        })
        result = error_parser(400, body)
        expected = err_mod.Error(
            type="bad-request",
            title="Bad Request",
            instance="f5334872-80ae-437c-89ed-fee729f3a8de",
            detail=(
                "Invalid value 'a' for query parameter validationScope."
            ),
            status=400,
            errors=[
                err_mod.ErrorDetail(
                    type="error-types/invalid",
                    title="Invalid Value",
                    detail=(
                        "Invalid value 'a' for query parameter "
                        "validationScope."
                    ),
                    field="validationScope",
                    problem_id="f5334872-80ae-437c-89ed-fee729f3a8de",
                ),
            ],
            problem_id="f5334872-80ae-437c-89ed-fee729f3a8de",
        )
        assert result == expected

    def test_resource_not_found_404(self, error_parser):
        body = json.dumps({
            "type": "not-found",
            "title": "Not Found",
            "instance": "fe111e63-225d-45ea-8e0a-dd182496092d",
            "status": 404,
            "detail":
                "The requested resource could not be found on the server.",
            "field": "domainName",
            "value": "example.com",
        })
        result = error_parser(404, body)
        expected = err_mod.Error(
            title="Not Found",
            type="not-found",
            detail=(
                "The requested resource could not be found on the server."
            ),
            status=404,
            instance="fe111e63-225d-45ea-8e0a-dd182496092d",
        )
        assert result == expected

    def test_invalid_response_body_assign_status_code(self, error_parser):
        result = error_parser(500, "test")
        expected = err_mod.Error(
            title=(
                "Failed to unmarshal error body. Domain Ownership Manager"
                " API failed. Check details for more information."
            ),
            detail="test",
            status=500,
        )
        assert result == expected

    def test_empty_response_body_assign_status_code(self, error_parser):
        result = error_parser(500, "")
        expected = err_mod.Error(
            title=(
                "Failed to unmarshal error body. Domain Ownership Manager"
                " API failed. Check details for more information."
            ),
            detail="",
            status=500,
        )
        assert result == expected


# ------------------------------------------------------------------ #
# TestIs – mirrors Go TestIs (errors_test.go:191-224)
# ------------------------------------------------------------------ #

class TestIs:  # pylint: disable=too-few-public-methods
    """Test Error.is_equivalent() comparison semantics."""

    @pytest.mark.parametrize("name,error,target,expected", [
        (
            "different error code",
            err_mod.Error(status=404),
            err_mod.Error(status=401),
            False,
        ),
        (
            "same error code",
            err_mod.Error(status=404),
            err_mod.Error(status=404),
            True,
        ),
        (
            "same error code and title",
            err_mod.Error(status=404, title="some error"),
            err_mod.Error(status=404, title="some error"),
            True,
        ),
        (
            "same error code and different error message",
            err_mod.Error(status=404, title="some error"),
            err_mod.Error(status=404, title="other error"),
            False,
        ),
    ])
    def test_is_equivalent(self, name, error, target, expected):
        assert error.is_equivalent(target) == expected, name


# ------------------------------------------------------------------ #
# Reusable helper builders — keep test bodies concise
# ------------------------------------------------------------------ #

_EXPIRATION = "2025-08-05T13:27:19Z"


def _challenge_json(n, http_file=True, http_redirect=True):
    """Build challenge dict matching Go test fixture data for domain *n*."""
    obj = {
        "cnameRecord": {
            "name": f"cname-name-{n}", "target": f"cname-target-{n}",
        },
        "txtRecord": {
            "name": f"txt-name-{n}", "value": f"txt-value-{n}",
        },
    }
    if http_file:
        obj["httpFile"] = {
            "path": f"http-file-path-{n}",
            "content": f"http-file-content-{n}",
            "contentType": "text/plain",
        }
    if http_redirect:
        obj["httpRedirect"] = {
            "from": f"http-redirect-from-{n}",
            "to": f"http-redirect-to-{n}",
        }
    obj["expirationDate"] = _EXPIRATION
    return obj


def _expected_challenge(n, http_file=True, http_redirect=True):
    """Build expected ValidationChallenge model for domain *n*."""
    return models.ValidationChallenge(
        cname_record=models.CnameRecord(
            name=f"cname-name-{n}", target=f"cname-target-{n}",
        ),
        txt_record=models.TXTRecord(
            name=f"txt-name-{n}", value=f"txt-value-{n}",
        ),
        http_file=(
            models.HTTPFile(
                path=f"http-file-path-{n}",
                content=f"http-file-content-{n}",
                content_type="text/plain",
            )
            if http_file
            else None
        ),
        http_redirect=(
            models.HTTPRedirect(
                from_url=f"http-redirect-from-{n}",
                to=f"http-redirect-to-{n}",
            )
            if http_redirect
            else None
        ),
        expiration_date=_EXPIRATION,
    )


def _domain_json(n, scope="HOST", date="2025-08-04T13:27:19Z",
                  http_file=True, http_redirect=True):
    """Build domain JSON dict matching Go test fixture data."""
    return {
        "accountId": "1-ACCOUN",
        "domainName": f"dom{n}.test",
        "validationScope": scope,
        "domainStatus": "REQUEST_ACCEPTED",
        "validationRequestedBy": "someuser",
        "validationRequestedDate": date,
        "validationChallenge": _challenge_json(
            n, http_file, http_redirect,
        ),
    }


def _expected_domain_item(
    n, scope="HOST", date="2025-08-04T13:27:19Z",
    http_file=True, http_redirect=True,
):
    """Build expected DomainItem model for domain *n*."""
    return models.DomainItem(
        account_id="1-ACCOUN",
        domain_name=f"dom{n}.test",
        validation_scope=scope,
        domain_status="REQUEST_ACCEPTED",
        validation_requested_by="someuser",
        validation_requested_date=date,
        validation_challenge=_expected_challenge(
            n, http_file, http_redirect,
        ),
    )


_SELF_LINK_JSON = {
    "rel": "self",
    "href": "/domain-validation-service/api/v1/domains?page=1&pageSize=10",
}
_NEXT_LINK_JSON = {
    "rel": "next",
    "href": "/domain-validation-service/api/v1/domains?page=2&pageSize=10",
}
_SELF_LINK = models.Link(
    rel="self",
    href="/domain-validation-service/api/v1/domains?page=1&pageSize=10",
)
_NEXT_LINK = models.Link(
    rel="next",
    href="/domain-validation-service/api/v1/domains?page=2&pageSize=10",
)


def _single_domain_response_json():
    """Build 1-domain response JSON dict (reused across several tests)."""
    return {
        "metadata": {
            "hasPrevious": False,
            "hasNext": False,
            "page": 1,
            "pageSize": 10,
            "totalItems": 1,
        },
        "domains": [_domain_json(1)],
        "links": [_SELF_LINK_JSON],
    }


def _single_domain_expected():
    """Build expected 1-domain ListDomainsResponse."""
    return models.ListDomainsResponse(
        metadata=models.Metadata(
            has_previous=False,
            has_next=False,
            page=1,
            page_size=10,
            total_items=1,
        ),
        domains=[_expected_domain_item(1)],
        links=[_SELF_LINK],
    )


_500_BODY = json.dumps({
    "type": "internal_error",
    "title": "Internal Server Error",
    "detail": "Error making request",
    "status": 500,
})

_500_ERROR = err_mod.Error(
    type="internal_error",
    title="Internal Server Error",
    detail="Error making request",
    status=500,
)


# ------------------------------------------------------------------ #
# TestListDomains — mirrors Go TestListDomains (domains_test.go:18-1177)
# ------------------------------------------------------------------ #

class TestListDomains:
    """Test list_domains endpoint."""

    def test_200_no_args_multiple_results(self, mock_session):
        body = {
            "metadata": {
                "hasPrevious": False,
                "hasNext": True,
                "page": 1,
                "pageSize": 10,
                "totalItems": 11,
            },
            "domains": [
                _domain_json(1),
                _domain_json(
                    2, date="2025-08-04T13:26:58Z",
                    http_file=False, http_redirect=False,
                ),
                _domain_json(3, date="2025-08-04T13:26:50Z"),
                _domain_json(4, date="2025-08-04T13:26:50Z"),
                _domain_json(5, date="2025-08-04T13:26:50Z"),
                _domain_json(
                    6, scope="WILDCARD", date="2025-08-04T13:26:50Z",
                ),
                _domain_json(
                    7, scope="DOMAIN", date="2025-08-04T13:26:50Z",
                ),
                _domain_json(8, date="2025-08-04T13:26:29Z"),
                _domain_json(9, date="2025-08-04T13:26:29Z"),
                _domain_json(
                    10, scope="DOMAIN", date="2025-08-04T13:26:29Z",
                ),
            ],
            "links": [_SELF_LINK_JSON, _NEXT_LINK_JSON],
        }
        body_str = json.dumps(body)
        mock_session.get.return_value = (
            _mock_resp(200, body_str), body,
        )

        client = Client(mock_session)
        result = client.list_domains(models.ListDomainsRequest())

        mock_session.get.assert_called_once()
        call_args = mock_session.get.call_args
        assert call_args[0][0] == "/domain-validation/v1/domains"

        assert len(result.domains) == 10
        assert result.metadata == models.Metadata(
            has_previous=False, has_next=True,
            page=1, page_size=10, total_items=11,
        )
        assert result.links == [_SELF_LINK, _NEXT_LINK]

        # Verify each domain item
        assert result.domains[0] == _expected_domain_item(1)
        assert result.domains[1] == _expected_domain_item(
            2, date="2025-08-04T13:26:58Z",
            http_file=False, http_redirect=False,
        )
        assert result.domains[5] == _expected_domain_item(
            6, scope="WILDCARD", date="2025-08-04T13:26:50Z",
        )
        assert result.domains[6] == _expected_domain_item(
            7, scope="DOMAIN", date="2025-08-04T13:26:50Z",
        )
        assert result.domains[9] == _expected_domain_item(
            10, scope="DOMAIN", date="2025-08-04T13:26:29Z",
        )

    def test_200_explicit_page_and_page_size(self, mock_session):
        body = _single_domain_response_json()
        body_str = json.dumps(body)
        mock_session.get.return_value = (
            _mock_resp(200, body_str), body,
        )
        client = Client(mock_session)
        result = client.list_domains(
            models.ListDomainsRequest(page=1, page_size=10),
        )
        call_args = mock_session.get.call_args
        assert call_args[0][0] == "/domain-validation/v1/domains"
        assert call_args[1]["params"] == {
            "page": "1", "pageSize": "10",
        }
        assert result == _single_domain_expected()

    def test_200_explicit_paginate_page_and_page_size(self, mock_session):
        body = {
            "metadata": {
                "hasPrevious": False,
                "hasNext": False,
                "page": 1,
                "pageSize": 10,
                "totalItems": 1,
            },
            "domains": [
                _domain_json(9, date="2025-08-04T13:26:29Z"),
            ],
            "links": [_SELF_LINK_JSON],
        }
        body_str = json.dumps(body)
        mock_session.get.return_value = (
            _mock_resp(200, body_str), body,
        )
        client = Client(mock_session)
        result = client.list_domains(
            models.ListDomainsRequest(
                paginate=True, page=1, page_size=10,
            ),
        )
        params = mock_session.get.call_args[1]["params"]
        assert params["paginate"] == "true"
        assert params["page"] == "1"
        assert params["pageSize"] == "10"
        assert result.domains[0] == _expected_domain_item(
            9, date="2025-08-04T13:26:29Z",
        )

    def test_200_only_paginate(self, mock_session):
        body = _single_domain_response_json()
        body_str = json.dumps(body)
        mock_session.get.return_value = (
            _mock_resp(200, body_str), body,
        )
        client = Client(mock_session)
        result = client.list_domains(
            models.ListDomainsRequest(paginate=True),
        )
        params = mock_session.get.call_args[1]["params"]
        assert params == {"paginate": "true"}
        assert result == _single_domain_expected()

    def test_200_only_page_size(self, mock_session):
        body = _single_domain_response_json()
        body_str = json.dumps(body)
        mock_session.get.return_value = (
            _mock_resp(200, body_str), body,
        )
        client = Client(mock_session)
        result = client.list_domains(
            models.ListDomainsRequest(page_size=10),
        )
        params = mock_session.get.call_args[1]["params"]
        assert params == {"pageSize": "10"}
        assert result == _single_domain_expected()

    def test_200_only_page(self, mock_session):
        body = _single_domain_response_json()
        body_str = json.dumps(body)
        mock_session.get.return_value = (
            _mock_resp(200, body_str), body,
        )
        client = Client(mock_session)
        result = client.list_domains(
            models.ListDomainsRequest(page=1),
        )
        params = mock_session.get.call_args[1]["params"]
        assert params == {"page": "1"}
        assert result == _single_domain_expected()

    def test_validation_page_or_page_size_without_paging(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.list_domains(
                models.ListDomainsRequest(
                    paginate=False, page=1, page_size=10,
                ),
            )
        assert str(exc_info.value) == (
            "list domains: struct validation:\n"
            "Page: must be 0 when Paginate is false\n"
            "PageSize: must be 0 when Paginate is false"
        )

    def test_validation_page_size_too_small(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.list_domains(
                models.ListDomainsRequest(page_size=1),
            )
        assert str(exc_info.value) == (
            "list domains: struct validation:\n"
            "PageSize: must be no less than 10"
        )

    def test_validation_page_size_too_big(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.list_domains(
                models.ListDomainsRequest(page_size=1001),
            )
        assert str(exc_info.value) == (
            "list domains: struct validation:\n"
            "PageSize: must be no greater than 1000"
        )

    def test_500_internal_server_error(self, mock_session):
        mock_session.get.return_value = (
            _mock_resp(500, _500_BODY), None,
        )
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.list_domains(models.ListDomainsRequest())
        assert _500_ERROR.is_equivalent(exc_info.value)


# ------------------------------------------------------------------ #
# TestGetDomain — mirrors Go TestGetDomain (domains_test.go:1179-1501)  7 cases
# ------------------------------------------------------------------ #

class TestGetDomain:
    """Test get_domain endpoint. 7 cases."""

    def _get_domain_body(self):
        """Shared base body dict for not-validated dom1 response."""
        return {
            "accountId": "1-ACCOUN",
            "domainName": "dom1.test",
            "validationScope": "HOST",
            "domainStatus": "REQUEST_ACCEPTED",
            "validationRequestedBy": "someuser",
            "validationRequestedDate": "2025-08-04T13:27:19Z",
            "validationChallenge": _challenge_json(1),
        }

    def _get_domain_expected(self):
        """Shared expected response for not-validated dom1."""
        return models.GetDomainResponse(
            account_id="1-ACCOUN",
            domain_name="dom1.test",
            validation_scope="HOST",
            domain_status="REQUEST_ACCEPTED",
            validation_requested_by="someuser",
            validation_requested_date="2025-08-04T13:27:19Z",
            validation_challenge=_expected_challenge(1),
        )

    def test_200_only_required_args_not_validated(self, mock_session):
        body = self._get_domain_body()
        body_str = json.dumps(body)
        mock_session.get.return_value = (
            _mock_resp(200, body_str), body,
        )
        client = Client(mock_session)
        result = client.get_domain(
            models.GetDomainRequest(
                domain_name="dom1.test",
                validation_scope=models.VALIDATION_SCOPE_HOST,
            ),
        )
        call_args = mock_session.get.call_args
        assert call_args[0][0] == (
            "/domain-validation/v1/domains/dom1.test"
        )
        assert call_args[1]["params"]["validationScope"] == "HOST"
        assert result == self._get_domain_expected()

    def test_200_not_validated_minimal_challenges(self, mock_session):
        body = self._get_domain_body()
        body_str = json.dumps(body)
        mock_session.get.return_value = (
            _mock_resp(200, body_str), body,
        )
        client = Client(mock_session)
        result = client.get_domain(
            models.GetDomainRequest(
                domain_name="dom1.test",
                validation_scope=models.VALIDATION_SCOPE_HOST,
            ),
        )
        assert result == self._get_domain_expected()

    def test_200_with_status_history_not_validated(self, mock_session):
        body = {
            "accountId": "1-ACCOUN",
            "domainName": "dom1.test",
            "validationScope": "HOST",
            "domainStatus": "VALIDATION_IN_PROGRESS",
            "validationRequestedBy": "someuser",
            "validationRequestedDate": "2025-08-04T13:27:19Z",
            "validationChallenge": _challenge_json(1),
            "domainStatusHistory": [
                {
                    "domainStatus": "REQUEST_ACCEPTED",
                    "modifiedUser": "someuser",
                    "modifiedDate": "2025-08-04T11:49:53Z",
                },
                {
                    "domainStatus": "VALIDATION_IN_PROGRESS",
                    "message": "DNS verification failed.",
                    "modifiedUser": "someuser",
                    "modifiedDate": "2025-08-04T11:50:53Z",
                },
            ],
        }
        body_str = json.dumps(body)
        mock_session.get.return_value = (
            _mock_resp(200, body_str), body,
        )
        client = Client(mock_session)
        result = client.get_domain(
            models.GetDomainRequest(
                domain_name="dom1.test",
                validation_scope=models.VALIDATION_SCOPE_HOST,
                include_domain_status_history=True,
            ),
        )
        params = mock_session.get.call_args[1]["params"]
        assert params["includeDomainStatusHistory"] == "true"
        assert params["validationScope"] == "HOST"

        assert result.domain_status == "VALIDATION_IN_PROGRESS"
        assert len(result.domain_status_history) == 2
        assert result.domain_status_history[0] == (
            models.DomainStatusHistory(
                domain_status="REQUEST_ACCEPTED",
                modified_user="someuser",
                modified_date="2025-08-04T11:49:53Z",
            )
        )
        assert result.domain_status_history[1] == (
            models.DomainStatusHistory(
                domain_status="VALIDATION_IN_PROGRESS",
                message="DNS verification failed.",
                modified_user="someuser",
                modified_date="2025-08-04T11:50:53Z",
            )
        )

    def test_200_validated(self, mock_session):
        body = {
            "accountId": "1-ACCOUN",
            "domainName": "dom1.test",
            "validationScope": "HOST",
            "domainStatus": "VALIDATED",
            "validationMethod": "SYSTEM",
            "validationRequestedBy": "someuser",
            "validationRequestedDate": "2025-08-04T13:27:19Z",
            "validationCompletedDate": "2025-08-05T11:56:07Z",
        }
        body_str = json.dumps(body)
        mock_session.get.return_value = (
            _mock_resp(200, body_str), body,
        )
        client = Client(mock_session)
        result = client.get_domain(
            models.GetDomainRequest(
                domain_name="dom1.test",
                validation_scope=models.VALIDATION_SCOPE_HOST,
            ),
        )
        assert result.domain_status == "VALIDATED"
        assert result.validation_method == "SYSTEM"
        assert result.validation_completed_date == (
            "2025-08-05T11:56:07Z"
        )
        assert result.validation_challenge is None

    def test_validation_no_arguments(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.get_domain(models.GetDomainRequest())
        assert str(exc_info.value) == (
            "get domain: struct validation:\n"
            "DomainName: cannot be blank\n"
            "ValidationScope: cannot be blank"
        )

    def test_validation_incorrect_scope(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.get_domain(
                models.GetDomainRequest(
                    domain_name="dom1.test",
                    validation_scope="incorrect",
                ),
            )
        assert str(exc_info.value) == (
            "get domain: struct validation:\n"
            "ValidationScope: value 'incorrect' is invalid. "
            "Must be one of: 'HOST', 'DOMAIN' or 'WILDCARD'"
        )

    def test_500_internal_server_error(self, mock_session):
        mock_session.get.return_value = (
            _mock_resp(500, _500_BODY), None,
        )
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.get_domain(
                models.GetDomainRequest(
                    domain_name="dom1.test",
                    validation_scope=models.VALIDATION_SCOPE_DOMAIN,
                ),
            )
        assert _500_ERROR.is_equivalent(exc_info.value)


# ------------------------------------------------------------------ #
# TestSearchDomains — mirrors Go TestSearchDomains
# (domains_test.go:1503-1760) — 6 cases
# ------------------------------------------------------------------ #

class TestSearchDomains:
    """Test search_domains endpoint."""

    def test_200_without_details(self, mock_session):
        body = {
            "domains": [
                {
                    "domainName": "dom1.test",
                    "validationScope": "HOST",
                    "domainStatus": "REQUEST_ACCEPTED",
                    "validationLevel": "FQDN",
                },
                {
                    "domainName": "dom2.test",
                    "validationScope": "HOST",
                    "domainStatus": "VALIDATED",
                    "validationLevel": "FQDN",
                },
            ],
        }
        body_str = json.dumps(body)
        mock_session.post.return_value = (
            _mock_resp(200, body_str), body,
        )
        client = Client(mock_session)
        result = client.search_domains(
            models.SearchDomainsRequest(
                body=models.SearchDomainsBody(
                    domains=[
                        models.Domain(
                            domain_name="dom1.test",
                            validation_scope=models.VALIDATION_SCOPE_HOST,
                        ),
                        models.Domain(
                            domain_name="dom2.test",
                            validation_scope=(
                                models.VALIDATION_SCOPE_DOMAIN
                            ),
                        ),
                    ],
                ),
            ),
        )
        call_args = mock_session.post.call_args
        assert call_args[0][0] == (
            "/domain-validation/v1/domains/search"
        )
        assert result == models.SearchDomainsResponse(
            domains=[
                models.SearchDomainItem(
                    domain_name="dom1.test",
                    validation_scope="HOST",
                    domain_status="REQUEST_ACCEPTED",
                    validation_level="FQDN",
                ),
                models.SearchDomainItem(
                    domain_name="dom2.test",
                    validation_scope="HOST",
                    domain_status="VALIDATED",
                    validation_level="FQDN",
                ),
            ],
        )

    def test_200_with_details(self, mock_session):
        body = {
            "domains": [
                {
                    "accountId": "1-ACCOUN",
                    "domainName": "dom1.test",
                    "validationScope": "HOST",
                    "domainStatus": "REQUEST_ACCEPTED",
                    "validationLevel": "FQDN",
                    "validationMethod": "DNS_TXT",
                    "validationRequestedBy": "someuser",
                    "validationRequestedDate": "2025-08-04T13:27:19Z",
                    "validationChallenge": _challenge_json(1),
                },
                {
                    "accountId": "1-ACCOUN",
                    "domainName": "dom2.test",
                    "validationScope": "HOST",
                    "domainStatus": "VALIDATED",
                    "validationLevel": "FQDN",
                    "validationMethod": "SYSTEM",
                    "validationRequestedBy": "someuser",
                    "validationRequestedDate": "2025-08-04T13:27:19Z",
                    "validationCompletedDate": "2025-08-05T11:56:07Z",
                },
            ],
        }
        body_str = json.dumps(body)
        mock_session.post.return_value = (
            _mock_resp(200, body_str), body,
        )
        client = Client(mock_session)
        result = client.search_domains(
            models.SearchDomainsRequest(
                include_all=True,
                body=models.SearchDomainsBody(
                    domains=[
                        models.Domain(
                            domain_name="dom1.test",
                            validation_scope=models.VALIDATION_SCOPE_HOST,
                        ),
                        models.Domain(
                            domain_name="dom2.test",
                            validation_scope=(
                                models.VALIDATION_SCOPE_DOMAIN
                            ),
                        ),
                    ],
                ),
            ),
        )
        params = mock_session.post.call_args[1].get("params", {})
        assert params.get("includeAll") == "true"

        dom1 = result.domains[0]
        assert dom1.account_id == "1-ACCOUN"
        assert dom1.validation_method == "DNS_TXT"
        assert dom1.validation_requested_by == "someuser"
        assert dom1.validation_requested_date == (
            "2025-08-04T13:27:19Z"
        )
        assert dom1.validation_challenge == _expected_challenge(1)

        dom2 = result.domains[1]
        assert dom2.domain_status == "VALIDATED"
        assert dom2.validation_method == "SYSTEM"
        assert dom2.validation_completed_date == (
            "2025-08-05T11:56:07Z"
        )

    def test_validation_no_arguments(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.search_domains(models.SearchDomainsRequest())
        assert str(exc_info.value) == (
            "search domains: struct validation:\n"
            "Body: {\n"
            "\tDomains: cannot be blank\n"
            "}"
        )

    def test_validation_empty_domain(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.search_domains(
                models.SearchDomainsRequest(
                    body=models.SearchDomainsBody(
                        domains=[models.Domain()],
                    ),
                ),
            )
        assert str(exc_info.value) == (
            "search domains: struct validation:\n"
            "Body: {\n"
            "\tDomains[0]: {\n"
            "\t\tDomainName: cannot be blank\n"
            "\t\tValidationScope: cannot be blank\n"
            "\t}\n"
            "}"
        )

    def test_validation_incorrect_scope(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.search_domains(
                models.SearchDomainsRequest(
                    body=models.SearchDomainsBody(
                        domains=[
                            models.Domain(
                                domain_name="dom1.test",
                                validation_scope="incorrect",
                            ),
                        ],
                    ),
                ),
            )
        assert str(exc_info.value) == (
            "search domains: struct validation:\n"
            "Body: {\n"
            "\tDomains[0]: {\n"
            "\t\tValidationScope: value 'incorrect' is invalid. "
            "Must be one of: 'HOST', 'DOMAIN' or 'WILDCARD'\n"
            "\t}\n"
            "}"
        )

    def test_500_internal_server_error(self, mock_session):
        mock_session.post.return_value = (
            _mock_resp(500, _500_BODY), None,
        )
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.search_domains(
                models.SearchDomainsRequest(
                    body=models.SearchDomainsBody(
                        domains=[
                            models.Domain(
                                domain_name="dom1.test",
                                validation_scope=(
                                    models.VALIDATION_SCOPE_DOMAIN
                                ),
                            ),
                        ],
                    ),
                ),
            )
        assert _500_ERROR.is_equivalent(exc_info.value)


# ------------------------------------------------------------------ #
# TestAddDomains — mirrors Go TestAddDomains
# (domains_test.go:1762-2261) — 10 cases
# ------------------------------------------------------------------ #

_ADD_CHALLENGE_JSON_1 = {
    "cnameRecord": {
        "name": "cname-name-1",
        "target": "cname-target-1",
    },
    "txtRecord": {
        "name": "txt-name-1",
        "value": "txt-value-1",
    },
    "httpFile": {
        "path": "http-file-path-1",
        "content": "http-file-content-1",
        "contentType": "text/plain",
    },
    "httpRedirect": {
        "from": "http-redirect-from-1",
        "to": "http-redirect-to-1",
    },
    "expirationDate": "2025-08-05T13:27:19Z",
}

_ADD_CHALLENGE_JSON_2 = {
    "cnameRecord": {
        "name": "cname-name-2",
        "target": "cname-target-2",
    },
    "txtRecord": {
        "name": "txt-name-2",
        "value": "txt-value-2",
    },
    "httpFile": {
        "path": "http-file-path-2",
        "content": "http-file-content-2",
        "contentType": "text/plain",
    },
    "httpRedirect": {
        "from": "http-redirect-from-2",
        "to": "http-redirect-to-2",
    },
    "expirationDate": "2025-08-05T13:27:19Z",
}

_ADD_EXPECTED_CHALLENGE_1 = models.ValidationChallenge(
    cname_record=models.CnameRecord(
        name="cname-name-1", target="cname-target-1",
    ),
    txt_record=models.TXTRecord(
        name="txt-name-1", value="txt-value-1",
    ),
    http_file=models.HTTPFile(
        path="http-file-path-1",
        content="http-file-content-1",
        content_type="text/plain",
    ),
    http_redirect=models.HTTPRedirect(
        from_url="http-redirect-from-1",
        to="http-redirect-to-1",
    ),
    expiration_date="2025-08-05T13:27:19Z",
)

_ADD_EXPECTED_CHALLENGE_2 = models.ValidationChallenge(
    cname_record=models.CnameRecord(
        name="cname-name-2", target="cname-target-2",
    ),
    txt_record=models.TXTRecord(
        name="txt-name-2", value="txt-value-2",
    ),
    http_file=models.HTTPFile(
        path="http-file-path-2",
        content="http-file-content-2",
        content_type="text/plain",
    ),
    http_redirect=models.HTTPRedirect(
        from_url="http-redirect-from-2",
        to="http-redirect-to-2",
    ),
    expiration_date="2025-08-05T13:27:19Z",
)

_ADD_HINT = (
    "Hint: Domain must: not be empty, not begin with '*', "
    "not begin or end with whitespace, and not exceed 200 "
    "characters"
)


class TestAddDomains:
    """Test add_domains endpoint. Mirrors Go TestAddDomains."""

    def test_207_all_success(self, mock_session):
        body = {
            "errors": [],
            "successes": [
                {
                    "domainName": "sample1.com",
                    "domainStatus": "REQUEST_ACCEPTED",
                    "accountId": "A-CCT5678",
                    "validationScope": "HOST",
                    "validationMethod": "DNS_TXT",
                    "validationRequestedBy": "someone",
                    "validationRequestedDate": (
                        "2024-02-06T06:01:45Z"
                    ),
                    "validationChallenge": _ADD_CHALLENGE_JSON_1,
                },
                {
                    "domainName": "sample2.com",
                    "domainStatus": "REQUEST_ACCEPTED",
                    "accountId": "A-CCT7890",
                    "validationScope": "HOST",
                    "validationRequestedBy": "someone",
                    "validationRequestedDate": (
                        "2024-02-06T06:01:45Z"
                    ),
                    "validationChallenge": _ADD_CHALLENGE_JSON_2,
                },
            ],
        }
        body_str = json.dumps(body)
        mock_session.post.return_value = (
            _mock_resp(207, body_str), body,
        )
        client = Client(mock_session)
        result = client.add_domains(
            models.AddDomainsRequest(
                domains=[
                    models.Domain(
                        domain_name="sample1.com",
                        validation_scope=(
                            models.VALIDATION_SCOPE_HOST
                        ),
                    ),
                    models.Domain(
                        domain_name="sample2.com",
                        validation_scope=(
                            models.VALIDATION_SCOPE_HOST
                        ),
                    ),
                ],
            ),
        )
        assert isinstance(result, models.AddDomainsResponse)
        assert not result.errors
        assert len(result.successes) == 2

        s1 = result.successes[0]
        assert isinstance(s1, models.AddDomainSuccess)
        assert s1.domain_name == "sample1.com"
        assert s1.domain_status == "REQUEST_ACCEPTED"
        assert s1.account_id == "A-CCT5678"
        assert s1.validation_scope == "HOST"
        assert s1.validation_method == "DNS_TXT"
        assert s1.validation_requested_by == "someone"
        assert s1.validation_requested_date == (
            "2024-02-06T06:01:45Z"
        )
        assert s1.validation_challenge == _ADD_EXPECTED_CHALLENGE_1

        s2 = result.successes[1]
        assert s2.domain_name == "sample2.com"
        assert s2.domain_status == "REQUEST_ACCEPTED"
        assert s2.account_id == "A-CCT7890"
        assert s2.validation_scope == "HOST"
        assert s2.validation_requested_by == "someone"
        assert s2.validation_requested_date == (
            "2024-02-06T06:01:45Z"
        )
        assert s2.validation_challenge == _ADD_EXPECTED_CHALLENGE_2

    def test_207_partial_success(self, mock_session):
        body = {
            "errors": [
                {
                    "domainName": "sample3.com",
                    "detail": "Domain already exists.",
                    "title": "Internal Server Error",
                    "type": "internal-server-error",
                    "validationScope": "HOST",
                },
                {
                    "domainName": "sample4.com",
                    "detail": (
                        "Supernet domain has been validated "
                        "and is ready for use."
                    ),
                    "title": "Internal Server Error",
                    "type": "internal-server-error",
                    "validationScope": "HOST",
                },
                {
                    "domainName": "sample5.com",
                    "detail": (
                        "Domain is already in use within the "
                        "system. You cannot use this domain."
                    ),
                    "title": "Internal Server Error",
                    "type": "internal-server-error",
                    "validationScope": "HOST",
                },
            ],
            "successes": [
                {
                    "domainName": "sample1.com",
                    "domainStatus": "REQUEST_ACCEPTED",
                    "accountId": "A-CCT5678",
                    "validationScope": "HOST",
                    "validationMethod": "DNS_TXT",
                    "validationRequestedBy": "someone",
                    "validationRequestedDate": (
                        "2024-02-06T06:01:45Z"
                    ),
                    "validationChallenge": _ADD_CHALLENGE_JSON_1,
                },
                {
                    "domainName": "sample2.com",
                    "domainStatus": "REQUEST_ACCEPTED",
                    "accountId": "A-CCT7890",
                    "validationScope": "HOST",
                    "validationRequestedBy": "someone",
                    "validationRequestedDate": (
                        "2024-02-06T06:01:45Z"
                    ),
                    "validationChallenge": _ADD_CHALLENGE_JSON_2,
                },
            ],
        }
        body_str = json.dumps(body)
        mock_session.post.return_value = (
            _mock_resp(207, body_str), body,
        )
        client = Client(mock_session)
        result = client.add_domains(
            models.AddDomainsRequest(
                domains=[
                    models.Domain(
                        domain_name="sample1.com",
                        validation_scope=(
                            models.VALIDATION_SCOPE_HOST
                        ),
                    ),
                    models.Domain(
                        domain_name="sample2.com",
                        validation_scope=(
                            models.VALIDATION_SCOPE_HOST
                        ),
                    ),
                    models.Domain(
                        domain_name="sample3.com",
                        validation_scope=(
                            models.VALIDATION_SCOPE_HOST
                        ),
                    ),
                    models.Domain(
                        domain_name="sample4.com",
                        validation_scope=(
                            models.VALIDATION_SCOPE_HOST
                        ),
                    ),
                    models.Domain(
                        domain_name="sample5.com",
                        validation_scope=(
                            models.VALIDATION_SCOPE_HOST
                        ),
                    ),
                ],
            ),
        )
        assert len(result.errors) == 3
        assert result.errors[0] == models.AddDomainError(
            domain_name="sample3.com",
            detail="Domain already exists.",
            title="Internal Server Error",
            type="internal-server-error",
            validation_scope="HOST",
        )
        assert result.errors[1] == models.AddDomainError(
            domain_name="sample4.com",
            detail=(
                "Supernet domain has been validated "
                "and is ready for use."
            ),
            title="Internal Server Error",
            type="internal-server-error",
            validation_scope="HOST",
        )
        assert result.errors[2] == models.AddDomainError(
            domain_name="sample5.com",
            detail=(
                "Domain is already in use within the "
                "system. You cannot use this domain."
            ),
            title="Internal Server Error",
            type="internal-server-error",
            validation_scope="HOST",
        )
        assert len(result.successes) == 2
        assert result.successes[0].domain_name == "sample1.com"
        assert result.successes[1].domain_name == "sample2.com"

    def test_validation_empty_domain(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.add_domains(
                models.AddDomainsRequest(domains=[]),
            )
        assert str(exc_info.value) == (
            "add domains: struct validation:\n"
            "Domains: cannot be blank"
        )

    def test_validation_domain_name_not_supplied(
        self, mock_session,
    ):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.add_domains(
                models.AddDomainsRequest(
                    domains=[
                        models.Domain(
                            domain_name="sample1.com",
                            validation_scope=(
                                models.VALIDATION_SCOPE_HOST
                            ),
                        ),
                        models.Domain(
                            validation_scope=(
                                models.VALIDATION_SCOPE_HOST
                            ),
                        ),
                    ],
                ),
            )
        assert str(exc_info.value) == (
            "add domains: struct validation:\n"
            "Domains[1]: {\n"
            "\tDomainName: cannot be blank\n"
            "}\n"
            + _ADD_HINT
        )

    def test_validation_scope_not_supplied(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.add_domains(
                models.AddDomainsRequest(
                    domains=[
                        models.Domain(
                            domain_name="sample1.com",
                        ),
                    ],
                ),
            )
        assert str(exc_info.value) == (
            "add domains: struct validation:\n"
            "Domains[0]: {\n"
            "\tValidationScope: cannot be blank\n"
            "}"
        )

    def test_validation_domain_name_starts_with_star(
        self, mock_session,
    ):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.add_domains(
                models.AddDomainsRequest(
                    domains=[
                        models.Domain(
                            domain_name="*sample1.com",
                            validation_scope=(
                                models.VALIDATION_SCOPE_HOST
                            ),
                        ),
                    ],
                ),
            )
        assert str(exc_info.value) == (
            "add domains: struct validation:\n"
            "Domains[0]: {\n"
            "\tDomainName: domain '*sample1.com': "
            "invalid name format\n"
            "}\n"
            + _ADD_HINT
        )

    def test_validation_domain_name_bad_format(
        self, mock_session,
    ):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.add_domains(
                models.AddDomainsRequest(
                    domains=[
                        models.Domain(
                            domain_name="*example.com",
                            validation_scope=(
                                models.VALIDATION_SCOPE_HOST
                            ),
                        ),
                    ],
                ),
            )
        assert str(exc_info.value) == (
            "add domains: struct validation:\n"
            "Domains[0]: {\n"
            "\tDomainName: domain '*example.com': "
            "invalid name format\n"
            "}\n"
            + _ADD_HINT
        )

    def test_validation_domain_name_greater_than_200(
        self, mock_session,
    ):
        long_name = "sample1.com" + "a" * 190
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.add_domains(
                models.AddDomainsRequest(
                    domains=[
                        models.Domain(
                            domain_name=long_name,
                            validation_scope=(
                                models.VALIDATION_SCOPE_HOST
                            ),
                        ),
                    ],
                ),
            )
        assert str(exc_info.value) == (
            "add domains: struct validation:\n"
            "Domains[0]: {\n"
            f"\tDomainName: domain '{long_name}': "
            "cannot exceed 200 characters\n"
            "}\n"
            + _ADD_HINT
        )

    def test_validation_incorrect_scope(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.add_domains(
                models.AddDomainsRequest(
                    domains=[
                        models.Domain(
                            domain_name="sample1.com",
                            validation_scope="incorrect",
                        ),
                        models.Domain(
                            domain_name="sample2.com",
                            validation_scope=(
                                models.VALIDATION_SCOPE_HOST
                            ),
                        ),
                    ],
                ),
            )
        assert str(exc_info.value) == (
            "add domains: struct validation:\n"
            "Domains[0]: {\n"
            "\tValidationScope: value 'incorrect' is invalid. "
            "Must be one of: 'HOST', 'DOMAIN' or 'WILDCARD'\n"
            "}"
        )

    def test_500_internal_server_error(self, mock_session):
        mock_session.post.return_value = (
            _mock_resp(500, _500_BODY), None,
        )
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.add_domains(
                models.AddDomainsRequest(
                    domains=[
                        models.Domain(
                            domain_name="sample1.com",
                            validation_scope=(
                                models.VALIDATION_SCOPE_DOMAIN
                            ),
                        ),
                    ],
                ),
            )
        assert _500_ERROR.is_equivalent(exc_info.value)


# ------------------------------------------------------------------ #
# TestDeleteDomain — mirrors Go TestDeleteDomain
# (domains_test.go:2263-2381) — 6 cases
# ------------------------------------------------------------------ #


class TestDeleteDomain:
    """Test delete_domain endpoint. Mirrors Go TestDeleteDomain."""

    def test_200_ok(self, mock_session):
        mock_session.delete.return_value = (
            _mock_resp(204, ""), None,
        )
        client = Client(mock_session)
        client.delete_domain(
            models.DeleteDomainRequest(
                domain_name="sample1.com",
                validation_scope=models.VALIDATION_SCOPE_HOST,
            ),
        )
        call_args = mock_session.delete.call_args
        assert "/domain-validation/v1/domains/sample1.com" in (
            call_args[0][0]
        )

    def test_validation_errors_both_blank(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.delete_domain(models.DeleteDomainRequest())
        assert str(exc_info.value) == (
            "delete domain: struct validation:\n"
            "DomainName: cannot be blank\n"
            "ValidationScope: cannot be blank"
        )

    def test_validation_errors_domain_name_missing(
        self, mock_session,
    ):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.delete_domain(
                models.DeleteDomainRequest(
                    validation_scope=(
                        models.VALIDATION_SCOPE_HOST
                    ),
                ),
            )
        assert str(exc_info.value) == (
            "delete domain: struct validation:\n"
            "DomainName: cannot be blank"
        )

    def test_validation_errors_scope_missing(
        self, mock_session,
    ):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.delete_domain(
                models.DeleteDomainRequest(
                    domain_name="sample1.com",
                ),
            )
        assert str(exc_info.value) == (
            "delete domain: struct validation:\n"
            "ValidationScope: cannot be blank"
        )

    def test_404_not_found(self, mock_session):
        error_body = json.dumps({
            "detail": "Domain is not found.",
            "instance": "55f55b02-bfac-4654-91f6-f72626839bb3",
            "status": 404,
            "title": "Not Found",
            "type": "not-found",
        })
        mock_session.delete.return_value = (
            _mock_resp(404, error_body), None,
        )
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.delete_domain(
                models.DeleteDomainRequest(
                    domain_name="sample1.com",
                    validation_scope=(
                        models.VALIDATION_SCOPE_HOST
                    ),
                ),
            )
        want = err_mod.Error(
            title="Not Found",
            type="not-found",
            status=404,
            instance=(
                "55f55b02-bfac-4654-91f6-f72626839bb3"
            ),
            detail="Domain is not found.",
        )
        assert want.is_equivalent(exc_info.value)

    def test_500_internal_server_error(self, mock_session):
        mock_session.delete.return_value = (
            _mock_resp(500, _500_BODY), None,
        )
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.delete_domain(
                models.DeleteDomainRequest(
                    domain_name="sample1.com",
                    validation_scope=(
                        models.VALIDATION_SCOPE_HOST
                    ),
                ),
            )
        assert _500_ERROR.is_equivalent(exc_info.value)


# ------------------------------------------------------------------ #
# TestDeleteDomains — mirrors Go TestDeleteDomains
# (domains_test.go:2383-2572) — 9 cases
# NOTE: delete_domains uses colon-SPACE (not colon-newline) for
# validation error format.
# ------------------------------------------------------------------ #


class TestDeleteDomains:
    """Test delete_domains endpoint. Mirrors Go TestDeleteDomains."""

    def test_200_ok(self, mock_session):
        mock_session.delete.return_value = (
            _mock_resp(204, ""), None,
        )
        client = Client(mock_session)
        client.delete_domains(
            models.DeleteDomainsRequest(
                domains=[
                    models.Domain(
                        domain_name="sample1.com",
                        validation_scope=(
                            models.VALIDATION_SCOPE_HOST
                        ),
                    ),
                ],
            ),
        )
        call_args = mock_session.delete.call_args
        assert call_args[0][0] == (
            "/domain-validation/v1/domains"
        )

    def test_validation_errors_empty_params(
        self, mock_session,
    ):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.delete_domains(
                models.DeleteDomainsRequest(),
            )
        assert str(exc_info.value) == (
            "delete domains: struct validation: "
            "Domains: cannot be blank"
        )

    def test_validation_errors_empty_domains(
        self, mock_session,
    ):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.delete_domains(
                models.DeleteDomainsRequest(domains=[]),
            )
        assert str(exc_info.value) == (
            "delete domains: struct validation: "
            "Domains: cannot be blank"
        )

    def test_validation_errors_empty_domain(
        self, mock_session,
    ):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.delete_domains(
                models.DeleteDomainsRequest(
                    domains=[models.Domain()],
                ),
            )
        assert str(exc_info.value) == (
            "delete domains: struct validation: "
            "Domains[0]: {\n"
            "\tDomainName: cannot be blank\n"
            "\tValidationScope: cannot be blank\n"
            "}"
        )

    def test_validation_errors_domain_name_missing(
        self, mock_session,
    ):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.delete_domains(
                models.DeleteDomainsRequest(
                    domains=[
                        models.Domain(
                            validation_scope=(
                                models.VALIDATION_SCOPE_HOST
                            ),
                        ),
                    ],
                ),
            )
        assert str(exc_info.value) == (
            "delete domains: struct validation: "
            "Domains[0]: {\n"
            "\tDomainName: cannot be blank\n"
            "}"
        )

    def test_validation_errors_scope_missing(
        self, mock_session,
    ):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.delete_domains(
                models.DeleteDomainsRequest(
                    domains=[
                        models.Domain(
                            domain_name="sample1.com",
                        ),
                    ],
                ),
            )
        assert str(exc_info.value) == (
            "delete domains: struct validation: "
            "Domains[0]: {\n"
            "\tValidationScope: cannot be blank\n"
            "}"
        )

    def test_validation_errors_invalid_scope(
        self, mock_session,
    ):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.delete_domains(
                models.DeleteDomainsRequest(
                    domains=[
                        models.Domain(
                            domain_name="sample1.com",
                            validation_scope="foo",
                        ),
                    ],
                ),
            )
        assert str(exc_info.value) == (
            "delete domains: struct validation: "
            "Domains[0]: {\n"
            "\tValidationScope: value 'foo' is invalid. "
            "Must be one of: 'HOST', 'DOMAIN' or 'WILDCARD'\n"
            "}"
        )

    def test_400_domain_not_found(self, mock_session):
        error_body = json.dumps({
            "type": "bad-request",
            "title": "Bad Request",
            "instance": "12345-c988-463e-9382-6c15e80868c0",
            "status": 400,
            "detail": (
                "Oops, something wasn't right. "
                "Please correct the errors."
            ),
            "errors": [
                {
                    "type": "error-types/invalid",
                    "title": "Invalid Check",
                    "detail": "Domain is not found.",
                    "problemId": (
                        "0030b473-0bd9-40eb-8afa-d6a08c9be687"
                    ),
                    "field": "domains[0].domainName",
                },
            ],
            "problemId": (
                "85588d59-c988-463e-9382-6c15e80868c0"
            ),
        })
        mock_session.delete.return_value = (
            _mock_resp(400, error_body), None,
        )
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.delete_domains(
                models.DeleteDomainsRequest(
                    domains=[
                        models.Domain(
                            domain_name="sample1.com",
                            validation_scope=(
                                models.VALIDATION_SCOPE_HOST
                            ),
                        ),
                    ],
                ),
            )
        want = err_mod.Error(
            title="Bad Request",
            type="bad-request",
            status=400,
            instance=(
                "12345-c988-463e-9382-6c15e80868c0"
            ),
            detail=(
                "Oops, something wasn't right. "
                "Please correct the errors."
            ),
            problem_id=(
                "85588d59-c988-463e-9382-6c15e80868c0"
            ),
            errors=[
                err_mod.ErrorDetail(
                    type="error-types/invalid",
                    title="Invalid Check",
                    detail="Domain is not found.",
                    problem_id=(
                        "0030b473-0bd9-40eb-8afa-"
                        "d6a08c9be687"
                    ),
                    field="domains[0].domainName",
                ),
            ],
        )
        assert want.is_equivalent(exc_info.value)

    def test_500_internal_server_error(self, mock_session):
        mock_session.delete.return_value = (
            _mock_resp(500, _500_BODY), None,
        )
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.delete_domains(
                models.DeleteDomainsRequest(
                    domains=[
                        models.Domain(
                            domain_name="sample1.com",
                            validation_scope=(
                                models.VALIDATION_SCOPE_HOST
                            ),
                        ),
                    ],
                ),
            )
        assert _500_ERROR.is_equivalent(exc_info.value)


# ------------------------------------------------------------------ #
# TestValidateDomains — mirrors Go TestValidateDomains
# (validations_test.go:14-236) — 8 cases
# ------------------------------------------------------------------ #


class TestValidateDomains:
    """Test validate_domains endpoint."""

    def test_200_ok(self, mock_session):
        body = {
            "domains": [
                {
                    "domainName": "sample1.com",
                    "domainStatus": "VALIDATED",
                    "validationScope": "HOST",
                },
                {
                    "domainName": "sample2.com",
                    "domainStatus": "REQUEST_ACCEPTED",
                    "validationScope": "WILDCARD",
                },
                {
                    "domainName": "sample3.com",
                    "domainStatus": "REQUEST_ACCEPTED",
                    "validationScope": "DOMAIN",
                },
            ],
        }
        body_str = json.dumps(body)
        mock_session.post.return_value = (
            _mock_resp(200, body_str), body,
        )
        client = Client(mock_session)
        result = client.validate_domains(
            models.ValidateDomainsRequest(
                domains=[
                    models.ValidateDomain(
                        domain_name="sample1.com",
                        validation_scope=(
                            models.VALIDATION_SCOPE_HOST
                        ),
                        validation_method=(
                            models.VALIDATION_METHOD_HTTP
                        ),
                    ),
                    models.ValidateDomain(
                        domain_name="sample2.com",
                        validation_scope=(
                            models.VALIDATION_SCOPE_WILDCARD
                        ),
                        validation_method=(
                            models.VALIDATION_METHOD_DNS_CNAME
                        ),
                    ),
                    models.ValidateDomain(
                        domain_name="sample3.com",
                        validation_scope=(
                            models.VALIDATION_SCOPE_DOMAIN
                        ),
                        validation_method=(
                            models.VALIDATION_METHOD_DNS_TXT
                        ),
                    ),
                ],
            ),
        )
        call_args = mock_session.post.call_args
        assert call_args[0][0] == (
            "/domain-validation/v1/domains/validate-now"
        )
        assert result == models.ValidateDomainsResponse(
            domains=[
                models.ValidateDomainResponse(
                    domain_name="sample1.com",
                    domain_status="VALIDATED",
                    validation_scope="HOST",
                ),
                models.ValidateDomainResponse(
                    domain_name="sample2.com",
                    domain_status="REQUEST_ACCEPTED",
                    validation_scope="WILDCARD",
                ),
                models.ValidateDomainResponse(
                    domain_name="sample3.com",
                    domain_status="REQUEST_ACCEPTED",
                    validation_scope="DOMAIN",
                ),
            ],
        )

    def test_validation_empty_domain(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.validate_domains(
                models.ValidateDomainsRequest(domains=[]),
            )
        assert str(exc_info.value) == (
            "validate domains: struct validation:\n"
            "Domains: cannot be blank"
        )

    def test_validation_domain_name_not_supplied(
        self, mock_session,
    ):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.validate_domains(
                models.ValidateDomainsRequest(
                    domains=[
                        models.ValidateDomain(
                            domain_name="sample1.com",
                            validation_scope=(
                                models.VALIDATION_SCOPE_HOST
                            ),
                            validation_method=(
                                models.VALIDATION_METHOD_HTTP
                            ),
                        ),
                        models.ValidateDomain(
                            validation_scope=(
                                models.VALIDATION_SCOPE_HOST
                            ),
                            validation_method=(
                                models.VALIDATION_METHOD_HTTP
                            ),
                        ),
                    ],
                ),
            )
        assert str(exc_info.value) == (
            "validate domains: struct validation:\n"
            "Domains[1]: {\n"
            "\tDomainName: cannot be blank\n"
            "}"
        )

    def test_validation_scope_not_supplied(
        self, mock_session,
    ):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.validate_domains(
                models.ValidateDomainsRequest(
                    domains=[
                        models.ValidateDomain(
                            domain_name="sample1.com",
                            validation_method=(
                                models.VALIDATION_METHOD_HTTP
                            ),
                        ),
                    ],
                ),
            )
        assert str(exc_info.value) == (
            "validate domains: struct validation:\n"
            "Domains[0]: {\n"
            "\tValidationScope: cannot be blank\n"
            "}"
        )

    def test_validation_method_not_supplied(
        self, mock_session,
    ):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.validate_domains(
                models.ValidateDomainsRequest(
                    domains=[
                        models.ValidateDomain(
                            domain_name="sample1.com",
                            validation_scope=(
                                models.VALIDATION_SCOPE_HOST
                            ),
                        ),
                    ],
                ),
            )
        assert str(exc_info.value) == (
            "validate domains: struct validation:\n"
            "Domains[0]: {\n"
            "\tValidationMethod: cannot be blank\n"
            "}"
        )

    def test_validation_incorrect_scope(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.validate_domains(
                models.ValidateDomainsRequest(
                    domains=[
                        models.ValidateDomain(
                            domain_name="sample1.com",
                            validation_scope="incorrect",
                            validation_method=(
                                models.VALIDATION_METHOD_HTTP
                            ),
                        ),
                        models.ValidateDomain(
                            domain_name="sample2.com",
                            validation_scope=(
                                models.VALIDATION_SCOPE_HOST
                            ),
                            validation_method=(
                                models.VALIDATION_METHOD_HTTP
                            ),
                        ),
                    ],
                ),
            )
        assert str(exc_info.value) == (
            "validate domains: struct validation:\n"
            "Domains[0]: {\n"
            "\tValidationScope: value 'incorrect' is invalid. "
            "Must be one of: 'HOST', 'DOMAIN' or 'WILDCARD'\n"
            "}"
        )

    def test_validation_incorrect_method(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.validate_domains(
                models.ValidateDomainsRequest(
                    domains=[
                        models.ValidateDomain(
                            domain_name="sample1.com",
                            validation_method="incorrect",
                            validation_scope=(
                                models.VALIDATION_SCOPE_HOST
                            ),
                        ),
                        models.ValidateDomain(
                            domain_name="sample2.com",
                            validation_scope=(
                                models.VALIDATION_SCOPE_HOST
                            ),
                            validation_method=(
                                models.VALIDATION_METHOD_HTTP
                            ),
                        ),
                    ],
                ),
            )
        assert str(exc_info.value) == (
            "validate domains: struct validation:\n"
            "Domains[0]: {\n"
            "\tValidationMethod: value must be one of: "
            "'DNS_CNAME', 'DNS_TXT' or 'HTTP'\n"
            "}"
        )

    def test_500_internal_server_error(self, mock_session):
        mock_session.post.return_value = (
            _mock_resp(500, _500_BODY), None,
        )
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.validate_domains(
                models.ValidateDomainsRequest(
                    domains=[
                        models.ValidateDomain(
                            domain_name="sample1.com",
                            validation_scope=(
                                models.VALIDATION_SCOPE_DOMAIN
                            ),
                            validation_method=(
                                models.VALIDATION_METHOD_HTTP
                            ),
                        ),
                    ],
                ),
            )
        assert _500_ERROR.is_equivalent(exc_info.value)


# ------------------------------------------------------------------ #
# TestInvalidateDomain — mirrors Go TestInvalidateDomain
# (validations_test.go:238-348) — 5 cases
# ------------------------------------------------------------------ #


class TestInvalidateDomain:
    """Test invalidate_domain endpoint."""

    def test_200_ok(self, mock_session):
        body = {
            "domainName": "sample1.com",
            "domainStatus": "INVALIDATED",
            "validationScope": "HOST",
        }
        body_str = json.dumps(body)
        mock_session.post.return_value = (
            _mock_resp(200, body_str), body,
        )
        client = Client(mock_session)
        result = client.invalidate_domain(
            models.InvalidateDomainRequest(
                domain_name="sample1.com",
                validation_scope=models.VALIDATION_SCOPE_HOST,
            ),
        )
        call_args = mock_session.post.call_args
        path = call_args[0][0]
        assert (
            "/domain-validation/v1/domains/invalidate/"
            "sample1.com"
        ) in path
        assert result == models.InvalidateDomainResponse(
            domain_name="sample1.com",
            domain_status="INVALIDATED",
            validation_scope="HOST",
        )

    def test_validation_domain_name_not_supplied(
        self, mock_session,
    ):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.invalidate_domain(
                models.InvalidateDomainRequest(
                    validation_scope=(
                        models.VALIDATION_SCOPE_HOST
                    ),
                ),
            )
        assert str(exc_info.value) == (
            "invalidate domain: struct validation:\n"
            "DomainName: cannot be blank"
        )

    def test_validation_scope_not_supplied(
        self, mock_session,
    ):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.invalidate_domain(
                models.InvalidateDomainRequest(
                    domain_name="sample1.com",
                ),
            )
        assert str(exc_info.value) == (
            "invalidate domain: struct validation:\n"
            "ValidationScope: cannot be blank"
        )

    def test_validation_incorrect_scope(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.invalidate_domain(
                models.InvalidateDomainRequest(
                    domain_name="sample1.com",
                    validation_scope="incorrect",
                ),
            )
        assert str(exc_info.value) == (
            "invalidate domain: struct validation:\n"
            "ValidationScope: value 'incorrect' is invalid. "
            "Must be one of: 'HOST', 'DOMAIN' or 'WILDCARD'"
        )

    def test_500_internal_server_error(self, mock_session):
        mock_session.post.return_value = (
            _mock_resp(500, _500_BODY), None,
        )
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.invalidate_domain(
                models.InvalidateDomainRequest(
                    domain_name="sample1.com",
                    validation_scope=(
                        models.VALIDATION_SCOPE_HOST
                    ),
                ),
            )
        assert _500_ERROR.is_equivalent(exc_info.value)


# ------------------------------------------------------------------ #
# TestInvalidateDomains — mirrors Go TestInvalidateDomains
# (validations_test.go:350-531) — 6 cases
# ------------------------------------------------------------------ #


class TestInvalidateDomains:
    """Test invalidate_domains endpoint."""

    def test_200_ok(self, mock_session):
        body = {
            "domains": [
                {
                    "domainName": "sample1.com",
                    "domainStatus": "INVALIDATED",
                    "validationScope": "HOST",
                },
                {
                    "domainName": "sample2.com",
                    "domainStatus": "INVALIDATED",
                    "validationScope": "WILDCARD",
                },
                {
                    "domainName": "sample3.com",
                    "domainStatus": "INVALIDATED",
                    "validationScope": "DOMAIN",
                },
            ],
        }
        body_str = json.dumps(body)
        mock_session.post.return_value = (
            _mock_resp(200, body_str), body,
        )
        client = Client(mock_session)
        result = client.invalidate_domains(
            models.InvalidateDomainsRequest(
                domains=[
                    models.Domain(
                        domain_name="sample1.com",
                        validation_scope=(
                            models.VALIDATION_SCOPE_HOST
                        ),
                    ),
                    models.Domain(
                        domain_name="sample2.com",
                        validation_scope=(
                            models.VALIDATION_SCOPE_WILDCARD
                        ),
                    ),
                    models.Domain(
                        domain_name="sample3.com",
                        validation_scope=(
                            models.VALIDATION_SCOPE_DOMAIN
                        ),
                    ),
                ],
            ),
        )
        call_args = mock_session.post.call_args
        assert call_args[0][0] == (
            "/domain-validation/v1/domains/invalidate"
        )
        assert result == models.InvalidateDomainsResponse(
            domains=[
                models.InvalidateDomainResponse(
                    domain_name="sample1.com",
                    domain_status="INVALIDATED",
                    validation_scope="HOST",
                ),
                models.InvalidateDomainResponse(
                    domain_name="sample2.com",
                    domain_status="INVALIDATED",
                    validation_scope="WILDCARD",
                ),
                models.InvalidateDomainResponse(
                    domain_name="sample3.com",
                    domain_status="INVALIDATED",
                    validation_scope="DOMAIN",
                ),
            ],
        )

    def test_validation_empty_domain(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.invalidate_domains(
                models.InvalidateDomainsRequest(domains=[]),
            )
        assert str(exc_info.value) == (
            "invalidate domains: struct validation:\n"
            "Domains: cannot be blank"
        )

    def test_validation_domain_name_not_supplied(
        self, mock_session,
    ):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.invalidate_domains(
                models.InvalidateDomainsRequest(
                    domains=[
                        models.Domain(
                            domain_name="sample1.com",
                            validation_scope=(
                                models.VALIDATION_SCOPE_HOST
                            ),
                        ),
                        models.Domain(
                            validation_scope=(
                                models.VALIDATION_SCOPE_HOST
                            ),
                        ),
                    ],
                ),
            )
        assert str(exc_info.value) == (
            "invalidate domains: struct validation:\n"
            "Domains[1]: {\n"
            "\tDomainName: cannot be blank\n"
            "}"
        )

    def test_validation_scope_not_supplied(
        self, mock_session,
    ):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.invalidate_domains(
                models.InvalidateDomainsRequest(
                    domains=[
                        models.Domain(
                            domain_name="sample1.com",
                        ),
                    ],
                ),
            )
        assert str(exc_info.value) == (
            "invalidate domains: struct validation:\n"
            "Domains[0]: {\n"
            "\tValidationScope: cannot be blank\n"
            "}"
        )

    def test_validation_incorrect_scope(self, mock_session):
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.invalidate_domains(
                models.InvalidateDomainsRequest(
                    domains=[
                        models.Domain(
                            domain_name="sample1.com",
                            validation_scope="incorrect",
                        ),
                        models.Domain(
                            domain_name="sample2.com",
                            validation_scope=(
                                models.VALIDATION_SCOPE_HOST
                            ),
                        ),
                    ],
                ),
            )
        assert str(exc_info.value) == (
            "invalidate domains: struct validation:\n"
            "Domains[0]: {\n"
            "\tValidationScope: value 'incorrect' is invalid. "
            "Must be one of: 'HOST', 'DOMAIN' or 'WILDCARD'\n"
            "}"
        )

    def test_500_internal_server_error(self, mock_session):
        mock_session.post.return_value = (
            _mock_resp(500, _500_BODY), None,
        )
        client = Client(mock_session)
        with pytest.raises(ValueError) as exc_info:
            client.invalidate_domains(
                models.InvalidateDomainsRequest(
                    domains=[
                        models.Domain(
                            domain_name="sample1.com",
                            validation_scope=(
                                models.VALIDATION_SCOPE_DOMAIN
                            ),
                        ),
                    ],
                ),
            )
        assert _500_ERROR.is_equivalent(exc_info.value)
