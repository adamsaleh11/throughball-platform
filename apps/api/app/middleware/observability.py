import json
import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger("throughball.api")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start = time.perf_counter()
        request_id = request.headers.get("x-request-id", f"req_{uuid.uuid4().hex}")
        trace_id = request.headers.get("x-trace-id", f"trc_{uuid.uuid4().hex}")
        request.state.started_at = start
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        request.state.retries = 0
        request.state.degraded = False

        response = await call_next(request)
        latency_ms = int((time.perf_counter() - start) * 1000)

        response.headers["x-request-id"] = request_id
        response.headers["x-trace-id"] = trace_id
        response.headers["x-latency-ms"] = str(latency_ms)

        logger.info(
            json.dumps(
                {
                    "event": "request_completed",
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "request_id": request_id,
                    "trace_id": trace_id,
                    "latency_ms": latency_ms,
                    "retries": request.state.retries,
                    "degraded": request.state.degraded,
                }
            )
        )
        return response


class OpenTelemetryPlaceholderMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        return await call_next(request)
