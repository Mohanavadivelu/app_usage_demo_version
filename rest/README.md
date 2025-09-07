# App Usage RESTful API

A FastAPI-based RESTful API for application usage tracking and management.

## Project Structure

```text
rest/
├── app/
│   ├── __init__.py                     # Makes app a Python package
│   ├── main.py                         # FastAPI application entry point
│   ├── config/
│   │   ├── __init__.py                 # Makes config a Python package
│   │   ├── database.py                 # SQLite database connection and session management
│   │   └── settings.py                 # Environment variables and application configuration
│   ├── core/
│   │   ├── __init__.py                 # Makes core a Python package
│   │   ├── security.py                 # API key validation and authentication
│   │   ├── middleware.py               # Custom middleware (logging, timing, etc.)
│   │   └── exceptions.py               # Custom exception classes and handlers
│   ├── app_usage/                      # App Usage domain
│   │   ├── __init__.py                 # Makes app_usage a Python package
│   │   ├── models.py                   # SQLAlchemy ORM model for app_usage table
│   │   ├── schemas.py                  # Pydantic models for request/response validation
│   │   ├── crud.py                     # Database CRUD operations
│   │   ├── service.py                  # Business logic layer
│   │   └── router.py                   # FastAPI routes and endpoints
│   ├── app_list/                       # App List domain
│   │   ├── __init__.py                 # Makes app_list a Python package
│   │   ├── models.py                   # SQLAlchemy ORM model for app_list table
│   │   ├── schemas.py                  # Pydantic models for request/response validation
│   │   ├── crud.py                     # Database CRUD operations
│   │   ├── service.py                  # Business logic layer
│   │   └── router.py                   # FastAPI routes and endpoints
│   └── auth/
│       ├── __init__.py                 # Makes auth a Python package
│       ├── schemas.py                  # Pydantic models for authentication
│       ├── service.py                  # Authentication business logic
│       └── router.py                   # Authentication endpoints
├── requirements.txt                    # Python dependencies
├── README.md                           # Project documentation
└── run.py                              # Development server launcher

## Features

- **FastAPI Framework**: Modern, fast web framework for building APIs
- **SQLAlchemy ORM**: Object-relational mapping for database operations
- **Pydantic Validation**: Data validation and serialization
- **API Key Authentication**: Simple and secure API key-based authentication
- **Automatic API Documentation**: Interactive Swagger UI and ReDoc
- **Domain-Driven Design**: Organized by business domains (app_usage, app_list)
- **SQLite Database**: Lightweight database for development and small deployments

## File Functionality

### Configuration Files

#### `app/config/settings.py`

- Centralized configuration management using Pydantic BaseSettings
- Environment variable loading with type validation
- API key settings, CORS configuration, database URL

#### `app/config/database.py`

- SQLAlchemy engine and session management
- Database connection setup for SQLite
- Dependency injection for database sessions

### Core Services

#### `app/core/security.py`

- API key validation and management
- Request authentication using API keys
- Security middleware for protected endpoints

#### `app/core/middleware.py`

- Custom middleware for request timing
- Logging and performance monitoring
- Error tracking

#### `app/core/exceptions.py`

- Custom exception classes
- Global error handlers
- Consistent error response formatting

### App Usage Domain

#### `app/app_usage/models.py`

- SQLAlchemy ORM model for app_usage table
- Maps to database schema with constraints
- Automatic timestamp handling

#### `app/app_usage/schemas.py`

- **AppUsageBase**: Common fields for operations
- **AppUsageCreate**: Schema for creating usage records
- **AppUsageUpdate**: Schema for partial updates
- **AppUsageResponse**: API response schema
- **AppUsageStats**: Usage analytics schema

#### `app/app_usage/crud.py`

- Database CRUD operations
- Query optimization and filtering
- Usage statistics calculations

#### `app/app_usage/service.py`

- Business logic layer
- Data aggregation and analytics
- Complex business operations

#### `app/app_usage/router.py`

- FastAPI routes and endpoints
- Request/response validation
- API key authentication integration

### App List Domain

#### `app/app_list/models.py`

- SQLAlchemy ORM model for app_list table
- Application catalog management
- Tracking configuration fields

#### `app/app_list/schemas.py`

- Application registration schemas
- Tracking configuration models
- Search and filtering schemas

#### `app/app_list/crud.py`

- Application catalog operations
- Version management
- Bulk operations support

#### `app/app_list/service.py`

- Application registration logic
- Version conflict resolution
- Publisher verification

#### `app/app_list/router.py`

- Application management endpoints
- Search functionality
- Tracking configuration updates

### Authentication

#### `app/auth/schemas.py`

- API key validation models
- Authentication response schemas
- Error handling models

#### `app/auth/service.py`

- API key validation logic
- Key management utilities
- Authentication middleware

#### `app/auth/router.py`

- API key validation endpoints
- Key management functionality

## API Endpoints

### Authentication

- `POST /api/v1/auth/validate-key` - Validate API key
- `GET /api/v1/auth/keys` - List available API keys (admin only)
- `POST /api/v1/auth/keys` - Generate new API key (admin only)
- `DELETE /api/v1/auth/keys/{key_id}` - Revoke API key (admin only)

### App Usage

- `GET /api/v1/app-usage/` - List usage records (with filtering)
- `POST /api/v1/app-usage/` - Create new usage record
- `GET /api/v1/app-usage/{id}` - Get specific usage record
- `PUT /api/v1/app-usage/{id}` - Update usage record
- `DELETE /api/v1/app-usage/{id}` - Delete usage record
- `GET /api/v1/app-usage/stats` - Get usage statistics

### App List

- `GET /api/v1/app-list/` - List applications (with filtering)
- `POST /api/v1/app-list/` - Register new application
- `GET /api/v1/app-list/{app_id}` - Get application details
- `PUT /api/v1/app-list/{app_id}` - Update application
- `DELETE /api/v1/app-list/{app_id}` - Remove application
- `PUT /api/v1/app-list/{app_id}/tracking` - Update tracking settings
- `GET /api/v1/app-list/search` - Advanced search

## Installation

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

1. **Setup environment variables**

   ```bash
   copy .env.example .env  # Windows
   # cp .env.example .env  # Linux/Mac
   ```

   Edit `.env` file with your configuration.

1. **Run the application**

   ```bash
   python run.py
   # or
   uvicorn app.main:app --reload
   ```

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Database
DATABASE_URL=sqlite:///./app_usage.db

# Security
API_KEYS=app-monitor-key-123:app-monitor,admin-dashboard-key-456:admin-dashboard,analytics-service-key-789:analytics-service
ADMIN_API_KEY=admin-super-secret-key

# API Settings
API_V1_STR=/api/v1
PROJECT_NAME=App Usage API
DEBUG=True

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
```

