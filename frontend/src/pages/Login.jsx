import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function Login() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    const fn = mode === "login" ? login : register;
    const result = await fn(email, password);
    setLoading(false);
    if (result.ok) {
      navigate("/admin");
    } else {
      setError(result.error);
    }
  }

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <h1>{mode === "login" ? "Sign In" : "Create Account"}</h1>
        <p className="subtitle">
          {mode === "login"
            ? "Access your business dashboard"
            : "Register to manage your business"}
        </p>

        <div className="auth-tabs">
          <button
            className={mode === "login" ? "active" : ""}
            onClick={() => { setMode("login"); setError(""); }}
          >
            Sign In
          </button>
          <button
            className={mode === "register" ? "active" : ""}
            onClick={() => { setMode("register"); setError(""); }}
          >
            Register
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <label>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
            autoFocus
          />
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
            minLength={6}
          />
          <button type="submit" disabled={loading}>
            {loading ? "Please wait..." : mode === "login" ? "Sign In" : "Create Account"}
          </button>
          {error && (
            <p style={{ marginTop: "0.75rem", fontSize: "0.85rem", color: "#991b1b" }}>
              {error}
            </p>
          )}
        </form>
      </div>
    </div>
  );
}
