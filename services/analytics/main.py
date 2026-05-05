import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from prometheus_fastapi_instrumentator import Instrumentator
from controller import router
import controller
from repository import AnalyticsWriteRepository, AnalyticsReadRepository
from event_handler import AnalyticsEventHandler
from platform_metrics import PlatformMetricsRefresher

BUSINESS_TIMEOUT = 5.0
POOL_LIMITS = httpx.Limits(max_connections=10, max_keepalive_connections=5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient(os.getenv("MONGO_URL", "mongodb://localhost:27017"))
    db = client[os.getenv("MONGO_DB", "analytics_db")]
    write_repo = AnalyticsWriteRepository(db)
    read_repo = AnalyticsReadRepository(db)
    controller.read_repo = read_repo
    controller.business_client = httpx.AsyncClient(
        timeout=httpx.Timeout(BUSINESS_TIMEOUT),
        limits=POOL_LIMITS,
    )

    handler = AnalyticsEventHandler(
        os.getenv("REDIS_URL", "redis://localhost:6379"),
        write_repo,
        read_repo,
    )
    metrics_refresher = PlatformMetricsRefresher(read_repo)
    await handler.start()
    await metrics_refresher.start()

    yield

    await metrics_refresher.stop()
    await handler.stop()
    await controller.business_client.aclose()
    client.close()


app = FastAPI(title="Analytics Service", lifespan=lifespan)
Instrumentator().instrument(app).expose(
    app, endpoint="/metrics", include_in_schema=False
)
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8004")))
