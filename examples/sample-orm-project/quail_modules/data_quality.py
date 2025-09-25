"""
Simplified sample data quality module for QuailTrail demonstration

This demonstrates the structure and concepts of using QuailTrail with ORM patterns.
In a real implementation, you would replace the mock data with actual service calls.
"""
from datetime import datetime
from quail.core import qtask, qcheck, CheckResult


@qtask(id="load_sample_data")
def load_sample_data(ctx):
    """
    Load sample data using ORM services
    
    In real implementation:
    - Initialize your FeatureStoreService, PropertyService, PricingReportService
    - Use services to query your ORM models
    - Store results in context for quality checks
    """
    try:
        # Sample listing IDs for demo
        sample_listings = ["listing_001", "listing_002", "listing_003", "listing_004", "listing_005"]
        
        # Mock data representing what your ORM services would return
        mock_featurestore_data = [
            {"listing_id": "listing_001", "price": 150.0, "bedrooms": 2, "rating": 4.5, "completeness": 0.95},
            {"listing_id": "listing_002", "price": 200.0, "bedrooms": 3, "rating": 4.2, "completeness": 0.88},
            {"listing_id": "listing_003", "price": 120.0, "bedrooms": 1, "rating": 4.8, "completeness": 1.0},
            {"listing_id": "listing_004", "price": 0, "bedrooms": 2, "rating": 3.9, "completeness": 0.75},  # Invalid price
            {"listing_id": "listing_005", "price": 180.0, "bedrooms": 4, "rating": 4.6, "completeness": 0.92}
        ]
        
        mock_properties_data = [
            {"listing_id": "listing_001", "quality_checks_enabled": True, "quality_score": 0.9, "last_check": "2025-09-20"},
            {"listing_id": "listing_002", "quality_checks_enabled": True, "quality_score": 0.85, "last_check": "2025-09-21"},
            {"listing_id": "listing_003", "quality_checks_enabled": False, "quality_score": 0.95, "last_check": None},
            {"listing_id": "listing_004", "quality_checks_enabled": True, "quality_score": 0.7, "last_check": "2025-09-19"},  # Low quality
            {"listing_id": "listing_005", "quality_checks_enabled": True, "quality_score": 0.88, "last_check": "2025-09-22"}
        ]
        
        # Store data in context for quality checks
        ctx.put('sample_listings', sample_listings)
        ctx.put('featurestore_sample', mock_featurestore_data)
        ctx.put('properties_sample', mock_properties_data)
        
        return {
            "sample_listings_count": len(sample_listings),
            "featurestore_records": len(mock_featurestore_data),
            "properties_records": len(mock_properties_data),
            "demo_mode": True,
            "message": "Demo data loaded - replace with real ORM service calls"
        }
        
    except Exception as e:
        return {"error": f"Failed to load sample data: {str(e)}"}


@qcheck(id="check_featurestore_quality", requires=["load_sample_data"], severity="error")
def check_featurestore_data_quality(ctx):
    """
    Check featurestore data quality
    
    In real implementation: Use FeatureStoreService to query models and validate data
    """
    featurestore_data = ctx.get('featurestore_sample', [])
    
    if not featurestore_data:
        return CheckResult(
            id="check_featurestore_quality",
            status="skip",
            description="No featurestore data available"
        )
    
    try:
        # Check data completeness
        total_records = len(featurestore_data)
        avg_completeness = sum(record.get('completeness', 0) for record in featurestore_data) / total_records
        
        # Check for validation issues (e.g., invalid prices)
        validation_issues = sum(1 for record in featurestore_data if record.get('price', 0) <= 0)
        
        # Check against thresholds
        completeness_threshold = ctx.params.get('min_completeness', 0.95)
        max_validation_errors = ctx.params.get('max_validation_errors', 0)
        
        status = "pass"
        issues = []
        
        if avg_completeness < completeness_threshold:
            status = "fail"
            issues.append(f"Average completeness {avg_completeness:.2f} below threshold {completeness_threshold}")
        
        if validation_issues > max_validation_errors:
            status = "fail"
            issues.append(f"Found {validation_issues} validation issues (invalid prices)")
        
        return CheckResult(
            id="check_featurestore_quality",
            status=status,
            metrics={
                'total_records': total_records,
                'avg_completeness': avg_completeness,
                'validation_issues': validation_issues,
                'completeness_threshold': completeness_threshold
            },
            description="FeatureStore data quality validation (DEMO)",
            error="; ".join(issues) if issues else None
        )
        
    except Exception as e:
        return CheckResult(
            id="check_featurestore_quality",
            status="error",
            error=f"Quality check failed: {str(e)}",
            description="FeatureStore data quality validation"
        )


