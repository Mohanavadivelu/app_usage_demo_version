# App Usage REST API

A comprehensive FastAPI-based REST API for application usage tracking and application catalog management with centralized database operations.

## 🏗️ Architecture Overview

The App Usage REST API follows a modular microservices-inspired architecture with:
- **FastAPI** as the web framework
- **SQLite** with WAL mode for database operations
- **Pydantic** for data validation and serialization
- **Centralized database management** with connection pooling
- **API key-based authentication**
- **Comprehensive error handling and logging**

## 📁 Project Structure

```
rest/
├── main.py                     # FastAPI application entry point
├── requirements.txt            # Python dependencies
├── .env.example               # Environment configuration template
├── README.md                  # This documentation
├── core/                      # Core utilities and shared components
│   ├── __init__.py
│   ├── auth.py                # Authentication and authorization
│   ├── config.py              # Configuration management
│   ├── database.py            # Database connection and management
│   ├── exceptions.py          # Custom exceptions and error handling
│   └── utils.py               # Utility functions
└── services/                  # Business logic services
    ├── __init__.py
    ├── app_usage/             # App usage tracking service
    │   ├── __init__.py
    │   ├── routes.py          # API endpoints
    │   ├── models.py          # Pydantic schemas
    │   ├── crud.py            # Database operations
    │   └── database.py        # Service-specific DB initialization
    └── app_list/              # App catalog management service
        ├── __init__.py
        ├── routes.py          # API endpoints
        ├── models.py          # Pydantic schemas
        ├── crud.py            # Database operations
        └── database.py        # Service-specific DB initialization
```

## 🛠️ Technology Stack

### Backend Framework
- **FastAPI 0.104.1** - Modern, fast web framework for building APIs
- **Uvicorn 0.24.0** - ASGI server for running FastAPI applications
- **Pydantic 2.5.0** - Data validation and settings management

### Database
- **SQLite** - Lightweight, serverless database
- **WAL Mode** - Write-Ahead Logging for better concurrency
- **Connection Pooling** - Custom implementation for efficient connection management

## 🗄️ Database Architecture

### Database Design
The application uses SQLite with Write-Ahead Logging (WAL) mode for improved concurrency and performance, connecting to `../database/app_usage.db`.

### Tables Schema

#### `app_usage`
Stores application usage data and metrics:
```sql
CREATE TABLE app_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    monitor_app_version TEXT NOT NULL CHECK(length(monitor_app_version) <= 50),
    platform TEXT NOT NULL CHECK(length(platform) <= 50),
    user TEXT NOT NULL CHECK(length(user) <= 100),
    application_name TEXT NOT NULL CHECK(length(application_name) <= 100),
    application_version TEXT NOT NULL CHECK(length(application_version) <= 50),
    log_date TEXT NOT NULL,
    legacy_app BOOLEAN NOT NULL,
    duration_seconds INTEGER NOT NULL CHECK(duration_seconds >= 0),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### `app_list`
Stores application catalog and tracking configuration:
```sql
CREATE TABLE app_list (
    app_id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_name TEXT NOT NULL,
    app_type TEXT NOT NULL,
    current_version TEXT NOT NULL,
    released_date TEXT NOT NULL,
    publisher TEXT NOT NULL,
    description TEXT NOT NULL,
    download_link TEXT NOT NULL,
    enable_tracking BOOLEAN NOT NULL,
    track_usage BOOLEAN NOT NULL,
    track_location BOOLEAN NOT NULL,
    track_cm BOOLEAN NOT NULL,
    track_intr INTEGER NOT NULL,
    registered_date TEXT NOT NULL
);
```

### Indexes for Performance
- `idx_app_usage_user` - Index on user field
- `idx_app_usage_date` - Index on log_date field
- `idx_app_usage_app` - Index on application_name field
- `idx_app_list_name_type_version` - Composite index for app identification

## 🔌 API Endpoints

### Authentication
All endpoints require API key authentication via the `X-API-Key-725d9439` header.

### App Usage Endpoints (`/api/v1/app_usage`)

#### `POST /api/v1/app_usage/`
Create new app usage record.
```bash
curl -X POST "http://localhost:8000/api/v1/app_usage/" \
  -H "X-API-Key-725d9439: CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w" \
  -H "Content-Type: application/json" \
  -d '{
    "monitor_app_version": "1.0.1",
    "platform": "windows",
    "user": "vroot",
    "application_name": "chrome",
    "application_version": "138.0.7204.97",
    "log_date": "2025-01-07",
    "legacy_app": true,
    "duration": "00:00:13"
  }'
```

#### `POST /api/v1/app_usage/upsert`
Create or update app usage record (sums durations for existing records).

#### `GET /api/v1/app_usage/`
List all app usage records with pagination.

#### `GET /api/v1/app_usage/{usage_id}`
Get specific app usage record by ID.

#### `PUT /api/v1/app_usage/{usage_id}`
Update existing app usage record.

#### `DELETE /api/v1/app_usage/{usage_id}`
Delete app usage record.

#### `GET /api/v1/app_usage/analytics/{application_name}`
Get analytics for specific application.

#### `GET /api/v1/app_usage/analytics/{application_name}/date-range`
Get analytics for specific application within date range.

#### `GET /api/v1/app_usage/user-analytics/{user}`
Get analytics for specific user.

### App List Endpoints (`/api/v1/app_list`)

#### `POST /api/v1/app_list/`
Create new app list entry.
```bash
curl -X POST "http://localhost:8000/api/v1/app_list/" \
  -H "X-API-Key-725d9439: CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w" \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "notepad",
    "app_type": "windows",
    "current_version": "1.0.0",
    "released_date": "2025-01-01",
    "publisher": "Microsoft",
    "description": "Simple text editor",
    "download_link": "https://microsoft.com/notepad",
    "enable_tracking": true,
    "track": {
      "usage": true,
      "location": false,
      "cpu_memory": {
        "track_cm": false,
        "track_intr": 1
      }
    },
    "registered_date": "2025-01-07"
  }'
