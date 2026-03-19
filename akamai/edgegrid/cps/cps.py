# pylint: disable=too-many-lines,too-many-public-methods
"""CPS (Certificate Provisioning System) API client implementation.

Provides the :class:`CPSClient` class that mirrors the Go
``pkg/cps.CPS`` interface with 26 endpoint methods and one static utility
for extracting IDs from Location header URLs.

See: https://techdocs.akamai.com/cps/reference/api
"""

from __future__ import annotations

import logging
import re
import types
from dataclasses import fields, is_dataclass
from typing import Any, Union, get_args, get_origin, get_type_hints
from urllib.parse import urlparse

from akamai.edgegrid.session import Session
from akamai.edgegrid.cps import models
from akamai.edgegrid.cps import errors
from akamai.edgegrid.cps import validation

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# camelCase ↔ snake_case conversion helpers
# ---------------------------------------------------------------------------

_CAMEL_RE1 = re.compile(r"(.)([A-Z][a-z]+)")
_CAMEL_RE2 = re.compile(r"([a-z0-9])([A-Z])")
_NONE_TYPE = type(None)  # pylint: disable=invalid-name


def _camel_to_snake(name: str) -> str:
    """Convert a *camelCase* identifier to *snake_case*."""
    result = _CAMEL_RE1.sub(r"\1_\2", name)
    result = _CAMEL_RE2.sub(r"\1_\2", result)
    return result.lower()


def _snake_to_camel(name: str) -> str:
    """Convert a *snake_case* identifier to *camelCase*."""
    parts = name.split("_")
    return parts[0] + "".join(word.title() for word in parts[1:])


# ---------------------------------------------------------------------------
# Type introspection helpers
# ---------------------------------------------------------------------------


def _unwrap_optional(tp: type) -> type:
    """Unwrap ``T | None`` or ``Optional[T]`` to ``T``.

    Returns the original type when it is not an optional wrapper.
    """
    origin = get_origin(tp)
    if origin is Union or isinstance(tp, types.UnionType):
        non_none_args = [a for a in get_args(tp) if a is not _NONE_TYPE]
        if len(non_none_args) == 1:
            return non_none_args[0]
    return tp


def _is_dataclass_type(tp: type) -> bool:
    """Return ``True`` when *tp* is a dataclass **class** (not instance)."""
    return isinstance(tp, type) and is_dataclass(tp)


# ---------------------------------------------------------------------------
# JSON → dataclass builder (response deserialization)
# ---------------------------------------------------------------------------


def _coerce_value(field_type: type, value: Any) -> Any:
    """Recursively coerce a JSON-parsed *value* to match *field_type*.

    Handles nested dataclasses, lists of dataclasses, and optional wrappers.
    """
    if value is None:
        return None

    real_type = _unwrap_optional(field_type)

    # Nested dataclass
    if _is_dataclass_type(real_type) and isinstance(value, dict):
        return _build_response(real_type, value)

    # list[T] where T may be a dataclass
    origin = get_origin(real_type)
    if origin is list and isinstance(value, list):
        list_args = get_args(real_type)
        if list_args and _is_dataclass_type(list_args[0]):
            return [_build_response(list_args[0], item)
                    if isinstance(item, dict) else item
                    for item in value]
        return value

    return value


def _build_response(cls: type, data: Any) -> Any:
    """Convert a camelCase JSON dict into a dataclass of type *cls*.

    Recursively converts nested dicts to nested dataclass instances and
    lists of dicts to lists of dataclass instances.
    """
    if data is None:
        return cls()
    if not isinstance(data, dict):
        return data

    hints = get_type_hints(cls)
    field_names = {f.name for f in fields(cls)}
    kwargs: dict[str, Any] = {}

    for key, value in data.items():
        snake_key = _camel_to_snake(key)
        if snake_key not in field_names:
            continue
        field_type = hints.get(snake_key)
        if field_type is not None:
            kwargs[snake_key] = _coerce_value(field_type, value)
        else:
            kwargs[snake_key] = value

    return cls(**kwargs)


# ---------------------------------------------------------------------------
# dataclass → JSON dict builder (request serialization)
# ---------------------------------------------------------------------------


def _model_to_dict(obj: Any) -> dict[str, Any] | Any:
    """Convert a dataclass instance to a camelCase JSON-serializable dict.

    - snake_case attribute names are converted to camelCase keys.
    - Nested dataclass instances are recursively converted.
    - ``None`` values are omitted (matching Go ``omitempty`` for pointers).
    """
    if not is_dataclass(obj) or isinstance(obj, type):
        return obj

    result: dict[str, Any] = {}
    for fld in fields(obj):
        value = getattr(obj, fld.name)
        if value is None:
            continue
        camel_key = _snake_to_camel(fld.name)
        if is_dataclass(value) and not isinstance(value, type):
            result[camel_key] = _model_to_dict(value)
        elif isinstance(value, list):
            result[camel_key] = [
                _model_to_dict(item)
                if (is_dataclass(item) and not isinstance(item, type))
                else item
                for item in value
            ]
        else:
            result[camel_key] = value
    return result


# ---------------------------------------------------------------------------
# CPSClient
# ---------------------------------------------------------------------------


