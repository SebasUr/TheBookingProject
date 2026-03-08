import os
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from contextlib import asynccontextmanager
from controller import router
import controller
from repository import AnalyticsWriteRepository, AnalyticsReadRepository
from event_handler import AnalyticsEventHandler


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient(os.getenv("MONGO_URL", "mongodb://localhost:27017"))
    db = client[os.getenv("MONGO_DB", "analytics_db")]
    write_repo = AnalyticsWriteRepository(db)
    read_repo = AnalyticsReadRepository(db)
    controller.read_repo = read_repo

    handler = AnalyticsEventHandler(
        os.getenv("REDIS_URL", "redis://localhost:6379"),
        write_repo,
        read_repo,
    )
    await handler.start()

    yield

    await handler.stop()
    client.close()


app = FastAPI(title="Analytics Service", lifespan=lifespan)
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8004")))
