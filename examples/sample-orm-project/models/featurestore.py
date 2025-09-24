"""
FeatureStore models for SQL/Redshift tables
Following the pattern from dynamic-pricing-strategy/models/market_features.py

This is a SAMPLE project showing how to use QuailTrail with ORM patterns
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime

Base = declarative_base()

class FeatureStore(Base):
    """
    Main featurestore table - equivalent to MarketFeature in dynamic-pricing-strategy
    Maps to process_data.featurestore table in Redshift
    """
    __tablename__ = 'featurestore'
    __table_args__ = {'schema': 'process_data'}

    listing_id = Column('id', String, primary_key=True)
    price = Column(String)
    review_count = Column(String)
    img_score = Column('weighted_avg_score', Float)
    bedrooms = Column(Integer)
    rating_value = Column(Float)
    min_nights = Column('minnights', Integer)
    pool = Column(Integer)
    tub = Column(Integer)
    views = Column(Integer)
    waterfront = Column(Integer)
    bookable_search = Column(Float)
    available = Column(Boolean)
    calendar_date = Column('calendardate', String, primary_key=True)
    scraped_date = Column(DateTime, primary_key=True)
    
    # Additional quality metrics
    completeness_score = Column(Float)
    data_freshness_hours = Column(Float)
    validation_status = Column(String)


class FeatureStoreAlt(Base):
    """
    Alternative/processed featurestore - equivalent to MarketDummy in dynamic-pricing-strategy
    Maps to process_data.model_data table in Redshift
    """
    __tablename__ = 'model_data'
    __table_args__ = {'schema': 'process_data'}

    listing_id = Column('id', String, primary_key=True)
    price = Column(Float)
    review_count = Column(Integer)
    img_score = Column(Float)
    bedrooms = Column(Integer)
    rating_value = Column(Float)
    min_nights = Column(Integer)
    pool = Column(Integer)
    tub = Column(Integer)
    views = Column(Integer)
    waterfront = Column(Integer)
    bookable_search = Column(Float)
    available = Column(Boolean)
    calendar_date = Column(String, primary_key=True)
    scraped_date = Column(DateTime, primary_key=True)