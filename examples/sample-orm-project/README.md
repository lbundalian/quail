# Sample ORM Project - QuailTrail Example

This is a **sample project** that demonstrates how to use QuailTrail with the ORM pattern following the `dynamic-pricing-strategy` architecture.

## Architecture Overview

This project shows how to structure a data quality pipeline using QuailTrail when you want to follow the ORM pattern with separate models and services.

### Project Structure

```
sample-orm-project/
├── models/                    # Database models (one file per table/collection)
│   ├── __init__.py           # Package imports
│   ├── featurestore.py       # SQL models for featurestore tables
│   ├── pricing_report.py     # SQL models for pricing report table
│   ├── quality_check.py      # MongoDB models for quality results
│   └── user_properties.py    # MongoDB models for user properties
├── services/                  # Service layer (imports models, uses database contexts)
│   ├── __init__.py           # Package imports
│   ├── featurestore_service.py    # Service for featurestore operations
│   ├── pricing_report_service.py  # Service for pricing report operations
│   ├── property_service.py        # Service for property operations
│   ├── user_service.py            # Service for user operations
│   └── quality_service.py         # Service for quality check operations
├── quail_modules/             # QuailTrail pipeline modules
│   ├── __init__.py           # Package definition
│   └── data_quality.py       # Quality check tasks using the services
└── quail_config.yml          # QuailTrail configuration
```

## How It Works

### 1. Models (`models/`)
Each file represents a table (SQL) or collection (MongoDB):
- **SQL Models**: Use SQLAlchemy `declarative_base` with `__tablename__` and `__table_args__`
- **MongoDB Models**: Use mongoengine `DynamicDocument` with `meta` collection specification

### 2. Services (`services/`)
Each service handles database operations for related models:
- Services are initialized with a database parameter
- Use database context managers for connections
- Import models and query them directly
- Follow the pattern: `with DatabaseContext(database) as session:`

### 3. QuailTrail Modules (`quail_modules/`)
Pipeline tasks and checks that use the services:
- `@qtask` functions for data loading and processing
- `@qcheck` functions for quality validation
- Services are retrieved from context: `ctx.env.get("service_name")`
- Services handle all database interactions

### 4. Configuration (`quail_config.yml`)
QuailTrail configuration that specifies:
- Which modules to load
- Database connection details
- Pipeline targets (which steps to run)
- Parameters and thresholds

## Example Usage

### Running the Sample Pipeline

```bash
# Run the sample pipeline (default target)
quail run

# Or explicitly specify the target
quail run sample_pipeline

# Run with different environment
quail run --profile prod
```

### Key Patterns Demonstrated

1. **Service Initialization**:
```python
# In load_sample_data task
featurestore_service = FeatureStoreService(ctx.env.get("sql_database"))
property_service = PropertyService(ctx.env.get("mongo_database"))
```

2. **Using Services in Quality Checks**:
```python
# In check_featurestore_quality
featurestore_service = ctx.env.get("featurestore_service")
completeness_report = featurestore_service.check_data_completeness(sample_listings)
validation_report = featurestore_service.validate_data_ranges(sample_listings)
```

3. **Database Context Pattern**:
```python
# In services
with RedshiftDbContext(self.database) as session:
    results = session.query(FeatureStore).filter(...).all()
    return results
```

## Benefits of This Approach

1. **Separation of Concerns**: Models define schema, services handle queries, modules orchestrate logic
2. **Reusable Services**: Services can be used across multiple QuailTrail modules
3. **Database Abstraction**: Context managers handle connection lifecycle
4. **Testable**: Services can be easily mocked for testing
5. **Scalable**: Easy to add new models and services as needed

## Requirements

- QuailTrail library
- SQLAlchemy (for SQL models)
- mongoengine (for MongoDB models)
- Database connections configured in `quail_config.yml`

## Extending This Example

To add new functionality:

1. **Add a new table/collection**: Create model in `models/`
2. **Add service methods**: Create or extend service in `services/`
3. **Create quality checks**: Use services in `quail_modules/` tasks
4. **Update config**: Add new targets or parameters as needed

This pattern matches the `dynamic-pricing-strategy` architecture and provides a clean, maintainable way to build data quality pipelines with QuailTrail.