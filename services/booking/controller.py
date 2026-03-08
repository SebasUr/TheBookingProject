from fastapi import APIRouter, HTTPException, Query
from models import BookingCreate
from datetime import datetime as dt
import httpx

router = APIRouter()
repo = None
saga = None
business_service_url = None


@router.get("/")
async def list_bookings(business_id: str = Query(None)):
    return await repo.find_all(business_id)


@router.get("/slots")
async def get_available_slots(
    business_id: str = Query(...),
    service_name: str = Query(...),
    date: str = Query(...),
):
    # Fetch business config from Business Service
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{business_service_url}/{business_id}")
        if resp.status_code != 200:
            raise HTTPException(404, "business not found")
        business = resp.json()

    # Find the service definition
    service = None
    for s in business.get("services", []):
        if s["name"] == service_name:
            service = s
            break
    if not service:
        raise HTTPException(404, "service not found")

    # Determine day of week
    try:
        parsed_date = dt.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(400, "invalid date format, use YYYY-MM-DD")

    day_name = parsed_date.strftime("%A").lower()
    schedule = business.get("schedule", {}).get(day_name)
    if not schedule:
        return []

    # Generate time slots based on service duration
    duration = service["duration_minutes"]
    capacity = service.get("capacity", 1)

    start_h, start_m = map(int, schedule["start"].split(":"))
    end_h, end_m = map(int, schedule["end"].split(":"))
    start_total = start_h * 60 + start_m
    end_total = end_h * 60 + end_m

    slots = []
    t = start_total
    while t + duration <= end_total:
        h, m = divmod(t, 60)
        slots.append(f"{h:02d}:{m:02d}")
        t += duration

    # Check existing bookings for this date
    bookings = await repo.find_by_date(business_id, service_name, date)
    booked_counts = {}
    for b in bookings:
        slot = b["time_slot"]
        booked_counts[slot] = booked_counts.get(slot, 0) + 1

    # Return only available slots
    available = []
    for slot in slots:
        used = booked_counts.get(slot, 0)
        if used < capacity:
            available.append({"time": slot, "remaining": capacity - used})

    return available


@router.post("/", status_code=201)
async def create_booking(data: BookingCreate):
    booking = await repo.create(data.model_dump())

    if data.amount > 0:
        # Execute saga: booking -> payment
        result = await saga.execute(booking)
        return result
    else:
        # No payment required, confirm immediately
        confirmed = await repo.update_status_optimistic(
            booking["id"], "confirmed", booking["version"]
        )
        await saga.events.publish("booking.confirmed", confirmed)
        return confirmed


@router.get("/{id}")
async def get_booking(id: str):
    booking = await repo.find_by_id(id)
    if not booking:
        raise HTTPException(404, "booking not found")
    return booking


@router.post("/{id}/cancel")
async def cancel_booking(id: str):
    booking = await repo.find_by_id(id)
    if not booking:
        raise HTTPException(404, "booking not found")
    if booking["status"] == "cancelled":
        raise HTTPException(400, "already cancelled")

    cancelled = await repo.update_status_optimistic(
        id, "cancelled", booking["version"]
    )
    await saga.events.publish("booking.cancelled", cancelled)
    return cancelled
