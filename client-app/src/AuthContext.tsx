import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from "react";

type AuthContextValue = {
  token: string | null;
  login: (token: string) => void;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(
    () => sessionStorage.getItem("access_token"),
  );

  function login(accessToken: string) {
    sessionStorage.setItem("access_token", accessToken);
    setToken(accessToken);
  }

  function logout() {
    sessionStorage.removeItem("access_token");
    setToken(null);
  }

  return (
    <AuthContext.Provider value={{ token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth requires an AuthProvider");
  }

  return context;
}
