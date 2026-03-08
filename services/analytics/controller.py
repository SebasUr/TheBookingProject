from fastapi import APIRouter, Query

router = APIRouter()
read_repo = None


@router.get("/summary/{business_id}")
async def get_summary(
    business_id: str,
    start: str = Query(None),
    end: str = Query(None),
):
    return await read_repo.get_summary(business_id, start, end)


@router.get("/totals/{business_id}")
async def get_totals(business_id: str):
    return await read_repo.get_totals(business_id)
