"""AI Model Registry API routes (Phase 5.4: AI Model Registry & Discovery APIs).

This module provides read-only HTTP endpoints for discovering registered AI models.

Phase 5.4 Constraints:
- Read-only operations (no writes, updates, or deletes from external callers)
- Metadata only (NOT runtime state)
- Environment-scoped (global, not per-camera)
- Independent of containers, inference, or execution
- Fail-closed validation source (unknown model_id = invalid)
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from loguru import logger

from database import get_db
from app.models.ai_model import AIModel
from app.schemas.ai_model import AIModelResponse, AIModelListResponse


router = APIRouter(prefix="/api/v1/ai-models", tags=["ai-models"])


@router.get("/{model_id}", response_model=AIModelResponse)
async def get_ai_model(
    model_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a single AI model by ID (Phase 5.4: Read-only discovery).

    Args:
        model_id: AI model identifier (e.g., "ruth-person-detection-v1")
        db: Database session (injected)

    Returns:
        AIModelResponse with model metadata

    Raises:
        HTTPException: 404 if model not found

    Phase 5.4 Constraints:
    - Read-only operation
    - Returns metadata only (NOT runtime state)
    - No side effects
    - Model may be enabled or disabled

    Example:
        GET /api/v1/ai-models/ruth-person-detection-v1
    """
    try:
        # Query for model by primary key
        stmt = select(AIModel).where(AIModel.model_id == model_id)
        result = await db.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI model '{model_id}' not found"
            )

        return AIModelResponse.model_validate(model)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get AI model {model_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve AI model: {str(e)}"
        )


@router.get("", response_model=AIModelListResponse)
async def list_ai_models(
    enabled: Optional[bool] = Query(None, description="Filter by enabled status (true/false)"),
    db: AsyncSession = Depends(get_db)
):
    """List all registered AI models with optional filtering (Phase 5.4: Read-only discovery).

    Query parameters:
        enabled: Optional boolean to filter by enabled status
                 - true: only enabled models
                 - false: only disabled models
                 - omit: all models (default)

    Returns:
        AIModelListResponse with:
        - models: List of AI models (ordered by created_at DESC)
        - total: Total number of models returned

    Phase 5.4 Constraints:
    - Read-only operation
    - Returns metadata only (NOT runtime state)
    - No pagination (model count expected to be small < 100)
    - No side effects

    Used by:
    - Frontend model selection UI (Phase 8.3) - typically filters enabled=true
    - Backend validation for assignments (Phase 8.1)
    - Ruth AI Core model discovery (future phases)

    Example:
        GET /api/v1/ai-models
        GET /api/v1/ai-models?enabled=true
    """
    try:
        # Build query with optional filter
        stmt = select(AIModel)

        if enabled is not None:
            stmt = stmt.where(AIModel.enabled == enabled)

        # Order by creation date (newest first)
        stmt = stmt.order_by(AIModel.created_at.desc())

        # Execute query
        result = await db.execute(stmt)
        models = result.scalars().all()

        # Convert to response schema
        model_responses = [
            AIModelResponse.model_validate(model)
            for model in models
        ]

        return AIModelListResponse(
            models=model_responses,
            total=len(model_responses)
        )

    except Exception as e:
        logger.error(f"Failed to list AI models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list AI models: {str(e)}"
        )
