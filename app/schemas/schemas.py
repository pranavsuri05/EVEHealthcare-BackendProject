from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ============ Auth Schemas ============
class UserSignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Diagnostic Centre Schemas ============
class DiagnosticCentreRequest(BaseModel):
    name: str = Field(..., min_length=1)
    location: str = Field(..., min_length=1)


class DiagnosticCentreResponse(BaseModel):
    id: int
    name: str
    location: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Diagnostic Test Schemas ============
class DiagnosticTestRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None


class DiagnosticTestResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Centre Test Schemas ============
class CentreTestRequest(BaseModel):
    centre_id: int
    test_id: int
    price: float = Field(..., gt=0)
    available: bool = True


class CentreTestResponse(BaseModel):
    id: int
    centre_id: int
    test_id: int
    price: float
    available: bool
    centre: Optional[DiagnosticCentreResponse] = None
    test: Optional[DiagnosticTestResponse] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CentreTestWithRelationsResponse(BaseModel):
    id: int
    centre_id: int
    test_id: int
    price: float
    available: bool
    centre: DiagnosticCentreResponse
    test: DiagnosticTestResponse
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Booking Schemas ============
class BookingCreateRequest(BaseModel):
    centre_test_id: int
    appointment_date: datetime


class BookingResponse(BaseModel):
    id: int
    user_id: int
    centre_id: int
    test_id: int
    centre_test_id: int
    appointment_date: datetime
    amount: float
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookingDetailResponse(BaseModel):
    id: int
    user_id: int
    centre_id: int
    test_id: int
    centre_test_id: int
    appointment_date: datetime
    amount: float
    status: str
    centre: DiagnosticCentreResponse
    test: DiagnosticTestResponse
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Payment Schemas ============
class PaymentCreateRequest(BaseModel):
    booking_id: int


class PaymentResponse(BaseModel):
    id: int
    booking_id: int
    amount: float
    status: str
    provider_event_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Webhook Schemas ============
class WebhookPaymentEvent(BaseModel):
    event_id: str
    booking_id: int
    status: str
    amount: float


# ============ Pagination Schemas ============
class PaginationParams(BaseModel):
    skip: int = Field(0, ge=0)
    limit: int = Field(10, ge=1, le=100)


class PaginatedResponse(BaseModel):
    items: list
    total: int
    skip: int
    limit: int


# ============ Error Schemas ============
class ErrorResponse(BaseModel):
    detail: str
