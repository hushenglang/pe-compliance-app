from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from model.compliance_news import ComplianceNews

class ComplianceNewsRepository:
    """Repository class for compliance news operations"""
    
    def __init__(self, db: Session):
        self.db = db

    def create(self, compliance_news: ComplianceNews) -> ComplianceNews:
        """Create a new compliance news record"""
        self.db.add(compliance_news)
        self.db.commit()
        self.db.refresh(compliance_news)
        return compliance_news

    def _get_by_id(self, news_id: int) -> Optional[ComplianceNews]:
        """Get compliance news by ID"""
        return self.db.query(ComplianceNews).filter(ComplianceNews.id == news_id).first()

    def get_by_source(self, source: str, skip: int = 0, limit: int = 100) -> List[ComplianceNews]:
        """Get compliance news by source"""
        return self.db.query(ComplianceNews).filter(
            ComplianceNews.source == source
        ).offset(skip).limit(limit).all()

    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[ComplianceNews]:
        """Get compliance news within a date range"""
        return self.db.query(ComplianceNews).filter(
            ComplianceNews.issue_date >= start_date,
            ComplianceNews.issue_date <= end_date
        ).all()

    def update(self, compliance_news: ComplianceNews) -> Optional[ComplianceNews]:
        """Update compliance news record"""
        db_news = self._get_by_id(compliance_news.id)
        if db_news:
            db_news.source = compliance_news.source
            db_news.issue_date = compliance_news.issue_date
            db_news.title = compliance_news.title
            db_news.content = compliance_news.content
            db_news.content_url = compliance_news.content_url
            db_news.llm_summary = compliance_news.llm_summary
            db_news.creation_user = compliance_news.creation_user
            self.db.commit()
            self.db.refresh(db_news)
        return db_news

    def delete(self, compliance_news: ComplianceNews) -> bool:
        """Delete compliance news record"""
        db_news = self._get_by_id(compliance_news.id)
        if db_news:
            self.db.delete(db_news)
            self.db.commit()
            return True
        return False

