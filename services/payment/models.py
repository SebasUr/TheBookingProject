from pydantic import BaseModel


class PaymentCreate(BaseModel):
    booking_id: str
    amount: float
