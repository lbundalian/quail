<p align="center">
  <img src="quail.png" alt="QuailTrail Logo" width="120"/>
</p>

# QuailTrail

**QuailTrail** is a lightweight, Python-based data quality framework inspired by workflow engines like Snakemake. It provides a clean way to define, execute, and monitor data quality checks and tasks using a modular approach.

---

## 🎯 Key Features

- **Modular Architecture**: Define quality checks and tasks in separate modules
- **ORM Support**: Works seamlessly with your existing ORM patterns (SQLAlchemy, MongoEngine)
- **Configuration-Driven**: Simple YAML configuration for environments and targets
- **Dependency Management**: Automatic task dependency resolution
- **Quality Checks**: Built-in support for data quality validation with severity levels
- **Multiple Targets**: Define different execution pipelines (daily, weekly, validation suites)

---

## 📦 Installation

### Option 1: Install from Source (Recommended for Development)

#### 1. Clone the repository
```bash
git clone https://github.com/lbundalian/quail.git
cd quail
```

#### 2. Create and activate a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
```

#### 3. Install QuailTrail
```bash
# For development (editable install - auto-reflects changes)
pip install -e .

# Or for production use
pip install .
```

### Option 2: Install with Optional Dependencies

QuailTrail supports optional dependencies for different use cases:

```bash
# Install with database support (SQLAlchemy, PostgreSQL, Redshift)
pip install -e ".[database]"

# Install with MongoDB support
pip install -e ".[mongodb]"

# Install with analytics support (pandas, numpy)
pip install -e ".[analytics]"

# Install with all optional dependencies
pip install -e ".[all]"

# Install for development (includes testing, linting tools)
pip install -e ".[dev]"
```

### Option 3: Install Minimal Core Only
```bash
# Minimal installation (just YAML and CLI support)
pip install -e .
```

### Verify Installation
```bash
# Test installation (recommended)
python verify_installation.py

# Check CLI availability (use module form on Windows)
python -m quail --help

# Or direct command (if CLI installed properly)
quail --help

# Create a test project
python -m quail nest my_test_project
cd my_test_project
python -m quail trail --dry-run
```

### Installation Commands Summary
```bash
# Basic installation
pip install -e .

# With database support (recommended for most projects)
pip install -e ".[database,mongodb]"

# Full installation with all features
pip install -e ".[all]"

# Development installation
pip install -e ".[dev]"
```

---

## 🚀 Quick Start

### 1. Configuration (`quail_config.yml`)
Create a configuration file that defines your modules, environments, and targets:

```yaml
profile: dev

modules:
  - quail_modules.data_quality

envs:
  dev:
    sql_database:
      url: your_database_url
      schema: your_schema
    mongo_database:
      url: mongodb://localhost:27017/
      database: your_database

params:
  report_date: ${REPORT_DATE:-2025-09-24}
  min_completeness: 0.95

targets:
  daily:
    - check_pricing_completeness
    - check_pricing_validity
    - generate_quality_report

default_target: "daily"
```

### 2. Define Quality Modules (`quail_modules/`)
Create modules with tasks and checks:

```python
from quail.core import qtask, qcheck, CheckResult

@qtask(id="load_data")
def load_data(ctx):
    # Your data loading logic using ORM services
    return {"records_loaded": 1000}

@qcheck(id="check_completeness", requires=["load_data"], severity="error")
def check_completeness(ctx):
    # Your quality check logic
    return CheckResult(
        id="check_completeness",
        status="pass",
        metrics={"completeness_score": 0.98},
        description="Data completeness validation"
    )
```

### 3. Run QuailTrail
```bash
# Run default target
quail run

# Run specific target
quail run daily

# Run with different profile
quail run --profile prod
```

---

## 📁 Project Structure

```
your-project/
├── quail_config.yml          # Configuration file
├── quail_modules/             # Your quality modules
│   ├── __init__.py
│   └── data_quality.py        # Tasks and checks
└── models/                    # Your ORM models (optional)
    └── services/              # Your service layer (optional)
```

---

## 🔧 ORM Integration

QuailTrail works seamlessly with existing ORM patterns. See the complete example in `examples/sample-orm-project/` that demonstrates:

- **Models**: SQLAlchemy and MongoEngine model definitions
- **Services**: Database service layer with context managers  
- **Integration**: How to use services within QuailTrail tasks

### Example Service Usage
```python
@qtask(id="load_sample_data")
def load_sample_data(ctx):
    # Initialize services with database contexts
    service = FeatureStoreService(ctx.env.get("sql_database"))
    
    # Use service to load data
    data = service.get_feature_store(['listing_001', 'listing_002'])
    
    # Store in context for other tasks
    ctx.put('sample_data', data)
    return {"records_loaded": len(data)}
```

---

## 📖 Documentation

- **[Sample ORM Project](examples/sample-orm-project/README.md)** - Complete example following dynamic-pricing-strategy patterns
- **[Usage Guide](USAGE.md)** - Detailed usage instructions
- **Core Concepts**:
  - `@qtask`: Define data processing tasks
  - `@qcheck`: Define quality validation checks  
  - `CheckResult`: Standardized check result format
  - Context (`ctx`): Pass data between tasks and access configuration

---

## 🎯 Design Philosophy

QuailTrail follows these principles:

1. **Configuration over Code**: Define what to run in YAML, not Python
2. **Separation of Concerns**: Models, services, and pipeline logic are separate
3. **ORM Agnostic**: Works with your existing database patterns
4. **Quality First**: Built-in support for data quality validation
5. **Developer Friendly**: Simple, intuitive Python decorators

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License.
- Environments (e.g. dev, prod)
- Database connections
- Parameters
- Targets / tables

Example `quail.yml`:
```yaml
profile: dev
envs:
  dev:
    url: sqlite:///quail.db
params:
  schema: public
targets:
  daily:
    tasks:
      - reflect_tables
      - run_checks
```

---

## 🚀 Usage

### Run Quail on a workflow
```bash
quail run my_pipeline.ql --config quail.yml --targets daily
```

### Run as a Python module
```bash
python -m quail --config quail.yml
```

### Import in your own code
```python
from quail.core import Runner, qtask, qcheck

@qcheck(id="row_count")
def row_count(ctx):
    # return a CheckResult here
    ...

Runner(config="quail.yml").run("my_pipeline.ql")
```

---

## 🧪 Prototype Example

For local testing you can use `prototype/main.py`:
```python
from quail.core import some_func

if __name__ == "__main__":
    print("Prototype running")
    print(some_func())
```

Run it:
```bash
python prototype/main.py
```

---

## 🧪 Testing

We use **pytest**:
```bash
pip install -e ".[dev]"
pytest -q
```

---

## 📜 License

MIT License © 2025 Linnaeus Bundalian
