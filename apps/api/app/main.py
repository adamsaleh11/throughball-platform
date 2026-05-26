import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.middleware.observability import (
    ObservabilityMiddleware,
    OpenTelemetryPlaceholderMiddleware,
)
from app.models.health import HealthResponse, ObservabilityMeta
from app.routes.profile import router as profile_router


settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ObservabilityMiddleware)
app.add_middleware(OpenTelemetryPlaceholderMiddleware)
app.include_router(profile_router)


@app.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    started_at = getattr(request.state, "started_at", time.perf_counter())
    return HealthResponse(
        status="OK",
        meta=ObservabilityMeta(
            request_id=request.state.request_id,
            trace_id=request.state.trace_id,
            latency_ms=int((time.perf_counter() - started_at) * 1000),
            retries=request.state.retries,
            degraded=request.state.degraded,
        ),
    )
