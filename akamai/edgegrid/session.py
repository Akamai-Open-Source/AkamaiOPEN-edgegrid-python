"""Base session providing authenticated HTTP request execution for Akamai APIs.

Provides the Session class that wraps requests.Session with EdgeGridAuth to
deliver signed HTTP requests to Akamai APIs. All 22+ service-specific clients
depend on this module for HTTP communication.

Mirrors Go pkg/session (session.go, request.go) and internal/request
(request.go).
"""

import json
import logging
import platform

from typing import Any

import requests

from akamai.edgegrid.edgegrid import EdgeGridAuth
from akamai.edgegrid.edgerc import EdgeRc
from akamai.edgegrid import errors

logger = logging.getLogger(__name__)

# Version constant matching Go's session.Version.
# Kept in sync with the package version in setup.py.
VERSION = "3.0.0"


class Session:
    """Base Akamai API session providing authenticated HTTP request execution.

    Wraps requests.Session with EdgeGridAuth to provide signed API calls.
    All service-specific clients use this session for HTTP communication.

    Mirrors Go pkg/session.Session interface and session struct.

    Usage::

        >>> session = Session(edgerc_path="~/.edgerc", section="default")
        >>> response, data = session.exec(
        ...     "GET", "/api/v1/resource", out_type=dict
        ... )
    """

    DEFAULT_USER_AGENT = (
        f"Akamai-Open-Edgegrid-python/{VERSION} "
        f"python/{platform.python_version()}"
    )

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        edgerc_path: str | None = None,
        section: str = "default",
        auth: EdgeGridAuth | None = None,
        user_agent: str | None = None,
        http_trace: bool = False,
    ):
        """Initialize an authenticated session.

        Either provide edgerc_path (and optional section) for credential file
        loading, or provide a pre-configured auth handler directly.

        Mirrors Go session.New() with WithSigner, WithUserAgent,
        WithHTTPTracing options.

        :param edgerc_path: Path to .edgerc credentials file (uses EdgeRc).
        :param section: Section name within .edgerc file.
        :param auth: Pre-configured EdgeGridAuth instance (alternative to
            edgerc_path).
        :param user_agent: Custom User-Agent string (defaults to library
            identifier).
        :param http_trace: Enable HTTP request/response tracing via logging.
        """
        self._session = requests.Session()
        self._user_agent = user_agent or self.DEFAULT_USER_AGENT
        self._trace = http_trace

        # Configure authentication — delegates entirely to EdgeGridAuth.
        # EdgeGridAuth.__call__() is invoked automatically by requests for
        # every HTTP request through the session.auth mechanism.
        if auth is not None:
            self._session.auth = auth
        elif edgerc_path is not None:
            edgerc = EdgeRc(edgerc_path)
            self._session.auth = EdgeGridAuth.from_edgerc(edgerc, section)

    # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-branches
    def exec(
        self,
        method: str,
        path: str,
        body: Any = None,
        out_type: type | None = None,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> tuple[requests.Response, Any]:
        """Execute an authenticated HTTP request.

        Mirrors Go session.Exec(): signs the request, executes it, and
        optionally deserializes the response body.

        The flow mirrors Go Exec steps:
        1. Validate arguments
        2. Set default headers (User-Agent, Content-Type, Accept)
        3. Marshal body to JSON if provided
        4. Execute HTTP request (EdgeGridAuth signs automatically)
        5. Check for error status codes (>= 400)
        6. Unmarshal JSON response body if out_type is provided

        :param method: HTTP method (GET, POST, PUT, PATCH, DELETE).
        :param path: API path (e.g., "/iam/v3/api-clients").
        :param body: Request body to serialize as JSON (optional).
            Accepts dicts, lists, strings, bytes, or any JSON-serializable
            object. Strings and bytes are sent as-is.
        :param out_type: Expected response type for deserialization (optional).
            When provided and the response status is 2xx (excluding 204 and
            205), the response body is deserialized from JSON.
        :param headers: Additional request headers (optional). Overrides the
            default Content-Type, Accept, and User-Agent headers if specified.
        :param params: Query parameters (optional).
        :returns: Tuple of (response, deserialized_body_or_None).
        :raises errors.ErrInvalidArgument: If method or path is empty.
        :raises errors.ErrMarshaling: If request body JSON serialization fails.
        :raises errors.ErrUnmarshaling: If response body JSON deserialization
            fails.
        :raises errors.Error: If the API returns an error status code (>= 400).
        """
        # Validate arguments (mirrors Go's argument count check in Exec)
        if not method:
            raise errors.ErrInvalidArgument(
                "'method' must not be empty"
            )
        if not path:
            raise errors.ErrInvalidArgument(
                "'path' must not be empty"
            )

        # Set default headers (mirrors Go Exec: User-Agent, Content-Type,
        # Accept headers set when not already present)
        request_headers = {
            "User-Agent": self._user_agent,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if headers:
            request_headers.update(headers)

        # Marshal body if provided (mirrors Go Exec: json.Marshal(in[0]))
        json_body = None
        if body is not None:
            try:
                if isinstance(body, (str, bytes)):
                    json_body = body
                else:
                    json_body = json.dumps(body)
            except (TypeError, ValueError) as err:
                raise errors.ErrMarshaling(
                    f"marshaling input: {err}"
                ) from err

        # Trace logging for request (mirrors Go httputil.DumpRequestOut)
        if self._trace:
            logger.debug("Request: %s %s", method, path)
            if json_body:
                logger.debug("Request body: %s", json_body)

        # Execute HTTP request (mirrors Go Exec: Sign + client.Do)
        # EdgeGridAuth.__call__() is invoked automatically by the requests
        # library through the session.auth mechanism on every request.
        response = self._session.request(
            method=method,
            url=path,
            data=json_body,
            headers=request_headers,
            params=params,
        )

        # Trace logging for response (mirrors Go httputil.DumpResponse)
        if self._trace:
            response_preview = response.text[:500] if response.text else ""
            logger.debug(
                "Response: %s %s", response.status_code, response_preview
            )

        # Handle error responses — parse RFC 7807 error payload and raise.
        # This centralizes the error check that every Go service client
        # performs individually (e.g., if resp.StatusCode != http.StatusOK).
        if response.status_code >= 400:
            api_error = errors.parse_error_response(response)
            raise api_error

        # Unmarshal response if out_type provided and status is success
        # (2xx, excluding 204 No Content and 205 Reset Content).
        # Mirrors Go Exec: json.Unmarshal(data, out) when out != nil.
        result = None
        if (
            out_type is not None
            and 200 <= response.status_code < 300
            and response.status_code not in (204, 205)
        ):
            try:
                result = response.json()
            except (json.JSONDecodeError, ValueError) as err:
                raise errors.ErrUnmarshaling(
                    f"unmarshaling output: {err}"
                ) from err

        return response, result

    def get(
        self, path: str, **kwargs
    ) -> tuple[requests.Response, Any]:
        """Execute a GET request.

        Convenience wrapper for exec() that delegates to the core execution
        method with HTTP GET method.

        Mirrors Go internal/request.NewGet().

        :param path: API path (e.g., "/iam/v3/api-clients").
        :param kwargs: Additional keyword arguments passed to exec().
        :returns: Tuple of (response, deserialized_body_or_None).
        """
        return self.exec("GET", path, **kwargs)

    def post(
        self, path: str, body: Any = None, **kwargs
    ) -> tuple[requests.Response, Any]:
        """Execute a POST request.

        Convenience wrapper for exec() that delegates to the core execution
        method with HTTP POST method.

        Mirrors Go internal/request.NewPost().

        :param path: API path (e.g., "/iam/v3/api-clients").
        :param body: Request body to serialize as JSON (optional).
        :param kwargs: Additional keyword arguments passed to exec().
        :returns: Tuple of (response, deserialized_body_or_None).
        """
        return self.exec("POST", path, body=body, **kwargs)

    def put(
        self, path: str, body: Any = None, **kwargs
    ) -> tuple[requests.Response, Any]:
        """Execute a PUT request.

        Convenience wrapper for exec() that delegates to the core execution
        method with HTTP PUT method.

        Mirrors Go internal/request.NewPut().

        :param path: API path (e.g., "/iam/v3/api-clients/{clientId}").
        :param body: Request body to serialize as JSON (optional).
        :param kwargs: Additional keyword arguments passed to exec().
        :returns: Tuple of (response, deserialized_body_or_None).
        """
        return self.exec("PUT", path, body=body, **kwargs)

    def patch(
        self, path: str, body: Any = None, **kwargs
    ) -> tuple[requests.Response, Any]:
        """Execute a PATCH request.

        Convenience wrapper for exec() that delegates to the core execution
        method with HTTP PATCH method.

        Mirrors Go internal/request.NewPatch().

        :param path: API path (e.g., "/iam/v3/api-clients/{clientId}").
        :param body: Request body to serialize as JSON (optional).
        :param kwargs: Additional keyword arguments passed to exec().
        :returns: Tuple of (response, deserialized_body_or_None).
        """
        return self.exec("PATCH", path, body=body, **kwargs)

    def delete(
        self, path: str, **kwargs
    ) -> tuple[requests.Response, Any]:
        """Execute a DELETE request.

        Convenience wrapper for exec() that delegates to the core execution
        method with HTTP DELETE method.

        Mirrors Go internal/request.NewDelete().

        :param path: API path (e.g., "/iam/v3/api-clients/{clientId}").
        :param kwargs: Additional keyword arguments passed to exec().
        :returns: Tuple of (response, deserialized_body_or_None).
        """
        return self.exec("DELETE", path, **kwargs)

    @property
    def client(self) -> requests.Session:
        """Return the underlying requests.Session.

        Provides access to the underlying HTTP client for advanced
        configuration or direct use.

        Mirrors Go session.Client().

        :returns: The requests.Session instance with EdgeGridAuth configured.
        """
        return self._session

    @staticmethod
    def close_response_body(response: requests.Response) -> None:
        """Close response body.

        In Python with requests, connection cleanup is normally handled
        automatically, but this method is provided for API parity with
        Go's session.CloseResponseBody().

        Mirrors Go session.CloseResponseBody().

        :param response: The requests.Response to close.
        """
        response.close()
