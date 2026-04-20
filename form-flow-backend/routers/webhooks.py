"""
Webhook Router

Provides endpoints for webhook management.

Endpoints:
    POST /webhooks - Create a new webhook
    GET /webhooks - List all webhooks for user
    GET /webhooks/{id} - Get webhook details
    DELETE /webhooks/{id} - Delete a webhook
    PATCH /webhooks/{id} - Update a webhook
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from core import database, schemas
from core.schemas import WebhookCreate, WebhookUpdate, WebhookResponse, WebhookCreateResponse
from services.webhook.service import WebhookService, get_webhook_service
from utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


async def get_current_user_webhook_service(
    db: AsyncSession = Depends(database.get_db),
    service: WebhookService = Depends(get_webhook_service)
) -> tuple[int, WebhookService]:
    """
    Get current user ID and webhook service.
    
    In a real implementation, this would extract user from JWT token.
    For now, returns a placeholder user_id.
    """
    # TODO: Extract user_id from JWT token
    # For development, use a default user
    return 1, service


@router.post(
    "",
    response_model=WebhookCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new webhook",
    responses={
        201: {"description": "Webhook created successfully"},
        400: {"description": "Invalid URL or too many webhooks"},
        422: {"description": "Validation error"},
    }
)
async def create_webhook(
    webhook_data: WebhookCreate,
    user_id: int = 1,  # TODO: Get from auth
    service: WebhookService = Depends(get_webhook_service)
):
    """
    Create a new webhook for receiving form events.
    
    The secret is returned only once - make sure to save it.
    """
    try:
        webhook = await service.create_webhook(user_id, webhook_data)
        return webhook
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "",
    response_model=List[WebhookResponse],
    summary="List all webhooks",
    responses={
        200: {"description": "List of webhooks"},
    }
)
async def list_webhooks(
    user_id: int = 1,  # TODO: Get from auth
    service: WebhookService = Depends(get_webhook_service)
):
    """Get all webhooks for the current user."""
    webhooks = await service.list_webhooks(user_id)
    return webhooks


@router.get(
    "/{webhook_id}",
    response_model=WebhookResponse,
    summary="Get webhook details",
    responses={
        200: {"description": "Webhook details"},
        404: {"description": "Webhook not found"},
    }
)
async def get_webhook(
    webhook_id: UUID,
    user_id: int = 1,  # TODO: Get from auth
    service: WebhookService = Depends(get_webhook_service)
):
    """Get a specific webhook by ID."""
    webhook = await service.get_webhook(webhook_id, user_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook


@router.delete(
    "/{webhook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a webhook",
    responses={
        204: {"description": "Webhook deleted"},
        404: {"description": "Webhook not found"},
    }
)
async def delete_webhook(
    webhook_id: UUID,
    user_id: int = 1,  # TODO: Get from auth
    service: WebhookService = Depends(get_webhook_service)
):
    """Delete a webhook."""
    deleted = await service.delete_webhook(webhook_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return None


@router.patch(
    "/{webhook_id}",
    response_model=WebhookResponse,
    summary="Update a webhook",
    responses={
        200: {"description": "Webhook updated"},
        404: {"description": "Webhook not found"},
    }
)
async def update_webhook(
    webhook_id: UUID,
    updates: WebhookUpdate,
    user_id: int = 1,  # TODO: Get from auth
    service: WebhookService = Depends(get_webhook_service)
):
    """Update a webhook (enable/disable, change URL or events)."""
    try:
        webhook = await service.update_webhook(webhook_id, user_id, updates)
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        return webhook
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))