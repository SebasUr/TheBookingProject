import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from prometheus_fastapi_instrumentator import Instrumentator
from controller import router
import controller
from repository import BookingRepository
from saga import BookingSaga
from events import EventPublisher

BUSINESS_TIMEOUT = 10.0
PAYMENT_TIMEOUT = 15.0
POOL_LIMITS = httpx.Limits(max_connections=10, max_keepalive_connections=5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient(os.getenv("MONGO_URL", "mongodb://localhost:27017"))
    db = client[os.getenv("MONGO_DB", "booking_db")]
    controller.repo = BookingRepository(db)
    event_pub = EventPublisher(os.getenv("REDIS_URL", "redis://localhost:6379"))
    business_client = httpx.AsyncClient(
        timeout=httpx.Timeout(BUSINESS_TIMEOUT),
        limits=POOL_LIMITS,
    )
    payment_client = httpx.AsyncClient(
        timeout=httpx.Timeout(PAYMENT_TIMEOUT),
        limits=POOL_LIMITS,
    )
    controller.saga = BookingSaga(
        controller.repo,
        os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8003"),
        event_pub,
        payment_client,
    )
    controller.business_service_url = os.getenv(
        "BUSINESS_SERVICE_URL", "http://localhost:8001"
    )
    controller.business_client = business_client
    yield
    await business_client.aclose()
    await payment_client.aclose()
    await event_pub.close()
    client.close()


app = FastAPI(title="Booking Service", lifespan=lifespan)
Instrumentator().instrument(app).expose(
    app, endpoint="/metrics", include_in_schema=False
)
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8002")))
