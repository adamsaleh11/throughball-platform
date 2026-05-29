import time
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse

from app.core.city_guide import (
    CityGuideNotFoundError,
    CityGuideService,
    CityGuideStorageError,
    EventGuideQuery,
    GuideQuery,
    get_default_city_guide_service,
)
from app.models.city_guide import CityDetailResponse


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


def get_city_guide_service() -> CityGuideService:
    return get_default_city_guide_service()


def not_found_error(request: Request, error: CityGuideNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "code": error.code,
                "message": str(error),
            },
            "meta": response_meta(request),
        },
    )


def storage_error(request: Request, error: CityGuideStorageError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": "CITY_GUIDE_STORAGE_UNAVAILABLE",
                "message": str(error),
            },
            "meta": response_meta(request),
        },
    )


@router.get("/cities/{city_id}", response_model=CityDetailResponse)
async def get_city(
    city_id: str,
    request: Request,
    city_guide: CityGuideService = Depends(get_city_guide_service),
) -> JSONResponse:
    try:
        payload = await city_guide.city(city_id)
    except CityGuideNotFoundError as error:
        return not_found_error(request, error)
    except CityGuideStorageError as error:
        return storage_error(request, error)

    return JSONResponse(content={**payload, "meta": response_meta(request)})


@router.get("/cities/{city_id}/venues")
async def list_city_venues(
    city_id: str,
    request: Request,
    venue_type: Optional[str] = None,
    area_label: Optional[str] = None,
    amenity: Optional[str] = None,
    tag: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    city_guide: CityGuideService = Depends(get_city_guide_service),
) -> JSONResponse:
    try:
        payload = await city_guide.venues(
            GuideQuery(
                city_id=city_id,
                item_type=venue_type,
                area_label=area_label,
                amenity=amenity,
                tag=tag,
                page=page,
                page_size=page_size,
            )
        )
    except CityGuideNotFoundError as error:
        return not_found_error(request, error)
    except CityGuideStorageError as error:
        return storage_error(request, error)

    return JSONResponse(content={**payload, "meta": response_meta(request)})


@router.get("/cities/{city_id}/events")
async def list_city_events(
    city_id: str,
    request: Request,
    event_type: Optional[str] = None,
    starts_after: Optional[str] = None,
    starts_before: Optional[str] = None,
    tag: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    city_guide: CityGuideService = Depends(get_city_guide_service),
) -> JSONResponse:
    try:
        payload = await city_guide.events(
            EventGuideQuery(
                city_id=city_id,
                event_type=event_type,
                starts_after=starts_after,
                starts_before=starts_before,
                tag=tag,
                page=page,
                page_size=page_size,
            )
        )
    except CityGuideNotFoundError as error:
        return not_found_error(request, error)
    except CityGuideStorageError as error:
        return storage_error(request, error)

    return JSONResponse(content={**payload, "meta": response_meta(request)})


@router.get("/cities/{city_id}/tourist-spots")
async def list_city_tourist_spots(
    city_id: str,
    request: Request,
    spot_type: Optional[str] = None,
    area_label: Optional[str] = None,
    tag: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    city_guide: CityGuideService = Depends(get_city_guide_service),
) -> JSONResponse:
    try:
        payload = await city_guide.tourist_spots(
            GuideQuery(
                city_id=city_id,
                item_type=spot_type,
                area_label=area_label,
                tag=tag,
                page=page,
                page_size=page_size,
            )
        )
    except CityGuideNotFoundError as error:
        return not_found_error(request, error)
    except CityGuideStorageError as error:
        return storage_error(request, error)

    return JSONResponse(content={**payload, "meta": response_meta(request)})


@router.get("/cities/{city_id}/transport-hubs")
async def list_city_transport_hubs(
    city_id: str,
    request: Request,
    hub_type: Optional[str] = None,
    area_label: Optional[str] = None,
    tag: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    city_guide: CityGuideService = Depends(get_city_guide_service),
) -> JSONResponse:
    try:
        payload = await city_guide.transport_hubs(
            GuideQuery(
                city_id=city_id,
                item_type=hub_type,
                area_label=area_label,
                tag=tag,
                page=page,
                page_size=page_size,
            )
        )
    except CityGuideNotFoundError as error:
        return not_found_error(request, error)
    except CityGuideStorageError as error:
        return storage_error(request, error)

    return JSONResponse(content={**payload, "meta": response_meta(request)})
