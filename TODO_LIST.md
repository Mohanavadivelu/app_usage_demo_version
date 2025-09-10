
### Dashboard Content:
#### Top-Row KPIs (Single Row, Prominent):
- **Compact KPI Cards** (4–6 cards) for quick insights:
  1. **Total Applications Tracked**: Quick inventory snapshot.  
     - **Interaction**: Click → App Manager filtered to “all apps”.
  2. **Active Users (Selected Range)**: Measures reach/engagement.  
     - **Interaction**: Click → List of active users.
  3. **Total Usage Hours (Selected Range)**: Overall consumption metric.  
     - **Interaction**: Click → Timeseries chart / breakdown by app.
  4. **New Users (Last 7/30 Days)**: Growth indicator for onboarding.  
     - **Interaction**: Click → Onboarding trend.
  5. **Top App by Usage**: Displays app name + small sparkline.  
     - **Interaction**: Click → App detail.
  6. **Churn Rate (Optional)**: Health metric for retention.  
     - **Interaction**: Click → Churn cohort analysis.

#### Second Row — Key Visualizations (2–3 Columns):
- **Total Usage Time (Timeseries Line Chart)**:
  - Displays daily/weekly usage across all apps.
  - **Controls**: Date range selector, compare previous period toggle.
  - **Why**: Detect trends, seasonality, sudden drops/spikes.
- **Top N Applications by Usage (Bar Chart)**:
  - Displays top 5–10 apps by total hours.
  - **Interaction**: Click bar → Filter other widgets to that app.
- **Number of Users by App (Bar Chart or Stacked Chart)**:
  - Distinguishes popular apps by users vs heavy-usage apps.
  - **Interaction**: Switch metric between unique users and total sessions.

#### Third Row — Platform & Version Insights (2 Columns):
- **Platform Breakdown (Pie/Stacked Bar Chart)**:
  - Displays usage by platform (e.g., Windows, Linux, Android, macOS).
  - **Why**: Resource allocation and engineering priorities.
  - **Interaction**: Click slice → Filtered top-app chart for that platform.
- **Version Distribution (Stacked Bar or Donut Chart)**:
  - Displays % of users on each major version for the top app.
  - **Why**: Reveals upgrade adoption and outdated versions.

### Additional Features:
- Use **modular JavaScript** to handle dynamic content loading.
- Include **comments** in the code for clarity and maintainability.
- Ensure **all pages are linked properly** via the sidebar navigation.
- Leverage **third-party libraries** (e.g., Chart.js) for visualizations.
- Test for **responsiveness** across devices and browsers.

### Development Notes:
- Prioritize clean, maintainable code with a focus on scalability.
- Use **Bootstrap utilities** to ensure consistent styling and layout.
- Provide **clear documentation** for folder structure and code organization.
"