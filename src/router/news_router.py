from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict
from datetime import datetime
from pydantic import BaseModel

from service.sfc_news_service import SfcNewsService
from model.compliance_news import ComplianceNews

# Create a Pydantic model for the response
class ComplianceNewsResponse(BaseModel):
    id: int
    source: str
    issue_date: datetime = None
    title: str
    content: str = None
    content_url: str = None
    llm_summary: str = None
    creation_date: datetime
    creation_user: str

    class Config:
        from_attributes = True

# Create the router
router = APIRouter(
    prefix="/api/news",
    tags=["news"],
    responses={404: {"description": "Not found"}},
)

@router.post("/today", response_model=List[ComplianceNewsResponse])
async def fetch_and_persist_today_news(
    llm_enabled: bool = True,
    user: str = "api"
):
    """
    Fetch and persist today's SFC news and return all persisted news.
    
    - **llm_enabled**: Whether to enable LLM processing for content summarization
    - **user**: User who initiated the fetch operation
    
    Returns:
        List of persisted ComplianceNews objects
    """
    # Create a service instance
    sfc_news_service = SfcNewsService()
    
    try:
        # Fetch and persist today's news synchronously
        persisted_news = sfc_news_service.fetch_and_persist_today_news(
            creation_user=user,
            llm_enabled=llm_enabled
        )
        return persisted_news
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch and persist news: {str(e)}")
    finally:
        # Ensure the service is properly closed
        sfc_news_service.close()

@router.get("/last7days", response_model=List[ComplianceNewsResponse])
async def get_last_7days_news():
    """
    Get SFC news from the last 7 days.
    """
    sfc_news_service = SfcNewsService()
    try:
        news_items = sfc_news_service.get_news_last_7days()
        return news_items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch news: {str(e)}") 