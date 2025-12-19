from typing import Dict
from currency import get_rate

BASIC = 25000
HRA = 5000
CONVEYANCE = 2500
TAX = 500
HEALTH_INSURANCE = 1500

def compute_pay() -> int:
    #********************************
    #Compute gross pay
    #********************************
    return BASIC + HRA + CONVEYANCE

def compute_deduction(loan: int) -> int:
    #********************************
    #Compute deductions
    #********************************
    return TAX + HEALTH_INSURANCE

def compute_net_salary(months: int, loan: int) -> int:
    #********************************
    #Compute net salary
    #********************************
    payB = compute_pay()
    payD = compute_deduction(loan)
    return (payB - payD) * int(months)

def validate_inputs(data: Dict) -> tuple[bool, str]:
    required = ['name','company_id','age','role','department','months','loan']
    #********************************
    #Validate required fields
    #********************************
    for k in required:
        if not str(data.get(k,'')).strip():
            return False, f"Field '{k}' is required."
    try:
        int(data['age'])
        int(data['months'])
        int(data['loan'])
    except ValueError:
        return False, "Age, months and loan must be integers."
    return True, ""

def validate_and_parse_dates(start_date_str: str, end_date_str: str) -> tuple[int, str, str]:
    #********************************
    #Parse validate dates
    #********************************
    if not start_date_str or not end_date_str:
        raise ValueError("Start Date and End Date are required.")
    
    try:
        start_parts = start_date_str.split('/')
        end_parts = end_date_str.split('/')
        start_year, start_month_num = int(start_parts[0]), int(start_parts[1])
        end_year, end_month_num = int(end_parts[0]), int(end_parts[1])
    except (ValueError, IndexError):
        raise ValueError("Invalid date format. Please use YYYY/MM format.")
    
    months = (end_year - start_year) * 12 + (end_month_num - start_month_num) + 1
    
    if months < 1:
        raise ValueError("End Date must be equal to or after Start Date.")
    if months > 12:
        raise ValueError("Period cannot exceed 12 months.")
    
    return months, start_date_str, end_date_str

def compute_selected_totals(db_row: tuple, months: int = None) -> dict:
    #********************************
    #Compute salary totals
    #********************************
    loan = int(db_row[7]) if db_row[7] is not None else 0
    months = months or (int(db_row[6]) if db_row[6] is not None else 1)
    payD = int(db_row[8]) if db_row[8] is not None else 0
    monthly_net = int(db_row[9]) if db_row[9] is not None else 0
    payB = monthly_net + payD
    totalS = payB * months
    totalD = payD * months
    total = int(db_row[10]) if db_row[10] is not None else (monthly_net * months - loan)
    
    return {
        'loan': loan,
        'months': months,
        'payD': payD,
        'payB': payB,
        'totalS': totalS,
        'totalD': totalD,
        'total': total
    }

def compute_record(data: Dict):
    ok, msg = validate_inputs(data)
    if not ok:
        raise ValueError(msg)

    months = int(data['months'])
    loan = int(data['loan'])

    # Monthly figures
    payB = compute_pay()                 # monthly gross
    payD = compute_deduction(loan)       # monthly deductions (no loan)
    net_monthly = payB - payD            # monthly net (no loan)

    # Totals for the selected number of months
    totalS = payB * months               # total salary (gross) for n months
    totalD = payD * months               # total deduction for n months (no loan)
    # Overall total net = totalS - totalD - loan(one-time)
    total = totalS - totalD - loan

    currency = str(data.get('currency', 'php')).lower()
    fx_date = str(data.get('fx_date', 'latest')).strip() or 'latest'

    fx_rate = 1.0
    net_monthly_php = net_monthly
    total_php = total
    if currency != 'php':
        try:
            fx_rate = get_rate(currency, 'php', fx_date)
            net_monthly_php = int(round(net_monthly * fx_rate))
            total_php = int(round(total * fx_rate))
        except Exception:
            # If FX fails, keep PHP as-is and rate=1
            fx_rate = 1.0

    # Compose record with new naming plus backward-compatible keys used by UI/DB
    record = {
        'name': data['name'].strip(),
        'company_id': data['company_id'].strip(),
        'age': int(data['age']),
        'role': data['role'].strip(),
        'department': data['department'].strip(),
        'start_month': str(data.get('start_month', '')).strip(),
        'end_month': str(data.get('end_month', '')).strip(),
        'months': months,
        'loan': loan,

        # New names requested
        'payB': payB,
        'payD': payD,
        'totalS': totalS,
        'totalD': totalD,
        'total': total,

        # Back-compat names currently used by app/database
        'deduction': payD,                # monthly deduction (no loan)
        'overall_salary': net_monthly,    # monthly net (no loan)
        'total_salary': total,            # overall net for n months minus one-time loan

        # Currency metadata and PHP conversions (for net values)
        'currency': currency,
        'fx_date': fx_date,
        'fx_rate': fx_rate,
        'overall_salary_php': net_monthly_php,
        'total_salary_php': total_php
    }
    return record

# Database operations are handled in database.py and the UI layer.
# This module focuses on business logic computations only.