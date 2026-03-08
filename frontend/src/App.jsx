import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import Home from "./pages/Home";
import BusinessPage from "./pages/BusinessPage";
import Admin from "./pages/Admin";
import Analytics from "./pages/Analytics";
import "./App.css";

export default function App() {
  return (
    <BrowserRouter>
      <nav>
        <Link to="/" className="nav-brand">
          Booking
        </Link>
        <div className="nav-links">
          <Link to="/">Explore</Link>
          <Link to="/admin">Admin</Link>
        </div>
      </nav>
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/book/:id" element={<BusinessPage />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/analytics/:id" element={<Analytics />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
