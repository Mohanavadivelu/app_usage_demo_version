# User Last App - Prompt Documentation

## Overview
Find the last application used by a user

## Feature ID
Feature #18 from the original requirements

## Parameters
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| limit | integer | No | Maximum number of results to return | 100 |

## Usage Examples
```json
Input: {"limit": 10}
Output: {
  "tool": "user_last_app",
  "description": "Find the last application used by a user",
  "results": [...]
}
```

## Implementation Status
**In Progress** - This tool is currently being implemented.

## Related Features
- Related tools and features will be documented here
