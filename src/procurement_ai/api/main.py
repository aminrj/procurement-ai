"""
FastAPI Application
Main API server for Procurement AI
"""
import logging
import time

from fastapi import Depends, FastAPI, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from procurement_ai import __version__
from procurement_ai.api.routes import tenders, web
from procurement_ai.api.schemas import HealthResponse
from procurement_ai.api.dependencies import get_db, get_config
from procurement_ai.config import Config
from procurement_ai.storage import DatabaseManager

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Procurement AI API",
    description="AI-powered tender analysis and bid generation",
    version=__version__,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS middleware (configure for your needs)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_config().CORS_ORIGINS,
    allow_credentials=False,
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
app.include_router(web.router)  # Web UI (HTMX)
app.include_router(tenders.router)  # REST API


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["health"])
def health_check(
    db: DatabaseManager = Depends(get_db),
    config: Config = Depends(get_config),
):
    """
    Health check endpoint
    
    Returns status of API, database, and LLM service.
    """
    db_status = "unknown"
    llm_status = "unknown"

    # Check database
    try:
        with db.get_session() as session:
            session.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)[:50]}"

    # Check LLM (basic check - config exists)
    try:
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


# Root endpoint - redirect to web UI
@app.get("/", tags=["root"])
def read_root():
    """Redirect to web dashboard"""
    return RedirectResponse(url="/web/")


@app.get("/api", tags=["root"])
def api_root():
    """API information"""
    return {
        "message": "Procurement AI API",
        "version": __version__,
        "docs": "/api/docs",
        "health": "/health",
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler"""
    logger.exception("Unhandled exception for %s", request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error. Please contact support.",
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
