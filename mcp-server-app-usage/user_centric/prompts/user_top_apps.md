# User Top Apps - Prompt Documentation

## Overview
Top N applications for a specific user

## Feature ID
Feature #20 from the original requirements

## Parameters
| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| limit | integer | No | Maximum number of results to return | 100 |

## Usage Examples
```json
Input: {"limit": 10}
Output: {
  "tool": "user_top_apps",
  "description": "Top N applications for a specific user",
  "results": [...]
}
```

## Implementation Status
**In Progress** - This tool is currently being implemented.

## Related Features
- Related tools and features will be documented here
