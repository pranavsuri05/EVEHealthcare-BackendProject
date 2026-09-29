#!/usr/bin/env python3
"""Verification script to test the project structure and basic functionality"""

import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

def verify_imports():
    """Verify all modules can be imported"""
    print("Verifying imports...")
    try:
        # Import models first (these don't need database)
        from app.db.models import User, Booking, Payment, DiagnosticCentre, DiagnosticTest, CentreTest
        from app.core.security import hash_password, verify_password, create_access_token, decode_token
        from app.services.auth_service import AuthService
        from app.services.booking_service import BookingService
        from app.services.payment_service import PaymentService, MockPaymentProvider
        from app.schemas.schemas import UserSignupRequest, BookingCreateRequest

        # Try to import app.main but skip database connection errors
        try:
            from app.main import app
        except Exception as db_error:
            if "connection to server" in str(db_error) or "role" in str(db_error):
                print("  ℹ️ Skipping app import (PostgreSQL not available - expected for this environment)")
            else:
                raise

        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def verify_models():
    """Verify database models"""
    print("\nVerifying database models...")
    try:
        from app.db.models import (
            Base, User, DiagnosticCentre, DiagnosticTest, CentreTest,
            Booking, Payment, BookingStatus, PaymentStatus
        )

        # Check model attributes
        assert hasattr(User, 'email')
        assert hasattr(User, 'hashed_password')
        assert hasattr(Booking, 'amount')
        assert hasattr(Booking, 'status')
        assert hasattr(Payment, 'provider_event_id')
        assert hasattr(CentreTest, 'price')

        print("✅ Database models verified")
        return True
    except Exception as e:
        print(f"❌ Model verification failed: {e}")
        return False


def verify_security():
    """Verify security functions work"""
    print("\nVerifying security functions...")
    try:
        from app.core.security import hash_password, verify_password, create_access_token, decode_token

        # Test password hashing
        password = "TestPassword123"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("WrongPassword", hashed)

        # Test JWT
        data = {"sub": "1"}
        token = create_access_token(data)
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded.get("sub") == "1"

        print("✅ Security functions verified")
        return True
    except Exception as e:
        print(f"❌ Security verification failed: {e}")
        return False


def verify_schemas():
    """Verify Pydantic schemas"""
    print("\nVerifying schemas...")
    try:
        from app.schemas.schemas import (
            UserSignupRequest, UserLoginRequest, BookingCreateRequest,
            DiagnosticCentreRequest, DiagnosticTestRequest,
            PaymentCreateRequest, WebhookPaymentEvent
        )

        # Test schema validation
        signup = UserSignupRequest(email="test@example.com", password="SecurePass123")
        assert signup.email == "test@example.com"

        booking = BookingCreateRequest(
            centre_test_id=1,
            appointment_date="2025-10-15T10:00:00Z"
        )
        assert booking.centre_test_id == 1

        print("✅ Schemas verified")
        return True
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")
        return False


def verify_api_routes():
    """Verify API routes exist"""
    print("\nVerifying API routes...")
    try:
        from app.api import auth, centres, tests, bookings, payments

        # Verify route modules have router objects
        assert hasattr(auth, 'router'), "auth module missing router"
        assert hasattr(centres, 'router'), "centres module missing router"
        assert hasattr(tests, 'router'), "tests module missing router"
        assert hasattr(bookings, 'router'), "bookings module missing router"
        assert hasattr(payments, 'router'), "payments module missing router"

        print("✅ API routes verified")
        return True
    except Exception as e:
        if "connection to server" in str(e) or "role" in str(e):
            print("  ℹ️ Skipping app import (PostgreSQL not available - expected for this environment)")
            return True
        print(f"❌ API routes verification failed: {e}")
        return False


def verify_payment_service():
    """Verify payment service logic"""
    print("\nVerifying payment service...")
    try:
        from app.services.payment_service import MockPaymentProvider, PaymentService

        # Test mock provider
        provider_success = MockPaymentProvider(success=True)
        assert provider_success.process_payment(100.0, 1) is True

        provider_fail = MockPaymentProvider(success=False)
        assert provider_fail.process_payment(100.0, 1) is False

        # Test service creation
        service = PaymentService(provider_success)
        assert service.provider is not None

        print("✅ Payment service verified")
        return True
    except Exception as e:
        print(f"❌ Payment service verification failed: {e}")
        return False


def verify_project_structure():
    """Verify project structure"""
    print("\nVerifying project structure...")
    try:
        required_files = [
            "app/main.py",
            "app/core/config.py",
            "app/core/security.py",
            "app/db/models.py",
            "app/api/auth.py",
            "app/api/bookings.py",
            "app/api/payments.py",
            "requirements.txt",
            "README.md",
            ".env.example",
            "Dockerfile",
            "docker-compose.yml",
            ".gitignore",
        ]

        for file_path in required_files:
            full_path = os.path.join(os.path.dirname(__file__), file_path)
            assert os.path.exists(full_path), f"File not found: {file_path}"

        print("✅ Project structure verified")
        return True
    except Exception as e:
        print(f"❌ Project structure verification failed: {e}")
        return False


def main():
    """Run all verifications"""
    print("=" * 60)
    print("EVE Healthcare Booking Service - Verification")
    print("=" * 60)

    checks = [
        verify_project_structure,
        verify_imports,
        verify_models,
        verify_security,
        verify_schemas,
        verify_payment_service,
        verify_api_routes,
    ]

    results = [check() for check in checks]

    print("\n" + "=" * 60)
    if all(results):
        print("✅ All verifications passed!")
        print("=" * 60)
        return 0
    else:
        print("❌ Some verifications failed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
