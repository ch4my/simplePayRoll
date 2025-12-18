import sqlite3
import hashlib
import secrets
from datetime import datetime

DB_PATH = "payroll.db"
AUTH_DB_PATH = "auth.db"

_conn = None
_cursor = None

_auth_conn = None
_auth_cursor = None

# constants duplicated from method.py for safe migration
_BASIC = 25000
_HRA = 5000
_CONVEYANCE = 2500
_TAX = 500
_HEALTH_INSURANCE = 1500

def _compute_deduction(loan: int) -> int:
    return _TAX + _HEALTH_INSURANCE + max(0, int(loan))

def _compute_overall() -> int:
    # kept for compatibility but avoid using this alone for rows that have loan
    return _BASIC + _HRA + _CONVEYANCE - (_TAX + _HEALTH_INSURANCE)

def connect():
    """
    Open DB and ensure the salaries table has deduction and overall_salary columns.
    If columns are missing, ALTER the table and backfill values for existing rows.
    """
    global _conn, _cursor
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH)
        _cursor = _conn.cursor()
        # Create table if it doesn't exist (may be older schema without new columns)
        _cursor.execute('''
        CREATE TABLE IF NOT EXISTS salaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company_id TEXT NOT NULL,
            age INTEGER,
            role TEXT,
            department TEXT,
            months INTEGER,
            loan INTEGER,
            total_salary INTEGER,
            created_at TEXT
        )
        ''')
        _conn.commit()

        # Inspect columns
        _cursor.execute("PRAGMA table_info('salaries')")
        cols = [_r[1] for _r in _cursor.fetchall()]

        # If deduction column missing, add deduction and overall_salary columns
        added = False
        if 'deduction' not in cols:
            _cursor.execute("ALTER TABLE salaries ADD COLUMN deduction INTEGER DEFAULT 0")
            added = True
        if 'overall_salary' not in cols:
            _cursor.execute("ALTER TABLE salaries ADD COLUMN overall_salary INTEGER DEFAULT 0")
            added = True

        # Add optional start/end month columns for display if missing
        if 'start_month' not in cols:
            _cursor.execute("ALTER TABLE salaries ADD COLUMN start_month TEXT")
        if 'end_month' not in cols:
            _cursor.execute("ALTER TABLE salaries ADD COLUMN end_month TEXT")
        # Add currency column to persist selected currency per record
        if 'currency' not in cols:
            _cursor.execute("ALTER TABLE salaries ADD COLUMN currency TEXT DEFAULT 'PHP'")

        if added:
            # Backfill existing rows: compute deduction and overall_salary from loan/total_salary when possible
            # Rows may have loan stored; if not, assume 0.
            _cursor.execute("SELECT id, loan FROM salaries")
            rows = _cursor.fetchall()
            for rid, loan in rows:
                loan_val = int(loan) if loan is not None else 0
                ded = _compute_deduction(loan_val)
                # overall must subtract the same deduction (including loan)
                overall = (_BASIC + _HRA + _CONVEYANCE) - ded
                # store per-month overall (net) and deduction
                _cursor.execute("UPDATE salaries SET deduction = ?, overall_salary = ? WHERE id = ?", (ded, overall, rid))
            _conn.commit()

    return _conn, _cursor

def insert_salary(record):
    conn, cursor = connect()
    # ensure keys exist (for old callers that only provided total_salary)
    deduction = record.get('deduction', _compute_deduction(record.get('loan', 0)))
    # compute overall per-month as gross pay minus the actual deduction (which includes loan)
    overall = record.get('overall_salary', (_BASIC + _HRA + _CONVEYANCE) - deduction)
    cursor.execute('''
        INSERT INTO salaries
        (name, company_id, age, role, department, months, loan, total_salary, deduction, overall_salary, created_at, start_month, end_month, currency)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        record.get('name'),
        record.get('company_id'),
        record.get('age'),
        record.get('role'),
        record.get('department'),
        record.get('months'),
        record.get('loan'),
        record.get('total_salary'),
        deduction,
        overall,
        datetime.utcnow().isoformat(),
        record.get('start_month'),
        record.get('end_month'),
        str(record.get('currency', 'PHP')).upper()
    ))
    conn.commit()

def fetch_all():
    conn, cursor = connect()
    # select in consistent order; if columns missing for some reason, PRAGMA ensures they exist
    cursor.execute('''
        SELECT id, name, company_id, age, role, department, months, loan, deduction, overall_salary, total_salary, created_at, start_month, end_month, currency
        FROM salaries ORDER BY id
    ''')
    return cursor.fetchall()

def fetch_one(record_id):
    conn, cursor = connect()
    cursor.execute('''
        SELECT id, name, company_id, age, role, department, months, loan, deduction, overall_salary, total_salary, created_at, start_month, end_month, currency
        FROM salaries WHERE id = ?
    ''', (record_id,))
    return cursor.fetchone()

def delete_data(record_id):
    conn, cursor = connect()
    cursor.execute('DELETE FROM salaries WHERE id = ?', (record_id,))
    conn.commit()

def close_connection():
    global _conn, _cursor
    if _conn:
        _conn.close()
        _conn = None
        _cursor = None

def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Hash password with salt using SHA-256."""
    if salt is None:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return pwd_hash, salt

def connect_auth():
    """Initialize authentication database with users table."""
    global _auth_conn, _auth_cursor
    if _auth_conn is None:
        _auth_conn = sqlite3.connect(AUTH_DB_PATH)
        _auth_cursor = _auth_conn.cursor()
        _auth_cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'user',
                created_at TEXT,
                last_login TEXT
            )
        ''')
        _auth_conn.commit()
    return _auth_conn, _auth_cursor

def create_user(username: str, email: str, password: str, full_name: str = "", role: str = "user") -> tuple[bool, str]:
    """
    Create a new user account.
    Returns (success: bool, message: str)
    """
    conn, cursor = connect_auth()
    
    # Validate inputs
    if not username.strip() or not email.strip() or not password.strip():
        return False, "Username, email, and password are required."
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    
    # Check if username or email already exists
    cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
    if cursor.fetchone():
        return False, "Username or email already exists."
    
    # Hash password and insert user
    pwd_hash, salt = hash_password(password)
    try:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, salt, full_name, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, email, pwd_hash, salt, full_name, role, datetime.utcnow().isoformat()))
        conn.commit()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "Username or email already exists."
    except Exception as e:
        return False, f"Error creating account: {str(e)}"

def authenticate_user(username: str, password: str) -> tuple[bool, str, dict]:
    """
    Authenticate user credentials.
    Returns (success: bool, message: str, user_data: dict)
    """
    conn, cursor = connect_auth()
    
    cursor.execute('''
        SELECT id, username, email, password_hash, salt, full_name, role
        FROM users WHERE username = ?
    ''', (username,))
    
    row = cursor.fetchone()
    if not row:
        return False, "Invalid username or password.", {}
    
    user_id, uname, email, stored_hash, salt, full_name, role = row
    
    # Verify password
    pwd_hash, _ = hash_password(password, salt)
    if pwd_hash != stored_hash:
        return False, "Invalid username or password.", {}
    
    # Update last login
    cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                   (datetime.utcnow().isoformat(), user_id))
    conn.commit()
    
    user_data = {
        'id': user_id,
        'username': uname,
        'email': email,
        'full_name': full_name,
        'role': role
    }
    
    return True, "Login successful!", user_data

def close_auth_connection():
    """Close authentication database connection."""
    global _auth_conn, _auth_cursor
    if _auth_conn:
        _auth_conn.close()
        _auth_conn = None
        _auth_cursor = None