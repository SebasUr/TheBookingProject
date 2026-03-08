from datetime import datetime, timezone


class AnalyticsWriteRepository:
    """CQRS Write Side: stores raw domain events."""

    def __init__(self, db):
        self.events = db["events"]

    async def store_event(self, event: dict):
        event["stored_at"] = datetime.now(timezone.utc)
        await self.events.insert_one(event)


class AnalyticsReadRepository:
    """CQRS Read Side: stores and queries pre-aggregated summaries."""

    def __init__(self, db):
        self.summaries = db["summaries"]

    async def get_summary(
        self, business_id: str, start_date: str = None, end_date: str = None
    ):
        query = {"business_id": business_id}
        if start_date or end_date:
            query["date"] = {}
            if start_date:
                query["date"]["$gte"] = start_date
            if end_date:
                query["date"]["$lte"] = end_date

        cursor = self.summaries.find(query).sort("date", -1)
        return [self._to_dict(doc) async for doc in cursor]

    async def increment_summary(
        self, business_id: str, date: str, field: str, amount=1
    ):
        await self.summaries.update_one(
            {"business_id": business_id, "date": date},
            {
                "$inc": {field: amount},
                "$setOnInsert": {"business_id": business_id, "date": date},
            },
            upsert=True,
        )

    async def increment_service_count(
        self, business_id: str, date: str, service_name: str
    ):
        safe_name = service_name.replace(".", "_")
        await self.summaries.update_one(
            {"business_id": business_id, "date": date},
            {
                "$inc": {f"bookings_by_service.{safe_name}": 1},
                "$setOnInsert": {"business_id": business_id, "date": date},
            },
            upsert=True,
        )

    async def get_totals(self, business_id: str):
        pipeline = [
            {"$match": {"business_id": business_id}},
            {
                "$group": {
                    "_id": "$business_id",
                    "total_bookings": {"$sum": "$total_bookings"},
                    "confirmed_bookings": {"$sum": "$confirmed_bookings"},
                    "cancelled_bookings": {"$sum": "$cancelled_bookings"},
                    "total_revenue": {"$sum": "$total_revenue"},
                }
            },
        ]
        async for doc in self.summaries.aggregate(pipeline):
            doc.pop("_id", None)
            return doc
        return {
            "total_bookings": 0,
            "confirmed_bookings": 0,
            "cancelled_bookings": 0,
            "total_revenue": 0,
        }

    def _to_dict(self, doc):
        if not doc:
            return None
        doc = dict(doc)
        doc["id"] = str(doc.pop("_id"))
        return doc
