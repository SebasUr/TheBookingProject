import { createContext, useContext, useState, useCallback } from "react";
import { login as apiLogin, register as apiRegister } from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem("auth_user");
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const login = useCallback(async (email, password) => {
    const data = await apiLogin(email, password);
    if (data.access_token) {
      localStorage.setItem("auth_token", data.access_token);
      const u = { id: data.user_id, email: data.email };
      localStorage.setItem("auth_user", JSON.stringify(u));
      setUser(u);
      return { ok: true };
    }
    return { ok: false, error: data.detail || "Login failed" };
  }, []);

  const register = useCallback(async (email, password) => {
    const data = await apiRegister(email, password);
    if (data.access_token) {
      localStorage.setItem("auth_token", data.access_token);
      const u = { id: data.user_id, email: data.email };
      localStorage.setItem("auth_user", JSON.stringify(u));
      setUser(u);
      return { ok: true };
    }
    return { ok: false, error: data.detail || "Registration failed" };
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user");
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
