# App Users - Prompt Documentation

## Overview

List users who have used a specific application

## Feature ID

Feature #21 from the original requirements

## Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| limit | integer | No | Maximum number of results to return | 100 |

## Usage Examples

```json
Input: {"limit": 10}
Output: {
  "tool": "app_users",
  "description": "List users who have used a specific application",
  "results": [...]
}
```text

## Implementation Status

**In Progress** - This tool is currently being implemented.

## Related Features

- Related tools and features will be documented here
