import requests
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from util.logging_util import get_logger


class HKMAClient:
    """Client for fetching press release data from HKMA API."""
    
    def __init__(self):
        self.base_url = "https://api.hkma.gov.hk/public/press-releases"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.logger = get_logger(__name__)
    
    def fetch_press_releases(self, from_date: Optional[str] = None, to_date: Optional[str] = None, 
                           lang: str = "tc", offset: int = 0) -> List[Dict[str, Any]]:
        """
        Fetch press release data from HKMA API.
        
        Args:
            from_date: Start date in format "yyyy-mm-dd" (e.g., "2025-07-03")
            to_date: End date in format "yyyy-mm-dd" (e.g., "2025-07-03")
            lang: Language code ("en" or "tc")
            offset: Number of records to skip for pagination
        
        Returns:
            List of dictionaries containing title, link, and date
        """
        params: Dict[str, Union[str, int]] = {
            "offset": offset,
            "lang": lang,
            "choose": "date"
        }
        
        # Add date parameters if provided
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        
        try:
            self.logger.info(f"Fetching press releases from HKMA API with params: {params}")
            response = requests.get(self.base_url, params=params, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check if the API request was successful
            if not data.get("header", {}).get("success", False):
                error_code = data.get("header", {}).get("err_code", "Unknown")
                error_msg = data.get("header", {}).get("err_msg", "Unknown error")
                self.logger.error(f"API returned error - Code: {error_code}, Message: {error_msg}")
                return []
            
            # Extract press releases from the response
            press_releases = []
            result = data.get("result", {})
            records = result.get("records", [])
            
            if records:
                total_items = len(records)
                self.logger.info(f"Processing {total_items} press release items from API response")
                
                for record in records:
                    press_release = {
                        "title": record.get("title"),
                        "link": record.get("link"),
                        "date": record.get("date")
                    }
                    press_releases.append(press_release)
            
            self.logger.info(f"Found {len(press_releases)} press releases")
            return press_releases
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error making request: {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON response: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return []
    
    def fetch_press_release_content(self, url: str) -> Optional[str]:
        """
        Fetch press release content from a given URL.
        
        Args:
            url: The URL to fetch press release content from
        
        Returns:
            String containing the press release content, or None if failed
        """
        try:
            self.logger.debug(f"Fetching content from URL: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # Since HKMA press releases are HTML pages, return the text content
            content = response.text
            
            if content:
                self.logger.debug(f"Successfully fetched content ({len(content)} characters)")
            else:
                self.logger.warning(f"No content found in response from {url}")
            
            return content
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error making request to {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error fetching content from {url}: {e}")
            return None
    
    def fetch_press_releases_by_date_range(self, from_date: str, to_date: str, 
                                         lang: str = "en") -> List[Dict[str, Any]]:
        """
        Fetch press releases for a specific date range.
        
        Args:
            from_date: Start date in format "yyyy-mm-dd"
            to_date: End date in format "yyyy-mm-dd"
            lang: Language code ("en" or "tc")
        
        Returns:
            List of dictionaries containing title, link, and date
        """
        # Validate date format
        try:
            datetime.strptime(from_date, "%Y-%m-%d")
            datetime.strptime(to_date, "%Y-%m-%d")
        except ValueError:
            self.logger.error("Invalid date format. Expected format: yyyy-mm-dd")
            return []
        
        return self.fetch_press_releases(from_date=from_date, to_date=to_date, lang=lang)
    
    def fetch_press_releases_by_single_date(self, date: str, lang: str = "en") -> List[Dict[str, Any]]:
        """
        Fetch press releases for a single date.
        
        Args:
            date: Date in format "yyyy-mm-dd"
            lang: Language code ("en" or "tc")
        
        Returns:
            List of dictionaries containing title, link, and date
        """
        return self.fetch_press_releases_by_date_range(from_date=date, to_date=date, lang=lang) 