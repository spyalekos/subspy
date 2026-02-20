"""
SubsPy - Database Layer
SQLite database operations for income/expense management.
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List, Tuple

from platform_utils import get_data_dir


def get_db_path() -> str:
    """Get database path based on platform."""
    app_dir = get_data_dir()
    os.makedirs(app_dir, exist_ok=True)
    return os.path.join(app_dir, 'subscriptions.db')


def get_connection() -> sqlite3.Connection:
    """Get database connection."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_database() -> None:
    """Initialize database with schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            charge_date DATE NOT NULL,
            amount REAL NOT NULL,
            repeat_days INTEGER DEFAULT 0,
            category TEXT DEFAULT '',
            entry_type TEXT DEFAULT 'expense'
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # Run migration for existing databases
    _migrate_add_entry_type()


def _migrate_add_entry_type() -> None:
    """Add entry_type column if missing and migrate negative amounts to income."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(subscriptions)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'entry_type' not in columns:
        cursor.execute("ALTER TABLE subscriptions ADD COLUMN entry_type TEXT DEFAULT 'expense'")
        # Migrate: negative amounts become income with positive value
        cursor.execute("""
            UPDATE subscriptions
            SET entry_type = 'income', amount = ABS(amount)
            WHERE amount < 0
        """)
        conn.commit()
    
    conn.close()


