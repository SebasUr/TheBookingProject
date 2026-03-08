import os
import httpx
from fastapi import APIRouter, Query, Header, HTTPException

router = APIRouter()
read_repo = None

BUSINESS_SERVICE_URL = os.getenv("BUSINESS_SERVICE_URL", "http://localhost:8001")


async def _assert_owner(business_id: str, user_id: str | None) -> None:
    """Raise 403 if the given user is not the owner of the business."""
    if not user_id:
        raise HTTPException(401, "authentication required")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{BUSINESS_SERVICE_URL}/{business_id}")
            if resp.status_code != 200:
                raise HTTPException(404, "business not found")
            business = resp.json()
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(503, "could not reach business service")
    if business.get("owner_id") != user_id:
        raise HTTPException(403, "access denied")


@router.get("/summary/{business_id}")
async def get_summary(
    business_id: str,
    x_user_id: str = Header(None),
    start: str = Query(None),
    end: str = Query(None),
):
    await _assert_owner(business_id, x_user_id)
    return await read_repo.get_summary(business_id, start, end)


@router.get("/totals/{business_id}")
async def get_totals(
    business_id: str,
    x_user_id: str = Header(None),
):
    await _assert_owner(business_id, x_user_id)
    return await read_repo.get_totals(business_id)
