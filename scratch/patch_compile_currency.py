with open('scratch/compile_international.py', 'r') as f:
    content = f.read()

old_code = '''            currency = info.get('financialCurrency', info.get('currency', 'USD'))
            rate = get_usd_rate(currency) if currency != 'USD' else 1.0'''

new_code = '''            currency = info.get('currency', 'USD')
            rate = get_usd_rate(currency) if currency != 'USD' else 1.0'''

content = content.replace(old_code, new_code)

with open('scratch/compile_international.py', 'w') as f:
    f.write(content)
print('compile_international.py patched for correct currency!')
