from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class ComplianceNewsResponse(BaseModel):
    """Pydantic schema for ComplianceNews API response"""
    id: int
    source: str
    issue_date: Optional[datetime] = None
    title: str
    content: Optional[str] = None
    content_url: Optional[str] = None
    llm_summary: Optional[str] = None
    creation_date: datetime
    creation_user: str
    status: str

    class Config:
        from_attributes = True


class ComplianceNewsLightResponse(BaseModel):
    """Lightweight Pydantic schema for ComplianceNews API response without content field"""
    id: int
    source: str
    issue_date: Optional[datetime] = None
    title: str
    content_url: Optional[str] = None
    llm_summary: Optional[str] = None
    creation_date: datetime
    creation_user: str
    status: str

    class Config:
        from_attributes = True


class ComplianceNewsStatisticsResponse(BaseModel):
    """Pydantic schema for compliance news statistics response"""
    source: str
    status: str
    record_count: int

    class Config:
        from_attributes = True


class GroupedComplianceNewsResponse(BaseModel):
    """Pydantic schema for grouped compliance news response by source"""
    grouped_news: Dict[str, List[ComplianceNewsLightResponse]]

    class Config:
        from_attributes = True


class UpdateStatusRequest(BaseModel):
    """Pydantic schema for updating news status request"""
    status: str

    class Config:
        from_attributes = True


class UpdateStatusResponse(BaseModel):
    """Pydantic schema for updating news status response"""
    id: int
    status: str
    message: str

    class Config:
        from_attributes = True 