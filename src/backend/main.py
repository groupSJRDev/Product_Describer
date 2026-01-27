"""FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import CORS_ORIGINS
from backend.api.auth import router as auth_router
from backend.api.products import router as products_router
from backend.api.analysis import router as analysis_router

# Create FastAPI app
app = FastAPI(
    title="Product Describer API",
    description="Backend API for Product Describer - Analyze products and generate images",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Product Describer API",
        "version": "1.0.0",
        "docs": "/api/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
