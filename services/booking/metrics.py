from prometheus_client import Counter

BOOKINGS_CONFIRMED = Counter(
    "bookings_confirmed_total",
    "Confirmed bookings",
)
BOOKINGS_CONFIRMED_AMOUNT = Counter(
    "bookings_confirmed_amount_total",
    "Gross booking value confirmed",
)
BOOKINGS_CREATED = Counter(
    "bookings_created_total",
    "Created bookings",
)
BOOKINGS_CREATED_AMOUNT = Counter(
    "bookings_created_amount_total",
    "Gross booking value created",
)
BOOKINGS_CANCELLED = Counter(
    "bookings_cancelled_total",
    "Cancelled bookings",
)
BOOKINGS_CANCELLED_AMOUNT = Counter(
    "bookings_cancelled_amount_total",
    "Gross booking value cancelled",
)
