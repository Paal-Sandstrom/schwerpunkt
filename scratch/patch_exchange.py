with open('app.py', 'r') as f:
    content = f.read()

old_code = '''            snapshot = {
                'symbol': symbol,
                'name': info.get('longName') or info.get('shortName') or symbol,
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'summary': info.get('longBusinessSummary', 'No description available.'),
                'price': info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose') or 0.0
            }'''

new_code = '''            snapshot = {
                'symbol': symbol,
                'name': info.get('longName') or info.get('shortName') or symbol,
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'summary': info.get('longBusinessSummary', 'No description available.'),
                'exchange': info.get('exchange', 'NASDAQ/NYSE'),
                'price': info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose') or 0.0
            }'''

content = content.replace(old_code, new_code)

with open('app.py', 'w') as f:
    f.write(content)

with open('templates/ticker.html', 'r') as f:
    html_content = f.read()

html_content = html_content.replace('NASDAQ/NYSE', '{{ snapshot.exchange }}')

with open('templates/ticker.html', 'w') as f:
    f.write(html_content)

print('Patched app.py and ticker.html for correct exchange display!')
