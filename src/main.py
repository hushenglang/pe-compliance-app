from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from router.news_router import router as news_router
from router.health_router import router as health_router
from util.logging_util import setup_logging, get_logger
import uvicorn

# Setup logging
setup_logging()
logger = get_logger(__name__)


# Create FastAPI app
app = FastAPI(
    title="Financial Compliance News API",
    description="API for fetching and managing financial compliance news",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this more restrictively in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(news_router)
app.include_router(health_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
