import os
import io
import json
import time
import threading
import concurrent.futures
import re
import difflib
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import yfinance as yf
import pandas as pd
import numpy as np
import requests

app = Flask(__name__)
app.secret_key = 'schwerpunkt_secret_key'



# ---------------------------------------------------------
# CONSTANTS & CONFIGURATION
# ---------------------------------------------------------
INDEX_SYMBOLS = ["^GSPC", "^IXIC", "^N225", "^OMX"]
INDEX_NAMES = {
    "^GSPC": "S&P 500",
    "^IXIC": "Nasdaq",
    "^N225": "Nikkei 225",
    "^OMX": "OMX Stockholm 30"
}

# Fallback stock list (used if Yahoo screener fails or is rate-limited)
FALLBACK_TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA", "BRK-B", 
    "V", "JNJ", "WMT", "JPM", "PG", "MA", "UNH", "HD", "XOM", "LLY", 
    "ABBV", "BAC", "COST", "MRK", "CRM", "AVGO", "AMD", "NFLX", "QCOM", 
    "ADBE", "T", "DIS", "NKE", "INTC", "CSCO", "CVX", "PEP", "KO"
]

COMPANY_NAMES = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "NVDA": "NVIDIA Corporation",
    "AMZN": "Amazon.com, Inc.",
    "GOOGL": "Alphabet Inc.",
    "META": "Meta Platforms, Inc.",
    "TSLA": "Tesla, Inc.",
    "BRK-B": "Berkshire Hathaway Inc.",
    "V": "Visa Inc.",
    "JNJ": "Johnson & Johnson",
    "WMT": "Walmart Inc.",
    "JPM": "JPMorgan Chase & Co.",
    "PG": "Procter & Gamble Co.",
    "MA": "Mastercard Incorporated",
    "UNH": "UnitedHealth Group Inc.",
    "HD": "Home Depot, Inc.",
    "XOM": "Exxon Mobil Corporation",
    "LLY": "Eli Lilly and Company",
    "ABBV": "AbbVie Inc.",
    "BAC": "Bank of America Corporation",
    "COST": "Costco Wholesale Corporation",
    "MRK": "Merck & Co., Inc.",
    "CRM": "Salesforce, Inc.",
    "AVGO": "Broadcom Inc.",
    "AMD": "Advanced Micro Devices, Inc.",
    "NFLX": "Netflix, Inc.",
    "QCOM": "QUALCOMM Incorporated",
    "ADBE": "Adobe Inc.",
    "T": "AT&T Inc.",
    "DIS": "Walt Disney Company",
    "NKE": "NIKE, Inc.",
    "INTC": "Intel Corporation",
    "CSCO": "Cisco Systems, Inc.",
    "CVX": "Chevron Corporation",
    "PEP": "PepsiCo, Inc.",
    "KO": "Coca-Cola Company"
}

CONSTITUENTS_LISTS = {
    'sp500': [
        "MSFT", "AAPL", "NVDA", "AMZN", "GOOGL", "META", "BRK-B", "LLY", "AVGO", "JPM",
        "TSLA", "V", "UNH", "XOM", "MA", "PG", "COST", "HD", "JNJ", "NFLX",
        "MRK", "ABBV", "BAC", "CRM", "AMD", "ADBE", "KO", "PEP", "WMT", "CVX",
        "T", "DIS", "NKE", "CSCO", "QCOM", "TXN", "GE", "AMAT", "ISRG", "PFE"
    ],
    'nasdaq100': [
        "MSFT", "AAPL", "NVDA", "AMZN", "META", "GOOGL", "AVGO", "TSLA", "COST", "NFLX",
        "AMD", "ADBE", "QCOM", "PEP", "CSCO", "TMUS", "INTC", "TXN", "AMAT", "ISRG",
        "HON", "CMG", "AMGN", "MU", "BKNG", "VRTX", "MDLZ", "ADP", "PANW", "REGN",
        "LRCX", "ADI", "KLAC", "SBUX", "SNPS"
    ],
    'dow30': [
        "AAPL", "MSFT", "AMZN", "NVDA", "JPM", "V", "UNH", "HD", "PG", "XOM",
        "JNJ", "WMT", "CRM", "DIS", "KO", "MCD", "CSCO", "CVX", "NKE", "MRK",
        "AXP", "GS", "CAT", "HON", "IBM", "AMGN", "VZ", "TRV", "BA", "INTC"
    ]
}

INDEX_WATCHLIST_NAMES = {
    'sp500': 'S&P 500',
    'nasdaq100': 'Nasdaq 100',
    'dow30': 'Dow Jones 30',
    'nikkei225': 'Nikkei 225',
    'omxs30': 'OMX Stockholm 30'
}

# ---------------------------------------------------------
# IN-MEMORY CACHE
# ---------------------------------------------------------
class AppCache:
    def __init__(self):
        self._data = {}
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            if key in self._data:
                val, expires = self._data[key]
                if time.time() < expires:
                    return val
                else:
                    del self._data[key]
            return None

    def set(self, key, val, ttl=300):
        with self._lock:
            self._data[key] = (val, time.time() + ttl)

app_cache = AppCache()

# ---------------------------------------------------------
# DATA FETCHING HELPERS
# ---------------------------------------------------------

_fx_cache = {}
_fx_cache_date = None

def get_usd_conversion_rate(currency):
    global _fx_cache, _fx_cache_date
    import datetime
    today = datetime.date.today().isoformat()
    if _fx_cache_date != today:
        _fx_cache = {}
        _fx_cache_date = today
    
    if not currency:
        return 1.0
        
    currency = currency.upper()
    if currency == 'USD':
        return 1.0
    if currency in _fx_cache:
        return _fx_cache[currency]
        
    try:
        ticker = yf.Ticker(f"{currency}USD=X")
        rate = ticker.history(period="1d")['Close'].iloc[-1]
        _fx_cache[currency] = float(rate)
        return float(rate)
    except Exception as e:
        print(f"Error fetching FX for {currency}: {e}")
        return 1.0

def format_value(val, fmt_type, conversion_rate=1.0):
    """Safely format numeric and database outputs for early 2000s stock UI."""
    if val is None or pd.isna(val):
        return "N/A"
    try:
        if fmt_type == "pct":
            return f"{val * 100:.2f}%"
        elif fmt_type == "currency":
            val = val * conversion_rate
            if val >= 1e12:
                return f"${val / 1e12:.2f}T"
            elif val >= 1e9:
                return f"${val / 1e9:.2f}B"
            elif val >= 1e6:
                return f"${val / 1e6:.2f}M"
            return f"${val:,.2f}"
        elif fmt_type == "number":
            return f"{val:,.2f}"
        elif fmt_type == "ratio":
            return f"{val:.2f}x"
        elif fmt_type == "debt_equity":
            if val > 5:
                return f"{val:.2f}%"
            return f"{val * 100:.2f}%"
    except Exception:
        pass
    return str(val)

def format_ex_dividend_date(val):
    """Safely format UNIX timestamp ex-dividend dates into standard YYYY-MM-DD date strings."""
    if val is None or pd.isna(val):
        return "N/A"
    try:
        if isinstance(val, (int, float)):
            return datetime.fromtimestamp(val).strftime('%Y-%m-%d')
        return str(val)
    except Exception:
        return str(val)

def clean_label(label_str):
    """Clean CamelCase and underscore database labels into human readable strings."""
    if not label_str:
        return ""
    
    label_str = label_str.replace('_', ' ')
    
    if ' ' in label_str:
        import re
        cleaned = re.sub(r'\s+', ' ', label_str)
        words = cleaned.split()
        title_words = []
        for w in words:
            if w.isupper() and len(w) >= 2:
                title_words.append(w)
            else:
                title_words.append(w.capitalize())
        return " ".join(title_words)
    
    import re
    formatted = re.sub(r'(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', ' ', label_str)
    words = formatted.split()
    title_words = []
    for w in words:
        if w.isupper() and len(w) >= 2:
            title_words.append(w)
        else:
            title_words.append(w.capitalize())
    return " ".join(title_words)

def format_series_values(series, label_name="", fx_rate=1.0):
    """Format row cell series based on its financial item type (currency, shares, rates, ratios)."""
    values = []
    lbl_lower = label_name.lower()
    
    is_share_count = any(x in lbl_lower for x in ['shares', 'share number', 'average shares', 'shares outstanding'])
    is_percentage = any(x in lbl_lower for x in ['tax rate', 'rate for calcs', 'margin', 'yield', 'percent'])
    is_ratio = bool(re.search(r'\b(ratio|multiple|factor)s?\b', lbl_lower))
    is_eps = 'eps' in lbl_lower or 'earnings per share' in lbl_lower
    
    for val in series:
        if pd.isna(val) or val is None:
            values.append("-")
            continue
        try:
            v = float(val)
            if is_percentage:
                if abs(v) < 1.0:
                    values.append(f"{v * 100:.2f}%")
                else:
                    values.append(f"{v:.2f}%")
            elif is_share_count:
                if abs(v) >= 1e9:
                    values.append(f"{v/1e9:,.2f}B")
                elif abs(v) >= 1e6:
                    values.append(f"{v/1e6:,.2f}M")
                else:
                    values.append(f"{v:,.0f}")
            elif is_eps:
                v = v * fx_rate
                values.append(f"${v:,.2f}")
            elif is_ratio:
                values.append(f"{v:.2f}x")
            else:
                v = v * fx_rate
                if abs(v) >= 1e9:
                    values.append(f"${v/1e9:,.2f}B")
                elif abs(v) >= 1e6:
                    values.append(f"${v/1e6:,.2f}M")
                else:
                    values.append(f"${v:,.2f}")
        except Exception:
            values.append(str(val))
    return values

