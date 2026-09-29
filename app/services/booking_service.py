from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models import (
    Booking,
    CentreTest,
    DiagnosticCentre,
    DiagnosticTest,
    BookingStatus,
)
from app.core.exceptions import (
    ResourceNotFound,
    ValidationError,
    NotAuthorized,
)
from app.core.logging import log_booking_created


class BookingService:
    @staticmethod
    def create_booking(
        user_id: int,
        centre_test_id: int,
        appointment_date: datetime,
        db: Session,
    ) -> Booking:
        # Get centre_test
        centre_test = (
            db.query(CentreTest).filter(CentreTest.id == centre_test_id).first()
        )
        if not centre_test:
            raise ResourceNotFound("Centre test", str(centre_test_id))

        # Verify test is available
        if not centre_test.available:
            raise ValidationError("Test is not available at this centre")

        # Verify appointment time is in the future
        now = datetime.now(timezone.utc)
        if appointment_date <= now:
            raise ValidationError("Appointment time cannot be in the past")

        # Create booking with current price snapshot
        booking = Booking(
            user_id=user_id,
            centre_test_id=centre_test_id,
            centre_id=centre_test.centre_id,
            test_id=centre_test.test_id,
            appointment_date=appointment_date,
            amount=centre_test.price,
            status=BookingStatus.PENDING,
        )

        db.add(booking)
        db.commit()
        db.refresh(booking)

        log_booking_created(user_id, booking.id, booking.amount)

        return booking

    @staticmethod
    def get_booking(booking_id: int, user_id: int, db: Session) -> Booking:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise ResourceNotFound("Booking", str(booking_id))

        # Verify ownership
        if booking.user_id != user_id:
            raise NotAuthorized("You can only access your own bookings")

        return booking

    @staticmethod
    def list_bookings(user_id: int, skip: int, limit: int, db: Session) -> tuple[list, int]:
        query = db.query(Booking).filter(Booking.user_id == user_id)
        total = query.count()
        bookings = query.offset(skip).limit(limit).all()
        return bookings, total

    @staticmethod
    def cancel_booking(booking_id: int, user_id: int, db: Session) -> Booking:
        booking = BookingService.get_booking(booking_id, user_id, db)

        # Check if already cancelled
        if booking.status == BookingStatus.CANCELLED:
            raise ValidationError("Booking is already cancelled")

        # Cannot cancel if already confirmed or failed with successful payment
        if booking.status == BookingStatus.CONFIRMED:
            raise ValidationError("Cannot cancel a confirmed booking")

        # Cancel booking
        booking.status = BookingStatus.CANCELLED
        db.commit()
        db.refresh(booking)

        return booking