```

#### `POST /api/v1/app_list/upsert`
Create or update app list entry.

#### `GET /api/v1/app_list/`
List all app list entries with pagination.

#### `GET /api/v1/app_list/{app_id}`
Get specific app list entry by ID.

#### `PUT /api/v1/app_list/{app_id}`
Update existing app list entry.

#### `DELETE /api/v1/app_list/{app_id}`
Delete app list entry.

#### `GET /api/v1/app_list/by-name/{app_name}`
Get app list entries by app name.

#### `GET /api/v1/app_list/by-type/{app_type}`
Get app list entries by app type.

#### `GET /api/v1/app_list/summary/stats`
Get summary statistics for app list.

### Health Check
#### `GET /health`
Application health check endpoint (no authentication required).

## 🔧 Configuration

### Environment Variables
Create a `.env` file based on `.env.example`:

```env
# Application Configuration
DEBUG=false
ENVIRONMENT=development
LOG_LEVEL=INFO

# Database Configuration
DATABASE_NAME=app_usage.db
DATABASE_MAX_CONNECTIONS=10

# API Configuration
API_TITLE=App Usage REST API
API_VERSION=1.0.0
API_PREFIX=/api/v1

# Authentication Configuration
API_KEY=CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w
API_KEY_NAME=X-API-Key-725d9439

# CORS Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=*

# Server Configuration
HOST=127.0.0.1
PORT=8000
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip for dependency management

### Installation

1. **Navigate to the rest directory**
```bash
cd rest
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment**
```bash
cp .env.example .env
# Edit .env with your configuration if needed
```

4. **Initialize database**
```bash
python -c "from core.database import init_db; init_db()"
```

### Running the Application

#### Development Mode
```bash
python main.py
```

#### Production Mode
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

#### With Auto-reload (Development)
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### API Documentation
Once running, access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔒 Security

### Authentication
- **API Key Authentication**: All endpoints require valid API key
- **Configurable Keys**: API keys can be changed via environment variables
- **Header-based**: API key passed in custom header for security

### Database Security
- **SQL Injection Protection**: Parameterized queries throughout
- **Connection Security**: Secure connection handling with proper cleanup
- **Error Handling**: Sensitive information not exposed in error messages

## 📊 Monitoring & Logging

### Logging
- **Structured Logging**: Comprehensive logging throughout the application
- **Log Levels**: Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- **Context Information**: Rich context in error logs for debugging

### Health Monitoring
- **Health Check Endpoint**: `/health` for application status
- **Database Health**: Connection pool monitoring
- **Error Tracking**: Comprehensive error handling and reporting

## 🛡️ Error Handling

### Custom Exceptions
- **ApplicationError**: Base exception for application-specific errors
- **DatabaseError**: Database operation errors
- **NotFoundError**: Resource not found errors
- **ValidationError**: Data validation errors

### Error Response Format
```json
{
  "error": {
    "message": "Error description",
    "error_code": "ERROR_CODE",
    "details": {},
    "timestamp": "2025-01-07T10:30:00Z"
  }
}
```

## 📈 Performance Considerations

### Database Optimization
- **WAL Mode**: Write-Ahead Logging for better concurrency
- **Connection Pooling**: Efficient connection reuse
- **Indexed Queries**: Strategic indexing for common queries
- **Transaction Management**: Proper transaction boundaries

### API Performance
- **Async Operations**: FastAPI's async capabilities
- **Pagination**: Built-in pagination for list endpoints
- **Efficient Serialization**: Pydantic for fast data serialization

## 🤝 Usage Examples

### Creating App Usage Record
```python
import requests

url = "http://localhost:8000/api/v1/app_usage/"
headers = {
    "X-API-Key-725d9439": "CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w",
    "Content-Type": "application/json"
}
data = {
    "monitor_app_version": "1.0.1",
    "platform": "windows",
    "user": "vroot",
    "application_name": "chrome",
    "application_version": "138.0.7204.97",
    "log_date": "2025-01-07",
    "legacy_app": True,
    "duration": "00:00:13"
}

response = requests.post(url, headers=headers, json=data)
print(f"Created record ID: {response.json()}")
```

### Getting Analytics
```python
import requests

url = "http://localhost:8000/api/v1/app_usage/analytics/chrome"
headers = {
    "X-API-Key-725d9439": "CyRLgKg-FL7RuTtVvb7BPr8wmUoI1PamDj4Xdb3eT9w"
}

response = requests.get(url, headers=headers)
analytics = response.json()
print(f"Chrome usage: {analytics['total_hours']} by {analytics['user_count']} users")
```

## 📝 License

[Add your license information here]

## 📞 Support

For questions, issues, or contributions:
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

## 🔄 Database Schema Application

The database schema is automatically applied when the application starts. To manually apply the schema:

```bash
python -c "from core.database import init_db; init_db()"
```

This will create the `app_usage` and `app_list` tables with proper indexes in the `../database/app_usage.db` file.
