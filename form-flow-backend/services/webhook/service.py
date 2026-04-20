"""
Webhook Service

Provides webhook management and delivery functionality.

Usage:
    from services.webhook.service import WebhookService
    
    service = WebhookService()
    webhooks = await service.list_webhooks(user_id)
"""

import secrets
import json
import hmac
import hashlib
import asyncio
import httpx
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.models import Webhook, WebhookDeliveryLog
from core.schemas import WebhookCreate, WebhookUpdate
from config.settings import settings
from utils.logging import get_logger

logger = get_logger(__name__)

# Valid event types
VALID_EVENTS = ["form.submitted", "form.failed", "form.scraped"]


class WebhookService:
    """Service for managing webhooks and delivering events."""
    
    def __init__(self, db: AsyncSession = None):
        self.db = db
    
    async def create_webhook(
        self,
        user_id: int,
        webhook_data: WebhookCreate
    ) -> Webhook:
        """
        Create a new webhook for a user.
        
        Args:
            user_id: User ID
            webhook_data: Webhook configuration
            
        Returns:
            Created webhook with auto-generated secret
            
        Raises:
            ValueError: If URL is invalid or too many webhooks
        """
        # Validate URL
        url = webhook_data.url.strip()
        if not url.startswith("https://"):
            raise ValueError("Webhook URL must use HTTPS")
        
        # Validate events
        events = webhook_data.events or ["form.submitted"]
        for event in events:
            if event not in VALID_EVENTS:
                raise ValueError(f"Invalid event type: {event}. Valid: {VALID_EVENTS}")
        
        # Check webhook limit
        if self.db:
            from sqlalchemy import func
            count_result = await self.db.execute(
                select(func.count(Webhook.id)).where(Webhook.user_id == user_id)
            )
            count = count_result.scalar() or 0
            if count >= settings.WEBHOOK_MAX_PER_USER:
                raise ValueError(f"Maximum {settings.WEBHOOK_MAX_PER_USER} webhooks per user")
        
        # Generate secret
        secret = secrets.token_hex(32)
        
        # Create webhook
        webhook = Webhook(
            user_id=user_id,
            url=url,
            events=events,
            secret=secret,
            is_active=True
        )
        
        self.db.add(webhook)
        await self.db.commit()
        await self.db.refresh(webhook)
        
        logger.info(f"Created webhook {webhook.id} for user {user_id}")
        return webhook
    
    async def list_webhooks(self, user_id: int) -> List[Webhook]:
        """
        List all webhooks for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of webhooks
        """
        result = await self.db.execute(
            select(Webhook)
            .where(Webhook.user_id == user_id)
            .order_by(Webhook.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_webhook(self, webhook_id: UUID, user_id: int) -> Optional[Webhook]:
        """
        Get a specific webhook.
        
        Args:
            webhook_id: Webhook UUID
            user_id: User ID for ownership check
            
        Returns:
            Webhook if found and owned by user
        """
        result = await self.db.execute(
            select(Webhook)
            .where(Webhook.id == webhook_id, Webhook.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def delete_webhook(self, webhook_id: UUID, user_id: int) -> bool:
        """
        Delete a webhook.
        
        Args:
            webhook_id: Webhook UUID
            user_id: User ID for ownership check
            
        Returns:
            True if deleted
        """
        webhook = await self.get_webhook(webhook_id, user_id)
        if not webhook:
            return False
        
        await self.db.delete(webhook)
        await self.db.commit()
        
        logger.info(f"Deleted webhook {webhook_id}")
        return True
    
    async def update_webhook(
        self,
        webhook_id: UUID,
        user_id: int,
        updates: WebhookUpdate
    ) -> Optional[Webhook]:
        """
        Update a webhook.
        
        Args:
            webhook_id: Webhook UUID
            user_id: User ID for ownership check
            updates: Fields to update
            
        Returns:
            Updated webhook or None if not found
        """
        webhook = await self.get_webhook(webhook_id, user_id)
        if not webhook:
            return None
        
        if updates.url is not None:
            url = updates.url.strip()
            if not url.startswith("https://"):
                raise ValueError("Webhook URL must use HTTPS")
            webhook.url = url
        
        if updates.events is not None:
            for event in updates.events:
                if event not in VALID_EVENTS:
                    raise ValueError(f"Invalid event type: {event}")
            webhook.events = updates.events
        
        if updates.is_active is not None:
            webhook.is_active = updates.is_active
        
        await self.db.commit()
        await self.db.refresh(webhook)
        
        logger.info(f"Updated webhook {webhook_id}")
        return webhook
    
    async def queue_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Queue an event for delivery to all active webhooks subscribed to it.
        
        Args:
            event_type: Event type (e.g., "form.submitted")
            data: Event data payload
        """
        if event_type not in VALID_EVENTS:
            logger.warning(f"Invalid event type: {event_type}")
            return
        
        # Get all active webhooks subscribed to this event
        result = await self.db.execute(
            select(Webhook)
            .where(Webhook.is_active == True)
            .where(Webhook.events.contains(event_type))
        )
        webhooks = list(result.scalars().all())
        
        if not webhooks:
            return
        
        # Create delivery logs
        payload = {
            "event": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": data
        }
        
        for webhook in webhooks:
            log = WebhookDeliveryLog(
                webhook_id=webhook.id,
                event=event_type,
                payload=payload,
                status="pending"
            )
            self.db.add(log)
        
        await self.db.commit()
        
        # Process deliveries asynchronously
        asyncio.create_task(self._process_deliveries())
    
    async def _process_deliveries(self) -> None:
        """Process pending webhook deliveries."""
        # Get pending deliveries
        result = await self.db.execute(
            select(WebhookDeliveryLog)
            .where(WebhookDeliveryLog.status == "pending")
            .order_by(WebhookDeliveryLog.created_at)
            .limit(50)
        )
        deliveries = list(result.scalars().all())
        
        for delivery in deliveries:
            await self._deliver_webhook(delivery)
    
    async def _deliver_webhook(self, delivery: WebhookDeliveryLog) -> None:
        """
        Deliver a webhook payload.
        
        Args:
            delivery: Delivery log entry
        """
        # Get webhook
        result = await self.db.execute(
            select(Webhook).where(Webhook.id == delivery.webhook_id)
        )
        webhook = result.scalar_one_or_none()
        
        if not webhook or not webhook.is_active:
            delivery.status = "failed"
            await self.db.commit()
            return
        
        # Prepare payload
        payload = delivery.payload
        timestamp = str(int(datetime.utcnow().timestamp()))
        
        # Generate signature
        signature = self._generate_signature(payload, webhook.secret, timestamp)
        
        # Attempt delivery
        delivery.attempts += 1
        
        try:
            async with httpx.AsyncClient(timeout=settings.WEBHOOK_TIMEOUT_SECONDS) as client:
                response = await client.post(
                    webhook.url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Signature": signature,
                        "X-Webhook-Timestamp": timestamp,
                        "X-Webhook-Event": delivery.event
                    }
                )
                
                delivery.response_code = response.status_code
                delivery.response_body = response.text[:1000] if response.text else ""
                
                if response.status_code >= 200 and response.status_code < 300:
                    delivery.status = "success"
                    delivery.delivered_at = datetime.utcnow()
                    logger.info(f"Webhook delivered successfully: {webhook.id}")
                else:
                    delivery.status = "failed"
                    logger.warning(f"Webhook delivery failed: {webhook.id}, status: {response.status_code}")
        
        except httpx.TimeoutException:
            delivery.response_code = 0
            delivery.response_body = "Timeout"
            delivery.status = "failed"
            logger.warning(f"Webhook delivery timeout: {webhook.id}")
        
        except Exception as e:
            delivery.response_code = 0
            delivery.response_body = str(e)[:1000]
            delivery.status = "failed"
            logger.error(f"Webhook delivery error: {webhook.id}, error: {e}")
        
        await self.db.commit()
    
    def _generate_signature(self, payload: Dict, secret: str, timestamp: str) -> str:
        """
        Generate HMAC-SHA256 signature for webhook payload.
        
        Args:
            payload: JSON payload
            secret: Webhook secret
            timestamp: Unix timestamp
            
        Returns:
            Hex-encoded signature
        """
        message = f"{timestamp}.{json.dumps(payload, sort_keys=True)}"
        return hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()


async def get_webhook_service(db: AsyncSession = None) -> WebhookService:
    """Dependency for getting webhook service."""
    return WebhookService(db)