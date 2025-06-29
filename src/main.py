from client.sfc_news_client import SfcNewsClient
from util.date_util import get_current_date_hk
from util.logging_util import setup_logging, get_logger

def main():
    """Main function to run the news data fetching."""
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting SFC news data fetching process")
    print("Fetching news data from SFC Hong Kong...")
    
    # Create an instance of the SFC news client
    client = SfcNewsClient()    
    # Get current date in Hong Kong timezone
    
    today_date = get_current_date_hk()
    logger.info(f"Hong Kong current date: {today_date}")
    
    try:
        news_data = client.fetch_news(date="2025-06-27")
        logger.info(f"Fetched {len(news_data)} news items")
        
        for i, news in enumerate(news_data):
            logger.info(f"Processing news item {i+1}/{len(news_data)}: {news['newsRefNo']}")
            print(f"News Ref No: {news['newsRefNo']}")
            print(f"Issue Date: {news['issueDate']}")
            print(f"Title: {news['title']}")
            print(f"Language: {news['lang']}")
            print(f"URL: {news['url']}")

            # Fetch news content
            try:
                content = client.fetch_news_content(news['url'])
                print(f"Content: {content}")
                logger.debug(f"Successfully fetched content for {news['newsRefNo']}")
            except Exception as e:
                logger.error(f"Failed to fetch content for {news['newsRefNo']}: {e}")

            print("-" * 80)
    except Exception as e:
        logger.error(f"Error during news fetching process: {e}")
        raise
            

if __name__ == "__main__":
    main()
