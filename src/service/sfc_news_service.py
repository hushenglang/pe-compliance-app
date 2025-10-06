"""SFC News Service for fetching and persisting SFC compliance news."""

import logging
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from urllib.parse import urlparse, parse_qs

from client.sfc_news_client import SfcNewsClient
from model.compliance_news import ComplianceNews
from repo.compliance_news_repository import ComplianceNewsRepository
from service.agent_service import AgentService
from util.date_util import get_current_datetime_hk, get_hk_timezone
from util.logging_util import get_logger
from constant.prompt_constants import FINANCIAL_COMPLIANCE_SYSTEM_PROMPT
from constant.status_constants import PENDING


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
                        content = self.client.fetch_content(item["url"])
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
                        creation_user=creation_user,
                        status=PENDING
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
    
    async def fetch_and_persist_circular_by_date(self, date: str, creation_user: str = "system", llm_enabled: bool = True) -> List[ComplianceNews]:
        """Fetch SFC circular for a specific date and persist to database.
        
        Args:
            date: Date in format "yyyy-mm-dd" (e.g., "2024-12-15")
            creation_user: User who initiated the fetch operation
            llm_enabled: Whether to enable LLM processing for content summarization
            
        Returns:
            List of persisted ComplianceNews objects
        """
        self.logger.info(f"Fetching SFC circular for date: {date}")
        
        try:
            # Fetch circular from SFC API
            circular_items = self.client.fetch_circular(date)
            
            if not circular_items:
                self.logger.info(f"No circular found for date: {date}")
                return []
            
            self.logger.info(f"Found {len(circular_items)} circular items for date: {date}")
            
            persisted_circular = []
            for item in circular_items:
                try:
                    # Fetch content for each circular item
                    content = None
                    if item.get("url"):
                        content = self.client.fetch_content(item["url"])
                        if content:
                            self.logger.debug(f"Fetched content for circular: {item.get('refNo')}")
                        else:
                            self.logger.warning(f"Failed to fetch content for circular: {item.get('refNo')}")
                    
                    # Convert release date string to datetime
                    release_date = None
                    if item.get("releasedDate"):
                        try:
                            release_date = datetime.strptime(item["releasedDate"], "%Y-%m-%d")
                            # Localize to Hong Kong timezone
                            hk_tz = get_hk_timezone()
                            release_date = release_date.replace(tzinfo=hk_tz)
                        except ValueError as e:
                            self.logger.warning(f"Failed to parse release date: {item.get('releasedDate')}, error: {e}")
                    
                    llm_summary = None
                    if llm_enabled and content is not None:
                        llm_summary = await self.agent_service.chat(content)

                    # Create ComplianceNews object (using issue_date field for release_date)
                    compliance_circular = ComplianceNews(
                        source="SFC",
                        issue_date=release_date,
                        title=item.get("title", ""),
                        content=content,
                        llm_summary=llm_summary,
                        content_url=item.get("url"),
                        creation_user=creation_user,
                        status=PENDING
                    )
                    
                    # Persist to database
                    persisted_item = self.repository.create(compliance_circular)
                    persisted_circular.append(persisted_item)
                    
                    self.logger.info(f"Successfully persisted circular: {item.get('refNo')} - {item.get('title')}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to process circular item {item.get('refNo')}: {e}")
                    # Continue with other items even if one fails
                    continue
            
            self.logger.info(f"Successfully persisted {len(persisted_circular)} out of {len(circular_items)} circular items")
            return persisted_circular
            
        except Exception as e:
            self.logger.error(f"Error fetching and persisting circular for date {date}: {e}")
            raise
    
    async def fetch_and_persist_today_circular(self, creation_user: str = "system", llm_enabled: bool = True) -> List[ComplianceNews]:
        """Fetch SFC circular for today (Hong Kong timezone) and persist to database.
        
        Args:
            creation_user: User who initiated the fetch operation
            llm_enabled: Whether to enable LLM processing for content summarization
            
        Returns:
            List of persisted ComplianceNews objects
        """
        today = get_current_datetime_hk().strftime("%Y-%m-%d")
        self.logger.info(f"Fetching today's SFC circular for HK date: {today}")
        return await self.fetch_and_persist_circular_by_date(today, creation_user, llm_enabled)
    
    async def fetch_and_persist_consultation_by_date(self, date: str, creation_user: str = "system", llm_enabled: bool = True) -> List[ComplianceNews]:
        """Fetch SFC consultation for a specific date and persist to database.
        
        Args:
            date: Date in format "yyyy-mm-dd" (e.g., "2024-12-15")
            creation_user: User who initiated the fetch operation
            llm_enabled: Whether to enable LLM processing for content summarization
            
        Returns:
            List of persisted ComplianceNews objects
        """
        self.logger.info(f"Fetching SFC consultation for date: {date}")
        
        try:
            # Fetch consultation from SFC API
            consultation_items = self.client.fetch_consultation(date)
            
            if not consultation_items:
                self.logger.info(f"No consultation found for date: {date}")
                return []
            
            self.logger.info(f"Found {len(consultation_items)} consultation items for date: {date}")
            
            persisted_consultation = []
            for item in consultation_items:
                try:
                    # Fetch content for each consultation item
                    content = None
                    if item.get("url"):
                        content = self.client.fetch_content(item["url"])
                        if content:
                            self.logger.debug(f"Fetched content for consultation: {item.get('cpRefNo')}")
                        else:
                            self.logger.warning(f"Failed to fetch content for consultation: {item.get('cpRefNo')}")
                    
                    # Convert issue date string to datetime
                    issue_date = None
                    if item.get("cpIssueDate"):
                        try:
                            issue_date = datetime.strptime(item["cpIssueDate"], "%Y-%m-%d")
                            # Localize to Hong Kong timezone
                            hk_tz = get_hk_timezone()
                            issue_date = issue_date.replace(tzinfo=hk_tz)
                        except ValueError as e:
                            self.logger.warning(f"Failed to parse issue date: {item.get('cpIssueDate')}, error: {e}")
                    
                    llm_summary = None
                    if llm_enabled and content is not None:
                        llm_summary = await self.agent_service.chat(content)

                    # Create ComplianceNews object (using issue_date field for consultation issue date)
                    compliance_consultation = ComplianceNews(
                        source="SFC",
                        issue_date=issue_date,
                        title=item.get("cpTitle", ""),
                        content=content,
                        llm_summary=llm_summary,
                        content_url=item.get("url"),
                        creation_user=creation_user,
                        status=PENDING
                    )
                    
                    # Persist to database
                    persisted_item = self.repository.create(compliance_consultation)
                    persisted_consultation.append(persisted_item)
                    
                    self.logger.info(f"Successfully persisted consultation: {item.get('cpRefNo')} - {item.get('cpTitle')}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to process consultation item {item.get('cpRefNo')}: {e}")
                    # Continue with other items even if one fails
                    continue
            
            self.logger.info(f"Successfully persisted {len(persisted_consultation)} out of {len(consultation_items)} consultation items")
            return persisted_consultation
            
        except Exception as e:
            self.logger.error(f"Error fetching and persisting consultation for date {date}: {e}")
            raise
    
    async def fetch_and_persist_today_consultation(self, creation_user: str = "system", llm_enabled: bool = True) -> List[ComplianceNews]:
        """Fetch SFC consultation for today (Hong Kong timezone) and persist to database.
        
        Args:
            creation_user: User who initiated the fetch operation
            llm_enabled: Whether to enable LLM processing for content summarization
            
        Returns:
            List of persisted ComplianceNews objects
        """
        today = get_current_datetime_hk().strftime("%Y-%m-%d")
        self.logger.info(f"Fetching today's SFC consultation for HK date: {today}")
        return await self.fetch_and_persist_consultation_by_date(today, creation_user, llm_enabled)
    
 

    def convert_api_url_to_news_orignal_url(self, api_url: str) -> str:
        """Convert SFC API URL to gateway URL format.
        Supports multiple API entrypoints and normalizes alternate CDN prefixes.
        Examples:
        - From: https://apps.sfc.hk/edistributionWeb/api/news/content?refNo=25PR99&lang=TC
          To:   https://apps.sfc.hk/edistributionWeb/gateway/TC/news-and-announcements/news/doc?refNo=25PR99
        - From: https://sc.sfc.hk/TuniS/apps.sfc.hk/edistributionWeb/api/circular/content?refNo=25EC48&lang=TC
          To:   https://apps.sfc.hk/edistributionWeb/gateway/TC/circulars/doc?refNo=25EC48
        Args:
            api_url: The original API URL
        Returns:
            The converted gateway URL
        Raises:
            ValueError: If the URL format is invalid or missing required parameters
        """
        try:
            parsed_url = urlparse(api_url)
            
            # Determine and validate base path (allow CDN-prefixed TuniS path)
            path_before_api = parsed_url.path.split('/api')[0]
            if not path_before_api.endswith('/edistributionWeb'):
                raise ValueError("Invalid base URL path. Expected path to end with /edistributionWeb")
            
            # Normalize to canonical base
            canonical_base = "https://apps.sfc.hk/edistributionWeb"
            
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
            
            # Identify API type from the path after /api/
            remainder_after_api = parsed_url.path.split('/api/', 1)[1] if '/api/' in parsed_url.path else ''
            api_type = remainder_after_api.split('/', 1)[0] if remainder_after_api else ''
            
            # Map API type to gateway path
            # Only map known types; otherwise, return original URL to avoid breaking
            if api_type == 'news':
                gateway_path = 'news-and-announcements/news'
            elif api_type == 'circular':
                gateway_path = 'circulars'
            else:
                # For unknown types (e.g., consultation), fall back to original URL
                self.logger.warning(
                    f"[URL-CONVERT] Unhandled API type '{api_type}' in URL: {api_url}. Returning original URL.")
                return api_url
            
            # Construct the new gateway URL
            gateway_url = f"{canonical_base}/gateway/{lang}/{gateway_path}/doc?refNo={ref_no}"
            
            self.logger.debug(f"Converted API URL to gateway URL: {api_url} -> {gateway_url}")
            return gateway_url
            
        except Exception as e:
            self.logger.error(f"Failed to convert API URL to gateway URL: {api_url}, error: {e}")
            raise ValueError(f"Invalid URL format: {e}")

