# MCP App Usage Analytics - Prompt Guide

This document provides comprehensive examples of all possible prompts you can use with the MCP App Usage Analytics Server. The server provides 43 different analytics tools organized into 7 categories.

## 🚀 Quick Start

To use any tool, simply ask the MCP client with natural language. The server will automatically map your request to the appropriate tool and parameters.

---

## 📊 General Application Information (Features 1-7)

### 1. List Applications
**Tool:** `list_applications`

**Example Prompts:**
```
"Show me all applications being tracked"
"List all apps in the system"
"What applications do we have data for?"
"Show me productivity apps only"
"List the first 50 applications sorted by name"
"Show me all applications with tracking enabled"
```

**Parameters:**
- `limit`: Maximum number of results (default: 100)
- `app_type`: Filter by application type
- `enable_tracking`: Filter by tracking status
- `sort_by`: Sort field (name, type, released_date, publisher)
- `sort_order`: Sort order (asc, desc)

### 2. Application Details
**Tool:** `app_details`

**Example Prompts:**
```
"Show me details for Microsoft Word"
"What information do we have about Chrome?"
"Get full details for Slack application"
"Tell me about the Photoshop app"
```

**Parameters:**
- `app_name`: Application name (required)

### 3. Tracking Status
**Tool:** `tracking_status`

**Example Prompts:**
```
"Which applications have tracking enabled?"
"Show me apps that are being monitored"
"List applications with disabled tracking"
"What's the tracking configuration for all apps?"
```

### 4. Legacy Applications
**Tool:** `legacy_apps`

**Example Prompts:**
```
"Show me all legacy applications"
"Which apps are marked as legacy?"
"List outdated applications in the system"
"What legacy software do we have?"
```

### 5. Recent Releases
**Tool:** `recent_releases`

**Example Prompts:**
```
"Show me applications released in the last 30 days"
"What apps were released this month?"
"List new applications from the past week"
"Show me recent software releases"
```

**Parameters:**
- `days`: Number of days to look back (default: 30)
- `limit`: Maximum number of results

### 6. Top Publishers
**Tool:** `top_publishers`

**Example Prompts:**
```
"Who are the top software publishers?"
"Show me publishers with the most applications"
"List the most active software companies"
"Which publishers have released the most apps?"
```

**Parameters:**
- `limit`: Number of top publishers to show

### 7. Application Versions
**Tool:** `app_versions`

**Example Prompts:**
```
"Show me all applications with their current versions"
"List app versions in the system"
"What versions of software do we track?"
"Show me version information for all apps"
```

---

## 📈 Usage Statistics (Features 8-14)

### 8. Usage Time Statistics
**Tool:** `usage_time_stats`

**Example Prompts:**
```
"Show me total usage time for all applications"
"Which apps are used the most in hours?"
"List applications by total usage time"
"Show me usage statistics for this month"
"What are the usage hours for apps from Jan 1 to Jan 31?"
```

**Parameters:**
- `start_date`: Start date (YYYY-MM-DD)
- `end_date`: End date (YYYY-MM-DD)
- `limit`: Maximum number of results

### 9. User Count Statistics
**Tool:** `user_count_stats`

**Example Prompts:**
```
"How many users are using each application?"
"Show me user counts for all apps"
"Which applications have the most users?"
"List apps by number of unique users"
```

### 10. Average Usage Time
**Tool:** `average_usage_time`

**Example Prompts:**
```
"What's the average time users spend on each app?"
"Show me average session length per application"
"Calculate average usage time per user per app"
"How long do users typically spend on Microsoft Word?"
```

**Parameters:**
- `application_name`: Specific app to analyze
- `start_date`: Start date for analysis
- `end_date`: End date for analysis

### 11. Top Apps by Usage Time
**Tool:** `top_apps_by_usage`

**Example Prompts:**
```
"Show me the top 10 most used applications"
"Which apps have the highest total usage time?"
"Rank applications by usage hours"
"What are the top 5 apps by total time spent?"
```

**Parameters:**
- `top_n`: Number of top apps (default: 10)
- `start_date`: Start date for analysis
- `end_date`: End date for analysis
- `platform`: Filter by platform

### 12. Top Apps by User Count
**Tool:** `top_apps_by_users`

**Example Prompts:**
```
"Which applications have the most users?"
"Show me top 10 apps by user count"
"Rank apps by number of unique users"
"What are the most popular applications?"
```

**Parameters:**
- `top_n`: Number of top apps (default: 10)
- `min_users`: Minimum user count threshold

### 13. Total Usage by Time Period
**Tool:** `total_usage_period`

**Example Prompts:**
```
"Show me total usage time for each day this week"
"What's the daily usage pattern for January?"
"Calculate weekly usage totals"
"Show me monthly usage statistics"
```

