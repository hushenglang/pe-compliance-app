"""Compliance News Service for consolidated news operations across all sources."""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from model.compliance_news import ComplianceNews
from repo.compliance_news_repository import ComplianceNewsRepository
from util.date_util import get_current_datetime_hk
from util.logging_util import get_logger


class ComplianceNewsService:
    """Service for managing consolidated compliance news operations across all sources."""
    
    def __init__(self, db: Session):
        """Initialize the compliance news service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.repository = ComplianceNewsRepository(db)
        
        # Configure detailed logging
        self.logger = get_logger(__name__, level=logging.INFO, format_style="detailed")
        
        self.logger.info("[INIT] ComplianceNewsService initialized")
    
    def get_existing_news(self, source: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[ComplianceNews]:
        """Get existing news from database, optionally filtered by source.
        
        Args:
            source: Optional news source filter ("SFC", "SEC", "HKEX", "HKMA"). If None, returns all sources.
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of ComplianceNews objects
        """
        if source:
            self.logger.info(f"Fetching existing {source} news (skip={skip}, limit={limit})")
            return self.repository.get_by_source(source, skip, limit)
        else:
            self.logger.info(f"Fetching existing news from all sources (skip={skip}, limit={limit})")
            return self.repository.get_all(skip, limit)
    
    def get_news_by_date_range(self, start_date: datetime, end_date: datetime, source: Optional[str] = None, status: Optional[str] = None) -> List[ComplianceNews]:
        """Get existing news from database within date range, optionally filtered by source and status.
        
        Args:
            start_date: Start datetime
            end_date: End datetime
            source: Optional news source filter ("SFC", "SEC", "HKEX", "HKMA"). If None, returns all sources.
            status: Optional status filter ("PENDING", "VERIFIED", "DISCARD"). If None, returns all statuses.
            
        Returns:
            List of ComplianceNews objects
        """
        filter_desc = f"date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        if source:
            filter_desc = f"{source} news for " + filter_desc
        else:
            filter_desc = "news from all sources for " + filter_desc
        if status:
            filter_desc += f" with status: {status}"
            
        self.logger.info(f"Fetching {filter_desc}")
        return self.repository.get_by_date_range(start_date, end_date, source, status)
    
    def get_news_last_7days(self, source: Optional[str] = None) -> List[ComplianceNews]:
        """Get news from the last 7 days, optionally filtered by source.
        
        Args:
            source: Optional news source filter ("SFC", "SEC", "HKEX", "HKMA"). If None, returns all sources.
            
        Returns:
            List of ComplianceNews objects from the last 7 days
        """
        end_date = get_current_datetime_hk()
        start_date = end_date - timedelta(days=7)
        
        if source:
            self.logger.info(f"Fetching {source} news for the last 7 days: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        else:
            self.logger.info(f"Fetching news from all sources for the last 7 days: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        return self.get_news_by_date_range(start_date, end_date, source)
    
    def get_news_by_sources(self, sources: List[str], skip: int = 0, limit: int = 100) -> Dict[str, List[ComplianceNews]]:
        """Get existing news from database grouped by specified sources.
        
        Args:
            sources: List of news sources ("SFC", "SEC", "HKEX", "HKMA")
            skip: Number of records to skip per source
            limit: Maximum number of records to return per source
            
        Returns:
            Dictionary mapping source names to lists of ComplianceNews objects
        """
        self.logger.info(f"Fetching news from sources: {sources} (skip={skip}, limit={limit})")
        
        result: Dict[str, List[ComplianceNews]] = {}
        for source in sources:
            result[source] = self.repository.get_by_source(source, skip, limit)
        
        return result
    
    def get_news_by_date_range_grouped_all_sources(self, start_date: datetime, end_date: datetime, sources: Optional[List[str]] = None, status: Optional[str] = None) -> Dict[str, List[ComplianceNews]]:
        """Get news from date range grouped by source.
        
        Args:
            start_date: Start datetime
            end_date: End datetime
            sources: Optional list of news sources. If None, includes all sources.
            status: Optional status filter ("PENDING", "VERIFIED", "DISCARD"). If None, returns all statuses.
            
        Returns:
            Dictionary mapping source names to lists of ComplianceNews objects
        """
        if sources is None:
            sources = ["SFC", "SEC", "HKEX", "HKMA"]
        
        filter_desc = f"sources {sources} for date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        if status:
            filter_desc += f" with status: {status}"
        self.logger.info(f"Fetching news from {filter_desc}")
        
        # Single query to get all news for the date range from all sources with optional status filter
        all_news = self.repository.get_by_date_range(start_date, end_date, status=status)
        
        # Filter by requested sources and group by source
        result: Dict[str, List[ComplianceNews]] = {source: [] for source in sources}
        for news in all_news:
            news_source = str(news.source)  # Cast to string to avoid Column type issues
            if news_source in sources:
                result[news_source].append(news)
        
        return result
    
    def get_news_last_7days_grouped_all_sources(self, sources: Optional[List[str]] = None, status: Optional[str] = None) -> Dict[str, List[ComplianceNews]]:
        """Get news from the last 7 days grouped by source.
        
        Args:
            sources: Optional list of news sources. If None, includes all sources.
            status: Optional status filter ("PENDING", "VERIFIED", "DISCARD"). If None, returns all statuses.
            
        Returns:
            Dictionary mapping source names to lists of ComplianceNews objects from the last 7 days
        """
        end_date = get_current_datetime_hk()
        start_date = end_date - timedelta(days=7)
        
        return self.get_news_by_date_range_grouped_all_sources(start_date, end_date, sources, status)
    
    def get_statistics_by_source_and_status(self) -> List[Dict[str, Any]]:
        """Get statistics of compliance news grouped by source and status.
        
        Returns:
            List of dictionaries containing source, status, and record_count
        """
        self.logger.info("Fetching compliance news statistics by source and status")
        return self.repository.get_statistics_by_source_and_status() 