# Requirements Structure

This directory contains modular Python dependencies organized by environment.

## Files

- **base.txt** - Core dependencies required in all environments (Flask, SQLAlchemy, etc.)
- **dev.txt** - Development and testing dependencies (pytest, coverage, etc.)
- **prod.txt** - Production-only dependencies (Gunicorn, psycopg2)

## Usage

### Development
```bash
pip install -r requirements/dev.txt
```

### Production
```bash
pip install -r requirements/prod.txt
```

### Docker Build
The Dockerfile uses `requirements/prod.txt` for production builds.

## Backward Compatibility

The root `requirements.txt` file is maintained for backward compatibility and points to production dependencies.
