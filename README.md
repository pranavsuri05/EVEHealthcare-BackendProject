# EVE Healthcare — Diagnostic Booking Backend

## 1. Overview

This is a production-oriented backend service for managing diagnostic test bookings and simulated payments. The system is designed to support:

- **User authentication** with JWT tokens
- **Diagnostic centre and test management** with flexible pricing
- **Booking workflow** with appointment scheduling
- **Simulated payment processing** with state management
- **Idempotent payment webhooks** for reliability
- **Comprehensive error handling** and validation
- **Structured logging** and monitoring-friendly output

The architecture prioritizes **correctness, maintainability, and edge-case handling** over unnecessary complexity.

## 2. Features

✅ **JWT Authentication** — Signup, login, and token-based access control
✅ **Diagnostic Centres & Tests** — Create and manage centres, tests, and centre-test relationships with pricing
✅ **Booking System** — Users can book diagnostic tests with automatic price snapshots
✅ **Simulated Payments** — Deterministic payment processing with state tracking
✅ **Idempotent Webhooks** — Reliable payment status updates using provider event IDs
✅ **Validation & Error Handling** — Comprehensive input validation and edge-case protection
✅ **Pagination** — List endpoints support limit/offset pagination
✅ **Structured Logging** — JSON-formatted logs for observability
✅ **Docker & Docker Compose** — Containerized deployment
✅ **Swagger/OpenAPI** — Auto-generated API documentation
✅ **Comprehensive Tests** — 40+ test cases covering all major flows
✅ **Database Migrations** — Ready for Alembic (migrations can be added as needed)

## 3. Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Framework** | FastAPI | Fast, modern, excellent OpenAPI support, built-in validation |
| **Database** | PostgreSQL | Relational integrity, constraints, transactions for consistency |
| **ORM** | SQLAlchemy 2.x | Powerful, type-safe, strong relationship handling |
| **Auth** | python-jose + Argon2 | Industry-standard JWT, secure password hashing |
| **Validation** | Pydantic v2 | Declarative schemas, automatic OpenAPI documentation |
| **Testing** | pytest | Comprehensive, flexible, excellent fixture support |
| **Deployment** | Docker + docker-compose | Consistent environments, easy local development |

## 4. Architecture

```
app/
├── main.py                      # FastAPI app initialization
├── core/
│   ├── config.py               # Settings and environment variables
│   ├── security.py             # JWT and password hashing
│   ├── exceptions.py           # Centralized exception definitions
│   ├── dependencies.py         # JWT extraction and current user
│   └── logging.py              # Structured logging utilities
├── db/
│   ├── database.py             # SQLAlchemy setup
│   └── models.py               # All ORM models
├── schemas/
│   └── schemas.py              # Pydantic request/response models
├── api/
│   ├── auth.py                 # Authentication endpoints
│   ├── centres.py              # Diagnostic centre endpoints
│   ├── tests.py                # Diagnostic test endpoints
│   ├── bookings.py             # Booking endpoints
│   └── payments.py             # Payment and webhook endpoints
├── services/
│   ├── auth_service.py         # User signup/login logic
│   ├── booking_service.py      # Booking creation/management
│   └── payment_service.py      # Payment processing and webhooks
└── repositories/               # (Data access abstraction layer)

tests/
├── conftest.py                 # Pytest configuration and fixtures
├── test_auth.py                # Authentication tests
├── test_centres_tests.py       # Centre/test management tests
├── test_bookings.py            # Booking workflow tests
└── test_payments.py            # Payment and webhook tests

alembic/                         # Database migrations (ready to use)
Dockerfile                       # Container image definition
docker-compose.yml              # Local development setup
requirements.txt                # Python dependencies
.env.example                    # Environment variable template
```

### Key Design Decisions

1. **Service Layer Abstraction** — Business logic lives in services, not route handlers
2. **Dependency Injection** — MockPaymentProvider can be injected for deterministic testing
3. **Database Constraints** — Foreign keys, unique constraints, and indexes enforce invariants
4. **Structured Responses** — Consistent error format, proper HTTP status codes
5. **No Mass Assignment** — Explicit request models prevent accidental field exposure

