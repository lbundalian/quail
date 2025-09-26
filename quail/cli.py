import argparse,sys,os,runpy,yaml,importlib
from .core import Runner,list_nodes
from .orm import build_env_from_cfg

def load_config(path="quail.yml"):
    with open(path) as f: cfg=yaml.safe_load(f) or {}
    profile=os.environ.get("QUAIL_PROFILE") or cfg.get("profile","dev")
    env_cfg=cfg.get("envs",{}).get(profile,{}) 
    params=cfg.get("params",{})
    return cfg,env_cfg,params,profile

def import_trail(cfg,cfg_dir,explicit=None):
    if explicit: importlib.import_module(explicit); return
    if cfg.get("modules"): [importlib.import_module(m) for m in cfg["modules"]]; return
    trail_path=os.path.join(cfg_dir,"Quailtrail")
    if not os.path.isfile(trail_path): sys.exit("No Quailtrail file found")
    runpy.run_path(trail_path,run_name="__quailtrail__")

def cmd_trail(args):
    """Execute QuailTrail data quality pipeline"""
    # Load configuration
    cfg, env_cfg, params, profile = load_config(args.config)
    
    # Override profile if specified
    if hasattr(args, 'profile') and args.profile:
        profile = args.profile
        env_cfg = cfg.get("envs", {}).get(profile, {})
        print(f"🔧 Using profile: {profile}")
    
    # Import pipeline modules
    cfg_dir = os.path.abspath(os.path.dirname(args.config) or ".")
    try:
        import_trail(cfg, cfg_dir, args.module)
    except Exception as e:
        print(f"❌ Failed to import pipeline modules: {e}")
        sys.exit(1)
    
    # Build environment (database connections, etc.)
    try:
        env = build_env_from_cfg(env_cfg.get("orm", {}))
        print(f"🔌 Connected to databases in '{profile}' environment")
    except Exception as e:
        print(f"⚠️  Database connection failed: {e}")
        print("   Continuing with limited functionality...")
        env = {}
    
    # Create runner
    runner = Runner(env, params, progress=True)
    
    # Resolve targets
    if args.targets:
        # Use explicit targets from command line
        target_names = args.targets
        resolved_targets = []
        
        for target in target_names:
            if target in cfg.get("targets", {}):
                # It's a target group - expand it
                resolved_targets.extend(cfg["targets"][target])
                print(f"📂 Expanded target '{target}': {cfg['targets'][target]}")
            else:
                # It's a direct task/check name
                resolved_targets.append(target)
        
        targets = resolved_targets
    else:
        # Use default target
        default_target = cfg.get("default_target") or cfg.get("default_covey", "daily")
        if default_target in cfg.get("targets", {}):
            targets = cfg["targets"][default_target]
            print(f"🎯 Using default target '{default_target}': {targets}")
        else:
            print(f"⚠️  No targets specified and no default target found")
            print("   Available targets:", list(cfg.get("targets", {}).keys()))
            sys.exit(1)
    
    if not targets:
        print("❌ No targets to execute")
        sys.exit(1)
    
    # Show execution plan or run pipeline
    if hasattr(args, 'dry_run') and args.dry_run:
        print("🔍 **Dry Run Mode** - Showing execution plan\n")
        try:
            runner.print_execution_plan(targets)
            print("💡 Use 'quail --trail' (without --dry-run) to execute the pipeline")
        except Exception as e:
            print(f"❌ Failed to generate execution plan: {e}")
            sys.exit(1)
    else:
        # Execute pipeline
        print(f"🚀 **Executing QuailTrail Pipeline**")
        print(f"Targets: {', '.join(targets)}")
        print(f"Profile: {profile}")
        print("")
        
        try:
            results = runner.run(targets)
            
            # Generate report
            try:
                from .reporting.markdown_reporter import print_markdown
                print_markdown(results)
            except ImportError:
                # Fallback simple reporting
                print("\n📊 **Pipeline Results**")
                for name, (result_type, result) in results.items():
                    if result_type == "task":
                        print(f"✅ Task: {name}")
                    elif result_type == "check":
                        status_icon = "✅" if result.status == "pass" else "❌" if result.status == "fail" else "⏭️"
                        print(f"{status_icon} Check: {name} [{result.status}]")
            
            print(f"\n🎉 Pipeline completed successfully!")
            
        except KeyboardInterrupt:
            print(f"\n🛑 Pipeline interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Pipeline failed: {e}")
            import traceback
            if os.getenv("QUAIL_DEBUG"):
                traceback.print_exc()
            sys.exit(1)

