import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def setup_logging():
    handler = logging.StreamHandler()
    formatter = StructuredFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def log_user_signup(email: str):
    logger.info(json.dumps({"event": "user_signup", "email": email}))


def log_auth_failure(email: str, reason: str):
    logger.info(json.dumps({"event": "auth_failure", "email": email, "reason": reason}))


def log_booking_created(user_id: int, booking_id: int, amount: float):
    logger.info(
        json.dumps(
            {
                "event": "booking_created",
                "user_id": user_id,
                "booking_id": booking_id,
                "amount": amount,
            }
        )
    )


def log_payment_created(booking_id: int, amount: float):
    logger.info(
        json.dumps(
            {
                "event": "payment_created",
                "booking_id": booking_id,
                "amount": amount,
            }
        )
    )


def log_payment_status(payment_id: int, status: str, booking_id: int):
    logger.info(
        json.dumps(
            {
                "event": "payment_status",
                "payment_id": payment_id,
                "status": status,
                "booking_id": booking_id,
            }
        )
    )


def log_webhook_received(provider_event_id: str):
    logger.info(
        json.dumps(
            {
                "event": "webhook_received",
                "provider_event_id": provider_event_id,
            }
        )
    )


def log_webhook_duplicate(provider_event_id: str):
    logger.info(
        json.dumps(
            {
                "event": "webhook_duplicate",
                "provider_event_id": provider_event_id,
            }
        )
    )
