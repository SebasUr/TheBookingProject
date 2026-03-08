from bson import ObjectId
from datetime import datetime, timezone
from fastapi import HTTPException


class BookingRepository:
    def __init__(self, db):
        self.collection = db["bookings"]

    async def find_all(self, business_id: str = None):
        query = {}
        if business_id:
            query["business_id"] = business_id
        cursor = self.collection.find(query).sort("created_at", -1)
        return [self._to_dict(doc) async for doc in cursor]

    async def find_by_id(self, id: str):
        doc = await self.collection.find_one({"_id": ObjectId(id)})
        return self._to_dict(doc) if doc else None

    async def find_by_date(self, business_id: str, service_name: str, date: str):
        cursor = self.collection.find(
            {
                "business_id": business_id,
                "service_name": service_name,
                "date": date,
                "status": {"$ne": "cancelled"},
            }
        )
        return [self._to_dict(doc) async for doc in cursor]

    async def create(self, data: dict):
        data["status"] = "pending"
        data["version"] = 1
        data["created_at"] = datetime.now(timezone.utc)
        data["updated_at"] = datetime.now(timezone.utc)
        result = await self.collection.insert_one(data)
        data["_id"] = result.inserted_id
        return self._to_dict(data)

    async def update_status_optimistic(
        self, id: str, new_status: str, expected_version: int
    ):
        """Optimistic locking: only updates if version matches."""
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(id), "version": expected_version},
            {
                "$set": {
                    "status": new_status,
                    "updated_at": datetime.now(timezone.utc),
                },
                "$inc": {"version": 1},
            },
            return_document=True,
        )
        if not result:
            raise HTTPException(
                409, "Conflict: booking was modified by another process"
            )
        return self._to_dict(result)

    def _to_dict(self, doc):
        if not doc:
            return None
        doc = dict(doc)
        doc["id"] = str(doc.pop("_id"))
        for field in ("created_at", "updated_at"):
            if field in doc and hasattr(doc[field], "isoformat"):
                doc[field] = doc[field].isoformat()
        return doc
