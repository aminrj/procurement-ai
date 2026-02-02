"""
FastAPI Application
Main API server for Procurement AI
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import time

from procurement_ai import __version__
from procurement_ai.api.routes import tenders
from procurement_ai.api.schemas import HealthResponse
from procurement_ai.api.dependencies import get_db, get_config

# Create FastAPI app
app = FastAPI(
    title="Procurement AI API",
    description="AI-powered tender analysis and bid generation",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware (configure for your needs)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Include routers
app.include_router(tenders.router)


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["health"])
def health_check():
    """
    Health check endpoint
    
    Returns status of API, database, and LLM service.
    """
    db_status = "unknown"
    llm_status = "unknown"

    # Check database
    try:
        db = get_db()
        with db.get_session() as session:
            session.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)[:50]}"

    # Check LLM (basic check - config exists)
    try:
        config = get_config()
        llm_status = f"configured: {config.LLM_BASE_URL}"
    except Exception as e:
        llm_status = f"error: {str(e)[:50]}"

    overall_status = "healthy" if db_status == "healthy" else "degraded"

    return HealthResponse(
        status=overall_status,
        version=__version__,
        database=db_status,
        llm=llm_status,
    )


# Root endpoint
@app.get("/", tags=["root"])
def read_root():
    """API root - redirects to documentation"""
    return {
        "message": "Procurement AI API",
        "version": __version__,
        "docs": "/docs",
        "health": "/health",
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc),
            "path": str(request.url),
        },
    )


# For running with uvicorn directly
def main():
    """Run the API server"""
    import uvicorn

    uvicorn.run(
        "procurement_ai.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