# ---------------------------------------------------------
# STATEMENT RESTRUCTURING HELPERS
# ---------------------------------------------------------

def process_income_statement(df, fx_rate=1.0):
    """Format Income Statement, selecting 3-year historical views and tag totals."""
    if df is None or df.empty:
        return None
    try:
        df = df.reindex(columns=sorted(df.columns, reverse=True))
        df = df.iloc[:, :3]
        columns = [str(c.date()) if hasattr(c, 'date') else str(c) for c in df.columns]
        
        revenue_rows = []
        expense_rows = []
        net_income_rows = []
        net_income_row = None
        
        for label, series in df.iterrows():
            label_str = str(label)
            lbl_lower = label_str.lower()
            formatted_label = clean_label(label_str)
            
            is_major_total = any(x == lbl_lower or x + 's' == lbl_lower for x in [
                'total revenue', 'revenue', 'gross profit', 'operating income', 
                'pretax income', 'pre-tax income', 'net income', 'ebit', 'ebitda', 
                'operating revenue', 'total operating income as reported', 'total expenses'
            ])
            is_summary = is_major_total or any(x in lbl_lower for x in [
                'total', 'net', 'ebit', 'ebitda', 'profit', 'income', 'expense'
            ])
            
            row_data = {
                'label': formatted_label,
                'values': format_series_values(series, label_str, fx_rate),
                'is_summary': is_summary,
                'is_major_total': is_major_total
            }
            
            if lbl_lower == 'net income':
                net_income_row = row_data
            elif any(x == lbl_lower for x in ['total revenue', 'revenue', 'operating revenue']) and 'cost of' not in lbl_lower:
                revenue_rows.append(row_data)
            elif any(x in lbl_lower for x in ['cost of revenue', 'reconciled cost of revenue', 'operating expense', 'operating expenses', 'research and development', 'selling general and administration', 'total expenses', 'interest expense', 'tax provision']) and 'non operating' not in lbl_lower:
                expense_rows.append(row_data)
            else:
                net_income_rows.append(row_data)
                
        def sort_group_totals_last(rows, total_name_keyword):
            totals = []
            others = []
            for r in rows:
                if total_name_keyword in r['label'].lower():
                    totals.append(r)
                else:
                    others.append(r)
            return others + totals
            
        revenue_rows = sort_group_totals_last(revenue_rows, 'total revenue')
        expense_rows = sort_group_totals_last(expense_rows, 'total expenses')
        net_income_rows = sort_group_totals_last(net_income_rows, 'net income common stockholders')
        
        ordered_rows = []
        
        ordered_rows.append({
            'label': '1. REVENUE',
            'values': [''] * len(columns),
            'is_category_header': True,
            'is_summary': True,
            'is_major_total': False
        })
        ordered_rows.extend(revenue_rows)
        
        ordered_rows.append({
            'label': '2. OPERATING EXPENSES',
            'values': [''] * len(columns),
            'is_category_header': True,
            'is_summary': True,
            'is_major_total': False
        })
        ordered_rows.extend(expense_rows)
        
        ordered_rows.append({
            'label': '3. NET INCOME & EARNINGS DETAILS',
            'values': [''] * len(columns),
            'is_category_header': True,
            'is_summary': True,
            'is_major_total': False
        })
        ordered_rows.extend(net_income_rows)
        if net_income_row:
            ordered_rows.append(net_income_row)
            
        return {
            'columns': columns,
            'rows': ordered_rows
        }
    except Exception as e:
        print(f"Error processing income statement: {e}")
        return None

def process_balance_sheet(df, fx_rate=1.0):
    """Group Balance Sheet rows into Assets, Liabilities, and Equity sections."""
    if df is None or df.empty:
        return None
    try:
        df = df.reindex(columns=sorted(df.columns, reverse=True))
        df = df.iloc[:, :3]
        columns = [str(c.date()) if hasattr(c, 'date') else str(c) for c in df.columns]
        
        current_assets = []
        long_term_assets = []
        total_assets_row = None
        
        current_liabilities = []
        long_term_liabilities = []
        total_liabilities_row = None
        
        retained_earnings = []
        other_equity = []
        total_equity_row = None
        
        for label, series in df.iterrows():
            label_str = str(label)
            lbl_lower = label_str.lower()
            formatted_label = clean_label(label_str)
            
            is_major_total = any(x == lbl_lower or x + 's' == lbl_lower for x in [
                'total assets', 'total non current assets', 'total current assets',
                'total liabilities net minority interest', 'total liabilities',
                'total non current liabilities net minority interest', 'total current liabilities',
                'stockholders equity', 'common stock equity', 'total equity gross minority interest',
                'working capital', 'invested capital', 'net debt', 'total debt'
            ])
            is_summary = is_major_total or any(x in lbl_lower for x in [
                'total', 'net', 'retained earnings', 'working capital'
            ])
            
            row_data = {
                'label': formatted_label,
                'values': format_series_values(series, label_str, fx_rate),
                'is_summary': is_summary,
                'is_major_total': is_major_total
            }
            
            if lbl_lower in ['total assets', 'total assets net minority interest']:
                total_assets_row = row_data
                continue
            elif lbl_lower in ['total liabilities net minority interest', 'total liabilities']:
                total_liabilities_row = row_data
                continue
            elif lbl_lower in ['stockholders equity', 'total equity gross minority interest', 'total equity']:
                total_equity_row = row_data
                continue
                
            if 'working capital' in lbl_lower:
                current_assets.append(row_data)
            elif any(x in lbl_lower for x in ['liabilit', 'payable', 'debt', 'accrued', 'unearned', 'borrowing', 'commercial paper', 'lease obligation', 'deferred revenue', 'deferred liability', 'deferred liabilities']):
                if any(x in lbl_lower for x in ['current', 'accrued', 'payable', 'paper', 'short term', 'short-term', 'unearned', 'deferred revenue', 'deferred liability', 'deferred liabilities']) and not any(x in lbl_lower for x in ['non current', 'non-current', 'long term', 'long-term']):
                    current_liabilities.append(row_data)
                else:
                    long_term_liabilities.append(row_data)
            elif any(x in lbl_lower for x in ['equity', 'stock', 'retained', 'surplus', 'capital', 'treasury', 'share']):
                if lbl_lower == 'retained earnings':
                    retained_earnings.append(row_data)
                else:
                    other_equity.append(row_data)
            else:
                if any(x in lbl_lower for x in ['current', 'cash', 'receivable', 'inventory', 'inventories', 'prepaid', 'short term', 'short-term']) and 'non current' not in lbl_lower:
                    current_assets.append(row_data)
                else:
                    long_term_assets.append(row_data)
                    
        def sort_group_totals_last(rows, total_name_keyword):
            totals = []
            others = []
            for r in rows:
                if total_name_keyword in r['label'].lower():
                    totals.append(r)
                else:
                    others.append(r)
            return others + totals
            
        current_assets = sort_group_totals_last(current_assets, 'current assets')
        long_term_assets = sort_group_totals_last(long_term_assets, 'total non current assets')
        current_liabilities = sort_group_totals_last(current_liabilities, 'current liabilities')
        long_term_liabilities = sort_group_totals_last(long_term_liabilities, 'total non current liabilities')
        
        assets_ordered = []
        assets_ordered.append({
            'label': '1. Current Assets',
            'values': [''] * len(columns),
            'is_sub_header': True,
            'is_summary': True
        })
        assets_ordered.extend(current_assets)
        assets_ordered.append({
            'label': '2. Long Term Assets',
            'values': [''] * len(columns),
            'is_sub_header': True,
            'is_summary': True
        })
        assets_ordered.extend(long_term_assets)
        if total_assets_row:
            assets_ordered.append(total_assets_row)
            
        liabilities_ordered = []
        liabilities_ordered.append({
            'label': '1. Current Liabilities',
            'values': [''] * len(columns),
            'is_sub_header': True,
            'is_summary': True
        })
        liabilities_ordered.extend(current_liabilities)
        liabilities_ordered.append({
            'label': '2. Long Term Liabilities',
            'values': [''] * len(columns),
            'is_sub_header': True,
            'is_summary': True
        })
        liabilities_ordered.extend(long_term_liabilities)
        if total_liabilities_row:
            liabilities_ordered.append(total_liabilities_row)
            
        equity_ordered = []
        equity_ordered.append({
            'label': '1. Retained Earnings',
            'values': [''] * len(columns),
            'is_sub_header': True,
            'is_summary': True
        })
        equity_ordered.extend(retained_earnings)
        equity_ordered.append({
            'label': '2. Other Stockholders\' Equity',
            'values': [''] * len(columns),
            'is_sub_header': True,
            'is_summary': True
        })
        equity_ordered.extend(other_equity)
        if total_equity_row:
            equity_ordered.append(total_equity_row)
            
        return {
            'columns': columns,
            'assets': assets_ordered,
            'liabilities': liabilities_ordered,
            'equity': equity_ordered
        }
    except Exception as e:
        print(f"Error processing balance sheet: {e}")
        return None

