import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { fetchBusinesses, createBusiness } from "../api";

const DEFAULT_SCHEDULE = {
  monday: { start: "09:00", end: "17:00" },
  tuesday: { start: "09:00", end: "17:00" },
  wednesday: { start: "09:00", end: "17:00" },
  thursday: { start: "09:00", end: "17:00" },
  friday: { start: "09:00", end: "17:00" },
};

const EMPTY_SERVICE = { name: "", duration_minutes: 30, price: 0, capacity: 1 };

export default function Admin() {
  const [businesses, setBusinesses] = useState([]);
  const [form, setForm] = useState({
    name: "",
    slug: "",
    description: "",
    services: [{ ...EMPTY_SERVICE }],
    schedule: { ...DEFAULT_SCHEDULE },
  });
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetchBusinesses().then(setBusinesses);
  }, []);

  function addService() {
    setForm({
      ...form,
      services: [...form.services, { ...EMPTY_SERVICE }],
    });
  }

  function removeService(index) {
    const services = form.services.filter((_, i) => i !== index);
    setForm({ ...form, services });
  }

  function updateService(index, field, value) {
    const services = [...form.services];
    services[index] = { ...services[index], [field]: value };
    setForm({ ...form, services });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setMessage("");
    const data = {
      ...form,
      services: form.services.filter((s) => s.name.trim()),
    };
    const result = await createBusiness(data);
    if (result.id) {
      setBusinesses([...businesses, result]);
      setForm({
        name: "",
        slug: "",
        description: "",
        services: [{ ...EMPTY_SERVICE }],
        schedule: { ...DEFAULT_SCHEDULE },
      });
      setMessage("Business created");
    } else {
      setMessage(result.detail || "Error creating business");
    }
  }

  return (
    <div>
      <h1>Admin Panel</h1>
      <p className="subtitle">Manage your businesses</p>

      <section>
        <h2>Create Business</h2>
        <form onSubmit={handleSubmit}>
          <label>Name</label>
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
            placeholder="My Business"
          />

          <label>Slug</label>
          <input
            value={form.slug}
            onChange={(e) => setForm({ ...form, slug: e.target.value })}
            required
            placeholder="my-business"
          />

          <label>Description</label>
          <textarea
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="What does your business do?"
          />

          <h2>Services</h2>
          {form.services.map((s, i) => (
            <div key={i} className="service-row">
              <input
                placeholder="Service name"
                value={s.name}
                onChange={(e) => updateService(i, "name", e.target.value)}
              />
              <input
                type="number"
                placeholder="Min"
                value={s.duration_minutes}
                onChange={(e) =>
                  updateService(
                    i,
                    "duration_minutes",
                    parseInt(e.target.value) || 30
                  )
                }
              />
              <input
                type="number"
                placeholder="Price"
                value={s.price}
                onChange={(e) =>
                  updateService(i, "price", parseFloat(e.target.value) || 0)
                }
              />
              <input
                type="number"
                placeholder="Cap"
                value={s.capacity}
                onChange={(e) =>
                  updateService(
                    i,
                    "capacity",
                    parseInt(e.target.value) || 1
                  )
                }
              />
            </div>
          ))}
          <button type="button" className="secondary" onClick={addService}>
            + Add Service
          </button>

          <br />
          <button type="submit">Create Business</button>

          {message && (
            <p
              style={{
                marginTop: "0.75rem",
                fontSize: "0.85rem",
                color: message.includes("Error") ? "#991b1b" : "#166534",
              }}
            >
              {message}
            </p>
          )}
        </form>
      </section>

      <section>
        <h2>Existing Businesses</h2>
        {businesses.length === 0 ? (
          <p className="empty">No businesses created yet</p>
        ) : (
          <div className="grid">
            {businesses.map((b) => (
              <div key={b.id} className="card">
                <h3>{b.name}</h3>
                <p>/{b.slug}</p>
                <p>{b.services?.length || 0} services</p>
                <div className="card-actions">
                  <Link to={`/book/${b.id}`}>View</Link>
                  <Link to={`/analytics/${b.id}`}>Analytics</Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
