# MCP App Usage Analytics Server - Deployment Guide

This guide provides comprehensive instructions for deploying and configuring the MCP App Usage Analytics Server in production environments.

## 🚀 Quick Start

### Prerequisites
- Python 3.13 or higher
- SQLite database with app usage data
- MCP-compatible client (Claude Desktop, etc.)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd mcp-server-app-usage

# Install dependencies
pip install -e .
# or using uv
uv sync

# Verify installation
python main.py --help
```

## 📊 Database Setup

### Database Schema Validation
The server expects two main tables:

```sql
-- Verify your database has these tables
.schema app_usage
.schema app_list

-- Check data availability
SELECT COUNT(*) FROM app_usage;
SELECT COUNT(*) FROM app_list;
```

### Database Configuration
Set the database path using environment variables:

```bash
# Option 1: Environment variable
export MCP_APP_USAGE_DB_PATH="/path/to/your/app_usage.db"

# Option 2: Configuration file
echo '{"db_path": "/path/to/your/app_usage.db"}' > config.json
```

## ⚙️ Configuration

### Environment Variables
```bash
# Database Configuration
export MCP_APP_USAGE_DB_PATH="/path/to/database.db"

# Server Settings
export MCP_APP_USAGE_LOG_LEVEL="INFO"
export MCP_APP_USAGE_MAX_QUERY_RESULTS="1000"
export MCP_APP_USAGE_CACHE_ENABLED="true"
export MCP_APP_USAGE_CACHE_TTL="300"

# Performance Tuning
export MCP_APP_USAGE_QUERY_TIMEOUT="30"
export MCP_APP_USAGE_CONNECTION_POOL_SIZE="10"

# Security Settings
export MCP_APP_USAGE_RATE_LIMIT_ENABLED="true"
export MCP_APP_USAGE_MAX_REQUESTS_PER_MINUTE="100"
```

### Configuration File
Create `config.json` for persistent settings:

```json
{
  "log_level": "INFO",
  "max_query_results": 1000,
  "cache_enabled": true,
  "cache_ttl": 300,
  "query_timeout": 30,
  "connection_pool_size": 10,
  "enable_advanced_analytics": true,
  "enable_data_export": true,
  "rate_limit_enabled": true,
  "max_requests_per_minute": 100
}
```

## 🔧 MCP Client Configuration

### Claude Desktop Configuration
Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "app-usage-analytics": {
      "command": "python",
      "args": ["/path/to/mcp-server-app-usage/main.py"],
      "env": {
        "MCP_APP_USAGE_DB_PATH": "/path/to/your/app_usage.db",
        "MCP_APP_USAGE_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Other MCP Clients
For other MCP clients, use the stdio transport:

```bash
# Start the server
python main.py

# The server will listen on stdin/stdout for MCP protocol messages
```

## 🏗️ Production Deployment

### Docker Deployment
Create `Dockerfile`:

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY . .

RUN pip install -e .

# Create non-root user
RUN useradd -m -u 1000 mcpuser
USER mcpuser

CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t mcp-app-usage-server .
docker run -v /path/to/database:/data -e MCP_APP_USAGE_DB_PATH=/data/app_usage.db mcp-app-usage-server
```

### Systemd Service
Create `/etc/systemd/system/mcp-app-usage.service`:

```ini
[Unit]
Description=MCP App Usage Analytics Server
After=network.target

[Service]
Type=simple
User=mcpuser
WorkingDirectory=/opt/mcp-server-app-usage
ExecStart=/usr/bin/python3 main.py
Environment=MCP_APP_USAGE_DB_PATH=/data/app_usage.db
Environment=MCP_APP_USAGE_LOG_LEVEL=INFO
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable mcp-app-usage
sudo systemctl start mcp-app-usage
sudo systemctl status mcp-app-usage
```

## 📈 Performance Optimization

### Database Optimization
```sql
-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_app_usage_user_date ON app_usage(user, log_date);
CREATE INDEX IF NOT EXISTS idx_app_usage_app_date ON app_usage(application_name, log_date);
CREATE INDEX IF NOT EXISTS idx_app_usage_platform ON app_usage(platform);
CREATE INDEX IF NOT EXISTS idx_app_list_publisher ON app_list(publisher);
CREATE INDEX IF NOT EXISTS idx_app_list_type ON app_list(app_type);

-- Analyze tables for query optimization
ANALYZE app_usage;
ANALYZE app_list;
```

### Server Tuning
```bash
# Increase connection pool for high load
export MCP_APP_USAGE_CONNECTION_POOL_SIZE="20"

# Enable caching for frequently accessed data
export MCP_APP_USAGE_CACHE_ENABLED="true"
export MCP_APP_USAGE_CACHE_TTL="600"  # 10 minutes

# Adjust query timeout for complex analytics
export MCP_APP_USAGE_QUERY_TIMEOUT="60"
```

## 🔒 Security Configuration

### Authentication Setup
```bash
# Enable authentication
export MCP_APP_USAGE_ENABLE_AUTHENTICATION="true"
export MCP_APP_USAGE_API_KEY_REQUIRED="true"

# Set API key (in production, use secure key management)
export MCP_APP_USAGE_API_KEY="your-secure-api-key"
```

### Rate Limiting
```bash
# Configure rate limiting
export MCP_APP_USAGE_RATE_LIMIT_ENABLED="true"
export MCP_APP_USAGE_MAX_REQUESTS_PER_MINUTE="100"
```

