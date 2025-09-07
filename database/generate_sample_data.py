#!/usr/bin/env python3
"""
Sample Data Generator for App Usage Application Database
Generates realistic sample data for app_list and app_usage tables
"""

import sqlite3
import random
import datetime
from typing import List, Dict, Tuple
import os

# Configuration
DATABASE_PATH = "app_usage.db"
MONITOR_APP_VERSION = "2.1.0"
START_DATE = datetime.date(2024, 1, 1)
END_DATE = datetime.date(2024, 12, 31)

# Application data
APPLICATIONS = [
    {
        'app_name': 'Microsoft Word',
        'app_type': 'Office Suite',
        'current_version': '2021',
        'released_date': '2021-10-05',
        'publisher': 'Microsoft Corporation',
        'description': 'Word processing application for creating and editing documents',
        'download_link': 'https://office.microsoft.com/word',
        'enable_tracking': 1,
        'track_usage': 1,
        'track_location': 0,
        'track_cm': 1,
        'track_intr': 60,
        'registered_date': '2025-01-15',
        'min_duration': 1800,
        'max_duration': 7200
    },
    {
        'app_name': 'Google Chrome',
        'app_type': 'Web Browser',
        'current_version': '118.0.5993.88',
        'released_date': '2023-10-24',
        'publisher': 'Google LLC',
        'description': 'Fast and secure web browser with built-in Google services',
        'download_link': 'https://www.google.com/chrome/',
        'enable_tracking': 1,
        'track_usage': 1,
        'track_location': 1,
        'track_cm': 0,
        'track_intr': 30,
        'registered_date': '2025-01-15',
        'min_duration': 900,
        'max_duration': 3600
    },
    {
        'app_name': 'Adobe Photoshop',
        'app_type': 'Graphics Design',
        'current_version': '2024',
        'released_date': '2023-10-17',
        'publisher': 'Adobe Inc.',
        'description': 'Professional image editing and graphic design software',
        'download_link': 'https://www.adobe.com/products/photoshop.html',
        'enable_tracking': 1,
        'track_usage': 1,
        'track_location': 0,
        'track_cm': 1,
        'track_intr': 120,
        'registered_date': '2025-01-16',
        'min_duration': 3600,
        'max_duration': 14400
    },
    {
        'app_name': 'Visual Studio Code',
        'app_type': 'Code Editor',
        'current_version': '1.84.2',
        'released_date': '2023-11-09',
        'publisher': 'Microsoft Corporation',
        'description': 'Lightweight but powerful source code editor with debugging support',
        'download_link': 'https://code.visualstudio.com/',
        'enable_tracking': 1,
        'track_usage': 1,
        'track_location': 0,
        'track_cm': 1,
        'track_intr': 45,
        'registered_date': '2025-01-16',
        'min_duration': 2700,
        'max_duration': 10800
    },
    {
        'app_name': 'Slack',
        'app_type': 'Communication',
        'current_version': '4.35.126',
        'released_date': '2023-11-01',
        'publisher': 'Slack Technologies',
        'description': 'Business communication platform for team collaboration',
        'download_link': 'https://slack.com/downloads/',
        'enable_tracking': 1,
        'track_usage': 1,
        'track_location': 1,
        'track_cm': 0,
        'track_intr': 90,
        'registered_date': '2025-01-17',
        'min_duration': 1200,
        'max_duration': 5400
    },
    {
        'app_name': 'AutoCAD',
        'app_type': 'CAD Software',
        'current_version': '2024',
        'released_date': '2023-03-29',
        'publisher': 'Autodesk Inc.',
        'description': 'Computer-aided design software for 2D and 3D drafting',
        'download_link': 'https://www.autodesk.com/products/autocad/',
        'enable_tracking': 1,
        'track_usage': 1,
        'track_location': 0,
        'track_cm': 1,
        'track_intr': 180,
        'registered_date': '2025-01-17',
        'min_duration': 5400,
        'max_duration': 21600
    },
    {
        'app_name': 'Zoom',
        'app_type': 'Video Conferencing',
        'current_version': '5.16.10',
        'released_date': '2023-10-30',
        'publisher': 'Zoom Video Communications',
        'description': 'Video conferencing and online meeting platform',
        'download_link': 'https://zoom.us/download',
        'enable_tracking': 1,
        'track_usage': 1,
        'track_location': 1,
        'track_cm': 0,
        'track_intr': 60,
        'registered_date': '2025-01-18',
        'min_duration': 1800,
        'max_duration': 7200
    },
    {
        'app_name': 'Microsoft Excel',
        'app_type': 'Spreadsheet',
        'current_version': '2021',
        'released_date': '2021-10-05',
        'publisher': 'Microsoft Corporation',
        'description': 'Spreadsheet application for data analysis and calculations',
        'download_link': 'https://office.microsoft.com/excel',
        'enable_tracking': 1,
        'track_usage': 1,
        'track_location': 0,
        'track_cm': 1,
        'track_intr': 75,
        'registered_date': '2025-01-18',
        'min_duration': 2400,
        'max_duration': 9600
    },
    {
        'app_name': 'Notepad++',
        'app_type': 'Text Editor',
        'current_version': '8.5.8',
        'released_date': '2023-09-19',
        'publisher': 'Don Ho',
        'description': 'Free source code editor with syntax highlighting',
        'download_link': 'https://notepad-plus-plus.org/downloads/',
        'enable_tracking': 0,
        'track_usage': 0,
        'track_location': 0,
        'track_cm': 0,
        'track_intr': 0,
        'registered_date': '2025-01-19',
        'min_duration': 300,
        'max_duration': 3600
    },
    {
        'app_name': 'Firefox',
        'app_type': 'Web Browser',
        'current_version': '119.0',
        'released_date': '2023-10-24',
        'publisher': 'Mozilla Foundation',
        'description': 'Open-source web browser focused on privacy and security',
        'download_link': 'https://www.mozilla.org/firefox/',
        'enable_tracking': 1,
        'track_usage': 1,
        'track_location': 1,
        'track_cm': 1,
        'track_intr': 45,
        'registered_date': '2025-01-19',
        'min_duration': 1200,
        'max_duration': 5400
    }
]

