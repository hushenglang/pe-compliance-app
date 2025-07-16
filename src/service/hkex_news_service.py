"""HKEX News Service for fetching and persisting HKEX compliance news."""

import logging
from typing import List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from client.hkex_news_client import HkexNewsClient
from model.compliance_news import ComplianceNews
from repo.compliance_news_repository import ComplianceNewsRepository
from service.agent_service import AgentService
from util.date_util import get_current_datetime_hk, get_hk_timezone
from util.logging_util import get_logger
from constant.prompt_constants import FINANCIAL_COMPLIANCE_SYSTEM_PROMPT


class HkexNewsService:
    """Service for managing HKEX news operations."""
    
    def __init__(self, db: Session):
        """Initialize the HKEX news service.
        
        Args:
            db: Database session
        """
        self.client = HkexNewsClient()
        self.db = db
        self.repository = ComplianceNewsRepository(db)
        self.agent_service = AgentService("hkex_financial_compliance_assistant", FINANCIAL_COMPLIANCE_SYSTEM_PROMPT)
        
        # Configure detailed logging
        self.logger = get_logger(__name__, level=logging.INFO, format_style="detailed")
        
        self.logger.info("[INIT] HkexNewsService initialized")
    
    async def fetch_and_persist_news_by_date(self, date: str, creation_user: str = "system", llm_enabled: bool = True) -> List[ComplianceNews]:
        """Fetch HKEX news for a specific date and persist to database.
        
        Args:
            date: Date in format "yyyy-mm-dd" (e.g., "2024-12-15")
            creation_user: User who initiated the fetch operation
            llm_enabled: Whether to enable LLM processing for content summarization
            
        Returns:
            List of persisted ComplianceNews objects
        """
        self.logger.info(f"Fetching HKEX news for date: {date}")
        
        try:
            # Fetch news from HKEX regulatory announcements page using the updated client API
            # Use the same date for both from_date and to_date to fetch news for a specific date
            news_items = self.client.fetch_news(from_date=date, to_date=date)
            
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
                            self.logger.debug(f"Fetched content for news: {item.get('title')}")
                        else:
                            self.logger.warning(f"Failed to fetch content for news: {item.get('title')}")
                    
                    # Convert date string to datetime (using 'date' instead of 'issueDate')
                    issue_date = None
                    if item.get("date"):
                        try:
                            issue_date = datetime.strptime(item["date"], "%Y-%m-%d")
                            # Localize to Hong Kong timezone
                            hk_tz = get_hk_timezone()
                            issue_date = issue_date.replace(tzinfo=hk_tz)
                        except ValueError as e:
                            self.logger.warning(f"Failed to parse issue date: {item.get('date')}, error: {e}")
                    
                    llm_summary = None
                    if llm_enabled and content is not None:
                        llm_summary = await self.agent_service.chat(content)

                    # Create ComplianceNews object
                    compliance_news = ComplianceNews(
                        source="HKEX",
                        issue_date=issue_date,
                        title=item.get("title", ""),
                        content=content,
                        llm_summary=llm_summary,
                        content_url=item.get("url"),
                        creation_user=creation_user,
                        status="PENDING"
                    )
                    
                    # Persist to database
                    persisted_item = self.repository.create(compliance_news)
                    persisted_news.append(persisted_item)
                    
                    self.logger.info(f"Successfully persisted news: {item.get('title')}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to process news item {item.get('title')}: {e}")
                    # Continue with other items even if one fails
                    continue
            
            self.logger.info(f"Successfully persisted {len(persisted_news)} out of {len(news_items)} news items")
            return persisted_news
            
        except Exception as e:
            self.logger.error(f"Error fetching and persisting news for date {date}: {e}")
            raise
    
    async def fetch_and_persist_news_by_date_range(self, from_date: str, to_date: str, creation_user: str = "system", llm_enabled: bool = True) -> List[ComplianceNews]:
        """Fetch HKEX news for a date range and persist to database.
        
        Args:
            from_date: Start date in format "yyyy-mm-dd" (e.g., "2024-12-15")
            to_date: End date in format "yyyy-mm-dd" (e.g., "2024-12-16")
            creation_user: User who initiated the fetch operation
            llm_enabled: Whether to enable LLM processing for content summarization
            
        Returns:
            List of persisted ComplianceNews objects
        """
        self.logger.info(f"Fetching HKEX news for date range: {from_date} to {to_date}")
        
        try:
            # Fetch news from HKEX regulatory announcements page using the updated client API
            news_items = self.client.fetch_news(from_date=from_date, to_date=to_date)
            
            if not news_items:
                self.logger.info(f"No news found for date range: {from_date} to {to_date}")
                return []
            
            self.logger.info(f"Found {len(news_items)} news items for date range: {from_date} to {to_date}")
            
            persisted_news = []
            for item in news_items:
                try:
                    # Fetch content for each news item
                    content = None
                    if item.get("url"):
                        content = self.client.fetch_news_content(item["url"])
                        if content:
                            self.logger.debug(f"Fetched content for news: {item.get('title')}")
                        else:
                            self.logger.warning(f"Failed to fetch content for news: {item.get('title')}")
                    
                    # Convert date string to datetime (using 'date' instead of 'issueDate')
                    issue_date = None
                    if item.get("date"):
                        try:
                            issue_date = datetime.strptime(item["date"], "%Y-%m-%d")
                            # Localize to Hong Kong timezone
                            hk_tz = get_hk_timezone()
                            issue_date = issue_date.replace(tzinfo=hk_tz)
                        except ValueError as e:
                            self.logger.warning(f"Failed to parse issue date: {item.get('date')}, error: {e}")
                    
                    llm_summary = None
                    if llm_enabled and content is not None:
                        llm_summary = await self.agent_service.chat(content)

                    # Create ComplianceNews object
                    compliance_news = ComplianceNews(
                        source="HKEX",
                        issue_date=issue_date,
                        title=item.get("title", ""),
                        content=content,
                        llm_summary=llm_summary,
                        content_url=item.get("url"),
                        creation_user=creation_user,
                        status="PENDING"
                    )
                    
                    # Persist to database
                    persisted_item = self.repository.create(compliance_news)
                    persisted_news.append(persisted_item)
                    
                    self.logger.info(f"Successfully persisted news: {item.get('title')}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to process news item {item.get('title')}: {e}")
                    # Continue with other items even if one fails
                    continue
            
            self.logger.info(f"Successfully persisted {len(persisted_news)} out of {len(news_items)} news items")
            return persisted_news
            
        except Exception as e:
            self.logger.error(f"Error fetching and persisting news for date range {from_date} to {to_date}: {e}")
            raise
    
    
    async def fetch_and_persist_today_news(self, creation_user: str = "system", llm_enabled: bool = True) -> List[ComplianceNews]:
        """Fetch HKEX news for today (Hong Kong timezone) and persist to database.
        
        Args:
            creation_user: User who initiated the fetch operation
            llm_enabled: Whether to enable LLM processing for content summarization
            
        Returns:
            List of persisted ComplianceNews objects
        """
        today = get_current_datetime_hk().strftime("%Y-%m-%d")
        self.logger.info(f"Fetching today's HKEX news for HK date: {today}")
        return await self.fetch_and_persist_news_by_date(today, creation_user, llm_enabled)
    
    def get_existing_news(self, skip: int = 0, limit: int = 100) -> List[ComplianceNews]:
        """Get existing HKEX news from database.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of ComplianceNews objects
        """
        return self.repository.get_by_source("HKEX", skip, limit)
    
    def get_news_by_date_range(self, start_date: datetime, end_date: datetime) -> List[ComplianceNews]:
        """Get existing HKEX news from database within date range.
        
        Args:
            start_date: Start datetime
            end_date: End datetime
            
        Returns:
            List of ComplianceNews objects
        """
        return self.repository.get_by_date_range(start_date, end_date, "HKEX")
    
    def get_news_last_7days(self) -> List[ComplianceNews]:
        """Get HKEX news from the last 7 days.
            
        Returns:
            List of ComplianceNews objects from the last 7 days
        """
        end_date = get_current_datetime_hk()
        start_date = end_date - timedelta(days=7)
        
        self.logger.info(f"Fetching HKEX news for the last 7 days: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        return self.get_news_by_date_range(start_date, end_date) 
    