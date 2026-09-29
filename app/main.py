from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.database import engine
from app.db.models import Base
from app.api import auth, centres, tests, bookings, payments

# Setup logging
setup_logging()

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Diagnostic test booking service with simulated payments",
    version="1.0.0",
)

# Include routers
app.include_router(auth.router)
app.include_router(centres.router)
app.include_router(tests.router)
app.include_router(bookings.router)
app.include_router(payments.router)


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "app": settings.app_name}


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
