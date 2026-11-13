import { useEffect, useState, type SubmitEvent } from "react";
import { useAuth } from "./AuthContext";

type Reservation = {
  id: string;
  room_name: string;
  starts_at: string;
  ends_at: string;
  status: "requested" | "confirmed" | "cancelled";
};

function ReservationItem({
  reservation,
  onCancel,
}: {
  reservation: Reservation;
  onCancel: () => void;
}) {
  const [cancelling, setCancelling] = useState(false);
  const { token } = useAuth();
  const [reason, setReason] = useState("");

  async function handleCancel(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      const response = await fetch(
        `/api/v1/reservations/${reservation.id}/cancel`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ reason }),
        },
      );
      if (!response.ok) {
        const problem = await response.json().catch(() => null);
        alert(
          typeof problem?.detail === "string"
            ? problem.detail
            : "No se pudo cancelar la reserva.",
        );
        return;
      }

      onCancel();
    } catch {
      alert("No se pudo conectar con el servidor.");
    } finally {
      setCancelling(false);
      setReason("");
    }
  }

  return (
    <tr>
      <td>{reservation.room_name}</td>
      <td>
        {new Date(reservation.starts_at).toLocaleString("es-CL", {
          dateStyle: "short",
          timeStyle: "short",
        })}
      </td>
      <td>
        <span className={`status-badge status-${reservation.status}`}>
          {reservation.status}
        </span>
      </td>
      <td>
        {reservation.status === "requested" &&
          (cancelling ? (
            <form onSubmit={handleCancel}>
              <label htmlFor={`reason-${reservation.id}`}>Motivo</label>
              <input
                id={`reason-${reservation.id}`}
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                required
              />
              <button type="submit">Confirmar cancelación</button>
              <button type="button" onClick={() => setCancelling(false)}>
                Volver
              </button>
            </form>
          ) : (
            <button type="button" onClick={() => setCancelling(true)}>
              Cancelar
            </button>
          ))}
      </td>
    </tr>
  );
}

export function ReservationsPage() {
  const { token, logout } = useAuth();
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [displayName, setDisplayName] = useState("");

  useEffect(() => {
    async function loadProfile() {
      try {
        const response = await fetch("/api/v1/auth/me", {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (response.status === 401) {
          logout();
          return;
        }

        if (!response.ok) {
          throw new Error("No se pudo cargar el perfil");
        }

        const profile: { display_name: string } = await response.json();
        setDisplayName(profile.display_name);
      } catch {
        setError("No se pudo cargar tu perfil.");
      }
    }

    void loadProfile();
  }, [token]);

  async function fetchReservations() {
    setError("");
    setLoading(true);

    try {
      const response = await fetch("/api/v1/reservations/", {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const problem = await response.json().catch(() => null);
        setError(
          typeof problem?.detail === "string"
            ? problem.detail
            : "No se pudo obtener las reservas.",
        );
        return;
      }

      const data = (await response.json()) as Reservation[];
      setReservations(data);
    } catch {
      setError("No se pudo conectar con el servidor.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void fetchReservations();
  }, [token]);

  return (
    <main>
      <div className="welcome-header">
        {displayName && <p>Hola, {displayName}</p>}
        <button type="button" onClick={logout}>
          Cerrar sesión
        </button>
      </div>

      <h1>Mis reservas</h1>

      {loading && <p>Cargando...</p>}

      {error && <p role="alert">{error}</p>}

      <div className="table-container">
        <table className="reservations-table">
          <thead>
            <tr>
              <th scope="col">Sala</th>
              <th scope="col">Inicio</th>
              <th scope="col">Estado</th>
              <th scope="col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {reservations.map((reservation) => (
              <ReservationItem
                key={reservation.id}
                reservation={reservation}
                onCancel={() => {
                  setReservations((previous) =>
                    previous.map((item) =>
                      item.id === reservation.id
                        ? { ...item, status: "cancelled" }
                        : item,
                    ),
                  );
                }}
              />
            ))}
          </tbody>
        </table>
      </div>
    </main>
  );
}