def cmd_list(args):
    """List available tasks, checks, and targets in the pipeline"""
    # Load configuration
    cfg, env_cfg, params, profile = load_config(args.config)
    
    # Import pipeline modules
    cfg_dir = os.path.abspath(os.path.dirname(args.config) or ".")
    try:
        import_trail(cfg, cfg_dir, args.module)
    except Exception as e:
        print(f"❌ Failed to import pipeline modules: {e}")
        sys.exit(1)
    
    # Get available nodes
    nodes = list_nodes()
    
    print("🐦 **QuailTrail Pipeline Overview**")
    print(f"Configuration: {args.config}")
    print(f"Project: {cfg.get('project', 'Unknown')}")
    print(f"Profile: {profile}")
    print("")
    
    # Show targets (workflow definitions)
    targets = cfg.get("targets", {})
    if targets:
        print("🎯 **Available Targets:**")
        default_target = cfg.get("default_target") or cfg.get("default_covey")
        
        for target_name, target_steps in targets.items():
            default_marker = " (default)" if target_name == default_target else ""
            print(f"  • **{target_name}**{default_marker}")
            for step in target_steps:
                step_type = "task" if step in nodes["tasks"] else "check" if step in nodes["checks"] else "unknown"
                icon = "📋" if step_type == "task" else "✅" if step_type == "check" else "❓"
                print(f"    {icon} {step} [{step_type}]")
        print("")
    
    # Show all tasks
    if nodes["tasks"]:
        print("📋 **Available Tasks:**")
        for task_name in sorted(nodes["tasks"]):
            # Try to get task metadata
            from .core import _TASKS
            if task_name in _TASKS:
                task_func = _TASKS[task_name]
                meta = getattr(task_func, '__qmeta__', {})
                requires = meta.get('requires', [])
                
                deps_info = f" (depends on: {', '.join(requires)})" if requires else ""
                print(f"  • {task_name}{deps_info}")
            else:
                print(f"  • {task_name}")
        print("")
    
    # Show all checks
    if nodes["checks"]:
        print("✅ **Available Checks:**")
        for check_name in sorted(nodes["checks"]):
            # Try to get check metadata
            from .core import _CHECKS
            if check_name in _CHECKS:
                check_func = _CHECKS[check_name]
                meta = getattr(check_func, '__qmeta__', {})
                requires = meta.get('requires', [])
                severity = meta.get('severity', 'unknown')
                
                deps_info = f" (depends on: {', '.join(requires)})" if requires else ""
                print(f"  • {check_name} [{severity}]{deps_info}")
            else:
                print(f"  • {check_name}")
        print("")
    
    # Show parameters
    if params:
        print("⚙️  **Configuration Parameters:**")
        for key, value in sorted(params.items()):
            # Hide sensitive values
            if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                value = "***HIDDEN***"
            print(f"  • {key}: {value}")
        print("")
    
    # Show database connections
    orm_config = env_cfg.get("orm", {})
    if orm_config:
        print("🔌 **Database Connections:**")
        for db_type, db_config in orm_config.items():
            if isinstance(db_config, dict) and 'url' in db_config:
                # Hide credentials in URL
                url = db_config['url']
                if '@' in url:
                    # Replace credentials with ***
                    parts = url.split('@')
                    if '://' in parts[0]:
                        protocol_user = parts[0].split('://')
                        url = f"{protocol_user[0]}://***@{parts[1]}"
                print(f"  • {db_type}: {url}")
        print("")
    
    # Usage examples
    print("💻 **Usage Examples:**")
    if targets:
        example_target = list(targets.keys())[0]
        print(f"  quail --trail {example_target}    # Run specific target")
    print(f"  quail --trail                     # Run default target")
    print(f"  quail --trail --dry-run           # Show execution plan")
    if nodes["tasks"]:
        example_task = list(nodes["tasks"])[0]
        print(f"  quail --trail {example_task}      # Run single task")
    print("")

