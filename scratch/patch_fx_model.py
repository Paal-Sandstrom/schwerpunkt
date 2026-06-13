with open('app.py', 'r') as f:
    content = f.read()

old_code = '''            stock = yf.Ticker(t)
            info = stock.info
            fast_info = stock.fast_info
            
            # Determine price safely'''

new_code = '''            stock = yf.Ticker(t)
            info = stock.info
            fast_info = stock.fast_info
            
            currency = info.get('currency', 'USD')
            fx_rate = get_usd_conversion_rate(currency)
            
            # Determine price safely'''

content = content.replace(old_code, new_code)

with open('app.py', 'w') as f:
    f.write(content)
print('Fixed fx_rate missing bug in /api/financial_data!')
