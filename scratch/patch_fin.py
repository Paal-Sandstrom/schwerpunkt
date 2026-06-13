with open('app.py', 'r') as f:
    content = f.read()

# 1. Update format_series_values
old_format = '''def format_series_values(series, label_name=""):
    """Format row cell series based on its financial item type (currency, shares, rates, ratios)."""
    values = []
    lbl_lower = label_name.lower()
    
    is_share_count = any(x in lbl_lower for x in ['shares', 'share number', 'average shares', 'shares outstanding'])
    is_percentage = any(x in lbl_lower for x in ['tax rate', 'rate for calcs', 'margin', 'yield', 'percent'])
    is_ratio = bool(re.search(r'\\b(ratio|multiple|factor)s?\\b', lbl_lower))
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
                values.append(f"${v:,.2f}")
            elif is_ratio:
                values.append(f"{v:.2f}x")
            else:
                if abs(v) >= 1e9:
                    values.append(f"${v/1e9:,.2f}B")
                elif abs(v) >= 1e6:
                    values.append(f"${v/1e6:,.2f}M")
                else:
                    values.append(f"${v:,.2f}")
        except Exception:
            values.append(str(val))
    return values'''

new_format = '''def format_series_values(series, label_name="", fx_rate=1.0):
    """Format row cell series based on its financial item type (currency, shares, rates, ratios)."""
    values = []
    lbl_lower = label_name.lower()
    
    is_share_count = any(x in lbl_lower for x in ['shares', 'share number', 'average shares', 'shares outstanding'])
    is_percentage = any(x in lbl_lower for x in ['tax rate', 'rate for calcs', 'margin', 'yield', 'percent'])
    is_ratio = bool(re.search(r'\\b(ratio|multiple|factor)s?\\b', lbl_lower))
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
    return values'''
content = content.replace(old_format, new_format)

# 2. Update process_* statements
content = content.replace("def process_income_statement(df):", "def process_income_statement(df, fx_rate=1.0):")
content = content.replace("'values': format_series_values(series, label_str),", "'values': format_series_values(series, label_str, fx_rate),")
content = content.replace("def process_balance_sheet(df):", "def process_balance_sheet(df, fx_rate=1.0):")
content = content.replace("def process_cash_flow(df):", "def process_cash_flow(df, fx_rate=1.0):")

# 3. Update the ticker_detail call
old_statements = """            statements = {
                'income_stmt': process_income_statement(inc_df),
                'balance_sheet': process_balance_sheet(bal_df),
                'cashflow': process_cash_flow(cf_df)
            }"""
new_statements = """            statements = {
                'income_stmt': process_income_statement(inc_df, fx_rate),
                'balance_sheet': process_balance_sheet(bal_df, fx_rate),
                'cashflow': process_cash_flow(cf_df, fx_rate)
            }"""
content = content.replace(old_statements, new_statements)

# 4. Update fair_value format
content = content.replace("'fair_value': f\"${dcf_calc['fair_value']:,.2f}\",", "'fair_value': f\"${dcf_calc['fair_value'] * fx_rate:,.2f}\",")

with open('app.py', 'w') as f:
    f.write(content)
print('app.py patched for financial statements conversion!')
