const API = "/api";

export async function fetchBusinesses() {
  const res = await fetch(`${API}/businesses`);
  return res.json();
}

export async function createBusiness(data) {
  const res = await fetch(`${API}/businesses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function getBusiness(id) {
  const res = await fetch(`${API}/businesses/${id}`);
  return res.json();
}

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
  const res = await fetch(`${API}/bookings${params}`);
  return res.json();
}

export async function cancelBooking(id) {
  const res = await fetch(`${API}/bookings/${id}/cancel`, { method: "POST" });
  return res.json();
}

export async function getAnalyticsTotals(businessId) {
  const res = await fetch(`${API}/analytics/totals/${businessId}`);
  return res.json();
}

export async function getAnalyticsSummary(businessId) {
  const res = await fetch(`${API}/analytics/summary/${businessId}`);
  return res.json();
}
