# QuailTrail Usage Guide

This guide shows how to use QuailTrail for data quality pipelines.

## 🚀 Basic Usage

### Running QuailTrail
```bash
# Run default target
quail run

# Run specific target
quail run daily

# Run with different profile/environment
quail run --profile prod

# List available targets
quail list

# Show configuration
quail config
python -m quail --help

# Run default pipeline
python -m quail --trail

# Run specific targets  
python -m quail --trail quick full

# Generate project scaffold
python -m quail --nest myproject
```

### Option 3: Windows Batch File
```cmd
# Show help
quail.bat --help

# Run default pipeline
quail.bat --trail

# Generate project scaffold
quail.bat --nest myproject
```

### Option 4: Installed Package (Optional)
```bash
# Install in development mode
pip install -e .

# Then use quail command directly
quail --trail
quail --nest myproject
quail --list
```

## 📋 QuailTrailFile Format

Create a `QuailTrailFile` (like Snakefile) in your project root:

```python
#!/usr/bin/env python3
"""
QuailTrailFile for MyProject
Define your quality checking pipeline here
"""
from quail.core import qtask, qcheck, CheckResult

# Pipeline configuration
config = {
    'env': {
        'service_context': None,  # Will be initialized from quail_config.yaml
    },
    'params': {
        'report_date': '2025-09-24',
        'min_records': 1000,
        'max_error_rate': 0.05,
    },
    'targets': {
        'default': ['setup', 'load_data', 'check_quality'],
        'quick': ['setup', 'check_connections'],
        'full': ['setup', 'load_data', 'check_quality', 'generate_report'],
    },
    'default_target': 'default'
}

@qtask(id="setup")
def setup_pipeline(ctx):
    """Initialize pipeline and test connections"""
    # Your setup code here
    return {'status': 'initialized'}

@qtask(id="load_data", requires=["setup"]) 
def load_data(ctx):
    """Load data for quality checking"""
    # Your data loading code here
    ctx.put('data_loaded', True)
    return {'data_loaded': True, 'record_count': 1000}

@qcheck(id="check_quality", requires=["load_data"], severity="error")
def check_data_quality(ctx):
    """Main data quality check"""
    if not ctx.get('data_loaded', False):
        return CheckResult(
            id="check_quality",
            status="skip",
            description="Data not loaded, skipping quality check"
        )
    
    # Your quality check logic here
    return CheckResult(
        id="check_quality",
        status="pass",  # or "fail", "error", "skip"
        metrics={'completeness': 95.0},
        description="Data quality validation"
    )
```

## 🏗️ Project Scaffold

Generate a complete project structure:

```bash
python quail.py --nest myproject
```

This creates:
- `QuailTrailFile` - Pipeline definition
- `quail_config.yaml` - Configuration 
- `checks/data_quality.py` - Example quality checks
- `.env.example` - Environment template
- `README.md` - Documentation
- `.gitignore` - Git ignore rules

## 📊 Commands

| Command | Description |
|---------|-------------|
| `--trail [targets]` | Run quality pipeline |
| `--nest [project]` | Generate project scaffold |
| `--list` | List available targets |
| `--status` | Show pipeline status |
| `--dry-run` | Show what would execute |
| `--verbose` | Verbose output |

## 🎯 Target Types

- **Individual tasks/checks**: `setup`, `load_data`, `check_quality`
- **Target groups**: `quick`, `default`, `full`
- **Default behavior**: Runs `default` target if none specified

## 💡 Features

✅ **No Installation Required** - Works as direct Python script or module  
✅ **Snakemake-like Interface** - Familiar command structure  
✅ **Project Scaffolding** - Generate complete project templates  
✅ **Target Groups** - Define collections of tasks/checks  
✅ **Dry Run** - Preview what would execute  
✅ **Dependency Resolution** - Automatic task ordering  
✅ **Graceful Fallbacks** - Works with or without full dependencies  
✅ **Multiple Usage Modes** - Script, module, batch, or installed  

## 🔧 Configuration

The `quail_config.yaml` defines:
- Database connections (SQL/MongoDB)
- Quality thresholds and parameters
- Target groups and default behavior
- Environment-specific settings

## 📁 File Structure

```
myproject/
├── QuailTrailFile          # Pipeline definition (like Snakefile)
├── quail_config.yaml       # Configuration
├── checks/                 # Quality check modules
│   └── data_quality.py
├── tasks/                  # Custom task modules
├── config/                 # Additional configurations
├── .env.example           # Environment template
└── README.md              # Documentation
```

## 🌟 Example Usage

```bash
# Generate new project
python quail.py --nest data_validation

cd data_validation

# Copy and edit environment
cp .env.example .env
# Edit .env with your database connections

# Edit quail_config.yaml for your tables and rules

# Run quality checks
python ../quail.py --trail quick    # Quick connection test
python ../quail.py --trail          # Default pipeline  
python ../quail.py --trail full     # Full validation suite

# List what's available
python ../quail.py --list

# Check status
python ../quail.py --status
```

QuailTrail is now ready to use like Snakemake for database quality checking! 🎯