def add_subscription(
    description: str,
    charge_date: str,
    amount: float,
    repeat_days: int = 0,
    category: str = "",
    entry_type: str = "expense"
) -> int:
    """Add a new entry and return its ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO subscriptions (description, charge_date, amount, repeat_days, category, entry_type)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (description, charge_date, amount, repeat_days, category, entry_type))
    
    subscription_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return subscription_id


def update_subscription(
    subscription_id: int,
    description: str,
    charge_date: str,
    amount: float,
    repeat_days: int = 0,
    category: str = "",
    entry_type: str = "expense"
) -> bool:
    """Update an existing entry."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE subscriptions
        SET description = ?, charge_date = ?, amount = ?, repeat_days = ?, category = ?, entry_type = ?
        WHERE id = ?
    ''', (description, charge_date, amount, repeat_days, category, entry_type, subscription_id))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


def delete_subscription(subscription_id: int) -> bool:
    """Delete a subscription by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM subscriptions WHERE id = ?', (subscription_id,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


def get_all_subscriptions() -> List[dict]:
    """Get all entries."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, description, charge_date, amount, repeat_days, category, entry_type
        FROM subscriptions
        ORDER BY charge_date
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def get_subscription_by_id(subscription_id: int) -> Optional[dict]:
    """Get a single entry by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, description, charge_date, amount, repeat_days, category, entry_type
        FROM subscriptions
        WHERE id = ?
    ''', (subscription_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def get_progressive_charges(from_date: str, to_date: str) -> List[dict]:
    """
    Calculate progressive charges between two dates.
    Returns list of upcoming charges sorted by date.
    """
    subscriptions = get_all_subscriptions()
    charges = []
    
    from_dt = datetime.strptime(from_date, '%Y-%m-%d')
    to_dt = datetime.strptime(to_date, '%Y-%m-%d')
    
    for sub in subscriptions:
        charge_dt = datetime.strptime(sub['charge_date'], '%Y-%m-%d')
        repeat_days = sub['repeat_days']
        
        if repeat_days == 0:
            # Non-repeating: only include if within range
            if from_dt <= charge_dt <= to_dt:
                charges.append({
                    'date': sub['charge_date'],
                    'description': sub['description'],
                    'amount': sub['amount'],
                    'category': sub['category'],
                    'entry_type': sub.get('entry_type', 'expense'),
                    'subscription_id': sub['id']
                })
        else:
            # Repeating subscription
            current_dt = charge_dt
            
            # Find the first occurrence on or after from_date
            while current_dt < from_dt:
                current_dt += timedelta(days=repeat_days)
            
            # Add all occurrences within the range
            while current_dt <= to_dt:
                charges.append({
                    'date': current_dt.strftime('%Y-%m-%d'),
                    'description': sub['description'],
                    'amount': sub['amount'],
                    'category': sub['category'],
                    'entry_type': sub.get('entry_type', 'expense'),
                    'subscription_id': sub['id']
                })
                current_dt += timedelta(days=repeat_days)
    
    # Sort by date
    charges.sort(key=lambda x: x['date'])
    return charges


def get_categories() -> List[str]:
    """Get list of existing categories."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DISTINCT category FROM subscriptions
        WHERE category != ''
        ORDER BY category
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [row['category'] for row in rows]


def add_category(name: str) -> bool:
    """Add a category."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create categories table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    
    try:
        cursor.execute('INSERT INTO categories (name) VALUES (?)', (name,))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False  # Category already exists
    
    conn.close()
    return success


def delete_category(name: str) -> bool:
    """Delete a category by name."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM categories WHERE name = ?', (name,))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


def get_all_categories() -> List[str]:
    """Get list of all categories from database."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    
    cursor.execute('SELECT name FROM categories ORDER BY name')
    rows = cursor.fetchall()
    conn.close()
    
    return [row['name'] for row in rows]


def get_custom_categories() -> List[str]:
    """Alias for get_all_categories for backward compatibility."""
    return get_all_categories()


def init_default_categories() -> None:
    """Initialize default categories if the categories table is empty."""
    default_cats = [
        "Streaming",
        "Λογισμικό",
        "Υπηρεσίες Internet",
        "Ασφάλειες",
        "Συνδρομές",
        "Μισθός",
        "Έσοδα",
        "Άλλο"
    ]
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create categories table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Check if table is empty
    cursor.execute('SELECT COUNT(*) FROM categories')
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Insert default categories
        for cat in default_cats:
            try:
                cursor.execute('INSERT INTO categories (name) VALUES (?)', (cat,))
            except sqlite3.IntegrityError:
                pass
        conn.commit()
    
    conn.close()


def export_database(filepath: str) -> Tuple[bool, str]:
    """Export all data to JSON file. Returns (success, message)."""
    try:
        subscriptions = get_all_subscriptions()
        custom_categories = get_custom_categories()
        data = {
            'version': '1.1',
            'export_date': datetime.now().isoformat(),
            'subscriptions': subscriptions,
            'categories': custom_categories
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True, filepath
    except PermissionError as e:
        return False, f"Δεν επιτρέπεται η πρόσβαση: {e}"
    except Exception as e:
        return False, f"Σφάλμα εξαγωγής: {e}"


def import_database(filepath: str, replace: bool = True) -> Tuple[bool, str]:
    """
    Import data from JSON file.
    If replace=True, clears existing data first.
    Returns (success, message).
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        subscriptions = data.get('subscriptions', [])
        
        if not subscriptions:
            return False, "Δεν βρέθηκαν καταχωρήσεις στο αρχείο."
        
        conn = get_connection()
        cursor = conn.cursor()
        
        if replace:
            cursor.execute('DELETE FROM subscriptions')
        
        count = 0
        for sub in subscriptions:
            cursor.execute('''
                INSERT INTO subscriptions (description, charge_date, amount, repeat_days, category, entry_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                sub.get('description', ''),
                sub.get('charge_date', ''),
                sub.get('amount', 0),
                sub.get('repeat_days', 0),
                sub.get('category', ''),
                sub.get('entry_type', 'expense')
            ))
            count += 1
        
        # Import custom categories if present
        categories = data.get('categories', [])
        if categories:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            ''')
            for cat_name in categories:
                try:
                    cursor.execute('INSERT INTO categories (name) VALUES (?)', (cat_name,))
                except sqlite3.IntegrityError:
                    pass  # Category already exists
        
        conn.commit()
        conn.close()
        
        return True, f"Εισήχθησαν {count} καταχωρήσεις επιτυχώς."
    except json.JSONDecodeError:
        return False, "Μη έγκυρο αρχείο JSON."
    except Exception as e:
        return False, f"Σφάλμα εισαγωγής: {e}"


# Initialize database on module load
init_database()
init_default_categories()

