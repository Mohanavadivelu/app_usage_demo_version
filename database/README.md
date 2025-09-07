# 📊 App Usage Database

This folder contains the database schema and tables used for tracking **application usage** and related metadata.

---

## 📂 Contents

- **schema file** – Defines the database schema and table structures.
- **Tables:**
  1. **app_usage** – Stores logs of application usage per user.
  2. **app_list** – Maintains the master list of applications with metadata.

- **Indexes:**  
  To improve query performance on frequently used columns such as `user`, `log_date`, and `application_name`.

---

## 🗄️ Database Schema

### **1. app_usage**
Tracks user activity on applications.

| Column              | Type     | Description                      |
|----------------------|---------|----------------------------------|
| id                  | INTEGER  | Primary key (autoincrement).     |
| monitor_app_version | TEXT(50) | Version of monitoring app.       |
| platform            | TEXT(50) | OS/Platform used.                |
| user                | TEXT(100)| User identifier.                 |
| application_name    | TEXT(100)| Name of the application.         |
| application_version | TEXT(50) | Version of the application.      |
| log_date            | TEXT     | Date of usage log.               |
| legacy_app          | BOOLEAN  | Flag if the app is legacy.       | 
| duration_seconds    | INTEGER  | Duration of usage in seconds.    |
| created_at          | DATETIME | Record creation timestamp.       |
| updated_at          | DATETIME | Record update timestamp.         |

Indexes:  
- `idx_app_usage_user`  
- `idx_app_usage_date`  
- `idx_app_usage_app`

---

### **2. app_list**
Holds metadata about applications.

| Column           | Type     | Description                               |
|------------------|----------|-------------------------------------------|
| app_id           | INTEGER  | Primary key (autoincrement).              |
| app_name         | TEXT     | Application name.                         |
| app_type         | TEXT     | Type of app (e.g., Web, Mobile, Desktop). |
| current_version  | TEXT     | Latest released version.                  |
| released_date    | TEXT     | Date of release.                          |
| publisher        | TEXT     | Publisher of the app.                     |
| description      | TEXT     | Description of the app.                   |
| download_link    | TEXT     | Download link of the app.                 |
| enable_tracking  | BOOLEAN  | Whether tracking is enabled.              |
| track_usage      | BOOLEAN  | Whether usage tracking is enabled.        |
| track_location   | BOOLEAN  | Whether location tracking is enabled.     |
| track_cm         | BOOLEAN  | Whether CM tracking is enabled.           |
| track_intr       | INTEGER  | Interrupt tracking level.                 |
| registered_date  | TEXT     | Date the app was registered.              |

---

## ⚡ Creating the Database

To generate the database from the schema file, run:

```bash
# Create a new SQLite database from the schema
Get-Content schema.sql | sqlite3 app_usage.db
