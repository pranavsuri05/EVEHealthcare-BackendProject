from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.schemas.schemas import PaymentCreateRequest, PaymentResponse, WebhookPaymentEvent
from app.services.payment_service import PaymentService
from app.core.dependencies import get_current_user
from app.core.logging import log_webhook_received, log_webhook_duplicate
from app.core.exceptions import ValidationError

router = APIRouter(prefix="/payments", tags=["payments"])

payment_service = PaymentService()


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    request: PaymentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a payment for a booking.

    The payment will be processed by the simulated payment provider.
    """
    payment = payment_service.create_payment(
        booking_id=request.booking_id,
        user_id=current_user.id,
        db=db,
    )
    return payment


@router.post("/{payment_id}/process", response_model=PaymentResponse)
def process_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Process a pending payment.

    The simulated payment provider will either succeed or fail the payment,
    and the booking status will be updated accordingly.
    """
    payment = payment_service.process_payment(
        payment_id=payment_id,
        user_id=current_user.id,
        db=db,
    )
    return payment


@router.post("/webhook/payment-status")
async def payment_webhook(
    event: WebhookPaymentEvent,
    db: Session = Depends(get_db),
):
    """
    Idempotent webhook for payment status updates from provider.

    This endpoint ensures that even if the webhook is received multiple times
    with the same event_id, the payment is only updated once.
    """
    log_webhook_received(event.event_id)

    try:
        payment = payment_service.process_webhook_payment(
            payment_id=event.booking_id,  # In this simple implementation, using booking_id
            status=event.status,
            provider_event_id=event.event_id,
            db=db,
        )
        return {"status": "processed", "payment_id": payment.id}
    except ValidationError as e:
        if "Cannot update payment" in str(e.detail):
            log_webhook_duplicate(event.event_id)
            # Already processed - return idempotent success
            return {"status": "already_processed", "event_id": event.event_id}
        raise
