from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
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
from schemas.response_schemas import (
    ComplianceNewsResponse, 
    ComplianceNewsStatisticsResponse, 
    GroupedComplianceNewsResponse, 
    ComplianceNewsLightResponse, 
    UpdateStatusRequest, 
    UpdateStatusResponse,
    UpdateTitleAndSummaryRequest,
    UpdateTitleAndSummaryResponse
)

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
    Fetch and persist today's news, circular and consultation from SFC, HKMA, SEC, and HKEX sources and return all persisted news.
    
    - **llm_enabled**: Whether to enable LLM processing for content summarization
    - **user**: User who initiated the fetch operation
    
    Returns:
        List of persisted ComplianceNews objects from SFC (news + circular + consultation), HKMA, SEC, and HKEX sources
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
        
        # Fetch and persist today's SFC circular
        logger.info("[POST /today] Calling SfcNewsService.fetch_and_persist_today_circular")
        sfc_circular = await sfc_news_service.fetch_and_persist_today_circular(
            creation_user=user,
            llm_enabled=llm_enabled
        )
        all_persisted_news.extend(sfc_circular)
        logger.info(f"[POST /today] Successfully fetched and persisted {len(sfc_circular)} SFC circular items")
        
        # Fetch and persist today's SFC consultation
        logger.info("[POST /today] Calling SfcNewsService.fetch_and_persist_today_consultation")
        sfc_consultation = await sfc_news_service.fetch_and_persist_today_consultation(
            creation_user=user,
            llm_enabled=llm_enabled
        )
        all_persisted_news.extend(sfc_consultation)
        logger.info(f"[POST /today] Successfully fetched and persisted {len(sfc_consultation)} SFC consultation items")
        
    except Exception as e:
        logger.error(f"[POST /today] Failed to fetch and persist SFC news/circular/consultation: {str(e)}")
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
    Fetch and persist news, circular and consultation from SFC, HKMA, SEC, and HKEX sources for a specific date and return all persisted news.
    
    - **date**: Date in format "yyyy-mm-dd" (e.g., "2024-12-15")
    - **llm_enabled**: Whether to enable LLM processing for content summarization
    - **user**: User who initiated the fetch operation
    
    Returns:
        List of persisted ComplianceNews objects from SFC (news + circular + consultation), HKMA, SEC, and HKEX sources
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
        
        # Fetch and persist SFC circular for the specified date
        logger.info(f"[POST /date/{date}] Calling SfcNewsService.fetch_and_persist_circular_by_date")
        sfc_circular = await sfc_news_service.fetch_and_persist_circular_by_date(
            date=date,
            creation_user=user,
            llm_enabled=llm_enabled
        )
        all_persisted_news.extend(sfc_circular)
        logger.info(f"[POST /date/{date}] Successfully fetched and persisted {len(sfc_circular)} SFC circular items")
        
        # Fetch and persist SFC consultation for the specified date
        logger.info(f"[POST /date/{date}] Calling SfcNewsService.fetch_and_persist_consultation_by_date")
        sfc_consultation = await sfc_news_service.fetch_and_persist_consultation_by_date(
            date=date,
            creation_user=user,
            llm_enabled=llm_enabled
        )
        all_persisted_news.extend(sfc_consultation)
        logger.info(f"[POST /date/{date}] Successfully fetched and persisted {len(sfc_consultation)} SFC consultation items")
        
    except Exception as e:
        logger.error(f"[POST /date/{date}] Failed to fetch and persist SFC news/circular/consultation: {str(e)}")
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
            
            # Handle SFC URL conversion specially with safe fallback
            if source == "SFC" and news_item.content_url:
                try:
                    content_url = sfc_news_service.convert_api_url_to_news_orignal_url(str(news_item.content_url))
                except Exception as e:
                    logger.warning(f"[GET /html-email/last7days] URL convert failed for '{news_item.content_url}': {e}. Falling back to original URL.")
                    content_url = str(news_item.content_url)
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

