"""
PricingReport model for SQL/Redshift table
Following the pattern from dynamic-pricing-strategy/models/report.py

This is a SAMPLE project showing how to use QuailTrail with ORM patterns
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, Numeric

Base = declarative_base()

class PricingReport(Base):
    """
    Pricing report table - equivalent to Report in dynamic-pricing-strategy
    Maps to raw_data.pricing_report table in Redshift
    """
    __tablename__ = 'pricing_report'
    __table_args__ = {'schema': 'raw_data'}

    listing_id = Column(String, primary_key=True)
    client_id = Column(String, primary_key=True) 
    calendar_date = Column(DateTime, primary_key=True)
    report_date = Column(DateTime, primary_key=True)
    available = Column(Boolean)
    bedrooms = Column(Integer)
    bookable_search = Column(Float)
    dist = Column(Float)
    email = Column(String)
    img_score = Column(Float)
    jacuzzi = Column(Integer)
    landscape_views = Column(Integer)
    market_id = Column(Integer)
    min_nights = Column(Integer)
    optimized_price = Column(Float)
    pool = Column(Integer)
    price = Column(Float)
    rating_value = Column(Float)
    review_count = Column(Integer)
    market_share = Column(Float)
    to_optimize = Column(Boolean)
    version = Column(String)
    
    # Additional quality tracking fields
    quality_score = Column(Numeric(5, 2))
    data_completeness = Column(Numeric(5, 2))
    validation_errors = Column(Integer)
    processing_time_ms = Column(Integer)
    data_source = Column(String(50))
    quality_status = Column(String(20))  # 'pass', 'fail', 'warning'