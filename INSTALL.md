# QuailTrail Installation Guide

## 🚀 Quick Installation

QuailTrail can be installed in several ways depending on your needs and environment.

### Method 1: Standard Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/lbundalian/quail.git
cd quail

# Install in editable mode
pip install -e .
```

### Method 2: Production Installation

```bash
# Install from source (stable)
pip install .
```

### Method 3: With Optional Dependencies

```bash
# For database projects (SQLAlchemy, PostgreSQL, Redshift)
pip install -e ".[database]"

# For MongoDB projects
pip install -e ".[mongodb]"

# For analytics projects (pandas, numpy)
pip install -e ".[analytics]"

# Install everything
pip install -e ".[all]"
```

## 🔧 Usage

QuailTrail can be used in two ways:

### Option 1: Module Command (Always Works)
```bash
python -m quail --help
python -m quail trail my_pipeline
python -m quail nest new_project
```

### Option 2: Direct Command (If CLI installed properly)
```bash
quail --help
quail trail my_pipeline
quail nest new_project
```

**Note:** On Windows, the direct `quail` command may not install due to permission issues. Use `python -m quail` instead.

## ✅ Verify Installation

Run the verification script:
```bash
python verify_installation.py
```

This will check:
- ✅ Python version compatibility (3.10+)
- ✅ QuailTrail package import
- ✅ Core modules functionality
- ✅ CLI availability
- ⚠️ Optional dependencies

## 🎯 Quick Start

1. **Create a new project:**
```bash
python -m quail nest my_data_pipeline
cd my_data_pipeline
```

2. **Run the pipeline:**
```bash
python -m quail trail my_target
```

3. **View execution plan:**
```bash
python -m quail trail --dry-run my_target
```

## 🐛 Troubleshooting

### CLI Command Not Found
If `quail` command is not available:
- **Solution:** Use `python -m quail` instead
- **Cause:** Windows permissions or PATH issues

### Import Errors
If you get import errors:
```bash
# Reinstall in editable mode
pip uninstall quailtrail
pip install -e .
```

### Missing Dependencies
For specific features, install optional dependencies:
```bash
pip install -e ".[database,mongodb,analytics]"
```

### Python Version Issues
QuailTrail requires Python 3.10+:
```bash
python --version  # Should be 3.10 or higher
```

## 📦 Package Structure

After installation, QuailTrail provides:

- **Core Engine:** `quail.core` - Task and check decorators
- **CLI Interface:** `quail.cli` - Command-line interface
- **ORM Support:** `quail.orm` - Database integration
- **Graph Engine:** `quail.graph` - Dependency resolution

## 🌟 Next Steps

1. Check the [Examples](./pricing_quality_pipeline/) directory
2. Read the [Documentation](./README.md)
3. Create your first pipeline with `python -m quail nest`

---

**Need Help?** Open an issue on [GitHub](https://github.com/lbundalian/quail/issues)