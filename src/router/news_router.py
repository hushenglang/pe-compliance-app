from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import List, Dict
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session
import logging

from service.sfc_news_service import SfcNewsService
from model.compliance_news import ComplianceNews
from config.database import get_db
from util.logging_util import get_logger

# Initialize logger
logger = get_logger(__name__, level=logging.INFO, format_style="detailed")

# Create a Pydantic model for the response
class ComplianceNewsResponse(BaseModel):
    id: int
    source: str
    issue_date: datetime = None
    title: str
    content: str = None
    content_url: str = None
    llm_summary: str = None
    creation_date: datetime
    creation_user: str

    class Config:
        from_attributes = True

# Create the router
router = APIRouter(
    prefix="/api/news",
    tags=["news"],
    responses={404: {"description": "Not found"}},
)

@router.post("/today", response_model=List[ComplianceNewsResponse])
async def fetch_and_persist_today_news(
    llm_enabled: bool = True,
    user: str = "api",
    db: Session = Depends(get_db)
):
    """
    Fetch and persist today's SFC news and return all persisted news.
    
    - **llm_enabled**: Whether to enable LLM processing for content summarization
    - **user**: User who initiated the fetch operation
    
    Returns:
        List of persisted ComplianceNews objects
    """
    logger.info(f"[POST /today] Starting fetch and persist today's news request - llm_enabled: {llm_enabled}, user: {user}")
    
    # Create a service instance with database session
    sfc_news_service = SfcNewsService(db)
    
    try:
        # Fetch and persist today's news
        logger.info("[POST /today] Calling SfcNewsService.fetch_and_persist_today_news")
        persisted_news = sfc_news_service.fetch_and_persist_today_news(
            creation_user=user,
            llm_enabled=llm_enabled
        )
        
        logger.info(f"[POST /today] Successfully fetched and persisted {len(persisted_news)} news items")
        return persisted_news
        
    except Exception as e:
        logger.error(f"[POST /today] Failed to fetch and persist news: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch and persist news: {str(e)}")

@router.get("/last7days", response_model=List[ComplianceNewsResponse])
async def get_last_7days_news(db: Session = Depends(get_db)):
    """
    Get SFC news from the last 7 days.
    """
    logger.info("[GET /last7days] Starting request to get last 7 days news")
    
    sfc_news_service = SfcNewsService(db)
    
    try:
        logger.info("[GET /last7days] Calling SfcNewsService.get_news_last_7days")
        news_items = sfc_news_service.get_news_last_7days()
        
        logger.info(f"[GET /last7days] Successfully retrieved {len(news_items)} news items from last 7 days")
        return news_items
        
    except Exception as e:
        logger.error(f"[GET /last7days] Failed to fetch news: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {str(e)}")
