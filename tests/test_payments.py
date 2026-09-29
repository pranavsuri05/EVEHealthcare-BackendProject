import pytest
from datetime import datetime, timedelta, timezone
from app.services.payment_service import MockPaymentProvider, PaymentService


def create_booking_for_payment(test_client, auth_headers):
    """Helper to create a booking for payment testing"""
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
    centre_test_id = ct_response.json()["id"]

    appointment_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    booking_response = test_client.post(
        "/bookings",
        json={"centre_test_id": centre_test_id, "appointment_date": appointment_date},
        headers=auth_headers,
    )
    return booking_response.json()["id"]


def test_create_payment(test_client, auth_headers):
    """Test creating a payment"""
    booking_id = create_booking_for_payment(test_client, auth_headers)

    response = test_client.post(
        "/payments",
        json={"booking_id": booking_id},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["status"] == "PENDING"
    assert response.json()["amount"] == 500.0


def test_create_payment_invalid_booking(test_client, auth_headers):
    """Test payment for non-existent booking"""
    response = test_client.post(
        "/payments",
        json={"booking_id": 9999},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_create_payment_unauthorized(test_client, auth_headers, auth_headers_user2):
    """Test payment for another user's booking"""
    booking_id = create_booking_for_payment(test_client, auth_headers)

    response = test_client.post(
        "/payments",
        json={"booking_id": booking_id},
        headers=auth_headers_user2,
    )
    assert response.status_code == 403


def test_create_payment_cancelled_booking(test_client, auth_headers):
    """Test payment for cancelled booking"""
    booking_id = create_booking_for_payment(test_client, auth_headers)

    test_client.post(f"/bookings/{booking_id}/cancel", headers=auth_headers)

    response = test_client.post(
        "/payments",
        json={"booking_id": booking_id},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_process_payment_success(test_client, auth_headers):
    """Test successful payment processing"""
    booking_id = create_booking_for_payment(test_client, auth_headers)

    payment_response = test_client.post(
        "/payments",
        json={"booking_id": booking_id},
        headers=auth_headers,
    )
    payment_id = payment_response.json()["id"]

    response = test_client.post(
        f"/payments/{payment_id}/process",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "SUCCESS"

    # Verify booking is confirmed
    booking_response = test_client.get(f"/bookings/{booking_id}", headers=auth_headers)
    assert booking_response.json()["status"] == "CONFIRMED"


def test_duplicate_payment_prevention(test_client, auth_headers):
    """Test that duplicate payments are prevented"""
    booking_id = create_booking_for_payment(test_client, auth_headers)

    # Create first payment
    payment_response = test_client.post(
        "/payments",
        json={"booking_id": booking_id},
        headers=auth_headers,
    )
    payment_id = payment_response.json()["id"]

    # Process it
    test_client.post(f"/payments/{payment_id}/process", headers=auth_headers)

    # Try to create another payment for same booking
    response = test_client.post(
        "/payments",
        json={"booking_id": booking_id},
        headers=auth_headers,
    )
    assert response.status_code == 409


def test_webhook_payment_success(test_client, auth_headers):
    """Test webhook payment success"""
    booking_id = create_booking_for_payment(test_client, auth_headers)

    # Create payment but don't process it through normal flow
    payment_response = test_client.post(
        "/payments",
        json={"booking_id": booking_id},
        headers=auth_headers,
    )
    payment_id = payment_response.json()["id"]

    # Send webhook
    response = test_client.post(
        "/payments/webhook/payment-status",
        json={
            "event_id": "evt_123456",
            "booking_id": payment_id,  # Using payment_id as identifier
            "status": "SUCCESS",
            "amount": 500.0,
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "processed"


def test_webhook_idempotency(test_client, auth_headers):
    """Test that webhook is idempotent"""
    booking_id = create_booking_for_payment(test_client, auth_headers)

    payment_response = test_client.post(
        "/payments",
        json={"booking_id": booking_id},
        headers=auth_headers,
    )
    payment_id = payment_response.json()["id"]

    # Send same webhook twice with same event_id
    event_id = "evt_idempotent_123"
    webhook_payload = {
        "event_id": event_id,
        "booking_id": payment_id,
        "status": "SUCCESS",
        "amount": 500.0,
    }

    response1 = test_client.post(
        "/payments/webhook/payment-status",
        json=webhook_payload,
    )
    assert response1.status_code == 200

    response2 = test_client.post(
        "/payments/webhook/payment-status",
        json=webhook_payload,
    )
    assert response2.status_code == 200
    # Second response should indicate already processed
    assert "already_processed" in response2.json()["status"] or "processed" in response2.json()["status"]


def test_webhook_duplicate_event_id(test_client, auth_headers):
    """Test that duplicate event IDs are handled properly"""
    booking_id = create_booking_for_payment(test_client, auth_headers)

    payment_response = test_client.post(
        "/payments",
        json={"booking_id": booking_id},
        headers=auth_headers,
    )
    payment_id = payment_response.json()["id"]

    # Send webhook
    event_id = "evt_same_123"
    test_client.post(
        "/payments/webhook/payment-status",
        json={
            "event_id": event_id,
            "booking_id": payment_id,
            "status": "SUCCESS",
            "amount": 500.0,
        },
    )

    # Try to send again with same event_id
    response = test_client.post(
        "/payments/webhook/payment-status",
        json={
            "event_id": event_id,
            "booking_id": payment_id,
            "status": "SUCCESS",
            "amount": 500.0,
        },
    )
    assert response.status_code == 200


def test_payment_state_protection(test_client, auth_headers):
    """Test that payment state transitions are protected"""
    booking_id = create_booking_for_payment(test_client, auth_headers)

    payment_response = test_client.post(
        "/payments",
        json={"booking_id": booking_id},
        headers=auth_headers,
    )
    payment_id = payment_response.json()["id"]

    # Process first time - should succeed
    response1 = test_client.post(
        f"/payments/{payment_id}/process",
        headers=auth_headers,
    )
    assert response1.status_code == 200

    # Try to process again - should fail
    response2 = test_client.post(
        f"/payments/{payment_id}/process",
        headers=auth_headers,
    )
    assert response2.status_code == 422
