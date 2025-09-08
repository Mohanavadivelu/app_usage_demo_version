# List Applications - Prompt Documentation

## Overview

The `list_applications` tool provides a comprehensive view of all applications being tracked in the system. It retrieves data from the `app_list` table and offers flexible filtering and sorting options to help users find specific applications or analyze the application catalog.

## Feature ID

Feature #1 from the original requirements: "Implement an endpoint to list all applications being tracked."

## Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| limit | integer | No | Maximum number of applications to return (default: 100, max: 1000) | 50 |
| app_type | string | No | Filter by application type | "productivity" |
| enable_tracking | boolean | No | Filter by tracking status | true |
| sort_by | string | No | Field to sort by (default: "app_name") | "released_date" |
| sort_order | string | No | Sort order: "asc" or "desc" (default: "asc") | "desc" |

### Valid sort_by values:

- `app_name`: Sort by application name
- `app_type`: Sort by application type/category
- `released_date`: Sort by release date
- `publisher`: Sort by publisher name
- `registered_date`: Sort by registration date in the system

## Usage Examples

### Basic Usage

List all applications with default settings:
```json
Input: {}
Output: {
  "tool": "list_applications",
  "description": "List of all tracked applications",
  "total_applications": 25,
  "applications": [
    {
      "app_id": 1,
      "name": "Chrome Browser",
      "type": "web_browser",
      "version": "120.0.6099.109",
      "released_date": "2024-01-15",
      "publisher": "Google",
      "description": "Fast and secure web browser...",
      "tracking": {
        "enabled": true,
        "usage": true,
        "location": false,
        "cpu_memory": true,
        "interval_seconds": 300
      }
    }
  ]
}
```text

### Filtered Usage

Get productivity applications with tracking enabled:
```json
Input: {
  "app_type": "productivity",
  "enable_tracking": true,
  "limit": 10,
  "sort_by": "released_date",
  "sort_order": "desc"
}
Output: {
  "tool": "list_applications",
  "total_applications": 8,
  "filters_applied": {
    "app_type": "productivity",
    "enable_tracking": true,
    "limit": 10,
    "sort_by": "released_date",
    "sort_order": "desc"
  },
  "applications": [...]
}
```text

### Publisher Analysis

List applications sorted by publisher:
```json
Input: {
  "sort_by": "publisher",
  "sort_order": "asc",
  "limit": 20
}
```text

## Response Structure

The tool returns a JSON object with the following structure:

```json
{
  "tool": "list_applications",
  "description": "List of all tracked applications",
  "total_applications": 25,
  "query_time_ms": 15.2,
  "filters_applied": {
    "app_type": null,
    "enable_tracking": null,
    "limit": 100,
    "sort_by": "app_name",
    "sort_order": "asc"
  },
  "applications": [
    {
      "app_id": 1,
      "name": "Application Name",
      "type": "application_type",
      "version": "1.0.0",
      "released_date": "2024-01-15",
      "publisher": "Publisher Name",
      "description": "Application description...",
      "download_link": "https://example.com/download",
      "tracking": {
        "enabled": true,
        "usage": true,
        "location": false,
        "cpu_memory": true,
        "interval_seconds": 300
      },
      "registered_date": "2024-01-01"
    }
  ],
  "summary": {
    "total_applications": 25,
    "tracking_enabled": 20,
    "tracking_disabled": 5,
    "unique_app_types": 8,
    "unique_publishers": 12,
    "top_app_types": [
      ["productivity", 8],
      ["entertainment", 5],
      ["development", 4]
    ],
    "top_publishers": [
      ["Microsoft", 6],
      ["Google", 4],
      ["Adobe", 3]
    ]
  }
}
```text

## Database Queries

The tool executes queries against the `app_list` table:

```sql
SELECT
    app_id, app_name, app_type, current_version, released_date,
    publisher, description, download_link, enable_tracking,
    track_usage, track_location, track_cm, track_intr, registered_date
FROM app_list
WHERE [optional filters]
ORDER BY [sort_field] [sort_order]
LIMIT [limit]
```text

## Error Handling

### Common Errors:

1. **Invalid sort_by field**: Returns error if sort_by is not in allowed values
2. **Invalid sort_order**: Returns error if sort_order is not 'asc' or 'desc'
3. **Invalid limit**: Returns error if limit is not between 1 and 1000
4. **Database connection error**: Returns error if database is unavailable

### Error Response Format:

```json
{
  "tool": "list_applications",
  "error": "Invalid sort_by field. Must be one of: app_name, app_type, released_date, publisher, registered_date",
  "message": "Failed to retrieve application list"
}
```text

## Performance Considerations

- Default limit of 100 applications for reasonable response times
- Maximum limit of 1000 to prevent excessive memory usage
- Indexed fields (app_name, app_type, publisher) provide faster sorting
- Query execution time is included in response for monitoring

## Related Features

- **app_details**: Get detailed information about a specific application
- **tracking_status**: Check tracking configuration for applications
- **recent_releases**: List recently released applications
- **top_publishers**: Get publishers with most applications

## Use Cases

1. **Application Catalog Management**: View all tracked applications
2. **Tracking Configuration Audit**: Find applications with specific tracking settings
3. **Publisher Analysis**: Analyze applications by publisher
4. **Type-based Filtering**: Focus on specific application categories
5. **Release Date Analysis**: Sort applications by release timeline

## Integration Notes

- This tool provides the foundation for other application-related queries
- Results can be used as input for detailed analysis tools
- Supports pagination through the limit parameter
- Summary statistics provide quick insights into the application catalog
