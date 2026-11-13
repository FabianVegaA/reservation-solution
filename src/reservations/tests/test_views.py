import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from reservations.constants import (
    RESERVATION_STATUS_ON_HOLD,
    RESERVATION_STATUS_REQUESTED,
)
from reservations.tests.factories import (
    ReservationFactory,
    UserFactory,
    grant_permission,
)


@pytest.mark.django_db
def test_reservation_list_requires_login(client):
    response = client.get(reverse("reservation_list"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_reservation_list_renders_for_user_with_permission(client):
    reservation = ReservationFactory()
    user = UserFactory()
    grant_permission(user=user, codename="view_reservation")
    client.force_login(user)

    response = client.get(reverse("reservation_list"))

    assert response.status_code == 200
    assert reservation.customer.display_name in response.content.decode()


@pytest.mark.django_db
def test_reservation_confirm_requires_permission(client):
    reservation = ReservationFactory()
    user = UserFactory()
    client.force_login(user)

    response = client.post(reverse("reservation_confirm", args=[reservation.id]))

    assert response.status_code == 403


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("route", "initial_status", "data", "access", "expected_code", "expected_message"),
    [
        (
            "reservation_hold",
            RESERVATION_STATUS_REQUESTED,
            {"hold_reason": "Pago pendiente"},
            "allowed",
            302,
            "Reserva puesta en espera.",
        ),
        (
            "reservation_hold",
            RESERVATION_STATUS_REQUESTED,
            {"hold_reason": " \n\t "},
            "allowed",
            302,
            "Se requiere una razón para ponerla en espera.",
        ),
        (
            "reservation_release",
            RESERVATION_STATUS_ON_HOLD,
            {},
            "allowed",
            302,
            "Reserva liberada.",
        ),
        (
            "reservation_hold",
            RESERVATION_STATUS_REQUESTED,
            {"hold_reason": "Pago pendiente"},
            "denied",
            403,
            None,
        ),
        ("reservation_release", RESERVATION_STATUS_ON_HOLD, {}, "denied", 403, None),
        (
            "reservation_hold",
            RESERVATION_STATUS_REQUESTED,
            {"hold_reason": "Pago pendiente"},
            "anonymous",
            302,
            None,
        ),
        ("reservation_release", RESERVATION_STATUS_ON_HOLD, {}, "anonymous", 302, None),
    ],
)
def test_hold_and_release_views(
    client,
    route,
    initial_status,
    data,
    access,
    expected_code,
    expected_message,
):
    reservation = ReservationFactory(
        status=initial_status,
        hold_reason="Pago pendiente"
        if initial_status == RESERVATION_STATUS_ON_HOLD
        else "",
    )

    if access != "anonymous":
        user = UserFactory()
        if access == "allowed":
            grant_permission(user=user, codename="hold_reservation")
        client.force_login(user)

    response = client.post(reverse(route, args=[reservation.id]), data)

    assert response.status_code == expected_code

    if access == "allowed":
        assert response.url == reverse("reservation_detail", args=[reservation.id])
        assert [str(message) for message in get_messages(response.wsgi_request)] == [
            expected_message
        ]
    elif access == "anonymous":
        assert response.url.startswith("/accounts/login/")

    if access != "allowed":
        reservation.refresh_from_db()
        assert reservation.status == initial_status
