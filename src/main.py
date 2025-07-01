from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router.news_router import router as news_router
from router.health_router import router as health_router
from util.logging_util import setup_logging, get_logger
from config.settings import settings
import uvicorn

# Configure logging based on environment
log_level_mapping = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50
}

log_level = log_level_mapping.get(settings.log_level, 20)  # Default to INFO
format_style = "json" if settings.is_production else "detailed"
enable_json_logging = settings.is_production
log_to_file = settings.log_to_file
log_file_path = settings.log_file_path

# Setup logging
setup_logging(
    level=log_level,
    format_style=format_style,
    enable_json_logging=enable_json_logging,
    log_to_file=log_to_file,
    log_file_path=log_file_path if log_to_file else None
)
logger = get_logger(__name__)

# Log startup information
logger.info(f"Starting PE Compliance App - Environment: {settings.app_env}")
logger.info(f"Log Level: {settings.log_level}, JSON Logging: {enable_json_logging}")
if log_to_file:
    logger.info(f"File logging enabled - Path: {log_file_path}")
else:
    logger.info("File logging disabled - Logging to console only")

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
