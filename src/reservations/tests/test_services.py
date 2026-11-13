import pytest

from reservations.constants import (
    RESERVATION_STATUS_CANCELLED,
    RESERVATION_STATUS_CONFIRMED,
    RESERVATION_STATUS_ON_HOLD,
    RESERVATION_STATUS_REQUESTED,
)
from reservations.exceptions import ReservationStatusTransitionError
from reservations.services import ReservationLifecycleService
from reservations.tests.factories import ReservationFactory


@pytest.mark.django_db
def test_confirm_reservation_moves_requested_to_confirmed():
    reservation = ReservationFactory(status="requested")

    ReservationLifecycleService().confirm_reservation(reservation_id=reservation.id)

    reservation.refresh_from_db()
    assert reservation.status == RESERVATION_STATUS_CONFIRMED


@pytest.mark.django_db
def test_confirm_reservation_rejects_invalid_transition():
    reservation = ReservationFactory(status=RESERVATION_STATUS_CANCELLED)

    with pytest.raises(ReservationStatusTransitionError):
        ReservationLifecycleService().confirm_reservation(reservation_id=reservation.id)


@pytest.fixture
def lifecycle_service():
    return ReservationLifecycleService()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("initial_status", "reason", "expected_status", "expected_reason", "error"),
    [
        (
            RESERVATION_STATUS_REQUESTED,
            "  Pago pendiente  ",
            RESERVATION_STATUS_ON_HOLD,
            "Pago pendiente",
            None,
        ),
        (
            RESERVATION_STATUS_REQUESTED,
            "",
            RESERVATION_STATUS_REQUESTED,
            "",
            ReservationLifecycleService.HoldReasonRequiredError,
        ),
        (
            RESERVATION_STATUS_REQUESTED,
            " \n\t ",
            RESERVATION_STATUS_REQUESTED,
            "",
            ReservationLifecycleService.HoldReasonRequiredError,
        ),
        (
            RESERVATION_STATUS_CONFIRMED,
            "Pendiente",
            RESERVATION_STATUS_CONFIRMED,
            "",
            ReservationStatusTransitionError,
        ),
        (
            RESERVATION_STATUS_CANCELLED,
            "Pendiente",
            RESERVATION_STATUS_CANCELLED,
            "",
            ReservationStatusTransitionError,
        ),
        (
            RESERVATION_STATUS_ON_HOLD,
            "Pendiente",
            RESERVATION_STATUS_ON_HOLD,
            "Motivo anterior",
            ReservationStatusTransitionError,
        ),
    ],
)
def test_place_reservation_on_hold(
    lifecycle_service,
    initial_status,
    reason,
    expected_status,
    expected_reason,
    error,
):
    initial_reason = (
        "Motivo anterior" if initial_status == RESERVATION_STATUS_ON_HOLD else ""
    )
    reservation = ReservationFactory(
        status=initial_status,
        hold_reason=initial_reason,
    )

    if error:
        with pytest.raises(error):
            lifecycle_service.place_reservation_on_hold(
                reservation_id=reservation.id,
                reason=reason,
            )
    else:
        lifecycle_service.place_reservation_on_hold(
            reservation_id=reservation.id,
            reason=reason,
        )

    reservation.refresh_from_db()
    assert reservation.status == expected_status
    assert reservation.hold_reason == expected_reason


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("initial_status", "expected_status", "expected_reason", "error"),
    [
        (RESERVATION_STATUS_ON_HOLD, RESERVATION_STATUS_REQUESTED, "", None),
        (
            RESERVATION_STATUS_REQUESTED,
            RESERVATION_STATUS_REQUESTED,
            "",
            ReservationStatusTransitionError,
        ),
        (
            RESERVATION_STATUS_CONFIRMED,
            RESERVATION_STATUS_CONFIRMED,
            "",
            ReservationStatusTransitionError,
        ),
        (
            RESERVATION_STATUS_CANCELLED,
            RESERVATION_STATUS_CANCELLED,
            "",
            ReservationStatusTransitionError,
        ),
    ],
)
def test_release_reservation_from_hold(
    lifecycle_service,
    initial_status,
    expected_status,
    expected_reason,
    error,
):
    initial_reason = (
        "Pago pendiente" if initial_status == RESERVATION_STATUS_ON_HOLD else ""
    )
    reservation = ReservationFactory(
        status=initial_status,
        hold_reason=initial_reason,
    )

    if error:
        with pytest.raises(error):
            lifecycle_service.release_reservation_from_hold(
                reservation_id=reservation.id
            )
    else:
        lifecycle_service.release_reservation_from_hold(reservation_id=reservation.id)

    reservation.refresh_from_db()
    assert reservation.status == expected_status
    assert reservation.hold_reason == expected_reason