@router.post("/html-email/by-ids", response_model=str)
async def get_news_html_email(
    news_id_list: List[int],
    db: Session = Depends(get_db)
):
    """
    Get news items by their IDs and convert to HTML email format.
    
    - **news_id_list**: List of news item IDs to include in the email
    
    Returns:
        HTML formatted string for email containing the specified news items
    """
    logger.info(f"[POST /html-email/by-ids] Starting request to get news HTML email - news_ids: {news_id_list}")
    
    if not news_id_list:
        logger.error("[POST /html-email/by-ids] Empty news ID list provided")
        raise HTTPException(status_code=400, detail="News ID list cannot be empty")
    
    compliance_news_service = ComplianceNewsService(db)
    sfc_news_service = SfcNewsService(db)  # Still needed for URL conversion
    
    try:
        logger.info(f"[POST /html-email/by-ids] Calling ComplianceNewsService.get_news_by_ids for {len(news_id_list)} IDs")
        news_items = compliance_news_service.get_news_by_ids(news_id_list)
        
        if not news_items:
            logger.warning(f"[POST /html-email/by-ids] No news items found for provided IDs: {news_id_list}")
            raise HTTPException(status_code=404, detail=f"No news items found for the provided IDs: {news_id_list}")
        
        # Check if some IDs were not found
        found_ids = {item.id for item in news_items}  # type: ignore
        missing_ids = set(news_id_list) - found_ids  # type: ignore
        if missing_ids:
            logger.warning(f"[POST /html-email/by-ids] Some news items not found: {missing_ids}")
        
        html_email = ""
        for news_item in news_items:
            source = news_item.source
            issue_date = news_item.issue_date.strftime("%Y-%m-%d") if news_item.issue_date else "N/A"
            title = news_item.title
            
            # Handle SFC URL conversion specially with safe fallback
            if source == "SFC" and news_item.content_url:
                try:
                    content_url = sfc_news_service.convert_api_url_to_news_orignal_url(str(news_item.content_url))
                except Exception as e:
                    logger.warning(f"[POST /html-email/by-ids] URL convert failed for '{news_item.content_url}': {e}. Falling back to original URL.")
                    content_url = str(news_item.content_url)
            else:
                content_url = str(news_item.content_url) if news_item.content_url else ""
            
            llm_summary = news_item.llm_summary
            html_summary = markdown2.markdown(llm_summary, extras=['tables', 'fenced-code-blocks', 'toc']).replace('\n', '') if llm_summary else ""
            html_email += f"""<p><h2>{source} - <a href="{content_url}">{title}</a></h2></p><p>{issue_date}</p><p>{html_summary}</p>""" + "<br><br>"
        
        logger.info(f"[POST /html-email/by-ids] Successfully processed {len(news_items)} news items")
        if missing_ids:
            logger.info(f"[POST /html-email/by-ids] Note: {len(missing_ids)} news items were not found: {missing_ids}")
        logger.info("[POST /html-email/by-ids] Successfully generated HTML email")
        return html_email
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"[POST /html-email/by-ids] Failed to process news: {str(e)}")
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


