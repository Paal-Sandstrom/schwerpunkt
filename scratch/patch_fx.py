with open('app.py', 'r') as f:
    content = f.read()

# Fix fetch_stock_basic_info
old_fetch = '''    try:
        # GCP FIX: Injected masked custom desktop session
        ticker = yf.Ticker(symbol)
        info = ticker.info
        name = info.get('longName') or info.get('shortName') or COMPANY_NAMES.get(symbol) or symbol'''

new_fetch = '''    try:
        # GCP FIX: Injected masked custom desktop session
        ticker = yf.Ticker(symbol)
        info = ticker.info
        currency = info.get('financialCurrency', info.get('currency', 'USD'))
        fx_rate = get_usd_conversion_rate(currency)
        name = info.get('longName') or info.get('shortName') or COMPANY_NAMES.get(symbol) or symbol'''
content = content.replace(old_fetch, new_fetch)

# Fix index_constituents
content = content.replace("'market_cap_formatted': format_value(market_cap, 'currency', fx_rate) if market_cap else 'N/A',", "'market_cap_formatted': format_value(market_cap, 'currency') if market_cap else 'N/A',")
content = content.replace("'market_cap_formatted': format_value(cap, 'currency', fx_rate),", "'market_cap_formatted': format_value(cap, 'currency'),")

with open('app.py', 'w') as f:
    f.write(content)

print('app.py fixed')
