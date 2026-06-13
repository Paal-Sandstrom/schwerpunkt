with open('app.py', 'r') as f:
    content = f.read()

# Replace dcf_raw_inputs declaration
old_dcf_raw = """            dcf_raw_inputs = {
                'fcf_base': float(fcf_base) if fcf_base and not pd.isna(fcf_base) else 0.0,
                'total_cash': float(total_cash),
                'total_debt': float(total_debt),
                'net_debt': float(net_debt),
                'shares_outstanding': float(shares_outstanding) if shares_outstanding else 0.0,
                'default_growth': default_growth
            }"""

new_dcf_raw = """            dcf_raw_inputs = {
                'fcf_base': float(fcf_base) if fcf_base and not pd.isna(fcf_base) else 0.0,
                'total_cash': float(total_cash),
                'total_debt': float(total_debt),
                'net_debt': float(net_debt),
                'shares_outstanding': float(shares_outstanding) if shares_outstanding else 0.0,
                'default_growth': default_growth,
                'fx_rate': fx_rate
            }"""

content = content.replace(old_dcf_raw, new_dcf_raw)

# Replace the dcf view definition
old_dcf_view = """    if view == 'dcf':
        raw = data['dcf_raw']
        if raw['fcf_base'] <= 0:"""

new_dcf_view = """    if view == 'dcf':
        raw = data['dcf_raw']
        fx_rate = raw.get('fx_rate', 1.0)
        if raw['fcf_base'] <= 0:"""

content = content.replace(old_dcf_view, new_dcf_view)

with open('app.py', 'w') as f:
    f.write(content)

print('Patched app.py to persist fx_rate in cache for DCF!')
