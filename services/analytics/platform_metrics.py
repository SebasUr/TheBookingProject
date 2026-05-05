import asyncio
import contextlib

from prometheus_client import Gauge

PLATFORM_TOTAL_BOOKINGS = Gauge(
    "platform_total_bookings",
    "Total bookings across the platform aggregated from analytics summaries",
)
PLATFORM_CONFIRMED_BOOKINGS = Gauge(
    "platform_confirmed_bookings",
    "Total confirmed bookings across the platform aggregated from analytics summaries",
)
PLATFORM_CANCELLED_BOOKINGS = Gauge(
    "platform_cancelled_bookings",
    "Total cancelled bookings across the platform aggregated from analytics summaries",
)
PLATFORM_TOTAL_REVENUE = Gauge(
    "platform_total_revenue",
    "Total captured GMV across the platform aggregated from analytics summaries",
)


class PlatformMetricsRefresher:
    def __init__(self, read_repo, refresh_interval_seconds: int = 15):
        self.read_repo = read_repo
        self.refresh_interval_seconds = refresh_interval_seconds
        self._task = None

    async def start(self):
        await self.refresh_once()
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    async def _run(self):
        while True:
            await asyncio.sleep(self.refresh_interval_seconds)
            await self.refresh_once()

    async def refresh_once(self):
        totals = await self.read_repo.get_platform_totals()
        PLATFORM_TOTAL_BOOKINGS.set(totals.get("total_bookings", 0))
        PLATFORM_CONFIRMED_BOOKINGS.set(totals.get("confirmed_bookings", 0))
        PLATFORM_CANCELLED_BOOKINGS.set(totals.get("cancelled_bookings", 0))
        PLATFORM_TOTAL_REVENUE.set(totals.get("total_revenue", 0))
