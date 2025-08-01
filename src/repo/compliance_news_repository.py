from sqlalchemy.orm import Session
from typing import List, Optional, cast, Dict, Any
from datetime import datetime
from model.compliance_news import ComplianceNews
from util.logging_util import get_logger

class ComplianceNewsRepository:
    """Repository class for compliance news operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = get_logger(__name__)

    def create(self, compliance_news: ComplianceNews) -> ComplianceNews:
        """Create a new compliance news record"""
        try:
            self.logger.debug(f"Creating new compliance news record: {compliance_news.title}")
            self.db.add(compliance_news)
            self.db.commit()
            self.db.refresh(compliance_news)
            self.logger.info(f"Successfully created compliance news record with ID: {compliance_news.id}")
            return compliance_news
        except Exception as e:
            self.logger.error(f"Failed to create compliance news record: {e}")
            self.db.rollback()
            raise

    def _get_by_id(self, news_id: int) -> Optional[ComplianceNews]:
        """Get compliance news by ID"""
        return self.db.query(ComplianceNews).filter(ComplianceNews.id == news_id).first()

    def get_by_id(self, news_id: int) -> Optional[ComplianceNews]:
        """Get compliance news by ID"""
        try:
            self.logger.debug(f"Fetching compliance news by ID: {news_id}")
            result = self.db.query(ComplianceNews).filter(ComplianceNews.id == news_id).first()
            if result:
                self.logger.info(f"Found compliance news record with ID: {news_id}")
            else:
                self.logger.warning(f"No compliance news record found with ID: {news_id}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to fetch compliance news by ID {news_id}: {e}")
            raise

    def get_by_ids(self, news_ids: List[int]) -> List[ComplianceNews]:
        """Get compliance news by list of IDs"""
        try:
            self.logger.debug(f"Fetching compliance news by IDs: {news_ids}")
            results = self.db.query(ComplianceNews).filter(
                ComplianceNews.id.in_(news_ids)
            ).order_by(ComplianceNews.issue_date.desc(), ComplianceNews.source).all()
            
            found_count = len(results)
            requested_count = len(news_ids)
            
            if found_count == requested_count:
                self.logger.info(f"Found all {found_count} requested compliance news records")
            else:
                found_ids = [news.id for news in results]
                missing_ids = [id for id in news_ids if id not in found_ids]
                self.logger.warning(f"Found {found_count} out of {requested_count} compliance news records. Missing IDs: {missing_ids}")
            
            return results
        except Exception as e:
            self.logger.error(f"Failed to fetch compliance news by IDs {news_ids}: {e}")
            raise

    def get_by_source(self, source: str, skip: int = 0, limit: int = 100) -> List[ComplianceNews]:
        """Get compliance news by source"""
        try:
            self.logger.debug(f"Fetching compliance news by source: {source}, skip: {skip}, limit: {limit}")
            results = self.db.query(ComplianceNews).filter(
                ComplianceNews.source == source
            ).order_by(ComplianceNews.issue_date.asc(), ComplianceNews.source).offset(skip).limit(limit).all()
            self.logger.info(f"Found {len(results)} compliance news records for source: {source}")
            return results
        except Exception as e:
            self.logger.error(f"Failed to fetch compliance news by source {source}: {e}")
            raise

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ComplianceNews]:
        """Get all compliance news from all sources"""
        try:
            self.logger.debug(f"Fetching all compliance news, skip: {skip}, limit: {limit}")
            results = self.db.query(ComplianceNews).order_by(
                ComplianceNews.issue_date.desc(), 
                ComplianceNews.source
            ).offset(skip).limit(limit).all()
            self.logger.info(f"Found {len(results)} compliance news records from all sources")
            return results
        except Exception as e:
            self.logger.error(f"Failed to fetch all compliance news: {e}")
            raise

    def get_by_date_range(self, start_date: datetime, end_date: datetime, source: Optional[str] = None, status: Optional[str] = None) -> List[ComplianceNews]:
        """Get compliance news within a date range, optionally filtered by source and status"""
        try:
            query = self.db.query(ComplianceNews).filter(
                ComplianceNews.issue_date >= start_date,
                ComplianceNews.issue_date <= end_date
            )
            
            if source:
                query = query.filter(ComplianceNews.source == source)
                
            if status:
                query = query.filter(ComplianceNews.status == status)
            
            results = query.order_by(ComplianceNews.issue_date.desc(), ComplianceNews.source).all()
            
            filter_desc = f"date range: {start_date} to {end_date}"
            if source:
                filter_desc += f", source: {source}"
            if status:
                filter_desc += f", status: {status}"
                
            self.logger.debug(f"Fetching compliance news by {filter_desc}")
            self.logger.info(f"Found {len(results)} compliance news records for {filter_desc}")
            return results
        except Exception as e:
            self.logger.error(f"Failed to fetch compliance news by date range: {e}")
            raise

    def get_statistics_by_source_and_status(self) -> List[Dict[str, Any]]:
        """Get statistics of compliance news grouped by source and status"""
        try:
            self.logger.debug("Fetching compliance news statistics by source and status")
            # Execute the SQL query equivalent to:
            # SELECT source, status, COUNT(*) as record_count
            # FROM compliance_news
            # GROUP BY source, status
            # ORDER BY source, status;
            from sqlalchemy import func
            
            results = self.db.query(
                ComplianceNews.source,
                ComplianceNews.status,
                func.count().label('record_count')
            ).group_by(
                ComplianceNews.source,
                ComplianceNews.status
            ).order_by(
                ComplianceNews.source,
                ComplianceNews.status
            ).all()
            
            # Convert to list of dictionaries for easier JSON serialization
            statistics = []
            for result in results:
                statistics.append({
                    'source': result.source,
                    'status': result.status,
                    'record_count': result.record_count
                })
            
            self.logger.info(f"Found {len(statistics)} source-status combinations in statistics")
            return statistics
        except Exception as e:
            self.logger.error(f"Failed to fetch compliance news statistics: {e}")
            raise

    def update(self, compliance_news: ComplianceNews) -> Optional[ComplianceNews]:
        """Update compliance news record"""
        if compliance_news.id is None:
            return None
        db_news = self._get_by_id(cast(int, compliance_news.id))
        if db_news:
            db_news.source = compliance_news.source
            db_news.issue_date = compliance_news.issue_date
            db_news.title = compliance_news.title
            db_news.content = compliance_news.content
            db_news.content_url = compliance_news.content_url
            db_news.llm_summary = compliance_news.llm_summary
            db_news.creation_user = compliance_news.creation_user
            db_news.status = compliance_news.status
            self.db.commit()
            self.db.refresh(db_news)
        return db_news

    def update_status_by_id(self, news_id: int, status: str) -> Optional[ComplianceNews]:
        """Update compliance news status by ID"""
        try:
            self.logger.debug(f"Updating status for news ID: {news_id} to status: {status}")
            db_news = self._get_by_id(news_id)
            if db_news:
                db_news.status = status  # type: ignore
                self.db.commit()
                self.db.refresh(db_news)
                self.logger.info(f"Successfully updated status for news ID: {news_id} to status: {status}")
                return db_news
            else:
                self.logger.warning(f"News record not found for ID: {news_id}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to update status for news ID {news_id}: {e}")
            self.db.rollback()
            raise

    def update_title_and_summary_by_id(self, news_id: int, title: Optional[str] = None, llm_summary: Optional[str] = None) -> Optional[ComplianceNews]:
        """Update compliance news title and/or llm_summary by ID"""
        try:
            self.logger.debug(f"Updating title and/or llm_summary for news ID: {news_id}")
            db_news = self._get_by_id(news_id)
            if db_news:
                # Update title if provided
                if title is not None:
                    db_news.title = title  # type: ignore
                    self.logger.debug(f"Updated title for news ID: {news_id}")
                
                # Update llm_summary if provided
                if llm_summary is not None:
                    db_news.llm_summary = llm_summary  # type: ignore
                    self.logger.debug(f"Updated llm_summary for news ID: {news_id}")
                
                # Only commit if at least one field was provided
                if title is not None or llm_summary is not None:
                    self.db.commit()
                    self.db.refresh(db_news)
                    self.logger.info(f"Successfully updated title and/or llm_summary for news ID: {news_id}")
                else:
                    self.logger.warning(f"No fields provided to update for news ID: {news_id}")
                
                return db_news
            else:
                self.logger.warning(f"News record not found for ID: {news_id}")
                return None
        except Exception as e:
            self.logger.error(f"Failed to update title and/or llm_summary for news ID {news_id}: {e}")
            self.db.rollback()
            raise

    def delete(self, compliance_news: ComplianceNews) -> bool:
        """Delete compliance news record"""
        if compliance_news.id is None:
            return False
        db_news = self._get_by_id(cast(int, compliance_news.id))
        if db_news:
            self.db.delete(db_news)
            self.db.commit()
            return True
        return False