@qcheck(id="check_property_quality", requires=["load_sample_data"], severity="warning")
def check_property_data_quality(ctx):
    """
    Check property data quality
    
    In real implementation: Use PropertyService to query models and validate properties
    """
    properties_data = ctx.get('properties_sample', [])
    
    if not properties_data:
        return CheckResult(
            id="check_property_quality",
            status="skip",
            description="No properties data available"
        )
    
    try:
        total_properties = len(properties_data)
        properties_with_quality_enabled = sum(1 for p in properties_data if p.get('quality_checks_enabled', False))
        properties_with_recent_checks = sum(1 for p in properties_data if p.get('last_check'))
        
        # Calculate average quality score
        quality_scores = [p.get('quality_score', 0) for p in properties_data if p.get('quality_score') is not None]
        avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Check thresholds
        min_quality_score = ctx.params.get('min_property_quality_score', 0.8)
        min_enabled_percent = ctx.params.get('min_quality_enabled_percent', 0.8)
        
        status = "pass"
        issues = []
        
        enabled_percent = properties_with_quality_enabled / total_properties if total_properties > 0 else 0
        if enabled_percent < min_enabled_percent:
            status = "warning"
            issues.append(f"Only {enabled_percent:.1%} of properties have quality checks enabled")
        
        if avg_quality_score < min_quality_score:
            status = "warning" if status == "pass" else status
            issues.append(f"Average quality score {avg_quality_score:.2f} below threshold {min_quality_score}")
        
        return CheckResult(
            id="check_property_quality",
            status=status,
            metrics={
                'total_properties': total_properties,
                'quality_enabled': properties_with_quality_enabled,
                'recent_checks': properties_with_recent_checks,
                'avg_quality_score': avg_quality_score,
                'enabled_percent': enabled_percent
            },
            description="Property data quality validation (DEMO)",
            error="; ".join(issues) if issues else None
        )
        
    except Exception as e:
        return CheckResult(
            id="check_property_quality",
            status="error",
            error=f"Property quality check failed: {str(e)}",
            description="Property data quality validation"
        )


@qcheck(id="generate_quality_report", requires=["check_featurestore_quality", "check_property_quality"], severity="info")
def generate_quality_report(ctx):
    """
    Generate comprehensive quality report
    
    In real implementation: Use QualityService to save results to MongoDB
    """
    try:
        # Get check results from previous steps
        featurestore_result = None  # In real implementation: ctx.get_check_result("check_featurestore_quality")
        property_result = None      # In real implementation: ctx.get_check_result("check_property_quality")
        
        # For demo, create a simple report
        report_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'pipeline': 'sample_pipeline',
            'checks_run': ['check_featurestore_quality', 'check_property_quality'],
            'status': 'completed',
            'demo_mode': True,
            'message': 'In real implementation, this would save to MongoDB using QualityService'
        }
        
        return CheckResult(
            id="generate_quality_report",
            status="pass",
            metrics={
                'checks_included': len(report_data['checks_run']),
                'report_timestamp': report_data['timestamp']
            },
            description="Quality report generated (DEMO)"
        )
        
    except Exception as e:
        return CheckResult(
            id="generate_quality_report",
            status="error",
            error=f"Report generation failed: {str(e)}",
            description="Quality report generation"
        )