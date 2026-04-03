"""
Database module - handles SQLite connection, schema creation,
and seeding with initial data (roles + demo users).
"""

import sqlite3
import os

# path to the database file (same folder as this script)
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'finance.db')


def get_db():
    """
    Get a database connection. Uses Row factory so we can
    access columns by name instead of index.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # enable foreign key support
    return conn


def init_db():
    """
    Create all tables if they don't exist and insert
    default data (roles and demo users).
    Called once when the app starts up.
    """
    conn = get_db()
    cursor = conn.cursor()

    # --- Create tables ---

    # Roles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT
        )
    ''')

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role_id INTEGER NOT NULL,
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (role_id) REFERENCES roles(id)
        )
    ''')

    # Financial records table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            type TEXT CHECK(type IN ('income', 'expense')),
            category TEXT NOT NULL,
            description TEXT,
            record_date DATE NOT NULL,
            is_deleted INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Audit log table (for tracking operations)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id INTEGER,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    conn.commit()

    # --- Seed default data ---
    _seed_roles(conn)
    _seed_demo_users(conn)
    _seed_sample_records(conn)

    conn.close()
    print("[+] Database initialized successfully!")


def _seed_roles(conn):
    """Insert the 3 predefined roles if they don't exist yet"""
    cursor = conn.cursor()

    roles = [
        ('viewer', 'Can only view dashboard data and own records'),
        ('analyst', 'Can create, view, update, delete own records and access analytics'),
        ('admin', 'Full access to everything - records, users, dashboard')
    ]

    for name, description in roles:
        # check if role already exists
        existing = cursor.execute(
            "SELECT id FROM roles WHERE name = ?", (name,)
        ).fetchone()

        if not existing:
            cursor.execute(
                "INSERT INTO roles (name, description) VALUES (?, ?)",
                (name, description)
            )

    conn.commit()


def _seed_demo_users(conn):
    """Create the 3 demo users if they don't exist"""
    cursor = conn.cursor()

    # get role IDs
    viewer_role = cursor.execute(
        "SELECT id FROM roles WHERE name = 'viewer'"
    ).fetchone()
    analyst_role = cursor.execute(
        "SELECT id FROM roles WHERE name = 'analyst'"
    ).fetchone()
    admin_role = cursor.execute(
        "SELECT id FROM roles WHERE name = 'admin'"
    ).fetchone()

    demo_users = [
        ('viewer_user', 'viewer@example.com', 'viewer123', viewer_role['id']),
        ('analyst_user', 'analyst@example.com', 'analyst123', analyst_role['id']),
        ('admin_user', 'admin@example.com', 'admin123', admin_role['id']),
    ]

    for username, email, password, role_id in demo_users:
        existing = cursor.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()

        if not existing:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, role_id) VALUES (?, ?, ?, ?)",
                (username, email, password, role_id)
            )

    conn.commit()


def _seed_sample_records(conn):
    """
    Insert some sample financial records for demo purposes.
    Only inserts if there are no records yet.
    """
    cursor = conn.cursor()

    count = cursor.execute("SELECT COUNT(*) as cnt FROM financial_records").fetchone()['cnt']
    if count > 0:
        return  # already have records, skip

    # get user IDs
    analyst = cursor.execute(
        "SELECT id FROM users WHERE username = 'analyst_user'"
    ).fetchone()
    admin = cursor.execute(
        "SELECT id FROM users WHERE username = 'admin_user'"
    ).fetchone()
    viewer = cursor.execute(
        "SELECT id FROM users WHERE username = 'viewer_user'"
    ).fetchone()

    if not analyst or not admin or not viewer:
        return

    # sample records for analyst_user
    sample_records = [
        # analyst_user records
        (analyst['id'], 50000.00, 'income', 'Salary', 'Monthly salary - January', '2024-01-31'),
        (analyst['id'], 50000.00, 'income', 'Salary', 'Monthly salary - February', '2024-02-29'),
        (analyst['id'], 50000.00, 'income', 'Salary', 'Monthly salary - March', '2024-03-31'),
        (analyst['id'], 12000.00, 'expense', 'Rent', 'Monthly rent payment', '2024-01-05'),
        (analyst['id'], 12000.00, 'expense', 'Rent', 'Monthly rent payment', '2024-02-05'),
        (analyst['id'], 12000.00, 'expense', 'Rent', 'Monthly rent payment', '2024-03-05'),
        (analyst['id'], 3500.00, 'expense', 'Groceries', 'Weekly groceries', '2024-01-10'),
        (analyst['id'], 4200.00, 'expense', 'Groceries', 'Weekly groceries', '2024-02-10'),
        (analyst['id'], 2000.00, 'expense', 'Transport', 'Metro pass', '2024-01-15'),
        (analyst['id'], 5000.00, 'income', 'Freelance', 'Weekend project payment', '2024-02-20'),
        (analyst['id'], 1500.00, 'expense', 'Entertainment', 'Movie and dinner', '2024-03-15'),
        (analyst['id'], 8000.00, 'income', 'Freelance', 'Website design project', '2024-03-20'),

        # admin_user records
        (admin['id'], 80000.00, 'income', 'Salary', 'Monthly salary', '2024-01-31'),
        (admin['id'], 80000.00, 'income', 'Salary', 'Monthly salary', '2024-02-29'),
        (admin['id'], 25000.00, 'expense', 'Rent', 'Apartment rent', '2024-01-05'),
        (admin['id'], 25000.00, 'expense', 'Rent', 'Apartment rent', '2024-02-05'),
        (admin['id'], 15000.00, 'income', 'Investment', 'Stock dividends', '2024-02-15'),
        (admin['id'], 6000.00, 'expense', 'Groceries', 'Monthly groceries', '2024-01-12'),
        (admin['id'], 3000.00, 'expense', 'Utilities', 'Electricity and water', '2024-02-10'),
        (admin['id'], 10000.00, 'expense', 'Shopping', 'New laptop accessories', '2024-03-01'),

        # viewer_user records (added by admin in real scenario)
        (viewer['id'], 30000.00, 'income', 'Salary', 'Part-time salary', '2024-01-31'),
        (viewer['id'], 30000.00, 'income', 'Salary', 'Part-time salary', '2024-02-29'),
        (viewer['id'], 8000.00, 'expense', 'Rent', 'Room rent', '2024-01-05'),
        (viewer['id'], 8000.00, 'expense', 'Rent', 'Room rent', '2024-02-05'),
        (viewer['id'], 2500.00, 'expense', 'Food', 'Mess charges', '2024-01-10'),
        (viewer['id'], 1000.00, 'expense', 'Transport', 'Bus pass', '2024-02-01'),
    ]

    for record in sample_records:
        cursor.execute(
            """INSERT INTO financial_records
               (user_id, amount, type, category, description, record_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            record
        )

    conn.commit()
    print(f"[+] Inserted {len(sample_records)} sample financial records")


def log_audit(user_id, action, resource_type, resource_id=None, details=None):
    """
    Log an action to the audit log table.
    Called after create/update/delete operations.
    """
    try:
        conn = get_db()
        conn.execute(
            """INSERT INTO audit_log (user_id, action, resource_type, resource_id, details)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, action, resource_type, resource_id, details)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        # don't let audit logging errors break the app
        print(f"[!] Audit log error: {e}")