# User data (50 male, 50 female)
USERS = {
    'male': [
        ('james.smith', 'Windows'),
        ('robert.williams', 'macOS'),
        ('michael.jones', 'Windows'),
        ('william.miller', 'macOS'),
        ('david.rodriguez', 'Windows'),
        ('richard.hernandez', 'Windows'),
        ('joseph.gonzalez', 'Windows'),
        ('thomas.anderson', 'Windows'),
        ('charles.taylor', 'macOS'),
        ('christopher.jackson', 'Windows'),
        ('daniel.lee', 'Windows'),
        ('matthew.thompson', 'Windows'),
        ('anthony.harris', 'Windows'),
        ('mark.clark', 'macOS'),
        ('donald.lewis', 'Windows'),
        ('steven.walker', 'Windows'),
        ('paul.allen', 'Windows'),
        ('andrew.hernandez', 'Windows'),
        ('joshua.wright', 'macOS'),
        ('kenneth.hill', 'Windows'),
        ('kevin.green', 'Windows'),
        ('brian.baker', 'Windows'),
        ('george.nelson', 'Windows'),
        ('edward.mitchell', 'macOS'),
        ('ronald.roberts', 'Windows'),
        ('timothy.phillips', 'Windows'),
        ('jason.parker', 'Windows'),
        ('jeffrey.edwards', 'Windows'),
        ('ryan.stewart', 'macOS'),
        ('jacob.morris', 'Windows'),
        ('gary.rogers', 'Windows'),
        ('nicholas.cook', 'Windows'),
        ('eric.morgan', 'Windows'),
        ('jonathan.cooper', 'macOS'),
        ('stephen.peterson', 'Windows'),
        ('larry.ward', 'Windows'),
        ('justin.torres', 'Windows'),
        ('scott.gray', 'Windows'),
        ('brandon.james', 'macOS'),
        ('benjamin.brooks', 'Windows'),
        ('samuel.sanders', 'Windows'),
        ('gregory.bennett', 'Windows'),
        ('alexander.barnes', 'Windows'),
        ('patrick.henderson', 'macOS'),
        ('frank.jenkins', 'Windows'),
        ('raymond.powell', 'Windows'),
        ('jack.hughes', 'Windows'),
        ('dennis.washington', 'Windows'),
        ('jerry.simmons', 'macOS'),
        ('tyler.gonzales', 'Windows')
    ],
    'female': [
        ('mary.johnson', 'Windows'),
        ('patricia.brown', 'Linux'),
        ('jennifer.garcia', 'Windows'),
        ('elizabeth.davis', 'Windows'),
        ('barbara.martinez', 'Linux'),
        ('susan.lopez', 'macOS'),
        ('jessica.wilson', 'Linux'),
        ('sarah.thomas', 'Windows'),
        ('karen.moore', 'Windows'),
        ('nancy.martin', 'Linux'),
        ('lisa.perez', 'macOS'),
        ('betty.white', 'Linux'),
        ('helen.sanchez', 'Windows'),
        ('sandra.ramirez', 'Windows'),
        ('donna.robinson', 'Linux'),
        ('carol.hall', 'macOS'),
        ('ruth.young', 'Linux'),
        ('sharon.king', 'Windows'),
        ('michelle.lopez', 'Windows'),
        ('laura.scott', 'Linux'),
        ('emily.adams', 'macOS'),
        ('kimberly.gonzalez', 'Linux'),
        ('deborah.carter', 'Windows'),
        ('dorothy.perez', 'Windows'),
        ('lisa.turner', 'Linux'),
        ('nancy.campbell', 'macOS'),
        ('karen.evans', 'Linux'),
        ('betty.collins', 'Windows'),
        ('helen.clark', 'Windows'),
        ('sandra.murphy', 'Linux'),
        ('donna.reed', 'macOS'),
        ('carol.bailey', 'Linux'),
        ('ruth.rivera', 'Windows'),
        ('sharon.richardson', 'Windows'),
        ('michelle.cox', 'Linux'),
        ('laura.howard', 'macOS'),
        ('sarah.peterson', 'Linux'),
        ('kimberly.ramirez', 'Windows'),
        ('deborah.watson', 'Windows'),
        ('dorothy.kelly', 'Linux'),
        ('lisa.price', 'macOS'),
        ('nancy.wood', 'Linux'),
        ('karen.ross', 'Windows'),
        ('betty.coleman', 'Windows'),
        ('helen.perry', 'Linux'),
        ('maria.long', 'macOS'),
        ('donna.flores', 'Linux'),
        ('carol.butler', 'Windows'),
        ('ruth.foster', 'Windows'),
        ('sharon.bryant', 'Linux')
    ]
}

