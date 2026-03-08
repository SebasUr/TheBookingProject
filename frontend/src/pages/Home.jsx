import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchBusinesses } from "../api";
import { useAuth } from "../contexts/AuthContext";

export default function Home() {
  const { user } = useAuth();
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
          <Link to="/login" style={{ color: "#1a1a1a" }}>
            Register your business
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
                {user && user.id === b.owner_id && (
                  <Link to={`/analytics/${b.id}`}>Analytics</Link>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