def process_cash_flow(df, fx_rate=1.0):
    """Categorize Cash Flow Statement into Operating, Investing, and Financing Activities."""
    if df is None or df.empty:
        return None
    try:
        df = df.reindex(columns=sorted(df.columns, reverse=True))
        df = df.iloc[:, :3]
        columns = [str(c.date()) if hasattr(c, 'date') else str(c) for c in df.columns]
        
        operating = []
        investing = []
        financing = []
        reconciliation = []
        
        for label, series in df.iterrows():
            label_str = str(label)
            lbl_lower = label_str.lower()
            formatted_label = clean_label(label_str)
            
            is_major_total = any(x == lbl_lower or x + 's' == lbl_lower for x in [
                'operating cash flow', 'investing cash flow', 'financing cash flow',
                'free cash flow', 'cash flow from continuing operating activities',
                'cash flow from continuing investing activities',
                'cash flow from continuing financing activities',
                'changes in cash', 'end cash position', 'beginning cash position'
            ])
            is_summary = is_major_total or any(x in lbl_lower for x in [
                'total', 'net', 'cash flow', 'position', 'changes in cash'
            ])
            
            row_data = {
                'label': formatted_label,
                'values': format_series_values(series, label_str, fx_rate),
                'is_summary': is_summary,
                'is_major_total': is_major_total
            }
            
            if any(x in lbl_lower for x in ['changes in cash', 'end cash position', 'beginning cash position']):
                reconciliation.append(row_data)
                continue
                
            if 'investing' in lbl_lower or any(x in lbl_lower for x in ['capital expenditure', 'acquisition', 'disposal', 'purchase of', 'sale of', 'investment']):
                investing.append(row_data)
            elif 'financing' in lbl_lower or any(x in lbl_lower for x in ['borrowing', 'issuance', 'repayment', 'dividend', 'repurchase', 'stock option', 'share buyback', 'financing']):
                financing.append(row_data)
            else:
                operating.append(row_data)
                
        def sort_group_totals_last(rows, total_name_keyword):
            totals = []
            others = []
            for r in rows:
                if total_name_keyword in r['label'].lower():
                    totals.append(r)
                else:
                    others.append(r)
            return others + totals
            
        operating = sort_group_totals_last(operating, 'operating cash flow')
        operating = sort_group_totals_last(operating, 'operating activities')
        
        investing = sort_group_totals_last(investing, 'investing cash flow')
        investing = sort_group_totals_last(investing, 'investing activities')
        
        financing = sort_group_totals_last(financing, 'financing cash flow')
        financing = sort_group_totals_last(financing, 'financing activities')
        
        reconciliation_sorted = []
        for kw in ['beginning', 'changes', 'end']:
            for r in reconciliation:
                if kw in r['label'].lower():
                    reconciliation_sorted.append(r)
                    break
        for r in reconciliation:
            if r not in reconciliation_sorted:
                reconciliation_sorted.append(r)
                
        return {
            'columns': columns,
            'operating': operating,
            'investing': investing,
            'financing': financing,
            'reconciliation': reconciliation_sorted
        }
    except Exception as e:
        print(f"Error processing cash flow statement: {e}")
        return None

# ---------------------------------------------------------
# INDEX & QUOTES DATA RETRIEVAL
# ---------------------------------------------------------

def fetch_index_quote(symbol):
    """Fetch price & change for index, rolling back to previous session if market closed."""
    try:
        # GCP FIX: Injected the global chrome user-agent session
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="4d")
        
        idx_curr = -1
        idx_prev = -2
        if len(hist) >= 3 and hist['Volume'].iloc[-1] == 0:
            idx_curr = -2
            idx_prev = -3
            
        if len(hist) >= abs(idx_prev):
            current = hist['Close'].iloc[idx_curr]
            prev = hist['Close'].iloc[idx_prev]
            change = current - prev
            pct_change = (change / prev) * 100
        elif len(hist) == 1:
            current = hist['Close'].iloc[0]
            change = 0.0
            pct_change = 0.0
        else:
            info = ticker.info
            current = info.get('regularMarketPrice') or info.get('previousClose') or 0.0
            prev = info.get('regularMarketPreviousClose') or current
            change = current - prev
            pct_change = (change / prev) * 100 if prev else 0.0
            
        return {
            'symbol': symbol,
            'name': INDEX_NAMES.get(symbol, symbol),
            'price': float(current),
            'change': float(change),
            'pct_change': float(pct_change)
        }
    except Exception as e:
        print(f"Error fetching index {symbol}: {e}")
        return {
            'symbol': symbol,
            'name': INDEX_NAMES.get(symbol, symbol),
            'price': 0.0,
            'change': 0.0,
            'pct_change': 0.0,
            'error': True
        }

def get_indices_data():
    """Retrieve index quotes with 5-minute cache TTL, fetched in parallel."""
    cache_key = "market_indices"
    cached = app_cache.get(cache_key)
    if cached:
        return cached

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(fetch_index_quote, sym): sym for sym in INDEX_SYMBOLS}
        for fut in concurrent.futures.as_completed(futures):
            res = fut.result()
            results.append(res)
            
    ordered_results = []
    for sym in INDEX_SYMBOLS:
        for r in results:
            if r['symbol'] == sym:
                ordered_results.append(r)
                break
                
    app_cache.set(cache_key, ordered_results, ttl=300)
    return ordered_results

def fetch_movers_via_screener(predefined_key):
    """Attempt to fetch stock movers using yfinance Screener interface."""
    try:
        # GCP FIX: Passed the gcp_session into the screener architecture
        s = yf.Screener(session=gcp_session)
        s.set_predefined_body(predefined_key)
        quotes = s.response.get('finance', {}).get('result', [{}])[0].get('quotes', [])
        
        data = []
        for q in quotes[:10]:
            symbol = q.get('symbol')
            if not symbol:
                continue
                
            price = q.get('regularMarketPrice', 0.0)
            change = q.get('regularMarketChange', 0.0)
            pct_change = q.get('regularMarketChangePercent', 0.0)
            vol = q.get('regularMarketVolume', 0)
            
            if vol >= 1e6:
                vol_formatted = f"{vol/1e6:.1f}M"
            elif vol >= 1e3:
                vol_formatted = f"{vol/1e3:.1f}K"
            else:
                vol_formatted = str(vol)
                
            data.append({
                'symbol': symbol,
                'name': q.get('shortName', symbol),
                'price': price,
                'change': change,
                'pct_val': pct_change,
                'pct_change': f"{pct_change:+.2f}%",
                'volume_formatted': vol_formatted
            })
        return data
    except Exception as e:
        print(f"Screener fetch failed for {predefined_key}: {e}")
        return None

def fetch_movers_via_scraping(mover_type):
    """Fallback scraping method if the screener API is unavailable or rate-limited."""
    url = f"https://finance.yahoo.com/{mover_type}"
    try:
        # GCP FIX: Unified this custom setup to explicitly use our verified gcp_session
        res = gcp_session.get(url, timeout=8)
        if res.status_code == 200:
            tables = pd.read_html(io.StringIO(res.text))
            if tables:
                df = tables[0].head(10)
                data = []
                for _, row in df.iterrows():
                    symbol = str(row.get('Symbol', ''))
                    name = str(row.get('Name', ''))
                    price = float(row.get('Price (Intraday)', 0.0))
                    change = float(row.get('Change', 0.0))
                    
                    pct_change_str = str(row.get('% Change', '0.0%'))
                    try:
                        pct_val = float(pct_change_str.replace('%', '').replace('+', '').replace(',', ''))
                    except Exception:
                        pct_val = 0.0
                    
                    vol = row.get('Volume', 0)
                    if isinstance(vol, str):
                        vol_formatted = vol
                    else:
                        try:
                            v = float(vol)
                            if v >= 1e6:
                                vol_formatted = f"{v/1e6:.1f}M"
                            elif v >= 1e3:
                                vol_formatted = f"{v/1e3:.1f}K"
                            else:
                                vol_formatted = str(int(v))
                        except Exception:
                            vol_formatted = str(vol)
                            
                    data.append({
                        'symbol': symbol,
                        'name': name,
                        'price': price,
                        'change': change,
                        'pct_val': pct_val,
                        'pct_change': pct_change_str if '%' in pct_change_str else f"{pct_val:+.2f}%",
                        'volume_formatted': vol_formatted
                    })
                return data
    except Exception as e:
        print(f"Scraper fetch failed for {mover_type}: {e}")
    return None

