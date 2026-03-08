const API = "/api";

function getToken() {
  return localStorage.getItem("auth_token");
}

function authHeaders(extra = {}) {
  const headers = { "Content-Type": "application/json", ...extra };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

// ── Auth ──────────────────────────────────────────────────────────────

export async function login(email, password) {
  const res = await fetch(`${API}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return res.json();
}

export async function register(email, password) {
  const res = await fetch(`${API}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return res.json();
}

// ── Businesses ────────────────────────────────────────────────────────

export async function fetchBusinesses() {
  const res = await fetch(`${API}/businesses`);
  return res.json();
}

export async function createBusiness(data) {
  const res = await fetch(`${API}/businesses`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function getBusiness(id) {
  const res = await fetch(`${API}/businesses/${id}`);
  return res.json();
}

// ── Bookings ──────────────────────────────────────────────────────────

export async function getSlots(businessId, serviceName, date) {
  const params = new URLSearchParams({
    business_id: businessId,
    service_name: serviceName,
    date,
  });
  const res = await fetch(`${API}/bookings/slots?${params}`);
  return res.json();
}

export async function createBooking(data) {
  const res = await fetch(`${API}/bookings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function getBookings(businessId) {
  const params = businessId ? `?business_id=${businessId}` : "";
  const res = await fetch(`${API}/bookings${params}`, {
    headers: authHeaders(),
  });
  return res.json();
}

export async function cancelBooking(id) {
  const res = await fetch(`${API}/bookings/${id}/cancel`, {
    method: "POST",
    headers: authHeaders(),
  });
  return res.json();
}

// ── Analytics ─────────────────────────────────────────────────────────

export async function getAnalyticsTotals(businessId) {
  const res = await fetch(`${API}/analytics/totals/${businessId}`, {
    headers: authHeaders(),
  });
  return res.json();
}

export async function getAnalyticsSummary(businessId) {
  const res = await fetch(`${API}/analytics/summary/${businessId}`, {
    headers: authHeaders(),
  });
  return res.json();
}

