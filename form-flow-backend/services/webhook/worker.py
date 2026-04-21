"""
Webhook Delivery Worker

Background task for processing webhook deliveries with connection pooling.

Usage:
    from services.webhook.worker import DeliveryWorker
    
    worker = DeliveryWorker()
    await worker.run()  # Process pending deliveries
"""

import asyncio
import json
import hmac
import hashlib
from typing import List, Optional
from uuid import UUID
from datetime import datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Webhook, WebhookDeliveryLog
from config.settings import settings
from utils.logging import get_logger

logger = get_logger(__name__)

# Maximum deliveries to process per execution cycle
MAX_DELIVERIES_PER_CYCLE = 50

# Maximum retry attempts before permanent failure
MAX_RETRIES = 3


class DeliveryWorker:
    """
    Background worker for delivering webhook payloads.
    
    Features:
    - Processes up to 50 pending deliveries per execution cycle
    - Uses connection pooling for HTTP requests
    - Fetches pending deliveries ordered by created_at
    - Handles retry logic with exponential backoff
    
    Requirements: 16.1, 16.2
    """
    
    def __init__(self, db: AsyncSession = None):
        self.db = db
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def get_http_client(self) -> httpx.AsyncClient:
        """
        Get or create HTTP client with connection pooling.
        
        Returns:
            Async HTTP client with connection pooling configured
            
        Requirements: 16.2 - Use connection pooling for HTTP requests
        """
        if self._http_client is None or self._http_client.is_closed:
            # Configure connection pooling
            limits = httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=30.0
            )
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(settings.WEBHOOK_TIMEOUT_SECONDS),
                limits=limits
            )
        return self._http_client
    
    async def close(self):
        """Close the HTTP client and release connections."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None
    
    async def run(self) -> int:
        """
        Run the delivery worker to process pending deliveries.
        
        Returns:
            Number of deliveries processed
            
        Requirements: 16.1 - Process up to 50 pending deliveries per execution cycle
        """
        if not self.db:
            logger.warning("No database session provided to delivery worker")
            return 0
        
        # Fetch pending deliveries ordered by created_at
        pending_deliveries = await self._fetch_pending_deliveries()
        
        # Also fetch retrying deliveries that are due
        retry_deliveries = await self._fetch_retry_deliveries()
        
        # Combine all deliveries to process
        all_deliveries = pending_deliveries + retry_deliveries
        
        if not all_deliveries:
            logger.debug("No pending deliveries to process")
            return 0
        
        logger.info(f"Processing {len(all_deliveries)} webhook deliveries")
        
        # Process each delivery
        processed = 0
        for delivery in all_deliveries:
            try:
                await self._process_delivery(delivery)
                processed += 1
            except Exception as e:
                logger.error(f"Error processing delivery {delivery.id}: {e}")
        
        return processed
    
    async def _fetch_pending_deliveries(self) -> List[WebhookDeliveryLog]:
        """
        Fetch pending deliveries ordered by created_at.
        
        Returns:
            List of pending delivery logs (max 50)
            
        Requirements: 16.1 - Process up to 50 pending deliveries per execution cycle
        """
        result = await self.db.execute(
            select(WebhookDeliveryLog)
            .where(WebhookDeliveryLog.status == "pending")
            .order_by(WebhookDeliveryLog.created_at)
            .limit(MAX_DELIVERIES_PER_CYCLE)
        )
        return list(result.scalars().all())
    
    async def _fetch_retry_deliveries(self) -> List[WebhookDeliveryLog]:
        """
        Fetch retrying deliveries that are due for retry.
        
        Returns:
            List of retrying delivery logs that are due
        """
        now = datetime.utcnow()
        result = await self.db.execute(
            select(WebhookDeliveryLog)
            .where(WebhookDeliveryLog.status == "retrying")
            .where(WebhookDeliveryLog.next_retry_at <= now)
            .order_by(WebhookDeliveryLog.next_retry_at)
            .limit(MAX_DELIVERIES_PER_CYCLE)
        )
        return list(result.scalars().all())
    
    async def _process_delivery(self, delivery: WebhookDeliveryLog) -> None:
        """
        Process a single webhook delivery.
        
        Args:
            delivery: The delivery log to process
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
            client = await self.get_http_client()
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
            
            # Success on HTTP 2xx
            if response.status_code >= 200 and response.status_code < 300:
                delivery.status = "success"
                delivery.delivered_at = datetime.utcnow()
                delivery.next_retry_at = None
                logger.info(f"Webhook delivered successfully: {webhook.id}")
            else:
                # Failed on HTTP 4xx/5xx
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
        
        # Handle retry logic
        await self._handle_retry(delivery)
        
        await self.db.commit()
    
    async def _handle_retry(self, delivery: WebhookDeliveryLog) -> None:
        """
        Handle retry logic with exponential backoff.
        
        Requirements: 9.1-9.5
        - Retry up to 3 times
        - Exponential backoff: 60 × 2^(n-1) seconds
        """
        if delivery.status == "failed" and delivery.attempts < MAX_RETRIES:
            # Exponential backoff: 60 × 2^(n-1) seconds
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
        elif delivery.status == "failed" and delivery.attempts >= MAX_RETRIES:
            # Max retries exceeded, mark permanently failed
            delivery.status = "failed"
            delivery.next_retry_at = None
            logger.warning(
                f"Delivery {delivery.id} permanently failed after {delivery.attempts} attempts"
            )
    
    def _generate_signature(self, payload: dict, secret: str, timestamp: str) -> str:
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
        """
        if attempt_number < 1:
            return 60
        return 60 * (2 ** (attempt_number - 1))


async def run_delivery_worker(db: AsyncSession) -> int:
    """
    Convenience function to run the delivery worker.
    
    Args:
        db: Database session
        
    Returns:
        Number of deliveries processed
    """
    worker = DeliveryWorker(db)
    try:
        return await worker.run()
    finally:
        await worker.close()