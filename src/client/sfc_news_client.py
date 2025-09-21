import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from util.logging_util import get_logger


class SfcNewsClient:
    """Client for fetching news data from SFC Hong Kong API."""
    
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.logger = get_logger(__name__)
    
    def fetch_news(self, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch news data from SFC Hong Kong API.
        
        Args:
            date: Date to filter by in format "yyyy-mm-dd" (e.g., "2024-12-15") or None for all dates
        
        Returns:
            List of dictionaries containing newsRefNo, issueDate, title, and lang
        """
        base_url = "https://apps.sfc.hk/edistributionWeb/api/news"
        url = f"{base_url}/search"
        
        # Parse date if provided
        year = "all"
        month = "all"
        
        if date:
            try:
                parsed_date = datetime.strptime(date, "%Y-%m-%d")
                year = str(parsed_date.year)
                month = f"{parsed_date.month:02d}"  # Format month with leading zero if needed
            except ValueError:
                self.logger.error(f"Invalid date format: {date}. Expected format: yyyy-mm-dd")
                return []
        
        payload = {
            "lang": "TC",
            "category": "all",
            "year": year,
            "month": month,
            "pageNo": 0,
            "pageSize": 20,
            "isLoading": True,
            "errors": None,
            "items": None,
            "total": -1
        }
        
        try:
            self.logger.info(f"Fetching news from SFC API for date: {date}")
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract required fields from the response
            news_list = []
            if "items" in data and data["items"]:
                total_items = len(data["items"])
                self.logger.info(f"Processing {total_items} news items from API response")
                
                for item in data["items"]:
                    # Convert issueDate from datetime format to yyyy-mm-dd
                    issue_date = item.get("issueDate")
                    formatted_date = issue_date
                    if issue_date:
                        try:
                            # Parse datetime string and format to yyyy-mm-dd
                            parsed_datetime = datetime.fromisoformat(issue_date.replace('Z', '+00:00'))
                            formatted_date = parsed_datetime.strftime("%Y-%m-%d")
                        except (ValueError, AttributeError):
                            # Keep original format if parsing fails
                            formatted_date = issue_date
                            self.logger.warning(f"Failed to parse date format: {issue_date}")
                    
                    # Only append news_item if the issueDate matches the input date
                    if formatted_date == date:
                        news_item = {
                            "newsRefNo": item.get("newsRefNo"),
                            "issueDate": formatted_date,
                            "title": item.get("title"),
                            "lang": item.get("lang"),
                            "url": f"{base_url}/content?refNo={item.get('newsRefNo')}&lang={item.get('lang')}"
                        }
                        news_list.append(news_item)
            
            self.logger.info(f"Found {len(news_list)} news items matching date: {date}")
            return news_list
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error making request: {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON response: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return []

    def fetch_circular(self, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch circular data from SFC Hong Kong API.
        
        Args:
            date: Date to filter by in format "yyyy-mm-dd" (e.g., "2024-12-15") or None for all dates
        
        Returns:
            List of dictionaries containing refNo, releasedDate, title, lang, and publicUrl
        """
        base_url = "https://sc.sfc.hk/TuniS/apps.sfc.hk/edistributionWeb/api/circular"
        url = f"{base_url}/search"
        
        # Parse date if provided
        year = "all"
        
        if date:
            try:
                parsed_date = datetime.strptime(date, "%Y-%m-%d")
                year = parsed_date.year
            except ValueError:
                self.logger.error(f"Invalid date format: {date}. Expected format: yyyy-mm-dd")
                return []
        else:
            # Default to current year if no date provided
            year = datetime.now().year
        
        payload = {
            "lang": "TC",
            "category": "all",
            "year": year,
            "pageNo": 0,
            "pageSize": 20,
            "sort": {"field": "issueDate", "order": "desc"},
            "isLoading": True,
            "errors": None,
            "items": None,
            "total": -1
        }
        
        try:
            self.logger.info(f"Fetching circular from SFC API for date: {date}")
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract required fields from the response
            circular_list = []
            if "items" in data and data["items"]:
                total_items = len(data["items"])
                self.logger.info(f"Processing {total_items} circular items from API response")
                
                for item in data["items"]:
                    # Convert releasedDate from datetime format to yyyy-mm-dd
                    released_date = item.get("releasedDate")
                    formatted_date = released_date
                    if released_date:
                        try:
                            # Parse datetime string and format to yyyy-mm-dd
                            parsed_datetime = datetime.fromisoformat(released_date.replace('Z', '+00:00'))
                            formatted_date = parsed_datetime.strftime("%Y-%m-%d")
                        except (ValueError, AttributeError):
                            # Keep original format if parsing fails
                            formatted_date = released_date
                            self.logger.warning(f"Failed to parse date format: {released_date}")
                    
                    # Only append circular_item if the releasedDate matches the input date or if no date filter
                    if date is None or formatted_date == date:
                        # Build full URL for circular content
                        public_url = item.get("publicUrl")
                        full_content_url = f"{base_url}/content?refNo={item.get('refNo')}&lang={item.get('lang')}"
                        
                        circular_item = {
                            "refNo": item.get("refNo"),
                            "releasedDate": formatted_date,
                            "title": item.get("title"),
                            "lang": item.get("lang"),
                            "publicUrl": public_url,
                            "url": full_content_url
                        }
                        circular_list.append(circular_item)
            
            self.logger.info(f"Found {len(circular_list)} circular items matching date: {date}")
            return circular_list
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error making request: {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON response: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return []

    def fetch_consultation(self, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch consultation data from SFC Hong Kong API.
        
        Args:
            date: Date to filter by in format "yyyy-mm-dd" (e.g., "2024-12-15") or None for all dates
        
        Returns:
            List of dictionaries containing cpRefNo, cpIssueDate, cpTitle, lang, and url
        """
        base_url = "https://sc.sfc.hk/TuniS/apps.sfc.hk/edistributionWeb/api/consultation"
        url = f"{base_url}/search"
        
        # Parse date if provided
        year = "all"
        
        if date:
            try:
                parsed_date = datetime.strptime(date, "%Y-%m-%d")
                year = parsed_date.year
            except ValueError:
                self.logger.error(f"Invalid date format: {date}. Expected format: yyyy-mm-dd")
                return []
        else:
            # Default to current year if no date provided
            year = datetime.now().year
        
        payload = {
            "lang": "TC",
            "year": year,
            "pageNo": 0,
            "pageSize": 20,
            "isLoading": True,
            "errors": None,
            "items": None,
            "total": -1
        }
        
        try:
            self.logger.info(f"Fetching consultation from SFC API for date: {date}")
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract required fields from the response
            consultation_list = []
            if "items" in data and data["items"]:
                total_items = len(data["items"])
                self.logger.info(f"Processing {total_items} consultation items from API response")
                
                for item in data["items"]:
                    # Convert cpIssueDate from datetime format to yyyy-mm-dd
                    issue_date = item.get("cpIssueDate")
                    formatted_date = issue_date
                    if issue_date:
                        try:
                            # Parse datetime string and format to yyyy-mm-dd
                            parsed_datetime = datetime.fromisoformat(issue_date.replace('Z', '+00:00'))
                            formatted_date = parsed_datetime.strftime("%Y-%m-%d")
                        except (ValueError, AttributeError):
                            # Keep original format if parsing fails
                            formatted_date = issue_date
                            self.logger.warning(f"Failed to parse date format: {issue_date}")
                    
                    # Only append consultation_item if the cpIssueDate matches the input date or if no date filter
                    if date is None or formatted_date == date:
                        # Build full URL for consultation content
                        full_content_url = f"{base_url}/content?refNo={item.get('cpRefNo')}&lang={item.get('lang')}"
                        
                        consultation_item = {
                            "cpRefNo": item.get("cpRefNo"),
                            "cpIssueDate": formatted_date,
                            "cpTitle": item.get("cpTitle"),
                            "lang": item.get("lang"),
                            "commentDeadline": item.get("commentDeadline"),
                            "url": full_content_url
                        }
                        consultation_list.append(consultation_item)
            
            self.logger.info(f"Found {len(consultation_list)} consultation items matching date: {date}")
            return consultation_list
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error making request: {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON response: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return []

    def fetch_content(self, url: str) -> Optional[str]:
        """
        Fetch news content from a given URL.
        
        Args:
            url: The URL to fetch news content from
        
        Returns:
            String containing the news content, or None if failed
        """
        try:
            self.logger.debug(f"Fetching content from URL: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            content = data.get("html")
            
            if content:
                self.logger.debug(f"Successfully fetched content ({len(content)} characters)")
            else:
                self.logger.warning(f"No content found in response from {url}")
            
            return content
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error making request to {url}: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON response from {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error fetching content from {url}: {e}")
            return None 