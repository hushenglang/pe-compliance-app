from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
import logging
import markdown2  # type: ignore

from service.sfc_news_service import SfcNewsService
from service.hkma_news_service import HkmaNewsService
from service.sec_news_service import SecNewsService
from service.hkex_news_service import HkexNewsService
from service.compliance_news_service import ComplianceNewsService
from config.database import get_db
from util.logging_util import get_logger
from schemas.response_schemas import ComplianceNewsResponse, ComplianceNewsStatisticsResponse

# Initialize logger
logger = get_logger(__name__, level=logging.INFO, format_style="detailed")

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
    Fetch and persist today's news from SFC, HKMA, SEC, and HKEX sources and return all persisted news.
    
    - **llm_enabled**: Whether to enable LLM processing for content summarization
    - **user**: User who initiated the fetch operation
    
    Returns:
        List of persisted ComplianceNews objects from SFC, HKMA, SEC, and HKEX sources
    """
    logger.info(f"[POST /today] Starting fetch and persist today's news request - llm_enabled: {llm_enabled}, user: {user}")
    
    # Create service instances with database session
    sfc_news_service = SfcNewsService(db)
    hkma_news_service = HkmaNewsService(db)
    sec_news_service = SecNewsService(db)
    hkex_news_service = HkexNewsService(db)
    
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
    
    try:
        # Fetch and persist today's HKEX news
        logger.info("[POST /today] Calling HkexNewsService.fetch_and_persist_today_news")
        hkex_news = await hkex_news_service.fetch_and_persist_today_news(
            creation_user=user,
            llm_enabled=llm_enabled
        )
        all_persisted_news.extend(hkex_news)
        logger.info(f"[POST /today] Successfully fetched and persisted {len(hkex_news)} HKEX news items")
        
    except Exception as e:
        logger.error(f"[POST /today] Failed to fetch and persist HKEX news: {str(e)}")
        errors.append(f"HKEX: {str(e)}")
    
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
    Fetch and persist news from SFC, HKMA, SEC, and HKEX sources for a specific date and return all persisted news.
    
    - **date**: Date in format "yyyy-mm-dd" (e.g., "2024-12-15")
    - **llm_enabled**: Whether to enable LLM processing for content summarization
    - **user**: User who initiated the fetch operation
    
    Returns:
        List of persisted ComplianceNews objects from SFC, HKMA, SEC, and HKEX sources
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
    hkex_news_service = HkexNewsService(db)
    
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
    
    try:
        # Fetch and persist HKEX news for the specified date
        logger.info(f"[POST /date/{date}] Calling HkexNewsService.fetch_and_persist_news_by_date")
        hkex_news = await hkex_news_service.fetch_and_persist_news_by_date(
            date=date,
            creation_user=user,
            llm_enabled=llm_enabled
        )
        all_persisted_news.extend(hkex_news)
        logger.info(f"[POST /date/{date}] Successfully fetched and persisted {len(hkex_news)} HKEX news items")
        
    except Exception as e:
        logger.error(f"[POST /date/{date}] Failed to fetch and persist HKEX news: {str(e)}")
        errors.append(f"HKEX: {str(e)}")
    
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
    Get news from SFC, HKMA, SEC, and HKEX sources from the last 7 days.
    
    Returns:
        List of ComplianceNews objects from the last 7 days from all sources
    """
    logger.info("[GET /last7days] Starting request to get last 7 days news")
    
    compliance_news_service = ComplianceNewsService(db)
    
    try:
        logger.info("[GET /last7days] Calling ComplianceNewsService.get_news_last_7days")
        all_news_items = compliance_news_service.get_news_last_7days()
        logger.info(f"[GET /last7days] Successfully retrieved {len(all_news_items)} total news items from last 7 days")
        return all_news_items
        
    except Exception as e:
        logger.error(f"[GET /last7days] Failed to fetch news: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {str(e)}")

@router.get("/html-email/last7days", response_model=str)
async def get_last_7days_news_html_email(db: Session = Depends(get_db)):
    """
    Get news from SFC, HKMA, SEC, and HKEX sources from the last 7 days, convert to html email format.
    
    Returns:
        HTML formatted string for email containing news from all sources
    """
    logger.info("[GET /html-email/last7days] Starting request to get last 7 days news")
    
    compliance_news_service = ComplianceNewsService(db)
    sfc_news_service = SfcNewsService(db)  # Still needed for URL conversion
    
    try:
        logger.info("[GET /html-email/last7days] Calling ComplianceNewsService.get_news_last_7days")
        all_news_items = compliance_news_service.get_news_last_7days()
        
        html_email = ""
        for news_item in all_news_items:
            source = news_item.source
            issue_date = news_item.issue_date.strftime("%Y-%m-%d") if news_item.issue_date else "N/A"
            title = news_item.title
            
            # Handle SFC URL conversion specially
            if source == "SFC" and news_item.content_url:
                content_url = sfc_news_service.convert_api_url_to_news_orignal_url(str(news_item.content_url))
            else:
                content_url = str(news_item.content_url) if news_item.content_url else ""
            
            llm_summary = news_item.llm_summary
            html_summary = markdown2.markdown(llm_summary, extras=['tables', 'fenced-code-blocks', 'toc']).replace('\n', '') if llm_summary else ""
            html_email += f"""<p><h2>{source} - <a href="{content_url}">{title}</a></h2></p><p>{issue_date}</p><p>{html_summary}</p>""" + "<br><br>"
        
        logger.info(f"[GET /html-email/last7days] Successfully processed {len(all_news_items)} total news items")
        logger.info("[GET /html-email/last7days] Successfully generated HTML email")
        return html_email
        
    except Exception as e:
        logger.error(f"[GET /html-email/last7days] Failed to process news: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch and process news: {str(e)}")

@router.get("/statistics", response_model=List[ComplianceNewsStatisticsResponse])
async def get_news_statistics(db: Session = Depends(get_db)):
    """
    Get statistics for news by source and status.
    
    Returns:
        List of ComplianceNewsStatisticsResponse objects containing source, status, and record count.
    """
    logger.info("[GET /statistics] Starting request to get news statistics")
    
    compliance_news_service = ComplianceNewsService(db)
    
    try:
        logger.info("[GET /statistics] Calling ComplianceNewsService.get_statistics_by_source_and_status")
        statistics = compliance_news_service.get_statistics_by_source_and_status()
        logger.info(f"[GET /statistics] Successfully retrieved {len(statistics)} statistics records")
        return statistics
        
    except Exception as e:
        logger.error(f"[GET /statistics] Failed to fetch statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch statistics: {str(e)}")