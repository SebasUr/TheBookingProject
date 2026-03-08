from fastapi import APIRouter, HTTPException
from models import BusinessCreate

router = APIRouter()
repo = None


@router.get("/")
async def list_businesses():
    return await repo.find_all()


@router.post("/", status_code=201)
async def create_business(data: BusinessCreate):
    existing = await repo.find_by_slug(data.slug)
    if existing:
        raise HTTPException(400, "slug already exists")
    return await repo.create(data.model_dump())


@router.get("/slug/{slug}")
async def get_by_slug(slug: str):
    business = await repo.find_by_slug(slug)
    if not business:
        raise HTTPException(404, "business not found")
    return business


@router.get("/{id}")
async def get_business(id: str):
    business = await repo.find_by_id(id)
    if not business:
        raise HTTPException(404, "business not found")
    return business


@router.put("/{id}")
async def update_business(id: str, data: BusinessCreate):
    business = await repo.find_by_id(id)
    if not business:
        raise HTTPException(404, "business not found")
    return await repo.update(id, data.model_dump())


@router.delete("/{id}", status_code=204)
async def delete_business(id: str):
    deleted = await repo.delete(id)
    if not deleted:
        raise HTTPException(404, "business not found")