class CPSClient:
    """CPS (Certificate Provisioning System) API client.

    Provides access to the Akamai CPS APIs for managing SSL/TLS certificate
    enrollments, changes, deployments, and related operations.

    Implements 26 endpoint methods and one static utility mirroring the Go
    ``pkg/cps.CPS`` interface:

    * Change management info — 3 methods
    * Changes — 2 methods
    * Deployments — 3 methods
    * Deployment schedules — 2 methods
    * DV challenges — 2 methods
    * Enrollments — 5 methods
    * History — 3 methods
    * Post-verification warnings — 2 methods
    * Pre-verification warnings — 2 methods
    * Third-party CSR — 2 methods
    * Utility — ``get_id_from_location`` (static)

    See: https://techdocs.akamai.com/cps/reference/api
    """

    def __init__(self, session: Session) -> None:
        """Initialize CPS client with an authenticated session.

        Mirrors Go ``cps.Client(sess session.Session, opts ...Option) CPS``.

        :param session: An authenticated
            :class:`~akamai.edgegrid.session.Session` instance.
        """
        self._session = session

    # ------------------------------------------------------------------
    # Change Management Info (change_management_info.go)
    # ------------------------------------------------------------------

    def get_change_management_info(
        self, enrollment_id: int, change_id: int,
    ) -> models.ChangeManagementInfoResponse:
        """Get change management info for a change.

        Mirrors Go ``CPS.GetChangeManagementInfo``
        (change_management_info.go).

        See: https://techdocs.akamai.com/cps/reference/get-change-management-info

        :param enrollment_id: Enrollment identifier.
        :param change_id: Change identifier.
        :returns: Change management information.
        """
        logger.debug("GetChangeManagementInfo")

        validation_err = validation.validate_get_change_request(
            enrollment_id, change_id,
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetChangeManagementInfo}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = (
            f"/cps/v2/enrollments/{enrollment_id}"
            f"/changes/{change_id}/input/info/change-management-info"
        )
        headers = {
            "Accept":
                "application/vnd.akamai.cps.change-management-info.v5+json",
        }

        try:
            _, result = self._session.exec(
                "GET", path,
                expect_json=True,
                headers=headers,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=f"{errors.ErrGetChangeManagementInfo}: {err.title}",
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetChangeManagementInfo}: "
                    f"request failed: {err}"
                ),
            ) from err

        return _build_response(
            models.ChangeManagementInfoResponse, result,
        )

    def get_change_deployment_info(
        self, enrollment_id: int, change_id: int,
    ) -> models.ChangeDeploymentInfoResponse:
        """Get change deployment info for a change.

        Uses the same URL path as :meth:`get_change_management_info`
        but with a different ``Accept`` header requesting deployment data.

        Mirrors Go ``CPS.GetChangeDeploymentInfo``
        (change_management_info.go).

        See: https://techdocs.akamai.com/cps/reference/get-change-deployment-info

        :param enrollment_id: Enrollment identifier.
        :param change_id: Change identifier.
        :returns: Change deployment information (a ``Deployment`` instance).
        """
        logger.debug("GetChangeDeploymentInfo")

        validation_err = validation.validate_get_change_request(
            enrollment_id, change_id,
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetChangeDeploymentInfo}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = (
            f"/cps/v2/enrollments/{enrollment_id}"
            f"/changes/{change_id}/input/info/change-management-info"
        )
        headers = {
            "Accept": "application/vnd.akamai.cps.deployment.v8+json",
        }

        try:
            _, result = self._session.exec(
                "GET", path,
                expect_json=True,
                headers=headers,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=f"{errors.ErrGetChangeDeploymentInfo}: {err.title}",
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetChangeDeploymentInfo}: "
                    f"request failed: {err}"
                ),
            ) from err

        return _build_response(
            models.ChangeDeploymentInfoResponse, result,
        )

    def acknowledge_change_management(
        self,
        enrollment_id: int,
        change_id: int,
        acknowledgement: str,
    ) -> None:
        """Acknowledge or deny change management for a change.

        Mirrors Go ``CPS.AcknowledgeChangeManagement``
        (change_management_info.go).

        See: https://techdocs.akamai.com/cps/reference/acknowledge-change-management

        :param enrollment_id: Enrollment identifier.
        :param change_id: Change identifier.
        :param acknowledgement: Acknowledgement value — use
            ``errors.ACKNOWLEDGEMENT_ACKNOWLEDGE`` or
            ``errors.ACKNOWLEDGEMENT_DENY``.
        """
        logger.debug("AcknowledgeChangeManagement")

        validation_err = validation.validate_acknowledgement_request(
            enrollment_id, change_id, acknowledgement,
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrAcknowledgeChangeManagement}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = (
            f"/cps/v2/enrollments/{enrollment_id}"
            f"/changes/{change_id}/input/update/change-management-ack"
        )
        headers = {
            "Accept": "application/vnd.akamai.cps.change-id.v1+json",
            "Content-Type": (
                "application/vnd.akamai.cps.acknowledgement.v1+json"
                "; charset=utf-8"
            ),
        }
        body = {"acknowledgement": acknowledgement}

        try:
            self._session.exec(
                "POST", path,
                body=body,
                headers=headers,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrAcknowledgeChangeManagement}: {err.title}"
                ),
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrAcknowledgeChangeManagement}: "
                    f"request failed: {err}"
                ),
            ) from err

    # ------------------------------------------------------------------
    # Changes (changes.go)
    # ------------------------------------------------------------------

    def get_change_status(
        self, enrollment_id: int, change_id: int,
    ) -> models.Change:
        """Get the status of a change.

        Mirrors Go ``CPS.GetChangeStatus`` (changes.go).

        See: https://techdocs.akamai.com/cps/reference/get-change

        :param enrollment_id: Enrollment identifier.
        :param change_id: Change identifier.
        :returns: Change status and details.
        """
        logger.debug("GetChangeStatus")

        validation_err = validation.validate_get_change_status_request(
            enrollment_id, change_id,
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetChangeStatus}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = (
            f"/cps/v2/enrollments/{enrollment_id}"
            f"/changes/{change_id}"
        )
        headers = {
            "Accept": "application/vnd.akamai.cps.change.v2+json",
        }

        try:
            _, result = self._session.exec(
                "GET", path,
                expect_json=True,
                headers=headers,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=f"{errors.ErrGetChangeStatus}: {err.title}",
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetChangeStatus}: request failed: {err}"
                ),
            ) from err

        return _build_response(models.Change, result)

    def cancel_change(
        self, enrollment_id: int, change_id: int,
    ) -> models.CancelChangeResponse:
        """Cancel a pending change.

        Mirrors Go ``CPS.CancelChange`` (changes.go).

        See: https://techdocs.akamai.com/cps/reference/delete-change

        :param enrollment_id: Enrollment identifier.
        :param change_id: Change identifier.
        :returns: Cancellation response.
        """
        logger.debug("CancelChange")

        validation_err = validation.validate_cancel_change_request(
            enrollment_id, change_id,
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrCancelChange}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = (
            f"/cps/v2/enrollments/{enrollment_id}"
            f"/changes/{change_id}"
        )
        headers = {
            "Accept": "application/vnd.akamai.cps.change-id.v1+json",
        }

        try:
            _, result = self._session.exec(
                "DELETE", path,
                expect_json=True,
                headers=headers,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=f"{errors.ErrCancelChange}: {err.title}",
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrCancelChange}: request failed: {err}"
                ),
            ) from err

        return _build_response(models.CancelChangeResponse, result)

    # ------------------------------------------------------------------
    # Deployments (deployments.go)
    # ------------------------------------------------------------------

    def list_deployments(
        self, enrollment_id: int,
    ) -> models.ListDeploymentsResponse:
        """List deployments for an enrollment.

        Mirrors Go ``CPS.ListDeployments`` (deployments.go).

        See: https://techdocs.akamai.com/cps/reference/get-deployments

        :param enrollment_id: Enrollment identifier.
        :returns: List of deployments.
        """
        logger.debug("ListDeployments")

        validation_err = validation.validate_list_deployments_request(
            enrollment_id,
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrListDeployments}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = f"/cps/v2/enrollments/{enrollment_id}/deployments"
        headers = {
            "Accept": "application/vnd.akamai.cps.deployments.v8+json",
        }

        try:
            _, result = self._session.exec(
                "GET", path,
                expect_json=True,
                headers=headers,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=f"{errors.ErrListDeployments}: {err.title}",
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrListDeployments}: request failed: {err}"
                ),
            ) from err

        return _build_response(models.ListDeploymentsResponse, result)

    def get_production_deployment(
        self, enrollment_id: int,
    ) -> models.GetProductionDeploymentResponse:
        """Get the production deployment for an enrollment.

        Mirrors Go ``CPS.GetProductionDeployment`` (deployments.go).

        See: https://techdocs.akamai.com/cps/reference/get-production-deployment

        :param enrollment_id: Enrollment identifier.
        :returns: Production deployment details.
        """
        logger.debug("GetProductionDeployment")

        validation_err = validation.validate_get_deployment_request(
            enrollment_id,
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetProductionDeployment}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = (
            f"/cps/v2/enrollments/{enrollment_id}/deployments/production"
        )
        headers = {
            "Accept": "application/vnd.akamai.cps.deployment.v8+json",
        }

        try:
            _, result = self._session.exec(
                "GET", path,
                expect_json=True,
                headers=headers,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetProductionDeployment}: {err.title}"
                ),
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetProductionDeployment}: "
                    f"request failed: {err}"
                ),
            ) from err

        return _build_response(
            models.GetProductionDeploymentResponse, result,
        )

    def get_staging_deployment(
        self, enrollment_id: int,
    ) -> models.GetStagingDeploymentResponse:
        """Get the staging deployment for an enrollment.

        Mirrors Go ``CPS.GetStagingDeployment`` (deployments.go).

        See: https://techdocs.akamai.com/cps/reference/get-staging-deployment

        :param enrollment_id: Enrollment identifier.
        :returns: Staging deployment details.
        """
        logger.debug("GetStagingDeployment")

        validation_err = validation.validate_get_deployment_request(
            enrollment_id,
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetStagingDeployment}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = f"/cps/v2/enrollments/{enrollment_id}/deployments/staging"
        headers = {
            "Accept": "application/vnd.akamai.cps.deployment.v8+json",
        }

        try:
            _, result = self._session.exec(
                "GET", path,
                expect_json=True,
                headers=headers,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=f"{errors.ErrGetStagingDeployment}: {err.title}",
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetStagingDeployment}: "
                    f"request failed: {err}"
                ),
            ) from err

        return _build_response(
            models.GetStagingDeploymentResponse, result,
        )

    # ------------------------------------------------------------------
    # Deployment Schedules (deployment_schedules.go)
    # ------------------------------------------------------------------

    def get_deployment_schedule(
        self, enrollment_id: int, change_id: int,
    ) -> models.DeploymentSchedule:
        """Get the deployment schedule for a change.

        Mirrors Go ``CPS.GetDeploymentSchedule``
        (deployment_schedules.go).

        See: https://techdocs.akamai.com/cps/reference/get-deployment-schedule

        :param enrollment_id: Enrollment identifier.
        :param change_id: Change identifier.
        :returns: Deployment schedule.
        """
        logger.debug("GetDeploymentSchedule")

        validation_err = (
            validation.validate_get_deployment_schedule_request(
                change_id, enrollment_id,
            )
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetDeploymentSchedule}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = (
            f"/cps/v2/enrollments/{enrollment_id}"
            f"/changes/{change_id}/deployment-schedule"
        )
        headers = {
            "Accept": (
                "application/vnd.akamai.cps"
                ".deployment-schedule.v1+json"
            ),
        }

        try:
            _, result = self._session.exec(
                "GET", path,
                expect_json=True,
                headers=headers,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetDeploymentSchedule}: {err.title}"
                ),
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetDeploymentSchedule}: "
                    f"request failed: {err}"
                ),
            ) from err

        return _build_response(models.DeploymentSchedule, result)

    def update_deployment_schedule(
        self,
        enrollment_id: int,
        change_id: int,
        body: models.DeploymentSchedule,
    ) -> models.UpdateDeploymentScheduleResponse:
        """Update the deployment schedule for a change.

        Mirrors Go ``CPS.UpdateDeploymentSchedule``
        (deployment_schedules.go).

        See: https://techdocs.akamai.com/cps/reference/put-deployment-schedule

        :param enrollment_id: Enrollment identifier.
        :param change_id: Change identifier.
        :param body: Updated deployment schedule.
        :returns: Update response.
        """
        logger.debug("UpdateDeploymentSchedule")

        validation_err = (
            validation.validate_update_deployment_schedule_request(
                change_id, enrollment_id,
            )
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrUpdateDeploymentSchedule}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = (
            f"/cps/v2/enrollments/{enrollment_id}"
            f"/changes/{change_id}/deployment-schedule"
        )
        headers = {
            "Accept": "application/vnd.akamai.cps.change-id.v1+json",
            "Content-Type": (
                "application/vnd.akamai.cps"
                ".deployment-schedule.v1+json; charset=utf-8"
            ),
        }

        try:
            _, result = self._session.exec(
                "PUT", path,
                body=_model_to_dict(body),
                expect_json=True,
                headers=headers,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrUpdateDeploymentSchedule}: {err.title}"
                ),
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrUpdateDeploymentSchedule}: "
                    f"request failed: {err}"
                ),
            ) from err

        return _build_response(
            models.UpdateDeploymentScheduleResponse, result,
        )

    # ------------------------------------------------------------------
    # DV Challenges (dv_challenges.go)
    # ------------------------------------------------------------------

    def get_change_lets_encrypt_challenges(
        self, enrollment_id: int, change_id: int,
    ) -> models.DVArray:
        """Get Let's Encrypt challenges for a change.

        Mirrors Go ``CPS.GetChangeLetsEncryptChallenges``
        (dv_challenges.go).

        See: https://techdocs.akamai.com/cps/reference/get-dv-challenges

        :param enrollment_id: Enrollment identifier.
        :param change_id: Change identifier.
        :returns: DV challenge array.
        """
        logger.debug("GetChangeLetsEncryptChallenges")

        validation_err = validation.validate_get_change_request(
            enrollment_id, change_id,
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetChangeLetsEncryptChallenges}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = (
            f"/cps/v2/enrollments/{enrollment_id}"
            f"/changes/{change_id}"
            "/input/info/lets-encrypt-challenges"
        )
        headers = {
            "Accept": (
                "application/vnd.akamai.cps.dv-challenges.v2+json"
            ),
        }

        try:
            _, result = self._session.exec(
                "GET", path,
                expect_json=True,
                headers=headers,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetChangeLetsEncryptChallenges}: "
                    f"{err.title}"
                ),
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetChangeLetsEncryptChallenges}: "
                    f"request failed: {err}"
                ),
            ) from err

        return _build_response(models.DVArray, result)

    def acknowledge_dv_challenges(
        self,
        enrollment_id: int,
        change_id: int,
        acknowledgement: str,
    ) -> None:
        """Acknowledge DV (Let's Encrypt) challenges completion.

        Mirrors Go ``CPS.AcknowledgeDVChallenges`` (dv_challenges.go).
        Accepts status 204, 202, or 200.

        See: https://techdocs.akamai.com/cps/reference/post-dv-challenges

        :param enrollment_id: Enrollment identifier.
        :param change_id: Change identifier.
        :param acknowledgement: Acknowledgement value.
        """
        logger.debug("AcknowledgeDVChallenges")

        validation_err = validation.validate_acknowledgement_request(
            enrollment_id, change_id, acknowledgement,
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrAcknowledgeLetsEncryptChallenges}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = (
            f"/cps/v2/enrollments/{enrollment_id}"
            f"/changes/{change_id}"
            "/input/update/lets-encrypt-challenges-completed"
        )
        headers = {
            "Accept": "application/vnd.akamai.cps.change-id.v1+json",
            "Content-Type": (
                "application/vnd.akamai.cps"
                ".acknowledgement.v1+json; charset=utf-8"
            ),
        }
        body = {"acknowledgement": acknowledgement}

        try:
            response, _ = self._session.exec(
                "POST", path,
                body=body,
                headers=headers,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrAcknowledgeLetsEncryptChallenges}: "
                    f"{err.title}"
                ),
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrAcknowledgeLetsEncryptChallenges}: "
                    f"request failed: {err}"
                ),
            ) from err

        if response.status_code not in (204, 202, 200):
            raise errors.parse_cps_error(response)

    # ------------------------------------------------------------------
    # Enrollments (enrollments.go)
    # ------------------------------------------------------------------

    def list_enrollments(
        self, contract_id: str,
    ) -> models.ListEnrollmentsResponse:
        """List enrollments for a contract.

        Mirrors Go ``CPS.ListEnrollments`` (enrollments.go).

        See: https://techdocs.akamai.com/cps/reference/get-enrollments

        :param contract_id: Contract identifier.
        :returns: List of enrollments.
        """
        logger.debug("ListEnrollments")

        validation_err = validation.validate_list_enrollments_request(
            contract_id,
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrListEnrollments}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = "/cps/v2/enrollments"
        headers = {
            "Accept": (
                "application/vnd.akamai.cps.enrollments.v11+json"
            ),
        }
        params = {"contractId": contract_id}

        try:
            _, result = self._session.exec(
                "GET", path,
                expect_json=True,
                headers=headers,
                params=params,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=f"{errors.ErrListEnrollments}: {err.title}",
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrListEnrollments}: "
                    f"request failed: {err}"
                ),
            ) from err

        return _build_response(models.ListEnrollmentsResponse, result)

    def get_enrollment(
        self, enrollment_id: int,
    ) -> models.GetEnrollmentResponse:
        """Get a specific enrollment.

        Mirrors Go ``CPS.GetEnrollment`` (enrollments.go).

        See: https://techdocs.akamai.com/cps/reference/get-enrollment

        :param enrollment_id: Enrollment identifier.
        :returns: Enrollment details.
        """
        logger.debug("GetEnrollment")

        validation_err = validation.validate_get_enrollment_request(
            enrollment_id,
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetEnrollment}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = f"/cps/v2/enrollments/{enrollment_id}"
        headers = {
            "Accept": (
                "application/vnd.akamai.cps.enrollment.v11+json"
            ),
        }

        try:
            _, result = self._session.exec(
                "GET", path,
                expect_json=True,
                headers=headers,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=f"{errors.ErrGetEnrollment}: {err.title}",
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetEnrollment}: request failed: {err}"
                ),
            ) from err

        return _build_response(models.GetEnrollmentResponse, result)

    def create_enrollment(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        contract_id: str,
        body: models.EnrollmentRequestBody,
        deploy_not_after: str = "",
        deploy_not_before: str = "",
        allow_duplicate_cn: bool = False,
    ) -> models.CreateEnrollmentResponse:
        """Create a new enrollment.

        Mirrors Go ``CPS.CreateEnrollment`` (enrollments.go).
        Expects 202 Accepted.  Parses enrollment ID from the
        ``enrollment`` field in the response using
        ``get_id_from_location``.

        See: https://techdocs.akamai.com/cps/reference/post-enrollment

        :param contract_id: Contract identifier.
        :param body: Enrollment request body.
        :param deploy_not_after: Optional deploy-not-after date.
        :param deploy_not_before: Optional deploy-not-before date.
        :param allow_duplicate_cn: Allow duplicate CN.
        :returns: Create enrollment response with parsed ID.
        """
        logger.debug("CreateEnrollment")

        validation_err = validation.validate_create_enrollment_request(
            body, contract_id,
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrCreateEnrollment}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = "/cps/v2/enrollments"
        headers = {
            "Accept": (
                "application/vnd.akamai.cps"
                ".enrollment-status.v1+json"
            ),
            "Content-Type": (
                "application/vnd.akamai.cps"
                ".enrollment.v11+json; charset=utf-8"
            ),
        }
        params: dict[str, str] = {"contractId": contract_id}
        if deploy_not_after:
            params["deploy-not-after"] = deploy_not_after
        if deploy_not_before:
            params["deploy-not-before"] = deploy_not_before
        if allow_duplicate_cn:
            params["allow-duplicate-cn"] = "true"

        try:
            response, result = self._session.exec(
                "POST", path,
                body=_model_to_dict(body),
                expect_json=True,
                headers=headers,
                params=params,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=f"{errors.ErrCreateEnrollment}: {err.title}",
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrCreateEnrollment}: "
                    f"request failed: {err}"
                ),
            ) from err

        if response.status_code != 202:
            raise errors.parse_cps_error(response)

        resp = _build_response(models.CreateEnrollmentResponse, result)

        # Parse the enrollment ID from the location URL.
        if resp.enrollment:
            try:
                resp.id = CPSClient.get_id_from_location(
                    resp.enrollment,
                )
            except (ValueError, IndexError) as err:
                raise errors.Error(
                    title=(
                        f"{errors.ErrCreateEnrollment}: "
                        f"failed to parse location: {err}"
                    ),
                ) from err
        return resp

    def update_enrollment(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
        self,
        enrollment_id: int,
        body: models.EnrollmentRequestBody,
        allow_cancel_pending_changes: bool | None = None,
        allow_staging_bypass: bool | None = None,
        deploy_not_after: str = "",
        deploy_not_before: str = "",
        force_renewal: bool | None = None,
        renewal_date_check_override: bool | None = None,
    ) -> models.UpdateEnrollmentResponse:
        """Update an enrollment.

        Mirrors Go ``CPS.UpdateEnrollment`` (enrollments.go).
        Expects 202 or 200.  Parses enrollment ID from the
        ``enrollment`` field in the response using
        ``get_id_from_location``.

        NOTE: The Go implementation uses ``ErrCreateEnrollment``
        (not ``ErrUpdateEnrollment``) for the validation sentinel —
        this mirrors that behaviour.

        See: https://techdocs.akamai.com/cps/reference/put-enrollment

        :param enrollment_id: Enrollment identifier.
        :param body: Enrollment request body.
        :param allow_cancel_pending_changes: Optional flag.
        :param allow_staging_bypass: Optional flag.
        :param deploy_not_after: Optional deploy-not-after date.
        :param deploy_not_before: Optional deploy-not-before date.
        :param force_renewal: Optional flag.
        :param renewal_date_check_override: Optional flag.
        :returns: Update enrollment response with parsed ID.
        """
        logger.debug("UpdateEnrollment")

        # NOTE: Go bug — uses ErrCreateEnrollment instead of
        # ErrUpdateEnrollment for the validation sentinel.
        validation_err = validation.validate_update_enrollment_request(
            body, enrollment_id,
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrCreateEnrollment}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = f"/cps/v2/enrollments/{enrollment_id}"
        headers = {
            "Accept": (
                "application/vnd.akamai.cps"
                ".enrollment-status.v1+json"
            ),
            "Content-Type": (
                "application/vnd.akamai.cps"
                ".enrollment.v11+json; charset=utf-8"
            ),
        }
        params: dict[str, str] = {}
        if allow_cancel_pending_changes is not None:
            params["allow-cancel-pending-changes"] = str(
                allow_cancel_pending_changes,
            ).lower()
        if allow_staging_bypass is not None:
            params["allow-staging-bypass"] = str(
                allow_staging_bypass,
            ).lower()
        if deploy_not_after:
            params["deploy-not-after"] = deploy_not_after
        if deploy_not_before:
            params["deploy-not-before"] = deploy_not_before
        if force_renewal is not None:
            params["force-renewal"] = str(force_renewal).lower()
        if renewal_date_check_override is not None:
            params["renewal-date-check-override"] = str(
                renewal_date_check_override,
            ).lower()

        try:
            response, result = self._session.exec(
                "PUT", path,
                body=_model_to_dict(body),
                expect_json=True,
                headers=headers,
                params=params,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=f"{errors.ErrUpdateEnrollment}: {err.title}",
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrUpdateEnrollment}: "
                    f"request failed: {err}"
                ),
            ) from err

        if response.status_code not in (202, 200):
            raise errors.parse_cps_error(response)

        resp = _build_response(models.UpdateEnrollmentResponse, result)

        # Parse the enrollment ID from the location URL.
        # NOTE: Go bug — uses ErrCreateEnrollment for this error too.
        if resp.enrollment:
            try:
                resp.id = CPSClient.get_id_from_location(
                    resp.enrollment,
                )
            except (ValueError, IndexError) as err:
                raise errors.Error(
                    title=(
                        f"{errors.ErrCreateEnrollment}: "
                        f"failed to parse location: {err}"
                    ),
                ) from err
        return resp

    def remove_enrollment(
        self,
        enrollment_id: int,
        allow_cancel_pending_changes: bool | None = None,
        deploy_not_after: str = "",
        deploy_not_before: str = "",
    ) -> models.RemoveEnrollmentResponse:
        """Remove (delete) an enrollment.

        Mirrors Go ``CPS.RemoveEnrollment`` (enrollments.go).
        Expects 202 or 200.

        See: https://techdocs.akamai.com/cps/reference/delete-enrollment

        :param enrollment_id: Enrollment identifier.
        :param allow_cancel_pending_changes: Optional flag.
        :param deploy_not_after: Optional deploy-not-after date.
        :param deploy_not_before: Optional deploy-not-before date.
        :returns: Remove enrollment response.
        """
        logger.debug("RemoveEnrollment")

        validation_err = validation.validate_remove_enrollment_request(
            enrollment_id,
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrRemoveEnrollment}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = f"/cps/v2/enrollments/{enrollment_id}"
        headers = {
            "Accept": (
                "application/vnd.akamai.cps"
                ".enrollment-status.v1+json"
            ),
        }
        params: dict[str, str] = {}
        if allow_cancel_pending_changes is not None:
            params["allow-cancel-pending-changes"] = str(
                allow_cancel_pending_changes,
            ).lower()
        if deploy_not_after:
            params["deploy-not-after"] = deploy_not_after
        if deploy_not_before:
            params["deploy-not-before"] = deploy_not_before

        try:
            response, result = self._session.exec(
                "DELETE", path,
                expect_json=True,
                headers=headers,
                params=params,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=f"{errors.ErrRemoveEnrollment}: {err.title}",
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrRemoveEnrollment}: "
                    f"request failed: {err}"
                ),
            ) from err

        if response.status_code not in (202, 200):
            raise errors.parse_cps_error(response)

        return _build_response(
            models.RemoveEnrollmentResponse, result,
        )

    # ------------------------------------------------------------------
    # History (history.go)
    # ------------------------------------------------------------------

    def get_dv_history(
        self, enrollment_id: int,
    ) -> models.GetDVHistoryResponse:
        """Get DV validation history for an enrollment.

        Mirrors Go ``CPS.GetDVHistory`` (history.go).

        See: https://techdocs.akamai.com/cps/reference/get-dv-history

        :param enrollment_id: Enrollment identifier.
        :returns: DV history.
        """
        logger.debug("GetDVHistory")

        validation_err = validation.validate_get_dv_history_request(
            enrollment_id,
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetDVHistory}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = f"/cps/v2/enrollments/{enrollment_id}/dv-history"
        headers = {
            "Accept": (
                "application/vnd.akamai.cps.dv-history.v1+json"
            ),
        }

        try:
            _, result = self._session.exec(
                "GET", path,
                expect_json=True,
                headers=headers,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=f"{errors.ErrGetDVHistory}: {err.title}",
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetDVHistory}: request failed: {err}"
                ),
            ) from err

        return _build_response(models.GetDVHistoryResponse, result)

    def get_certificate_history(
        self, enrollment_id: int,
    ) -> models.GetCertificateHistoryResponse:
        """Get certificate history for an enrollment.

        Mirrors Go ``CPS.GetCertificateHistory`` (history.go).

        See: https://techdocs.akamai.com/cps/reference/get-certificate-history

        :param enrollment_id: Enrollment identifier.
        :returns: Certificate history.
        """
        logger.debug("GetCertificateHistory")

        validation_err = (
            validation.validate_get_certificate_history_request(
                enrollment_id,
            )
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetCertificateHistory}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = (
            f"/cps/v2/enrollments/{enrollment_id}/history/certificates"
        )
        headers = {
            "Accept": (
                "application/vnd.akamai.cps"
                ".certificate-history.v2+json"
            ),
        }

        try:
            _, result = self._session.exec(
                "GET", path,
                expect_json=True,
                headers=headers,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetCertificateHistory}: {err.title}"
                ),
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetCertificateHistory}: "
                    f"request failed: {err}"
                ),
            ) from err

        return _build_response(
            models.GetCertificateHistoryResponse, result,
        )

    def get_change_history(
        self, enrollment_id: int,
    ) -> models.GetChangeHistoryResponse:
        """Get change history for an enrollment.

        Mirrors Go ``CPS.GetChangeHistory`` (history.go).

        See: https://techdocs.akamai.com/cps/reference/get-change-history

        :param enrollment_id: Enrollment identifier.
        :returns: Change history.
        """
        logger.debug("GetChangeHistory")

        validation_err = (
            validation.validate_get_change_history_request(
                enrollment_id,
            )
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetChangeHistory}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = f"/cps/v2/enrollments/{enrollment_id}/history/changes"
        headers = {
            "Accept": (
                "application/vnd.akamai.cps.change-history.v5+json"
            ),
        }

        try:
            _, result = self._session.exec(
                "GET", path,
                expect_json=True,
                headers=headers,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=f"{errors.ErrGetChangeHistory}: {err.title}",
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetChangeHistory}: "
                    f"request failed: {err}"
                ),
            ) from err

        return _build_response(
            models.GetChangeHistoryResponse, result,
        )

    # ------------------------------------------------------------------
    # Post-Verification Warnings (post_verification_warnings.go)
    # ------------------------------------------------------------------

    def get_change_post_verification_warnings(
        self, enrollment_id: int, change_id: int,
    ) -> models.PostVerificationWarnings:
        """Get post-verification warnings for a change.

        Mirrors Go ``CPS.GetChangePostVerificationWarnings``
        (post_verification_warnings.go).

        See: https://techdocs.akamai.com/cps/reference/get-post-verification-warnings

        :param enrollment_id: Enrollment identifier.
        :param change_id: Change identifier.
        :returns: Post-verification warnings.
        """
        logger.debug("GetChangePostVerificationWarnings")

        validation_err = validation.validate_get_change_request(
            enrollment_id, change_id,
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetChangePostVerificationWarnings}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = (
            f"/cps/v2/enrollments/{enrollment_id}"
            f"/changes/{change_id}"
            "/input/info/post-verification-warnings"
        )
        headers = {
            "Accept": (
                "application/vnd.akamai.cps.warnings.v1+json"
            ),
        }

        try:
            _, result = self._session.exec(
                "GET", path,
                expect_json=True,
                headers=headers,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetChangePostVerificationWarnings}: "
                    f"{err.title}"
                ),
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetChangePostVerificationWarnings}: "
                    f"request failed: {err}"
                ),
            ) from err

        return _build_response(
            models.PostVerificationWarnings, result,
        )

    def acknowledge_post_verification_warnings(
        self,
        enrollment_id: int,
        change_id: int,
        acknowledgement: str,
    ) -> None:
        """Acknowledge post-verification warnings.

        Mirrors Go ``CPS.AcknowledgePostVerificationWarnings``
        (post_verification_warnings.go).  Expects 200.

        See: https://techdocs.akamai.com/cps/reference/post-post-verification-warnings

        :param enrollment_id: Enrollment identifier.
        :param change_id: Change identifier.
        :param acknowledgement: Acknowledgement value.
        """
        logger.debug("AcknowledgePostVerificationWarnings")

        validation_err = validation.validate_acknowledgement_request(
            enrollment_id, change_id, acknowledgement,
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrAcknowledgePostVerificationWarnings}"
                    f": {errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = (
            f"/cps/v2/enrollments/{enrollment_id}"
            f"/changes/{change_id}"
            "/input/update/post-verification-warnings-ack"
        )
        headers = {
            "Accept": "application/vnd.akamai.cps.change-id.v1+json",
            "Content-Type": (
                "application/vnd.akamai.cps"
                ".acknowledgement.v1+json; charset=utf-8"
            ),
        }
        body = {"acknowledgement": acknowledgement}

        try:
            _, _ = self._session.exec(
                "POST", path,
                body=body,
                headers=headers,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrAcknowledgePostVerificationWarnings}"
                    f": {err.title}"
                ),
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrAcknowledgePostVerificationWarnings}"
                    f": request failed: {err}"
                ),
            ) from err

    # ------------------------------------------------------------------
    # Pre-Verification Warnings (pre_verification_warnings.go)
    # ------------------------------------------------------------------

    def get_change_pre_verification_warnings(
        self, enrollment_id: int, change_id: int,
    ) -> models.PreVerificationWarnings:
        """Get pre-verification warnings for a change.

        Mirrors Go ``CPS.GetChangePreVerificationWarnings``
        (pre_verification_warnings.go).

        See: https://techdocs.akamai.com/cps/reference/get-pre-verification-warnings

        :param enrollment_id: Enrollment identifier.
        :param change_id: Change identifier.
        :returns: Pre-verification warnings.
        """
        logger.debug("GetChangePreVerificationWarnings")

        validation_err = validation.validate_get_change_request(
            enrollment_id, change_id,
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetChangePreVerificationWarnings}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = (
            f"/cps/v2/enrollments/{enrollment_id}"
            f"/changes/{change_id}"
            "/input/info/pre-verification-warnings"
        )
        headers = {
            "Accept": (
                "application/vnd.akamai.cps.warnings.v1+json"
            ),
        }

        try:
            _, result = self._session.exec(
                "GET", path,
                expect_json=True,
                headers=headers,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetChangePreVerificationWarnings}: "
                    f"{err.title}"
                ),
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetChangePreVerificationWarnings}: "
                    f"request failed: {err}"
                ),
            ) from err

        return _build_response(
            models.PreVerificationWarnings, result,
        )

    def acknowledge_pre_verification_warnings(
        self,
        enrollment_id: int,
        change_id: int,
        acknowledgement: str,
    ) -> None:
        """Acknowledge pre-verification warnings.

        Mirrors Go ``CPS.AcknowledgePreVerificationWarnings``
        (pre_verification_warnings.go).
        Accepts status 204, 202, or 200.

        See: https://techdocs.akamai.com/cps/reference/post-pre-verification-warnings

        :param enrollment_id: Enrollment identifier.
        :param change_id: Change identifier.
        :param acknowledgement: Acknowledgement value.
        """
        logger.debug("AcknowledgePreVerificationWarnings")

        validation_err = validation.validate_acknowledgement_request(
            enrollment_id, change_id, acknowledgement,
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrAcknowledgePreVerificationWarnings}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = (
            f"/cps/v2/enrollments/{enrollment_id}"
            f"/changes/{change_id}"
            "/input/update/pre-verification-warnings-ack"
        )
        headers = {
            "Accept": "application/vnd.akamai.cps.change-id.v1+json",
            "Content-Type": (
                "application/vnd.akamai.cps"
                ".acknowledgement.v1+json; charset=utf-8"
            ),
        }
        body = {"acknowledgement": acknowledgement}

        try:
            response, _ = self._session.exec(
                "POST", path,
                body=body,
                headers=headers,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrAcknowledgePreVerificationWarnings}: "
                    f"{err.title}"
                ),
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrAcknowledgePreVerificationWarnings}: "
                    f"request failed: {err}"
                ),
            ) from err

        if response.status_code not in (204, 202, 200):
            raise errors.parse_cps_error(response)

    # ------------------------------------------------------------------
    # Third-Party CSR (third_party_csr.go)
    # ------------------------------------------------------------------

    def get_change_third_party_csr(
        self, enrollment_id: int, change_id: int,
    ) -> models.ThirdPartyCSRResponse:
        """Get the third-party CSR for a change.

        Mirrors Go ``CPS.GetChangeThirdPartyCSR``
        (third_party_csr.go).

        See: https://techdocs.akamai.com/cps/reference/get-third-party-csr

        :param enrollment_id: Enrollment identifier.
        :param change_id: Change identifier.
        :returns: Third-party CSR response.
        """
        logger.debug("GetChangeThirdPartyCSR")

        validation_err = validation.validate_get_change_request(
            enrollment_id, change_id,
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetChangeThirdPartyCSR}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = (
            f"/cps/v2/enrollments/{enrollment_id}"
            f"/changes/{change_id}"
            "/input/info/third-party-csr"
        )
        headers = {
            "Accept": "application/vnd.akamai.cps.csr.v2+json",
        }

        try:
            _, result = self._session.exec(
                "GET", path,
                expect_json=True,
                headers=headers,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetChangeThirdPartyCSR}: {err.title}"
                ),
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrGetChangeThirdPartyCSR}: "
                    f"request failed: {err}"
                ),
            ) from err

        return _build_response(models.ThirdPartyCSRResponse, result)

    def upload_third_party_cert_and_trust_chain(
        self,
        enrollment_id: int,
        change_id: int,
        certificates: models.ThirdPartyCertificates,
    ) -> None:
        """Upload third-party certificate and trust chain.

        Mirrors Go ``CPS.UploadThirdPartyCertAndTrustChain``
        (third_party_csr.go).  Expects 200.

        See: https://techdocs.akamai.com/cps/reference/post-third-party-cert

        :param enrollment_id: Enrollment identifier.
        :param change_id: Change identifier.
        :param certificates: Third-party certificates payload.
        """
        logger.debug("UploadThirdPartyCertAndTrustChain")

        validation_err = (
            validation.validate_upload_third_party_cert_request(
                enrollment_id, change_id, certificates,
            )
        )
        if validation_err is not None:
            raise errors.Error(
                title=(
                    f"{errors.ErrUploadThirdPartyCertAndTrustChain}: "
                    f"{errors.ErrStructValidation}: {validation_err}"
                ),
            )

        path = (
            f"/cps/v2/enrollments/{enrollment_id}"
            f"/changes/{change_id}"
            "/input/update/third-party-cert-and-trust-chain"
        )
        headers = {
            "Accept": "application/vnd.akamai.cps.change-id.v1+json",
            "Content-Type": (
                "application/vnd.akamai.cps"
                ".certificate-and-trust-chain.v2+json; charset=utf-8"
            ),
        }

        try:
            _, _ = self._session.exec(
                "POST", path,
                body=_model_to_dict(certificates),
                headers=headers,
                error_parser=errors.parse_cps_error,
            )
        except errors.Error as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrUploadThirdPartyCertAndTrustChain}: "
                    f"{err.title}"
                ),
                detail=err.detail,
                status_code=err.status_code,
            ) from err
        except Exception as err:
            raise errors.Error(
                title=(
                    f"{errors.ErrUploadThirdPartyCertAndTrustChain}: "
                    f"request failed: {err}"
                ),
            ) from err

    # ------------------------------------------------------------------
    # Utility (location_url.go)
    # ------------------------------------------------------------------

    @staticmethod
    def get_id_from_location(location: str) -> int:
        """Parse the link and return the ID from its last path segment.

        Mirrors Go ``GetIDFromLocation`` (location_url.go).

        :param location: URL (e.g.
            ``/cps/v2/enrollments/12345``) from which the trailing
            integer identifier is extracted.
        :returns: The parsed integer identifier.
        :raises ValueError: If the last path segment cannot be
            converted to an integer.
        """
        parsed = urlparse(location)
        path_parts = parsed.path.rstrip("/").split("/")
        return int(path_parts[-1])