### Database Security
```bash
# Set restrictive file permissions
chmod 600 /path/to/app_usage.db
chown mcpuser:mcpuser /path/to/app_usage.db

# Use read-only database connection if possible
export MCP_APP_USAGE_DB_READONLY="true"
```

## 📊 Monitoring and Logging

### Log Configuration
```bash
# Set appropriate log level
export MCP_APP_USAGE_LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR

# Log to file
export MCP_APP_USAGE_LOG_FILE="/var/log/mcp-app-usage.log"
```

### Health Monitoring
Create monitoring script `health_check.py`:

```python
#!/usr/bin/env python3
import sqlite3
import sys
import os

def health_check():
    try:
        db_path = os.getenv('MCP_APP_USAGE_DB_PATH', '../database/app_usage.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test database connectivity
        cursor.execute("SELECT COUNT(*) FROM app_usage LIMIT 1")
        cursor.execute("SELECT COUNT(*) FROM app_list LIMIT 1")
        
        conn.close()
        print("✅ Health check passed")
        return 0
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(health_check())
```

### Metrics Collection
Monitor key metrics:
- Query execution times
- Database connection pool usage
- Memory usage
- Request rate and errors
- Cache hit rates

## 🧪 Testing Deployment

### Functional Testing
```bash
# Test basic functionality
python -c "
import asyncio
from main import main
print('Testing server startup...')
# Add basic connectivity test
"

# Test database connectivity
python health_check.py

# Test MCP protocol
echo '{}' | python main.py
```

### Load Testing
```bash
# Install load testing tools
pip install locust

# Create load test script
cat > load_test.py << 'EOF'
from locust import User, task, between
import json
import subprocess

class MCPUser(User):
    wait_time = between(1, 3)
    
    @task
    def test_list_applications(self):
        # Simulate MCP tool call
        cmd = ['python', 'main.py']
        input_data = json.dumps({
            "tool": "list_applications",
            "arguments": {"limit": 10}
        })
        subprocess.run(cmd, input=input_data, text=True, capture_output=True)
EOF

# Run load test
locust -f load_test.py --host=localhost
```

## 🔄 Backup and Recovery

### Database Backup
```bash
#!/bin/bash
# backup_database.sh
DB_PATH="${MCP_APP_USAGE_DB_PATH:-../database/app_usage.db}"
BACKUP_DIR="/backup/mcp-app-usage"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"
sqlite3 "$DB_PATH" ".backup $BACKUP_DIR/app_usage_$TIMESTAMP.db"
gzip "$BACKUP_DIR/app_usage_$TIMESTAMP.db"

# Keep only last 30 days of backups
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete
```

### Configuration Backup
```bash
# Backup configuration
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
    config.json \
    .env \
    /etc/systemd/system/mcp-app-usage.service
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   # Check database file exists and is readable
   ls -la /path/to/app_usage.db
   sqlite3 /path/to/app_usage.db ".tables"
   ```

2. **Permission Denied**
   ```bash
   # Fix file permissions
   chown -R mcpuser:mcpuser /opt/mcp-server-app-usage
   chmod -R 755 /opt/mcp-server-app-usage
   chmod 600 /path/to/app_usage.db
   ```

3. **High Memory Usage**
   ```bash
   # Reduce query result limits
   export MCP_APP_USAGE_MAX_QUERY_RESULTS="500"
   
   # Disable caching if needed
   export MCP_APP_USAGE_CACHE_ENABLED="false"
   ```

4. **Slow Query Performance**
   ```sql
   -- Add missing indexes
   CREATE INDEX idx_app_usage_composite ON app_usage(user, application_name, log_date);
   
   -- Analyze query performance
   EXPLAIN QUERY PLAN SELECT * FROM app_usage WHERE user = 'test';
   ```

### Debug Mode
```bash
# Enable debug logging
export MCP_APP_USAGE_LOG_LEVEL="DEBUG"

# Run with verbose output
python main.py --verbose
```

## 📋 Maintenance

### Regular Maintenance Tasks
1. **Database Maintenance**
   ```sql
   -- Vacuum database monthly
   VACUUM;
   
   -- Update statistics
   ANALYZE;
   
   -- Check database integrity
   PRAGMA integrity_check;
   ```

2. **Log Rotation**
   ```bash
   # Setup logrotate
   cat > /etc/logrotate.d/mcp-app-usage << 'EOF'
   /var/log/mcp-app-usage.log {
       daily
       rotate 30
       compress
       delaycompress
       missingok
       notifempty
       postrotate
           systemctl reload mcp-app-usage
       endscript
   }
   EOF
   ```

3. **Performance Monitoring**
   ```bash
   # Monitor resource usage
   top -p $(pgrep -f "python main.py")
   
   # Check database size
   du -h /path/to/app_usage.db
   
   # Monitor query performance
   tail -f /var/log/mcp-app-usage.log | grep "Query executed"
   ```

## 🔄 Updates and Upgrades

### Version Updates
```bash
# Backup current installation
cp -r /opt/mcp-server-app-usage /opt/mcp-server-app-usage.backup

# Update code
git pull origin main
pip install -e . --upgrade

# Test new version
python health_check.py

# Restart service
sudo systemctl restart mcp-app-usage
```

### Database Schema Updates
```bash
# Always backup before schema changes
sqlite3 app_usage.db ".backup app_usage_backup.db"

# Apply schema updates
sqlite3 app_usage.db < schema_updates.sql

# Verify schema
sqlite3 app_usage.db ".schema"
```

This deployment guide ensures a robust, secure, and maintainable production deployment of the MCP App Usage Analytics Server.
