import time
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.core.auth import AuthValidationError, SupabaseJwtValidator
from app.core.itineraries import (
    ItineraryInputCommand,
    ItineraryHistoryQuery,
    ItineraryItemCommand,
    ItineraryService,
    ItineraryStorageError,
    SaveItineraryCommand,
    get_default_itinerary_service,
)
from app.core.profile import AuthenticatedUser


router = APIRouter()
auth_validator = SupabaseJwtValidator()


class ItineraryInputRequest(BaseModel):
    city_id: UUID
    match_id: Optional[UUID] = None
    date: Optional[str] = None
    party_size: int = Field(ge=1, le=20)
    interests: list[str] = Field(default_factory=list, max_length=20)
    pace: str = "balanced"

    model_config = ConfigDict(extra="ignore")

    def to_command(self) -> ItineraryInputCommand:
        return ItineraryInputCommand(
            city_id=self.city_id,
            match_id=self.match_id,
            date=self.date,
            party_size=self.party_size,
            interests=self.interests,
            pace=self.pace,
        )


class ItineraryItemRequest(BaseModel):
    position: int = Field(ge=1)
    item_type: str = Field(max_length=50)
    source_table: Optional[str] = Field(default=None, max_length=80)
    source_id: Optional[UUID] = None
    title: str = Field(max_length=160)
    description: Optional[str] = Field(default=None, max_length=1500)
    starts_at: Optional[str] = None
    ends_at: Optional[str] = None
    area_label: Optional[str] = Field(default=None, max_length=120)
    route_context: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="ignore")

    def to_command(self) -> ItineraryItemCommand:
        return ItineraryItemCommand(
            position=self.position,
            item_type=self.item_type,
            source_table=self.source_table,
            source_id=self.source_id,
            title=self.title,
            description=self.description,
            starts_at=self.starts_at,
            ends_at=self.ends_at,
            area_label=self.area_label,
            route_context=self.route_context,
        )


class ItineraryPayloadRequest(BaseModel):
    title: str = Field(max_length=120)
    summary: Optional[str] = Field(default=None, max_length=1000)
    items: list[ItineraryItemRequest] = Field(default_factory=list, max_length=50)

    model_config = ConfigDict(extra="ignore")


class SaveItineraryRequest(BaseModel):
    input: ItineraryInputRequest
    itinerary: ItineraryPayloadRequest

    model_config = ConfigDict(extra="ignore")

    def to_command(self) -> SaveItineraryCommand:
        return SaveItineraryCommand(
            input=self.input.to_command(),
            title=self.itinerary.title,
            summary=self.itinerary.summary,
            items=[item.to_command() for item in self.itinerary.items],
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


def storage_error(request: Request, error: ItineraryStorageError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": "ITINERARY_STORAGE_UNAVAILABLE",
                "message": str(error),
            },
            "meta": response_meta(request),
        },
    )


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


def get_itinerary_service() -> ItineraryService:
    return get_default_itinerary_service()


@router.post("/itineraries/generate")
async def generate_itinerary(
    request: Request,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user),
) -> JSONResponse:
    if current_user is None:
        authorization = request.headers.get("authorization", "")
        if authorization:
            return unauthorized(request, "Invalid bearer token.")
        return unauthorized(request, "Missing bearer token.")

    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "error": {
                "code": "ITINERARY_GENERATION_NOT_IMPLEMENTED",
                "message": "Itinerary generation is not implemented until Phase 06.",
                "details": {
                    "phase": "Phase 06",
                    "contract": "POST /itineraries/save accepts generated itinerary payloads for persistence.",
                },
            },
            "meta": response_meta(request),
        },
    )


@router.post("/itineraries/save")
async def save_itinerary(
    payload: SaveItineraryRequest,
    request: Request,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user),
    itinerary_service: ItineraryService = Depends(get_itinerary_service),
) -> JSONResponse:
    if current_user is None:
        authorization = request.headers.get("authorization", "")
        if authorization:
            return unauthorized(request, "Invalid bearer token.")
        return unauthorized(request, "Missing bearer token.")

    try:
        saved = await itinerary_service.save_itinerary(current_user, payload.to_command())
    except ItineraryStorageError as error:
        return storage_error(request, error)

    return JSONResponse(
        status_code=status.HTTP_200_OK if saved.get("reused") else status.HTTP_201_CREATED,
        content={**saved, "meta": response_meta(request)},
    )


@router.get("/itineraries/me")
async def my_itineraries(
    request: Request,
    current_user: Optional[AuthenticatedUser] = Depends(get_current_user),
    itinerary_service: ItineraryService = Depends(get_itinerary_service),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> JSONResponse:
    if current_user is None:
        authorization = request.headers.get("authorization", "")
        if authorization:
            return unauthorized(request, "Invalid bearer token.")
        return unauthorized(request, "Missing bearer token.")

    try:
        payload = await itinerary_service.itineraries_for_user(
            current_user,
            ItineraryHistoryQuery(page=page, page_size=page_size),
        )
    except ItineraryStorageError as error:
        return storage_error(request, error)

    return JSONResponse(content={**payload, "meta": response_meta(request)})
