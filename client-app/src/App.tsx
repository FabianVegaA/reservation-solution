import { Navigate, Route, Routes } from "react-router";
import { LoginPage } from "./LoginPage";
import { ReservationsPage } from "./ReservationsPage";
import { useAuth } from "./AuthContext";



export default function App() {
  const { token } = useAuth();

  return (
    <Routes>
      <Route
        path="/login"
        element={token ? <Navigate to="/reservations" replace /> : <LoginPage />}
      />
      <Route
        path="/reservations"
        element={token ? <ReservationsPage /> : <Navigate to="/login" replace />}
      />
      <Route path="*" element={token ? <> </> : <Navigate to="/login" replace />} />
    </Routes>
  );
}
