import os
import uuid
from datetime import datetime

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


class BookingPlatformUser(HttpUser):
    wait_time = between(1, 3)
    host = os.getenv("TARGET_HOST", "http://localhost:8000")

    def on_start(self):
        self.user_suffix = uuid.uuid4().hex[:8]
        self.user_email = f"locust_{self.user_suffix}@example.com"
        self.user_password = "locust_password"
        self.token = None
        self.business_id = None
        self.business_slug = None
        self.service_name = "Standard Service"
        self.booking_id = None
        self.payment_id = None
        self.payment_booking_id = None
        self.booking_date = datetime.utcnow().date().isoformat()

        self._register_or_login()
        self._create_business()

    def _auth_headers(self):
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    def _expect(self, resp, ok):
        if resp.status_code not in ok:
            resp.failure(
                f"Unexpected status {resp.status_code}: {resp.text}"
            )
        return resp

    def _register_or_login(self):
        payload = {
            "email": self.user_email,
            "password": self.user_password,
            "name": f"Locust {self.user_suffix}",
        }
        with self.client.post(
            "/api/auth/register", json=payload, catch_response=True
        ) as resp:
            if resp.status_code == 201:
                data = resp.json()
                self.token = data.get("access_token")
                return
            if resp.status_code != 400:
                self._expect(resp, (201, 400))
                return

        with self.client.post(
            "/api/auth/login",
            json={
                "email": self.user_email,
                "password": self.user_password,
            },
            catch_response=True,
        ) as resp:
            self._expect(resp, (200,))
            data = resp.json()
            self.token = data.get("access_token")

    def _business_payload(self, slug):
        schedule = {day: {"start": "09:00", "end": "17:00"} for day in DAYS}
        return {
            "name": f"Locust Biz {slug}",
            "slug": slug,
            "description": "Load test business",
            "services": [
                {
                    "name": self.service_name,
                    "duration_minutes": 30,
                    "price": 25.0,
                    "capacity": 2,
                }
            ],
            "schedule": schedule,
        }

    def _create_business(self):
        slug = f"locust-{self.user_suffix}"
        payload = self._business_payload(slug)
        with self.client.post(
            "/api/businesses",
            json=payload,
            headers=self._auth_headers(),
            catch_response=True,
        ) as resp:
            if resp.status_code == 201:
                data = resp.json()
                self.business_id = data.get("id")
                self.business_slug = slug
                return
            if resp.status_code == 400:
                slug = f"locust-{uuid.uuid4().hex[:8]}"
                payload = self._business_payload(slug)
                with self.client.post(
                    "/api/businesses",
                    json=payload,
                    headers=self._auth_headers(),
                    catch_response=True,
                ) as retry:
                    self._expect(retry, (201,))
                    data = retry.json()
                    self.business_id = data.get("id")
                    self.business_slug = slug
                    return
            self._expect(resp, (201,))

    def _get_slot(self):
        if not self.business_id:
            return "09:00"
        params = {
            "business_id": self.business_id,
            "service_name": self.service_name,
            "date": self.booking_date,
        }
        with self.client.get(
            "/api/bookings/slots",
            params=params,
            headers=self._auth_headers(),
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    return data[0]["time"]
                return "09:00"
            self._expect(resp, (200,))
        return "09:00"

    def _ensure_booking(self):
        if self.booking_id:
            return
        if not self.business_id:
            self._create_business()
        payload = {
            "business_id": self.business_id,
            "service_name": self.service_name,
            "customer_name": "Locust User",
            "customer_email": self.user_email,
            "date": self.booking_date,
            "time_slot": self._get_slot(),
            "amount": 20.0,
        }
        with self.client.post(
            "/api/bookings",
            json=payload,
            headers=self._auth_headers(),
            catch_response=True,
        ) as resp:
            self._expect(resp, (200, 201))
            data = resp.json()
            self.booking_id = data.get("id")

    def _ensure_payment(self):
        if self.payment_id:
            return
        booking_id = self.booking_id or f"locust-{uuid.uuid4().hex[:8]}"
        payload = {
            "booking_id": booking_id,
            "amount": 20.0,
        }
        with self.client.post(
            "/api/payments",
            json=payload,
            headers=self._auth_headers(),
            catch_response=True,
        ) as resp:
            self._expect(resp, (201,))
            data = resp.json()
            self.payment_id = data.get("id")
            self.payment_booking_id = data.get("booking_id")

    @task(2)
    def list_businesses(self):
        with self.client.get(
            "/api/businesses", headers=self._auth_headers(), catch_response=True
        ) as resp:
            self._expect(resp, (200,))

    @task(1)
    def get_business_by_id(self):
        if not self.business_id:
            self._create_business()
        with self.client.get(
            f"/api/businesses/{self.business_id}",
            headers=self._auth_headers(),
            catch_response=True,
        ) as resp:
            self._expect(resp, (200,))

    @task(1)
    def get_business_by_slug(self):
        if not self.business_slug:
            self._create_business()
        with self.client.get(
            f"/api/businesses/slug/{self.business_slug}",
            headers=self._auth_headers(),
            catch_response=True,
        ) as resp:
            self._expect(resp, (200,))

    @task(1)
    def update_business(self):
        if not self.business_id:
            self._create_business()
        payload = self._business_payload(self.business_slug)
        payload["description"] = "Load test update"
        with self.client.put(
            f"/api/businesses/{self.business_id}",
            json=payload,
            headers=self._auth_headers(),
            catch_response=True,
        ) as resp:
            self._expect(resp, (200,))

    @task(1)
    def delete_and_recreate_business(self):
        if not self.business_id:
            return
        with self.client.delete(
            f"/api/businesses/{self.business_id}",
            headers=self._auth_headers(),
            catch_response=True,
        ) as resp:
            if resp.status_code == 204:
                self.business_id = None
                self.business_slug = None
                self._create_business()
                return
            self._expect(resp, (204,))

    @task(2)
    def list_bookings(self):
        with self.client.get(
            "/api/bookings",
            headers=self._auth_headers(),
            catch_response=True,
        ) as resp:
            self._expect(resp, (200,))

    @task(2)
    def get_available_slots(self):
        if not self.business_id:
            self._create_business()
        params = {
            "business_id": self.business_id,
            "service_name": self.service_name,
            "date": self.booking_date,
        }
        with self.client.get(
            "/api/bookings/slots",
            params=params,
            headers=self._auth_headers(),
            catch_response=True,
        ) as resp:
            self._expect(resp, (200, 404))

    @task(2)
    def create_booking(self):
        if not self.business_id:
            self._create_business()
        payload = {
            "business_id": self.business_id,
            "service_name": self.service_name,
            "customer_name": "Locust User",
            "customer_email": self.user_email,
            "date": self.booking_date,
            "time_slot": self._get_slot(),
            "amount": 20.0,
        }
        with self.client.post(
            "/api/bookings",
            json=payload,
            headers=self._auth_headers(),
            catch_response=True,
        ) as resp:
            self._expect(resp, (200, 201))
            data = resp.json()
            self.booking_id = data.get("id")

    @task(1)
    def get_booking(self):
        self._ensure_booking()
        with self.client.get(
            f"/api/bookings/{self.booking_id}",
            headers=self._auth_headers(),
            catch_response=True,
        ) as resp:
            self._expect(resp, (200,))

    @task(1)
    def cancel_booking(self):
        self._ensure_booking()
        with self.client.post(
            f"/api/bookings/{self.booking_id}/cancel",
            headers=self._auth_headers(),
            catch_response=True,
        ) as resp:
            self._expect(resp, (200, 400))
            if resp.status_code == 200:
                self.booking_id = None

    @task(1)
    def create_payment(self):
        booking_id = f"locust-{uuid.uuid4().hex[:8]}"
        payload = {"booking_id": booking_id, "amount": 20.0}
        with self.client.post(
            "/api/payments",
            json=payload,
            headers=self._auth_headers(),
            catch_response=True,
        ) as resp:
            self._expect(resp, (201,))

    @task(1)
    def get_payment(self):
        self._ensure_payment()
        with self.client.get(
            f"/api/payments/{self.payment_id}",
            headers=self._auth_headers(),
            catch_response=True,
        ) as resp:
            self._expect(resp, (200,))

    @task(1)
    def get_payment_by_booking(self):
        self._ensure_payment()
        with self.client.get(
            f"/api/payments/booking/{self.payment_booking_id}",
            headers=self._auth_headers(),
            catch_response=True,
        ) as resp:
            self._expect(resp, (200,))

    @task(1)
    def get_payment_circuit_status(self):
        with self.client.get(
            "/api/payments/circuit-breaker/status",
            headers=self._auth_headers(),
            catch_response=True,
        ) as resp:
            self._expect(resp, (200,))

    @task(1)
    def analytics_summary(self):
        if not self.business_id:
            self._create_business()
        with self.client.get(
            f"/api/analytics/summary/{self.business_id}",
            headers=self._auth_headers(),
            catch_response=True,
        ) as resp:
            self._expect(resp, (200, 404, 403))

    @task(1)
    def analytics_totals(self):
        if not self.business_id:
            self._create_business()
        with self.client.get(
            f"/api/analytics/totals/{self.business_id}",
            headers=self._auth_headers(),
            catch_response=True,
        ) as resp:
            self._expect(resp, (200, 404, 403))

    @task(1)
    def auth_login(self):
        with self.client.post(
            "/api/auth/login",
            json={
                "email": self.user_email,
                "password": self.user_password,
            },
            catch_response=True,
        ) as resp:
            self._expect(resp, (200,))
            data = resp.json()
            self.token = data.get("access_token")

    @task(1)
    def auth_validate(self):
        with self.client.post(
            "/api/auth/validate",
            headers=self._auth_headers(),
            catch_response=True,
        ) as resp:
            self._expect(resp, (200, 401))

    @task(1)
    def auth_me(self):
        with self.client.get(
            "/api/auth/me",
            headers=self._auth_headers(),
            catch_response=True,
        ) as resp:
            self._expect(resp, (200, 401))
