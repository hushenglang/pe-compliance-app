"""SFC News Service for fetching and persisting SFC compliance news."""

import logging
from typing import List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from urllib.parse import urlparse, parse_qs

from client.sfc_news_client import SfcNewsClient
from model.compliance_news import ComplianceNews
from repo.compliance_news_repository import ComplianceNewsRepository
from service.agent_service import AgentService
from util.date_util import get_current_datetime_hk, get_hk_timezone
from util.logging_util import get_logger
from constant.prompt_constants import FINANCIAL_COMPLIANCE_SYSTEM_PROMPT


class SfcNewsService:
    """Service for managing SFC news operations."""
    
    def __init__(self, db: Session):
        """Initialize the SFC news service.
        
        Args:
            db: Database session
        """
        self.client = SfcNewsClient()
        self.db = db
        self.repository = ComplianceNewsRepository(db)
        self.agent_service = AgentService("sfc_financial_compliance_assistant", FINANCIAL_COMPLIANCE_SYSTEM_PROMPT)
        
        # Configure detailed logging
        self.logger = get_logger(__name__, level=logging.INFO, format_style="detailed")
        
        self.logger.info("[INIT] SfcNewsService initialized")
    
    async def fetch_and_persist_news_by_date(self, date: str, creation_user: str = "system", llm_enabled: bool = True) -> List[ComplianceNews]:
        """Fetch SFC news for a specific date and persist to database.
        
        Args:
            date: Date in format "yyyy-mm-dd" (e.g., "2024-12-15")
            creation_user: User who initiated the fetch operation
            llm_enabled: Whether to enable LLM processing for content summarization
            
        Returns:
            List of persisted ComplianceNews objects
        """
        self.logger.info(f"Fetching SFC news for date: {date}")
        
        try:
            # Fetch news from SFC API
            news_items = self.client.fetch_news(date)
            
            if not news_items:
                self.logger.info(f"No news found for date: {date}")
                return []
            
            self.logger.info(f"Found {len(news_items)} news items for date: {date}")
            
            persisted_news = []
            for item in news_items:
                try:
                    # Fetch content for each news item
                    content = None
                    if item.get("url"):
                        content = self.client.fetch_news_content(item["url"])
                        if content:
                            self.logger.debug(f"Fetched content for news: {item.get('newsRefNo')}")
                        else:
                            self.logger.warning(f"Failed to fetch content for news: {item.get('newsRefNo')}")
                    
                    # Convert issue date string to datetime
                    issue_date = None
                    if item.get("issueDate"):
                        try:
                            issue_date = datetime.strptime(item["issueDate"], "%Y-%m-%d")
                            # Localize to Hong Kong timezone
                            hk_tz = get_hk_timezone()
                            issue_date = issue_date.replace(tzinfo=hk_tz)
                        except ValueError as e:
                            self.logger.warning(f"Failed to parse issue date: {item.get('issueDate')}, error: {e}")
                    
                    llm_summary = None
                    if llm_enabled and content is not None:
                        llm_summary = await self.agent_service.chat(content)

                    # Create ComplianceNews object
                    compliance_news = ComplianceNews(
                        source="SFC",
                        issue_date=issue_date,
                        title=item.get("title", ""),
                        content=content,
                        llm_summary=llm_summary,
                        content_url=item.get("url"),
                        creation_user=creation_user
                    )
                    
                    # Persist to database
                    persisted_item = self.repository.create(compliance_news)
                    persisted_news.append(persisted_item)
                    
                    self.logger.info(f"Successfully persisted news: {item.get('newsRefNo')} - {item.get('title')}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to process news item {item.get('newsRefNo')}: {e}")
                    # Continue with other items even if one fails
                    continue
            
            self.logger.info(f"Successfully persisted {len(persisted_news)} out of {len(news_items)} news items")
            return persisted_news
            
        except Exception as e:
            self.logger.error(f"Error fetching and persisting news for date {date}: {e}")
            raise
    
    
    async def fetch_and_persist_today_news(self, creation_user: str = "system", llm_enabled: bool = True) -> List[ComplianceNews]:
        """Fetch SFC news for today (Hong Kong timezone) and persist to database.
        
        Args:
            creation_user: User who initiated the fetch operation
            llm_enabled: Whether to enable LLM processing for content summarization
            
        Returns:
            List of persisted ComplianceNews objects
        """
        today = get_current_datetime_hk().strftime("%Y-%m-%d")
        self.logger.info(f"Fetching today's SFC news for HK date: {today}")
        return await self.fetch_and_persist_news_by_date(today, creation_user, llm_enabled)
    
    def get_existing_news(self, skip: int = 0, limit: int = 100) -> List[ComplianceNews]:
        """Get existing SFC news from database.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of ComplianceNews objects
        """
        return self.repository.get_by_source("SFC", skip, limit)
    
    def get_news_by_date_range(self, start_date: datetime, end_date: datetime) -> List[ComplianceNews]:
        """Get existing SFC news from database within date range.
        
        Args:
            start_date: Start datetime
            end_date: End datetime
            
        Returns:
            List of ComplianceNews objects
        """
        return self.repository.get_by_date_range(start_date, end_date)
    
    def get_news_last_7days(self) -> List[ComplianceNews]:
        """Get SFC news from the last 7 days.
            
        Returns:
            List of ComplianceNews objects from the last 7 days
        """
        end_date = get_current_datetime_hk()
        start_date = end_date - timedelta(days=7)
        
        self.logger.info(f"Fetching SFC news for the last 7 days: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        return self.get_news_by_date_range(start_date, end_date) 

    def convert_api_url_to_news_orignal_url(self, api_url: str) -> str:
        """Convert SFC API URL to gateway URL format.
        Converts from:
        https://apps.sfc.hk/edistributionWeb/api/news/content?refNo=25PR99&lang=TC
        To:
        https://apps.sfc.hk/edistributionWeb/gateway/TC/news-and-announcements/news/doc?refNo=25PR99
        Args:
            api_url: The original API URL
        Returns:
            The converted gateway URL
        Raises:
            ValueError: If the URL format is invalid or missing required parameters
        """
        try:
            parsed_url = urlparse(api_url)
            
            # Validate base URL
            expected_base = "https://apps.sfc.hk/edistributionWeb"
            actual_base = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path.split('/api')[0]}"
            
            if actual_base != expected_base:
                raise ValueError(f"Invalid base URL. Expected: {expected_base}, Got: {actual_base}")
            
            # Extract query parameters
            query_params = parse_qs(parsed_url.query)
            
            # Get refNo parameter
            ref_no_list = query_params.get('refNo')
            if not ref_no_list:
                raise ValueError("Missing 'refNo' parameter in URL")
            ref_no = ref_no_list[0]  # parse_qs returns lists
            
            # Get lang parameter (default to 'TC' if not present)
            lang_list = query_params.get('lang')
            lang = lang_list[0] if lang_list else 'TC'
            
            # Construct the new gateway URL
            gateway_url = f"{expected_base}/gateway/{lang}/news-and-announcements/news/doc?refNo={ref_no}"
            
            self.logger.debug(f"Converted API URL to gateway URL: {api_url} -> {gateway_url}")
            return gateway_url
            
        except Exception as e:
            self.logger.error(f"Failed to convert API URL to gateway URL: {api_url}, error: {e}")
            raise ValueError(f"Invalid URL format: {e}")