@router.get("/date-range/grouped", response_model=GroupedComplianceNewsResponse)
async def get_news_by_date_range_grouped_all_sources(
    start_date: str,
    end_date: str,
    sources: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get news from date range grouped by source.
    
    - **start_date**: Start date in format "yyyy-mm-dd" (e.g., "2024-12-15")
    - **end_date**: End date in format "yyyy-mm-dd" (e.g., "2024-12-22")
    - **sources**: Optional comma-separated list of sources (e.g., "SFC,SEC,HKEX,HKMA"). If not provided, includes all sources.
    - **status**: Optional status filter ("PENDING", "VERIFIED", "DISCARD"). If not provided, includes all statuses.
    
    Returns:
        GroupedComplianceNewsResponse with news grouped by source
    """
    logger.info(f"[GET /date-range/grouped] Starting request - start_date: {start_date}, end_date: {end_date}, sources: {sources}, status: {status}")
    
    # Validate date formats
    try:
        start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        logger.error("[GET /date-range/grouped] Invalid date format")
        raise HTTPException(status_code=400, detail="Invalid date format. Please use yyyy-mm-dd format (e.g., 2024-12-15)")
    
    # Validate date range
    if start_datetime > end_datetime:
        logger.error("[GET /date-range/grouped] Start date is after end date")
        raise HTTPException(status_code=400, detail="Start date must be before or equal to end date")
    
    # Parse sources parameter
    sources_list = None
    if sources:
        sources_list = [source.strip().upper() for source in sources.split(",")]
        valid_sources = {"SFC", "SEC", "HKEX", "HKMA"}
        invalid_sources = set(sources_list) - valid_sources
        if invalid_sources:
            logger.error(f"[GET /date-range/grouped] Invalid sources: {invalid_sources}")
            raise HTTPException(status_code=400, detail=f"Invalid sources: {invalid_sources}. Valid sources are: {valid_sources}")
    
    # Validate status parameter
    if status:
        from constant.status_constants import PENDING, VERIFIED, DISCARD
        valid_statuses = {PENDING, VERIFIED, DISCARD}
        if status.upper() not in valid_statuses:
            logger.error(f"[GET /date-range/grouped] Invalid status: {status}")
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}. Valid statuses are: {valid_statuses}")
        status = status.upper()  # Normalize to uppercase
    
    compliance_news_service = ComplianceNewsService(db)
    
    try:
        logger.info("[GET /date-range/grouped] Calling ComplianceNewsService.get_news_by_date_range_grouped_all_sources")
        grouped_news = compliance_news_service.get_news_by_date_range_grouped_all_sources(
            start_date=start_datetime,
            end_date=end_datetime,
            sources=sources_list,
            status=status
        )
        
        # Convert to lightweight response format (without content field)
        grouped_light_news = {}
        for source, news_list in grouped_news.items():
            grouped_light_news[source] = [
                ComplianceNewsLightResponse(
                    id=news.id,  # type: ignore
                    source=news.source,  # type: ignore
                    issue_date=news.issue_date,  # type: ignore
                    title=news.title,  # type: ignore
                    content_url=news.content_url,  # type: ignore
                    llm_summary=news.llm_summary,  # type: ignore
                    creation_date=news.creation_date,  # type: ignore
                    creation_user=news.creation_user,  # type: ignore
                    status=news.status  # type: ignore
                ) for news in news_list
            ]
        
        total_count = sum(len(news_list) for news_list in grouped_news.values())
        filter_desc = f"{total_count} total news items grouped by {len(grouped_news)} sources"
        if status:
            filter_desc += f" with status: {status}"
        logger.info(f"[GET /date-range/grouped] Successfully retrieved {filter_desc}")
        
        return GroupedComplianceNewsResponse(grouped_news=grouped_light_news)
        
    except Exception as e:
        logger.error(f"[GET /date-range/grouped] Failed to fetch grouped news: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch grouped news: {str(e)}")

@router.put("/update-status/{news_id}", response_model=UpdateStatusResponse)
async def update_news_status(
    news_id: int,
    update_status_request: UpdateStatusRequest,
    db: Session = Depends(get_db)
):
    """
    Update the status of a specific news item by its ID.
    
    - **news_id**: The ID of the news item to update.
    - **update_status_request**: A JSON object containing the new status.
    
    Returns:
        UpdateStatusResponse indicating the success of the update.
    """
    logger.info(f"[PUT /update-status/{news_id}] Starting update news status request - news_id: {news_id}, new_status: {update_status_request.status}")
    
    compliance_news_service = ComplianceNewsService(db)
    
    try:
        logger.info(f"[PUT /update-status/{news_id}] Calling ComplianceNewsService.update_news_status")
        updated_news = compliance_news_service.update_news_status(
            news_id=news_id,
            status=update_status_request.status
        )
        
        if updated_news is None:
            logger.error(f"[PUT /update-status/{news_id}] News record not found")
            raise HTTPException(status_code=404, detail=f"News record with ID {news_id} not found")
        
        logger.info(f"[PUT /update-status/{news_id}] Successfully updated news status to {updated_news.status}")
        return UpdateStatusResponse(
            id=updated_news.id,  # type: ignore
            status=updated_news.status,  # type: ignore
            message=f"News with ID {news_id} status updated to {updated_news.status}"
        )
        
    except ValueError as e:
        logger.error(f"[PUT /update-status/{news_id}] Invalid status value: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[PUT /update-status/{news_id}] Failed to update news status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update news status: {str(e)}")

@router.put("/update-content/{news_id}", response_model=UpdateTitleAndSummaryResponse)
async def update_news_title_and_summary(
    news_id: int,
    update_request: UpdateTitleAndSummaryRequest,
    db: Session = Depends(get_db)
):
    """
    Update the title and/or llm_summary of a specific news item by its ID.
    
    - **news_id**: The ID of the news item to update.
    - **update_request**: A JSON object containing the new title and/or llm_summary.
    
    Returns:
        UpdateTitleAndSummaryResponse indicating the success of the update.
    """
    logger.info(f"[PUT /update-content/{news_id}] Starting update news title and summary request - news_id: {news_id}")
    
    compliance_news_service = ComplianceNewsService(db)
    
    try:
        logger.info(f"[PUT /update-content/{news_id}] Calling ComplianceNewsService.update_news_title_and_summary")
        updated_news = compliance_news_service.update_news_title_and_summary(
            news_id=news_id,
            title=update_request.title,
            llm_summary=update_request.llm_summary
        )
        
        if updated_news is None:
            logger.error(f"[PUT /update-content/{news_id}] News record not found")
            raise HTTPException(status_code=404, detail=f"News record with ID {news_id} not found")
        
        logger.info(f"[PUT /update-content/{news_id}] Successfully updated news title and/or llm_summary")
        return UpdateTitleAndSummaryResponse(
            id=updated_news.id,  # type: ignore
            title=updated_news.title,  # type: ignore
            llm_summary=updated_news.llm_summary,  # type: ignore
            message=f"News with ID {news_id} updated successfully"
        )
        
    except ValueError as e:
        logger.error(f"[PUT /update-content/{news_id}] Invalid request data: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[PUT /update-content/{news_id}] Failed to update news title and summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update news title and summary: {str(e)}")