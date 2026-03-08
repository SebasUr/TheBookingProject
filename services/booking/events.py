import json
import redis.asyncio as aioredis


class EventPublisher:
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)

    async def publish(self, event_type: str, data: dict):
        event = {"type": event_type, "data": data}
        await self.redis.publish("domain_events", json.dumps(event, default=str))

    async def close(self):
        await self.redis.close()
