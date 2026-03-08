from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRepository:
    def __init__(self, db):
        self.collection = db["users"]

    async def find_by_email(self, email: str):
        doc = await self.collection.find_one({"email": email})
        return self._to_dict(doc) if doc else None

    async def create(self, data: dict):
        data["password_hash"] = pwd_context.hash(data.pop("password"))
        result = await self.collection.insert_one(data)
        data["_id"] = result.inserted_id
        return self._to_dict(data)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    def _to_dict(self, doc):
        if not doc:
            return None
        doc = dict(doc)
        doc["id"] = str(doc.pop("_id"))
        return doc
