from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from .service_context import ServiceContext
from ..core import CheckResult


class QualityContext:
    """Context for quality checking operations with service integration"""
    
    def __init__(self, service_context: ServiceContext):
        self.services = service_context
        self.current_run_id = None
        self.run_metadata = {}
        self.results_cache = {}
    
    def start_quality_run(self, 
                         run_id: Optional[str] = None,
                         metadata: Dict[str, Any] = None) -> str:
        """Start a new quality checking run"""
        if not run_id:
            run_id = f"qc_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        self.current_run_id = run_id
        self.run_metadata = metadata or {}
        self.results_cache.clear()
        
        # Record run start in MongoDB if available
        if self.services.get_mongo_service():
            self.services.get_mongo_service().save_task_execution({
                'task_id': 'quality_run_start',
                'run_id': run_id,
                'task_type': 'task',
                'status': 'running',
                'started_at': datetime.utcnow(),
                'environment': self.services.environment,
                'parameters': self.run_metadata
            })
        
        return run_id
    
    def save_check_result(self, check_result: CheckResult) -> str:
        """Save a check result and cache it locally"""
        if not self.current_run_id:
            raise RuntimeError("No active quality run. Call start_quality_run() first.")
        
        # Cache result locally
        self.results_cache[check_result.id] = check_result
        
        # Save to services if available
        result_id = None
        if self.services.get_quality_service():
            result_id = self.services.get_quality_service().save_check_result(
                check_result, self.current_run_id
            )
        
        return result_id or check_result.id
    
    def get_cached_result(self, check_id: str) -> Optional[CheckResult]:
        """Get a cached check result"""
        return self.results_cache.get(check_id)
    
    def get_all_cached_results(self) -> Dict[str, CheckResult]:
        """Get all cached results for current run"""
        return self.results_cache.copy()
    
    def finish_quality_run(self) -> Dict[str, Any]:
        """Finish the current quality run and generate report"""
        if not self.current_run_id:
            raise RuntimeError("No active quality run to finish.")
        
        run_id = self.current_run_id
        
        # Generate summary from cached results
        total_checks = len(self.results_cache)
        passed_checks = sum(1 for r in self.results_cache.values() if r.status == 'pass')
        failed_checks = sum(1 for r in self.results_cache.values() if r.status == 'fail')
        error_checks = sum(1 for r in self.results_cache.values() if r.status == 'error')
        skipped_checks = sum(1 for r in self.results_cache.values() if r.status == 'skip')
        
        summary = {
            'run_id': run_id,
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'failed_checks': failed_checks,
            'error_checks': error_checks,
            'skipped_checks': skipped_checks,
            'success_rate': (passed_checks / total_checks * 100) if total_checks > 0 else 0,
            'metadata': self.run_metadata
        }
        
        # Generate full report using quality service
        report = None
        if self.services.get_quality_service():
            report = self.services.get_quality_service().generate_quality_report(run_id)
        
        # Record run completion
        if self.services.get_mongo_service():
            self.services.get_mongo_service().save_task_execution({
                'task_id': 'quality_run_finish',
                'run_id': run_id,
                'task_type': 'task',
                'status': 'completed',
                'started_at': datetime.utcnow(),
                'finished_at': datetime.utcnow(),
                'environment': self.services.environment,
                'output_summary': summary
            })
        
        # Clear current run
        self.current_run_id = None
        self.run_metadata.clear()
        
        return {
            'summary': summary,
            'report': report,
            'cached_results': list(self.results_cache.keys())
        }
    
    def load_data_for_check(self, 
                           check_type: str,
                           table_name: str = None,
                           **kwargs) -> Any:
        """Load data needed for quality checks"""
        sql_service = self.services.get_sql_service()
        if not sql_service:
            raise RuntimeError("SQL service not available for data loading")
        
        if check_type == 'pricing_report':
            return sql_service.load_pricing_report(
                report_date=kwargs.get('report_date'),
                listing_ids=kwargs.get('listing_ids')
            )
        elif check_type == 'featurestore':
            return sql_service.load_featurestore(
                listing_ids=kwargs.get('listing_ids'),
                calendar_dates=kwargs.get('calendar_dates')
            )
        elif check_type == 'bookable_data':
            return sql_service.load_bookable_data(
                listing_ids=kwargs.get('listing_ids')
            )
        elif check_type == 'custom_query':
            return sql_service.execute_custom_query(
                kwargs.get('query', ''),
                kwargs.get('params', {})
            )
        else:
            raise ValueError(f"Unknown check type: {check_type}")
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get table metadata for quality checks"""
        sql_service = self.services.get_sql_service()
        if not sql_service:
            raise RuntimeError("SQL service not available")
        
        return sql_service.get_table_info(table_name)
    
    def save_error_to_database(self, 
                              error_type: str,
                              error_message: str,
                              **kwargs):
        """Save error information to database"""
        sql_service = self.services.get_sql_service()
        if sql_service:
            sql_service.save_error_report(
                error_type=error_type,
                error_message=error_message,
                check_id=kwargs.get('check_id'),
                table_name=kwargs.get('table_name'),
                listing_id=kwargs.get('listing_id'),
                severity=kwargs.get('severity', 'error'),
                metadata=kwargs.get('metadata')
            )
    
    def get_historical_results(self, 
                              check_id: str,
                              days: int = 30) -> List[Dict[str, Any]]:
        """Get historical results for a specific check"""
        mongo_service = self.services.get_mongo_service()
        if not mongo_service:
            return []
        
        from datetime import timedelta
        start_date = datetime.utcnow() - timedelta(days=days)
        
        results = mongo_service.get_check_results(check_id=check_id, limit=100)
        
        # Filter by date
        filtered_results = [
            r for r in results 
            if r['created_at'] >= start_date
        ]
        
        return filtered_results
    
    def run_validation_suite(self, 
                           table_names: List[str],
                           validation_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run comprehensive validation suite"""
        run_id = self.start_quality_run(
            metadata={'validation_suite': True, 'tables': table_names}
        )
        
        try:
            quality_service = self.services.get_quality_service()
            if not quality_service:
                raise RuntimeError("Quality service not available")
            
            # Use quality service validation suite
            suite_results = quality_service.run_data_validation_suite(
                table_names, validation_config or {}
            )
            
            # Finish the run
            run_results = self.finish_quality_run()
            
            return {
                'run_id': run_id,
                'suite_results': suite_results,
                'run_summary': run_results['summary'],
                'full_report': run_results['report']
            }
            
        except Exception as e:
            # Ensure run is finished even on error
            if self.current_run_id:
                self.current_run_id = None
                self.run_metadata.clear()
            raise e
    
    def get_dashboard_data(self, days: int = 7) -> Dict[str, Any]:
        """Get quality dashboard data"""
        quality_service = self.services.get_quality_service()
        if not quality_service:
            return {'error': 'Quality service not available'}
        
        return quality_service.get_quality_dashboard_data(days)
    
    def export_results(self, format: str = 'json', filename: str = None) -> str:
        """Export current run results"""
        if not self.results_cache:
            return "No results to export"
        
        if format.lower() == 'json':
            import json
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = filename or f"quality_results_{timestamp}.json"
            
            export_data = {
                'run_id': self.current_run_id,
                'export_date': datetime.utcnow().isoformat(),
                'total_results': len(self.results_cache),
                'results': [
                    {
                        'check_id': result.id,
                        'status': result.status,
                        'severity': result.severity,
                        'description': result.description,
                        'metrics': result.metrics,
                        'error': result.error,
                        'started_at': result.started_at,
                        'finished_at': result.finished_at
                    }
                    for result in self.results_cache.values()
                ]
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return filename
        
        elif format.lower() == 'csv':
            import pandas as pd
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = filename or f"quality_results_{timestamp}.csv"
            
            df_data = []
            for result in self.results_cache.values():
                row = {
                    'check_id': result.id,
                    'status': result.status,
                    'severity': result.severity,
                    'description': result.description,
                    'error': result.error,
                    'started_at': result.started_at,
                    'finished_at': result.finished_at
                }
                # Add metrics as separate columns
                if result.metrics:
                    for metric_name, metric_value in result.metrics.items():
                        row[f'metric_{metric_name}'] = metric_value
                
                df_data.append(row)
            
            df = pd.DataFrame(df_data)
            df.to_csv(filename, index=False)
            
            return filename
        
        else:
            raise ValueError(f"Unsupported export format: {format}")