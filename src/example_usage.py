"""
Example usage of the Financial News Crawl system.

This module demonstrates how to use the various services in the system.
"""

import logging
import os
from datetime import datetime, timedelta
import asyncio

from service.sfc_news_service import SfcNewsService
from service.agent_service import AgentService
from util.date_util import get_current_datetime_hk


def setup_logging():
    """Setup basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def example_sfc_news_service():
    """Example usage of SFC News Service."""
    print("=" * 50)
    print("SFC News Service Example")
    print("=" * 50)
    
    # Create service instance
    service = SfcNewsService()
    
    try:
        # Fetch today's news
        print("Fetching today's SFC news...")
        news_items = service.fetch_and_persist_today_news()
        print(f"Found and persisted {len(news_items)} news items")
        
        # Display some news items
        for i, news in enumerate(news_items[:3]):  # Show first 3 items
            print(f"\n{i+1}. {news.title}")
            print(f"   Date: {news.issue_date}")
            print(f"   URL: {news.content_url}")
            if news.content:
                print(f"   Content preview: {news.content[:100]}...")
        
        # Fetch existing news
        print("\nFetching existing SFC news from database...")
        existing_news = service.get_existing_news_by_source(limit=5)
        print(f"Found {len(existing_news)} existing news items")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        service.close()


def example_agent_service(system_prompt: str):
    """Example usage of Agent Service."""
    print("=" * 50)
    print("Agent Service Example")
    print("=" * 50)
    
    # Create service instance
    service = AgentService("financial_compliance_assistant", system_prompt)

    # Test the agent service
    print("Testing agent service...")
    response = asyncio.run(service.chat("What is the capital of France?"))
    print(f"Agent response: {response}")


def main():
    """Main function to run examples."""
    setup_logging()
    
    print("Financial News Crawl - Example Usage")
    print("=" * 60)
    
    # Run SFC News Service example
    # example_sfc_news_service()
    
    # print("\n" + "=" * 60)
    
    # Run Agent Service example
    system_prompt = """You are a specialized financial compliance assistant focused on Hong Kong SFC regulations. 
    Provide accurate, concise responses about SFC rules, regulatory requirements, and compliance best practices. 
    Use clear language and cite relevant regulations when applicable."""
    example_agent_service(system_prompt)
    
    print("\n" + "=" * 60)
    print("Examples completed!")


if __name__ == "__main__":
    main() 