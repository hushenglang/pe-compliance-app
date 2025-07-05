import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from util.logging_util import get_logger


class SECNewsClient:
    """Client for fetching press release data from SEC RSS feed."""
    
    def __init__(self):
        self.base_url = "https://www.sec.gov/news/pressreleases.rss"
        self.headers = {
            "User-Agent": "ComplianceNewsBot/1.0 (Compliance News Monitoring; contact@compliance-app.com)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/rss+xml;q=0.8,*/*;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "From": "compliance-monitoring@app.com"
        }
        self.logger = get_logger(__name__)
    
    def fetch_press_releases(self, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch press release data from SEC RSS feed.
        
        Args:
            from_date: Start date in format "yyyy-mm-dd" (e.g., "2025-07-03")
            to_date: End date in format "yyyy-mm-dd" (e.g., "2025-07-03")
        
        Returns:
            List of dictionaries containing title, link, description, date, and guid
        """
        try:
            self.logger.info(f"Fetching press releases from SEC RSS feed")
            response = requests.get(self.base_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # Parse XML content
            root = ET.fromstring(response.content)
            
            # Find all item elements
            items = root.findall('.//item')
            
            press_releases = []
            
            if items:
                total_items = len(items)
                self.logger.info(f"Processing {total_items} press release items from RSS feed")
                
                for item in items:
                    # Extract data from each item
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    description_elem = item.find('description')
                    pubdate_elem = item.find('pubDate')
                    guid_elem = item.find('guid')
                    
                    # Convert pubDate to our standard format
                    pub_date_str = pubdate_elem.text if pubdate_elem is not None else None
                    formatted_date = None
                    
                    if pub_date_str:
                        try:
                            # Parse RSS date format: "Thu, 26 Jun 2025 11:00:00 -0400"
                            parsed_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
                            formatted_date = parsed_date.strftime("%Y-%m-%d")
                        except ValueError:
                            self.logger.warning(f"Could not parse date: {pub_date_str}")
                            formatted_date = pub_date_str
                    
                    press_release = {
                        "title": title_elem.text.strip() if title_elem is not None else None,
                        "link": link_elem.text.strip() if link_elem is not None else None,
                        "description": description_elem.text.strip() if description_elem is not None else None,
                        "date": formatted_date,
                        "pubDate": pub_date_str,
                        "guid": guid_elem.text.strip() if guid_elem is not None else None
                    }
                    
                    # Apply date filtering if specified
                    if self._should_include_by_date(formatted_date, from_date, to_date):
                        press_releases.append(press_release)
            
            self.logger.info(f"Found {len(press_releases)} press releases after filtering")
            return press_releases
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error making request: {e}")
            return []
        except ET.ParseError as e:
            self.logger.error(f"Error parsing XML response: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return []
    
    def _should_include_by_date(self, item_date: Optional[str], from_date: Optional[str], to_date: Optional[str]) -> bool:
        """
        Check if an item should be included based on date filtering.
        
        Args:
            item_date: Date of the item in "yyyy-mm-dd" format
            from_date: Start date filter in "yyyy-mm-dd" format
            to_date: End date filter in "yyyy-mm-dd" format
        
        Returns:
            True if item should be included, False otherwise
        """
        if not item_date:
            return True  # Include items without dates
        
        if not from_date and not to_date:
            return True  # No date filtering
        
        try:
            item_date_obj = datetime.strptime(item_date, "%Y-%m-%d").date()
            
            if from_date:
                from_date_obj = datetime.strptime(from_date, "%Y-%m-%d").date()
                if item_date_obj < from_date_obj:
                    return False
            
            if to_date:
                to_date_obj = datetime.strptime(to_date, "%Y-%m-%d").date()
                if item_date_obj > to_date_obj:
                    return False
            
            return True
            
        except ValueError:
            self.logger.warning(f"Could not parse date for filtering: {item_date}")
            return True  # Include items with unparseable dates
    
    def fetch_press_release_content(self, url: str, max_retries: int = 3) -> Optional[str]:
        """
        Fetch press release content from a given URL.
        
        Args:
            url: The URL to fetch press release content from
            max_retries: Maximum number of retry attempts
        
        Returns:
            String containing the press release content, or None if failed
        """
        import time
        
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"Fetching content from URL (attempt {attempt + 1}/{max_retries}): {url}")
                
                # Add a small delay between retries
                if attempt > 0:
                    time.sleep(2)
                
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                
                # Parse HTML content using BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find the main content div
                main_content_div = soup.find('div', class_='main-content__main page-layout-type--layout-details')
                
                if main_content_div:
                    # Extract text content from the div
                    content = main_content_div.get_text(strip=True, separator='\n')
                    
                    if content:
                        self.logger.debug(f"Successfully extracted content ({len(content)} characters)")
                        return content
                    else:
                        self.logger.warning(f"No text content found in main content div for {url}")
                else:
                    self.logger.warning(f"Could not find main content div with specified class for {url}")
                    
                return None
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    self.logger.warning(f"Access forbidden (403) for {url} - attempt {attempt + 1}/{max_retries}")
                    if attempt == max_retries - 1:
                        self.logger.error(f"Failed to fetch content after {max_retries} attempts due to 403 error")
                        return None
                else:
                    self.logger.error(f"HTTP error {e.response.status_code} for {url}: {e}")
                    return None
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error making request to {url}: {e}")
                if attempt == max_retries - 1:
                    return None
            except Exception as e:
                self.logger.error(f"Unexpected error fetching content from {url}: {e}")
                return None
        
        return None
    
    def fetch_press_releases_by_date_range(self, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """
        Fetch press releases for a specific date range.
        
        Args:
            from_date: Start date in format "yyyy-mm-dd"
            to_date: End date in format "yyyy-mm-dd"
        
        Returns:
            List of dictionaries containing title, link, description, date, and guid
        """
        # Validate date format
        try:
            datetime.strptime(from_date, "%Y-%m-%d")
            datetime.strptime(to_date, "%Y-%m-%d")
        except ValueError:
            self.logger.error(f"Invalid date format. Expected format: yyyy-mm-dd")
            return []
        
        return self.fetch_press_releases(from_date=from_date, to_date=to_date)
    
    def fetch_press_releases_by_single_date(self, date: str) -> List[Dict[str, Any]]:
        """
        Fetch press releases for a single date.
        
        Args:
            date: Date in format "yyyy-mm-dd"
        
        Returns:
            List of dictionaries containing title, link, description, date, and guid
        """
        return self.fetch_press_releases_by_date_range(from_date=date, to_date=date)
    
    def fetch_latest_press_releases(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch the latest press releases without date filtering.
        
        Args:
            limit: Maximum number of press releases to return
        
        Returns:
            List of dictionaries containing title, link, description, date, and guid
        """
        press_releases = self.fetch_press_releases()
        return press_releases[:limit] if press_releases else [] 