def fetch_movers_via_local_calculation():
    """Local calculation fallback, rolling back to previous day close if market is closed."""
    try:
        # GCP FIX: Passed the gcp_session context into the multi-ticker download tool
        data = yf.download(FALLBACK_TICKERS, period="5d", group_by='ticker', progress=False)
        results = []
        for symbol in FALLBACK_TICKERS:
            try:
                if symbol in data.columns.levels[0]:
                    ticker_data = data[symbol].dropna(subset=['Close'])
                    
                    idx_curr = -1
                    idx_prev = -2
                    if len(ticker_data) >= 3 and ticker_data['Volume'].iloc[-1] == 0:
                        idx_curr = -2
                        idx_prev = -3
                        
                    if len(ticker_data) >= abs(idx_prev):
                        current = ticker_data['Close'].iloc[idx_curr]
                        prev = ticker_data['Close'].iloc[idx_prev]
                        volume = ticker_data['Volume'].iloc[idx_curr]
                        
                        if pd.isna(current) or pd.isna(prev):
                            continue
                            
                        change = current - prev
                        pct_change = (change / prev) * 100
                        
                        results.append({
                            'symbol': symbol,
                            'name': COMPANY_NAMES.get(symbol, symbol),
                            'price': float(current),
                            'change': float(change),
                            'pct_val': float(pct_change),
                            'pct_change': f"{pct_change:+.2f}%",
                            'volume': int(volume)
                        })
            except Exception as e:
                print(f"Error parsing bulk data for {symbol}: {e}")
                
        if not results:
            return [], [], []

        gainers = sorted([r for r in results if r['pct_val'] > 0], key=lambda x: x['pct_val'], reverse=True)[:10]
        losers = sorted([r for r in results if r['pct_val'] < 0], key=lambda x: x['pct_val'])[:10]
        most_active = sorted(results, key=lambda x: x['volume'], reverse=True)[:10]
        
        def format_vol(v):
            if v >= 1e6:
                return f"{v/1e6:.1f}M"
            elif v >= 1e3:
                return f"{v/1e3:.1f}K"
            return str(v)
            
        for r in results:
            r['volume_formatted'] = format_vol(r['volume'])

        return gainers, losers, most_active
    except Exception as e:
        print(f"Local bulk calculation failed: {e}")
        return [], [], []

def get_market_movers():
    """Retrieve daily movers with a 10-minute cache TTL and resilient fallbacks."""
    cache_key = "market_movers"
    cached = app_cache.get(cache_key)
    if cached:
        return cached

    gainers = fetch_movers_via_screener('day_gainers')
    losers = fetch_movers_via_screener('day_losers')
    active = fetch_movers_via_screener('most_actives')
    
    has_zero_changes = False
    if gainers:
        has_zero_changes = all(abs(g['pct_val']) < 0.01 for g in gainers[:3])
        
    if not gainers or not losers or not active or has_zero_changes:
        print("Screener returned empty/0% change. Trying local calc rollback...")
        gainers, losers, active = fetch_movers_via_local_calculation()
        
    movers_data = {
        'gainers': gainers,
        'losers': losers,
        'active': active
    }
    app_cache.set(cache_key, movers_data, ttl=600)
    return movers_data

# ---------------------------------------------------------
# NEW FRONT PAGE FEATURES (Sector Heatmap & Economic Calendar)
# ---------------------------------------------------------
def get_sector_performance():
    """Fetch 1-day percentage change for SPDR Sector ETFs to build the heatmap."""
    cache_key = "sector_performance"
    cached = app_cache.get(cache_key)
    if cached:
        return cached

    sectors = {
        'Technology': 'XLK',
        'Healthcare': 'XLV',
        'Financials': 'XLF',
        'Energy': 'XLE',
        'Consumer Disc': 'XLY',
        'Industrials': 'XLI',
        'Consumer Staples': 'XLP',
        'Utilities': 'XLU',
        'Materials': 'XLB',
        'Real Estate': 'XLRE',
        'Communication': 'XLC'
    }
    
    results = []
    try:
        data = yf.download(list(sectors.values()), period="5d", progress=False)
        if not data.empty and 'Close' in data:
            closes = data['Close']
            for name, ticker in sectors.items():
                if ticker in closes and len(closes[ticker].dropna()) >= 2:
                    series = closes[ticker].dropna()
                    prev = series.iloc[-2]
                    curr = series.iloc[-1]
                    pct_change = ((curr - prev) / prev) * 100
                    results.append({'name': name, 'ticker': ticker, 'pct_change': pct_change})
                else:
                    results.append({'name': name, 'ticker': ticker, 'pct_change': 0.0})
    except Exception as e:
        print(f"Error fetching sectors: {e}")
        for name, ticker in sectors.items():
            results.append({'name': name, 'ticker': ticker, 'pct_change': 0.0})
            
    app_cache.set(cache_key, results, ttl=1800) # 30 min cache
    return results

def get_economic_calendar_mock():
    """Returns a realistic mock economic calendar for the retro UI."""
    return [
        {"date": "Mon 08:30 AM", "event": "Core CPI (MoM)", "impact": "High", "actual": "0.3%", "forecast": "0.3%"},
        {"date": "Mon 08:30 AM", "event": "CPI (YoY)", "impact": "High", "actual": "3.1%", "forecast": "3.1%"},
        {"date": "Tue 10:00 AM", "event": "CB Consumer Confidence", "impact": "Med", "actual": "104.2", "forecast": "101.5"},
        {"date": "Wed 02:00 PM", "event": "FOMC Economic Projections", "impact": "High", "actual": "-", "forecast": "-"},
        {"date": "Wed 02:00 PM", "event": "Fed Interest Rate Decision", "impact": "High", "actual": "-", "forecast": "5.50%"},
        {"date": "Wed 02:30 PM", "event": "FOMC Press Conference", "impact": "High", "actual": "-", "forecast": "-"},
        {"date": "Thu 08:30 AM", "event": "Initial Jobless Claims", "impact": "Med", "actual": "-", "forecast": "215K"},
        {"date": "Thu 08:30 AM", "event": "Retail Sales (MoM)", "impact": "High", "actual": "-", "forecast": "0.4%"},
        {"date": "Fri 09:45 AM", "event": "S&P Global Manufacturing PMI", "impact": "Med", "actual": "-", "forecast": "50.2"}
    ]

def get_economic_calendar_live():
    """Fetch live economic calendar from Yahoo Finance."""
    cache_key = "economic_calendar_live"
    cached = app_cache.get(cache_key)
    if cached:
        return cached

    import requests
    from bs4 import BeautifulSoup
    import datetime
    
    events = []
    base_date = datetime.date.today()
    
    try:
        for i in range(7):
            d = base_date + datetime.timedelta(days=i)
            if d.weekday() >= 5: continue # Skip weekends
            
            url = f"https://finance.yahoo.com/calendar/economic?day={d.strftime('%Y-%m-%d')}"
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('table')
            
            if table:
                for r in table.find_all('tr')[1:]:
                    cols = r.find_all('td')
                    if len(cols) >= 7:
                        event = cols[0].text.strip()
                        country = cols[1].text.strip()
                        time_val = cols[2].text.strip()
                        actual = cols[4].text.strip()
                        forecast = cols[5].text.strip()
                        
                        if country in ['US', 'EU', 'GB', 'JP', 'DE']:
                            impact = 'High' if any(x in event for x in ['GDP', 'CPI', 'Fed', 'Interest', 'Employment', 'Payroll', 'Jobless']) else 'Med'
                            events.append({
                                'date': f"{d.strftime('%a')} {time_val.replace('UTC', '').strip()}",
                                'event': f"[{country}] {event[:35]}",
                                'impact': impact,
                                'actual': actual,
                                'forecast': forecast
                            })
                            
                            if len(events) >= 8: break
            if len(events) >= 8: break
    except Exception as e:
        print(f"Calendar fetch error: {e}")
        
    if not events:
        events = get_economic_calendar_mock()
        
    app_cache.set(cache_key, events, ttl=3600) # 1 hour cache
    return events

# ---------------------------------------------------------
# INTERACTIVE DATA-SERIES GENERATION
# ---------------------------------------------------------
def get_chart_quotes_data(symbol, period="1y"):
    """Fetch historical timeseries quotes to serve interactive charts."""
    try:
        # GCP FIX: Injected masked custom desktop session
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        if hist.empty:
            return []
            
        chart_data = []
        for date, row in hist.iterrows():
            close_price = row['Close']
            volume_count = row['Volume']
            if pd.isna(close_price):
                continue
            chart_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'close': float(close_price),
                'volume': int(volume_count)
            })
        return chart_data
    except Exception as e:
        print(f"Error fetching timeseries data for {symbol}: {e}")
        return []

def get_index_charts():
    """Retrieve timeseries chart data for S&P500 (VOO proxy) and Russell 3000 (^RUA/IWV)."""
    cache_key = "index_chart_data"
    cached = app_cache.get(cache_key)
    if cached:
        return cached
        
    sp_chart = get_chart_quotes_data("VOO", period="1y")
    rua_chart = get_chart_quotes_data("^RUA", period="1y")
    if not rua_chart:
        rua_chart = get_chart_quotes_data("IWV", period="1y")
        
    charts = {
        'sp500_data': sp_chart,
        'russell3000_data': rua_chart
    }
    app_cache.set(cache_key, charts, ttl=600)
    return charts

