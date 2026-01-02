"""AI Model Assignment API routes (Phase 8.1: Backend Model Assignment APIs).

This module provides authoritative backend control-plane APIs to persist
camera-to-AI-model assignment intent.

Phase 8.1 Constraints:
- Control-plane only (records intent, does NOT trigger execution)
- No communication with Ruth AI Core or model containers
- No side effects beyond persistence
- Idempotent operations
- No execution or reconciliation logic

CRITICAL: These APIs store INTENT only, not execution state.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Optional, List
from uuid import UUID
from loguru import logger

from database import get_db
from app.models import AIModelAssignment, Device
from app.schemas.ai_model_assignment import (
    AIModelAssignmentCreate,
    AIModelAssignmentUpdate,
    AIModelAssignmentResponse,
    AIModelAssignmentListResponse
)


router = APIRouter(prefix="/api/v1/ai-model-assignments", tags=["ai-model-assignments"])


@router.post("", response_model=AIModelAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    assignment_data: AIModelAssignmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new camera-to-model assignment (Phase 8.1).

    This records assignment INTENT only. It does NOT:
    - Start model execution
    - Communicate with AI runtime
    - Affect video pipelines
    - Trigger any background tasks

    Args:
        assignment_data: Assignment creation data
        db: Database session (injected)

    Returns:
        AIModelAssignmentResponse with created assignment

    Raises:
        HTTPException: 400 if camera_id doesn't exist
        HTTPException: 409 if assignment already exists (camera_id + model_id unique)
        HTTPException: 500 on persistence failure

    Phase 8.1 Constraints:
    - Idempotent (duplicate creates return existing if enabled state matches)
    - Validates camera_id existence (best-effort)
    - Does NOT validate model_id against running models
    - Purely control-plane persistence
    """
    try:
        # Validate camera_id exists (best-effort validation)
        camera_result = await db.execute(
            select(Device).where(Device.id == assignment_data.camera_id)
        )
        camera = camera_result.scalar_one_or_none()

        if not camera:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Camera {assignment_data.camera_id} not found"
            )

        # Check if assignment already exists
        existing_result = await db.execute(
            select(AIModelAssignment).where(
                and_(
                    AIModelAssignment.camera_id == assignment_data.camera_id,
                    AIModelAssignment.model_id == assignment_data.model_id
                )
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            # Idempotent behavior: if enabled state matches, return existing
            if existing.enabled == assignment_data.enabled:
                logger.info(
                    f"Assignment already exists: camera={assignment_data.camera_id} "
                    f"model={assignment_data.model_id} (idempotent)"
                )
                return AIModelAssignmentResponse.from_orm(existing)

            # Otherwise, conflict
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Assignment already exists for camera {assignment_data.camera_id} "
                       f"and model {assignment_data.model_id} with different state"
            )

        # Create new assignment
        assignment = AIModelAssignment(**assignment_data.model_dump())
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)

        logger.info(
            f"Created assignment: id={assignment.id} camera={assignment.camera_id} "
            f"model={assignment.model_id} enabled={assignment.enabled}"
        )

        return AIModelAssignmentResponse.from_orm(assignment)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create assignment: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create assignment: {str(e)}"
        )


