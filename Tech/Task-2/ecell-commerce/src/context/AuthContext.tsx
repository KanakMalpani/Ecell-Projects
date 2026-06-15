/**
 * AuthContext — global authentication state for the entire app.
 *
 * React Context lets any component read "who is logged in" without
 * passing props through every layer. Wrap the app in <AuthProvider>
 * (see Providers.tsx), then call useAuth() in any client component.
 *
 * On mount, it calls GET /api/auth/me to restore the session from the cookie.
 * login / register / logout talk to /api/auth and update local state.
 *
 * "use client" is required because this uses React hooks and fetch.
 */
"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";

export type User = {
  id: string;
  email: string;
  name: string;
  role: "USER" | "ADMIN";
};

type AuthContextType = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Re-fetch the current user from the server (reads the httpOnly cookie)
  const refresh = async () => {
    try {
      const res = await fetch("/api/auth/me");
      const data = await res.json();
      setUser(data.user);
    } catch {
      setUser(null);
    }
  };

  // Check session once when the app first loads
  useEffect(() => {
    refresh().finally(() => setLoading(false));
  }, []);

  // PUT /api/auth — email + password login
  const login = async (email: string, password: string) => {
    const res = await fetch("/api/auth", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Login failed");
    setUser(data.user);
  };

  // POST /api/auth — create a new account
  const register = async (name: string, email: string, password: string) => {
    const res = await fetch("/api/auth", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Registration failed");
    setUser(data.user);
  };

  // DELETE /api/auth — clear the auth cookie
  const logout = async () => {
    await fetch("/api/auth", { method: "DELETE" });
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

/** Hook to access auth state — must be used inside <AuthProvider>. */
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
