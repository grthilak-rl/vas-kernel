"""AI Event API routes (Phase 5.3: Read-only Backend APIs).

This module provides read-only HTTP endpoints for querying AI events
persisted in Phase 5.1.

Phase 5.3 Constraints:
- Read-only operations (no writes, updates, or deletes)
- Safe defaults (bounded limits, predictable ordering)
- No aggregations or analytics
- No side effects
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from uuid import UUID
from loguru import logger

from database import get_db
from app.services.ai_event_service import AIEventService
from app.schemas.ai_event import AIEventResponse, AIEventListResponse


router = APIRouter(prefix="/api/v1/ai-events", tags=["ai-events"])

# Service instance
ai_event_service = AIEventService()


@router.get("/{event_id}", response_model=AIEventResponse)
async def get_ai_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a single AI event by ID (Phase 5.3: Read-only).

    Args:
        event_id: AI event UUID
        db: Database session (injected)

    Returns:
        AIEventResponse with event details

    Raises:
        HTTPException: 404 if event not found

    Phase 5.3 Constraints:
    - Read-only operation
    - No side effects
    """
    try:
        event = await ai_event_service.get_event(event_id, db)

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI event {event_id} not found"
            )

        return AIEventResponse.from_orm(event)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get AI event {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve AI event: {str(e)}"
        )


@router.get("", response_model=AIEventListResponse)
async def list_ai_events(
    camera_id: Optional[UUID] = Query(None, description="Filter by camera/device UUID"),
    model_id: Optional[str] = Query(None, description="Filter by model identifier"),
    start_time: Optional[datetime] = Query(None, description="Filter by start time (ISO 8601)"),
    end_time: Optional[datetime] = Query(None, description="Filter by end time (ISO 8601)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results (1-1000)"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db)
):
    """List AI events with optional filtering and pagination (Phase 5.3: Read-only).

    Query parameters:
        camera_id: Optional UUID to filter by camera
        model_id: Optional string to filter by model
        start_time: Optional ISO 8601 datetime for range start (inclusive)
        end_time: Optional ISO 8601 datetime for range end (inclusive)
        limit: Maximum results to return (default 100, max 1000)
        offset: Number of results to skip (default 0)

    Returns:
        AIEventListResponse with:
        - events: List of AI events (ordered by timestamp DESC)
        - total: Total count matching filters
        - limit: Limit applied to this query
        - offset: Offset applied to this query

    Phase 5.3 Constraints:
    - Read-only operation
    - Safe defaults (limit capped at 1000)
    - Ordered by timestamp DESC (newest first)
    - No aggregations or analytics

    Example:
        GET /api/v1/ai-events?camera_id=abc123&limit=50
        GET /api/v1/ai-events?model_id=yolov8-person-detection&start_time=2024-01-01T00:00:00Z
    """
    try:
        # Get total count (for pagination metadata)
        total = await ai_event_service.count_events(
            db=db,
            camera_id=camera_id,
            model_id=model_id,
            start_time=start_time,
            end_time=end_time
        )

        # Get events
        events = await ai_event_service.list_events(
            db=db,
            camera_id=camera_id,
            model_id=model_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset
        )

        # Convert to response schema
        event_responses = [
            AIEventResponse.from_orm(event)
            for event in events
        ]

        return AIEventListResponse(
            events=event_responses,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Failed to list AI events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list AI events: {str(e)}"
        )


@router.get("/cameras/{camera_id}/events", response_model=AIEventListResponse)
async def list_camera_ai_events(
    camera_id: UUID,
    model_id: Optional[str] = Query(None, description="Filter by model identifier"),
    start_time: Optional[datetime] = Query(None, description="Filter by start time (ISO 8601)"),
    end_time: Optional[datetime] = Query(None, description="Filter by end time (ISO 8601)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results (1-1000)"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db)
):
    """List AI events for a specific camera (Phase 5.3: Read-only).

    This is a convenience endpoint equivalent to:
        GET /api/v1/ai-events?camera_id={camera_id}&...

    Args:
        camera_id: Camera/device UUID (required)
        model_id: Optional filter by model
        start_time: Optional filter by start time
        end_time: Optional filter by end time
        limit: Maximum results (default 100, max 1000)
        offset: Results to skip (default 0)

    Returns:
        AIEventListResponse with events for the specified camera

    Phase 5.3 Note:
    - Convenience wrapper around list_ai_events()
    - Same constraints and defaults apply
    """
    try:
        # Get total count
        total = await ai_event_service.count_events(
            db=db,
            camera_id=camera_id,
            model_id=model_id,
            start_time=start_time,
            end_time=end_time
        )

        # Get events
        events = await ai_event_service.list_events(
            db=db,
            camera_id=camera_id,
            model_id=model_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset
        )

        # Convert to response schema
        event_responses = [
            AIEventResponse.from_orm(event)
            for event in events
        ]

        return AIEventListResponse(
            events=event_responses,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Failed to list AI events for camera {camera_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list AI events for camera: {str(e)}"
        )
