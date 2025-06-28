import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime


class SfcNewsClient:
    """Client for fetching news data from SFC Hong Kong API."""
    
    def __init__(self):
        self.base_url = "https://apps.sfc.hk/edistributionWeb/api/news"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    def fetch_news(self, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch news data from SFC Hong Kong API.
        
        Args:
            date: Date to filter by in format "yyyy-mm-dd" (e.g., "2024-12-15") or None for all dates
        
        Returns:
            List of dictionaries containing newsRefNo, issueDate, title, and lang
        """
        url = f"{self.base_url}/search"
        
        # Parse date if provided
        year = "all"
        month = "all"
        
        if date:
            try:
                parsed_date = datetime.strptime(date, "%Y-%m-%d")
                year = str(parsed_date.year)
                month = f"{parsed_date.month:02d}"  # Format month with leading zero if needed
            except ValueError:
                print(f"Invalid date format: {date}. Expected format: yyyy-mm-dd")
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
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract required fields from the response
            news_list = []
            if "items" in data and data["items"]:
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
                    
                    # Only append news_item if the issueDate matches the input date
                    if formatted_date == date:
                        news_item = {
                            "newsRefNo": item.get("newsRefNo"),
                            "issueDate": formatted_date,
                            "title": item.get("title"),
                            "lang": item.get("lang"),
                            "url": f"{self.base_url}/content?refNo={item.get('newsRefNo')}&lang={item.get('lang')}"
                        }
                        news_list.append(news_item)
            
            return news_list
            
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error: {e}")
            return [] 