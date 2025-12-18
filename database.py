import sqlite3
from datetime import datetime

DB_PATH = "payroll.db"

_conn = None
_cursor = None

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
        (name, company_id, age, role, department, months, loan, total_salary, deduction, overall_salary, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)
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
        datetime.utcnow().isoformat()
    ))
    conn.commit()

def fetch_all():
    conn, cursor = connect()
    # select in consistent order; if columns missing for some reason, PRAGMA ensures they exist
    cursor.execute('''
        SELECT id, name, company_id, age, role, department, months, loan, deduction, overall_salary, total_salary, created_at
        FROM salaries ORDER BY id
    ''')
    return cursor.fetchall()

def fetch_one(record_id):
    conn, cursor = connect()
    cursor.execute('''
        SELECT id, name, company_id, age, role, department, months, loan, deduction, overall_salary, total_salary, created_at
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