"""
Pricing Report Service for querying SQL/Redshift tables
Following the pattern from dynamic-pricing-strategy/services/report_service.py

This is a SAMPLE project showing how to use QuailTrail with ORM patterns
"""
from models import PricingReport
from quail.context import RedshiftDbContext

class PricingReportService:
    
    def __init__(self, database):
        """Initialize with database context - matches dynamic-pricing-strategy pattern"""
        self.database = database
        
    def get_reports(self, report_date: str = None):
        """
        Get pricing reports, optionally filtered by date
        Similar to get_reports in ReportService
        """
        with RedshiftDbContext(self.database) as session:
            query = session.query(PricingReport)
            
            if report_date:
                query = query.filter(PricingReport.report_date == report_date)
            
            results = query.all()
            return results
    
    def get_reports_by_listing(self, listing_ids: list):
        """
        Get reports for specific listings
        """
        with RedshiftDbContext(self.database) as session:
            results = session.query(PricingReport).filter(
                PricingReport.listing_id.in_(listing_ids)
            ).all()
            return results
    
    def save_quality_data(self, listing_id: str, quality_metrics: dict):
        """
        Save quality metrics for a pricing report
        """
        with RedshiftDbContext(self.database) as session:
            session.query(PricingReport).filter(
                PricingReport.listing_id == listing_id
            ).update({
                PricingReport.quality_score: quality_metrics.get('quality_score'),
                PricingReport.data_completeness: quality_metrics.get('completeness'),
                PricingReport.validation_errors: quality_metrics.get('error_count', 0),
                PricingReport.quality_status: quality_metrics.get('status', 'unknown')
            })
            session.commit()
    
    def check_data_freshness(self, max_age_hours: int = 24):
        """
        Check data freshness based on report dates
        """
        with RedshiftDbContext(self.database) as session:
            from datetime import datetime, timedelta
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            fresh_count = session.query(PricingReport).filter(
                PricingReport.report_date >= cutoff_time
            ).count()
            
            total_count = session.query(PricingReport).count()
            
            return {
                'fresh_records': fresh_count,
                'total_records': total_count,
                'freshness_ratio': fresh_count / total_count if total_count > 0 else 0,
                'cutoff_time': cutoff_time
            }