from client.sfc_news_client import SfcNewsClient
from util.date_util import get_current_date_hk

def main():
    """Main function to run the news data fetching."""
    print("Fetching news data from SFC Hong Kong...")
    
    # Create an instance of the SFC news client
    client = SfcNewsClient()    
    # Get current date in Hong Kong timezone
    
    today_date = get_current_date_hk()
    news_data = client.fetch_news(date="2025-06-27")
        
    for news in news_data:
        print(f"News Ref No: {news['newsRefNo']}")
        print(f"Issue Date: {news['issueDate']}")
        print(f"Title: {news['title']}")
        print(f"Language: {news['lang']}")
        print(f"URL: {news['url']}")
        print("-" * 80)
            

if __name__ == "__main__":
    main()