def cmd_nest(args):
    """Create a new QuailTrail data quality project scaffold"""
    import os
    from pathlib import Path
    
    project_name = args.name if hasattr(args, 'name') and args.name else "quail_project"
    
    # Create project structure
    dirs = [
        f"{project_name}",
        f"{project_name}/models",
        f"{project_name}/services", 
        f"{project_name}/quail_modules",
        f"{project_name}/tests"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {dir_path}")
    
    # Create quail.yml configuration
    config_content = f'''# QuailTrail Data Quality Pipeline Configuration
project: {project_name}
profile: dev
default_target: daily_checks

# Database environments
envs:
  dev:
    # SQL Database (Redshift/PostgreSQL)
    sql_database:
      url: ${{DB_URL:-postgresql://user:pass@localhost:5432/quail_dev}}
      schema: raw_data
      engine_options:
        pool_pre_ping: true
        pool_size: 5
        max_overflow: 10
    
    # MongoDB (optional)
    mongo_database:
      url: ${{MONGO_URL:-mongodb://localhost:27017/}}
      database: {project_name}_dev
      timeout_minutes: 60
  
  prod:
    sql_database:
      url: ${{PROD_DB_URL}}
      schema: production
      engine_options:
        pool_pre_ping: true
        pool_size: 20
        max_overflow: 50
    
    mongo_database:
      url: ${{PROD_MONGO_URL}}
      database: {project_name}_prod
      timeout_minutes: 120

# Quality check parameters
params:
  # Data extraction
  report_date: ${{REPORT_DATE}}
  batch_size: 1000
  
  # Quality thresholds
  completeness_threshold: 0.95
  price_validity_threshold: 0.0
  multiplier_z_threshold: 2.5
  min_rows_for_stats: 200
  
  # Business rules
  min_listing_count: 5
  max_price_deviation: 0.2

# Pipeline modules (your quality checks)
modules:
  - quail_modules.data_quality

# Workflow targets
targets:
  # Daily quality checks
  daily_checks:
    - extract_data
    - validate_completeness
    - check_data_quality
    - generate_report
  
  # Quick validation
  quick:
    - extract_data
    - validate_completeness
  
  # Full quality suite
  full_quality:
    - extract_data
    - validate_completeness
    - check_data_quality
    - check_business_rules
    - detect_anomalies
    - generate_comprehensive_report

# Default target when running 'quail --trail'
default_target: daily_checks
'''
    
    config_path = f"{project_name}/quail.yml"
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_content)
    print(f"📝 Created configuration: {config_path}")
    
    # Create sample models
    model_content = '''# models/data_models.py - SQLAlchemy and MongoEngine models
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from mongoengine import Document, StringField, FloatField, DateTimeField, BooleanField

# SQLAlchemy Base
SQLBase = declarative_base()

class FeaturestoreRecord(SQLBase):
    """Example SQL model for feature store data"""
    __tablename__ = 'featurestore'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(String(50))
    listing_id = Column(String(50))
    report_date = Column(DateTime)
    completeness = Column(Float)
    optimized_price = Column(Float)
    multiplier = Column(Float)

class PricingReport(SQLBase):
    """Example SQL model for pricing reports"""
    __tablename__ = 'pricing_report'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(String(50))
    listing_id = Column(String(50))
    calendar_date = Column(DateTime)
    report_date = Column(DateTime)
    optimized_price = Column(Float)
    expected_revenue = Column(Float)
    price = Column(Float)
    multiplier = Column(Float)

# MongoDB Models
class PropertyQuality(Document):
    """Example MongoDB model for property quality data"""
    meta = {'collection': 'property_quality'}
    
    property_id = StringField(required=True)
    quality_score = FloatField()
    quality_enabled = BooleanField(default=True)
    last_updated = DateTimeField()
'''
    
    model_path = f"{project_name}/models/data_models.py"
    with open(model_path, "w", encoding="utf-8") as f:
        f.write(model_content)
    print(f"🏗️  Created models: {model_path}")
    
    # Create sample services
    service_content = '''# services/data_services.py - Service layer for database operations
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select
from mongoengine import connect

class FeaturestoreService:
    """Service for accessing feature store data"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_completeness_data(self, report_date: Optional[datetime] = None) -> List[Dict]:
        """Get completeness data for quality checking"""
        from models.data_models import FeaturestoreRecord
        
        query = select(FeaturestoreRecord)
        if report_date:
            query = query.where(FeaturestoreRecord.report_date == report_date)
        
        results = self.db.execute(query).scalars().all()
        return [{{
            'client_id': r.client_id,
            'listing_id': r.listing_id,
            'completeness': r.completeness,
            'optimized_price': r.optimized_price,
            'multiplier': r.multiplier
        }} for r in results]

class PricingService:
    """Service for accessing pricing data"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_pricing_reports(self, report_date: Optional[datetime] = None) -> pd.DataFrame:
        """Get pricing reports as DataFrame for analysis"""
        from models.data_models import PricingReport
        
        query = select(PricingReport)
        if report_date:
            query = query.where(PricingReport.report_date == report_date)
        
        results = self.db.execute(query).scalars().all()
        
        data = []
        for r in results:
            data.append({{
                'client_id': r.client_id,
                'listing_id': r.listing_id,
                'calendar_date': r.calendar_date,
                'optimized_price': r.optimized_price,
                'multiplier': r.multiplier,
                'expected_revenue': r.expected_revenue
            }})
        
        return pd.DataFrame(data)

class PropertyService:
    """Service for accessing property quality data (MongoDB)"""
    
    def __init__(self, mongo_url: str, database: str):
        connect(database, host=mongo_url)
    
    def get_quality_scores(self) -> List[Dict]:
        """Get property quality scores"""
        from models.data_models import PropertyQuality
        
        properties = PropertyQuality.objects.all()
        return [{{
            'property_id': p.property_id,
            'quality_score': p.quality_score,
            'quality_enabled': p.quality_enabled,
            'last_updated': p.last_updated
        }} for p in properties]
'''
    
    service_path = f"{project_name}/services/data_services.py"
    with open(service_path, "w", encoding="utf-8") as f:
        f.write(service_content)
    print(f"🔧 Created services: {service_path}")
    
    # Create sample quality checks module
    quality_module = f'''# quail_modules/data_quality.py - QuailTrail quality checks
import pandas as pd
from datetime import datetime
from typing import Dict, Any
from quail.core import qtask, qcheck, CheckResult

@qtask(id="extract_data", requires=[])
def extract_data(ctx):
    """Extract data using ORM services"""
    print("📊 Extracting data from databases...")
    
    # Get database connections from context
    service_context = ctx.env.get("service_context")
    
    if service_context:
        # Use your service pattern
        with service_context.sql_context as db:
            from services.data_services import FeaturestoreService, PricingService
            
            fs_service = FeaturestoreService(db.session)
            pricing_service = PricingService(db.session)
            
            # Extract data
            completeness_data = fs_service.get_completeness_data()
            pricing_df = pricing_service.get_pricing_reports()
            
            print(f"✅ Extracted {{len(completeness_data)}} completeness records")
            print(f"✅ Extracted {{len(pricing_df)}} pricing records")
            
            return {{
                "completeness_data": completeness_data,
                "pricing_data": pricing_df,
                "extraction_time": datetime.now().isoformat()
            }}
    else:
        # Mock data for demo
        print("⚠️  Using mock data (no database connection)")
        return {{
            "completeness_data": [
                {{"client_id": "C001", "completeness": 0.95, "optimized_price": 150.0}},
                {{"client_id": "C002", "completeness": 0.88, "optimized_price": 200.0}},
            ],
            "pricing_data": pd.DataFrame({{
                "client_id": ["C001", "C002"],
                "multiplier": [1.2, 0.8],
                "optimized_price": [150.0, 200.0]
            }}),
            "extraction_time": datetime.now().isoformat()
        }}

@qcheck(id="validate_completeness", requires=["extract_data"], severity="error")
def validate_completeness(ctx):
    """Check data completeness meets quality thresholds"""
    print("🔍 Validating data completeness...")
    
    data = ctx.get("extract_data")
    if not data:
        return CheckResult(
            id="validate_completeness",
            status="error",
            description="No data available for completeness check"
        )
    
    completeness_data = data.get("completeness_data", [])
    threshold = ctx.params.get("completeness_threshold", 0.95)
    
    if not completeness_data:
        return CheckResult(
            id="validate_completeness",
            status="fail",
            metrics={{"reason": "No completeness data found"}},
            description="Data completeness validation failed - no data"
        )
    
    # Calculate completeness metrics
    total_records = len(completeness_data)
    complete_records = len([r for r in completeness_data if r.get("completeness", 0) >= threshold])
    completeness_rate = complete_records / total_records if total_records > 0 else 0
    
    status = "pass" if completeness_rate >= 0.9 else "fail"
    
    return CheckResult(
        id="validate_completeness",
        status=status,
        metrics={{
            "total_records": total_records,
            "complete_records": complete_records,
            "completeness_rate": completeness_rate,
            "threshold": threshold
        }},
        description=f"Completeness check: {{completeness_rate:.1%}} of records meet {{threshold:.1%}} threshold"
    )

@qcheck(id="check_data_quality", requires=["extract_data"], severity="warning") 
def check_data_quality(ctx):
    """Advanced data quality checks"""
    print("🎯 Running advanced quality checks...")
    
    data = ctx.get("extract_data")
    pricing_df = data.get("pricing_data")
    
    if pricing_df is None or pricing_df.empty:
        return CheckResult(
            id="check_data_quality",
            status="skip",
            description="No pricing data for quality analysis"
        )
    
    # Check for price anomalies
    if "optimized_price" in pricing_df.columns:
        prices = pricing_df["optimized_price"].dropna()
        invalid_prices = len(prices[prices <= 0])
        price_validity_rate = 1 - (invalid_prices / len(prices)) if len(prices) > 0 else 0
    else:
        invalid_prices = 0
        price_validity_rate = 1.0
    
    # Check multiplier distribution
    multiplier_issues = 0
    if "multiplier" in pricing_df.columns:
        multipliers = pricing_df["multiplier"].dropna()
        z_threshold = ctx.params.get("multiplier_z_threshold", 2.5)
        
        if len(multipliers) > 0:
            # Simple outlier detection
            mean_mult = multipliers.mean()
            std_mult = multipliers.std()
            if std_mult > 0:
                z_scores = abs((multipliers - mean_mult) / std_mult)
                multiplier_issues = len(z_scores[z_scores > z_threshold])
    
    total_issues = invalid_prices + multiplier_issues
    status = "pass" if total_issues == 0 else "warning" if total_issues < 5 else "fail"
    
    return CheckResult(
        id="check_data_quality",
        status=status,
        metrics={{
            "invalid_prices": invalid_prices,
            "price_validity_rate": price_validity_rate,
            "multiplier_outliers": multiplier_issues, 
            "total_issues": total_issues
        }},
        description=f"Quality analysis found {{total_issues}} issues in data"
    )

@qtask(id="generate_report", requires=["validate_completeness", "check_data_quality"])
def generate_report(ctx):
    """Generate quality summary report"""
    print("📋 Generating quality report...")
    
    completeness_result = ctx.get("validate_completeness")
    quality_result = ctx.get("check_data_quality") 
    
    report = {{
        "report_timestamp": datetime.now().isoformat(),
        "checks_run": 2,
        "checks_passed": 0,
        "checks_failed": 0,
        "checks_warnings": 0,
        "summary": {{}}
    }}
    
    # Summarize check results
    for check_result in [completeness_result, quality_result]:
        if check_result and hasattr(check_result, 'status'):
            if check_result.status == "pass":
                report["checks_passed"] += 1
            elif check_result.status == "fail":
                report["checks_failed"] += 1
            elif check_result.status == "warning":
                report["checks_warnings"] += 1
            
            report["summary"][check_result.id] = {{
                "status": check_result.status,
                "metrics": getattr(check_result, 'metrics', {{}})
            }}
    
    print(f"✅ Report generated: {{report['checks_passed']}} passed, {{report['checks_failed']}} failed, {{report['checks_warnings']}} warnings")
    
    return report
'''
    
    quality_path = f"{project_name}/quail_modules/data_quality.py"
    with open(quality_path, "w", encoding="utf-8") as f:
        f.write(quality_module)
    print(f"✅ Created quality module: {quality_path}")
    
    # Create __init__.py files
    for init_dir in ["models", "services", "quail_modules"]:
        init_path = f"{project_name}/{init_dir}/__init__.py"
        with open(init_path, "w", encoding="utf-8") as f:
            f.write("")
        print(f"📦 Created package: {init_path}")
    
    # Create README
    readme_content = f'''# {project_name.title()} - QuailTrail Data Quality Pipeline

This project uses **QuailTrail** - an independent workflow orchestration engine for data quality checks using ORM-based services.

## Project Structure

```
{project_name}/
├── quail.yml                   # Pipeline configuration
├── models/                     # SQLAlchemy & MongoEngine models
│   └── data_models.py
├── services/                   # Database service layer  
│   └── data_services.py
├── quail_modules/              # Quality check modules
│   └── data_quality.py
└── tests/                      # Test files
```

## Quick Start

1. **Configure your databases** in `quail.yml`
2. **Define your models** in `models/data_models.py`
3. **Create services** in `services/data_services.py` 
4. **Write quality checks** in `quail_modules/data_quality.py`

## Running the Pipeline

```bash
# Run daily quality checks
quail --trail

# Run specific target
quail --trail daily_checks

# Run quick validation only
quail --trail quick

# List available tasks and checks
quail --list

# Show help
quail --help
```

## Available Targets

- **daily_checks**: Complete daily quality pipeline
- **quick**: Fast validation checks only
- **full_quality**: Comprehensive quality analysis

## Configuration

Edit `quail.yml` to:
- Set database connection strings
- Adjust quality thresholds
- Configure pipeline parameters
- Define workflow targets

## Adding New Quality Checks

1. Create new `@qcheck` functions in `quail_modules/data_quality.py`
2. Add dependencies using `requires=["other_task"]`
3. Return `CheckResult` objects with metrics
4. Add to pipeline targets in `quail.yml`

## ORM Integration

QuailTrail integrates with your existing ORM patterns:
- **SQLAlchemy** for SQL databases (PostgreSQL, Redshift)
- **MongoEngine** for MongoDB
- **Service layer** for clean database abstraction
- **Context managers** for connection handling

Built with ❤️ using QuailTrail
'''
    
    readme_path = f"{project_name}/README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"📖 Created README: {readme_path}")
    
    print(f"\n🎉 Successfully created QuailTrail project: {project_name}")
    print(f"\nNext steps:")
    print(f"1. cd {project_name}")
    print(f"2. Edit quail.yml with your database connections")
    print(f"3. Customize models and services for your data")
    print(f"4. Run: quail --trail")
    print(f"\n🚀 Happy data quality checking!")

