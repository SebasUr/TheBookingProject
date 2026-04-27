from prometheus_client import Counter

PAYMENTS_COMPLETED = Counter(
    "payments_completed_total",
    "Completed payments",
)
PAYMENTS_FAILED = Counter(
    "payments_failed_total",
    "Failed payments",
)
PAYMENTS_CIRCUIT_OPEN = Counter(
    "payments_circuit_open_total",
    "Payments blocked by circuit breaker",
)
