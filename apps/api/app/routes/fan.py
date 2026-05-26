import time
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.core.auth import AuthValidationError, SupabaseJwtValidator
from app.core.fan import (
    CheckinHistoryQuery,
    CreateCheckinCommand,
    FanService,
    FanStorageError,
    HotspotQuery,
    get_default_fan_service,
)
from app.core.profile import AuthenticatedUser


router = APIRouter()
auth_validator = SupabaseJwtValidator()


class CreateCheckinRequest(BaseModel):
    city_id: UUID
    match_id: Optional[UUID] = None
    venue_id: Optional[UUID] = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    checked_in_at: Optional[str] = None
    visibility: str = "private"

    model_config = ConfigDict(extra="ignore")

    def to_command(self) -> CreateCheckinCommand:
        return CreateCheckinCommand(
            city_id=self.city_id,
            match_id=self.match_id,
            venue_id=self.venue_id,
            latitude=self.latitude,
            longitude=self.longitude,
            checked_in_at=self.checked_in_at,
        )


def response_meta(request: Request) -> dict[str, Any]:
    started_at = getattr(request.state, "started_at", time.perf_counter())
    return {
        "request_id": request.state.request_id,
        "trace_id": request.state.trace_id,
        "latency_ms": int((time.perf_counter() - started_at) * 1000),
        "retries": request.state.retries,
        "degraded": request.state.degraded,
    }


def unauthorized(request: Request, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": {
                "code": "UNAUTHORIZED",
                "message": message,
            },
            "meta": response_meta(request),
        },
    )


def storage_error(request: Request, error: FanStorageError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": "FAN_STORAGE_UNAVAILABLE",
                "message": str(error),
            },
            "meta": response_meta(request),
        },
    )


def get_fan_service() -> FanService:
    return get_default_fan_service()


async def get_current_user(authorization: str = Header(default="")) -> Optional[AuthenticatedUser]:
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme != "Bearer" or not token:
        return None

    try:
        user = await auth_validator.validate(token)
        return AuthenticatedUser(user_id=user["user_id"], access_token=user["access_token"])
    except AuthValidationError:
        return None


@router.post("/fan/checkins")
async def create_checkin(
    payload: CreateCheckinRequest,
    request: Request,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user),
    fan_service: FanService = Depends(get_fan_service),
) -> JSONResponse:
    if current_user is None:
        authorization = request.headers.get("authorization", "")
        if authorization:
            return unauthorized(request, "Invalid bearer token.")
        return unauthorized(request, "Missing bearer token.")

    if payload.visibility != "private":
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "INVALID_CHECKIN_VISIBILITY",
                    "message": "Only private check-ins are supported.",
                },
                "meta": response_meta(request),
            },
        )

    try:
        checkin = await fan_service.create_checkin(current_user, payload.to_command())
    except FanStorageError as error:
        return storage_error(request, error)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "checkin": checkin,
            "meta": response_meta(request),
        },
    )


@router.get("/fan/checkins/me")
async def my_checkins(
    request: Request,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user),
    fan_service: FanService = Depends(get_fan_service),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> JSONResponse:
    if current_user is None:
        authorization = request.headers.get("authorization", "")
        if authorization:
            return unauthorized(request, "Invalid bearer token.")
        return unauthorized(request, "Missing bearer token.")

    try:
        payload = await fan_service.checkins_for_user(
            current_user,
            CheckinHistoryQuery(page=page, page_size=page_size),
        )
    except FanStorageError as error:
        return storage_error(request, error)

    return JSONResponse(content={**payload, "meta": response_meta(request)})


@router.get("/cities/{city_id}/hotspots")
async def city_hotspots(
    city_id: UUID,
    request: Request,
    match_id: Optional[UUID] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    fan_service: FanService = Depends(get_fan_service),
) -> JSONResponse:
    try:
        payload = await fan_service.hotspots(
            HotspotQuery(city_id=city_id, match_id=match_id, page=page, page_size=page_size)
        )
    except FanStorageError as error:
        return storage_error(request, error)

    return JSONResponse(content={**payload, "meta": response_meta(request)})