def main():
    """QuailTrail - Data Quality Pipeline Orchestration Tool"""
    p = argparse.ArgumentParser(
        "quail", 
        description="QuailTrail: Data quality pipeline orchestration with ORM integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  quail --trail                    # Run default target  
  quail --trail daily_checks       # Run specific target
  quail --trail extract_data       # Run single task
  quail --list                     # Show available tasks
  quail --nest my_project          # Create new project
  
QuailTrail is an independent workflow orchestration engine specifically 
designed for data quality pipelines using ORM patterns with SQLAlchemy and MongoEngine.
        """
    )
    
    sub = p.add_subparsers(dest="cmd", help="Available commands")
    
    # Trail command - main execution
    t = sub.add_parser("trail", help="Execute data quality pipeline")
    t.add_argument("targets", nargs="*", help="Pipeline targets to execute")
    t.add_argument("--config", default="quail.yml", help="Configuration file (default: quail.yml)")
    t.add_argument("--module", help="Python module to import explicitly")
    t.add_argument("--dry-run", action="store_true", help="Show execution plan without running")
    t.add_argument("--profile", help="Override configuration profile")
    t.set_defaults(func=cmd_trail)
    
    # List command - introspection
    l = sub.add_parser("list", help="List available tasks, checks, and targets")
    l.add_argument("--config", default="quail.yml", help="Configuration file")
    l.add_argument("--module", help="Python module to import explicitly") 
    l.set_defaults(func=cmd_list)
    
    # Nest command - project scaffolding
    n = sub.add_parser("nest", help="Create new QuailTrail project")
    n.add_argument("name", nargs="?", default="quail_project", help="Project name (default: quail_project)")
    n.set_defaults(func=cmd_nest)
    
    # Support direct execution (no command specified)
    if len(sys.argv) > 1 and sys.argv[1] not in {"trail", "list", "nest"}:
        sys.argv.insert(1, "trail")
    
    args = p.parse_args()
    
    if not getattr(args, "func", None):
        p.print_help()
        sys.exit(0)
    
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n🛑 Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        sys.exit(1)
