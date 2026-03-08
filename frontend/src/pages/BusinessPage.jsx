import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getBusiness, getSlots, createBooking } from "../api";

export default function BusinessPage() {
  const { id } = useParams();
  const [business, setBusiness] = useState(null);
  const [selectedService, setSelectedService] = useState("");
  const [date, setDate] = useState("");
  const [slots, setSlots] = useState([]);
  const [selectedSlot, setSelectedSlot] = useState("");
  const [form, setForm] = useState({ name: "", email: "" });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getBusiness(id).then(setBusiness);
  }, [id]);

  useEffect(() => {
    if (selectedService && date) {
      setSelectedSlot("");
      setResult(null);
      getSlots(id, selectedService, date).then(setSlots);
    }
  }, [id, selectedService, date]);

  async function handleBook() {
    if (!selectedSlot || !form.name || !form.email) return;
    setLoading(true);
    const service = business.services.find((s) => s.name === selectedService);
    const res = await createBooking({
      business_id: id,
      service_name: selectedService,
      customer_name: form.name,
      customer_email: form.email,
      date,
      time_slot: selectedSlot,
      amount: service?.price || 0,
    });
    setResult(res);
    setLoading(false);
    getSlots(id, selectedService, date).then(setSlots);
  }

  if (!business) return <p className="empty">Loading...</p>;

  return (
    <div>
      <Link to="/" className="back-link">
        Back
      </Link>
      <h1>{business.name}</h1>
      <p className="subtitle">{business.description}</p>

      <section>
        <h2>Book an Appointment</h2>

        <label>Service</label>
        <select
          value={selectedService}
          onChange={(e) => setSelectedService(e.target.value)}
        >
          <option value="">Select a service</option>
          {business.services?.map((s) => (
            <option key={s.name} value={s.name}>
              {s.name} -- {s.duration_minutes}min -- ${s.price}
            </option>
          ))}
        </select>

        <label>Date</label>
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />

        {selectedService && date && (
          <>
            <label>Available Slots</label>
            {slots.length === 0 ? (
              <p className="empty">No slots available for this date</p>
            ) : (
              <div className="slots">
                {slots.map((s) => (
                  <button
                    key={s.time}
                    className={`slot ${selectedSlot === s.time ? "selected" : ""}`}
                    onClick={() => setSelectedSlot(s.time)}
                  >
                    {s.time} ({s.remaining} left)
                  </button>
                ))}
              </div>
            )}
          </>
        )}

        {selectedSlot && (
          <div className="booking-form">
            <label>Name</label>
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Your name"
            />
            <label>Email</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              placeholder="your@email.com"
            />
            <button onClick={handleBook} disabled={loading}>
              {loading ? "Processing..." : "Book Now"}
            </button>
          </div>
        )}

        {result && (
          <div className={`result ${result.status}`}>
            Booking {result.status}
            {result.id && <span> (ID: {result.id})</span>}
          </div>
        )}
      </section>
    </div>
  );
}
