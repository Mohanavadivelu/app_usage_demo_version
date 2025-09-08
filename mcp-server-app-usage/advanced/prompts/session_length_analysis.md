# Session Length Analysis - Prompt Documentation

## Overview
Average session length per user/app

## Feature ID
Feature #37 from the original requirements

## Parameters
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| limit | integer | No | Maximum number of results to return | 100 |

## Usage Examples
```json
Input: {"limit": 10}
Output: {
  "tool": "session_length_analysis",
  "description": "Average session length per user/app",
  "results": [...]
}
```

## Implementation Status
**In Progress** - This tool is currently being implemented.

## Related Features
- Related tools and features will be documented here
