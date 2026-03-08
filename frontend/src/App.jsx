import { BrowserRouter, Routes, Route, Link, Navigate } from "react-router-dom";
import Home from "./pages/Home";
import BusinessPage from "./pages/BusinessPage";
import Admin from "./pages/Admin";
import Analytics from "./pages/Analytics";
import Login from "./pages/Login";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import "./App.css";

function ProtectedRoute({ children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function Nav() {
  const { user, logout } = useAuth();
  return (
    <nav>
      <Link to="/" className="nav-brand">
        Booking
      </Link>
      <div className="nav-links">
        <Link to="/">Explore</Link>
        {user ? (
          <>
            <Link to="/admin">My Businesses</Link>
            <button className="nav-logout" onClick={logout}>
              Sign Out
            </button>
          </>
        ) : (
          <Link to="/login">Business Login</Link>
        )}
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Nav />
        <main>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/book/:id" element={<BusinessPage />} />
            <Route path="/login" element={<Login />} />
            <Route
              path="/admin"
              element={
                <ProtectedRoute>
                  <Admin />
                </ProtectedRoute>
              }
            />
            <Route
              path="/analytics/:id"
              element={
                <ProtectedRoute>
                  <Analytics />
                </ProtectedRoute>
              }
            />
          </Routes>
        </main>
      </BrowserRouter>
    </AuthProvider>
  );
}

