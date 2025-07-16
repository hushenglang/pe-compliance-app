from sqlalchemy import Column, Integer, String, Text, DateTime, func
from config.database import Base

class ComplianceNews(Base):
    """SQLAlchemy model for compliance_news table"""
    __tablename__ = "compliance_news"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(255), nullable=False)
    issue_date = Column(DateTime, nullable=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    content_url = Column(String(2000), nullable=True)
    llm_summary = Column(Text, nullable=True)
    creation_date = Column(DateTime, default=func.current_timestamp())
    creation_user = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default='PENDING')