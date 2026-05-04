from prometheus_client import Counter

PAYMENTS_COMPLETED = Counter(
    "payments_completed_total",
    "Completed payments",
)
PAYMENTS_COMPLETED_AMOUNT = Counter(
    "payments_completed_amount_total",
    "Total amount of completed payments",
)
PAYMENTS_FAILED = Counter(
    "payments_failed_total",
    "Failed payments",
)
PAYMENTS_FAILED_AMOUNT = Counter(
    "payments_failed_amount_total",
    "Total amount of failed payment attempts",
)
PAYMENTS_CIRCUIT_OPEN = Counter(
    "payments_circuit_open_total",
    "Payments blocked by circuit breaker",
)
PAYMENTS_CIRCUIT_OPEN_AMOUNT = Counter(
    "payments_circuit_open_amount_total",
    "Total amount blocked by the payment circuit breaker",
)
