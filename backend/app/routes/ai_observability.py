"""
Phase 7 – Observability & Operational Controls

AI OBSERVABILITY API ROUTES

This module provides read-only REST APIs for AI system observability.

PHASE 7 SCOPE:
- Read-only health and metrics endpoints
- Per-camera metrics endpoints
- Per-model health endpoints
- System-wide AI health aggregation

WHAT THIS IS:
- Read-only observability APIs
- HTTP GET endpoints only
- Best-effort metrics exposure
- Non-blocking health checks

WHAT THIS IS NOT:
- Control/command APIs (no POST/PUT/DELETE for health management)
- Configuration endpoints
- Alerting APIs
- Auto-restart or remediation endpoints

CRITICAL CONSTRAINTS:
- All endpoints are GET only (read-only)
- All errors return graceful degraded responses
- No blocking or synchronous dependencies
- No cascading failures
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Path as FastAPIPath
from fastapi.responses import JSONResponse

from ..schemas.ai_health import (
    AISystemHealth,
    CameraMetrics,
    ModelContainerHealth,
)
from ..services.ai_health_service import AIHealthService

# Create router for AI observability endpoints
router = APIRouter(prefix="/ai/observability", tags=["AI Observability"])

# Initialize health service
# NOTE: This is a module-level singleton for simplicity
# In production, could use dependency injection
_health_service = AIHealthService()


@router.get(
    "/health",
    response_model=AISystemHealth,
    summary="Get overall AI system health",
    description="""
Phase 7: Get overall AI system health status and metrics.

Returns aggregated health across all cameras and model containers.

**Read-only endpoint** - provides operational visibility without affecting system behavior.

**Best-effort semantics**:
- Missing metrics are acceptable
- Stale data may be returned
- Errors result in degraded status
"""
)
async def get_system_health() -> AISystemHealth:
    """
    Phase 7: Get overall AI system health.

    Returns:
        AISystemHealth: System-wide health status and metrics
    """
    try:
        return _health_service.get_system_health()
    except Exception:
        # Phase 7: Silent failure - return degraded status
        from datetime import datetime
        return AISystemHealth(
            status="unknown",
            timestamp=datetime.utcnow().isoformat() + "Z",
            camera_count=0,
            model_count=0,
            cameras=[],
            models=[]
        )


@router.get(
    "/models/{model_id}/health",
    response_model=ModelContainerHealth,
    summary="Get model container health",
    description="""
Phase 7: Get health status for a specific model container.

Returns liveness, metrics, and performance data for the model container.

**Read-only endpoint** - provides operational visibility without affecting inference.

**Best-effort semantics**:
- Returns 404 if model not found or heartbeat missing
- Stale heartbeat indicates degraded status
- Errors result in 500 with degraded status
"""
)
async def get_model_health(
    model_id: str = FastAPIPath(..., description="Model identifier (e.g., 'yolov8n')")
) -> ModelContainerHealth:
    """
    Phase 7: Get health status for a specific model container.

    Args:
        model_id: Model identifier

    Returns:
        ModelContainerHealth: Model health status and metrics

    Raises:
        HTTPException 404: If model not found or heartbeat missing
    """
    try:
        health = _health_service.get_model_health(model_id)
        if health is None:
            raise HTTPException(
                status_code=404,
                detail=f"Model '{model_id}' not found or heartbeat missing"
            )
        return health
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Phase 7: Silent failure - return 500 with error detail
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get model health: {str(e)}"
        )


@router.get(
    "/cameras/{camera_id}/metrics",
    response_model=CameraMetrics,
    summary="Get camera AI metrics",
    description="""
Phase 7: Get AI metrics for a specific camera.

Returns per-subscription dispatch/drop metrics and StreamAgent state.

**Read-only endpoint** - provides operational visibility without affecting video pipeline.

**Best-effort semantics**:
- Returns 404 if camera not found or StreamAgent not integrated
- Missing metrics are acceptable
- Errors result in 500 with error detail

**NOTE**: This endpoint requires StreamAgent integration with VAS backend.
Currently returns 404 as StreamAgents are not yet integrated.
"""
)
async def get_camera_metrics(
    camera_id: str = FastAPIPath(..., description="Camera identifier (e.g., 'camera_1')")
) -> CameraMetrics:
    """
    Phase 7: Get AI metrics for a specific camera.

    Args:
        camera_id: Camera identifier

    Returns:
        CameraMetrics: Camera AI metrics and subscription data

    Raises:
        HTTPException 404: If camera not found or StreamAgent not integrated
        HTTPException 501: If StreamAgent integration not yet available
    """
    try:
        metrics = _health_service.get_camera_metrics(camera_id)
        if metrics is None:
            # TODO: Remove this when StreamAgent integration is complete
            raise HTTPException(
                status_code=501,
                detail="StreamAgent integration not yet available. Camera metrics coming in future phase."
            )
        return metrics
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Phase 7: Silent failure - return 500 with error detail
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get camera metrics: {str(e)}"
        )


@router.get(
    "/models",
    summary="List all model containers",
    description="""
Phase 7: List all active model containers with health status.

Returns a list of all model containers that have emitted heartbeats.

**Read-only endpoint** - provides operational visibility without affecting inference.

**Best-effort semantics**:
- Missing containers are silently omitted
- Stale heartbeats indicate degraded status
- Errors result in empty list
"""
)
async def list_models() -> JSONResponse:
    """
    Phase 7: List all model containers.

    Returns:
        List of model IDs and health statuses
    """
    try:
        system_health = _health_service.get_system_health()
        models = [
            {
                "model_id": model.model_id,
                "status": model.status,
                "last_heartbeat": model.last_heartbeat
            }
            for model in system_health.models
        ]
        return JSONResponse(content={"models": models})
    except Exception:
        # Phase 7: Silent failure - return empty list
        return JSONResponse(content={"models": []})


@router.get(
    "/cameras",
    summary="List all cameras with AI subscriptions",
    description="""
Phase 7: List all cameras that have AI model subscriptions.

Returns a list of all cameras with StreamAgent state and subscription counts.

**Read-only endpoint** - provides operational visibility without affecting video pipeline.

**Best-effort semantics**:
- Missing cameras are silently omitted
- Errors result in empty list

**NOTE**: This endpoint requires StreamAgent integration with VAS backend.
Currently returns empty list as StreamAgents are not yet integrated.
"""
)
async def list_cameras() -> JSONResponse:
    """
    Phase 7: List all cameras with AI subscriptions.

    Returns:
        List of camera IDs and subscription counts
    """
    try:
        system_health = _health_service.get_system_health()
        cameras = [
            {
                "camera_id": camera.camera_id,
                "state": camera.state,
                "subscription_count": camera.subscription_count
            }
            for camera in system_health.cameras
        ]
        return JSONResponse(content={"cameras": cameras})
    except Exception:
        # Phase 7: Silent failure - return empty list
        return JSONResponse(content={"cameras": []})
