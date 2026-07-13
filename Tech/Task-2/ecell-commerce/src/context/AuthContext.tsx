/**
 * AuthContext — global authentication state (React Context).
 *
 * ROLE IN THE APP:
 *   Client-side session mirror. On mount, calls GET /api/auth/me to restore
 *   the user from the httpOnly JWT cookie. Exposes login/register/logout
 *   methods that hit /api/auth and update local React state.
 *
 * KEY PATTERN:
 *   "use client" required — uses hooks (useState, useEffect) and fetch.
 *   Wrapped by Providers.tsx at the root layout level.
 *
 * PI INTERVIEW TALKING POINTS:
 *   - Why Context over Redux? Simple global state; no boilerplate for 1 user object
 *   - Cookie is httpOnly → client can't read JWT; must ask server via /api/auth/me
 *   - loading flag prevents flash of login UI before session check completes
 *   - PUT for login (non-standard) chosen to separate from POST register on same route
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

/** AuthProvider — wraps children with auth state and action methods. */
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
