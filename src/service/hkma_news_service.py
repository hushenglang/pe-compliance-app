"""HKMA News Service for fetching and persisting HKMA compliance news."""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup, Tag
from client.hkma_client import HKMAClient
from model.compliance_news import ComplianceNews
from repo.compliance_news_repository import ComplianceNewsRepository
from service.agent_service import AgentService
from util.date_util import get_current_datetime_hk, get_hk_timezone
from util.logging_util import get_logger
from constant.prompt_constants import FINANCIAL_COMPLIANCE_SYSTEM_PROMPT


class HkmaNewsService:
    """Service for managing HKMA news operations."""
    
    def __init__(self, db: Session):
        """Initialize the HKMA news service.
        
        Args:
            db: Database session
        """
        self.client = HKMAClient()
        self.db = db
        self.repository = ComplianceNewsRepository(db)
        self.agent_service = AgentService("hkma_financial_compliance_assistant", FINANCIAL_COMPLIANCE_SYSTEM_PROMPT)
        
        # Configure detailed logging
        self.logger = get_logger(__name__, level=logging.INFO, format_style="detailed")
        
        self.logger.info("[INIT] HkmaNewsService initialized")
    
    async def fetch_and_persist_news_by_date(self, date: str, creation_user: str = "system", llm_enabled: bool = True) -> List[ComplianceNews]:
        """Fetch HKMA press releases for a specific date and persist to database.
        
        Args:
            date: Date in format "yyyy-mm-dd" (e.g., "2024-12-15")
            creation_user: User who initiated the fetch operation
            llm_enabled: Whether to enable LLM processing for content summarization
            
        Returns:
            List of persisted ComplianceNews objects
        """
        self.logger.info(f"Fetching HKMA press releases for date: {date}")
        
        try:
            # Fetch press releases from HKMA API
            press_releases = self.client.fetch_press_releases_by_single_date(date)
            return await self._process_and_persist_press_releases(
                press_releases, 
                creation_user, 
                llm_enabled, 
                f"date: {date}"
            )
            
        except Exception as e:
            self.logger.error(f"Error fetching and persisting press releases for date {date}: {e}")
            raise
    
    async def fetch_and_persist_news_by_date_range(self, from_date: str, to_date: str, 
                                                  creation_user: str = "system", llm_enabled: bool = True) -> List[ComplianceNews]:
        """Fetch HKMA press releases for a date range and persist to database.
        
        Args:
            from_date: Start date in format "yyyy-mm-dd"
            to_date: End date in format "yyyy-mm-dd"
            creation_user: User who initiated the fetch operation
            llm_enabled: Whether to enable LLM processing for content summarization
            
        Returns:
            List of persisted ComplianceNews objects
        """
        self.logger.info(f"Fetching HKMA press releases for date range: {from_date} to {to_date}")
        
        try:
            # Fetch press releases from HKMA API
            press_releases = self.client.fetch_press_releases_by_date_range(from_date, to_date)
            return await self._process_and_persist_press_releases(
                press_releases, 
                creation_user, 
                llm_enabled, 
                f"date range: {from_date} to {to_date}"
            )
            
        except Exception as e:
            self.logger.error(f"Error fetching and persisting press releases for date range {from_date} to {to_date}: {e}")
            raise
    
    async def fetch_and_persist_today_news(self, creation_user: str = "system", llm_enabled: bool = True) -> List[ComplianceNews]:
        """Fetch HKMA press releases for today (Hong Kong timezone) and persist to database.
        
        Args:
            creation_user: User who initiated the fetch operation
            llm_enabled: Whether to enable LLM processing for content summarization
            
        Returns:
            List of persisted ComplianceNews objects
        """
        today = get_current_datetime_hk().strftime("%Y-%m-%d")
        self.logger.info(f"Fetching today's HKMA press releases for HK date: {today}")
        return await self.fetch_and_persist_news_by_date(today, creation_user, llm_enabled)
    
    def get_existing_news(self, skip: int = 0, limit: int = 100) -> List[ComplianceNews]:
        """Get existing HKMA news from database.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of ComplianceNews objects
        """
        return self.repository.get_by_source("HKMA", skip, limit)
    
    def get_news_by_date_range(self, start_date: datetime, end_date: datetime) -> List[ComplianceNews]:
        """Get existing HKMA news from database within date range.
        
        Args:
            start_date: Start datetime
            end_date: End datetime
            
        Returns:
            List of ComplianceNews objects
        """
        return self.repository.get_by_date_range(start_date, end_date)
    
    def get_news_last_7days(self) -> List[ComplianceNews]:
        """Get HKMA news from the last 7 days.
            
        Returns:
            List of ComplianceNews objects from the last 7 days
        """
        end_date = get_current_datetime_hk()
        start_date = end_date - timedelta(days=7)
        
        self.logger.info(f"Fetching HKMA news for the last 7 days: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        return self.get_news_by_date_range(start_date, end_date) 
    
    async def _process_and_persist_press_releases(self, press_releases: List[dict], 
                                                creation_user: str, llm_enabled: bool, 
                                                context: str) -> List[ComplianceNews]:
        """Process and persist press releases to database.
        
        Args:
            press_releases: List of press release dictionaries
            creation_user: User who initiated the fetch operation
            llm_enabled: Whether to enable LLM processing for content summarization
            context: Context string for logging (e.g., "date: 2024-12-15")
            
        Returns:
            List of persisted ComplianceNews objects
        """
        if not press_releases:
            self.logger.info(f"No press releases found for {context}")
            return []
        
        self.logger.info(f"Found {len(press_releases)} press releases for {context}")
        
        persisted_news = []
        for item in press_releases:
            try:
                # Fetch content for each press release
                content = self._fetch_press_release_content(item)
                
                # Parse issue date
                issue_date = self._parse_issue_date(item.get("date"))
                
                # Generate LLM summary if enabled
                llm_summary = None
                if llm_enabled and content is not None:
                    llm_summary = await self.agent_service.chat(content)

                # Create ComplianceNews object
                compliance_news = ComplianceNews(
                    source="HKMA",
                    issue_date=issue_date,
                    title=item.get("title", ""),
                    content=content,
                    llm_summary=llm_summary,
                    content_url=item.get("link"),
                    creation_user=creation_user
                )
                
                # Persist to database
                persisted_item = self.repository.create(compliance_news)
                persisted_news.append(persisted_item)
                
                self.logger.info(f"Successfully persisted press release: {item.get('title')}")
                
            except Exception as e:
                self.logger.error(f"Failed to process press release {item.get('title')}: {e}")
                # Continue with other items even if one fails
                continue
        
        self.logger.info(f"Successfully persisted {len(persisted_news)} out of {len(press_releases)} press releases")
        return persisted_news
    
    def _fetch_press_release_content(self, item: dict) -> Optional[str]:
        """Fetch content for a press release item.
        
        Args:
            item: Press release dictionary containing link and title
            
        Returns:
            Extracted content or None if failed
        """
        content = None
        if item.get("link"):
            raw_content = self.client.fetch_press_release_content(item["link"])
            if raw_content:
                content = self._extract_content_from_hkma_html(raw_content)
                if content:
                    self.logger.debug(f"Fetched content for press release: {item.get('title')}")
                else:
                    self.logger.warning(f"Failed to fetch content for press release: {item.get('title')}")
        return content
    
    def _parse_issue_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse issue date string to datetime object.
        
        Args:
            date_str: Date string in format "yyyy-mm-dd"
            
        Returns:
            Parsed datetime object with HK timezone or None if parsing fails
        """
        if not date_str:
            return None
            
        try:
            issue_date = datetime.strptime(date_str, "%Y-%m-%d")
            # Localize to Hong Kong timezone
            hk_tz = get_hk_timezone()
            return issue_date.replace(tzinfo=hk_tz)
        except ValueError as e:
            self.logger.warning(f"Failed to parse issue date: {date_str}, error: {e}")
            return None
    
    def _extract_content_from_hkma_html(self, html_content: str) -> str:
        """Extract content from HTML.
        
        Args:
            html_content: HTML content
            
        Returns:
            String containing the content
        """
        if not html_content:
            return ""
            
        self.logger.info(f"Extracting content from HTML: {html_content[:100]}")
        soup = BeautifulSoup(html_content, 'html.parser')
        # Find the main content div
        content_div = soup.find('div', class_='content-with-right-content layout-press-release-detail full-content-printer')
        if content_div and isinstance(content_div, Tag):
            # Find the content wrapper within the main div
            content_wrapper = content_div.find('div', class_='content-wrapper')
            if content_wrapper and isinstance(content_wrapper, Tag):
                self.logger.info(f"Found content wrapper: {content_wrapper}")
                return content_wrapper.get_text()
    
        self.logger.info(f"No content wrapper found, returning original HTML: {html_content[:100]}")
        return html_content