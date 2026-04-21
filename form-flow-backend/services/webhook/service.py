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

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core import database
from core.models import Webhook, WebhookDeliveryLog
from core.schemas import WebhookCreate, WebhookUpdate
from config.settings import settings
from utils.logging import get_logger
from .schemas import FormEventType

logger = get_logger(__name__)

# Valid event types (using enum values)
VALID_EVENTS = [e.value for e in FormEventType]


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
        
        # Generate or use custom secret
        secret = webhook_data.secret if webhook_data.secret else secrets.token_hex(32)
        
        # Create webhook
        webhook = Webhook(
            user_id=user_id,
            url=url,
            events=events,
            name=webhook_data.name,
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
        
        if updates.name is not None:
            webhook.name = updates.name
        
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
        """
        Process pending webhook deliveries.
        
        Requirements:
        - Process up to 50 pending deliveries per execution
        - Also process retrying deliveries that are due
        """
        # Get pending deliveries
        result = await self.db.execute(
            select(WebhookDeliveryLog)
            .where(WebhookDeliveryLog.status == "pending")
            .order_by(WebhookDeliveryLog.created_at)
            .limit(50)
        )
        deliveries = list(result.scalars().all())
        
        # Also get retrying deliveries that are due
        now = datetime.utcnow()
        retry_result = await self.db.execute(
            select(WebhookDeliveryLog)
            .where(WebhookDeliveryLog.status == "retrying")
            .where(WebhookDeliveryLog.next_retry_at <= now)
            .order_by(WebhookDeliveryLog.next_retry_at)
            .limit(50)
        )
        retry_deliveries = list(retry_result.scalars().all())
        
        # Combine and process all deliveries
        all_deliveries = deliveries + retry_deliveries
        
        for delivery in all_deliveries:
            await self._deliver_webhook(delivery)
    
    async def deliver_webhook(self, delivery_id: UUID) -> bool:
        """
        Public method to deliver a webhook payload.
        
        Args:
            delivery_id: UUID of the delivery log entry
            
        Returns:
            True if delivery succeeded, False otherwise
            
        Requirements 8.1-8.7:
        - Send HTTP POST with JSON body
        - Include required headers
        - Handle response codes (2xx = success, 4xx/5xx = failed)
        """
        result = await self.db.execute(
            select(WebhookDeliveryLog).where(WebhookDeliveryLog.id == delivery_id)
        )
        delivery = result.scalar_one_or_none()
        
        if not delivery:
            logger.warning(f"Delivery not found: {delivery_id}")
            return False
        
        await self._deliver_webhook(delivery)
        
        return delivery.status == "success"
    
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
            delivery.response_body = "Webhook not found or inactive"
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
                
                # Requirement 8.6: Success on HTTP 2xx
                if response.status_code >= 200 and response.status_code < 300:
                    delivery.status = "success"
                    delivery.delivered_at = datetime.utcnow()
                    delivery.next_retry_at = None
                    logger.info(f"Webhook delivered successfully: {webhook.id}")
                else:
                    # Requirement 8.7: Failed on HTTP 4xx/5xx
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
        
        # Requirement 9.1-9.5: Retry logic with exponential backoff
        await self._handle_retry(delivery)
        
        await self.db.commit()
    
    async def _handle_retry(self, delivery: WebhookDeliveryLog) -> None:
        """
        Handle retry logic with exponential backoff.
        
        Requirements 9.1-9.5:
        - Retry up to 3 times
        - Exponential backoff: 60 × 2^(n-1) seconds (1min, 2min, 4min)
        - Schedule retries and record next_retry_at
        """
        max_retries = 3
        
        if delivery.status == "failed" and delivery.attempts < max_retries:
            # Requirement 9.2: Exponential backoff: 60 × 2^(n-1) seconds
            # n is the attempt number (1-indexed), so for attempt 1: 60 × 2^0 = 60s
            # for attempt 2: 60 × 2^1 = 120s, for attempt 3: 60 × 2^2 = 240s
            delay_seconds = 60 * (2 ** (delivery.attempts - 1))
            
            delivery.next_retry_at = datetime.utcnow()
            delivery.next_retry_at = delivery.next_retry_at.replace(
                second=delivery.next_retry_at.second + delay_seconds
            )
            delivery.status = "retrying"
            
            logger.info(
                f"Scheduling retry for delivery {delivery.id}, "
                f"attempt {delivery.attempts}, delay {delay_seconds}s"
            )
        elif delivery.status == "failed" and delivery.attempts >= max_retries:
            # Requirement 9.4: Max retries exceeded, mark permanently failed
            delivery.status = "failed"
            delivery.next_retry_at = None
            logger.warning(
                f"Delivery {delivery.id} permanently failed after {delivery.attempts} attempts"
            )
    
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
    
    @staticmethod
    def calculate_backoff_delay(attempt_number: int) -> int:
        """
        Calculate exponential backoff delay for a given attempt number.
        
        Args:
            attempt_number: The attempt number (1-indexed)
            
        Returns:
            Delay in seconds using formula: 60 × 2^(n-1)
            
        Examples:
            attempt_number=1 -> 60 seconds (1 minute)
            attempt_number=2 -> 120 seconds (2 minutes)
            attempt_number=3 -> 240 seconds (4 minutes)
            
        Validates: Requirement 9.2
        """
        if attempt_number < 1:
            return 60
        return 60 * (2 ** (attempt_number - 1))
    
    async def retry_delivery(self, delivery_id: UUID) -> bool:
        """
        Manually retry a failed delivery.
        
        Args:
            delivery_id: UUID of the delivery log entry
            
        Returns:
            True if retry was scheduled, False if delivery not found
            
        Requirements 14.1, 14.2:
        - Reset attempt count to 0
        - Re-queue the delivery
        """
        result = await self.db.execute(
            select(WebhookDeliveryLog).where(WebhookDeliveryLog.id == delivery_id)
        )
        delivery = result.scalar_one_or_none()
        
        if not delivery:
            logger.warning(f"Delivery not found for retry: {delivery_id}")
            return False
        
        # Only allow manual retry for deliveries that have exceeded max retries
        if delivery.status != "failed" or delivery.attempts < 3:
            logger.warning(f"Cannot manually retry delivery {delivery_id}: status={delivery.status}, attempts={delivery.attempts}")
            return False
        
        # Reset attempt count and re-queue
        delivery.attempts = 0
        delivery.status = "pending"
        delivery.next_retry_at = None
        delivery.response_code = None
        delivery.response_body = None
        
        await self.db.commit()
        
        logger.info(f"Manual retry scheduled for delivery {delivery_id}")
        
        # Trigger async delivery processing
        asyncio.create_task(self._process_deliveries())
        
        return True
    
    async def list_deliveries(
        self,
        webhook_id: UUID,
        user_id: int,
        status: Optional[str] = None,
        event: Optional[str] = None
    ) -> List[WebhookDeliveryLog]:
        """
        List delivery logs for a webhook.
        
        Args:
            webhook_id: Webhook UUID
            user_id: User ID for ownership check
            status: Optional filter by status (pending, success, failed, retrying)
            event: Optional filter by event type
            
        Returns:
            List of delivery logs
            
        Requirements 13.1, 13.2, 13.3:
        - Return all delivery log entries for a webhook
        - Allow filtering by status
        - Allow filtering by event type
        """
        # Verify webhook ownership
        webhook = await self.get_webhook(webhook_id, user_id)
        if not webhook:
            return []
        
        # Build query
        query = select(WebhookDeliveryLog).where(
            WebhookDeliveryLog.webhook_id == webhook_id
        )
        
        if status:
            query = query.where(WebhookDeliveryLog.status == status)
        
        if event:
            query = query.where(WebhookDeliveryLog.event == event)
        
        query = query.order_by(WebhookDeliveryLog.created_at.desc())
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_delivery(
        self,
        delivery_id: UUID,
        webhook_id: UUID,
        user_id: int
    ) -> Optional[WebhookDeliveryLog]:
        """
        Get a specific delivery log.
        
        Args:
            delivery_id: Delivery log UUID
            webhook_id: Webhook UUID (for ownership verification)
            user_id: User ID for ownership check
            
        Returns:
            Delivery log if found and owned by user
        """
        # Verify webhook ownership
        webhook = await self.get_webhook(webhook_id, user_id)
        if not webhook:
            return None
        
        result = await self.db.execute(
            select(WebhookDeliveryLog).where(
                WebhookDeliveryLog.id == delivery_id,
                WebhookDeliveryLog.webhook_id == webhook_id
            )
        )
        return result.scalar_one_or_none()


async def get_webhook_service(db: AsyncSession = Depends(database.get_db)) -> WebhookService:
    """Dependency for getting webhook service."""
    return WebhookService(db)