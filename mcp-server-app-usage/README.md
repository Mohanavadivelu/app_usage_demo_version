# MCP App Usage Analytics Server

A comprehensive Model Context Protocol (MCP) server that provides 43 different analytics tools for application usage data analysis. This server connects to your existing app usage database and provides powerful analytics capabilities through the MCP protocol.

## 🚀 Features

The server implements **43 analytics tools** organized into **7 categories**:

### 📊 General (Features 1-7)

- **list_applications**: List all tracked applications with filtering and sorting
- **app_details**: Get detailed information about a specific application
- **tracking_status**: Check which applications have tracking enabled
- **legacy_apps**: List legacy applications
- **recent_releases**: Find applications released in the last X days/months
- **top_publishers**: Show publishers with the most applications
- **app_versions**: List applications with their current versions

### 📈 Usage Statistics (Features 8-14)

- **usage_time_stats**: Get total usage time per application
- **user_count_stats**: Get user counts per application
- **average_usage_time**: Calculate average time per user per application
- **top_apps_by_usage**: Rank applications by total usage time
- **top_apps_by_users**: Rank applications by user count
- **total_usage_period**: Calculate usage totals for time periods
- **platform_usage_stats**: Most used applications per platform

### 👤 User-Centric (Features 15-21)

- **user_applications**: List all applications used by a user
- **user_total_hours**: Calculate total hours for a user across all apps
- **user_app_hours**: Hours spent by user on specific application
- **user_last_app**: Find the last application used by a user
- **user_last_active**: When was a user last active
- **user_top_apps**: Top N applications for a specific user
- **app_users**: List users who have used a specific application

### ⏰ Time-Based (Features 22-28)

- **new_users_count**: Count new users in time periods
- **active_users_count**: Count active users in time periods
- **daily_usage_trend**: Daily usage trends for applications
- **usage_trends**: Weekly/monthly usage trends
- **peak_usage_hours**: Identify peak usage hours
- **onboarding_trend**: Track new application adoptions
- **usage_comparison**: Compare usage between date ranges

### 🔄 Cross-Analysis (Features 29-32)

- **user_app_matrix**: User vs application usage matrix
- **multi_app_users**: Users using multiple applications
- **common_app_combinations**: Applications commonly used together
- **usage_percentage_breakdown**: Usage percentage per app per user

### 🏷️ Version Tracking (Features 33-36)

- **version_usage_breakdown**: Usage statistics by application version
- **legacy_vs_modern**: Compare legacy vs non-legacy app usage
- **outdated_versions**: Identify applications with outdated versions
- **version_distribution**: Version distribution analysis

### 🧠 Advanced Analytics (Features 37-43)

- **session_length_analysis**: Average session length per user/app
- **median_session_length**: Median session length calculations
- **heavy_users**: Identify users with high usage (>X hours/week)
- **inactive_users**: Find users with no recent activity
- **churn_rate_analysis**: Calculate application churn rates
- **new_vs_returning_users**: Analyze new vs returning user patterns
- **growth_trend_analysis**: Application growth trend analysis

## 🏗️ Architecture

```text
mcp-server-app-usage/
├── main.py                          # MCP server entry point
├── config/                          # Configuration management
│   ├── database.py                  # Database connection handling
│   └── settings.py                  # Server settings and logging
├── shared/                          # Shared utilities and models
│   ├── models.py                    # Data models and schemas
│   ├── database_utils.py            # Database query utilities
│   ├── date_utils.py                # Date/time helper functions
│   └── analytics_utils.py           # Analytics calculation helpers
├── general/                         # General application tools
│   ├── tools/                       # Tool implementations
│   └── prompts/                     # Tool documentation
├── usage_stats/                     # Usage statistics tools
├── user_centric/                    # User-focused tools
├── time_based/                      # Time-based analytics tools
├── cross_analysis/                  # Cross-analysis tools
├── version_tracking/                # Version tracking tools
├── advanced/                        # Advanced analytics tools
└── docs/                           # Comprehensive documentation
```text

## 🛠️ Installation

### Prerequisites

- Python 3.13+
- SQLite database with app usage data
- MCP-compatible client (Claude Desktop, etc.)

### Setup

1. **Clone or navigate to the project directory**

   ```bash
   cd mcp-server-app-usage
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt

   # or using uv

   uv sync
   ```