**Parameters:**
- `start_date`: Start date for analysis
- `end_date`: End date for analysis
- `period_type`: Grouping period (day, week, month)

### 14. Platform Usage Statistics
**Tool:** `platform_usage_stats`

**Example Prompts:**
```
"Which apps are most used on Windows?"
"Show me platform-specific usage statistics"
"What applications are popular on Mac?"
"Compare app usage across different platforms"
```

**Parameters:**
- `platform`: Specific platform to analyze
- `limit`: Maximum number of results

---

## 👤 User-Centric Queries (Features 15-21)

### 15. User Applications
**Tool:** `user_applications`

**Example Prompts:**
```
"What applications does john.doe use?"
"Show me all apps used by user alice.smith"
"List applications for user mike.johnson"
"What software does sarah.wilson have access to?"
```

**Parameters:**
- `user`: User identifier (required)
- `start_date`: Start date for analysis
- `end_date`: End date for analysis

### 16. User Total Hours
**Tool:** `user_total_hours`

**Example Prompts:**
```
"How many total hours has john.doe spent on all apps?"
"Calculate total usage time for user alice.smith"
"What's the total screen time for mike.johnson?"
"Show me cumulative hours for sarah.wilson"
```

**Parameters:**
- `user`: User identifier (required)
- `start_date`: Start date for analysis
- `end_date`: End date for analysis

### 17. User App Hours
**Tool:** `user_app_hours`

**Example Prompts:**
```
"How much time has john.doe spent on Microsoft Word?"
"Show me alice.smith's usage of Chrome"
"Calculate mike.johnson's hours on Slack"
"How long has sarah.wilson used Photoshop?"
```

**Parameters:**
- `user`: User identifier (required)
- `application_name`: Application name (required)
- `start_date`: Start date for analysis
- `end_date`: End date for analysis

### 18. User Last Application
**Tool:** `user_last_app`

**Example Prompts:**
```
"What was the last app john.doe used?"
"Show me alice.smith's most recent application"
"What did mike.johnson use last?"
"Find sarah.wilson's last used application"
```

**Parameters:**
- `user`: User identifier (required)

### 19. User Last Active
**Tool:** `user_last_active`

**Example Prompts:**
```
"When was john.doe last active?"
"Show me alice.smith's last activity date"
"When did mike.johnson last use any app?"
"Find sarah.wilson's last active session"
```

**Parameters:**
- `user`: User identifier (required)

### 20. User Top Applications
**Tool:** `user_top_apps`

**Example Prompts:**
```
"What are john.doe's top 5 most used apps?"
"Show me alice.smith's favorite applications"
"List mike.johnson's most frequently used software"
"What apps does sarah.wilson use the most?"
```

**Parameters:**
- `user`: User identifier (required)
- `top_n`: Number of top apps (default: 10)
- `start_date`: Start date for analysis
- `end_date`: End date for analysis

### 21. Application Users
**Tool:** `app_users`

**Example Prompts:**
```
"Who uses Microsoft Word?"
"Show me all users of Chrome browser"
"List everyone who has used Slack"
"Which users have access to Photoshop?"
```

**Parameters:**
- `application_name`: Application name (required)
- `start_date`: Start date for analysis
- `end_date`: End date for analysis

---

## ⏰ Time-Based Queries (Features 22-28)

### 22. New Users Count
**Tool:** `new_users_count`

**Example Prompts:**
```
"How many new users joined today?"
"Show me new user registrations this week"
"Calculate new users for January 2024"
"What's the daily new user trend?"
```

**Parameters:**
- `start_date`: Start date for analysis
- `end_date`: End date for analysis
- `period_type`: Grouping period (day, week, month)

### 23. Active Users Count
**Tool:** `active_users_count`

**Example Prompts:**
```
"How many users were active today?"
"Show me daily active user counts"
"Calculate weekly active users"
"What's the active user trend this month?"
```

**Parameters:**
- `start_date`: Start date for analysis
- `end_date`: End date for analysis
- `period_type`: Grouping period (day, week, month)

### 24. Daily Usage Trend
**Tool:** `daily_usage_trend`

**Example Prompts:**
```
"Show me daily usage trend for Microsoft Word"
"What's the usage pattern for Chrome over time?"
"Display daily statistics for Slack"
"How has Photoshop usage changed daily?"
```

**Parameters:**
- `application_name`: Application name (required)
- `start_date`: Start date for analysis
- `end_date`: End date for analysis

### 25. Usage Trends
**Tool:** `usage_trends`

**Example Prompts:**
```
"Show me weekly usage trends"
"What are the monthly usage patterns?"
"Display usage trends for the last quarter"
"How has overall usage changed over time?"
```

