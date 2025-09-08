# User Applications - Prompt Documentation

## Overview

List all applications used by a user

## Feature ID

Feature #15 from the original requirements

## Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| limit | integer | No | Maximum number of results to return | 100 |

## Usage Examples

```json
Input: {"limit": 10}
Output: {
  "tool": "user_applications",
  "description": "List all applications used by a user",
  "results": [...]
}
```text

## Implementation Status

**In Progress** - This tool is currently being implemented.

## Related Features

- Related tools and features will be documented here
