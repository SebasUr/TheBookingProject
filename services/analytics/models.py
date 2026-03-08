from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    business_id: str
    date: str
    total_bookings: int = 0
    confirmed_bookings: int = 0
    cancelled_bookings: int = 0
    total_revenue: float = 0.0
    bookings_by_service: dict = {}