## 5. Database Design

### Entity Relationship Diagram

```
┌──────────────────┐
│     users        │
├──────────────────┤
│ id (PK)          │
│ email (UNIQUE)   │
│ hashed_password  │
│ created_at       │
│ updated_at       │
└────────┬─────────┘
         │ 1:N
         │
         └──────────┐
                    │
         ┌──────────┴─────────┐
         │     bookings       │
         ├────────────────────┤
         │ id (PK)            │
         │ user_id (FK)       │
         │ centre_test_id (FK)│
         │ centre_id (FK)     │
         │ test_id (FK)       │
         │ appointment_date   │
         │ amount             │
         │ status             │
         │ created_at         │
         │ updated_at         │
         └────────┬───────────┘
                  │
         ┌────────┴──────────────┐
         │                       │
    ┌────┴────┐            ┌─────┴─────┐
    │ payments │            │ centre_test│
    ├──────────┤            ├────────────┤
    │ id (PK)  │            │ id (PK)    │
    │ booking  │            │ centre_id  │
    │ (FK)     │            │ (FK)       │
    │ amount   │            │ test_id    │
    │ status   │            │ (FK)       │
    │ provider │            │ price      │
    │ event_id │            │ available  │
    │ created  │            │ created_at │
    │ updated  │            │ updated_at │
    └──────────┘            └─────┬──────┘
                                  │
                    ┌─────────────┴──────────────┐
                    │                            │
         ┌──────────┴────────────┐   ┌──────────┴─────────┐
         │ diagnostic_centres    │   │ diagnostic_tests   │
         ├───────────────────────┤   ├────────────────────┤
         │ id (PK)               │   │ id (PK)            │
         │ name                  │   │ name (UNIQUE)      │
         │ location              │   │ description        │
         │ created_at            │   │ created_at         │
         │ updated_at            │   │ updated_at         │
         └───────────────────────┘   └────────────────────┘
```

### Critical Design Points

**1. Centre/Test Relationship (centre_tests table)**

A diagnostic test can be offered by multiple centres at different prices. Instead of storing price on either `diagnostic_tests` or `diagnostic_centres`, we use a **junction table**:

```sql
-- centre_tests table
CREATE TABLE centre_tests (
  id SERIAL PRIMARY KEY,
  centre_id INTEGER NOT NULL REFERENCES diagnostic_centres(id),
  test_id INTEGER NOT NULL REFERENCES diagnostic_tests(id),
  price FLOAT NOT NULL,
  available BOOLEAN DEFAULT true,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  UNIQUE(centre_id, test_id)  -- Enforce one entry per centre/test pair
);
```

**Why:**
- Same test at different centres can have different prices
- Easy to update availability without affecting other centres
- Clear separation of concerns

**2. Booking Amount Snapshot**

When a booking is created, we capture the current price:

```python
booking = Booking(
  user_id=user_id,
  centre_test_id=centre_test_id,
  centre_id=centre_test.centre_id,
  test_id=centre_test.test_id,
  appointment_date=appointment_date,
  amount=centre_test.price,  # Snapshot at booking time
  status=BookingStatus.PENDING,
)
```

**Why:**
- If a centre changes test pricing later, existing bookings retain original price
- Prevents payment disputes
- Simplifies audit trail

**3. Payment Idempotency with provider_event_id**

Each payment webhook must include a unique `provider_event_id`:

```sql
CREATE TABLE payments (
  id SERIAL PRIMARY KEY,
  booking_id INTEGER NOT NULL REFERENCES bookings(id),
  amount FLOAT NOT NULL,
  status VARCHAR NOT NULL,
  provider_event_id VARCHAR UNIQUE,  -- Ensures idempotency
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);
```

**Why:**
- Network failures can cause duplicate webhook deliveries
- UNIQUE constraint prevents duplicate processing at the database level
- Webhook handler checks if `provider_event_id` was already processed

