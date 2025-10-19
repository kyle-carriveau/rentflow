# Configuration Module

This module provides environment-specific configurations for the RentFlow application.

## Structure

```
config/
├── __init__.py      # All configuration classes
└── README.md        # This file
```

## Configuration Classes

### Base Config
Common settings shared across all environments.

### DevelopmentConfig
- SQLite database
- Debug mode enabled
- Template auto-reload
- Relaxed security settings

### ProductionConfig
- PostgreSQL database (required)
- Debug mode disabled
- Strict security settings
- Environment variable validation

### TestingConfig
- In-memory SQLite database
- CSRF protection disabled
- Rate limiting disabled
- Isolated test environment

## Usage

### In Application Factory

```python
from config import get_config

def create_app(config_name=None):
    app = Flask(__name__)

    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    config_class.init_app(app)

    # ... rest of initialization
    return app
```

### Environment Selection

Configuration is selected based on (in order of priority):

1. **Explicit parameter**: `create_app('production')`
2. **FLASK_ENV variable**: Set in `.env` or environment
3. **Default**: Falls back to 'development'

### Required Environment Variables

#### All Environments
- `SECRET_KEY`: Flask secret key (generated secure key recommended)

#### Production Only
- `DATABASE_URL`: PostgreSQL connection string
- `RATELIMIT_STORAGE_URL`: Redis URL for rate limiting

#### Optional
- `MAIL_SERVER`, `MAIL_USERNAME`, `MAIL_PASSWORD`: Email configuration
- `UPLOAD_FOLDER`: Custom upload directory
- `MAX_CONTENT_LENGTH`: Maximum upload size in bytes

## Example .env Files

### Development (.env.development)
```bash
FLASK_ENV=development
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///database.db
```

### Production (.env.production)
```bash
FLASK_ENV=production
SECRET_KEY=your-secure-random-key-here
DATABASE_URL=postgresql://user:pass@db:5432/rentflow
RATELIMIT_STORAGE_URL=redis://redis:6379/0
SESSION_COOKIE_SECURE=True
```

### Testing (.env.testing)
```bash
FLASK_ENV=testing
SECRET_KEY=test-secret-key
```

## Adding New Settings

1. Add to `Config` base class if common to all environments
2. Override in specific environment classes if needed
3. Use `env_config()` for environment variable values
4. Provide sensible defaults for development

Example:
```python
class Config:
    NEW_SETTING = env_config('NEW_SETTING', default='default_value')
```

## Migration Notes

To migrate from old configuration style:

1. **Before**: `app.config['KEY'] = config('KEY', default='value')`
2. **After**: Add to Config class in this module
3. **Update**: Change `create_app()` to use `app.config.from_object()`

Old inline configuration will continue to work during migration period.
