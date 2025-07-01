from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session
import logging
import markdown2  # type: ignore

from service.sfc_news_service import SfcNewsService
from config.database import get_db
from util.logging_util import get_logger

# Initialize logger
logger = get_logger(__name__, level=logging.INFO, format_style="detailed")

# Create a Pydantic model for the response
class ComplianceNewsResponse(BaseModel):
    id: int
    source: str
    issue_date: Optional[datetime] = None
    title: str
    content: Optional[str] = None
    content_url: Optional[str] = None
    llm_summary: Optional[str] = None
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
        persisted_news = await sfc_news_service.fetch_and_persist_today_news(
            creation_user=user,
            llm_enabled=llm_enabled
        )
        
        logger.info(f"[POST /today] Successfully fetched and persisted {len(persisted_news)} news items")
        return persisted_news
        
    except Exception as e:
        logger.error(f"[POST /today] Failed to fetch and persist news: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch and persist news: {str(e)}")

@router.post("/date/{date}", response_model=List[ComplianceNewsResponse])
async def fetch_and_persist_news_by_date(
    date: str,
    llm_enabled: bool = True,
    user: str = "api",
    db: Session = Depends(get_db)
):
    """
    Fetch and persist SFC news for a specific date and return all persisted news.
    
    - **date**: Date in format "yyyy-mm-dd" (e.g., "2024-12-15")
    - **llm_enabled**: Whether to enable LLM processing for content summarization
    - **user**: User who initiated the fetch operation
    
    Returns:
        List of persisted ComplianceNews objects
    """
    logger.info(f"[POST /date/{date}] Starting fetch and persist news by date request - date: {date}, llm_enabled: {llm_enabled}, user: {user}")
    
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        logger.error(f"[POST /date/{date}] Invalid date format: {date}")
        raise HTTPException(status_code=400, detail="Invalid date format. Please use yyyy-mm-dd format (e.g., 2024-12-15)")
    
    # Create a service instance with database session
    sfc_news_service = SfcNewsService(db)
    
    try:
        # Fetch and persist news for the specified date
        logger.info(f"[POST /date/{date}] Calling SfcNewsService.fetch_and_persist_news_by_date")
        persisted_news = await sfc_news_service.fetch_and_persist_news_by_date(
            date=date,
            creation_user=user,
            llm_enabled=llm_enabled
        )
        
        logger.info(f"[POST /date/{date}] Successfully fetched and persisted {len(persisted_news)} news items")
        return persisted_news
        
    except Exception as e:
        logger.error(f"[POST /date/{date}] Failed to fetch and persist news: {str(e)}")
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

@router.get("/html-email/last7days", response_model=str)
async def get_last_7days_news_html_email(db: Session = Depends(get_db)):
    """
    Get SFC news from the last 7 days, convert to html email format.
    """
    logger.info("[GET /html-email/last7days] Starting request to get last 7 days news")
    
    sfc_news_service = SfcNewsService(db)
    
    try:
        logger.info("[GET /html-email/last7days] Calling SfcNewsService.get_news_last_7days")
        sfc_news_items = sfc_news_service.get_news_last_7days()
        html_email = ""
        for sfc_news_item in sfc_news_items:
            source = sfc_news_item.source
            issue_date = sfc_news_item.issue_date.strftime("%Y-%m-%d")
            title = sfc_news_item.title
            content_url = sfc_news_service.convert_api_url_to_news_orignal_url(str(sfc_news_item.content_url)) if sfc_news_item.content_url else ""
            llm_summary = sfc_news_item.llm_summary
            html_summary = markdown2.markdown(llm_summary, extras=['tables', 'fenced-code-blocks', 'toc']).replace('\n', '') if llm_summary else ""
            html_email = html_email + f"""<p><h2>{source} - <a href="{content_url}">{title}</a></h2></p><p>{issue_date}</p><p>{html_summary}</p>""" + "<br><br>"

        logger.info(f"[GET /html-email/last7days] Successfully retrieved {len(sfc_news_items)} news items from last 7 days")
        return html_email
        
    except Exception as e:
        logger.error(f"[GET /html-email/last7days] Failed to fetch news: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {str(e)}")