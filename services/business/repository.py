from bson import ObjectId
from datetime import datetime, timezone


class BusinessRepository:
    def __init__(self, db):
        self.collection = db["businesses"]

    async def find_all(self):
        cursor = self.collection.find()
        return [self._to_dict(doc) async for doc in cursor]

    async def find_by_id(self, id: str):
        doc = await self.collection.find_one({"_id": ObjectId(id)})
        return self._to_dict(doc) if doc else None

    async def find_by_slug(self, slug: str):
        doc = await self.collection.find_one({"slug": slug})
        return self._to_dict(doc) if doc else None

    async def create(self, data: dict):
        data["created_at"] = datetime.now(timezone.utc)
        result = await self.collection.insert_one(data)
        data["_id"] = result.inserted_id
        return self._to_dict(data)

    async def update(self, id: str, data: dict):
        data["updated_at"] = datetime.now(timezone.utc)
        await self.collection.update_one({"_id": ObjectId(id)}, {"$set": data})
        return await self.find_by_id(id)

    async def delete(self, id: str):
        result = await self.collection.delete_one({"_id": ObjectId(id)})
        return result.deleted_count > 0

    def _to_dict(self, doc):
        if not doc:
            return None
        doc = dict(doc)
        doc["id"] = str(doc.pop("_id"))
        if "created_at" in doc and hasattr(doc["created_at"], "isoformat"):
            doc["created_at"] = doc["created_at"].isoformat()
        if "updated_at" in doc and hasattr(doc["updated_at"], "isoformat"):
            doc["updated_at"] = doc["updated_at"].isoformat()
        return doc
