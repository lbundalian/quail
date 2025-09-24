"""
Quality Service for quality check operations using MongoDB
Following the pattern from dynamic-pricing-strategy/services/pricing_service.py

This is a SAMPLE project showing how to use QuailTrail with ORM patterns
"""
from models import QualityCheckResult, QualityRun, QualityMetric
from quail.context import MongoDbContext
from datetime import datetime, timedelta

class QualityService:
    
    def __init__(self, database):
        """Initialize with database context - matches dynamic-pricing-strategy pattern"""
        self.database = database

    def save_quality_results(self, results_data: dict):
        """
        Save quality check results
        Similar to save_quality_results in PricingService
        """
        with MongoDbContext(self.database) as db:
            # Create a quality run record
            quality_run = QualityRun(
                run_id=results_data.get('run_id'),
                pipeline_name=results_data.get('pipeline_name', 'data_quality'),
                target_name=results_data.get('target_name', 'default'),
                status='completed',
                start_time=results_data.get('start_time', datetime.utcnow()),
                end_time=datetime.utcnow(),
                total_checks=len(results_data.get('checks', [])),
                environment=results_data.get('environment', 'dev')
            )
            quality_run.save()
            
            # Save individual check results
            for check_data in results_data.get('checks', []):
                result = QualityCheckResult(
                    check_id=check_data.get('check_id'),
                    run_id=results_data.get('run_id'),
                    status=check_data.get('status'),
                    description=check_data.get('description', ''),
                    timestamp=datetime.utcnow()
                )
                
                # Add metrics if present
                if 'metrics' in check_data:
                    for metric_name, metric_value in check_data['metrics'].items():
                        metric = QualityMetric(
                            metric_name=metric_name,
                            metric_value=float(metric_value) if isinstance(metric_value, (int, float)) else None,
                            status='pass',  # Could be determined based on thresholds
                            timestamp=datetime.utcnow()
                        )
                        result.metrics.append(metric)
                
                result.save()
            
            return quality_run.run_id

    def save_check_result(self, check_id: str, run_id: str, result_data: dict):
        """
        Save individual check result
        """
        with MongoDbContext(self.database) as db:
            result = QualityCheckResult(
                check_id=check_id,
                run_id=run_id,
                status=result_data.get('status'),
                severity=result_data.get('severity', 'info'),
                error_message=result_data.get('error'),
                description=result_data.get('description', ''),
                execution_time_ms=result_data.get('execution_time_ms', 0),
                timestamp=datetime.utcnow()
            )
            result.save()
            return result

    def generate_quality_report(self, lookback_days: int = 7):
        """
        Generate quality report with lookback period
        Similar to generate_quality_report in PricingService with lookback logic
        """
        with MongoDbContext(self.database) as db:
            lookback_date = datetime.utcnow() - timedelta(days=lookback_days)
            
            # Get recent quality runs
            recent_runs = QualityRun.objects(start_time__gte=lookback_date).order_by('-start_time')
            
            # Get recent check results
            recent_results = QualityCheckResult.objects(timestamp__gte=lookback_date)
            
            # Calculate summary statistics
            total_runs = recent_runs.count()
            total_checks = recent_results.count()
            passed_checks = recent_results.filter(status='pass').count()
            failed_checks = recent_results.filter(status='fail').count()
            error_checks = recent_results.filter(status='error').count()
            
            # Calculate success rate
            success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
            
            report = {
                'report_period': {
                    'start_date': lookback_date,
                    'end_date': datetime.utcnow(),
                    'days': lookback_days
                },
                'summary': {
                    'total_runs': total_runs,
                    'total_checks': total_checks,
                    'passed_checks': passed_checks,
                    'failed_checks': failed_checks,
                    'error_checks': error_checks,
                    'success_rate': success_rate
                },
                'recent_runs': [
                    {
                        'run_id': run.run_id,
                        'pipeline_name': run.pipeline_name,
                        'status': run.status,
                        'start_time': run.start_time,
                        'total_checks': run.total_checks
                    } for run in recent_runs[:10]  # Last 10 runs
                ]
            }
            
            return report

    def get_check_history(self, check_id: str, limit: int = 50):
        """
        Get historical results for a specific check
        """
        with MongoDbContext(self.database) as db:
            results = QualityCheckResult.objects(
                check_id=check_id
            ).order_by('-timestamp').limit(limit)
            
            return [
                {
                    'run_id': result.run_id,
                    'status': result.status,
                    'timestamp': result.timestamp,
                    'metrics_count': len(result.metrics) if result.metrics else 0,
                    'error_message': result.error_message
                } for result in results
            ]

    def cleanup_old_results(self, retention_days: int = 30):
        """
        Clean up old quality check results
        """
        with MongoDbContext(self.database) as db:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Delete old results
            deleted_results = QualityCheckResult.objects(timestamp__lt=cutoff_date).delete()
            deleted_runs = QualityRun.objects(start_time__lt=cutoff_date).delete()
            
            return {
                'deleted_results': deleted_results,
                'deleted_runs': deleted_runs,
                'cutoff_date': cutoff_date
            }