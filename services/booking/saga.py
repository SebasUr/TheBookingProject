import asyncio
import random

import httpx
from events import EventPublisher
from metrics import (
    BOOKINGS_CONFIRMED,
    BOOKINGS_CONFIRMED_AMOUNT,
    BOOKINGS_CANCELLED,
    BOOKINGS_CANCELLED_AMOUNT,
)

PAYMENT_MAX_ATTEMPTS = 3
PAYMENT_BASE_DELAY = 0.2
PAYMENT_MAX_DELAY = 2.0
PAYMENT_JITTER = 0.2


class BookingSaga:
    """Orchestrates the booking -> payment distributed transaction."""

    def __init__(
        self,
        booking_repo,
        payment_url: str,
        event_publisher: EventPublisher,
        payment_client: httpx.AsyncClient,
    ):
        self.repo = booking_repo
        self.payment_url = payment_url
        self.events = event_publisher
        self.payment_client = payment_client

    async def _sleep_backoff(self, attempt: int) -> None:
        delay = min(PAYMENT_MAX_DELAY, PAYMENT_BASE_DELAY * (2 ** (attempt - 1)))
        delay += random.uniform(0, PAYMENT_JITTER)
        await asyncio.sleep(delay)

    async def _request_payment(self, booking_id: str, amount: float):
        payload = {"booking_id": booking_id, "amount": amount}
        for attempt in range(1, PAYMENT_MAX_ATTEMPTS + 1):
            try:
                resp = await self.payment_client.post(
                    f"{self.payment_url}/",
                    json=payload,
                )
            except httpx.RequestError:
                if attempt >= PAYMENT_MAX_ATTEMPTS:
                    raise
                await self._sleep_backoff(attempt)
                continue

            if resp.status_code >= 500 and attempt < PAYMENT_MAX_ATTEMPTS:
                await self._sleep_backoff(attempt)
                continue
            return resp

    async def execute(self, booking: dict):
        booking_id = booking["id"]

        # Step 1: Booking already created in PENDING state
        await self.events.publish("booking.created", booking)

        # Step 2: Request payment
        try:
            resp = await self._request_payment(
                booking_id, booking.get("amount", 0)
            )

            if resp.status_code == 201:
                payment = resp.json()
                if payment.get("status") == "completed":
                    # Step 3a: Payment succeeded -> confirm booking
                    confirmed = await self.repo.update_status_optimistic(
                        booking_id, "confirmed", booking["version"]
                    )
                    await self.events.publish("booking.confirmed", confirmed)
                    BOOKINGS_CONFIRMED.inc()
                    BOOKINGS_CONFIRMED_AMOUNT.inc(booking.get("amount", 0))
                    return confirmed

            # Step 3b: Payment failed -> compensating transaction
            cancelled = await self.repo.update_status_optimistic(
                booking_id, "cancelled", booking["version"]
            )
            await self.events.publish("booking.cancelled", cancelled)
            BOOKINGS_CANCELLED.inc()
            BOOKINGS_CANCELLED_AMOUNT.inc(booking.get("amount", 0))
            return cancelled

        except Exception:
            # Compensating transaction on error
            try:
                cancelled = await self.repo.update_status_optimistic(
                    booking_id, "cancelled", booking["version"]
                )
                await self.events.publish("booking.cancelled", cancelled)
                BOOKINGS_CANCELLED.inc()
                BOOKINGS_CANCELLED_AMOUNT.inc(booking.get("amount", 0))
                return cancelled
            except Exception:
                return booking
