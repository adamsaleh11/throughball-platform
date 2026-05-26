from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.core.auth import (
    AuthValidationError,
    SupabaseJwtValidator,
)
from app.core.profile import (
    AuthenticatedUser,
    ProfilePersistence,
    ProfileStorageError,
    ProfileUpdateCommand,
    SupabaseProfilePersistence,
)


router = APIRouter()

auth_validator = SupabaseJwtValidator()


class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(default=None, max_length=50)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    home_city_id: Optional[UUID] = None
    preferred_match_tags: list[str] = Field(default_factory=list, max_length=20)
    favorite_team_ids: list[UUID] = Field(default_factory=list, max_length=10)

    model_config = ConfigDict(extra="ignore")

    def to_command(self) -> ProfileUpdateCommand:
        return ProfileUpdateCommand(
            display_name=self.display_name,
            avatar_url=self.avatar_url,
            home_city_id=self.home_city_id,
            preferred_match_tags=self.preferred_match_tags,
            favorite_team_ids=self.favorite_team_ids,
        )


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


def get_profile_persistence() -> ProfilePersistence:
    return SupabaseProfilePersistence()


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


@router.get("/me/profile")
async def get_profile(
    request: Request,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user),
    profile_persistence: ProfilePersistence = Depends(get_profile_persistence),
) -> JSONResponse:
    if current_user is None:
        authorization = request.headers.get("authorization", "")
        if authorization:
            return unauthorized(request, "Invalid bearer token.")
        return unauthorized(request, "Missing bearer token.")

    try:
        profile_payload = await profile_persistence.current_profile(current_user)
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
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user),
    profile_persistence: ProfilePersistence = Depends(get_profile_persistence),
) -> JSONResponse:
    if current_user is None:
        authorization = request.headers.get("authorization", "")
        if authorization:
            return unauthorized(request, "Invalid bearer token.")
        return unauthorized(request, "Missing bearer token.")

    try:
        profile_payload = await profile_persistence.save_current_profile(
            current_user,
            payload.to_command(),
        )
    except ProfileStorageError as error:
        return storage_error(request, error)
    return JSONResponse(
        content={
            **profile_payload,
            "meta": response_meta(request),
        },
    )
