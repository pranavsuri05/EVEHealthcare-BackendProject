from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import DiagnosticCentre
from app.schemas.schemas import (
    DiagnosticCentreRequest,
    DiagnosticCentreResponse,
    PaginatedResponse,
)
from app.core.exceptions import ResourceNotFound, ValidationError

router = APIRouter(prefix="/centres", tags=["centres"])


@router.post(
    "", response_model=DiagnosticCentreResponse, status_code=status.HTTP_201_CREATED
)
def create_centre(request: DiagnosticCentreRequest, db: Session = Depends(get_db)):
    """Create a new diagnostic centre"""
    centre = DiagnosticCentre(name=request.name, location=request.location)
    db.add(centre)
    db.commit()
    db.refresh(centre)
    return centre


@router.get("", response_model=PaginatedResponse)
def list_centres(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """List all diagnostic centres with pagination"""
    query = db.query(DiagnosticCentre)
    total = query.count()
    centres = query.offset(skip).limit(limit).all()
    items = [DiagnosticCentreResponse.model_validate(c) for c in centres]
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/{centre_id}", response_model=DiagnosticCentreResponse)
def get_centre(centre_id: int, db: Session = Depends(get_db)):
    """Get a specific diagnostic centre by ID"""
    centre = db.query(DiagnosticCentre).filter(DiagnosticCentre.id == centre_id).first()
    if not centre:
        raise ResourceNotFound("Diagnostic centre", str(centre_id))
    return centre
