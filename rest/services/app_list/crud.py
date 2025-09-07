"""
CRUD operations for App List domain.
"""
import logging
import json
from typing import List, Optional, Dict, Any
from core.database import get_db_transaction, get_db_context
from core.exceptions import DatabaseError, NotFoundError, handle_database_error
from .models import AppListCreate, AppListUpdate, flatten_tracking_config

logger = logging.getLogger(__name__)

@handle_database_error
def create_app_list(app_list: AppListCreate) -> int:
    """
    Create new app list entry.
    Returns the ID of the created record.
    """
    try:
        # Log the received data
        logger.info(f"Creating app list entry for: {app_list.app_name}")
        logger.debug(f"App list details: {json.dumps(app_list.dict(), indent=2)}")

        # Flatten tracking configuration
        tracking_config = flatten_tracking_config(app_list.track)

        with get_db_transaction() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO app_list
                (app_name, app_type, current_version, released_date, publisher,
                 description, download_link, enable_tracking, track_usage,
                 track_location, track_cm, track_intr, registered_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                app_list.app_name, app_list.app_type, app_list.current_version,
                app_list.released_date, app_list.publisher, app_list.description,
                app_list.download_link, app_list.enable_tracking,
                tracking_config['track_usage'], tracking_config['track_location'],
                tracking_config['track_cm'], tracking_config['track_intr'],
                app_list.registered_date
            ))

            record_id = cursor.lastrowid
            logger.info(f"Successfully created app list entry (ID: {record_id})")
            return record_id

    except Exception as e:
        logger.error(f"Failed to create app list entry for {app_list.app_name}: {e}")
        raise DatabaseError(f"Failed to create app list entry: {str(e)}")

