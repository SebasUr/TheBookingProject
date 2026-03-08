import json
import asyncio
import redis.asyncio as aioredis


class AnalyticsEventHandler:
    """
    CQRS event handler.
    Consumes domain events (write side) and updates read-optimized summaries.
    """

    def __init__(self, redis_url: str, write_repo, read_repo):
        self.redis_url = redis_url
        self.write_repo = write_repo
        self.read_repo = read_repo
        self._task = None

    async def start(self):
        self._task = asyncio.create_task(self._listen())

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _listen(self):
        r = aioredis.from_url(self.redis_url)
        pubsub = r.pubsub()
        await pubsub.subscribe("domain_events")
        print("[analytics] Listening for domain events...")
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            try:
                event = json.loads(message["data"])
                await self._handle(event)
            except Exception as e:
                print(f"[analytics] Error processing event: {e}")

    async def _handle(self, event: dict):
        event_type = event.get("type", "")
        data = event.get("data", {})

        # Write side: store raw event
        await self.write_repo.store_event(event)

        business_id = data.get("business_id", "")
        date = data.get("date", "")

        if not business_id or not date:
            return

        # Read side: update aggregated summaries
        if event_type == "booking.created":
            await self.read_repo.increment_summary(
                business_id, date, "total_bookings"
            )
            service_name = data.get("service_name", "unknown")
            await self.read_repo.increment_service_count(
                business_id, date, service_name
            )

        elif event_type == "booking.confirmed":
            await self.read_repo.increment_summary(
                business_id, date, "confirmed_bookings"
            )
            amount = data.get("amount", 0)
            if amount:
                await self.read_repo.increment_summary(
                    business_id, date, "total_revenue", amount
                )

        elif event_type == "booking.cancelled":
            await self.read_repo.increment_summary(
                business_id, date, "cancelled_bookings"
            )
