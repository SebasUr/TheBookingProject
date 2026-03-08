import uuid
from fastapi import APIRouter, HTTPException
from models import PaymentCreate
from circuit_breaker import CircuitBreaker

router = APIRouter()
repo = None
event_publisher = None
circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)


async def call_external_payment_provider(amount: float) -> dict:
    """
    Simulates an external payment provider call (e.g. Stripe, MercadoPago).
    In production, this would be an HTTP call to the provider's API.
    The circuit breaker wraps this call.
    """
    return {
        "provider_ref": f"pay_{uuid.uuid4().hex[:12]}",
        "status": "completed",
    }


@router.post("/", status_code=201)
async def create_payment(data: PaymentCreate):
    # Circuit breaker check
    if not circuit_breaker.can_execute():
        raise HTTPException(
            503,
            f"Payment service unavailable (circuit: {circuit_breaker.get_state()})",
        )

    try:
        # External call wrapped by circuit breaker
        external_result = await call_external_payment_provider(data.amount)
        circuit_breaker.record_success()
    except Exception:
        circuit_breaker.record_failure()
        raise HTTPException(502, "Payment provider failed")

    payment = await repo.create(
        {
            "booking_id": data.booking_id,
            "amount": data.amount,
            "status": external_result["status"],
            "provider_ref": external_result["provider_ref"],
        }
    )

    if event_publisher:
        await event_publisher.publish("payment.completed", payment)

    return payment


@router.get("/{id}")
async def get_payment(id: str):
    payment = await repo.find_by_id(id)
    if not payment:
        raise HTTPException(404, "payment not found")
    return payment


@router.get("/booking/{booking_id}")
async def get_payment_by_booking(booking_id: str):
    payment = await repo.find_by_booking(booking_id)
    if not payment:
        raise HTTPException(404, "payment not found")
    return payment


@router.get("/circuit-breaker/status")
async def circuit_status():
    return {
        "state": circuit_breaker.get_state(),
        "failure_count": circuit_breaker.failure_count,
    }