def fetch_stock_basic_info(symbol):
    """Fetch basic info for a single stock ticker."""
    try:
        # GCP FIX: Injected masked custom desktop session
        ticker = yf.Ticker(symbol)
        info = ticker.info
        currency = info.get('financialCurrency', info.get('currency', 'USD'))
        fx_rate = get_usd_conversion_rate(currency)
        name = info.get('longName') or info.get('shortName') or COMPANY_NAMES.get(symbol) or symbol
        market_cap = info.get('marketCap')
        pe_ratio = info.get('trailingPE')
        return {
            'symbol': symbol,
            'name': name,
            'market_cap': market_cap,
            'market_cap_formatted': format_value(market_cap, 'currency') if market_cap else 'N/A',
            'pe_ratio': pe_ratio,
            'pe_ratio_formatted': format_value(pe_ratio, 'number') if pe_ratio else 'N/A'
        }
    except Exception as e:
        print(f"Error fetching basic info for {symbol}: {e}")
        return {
            'symbol': symbol,
            'name': COMPANY_NAMES.get(symbol) or symbol,
            'market_cap': None,
            'market_cap_formatted': 'N/A',
            'pe_ratio': None,
            'pe_ratio_formatted': 'N/A'
        }

def get_index_constituents_data(index_id):
    """Retrieve index constituents sorted descending by market cap, cached for 1 hour."""
    cache_key = f"constituents_data_{index_id}"
    cached = app_cache.get(cache_key)
    if cached:
        return cached
        
    tickers = CONSTITUENTS_LISTS.get(index_id, [])
    if not tickers:
        return []
        
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_stock_basic_info, sym): sym for sym in tickers}
        for fut in concurrent.futures.as_completed(futures):
            res = fut.result()
            results.append(res)
            
    results.sort(key=lambda x: x['market_cap'] if x['market_cap'] is not None else -1, reverse=True)
    
    app_cache.set(cache_key, results, ttl=3600)
    return results

# ---------------------------------------------------------
# DCF MATHEMATICAL PROJECTIONS
# ---------------------------------------------------------
def run_dcf_valuation(fcf_base, growth_rate, discount_rate, terminal_growth_rate, net_debt, shares):
    """Project Free Cash Flows and calculate discounted fair equity value per share."""
    if fcf_base is None or fcf_base <= 0 or not shares or shares <= 0:
        return None
        
    projections = []
    current_fcf = fcf_base
    sum_pv_fcf = 0.0
    
    for year in range(1, 6):
        current_fcf = current_fcf * (1 + growth_rate)
        pv = current_fcf / ((1 + discount_rate) ** year)
        sum_pv_fcf += pv
        projections.append({
            'year': year,
            'fcf': current_fcf,
            'pv': pv
        })
        
    g_t = terminal_growth_rate
    r = discount_rate
    if r <= g_t:
        g_t = r - 0.05 if r > 0.05 else 0.02
        
    tv = projections[-1]['fcf'] * (1 + g_t) / (r - g_t)
    pv_tv = tv / ((1 + discount_rate) ** 5)
    
    enterprise_value = sum_pv_fcf + pv_tv
    equity_value = enterprise_value - net_debt
    fair_value = equity_value / shares
    
    return {
        'projections': projections,
        'sum_pv_fcf': sum_pv_fcf,
        'terminal_value': tv,
        'pv_terminal_value': pv_tv,
        'enterprise_value': enterprise_value,
        'equity_value': equity_value,
        'fair_value': fair_value,
        'terminal_growth_used': g_t
    }

# ---------------------------------------------------------
# FLASK ROUTES
# ---------------------------------------------------------


# ---------------------------------------------------------
# SEARCH INDEX CACHE
# ---------------------------------------------------------
SEARCH_INDEX = []

def build_search_index():
    global SEARCH_INDEX
    SEARCH_INDEX = []
    import os, json
    index_path = os.path.join('static', 'index_data.json')
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            data = json.load(f)
            seen = set()
            for idx_key, idx_data in data.items():
                for stock in idx_data.get('constituents', []):
                    symbol = stock.get('symbol')
                    if symbol and symbol not in seen:
                        seen.add(symbol)
                        SEARCH_INDEX.append({
                            'symbol': symbol,
                            'name': stock.get('name', symbol)
                        })

# Build it on startup
build_search_index()

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '').lower().strip()
    if not query:
        return jsonify([])
    
    results = []
    for item in SEARCH_INDEX:
        if query in item['symbol'].lower() or query in item['name'].lower():
            results.append(item)
            if len(results) >= 10:
                break
    return jsonify(results)

@app.route('/')

def index():
    """Index view displaying indices quote grid, movers, side-by-side index charts, and user projects."""
    start_time = time.time()
    try:
        indices = get_indices_data()
        movers = get_market_movers()
        charts = get_index_charts()
    except Exception as e:
        print(f"Index route data fetch error: {e}")
        indices = []
        movers = {'gainers': [], 'losers': [], 'active': []}
        charts = {'sp500_data': [], 'russell3000_data': []}
        
    try:
        # Folders are now entirely handled by frontend localStorage
        folders = []
    except Exception as e:
        print(f"DB error: {e}")
        folders = []
        
    query_time = f"{(time.time() - start_time):.3f}s"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    charts = get_index_charts()
    
    # NEW: Fetch sector performance and calendar
    sector_performance = get_sector_performance()
    economic_calendar = get_economic_calendar_live()
    
    return render_template(
        'index.html',
        indices=indices,
        charts=charts,
        sector_performance=sector_performance,
        economic_calendar=economic_calendar,
        gainers=movers['gainers'],
        losers=movers['losers'],
        active=movers['active'],
        folders=folders,
        query_time=query_time,
        current_time=current_time
    )