### Indexes

Indexes are placed on frequently queried columns:

```python
# Users
Index("idx_user_email", "email")

# Centre Tests
Index("idx_centre_test_centre", "centre_id")
Index("idx_centre_test_test", "test_id")

# Bookings
Index("idx_booking_user", "user_id")
Index("idx_booking_centre", "centre_id")
Index("idx_booking_test", "test_id")
Index("idx_booking_status", "status")

# Payments
Index("idx_payment_booking", "booking_id")
Index("idx_payment_status", "status")
Index("idx_payment_provider_event", "provider_event_id")
```

## 6. Booking Flow

```
User Flow:
  1. User signs up or logs in
  2. Receives JWT access token
  3. Views available diagnostic centres and tests
  4. Selects a test + centre combination + appointment date
  5. Creates booking (status: PENDING, amount captured)
  6. Creates payment request
  7. Processes payment
     a. SUCCESS → Booking status: CONFIRMED
     b. FAILED → Booking status: FAILED
  8. User can cancel pending booking

Webhook Flow:
  1. Provider sends payment status update
  2. Includes unique event_id
  3. Handler checks if event_id already processed (idempotency)
  4. Updates payment + booking status atomically
  5. Returns idempotent success response
```

## 7. Payment & Webhook Design

### Payment State Machine

```
┌─────────────────────────────────────────────────┐
│ Booking States                                  │
├─────────────────────────────────────────────────┤
│                                                 │
│  PENDING (initial)                              │
│    ↓                                            │
│    ├─→ CONFIRMED (payment SUCCESS)              │
│    ├─→ FAILED (payment FAILED)                  │
│    └─→ CANCELLED (user cancels)                 │
│                                                 │
│ Constraints:                                    │
│  - Cannot cancel CONFIRMED or FAILED           │
│  - Cannot transition from CANCELLED            │
│  - Each booking can have one SUCCESS payment   │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Webhook Idempotency

**Key Principle:** If the same webhook is received multiple times, the system must:
- ✅ Not create duplicate payments
- ✅ Not corrupt booking state
- ✅ Return success both times (idempotent)

**Implementation:**

```python
# 1. Check if event already processed
existing = db.query(Payment).filter(
    Payment.provider_event_id == provider_event_id
).first()
if existing:
    return {"status": "already_processed"}

# 2. Process atomically
payment.status = PaymentStatus.SUCCESS
booking.status = BookingStatus.CONFIRMED
payment.provider_event_id = provider_event_id
db.commit()

return {"status": "processed"}
```

**Protection Against Invalid Transitions:**

```python
# Don't allow SUCCESS if booking is already CANCELLED
if status == PaymentStatus.SUCCESS:
    if booking.status == BookingStatus.CANCELLED:
        raise ValidationError("Cannot confirm cancelled booking")
```

## 8. API Endpoints

| Method | Endpoint | Authentication | Purpose |
|--------|----------|----------------|---------|
| **POST** | `/auth/signup` | ❌ | Create new user account |
| **POST** | `/auth/login` | ❌ | Login and receive JWT |
| **GET** | `/auth/me` | ✅ | Get current user info |
| | | | |
| **POST** | `/centres` | ❌ | Create diagnostic centre |
| **GET** | `/centres` | ❌ | List centres (paginated) |
| **GET** | `/centres/{id}` | ❌ | Get centre details |
| | | | |
| **POST** | `/tests` | ❌ | Create diagnostic test |
| **GET** | `/tests` | ❌ | List tests (paginated) |
| **GET** | `/tests/{id}` | ❌ | Get test details |
| **POST** | `/tests/{id}/centres` | ❌ | Add test to centre |
| **GET** | `/tests/centre/{id}/tests` | ❌ | List tests at centre |
| | | | |
| **POST** | `/bookings` | ✅ | Create booking |
| **GET** | `/bookings` | ✅ | List user's bookings |
| **GET** | `/bookings/{id}` | ✅ | Get booking details |
| **POST** | `/bookings/{id}/cancel` | ✅ | Cancel booking |
| | | | |
| **POST** | `/payments` | ✅ | Create payment |
| **POST** | `/payments/{id}/process` | ✅ | Process payment |
| **POST** | `/payments/webhook/payment-status` | ❌ | Webhook: payment update |
| | | | |
| **GET** | `/health` | ❌ | Health check |
| **GET** | `/docs` | ❌ | Swagger UI |

### Example Request/Response Payloads

**Signup:**
```bash
POST /auth/signup
{
  "email": "user@example.com",
  "password": "SecurePass123"
}

