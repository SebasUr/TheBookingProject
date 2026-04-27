from prometheus_client import Counter

BOOKINGS_CONFIRMED = Counter(
    "bookings_confirmed_total",
    "Confirmed bookings",
)
BOOKINGS_CREATED = Counter(
    "bookings_created_total",
    "Created bookings",
)
BOOKINGS_CANCELLED = Counter(
    "bookings_cancelled_total",
    "Cancelled bookings",
)