@app.route('/ticker/<symbol>')
def ticker_detail(symbol):
    """Detailed ticker profile view supporting Overview, Financials, and DCF Valuation tabs."""
    symbol = symbol.strip().upper()
    start_time = time.time()
    period = request.args.get('period', '1y')
    view = request.args.get('view', 'overview')
    stmt = request.args.get('stmt', 'income')
    
    if period not in ['1mo', '3mo', '6mo', '1y', '5y', 'max']:
        period = '1y'
    if view not in ['overview', 'financials', 'metrics', 'dcf']:
        view = 'overview'
    if stmt not in ['income', 'balance', 'cashflow']:
        stmt = 'income'
        
    cache_key = f"detail_{symbol}_{period}"
    cached_data = app_cache.get(cache_key)
    
    if cached_data:
        data = cached_data
    else:
        try:
            # GCP FIX: Injected masked custom desktop session
            ticker = yf.Ticker(symbol)
            info = ticker.info
            currency = info.get('financialCurrency', info.get('currency', 'USD'))
            fx_rate = get_usd_conversion_rate(currency)
            
            if not info or 'symbol' not in info and 'longName' not in info:
                hist = ticker.history(period="1d")
                if hist.empty:
                    flash(f"Error: Ticker symbol '{symbol}' was not found in the database.", "error")
                    return redirect(url_for('index'))
                    
            snapshot = {
                'symbol': symbol,
                'name': info.get('longName') or info.get('shortName') or symbol,
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'summary': info.get('longBusinessSummary', 'No description available.'),
                'exchange': info.get('exchange', 'NASDAQ/NYSE'),
                'price': info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose') or 0.0
            }
            
            prev_close = info.get('previousClose') or info.get('regularMarketPreviousClose') or snapshot['price']
            snapshot['change'] = snapshot['price'] - prev_close
            snapshot['change_pct'] = (snapshot['change'] / prev_close * 100) if prev_close else 0.0
            
            snapshot['price_formatted'] = f"${snapshot['price']:,.2f}"
            snapshot['change_formatted'] = f"{snapshot['change']:+,.2f}"
            snapshot['change_pct_formatted'] = f"{snapshot['change_pct']:+.2f}%"
            
            market_cap = info.get('marketCap')
            fcf = info.get('freeCashflow') or info.get('operatingCashflow')
            
            fcf_yield = "N/A"
            if market_cap and fcf and fcf > 0 and market_cap > 0:
                fcf_yield = f"{(fcf / market_cap) * 100:.2f}%"
                
            pe_ratio = format_value(info.get('trailingPE'), 'ratio')
                
            metrics = {
                'market_cap': format_value(market_cap, 'currency', fx_rate),
                'fcf_yield': fcf_yield,
                'current_price': snapshot['price_formatted'],
                'pe_ratio': pe_ratio
            }
            
            ratios = {
                'Trailing P/E': pe_ratio,
                'Forward P/E': format_value(info.get('forwardPE'), 'ratio'),
                'Price-to-Book (P/B)': format_value(info.get('priceToBook'), 'ratio'),
                'Price-to-Sales (P/S)': format_value(info.get('priceToSalesTrailing12Months'), 'ratio'),
                'Net Profit Margin (Net Income / Revenue)': format_value(info.get('profitMargins'), 'pct'),
                'Operating Profit Margin (EBIT / Revenue)': format_value(info.get('operatingMargins'), 'pct'),
                'Return on Equity (ROE)': format_value(info.get('returnOnEquity'), 'pct'),
                'Return on Assets (ROA)': format_value(info.get('returnOnAssets'), 'pct'),
                'Dividend Rate': format_value(info.get('dividendRate'), 'currency', fx_rate),
                'Dividend Yield': format_value(info.get('dividendYield') / 100 if info.get('dividendYield') else None, 'pct'),
                'Ex-Dividend Date': format_ex_dividend_date(info.get('exDividendDate')),
                'Next Earnings Date': format_ex_dividend_date(info.get('earningsTimestamp') or info.get('earningsTimestampStart')),
            }
            
            chart_data = get_chart_quotes_data(symbol, period)
            
            try:
                inc_df = ticker.income_stmt
                bal_df = ticker.balance_sheet
                cf_df = ticker.cashflow
            except Exception as e:
                print(f"Error calling financial statements: {e}")
                inc_df, bal_df, cf_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
                
            statements = {
                'income_stmt': process_income_statement(inc_df, fx_rate),
                'balance_sheet': process_balance_sheet(bal_df, fx_rate),
                'cashflow': process_cash_flow(cf_df, fx_rate)
            }
            
            fcf_base = info.get('freeCashflow')
            if not fcf_base or pd.isna(fcf_base) or fcf_base <= 0:
                ocf = info.get('operatingCashflow')
                cap_ex = info.get('capitalExpenditure') or 0
                if ocf and not pd.isna(ocf):
                    fcf_base = ocf + cap_ex if cap_ex < 0 else ocf - cap_ex
                    
            if not fcf_base or pd.isna(fcf_base) or fcf_base <= 0:
                try:
                    if not cf_df.empty:
                        fcf_row = None
                        for idx in cf_df.index:
                            if 'Free Cash Flow' in str(idx):
                                fcf_row = cf_df.loc[idx]
                                break
                        if fcf_row is not None and not fcf_row.empty:
                            fcf_base = float(fcf_row.iloc[0])
                except Exception:
                    pass
            
            total_cash = info.get('totalCash') or 0.0
            total_debt = info.get('totalDebt') or 0.0
            
            if (total_cash == 0.0 or total_debt == 0.0) and not bal_df.empty:
                try:
                    for idx in bal_df.index:
                        if 'Cash And Cash Equivalents' in str(idx) and total_cash == 0.0:
                            total_cash = float(bal_df.loc[idx].iloc[0])
                        elif 'Total Debt' in str(idx) and total_debt == 0.0:
                            total_debt = float(bal_df.loc[idx].iloc[0])
                except Exception:
                    pass
                    
            net_debt = total_debt - total_cash
            shares_outstanding = info.get('sharesOutstanding')
            
            default_growth = 10.0
            earnings_growth = info.get('earningsGrowth') or info.get('revenueGrowth')
            if earnings_growth and not pd.isna(earnings_growth):
                default_growth = float(earnings_growth) * 100.0
                if default_growth <= 0:
                    default_growth = 10.0
                    
            dcf_raw_inputs = {
                'fcf_base': float(fcf_base) if fcf_base and not pd.isna(fcf_base) else 0.0,
                'total_cash': float(total_cash),
                'total_debt': float(total_debt),
                'net_debt': float(net_debt),
                'shares_outstanding': float(shares_outstanding) if shares_outstanding else 0.0,
                'default_growth': default_growth,
                'fx_rate': fx_rate
            }
            
            data = {
                'snapshot': snapshot,
                'metrics': metrics,
                'ratios': ratios,
                'chart_data': chart_data,
                'statements': statements,
                'dcf_raw': dcf_raw_inputs
            }
            app_cache.set(cache_key, data, ttl=300)
            
        except Exception as e:
            print(f"Error fetching detail for {symbol}: {e}")
            flash(f"Error: An issue occurred fetching data for ticker '{symbol}'. Details: {str(e)}", "error")
            return redirect(url_for('index'))
            
    dcf_results = None
    dcf_error = None
    dcf_params = {}
    
    if view == 'dcf':
        raw = data['dcf_raw']
        fx_rate = raw.get('fx_rate', 1.0)
        if raw['fcf_base'] <= 0:
            dcf_error = "Valuation Notice: The company has negative or unavailable Free Cash Flow (FCF) data. DCF valuation cannot be computed using negative cash flows."
        elif raw['shares_outstanding'] <= 0:
            dcf_error = "Valuation Notice: Shares outstanding count is unavailable. Per-share equity fair value cannot be computed."
        else:
            try:
                growth_pct = float(request.args.get('growth', raw['default_growth']))
                discount_pct = float(request.args.get('discount', 9.0))
                terminal_pct = float(request.args.get('terminal', 2.5))
                custom_fcf_mil = request.args.get('fcf_base')
                if custom_fcf_mil is not None:
                    custom_fcf = float(custom_fcf_mil) * 1e6
                else:
                    custom_fcf = raw['fcf_base']
                
                if growth_pct < -50 or growth_pct > 200: growth_pct = raw['default_growth']
                if discount_pct < 2 or discount_pct > 30: discount_pct = 9.0
                if terminal_pct < 0 or terminal_pct > 10: terminal_pct = 2.5
                if custom_fcf <= 0: custom_fcf = raw['fcf_base']
                
                dcf_params = {
                    'growth': growth_pct,
                    'discount': discount_pct,
                    'terminal': terminal_pct,
                    'fcf_base': custom_fcf / 1e6
                }
                
                dcf_calc = run_dcf_valuation(
                    fcf_base=custom_fcf,
                    growth_rate=growth_pct / 100.0,
                    discount_rate=discount_pct / 100.0,
                    terminal_growth_rate=terminal_pct / 100.0,
                    net_debt=raw['net_debt'],
                    shares=raw['shares_outstanding']
                )
                
                if dcf_calc:
                    formatted_projs = []
                    for p in dcf_calc['projections']:
                        formatted_projs.append({
                            'year': p['year'],
                            'fcf': format_value(p['fcf'], 'currency', fx_rate),
                            'pv': format_value(p['pv'], 'currency', fx_rate)
                        })
                    
                    dcf_results = {
                        'projections': formatted_projs,
                        'fcf_base_formatted': format_value(raw['fcf_base'], 'currency', fx_rate),
                        'sum_pv_fcf': format_value(dcf_calc['sum_pv_fcf'], 'currency', fx_rate),
                        'terminal_value': format_value(dcf_calc['terminal_value'], 'currency', fx_rate),
                        'pv_terminal_value': format_value(dcf_calc['pv_terminal_value'], 'currency', fx_rate),
                        'enterprise_value': format_value(dcf_calc['enterprise_value'], 'currency', fx_rate),
                        'cash': format_value(raw['total_cash'], 'currency', fx_rate),
                        'debt': format_value(raw['total_debt'], 'currency', fx_rate),
                        'net_debt': format_value(raw['net_debt'], 'currency', fx_rate),
                        'equity_value': format_value(dcf_calc['equity_value'], 'currency', fx_rate),
                        'shares': format_value(raw['shares_outstanding'], 'number'),
                        'fair_value': f"${dcf_calc['fair_value'] * fx_rate:,.2f}",
                        'growth_rate_used': f"{growth_pct:.1f}%",
                        'discount_rate_used': f"{discount_pct:.1f}%",
                        'terminal_growth_used': f"{dcf_calc['terminal_growth_used']*100:.1f}%",
                    }
                else:
                    dcf_error = "Valuation Error: Projection model execution failed."
            except Exception as ex:
                dcf_error = f"Valuation Error: Inputs processing failed. Details: {str(ex)}"
                
    query_time = f"{(time.time() - start_time):.3f}s"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return render_template(
        'ticker.html',
        symbol=symbol,
        snapshot=data['snapshot'],
        metrics=data['metrics'],
        ratios=data['ratios'],
        chart_data=data['chart_data'],
        statements=data['statements'],
        dcf_raw=data['dcf_raw'],
        dcf_results=dcf_results,
        dcf_error=dcf_error,
        dcf_params=dcf_params,
        view=view,
        stmt=stmt,
        period=period,
        query_time=query_time,
        current_time=current_time
    )

INDEX_DATA_CACHE = None
INDEX_DATA_LOCK = threading.Lock()

def load_precompiled_index_data():
    """Load precompiled index constituents and growth data from static/index_data.json."""
    global INDEX_DATA_CACHE
    with INDEX_DATA_LOCK:
        if INDEX_DATA_CACHE is not None:
            return INDEX_DATA_CACHE
            
        json_path = os.path.join(app.static_folder, 'index_data.json')
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    INDEX_DATA_CACHE = json.load(f)
                    print("Successfully loaded precompiled index_data.json.")
                    return INDEX_DATA_CACHE
            except Exception as e:
                print(f"Error loading index_data.json: {e}")
        else:
            print("WARNING: index_data.json not found. Please compile it first.")
        return {}

