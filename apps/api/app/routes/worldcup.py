import time
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse

from app.core.worldcup import SupabaseWorldCupService, WorldCupStorageError


router = APIRouter()


def response_meta(request: Request) -> dict[str, Any]:
    started_at = getattr(request.state, "started_at", time.perf_counter())
    return {
        "request_id": request.state.request_id,
        "trace_id": request.state.trace_id,
        "latency_ms": int((time.perf_counter() - started_at) * 1000),
        "retries": request.state.retries,
        "degraded": request.state.degraded,
    }


def storage_error(request: Request, error: WorldCupStorageError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": "WORLDCUP_STORAGE_UNAVAILABLE",
                "message": str(error),
            },
            "meta": response_meta(request),
        },
    )


class WorldCupService:
    async def list_cities(self) -> list[dict[str, Any]]:
        raise NotImplementedError("World Cup service is not configured.")

    async def list_matches(
        self,
        city_id: Optional[str],
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        raise NotImplementedError("World Cup service is not configured.")


def get_worldcup_service() -> WorldCupService:
    return SupabaseWorldCupService()


@router.get("/cities")
async def list_cities(
    request: Request,
    worldcup_service: WorldCupService = Depends(get_worldcup_service),
) -> JSONResponse:
    try:
        cities = await worldcup_service.list_cities()
    except WorldCupStorageError as error:
        return storage_error(request, error)

    return JSONResponse(
        content={
            "cities": cities,
            "meta": response_meta(request),
        },
    )


@router.get("/matches")
async def list_matches(
    request: Request,
    city_id: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    worldcup_service: WorldCupService = Depends(get_worldcup_service),
) -> JSONResponse:
    try:
        payload = await worldcup_service.list_matches(city_id, page, page_size)
    except WorldCupStorageError as error:
        return storage_error(request, error)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            **payload,
            "meta": response_meta(request),
        },
    )
