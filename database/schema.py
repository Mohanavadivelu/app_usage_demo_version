TABLES = {
    "app_usage": """
        CREATE TABLE IF NOT EXISTS app_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            monitor_app_version TEXT NOT NULL CHECK(length(monitor_app_version) <= 50),
            platform TEXT NOT NULL CHECK(length(platform) <= 50),
            user TEXT NOT NULL CHECK(length(user) <= 100),
            application_name TEXT NOT NULL CHECK(length(application_name) <= 100),
            application_version TEXT NOT NULL CHECK(length(application_version) <= 50),
            log_date TEXT NOT NULL,
            legacy_app BOOLEAN NOT NULL,
            duration_seconds INTEGER NOT NULL CHECK(duration_seconds >= 0),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """,
    "app_list": """
        CREATE TABLE IF NOT EXISTS app_list (
            app_id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_name TEXT NOT NULL,
            app_type TEXT NOT NULL,
            current_version TEXT NOT NULL,
            released_date TEXT NOT NULL,
            publisher TEXT NOT NULL,
            description TEXT NOT NULL,
            download_link TEXT NOT NULL,
            enable_tracking BOOLEAN NOT NULL,
            track_usage BOOLEAN NOT NULL,
            track_location BOOLEAN NOT NULL,
            track_cm BOOLEAN NOT NULL,
            track_intr INTEGER NOT NULL,
            registered_date TEXT NOT NULL
        )
    """
}

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_app_usage_user ON app_usage(user)",
    "CREATE INDEX IF NOT EXISTS idx_app_usage_date ON app_usage(log_date)",
    "CREATE INDEX IF NOT EXISTS idx_app_usage_app ON app_usage(application_name)"
]
