import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchBusinesses } from "../api";

export default function Home() {
  const [businesses, setBusinesses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBusinesses()
      .then(setBusinesses)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="empty">Loading...</p>;

  return (
    <div>
      <h1>Booking Platform</h1>
      <p className="subtitle">Select a business to book an appointment</p>

      {businesses.length === 0 ? (
        <div className="empty">
          No businesses yet.{" "}
          <Link to="/admin" style={{ color: "#1a1a1a" }}>
            Create one
          </Link>
        </div>
      ) : (
        <div className="grid">
          {businesses.map((b) => (
            <div key={b.id} className="card">
              <h3>{b.name}</h3>
              <p>{b.description}</p>
              <p>{b.services?.length || 0} services</p>
              <div className="card-actions">
                <Link to={`/book/${b.id}`}>Book</Link>
                <Link to={`/analytics/${b.id}`}>Analytics</Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