@app.route('/index-constituents/<index_id>')
def index_constituents(index_id):
    """Watchlist page for index constituents featuring sector weights, top holdings, and growth charts."""
    start_time = time.time()
    index_id = index_id.lower().strip()
    
    supported_indices = {
        'sp500': 'S&P 500',
        'nasdaq100': 'Nasdaq 100',
        'dow30': 'Dow Jones 30',
        'russell3000': 'Russell 3000',
        'nikkei225': 'Nikkei 225',
        'omxs30': 'OMX Stockholm 30'
    }
    
    if index_id not in supported_indices:
        flash(f"Error: Index '{index_id}' is not supported.", "error")
        return redirect(url_for('index'))
        
    index_name = supported_indices[index_id]
    
    full_data = load_precompiled_index_data()
    index_dataset = full_data.get(index_id, {})
    constituents = index_dataset.get('constituents', [])
    growth_data = index_dataset.get('growth', [])
    
    index_ticker_map = {
        'sp500': '^GSPC',
        'nasdaq100': '^IXIC',
        'dow30': '^DJI',
        'russell3000': '^RUA',
        'nikkei225': '^N225',
        'omxs30': '^OMX'
    }
    try:
        index_quote = fetch_index_quote(index_ticker_map[index_id])
    except:
        index_quote = None

    formatted_constituents = []
    for stock in constituents:
        market_cap = stock.get('market_cap')
        pe_ratio = stock.get('pe_ratio')
        formatted_constituents.append({
            'symbol': stock['symbol'],
            'name': stock['name'],
            'market_cap': market_cap,
            'market_cap_formatted': format_value(market_cap, 'currency') if market_cap else 'N/A',
            'pe_ratio': pe_ratio,
            'pe_ratio_formatted': format_value(pe_ratio, 'number') if pe_ratio else 'N/A',
            'sector': stock.get('sector', 'Other')
        })
        
    sector_caps = {}
    total_index_cap = 0
    for stock in constituents:
        cap = stock.get('market_cap') or 0
        sector = stock.get('sector') or 'Other'
        sector_caps[sector] = sector_caps.get(sector, 0) + cap
        total_index_cap += cap
        
    sector_concentration = []
    if total_index_cap > 0:
        for sector, cap in sector_caps.items():
            pct = (cap / total_index_cap) * 100
            sector_concentration.append({
                'sector': sector,
                'market_cap': cap,
                'market_cap_formatted': format_value(cap, 'currency'),
                'percentage': round(pct, 2)
            })
        sector_concentration.sort(key=lambda x: x['market_cap'], reverse=True)

    top_holdings = []
    accumulated_cap = 0
    if total_index_cap > 0:
        for idx, c in enumerate(constituents):
            cap = c.get('market_cap') or 0
            pct = (cap / total_index_cap * 100)
            
            remaining_pct = 100.0 - (accumulated_cap / total_index_cap * 100)
            
            if remaining_pct < 5.0 and idx < len(constituents):
                other_cap = sum(stock.get('market_cap') or 0 for stock in constituents[idx:])
                other_pct = (other_cap / total_index_cap * 100)
                top_holdings.append({
                    'symbol': 'Others',
                    'name': 'Other Tickers',
                    'market_cap': other_cap,
                    'percentage': round(other_pct, 2)
                })
                break
            else:
                top_holdings.append({
                    'symbol': c['symbol'],
                    'name': c['name'],
                    'market_cap': cap,
                    'percentage': round(pct, 2)
                })
                accumulated_cap += cap

    query_time = f"{(time.time() - start_time):.3f}s"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template(
        'constituents.html',
        index_id=index_id,
        index_name=index_name,
        index_quote=index_quote,
        constituents=formatted_constituents,
        sector_concentration=sector_concentration,
        top_holdings=top_holdings,
        growth_data=growth_data,
        query_time=query_time,
        current_time=current_time
    )

@app.route('/model-builder')
def model_builder_view():
    return render_template('model_builder.html')

@app.route('/guide')
def guide_view():
    return render_template('guide.html')

@app.route('/stock')
def stock_search_view():
    return render_template('stock_search.html')

@app.route('/query', methods=['GET', 'POST'])
def query_ticker():
    """Redirect user search input to target stock ticker route."""
    if request.method == 'POST':
        symbol = request.form.get('symbol', '').strip().upper()
    else:
        symbol = request.args.get('symbol', '').strip().upper()
        
    if not symbol:
        flash("Error: Please enter a valid ticker symbol.", "error")
        return redirect(url_for('index'))
        
    return redirect(url_for('ticker_detail', symbol=symbol))

