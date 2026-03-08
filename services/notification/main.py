import os
import json
import asyncio
import redis.asyncio as aioredis


async def handle_event(event: dict):
    event_type = event.get("type", "")
    data = event.get("data", {})

    customer = data.get("customer_name", "N/A")
    email = data.get("customer_email", "N/A")
    booking_id = data.get("id", data.get("booking_id", "N/A"))

    if event_type == "booking.confirmed":
        print(
            f"[NOTIFICATION] -> {email}: "
            f"Booking {booking_id} confirmed for {customer}"
        )
    elif event_type == "booking.cancelled":
        print(
            f"[NOTIFICATION] -> {email}: "
            f"Booking {booking_id} cancelled for {customer}"
        )
    elif event_type == "payment.completed":
        print(
            f"[NOTIFICATION] -> Payment completed for booking {booking_id}"
        )
    elif event_type == "booking.created":
        print(
            f"[NOTIFICATION] -> {email}: "
            f"Booking {booking_id} created (pending) for {customer}"
        )


async def main():
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    r = aioredis.from_url(redis_url)
    pubsub = r.pubsub()
    await pubsub.subscribe("domain_events")
    print("[notification-service] Listening for events...")

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        try:
            event = json.loads(message["data"])
            await handle_event(event)
        except Exception as e:
            print(f"[notification-service] Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
