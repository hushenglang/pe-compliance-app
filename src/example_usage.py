"""
Example usage of the compliance news database components
"""

from datetime import datetime
from config.database import SessionLocal
from model.compliance_news import ComplianceNews
from repo.compliance_news_repository import ComplianceNewsRepository
import os
from dotenv import load_dotenv

def example_usage():
    """Demonstrate how to use the compliance news components"""
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Create tables (do this once when setting up the database)
    print("connect to database...")
    DATABASE_URL = os.getenv("MySQL_DATABASE_URL")
    print("DATABASE_URL: ", DATABASE_URL)
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Initialize the repository
        repo = ComplianceNewsRepository(db)
        
        repo.create(ComplianceNews(
            source="test",
            issue_date=datetime.now(),
            title="test",
            content="test",
            content_url="test",
            creation_user="hushenglang"
        ))  

        print(repo.get_by_source("test"))
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

def example_sfc_news_service():
    """Example usage of SFC News Service"""
    from service.sfc_news_service import SfcNewsService
    from datetime import datetime, timedelta
    
    print("\n=== SFC News Service Example ===")
    
    # Create service instance with context manager for automatic cleanup
    with SfcNewsService() as service:
        try:
            # Example 1: Fetch today's news
            print("\n1. Fetching today's SFC news...")
            today_news = service.fetch_and_persist_today_news(creation_user="example_user")
            print(f"Found and persisted {len(today_news)} news items for today")
            
            # Example 2: Fetch news for a specific date
            print("\n2. Fetching SFC news for a specific date...")
            specific_date = "2025-06-27"  # Example date
            daily_news = service.fetch_and_persist_news_by_date(specific_date, creation_user="example_user")
            print(f"Found and persisted {len(daily_news)} news items for {specific_date}")
            
    
            
            # Example 4: Get existing news from database
            print("\n4. Retrieving existing SFC news from database...")
            existing_news = service.get_existing_news_by_source(skip=0, limit=10)
            print(f"Retrieved {len(existing_news)} existing SFC news items from database")
            
            # Display some details of the retrieved news
            for i, news in enumerate(existing_news[:3], 1):  # Show first 3 items
                print(f"  {i}. {news.title[:50]}... (Date: {news.issue_date})")
            
            # Example 5: Get news by date range from database
            print("\n5. Retrieving news from database by date range...")
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=7)  # Last 7 days
            date_range_news = service.get_news_by_date_range(start_dt, end_dt)
            print(f"Retrieved {len(date_range_news)} news items from last 7 days")
            
        except Exception as e:
            print(f"Error in SFC news service example: {e}")

if __name__ == "__main__":
    # Run both examples
    print("=== Running Basic Database Example ===")
    # example_usage()
    
    print("\n" + "="*50)
    print("=== Running SFC News Service Example ===")
    example_sfc_news_service() 