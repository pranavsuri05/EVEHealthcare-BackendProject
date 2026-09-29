import pytest
from datetime import datetime, timedelta, timezone


def create_centre_test(test_client):
    """Helper to create a centre_test"""
    centre_response = test_client.post(
        "/centres", json={"name": "Lab 1", "location": "Loc 1"}
    )
    centre_id = centre_response.json()["id"]

    test_response = test_client.post("/tests", json={"name": "CBC"})
    test_id = test_response.json()["id"]

    ct_response = test_client.post(
        f"/tests/{test_id}/centres",
        json={"centre_id": centre_id, "test_id": test_id, "price": 500.0},
    )
    return ct_response.json()["id"]


def test_create_booking_success(test_client, auth_headers):
    """Test successful booking creation"""
    centre_test_id = create_centre_test(test_client)
    appointment_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    response = test_client.post(
        "/bookings",
        json={"centre_test_id": centre_test_id, "appointment_date": appointment_date},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["status"] == "PENDING"
    assert response.json()["amount"] == 500.0


def test_booking_price_snapshot(test_client, auth_headers, db):
    """Test that booking captures price at time of creation"""
    centre_test_id = create_centre_test(test_client)
    appointment_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    # Create booking at price 500
    response = test_client.post(
        "/bookings",
        json={"centre_test_id": centre_test_id, "appointment_date": appointment_date},
        headers=auth_headers,
    )
    assert response.json()["amount"] == 500.0


def test_create_booking_without_auth(test_client):
    """Test booking creation without authentication"""
    centre_test_id = create_centre_test(test_client)
    appointment_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    response = test_client.post(
        "/bookings",
        json={"centre_test_id": centre_test_id, "appointment_date": appointment_date},
    )
    assert response.status_code == 403


def test_booking_past_appointment(test_client, auth_headers):
    """Test booking with past appointment date"""
    centre_test_id = create_centre_test(test_client)
    appointment_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()

    response = test_client.post(
        "/bookings",
        json={"centre_test_id": centre_test_id, "appointment_date": appointment_date},
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert "past" in response.json()["detail"].lower()


def test_booking_nonexistent_centre_test(test_client, auth_headers):
    """Test booking with non-existent centre_test"""
    appointment_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    response = test_client.post(
        "/bookings",
        json={"centre_test_id": 9999, "appointment_date": appointment_date},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_list_bookings(test_client, auth_headers):
    """Test listing user's bookings"""
    centre_test_id = create_centre_test(test_client)
    appointment_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    test_client.post(
        "/bookings",
        json={"centre_test_id": centre_test_id, "appointment_date": appointment_date},
        headers=auth_headers,
    )

    response = test_client.get("/bookings", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1


def test_get_booking(test_client, auth_headers):
    """Test retrieving a specific booking"""
    centre_test_id = create_centre_test(test_client)
    appointment_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    create_response = test_client.post(
        "/bookings",
        json={"centre_test_id": centre_test_id, "appointment_date": appointment_date},
        headers=auth_headers,
    )
    booking_id = create_response.json()["id"]

    response = test_client.get(f"/bookings/{booking_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == booking_id


def test_get_booking_unauthorized(test_client, auth_headers, auth_headers_user2):
    """Test accessing another user's booking"""
    centre_test_id = create_centre_test(test_client)
    appointment_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    create_response = test_client.post(
        "/bookings",
        json={"centre_test_id": centre_test_id, "appointment_date": appointment_date},
        headers=auth_headers,
    )
    booking_id = create_response.json()["id"]

    response = test_client.get(f"/bookings/{booking_id}", headers=auth_headers_user2)
    assert response.status_code == 403


def test_cancel_booking(test_client, auth_headers):
    """Test cancelling a booking"""
    centre_test_id = create_centre_test(test_client)
    appointment_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    create_response = test_client.post(
        "/bookings",
        json={"centre_test_id": centre_test_id, "appointment_date": appointment_date},
        headers=auth_headers,
    )
    booking_id = create_response.json()["id"]

    response = test_client.post(
        f"/bookings/{booking_id}/cancel", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"


def test_cancel_already_cancelled_booking(test_client, auth_headers):
    """Test cancelling an already cancelled booking"""
    centre_test_id = create_centre_test(test_client)
    appointment_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    create_response = test_client.post(
        "/bookings",
        json={"centre_test_id": centre_test_id, "appointment_date": appointment_date},
        headers=auth_headers,
    )
    booking_id = create_response.json()["id"]

    test_client.post(f"/bookings/{booking_id}/cancel", headers=auth_headers)

    response = test_client.post(
        f"/bookings/{booking_id}/cancel", headers=auth_headers
    )
    assert response.status_code == 422


def test_unavailable_test_booking(test_client, auth_headers):
    """Test booking unavailable test"""
    centre_response = test_client.post(
        "/centres", json={"name": "Lab 1", "location": "Loc 1"}
    )
    centre_id = centre_response.json()["id"]

    test_response = test_client.post("/tests", json={"name": "Test 1"})
    test_id = test_response.json()["id"]

    # Create centre_test with available=False
    ct_response = test_client.post(
        f"/tests/{test_id}/centres",
        json={
            "centre_id": centre_id,
            "test_id": test_id,
            "price": 500,
            "available": False,
        },
    )
    centre_test_id = ct_response.json()["id"]

    appointment_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    response = test_client.post(
        "/bookings",
        json={"centre_test_id": centre_test_id, "appointment_date": appointment_date},
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert "not available" in response.json()["detail"]
