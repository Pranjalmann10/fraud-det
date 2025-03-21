from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from . import endpoints
from ..database import models, database

# Create FastAPI app
app = FastAPI(
    title="Fraud Detection, Alert, and Monitoring (FDAM) System",
    description="API for detecting, reporting, and monitoring fraudulent transactions",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(endpoints.router, prefix="/api", tags=["fraud"])

# Create database tables on startup
@app.on_event("startup")
def startup_db_client():
    models.Base.metadata.create_all(bind=database.engine)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Fraud Detection, Alert, and Monitoring (FDAM) System",
        "docs": "/docs",
        "api": "/api"
    }
