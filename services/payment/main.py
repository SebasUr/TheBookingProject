import os
import json
import redis.asyncio as aioredis
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from controller import router
import controller
from repository import PaymentRepository


class EventPublisher:
    def __init__(self, redis_url: str):
        self.redis = aioredis.from_url(redis_url)

    async def publish(self, event_type: str, data: dict):
        event = {"type": event_type, "data": data}
        await self.redis.publish("domain_events", json.dumps(event, default=str))

    async def close(self):
        await self.redis.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient(os.getenv("MONGO_URL", "mongodb://localhost:27017"))
    db = client[os.getenv("MONGO_DB", "payment_db")]
    controller.repo = PaymentRepository(db)
    controller.event_publisher = EventPublisher(
        os.getenv("REDIS_URL", "redis://localhost:6379")
    )
    yield
    await controller.event_publisher.close()
    client.close()


app = FastAPI(title="Payment Service", lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8003")))
