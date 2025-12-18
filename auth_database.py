import sqlite3
import hashlib
import secrets
from datetime import datetime

AUTH_DB_PATH = "auth.db"

_auth_conn = None
_auth_cursor = None

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
