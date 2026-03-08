import httpx
from events import EventPublisher


class BookingSaga:
    """Orchestrates the booking -> payment distributed transaction."""

    def __init__(
        self, booking_repo, payment_url: str, event_publisher: EventPublisher
    ):
        self.repo = booking_repo
        self.payment_url = payment_url
        self.events = event_publisher

    async def execute(self, booking: dict):
        booking_id = booking["id"]

        # Step 1: Booking already created in PENDING state
        await self.events.publish("booking.created", booking)

        # Step 2: Request payment
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{self.payment_url}/",
                    json={
                        "booking_id": booking_id,
                        "amount": booking.get("amount", 0),
                    },
                )

            if resp.status_code == 201:
                payment = resp.json()
                if payment.get("status") == "completed":
                    # Step 3a: Payment succeeded -> confirm booking
                    confirmed = await self.repo.update_status_optimistic(
                        booking_id, "confirmed", booking["version"]
                    )
                    await self.events.publish("booking.confirmed", confirmed)
                    return confirmed

            # Step 3b: Payment failed -> compensating transaction
            cancelled = await self.repo.update_status_optimistic(
                booking_id, "cancelled", booking["version"]
            )
            await self.events.publish("booking.cancelled", cancelled)
            return cancelled

        except Exception:
            # Compensating transaction on error
            try:
                cancelled = await self.repo.update_status_optimistic(
                    booking_id, "cancelled", booking["version"]
                )
                await self.events.publish("booking.cancelled", cancelled)
                return cancelled
            except Exception:
                return booking