## API Documentation

Once the server is running, you can access:

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>
- **OpenAPI JSON**: <http://localhost:8000/api/v1/openapi.json>

## Testing with Postman

### Authentication

1. **Get API Key**: Obtain an API key from your administrator or configuration
2. **Set Header**: Add `X-API-Key: your-api-key-here` to request headers
3. **Test Validation**: POST to `/api/v1/auth/validate-key` to verify your key

### Sample Requests

#### Validate API Key

```json
POST /api/v1/auth/validate-key
Headers:
X-API-Key: app-monitor-key-123

Response:
{
  "valid": true,
  "key_name": "app-monitor",
  "permissions": ["read", "write"]
}
```

#### Create Usage Record

```json
POST /api/v1/app-usage/
Headers:
X-API-Key: app-monitor-key-123

{
  "monitor_app_version": "1.0.0",
  "platform": "Windows",
  "user": "john.doe",
  "application_name": "Microsoft Word",
  "application_version": "2021",
  "log_date": "2025-09-07",
  "legacy_app": false,
  "duration_seconds": 3600
}
```

#### Register Application

```json
POST /api/v1/app-list/
Headers:
X-API-Key: admin-dashboard-key-456

{
  "app_name": "Microsoft Word",
  "app_type": "Office Suite",
  "current_version": "2021",
  "released_date": "2021-10-05",
  "publisher": "Microsoft",
  "description": "Word processing application",
  "download_link": "https://office.microsoft.com",
  "enable_tracking": true,
  "track_usage": true,
  "track_location": false,
  "track_cm": true,
  "track_intr": 60,
  "registered_date": "2025-09-07"
}
```