**Parameters:**
- `period_type`: Grouping period (week, month)
- `start_date`: Start date for analysis
- `end_date`: End date for analysis
- `application_name`: Specific app to analyze

### 26. Peak Usage Hours
**Tool:** `peak_usage_hours`

**Example Prompts:**
```
"What are the peak usage hours of the day?"
"When are users most active?"
"Show me hourly usage patterns"
"What time of day has the highest activity?"
```

**Parameters:**
- `start_date`: Start date for analysis
- `end_date`: End date for analysis
- `application_name`: Specific app to analyze

### 27. Onboarding Trend
**Tool:** `onboarding_trend`

**Example Prompts:**
```
"Which apps are users adopting recently?"
"Show me new application adoptions"
"What software has been onboarded lately?"
"Track first-time app usage trends"
```

**Parameters:**
- `start_date`: Start date for analysis
- `end_date`: End date for analysis
- `limit`: Maximum number of results

### 28. Usage Comparison
**Tool:** `usage_comparison`

**Example Prompts:**
```
"Compare usage between January and February"
"Show me usage changes from Q1 to Q2"
"Compare this month vs last month usage"
"How did usage change between two time periods?"
```

**Parameters:**
- `period1_start`: First period start date (required)
- `period1_end`: First period end date (required)
- `period2_start`: Second period start date (required)
- `period2_end`: Second period end date (required)

---

## 🔄 Cross-Analysis (Features 29-32)

### 29. User-App Matrix
**Tool:** `user_app_matrix`

**Example Prompts:**
```
"Show me a matrix of users vs applications"
"Create a cross-tab of who uses what"
"Display user-application relationships"
"Show me the usage matrix for all users and apps"
```

**Parameters:**
- `start_date`: Start date for analysis
- `end_date`: End date for analysis
- `limit`: Maximum number of results

### 30. Multi-App Users
**Tool:** `multi_app_users`

**Example Prompts:**
```
"Which users use multiple applications?"
"Show me users with diverse app usage"
"Find users who use more than 5 apps"
"List power users with many applications"
```

**Parameters:**
- `min_apps`: Minimum number of apps (default: 2)
- `start_date`: Start date for analysis
- `end_date`: End date for analysis

### 31. Common App Combinations
**Tool:** `common_app_combinations`

**Example Prompts:**
```
"Which applications are commonly used together?"
"Show me app combinations used by the same users"
"Find applications that complement each other"
"What apps do users typically use in combination?"
```

**Parameters:**
- `min_users`: Minimum common users (default: 2)
- `start_date`: Start date for analysis
- `end_date`: End date for analysis

### 32. Usage Percentage Breakdown
**Tool:** `user_app_usage_percentage`

**Example Prompts:**
```
"What percentage of time does john.doe spend on each app?"
"Show me usage percentage breakdown for alice.smith"
"Calculate app usage distribution for mike.johnson"
"How does sarah.wilson distribute her time across apps?"
```

**Parameters:**
- `user`: User identifier (required)
- `start_date`: Start date for analysis
- `end_date`: End date for analysis
- `min_percentage`: Minimum percentage threshold

---

## 🏷️ Version & Legacy Tracking (Features 33-36)

### 33. Usage by Version
**Tool:** `version_usage_breakdown`

**Example Prompts:**
```
"Show me usage statistics by application version"
"Which versions of Microsoft Word are being used?"
"Break down usage by Chrome versions"
"Display version-specific usage data"
```

**Parameters:**
- `application_name`: Specific app to analyze
- `start_date`: Start date for analysis
- `end_date`: End date for analysis

### 34. Legacy vs Modern Usage
**Tool:** `legacy_vs_modern`

**Example Prompts:**
```
"Compare usage between legacy and modern applications"
"Show me legacy vs current app usage"
"What's the split between old and new software?"
"How much are legacy applications still used?"
```

**Parameters:**
- `start_date`: Start date for analysis
- `end_date`: End date for analysis

### 35. Outdated Versions
**Tool:** `outdated_versions`

**Example Prompts:**
```
"Which applications have outdated versions in use?"
"Show me apps that need version updates"
"Find software with old versions still being used"
"List applications with legacy versions"
```

**Parameters:**
- `min_days_old`: Minimum age in days (default: 365)
- `start_date`: Start date for analysis
- `end_date`: End date for analysis

### 36. Version Distribution
**Tool:** `version_distribution`

**Example Prompts:**
```
"Show me version distribution for Microsoft Office"
"What versions of Chrome are users running?"
"Display version breakdown for Adobe products"
"How are different app versions distributed?"
```

**Parameters:**
- `application_name`: Specific app to analyze
- `start_date`: Start date for analysis
- `end_date`: End date for analysis

