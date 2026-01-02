"""
Phase 7 – Observability & Operational Controls

AI HEALTH AND METRICS SCHEMAS

This module defines Pydantic schemas for AI system observability.

PHASE 7 SCOPE:
- Read-only health and metrics data models
- Per-camera metrics schemas
- Per-model container health schemas
- System-wide AI health aggregation

WHAT THIS IS:
- Data transfer objects for observability APIs
- Read-only health status representations
- Metrics aggregation schemas

WHAT THIS IS NOT:
- Writable configuration schemas
- Control/command schemas
- Alerting configuration
- Automatic action triggers
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class SubscriptionMetrics(BaseModel):
    """
    Phase 7: Per-subscription (camera + model) metrics.

    Represents operational metrics for one model subscribed to one camera.
    """

    camera_id: str = Field(..., description="Camera identifier")
    model_id: str = Field(..., description="Model identifier")
    active: bool = Field(..., description="Subscription active status")
    dispatch_count: int = Field(..., description="Total frames dispatched to model", ge=0)
    drop_count: int = Field(..., description="Total frames dropped (skipped)", ge=0)
    last_dispatch_time: Optional[str] = Field(None, description="ISO timestamp of last dispatch")
    last_dispatched_frame_id: Optional[int] = Field(None, description="Frame ID of last dispatch")

    class Config:
        json_schema_extra = {
            "example": {
                "camera_id": "camera_1",
                "model_id": "yolov8n",
                "active": True,
                "dispatch_count": 1250,
                "drop_count": 450,
                "last_dispatch_time": "2026-01-02T10:30:45.123Z",
                "last_dispatched_frame_id": 1700
            }
        }


class CameraMetrics(BaseModel):
    """
    Phase 7: Per-camera AI metrics.

    Aggregates metrics for all model subscriptions on a camera.
    """

    camera_id: str = Field(..., description="Camera identifier")
    state: str = Field(..., description="StreamAgent state (CREATED, RUNNING, STOPPED)")
    subscription_count: int = Field(..., description="Number of active model subscriptions", ge=0)
    subscriptions: List[SubscriptionMetrics] = Field(default_factory=list, description="Per-subscription metrics")

    class Config:
        json_schema_extra = {
            "example": {
                "camera_id": "camera_1",
                "state": "RUNNING",
                "subscription_count": 2,
                "subscriptions": [
                    {
                        "camera_id": "camera_1",
                        "model_id": "yolov8n",
                        "active": True,
                        "dispatch_count": 1250,
                        "drop_count": 450,
                        "last_dispatch_time": "2026-01-02T10:30:45.123Z",
                        "last_dispatched_frame_id": 1700
                    }
                ]
            }
        }


class ModelContainerMetrics(BaseModel):
    """
    Phase 7: Per-model container metrics.

    Represents inference performance metrics for a model container.
    """

    total_requests: int = Field(..., description="Total inference requests processed", ge=0)
    total_errors: int = Field(..., description="Total failed inferences", ge=0)
    avg_latency_ms: float = Field(..., description="Average inference latency (milliseconds)", ge=0.0)
    uptime_seconds: int = Field(..., description="Container uptime in seconds", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "total_requests": 5432,
                "total_errors": 12,
                "avg_latency_ms": 45.2,
                "uptime_seconds": 7200
            }
        }


class ModelContainerHealth(BaseModel):
    """
    Phase 7: Per-model container health status.

    Represents the operational health of a model container.
    """

    model_id: str = Field(..., description="Model identifier")
    status: str = Field(..., description="Health status: healthy, degraded, unknown")
    last_heartbeat: Optional[str] = Field(None, description="ISO timestamp of last heartbeat")
    metrics: ModelContainerMetrics = Field(..., description="Container performance metrics")

    class Config:
        json_schema_extra = {
            "example": {
                "model_id": "yolov8n",
                "status": "healthy",
                "last_heartbeat": "2026-01-02T10:30:50.123Z",
                "metrics": {
                    "total_requests": 5432,
                    "total_errors": 12,
                    "avg_latency_ms": 45.2,
                    "uptime_seconds": 7200
                }
            }
        }


class AISystemHealth(BaseModel):
    """
    Phase 7: Overall AI system health.

    Aggregates health status across all cameras and models.
    """

    status: str = Field(..., description="Overall system status: healthy, degraded, unknown")
    timestamp: str = Field(..., description="ISO timestamp of health check")
    camera_count: int = Field(..., description="Number of cameras with AI subscriptions", ge=0)
    model_count: int = Field(..., description="Number of active model containers", ge=0)
    cameras: List[CameraMetrics] = Field(default_factory=list, description="Per-camera metrics")
    models: List[ModelContainerHealth] = Field(default_factory=list, description="Per-model container health")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2026-01-02T10:30:55.123Z",
                "camera_count": 3,
                "model_count": 2,
                "cameras": [],
                "models": []
            }
        }
