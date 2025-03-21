from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Add the parent directory to sys.path to fix import issues
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.api import endpoints
from src.database import models, database

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

# Health check endpoint for Azure
@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
