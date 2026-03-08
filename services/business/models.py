from pydantic import BaseModel
from typing import Optional


class ServiceItem(BaseModel):
    name: str
    duration_minutes: int = 30
    price: float = 0.0
    capacity: int = 1


class DaySchedule(BaseModel):
    start: str = "09:00"
    end: str = "17:00"


class BusinessCreate(BaseModel):
    name: str
    slug: str
    description: str = ""
    services: list[ServiceItem] = []
    schedule: dict[str, DaySchedule] = {}
