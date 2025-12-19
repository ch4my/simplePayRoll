import requests
from functools import lru_cache

BASE_URL = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date}/v1/currencies/{base}.json"
FALLBACK_URL = "https://{date}.currency-api.pages.dev/v1/currencies/{base}.json"
LIST_URL = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{date}/v1/currencies.json"
LIST_FALLBACK_URL = "https://{date}.currency-api.pages.dev/v1/currencies.json"

@lru_cache(maxsize=256)
def get_rate(base: str, target: str, date: str = "latest") -> float:
    base = base.lower().strip()
    target = target.lower().strip()
    if base == target:
        return 1.0
    urls = [
        BASE_URL.format(date=date, base=base),
        FALLBACK_URL.format(date=date, base=base),
    ]
    last_err = None
    for url in urls:
        try:
            r = requests.get(url, timeout=6)
            r.raise_for_status()
            data = r.json()
            #********************************
            #Parse JSON rates
            #********************************
            rates = data.get(base, {})
            rate = rates.get(target)
            if rate is not None:
                return float(rate)
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"Failed to fetch FX rate {base}->{target} ({date}): {last_err}")


@lru_cache(maxsize=2)
def list_currency_names(date: str = "latest") -> dict:
    #********************************
    #Fetch currency names
    #********************************
    urls = [
        LIST_URL.format(date=date),
        LIST_FALLBACK_URL.format(date=date),
    ]
    last_err = None
    for url in urls:
        try:
            r = requests.get(url, timeout=8)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, dict) and data:
                return data
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"Failed to fetch currency list ({date}): {last_err}")


@lru_cache(maxsize=2)
def list_currency_codes(date: str = "latest") -> list:
    #********************************
    #Get currency codes
    #********************************
    names = list_currency_names(date)
    return sorted(names.keys())