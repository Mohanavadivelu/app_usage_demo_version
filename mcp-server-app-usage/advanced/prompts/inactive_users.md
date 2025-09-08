# Inactive Users - Prompt Documentation

## Overview
Find users with no recent activity

## Feature ID
Feature #40 from the original requirements

## Parameters
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| limit | integer | No | Maximum number of results to return | 100 |

## Usage Examples
```json
Input: {"limit": 10}
Output: {
  "tool": "inactive_users",
  "description": "Find users with no recent activity",
  "results": [...]
}
```

## Implementation Status
**In Progress** - This tool is currently being implemented.

## Related Features
- Related tools and features will be documented here
