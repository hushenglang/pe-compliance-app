import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime
from util.logging_util import get_logger


class HkexNewsClient:
    """Client for fetching news data from HKEX regulatory announcements page."""
    
    def __init__(self):
        self.base_url = "https://www.hkex.com.hk/News/Regulatory-Announcements?sc_lang=en"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        self.logger = get_logger(__name__)
    
    def fetch_news(self, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """
        Fetch news from HKEX regulatory announcements page.
        
        Args:
            from_date: Start date filter in format 'YYYY-MM-DD'
            to_date: End date filter in format 'YYYY-MM-DD'
        
        Returns:
            List of dictionaries containing news data with keys:
            - date: Publication date
            - title: News title
            - url: Full URL to the news article
            - category: News category (usually 'Regulatory')
        """
        try:
            self.logger.debug(f"Fetching HKEX news from {from_date} to {to_date}")
            response = requests.get(self.base_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            # Parse HTML content using the private method
            news_items = self._parse_news_html(response.content, from_date, to_date)
            
            self.logger.info(f"Successfully fetched {len(news_items)} news items")
            return news_items
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error making request to HKEX: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error fetching HKEX news: {e}")
            return []

    def _parse_news_html(self, html_content: bytes, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """
        Parse HTML content and extract news items within the specified date range.
        
        Args:
            html_content: Raw HTML content from the response
            from_date: Start date filter in format 'YYYY-MM-DD'
            to_date: End date filter in format 'YYYY-MM-DD'
        
        Returns:
            List of dictionaries containing parsed news data
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all news rows
        news_rows = soup.find_all('div', class_='whats_on_tdy_row')
        news_items = []
        
        for row in news_rows:
            try:
                # Extract date information
                date_ball = row.find('div', class_='whats_on_tdy_ball')
                if not date_ball:
                    continue
                
                # Get day number
                day_element = date_ball.find('div', class_='whats_on_tdy_ball_number')
                if not day_element:
                    continue
                day_div = day_element.find('div')
                if not day_div:
                    continue
                day = day_div.get_text(strip=True)
                
                # Get month and year (second div in date_ball)
                date_divs = date_ball.find_all('div', recursive=False)
                if len(date_divs) < 2:
                    continue
                month_year = date_divs[1].get_text(strip=True)
                
                # Combine to form full date
                try:
                    # Parse date like "04 Jul 2025"
                    full_date_str = f"{day} {month_year}"
                    parsed_date = datetime.strptime(full_date_str, "%d %b %Y")
                    formatted_date = parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    # Skip if date parsing fails
                    continue
                
                # Extract title and URL
                right_section = row.find('div', class_='whats_on_tdy_right')
                if not right_section:
                    continue
                
                text_container = right_section.find('div', class_='whats_on_tdy_text_container')
                if not text_container:
                    continue
                
                # Get category (text_1)
                category_element = text_container.find('div', class_='whats_on_tdy_text_1')
                category = category_element.get_text(strip=True) if category_element else 'Regulatory'
                
                # Get title and URL (text_2)
                title_element = text_container.find('div', class_='whats_on_tdy_text_2')
                if not title_element:
                    continue
                
                link_element = title_element.find('a')
                if not link_element:
                    continue
                
                title = link_element.get_text(strip=True)
                relative_url = link_element.get('href', '')
                
                # Convert relative URL to absolute URL
                if relative_url.startswith('/'):
                    full_url = f"https://www.hkex.com.hk{relative_url}"
                else:
                    full_url = relative_url
                
                # Apply date range filter
                if formatted_date < from_date or formatted_date > to_date:
                    continue
                
                news_item = {
                    'date': formatted_date,
                    'title': title,
                    'url': full_url,
                    'category': category,
                    'source': 'HKEX'
                }
                
                news_items.append(news_item)
                
            except Exception as e:
                self.logger.warning(f"Error parsing news row: {e}")
                continue
        
        return news_items

    def fetch_news_content(self, url: str) -> Optional[str]:
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
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the main content area specifically
            main_element = soup.find('main')
            
            if main_element:
                # Remove scripts, styles, and other unwanted elements
                for unwanted in main_element(["script", "style", "nav", "header", "footer"]):
                    unwanted.decompose()
                
                # Extract all text content from main tag
                content = main_element.get_text(separator='\n', strip=True)
                
                # Clean up excessive whitespace and empty lines
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                content = '\n'.join(lines)
                
            else:
                self.logger.warning(f"No main element found in response from {url}")
                return None
            
            if content:
                self.logger.debug(f"Successfully fetched content ({len(content)} characters)")
                pass
            else:
                self.logger.warning(f"No content found in main element from {url}")
                pass
            
            return content
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error making request to {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error fetching content from {url}: {e}")
            return None
        