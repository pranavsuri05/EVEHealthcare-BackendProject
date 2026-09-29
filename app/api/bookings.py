from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.schemas.schemas import (
    BookingCreateRequest,
    BookingResponse,
    BookingDetailResponse,
    PaginatedResponse,
)
from app.services.booking_service import BookingService
from app.core.dependencies import get_current_user
from app.core.exceptions import ResourceNotFound

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post(
    "", response_model=BookingResponse, status_code=status.HTTP_201_CREATED
)
def create_booking(
    request: BookingCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new diagnostic test booking.

    The booking amount is automatically captured from the current
    centre_test price at the time of booking creation.
    """
    booking = BookingService.create_booking(
        user_id=current_user.id,
        centre_test_id=request.centre_test_id,
        appointment_date=request.appointment_date,
        db=db,
    )
    return booking


@router.get("", response_model=PaginatedResponse)
def list_bookings(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all bookings for the current user"""
    bookings, total = BookingService.list_bookings(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        db=db,
    )
    return PaginatedResponse(items=bookings, total=total, skip=skip, limit=limit)


@router.get("/{booking_id}", response_model=BookingDetailResponse)
def get_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details of a specific booking"""
    booking = BookingService.get_booking(
        booking_id=booking_id,
        user_id=current_user.id,
        db=db,
    )
    return booking


@router.post("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel an existing booking"""
    booking = BookingService.cancel_booking(
        booking_id=booking_id,
        user_id=current_user.id,
        db=db,
    )
    return booking
