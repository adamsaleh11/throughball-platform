from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.core.auth import (
    AuthValidationError,
    ProfileStorageError,
    SupabaseJwtValidator,
    SupabaseProfileService,
)


router = APIRouter()
ALLOWED_MATCH_TAGS = {"rivalry", "high_press", "underdog", "knockout", "fan_festival"}
auth_validator = SupabaseJwtValidator()


class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(default=None, max_length=50)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    home_city_id: Optional[UUID] = None
    preferred_match_tags: list[str] = Field(default_factory=list, max_length=20)
    favorite_team_ids: list[UUID] = Field(default_factory=list, max_length=10)

    model_config = ConfigDict(extra="ignore")

    @property
    def completed(self) -> bool:
        return bool(self.display_name and (self.home_city_id or self.favorite_team_ids))

    def service_payload(self) -> dict[str, Any]:
        return {
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "home_city_id": str(self.home_city_id) if self.home_city_id else None,
            "preferred_match_tags": self.preferred_match_tags,
            "favorite_team_ids": [str(team_id) for team_id in self.favorite_team_ids],
            "profile_completed": self.completed,
        }


def response_meta(request: Request) -> dict[str, Any]:
    return {
        "request_id": request.state.request_id,
        "trace_id": request.state.trace_id,
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


def storage_error(request: Request, error: ProfileStorageError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": "PROFILE_STORAGE_UNAVAILABLE",
                "message": str(error),
            },
            "meta": response_meta(request),
        },
    )


class ProfileService:
    async def get_profile(self, user_id: str, access_token: str) -> dict[str, Any]:
        raise NotImplementedError("Supabase profile service is not configured.")

    async def update_profile(
        self,
        user_id: str,
        access_token: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError("Supabase profile service is not configured.")


def get_profile_service() -> ProfileService:
    return SupabaseProfileService()


async def get_current_user(authorization: str = Header(default="")) -> Optional[dict[str, str]]:
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme != "Bearer" or not token:
        return None

    try:
        return await auth_validator.validate(token)
    except AuthValidationError:
        return None


@router.get("/me/profile")
async def get_profile(
    request: Request,
    current_user: Optional[dict[str, str]] = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
) -> JSONResponse:
    if current_user is None:
        authorization = request.headers.get("authorization", "")
        if authorization:
            return unauthorized(request, "Invalid bearer token.")
        return unauthorized(request, "Missing bearer token.")

    try:
        profile_payload = await profile_service.get_profile(
            current_user["user_id"],
            current_user["access_token"],
        )
    except ProfileStorageError as error:
        return storage_error(request, error)
    return JSONResponse(
        content={
            **profile_payload,
            "meta": response_meta(request),
        },
    )


@router.put("/me/profile")
async def update_profile(
    payload: ProfileUpdateRequest,
    request: Request,
    current_user: Optional[dict[str, str]] = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
) -> JSONResponse:
    if current_user is None:
        authorization = request.headers.get("authorization", "")
        if authorization:
            return unauthorized(request, "Invalid bearer token.")
        return unauthorized(request, "Missing bearer token.")

    invalid_tags = set(payload.preferred_match_tags) - ALLOWED_MATCH_TAGS
    if invalid_tags:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Unsupported preferred match tag.",
                },
                "meta": response_meta(request),
            },
        )

    try:
        profile_payload = await profile_service.update_profile(
            current_user["user_id"],
            current_user["access_token"],
            payload.service_payload(),
        )
    except ProfileStorageError as error:
        return storage_error(request, error)
    return JSONResponse(
        content={
            **profile_payload,
            "meta": response_meta(request),
        },
    )
