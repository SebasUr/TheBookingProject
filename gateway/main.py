import os
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Booking Platform - API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ROUTES = {
    "businesses": os.getenv("BUSINESS_SERVICE_URL", "http://localhost:8001"),
    "bookings": os.getenv("BOOKING_SERVICE_URL", "http://localhost:8002"),
    "payments": os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8003"),
    "analytics": os.getenv("ANALYTICS_SERVICE_URL", "http://localhost:8004"),
}


async def _proxy(service: str, path: str, request: Request) -> Response:
    base_url = ROUTES.get(service)
    if not base_url:
        return Response(
            content='{"detail":"service not found"}',
            status_code=404,
            media_type="application/json",
        )
    url = f"{base_url}/{path}" if path else f"{base_url}/"
    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in ("host", "content-length")
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.request(
            method=request.method,
            url=url,
            content=await request.body(),
            headers=headers,
            params=dict(request.query_params),
        )
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type", "application/json"),
    )


@app.api_route(
    "/api/{service}/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
async def proxy_with_path(service: str, path: str, request: Request):
    return await _proxy(service, path, request)


@app.api_route(
    "/api/{service}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
async def proxy_root(service: str, request: Request):
    return await _proxy(service, "", request)


@app.get("/health")
async def health():
    return {"status": "ok"}
