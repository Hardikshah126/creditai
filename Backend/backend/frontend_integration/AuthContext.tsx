/**
 * AuthContext — drop in src/context/AuthContext.tsx
 *
 * Wraps the app so any component can read the current user
 * and call login / logout / signup.
 */
import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { api, saveSession, clearSession, getSessionUser, getToken, TokenResponse } from "@/lib/api";

interface SessionUser {
  id: string;
  name: string;
  role: string;
}

interface AuthContextType {
  user: SessionUser | null;
  isLoading: boolean;
  signup: (body: {
    name: string;
    phone: string;
    country: string;
    password: string;
    email?: string;
    role?: string;
  }) => Promise<void>;
  login: (phone: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore session from localStorage on mount
  useEffect(() => {
    const stored = getSessionUser();
    if (stored && getToken()) {
      setUser(stored);
    }
    setIsLoading(false);
  }, []);

  const handleToken = (token: TokenResponse) => {
    saveSession(token);
    setUser({ id: token.user_id, name: token.name, role: token.role });
  };

  const signup = async (body: Parameters<typeof api.auth.signup>[0]) => {
    const token = await api.auth.signup(body);
    handleToken(token);
  };

  const login = async (phone: string, password: string) => {
    const token = await api.auth.login(phone, password);
    handleToken(token);
  };

  const logout = () => {
    clearSession();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, signup, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
