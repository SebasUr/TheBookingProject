from pydantic import BaseModel


class BookingCreate(BaseModel):
    business_id: str
    service_name: str
    customer_name: str
    customer_email: str
    date: str
    time_slot: str
    amount: float = 0.0
