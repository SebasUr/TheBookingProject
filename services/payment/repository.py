from bson import ObjectId
from datetime import datetime, timezone


class PaymentRepository:
    def __init__(self, db):
        self.collection = db["payments"]

    async def find_by_id(self, id: str):
        doc = await self.collection.find_one({"_id": ObjectId(id)})
        return self._to_dict(doc) if doc else None

    async def find_by_booking(self, booking_id: str):
        doc = await self.collection.find_one({"booking_id": booking_id})
        return self._to_dict(doc) if doc else None

    async def create(self, data: dict):
        data["created_at"] = datetime.now(timezone.utc)
        result = await self.collection.insert_one(data)
        data["_id"] = result.inserted_id
        return self._to_dict(data)

    async def update_status(self, id: str, status: str):
        await self.collection.update_one(
            {"_id": ObjectId(id)}, {"$set": {"status": status}}
        )
        return await self.find_by_id(id)

    def _to_dict(self, doc):
        if not doc:
            return None
        doc = dict(doc)
        doc["id"] = str(doc.pop("_id"))
        if "created_at" in doc and hasattr(doc["created_at"], "isoformat"):
            doc["created_at"] = doc["created_at"].isoformat()
        return doc
