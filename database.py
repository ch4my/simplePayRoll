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

_BASIC = 25000
_HRA = 5000
_CONVEYANCE = 2500
_TAX = 500
_HEALTH_INSURANCE = 1500

def _compute_deduction(loan: int) -> int:
    return _TAX + _HEALTH_INSURANCE + max(0, int(loan))

def _compute_overall() -> int:
    #********************************
    #Compute overall salary
    #********************************
    return _BASIC + _HRA + _CONVEYANCE - (_TAX + _HEALTH_INSURANCE)

def connect():
    #********************************
    #Initialize database
    #********************************
    global _conn, _cursor
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH)
        _cursor = _conn.cursor()
        #********************************
        #Create table
        #********************************
        _cursor.execute('''
        CREATE TABLE IF NOT EXISTS salaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
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

        #********************************
        #Inspect columns
        #********************************
        _cursor.execute("PRAGMA table_info('salaries')")
        cols = [_r[1] for _r in _cursor.fetchall()]

        #********************************
        #Add missing columns
        #********************************
        added = False
        # ensure user_id exists to scope data per authenticated user
        if 'user_id' not in cols:
            _cursor.execute("ALTER TABLE salaries ADD COLUMN user_id INTEGER")
            added = True
        if 'deduction' not in cols:
            _cursor.execute("ALTER TABLE salaries ADD COLUMN deduction INTEGER DEFAULT 0")
            added = True
        if 'overall_salary' not in cols:
            _cursor.execute("ALTER TABLE salaries ADD COLUMN overall_salary INTEGER DEFAULT 0")
            added = True

        #********************************
        #Add optional columns
        #********************************
        if 'start_month' not in cols:
            _cursor.execute("ALTER TABLE salaries ADD COLUMN start_month TEXT")
        if 'end_month' not in cols:
            _cursor.execute("ALTER TABLE salaries ADD COLUMN end_month TEXT")
        if 'currency' not in cols:
            _cursor.execute("ALTER TABLE salaries ADD COLUMN currency TEXT DEFAULT 'PHP'")

        if added:
            _cursor.execute("SELECT id, loan FROM salaries")
            rows = _cursor.fetchall()
            for rid, loan in rows:
                loan_val = int(loan) if loan is not None else 0
                ded = _compute_deduction(loan_val)
                overall = (_BASIC + _HRA + _CONVEYANCE) - ded
                _cursor.execute("UPDATE salaries SET deduction = ?, overall_salary = ? WHERE id = ?", (ded, overall, rid))
            _conn.commit()

    return _conn, _cursor

def insert_salary(record, user_id: int):
    conn, cursor = connect()
    deduction = record.get('deduction', _compute_deduction(record.get('loan', 0)))
    overall = record.get('overall_salary', (_BASIC + _HRA + _CONVEYANCE) - deduction)
    cursor.execute('''
        INSERT INTO salaries
        (user_id, name, company_id, age, role, department, months, loan, total_salary, deduction, overall_salary, created_at, start_month, end_month, currency)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (
        int(user_id),
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
    return cursor.lastrowid

def fetch_all(user_id: int):
    conn, cursor = connect()
    cursor.execute('''
        SELECT id, name, company_id, age, role, department, months, loan, deduction, overall_salary, total_salary, created_at, start_month, end_month, currency
        FROM salaries WHERE user_id = ? ORDER BY id
    ''', (int(user_id),))
    return cursor.fetchall()

def fetch_one(record_id, user_id: int | None = None):
    conn, cursor = connect()
    if user_id is None:
        cursor.execute('''
            SELECT id, name, company_id, age, role, department, months, loan, deduction, overall_salary, total_salary, created_at, start_month, end_month, currency
            FROM salaries WHERE id = ?
        ''', (record_id,))
    else:
        cursor.execute('''
            SELECT id, name, company_id, age, role, department, months, loan, deduction, overall_salary, total_salary, created_at, start_month, end_month, currency
            FROM salaries WHERE id = ? AND user_id = ?
        ''', (record_id, int(user_id)))
    return cursor.fetchone()

def load_and_format_records(currency_code: str = 'PHP', user_id: int | None = None) -> list:
    """
    Fetch all records from DB and format for table display.
    Returns list of tuples for Treeview: (name, id, age, role, dept, months_display, payB, payD, loan, total, converted).
    """
    from currency import get_rate
    
    if user_id is None:
        rows = []
    else:
        rows = fetch_all(int(user_id))
    try:
        rate = get_rate('php', currency_code.lower()) if currency_code != 'PHP' else 1.0
    except Exception:
        rate = 1.0
    
    formatted = []
    for r in rows:
        payD = int(r[8]) if r[8] is not None else 0
        monthly_net = int(r[9]) if r[9] is not None else 0
        payB = monthly_net + payD
        total = int(r[10]) if r[10] is not None else monthly_net
        
        start_month = str(r[12] or '').strip()
        end_month = str(r[13] or '').strip()
        months_display = f"{start_month} - {end_month} ({r[6]})" if start_month and end_month else f"{start_month or end_month} ({r[6]})"
        
        conv_val = int(round(total * rate))
        
        formatted.append((
            r[0],  # id (for iid)
            r[1],  # name
            r[2],  # company_id
            r[3],  # age
            r[4],  # role
            r[5],  # department
            months_display,
            f"PHP {payB:,}",
            f"PHP {payD:,}",
            f"PHP {int(r[7] or 0):,}",
            f"PHP {total:,}",
            f"{currency_code} {conv_val:,}"
        ))
    
    return formatted

def delete_data(record_id, user_id: int | None = None):
    conn, cursor = connect()
    if user_id is None:
        cursor.execute('DELETE FROM salaries WHERE id = ?', (record_id,))
    else:
        cursor.execute('DELETE FROM salaries WHERE id = ? AND user_id = ?', (record_id, int(user_id)))
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