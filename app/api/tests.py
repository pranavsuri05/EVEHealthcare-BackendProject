from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.database import get_db
from app.db.models import DiagnosticTest, CentreTest, DiagnosticCentre
from app.schemas.schemas import (
    DiagnosticTestRequest,
    DiagnosticTestResponse,
    CentreTestRequest,
    CentreTestWithRelationsResponse,
    PaginatedResponse,
)
from app.core.exceptions import ResourceNotFound, ConflictError, ValidationError

router = APIRouter(prefix="/tests", tags=["tests"])


@router.post("", response_model=DiagnosticTestResponse, status_code=status.HTTP_201_CREATED)
def create_test(request: DiagnosticTestRequest, db: Session = Depends(get_db)):
    """Create a new diagnostic test"""
    test = DiagnosticTest(name=request.name, description=request.description)
    db.add(test)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError(f"Test with name '{request.name}' already exists")
    db.refresh(test)
    return test


@router.get("", response_model=PaginatedResponse)
def list_tests(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """List all diagnostic tests with pagination"""
    query = db.query(DiagnosticTest)
    total = query.count()
    tests = query.offset(skip).limit(limit).all()
    return PaginatedResponse(items=tests, total=total, skip=skip, limit=limit)


@router.get("/{test_id}", response_model=DiagnosticTestResponse)
def get_test(test_id: int, db: Session = Depends(get_db)):
    """Get a specific diagnostic test by ID"""
    test = db.query(DiagnosticTest).filter(DiagnosticTest.id == test_id).first()
    if not test:
        raise ResourceNotFound("Diagnostic test", str(test_id))
    return test


@router.post(
    "/{test_id}/centres",
    response_model=CentreTestWithRelationsResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_test_to_centre(
    test_id: int, request: CentreTestRequest, db: Session = Depends(get_db)
):
    """Add a test to a centre with pricing"""
    # Verify test exists
    test = db.query(DiagnosticTest).filter(DiagnosticTest.id == test_id).first()
    if not test:
        raise ResourceNotFound("Diagnostic test", str(test_id))

    # Verify centre exists
    centre = (
        db.query(DiagnosticCentre)
        .filter(DiagnosticCentre.id == request.centre_id)
        .first()
    )
    if not centre:
        raise ResourceNotFound("Diagnostic centre", str(request.centre_id))

    # Validate price
    if request.price <= 0:
        raise ValidationError("Price must be greater than 0")

    # Create centre_test
    centre_test = CentreTest(
        centre_id=request.centre_id,
        test_id=test_id,
        price=request.price,
        available=request.available,
    )

    db.add(centre_test)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError(
            f"Test {test_id} is already offered at centre {request.centre_id}"
        )

    db.refresh(centre_test)
    return centre_test


@router.get(
    "/centre/{centre_id}/tests", response_model=PaginatedResponse
)
def list_centre_tests(
    centre_id: int,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """List all tests offered by a centre"""
    # Verify centre exists
    centre = (
        db.query(DiagnosticCentre)
        .filter(DiagnosticCentre.id == centre_id)
        .first()
    )
    if not centre:
        raise ResourceNotFound("Diagnostic centre", str(centre_id))

    query = db.query(CentreTest).filter(CentreTest.centre_id == centre_id)
    total = query.count()
    centre_tests = query.offset(skip).limit(limit).all()

    # Convert to response format
    items = [
        {
            "id": ct.id,
            "centre_id": ct.centre_id,
            "test_id": ct.test_id,
            "price": ct.price,
            "available": ct.available,
            "centre": ct.centre,
            "test": ct.test,
            "created_at": ct.created_at,
            "updated_at": ct.updated_at,
        }
        for ct in centre_tests
    ]

    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)