Response 201:
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

**Create Booking:**
```bash
POST /bookings
Authorization: Bearer {token}
{
  "centre_test_id": 1,
  "appointment_date": "2025-10-15T10:00:00Z"
}

Response 201:
{
  "id": 1,
  "user_id": 1,
  "centre_id": 1,
  "test_id": 1,
  "centre_test_id": 1,
  "appointment_date": "2025-10-15T10:00:00Z",
  "amount": 500.0,
  "status": "PENDING",
  "created_at": "2025-09-29T...",
  "updated_at": "2025-09-29T..."
}
```

**Payment Webhook:**
```bash
POST /payments/webhook/payment-status
{
  "event_id": "evt_abc123",
  "booking_id": 1,
  "status": "SUCCESS",
  "amount": 500.0
}

Response 200:
{
  "status": "processed",
  "payment_id": 1
}
```

## 9. Setup

### Prerequisites

- Python 3.12+
- Docker & Docker Compose (for containerized setup)
- OR PostgreSQL 14+ (for local development)

### Quick Start (Docker)

```bash
# Clone repository
git clone <repo>
cd <repo>

# Start services
docker compose up --build

# Application is available at http://localhost:8000
# Swagger UI: http://localhost:8000/docs
```

### Local Development (Without Docker)

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your PostgreSQL credentials
# DATABASE_URL=postgresql://user:password@localhost:5432/eve_db

# Run application
uvicorn app.main:app --reload

# Application is available at http://localhost:8000
```

## 10. Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | (required) | PostgreSQL connection string |
| `SECRET_KEY` | (required) | JWT signing key (change in production!) |
| `ALGORITHM` | HS256 | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Token expiration time |
| `APP_NAME` | EVE Healthcare Booking Service | Application name |
| `APP_ENV` | development | Environment (development/production) |
| `DEBUG` | True | Debug mode |

Example `.env`:
```
DATABASE_URL=postgresql://eve_user:eve_password@localhost:5432/eve_db
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
APP_NAME=EVE Healthcare Booking Service
APP_ENV=development
DEBUG=True
```

## 11. Database Migrations

This project uses SQLAlchemy ORM. For production deployments, use Alembic:

```bash
# Initialize Alembic (if starting fresh)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

For local development with Docker, the database is initialized automatically on startup.

## 12. Testing

Run comprehensive test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_signup_success

