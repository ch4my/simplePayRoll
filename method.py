from typing import Dict
import database
from currency import get_rate  # add this import

BASIC = 25000
HRA = 5000
CONVEYANCE = 2500
TAX = 500
HEALTH_INSURANCE = 1500

def compute_pay() -> int:
    # Monthly gross (pay breakdown total)
    return BASIC + HRA + CONVEYANCE

def compute_deduction(loan: int) -> int:
    # Monthly deductions total (EXCLUDES loan; loan is one-time)
    return TAX + HEALTH_INSURANCE

def compute_net_salary(months: int, loan: int) -> int:
    # Overall net for given months
    payB = compute_pay()
    payD = compute_deduction(loan)
    return (payB - payD) * int(months)

def validate_inputs(data: Dict) -> tuple[bool, str]:
    required = ['name','company_id','age','role','department','months','loan']
    # allow optional currency/fx_date
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

def save_record(data: Dict):
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
    database.insert_salary(record)
    return record

def delete_record(record_id: int):
    database.delete_data(record_id)