"""
Sample data quality module using QuailTrail with ORM pattern

This demonstrates how to write QuailTrail modules that use the ORM services
following the dynamic-pricing-strategy pattern.
"""
import pandas as pd
from datetime import datetime
from quail.core import qtask, qcheck, CheckResult

# Import our sample services
from services import FeatureStoreService, PropertyService, PricingReportService, QualityService


@qtask(id="load_sample_data")
def load_sample_data(ctx):
    """
    Load sample data using ORM services
    This shows how to initialize services and load data samples for quality checks
    """
    # Initialize services with database contexts from environment
    featurestore_service = FeatureStoreService(ctx.env.get("sql_database"))
    property_service = PropertyService(ctx.env.get("mongo_database"))
    pricing_service = PricingReportService(ctx.env.get("sql_database"))
    
    # Store services in context for other tasks to use
    ctx.env.put("featurestore_service", featurestore_service)
    ctx.env.put("property_service", property_service)
    ctx.env.put("pricing_service", pricing_service)
    
    try:
        # Load sample listing IDs for testing (in real scenario, these would come from parameters)
        sample_listings = ["listing_001", "listing_002", "listing_003", "listing_004", "listing_005"]
        
        # Use services to load sample data
        featurestore_data = featurestore_service.get_feature_store(sample_listings)
        properties_data = property_service.get_properties_by_id(sample_listings)
        pricing_data = pricing_service.get_reports(ctx.params.get("report_date"))
        
        # Store sample data in context
        ctx.put('sample_listings', sample_listings)
        ctx.put('featurestore_sample', featurestore_data)
        ctx.put('properties_sample', properties_data)
        ctx.put('pricing_sample', pricing_data)
        
        return {
            "sample_listings_count": len(sample_listings),
            "featurestore_records": len(featurestore_data) if featurestore_data else 0,
            "properties_records": len(properties_data) if properties_data else 0,
            "pricing_records": len(pricing_data) if pricing_data else 0,
            "services_initialized": ["featurestore_service", "property_service", "pricing_service"]
        }
        
    except Exception as e:
        return {"error": f"Failed to load sample data: {str(e)}"}


@qcheck(id="check_featurestore_quality", requires=["load_sample_data"], severity="error")
def check_featurestore_data_quality(ctx):
    """
    Check featurestore data quality using the ORM services
    Following the pattern from dynamic-pricing-strategy where services query models directly
    """
    featurestore_service = ctx.env.get("featurestore_service")
    if not featurestore_service:
        return CheckResult(
            id="check_featurestore_quality",
            status="skip",
            description="FeatureStoreService not available"
        )
    
    sample_listings = ctx.get('sample_listings', [])
    if not sample_listings:
        return CheckResult(
            id="check_featurestore_quality",
            status="skip", 
            description="No sample listings available for quality check"
        )
    
    try:
        # Use the service to check data completeness (like get_feature_store in MarketFeatureService)
        completeness_report = featurestore_service.check_data_completeness(sample_listings)
        
        # Use the service to validate data ranges
        validation_report = featurestore_service.validate_data_ranges(sample_listings)
        
        # Calculate overall metrics
        total_records = len(completeness_report)
        avg_completeness = sum(r['completeness_score'] for r in completeness_report) / total_records if total_records > 0 else 0
        
        validation_issues = sum(len(r['validation_issues']) for r in validation_report)
        valid_records = sum(1 for r in validation_report if r['is_valid'])
        
        # Determine status based on thresholds
        completeness_threshold = ctx.params.get('min_completeness', 0.95)
        validation_threshold = ctx.params.get('max_validation_errors', 0)
        
        status = "pass"
        issues = []
        
        if avg_completeness < completeness_threshold:
            status = "fail"
            issues.append(f"Average completeness {avg_completeness:.2f} below threshold {completeness_threshold}")
        
        if validation_issues > validation_threshold:
            status = "fail" 
            issues.append(f"Found {validation_issues} validation issues, threshold is {validation_threshold}")
        
        return CheckResult(
            id="check_featurestore_quality",
            status=status,
            metrics={
                'total_records': total_records,
                'avg_completeness': avg_completeness,
                'validation_issues': validation_issues,
                'valid_records': valid_records,
                'completeness_threshold': completeness_threshold
            },
            description="FeatureStore data quality validation using ORM services",
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
    Check property data quality using PropertyService
    Similar to property validation in dynamic-pricing-strategy
    """
    property_service = ctx.env.get("property_service")
    if not property_service:
        return CheckResult(
            id="check_property_quality",
            status="skip",
            description="PropertyService not available"
        )
    
    sample_listings = ctx.get('sample_listings', [])
    if not sample_listings:
        return CheckResult(
            id="check_property_quality",
            status="skip",
            description="No sample listings available"
        )
    
    try:
        # Get property data using the service (like get_properties_by_id)
        properties = property_service.get_properties_by_id(sample_listings)
        
        # Validate property data
        total_properties = len(properties)
        properties_with_quality_enabled = sum(1 for p in properties if p.get('quality_checks_enabled', False))
        properties_with_recent_checks = sum(1 for p in properties if p.get('last_quality_check'))
        
        avg_quality_score = 0
        if properties:
            quality_scores = [p.get('quality_score', 0) for p in properties if p.get('quality_score') is not None]
            avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Check thresholds
        min_quality_score = ctx.params.get('min_property_quality_score', 0.8)
        min_enabled_percent = ctx.params.get('min_quality_enabled_percent', 0.8)
        
        status = "pass"
        issues = []
        
        if total_properties > 0:
            enabled_percent = properties_with_quality_enabled / total_properties
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
                'enabled_percent': properties_with_quality_enabled / total_properties if total_properties > 0 else 0
            },
            description="Property data quality validation using PropertyService",
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
    Generate a comprehensive quality report using QualityService
    """
    quality_service = QualityService(ctx.env.get("mongo_database"))
    
    try:
        # Get check results from context
        featurestore_result = ctx.get_check_result("check_featurestore_quality")
        property_result = ctx.get_check_result("check_property_quality")
        
        # Generate report using service
        report_data = {
            'run_id': ctx.run_id,
            'timestamp': datetime.utcnow(),
            'checks': [
                {
                    'check_id': 'check_featurestore_quality',
                    'status': featurestore_result.status if featurestore_result else 'unknown',
                    'metrics': featurestore_result.metrics if featurestore_result else {}
                },
                {
                    'check_id': 'check_property_quality', 
                    'status': property_result.status if property_result else 'unknown',
                    'metrics': property_result.metrics if property_result else {}
                }
            ]
        }
        
        # Save report using quality service
        quality_service.save_quality_results(report_data)
        
        return CheckResult(
            id="generate_quality_report",
            status="pass",
            metrics={
                'checks_included': len(report_data['checks']),
                'report_timestamp': report_data['timestamp'].isoformat()
            },
            description="Quality report generated and saved using ORM"
        )
        
    except Exception as e:
        return CheckResult(
            id="generate_quality_report",
            status="error",
            error=f"Report generation failed: {str(e)}",
            description="Quality report generation"
        )