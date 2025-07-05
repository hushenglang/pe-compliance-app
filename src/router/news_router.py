from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session
import logging
import markdown2  # type: ignore

from service.sfc_news_service import SfcNewsService
from service.hkma_news_service import HkmaNewsService
from service.sec_news_service import SecNewsService
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
    Fetch and persist today's news from SFC, HKMA, and SEC sources and return all persisted news.
    
    - **llm_enabled**: Whether to enable LLM processing for content summarization
    - **user**: User who initiated the fetch operation
    
    Returns:
        List of persisted ComplianceNews objects from SFC, HKMA, and SEC sources
    """
    logger.info(f"[POST /today] Starting fetch and persist today's news request - llm_enabled: {llm_enabled}, user: {user}")
    
    # Create service instances with database session
    sfc_news_service = SfcNewsService(db)
    hkma_news_service = HkmaNewsService(db)
    sec_news_service = SecNewsService(db)
    
    all_persisted_news = []
    errors = []
    
    try:
        # Fetch and persist today's SFC news
        logger.info("[POST /today] Calling SfcNewsService.fetch_and_persist_today_news")
        sfc_news = await sfc_news_service.fetch_and_persist_today_news(
            creation_user=user,
            llm_enabled=llm_enabled
        )
        all_persisted_news.extend(sfc_news)
        logger.info(f"[POST /today] Successfully fetched and persisted {len(sfc_news)} SFC news items")
        
    except Exception as e:
        logger.error(f"[POST /today] Failed to fetch and persist SFC news: {str(e)}")
        errors.append(f"SFC: {str(e)}")
    
    try:
        # Fetch and persist today's HKMA news
        logger.info("[POST /today] Calling HkmaNewsService.fetch_and_persist_today_news")
        hkma_news = await hkma_news_service.fetch_and_persist_today_news(
            creation_user=user,
            llm_enabled=llm_enabled
        )
        all_persisted_news.extend(hkma_news)
        logger.info(f"[POST /today] Successfully fetched and persisted {len(hkma_news)} HKMA news items")
        
    except Exception as e:
        logger.error(f"[POST /today] Failed to fetch and persist HKMA news: {str(e)}")
        errors.append(f"HKMA: {str(e)}")
    
    try:
        # Fetch and persist today's SEC news
        logger.info("[POST /today] Calling SecNewsService.fetch_and_persist_today_news")
        sec_news = await sec_news_service.fetch_and_persist_today_news(
            creation_user=user,
            llm_enabled=llm_enabled
        )
        all_persisted_news.extend(sec_news)
        logger.info(f"[POST /today] Successfully fetched and persisted {len(sec_news)} SEC news items")
        
    except Exception as e:
        logger.error(f"[POST /today] Failed to fetch and persist SEC news: {str(e)}")
        errors.append(f"SEC: {str(e)}")
    
    # If all services failed, raise an error
    if errors and not all_persisted_news:
        error_message = "; ".join(errors)
        logger.error(f"[POST /today] All services failed: {error_message}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch and persist news: {error_message}")
    
    # Log partial failures
    if errors:
        logger.warning(f"[POST /today] Partial failures occurred: {'; '.join(errors)}")
    
    logger.info(f"[POST /today] Successfully fetched and persisted {len(all_persisted_news)} total news items")
    return all_persisted_news

@router.post("/date/{date}", response_model=List[ComplianceNewsResponse])
async def fetch_and_persist_news_by_date(
    date: str,
    llm_enabled: bool = True,
    user: str = "api",
    db: Session = Depends(get_db)
):
    """
    Fetch and persist news from SFC, HKMA, and SEC sources for a specific date and return all persisted news.
    
    - **date**: Date in format "yyyy-mm-dd" (e.g., "2024-12-15")
    - **llm_enabled**: Whether to enable LLM processing for content summarization
    - **user**: User who initiated the fetch operation
    
    Returns:
        List of persisted ComplianceNews objects from SFC, HKMA, and SEC sources
    """
    logger.info(f"[POST /date/{date}] Starting fetch and persist news by date request - date: {date}, llm_enabled: {llm_enabled}, user: {user}")
    
    # Validate date format
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        logger.error(f"[POST /date/{date}] Invalid date format: {date}")
        raise HTTPException(status_code=400, detail="Invalid date format. Please use yyyy-mm-dd format (e.g., 2024-12-15)")
    
    # Create service instances with database session
    sfc_news_service = SfcNewsService(db)
    hkma_news_service = HkmaNewsService(db)
    sec_news_service = SecNewsService(db)
    
    all_persisted_news = []
    errors = []
    
    try:
        # Fetch and persist SFC news for the specified date
        logger.info(f"[POST /date/{date}] Calling SfcNewsService.fetch_and_persist_news_by_date")
        sfc_news = await sfc_news_service.fetch_and_persist_news_by_date(
            date=date,
            creation_user=user,
            llm_enabled=llm_enabled
        )
        all_persisted_news.extend(sfc_news)
        logger.info(f"[POST /date/{date}] Successfully fetched and persisted {len(sfc_news)} SFC news items")
        
    except Exception as e:
        logger.error(f"[POST /date/{date}] Failed to fetch and persist SFC news: {str(e)}")
        errors.append(f"SFC: {str(e)}")
    
    try:
        # Fetch and persist HKMA news for the specified date
        logger.info(f"[POST /date/{date}] Calling HkmaNewsService.fetch_and_persist_news_by_date")
        hkma_news = await hkma_news_service.fetch_and_persist_news_by_date(
            date=date,
            creation_user=user,
            llm_enabled=llm_enabled
        )
        all_persisted_news.extend(hkma_news)
        logger.info(f"[POST /date/{date}] Successfully fetched and persisted {len(hkma_news)} HKMA news items")
        
    except Exception as e:
        logger.error(f"[POST /date/{date}] Failed to fetch and persist HKMA news: {str(e)}")
        errors.append(f"HKMA: {str(e)}")
    
    try:
        # Fetch and persist SEC news for the specified date
        logger.info(f"[POST /date/{date}] Calling SecNewsService.fetch_and_persist_news_by_date")
        sec_news = await sec_news_service.fetch_and_persist_news_by_date(
            date=date,
            creation_user=user,
            llm_enabled=llm_enabled
        )
        all_persisted_news.extend(sec_news)
        logger.info(f"[POST /date/{date}] Successfully fetched and persisted {len(sec_news)} SEC news items")
        
    except Exception as e:
        logger.error(f"[POST /date/{date}] Failed to fetch and persist SEC news: {str(e)}")
        errors.append(f"SEC: {str(e)}")
    
    # If all services failed, raise an error
    if errors and not all_persisted_news:
        error_message = "; ".join(errors)
        logger.error(f"[POST /date/{date}] All services failed: {error_message}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch and persist news: {error_message}")
    
    # Log partial failures
    if errors:
        logger.warning(f"[POST /date/{date}] Partial failures occurred: {'; '.join(errors)}")
    
    logger.info(f"[POST /date/{date}] Successfully fetched and persisted {len(all_persisted_news)} total news items")
    return all_persisted_news

@router.get("/last7days", response_model=List[ComplianceNewsResponse])
async def get_last_7days_news(db: Session = Depends(get_db)):
    """
    Get news from SFC, HKMA, and SEC sources from the last 7 days.
    
    Returns:
        List of ComplianceNews objects from the last 7 days from all sources
    """
    logger.info("[GET /last7days] Starting request to get last 7 days news")
    
    sfc_news_service = SfcNewsService(db)
    hkma_news_service = HkmaNewsService(db)
    sec_news_service = SecNewsService(db)
    
    all_news_items = []
    errors = []
    
    try:
        logger.info("[GET /last7days] Calling SfcNewsService.get_news_last_7days")
        sfc_news_items = sfc_news_service.get_news_last_7days()
        all_news_items.extend(sfc_news_items)
        logger.info(f"[GET /last7days] Successfully retrieved {len(sfc_news_items)} SFC news items from last 7 days")
        
    except Exception as e:
        logger.error(f"[GET /last7days] Failed to fetch SFC news: {str(e)}")
        errors.append(f"SFC: {str(e)}")
    
    try:
        logger.info("[GET /last7days] Calling HkmaNewsService.get_news_last_7days")
        hkma_news_items = hkma_news_service.get_news_last_7days()
        all_news_items.extend(hkma_news_items)
        logger.info(f"[GET /last7days] Successfully retrieved {len(hkma_news_items)} HKMA news items from last 7 days")
        
    except Exception as e:
        logger.error(f"[GET /last7days] Failed to fetch HKMA news: {str(e)}")
        errors.append(f"HKMA: {str(e)}")
    
    try:
        logger.info("[GET /last7days] Calling SecNewsService.get_news_last_7days")
        sec_news_items = sec_news_service.get_news_last_7days()
        all_news_items.extend(sec_news_items)
        logger.info(f"[GET /last7days] Successfully retrieved {len(sec_news_items)} SEC news items from last 7 days")
        
    except Exception as e:
        logger.error(f"[GET /last7days] Failed to fetch SEC news: {str(e)}")
        errors.append(f"SEC: {str(e)}")
    
    # If all services failed, raise an error
    if errors and not all_news_items:
        error_message = "; ".join(errors)
        logger.error(f"[GET /last7days] All services failed: {error_message}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {error_message}")
    
    # Log partial failures
    if errors:
        logger.warning(f"[GET /last7days] Partial failures occurred: {'; '.join(errors)}")
    
    logger.info(f"[GET /last7days] Successfully retrieved {len(all_news_items)} total news items from last 7 days")
    return all_news_items

@router.get("/html-email/last7days", response_model=str)
async def get_last_7days_news_html_email(db: Session = Depends(get_db)):
    """
    Get news from SFC, HKMA, and SEC sources from the last 7 days, convert to html email format.
    
    Returns:
        HTML formatted string for email containing news from all sources
    """
    logger.info("[GET /html-email/last7days] Starting request to get last 7 days news")
    
    sfc_news_service = SfcNewsService(db)
    hkma_news_service = HkmaNewsService(db)
    sec_news_service = SecNewsService(db)
    
    html_email = ""
    errors = []
    
    try:
        logger.info("[GET /html-email/last7days] Calling SfcNewsService.get_news_last_7days")
        sfc_news_items = sfc_news_service.get_news_last_7days()
        
        for sfc_news_item in sfc_news_items:
            source = sfc_news_item.source
            issue_date = sfc_news_item.issue_date.strftime("%Y-%m-%d") if sfc_news_item.issue_date else "N/A"
            title = sfc_news_item.title
            content_url = sfc_news_service.convert_api_url_to_news_orignal_url(str(sfc_news_item.content_url)) if sfc_news_item.content_url else ""
            llm_summary = sfc_news_item.llm_summary
            html_summary = markdown2.markdown(llm_summary, extras=['tables', 'fenced-code-blocks', 'toc']).replace('\n', '') if llm_summary else ""
            html_email += f"""<p><h2>{source} - <a href="{content_url}">{title}</a></h2></p><p>{issue_date}</p><p>{html_summary}</p>""" + "<br><br>"
        
        logger.info(f"[GET /html-email/last7days] Successfully processed {len(sfc_news_items)} SFC news items")
        
    except Exception as e:
        logger.error(f"[GET /html-email/last7days] Failed to process SFC news: {str(e)}")
        errors.append(f"SFC: {str(e)}")
    
    try:
        logger.info("[GET /html-email/last7days] Calling HkmaNewsService.get_news_last_7days")
        hkma_news_items = hkma_news_service.get_news_last_7days()
        
        for hkma_news_item in hkma_news_items:
            source = hkma_news_item.source
            issue_date = hkma_news_item.issue_date.strftime("%Y-%m-%d") if hkma_news_item.issue_date else "N/A"
            title = hkma_news_item.title
            content_url = str(hkma_news_item.content_url) if hkma_news_item.content_url else ""
            llm_summary = hkma_news_item.llm_summary
            html_summary = markdown2.markdown(llm_summary, extras=['tables', 'fenced-code-blocks', 'toc']).replace('\n', '') if llm_summary else ""
            html_email += f"""<p><h2>{source} - <a href="{content_url}">{title}</a></h2></p><p>{issue_date}</p><p>{html_summary}</p>""" + "<br><br>"
        
        logger.info(f"[GET /html-email/last7days] Successfully processed {len(hkma_news_items)} HKMA news items")
        
    except Exception as e:
        logger.error(f"[GET /html-email/last7days] Failed to process HKMA news: {str(e)}")
        errors.append(f"HKMA: {str(e)}")
    
    try:
        logger.info("[GET /html-email/last7days] Calling SecNewsService.get_news_last_7days")
        sec_news_items = sec_news_service.get_news_last_7days()
        
        for sec_news_item in sec_news_items:
            source = sec_news_item.source
            issue_date = sec_news_item.issue_date.strftime("%Y-%m-%d") if sec_news_item.issue_date else "N/A"
            title = sec_news_item.title
            content_url = str(sec_news_item.content_url) if sec_news_item.content_url else ""
            llm_summary = sec_news_item.llm_summary
            html_summary = markdown2.markdown(llm_summary, extras=['tables', 'fenced-code-blocks', 'toc']).replace('\n', '') if llm_summary else ""
            html_email += f"""<p><h2>{source} - <a href="{content_url}">{title}</a></h2></p><p>{issue_date}</p><p>{html_summary}</p>""" + "<br><br>"
        
        logger.info(f"[GET /html-email/last7days] Successfully processed {len(sec_news_items)} SEC news items")
        
    except Exception as e:
        logger.error(f"[GET /html-email/last7days] Failed to process SEC news: {str(e)}")
        errors.append(f"SEC: {str(e)}")
    
    # If all services failed, raise an error
    if errors and not html_email:
        error_message = "; ".join(errors)
        logger.error(f"[GET /html-email/last7days] All services failed: {error_message}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {error_message}")
    
    # Log partial failures
    if errors:
        logger.warning(f"[GET /html-email/last7days] Partial failures occurred: {'; '.join(errors)}")
    
    logger.info(f"[GET /html-email/last7days] Successfully generated HTML email")
    return html_email