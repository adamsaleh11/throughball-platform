from pydantic import BaseModel


class ObservabilityMeta(BaseModel):
    request_id: str
    trace_id: str
    latency_ms: int
    retries: int
    degraded: bool


class HealthResponse(BaseModel):
    status: str
    meta: ObservabilityMeta