def create_database_connection(db_path: str) -> sqlite3.Connection:
    """Create and return database connection"""
    return sqlite3.connect(db_path)

def insert_app_list_data(cursor: sqlite3.Cursor) -> None:
    """Insert sample data into app_list table"""
    print("🔄 Inserting app_list data...")
    
    insert_sql = """
    INSERT OR IGNORE INTO app_list (
        app_name, app_type, current_version, released_date, publisher, 
        description, download_link, enable_tracking, track_usage, 
        track_location, track_cm, track_intr, registered_date
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    for app in APPLICATIONS:
        cursor.execute(insert_sql, (
            app['app_name'],
            app['app_type'],
            app['current_version'],
            app['released_date'],
            app['publisher'],
            app['description'],
            app['download_link'],
            app['enable_tracking'],
            app['track_usage'],
            app['track_location'],
            app['track_cm'],
            app['track_intr'],
            app['registered_date']
        ))
    
    print(f"✅ Inserted {len(APPLICATIONS)} applications into app_list")

def get_all_users() -> List[Tuple[str, str]]:
    """Get combined list of all users with their platforms"""
    all_users = []
    all_users.extend(USERS['male'])
    all_users.extend(USERS['female'])
    return all_users

def generate_usage_data_for_date(cursor: sqlite3.Cursor, date: datetime.date, 
                                 users: List[Tuple[str, str]], 
                                 apps: List[Dict]) -> int:
    """Generate usage data for a specific date"""
    records_generated = 0
    
    insert_sql = """
    INSERT INTO app_usage (
        monitor_app_version, platform, user, application_name, application_version,
        log_date, legacy_app, duration_seconds
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    # Each day, randomly select users and apps for usage
    for user_name, user_platform in users:
        # Each user has a 70% chance to use applications on any given day
        if random.random() < 0.7:
            # Select 1-4 random applications for this user on this day
            num_apps = random.randint(1, 4)
            selected_apps = random.sample(apps, min(num_apps, len(apps)))
            
            for app in selected_apps:
                # Only track apps that have tracking enabled
                if app['enable_tracking']:
                    # Generate random duration within app's typical range
                    duration = random.randint(
                        app['min_duration'], 
                        app['max_duration']
                    )
                    
                    cursor.execute(insert_sql, (
                        MONITOR_APP_VERSION,
                        user_platform,
                        user_name,
                        app['app_name'],
                        app['current_version'],
                        date.strftime('%Y-%m-%d'),
                        0,  # legacy_app = False
                        duration
                    ))
                    records_generated += 1
    
    return records_generated

def insert_app_usage_data(cursor: sqlite3.Cursor) -> None:
    """Generate and insert sample usage data for the full year"""
    print("🔄 Generating app_usage data...")
    
    all_users = get_all_users()
    total_records = 0
    
    # Generate data for each day in the date range
    current_date = START_DATE
    while current_date <= END_DATE:
        # Show progress every month
        if current_date.day == 1:
            print(f"📅 Generating data for {current_date.strftime('%B %Y')}...")
        
        daily_records = generate_usage_data_for_date(
            cursor, current_date, all_users, APPLICATIONS
        )
        total_records += daily_records
        
        current_date += datetime.timedelta(days=1)
    
    print(f"✅ Generated {total_records} usage records for {(END_DATE - START_DATE).days + 1} days")

def create_indexes(cursor: sqlite3.Cursor) -> None:
    """Create performance indexes"""
    print("🔄 Creating indexes...")
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_app_usage_user ON app_usage(user)",
        "CREATE INDEX IF NOT EXISTS idx_app_usage_date ON app_usage(log_date)",
        "CREATE INDEX IF NOT EXISTS idx_app_usage_app ON app_usage(application_name)"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    print("✅ Indexes created successfully")

def show_statistics(cursor: sqlite3.Cursor) -> None:
    """Show statistics about generated data"""
    print("\n📊 Data Generation Statistics:")
    print("=" * 50)
    
    # App list count
    cursor.execute("SELECT COUNT(*) FROM app_list")
    app_count = cursor.fetchone()[0]
    print(f"Applications: {app_count}")
    
    # Usage records count
    cursor.execute("SELECT COUNT(*) FROM app_usage")
    usage_count = cursor.fetchone()[0]
    print(f"Usage records: {usage_count:,}")
    
    # Unique users
    cursor.execute("SELECT COUNT(DISTINCT user) FROM app_usage")
    user_count = cursor.fetchone()[0]
    print(f"Unique users: {user_count}")
    
    # Date range
    cursor.execute("SELECT MIN(log_date), MAX(log_date) FROM app_usage")
    min_date, max_date = cursor.fetchone()
    print(f"Date range: {min_date} to {max_date}")
    
    # Total usage time
    cursor.execute("SELECT SUM(duration_seconds) FROM app_usage")
    total_seconds = cursor.fetchone()[0]
    total_hours = total_seconds / 3600 if total_seconds else 0
    print(f"Total usage time: {total_hours:,.1f} hours")
    
    # Most popular app
    cursor.execute("""
        SELECT application_name, COUNT(*) as usage_count 
        FROM app_usage 
        GROUP BY application_name 
        ORDER BY usage_count DESC 
        LIMIT 1
    """)
    result = cursor.fetchone()
    if result:
        app_name, usage_count = result
        print(f"Most used app: {app_name} ({usage_count:,} sessions)")

def main():
    """Main function to generate all sample data"""
    print("🚀 App Usage Sample Data Generator")
    print("=" * 50)
    
    # Check if database exists
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Database not found: {DATABASE_PATH}")
        print("Please run the schema.sql file first to create the database structure.")
        return
    
    try:
        # Connect to database
        conn = create_database_connection(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Generate data
        insert_app_list_data(cursor)
        insert_app_usage_data(cursor)
        create_indexes(cursor)
        
        # Commit changes
        conn.commit()
        
        # Show statistics
        show_statistics(cursor)
        
        print("\n🎉 Sample data generation completed successfully!")
        print(f"Database: {os.path.abspath(DATABASE_PATH)}")
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
