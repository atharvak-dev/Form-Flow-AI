"""
Webhook Router

Provides endpoints for webhook management.

Endpoints:
    POST /webhooks - Create a new webhook
    GET /webhooks - List all webhooks for user
    GET /webhooks/{id} - Get webhook details
    DELETE /webhooks/{id} - Delete a webhook
    PATCH /webhooks/{id} - Update a webhook
    GET /webhooks/{id}/deliveries - List delivery logs
    GET /webhooks/{id}/deliveries/{delivery_id} - Get delivery log
    POST /webhooks/{id}/deliveries/{delivery_id}/retry - Manual retry
    POST /webhooks/test-event - Trigger a test event
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from uuid import UUID

from core import database, schemas
from core.schemas import WebhookCreate, WebhookUpdate, WebhookResponse, WebhookCreateResponse, WebhookDeliveryLogResponse
from services.webhook.service import WebhookService, get_webhook_service
from utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


async def get_current_user_webhook_service(
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


# Test event endpoint must be defined BEFORE dynamic routes to avoid /test-event being matched as {webhook_id}
@router.post(
    "/test-event",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger a test event",
    responses={
        202: {"description": "Event queued"},
        400: {"description": "Invalid event type"},
    }
)
async def trigger_test_event(
    event_type: str = Query(..., description="Event type to trigger"),
    data: Optional[str] = Query(None, description="Optional JSON test data"),
    user_id: int = 1,  # TODO: Get from auth
    service: WebhookService = Depends(get_webhook_service)
):
    """
    Trigger a test event for webhook delivery.
    
    Requirements 7.1-7.4:
    - Accepts an event_type parameter
    - Accepts optional test data
    - Calls the queue_event method to trigger the event
    """
    import json
    
    # Parse test data if provided
    event_data = {}
    if data:
        try:
            event_data = json.loads(data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in data parameter")
    
    # Add test indicator to data
    event_data["_test"] = True
    
    try:
        await service.queue_event(event_type, event_data)
        return {"message": f"Event '{event_type}' queued for delivery", "event_type": event_type}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{webhook_id}/deliveries",
    response_model=List[WebhookDeliveryLogResponse],
    summary="List delivery logs",
    responses={
        200: {"description": "List of delivery logs"},
        404: {"description": "Webhook not found"},
    }
)
async def list_deliveries(
    webhook_id: UUID,
    status: Optional[str] = Query(None, description="Filter by status (pending, success, failed, retrying)"),
    event: Optional[str] = Query(None, description="Filter by event type"),
    user_id: int = 1,  # TODO: Get from auth
    service: WebhookService = Depends(get_webhook_service)
):
    """
    List delivery logs for a webhook.
    
    Requirements 13.1, 13.2, 13.3:
    - Returns all delivery log entries for a webhook
    - Can filter by status
    - Can filter by event type
    """
    deliveries = await service.list_deliveries(webhook_id, user_id, status, event)
    return deliveries


@router.get(
    "/{webhook_id}/deliveries/{delivery_id}",
    response_model=WebhookDeliveryLogResponse,
    summary="Get delivery log",
    responses={
        200: {"description": "Delivery log details"},
        404: {"description": "Webhook or delivery not found"},
    }
)
async def get_delivery(
    webhook_id: UUID,
    delivery_id: UUID,
    user_id: int = 1,  # TODO: Get from auth
    service: WebhookService = Depends(get_webhook_service)
):
    """Get a specific delivery log for a webhook."""
    delivery = await service.get_delivery(delivery_id, webhook_id, user_id)
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return delivery


@router.post(
    "/{webhook_id}/deliveries/{delivery_id}/retry",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Manual retry",
    responses={
        202: {"description": "Retry scheduled"},
        404: {"description": "Webhook or delivery not found"},
        400: {"description": "Cannot retry - delivery not eligible"},
    }
)
async def retry_delivery(
    webhook_id: UUID,
    delivery_id: UUID,
    user_id: int = 1,  # TODO: Get from auth
    service: WebhookService = Depends(get_webhook_service)
):
    """
    Manually retry a failed delivery.
    
    Requirements 14.1, 14.2:
    - Only allows manual retry for deliveries that have exceeded max automatic retries
    - Resets attempt count and re-queues the delivery
    """
    # First verify webhook ownership
    webhook = await service.get_webhook(webhook_id, user_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    
    # Attempt retry
    success = await service.retry_delivery(delivery_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Cannot manually retry: delivery not found or not eligible for retry (must have failed after 3 attempts)"
        )
    return {"message": "Retry scheduled"}