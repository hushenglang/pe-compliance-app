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

if __name__ == "__main__":
    example_usage() 