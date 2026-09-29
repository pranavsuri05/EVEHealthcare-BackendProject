from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import Payment, Booking, PaymentStatus, BookingStatus
from app.core.exceptions import (
    ResourceNotFound,
    ValidationError,
    ConflictError,
    NotAuthorized,
)
from app.core.logging import log_payment_created, log_payment_status


class PaymentProvider:
    """Abstract payment provider interface"""

    def process_payment(self, amount: float, booking_id: int) -> bool:
        raise NotImplementedError


class MockPaymentProvider(PaymentProvider):
    """Deterministic mock payment provider for testing"""

    def __init__(self, success: bool = True):
        self.success = success

    def process_payment(self, amount: float, booking_id: int) -> bool:
        return self.success


class PaymentService:
    def __init__(self, provider: PaymentProvider = None):
        self.provider = provider or MockPaymentProvider(success=True)

    def create_payment(
        self, booking_id: int, user_id: int, db: Session
    ) -> Payment:
        # Get booking
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise ResourceNotFound("Booking", str(booking_id))

        # Verify ownership
        if booking.user_id != user_id:
            raise NotAuthorized("You can only pay for your own bookings")

        # Check booking status
        if booking.status == BookingStatus.CANCELLED:
            raise ValidationError("Cannot create payment for cancelled booking")

        if booking.status == BookingStatus.CONFIRMED:
            raise ValidationError("Booking already has successful payment")

        # Check if payment already exists with SUCCESS status
        existing_payment = (
            db.query(Payment)
            .filter(
                Payment.booking_id == booking_id,
                Payment.status == PaymentStatus.SUCCESS,
            )
            .first()
        )
        if existing_payment:
            raise ConflictError("Payment already successfully processed for this booking")

        # Create new payment
        payment = Payment(booking_id=booking_id, amount=booking.amount)
        db.add(payment)
        db.flush()  # Get the ID

        log_payment_created(booking_id, booking.amount)

        db.commit()
        db.refresh(payment)
        return payment

    def process_payment(
        self, payment_id: int, user_id: int, db: Session
    ) -> Payment:
        # Get payment
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise ResourceNotFound("Payment", str(payment_id))

        # Verify ownership through booking
        booking = payment.booking
        if booking.user_id != user_id:
            raise NotAuthorized("You can only process payments for your own bookings")

        # Check if already processed
        if payment.status != PaymentStatus.PENDING:
            raise ValidationError(f"Payment already {payment.status.lower()}")

        # Process payment with provider
        success = self.provider.process_payment(payment.amount, booking.id)

        # Update payment status
        payment.status = PaymentStatus.SUCCESS if success else PaymentStatus.FAILED

        # Update booking status
        if success:
            booking.status = BookingStatus.CONFIRMED
        else:
            booking.status = BookingStatus.FAILED

        db.commit()
        db.refresh(payment)

        log_payment_status(payment.id, payment.status, booking.id)

        return payment

    def process_webhook_payment(
        self, payment_id: int, status: str, provider_event_id: str, db: Session
    ) -> Payment:
        # Check if event already processed
        existing = (
            db.query(Payment)
            .filter(Payment.provider_event_id == provider_event_id)
            .first()
        )
        if existing:
            # Already processed
            return existing

        # Get payment
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise ResourceNotFound("Payment", str(payment_id))

        booking = payment.booking

        # Only update if current status is PENDING
        if payment.status != PaymentStatus.PENDING:
            raise ValidationError(
                f"Cannot update payment with status {payment.status}"
            )

        # Protect state transitions
        if status == PaymentStatus.SUCCESS:
            if booking.status not in [
                BookingStatus.PENDING,
                BookingStatus.FAILED,
            ]:
                raise ValidationError(
                    f"Cannot confirm booking with status {booking.status}"
                )
            payment.status = PaymentStatus.SUCCESS
            booking.status = BookingStatus.CONFIRMED
        elif status == PaymentStatus.FAILED:
            if booking.status == BookingStatus.CANCELLED:
                raise ValidationError("Cannot fail payment for cancelled booking")
            payment.status = PaymentStatus.FAILED
            booking.status = BookingStatus.FAILED
        else:
            raise ValidationError(f"Invalid payment status: {status}")

        # Set provider event ID for idempotency
        payment.provider_event_id = provider_event_id

        db.commit()
        db.refresh(payment)

        log_payment_status(payment.id, payment.status, booking.id)

        return payment
