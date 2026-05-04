import os
import random
import uuid
from datetime import datetime, timedelta

from locust import HttpUser, between, task


DAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

CUSTOMER_NAMES = [
    "Ana Gomez",
    "Carlos Ruiz",
    "Laura Perez",
    "Miguel Torres",
    "Sofia Martinez",
]

SERVICE_NAMES = [
    "Standard Service",
    "Express Service",
    "Premium Service",
]

BOOKING_INTENT_RATE = float(os.getenv("BOOKING_INTENT_RATE", "0.45"))
CANCEL_AFTER_BOOKING_RATE = float(os.getenv("CANCEL_AFTER_BOOKING_RATE", "0.08"))
OWNER_FLOW_RATE = float(os.getenv("OWNER_FLOW_RATE", "0.12"))


class BookingPlatformUser(HttpUser):
    wait_time = between(2, 7)
    host = os.getenv("TARGET_HOST", "http://localhost:8000")

    catalog = []

    def on_start(self):
        self.user_suffix = uuid.uuid4().hex[:8]
        self.user_email = f"locust_{self.user_suffix}@example.com"
        self.user_password = "locust_password"
        self.token = None
        self.owned_business_id = None
        self.owned_business_slug = None
        self.recent_bookings = []

        self._register_or_login()
        self._refresh_catalog()
        if not self.catalog:
            self._create_business()
            self._refresh_catalog()

    def _auth_headers(self):
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    def _expect(self, resp, ok):
        if resp.status_code not in ok:
            resp.failure(f"Unexpected status {resp.status_code}: {resp.text}")
        return resp

    def _json(self, resp, fallback=None):
        try:
            return resp.json()
        except Exception:
            return fallback

    def _register_or_login(self):
        payload = {
            "email": self.user_email,
            "password": self.user_password,
            "name": f"Locust {self.user_suffix}",
        }
        with self.client.post(
            "/api/auth/register",
            json=payload,
            catch_response=True,
            name="/api/auth/register",
        ) as resp:
            if resp.status_code == 201:
                self.token = self._json(resp, {}).get("access_token")
                return
            if resp.status_code != 400:
                self._expect(resp, (201, 400))
                return

        with self.client.post(
            "/api/auth/login",
            json={"email": self.user_email, "password": self.user_password},
            catch_response=True,
            name="/api/auth/login",
        ) as resp:
            self._expect(resp, (200,))
            self.token = self._json(resp, {}).get("access_token")

    def _business_payload(self, slug):
        schedule = {day: {"start": "09:00", "end": "18:00"} for day in DAYS}
        return {
            "name": f"Locust Studio {slug[-6:]}",
            "slug": slug,
            "description": "Seed business used by realistic load journeys",
            "services": [
                {
                    "name": SERVICE_NAMES[0],
                    "duration_minutes": 30,
                    "price": 25.0,
                    "capacity": 8,
                },
                {
                    "name": SERVICE_NAMES[1],
                    "duration_minutes": 45,
                    "price": 40.0,
                    "capacity": 5,
                },
                {
                    "name": SERVICE_NAMES[2],
                    "duration_minutes": 60,
                    "price": 65.0,
                    "capacity": 3,
                },
            ],
            "schedule": schedule,
        }

    def _create_business(self):
        slug = f"locust-{uuid.uuid4().hex[:8]}"
        with self.client.post(
            "/api/businesses",
            json=self._business_payload(slug),
            headers=self._auth_headers(),
            catch_response=True,
            name="/api/businesses [owner creates business]",
        ) as resp:
            if resp.status_code == 201:
                business = self._json(resp, {})
                self.owned_business_id = business.get("id")
                self.owned_business_slug = business.get("slug", slug)
                self.catalog.append(business)
                return business
            self._expect(resp, (201, 400, 401))
        return None

    def _refresh_catalog(self):
        with self.client.get(
            "/api/businesses",
            catch_response=True,
            name="/api/businesses [browse catalog]",
        ) as resp:
            self._expect(resp, (200,))
            businesses = self._json(resp, [])
            if isinstance(businesses, list):
                self.catalog = [
                    b for b in businesses if b.get("id") and b.get("services")
                ]
            return self.catalog

    def _choose_business(self):
        if not self.catalog or random.random() < 0.2:
            self._refresh_catalog()
        if not self.catalog:
            business = self._create_business()
            if business:
                return business
            return None
        return random.choice(self.catalog)

    def _view_business_detail(self, business):
        business_id = business.get("id")
        if not business_id:
            return business

        with self.client.get(
            f"/api/businesses/{business_id}",
            catch_response=True,
            name="/api/businesses/{id} [view detail]",
        ) as resp:
            if resp.status_code == 200:
                return self._json(resp, business)
            self._expect(resp, (200, 404))
        return business

    def _future_date(self):
        days_ahead = random.randint(1, 14)
        return (datetime.utcnow().date() + timedelta(days=days_ahead)).isoformat()

    def _select_service(self, business):
        services = business.get("services") or []
        if not services:
            return None
        return random.choice(services)

    def _get_slots(self, business, service, booking_date):
        params = {
            "business_id": business.get("id"),
            "service_name": service.get("name"),
            "date": booking_date,
        }
        with self.client.get(
            "/api/bookings/slots",
            params=params,
            catch_response=True,
            name="/api/bookings/slots [check availability]",
        ) as resp:
            self._expect(resp, (200, 404))
            if resp.status_code != 200:
                return []
            slots = self._json(resp, [])
            return slots if isinstance(slots, list) else []

    def _create_booking(self, business, service, booking_date, slot):
        amount = float(service.get("price", 0) or 0)
        payload = {
            "business_id": business.get("id"),
            "service_name": service.get("name"),
            "customer_name": random.choice(CUSTOMER_NAMES),
            "customer_email": self.user_email,
            "date": booking_date,
            "time_slot": slot["time"],
            "amount": amount,
        }
        with self.client.post(
            "/api/bookings",
            json=payload,
            catch_response=True,
            name="/api/bookings [reserve and pay]",
        ) as resp:
            self._expect(resp, (200, 201, 409))
            if resp.status_code not in (200, 201):
                return None

            booking = self._json(resp, {})
            if booking.get("id"):
                self.recent_bookings.append(booking)
                self.recent_bookings = self.recent_bookings[-5:]
            return booking

    def _view_booking(self, booking):
        booking_id = booking.get("id")
        if not booking_id:
            return

        with self.client.get(
            f"/api/bookings/{booking_id}",
            catch_response=True,
            name="/api/bookings/{id} [view confirmation]",
        ) as resp:
            self._expect(resp, (200, 404))

    @task(9)
    def customer_booking_journey(self):
        business = self._choose_business()
        if not business:
            return

        business = self._view_business_detail(business)
        service = self._select_service(business)
        if not service:
            return

        booking_date = self._future_date()
        slots = self._get_slots(business, service, booking_date)
        if not slots:
            return

        if random.random() > BOOKING_INTENT_RATE:
            return

        booking = self._create_booking(business, service, booking_date, slots[0])
        if not booking:
            return

        self._view_booking(booking)

        if (
            booking.get("status") == "confirmed"
            and random.random() < CANCEL_AFTER_BOOKING_RATE
        ):
            with self.client.post(
                f"/api/bookings/{booking['id']}/cancel",
                headers=self._auth_headers(),
                catch_response=True,
                name="/api/bookings/{id}/cancel [user cancels]",
            ) as resp:
                self._expect(resp, (200, 400, 404))

    @task(3)
    def returning_user_checks_reservations(self):
        if not self.recent_bookings:
            self.customer_booking_journey()
            return

        booking = random.choice(self.recent_bookings)
        self._view_booking(booking)

    @task(2)
    def authenticated_session_check(self):
        if random.random() < 0.35:
            self._register_or_login()

        with self.client.get(
            "/api/auth/me",
            headers=self._auth_headers(),
            catch_response=True,
            name="/api/auth/me [session]",
        ) as resp:
            self._expect(resp, (200, 401))

    @task(1)
    def owner_dashboard_journey(self):
        if random.random() > OWNER_FLOW_RATE:
            return

        if not self.owned_business_id:
            business = self._create_business()
            if not business:
                return

        with self.client.get(
            f"/api/bookings?business_id={self.owned_business_id}",
            headers=self._auth_headers(),
            catch_response=True,
            name="/api/bookings?business_id=... [owner calendar]",
        ) as resp:
            self._expect(resp, (200, 401))

        with self.client.get(
            f"/api/analytics/summary/{self.owned_business_id}",
            headers=self._auth_headers(),
            catch_response=True,
            name="/api/analytics/summary/{business_id} [owner]",
        ) as resp:
            self._expect(resp, (200, 403, 404))