#### Error Response Examples

```json
// Invalid API Key
POST /api/v1/app-usage/
Headers:
X-API-Key: invalid-key

Response (401):
{
  "detail": "Invalid API key",
  "error_code": "INVALID_API_KEY"
}

// Validation Error
POST /api/v1/app-usage/
Headers:
X-API-Key: app-monitor-key-123

{
  "duration_seconds": -100  // Invalid negative value
}

Response (422):
{
  "detail": [
    {
      "loc": ["body", "duration_seconds"],
      "msg": "Duration must be non-negative",
      "type": "value_error"
    }
  ]
}
```

## Development

### Code Structure

- **Domain-Driven Design**: Code organized by business domains
- **Dependency Injection**: Database sessions and authentication
- **Type Safety**: Pydantic models and SQLAlchemy ORM
- **Separation of Concerns**: Models, CRUD/repositories, services, and routers

### Adding New Features

1. Create models in `models.py`
2. Define schemas in `schemas.py`
3. Implement CRUD operations in `crud.py`
4. Add business logic in `service.py`
5. Create API routes in `router.py`
6. Register routes in `main.py`

## Deployment

### Development Server

**Using Uvicorn with Auto-reload:**

```bash
# Start development server with hot reload
uvicorn app.main:app --reload

# With custom host and port
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# With log level
uvicorn app.main:app --reload --log-level debug
```

**Using the run.py script:**

```bash
python run.py
```

**Development Features:**

- ✅ **Auto-reload** - Code changes trigger automatic restart
- ✅ **Fast startup** - Quick development iteration
- ✅ **Debug logging** - Detailed error information
- ✅ **Interactive docs** - Swagger UI at `/docs`

This production uvicorn setup provides excellent performance for your application while maintaining simplicity and reliability! 🚀

## Database Schema

The API works with the following database tables:

### app_usage

- **Purpose**: Stores application usage data and metrics
- **Primary Key**: `id` (INTEGER, AUTO INCREMENT)
- **Key Fields**:
  - `monitor_app_version` (TEXT, max 50 chars) - Version of monitoring application
  - `platform` (TEXT, max 50 chars) - Operating system platform
  - `user` (TEXT, max 100 chars) - Username who used the application
  - `application_name` (TEXT, max 100 chars) - Name of the application used
  - `application_version` (TEXT, max 50 chars) - Version of the application
  - `log_date` (TEXT) - Date when usage was logged
  - `legacy_app` (BOOLEAN) - Whether the application is legacy
  - `duration_seconds` (INTEGER) - Duration of usage in seconds
  - `created_at`, `updated_at` (DATETIME) - Timestamps
- **Indexes**: user, log_date, application_name (for optimized queries)

### app_list

- **Purpose**: Stores application catalog and tracking configuration
- **Primary Key**: `app_id` (INTEGER, AUTO INCREMENT)
- **Key Fields**:
  - `app_name` (TEXT) - Application name
  - `app_type` (TEXT) - Type/category of application
  - `current_version` (TEXT) - Current version of the application
  - `released_date` (TEXT) - Release date
  - `publisher` (TEXT) - Application publisher
  - `description` (TEXT) - Application description
  - `download_link` (TEXT) - Download URL
  - `enable_tracking` (BOOLEAN) - Whether tracking is enabled
  - `track_usage` (BOOLEAN) - Track usage data
  - `track_location` (BOOLEAN) - Track location data
  - `track_cm` (BOOLEAN) - Track configuration management
  - `track_intr` (INTEGER) - Tracking interval in seconds
  - `registered_date` (TEXT) - Registration date

## Security

- **API Key Authentication**: Simple and secure API key-based authentication
- **Key Management**: Configurable API keys with different permission levels
- **CORS**: Configurable cross-origin resource sharing
- **Input Validation**: Pydantic schemas for all inputs
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection

## Performance

- **Database Indexing**: Optimized queries with proper indexes
- **Async Support**: FastAPI async capabilities
- **Connection Pooling**: SQLAlchemy connection management
- **Response Caching**: Configurable caching for frequently accessed data

---

**Next Steps**: Ready for code generation. Let me know when you want to proceed with creating the actual implementation files.