---

## 🧠 Advanced Analytics (Features 37-43)

### 37. Average Session Length
**Tool:** `session_length_analysis`

**Example Prompts:**
```
"What's the average session length per user per app?"
"Show me session duration statistics"
"Calculate average time spent per session"
"How long are typical user sessions?"
```

**Parameters:**
- `user`: Specific user to analyze
- `application_name`: Specific app to analyze
- `start_date`: Start date for analysis
- `end_date`: End date for analysis

### 38. Median Session Length
**Tool:** `median_session_length`

**Example Prompts:**
```
"What's the median session length across all apps?"
"Show me median usage time statistics"
"Calculate median session duration"
"What's the typical session length?"
```

**Parameters:**
- `start_date`: Start date for analysis
- `end_date`: End date for analysis
- `application_name`: Specific app to analyze

### 39. Heavy Users
**Tool:** `heavy_users`

**Example Prompts:**
```
"Who are the heavy users with more than 40 hours usage?"
"Show me power users with high usage"
"Find users who spend more than 60 hours per week"
"List users with excessive screen time"
```

**Parameters:**
- `min_hours`: Minimum hours threshold (default: 40)
- `start_date`: Start date for analysis
- `end_date`: End date for analysis

### 40. Inactive Users
**Tool:** `inactive_users`

**Example Prompts:**
```
"Who hasn't used any apps in the last 30 days?"
"Show me inactive users"
"Find users with no recent activity"
"List users who haven't logged in for 2 weeks"
```

**Parameters:**
- `min_inactive_days`: Minimum inactive days (default: 30)
- `limit`: Maximum number of results

### 41. App Churn Rate
**Tool:** `churn_rate_analysis`

**Example Prompts:**
```
"What's the churn rate for applications after January 1st?"
"Show me user retention rates for apps"
"Calculate app abandonment rates"
"Which apps have the highest churn?"
```

**Parameters:**
- `churn_date`: Date to measure churn from (required)
- `start_date`: Analysis start date
- `end_date`: Analysis end date

### 42. New vs Returning Users
**Tool:** `new_vs_returning_users`

**Example Prompts:**
```
"What's the ratio of new vs returning users?"
"Show me new user vs existing user breakdown"
"Calculate daily new vs returning user percentages"
"How many users are new vs repeat users?"
```

**Parameters:**
- `start_date`: Start date for analysis
- `end_date`: End date for analysis
- `application_name`: Specific app to analyze

### 43. App Growth Trend
**Tool:** `growth_trend_analysis`

**Example Prompts:**
```
"Show me growth trends for Microsoft Teams"
"What's the user growth pattern for Slack?"
"Display growth analytics for Chrome browser"
"How has Zoom usage grown over time?"
```

**Parameters:**
- `application_name`: Specific app to analyze
- `start_date`: Start date for analysis
- `end_date`: End date for analysis

---

## 💡 Tips for Better Prompts

### 1. **Be Specific with Dates**
```
✅ Good: "Show me usage from 2024-01-01 to 2024-01-31"
❌ Vague: "Show me recent usage"
```

### 2. **Use Exact Application Names**
```
✅ Good: "Microsoft Word usage statistics"
❌ Vague: "Word processor usage"
```

### 3. **Specify User Identifiers Clearly**
```
✅ Good: "john.doe's application usage"
❌ Vague: "John's usage"
```

### 4. **Combine Multiple Filters**
```
✅ Good: "Top 10 Windows applications used in January 2024"
❌ Basic: "Top applications"
```

### 5. **Use Natural Language**
```
✅ Good: "Which users haven't been active for more than 2 weeks?"
✅ Good: "Show me the most popular apps among heavy users"
✅ Good: "Compare Chrome usage between Q1 and Q2 2024"
```

---

## 🔧 Parameter Reference

### Common Parameters Across Tools:

- **Date Parameters**: Use YYYY-MM-DD format (e.g., "2024-01-15")
- **User Identifiers**: Use exact user IDs (e.g., "john.doe", "alice.smith")
- **Application Names**: Use exact app names (e.g., "Microsoft Word", "Google Chrome")
- **Limits**: Specify number of results (e.g., 10, 50, 100)
- **Thresholds**: Set minimum values for filtering (e.g., min_hours: 40)

### Date Range Examples:
```
"from 2024-01-01 to 2024-01-31"    # January 2024
"in the last 30 days"              # Recent period
"this week"                        # Current week
"between March 1 and March 15"     # Mid-month period
```

---

This comprehensive guide covers all 43 analytics tools available in the MCP App Usage Analytics Server. Each tool can be accessed through natural language prompts, making it easy to get insights from your application usage data.
