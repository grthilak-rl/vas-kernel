"""API Key management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import secrets
import hashlib

from database import get_db
from app.models.api_key import ApiKey

router = APIRouter(
    prefix="/api/v1/auth/api-keys",
    tags=["Authentication"],
)


# Pydantic models
class ApiKeyCreate(BaseModel):
    """Request model for creating API key."""
    name: str = Field(..., description="Friendly name for the API key")
    description: Optional[str] = Field(None, description="Optional description")
    expires_at: Optional[datetime] = Field(None, description="Optional expiration datetime")


class ApiKeyResponse(BaseModel):
    """Response model for API key."""
    id: str
    name: str
    description: Optional[str]
    is_active: bool
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ApiKeyCreateResponse(ApiKeyResponse):
    """Response model for newly created API key (includes the actual key)."""
    key: str


class ApiKeyListResponse(BaseModel):
    """Response model for listing API keys."""
    api_keys: List[ApiKeyResponse]
    total: int


def generate_api_key() -> str:
    """Generate a secure random API key."""
    # Generate 32 random bytes and convert to hex (64 characters)
    return secrets.token_hex(32)


@router.post("", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: ApiKeyCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new API key.

    **Important**: The actual key value is only returned once during creation.
    Store it securely - you won't be able to retrieve it again.
    """
    # Generate the API key
    key = generate_api_key()

    # Create database record
    db_api_key = ApiKey(
        key=key,
        name=api_key_data.name,
        description=api_key_data.description,
        expires_at=api_key_data.expires_at,
        is_active=True
    )

    db.add(db_api_key)
    await db.commit()
    await db.refresh(db_api_key)

    # Convert to response model
    response = ApiKeyCreateResponse(
        id=str(db_api_key.id),
        key=key,
        name=db_api_key.name,
        description=db_api_key.description,
        is_active=db_api_key.is_active,
        expires_at=db_api_key.expires_at,
        last_used_at=db_api_key.last_used_at,
        created_at=db_api_key.created_at,
        updated_at=db_api_key.updated_at
    )

    return response


@router.get("", response_model=ApiKeyListResponse)
async def list_api_keys(
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    List all API keys.

    By default, only active keys are returned.
    Set include_inactive=true to see inactive keys as well.
    """
    query = select(ApiKey)

    if not include_inactive:
        query = query.where(ApiKey.is_active == True)

    query = query.order_by(ApiKey.created_at.desc())

    result = await db.execute(query)
    api_keys = result.scalars().all()

    return ApiKeyListResponse(
        api_keys=[
            ApiKeyResponse(
                id=str(key.id),
                name=key.name,
                description=key.description,
                is_active=key.is_active,
                expires_at=key.expires_at,
                last_used_at=key.last_used_at,
                created_at=key.created_at,
                updated_at=key.updated_at
            )
            for key in api_keys
        ],
        total=len(api_keys)
    )


@router.get("/{api_key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    api_key_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get details of a specific API key."""
    stmt = select(ApiKey).where(ApiKey.id == api_key_id)
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key with ID {api_key_id} not found"
        )

    return ApiKeyResponse(
        id=str(api_key.id),
        name=api_key.name,
        description=api_key.description,
        is_active=api_key.is_active,
        expires_at=api_key.expires_at,
        last_used_at=api_key.last_used_at,
        created_at=api_key.created_at,
        updated_at=api_key.updated_at
    )


@router.delete("/{api_key_id}", status_code=status.HTTP_200_OK)
async def revoke_api_key(
    api_key_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke (deactivate) an API key.

    This doesn't delete the key from the database, just marks it as inactive.
    """
    stmt = select(ApiKey).where(ApiKey.id == api_key_id)
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key with ID {api_key_id} not found"
        )

    if not api_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key is already revoked"
        )

    api_key.is_active = False
    await db.commit()

    return {
        "message": "API key revoked successfully",
        "id": str(api_key.id),
        "name": api_key.name
    }


@router.post("/{api_key_id}/activate", response_model=ApiKeyResponse)
async def activate_api_key(
    api_key_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Reactivate a previously revoked API key."""
    stmt = select(ApiKey).where(ApiKey.id == api_key_id)
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key with ID {api_key_id} not found"
        )

    if api_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key is already active"
        )

    api_key.is_active = True
    await db.commit()
    await db.refresh(api_key)

    return ApiKeyResponse(
        id=str(api_key.id),
        name=api_key.name,
        description=api_key.description,
        is_active=api_key.is_active,
        expires_at=api_key.expires_at,
        last_used_at=api_key.last_used_at,
        created_at=api_key.created_at,
        updated_at=api_key.updated_at
    )
