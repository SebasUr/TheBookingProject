import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  getAnalyticsTotals,
  getAnalyticsSummary,
  getBookings,
  cancelBooking,
  getBusiness,
} from "../api";
import { useAuth } from "../contexts/AuthContext";

export default function Analytics() {
  const { id } = useParams();
  const { user } = useAuth();
  const [totals, setTotals] = useState(null);
  const [summary, setSummary] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [accessDenied, setAccessDenied] = useState(false);
  const [loading, setLoading] = useState(true);

  function loadData() {
    getAnalyticsTotals(id).then(setTotals);
    getAnalyticsSummary(id).then(setSummary);
    getBookings(id).then(setBookings);
  }

  useEffect(() => {
    // Verify ownership before loading analytics
    getBusiness(id).then((business) => {
      if (!business || business.owner_id !== user?.id) {
        setAccessDenied(true);
      } else {
        loadData();
      }
      setLoading(false);
    });
  }, [id]);

  async function handleCancel(bookingId) {
    await cancelBooking(bookingId);
    loadData();
  }

  if (loading) return <p className="empty">Loading...</p>;

  if (accessDenied) {
    return (
      <div>
        <Link to="/" className="back-link">Back</Link>
        <p className="empty">You don&apos;t have permission to view this page.</p>
      </div>
    );
  }

  return (
    <div>
      <Link to="/" className="back-link">
        Back
      </Link>
      <h1>Analytics</h1>
      <p className="subtitle">Business performance overview</p>

      {totals && (
        <div className="stats">
          <div className="stat">
            <span className="stat-value">
              {totals.total_bookings || 0}
            </span>
            <span className="stat-label">Total Bookings</span>
          </div>
          <div className="stat">
            <span className="stat-value">
              {totals.confirmed_bookings || 0}
            </span>
            <span className="stat-label">Confirmed</span>
          </div>
          <div className="stat">
            <span className="stat-value">
              {totals.cancelled_bookings || 0}
            </span>
            <span className="stat-label">Cancelled</span>
          </div>
          <div className="stat">
            <span className="stat-value">
              ${(totals.total_revenue || 0).toFixed(2)}
            </span>
            <span className="stat-label">Revenue</span>
          </div>
        </div>
      )}

      <section>
        <h2>Daily Breakdown</h2>
        {summary.length === 0 ? (
          <p className="empty">No data yet</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Bookings</th>
                <th>Confirmed</th>
                <th>Cancelled</th>
                <th>Revenue</th>
              </tr>
            </thead>
            <tbody>
              {summary.map((s) => (
                <tr key={s.id}>
                  <td>{s.date}</td>
                  <td>{s.total_bookings || 0}</td>
                  <td>{s.confirmed_bookings || 0}</td>
                  <td>{s.cancelled_bookings || 0}</td>
                  <td>${(s.total_revenue || 0).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section>
        <h2>Recent Bookings</h2>
        {bookings.length === 0 ? (
          <p className="empty">No bookings yet</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Customer</th>
                <th>Service</th>
                <th>Date</th>
                <th>Time</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {bookings.map((b) => (
                <tr key={b.id}>
                  <td>{b.customer_name}</td>
                  <td>{b.service_name}</td>
                  <td>{b.date}</td>
                  <td>{b.time_slot}</td>
                  <td className={`status-${b.status}`}>{b.status}</td>
                  <td>
                    {b.status === "confirmed" && (
                      <button
                        className="secondary"
                        style={{
                          margin: 0,
                          padding: "0.2rem 0.5rem",
                          fontSize: "0.72rem",
                        }}
                        onClick={() => handleCancel(b.id)}
                      >
                        Cancel
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
