"""SFC News Service for fetching and persisting SFC compliance news."""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from client.sfc_news_client import SfcNewsClient
from model.compliance_news import ComplianceNews
from repo.compliance_news_repository import ComplianceNewsRepository
from config.database import get_db
from util.date_util import get_current_datetime_hk, get_hk_timezone


class SfcNewsService:
    """Service for managing SFC news operations."""
    
    def __init__(self, db: Optional[Session] = None):
        """Initialize the SFC news service.
        
        Args:
            db: Database session. If None, will create a new session.
        """
        self.client = SfcNewsClient()
        self._db = db
        self._repository = None
        self.logger = logging.getLogger(__name__)
    
    @property
    def db(self) -> Session:
        """Get database session."""
        if self._db is None:
            self._db = next(get_db())
        return self._db
    
    @property
    def repository(self) -> ComplianceNewsRepository:
        """Get repository instance."""
        if self._repository is None:
            self._repository = ComplianceNewsRepository(self.db)
        return self._repository
    
    def fetch_and_persist_news_by_date(self, date: str, creation_user: str = "system") -> List[ComplianceNews]:
        """Fetch SFC news for a specific date and persist to database.
        
        Args:
            date: Date in format "yyyy-mm-dd" (e.g., "2024-12-15")
            creation_user: User who initiated the fetch operation
            
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
                    
                    # Create ComplianceNews object
                    compliance_news = ComplianceNews(
                        source="SFC",
                        issue_date=issue_date,
                        title=item.get("title", ""),
                        content=content,
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
    
    
    def fetch_and_persist_today_news(self, creation_user: str = "system") -> List[ComplianceNews]:
        """Fetch SFC news for today (Hong Kong timezone) and persist to database.
        
        Args:
            creation_user: User who initiated the fetch operation
            
        Returns:
            List of persisted ComplianceNews objects
        """
        today = get_current_datetime_hk().strftime("%Y-%m-%d")
        self.logger.info(f"Fetching today's SFC news for HK date: {today}")
        return self.fetch_and_persist_news_by_date(today, creation_user)
    
    def get_existing_news_by_source(self, skip: int = 0, limit: int = 100) -> List[ComplianceNews]:
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
    
    def close(self):
        """Close database session if it was created by this service."""
        if self._db and hasattr(self._db, 'close'):
            self._db.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close() 