@app.route('/api/terminal', methods=['POST'])
def terminal_command():
    data = request.json
    cmd = data.get('command', '').strip()
    
    if not cmd:
        return jsonify({'error': 'Empty command'})
        
    parts = cmd.split()
    action = parts[0].lower()
    
    try:
        cmd_lower = cmd.lower()
        if 'balance sheet' in cmd_lower:
            # Extract ticker by removing "balance" and "sheet"
            ticker_parts = [p for p in parts if p.lower() not in ['balance', 'sheet']]
            ticker = ticker_parts[0].upper() if ticker_parts else ''
            
            # GCP FIX: Injected global desktop session context
            stock = yf.Ticker(ticker)
            processed = process_balance_sheet(stock.balance_sheet)
            if processed:
                headers = processed['columns']
                rows = []
                for section in ['assets', 'liabilities', 'equity']:
                    for r in processed[section]:
                        rows.append([r['label']] + r['values'])
                return jsonify({'action': 'statement', 'title': f"{ticker} Balance Sheet", 'headers': headers, 'rows': rows})
            return jsonify({'error': f'No balance sheet data for {ticker}'})
            
        elif 'income statement' in cmd_lower:
            ticker_parts = [p for p in parts if p.lower() not in ['income', 'statement']]
            ticker = ticker_parts[0].upper() if ticker_parts else ''
            
            # GCP FIX: Injected global desktop session context
            stock = yf.Ticker(ticker)
            processed = process_income_statement(stock.financials)
            if processed:
                headers = processed['columns']
                rows = []
                for r in processed['rows']:
                    rows.append([r['label']] + r['values'])
                return jsonify({'action': 'statement', 'title': f"{ticker} Income Statement", 'headers': headers, 'rows': rows})
            return jsonify({'error': f'No income statement data for {ticker}'})
            
        elif 'cash flow' in cmd_lower:
            ticker_parts = [p for p in parts if p.lower() not in ['cash', 'flow']]
            ticker = ticker_parts[0].upper() if ticker_parts else ''
            # GCP FIX: Injected global desktop session context
            stock = yf.Ticker(ticker)
            processed = process_cash_flow(stock.cashflow)
            if processed:
                headers = processed['columns']
                rows = []
                if processed['operating']:
                    rows.append(['1. OPERATING ACTIVITIES'] + [''] * len(headers))
                    for r in processed['operating']: rows.append([r['label']] + r['values'])
                if processed['investing']:
                    rows.append(['2. INVESTING ACTIVITIES'] + [''] * len(headers))
                    for r in processed['investing']: rows.append([r['label']] + r['values'])
                if processed['financing']:
                    rows.append(['3. FINANCING ACTIVITIES'] + [''] * len(headers))
                    for r in processed['financing']: rows.append([r['label']] + r['values'])
                if processed['reconciliation']:
                    rows.append(['4. RECONCILIATION'] + [''] * len(headers))
                    for r in processed['reconciliation']: rows.append([r['label']] + r['values'])
                return jsonify({'action': 'statement', 'title': f"{ticker} Cash Flow", 'headers': headers, 'rows': rows})
            return jsonify({'error': f'No cash flow data for {ticker}'})

        elif action == 'help':
            help_text = (
                "[ FINANCIAL LOOKUPS ]\n"
                "- balance sheet [ticker] : Open balance sheet\n"
                "- income statement [ticker] : Open income statement\n"
                "- cash flow [ticker] : Open cash flow statement\n"
                "- chart [ticker] : Open interactive chart for ticker\n"
                "- price [ticker] : Get current price info\n"
                "- pe [ticker] : Get P/E ratio\n"
                "- [metric] [year] [ticker] : Search any financial metric\n"
                "\n"
                "[ RESEARCH FOLDERS ]\n"
                "- mkdir [name] : Create a new research folder\n"
                "- cd [name] : Enter a research folder (or 'cd ..' to exit)\n"
                "- ls : List notes in current folder\n"
                "- note [\"Title\"] [text] : Add a note to the current folder\n"
                "- cat [id] : View full contents of a note\n"
                "- rm [name] : Delete a research folder\n"
                "\n"
                "[ SYSTEM ]\n"
                "- nav [ticker] : Navigate main window to ticker page\n"
                "- /panic : Liquidate all assets and scramble MAC address\n"
                "- clear : Clear terminal output"
            )
            return jsonify({'action': 'print', 'text': help_text})
            
        elif action == 'nav' and len(parts) > 1:
            target = " ".join(parts[1:]).lower()
            if target in ['home', 'market home']:
                return jsonify({'action': 'redirect', 'url': url_for('index')})
            elif target == 'indices' or target == 'index constituents':
                return jsonify({'action': 'redirect', 'url': url_for('index_constituents', index_id='sp500')})
            elif target == 'model builder':
                return jsonify({'action': 'redirect', 'url': url_for('model_builder_view')})
            elif target == 'guide':
                return jsonify({'action': 'redirect', 'url': url_for('guide_view')})
            else:
                ticker = parts[1].upper()
                return jsonify({'action': 'redirect', 'url': url_for('ticker_detail', symbol=ticker)})
            
        elif action == 'price' and len(parts) > 1:
            ticker = parts[1].upper()
            # GCP FIX: Injected global desktop session context
            stock = yf.Ticker(ticker)
            info = stock.info
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            if price:
                return jsonify({'action': 'print', 'text': f"{ticker} Current Price: ${price:.2f}"})
            else:
                return jsonify({'error': f'Could not fetch price for {ticker}'})
                
        elif action == 'pe' and len(parts) > 1:
            ticker = parts[1].upper()
            # GCP FIX: Injected global desktop session context
            stock = yf.Ticker(ticker)
            info = stock.info
            pe = info.get('trailingPE')
            if pe:
                return jsonify({'action': 'print', 'text': f"{ticker} P/E Ratio: {pe:.2f}"})
            else:
                return jsonify({'error': f'Could not fetch P/E for {ticker}'})
                
        elif action == 'chart' and len(parts) > 1:
            ticker = parts[1].upper()
            period = '1y'
            if len(parts) > 2:
                allowed_periods = ['1mo', '3mo', '6mo', '1y', '5y', 'max', 'ytd']
                if parts[2].lower() in allowed_periods:
                    period = parts[2].lower()
            
            # GCP FIX: Injected global desktop session context
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            if not hist.empty:
                chart_data = []
                for date, row in hist.iterrows():
                    chart_data.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'close': float(row['Close']),
                        'volume': int(row['Volume'])
                    })
                return jsonify({'action': 'chart', 'symbol': ticker, 'period': period, 'data': chart_data})
            else:
                return jsonify({'error': f'No chart data for {ticker}'})
                
        else:
            year = None
            for i, p in enumerate(parts):
                if p.isdigit() and len(p) == 4:
                    year = p
                    parts.pop(i)
                    break
            
            if len(parts) < 2:
                return jsonify({'error': "Invalid metric query. Try: [ticker] [metric] [year]"})
                
            # Detect ticker position (first or last)
            if parts[0].upper().isalpha() and len(parts[0]) <= 5 and len(parts[-1]) > 5:
                ticker = parts[0].upper()
                metric_query = " ".join(parts[1:]).lower()
            elif parts[-1].upper().isalpha() and len(parts[-1]) <= 5:
                ticker = parts[-1].upper()
                metric_query = " ".join(parts[:-1]).lower()
            else:
                # Default assume first is ticker
                ticker = parts[0].upper()
                metric_query = " ".join(parts[1:]).lower()
                
            # Handle common acronyms
            aliases = {
                'ocf': 'operating cash flow',
                'fcf': 'free cash flow',
                'capex': 'capital expenditure',
                'ebitda': 'normalized ebitda'
            }
            if metric_query in aliases:
                metric_query = aliases[metric_query]
                
            stock = yf.Ticker(ticker)
            currency = stock.info.get('financialCurrency', stock.info.get('currency', 'USD'))
            fx_rate = get_usd_conversion_rate(currency)
            all_indexes = {}
            try:
                dfs = [stock.income_stmt, stock.balance_sheet, stock.cashflow]
            except Exception:
                dfs = [stock.financials, stock.balance_sheet, stock.cashflow]
                
            for df in dfs:
                if df is not None and not df.empty:
                    for idx in df.index:
                        all_indexes[str(idx)] = df.loc[idx]
            
            if not all_indexes:
                return jsonify({'error': f"No financial data found for {ticker}."})
                
            matches = difflib.get_close_matches(metric_query, [k.lower() for k in all_indexes.keys()], n=1, cutoff=0.3)
            if not matches:
                for k in all_indexes.keys():
                    if metric_query in k.lower():
                        matches = [k.lower()]
                        break
                        
            if matches:
                matched_key_lower = matches[0]
                actual_key = next(k for k in all_indexes.keys() if k.lower() == matched_key_lower)
                row_data = all_indexes[actual_key]
                
                if year:
                    for col in row_data.index:
                        if str(col).startswith(year):
                            val = row_data[col]
                            return jsonify({'action': 'print', 'text': f"{ticker} {actual_key} ({year}): {format_value(val, 'currency', fx_rate)}"})
                    return jsonify({'error': f"Found {actual_key} but no data for year {year}."})
                else:
                    result_parts = []
                    for col in row_data.index:
                        year_str = str(col)[:4]
                        val_str = format_value(row_data[col], 'currency', fx_rate)
                        result_parts.append(f"{year_str}: {val_str}")
                    return jsonify({'action': 'print', 'text': f"{ticker} {actual_key} -> " + " | ".join(result_parts)})
            else:
                return jsonify({'error': f"Unknown command or metric: '{cmd}'. Type 'help'."})
            
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/financial_data', methods=['POST'])
def financial_data():
    data = request.json
    tickers = data.get('tickers', [])
    result = {}
    for t in tickers:
        if not t: continue
        t = t.upper()
        try:
            stock = yf.Ticker(t)
            info = stock.info
            fast_info = stock.fast_info
            
            currency = info.get('currency', 'USD')
            fx_rate = get_usd_conversion_rate(currency)
            
            # Determine price safely
            price = "N/A"
            try:
                price = f"${fast_info.last_price:.2f}"
            except:
                if info.get('currentPrice'):
                    price = f"${info.get('currentPrice'):.2f}"
                    
            result[t] = {
                'price': price,
                'pe': format_value(info.get('trailingPE'), 'ratio'),
                'fwd_pe': format_value(info.get('forwardPE'), 'ratio'),
                'market_cap': format_value(info.get('marketCap'), 'currency', fx_rate),
                'revenue': format_value(info.get('totalRevenue'), 'currency', fx_rate),
                'net_income': format_value(info.get('netIncomeToCommon'), 'currency', fx_rate),
                'dividend_yield': format_value(info.get('dividendYield') / 100 if info.get('dividendYield') else None, 'pct'),
                'dividend_rate': format_value(info.get('dividendRate'), 'currency', fx_rate),
                'profit_margin': format_value(info.get('profitMargins'), 'pct'),
                'roa': format_value(info.get('returnOnAssets'), 'pct'),
                'roe': format_value(info.get('returnOnEquity'), 'pct'),
            }
        except:
            result[t] = { 'error': 'Failed to fetch data' }
    return jsonify({'success': True, 'data': result})

@app.route('/api/historical_metrics', methods=['POST'])
def historical_metrics_api():
    data = request.json
    ticker = data.get('ticker', '').strip().upper()
    if not ticker:
        return jsonify({'error': 'No ticker provided'})
        
    stock = yf.Ticker(ticker)
    q_fin = stock.quarterly_financials
    q_cf = stock.quarterly_cashflow

    if q_fin.empty and q_cf.empty:
        return jsonify({'error': 'No quarterly data found for this ticker.'})

    # Transpose so rows are dates, then sort oldest to newest
    q_fin = q_fin.T.sort_index() if not q_fin.empty else pd.DataFrame()
    q_cf = q_cf.T.sort_index() if not q_cf.empty else pd.DataFrame()

    def get_series(df, keys):
        for k in keys:
            if k in df.columns:
                return df[k]
        return pd.Series(index=df.index, dtype=float)

    rev = get_series(q_fin, ['Total Revenue', 'Operating Revenue'])
    ni = get_series(q_fin, ['Net Income', 'Net Income Common Stockholders', 'Net Income Continuous Operations'])
    ebit = get_series(q_fin, ['EBIT', 'Operating Income'])
    ocf = get_series(q_cf, ['Operating Cash Flow', 'Cash Flow From Operating Activities'])
    fcf = get_series(q_cf, ['Free Cash Flow'])

    margin = pd.Series(index=rev.index, dtype=float)
    if not rev.empty and not ebit.empty:
        margin_arr = np.where(rev != 0, ebit / rev, np.nan)
        margin = pd.Series(margin_arr, index=rev.index)

    def process_metric(series, is_pct=False):
        if series.isna().all():
            return []
        series = series.dropna()
        
        data_points = []
        for date, val in series.items():
            if isinstance(date, pd.Timestamp):
                date_str = f"Q{(date.month-1)//3 + 1} '{date.strftime('%y')}"
            else:
                date_str = str(date)
            data_points.append({'date': date_str, 'value': float(val)})

        if len(data_points) == 0:
            return []

        vals = np.array([dp['value'] for dp in data_points])
        avg_val = float(np.mean(vals))
        std_dev = float(np.std(vals))
        
        yoy_change = None
        if len(vals) >= 5:
            # YoY change between the most recent quarter and the quarter 1 year ago (4 quarters prior)
            if vals[-5] != 0:
                yoy_change = float((vals[-1] - vals[-5]) / abs(vals[-5]))

        return {
            'data': data_points,
            'stats': {
                'avg': avg_val,
                'std': std_dev,
                'avg_change': yoy_change
            }
        }

    res = {
        'Revenue': process_metric(rev),
        'Net Income': process_metric(ni),
        'EBIT': process_metric(ebit),
        'Operating Cash Flow': process_metric(ocf),
        'Free Cash Flow': process_metric(fcf),
        'Operating Margin': process_metric(margin, is_pct=True)
    }
    
    return jsonify(res)

if __name__ == '__main__':
    # Binding to the dynamic port required by Cloud Run environment rules
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)

# Trigger Flask Reload

# Hot reload trigger after JSON update
