from shared.errors import DomainError


class ReservationError(DomainError):
    code = "reservation_error"
    detail = "Reservation error."


class ReservationNotFoundError(ReservationError):
    code = "reservation_not_found"
    detail = "Reservation not found."


class ReservationStatusTransitionError(ReservationError):
    code = "reservation_invalid_transition"
    detail = "Reservation cannot transition from its current status."

    def __init__(
        self, *, current_status: str | None = None, target_status: str | None = None
    ) -> None:
        self.current_status = current_status
        self.target_status = target_status

        if current_status is None or target_status is None:
            super().__init__()
        else:
            super().__init__(
                detail=f"Reservation cannot transition from {current_status} to {target_status}."
            )