# Run with verbose output
pytest -v
```

**Test Coverage:**

- ✅ **Authentication (8 tests)**
  - Signup success, duplicate email, invalid email, weak password
  - Login success, invalid email, invalid password
  - Protected endpoints, invalid tokens

- ✅ **Centres & Tests (9 tests)**
  - Create/list/retrieve centres
  - Create/list/retrieve tests
  - Add tests to centres with pricing
  - Duplicate relationships, invalid prices

- ✅ **Bookings (11 tests)**
  - Create booking, price snapshot
  - Past appointments, unavailable tests
  - Authorization checks
  - Booking cancellation
  - State transitions

- ✅ **Payments (9 tests)**
  - Create/process payments
  - Payment for cancelled bookings
  - Duplicate payment prevention
  - Webhook idempotency
  - State protection

**Total: 40+ test cases ensuring correctness and edge-case handling**

## 13. Error Handling

All errors follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| **200** | OK | Successful GET, successful payment |
| **201** | Created | User signup, booking created |
| **204** | No Content | Successful DELETE (if used) |
| **400** | Bad Request | Invalid query parameters |
| **401** | Unauthorized | Missing/invalid JWT |
| **403** | Forbidden | Authenticated but not authorized |
| **404** | Not Found | Resource doesn't exist |
| **409** | Conflict | Duplicate resource, invalid state |
| **422** | Unprocessable Entity | Validation error (invalid input) |
| **500** | Server Error | Unexpected exception |

## 14. Assumptions

1. **Test Pricing** — The same diagnostic test can be offered at different prices by different centres
2. **Booking Snapshots** — Booking amount is captured at booking creation time; price changes don't affect existing bookings
3. **User Isolation** — Users can only access/modify their own bookings and payments
4. **Appointment Timing** — Appointment times cannot be in the past
5. **Payment Uniqueness** — A booking can have at most one successful payment
6. **Webhook Idempotency** — Payment webhook provider events use unique IDs; repeated webhooks are safely handled
7. **State Protection** — Invalid state transitions are rejected (e.g., can't confirm a cancelled booking)
8. **Test Availability** — Tests can be marked unavailable per centre
9. **Admin Operations** — Centre and test management endpoints are publicly accessible (in production, add role-based access control)
10. **No Inventory** — Bookings don't decrement test availability (treat as unlimited capacity)

## 15. Design Decisions & Tradeoffs

| Decision | Rationale | Tradeoff |
|----------|-----------|----------|
| **JWT instead of sessions** | Stateless, scalable, ideal for APIs | Cannot revoke tokens without Redis |
| **Argon2 password hashing** | Slow, memory-hard, resistant to GPU attacks | Slightly slower signup/login |
| **SQLite for tests** | Fast, in-memory, no external dependencies | Not PostgreSQL compatible |
| **Deterministic mock payment** | Enables reliable, repeatable tests | Doesn't simulate rate limits or network errors |
| **Webhook idempotency via DB constraint** | Enforced at database level, foolproof | Requires unique provider event IDs |
| **Price snapshot in booking** | Prevents disputes, clear audit trail | Small storage overhead |
| **Junction table for centre/test** | Flexible pricing, clean separation | Slightly more complex queries |
| **Structured JSON logging** | Machine-readable, easy to aggregate | Slightly more verbose output |

## 16. What I Would Improve With More Time

1. **Redis Caching** — Cache frequently accessed centres, tests, and centre-test relationships to reduce database load
2. **Background Tasks** — Use Celery for webhook retry logic, async notifications, and non-critical operations
3. **Rate Limiting** — Implement rate limiting on authentication and payment endpoints to prevent abuse
4. **Comprehensive Integration Tests** — Add end-to-end tests simulating full user journeys
5. **Production Deployment Config** — Add Kubernetes manifests, health checks, graceful shutdown, and monitoring hooks
6. **Admin APIs** — Add role-based access control and admin endpoints for user/centre/test management
7. **Payment Retries** — Implement exponential backoff for webhook retries and failed payments
8. **Audit Logging** — Add immutable audit trail for all financial transactions
9. **API Rate Limiting** — Implement sliding window rate limiting per user/IP
10. **OpenTelemetry Integration** — Add distributed tracing for monitoring in production

These improvements are practical and realistic extensions that could be implemented in follow-up iterations without fundamentally redesigning the system.

## 17. Troubleshooting

**Database connection failed:**
```bash
# Check PostgreSQL is running
docker compose ps

# Check credentials in .env
cat .env
```

**Port 8000 already in use:**
```bash
# Run on different port
uvicorn app.main:app --port 8001
```

**Tests failing:**
```bash
# Ensure pytest is installed
pip install pytest pytest-asyncio

# Run with verbose output for debugging
pytest -v --tb=short
```

**Swagger UI not loading:**
```bash
# Ensure FastAPI is running correctly
curl http://localhost:8000/health
```

---

**Built with ❤️ for EVE Healthcare**

*This service demonstrates backend engineering best practices: clean architecture, comprehensive testing, database design, error handling, and production-oriented code.*