3. **Configure database path**

   The server automatically detects the database at `../database/app_usage.db`

   Or set environment variable:
   ```bash
   export MCP_APP_USAGE_DB_PATH="/path/to/your/app_usage.db"
   ```

4. **Test the server**

   ```bash
   python main.py
   ```

## 📊 Database Schema

The server works with two main tables:

### app_usage

```sql
CREATE TABLE app_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    monitor_app_version TEXT NOT NULL,
    platform TEXT NOT NULL,
    user TEXT NOT NULL,
    application_name TEXT NOT NULL,
    application_version TEXT NOT NULL,
    log_date TEXT NOT NULL,
    legacy_app BOOLEAN NOT NULL,
    duration_seconds INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```text

### app_list

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
```text

## 🔧 Configuration

### Environment Variables

```bash

# Database

MCP_APP_USAGE_DB_PATH="/path/to/database.db"

# Server Settings

MCP_APP_USAGE_LOG_LEVEL="INFO"
MCP_APP_USAGE_MAX_QUERY_RESULTS="1000"
MCP_APP_USAGE_CACHE_ENABLED="true"
MCP_APP_USAGE_CACHE_TTL="300"

# Performance

MCP_APP_USAGE_QUERY_TIMEOUT="30"
MCP_APP_USAGE_CONNECTION_POOL_SIZE="10"

# Security

MCP_APP_USAGE_ENABLE_AUTHENTICATION="false"
MCP_APP_USAGE_RATE_LIMIT_ENABLED="true"
MCP_APP_USAGE_MAX_REQUESTS_PER_MINUTE="100"
```text

## Configuration File

Create `config.json`:
```json
{
  "log_level": "INFO",
  "max_query_results": 1000,
  "cache_enabled": true,
  "cache_ttl": 300,
  "enable_advanced_analytics": true,
  "enable_data_export": true
}
```text

## 🚀 Usage Examples

### Basic Application Listing

```json
{
  "tool": "list_applications",
  "arguments": {
    "limit": 10,
    "sort_by": "released_date",
    "sort_order": "desc"
  }
}
```text

### User Analytics

```json
{
  "tool": "user_total_hours",
  "arguments": {
    "user": "john_doe",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  }
}
```text

### Usage Trends

```json
{
  "tool": "daily_usage_trend",
  "arguments": {
    "application_name": "Chrome Browser",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  }
}
```text

### Top Applications

```json
{
  "tool": "top_apps_by_usage",
  "arguments": {
    "top_n": 10,
    "time_period": "last_30_days"
  }
}
```text

## 📈 Performance

- **Query Optimization**: Indexed database fields for fast queries
- **Connection Pooling**: Efficient database connection management
- **Caching**: Optional result caching for frequently accessed data
- **Rate Limiting**: Configurable request rate limiting
- **Monitoring**: Built-in query performance tracking

## 🔒 Security

- **Parameter Validation**: All inputs are validated and sanitized
- **SQL Injection Protection**: Parameterized queries prevent SQL injection
- **Rate Limiting**: Configurable request rate limiting
- **Authentication**: Optional authentication support
- **Logging**: Comprehensive security event logging

## 📚 Documentation

### Tool Documentation

Each tool includes comprehensive documentation:

- Parameter specifications with examples
- Response format documentation
- Error handling information
- Performance considerations
- Related tools and use cases

### API Reference

- Complete parameter schemas
- Response format specifications
- Error code documentation
- Usage examples for all 43 tools

## 🧪 Testing

```bash

# Run unit tests

python -m pytest tests/

# Test specific category

python -m pytest tests/test_general_tools.py

# Test with coverage

python -m pytest --cov=. tests/
```text

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Update documentation
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Common Issues

1. **Database Connection Error**
  - Verify database path is correct
  - Check database file permissions
  - Ensure database schema matches expected format

2. **Tool Registration Error**
  - Check Python import paths
  - Verify all dependencies are installed
  - Review server logs for specific errors

3. **Performance Issues**
  - Increase connection pool size
  - Enable caching for frequently accessed data
  - Add database indexes for custom queries

### Getting Help

- Check the documentation in the `docs/` directory
- Review tool-specific prompt files
- Enable debug logging for detailed error information
- Check the GitHub issues for known problems

## 🔄 Version History

- **v1.0.0**: Initial release with all 43 analytics tools
- Comprehensive MCP server implementation
- Full documentation and testing suite
- Production-ready configuration options

---

**Built with ❤️ for comprehensive app usage analytics**