@handle_database_error
def create_or_update_app_list(app_list: AppListCreate) -> int:
    """
    Create new app list entry or update existing one.
    If an entry exists with the same app_name, app_type, and current_version,
    it will be updated. Otherwise, a new entry is created.
    Returns the ID of the created or updated record.
    """
    try:
        # Log the received data
        logger.info(f"Processing app list entry for: {app_list.app_name}")
        logger.debug(f"App list details: {json.dumps(app_list.dict(), indent=2)}")

        # Flatten tracking configuration
        tracking_config = flatten_tracking_config(app_list.track)

        with get_db_transaction() as conn:
            cursor = conn.cursor()

            # Check if a record exists with the same app_name, app_type, and current_version
            cursor.execute('''
                SELECT app_id FROM app_list
                WHERE app_name = ? AND app_type = ? AND current_version = ?
            ''', (app_list.app_name, app_list.app_type, app_list.current_version))

            existing_record = cursor.fetchone()

            if existing_record:
                # Update existing record
                record_id = existing_record['app_id']
                logger.info(f"Updating existing app list entry (ID: {record_id})")

                cursor.execute('''
                    UPDATE app_list SET
                    released_date = ?, publisher = ?, description = ?, download_link = ?,
                    enable_tracking = ?, track_usage = ?, track_location = ?,
                    track_cm = ?, track_intr = ?, registered_date = ?
                    WHERE app_id = ?
                ''', (
                    app_list.released_date, app_list.publisher, app_list.description,
                    app_list.download_link, app_list.enable_tracking,
                    tracking_config['track_usage'], tracking_config['track_location'],
                    tracking_config['track_cm'], tracking_config['track_intr'],
                    app_list.registered_date, record_id
                ))

                logger.info(f"Successfully updated app list entry (ID: {record_id})")
                return record_id
            else:
                # Create new record
                logger.info(f"Creating new app list entry")

                cursor.execute('''
                    INSERT INTO app_list
                    (app_name, app_type, current_version, released_date, publisher,
                     description, download_link, enable_tracking, track_usage,
                     track_location, track_cm, track_intr, registered_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    app_list.app_name, app_list.app_type, app_list.current_version,
                    app_list.released_date, app_list.publisher, app_list.description,
                    app_list.download_link, app_list.enable_tracking,
                    tracking_config['track_usage'], tracking_config['track_location'],
                    tracking_config['track_cm'], tracking_config['track_intr'],
                    app_list.registered_date
                ))

                record_id = cursor.lastrowid
                logger.info(f"Successfully created new app list entry (ID: {record_id})")
                return record_id

    except Exception as e:
        logger.error(f"Failed to create/update app list entry for {app_list.app_name}: {e}")
        raise DatabaseError(f"Failed to create/update app list entry: {str(e)}")

@handle_database_error
def get_app_list_by_id(app_id: int) -> Optional[Dict[str, Any]]:
    """Get app list entry by ID."""
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM app_list WHERE app_id = ?", (app_id,))
            row = cursor.fetchone()

            if row:
                data = _row_to_dict(row)
                logger.info(f"Retrieved app list entry (ID: {app_id})")
                return data
            else:
                logger.info(f"App list entry not found (ID: {app_id})")
                return None

    except Exception as e:
        logger.error(f"Failed to retrieve app list entry (ID: {app_id}): {e}")
        raise DatabaseError(f"Failed to retrieve app list entry: {str(e)}")

@handle_database_error
def get_app_list(skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    """Retrieve app list entries with pagination."""
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Get total count
            cursor.execute("SELECT COUNT(*) as total FROM app_list")
            total = cursor.fetchone()['total']
            
            # Get paginated data
            cursor.execute("""
                SELECT * FROM app_list 
                ORDER BY registered_date DESC, app_id DESC 
                LIMIT ? OFFSET ?
            """, (limit, skip))
            rows = cursor.fetchall()

            data = [_row_to_dict(row) for row in rows]
            logger.info(f"Retrieved {len(data)} app list entries (total: {total})")
            
            return {
                "app_list": data,
                "total": total
            }

    except Exception as e:
        logger.error(f"Failed to retrieve app list: {e}")
        raise DatabaseError(f"Failed to retrieve app list: {str(e)}")

@handle_database_error
def update_app_list(app_id: int, app_list_update: AppListUpdate) -> bool:
    """Update app list entry."""
    try:
        # Get current record
        current_record = get_app_list_by_id(app_id)
        if not current_record:
            raise NotFoundError(f"App list entry not found (ID: {app_id})")

        # Build update query dynamically
        update_fields = []
        update_values = []
        
        for field, value in app_list_update.dict(exclude_unset=True).items():
            if field == 'track' and value is not None:
                # Handle tracking configuration
                tracking_config = flatten_tracking_config(value)
                for track_field, track_value in tracking_config.items():
                    update_fields.append(f'{track_field} = ?')
                    update_values.append(track_value)
            elif value is not None:
                update_fields.append(f'{field} = ?')
                update_values.append(value)
        
        if not update_fields:
            logger.info(f"No fields to update for app list entry (ID: {app_id})")
            return True

        update_values.append(app_id)

        with get_db_transaction() as conn:
            cursor = conn.cursor()
            query = f"UPDATE app_list SET {', '.join(update_fields)} WHERE app_id = ?"
            cursor.execute(query, update_values)
            
            if cursor.rowcount > 0:
                logger.info(f"Successfully updated app list entry (ID: {app_id})")
                return True
            else:
                logger.warning(f"No rows updated for app list entry (ID: {app_id})")
                return False

    except Exception as e:
        logger.error(f"Failed to update app list entry (ID: {app_id}): {e}")
        raise DatabaseError(f"Failed to update app list entry: {str(e)}")

@handle_database_error
def delete_app_list(app_id: int) -> bool:
    """Delete app list entry."""
    try:
        with get_db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM app_list WHERE app_id = ?", (app_id,))
            
            if cursor.rowcount > 0:
                logger.info(f"Successfully deleted app list entry (ID: {app_id})")
                return True
            else:
                logger.warning(f"App list entry not found for deletion (ID: {app_id})")
                return False

    except Exception as e:
        logger.error(f"Failed to delete app list entry (ID: {app_id}): {e}")
        raise DatabaseError(f"Failed to delete app list entry: {str(e)}")

@handle_database_error
def get_app_list_by_name(app_name: str) -> List[Dict[str, Any]]:
    """Get app list entries by app name."""
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM app_list WHERE app_name = ? ORDER BY current_version DESC", (app_name,))
            rows = cursor.fetchall()

            data = [_row_to_dict(row) for row in rows]
            logger.info(f"Retrieved {len(data)} app list entries for app: {app_name}")
            return data

    except Exception as e:
        logger.error(f"Failed to retrieve app list entries for app {app_name}: {e}")
        raise DatabaseError(f"Failed to retrieve app list entries for app: {str(e)}")

@handle_database_error
def get_app_list_by_type(app_type: str) -> List[Dict[str, Any]]:
    """Get app list entries by app type."""
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM app_list WHERE app_type = ? ORDER BY app_name", (app_type,))
            rows = cursor.fetchall()

            data = [_row_to_dict(row) for row in rows]
            logger.info(f"Retrieved {len(data)} app list entries for type: {app_type}")
            return data

    except Exception as e:
        logger.error(f"Failed to retrieve app list entries for type {app_type}: {e}")
        raise DatabaseError(f"Failed to retrieve app list entries for type: {str(e)}")

@handle_database_error
def get_app_list_summary() -> Dict[str, Any]:
    """Get summary statistics for app list."""
    try:
        with get_db_context() as conn:
            cursor = conn.cursor()

            # Get total apps and tracking status
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_apps,
                    SUM(CASE WHEN enable_tracking = 1 THEN 1 ELSE 0 END) as enabled_tracking,
                    SUM(CASE WHEN enable_tracking = 0 THEN 1 ELSE 0 END) as disabled_tracking
                FROM app_list
            ''')
            result = cursor.fetchone()

            # Get app types distribution
            cursor.execute('''
                SELECT app_type, COUNT(*) as count
                FROM app_list
                GROUP BY app_type
                ORDER BY count DESC
            ''')
            app_types = {row['app_type']: row['count'] for row in cursor.fetchall()}

            # Get publishers distribution
            cursor.execute('''
                SELECT publisher, COUNT(*) as count
                FROM app_list
                GROUP BY publisher
                ORDER BY count DESC
                LIMIT 10
            ''')
            publishers = {row['publisher']: row['count'] for row in cursor.fetchall()}

            summary = {
                "total_apps": result['total_apps'],
                "enabled_tracking": result['enabled_tracking'],
                "disabled_tracking": result['disabled_tracking'],
                "app_types": app_types,
                "publishers": publishers
            }

            logger.info(f"Retrieved app list summary: {result['total_apps']} total apps")
            return summary

    except Exception as e:
        logger.error(f"Failed to get app list summary: {e}")
        raise DatabaseError(f"Failed to get app list summary: {str(e)}")

def _row_to_dict(row) -> Dict[str, Any]:
    """Convert a database row to the expected dictionary format."""
    return {
        "app_id": row["app_id"],
        "app_name": row["app_name"],
        "app_type": row["app_type"],
        "current_version": row["current_version"],
        "released_date": row["released_date"],
        "publisher": row["publisher"],
        "description": row["description"],
        "download_link": row["download_link"],
        "enable_tracking": bool(row["enable_tracking"]),
        "track_usage": bool(row["track_usage"]),
        "track_location": bool(row["track_location"]),
        "track_cm": bool(row["track_cm"]),
        "track_intr": row["track_intr"],
        "registered_date": row["registered_date"]
    }