@router.get("/{assignment_id}", response_model=AIModelAssignmentResponse)
async def get_assignment(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific assignment by ID (Phase 8.1).

    Args:
        assignment_id: Assignment UUID
        db: Database session (injected)

    Returns:
        AIModelAssignmentResponse with assignment details

    Raises:
        HTTPException: 404 if assignment not found

    Phase 8.1 Constraints:
    - Read-only operation
    - Returns intent state, not execution state
    """
    try:
        result = await db.execute(
            select(AIModelAssignment).where(AIModelAssignment.id == assignment_id)
        )
        assignment = result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assignment {assignment_id} not found"
            )

        return AIModelAssignmentResponse.from_orm(assignment)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get assignment {assignment_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve assignment: {str(e)}"
        )


@router.get("", response_model=AIModelAssignmentListResponse)
async def list_assignments(
    camera_id: Optional[UUID] = Query(None, description="Filter by camera/device UUID"),
    model_id: Optional[str] = Query(None, description="Filter by model identifier"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled state"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results (1-1000)"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: AsyncSession = Depends(get_db)
):
    """List assignments with optional filtering and pagination (Phase 8.1).

    Query parameters:
        camera_id: Optional UUID to filter by camera
        model_id: Optional string to filter by model
        enabled: Optional boolean to filter by enabled state
        limit: Maximum results to return (default 100, max 1000)
        offset: Number of results to skip (default 0)

    Returns:
        AIModelAssignmentListResponse with:
        - assignments: List of assignments (ordered by created_at DESC)
        - total: Total count matching filters
        - limit: Limit applied to this query
        - offset: Offset applied to this query

    Phase 8.1 Constraints:
    - Read-only operation
    - Returns intent state, not execution state
    - Safe defaults (bounded limits)
    """
    try:
        # Build filter conditions
        filters = []
        if camera_id is not None:
            filters.append(AIModelAssignment.camera_id == camera_id)
        if model_id is not None:
            filters.append(AIModelAssignment.model_id == model_id)
        if enabled is not None:
            filters.append(AIModelAssignment.enabled == enabled)

        # Count total matching records
        count_query = select(func.count()).select_from(AIModelAssignment)
        if filters:
            count_query = count_query.where(and_(*filters))

        count_result = await db.execute(count_query)
        total = count_result.scalar()

        # Fetch paginated results
        query = select(AIModelAssignment)
        if filters:
            query = query.where(and_(*filters))

        query = query.order_by(AIModelAssignment.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        assignments = result.scalars().all()

        return AIModelAssignmentListResponse(
            assignments=[AIModelAssignmentResponse.from_orm(a) for a in assignments],
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Failed to list assignments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list assignments: {str(e)}"
        )


@router.patch("/{assignment_id}", response_model=AIModelAssignmentResponse)
async def update_assignment(
    assignment_id: UUID,
    assignment_data: AIModelAssignmentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing assignment (Phase 8.1).

    This updates assignment INTENT only. It does NOT:
    - Affect running inference
    - Communicate with AI runtime
    - Trigger reconciliation or restart

    Args:
        assignment_id: Assignment UUID
        assignment_data: Fields to update (PATCH semantics)
        db: Database session (injected)

    Returns:
        AIModelAssignmentResponse with updated assignment

    Raises:
        HTTPException: 404 if assignment not found
        HTTPException: 500 on persistence failure

    Phase 8.1 Constraints:
    - Idempotent (same update returns success)
    - PATCH semantics (only provided fields updated)
    - Purely control-plane persistence
    - No execution side effects
    """
    try:
        # Fetch existing assignment
        result = await db.execute(
            select(AIModelAssignment).where(AIModelAssignment.id == assignment_id)
        )
        assignment = result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assignment {assignment_id} not found"
            )

        # Update only provided fields (PATCH semantics)
        update_data = assignment_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(assignment, field, value)

        await db.commit()
        await db.refresh(assignment)

        logger.info(
            f"Updated assignment: id={assignment.id} camera={assignment.camera_id} "
            f"model={assignment.model_id} enabled={assignment.enabled}"
        )

        return AIModelAssignmentResponse.from_orm(assignment)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update assignment {assignment_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update assignment: {str(e)}"
        )


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete an assignment (Phase 8.1).

    This removes assignment INTENT. It does NOT:
    - Stop running inference
    - Communicate with AI runtime
    - Clean up model resources

    Args:
        assignment_id: Assignment UUID
        db: Database session (injected)

    Returns:
        204 No Content on success

    Raises:
        HTTPException: 404 if assignment not found
        HTTPException: 500 on persistence failure

    Phase 8.1 Constraints:
    - Idempotent (deleting non-existent returns 404)
    - Hard delete (removes record entirely)
    - Purely control-plane persistence
    - No execution side effects

    Note: For soft delete (preserving intent), use PATCH to set enabled=false
    """
    try:
        # Fetch existing assignment
        result = await db.execute(
            select(AIModelAssignment).where(AIModelAssignment.id == assignment_id)
        )
        assignment = result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assignment {assignment_id} not found"
            )

        # Delete assignment
        await db.delete(assignment)
        await db.commit()

        logger.info(
            f"Deleted assignment: id={assignment_id} camera={assignment.camera_id} "
            f"model={assignment.model_id}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete assignment {assignment_id}: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete assignment: {str(e)}"
        )
