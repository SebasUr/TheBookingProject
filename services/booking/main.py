import os
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from controller import router
import controller
from repository import BookingRepository
from saga import BookingSaga
from events import EventPublisher


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient(os.getenv("MONGO_URL", "mongodb://localhost:27017"))
    db = client[os.getenv("MONGO_DB", "booking_db")]
    controller.repo = BookingRepository(db)
    event_pub = EventPublisher(os.getenv("REDIS_URL", "redis://localhost:6379"))
    controller.saga = BookingSaga(
        controller.repo,
        os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8003"),
        event_pub,
    )
    controller.business_service_url = os.getenv(
        "BUSINESS_SERVICE_URL", "http://localhost:8001"
    )
    yield
    await event_pub.close()
    client.close()


app = FastAPI(title="Booking Service", lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8002")))
