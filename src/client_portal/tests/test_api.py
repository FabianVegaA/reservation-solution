import pytest

from client_portal.security import ClientTokenService
from reservations.constants import (
    RESERVATION_STATUS_CANCELLED,
    RESERVATION_STATUS_REQUESTED,
)
from reservations.tests.factories import (
    CustomerFactory,
    ReservationFactory,
    UserFactory,
)


@pytest.mark.django_db
def test_login_returns_access_token(client):
    user = UserFactory(email="alice@example.com", username="alice", password="demo1234")
    customer = CustomerFactory(user=user)

    response = client.post(
        "/api/v1/auth/login",
        data={"email": customer.user.email, "password": "demo1234"},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.django_db
def test_me_returns_customer_profile(client):
    customer = CustomerFactory()
    token = ClientTokenService.issue_access_token(customer=customer)

    response = client.get(
        "/api/v1/auth/me",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(customer.id)


@pytest.mark.django_db
def test_reservation_list_is_scoped_to_customer(client):
    customer = CustomerFactory()
    other_customer = CustomerFactory()
    own_reservation = ReservationFactory(customer=customer)
    ReservationFactory(customer=other_customer)
    token = ClientTokenService.issue_access_token(customer=customer)

    response = client.get(
        "/api/v1/reservations/",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == str(own_reservation.id)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("owner", "status", "reason", "expected_status"),
    [
        (True, RESERVATION_STATUS_REQUESTED, "Cambio de planes", 200),
        (False, RESERVATION_STATUS_REQUESTED, "Cambio de planes", 400),
        (True, RESERVATION_STATUS_CANCELLED, "Cambio de planes", 400),
        (True, RESERVATION_STATUS_REQUESTED, "   ", 422),
    ],
)
def test_cancel_reservation(client, owner, status, reason, expected_status):
    customer = CustomerFactory()
    reservation_customer = customer if owner else CustomerFactory()
    reservation = ReservationFactory(
        customer=reservation_customer,
        status=status,
    )
    token = ClientTokenService.issue_access_token(customer=customer)

    response = client.post(
        f"/api/v1/reservations/{reservation.id}/cancel",
        data={"reason": reason},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == expected_status
    reservation.refresh_from_db()

    if expected_status == 200:
        assert reservation.status == RESERVATION_STATUS_CANCELLED
        assert reservation.cancel_reason == reason
    else:
        assert reservation.status == status
