import re

with open('app.py', 'r') as f:
    content = f.read()

# In ticker_detail
content = content.replace(
    '''    try:
        info = stock.info''',
    '''    try:
        info = stock.info
        currency = info.get('financialCurrency', info.get('currency', 'USD'))
        fx_rate = get_usd_conversion_rate(currency)'''
)

# Update market cap formats
content = content.replace("format_value(market_cap, 'currency')", "format_value(market_cap, 'currency', fx_rate)")
content = content.replace("format_value(info.get('dividendRate'), 'currency')", "format_value(info.get('dividendRate'), 'currency', fx_rate)")
content = content.replace("format_value(cap, 'currency')", "format_value(cap, 'currency', fx_rate)")

# Update process_df definition
content = content.replace("def process_df(df):", "def process_df(df, fx_rate=1.0):")
content = content.replace("row['values'].append(format_value(df.loc[idx, col], 'currency'))", "row['values'].append(format_value(df.loc[idx, col], 'currency', fx_rate))")

# Update process_df calls
content = content.replace("process_df(income_stmt)", "process_df(income_stmt, fx_rate)")
content = content.replace("process_df(balance_sheet)", "process_df(balance_sheet, fx_rate)")
content = content.replace("process_df(cash_flow)", "process_df(cash_flow, fx_rate)")

# DCF variables
content = content.replace("format_value(p['fcf'], 'currency')", "format_value(p['fcf'], 'currency', fx_rate)")
content = content.replace("format_value(p['pv'], 'currency')", "format_value(p['pv'], 'currency', fx_rate)")
content = content.replace("format_value(raw['fcf_base'], 'currency')", "format_value(raw['fcf_base'], 'currency', fx_rate)")
content = content.replace("format_value(dcf_calc['sum_pv_fcf'], 'currency')", "format_value(dcf_calc['sum_pv_fcf'], 'currency', fx_rate)")
content = content.replace("format_value(dcf_calc['terminal_value'], 'currency')", "format_value(dcf_calc['terminal_value'], 'currency', fx_rate)")
content = content.replace("format_value(dcf_calc['pv_terminal_value'], 'currency')", "format_value(dcf_calc['pv_terminal_value'], 'currency', fx_rate)")
content = content.replace("format_value(dcf_calc['enterprise_value'], 'currency')", "format_value(dcf_calc['enterprise_value'], 'currency', fx_rate)")
content = content.replace("format_value(raw['total_cash'], 'currency')", "format_value(raw['total_cash'], 'currency', fx_rate)")
content = content.replace("format_value(raw['total_debt'], 'currency')", "format_value(raw['total_debt'], 'currency', fx_rate)")
content = content.replace("format_value(raw['net_debt'], 'currency')", "format_value(raw['net_debt'], 'currency', fx_rate)")
content = content.replace("format_value(dcf_calc['equity_value'], 'currency')", "format_value(dcf_calc['equity_value'], 'currency', fx_rate)")

# /api/financial_data
content = content.replace(
    '''    try:
        stock = yf.Ticker(ticker)
        if statement_type == 'income':''',
    '''    try:
        stock = yf.Ticker(ticker)
        currency = stock.info.get('financialCurrency', stock.info.get('currency', 'USD'))
        fx_rate = get_usd_conversion_rate(currency)
        if statement_type == 'income':'''
)
content = content.replace("processed = process_df(df)", "processed = process_df(df, fx_rate)")

# /api/terminal
content = content.replace(
    '''            stock = yf.Ticker(ticker)
            all_indexes = {}''',
    '''            stock = yf.Ticker(ticker)
            currency = stock.info.get('financialCurrency', stock.info.get('currency', 'USD'))
            fx_rate = get_usd_conversion_rate(currency)
            all_indexes = {}'''
)
content = content.replace("format_value(val, 'currency')", "format_value(val, 'currency', fx_rate)")
content = content.replace("format_value(row_data[col], 'currency')", "format_value(row_data[col], 'currency', fx_rate)")

# /api/historical_metrics
content = content.replace(
    '''    try:
        stock = yf.Ticker(ticker)
        info = stock.info''',
    '''    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        currency = info.get('financialCurrency', info.get('currency', 'USD'))
        fx_rate = get_usd_conversion_rate(currency)'''
)
content = content.replace("format_value(info.get('marketCap'), 'currency')", "format_value(info.get('marketCap'), 'currency', fx_rate)")
content = content.replace("format_value(info.get('totalRevenue'), 'currency')", "format_value(info.get('totalRevenue'), 'currency', fx_rate)")
content = content.replace("format_value(info.get('netIncomeToCommon'), 'currency')", "format_value(info.get('netIncomeToCommon'), 'currency', fx_rate)")

with open('app.py', 'w') as f:
    f.write(content)
